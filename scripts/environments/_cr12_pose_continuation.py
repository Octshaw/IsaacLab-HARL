"""Fixed two-view targets and an explicit, zero-step controller handoff.

CPU math only. The one pose generator retains the controller, command integrator,
trust anchor and global clock. This context changes only the request reference.
"""
from __future__ import annotations

import copy
import math
import numpy as np
import _cr12_pose_control as pc

PROFILE = 'two_view_local_return_v1'


class FrozenPoseSegment:
    """Original four-second quintic translation and shortest rotation geodesic."""
    def __init__(self, actual_start, frozen_target):
        self._initial = pc._transform(actual_start)
        self._target = pc._transform(frozen_target)
        relative = np.eye(4)
        relative[:3, :3] = self._target[:3, :3] @ self._initial[:3, :3].T
        _, quaternion = pc.pose_to_wxyz(relative)
        sine = float(np.linalg.norm(quaternion[1:]))
        self._angle = 2 * math.atan2(sine, max(0., float(quaternion[0])))
        self._axis = quaternion[1:] / sine if sine > 1e-15 else np.array([1., 0., 0.])
        self._initial.setflags(write=False)
        self._target.setflags(write=False)

    @property
    def initial(self):
        return self._initial.copy()

    @property
    def target(self):
        return self._target.copy()

    def reference(self, time):
        u = min(pc._time(time) / pc.REFERENCE_SECONDS, 1.)
        h = 10*u**3 - 15*u**4 + 6*u**5
        result = self._initial.copy()
        result[:3, 3] += h * (self._target[:3, 3] - self._initial[:3, 3])
        result[:3, :3] = pc.rotation_axis_angle(self._axis, h*self._angle) @ self._initial[:3, :3]
        return result


class TwoViewPoseContinuation:
    """Exactly two immutable targets and at most one admitted handoff."""
    def __init__(self, initial_scanner):
        self._initial = pc._transform(initial_scanner)
        first = pc.FrozenPoseTarget(self._initial)
        self._targets = (first.target, self._initial.copy())
        for matrix in (self._initial, *self._targets):
            matrix.setflags(write=False)
        self.goal_index = 1
        self.goal_start_step = 0
        self.goal_start_physics_time = None
        self.last_step = 0
        self._latest = None
        self._pending = None
        self._handoff = None
        self._control = None
        self.failure = None

    @property
    def goal_id(self):
        return f'goal_{self.goal_index}'

    def fail(self, category, message):
        if self.failure is None:
            self.failure = {'category': str(category), 'message': str(message), 'global_step': self.last_step}

    def _reject(self, message):
        self.fail('CONTINUATION', message)
        raise pc.PoseCheckError('CONTINUATION', message)

    def _healthy(self):
        if self.failure is not None:
            raise pc.PoseCheckError(self.failure['category'], self.failure['message'])

    def initial_target(self, actual_initial_scanner):
        self._healthy()
        if not np.array_equal(pc._transform(actual_initial_scanner), self._initial):
            self._reject('Targets were not frozen from this actual initialized scanner')
        return pc.FrozenPoseTarget(self._initial)

    def bind_control(self, controller, integrator, physics_time):
        self._healthy()
        if self._control is not None or integrator.generation != 0:
            self._reject('Continuation control can be bound only once before motion')
        self.goal_start_physics_time = pc._time(physics_time)
        self._control = {'controller_object_id': id(controller), 'integrator_object_id': id(integrator),
                         'trust_initial_q_rad': integrator.initial_q.tolist(), 'bind_count': 1}

    def observe_yield(self, tick):
        """Remember a guarded post-step boundary; never advance the simulator."""
        self._healthy()
        if self._control is None or tick['step'] != self.last_step + 1:
            self._reject('Nonconsecutive continuation boundary')
        self.last_step = int(tick['step'])
        self._latest = {key: copy.deepcopy(tick[key]) for key in
                        ('step', 'physics_time_s', 'controlled_time_s', 'scanner', 'q', 'dq',
                         'q_cmd', 'dq_cmd', 'rendered', 'pose_reached', 'local_step', 'local_time_s')}
        self._latest['render_count'] = int(tick['render_count'])

    def queue_goal_2(self, last_tick, *, completed_request):
        """Admit the second request without consuming a tick or resetting state."""
        self._healthy()
        if self.goal_index != 1 or self._pending is not None or self._handoff is not None or self._latest is None:
            self._reject('Only one goal_1 to goal_2 transition is permitted')
        required = ('acquired', 'artifact_saved', 'off_confirmed')
        if (completed_request.get('state') != 'SUCCEEDED_OFF' or completed_request.get('goal_id') != 'goal_1'
                or any(completed_request.get(key) is not True for key in required)
                or completed_request.get('failure') is not None or last_tick.get('pose_reached') is not True):
            self._reject('Goal_2 requires goal_1 arrival, independent data, saved artifact and confirmed OFF without failure')
        for key, expected in self._latest.items():
            value = last_tick.get(key)
            if not np.array_equal(value, expected):
                self._reject(f'Handoff must use the latest actual post-step boundary: {key}')
        self._pending = copy.deepcopy(self._latest)
        self._handoff = {key: value.tolist() if isinstance(value, np.ndarray) else copy.deepcopy(value)
                         for key, value in self._pending.items()}
        self._handoff.update(next_goal_id='goal_2', submitted_after_request=copy.deepcopy(completed_request),
                             activation_count=0, reference_start_world_matrix=self._pending['scanner'].tolist())
        return copy.deepcopy(self._handoff)

    def activate_pending(self, *, global_step, physics_time, actual_scanner, q, dq, controller, integrator):
        """Called by the SAME generator immediately before its next command."""
        self._healthy()
        if self._pending is None:
            return None
        pending = self._pending
        if (global_step != pending['step'] or physics_time != pending['physics_time_s']
                or id(controller) != self._control['controller_object_id']
                or id(integrator) != self._control['integrator_object_id']
                or integrator.generation != global_step
                or not np.array_equal(integrator.initial_q, self._control['trust_initial_q_rad'])):
            self._reject('Handoff changed the clock, controller, integrator or original trust anchor')
        for actual, expected in ((actual_scanner, pending['scanner']), (q, pending['q']), (dq, pending['dq']),
                                 (integrator.previous, pending['q_cmd'])):
            if not np.array_equal(actual, expected):
                self._reject('Actual state or previously submitted command changed at the handoff')
        integrator.check_actual(q, dq)
        target = FrozenPoseSegment(actual_scanner, self._targets[1])
        self.goal_index = 2
        self.goal_start_step = global_step
        self.goal_start_physics_time = physics_time
        self._handoff.update(activation_count=1, activation_global_step=global_step,
                             activation_physics_time_s=physics_time, controller_object_id=id(controller),
                             integrator_object_id=id(integrator), integrator_generation=integrator.generation,
                             command_unchanged=True, actual_state_unchanged=True, clock_unchanged=True)
        self._pending = None
        return target

    def record(self):
        targets = []
        for index, matrix in enumerate(self._targets, 1):
            position, quaternion = pc.pose_to_wxyz(matrix)
            targets.append({'goal_id': f'goal_{index}', 'matrix': matrix.tolist(),
                            'position_m': position.tolist(), 'quaternion_wxyz': quaternion.tolist()})
        distance, angle = pc.pose_error(*self._targets)
        return copy.deepcopy({'profile': PROFILE, 'targets': targets, 'initial_scanner': self._initial.tolist(),
                              'target_distance_m': distance, 'target_angle_rad': angle,
                              'active_goal_id': self.goal_id, 'goal_start_step': self.goal_start_step,
                              'goal_start_physics_time_s': self.goal_start_physics_time,
                              'last_global_step': self.last_step, 'control': self._control,
                              'handoff': self._handoff, 'pending': self._pending is not None, 'failure': self.failure})
