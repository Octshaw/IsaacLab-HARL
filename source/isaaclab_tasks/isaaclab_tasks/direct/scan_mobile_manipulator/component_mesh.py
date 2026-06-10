"""Visual component mesh loading and rotation-aware bbox proxy utilities."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


Vector3 = tuple[float, float, float]
QuatWxyz = tuple[float, float, float, float]


@dataclass(frozen=True)
class ObjMeshData:
    """Minimal OBJ data needed for visual-only USD mesh creation."""

    path: Path
    vertices: tuple[Vector3, ...]
    faces: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ComponentMeshBounds:
    """Bounds and auto bbox proxy produced from transformed mesh vertices."""

    mesh_path: str
    mesh_format: str
    mesh_unit: str
    mesh_scale: Vector3
    mesh_position: Vector3
    mesh_orientation: QuatWxyz
    raw_bounds_obj_units_min: Vector3
    raw_bounds_obj_units_max: Vector3
    scaled_local_bounds_m_min: Vector3
    scaled_local_bounds_m_max: Vector3
    world_bounds_m_min: Vector3
    world_bounds_m_max: Vector3
    auto_component_proxy_center: Vector3
    auto_component_proxy_half_extents: Vector3
    component_proxy_padding: float

    def to_dict(self) -> dict:
        return {
            "mesh_path": self.mesh_path,
            "mesh_format": self.mesh_format,
            "mesh_unit": self.mesh_unit,
            "mesh_scale": list(self.mesh_scale),
            "mesh_position": list(self.mesh_position),
            "mesh_orientation": list(self.mesh_orientation),
            "raw_bounds_obj_units_min": list(self.raw_bounds_obj_units_min),
            "raw_bounds_obj_units_max": list(self.raw_bounds_obj_units_max),
            "scaled_local_bounds_m_min": list(self.scaled_local_bounds_m_min),
            "scaled_local_bounds_m_max": list(self.scaled_local_bounds_m_max),
            "world_bounds_m_min": list(self.world_bounds_m_min),
            "world_bounds_m_max": list(self.world_bounds_m_max),
            "auto_component_proxy_center": list(self.auto_component_proxy_center),
            "auto_component_proxy_half_extents": list(self.auto_component_proxy_half_extents),
            "component_proxy_padding": float(self.component_proxy_padding),
        }


@dataclass(frozen=True)
class MeshBaseCenterAlignment:
    """Translation that places the transformed mesh base center at the world origin."""

    base_center_before_translation: Vector3
    auto_translation: Vector3
    rotated_local_bounds_m_min: Vector3
    rotated_local_bounds_m_max: Vector3

    def to_dict(self) -> dict:
        return {
            "base_center_before_translation": list(self.base_center_before_translation),
            "auto_translation_if_used": list(self.auto_translation),
            "rotated_local_bounds_m_min": list(self.rotated_local_bounds_m_min),
            "rotated_local_bounds_m_max": list(self.rotated_local_bounds_m_max),
        }


def resolve_mesh_path(mesh_path: str | Path, *, search_roots: Sequence[Path] = ()) -> Path:
    """Resolve a mesh path against cwd and optional search roots."""

    if mesh_path is None:
        raise ValueError("component mesh path must not be None.")
    raw_path = Path(mesh_path).expanduser()
    candidates = [raw_path]
    if not raw_path.is_absolute():
        candidates.extend(root / raw_path for root in search_roots)
    for candidate in candidates:
        if candidate.exists():
            if not candidate.is_file():
                raise ValueError(f"component mesh path is not a file: {candidate}")
            return candidate.resolve()
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"component mesh file does not exist. searched: {searched}")


def validate_mesh_format(mesh_format: str) -> str:
    value = str(mesh_format).strip().lower()
    if value != "obj":
        raise ValueError(f"Unsupported component_mesh_format={mesh_format!r}; only 'obj' is supported.")
    return value


def validate_mesh_unit(mesh_unit: str) -> str:
    value = str(mesh_unit).strip().lower()
    if value != "mm":
        raise ValueError(f"Unsupported component_mesh_unit={mesh_unit!r}; only 'mm' is supported for now.")
    return value


def validate_orientation_format(orientation_format: str) -> str:
    value = str(orientation_format).strip().lower()
    if value != "qwxyz":
        raise ValueError(
            f"Unsupported component_mesh_orientation_format={orientation_format!r}; only 'qwxyz' is supported."
        )
    return value


def load_obj_vertices(mesh_path: str | Path, *, search_roots: Sequence[Path] = ()) -> tuple[Vector3, ...]:
    """Load only OBJ vertex rows (`v x y z`) for bbox computation."""

    resolved_path = resolve_mesh_path(mesh_path, search_roots=search_roots)
    vertices: list[Vector3] = []
    try:
        with resolved_path.open("r", encoding="utf-8", errors="strict") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if parts[0] != "v":
                    continue
                if len(parts) < 4:
                    raise ValueError(f"OBJ vertex row at {resolved_path}:{line_number} must contain x y z.")
                try:
                    vertex = (float(parts[1]), float(parts[2]), float(parts[3]))
                except ValueError as exc:
                    raise ValueError(f"OBJ vertex row at {resolved_path}:{line_number} has invalid float values.") from exc
                if not all(math.isfinite(value) for value in vertex):
                    raise ValueError(f"OBJ vertex row at {resolved_path}:{line_number} contains non-finite values.")
                vertices.append(vertex)
    except UnicodeDecodeError as exc:
        raise ValueError(f"Could not read OBJ mesh as UTF-8 text: {resolved_path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read OBJ mesh: {resolved_path}") from exc

    if not vertices:
        raise ValueError(f"OBJ mesh contains no valid vertex rows: {resolved_path}")
    return tuple(vertices)


def load_obj_mesh(mesh_path: str | Path, *, search_roots: Sequence[Path] = ()) -> ObjMeshData:
    """Load OBJ vertices and polygon faces for visual-only USD mesh creation."""

    resolved_path = resolve_mesh_path(mesh_path, search_roots=search_roots)
    vertices: list[Vector3] = []
    raw_faces: list[tuple[int, list[str]]] = []
    try:
        with resolved_path.open("r", encoding="utf-8", errors="strict") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if parts[0] == "v":
                    if len(parts) < 4:
                        raise ValueError(f"OBJ vertex row at {resolved_path}:{line_number} must contain x y z.")
                    try:
                        vertex = (float(parts[1]), float(parts[2]), float(parts[3]))
                    except ValueError as exc:
                        raise ValueError(
                            f"OBJ vertex row at {resolved_path}:{line_number} has invalid float values."
                        ) from exc
                    if not all(math.isfinite(value) for value in vertex):
                        raise ValueError(f"OBJ vertex row at {resolved_path}:{line_number} contains non-finite values.")
                    vertices.append(vertex)
                elif parts[0] == "f":
                    if len(parts) < 4:
                        raise ValueError(f"OBJ face row at {resolved_path}:{line_number} must contain at least 3 vertices.")
                    raw_faces.append((line_number, parts[1:]))
    except UnicodeDecodeError as exc:
        raise ValueError(f"Could not read OBJ mesh as UTF-8 text: {resolved_path}") from exc
    except OSError as exc:
        raise OSError(f"Could not read OBJ mesh: {resolved_path}") from exc

    if not vertices:
        raise ValueError(f"OBJ mesh contains no valid vertex rows: {resolved_path}")

    faces = []
    for line_number, tokens in raw_faces:
        face = []
        for token in tokens:
            vertex_index_text = token.split("/", 1)[0]
            if not vertex_index_text:
                raise ValueError(f"OBJ face row at {resolved_path}:{line_number} has an empty vertex index.")
            try:
                obj_index = int(vertex_index_text)
            except ValueError as exc:
                raise ValueError(f"OBJ face row at {resolved_path}:{line_number} has invalid vertex index.") from exc
            if obj_index == 0:
                raise ValueError(f"OBJ face row at {resolved_path}:{line_number} uses invalid vertex index 0.")
            zero_based = obj_index - 1 if obj_index > 0 else len(vertices) + obj_index
            if zero_based < 0 or zero_based >= len(vertices):
                raise ValueError(
                    f"OBJ face row at {resolved_path}:{line_number} references vertex {obj_index}, "
                    f"but mesh has {len(vertices)} vertices."
                )
            face.append(zero_based)
        faces.append(tuple(face))

    return ObjMeshData(path=resolved_path, vertices=tuple(vertices), faces=tuple(faces))


def compute_component_mesh_bounds(
    *,
    mesh_path: str | Path,
    mesh_format: str = "obj",
    mesh_unit: str = "mm",
    mesh_scale: Sequence[float] = (0.001, 0.001, 0.001),
    mesh_position: Sequence[float] = (0.0, 0.0, 0.0),
    mesh_orientation: Sequence[float] = (1.0, 0.0, 0.0, 0.0),
    mesh_orientation_format: str = "qwxyz",
    component_proxy_padding: float = 0.0,
    search_roots: Sequence[Path] = (),
) -> ComponentMeshBounds:
    """Compute a world-space AABB from transformed OBJ vertices."""

    mesh_format = validate_mesh_format(mesh_format)
    mesh_unit = validate_mesh_unit(mesh_unit)
    validate_orientation_format(mesh_orientation_format)
    scale = _as_finite_vector3(mesh_scale, name="component_mesh_scale")
    if any(value <= 0.0 for value in scale):
        raise ValueError(f"component_mesh_scale must contain positive values, got {scale!r}.")
    position = _as_finite_vector3(mesh_position, name="component_mesh_position")
    orientation = normalize_quat_wxyz(mesh_orientation)
    padding = float(component_proxy_padding)
    if not math.isfinite(padding) or padding < 0.0:
        raise ValueError(f"component_proxy_padding must be finite and non-negative, got {component_proxy_padding!r}.")

    resolved_path = resolve_mesh_path(mesh_path, search_roots=search_roots)
    vertices = load_obj_vertices(resolved_path)
    raw_min, raw_max = _bounds(vertices)
    scaled_vertices = apply_scale(vertices, scale)
    scaled_min, scaled_max = _bounds(scaled_vertices)
    world_vertices = transform_vertices(
        vertices,
        mesh_scale=scale,
        mesh_position=position,
        mesh_orientation=orientation,
    )
    world_min, world_max = _bounds(world_vertices)
    center = tuple((world_min[index] + world_max[index]) * 0.5 for index in range(3))
    half_extents = tuple((world_max[index] - world_min[index]) * 0.5 + padding for index in range(3))
    if any(value <= 0.0 for value in half_extents):
        raise ValueError(
            "auto component bbox half extents must be positive after padding; "
            f"got {half_extents!r} from mesh {resolved_path}."
        )

    return ComponentMeshBounds(
        mesh_path=str(resolved_path),
        mesh_format=mesh_format,
        mesh_unit=mesh_unit,
        mesh_scale=scale,
        mesh_position=position,
        mesh_orientation=orientation,
        raw_bounds_obj_units_min=raw_min,
        raw_bounds_obj_units_max=raw_max,
        scaled_local_bounds_m_min=scaled_min,
        scaled_local_bounds_m_max=scaled_max,
        world_bounds_m_min=world_min,
        world_bounds_m_max=world_max,
        auto_component_proxy_center=center,
        auto_component_proxy_half_extents=half_extents,
        component_proxy_padding=padding,
    )


def compute_base_center_alignment_translation(
    *,
    mesh_path: str | Path,
    mesh_format: str = "obj",
    mesh_unit: str = "mm",
    mesh_scale: Sequence[float] = (0.001, 0.001, 0.001),
    mesh_orientation: Sequence[float] = (1.0, 0.0, 0.0, 0.0),
    mesh_orientation_format: str = "qwxyz",
    search_roots: Sequence[Path] = (),
) -> MeshBaseCenterAlignment:
    """Compute the translation that maps the scaled/rotated mesh base center to world origin."""

    validate_mesh_format(mesh_format)
    validate_mesh_unit(mesh_unit)
    validate_orientation_format(mesh_orientation_format)
    scale = _as_finite_vector3(mesh_scale, name="component_mesh_scale")
    if any(value <= 0.0 for value in scale):
        raise ValueError(f"component_mesh_scale must contain positive values, got {scale!r}.")
    orientation = normalize_quat_wxyz(mesh_orientation)

    resolved_path = resolve_mesh_path(mesh_path, search_roots=search_roots)
    vertices = load_obj_vertices(resolved_path)
    scaled_vertices = apply_scale(vertices, scale)
    rotated_vertices = tuple(rotate_vector_wxyz(orientation, vertex) for vertex in scaled_vertices)
    rotated_min, rotated_max = _bounds(rotated_vertices)
    base_center = (
        (rotated_min[0] + rotated_max[0]) * 0.5,
        (rotated_min[1] + rotated_max[1]) * 0.5,
        rotated_min[2],
    )
    auto_translation = (-base_center[0], -base_center[1], -base_center[2])
    return MeshBaseCenterAlignment(
        base_center_before_translation=base_center,
        auto_translation=auto_translation,
        rotated_local_bounds_m_min=rotated_min,
        rotated_local_bounds_m_max=rotated_max,
    )


def apply_scale(vertices: Iterable[Vector3], scale: Vector3) -> tuple[Vector3, ...]:
    return tuple((vertex[0] * scale[0], vertex[1] * scale[1], vertex[2] * scale[2]) for vertex in vertices)


def transform_vertices(
    vertices: Iterable[Vector3],
    *,
    mesh_scale: Sequence[float],
    mesh_position: Sequence[float],
    mesh_orientation: Sequence[float],
) -> tuple[Vector3, ...]:
    scale = _as_finite_vector3(mesh_scale, name="component_mesh_scale")
    position = _as_finite_vector3(mesh_position, name="component_mesh_position")
    orientation = normalize_quat_wxyz(mesh_orientation)
    transformed = []
    for vertex in vertices:
        scaled = (vertex[0] * scale[0], vertex[1] * scale[1], vertex[2] * scale[2])
        rotated = rotate_vector_wxyz(orientation, scaled)
        transformed.append(
            (rotated[0] + position[0], rotated[1] + position[1], rotated[2] + position[2])
        )
    return tuple(transformed)


def normalize_quat_wxyz(quat: Sequence[float]) -> QuatWxyz:
    values = _as_finite_tuple(quat, name="component_mesh_orientation", length=4)
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 1.0e-8:
        raise ValueError("component_mesh_orientation quaternion must be non-zero.")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def rotate_vector_wxyz(quat: QuatWxyz, vector: Vector3) -> Vector3:
    w, x, y, z = quat
    q_vec = (x, y, z)
    t = _mul_scalar(_cross(q_vec, vector), 2.0)
    return _add(vector, _add(_mul_scalar(t, w), _cross(q_vec, t)))


def bounds_to_json(bounds: ComponentMeshBounds) -> str:
    return json.dumps(bounds.to_dict(), indent=2)


def _as_finite_vector3(value: Sequence[float], *, name: str) -> Vector3:
    return _as_finite_tuple(value, name=name, length=3)  # type: ignore[return-value]


def _as_finite_tuple(value: Sequence[float], *, name: str, length: int) -> tuple[float, ...]:
    try:
        values = tuple(float(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of {length} finite floats, got {value!r}.") from exc
    if len(values) != length:
        raise ValueError(f"{name} must contain {length} values, got {len(values)}: {value!r}.")
    if not all(math.isfinite(item) for item in values):
        raise ValueError(f"{name} must contain only finite values, got {value!r}.")
    return values


def _bounds(vertices: Sequence[Vector3]) -> tuple[Vector3, Vector3]:
    if not vertices:
        raise ValueError("Cannot compute bounds for an empty vertex set.")
    min_corner = tuple(min(vertex[axis] for vertex in vertices) for axis in range(3))
    max_corner = tuple(max(vertex[axis] for vertex in vertices) for axis in range(3))
    return min_corner, max_corner


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul_scalar(a: Vector3, value: float) -> Vector3:
    return (a[0] * value, a[1] * value, a[2] * value)
