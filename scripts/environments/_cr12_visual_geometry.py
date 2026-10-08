"""Explicit, pre-initialization render visibility for the accepted CR12 asset.

No Isaac/pxr imports at module import time. Identity requires source geometry,
body transform, composition and separate visual/collision prims to agree.
The only authored opinion is visibility=invisible on proven collision leaves.
Nothing is saved to the original USD or promoted to existing entry defaults.
The caller proves pre-physics timing; sealing forbids later layer mutations.
"""
from __future__ import annotations

import hashlib
import json


def _digest(value):
    import numpy as np
    try:
        data = np.asarray(value)
        if data.dtype.kind in "biufcSU":
            header = repr((data.shape, data.dtype.str)).encode("ascii")
            return hashlib.sha256(header + data.tobytes()).hexdigest()
    except (TypeError, ValueError):
        pass
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def display_state(prim):
    from pxr import UsdGeom
    chain, current = [], prim
    while current.IsValid() and not current.IsPseudoRoot():
        image = UsdGeom.Imageable(current)
        if image:
            chain.append({"path": str(current.GetPath()),
                          "visibility": str(image.GetVisibilityAttr().Get()),
                          "purpose": str(image.GetPurposeAttr().Get())})
        current = current.GetParent()
    image = UsdGeom.Imageable(prim)
    return {"effective_visibility": str(image.ComputeVisibility()),
            "effective_purpose": str(image.ComputePurpose()), "ancestors": chain}


def inspect_visual_mapping(stage, root_path, sources):
    """Match each source representation, allowing importer material/group splits.

    Every leaf is transformed into its rigid-body axes before aggregation.
    Triangle multiset equality establishes geometry; names only route candidates.
    """
    import numpy as np
    from pxr import Usd, UsdGeom, UsdPhysics
    from _cr12_visual_source import compare_mesh

    root = stage.GetPrimAtPath(root_path)
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    meshes = [p for p in Usd.PrimRange(root) if p.IsA(UsdGeom.Mesh)]
    records, errors, used = [], [], set()
    for source in sources:
        kind, body, name = source["kind"], source["body"], source["name"]
        container = "visuals" if kind == "visual" else "collisions"
        source_path = root_path + "/" + body + "/" + container + "/" + name
        candidates = [p for p in meshes if str(p.GetPath()) == source_path
                      or str(p.GetPath()).startswith(source_path + "/")]
        if not candidates or (kind == "collision" and len(candidates) != 1):
            errors.append({"source": name, "reason": "unexpected_candidate_count",
                           "candidates": [str(p.GetPath()) for p in candidates]})
            continue
        chunks, counts_parts, indices_parts, leaf_records = [], [], [], []
        offset, role_ok = 0, True
        for prim in candidates:
            mesh = UsdGeom.Mesh(prim)
            owner = prim
            while owner.IsValid() and not owner.HasAPI(UsdPhysics.RigidBodyAPI):
                owner = owner.GetParent()
            if not owner.IsValid() or owner.GetName() != body:
                errors.append({"source": name, "reason": "wrong_body", "path": str(prim.GetPath())})
                continue
            points = np.asarray(mesh.GetPointsAttr().Get(), dtype=np.float64)
            matrix = np.asarray(cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(owner).GetInverse(), dtype=np.float64).T
            chunks.append(points @ matrix[:3, :3].T + matrix[:3, 3])
            counts_parts.append(np.asarray(mesh.GetFaceVertexCountsAttr().Get(), dtype=np.int64))
            indices_parts.append(np.asarray(mesh.GetFaceVertexIndicesAttr().Get(), dtype=np.int64) + offset)
            offset += len(points)
            physics = bool(prim.HasAPI(UsdPhysics.CollisionAPI))
            role_ok = role_ok and physics == (kind == "collision")
            refs, ancestor = [], prim
            while ancestor.IsValid() and not ancestor.IsPseudoRoot():
                for key in ("references", "payload"):
                    value = ancestor.GetMetadata(key)
                    if value:
                        refs.append({"prim": str(ancestor.GetPath()), "field": key, "value": str(value)})
                if ancestor == root:
                    break
                ancestor = ancestor.GetParent()
            leaf_records.append({"path": str(prim.GetPath()), "mesh_to_body": matrix.tolist(),
                "has_collision_api": physics, "point_count": len(points), "face_count": len(counts_parts[-1]),
                "specs": [{"layer": s.layer.identifier, "path": str(s.path)} for s in prim.GetPrimStack()],
                "point_specs": [{"layer": s.layer.identifier, "path": str(s.path)} for s in mesh.GetPointsAttr().GetPropertyStack(Usd.TimeCode.Default())],
                "references": refs, "subdivision": str(mesh.GetSubdivisionSchemeAttr().Get()),
                "orientation": str(mesh.GetOrientationAttr().Get()), "hole_count": len(mesh.GetHoleIndicesAttr().Get() or []),
                "double_sided": mesh.GetDoubleSidedAttr().Get(), **display_state(prim)})
            used.add(str(prim.GetPath()))
        if len(chunks) != len(candidates):
            continue
        comparison = compare_mesh(source, np.concatenate(chunks), np.concatenate(counts_parts), np.concatenate(indices_parts))
        path = str(candidates[0].GetPath()) if kind == "collision" else source_path
        anchor = stage.GetPrimAtPath(path)
        state = display_state(anchor)
        if any(leaf["effective_visibility"] != "inherited" for leaf in leaf_records) and kind == "visual":
            state["effective_visibility"] = "some_visual_leaves_hidden"
        render_surface_ok = bool(comparison.get("winding_match") and all(
            leaf["subdivision"] == "none" and leaf["hole_count"] == 0
            and leaf["orientation"] == "rightHanded" for leaf in leaf_records))
        record = {"name": name, "kind": kind, "body": body, "path": path,
                  "paths": [r["path"] for r in leaf_records], "source": source["filename"],
                  "scale": source["scale"], "origin_xyz": source["origin_xyz"], "origin_rpy": source["origin_rpy"],
                  "comparison": comparison, "has_collision_api": any(r["has_collision_api"] for r in leaf_records),
                  "role_schema_matches": role_ok, "render_surface_matches_control_mesh": render_surface_ok,
                  "leaves": leaf_records, **state}
        records.append(record)
        if not (comparison.get("points_match") and comparison.get("triangle_geometry_match") and role_ok and render_surface_ok):
            errors.append({"source": name, "reason": "geometry_role_or_surface_mismatch", "comparison": comparison})
    extras = [str(p.GetPath()) for p in meshes if str(p.GetPath()) not in used]
    if extras:
        errors.append({"reason": "unmapped_robot_mesh", "paths": extras})
    return {"pass": len(records) == 20 and not errors, "meshes": records, "errors": errors,
            "source_representation_count": len(records), "mesh_count": len(meshes),
            "layer_stack": [x.identifier for x in stage.GetLayerStack()],
            "comparison_frame": "body LINK, metres; source scale and origin applied once"}


def select_collision_leaves(mapping):
    """Never hide a body, parent, correct visual, or shared visual/collider."""
    if not mapping.get("pass"):
        raise ValueError("Source/composition mapping must pass before rendering changes")
    records = mapping["meshes"]
    visuals = {r["name"]: r for r in records if r["kind"] == "visual"}
    result = []
    for item in records:
        if item["kind"] != "collision":
            continue
        visual = visuals.get(item["name"].removesuffix("_collision") + "_visual")
        if (visual is None or visual["body"] != item["body"] or visual["path"] == item["path"]
                or visual["has_collision_api"] or not item["has_collision_api"]
                or not item["role_schema_matches"] or not visual["role_schema_matches"]
                or not item["path"].endswith("/mesh")
                or "/collisions/" not in item["path"]
                or visual["effective_visibility"] != "inherited"):
            raise ValueError("Separate, visible source visual and collision leaf required")
        for r in (item, visual):
            if mapping.get("validation_mode") == "preinit_accepted_source_metadata_v1":
                identity_ok = r.get("metadata_identity_matches") is True
            else:
                identity_ok = (r["comparison"].get("points_match")
                               and r["comparison"].get("triangle_geometry_match"))
            if not identity_ok:
                raise ValueError("Geometry source identity is unresolved")
        result.append(item["path"])
    if len(result) != 10 or len(set(result)) != 10:
        raise ValueError("Exactly ten distinct source collision leaves required")
    return result


def inspect_preinit_mapping(stage, root_path, derived_urdf):
    """Check accepted input identity without repeating the previous mesh audit.

    Caller protects the accepted asset files. This reads only URDF metadata,
    composed transforms, source property specs and schemas, never mesh points.
    A metadata PASS is not a new vertex/triangle or material comparison.
    """
    import math
    from pathlib import Path
    import xml.etree.ElementTree as ET
    import numpy as np
    from pxr import Usd, UsdGeom, UsdPhysics

    expected_bodies = {"agv": "agv", "elevate": "agv", "base_link": "agv",
                       **{f"link_{i}": f"link_{i}" for i in range(1, 7)}, "scanner": "link_6"}
    accepted_geometry_layer = (Path(derived_urdf).resolve().parent / "usd" / "configuration"
                               / "cr12_fixed_lift0_base.usd")
    document = ET.parse(derived_urdf).getroot()
    root = stage.GetPrimAtPath(root_path)
    if not root:
        raise ValueError("Accepted robot root is missing")
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    meshes = {str(p.GetPath()): p for p in Usd.PrimRange(root) if p.IsA(UsdGeom.Mesh)}
    records, errors, used, identities = [], [], set(), set()
    for body_node in document.findall("link"):
        body = body_node.get("name")
        for kind in ("visual", "collision"):
            for node in body_node.findall(kind):
                name = node.get("name", "")
                shape = name.removesuffix("_" + kind)
                if (name != shape + "_" + kind or expected_bodies.get(shape) != body
                        or (shape, kind) in identities):
                    raise ValueError("Unexpected or duplicate accepted source representation")
                identities.add((shape, kind))
                mesh_node, origin = node.find("geometry/mesh"), node.find("origin")
                if mesh_node is None:
                    raise ValueError("Accepted source representation must be a mesh")
                filename = mesh_node.get("filename", "")
                scale = np.asarray([float(x) for x in mesh_node.get("scale", "1 1 1").split()])
                xyz = np.asarray([float(x) for x in (origin.get("xyz", "0 0 0") if origin is not None else "0 0 0").split()])
                rpy = np.asarray([float(x) for x in (origin.get("rpy", "0 0 0") if origin is not None else "0 0 0").split()])
                if (not filename or any(v.shape != (3,) or not np.isfinite(v).all() for v in (scale, xyz, rpy))
                        or not np.array_equal(scale, [.001, .001, .001])):
                    raise ValueError("Invalid accepted source scale/origin")
                cr, cp, cy = map(math.cos, rpy)
                sr, sp, sy = map(math.sin, rpy)
                rotation = np.array([[cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr],
                                     [sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr],
                                     [-sp, cp*sr, cp*cr]])
                expected = np.eye(4)
                expected[:3, :3], expected[:3, 3] = rotation @ np.diag(scale), xyz
                container = "visuals" if kind == "visual" else "collisions"
                source_path = f"{root_path}/{body}/{container}/{name}"
                path = source_path + "/mesh"
                prim = meshes.get(path)
                candidates = [p for p in meshes if p == source_path or p.startswith(source_path + "/")]
                if prim is None or candidates != [path]:
                    errors.append({"source": name, "reason": "accepted_single_mesh_missing_or_changed", "paths": candidates})
                    continue
                owner = prim
                while owner and not owner.HasAPI(UsdPhysics.RigidBodyAPI):
                    owner = owner.GetParent()
                if not owner or str(owner.GetPath()) != root_path + "/" + body:
                    errors.append({"source": name, "reason": "wrong_rigid_body"})
                    continue
                actual = np.asarray(cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(owner).GetInverse(), dtype=np.float64).T
                point_specs = [{"layer": s.layer.identifier, "path": str(s.path)}
                               for s in UsdGeom.Mesh(prim).GetPointsAttr().GetPropertyStack(Usd.TimeCode.Default())]
                source_spec = "/meshes/" + Path(filename).stem + "/mesh.points"
                source_matches = bool(point_specs) and all(
                    s["path"] == source_spec and Path(s["layer"]).resolve() == accepted_geometry_layer
                    for s in point_specs)
                transform_matches = bool(np.isfinite(actual).all() and np.allclose(actual, expected, rtol=0, atol=1e-7))
                has_collision = bool(prim.HasAPI(UsdPhysics.CollisionAPI))
                role_ok = has_collision == (kind == "collision")
                state = display_state(prim)
                identity_ok = source_matches and transform_matches and role_ok
                used.add(path)
                records.append({"name": name, "kind": kind, "body": body,
                    "path": path if kind == "collision" else source_path, "paths": [path],
                    "source": filename, "scale": scale.tolist(), "origin_xyz": xyz.tolist(), "origin_rpy": rpy.tolist(),
                    "has_collision_api": has_collision, "role_schema_matches": role_ok,
                    "metadata_identity_matches": identity_ok,
                    "comparison": {"status": "NOT_REPEATED_PREVIOUS_ACCEPTED_AUDIT"},
                    "leaves": [{"path": path, "point_specs": point_specs, "mesh_to_body": actual.tolist(),
                                "source_spec_matches": source_matches, "transform_matches": transform_matches,
                                "transform_max_error": float(np.max(np.abs(actual - expected))), **state}], **state})
                if not identity_ok:
                    errors.append({"source": name, "reason": "source_transform_or_schema_mismatch"})
    expected_identities = {(shape, kind) for shape in expected_bodies for kind in ("visual", "collision")}
    if identities != expected_identities:
        raise ValueError("Exactly twenty accepted source representations required")
    extras = sorted(set(meshes) - used)
    if extras:
        errors.append({"reason": "unmapped_robot_mesh", "paths": extras})
    return {"pass": len(records) == 20 and len(meshes) == 20 and not errors, "meshes": records, "errors": errors,
            "source_representation_count": len(records), "mesh_count": len(meshes),
            "validation_mode": "preinit_accepted_source_metadata_v1",
            "source_geometry_evidence": "previous accepted audit; not repeated",
            "accepted_geometry_layer": str(accepted_geometry_layer),
            "comparison_frame": "body LINK, metres; source scale and origin applied once"}


def physical_snapshot(stage, root_path):
    """Compact physical/schema/transform/topology fingerprint; excludes display.

This is composed USD evidence, not a claim to read cooked PhysX hull vertices.
"""
    from pxr import Usd, UsdGeom, UsdPhysics
    result = {}
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root_path)):
        attrs = {}
        for attr in prim.GetAttributes():
            name = attr.GetName()
            if (name.startswith(("physics:", "physx", "drive:", "xformOp"))
                    or name in ("points", "faceVertexCounts", "faceVertexIndices", "holeIndices", "orientation")):
                attrs[name] = _digest(attr.Get())
        rels = {r.GetName(): list(map(str, r.GetTargets())) for r in prim.GetRelationships()
                if r.GetName().startswith(("physics:", "physx"))}
        result[str(prim.GetPath())] = {"type": prim.GetTypeName(), "active": prim.IsActive(),
            "schemas": list(prim.GetAppliedSchemas()), "attributes": attrs, "relationships": rels}
    return result


class CollisionVisualOverride:
    """Apply once before physics, seal, then only read during the lifecycle.

    Timing is a caller-verified precondition, not inferred from a USD Stage.
    Revoke remains available solely before sealing on an uninitialized stage.
    There is deliberately no cleanup, context-manager exit or destructor.
    """

    def __init__(self, stage, mapping):
        self.stage = stage
        self.paths = select_collision_leaves(mapping)
        self.visual_paths = [path for r in mapping["meshes"] if r["kind"] == "visual"
                             for path in r.get("paths", [r["path"]])]
        self.root_path = self.paths[0].split("/collisions/", 1)[0].rsplit("/", 1)[0]
        self.layer = None
        self._previous_paths = None
        self.apply_count = 0
        self.sealed = False
        self._stable_state = None

    def apply(self, *, before_first_physics_initialization=False):
        from pxr import Sdf, Usd, UsdGeom, UsdPhysics
        if self.sealed or self.apply_count:
            raise ValueError("Override already applied; reapplication is forbidden")
        if before_first_physics_initialization is not True:
            raise ValueError("Caller must verify before_first_physics_initialization=True")
        session = self.stage.GetSessionLayer()
        self._previous_paths = list(session.subLayerPaths)
        layer = Sdf.Layer.CreateAnonymous("cr12_collision_render_visibility.usda")
        self.layer = layer
        self.apply_count += 1
        session.subLayerPaths = [layer.identifier, *self._previous_paths]
        try:
            with Usd.EditContext(self.stage, layer):
                for path in self.paths:
                    prim = self.stage.GetPrimAtPath(path)
                    if not prim:
                        raise ValueError("Expected a leaf mesh")
                    for child in prim.GetChildren():
                        if (not child.IsA(UsdGeom.Subset) or child.GetChildren()
                                or set(child.GetAppliedSchemas()) - {"MaterialBindingAPI"}
                                or child.HasAPI(UsdPhysics.CollisionAPI) or child.HasAPI(UsdPhysics.RigidBodyAPI)):
                            raise ValueError("Only nonphysical face/material subsets may be below a collision mesh")
                    if not UsdGeom.Imageable(prim).CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible):
                        raise ValueError("Visibility authoring failed")
            self.verify()
        except BaseException:
            self.revoke()
            raise
        return {"mode": "collision_leaf_visibility_v1", "layer": layer.identifier,
                "properties": {p: "visibility=invisible" for p in self.paths}, "saved_to_disk": False,
                "apply_count": self.apply_count, "before_first_physics_initialization": True,
                "sealed": self.sealed}

    def verify(self):
        from pxr import UsdGeom
        if self.layer is None:
            raise ValueError("No applied override")
        if list(self.stage.GetSessionLayer().subLayerPaths).count(self.layer.identifier) != 1:
            raise ValueError("Override layer is missing or duplicated in session composition")
        for path in self.paths:
            if UsdGeom.Imageable(self.stage.GetPrimAtPath(path)).ComputeVisibility() != UsdGeom.Tokens.invisible:
                raise ValueError("Visibility opinion did not take effect")
        for path in self.visual_paths:
            prim = self.stage.GetPrimAtPath(path)
            if not prim or str(UsdGeom.Imageable(prim).ComputeVisibility()) != "inherited":
                raise ValueError("Correct source visual is no longer visible")
        # Only ancestor over specs and the ten approved token attributes allowed.
        found = []
        def visit(path):
            if str(path) == "/":
                return
            spec = self.layer.GetObjectAtPath(path)
            if getattr(spec, "name", None) == "visibility":
                found.append(str(path.GetPrimPath()))
            elif path.IsPropertyPath():
                raise ValueError("Unexpected render override property")
            elif hasattr(spec, "specifier"):
                from pxr import Sdf
                if spec.specifier != Sdf.SpecifierOver or spec.typeName:
                    raise ValueError("Render override must not define new typed/physical prims")
        self.layer.Traverse("/", visit)
        if sorted(found) != sorted(self.paths):
            raise ValueError("Render layer whitelist differs")
        return True

    def _read_stable_state(self):
        """Read only our layer and robot composition arcs, not all Kit layers."""
        from pxr import Usd
        arcs = []
        keys = {"references", "payload", "inheritPaths", "specializes", "variantSelection", "instanceable"}
        root = self.stage.GetPrimAtPath(self.root_path)
        if not root:
            raise ValueError("Robot root disappeared")
        for prim in Usd.PrimRange(root):
            specs = []
            for spec in prim.GetPrimStack():
                opinions = {key: str(spec.GetInfo(key)) for key in sorted(set(spec.ListInfoKeys()) & keys)}
                if opinions:
                    specs.append({"layer": spec.layer.identifier, "path": str(spec.path), "arcs": opinions})
            arcs.append({"path": str(prim.GetPath()), "arcs": specs})
        return {"layer": self.layer.identifier,
                "layer_sha256": hashlib.sha256(self.layer.ExportToString().encode("utf-8")).hexdigest(),
                "robot_composition_sha256": hashlib.sha256(json.dumps(arcs, sort_keys=True).encode("utf-8")).hexdigest()}

    def seal_before_physics_initialization(self):
        """Lock mutation before the caller starts the first physics lifecycle."""
        if self.sealed:
            raise ValueError("Override is already sealed")
        self.verify()
        self._stable_state = self._read_stable_state()
        self.sealed = True
        return self.verify_stable("sealed_before_first_physics_initialization")

    def verify_stable(self, phase):
        """Read-only key-stage check; never revokes/reapplies on failure."""
        if not self.sealed:
            raise ValueError("Seal the override before runtime stability checks")
        self.verify()
        current = self._read_stable_state()
        if current != self._stable_state:
            raise ValueError("Sealed visual layer or robot composition changed")
        return {"phase": str(phase), "pass": True, "apply_count": self.apply_count,
                "sealed": True, "collision_leaves_invisible": len(self.paths),
                "visuals_visible": len(self.visual_paths), "saved_to_disk": False, **current}

    def revoke(self):
        if self.sealed:
            raise ValueError("Sealed override cannot be revoked during initialization, runtime or cleanup")
        if self.layer is None:
            return
        session = self.stage.GetSessionLayer()
        current = list(session.subLayerPaths)
        if current != [self.layer.identifier, *self._previous_paths]:
            raise ValueError("Session composition changed externally; cannot undo safely")
        session.subLayerPaths = self._previous_paths
        self.layer = None

