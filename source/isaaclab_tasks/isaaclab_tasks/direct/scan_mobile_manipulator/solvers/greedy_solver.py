# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from .base_solver import BaseAssignmentSolver


class GreedyAssignmentSolver(BaseAssignmentSolver):
    """Greedily assign each agent the highest score available viewpoint.

    The current score is inverse distance, so this behaves similarly to nearest assignment but keeps the scoring step
    explicit. Future variants can add coverage value, robot capability, route balance, or priority weights here without
    changing the solver interface.
    """

    def solve(self, problem):
        # `available_mask` gates all invalid choices. The inverse-distance score is only evaluated for readability; the
        # mask will set disallowed choices to -inf before selecting the maximum.
        available_mask = problem["available_mask"]
        cost_matrix = problem["cost_matrix"]
        num_envs = problem["num_envs"]
        num_agents = problem["num_agents"]
        num_viewpoints = problem["num_viewpoints"]
        device = available_mask.device

        assignment = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)
        score = 1.0 / (cost_matrix + 1.0e-6)

        for env_id in range(num_envs):
            # Greedy selection is done in fixed agent order. It avoids duplicates within a single env step, but does not
            # solve the full Hungarian/global assignment problem.
            selected = torch.zeros(num_viewpoints, dtype=torch.bool, device=device)
            for agent_id in range(num_agents):
                candidate_mask = available_mask[env_id, agent_id] & (~selected)
                masked_score = score[env_id, agent_id].masked_fill(~candidate_mask, -float("inf"))
                best_score, best_viewpoint = torch.max(masked_score, dim=0)
                if not torch.isfinite(best_score):
                    continue

                assignment[env_id, agent_id] = best_viewpoint
                selected[best_viewpoint] = True

        return assignment
