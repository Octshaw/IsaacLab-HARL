# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import gymnasium
import torch

try:
    from .assignment_rl_interface import decode_discrete_assignment, make_assignment_action_mask
except ImportError:  # Allows file-based smoke tests without importing the Isaac task package.
    from assignment_rl_interface import decode_discrete_assignment, make_assignment_action_mask


def make_assignment_discrete_action_space(num_viewpoints: int) -> gymnasium.spaces.Discrete:
    """Create the HARL-facing scalar assignment action space."""
    if num_viewpoints <= 0:
        raise ValueError(f"num_viewpoints must be positive, got {num_viewpoints}")
    return gymnasium.spaces.Discrete(num_viewpoints + 1)


def make_assignment_discrete_action_spaces(
    num_agents: int,
    num_viewpoints: int,
    agent_ids: Sequence[int] | None = None,
) -> dict[int, gymnasium.spaces.Discrete]:
    """Create one Discrete(num_viewpoints + 1) action space per agent."""
    if num_agents <= 0:
        raise ValueError(f"num_agents must be positive, got {num_agents}")

    if agent_ids is None:
        agent_ids = tuple(range(num_agents))
    if len(agent_ids) != num_agents:
        raise ValueError(f"agent_ids length must match num_agents={num_agents}, got {len(agent_ids)}")

    return {int(agent_id): make_assignment_discrete_action_space(num_viewpoints) for agent_id in agent_ids}


def get_harl_scalar_action_dim(action_space: gymnasium.Space) -> int:
    """Return the scalar action storage dim HARL should use for an action space.

    For Discrete spaces this is 1, not action_space.n. The Categorical head has
    n logits internally, but sampled actions are stored as scalar ids.
    """
    action_type = action_space.__class__.__name__
    if action_type == "Discrete":
        return 1
    if action_type in {"Box", "MultiBinary", "MultiDiscrete"}:
        return int(action_space.shape[0])
    raise NotImplementedError(f"Unsupported HARL action space type: {action_type}")


def get_harl_available_action_dim(action_space: gymnasium.Space) -> int | None:
    """Return the available_actions mask width for action spaces that use masks."""
    if action_space.__class__.__name__ == "Discrete":
        return int(action_space.n)
    return None


def get_max_harl_scalar_action_dim(action_spaces: Mapping[int, gymnasium.Space]) -> int:
    """Return the max scalar action dim for runner/play tensor allocation."""
    if not action_spaces:
        raise ValueError("action_spaces must be non-empty")
    return max(get_harl_scalar_action_dim(action_space) for action_space in action_spaces.values())


def make_harl_action_tensor(
    num_envs: int,
    action_spaces: Mapping[int, gymnasium.Space],
    device: torch.device | str | None = None,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """Allocate a HARL action tensor with scalar Discrete ids stored in width 1."""
    if num_envs <= 0:
        raise ValueError(f"num_envs must be positive, got {num_envs}")
    max_action_dim = get_max_harl_scalar_action_dim(action_spaces)
    return torch.zeros((num_envs, len(action_spaces), max_action_dim), dtype=dtype, device=device)


@dataclass(frozen=True)
class AssignmentHarlAdapter:
    """Small repo-local adapter for Phase 2 Discrete action shape smoke tests.

    This class intentionally does not call env.step(). Phase 3 should use the
    same helpers inside an assignment-aware IsaacLab wrapper.
    """

    num_envs: int
    num_agents: int
    num_viewpoints: int
    device: torch.device | str | None = None

    @property
    def noop_action_id(self) -> int:
        return self.num_viewpoints

    @property
    def action_spaces(self) -> dict[int, gymnasium.spaces.Discrete]:
        return make_assignment_discrete_action_spaces(self.num_agents, self.num_viewpoints)

    @property
    def max_scalar_action_dim(self) -> int:
        return get_max_harl_scalar_action_dim(self.action_spaces)

    def make_action_tensor(self, dtype: torch.dtype = torch.float32) -> torch.Tensor:
        return make_harl_action_tensor(self.num_envs, self.action_spaces, device=self.device, dtype=dtype)

    def make_available_actions(self, problem: dict, include_noop: bool = True) -> torch.Tensor:
        return make_assignment_action_mask(problem, include_noop=include_noop)

    def decode_actions(
        self,
        actions: torch.Tensor,
        layout: str = "env_agent_action",
        strict: bool = True,
    ) -> torch.Tensor:
        return decode_discrete_assignment(
            actions,
            num_viewpoints=self.num_viewpoints,
            num_envs=self.num_envs,
            num_agents=self.num_agents,
            layout=layout,
            strict=strict,
        )


__all__ = [
    "AssignmentHarlAdapter",
    "get_harl_available_action_dim",
    "get_harl_scalar_action_dim",
    "get_max_harl_scalar_action_dim",
    "make_assignment_discrete_action_space",
    "make_assignment_discrete_action_spaces",
    "make_harl_action_tensor",
]
