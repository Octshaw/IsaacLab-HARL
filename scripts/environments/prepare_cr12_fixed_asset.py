"""Generate the approved fixed CR12 URDF, or import it in a separate GUI process.

The URDF branch imports only standard-library code and the CPU-only math module.
Simulator imports, including pxr, stay inside the explicitly selected USD branch.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback


def emit(event: str, **facts):
    print("[RUNTIME_CHECK] " + json.dumps(
        {"event": event, "stage": event, "pid": os.getpid(), **facts}, allow_nan=False
    ), flush=True)


def write_summary(directory: Path, name: str, value):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def _rotation(quaternion):
    """USD quaternion -> column-vector rotation, independent of Gf row matrices."""
    import numpy as np
    w = float(quaternion.GetReal())
    x, y, z = map(float, quaternion.GetImaginary())
    if not math.isclose(w*w + x*x + y*y + z*z, 1.0, abs_tol=1e-5):
        raise ValueError("Non-unit USD quaternion")
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ], dtype=np.float64)


def _robot_prims(stage, root_path):
    from pxr import Usd
    root = stage.GetPrimAtPath(root_path)
    if not root.IsValid():
        raise ValueError(f"Missing robot prim: {root_path}")
    return list(Usd.PrimRange(root))


def inspect_usd_stage(stage, robot_root_path, expected_properties, *, check_drives=True):
    """Read composed robot properties; never modify the asset or observed values.

Bounds use actual USD collision mesh points transformed to the owning link axes.
They enclose each convex hull; they are not a claim to read cooked PhysX vertices.
"""
    import numpy as np
    from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics

    def close(actual, expected, label, atol=1e-6, rtol=1e-4):
        values = np.asarray(actual, dtype=np.float64)
        if not np.isfinite(values).all() or not np.allclose(values, expected, atol=atol, rtol=rtol):
            raise ValueError(f"USD {label}: actual={actual}; expected={expected}")

    if UsdGeom.GetStageUpAxis(stage) != "Z":
        raise ValueError("USD is not Z-up")
    close(UsdGeom.GetStageMetersPerUnit(stage), 1.0, "metersPerUnit", atol=1e-9, rtol=0)
    prims = _robot_prims(stage, robot_root_path)
    if any(p.IsInstanceable() or p.IsInstance() for p in prims):
        raise ValueError("Expected a non-instanceable inspection asset")
    bodies = [p for p in prims if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    roots = [p for p in prims if p.HasAPI(UsdPhysics.ArticulationRootAPI)]
    revolutes = [p for p in prims if p.IsA(UsdPhysics.RevoluteJoint)]
    fixed = [p for p in prims if p.IsA(UsdPhysics.FixedJoint)]
    all_joints = [p for p in prims if p.IsA(UsdPhysics.Joint)]
    expected_names = ["agv"] + [f"link_{i}" for i in range(1, 7)]
    if len(bodies) != 7 or sorted(p.GetName() for p in bodies) != sorted(expected_names):
        raise ValueError(f"Expected 7 unique bodies: {[str(p.GetPath()) for p in bodies]}")
    if len(roots) != 1 or len(revolutes) != 6 or len(fixed) != 1 or len(all_joints) != 7:
        raise ValueError(f"Unexpected roots/revolute/fixed/all: {len(roots)}/{len(revolutes)}/{len(fixed)}/{len(all_joints)}")
    body_paths = {p.GetName(): str(p.GetPath()) for p in bodies}
    filtered_pairs = []
    for prim in prims:
        if prim.IsA(UsdPhysics.CollisionGroup):
            raise ValueError(f"Unexpected collision group needs review: {prim.GetPath()}")
        if prim.HasAPI(UsdPhysics.FilteredPairsAPI):
            targets = UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().GetTargets()
            if targets:
                # Adjacent suppression is already expressed by the six joints.
                # Do not silently accept other filters masking prohibited pairs.
                raise ValueError(f"Unexpected additional collision pair filters at {prim.GetPath()}: {targets}")
    root_physx = PhysxSchema.PhysxArticulationAPI(roots[0])
    if not root_physx.GetEnabledSelfCollisionsAttr().Get():
        raise ValueError("Self collision is not enabled")
    body_values = {}
    for prim in bodies:
        name = prim.GetName()
        rigid = UsdPhysics.RigidBodyAPI(prim)
        if not rigid.GetRigidBodyEnabledAttr().Get() or rigid.GetKinematicEnabledAttr().Get():
            raise ValueError(f"Disabled or kinematic body: {name}")
        if not prim.HasAPI(UsdPhysics.MassAPI):
            raise ValueError(f"Missing explicit MassAPI: {name}")
        mass_api = UsdPhysics.MassAPI(prim)
        mass = float(mass_api.GetMassAttr().Get())
        com = list(mass_api.GetCenterOfMassAttr().Get())
        diagonal = list(mass_api.GetDiagonalInertiaAttr().Get())
        principal = mass_api.GetPrincipalAxesAttr().Get()
        rot = _rotation(principal)
        tensor = rot @ np.diag(diagonal) @ rot.T
        want = expected_properties[name]
        close(mass, want["mass"], name + " mass", atol=1e-6, rtol=1e-5)
        close(com, want["com"], name + " COM", atol=1e-5, rtol=0)
        close(tensor, want.get("inertia3x3", want.get("inertia")), name + " inertia")
        body_values[name] = {"mass": mass, "com": com, "diagonalInertia": diagonal,
                             "principalAxes_wxyz": [principal.GetReal(), *principal.GetImaginary()],
                             "inertia3x3": tensor.tolist(), "path": str(prim.GetPath())}
    close(sum(v["mass"] for v in body_values.values()), 82.860365324, "total mass", rtol=1e-5)
    joint_paths, joint_values = {}, {}
    stiffness = [200, 4000, 2000, 200, 1000, 150]
    damping = [20, 550, 166, 12, 37, 7]
    origins = [[.105, 0, 1.062], [0, 0, .35], [0, 0, .76], [0, 0, .54], [0, -.15, 0], [0, 0, .123]]
    for i in range(1, 7):
        name = f"joint_{i}"
        matches = [p for p in revolutes if p.GetName() == name]
        if len(matches) != 1:
            raise ValueError(f"Missing/duplicate joint {name}")
        prim = matches[0]
        joint = UsdPhysics.RevoluteJoint(prim)
        parent = "agv" if i == 1 else f"link_{i-1}"
        child = f"link_{i}"
        body0, body1 = joint.GetBody0Rel().GetTargets(), joint.GetBody1Rel().GetTargets()
        if list(map(str, body0)) != [body_paths[parent]] or list(map(str, body1)) != [body_paths[child]]:
            raise ValueError(f"Joint {name} has unexpected bindings: {body0}, {body1}")
        if not joint.GetJointEnabledAttr().Get() or joint.GetCollisionEnabledAttr().Get():
            raise ValueError(f"Joint {name} disabled or adjacent collisions enabled")
        limit = 2.9671 if i == 2 else 3.0543
        lower, upper = joint.GetLowerLimitAttr().Get(), joint.GetUpperLimitAttr().Get()
        close([lower, upper], np.rad2deg([-limit, limit]), name + " limits", atol=1e-4)
        close(list(joint.GetLocalPos0Attr().Get()), origins[i-1], name + " parent origin", atol=1e-5, rtol=0)
        close(list(joint.GetLocalPos1Attr().Get()), [0, 0, 0], name + " child origin", atol=1e-5, rtol=0)
        axis = np.eye(3)["XYZ".index(joint.GetAxisAttr().Get())]
        axis_parent = _rotation(joint.GetLocalRot0Attr().Get()) @ axis
        close(axis_parent, [0, 1, 0] if i in (2, 3, 5) else [0, 0, 1], name + " physical axis", atol=1e-5, rtol=0)
        close(_rotation(joint.GetLocalRot0Attr().Get()) @ _rotation(joint.GetLocalRot1Attr().Get()).T,
              np.eye(3), name + " zero-pose joint frame agreement", atol=1e-5, rtol=0)
        drive = UsdPhysics.DriveAPI(prim, "angular")
        gains = [drive.GetStiffnessAttr().Get(), drive.GetDampingAttr().Get()]
        if drive.GetTypeAttr().Get() != "force":
            raise ValueError(f"Non-force drive: {name}")
        if check_drives:
            close(gains, np.asarray([stiffness[i-1], damping[i-1]]) * math.pi / 180, name + " USD PD")
        joint_paths[name] = str(prim.GetPath())
        joint_values[name] = {"path": str(prim.GetPath()), "body0": list(map(str, body0)),
                              "body1": list(map(str, body1)), "axis": joint.GetAxisAttr().Get(),
                              "physical_axis_parent": axis_parent.tolist(), "limits_deg": [lower, upper],
                              "stiffness_per_degree": gains[0], "damping_per_degree": gains[1],
                              "max_force": drive.GetMaxForceAttr().Get(), "collisionEnabled": False}
    fixed_api = UsdPhysics.FixedJoint(fixed[0])
    fixed_targets = [list(map(str, fixed_api.GetBody0Rel().GetTargets())), list(map(str, fixed_api.GetBody1Rel().GetTargets()))]
    if sorted(fixed_targets, key=len) != [[], [body_paths["agv"]]] or not fixed_api.GetJointEnabledAttr().Get():
        raise ValueError(f"Not a unique enabled world-agv fixed joint: {fixed_targets}")
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    colliders = []
    for prim in prims:
        if not prim.HasAPI(UsdPhysics.CollisionAPI):
            continue
        if not UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get():
            raise ValueError(f"Disabled collider {prim.GetPath()}")
        ancestor = prim
        while ancestor.IsValid() and not ancestor.HasAPI(UsdPhysics.RigidBodyAPI):
            ancestor = ancestor.GetParent()
        if not ancestor.IsValid() or ancestor.GetName() not in body_paths:
            raise ValueError(f"Collider has no approved body: {prim.GetPath()}")
        mesh = UsdGeom.Mesh(prim)
        if not mesh or not prim.HasAPI(UsdPhysics.MeshCollisionAPI):
            raise ValueError(f"Expected mesh collider at {prim.GetPath()}")
        approximation = UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()
        if approximation != "convexHull":
            raise ValueError(f"Unexpected collision approximation: {approximation}")
        phys = PhysxSchema.PhysxCollisionAPI(prim)
        offsets = [phys.GetContactOffsetAttr().Get(), phys.GetRestOffsetAttr().Get()]
        close(offsets, [.002, 0], "collision offsets", atol=1e-8, rtol=0)
        points = mesh.GetPointsAttr().Get()
        if points is None or len(points) < 4:
            raise ValueError(f"Missing collision points: {prim.GetPath()}")
        transform = cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(ancestor).GetInverse()
        local = np.array([transform.Transform(Gf.Vec3d(*point)) for point in points], dtype=np.float64)
        if not np.isfinite(local).all():
            raise ValueError("Nonfinite collision mesh points")
        colliders.append({"path": str(prim.GetPath()), "body": ancestor.GetName(),
                          "local_bbox_min": local.min(axis=0).tolist(), "local_bbox_max": local.max(axis=0).tolist(),
                          "point_count": len(points), "approximation": approximation,
                          "contact_offset": offsets[0], "rest_offset": offsets[1]})
    if len(colliders) != 10:
        raise ValueError(f"Expected all 10 source collision shapes; found {len(colliders)}")
    frame_paths = {"elevate": body_paths["agv"] + "/elevate",
                   "base_link": body_paths["agv"] + "/base_link",
                   "tool": body_paths["link_6"] + "/tool",
                   "scanner": body_paths["link_6"] + "/tool/scanner"}
    for name, path in frame_paths.items():
        prim = stage.GetPrimAtPath(path)
        if not prim.IsValid() or prim.GetTypeName() != "Xform":
            raise ValueError(f"Missing pure frame {path}")
        if prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.HasAPI(UsdPhysics.MassAPI) or prim.IsA(UsdPhysics.Joint):
            raise ValueError(f"Physical properties on pure frame {path}")
        local = UsdGeom.Xformable(prim).GetLocalTransformation()
        translation = {"elevate": [0, 0, .314], "base_link": [.105, 0, 1.062]}.get(name, [0, 0, 0])
        close(list(local.ExtractTranslation()), translation, name + " frame position", atol=1e-7, rtol=0)
        expected_rotation = np.eye(3)
        if name == "scanner":
            a = 3*math.pi/4
            expected_rotation = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        close(_rotation(local.ExtractRotationQuat()), expected_rotation, name + " frame rotation", atol=1e-7, rtol=0)
    if any(p.IsA(UsdGeom.Camera) for p in prims):
        raise ValueError("Unexpected camera in basic drive asset")
    return {"body_paths": body_paths, "joint_paths": joint_paths, "fixed_joint": str(fixed[0].GetPath()),
            "fixed_bindings": fixed_targets, "articulation_roots": [str(p.GetPath()) for p in roots],
            "frame_paths": frame_paths, "colliders": colliders, "bodies": body_values, "joints": joint_values,
            "metersPerUnit": 1.0, "upAxis": "Z", "self_collision": True,
            "additional_filtered_pairs": filtered_pairs,
            "bounds_source": "composed USD collision mesh points; convex hull enclosure, not cooked vertex readback"}


def _finish_imported_stage(stage):
    """Author only the approved derived frames and collision settings before save."""
    from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics
    deinstanced = []
    # The local URDF wrapper accepts make_instanceable=False but native importer
    # history states that mesh references are made instanceable unconditionally.
    # Author the requested inspection layout in this new derived root layer only.
    for _ in range(10):
        instances = [p for p in stage.Traverse() if p.IsInstanceable() or p.IsInstance()]
        if not instances:
            break
        for prim in instances:
            deinstanced.append(str(prim.GetPath()))
            prim.SetInstanceable(False)
    else:
        raise ValueError("Could not resolve imported nested mesh instances")
    prims = list(stage.Traverse())
    bodies = {p.GetName(): p for p in prims if p.HasAPI(UsdPhysics.RigidBodyAPI)}
    if set(bodies) != {"agv", *[f"link_{i}" for i in range(1, 7)]}:
        raise ValueError("Importer did not preserve the approved body set")
    # Importer 2.3.9+ can author one mesh-merge collider per link. A hull of
    # several source shapes would fill the gaps between them. Preserve the
    # approved one-convex-hull-per-source-collision representation explicitly.
    collision_meshes = {}
    merge_containers = []
    for prim in prims:
        if prim.HasAPI(PhysxSchema.PhysxMeshMergeCollisionAPI):
            collection = PhysxSchema.PhysxMeshMergeCollisionAPI(prim).GetCollisionMeshesCollectionAPI()
            included = Usd.CollectionAPI.ComputeIncludedPaths(collection.ComputeMembershipQuery(), stage)
            meshes = [stage.GetPrimAtPath(path) for path in included if stage.GetPrimAtPath(path).IsA(UsdGeom.Mesh)]
            if not meshes:
                raise ValueError(f"Empty importer collision collection: {prim.GetPath()}")
            collision_meshes.update({str(mesh.GetPath()): mesh for mesh in meshes})
            merge_containers.append(prim)
        elif prim.HasAPI(UsdPhysics.CollisionAPI) and prim.IsA(UsdGeom.Mesh):
            collision_meshes[str(prim.GetPath())] = prim
    counts = {name: 0 for name in bodies}
    for mesh in collision_meshes.values():
        owner = mesh
        while owner.IsValid() and not owner.HasAPI(UsdPhysics.RigidBodyAPI):
            owner = owner.GetParent()
        if not owner.IsValid() or owner.GetName() not in counts:
            raise ValueError(f"Imported collision mesh has no approved owner: {mesh.GetPath()}")
        counts[owner.GetName()] += 1
    expected_counts = {"agv": 3, **{f"link_{i}": 1 for i in range(1, 6)}, "link_6": 2}
    if counts != expected_counts:
        raise ValueError(f"Expected ten individual source collision meshes, got {counts}")
    normalized = []
    for container in merge_containers:
        normalized.append(str(container.GetPath()))
        container.RemoveAPI(PhysxSchema.PhysxMeshMergeCollisionAPI)
        container.RemoveAPI(UsdPhysics.CollisionAPI)
        container.RemoveAPI(UsdPhysics.MeshCollisionAPI)
        container.RemoveAPI(PhysxSchema.PhysxCollisionAPI)
    for mesh in collision_meshes.values():
        UsdPhysics.CollisionAPI.Apply(mesh).CreateCollisionEnabledAttr(True)
        UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr("convexHull")
        phys = PhysxSchema.PhysxCollisionAPI.Apply(mesh)
        phys.CreateContactOffsetAttr(.002)
        phys.CreateRestOffsetAttr(0.0)
    definitions = [
        (str(bodies["agv"].GetPath()) + "/elevate", (0, 0, .314), 0),
        (str(bodies["agv"].GetPath()) + "/base_link", (.105, 0, 1.062), 0),
        (str(bodies["link_6"].GetPath()) + "/tool", (0, 0, 0), 0),
        (str(bodies["link_6"].GetPath()) + "/tool/scanner", (0, 0, 0), 135),
    ]
    for path, translation, angle in definitions:
        if stage.GetPrimAtPath(path).IsValid():
            raise ValueError(f"Refusing to overwrite an existing frame: {path}")
        frame = UsdGeom.Xform.Define(stage, path)
        frame.AddTranslateOp().Set(Gf.Vec3d(*translation))
        frame.AddOrientOp().Set(Gf.Quatf(math.cos(math.radians(angle)/2), Gf.Vec3f(0, 0, math.sin(math.radians(angle)/2))))
    for prim in prims:
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            phys = PhysxSchema.PhysxCollisionAPI.Apply(prim)
            phys.CreateContactOffsetAttr(.002)
            phys.CreateRestOffsetAttr(0.0)
        if prim.IsA(UsdPhysics.RevoluteJoint):
            UsdPhysics.Joint(prim).CreateCollisionEnabledAttr(False)
    return {"deinstanced_mesh_references": deinstanced, "removed_merge_collision_containers": normalized,
            "source_mesh_hull_counts": counts, "mass_or_mesh_points_modified": False}


def check_source_collision_bounds(readback, expected):
    """Match each imported hull input to one original transformed collision mesh."""
    import numpy as np
    from _cr12_asset_math import geometry_body_bounds
    comparisons = []
    for body, geometries in expected["geometries"].items():
        candidates = [item for item in readback["colliders"] if item["body"] == body]
        for geometry in (g for g in geometries if g["kind"] == "collision"):
            lo, hi = geometry_body_bounds(geometry)
            matches = [item for item in candidates
                       if np.allclose(item["local_bbox_min"], lo, atol=1e-5, rtol=0)
                       and np.allclose(item["local_bbox_max"], hi, atol=1e-5, rtol=0)]
            if len(matches) != 1:
                raise ValueError(f"Imported collision bounds do not uniquely match {geometry['name']}: "
                                 f"expected min={lo.tolist()}, max={hi.tolist()}, candidates={candidates}")
            match = matches[0]
            candidates.remove(match)
            comparisons.append({"source": geometry["filename"], "usd_collider": match["path"], "body": body,
                                "max_bounds_error_m": float(max(np.max(np.abs(lo-match["local_bbox_min"])),
                                                                np.max(np.abs(hi-match["local_bbox_max"]))))})
        if candidates:
            raise ValueError(f"Unmatched extra imported collision meshes for {body}")
    return comparisons


def _import_usd(args, app_launcher_type):
    from _windows_runtime_startup import prepare_windows_runtime_args
    from view_scan_assignment import _prepare_cuda_before_app
    from _cr12_asset_math import validate_derived
    if args.device != "cuda:0" or args.headless or args.enable_cameras or args.livestream not in (-1, 0):
        raise ValueError("This import requires GUI/cuda:0, no cameras or livestream")
    urdf_path = Path(args.urdf_path).resolve(strict=True)
    expected = validate_derived(urdf_path)
    usd_dir = urdf_path.parent / "usd"
    if usd_dir.exists():
        raise FileExistsError(f"Use a new derived version; refusing existing USD directory: {usd_dir}")
    preparation = prepare_windows_runtime_args(args, list(sys.argv))
    emit("startup_prepared", **preparation, python=sys.executable, cwd=os.getcwd(), device=args.device)
    emit("pre_app_cuda_begin")
    emit("pre_app_cuda_ready", **_prepare_cuda_before_app(args.device))
    app, failed = None, False
    try:
        emit("app_create_begin")
        launcher = app_launcher_type(args)
        app = launcher.app
        import carb
        from pxr import Sdf, Usd, UsdUtils
        from isaaclab.sim.converters import UrdfConverter, UrdfConverterCfg
        settings = carb.settings.get_settings()
        emit("app_ready", experience=launcher._sim_experience_file,
             kit_log_file=settings.get("/log/file"), vulkan_setting=settings.get("/app/vulkan"),
             headless=launcher._headless, device=args.device, enable_cameras=launcher._enable_cameras,
             livestream=launcher._livestream, xr=launcher._xr)
        if launcher._headless or launcher._enable_cameras or launcher._livestream or launcher._xr:
            raise RuntimeError("Resolved launcher mode differs from GUI without camera/livestream/XR")

        class ApprovedCr12Converter(UrdfConverter):
            def _get_urdf_import_config(self):
                config = super()._get_urdf_import_config()
                config.set_import_inertia_tensor(True)
                config.set_up_vector(0, 0, 1)
                return config

        cfg = UrdfConverterCfg(
            asset_path=str(urdf_path), usd_dir=str(usd_dir), usd_file_name=urdf_path.stem + ".usd",
            force_usd_conversion=True, make_instanceable=False,
            fix_base=True, root_link_name="agv", merge_fixed_joints=False, link_density=0.0,
            collision_from_visuals=False, collider_type="convex_hull",
            replace_cylinders_with_capsules=False, self_collision=True,
            joint_drive=UrdfConverterCfg.JointDriveCfg(
                drive_type="force", target_type="position",
                gains=UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                    stiffness=dict(zip([f"joint_{i}" for i in range(1, 7)], [200, 4000, 2000, 200, 1000, 150])),
                    damping=dict(zip([f"joint_{i}" for i in range(1, 7)], [20, 550, 166, 12, 37, 7])),
                ),
            ),
        )
        emit("usd_import_begin", urdf_path=str(urdf_path), usd_dir=str(usd_dir))
        converter = ApprovedCr12Converter(cfg)
        usd_path = Path(converter.usd_path).resolve(strict=True)
        stage = Usd.Stage.Open(str(usd_path))
        if not stage or not stage.GetDefaultPrim().IsValid():
            raise RuntimeError("Import produced no usable default prim")
        finishing = _finish_imported_stage(stage)
        stage.GetRootLayer().Save()
        # A distinct Stage composes the saved layer and all required references.
        stage.GetRootLayer().Reload(True)
        stage = Usd.Stage.Open(str(usd_path))
        readback = inspect_usd_stage(stage, str(stage.GetDefaultPrim().GetPath()), expected["bodies"])
        readback["source_collision_bounds"] = check_source_collision_bounds(readback, expected)
        layers, assets, unresolved = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(str(usd_path)))
        if unresolved:
            raise ValueError(f"Unresolved USD dependencies: {list(unresolved)}")
        readback["dependencies"] = {"layers": [layer.identifier for layer in layers],
                                    "assets": list(assets), "unresolved": list(unresolved)}
        readback["urdf_path"], readback["usd_path"] = str(urdf_path), str(usd_path)
        readback["expected_bodies"] = expected["bodies"]
        readback["derived_collision_normalization"] = finishing
        write_summary(Path(args.output_dir), "usd_readback.json", readback)
        emit("work_completed", mode="usd", usd_path=str(usd_path), body_count=7, dof_count=6,
             total_mass=sum(v["mass"] for v in readback["bodies"].values()), physics_steps=0)
    except BaseException as error:
        failed = True
        emit("work_failed", mode="usd", error_type=type(error).__name__, error=str(error))
        traceback.print_exc()
    finally:
        if app is not None:
            emit("app_close_begin", work_failed=failed)
            try:
                app.close()
                emit("app_close_returned")
            except BaseException as error:
                failed = True
                emit("close_failure", error_type=type(error).__name__, error=str(error))
                traceback.print_exc()
    return 1 if failed else 0


def main():
    emit("process_start", python=sys.executable, utf8_mode=sys.flags.utf8_mode, cwd=os.getcwd())
    selector = argparse.ArgumentParser(add_help=False)
    selector.add_argument("--stage", required=True, choices=("urdf", "usd"))
    selected, _ = selector.parse_known_args()
    parser = argparse.ArgumentParser(description=__doc__, parents=[selector])
    repository = Path(__file__).resolve().parents[2]
    original = repository / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/rokea_cr12_7DOF.urdf"
    parser.add_argument("--source", type=Path, default=original)
    parser.add_argument("--urdf-path", type=Path, default=original.parent / "derived/fixed_lift0_v1/cr12_fixed_lift0.urdf")
    parser.add_argument("--output-dir", type=Path, required=True)
    launcher_type = None
    if selected.stage == "usd":
        from isaaclab.app import AppLauncher
        launcher_type = AppLauncher
        AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.stage == "urdf":
        start = time.monotonic()
        from _cr12_asset_math import generate_urdf
        result = generate_urdf(args.source, args.urdf_path)
        write_summary(args.output_dir, "urdf_check.json", result)
        elapsed = time.monotonic() - start
        if elapsed > 30:
            raise TimeoutError(f"CPU URDF budget exceeded: {elapsed:.3f}s")
        forbidden = [n for n in sys.modules if n == "torch" or n == "pxr" or n.startswith(("isaaclab", "isaacsim", "omni."))]
        if forbidden:
            raise RuntimeError(f"CPU branch imported runtime modules: {forbidden}")
        emit("work_completed", mode="urdf", derived_path=str(args.urdf_path.resolve()), elapsed_s=elapsed,
             body_count=7, dof_count=6, total_mass=82.860365324, runtime_modules_imported=forbidden)
        return 0
    return _import_usd(args, launcher_type)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        emit("work_failed", error_type=type(error).__name__, error=str(error))
        traceback.print_exc()
        raise SystemExit(1)
