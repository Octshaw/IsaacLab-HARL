"""Generate irregular viewpoint CSVs from sampled OBJ mesh surface points."""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


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
    load_obj_mesh,
    transform_vertices,
    validate_mesh_format,
    validate_mesh_unit,
    validate_orientation_format,
)
from scenario_config import (  # noqa: E402
    load_scenario_config,
    mesh_bounds_defaults_from_config,
    validate_generation_args,
)
from viewpoint_csv import VIEWPOINT_CSV_COLUMNS, VIEWPOINT_CSV_CONVENTIONS, VIEWPOINT_CSV_FORMAT  # noqa: E402


QuatWxyz = tuple[float, float, float, float]


@dataclass(frozen=True)
class MeshTriangle:
    v0: Vector3
    v1: Vector3
    v2: Vector3
    normal: Vector3
    area: float


@dataclass(frozen=True)
class GeneratedViewpoint:
    row: dict[str, str]
    position: Vector3
    target: Vector3
    direction: Vector3
    sampled_distance: float
    side: str | None


def _put(defaults: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        defaults[key] = value


def _mapping(value: Any, label: str, *, required: bool = False) -> Mapping[str, Any]:
    if value is None:
        if required:
            raise ValueError(f"scenario_config requires a {label} mapping.")
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"scenario_config {label} must be a mapping, got {type(value).__name__}.")
    return value


def _mesh_viewpoint_generation_defaults_from_config(config: Mapping[str, Any]) -> dict[str, Any]:
    defaults = mesh_bounds_defaults_from_config(config)
    generation = _mapping(config.get("viewpoint_generation"), "viewpoint_generation", required=False)
    mesh_generation = _mapping(
        config.get("mesh_viewpoint_generation"),
        "mesh_viewpoint_generation",
        required=False,
    )

    # Reuse the generic viewpoint distance key when a bbox-generation config is
    # being adapted, then let mesh-specific settings override it.
    _put(defaults, "viewpoint_distance", generation.get("viewpoint_distance"))
    for key in (
        "num_viewpoints",
        "placement_mode",
        "sampling_mode",
        "viewpoint_distance",
        "distance_jitter",
        "surface_jitter",
        "normal_jitter_deg",
        "min_spacing",
        "seed",
        "normal_mode",
        "min_z",
        "max_z",
        "max_attempts_multiplier",
    ):
        _put(defaults, key, mesh_generation.get(key))

    proxy = _mapping(config.get("component_proxy"), "component_proxy", required=False)
    _put(defaults, "component_proxy_center", proxy.get("center"))
    _put(defaults, "component_proxy_half_extents", proxy.get("half_extents"))

    output = _mapping(config.get("output"), "output", required=False)
    _put(defaults, "output_csv", output.get("csv_path") or output.get("output_csv"))
    _put(defaults, "output_json", output.get("json_path") or output.get("output_json"))
    return defaults


def _normalize(vector: Vector3, *, label: str) -> Vector3:
    norm = math.sqrt(_dot(vector, vector))
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


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _subtract(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul_scalar(a: Vector3, value: float) -> Vector3:
    return (a[0] * value, a[1] * value, a[2] * value)


def _distance_squared(a: Vector3, b: Vector3) -> float:
    delta = _subtract(a, b)
    return _dot(delta, delta)


def _bounds(vertices: Sequence[Vector3]) -> tuple[Vector3, Vector3]:
    if not vertices:
        raise ValueError("Cannot compute bounds for an empty vertex set.")
    min_corner = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    max_corner = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
    return min_corner, max_corner


def _center_from_bounds(bounds_min: Vector3, bounds_max: Vector3) -> Vector3:
    return tuple((bounds_min[axis] + bounds_max[axis]) * 0.5 for axis in range(3))  # type: ignore[return-value]


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


def _as_vector3(value: Sequence[float], *, label: str) -> Vector3:
    try:
        vector = tuple(float(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"{label} must be a sequence of 3 finite floats, got {value!r}.") from exc
    if len(vector) != 3:
        raise ValueError(f"{label} must contain 3 values, got {len(vector)}: {value!r}.")
    if not all(math.isfinite(item) for item in vector):
        raise ValueError(f"{label} must contain finite values, got {value!r}.")
    return vector  # type: ignore[return-value]


def _build_mesh_triangles(world_vertices: Sequence[Vector3], faces: Sequence[Sequence[int]]) -> list[MeshTriangle]:
    triangles: list[MeshTriangle] = []
    for face in faces:
        if len(face) < 3:
            continue
        anchor = world_vertices[face[0]]
        for index in range(1, len(face) - 1):
            v1 = world_vertices[face[index]]
            v2 = world_vertices[face[index + 1]]
            normal_unnormalized = _cross(_subtract(v1, anchor), _subtract(v2, anchor))
            normal_length = math.sqrt(_dot(normal_unnormalized, normal_unnormalized))
            if normal_length <= 1.0e-12:
                continue
            area = 0.5 * normal_length
            normal = _mul_scalar(normal_unnormalized, 1.0 / normal_length)
            triangles.append(MeshTriangle(v0=anchor, v1=v1, v2=v2, normal=normal, area=area))
    if not triangles:
        raise ValueError("OBJ mesh has no non-degenerate triangles after fan triangulation.")
    return triangles


def _sample_triangle_point(triangle: MeshTriangle, rng: random.Random) -> Vector3:
    sqrt_r1 = math.sqrt(rng.random())
    r2 = rng.random()
    weight0 = 1.0 - sqrt_r1
    weight1 = sqrt_r1 * (1.0 - r2)
    weight2 = sqrt_r1 * r2
    return (
        triangle.v0[0] * weight0 + triangle.v1[0] * weight1 + triangle.v2[0] * weight2,
        triangle.v0[1] * weight0 + triangle.v1[1] * weight1 + triangle.v2[1] * weight2,
        triangle.v0[2] * weight0 + triangle.v1[2] * weight1 + triangle.v2[2] * weight2,
    )


def _triangle_centroid(triangle: MeshTriangle) -> Vector3:
    return (
        (triangle.v0[0] + triangle.v1[0] + triangle.v2[0]) / 3.0,
        (triangle.v0[1] + triangle.v1[1] + triangle.v2[1]) / 3.0,
        (triangle.v0[2] + triangle.v1[2] + triangle.v2[2]) / 3.0,
    )


def _base_direction(
    *,
    surface_point: Vector3,
    triangle: MeshTriangle,
    mesh_center: Vector3,
    normal_mode: str,
) -> Vector3:
    if normal_mode == "radial_xy":
        radial = (surface_point[0] - mesh_center[0], surface_point[1] - mesh_center[1], 0.0)
        if math.sqrt(_dot(radial, radial)) > 1.0e-8:
            return _normalize(radial, label="radial XY offset direction")
        triangle_xy = (triangle.normal[0], triangle.normal[1], 0.0)
        if math.sqrt(_dot(triangle_xy, triangle_xy)) > 1.0e-8:
            return _normalize(triangle_xy, label="triangle XY fallback direction")
        return (1.0, 0.0, 0.0)

    if normal_mode == "triangle_normal":
        direction = triangle.normal
        if _dot(direction, _subtract(_triangle_centroid(triangle), mesh_center)) < 0.0:
            direction = _mul_scalar(direction, -1.0)
        return _normalize(direction, label="triangle normal offset direction")

    raise ValueError(f"Unsupported normal_mode={normal_mode!r}")


def _tangent_basis(direction: Vector3) -> tuple[Vector3, Vector3]:
    reference = (0.0, 0.0, 1.0)
    if abs(_dot(direction, reference)) > 0.95:
        reference = (0.0, 1.0, 0.0)
    tangent_a = _normalize(_cross(reference, direction), label="tangent basis a")
    tangent_b = _normalize(_cross(direction, tangent_a), label="tangent basis b")
    return tangent_a, tangent_b


def _jitter_direction(
    *,
    direction: Vector3,
    normal_jitter_deg: float,
    rng: random.Random,
) -> Vector3:
    if normal_jitter_deg <= 0.0:
        return direction
    tangent_a, tangent_b = _tangent_basis(direction)
    max_component = math.tan(math.radians(normal_jitter_deg))
    jittered = _add(
        direction,
        _add(
            _mul_scalar(tangent_a, rng.uniform(-max_component, max_component)),
            _mul_scalar(tangent_b, rng.uniform(-max_component, max_component)),
        ),
    )
    return _normalize(jittered, label="jittered offset direction")


def _jitter_target(
    *,
    target: Vector3,
    direction: Vector3,
    surface_jitter: float,
    rng: random.Random,
) -> Vector3:
    if surface_jitter <= 0.0:
        return target
    tangent_a, tangent_b = _tangent_basis(direction)
    return _add(
        target,
        _add(
            _mul_scalar(tangent_a, rng.uniform(-surface_jitter, surface_jitter)),
            _mul_scalar(tangent_b, rng.uniform(-surface_jitter, surface_jitter)),
        ),
    )


def _append_viewpoint_row(
    rows: list[GeneratedViewpoint],
    *,
    position: Vector3,
    target: Vector3,
    direction: Vector3,
    sampled_distance: float,
    side: str | None = None,
) -> bool:
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
    rows.append(
        GeneratedViewpoint(
            row=row,
            position=position,
            target=target,
            direction=direction,
            sampled_distance=sampled_distance,
            side=side,
        )
    )
    return used_fallback


def _proxy_surface_radial_position(
    *,
    target: Vector3,
    direction: Vector3,
    component_proxy_center: Vector3,
    component_proxy_half_extents: Vector3,
    clearance: float,
) -> tuple[Vector3, Vector3]:
    xy_direction = (direction[0], direction[1], 0.0)
    if math.sqrt(_dot(xy_direction, xy_direction)) <= 1.0e-8:
        xy_direction = (target[0] - component_proxy_center[0], target[1] - component_proxy_center[1], 0.0)
    if math.sqrt(_dot(xy_direction, xy_direction)) <= 1.0e-8:
        xy_direction = (1.0, 0.0, 0.0)
    xy_direction = _normalize(xy_direction, label="proxy radial placement direction")

    candidates = []
    if abs(xy_direction[0]) > 1.0e-8:
        candidates.append(component_proxy_half_extents[0] / abs(xy_direction[0]))
    if abs(xy_direction[1]) > 1.0e-8:
        candidates.append(component_proxy_half_extents[1] / abs(xy_direction[1]))
    if not candidates:
        raise ValueError("proxy radial placement direction has no XY component.")
    boundary_distance = min(candidates)
    boundary = (
        component_proxy_center[0] + xy_direction[0] * boundary_distance,
        component_proxy_center[1] + xy_direction[1] * boundary_distance,
        target[2],
    )
    position = (
        boundary[0] + xy_direction[0] * clearance,
        boundary[1] + xy_direction[1] * clearance,
        boundary[2],
    )
    min_corner = _subtract(component_proxy_center, component_proxy_half_extents)
    max_corner = _add(component_proxy_center, component_proxy_half_extents)
    nearest_proxy_point = (
        min(max(position[0], min_corner[0]), max_corner[0]),
        min(max(position[1], min_corner[1]), max_corner[1]),
        min(max(position[2], min_corner[2]), max_corner[2]),
    )
    return position, nearest_proxy_point


def _proxy_side_balanced_position(
    *,
    target: Vector3,
    side: str,
    component_proxy_center: Vector3,
    component_proxy_half_extents: Vector3,
    clearance: float,
) -> tuple[Vector3, Vector3]:
    min_corner = _subtract(component_proxy_center, component_proxy_half_extents)
    max_corner = _add(component_proxy_center, component_proxy_half_extents)
    clamped_x = min(max(target[0], min_corner[0]), max_corner[0])
    clamped_y = min(max(target[1], min_corner[1]), max_corner[1])
    clamped_z = min(max(target[2], min_corner[2]), max_corner[2])

    if side == "+x":
        position = (max_corner[0] + clearance, clamped_y, target[2])
        nearest_proxy_point = (max_corner[0], clamped_y, clamped_z)
    elif side == "-x":
        position = (min_corner[0] - clearance, clamped_y, target[2])
        nearest_proxy_point = (min_corner[0], clamped_y, clamped_z)
    elif side == "+y":
        position = (clamped_x, max_corner[1] + clearance, target[2])
        nearest_proxy_point = (clamped_x, max_corner[1], clamped_z)
    elif side == "-y":
        position = (clamped_x, min_corner[1] - clearance, target[2])
        nearest_proxy_point = (clamped_x, min_corner[1], clamped_z)
    else:
        raise ValueError(f"Unsupported side={side!r}")
    return position, nearest_proxy_point


def _generate_viewpoints(
    *,
    triangles: Sequence[MeshTriangle],
    mesh_center: Vector3,
    num_viewpoints: int,
    placement_mode: str,
    sampling_mode: str,
    viewpoint_distance: float,
    distance_jitter: float,
    surface_jitter: float,
    normal_jitter_deg: float,
    min_spacing: float,
    seed: int,
    normal_mode: str,
    component_proxy_center: Vector3,
    component_proxy_half_extents: Vector3,
    min_z: float | None,
    max_z: float | None,
    max_attempts_multiplier: int,
) -> tuple[list[GeneratedViewpoint], dict[str, Any]]:
    if num_viewpoints <= 0:
        raise ValueError(f"--num_viewpoints must be positive, got {num_viewpoints!r}")
    if placement_mode not in {"mesh_offset", "proxy_surface_radial"}:
        raise ValueError(
            f"--placement_mode must be 'mesh_offset' or 'proxy_surface_radial', got {placement_mode!r}"
        )
    if sampling_mode not in {"area_random", "proxy_side_balanced"}:
        raise ValueError(
            f"--sampling_mode must be 'area_random' or 'proxy_side_balanced', got {sampling_mode!r}"
        )
    if viewpoint_distance <= 0.0 or not math.isfinite(viewpoint_distance):
        raise ValueError(f"--viewpoint_distance must be finite and positive, got {viewpoint_distance!r}")
    if distance_jitter < 0.0 or not math.isfinite(distance_jitter):
        raise ValueError(f"--distance_jitter must be finite and non-negative, got {distance_jitter!r}")
    if distance_jitter >= viewpoint_distance:
        raise ValueError("--distance_jitter must be smaller than --viewpoint_distance.")
    if surface_jitter < 0.0 or not math.isfinite(surface_jitter):
        raise ValueError(f"--surface_jitter must be finite and non-negative, got {surface_jitter!r}")
    if normal_jitter_deg < 0.0 or normal_jitter_deg >= 90.0 or not math.isfinite(normal_jitter_deg):
        raise ValueError("--normal_jitter_deg must be finite and in [0, 90).")
    if min_spacing < 0.0 or not math.isfinite(min_spacing):
        raise ValueError(f"--min_spacing must be finite and non-negative, got {min_spacing!r}")
    if min_z is not None and (not math.isfinite(min_z)):
        raise ValueError(f"--min_z must be finite when provided, got {min_z!r}")
    if max_z is not None and (not math.isfinite(max_z)):
        raise ValueError(f"--max_z must be finite when provided, got {max_z!r}")
    if min_z is not None and max_z is not None and min_z > max_z:
        raise ValueError("--min_z cannot be greater than --max_z.")
    if max_attempts_multiplier <= 0:
        raise ValueError("--max_attempts_multiplier must be positive.")
    if any(value <= 0.0 for value in component_proxy_half_extents):
        raise ValueError(
            f"--component_proxy_half_extents values must be positive, got {component_proxy_half_extents!r}"
        )

    rng = random.Random(seed)
    cumulative_areas: list[float] = []
    total_area = 0.0
    for triangle in triangles:
        total_area += triangle.area
        cumulative_areas.append(total_area)
    if total_area <= 0.0:
        raise ValueError("Cannot sample viewpoints from zero total mesh area.")

    generated: list[GeneratedViewpoint] = []
    fallback_count = 0
    rejected_by_spacing = 0
    rejected_by_z = 0
    attempts = 0
    max_attempts = num_viewpoints * max_attempts_multiplier
    min_spacing_squared = min_spacing * min_spacing
    side_sequence = ("+x", "-x", "+y", "-y")
    side_counts = {side: 0 for side in side_sequence}

    while len(generated) < num_viewpoints and attempts < max_attempts:
        attempts += 1
        side = side_sequence[len(generated) % len(side_sequence)] if sampling_mode == "proxy_side_balanced" else None
        area_pick = rng.uniform(0.0, total_area)
        triangle = triangles[min(bisect.bisect_left(cumulative_areas, area_pick), len(triangles) - 1)]
        surface_point = _sample_triangle_point(triangle, rng)
        base_direction = _base_direction(
            surface_point=surface_point,
            triangle=triangle,
            mesh_center=mesh_center,
            normal_mode=normal_mode,
        )
        direction = _jitter_direction(
            direction=base_direction,
            normal_jitter_deg=normal_jitter_deg,
            rng=rng,
        )
        target = _jitter_target(
            target=surface_point,
            direction=base_direction,
            surface_jitter=surface_jitter,
            rng=rng,
        )
        sampled_distance = viewpoint_distance + rng.uniform(-distance_jitter, distance_jitter)
        if sampling_mode == "proxy_side_balanced":
            if placement_mode != "proxy_surface_radial":
                raise ValueError("--sampling_mode proxy_side_balanced requires --placement_mode proxy_surface_radial.")
            position, look_target = _proxy_side_balanced_position(
                target=target,
                side=str(side),
                component_proxy_center=component_proxy_center,
                component_proxy_half_extents=component_proxy_half_extents,
                clearance=sampled_distance,
            )
            direction = _normalize(_subtract(position, look_target), label="viewpoint offset direction")
        elif placement_mode == "proxy_surface_radial":
            position, look_target = _proxy_surface_radial_position(
                target=target,
                direction=direction,
                component_proxy_center=component_proxy_center,
                component_proxy_half_extents=component_proxy_half_extents,
                clearance=sampled_distance,
            )
            direction = _normalize(_subtract(position, look_target), label="viewpoint offset direction")
        else:
            position = _add(target, _mul_scalar(direction, sampled_distance))
            look_target = target

        if (min_z is not None and position[2] < min_z) or (max_z is not None and position[2] > max_z):
            rejected_by_z += 1
            continue
        if min_spacing > 0.0 and any(
            _distance_squared(position, existing.position) < min_spacing_squared
            for existing in generated
        ):
            rejected_by_spacing += 1
            continue

        if _append_viewpoint_row(
            generated,
            position=position,
            target=look_target,
            direction=direction,
            sampled_distance=sampled_distance,
            side=side,
        ):
            fallback_count += 1
        if side is not None:
            side_counts[side] += 1

    if len(generated) != num_viewpoints:
        raise RuntimeError(
            f"Only generated {len(generated)}/{num_viewpoints} viewpoints after {attempts} attempts. "
            "Try reducing --min_spacing or widening --min_z/--max_z."
        )

    stats = {
        "attempts": attempts,
        "look_at_fallback_up_count": fallback_count,
        "rejected_by_min_spacing": rejected_by_spacing,
        "rejected_by_z": rejected_by_z,
        "side_counts": side_counts,
    }
    return generated, stats


def _write_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=VIEWPOINT_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _preview(generated: Sequence[GeneratedViewpoint], *, count: int = 5) -> list[dict[str, Any]]:
    preview_rows = []
    for item in generated[:count]:
        row = item.row
        preview_rows.append(
            {
                "id": int(row["id"]),
                "position": [float(row["x"]), float(row["y"]), float(row["z"])],
                "target": list(item.target),
                "direction": list(item.direction),
                "sampled_distance": item.sampled_distance,
                "side": item.side,
            }
        )
    return preview_rows


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
    pre_args, _ = pre_parser.parse_known_args()
    scenario_config = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
    scenario_defaults = _mesh_viewpoint_generation_defaults_from_config(scenario_config)

    parser = argparse.ArgumentParser(
        description="Generate an irregular mesh-sampled viewpoint CSV for diagnostic scans.",
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
        "--align_base_center_to_world_origin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Set mesh translation so the scaled/rotated mesh base center is at world origin.",
    )
    parser.add_argument("--component_proxy_padding", type=float, default=0.0)
    parser.add_argument("--output_csv", default=None)
    parser.add_argument("--output_json", default=None)
    parser.add_argument("--num_viewpoints", type=int, default=50)
    parser.add_argument(
        "--placement_mode",
        choices=("mesh_offset", "proxy_surface_radial"),
        default="mesh_offset",
        help=(
            "mesh_offset places the scanner relative to sampled OBJ surface points; "
            "proxy_surface_radial keeps OBJ targets but places scanner poses outside the active bbox proxy."
        ),
    )
    parser.add_argument(
        "--sampling_mode",
        choices=("area_random", "proxy_side_balanced"),
        default="area_random",
        help="area_random samples all OBJ triangles by area; proxy_side_balanced cycles viewpoints across +/-X and +/-Y.",
    )
    parser.add_argument("--viewpoint_distance", type=float, default=0.8)
    parser.add_argument("--distance_jitter", type=float, default=0.12)
    parser.add_argument("--surface_jitter", type=float, default=0.08)
    parser.add_argument("--normal_jitter_deg", type=float, default=6.0)
    parser.add_argument("--min_spacing", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--normal_mode",
        choices=("radial_xy", "triangle_normal"),
        default="radial_xy",
        help="radial_xy keeps mobile-base viewpoints around the OBJ footprint; triangle_normal offsets along face normals.",
    )
    parser.add_argument("--min_z", type=float, default=None)
    parser.add_argument("--max_z", type=float, default=None)
    parser.add_argument("--component_proxy_center", nargs=3, type=float, default=(0.0, 0.0, 1.0))
    parser.add_argument("--component_proxy_half_extents", nargs=3, type=float, default=(3.0, 1.0, 1.0))
    parser.add_argument("--max_attempts_multiplier", type=int, default=200)
    parser.set_defaults(**scenario_defaults)
    args = parser.parse_args()

    validate_mesh_format(args.mesh_format)
    validate_mesh_unit(args.mesh_unit)
    validate_orientation_format(args.mesh_orientation_format)
    validate_generation_args(args, repo_root=REPO_ROOT)
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

    mesh = load_obj_mesh(args.mesh_path, search_roots=(REPO_ROOT,))
    world_vertices = transform_vertices(
        mesh.vertices,
        mesh_scale=args.mesh_scale,
        mesh_position=mesh_position,
        mesh_orientation=args.mesh_orientation,
    )
    world_bounds_min, world_bounds_max = _bounds(world_vertices)
    mesh_center = _center_from_bounds(world_bounds_min, world_bounds_max)
    triangles = _build_mesh_triangles(world_vertices, mesh.faces)
    component_proxy_center = _as_vector3(args.component_proxy_center, label="component_proxy_center")
    component_proxy_half_extents = _as_vector3(
        args.component_proxy_half_extents,
        label="component_proxy_half_extents",
    )
    generated, stats = _generate_viewpoints(
        triangles=triangles,
        mesh_center=mesh_center,
        num_viewpoints=int(args.num_viewpoints),
        placement_mode=str(args.placement_mode),
        sampling_mode=str(args.sampling_mode),
        viewpoint_distance=float(args.viewpoint_distance),
        distance_jitter=float(args.distance_jitter),
        surface_jitter=float(args.surface_jitter),
        normal_jitter_deg=float(args.normal_jitter_deg),
        min_spacing=float(args.min_spacing),
        seed=int(args.seed),
        normal_mode=str(args.normal_mode),
        component_proxy_center=component_proxy_center,
        component_proxy_half_extents=component_proxy_half_extents,
        min_z=args.min_z,
        max_z=args.max_z,
        max_attempts_multiplier=int(args.max_attempts_multiplier),
    )

    output_csv = Path(args.output_csv)
    _write_csv(output_csv, [item.row for item in generated])

    report = {
        "mesh_path": str(mesh.path),
        "mesh_format": str(args.mesh_format),
        "mesh_unit": str(args.mesh_unit),
        "mesh_scale": [float(value) for value in args.mesh_scale],
        "mesh_position": list(mesh_position),
        "mesh_orientation": [float(value) for value in args.mesh_orientation],
        "mesh_orientation_format": str(args.mesh_orientation_format),
        "align_base_center_to_world_origin": bool(args.align_base_center_to_world_origin),
        "world_origin_convention": (
            "model_base_center" if args.align_base_center_to_world_origin else "explicit_mesh_position"
        ),
        "base_center_before_translation": (
            list(alignment.base_center_before_translation) if alignment is not None else None
        ),
        "auto_translation_if_used": list(alignment.auto_translation) if alignment is not None else None,
        "world_bounds_m_min": list(world_bounds_min),
        "world_bounds_m_max": list(world_bounds_max),
        "world_bounds_m_center": list(mesh_center),
        "raw_vertex_count": len(mesh.vertices),
        "raw_face_count": len(mesh.faces),
        "triangulated_face_count": len(triangles),
        "num_viewpoints": int(args.num_viewpoints),
        "placement_mode": str(args.placement_mode),
        "sampling_mode": str(args.sampling_mode),
        "viewpoint_distance": float(args.viewpoint_distance),
        "distance_jitter": float(args.distance_jitter),
        "surface_jitter": float(args.surface_jitter),
        "normal_jitter_deg": float(args.normal_jitter_deg),
        "min_spacing": float(args.min_spacing),
        "seed": int(args.seed),
        "normal_mode": str(args.normal_mode),
        "component_proxy_center": list(component_proxy_center),
        "component_proxy_half_extents": list(component_proxy_half_extents),
        "min_z": args.min_z,
        "max_z": args.max_z,
        "generated_num_viewpoints": len(generated),
        "generation_stats": stats,
        "csv_format": VIEWPOINT_CSV_FORMAT,
        "output_csv": str(output_csv),
        "sample": _preview(generated),
    }

    if args.output_json is not None:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[INFO]: Generated mesh-sampled viewpoint CSV")
    print(f"[INFO]: mesh_path={mesh.path}")
    print(
        "[INFO]: mesh_transform "
        f"unit={args.mesh_unit} scale={tuple(args.mesh_scale)} position={mesh_position} "
        f"orientation={tuple(args.mesh_orientation)}"
    )
    print(f"[INFO]: world_origin_convention={report['world_origin_convention']}")
    if alignment is not None:
        print(
            "[INFO]: base-center alignment "
            f"base_center_before_translation={alignment.base_center_before_translation} "
            f"auto_translation={alignment.auto_translation}"
        )
    print(
        "[INFO]: world bounds "
        f"min={world_bounds_min} max={world_bounds_max} center={mesh_center}"
    )
    print(
        "[INFO]: mesh sampling "
        f"vertices={len(mesh.vertices)} faces={len(mesh.faces)} triangulated={len(triangles)} "
        f"normal_mode={args.normal_mode} placement_mode={args.placement_mode} "
        f"sampling_mode={args.sampling_mode} seed={args.seed}"
    )
    print(
        "[INFO]: viewpoints "
        f"count={len(generated)} distance={args.viewpoint_distance} "
        f"distance_jitter={args.distance_jitter} surface_jitter={args.surface_jitter} "
        f"normal_jitter_deg={args.normal_jitter_deg} min_spacing={args.min_spacing} "
        f"stats={stats}"
    )
    print(f"[OK] wrote {output_csv}")


if __name__ == "__main__":
    main()
