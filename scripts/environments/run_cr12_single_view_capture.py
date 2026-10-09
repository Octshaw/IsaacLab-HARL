"""One formal CR12 target, one on-demand camera frame, verified OFF and exit.

This entry owns the single simulation clock. Original pose commands, scene and
guards are reused; the dedicated camera adapter never advances simulation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from _cr12_runtime_support import (Recorder, DriveCheckError, _clock, _read_physics,
    _contact_summary, create_fixed_cr12_scene, initialize_fixed_cr12_state)
from run_cr12_manual_joint_sweep import validate_private_path, APPROVED_USD


def parse_args(app_launcher_type, argv=None, *, configure_parser=None):
    from _cr12_external_forces import add_external_forces_arguments, external_forces_source
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usd-path', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--manual-check', action='store_true')
    parser.add_argument('--gui-startup-diagnostics', action='store_true',
                        help='Record read-only Windows GUI startup facts and enforce the frozen DPI experiment.')
    add_external_forces_arguments(parser)
    app_launcher_type.add_app_launcher_args(parser)
    if configure_parser is not None:
        configure_parser(parser)
    values = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(values)
    args.external_forces_source = external_forces_source(values)
    if args.external_forces_every_iteration != 'on' or args.external_forces_source != 'explicit_cli':
        parser.error('Explicit --external-forces-every-iteration on is required')
    if (args.device != 'cuda:0' or args.headless or not args.enable_cameras
            or args.livestream not in (-1, 0) or getattr(args, 'xr', False)):
        parser.error('This entry requires GUI/cuda:0/--enable_cameras, without livestream/XR')
    if sys.flags.utf8_mode != 1 or any(os.environ.get(k) not in (None, '', '0') for k in ('HEADLESS', 'LIVESTREAM', 'XR')):
        parser.error('Start a UTF8 Python process with the reviewed GUI environment')
    if os.environ.get('ENABLE_CAMERAS') not in (None, '', '1'):
        parser.error('ENABLE_CAMERAS must not suppress this camera request')
    args.usd_path = args.usd_path.resolve(strict=True)
    args.output_dir = args.output_dir.resolve()
    if args.usd_path != APPROVED_USD.resolve(strict=True):
        parser.error('Only the accepted fixed_lift0_v1 USD is allowed')
    try:
        args.private_user_config = validate_private_path(args.kit_args, args.output_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    # Original formal controller options stay fixed; no camera options are
    # forwarded back into the original no-camera CLI.
    args.motion_profile = 'formal'
    args.physics_steps = 960
    args.pd_profile = 'baseline'
    args.visual_debug_pose = False
    args.view_preset = 'overall'
    return args


def phase_saved(recorder, event, **facts):
    recorder.phase = event
    recorder.result.setdefault('phase_order', []).append(event)
    recorder.save()
    for name in ('goal_id', 'capture_id'):
        if recorder.result.get('active_' + name) is not None:
            facts.setdefault(name, recorder.result['active_' + name])
    facts.setdefault('wall_time_s', time.time())
    recorder.emit(event, **facts)


def count_app_update(resources, _event):
    resources['app_update_counter']['count'] += 1


def native_validity(robot, sim):
    """Never touch native getters after a known invalid view or STOP."""
    view = sim.physics_sim_view
    root = getattr(robot, '_root_physx_view', None)
    facts = {'robot_initialized': bool(robot.is_initialized), 'simulation_view_present': view is not None,
             'articulation_view_present': root is not None, 'timeline_playing': bool(sim.is_playing())}
    if not all(facts.values()):
        raise DriveCheckError('NATIVE_VIEW_INVALID', 'Native view is unavailable', facts=facts)
    facts.update(simulation_is_valid=bool(view.is_valid), simulation_check=bool(view.check()), articulation_check=bool(root.check()))
    if not all(facts.values()):
        raise DriveCheckError('NATIVE_VIEW_INVALID', 'Native view validity check failed', facts=facts)
    return facts


def protected_inputs(usd):
    """Only the seven accepted derived files and the scanner visual source."""
    base = usd.parent.parent
    paths = [p for p in base.rglob('*') if p.is_file()]
    paths.append(usd.parents[3] / 'model/scanner_sys_scanner_visual.obj')
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class CompactPoseTrace:
    """Keep selected real control samples and aggregates, no full tensor dump."""
    def __init__(self):
        self.count = 0
        self.samples = []
        self.last = None

    def append(self, sample):
        self.count += 1
        keep = {k: sample.get(k) for k in ('step', 'physics_time_s', 'controlled_time_s', 'phase',
            'target_position_error_m', 'target_orientation_error_rad', 'stable_samples', 'stable_span_s', 'status', 'failure')}
        keep['max_abs_native_dq_rad_s'] = max(abs(float(v)) for v in sample.get('dq', [0]))
        self.last = keep
        if self.count == 1 or self.count % 120 == 0 or sample.get('status') in ('POSE_REACHED', 'FAIL'):
            self.samples.append(keep)

    def close(self):
        pass


def _make_camera_pre_physics(args, recorder, resources, camera_config, receive_context, *,
        camera_request_limit=1, camera_integration=False, prim_path='/World/CR12', nominal_root=None,
        fixture_path=None, resource_names=None, defer_visual_seal=False, shared_fixture=None):
    import omni.physx
    import _cr12_pose_control as pc
    from _cr12_camera_mount import create_camera_and_fixture
    from _cr12_camera_capture import OwnedCameraCapture
    from _cr12_visual_geometry import inspect_preinit_mapping, physical_snapshot, CollisionVisualOverride
    from _cr12_asset_math import ROOT_TRANSLATION

    derived = args.usd_path.parent.parent / 'cr12_fixed_lift0.urdf'
    model = pc.KinematicModel.from_derived_urdf(derived)
    if nominal_root is None:
        nominal_root = pc.pose_from_wxyz(ROOT_TRANSLATION, (1, 0, 0, 0))
    def pre_physics(*, stage, sim, robot, info):
        timing = {'robot_initialized': bool(robot.is_initialized), 'simulation_view_present': sim.physics_sim_view is not None,
            'robot_view_present': getattr(robot, '_root_physx_view', None) is not None,
            'physics_initialized': bool(sim.is_simulating()), 'physics_running': bool(omni.physx.get_physx_interface().is_running()),
            'timeline_playing': bool(sim.is_playing()), 'timeline_stopped': bool(sim.is_stopped()),
            'attached_stage_id_observed': int(omni.physx.get_physx_simulation_interface().get_attached_stage())}
        if any(timing[k] for k in ('robot_initialized', 'simulation_view_present', 'robot_view_present',
                'physics_initialized', 'physics_running', 'timeline_playing')) or not timing['timeline_stopped'] or timing['attached_stage_id_observed'] != 0:
            raise DriveCheckError('preinit_timing', 'Scene already initialized before new camera/visual creation', actual=timing)
        recorder.result['preinit_timing'] = timing
        recorder.result['camera_mount'] = create_camera_and_fixture(stage, info, camera_config, model, nominal_root,
            **({} if fixture_path is None else {'fixture_path': fixture_path}),
            **({} if shared_fixture is None else {'shared_fixture': shared_fixture}))
        mapping = inspect_preinit_mapping(stage, prim_path, derived)
        if not mapping['pass']:
            raise DriveCheckError('visual_mapping', 'Accepted visual/collision mapping differs', errors=mapping['errors'])
        override = CollisionVisualOverride(stage, mapping)
        resources['visual_override'] = override
        before = physical_snapshot(stage, prim_path)
        applied = override.apply(before_first_physics_initialization=True)
        if before != physical_snapshot(stage, prim_path):
            raise DriveCheckError('physical_invariance', 'Visual override changed composed physical properties')
        if not defer_visual_seal:
            override.seal_before_physics_initialization()
        recorder.result['visual_preinit'] = {'apply_count': 1, 'revoke_count': 0, 'reapply_count': 0,
            'composed_apply_equal': True, 'render_override': applied,
            'stage_checks': [] if defer_visual_seal else [override.verify_stable('preinit')], 'pass': False}
        phase_saved(recorder, 'overlay_applied_preinit')
        before_camera = _clock(sim)
        updates_before = resources.get('app_update_counter', {}).get('count')
        capture = OwnedCameraCapture.prepare(recorder.result['camera_mount']['camera_prim'],
            resolution=camera_config.resolution, context_provider=lambda: copy.deepcopy(receive_context),
            **(resource_names or {}),
            **({'max_requests': camera_request_limit, 'integration_mode': True} if camera_integration
               else ({} if camera_request_limit == 1 else {'max_requests': camera_request_limit})))
        resources['capture'] = capture
        capture.assert_off('pre_physics_prepared')
        recorder.result['camera_prepare_clock'] = {'before': list(before_camera), 'after': list(_clock(sim)),
            'app_update_events_before': updates_before, 'app_update_events_after': resources.get('app_update_counter', {}).get('count')}
        if before_camera != _clock(sim):
            raise DriveCheckError('physics_count', 'Camera prepare advanced physics')
        phase_saved(recorder, 'camera_prepared_off', product_path=capture.product_path)
    return pre_physics


def _initialize_camera_off(scene, recorder, resources):
    recorder.result['simulation']['camera_sensor_created'] = True
    capture = resources['capture']
    before_init = _clock(scene['sim'])
    updates_before = resources.get('app_update_counter', {}).get('count')
    capture.initialize_off(physics_sim_view=scene['sim'].physics_sim_view)
    capture.assert_off('initialized_before_motion')
    recorder.result['camera_initialize_clock'] = {'before': list(before_init), 'after': list(_clock(scene['sim'])),
        'app_update_events_before': updates_before, 'app_update_events_after': resources.get('app_update_counter', {}).get('count')}
    if _clock(scene['sim']) != before_init:
        raise DriveCheckError('physics_count', 'Camera initialize advanced physics')
    recorder.result['visual_preinit']['stage_checks'].append(resources['visual_override'].verify_stable('after_camera_initialize'))
    recorder.result['initialization']['app_update_events_before_motion'] = resources.get('app_update_counter', {}).get('count')


def prepare_scene(args, app, recorder, resources, expected, camera_config, receive_context, *, camera_request_limit=1, camera_integration=False):
    pre_physics = _make_camera_pre_physics(args, recorder, resources, camera_config, receive_context,
        camera_request_limit=camera_request_limit, camera_integration=camera_integration)
    def before_native_read(*, robot, sim):
        recorder.result['setup_native_validity'] = native_validity(robot, sim)
    scene = create_fixed_cr12_scene(args, app, recorder, resources, expected,
        pre_physics=pre_physics, before_native_read=before_native_read)
    initial = initialize_fixed_cr12_state(args, recorder, scene)
    _initialize_camera_off(scene, recorder, resources)
    return scene, initial
def preserve_artifact(args, recorder, snapshot, request, camera_config):
    """Saving is separate from acquisition and OFF; a failed save is not no-data."""
    from _cr12_camera_capture import save_rgba_png
    if snapshot is None or recorder.result.get('artifact_save_attempted'):
        return
    recorder.result['artifact_save_attempted'] = True
    recorder.result['capture_metadata'] = copy.deepcopy(snapshot['metadata'])
    try:
        artifact = save_rgba_png(args.output_dir / 'camera_rgba.png', snapshot['rgba'])
        artifact['path'] = str(args.output_dir / 'camera_rgba.png')
        recorder.result['camera_artifact'] = artifact
        request.record_artifact(artifact['path'])
    except BaseException as exc:
        request.record_artifact(str(args.output_dir / 'camera_rgba.png'), error=f'{type(exc).__name__}: {exc}')
        recorder.result['artifact_error'] = f'{type(exc).__name__}: {exc}'
    metadata = {**copy.deepcopy(snapshot['metadata']), 'virtual_camera': camera_config.record(),
        'optics_readback': recorder.result.get('camera_optics'),
        'product_path': recorder.result['capture_product_path'],
        'camera_prim': recorder.result['camera_mount']['camera_prim'],
        'receive_boundary_pose': recorder.result.get('data_receive_boundary'),
        'on_window_hold': recorder.result.get('on_window_hold'),
        'off_confirmation': recorder.result.get('off_confirmation'),
        'capture_on_boundary': request.capture_boundary, 'capture_off_boundary': request.close_boundary,
        'source_on_baseline': recorder.result.get('capture_source_on_baseline'),
        'data_received': recorder.result.get('data_received'),
        'artifact': recorder.result.get('camera_artifact'), 'artifact_error': recorder.result.get('artifact_error'),
        'save_wall_time_s': time.time(), 'time_semantics': 'source frame and receive/save times are distinct; no exact exposure pose claim'}
    metadata_path = args.output_dir / 'capture_metadata.json'
    recorder.result['capture_metadata_path'] = str(metadata_path)
    try:
        with metadata_path.open('x', encoding='utf-8') as stream:
            json.dump(metadata, stream, indent=2, allow_nan=False)
            stream.write('\n')
    except BaseException as exc:
        recorder.result['metadata_error'] = f'{type(exc).__name__}: {exc}'
        request.fail('ARTIFACT_METADATA', recorder.result['metadata_error'])


def refresh_initial_camera_publications(runs):
    """Publish every prepared zero state through exactly one shared forward."""
    import numpy as np
    from _cr12_camera_mount import actual_camera_pose, numpy_value, read_local_mount
    if not runs or len({id(run['scene']['sim']) for run in runs}) != 1:
        raise DriveCheckError('SETUP', 'Fabric publication requires one shared simulation')
    sim = runs[0]['scene']['sim']
    pending = []
    for run in runs:
        scene, initial, capture = run['scene'], run['initial'], run['capture']
        config, recorder, resources = run['camera_config'], run['recorder'], run['resources']
        capture.assert_off('initial_fabric_publication')
        native_validity(scene['robot'], sim)
        view = scene['robot'].root_physx_view
        getters = (view.get_dof_positions, view.get_dof_velocities, view.get_link_transforms)
        native_before = tuple(np.array(numpy_value(getter().clone()), copy=True) for getter in getters)
        before_clock = _clock(sim)
        before_updates = resources.get('app_update_counter', {}).get('count')
        record = {'before_clock': list(before_clock), 'app_updates_before': before_updates,
            'local_mount': read_local_mount(capture.camera, config),
            'before_camera': actual_camera_pose(capture.camera, initial['poses']['link_6'], config,
                clock=before_clock, phase='initial_before_fabric_publication', require_match=False)}
        recorder.result['initial_fabric_publication'] = record
        recorder.save()
        pending.append((run, getters, native_before, before_clock, before_updates, record))
    sim.forward()
    # Verify both native states before accepting either camera pose.
    for run, getters, native_before, before_clock, before_updates, record in pending:
        native_after = tuple(np.array(numpy_value(getter().clone()), copy=True) for getter in getters)
        record.update(after_clock=list(_clock(sim)),
            app_updates_after=run['resources'].get('app_update_counter', {}).get('count'),
            native_arrays_equal=[bool(np.array_equal(a, b)) for a, b in zip(native_before, native_after)],
            native_array_shapes=[list(a.shape) for a in native_before], forward_calls=1,
            shared_instance_count=len(runs))
        if (_clock(sim) != before_clock or record['app_updates_after'] != before_updates
                or not all(record['native_arrays_equal'])):
            raise DriveCheckError('physical_invariance', 'Initial Fabric publication changed native state or clocks', evidence=record)
    after_cameras = []
    for run, _getters, _before, _clock_before, _updates, record in pending:
        run['capture'].assert_off('after_initial_fabric_publication')
        after_camera = actual_camera_pose(run['capture'].camera, run['initial']['poses']['link_6'], run['camera_config'],
            clock=_clock(sim), phase='initial_after_fabric_publication')
        record.update(after_camera=after_camera, extra_physics_steps=0, extra_app_updates=0, pass_=True)
        run['recorder'].save()
        after_cameras.append(after_camera)
    return tuple(after_cameras)


def refresh_initial_camera_publication(scene, initial, capture, camera_config, recorder, resources):
    """Preserved single-instance wrapper around the common Fabric publication."""
    return refresh_initial_camera_publications((dict(scene=scene, initial=initial, capture=capture,
        camera_config=camera_config, recorder=recorder, resources=resources),))[0]
def initialize_capture_run(args, app, recorder, resources, expected, camera_config, *, camera_request_limit=1, camera_integration=False):
    """One scene/sensor/native lifecycle; shared by explicit one/two-view entries."""
    from _cr12_camera_mount import read_optics
    receive_context = {}
    scene, initial = prepare_scene(args, app, recorder, resources, expected, camera_config, receive_context,
        **({'camera_request_limit': camera_request_limit, 'camera_integration': True} if camera_integration
           else ({} if camera_request_limit == 1 else {'camera_request_limit': camera_request_limit})))
    sim, robot, capture = scene['sim'], scene['robot'], resources['capture']
    initial_parameters = copy.deepcopy(recorder.result['physx_readback'])
    recorder.result['camera_optics'] = read_optics(capture.camera, camera_config)
    recorder.result['capture_product_path'] = capture.product_path
    initial_camera = refresh_initial_camera_publication(scene, initial, capture, camera_config, recorder, resources)
    camera_checks = [initial_camera]
    mount_aggregate = {'count': 1, 'maximum_position_error_m': initial_camera['position_error_m'],
        'maximum_orientation_error_rad': initial_camera['orientation_error_rad'], 'selected_samples': camera_checks}
    recorder.result['camera_mount_checks'] = mount_aggregate
    trace = resources['trace'] = CompactPoseTrace()
    return dict(scene=scene, initial=initial, initial_parameters=initial_parameters,
        receive_context=receive_context, mount_aggregate=mount_aggregate, initial_camera=initial_camera, trace=trace)


def _validated_dual_specs(specs, *, profile_name='legacy'):
    """Independent expected layout, never inferred from measured robot poses."""
    import numpy as np
    shared = profile_name == 'shared_m2n1'
    if profile_name not in ('legacy', 'shared_m2n1'):
        raise DriveCheckError('instance_setup', 'Unknown dual instance profile')
    values = tuple(dict(item) for item in specs)
    if len(values) != 2:
        raise DriveCheckError('instance_setup', 'This entry requires exactly two fixed camera instances')
    robot_ids = [item.get('robot_id') for item in values]
    if any(type(robot_id) is not int for robot_id in robot_ids) or set(robot_ids) != {0, 1}:
        raise DriveCheckError('instance_setup', 'Dual specs must contain robot IDs 0 and 1 exactly once')
    result = []
    for item in values:
        robot_id = item['robot_id']
        expected = np.eye(4, dtype=np.float64)
        expected[:3, 3] = (0., 2.*robot_id, .053)
        if shared:
            from _cr12_shared_task_profile import root_pose
            expected = root_pose(robot_id)
        required = dict(robot_id=robot_id, prim_path=f'/World/CR12_{robot_id}',
            fixture_path='/World/SharedTaskCameraFixture' if shared else f'/World/CameraInterfaceFixture_R{robot_id}',
            product_name=f'CR12_R{robot_id}_Capture',
            camera_name=f'cr12_r{robot_id}_camera', observer_name=f'cr12.r{robot_id}.independent_completion')
        if any(item.get(key) != value for key, value in required.items()):
            raise DriveCheckError('instance_setup', 'Dual instance identity/fields differ from the approved layout', expected=required)
        pose = np.asarray(item.get('expected_root_pose'), dtype=np.float64)
        if pose.shape != (4, 4) or not np.array_equal(pose, expected):
            raise DriveCheckError('instance_setup', 'Expected root pose differs from the independent approved layout')
        item['expected_root_pose'] = pose.copy()
        result.append(item)
    return tuple(result)


class _InstanceRecorder(Recorder):
    """Small per-robot record, persisted in the one parent result."""
    def __init__(self, parent, robot_id):
        super().__init__()
        self.parent, self.robot_id = parent, robot_id
        self.result['robot_id'] = robot_id
        self.result['pd_selection'] = copy.deepcopy(parent.result['pd_selection'])

    def save(self):
        self.parent.save()

    def emit(self, event, **facts):
        facts.setdefault('robot_id', self.robot_id)
        self.parent.emit(event, **facts)


def initialize_dual_capture_runs(args, app, recorder, resources, expected, camera_config, specs, *, profile_name='legacy'):
    """Two explicit instances, one reset and one common zero-state publication."""
    from _cr12_runtime_support import (create_fixed_cr12_world, spawn_fixed_cr12_instance,
        prepare_fixed_cr12_contacts, reset_fixed_cr12_world, read_fixed_cr12_instance)
    from _cr12_camera_mount import read_optics
    from _cr12_camera_capture import verify_camera_isolation
    specs = _validated_dual_specs(specs, profile_name=profile_name)
    shared = profile_name == 'shared_m2n1'
    if 'runs' in resources:
        raise DriveCheckError('instance_setup', 'Dual preparation may only occur once')
    runs = resources['runs'] = []  # Present before construction, including partial-failure cleanup.
    recorder.result['instance_setup'] = []
    world = create_fixed_cr12_world(args, app, recorder, resources)
    shared_fixture = None
    if shared:
        from _cr12_shared_task_profile import scanner_target, initial_q
        from _cr12_camera_mount import create_shared_fixture
        shared_fixture = create_shared_fixture(world['stage'], camera_config, scanner_target())
        resources['shared_fixture'] = shared_fixture
    for spec in specs:
        instance_recorder = _InstanceRecorder(recorder, spec['robot_id'])
        recorder.result['instance_setup'].append(instance_recorder.result)
        instance_resources = {'app_update_counter': resources['app_update_counter']}
        instance_resources['external_forces_context'] = resources['external_forces_context']
        run = dict(robot_id=spec['robot_id'], recorder=instance_recorder, resources=instance_resources, receive_context={},
            camera_config=camera_config, spec=spec)
        runs.append(run)
        hook = _make_camera_pre_physics(args, instance_recorder, instance_resources, camera_config,
            run['receive_context'], camera_request_limit=2, camera_integration=True,
            prim_path=spec['prim_path'], nominal_root=spec['expected_root_pose'], fixture_path=spec['fixture_path'],
            resource_names={key: spec[key] for key in ('product_name', 'camera_name', 'observer_name')},
            defer_visual_seal=True, **({'shared_fixture': shared_fixture} if shared else {}))
        run['scene'] = spawn_fixed_cr12_instance(args, app, instance_recorder, instance_resources, expected,
            world=world, prim_path=spec['prim_path'], expected_root_pose=spec['expected_root_pose'], pre_physics=hook,
            **({'profile_name': profile_name, 'initial_q': initial_q(spec['robot_id'])} if shared else {}))
        run['capture'] = instance_resources['capture']
    # Every camera/fixture/product exists before the layers are sealed and the
    # shared physics scene is initialized. Contacts resolve both complete roots.
    for run in runs:
        prepare_fixed_cr12_contacts(run['scene'], run['resources'],
            other_instances=tuple(other['scene'] for other in runs if other is not run))
    for run in runs:
        overlay = run['resources']['visual_override']
        overlay.seal_before_physics_initialization()
        run['recorder'].result['visual_preinit']['stage_checks'].append(overlay.verify_stable('preinit'))
        run['capture'].assert_off('both_prepared_before_shared_reset')
    world['sim'].set_camera_view(eye=(3., -3., 3.), target=(0., 1., 1.3))
    reset_fixed_cr12_world(world, app, recorder, [run['scene'] for run in runs])
    for run in runs:
        scene, instance_recorder = run['scene'], run['recorder']
        def before_native_read(*, robot, sim, _recorder=instance_recorder):
            _recorder.result['setup_native_validity'] = native_validity(robot, sim)
        read_fixed_cr12_instance(scene, instance_recorder, expected, before_native_read=before_native_read)
        run['initial'] = initialize_fixed_cr12_state(args, instance_recorder, scene)
        run['initial_parameters'] = copy.deepcopy(instance_recorder.result['physx_readback'])
    # Both one-time initial state writes precede either camera initialization/publication.
    for run in runs:
        _initialize_camera_off(run['scene'], run['recorder'], run['resources'])
        run['recorder'].result['camera_optics'] = read_optics(run['capture'].camera, camera_config)
        run['recorder'].result['capture_product_path'] = run['capture'].product_path
    recorder.result['camera_isolation_initial'] = verify_camera_isolation([run['capture'] for run in runs])
    initial_cameras = refresh_initial_camera_publications(runs)
    for run, camera in zip(runs, initial_cameras):
        run['initial_camera'] = camera
        run['mount_aggregate'] = {'count': 1, 'maximum_position_error_m': camera['position_error_m'],
            'maximum_orientation_error_rad': camera['orientation_error_rad'], 'selected_samples': [camera]}
        run['recorder'].result['camera_mount_checks'] = run['mount_aggregate']
        run['trace'] = run['resources']['trace'] = CompactPoseTrace()
    recorder.result['common_camera_publication'] = {'forward_calls': 1, 'instance_count': 2,
        'physics_clock': list(_clock(world['sim'])), 'pass': True}
    recorder.save()
    return tuple(runs)


def receive_context_callback(initial, receive_context):
    import numpy as np
    def cache_before_render(tick):
        # No stepping/native getters; this state was read by the sole controller
        # immediately before the render that may deliver a Camera callback.
        receive_context.clear()
        receive_context.update(physics_step=tick['step']+initial['baseline'][0],
            controlled_step=tick['step'], simulation_time=tick['physics_time_s'],
            scanner_world_matrix=tick['scanner'].tolist(), link_6_world_matrix=tick['poses']['link_6'].tolist(),
            native_dq_rad_s=np.asarray(tick['dq']).tolist(),
            source='native post-step state immediately before the current normal render',
            camera_pose_note='camera Fabric pose is read after render; this callback context is the actual link/scanner sample')
        if 'goal_id' in tick:
            receive_context.update(goal_id=tick['goal_id'], local_step=tick['local_step'],
                local_time_s=tick['local_time_s'])

    return cache_before_render


def unique_product_events(capture):
    summary = capture.summary()
    return summary.get('unique_product_event_count', summary['product_event_count'])


def execute_capture_request(args, app, recorder, resources, camera_config, *, scene, initial,
        receive_context, mount_aggregate, initial_camera, trace, ticks, request,
        global_start_step=0, global_start_time=None, close_ticks=True):
    """Advance one request using the caller's sole controller and device.

    Request clocks are local; controller/render/native clocks remain global.
    Final device release belongs to the enclosing scene, not this request.
    """
    import numpy as np
    from _cr12_camera_mount import actual_camera_pose
    from _cr12_camera_capture import CameraCaptureError
    from _cr12_single_view_capture import CaptureRequestError, TERMINAL_STATES
    sim, robot, capture = scene['sim'], scene['robot'], resources['capture']
    camera_checks = mount_aggregate['selected_samples']
    if global_start_time is None:
        global_start_time = initial['baseline'][1]
    resources['request'] = request
    request.start_motion(capture.assert_off('moving_entry'), time.monotonic())
    start_event_count = unique_product_events(capture)
    moving_off_samples = 0
    moving_product_events = 0
    snapshot = None
    acquisition_error = physical_error = None
    close_evidence = None
    last_camera = initial_camera
    latest_tick = None
    recorder.result['on_window_hold'] = {'samples': 0, 'max_position_error_m': 0.,
        'max_orientation_error_rad': 0., 'max_abs_native_dq_rad_s': 0.,
        'semantics': 'post-step holding bounds over the ON window, not exact exposure pose'}

    def start_close():
        if recorder.result.get('capture_off_request') is not None:
            return
        boundary = request.request_close(time.monotonic())
        actual_boundary = {**boundary, 'native_physics_clock': list(_clock(sim)),
            'global_physics_step': global_start_step + boundary['physics_step']}
        capture.request_off(actual_boundary)
        recorder.result['capture_off_request'] = copy.deepcopy(actual_boundary)
        phase_saved(recorder, 'capture_off_requested', **actual_boundary)

    try:
        while request.state not in TERMINAL_STATES:
            try:
                request.check_before_tick(time.monotonic())
            except CaptureRequestError as exc:
                acquisition_error = acquisition_error or exc
                if request.state == 'STOP_UNCONFIRMED':
                    break
                start_close()
                continue
            state_before_tick = request.state
            if state_before_tick == 'MOVING_OFF':
                capture.assert_off('moving_before_tick')
            native_validity(robot, sim)
            # Exactly one existing actuator/physics/guard tick; no independent
            # camera loop, no orchestrator.step, no teleport or timeline switch.
            latest_tick = next(ticks)
            resources['latest_capture_tick'] = latest_tick
            tick = latest_tick if global_start_step == 0 else {**latest_tick,
                'step': latest_tick['step'] - global_start_step,
                'controlled_time_s': latest_tick['physics_time_s'] - global_start_time}
            if tick.get('local_step', tick['step']) != tick['step']:
                raise DriveCheckError('physics_count', 'Controller and request local clocks differ')
            try:
                request.observe_tick(tick, capture.read_updates_enabled(), time.monotonic())
            except CaptureRequestError as exc:
                if exc.category != 'CAPTURE_TIMEOUT':
                    raise
                acquisition_error = acquisition_error or exc
                start_close()
                continue
            if state_before_tick == 'MOVING_OFF':
                moving_off_samples += 1
                moving_product_events = unique_product_events(capture) - start_event_count
                capture.assert_off('moving_after_tick')
                if moving_product_events != 0:
                    raise CameraCaptureError('camera_moving_output', 'Dedicated camera produced an event while MOVING_OFF')
            if tick['rendered']:
                last_camera = actual_camera_pose(capture.camera, tick['poses']['link_6'], camera_config,
                    clock=_clock(sim), phase=request.state)
                mount_aggregate['count'] += 1
                for key in ('position', 'orientation'):
                    unit = 'm' if key == 'position' else 'rad'
                    metric = f'{key}_error_{unit}'
                    mount_aggregate[f'maximum_{metric}'] = max(mount_aggregate[f'maximum_{metric}'], last_camera[metric])
                if tick['step'] % 120 == 0 or request.state == 'ARRIVED_HOLD_OFF':
                    camera_checks.append(copy.deepcopy(last_camera))
            if state_before_tick in ('CAPTURE_STARTING', 'WAITING_DATA'):
                hold = recorder.result['on_window_hold']
                hold['samples'] += 1
                hold['max_position_error_m'] = max(hold['max_position_error_m'], tick['sample']['target_position_error_m'])
                hold['max_orientation_error_rad'] = max(hold['max_orientation_error_rad'], tick['sample']['target_orientation_error_rad'])
                hold['max_abs_native_dq_rad_s'] = max(hold['max_abs_native_dq_rad_s'], float(np.max(np.abs(tick['dq']))))

            if request.state == 'ARRIVED_HOLD_OFF':
                recorder.result['arrival'] = {**copy.deepcopy(request.arrival),
                    'sample': {k: tick['sample'][k] for k in ('target_position_error_m', 'target_orientation_error_rad', 'stable_samples', 'stable_span_s')},
                    'scanner_world_matrix': tick['scanner'].tolist(), 'camera_readback': copy.deepcopy(last_camera)}
                phase_saved(recorder, 'pose_reached', global_physics_step=global_start_step+request.step, **request.arrival)
                starting = request.capture_starting(time.monotonic())
                boundary = {**starting['boundary'], 'native_physics_clock': list(_clock(sim)),
                    'global_physics_step': global_start_step + request.step,
                    'scanner_world_matrix': tick['scanner'].tolist(), 'camera_readback': copy.deepcopy(last_camera)}
                try:
                    on = capture.begin_capture(starting['ids'], boundary)
                    request.capture_started({'updates_enabled': on['actual'], 'render_product_path': capture.product_path})
                    recorder.result['capture_on_request'] = boundary
                    recorder.result['capture_source_on_baseline'] = capture.summary()['request']
                    phase_saved(recorder, 'capture_on', product_path=capture.product_path, **boundary)
                except (CameraCaptureError, CaptureRequestError) as exc:
                    acquisition_error = acquisition_error or exc
                    request.fail(getattr(exc, 'category', 'CAPTURE_START'), str(exc), time.monotonic())
                    start_close()
            elif request.state == 'WAITING_DATA':
                try:
                    candidate = capture.poll_snapshot()
                    if candidate is not None:
                        request.accept_frame(candidate['metadata'], now=time.monotonic())
                        snapshot = candidate
                        recorder.result['data_receive_boundary'] = {'physics_clock': list(_clock(sim)),
                            'scanner_world_matrix': tick['scanner'].tolist(), 'camera_readback': copy.deepcopy(last_camera),
                            'semantics': 'post-render read in receive tick; not exact exposure pose'}
                        recorder.result['data_received'] = {'wall_time_s': time.time(), 'physics_clock': list(_clock(sim)),
                            'rendering_frame': snapshot['metadata']['rendering_frame'], 'count': 1}
                        phase_saved(recorder, 'data_received', **recorder.result['data_received'])
                        start_close()
                except (CameraCaptureError, CaptureRequestError) as exc:
                    acquisition_error = acquisition_error or exc
                    request.fail(getattr(exc, 'category', 'CAPTURE'), str(exc), time.monotonic())
                    start_close()
            elif request.state in ('CAPTURE_CLOSING', 'CLOSING_AFTER_FAILURE'):
                # The render in which OFF was requested does not count toward
                # drain observation; this branch begins on the following tick.
                close_evidence = capture.observe_close(render_opportunity=tick['rendered'])
                recorder.result['off_confirmation'] = {
                    **close_evidence, 'product_path': capture.product_path,
                    'render_opportunities': close_evidence['opportunity_count'],
                    'consecutive_quiet_render_opportunities': close_evidence['quiet_opportunities'],
                    'independent_product_events': close_evidence['independent_observer_active']}
                if close_evidence['confirmed']:
                    phase_saved(recorder, 'capture_off_confirmed', **recorder.result['off_confirmation'])
                    # OFF and acquisition facts survive any PNG/metadata I/O error.
                    save_clock, save_wall = _clock(sim), time.monotonic()
                    preserve_artifact(args, recorder, snapshot, request, camera_config)
                    recorder.result['artifact_save_observation'] = {
                        'before_clock': list(save_clock), 'after_clock': list(_clock(sim)),
                        'wall_elapsed_s': time.monotonic()-save_wall,
                        'product_updates_enabled': capture.read_updates_enabled()}
                    if _clock(sim) != save_clock or capture.read_updates_enabled():
                        raise DriveCheckError('physics_count', 'Saving advanced physics or enabled the camera')
                request.observe_close(close_evidence, time.monotonic())
            if tick['step'] % 120 == 0:
                recorder.result['single_view_request'] = request.summary()
                recorder.result['camera_backend'] = capture.summary()
                recorder.save()
    except BaseException as exc:
        physical_error = exc
        request.fail(getattr(exc, 'category', 'runtime_exception'), str(exc), time.monotonic())
        # A failed physical/native guard must not be followed by extra stepping.
        # Disable this product, preserve data, and leave OFF unconfirmed unless
        # the independent drain evidence had already completed.
        try:
            start_close()
        except BaseException as closing_error:
            recorder.secondary(closing_error, 'failure_off_request')
        if not request.off_confirmed:
            request.stop_unconfirmed(getattr(exc, 'category', 'runtime_exception'), str(exc), time.monotonic())
    finally:
        if close_ticks:
            ticks.close()
        if snapshot is not None and not recorder.result.get('artifact_save_attempted'):
            try:
                preserve_artifact(args, recorder, snapshot, request, camera_config)
            except BaseException as artifact_error:
                request.fail('ARTIFACT', str(artifact_error))
                recorder.secondary(artifact_error, 'preserve_acquired_frame')
        summary = request.summary()
        recorder.result['single_view_request'] = summary
        recorder.result['camera_backend'] = capture.summary()
        actual_steps = int(recorder.result['completed_physics_steps']) - global_start_step
        actual_off = recorder.result.get('capture_off_request')
        close_step = None if actual_off is None else int(actual_off['native_physics_clock'][0])-initial['baseline'][0]-global_start_step
        capture_step = None if request.capture_boundary is None else request.capture_boundary['physics_step']
        pose_steps = actual_steps if capture_step is None else capture_step
        capture_steps = 0 if capture_step is None else (actual_steps if close_step is None else close_step)-capture_step
        close_steps = 0 if close_step is None else actual_steps-close_step
        # A guard can reject a real post-step before the generator yields it.
        # Preserve that physics tick, even though the FSM never accepted it.
        if capture_step is None:
            pose_steps = actual_steps-close_steps
        recorder.result['stage_counts'] = {'pose_steps': pose_steps, 'capture_steps': capture_steps,
            'close_steps': close_steps, 'total_controlled_steps': actual_steps,
            'fsm_observed_steps': request.step, 'unaccepted_poststep_count': actual_steps-request.step}
        close_start = request.close_boundary
        now = time.monotonic()
        recorder.result['capture_wall_time_s'] = 0. if request.capture_boundary is None else (close_start or {'wall_time': now})['wall_time'] - request.capture_boundary['wall_time']
        recorder.result['close_wall_time_s'] = 0. if close_start is None else now-close_start['wall_time']
        recorder.result['moving_camera_off'] = {'checked_poststep_samples': moving_off_samples,
            'product_event_count_during_motion': moving_product_events, 'pass': moving_off_samples == pose_steps and moving_product_events == 0}
        recorder.result['pose_phase_trace'] = {'count': trace.count, 'selected_samples': trace.samples, 'last': trace.last}
        recorder.result['app_update_observation'] = {'before_motion': recorder.result.get('initialization', {}).get('app_update_events_before_motion'),
            'before_resource_release': resources.get('app_update_counter', {}).get('count'),
            'controlled_render_calls': recorder.result.get('pose_summary', {}).get('render_calls')}
        recorder.result['capture_summary'] = {**request.ids, 'product_path': capture.product_path,
            'state': request.state, 'acquired': request.acquired, 'saved': request.artifact_saved,
            'confirmed_off': request.off_confirmed, 'fresh_frame_confirmed': request.acquired and request.frame.get('fresh') is True,
            'moving_off_verified': recorder.result['moving_camera_off']['pass'],
            'product_identity_confirmed': request.acquired and request.frame.get('render_product_path') == capture.product_path,
            'artifact': recorder.result.get('camera_artifact'), 'metadata_path': recorder.result.get('capture_metadata_path')}
        recorder.save()

    if physical_error is not None:
        raise physical_error
    if request.state != 'SUCCEEDED_OFF' or acquisition_error is not None:
        raise acquisition_error or DriveCheckError('capture_request', 'Single view did not complete', request=summary)
    return {'request': request, 'snapshot': snapshot, 'last_tick': latest_tick, 'last_camera': last_camera}


def verify_final_capture_scene(scene, expected, recorder, resources, initial_parameters, request, *, total_steps=None):
    from _cr12_external_forces import read_scene_external_forces
    sim, robot, capture = scene['sim'], scene['robot'], resources['capture']
    # Camera is OFF, but the same valid physics scene remains active until all
    # required final native reads finish. No getter is deferred to finally.
    recorder.result['final_native_validity'] = native_validity(robot, sim)
    before_native = _clock(sim)
    _, _, final_parameters = _read_physics(robot, expected['bodies'], scene['configuration'], recorder, scene['selected_pd'])
    if initial_parameters != final_parameters or _clock(sim) != before_native:
        raise DriveCheckError('physical_invariance', 'Native parameters or physics clock changed during final read')
    recorder.result['native_parameters_unchanged'] = True
    override = resources['visual_override']
    recorder.result['visual_preinit']['stage_checks'].append(override.verify_stable('after_capture_off_before_release'))
    recorder.result['visual_preinit']['pass'] = True
    read_scene_external_forces(scene['stage'], scene['setup'], 'before_exit',
        scene['physx_schema'], scene['usd_physics'], scene['default_time'])
    stats = recorder.result['pose_summary']
    stats.update(outcome='POSE_REACHED', stable_count=request.arrival['stable_samples'],
        stable_span_s=request.arrival['stable_span_s'], capture_hold_pass=True)
    recorder.result['physical_summary'] = {'all_guards_passed': all(n == (request.step if total_steps is None else total_steps) for n in stats['guard_pass_counts'].values()),
        'guard_pass_counts': dict(stats['guard_pass_counts']), 'native_lifecycle_pass': True,
        'visual_preinit_pass': True, 'mount_pose_checks_pass': True}
    recorder.save()


def finalize_capture_scene(scene, expected, recorder, resources, initial_parameters, request, *, total_steps=None):
    """Legacy wrapper; dual callers verify both instances before either release."""
    verify_final_capture_scene(scene, expected, recorder, resources, initial_parameters, request, total_steps=total_steps)
    capture = resources['capture']
    recorder.result['camera_release'] = capture.release()
    recorder.result['camera_resources_released'] = True
    recorder.result['resource_release_before_stop'] = True
    recorder.save()


def run_capture(args, app, recorder, resources, expected, camera_config):
    """The original default still submits exactly one formal goal and exits."""
    from _cr12_single_view_capture import SingleViewRequest
    from run_cr12_pose_target import _pose_ticks
    run = initialize_capture_run(args, app, recorder, resources, expected, camera_config)
    request = SingleViewRequest('formal_goal_1', args.output_dir.name, resources['capture'].product_path, 'capture_1')
    ticks = _pose_ticks(args, app, recorder, resources, expected, scene=run['scene'], initial=run['initial'],
        continue_after_arrival=True, before_render=receive_context_callback(run['initial'], run['receive_context']))
    execute_capture_request(args, app, recorder, resources, camera_config, ticks=ticks, request=request,
        **{k: v for k, v in run.items() if k != 'initial_parameters'})
    finalize_capture_scene(run['scene'], expected, recorder, resources, run['initial_parameters'], request)


def cleanup_failure(recorder, exc, phase, primary):
    if primary is None:
        recorder.fail(exc, phase)
        return exc
    recorder.secondary(exc, phase)
    return primary


def release_capture_with_record(capture, recorder):
    """Separate cached pre-release facts from the result of owned cleanup."""
    before = copy.deepcopy(capture.summary())
    recorder.result['camera_backend'] = before  # compatibility: this is explicitly pre-release
    recorder.result['camera_backend_snapshot_at'] = 'pre_release'
    recorder.result['camera_backend_pre_release'] = copy.deepcopy(before)
    recorder.result['camera_backend_post_release'] = 'NOT_READ'
    recorder.result['camera_backend_post_release_snapshot_at'] = 'NOT_READ'
    release = capture.release()
    recorder.result['camera_release'] = copy.deepcopy(release)
    recorder.result['camera_backend_post_release'] = copy.deepcopy(capture.summary())
    recorder.result['camera_backend_post_release_snapshot_at'] = 'post_release'
    return release


def main(*, capture_runner=None, success_label='SINGLE_VIEW_CAPTURE_INTEGRATION_PASS', entry_source=None, configure_parser=None, pre_app_validator=None, completion_label=None):
    recorder, resources, app, failure = Recorder(), {}, None, None
    recorder.emit('process_started', python=sys.executable, cwd=os.getcwd(), argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode)
    try:
        from isaaclab.app import AppLauncher
        args = parse_args(AppLauncher, **({} if configure_parser is None else {'configure_parser': configure_parser}))
        if pre_app_validator is not None:
            pre_app_validator(args)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        result_path = args.output_dir / 'result.json'
        if result_path.exists():
            raise FileExistsError(result_path)
        recorder.path = result_path
        from _cr12_camera_mount import resolve_virtual_mount
        from _cr12_collision_refinement import load_accepted_inputs
        from _cr12_hold_diagnostics import select_pd_profile
        from _windows_runtime_startup import prepare_windows_runtime_args
        from view_scan_assignment import _prepare_cuda_before_app
        derived = args.usd_path.parent.parent / 'cr12_fixed_lift0.urdf'
        expected = load_accepted_inputs(derived)
        config = resolve_virtual_mount(derived)
        protected = protected_inputs(args.usd_path)
        recorder.result.update(usd_path=str(args.usd_path), python=sys.executable, entry_source=entry_source or __file__,
            original_argv=list(sys.argv), utf8_mode=sys.flags.utf8_mode, pd_selection=select_pd_profile('baseline'),
            private_user_config=args.private_user_config, manual_check=args.manual_check,
            camera_config_frozen_before_app=config.record(),
            external_forces_request={'mode': 'on', 'source': args.external_forces_source})
        recorder.phase = 'startup_preparation'
        startup = prepare_windows_runtime_args(args, list(sys.argv))
        if startup['requested_backend'] != 'D3D12':
            raise DriveCheckError('SETUP', 'D3D12 required')
        recorder.result['startup'] = startup
        recorder.emit('startup_prepared', **startup)
        recorder.emit('pre_app_cuda_begin')
        recorder.result['pre_app_cuda'] = _prepare_cuda_before_app(args.device)
        recorder.emit('pre_app_cuda_ready', **recorder.result['pre_app_cuda'])
        if args.gui_startup_diagnostics:
            from _cr12_gui_startup_diagnostics import record_gui_startup_diagnostics
            record_gui_startup_diagnostics(args, recorder, 'before_app')
        phase_saved(recorder, 'app_constructor_begin')
        launcher = AppLauncher(args)
        app = launcher.app
        if args.gui_startup_diagnostics:
            record_gui_startup_diagnostics(args, recorder, 'after_app', launcher=launcher)
        import carb
        settings = carb.settings.get_settings()
        effective = {'experience': launcher._sim_experience_file, 'kit_log_file': settings.get('/log/file'),
            'vulkan_setting': settings.get('/app/vulkan'), 'headless': launcher._headless,
            'enable_cameras': launcher._enable_cameras, 'livestream': launcher._livestream,
            'xr': launcher._xr, 'device': args.device, 'user_config_path': settings.get('/app/userConfigPath')}
        recorder.result['app'] = effective
        recorder.emit('app_ready', **effective)
        if (launcher._headless or not launcher._enable_cameras or launcher._livestream or launcher._xr
                or settings.get('/app/vulkan') is not False
                or Path(effective['user_config_path']).resolve() != Path(args.private_user_config)):
            raise DriveCheckError('SETUP', 'Effective camera GUI/private mode differs')
        import omni.kit.app
        resources['app_update_counter'] = {'count': 0}
        resources['app_update_subscription'] = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            lambda event: count_app_update(resources, event), name='cr12.capture.initialization_update_count')
        (run_capture if capture_runner is None else capture_runner)(args, app, recorder, resources, expected, config)
        if protected_inputs(args.usd_path) != protected:
            raise DriveCheckError('asset_protection', 'Accepted asset/source content changed')
        recorder.result['asset_protection'] = {'pass': True, 'count': len(protected), 'files_sha256': protected}
        recorder.result.update(status='WORK_COMPLETED_PENDING_PROCESS_EXIT', work_completed=True,
            classification=success_label if completion_label is None else completion_label(recorder.result), diagnostics_complete=True)
        phase_saved(recorder, 'work_completed', completed_physics_steps=recorder.result['completed_physics_steps'])
    except BaseException as exc:
        failure = exc
        recorder.result['classification'] = ('NOT_HIT'
            if recorder.result.get('case_classification') == 'NOT_HIT'
            else success_label.removesuffix('_PASS') + '_FAIL')
        recorder.fail(exc)
    finally:
        # No robot native getter here. All required native reads precede release
        # and STOP; failure cleanup never tries to resurrect an invalid view.
        for run in resources.get('runs', ()):
            own_resources, own_recorder = run['resources'], run['recorder']
            owned = own_resources.get('capture')
            if owned is not None and not own_recorder.result.get('camera_resources_released'):
                try:
                    owned.request_off()
                except BaseException as exc:
                    failure = cleanup_failure(recorder, exc, 'camera_off_cleanup_r'+str(run['robot_id']), failure)
                try:
                    release_capture_with_record(owned, own_recorder)
                    own_recorder.result['camera_resources_released'] = True
                    own_recorder.result['resource_release_before_stop'] = True
                except BaseException as exc:
                    failure = cleanup_failure(recorder, exc, 'camera_resource_cleanup_r'+str(run['robot_id']), failure)
            if 'contacts' in own_resources:
                try:
                    own_recorder.result['contact_summary'] = _contact_summary(own_resources['contacts'])
                except BaseException as exc:
                    failure = cleanup_failure(recorder, exc, 'contact_summary_r'+str(run['robot_id']), failure)
        capture = resources.get('capture')
        if capture is not None and not recorder.result.get('camera_resources_released'):
            try:
                capture.request_off()
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'camera_off_cleanup', failure)
            try:
                release_capture_with_record(capture, recorder)
                recorder.result['camera_resources_released'] = True
                recorder.result['resource_release_before_stop'] = True
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'camera_resource_cleanup', failure)
        if 'contacts' in resources:
            try:
                recorder.result['contact_summary'] = _contact_summary(resources['contacts'])
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'contact_summary', failure)
        resources['app_update_subscription'] = None
        if resources.get('sim') is not None:
            try:
                recorder.phase = 'simulation_stop'
                resources['sim']._disable_app_control_on_stop_handle = True
                resources['sim'].stop()
                recorder.result['simulation_stop_returned'] = True
                phase_saved(recorder, 'simulation_stop_returned')
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'simulation_stop', failure)
        if app is not None:
            recorder.phase = 'app_close'
            recorder.result['app_close_requested'] = True
            try:
                phase_saved(recorder, 'app_close_begin', work_completed=recorder.result['work_completed'],
                    failures=len(recorder.result['failures'])+len(recorder.result['secondary_failures']))
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'pre_close_recording', failure)
            try:
                app.close()
                recorder.emit('app_close_returned')
            except BaseException as exc:
                failure = cleanup_failure(recorder, exc, 'app_close', failure)
        else:
            recorder.save()
    if failure is not None:
        raise failure
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
