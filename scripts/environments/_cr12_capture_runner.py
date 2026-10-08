"""One capture request advanced by an external scene clock.

No physics/render loop lives here. A terminal request remains guarded until the
host validates the authority receipt and retires its device-local slot.
"""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import numpy as np
from _cr12_runtime_support import DriveCheckError, _clock
from _cr12_single_view_capture import SingleViewRequest, TERMINAL_STATES, check_arrived_hold
from _cr12_camera_capture import save_rgba_png
from _cr12_camera_mount import actual_camera_pose


class CaptureRequestRunner:
    def __init__(self, binding, capture, scene, camera_config, *, start_tick,
                 output_dir, recorder, mount_aggregate, initial_camera, cancel_at_wait=False):
        self.binding, self.capture, self.scene = binding, capture, scene
        self.config, self.recorder = camera_config, recorder
        self.start_step, self.start_time = start_tick['step'], start_tick['physics_time_s']
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=False)
        self.request = SingleViewRequest(binding.goal_id, binding.attempt_id, capture.product_path,
                                         binding.capture_id, delivery_policy='raw-held-with-custody')
        self.request.start_motion(capture.assert_off('integration_motion_entry'), time.monotonic())
        self.mount_aggregate, self.last_camera = mount_aggregate, initial_camera
        self.latest_tick = start_tick
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
            'task_id': binding.task_id, 'episode_generation': binding.episode_generation,
            'global_start_step': self.start_step, 'events': [], 'artifact_saved': False,
            'artifact_error': None, 'metadata_saved': False, 'tail_hold_ticks': 0,
            'on_hold_samples': 0, 'block_end_checks': [], 'retired_after_receipt': False}
        self._event('request_created')

    def _event(self, name, **values):
        row = {'event': name, 'global_step': self.latest_tick['step'], **values}
        self.record['events'].append(row)
        self.recorder.emit(name, goal_id=self.binding.goal_id, task_id=self.binding.task_id,
                           **{key: value for key, value in row.items() if key != 'event'})

    @property
    def terminal(self):
        return self.request.state in TERMINAL_STATES

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

    def before_tick(self):
        if self.retired:
            raise DriveCheckError('request_state', 'Retired request cannot advance')
        if self.terminal:
            return
        self.request.check_before_tick(time.monotonic())
        if self.cancel_at_wait and not self.cancel_issued and self.request.state == 'WAITING_DATA':
            peek = self._accept_retained()
            if peek['raw_copy_present'] or self.request.acquired:
                self.cancel_raced = True
                raise DriveCheckError('cancel_not_hit', 'Fresh data won before the no-data cancel boundary')
            self.cancel_issued = True
            self.request.cancel(time.monotonic())
            self._event('cancel_requested', injection='WAITING_DATA before first subsequent physics/render')
            self._close()
        if self.request.state == 'MOVING_OFF':
            self.capture.assert_off('integration_moving_before_tick')

    def observe_tick(self, tick):
        self.latest_tick = tick
        before = self.request.state
        if self.terminal:
            self.record['tail_hold_ticks'] += 1
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
            self.record['arrival'] = copy.deepcopy(self.request.arrival)
            self._event('pose_reached', stable_samples=self.request.arrival['stable_samples'])
            starting = self.request.capture_starting(time.monotonic())
            boundary = {**starting['boundary'], 'global_physics_step': tick['step'],
                        'scanner_world_matrix': tick['scanner'].tolist(),
                        'native_physics_clock': list(_clock(self.scene['sim']))}
            on = self.capture.begin_capture(starting['ids'], boundary)
            self.request.capture_started({'updates_enabled': on['actual'],
                                          'render_product_path': self.capture.product_path})
            self.record['on_baseline'] = copy.deepcopy(self.capture.summary()['request'])
            self.record['on_boundary'] = boundary
            self._event('capture_on')
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

    def verify_hold(self, tick):
        sample = tick['sample']
        check_arrived_hold(sample['target_position_error_m'], sample['target_orientation_error_rad'], tick['dq'])

    def boundary(self):
        """Fresh checks, including after terminal lock and before authority C/R."""
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_cr12_execution_adapter import ExecutionBoundaryEvidence
        from run_cr12_single_view_capture import native_validity
        native_validity(self.scene['robot'], self.scene['sim'])
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
        self.record['pose_target'] = self.latest_tick['target'].tolist() if 'target' in self.latest_tick else None
        path = self.output_dir / 'capture_metadata.json'
        self.record['metadata_saved'] = True
        try:
            path.write_text(json.dumps(self.record, indent=2, ensure_ascii=True, allow_nan=False)+'\n', encoding='utf-8')
        except Exception:
            self.record['metadata_saved'] = False
            raise
        return copy.deepcopy(self.record)

