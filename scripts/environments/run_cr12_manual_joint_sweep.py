"""Fixed manual CR12 joint-space roundtrip with explicit OBB refinement.

Importing this entry does not import Isaac/torch or launch a process. This is an
observation profile, not formal pose acceptance, IK or scan acquisition.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

from _cr12_runtime_support import (
    DriveCheckError, Recorder, _assert_active, _body_poses, _capture_submitted_targets,
    _check_contacts, _check_frames, _clock, _contact_summary, check_clock,
    create_fixed_cr12_scene, initialize_fixed_cr12_state,
)
# These readback/recording helpers have no IK or simulator side effects on import.
from run_cr12_pose_target import (
    _native_state, _pose_record, _checked_tick_guard, finish_sample_trace,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
APPROVED_USD = REPO_ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd"
GEOMETRY_MODE = "aabb_then_obb_margin_v1"
PROFILE_NAME = "j3_visible_roundtrip_v1"


def validate_private_path(kit_args, output_dir):
    """Match AppLauncher.split(), require a task-owned prepared private file."""
    tokens = kit_args.split()
    key = "--/app/userConfigPath="
    matches = [token for token in tokens if token.startswith(key)]
    if len(matches) != 1 or any(token == key[:-1] for token in tokens):
        raise ValueError("Exactly one --/app/userConfigPath=<private absolute path> is required")
    supplied = Path(matches[0][len(key):])
    expected = Path(output_dir) / "private_config/user.config.json"
    if not supplied.is_absolute() or supplied.resolve(strict=True) != expected.resolve():
        raise ValueError("The private config must be output-dir/private_config/user.config.json")
    source = Path(sys.prefix) / "Lib/site-packages/omni/data/Kit/Isaac-Sim/4.5/user.config.json"
    if source.exists() and os.path.samefile(supplied, source):
        raise ValueError("Refusing the real source user.config")
    tree = json.loads(supplied.read_text(encoding="utf-8-sig"))
    window = tree["persistent"]["app"]["window"]
    for field, value in (("width", 1440), ("height", 900), ("maximized", False)):
        if type(window[field]) is not type(value) or window[field] != value:
            raise ValueError("Private saved window state has not been prepared")
    return str(supplied.resolve())


def parse_args(app_launcher_type, argv=None):
    from _cr12_external_forces import add_external_forces_arguments, external_forces_source
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd-path", "--usd_path", type=Path, required=True)
    parser.add_argument("--output-dir", "--output_dir", type=Path, required=True)
    parser.add_argument("--profile", choices=(PROFILE_NAME,), default=PROFILE_NAME)
    parser.add_argument("--geometry_mode", choices=(GEOMETRY_MODE,), default=GEOMETRY_MODE)
    parser.add_argument("--view", choices=("arm-oblique",), default="arm-oblique")
    add_external_forces_arguments(parser)
    app_launcher_type.add_app_launcher_args(parser)
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(actual_argv)
    args.external_forces_source = external_forces_source(actual_argv)
    if args.external_forces_every_iteration != "on" or args.external_forces_source != "explicit_cli":
        parser.error("Explicit --external-forces-every-iteration on is required")
    if (args.device != "cuda:0" or args.headless or args.enable_cameras
            or args.livestream not in (-1, 0) or getattr(args, "xr", False)):
        parser.error("Only GUI cuda:0 without scan cameras/livestream/XR is supported")
    if sys.flags.utf8_mode != 1:
        parser.error("Enable UTF8 before starting Python")
    for key in ("HEADLESS", "ENABLE_CAMERAS", "LIVESTREAM", "XR"):
        if os.environ.get(key) not in (None, "", "0"):
            parser.error(f"{key} would change the frozen mode")
    args.usd_path = args.usd_path.expanduser().resolve(strict=True)
    if args.usd_path != APPROVED_USD.resolve(strict=True):
        parser.error("Only the accepted fixed_lift0_v1 USD is allowed")
    args.output_dir = args.output_dir.expanduser().resolve()
    try:
        args.private_user_config = validate_private_path(args.kit_args, args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    return args


class SweepTrace:
    """One compact CSV; includes actual native state and the failing sample."""
    GUARDS = ("clock", "joint", "contact", "geometry", "frame", "render_clock")
    VECTORS = {"q": 6, "dq": 6, "q_cmd": 6, "dq_cmd": 6, "actual_p": 3, "actual_qwxyz": 4}

    def __init__(self, path):
        fields = ["step", "physics_time_s", "controlled_time_s", "reference_time_s", "phase",
                  "joint3_delta_deg", "scanner_from_start_m", "status", "failure"]
        for key, size in self.VECTORS.items():
            fields.extend(f"{key}_{i}" for i in range(size))
        fields.extend("guard_" + key for key in self.GUARDS)
        self.stream = Path(path).open("x", encoding="utf-8", newline="")
        self.writer = csv.DictWriter(self.stream, fieldnames=fields)
        self.writer.writeheader()
        self.stream.flush()
        self.count = 0

    def append(self, sample):
        row = dict(sample)
        for key, size in self.VECTORS.items():
            values = row.pop(key, [])
            for i in range(size):
                row[f"{key}_{i}"] = values[i] if i < len(values) else ""
        self.writer.writerow(row)
        self.stream.flush()
        self.count += 1

    def close(self):
        self.stream.close()


def finish_sweep_sample(trace, sample, recorder, monitor, pacer, controlled_time, primary_error):
    """Always preserve the failing CSV row; diagnostic errors cannot hide its cause."""
    recording_error = None
    for key, callback in (("monitor_summary", monitor.summary),
                          ("pacing", lambda: pacer.summary(controlled_time))):
        try:
            recorder.result[key] = callback()
        except BaseException as exc:
            if primary_error is not None or recording_error is not None:
                recorder.secondary(exc, key + "_after_failure")
            else:
                recording_error = exc
                sample.update(status="FAIL", failure=f"{type(exc).__name__}: {exc}")
    finish_sample_trace(trace, sample, recorder, primary_error or recording_error)
    if recording_error is not None:
        raise recording_error


def _run_sweep(args, app, recorder, resources, expected):
    import numpy as np
    import torch
    import _cr12_pose_control as pc
    import _cr12_manual_joint_sweep as sweep
    import _cr12_collision_refinement as geometry
    from _cr12_external_forces import read_scene_external_forces
    from _cr12_pose_visuals import PoseDebugVisuals

    scene = create_fixed_cr12_scene(args, app, recorder, resources, expected)
    sim, robot, info, stage = (scene[k] for k in ("sim", "robot", "info", "stage"))
    body_ids, joint_ids, frames, contacts = (scene[k] for k in ("body_ids", "joint_ids", "frames", "contacts"))
    wanted = {item["path"]: item for item in expected["colliders"]}
    actual_shapes = {item["path"]: item for item in info["colliders"]}
    if len(actual_shapes) != 10 or set(actual_shapes) != set(wanted):
        raise DriveCheckError("SETUP", "Actual collision shape identities differ from offline inputs")
    for path, item in actual_shapes.items():
        if item["body"] != wanted[path]["body"] or any(
            not np.allclose(item[key], wanted[path][key], atol=1e-6, rtol=0)
            for key in ("local_bbox_min", "local_bbox_max")
        ):
            raise DriveCheckError("SETUP", "Actual collision body/bounds differ from offline inputs", shape=path)
    guard = geometry.GeometryGuard(info["colliders"])
    geometry_totals = {key: geometry.GeometrySummary() for key in ("initial", "initial_path", "pre_submit", "actual")}
    recorder.result["geometry_summary"] = {}

    def inspect(poses, bucket):
        result = guard.inspect(poses)
        geometry_totals[bucket].add(result)
        recorder.result["geometry_summary"][bucket] = geometry_totals[bucket].summary()
        if not result["passed"]:
            raise DriveCheckError("geometry_guard", "Refined collision enclosures are unresolved",
                                  geometry=result, contact_proven=False)
        return result["min_arm_z"]

    def initial_geometry(colliders, poses, offset):
        if offset != .002 or colliders is not info["colliders"]:
            raise DriveCheckError("SETUP", "Unexpected initialization geometry input")
        return inspect(poses, "initial")

    initial = initialize_fixed_cr12_state(args, recorder, scene, geometry_check=initial_geometry)
    baseline, initial_root = initial["baseline"], initial["initial_root"]
    recorder.phase = "sweep_setup"
    mapping = pc.resolve_mapping(robot.body_names, robot.joint_names, robot.is_fixed_base)
    if list(mapping["joint_ids"]) != list(joint_ids) or list(mapping["body_ids"]) != list(body_ids):
        raise DriveCheckError("SETUP", "Native body/joint name mappings differ")
    q_tensor, dq_tensor = _native_state(robot, joint_ids)
    q, dq = (value[0].detach().cpu().numpy().astype(np.float64, copy=True) for value in (q_tensor, dq_tensor))
    poses = _body_poses(robot, body_ids)
    _check_frames(stage, info, frames, poses, initial_root)
    for name, wanted in (("tool", np.eye(4)), ("scanner", pc.T_ES)):
        if not np.allclose(frames[name], wanted, atol=1e-5, rtol=0):
            raise DriveCheckError("SETUP", f"Unexpected fixed {name} transform")
    model = pc.KinematicModel.from_derived_urdf(args.usd_path.parent.parent / "cr12_fixed_lift0.urdf")
    plan = sweep.SweepPlan(q)
    actual_scanner = pc.scanner_from_ee(poses["link_6"])
    initial_scanner = actual_scanner.copy()
    target = pc.scanner_from_ee(model.forward(plan.q_out, initial_root)["link_6"])
    recorder.result["frozen_poses"] = {"initial_root": _pose_record(initial_root),
        "initial_scanner": _pose_record(initial_scanner), "outbound_reference": _pose_record(target),
        "T_ES": _pose_record(pc.T_ES), "target_meaning": "fixed outbound FK endpoint, not measured state or IK goal"}
    recorder.result["q_start_rad"] = q.tolist()
    recorder.result["q_out_rad"] = plan.q_out.tolist()
    # Freeze from the measured initial state. No state writes or alternative target.
    for ratio in np.linspace(0.0, 1.0, 201):
        predicted_q = plan.q_start + ratio * (plan.q_out - plan.q_start)
        if np.any(predicted_q < pc.JOINT_LIMITS[:, 0] + .02) or np.any(predicted_q > pc.JOINT_LIMITS[:, 1] - .02):
            raise DriveCheckError("SETUP", "Frozen path violates command hard-limit margin")
        inspect(model.forward(predicted_q, initial_root), "initial_path")
    if _clock(sim) != baseline:
        raise DriveCheckError("physics_count", "Initialization/path checking advanced physics")
    visuals = PoseDebugVisuals(stage, initial_scanner, args.view, target_scanner_pose=target)
    recorder.result.update(visual_errors=[], visual_metadata=visuals.metadata,
        spectator=visuals.metadata["view"], visual_setup_completed=True, visual_update_count=1)
    if _clock(sim) != baseline:
        raise DriveCheckError("physics_count", "Marker initialization advanced physics")
    monitor = sweep.SweepMonitor(plan, initial_scanner)
    resources["monitor"] = monitor
    trace = resources["trace"]
    counts = {key: 0 for key in SweepTrace.GUARDS}
    stats = {"guard_pass_counts": counts, "submitted_target_checks": 0, "sanity_checks": 0,
        "render_calls": 0, "maximum_forbidden_contact_n": 0.0,
        "maximum_root_translation_m": 0.0, "maximum_root_rotation_rad": 0.0,
        "minimum_arm_collision_z_m": initial["initial_minimum_z"], "all_guards_passed": False}
    recorder.result["sweep_summary"] = stats
    recorder.result["control"] = {"type": "joint_space_quintic", "profile": args.profile,
        "geometry_mode": args.geometry_mode, "maximum_steps": sweep.MAX_STEPS, "maximum_seconds": 21.0,
        "joint_state_source": "native PhysX get_dof_positions/get_dof_velocities clone",
        "actual_scanner_source": "actual body_link pose link_6 composed with fixed T_ES",
        "reference_marker": "fixed outbound FK endpoint for the entire roundtrip",
        "pacing": "monotonic deadline sleep only; no extra physics/render/update"}
    read_scene_external_forces(stage, scene["setup"], "before_motion", scene["physx_schema"],
                              scene["usd_physics"], scene["default_time"])
    recorder.result["monitor_summary"] = monitor.summary()
    recorder.save()
    recorder.emit("physics_ready", body_count=7, dof_count=6, initial_physics_clock=list(baseline))
    recorder.phase = "controlled_sweep"
    pacer = sweep.RealtimePacer()
    previous_command = np.asarray(plan.q_start, dtype=np.float32)
    previous_phase = None

    def tensor(value):
        return torch.tensor(np.array(value, copy=True), dtype=torch.float32, device=robot.device).unsqueeze(0)

    for step in range(1, sweep.MAX_STEPS + 1):
        _assert_active(app, sim)
        before = _clock(sim)
        if before[0] != baseline[0] + step - 1 or abs(before[1]-baseline[1]-(step-1)*sweep.DT) > 1e-4:
            raise DriveCheckError("physics_count", "Physics advanced outside controlled stepping")
        ref = plan.command(step, previous_command, dtype=np.float32)
        if ref.phase != previous_phase:
            recorder.emit("sweep_phase", stage_name=ref.phase, step=step, reference_time_s=ref.time_s)
            previous_phase = ref.phase
        for ratio in (.5, 1.0):
            inspect(model.forward(q + ratio*(ref.q-q), poses["agv"]), "pre_submit")
            stats["sanity_checks"] += 1
        pos_cmd, vel_cmd = tensor(ref.q), tensor(ref.dq)
        robot.set_joint_position_target(pos_cmd, joint_ids=joint_ids)
        robot.set_joint_velocity_target(vel_cmd, joint_ids=joint_ids)
        robot.write_data_to_sim()
        submitted_q, submitted_dq = _capture_submitted_targets(robot, joint_ids, pos_cmd, vel_cmd)
        previous_command = np.asarray(submitted_q)
        stats["submitted_target_checks"] += 1
        if step == 1:
            recorder.result["controlled_step_attempted"] = True
            recorder.save()
            recorder.emit("controlled_step_begin", step=1)
        sim.step(render=False)
        after = _clock(sim)
        controlled_time = after[1] - baseline[1]
        recorder.result.update(completed_physics_steps=after[0]-baseline[0],
                               controlled_simulation_time_s=controlled_time)
        sample = {"step": step, "physics_time_s": after[1], "controlled_time_s": controlled_time,
            "reference_time_s": ref.time_s, "phase": ref.phase, "q_cmd": submitted_q, "dq_cmd": submitted_dq,
            "status": "RUNNING", **{"guard_"+key: "NOT_RUN" for key in SweepTrace.GUARDS}}
        sample_failure = None
        try:
            _checked_tick_guard(sample, counts, "clock", lambda: check_clock(*before, *after, sweep.DT))
            robot.update(sweep.DT)
            q_tensor, dq_tensor = _native_state(robot, joint_ids)
            q, dq = (value[0].detach().cpu().numpy().astype(np.float64, copy=True) for value in (q_tensor, dq_tensor))
            sample.update(q=q, dq=dq)
            poses = _body_poses(robot, body_ids)
            actual_scanner = pc.scanner_from_ee(poses["link_6"])
            sample.update(q=q, dq=dq, joint3_delta_deg=float(np.rad2deg(q[plan.moving_index]-plan.q_start[plan.moving_index])),
                          scanner_from_start_m=float(np.linalg.norm(actual_scanner[:3, 3]-initial_scanner[:3, 3])))
            sample["actual_p"], sample["actual_qwxyz"] = pc.pose_to_wxyz(actual_scanner)
            _checked_tick_guard(sample, counts, "joint", lambda: monitor.observe(step, controlled_time, q, dq, actual_scanner))
            force = _checked_tick_guard(sample, counts, "contact", lambda: _check_contacts(contacts, sweep.DT))
            min_z = _checked_tick_guard(sample, counts, "geometry", lambda: inspect(poses, "actual"))
            distance, angle, fixed_errors = _checked_tick_guard(sample, counts, "frame",
                lambda: _check_frames(stage, info, frames, poses, initial_root))
            try:
                visuals.update(actual_scanner, target)
                recorder.result["visual_update_count"] += 1
            except Exception as exc:
                recorder.result["visual_errors"].append(f"{type(exc).__name__}: {exc}")
                raise DriveCheckError("visual_failure", "Marker update failed") from exc
            if step % 2 == 0:
                sim.render()
                stats["render_calls"] += 1
            def render_guard():
                if _clock(sim) != after:
                    raise DriveCheckError("physics_count", "Readback/display/render advanced physics")
                _assert_active(app, sim)
            _checked_tick_guard(sample, counts, "render_clock", render_guard)
            stats.update(maximum_forbidden_contact_n=max(stats["maximum_forbidden_contact_n"], force),
                maximum_root_translation_m=max(stats["maximum_root_translation_m"], distance),
                maximum_root_rotation_rad=max(stats["maximum_root_rotation_rad"], angle),
                minimum_arm_collision_z_m=min(stats["minimum_arm_collision_z_m"], min_z),
                final_fixed_frame_errors=fixed_errors)
            pacer.pace(ref.time_s)
            sample["status"] = "PASS"
        except BaseException as exc:
            sample_failure = exc
            sample.update(status="FAIL", failure=f"{getattr(exc, 'category', type(exc).__name__)}: {exc}")
            monitor.mark_failure(getattr(exc, "category", type(exc).__name__), str(exc))
            raise
        finally:
            finish_sweep_sample(trace, sample, recorder, monitor, pacer, controlled_time, sample_failure)
        if step % 120 == 0:
            recorder.save()
            if step % 240 == 0:
                recorder.emit("sweep_progress", completed_physics_steps=step,
                    joint3_delta_deg=sample["joint3_delta_deg"], scanner_from_start_m=sample["scanner_from_start_m"])
    stats["all_guards_passed"] = all(value == sweep.MAX_STEPS for value in counts.values())
    final_monitor = monitor.summary()
    if (not stats["all_guards_passed"] or trace.count != sweep.MAX_STEPS
            or not final_monitor["all_passed"] or not final_monitor["complete"]
            or any(item["updates"] != sweep.MAX_STEPS for item in contacts.values())
            or recorder.result["failures"] or recorder.result["secondary_failures"]
            or recorder.result["visual_errors"]):
        raise DriveCheckError("completion", "Incomplete checks or sticky failures forbid success")
    recorder.result["monitor_summary"] = monitor.summary()
    recorder.result["contact_summary"] = _contact_summary(contacts)
    recorder.result["pacing"] = pacer.summary(recorder.result["controlled_simulation_time_s"])
    recorder.result.update(controlled_wall_time_s=recorder.result["pacing"]["controlled_wall_time_s"],
                           playback_ratio=recorder.result["pacing"]["playback_ratio"])
    recorder.result.update(sweep_outcome="MANUAL_JOINT_SWEEP_COMPLETED", work_completed=True,
                           status="WORK_COMPLETED_PENDING_NATURAL_EXIT")
    recorder.save()
    recorder.emit("sweep_phase", stage_name="COMPLETE", step=sweep.MAX_STEPS)
    recorder.emit("work_completed", completed_physics_steps=sweep.MAX_STEPS,
                  simulation_time_s=recorder.result["controlled_simulation_time_s"])


def main():
    recorder, resources, app, failure = Recorder(), {}, None, None
    recorder.emit("process_start", python=sys.executable, cwd=os.getcwd(), argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode)
    try:
        from isaaclab.app import AppLauncher
        args = parse_args(AppLauncher)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result_path = args.output_dir / "result.json"
        if result_path.exists():
            raise FileExistsError(result_path)
        recorder.path = result_path
        resources["trace"] = SweepTrace(args.output_dir / "joint_scanner_trace.csv")
        from _cr12_collision_refinement import load_accepted_inputs
        from _cr12_manual_joint_sweep import PROFILE
        from _cr12_hold_diagnostics import select_pd_profile
        from _windows_runtime_startup import prepare_windows_runtime_args
        from view_scan_assignment import _prepare_cuda_before_app
        expected = load_accepted_inputs(args.usd_path.parent.parent / "cr12_fixed_lift0.urdf")
        recorder.result.update(MANUAL_JOINT_VISUAL_ONLY=True, profile=args.profile, geometry_mode=args.geometry_mode,
            frozen_profile=asdict(PROFILE), sweep_outcome="NOT_REACHED", usd_path=str(args.usd_path),
            python=sys.executable, entry_source=__file__, original_argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode,
            pd_selection=select_pd_profile("baseline"), view_preset=args.view, visual_debug_pose=True,
            private_user_config=args.private_user_config,
            external_forces_request={"mode": "on", "source": args.external_forces_source},
            git_head=subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                    text=True, timeout=5, check=True).stdout.strip())
        recorder.phase = "startup_preparation"
        startup = prepare_windows_runtime_args(args, list(sys.argv))
        if startup["requested_backend"] != "D3D12":
            raise DriveCheckError("SETUP", "D3D12 required")
        recorder.result["startup"] = startup
        recorder.emit("startup_prepared", **startup)
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
            "xr": launcher._xr, "device": args.device, "user_config_path": settings.get("/app/userConfigPath")}
        recorder.result["app"] = effective
        recorder.emit("app_ready", **effective)
        if (launcher._headless or launcher._enable_cameras or launcher._livestream or launcher._xr
                or settings.get("/app/vulkan") is not False
                or Path(effective["user_config_path"]).resolve() != Path(args.private_user_config)):
            raise DriveCheckError("SETUP", "Effective mode/private config differs from frozen request")
        _run_sweep(args, app, recorder, resources, expected)
    except BaseException as exc:
        failure = exc
        recorder.result["sweep_outcome"] = getattr(exc, "category", "INFRASTRUCTURE")
        recorder.fail(exc)
    finally:
        if "contacts" in resources:
            try:
                recorder.result["contact_summary"] = _contact_summary(resources["contacts"])
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, "contact_summary")
        if "monitor" in resources:
            try:
                recorder.result["monitor_summary"] = resources["monitor"].summary()
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, "monitor_summary")
        if "trace" in resources:
            recorder.result["csv_sample_count"] = resources["trace"].count
            try:
                resources["trace"].close()
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, "trace_close")
        setup = recorder.result.get("external_forces_setup")
        if setup is not None and setup.get("after") is not None:
            try:
                from _cr12_external_forces import read_scene_external_forces
                stage, schema, physics, default_time = resources["external_forces_context"]
                read_scene_external_forces(stage, setup, "before_exit", schema, physics, default_time)
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, "external_forces_exit_readback")
        if resources.get("sim") is not None:
            try:
                recorder.phase = "simulation_stop"
                resources["sim"]._disable_app_control_on_stop_handle = True
                resources["sim"].stop()
                recorder.result["simulation_stop_returned"] = True
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc)
        if app is not None:
            recorder.phase = "app_close"
            recorder.result["app_close_requested"] = True
            for action in (recorder.save, lambda: recorder.emit("app_close_begin",
                    work_completed=recorder.result["work_completed"],
                    failures=len(recorder.result["failures"])+len(recorder.result["secondary_failures"]))):
                try:
                    action()
                except BaseException as exc:
                    failure = failure or exc
                    recorder.secondary(exc, "pre_close_recording")
            try:
                app.close()
                recorder.emit("app_close_returned")
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc)
        else:
            recorder.save()
    if failure is not None:
        raise failure
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
