"""Fast smoke checks for wrapper-local failed-pair/release-memory masking.

This script uses a tiny fake assignment env so it can validate the Phase 9G-2
guardrail without launching Isaac simulation, playback, or training.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
ISAACLAB_TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks"
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
for source_path in (ISAACLAB_TASKS_SOURCE, SCAN_TASK_SOURCE):
    if str(source_path) not in sys.path:
        sys.path.insert(0, str(source_path))

from assignment_harl_wrapper import AssignmentHarlWrapper  # noqa: E402
from assignment_rl_interface import make_assignment_action_mask  # noqa: E402


class _FakeSceneCfg:
    env_spacing = 1.0


class _FakeCfg:
    scene = _FakeSceneCfg()

    assignment_cooldown_enabled = False
    assignment_cooldown_scope = "per_robot_target"
    assignment_cooldown_trigger_mode = "streak"
    assignment_cooldown_trigger_attempts = 3
    assignment_cooldown_trigger_same_target_streak = 10
    assignment_cooldown_trigger_steps_since_global_gain = 10
    assignment_cooldown_duration_steps = 20
    assignment_cooldown_require_uncovered = True
    assignment_cooldown_require_available = True
    assignment_cooldown_require_feasible = True
    assignment_cooldown_require_no_global_gain = True
    assignment_cooldown_clear_on_covered = True
    assignment_cooldown_apply_to_action_mask = True
    assignment_cooldown_log_diagnostics = True
    assignment_cooldown_budget_multiplier = 1.5
    assignment_cooldown_budget_slack_steps = 5
    assignment_cooldown_budget_min_streak = 10
    assignment_cooldown_budget_require_no_global_gain = True
    assignment_cooldown_budget_require_uncovered = True
    assignment_cooldown_budget_require_available = True
    assignment_cooldown_budget_require_feasible = True

    assignment_redirect_guardrail_enabled = False
    assignment_redirect_guardrail_apply_context = "recent_budget_trigger"
    assignment_redirect_guardrail_window_steps = 1
    assignment_redirect_guardrail_claimed_target_enabled = True
    assignment_redirect_guardrail_spacing_enabled = True
    assignment_redirect_guardrail_spacing_threshold = None
    assignment_redirect_guardrail_fail_open_spacing = True
    assignment_redirect_guardrail_fail_open_claimed = True
    assignment_redirect_guardrail_log_diagnostics = True

    assignment_failed_pair_memory_enabled = False
    assignment_failed_pair_memory_duration_steps = 5
    assignment_failed_pair_memory_apply_to_action_mask = True
    assignment_failed_pair_memory_source = "budget_trigger"
    assignment_failed_pair_memory_fail_open = True
    assignment_failed_pair_memory_clear_on_coverage = True
    assignment_failed_pair_memory_log_diagnostics = True

    inter_robot_target_conflict_radius = 0.35
    inter_robot_target_conflict_safety_margin = 0.15
    max_base_xy_step = (0.08, 0.10, 0.06)


class _FakeAssignmentEnv:
    def __init__(
        self,
        *,
        memory_enabled: bool = False,
        memory_duration_steps: int = 5,
        memory_apply_to_action_mask: bool = True,
        memory_fail_open: bool = True,
        memory_clear_on_coverage: bool = True,
        cooldown_enabled: bool = False,
        num_envs: int = 2,
        num_agents: int = 3,
        num_viewpoints: int = 6,
        trigger_mode: str = "streak",
        trigger_attempts: int = 3,
        trigger_same_target_streak: int = 10,
        trigger_steps_since_global_gain: int = 10,
        cooldown_duration_steps: int = 20,
        budget_multiplier: float = 1.5,
        budget_slack_steps: int = 5,
        budget_min_streak: int = 10,
        max_base_xy_step: tuple[float, ...] = (0.08, 0.10, 0.06),
    ) -> None:
        self.unwrapped = self
        self.num_envs = int(num_envs)
        self.num_agents = int(num_agents)
        self.num_viewpoints = int(num_viewpoints)
        self.device = torch.device("cpu")
        self.max_episode_length = 300
        self.possible_agents = [f"robot_{index}" for index in range(self.num_agents)]
        self.agents = list(self.possible_agents)
        self.observation_spaces = {agent: 96 for agent in self.possible_agents}
        self.cfg = _FakeCfg()
        self.cfg.assignment_failed_pair_memory_enabled = bool(memory_enabled)
        self.cfg.assignment_failed_pair_memory_duration_steps = int(memory_duration_steps)
        self.cfg.assignment_failed_pair_memory_apply_to_action_mask = bool(memory_apply_to_action_mask)
        self.cfg.assignment_failed_pair_memory_fail_open = bool(memory_fail_open)
        self.cfg.assignment_failed_pair_memory_clear_on_coverage = bool(memory_clear_on_coverage)
        self.cfg.assignment_cooldown_enabled = bool(cooldown_enabled)
        self.cfg.assignment_cooldown_trigger_mode = str(trigger_mode)
        self.cfg.assignment_cooldown_trigger_attempts = int(trigger_attempts)
        self.cfg.assignment_cooldown_trigger_same_target_streak = int(trigger_same_target_streak)
        self.cfg.assignment_cooldown_trigger_steps_since_global_gain = int(trigger_steps_since_global_gain)
        self.cfg.assignment_cooldown_duration_steps = int(cooldown_duration_steps)
        self.cfg.assignment_cooldown_budget_multiplier = float(budget_multiplier)
        self.cfg.assignment_cooldown_budget_slack_steps = int(budget_slack_steps)
        self.cfg.assignment_cooldown_budget_min_streak = int(budget_min_streak)
        max_base_xy_values = tuple(float(value) for value in max_base_xy_step)
        if len(max_base_xy_values) == 1:
            max_base_xy_values = max_base_xy_values * self.num_agents
        elif len(max_base_xy_values) != self.num_agents:
            if len(max_base_xy_values) > self.num_agents:
                max_base_xy_values = max_base_xy_values[: self.num_agents]
            else:
                max_base_xy_values = max_base_xy_values + (max_base_xy_values[-1],) * (
                    self.num_agents - len(max_base_xy_values)
                )
        self.cfg.max_base_xy_step = max_base_xy_values
        self.episode_length_buf = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)

        self.viewpoints_covered = torch.zeros(self.num_envs, self.num_viewpoints, dtype=torch.bool, device=self.device)
        self.feasible_mask_base = torch.ones(self.num_agents, self.num_viewpoints, dtype=torch.bool, device=self.device)
        viewpoint_ids = torch.arange(self.num_viewpoints, dtype=torch.float32, device=self.device)
        self.viewpoint_pos = torch.stack(
            (viewpoint_ids, torch.zeros_like(viewpoint_ids), torch.ones_like(viewpoint_ids)),
            dim=-1,
        )
        self.viewpoint_quat = torch.zeros(self.num_viewpoints, 4, dtype=torch.float32, device=self.device)
        self.viewpoint_quat[:, 0] = 1.0
        self.scanner_pos = torch.zeros(self.num_envs, self.num_agents, 3, dtype=torch.float32, device=self.device)
        self.scanner_quat = torch.zeros(self.num_envs, self.num_agents, 4, dtype=torch.float32, device=self.device)
        self.scanner_quat[:, :, 0] = 1.0

    def reset(self, *args, **kwargs) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
        self.viewpoints_covered.zero_()
        self.episode_length_buf.zero_()
        obs = {
            agent: torch.zeros(self.num_envs, 96, dtype=torch.float32, device=self.device)
            for agent in self.possible_agents
        }
        return obs, {}

    def get_assignment_problem(self) -> dict[str, Any]:
        feasible = self.feasible_mask_base.unsqueeze(0).expand(self.num_envs, -1, -1)
        available = feasible & (~self.viewpoints_covered[:, None, :])
        viewpoint_pos = self.viewpoint_pos.unsqueeze(0).expand(self.num_envs, -1, -1)
        viewpoint_quat = self.viewpoint_quat.unsqueeze(0).expand(self.num_envs, -1, -1)
        cost_matrix = torch.linalg.norm(self.scanner_pos[:, :, None, :] - viewpoint_pos[:, None, :, :], dim=-1)
        return {
            "num_envs": self.num_envs,
            "num_agents": self.num_agents,
            "agent_names": tuple(self.possible_agents),
            "num_viewpoints": self.num_viewpoints,
            "viewpoint_ids": tuple(range(self.num_viewpoints)),
            "scanner_pos": self.scanner_pos,
            "scanner_quat": self.scanner_quat,
            "viewpoint_pos": viewpoint_pos,
            "viewpoint_quat": viewpoint_quat,
            "viewpoints_covered": self.viewpoints_covered,
            "cost_matrix": cost_matrix,
            "static_geometric_feasible_mask": feasible,
            "feasible_mask": feasible,
            "available_mask": available,
            "inter_robot_target_conflict_radius": 0.35,
            "inter_robot_target_conflict_safety_margin": 0.15,
        }

    def close(self) -> None:
        pass


def _make_wrapper(**kwargs) -> AssignmentHarlWrapper:
    return AssignmentHarlWrapper(_FakeAssignmentEnv(**kwargs))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _selected_available(wrapper: AssignmentHarlWrapper, assignment: torch.Tensor, problem: dict[str, Any]) -> torch.Tensor:
    available_actions = wrapper._build_available_actions(problem=problem)
    return wrapper._selected_available_mask(assignment, available_actions)


def _update(
    wrapper: AssignmentHarlWrapper,
    assignment: torch.Tensor,
    pre_problem: dict[str, Any],
    post_problem: dict[str, Any],
) -> None:
    wrapper._update_assignment_diagnostics(
        assignment=assignment,
        pre_step_problem=pre_problem,
        post_step_problem=post_problem,
        selected_available_mask=_selected_available(wrapper, assignment, pre_problem),
    )


def run_smoke() -> dict[str, Any]:
    disabled = _make_wrapper(memory_enabled=False)
    disabled_problem = disabled.unwrapped.get_assignment_problem()
    disabled._assignment_failed_pair_memory_remaining[0, 0, 2] = 5
    disabled_mask = disabled._build_available_actions(problem=disabled_problem)
    disabled_baseline = make_assignment_action_mask(disabled_problem, include_noop=True)
    _assert(torch.equal(disabled_mask, disabled_baseline), "disabled failed-pair memory changed available_actions")
    disabled_info = disabled._assignment_failed_pair_memory_info()
    _assert(float(disabled_info["enabled"]) == 0.0, "disabled info must report enabled=0")
    _assert(float(disabled_info["active_count"].sum().item()) == 0.0, "disabled active diagnostics must be zero")

    enabled = _make_wrapper(memory_enabled=True, num_envs=1, num_agents=3, num_viewpoints=6)
    problem = enabled.unwrapped.get_assignment_problem()
    available_before = problem["available_mask"].clone()
    baseline_shape = make_assignment_action_mask(problem, include_noop=True).shape
    enabled._assignment_failed_pair_memory_remaining[0, 0, 2] = 3
    masked = enabled._build_available_actions(problem=problem)
    _assert(torch.equal(problem["available_mask"], available_before), "failed-pair memory mutated base available_mask")
    _assert(tuple(masked.shape) == tuple(baseline_shape), "failed-pair memory changed available_actions shape")
    _assert(float(masked[0, 0, 2].item()) == 0.0, "failed-pair memory did not suppress selected robot-target pair")
    _assert(float(masked[0, 1, 2].item()) == 1.0, "failed-pair memory leaked to another robot")
    _assert(float(masked[0, 0, -1].item()) == 1.0, "failed-pair memory masked noop")
    _assert(
        int(enabled._last_failed_pair_memory_suppressed_count[0, 0].item()) == 1,
        "suppressed-count diagnostic mismatch",
    )

    fail_open = _make_wrapper(memory_enabled=True, num_envs=1, num_agents=2, num_viewpoints=4)
    fail_open_problem = fail_open.unwrapped.get_assignment_problem()
    fail_open_problem["available_mask"] = fail_open_problem["available_mask"].clone()
    fail_open_problem["available_mask"][0, 0, :] = False
    fail_open_problem["available_mask"][0, 0, 2] = True
    fail_open_available_before = fail_open_problem["available_mask"].clone()
    fail_open._assignment_failed_pair_memory_remaining[0, 0, 2] = 4
    fail_open_mask = fail_open._build_available_actions(problem=fail_open_problem)
    _assert(
        torch.equal(fail_open_problem["available_mask"], fail_open_available_before),
        "failed-pair fail-open mutated base available_mask",
    )
    _assert(float(fail_open_mask[0, 0, 2].item()) == 1.0, "failed-pair memory did not fail open")
    _assert(float(fail_open_mask[0, 0, -1].item()) == 1.0, "failed-pair fail-open masked noop")
    _assert(
        int(fail_open._last_failed_pair_memory_fail_open_count[0, 0].item()) == 1,
        "fail-open diagnostic missing",
    )
    _assert(
        int(fail_open._last_failed_pair_memory_suppressed_count[0, 0].item()) == 0,
        "failed-open suppression should not count as actual suppression",
    )

    ttl = _make_wrapper(memory_enabled=True, memory_duration_steps=2, num_envs=1, num_agents=2, num_viewpoints=4)
    ttl_problem = ttl.unwrapped.get_assignment_problem()
    ttl._assignment_failed_pair_memory_remaining[0, 0, 2] = 2
    noop_assignment = torch.full((1, 2), -1, dtype=torch.long)
    _update(ttl, noop_assignment, ttl_problem, ttl_problem)
    _assert(int(ttl._assignment_failed_pair_memory_remaining[0, 0, 2].item()) == 1, "memory TTL did not decrement")
    _update(ttl, noop_assignment, ttl_problem, ttl_problem)
    _assert(int(ttl._assignment_failed_pair_memory_remaining[0, 0, 2].item()) == 0, "memory TTL did not expire")
    ttl_mask = ttl._build_available_actions(problem=ttl_problem)
    _assert(float(ttl_mask[0, 0, 2].item()) == 1.0, "expired memory did not release target")

    coverage = _make_wrapper(memory_enabled=True, num_envs=1, num_agents=2, num_viewpoints=4)
    coverage_problem = coverage.unwrapped.get_assignment_problem()
    coverage._assignment_failed_pair_memory_remaining[0, 0, 2] = 3
    covered_post = coverage.unwrapped.get_assignment_problem()
    covered_post["viewpoints_covered"] = covered_post["viewpoints_covered"].clone()
    covered_post["viewpoints_covered"][0, 2] = True
    _update(coverage, noop_assignment, coverage_problem, covered_post)
    _assert(
        int(coverage._assignment_failed_pair_memory_remaining[0, :, 2].sum().item()) == 0,
        "covered target did not clear failed-pair memory",
    )

    reset = _make_wrapper(memory_enabled=True, num_envs=2, num_agents=2, num_viewpoints=4)
    reset_problem = reset.unwrapped.get_assignment_problem()
    reset._assignment_failed_pair_memory_remaining[:] = 4
    reset._assignment_failed_pair_memory_trigger_step[:] = 7
    reset._reset_assignment_diagnostics(env_ids=torch.tensor([1], dtype=torch.long), problem=reset_problem)
    _assert(int(reset._assignment_failed_pair_memory_remaining[1].sum().item()) == 0, "partial reset missed memory")
    _assert(int(reset._assignment_failed_pair_memory_remaining[0].sum().item()) > 0, "partial reset cleared wrong env")
    reset._reset_assignment_diagnostics(problem=reset_problem)
    _assert(int(reset._assignment_failed_pair_memory_remaining.sum().item()) == 0, "full reset missed memory")
    _assert(int((reset._assignment_failed_pair_memory_trigger_step >= 0).sum().item()) == 0, "full reset missed steps")

    trigger = _make_wrapper(
        memory_enabled=True,
        memory_duration_steps=4,
        cooldown_enabled=True,
        trigger_mode="budget_and_streak",
        trigger_attempts=999999,
        trigger_same_target_streak=999999,
        trigger_steps_since_global_gain=0,
        cooldown_duration_steps=5,
        budget_multiplier=1.0,
        budget_slack_steps=1,
        budget_min_streak=1,
        max_base_xy_step=(1.0, 1.0, 1.0),
        num_envs=1,
        num_agents=2,
        num_viewpoints=4,
    )
    trigger_problem = trigger.unwrapped.get_assignment_problem()
    trigger_assignment = torch.full((1, 2), -1, dtype=torch.long)
    trigger_assignment[:, 0] = 1
    _update(trigger, trigger_assignment, trigger_problem, trigger_problem)
    _update(trigger, trigger_assignment, trigger_problem, trigger_problem)
    _update(trigger, trigger_assignment, trigger_problem, trigger_problem)
    _assert(
        int(trigger._assignment_failed_pair_memory_remaining[0, 0, 1].item()) == 4,
        "budget trigger did not activate failed-pair memory",
    )
    _assert(
        int(trigger._assignment_failed_pair_memory_remaining[0, 1, 1].item()) == 0,
        "budget trigger memory leaked to teammate",
    )
    _assert(
        trigger._last_failed_pair_memory_trigger_robot_ids[0] == [0],
        "failed-pair trigger robot diagnostic missing",
    )
    _assert(
        trigger._last_failed_pair_memory_trigger_target_ids[0] == [1],
        "failed-pair trigger target diagnostic missing",
    )
    _assert(
        trigger._last_failed_pair_memory_trigger_reasons[0] == ["budget_trigger"],
        "failed-pair trigger reason diagnostic missing",
    )
    trigger_mask = trigger._build_available_actions(problem=trigger_problem)
    _assert(float(trigger_mask[0, 0, 1].item()) == 0.0, "active failed-pair memory did not filter mask")
    _assert(float(trigger_mask[0, 1, 1].item()) == 1.0, "active failed-pair memory masked teammate")
    trigger_info = trigger._assignment_failed_pair_memory_info()
    _assert(float(trigger_info["active_count"][0].item()) == 1.0, "active-count diagnostic mismatch")

    return {
        "status": "passed",
        "disabled_mask_matches_baseline": True,
        "pair_scoped_suppression": True,
        "same_target_available_to_teammate": True,
        "noop_preserved": True,
        "fail_open_preserved_non_noop": True,
        "ttl_expired": True,
        "coverage_clear": True,
        "reset_clear": True,
        "available_actions_shape_unchanged": True,
        "base_mask_not_mutated": True,
        "budget_trigger_source_recorded": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result_file", type=str, default=None, help="Optional JSON result path.")
    args = parser.parse_args()
    result = run_smoke()
    if args.result_file:
        path = Path(args.result_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[OK]: assignment failed-pair memory smoke passed: {json.dumps(result, sort_keys=True)}")


if __name__ == "__main__":
    main()
