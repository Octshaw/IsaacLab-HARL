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


def _make_contacts(info, ground_path):
    from _cr12_asset_math import BODY_NAMES
    from isaaclab.sensors import ContactSensor, ContactSensorCfg

    contacts = {}
    for index, name in enumerate(BODY_NAMES):
        targets = {info["body_paths"][other]: other for other_index, other in enumerate(BODY_NAMES)
                   if abs(index - other_index) > 1}
        if name != "agv":
            targets[ground_path] = "ground"
        sensor = ContactSensor(ContactSensorCfg(
            prim_path=info["body_paths"][name], update_period=0.0, history_length=0,
            filter_prim_paths_expr=list(targets), track_pose=False, track_air_time=False,
        ))
        contacts[name] = {"sensor": sensor, "targets": targets, "body_path": info["body_paths"][name],
                          "updates": 0, "maximum_force_n": 0.0, "timestamp": 0.0}
    return contacts


def _check_contacts(contacts, dt, *, initialize=False):
    import numpy as np

    maximum_force = 0.0
    for name, record in contacts.items():
        sensor = record["sensor"]
        if not sensor.is_initialized:
            raise DriveCheckError("contact_monitor", f"Contact sensor failed to initialize: {name}")
        # Force a new read after EVERY real physics tick, independently of lazy data access.
        sensor.update(dt, force_recompute=True)
        view = sensor.contact_physx_view
        sensor_paths = _flatten_paths(view.sensor_paths)
        filter_paths = _flatten_paths(view.filter_paths)
        record["resolved_sensor_paths"] = sensor_paths
        record["resolved_filters"] = filter_paths
        if (sensor.num_bodies != 1 or view.sensor_count != 1 or sensor_paths != [record["body_path"]]
                or len(filter_paths) != len(record["targets"]) or len(set(filter_paths)) != len(filter_paths)
                or set(filter_paths) != set(record["targets"]) or view.filter_count != len(filter_paths)):
            raise DriveCheckError("contact_monitor", f"Native contact mapping mismatch: {name}",
                                 sensor_paths=sensor_paths, filter_paths=filter_paths,
                                 expected_filters=list(record["targets"]))
        data = sensor.data.force_matrix_w
        if data is None or tuple(data.shape) != (1, 1, len(filter_paths), 3):
            raise DriveCheckError("contact_monitor", f"Missing/incorrect filtered force matrix: {name}")
        forces = data.detach().cpu().numpy().astype(np.float64)[0, 0]
        timestamp = float(sensor._timestamp.item())
        last_update = float(sensor._timestamp_last_update.item())
        if (not np.isfinite(forces).all() or bool(sensor._is_outdated.any().item())
                or abs(timestamp - last_update) > 1e-6
                or abs(timestamp - record["timestamp"] - dt) > 1e-6):
            raise DriveCheckError("contact_monitor", f"Stale or invalid contact read: {name}")
        norms = np.linalg.norm(forces, axis=-1)
        index = int(np.argmax(norms))
        force = float(norms[index])
        # Save valid observations, including the force which triggers a stop.
        record["timestamp"] = timestamp
        record["updates"] += int(not initialize)
        record["maximum_force_n"] = max(record["maximum_force_n"], force)
        if force > 0.1:
            raise DriveCheckError("forbidden_contact", "Forbidden body pair exceeds 0.1 N",
                                 body=name, target=record["targets"][filter_paths[index]], force_n=force)
        maximum_force = max(maximum_force, force)
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
    return {name: {key: value for key, value in record.items() if key != "sensor"}
            for name, record in contacts.items()}


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


def create_fixed_cr12_scene(args, app, recorder, resources, expected, *, pre_physics=None, before_native_read=None):
    """Create/reset the accepted fixed scene and read back its physical parameters.

    resources receives live handles immediately so callers can close a partly
    constructed scene on failure. No controlled motion or pose logic runs here.
    """
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
    selected_pd = recorder.result["pd_selection"]
    robot = Articulation(configuration.make_cr12_cfg(
        args.usd_path, stiffness=selected_pd["stiffness"], damping=selected_pd["damping"]
    ))
    info = inspect_usd_stage(stage, "/World/CR12", expected["bodies"])
    recorder.result["source_collision_bounds"] = check_source_collision_bounds(info, expected)
    recorder.result["usd_readback"] = info
    recorder.result["root_anchor"] = _calibrate_root_anchor(stage, info)
    frames = _frame_locals(stage, info)
    if pre_physics is not None:
        pre_physics(stage=stage, sim=sim, robot=robot, info=info)
    contacts = _make_contacts(info, ground_path)
    resources["contacts"] = contacts
    sim.set_camera_view(eye=(3.0, -3.0, 2.4), target=(0.0, 0.0, 1.0))
    recorder.result["simulation"] = {
        "dt": cfg.dt, "render_interval": cfg.render_interval, "gravity": list(cfg.gravity),
        "solver_type": cfg.physx.solver_type, "solver_position_iterations": 8, "solver_velocity_iterations": 2,
        "ground_path": ground_path, "ground_source": "local physicsUtils.add_ground_plane",
        "camera_sensor_created": False, "initial_root_link_xyz": list(ROOT_TRANSLATION),
        "collision_policy": "nonadjacent body pairs and moving arm versus ground",
    }
    recorder.phase = "physics_initialize"
    before_reset = _clock(sim)
    recorder.result["external_forces_first_reset_requested_after_setup"] = True
    sim.reset()
    # This instance must fail on STOP, not enter the framework's resume-wait loop.
    sim._disable_app_control_on_stop_handle = True
    read_scene_external_forces(stage, setup, "after_first_reset", PhysxSchema, UsdPhysics, default_time)
    after_reset = _clock(sim)
    _assert_active(app, sim)
    recorder.result["initialization"] = {"reset_calls": 1, "before_reset_clock": list(before_reset),
                                       "after_reset_clock": list(after_reset), "hidden_settle_steps": 0}
    if before_native_read is not None:
        before_native_read(robot=robot, sim=sim)
    body_ids, joint_ids, readback = _read_physics(robot, expected["bodies"], configuration, recorder, selected_pd)
    recorder.result["physx_readback"] = readback
    return {
        "sim": sim, "stage": stage, "robot": robot, "info": info, "setup": setup,
        "frames": frames, "contacts": contacts, "body_ids": body_ids, "joint_ids": joint_ids,
        "after_reset": after_reset, "configuration": configuration, "selected_pd": selected_pd,
        "default_time": default_time, "physx_schema": PhysxSchema, "usd_physics": UsdPhysics,
    }


def initialize_fixed_cr12_state(args, recorder, scene, *, geometry_check=None):
    """Perform the accepted one-time zero initialization without a physics tick."""
    import numpy as np
    import torch
    from _cr12_asset_math import BODY_NAMES, ROOT_TRANSLATION

    sim, robot = scene["sim"], scene["robot"]
    configuration = scene["configuration"]
    body_ids, joint_ids = scene["body_ids"], scene["joint_ids"]
    info, contacts, after_reset = scene["info"], scene["contacts"], scene["after_reset"]
    actual_device = torch.device(robot.device)
    if actual_device != torch.device(args.device) or robot.data.joint_pos.device != actual_device or robot.data.joint_vel.device != actual_device:
        raise DriveCheckError("scene_parameters", "Actual articulation joint tensors are not on cuda:0")
    recorder.result["physical_backend"]["joint_tensor_device"] = str(robot.data.joint_pos.device)
    # One authorized initial joint-state write. No root or scanner state is written.
    zero = torch.zeros((1, 6), dtype=torch.float32, device=robot.device)
    robot.write_joint_state_to_sim(zero, zero, joint_ids=joint_ids)
    robot.set_joint_position_target(zero, joint_ids=joint_ids)
    robot.set_joint_velocity_target(zero, joint_ids=joint_ids)
    robot.reset()
    robot.update(0.0)
    q, dq = _joint_state(robot, joint_ids)
    recorder.result["initial_joint_state"] = {"q_rad": q, "dq_rad_s": dq}
    if not np.allclose([q, dq], 0.0, atol=1e-6, rtol=0):
        raise DriveCheckError("initial_state", "Initial named joint position/velocity differs from zero")
    poses = _body_poses(robot, body_ids)
    recorder.result["initial_body_link_poses"] = {name: pose.tolist() for name, pose in poses.items()}
    expected_root = _pose_matrix(ROOT_TRANSLATION, (1.0, 0.0, 0.0, 0.0))
    if (np.linalg.norm(poses["agv"][:3, 3] - expected_root[:3, 3]) > 1e-5
            or _rotation_error(poses["agv"][:3, :3], expected_root[:3, :3]) > 1e-5):
        raise DriveCheckError("initial_state", "Initial actual agv LINK pose differs from the approved spawn pose")
    initial_root = poses["agv"].copy()
    # Old callers retain the original AABB policy. New experiments must opt in.
    checker = _check_geometry if geometry_check is None else geometry_check
    initial_minimum_z = checker(info["colliders"], poses, configuration.CONTACT_OFFSET)
    _check_contacts(contacts, 0.0, initialize=True)
    recorder.result["contact_summary"] = _contact_summary(contacts)
    baseline = _clock(sim)
    if baseline != after_reset:
        raise DriveCheckError("physics_count", "Unexpected physics tick during initialization readback")
    recorder.result["initialization"].update({"joint_state_writes": 1, "root_state_writes": 0,
                                           "baseline_clock": list(baseline), "body_names": list(BODY_NAMES)})
    return {
        "q": q, "dq": dq, "poses": poses, "initial_root": initial_root,
        "initial_minimum_z": initial_minimum_z, "baseline": baseline,
    }
