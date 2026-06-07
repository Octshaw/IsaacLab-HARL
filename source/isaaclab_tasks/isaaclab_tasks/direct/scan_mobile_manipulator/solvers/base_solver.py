# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


class BaseAssignmentSolver:
    """Base interface for high-level viewpoint assignment solvers.

    Solvers consume the dictionary returned by `ScanMobileManipulatorEnv.get_assignment_problem()` and return a
    `torch.long` tensor with shape [num_envs, num_agents]. They do not call `env.step()` and should not mutate the
    environment state; this keeps assignment algorithms interchangeable and easy to evaluate headlessly.
    """

    def reset(self):
        """Reset any internal solver state.

        The bundled baseline solvers are stateless, but the hook is useful for future solvers that maintain a task queue,
        route history, or learned recurrent state across environment steps.
        """
        pass

    def solve(self, problem):
        """Return a viewpoint assignment tensor with shape ``[num_envs, num_agents]``.

        Each entry is a viewpoint id, or ``-1`` for no-op. Returned tensors should stay on the same device as
        `problem["available_mask"]` so the scripted controller can consume them without extra transfers.
        """
        raise NotImplementedError
