# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from .base_solver import BaseAssignmentSolver


class NearestAssignmentSolver(BaseAssignmentSolver):
    """Assign each agent its nearest currently available viewpoint.

    The solver is deterministic for a fixed problem snapshot and agent order. It is useful as a stronger baseline than
    random selection while still being easy to inspect in the GUI viewer.
    """

    def solve(self, problem):
        # `cost_matrix[e, a, v]` is scanner-to-viewpoint distance. Infeasible, covered, or already selected viewpoints
        # are masked to +inf before taking the minimum.
        available_mask = problem["available_mask"]
        cost_matrix = problem["cost_matrix"]
        num_envs = problem["num_envs"]
        num_agents = problem["num_agents"]
        num_viewpoints = problem["num_viewpoints"]
        device = available_mask.device

        assignment = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)

        for env_id in range(num_envs):
            # Prevent duplicate targets among agents in this environment. This greedy per-agent ordering is simple and
            # deterministic, but it is not globally optimal assignment.
            selected = torch.zeros(num_viewpoints, dtype=torch.bool, device=device)
            for agent_id in range(num_agents):
                candidate_mask = available_mask[env_id, agent_id] & (~selected)
                masked_cost = cost_matrix[env_id, agent_id].masked_fill(~candidate_mask, float("inf"))
                best_cost, best_viewpoint = torch.min(masked_cost, dim=0)
                if not torch.isfinite(best_cost):
                    continue

                assignment[env_id, agent_id] = best_viewpoint
                selected[best_viewpoint] = True

        return assignment
