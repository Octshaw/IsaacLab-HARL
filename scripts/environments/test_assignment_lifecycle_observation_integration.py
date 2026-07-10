"""Lightweight integration tests for lifecycle actor/shared observation wiring.

These tests exercise the project-local HARL wrapper observation composition with
synthetic tensors only. They do not launch Isaac Sim, construct the real scan
environment, run training, run playback/evaluation, or change runtime masks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import gymnasium
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

from assignment_harl_wrapper import AssignmentHarlWrapper  # noqa: E402
from assignment_lifecycle_observation import (  # noqa: E402
    ACTOR_LIFECYCLE_FEATURE_ORDER,
    CRITIC_BUDGET_FEATURE_ORDER,
    build_critic_budget_tensors,
)
from assignment_lifecycle_resolver import (  # noqa: E402
    NO_OWNER,
    NO_TARGET,
    PAIR_ACTIVE,
    PAIR_FAILED_BUDGET,
    PAIR_RELEASED_BUDGET,
)
from assignment_rl_interface import make_assignment_action_mask  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_tensor_equal(actual: torch.Tensor, expected: torch.Tensor, message: str) -> None:
    if not torch.equal(actual, expected):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def _assert_close(actual: torch.Tensor, expected: torch.Tensor, message: str, *, atol: float = 1.0e-6) -> None:
    if not torch.allclose(actual, expected, atol=atol, rtol=0.0):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


class FakeAssignmentEnv:
    def __init__(
        self,
        *,
        profile: str,
        num_envs: int = 2,
        num_agents: int = 3,
        num_tasks: int = 50,
        config_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.num_envs = int(num_envs)
        self.num_viewpoints = int(num_tasks)
        self.device = torch.device("cpu")
        self.max_episode_length = 300
        self.possible_agents = tuple(f"agent_{index}" for index in range(num_agents))
        self.agents = list(self.possible_agents)
        self.cfg = SimpleNamespace(
            assignment_lifecycle_profile=profile,
            assignment_lifecycle_resolver_enabled=False,
            assignment_lifecycle_resolver_strict_proposals=True,
            assignment_lifecycle_resolver_log_diagnostics=False,
            assignment_lifecycle_resolver_output_dir=None,
            assignment_cooldown_enabled=False,
            assignment_cooldown_trigger_mode="streak",
            assignment_cooldown_apply_to_action_mask=True,
            assignment_cooldown_duration_steps=20,
            assignment_redirect_guardrail_enabled=False,
            assignment_failed_pair_memory_enabled=False,
            max_base_xy_step=(0.08, 0.10, 0.06),
            scene=SimpleNamespace(env_spacing=1.0),
        )
        for key, value in (config_overrides or {}).items():
            setattr(self.cfg, key, value)
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-float("inf"), float("inf"), shape=(96,), dtype=float)
            for agent in self.possible_agents
        }
        self._raw_obs = {
            agent: (
                torch.arange(self.num_envs * 96, dtype=torch.float32).reshape(self.num_envs, 96)
                + float(agent_index * 1000)
            )
            for agent_index, agent in enumerate(self.possible_agents)
        }
        self._problem = self._make_problem()

    @property
    def unwrapped(self) -> "FakeAssignmentEnv":
        return self

    def reset(self, *args: Any, **kwargs: Any) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
        del args, kwargs
        return {agent: obs.clone() for agent, obs in self._raw_obs.items()}, {}

    def get_assignment_problem(self) -> dict[str, torch.Tensor | int]:
        return {
            key: value.clone() if isinstance(value, torch.Tensor) else value
            for key, value in self._problem.items()
        }

    def _make_problem(self) -> dict[str, torch.Tensor | int]:
        env_offsets = torch.arange(self.num_envs, dtype=torch.float32).view(self.num_envs, 1, 1)
        task_ids = torch.arange(self.num_viewpoints, dtype=torch.float32).view(1, self.num_viewpoints, 1)
        viewpoint_pos = torch.cat(
            (
                task_ids.repeat(self.num_envs, 1, 1) / 100.0,
                env_offsets.repeat(1, self.num_viewpoints, 1),
                torch.ones(self.num_envs, self.num_viewpoints, 1),
            ),
            dim=-1,
        )
        viewpoint_quat = torch.zeros(self.num_envs, self.num_viewpoints, 4, dtype=torch.float32)
        viewpoint_quat[..., 0] = 1.0
        scanner_pos = torch.zeros(self.num_envs, len(self.possible_agents), 3, dtype=torch.float32)
        available = torch.ones(self.num_envs, len(self.possible_agents), self.num_viewpoints, dtype=torch.bool)
        feasible = torch.ones_like(available)
        cost = torch.arange(
            self.num_envs * len(self.possible_agents) * self.num_viewpoints,
            dtype=torch.float32,
        ).reshape(self.num_envs, len(self.possible_agents), self.num_viewpoints)
        return {
            "num_envs": self.num_envs,
            "num_agents": len(self.possible_agents),
            "num_viewpoints": self.num_viewpoints,
            "viewpoint_pos": viewpoint_pos,
            "viewpoint_quat": viewpoint_quat,
            "scanner_pos": scanner_pos,
            "viewpoints_covered": torch.zeros(self.num_envs, self.num_viewpoints, dtype=torch.bool),
            "available_mask": available,
            "feasible_mask": feasible,
            "static_geometric_feasible_mask": feasible.clone(),
            "cost_matrix": cost,
        }


def _contract_c_overrides() -> dict[str, Any]:
    return {
        "assignment_cooldown_enabled": True,
        "assignment_cooldown_trigger_mode": "budget",
        "assignment_cooldown_apply_to_action_mask": False,
        "assignment_cooldown_duration_steps": 20,
    }


def _make_wrapper(profile: str, *, config_overrides: dict[str, Any] | None = None) -> AssignmentHarlWrapper:
    return AssignmentHarlWrapper(FakeAssignmentEnv(profile=profile, config_overrides=config_overrides))


def _augment_all(wrapper: AssignmentHarlWrapper) -> dict[str, torch.Tensor]:
    raw_obs, _ = wrapper.unwrapped.reset()
    return wrapper._augment_assignment_observations(raw_obs, problem=wrapper.unwrapped.get_assignment_problem())


def test_legacy_exact_identity_and_spaces() -> None:
    wrapper = _make_wrapper("legacy")
    raw_obs, _ = wrapper.unwrapped.reset()
    problem = wrapper.unwrapped.get_assignment_problem()
    augmented = wrapper._augment_assignment_observations(raw_obs, problem=problem)
    shared = wrapper._build_shared_obs(augmented)
    available = wrapper._build_available_actions(problem)
    expected_available = make_assignment_action_mask(problem, include_noop=True)

    _assert(wrapper.assignment_lifecycle_profile_config["profile_name"] == "legacy", "default legacy profile")
    for agent in wrapper.possible_agents:
        _assert(tuple(augmented[agent].shape) == (2, 909), "legacy actor shape")
        _assert(tuple(wrapper.observation_spaces[agent].shape) == (909,), "legacy observation space")
    _assert(tuple(shared.shape) == (2, 3, 2727), "legacy shared shape")
    _assert(tuple(wrapper.share_observation_space[0].shape) == (2727,), "legacy shared space")
    _assert(wrapper.action_space[0].n == 51, "action space remains Discrete(N+1)")
    _assert_tensor_equal(available, expected_available, "legacy available-actions unchanged")
    _assert(wrapper.assignment_observation_layout["viewpoint_row_dim"] == 14, "legacy row width")
    _assert(wrapper.last_actor_observation_generation is None, "legacy has no actor lifecycle generation")
    _assert(wrapper.last_shared_observation_generation is None, "legacy has no shared lifecycle generation")


def test_lifecycle_actor_shared_ordering_and_generation() -> None:
    wrapper = _make_wrapper("lifecycle_contract_c", config_overrides=_contract_c_overrides())
    reset_obs, reset_shared, reset_available = wrapper.reset()
    del reset_obs, reset_shared, reset_available
    problem = wrapper.unwrapped.get_assignment_problem()
    resolver = wrapper._assignment_lifecycle_resolver_runtime.resolver

    resolver.active_target_id[0, 1] = 7
    resolver.task_owner_robot_id[0, 7] = 1
    resolver.pair_state[0, 1, 7] = PAIR_ACTIVE
    resolver.pair_state[0, 0, 9] = PAIR_RELEASED_BUDGET
    resolver.pair_state[1, 2, 11] = PAIR_FAILED_BUDGET
    wrapper._budget_attempt_target[0, 1] = 7
    wrapper._budget_attempt_steps[0, 1] = 3
    wrapper._budget_attempt_budget_steps[0, 1] = 10

    wrapper._capture_lifecycle_decision_snapshot(problem=problem)
    augmented = wrapper._augment_assignment_observations(wrapper.unwrapped.reset()[0], problem=problem)
    shared = wrapper._build_shared_obs(augmented)
    available = wrapper._build_available_actions(problem=problem)
    snapshot = wrapper._last_lifecycle_decision_snapshot
    _assert(snapshot is not None, "lifecycle snapshot captured")

    row_start = wrapper.assignment_observation_layout["viewpoint_rows_start"]
    row_dim = wrapper.assignment_observation_layout["viewpoint_row_dim"]
    _assert(row_dim == 17, "lifecycle row width")
    _assert(tuple(augmented["agent_0"].shape) == (2, 1059), "lifecycle actor shape")
    _assert(tuple(shared.shape) == (2, 3, 3183), "lifecycle shared shape")
    _assert(tuple(available.shape) == (2, 3, 51), "lifecycle available-actions shape")
    _assert(tuple(wrapper.observation_spaces["agent_0"].shape) == (1059,), "lifecycle observation space")
    _assert(tuple(wrapper.share_observation_space[0].shape) == (3183,), "lifecycle shared space")

    active_offset = row_start + 7 * row_dim + 14
    teammate_offset = row_start + 7 * row_dim + 15
    failed_offset = row_start + 9 * row_dim + 16
    _assert_close(augmented["agent_1"][0, active_offset], torch.tensor(1.0), "owner active field")
    _assert_close(augmented["agent_1"][0, teammate_offset], torch.tensor(0.0), "owner teammate field")
    _assert_close(augmented["agent_0"][0, teammate_offset], torch.tensor(1.0), "teammate-owned field")
    _assert_close(augmented["agent_0"][0, failed_offset], torch.tensor(1.0), "released pair field")

    concatenated_actor = torch.cat([augmented[agent] for agent in wrapper.possible_agents], dim=-1)
    _assert_tensor_equal(shared[:, 0, : 3 * 1059], concatenated_actor, "shared actor concat block")
    critic_budget = build_critic_budget_tensors(snapshot).critic_budget_flat
    _assert_close(shared[:, 0, 3 * 1059 :], critic_budget, "shared critic budget tail")
    for agent_index in range(3):
        _assert_tensor_equal(shared[:, agent_index, :], shared[:, 0, :], "shared state repeated for every agent")
    _assert(
        wrapper.last_actor_observation_generation
        == wrapper.last_shared_observation_generation
        == wrapper.last_available_actions_generation
        == wrapper.last_lifecycle_snapshot_generation,
        "actor/shared/available-actions/snapshot generation match",
    )


def test_lifecycle_ablation_zero_state_and_available_actions_non_change() -> None:
    wrapper = _make_wrapper("lifecycle_ablation")
    obs, _shared_obs, _available_actions = wrapper.reset()
    shared = wrapper._build_shared_obs(obs)
    problem = wrapper.unwrapped.get_assignment_problem()
    available = wrapper._build_available_actions(problem)
    expected_available = make_assignment_action_mask(problem, include_noop=True)
    row_start = wrapper.assignment_observation_layout["viewpoint_rows_start"]
    row_dim = wrapper.assignment_observation_layout["viewpoint_row_dim"]
    lifecycle_indices = []
    for task_id in range(wrapper.num_viewpoints):
        lifecycle_indices.extend([row_start + task_id * row_dim + index for index in (14, 15, 16)])
    for agent in wrapper.possible_agents:
        _assert_close(obs[agent][:, lifecycle_indices], torch.zeros(2, 150), "zero lifecycle actor fields")
    _assert_close(shared[:, 0, 3 * 1059 :], torch.zeros(2, 6), "zero budget block")
    _assert_tensor_equal(available, expected_available, "lifecycle-ablation available-actions unchanged")
    _assert(
        wrapper.last_actor_observation_generation
        == wrapper.last_shared_observation_generation
        == wrapper.last_available_actions_generation
        == wrapper.last_lifecycle_snapshot_generation,
        "lifecycle-ablation actor/shared/available-actions generation match",
    )


def test_partial_reset_episode_generation() -> None:
    wrapper = _make_wrapper("lifecycle_ablation")
    wrapper.reset()
    original = wrapper.last_lifecycle_episode_generation
    wrapper._advance_lifecycle_episode_generation(env_ids=torch.tensor([1], dtype=torch.long))
    wrapper._capture_lifecycle_decision_snapshot(problem=wrapper.unwrapped.get_assignment_problem())
    updated = wrapper._last_lifecycle_decision_snapshot.episode_generation
    _assert_tensor_equal(updated, torch.tensor([original[0], original[1] + 1]), "partial episode generation")


def test_snapshot_timing_state_alignment() -> None:
    wrapper = _make_wrapper("lifecycle_ablation")
    wrapper.reset()
    resolver = wrapper._assignment_lifecycle_resolver_runtime.resolver
    resolver.active_target_id[0, 2] = 13
    resolver.task_owner_robot_id[0, 13] = 2
    resolver.pair_state[0, 2, 13] = PAIR_ACTIVE
    wrapper._budget_attempt_target[0, 2] = 13
    wrapper._budget_attempt_steps[0, 2] = 10
    wrapper._budget_attempt_budget_steps[0, 2] = 10
    resolver.active_target_id[1, :] = NO_TARGET
    resolver.task_owner_robot_id[1, :] = NO_OWNER
    resolver.pair_state[1, :, :] = 0
    wrapper._budget_attempt_target[1, :] = -1
    wrapper._budget_attempt_steps[1, :] = 0
    wrapper._budget_attempt_budget_steps[1, :] = 0
    wrapper._advance_lifecycle_episode_generation(env_ids=torch.tensor([1], dtype=torch.long))
    wrapper._capture_lifecycle_decision_snapshot(problem=wrapper.unwrapped.get_assignment_problem())

    snapshot = wrapper._last_lifecycle_decision_snapshot
    _assert(int(snapshot.active_target_id[0, 2].item()) == 13, "snapshot sees post-update active target")
    _assert(int(snapshot.active_target_id[1, 0].item()) == NO_TARGET, "snapshot sees reset cleared target")
    _assert(int(snapshot.budget_attempt_steps[0, 2].item()) == 10, "snapshot sees post-update budget")
    _assert(int(snapshot.budget_attempt_steps[1, 0].item()) == 0, "snapshot sees reset budget cleanup")


def test_manifest_ordering() -> None:
    wrapper = _make_wrapper("lifecycle_ablation")
    manifest = wrapper.assignment_observation_schema_manifest
    _assert(manifest["profile_name"] == "lifecycle_ablation", "manifest profile")
    _assert(
        tuple(manifest["actor_task_row_order"][-3:]) == ACTOR_LIFECYCLE_FEATURE_ORDER,
        "manifest lifecycle task row order",
    )
    _assert(manifest["actor_dimension"] == 1059, "manifest actor dimension")
    _assert(manifest["actor_dimension_by_agent"]["agent_0"] == 1059, "manifest actor dimension by agent")
    _assert(manifest["shared_dimension"] == 3183, "manifest shared dimension")
    _assert(manifest["mask_contract_version"] == "lifecycle_ablation_physical_mask_v1", "manifest mask contract")
    _assert(manifest["budget_release_contract"] == "disabled", "manifest budget release contract")
    _assert(manifest["available_actions_shape"] == [2, 3, 51], "manifest available-actions shape")
    _assert(manifest["noop_always_available"] is True, "manifest noop availability")
    budget_block_names = [block["name"] for block in manifest["shared_ordered_blocks"][-6:]]
    expected_names = [
        f"{feature}_robot_{robot_id}"
        for robot_id in range(3)
        for feature in CRITIC_BUDGET_FEATURE_ORDER
    ]
    _assert(budget_block_names == expected_names, "manifest shared budget block order")


TESTS = (
    test_legacy_exact_identity_and_spaces,
    test_lifecycle_actor_shared_ordering_and_generation,
    test_lifecycle_ablation_zero_state_and_available_actions_non_change,
    test_partial_reset_episode_generation,
    test_snapshot_timing_state_alignment,
    test_manifest_ordering,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary.")
    args = parser.parse_args()
    results = []
    for test in TESTS:
        test()
        results.append({"name": test.__name__, "status": "passed"})
    if args.json:
        print(json.dumps({"status": "passed", "tests": results}, indent=2))
    else:
        for result in results:
            print(f"PASS {result['name']}")
        print(f"PASS {len(results)} integration tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
