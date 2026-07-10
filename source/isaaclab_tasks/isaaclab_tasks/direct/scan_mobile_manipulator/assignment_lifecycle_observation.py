"""Pure lifecycle decision-snapshot and tensor builders.

This module is intentionally project-local and integration-free. It copies one
policy-decision lifecycle state into a no-alias snapshot, validates frozen
Contract C invariants, and builds the Phase 9G-8C actor/critic lifecycle tensor
blocks. It does not modify resolver, wrapper, mask, checkpoint, or HARL runtime
behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch

try:
    from .assignment_lifecycle_resolver import (
        NO_OWNER,
        NO_TARGET,
        PAIR_ACTIVE,
        PAIR_COMPLETED,
        PAIR_FAILED_BUDGET,
        PAIR_NONE,
        PAIR_RELEASED_BUDGET,
    )
except ImportError:  # Allows direct file-based smoke tests after adding this directory to sys.path.
    from assignment_lifecycle_resolver import (  # type: ignore
        NO_OWNER,
        NO_TARGET,
        PAIR_ACTIVE,
        PAIR_COMPLETED,
        PAIR_FAILED_BUDGET,
        PAIR_NONE,
        PAIR_RELEASED_BUDGET,
    )


ACTOR_LIFECYCLE_FEATURE_ORDER: tuple[str, str, str] = (
    "self_active_target",
    "task_owned_by_teammate",
    "self_pair_failed_or_released",
)

CRITIC_BUDGET_FEATURE_ORDER: tuple[str, str] = (
    "active_budget_progress_norm",
    "active_budget_step_fraction",
)

SNAPSHOT_CONTRACT_VERSION = "lifecycle_decision_snapshot_v1"
ACTOR_SCHEMA_VERSION = "lifecycle_v1_actor_3n"
CRITIC_BUDGET_SCHEMA_VERSION = "lifecycle_v1_critic_budget_2m"
LIFECYCLE_ABLATION_MASK_VERSION = "lifecycle_ablation_physical_mask_v1"
LIFECYCLE_CONTRACT_C_MASK_VERSION = "lifecycle_contract_c_mask_v1"

_VALID_PAIR_STATES = {
    PAIR_NONE,
    PAIR_ACTIVE,
    PAIR_COMPLETED,
    PAIR_FAILED_BUDGET,
    PAIR_RELEASED_BUDGET,
}


def _clone_tensor(value: torch.Tensor, *, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor, got {type(value).__name__}")
    return value.detach().clone()


def _clone_optional_tensor(value: torch.Tensor | None, *, name: str) -> torch.Tensor | None:
    if value is None:
        return None
    return _clone_tensor(value, name=name)


def _normalize_episode_generation(
    value: int | torch.Tensor,
    *,
    num_envs: int,
    device: torch.device,
) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return torch.full((num_envs,), int(value.item()), dtype=torch.long, device=device)
        tensor = value.detach().clone().to(device=device, dtype=torch.long).flatten()
        if tuple(tensor.shape) != (num_envs,):
            raise ValueError(
                "episode_generation must be a scalar or have shape "
                f"({num_envs},), got {tuple(value.shape)}"
            )
        return tensor
    return torch.full((num_envs,), int(value), dtype=torch.long, device=device)


def _format_bad_indices(mask: torch.Tensor, *, limit: int = 8) -> str:
    rows = torch.nonzero(mask.detach().cpu(), as_tuple=False).tolist()
    return str(rows[:limit])


def _require_shape(tensor: torch.Tensor, expected: tuple[int, ...], *, name: str) -> None:
    if tuple(tensor.shape) != expected:
        raise ValueError(f"{name} must have shape {expected}, got {tuple(tensor.shape)}")


def _require_device(tensor: torch.Tensor, device: torch.device, *, name: str) -> None:
    if tensor.device != device:
        raise ValueError(f"{name} must be on device {device}, got {tensor.device}")


def _require_dtype(tensor: torch.Tensor, dtype: torch.dtype, *, name: str) -> None:
    if tensor.dtype != dtype:
        raise TypeError(f"{name} must have dtype {dtype}, got {tensor.dtype}")


@dataclass(frozen=True)
class LifecycleDecisionSnapshot:
    """Copied immutable-by-contract lifecycle state for one policy decision."""

    snapshot_generation: int
    episode_generation: int | torch.Tensor
    active_target_id: torch.Tensor
    task_owner_robot_id: torch.Tensor
    pair_state: torch.Tensor
    budget_attempt_target: torch.Tensor
    budget_attempt_steps: torch.Tensor
    budget_attempt_budget_steps: torch.Tensor
    viewpoints_covered: torch.Tensor
    available_mask: torch.Tensor
    feasible_mask: torch.Tensor
    task_valid: torch.Tensor | None = None
    budget_attempt_expected_steps: torch.Tensor | None = None
    budget_attempt_initial_cost: torch.Tensor | None = None
    contract_version: str = SNAPSHOT_CONTRACT_VERSION

    def __post_init__(self) -> None:
        active_target_id = _clone_tensor(self.active_target_id, name="active_target_id")
        task_owner_robot_id = _clone_tensor(self.task_owner_robot_id, name="task_owner_robot_id")
        pair_state = _clone_tensor(self.pair_state, name="pair_state")
        budget_attempt_target = _clone_tensor(self.budget_attempt_target, name="budget_attempt_target")
        budget_attempt_steps = _clone_tensor(self.budget_attempt_steps, name="budget_attempt_steps")
        budget_attempt_budget_steps = _clone_tensor(
            self.budget_attempt_budget_steps,
            name="budget_attempt_budget_steps",
        )
        viewpoints_covered = _clone_tensor(self.viewpoints_covered, name="viewpoints_covered")
        available_mask = _clone_tensor(self.available_mask, name="available_mask")
        feasible_mask = _clone_tensor(self.feasible_mask, name="feasible_mask")

        if active_target_id.ndim != 2:
            raise ValueError(f"active_target_id must have rank 2 [E,M], got {tuple(active_target_id.shape)}")
        num_envs, num_robots = (int(active_target_id.shape[0]), int(active_target_id.shape[1]))
        if task_owner_robot_id.ndim != 2:
            raise ValueError(
                "task_owner_robot_id must have rank 2 [E,N], "
                f"got {tuple(task_owner_robot_id.shape)}"
            )
        num_tasks = int(task_owner_robot_id.shape[1])
        device = active_target_id.device

        task_valid = _clone_optional_tensor(self.task_valid, name="task_valid")
        if task_valid is None:
            task_valid = torch.ones(num_envs, num_tasks, dtype=torch.bool, device=device)
        budget_attempt_expected_steps = _clone_optional_tensor(
            self.budget_attempt_expected_steps,
            name="budget_attempt_expected_steps",
        )
        budget_attempt_initial_cost = _clone_optional_tensor(
            self.budget_attempt_initial_cost,
            name="budget_attempt_initial_cost",
        )
        episode_generation = _normalize_episode_generation(
            self.episode_generation,
            num_envs=num_envs,
            device=device,
        )

        object.__setattr__(self, "snapshot_generation", int(self.snapshot_generation))
        object.__setattr__(self, "episode_generation", episode_generation)
        object.__setattr__(self, "active_target_id", active_target_id)
        object.__setattr__(self, "task_owner_robot_id", task_owner_robot_id)
        object.__setattr__(self, "pair_state", pair_state)
        object.__setattr__(self, "budget_attempt_target", budget_attempt_target)
        object.__setattr__(self, "budget_attempt_steps", budget_attempt_steps)
        object.__setattr__(self, "budget_attempt_budget_steps", budget_attempt_budget_steps)
        object.__setattr__(self, "viewpoints_covered", viewpoints_covered)
        object.__setattr__(self, "available_mask", available_mask)
        object.__setattr__(self, "feasible_mask", feasible_mask)
        object.__setattr__(self, "task_valid", task_valid)
        object.__setattr__(self, "budget_attempt_expected_steps", budget_attempt_expected_steps)
        object.__setattr__(self, "budget_attempt_initial_cost", budget_attempt_initial_cost)
        object.__setattr__(self, "contract_version", str(self.contract_version))

        validate_lifecycle_decision_snapshot(self)

    @property
    def num_envs(self) -> int:
        return int(self.active_target_id.shape[0])

    @property
    def num_robots(self) -> int:
        return int(self.active_target_id.shape[1])

    @property
    def num_tasks(self) -> int:
        return int(self.task_owner_robot_id.shape[1])

    @property
    def device(self) -> torch.device:
        return self.active_target_id.device


@dataclass(frozen=True)
class LifecycleSnapshotDerivedTensors:
    """Validated derived tensors used internally by pure builders."""

    task_owned_by_self: torch.Tensor
    self_active_target: torch.Tensor
    task_owned_by_teammate: torch.Tensor
    self_pair_failed_or_released: torch.Tensor
    active_robot: torch.Tensor

    def __post_init__(self) -> None:
        object.__setattr__(self, "task_owned_by_self", _clone_tensor(self.task_owned_by_self, name="task_owned_by_self"))
        object.__setattr__(self, "self_active_target", _clone_tensor(self.self_active_target, name="self_active_target"))
        object.__setattr__(
            self,
            "task_owned_by_teammate",
            _clone_tensor(self.task_owned_by_teammate, name="task_owned_by_teammate"),
        )
        object.__setattr__(
            self,
            "self_pair_failed_or_released",
            _clone_tensor(self.self_pair_failed_or_released, name="self_pair_failed_or_released"),
        )
        object.__setattr__(self, "active_robot", _clone_tensor(self.active_robot, name="active_robot"))


@dataclass(frozen=True)
class ActorLifecycleTensorResult:
    """Pure actor lifecycle tensor block."""

    snapshot_generation: int
    actor_lifecycle_features: torch.Tensor
    actor_lifecycle_flat: torch.Tensor
    feature_order: tuple[str, str, str] = ACTOR_LIFECYCLE_FEATURE_ORDER
    schema_version: str = ACTOR_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_generation", int(self.snapshot_generation))
        object.__setattr__(
            self,
            "actor_lifecycle_features",
            _clone_tensor(self.actor_lifecycle_features, name="actor_lifecycle_features"),
        )
        object.__setattr__(
            self,
            "actor_lifecycle_flat",
            _clone_tensor(self.actor_lifecycle_flat, name="actor_lifecycle_flat"),
        )
        object.__setattr__(self, "feature_order", tuple(str(item) for item in self.feature_order))
        object.__setattr__(self, "schema_version", str(self.schema_version))


@dataclass(frozen=True)
class CriticBudgetTensorResult:
    """Pure critic/shared budget tensor block."""

    snapshot_generation: int
    critic_budget_features: torch.Tensor
    critic_budget_flat: torch.Tensor
    feature_order: tuple[str, str] = CRITIC_BUDGET_FEATURE_ORDER
    schema_version: str = CRITIC_BUDGET_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_generation", int(self.snapshot_generation))
        object.__setattr__(
            self,
            "critic_budget_features",
            _clone_tensor(self.critic_budget_features, name="critic_budget_features"),
        )
        object.__setattr__(
            self,
            "critic_budget_flat",
            _clone_tensor(self.critic_budget_flat, name="critic_budget_flat"),
        )
        object.__setattr__(self, "feature_order", tuple(str(item) for item in self.feature_order))
        object.__setattr__(self, "schema_version", str(self.schema_version))


@dataclass(frozen=True)
class LifecycleAvailableActionsResult:
    """Pure available-action mask tensor block for one lifecycle decision snapshot."""

    snapshot_generation: int
    available_actions: torch.Tensor
    mask_contract_version: str
    base_target_mask: torch.Tensor | None = None
    idle_target_mask: torch.Tensor | None = None
    executing_target_mask: torch.Tensor | None = None
    noop_mask: torch.Tensor | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_generation", int(self.snapshot_generation))
        object.__setattr__(
            self,
            "available_actions",
            _clone_tensor(self.available_actions, name="available_actions"),
        )
        object.__setattr__(self, "mask_contract_version", str(self.mask_contract_version))
        object.__setattr__(
            self,
            "base_target_mask",
            _clone_optional_tensor(self.base_target_mask, name="base_target_mask"),
        )
        object.__setattr__(
            self,
            "idle_target_mask",
            _clone_optional_tensor(self.idle_target_mask, name="idle_target_mask"),
        )
        object.__setattr__(
            self,
            "executing_target_mask",
            _clone_optional_tensor(self.executing_target_mask, name="executing_target_mask"),
        )
        object.__setattr__(
            self,
            "noop_mask",
            _clone_optional_tensor(self.noop_mask, name="noop_mask"),
        )


def capture_lifecycle_decision_snapshot(
    *,
    snapshot_generation: int,
    episode_generation: int | torch.Tensor,
    active_target_id: torch.Tensor,
    task_owner_robot_id: torch.Tensor,
    pair_state: torch.Tensor,
    budget_attempt_target: torch.Tensor,
    budget_attempt_steps: torch.Tensor,
    budget_attempt_budget_steps: torch.Tensor,
    viewpoints_covered: torch.Tensor,
    available_mask: torch.Tensor,
    feasible_mask: torch.Tensor,
    task_valid: torch.Tensor | None = None,
    budget_attempt_expected_steps: torch.Tensor | None = None,
    budget_attempt_initial_cost: torch.Tensor | None = None,
) -> LifecycleDecisionSnapshot:
    """Copy one decision state into a validated no-alias snapshot."""

    return LifecycleDecisionSnapshot(
        snapshot_generation=snapshot_generation,
        episode_generation=episode_generation,
        active_target_id=active_target_id,
        task_owner_robot_id=task_owner_robot_id,
        pair_state=pair_state,
        budget_attempt_target=budget_attempt_target,
        budget_attempt_steps=budget_attempt_steps,
        budget_attempt_budget_steps=budget_attempt_budget_steps,
        viewpoints_covered=viewpoints_covered,
        available_mask=available_mask,
        feasible_mask=feasible_mask,
        task_valid=task_valid,
        budget_attempt_expected_steps=budget_attempt_expected_steps,
        budget_attempt_initial_cost=budget_attempt_initial_cost,
    )


def capture_lifecycle_decision_snapshot_from_mappings(
    *,
    snapshot_generation: int,
    episode_generation: int | torch.Tensor,
    resolver_snapshot: Mapping[str, Any],
    budget_state: Mapping[str, Any],
    assignment_problem: Mapping[str, Any],
    task_valid: torch.Tensor | None = None,
) -> LifecycleDecisionSnapshot:
    """Capture from resolver, wrapper-budget, and assignment-problem mappings."""

    active_target_id = resolver_snapshot["active_target_id"]
    task_owner_robot_id = resolver_snapshot["task_owner_robot_id"]
    pair_state = resolver_snapshot["pair_state"]

    def _budget_value(public_key: str, private_key: str) -> torch.Tensor | None:
        value = budget_state.get(public_key)
        if value is None:
            value = budget_state.get(private_key)
        return value

    budget_attempt_target = _budget_value("budget_attempt_target", "_budget_attempt_target")
    budget_attempt_steps = _budget_value("budget_attempt_steps", "_budget_attempt_steps")
    budget_attempt_budget_steps = _budget_value("budget_attempt_budget_steps", "_budget_attempt_budget_steps")
    if budget_attempt_target is None or budget_attempt_steps is None or budget_attempt_budget_steps is None:
        raise KeyError(
            "budget_state must contain budget_attempt_target, budget_attempt_steps, "
            "and budget_attempt_budget_steps, with or without leading underscores"
        )

    return capture_lifecycle_decision_snapshot(
        snapshot_generation=snapshot_generation,
        episode_generation=episode_generation,
        active_target_id=active_target_id,
        task_owner_robot_id=task_owner_robot_id,
        pair_state=pair_state,
        budget_attempt_target=budget_attempt_target,
        budget_attempt_steps=budget_attempt_steps,
        budget_attempt_budget_steps=budget_attempt_budget_steps,
        budget_attempt_expected_steps=_budget_value(
            "budget_attempt_expected_steps",
            "_budget_attempt_expected_steps",
        ),
        budget_attempt_initial_cost=_budget_value(
            "budget_attempt_initial_cost",
            "_budget_attempt_initial_cost",
        ),
        viewpoints_covered=assignment_problem["viewpoints_covered"],
        available_mask=assignment_problem["available_mask"],
        feasible_mask=assignment_problem["feasible_mask"],
        task_valid=task_valid,
    )


def validate_lifecycle_decision_snapshot(snapshot: LifecycleDecisionSnapshot) -> LifecycleSnapshotDerivedTensors:
    """Validate frozen snapshot invariants and return derived tensors."""

    num_envs = snapshot.num_envs
    num_robots = snapshot.num_robots
    num_tasks = snapshot.num_tasks
    device = snapshot.device

    _require_shape(snapshot.active_target_id, (num_envs, num_robots), name="active_target_id")
    _require_shape(snapshot.task_owner_robot_id, (num_envs, num_tasks), name="task_owner_robot_id")
    _require_shape(snapshot.pair_state, (num_envs, num_robots, num_tasks), name="pair_state")
    _require_shape(snapshot.budget_attempt_target, (num_envs, num_robots), name="budget_attempt_target")
    _require_shape(snapshot.budget_attempt_steps, (num_envs, num_robots), name="budget_attempt_steps")
    _require_shape(snapshot.budget_attempt_budget_steps, (num_envs, num_robots), name="budget_attempt_budget_steps")
    _require_shape(snapshot.viewpoints_covered, (num_envs, num_tasks), name="viewpoints_covered")
    _require_shape(snapshot.available_mask, (num_envs, num_robots, num_tasks), name="available_mask")
    _require_shape(snapshot.feasible_mask, (num_envs, num_robots, num_tasks), name="feasible_mask")
    _require_shape(snapshot.task_valid, (num_envs, num_tasks), name="task_valid")
    _require_shape(snapshot.episode_generation, (num_envs,), name="episode_generation")
    if snapshot.budget_attempt_expected_steps is not None:
        _require_shape(snapshot.budget_attempt_expected_steps, (num_envs, num_robots), name="budget_attempt_expected_steps")
    if snapshot.budget_attempt_initial_cost is not None:
        _require_shape(snapshot.budget_attempt_initial_cost, (num_envs, num_robots), name="budget_attempt_initial_cost")

    tensor_by_name = {
        "active_target_id": snapshot.active_target_id,
        "task_owner_robot_id": snapshot.task_owner_robot_id,
        "pair_state": snapshot.pair_state,
        "budget_attempt_target": snapshot.budget_attempt_target,
        "budget_attempt_steps": snapshot.budget_attempt_steps,
        "budget_attempt_budget_steps": snapshot.budget_attempt_budget_steps,
        "viewpoints_covered": snapshot.viewpoints_covered,
        "available_mask": snapshot.available_mask,
        "feasible_mask": snapshot.feasible_mask,
        "task_valid": snapshot.task_valid,
        "episode_generation": snapshot.episode_generation,
    }
    if snapshot.budget_attempt_expected_steps is not None:
        tensor_by_name["budget_attempt_expected_steps"] = snapshot.budget_attempt_expected_steps
    if snapshot.budget_attempt_initial_cost is not None:
        tensor_by_name["budget_attempt_initial_cost"] = snapshot.budget_attempt_initial_cost
    for name, tensor in tensor_by_name.items():
        _require_device(tensor, device, name=name)

    for name in (
        "active_target_id",
        "task_owner_robot_id",
        "pair_state",
        "budget_attempt_target",
        "budget_attempt_steps",
        "budget_attempt_budget_steps",
        "episode_generation",
    ):
        _require_dtype(tensor_by_name[name], torch.long, name=name)
    for name in ("viewpoints_covered", "available_mask", "feasible_mask", "task_valid"):
        _require_dtype(tensor_by_name[name], torch.bool, name=name)
    if snapshot.budget_attempt_expected_steps is not None:
        _require_dtype(snapshot.budget_attempt_expected_steps, torch.long, name="budget_attempt_expected_steps")
    if snapshot.budget_attempt_initial_cost is not None:
        _require_dtype(snapshot.budget_attempt_initial_cost, torch.float32, name="budget_attempt_initial_cost")

    invalid_active = (snapshot.active_target_id != NO_TARGET) & (
        (snapshot.active_target_id < 0) | (snapshot.active_target_id >= num_tasks)
    )
    if bool(invalid_active.any()):
        raise ValueError(
            "active_target_id must contain NO_TARGET or valid target ids; bad indices "
            f"{_format_bad_indices(invalid_active)}"
        )
    invalid_owner = (snapshot.task_owner_robot_id != NO_OWNER) & (
        (snapshot.task_owner_robot_id < 0) | (snapshot.task_owner_robot_id >= num_robots)
    )
    if bool(invalid_owner.any()):
        raise ValueError(
            "task_owner_robot_id must contain NO_OWNER or valid robot ids; bad indices "
            f"{_format_bad_indices(invalid_owner)}"
        )
    invalid_budget_target = (snapshot.budget_attempt_target != NO_TARGET) & (
        (snapshot.budget_attempt_target < 0) | (snapshot.budget_attempt_target >= num_tasks)
    )
    if bool(invalid_budget_target.any()):
        raise ValueError(
            "budget_attempt_target must contain NO_TARGET or valid target ids; bad indices "
            f"{_format_bad_indices(invalid_budget_target)}"
        )
    invalid_pair_state = torch.ones_like(snapshot.pair_state, dtype=torch.bool)
    for state in _VALID_PAIR_STATES:
        invalid_pair_state &= snapshot.pair_state != int(state)
    if bool(invalid_pair_state.any()):
        raise ValueError(
            "pair_state contains values outside known resolver pair states; bad indices "
            f"{_format_bad_indices(invalid_pair_state)}"
        )

    task_ids = torch.arange(num_tasks, dtype=torch.long, device=device).view(1, 1, num_tasks)
    robot_ids = torch.arange(num_robots, dtype=torch.long, device=device).view(1, num_robots, 1)
    self_active_target = snapshot.active_target_id.unsqueeze(-1) == task_ids
    task_owned_by_self = snapshot.task_owner_robot_id.unsqueeze(1) == robot_ids
    if not bool(torch.equal(task_owned_by_self, self_active_target)):
        mismatch = task_owned_by_self ^ self_active_target
        raise ValueError(
            "ownership-active invariant failed: task_owned_by_self must equal self_active_target; "
            f"bad indices {_format_bad_indices(mismatch)}"
        )
    active_robot = snapshot.active_target_id != NO_TARGET
    active_pair_ok = torch.where(
        self_active_target,
        snapshot.pair_state == PAIR_ACTIVE,
        torch.ones_like(self_active_target, dtype=torch.bool),
    )
    if not bool(active_pair_ok.all()):
        bad = ~active_pair_ok
        raise ValueError(
            "active pair invariant failed: active targets must have PAIR_ACTIVE pair_state; "
            f"bad indices {_format_bad_indices(bad)}"
        )
    stray_active_pair = (snapshot.pair_state == PAIR_ACTIVE) & (~self_active_target)
    if bool(stray_active_pair.any()):
        raise ValueError(
            "active pair invariant failed: PAIR_ACTIVE must match active_target_id; "
            f"bad indices {_format_bad_indices(stray_active_pair)}"
        )
    active_invalid_task_slot = self_active_target & (~snapshot.task_valid.unsqueeze(1))
    if bool(active_invalid_task_slot.any()):
        raise ValueError(
            "active target invariant failed: active targets must refer to valid task slots; "
            f"bad indices {_format_bad_indices(active_invalid_task_slot)}"
        )
    active_covered_target = self_active_target & snapshot.viewpoints_covered.unsqueeze(1)
    if bool(active_covered_target.any()):
        raise ValueError(
            "active target invariant failed: active targets must not already be covered; "
            f"bad indices {_format_bad_indices(active_covered_target)}"
        )

    inactive_robot = ~active_robot
    active_budget_target_mismatch = active_robot & (snapshot.budget_attempt_target != snapshot.active_target_id)
    if bool(active_budget_target_mismatch.any()):
        raise ValueError(
            "budget-target alignment failed: active budget_attempt_target must equal active_target_id; "
            f"bad indices {_format_bad_indices(active_budget_target_mismatch)}"
        )
    active_bad_steps = active_robot & (snapshot.budget_attempt_steps < 1)
    if bool(active_bad_steps.any()):
        raise ValueError(
            "budget-target alignment failed: active robots must have budget_attempt_steps >= 1; "
            f"bad indices {_format_bad_indices(active_bad_steps)}"
        )
    active_bad_budget = active_robot & (snapshot.budget_attempt_budget_steps < 1)
    if bool(active_bad_budget.any()):
        raise ValueError(
            "budget-target alignment failed: active robots must have budget_attempt_budget_steps >= 1; "
            f"bad indices {_format_bad_indices(active_bad_budget)}"
        )
    inactive_budget_bad = inactive_robot & (
        (snapshot.budget_attempt_target != NO_TARGET)
        | (snapshot.budget_attempt_steps != 0)
        | (snapshot.budget_attempt_budget_steps != 0)
    )
    if bool(inactive_budget_bad.any()):
        raise ValueError(
            "inactive budget invariant failed: idle robots must have target=-1, steps=0, budget_steps=0; "
            f"bad indices {_format_bad_indices(inactive_budget_bad)}"
        )
    if snapshot.budget_attempt_expected_steps is not None:
        inactive_expected_bad = inactive_robot & (snapshot.budget_attempt_expected_steps != 0)
        if bool(inactive_expected_bad.any()):
            raise ValueError(
                "inactive budget invariant failed: idle robots must have budget_attempt_expected_steps=0; "
                f"bad indices {_format_bad_indices(inactive_expected_bad)}"
            )
    if snapshot.budget_attempt_initial_cost is not None:
        inactive_cost_bad = inactive_robot & (snapshot.budget_attempt_initial_cost != 0.0)
        if bool(inactive_cost_bad.any()):
            raise ValueError(
                "inactive budget invariant failed: idle robots must have budget_attempt_initial_cost=0; "
                f"bad indices {_format_bad_indices(inactive_cost_bad)}"
            )

    task_owned_by_teammate = (snapshot.task_owner_robot_id.unsqueeze(1) != NO_OWNER) & (
        snapshot.task_owner_robot_id.unsqueeze(1) != robot_ids
    )
    self_pair_failed_or_released = (snapshot.pair_state == PAIR_FAILED_BUDGET) | (
        snapshot.pair_state == PAIR_RELEASED_BUDGET
    )
    return LifecycleSnapshotDerivedTensors(
        task_owned_by_self=task_owned_by_self,
        self_active_target=self_active_target,
        task_owned_by_teammate=task_owned_by_teammate,
        self_pair_failed_or_released=self_pair_failed_or_released,
        active_robot=active_robot,
    )


def build_actor_lifecycle_tensors(snapshot: LifecycleDecisionSnapshot) -> ActorLifecycleTensorResult:
    """Build the frozen [E,M,N,3] actor lifecycle add-on block."""

    derived = validate_lifecycle_decision_snapshot(snapshot)
    features = torch.stack(
        (
            derived.self_active_target,
            derived.task_owned_by_teammate,
            derived.self_pair_failed_or_released,
        ),
        dim=-1,
    ).to(dtype=torch.float32)
    flat = features.reshape(snapshot.num_envs, snapshot.num_robots, snapshot.num_tasks * len(ACTOR_LIFECYCLE_FEATURE_ORDER))
    return ActorLifecycleTensorResult(
        snapshot_generation=snapshot.snapshot_generation,
        actor_lifecycle_features=features,
        actor_lifecycle_flat=flat,
    )


def build_critic_budget_tensors(snapshot: LifecycleDecisionSnapshot) -> CriticBudgetTensorResult:
    """Build the frozen [E,M,2] critic/shared budget statistic block."""

    validate_lifecycle_decision_snapshot(snapshot)
    active = snapshot.active_target_id != NO_TARGET
    denominator = snapshot.budget_attempt_budget_steps.clamp(min=1).to(dtype=torch.float32)
    progress = torch.clamp(snapshot.budget_attempt_steps.to(dtype=torch.float32) / denominator, 0.0, 1.0)
    step_fraction = torch.ones_like(progress) / denominator
    zeros = torch.zeros_like(progress)
    progress = torch.where(active, progress, zeros)
    step_fraction = torch.where(active, step_fraction, zeros)
    features = torch.stack((progress, step_fraction), dim=-1)
    flat = features.reshape(snapshot.num_envs, snapshot.num_robots * len(CRITIC_BUDGET_FEATURE_ORDER))
    return CriticBudgetTensorResult(
        snapshot_generation=snapshot.snapshot_generation,
        critic_budget_features=features,
        critic_budget_flat=flat,
    )


def _build_base_target_mask(snapshot: LifecycleDecisionSnapshot) -> torch.Tensor:
    return (
        snapshot.task_valid.unsqueeze(1)
        & snapshot.available_mask
        & snapshot.feasible_mask
        & (~snapshot.viewpoints_covered.unsqueeze(1))
    )


def _finalize_available_actions_result(
    *,
    snapshot: LifecycleDecisionSnapshot,
    target_mask: torch.Tensor,
    mask_contract_version: str,
    base_target_mask: torch.Tensor | None,
    idle_target_mask: torch.Tensor | None,
    executing_target_mask: torch.Tensor | None,
) -> LifecycleAvailableActionsResult:
    noop_mask = torch.ones(snapshot.num_envs, snapshot.num_robots, 1, dtype=torch.float32, device=snapshot.device)
    available_actions = torch.cat((target_mask.to(dtype=torch.float32), noop_mask), dim=-1)
    expected_shape = (snapshot.num_envs, snapshot.num_robots, snapshot.num_tasks + 1)
    _require_shape(available_actions, expected_shape, name="available_actions")
    if bool((available_actions.sum(dim=-1) <= 0.0).any()):
        raise ValueError(
            "available_actions invariant failed: every robot must have at least one available action"
        )
    if not bool(torch.all(available_actions[..., -1] > 0.0)):
        raise ValueError("available_actions invariant failed: noop must always be available")
    return LifecycleAvailableActionsResult(
        snapshot_generation=snapshot.snapshot_generation,
        available_actions=available_actions,
        mask_contract_version=mask_contract_version,
        base_target_mask=base_target_mask.to(dtype=torch.float32) if base_target_mask is not None else None,
        idle_target_mask=idle_target_mask.to(dtype=torch.float32) if idle_target_mask is not None else None,
        executing_target_mask=executing_target_mask.to(dtype=torch.float32)
        if executing_target_mask is not None
        else None,
        noop_mask=noop_mask,
    )


def build_lifecycle_ablation_available_action_tensors(
    snapshot: LifecycleDecisionSnapshot,
) -> LifecycleAvailableActionsResult:
    """Build resolver-disabled lifecycle-ablation physical/noop available actions from one snapshot."""

    validate_lifecycle_decision_snapshot(snapshot)
    target_mask = snapshot.available_mask.to(dtype=torch.bool)
    return _finalize_available_actions_result(
        snapshot=snapshot,
        target_mask=target_mask,
        mask_contract_version=LIFECYCLE_ABLATION_MASK_VERSION,
        base_target_mask=target_mask,
        idle_target_mask=target_mask,
        executing_target_mask=None,
    )


def build_lifecycle_contract_c_available_action_tensors(
    snapshot: LifecycleDecisionSnapshot,
) -> LifecycleAvailableActionsResult:
    """Build the frozen Contract C lifecycle-aware available-action mask."""

    derived = validate_lifecycle_decision_snapshot(snapshot)
    base_target_mask = _build_base_target_mask(snapshot)
    idle_target_mask = (
        base_target_mask
        & (~derived.task_owned_by_teammate)
        & (~derived.self_pair_failed_or_released)
    )
    executing_target_mask = derived.self_active_target
    target_mask = torch.where(
        derived.active_robot.unsqueeze(-1),
        executing_target_mask,
        idle_target_mask,
    )
    return _finalize_available_actions_result(
        snapshot=snapshot,
        target_mask=target_mask,
        mask_contract_version=LIFECYCLE_CONTRACT_C_MASK_VERSION,
        base_target_mask=base_target_mask,
        idle_target_mask=idle_target_mask,
        executing_target_mask=executing_target_mask,
    )


def actor_lifecycle_addon_dim(num_tasks: int) -> int:
    return int(num_tasks) * len(ACTOR_LIFECYCLE_FEATURE_ORDER)


def critic_budget_addon_dim(num_robots: int) -> int:
    return int(num_robots) * len(CRITIC_BUDGET_FEATURE_ORDER)


def legacy_actor_dim(num_robots: int, num_tasks: int) -> int:
    return 100 + 3 * int(num_robots) + 16 * int(num_tasks)


def lifecycle_actor_dim(num_robots: int, num_tasks: int) -> int:
    return legacy_actor_dim(num_robots, num_tasks) + actor_lifecycle_addon_dim(num_tasks)


def shared_option_a_dim(num_robots: int, num_tasks: int) -> int:
    return int(num_robots) * lifecycle_actor_dim(num_robots, num_tasks) + critic_budget_addon_dim(num_robots)


__all__ = [
    "ACTOR_LIFECYCLE_FEATURE_ORDER",
    "ACTOR_SCHEMA_VERSION",
    "CRITIC_BUDGET_FEATURE_ORDER",
    "CRITIC_BUDGET_SCHEMA_VERSION",
    "LIFECYCLE_ABLATION_MASK_VERSION",
    "LIFECYCLE_CONTRACT_C_MASK_VERSION",
    "SNAPSHOT_CONTRACT_VERSION",
    "ActorLifecycleTensorResult",
    "CriticBudgetTensorResult",
    "LifecycleAvailableActionsResult",
    "LifecycleDecisionSnapshot",
    "LifecycleSnapshotDerivedTensors",
    "actor_lifecycle_addon_dim",
    "build_actor_lifecycle_tensors",
    "build_critic_budget_tensors",
    "build_lifecycle_ablation_available_action_tensors",
    "build_lifecycle_contract_c_available_action_tensors",
    "capture_lifecycle_decision_snapshot",
    "capture_lifecycle_decision_snapshot_from_mappings",
    "critic_budget_addon_dim",
    "legacy_actor_dim",
    "lifecycle_actor_dim",
    "shared_option_a_dim",
    "validate_lifecycle_decision_snapshot",
]
