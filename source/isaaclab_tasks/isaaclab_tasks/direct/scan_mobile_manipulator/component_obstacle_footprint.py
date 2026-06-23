"""Dependency-light diagnostic footprint from a component OBJ mesh.

This helper deliberately does not create physics collision geometry. It builds a
small 2D occupancy proxy from the measured component mesh so assignment smokes
can report whether straight-line robot-to-viewpoint XY segments cross the
inflated component footprint.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .component_mesh import load_obj_mesh, transform_vertices, validate_orientation_format


Vector2 = tuple[float, float]
Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class ComponentObstacleFootprint:
    """Compact mesh-footprint occupancy used for diagnostic segment checks."""

    mesh_path: str
    bounds_xy_min: Vector2
    bounds_xy_max: Vector2
    grid_shape: tuple[int, int]
    resolution: float
    inflation_radius: float
    line_sample_step: float
    occupied_cells: frozenset[tuple[int, int]]
    inflated_occupied_cells: frozenset[tuple[int, int]]
    source_vertex_count: int
    source_face_count: int
    rasterized_triangle_count: int
    edge_sample_count: int
    method: str = "projected_triangle_grid_rasterization_with_edge_sampling"

    @property
    def occupied_cell_count(self) -> int:
        return len(self.occupied_cells)

    @property
    def inflated_occupied_cell_count(self) -> int:
        return len(self.inflated_occupied_cells)

    def contains_xy(self, xy: Sequence[float]) -> bool:
        cell = self.xy_to_cell(xy)
        return cell in self.inflated_occupied_cells if cell is not None else False

    def intersects_segment(self, start_xy: Sequence[float], end_xy: Sequence[float]) -> bool:
        start = _as_vector2(start_xy, name="segment_start_xy")
        end = _as_vector2(end_xy, name="segment_end_xy")
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        sample_count = max(1, int(math.ceil(length / self.line_sample_step)))
        for sample_index in range(sample_count + 1):
            alpha = sample_index / sample_count
            point = (start[0] + alpha * dx, start[1] + alpha * dy)
            if self.contains_xy(point):
                return True
        return False

    def xy_to_cell(self, xy: Sequence[float]) -> tuple[int, int] | None:
        point = _as_vector2(xy, name="xy")
        col = int(math.floor((point[0] - self.bounds_xy_min[0]) / self.resolution))
        row = int(math.floor((point[1] - self.bounds_xy_min[1]) / self.resolution))
        rows, cols = self.grid_shape
        if row < 0 or col < 0 or row >= rows or col >= cols:
            return None
        return row, col

    def cell_center(self, row: int, col: int) -> Vector2:
        return (
            self.bounds_xy_min[0] + (col + 0.5) * self.resolution,
            self.bounds_xy_min[1] + (row + 0.5) * self.resolution,
        )

    def to_diagnostics(self) -> dict[str, object]:
        return {
            "mesh_path": self.mesh_path,
            "obstacle_source": "component_mesh_footprint",
            "method": self.method,
            "path_segment_definition": "robot_base_xy_to_viewpoint_xy",
            "footprint_bounds_xy_min": list(self.bounds_xy_min),
            "footprint_bounds_xy_max": list(self.bounds_xy_max),
            "footprint_bounds_xy": [list(self.bounds_xy_min), list(self.bounds_xy_max)],
            "footprint_grid_shape": list(self.grid_shape),
            "footprint_resolution": float(self.resolution),
            "footprint_inflation_radius": float(self.inflation_radius),
            "line_sample_step": float(self.line_sample_step),
            "occupied_cell_count": self.occupied_cell_count,
            "inflated_occupied_cell_count": self.inflated_occupied_cell_count,
            "source_vertex_count": int(self.source_vertex_count),
            "source_face_count": int(self.source_face_count),
            "rasterized_triangle_count": int(self.rasterized_triangle_count),
            "edge_sample_count": int(self.edge_sample_count),
            "fallback_behavior": None,
            "notes": (
                "Diagnostic-only mesh footprint. It does not create collision bodies and does not alter "
                "assignment cost_matrix, masks, reward, or controller behavior."
            ),
        }


def build_component_obstacle_footprint(
    *,
    mesh_path: str | Path,
    mesh_scale: Sequence[float],
    mesh_position: Sequence[float],
    mesh_orientation: Sequence[float],
    mesh_orientation_format: str = "qwxyz",
    footprint_resolution: float = 0.10,
    footprint_inflation_radius: float = 0.30,
    line_sample_step: float = 0.10,
    search_roots: Sequence[Path] = (),
) -> ComponentObstacleFootprint:
    """Build an inflated XY footprint from transformed OBJ triangles."""

    validate_orientation_format(mesh_orientation_format)
    resolution = _positive_finite(footprint_resolution, name="footprint_resolution")
    inflation_radius = _non_negative_finite(footprint_inflation_radius, name="footprint_inflation_radius")
    sample_step = _positive_finite(line_sample_step, name="line_sample_step")

    mesh_data = load_obj_mesh(mesh_path, search_roots=search_roots)
    world_vertices = transform_vertices(
        mesh_data.vertices,
        mesh_scale=mesh_scale,
        mesh_position=mesh_position,
        mesh_orientation=mesh_orientation,
    )
    if not world_vertices:
        raise ValueError(f"Cannot build obstacle footprint from an empty mesh: {mesh_data.path}")

    min_x = min(vertex[0] for vertex in world_vertices) - inflation_radius - resolution
    max_x = max(vertex[0] for vertex in world_vertices) + inflation_radius + resolution
    min_y = min(vertex[1] for vertex in world_vertices) - inflation_radius - resolution
    max_y = max(vertex[1] for vertex in world_vertices) + inflation_radius + resolution
    cols = max(1, int(math.ceil((max_x - min_x) / resolution)))
    rows = max(1, int(math.ceil((max_y - min_y) / resolution)))
    bounds_xy_min = (min_x, min_y)
    bounds_xy_max = (min_x + cols * resolution, min_y + rows * resolution)

    occupied: set[tuple[int, int]] = set()
    rasterized_triangle_count = 0
    edge_sample_count = 0
    for face in mesh_data.faces:
        if len(face) < 3:
            continue
        first = face[0]
        for face_index in range(1, len(face) - 1):
            tri = (
                _xy(world_vertices[first]),
                _xy(world_vertices[face[face_index]]),
                _xy(world_vertices[face[face_index + 1]]),
            )
            rasterized_triangle_count += 1
            edge_sample_count += _mark_triangle_cells(
                occupied,
                tri,
                bounds_xy_min=bounds_xy_min,
                grid_shape=(rows, cols),
                resolution=resolution,
            )

    if not occupied:
        # A valid OBJ can theoretically contain only vertices. Mark transformed
        # vertices so diagnostics remain mesh-derived rather than falling back
        # to the overall component bbox.
        for vertex in world_vertices:
            cell = _xy_to_cell(_xy(vertex), bounds_xy_min=bounds_xy_min, grid_shape=(rows, cols), resolution=resolution)
            if cell is not None:
                occupied.add(cell)

    inflated = _inflate_cells(
        occupied,
        bounds_xy_min=bounds_xy_min,
        grid_shape=(rows, cols),
        resolution=resolution,
        inflation_radius=inflation_radius,
    )
    return ComponentObstacleFootprint(
        mesh_path=str(mesh_data.path),
        bounds_xy_min=bounds_xy_min,
        bounds_xy_max=bounds_xy_max,
        grid_shape=(rows, cols),
        resolution=resolution,
        inflation_radius=inflation_radius,
        line_sample_step=sample_step,
        occupied_cells=frozenset(occupied),
        inflated_occupied_cells=frozenset(inflated),
        source_vertex_count=len(mesh_data.vertices),
        source_face_count=len(mesh_data.faces),
        rasterized_triangle_count=rasterized_triangle_count,
        edge_sample_count=edge_sample_count,
    )


def _mark_triangle_cells(
    occupied: set[tuple[int, int]],
    triangle: tuple[Vector2, Vector2, Vector2],
    *,
    bounds_xy_min: Vector2,
    grid_shape: tuple[int, int],
    resolution: float,
) -> int:
    min_x = min(point[0] for point in triangle)
    max_x = max(point[0] for point in triangle)
    min_y = min(point[1] for point in triangle)
    max_y = max(point[1] for point in triangle)
    min_cell = _xy_to_cell((min_x, min_y), bounds_xy_min=bounds_xy_min, grid_shape=grid_shape, resolution=resolution)
    max_cell = _xy_to_cell((max_x, max_y), bounds_xy_min=bounds_xy_min, grid_shape=grid_shape, resolution=resolution)
    rows, cols = grid_shape
    if min_cell is None:
        min_row = max(0, int(math.floor((min_y - bounds_xy_min[1]) / resolution)))
        min_col = max(0, int(math.floor((min_x - bounds_xy_min[0]) / resolution)))
    else:
        min_row, min_col = min_cell
    if max_cell is None:
        max_row = min(rows - 1, int(math.floor((max_y - bounds_xy_min[1]) / resolution)))
        max_col = min(cols - 1, int(math.floor((max_x - bounds_xy_min[0]) / resolution)))
    else:
        max_row, max_col = max_cell

    if max_row < 0 or max_col < 0 or min_row >= rows or min_col >= cols:
        return 0
    min_row = max(0, min_row)
    min_col = max(0, min_col)
    max_row = min(rows - 1, max_row)
    max_col = min(cols - 1, max_col)

    marked_before = len(occupied)
    area = _triangle_area2(*triangle)
    if abs(area) > 1.0e-12:
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                center = (
                    bounds_xy_min[0] + (col + 0.5) * resolution,
                    bounds_xy_min[1] + (row + 0.5) * resolution,
                )
                if _point_in_triangle(center, triangle):
                    occupied.add((row, col))

    edge_samples = 0
    for start, end in ((triangle[0], triangle[1]), (triangle[1], triangle[2]), (triangle[2], triangle[0])):
        edge_samples += _mark_line_cells(
            occupied,
            start,
            end,
            bounds_xy_min=bounds_xy_min,
            grid_shape=grid_shape,
            resolution=resolution,
        )
    return edge_samples + max(0, len(occupied) - marked_before)


def _mark_line_cells(
    occupied: set[tuple[int, int]],
    start: Vector2,
    end: Vector2,
    *,
    bounds_xy_min: Vector2,
    grid_shape: tuple[int, int],
    resolution: float,
) -> int:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    sample_count = max(1, int(math.ceil(length / (resolution * 0.5))))
    marked = 0
    for sample_index in range(sample_count + 1):
        alpha = sample_index / sample_count
        point = (start[0] + alpha * dx, start[1] + alpha * dy)
        cell = _xy_to_cell(point, bounds_xy_min=bounds_xy_min, grid_shape=grid_shape, resolution=resolution)
        if cell is not None and cell not in occupied:
            occupied.add(cell)
            marked += 1
    return marked


def _inflate_cells(
    occupied: Iterable[tuple[int, int]],
    *,
    bounds_xy_min: Vector2,
    grid_shape: tuple[int, int],
    resolution: float,
    inflation_radius: float,
) -> set[tuple[int, int]]:
    rows, cols = grid_shape
    inflation_cells = int(math.ceil(inflation_radius / resolution))
    inflated = set(occupied)
    if inflation_cells <= 0:
        return inflated
    max_distance = inflation_radius + resolution * math.sqrt(0.5)
    for row, col in tuple(occupied):
        center = _cell_center(row, col, bounds_xy_min=bounds_xy_min, resolution=resolution)
        for d_row in range(-inflation_cells, inflation_cells + 1):
            next_row = row + d_row
            if next_row < 0 or next_row >= rows:
                continue
            for d_col in range(-inflation_cells, inflation_cells + 1):
                next_col = col + d_col
                if next_col < 0 or next_col >= cols:
                    continue
                next_center = _cell_center(next_row, next_col, bounds_xy_min=bounds_xy_min, resolution=resolution)
                if math.hypot(next_center[0] - center[0], next_center[1] - center[1]) <= max_distance:
                    inflated.add((next_row, next_col))
    return inflated


def _xy_to_cell(
    xy: Vector2,
    *,
    bounds_xy_min: Vector2,
    grid_shape: tuple[int, int],
    resolution: float,
) -> tuple[int, int] | None:
    col = int(math.floor((xy[0] - bounds_xy_min[0]) / resolution))
    row = int(math.floor((xy[1] - bounds_xy_min[1]) / resolution))
    rows, cols = grid_shape
    if row < 0 or col < 0 or row >= rows or col >= cols:
        return None
    return row, col


def _cell_center(row: int, col: int, *, bounds_xy_min: Vector2, resolution: float) -> Vector2:
    return (
        bounds_xy_min[0] + (col + 0.5) * resolution,
        bounds_xy_min[1] + (row + 0.5) * resolution,
    )


def _point_in_triangle(point: Vector2, triangle: tuple[Vector2, Vector2, Vector2]) -> bool:
    a, b, c = triangle
    area = _triangle_area2(a, b, c)
    if abs(area) <= 1.0e-12:
        return False
    inv_area = 1.0 / area
    w0 = _triangle_area2(point, b, c) * inv_area
    w1 = _triangle_area2(a, point, c) * inv_area
    w2 = _triangle_area2(a, b, point) * inv_area
    eps = 1.0e-8
    return w0 >= -eps and w1 >= -eps and w2 >= -eps and (w0 + w1 + w2) <= 1.0 + eps


def _triangle_area2(a: Vector2, b: Vector2, c: Vector2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _as_vector2(value: Sequence[float], *, name: str) -> Vector2:
    try:
        values = tuple(float(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of two finite floats, got {value!r}.") from exc
    if len(values) != 2:
        raise ValueError(f"{name} must contain two values, got {len(values)}: {value!r}.")
    if not all(math.isfinite(item) for item in values):
        raise ValueError(f"{name} must contain only finite values, got {value!r}.")
    return values  # type: ignore[return-value]


def _positive_finite(value: float, *, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be positive and finite, got {value!r}.")
    return numeric


def _non_negative_finite(value: float, *, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise ValueError(f"{name} must be finite and non-negative, got {value!r}.")
    return numeric


def _xy(vertex: Vector3) -> Vector2:
    return (float(vertex[0]), float(vertex[1]))
