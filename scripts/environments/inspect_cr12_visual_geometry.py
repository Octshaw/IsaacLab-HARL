"""Pre-initialization CR12 render overlay and bounded 120-tick compatibility hold.

One pre-physics apply; all native parameter reads precede pause/screenshots.
No live layer switching, motion task, scan sensor, or original asset saving.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time
import xml.etree.ElementTree as ET

from _cr12_runtime_support import (Recorder, DriveCheckError, create_fixed_cr12_scene,
    initialize_fixed_cr12_state, _clock, _read_physics, _contact_summary,
    _assert_active, _body_poses, _check_contacts, _check_frames, _check_geometry,
    _capture_submitted_targets, check_clock)
from run_cr12_manual_joint_sweep import validate_private_path, APPROVED_USD, REPO_ROOT


def parse_args(app_launcher_type, argv=None):
    from _cr12_external_forces import add_external_forces_arguments, external_forces_source
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manual-check", action="store_true")
    add_external_forces_arguments(parser)
    app_launcher_type.add_app_launcher_args(parser)
    values = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(values)
    args.external_forces_source = external_forces_source(values)
    if args.external_forces_every_iteration != "on" or args.external_forces_source != "explicit_cli":
        parser.error("Explicit external-forces-every-iteration on required")
    if (args.device != "cuda:0" or args.headless or args.enable_cameras
            or args.livestream not in (-1, 0) or getattr(args, "xr", False)):
        parser.error("Only GUI cuda:0, no scan cameras/livestream/XR")
    if sys.flags.utf8_mode != 1 or any(os.environ.get(k) not in (None, "", "0") for k in ("HEADLESS", "ENABLE_CAMERAS", "LIVESTREAM", "XR")):
        parser.error("Start UTF8 Python with GUI environment")
    args.usd_path = args.usd_path.resolve(strict=True)
    args.output_dir = args.output_dir.resolve()
    if args.usd_path != APPROVED_USD.resolve(strict=True):
        parser.error("Only accepted v1 USD")
    try:
        args.private_user_config = validate_private_path(args.kit_args, args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    return args


def png_complete(path):
    """Observe a completed PNG without rewriting/cropping the screenshot."""
    path = Path(path)
    if not path.is_file():
        return None
    data = path.read_bytes()
    if len(data) < 32 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[-12:-8] != b"\0\0\0\0" or data[-8:-4] != b"IEND":
        return None
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        return None
    return {"width": width, "height": height, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


HOLDING_STEPS = 120
GUARDS = ("clock", "joint", "contact", "geometry", "frame", "render_clock")


def source_protection(usd):
    """Only original URDF/referenced OBJ and the seven existing v1 files."""
    asset = usd.parents[3]
    original = asset / "rokea_cr12_7DOF.urdf"
    paths = {original}
    for mesh in ET.fromstring(original.read_bytes()).findall(".//mesh"):
        path = Path(mesh.get("filename"))
        paths.add(path if path.is_absolute() else (asset / path).resolve(strict=True))
    paths.update(p for p in usd.parent.parent.rglob("*") if p.is_file())
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def phase_saved(recorder, phase, **facts):
    recorder.phase = phase
    recorder.result.setdefault("phase_order", []).append(phase)
    recorder.emit(phase, **facts)
    recorder.save()


def native_view_validity(robot, sim):
    """Use exposed SimulationView.is_valid/check and ArticulationView.check.

    No parameter getter is attempted on known-invalid views. A missing native
    query is reported NOT_EXPOSED, never fabricated as valid. None is invalid,
    not evidence that a query is unavailable.
    """
    facts = {"robot_initialized": bool(robot.is_initialized)}
    if not facts["robot_initialized"]:
        raise DriveCheckError("NATIVE_VIEW_INVALID", "Articulation is not initialized", validity=facts)
    view = sim.physics_sim_view
    facts["simulation_view_present"] = view is not None
    if view is None:
        raise DriveCheckError("NATIVE_VIEW_INVALID", "Simulation tensor view is absent", validity=facts)
    facts["simulation_is_valid"] = bool(view.is_valid) if hasattr(view, "is_valid") else "NOT_EXPOSED"
    if facts["simulation_is_valid"] is False:
        raise DriveCheckError("NATIVE_VIEW_INVALID", "Simulation tensor view is invalid", validity=facts)
    check = getattr(view, "check", None)
    facts["simulation_check"] = bool(check()) if callable(check) else "NOT_EXPOSED"
    if facts["simulation_check"] is False:
        raise DriveCheckError("NATIVE_VIEW_INVALID", "Simulation view check failed", validity=facts)
    articulation = robot.root_physx_view
    check = getattr(articulation, "check", None)
    facts["articulation_check"] = bool(check()) if callable(check) else "NOT_EXPOSED"
    if articulation is None or facts["articulation_check"] is False:
        raise DriveCheckError("NATIVE_VIEW_INVALID", "Articulation tensor view check failed", validity=facts)
    return facts


def read_native_snapshot(scene, expected, recorder, label):
    """A fresh accepted read, independently copied and persisted before later getters."""
    sim, robot = scene["sim"], scene["robot"]
    recorder.phase = "native_" + label + "_reading"
    validity = native_view_validity(robot, sim)
    clock = _clock(sim)
    recorder.result.setdefault("native_read_attempts", {})[label] = {"validity": validity, "clock": list(clock)}
    recorder.save()
    _, _, checked = _read_physics(robot, expected["bodies"], scene["configuration"], recorder, scene["selected_pd"])
    snapshot = {"raw": copy.deepcopy(recorder.result["physx_raw_readback"]),
                "checked": copy.deepcopy(checked), "validity": copy.deepcopy(validity),
                "clock": list(clock), "expected_pass": True,
                "copy_method": "accepted getter host() synchronizes via cpu and copies float64; deepcopy lists immediately"}
    recorder.result.setdefault("native_snapshots", {})[label] = snapshot
    recorder.save()
    if _clock(sim) != clock:
        raise DriveCheckError("physics_count", "Native parameter read advanced physics")
    phase_saved(recorder, "native_" + label + "_saved")
    return snapshot


def compare_native_parameters(first, final):
    """Same parameter fields and tolerances as the accepted independent checker."""
    import numpy as np
    a, b = first["raw"], final["raw"]
    for key in ("body_order", "joint_order", "inertia_convention"):
        if a[key] != b[key]:
            raise DriveCheckError("physical_invariance", "Native ordering/convention changed", field=key)
    fields = [(key, a[key], b[key], rtol, atol) for key, rtol, atol in (
        ("mass", 1e-5, 1e-6), ("com_local_xyz_xyzw", 0, 1e-5),
        ("inertia_about_com_body_axes", 1e-4, 1e-6))]
    if set(a["joint_parameters"]) != set(b["joint_parameters"]):
        raise DriveCheckError("physical_invariance", "Native joint parameter fields changed")
    fields.extend((key, a["joint_parameters"][key], b["joint_parameters"][key],
                   0 if key in ("friction", "armature") else 1e-4, 1e-6)
                  for key in a["joint_parameters"])
    differences = {}
    for key, left, right, rtol, atol in fields:
        left, right = np.asarray(left), np.asarray(right)
        if left.shape != right.shape or not np.isfinite([left, right]).all() or not np.allclose(left, right, rtol=rtol, atol=atol):
            raise DriveCheckError("physical_invariance", "Native physical parameter changed", field=key)
        differences[key] = {"max_abs_difference": float(np.max(np.abs(left-right))), "rtol": rtol, "atol": atol}
    for key in ("body_order", "joint_order", "body_indices", "joint_indices", "is_fixed_base"):
        if first["checked"][key] != final["checked"][key]:
            raise DriveCheckError("physical_invariance", "Native articulation metadata changed", field=key)
    return {"equal": True, "parameter_differences": differences,
            "runtime_q_dq_world_poses_compared_as_configuration": False}


def check_hold_state(q, dq, limits):
    """Accepted finite/hard-limit/actual-speed guards, no task tracking window."""
    import numpy as np
    q, dq, limits = np.asarray(q), np.asarray(dq), np.asarray(limits)
    if q.shape != (6,) or dq.shape != (6,) or limits.shape != (6, 2) or not all(np.isfinite(x).all() for x in (q, dq, limits)):
        raise DriveCheckError("state_invalid", "Expected finite six-axis state and limits")
    if np.any(q < limits[:, 0]-1e-3) or np.any(q > limits[:, 1]+1e-3):
        raise DriveCheckError("joint_limit", "Original hard joint limit exceeded")
    if np.any(np.abs(dq) > .25):
        raise DriveCheckError("tracking", "Actual joint speed exceeds original 0.25 rad/s")
    return float(np.max(np.abs(q))), float(np.max(np.abs(dq)))


def run_hold(app, scene, initial, recorder):
    import numpy as np
    import torch
    sim, robot = scene["sim"], scene["robot"]
    dt = scene["configuration"].PHYSICS_DT
    joint_ids, baseline = scene["joint_ids"], initial["baseline"]
    zero = torch.zeros((1, 6), device=robot.device, dtype=torch.float32)
    limits = recorder.result["physx_readback"]["joints"]["position_limits"]
    stats = {"complete": False, "steps": 0, "guard_pass_counts": {k: 0 for k in GUARDS},
             "render_calls": 0, "position_target_rad": [0.0]*6, "velocity_target_rad_s": [0.0]*6,
             "maximum_abs_position_rad": 0.0, "maximum_abs_speed_rad_s": 0.0,
             "maximum_forbidden_contact_n": 0.0, "minimum_arm_z_m": None,
             "runtime_joint_state_writes": 0, "runtime_root_state_writes": 0}
    recorder.result["holding_check"] = stats
    recorder.phase = "controlled_hold"
    for step in range(1, HOLDING_STEPS+1):
        _assert_active(app, sim)
        before = _clock(sim)
        robot.set_joint_position_target(zero, joint_ids=joint_ids)
        robot.set_joint_velocity_target(zero, joint_ids=joint_ids)
        robot.write_data_to_sim()
        _capture_submitted_targets(robot, joint_ids, zero, zero)
        if step == 1:
            recorder.result["controlled_step_attempted"] = True
            recorder.save()
            recorder.emit("controlled_step_begin", step=1)
        sim.step(render=False)
        after = _clock(sim)
        recorder.result["completed_physics_steps"] = after[0]-baseline[0]
        recorder.result["controlled_simulation_time_s"] = after[1]-baseline[1]
        check_clock(*before, *after, dt)
        stats["guard_pass_counts"]["clock"] += 1
        robot.update(dt)
        view = robot.root_physx_view
        q = view.get_dof_positions()[0, joint_ids].detach().cpu().numpy().copy()
        dq = view.get_dof_velocities()[0, joint_ids].detach().cpu().numpy().copy()
        displacement, speed = check_hold_state(q, dq, limits)
        stats["guard_pass_counts"]["joint"] += 1
        force = _check_contacts(scene["contacts"], dt)
        stats["guard_pass_counts"]["contact"] += 1
        poses = _body_poses(robot, scene["body_ids"])
        minimum_z = _check_geometry(scene["info"]["colliders"], poses, scene["configuration"].CONTACT_OFFSET)
        stats["guard_pass_counts"]["geometry"] += 1
        _check_frames(scene["stage"], scene["info"], scene["frames"], poses, initial["initial_root"])
        stats["guard_pass_counts"]["frame"] += 1
        if step % 2 == 0:
            sim.render()
            stats["render_calls"] += 1
        if _clock(sim) != after:
            raise DriveCheckError("physics_count", "Render advanced physics")
        _assert_active(app, sim)
        stats["guard_pass_counts"]["render_clock"] += 1
        stats.update(steps=step, maximum_abs_position_rad=max(stats["maximum_abs_position_rad"], displacement),
                     maximum_abs_speed_rad_s=max(stats["maximum_abs_speed_rad_s"], speed),
                     maximum_forbidden_contact_n=max(stats["maximum_forbidden_contact_n"], force),
                     minimum_arm_z_m=minimum_z if stats["minimum_arm_z_m"] is None else min(stats["minimum_arm_z_m"], minimum_z),
                     last_q_rad=q.tolist(), last_dq_rad_s=dq.tolist())
        if step % 30 == 0:
            recorder.save()
    stats.update(complete=True, clock_before=list(baseline), clock_after=list(_clock(sim)))
    recorder.result["contact_summary"] = _contact_summary(scene["contacts"])
    phase_saved(recorder, "holding_completed", steps=stats["steps"])


def commit_pause(timeline):
    """Commit queued pause on the main thread, without a UI/physics update."""
    timeline.pause()
    timeline.commit()
    if timeline.is_playing() or timeline.is_stopped():
        raise DriveCheckError("render_pause", "Committed timeline is not paused")


def render_corrected(args, app, scene, recorder):
    """After pause: no robot/Tensor getter, reset, physics step or layer mutation."""
    import numpy as np
    import omni.timeline
    from omni.kit.viewport.utility import get_active_viewport, capture_viewport_to_file
    from omni.kit.async_engine import run_coroutine
    from pxr import UsdGeom
    sim, stage = scene["sim"], scene["stage"]
    timeline = omni.timeline.get_timeline_interface()
    clock, timeline_time = _clock(sim), float(timeline.get_current_time())
    commit_pause(timeline)
    recorder.result["paused_state"] = {"clock": list(clock), "timeline_time": timeline_time,
        "playing": bool(timeline.is_playing()), "stopped": bool(timeline.is_stopped()),
        "native_reads_after_pause": 0, "method": "main-thread pause + commit; separate clocks checked without native getters"}
    phase_saved(recorder, "timeline_paused")
    viewport = get_active_viewport()
    if viewport is None:
        raise DriveCheckError("viewport", "No active GUI viewport")
    recorder.result["viewport"] = {"resolution": list(viewport.resolution), "camera_path": str(viewport.camera_path),
        "existing_render_product": str(viewport.render_product_path), "new_render_product_created": False}
    # Covers full scanner bounds (head and bracket), unlike the prior cropped view.
    views = {"scanner": {"eye": (1.03, -.98, 3.58), "target": (.23, -.03, 3.08)},
             "agv": {"eye": (1.75, -2.2, 1.35), "target": (0, 0, .53)}}
    recorder.result["views"] = views
    screenshots = recorder.result.setdefault("screenshots", [])
    total_updates = 0
    def assert_frozen():
        if (not app.is_running() or timeline.is_playing() or timeline.is_stopped()
                or _clock(sim) != clock or float(timeline.get_current_time()) != timeline_time):
            raise DriveCheckError("render_physics_advanced", "Paused clocks/timeline changed")
    def update():
        nonlocal total_updates
        assert_frozen()
        app.update()
        total_updates += 1
        assert_frozen()
    assert_frozen()
    for view_name in ("scanner", "agv"):
        recorder.phase = "capture_" + view_name
        path = args.output_dir / f"{view_name}_corrected.png"
        if path.exists():
            raise FileExistsError(path)
        start_updates = total_updates
        sim.set_camera_view(**views[view_name])
        for _ in range(12):
            update()
        capture_api = capture_viewport_to_file(viewport, str(path), is_hdr=False)
        future = run_coroutine(capture_api.wait_for_result(completion_frames=2))
        complete = None
        try:
            while total_updates-start_updates < 60:
                update()
                if future.done():
                    future.result()
                    complete = png_complete(path)
                    if complete:
                        break
                time.sleep(.03)
            if complete is None:
                raise DriveCheckError("screenshot_timeout", "PNG not complete within 60 updates", view=view_name)
        finally:
            if not future.done():
                future.cancel()
        if args.manual_check:
            # Static observation within the same per-view 60-update cap.
            while total_updates-start_updates < 60:
                update()
                time.sleep(.3)
        camera = UsdGeom.Camera(stage.GetPrimAtPath(str(viewport.camera_path)))
        if not camera:
            raise DriveCheckError("viewport", "Cannot read existing spectator")
        item = {"path": str(path), "view": view_name, "condition": "corrected",
                "render_updates": total_updates-start_updates, "physics_advanced": False,
                "clock_before_after": list(clock), "timeline_time_before_after": timeline_time, **complete,
                "spectator_readback": {"path": str(viewport.camera_path), "resolution": list(viewport.resolution),
                    "world_matrix": np.asarray(UsdGeom.Xformable(camera.GetPrim()).ComputeLocalToWorldTransform(scene["default_time"])).tolist(),
                    "focal_length": camera.GetFocalLengthAttr().Get(),
                    "horizontal_aperture": camera.GetHorizontalApertureAttr().Get(),
                    "vertical_aperture": camera.GetVerticalApertureAttr().Get()}}
        screenshots.append(item)
        recorder.emit("viewport_captured", **item)
        recorder.save()
    assert_frozen()
    recorder.result["render_comparison"] = {"complete": True, "pass": True, "timeline_paused": True,
        "physics_steps_unchanged": True, "total_ui_updates": total_updates, "new_images": len(screenshots),
        "comparison_type": "corrected-only; no repeat of previous A/B", "native_getters_after_pause": 0,
        "user_appearance_acceptance": "PENDING_USER_REVIEW"}
    phase_saved(recorder, "screenshots_completed")


def _run_check(args, app, recorder, resources, expected):
    import omni.physx
    import omni.timeline
    from _cr12_visual_geometry import inspect_preinit_mapping, physical_snapshot, CollisionVisualOverride
    from _cr12_external_forces import read_scene_external_forces

    protected = source_protection(args.usd_path)
    recorder.result["asset_protection"] = {"status": "BEFORE_ONLY", "count": len(protected)}
    recorder.result["native_snapshots"] = {"initial": {"status": "NOT_RUN"}, "final": {"status": "NOT_RUN"}}
    derived = args.usd_path.parent.parent / "cr12_fixed_lift0.urdf"
    holder = {}
    def pre_physics(*, stage, sim, robot, info):
        recorder.phase = "visual_preinit"
        native = omni.physx.get_physx_interface()
        timeline = omni.timeline.get_timeline_interface()
        timing = {"robot_initialized": bool(robot.is_initialized),
                  "simulation_view_present": sim.physics_sim_view is not None,
                  "robot_view_present": getattr(robot, "_root_physx_view", None) is not None,
                  "physics_initialized": bool(sim.is_simulating()), "physics_running": bool(native.is_running()),
                  "timeline_playing": bool(timeline.is_playing()), "timeline_stopped": bool(timeline.is_stopped()),
                  "attached_stage_id_observed": int(omni.physx.get_physx_simulation_interface().get_attached_stage())}
        recorder.result["preinit_timing"] = timing
        recorder.save()
        if (any(timing[k] for k in ("robot_initialized", "simulation_view_present", "robot_view_present",
                                   "physics_initialized", "physics_running", "timeline_playing"))
                or not timing["timeline_stopped"] or timing["attached_stage_id_observed"] != 0):
            raise DriveCheckError("preinit_timing", "Physics/view already initialized before visual apply", actual=timing)
        mapping = inspect_preinit_mapping(stage, "/World/CR12", derived)
        recorder.result["visual_mapping"] = mapping
        recorder.save()
        if not mapping["pass"]:
            raise DriveCheckError("visual_mapping", "Independent visual/collision identity unresolved", errors=mapping["errors"])
        override = CollisionVisualOverride(stage, mapping)
        before = physical_snapshot(stage, "/World/CR12")
        edit_target = stage.GetEditTarget().GetLayer().identifier
        applied = override.apply(before_first_physics_initialization=True)
        after = physical_snapshot(stage, "/World/CR12")
        if before != after:
            raise DriveCheckError("physical_invariance", "Adjacent preinit composed physical snapshots differ")
        if stage.GetEditTarget().GetLayer().identifier != edit_target:
            raise DriveCheckError("render_layer", "Original edit target not restored")
        override.seal_before_physics_initialization()
        holder["override"] = override
        stable = override.verify_stable("preinit")
        recorder.result["render_override"] = applied
        recorder.result["visual_preinit"] = {"complete": True, "apply_count": 1, "pre_physics_confirmed": True,
            "collision_leaves_invisible": stable["collision_leaves_invisible"], "visuals_visible": stable["visuals_visible"],
            "unchanged_during_run": False, "revoke_count": 0, "reapply_count": 0,
            "composed_apply_equal": True, "composed_prim_count": len(before),
            "composed_digest": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
            "stage_checks": [stable], "edit_target_restored": True}
        phase_saved(recorder, "overlay_applied_preinit")
    def before_setup_native(*, robot, sim):
        recorder.result["setup_native_validity"] = native_view_validity(robot, sim)
        recorder.save()

    scene = create_fixed_cr12_scene(args, app, recorder, resources, expected,
                                    pre_physics=pre_physics, before_native_read=before_setup_native)
    initial = initialize_fixed_cr12_state(args, recorder, scene)
    override = holder["override"]
    stages = recorder.result["visual_preinit"]["stage_checks"]
    stages.append(override.verify_stable("after_initialization"))
    # create_fixed_cr12_scene retains its accepted setup read before the one-time
    # joint-state write. The two independent comparison snapshots below follow it.
    first = read_native_snapshot(scene, expected, recorder, "initial")
    first_witness = copy.deepcopy(first)
    run_hold(app, scene, initial, recorder)
    final = read_native_snapshot(scene, expected, recorder, "final")
    if first != first_witness:
        raise DriveCheckError("physical_invariance", "Retained initial snapshot mutated")
    compared = compare_native_parameters(first, final)
    stages.append(override.verify_stable("after_final_native"))
    recorder.result["physical_invariance"] = {"pass": True, "composed_apply_equal": True,
        "initial_native_expected_pass": True, "final_native_equal": compared["equal"], "native_reads_before_pause": True,
        "independent_snapshots": True, "initial_snapshot_retained_unchanged": True,
        "comparison": compared, "native_cooked_hull_vertices": "NOT_READ"}
    read_scene_external_forces(scene["stage"], scene["setup"], "before_render",
                              scene["physx_schema"], scene["usd_physics"], scene["default_time"])
    recorder.save()
    render_corrected(args, app, scene, recorder)
    stages.append(override.verify_stable("after_screenshots"))
    recorder.result["visual_preinit"]["unchanged_during_run"] = True
    if source_protection(args.usd_path) != protected:
        raise DriveCheckError("asset_protection", "Original asset content changed")
    recorder.result["asset_protection"] = {"pass": True, "count": len(protected), "files_sha256": protected}
    recorder.result["visual_check"] = {"complete": True, "route": "B_preinit_once",
                                      "camera_sensor": "NOT_IMPLEMENTED_NOT_VALIDATED"}
    recorder.result.update(status="WORK_COMPLETED_PENDING_PROCESS_EXIT", work_completed=True,
                          classification="VISUAL_PREINIT_INTEGRATION_PASS", diagnostics_complete=True)
    phase_saved(recorder, "work_completed", completed_physics_steps=HOLDING_STEPS)


def cleanup_failure(recorder, exc, phase, primary):
    """Keep a cleanup error separate when an earlier work failure already exists."""
    if primary is None:
        recorder.fail(exc, phase)
        return exc
    recorder.secondary(exc, phase)
    try:
        recorder.save()
    except BaseException as io_error:
        recorder.secondary(io_error, "cleanup_failure_recording")
    return primary


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
        from _cr12_collision_refinement import load_accepted_inputs
        from _cr12_hold_diagnostics import select_pd_profile
        from _windows_runtime_startup import prepare_windows_runtime_args
        from view_scan_assignment import _prepare_cuda_before_app
        derived = args.usd_path.parent.parent / "cr12_fixed_lift0.urdf"
        expected = load_accepted_inputs(derived)
        recorder.result.update(usd_path=str(args.usd_path), python=sys.executable, entry_source=__file__,
            original_argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode, pd_selection=select_pd_profile("baseline"),
            private_user_config=args.private_user_config, manual_check=args.manual_check,
            external_forces_request={"mode": "on", "source": args.external_forces_source})
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
            raise DriveCheckError("SETUP", "Effective GUI/private mode differs")
        _run_check(args, app, recorder, resources, expected)
    except BaseException as exc:
        failure = exc
        recorder.fail(exc)
    finally:
        setup = recorder.result.get("external_forces_setup")
        if setup is not None and setup.get("after") is not None:
            try:
                from _cr12_external_forces import read_scene_external_forces
                stage, schema, physics, default_time = resources["external_forces_context"]
                read_scene_external_forces(stage, setup, "before_exit", schema, physics, default_time)
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, "external_forces_exit_readback", failure)
        if "contacts" in resources:
            try:
                recorder.result["contact_summary"] = _contact_summary(resources["contacts"])
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, "contact_summary", failure)
        if resources.get("sim") is not None:
            try:
                recorder.phase = "simulation_stop"
                resources["sim"]._disable_app_control_on_stop_handle = True
                resources["sim"].stop()
                recorder.result["simulation_stop_returned"] = True
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, "simulation_stop", failure)
        if app is not None:
            recorder.phase = "app_close"
            recorder.result["app_close_requested"] = True
            for action in (recorder.save, lambda: recorder.emit("app_close_begin", work_completed=recorder.result["work_completed"], failures=len(recorder.result["failures"])+len(recorder.result["secondary_failures"]))):
                try:
                    action()
                except BaseException as exc:
                    failure = cleanup_failure(recorder, exc, "pre_close_recording", failure)
            try:
                app.close()
                recorder.emit("app_close_returned")
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, "app_close", failure)
        else:
            recorder.save()
    if failure is not None:
        raise failure
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
