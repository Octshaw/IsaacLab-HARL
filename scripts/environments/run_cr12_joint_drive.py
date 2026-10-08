# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""Bounded, monitored CR12 joint drive using a previously inspected derived USD.

Importing this module performs no Isaac, torch, CUDA, or filesystem operation.
The accepted Windows startup functions are reused without changing them.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys


from _cr12_runtime_support import (
    DriveCheckError,
    check_clock,
    Recorder,
    _json_safe,
    _pose_matrix,
    _usd_world_matrix,
    _rotation_error,
    _calibrate_root_anchor,
    _read_physics,
    _body_poses,
    _frame_locals,
    _check_frames,
    _check_geometry,
    _flatten_paths,
    _make_contacts,
    _check_contacts,
    _assert_active,
    _clock,
    _joint_state,
    _contact_summary,
    _capture_submitted_targets,
    create_fixed_cr12_scene,
    initialize_fixed_cr12_state,
)


def check_joint_sample(q, dq, reference, limits, sample_time: float, ramp_start: float | None):
    """Pure checking logic; reference is evaluated at the measured sample time."""
    if any(len(values) != 6 for values in (q, dq, reference, limits)):
        raise DriveCheckError("state_invalid", "Expected six named joint coordinates")
    if (not math.isfinite(sample_time)
            or (ramp_start is not None and not math.isfinite(ramp_start))
            or not all(math.isfinite(float(value)) for values in (q, dq, reference) for value in values)):
        raise DriveCheckError("state_invalid", "Non-finite joint state or reference")
    errors = [abs(float(actual) - float(desired)) for actual, desired in zip(q, reference)]
    speeds = [abs(float(value)) for value in dq]
    for index, (value, bounds) in enumerate(zip(q, limits)):
        if len(bounds) != 2 or not all(math.isfinite(float(bound)) for bound in bounds) or bounds[0] >= bounds[1]:
            raise DriveCheckError("state_invalid", "Invalid original hard joint limit", joint=index + 1)
        if value < bounds[0] - 1e-3 or value > bounds[1] + 1e-3:
            raise DriveCheckError("joint_limit", "Original hard joint limit exceeded", joint=index + 1)
    if any(error > math.radians(0.5) for error in errors):
        raise DriveCheckError("tracking", "Joint tracking error exceeds 0.5 degrees", errors_rad=errors)
    if any(speed > 0.25 for speed in speeds):
        raise DriveCheckError("tracking", "Joint speed exceeds 0.25 rad/s", speeds_rad_s=speeds)
    if sample_time >= 5.0 - 1e-8 and any(speed > 0.01 for speed in speeds):
        raise DriveCheckError("tracking", "Last-second holding velocity exceeds 0.01 rad/s", speeds_rad_s=speeds)
    if abs(sample_time - 2.0) <= 1e-7:
        if ramp_start is None or float(q[1]) - ramp_start < math.radians(1.0):
            raise DriveCheckError("no_progress", "Less than one degree progress one second into the ramp")
    return errors, speeds


def _parse_args(app_launcher_type):
    from _cr12_hold_diagnostics import add_diagnostic_arguments
    from _cr12_external_forces import add_external_forces_arguments, external_forces_source

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd-path", type=Path, required=True, help="Explicit previously inspected derived USD.")
    parser.add_argument("--output-dir", type=Path, required=True, help="This attempt's evidence directory.")
    parser.add_argument("--physics_steps", type=int, default=720)
    parser.add_argument("--diagnose-state-consistency", action="store_true",
                        help="Observe cached/native/link state at the same tick; retain all original criteria.")
    add_diagnostic_arguments(parser)
    add_external_forces_arguments(parser)
    app_launcher_type.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.external_forces_source = external_forces_source(sys.argv[1:])
    if args.diagnose_state_consistency and (args.pd_profile != "baseline" or not args.record_joint_trace):
        parser.error("State consistency diagnosis requires baseline PD and --record-joint-trace")
    if args.physics_steps != 720:
        parser.error("This approved experiment requires exactly 720 controlled physics steps")
    if args.device != "cuda:0" or args.headless or args.enable_cameras or args.livestream not in (-1, 0):
        parser.error("This experiment requires GUI cuda:0 without cameras or livestream")
    for key in ("HEADLESS", "ENABLE_CAMERAS", "LIVESTREAM", "XR"):
        if os.environ.get(key) not in (None, "", "0"):
            parser.error(f"{key} would change the approved mode; use the correct child-process environment")
    if getattr(args, "xr", False):
        parser.error("XR is outside this experiment")
    args.usd_path = args.usd_path.expanduser().resolve(strict=True)
    args.output_dir = args.output_dir.expanduser().resolve()
    if not args.usd_path.is_file() or args.usd_path.suffix.lower() != ".usd":
        parser.error("--usd-path must name an existing .usd file")
    return args


def _state_joint_frames(stage, info, robot):
    """Read joint local frames only; never use authored world transforms as physical link state."""
    from pxr import UsdPhysics
    from _cr12_state_consistency import bind_joint_frames
    from _cr12_asset_math import JOINT_NAMES

    def quat(value):
        return [float(value.GetReal()), *map(float, value.GetImaginary())]

    records = []
    for name in JOINT_NAMES:
        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath(info["joints"][name]["path"]))
        body0, body1 = joint.GetBody0Rel().GetTargets(), joint.GetBody1Rel().GetTargets()
        if len(body0) != 1 or len(body1) != 1:
            raise DriveCheckError("state_mapping", "Diagnostic joint requires two bound physical links", joint=name)
        records.append({"name": name, "prim_path": info["joints"][name]["path"],
                        "body0": body0[0].name, "body1": body1[0].name,
                        "body0_path": str(body0[0]), "body1_path": str(body1[0]),
                        "axis": str(joint.GetAxisAttr().Get()),
                        "localPos0": list(map(float, joint.GetLocalPos0Attr().Get())),
                        "localPos1": list(map(float, joint.GetLocalPos1Attr().Get())),
                        "localRot0": quat(joint.GetLocalRot0Attr().Get()),
                        "localRot1": quat(joint.GetLocalRot1Attr().Get())})
    return bind_joint_frames(records, JOINT_NAMES, robot.body_names)


def _solver_observation(stage, sim, info):
    """Read resolved schema values, explicitly not a native solver-stage observation."""
    from pxr import PhysxSchema

    def attributes(api, names):
        result = {}
        for name in names:
            try:
                attr = getattr(api, "Get" + name + "Attr")()
                result[name] = {"value": attr.Get(), "authored": attr.HasAuthoredValueOpinion(),
                                "property": str(attr.GetPath())}
            except Exception as exc:
                result[name] = {"value": None, "status": "UNKNOWN", "reason": str(exc)}
        return result

    scene = PhysxSchema.PhysxSceneAPI(stage.GetPrimAtPath(sim.cfg.physics_prim_path))
    root = PhysxSchema.PhysxArticulationAPI(stage.GetPrimAtPath(info["articulation_roots"][0]))
    return {"source": "composed USD schema after physics initialization; not native internal counters",
            "scene": attributes(scene, ("SolverType", "MinPositionIterationCount", "MaxPositionIterationCount",
                                        "MinVelocityIterationCount", "MaxVelocityIterationCount",
                                        "EnableExternalForcesEveryIteration", "EnableStabilization")),
            "articulation": attributes(root, ("SolverPositionIterationCount", "SolverVelocityIterationCount",
                                              "SleepThreshold", "StabilizationThreshold")),
            "native_solver_iteration_getter": "UNKNOWN: not exposed by the installed tensor ArticulationView"}


def _probe_state(robot, joint_ids, sim, q, dq, clock_before, state_trace, trace, step, baseline, reference_time):
    """No state writes, stepping, rendering, kinematic refresh, or robot.update in this block."""
    import numpy as np
    import torch
    from _cr12_state_consistency import snapshot_read, analyze_links, SnapshotReadError

    def copy_value(value):
        # Blocking D2H copy, then independent host allocation. A device-wide fence
        # also completes queued work before a native getter can reuse its buffer.
        if isinstance(value, torch.Tensor):
            return value.detach().to(device="cpu", non_blocking=False).numpy().copy()
        return np.array(value, copy=True)

    view = robot.root_physx_view
    try:
        sample = snapshot_read(
            {"q": lambda: q, "dq": lambda: dq},
            {"q": lambda: view.get_dof_positions()[0, joint_ids],
             "dq": lambda: view.get_dof_velocities()[0, joint_ids],
             "poses": lambda: view.get_link_transforms()[0],
             "velocities": lambda: view.get_link_velocities()[0]},
            copy_value, lambda: torch.cuda.synchronize(robot.device), lambda: _clock(sim),
        )
    except SnapshotReadError as exc:
        sample = exc.sample
        native = sample["native"]
        local_read_error = isinstance(exc.__cause__, (AttributeError, KeyError, IndexError, TypeError))
        primary = DriveCheckError("state_consistency_reading" if local_read_error else "state_invalid",
                                  "State comparison getter/copy failed", error=str(exc))
        try:
            trace.set_state_comparison(step, native.get("q"), native.get("dq"))
            state_trace.append(step, clock_before[1], clock_before[1]-baseline[1], reference_time,
                               poses=native.get("poses"), velocities=native.get("velocities"),
                               clock_before=clock_before, clock_after=sample.get("clock_after"), status="READ_ERROR")
        except BaseException as secondary:
            primary.details["secondary_recording_error"] = f"{type(secondary).__name__}: {secondary}"
        raise primary from exc
    native = sample["native"]
    trace.set_state_comparison(step, native["q"], native["dq"])
    if _clock(sim) != clock_before:
        primary = DriveCheckError("physics_count", "State read block advanced physics")
        try:
            state_trace.append(step, clock_before[1], clock_before[1]-baseline[1], reference_time,
                               poses=native["poses"], velocities=native["velocities"],
                               clock_before=clock_before, clock_after=sample["clock_after"], status="CLOCK_CHANGED")
        except BaseException as secondary:
            primary.details["secondary_recording_error"] = f"{type(secondary).__name__}: {secondary}"
        raise primary
    try:
        analysis = analyze_links(state_trace.metadata["bindings"], native["poses"], native["velocities"],
                                 previous_angles=getattr(state_trace, "previous_angles", None))
    except (ValueError, TypeError, KeyError) as exc:
        primary = DriveCheckError("state_invalid", "Cannot interpret observed link state", error=str(exc))
        try:
            state_trace.append(step, clock_before[1], clock_before[1]-baseline[1], reference_time,
                               poses=native["poses"], velocities=native["velocities"],
                               clock_before=clock_before, clock_after=sample["clock_after"], status="INVALID_LINK_STATE")
        except BaseException as secondary:
            primary.details["secondary_recording_error"] = f"{type(secondary).__name__}: {secondary}"
        raise primary from exc
    state_trace.previous_angles = analysis["angle_rad"]
    state_trace.append(step, clock_before[1], clock_before[1]-baseline[1], reference_time,
                       poses=native["poses"], velocities=native["velocities"], analysis=analysis,
                       clock_before=clock_before, clock_after=_clock(sim),
                       comparison_valid=sample["complete"])
    # Retain a few first host snapshots across subsequent getters and ticks.
    # Compare their actual objects to independent witnesses, not a reread cache.
    if step in (1, 120, 360, 480, 600):
        retained = getattr(state_trace, "retained_snapshots", [])
        checks = state_trace.metadata.setdefault("snapshot_rechecks", [])
        for old_step, values, witnesses in retained:
            checks.append({"saved_step": old_step, "checked_at_step": step,
                           "unchanged": all(np.array_equal(value, witness) for value, witness in zip(values, witnesses))})
        values = [sample["cached"]["q"], sample["cached"]["dq"], native["q"], native["dq"],
                  native["poses"], native["velocities"]]
        checks.append({"saved_step": step, "checked_at_step": step,
                       "acceptance_snapshot_unchanged": bool(np.array_equal(q, sample["cached"]["q"])
                                                            and np.array_equal(dq, sample["cached"]["dq"]))})
        retained.append((step, values, [value.copy() for value in values]))
        state_trace.retained_snapshots = retained


def _trace_check(trace, name, callback):
    """Record check coverage without continuing any runtime API after its failure."""
    trace.mark_check(name, "STARTED")
    try:
        value = callback()
    except BaseException as exc:
        trace.mark_check(name, "FAIL" if isinstance(exc, DriveCheckError) else "ERROR",
                         details={"type": type(exc).__name__, "message": str(exc)})
        raise
    trace.mark_check(name, "PASS")
    return value


def _sync_diagnostics(recorder, trace, state_trace=None):
    """Flush acquired observations; never obtain another runtime state to fill a gap."""
    trace.flush()
    summary = trace.summary()
    recorder.result["joint_diagnostics_summary"] = summary
    if state_trace is not None:
        state_trace.flush()
        recorder.result["state_consistency"] = state_trace.summary()
    if "drive_summary" in recorder.result:
        stats = recorder.result["drive_summary"]
        whole, hold = summary["windows"]["all_controlled"], summary["windows"]["strict_hold"]
        stats.update({
            "maximum_error_rad": whole["max_abs_error_rad"],
            "maximum_speed_rad_s": whole["max_abs_speed_rad_s"],
            "last_second_maximum_error_rad": hold["max_abs_error_rad"],
            "last_second_maximum_speed_rad_s": hold["max_abs_speed_rad_s"],
        })


def _run_drive(args, app, recorder, resources, expected):
    import numpy as np
    import torch
    import isaaclab.sim as sim_utils
    from isaaclab.assets import Articulation
    from isaaclab_assets.robots import rokea_cr12 as configuration
    from isaacsim.core.utils.stage import get_current_stage
    from omni.physx.scripts.physicsUtils import add_ground_plane
    from pxr import Gf, PhysxSchema, Usd, UsdPhysics
    from _cr12_asset_math import ASSET_VERSION, BODY_NAMES, JOINT_LIMITS, ROOT_TRANSLATION, step_reference_times, trajectory
    from prepare_cr12_fixed_asset import inspect_usd_stage, check_source_collision_bounds
    from _cr12_external_forces import apply_scene_external_forces, read_scene_external_forces, SceneExternalForcesError
    import omni.physx
    import omni.timeline

    scene = create_fixed_cr12_scene(args, app, recorder, resources, expected)
    sim, stage, robot, info = scene["sim"], scene["stage"], scene["robot"], scene["info"]
    setup, frames, contacts = scene["setup"], scene["frames"], scene["contacts"]
    body_ids, joint_ids, after_reset = scene["body_ids"], scene["joint_ids"], scene["after_reset"]
    default_time = scene["default_time"]
    if args.diagnose_state_consistency:
        from _cr12_state_consistency import StateConsistencyTrace
        recorder.result["solver_observation"] = _solver_observation(stage, sim, info)
        resources["state_trace"] = StateConsistencyTrace(args.output_dir / "body_state_trace.csv", {
            "bindings": _state_joint_frames(stage, info, robot),
            "body_names": list(robot.body_names), "joint_names": list(configuration.JOINT_NAMES),
            "joint_names_native": list(robot.joint_names),
            "joint_indices": list(joint_ids),
            "acceptance_source": "ArticulationData.joint_pos/joint_vel after normal robot.update; immutable CPU q/dq",
            "read_order": "clock -> cached q/dq blocking D2H -> trace -> explicit CUDA fence -> each native getter -> fence -> independent blocking D2H -> fence -> clock",
            "pose_source": "ArticulationView.get_link_transforms: world link/actor xyz+XYZW, metres",
            "omega_source": "ArticulationView.get_link_velocities[...,3:6]: world angular rad/s, no COM rotation",
            "local_frame_source": "composed UsdPhysics.RevoluteJoint body0/body1/axis/localPos/localRot (WXYZ)",
            "refresh": "no extra step/render/app.update/robot.update/kinematic update/state or target write in probe",
            "source_independence": "native link and generalized state share PhysX articulation; not independent physical ground truth",
        })
    initial = initialize_fixed_cr12_state(args, recorder, scene)
    q, dq, poses = initial["q"], initial["dq"], initial["poses"]
    initial_root = initial["initial_root"]
    initial_minimum_z, baseline = initial["initial_minimum_z"], initial["baseline"]
    trace = resources["trace"]
    state_trace = resources.get("state_trace")
    trace.append(0, baseline[1], 0.0, 0.0,
                 robot.data.joint_pos_target[0, joint_ids].detach().cpu().tolist(),
                 robot.data.joint_vel_target[0, joint_ids].detach().cpu().tolist(), q, dq, q_reference=[0.0] * 6)
    trace.flush()
    recorder.emit("physics_ready", body_count=7, dof_count=6, fixed_base=True, initial_physics_clock=list(baseline))
    recorder.save()
    read_scene_external_forces(stage, setup, "before_motion", PhysxSchema, UsdPhysics, default_time)
    recorder.phase = "controlled_drive"
    stats = {"maximum_error_rad": None, "maximum_speed_rad_s": None,
             "last_second_maximum_speed_rad_s": None, "maximum_root_translation_m": 0.0,
             "maximum_root_rotation_rad": 0.0, "maximum_forbidden_contact_n": 0.0,
             "last_second_maximum_error_rad": None,
             "maximum_fixed_frame_errors": {name: [0.0, 0.0] for name in frames},
             "minimum_arm_collision_z_m": initial_minimum_z, "render_calls": 0, "no_progress_check_passed": False,
             "submitted_target_checks": 0,
             "baseline_target_source": "initial setter cache before controlled write_data_to_sim",
             "controlled_target_source": "exact _joint_pos/vel_target_sim buffers after write_data_to_sim",
             "reference_convention": "q_ref(t_after), dq_ref(t_after) submitted before tick; measured post-tick at t_after"}
    recorder.result["drive_summary"] = stats
    ramp_start = None
    for index in range(args.physics_steps):
        _assert_active(app, sim)
        before_time, after_time = step_reference_times(index)
        before = _clock(sim)
        if before[0] != baseline[0] + index or abs(before[1] - baseline[1] - before_time) > 1e-4:
            raise DriveCheckError("physics_count", "Physics advanced outside controlled stepping")
        # Endpoint sampling: targets and the comparison reference share t_after.
        reference, velocity_reference = trajectory(after_time)
        position_command = torch.as_tensor(reference, dtype=torch.float32, device=robot.device).unsqueeze(0)
        velocity_command = torch.as_tensor(velocity_reference, dtype=torch.float32, device=robot.device).unsqueeze(0)
        robot.set_joint_position_target(position_command, joint_ids=joint_ids)
        robot.set_joint_velocity_target(velocity_command, joint_ids=joint_ids)
        robot.write_data_to_sim()
        submitted_position, submitted_velocity = _capture_submitted_targets(
            robot, joint_ids, position_command, velocity_command
        )
        stats["submitted_target_checks"] += 1
        if index == 0:
            recorder.result["controlled_step_attempted"] = True
            recorder.save()
            recorder.emit("controlled_step_begin", step=1)
        sim.step(render=False)
        after = _clock(sim)
        recorder.result["completed_physics_steps"] = after[0] - baseline[0]
        recorder.result["controlled_simulation_time_s"] = after[1] - baseline[1]
        trace.mark_check("clock", "STARTED", step=index + 1)
        try:
            check_clock(*before, *after, configuration.PHYSICS_DT)
        except BaseException as exc:
            trace.mark_check("clock", "FAIL", step=index + 1, details={"message": str(exc)})
            raise
        trace.mark_check("clock", "PASS", step=index + 1)
        robot.update(configuration.PHYSICS_DT)
        probe_clock = _clock(sim)
        q, dq = _joint_state(robot, joint_ids)
        # Preserve the acquired sample before any monitor may terminate this tick.
        # The mathematical comparison reference remains the original float64 trajectory.
        trace.append(index + 1, after[1], after[1] - baseline[1], after_time,
                     submitted_position, submitted_velocity, q, dq, q_reference=reference)
        stats.update({"final_q_rad": q, "final_dq_rad_s": dq, "last_sample_time_s": after_time})
        if not all(math.isfinite(value) for value in q + dq):
            # Do not call another runtime sensor API after observing non-finite state.
            _trace_check(trace, "joint", lambda: check_joint_sample(q, dq, reference, JOINT_LIMITS, after_time, ramp_start))
        if state_trace is not None:
            _probe_state(robot, joint_ids, sim, q, dq, probe_clock, state_trace, trace,
                         index + 1, baseline, after_time)
        force = _trace_check(trace, "contact", lambda: _check_contacts(contacts, configuration.PHYSICS_DT))
        stats["maximum_forbidden_contact_n"] = max(stats["maximum_forbidden_contact_n"], force)
        errors, speeds = _trace_check(
            trace, "joint", lambda: check_joint_sample(q, dq, reference, JOINT_LIMITS, after_time, ramp_start)
        )
        if abs(after_time - 1.0) < 1e-7:
            ramp_start = float(q[1])
        if abs(after_time - 2.0) < 1e-7:
            stats["no_progress_check_passed"] = True
        poses = _body_poses(robot, body_ids)
        minimum_z = _trace_check(trace, "geometry", lambda: _check_geometry(info["colliders"], poses, configuration.CONTACT_OFFSET))
        distance, angle, frame_errors = _trace_check(trace, "frame", lambda: _check_frames(stage, info, frames, poses, initial_root))
        stats["maximum_root_translation_m"] = max(stats["maximum_root_translation_m"], distance)
        stats["maximum_root_rotation_rad"] = max(stats["maximum_root_rotation_rad"], angle)
        stats["minimum_arm_collision_z_m"] = min(stats["minimum_arm_collision_z_m"], minimum_z)
        stats["final_fixed_frame_errors"] = frame_errors
        for name, errors_for_frame in frame_errors.items():
            stats["maximum_fixed_frame_errors"][name] = [max(a, b) for a, b in zip(stats["maximum_fixed_frame_errors"][name], errors_for_frame)]
        if (index + 1) % 2 == 0:
            sim.render()
            stats["render_calls"] += 1
            if _clock(sim) != after:
                raise DriveCheckError("physics_count", "Rendering unexpectedly advanced physics")
            _assert_active(app, sim)
        if (index + 1) % 120 == 0:
            _sync_diagnostics(recorder, trace, state_trace)
            recorder.save()
            recorder.emit("drive_progress", completed_physics_steps=index + 1, simulation_time_s=after_time,
                          joint_2_deg=math.degrees(q[1]))
    final_clock = _clock(sim)
    if (final_clock[0] - baseline[0] != 720 or abs(final_clock[1] - baseline[1] - 6.0) > 1e-4
            or not stats["no_progress_check_passed"] or math.degrees(q[1]) < 4.5
            or any(record["updates"] != 720 for record in contacts.values())):
        raise DriveCheckError("incomplete_experiment", "Final physics/time/progress/contact budget was not satisfied")
    stats.update({"final_q_rad": q, "final_dq_rad_s": dq, "final_joint_2_deg": math.degrees(q[1]),
                  "physics_count_delta": final_clock[0] - baseline[0], "simulation_time_delta_s": final_clock[1] - baseline[1]})
    recorder.result["drive_summary"] = stats
    recorder.result["contact_summary"] = _contact_summary(contacts)
    _sync_diagnostics(recorder, trace, state_trace)
    diagnostic_summary = recorder.result["joint_diagnostics_summary"]
    recorder.result["diagnostics_complete"] = (
        diagnostic_summary["windows"]["all_controlled"]["complete"]
        and diagnostic_summary["windows"]["strict_hold"]["complete"]
        and all(item["complete"] and item["passed_sample_count"] == 720
                for item in diagnostic_summary["coverage"].values())
        and not diagnostic_summary["has_failure"]
        and not diagnostic_summary["invalid_sample_count"]
        and not diagnostic_summary["recording_error"]
        and diagnostic_summary["math_reference_sample_count"] == 720
    )
    if not recorder.result["diagnostics_complete"]:
        raise DriveCheckError("diagnostics_incomplete", "Joint trace/check windows are not complete")
    recorder.result["status"] = "WORK_COMPLETED_PENDING_NATURAL_EXIT"
    recorder.result["work_completed"] = True
    recorder.save()
    recorder.emit("work_completed", completed_physics_steps=720, simulation_time_s=6.0,
                  final_joint_2_deg=stats["final_joint_2_deg"], result_path=str(recorder.path))


def main():
    recorder = Recorder()
    recorder.emit("process_start", python=sys.executable, cwd=os.getcwd(), argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode)
    app = None
    resources = {}
    failure = None
    try:
        from isaaclab.app import AppLauncher
        args = _parse_args(AppLauncher)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result_path = args.output_dir / "result.json"
        if result_path.exists():
            raise FileExistsError(f"Refusing to overwrite an earlier attempt result: {result_path}")
        recorder.path = result_path
        from _cr12_hold_diagnostics import JointTrace, select_pd_profile
        from _cr12_asset_math import validate_derived
        from _windows_runtime_startup import prepare_windows_runtime_args
        from view_scan_assignment import _prepare_cuda_before_app
        selected_pd = select_pd_profile(args.pd_profile)
        trace_path = args.output_dir / "joint_trace.csv" if args.record_joint_trace else None
        resources["trace"] = JointTrace(trace_path, state_consistency=args.diagnose_state_consistency)
        urdf_path = args.usd_path.parent.parent / "cr12_fixed_lift0.urdf"
        expected = validate_derived(urdf_path)
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
                                  capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        recorder.result.update({"usd_path": str(args.usd_path), "derived_urdf_path": str(urdf_path),
                                "derived_urdf_sha256": expected["derived_sha256"], "git_head": revision,
                                "python": sys.executable, "entry_source": __file__, "original_argv": list(sys.argv),
                                "pd_selection": selected_pd, "record_joint_trace": args.record_joint_trace,
                                "diagnose_state_consistency": args.diagnose_state_consistency,
                                "external_forces_request": {"mode": args.external_forces_every_iteration,
                                                            "source": args.external_forces_source},
                                "trace_path": str(trace_path) if trace_path else None,
                                "torque_observation": "Native implicit solver torque not acquired. Any post-state PD estimate is diagnostic only."})
        recorder.phase = "startup_preparation"
        preparation = prepare_windows_runtime_args(args, list(sys.argv))
        if preparation["requested_backend"] != "D3D12":
            raise DriveCheckError("startup_mode", "Approved Windows experiment requires D3D12")
        recorder.result["startup"] = preparation
        recorder.emit("startup_prepared", **preparation)
        recorder.emit("pre_app_cuda_begin")
        recorder.result["pre_app_cuda"] = _prepare_cuda_before_app(args.device)
        recorder.emit("pre_app_cuda_ready", **recorder.result["pre_app_cuda"])
        recorder.phase = "app_create"
        recorder.save()
        recorder.emit("app_create_begin")
        launcher = AppLauncher(args)
        app = launcher.app
        import carb
        settings = carb.settings.get_settings()
        effective = {"experience": launcher._sim_experience_file, "kit_log_file": settings.get("/log/file"),
                     "vulkan_setting": settings.get("/app/vulkan"), "headless": launcher._headless,
                     "enable_cameras": launcher._enable_cameras, "livestream": launcher._livestream,
                     "xr": launcher._xr, "device": args.device}
        recorder.result["app"] = effective
        recorder.emit("app_ready", **effective)
        if (launcher._headless or launcher._enable_cameras or launcher._livestream or launcher._xr
                or settings.get("/app/vulkan") is not False):
            raise DriveCheckError("startup_mode", "Effective application mode differs from approved GUI/D3D12 mode")
        _run_drive(args, app, recorder, resources, expected)
    except BaseException as exc:
        failure = exc
        trace = resources.get("trace")
        if trace is not None:
            try:
                trace.mark_failure(getattr(exc, "category", "runtime_exception"), str(exc))
                state_trace = resources.get("state_trace")
                if state_trace is not None:
                    state_trace.mark_failure(getattr(exc, "category", "runtime_exception"), str(exc),
                                             affects_comparison=False)
                _sync_diagnostics(recorder, trace, state_trace)
            except BaseException as secondary:
                recorder.secondary(secondary, "failure_trace_recording")
                # The in-memory observed samples remain useful even if CSV I/O failed.
                try:
                    recorder.result["joint_diagnostics_summary"] = trace.summary()
                except BaseException as summary_error:
                    recorder.secondary(summary_error, "failure_trace_summary")
        if "contacts" in resources:
            recorder.result["contact_summary"] = _contact_summary(resources["contacts"])
        recorder.fail(exc)
    finally:
        state_trace = resources.get("state_trace")
        if state_trace is not None:
            try:
                state_trace.close()
                recorder.result["state_consistency"] = state_trace.summary()
            except BaseException as exc:
                if failure is None:
                    failure = exc
                    recorder.fail(exc, "state_trace_close")
                else:
                    recorder.secondary(exc, "state_trace_close")
        trace = resources.get("trace")
        if trace is not None:
            try:
                trace.close()
                _sync_diagnostics(recorder, trace)
            except BaseException as exc:
                if failure is None:
                    failure = exc
                    recorder.fail(exc, "trace_close")
                else:
                    recorder.secondary(exc, "trace_close")
        sim = resources.get("sim")
        setup = recorder.result.get("external_forces_setup")
        if setup is not None and setup.get("after") is not None:
            try:
                from _cr12_external_forces import read_scene_external_forces
                stage, physx_schema, usd_physics, default_time = resources["external_forces_context"]
                read_scene_external_forces(stage, setup, "before_exit", physx_schema, usd_physics, default_time)
            except BaseException as exc:
                if failure is None:
                    failure = exc
                    recorder.fail(exc, "external_forces_exit_readback")
                else:
                    recorder.secondary(exc, "external_forces_exit_readback")
        if sim is not None:
            recorder.phase = "simulation_stop"
            try:
                sim._disable_app_control_on_stop_handle = True
                sim.stop()
                recorder.result["simulation_stop_returned"] = True
            except BaseException as exc:
                if failure is None:
                    failure = exc
                recorder.fail(exc)
        if app is not None:
            recorder.phase = "app_close"
            recorder.result["app_close_requested"] = True
            for action in (recorder.save, lambda: recorder.emit(
                    "app_close_begin", work_completed=recorder.result["work_completed"],
                    failures=len(recorder.result["failures"]) + len(recorder.result["secondary_failures"]))):
                try:
                    action()
                except BaseException as exc:
                    if failure is None:
                        failure = exc
                        recorder.fail(exc, "pre_close_recording")
                    else:
                        recorder.secondary(exc, "pre_close_recording")
            try:
                app.close()
                recorder.emit("app_close_returned")
            except BaseException as exc:
                if failure is None:
                    failure = exc
                recorder.fail(exc)
    if failure is not None:
        raise failure
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
