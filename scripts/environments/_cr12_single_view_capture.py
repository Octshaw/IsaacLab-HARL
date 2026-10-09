"""One-request capture lifecycle; no renderer, camera, or physics calls.

Evidence is supplied by the scene owner and owned camera backend. This module
does not create frames, OFF acknowledgements, render opportunities, or clocks.
"""
from __future__ import annotations

import math

DT = 1 / 120
POSE_STEPS = 960
CAPTURE_STEPS = 600
CLOSE_STEPS = 240
TOTAL_STEPS = 1800
CAPTURE_WALL_SECONDS = 60.0
CLOSE_WALL_SECONDS = 30.0
TERMINAL_STATES = frozenset(('SUCCEEDED_OFF', 'FAILED_OFF', 'STOP_UNCONFIRMED'))


class CaptureRequestError(RuntimeError):
    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category = category
        self.details = details


def check_arrived_hold(position_error_m, orientation_error_rad, native_dq):
    """No restabilization grace: every post-arrival sample must remain valid."""
    values = [float(position_error_m), float(orientation_error_rad)]
    speeds = [float(v) for v in native_dq]
    if len(speeds) != 6 or not all(math.isfinite(v) for v in values + speeds):
        raise CaptureRequestError('CAPTURE_HOLD_LOST', 'Non-finite or malformed actual hold sample')
    if values[0] < 0 or values[1] < 0 or values[0] > .002 or values[1] > math.radians(.25) or max(map(abs, speeds)) > .01:
        raise CaptureRequestError('CAPTURE_HOLD_LOST', 'Actual scanner left the accepted arrival tolerance',
                                  position_error_m=values[0], orientation_error_rad=values[1],
                                  max_abs_native_dq_rad_s=max(map(abs, speeds)))


class SingleViewRequest:
    """A single request with sticky failure and separate data/save/OFF facts."""
    def __init__(self, goal_id, attempt_id, product_path, capture_id, *, delivery_policy='artifact-required', execution_profile=None):
        for name, value in (('goal_id', goal_id), ('attempt_id', attempt_id),
                            ('product_path', product_path), ('capture_id', capture_id)):
            if not isinstance(value, str) or not value:
                raise ValueError(f'{name} must be a nonempty string')
        self.ids = {'goal_id': goal_id, 'attempt_id': attempt_id, 'capture_id': capture_id}
        if delivery_policy not in ('artifact-required', 'raw-held-with-custody'):
            raise ValueError('Unsupported data delivery policy')
        self.delivery_policy = delivery_policy
        self.pose_steps, self.total_steps = POSE_STEPS, TOTAL_STEPS
        if execution_profile is not None:
            from _cr12_shared_task_profile import PROFILE_NAME, MAX_STEPS, REQUEST_MAX_STEPS
            if execution_profile != PROFILE_NAME or delivery_policy != 'raw-held-with-custody':
                raise ValueError('Only the trusted shared capture integration profile is supported')
            self.pose_steps, self.total_steps = MAX_STEPS, REQUEST_MAX_STEPS
        self.execution_profile = execution_profile
        self._custody = None
        self.cancel_requested = None
        self.product_path = product_path
        self.state = 'READY_OFF'
        self.step = 0
        self.simulation_time = None
        self.controlled_time_s = 0.0
        self._last_wall = None
        self.arrival = None
        self.capture_boundary = None
        self.close_boundary = None
        self.acquired = False
        self.artifact_saved = False
        self.off_confirmed = False
        self.frame = None
        self.artifact_path = None
        self.artifact_error = None
        self.failure = None
        self.close_evidence = None
        self.transitions = [{'state': self.state, 'physics_step': 0}]

    def _now(self, now):
        value = float(now)
        if not math.isfinite(value) or (self._last_wall is not None and value < self._last_wall):
            self._reject('CLOCK', 'Wall clock must be finite and monotonic')
        self._last_wall = value
        return value

    def _transition(self, state):
        if self.state != state:
            self.state = state
            self.transitions.append({'state': state, 'physics_step': self.step,
                                     'simulation_time': self.simulation_time})

    def _reject(self, category, message, **details):
        if self.failure is None:
            self.failure = {'category': category, 'message': message, 'details': details,
                            'physics_step': self.step}
        if self.off_confirmed:
            self._transition('FAILED_OFF')
        elif self.state not in TERMINAL_STATES:
            self._transition('CLOSING_AFTER_FAILURE')
        raise CaptureRequestError(category, message, **details)

    def _require(self, *states):
        if self.state not in states:
            self._reject('STATE', f'Operation unavailable in {self.state}', expected=list(states))

    def _off(self, evidence):
        if not isinstance(evidence, dict) or evidence.get('updates_enabled') is not False:
            self._reject('OFF_REQUIRED', 'Actual product updates must be disabled')

    def start_motion(self, off_evidence, now):
        self._require('READY_OFF')
        self._now(now)
        self._off(off_evidence)
        self._transition('MOVING_OFF')

    def observe_tick(self, tick, updates_enabled, now):
        """Observe exactly one real post-step sample, never an interpolated state."""
        self._now(now)
        if self.state in TERMINAL_STATES:
            self._reject('STATE', 'A terminal request cannot consume more physical ticks')
        step = tick.get('step')
        actual_time = float(tick.get('controlled_time_s', math.nan))
        physics_time = float(tick.get('physics_time_s', math.nan))
        if (type(step) is not int or step != self.step + 1 or step > self.total_steps
                or not math.isfinite(actual_time) or not math.isfinite(physics_time)
                or abs(actual_time - step * DT) > 1e-4
                or (self.simulation_time is not None and abs(physics_time-self.simulation_time-DT) > 1e-4)):
            self._reject('CLOCK', 'Missing, extra, or inconsistent controlled physical tick')
        self.step, self.controlled_time_s, self.simulation_time = step, actual_time, physics_time
        self._check_elapsed(now, before_tick=False)
        if self.state in ('MOVING_OFF', 'ARRIVED_HOLD_OFF'):
            self._off({'updates_enabled': updates_enabled})
        if self.state == 'MOVING_OFF':
            if step > self.pose_steps:
                self._reject('POSE_TIMEOUT', f'Arrival was not established within {self.pose_steps} steps')
            if tick.get('pose_reached') is True:
                sample = tick.get('sample', {})
                count = sample.get('stable_samples', 0)
                span = sample.get('stable_span_s', 0)
                if type(count) is not int or count < 121 or not math.isfinite(float(span)) or span < 1-1e-6:
                    self._reject('ARRIVAL_EVIDENCE', 'Arrival requires 121 samples spanning at least one second')
                self.arrival = {'physics_step': step, 'simulation_time': physics_time,
                                'controlled_time_s': actual_time, 'stable_samples': count, 'stable_span_s': span}
                self._transition('ARRIVED_HOLD_OFF')
        if self.arrival is not None:
            sample = tick.get('sample', {})
            try:
                check_arrived_hold(sample.get('target_position_error_m', math.nan),
                                   sample.get('target_orientation_error_rad', math.nan), tick.get('dq', []))
            except CaptureRequestError as exc:
                self._reject(exc.category, str(exc), **exc.details)

    def capture_starting(self, now):
        self._require('ARRIVED_HOLD_OFF')
        now = self._now(now)
        self.capture_boundary = {'physics_step': self.step, 'simulation_time': self.simulation_time,
                                 'wall_time': now}
        self._transition('CAPTURE_STARTING')
        return {'ids': dict(self.ids), 'boundary': dict(self.capture_boundary)}

    def capture_started(self, on_evidence):
        self._require('CAPTURE_STARTING')
        if (not isinstance(on_evidence, dict) or on_evidence.get('updates_enabled') is not True
                or on_evidence.get('render_product_path') != self.product_path):
            self._reject('ON_EVIDENCE', 'Dedicated product ON readback is missing or mismatched')
        self._transition('WAITING_DATA')

    def accept_frame(self, metadata, now=None):
        cancellation_race = (self.delivery_policy == 'raw-held-with-custody'
            and self.state == 'CLOSING_AFTER_FAILURE' and self.failure is not None
            and self.failure['category'] == 'CANCELLED' and not self.off_confirmed)
        if not cancellation_race:
            self._require('WAITING_DATA')
        if now is not None:
            self._check_elapsed(self._now(now), before_tick=False)
        if not isinstance(metadata, dict) or metadata.get('fresh') is not True:
            self._reject('FRAME_IDENTITY', 'Frame lacks backend evidence for a fresh same-event buffer')
        if any(metadata.get(key) != value for key, value in self.ids.items()) or metadata.get('render_product_path') != self.product_path:
            self._reject('FRAME_IDENTITY', 'Frame does not belong to this capture/product')
        source_time = metadata.get('source_time')
        receive_time = metadata.get('received_wall_time')
        if (isinstance(metadata.get('rendering_frame'), bool) or not isinstance(metadata.get('rendering_frame'), (int, float))
                or not math.isfinite(float(metadata['rendering_frame']))
                or source_time is None or not math.isfinite(float(source_time))
                or receive_time is None or not math.isfinite(float(receive_time))):
            self._reject('FRAME_IDENTITY', 'Frame source and receive timing evidence is incomplete')
        # The owned backend proves event > ON baseline and copies the same updated
        # Camera frame. Do not substitute receive time for exposure/source time.
        from copy import deepcopy
        self.frame = deepcopy(metadata)
        self.acquired = True
        if cancellation_race:
            # This removes only the request's provisional cancellation outcome,
            # never a backend/resource failure. The cancellation remains recorded.
            self.failure = None
            self.cancel_requested['superseded_by_acquisition'] = True
        self._transition('CAPTURE_CLOSING' if self.close_boundary is not None else 'DATA_RECEIVED')

    def retain_custody(self, snapshot):
        """Hold independent immutable raw data before accepting its metadata.

        This is an explicit integration delivery policy. No acquired boolean is
        set here: source validation and FSM acceptance remain separate facts.
        """
        import numpy as np
        from copy import deepcopy
        if self.delivery_policy != 'raw-held-with-custody':
            raise CaptureRequestError('CUSTODY', 'Raw custody requires the explicit integration delivery policy')
        if self._custody is not None:
            raise CaptureRequestError('CUSTODY', 'Retained custody cannot be overwritten')
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get('metadata'), dict):
            raise CaptureRequestError('CUSTODY', 'A real raw snapshot and source metadata are required')
        rgba, metadata = snapshot.get('rgba'), snapshot['metadata']
        if (not isinstance(rgba, np.ndarray) or rgba.dtype != np.uint8 or rgba.ndim != 3
                or rgba.shape[-1] != 4 or min(rgba.shape[:2]) <= 0 or rgba.flags.writeable):
            raise CaptureRequestError('CUSTODY', 'Custody requires nonempty readonly HxWx4 uint8 data')
        if (metadata.get('fresh') is not True or metadata.get('render_product_path') != self.product_path
                or any(metadata.get(key) != value for key, value in self.ids.items())):
            raise CaptureRequestError('CUSTODY', 'Raw data identity does not match this fresh request')
        # A bytes-backed array cannot have WRITEABLE switched back on by a reader.
        # Its independent storage survives camera slot retirement and reuse.
        owned = np.frombuffer(rgba.tobytes(order='C'), dtype=np.uint8).reshape(rgba.shape)
        self._custody = {'rgba': owned, 'metadata': deepcopy(metadata)}

    def _custody_valid(self):
        if self._custody is None:
            return False
        import numpy as np
        rgba, metadata = self._custody['rgba'], self._custody['metadata']
        return (isinstance(rgba, np.ndarray) and rgba.dtype == np.uint8 and rgba.ndim == 3
                and rgba.shape[-1] == 4 and min(rgba.shape[:2]) > 0 and not rgba.flags.writeable
                and metadata.get('fresh') is True and metadata.get('render_product_path') == self.product_path
                and all(metadata.get(key) == value for key, value in self.ids.items())
                and (self.frame is None or metadata == self.frame))

    def peek_custody(self):
        """Return a reference to owned immutable data and a metadata copy, no I/O."""
        from copy import deepcopy
        if not self._custody_valid():
            return None
        return {'rgba': self._custody['rgba'], 'metadata': deepcopy(self._custody['metadata'])}

    def record_artifact(self, path=None, error=None):
        if not self.acquired:
            self._reject('ARTIFACT', 'No acquired frame exists to save')
        if error is not None:
            self.artifact_error = str(error)
            self.artifact_saved = False
            if self.delivery_policy == 'artifact-required':
                self.fail('ARTIFACT', str(error))
        elif not isinstance(path, str) or not path:
            self._reject('ARTIFACT', 'Saved artifact path is missing')
        elif self.artifact_error is None:
            self.artifact_path, self.artifact_saved = path, True

    def request_close(self, now):
        now = self._now(now)
        if self.state in TERMINAL_STATES:
            return self.close_boundary
        if self.close_boundary is None:
            self.close_boundary = {'physics_step': self.step, 'simulation_time': self.simulation_time,
                                   'wall_time': now}
        if self.failure is None and not self.acquired:
            self.fail('NO_DATA', 'Closing before a valid frame was acquired')
        self._transition('CLOSING_AFTER_FAILURE' if self.failure else 'CAPTURE_CLOSING')
        return dict(self.close_boundary)

    def observe_close(self, evidence, now):
        now = self._now(now)
        self._require('CAPTURE_CLOSING', 'CLOSING_AFTER_FAILURE')
        if self.close_boundary is None:
            self._reject('STATE', 'Close observation requires a recorded OFF request')
        self._check_elapsed(now, before_tick=False)
        self._off(evidence)
        self.close_evidence = dict(evidence)
        if evidence.get('confirmed') is True:
            opportunities, quiet = evidence.get('opportunity_count'), evidence.get('quiet_opportunities')
            if type(opportunities) is not int or type(quiet) is not int or opportunities < 30 or quiet < 6 or quiet > opportunities:
                self._reject('OFF_EVIDENCE', 'OFF confirmation lacks 30 opportunities and six final quiet opportunities')
            self.off_confirmed = True
            if self.failure is None:
                if self.delivery_policy == 'artifact-required' and not self.artifact_saved:
                    self.fail('ARTIFACT', 'Acquired data has no successfully saved artifact')
                elif self.delivery_policy == 'raw-held-with-custody' and not self._custody_valid():
                    self.fail('CUSTODY', 'Acquired data is not retained by a valid custodian')
            self._transition('FAILED_OFF' if self.failure else 'SUCCEEDED_OFF')
        return self.state

    def fail(self, category, message, now=None, **details):
        if now is not None:
            self._now(now)
        if self.failure is None:
            self.failure = {'category': str(category), 'message': str(message), 'details': details,
                            'physics_step': self.step}
        if self.off_confirmed:
            self._transition('FAILED_OFF')
        elif self.state != 'STOP_UNCONFIRMED':
            self._transition('CLOSING_AFTER_FAILURE')

    def cancel(self, now):
        if self.delivery_policy == 'raw-held-with-custody':
            self._now(now)
            if self.cancel_requested is None:
                self.cancel_requested = {'physics_step': self.step, 'wall_time': float(now),
                                         'superseded_by_acquisition': self.acquired}
            if self.acquired:
                return  # Keep this result and the ongoing OFF drain; never restart ON.
        self.fail('CANCELLED', 'Request cancelled', now)

    def stop_unconfirmed(self, category, message, now=None):
        """Record an abort that cannot safely provide the required OFF evidence."""
        self.fail(category, message, now)
        if not self.off_confirmed:
            self._transition('STOP_UNCONFIRMED')

    def check_before_tick(self, now):
        """Call before next(generator); endpoint evidence may be processed first."""
        now = self._now(now)
        if self.state in TERMINAL_STATES:
            self._reject('STATE', 'Terminal request must not advance physics')
        self._check_elapsed(now, before_tick=True)

    def _check_elapsed(self, now, *, before_tick):
        # The last permitted post-step sample can still deliver a frame/OFF ACK.
        # Another step is forbidden at that endpoint; wall budgets are hard caps.
        def exhausted(steps, limit):
            return steps >= limit if before_tick else steps > limit
        if exhausted(self.step, self.total_steps):
            self.fail('TOTAL_BUDGET', f'Total {self.total_steps}-step budget exhausted')
            if not self.off_confirmed:
                self._transition('STOP_UNCONFIRMED')
            raise CaptureRequestError('TOTAL_BUDGET', f'Total {self.total_steps}-step budget exhausted')
        if self.close_boundary is not None:
            if exhausted(self.step-self.close_boundary['physics_step'], CLOSE_STEPS) or now-self.close_boundary['wall_time'] >= CLOSE_WALL_SECONDS:
                self.fail('CLOSE_TIMEOUT', 'OFF could not be confirmed within its independent budget')
                self._transition('STOP_UNCONFIRMED')
                raise CaptureRequestError('CLOSE_TIMEOUT', 'OFF could not be confirmed within its independent budget')
        elif self.capture_boundary is not None:
            if exhausted(self.step-self.capture_boundary['physics_step'], CAPTURE_STEPS) or now-self.capture_boundary['wall_time'] >= CAPTURE_WALL_SECONDS:
                self._reject('CAPTURE_TIMEOUT', 'No completed acquisition within its independent budget')
        elif self.state == 'MOVING_OFF' and exhausted(self.step, self.pose_steps):
            self._reject('POSE_TIMEOUT', f'Arrival was not established within {self.pose_steps} steps')

    def summary(self):
        from copy import deepcopy
        return deepcopy({'state': self.state, **self.ids, 'render_product_path': self.product_path,
                         'execution_profile': self.execution_profile,
                         'pose_steps_limit': self.pose_steps, 'total_steps_limit': self.total_steps,
                         'completed_physics_steps': self.step, 'controlled_simulation_time_s': self.controlled_time_s,
                         'arrival': self.arrival, 'capture_boundary': self.capture_boundary, 'close_boundary': self.close_boundary,
                         'capture_steps': 0 if self.capture_boundary is None else (self.close_boundary or {'physics_step': self.step})['physics_step']-self.capture_boundary['physics_step'],
                         'close_steps': 0 if self.close_boundary is None else self.step-self.close_boundary['physics_step'],
                         'acquired': self.acquired, 'artifact_saved': self.artifact_saved, 'off_confirmed': self.off_confirmed,
                         'delivery_policy': self.delivery_policy, 'custody_held': self._custody_valid(),
                         'cancel_requested': self.cancel_requested,
                         'frame': self.frame, 'artifact_path': self.artifact_path, 'artifact_error': self.artifact_error,
                         'failure': self.failure, 'close_evidence': self.close_evidence, 'transitions': self.transitions})
