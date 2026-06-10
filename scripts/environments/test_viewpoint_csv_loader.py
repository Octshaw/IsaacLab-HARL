# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


parser = argparse.ArgumentParser(description="Smoke-test the scan viewpoint CSV loader.")
parser.add_argument(
    "--csv_path",
    type=str,
    default="configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv",
    help="Fixed-N viewpoint CSV path.",
)
parser.add_argument("--expect_num_viewpoints", type=int, default=None, help="Assert the loaded viewpoint count.")
args_cli = parser.parse_args()

REPO_ROOT = Path(__file__).resolve().parents[2]
VIEWPOINT_CSV_PATH = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
    / "viewpoint_csv.py"
)


def _load_viewpoint_csv_module():
    spec = importlib.util.spec_from_file_location("scan_viewpoint_csv_under_test", VIEWPOINT_CSV_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec from {VIEWPOINT_CSV_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    viewpoint_csv = _load_viewpoint_csv_module()
    result = viewpoint_csv.load_fixed_viewpoint_csv(args_cli.csv_path)
    if args_cli.expect_num_viewpoints is not None and len(result.poses) != args_cli.expect_num_viewpoints:
        raise AssertionError(
            f"num_viewpoints mismatch: expected {args_cli.expect_num_viewpoints}, got {len(result.poses)}"
        )
    expected_ids = tuple(range(len(result.poses)))
    if result.ids != expected_ids:
        raise AssertionError(f"viewpoint ids mismatch: expected {expected_ids}, got {result.ids}")
    if result.conventions != viewpoint_csv.VIEWPOINT_CSV_CONVENTIONS:
        raise AssertionError(
            f"conventions mismatch: expected {viewpoint_csv.VIEWPOINT_CSV_CONVENTIONS}, got {result.conventions}"
        )

    print(
        "[OK] viewpoint CSV loader smoke passed "
        f"format={viewpoint_csv.VIEWPOINT_CSV_FORMAT} path={result.path} "
        f"num_viewpoints={len(result.poses)} no-op id={len(result.poses)} "
        f"viewpoint_ids={list(result.ids)}"
    )


if __name__ == "__main__":
    main()
