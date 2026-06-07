# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Any, Mapping

import gymnasium
import numpy as np
import torch

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
        return {self._agent_map[agent]: self._unwrapped.observation_spaces[agent] for agent in self._agents}

    @property
    def share_observation_space(self) -> Mapping[int, gymnasium.Space]:
        state_space = getattr(self._unwrapped, "state_space", None)
        if state_space is None:
            shape = 0
            for agent in self._agents:
                shape += int(np.prod(self._unwrapped.observation_spaces[agent].shape))
            state_space = gymnasium.spaces.Box(-np.inf, np.inf, shape=(shape,), dtype=np.float32)
        return {agent_id: state_space for agent_id in range(self._num_agents)}

    def reset(self, *args, **kwargs) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor]:
        obs, _ = self._env.reset(*args, **kwargs)
        self._sync_agents(obs)
        shared_obs = self._build_shared_obs(obs)
        available_actions = self._build_available_actions()
        self.last_available_actions = available_actions
        return obs, shared_obs, available_actions

    def step(
        self,
        discrete_actions: torch.Tensor,
        layout: str | None = None,
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor, torch.Tensor, torch.Tensor, dict, torch.Tensor]:
        pre_step_available_actions = self._build_available_actions()
        assignment = self.decode_actions(discrete_actions, layout=layout)
        env_actions = self.assignment_to_env_actions(assignment)
        selected_available_mask = self._selected_available_mask(assignment, pre_step_available_actions)

        obs, rewards, terminated, truncated, info = self._env.step(env_actions)
        self._sync_agents(obs)

        shared_obs = self._build_shared_obs(obs)
        reward_tensor = self._stack_rewards(rewards)
        dones = self._stack_dones(terminated, truncated)
        available_actions = self._build_available_actions()

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

        info = self._augment_info(
            info,
            duplicate_count=duplicate_count,
            noop_count=noop_count,
            valid_action_count=valid_action_count,
            selected_available_mask=selected_available_mask,
        )
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

    def _build_shared_obs(self, obs: dict[str, torch.Tensor]) -> torch.Tensor:
        observations = []
        for agent in self._agents:
            observation = obs[agent]
            if observation.ndim > 2:
                observation = observation.reshape(observation.shape[0], -1)
            observations.append(observation)
        shared = torch.cat(observations, dim=-1)
        return torch.stack([shared for _ in range(self._num_agents)], dim=1)

    def _build_available_actions(self) -> torch.Tensor:
        problem = self._unwrapped.get_assignment_problem()
        available_actions = make_assignment_action_mask(problem, include_noop=self.include_noop)
        expected_shape = (self._num_envs, self._num_agents, self._num_viewpoints + int(self.include_noop))
        if tuple(available_actions.shape) != expected_shape:
            raise RuntimeError(f"available_actions must have shape {expected_shape}, got {tuple(available_actions.shape)}")
        return available_actions

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
