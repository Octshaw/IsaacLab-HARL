# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class StaticGeometricFeasibilityResult:
    """Static Level 1 feasibility output for one fixed-N viewpoint set."""

    feasible_mask: torch.Tensor
    diagnostic_rows: list[dict]
    surface_distance: torch.Tensor
    range_ok: torch.Tensor
    height_reach_ok: torch.Tensor
    alignment_ok: torch.Tensor


def generate_static_geometric_feasibility(
    *,
    viewpoint_ids: tuple[int, ...],
    viewpoint_pos: torch.Tensor,
    viewpoint_quat: torch.Tensor,
    component_center: torch.Tensor,
    component_half_extents: torch.Tensor,
    agent_names: tuple[str, ...],
    base_start_poses: torch.Tensor,
    arm_reach: torch.Tensor,
    scanner_min_range: torch.Tensor,
    scanner_max_range: torch.Tensor,
    scanner_fov_cos: torch.Tensor,
    scanner_fov_deg: torch.Tensor,
    scan_pos_tolerance: torch.Tensor,
    scan_rot_tolerance: torch.Tensor,
) -> StaticGeometricFeasibilityResult:
    """Generate deterministic static geometric feasibility and per-pair diagnostics.

    This is a Level 1 geometric screen only. It intentionally avoids controller rollout,
    IK, collision, joint limits, or real articulation state.
    """

    if viewpoint_pos.ndim != 2 or viewpoint_pos.shape[-1] != 3:
        raise ValueError(f"viewpoint_pos must have shape [num_viewpoints, 3], got {tuple(viewpoint_pos.shape)}")
    if viewpoint_quat.ndim != 2 or viewpoint_quat.shape[-1] != 4:
        raise ValueError(f"viewpoint_quat must have shape [num_viewpoints, 4], got {tuple(viewpoint_quat.shape)}")

    num_viewpoints = int(viewpoint_pos.shape[0])
    num_agents = len(agent_names)
    if len(viewpoint_ids) != num_viewpoints:
        raise ValueError(f"viewpoint_ids length must be {num_viewpoints}, got {len(viewpoint_ids)}")
    if num_agents <= 0:
        raise ValueError("agent_names must not be empty")

    surface_vectors = _bbox_surface_vectors(
        viewpoint_pos,
        component_center=component_center,
        component_half_extents=component_half_extents,
    )
    surface_distance = torch.norm(surface_vectors, dim=-1)
    direction_to_surface = _normalize_with_fallback(
        surface_vectors,
        fallback=component_center.view(1, 3) - viewpoint_pos,
    )

    forward_axis = torch.tensor([1.0, 0.0, 0.0], dtype=viewpoint_pos.dtype, device=viewpoint_pos.device)
    scanner_forward = _quat_apply_wxyz(viewpoint_quat, forward_axis.expand(num_viewpoints, 3))
    scanner_forward = _normalize_with_fallback(scanner_forward, fallback=forward_axis.expand(num_viewpoints, 3))
    alignment_cos = torch.sum(scanner_forward * direction_to_surface, dim=-1).clamp(-1.0, 1.0)

    surface_distance_agent = surface_distance.view(1, num_viewpoints).expand(num_agents, num_viewpoints)
    range_min_margin = surface_distance_agent - scanner_min_range.view(num_agents, 1)
    range_max_margin = scanner_max_range.view(num_agents, 1) - surface_distance_agent
    range_margin = torch.minimum(range_min_margin, range_max_margin)
    range_ok = (range_min_margin >= -1.0e-6) & (range_max_margin >= -1.0e-6)

    base_z = base_start_poses[:, 2].view(num_agents, 1)
    vertical_reach = torch.abs(base_z - viewpoint_pos[:, 2].view(1, num_viewpoints))
    arm_margin = arm_reach.view(num_agents, 1) - vertical_reach
    height_reach_ok = arm_margin >= -1.0e-6

    alignment_cos_agent = alignment_cos.view(1, num_viewpoints).expand(num_agents, num_viewpoints)
    alignment_margin = alignment_cos_agent - scanner_fov_cos.view(num_agents, 1)
    alignment_ok = alignment_margin >= -1.0e-6

    feasible_mask = range_ok & height_reach_ok & alignment_ok
    rows = _make_diagnostic_rows(
        viewpoint_ids=viewpoint_ids,
        agent_names=agent_names,
        feasible_mask=feasible_mask,
        surface_distance=surface_distance,
        range_ok=range_ok,
        height_reach_ok=height_reach_ok,
        alignment_ok=alignment_ok,
        arm_margin=arm_margin,
        range_margin=range_margin,
        alignment_cos=alignment_cos,
        alignment_margin=alignment_margin,
        vertical_reach=vertical_reach,
        scanner_min_range=scanner_min_range,
        scanner_max_range=scanner_max_range,
        scanner_fov_deg=scanner_fov_deg,
        scan_pos_tolerance=scan_pos_tolerance,
        scan_rot_tolerance=scan_rot_tolerance,
    )

    return StaticGeometricFeasibilityResult(
        feasible_mask=feasible_mask,
        diagnostic_rows=rows,
        surface_distance=surface_distance,
        range_ok=range_ok,
        height_reach_ok=height_reach_ok,
        alignment_ok=alignment_ok,
    )


def _bbox_surface_vectors(
    viewpoint_pos: torch.Tensor,
    *,
    component_center: torch.Tensor,
    component_half_extents: torch.Tensor,
) -> torch.Tensor:
    min_corner = component_center - component_half_extents
    max_corner = component_center + component_half_extents
    nearest_point = torch.minimum(torch.maximum(viewpoint_pos, min_corner.view(1, 3)), max_corner.view(1, 3))
    return nearest_point - viewpoint_pos


def _normalize_with_fallback(vector: torch.Tensor, *, fallback: torch.Tensor) -> torch.Tensor:
    eps = 1.0e-8
    norm = torch.norm(vector, dim=-1, keepdim=True)
    fallback_norm = torch.norm(fallback, dim=-1, keepdim=True)
    normalized_fallback = torch.where(
        fallback_norm > eps,
        fallback / fallback_norm.clamp(min=eps),
        torch.zeros_like(fallback),
    )
    return torch.where(norm > eps, vector / norm.clamp(min=eps), normalized_fallback)


def _quat_apply_wxyz(quat: torch.Tensor, vector: torch.Tensor) -> torch.Tensor:
    q_vec = quat[..., 1:4]
    q_w = quat[..., 0:1]
    t = 2.0 * torch.cross(q_vec, vector, dim=-1)
    return vector + q_w * t + torch.cross(q_vec, t, dim=-1)


def _make_diagnostic_rows(
    *,
    viewpoint_ids: tuple[int, ...],
    agent_names: tuple[str, ...],
    feasible_mask: torch.Tensor,
    surface_distance: torch.Tensor,
    range_ok: torch.Tensor,
    height_reach_ok: torch.Tensor,
    alignment_ok: torch.Tensor,
    arm_margin: torch.Tensor,
    range_margin: torch.Tensor,
    alignment_cos: torch.Tensor,
    alignment_margin: torch.Tensor,
    vertical_reach: torch.Tensor,
    scanner_min_range: torch.Tensor,
    scanner_max_range: torch.Tensor,
    scanner_fov_deg: torch.Tensor,
    scan_pos_tolerance: torch.Tensor,
    scan_rot_tolerance: torch.Tensor,
) -> list[dict]:
    rows = []
    feasible_cpu = feasible_mask.detach().cpu()
    range_ok_cpu = range_ok.detach().cpu()
    height_ok_cpu = height_reach_ok.detach().cpu()
    alignment_ok_cpu = alignment_ok.detach().cpu()
    for agent_index, agent_name in enumerate(agent_names):
        for viewpoint_index, viewpoint_id in enumerate(viewpoint_ids):
            reasons = []
            if not bool(range_ok_cpu[agent_index, viewpoint_index].item()):
                reasons.append("surface_distance_outside_sensor_range")
            if not bool(height_ok_cpu[agent_index, viewpoint_index].item()):
                reasons.append("viewpoint_height_outside_arm_reach")
            if not bool(alignment_ok_cpu[agent_index, viewpoint_index].item()):
                reasons.append("scanner_forward_axis_not_aligned_with_bbox_surface")

            feasible = bool(feasible_cpu[agent_index, viewpoint_index].item())
            rows.append(
                {
                    "viewpoint_id": int(viewpoint_id),
                    "viewpoint_index": int(viewpoint_index),
                    "agent": str(agent_name),
                    "agent_index": int(agent_index),
                    "feasible": feasible,
                    "surface_distance": _to_float(surface_distance[viewpoint_index]),
                    "range_ok": bool(range_ok_cpu[agent_index, viewpoint_index].item()),
                    "height_reach_ok": bool(height_ok_cpu[agent_index, viewpoint_index].item()),
                    "arm_margin": _to_float(arm_margin[agent_index, viewpoint_index]),
                    "reach_margin": _to_float(arm_margin[agent_index, viewpoint_index]),
                    "range_margin": _to_float(range_margin[agent_index, viewpoint_index]),
                    "fov_possible": bool(alignment_ok_cpu[agent_index, viewpoint_index].item()),
                    "alignment_ok": bool(alignment_ok_cpu[agent_index, viewpoint_index].item()),
                    "alignment_cos": _to_float(alignment_cos[viewpoint_index]),
                    "alignment_margin": _to_float(alignment_margin[agent_index, viewpoint_index]),
                    "vertical_reach": _to_float(vertical_reach[agent_index, viewpoint_index]),
                    "scanner_min_range": _to_float(scanner_min_range[agent_index]),
                    "scanner_max_range": _to_float(scanner_max_range[agent_index]),
                    "scanner_fov_deg": _to_float(scanner_fov_deg[agent_index]),
                    "scan_pos_tolerance": _to_float(scan_pos_tolerance[agent_index]),
                    "scan_rot_tolerance": _to_float(scan_rot_tolerance[agent_index]),
                    "reason_if_false": "" if feasible else ";".join(reasons),
                    "source": "static_geometric_v1",
                }
            )
    return rows


def _to_float(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())
