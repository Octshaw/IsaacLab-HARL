# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""Shared fixed-CR12 scene construction and the accepted physical guards.

Importing this module does not import Isaac, torch, or CUDA. Runtime imports
remain inside the functions used after AppLauncher creates the application.
No trajectory, pose-controller logic, or task success criteria live here.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import sys


class DriveCheckError(RuntimeError):
    """A classified failure, kept distinct from policy/task performance."""

    def __init__(self, category: str, message: str, **details):
        super().__init__(message)
        self.category = category
        self.details = details


def check_clock(step_before: int, time_before: float, step_after: int, time_after: float, dt: float):
    if (not all(math.isfinite(value) for value in (time_before, time_after, dt)) or dt <= 0
            or step_after != step_before + 1 or abs((time_after - time_before) - dt) > 1e-6):
        raise DriveCheckError(
            "physics_count", "Expected exactly one controlled physics tick",
            before_step=step_before, after_step=step_after, before_time=time_before, after_time=time_after,
        )


class Recorder:
    """One compact result and flushed lifecycle facts; no per-tick tensor archive."""

    def __init__(self):
        self.phase = "arguments"
        self.path = None
        self.result = {
            "status": "RUNNING", "pid": os.getpid(), "work_completed": False,
            "failures": [], "completed_physics_steps": 0, "app_close_requested": False,
            "secondary_failures": [], "diagnostics_complete": False,
            "controlled_step_attempted": False,
        }

    def emit(self, event: str, **facts):
        print("[RUNTIME_CHECK] " + json.dumps(
            _json_safe({"event": event, "stage": event, "phase": self.phase, "pid": os.getpid(), **facts}),
            ensure_ascii=True, allow_nan=False,
        ), flush=True)

    def save(self):
        if self.path is not None:
            # This task-owned result is updated before native shutdown can terminate Python.
            with self.path.open("w", encoding="utf-8") as stream:
                json.dump(_json_safe(self.result), stream, indent=2, ensure_ascii=True, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())

    def fail(self, exc: BaseException, phase: str | None = None):
        failure = {
            "phase": phase or self.phase, "type": type(exc).__name__, "message": str(exc),
            "category": getattr(exc, "category", "runtime_exception"),
            "details": getattr(exc, "details", {}),
        }
        self.result["failures"].append(failure)
        self.result["status"] = "FAILED"
        # A diagnostic I/O failure must never replace the original exception.
        for action in (lambda: self.emit("work_failed", failure=failure,
                                        completed_physics_steps=self.result["completed_physics_steps"]), self.save):
            try:
                action()
            except BaseException as secondary:
                self.secondary(secondary, "failure_recording")

    def secondary(self, exc: BaseException, phase: str):
        self.result["secondary_failures"].append({"phase": phase, "type": type(exc).__name__, "message": str(exc)})
        self.result["status"] = "FAILED"
        try:
            print(f"[CR12_SECONDARY_FAILURE] {phase}: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        except BaseException:
            pass


def _json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _pose_matrix(position, quaternion, *, order="wxyz"):
    import numpy as np
    from _cr12_asset_math import quaternion_matrix

    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = quaternion_matrix(quaternion, order=order)
    matrix[:3, 3] = np.asarray(position, dtype=np.float64)
    return matrix


def _usd_world_matrix(prim):
    import numpy as np
    from pxr import Usd, UsdGeom

    # Gf uses row vectors; the rest of these checks use column-vector transforms.
    return np.asarray(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default()), dtype=np.float64).T


def _rotation_error(first, second):
    import numpy as np

    relative = np.asarray(first).T @ np.asarray(second)
    return math.acos(float(np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)))


def _calibrate_root_anchor(stage, info):
    """Calibrate only the existing world-side frame, once, before physics starts."""
    import numpy as np
    from pxr import Gf, UsdPhysics

    joint = UsdPhysics.FixedJoint.Get(stage, info["fixed_joint"])
    targets = [joint.GetBody0Rel().GetTargets(), joint.GetBody1Rel().GetTargets()]
    if sorted(len(items) for items in targets) != [0, 1]:
        raise DriveCheckError("root_binding", "Fixed root must bind exactly one world side and one body")
    world_side = 0 if not targets[0] else 1
    body_side = 1 - world_side
    body_path = str(targets[body_side][0])
    if body_path != info["body_paths"]["agv"]:
        raise DriveCheckError("root_binding", "Fixed root is not attached to the agv rigid body")

    def frame(side):
        position = getattr(joint, f"GetLocalPos{side}Attr")().Get()
        quaternion = getattr(joint, f"GetLocalRot{side}Attr")().Get()
        imaginary = quaternion.GetImaginary()
        return _pose_matrix(position, [quaternion.GetReal(), *imaginary])

    body_world = _usd_world_matrix(stage.GetPrimAtPath(body_path))
    expected = body_world @ frame(body_side)
    previous = frame(world_side)
    changed = not np.allclose(previous, expected, atol=1e-7, rtol=0.0)
    if changed:
        # Scene-layer edit only: do not save the referenced, already validated USD.
        matrix = Gf.Matrix4d(*expected.T.reshape(-1).tolist())
        quaternion = Gf.Transform(matrix).GetRotation().GetQuat()
        getattr(joint, f"GetLocalPos{world_side}Attr")().Set(Gf.Vec3f(*expected[:3, 3].tolist()))
        getattr(joint, f"GetLocalRot{world_side}Attr")().Set(
            Gf.Quatf(float(quaternion.GetReal()), Gf.Vec3f(*quaternion.GetImaginary()))
        )
    actual = frame(world_side)
    if np.linalg.norm(actual[:3, 3] - expected[:3, 3]) > 1e-6 or _rotation_error(actual[:3, :3], expected[:3, :3]) > 1e-6:
        raise DriveCheckError("root_binding", "World and body-side fixed-joint frames disagree")
    return {"joint": info["fixed_joint"], "world_side": world_side, "changed": changed,
            "before_world_frame": previous.tolist(), "after_world_frame": actual.tolist(),
            "body_world_frame": expected.tolist(), "scene_layer_only": True}


def _read_physics(robot, expected, configuration, recorder, selected_pd):
    import numpy as np
    from _cr12_asset_math import BODY_NAMES, JOINT_NAMES, JOINT_LIMITS, name_indices, checked_physx_body_inertia

    if not robot.is_initialized or not robot.is_fixed_base or robot.num_instances != 1 or robot.num_bodies != 7 or robot.num_joints != 6:
        raise DriveCheckError("asset_parameters", "Expected one initialized fixed-base 7-body/6-DOF articulation")
    body_ids = name_indices(robot.body_names, BODY_NAMES)
    joint_ids = name_indices(robot.joint_names, JOINT_NAMES)
    view = robot.root_physx_view

    def host(tensor):
        values = tensor.detach().cpu().numpy().astype(np.float64, copy=True)
        if not np.isfinite(values).all():
            raise DriveCheckError("asset_parameters", "Non-finite PhysX parameter")
        return values

    masses = host(view.get_masses())[0, body_ids]
    coms = host(view.get_coms())[0, body_ids]
    tensors = host(view.get_inertias())[0, body_ids].reshape(7, 3, 3)
    joint_getters = {
        "position_limits": view.get_dof_limits, "stiffness": view.get_dof_stiffnesses,
        "damping": view.get_dof_dampings, "max_force": view.get_dof_max_forces,
        "max_velocity": view.get_dof_max_velocities, "friction": view.get_dof_friction_coefficients,
        "armature": view.get_dof_armatures,
    }
    raw_joints = {name: host(getter())[0, joint_ids] for name, getter in joint_getters.items()}
    recorder.result["physx_raw_readback"] = {
        "body_order": list(BODY_NAMES), "joint_order": list(JOINT_NAMES), "mass": masses.tolist(),
        "com_local_xyz_xyzw": coms.tolist(), "inertia_about_com_body_axes": tensors.tolist(),
        "inertia_convention": "native full 3x3 about COM, expressed in link/object axes; no second principal rotation",
        "joint_parameters": {name: value.tolist() for name, value in raw_joints.items()},
    }
    recorder.save()
    actual_bodies = {}
    for index, name in enumerate(BODY_NAMES):
        desired = expected[name]
        body_tensor = checked_physx_body_inertia(
            tensors[index], coms[index, 3:7], recorder.result["usd_readback"]["bodies"][name]["diagonalInertia"]
        )
        inertia = np.asarray(desired.get("inertia3x3", desired.get("inertia")), dtype=np.float64)
        if (not np.isclose(masses[index], desired["mass"], rtol=1e-5, atol=1e-6)
                or not np.allclose(coms[index, :3], desired["com"], rtol=0, atol=1e-5)
                or not np.allclose(body_tensor, inertia, rtol=1e-4, atol=1e-6)):
            raise DriveCheckError("asset_parameters", f"PhysX mass/COM/inertia mismatch for {name}",
                                 actual_mass=float(masses[index]), actual_com=coms[index, :3].tolist(),
                                 actual_inertia_body=body_tensor.tolist())
        eigenvalues = np.linalg.eigvalsh(body_tensor)
        if eigenvalues[0] <= 0 or eigenvalues[0] + eigenvalues[1] < eigenvalues[2] - 1e-6:
            raise DriveCheckError("asset_parameters", f"Invalid physical inertia for {name}")
        actual_bodies[name] = {"mass": float(masses[index]), "com_body": coms[index, :3].tolist(),
                               "com_quat_xyzw": coms[index, 3:].tolist(), "inertia_body": body_tensor.tolist()}
    if not np.isclose(masses.sum(), configuration.EXPECTED_TOTAL_MASS_KG, rtol=1e-5, atol=1e-6):
        raise DriveCheckError("asset_parameters", "Total PhysX mass differs from approved total")
    joint_parameters = {}
    for key, getter, desired in (
        ("position_limits", view.get_dof_limits, JOINT_LIMITS),
        ("stiffness", view.get_dof_stiffnesses, selected_pd["stiffness"]),
        ("damping", view.get_dof_dampings, selected_pd["damping"]),
        ("max_force", view.get_dof_max_forces, configuration.EFFORT_LIMITS),
        ("max_velocity", view.get_dof_max_velocities, [configuration.VELOCITY_LIMIT] * 6),
    ):
        actual = raw_joints[key]
        if not np.allclose(actual, desired, rtol=1e-4, atol=1e-6):
            raise DriveCheckError("asset_parameters", f"PhysX {key} differs from approved values", actual=actual.tolist())
        joint_parameters[key] = actual.tolist()
    for key, getter in (("friction", view.get_dof_friction_coefficients), ("armature", view.get_dof_armatures)):
        actual = raw_joints[key]
        if not np.allclose(actual, 0.0, rtol=0, atol=1e-6):
            raise DriveCheckError("asset_parameters", f"Unexpected imported {key}; no unstated friction/rotor inertia", actual=actual.tolist())
        joint_parameters[key] = actual.tolist()
    return body_ids, joint_ids, {"body_order": list(BODY_NAMES), "body_indices": list(body_ids),
                                 "joint_order": list(JOINT_NAMES), "joint_indices": list(joint_ids),
                                 "bodies": actual_bodies, "joints": joint_parameters,
                                 "total_mass": float(masses.sum()), "is_fixed_base": bool(robot.is_fixed_base)}


def _body_poses(robot, body_ids):
    import numpy as np
    from _cr12_asset_math import BODY_NAMES

    positions = robot.data.body_link_pos_w[0, body_ids].detach().cpu().numpy()
    rotations = robot.data.body_link_quat_w[0, body_ids].detach().cpu().numpy()
    if not np.isfinite(positions).all() or not np.isfinite(rotations).all():
        raise DriveCheckError("state_invalid", "Non-finite actual rigid-body link pose")
    return {name: _pose_matrix(position, rotation)
            for name, position, rotation in zip(BODY_NAMES, positions, rotations)}


def _frame_locals(stage, info):
    import numpy as np

    result = {}
    for name, path in info["frame_paths"].items():
        body = "agv" if name in ("elevate", "base_link") else "link_6"
        result[name] = np.linalg.inv(_usd_world_matrix(stage.GetPrimAtPath(info["body_paths"][body]))) @ _usd_world_matrix(stage.GetPrimAtPath(path))
    return result


def _check_frames(stage, info, initial_frames, poses, initial_root):
    import numpy as np

    root = poses["agv"]
    distance = float(np.linalg.norm(root[:3, 3] - initial_root[:3, 3]))
    angle = _rotation_error(root[:3, :3], initial_root[:3, :3])
    if distance > 1e-4 or angle > 1e-4:
        raise DriveCheckError("fixed_root_drift", "Actual agv LINK frame drift", translation_m=distance, rotation_rad=angle)
    current = _frame_locals(stage, info)
    differences = {}
    for name, first in initial_frames.items():
        actual = current[name]
        offset = float(np.linalg.norm(first[:3, 3] - actual[:3, 3]))
        rotation = _rotation_error(first[:3, :3], actual[:3, :3])
        if offset > 1e-5 or rotation > 1e-5:
            raise DriveCheckError("fixed_frame_drift", f"Pure fixed frame changed: {name}", translation_m=offset, rotation_rad=rotation)
        differences[name] = [offset, rotation]
    return distance, angle, differences


def _check_geometry(colliders, poses, offset):
    """Actual-pose AABB guard; an overlap is conservative geometry failure, not contact proof."""
    import numpy as np
    from _cr12_asset_math import BODY_NAMES

    if {item["body"] for item in colliders} != set(BODY_NAMES):
        raise DriveCheckError("geometry_monitor", "Collision enclosure missing an actual rigid body")
    boxes = []
    minimum_arm_z = math.inf
    for item in colliders:
        lower = np.asarray(item["local_bbox_min"], dtype=np.float64)
        upper = np.asarray(item["local_bbox_max"], dtype=np.float64)
        if lower.shape != (3,) or upper.shape != (3,) or not np.isfinite([lower, upper]).all() or np.any(upper <= lower):
            raise DriveCheckError("geometry_monitor", "Invalid actual collision-mesh enclosure", path=item["path"])
        corners = np.asarray(list(itertools.product(*zip(lower, upper))))
        pose = poses[item["body"]]
        world = corners @ pose[:3, :3].T + pose[:3, 3]
        lo, hi = world.min(axis=0), world.max(axis=0)
        if item["body"] != "agv":
            minimum_arm_z = min(minimum_arm_z, float(lo[2]))
            if lo[2] < -1e-6:
                raise DriveCheckError("geometry_guard", "Arm collision enclosure crosses ground z=0", path=item["path"], minimum_z=float(lo[2]))
        boxes.append((item, lo - offset, hi + offset))
    for (left, left_lo, left_hi), (right, right_lo, right_hi) in itertools.combinations(boxes, 2):
        if abs(BODY_NAMES.index(left["body"]) - BODY_NAMES.index(right["body"])) <= 1:
            continue  # same aggregate and six adjacent joint pairs are approved exceptions
        if np.all(np.minimum(left_hi, right_hi) - np.maximum(left_lo, right_lo) > 0):
            raise DriveCheckError("geometry_guard", "Forbidden conservative actual-pose collision enclosures overlap",
                                 left=left["path"], right=right["path"], contact_proven=False)
    return minimum_arm_z


def _flatten_paths(paths):
    flattened = []
    for item in paths:
        if isinstance(item, (list, tuple)):
            flattened.extend(_flatten_paths(item))
        else:
            flattened.append(str(item))
    return flattened


def _validated_root_pose(value):
    import numpy as np
    from _cr12_asset_math import ROOT_TRANSLATION

    if value is None:
        return _pose_matrix(ROOT_TRANSLATION, (1.0, 0.0, 0.0, 0.0))
    pose = np.array(value, dtype=np.float64, copy=True)
    if (pose.shape != (4, 4) or not np.isfinite(pose).all()
            or not np.allclose(pose[3], [0, 0, 0, 1], rtol=0, atol=1e-12)
            or not np.allclose(pose[:3, :3].T @ pose[:3, :3], np.eye(3), rtol=0, atol=1e-10)
            or abs(np.linalg.det(pose[:3, :3])-1) > 1e-10):
        raise DriveCheckError("instance_setup", "Expected an independent finite rigid 4x4 root pose")
    return pose


def _validated_initial_configuration(profile_name, prim_path, pose, q):
    """Pure fixed-profile gate, evaluated before any runtime state write."""
    import numpy as np
    if profile_name == "legacy":
        if q is not None and (np.asarray(q).shape != (6,) or not np.array_equal(q, np.zeros(6))):
            raise DriveCheckError("instance_setup", "Nonzero initialization requires the shared fixed profile")
        return (0.,)*6
    from _cr12_shared_task_profile import PROFILE_NAME, root_pose, initial_q
    if profile_name != PROFILE_NAME or prim_path not in ("/World/CR12_0", "/World/CR12_1"):
        raise DriveCheckError("instance_setup", "Unknown explicit initialization profile or robot path")
    robot_id = int(prim_path[-1])
    expected = root_pose(robot_id)
    values = np.asarray(q, dtype=np.float64)
    if (pose is None or not np.array_equal(pose, expected) or values.shape != (6,)
            or not np.isfinite(values).all() or not np.array_equal(values, initial_q(robot_id))):
        raise DriveCheckError("instance_setup", "Shared layout and initial q must equal the frozen independent inputs")
    return tuple(map(float, values))


def _validate_instance_paths(info, prim_path):
    """CPU validation of an inspected, explicit instance namespace."""
    from _cr12_asset_math import BODY_NAMES, JOINT_NAMES
    bodies, joints = info["body_paths"], info["joint_paths"]
    if (set(bodies) != set(BODY_NAMES) or set(joints) != set(JOINT_NAMES)
            or len(set(bodies.values())) != 7 or len(set(joints.values())) != 6
            or len(info["articulation_roots"]) != 1 or len(info["colliders"]) != 10):
        raise DriveCheckError("instance_mapping", "Expected independent 7/6/1/10 instance mapping")
    paths = [*bodies.values(), *joints.values(), info["fixed_joint"],
             *info["articulation_roots"], *(c["path"] for c in info["colliders"])]
    if any(not isinstance(p, str) or not p.startswith(prim_path + "/") for p in paths):
        raise DriveCheckError("instance_mapping", "A physical path escapes its configured robot root",
                              prim_path=prim_path, paths=paths)
    if sorted(info["fixed_bindings"], key=len) != [[], [bodies["agv"]]]:
        raise DriveCheckError("instance_mapping", "World fixed joint must bind this instance's agv")
    for index, name in enumerate(JOINT_NAMES):
        joint = info["joints"][name]
        if joint["body0"] != [bodies[BODY_NAMES[index]]] or joint["body1"] != [bodies[BODY_NAMES[index+1]]]:
            raise DriveCheckError("instance_mapping", "Joint bindings cross an instance or chain", joint=name)
    for item in info["colliders"]:
        if item["body"] not in bodies or not item["path"].startswith(bodies[item["body"]]+"/"):
            raise DriveCheckError("instance_mapping", "Collider is not under its declared body", collider=item)
    return paths


def _check_instance_composition(scene):
    """Before reset, reject misplaced/escaped bodies independently of later targets."""
    import numpy as np
    from pathlib import Path
    from pxr import UsdPhysics
    from _cr12_pose_control import KinematicModel

    info, stage = scene["info"], scene["stage"]
    _validate_instance_paths(info, scene["prim_path"])
    model = KinematicModel.from_derived_urdf(Path(scene["usd_path"]).parent.parent / "cr12_fixed_lift0.urdf")
    expected = model.forward(np.zeros(6), scene["expected_root_pose"])
    body_checks = {}
    for name, path in info["body_paths"].items():
        prim = stage.GetPrimAtPath(path)
        if not prim.IsValid() or not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            raise DriveCheckError("instance_mapping", "Missing expected rigid body", path=path)
        actual = _usd_world_matrix(prim)
        position_error = float(np.linalg.norm(actual[:3, 3]-expected[name][:3, 3]))
        angle_error = _rotation_error(actual[:3, :3], expected[name][:3, :3])
        if position_error > 1e-5 or angle_error > 1e-5:
            raise DriveCheckError("instance_mapping", "Composed body pose differs from independent spawn/FK expectation",
                                  path=path, expected=expected[name].tolist(), actual=actual.tolist())
        body_checks[name] = {"path": path, "position_error_m": position_error,
                             "rotation_error_rad": angle_error, "world_matrix": actual.tolist()}
    for name, path in {**info["joint_paths"], "root_joint": info["fixed_joint"]}.items():
        joint = UsdPhysics.Joint(stage.GetPrimAtPath(path))
        actual = [list(map(str, joint.GetBody0Rel().GetTargets())),
                  list(map(str, joint.GetBody1Rel().GetTargets()))]
        wanted = info["fixed_bindings"] if name == "root_joint" else [
            info["joints"][name]["body0"], info["joints"][name]["body1"]]
        if actual != wanted:
            raise DriveCheckError("instance_mapping", "Composed joint relationship changed or escaped", path=path, actual=actual)
    return {"prim_path": scene["prim_path"], "body_checks": body_checks,
            "independent_expected_root": scene["expected_root_pose"].tolist(),
            "body_and_joint_paths_verified": True}


def _check_dual_preinit(world, instances):
    import numpy as np
    from pxr import UsdPhysics
    from _cr12_asset_math import BODY_NAMES

    by_path = {scene["prim_path"]: scene for scene in instances}
    if set(by_path) != {"/World/CR12_0", "/World/CR12_1"} or any(not s["strict_instance"] for s in instances):
        raise DriveCheckError("instance_setup", "Only the reviewed fixed dual namespaces are supported")
    profiles = {scene.get("profile_name", "legacy") for scene in instances}
    if len(profiles) != 1:
        raise DriveCheckError("instance_setup", "Both instances must use the same explicit layout profile")
    shared = profiles == {"shared_m2n1"}
    if profiles not in ({"legacy"}, {"shared_m2n1"}):
        raise DriveCheckError("instance_setup", "Unknown dual layout profile")
    for index in (0, 1):
        scene = by_path[f"/World/CR12_{index}"]
        if shared:
            from _cr12_shared_task_profile import root_pose
            expected = root_pose(index)
        else:
            expected = np.eye(4)
            expected[:3, 3] = [0., 2.*index, .053]
        if not np.array_equal(scene["expected_root_pose"], expected):
            raise DriveCheckError("instance_setup", "Dual layout must retain the approved independent root expectations")
        scene["recorder"].result["preinit_instance_mapping"] = _check_instance_composition(scene)
        peer = by_path[f"/World/CR12_{1-index}"]
        if set(scene["contacts"]) != set(BODY_NAMES):
            raise DriveCheckError("contact_monitor", "Each instance requires seven body contact sensors")
        for name, record in scene["contacts"].items():
            if (record["body_path"] != scene["info"]["body_paths"][name]
                    or not set(peer["info"]["body_paths"].values()).issubset(record["targets"])):
                raise DriveCheckError("contact_monitor", "Every sensor must include every peer body")
    if shared:
        # Compose geometry is still q=0, before the authorized nonzero state write.
        poses = [{name: np.asarray(row["world_matrix"], dtype=np.float64)
                  for name, row in by_path[f"/World/CR12_{i}"]["recorder"].result[
                      "preinit_instance_mapping"]["body_checks"].items()} for i in (0, 1)]
        for i in (0, 1):
            scene = by_path[f"/World/CR12_{i}"]
            scene["recorder"].result["preinit_zero_geometry_min_z"] = _check_geometry(
                scene["info"]["colliders"], poses[i], scene["configuration"].CONTACT_OFFSET)
        world["recorder"].result["preinit_zero_cross_geometry"] = check_cross_geometry(
            by_path["/World/CR12_0"], poses[0], by_path["/World/CR12_1"], poses[1])
    paths0, paths1 = (set(scene["info"]["body_paths"].values()) for scene in instances)
    if paths0 & paths1 or instances[0]["robot"] is instances[1]["robot"]:
        raise DriveCheckError("instance_mapping", "Dual objects or physical body sets are shared")
    # Subtree inspection already rejects local filters. Also reject scene-level
    # exclusions that could silently mask the cross-instance physical pairs.
    for prim in world["stage"].Traverse():
        if prim.IsA(UsdPhysics.CollisionGroup):
            raise DriveCheckError("instance_mapping", "Unexpected scene collision group", path=str(prim.GetPath()))
        if prim.HasAPI(UsdPhysics.FilteredPairsAPI):
            targets = UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().GetTargets()
            if targets:
                raise DriveCheckError("instance_mapping", "Unexpected scene pair filtering",
                                      path=str(prim.GetPath()), targets=list(map(str, targets)))


def _check_native_instance(scene):
    from _cr12_asset_math import BODY_NAMES, JOINT_NAMES, name_indices

    robot, info = scene["robot"], scene["info"]
    if not robot.is_initialized or not robot.is_fixed_base or robot.num_instances != 1:
        raise DriveCheckError("instance_mapping", "Expected one initialized fixed articulation per object")
    view = robot.root_physx_view
    prims, links, dofs = (_flatten_paths(getattr(view, name)) for name in ("prim_paths", "link_paths", "dof_paths"))
    body_ids = name_indices(robot.body_names, BODY_NAMES)
    joint_ids = name_indices(robot.joint_names, JOINT_NAMES)
    if (prims != info["articulation_roots"] or len(links) != 7 or len(dofs) != 6
            or len(set(links)) != 7 or len(set(dofs)) != 6
            or [links[i] for i in body_ids] != [info["body_paths"][n] for n in BODY_NAMES]
            or [dofs[i] for i in joint_ids] != [info["joint_paths"][n] for n in JOINT_NAMES]):
        raise DriveCheckError("instance_mapping", "Native view paths/names differ from this instance",
                              prim_paths=prims, link_paths=links, dof_paths=dofs)
    scene["_native_paths"] = list(links)
    return {"prim_path": scene["prim_path"], "articulation_paths": prims,
            "native_body_paths": links, "native_dof_paths": dofs,
            "body_indices": list(body_ids), "joint_indices": list(joint_ids),
            "object_id": id(robot), "view_object_id": id(view), "verified": True}


def check_cross_geometry(scene0, poses0, scene1, poses1):
    """Fresh cross-robot AABBs; all 100 shape pairs, without adjacency exceptions."""
    import numpy as np
    from _cr12_asset_math import BODY_NAMES

    if scene0 is scene1 or scene0["prim_path"] == scene1["prim_path"]:
        raise DriveCheckError("cross_geometry", "Cross check requires two different physical instances")
    sets = []
    for scene, poses in ((scene0, poses0), (scene1, poses1)):
        items = scene["info"]["colliders"]
        offset = float(scene["configuration"].CONTACT_OFFSET)
        if (len(items) != 10 or {item["body"] for item in items} != set(BODY_NAMES)
                or not math.isfinite(offset) or offset != .002 or len({i["path"] for i in items}) != 10):
            raise DriveCheckError("cross_geometry", "Cross check requires all ten colliders and original .002 margin")
        boxes = []
        for item in items:
            lo = np.asarray(item["local_bbox_min"], dtype=np.float64)
            hi = np.asarray(item["local_bbox_max"], dtype=np.float64)
            pose = np.asarray(poses[item["body"]], dtype=np.float64)
            if (not item["path"].startswith(scene["prim_path"]+"/") or lo.shape != (3,) or hi.shape != (3,)
                    or pose.shape != (4, 4) or not np.isfinite([lo, hi]).all() or not np.isfinite(pose).all()
                    or np.any(hi <= lo)):
                raise DriveCheckError("cross_geometry", "Invalid cross-instance collision enclosure", path=item["path"])
            corners = np.asarray(list(itertools.product(*zip(lo, hi))))
            world = corners @ pose[:3, :3].T + pose[:3, 3]
            boxes.append((item, world.min(axis=0)-offset, world.max(axis=0)+offset))
        sets.append(boxes)
    def gap(lo0, hi0, lo1, hi1):
        return float(np.max(np.maximum(lo1-hi0, lo0-hi1)))
    lo0 = np.min([b[1] for b in sets[0]], axis=0)
    hi0 = np.max([b[2] for b in sets[0]], axis=0)
    lo1 = np.min([b[1] for b in sets[1]], axis=0)
    hi1 = np.max([b[2] for b in sets[1]], axis=0)
    coarse_gap = gap(lo0, hi0, lo1, hi1)
    record = {"logical_pairs": 100, "coarse_tests": 1, "coarse_separated": coarse_gap >= 0,
              "fine_pairs_checked": 0, "minimum_axis_gap_m": coarse_gap,
              "gap_basis": "whole_robot_AABB_separation_lower_bound",
              "roots": [scene0["prim_path"], scene1["prim_path"]]}
    if coarse_gap >= 0:
        return record
    minimum = math.inf
    for first, second in itertools.product(*sets):
        a, alo, ahi = first
        b, blo, bhi = second
        value = gap(alo, ahi, blo, bhi)
        record["fine_pairs_checked"] += 1
        minimum = min(minimum, value)
        if value < 0:
            record.update(minimum_axis_gap_m=minimum, gap_basis="checked_shape_pairs")
            raise DriveCheckError("cross_geometry", "Forbidden cross-robot AABB overlap",
                                  left=a["path"], right=b["path"], statistics=record,
                                  left_pose=np.asarray(poses0[a["body"]]).tolist(),
                                  right_pose=np.asarray(poses1[b["body"]]).tolist(), contact_proven=False)
    record.update(minimum_axis_gap_m=minimum, gap_basis="all_shape_pair_axis_separations")
    return record


def _make_contacts(info, ground_path, *, extra_filter_paths=()):
    from _cr12_asset_math import BODY_NAMES
    from isaaclab.sensors import ContactSensor, ContactSensorCfg

    contacts = {}
    extras = list(extra_filter_paths)
    if (len(set(extras)) != len(extras) or set(extras) & set(info["body_paths"].values())
            or ground_path in extras or any(not isinstance(p, str) or not p.startswith("/World/") for p in extras)):
        raise DriveCheckError("contact_monitor", "Peer contact filters must be unique full external body paths")
    for index, name in enumerate(BODY_NAMES):
        targets = {info["body_paths"][other]: other for other_index, other in enumerate(BODY_NAMES)
                   if abs(index - other_index) > 1}
        if name != "agv":
            targets[ground_path] = "ground"
        targets.update({path: path for path in extras})
        sensor = ContactSensor(ContactSensorCfg(
            prim_path=info["body_paths"][name], update_period=0.0, history_length=0,
            filter_prim_paths_expr=list(targets), track_pose=False, track_air_time=False,
        ))
        contacts[name] = _new_contact_record(sensor, targets, info["body_paths"][name])
    return contacts


def _new_contact_record(sensor, targets, body_path):
    """One generation per sensor object, unrelated to task/claim/episode resets."""
    import uuid
    return {"sensor": sensor, "targets": dict(targets), "body_path": body_path,
            "updates": 0, "maximum_force_n": 0.0, "timestamp": 0.0,
            "sensor_object_id": id(sensor), "generation": uuid.uuid4().hex,
            "_time_previous": None, "_failure": None,
            "diagnostics": {"schema": "contact_freshness_v1", "check_attempt_count": 0,
                "update_call_count": 0, "advance_pass_count": 0, "baseline_pass_count": 0,
                "readonly_pass_count": 0, "first_baseline": None, "boundary_samples": {"32": [], "64": []},
                "first_shadow_disagreements": {}, "first_failure": None, "last_sample": None,
                "max_old_increment_error": 0.0, "max_abs_timestamp": 0.0, "max_force_n": 0.0}}


def _contact_tensor_snapshot(value):
    """Copy tiny sensor bookkeeping buffers; never retain a reused tensor alias."""
    import numpy as np
    array = value.detach().cpu().numpy().copy()
    return {"value": array.item() if array.size == 1 else None,
            "dtype": str(value.dtype).split(".")[-1], "device": str(value.device),
            "shape": list(array.shape), "finite": bool(np.isfinite(array).all())}


def _keep_contact_sample(record, sample):
    """Bounded evidence only; no force matrices or per-tick trace on disk."""
    import copy
    diagnostic = record["diagnostics"]
    diagnostic["last_sample"] = copy.deepcopy(sample)
    if sample["mode"] == "baseline" and diagnostic["first_baseline"] is None:
        diagnostic["first_baseline"] = copy.deepcopy(sample)
    time_check = sample.get("time_validation") or {}
    error = time_check.get("old_increment_error")
    if isinstance(error, (int, float)) and math.isfinite(error):
        diagnostic["max_old_increment_error"] = max(diagnostic["max_old_increment_error"], abs(error))
    current = sample.get("current") or {}
    timestamp = current.get("value")
    if isinstance(timestamp, (int, float)) and math.isfinite(timestamp):
        diagnostic["max_abs_timestamp"] = max(diagnostic["max_abs_timestamp"], abs(timestamp))
        for label, saved in diagnostic["boundary_samples"].items():
            if (abs(timestamp-float(label)) <= 2.1/120 and len(saved) < 6
                    and not any(row.get("current", {}).get("value") == timestamp for row in saved)):
                saved.append(copy.deepcopy(sample))
    if isinstance(sample.get("force_n"), (int, float)) and math.isfinite(sample["force_n"]):
        diagnostic["max_force_n"] = max(diagnostic["max_force_n"], sample["force_n"])
    old, new = time_check.get("old_shadow_pass"), time_check.get("passed")
    if type(old) is bool and type(new) is bool and old != new:
        label = "old_reject_new_accept" if new else "old_accept_new_reject"
        diagnostic["first_shadow_disagreements"].setdefault(label, copy.deepcopy(sample))
    if not sample["passed"] and diagnostic["first_failure"] is None:
        diagnostic["first_failure"] = copy.deepcopy(sample)


def _check_contacts(contacts, dt, *, initialize=False, context=None, read_only=False):
    """One update -> data -> frozen checks; readonly explicitly performs no update.

    Numeric recursion validates the sensor's actual represented clock. The
    independently checked physics clock is context, never a replacement clock.
    """
    import copy
    from dataclasses import asdict
    import numpy as np
    from _cr12_contact_time import freeze_snapshot, validate_timestamp

    maximum_force = 0.0
    for name, record in contacts.items():
        if record.get("_failure") is not None:
            raise record["_failure"]
        sensor = record["sensor"]
        diagnostic = record["diagnostics"]
        diagnostic["check_attempt_count"] += 1
        mode = "baseline" if initialize else "readonly" if read_only else "advance"
        sample = {"body_name": name, "body_path": record["body_path"],
            "sensor_object_id": record["sensor_object_id"], "generation": record["generation"],
            "context": copy.deepcopy(context), "mode": mode, "update_dt": float(dt), "update_dt_type": type(dt).__name__,
            "previous": None if record["_time_previous"] is None else asdict(record["_time_previous"]),
            "current": None, "last_update": None, "outdated": None, "time_validation": None,
            "force_n": None, "force_target": None, "passed": False,
            "read_state": {"update": "NOT_READ", "mapping": "NOT_READ", "force": "NOT_READ", "clock": "NOT_READ"},
            "checks": {k: None for k in ("sensor_initialized", "sensor_identity", "call_mode", "mapping",
                       "force_shape", "force_device", "force_finite", "clock_metadata", "time", "force_threshold")}}
        try:
            def require(key, condition, message, category="contact_monitor"):
                sample["checks"][key] = bool(condition)
                if not condition:
                    sample["failed_condition"] = key
                    raise DriveCheckError(category, message, body=name, body_path=record["body_path"])
            require("sensor_initialized", sensor.is_initialized, f"Contact sensor failed to initialize: {name}")
            require("sensor_identity", id(sensor) == record["sensor_object_id"]
                    and sensor.cfg.prim_path == record["body_path"] and sensor.cfg.update_period == 0.0,
                    f"Contact sensor identity or update period changed: {name}")
            require("call_mode", not (initialize and read_only) and math.isfinite(float(dt))
                    and ((mode == "baseline" and dt == 0 and record["_time_previous"] is None)
                         or (mode == "readonly" and dt == 0 and record["_time_previous"] is not None)
                         or (mode == "advance" and dt == 1/120 and record["_time_previous"] is not None)),
                    "Contact call is not one baseline, one physics advance, or a same-tick readonly observation")
            if read_only:
                # A lazy data read must not silently repair stale state.
                before = _contact_tensor_snapshot(sensor._is_outdated)
                sample["outdated"] = before
                require("clock_metadata", before["shape"] == [1] and before["dtype"] == "bool"
                        and before["value"] is False, "Readonly contact would refresh an outdated buffer")
                sample["read_state"]["update"] = "NOT_CALLED_READONLY"
            else:
                diagnostic["update_call_count"] += 1
                sample["read_state"]["update"] = "CALLED"
                sensor.update(dt, force_recompute=True)
                sample["read_state"]["update"] = "RETURNED"
            view = sensor.contact_physx_view
            sensor_paths = _flatten_paths(view.sensor_paths)
            filter_paths = _flatten_paths(view.filter_paths)
            record["resolved_sensor_paths"], record["resolved_filters"] = sensor_paths, filter_paths
            sample["read_state"]["mapping"] = "READ"
            sample.update(sensor_paths=list(sensor_paths), filter_paths=list(filter_paths))
            require("mapping", sensor.num_bodies == 1 and view.sensor_count == 1
                    and sensor_paths == [record["body_path"]] and len(filter_paths) == len(record["targets"])
                    and len(set(filter_paths)) == len(filter_paths) and set(filter_paths) == set(record["targets"])
                    and view.filter_count == len(filter_paths), f"Native contact mapping mismatch: {name}")
            data = sensor.data.force_matrix_w
            sample["read_state"]["force"] = "READ"
            sample["force_shape"] = None if data is None else list(data.shape)
            require("force_shape", data is not None and tuple(data.shape) == (1, 1, len(filter_paths), 3),
                    f"Missing/incorrect filtered force matrix: {name}")
            sample.update(force_dtype=str(data.dtype), force_device=str(data.device))
            forces = data.detach().cpu().numpy().astype(np.float64, copy=True)[0, 0]
            current = _contact_tensor_snapshot(sensor._timestamp)
            last = _contact_tensor_snapshot(sensor._timestamp_last_update)
            outdated = _contact_tensor_snapshot(sensor._is_outdated)
            sample.update(current=current, last_update=last, outdated=outdated)
            sample["read_state"]["clock"] = "READ"
            snapshot = freeze_snapshot(timestamp=current["value"], last_update=last["value"],
                dtype=current["dtype"], device=current["device"], shape=current["shape"],
                last_dtype=last["dtype"], last_device=last["device"], last_shape=last["shape"],
                outdated=outdated["value"], identity=(record["body_path"], str(record["sensor_object_id"])),
                generation=record["generation"])
            time_check = validate_timestamp(record["_time_previous"], snapshot, dt, mode=mode)
            sample["time_validation"] = time_check
            sample["checks"]["time"] = time_check["passed"]
            sample["checks"]["force_finite"] = bool(np.isfinite(forces).all())
            sample["checks"]["force_device"] = str(data.device) == str(sensor.device)
            sample["checks"]["clock_metadata"] = bool(outdated["shape"] == [1] and outdated["dtype"] == "bool"
                and current["device"] == last["device"] == outdated["device"] == str(sensor.device))
            if sample["checks"]["force_finite"]:
                norms = np.linalg.norm(forces, axis=-1)
                index = int(np.argmax(norms))
                sample["force_n"] = float(norms[index])
                sample["force_target"] = filter_paths[index]
                sample["checks"]["force_threshold"] = sample["force_n"] <= .1
                record["maximum_force_n"] = max(record["maximum_force_n"], sample["force_n"])
            for key in ("force_device", "force_finite", "clock_metadata", "time", "force_threshold"):
                require(key, sample["checks"][key],
                        "Forbidden body pair exceeds 0.1 N" if key == "force_threshold" else f"Invalid contact {key}: {name}",
                        "forbidden_contact" if key == "force_threshold" else "contact_monitor")
            record["_time_previous"] = snapshot
            record["timestamp"] = current["value"]
            record["updates"] += int(mode == "advance")
            record["maximum_force_n"] = max(record["maximum_force_n"], sample["force_n"])
            diagnostic[{"baseline": "baseline_pass_count", "advance": "advance_pass_count", "readonly": "readonly_pass_count"}[mode]] += 1
            sample["passed"] = True
            _keep_contact_sample(record, sample)
            maximum_force = max(maximum_force, sample["force_n"])
        except BaseException as exc:
            sample.update(error_type=type(exc).__name__, error=str(exc))
            record["_failure"] = exc
            try:
                _keep_contact_sample(record, sample)
                if isinstance(exc, DriveCheckError):
                    exc.details["contact_sample"] = copy.deepcopy(sample)
            except BaseException:
                pass  # Diagnostics must never replace the primary native/check failure.
            raise
    return maximum_force


def _assert_active(app, sim):
    if not app.is_running() or not sim.is_playing() or sim.is_stopped():
        raise DriveCheckError("early_stop", "Window close, timeline pause, or timeline stop before completion")


def _clock(sim):
    return int(sim.current_time_step_index), float(sim.current_time)


def _joint_state(robot, joint_ids):
    return (robot.data.joint_pos[0, joint_ids].detach().cpu().tolist(),
            robot.data.joint_vel[0, joint_ids].detach().cpu().tolist())


def _contact_summary(contacts):
    import copy
    return copy.deepcopy({name: {key: value for key, value in record.items()
                               if key != "sensor" and not key.startswith("_")}
                          for name, record in contacts.items()})


def _capture_submitted_targets(robot, joint_ids, position_command, velocity_command):
    """Snapshot the exact buffers passed by write_data_to_sim to PhysX, in named order."""
    import numpy as np

    def host(value):
        return value.detach().cpu().numpy().astype(np.float64, copy=True)

    position = host(robot._joint_pos_target_sim[0, joint_ids])
    velocity = host(robot._joint_vel_target_sim[0, joint_ids])
    if (not np.array_equal(position, host(position_command[0]))
            or not np.array_equal(velocity, host(velocity_command[0]))
            or not np.array_equal(position, host(robot.data.joint_pos_target[0, joint_ids]))
            or not np.array_equal(velocity, host(robot.data.joint_vel_target[0, joint_ids]))):
        raise DriveCheckError("target_mismatch", "Submitted PhysX targets differ from the named command/cache")
    if not np.array_equal(host(robot._joint_effort_target_sim[0, joint_ids]), np.zeros(6)):
        raise DriveCheckError("target_mismatch", "Unexpected feed-forward effort command")
    return position.tolist(), velocity.tolist()


def create_fixed_cr12_world(args, app, recorder, resources):
    """Create the one world; no articulation, reset, or native view is created."""
    import isaaclab.sim as sim_utils
    from isaaclab.assets import Articulation
    from isaaclab_assets.robots import rokea_cr12 as configuration
    from isaacsim.core.utils.stage import get_current_stage
    from omni.physx.scripts.physicsUtils import add_ground_plane
    from pxr import Gf, PhysxSchema, Usd, UsdPhysics
    from _cr12_asset_math import ASSET_VERSION, ROOT_TRANSLATION
    from prepare_cr12_fixed_asset import inspect_usd_stage, check_source_collision_bounds
    from _cr12_external_forces import apply_scene_external_forces, read_scene_external_forces, SceneExternalForcesError
    import omni.physx
    import omni.timeline

    recorder.phase = "scene_constructing"
    native_physics = omni.physx.get_physx_interface()
    native_simulation = omni.physx.get_physx_simulation_interface()
    timeline = omni.timeline.get_timeline_interface()
    before_constructor = {
        "physics_running": bool(native_physics.is_running()),
        "timeline_playing": bool(timeline.is_playing()),
        "timeline_stopped": bool(timeline.is_stopped()),
        "attached_stage_id_observed": int(native_simulation.get_attached_stage()),
    }
    recorder.result["external_forces_pre_constructor"] = before_constructor
    if (before_constructor["physics_running"] or before_constructor["timeline_playing"]
            or not before_constructor["timeline_stopped"]):
        raise DriveCheckError("external_forces_setup_config", "Physics/timeline already active before scene construction",
                              actual=before_constructor)
    cfg = sim_utils.SimulationCfg(
        dt=configuration.PHYSICS_DT, render_interval=2, device=args.device, gravity=(0.0, 0.0, -9.81),
        physx=sim_utils.PhysxCfg(solver_type=1),
    )
    sim = sim_utils.SimulationContext(cfg)
    resources["sim"] = sim
    stage = get_current_stage()
    physics_context = sim.get_physics_context()
    timing = {
        "physics_initialized": bool(sim.is_simulating()),
        "physics_running": bool(native_physics.is_running()),
        "timeline_playing": bool(sim.is_playing()),
        "timeline_stopped": bool(sim.is_stopped()),
        "attached_stage_id_observed": int(native_simulation.get_attached_stage()),
        "reset_started": False,
        "callsite": "create_fixed_cr12_scene: immediately after SimulationContext constructor, before robot construction/first reset",
        "source_basis": "SimulationContext constructor creates PhysicsScene; first reset calls play then SimulationManager._warm_start",
        "before_constructor": before_constructor,
        "evidence_limit": "native is_running and timeline/view guards plus audited call order; USD readback is not a native scene-flag getter",
    }
    timing["before_first_physics_initialization"] = (
        not timing["physics_initialized"] and not timing["physics_running"]
        and not timing["timeline_playing"] and timing["timeline_stopped"]
    )
    default_time = Usd.TimeCode.Default()
    resources["external_forces_context"] = (stage, PhysxSchema, UsdPhysics, default_time)
    try:
        setup = apply_scene_external_forces(stage, physics_context.prim_path,
                                           args.external_forces_every_iteration, args.external_forces_source,
                                           timing, PhysxSchema, UsdPhysics, default_time)
    except SceneExternalForcesError as exc:
        recorder.result["external_forces_setup"] = exc.record
        recorder.result["external_forces_readbacks"] = exc.record.get("readbacks", [])
        raise
    recorder.result["external_forces_setup"] = setup
    recorder.result["external_forces_readbacks"] = setup["readbacks"]
    recorder.emit("external_forces_configured", mode=setup["mode"], scene_path=setup["scene_path"],
                  before=setup["before"], after=setup["after"], timing=timing)
    recorder.save()
    if str(sim.device) != args.device or abs(sim.get_physics_dt() - configuration.PHYSICS_DT) > 1e-9:
        raise DriveCheckError("scene_parameters", "Simulation device or dt differs from approved configuration")
    physics_context = sim.get_physics_context()
    physical_backend = {"use_gpu_pipeline": bool(physics_context.use_gpu_pipeline),
                        "gpu_dynamics_enabled": bool(physics_context.is_gpu_dynamics_enabled()),
                        "solver_type": physics_context.get_solver_type()}
    recorder.result["physical_backend"] = physical_backend
    if not physical_backend["use_gpu_pipeline"] or not physical_backend["gpu_dynamics_enabled"] or physical_backend["solver_type"] != "TGS":
        raise DriveCheckError("scene_parameters", "Actual physics backend differs from GPU/TGS", actual=physical_backend)
    if configuration.ASSET_MODEL_ID != ASSET_VERSION:
        raise DriveCheckError("asset_parameters", "Derived asset and articulation configuration version differ")
    recorder.result["asset_version"] = ASSET_VERSION
    stage = get_current_stage()
    ground_root = add_ground_plane(stage, "/World/Ground", "Z", 5.0, Gf.Vec3f(0), Gf.Vec3f(0.35))
    ground_path = str(ground_root) + "/CollisionPlane"
    ground = stage.GetPrimAtPath(ground_path)
    if not ground.IsValid() or not ground.HasAPI(UsdPhysics.CollisionAPI):
        raise DriveCheckError("contact_monitor", "Missing actual local ground-plane collider")
    ground_collision = PhysxSchema.PhysxCollisionAPI.Apply(ground)
    ground_collision.CreateContactOffsetAttr(configuration.CONTACT_OFFSET)
    ground_collision.CreateRestOffsetAttr(configuration.REST_OFFSET)
    light = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.8, 0.8, 0.8))
    light.func("/World/Light", light)
    return {
        "sim": sim, "stage": stage, "cfg": cfg, "configuration": configuration,
        "setup": setup, "ground_path": ground_path, "default_time": default_time,
        "physx_schema": PhysxSchema, "usd_physics": UsdPhysics,
        "recorder": recorder, "_instances": [], "_reset_started": False,
    }


def spawn_fixed_cr12_instance(args, app, recorder, resources, expected, *, world,
                              prim_path="/World/CR12", expected_root_pose=None, pre_physics=None,
                              profile_name="legacy", initial_q=None):
    """Compose one instance before the shared reset; do not construct contacts yet."""
    import copy
    from isaaclab.assets import Articulation
    from prepare_cr12_fixed_asset import inspect_usd_stage, check_source_collision_bounds

    if world["_reset_started"]:
        raise DriveCheckError("instance_setup", "Cannot spawn after shared reset began")
    strict = expected_root_pose is not None
    if not isinstance(prim_path, str) or not prim_path.startswith("/World/") or prim_path.endswith("/"):
        raise DriveCheckError("instance_setup", "Expected an absolute, explicit robot root path")
    if any(item["prim_path"] == prim_path for item in world["_instances"]):
        raise DriveCheckError("instance_setup", "Robot root is already owned", prim_path=prim_path)
    sim, stage, configuration = world["sim"], world["stage"], world["configuration"]
    if strict and stage.GetPrimAtPath(prim_path).IsValid():
        raise DriveCheckError("instance_setup", "Refusing an existing robot root", prim_path=prim_path)
    pose = _validated_root_pose(expected_root_pose)
    initial_values = ((0.,)*6 if profile_name == "legacy" and initial_q is None else
                      _validated_initial_configuration(profile_name, prim_path, pose, initial_q))
    resources["sim"] = sim
    for key in ("physical_backend", "asset_version", "external_forces_pre_constructor",
                "external_forces_setup", "external_forces_readbacks"):
        if recorder is not world["recorder"] and key in world["recorder"].result:
            recorder.result[key] = copy.deepcopy(world["recorder"].result[key])
    selected_pd = recorder.result["pd_selection"]
    cfg = configuration.make_cr12_cfg(
        args.usd_path, prim_path=prim_path,
        stiffness=selected_pd["stiffness"], damping=selected_pd["damping"])
    if strict:
        from _cr12_pose_control import pose_to_wxyz
        position, quaternion = pose_to_wxyz(pose)
        cfg.init_state.pos = tuple(position.tolist())
        cfg.init_state.rot = tuple(quaternion.tolist())
    robot = Articulation(cfg)
    resources["robot"] = robot
    info = inspect_usd_stage(stage, prim_path, expected["bodies"])
    recorder.result["source_collision_bounds"] = check_source_collision_bounds(info, expected)
    recorder.result["usd_readback"] = info
    scene = {
        "sim": sim, "stage": stage, "robot": robot, "info": info, "setup": world["setup"],
        "configuration": configuration, "selected_pd": selected_pd,
        "default_time": world["default_time"], "physx_schema": world["physx_schema"],
        "usd_physics": world["usd_physics"], "world": world, "prim_path": prim_path,
        "expected_root_pose": pose, "strict_instance": strict,
        "profile_name": profile_name, "initial_q": initial_values,
        "recorder": recorder, "resources": resources, "usd_path": args.usd_path,
    }
    if strict:
        recorder.result["preinit_instance_mapping"] = _check_instance_composition(scene)
    recorder.result["root_anchor"] = _calibrate_root_anchor(stage, info)
    scene["frames"] = _frame_locals(stage, info)
    world["_instances"].append(scene)
    if pre_physics is not None:
        pre_physics(stage=stage, sim=sim, robot=robot, info=info)
    return scene


def prepare_fixed_cr12_contacts(scene, resources, *, other_instances=()):
    """Create this body's filters only after every intended peer exists."""
    if scene["world"]["_reset_started"] or "contacts" in scene:
        raise DriveCheckError("contact_monitor", "Contacts may be prepared only once before reset")
    extras = []
    for other in other_instances:
        if other is scene or other["world"] is not scene["world"]:
            raise DriveCheckError("contact_monitor", "Contact peer must be another instance in this world")
        _validate_instance_paths(other["info"], other["prim_path"])
        extras.extend(other["info"]["body_paths"].values())
    contacts = _make_contacts(scene["info"], scene["world"]["ground_path"], extra_filter_paths=extras)
    scene["contacts"] = resources["contacts"] = contacts
    return contacts


def reset_fixed_cr12_world(world, app, recorder, instances):
    """One shared reset after all instances and pre-init opinions are ready."""
    import copy
    from _cr12_external_forces import read_scene_external_forces

    instances = list(instances)
    if (world["_reset_started"] or not instances or len(instances) not in (1, 2)
            or {id(item) for item in instances} != {id(item) for item in world["_instances"]}
            or len({id(item) for item in instances}) != len(instances)
            or any("contacts" not in item for item in instances)):
        raise DriveCheckError("instance_setup", "Reset requires all prepared instances exactly once")
    if len(instances) == 2:
        _check_dual_preinit(world, instances)
    sim, cfg = world["sim"], world["cfg"]
    for scene in instances:
        scene["recorder"].result["simulation"] = {
            "dt": cfg.dt, "render_interval": cfg.render_interval, "gravity": list(cfg.gravity),
            "solver_type": cfg.physx.solver_type, "solver_position_iterations": 8, "solver_velocity_iterations": 2,
            "ground_path": world["ground_path"], "ground_source": "local physicsUtils.add_ground_plane",
            "camera_sensor_created": False, "initial_root_link_xyz": scene["expected_root_pose"][:3, 3].tolist(),
            "collision_policy": "nonadjacent body pairs and moving arm versus ground",
        }
    recorder.phase = "physics_initialize"
    before_reset = _clock(sim)
    recorder.result["external_forces_first_reset_requested_after_setup"] = True
    world["_reset_started"] = True
    sim.reset()
    sim._disable_app_control_on_stop_handle = True
    read_scene_external_forces(world["stage"], world["setup"], "after_first_reset",
                              world["physx_schema"], world["usd_physics"], world["default_time"])
    after_reset = _clock(sim)
    _assert_active(app, sim)
    initialization = {"reset_calls": 1, "before_reset_clock": list(before_reset),
                      "after_reset_clock": list(after_reset), "hidden_settle_steps": 0}
    recorder.result["initialization"] = copy.deepcopy(initialization)
    world["before_reset"], world["after_reset"] = before_reset, after_reset
    for scene in instances:
        scene["after_reset"] = after_reset
        scene["recorder"].result["initialization"] = copy.deepcopy(initialization)
    if len(instances) == 2 and (after_reset[0]-before_reset[0] != 2
            or abs(after_reset[1]-before_reset[1]-2*cfg.dt) > 1e-6):
        raise DriveCheckError("initialization_budget", "Dual world must initialize with exactly two shared physics ticks",
                              before=list(before_reset), after=list(after_reset))
    return after_reset


def read_fixed_cr12_instance(scene, recorder, expected, *, before_native_read=None):
    """Read one already initialized instance, preserving per-instance copies."""
    if "after_reset" not in scene or scene.get("_parameters_read", False):
        raise DriveCheckError("instance_setup", "Initial parameter read requires the one completed reset")
    robot, sim = scene["robot"], scene["sim"]
    if before_native_read is not None:
        before_native_read(robot=robot, sim=sim)
    if scene["strict_instance"]:
        recorder.result["native_instance_mapping"] = _check_native_instance(scene)
    body_ids, joint_ids, readback = _read_physics(
        robot, expected["bodies"], scene["configuration"], recorder, scene["selected_pd"])
    recorder.result["physx_readback"] = readback
    scene.update(body_ids=body_ids, joint_ids=joint_ids, _parameters_read=True)
    if scene["strict_instance"]:
        others = [item for item in scene["world"]["_instances"] if item is not scene and "_native_paths" in item]
        for other in others:
            if (scene["robot"] is other["robot"]
                    or scene["robot"].root_physx_view is other["robot"].root_physx_view
                    or set(scene["_native_paths"]) & set(other["_native_paths"])):
                raise DriveCheckError("instance_mapping", "Articulation views or body sets overlap across robots")
    return scene


def create_fixed_cr12_scene(args, app, recorder, resources, expected, *, pre_physics=None, before_native_read=None):
    """Original single-instance default, composed from the shared phases."""
    world = create_fixed_cr12_world(args, app, recorder, resources)
    scene = spawn_fixed_cr12_instance(args, app, recorder, resources, expected,
                                     world=world, pre_physics=pre_physics)
    prepare_fixed_cr12_contacts(scene, resources)
    scene["sim"].set_camera_view(eye=(3.0, -3.0, 2.4), target=(0.0, 0.0, 1.0))
    reset_fixed_cr12_world(world, app, recorder, [scene])
    return read_fixed_cr12_instance(scene, recorder, expected, before_native_read=before_native_read)


def initialize_fixed_cr12_state(args, recorder, scene, *, geometry_check=None):
    """Write the authorized initial state once, without a physics tick."""
    import numpy as np
    import torch
    from _cr12_asset_math import BODY_NAMES, ROOT_TRANSLATION

    sim, robot = scene["sim"], scene["robot"]
    configuration = scene["configuration"]
    body_ids, joint_ids = scene["body_ids"], scene["joint_ids"]
    info, contacts, after_reset = scene["info"], scene["contacts"], scene["after_reset"]
    if scene.get("_initial_state_write_started", False):
        raise DriveCheckError("initial_state", "Initial joint state may only be written once")
    shared = scene.get("profile_name", "legacy") == "shared_m2n1"
    expected_q = _validated_initial_configuration(scene.get("profile_name", "legacy"),
        scene.get("prim_path", "/World/CR12"), scene.get("expected_root_pose"), scene.get("initial_q"))
    actual_device = torch.device(robot.device)
    if actual_device != torch.device(args.device) or robot.data.joint_pos.device != actual_device or robot.data.joint_vel.device != actual_device:
        raise DriveCheckError("scene_parameters", "Actual articulation joint tensors are not on cuda:0")
    recorder.result["physical_backend"]["joint_tensor_device"] = str(robot.data.joint_pos.device)
    contact_context = {"run_id": str(getattr(args, "output_dir", "UNKNOWN")),
        "robot_id": recorder.result.get("robot_id"), "global_physics_step": 0,
        "host_transition": None, "phase": "initial_zero_warm_contact" if shared else "initial_contact_baseline",
        "control_segment_id": None, "physics_clock": list(_clock(sim)), "controlled_time_s": 0.0}
    # One authorized initial joint-state write. No root or scanner state is written.
    zero = torch.zeros((1, 6), dtype=torch.float32, device=robot.device)
    if shared:
        _check_contacts(contacts, 0.0, initialize=True, context=contact_context)
        recorder.result["warm_zero_contact_summary"] = _contact_summary(contacts)
    position = torch.tensor([expected_q], dtype=torch.float32, device=robot.device) if shared else zero
    scene["_initial_state_write_started"] = True
    robot.write_joint_state_to_sim(position, zero, joint_ids=joint_ids)
    robot.set_joint_position_target(position, joint_ids=joint_ids)
    robot.set_joint_velocity_target(zero, joint_ids=joint_ids)
    robot.reset()
    robot.update(0.0)
    q, dq = _joint_state(robot, joint_ids)
    recorder.result["initial_joint_state"] = {"q_rad": q, "dq_rad_s": dq}
    if not np.allclose(q, expected_q, atol=1e-6, rtol=0) or not np.allclose(dq, 0., atol=1e-6, rtol=0):
        raise DriveCheckError("initial_state", "Initial named position/velocity differs from the frozen initialization")
    poses = _body_poses(robot, body_ids)
    recorder.result["initial_body_link_poses"] = {name: pose.tolist() for name, pose in poses.items()}
    expected_root = scene.get("expected_root_pose")
    if expected_root is None:
        expected_root = _pose_matrix(ROOT_TRANSLATION, (1.0, 0.0, 0.0, 0.0))
    if (np.linalg.norm(poses["agv"][:3, 3] - expected_root[:3, 3]) > 1e-5
            or _rotation_error(poses["agv"][:3, :3], expected_root[:3, :3]) > 1e-5):
        raise DriveCheckError("initial_state", "Initial actual agv LINK pose differs from the approved spawn pose")
    initial_root = poses["agv"].copy()
    if shared:
        from pathlib import Path
        from _cr12_pose_control import KinematicModel
        model = KinematicModel.from_derived_urdf(Path(scene["usd_path"]).parent.parent / "cr12_fixed_lift0.urdf")
        nominal = model.forward(expected_q, expected_root)
        for name in BODY_NAMES:
            if (np.linalg.norm(poses[name][:3, 3]-nominal[name][:3, 3]) > 1e-5
                    or _rotation_error(poses[name][:3, :3], nominal[name][:3, :3]) > 1e-5):
                raise DriveCheckError("initial_state", "Nonzero initialized native link differs from frozen FK", body=name)
    # Old callers retain the original AABB policy. New experiments must opt in.
    checker = _check_geometry if geometry_check is None else geometry_check
    initial_minimum_z = checker(info["colliders"], poses, configuration.CONTACT_OFFSET)
    if not shared:
        _check_contacts(contacts, 0.0, initialize=True, context=contact_context)
    recorder.result["contact_summary"] = _contact_summary(contacts)
    baseline = _clock(sim)
    if baseline != after_reset:
        raise DriveCheckError("physics_count", "Unexpected physics tick during initialization readback")
    recorder.result["initialization"].update({"joint_state_writes": 1, "root_state_writes": 0,
                                           "baseline_clock": list(baseline), "body_names": list(BODY_NAMES)})
    if shared:
        recorder.result["initialization"].update(
            initial_state_source="frozen shared_m2n1 q_initial; not motion from zero",
            nonzero_contact_status="NOT_OBSERVED_UNTIL_FIRST_CONTROLLED_PHYSICS_TICK")
    return {
        "q": q, "dq": dq, "poses": poses, "initial_root": initial_root,
        "initial_minimum_z": initial_minimum_z, "baseline": baseline,
    }
