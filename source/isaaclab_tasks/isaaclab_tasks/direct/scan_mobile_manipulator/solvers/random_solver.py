# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from .base_solver import BaseAssignmentSolver


class RandomAssignmentSolver(BaseAssignmentSolver):
    """Randomly select available viewpoints while avoiding duplicates within each environment.

    This is mainly a sanity-check baseline: it verifies that assignment masks, controller conversion, and environment
    stepping work even when the target choice itself is not optimized.
    """

    def solve(self, problem):
        # `available_mask[e, a, v]` already includes feasibility and uncovered-viewpoint checks. The solver only needs
        # to avoid assigning the same viewpoint to two agents in the same environment step.
        available_mask = problem["available_mask"]
        num_envs = problem["num_envs"]
        num_agents = problem["num_agents"]
        num_viewpoints = problem["num_viewpoints"]
        device = available_mask.device

        assignment = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)

        for env_id in range(num_envs):
            # Track viewpoints claimed by earlier agents in this vectorized environment. This is local to one env and is
            # reset for the next env_id.
            selected = torch.zeros(num_viewpoints, dtype=torch.bool, device=device)
            for agent_id in range(num_agents):
                candidate_mask = available_mask[env_id, agent_id] & (~selected)
                candidates = torch.nonzero(candidate_mask, as_tuple=False).flatten()
                if candidates.numel() == 0:
                    continue

                choice = candidates[torch.randint(candidates.numel(), (1,), device=device)]
                assignment[env_id, agent_id] = choice
                selected[choice] = True

        return assignment
