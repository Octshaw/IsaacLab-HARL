"""One capture request advanced by an external scene clock.

No physics/render loop lives here. A terminal request remains guarded until the
host validates the authority receipt and retires its device-local slot.
"""
from __future__ import annotations

import copy
import json
import math
import time
from functools import wraps
from pathlib import Path

import numpy as np
from _cr12_runtime_support import DriveCheckError, _clock
from _cr12_single_view_capture import SingleViewRequest, TERMINAL_STATES, check_arrived_hold
from _cr12_camera_capture import save_rgba_png
from _cr12_camera_mount import actual_camera_pose


def _shared_fail_closed(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        if self.shared_profile and self.execution_failure is not None:
            raise DriveCheckError('shared_execution_failed', 'Shared execution failure is sticky', failure=self.execution_failure)
        try:
            return method(self, *args, **kwargs)
        except BaseException as exc:
            if self.shared_profile and self.execution_failure is None:
                self.execution_failure = {'category': getattr(exc, 'category', type(exc).__name__),
                    'message': str(exc), 'global_step': self.latest_tick['step']}
                self.record['execution_failure'] = copy.deepcopy(self.execution_failure)
            raise
    return guarded


class CaptureRequestRunner:
    def __init__(self, binding, capture, scene, camera_config, *, start_tick,
                 output_dir, recorder, mount_aggregate, initial_camera, cancel_at_wait=False,
                 execution_profile=None, shared_model=None):
        self.binding, self.capture, self.scene = binding, capture, scene
        self.config, self.recorder = camera_config, recorder
        self.start_step, self.start_time = start_tick['step'], start_tick['physics_time_s']
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=False)
        self.request = SingleViewRequest(binding.goal_id, binding.attempt_id, capture.product_path,
                                         binding.capture_id, delivery_policy='raw-held-with-custody',
                                         execution_profile=execution_profile)
        self.shared_profile = execution_profile is not None
        self.execution_phase = 'APPROACHING'
        self.execution_failure = None
        self.control_segment_id = None
        self.clear_evidence = None
        self.delivery_ready_step = None
        self.cleanup_start_step = self.cleanup_start_time = None
        self._clear_start_step = self._clear_start_time = None
        self._clear_count = 0
        self._peer_tick = self._peer_status = None
        self._cancel_waiting_data = False
        if self.shared_profile:
            import _cr12_shared_task_profile as shared
            if execution_profile != shared.PROFILE_NAME or shared_model is None or binding.task_id != 0:
                raise DriveCheckError('shared_profile', 'Shared runner requires its trusted model and task zero')
            if binding.robot_id not in (0, 1) or bool(cancel_at_wait) != (binding.robot_id == 0):
                raise DriveCheckError('shared_profile', 'Only A cancels; B performs the one normal capture')
            self.shared = shared
            self.scanner_task_target = shared.scanner_target()
            self.cleanup_target = shared.park_pose(shared_model, 0)
            self.peer_park_target = shared.park_pose(shared_model, 1)
            for target in (self.scanner_task_target, self.cleanup_target, self.peer_park_target):
                target.setflags(write=False)
        self.request.start_motion(capture.assert_off('integration_motion_entry'), time.monotonic())
        self.mount_aggregate, self.last_camera = mount_aggregate, initial_camera
        self.latest_tick = start_tick
        self._start_q = np.array(start_tick['q'], copy=True)
        self._start_scanner = np.array(start_tick['scanner'], copy=True)
        self.start_events = capture.summary()['unique_product_event_count']
        self.cancel_at_wait = cancel_at_wait
        self.cancel_issued = False
        self.cancel_raced = False
        self.snapshot = None
        self.close_evidence = None
        self.pending_recorded = False
        self.terminal_step = None
        self.retired = False
        self._saved = False
        self.record = {
            'goal_id': binding.goal_id, 'capture_id': binding.capture_id,
            'attempt_id': binding.attempt_id, 'claim_token': binding.claim_token,
            'robot_id': binding.robot_id, 'root_path': scene.get('prim_path', scene.get('root_path')),
            'render_product_path': capture.product_path,
            'task_id': binding.task_id, 'episode_generation': binding.episode_generation,
            'global_start_step': self.start_step, 'events': [], 'artifact_saved': False,
            'artifact_error': None, 'metadata_saved': False, 'tail_hold_ticks': 0,
            'on_hold_samples': 0, 'block_end_checks': [], 'retired_after_receipt': False}
        self.record.update(max_joint_displacement_rad=0., max_scanner_displacement_m=0.)
        if self.shared_profile:
            self.record.update(execution_profile=execution_profile,
                scanner_task_target=self.scanner_task_target.tolist(), cleanup_target=self.cleanup_target.tolist(),
                execution_phases=[{'phase': self.execution_phase, 'global_step': self.start_step}])
        self._event('request_created')

    def _event(self, name, **values):
        row = {'event': name, 'global_step': self.latest_tick['step'], **values}
        self.record['events'].append(row)
        self.recorder.emit(name, goal_id=self.binding.goal_id, task_id=self.binding.task_id,
                           robot_id=self.binding.robot_id, render_product_path=self.capture.product_path,
                           **{key: value for key, value in row.items() if key != 'event'})

    @property
    def terminal(self):
        return self.request.state in TERMINAL_STATES

    @property
    def delivery_ready(self):
        if not self.shared_profile:
            return self.terminal
        return self.execution_failure is None and (
            self.terminal and self.request.state == 'SUCCEEDED_OFF' and self.binding.robot_id == 1
            or self.execution_phase in ('CLEAR_HOLD_READY', 'PENDING_R', 'RECEIPT_ACKED', 'RETIRED_CLEAR_HOLD'))

    @property
    def needs_retreat(self):
        return self.shared_profile and self.execution_failure is None and self.execution_phase == 'OFF_CONFIRMED_NO_DATA'

    def _execution_phase(self, value):
        if self.execution_phase != value:
            self.execution_phase = value
            if self.shared_profile:
                self.record['execution_phases'].append({'phase': value, 'global_step': self.latest_tick['step']})

    def _no_data_off(self, *, hold_verified=False, render_opportunity=False):
        peek = self.capture.peek_retained_snapshot()
        if peek['raw_copy_present'] or peek['fresh_identity_validated'] or self.request.acquired:
            self.cancel_raced = True
            self.record['cancel_raced'] = True
            raise DriveCheckError('cancel_not_hit', 'Shared cancellation has retained data; preserve it and stop')
        if peek['errors']:
            raise DriveCheckError('shared_cleanup_health', 'Cancelled backend has sticky errors', errors=peek['errors'])
        self.capture.assert_off('shared_bound_cleanup')
        close = self.capture.observe_close(render_opportunity=render_opportunity)
        eligible = self.capture.eligible_to_retire(self.request.ids, hold_verified=hold_verified)
        # While moving, hold is deliberately not asserted; every other retirement
        # prerequisite, including fresh events without buffers, remains mandatory.
        reasons = set(eligible['reasons']) - ({'latest_actual_hold_not_verified'} if not hold_verified else set())
        if reasons or close.get('confirmed') is not True or eligible.get('resource_healthy') is not True:
            raise DriveCheckError('shared_cleanup_health', 'Cleanup requires continuous healthy independent OFF', evidence=eligible)
        self.close_evidence = close
        return eligible

    @_shared_fail_closed
    def begin_retreat(self, control_segment_id, latest_tick):
        if not self.needs_retreat or not isinstance(control_segment_id, str) or not control_segment_id:
            raise DriveCheckError('shared_cleanup_state', 'Only the confirmed no-data cancellation can start retreat')
        if (latest_tick['step'] != self.latest_tick['step']
                or latest_tick['physics_time_s'] != self.latest_tick['physics_time_s']
                or any(not np.array_equal(latest_tick.get(k), self.latest_tick.get(k)) for k in ('q','dq','scanner','q_cmd'))):
            raise DriveCheckError('shared_cleanup_state', 'Retreat boundary is stale')
        self.verify_hold(latest_tick)
        self._no_data_off(hold_verified=True)
        self.control_segment_id = control_segment_id
        self.cleanup_start_step = latest_tick['step']
        self.cleanup_start_time = latest_tick['physics_time_s']
        self.record['cleanup_start'] = {'global_step': self.cleanup_start_step,
            'physics_time_s': self.cleanup_start_time, 'control_segment_id': control_segment_id,
            'q': np.asarray(latest_tick['q']).tolist(), 'q_cmd': copy.deepcopy(latest_tick.get('q_cmd')),
            'claim_token': self.binding.claim_token, 'goal_id': self.binding.goal_id}
        self._execution_phase('RETREATING_BOUND')

    def _peer_park(self, tick, peer_tick, peer_status):
        import _cr12_pose_control as pc
        if (not isinstance(peer_tick, dict) or not isinstance(peer_status, dict)
                or peer_tick.get('step') != tick['step']
                or peer_tick.get('physics_time_s') != tick['physics_time_s']
                or any(peer_status.get(k) is not True for k in ('off', 'resource_healthy', 'native_valid', 'guards_passed'))):
            raise DriveCheckError('shared_peer_park', 'Clear requires the same current healthy OFF peer boundary')
        pc.check_fixed_neighborhood(peer_tick['q'], self.shared.initial_q(1))
        check_arrived_hold(*pc.pose_error(peer_tick['scanner'], self.peer_park_target), peer_tick['dq'])

    def _observe_cleanup(self, tick, peer_tick, peer_status):
        import _cr12_pose_control as pc
        if self.execution_phase == 'OFF_CONFIRMED_NO_DATA':
            raise DriveCheckError('shared_cleanup_state', 'Host must activate the bound retreat before another tick')
        if tick.get('control_segment_id') != self.control_segment_id:
            raise DriveCheckError('shared_cleanup_state', 'Cleanup tick belongs to another control segment')
        elapsed = tick['step'] - self.cleanup_start_step
        limit = self.shared.MAX_STEPS + (self.shared.BLOCK_STEPS if self.delivery_ready else 0)
        if (elapsed <= 0 or elapsed > limit
                or abs(tick['physics_time_s']-self.cleanup_start_time-elapsed/120) > 1e-4):
            raise DriveCheckError('shared_cleanup_budget', 'Retreat exhausted its independent physical budget')
        self._no_data_off(render_opportunity=tick['rendered'])
        self._peer_park(tick, peer_tick, peer_status)
        pc.check_fixed_neighborhood(tick['q'], self.shared.clear_q(0)) if self.delivery_ready else None
        ep, er = pc.pose_error(tick['scanner'], self.cleanup_target)
        q = np.asarray(tick['q'], dtype=float)
        dq = np.asarray(tick['dq'], dtype=float)
        stable = (q.shape == (6,) and dq.shape == (6,) and np.isfinite([q, dq]).all()
            and np.max(np.abs(q-self.shared.clear_q(0))) <= math.radians(.5)
            and ep <= .002 and er <= math.radians(.25) and np.max(np.abs(dq)) <= .01)
        if self.delivery_ready and not stable:
            raise DriveCheckError('shared_clear_lost', 'Fixed clear holding was lost after qualification')
        if stable:
            if self._clear_start_step is None:
                self._clear_start_step, self._clear_start_time = tick['step'], tick['physics_time_s']
            self._clear_count += 1
        else:
            self._clear_count = 0
            self._clear_start_step = self._clear_start_time = None
        span = 0. if self._clear_start_time is None else tick['physics_time_s']-self._clear_start_time
        self.clear_evidence = {'physics_step': tick['step'], 'window_start_step': self._clear_start_step,
            'window_end_step': tick['step'], 'stable_samples': self._clear_count, 'stable_span_s': span,
            'position_error_m': ep, 'orientation_error_rad': er, 'peer_park_verified': True,
            'peer_physics_step': peer_tick['step'], 'control_segment_id': self.control_segment_id,
            'claim_token': self.binding.claim_token, 'goal_id': self.binding.goal_id,
            'fixed_q_error_rad': float(np.max(np.abs(q-self.shared.clear_q(0)))),
            'max_abs_native_dq_rad_s': float(np.max(np.abs(dq)))}
        self.record['clear_evidence'] = copy.deepcopy(self.clear_evidence)
        if self._clear_count >= 121 and span >= 1-1e-6 and tick.get('pose_reached') is True:
            if self.delivery_ready_step is None:
                self.delivery_ready_step = tick['step']
            self._execution_phase('CLEAR_HOLD_READY')
        if elapsed == self.shared.MAX_STEPS and not self.delivery_ready:
            raise DriveCheckError('shared_cleanup_budget', 'Retreat did not establish fixed clear at its endpoint')

    def pending_metadata(self):
        if not self.delivery_ready:
            raise DriveCheckError('shared_delivery_not_ready', 'Camera terminal alone is not a delivery boundary')
        metadata = {'request': self.request.summary(), 'terminal_physics_step': self.terminal_step}
        if self.shared_profile:
            metadata.update(scanner_task_target=self.scanner_task_target.tolist(),
                cleanup_target=self.cleanup_target.tolist(), clear_evidence=copy.deepcopy(self.clear_evidence),
                cancellation_source='stable_waiting_data' if self._cancel_waiting_data else None,
                camera_failure_category=None if self.request.failure is None else self.request.failure['category'],
                control_segment_id=self.control_segment_id)
        return metadata

    def _close(self):
        if self.request.close_boundary is None:
            boundary = self.request.request_close(time.monotonic())
            self.capture.request_off({**boundary, 'global_physics_step': self.latest_tick['step'],
                                      'native_physics_clock': list(_clock(self.scene['sim']))})
            self._event('request_off')

    def _accept_retained(self):
        peek = self.capture.peek_retained_snapshot()
        candidate = peek['snapshot']
        if candidate is not None and not self.request.acquired:
            if not peek['fresh_identity_validated']:
                raise DriveCheckError('capture_identity', 'Retained raw lacks validated fresh identity')
            self.request.retain_custody(candidate)
            self.request.accept_frame(candidate['metadata'], now=time.monotonic())
            self.capture.mark_snapshot_accepted(self.request.ids)
            self.snapshot = candidate
            self._event('data_acquired', rendering_frame=candidate['metadata']['rendering_frame'])
            if self.cancel_issued:
                self.cancel_raced = True
                self.record['cancel_raced'] = True
            self._close()
        return peek

    @_shared_fail_closed
    def before_tick(self):
        if self.retired:
            raise DriveCheckError('request_state', 'Retired request cannot advance')
        if self.shared_profile:
            maximum = self.shared.A_BIND_MAX_STEPS if self.binding.robot_id == 0 else self.shared.B_BIND_MAX_STEPS
            if self.latest_tick['step']-self.start_step >= maximum + (self.shared.BLOCK_STEPS if self.delivery_ready else 0):
                raise DriveCheckError('shared_binding_budget', 'Bound execution exhausted its fixed role budget')
            if self.delivery_ready_step is not None and self.latest_tick['step'] >= self.delivery_ready_step+self.shared.BLOCK_STEPS:
                raise DriveCheckError('shared_binding_budget', 'Ready delivery cannot wait beyond the current block tail')
        if self.terminal:
            return
        self.request.check_before_tick(time.monotonic())
        if self.cancel_at_wait and not self.cancel_issued and self.request.state == 'WAITING_DATA':
            peek = self._accept_retained()
            if peek['raw_copy_present'] or self.request.acquired:
                self.cancel_raced = True
                raise DriveCheckError('cancel_not_hit', 'Fresh data won before the no-data cancel boundary')
            self.cancel_issued = True
            self._cancel_waiting_data = self.request.arrival is not None
            self.request.cancel(time.monotonic())
            self._execution_phase('CANCEL_CLOSING')
            self._event('cancel_requested', injection='WAITING_DATA before first subsequent physics/render')
            self._close()
        if self.request.state == 'MOVING_OFF':
            self.capture.assert_off('integration_moving_before_tick')

    @_shared_fail_closed
    def observe_tick(self, tick, *, peer_tick=None, peer_status=None):
        if self.shared_profile and tick['step'] != self.latest_tick['step'] + 1:
            raise DriveCheckError('shared_clock', 'Runner requires every consecutive actual tick')
        if self.shared_profile:
            if (tick.get('goal_id') != self.binding.goal_id
                    or not np.array_equal(tick.get('scanner_task_target'), self.scanner_task_target)):
                raise DriveCheckError('shared_task_identity', 'Control tick changed the immutable claim/scanner task')
            if any(tick.get('sample', {}).get('guard_'+name) != 'PASS' for name in
                   ('clock', 'joint', 'contact', 'geometry', 'frame', 'render_clock')):
                raise DriveCheckError('shared_guard_evidence', 'Shared tick lacks the actual completed physical guards')
            expected_target = self.cleanup_target if self.cleanup_start_step is not None else self.scanner_task_target
            if not np.array_equal(tick.get('target'), expected_target):
                raise DriveCheckError('shared_task_identity', 'Active control target differs from its frozen task/cleanup endpoint')
        self.latest_tick = tick
        self._peer_tick, self._peer_status = peer_tick, peer_status
        self.record['max_joint_displacement_rad'] = max(self.record['max_joint_displacement_rad'],
            float(np.max(np.abs(tick['q'] - self._start_q))))
        self.record['max_scanner_displacement_m'] = max(self.record['max_scanner_displacement_m'],
            float(np.linalg.norm(tick['scanner'][:3, 3] - self._start_scanner[:3, 3])))
        before = self.request.state
        if self.terminal:
            self.record['tail_hold_ticks'] += 1
            if self.shared_profile and self.binding.robot_id == 0:
                self._observe_cleanup(tick, peer_tick, peer_status)
                return
            self.verify_hold(tick)
            self.capture.observe_close(render_opportunity=tick['rendered'])
            eligible = self.capture.eligible_to_retire(self.request.ids, hold_verified=True)
            if eligible['eligible'] is not True:
                raise DriveCheckError('handoff_ineligible', 'Post-terminal device eligibility lost', evidence=eligible)
            return
        local = {**tick, 'step': tick['step']-self.start_step,
                 'controlled_time_s': tick['physics_time_s']-self.start_time}
        if local.get('local_step', local['step']) != local['step']:
            raise DriveCheckError('physics_count', 'Pose/request local tick differs')
        self.request.observe_tick(local, self.capture.read_updates_enabled(), time.monotonic())
        if before == 'MOVING_OFF':
            self.capture.assert_off('integration_moving_after_tick')
            if self.capture.summary()['unique_product_event_count'] != self.start_events:
                raise DriveCheckError('camera_moving_output', 'Product event during OFF motion')
        if tick['rendered']:
            self.last_camera = actual_camera_pose(self.capture.camera, tick['poses']['link_6'], self.config,
                                                 clock=_clock(self.scene['sim']), phase=self.request.state)
            self.mount_aggregate['count'] += 1
            for key in ('position_error_m', 'orientation_error_rad'):
                dest = 'maximum_' + key
                self.mount_aggregate[dest] = max(self.mount_aggregate[dest], self.last_camera[key])
        if before in ('WAITING_DATA', 'CAPTURE_STARTING'):
            self.record['on_hold_samples'] += 1
        if self.request.state == 'ARRIVED_HOLD_OFF':
            self._execution_phase('SCAN_HOLD')
            self.record['arrival'] = copy.deepcopy(self.request.arrival)
            self._event('pose_reached', stable_samples=self.request.arrival['stable_samples'])
            starting = self.request.capture_starting(time.monotonic())
            boundary = {**starting['boundary'], 'global_physics_step': tick['step'],
                        'scanner_world_matrix': tick['scanner'].tolist(),
                        'native_physics_clock': list(_clock(self.scene['sim']))}
            capture_ids = {**starting['ids'], **{key: getattr(self.binding, key) for key in
                ('env_id', 'robot_id', 'task_id', 'claim_token', 'episode_generation', 'run_instance_id')}}
            on = self.capture.begin_capture(capture_ids, boundary)
            self.request.capture_started({'updates_enabled': on['actual'],
                                          'render_product_path': self.capture.product_path})
            self.record['on_baseline'] = copy.deepcopy(self.capture.summary()['request'])
            self.record['on_boundary'] = boundary
            self._event('capture_on')
            self._execution_phase('WAITING_DATA')
        elif self.request.state == 'WAITING_DATA':
            self.capture.poll_snapshot()  # includes the backend sticky/identity guard
            self._accept_retained()
        elif self.request.state in ('CAPTURE_CLOSING', 'CLOSING_AFTER_FAILURE'):
            self._accept_retained()  # a cancel race may not be discarded as no-data
            self.close_evidence = self.capture.observe_close(render_opportunity=tick['rendered'])
            self.request.observe_close(self.close_evidence, time.monotonic())
        if self.terminal:
            if self.request.state == 'STOP_UNCONFIRMED':
                raise DriveCheckError('off_unconfirmed', 'Request ended without independent OFF')
            self.terminal_step = tick['step']
            self.record['global_terminal_step'] = tick['step']
            self._event('request_terminal', state=self.request.state)
            self.save_data()
            if self.shared_profile and self.binding.robot_id == 1 and self.request.state == 'SUCCEEDED_OFF':
                self.delivery_ready_step = tick['step']
            if self.shared_profile and self.binding.robot_id == 0:
                if self.cancel_raced or self.request.acquired:
                    raise DriveCheckError('cancel_not_hit', 'Data won the cancel race; keep the result and stop this case')
                if (not self.cancel_issued or not self._cancel_waiting_data
                        or self.request.state != 'FAILED_OFF' or self.request.failure is None
                        or self.request.failure['category'] != 'CANCELLED' or not self.request.off_confirmed):
                    raise DriveCheckError('shared_cleanup_state', 'Only a stable WAITING_DATA no-data cancellation may retreat')
                self.verify_hold(tick)
                self._no_data_off(hold_verified=True)
                self._peer_park(tick, peer_tick, peer_status)
                self._execution_phase('OFF_CONFIRMED_NO_DATA')
        if before != self.request.state:
            self._event('request_phase_changed', before=before, after=self.request.state,
                        physics_time_s=tick['physics_time_s'])

    def verify_hold(self, tick):
        if self.shared_profile and self.binding.robot_id == 0 and self.cleanup_start_step is not None:
            import _cr12_pose_control as pc
            pc.check_fixed_neighborhood(tick['q'], self.shared.clear_q(0))
            check_arrived_hold(*pc.pose_error(tick['scanner'], self.cleanup_target), tick['dq'])
            return
        if self.shared_profile:
            import _cr12_pose_control as pc
            check_arrived_hold(*pc.pose_error(tick['scanner'], self.scanner_task_target), tick['dq'])
            return
        sample = tick['sample']
        check_arrived_hold(sample['target_position_error_m'], sample['target_orientation_error_rad'], tick['dq'])

    @_shared_fail_closed
    def boundary(self, *, peer_tick=None, peer_status=None):
        """Fresh checks, including after terminal lock and before authority C/R."""
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_cr12_execution_adapter import ExecutionBoundaryEvidence
        from run_cr12_single_view_capture import native_validity
        native_validity(self.scene['robot'], self.scene['sim'])
        if self.shared_profile and self.binding.robot_id == 0 and self.terminal:
            tick = self.latest_tick
            self._no_data_off(hold_verified=self.delivery_ready)
            self._peer_park(tick, peer_tick, peer_status)
            if self.delivery_ready:
                self.verify_hold(tick)
                if self.clear_evidence is None or self.clear_evidence['physics_step'] != tick['step']:
                    raise DriveCheckError('shared_clear_stale', 'Clear evidence must be from this exact block boundary')
            evidence = self.clear_evidence or {}
            self.record['block_end_checks'].append({'global_step': tick['step'], 'off': True,
                'holding': self.delivery_ready, 'healthy': True, 'no_data': True,
                'execution_phase': self.execution_phase, 'clear_evidence': copy.deepcopy(self.clear_evidence)})
            return ExecutionBoundaryEvidence(physics_step=tick['step'], goal_id=self.binding.goal_id,
                capture_id=self.binding.capture_id, off_confirmed=True, holding=self.delivery_ready,
                resource_healthy=True, native_valid=True, no_pending_data=True, continuous_hold=self.delivery_ready,
                hold_basis='clear', control_segment_id=self.control_segment_id,
                physical_clear=self.delivery_ready, clear_stable_samples=evidence.get('stable_samples', 0),
                clear_stable_span_s=evidence.get('stable_span_s', 0.),
                clear_window_start_step=evidence.get('window_start_step'),
                clear_window_end_step=evidence.get('window_end_step'), peer_park_verified=True,
                peer_physics_step=peer_tick['step'])
        peek = self.capture.peek_retained_snapshot()
        no_data = not peek['raw_copy_present'] and not self.request.acquired
        if self.terminal:
            self.verify_hold(self.latest_tick)
            self.close_evidence = self.capture.observe_close(render_opportunity=False)
            eligible = self.capture.eligible_to_retire(self.request.ids, hold_verified=True)
            if eligible['eligible'] is not True:
                raise DriveCheckError('handoff_ineligible', 'Block-end device eligibility lost', evidence=eligible)
            if self.cancel_raced:
                raise DriveCheckError('cancel_not_hit', 'No-data cancellation raced with real acquisition')
            self.record['block_end_checks'].append({
                'global_step': self.latest_tick['step'], 'off': bool(self.close_evidence['confirmed']),
                'holding': True, 'healthy': True, 'no_data': no_data, 'eligibility': eligible})
        else:
            self.capture.read_updates_enabled()
        return ExecutionBoundaryEvidence(
            physics_step=self.latest_tick['step'], goal_id=self.binding.goal_id,
            capture_id=self.binding.capture_id, off_confirmed=bool(self.request.off_confirmed),
            holding=self.request.arrival is not None, resource_healthy=not bool(peek['errors']),
            native_valid=True, no_pending_data=no_data, continuous_hold=self.request.arrival is not None)

    def save_data(self):
        if self._saved:
            return
        self._saved = True
        if self.snapshot is not None:
            try:
                path = self.output_dir / 'camera_rgba.png'
                evidence = save_rgba_png(path, self.snapshot['rgba'])
                self.request.record_artifact(str(path))
                self.record.update(artifact_saved=True, artifact_path=str(path), artifact=evidence)
            except Exception as exc:
                self.request.record_artifact(error=f'{type(exc).__name__}: {exc}')
                self.record['artifact_error'] = f'{type(exc).__name__}: {exc}'
        self.record['capture_metadata'] = (None if self.snapshot is None else copy.deepcopy(self.snapshot['metadata']))

    def finalize_record(self):
        self.record['request'] = self.request.summary()
        self.record['off_confirmation'] = copy.deepcopy(self.close_evidence)
        self.record['global_end_step'] = self.latest_tick['step']
        self.record['cancel_issued'] = self.cancel_issued
        self.record['cancel_raced'] = self.cancel_raced
        self.record['pose_target'] = (self.scanner_task_target.tolist() if self.shared_profile
            else self.latest_tick['target'].tolist() if 'target' in self.latest_tick else None)
        if self.shared_profile:
            self.record.update(execution_phase=self.execution_phase, clear_evidence=copy.deepcopy(self.clear_evidence))
        path = self.output_dir / 'capture_metadata.json'
        self.record['metadata_saved'] = True
        try:
            path.write_text(json.dumps(self.record, indent=2, ensure_ascii=True, allow_nan=False)+'\n', encoding='utf-8')
        except Exception:
            self.record['metadata_saved'] = False
            raise
        return copy.deepcopy(self.record)

