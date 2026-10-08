"""CPU-only conservative CR12 collision-enclosure refinement.

Bounds are metres in rigid-body LINK axes, after mesh scale and fixed origins.
Each OBB is expanded by the WORLD-axis cube [-.002,.002]^3. The 15 OBB
directions provide sufficient separation evidence, not a complete intersection
test for the resulting zonotopes. No separating direction means reject; it is
never proof of physical contact. No physics, rendering, or asset writes occur.
"""

import copy
import hashlib
import itertools
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

import numpy as np

BODY_NAMES = ("agv",) + tuple(f"link_{i}" for i in range(1, 7))
SHAPE_BODIES = {
    "agv_collision": "agv", "elevate_collision": "agv", "base_link_collision": "agv",
    **{f"link_{i}_collision": f"link_{i}" for i in range(1, 7)},
    "scanner_collision": "link_6",
}
GEOMETRY_MODE = "aabb_then_obb_margin_v1"
WORLD_MARGIN_M = 0.002
GAP_TOLERANCE_M = 1e-6
ROTATION_TOLERANCE = 1e-6
CROSS_AXIS_MIN_NORM = 1e-8
COUNTER_KEYS = ("total_shape_pairs", "exempt_pairs", "forbidden_pairs", "aabb_separated",
                "obb_refined", "obb_separated", "unresolved_pairs", "ground_failures")


class GeometryRefinementError(ValueError):
    def __init__(self, message, summary):
        super().__init__(message)
        self.category = "geometry_guard" if summary["input_valid"] else "geometry_monitor"
        self.summary = summary
        self.details = summary


def _array(value, shape):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"Expected finite geometry array {shape}; got {result.shape}")
    return result.copy()


def _rotation(value):
    rotation = _array(value, (3, 3))
    if (np.max(np.abs(rotation.T @ rotation - np.eye(3))) > ROTATION_TOLERANCE
            or abs(np.linalg.det(rotation) - 1.0) > ROTATION_TOLERANCE):
        raise ValueError("Geometry transform is not a proper rigid rotation (scale/shear/reflection)")
    return rotation  # No silent orthogonalization or normalization of input transforms.


def _pose(value):
    pose = _array(value, (4, 4))
    if not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-12, rtol=0):
        raise ValueError("Geometry transform has a non-affine last row")
    _rotation(pose[:3, :3])
    return pose


def box_from_bounds(lower, upper, pose):
    """Construct an OBB; input enclosure scale/origin must already be applied."""
    lower, upper, pose = _array(lower, (3,)), _array(upper, (3,)), _pose(pose)
    if np.any(upper <= lower):
        raise ValueError("Collision bounds must have positive dimensions")
    centre = pose[:3, :3] @ ((lower + upper) * 0.5) + pose[:3, 3]
    half = (upper - lower) * 0.5
    if not np.isfinite(centre).all() or not np.isfinite(half).all():
        raise ValueError("Collision enclosure arithmetic overflow")
    return {"center": centre, "axes": pose[:3, :3].copy(), "half_extents": half}


def _validated_box(box):
    center, axes, half = _array(box["center"], (3,)), _rotation(box["axes"]), _array(box["half_extents"], (3,))
    if np.any(half <= 0):
        raise ValueError("OBB half extents must be positive")
    return {"center": center, "axes": axes, "half_extents": half}


def projection_radius(box, unit_axis, margin=WORLD_MARGIN_M):
    """Support radius of B plus a world-axis cube along an explicit unit axis."""
    box, axis = _validated_box(box), _array(unit_axis, (3,))
    if abs(np.linalg.norm(axis) - 1.0) > 1e-12 or not np.isfinite(margin) or margin < 0:
        raise ValueError("Projection requires a unit axis and nonnegative finite margin")
    return float(np.dot(box["half_extents"], np.abs(box["axes"].T @ axis))
                 + margin * np.abs(axis).sum())


def pair_separation(left, right, *, margin=WORLD_MARGIN_M):
    """Test all 15 directions. Configurable margin is for CPU algebra tests only.

    The production GeometryGuard always supplies WORLD_MARGIN_M. Reliable
    separation requires gap strictly greater than GAP_TOLERANCE_M in float64.
    """
    left, right = _validated_box(left), _validated_box(right)
    if not np.isfinite(margin) or margin < 0:
        raise ValueError("Invalid world margin")
    axes = [(f"A{i}", left["axes"][:, i], False) for i in range(3)]
    axes += [(f"B{i}", right["axes"][:, i], False) for i in range(3)]
    axes += [(f"AxB{i}{j}", np.cross(left["axes"][:, i], right["axes"][:, j]), True)
             for i in range(3) for j in range(3)]
    delta, best, tested, skipped = right["center"] - left["center"], None, 0, 0
    for source, candidate, cross in axes:
        norm = float(np.linalg.norm(candidate))
        if cross and norm <= CROSS_AXIS_MIN_NORM:
            skipped += 1
            continue
        axis = candidate / norm
        # Keep box and world-cube support terms separate for evidence.
        box_radii = sum(float(np.dot(b["half_extents"], np.abs(b["axes"].T @ axis))) for b in (left, right))
        margin_radius = float(2 * margin * np.abs(axis).sum())
        gap = float(abs(np.dot(axis, delta)) - box_radii - margin_radius)
        if not np.isfinite(gap):
            raise ValueError("Nonfinite projection gap")
        tested += 1
        if best is None or gap > best["gap_m"]:
            best = {"axis_source": source, "axis_world": axis.tolist(), "gap_m": gap,
                    "pair_margin_radius_m": margin_radius}
    separated = best["gap_m"] > GAP_TOLERANCE_M
    return {"status": "SEPARATED" if separated else "OVERLAP_OR_UNRESOLVED", "separated": separated,
            "input_valid": True, "candidate_axes": 15, "tested_axes": tested,
            "skipped_near_parallel_cross_axes": skipped, "contact_proven": False, **best}


def _summary():
    return {"passed": False, "status": "INVALID_GEOMETRY", "input_valid": False,
            "mode": GEOMETRY_MODE, "margin_m": WORLD_MARGIN_M, "gap_tolerance_m": GAP_TOLERANCE_M,
            "min_arm_z": None, "minimum_separation_gap_m": None,
            "counters": dict.fromkeys(COUNTER_KEYS, 0), "refinement_records": [], "failures": [],
            "contact_proven": False}


def _validate_colliders(colliders):
    if not isinstance(colliders, (list, tuple)) or len(colliders) != len(SHAPE_BODIES):
        raise ValueError("Exactly ten collision shapes are required")
    checked, seen, roots = [], set(), set()
    for original in colliders:
        item = copy.deepcopy(original)
        path = item["path"]
        parts = PurePosixPath(path).parts
        if not isinstance(path, str) or not path.startswith("/") or len(parts) < 6:
            raise ValueError("Shape path must be an absolute USD prim path")
        body, shape = parts[-4], parts[-2]
        if (parts[-3] != "collisions" or parts[-1] != "mesh" or shape not in SHAPE_BODIES
                or SHAPE_BODIES[shape] != body or item["body"] != body
                or shape in seen or item.get("shape_id", shape) != shape):
            raise ValueError(f"Missing/duplicate/misbound collision shape: {path}")
        if item.get("units", "m") != "m" or item.get("bounds_frame", "body_link") != "body_link":
            raise ValueError("Bounds must be metres in body-link axes")
        lower, upper = _array(item["local_bbox_min"], (3,)), _array(item["local_bbox_max"], (3,))
        if np.any(upper <= lower):
            raise ValueError(f"Invalid bounds: {path}")
        roots.add(parts[:-4])
        seen.add(shape)
        checked.append({"path": path, "shape_id": shape, "body": body,
                        "local_bbox_min": lower.tolist(), "local_bbox_max": upper.tolist()})
    if seen != set(SHAPE_BODIES) or len(roots) != 1:
        raise ValueError("Collision inventory or common robot root mismatch")
    return checked


class GeometryGuard:
    """Fixed-policy, immutable-input all-pair check; same/adjacent bodies exempt."""

    def __init__(self, colliders):
        try:
            self._colliders = _validate_colliders(colliders)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            result = _summary()
            result["failures"].append({"status": "INVALID_GEOMETRY", "message": str(exc)})
            raise GeometryRefinementError(str(exc), result) from exc

    def inspect(self, poses):
        result = _summary()
        try:
            if not isinstance(poses, dict) or set(poses) != set(BODY_NAMES):
                raise ValueError("Poses must contain exactly the seven named rigid-body LINK frames")
            poses = {name: _pose(poses[name]) for name in BODY_NAMES}
            boxes = []
            minimum_z = np.inf
            for item in self._colliders:
                box = box_from_bounds(item["local_bbox_min"], item["local_bbox_max"], poses[item["body"]])
                world_radius = np.abs(box["axes"]) @ box["half_extents"]
                lo, hi = box["center"] - world_radius, box["center"] + world_radius
                if not np.isfinite([lo, hi]).all():
                    raise ValueError("Nonfinite world enclosure")
                if item["body"] != "agv":
                    minimum_z = min(minimum_z, float(lo[2]))
                    if lo[2] < -1e-6:  # Original unexpanded ground rule, unchanged.
                        result["counters"]["ground_failures"] += 1
                        result["failures"].append({"status": "GROUND", "path": item["path"], "minimum_z_m": float(lo[2])})
                boxes.append((item, box, lo - WORLD_MARGIN_M, hi + WORLD_MARGIN_M))
            result["min_arm_z"] = float(minimum_z)
            minimum_gap = np.inf
            for (a, box_a, lo_a, hi_a), (b, box_b, lo_b, hi_b) in itertools.combinations(boxes, 2):
                counts = result["counters"]
                counts["total_shape_pairs"] += 1
                if abs(BODY_NAMES.index(a["body"]) - BODY_NAMES.index(b["body"])) <= 1:
                    counts["exempt_pairs"] += 1
                    continue
                counts["forbidden_pairs"] += 1
                aabb_gap = float(np.maximum(lo_a - hi_b, lo_b - hi_a).max())
                if aabb_gap > GAP_TOLERANCE_M:
                    counts["aabb_separated"] += 1
                    minimum_gap = min(minimum_gap, aabb_gap)
                    continue
                counts["obb_refined"] += 1
                evidence = {"left": a["path"], "right": b["path"], "broad_phase_gap_m": aabb_gap,
                            "broad_phase_overlap_or_near": True, "mode": GEOMETRY_MODE,
                            **pair_separation(box_a, box_b)}
                result["refinement_records"].append(evidence)
                if evidence["separated"]:
                    counts["obb_separated"] += 1
                    minimum_gap = min(minimum_gap, evidence["gap_m"])
                else:
                    counts["unresolved_pairs"] += 1
                    result["failures"].append(evidence)
            result["minimum_separation_gap_m"] = None if not np.isfinite(minimum_gap) else float(minimum_gap)
            result["input_valid"] = True
            result["passed"] = not result["failures"]
            result["status"] = "SEPARATED" if result["passed"] else "OVERLAP_OR_UNRESOLVED"
        except (KeyError, TypeError, ValueError, OverflowError, FloatingPointError) as exc:
            result["passed"] = False
            result["status"] = "INVALID_GEOMETRY"
            result["input_valid"] = False
            result["failures"].append({"status": "INVALID_GEOMETRY", "message": str(exc)})
        return result

    def check(self, poses):
        result = self.inspect(poses)
        if not result["passed"]:
            raise GeometryRefinementError(f"{GEOMETRY_MODE}: {result['status']}", result)
        return result


def merge_counters(total, summary):
    """Return merged counters without modifying either caller-owned object."""
    return {key: int(total.get(key, 0)) + int(summary["counters"][key]) for key in COUNTER_KEYS}


class GeometrySummary:
    """Bounded evidence aggregate: no poses or per-tick pair history."""

    def __init__(self):
        self._result = {"mode": GEOMETRY_MODE, "checks": 0, "failed_checks": 0, "invalid_checks": 0,
                        "input_valid": True,
                        "counters": dict.fromkeys(COUNTER_KEYS, 0), "minimum_arm_z": None,
                        "minimum_separating_gap": None, "representative_obb": None, "failures": []}

    def add(self, result):
        if result["mode"] != GEOMETRY_MODE:
            raise ValueError("Cannot mix geometry policies in one aggregate")
        total = self._result
        total["checks"] += 1
        total["failed_checks"] += int(not result["passed"])
        total["invalid_checks"] += int(not result["input_valid"])
        total["input_valid"] = total["input_valid"] and result["input_valid"]
        total["counters"] = merge_counters(total["counters"], result)
        for source, target in (("min_arm_z", "minimum_arm_z"), ("minimum_separation_gap_m", "minimum_separating_gap")):
            value = result[source]
            if value is not None and (total[target] is None or value < total[target]):
                total[target] = value
        for record in result["refinement_records"]:
            if record["separated"] and (total["representative_obb"] is None
                                        or record["gap_m"] < total["representative_obb"]["gap_m"]):
                total["representative_obb"] = copy.deepcopy(record)
        for failure in result["failures"]:
            if len(total["failures"]) < 8:
                total["failures"].append(copy.deepcopy(failure))

    def summary(self):
        return copy.deepcopy(self._result)


def load_accepted_inputs(urdf):
    """Read existing seven inertials and ten collision meshes; never read visuals.

    No mass/inertia fitting or asset generation occurs. Mesh scale and collision
    origin are applied exactly once by geometry_body_bounds. Returned colliders
    are body-link enclosures, with canonical expected USD shape paths.
    """
    from _cr12_asset_math import geometry_body_bounds

    path = Path(urdf).resolve(strict=True)
    raw = path.read_bytes()
    document = ET.fromstring(raw)
    links = document.findall("link")
    if len(links) != 7 or {link.get("name") for link in links} != set(BODY_NAMES):
        raise ValueError("Accepted derived URDF requires exactly seven bodies")
    bodies, geometries, colliders = {}, {}, []
    for link in links:
        name = link.get("name")
        inertial = link.find("inertial")
        if inertial is None:
            raise ValueError(f"Missing existing inertial: {name}")
        origin = inertial.find("origin")
        com = _array([float(v) for v in origin.get("xyz").split()], (3,))
        if np.any(_array([float(v) for v in origin.get("rpy").split()], (3,)) != 0):
            raise ValueError("Accepted inertial frame must use body axes")
        mass = float(inertial.find("mass").get("value"))
        values = {key: float(value) for key, value in inertial.find("inertia").attrib.items()}
        xx, xy, xz, yy, yz, zz = (values[key] for key in ("ixx", "ixy", "ixz", "iyy", "iyz", "izz"))
        inertia = _array([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]], (3, 3))
        if not np.isfinite(mass) or mass <= 0 or np.linalg.eigvalsh(inertia)[0] <= 0:
            raise ValueError("Invalid existing mass/inertia")
        bodies[name] = {"mass": mass, "com": com.tolist(), "inertia3x3": inertia.tolist(), "inertia": inertia.tolist()}
        geometries[name] = []
        for collision in link.findall("collision"):
            mesh, local = collision.find("geometry/mesh"), collision.find("origin")
            if mesh is None or local is None:
                raise ValueError("Expected explicit mesh collision and body-local origin")
            geometry = {"kind": "collision", "name": collision.get("name"),
                        "filename": str((path.parent / mesh.get("filename")).resolve(strict=True)),
                        "scale": _array([float(v) for v in mesh.get("scale").split()], (3,)).tolist(),
                        "origin_xyz": _array([float(v) for v in local.get("xyz").split()], (3,)).tolist(),
                        "origin_rpy": _array([float(v) for v in local.get("rpy").split()], (3,)).tolist()}
            if np.any(np.asarray(geometry["scale"]) <= 0):
                raise ValueError("Collision mesh scale must be positive")
            lower, upper = geometry_body_bounds(geometry)
            geometries[name].append(geometry)
            colliders.append({"path": f"/World/CR12/{name}/collisions/{geometry['name']}/mesh",
                              "shape_id": geometry["name"], "body": name, "units": "m", "bounds_frame": "body_link",
                              "enclosure_semantics": "mesh_scale_and_collision_origin_applied_once",
                              "local_bbox_min": lower.tolist(), "local_bbox_max": upper.tolist()})
    GeometryGuard(colliders)
    return {"bodies": bodies, "geometries": geometries, "colliders": colliders,
            "source_urdf": str(path), "source_urdf_sha256": hashlib.sha256(raw).hexdigest()}
