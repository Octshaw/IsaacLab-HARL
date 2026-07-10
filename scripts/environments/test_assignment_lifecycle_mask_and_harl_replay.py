"""Phase 9G-8E lifecycle mask and HARL historical-mask replay tests.

These tests use synthetic tensors and the installed HARL buffer/actor APIs. They
do not launch Isaac Sim, run training, playback/evaluation, or modify HARL.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Callable

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
    LIFECYCLE_CONTRACT_C_MASK_VERSION,
    build_lifecycle_ablation_available_action_tensors,
    build_lifecycle_contract_c_available_action_tensors,
    capture_lifecycle_decision_snapshot,
)
from assignment_lifecycle_resolver import (  # noqa: E402
    AssignmentLifecycleResolver,
    NO_OWNER,
    NO_TARGET,
    PAIR_ACTIVE,
    PAIR_FAILED_BUDGET,
    PAIR_NONE,
    PAIR_RELEASED_BUDGET,
    REJECT_COVERED_TARGET,
    REJECT_FAILED_PAIR,
    REJECT_OWNED_TARGET,
    REJECT_SWITCH_DISABLED,
    REJECT_UNAVAILABLE_TARGET,
)
from assignment_rl_interface import make_assignment_action_mask  # noqa: E402
from test_assignment_lifecycle_observation_integration import (  # noqa: E402
    FakeAssignmentEnv,
    _contract_c_overrides,
)

from harl.algorithms.actors.haa2c import HAA2C  # noqa: E402
from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.algorithms.actors.hatrpo import HATRPO  # noqa: E402
from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer  # noqa: E402
from harl.utils.trans_tools import _sa_cast  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_tensor_equal(actual: torch.Tensor, expected: torch.Tensor, message: str) -> None:
    if not torch.equal(actual, expected):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def _expect_raises(func: Callable[[], Any], expected_substring: str) -> None:
    try:
        func()
    except (RuntimeError, TypeError, ValueError) as exc:
        if expected_substring not in str(exc):
            raise AssertionError(f"expected error containing {expected_substring!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected error containing {expected_substring!r}")


def _empty_state(num_envs: int = 1, num_robots: int = 3, num_tasks: int = 7) -> dict[str, torch.Tensor]:
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
        "task_valid": torch.ones(num_envs, num_tasks, dtype=torch.bool),
    }


def _snapshot(state: dict[str, torch.Tensor], generation: int = 1):
    return capture_lifecycle_decision_snapshot(
        snapshot_generation=generation,
        episode_generation=torch.zeros(state["active_target_id"].shape[0], dtype=torch.long),
        **state,
    )


def _problem_from_state(state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor | int]:
    num_envs, num_robots, num_tasks = state["pair_state"].shape
    return {
        "num_envs": num_envs,
        "num_agents": num_robots,
        "num_viewpoints": num_tasks,
        "viewpoints_covered": state["viewpoints_covered"],
        "available_mask": state["available_mask"],
        "feasible_mask": state["feasible_mask"],
        "cost_matrix": torch.arange(num_envs * num_robots * num_tasks, dtype=torch.float32).reshape(
            num_envs,
            num_robots,
            num_tasks,
        ),
    }


def test_lifecycle_mask_idle_ownership_failed_noop_and_simultaneous_claims() -> None:
    state = _empty_state(num_tasks=7)
    state["task_valid"][0, 1] = False
    state["available_mask"][0, 0, 2] = False
    state["feasible_mask"][0, 0, 3] = False
    state["viewpoints_covered"][0, 4] = True
    state["active_target_id"][0, 1] = 5
    state["task_owner_robot_id"][0, 5] = 1
    state["pair_state"][0, 1, 5] = PAIR_ACTIVE
    state["budget_attempt_target"][0, 1] = 5
    state["budget_attempt_steps"][0, 1] = 2
    state["budget_attempt_budget_steps"][0, 1] = 10
    state["pair_state"][0, 0, 6] = PAIR_FAILED_BUDGET
    result = build_lifecycle_contract_c_available_action_tensors(_snapshot(state))

    _assert(result.mask_contract_version == LIFECYCLE_CONTRACT_C_MASK_VERSION, "mask version")
    robot0 = result.available_actions[0, 0]
    _assert_tensor_equal(
        robot0,
        torch.tensor([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]),
        "idle robot lifecycle target eligibility",
    )
    _assert(result.available_actions[0, 1, 5].item() == 1.0, "executing owner keeps active target")
    _assert(result.available_actions[0, 1, -1].item() == 1.0, "executing owner keeps noop")

    simultaneous = build_lifecycle_contract_c_available_action_tensors(_snapshot(_empty_state(num_tasks=3)))
    _assert(simultaneous.available_actions[0, 0, 0].item() == 1.0, "robot 0 may claim unowned target")
    _assert(simultaneous.available_actions[0, 1, 0].item() == 1.0, "robot 1 may claim same unowned target")


def test_lifecycle_mask_executing_current_target_and_noop_only() -> None:
    state = _empty_state(num_tasks=5)
    state["active_target_id"][0, 2] = 3
    state["task_owner_robot_id"][0, 3] = 2
    state["pair_state"][0, 2, 3] = PAIR_ACTIVE
    state["budget_attempt_target"][0, 2] = 3
    state["budget_attempt_steps"][0, 2] = 4
    state["budget_attempt_budget_steps"][0, 2] = 12
    state["available_mask"][0, 2, 3] = False
    state["feasible_mask"][0, 2, 3] = False
    result = build_lifecycle_contract_c_available_action_tensors(_snapshot(state))
    _assert_tensor_equal(
        result.available_actions[0, 2],
        torch.tensor([0.0, 0.0, 0.0, 1.0, 0.0, 1.0]),
        "executing robot allows current target and noop only",
    )


def test_lifecycle_mask_failed_and_released_pairs() -> None:
    state = _empty_state(num_tasks=4)
    state["pair_state"][0, 0, 1] = PAIR_FAILED_BUDGET
    state["pair_state"][0, 0, 2] = PAIR_RELEASED_BUDGET
    result = build_lifecycle_contract_c_available_action_tensors(_snapshot(state))
    _assert(result.available_actions[0, 0, 1].item() == 0.0, "failed pair masked")
    _assert(result.available_actions[0, 0, 2].item() == 0.0, "released pair masked")
    _assert(result.available_actions[0, 1, 1].item() == 1.0, "teammate unrelated failed pair unaffected")


def test_lifecycle_mask_noop_nonzero_rows_and_stale_covered_active_error() -> None:
    state = _empty_state(num_tasks=3)
    state["task_valid"][0, :] = False
    result = build_lifecycle_contract_c_available_action_tensors(_snapshot(state))
    _assert_tensor_equal(result.available_actions[0, :, -1], torch.ones(3), "noop available with no valid targets")
    _assert(torch.all(result.available_actions.sum(dim=-1) > 0), "no all-zero action rows")

    invalid = _empty_state(num_tasks=3)
    invalid["active_target_id"][0, 0] = 1
    invalid["task_owner_robot_id"][0, 1] = 0
    invalid["pair_state"][0, 0, 1] = PAIR_ACTIVE
    invalid["budget_attempt_target"][0, 0] = 1
    invalid["budget_attempt_steps"][0, 0] = 1
    invalid["budget_attempt_budget_steps"][0, 0] = 5
    invalid["viewpoints_covered"][0, 1] = True
    _expect_raises(lambda: _snapshot(invalid), "active targets must not already be covered")


def test_ablation_mask_uses_snapshot_physical_mask() -> None:
    state = _empty_state(num_tasks=4)
    state["available_mask"][0, 0, 1] = False
    result = build_lifecycle_ablation_available_action_tensors(_snapshot(state))
    expected = torch.cat((state["available_mask"].to(dtype=torch.float32), torch.ones(1, 3, 1)), dim=-1)
    _assert_tensor_equal(result.available_actions, expected, "ablation mask is physical/noop snapshot mask")


def test_mask_and_resolver_agree_on_deterministic_rejections() -> None:
    state = _empty_state(num_tasks=7)
    state["available_mask"][0, 0, 2] = False
    state["viewpoints_covered"][0, 4] = True
    state["active_target_id"][0, 1] = 5
    state["task_owner_robot_id"][0, 5] = 1
    state["pair_state"][0, 1, 5] = PAIR_ACTIVE
    state["budget_attempt_target"][0, 1] = 5
    state["budget_attempt_steps"][0, 1] = 2
    state["budget_attempt_budget_steps"][0, 1] = 10
    state["pair_state"][0, 0, 6] = PAIR_RELEASED_BUDGET
    mask = build_lifecycle_contract_c_available_action_tensors(_snapshot(state)).available_actions
    resolver = AssignmentLifecycleResolver(num_envs=1, num_robots=3, num_tasks=7, enabled=True)
    resolver.active_target_id.copy_(state["active_target_id"])
    resolver.task_owner_robot_id.copy_(state["task_owner_robot_id"])
    resolver.pair_state.copy_(state["pair_state"])

    cases = (
        (torch.tensor([[2, NO_TARGET, NO_TARGET]]), 0, 2, REJECT_UNAVAILABLE_TARGET),
        (torch.tensor([[4, NO_TARGET, NO_TARGET]]), 0, 4, REJECT_COVERED_TARGET),
        (torch.tensor([[5, NO_TARGET, NO_TARGET]]), 0, 5, REJECT_OWNED_TARGET),
        (torch.tensor([[6, NO_TARGET, NO_TARGET]]), 0, 6, REJECT_FAILED_PAIR),
        (torch.tensor([[NO_TARGET, 0, NO_TARGET]]), 1, 0, REJECT_SWITCH_DISABLED),
    )
    problem = _problem_from_state(state)
    for proposal, robot_id, target_id, expected_reason in cases:
        result = resolver.resolve_pre_step(problem=problem, assignment_proposal=proposal)
        _assert(mask[0, robot_id, target_id].item() == 0.0, f"mask rejects target {target_id}")
        _assert(
            int(result.proposal_rejected_reason[0, robot_id].item()) == int(expected_reason),
            f"resolver rejects target {target_id} with expected reason",
        )


def test_wrapper_lifecycle_ablation_budget_disabled_validation_and_repeated_updates() -> None:
    _expect_raises(
        lambda: AssignmentHarlWrapper(
            FakeAssignmentEnv(
                profile="lifecycle_ablation",
                config_overrides={"assignment_cooldown_enabled": True},
            )
        ),
        "budget tracker and budget trigger remain disabled",
    )

    wrapper = AssignmentHarlWrapper(FakeAssignmentEnv(profile="lifecycle_ablation"))
    obs, shared, available = wrapper.reset()
    del obs, shared, available
    problem = wrapper.unwrapped.get_assignment_problem()
    assignment = torch.zeros(wrapper.num_envs, wrapper.num_agents, dtype=torch.long)
    selected_available = torch.ones(wrapper.num_envs, wrapper.num_agents, dtype=torch.bool)
    for _ in range(3):
        wrapper._update_assignment_diagnostics(
            assignment=assignment,
            pre_step_problem=problem,
            post_step_problem=problem,
            selected_available_mask=selected_available,
        )
        wrapper._capture_lifecycle_decision_snapshot(problem=problem)
        obs = wrapper._augment_assignment_observations(wrapper.unwrapped.reset()[0], problem=problem)
        shared = wrapper._build_shared_obs(obs)
        available = wrapper._build_available_actions(problem=problem)
        _assert(torch.all(wrapper._budget_attempt_target == NO_TARGET), "ablation budget target stays inactive")
        _assert(torch.all(wrapper._budget_attempt_steps == 0), "ablation budget steps stay zero")
        _assert(torch.all(wrapper._last_budget_triggered_by_budget == 0), "ablation budget trigger stays false")
        row_start = wrapper.assignment_observation_layout["viewpoint_rows_start"]
        row_dim = wrapper.assignment_observation_layout["viewpoint_row_dim"]
        lifecycle_indices = []
        for task_id in range(wrapper.num_viewpoints):
            lifecycle_indices.extend([row_start + task_id * row_dim + offset for offset in (14, 15, 16)])
        for agent in wrapper.possible_agents:
            _assert(torch.all(obs[agent][:, lifecycle_indices] == 0.0), "ablation lifecycle actor fields stay zero")
        _assert(torch.all(shared[:, 0, 3 * 1059 :] == 0.0), "ablation critic budget block stays zero")
        _assert_tensor_equal(available, make_assignment_action_mask(problem, include_noop=True), "ablation mask unchanged")


def test_wrapper_contract_c_generation_and_legacy_guardrail_non_regression() -> None:
    wrapper = AssignmentHarlWrapper(
        FakeAssignmentEnv(profile="lifecycle_contract_c", config_overrides=_contract_c_overrides())
    )
    obs, shared, available = wrapper.reset()
    _assert(tuple(available.shape) == (2, 3, 51), "contract_c available-actions shape")
    _assert(
        wrapper.last_actor_observation_generation
        == wrapper.last_shared_observation_generation
        == wrapper.last_available_actions_generation
        == wrapper.last_lifecycle_snapshot_generation,
        "contract_c actor/shared/mask/snapshot generation equality",
    )
    del obs, shared

    legacy = AssignmentHarlWrapper(
        FakeAssignmentEnv(
            profile="legacy",
            config_overrides={
                "assignment_cooldown_enabled": True,
                "assignment_cooldown_apply_to_action_mask": True,
            },
        )
    )
    problem = legacy.unwrapped.get_assignment_problem()
    legacy._per_robot_target_cooldown_remaining[0, 0, 3] = 5
    legacy_available = legacy._build_available_actions(problem=problem)
    _assert(legacy_available[0, 0, 3].item() == 0.0, "legacy cooldown overlay still masks target")
    _assert(legacy_available[0, 0, -1].item() == 1.0, "legacy noop remains available")


def _make_unique_masks(episode_length: int, n_threads: int, action_dim: int) -> torch.Tensor:
    masks = torch.zeros(episode_length + 1, n_threads, action_dim, dtype=torch.float32)
    for time_id in range(episode_length + 1):
        for env_id in range(n_threads):
            target = (time_id + env_id + 1) % (action_dim - 1)
            masks[time_id, env_id, target] = 1.0
            masks[time_id, env_id, -1] = 1.0
    return masks


def _make_actor_buffer() -> tuple[OnPolicyActorBuffer, torch.Tensor]:
    args = {
        "episode_length": 4,
        "n_rollout_threads": 2,
        "hidden_sizes": [8],
        "recurrent_n": 1,
    }
    buffer = OnPolicyActorBuffer(
        args,
        gymnasium.spaces.Box(-1.0, 1.0, shape=(1,), dtype=float),
        gymnasium.spaces.Discrete(6),
        device="cpu",
    )
    masks = _make_unique_masks(args["episode_length"], args["n_rollout_threads"], 6)
    for time_id in range(args["episode_length"] + 1):
        for env_id in range(args["n_rollout_threads"]):
            buffer.obs[time_id, env_id, 0] = float(time_id * 10 + env_id)
    buffer.available_actions[0] = masks[0].clone()
    for time_id in range(args["episode_length"]):
        next_obs = buffer.obs[time_id + 1].clone()
        rnn_states = torch.full((args["n_rollout_threads"], 1, 8), float(time_id + 1))
        actions = torch.full((args["n_rollout_threads"], 1), float(time_id))
        action_log_probs = torch.full((args["n_rollout_threads"], 1), -0.1 * float(time_id + 1))
        step_masks = torch.ones(args["n_rollout_threads"], 1)
        active_masks = torch.ones(args["n_rollout_threads"], 1)
        buffer.insert(
            next_obs,
            rnn_states,
            actions,
            action_log_probs,
            step_masks,
            active_masks,
            masks[time_id + 1],
        )
    return buffer, masks


def _verify_generator_sample(sample: tuple[Any, ...], masks: torch.Tensor, label: str) -> None:
    obs_batch = sample[0]
    available_actions_batch = sample[7]
    _assert(available_actions_batch is not None, f"{label} returned available_actions")
    for row_id in range(obs_batch.shape[0]):
        marker = int(obs_batch[row_id, 0].item())
        time_id, env_id = divmod(marker, 10)
        _assert(time_id < masks.shape[0] - 1, f"{label} sample uses historical obs index")
        _assert_tensor_equal(
            available_actions_batch[row_id],
            masks[time_id, env_id],
            f"{label} mask aligns with sample marker {marker}",
        )


def test_harl_feed_forward_and_naive_generators_replay_historical_masks() -> None:
    buffer, masks = _make_actor_buffer()
    advantages = torch.arange(4 * 2, dtype=torch.float32).reshape(4, 2, 1)

    for sample in buffer.feed_forward_generator_actor(advantages, actor_num_mini_batch=2):
        _verify_generator_sample(sample, masks, "feed_forward_generator_actor")
    for sample in buffer.naive_recurrent_generator_actor(advantages, actor_num_mini_batch=2):
        _verify_generator_sample(sample, masks, "naive_recurrent_generator_actor")


def test_installed_chunked_recurrent_incompatibility_remains_documented() -> None:
    source = inspect.getsource(_sa_cast)
    _assert("transpose(1, 0, 2)" in source, "installed _sa_cast incompatibility signature")
    _expect_raises(
        lambda: _sa_cast(torch.zeros(2, 2, 2)),
        "transpose() received an invalid combination of arguments",
    )


class _StopAfterEvaluate(Exception):
    pass


def _verify_algorithm_update_passes_historical_mask(algo_cls: type, label: str) -> None:
    buffer, masks = _make_actor_buffer()
    advantages = torch.ones(4, 2, 1)
    sample8 = next(buffer.feed_forward_generator_actor(advantages, actor_num_mini_batch=1))
    sample = (*sample8, torch.ones_like(sample8[6]))
    expected_available = sample8[7].clone()
    algo = algo_cls.__new__(algo_cls)
    algo.tpdv = {"dtype": torch.float32, "device": torch.device("cpu")}

    def _spy_evaluate_actions(
        obs_batch,
        rnn_states_batch,
        actions_batch,
        masks_batch,
        available_actions_batch,
        active_masks_batch,
    ):
        del obs_batch, rnn_states_batch, actions_batch, masks_batch, active_masks_batch
        _assert_tensor_equal(
            available_actions_batch,
            expected_available,
            f"{label} evaluate_actions receives historical mask batch",
        )
        for row_id in range(sample8[0].shape[0]):
            marker = int(sample8[0][row_id, 0].item())
            time_id, env_id = divmod(marker, 10)
            _assert_tensor_equal(
                available_actions_batch[row_id],
                masks[time_id, env_id],
                f"{label} evaluate_actions mask aligns with sample marker {marker}",
            )
        raise _StopAfterEvaluate()

    algo.evaluate_actions = _spy_evaluate_actions
    try:
        algo.update(sample)
    except _StopAfterEvaluate:
        return
    raise AssertionError(f"{label} update did not call evaluate_actions")


def test_actor_updates_pass_historical_mask_to_evaluate_actions() -> None:
    _verify_algorithm_update_passes_historical_mask(HAPPO, "HAPPO")
    _verify_algorithm_update_passes_historical_mask(HAA2C, "HAA2C")
    _verify_algorithm_update_passes_historical_mask(HATRPO, "HATRPO")


TESTS = (
    test_lifecycle_mask_idle_ownership_failed_noop_and_simultaneous_claims,
    test_lifecycle_mask_executing_current_target_and_noop_only,
    test_lifecycle_mask_failed_and_released_pairs,
    test_lifecycle_mask_noop_nonzero_rows_and_stale_covered_active_error,
    test_ablation_mask_uses_snapshot_physical_mask,
    test_mask_and_resolver_agree_on_deterministic_rejections,
    test_wrapper_lifecycle_ablation_budget_disabled_validation_and_repeated_updates,
    test_wrapper_contract_c_generation_and_legacy_guardrail_non_regression,
    test_harl_feed_forward_and_naive_generators_replay_historical_masks,
    test_installed_chunked_recurrent_incompatibility_remains_documented,
    test_actor_updates_pass_historical_mask_to_evaluate_actions,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary.")
    args = parser.parse_args()
    results = []
    failed = False
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - test runner records all required boundary failures.
            failed = True
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    if args.json:
        print(json.dumps({"status": "failed" if failed else "passed", "tests": results}, indent=2))
    else:
        for result in results:
            prefix = "PASS" if result["status"] == "passed" else "FAIL"
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{prefix} {result['name']}{suffix}")
        status = "FAIL" if failed else "PASS"
        print(f"{status} {len(results)} lifecycle mask / HARL replay tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
