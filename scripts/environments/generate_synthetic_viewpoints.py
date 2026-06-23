"""Generate deterministic synthetic viewpoint CSVs for interface smoke validation."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from viewpoint_csv import VIEWPOINT_CSV_COLUMNS, VIEWPOINT_CSV_CONVENTIONS, VIEWPOINT_CSV_FORMAT  # noqa: E402


SIDE_ORDER = ("+x", "-x", "+y", "-y")
SIDE_QUAT_WXYZ = {
    "+x": (0.0, 0.0, 0.0, 1.0),
    "-x": (1.0, 0.0, 0.0, 0.0),
    "+y": (math.sqrt(0.5), 0.0, 0.0, -math.sqrt(0.5)),
    "-y": (math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5)),
}


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise argparse.ArgumentTypeError(f"expected a positive finite float, got {value!r}")
    return number


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError(f"expected a finite float, got {value!r}")
    return number


def _linspace(start: float, stop: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("count must be positive")
    if count == 1:
        return [(start + stop) * 0.5]
    step = (stop - start) / float(count - 1)
    return [start + step * index for index in range(count)]


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError(f"CSV value must be finite, got {value!r}")
    if abs(value) <= 1.0e-12:
        value = 0.0
    return f"{value:.10g}"


def _side_counts(num_viewpoints: int) -> dict[str, int]:
    base_count = num_viewpoints // len(SIDE_ORDER)
    remainder = num_viewpoints % len(SIDE_ORDER)
    return {
        side: base_count + (1 if side_index < remainder else 0)
        for side_index, side in enumerate(SIDE_ORDER)
    }


def _positions_for_side(
    *,
    side: str,
    count: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
    surface_distance: float,
) -> list[tuple[float, float, float]]:
    if count <= 0:
        return []
    layers = max(1, math.ceil(math.sqrt(count)))
    columns = max(1, math.ceil(count / layers))
    z_values = _linspace(z_min, z_max, layers)

    if side in {"+x", "-x"}:
        u_values = _linspace(y_min, y_max, columns)
    else:
        u_values = _linspace(x_min, x_max, columns)

    positions: list[tuple[float, float, float]] = []
    for index in range(count):
        layer = index // columns
        column = index % columns
        z_value = z_values[layer]
        u_value = u_values[column]
        if side == "+x":
            positions.append((x_max + surface_distance, u_value, z_value))
        elif side == "-x":
            positions.append((x_min - surface_distance, u_value, z_value))
        elif side == "+y":
            positions.append((u_value, y_max + surface_distance, z_value))
        elif side == "-y":
            positions.append((u_value, y_min - surface_distance, z_value))
        else:
            raise ValueError(f"unknown side {side!r}")
    return positions


def _make_rows(
    *,
    num_viewpoints: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
    surface_distance: float,
) -> list[dict[str, str]]:
    if x_min >= x_max:
        raise ValueError(f"x_min must be < x_max, got {x_min} >= {x_max}")
    if y_min >= y_max:
        raise ValueError(f"y_min must be < y_max, got {y_min} >= {y_max}")
    if z_min > z_max:
        raise ValueError(f"z_min must be <= z_max, got {z_min} > {z_max}")

    rows: list[dict[str, str]] = []
    for side, count in _side_counts(num_viewpoints).items():
        quat = SIDE_QUAT_WXYZ[side]
        for position in _positions_for_side(
            side=side,
            count=count,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            z_min=z_min,
            z_max=z_max,
            surface_distance=surface_distance,
        ):
            rows.append(
                {
                    "id": str(len(rows)),
                    **VIEWPOINT_CSV_CONVENTIONS,
                    "x": _format_float(position[0]),
                    "y": _format_float(position[1]),
                    "z": _format_float(position[2]),
                    "qw": _format_float(quat[0]),
                    "qx": _format_float(quat[1]),
                    "qy": _format_float(quat[2]),
                    "qz": _format_float(quat[3]),
                }
            )
    if len(rows) != num_viewpoints:
        raise RuntimeError(f"internal generation mismatch: expected {num_viewpoints}, generated {len(rows)}")
    return rows


def _write_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=VIEWPOINT_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate exact-N synthetic smoke viewpoint CSVs around the default bbox proxy."
    )
    parser.add_argument("--num_viewpoints", type=_positive_int, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--x_min", type=_finite_float, default=-3.0)
    parser.add_argument("--x_max", type=_finite_float, default=3.0)
    parser.add_argument("--y_min", type=_finite_float, default=-1.0)
    parser.add_argument("--y_max", type=_finite_float, default=1.0)
    parser.add_argument("--z_min", type=_finite_float, default=0.75)
    parser.add_argument("--z_max", type=_finite_float, default=1.55)
    parser.add_argument("--surface_distance", type=_positive_float, default=0.8)
    args = parser.parse_args()

    rows = _make_rows(
        num_viewpoints=args.num_viewpoints,
        x_min=args.x_min,
        x_max=args.x_max,
        y_min=args.y_min,
        y_max=args.y_max,
        z_min=args.z_min,
        z_max=args.z_max,
        surface_distance=args.surface_distance,
    )
    output = Path(args.output)
    _write_csv(output, rows)
    print(
        "[OK] generated synthetic smoke viewpoints "
        f"format={VIEWPOINT_CSV_FORMAT} num_viewpoints={len(rows)} output={output}"
    )


if __name__ == "__main__":
    main()
