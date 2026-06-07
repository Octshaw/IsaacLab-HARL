# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch


def wrap_to_pi(angle: torch.Tensor) -> torch.Tensor:
    """Wrap angles to [-pi, pi] while preserving tensor shape and device."""
    return torch.atan2(torch.sin(angle), torch.cos(angle))


def _euler_xyz_from_quat(quat: torch.Tensor) -> torch.Tensor:
    """Convert WXYZ quaternions to XYZ Euler angles.

    Isaac Lab stores quaternions in scalar-first order. The scripted controller only needs a lightweight orientation
    error that can be mapped to the 9D action's roll/pitch/yaw slots, so this helper avoids adding another dependency
    or changing the environment's quaternion convention.
    """
    q_w, q_x, q_y, q_z = quat[..., 0], quat[..., 1], quat[..., 2], quat[..., 3]

    sin_roll = 2.0 * (q_w * q_x + q_y * q_z)
    cos_roll = 1.0 - 2.0 * (q_x * q_x + q_y * q_y)
    roll = torch.atan2(sin_roll, cos_roll)

    sin_pitch = 2.0 * (q_w * q_y - q_z * q_x)
    pitch = torch.asin(torch.clamp(sin_pitch, -1.0, 1.0))

    sin_yaw = 2.0 * (q_w * q_z + q_x * q_y)
    cos_yaw = 1.0 - 2.0 * (q_y * q_y + q_z * q_z)
    yaw = torch.atan2(sin_yaw, cos_yaw)

    return torch.stack((roll, pitch, yaw), dim=-1)


def viewpoint_assignment_to_actions(env, assignment: torch.Tensor) -> dict[str, torch.Tensor]:
    """Convert high-level viewpoint assignments to low-level 9D continuous actions.

    Args:
        env: ScanMobileManipulatorEnv instance.
        assignment: Long tensor with shape ``[num_envs, num_agents]``. Each value is a target viewpoint id, or
            ``-1`` for no-op.

    Returns:
        Dict from agent name to action tensor with shape ``[num_envs, 9]``.
    """
    # Pull a fresh problem snapshot so the controller sees the same feasibility/coverage masks as solvers. All tensors
    # remain on env.device; this function should be usable inside fast headless loops without CPU synchronization.
    problem = env.get_assignment_problem()
    num_envs = problem["num_envs"]
    num_agents = problem["num_agents"]
    num_viewpoints = problem["num_viewpoints"]
    device = torch.device(env.device)

    if assignment.dtype != torch.long:
        raise TypeError(f"assignment must have dtype torch.long, got {assignment.dtype}")
    if tuple(assignment.shape) != (num_envs, num_agents):
        raise ValueError(f"assignment must have shape ({num_envs}, {num_agents}), got {tuple(assignment.shape)}")

    # The caller may construct the assignment on CPU. Move it to the environment device only after shape/dtype checks so
    # downstream indexing and returned actions are device-consistent.
    assignment = assignment.to(device=device)
    actions = torch.zeros(num_envs, num_agents, 9, device=device, dtype=torch.float32)
    if num_viewpoints == 0:
        return {agent: actions[:, index, :] for agent, index in env.agent_index.items()}

    env_ids = torch.arange(num_envs, device=device).view(-1, 1).expand(num_envs, num_agents)
    agent_ids = torch.arange(num_agents, device=device).view(1, -1).expand(num_envs, num_agents)

    in_range = (assignment >= 0) & (assignment < num_viewpoints)
    safe_assignment = assignment.clamp(min=0, max=num_viewpoints - 1)

    # Invalid assignments are clamped only for safe tensor indexing. The `valid` mask below still turns invalid,
    # covered, or infeasible targets into zero actions rather than silently retargeting the robot.
    target_covered = problem["viewpoints_covered"][env_ids, safe_assignment]
    target_feasible = problem["feasible_mask"][env_ids, agent_ids, safe_assignment]
    valid = in_range & (~target_covered) & target_feasible

    target_pos = problem["viewpoint_pos"][env_ids, safe_assignment]
    target_quat = problem["viewpoint_quat"][env_ids, safe_assignment]
    base_to_target = target_pos - problem["base_pos"]
    scanner_delta = target_pos - problem["scanner_pos"]

    max_base_xy_step = env.max_base_xy_step.view(1, num_agents, 1).clamp(min=1e-6)
    max_base_yaw_step = env.max_base_yaw_step.view(1, num_agents).clamp(min=1e-6)
    max_ee_xyz_step = env.max_ee_xyz_step.view(1, num_agents, 1).clamp(min=1e-6)
    max_ee_rpy_step = env.max_ee_rpy_step.view(1, num_agents, 1).clamp(min=1e-6)

    # Base motion moves toward the assigned viewpoint in xy and points yaw toward the same target. This is intentionally
    # simple; it provides a deterministic bridge from discrete assignment to the existing continuous action interface.
    actions[:, :, 0:2] = torch.clamp(base_to_target[:, :, 0:2] / max_base_xy_step, -1.0, 1.0)

    target_yaw = torch.atan2(base_to_target[:, :, 1], base_to_target[:, :, 0])
    yaw_error = wrap_to_pi(target_yaw - problem["base_yaw"])
    actions[:, :, 2] = torch.clamp(yaw_error / max_base_yaw_step, -1.0, 1.0)

    # Scanner translation and orientation use the same normalized increment convention as the environment. Orientation
    # control matters because scan completion checks both pose tolerance and FOV direction.
    actions[:, :, 3:6] = torch.clamp(scanner_delta / max_ee_xyz_step, -1.0, 1.0)
    rpy_error = wrap_to_pi(_euler_xyz_from_quat(target_quat) - _euler_xyz_from_quat(problem["scanner_quat"]))
    actions[:, :, 6:9] = torch.clamp(rpy_error / max_ee_rpy_step, -1.0, 1.0)

    # No-op entries become exact zeros. The final clamp is defensive and keeps the DirectMARLEnv action contract intact
    # even if future controller terms are added.
    actions = torch.where(valid.unsqueeze(-1), actions, torch.zeros_like(actions))
    actions = torch.clamp(actions, -1.0, 1.0)

    return {agent: actions[:, index, :] for agent, index in env.agent_index.items()}
