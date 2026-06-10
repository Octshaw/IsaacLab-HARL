"""Generate a strict world-frame viewpoint CSV around an auto bbox component proxy."""

from __future__ import annotations

import argparse
import csv
import json
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

from component_mesh import (  # noqa: E402
    Vector3,
    compute_base_center_alignment_translation,
    compute_component_mesh_bounds,
)
from scenario_config import (  # noqa: E402
    load_scenario_config,
    validate_generation_args,
    viewpoint_generation_defaults_from_config,
)
from viewpoint_csv import VIEWPOINT_CSV_COLUMNS, VIEWPOINT_CSV_CONVENTIONS, VIEWPOINT_CSV_FORMAT  # noqa: E402


QuatWxyz = tuple[float, float, float, float]


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean value, got {value!r}")


def _linspace(start: float, stop: float, count: int) -> list[float]:
    if count <= 0:
        raise ValueError("count must be positive")
    if count == 1:
        return [(start + stop) * 0.5]
    step = (stop - start) / float(count - 1)
    return [start + step * index for index in range(count)]


def _normalize(vector: Vector3, *, label: str) -> Vector3:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1.0e-10:
        raise ValueError(f"{label} must be non-zero.")
    return (vector[0] / norm, vector[1] / norm, vector[2] / norm)


def _dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul_scalar(a: Vector3, value: float) -> Vector3:
    return (a[0] * value, a[1] * value, a[2] * value)


def _matrix_columns_to_quat_wxyz(x_axis: Vector3, y_axis: Vector3, z_axis: Vector3) -> QuatWxyz:
    m00, m01, m02 = x_axis[0], y_axis[0], z_axis[0]
    m10, m11, m12 = x_axis[1], y_axis[1], z_axis[1]
    m20, m21, m22 = x_axis[2], y_axis[2], z_axis[2]
    trace = m00 + m11 + m22
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (m21 - m12) / s
        qy = (m02 - m20) / s
        qz = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        qw = (m21 - m12) / s
        qx = 0.25 * s
        qy = (m01 + m10) / s
        qz = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        qw = (m02 - m20) / s
        qx = (m01 + m10) / s
        qy = 0.25 * s
        qz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        qw = (m10 - m01) / s
        qx = (m02 + m20) / s
        qy = (m12 + m21) / s
        qz = 0.25 * s

    quat = (qw, qx, qy, qz)
    norm = math.sqrt(sum(value * value for value in quat))
    if norm <= 1.0e-10:
        raise ValueError("look-at quaternion must be non-zero.")
    quat = tuple(value / norm for value in quat)  # type: ignore[assignment]
    if not all(math.isfinite(value) for value in quat):
        raise ValueError(f"look-at quaternion contains non-finite values: {quat!r}")
    return quat  # type: ignore[return-value]


def _look_at_quat_wxyz(scanner_position: Vector3, target_position: Vector3) -> tuple[QuatWxyz, bool]:
    forward = _normalize(_subtract(target_position, scanner_position), label="look direction")
    world_up = (0.0, 0.0, 1.0)
    up_projection = _subtract(world_up, _mul_scalar(forward, _dot(world_up, forward)))
    used_fallback = False
    if math.sqrt(_dot(up_projection, up_projection)) <= 1.0e-8:
        fallback_up = (0.0, 1.0, 0.0)
        up_projection = _subtract(fallback_up, _mul_scalar(forward, _dot(fallback_up, forward)))
        used_fallback = True
    up_axis = _normalize(up_projection, label="scanner up projection")
    y_axis = _normalize(_cross(up_axis, forward), label="scanner y axis")
    up_axis = _normalize(_cross(forward, y_axis), label="scanner z axis")
    quat = _matrix_columns_to_quat_wxyz(forward, y_axis, up_axis)
    norm = math.sqrt(sum(value * value for value in quat))
    if abs(norm - 1.0) > 1.0e-6:
        raise ValueError(f"look-at quaternion must be unit length; got norm {norm:.12f}")
    return quat, used_fallback


def _format_float(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError(f"CSV value must be finite, got {value!r}")
    if abs(value) <= 1.0e-12:
        value = 0.0
    return f"{value:.10g}"


def _generate_viewpoint_rows(
    *,
    bbox_min: Vector3,
    bbox_max: Vector3,
    viewpoint_distance: float,
    num_height_layers: int,
    points_per_side: int,
) -> tuple[list[dict[str, str]], int]:
    if viewpoint_distance <= 0.0 or not math.isfinite(viewpoint_distance):
        raise ValueError(f"--viewpoint_distance must be finite and positive, got {viewpoint_distance!r}")
    if num_height_layers <= 0:
        raise ValueError("--num_height_layers must be positive")
    if points_per_side <= 0:
        raise ValueError("--points_per_side must be positive")

    x_values = _linspace(bbox_min[0], bbox_max[0], points_per_side)
    y_values = _linspace(bbox_min[1], bbox_max[1], points_per_side)
    height_step = (bbox_max[2] - bbox_min[2]) / float(num_height_layers + 1)
    z_values = [bbox_min[2] + height_step * (index + 1) for index in range(num_height_layers)]

    rows: list[dict[str, str]] = []
    fallback_count = 0
    for z_value in z_values:
        for y_value in y_values:
            position = (bbox_max[0] + viewpoint_distance, y_value, z_value)
            target = (bbox_max[0], y_value, z_value)
            fallback_count += _append_viewpoint_row(rows, position, target)
        for y_value in y_values:
            position = (bbox_min[0] - viewpoint_distance, y_value, z_value)
            target = (bbox_min[0], y_value, z_value)
            fallback_count += _append_viewpoint_row(rows, position, target)
        for x_value in x_values:
            position = (x_value, bbox_max[1] + viewpoint_distance, z_value)
            target = (x_value, bbox_max[1], z_value)
            fallback_count += _append_viewpoint_row(rows, position, target)
        for x_value in x_values:
            position = (x_value, bbox_min[1] - viewpoint_distance, z_value)
            target = (x_value, bbox_min[1], z_value)
            fallback_count += _append_viewpoint_row(rows, position, target)

    return rows, fallback_count


def _append_viewpoint_row(rows: list[dict[str, str]], position: Vector3, target: Vector3) -> int:
    quat, used_fallback = _look_at_quat_wxyz(position, target)
    row = {
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
    rows.append(row)
    return 1 if used_fallback else 0


def _write_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=VIEWPOINT_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
    pre_args, _ = pre_parser.parse_known_args()
    scenario_config = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
    scenario_defaults = viewpoint_generation_defaults_from_config(scenario_config)

    parser = argparse.ArgumentParser(
        description="Generate a strict bbox-based viewpoint CSV for smoke testing.",
        parents=[pre_parser],
    )
    parser.add_argument("--mesh_path", default=None)
    parser.add_argument("--mesh_format", default="obj")
    parser.add_argument("--mesh_unit", default="mm")
    parser.add_argument("--mesh_scale", nargs=3, type=float, default=(0.001, 0.001, 0.001))
    parser.add_argument("--mesh_position", nargs=3, type=float, default=None)
    parser.add_argument("--mesh_orientation", nargs=4, type=float, default=(1.0, 0.0, 0.0, 0.0))
    parser.add_argument("--mesh_orientation_format", default="qwxyz")
    parser.add_argument(
        "--component_proxy_auto_from_mesh",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Accepted for consistency with env CLI; this generator always uses the auto mesh bbox.",
    )
    parser.add_argument("--component_proxy_padding", type=float, default=0.0)
    parser.add_argument(
        "--align_base_center_to_world_origin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Set mesh translation so the scaled/rotated mesh base center is at world origin.",
    )
    parser.add_argument("--output_csv", default=None)
    parser.add_argument("--output_json", default=None)
    parser.add_argument("--viewpoint_distance", type=float, default=0.8)
    parser.add_argument("--num_height_layers", type=int, default=2)
    parser.add_argument("--points_per_side", type=int, default=3)
    parser.add_argument("--include_top", nargs="?", const=True, default=False, type=_parse_bool)
    parser.set_defaults(**scenario_defaults)
    args = parser.parse_args()
    validate_generation_args(args, repo_root=REPO_ROOT)

    if args.include_top:
        raise ValueError("--include_top true is not supported in this smoke generator yet; pass --include_top false.")
    if args.align_base_center_to_world_origin and args.mesh_position is not None:
        raise ValueError(
            "--align_base_center_to_world_origin cannot be combined with --mesh_position. "
            "Use one world-origin convention at a time."
        )

    alignment = None
    mesh_position = tuple(args.mesh_position) if args.mesh_position is not None else (0.0, 0.0, 0.0)
    if args.align_base_center_to_world_origin:
        alignment = compute_base_center_alignment_translation(
            mesh_path=args.mesh_path,
            mesh_format=args.mesh_format,
            mesh_unit=args.mesh_unit,
            mesh_scale=args.mesh_scale,
            mesh_orientation=args.mesh_orientation,
            mesh_orientation_format=args.mesh_orientation_format,
            search_roots=(REPO_ROOT,),
        )
        mesh_position = alignment.auto_translation

    bounds = compute_component_mesh_bounds(
        mesh_path=args.mesh_path,
        mesh_format=args.mesh_format,
        mesh_unit=args.mesh_unit,
        mesh_scale=args.mesh_scale,
        mesh_position=mesh_position,
        mesh_orientation=args.mesh_orientation,
        mesh_orientation_format=args.mesh_orientation_format,
        component_proxy_padding=args.component_proxy_padding,
        search_roots=(REPO_ROOT,),
    )

    rows, fallback_count = _generate_viewpoint_rows(
        bbox_min=bounds.world_bounds_m_min,
        bbox_max=bounds.world_bounds_m_max,
        viewpoint_distance=args.viewpoint_distance,
        num_height_layers=args.num_height_layers,
        points_per_side=args.points_per_side,
    )
    output_csv = Path(args.output_csv)
    _write_csv(output_csv, rows)

    report = {
        "mesh_path": bounds.mesh_path,
        "mesh_format": bounds.mesh_format,
        "mesh_unit": bounds.mesh_unit,
        "mesh_scale": list(bounds.mesh_scale),
        "mesh_position": list(bounds.mesh_position),
        "mesh_orientation": list(bounds.mesh_orientation),
        "mesh_orientation_format": args.mesh_orientation_format,
        "component_proxy_auto_from_mesh": True,
        "component_proxy_padding": float(args.component_proxy_padding),
        "align_base_center_to_world_origin": bool(args.align_base_center_to_world_origin),
        "world_origin_convention": (
            "model_base_center" if args.align_base_center_to_world_origin else "explicit_mesh_position"
        ),
        "base_center_before_translation": (
            list(alignment.base_center_before_translation) if alignment is not None else None
        ),
        "auto_translation_if_used": list(alignment.auto_translation) if alignment is not None else None,
        "bbox_min": list(bounds.world_bounds_m_min),
        "bbox_max": list(bounds.world_bounds_m_max),
        "bbox_center": list(bounds.auto_component_proxy_center),
        "bbox_half_extents": list(bounds.auto_component_proxy_half_extents),
        "raw_bounds_obj_units_min": list(bounds.raw_bounds_obj_units_min),
        "raw_bounds_obj_units_max": list(bounds.raw_bounds_obj_units_max),
        "scaled_local_bounds_m_min": list(bounds.scaled_local_bounds_m_min),
        "scaled_local_bounds_m_max": list(bounds.scaled_local_bounds_m_max),
        "viewpoint_distance": float(args.viewpoint_distance),
        "num_height_layers": int(args.num_height_layers),
        "points_per_side": int(args.points_per_side),
        "include_top": bool(args.include_top),
        "generated_num_viewpoints": len(rows),
        "look_at_fallback_up_count": fallback_count,
        "csv_format": VIEWPOINT_CSV_FORMAT,
        "output_csv": str(output_csv),
    }

    if args.output_json is not None:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[INFO]: Generated bbox viewpoint CSV")
    print(f"[INFO]: mesh_path={bounds.mesh_path}")
    print(
        "[INFO]: mesh_transform "
        f"unit={bounds.mesh_unit} scale={bounds.mesh_scale} position={bounds.mesh_position} "
        f"orientation={bounds.mesh_orientation}"
    )
    print(f"[INFO]: world_origin_convention={report['world_origin_convention']}")
    if alignment is not None:
        print(
            "[INFO]: base-center alignment "
            f"base_center_before_translation={alignment.base_center_before_translation} "
            f"auto_translation={alignment.auto_translation}"
        )
    print(
        "[INFO]: auto bbox "
        f"center={bounds.auto_component_proxy_center} half_extents={bounds.auto_component_proxy_half_extents} "
        f"min={bounds.world_bounds_m_min} max={bounds.world_bounds_m_max}"
    )
    print(
        "[INFO]: viewpoints "
        f"count={len(rows)} distance={args.viewpoint_distance} height_layers={args.num_height_layers} "
        f"points_per_side={args.points_per_side} look_at_fallback_up_count={fallback_count}"
    )
    print(f"[OK] wrote {output_csv}")


if __name__ == "__main__":
    main()
