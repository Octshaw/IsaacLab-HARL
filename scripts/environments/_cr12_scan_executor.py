"""One CR12 feedback implementation; the owner supplies every step and render.

No simulator imports occur at module import. A session owns control memory, but
never advances physics, renders, resets state, creates a scene or owns a camera.
"""
from __future__ import annotations

import copy
import csv
from pathlib import Path
from functools import wraps
import numpy as np
import _cr12_pose_control as pc
from _cr12_runtime_support import (
    _assert_active, _body_poses, _capture_submitted_targets, _check_contacts,
    _check_frames, _check_geometry, _clock, _contact_summary, check_clock,
)

class PoseTrace:
    """One flushed compact CSV, including a failing post-step sample."""

    VECTOR_FIELDS = ('actual_p', 'actual_qwxyz', 'reference_p', 'reference_qwxyz',
                     'target_p', 'target_qwxyz', 'q', 'dq', 'q_cmd', 'dq_cmd')
    LENGTHS = (3, 4, 3, 4, 3, 4, 6, 6, 6, 6)
    GUARDS = ('clock', 'joint', 'contact', 'geometry', 'frame', 'render_clock')

    def __init__(self, path):
        fields = ['step', 'physics_time_s', 'controlled_time_s', 'reference_time_s', 'phase',
                  'target_position_error_m', 'target_orientation_error_rad',
                  'reference_position_error_m', 'reference_orientation_error_rad',
                  'max_raw_dls_update_rad', 'stable_samples', 'stable_span_s', 'status', 'failure']
        for name, length in zip(self.VECTOR_FIELDS, self.LENGTHS):
            fields.extend(f'{name}_{i}' for i in range(length))
        fields.extend('guard_' + name for name in self.GUARDS)
        self.stream = Path(path).open('x', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.stream, fieldnames=fields)
        self.writer.writeheader()
        self.stream.flush()
        self.count = 0

    def append(self, sample):
        row = dict(sample)
        for name, length in zip(self.VECTOR_FIELDS, self.LENGTHS):
            values = row.pop(name, [])
            if hasattr(values, 'tolist'):
                values = values.tolist()
            for i in range(length):
                row[f'{name}_{i}'] = values[i] if i < len(values) else ''
        self.writer.writerow(row)
        self.stream.flush()
        self.count += 1

    def close(self):
        self.stream.close()


def _native_state(robot, joint_ids):
    """Independent snapshots of generalized PhysX q/dq, in arm-name order."""
    import torch
    from _cr12_pose_control import PoseCheckError

    q = robot.root_physx_view.get_dof_positions().clone()
    dq = robot.root_physx_view.get_dof_velocities().clone()
    if q.shape != (1, 6) or dq.shape != (1, 6) or q.dtype != torch.float32 or dq.dtype != torch.float32:
        raise PoseCheckError('SETUP', 'Unexpected native generalized state shape/dtype')
    if q.device != torch.device('cuda:0') or dq.device != q.device:
        raise PoseCheckError('SETUP', 'Native generalized state is not on cuda:0')
    ids = torch.tensor(joint_ids, dtype=torch.long, device=q.device)
    return q.index_select(1, ids), dq.index_select(1, ids)


def _native_jacobian(robot, mapping):
    import torch
    import _cr12_pose_control as pc

    raw = robot.root_physx_view.get_jacobians().clone()
    if raw.dtype != torch.float32 or raw.device != torch.device('cuda:0'):
        raise pc.PoseCheckError('SETUP_JACOBIAN_SEMANTICS', 'Expected independent float32 cuda:0 Jacobian snapshot')
    cpu = raw.detach().cpu().numpy()
    return pc.extract_jacobian(cpu, mapping), {'shape': list(raw.shape), 'dtype': str(raw.dtype), 'device': str(raw.device)}


def _pose_record(transform):
    import _cr12_pose_control as pc
    p, q = pc.pose_to_wxyz(transform)
    return {'position_m': p.tolist(), 'quaternion_wxyz': q.tolist(), 'matrix': transform.tolist()}


def _checked_tick_guard(sample, totals, name, callback):
    sample['guard_' + name] = 'STARTED'
    try:
        value = callback()
    except BaseException:
        sample['guard_' + name] = 'FAIL'
        raise
    sample['guard_' + name] = 'PASS'
    totals[name] += 1
    return value


def finish_sample_trace(trace, sample, recorder, primary_error):
    """A secondary CSV error must not hide the first physical/control failure."""
    try:
        trace.append(sample)
    except BaseException as exc:
        if primary_error is None:
            raise
        recorder.secondary(exc, 'trace_after_primary_failure')

def manual_motion_outcome(category=None):
    """Manual result labels cannot replace or extend formal acceptance."""
    if category is None:
        return 'MANUAL_VISUAL_MOTION_COMPLETED'
    if category == 'TIMEOUT':
        return 'MANUAL_VISUAL_MOTION_TIMEOUT'
    if category in ('NO_PROGRESS', 'DIVERGENCE', 'PHYSICS_GUARD', 'COMMAND_REJECTED'):
        return 'MANUAL_VISUAL_MOTION_GUARD_FAIL'
    return 'MANUAL_VISUAL_RUNTIME_FAIL'


def _fail_closed(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except BaseException as exc:
            self.abort(exc)
            raise
    return guarded


class Cr12PoseControlSession:
    """Nonblocking command/readback phases around one externally owned tick."""

    def __init__(self, args, app, recorder, resources, expected, *, scene, initial,
                 integration=False, continuation=None, continue_after_arrival=True,
                 allow_unbound_hold=False, set_view=True, shared_robot_id=None):
        from isaaclab.controllers import DifferentialIKController, DifferentialIKControllerCfg
        from _cr12_external_forces import read_scene_external_forces
        from _cr12_pose_visuals import set_spectator_view

        self.args, self.app, self.recorder = args, app, recorder
        self.resources, self.expected = resources, expected
        self.scene, self.initial = scene, initial
        self.integration, self.continuation = bool(integration), continuation
        self.shared_robot_id = shared_robot_id
        if shared_robot_id is not None:
            from _cr12_shared_task_profile import PROFILE_NAME
            if (type(shared_robot_id) is not int or shared_robot_id not in (0, 1)
                    or not integration or not allow_unbound_hold or args.motion_profile != PROFILE_NAME):
                raise pc.PoseCheckError('SETUP', 'Shared execution requires the explicit two-robot profile')
        elif args.motion_profile == 'shared_m2n1':
            raise pc.PoseCheckError('SETUP', 'Shared profile requires a fixed robot identity')
        self.continue_after_arrival = bool(continue_after_arrival)
        if allow_unbound_hold and not integration:
            raise pc.PoseCheckError('SETUP', 'Unbound hold requires the private lifecycle session')
        self.allow_unbound_hold = bool(allow_unbound_hold)
        self._idle_hold = self.allow_unbound_hold
        if integration and (continuation is not None or not continue_after_arrival
                            or args.motion_profile != ('formal' if shared_robot_id is None else 'shared_m2n1')):
            raise pc.PoseCheckError('SETUP', 'Lifecycle session requires formal continuation without a two-view context')
        self.index = 0
        self._phase = 'ready'
        self.failure = None
        self._sample_written = True
        self._latest_tick = None
        self._goal_ids = set()
        self.goal_id = None
        self.goal_index = 0
        self.goal_start_step = 0
        self.segment_start_step = 0
        self.control_segment_id = None
        self.control_segment_kind = None
        self._setup_phase = 'SETUP_PENDING' if self.shared else None
        self._setup_stable_count = 0
        self._setup_stable_start = None
        self._setup_stable_now = False
        self._goal_submitted = not integration
        self.profile = pc.select_motion_profile(self.args.motion_profile)
        if self.continue_after_arrival and self.profile.manual_visual_only:
            raise pc.PoseCheckError('SETUP', 'Capture continuation requires the formal pose profile')
        if self.continuation is not None and (not self.continue_after_arrival or self.profile.manual_visual_only):
            raise pc.PoseCheckError('SETUP', 'Two-view context requires the explicit formal continuation path')
        if (self.scene is None) != (self.initial is None):
            raise pc.PoseCheckError('SETUP', 'Supply scene and initial together')
        if self.scene is None:
            raise pc.PoseCheckError('SETUP', 'Pose session requires an initialized scene')
        (self.sim, self.robot, self.info, self.stage) = (self.scene[k] for k in ('sim', 'robot', 'info', 'stage'))
        (self.contacts, self.frames) = (self.scene['contacts'], self.scene['frames'])
        (self.body_ids, self.joint_ids) = (self.scene['body_ids'], self.scene['joint_ids'])
        self.config = self.scene['configuration']
        (self.baseline, self.initial_root) = (self.initial['baseline'], self.initial['initial_root'])
        self.recorder.phase = 'pose_setup'
        self.mapping = pc.resolve_mapping(self.robot.body_names, self.robot.joint_names, self.robot.is_fixed_base)
        if list(self.mapping['joint_ids']) != list(self.joint_ids) or list(self.mapping['body_ids']) != list(self.body_ids):
            raise pc.PoseCheckError('SETUP_JACOBIAN_SEMANTICS', 'Shared/native name maps differ')
        (self.q_tensor, self.dq_tensor) = _native_state(self.robot, self.joint_ids)
        (self.q, self.dq) = (self.q_tensor[0].cpu().numpy().copy(), self.dq_tensor[0].cpu().numpy().copy())
        self.poses = _body_poses(self.robot, self.body_ids)
        _check_frames(self.stage, self.info, self.frames, self.poses, self.initial_root)
        for (name, wanted) in (('tool', np.eye(4)), ('scanner', pc.scanner_from_ee(np.eye(4)))):
            if not np.allclose(self.frames[name], wanted, rtol=0, atol=1e-05):
                raise pc.PoseCheckError('SETUP', f'Unexpected fixed {name} transform', actual=self.frames[name].tolist())
        self.model = pc.KinematicModel.from_derived_urdf(self.args.usd_path.parent.parent / 'cr12_fixed_lift0.urdf')
        self.limits = np.asarray(self.recorder.result['physx_readback']['joints']['position_limits'])
        self.com = np.asarray(self.recorder.result['physx_readback']['bodies']['link_6']['com_body'])
        anchor = self.q
        if self.shared:
            from _cr12_shared_task_profile import initial_q
            anchor = initial_q(self.shared_robot_id)
            if not np.allclose(self.q, anchor, rtol=0, atol=1e-6):
                raise pc.PoseCheckError('SETUP', 'Shared native initial q differs from frozen initial state')
        self.controller_ref = pc.CommandIntegrator(anchor, self.limits,
            **({'profile': self.profile} if self.shared else {}))
        self.controller_ref.propose(self.q, self.dq, self.q)
        self.initial_scanner = pc.scanner_from_ee(self.poses['link_6'])
        self.target = pc.FrozenManualPoseTarget(self.initial_scanner, self.poses['agv'], self.model) if self.profile.manual_visual_only else pc.FrozenPoseTarget(self.initial_scanner)
        if self._idle_hold:
            from _cr12_pose_continuation import FrozenPoseSegment
            self.target = FrozenPoseSegment(self.initial_scanner, self.initial_scanner)
        if self.shared:
            from _cr12_shared_task_profile import segment, scanner_target
            self.target = segment(self.model, self.shared_robot_id, 'park')
            self.scanner_task_target = scanner_target()
            self.cleanup_target = self.target.target.copy()
        if self.continuation is not None:
            self.target = self.continuation.initial_target(self.initial_scanner)
            self.recorder.result['pose_continuation'] = self.continuation.record()
        self.recorder.result['frozen_poses'] = {'initial_scanner': _pose_record(self.target.initial), 'target_scanner': _pose_record(self.target.target), 'initial_root': _pose_record(self.poses['agv']), 'T_ES': _pose_record(pc.scanner_from_ee(np.eye(4)))}
        before_j = _clock(self.sim)
        (self.native_j, self.native_meta) = _native_jacobian(self.robot, self.mapping)
        if self.profile.manual_visual_only:
            self.adapter = {'reference_point': 'com'}
            self.jac_record = {'native': self.native_meta, 'mapping': self.mapping, 'clock_before': list(before_j), 'clock_after': list(_clock(self.sim)), 'extra_refresh_steps': 0, 'reference_point': 'com', 'runtime_shape_checks_passed': True, 'semantic_recheck_performed': False, 'adapter_source': 'accepted formal 20260930_cr12_pose_target/attempt_01'}
            self.recorder.result['jacobian_adapter'] = self.jac_record
            self.recorder.result['manual_target'] = {'witness_deg': list(self.profile.witness_deg), 'beta': self.profile.beta, 'construction': 'actual_initial_root * model_FK(witness) * T_ES', 'translation_m': pc.pose_error(self.target.initial, self.target.target)[0], 'shortest_rotation_rad': pc.pose_error(self.target.initial, self.target.target)[1]}
        else:
            (je, jc) = self.model.jacobians(self.q, self.poses['agv'], self.com)
            self.jac_record = {'native': self.native_meta, 'mapping': self.mapping, 'clock_before': list(before_j), 'clock_after': list(_clock(self.sim)), 'extra_refresh_steps': 0, 'native_matrix': self.native_j.tolist(), 'analytical_E': je.tolist(), 'analytical_COM': jc.tolist(), 'passed': False}
            self.recorder.result['jacobian_check'] = self.jac_record
            try:
                self.adapter = pc.select_jacobian_adapter(self.native_j, je, jc)
            except pc.PoseCheckError as exc:
                self.jac_record['failure_details'] = exc.details
                try:
                    self.recorder.save()
                except BaseException as io_error:
                    self.recorder.secondary(io_error, 'jacobian_failure_recording')
                raise
            self.jac_record.update(self.adapter)
        if _clock(self.sim) != before_j or before_j != self.baseline:
            raise pc.PoseCheckError('SETUP_JACOBIAN_SEMANTICS', 'Physics advanced during first Jacobian checks')
        if not self.profile.manual_visual_only:
            self.jac_record['passed'] = True
        self.recorder.result['initialization']['jacobian_extra_steps'] = 0
        self.recorder.emit('jacobian_adapter_inherited' if self.profile.manual_visual_only else 'jacobian_semantics_passed', **self.jac_record)
        self.visuals = None
        self.recorder.result['visual_errors'] = []
        try:
            if self.args.visual_debug_pose:
                from _cr12_pose_visuals import PoseDebugVisuals
                self.visuals = PoseDebugVisuals(self.stage, self.initial_scanner, self.args.view_preset, target_scanner_pose=self.target.target)
                self.recorder.result['visual_metadata'] = self.visuals.metadata
                self.recorder.result['spectator'] = self.visuals.metadata['view']
                self.recorder.result['visual_setup_completed'] = True
                self.recorder.result['visual_update_count'] = 1
            elif set_view:
                self.recorder.result['spectator'] = set_spectator_view(self.initial_scanner, self.args.view_preset, target_scanner_pose=self.target.target)
        except Exception as exc:
            self.recorder.result['visual_errors'].append(f'{type(exc).__name__}: {exc}')
            if self.visuals is not None:
                try:
                    self.visuals.set_visibility(False)
                except Exception as hide_error:
                    self.recorder.result['visual_errors'].append(f'hide: {hide_error}')
            self.visuals = None
        if _clock(self.sim) != self.baseline:
            raise pc.PoseCheckError('SETUP', 'Visual setup advanced physics')
        self.controller = DifferentialIKController(DifferentialIKControllerCfg(command_type='pose', use_relative_mode=False, ik_method='dls', ik_params={'lambda_val': 0.01}), num_envs=1, device=self.robot.device)
        if self.continuation is not None:
            self.continuation.bind_control(self.controller, self.controller_ref, self.baseline[1])
            self.recorder.result['pose_continuation'] = self.continuation.record()
        self.monitor = pc.PoseMonitor(self.profile)
        self.trace = self.resources['trace']
        self.counts = {name: 0 for name in PoseTrace.GUARDS}
        self.stats = {'guard_pass_counts': self.counts, 'submitted_target_checks': 0, 'sanity_checks': 0, 'render_calls': 0, 'maximum_forbidden_contact_n': 0.0, 'maximum_root_translation_m': 0.0, 'maximum_root_rotation_rad': 0.0, 'minimum_arm_collision_z_m': self.initial['initial_minimum_z'], 'q_min_rad': self.q.tolist(), 'q_max_rad': self.q.tolist(), 'max_abs_dq_rad_s': np.abs(self.dq).tolist(), 'max_raw_dls_update_rad': 0.0, 'max_command_step_rad': 0.0, 'stable_samples': 0, 'stable_span_s': 0.0, 'all_guards_passed': False}
        self.recorder.result['pose_summary'] = self.stats
        self.recorder.result['control'] = {'command_type': 'pose', 'use_relative_mode': False, 'ik_method': 'dls', 'lambda_val': 0.01, 'integrator_gain_per_s': 2.0, 'alpha': 1 / 60, 'trajectory_seconds': self.profile.reference_seconds, 'maximum_seconds': self.profile.max_seconds, 'maximum_steps': self.profile.max_steps, 'joint_state_source': 'native PhysX get_dof_positions/get_dof_velocities clone', 'actual_scanner_source': 'actual body_link pose link_6 composed with fixed T_ES'}
        read_scene_external_forces(self.stage, self.scene['setup'], 'before_motion', self.scene['physx_schema'], self.scene['usd_physics'], self.scene['default_time'])
        self.recorder.save()
        self.recorder.emit('physics_ready', body_count=7, dof_count=6, initial_physics_clock=list(self.baseline))
        self.recorder.phase = 'controlled_pose'
        self.goal_start_physics_time = self.baseline[1]
        self.segment_start_physics_time = self.baseline[1]
        self.actual_scanner = self.initial_scanner.copy()
        self.controlled_time = 0.0
        self._clock_boundary = self.baseline
        self.submitted_q = self.controller_ref.previous.tolist()
        self.submitted_dq = np.zeros(6, dtype=np.float32).tolist()

    def tensor(self, value):
        import torch
        return torch.tensor(np.array(value, copy=True), dtype=torch.float32,
                               device=self.robot.device).unsqueeze(0)

    def _require(self, phase):
        if self.failure is not None:
            raise pc.PoseCheckError(self.failure['category'], self.failure['message'])
        if self._phase != phase:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL',
                                    f'Expected {phase}, found {self._phase}')

    @property
    def render_due(self):
        return (self.index + 1) % 2 == 0

    @property
    def phase(self):
        return self._phase

    def abort(self, exc):
        """Latch failure and preserve a post-step row; never advance or clean up."""
        if self.failure is None:
            self.failure = {'category': getattr(exc, 'category', 'INFRASTRUCTURE'),
                            'message': str(exc), 'step': self.index + 1}
            if self.shared:
                self.failure.update(details=copy.deepcopy(getattr(exc, 'details', {})),
                    observed_physics_steps=self.recorder.result.get('completed_physics_steps', self.index),
                    q=np.asarray(self.q).tolist(), dq=np.asarray(self.dq).tolist(),
                    q_cmd=list(self.submitted_q), dq_cmd=list(self.submitted_dq),
                    control_segment_id=self.control_segment_id)
                self.recorder.result.setdefault('shared_execution', {})['failure'] = copy.deepcopy(self.failure)
        if self.continuation is not None:
            self.continuation.fail(getattr(exc, 'category', 'INFRASTRUCTURE'), str(exc))
            self.recorder.result['pose_continuation'] = self.continuation.record()
        if not self._sample_written:
            self.sample.update(status='FAIL',
                               failure=f'{getattr(exc, "category", type(exc).__name__)}: {exc}',
                               stable_samples=0, stable_span_s=0.0)
            try:
                self.monitor.fail(getattr(exc, 'category', 'PHYSICS_GUARD'), str(exc))
            except pc.PoseCheckError:
                pass
            self.stats.update(stable_samples=0, stable_span_s=0.0, all_guards_passed=False)
            self._sample_written = True
            finish_sample_trace(self.trace, self.sample, self.recorder, exc)
        self._phase = 'failed'

    def current_state(self):
        """Last guarded boundary, copied; usable before the first goal submission."""
        return {'step': self.index, 'physics_time_s': self._clock_boundary[1],
                'controlled_time_s': self.controlled_time, 'q': self.q.copy(),
                'dq': self.dq.copy(), 'poses': {k: v.copy() for k, v in self.poses.items()},
                'scanner': self.actual_scanner.copy(), 'target': self.target.target.copy(),
                'q_cmd': list(self.submitted_q), 'dq_cmd': list(self.submitted_dq),
                'render_count': self.stats['render_calls'], 'pose_reached': self.monitor.reached,
                'goal_id': self.goal_id, 'goal_index': self.goal_index,
                'local_step': self.index - self.goal_start_step,
                'local_time_s': self._clock_boundary[1] - self.goal_start_physics_time,
                **self._shared_tick_fields(self.index, self._clock_boundary[1])}

    @property
    def shared(self):
        return getattr(self, 'shared_robot_id', None) is not None

    @property
    def setup_hold_ready(self):
        return bool(self.shared and self._setup_phase in ('SETUP_SETTLING', 'SETUP_HOLD_READY')
                    and self._setup_stable_now and self._setup_stable_count >= 121
                    and self._setup_stable_start is not None
                    and self._clock_boundary[1] - self._setup_stable_start >= 1.0 - 1e-6)

    def _shared_tick_fields(self, step, clock):
        if not self.shared:
            return {}
        setup_span = (getattr(self, '_setup_completed_span', 0.) if self._setup_phase == 'COMPLETE'
                      else (0. if self._setup_stable_start is None else clock-self._setup_stable_start))
        return {'execution_phase': self._setup_phase if self._setup_phase != 'COMPLETE' else
                    ('IDLE_HOLD' if self.idle_hold else self.control_segment_kind),
                'setup_stable_now': self._setup_stable_now, 'setup_hold_ready': self.setup_hold_ready,
                'setup_stable_samples': self._setup_stable_count,
                'setup_stable_span_s': setup_span,
                'setup_hold_completed': self._setup_phase == 'COMPLETE',
                'control_segment_id': self.control_segment_id,
                'control_segment_kind': self.control_segment_kind,
                'segment_step': step-self.segment_start_step,
                'segment_time_s': clock-self.segment_start_physics_time,
                'scanner_task_target': self.scanner_task_target.copy(),
                'cleanup_target': self.cleanup_target.copy(),
                'actual_tube': copy.deepcopy(getattr(self, '_actual_tube', None))}

    def _shared_actual_guard(self):
        if not self.shared:
            return None
        from _cr12_shared_task_profile import initial_q, goal_q
        park = initial_q(self.shared_robot_id)
        if (self._setup_phase != 'COMPLETE' or self.idle_hold
                or (self.control_segment_kind == 'retreat' and self.monitor.reached)):
            # B may retire at the task target; only A is required to park after retreat.
            if self.idle_hold and self.control_segment_kind == 'approach' and self.monitor.reached:
                result = pc.check_path_tube(self.q, park, goal_q(self.shared_robot_id))
            else:
                result = pc.check_fixed_neighborhood(self.q, park)
        else:
            result = pc.check_path_tube(self.q, park, goal_q(self.shared_robot_id))
        self._actual_tube = result
        record = self.recorder.result.setdefault('shared_execution', {})
        record['latest_actual_tube'] = copy.deepcopy(result)
        record['actual_tube_check_count'] = record.get('actual_tube_check_count', 0) + 1
        record['maximum_actual_tube_residual_rad'] = max(record.get('maximum_actual_tube_residual_rad', 0.),
            result['maximum_residual_rad'])
        return result

    @_fail_closed
    def begin_setup_hold(self):
        self._require('ready')
        if not self.shared or self._setup_phase != 'SETUP_PENDING' or self.index != 0 or self.goal_id is not None:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Setup hold starts once before any claim')
        self._validate_latest_boundary(self.current_state())
        self._setup_phase = 'SETUP_SETTLING'
        self.control_segment_kind = 'park'
        self.control_segment_id = f'setup_robot_{self.shared_robot_id}'
        self._shared_actual_guard()
        self.recorder.result.setdefault('shared_execution', {}).update(robot_id=self.shared_robot_id,
            setup_phase=self._setup_phase, setup_start_step=self.index,
            original_trust_anchor_rad=self.controller_ref.initial_q.tolist(),
            actual_joint_drive_effort='NOT_COLLECTED; no torque estimate substituted')
        return self.current_state()

    @_fail_closed
    def complete_setup_hold(self):
        self._require('ready')
        if not self.setup_hold_ready:
            raise pc.PoseCheckError('SETUP_HOLD_FAIL', 'Setup has no current consecutive stable window')
        self._validate_latest_boundary(self.current_state())
        self._shared_actual_guard()
        from _cr12_single_view_capture import check_arrived_hold
        check_arrived_hold(*pc.pose_error(self.actual_scanner, self.target.target), self.dq)
        evidence = self.current_state()
        self._setup_completed_span = evidence['setup_stable_span_s']
        self._setup_phase = 'COMPLETE'
        self.recorder.result['shared_execution'].update(setup_phase='COMPLETE',
            setup_completed_step=self.index, setup_stable_samples=self._setup_stable_count,
            setup_stable_span_s=evidence['setup_stable_span_s'])
        return evidence

    def _validate_latest_boundary(self, boundary):
        state = self.current_state()
        if boundary is None:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Shared segment requires latest actual boundary')
        for key in ('step', 'physics_time_s', 'q', 'dq', 'scanner', 'q_cmd', 'dq_cmd'):
            if key not in boundary or not np.array_equal(boundary[key], state[key]):
                raise pc.PoseCheckError('EXECUTOR_PROTOCOL', f'Segment boundary is stale: {key}')
        if _clock(self.sim) != (self.baseline[0] + self.index, state['physics_time_s']):
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Segment boundary clock changed')
        return state

    @_fail_closed
    def submit_bound_segment(self, kind='retreat', latest_actual_boundary=None):
        self._require('ready')
        if (not self.shared or self.shared_robot_id != 0 or kind != 'retreat'
                or self._setup_phase != 'COMPLETE' or not self._goal_submitted
                or self.control_segment_kind != 'approach' or not self.monitor.reached):
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Only the arrived, still-bound A goal may retreat')
        state = self._validate_latest_boundary(latest_actual_boundary)
        from _cr12_single_view_capture import check_arrived_hold
        check_arrived_hold(*pc.pose_error(self.actual_scanner, self.target.target), self.dq)
        from _cr12_shared_task_profile import segment
        self.target = segment(self.model, self.shared_robot_id, kind)
        self.monitor = pc.PoseMonitor(self.profile)
        self.control_segment_kind = kind
        self.control_segment_id = self.goal_id + ':retreat'
        self.segment_start_step = self.index
        self.segment_start_physics_time = state['physics_time_s']
        self.stats.update(stable_samples=0, stable_span_s=0., stable_count=0, outcome='RUNNING')
        self.recorder.result['pose_outcome'] = 'RUNNING'
        record = {'control_segment_id': self.control_segment_id, 'kind': kind,
            'goal_id': self.goal_id, 'global_step': self.index, 'physics_time_s': state['physics_time_s'],
            'actual_scanner': _pose_record(self.actual_scanner),
            'reference_start': _pose_record(self.target.initial),
            'first_reference_error': list(pc.pose_error(self.actual_scanner, self.target.initial)),
            'first_submitted_reference_error': list(pc.pose_error(self.actual_scanner, self.target.reference(pc.DT))),
            'scanner_task_target': _pose_record(self.scanner_task_target),
            'cleanup_target': _pose_record(self.cleanup_target),
            'q_cmd': list(self.submitted_q), 'dq_cmd': list(self.submitted_dq),
            'controller_object_id': id(self.controller), 'integrator_object_id': id(self.controller_ref),
            'integrator_generation': self.controller_ref.generation,
            'trust_initial_q_rad': self.controller_ref.initial_q.tolist()}
        self.recorder.result.setdefault('bound_segments', []).append(record)
        self.recorder.emit('bound_segment_activated', **record)
        return copy.deepcopy(record)

    @property
    def idle_hold(self):
        return bool(getattr(self, '_idle_hold', False))

    @_fail_closed
    def enter_idle_hold(self):
        """Retain the last frozen target and integrator; never chase actual state."""
        self._require('ready')
        if not self.integration or not self.allow_unbound_hold:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'This session does not admit unbound hold')
        if self.shared and (self._setup_phase != 'COMPLETE'
                or (self.shared_robot_id == 0 and self.control_segment_kind != 'retreat')):
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Shared A can retire only after bound retreat')
        if self._goal_submitted and not self.monitor.reached:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Unbound hold requires arrived retirement')
        from _cr12_single_view_capture import check_arrived_hold
        ep, er = pc.pose_error(self.actual_scanner, self.target.target)
        check_arrived_hold(ep, er, self.dq)
        self._idle_hold = True
        self._goal_submitted = False
        self.recorder.emit('unbound_hold_entered', global_step=self.index, previous_goal=self.goal_id,
                           frozen_target=_pose_record(self.target.target), q_cmd=list(self.submitted_q))
        self.goal_id = None
        self._shared_actual_guard()

    @_fail_closed
    def submit_goal(self, goal_id, target, latest_actual_boundary=None):
        """At a guarded boundary, change only reference/monitor and local time."""
        from _cr12_pose_continuation import FrozenPoseSegment
        self._require('ready')
        if not self.integration:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Explicit goals require lifecycle mode')
        if self.shared and (self._setup_phase != 'COMPLETE' or self._goal_ids):
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Shared robot requires completed setup and one request')
        if not isinstance(goal_id, str) or not goal_id or goal_id in self._goal_ids:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Each goal needs a new nonempty goal_id')
        if self._goal_submitted and not self.monitor.reached:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'A new goal requires the previous arrived hold')
        state = self.current_state()
        if latest_actual_boundary is not None:
            for key in ('step', 'physics_time_s', 'q', 'dq', 'scanner'):
                if key not in latest_actual_boundary or not np.array_equal(latest_actual_boundary[key], state[key]):
                    raise pc.PoseCheckError('EXECUTOR_PROTOCOL', f'Goal boundary is stale: {key}')
        if _clock(self.sim) != (self.baseline[0] + self.index, state['physics_time_s']):
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Goal submission cannot advance physics')
        if self.shared:
            from _cr12_shared_task_profile import segment, scanner_target
            self._validate_latest_boundary(latest_actual_boundary)
            if not np.array_equal(np.asarray(target), scanner_target()):
                raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Shared task target cannot change with the owner')
            new_target = segment(self.model, self.shared_robot_id, 'approach')
        else:
            new_target = FrozenPoseSegment(self.actual_scanner, target)
        self.target = new_target
        self.monitor = pc.PoseMonitor(self.profile)
        self.goal_id = goal_id
        self.goal_index += 1
        self._goal_ids.add(goal_id)
        self._goal_submitted = True
        self._idle_hold = False
        self.goal_start_step = self.index
        self.goal_start_physics_time = state['physics_time_s']
        if self.shared:
            self.control_segment_kind = 'approach'
            self.control_segment_id = goal_id + ':approach'
            self.segment_start_step = self.index
            self.segment_start_physics_time = state['physics_time_s']
        self.stats.update(stable_samples=0, stable_span_s=0.0, stable_count=0,
                          outcome='RUNNING', goal_id=goal_id)
        for key in ('arrival_step', 'arrival_time_s', 'arrival_local_step', 'arrival_local_time_s'):
            self.stats.pop(key, None)
        self.recorder.result['pose_outcome'] = 'RUNNING'
        record = {'goal_id': goal_id, 'goal_index': self.goal_index,
                  'global_step': self.index, 'physics_time_s': state['physics_time_s'],
                  'reference_start': _pose_record(self.target.initial),
                  'frozen_target': _pose_record(self.target.target),
                  'controller_object_id': id(self.controller),
                  'integrator_object_id': id(self.controller_ref),
                  'integrator_generation': self.controller_ref.generation,
                  'q_cmd': list(self.submitted_q), 'dq_cmd': list(self.submitted_dq),
                  'trust_initial_q_rad': self.controller_ref.initial_q.tolist()}
        if self.shared:
            record.update(control_segment_id=self.control_segment_id,
                          scanner_task_target=_pose_record(self.scanner_task_target))
        self.recorder.result.setdefault('pose_goals', []).append(record)
        self.recorder.emit('pose_goal_activated', **record)
        return copy.deepcopy(record)

    @_fail_closed
    def prepare_tick(self, boundary=None):
        """Compute and validate one proposal without writing targets."""
        self._require('ready')
        if self.shared:
            from _cr12_shared_task_profile import SETUP_MAX_STEPS
            if self._setup_phase == 'SETUP_PENDING':
                raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Begin the shared setup hold before stepping')
            if self._setup_phase != 'COMPLETE' and self.index >= SETUP_MAX_STEPS:
                raise pc.PoseCheckError('SETUP_HOLD_FAIL', 'Shared setup exceeded its controlled budget')
            if (self._setup_phase == 'COMPLETE' and not self.idle_hold and not self.monitor.reached
                    and self.index-self.segment_start_step >= self.profile.max_steps):
                raise pc.PoseCheckError('TIMEOUT', 'Bound physical segment exhausted its fixed budget')
            self._shared_actual_guard()
        if not self._goal_submitted and not self.idle_hold:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Submit a goal before preparing motion')
        if boundary is not None and tuple(boundary) != _clock(self.sim):
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Prepare boundary differs from the actual clock')
        _assert_active(self.app, self.sim)
        self.before = _clock(self.sim)
        if self.before[0] != self.baseline[0] + self.index or abs(self.before[1] - self.baseline[1] - self.index * pc.DT) > 0.0001:
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Physics advanced outside controlled stepping')
        if self.continuation is not None:
            next_target = self.continuation.activate_pending(global_step=self.index, physics_time=self.before[1], actual_scanner=pc.scanner_from_ee(self.poses['link_6']), q=self.q, dq=self.dq, controller=self.controller, integrator=self.controller_ref)
            if next_target is not None:
                self.target = next_target
                self.monitor = pc.PoseMonitor(self.profile)
                self.stats.update(stable_samples=0, stable_span_s=0.0, stable_count=0, outcome='RUNNING', goal_id=self.continuation.goal_id)
                for key in ('arrival_step', 'arrival_time_s', 'arrival_local_step', 'arrival_local_time_s'):
                    self.stats.pop(key, None)
                self.recorder.result['pose_outcome'] = 'RUNNING'
                self.recorder.result['pose_continuation'] = self.continuation.record()
                self.recorder.emit('pose_goal_activated', goal_id=self.continuation.goal_id, global_step=self.index, physics_time_s=self.before[1], reference_start=_pose_record(self.target.initial))
            if self.index + 1 - self.continuation.goal_start_step > 1800:
                raise pc.PoseCheckError('TOTAL_BUDGET', 'One goal exhausted its 1800 controlled ticks')
        self.reference_time = (self.index + 1) * pc.DT
        if self.continuation is not None:
            self.reference_time = (self.index + 1 - self.continuation.goal_start_step) * pc.DT
        if self.integration:
            self.reference_time = (self.index + 1 - self.goal_start_step) * pc.DT
        if self.shared:
            self.reference_time = (self.index + 1 - self.segment_start_step) * pc.DT
        self.reference = self.target.target.copy() if self.idle_hold else self.target.reference(self.reference_time)
        self.actual_e_r = pc.in_root(self.poses['agv'], self.poses['link_6'])
        self.reference_e_r = pc.in_root(self.poses['agv'], pc.ee_from_scanner(self.reference))
        (self.native_j, _) = _native_jacobian(self.robot, self.mapping)
        j_r = pc.adapt_jacobian(self.native_j, self.adapter['reference_point'], self.poses['agv'], self.poses['link_6'], self.com)
        (self.pe, self.qe) = pc.pose_to_wxyz(self.actual_e_r)
        (self.pr, self.qr) = pc.pose_to_wxyz(self.reference_e_r)
        self.controller.set_command(self.tensor(np.concatenate((self.pr, self.qr))))
        self.q_ik_tensor = self.controller.compute(self.tensor(self.pe), self.tensor(self.qe), self.tensor(j_r), self.q_tensor)
        self.q_ik = self.q_ik_tensor[0].detach().cpu().numpy().copy()
        self.proposal = self.controller_ref.propose(self.q, self.dq, self.q_ik)
        self.raw_delta = float(np.max(np.abs(self.q_ik - self.q)))
        for (label, predicted_poses) in self.model.sanity_samples(self.q, self.proposal.q, self.poses['agv']):
            _check_geometry(self.info['colliders'], predicted_poses, self.config.CONTACT_OFFSET)
            self.stats['sanity_checks'] += 1
        self._phase = 'prepared'
        return self.proposal

    @_fail_closed
    def submit_prepared(self, token):
        """Write exactly one checked position/velocity pair and commit it."""
        self._require('prepared')
        if token is not self.proposal:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Submission token is not the current proposal')
        if _clock(self.sim) != self.before:
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Physics advanced before command submission')
        (self.pos_cmd, self.vel_cmd) = (self.tensor(self.proposal.q), self.tensor(self.proposal.dq))
        self.robot.set_joint_position_target(self.pos_cmd, joint_ids=self.joint_ids)
        self.robot.set_joint_velocity_target(self.vel_cmd, joint_ids=self.joint_ids)
        self.robot.write_data_to_sim()
        (self.submitted_q, self.submitted_dq) = _capture_submitted_targets(self.robot, self.joint_ids, self.pos_cmd, self.vel_cmd)
        self.stats['submitted_target_checks'] += 1
        self.controller_ref.commit(self.proposal, self.submitted_q, self.submitted_dq)
        if self.index == 0:
            self.recorder.result['controlled_step_attempted'] = True
            self.recorder.save()
            self.recorder.emit('controlled_step_begin', step=1)
        self._phase = 'submitted'

    @_fail_closed
    def observe_physics(self, before=None, after=None):
        """Read and guard the externally completed step; return render context."""
        self._require('submitted')
        if before is not None and tuple(before) != self.before:
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Host supplied a different pre-step boundary')
        self.after = _clock(self.sim)
        self._clock_boundary = self.after
        self.controlled_time = self.after[1] - self.baseline[1]
        self.recorder.result['completed_physics_steps'] = self.after[0] - self.baseline[0]
        self.recorder.result['controlled_simulation_time_s'] = self.controlled_time
        self.sample = {'step': self.index + 1, 'physics_time_s': self.after[1], 'controlled_time_s': self.controlled_time, 'reference_time_s': self.reference_time, 'phase': 'trajectory' if self.reference_time < self.profile.reference_seconds else 'final_feedback', 'q_cmd': self.submitted_q, 'dq_cmd': self.submitted_dq, 'max_raw_dls_update_rad': self.raw_delta, 'status': 'RUNNING', **{'guard_' + name: 'NOT_RUN' for name in PoseTrace.GUARDS}}
        if self.continuation is not None:
            self.sample.update(goal_id=self.continuation.goal_id, goal_index=self.continuation.goal_index, local_step=self.index + 1 - self.continuation.goal_start_step, local_time_s=self.after[1] - self.continuation.goal_start_physics_time)
        if self.integration:
            self.sample.update(goal_id=self.goal_id, goal_index=self.goal_index,
                               local_step=self.index + 1 - self.goal_start_step,
                               local_time_s=self.after[1] - self.goal_start_physics_time)
        self._sample_written = False
        if after is not None and tuple(after) != self.after:
            raise pc.PoseCheckError('PHYSICS_GUARD', 'Host supplied a different post-step boundary')
        _checked_tick_guard(self.sample, self.counts, 'clock', lambda : check_clock(*self.before, *self.after, pc.DT))
        self.robot.update(pc.DT)
        (self.q_tensor, self.dq_tensor) = _native_state(self.robot, self.joint_ids)
        (self.q, self.dq) = (self.q_tensor[0].cpu().numpy().copy(), self.dq_tensor[0].cpu().numpy().copy())
        self.sample.update(q=self.q, dq=self.dq)
        _checked_tick_guard(self.sample, self.counts, 'joint', lambda : self.controller_ref.check_actual(self.q, self.dq))
        if self.shared:
            try:
                self._shared_actual_guard()
            except BaseException:
                self.sample['guard_joint'] = 'FAIL'
                self.counts['joint'] -= 1
                raise
        contact_context = dict(getattr(self, 'contact_context', {}))
        contact_context.update(global_physics_step=self.index+1, physics_clock=list(self.after),
                               controlled_time_s=self.controlled_time)
        contact_context.setdefault('run_id', getattr(self.args, 'output_dir', Path('UNKNOWN')).name)
        contact_context.setdefault('robot_id', self.shared_robot_id if self.shared else
                                   self.scene.get('robot_id', 0))
        contact_context.setdefault('phase', self._shared_tick_fields(self.index+1, self.after[1]).get(
            'execution_phase', 'controlled_pose'))
        contact_context.setdefault('control_segment_id', self.control_segment_id)
        self.force = _checked_tick_guard(self.sample, self.counts, 'contact',
            lambda: _check_contacts(self.contacts, pc.DT, context=contact_context))
        self.poses = _body_poses(self.robot, self.body_ids)
        self.actual_scanner = pc.scanner_from_ee(self.poses['link_6'])
        self.minimum_z = _checked_tick_guard(self.sample, self.counts, 'geometry', lambda : _check_geometry(self.info['colliders'], self.poses, self.config.CONTACT_OFFSET))
        (self.distance, self.angle, self.fixed_errors) = _checked_tick_guard(self.sample, self.counts, 'frame', lambda : _check_frames(self.stage, self.info, self.frames, self.poses, self.initial_root))
        for (prefix, transform) in (('actual', self.actual_scanner), ('reference', self.reference), ('target', self.target.target)):
            (self.sample[prefix + '_p'], self.sample[prefix + '_qwxyz']) = pc.pose_to_wxyz(transform)
        (self.ep, self.er) = pc.pose_error(self.actual_scanner, self.target.target)
        (self.ref_ep, self.ref_er) = pc.pose_error(self.actual_scanner, self.reference)
        self.sample.update(target_position_error_m=self.ep, target_orientation_error_rad=self.er, reference_position_error_m=self.ref_ep, reference_orientation_error_rad=self.ref_er)
        if ((self.idle_hold and not (self.shared and self._setup_phase in ('SETUP_SETTLING', 'SETUP_HOLD_READY')))
                or (self.continue_after_arrival and self.monitor.reached)):
            from _cr12_single_view_capture import check_arrived_hold
            check_arrived_hold(self.ep, self.er, self.dq)
        if self.visuals is not None:
            try:
                self.visuals.update(self.actual_scanner, self.target.target)
                self.recorder.result['visual_update_count'] += 1
            except Exception as exc:
                self.recorder.result['visual_errors'].append(f'{type(exc).__name__}: {exc}')
                try:
                    self.visuals.set_visibility(False)
                except Exception as hide_error:
                    self.recorder.result['visual_errors'].append(f'hide: {hide_error}')
                self.visuals = None
        self._phase = 'observed'
        return {'step': self.index + 1, 'physics_time_s': self.after[1],
                'controlled_time_s': self.controlled_time,
                'poses': {k: v.copy() for k, v in self.poses.items()},
                'scanner': self.actual_scanner.copy(), 'target': self.target.target.copy(),
                'q': self.q.copy(), 'dq': self.dq.copy(), 'rendered': self.render_due,
                'pose_reached': self.monitor.reached, 'sample': dict(self.sample),
                'q_cmd': list(self.submitted_q), 'dq_cmd': list(self.submitted_dq),
                **({k: self.sample[k] for k in ('goal_id', 'goal_index', 'local_step', 'local_time_s')}
                   if self.integration or self.continuation is not None else {}),
                **self._shared_tick_fields(self.index+1, self.after[1])}

    @_fail_closed
    def finish_tick(self, rendered):
        """Guard the render boundary, update arrival, and emit one trace sample."""
        self._require('observed')
        if type(rendered) is not bool or rendered != self.render_due:
            raise pc.PoseCheckError('EXECUTOR_PROTOCOL', 'Render cadence must preserve global even-step parity')
        if rendered:
            self.stats['render_calls'] += 1
        def render_guard():
            if _clock(self.sim) != self.after:
                raise pc.PoseCheckError('PHYSICS_GUARD', 'Readback/visual/render advanced physics')
            _assert_active(self.app, self.sim)
        _checked_tick_guard(self.sample, self.counts, 'render_clock', render_guard)
        self.stats.update(maximum_forbidden_contact_n=max(self.stats['maximum_forbidden_contact_n'], self.force), maximum_root_translation_m=max(self.stats['maximum_root_translation_m'], self.distance), maximum_root_rotation_rad=max(self.stats['maximum_root_rotation_rad'], self.angle), minimum_arm_collision_z_m=min(self.stats['minimum_arm_collision_z_m'], self.minimum_z), q_min_rad=np.minimum(self.stats['q_min_rad'], self.q).tolist(), q_max_rad=np.maximum(self.stats['q_max_rad'], self.q).tolist(), max_abs_dq_rad_s=np.maximum(self.stats['max_abs_dq_rad_s'], np.abs(self.dq)).tolist(), max_raw_dls_update_rad=max(self.stats['max_raw_dls_update_rad'], self.raw_delta), max_command_step_rad=max(self.stats['max_command_step_rad'], float(np.max(np.abs(self.proposal.dq))) * pc.DT), final_fixed_frame_errors=self.fixed_errors, final_actual_scanner=_pose_record(self.actual_scanner), final_q_rad=self.q.tolist(), final_dq_rad_s=self.dq.tolist(), final_position_error_m=self.ep, final_orientation_error_rad=self.er)
        if self.shared and self._setup_phase in ('SETUP_SETTLING', 'SETUP_HOLD_READY'):
            self.observation = self._observe_setup_hold()
        elif self.idle_hold:
            self.observation = {'status': 'IDLE_HOLD', 'stable_count': self.stats['stable_samples'],
                                'stable_span_s': self.stats['stable_span_s']}
        elif self.continue_after_arrival and self.monitor.reached:
            self.observation = {'status': 'ARRIVED_HOLD', 'stable_count': self.stats['stable_samples'], 'stable_span_s': self.stats['stable_span_s']}
        elif self.shared:
            if self.control_segment_kind == 'retreat' and self.ep <= pc.POSITION_TOLERANCE and self.er <= pc.ANGLE_TOLERANCE:
                from _cr12_shared_task_profile import clear_q
                pc.check_fixed_neighborhood(self.q, clear_q(self.shared_robot_id))
            self.observation = self.monitor.observe(self.index+1-self.segment_start_step,
                self.after[1]-self.segment_start_physics_time, self.actual_scanner,
                self.reference, self.target.target, self.dq)
        elif self.continuation is not None or self.integration:
            self.observation = self.monitor.observe(self.sample['local_step'], self.sample['local_time_s'], self.actual_scanner, self.reference, self.target.target, self.dq)
        else:
            self.observation = self.monitor.observe(self.index + 1, self.controlled_time, self.actual_scanner, self.reference, self.target.target, self.dq)
        self.sample.update(stable_samples=self.observation['stable_count'], stable_span_s=self.observation['stable_span_s'], status=self.observation['status'])
        self.stats.update(stable_samples=self.observation['stable_count'], stable_span_s=self.observation['stable_span_s'])
        if self.shared:
            shared_record = self.recorder.result['shared_execution']
            shared_record.update(setup_phase=self._setup_phase, control_segment_id=self.control_segment_id,
                control_segment_kind=self.control_segment_kind, completed_physics_steps=self.index+1,
                maximum_command_actual_error_rad=max(shared_record.get('maximum_command_actual_error_rad', 0.),
                    float(np.max(np.abs(np.asarray(self.submitted_q)-self.q)))))
        self._sample_written = True
        finish_sample_trace(self.trace, self.sample, self.recorder, None)
        if (self.index + 1) % 120 == 0:
            self.recorder.save()
            self.recorder.emit('pose_progress', completed_physics_steps=self.index + 1, simulation_time_s=self.controlled_time, position_error_m=self.ep, orientation_error_rad=self.er, max_speed_rad_s=float(np.max(np.abs(self.dq))))
        if self.observation['status'] == 'POSE_REACHED':
            self.stats['all_guards_passed'] = all((v == self.index + 1 for v in self.counts.values()))
            if not self.stats['all_guards_passed'] or self.trace.count != self.index + 1 or any((item['updates'] != self.index + 1 for item in self.contacts.values())) or self.recorder.result['failures'] or self.recorder.result['secondary_failures']:
                raise pc.PoseCheckError('PHYSICS_GUARD', 'Incomplete checks or earlier failure forbid success')
            if self.continue_after_arrival:
                self.stats.update(outcome='POSE_REACHED', arrival_step=self.index + 1, arrival_time_s=self.controlled_time, stable_count=self.stats['stable_samples'])
                if self.continuation is not None or self.integration:
                    self.stats.update(goal_id=self.continuation.goal_id if self.continuation is not None else self.goal_id, arrival_local_step=self.sample['local_step'], arrival_local_time_s=self.sample['local_time_s'])
                self.recorder.result['pose_outcome'] = 'POSE_REACHED'
                self.recorder.emit('POSE_REACHED', completed_physics_steps=self.index + 1, simulation_time_s=self.controlled_time, stable_samples=self.stats['stable_samples'], stable_span_s=self.stats['stable_span_s'])
            else:
                outcome = manual_motion_outcome() if self.profile.manual_visual_only else 'POSE_REACHED'
                self.recorder.result.update(pose_outcome=outcome, work_completed=True, status='WORK_COMPLETED_PENDING_NATURAL_EXIT')
                self.recorder.result['contact_summary'] = _contact_summary(self.contacts)
                self.recorder.save()
                self.recorder.emit(outcome, completed_physics_steps=self.index + 1, simulation_time_s=self.controlled_time, position_error_m=self.ep, orientation_error_rad=self.er, stable_samples=self.stats['stable_samples'], stable_span_s=self.stats['stable_span_s'])
                self.recorder.emit('work_completed', completed_physics_steps=self.index + 1, simulation_time_s=self.controlled_time)
                self.index += 1
                self._phase = 'completed'
                return None
        if self.continue_after_arrival:
            self.stats['all_guards_passed'] = all((v == self.index + 1 for v in self.counts.values()))
        tick = {'step': self.index + 1, 'physics_time_s': self.after[1], 'controlled_time_s': self.controlled_time, 'poses': {k: v.copy() for (k, v) in self.poses.items()}, 'scanner': self.actual_scanner.copy(), 'target': self.target.target.copy(), 'q': self.q.copy(), 'dq': self.dq.copy(), 'rendered': (self.index + 1) % 2 == 0, 'pose_reached': self.monitor.reached, 'sample': dict(self.sample)}
        if self.continuation is not None:
            tick.update(goal_id=self.continuation.goal_id, goal_index=self.continuation.goal_index, local_step=self.sample['local_step'], local_time_s=self.sample['local_time_s'], q_cmd=list(self.submitted_q), dq_cmd=list(self.submitted_dq), render_count=self.stats['render_calls'])
            self.continuation.observe_yield(tick)
            self.recorder.result['pose_continuation'] = self.continuation.record()
        if self.integration:
            tick.update(goal_id=self.goal_id, goal_index=self.goal_index,
                        local_step=self.sample['local_step'], local_time_s=self.sample['local_time_s'],
                        q_cmd=list(self.submitted_q), dq_cmd=list(self.submitted_dq),
                        render_count=self.stats['render_calls'])
        tick.update(self._shared_tick_fields(self.index+1, self.after[1]))
        self._latest_tick = copy.deepcopy(tick)
        self.index += 1
        self._phase = 'ready'
        return tick

    def _observe_setup_hold(self):
        """Only the strict stable window may converge; all safety guards already ran."""
        from _cr12_shared_task_profile import SETUP_MAX_STEPS
        now = self.after[1]
        stable = bool(self.ep <= pc.POSITION_TOLERANCE and self.er <= pc.ANGLE_TOLERANCE
                      and np.max(np.abs(self.dq)) <= .01)
        if self._setup_phase == 'SETUP_HOLD_READY' and not stable:
            raise pc.PoseCheckError('SETUP_HOLD_FAIL', 'Qualified setup hold was lost before common admission')
        self._setup_stable_now = stable
        if stable:
            if self._setup_stable_start is None:
                self._setup_stable_start = now
            self._setup_stable_count += 1
        else:
            self._setup_stable_count = 0
            self._setup_stable_start = None
        span = 0. if self._setup_stable_start is None else now-self._setup_stable_start
        if self._setup_stable_count >= 121 and span >= 1.-1e-6:
            self._setup_phase = 'SETUP_HOLD_READY'
        elif self.index+1 >= SETUP_MAX_STEPS:
            raise pc.PoseCheckError('SETUP_HOLD_FAIL', 'No common-ready local stable window within 360 steps')
        return {'status': self._setup_phase, 'stable_count': self._setup_stable_count, 'stable_span_s': span}

