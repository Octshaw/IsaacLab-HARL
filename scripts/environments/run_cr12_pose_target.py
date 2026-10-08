"""One bounded CR12 scanner pose, using the reviewed fixed-base v1 configuration.

No simulator imports or work occur when importing this entry. Runtime resources
are created only by main, after the accepted Windows/pre-App CUDA preparation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from _cr12_runtime_support import (
    DriveCheckError, Recorder, _assert_active, _body_poses, _capture_submitted_targets,
    _check_contacts, _check_frames, _check_geometry, _clock, _contact_summary,
    check_clock, create_fixed_cr12_scene, initialize_fixed_cr12_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
APPROVED_USD = REPO_ROOT / 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd'


def parse_args(app_launcher_type):
    from _cr12_external_forces import add_external_forces_arguments, external_forces_source

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usd-path', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--motion-profile', choices=('formal', 'manual_visible_local_v1'), default='formal')
    parser.add_argument('--physics_steps', type=int, default=None)
    parser.add_argument('--pd-profile', choices=('baseline',), default='baseline')
    parser.add_argument('--visual-debug-pose', action='store_true')
    parser.add_argument('--view-preset', choices=('overall', 'wrist', 'wrist-oblique', 'arm-oblique'), default='overall')
    add_external_forces_arguments(parser)
    app_launcher_type.add_app_launcher_args(parser)
    args = parser.parse_args()
    args.external_forces_source = external_forces_source(sys.argv[1:])
    if args.external_forces_every_iteration != 'on' or args.external_forces_source != 'explicit_cli':
        parser.error('This pose experiment requires explicit --external-forces-every-iteration on')
    from _cr12_pose_control import select_motion_profile
    profile = select_motion_profile(args.motion_profile)
    if args.physics_steps is None:
        args.physics_steps = profile.max_steps
    if args.physics_steps != profile.max_steps:
        parser.error(f'{profile.name} requires its fixed {profile.max_steps}-step budget')
    if args.device != 'cuda:0' or args.headless or args.enable_cameras or args.livestream not in (-1, 0) or getattr(args, 'xr', False):
        parser.error('GUI / cuda:0 only, without scan cameras, livestream or XR')
    if sys.flags.utf8_mode != 1:
        parser.error('Enable PYTHONUTF8 before creating this Python process')
    for key in ('HEADLESS', 'ENABLE_CAMERAS', 'LIVESTREAM', 'XR'):
        if os.environ.get(key) not in (None, '', '0'):
            parser.error(f'{key} would change the reviewed mode')
    args.usd_path = args.usd_path.expanduser().resolve(strict=True)
    if args.usd_path != APPROVED_USD.resolve(strict=True):
        parser.error('Only the accepted fixed_lift0_v1 USD is allowed')
    args.output_dir = args.output_dir.expanduser().resolve()
    return args


# Compatibility exports: shared control and trace have one implementation.
from _cr12_scan_executor import (
    Cr12PoseControlSession, PoseTrace, _native_state, _native_jacobian,
    _pose_record, _checked_tick_guard, finish_sample_trace, manual_motion_outcome,
)


def _classified_failure(exc, phase):
    from _cr12_pose_control import PoseCheckError
    if isinstance(exc, PoseCheckError):
        return exc
    physical = {'forbidden_contact', 'geometry_guard', 'fixed_root_drift', 'fixed_frame_drift',
                'physics_count', 'joint_limit', 'state_invalid', 'target_mismatch', 'tracking'}
    category = getattr(exc, 'category', None)
    if category in physical:
        return PoseCheckError('PHYSICS_GUARD', str(exc), original_category=category,
                              original_type=type(exc).__name__, original_details=getattr(exc, 'details', {}))
    if isinstance(exc, DriveCheckError):
        return PoseCheckError('SETUP' if phase != 'controlled_pose' else 'PHYSICS_GUARD', str(exc),
                              original_category=category, original_type=type(exc).__name__,
                              original_details=getattr(exc, 'details', {}))
    return exc


def _pose_ticks(args, app, recorder, resources, expected, *, scene=None, initial=None,
                continue_after_arrival=False, before_render=None, continuation=None):
    """Compatibility driver for the same externally schedulable pose session."""
    import _cr12_pose_control as pc

    profile = pc.select_motion_profile(args.motion_profile)
    if continue_after_arrival and profile.manual_visual_only:
        raise pc.PoseCheckError('SETUP', 'Capture continuation requires the formal pose profile')
    if continuation is not None and (not continue_after_arrival or profile.manual_visual_only):
        raise pc.PoseCheckError('SETUP', 'Two-view context requires the explicit formal continuation path')
    if (scene is None) != (initial is None):
        raise pc.PoseCheckError('SETUP', 'Supply scene and initial together')
    if scene is None:
        scene = create_fixed_cr12_scene(args, app, recorder, resources, expected)
        initial = initialize_fixed_cr12_state(args, recorder, scene)
    session = Cr12PoseControlSession(
        args, app, recorder, resources, expected, scene=scene, initial=initial,
        integration=False, continuation=continuation,
        continue_after_arrival=continue_after_arrival)
    maximum = 3600 if continuation is not None else 1800 if continue_after_arrival else profile.max_steps
    for _ in range(maximum):
        try:
            token = session.prepare_tick()
            session.submit_prepared(token)
            session.sim.step(render=False)
            render_context = session.observe_physics()
            rendered = session.render_due
            if rendered:
                if before_render is not None:
                    before_render(render_context)
                session.sim.render()
            tick = session.finish_tick(rendered)
        except BaseException as exc:
            session.abort(exc)
            raise
        if tick is None:
            return
        yield tick
    if continuation is not None:
        raise pc.PoseCheckError('TOTAL_BUDGET', 'Two-view caller exhausted 3600 controlled ticks')
    if continue_after_arrival:
        raise pc.PoseCheckError('TOTAL_BUDGET', 'Capture caller exhausted 1800 controlled ticks')
    raise pc.PoseCheckError('TIMEOUT', f'No complete stable arrival window within {profile.max_steps} controlled steps')


def _run_pose(args, app, recorder, resources, expected):
    # Original entry consumes the same loop and ends at its original arrival.
    for _ in _pose_ticks(args, app, recorder, resources, expected):
        pass


def main():
    recorder, resources = Recorder(), {}
    app = None
    failure = None
    recorder.emit('process_start', python=sys.executable, cwd=os.getcwd(), argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode)
    try:
        from isaaclab.app import AppLauncher
        args = parse_args(AppLauncher)
        manual_only = args.motion_profile == 'manual_visible_local_v1'
        recorder.result.update(motion_profile=args.motion_profile, MANUAL_VISUAL_ONLY=manual_only)
        recorder.emit('motion_profile_selected', motion_profile=args.motion_profile, MANUAL_VISUAL_ONLY=manual_only)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result_path = args.output_dir / 'result.json'
        if result_path.exists():
            raise FileExistsError(f'Refusing existing result: {result_path}')
        recorder.path = result_path
        resources['trace'] = PoseTrace(args.output_dir / 'pose_joint_trace.csv')
        from _cr12_asset_math import validate_derived
        from _cr12_hold_diagnostics import select_pd_profile
        from _windows_runtime_startup import prepare_windows_runtime_args
        from view_scan_assignment import _prepare_cuda_before_app
        expected = validate_derived(args.usd_path.parent.parent / 'cr12_fixed_lift0.urdf')
        recorder.result.update(usd_path=str(args.usd_path), python=sys.executable, entry_source=__file__,
                               utf8_mode=sys.flags.utf8_mode, original_argv=list(sys.argv),
                               pd_selection=select_pd_profile('baseline'), visual_debug_pose=args.visual_debug_pose,
                               view_preset=args.view_preset, pose_outcome='NOT_REACHED',
                               external_forces_request={'mode':'on', 'source':args.external_forces_source},
                               git_head=subprocess.run(['git','rev-parse','HEAD'],cwd=REPO_ROOT,capture_output=True,
                                                       text=True,timeout=5,check=True).stdout.strip())
        recorder.phase = 'startup_preparation'
        startup = prepare_windows_runtime_args(args, list(sys.argv))
        if startup['requested_backend'] != 'D3D12':
            raise DriveCheckError('SETUP', 'This approved experiment requires D3D12')
        recorder.result['startup'] = startup
        recorder.emit('startup_prepared', **startup)
        recorder.emit('pre_app_cuda_begin')
        recorder.result['pre_app_cuda'] = _prepare_cuda_before_app(args.device)
        recorder.emit('pre_app_cuda_ready', **recorder.result['pre_app_cuda'])
        recorder.phase = 'app_create'
        recorder.save()
        recorder.emit('app_create_begin')
        launcher = AppLauncher(args)
        app = launcher.app
        import carb
        settings = carb.settings.get_settings()
        effective = {'experience':launcher._sim_experience_file, 'kit_log_file':settings.get('/log/file'),
                     'vulkan_setting':settings.get('/app/vulkan'), 'headless':launcher._headless,
                     'enable_cameras':launcher._enable_cameras, 'livestream':launcher._livestream,
                     'xr':launcher._xr, 'device':args.device}
        recorder.result['app'] = effective
        recorder.emit('app_ready', **effective)
        if launcher._headless or launcher._enable_cameras or launcher._livestream or launcher._xr or settings.get('/app/vulkan') is not False:
            raise DriveCheckError('SETUP', 'Effective mode differs from GUI/D3D12/cuda:0 without cameras')
        _run_pose(args, app, recorder, resources, expected)
    except BaseException as exc:
        failure = _classified_failure(exc, recorder.phase)
        category = getattr(failure, 'category', 'INFRASTRUCTURE')
        recorder.result['pose_outcome'] = (manual_motion_outcome(category)
            if recorder.result.get('MANUAL_VISUAL_ONLY') else category)
        recorder.fail(failure)
    finally:
        if 'contacts' in resources:
            try:
                recorder.result['contact_summary'] = _contact_summary(resources['contacts'])
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, 'contact_summary')
        if resources.get('trace') is not None:
            try:
                recorder.result['csv_sample_count'] = resources['trace'].count
                resources['trace'].close()
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, 'trace_close')
        setup = recorder.result.get('external_forces_setup')
        if setup is not None and setup.get('after') is not None:
            try:
                from _cr12_external_forces import read_scene_external_forces
                stage, schema, physics, default_time = resources['external_forces_context']
                read_scene_external_forces(stage, setup, 'before_exit', schema, physics, default_time)
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc, 'external_forces_exit_readback')
        if resources.get('sim') is not None:
            try:
                recorder.phase = 'simulation_stop'
                resources['sim']._disable_app_control_on_stop_handle = True
                resources['sim'].stop()
                recorder.result['simulation_stop_returned'] = True
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc)
        if app is not None:
            recorder.phase = 'app_close'
            recorder.result['app_close_requested'] = True
            for action in (recorder.save, lambda: recorder.emit(
                    'app_close_begin', work_completed=recorder.result['work_completed'],
                    failures=len(recorder.result['failures'])+len(recorder.result['secondary_failures']))):
                try:
                    action()
                except BaseException as exc:
                    failure = failure or exc
                    recorder.secondary(exc, 'pre_close_recording')
            try:
                app.close()
                recorder.emit('app_close_returned')
            except BaseException as exc:
                failure = failure or exc
                recorder.fail(exc)
        else:
            recorder.save()
    if failure is not None:
        raise failure
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
