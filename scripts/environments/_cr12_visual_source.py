"""Small CPU-only source-mesh reader/comparator for the accepted CR12 visuals.

No USD, physics or rendering imports. Mesh scale and its collision/visual origin
are applied once, returning geometry in rigid-body LINK axes, in metres. Bounds
alone never establish surface agreement. The comparator matches points through
a bounded spatial hash, then compares triangle geometry independently of point
ordering, normal splits, and triangle ordering. It does not repair geometry.
"""

from collections import Counter
import hashlib
import itertools
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

POINT_TOLERANCE_M = 1e-6
_BODY_NAMES = ("agv",) + tuple(f"link_{i}" for i in range(1, 7))
_GROUPS = {"agv": ("agv", "elevate", "base_link"),
           **{f"link_{i}": (f"link_{i}",) for i in range(1, 6)},
           "link_6": ("link_6", "scanner")}
_NEIGHBORS = tuple(itertools.product((-1, 0, 1), repeat=3))


def _vector(value):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ValueError("Expected a finite three-vector")
    return result


def _rotation(rpy):
    r, p, y = _vector(rpy)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.asarray(((cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr),
                       (sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr), (-sp, cp*sr, cp*cr)))


def _points(value):
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != 3 or not len(result) or not np.isfinite(result).all():
        raise ValueError("Expected nonempty finite mesh points Nx3")
    return result


def _indices(value):
    result = np.asarray(value)
    if result.ndim != 1 or not np.issubdtype(result.dtype, np.integer):
        raise ValueError("Topology counts/indices must be one-dimensional integers")
    return result.astype(np.int64, copy=False)


def triangulate(counts, indices, point_count):
    counts, indices = _indices(counts), _indices(indices)
    if not len(counts) or np.any(counts < 3) or int(counts.sum()) != len(indices):
        raise ValueError("Invalid polygon counts or flattened indices")
    if np.any(indices < 0) or np.any(indices >= point_count):
        raise ValueError("Mesh index outside point array")
    if np.all(counts == 3):
        return indices.reshape(-1, 3).copy()
    triangles, offset = [], 0
    for count in counts:
        face = indices[offset:offset+count]
        triangles.extend((face[0], face[j], face[j+1]) for j in range(1, count-1))
        offset += count
    return np.asarray(triangles, dtype=np.int64)


def read_obj(path):
    """Read OBJ v/f only; preserve polygon arities and material-reference facts."""
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    points, counts, indices, materials = [], [], [], []
    for line in raw.decode("utf-8-sig").splitlines():
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        if fields[0] == "v":
            if len(fields) not in (4, 5) or (len(fields) == 5 and float(fields[4]) != 1):
                raise ValueError(f"Unsupported OBJ homogeneous vertex: {path}")
            points.append([float(x) for x in fields[1:4]])
        elif fields[0] == "f":
            face = []
            for field in fields[1:]:
                index = int(field.split("/")[0])
                if index == 0:
                    raise ValueError("OBJ index zero is invalid")
                face.append(index-1 if index > 0 else len(points)+index)
            counts.append(len(face)); indices.extend(face)
        elif fields[0] == "mtllib":
            materials.extend(fields[1:])
    points = _points(points)
    triangles = triangulate(np.asarray(counts, dtype=np.int64), np.asarray(indices, dtype=np.int64), len(points))
    return {"points": points, "triangles": triangles, "vertex_count": len(points), "face_count": len(counts),
            "triangle_count": len(triangles), "face_arity_counts": dict(sorted(Counter(counts).items())),
            "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
            "material_references": [{"name": name, "exists": (path.parent/name).is_file()} for name in materials]}


def load_visual_sources(derived_urdf):
    """Read exactly the existing 10 visual + 10 collision representations.

    Both kinds are returned so runtime can establish identity by source geometry,
    rather than by a prim name or a physics schema alone. Inertials are not read.
    """
    path = Path(derived_urdf).resolve(strict=True)
    root = ET.fromstring(path.read_bytes())
    links = root.findall("link")
    if len(links) != 7 or {link.get("name") for link in links} != set(_BODY_NAMES):
        raise ValueError("Expected the accepted seven-body derived URDF")
    result, seen = [], set()
    for link in links:
        body = link.get("name")
        for kind in ("visual", "collision"):
            for node in link.findall(kind):
                name = node.get("name")
                if name not in {f"{part}_{kind}" for part in _GROUPS[body]} or name in seen:
                    raise ValueError(f"Unexpected or duplicate source shape: {body}/{name}")
                seen.add(name)
                mesh, origin = node.find("geometry/mesh"), node.find("origin")
                if mesh is None or origin is None:
                    raise ValueError("Expected explicit existing mesh and origin")
                filename = (path.parent/mesh.get("filename")).resolve(strict=True)
                scale = _vector([float(x) for x in mesh.get("scale").split()])
                xyz = _vector([float(x) for x in origin.get("xyz").split()])
                rpy = _vector([float(x) for x in origin.get("rpy").split()])
                if np.any(scale <= 0):
                    raise ValueError("Source mesh scale must be positive")
                data = read_obj(filename)
                body_points = (data.pop("points")*scale) @ _rotation(rpy).T + xyz
                result.append({"name": name, "kind": kind, "body": body, "filename": str(filename),
                               "scale": scale.tolist(), "origin_xyz": xyz.tolist(), "origin_rpy": rpy.tolist(),
                               "points_body": body_points, "units": "m", "bounds_frame": "body_link",
                               **data})
    wanted = {f"{part}_{kind}" for parts in _GROUPS.values() for part in parts for kind in ("visual", "collision")}
    if seen != wanted or len(result) != 20:
        raise ValueError("Missing source visual/collision shapes")
    return result


def source_summary(record):
    """Return compact JSON evidence without duplicating source point/face arrays."""
    result = {key: value for key, value in record.items() if key not in ("points_body", "triangles")}
    points = _points(record["points_body"])
    result.update(bounds_min_m=points.min(0).tolist(), bounds_max_m=points.max(0).tolist(),
                  unique_position_count=int(len(np.unique(points, axis=0))))
    return result


def _match_points(expected, observed, tolerance):
    # Exact duplicates caused by normals/UV splits have one geometric identity.
    reference, expected_ids = np.unique(expected, axis=0, return_inverse=True)
    measured, measured_ids = np.unique(observed, axis=0, return_inverse=True)
    if max(np.abs(reference).max(), np.abs(measured).max())/tolerance > 1e14:
        raise ValueError("Coordinates exceed bounded spatial-hash range")
    buckets = {}
    for index, point in enumerate(reference):
        key = tuple(np.floor(point/tolerance).astype(np.int64))
        buckets.setdefault(key, []).append(index)
    mapping = np.full(len(measured), -1, dtype=np.int64)
    max_error, ambiguous, capped = 0.0, 0, 0
    for index, point in enumerate(measured):
        cell = np.floor(point/tolerance).astype(np.int64)
        candidates = []
        for offset in _NEIGHBORS:
            candidates.extend(buckets.get(tuple(cell+offset), ()))
        # Refuse pathological dense neighborhoods instead of unbounded work.
        if len(candidates) > 2048:
            capped += 1
            continue
        if not candidates:
            continue
        distances = np.linalg.norm(reference[candidates]-point, axis=1)
        close = distances <= tolerance
        if not close.any():
            continue
        ambiguous += int(np.count_nonzero(close) > 1)
        selected = int(np.argmin(distances))
        mapping[index] = candidates[selected]
        max_error = max(max_error, float(distances[selected]))
    return expected_ids, mapping[measured_ids], {"source_unique_positions": len(reference),
            "observed_unique_positions": len(measured), "unmatched_observed_unique_positions": int(np.count_nonzero(mapping < 0)),
            "ambiguous_neighborhoods": ambiguous, "capped_neighborhoods": capped,
            "maximum_matched_point_error_m": max_error}


def _triangle_keys(ids, oriented=False):
    if not oriented:
        rows = np.sort(ids, axis=1)
    else:
        rows = np.asarray([min(tuple(row), tuple(np.roll(row, 1)), tuple(np.roll(row, 2))) for row in ids])
    return Counter(map(tuple, rows))


def compare_mesh(expected, points_body, counts, indices, *, tolerance_m=POINT_TOLERANCE_M):
    """Compare referenced point locations and triangle multisets, not bounds alone.

    Triangle vertex order is ignored for geometry, with winding reported
    separately. Fan triangulation is explicit: another diagonal on a polygon may
    remain UNRESOLVED; this function does not assert source damage on mismatch.
    Nearest source-point assignment is accepted only if the full triangle
    multiset agrees. Ambiguity without full agreement remains UNRESOLVED.
    """
    if not math.isfinite(tolerance_m) or tolerance_m <= 0:
        raise ValueError("Positive finite point tolerance required")
    source, observed = _points(expected["points_body"]), _points(points_body)
    source_tri = np.asarray(expected["triangles"])
    if source_tri.ndim != 2 or source_tri.shape[1] != 3:
        raise ValueError("Source triangles must be Nx3")
    source_tri = triangulate(np.full(len(source_tri), 3, dtype=np.int64), source_tri.reshape(-1), len(source))
    counts, indices = _indices(counts), _indices(indices)
    observed_tri = triangulate(counts, indices, len(observed))
    source_ids, observed_ids, matching = _match_points(source, observed, tolerance_m)
    used_source = set(source_ids[source_tri].reshape(-1).tolist())
    used_observed = set(observed_ids[observed_tri].reshape(-1).tolist())
    points_match = -1 not in observed_ids and used_source == used_observed
    geometry_match = bool(points_match and _triangle_keys(source_ids[source_tri]) == _triangle_keys(observed_ids[observed_tri]))
    winding_match = bool(geometry_match and _triangle_keys(source_ids[source_tri], True) == _triangle_keys(observed_ids[observed_tri], True))
    source_lo, source_hi, observed_lo, observed_hi = source.min(0), source.max(0), observed.min(0), observed.max(0)
    bounds_error = float(max(np.max(abs(source_lo-observed_lo)), np.max(abs(source_hi-observed_hi))))
    return {"status": "GEOMETRY_MATCH" if geometry_match else "UNRESOLVED_GEOMETRY_DIFFERENCE",
            "tolerance_m": tolerance_m, "points_match": bool(points_match),
            "triangle_geometry_match": geometry_match, "winding_match": winding_match,
            "source_vertex_count": len(source), "observed_vertex_count": len(observed),
            "source_triangle_count": len(source_tri), "observed_face_count": len(counts),
            "observed_triangle_count": len(observed_tri), "bounds_max_error_m": bounds_error,
            "source_bounds_min_m": source_lo.tolist(), "source_bounds_max_m": source_hi.tolist(),
            "observed_bounds_min_m": observed_lo.tolist(), "observed_bounds_max_m": observed_hi.tolist(),
            **matching}
