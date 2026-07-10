"""Pure tests for lifecycle decision snapshots and tensor builders.

These tests use synthetic tensors only. They do not launch Isaac Sim, construct
an environment, run playback/evaluation, train, or integrate lifecycle tensors
into HARL runtime paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from assignment_lifecycle_observation import (  # noqa: E402
    ACTOR_LIFECYCLE_FEATURE_ORDER,
    CRITIC_BUDGET_FEATURE_ORDER,
    actor_lifecycle_addon_dim,
    build_actor_lifecycle_tensors,
    build_critic_budget_tensors,
    capture_lifecycle_decision_snapshot,
    critic_budget_addon_dim,
    legacy_actor_dim,
    lifecycle_actor_dim,
    shared_option_a_dim,
)
from assignment_lifecycle_resolver import (  # noqa: E402
    NO_OWNER,
    NO_TARGET,
    PAIR_ACTIVE,
    PAIR_COMPLETED,
    PAIR_FAILED_BUDGET,
    PAIR_NONE,
    PAIR_RELEASED_BUDGET,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_tensor_equal(actual: torch.Tensor, expected: torch.Tensor, message: str) -> None:
    if not torch.equal(actual, expected):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def _assert_close(actual: torch.Tensor, expected: torch.Tensor, message: str, *, atol: float = 1.0e-6) -> None:
    if not torch.allclose(actual, expected, atol=atol, rtol=0.0):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def _expect_raises(func, expected_substring: str) -> None:
    try:
        func()
    except (TypeError, ValueError) as exc:
        if expected_substring not in str(exc):
            raise AssertionError(f"expected error containing {expected_substring!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected error containing {expected_substring!r}")


def _empty_state(num_envs: int, num_robots: int, num_tasks: int) -> dict[str, torch.Tensor]:
    return {
        "active_target_id": torch.full((num_envs, num_robots), NO_TARGET, dtype=torch.long),
        "task_owner_robot_id": torch.full((num_envs, num_tasks), NO_OWNER, dtype=torch.long),
        "pair_state": torch.full((num_envs, num_robots, num_tasks), PAIR_NONE, dtype=torch.long),
        "budget_attempt_target": torch.full((num_envs, num_robots), NO_TARGET, dtype=torch.long),
        "budget_attempt_steps": torch.zeros(num_envs, num_robots, dtype=torch.long),
        "budget_attempt_budget_steps": torch.zeros(num_envs, num_robots, dtype=torch.long),
        "viewpoints_covered": torch.zeros(num_envs, num_tasks, dtype=torch.bool),
        "available_mask": torch.ones(num_envs, num_robots, num_tasks, dtype=torch.bool),
        "feasible_mask": torch.ones(num_envs, num_robots, num_tasks, dtype=torch.bool),
    }


def _set_active(
    state: dict[str, torch.Tensor],
    *,
    env_id: int,
    robot_id: int,
    target_id: int,
    steps: int = 1,
    budget_steps: int = 5,
) -> None:
    state["active_target_id"][env_id, robot_id] = target_id
    state["task_owner_robot_id"][env_id, target_id] = robot_id
    state["pair_state"][env_id, robot_id, target_id] = PAIR_ACTIVE
    state["budget_attempt_target"][env_id, robot_id] = target_id
    state["budget_attempt_steps"][env_id, robot_id] = steps
    state["budget_attempt_budget_steps"][env_id, robot_id] = budget_steps


def _snapshot(
    state: dict[str, torch.Tensor],
    *,
    generation: int = 7,
    episode_generation: int | torch.Tensor = 3,
):
    return capture_lifecycle_decision_snapshot(
        snapshot_generation=generation,
        episode_generation=episode_generation,
        active_target_id=state["active_target_id"],
        task_owner_robot_id=state["task_owner_robot_id"],
        pair_state=state["pair_state"],
        budget_attempt_target=state["budget_attempt_target"],
        budget_attempt_steps=state["budget_attempt_steps"],
        budget_attempt_budget_steps=state["budget_attempt_budget_steps"],
        viewpoints_covered=state["viewpoints_covered"],
        available_mask=state["available_mask"],
        feasible_mask=state["feasible_mask"],
        task_valid=state.get("task_valid"),
        budget_attempt_expected_steps=state.get("budget_attempt_expected_steps"),
        budget_attempt_initial_cost=state.get("budget_attempt_initial_cost"),
    )


def _case_idle_snapshot() -> dict[str, Any]:
    state = _empty_state(1, 3, 5)
    snapshot = _snapshot(state)
    actor = build_actor_lifecycle_tensors(snapshot)
    critic = build_critic_budget_tensors(snapshot)
    actor_repeat = build_actor_lifecycle_tensors(snapshot)
    critic_repeat = build_critic_budget_tensors(snapshot)
    _assert_tensor_equal(actor.actor_lifecycle_features, torch.zeros(1, 3, 5, 3), "idle actor features")
    _assert_tensor_equal(actor.actor_lifecycle_flat, torch.zeros(1, 3, 15), "idle actor flat")
    _assert_tensor_equal(critic.critic_budget_features, torch.zeros(1, 3, 2), "idle critic budget")
    _assert_tensor_equal(critic.critic_budget_flat, torch.zeros(1, 6), "idle critic budget flat")
    _assert_tensor_equal(actor.actor_lifecycle_features, actor_repeat.actor_lifecycle_features, "idle actor determinism")
    _assert_tensor_equal(critic.critic_budget_features, critic_repeat.critic_budget_features, "idle critic determinism")
    return {"case": "idle_snapshot", "passed": True}


def _case_active_claim() -> dict[str, Any]:
    state = _empty_state(1, 3, 5)
    _set_active(state, env_id=0, robot_id=1, target_id=3, steps=2, budget_steps=8)
    snapshot = _snapshot(state)
    actor = build_actor_lifecycle_tensors(snapshot)
    features = actor.actor_lifecycle_features

    _assert(float(features[0, 1, 3, 0].item()) == 1.0, "owner self_active_target missing")
    _assert(float(features[0, 1, 3, 1].item()) == 0.0, "owner should not see teammate ownership")
    _assert(float(features[0, 0, 3, 1].item()) == 1.0, "teammate-owned bit missing for robot 0")
    _assert(float(features[0, 2, 3, 1].item()) == 1.0, "teammate-owned bit missing for robot 2")
    _assert(int(snapshot.budget_attempt_target[0, 1].item()) == 3, "budget target did not match active target")
    return {"case": "active_claim", "passed": True}


def _case_multiple_robots_tasks_and_flatten_order() -> dict[str, Any]:
    state = _empty_state(2, 3, 5)
    _set_active(state, env_id=0, robot_id=0, target_id=1, steps=3, budget_steps=10)
    _set_active(state, env_id=0, robot_id=2, target_id=3, steps=4, budget_steps=11)
    _set_active(state, env_id=1, robot_id=1, target_id=2, steps=5, budget_steps=12)
    state["pair_state"][1, 0, 4] = PAIR_RELEASED_BUDGET

    snapshot = _snapshot(state, generation=9, episode_generation=torch.tensor([4, 5], dtype=torch.long))
    actor = build_actor_lifecycle_tensors(snapshot)

    expected_robot1_env0 = torch.tensor(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        dtype=torch.float32,
    )
    _assert_tensor_equal(actor.actor_lifecycle_flat[0, 1], expected_robot1_env0, "task-major flatten order")
    _assert(float(actor.actor_lifecycle_features[1, 0, 4, 2].item()) == 1.0, "released-pair bit missing")
    _assert_tensor_equal(snapshot.episode_generation, torch.tensor([4, 5], dtype=torch.long), "episode generation")
    return {"case": "multiple_robots_tasks_and_flatten_order", "passed": True}


def _case_failed_and_released_pair_encoding() -> dict[str, Any]:
    state = _empty_state(1, 3, 5)
    state["pair_state"][0, 0, 1] = PAIR_FAILED_BUDGET
    state["pair_state"][0, 1, 2] = PAIR_RELEASED_BUDGET
    state["pair_state"][0, 2, 3] = PAIR_COMPLETED
    snapshot = _snapshot(state)
    actor = build_actor_lifecycle_tensors(snapshot)
    features = actor.actor_lifecycle_features

    _assert(float(features[0, 0, 1, 2].item()) == 1.0, "failed budget pair should encode 1")
    _assert(float(features[0, 1, 2, 2].item()) == 1.0, "released budget pair should encode 1")
    _assert(float(features[0, 2, 3, 2].item()) == 0.0, "completed pair should encode 0")
    _assert(float(features[0, 2, 4, 2].item()) == 0.0, "none pair should encode 0")
    return {"case": "failed_and_released_pair_encoding", "passed": True}


def _case_budget_statistic_distinguishes_denominators() -> dict[str, Any]:
    state = _empty_state(1, 5, 5)
    _set_active(state, env_id=0, robot_id=0, target_id=0, steps=9, budget_steps=10)
    _set_active(state, env_id=0, robot_id=1, target_id=1, steps=90, budget_steps=100)
    _set_active(state, env_id=0, robot_id=2, target_id=2, steps=1, budget_steps=1)
    _set_active(state, env_id=0, robot_id=3, target_id=3, steps=1, budget_steps=1000)
    snapshot = _snapshot(state)
    critic = build_critic_budget_tensors(snapshot)
    features = critic.critic_budget_features

    _assert_close(features[0, 0, 0], features[0, 1, 0], "9/10 and 90/100 progress should match")
    _assert(float(features[0, 0, 1].item()) != float(features[0, 1, 1].item()), "step fractions should differ")
    _assert_close(features[0, 2], torch.tensor([1.0, 1.0]), "1/1 budget features")
    _assert_close(features[0, 3], torch.tensor([0.001, 0.001]), "1/1000 budget features", atol=1.0e-9)
    _assert_close(features[0, 4], torch.tensor([0.0, 0.0]), "inactive budget features")
    return {"case": "budget_statistic_distinguishes_denominators", "passed": True}


def _case_ownership_active_invariant_failure() -> dict[str, Any]:
    state = _empty_state(1, 2, 3)
    state["task_owner_robot_id"][0, 1] = 0
    _expect_raises(lambda: _snapshot(state), "ownership-active invariant")

    state = _empty_state(1, 2, 3)
    state["active_target_id"][0, 0] = 1
    state["task_owner_robot_id"][0, 1] = 1
    state["pair_state"][0, 0, 1] = PAIR_ACTIVE
    state["budget_attempt_target"][0, 0] = 1
    state["budget_attempt_steps"][0, 0] = 1
    state["budget_attempt_budget_steps"][0, 0] = 5
    _expect_raises(lambda: _snapshot(state), "ownership-active invariant")
    return {"case": "ownership_active_invariant_failure", "passed": True}


def _case_budget_target_alignment_failure() -> dict[str, Any]:
    state = _empty_state(1, 2, 3)
    _set_active(state, env_id=0, robot_id=0, target_id=1, steps=1, budget_steps=5)
    state["budget_attempt_target"][0, 0] = 2
    _expect_raises(lambda: _snapshot(state), "budget-target alignment")

    state = _empty_state(1, 2, 3)
    state["budget_attempt_target"][0, 0] = 1
    state["budget_attempt_steps"][0, 0] = 1
    state["budget_attempt_budget_steps"][0, 0] = 5
    _expect_raises(lambda: _snapshot(state), "inactive budget invariant")
    return {"case": "budget_target_alignment_failure", "passed": True}


def _case_reset_like_state() -> dict[str, Any]:
    state = _empty_state(2, 3, 5)
    _set_active(state, env_id=1, robot_id=2, target_id=4, steps=6, budget_steps=9)
    state["pair_state"][1, 0, 1] = PAIR_FAILED_BUDGET
    snapshot = _snapshot(state)
    actor = build_actor_lifecycle_tensors(snapshot)
    critic = build_critic_budget_tensors(snapshot)

    _assert_tensor_equal(actor.actor_lifecycle_features[0], torch.zeros(3, 5, 3), "reset-like env actor features")
    _assert_tensor_equal(critic.critic_budget_features[0], torch.zeros(3, 2), "reset-like env budget features")
    _assert(float(actor.actor_lifecycle_features[1, 2, 4, 0].item()) == 1.0, "other env active state changed")
    _assert(float(actor.actor_lifecycle_features[1, 0, 1, 2].item()) == 1.0, "other env failed pair changed")
    return {"case": "reset_like_state", "passed": True}


def _case_snapshot_immutability() -> dict[str, Any]:
    state = _empty_state(1, 3, 5)
    _set_active(state, env_id=0, robot_id=1, target_id=2, steps=4, budget_steps=7)
    snapshot = _snapshot(state, generation=101)
    actor = build_actor_lifecycle_tensors(snapshot)
    critic = build_critic_budget_tensors(snapshot)
    snapshot_before = {
        "active_target_id": snapshot.active_target_id.clone(),
        "task_owner_robot_id": snapshot.task_owner_robot_id.clone(),
        "pair_state": snapshot.pair_state.clone(),
        "budget_attempt_steps": snapshot.budget_attempt_steps.clone(),
        "budget_attempt_budget_steps": snapshot.budget_attempt_budget_steps.clone(),
        "viewpoints_covered": snapshot.viewpoints_covered.clone(),
        "available_mask": snapshot.available_mask.clone(),
        "feasible_mask": snapshot.feasible_mask.clone(),
    }
    actor_before = actor.actor_lifecycle_features.clone()
    critic_before = critic.critic_budget_features.clone()

    state["active_target_id"].fill_(4)
    state["task_owner_robot_id"].fill_(2)
    state["pair_state"].fill_(PAIR_RELEASED_BUDGET)
    state["budget_attempt_target"].fill_(4)
    state["budget_attempt_steps"].fill_(99)
    state["budget_attempt_budget_steps"].fill_(100)
    state["viewpoints_covered"].fill_(True)
    state["available_mask"].fill_(False)
    state["feasible_mask"].fill_(False)

    for name, expected in snapshot_before.items():
        _assert_tensor_equal(getattr(snapshot, name), expected, f"snapshot {name} aliased source")
    _assert_tensor_equal(actor.actor_lifecycle_features, actor_before, "actor output changed after source mutation")
    _assert_tensor_equal(critic.critic_budget_features, critic_before, "critic output changed after source mutation")
    return {"case": "snapshot_immutability", "passed": True}


def _case_generation_shape_dtype_and_dimensions() -> dict[str, Any]:
    state = _empty_state(2, 3, 5)
    snapshot = _snapshot(state, generation=55, episode_generation=torch.tensor([10, 11], dtype=torch.long))
    actor = build_actor_lifecycle_tensors(snapshot)
    critic = build_critic_budget_tensors(snapshot)
    actor_repeat = build_actor_lifecycle_tensors(snapshot)
    critic_repeat = build_critic_budget_tensors(snapshot)

    _assert(actor.snapshot_generation == 55, "actor generation mismatch")
    _assert(critic.snapshot_generation == 55, "critic generation mismatch")
    _assert(actor.snapshot_generation == snapshot.snapshot_generation, "actor did not propagate generation")
    _assert(critic.snapshot_generation == snapshot.snapshot_generation, "critic did not propagate generation")
    _assert(tuple(actor.actor_lifecycle_features.shape) == (2, 3, 5, 3), "actor unflattened shape")
    _assert(tuple(actor.actor_lifecycle_flat.shape) == (2, 3, 15), "actor flattened shape")
    _assert(tuple(critic.critic_budget_features.shape) == (2, 3, 2), "critic unflattened shape")
    _assert(tuple(critic.critic_budget_flat.shape) == (2, 6), "critic flattened shape")
    _assert(actor.actor_lifecycle_features.dtype == torch.float32, "actor dtype")
    _assert(critic.critic_budget_features.dtype == torch.float32, "critic dtype")
    _assert(str(actor.actor_lifecycle_features.device) == "cpu", "actor CPU device")
    _assert(str(critic.critic_budget_features.device) == "cpu", "critic CPU device")
    _assert_tensor_equal(actor.actor_lifecycle_features, actor_repeat.actor_lifecycle_features, "actor determinism")
    _assert_tensor_equal(critic.critic_budget_features, critic_repeat.critic_budget_features, "critic determinism")
    _assert(ACTOR_LIFECYCLE_FEATURE_ORDER == ("self_active_target", "task_owned_by_teammate", "self_pair_failed_or_released"), "actor feature order")
    _assert(CRITIC_BUDGET_FEATURE_ORDER == ("active_budget_progress_norm", "active_budget_step_fraction"), "critic feature order")
    _assert(actor_lifecycle_addon_dim(50) == 150, "actor lifecycle add-on dim")
    _assert(legacy_actor_dim(3, 50) == 909, "legacy actor dim")
    _assert(lifecycle_actor_dim(3, 50) == 1059, "future lifecycle actor dim")
    _assert(critic_budget_addon_dim(3) == 6, "critic budget add-on dim")
    _assert(shared_option_a_dim(3, 50) == 3183, "future shared dim")
    return {"case": "generation_shape_dtype_and_dimensions", "passed": True}


def _case_shape_device_dtype_validation() -> dict[str, Any]:
    state = _empty_state(1, 2, 3)
    bad_shape = dict(state)
    bad_shape["pair_state"] = torch.zeros(1, 2, 4, dtype=torch.long)
    _expect_raises(lambda: _snapshot(bad_shape), "pair_state must have shape")

    bad_dtype = dict(state)
    bad_dtype["available_mask"] = torch.ones(1, 2, 3, dtype=torch.float32)
    _expect_raises(lambda: _snapshot(bad_dtype), "available_mask must have dtype")

    bad_index = dict(state)
    bad_index["active_target_id"] = state["active_target_id"].clone()
    bad_index["active_target_id"][0, 0] = 3
    _expect_raises(lambda: _snapshot(bad_index), "active_target_id must contain")
    return {"case": "shape_device_dtype_validation", "passed": True}


def run_smoke() -> dict[str, Any]:
    cases = [
        _case_idle_snapshot(),
        _case_active_claim(),
        _case_multiple_robots_tasks_and_flatten_order(),
        _case_failed_and_released_pair_encoding(),
        _case_budget_statistic_distinguishes_denominators(),
        _case_ownership_active_invariant_failure(),
        _case_budget_target_alignment_failure(),
        _case_reset_like_state(),
        _case_snapshot_immutability(),
        _case_generation_shape_dtype_and_dimensions(),
        _case_shape_device_dtype_validation(),
    ]
    return {
        "status": "passed",
        "num_cases": len(cases),
        "cases": cases,
        "notes": [
            "synthetic CPU tensors only",
            "no Isaac Sim/AppLauncher/environment construction",
            "no HARL rollout/training/playback/evaluation",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Assignment lifecycle observation pure smoke passed: {result['num_cases']} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
