# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from .base_solver import BaseAssignmentSolver
from .conflict_aware_solver import ConflictAwareAssignmentSolver
from .greedy_solver import GreedyAssignmentSolver
from .nearest_solver import NearestAssignmentSolver
from .random_solver import RandomAssignmentSolver


def make_solver(name: str):
    """Create a viewpoint assignment solver by name.

    Viewer/evaluation scripts use this tiny factory so command-line solver names stay decoupled from concrete classes.
    Keep the accepted names synchronized with script argparse choices when adding new solvers.
    """
    name = name.lower()
    if name == "random":
        return RandomAssignmentSolver()
    if name == "nearest":
        return NearestAssignmentSolver()
    if name == "greedy":
        return GreedyAssignmentSolver()
    if name == "nearest_conflict_aware":
        return ConflictAwareAssignmentSolver(method_name="nearest_conflict_aware", base_method="nearest")
    if name == "greedy_conflict_aware":
        return ConflictAwareAssignmentSolver(method_name="greedy_conflict_aware", base_method="greedy")
    raise ValueError(f"Unknown solver: {name}")


__all__ = [
    "BaseAssignmentSolver",
    "ConflictAwareAssignmentSolver",
    "GreedyAssignmentSolver",
    "NearestAssignmentSolver",
    "RandomAssignmentSolver",
    "make_solver",
]
