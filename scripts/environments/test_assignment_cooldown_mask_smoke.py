"""Fast smoke checks for AssignmentHarlWrapper cooldown mask behavior.

This script uses a tiny fake assignment env so it can validate wrapper-local
state, reset, and mask behavior without launching Isaac simulation.
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
    inter_robot_target_conflict_radius = 0.35
    inter_robot_target_conflict_safety_margin = 0.15
    max_base_xy_step = (0.08, 0.10, 0.06)


class _FakeAssignmentEnv:
    def __init__(
        self,
        *,
        cooldown_enabled: bool,
        num_envs: int = 2,
        num_agents: int = 3,
        num_viewpoints: int = 50,
        trigger_attempts: int = 3,
        trigger_same_target_streak: int = 10,
        trigger_steps_since_global_gain: int = 10,
        duration_steps: int = 20,
        trigger_mode: str = "streak",
        budget_multiplier: float = 1.5,
        budget_slack_steps: int = 5,
        budget_min_streak: int = 10,
        max_base_xy_step: tuple[float, ...] = (0.08, 0.10, 0.06),
        redirect_guardrail_enabled: bool = False,
        redirect_guardrail_window_steps: int = 1,
        redirect_guardrail_claimed_target_enabled: bool = True,
        redirect_guardrail_spacing_enabled: bool = True,
        redirect_guardrail_spacing_threshold: float | None = None,
        redirect_guardrail_fail_open_spacing: bool = True,
        redirect_guardrail_fail_open_claimed: bool = True,
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
        self.cfg.assignment_cooldown_enabled = bool(cooldown_enabled)
        self.cfg.assignment_cooldown_trigger_mode = str(trigger_mode)
        self.cfg.assignment_cooldown_trigger_attempts = int(trigger_attempts)
        self.cfg.assignment_cooldown_trigger_same_target_streak = int(trigger_same_target_streak)
        self.cfg.assignment_cooldown_trigger_steps_since_global_gain = int(trigger_steps_since_global_gain)
        self.cfg.assignment_cooldown_duration_steps = int(duration_steps)
        self.cfg.assignment_cooldown_budget_multiplier = float(budget_multiplier)
        self.cfg.assignment_cooldown_budget_slack_steps = int(budget_slack_steps)
        self.cfg.assignment_cooldown_budget_min_streak = int(budget_min_streak)
        self.cfg.max_base_xy_step = tuple(float(value) for value in max_base_xy_step)
        self.cfg.assignment_redirect_guardrail_enabled = bool(redirect_guardrail_enabled)
        self.cfg.assignment_redirect_guardrail_window_steps = int(redirect_guardrail_window_steps)
        self.cfg.assignment_redirect_guardrail_claimed_target_enabled = bool(
            redirect_guardrail_claimed_target_enabled
        )
        self.cfg.assignment_redirect_guardrail_spacing_enabled = bool(redirect_guardrail_spacing_enabled)
        self.cfg.assignment_redirect_guardrail_spacing_threshold = redirect_guardrail_spacing_threshold
        self.cfg.assignment_redirect_guardrail_fail_open_spacing = bool(redirect_guardrail_fail_open_spacing)
        self.cfg.assignment_redirect_guardrail_fail_open_claimed = bool(redirect_guardrail_fail_open_claimed)
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
    disabled = _make_wrapper(cooldown_enabled=False)
    disabled_problem = disabled.unwrapped.get_assignment_problem()
    disabled._per_robot_target_cooldown_remaining[0, 0, 2] = 7
    disabled_mask = disabled._build_available_actions(problem=disabled_problem)
    baseline_mask = make_assignment_action_mask(disabled_problem, include_noop=True)
    _assert(torch.equal(disabled_mask, baseline_mask), "cooldown disabled path changed available_actions")
    disabled_info = disabled._assignment_cooldown_info()
    _assert(float(disabled_info["enabled"]) == 0.0, "disabled info must report enabled=0")
    _assert(float(disabled_info["active_count"].sum().item()) == 0.0, "disabled active diagnostics must be zero")

    enabled = _make_wrapper(cooldown_enabled=True)
    problem = enabled.unwrapped.get_assignment_problem()
    obs, shared_obs, available_actions = enabled.reset()
    _assert(tuple(obs["robot_0"].shape) == (2, 909), "actor obs dim changed from 909")
    _assert(tuple(shared_obs.shape) == (2, 3, 2727), "shared obs dim changed from 2727")
    _assert(tuple(available_actions.shape) == (2, 3, 51), "available_actions shape changed from [2,3,51]")

    enabled._per_robot_target_cooldown_remaining[0, 0, 2] = 3
    masked = enabled._build_available_actions(problem=problem)
    _assert(float(masked[0, 0, 2].item()) == 0.0, "cooldown did not mask selected robot-target pair")
    _assert(float(masked[0, 1, 2].item()) == 1.0, "cooldown masked the same viewpoint for another robot")
    _assert(bool(torch.all(masked[..., -1] == 1.0)), "noop column must remain available")
    _assert(bool(torch.all(masked.sum(dim=-1) > 0.0)), "cooldown produced an all-zero action row")

    noop_assignment = torch.full((2, 3), -1, dtype=torch.long)
    pre = enabled.unwrapped.get_assignment_problem()
    post = enabled.unwrapped.get_assignment_problem()
    _update(enabled, noop_assignment, pre, post)
    _assert(int(enabled._per_robot_target_cooldown_remaining[0, 0, 2].item()) == 2, "cooldown did not decrement")

    covered_post = enabled.unwrapped.get_assignment_problem()
    covered_post["viewpoints_covered"] = covered_post["viewpoints_covered"].clone()
    covered_post["viewpoints_covered"][0, 2] = True
    _update(enabled, noop_assignment, pre, covered_post)
    _assert(
        int(enabled._per_robot_target_cooldown_remaining[0, :, 2].sum().item()) == 0,
        "covered target did not clear cooldown",
    )
    _assert(
        int(enabled._per_robot_target_failed_attempt_count[0, :, 2].sum().item()) == 0,
        "covered target did not clear failed-attempt count",
    )

    trigger_wrapper = _make_wrapper(
        cooldown_enabled=True,
        trigger_attempts=1,
        trigger_same_target_streak=999,
        trigger_steps_since_global_gain=0,
        duration_steps=4,
    )
    trigger_problem = trigger_wrapper.unwrapped.get_assignment_problem()
    trigger_assignment = torch.full((2, 3), -1, dtype=torch.long)
    trigger_assignment[:, 0] = 1
    _update(trigger_wrapper, trigger_assignment, trigger_problem, trigger_problem)
    _assert(int(trigger_wrapper._per_robot_target_failed_attempt_count[0, 0, 1].item()) == 1, "failed count missing")
    _assert(int(trigger_wrapper._per_robot_target_cooldown_remaining[0, 0, 1].item()) == 4, "cooldown did not trigger")
    _assert(bool(trigger_wrapper._last_cooldown_triggered_after_step[0, 0].item()), "trigger diagnostic missing")
    trigger_mask = trigger_wrapper._build_available_actions(problem=trigger_problem)
    _assert(float(trigger_mask[0, 0, 1].item()) == 0.0, "triggered cooldown did not filter mask")
    _assert(float(trigger_mask[0, 1, 1].item()) == 1.0, "per-robot cooldown leaked to another robot")

    budget_wrapper = _make_wrapper(
        cooldown_enabled=True,
        trigger_mode="budget_and_streak",
        trigger_attempts=999999,
        trigger_same_target_streak=999999,
        trigger_steps_since_global_gain=0,
        duration_steps=5,
        budget_multiplier=1.0,
        budget_slack_steps=1,
        budget_min_streak=1,
        max_base_xy_step=(1.0, 1.0, 1.0),
    )
    budget_problem = budget_wrapper.unwrapped.get_assignment_problem()
    budget_assignment = torch.full((2, 3), -1, dtype=torch.long)
    budget_assignment[:, 0] = 1
    _update(budget_wrapper, budget_assignment, budget_problem, budget_problem)
    _assert(
        int(budget_wrapper._per_robot_target_cooldown_remaining[0, 0, 1].item()) == 0,
        "budget cooldown triggered before budget exhaustion at step 1",
    )
    _assert(int(budget_wrapper._last_budget_steps_for_selected_pair[0, 0].item()) == 3, "budget steps mismatch")
    _update(budget_wrapper, budget_assignment, budget_problem, budget_problem)
    _assert(
        int(budget_wrapper._per_robot_target_cooldown_remaining[0, 0, 1].item()) == 0,
        "budget cooldown triggered before budget exhaustion at step 2",
    )
    _update(budget_wrapper, budget_assignment, budget_problem, budget_problem)
    _assert(
        int(budget_wrapper._per_robot_target_cooldown_remaining[0, 0, 1].item()) == 5,
        "budget cooldown did not trigger at budget exhaustion",
    )
    _assert(bool(budget_wrapper._last_budget_triggered_by_budget[0, 0].item()), "budget trigger diagnostic missing")
    budget_mask = budget_wrapper._build_available_actions(problem=budget_problem)
    _assert(float(budget_mask[0, 0, 1].item()) == 0.0, "budget trigger did not filter selected pair")
    _assert(float(budget_mask[0, 1, 1].item()) == 1.0, "budget trigger leaked to another robot")
    _assert(bool(torch.all(budget_mask[..., -1] == 1.0)), "budget trigger masked noop")
    budget_wrapper._reset_assignment_diagnostics(problem=budget_problem)
    _assert(int(budget_wrapper._budget_attempt_steps.sum().item()) == 0, "full reset missed budget attempt steps")
    _assert(int((budget_wrapper._budget_attempt_target >= 0).sum().item()) == 0, "full reset missed budget targets")

    guardrail_disabled = _make_wrapper(
        cooldown_enabled=False,
        redirect_guardrail_enabled=False,
    )
    guardrail_disabled_problem = guardrail_disabled.unwrapped.get_assignment_problem()
    guardrail_disabled._assignment_redirect_guardrail_remaining[0, 0] = 1
    guardrail_disabled._previous_assignment[0, 1] = 2
    guardrail_disabled_mask = guardrail_disabled._build_available_actions(problem=guardrail_disabled_problem)
    guardrail_disabled_baseline = make_assignment_action_mask(guardrail_disabled_problem, include_noop=True)
    _assert(
        torch.equal(guardrail_disabled_mask, guardrail_disabled_baseline),
        "disabled redirect guardrail changed available_actions",
    )
    _assert(bool(torch.all(guardrail_disabled_mask[..., -1] == 1.0)), "disabled redirect guardrail masked noop")

    guardrail = _make_wrapper(
        cooldown_enabled=True,
        num_envs=1,
        num_agents=3,
        num_viewpoints=6,
        redirect_guardrail_enabled=True,
    )
    guardrail.unwrapped.viewpoint_pos[3, 0] = 2.4
    guardrail_problem = guardrail.unwrapped.get_assignment_problem()
    guardrail_available_before = guardrail_problem["available_mask"].clone()
    guardrail._assignment_redirect_guardrail_remaining[0, 0] = 1
    guardrail._previous_assignment[0] = torch.tensor([-1, 2, -1], dtype=torch.long)
    guardrail_mask = guardrail._build_available_actions(problem=guardrail_problem)
    _assert(
        torch.equal(guardrail_problem["available_mask"], guardrail_available_before),
        "redirect guardrail mutated base available_mask",
    )
    _assert(tuple(guardrail_mask.shape) == (1, 3, 7), "redirect guardrail changed available_actions shape")
    _assert(float(guardrail_mask[0, 0, 2].item()) == 0.0, "claimed-target guardrail did not suppress claim")
    _assert(float(guardrail_mask[0, 0, 3].item()) == 0.0, "spacing guardrail did not suppress nearby target")
    _assert(float(guardrail_mask[0, 0, 4].item()) == 1.0, "spacing guardrail over-suppressed distant target")
    _assert(float(guardrail_mask[0, 1, 2].item()) == 1.0, "guardrail affected robot without active redirect window")
    _assert(float(guardrail_mask[0, 1, 3].item()) == 1.0, "spacing affected robot without active redirect window")
    _assert(float(guardrail_mask[0, 0, -1].item()) == 1.0, "redirect guardrail masked noop")
    _assert(
        int(guardrail._last_redirect_guardrail_claimed_suppressed_count[0, 0].item()) == 1,
        "claimed-target suppression count mismatch",
    )
    _assert(
        int(guardrail._last_redirect_guardrail_spacing_suppressed_count[0, 0].item()) == 1,
        "spacing suppression count mismatch",
    )
    _assert(
        guardrail._last_redirect_guardrail_claimed_target_robot_ids[0][0] == [1],
        "claimed-target suppressor robot ids missing",
    )
    _assert(
        guardrail._last_redirect_guardrail_nearby_target_robot_ids[0][0] == [1],
        "nearby-target suppressor robot ids missing",
    )

    spacing_fail_open = _make_wrapper(
        cooldown_enabled=True,
        num_envs=1,
        num_agents=3,
        num_viewpoints=3,
        redirect_guardrail_enabled=True,
    )
    spacing_fail_open.unwrapped.viewpoint_pos[1, 0] = 0.4
    spacing_problem = spacing_fail_open.unwrapped.get_assignment_problem()
    spacing_problem["available_mask"] = spacing_problem["available_mask"].clone()
    spacing_problem["available_mask"][0, 0, :] = False
    spacing_problem["available_mask"][0, 0, 0] = True
    spacing_problem["available_mask"][0, 0, 1] = True
    spacing_available_before = spacing_problem["available_mask"].clone()
    spacing_fail_open._assignment_redirect_guardrail_remaining[0, 0] = 1
    spacing_fail_open._previous_assignment[0] = torch.tensor([-1, 0, -1], dtype=torch.long)
    spacing_mask = spacing_fail_open._build_available_actions(problem=spacing_problem)
    _assert(torch.equal(spacing_problem["available_mask"], spacing_available_before), "spacing fail-open mutated mask")
    _assert(float(spacing_mask[0, 0, 0].item()) == 0.0, "claimed target should remain suppressed before spacing")
    _assert(float(spacing_mask[0, 0, 1].item()) == 1.0, "spacing over-mask did not fail open")
    _assert(
        spacing_fail_open._last_redirect_guardrail_fail_open_reason[0][0] == "spacing_overmask",
        "spacing fail-open reason missing",
    )
    _assert(
        int(spacing_fail_open._last_redirect_guardrail_spacing_suppressed_count[0, 0].item()) == 0,
        "failed-open spacing should not count as actual suppression",
    )

    claimed_fail_open = _make_wrapper(
        cooldown_enabled=True,
        num_envs=1,
        num_agents=3,
        num_viewpoints=2,
        redirect_guardrail_enabled=True,
        redirect_guardrail_spacing_enabled=False,
    )
    claimed_problem = claimed_fail_open.unwrapped.get_assignment_problem()
    claimed_problem["available_mask"] = claimed_problem["available_mask"].clone()
    claimed_problem["available_mask"][0, 0, :] = False
    claimed_problem["available_mask"][0, 0, 0] = True
    claimed_fail_open._assignment_redirect_guardrail_remaining[0, 0] = 1
    claimed_fail_open._previous_assignment[0] = torch.tensor([-1, 0, -1], dtype=torch.long)
    claimed_mask = claimed_fail_open._build_available_actions(problem=claimed_problem)
    _assert(float(claimed_mask[0, 0, 0].item()) == 1.0, "claimed over-mask did not fail open")
    _assert(
        claimed_fail_open._last_redirect_guardrail_fail_open_reason[0][0] == "claimed_overmask",
        "claimed fail-open reason missing",
    )
    _assert(
        int(claimed_fail_open._last_redirect_guardrail_claimed_suppressed_count[0, 0].item()) == 0,
        "failed-open claimed mask should not count as actual suppression",
    )
    _assert(float(claimed_mask[0, 0, -1].item()) == 1.0, "claimed fail-open masked noop")

    redirect_budget_wrapper = _make_wrapper(
        cooldown_enabled=True,
        trigger_mode="budget_and_streak",
        trigger_attempts=999999,
        trigger_same_target_streak=999999,
        trigger_steps_since_global_gain=0,
        duration_steps=5,
        budget_multiplier=1.0,
        budget_slack_steps=1,
        budget_min_streak=1,
        max_base_xy_step=(1.0, 1.0, 1.0),
        redirect_guardrail_enabled=True,
    )
    redirect_budget_problem = redirect_budget_wrapper.unwrapped.get_assignment_problem()
    redirect_budget_assignment = torch.full((2, 3), -1, dtype=torch.long)
    redirect_budget_assignment[:, 0] = 1
    _update(redirect_budget_wrapper, redirect_budget_assignment, redirect_budget_problem, redirect_budget_problem)
    _update(redirect_budget_wrapper, redirect_budget_assignment, redirect_budget_problem, redirect_budget_problem)
    _update(redirect_budget_wrapper, redirect_budget_assignment, redirect_budget_problem, redirect_budget_problem)
    _assert(
        int(redirect_budget_wrapper._assignment_redirect_guardrail_remaining[0, 0].item()) == 1,
        "budget trigger did not activate redirect guardrail window",
    )
    _assert(
        int(redirect_budget_wrapper._assignment_redirect_guardrail_triggered_target[0, 0].item()) == 1,
        "redirect guardrail did not record triggered target",
    )
    redirect_guarded_mask = redirect_budget_wrapper._build_available_actions(problem=redirect_budget_problem)
    _assert(
        bool(redirect_budget_wrapper._last_redirect_guardrail_active_for_robot[0, 0].item()),
        "redirect guardrail active diagnostic missing after budget trigger",
    )
    _assert(float(redirect_guarded_mask[0, 0, -1].item()) == 1.0, "active redirect guardrail masked noop")
    redirect_noop = torch.full((2, 3), -1, dtype=torch.long)
    _update(redirect_budget_wrapper, redirect_noop, redirect_budget_problem, redirect_budget_problem)
    _assert(
        int(redirect_budget_wrapper._assignment_redirect_guardrail_remaining[0, 0].item()) == 0,
        "redirect guardrail window did not decrement after next action",
    )

    trigger_wrapper._per_robot_target_cooldown_remaining[:] = 5
    trigger_wrapper._per_robot_target_failed_attempt_count[:] = 5
    trigger_wrapper._assignment_cooldown_trigger_count[:] = 3.0
    trigger_wrapper._reset_assignment_diagnostics(
        env_ids=torch.tensor([1], dtype=torch.long),
        problem=trigger_problem,
    )
    _assert(int(trigger_wrapper._per_robot_target_cooldown_remaining[1].sum().item()) == 0, "partial reset missed done env")
    _assert(int(trigger_wrapper._per_robot_target_failed_attempt_count[1].sum().item()) == 0, "partial reset missed counts")
    _assert(int(trigger_wrapper._per_robot_target_cooldown_remaining[0].sum().item()) > 0, "partial reset cleared wrong env")

    trigger_wrapper._reset_assignment_diagnostics(problem=trigger_problem)
    _assert(int(trigger_wrapper._per_robot_target_cooldown_remaining.sum().item()) == 0, "full reset missed cooldown")
    _assert(int(trigger_wrapper._per_robot_target_failed_attempt_count.sum().item()) == 0, "full reset missed counts")

    return {
        "status": "passed",
        "actor_obs_shape": list(obs["robot_0"].shape),
        "shared_obs_shape": list(shared_obs.shape),
        "available_actions_shape": list(available_actions.shape),
        "disabled_mask_matches_baseline": True,
        "manual_pair_masked": True,
        "other_robot_same_viewpoint_available": True,
        "noop_available": True,
        "cooldown_decremented": True,
        "covered_target_cleared": True,
        "budget_trigger_waited_until_budget": True,
        "budget_trigger_masked_pair_only": True,
        "budget_reset_cleared": True,
        "redirect_guardrail_disabled_matches_baseline": True,
        "redirect_guardrail_claimed_target_suppressed": True,
        "redirect_guardrail_spacing_suppressed": True,
        "redirect_guardrail_scope_limited_to_active_window": True,
        "redirect_guardrail_spacing_fail_open": True,
        "redirect_guardrail_claimed_fail_open": True,
        "redirect_guardrail_window_activated_by_budget_trigger": True,
        "redirect_guardrail_window_decremented_after_action": True,
        "redirect_guardrail_base_mask_not_mutated": True,
        "redirect_guardrail_noop_available": True,
        "full_reset_cleared": True,
        "partial_reset_cleared_done_env_only": True,
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
    print(f"[OK]: assignment cooldown mask smoke passed: {json.dumps(result, sort_keys=True)}")


if __name__ == "__main__":
    main()
