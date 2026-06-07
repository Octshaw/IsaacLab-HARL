# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch


def make_assignment_action_mask(problem: dict, include_noop: bool = True) -> torch.Tensor:
    """Build a HARL-compatible discrete action mask from an assignment problem.

    Args:
        problem: Assignment problem returned by ``env.get_assignment_problem()``.
        include_noop: If true, append an always-available no-op action column.

    Returns:
        Float mask with shape ``[num_envs, num_agents, num_viewpoints]`` or
        ``[num_envs, num_agents, num_viewpoints + 1]`` when no-op is included.
        A value of 1 means the action is available and 0 means masked out.
    """
    if "available_mask" not in problem:
        raise KeyError("problem must contain 'available_mask'")

    available_mask = problem["available_mask"]
    if not isinstance(available_mask, torch.Tensor):
        raise TypeError(f"problem['available_mask'] must be a torch.Tensor, got {type(available_mask).__name__}")
    if available_mask.ndim != 3:
        raise ValueError(f"available_mask must have shape [num_envs, num_agents, num_viewpoints], got {tuple(available_mask.shape)}")

    mask = available_mask.to(dtype=torch.float32)
    if not include_noop:
        return mask

    noop_mask = torch.ones(*mask.shape[:2], 1, dtype=torch.float32, device=mask.device)
    return torch.cat((mask, noop_mask), dim=-1)


def decode_discrete_assignment(
    actions: torch.Tensor,
    num_viewpoints: int,
    num_envs: int,
    num_agents: int,
    layout: str = "env_agent_action",
    strict: bool = True,
) -> torch.Tensor:
    """Decode scalar discrete policy actions into a viewpoint assignment tensor.

    Supported layouts:
        - ``env_agent_action``: actions shape ``[num_envs, num_agents, 1]``.
        - ``agent_env_action``: actions shape ``[num_agents, num_envs, 1]``.

    Decode convention:
        - ``0..num_viewpoints - 1`` map to viewpoint ids.
        - ``num_viewpoints`` maps to no-op ``-1``.
    """
    if not isinstance(actions, torch.Tensor):
        raise TypeError(f"actions must be a torch.Tensor, got {type(actions).__name__}")
    if num_viewpoints < 0:
        raise ValueError(f"num_viewpoints must be non-negative, got {num_viewpoints}")
    if num_envs <= 0:
        raise ValueError(f"num_envs must be positive, got {num_envs}")
    if num_agents <= 0:
        raise ValueError(f"num_agents must be positive, got {num_agents}")

    if layout == "env_agent_action":
        expected_shape = (num_envs, num_agents, 1)
        if tuple(actions.shape) != expected_shape:
            raise ValueError(f"actions must have shape {expected_shape} for env_agent_action, got {tuple(actions.shape)}")
        raw_actions = actions[:, :, 0]
    elif layout == "agent_env_action":
        expected_shape = (num_agents, num_envs, 1)
        if tuple(actions.shape) != expected_shape:
            raise ValueError(f"actions must have shape {expected_shape} for agent_env_action, got {tuple(actions.shape)}")
        raw_actions = actions[:, :, 0].transpose(0, 1).contiguous()
    else:
        raise ValueError("layout must be either 'env_agent_action' or 'agent_env_action'")

    if torch.is_floating_point(raw_actions):
        if strict:
            integer_actions = torch.isfinite(raw_actions) & (raw_actions == torch.trunc(raw_actions))
            if not bool(integer_actions.all()):
                raise ValueError("actions must contain finite scalar integer ids in strict mode")
        raw_ids = raw_actions.to(dtype=torch.long)
    else:
        raw_ids = raw_actions.to(dtype=torch.long)

    invalid = (raw_ids < 0) | (raw_ids > num_viewpoints)
    if strict and bool(invalid.any()):
        raise ValueError(f"actions contain ids outside [0, {num_viewpoints}]")
    if not strict:
        raw_ids = torch.where(invalid, torch.full_like(raw_ids, num_viewpoints), raw_ids)

    return torch.where(raw_ids == num_viewpoints, torch.full_like(raw_ids, -1), raw_ids)


def assignment_to_env_actions(env, assignment: torch.Tensor) -> dict[str, torch.Tensor]:
    """Convert assignments to env actions through the existing controller."""
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import viewpoint_assignment_to_actions

    return viewpoint_assignment_to_actions(env, assignment)


def compute_assignment_duplicate_count(assignment: torch.Tensor) -> torch.Tensor:
    """Count duplicate non-no-op viewpoint selections for each environment."""
    if not isinstance(assignment, torch.Tensor):
        raise TypeError(f"assignment must be a torch.Tensor, got {type(assignment).__name__}")
    if assignment.ndim != 2:
        raise ValueError(f"assignment must have shape [num_envs, num_agents], got {tuple(assignment.shape)}")

    duplicates = torch.zeros(assignment.shape[0], dtype=torch.float32, device=assignment.device)
    for env_id in range(assignment.shape[0]):
        selected = assignment[env_id][assignment[env_id] >= 0]
        if selected.numel() == 0:
            continue
        duplicates[env_id] = float(selected.numel() - torch.unique(selected).numel())
    return duplicates


__all__ = [
    "assignment_to_env_actions",
    "compute_assignment_duplicate_count",
    "decode_discrete_assignment",
    "make_assignment_action_mask",
]
