# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import math
from typing import Any, Mapping

import gymnasium
import numpy as np
import torch
import torch.nn.functional as F

try:
    from .assignment_harl_adapter import (
        AssignmentHarlAdapter,
        get_harl_scalar_action_dim,
        make_assignment_discrete_action_spaces,
        make_harl_action_tensor,
    )
    from .assignment_rl_interface import (
        assignment_to_env_actions,
        compute_assignment_duplicate_count,
        make_assignment_action_mask,
    )
    from .assignment_lifecycle_resolver_runtime import AssignmentLifecycleResolverRuntimeAdapter
except ImportError:  # Allows direct file-based smoke tests after adding this directory to sys.path.
    from assignment_harl_adapter import (  # type: ignore
        AssignmentHarlAdapter,
        get_harl_scalar_action_dim,
        make_assignment_discrete_action_spaces,
        make_harl_action_tensor,
    )
    from assignment_rl_interface import (  # type: ignore
        assignment_to_env_actions,
        compute_assignment_duplicate_count,
        make_assignment_action_mask,
    )
    from assignment_lifecycle_resolver_runtime import AssignmentLifecycleResolverRuntimeAdapter  # type: ignore


class AssignmentHarlWrapper:
    """Repo-local HARL-facing wrapper for assignment-based scan actions.

    The wrapped scan env keeps its original 9D continuous action space. This wrapper exposes
    ``Discrete(num_viewpoints + 1)`` per agent, decodes scalar ids into an assignment tensor,
    calls the existing assignment controller, then forwards the resulting 9D action dict.
    """

    def __init__(self, env: Any, include_noop: bool = True, strict_decode: bool = True) -> None:
        self._env = env
        self._unwrapped = getattr(env, "unwrapped", env)
        self.include_noop = include_noop
        self.strict_decode = strict_decode

        self._agents = self._initial_agents()
        self._agent_map = {agent: index for index, agent in enumerate(self._agents)}
        self._agent_map_inv = {index: agent for agent, index in self._agent_map.items()}
        self._num_agents = len(self._agents)
        self._num_envs = int(getattr(self._unwrapped, "num_envs"))
        self._num_viewpoints = self._infer_num_viewpoints()
        self._device = torch.device(getattr(self._unwrapped, "device", "cpu"))
        self._normalization_horizon = max(1, int(getattr(self._unwrapped, "max_episode_length", 300) or 300))
        self._assignment_reward_config = self._build_assignment_reward_config()
        self._assignment_cooldown_config = self._build_assignment_cooldown_config()
        self._assignment_redirect_guardrail_config = self._build_assignment_redirect_guardrail_config()
        self._assignment_failed_pair_memory_config = self._build_assignment_failed_pair_memory_config()
        self._assignment_lifecycle_resolver_config = self._build_assignment_lifecycle_resolver_config()
        self._max_base_xy_step_by_agent = self._infer_max_base_xy_step_by_agent()

        self._adapter = AssignmentHarlAdapter(
            num_envs=self._num_envs,
            num_agents=self._num_agents,
            num_viewpoints=self._num_viewpoints,
            device=self._device,
        )
        self._action_space = make_assignment_discrete_action_spaces(self._num_agents, self._num_viewpoints)
        self._max_scalar_action_dim = max(get_harl_scalar_action_dim(space) for space in self._action_space.values())

        self.last_assignment: torch.Tensor | None = None
        self.last_assignment_proposal: torch.Tensor | None = None
        self.last_effective_assignment: torch.Tensor | None = None
        self.last_env_actions: dict[str, torch.Tensor] | None = None
        self.last_pre_step_available_actions: torch.Tensor | None = None
        self.last_available_actions: torch.Tensor | None = None
        self.last_duplicate_count: torch.Tensor | None = None
        self.last_noop_count: torch.Tensor | None = None
        self.last_valid_action_count: torch.Tensor | None = None
        self.last_selected_available_mask: torch.Tensor | None = None
        self.last_assignment_reward_terms: dict[str, Any] | None = None
        self._last_assignment_lifecycle_resolution: dict[str, Any] | None = None
        self._assignment_lifecycle_resolver_runtime = AssignmentLifecycleResolverRuntimeAdapter(
            enabled=bool(self._assignment_lifecycle_resolver_config["enabled"]),
            num_envs=self._num_envs,
            num_robots=self._num_agents,
            num_tasks=self._num_viewpoints,
            device=self._device,
            method_name="assignment_harl_wrapper",
            output_dir=self._assignment_lifecycle_resolver_config["output_dir"],
            log_diagnostics=bool(self._assignment_lifecycle_resolver_config["log_diagnostics"]),
            strict_proposals=bool(self._assignment_lifecycle_resolver_config["strict_proposals"]),
        )

        self._viewpoint_row_fields = (
            "relative_viewpoint_position_x",
            "relative_viewpoint_position_y",
            "relative_viewpoint_position_z",
            "viewpoint_quaternion_w",
            "viewpoint_quaternion_x",
            "viewpoint_quaternion_y",
            "viewpoint_quaternion_z",
            "covered_flag",
            "available_flag",
            "feasible_flag",
            "static_geometric_feasible_flag",
            "normalized_selected_path_cost",
            "per_viewpoint_attempted_count_norm",
            "per_viewpoint_last_attempt_age_norm",
        )
        self._noop_context_fields = (
            "agent_has_any_available_viewpoint",
            "team_has_any_available_viewpoint",
            "all_viewpoints_covered",
            "previous_assignment_was_noop",
            "episode_progress_norm",
        )
        self._dynamic_scalar_fields = (
            "consecutive_same_target_count_norm",
            "steps_since_last_global_coverage_gain_norm",
            "per_robot_completed_count_norm",
            "per_robot_repeated_assignment_count_norm",
            "global_coverage_ratio",
            "total_uncovered_count_norm",
            "episode_progress_norm",
        )
        self._viewpoint_row_dim = len(self._viewpoint_row_fields)
        self._noop_context_dim = len(self._noop_context_fields)
        self._previous_assignment_one_hot_dim = self._num_viewpoints + 1
        self._assignment_extension_dim = (
            self._num_viewpoints * self._viewpoint_row_dim
            + self._noop_context_dim
            + self._previous_assignment_one_hot_dim
            + len(self._dynamic_scalar_fields)
            + self._num_viewpoints
        )
        self._raw_observation_dims = self._infer_raw_observation_dims()
        self._observation_space = self._make_observation_space()
        self._share_observation_space = self._make_share_observation_space()
        self._reset_assignment_diagnostics()

    def __getattr__(self, key: str) -> Any:
        if hasattr(self._env, key):
            return getattr(self._env, key)
        if hasattr(self._unwrapped, key):
            return getattr(self._unwrapped, key)
        raise AttributeError(f"Wrapped environment ({self._unwrapped.__class__.__name__}) has no attribute '{key}'")

    @property
    def unwrapped(self) -> Any:
        return self._unwrapped

    @property
    def env(self) -> Any:
        """Expose the underlying scan env for HARL save/video traversal compatibility."""
        return self._unwrapped

    @property
    def num_envs(self) -> int:
        return self._num_envs

    @property
    def num_agents(self) -> int:
        return self._num_agents

    @property
    def n_agents(self) -> int:
        return self._num_agents

    @property
    def num_viewpoints(self) -> int:
        return self._num_viewpoints

    @property
    def noop_action_id(self) -> int:
        return self._adapter.noop_action_id

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def agents(self) -> list[str]:
        return list(self._agents)

    @property
    def possible_agents(self) -> list[str]:
        return list(self._agents)

    @property
    def action_space(self) -> Mapping[int, gymnasium.Space]:
        return self._action_space

    @property
    def max_scalar_action_dim(self) -> int:
        return self._max_scalar_action_dim

    @property
    def observation_space(self) -> Mapping[int, gymnasium.Space]:
        return self._observation_space

    @property
    def observation_spaces(self) -> Mapping[str, gymnasium.Space]:
        return {agent: self._observation_space[self._agent_map[agent]] for agent in self._agents}

    @property
    def share_observation_space(self) -> Mapping[int, gymnasium.Space]:
        return self._share_observation_space

    @property
    def assignment_observation_layout(self) -> dict[str, Any]:
        raw_dim = max(self._raw_observation_dims.values()) if self._raw_observation_dims else 0
        viewpoint_rows_start = raw_dim
        noop_context_start = viewpoint_rows_start + self._num_viewpoints * self._viewpoint_row_dim
        previous_assignment_start = noop_context_start + self._noop_context_dim
        covered_vector_start = previous_assignment_start + self._previous_assignment_one_hot_dim + len(
            self._dynamic_scalar_fields
        )
        return {
            "raw_observation_dim_by_agent": dict(self._raw_observation_dims),
            "raw_observation_dim": raw_dim,
            "assignment_extension_dim": self._assignment_extension_dim,
            "actor_observation_dim_by_agent": {
                agent: self._raw_observation_dims[agent] + self._assignment_extension_dim for agent in self._agents
            },
            "shared_observation_dim": sum(
                self._raw_observation_dims[agent] + self._assignment_extension_dim for agent in self._agents
            ),
            "num_agents": self._num_agents,
            "num_viewpoints": self._num_viewpoints,
            "noop_action_id": self.noop_action_id,
            "viewpoint_rows_start": viewpoint_rows_start,
            "viewpoint_row_dim": self._viewpoint_row_dim,
            "viewpoint_row_fields": list(self._viewpoint_row_fields),
            "viewpoint_row_field_offsets": {field: index for index, field in enumerate(self._viewpoint_row_fields)},
            "noop_context_start": noop_context_start,
            "noop_context_dim": self._noop_context_dim,
            "noop_context_fields": list(self._noop_context_fields),
            "previous_assignment_one_hot_start": previous_assignment_start,
            "previous_assignment_one_hot_dim": self._previous_assignment_one_hot_dim,
            "dynamic_scalar_start": previous_assignment_start + self._previous_assignment_one_hot_dim,
            "dynamic_scalar_fields": list(self._dynamic_scalar_fields),
            "covered_vector_start": covered_vector_start,
            "covered_vector_dim": self._num_viewpoints,
            "normalization_horizon": self._normalization_horizon,
        }

    @property
    def assignment_reward_config(self) -> dict[str, float | int]:
        return dict(self._assignment_reward_config)

    @property
    def assignment_cooldown_config(self) -> dict[str, bool | float | int | str]:
        return dict(self._assignment_cooldown_config)

    @property
    def assignment_redirect_guardrail_config(self) -> dict[str, bool | float | int | str | None]:
        return dict(self._assignment_redirect_guardrail_config)

    @property
    def assignment_failed_pair_memory_config(self) -> dict[str, bool | int | str]:
        return dict(self._assignment_failed_pair_memory_config)

    @property
    def assignment_lifecycle_resolver_config(self) -> dict[str, bool | str | None]:
        return dict(self._assignment_lifecycle_resolver_config)

    def get_last_assignment_lifecycle_resolution(self) -> dict[str, Any] | None:
        return self._clone_lifecycle_resolution_payload(self._last_assignment_lifecycle_resolution)

    def reset(self, *args, **kwargs) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor]:
        obs, _ = self._env.reset(*args, **kwargs)
        problem = self._unwrapped.get_assignment_problem()
        self._reset_assignment_diagnostics(problem=problem)
        self._assignment_lifecycle_resolver_runtime.reset_envs(env_ids=None)
        self._last_assignment_lifecycle_resolution = None
        self.last_assignment_reward_terms = None
        obs = self._augment_assignment_observations(obs, problem=problem)
        self._sync_agents(obs)
        shared_obs = self._build_shared_obs(obs)
        available_actions = self._build_available_actions(problem=problem)
        self.last_available_actions = available_actions
        return obs, shared_obs, available_actions

    def step(
        self,
        discrete_actions: torch.Tensor,
        layout: str | None = None,
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor, torch.Tensor, dict, torch.Tensor]:
        pre_step_problem = self._unwrapped.get_assignment_problem()
        pre_step_available_actions = self._build_available_actions(problem=pre_step_problem)
        self._capture_pre_step_assignment_redirect_guardrail_diagnostics()
        assignment_proposal = self.decode_actions(discrete_actions, layout=layout)
        lifecycle_pre_result = self._assignment_lifecycle_resolver_runtime.resolve_pre_step(
            problem=pre_step_problem,
            assignment_proposal=assignment_proposal,
            method_metadata={
                "method_name": "assignment_harl_wrapper",
                "proposal_type": "decoded_rl_assignment",
            },
        )
        effective_assignment = lifecycle_pre_result.effective_assignment.to(device=self._device, dtype=torch.long)
        env_actions = self.assignment_to_env_actions(effective_assignment)
        selected_available_mask = self._selected_available_mask(effective_assignment, pre_step_available_actions)

        obs, rewards, terminated, truncated, info = self._env.step(env_actions)
        post_step_problem = self._unwrapped.get_assignment_problem()
        dones = self._stack_dones(terminated, truncated)
        done_env_ids = torch.nonzero(torch.all(dones, dim=1), as_tuple=False).flatten()
        self._update_assignment_diagnostics(
            assignment=effective_assignment,
            pre_step_problem=pre_step_problem,
            post_step_problem=post_step_problem,
            selected_available_mask=selected_available_mask,
        )

        reward_tensor = self._stack_rewards(rewards)
        reward_decomposition = self._compute_assignment_reward_decomposition(
            base_reward_tensor=reward_tensor,
            assignment=effective_assignment,
            pre_step_problem=pre_step_problem,
            post_step_problem=post_step_problem,
        )
        reward_tensor = reward_decomposition["final_reward"]
        duplicate_count = compute_assignment_duplicate_count(effective_assignment)
        noop_count = (effective_assignment < 0).sum(dim=1).to(dtype=torch.float32)
        valid_action_count = (effective_assignment >= 0).sum(dim=1).to(dtype=torch.float32)

        self.last_assignment = effective_assignment
        self.last_assignment_proposal = assignment_proposal
        self.last_effective_assignment = effective_assignment
        self.last_env_actions = env_actions
        self.last_pre_step_available_actions = pre_step_available_actions
        self.last_duplicate_count = duplicate_count
        self.last_noop_count = noop_count
        self.last_valid_action_count = valid_action_count
        self.last_selected_available_mask = selected_available_mask
        self.last_assignment_reward_terms = reward_decomposition

        info = self._augment_info(
            info,
            duplicate_count=duplicate_count,
            noop_count=noop_count,
            valid_action_count=valid_action_count,
            selected_available_mask=selected_available_mask,
            reward_decomposition=reward_decomposition,
        )

        lifecycle_external = self._assignment_lifecycle_resolver_runtime.budget_failure_diagnostics(
            effective_assignment=effective_assignment,
            info=info if isinstance(info, Mapping) else None,
        )
        lifecycle_post_result = self._assignment_lifecycle_resolver_runtime.observe_post_step(
            pre_step_problem=pre_step_problem,
            assignment_proposal=assignment_proposal,
            effective_assignment=effective_assignment,
            post_step_problem=post_step_problem,
            external_diagnostics=lifecycle_external,
            done_env_ids=done_env_ids,
            method_metadata={
                "method_name": "assignment_harl_wrapper",
                "proposal_type": "decoded_rl_assignment",
            },
        )
        lifecycle_events = self._assignment_lifecycle_resolver_runtime.pop_events()
        self._last_assignment_lifecycle_resolution = self._make_lifecycle_resolution_payload(
            assignment_proposal=assignment_proposal,
            effective_assignment=effective_assignment,
            pre_result=lifecycle_pre_result,
            post_result=lifecycle_post_result,
            events=lifecycle_events,
        )

        if done_env_ids.numel() > 0:
            self._reset_assignment_diagnostics(env_ids=done_env_ids, problem=post_step_problem)

        obs = self._augment_assignment_observations(obs, problem=post_step_problem)
        self._sync_agents(obs)
        shared_obs = self._build_shared_obs(obs)
        available_actions = self._build_available_actions(problem=post_step_problem)
        self.last_available_actions = available_actions
        return obs, shared_obs, reward_tensor, dones, info, available_actions

    def close(self) -> None:
        self.finalize_assignment_lifecycle_resolver()
        self._env.close()

    def finalize_assignment_lifecycle_resolver(self) -> dict[str, Any]:
        return self._assignment_lifecycle_resolver_runtime.finalize()

    def make_action_tensor(self, dtype: torch.dtype = torch.float32) -> torch.Tensor:
        return make_harl_action_tensor(self._num_envs, self._action_space, device=self._device, dtype=dtype)

    def make_available_actions(self) -> torch.Tensor:
        return self._build_available_actions()

    def decode_actions(self, discrete_actions: torch.Tensor, layout: str | None = None, strict: bool | None = None) -> torch.Tensor:
        if layout is None:
            layout = self._infer_action_layout(discrete_actions)
        if strict is None:
            strict = self.strict_decode
        return self._adapter.decode_actions(discrete_actions, layout=layout, strict=strict)

    def assignment_to_env_actions(self, assignment: torch.Tensor) -> dict[str, torch.Tensor]:
        return assignment_to_env_actions(self._unwrapped, assignment)

    def _initial_agents(self) -> list[str]:
        if hasattr(self._unwrapped, "possible_agents"):
            agents = list(self._unwrapped.possible_agents)
        elif hasattr(self._unwrapped, "agents"):
            agents = list(self._unwrapped.agents)
        else:
            raise AttributeError("assignment HARL wrapper requires a multi-agent env with possible_agents or agents")
        if not agents:
            raise ValueError("assignment HARL wrapper requires at least one agent")
        return agents

    def _sync_agents(self, obs: dict[str, torch.Tensor]) -> None:
        agents = [agent for agent in self._agents if agent in obs]
        if len(agents) != self._num_agents:
            raise RuntimeError(
                f"assignment wrapper expects fixed agents {self._agents}, got observation keys {list(obs.keys())}"
            )

    def _infer_num_viewpoints(self) -> int:
        if hasattr(self._unwrapped, "num_viewpoints"):
            return int(self._unwrapped.num_viewpoints)
        cfg = getattr(self._unwrapped, "cfg", None)
        if cfg is not None and hasattr(cfg, "viewpoint_poses"):
            return len(cfg.viewpoint_poses)
        problem = self._unwrapped.get_assignment_problem()
        return int(problem["num_viewpoints"])

    def _build_assignment_reward_config(self) -> dict[str, float | int]:
        cfg = getattr(self._unwrapped, "cfg", None)

        def _float_attr(name: str, default: float) -> float:
            value = getattr(cfg, name, default)
            return float(value)

        def _int_attr(name: str, default: int) -> int:
            value = getattr(cfg, name, default)
            return max(0, int(value))

        return {
            "repeated_assignment_penalty_scale": _float_attr("repeated_assignment_penalty_scale", 0.01),
            "repeated_assignment_grace_steps": _int_attr("repeated_assignment_grace_steps", 2),
            "no_progress_penalty_scale": _float_attr("no_progress_penalty_scale", 0.01),
            "no_progress_grace_steps": _int_attr("no_progress_grace_steps", 2),
            "no_progress_penalty_cap": max(0.0, _float_attr("no_progress_penalty_cap", 0.05)),
            "selected_path_cost_penalty_scale": _float_attr("selected_path_cost_penalty_scale", 0.0),
        }

    def _build_assignment_cooldown_config(self) -> dict[str, bool | float | int | str]:
        cfg = getattr(self._unwrapped, "cfg", None)

        def _bool_attr(name: str, default: bool) -> bool:
            return bool(getattr(cfg, name, default))

        def _int_attr(name: str, default: int) -> int:
            return max(0, int(getattr(cfg, name, default)))

        def _float_attr(name: str, default: float) -> float:
            return max(0.0, float(getattr(cfg, name, default)))

        scope = str(getattr(cfg, "assignment_cooldown_scope", "per_robot_target")).strip().lower()
        if scope != "per_robot_target":
            raise ValueError(
                "assignment_cooldown_scope currently supports only 'per_robot_target', "
                f"got {scope!r}"
            )
        trigger_mode = str(getattr(cfg, "assignment_cooldown_trigger_mode", "streak")).strip().lower()
        if trigger_mode not in {"streak", "budget", "budget_and_streak"}:
            raise ValueError(
                "assignment_cooldown_trigger_mode must be one of 'streak', 'budget', or 'budget_and_streak', "
                f"got {trigger_mode!r}"
            )

        return {
            "enabled": _bool_attr("assignment_cooldown_enabled", False),
            "scope": scope,
            "trigger_mode": trigger_mode,
            "trigger_attempts": _int_attr("assignment_cooldown_trigger_attempts", 3),
            "trigger_same_target_streak": _int_attr("assignment_cooldown_trigger_same_target_streak", 10),
            "trigger_steps_since_global_gain": _int_attr(
                "assignment_cooldown_trigger_steps_since_global_gain",
                10,
            ),
            "duration_steps": _int_attr("assignment_cooldown_duration_steps", 20),
            "require_uncovered": _bool_attr("assignment_cooldown_require_uncovered", True),
            "require_available": _bool_attr("assignment_cooldown_require_available", True),
            "require_feasible": _bool_attr("assignment_cooldown_require_feasible", True),
            "require_no_global_gain": _bool_attr("assignment_cooldown_require_no_global_gain", True),
            "clear_on_covered": _bool_attr("assignment_cooldown_clear_on_covered", True),
            "apply_to_action_mask": _bool_attr("assignment_cooldown_apply_to_action_mask", True),
            "log_diagnostics": _bool_attr("assignment_cooldown_log_diagnostics", True),
            "budget_multiplier": _float_attr("assignment_cooldown_budget_multiplier", 1.5),
            "budget_slack_steps": _int_attr("assignment_cooldown_budget_slack_steps", 5),
            "budget_min_streak": _int_attr("assignment_cooldown_budget_min_streak", 10),
            "budget_require_no_global_gain": _bool_attr("assignment_cooldown_budget_require_no_global_gain", True),
            "budget_require_uncovered": _bool_attr("assignment_cooldown_budget_require_uncovered", True),
            "budget_require_available": _bool_attr("assignment_cooldown_budget_require_available", True),
            "budget_require_feasible": _bool_attr("assignment_cooldown_budget_require_feasible", True),
        }

    def _build_assignment_redirect_guardrail_config(self) -> dict[str, bool | float | int | str | None]:
        cfg = getattr(self._unwrapped, "cfg", None)

        def _bool_attr(name: str, default: bool) -> bool:
            return bool(getattr(cfg, name, default))

        def _int_attr(name: str, default: int) -> int:
            return max(0, int(getattr(cfg, name, default)))

        def _optional_float_attr(name: str) -> float | None:
            value = getattr(cfg, name, None)
            if value is None:
                return None
            numeric = float(value)
            if not math.isfinite(numeric) or numeric <= 0.0:
                raise ValueError(f"{name} must be finite and positive when provided, got {value!r}")
            return numeric

        context = str(getattr(cfg, "assignment_redirect_guardrail_apply_context", "recent_budget_trigger")).strip().lower()
        if context != "recent_budget_trigger":
            raise ValueError(
                "assignment_redirect_guardrail_apply_context currently supports only 'recent_budget_trigger', "
                f"got {context!r}"
            )
        window_steps = _int_attr("assignment_redirect_guardrail_window_steps", 1)
        enabled = _bool_attr("assignment_redirect_guardrail_enabled", False)
        if enabled and window_steps <= 0:
            raise ValueError("assignment_redirect_guardrail_window_steps must be positive when the guardrail is enabled")

        return {
            "enabled": enabled,
            "apply_context": context,
            "window_steps": window_steps,
            "claimed_target_enabled": _bool_attr("assignment_redirect_guardrail_claimed_target_enabled", True),
            "spacing_enabled": _bool_attr("assignment_redirect_guardrail_spacing_enabled", True),
            "spacing_threshold": _optional_float_attr("assignment_redirect_guardrail_spacing_threshold"),
            "fail_open_spacing": _bool_attr("assignment_redirect_guardrail_fail_open_spacing", True),
            "fail_open_claimed": _bool_attr("assignment_redirect_guardrail_fail_open_claimed", True),
            "log_diagnostics": _bool_attr("assignment_redirect_guardrail_log_diagnostics", True),
        }

    def _build_assignment_failed_pair_memory_config(self) -> dict[str, bool | int | str]:
        cfg = getattr(self._unwrapped, "cfg", None)

        def _bool_attr(name: str, default: bool) -> bool:
            return bool(getattr(cfg, name, default))

        def _int_attr(name: str, default: int) -> int:
            return max(0, int(getattr(cfg, name, default)))

        source = str(getattr(cfg, "assignment_failed_pair_memory_source", "budget_trigger")).strip().lower()
        if source != "budget_trigger":
            raise ValueError(
                "assignment_failed_pair_memory_source currently supports only 'budget_trigger', "
                f"got {source!r}"
            )
        duration_steps = _int_attr("assignment_failed_pair_memory_duration_steps", 5)
        enabled = _bool_attr("assignment_failed_pair_memory_enabled", False)
        if enabled and duration_steps <= 0:
            raise ValueError("assignment_failed_pair_memory_duration_steps must be positive when the guardrail is enabled")

        return {
            "enabled": enabled,
            "duration_steps": duration_steps,
            "apply_to_action_mask": _bool_attr("assignment_failed_pair_memory_apply_to_action_mask", True),
            "source": source,
            "fail_open": _bool_attr("assignment_failed_pair_memory_fail_open", True),
            "clear_on_coverage": _bool_attr("assignment_failed_pair_memory_clear_on_coverage", True),
            "log_diagnostics": _bool_attr("assignment_failed_pair_memory_log_diagnostics", True),
        }

    def _build_assignment_lifecycle_resolver_config(self) -> dict[str, bool | str | None]:
        cfg = getattr(self._unwrapped, "cfg", None)

        def _bool_attr(name: str, default: bool) -> bool:
            return bool(getattr(cfg, name, default))

        output_dir = getattr(cfg, "assignment_lifecycle_resolver_output_dir", None)
        if output_dir is not None:
            output_dir = str(output_dir)
        return {
            "enabled": _bool_attr("assignment_lifecycle_resolver_enabled", False),
            "strict_proposals": _bool_attr("assignment_lifecycle_resolver_strict_proposals", True),
            "log_diagnostics": _bool_attr("assignment_lifecycle_resolver_log_diagnostics", False),
            "output_dir": output_dir,
        }

    def _infer_max_base_xy_step_by_agent(self) -> torch.Tensor:
        cfg = getattr(self._unwrapped, "cfg", None)
        value = getattr(cfg, "max_base_xy_step", None)
        if value is None and self._num_agents == 3:
            value = (0.08, 0.10, 0.06)
        if value is None:
            value = (0.08,) * self._num_agents
        if isinstance(value, (int, float)):
            values = [float(value)] * self._num_agents
        else:
            values = [float(item) for item in value]
            if len(values) == 1:
                values = values * self._num_agents
        if len(values) != self._num_agents:
            raise ValueError(
                "max_base_xy_step must be scalar or have one value per assignment agent, "
                f"got {len(values)} values for {self._num_agents} agents"
            )
        tensor = torch.as_tensor(values, dtype=torch.float32, device=self._device)
        return torch.clamp(tensor, min=1.0e-6)

    def _infer_raw_observation_dims(self) -> dict[str, int]:
        spaces = getattr(self._unwrapped, "observation_spaces", {})
        dims = {}
        for agent in self._agents:
            space = spaces.get(agent) if isinstance(spaces, Mapping) else None
            if hasattr(space, "shape"):
                dims[agent] = int(np.prod(space.shape))
            elif space is not None:
                dims[agent] = int(space)
            else:
                dims[agent] = 0
        return dims

    def _make_observation_space(self) -> dict[int, gymnasium.Space]:
        return {
            self._agent_map[agent]: gymnasium.spaces.Box(
                -np.inf,
                np.inf,
                shape=(self._raw_observation_dims[agent] + self._assignment_extension_dim,),
                dtype=np.float32,
            )
            for agent in self._agents
        }

    def _make_share_observation_space(self) -> dict[int, gymnasium.Space]:
        shape = sum(self._raw_observation_dims[agent] + self._assignment_extension_dim for agent in self._agents)
        state_space = gymnasium.spaces.Box(-np.inf, np.inf, shape=(shape,), dtype=np.float32)
        return {agent_id: state_space for agent_id in range(self._num_agents)}

    def _build_shared_obs(self, obs: dict[str, torch.Tensor]) -> torch.Tensor:
        observations = []
        for agent in self._agents:
            observation = obs[agent]
            if observation.ndim > 2:
                observation = observation.reshape(observation.shape[0], -1)
            observations.append(observation)
        shared = torch.cat(observations, dim=-1)
        return torch.stack([shared for _ in range(self._num_agents)], dim=1)

    def _build_available_actions(self, problem: dict | None = None) -> torch.Tensor:
        if problem is None:
            problem = self._unwrapped.get_assignment_problem()
        cooldown_mask_enabled = self._assignment_cooldown_mask_enabled()
        redirect_guardrail_enabled = self._assignment_redirect_guardrail_enabled()
        failed_pair_memory_mask_enabled = self._assignment_failed_pair_memory_mask_enabled()
        if not cooldown_mask_enabled and not redirect_guardrail_enabled and not failed_pair_memory_mask_enabled:
            self._reset_assignment_redirect_guardrail_mask_diagnostics()
            self._reset_assignment_failed_pair_memory_mask_diagnostics()
            available_actions = make_assignment_action_mask(problem, include_noop=self.include_noop)
        else:
            available_mask = problem["available_mask"]
            if not isinstance(available_mask, torch.Tensor):
                raise TypeError(
                    "problem['available_mask'] must be a torch.Tensor, "
                    f"got {type(available_mask).__name__}"
                )
            if tuple(available_mask.shape) != (self._num_envs, self._num_agents, self._num_viewpoints):
                raise RuntimeError(
                    "problem['available_mask'] must have shape "
                    f"{(self._num_envs, self._num_agents, self._num_viewpoints)}, "
                    f"got {tuple(available_mask.shape)}"
                )
            filtered_mask = available_mask.to(device=self._device, dtype=torch.bool).clone()
            if cooldown_mask_enabled:
                filtered_mask = self._apply_assignment_cooldown_to_available_mask(filtered_mask)
            if redirect_guardrail_enabled:
                filtered_mask = self._apply_assignment_redirect_guardrail_to_available_mask(
                    filtered_mask,
                    problem=problem,
                )
            else:
                self._reset_assignment_redirect_guardrail_mask_diagnostics()
            if failed_pair_memory_mask_enabled:
                filtered_mask = self._apply_assignment_failed_pair_memory_to_available_mask(filtered_mask)
            else:
                self._reset_assignment_failed_pair_memory_mask_diagnostics()
            available_actions = filtered_mask.to(dtype=torch.float32)
            if self.include_noop:
                noop_mask = torch.ones(
                    self._num_envs,
                    self._num_agents,
                    1,
                    dtype=torch.float32,
                    device=available_actions.device,
                )
                available_actions = torch.cat((available_actions, noop_mask), dim=-1)
        expected_shape = (self._num_envs, self._num_agents, self._num_viewpoints + int(self.include_noop))
        if tuple(available_actions.shape) != expected_shape:
            raise RuntimeError(f"available_actions must have shape {expected_shape}, got {tuple(available_actions.shape)}")
        if bool((available_actions.sum(dim=-1) <= 0.0).any()):
            raise RuntimeError("available_actions contains an all-zero row")
        if self.include_noop and not bool(torch.all(available_actions[..., -1] > 0.0)):
            raise RuntimeError("assignment no-op action must remain available")
        return available_actions

    def _assignment_cooldown_enabled(self) -> bool:
        return bool(self._assignment_cooldown_config["enabled"])

    def _assignment_cooldown_mask_enabled(self) -> bool:
        return self._assignment_cooldown_enabled() and bool(self._assignment_cooldown_config["apply_to_action_mask"])

    def _apply_assignment_cooldown_to_available_mask(self, available_mask: torch.Tensor) -> torch.Tensor:
        cooldown_mask = self._per_robot_target_cooldown_remaining > 0
        return available_mask & (~cooldown_mask)

    def _assignment_redirect_guardrail_enabled(self) -> bool:
        return bool(self._assignment_redirect_guardrail_config["enabled"])

    def _assignment_failed_pair_memory_enabled(self) -> bool:
        return bool(self._assignment_failed_pair_memory_config["enabled"])

    def _assignment_failed_pair_memory_mask_enabled(self) -> bool:
        return self._assignment_failed_pair_memory_enabled() and bool(
            self._assignment_failed_pair_memory_config["apply_to_action_mask"]
        )

    def _empty_failed_pair_memory_trigger_lists(self) -> tuple[list[list[int]], list[list[int]], list[list[str]]]:
        return (
            [[] for _ in range(self._num_envs)],
            [[] for _ in range(self._num_envs)],
            [[] for _ in range(self._num_envs)],
        )

    def _reset_assignment_failed_pair_memory_mask_diagnostics(self, env_ids: torch.Tensor | None = None) -> None:
        if env_ids is None:
            env_ids = torch.arange(self._num_envs, device=self._device, dtype=torch.long)
        else:
            env_ids = env_ids.to(device=self._device, dtype=torch.long)
        if not hasattr(self, "_last_failed_pair_memory_suppressed_count"):
            self._last_failed_pair_memory_suppressed_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_failed_pair_memory_fail_open_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_failed_pair_memory_only_noop_remaining = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
        self._last_failed_pair_memory_suppressed_count[env_ids] = 0
        self._last_failed_pair_memory_fail_open_count[env_ids] = 0
        self._last_failed_pair_memory_only_noop_remaining[env_ids] = False

    def _reset_assignment_failed_pair_memory_step_diagnostics(self, env_ids: torch.Tensor | None = None) -> None:
        if env_ids is None:
            env_ids = torch.arange(self._num_envs, device=self._device, dtype=torch.long)
        else:
            env_ids = env_ids.to(device=self._device, dtype=torch.long)
        if not hasattr(self, "_last_failed_pair_memory_selected_pair_active"):
            self._last_failed_pair_memory_selected_pair_active = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._last_failed_pair_memory_selected_pair_ttl_remaining = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            (
                self._last_failed_pair_memory_trigger_robot_ids,
                self._last_failed_pair_memory_trigger_target_ids,
                self._last_failed_pair_memory_trigger_reasons,
            ) = self._empty_failed_pair_memory_trigger_lists()
        self._last_failed_pair_memory_selected_pair_active[env_ids] = False
        self._last_failed_pair_memory_selected_pair_ttl_remaining[env_ids] = 0
        for env_id in env_ids.detach().cpu().tolist():
            self._last_failed_pair_memory_trigger_robot_ids[env_id] = []
            self._last_failed_pair_memory_trigger_target_ids[env_id] = []
            self._last_failed_pair_memory_trigger_reasons[env_id] = []

    def _apply_assignment_failed_pair_memory_to_available_mask(self, available_mask: torch.Tensor) -> torch.Tensor:
        result = available_mask.to(device=self._device, dtype=torch.bool).clone()
        self._reset_assignment_failed_pair_memory_mask_diagnostics()
        if not self._assignment_failed_pair_memory_mask_enabled() or self._num_viewpoints <= 0:
            return result

        active = self._assignment_failed_pair_memory_remaining > 0
        if not bool(active.any()):
            return result

        fail_open = bool(self._assignment_failed_pair_memory_config["fail_open"])
        for env_id in range(self._num_envs):
            for robot_id in range(self._num_agents):
                row = result[env_id, robot_id]
                memory_mask = active[env_id, robot_id] & row
                if not bool(memory_mask.any()):
                    self._last_failed_pair_memory_only_noop_remaining[env_id, robot_id] = not bool(row.any())
                    continue

                tentative = row & (~memory_mask)
                suppressed_count = int(memory_mask.to(dtype=torch.long).sum().item())
                if bool(row.any()) and not bool(tentative.any()):
                    self._last_failed_pair_memory_fail_open_count[env_id, robot_id] += 1
                    if fail_open:
                        self._last_failed_pair_memory_only_noop_remaining[env_id, robot_id] = False
                        continue

                result[env_id, robot_id] = tentative
                self._last_failed_pair_memory_suppressed_count[env_id, robot_id] += suppressed_count
                self._last_failed_pair_memory_only_noop_remaining[env_id, robot_id] = not bool(tentative.any())

        return result

    def _assignment_redirect_guardrail_spacing_threshold(self, problem: dict) -> float:
        configured = self._assignment_redirect_guardrail_config.get("spacing_threshold")
        if configured is not None:
            return float(configured)

        cfg = getattr(self._unwrapped, "cfg", None)

        def _scalar(value: Any, default: float) -> float:
            if value is None:
                return default
            if isinstance(value, torch.Tensor):
                if value.numel() == 0:
                    return default
                value = value.detach().flatten()[0].cpu().item()
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return default
            return numeric if math.isfinite(numeric) else default

        radius = _scalar(
            problem.get("inter_robot_target_conflict_radius", getattr(cfg, "inter_robot_target_conflict_radius", None)),
            0.35,
        )
        margin = _scalar(
            problem.get(
                "inter_robot_target_conflict_safety_margin",
                getattr(cfg, "inter_robot_target_conflict_safety_margin", None),
            ),
            0.15,
        )
        return max(1.0e-6, (2.0 * radius) + margin)

    def _empty_redirect_guardrail_robot_id_lists(self) -> list[list[list[int]]]:
        return [[[] for _ in range(self._num_agents)] for _ in range(self._num_envs)]

    def _reset_assignment_redirect_guardrail_mask_diagnostics(self, env_ids: torch.Tensor | None = None) -> None:
        if env_ids is None:
            env_ids = torch.arange(self._num_envs, device=self._device, dtype=torch.long)
        else:
            env_ids = env_ids.to(device=self._device, dtype=torch.long)
        if not hasattr(self, "_last_redirect_guardrail_active_for_robot"):
            self._last_redirect_guardrail_active_for_robot = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._last_redirect_guardrail_claimed_suppressed_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_redirect_guardrail_spacing_suppressed_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_redirect_guardrail_overmask_non_noop_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_redirect_guardrail_only_noop_remaining = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._last_redirect_guardrail_fail_open_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_redirect_guardrail_threshold = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._last_redirect_guardrail_fail_open_reason = [
                ["" for _ in range(self._num_agents)] for _ in range(self._num_envs)
            ]
            self._last_redirect_guardrail_claimed_target_robot_ids = self._empty_redirect_guardrail_robot_id_lists()
            self._last_redirect_guardrail_nearby_target_robot_ids = self._empty_redirect_guardrail_robot_id_lists()
            self._capture_pre_step_assignment_redirect_guardrail_diagnostics()

        self._last_redirect_guardrail_active_for_robot[env_ids] = False
        self._last_redirect_guardrail_claimed_suppressed_count[env_ids] = 0
        self._last_redirect_guardrail_spacing_suppressed_count[env_ids] = 0
        self._last_redirect_guardrail_overmask_non_noop_count[env_ids] = 0
        self._last_redirect_guardrail_only_noop_remaining[env_ids] = False
        self._last_redirect_guardrail_fail_open_count[env_ids] = 0
        self._last_redirect_guardrail_threshold[env_ids] = 0.0
        for env_id in env_ids.detach().cpu().tolist():
            for robot_id in range(self._num_agents):
                self._last_redirect_guardrail_fail_open_reason[env_id][robot_id] = ""
                self._last_redirect_guardrail_claimed_target_robot_ids[env_id][robot_id] = []
                self._last_redirect_guardrail_nearby_target_robot_ids[env_id][robot_id] = []

    def _capture_pre_step_assignment_redirect_guardrail_diagnostics(self) -> None:
        if not hasattr(self, "_last_redirect_guardrail_active_for_robot"):
            return
        self._last_pre_step_redirect_guardrail_active_for_robot = (
            self._last_redirect_guardrail_active_for_robot.clone()
        )
        self._last_pre_step_redirect_guardrail_claimed_suppressed_count = (
            self._last_redirect_guardrail_claimed_suppressed_count.clone()
        )
        self._last_pre_step_redirect_guardrail_spacing_suppressed_count = (
            self._last_redirect_guardrail_spacing_suppressed_count.clone()
        )
        self._last_pre_step_redirect_guardrail_overmask_non_noop_count = (
            self._last_redirect_guardrail_overmask_non_noop_count.clone()
        )
        self._last_pre_step_redirect_guardrail_only_noop_remaining = (
            self._last_redirect_guardrail_only_noop_remaining.clone()
        )
        self._last_pre_step_redirect_guardrail_fail_open_count = (
            self._last_redirect_guardrail_fail_open_count.clone()
        )
        self._last_pre_step_redirect_guardrail_threshold = self._last_redirect_guardrail_threshold.clone()
        self._last_pre_step_redirect_guardrail_fail_open_reason = [
            list(row) for row in self._last_redirect_guardrail_fail_open_reason
        ]
        self._last_pre_step_redirect_guardrail_claimed_target_robot_ids = [
            [list(ids) for ids in row] for row in self._last_redirect_guardrail_claimed_target_robot_ids
        ]
        self._last_pre_step_redirect_guardrail_nearby_target_robot_ids = [
            [list(ids) for ids in row] for row in self._last_redirect_guardrail_nearby_target_robot_ids
        ]

    def _append_redirect_guardrail_fail_reason(self, current: str, reason: str) -> str:
        if not current:
            return reason
        if reason in current.split(";"):
            return current
        return f"{current};{reason}"

    def _apply_assignment_redirect_guardrail_to_available_mask(
        self,
        available_mask: torch.Tensor,
        *,
        problem: dict,
    ) -> torch.Tensor:
        result = available_mask.to(device=self._device, dtype=torch.bool).clone()
        self._reset_assignment_redirect_guardrail_mask_diagnostics()
        if not self._assignment_redirect_guardrail_enabled() or self._num_viewpoints <= 0:
            return result

        active = self._assignment_redirect_guardrail_remaining > 0
        if not bool(active.any()):
            return result

        viewpoint_pos = problem.get("viewpoint_pos")
        spacing_enabled = bool(self._assignment_redirect_guardrail_config["spacing_enabled"])
        if spacing_enabled:
            if not isinstance(viewpoint_pos, torch.Tensor):
                spacing_enabled = False
            else:
                viewpoint_pos = viewpoint_pos.to(device=self._device, dtype=torch.float32)
                if tuple(viewpoint_pos.shape[:2]) != (self._num_envs, self._num_viewpoints):
                    spacing_enabled = False
        threshold = self._assignment_redirect_guardrail_spacing_threshold(problem)
        claimed_enabled = bool(self._assignment_redirect_guardrail_config["claimed_target_enabled"])
        fail_open_claimed = bool(self._assignment_redirect_guardrail_config["fail_open_claimed"])
        fail_open_spacing = bool(self._assignment_redirect_guardrail_config["fail_open_spacing"])

        for env_id in range(self._num_envs):
            for robot_id in range(self._num_agents):
                if not bool(active[env_id, robot_id].item()):
                    continue

                self._last_redirect_guardrail_active_for_robot[env_id, robot_id] = True
                self._last_redirect_guardrail_threshold[env_id, robot_id] = float(threshold)
                row_before = result[env_id, robot_id].clone()
                row = row_before.clone()

                teammate_targets: dict[int, list[int]] = {}
                for other_robot_id in range(self._num_agents):
                    if other_robot_id == robot_id:
                        continue
                    target_id = int(self._previous_assignment[env_id, other_robot_id].item())
                    if 0 <= target_id < self._num_viewpoints:
                        teammate_targets.setdefault(target_id, []).append(other_robot_id)

                fail_reason = ""
                claimed_robot_ids: set[int] = set()
                if claimed_enabled and teammate_targets:
                    claimed_mask = torch.zeros(self._num_viewpoints, dtype=torch.bool, device=self._device)
                    for target_id, owner_ids in teammate_targets.items():
                        if bool(row[target_id].item()):
                            claimed_mask[target_id] = True
                            claimed_robot_ids.update(owner_ids)
                    if bool(claimed_mask.any()):
                        tentative = row & (~claimed_mask)
                        claimed_count = int(claimed_mask.to(dtype=torch.long).sum().item())
                        if bool(row.any()) and not bool(tentative.any()):
                            self._last_redirect_guardrail_overmask_non_noop_count[env_id, robot_id] += claimed_count
                            self._last_redirect_guardrail_fail_open_count[env_id, robot_id] += 1
                            fail_reason = self._append_redirect_guardrail_fail_reason(fail_reason, "claimed_overmask")
                            if not fail_open_claimed:
                                row = tentative
                                self._last_redirect_guardrail_claimed_suppressed_count[env_id, robot_id] += claimed_count
                        else:
                            row = tentative
                            self._last_redirect_guardrail_claimed_suppressed_count[env_id, robot_id] += claimed_count

                nearby_robot_ids: set[int] = set()
                if spacing_enabled and teammate_targets and bool(row.any()):
                    spacing_mask = torch.zeros(self._num_viewpoints, dtype=torch.bool, device=self._device)
                    teammate_positions: list[tuple[int, torch.Tensor]] = []
                    assert isinstance(viewpoint_pos, torch.Tensor)
                    for target_id, owner_ids in teammate_targets.items():
                        target_xy = viewpoint_pos[env_id, target_id, :2]
                        for owner_id in owner_ids:
                            teammate_positions.append((owner_id, target_xy))
                    candidate_ids = torch.nonzero(row, as_tuple=False).flatten().detach().cpu().tolist()
                    for candidate_id in candidate_ids:
                        if candidate_id in teammate_targets:
                            continue
                        candidate_xy = viewpoint_pos[env_id, candidate_id, :2]
                        close_owner_ids = [
                            owner_id
                            for owner_id, owner_xy in teammate_positions
                            if float(torch.linalg.norm(candidate_xy - owner_xy).item()) < threshold
                        ]
                        if close_owner_ids:
                            spacing_mask[candidate_id] = True
                            nearby_robot_ids.update(close_owner_ids)
                    if bool(spacing_mask.any()):
                        tentative = row & (~spacing_mask)
                        spacing_count = int(spacing_mask.to(dtype=torch.long).sum().item())
                        if bool(row.any()) and not bool(tentative.any()):
                            self._last_redirect_guardrail_overmask_non_noop_count[env_id, robot_id] += spacing_count
                            self._last_redirect_guardrail_fail_open_count[env_id, robot_id] += 1
                            fail_reason = self._append_redirect_guardrail_fail_reason(fail_reason, "spacing_overmask")
                            if not fail_open_spacing:
                                row = tentative
                                self._last_redirect_guardrail_spacing_suppressed_count[env_id, robot_id] += spacing_count
                        else:
                            row = tentative
                            self._last_redirect_guardrail_spacing_suppressed_count[env_id, robot_id] += spacing_count

                result[env_id, robot_id] = row
                self._last_redirect_guardrail_only_noop_remaining[env_id, robot_id] = not bool(row.any())
                self._last_redirect_guardrail_fail_open_reason[env_id][robot_id] = fail_reason
                self._last_redirect_guardrail_claimed_target_robot_ids[env_id][robot_id] = sorted(claimed_robot_ids)
                self._last_redirect_guardrail_nearby_target_robot_ids[env_id][robot_id] = sorted(nearby_robot_ids)

        return result

    def _advance_assignment_redirect_guardrail_window_after_action(self) -> None:
        if not hasattr(self, "_assignment_redirect_guardrail_remaining"):
            return
        active = self._assignment_redirect_guardrail_remaining > 0
        if not bool(active.any()):
            return
        self._assignment_redirect_guardrail_remaining = torch.clamp(
            self._assignment_redirect_guardrail_remaining - active.to(dtype=torch.long),
            min=0,
        )
        self._assignment_redirect_guardrail_triggered_target = torch.where(
            self._assignment_redirect_guardrail_remaining > 0,
            self._assignment_redirect_guardrail_triggered_target,
            torch.full_like(self._assignment_redirect_guardrail_triggered_target, -1),
        )

    def _activate_assignment_redirect_guardrail_for_budget_triggers(
        self,
        *,
        budget_trigger: torch.Tensor,
        assignment: torch.Tensor,
    ) -> None:
        if not self._assignment_redirect_guardrail_enabled():
            return
        if self._assignment_redirect_guardrail_config["apply_context"] != "recent_budget_trigger":
            return
        window_steps = int(self._assignment_redirect_guardrail_config["window_steps"])
        if window_steps <= 0:
            return
        env_indices, agent_indices = torch.nonzero(budget_trigger, as_tuple=True)
        if env_indices.numel() == 0:
            return
        triggered_targets = assignment[env_indices, agent_indices]
        valid = (triggered_targets >= 0) & (triggered_targets < self._num_viewpoints)
        if not bool(valid.any()):
            return
        env_indices = env_indices[valid]
        agent_indices = agent_indices[valid]
        triggered_targets = triggered_targets[valid]
        self._assignment_redirect_guardrail_remaining[env_indices, agent_indices] = window_steps
        self._assignment_redirect_guardrail_triggered_target[env_indices, agent_indices] = triggered_targets

    def _capture_assignment_failed_pair_memory_selected_pairs(
        self,
        *,
        assignment: torch.Tensor,
        valid_viewpoint: torch.Tensor,
        safe_ids: torch.Tensor,
    ) -> None:
        self._last_failed_pair_memory_selected_pair_active.zero_()
        self._last_failed_pair_memory_selected_pair_ttl_remaining.zero_()
        if not self._assignment_failed_pair_memory_enabled() or self._num_viewpoints <= 0:
            return
        selected_ttl = torch.gather(
            self._assignment_failed_pair_memory_remaining,
            dim=2,
            index=safe_ids,
        ).squeeze(-1)
        selected_active = (selected_ttl > 0) & valid_viewpoint
        self._last_failed_pair_memory_selected_pair_active = selected_active
        self._last_failed_pair_memory_selected_pair_ttl_remaining = torch.where(
            valid_viewpoint,
            selected_ttl,
            torch.zeros_like(selected_ttl),
        )

    def _advance_assignment_failed_pair_memory_after_action(self, covered: torch.Tensor) -> None:
        if not hasattr(self, "_assignment_failed_pair_memory_remaining"):
            return
        if self._assignment_failed_pair_memory_enabled():
            active = self._assignment_failed_pair_memory_remaining > 0
            if bool(active.any()):
                self._assignment_failed_pair_memory_remaining = torch.clamp(
                    self._assignment_failed_pair_memory_remaining - active.to(dtype=torch.long),
                    min=0,
                )
        self._assignment_failed_pair_memory_trigger_step = torch.where(
            self._assignment_failed_pair_memory_remaining > 0,
            self._assignment_failed_pair_memory_trigger_step,
            torch.full_like(self._assignment_failed_pair_memory_trigger_step, -1),
        )
        if bool(self._assignment_failed_pair_memory_config["clear_on_coverage"]):
            self._clear_assignment_failed_pair_memory_for_covered_targets(covered)

    def _activate_assignment_failed_pair_memory_for_budget_triggers(
        self,
        *,
        budget_trigger: torch.Tensor,
        assignment: torch.Tensor,
    ) -> None:
        if not self._assignment_failed_pair_memory_enabled():
            return
        if self._assignment_failed_pair_memory_config["source"] != "budget_trigger":
            return
        duration_steps = int(self._assignment_failed_pair_memory_config["duration_steps"])
        if duration_steps <= 0:
            return
        env_indices, agent_indices = torch.nonzero(budget_trigger, as_tuple=True)
        if env_indices.numel() == 0:
            return
        triggered_targets = assignment[env_indices, agent_indices]
        valid = (triggered_targets >= 0) & (triggered_targets < self._num_viewpoints)
        if not bool(valid.any()):
            return
        env_indices = env_indices[valid]
        agent_indices = agent_indices[valid]
        triggered_targets = triggered_targets[valid]
        self._assignment_failed_pair_memory_remaining[env_indices, agent_indices, triggered_targets] = duration_steps
        trigger_steps = self._assignment_step[env_indices]
        self._assignment_failed_pair_memory_trigger_step[env_indices, agent_indices, triggered_targets] = trigger_steps
        for env_id, agent_id, target_id in zip(
            env_indices.detach().cpu().tolist(),
            agent_indices.detach().cpu().tolist(),
            triggered_targets.detach().cpu().tolist(),
        ):
            self._last_failed_pair_memory_trigger_robot_ids[env_id].append(int(agent_id))
            self._last_failed_pair_memory_trigger_target_ids[env_id].append(int(target_id))
            self._last_failed_pair_memory_trigger_reasons[env_id].append("budget_trigger")

    def _cooldown_trigger_mode(self) -> str:
        return str(self._assignment_cooldown_config["trigger_mode"])

    def _cooldown_trigger_uses_budget(self) -> bool:
        return self._cooldown_trigger_mode() in {"budget", "budget_and_streak"}

    def _budget_expected_and_limit_steps(self, assignment: torch.Tensor, problem: dict) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        selected_cost = self._selected_path_cost(assignment, problem).to(device=self._device, dtype=torch.float32)
        per_agent_step = self._max_base_xy_step_by_agent.view(1, self._num_agents).expand(self._num_envs, -1)
        expected_steps = torch.ceil(selected_cost / per_agent_step).to(dtype=torch.long).clamp(min=1)
        budget_multiplier = float(self._assignment_cooldown_config["budget_multiplier"])
        budget_slack_steps = int(self._assignment_cooldown_config["budget_slack_steps"])
        budget_steps = torch.ceil(expected_steps.to(dtype=torch.float32) * budget_multiplier + float(budget_slack_steps))
        budget_steps = budget_steps.to(dtype=torch.long).clamp(min=1)
        return selected_cost, expected_steps, budget_steps

    def _update_budget_attempt_tracking(
        self,
        *,
        assignment: torch.Tensor,
        problem: dict,
        valid_viewpoint: torch.Tensor,
    ) -> torch.Tensor:
        selected_cost, expected_steps, budget_steps = self._budget_expected_and_limit_steps(assignment, problem)
        same_segment = valid_viewpoint & (self._budget_attempt_target == assignment)
        new_segment = valid_viewpoint & (~same_segment)
        inactive_segment = ~valid_viewpoint

        self._budget_attempt_target = torch.where(
            inactive_segment,
            torch.full_like(self._budget_attempt_target, -1),
            self._budget_attempt_target,
        )
        self._budget_attempt_steps = torch.where(
            inactive_segment,
            torch.zeros_like(self._budget_attempt_steps),
            self._budget_attempt_steps,
        )
        self._budget_attempt_initial_cost = torch.where(
            inactive_segment,
            torch.zeros_like(self._budget_attempt_initial_cost),
            self._budget_attempt_initial_cost,
        )
        self._budget_attempt_expected_steps = torch.where(
            inactive_segment,
            torch.zeros_like(self._budget_attempt_expected_steps),
            self._budget_attempt_expected_steps,
        )
        self._budget_attempt_budget_steps = torch.where(
            inactive_segment,
            torch.zeros_like(self._budget_attempt_budget_steps),
            self._budget_attempt_budget_steps,
        )

        self._budget_attempt_steps = torch.where(
            same_segment,
            self._budget_attempt_steps + 1,
            self._budget_attempt_steps,
        )
        self._budget_attempt_target = torch.where(new_segment, assignment, self._budget_attempt_target)
        self._budget_attempt_steps = torch.where(new_segment, torch.ones_like(self._budget_attempt_steps), self._budget_attempt_steps)
        self._budget_attempt_initial_cost = torch.where(new_segment, selected_cost, self._budget_attempt_initial_cost)
        self._budget_attempt_expected_steps = torch.where(new_segment, expected_steps, self._budget_attempt_expected_steps)
        self._budget_attempt_budget_steps = torch.where(new_segment, budget_steps, self._budget_attempt_budget_steps)

        safe_budget = self._budget_attempt_budget_steps.clamp(min=1).to(dtype=torch.float32)
        budget_ratio = self._budget_attempt_steps.to(dtype=torch.float32) / safe_budget
        budget_ratio = torch.where(valid_viewpoint, budget_ratio, torch.zeros_like(budget_ratio))

        self._last_budget_attempt_steps_for_selected_pair = torch.where(
            valid_viewpoint,
            self._budget_attempt_steps,
            torch.zeros_like(self._budget_attempt_steps),
        )
        self._last_budget_steps_for_selected_pair = torch.where(
            valid_viewpoint,
            self._budget_attempt_budget_steps,
            torch.zeros_like(self._budget_attempt_budget_steps),
        )
        self._last_budget_expected_steps_for_selected_pair = torch.where(
            valid_viewpoint,
            self._budget_attempt_expected_steps,
            torch.zeros_like(self._budget_attempt_expected_steps),
        )
        self._last_budget_ratio_for_selected_pair = budget_ratio
        return self._budget_attempt_steps >= self._budget_attempt_budget_steps.clamp(min=1)

    def _reset_budget_attempt_pairs(self, env_indices: torch.Tensor, agent_indices: torch.Tensor) -> None:
        if env_indices.numel() == 0:
            return
        self._budget_attempt_target[env_indices, agent_indices] = -1
        self._budget_attempt_steps[env_indices, agent_indices] = 0
        self._budget_attempt_initial_cost[env_indices, agent_indices] = 0.0
        self._budget_attempt_expected_steps[env_indices, agent_indices] = 0
        self._budget_attempt_budget_steps[env_indices, agent_indices] = 0

    def _clear_budget_attempts_for_covered_targets(self, covered: torch.Tensor) -> None:
        if self._num_viewpoints <= 0:
            return
        target = self._budget_attempt_target
        active = target >= 0
        safe_target = target.clamp(min=0, max=self._num_viewpoints - 1).unsqueeze(-1)
        selected_covered = torch.gather(
            covered.to(device=self._device, dtype=torch.bool).unsqueeze(1).expand(
                self._num_envs,
                self._num_agents,
                self._num_viewpoints,
            ),
            dim=2,
            index=safe_target,
        ).squeeze(-1)
        clear = active & selected_covered
        env_indices, agent_indices = torch.nonzero(clear, as_tuple=True)
        self._reset_budget_attempt_pairs(env_indices, agent_indices)

    def _env_spacing(self) -> float:
        cfg = getattr(self._unwrapped, "cfg", None)
        scene_cfg = getattr(cfg, "scene", None)
        spacing = float(getattr(scene_cfg, "env_spacing", 1.0))
        return spacing if abs(spacing) > 1.0e-6 else 1.0

    def _episode_progress_norm(self) -> torch.Tensor:
        buffer = getattr(self._unwrapped, "episode_length_buf", None)
        if isinstance(buffer, torch.Tensor):
            progress = buffer.to(device=self._device, dtype=torch.float32) / float(self._normalization_horizon)
        else:
            progress = self._assignment_step.to(dtype=torch.float32) / float(self._normalization_horizon)
        return torch.clamp(progress, 0.0, 1.0)

    def _reset_assignment_diagnostics(self, env_ids: torch.Tensor | None = None, problem: dict | None = None) -> None:
        if env_ids is None:
            env_ids = torch.arange(self._num_envs, device=self._device, dtype=torch.long)
        else:
            env_ids = env_ids.to(device=self._device, dtype=torch.long)
        if not hasattr(self, "_assignment_step"):
            self._assignment_step = torch.zeros(self._num_envs, dtype=torch.long, device=self._device)
            self._per_viewpoint_attempted_count = torch.zeros(
                self._num_envs, self._num_viewpoints, dtype=torch.float32, device=self._device
            )
            self._last_viewpoint_attempt_step = torch.full(
                (self._num_envs, self._num_viewpoints), -1, dtype=torch.long, device=self._device
            )
            self._previous_assignment = torch.full(
                (self._num_envs, self._num_agents), -1, dtype=torch.long, device=self._device
            )
            self._same_target_streak = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._steps_since_global_coverage_gain = torch.zeros(
                self._num_envs, dtype=torch.float32, device=self._device
            )
            self._per_robot_completed_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._per_robot_repeated_assignment_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._per_robot_selected_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._last_covered_mask = torch.zeros(
                self._num_envs, self._num_viewpoints, dtype=torch.bool, device=self._device
            )
            self._per_robot_target_failed_attempt_count = torch.zeros(
                self._num_envs,
                self._num_agents,
                self._num_viewpoints,
                dtype=torch.long,
                device=self._device,
            )
            self._per_robot_target_cooldown_remaining = torch.zeros(
                self._num_envs,
                self._num_agents,
                self._num_viewpoints,
                dtype=torch.long,
                device=self._device,
            )
            self._assignment_cooldown_trigger_count = torch.zeros(
                self._num_envs, dtype=torch.float32, device=self._device
            )
            self._assignment_cooldown_suppressed_count = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._assignment_cooldown_selected_target_was_in_cooldown_count = torch.zeros(
                self._num_envs, dtype=torch.float32, device=self._device
            )
            self._assignment_cooldown_last_triggered_viewpoint = torch.full(
                (self._num_envs, self._num_agents), -1, dtype=torch.long, device=self._device
            )
            self._last_cooldown_active_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._last_cooldown_remaining_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_cooldown_triggered_after_step = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._last_failed_attempt_count_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_cooldown_suppressed_available_count_for_robot = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._budget_attempt_target = torch.full(
                (self._num_envs, self._num_agents), -1, dtype=torch.long, device=self._device
            )
            self._budget_attempt_steps = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._budget_attempt_initial_cost = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._budget_attempt_expected_steps = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._budget_attempt_budget_steps = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._assignment_cooldown_budget_trigger_count = torch.zeros(
                self._num_envs, dtype=torch.float32, device=self._device
            )
            self._assignment_cooldown_budget_over_budget_selected_count = torch.zeros(
                self._num_envs, dtype=torch.float32, device=self._device
            )
            self._last_budget_attempt_steps_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_budget_steps_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_budget_expected_steps_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._last_budget_ratio_for_selected_pair = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            self._last_budget_triggered_by_budget = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.bool, device=self._device
            )
            self._assignment_redirect_guardrail_remaining = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.long, device=self._device
            )
            self._assignment_redirect_guardrail_triggered_target = torch.full(
                (self._num_envs, self._num_agents), -1, dtype=torch.long, device=self._device
            )
            self._reset_assignment_redirect_guardrail_mask_diagnostics()
            self._assignment_failed_pair_memory_remaining = torch.zeros(
                self._num_envs,
                self._num_agents,
                self._num_viewpoints,
                dtype=torch.long,
                device=self._device,
            )
            self._assignment_failed_pair_memory_trigger_step = torch.full(
                (self._num_envs, self._num_agents, self._num_viewpoints),
                -1,
                dtype=torch.long,
                device=self._device,
            )
            self._reset_assignment_failed_pair_memory_mask_diagnostics()
            self._reset_assignment_failed_pair_memory_step_diagnostics()

        self._assignment_step[env_ids] = 0
        self._per_viewpoint_attempted_count[env_ids] = 0.0
        self._last_viewpoint_attempt_step[env_ids] = -1
        self._previous_assignment[env_ids] = -1
        self._same_target_streak[env_ids] = 0.0
        self._steps_since_global_coverage_gain[env_ids] = 0.0
        self._per_robot_completed_count[env_ids] = 0.0
        self._per_robot_repeated_assignment_count[env_ids] = 0.0
        self._per_robot_selected_count[env_ids] = 0.0
        self._per_robot_target_failed_attempt_count[env_ids] = 0
        self._per_robot_target_cooldown_remaining[env_ids] = 0
        self._assignment_cooldown_trigger_count[env_ids] = 0.0
        self._assignment_cooldown_suppressed_count[env_ids] = 0.0
        self._assignment_cooldown_selected_target_was_in_cooldown_count[env_ids] = 0.0
        self._assignment_cooldown_last_triggered_viewpoint[env_ids] = -1
        self._budget_attempt_target[env_ids] = -1
        self._budget_attempt_steps[env_ids] = 0
        self._budget_attempt_initial_cost[env_ids] = 0.0
        self._budget_attempt_expected_steps[env_ids] = 0
        self._budget_attempt_budget_steps[env_ids] = 0
        self._assignment_cooldown_budget_trigger_count[env_ids] = 0.0
        self._assignment_cooldown_budget_over_budget_selected_count[env_ids] = 0.0
        self._last_budget_attempt_steps_for_selected_pair[env_ids] = 0
        self._last_budget_steps_for_selected_pair[env_ids] = 0
        self._last_budget_expected_steps_for_selected_pair[env_ids] = 0
        self._last_budget_ratio_for_selected_pair[env_ids] = 0.0
        self._last_budget_triggered_by_budget[env_ids] = False
        self._assignment_redirect_guardrail_remaining[env_ids] = 0
        self._assignment_redirect_guardrail_triggered_target[env_ids] = -1
        self._reset_assignment_redirect_guardrail_mask_diagnostics(env_ids=env_ids)
        self._capture_pre_step_assignment_redirect_guardrail_diagnostics()
        self._assignment_failed_pair_memory_remaining[env_ids] = 0
        self._assignment_failed_pair_memory_trigger_step[env_ids] = -1
        self._reset_assignment_failed_pair_memory_mask_diagnostics(env_ids=env_ids)
        self._reset_assignment_failed_pair_memory_step_diagnostics(env_ids=env_ids)
        if problem is not None and "viewpoints_covered" in problem:
            self._last_covered_mask[env_ids] = problem["viewpoints_covered"][env_ids].to(dtype=torch.bool)
        else:
            self._last_covered_mask[env_ids] = False

    def _update_assignment_diagnostics(
        self,
        *,
        assignment: torch.Tensor,
        pre_step_problem: dict,
        post_step_problem: dict,
        selected_available_mask: torch.Tensor,
    ) -> None:
        next_step = self._assignment_step + 1
        non_noop = assignment >= 0
        repeated = non_noop & (assignment == self._previous_assignment)
        self._per_robot_selected_count += non_noop.to(dtype=torch.float32)
        self._per_robot_repeated_assignment_count += repeated.to(dtype=torch.float32)
        self._same_target_streak = torch.where(
            non_noop,
            torch.where(repeated, self._same_target_streak + 1.0, torch.ones_like(self._same_target_streak)),
            torch.zeros_like(self._same_target_streak),
        )

        for agent_index in range(self._num_agents):
            selected = assignment[:, agent_index]
            valid_envs = torch.nonzero(selected >= 0, as_tuple=False).flatten()
            if valid_envs.numel() == 0:
                continue
            selected_ids = selected[valid_envs]
            self._per_viewpoint_attempted_count[valid_envs, selected_ids] += 1.0
            self._last_viewpoint_attempt_step[valid_envs, selected_ids] = next_step[valid_envs]

        covered_before = pre_step_problem.get("viewpoints_covered", self._last_covered_mask).to(dtype=torch.bool)
        covered_after = post_step_problem["viewpoints_covered"].to(dtype=torch.bool)
        newly_covered = covered_after & (~covered_before)
        has_global_gain = newly_covered.any(dim=-1)
        self._steps_since_global_coverage_gain = torch.where(
            has_global_gain,
            torch.zeros_like(self._steps_since_global_coverage_gain),
            self._steps_since_global_coverage_gain + 1.0,
        )

        selected_matrix = torch.zeros(
            self._num_envs,
            self._num_agents,
            self._num_viewpoints,
            dtype=torch.bool,
            device=self._device,
        )
        env_indices, agent_indices = torch.nonzero(non_noop, as_tuple=True)
        if env_indices.numel() > 0:
            selected_matrix[env_indices, agent_indices, assignment[env_indices, agent_indices]] = True
        newly_selected = selected_matrix & newly_covered.unsqueeze(1)
        duplicate_completion_count = newly_selected.to(dtype=torch.float32).sum(dim=1, keepdim=True).clamp(min=1.0)
        self._per_robot_completed_count += (newly_selected.to(dtype=torch.float32) / duplicate_completion_count).sum(
            dim=-1
        )

        self._previous_assignment = assignment.clone()
        self._assignment_step = next_step
        self._last_covered_mask = covered_after.clone()
        self._update_assignment_cooldown(
            assignment=assignment,
            pre_step_problem=pre_step_problem,
            selected_available_mask=selected_available_mask,
            covered_before=covered_before,
            covered_after=covered_after,
            newly_covered=newly_covered,
        )

    def _update_assignment_cooldown(
        self,
        *,
        assignment: torch.Tensor,
        pre_step_problem: dict,
        selected_available_mask: torch.Tensor,
        covered_before: torch.Tensor,
        covered_after: torch.Tensor,
        newly_covered: torch.Tensor,
    ) -> None:
        self._last_cooldown_triggered_after_step.zero_()
        self._last_failed_attempt_count_for_selected_pair.zero_()
        self._last_budget_attempt_steps_for_selected_pair.zero_()
        self._last_budget_steps_for_selected_pair.zero_()
        self._last_budget_expected_steps_for_selected_pair.zero_()
        self._last_budget_ratio_for_selected_pair.zero_()
        self._last_budget_triggered_by_budget.zero_()
        self._reset_assignment_failed_pair_memory_step_diagnostics()
        self._advance_assignment_redirect_guardrail_window_after_action()

        cooldown_enabled = self._assignment_cooldown_enabled()
        base_available = pre_step_problem["available_mask"].to(device=self._device, dtype=torch.bool)
        active_before = (
            self._per_robot_target_cooldown_remaining > 0
            if cooldown_enabled
            else torch.zeros_like(self._per_robot_target_cooldown_remaining, dtype=torch.bool)
        )
        suppressed_per_robot = (base_available & active_before).sum(dim=-1)
        self._assignment_cooldown_suppressed_count = suppressed_per_robot.to(dtype=torch.float32)
        self._last_cooldown_suppressed_available_count_for_robot = suppressed_per_robot.to(dtype=torch.long)

        num_viewpoints = self._num_viewpoints
        valid_viewpoint = (assignment >= 0) & (assignment < num_viewpoints)
        safe_ids = assignment.clamp(min=0, max=max(0, num_viewpoints - 1)).unsqueeze(-1)

        selected_cooldown_remaining = torch.zeros_like(assignment, dtype=torch.long)
        selected_in_cooldown = torch.zeros_like(assignment, dtype=torch.bool)
        if num_viewpoints > 0 and cooldown_enabled:
            selected_cooldown_remaining = torch.gather(
                self._per_robot_target_cooldown_remaining,
                dim=2,
                index=safe_ids,
            ).squeeze(-1)
            selected_in_cooldown = (selected_cooldown_remaining > 0) & valid_viewpoint
        self._last_cooldown_remaining_for_selected_pair = torch.where(
            valid_viewpoint,
            selected_cooldown_remaining,
            torch.zeros_like(selected_cooldown_remaining),
        )
        self._last_cooldown_active_for_selected_pair = selected_in_cooldown
        self._assignment_cooldown_selected_target_was_in_cooldown_count += selected_in_cooldown.to(
            dtype=torch.float32
        ).sum(dim=1)
        self._capture_assignment_failed_pair_memory_selected_pairs(
            assignment=assignment,
            valid_viewpoint=valid_viewpoint,
            safe_ids=safe_ids,
        )
        self._advance_assignment_failed_pair_memory_after_action(covered_after)

        if cooldown_enabled:
            self._per_robot_target_cooldown_remaining = torch.clamp(
                self._per_robot_target_cooldown_remaining
                - (self._per_robot_target_cooldown_remaining > 0).to(dtype=torch.long),
                min=0,
            )

        if bool(self._assignment_cooldown_config["clear_on_covered"]):
            self._clear_assignment_cooldown_for_covered_targets(covered_after)

        if not cooldown_enabled:
            return

        feasible = pre_step_problem.get("feasible_mask", base_available).to(device=self._device, dtype=torch.bool)
        selected_feasible = torch.zeros_like(assignment, dtype=torch.bool)
        selected_covered_before = torch.zeros_like(assignment, dtype=torch.bool)
        selected_covered_after = torch.zeros_like(assignment, dtype=torch.bool)
        if num_viewpoints > 0:
            selected_feasible = torch.gather(feasible, dim=2, index=safe_ids).squeeze(-1) & valid_viewpoint
            selected_covered_before = torch.gather(
                covered_before.unsqueeze(1).expand(self._num_envs, self._num_agents, self._num_viewpoints),
                dim=2,
                index=safe_ids,
            ).squeeze(-1)
            selected_covered_before = selected_covered_before & valid_viewpoint
            selected_covered_after = torch.gather(
                covered_after.unsqueeze(1).expand(self._num_envs, self._num_agents, self._num_viewpoints),
                dim=2,
                index=safe_ids,
            ).squeeze(-1)
            selected_covered_after = selected_covered_after & valid_viewpoint

        over_budget = self._update_budget_attempt_tracking(
            assignment=assignment,
            problem=pre_step_problem,
            valid_viewpoint=valid_viewpoint,
        )

        failed_attempt = valid_viewpoint
        if bool(self._assignment_cooldown_config["require_available"]):
            failed_attempt = failed_attempt & selected_available_mask.to(device=self._device, dtype=torch.bool)
        if bool(self._assignment_cooldown_config["require_feasible"]):
            failed_attempt = failed_attempt & selected_feasible
        if bool(self._assignment_cooldown_config["require_uncovered"]):
            failed_attempt = failed_attempt & (~selected_covered_before)

        global_gain = newly_covered.any(dim=-1)
        if bool(self._assignment_cooldown_config["require_no_global_gain"]):
            failed_attempt = failed_attempt & (~global_gain).unsqueeze(-1)

        steps_since_threshold = int(self._assignment_cooldown_config["trigger_steps_since_global_gain"])
        if steps_since_threshold > 0:
            failed_attempt = failed_attempt & (
                self._steps_since_global_coverage_gain >= float(steps_since_threshold)
            ).unsqueeze(-1)

        env_indices, agent_indices = torch.nonzero(failed_attempt, as_tuple=True)
        if env_indices.numel() > 0:
            selected_ids = assignment[env_indices, agent_indices]
            self._per_robot_target_failed_attempt_count[env_indices, agent_indices, selected_ids] += 1

        failed_counts_for_selected = torch.zeros_like(assignment, dtype=torch.long)
        if num_viewpoints > 0:
            failed_counts_for_selected = torch.gather(
                self._per_robot_target_failed_attempt_count,
                dim=2,
                index=safe_ids,
            ).squeeze(-1)
        self._last_failed_attempt_count_for_selected_pair = torch.where(
            valid_viewpoint,
            failed_counts_for_selected,
            torch.zeros_like(failed_counts_for_selected),
        )

        trigger_attempts = int(self._assignment_cooldown_config["trigger_attempts"])
        trigger_streak = int(self._assignment_cooldown_config["trigger_same_target_streak"])
        attempt_trigger = (
            failed_counts_for_selected >= int(trigger_attempts)
            if trigger_attempts > 0
            else torch.zeros_like(failed_attempt)
        )
        streak_trigger = (
            self._same_target_streak >= float(trigger_streak)
            if trigger_streak > 0
            else torch.zeros_like(failed_attempt)
        )
        streak_mode_trigger = failed_attempt & (attempt_trigger | streak_trigger)

        budget_candidate = valid_viewpoint
        if bool(self._assignment_cooldown_config["budget_require_available"]):
            budget_candidate = budget_candidate & selected_available_mask.to(device=self._device, dtype=torch.bool)
        if bool(self._assignment_cooldown_config["budget_require_feasible"]):
            budget_candidate = budget_candidate & selected_feasible
        if bool(self._assignment_cooldown_config["budget_require_uncovered"]):
            budget_candidate = budget_candidate & (~selected_covered_after)
        if bool(self._assignment_cooldown_config["budget_require_no_global_gain"]):
            budget_candidate = budget_candidate & (~global_gain).unsqueeze(-1)
        budget_over_budget_selected = budget_candidate & over_budget
        self._assignment_cooldown_budget_over_budget_selected_count += budget_over_budget_selected.to(
            dtype=torch.float32
        ).sum(dim=1)

        budget_mode_trigger = budget_over_budget_selected
        if self._cooldown_trigger_mode() == "budget_and_streak":
            budget_min_streak = int(self._assignment_cooldown_config["budget_min_streak"])
            if budget_min_streak > 0:
                budget_mode_trigger = budget_mode_trigger & (self._same_target_streak >= float(budget_min_streak))

        trigger_mode = self._cooldown_trigger_mode()
        if trigger_mode == "streak":
            trigger = streak_mode_trigger
            budget_trigger = torch.zeros_like(trigger)
        elif trigger_mode in {"budget", "budget_and_streak"}:
            trigger = budget_mode_trigger
            budget_trigger = budget_mode_trigger
        else:
            trigger = torch.zeros_like(streak_mode_trigger)
            budget_trigger = torch.zeros_like(streak_mode_trigger)

        duration = int(self._assignment_cooldown_config["duration_steps"])
        if duration <= 0:
            trigger = torch.zeros_like(trigger)
            budget_trigger = torch.zeros_like(budget_trigger)

        trigger_envs, trigger_agents = torch.nonzero(trigger, as_tuple=True)
        if trigger_envs.numel() == 0:
            if bool(self._assignment_cooldown_config["clear_on_covered"]):
                self._clear_assignment_cooldown_for_covered_targets(covered_after)
            return

        trigger_viewpoints = assignment[trigger_envs, trigger_agents]
        self._per_robot_target_cooldown_remaining[trigger_envs, trigger_agents, trigger_viewpoints] = duration
        self._assignment_cooldown_trigger_count += trigger.to(dtype=torch.float32).sum(dim=1)
        self._assignment_cooldown_budget_trigger_count += budget_trigger.to(dtype=torch.float32).sum(dim=1)
        self._assignment_cooldown_last_triggered_viewpoint[trigger_envs, trigger_agents] = trigger_viewpoints
        self._last_cooldown_triggered_after_step[trigger_envs, trigger_agents] = True
        budget_trigger_envs, budget_trigger_agents = torch.nonzero(budget_trigger, as_tuple=True)
        if budget_trigger_envs.numel() > 0:
            self._last_budget_triggered_by_budget[budget_trigger_envs, budget_trigger_agents] = True
            self._activate_assignment_redirect_guardrail_for_budget_triggers(
                budget_trigger=budget_trigger,
                assignment=assignment,
            )
            self._activate_assignment_failed_pair_memory_for_budget_triggers(
                budget_trigger=budget_trigger,
                assignment=assignment,
            )
        self._reset_budget_attempt_pairs(trigger_envs, trigger_agents)

        if bool(self._assignment_cooldown_config["clear_on_covered"]):
            self._clear_assignment_cooldown_for_covered_targets(covered_after)

    def _clear_assignment_cooldown_for_covered_targets(self, covered: torch.Tensor) -> None:
        covered_mask = covered.to(device=self._device, dtype=torch.bool).unsqueeze(1)
        if not bool(covered_mask.any()):
            return
        self._per_robot_target_failed_attempt_count = torch.where(
            covered_mask,
            torch.zeros_like(self._per_robot_target_failed_attempt_count),
            self._per_robot_target_failed_attempt_count,
        )
        self._per_robot_target_cooldown_remaining = torch.where(
            covered_mask,
            torch.zeros_like(self._per_robot_target_cooldown_remaining),
            self._per_robot_target_cooldown_remaining,
        )
        self._clear_budget_attempts_for_covered_targets(covered.to(device=self._device, dtype=torch.bool))

    def _clear_assignment_failed_pair_memory_for_covered_targets(self, covered: torch.Tensor) -> None:
        covered_mask = covered.to(device=self._device, dtype=torch.bool).unsqueeze(1)
        if not bool(covered_mask.any()):
            return
        self._assignment_failed_pair_memory_remaining = torch.where(
            covered_mask,
            torch.zeros_like(self._assignment_failed_pair_memory_remaining),
            self._assignment_failed_pair_memory_remaining,
        )
        self._assignment_failed_pair_memory_trigger_step = torch.where(
            covered_mask,
            torch.full_like(self._assignment_failed_pair_memory_trigger_step, -1),
            self._assignment_failed_pair_memory_trigger_step,
        )

    def _compute_assignment_reward_decomposition(
        self,
        *,
        base_reward_tensor: torch.Tensor,
        assignment: torch.Tensor,
        pre_step_problem: dict,
        post_step_problem: dict,
    ) -> dict[str, Any]:
        dtype = base_reward_tensor.dtype
        config = self._assignment_reward_config
        non_noop = (assignment >= 0).to(dtype=dtype)
        covered_before = pre_step_problem.get("viewpoints_covered", self._last_covered_mask).to(dtype=torch.bool)
        covered_after = post_step_problem["viewpoints_covered"].to(dtype=torch.bool)
        global_gain = (covered_after & (~covered_before)).any(dim=-1).to(dtype=dtype)
        no_global_gain = (global_gain <= 0.0).to(dtype=dtype).unsqueeze(-1)

        repeated_grace = int(config["repeated_assignment_grace_steps"])
        repeated_excess = torch.clamp(self._same_target_streak - float(repeated_grace), min=0.0)
        repeated_penalty = (
            -float(config["repeated_assignment_penalty_scale"]) * repeated_excess * non_noop * no_global_gain
        )

        no_progress_grace = int(config["no_progress_grace_steps"])
        no_progress_excess = torch.clamp(
            self._steps_since_global_coverage_gain - float(no_progress_grace),
            min=0.0,
        )
        no_progress_penalty_magnitude = float(config["no_progress_penalty_scale"]) * no_progress_excess
        no_progress_cap = float(config["no_progress_penalty_cap"])
        if no_progress_cap > 0.0:
            no_progress_penalty_magnitude = torch.clamp(no_progress_penalty_magnitude, max=no_progress_cap)
        global_no_progress_penalty = -no_progress_penalty_magnitude.unsqueeze(-1).expand(
            self._num_envs, self._num_agents
        )

        selected_path_cost_raw = self._selected_path_cost(assignment, pre_step_problem).to(dtype=dtype)
        selected_path_cost_norm = selected_path_cost_raw / self._env_spacing()
        selected_path_cost_penalty = (
            -float(config["selected_path_cost_penalty_scale"]) * selected_path_cost_norm * non_noop
        )

        repeated_penalty = repeated_penalty.unsqueeze(-1)
        global_no_progress_penalty = global_no_progress_penalty.unsqueeze(-1)
        selected_path_cost_penalty = selected_path_cost_penalty.unsqueeze(-1)
        total_adjustment = repeated_penalty + global_no_progress_penalty + selected_path_cost_penalty
        final_reward = base_reward_tensor + total_adjustment
        return {
            "config": dict(config),
            "base_env_reward": base_reward_tensor,
            "repeated_same_target_no_progress": repeated_penalty,
            "global_no_progress": global_no_progress_penalty,
            "selected_path_cost": selected_path_cost_penalty,
            "selected_path_cost_raw": selected_path_cost_raw.unsqueeze(-1),
            "selected_path_cost_norm": selected_path_cost_norm.unsqueeze(-1),
            "total_assignment_reward_adjustment": total_adjustment,
            "final_reward": final_reward,
            "same_target_streak": self._same_target_streak.unsqueeze(-1),
            "steps_since_global_coverage_gain": self._steps_since_global_coverage_gain.view(self._num_envs, 1, 1),
            "global_coverage_gain": global_gain.view(self._num_envs, 1, 1),
        }

    def _selected_path_cost(self, assignment: torch.Tensor, problem: dict) -> torch.Tensor:
        cost_matrix = problem["cost_matrix"].to(device=self._device, dtype=torch.float32)
        non_noop = assignment >= 0
        safe_ids = assignment.clamp(min=0).unsqueeze(-1)
        selected_cost = torch.gather(cost_matrix, dim=2, index=safe_ids).squeeze(-1)
        return torch.where(non_noop, selected_cost, torch.zeros_like(selected_cost))

    def _augment_assignment_observations(
        self,
        obs: dict[str, torch.Tensor],
        *,
        problem: dict | None = None,
    ) -> dict[str, torch.Tensor]:
        if problem is None:
            problem = self._unwrapped.get_assignment_problem()
        augmented = {}
        for agent in self._agents:
            agent_index = self._agent_map[agent]
            raw = obs[agent]
            if raw.ndim > 2:
                raw = raw.reshape(raw.shape[0], -1)
            extension = self._assignment_observation_extension(problem, agent_index)
            augmented[agent] = torch.cat((raw.to(dtype=torch.float32), extension), dim=-1)
        return augmented

    def _assignment_observation_extension(self, problem: dict, agent_index: int) -> torch.Tensor:
        dtype = torch.float32
        env_spacing = self._env_spacing()
        viewpoint_pos = problem["viewpoint_pos"].to(device=self._device, dtype=dtype)
        viewpoint_quat = problem["viewpoint_quat"].to(device=self._device, dtype=dtype)
        scanner_pos = problem["scanner_pos"][:, agent_index, :].to(device=self._device, dtype=dtype)
        covered = problem["viewpoints_covered"].to(device=self._device, dtype=torch.bool)
        available_mask = problem["available_mask"].to(device=self._device, dtype=torch.bool)
        feasible_mask = problem["feasible_mask"].to(device=self._device, dtype=torch.bool)
        static_mask = problem.get("static_geometric_feasible_mask", feasible_mask).to(device=self._device, dtype=torch.bool)
        cost_matrix = problem["cost_matrix"].to(device=self._device, dtype=dtype)

        relative_pos = (viewpoint_pos - scanner_pos.unsqueeze(1)) / env_spacing
        normalized_cost = torch.nan_to_num(cost_matrix[:, agent_index, :].unsqueeze(-1) / env_spacing)
        attempted_norm = torch.clamp(
            self._per_viewpoint_attempted_count / float(self._normalization_horizon), 0.0, 1.0
        ).unsqueeze(-1)
        never_attempted = self._last_viewpoint_attempt_step < 0
        age_steps = torch.clamp(
            self._assignment_step.unsqueeze(-1) - self._last_viewpoint_attempt_step,
            min=0,
        ).to(dtype=dtype)
        age_norm = torch.clamp(age_steps / float(self._normalization_horizon), 0.0, 1.0)
        age_norm = torch.where(never_attempted, torch.ones_like(age_norm), age_norm).unsqueeze(-1)
        viewpoint_rows = torch.cat(
            (
                relative_pos,
                viewpoint_quat,
                covered.to(dtype=dtype).unsqueeze(-1),
                available_mask[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
                feasible_mask[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
                static_mask[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
                normalized_cost,
                attempted_norm,
                age_norm,
            ),
            dim=-1,
        ).reshape(self._num_envs, self._num_viewpoints * self._viewpoint_row_dim)

        episode_progress = self._episode_progress_norm().unsqueeze(-1)
        agent_has_any_available = available_mask[:, agent_index, :].any(dim=-1, keepdim=True).to(dtype=dtype)
        team_has_any_available = available_mask.any(dim=(1, 2), keepdim=True).to(dtype=dtype).reshape(self._num_envs, 1)
        all_viewpoints_covered = covered.all(dim=-1, keepdim=True).to(dtype=dtype)
        previous_was_noop = (self._previous_assignment[:, agent_index] < 0).to(dtype=dtype).unsqueeze(-1)
        noop_context = torch.cat(
            (
                agent_has_any_available,
                team_has_any_available,
                all_viewpoints_covered,
                previous_was_noop,
                episode_progress,
            ),
            dim=-1,
        )

        previous_assignment_ids = torch.where(
            self._previous_assignment[:, agent_index] >= 0,
            self._previous_assignment[:, agent_index],
            torch.full(
                (self._num_envs,),
                self.noop_action_id,
                dtype=torch.long,
                device=self._device,
            ),
        )
        previous_assignment_one_hot = F.one_hot(
            previous_assignment_ids.clamp(min=0, max=self.noop_action_id),
            num_classes=self._previous_assignment_one_hot_dim,
        ).to(dtype=dtype)
        same_target_norm = torch.clamp(
            self._same_target_streak[:, agent_index] / float(self._normalization_horizon), 0.0, 1.0
        ).unsqueeze(-1)
        steps_since_gain_norm = torch.clamp(
            self._steps_since_global_coverage_gain / float(self._normalization_horizon), 0.0, 1.0
        ).unsqueeze(-1)
        completed_count_norm = torch.clamp(
            self._per_robot_completed_count[:, agent_index] / float(max(1, self._num_viewpoints)), 0.0, 1.0
        ).unsqueeze(-1)
        repeated_count_norm = torch.clamp(
            self._per_robot_repeated_assignment_count[:, agent_index] / float(self._normalization_horizon), 0.0, 1.0
        ).unsqueeze(-1)
        global_coverage_ratio = covered.to(dtype=dtype).mean(dim=-1, keepdim=True)
        total_uncovered_norm = (~covered).to(dtype=dtype).sum(dim=-1, keepdim=True) / float(
            max(1, self._num_viewpoints)
        )
        dynamic_scalars = torch.cat(
            (
                same_target_norm,
                steps_since_gain_norm,
                completed_count_norm,
                repeated_count_norm,
                global_coverage_ratio,
                total_uncovered_norm,
                episode_progress,
            ),
            dim=-1,
        )
        covered_vector = covered.to(dtype=dtype)
        return torch.cat(
            (
                viewpoint_rows,
                noop_context,
                previous_assignment_one_hot,
                dynamic_scalars,
                covered_vector,
            ),
            dim=-1,
        )

    def _infer_action_layout(self, actions: torch.Tensor) -> str:
        if tuple(actions.shape) == (self._num_envs, self._num_agents, 1):
            return "env_agent_action"
        if tuple(actions.shape) == (self._num_agents, self._num_envs, 1):
            return "agent_env_action"
        raise ValueError(
            "discrete actions must have shape "
            f"({self._num_envs}, {self._num_agents}, 1) or ({self._num_agents}, {self._num_envs}, 1), "
            f"got {tuple(actions.shape)}"
        )

    def _stack_rewards(self, rewards: dict[str, torch.Tensor]) -> torch.Tensor:
        return torch.stack([rewards[agent].reshape(self._num_envs) for agent in self._agents], dim=1).unsqueeze(-1)

    def _stack_dones(self, terminated: dict[str, torch.Tensor], truncated: dict[str, torch.Tensor]) -> torch.Tensor:
        terminated_tensor = torch.stack(
            [terminated[agent].to(dtype=torch.bool).reshape(self._num_envs) for agent in self._agents],
            dim=1,
        )
        truncated_tensor = torch.stack(
            [truncated[agent].to(dtype=torch.bool).reshape(self._num_envs) for agent in self._agents],
            dim=1,
        )
        return torch.logical_or(terminated_tensor, truncated_tensor)

    def _selected_available_mask(self, assignment: torch.Tensor, available_actions: torch.Tensor) -> torch.Tensor:
        if self._num_viewpoints == 0:
            return torch.zeros_like(assignment, dtype=torch.bool)
        viewpoint_mask = available_actions[..., : self._num_viewpoints].to(dtype=torch.bool)
        non_noop = assignment >= 0
        safe_ids = assignment.clamp(min=0).unsqueeze(-1)
        selected_available = torch.gather(viewpoint_mask, dim=2, index=safe_ids).squeeze(-1)
        return selected_available & non_noop

    def _make_lifecycle_resolution_payload(
        self,
        *,
        assignment_proposal: torch.Tensor,
        effective_assignment: torch.Tensor,
        pre_result: Any,
        post_result: Any,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "enabled": bool(self._assignment_lifecycle_resolver_config["enabled"]),
            "assignment_proposal": assignment_proposal.detach().clone(),
            "effective_assignment": effective_assignment.detach().clone(),
            "proposal_effective_changed": (
                assignment_proposal.to(device=effective_assignment.device) != effective_assignment
            ).detach().clone(),
            "proposal_accepted": pre_result.proposal_accepted.detach().clone(),
            "proposal_rejected_reason": pre_result.proposal_rejected_reason.detach().clone(),
            "continued_from_active_target": pre_result.continued_from_active_target.detach().clone(),
            "new_claim_started": pre_result.new_claim_started.detach().clone(),
            "switch_requested": pre_result.switch_requested.detach().clone(),
            "switch_rejected": pre_result.switch_rejected.detach().clone(),
            "claim_conflict": pre_result.claim_conflict.detach().clone(),
            "claim_winner": pre_result.claim_winner.detach().clone(),
            "claim_loser": pre_result.claim_loser.detach().clone(),
            "pre_behavior_changed": bool(pre_result.behavior_changed),
            "post_completed": post_result.completed.detach().clone(),
            "post_released": post_result.released.detach().clone(),
            "post_release_reason": post_result.release_reason.detach().clone(),
            "post_failure_reason": post_result.failure_reason.detach().clone(),
            "post_reset_env_ids": list(post_result.reset_env_ids),
            "post_behavior_changed": bool(post_result.behavior_changed),
            "resolver_snapshot": self._clone_lifecycle_resolution_payload(
                self._assignment_lifecycle_resolver_runtime.snapshot()
            ),
            "resolver_events": [dict(event) for event in events],
        }

    def _clone_lifecycle_resolution_payload(self, payload: Any) -> Any:
        if payload is None:
            return None
        if isinstance(payload, torch.Tensor):
            return payload.detach().clone()
        if isinstance(payload, dict):
            return {str(key): self._clone_lifecycle_resolution_payload(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._clone_lifecycle_resolution_payload(value) for value in payload]
        if isinstance(payload, tuple):
            return tuple(self._clone_lifecycle_resolution_payload(value) for value in payload)
        return payload

    def _augment_info(
        self,
        info: Any,
        *,
        duplicate_count: torch.Tensor,
        noop_count: torch.Tensor,
        valid_action_count: torch.Tensor,
        selected_available_mask: torch.Tensor,
        reward_decomposition: dict[str, Any],
    ) -> dict:
        if isinstance(info, dict):
            augmented = dict(info)
        else:
            augmented = {"env_info": info}
        augmented["assignment_rl"] = {
            "duplicate_count": duplicate_count,
            "noop_count": noop_count,
            "valid_action_count": valid_action_count,
            "selected_available_mask": selected_available_mask,
        }
        augmented["assignment_rl_reward"] = reward_decomposition
        if bool(self._assignment_cooldown_config["log_diagnostics"]):
            augmented["assignment_cooldown"] = self._assignment_cooldown_info()
        if bool(self._assignment_redirect_guardrail_config["log_diagnostics"]):
            augmented["assignment_redirect_guardrail"] = self._assignment_redirect_guardrail_info()
        if bool(self._assignment_failed_pair_memory_config["log_diagnostics"]):
            augmented["assignment_failed_pair_memory"] = self._assignment_failed_pair_memory_info()
        return augmented

    def _assignment_cooldown_info(self) -> dict[str, Any]:
        if self._assignment_cooldown_enabled():
            active_count = (self._per_robot_target_cooldown_remaining > 0).to(dtype=torch.float32).sum(dim=(1, 2))
            suppressed_per_env = self._assignment_cooldown_suppressed_count.sum(dim=1)
            failed_attempt_count = self._per_robot_target_failed_attempt_count.to(dtype=torch.float32)
            max_remaining = self._per_robot_target_cooldown_remaining.amax(dim=(1, 2)).to(dtype=torch.float32)
            last_triggered = self._assignment_cooldown_last_triggered_viewpoint
            triggered_pair_count = self._last_cooldown_triggered_after_step.to(dtype=torch.float32).sum(dim=1)
            budget_valid = self._last_budget_steps_for_selected_pair > 0
            budget_valid_float = budget_valid.to(dtype=torch.float32)
            budget_count = budget_valid_float.sum(dim=1).clamp(min=1.0)
            budget_attempt_steps = self._last_budget_attempt_steps_for_selected_pair.to(dtype=torch.float32)
            budget_steps = self._last_budget_steps_for_selected_pair.to(dtype=torch.float32)
            budget_ratio = self._last_budget_ratio_for_selected_pair.to(dtype=torch.float32)
            budget_attempt_steps_mean = (budget_attempt_steps * budget_valid_float).sum(dim=1) / budget_count
            budget_steps_mean = (budget_steps * budget_valid_float).sum(dim=1) / budget_count
            budget_ratio_mean = (budget_ratio * budget_valid_float).sum(dim=1) / budget_count
            budget_attempt_steps_max = budget_attempt_steps.amax(dim=1)
            budget_steps_max = budget_steps.amax(dim=1)
            budget_ratio_max = budget_ratio.amax(dim=1)
            budget_triggered_pair_count = self._last_budget_triggered_by_budget.to(dtype=torch.float32).sum(dim=1)
        else:
            active_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            suppressed_per_env = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            failed_attempt_count = torch.zeros(
                self._num_envs,
                self._num_agents,
                self._num_viewpoints,
                dtype=torch.float32,
                device=self._device,
            )
            max_remaining = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            last_triggered = torch.full(
                (self._num_envs, self._num_agents), -1, dtype=torch.long, device=self._device
            )
            triggered_pair_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_attempt_steps_mean = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_steps_mean = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_ratio_mean = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_attempt_steps_max = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_steps_max = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_ratio_max = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            budget_triggered_pair_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)

        trigger_mode = self._cooldown_trigger_mode()
        trigger_mode_code = {"streak": 0.0, "budget": 1.0, "budget_and_streak": 2.0}.get(trigger_mode, -1.0)

        return {
            "enabled": float(self._assignment_cooldown_enabled()),
            "trigger_mode": trigger_mode,
            "trigger_mode_code": trigger_mode_code,
            "active_count": active_count,
            "active_count_mean": active_count,
            "trigger_count": self._assignment_cooldown_trigger_count
            if self._assignment_cooldown_enabled()
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "trigger_count_mean": self._assignment_cooldown_trigger_count
            if self._assignment_cooldown_enabled()
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "triggered_pair_count": triggered_pair_count,
            "suppressed_action_count": suppressed_per_env,
            "suppressed_action_count_mean": suppressed_per_env,
            "failed_attempt_count_mean": failed_attempt_count,
            "max_cooldown_remaining": max_remaining,
            "max_cooldown_remaining_mean": max_remaining,
            "selected_target_was_in_cooldown_count": (
                self._assignment_cooldown_selected_target_was_in_cooldown_count
                if self._assignment_cooldown_enabled()
                else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            ),
            "last_triggered_viewpoint": last_triggered,
            "budget_multiplier": float(self._assignment_cooldown_config["budget_multiplier"]),
            "budget_slack_steps": float(self._assignment_cooldown_config["budget_slack_steps"]),
            "budget_min_streak": float(self._assignment_cooldown_config["budget_min_streak"]),
            "budget_trigger_count": self._assignment_cooldown_budget_trigger_count
            if self._assignment_cooldown_enabled()
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "budget_over_budget_selected_count": self._assignment_cooldown_budget_over_budget_selected_count
            if self._assignment_cooldown_enabled()
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "budget_triggered_pair_count": budget_triggered_pair_count,
            "budget_attempt_steps_mean": budget_attempt_steps_mean,
            "budget_attempt_steps_max": budget_attempt_steps_max,
            "budget_steps_mean": budget_steps_mean,
            "budget_steps_max": budget_steps_max,
            "budget_budget_steps_mean": budget_steps_mean,
            "budget_budget_steps_max": budget_steps_max,
            "budget_ratio_mean": budget_ratio_mean,
            "budget_ratio_max": budget_ratio_max,
            "budget_last_triggered_by_budget": self._last_budget_triggered_by_budget.to(dtype=torch.float32)
            if self._assignment_cooldown_enabled()
            else torch.zeros(self._num_envs, self._num_agents, dtype=torch.float32, device=self._device),
            "budget_last_triggered_by_budget_count": budget_triggered_pair_count,
        }

    def _assignment_redirect_guardrail_info(self) -> dict[str, Any]:
        enabled = self._assignment_redirect_guardrail_enabled()
        active = getattr(
            self,
            "_last_pre_step_redirect_guardrail_active_for_robot",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.bool, device=self._device),
        )
        claimed_count = getattr(
            self,
            "_last_pre_step_redirect_guardrail_claimed_suppressed_count",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.long, device=self._device),
        )
        spacing_count = getattr(
            self,
            "_last_pre_step_redirect_guardrail_spacing_suppressed_count",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.long, device=self._device),
        )
        overmask_count = getattr(
            self,
            "_last_pre_step_redirect_guardrail_overmask_non_noop_count",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.long, device=self._device),
        )
        only_noop = getattr(
            self,
            "_last_pre_step_redirect_guardrail_only_noop_remaining",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.bool, device=self._device),
        )
        fail_open_count = getattr(
            self,
            "_last_pre_step_redirect_guardrail_fail_open_count",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.long, device=self._device),
        )
        threshold = getattr(
            self,
            "_last_pre_step_redirect_guardrail_threshold",
            torch.zeros(self._num_envs, self._num_agents, dtype=torch.float32, device=self._device),
        )
        active_float = active.to(dtype=torch.float32)
        active_count = active_float.sum(dim=1)
        threshold_count = active_count.clamp(min=1.0)
        threshold_mean = (threshold.to(dtype=torch.float32) * active_float).sum(dim=1) / threshold_count
        threshold_mean = torch.where(active_count > 0.0, threshold_mean, torch.zeros_like(threshold_mean))
        return {
            "enabled": float(enabled),
            "context": str(self._assignment_redirect_guardrail_config["apply_context"]),
            "active_count": active_count if enabled else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "claimed_suppressed_count": claimed_count.to(dtype=torch.float32).sum(dim=1)
            if enabled
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "spacing_suppressed_count": spacing_count.to(dtype=torch.float32).sum(dim=1)
            if enabled
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "overmask_count": overmask_count.to(dtype=torch.float32).sum(dim=1)
            if enabled
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "only_noop_remaining_count": only_noop.to(dtype=torch.float32).sum(dim=1)
            if enabled
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "fail_open_count": fail_open_count.to(dtype=torch.float32).sum(dim=1)
            if enabled
            else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
            "threshold": threshold_mean if enabled else torch.zeros(self._num_envs, dtype=torch.float32, device=self._device),
        }

    def _assignment_failed_pair_memory_info(self) -> dict[str, Any]:
        enabled = self._assignment_failed_pair_memory_enabled()
        if enabled:
            active_count = (self._assignment_failed_pair_memory_remaining > 0).to(dtype=torch.float32).sum(dim=(1, 2))
            suppressed_count_per_robot = self._last_failed_pair_memory_suppressed_count.to(dtype=torch.float32)
            fail_open_count_per_robot = self._last_failed_pair_memory_fail_open_count.to(dtype=torch.float32)
            only_noop_remaining_per_robot = self._last_failed_pair_memory_only_noop_remaining.to(dtype=torch.float32)
            suppressed_count = suppressed_count_per_robot.sum(dim=1)
            fail_open_count = fail_open_count_per_robot.sum(dim=1)
            only_noop_count = only_noop_remaining_per_robot.sum(dim=1)
            selected_pair_active = self._last_failed_pair_memory_selected_pair_active.to(dtype=torch.float32)
            selected_pair_ttl = self._last_failed_pair_memory_selected_pair_ttl_remaining.to(dtype=torch.float32)
            trigger_count = torch.as_tensor(
                [len(ids) for ids in self._last_failed_pair_memory_trigger_robot_ids],
                dtype=torch.float32,
                device=self._device,
            )
            last_trigger_robot_ids = [list(ids) for ids in self._last_failed_pair_memory_trigger_robot_ids]
            last_trigger_target_ids = [list(ids) for ids in self._last_failed_pair_memory_trigger_target_ids]
            last_trigger_reason = [list(reasons) for reasons in self._last_failed_pair_memory_trigger_reasons]
        else:
            active_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            suppressed_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            fail_open_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            only_noop_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            suppressed_count_per_robot = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            fail_open_count_per_robot = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            only_noop_remaining_per_robot = torch.zeros(
                self._num_envs, self._num_agents, dtype=torch.float32, device=self._device
            )
            selected_pair_active = torch.zeros(self._num_envs, self._num_agents, dtype=torch.float32, device=self._device)
            selected_pair_ttl = torch.zeros(self._num_envs, self._num_agents, dtype=torch.float32, device=self._device)
            trigger_count = torch.zeros(self._num_envs, dtype=torch.float32, device=self._device)
            last_trigger_robot_ids = [[] for _ in range(self._num_envs)]
            last_trigger_target_ids = [[] for _ in range(self._num_envs)]
            last_trigger_reason = [[] for _ in range(self._num_envs)]

        return {
            "enabled": float(enabled),
            "source": str(self._assignment_failed_pair_memory_config["source"]),
            "duration_steps": float(self._assignment_failed_pair_memory_config["duration_steps"]),
            "apply_to_action_mask": float(self._assignment_failed_pair_memory_config["apply_to_action_mask"]),
            "fail_open": float(self._assignment_failed_pair_memory_config["fail_open"]),
            "clear_on_coverage": float(self._assignment_failed_pair_memory_config["clear_on_coverage"]),
            "active_count": active_count,
            "suppressed_count": suppressed_count,
            "suppressed_count_per_robot": suppressed_count_per_robot,
            "fail_open_count": fail_open_count,
            "fail_open_count_per_robot": fail_open_count_per_robot,
            "only_noop_remaining_count": only_noop_count,
            "only_noop_remaining_per_robot": only_noop_remaining_per_robot,
            "selected_pair_active": selected_pair_active,
            "selected_pair_ttl_remaining": selected_pair_ttl,
            "trigger_count": trigger_count,
            "last_trigger_robot_ids": last_trigger_robot_ids,
            "last_trigger_target_ids": last_trigger_target_ids,
            "last_trigger_reason": last_trigger_reason,
        }


def make_assignment_harl_env(
    task: str,
    *,
    cfg: Any | None = None,
    render_mode: str | None = None,
    include_noop: bool = True,
    strict_decode: bool = True,
    **gym_kwargs,
) -> AssignmentHarlWrapper:
    """Construct the normal IsaacLab scan env and wrap it with assignment Discrete actions."""

    if cfg is not None:
        gym_kwargs["cfg"] = cfg
    if render_mode is not None:
        gym_kwargs["render_mode"] = render_mode
    env = gymnasium.make(task, **gym_kwargs)
    return AssignmentHarlWrapper(env, include_noop=include_noop, strict_decode=strict_decode)


__all__ = [
    "AssignmentHarlWrapper",
    "make_assignment_harl_env",
]
