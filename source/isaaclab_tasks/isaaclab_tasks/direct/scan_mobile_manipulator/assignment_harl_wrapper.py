# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

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

        self._adapter = AssignmentHarlAdapter(
            num_envs=self._num_envs,
            num_agents=self._num_agents,
            num_viewpoints=self._num_viewpoints,
            device=self._device,
        )
        self._action_space = make_assignment_discrete_action_spaces(self._num_agents, self._num_viewpoints)
        self._max_scalar_action_dim = max(get_harl_scalar_action_dim(space) for space in self._action_space.values())

        self.last_assignment: torch.Tensor | None = None
        self.last_env_actions: dict[str, torch.Tensor] | None = None
        self.last_pre_step_available_actions: torch.Tensor | None = None
        self.last_available_actions: torch.Tensor | None = None
        self.last_duplicate_count: torch.Tensor | None = None
        self.last_noop_count: torch.Tensor | None = None
        self.last_valid_action_count: torch.Tensor | None = None
        self.last_selected_available_mask: torch.Tensor | None = None
        self.last_assignment_reward_terms: dict[str, Any] | None = None

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

    def reset(self, *args, **kwargs) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor]:
        obs, _ = self._env.reset(*args, **kwargs)
        problem = self._unwrapped.get_assignment_problem()
        self._reset_assignment_diagnostics(problem=problem)
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
        assignment = self.decode_actions(discrete_actions, layout=layout)
        env_actions = self.assignment_to_env_actions(assignment)
        selected_available_mask = self._selected_available_mask(assignment, pre_step_available_actions)

        obs, rewards, terminated, truncated, info = self._env.step(env_actions)
        post_step_problem = self._unwrapped.get_assignment_problem()
        dones = self._stack_dones(terminated, truncated)
        done_env_ids = torch.nonzero(torch.all(dones, dim=1), as_tuple=False).flatten()
        self._update_assignment_diagnostics(
            assignment=assignment,
            pre_step_problem=pre_step_problem,
            post_step_problem=post_step_problem,
        )

        reward_tensor = self._stack_rewards(rewards)
        reward_decomposition = self._compute_assignment_reward_decomposition(
            base_reward_tensor=reward_tensor,
            assignment=assignment,
            pre_step_problem=pre_step_problem,
            post_step_problem=post_step_problem,
        )
        reward_tensor = reward_decomposition["final_reward"]
        available_actions = self._build_available_actions(problem=post_step_problem)

        duplicate_count = compute_assignment_duplicate_count(assignment)
        noop_count = (assignment < 0).sum(dim=1).to(dtype=torch.float32)
        valid_action_count = (assignment >= 0).sum(dim=1).to(dtype=torch.float32)

        self.last_assignment = assignment
        self.last_env_actions = env_actions
        self.last_pre_step_available_actions = pre_step_available_actions
        self.last_available_actions = available_actions
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

        if done_env_ids.numel() > 0:
            self._reset_assignment_diagnostics(env_ids=done_env_ids, problem=post_step_problem)

        obs = self._augment_assignment_observations(obs, problem=post_step_problem)
        self._sync_agents(obs)
        shared_obs = self._build_shared_obs(obs)
        return obs, shared_obs, reward_tensor, dones, info, available_actions

    def close(self) -> None:
        self._env.close()

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
        available_actions = make_assignment_action_mask(problem, include_noop=self.include_noop)
        expected_shape = (self._num_envs, self._num_agents, self._num_viewpoints + int(self.include_noop))
        if tuple(available_actions.shape) != expected_shape:
            raise RuntimeError(f"available_actions must have shape {expected_shape}, got {tuple(available_actions.shape)}")
        return available_actions

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

        self._assignment_step[env_ids] = 0
        self._per_viewpoint_attempted_count[env_ids] = 0.0
        self._last_viewpoint_attempt_step[env_ids] = -1
        self._previous_assignment[env_ids] = -1
        self._same_target_streak[env_ids] = 0.0
        self._steps_since_global_coverage_gain[env_ids] = 0.0
        self._per_robot_completed_count[env_ids] = 0.0
        self._per_robot_repeated_assignment_count[env_ids] = 0.0
        self._per_robot_selected_count[env_ids] = 0.0
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
        return augmented


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
