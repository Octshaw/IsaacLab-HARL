# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VIEWPOINT_CSV_FORMAT = "scanner_pose_world_quat_wxyz_v1"

VIEWPOINT_CSV_COLUMNS = (
    "id",
    "pose_type",
    "coordinate_frame",
    "units",
    "quaternion_order",
    "scanner_forward_axis",
    "scanner_up_axis",
    "viewpoint_quaternion_meaning",
    "x",
    "y",
    "z",
    "qw",
    "qx",
    "qy",
    "qz",
)

VIEWPOINT_CSV_CONVENTIONS = {
    "pose_type": "scanner_pose_in_world",
    "coordinate_frame": "world",
    "units": "meters",
    "quaternion_order": "qw,qx,qy,qz",
    "scanner_forward_axis": "+X",
    "scanner_up_axis": "+Z",
    "viewpoint_quaternion_meaning": "scanner_frame_orientation_in_world",
}


@dataclass(frozen=True)
class ViewpointCsvLoadResult:
    """Loaded fixed-N viewpoint poses in internal [x, y, z, qw, qx, qy, qz] format."""

    path: Path
    ids: tuple[int, ...]
    poses: tuple[tuple[float, float, float, float, float, float, float], ...]
    conventions: dict[str, str]


def load_fixed_viewpoint_csv(
    csv_path: str | Path,
    *,
    search_roots: Iterable[str | Path] | None = None,
) -> ViewpointCsvLoadResult:
    """Load the single supported fixed-N viewpoint CSV format.

    The format is intentionally strict. Each row repeats all frame and quaternion
    conventions so experiments fail early if a file is ambiguous.
    """

    path = _resolve_csv_path(csv_path, search_roots=search_roots)
    if not path.exists():
        raise FileNotFoundError(f"Viewpoint CSV file does not exist: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        if fieldnames != VIEWPOINT_CSV_COLUMNS:
            raise ValueError(
                "Unsupported viewpoint CSV format. Expected columns exactly "
                f"{VIEWPOINT_CSV_COLUMNS}, got {fieldnames}. "
                f"Supported format is {VIEWPOINT_CSV_FORMAT}."
            )
        rows = list(reader)

    if not rows:
        raise ValueError(f"Viewpoint CSV file is empty: {path}")

    ids: list[int] = []
    poses: list[tuple[float, float, float, float, float, float, float]] = []
    for row_index, row in enumerate(rows, start=2):
        _validate_conventions(row, path=path, row_index=row_index)
        viewpoint_id = _parse_viewpoint_id(row["id"], path=path, row_index=row_index)
        expected_id = len(ids)
        if viewpoint_id != expected_id:
            raise ValueError(
                f"{path}:{row_index}: viewpoint ids must be contiguous, zero-based, and in file order; "
                f"expected id {expected_id}, got {viewpoint_id}."
            )
        pose = (
            _parse_float(row["x"], "x", path=path, row_index=row_index),
            _parse_float(row["y"], "y", path=path, row_index=row_index),
            _parse_float(row["z"], "z", path=path, row_index=row_index),
            _parse_float(row["qw"], "qw", path=path, row_index=row_index),
            _parse_float(row["qx"], "qx", path=path, row_index=row_index),
            _parse_float(row["qy"], "qy", path=path, row_index=row_index),
            _parse_float(row["qz"], "qz", path=path, row_index=row_index),
        )
        _validate_unit_quaternion(pose[3:7], path=path, row_index=row_index)
        ids.append(viewpoint_id)
        poses.append(pose)

    return ViewpointCsvLoadResult(
        path=path,
        ids=tuple(ids),
        poses=tuple(poses),
        conventions=dict(VIEWPOINT_CSV_CONVENTIONS),
    )


def _resolve_csv_path(
    csv_path: str | Path,
    *,
    search_roots: Iterable[str | Path] | None,
) -> Path:
    raw_path = Path(csv_path).expanduser()
    if raw_path.is_absolute():
        return raw_path

    roots = [Path.cwd(), Path(__file__).resolve().parent]
    if search_roots is not None:
        roots = [Path(root).expanduser() for root in search_roots] + roots

    for root in roots:
        candidate = (root / raw_path).resolve()
        if candidate.exists():
            return candidate
    return (Path.cwd() / raw_path).resolve()


def _validate_conventions(row: dict[str, str], *, path: Path, row_index: int) -> None:
    for key, expected_value in VIEWPOINT_CSV_CONVENTIONS.items():
        actual_value = (row.get(key) or "").strip()
        if actual_value != expected_value:
            label = key.replace("_", " ")
            raise ValueError(
                f"{path}:{row_index}: invalid {label}. Expected {key}={expected_value!r}, "
                f"got {actual_value!r}. The loader does not guess viewpoint file conventions."
            )


def _parse_viewpoint_id(value: str, *, path: Path, row_index: int) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{path}:{row_index}: id must be an integer, got {value!r}.") from exc


def _parse_float(value: str, name: str, *, path: Path, row_index: int) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{path}:{row_index}: {name} must be a finite float, got {value!r}.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{path}:{row_index}: {name} must be finite, got {value!r}.")
    return number


def _validate_unit_quaternion(quat: tuple[float, float, float, float], *, path: Path, row_index: int) -> None:
    norm = math.sqrt(sum(value * value for value in quat))
    if norm <= 1.0e-8:
        raise ValueError(f"{path}:{row_index}: quaternion must be non-zero.")
    if abs(norm - 1.0) > 1.0e-3:
        raise ValueError(
            f"{path}:{row_index}: quaternion must be unit length in qw,qx,qy,qz order; got norm {norm:.6f}."
        )
