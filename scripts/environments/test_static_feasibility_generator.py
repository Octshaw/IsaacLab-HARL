# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_FEASIBILITY_PATH = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
    / "static_feasibility.py"
)


def _load_static_feasibility_module():
    spec = importlib.util.spec_from_file_location("scan_static_feasibility_under_test", STATIC_FEASIBILITY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec from {STATIC_FEASIBILITY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = _load_static_feasibility_module()
    result = module.generate_static_geometric_feasibility(
        viewpoint_ids=(0, 1),
        viewpoint_pos=torch.tensor(
            [
                [0.0, -1.45, 1.4],
                [0.0, -10.0, 3.5],
            ],
            dtype=torch.float32,
        ),
        viewpoint_quat=torch.tensor(
            [
                [0.7071, 0.0, 0.0, 0.7071],
                [1.0, 0.0, 0.0, 0.0],
            ],
            dtype=torch.float32,
        ),
        component_center=torch.tensor([0.0, 0.0, 1.0], dtype=torch.float32),
        component_half_extents=torch.tensor([3.0, 1.0, 1.0], dtype=torch.float32),
        agent_names=("robot_0", "robot_1", "robot_2"),
        base_start_poses=torch.tensor(
            [
                [-4.0, -3.0, 0.15, 0.0],
                [0.0, 3.2, 0.15, -1.5708],
                [4.0, -3.0, 0.15, 3.1416],
            ],
            dtype=torch.float32,
        ),
        arm_reach=torch.tensor([2.0, 3.0, 1.6], dtype=torch.float32),
        scanner_min_range=torch.tensor([0.25, 0.35, 0.20], dtype=torch.float32),
        scanner_max_range=torch.tensor([1.4, 2.0, 1.1], dtype=torch.float32),
        scanner_fov_cos=torch.cos(0.5 * torch.deg2rad(torch.tensor([65.0, 90.0, 50.0], dtype=torch.float32))),
        scanner_fov_deg=torch.tensor([65.0, 90.0, 50.0], dtype=torch.float32),
        scan_pos_tolerance=torch.tensor([0.18, 0.25, 0.15], dtype=torch.float32),
        scan_rot_tolerance=torch.tensor([0.45, 0.60, 0.40], dtype=torch.float32),
    )

    if tuple(result.feasible_mask.shape) != (3, 2):
        raise AssertionError(f"feasible_mask shape mismatch: got {tuple(result.feasible_mask.shape)}")
    if len(result.diagnostic_rows) != 6:
        raise AssertionError(f"expected 6 diagnostic rows, got {len(result.diagnostic_rows)}")
    if not bool(result.feasible_mask[:, 0].all().item()):
        raise AssertionError("viewpoint 0 should be feasible for all three sample agents")
    if bool(result.feasible_mask[:, 1].any().item()):
        raise AssertionError("viewpoint 1 should be infeasible for all three sample agents")

    missing_reason_rows = [
        row for row in result.diagnostic_rows if not row["feasible"] and not row["reason_if_false"]
    ]
    if missing_reason_rows:
        raise AssertionError(f"infeasible rows must include reason_if_false: {missing_reason_rows}")

    print("[OK] static geometric feasibility generator self-check passed")


if __name__ == "__main__":
    main()
