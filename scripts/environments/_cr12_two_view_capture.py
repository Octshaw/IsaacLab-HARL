"""A fixed two-request sequence around the existing one-request execution loop.

No physics clock lives here. A single retained pose generator owns every tick;
each fresh SingleViewRequest sees a local counter derived from that global tick.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import time

from _cr12_runtime_support import DriveCheckError

MAX_STEPS = 3600
VIEW_FIELDS = ('single_view_request', 'capture_summary', 'arrival', 'capture_on_request',
    'capture_source_on_baseline', 'data_receive_boundary', 'data_received', 'capture_off_request',
    'off_confirmation', 'artifact_save_attempted', 'capture_metadata', 'camera_artifact',
    'capture_metadata_path', 'artifact_error', 'metadata_error', 'artifact_save_observation',
    'stage_counts', 'capture_wall_time_s', 'close_wall_time_s', 'moving_camera_off', 'on_window_hold')


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def require_completed_view(view):
    """Save is a sequence delivery gate; it cannot change the acquired fact."""
    request, capture = view.get('single_view_request', {}), view.get('capture_summary', {})
    if (view.get('status') != 'SUCCEEDED_OFF' or request.get('state') != 'SUCCEEDED_OFF'
            or any(request.get(k) is not True for k in ('acquired', 'artifact_saved', 'off_confirmed'))
            or any(capture.get(k) is not True for k in ('fresh_frame_confirmed', 'product_identity_confirmed', 'moving_off_verified'))
            or request.get('failure') is not None or view.get('artifact_error') or view.get('metadata_error')
            or not view.get('capture_metadata_path') or not view.get('off_confirmation', {}).get('confirmed')):
        raise DriveCheckError('sequence_handoff', 'Next goal requires arrival, fresh frozen data, OFF and both saved files')


class TwoViewSequence:
    """Exactly two records; terminal results are copied, never reset for reuse."""
    def __init__(self):
        self.views = [{'goal_id': f'goal_{i}', 'capture_id': f'capture_{i}', 'status': 'NOT_STARTED'} for i in (1, 2)]
        self.active = None
        self.failure = None

    def start(self, index):
        if (self.failure is not None or self.active is not None or index not in (0, 1)
                or self.views[index]['status'] != 'NOT_STARTED'):
            raise DriveCheckError('sequence_state', 'Sequence cannot start this request')
        if index == 1:
            require_completed_view(self.views[0])
        self.active = index
        self.views[index]['status'] = 'RUNNING'

    def finish(self, index, result):
        if self.active != index:
            raise DriveCheckError('sequence_state', 'Only the current request may finish')
        self.views[index] = copy.deepcopy(result)
        self.active = None
        if result.get('status') != 'SUCCEEDED_OFF':
            self.fail('sequence_request', f'goal_{index+1} did not complete')

    def fail(self, category, message):
        if self.failure is None:
            self.failure = {'category': str(category), 'message': str(message)}
        if self.active is not None and self.views[self.active]['status'] == 'RUNNING':
            self.views[self.active].update(status='FAILED', failure=copy.deepcopy(self.failure),
                result_not_finalized=True)
            self.active = None
        for view in self.views:
            if view['status'] == 'NOT_STARTED':
                view['blocked_by_previous_failure'] = True

    def records(self):
        return copy.deepcopy(self.views)


def immutable_evidence(request, snapshot, view):
    return {'rgba_sha256': hashlib.sha256(snapshot['rgba'].tobytes(order='C')).hexdigest(),
        'snapshot_metadata_sha256': object_digest(snapshot['metadata']),
        'request_sha256': object_digest(request.summary()),
        'result_sha256': object_digest(view),
        'png_sha256': hashlib.sha256(Path(view['camera_artifact']['path']).read_bytes()).hexdigest(),
        'metadata_sha256': hashlib.sha256(Path(view['capture_metadata_path']).read_bytes()).hexdigest()}


def verify_immutable(before, after):
    result = {'pass': before == after}
    for key in before:
        result[key+'_before'], result[key+'_after'] = before[key], after.get(key)
    if not result['pass']:
        raise DriveCheckError('sequence_immutable', 'The first frozen result or saved artifact changed', evidence=result)
    return result


def read_handoff_native(scene):
    """Only while the original native lifecycle is valid, with no physics step."""
    import _cr12_pose_control as pc
    from _cr12_runtime_support import _body_poses, _clock
    from run_cr12_pose_target import _native_state
    from run_cr12_single_view_capture import native_validity
    sim, robot = scene['sim'], scene['robot']
    native_validity(robot, sim)
    before = _clock(sim)
    q, dq = _native_state(robot, scene['joint_ids'])
    poses = _body_poses(robot, scene['body_ids'])
    if _clock(sim) != before:
        raise DriveCheckError('physics_count', 'Handoff native read advanced physics')
    return {'native_clock': list(before), 'q': q[0].cpu().numpy().tolist(),
        'dq': dq[0].cpu().numpy().tolist(), 'scanner': pc.scanner_from_ee(poses['link_6']).tolist()}


def scene_identity(scene):
    return {'scene_id': id(scene), 'sim_id': id(scene['sim']), 'robot_id': id(scene['robot']),
        'simulation_view_id': id(scene['sim'].physics_sim_view),
        'articulation_view_id': id(scene['robot'].root_physx_view)}


def handoff_goal_2(context, completed_view, request, last_tick, scene, capture, recorder):
    """A zero-step OFF handoff after saved goal_1, before the next command."""
    import numpy as np
    from run_cr12_single_view_capture import unique_product_events
    require_completed_view(completed_view)
    before = read_handoff_native(scene)
    for key in ('q', 'dq', 'scanner'):
        if not np.array_equal(before[key], last_tick[key]):
            raise DriveCheckError('sequence_handoff', 'Handoff snapshot is not the latest actual state', field=key)
    capture.assert_off('between_goals_before_submission')
    identity = capture.device_identity()
    events_before = unique_product_events(capture)
    wall = time.monotonic()
    queued = context.queue_goal_2(last_tick, completed_request=request.summary())
    after = read_handoff_native(scene)
    capture.assert_off('between_goals_after_submission')
    if before != after or identity != capture.device_identity() or events_before != unique_product_events(capture):
        raise DriveCheckError('sequence_handoff', 'Goal handoff changed native state, camera or completed output')
    evidence = {'pass': False, 'first_off_and_saved': True, 'no_physics_advance': True,
        'native_state_unchanged': True, 'command_state_continuous': False,
        'next_reference_from_latest_actual': False, 'product_off': True,
        'global_physics_step': last_tick['step'], 'render_count': last_tick['render_count'],
        'before': before, 'after': after, 'q_cmd': np.asarray(last_tick['q_cmd']).tolist(),
        'dq_cmd': np.asarray(last_tick['dq_cmd']).tolist(), 'next_goal_id': 'goal_2',
        'trajectory_start': last_tick['scanner'].tolist(), 'device_identity': identity,
        'previous_request': request.summary(), 'previous_off': copy.deepcopy(completed_view['off_confirmation']),
        'controller_queue': queued, 'wall_elapsed_s': time.monotonic()-wall,
        'product_new_completions': unique_product_events(capture)-events_before}
    recorder.result['handoff'] = evidence
    recorder.save()
    return evidence


def freeze_current_view(recorder, request, start_step, end_step, before_counts, trace_start):
    result = {key: copy.deepcopy(recorder.result[key]) for key in VIEW_FIELDS if key in recorder.result}
    stats = copy.deepcopy(recorder.result.get('pose_summary', {}))
    stats['guard_pass_counts'] = {k: n-before_counts.get('guard_pass_counts', {}).get(k, 0)
        for k, n in stats.get('guard_pass_counts', {}).items()}
    for key in ('render_calls', 'submitted_target_checks', 'sanity_checks'):
        stats[key] = stats.get(key, 0)-before_counts.get(key, 0)
    stats.update(outcome='POSE_REACHED' if request.arrival else 'NOT_REACHED',
        stable_count=0 if request.arrival is None else request.arrival['stable_samples'],
        stable_span_s=0 if request.arrival is None else request.arrival['stable_span_s'],
        capture_hold_pass=request.state == 'SUCCEEDED_OFF',
        metric_scope='counts are request-local deltas; motion extrema remain cumulative from App start')
    result.update(status=request.state, **request.ids, pose_summary=stats,
        global_start_step=start_step, global_end_step=end_step,
        pose_phase_trace={'count': end_step-start_step,
            'selected_samples': copy.deepcopy(trace_start.samples), 'last': copy.deepcopy(trace_start.last)})
    return result


def run_two_capture(args, app, recorder, resources, expected, camera_config):
    import numpy as np
    import _cr12_pose_control as pc
    from _cr12_pose_continuation import TwoViewPoseContinuation
    from _cr12_single_view_capture import SingleViewRequest
    from _cr12_runtime_support import _clock
    from run_cr12_pose_target import _pose_ticks
    import run_cr12_single_view_capture as shared

    run = shared.initialize_capture_run(args, app, recorder, resources, expected, camera_config, camera_request_limit=2)
    scene, initial, capture = run['scene'], run['initial'], resources['capture']
    context = TwoViewPoseContinuation(pc.scanner_from_ee(initial['poses']['link_6']))
    sequence = TwoViewSequence()
    recorder.result['two_view_profile'] = context.record()
    recorder.result['views'] = sequence.records()
    identities = [capture.device_identity()]
    recorder.result['resource_identity_samples'] = identities
    scene_identities = [scene_identity(scene)]
    recorder.result['scene_identity_samples'] = scene_identities
    recorder.result['sequence_summary'] = {'complete': False, 'completed_views': 0,
        'targets_frozen_before_motion': True, 'distinct_targets': context.record()['target_distance_m'] > 0,
        'first_result_unchanged': False}
    recorder.save()
    ticks = _pose_ticks(args, app, recorder, resources, expected, scene=scene, initial=initial,
        continue_after_arrival=True, before_render=shared.receive_context_callback(initial, run['receive_context']),
        continuation=context)
    first_request = first_snapshot = first_before = last_request = None
    start_step, start_time = 0, initial['baseline'][1]
    last_camera = run['initial_camera']
    try:
        for index in range(2):
            sequence.start(index)
            recorder.result['views'] = sequence.records()
            for key in VIEW_FIELDS:
                recorder.result.pop(key, None)
            recorder.result.update(active_goal_id=f'goal_{index+1}', active_capture_id=f'capture_{index+1}')
            view_args = copy.copy(args)
            view_args.output_dir = args.output_dir / f'view_{index+1:02d}'
            view_args.output_dir.mkdir(exist_ok=False)
            request = SingleViewRequest(f'goal_{index+1}', args.output_dir.name, capture.product_path, f'capture_{index+1}')
            last_request = request
            before_counts = copy.deepcopy(recorder.result.get('pose_summary', {}))
            trace = shared.CompactPoseTrace()
            # The sole generator retains the original global trace; views keep
            # only their own selected samples below.
            shared.phase_saved(recorder, 'goal_submitted', global_physics_step=start_step,
                target=context.record()['targets'][index], device_identity=capture.device_identity())
            outcome = None
            try:
                outcome = shared.execute_capture_request(view_args, app, recorder, resources, camera_config,
                    scene=scene, initial=initial, receive_context=run['receive_context'],
                    mount_aggregate=run['mount_aggregate'], initial_camera=last_camera, trace=run['trace'],
                    ticks=ticks, request=request, global_start_step=start_step,
                    global_start_time=start_time, close_ticks=False)
            finally:
                end_step = int(recorder.result['completed_physics_steps'])
                trace.samples = [s for s in run['trace'].samples if start_step < s['step'] <= end_step]
                trace.last = (copy.deepcopy(run['trace'].last)
                    if run['trace'].last is not None and run['trace'].last['step'] > start_step else None)
                view = freeze_current_view(recorder, request, start_step, end_step, before_counts, trace)
                view['target'] = context.record()['targets'][index]
                view['trajectory_start'] = (context.record()['initial_scanner'] if index == 0
                    else recorder.result['handoff']['trajectory_start'])
                sequence.finish(index, view)
                recorder.result['views'] = sequence.records()
                recorder.result['sequence_summary']['completed_views'] = sum(v['status'] == 'SUCCEEDED_OFF' for v in sequence.views)
                recorder.save()
            require_completed_view(view)
            if outcome is None or outcome['snapshot'] is None:
                raise DriveCheckError('sequence_request', 'Successful request has no frozen backend snapshot')
            if end_step > MAX_STEPS:
                raise DriveCheckError('physics_count', 'Two-view total exceeds 3600 steps')
            last_camera = outcome['last_camera']
            shared.phase_saved(recorder, 'view_completed', global_physics_step=end_step,
                acquired=True, saved=True, confirmed_off=True)
            if index == 0:
                first_request, first_snapshot = request, outcome['snapshot']
                first_before = immutable_evidence(first_request, first_snapshot, sequence.views[0])
                handoff_goal_2(context, view, request, outcome['last_tick'], scene, capture, recorder)
                identities.append(capture.device_identity())
                scene_identities.append(scene_identity(scene))
                shared.phase_saved(recorder, 'handoff_completed', global_physics_step=end_step, next_goal_id='goal_2')
                start_step, start_time = end_step, _clock(scene['sim'])[1]
            else:
                # The same generator independently verifies activation before its
                # first goal_2 command, including exact integrator continuity.
                activation = context.record()['handoff']
                handoff = recorder.result['handoff']
                handoff.update(controller_activation=activation,
                    command_state_continuous=activation['command_unchanged'],
                    next_reference_from_latest_actual=bool(np.array_equal(activation['reference_start_world_matrix'], handoff['trajectory_start'])))
                handoff['pass'] = all(handoff[k] for k in ('first_off_and_saved', 'no_physics_advance',
                    'native_state_unchanged', 'command_state_continuous', 'next_reference_from_latest_actual', 'product_off'))
                if not handoff['pass']:
                    raise DriveCheckError('sequence_handoff', 'Controller activation did not preserve the handoff')
                after = immutable_evidence(first_request, first_snapshot, sequence.views[0])
                recorder.result['first_view_immutability'] = verify_immutable(first_before, after)
                identities.append(capture.device_identity())
        ticks.close()
        scene_identities.append(scene_identity(scene))
        if any(row != scene_identities[0] for row in scene_identities):
            raise DriveCheckError('NATIVE_VIEW_INVALID', 'Scene/native lifecycle identity changed during sequence')
        recorder.result['scene_lifecycle'] = {
            'identity_unchanged': True, 'scene_create_calls': 1,
            'reset_calls': recorder.result['initialization']['reset_calls'],
            'joint_state_writes': recorder.result['initialization']['joint_state_writes'],
            'root_state_writes': recorder.result['initialization']['root_state_writes'],
            'initial_publication_calls': recorder.result['initial_fabric_publication']['forward_calls']}
        shared.finalize_capture_scene(scene, expected, recorder, resources, run['initial_parameters'],
            last_request, total_steps=recorder.result['completed_physics_steps'])
        backend = capture.summary()
        recorder.result['camera_backend_final'] = backend
        recorder.result['two_view_profile'] = context.record()
        recorder.result['resource_continuity'] = resource_continuity(backend, identities)
        recorder.result['sequence_summary'].update(complete=True, first_result_unchanged=True,
            global_steps_contiguous=context.last_step == recorder.result['completed_physics_steps'],
            single_control_source_per_tick=recorder.result['pose_summary']['submitted_target_checks'] == context.last_step,
            total_controlled_steps=context.last_step)
        if (not recorder.result['resource_continuity']['unchanged']
                or not recorder.result['sequence_summary']['global_steps_contiguous']
                or not recorder.result['sequence_summary']['single_control_source_per_tick']):
            raise DriveCheckError('sequence_continuity', 'Device or global controller continuity failed')
        shared.phase_saved(recorder, 'sequence_completed', completed_views=2, global_physics_step=context.last_step)
    except BaseException as exc:
        sequence.fail(getattr(exc, 'category', 'runtime_exception'), str(exc))
        context.fail(getattr(exc, 'category', 'runtime_exception'), str(exc))
        recorder.result['sequence_summary']['complete'] = False
        recorder.result['sequence_failure'] = copy.deepcopy(sequence.failure)
        recorder.result['views'] = sequence.records()
        recorder.result['two_view_profile'] = context.record()
        raise
    finally:
        ticks.close()
        recorder.save()


def resource_continuity(backend, identities):
    lifecycle = backend['lifecycle']
    # Filled from backend ownership facts, never inferred from identical paths.
    result = {'identity_samples': copy.deepcopy(identities),
        'unchanged': len(identities) >= 3 and all(row == identities[0] for row in identities),
        'prepare_count': lifecycle['prepare_calls'], 'initialize_count': lifecycle['initialize_calls'],
        'begin_count': lifecycle['begin_calls'], 'off_confirmed_count': lifecycle['off_confirmed_count'],
        'release_count': lifecycle['release_effective_count']}
    if [result[k] for k in ('prepare_count', 'initialize_count', 'begin_count', 'off_confirmed_count', 'release_count')] != [1, 1, 2, 2, 1]:
        result['unchanged'] = False
    if (any(lifecycle[k] != 1 for k in ('camera_create_calls', 'product_create_calls', 'observer_create_calls'))
            or any(lifecycle[k] != 2 for k in ('off_requests', 'request_resume_calls', 'request_pause_calls'))):
        result['unchanged'] = False
    return result
