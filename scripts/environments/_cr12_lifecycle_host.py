"""Private fixed M1/N2 and M2/N4 CR12 host with one physical and authority clock."""
from __future__ import annotations

import copy
from dataclasses import dataclass
import math
import time

import numpy as np
import torch
import _cr12_pose_control as pc
from _cr12_runtime_support import DriveCheckError, _clock
from _cr12_capture_runner import CaptureRequestRunner
from _cr12_scan_executor import Cr12PoseControlSession
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
    resolve_assignment_profile, AssignmentProfileResolutionOrigin)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
    _EventProfileLifecycleRuntimeDomain, _EventProfileLifecycleDomainSpec)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_synchronous_runtime import EventProfileSynchronousRuntimeCoordinator
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_runtime_facade import _compose_event_assignment_runtime_facade
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TaskLifecycleState, RobotLifecycleState
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_cr12_execution_adapter import (
    Cr12ExecutionAdapter, RawCaptureCustody, ExecutionBoundaryEvidence)
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_event_policy_scale_contract_v2
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_terminal_critic_sidecar import capture_pre_reset_critic_physical_snapshot_v2

DECIMATION = 12
CASE_LIMITS = {'normal': (320, 2), 'cancel_then_reclaim': (480, 3),
               'dual_normal_staggered': (420, 2)}


def tensor_list(value):
    return value.detach().cpu().tolist()


def publication_summary(pub):
    state = pub.lifecycle_state
    return {'store_version': pub.store_version, 'episode_generation': tensor_list(pub.episode_generation),
            'transition_generation': tensor_list(pub.transition_generation),
            'task_state': tensor_list(state.task_state), 'robot_state': tensor_list(state.robot_state),
            'ownership': tensor_list(state.ownership), 'completion_count': tensor_list(state.completion_count),
            'failed_pairs': tensor_list(state.cumulative_failed_pairs), 'result_present': pub.result is not None,
            'termination_reason': tensor_list(state.termination_reason)}


@dataclass
class RobotExecutionContext:
    robot_id: int
    run: dict
    recorder: object
    resources: dict
    session: object
    runner: object = None
    requests_started: int = 0
    idle_event_count: int = 0

    @property
    def scene(self): return self.run['scene']
    @property
    def initial(self): return self.run['initial']
    @property
    def capture(self): return self.resources['capture']


class CR12IntegrationHost:
    def __init__(self, args, app, recorder, resources, expected, camera_config, *,
                 setup=None, session_factory=Cr12PoseControlSession, runner_factory=CaptureRequestRunner,
                 instance_specs=None, cross_checker=None):
        self.args, self.app, self.recorder, self.resources = args, app, recorder, resources
        self.expected, self.config = expected, camera_config
        self.device = torch.device(args.device)
        self.case = args.integration_case
        from _cr12_shared_task_profile import CASE as SHARED_CASE, PROFILE_NAME, HOST_TRANSITIONS
        self.shared = self.case == SHARED_CASE
        self.dual = instance_specs is not None
        if self.dual != (self.case in ('dual_normal_staggered', SHARED_CASE)):
            raise DriveCheckError('host_profile', 'Only the explicitly selected fixed profiles are supported')
        self.specs = () if instance_specs is None else tuple(copy.deepcopy(instance_specs))
        if self.dual and sorted(s['robot_id'] for s in self.specs) != [0, 1]:
            raise DriveCheckError('host_profile', 'Exactly robot 0 and 1 are required')
        self.num_robots, self.num_tasks = (2, 1) if self.shared else ((2, 4) if self.dual else (1, 2))
        self.agent_names = ('cr12_0', 'cr12_1') if self.dual else ('cr12',)
        self.horizon, self.request_limit = (HOST_TRANSITIONS, 2) if self.shared else CASE_LIMITS[self.case]
        self._setup, self._session_factory, self._runner_factory = setup, session_factory, runner_factory
        self._cross_checker = cross_checker
        self.profile = resolve_assignment_profile('event_gated_local_mrta',
                            AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        self.domain = _EventProfileLifecycleRuntimeDomain(_EventProfileLifecycleDomainSpec(
            self.profile, device=self.device, env_ids=self.i([0]),
            num_robots=self.num_robots, num_tasks=self.num_tasks))
        self.validation = self.domain.environment_admission_validation_port
        self.lifecycle = self.domain.environment_port
        self.adapter = Cr12ExecutionAdapter(current_read_port=self.domain.current_read_port,
            run_instance_id=args.output_dir.name,
            **({'execution_profile': PROFILE_NAME if self.shared else 'dual_m2n4'} if self.dual else {}))
        self.scale = build_event_policy_scale_contract_v2(M=self.num_robots, N=self.num_tasks,
            ordered_agent_names=self.agent_names, ordered_task_ids=tuple(range(self.num_tasks)),
            scene_env_spacing=1., sim_dt_seconds=pc.DT, control_decimation=DECIMATION,
            episode_time_limit_seconds=self.horizon*.1)
        self.contexts = {}
        self.total_transitions = self.episode_steps = 0
        self.finished = self.cancel_consumed = False
        self.requests, self.claims, self.deliveries, self.rebuilds = [], [], [], []
        self.terminal_before_reset = self._action_binding = None
        self.identities = []
        self.start_wall = time.monotonic()
        self.cross_summary = {'calls': 0, 'actual_checks': 0, 'command_checks': 0,
            'logical_pair_checks': 0, 'coarse_tests': 0, 'fine_pairs_checked': 0,
            'minimum_axis_gap_m': None}
        self.parallel = {'simultaneous_actual_motion_ticks': 0, 'first_motion_overlap_step': None,
            'last_motion_overlap_step': None, 'phase_intervals': [], 'mixed_stage_observed': False,
            'off_a_fresh_b': []}
        self._reset_started = False
        self.setup_ticks = 0
        self.partial_block_ticks = 0
        self.shared_handover = {'setup': None, 'retreat_switch': None,
                               'clear_release': None, 'b_admission': None}

    # These aliases keep the accepted single-robot entry and its results unchanged.
    @property
    def run(self): return self.contexts[0].run if self.contexts else None
    @property
    def scene(self): return self.contexts[0].scene
    @property
    def initial(self): return self.contexts[0].initial
    @property
    def capture(self): return self.contexts[0].capture
    @property
    def session(self): return self.contexts[0].session if self.contexts else None
    @property
    def runner(self): return self.contexts[0].runner if self.contexts else None

    def i(self, data): return torch.tensor(data, dtype=torch.int64, device=self.device)
    def f(self, data): return torch.tensor(data, dtype=torch.float32, device=self.device)
    def b(self, data): return torch.tensor(data, dtype=torch.bool, device=self.device)

    def _ordered(self):
        return tuple(self.contexts[r] for r in range(self.num_robots))

    def _reset_args(self):
        return dict(selected_env_ids=self.i([0]),
            initial_task_state=self.i([[int(TaskLifecycleState.AVAILABLE)]*self.num_tasks]),
            initial_robot_state=self.i([[int(RobotLifecycleState.NEEDS_ASSIGNMENT)]*self.num_robots]),
            initial_ownership=self.i([[-1]*self.num_tasks]))

    def _new_episode_context(self):
        actual = {c.robot_id: c.session.current_state() for c in self._ordered()}
        self.episode_context = {
            'generation': tensor_list(self.domain.current_read_port.read_current().episode_generation),
            'robots': {r: {'initial_actual_scanner': s['scanner'].copy(),
                'initial_actual_q': s['q'].copy(), 'initial_q_cmd': copy.deepcopy(s['q_cmd']),
                'global_step_origin': s['step']} for r, s in actual.items()}}
        self.episode_steps = 0

    def reset(self):
        if self._reset_started:
            raise DriveCheckError('reset_scope', 'Only initial standalone reset is supported')
        self._reset_started = True
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(**self._reset_args()) as rebuild:
            if self._setup is not None:
                prepared = self._setup()
            elif self.dual:
                from run_cr12_single_view_capture import initialize_dual_capture_runs
                prepared = initialize_dual_capture_runs(self.args, self.app, self.recorder, self.resources,
                    self.expected, self.config, self.specs,
                    **({'profile_name': 'shared_m2n1'} if self.shared else {}))
            else:
                from run_cr12_single_view_capture import initialize_capture_run
                prepared = initialize_capture_run(self.args, self.app, self.recorder, self.resources,
                    self.expected, self.config, camera_request_limit=self.request_limit, camera_integration=True)
            runs = tuple(prepared) if self.dual else (prepared,)
            for run in runs:
                robot_id = int(run['robot_id']) if self.dual else 0
                if robot_id in self.contexts or not 0 <= robot_id < self.num_robots:
                    raise DriveCheckError('instance_identity', 'Duplicate or unexpected robot context')
                recorder = run['recorder'] if self.dual else self.recorder
                resources = run['resources'] if self.dual else self.resources
                session = self._session_factory(self.args, self.app, recorder, resources, self.expected,
                    scene=run['scene'], initial=run['initial'], integration=True,
                    **({'allow_unbound_hold': True, 'set_view': False} if self.dual else {}),
                    **({'shared_robot_id': robot_id} if self.shared else {}))
                self.contexts[robot_id] = RobotExecutionContext(robot_id, run, recorder, resources, session,
                    idle_event_count=resources['capture'].summary()['unique_product_event_count'])
            if len(self.contexts) != self.num_robots:
                raise DriveCheckError('instance_identity', 'Missing real robot context')
            clocks = [_clock(c.scene['sim']) for c in self._ordered()]
            if any(c.scene['sim'] is not self.scene['sim'] for c in self._ordered()) or len(set(clocks)) != 1:
                raise DriveCheckError('global_clock', 'All instances must share the same simulation and boundary')
            if self.dual:
                self._check_cross([c.session.current_state()['poses'] for c in self._ordered()], 'initial')
            # Setup has checked independent expected roots/native maps/camera before this freeze.
            targets = []
            for c in self._ordered():
                original = c.session.current_state()['scanner'].copy()
                if not self.shared:
                    targets.extend((pc.FrozenPoseTarget(original).target, original))
                self.identities.append({'robot_id': c.robot_id, 'identity': c.capture.device_identity()}
                                       if self.dual else c.capture.device_identity())
                before = c.recorder.result['initialization']['before_reset_clock']
                warm_ticks = c.initial['baseline'][0] - before[0]
                if (self.dual and warm_ticks != 2) or (not self.dual and warm_ticks > 2):
                    raise DriveCheckError('initialization_budget', 'Unexpected shared initialization tick count',
                                          robot_id=c.robot_id, ticks=warm_ticks)
            if self.shared:
                from _cr12_shared_task_profile import scanner_target
                targets = [scanner_target()]
            self.targets = tuple(targets)
            for target in self.targets: target.setflags(write=False)
            self.recorder.result['frozen_tasks'] = [
                {'task_id': i, 'allowed_robot': [0, 1] if self.shared else i//2, 'matrix': t.tolist(),
                 'position_m': pc.pose_to_wxyz(t)[0].tolist(),
                 'quaternion_wxyz': pc.pose_to_wxyz(t)[1].tolist()} for i, t in enumerate(self.targets)]
            self.arm_reaches = [float(sum(np.linalg.norm(v) for v in c.session.model.origins)
                + np.linalg.norm(pc.scanner_from_ee(np.eye(4))[:3, 3])) for c in self._ordered()]
            self.arm_reach = self.arm_reaches[0]
            if self.shared:
                self._run_setup_hold()
            rebuild.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        self._new_episode_context()
        self.rebuilds.append({'kind': 'initial', 'publication': publication_summary(self.domain.current_read_port.read_current()),
                              'physics_clock': list(_clock(self.scene['sim']))})
        return self.observation(), {'private_execution_backend': 'cr12'}

    def observation(self):
        return {name: self.f([np.concatenate(pc.pose_to_wxyz(c.session.current_state()['scanner'])).tolist()])
                for name, c in zip(self.agent_names, self._ordered())}

    def assignment_problem(self):
        states = [c.session.current_state() for c in self._ordered()]
        scanners = [pc.pose_to_wxyz(s['scanner']) for s in states]
        targets = [pc.pose_to_wxyz(t) for t in self.targets]
        return dict(num_envs=1, num_agents=self.num_robots, agent_names=self.agent_names,
            num_viewpoints=self.num_tasks, viewpoint_ids=tuple(range(self.num_tasks)),
            base_pos=self.f([[s['poses']['agv'][:3, 3].tolist() for s in states]]),
            base_yaw=self.f([[math.atan2(s['poses']['agv'][1, 0], s['poses']['agv'][0, 0]) for s in states]]),
            scanner_pos=self.f([[p.tolist() for p, _ in scanners]]),
            scanner_quat=self.f([[q.tolist() for _, q in scanners]]),
            viewpoint_pos=self.f([[p.tolist() for p, _ in targets]]),
            viewpoint_quat=self.f([[q.tolist() for _, q in targets]]),
            arm_reach=self.f(self.arm_reaches), scanner_min_range=self.f([self.config.near_m]*self.num_robots),
            scanner_max_range=self.f([self.config.far_m]*self.num_robots),
            scanner_fov_deg=self.f([self.config.horizontal_fov_deg]*self.num_robots),
            feasible_mask=self.b([[[self.shared or r == t//2 for t in range(self.num_tasks)]
                                  for r in range(self.num_robots)]]),
            cost_matrix=self.f([[[float(np.linalg.norm(p-pt)) for pt, _ in targets] for p, _ in scanners]]))

    def bind_effective_assignment(self, environment, assignment):
        if environment is not self or self.finished:
            raise DriveCheckError('host_identity', 'Unexpected host or post-terminal step')
        entries = (self.adapter.bind_effective_assignments(assignment) if self.dual
                   else (self.adapter.bind_effective_assignment(assignment),))
        for c, (binding, is_new) in zip(self._ordered(), entries):
            if binding is None:
                if c.runner is not None or not self.dual:
                    raise DriveCheckError('assignment_missing', 'A live runner needs its real binding')
                continue
            if binding.robot_id != c.robot_id:
                raise DriveCheckError('instance_identity', 'Binding addresses another robot')
            if is_new:
                if c.runner is not None or c.requests_started >= (1 if self.shared else self.request_limit):
                    raise DriveCheckError('request_budget', 'Previous request remains or local request budget exhausted')
                if self.shared:
                    from _cr12_shared_task_profile import A_BINDING_TICKS, B_BINDING_TICKS
                    required_ticks = A_BINDING_TICKS if c.robot_id == 0 else B_BINDING_TICKS
                    if c.robot_id == 1:
                        self.check_shared_successor_ready(require_available=False)
                else:
                    required_ticks = 1800
                if (self.horizon-self.episode_steps)*DECIMATION < required_ticks+DECIMATION:
                    raise DriveCheckError('case_budget', 'Insufficient time to admit a safe bounded request')
                actual = c.session.current_state()
                c.session.submit_goal(binding.goal_id, self.targets[binding.task_id], latest_actual_boundary=actual)
                output = (self.args.output_dir / f'robot_{c.robot_id}' / f'task_{binding.task_id}' /
                          f'claim_{binding.claim_token}') if self.dual else self.args.output_dir / f'request_{len(self.claims)+1:02d}'
                if self.dual: output.parent.mkdir(parents=True, exist_ok=True)
                c.runner = self._runner_factory(binding, c.capture, c.scene, self.config,
                    start_tick=actual, output_dir=output, recorder=c.recorder,
                    mount_aggregate=c.run['mount_aggregate'], initial_camera=c.run['initial_camera'],
                    cancel_at_wait=(self.shared and c.robot_id == 0) or
                        (self.case == 'cancel_then_reclaim' and not self.cancel_consumed),
                    **({'execution_profile': 'shared_m2n1', 'shared_model': c.session.model}
                       if self.shared else {}))
                c.resources['request'] = c.runner.request
                c.requests_started += 1
                self.claims.append({**binding.summary(), 'global_start_step': actual['step'],
                    'q_cmd_at_accept': np.asarray(actual['q_cmd']).tolist(),
                    'actual_scanner_at_accept': actual['scanner'].tolist(),
                    'target_matrix': self.targets[binding.task_id].tolist()})
                self.recorder.emit('authority_claim_bound', **self.claims[-1])
        self._action_binding = tuple(b for b, _ in entries) if self.dual else entries[0][0]
        return self._action_binding

    def _deliver(self, outcome):
        receipts = self.adapter.ack_authority_deliveries(outcome) if self.dual else (self.adapter.ack_authority_delivery(outcome),)
        receipts = tuple(r for r in receipts if r is not None)
        # Preserve the whole committed batch before the first local retirement can fail.
        after = publication_summary(self.domain.current_read_port.read_current())
        for receipt in receipts:
            c = self.contexts[receipt.binding.robot_id]
            c.runner.record['authority_receipt'] = receipt.summary()
            c.runner.record['authority_after'] = after
            self.deliveries.append(receipt.summary())
        self.recorder.result['authority_deliveries'] = self.deliveries
        if receipts: self.recorder.save()
        for receipt in receipts:
            c = self.contexts[receipt.binding.robot_id]
            runner, binding = c.runner, c.runner.binding
            self._runner_boundary(c)
            def validate(candidate, ids, receipt=receipt, binding=binding, runner=runner, c=c):
                return (candidate is receipt and candidate.binding is binding
                    and candidate.pending is self.adapter.pending_result(c.robot_id)
                    and ids == runner.request.ids and candidate.result is outcome.result)
            c.capture.retire_request(runner.request.ids, authority_receipt=receipt,
                                    receipt_validator=validate, hold_verified=True)
            runner.retired = True
            self.adapter.retire_request(binding, receipt)
            runner.record['retired_after_receipt'] = True
            runner.record['receipt_then_retire_step'] = runner.latest_tick['step']
            self.requests.append(runner.finalize_record())
            c.resources['last_integration_request'] = runner.request
            if runner.cancel_issued: self.cancel_consumed = True
            self.identities.append({'robot_id': c.robot_id, 'identity': c.capture.device_identity()}
                                   if self.dual else c.capture.device_identity())
            self.recorder.emit('authority_result_delivered_and_retired', **receipt.summary())
            if self.dual:
                c.session.enter_idle_hold()
                c.idle_event_count = c.capture.summary()['unique_product_event_count']
            c.runner = None
        if not self.dual and receipts: self._action_binding = None

    def _idle_boundary(self, c, *, rendered=False):
        from run_cr12_single_view_capture import native_validity
        from _cr12_single_view_capture import check_arrived_hold
        native_validity(c.scene['robot'], c.scene['sim'])
        actual = c.session.current_state()
        check_arrived_hold(*pc.pose_error(actual['scanner'], actual['target']), actual['dq'])
        if self.shared and (c.robot_id == 0 or c.requests_started == 0):
            from _cr12_shared_task_profile import initial_q
            pc.check_fixed_neighborhood(actual['q'], initial_q(c.robot_id))
        c.capture.assert_off('unbound_feedback_hold')
        peek = c.capture.peek_retained_snapshot()
        if peek['errors']:
            raise DriveCheckError('idle_camera_health', 'Idle camera has sticky errors', robot_id=c.robot_id)
        summary = c.capture.summary()
        if summary['unique_product_event_count'] != c.idle_event_count:
            raise DriveCheckError('idle_camera_output', 'OFF unbound camera produced new output', robot_id=c.robot_id)
        if summary['request'] is not None:
            if not summary['request_retired']:
                raise DriveCheckError('idle_request', 'Unbound camera request has not retired')
            close = c.capture.observe_close(render_opportunity=rendered)
            if not close['confirmed']:
                raise DriveCheckError('idle_camera_off', 'Retired request lost independent OFF')
        return ExecutionBoundaryEvidence(physics_step=actual['step'], goal_id=None, capture_id=None,
            off_confirmed=True, holding=True, resource_healthy=True, native_valid=True,
            no_pending_data=True, continuous_hold=True)

    def _shared_camera_health(self, c):
        """Current OFF/native facts; this never reads lifecycle while reset is locked."""
        from run_cr12_single_view_capture import native_validity
        native_validity(c.scene['robot'], c.scene['sim'])
        c.capture.assert_off('shared_park_or_cleanup_peer')
        peek = c.capture.peek_retained_snapshot()
        if peek['errors']:
            raise DriveCheckError('shared_peer_health', 'Shared waiting camera is unhealthy',
                                  robot_id=c.robot_id, errors=peek['errors'])
        if c.capture.summary()['unique_product_event_count'] != c.idle_event_count:
            raise DriveCheckError('shared_peer_output', 'An OFF waiting product produced new data',
                                  robot_id=c.robot_id)
        return dict(off=True, resource_healthy=True, native_valid=True, guards_passed=True)

    def _runner_boundary(self, c):
        if not self.shared:
            return c.runner.boundary()
        peer = self.contexts[1-c.robot_id]
        return c.runner.boundary(peer_tick=peer.session.current_state(),
                                 peer_status=self._shared_camera_health(peer))

    def check_shared_successor_ready(self, *, require_available=True):
        """R is not a permanent space permit: check the current physical boundary."""
        if not self.shared or len(self.claims) != 1 or len(self.deliveries) != 1:
            raise DriveCheckError('shared_b_admission', 'B requires exactly one preceding real A release')
        a, b = self.contexts[0], self.contexts[1]
        if (a.runner is not None or self.adapter.binding_for(0) is not None
                or self.adapter.pending_result(0) is not None or len(self.requests) != 1
                or self.deliveries[0]['outcome'] != 'cancelled'
                or self.claims[0]['robot_id'] != 0 or self.claims[0]['task_id'] != 0):
            raise DriveCheckError('shared_b_admission', 'A has not completed receipt-backed clear retirement')
        for c in (a, b): self._idle_boundary(c)
        self._check_cross([c.session.current_state()['poses'] for c in (a, b)], 'actual')
        if require_available:
            state = self.domain.current_read_port.read_current().lifecycle_state
            if (int(state.ownership[0, 0]) != -1
                    or int(state.task_state[0, 0]) != int(TaskLifecycleState.AVAILABLE)):
                raise DriveCheckError('shared_b_admission', 'Real task is not AVAILABLE and unowned')
        actual = a.session.current_state()
        previous = self.shared_handover.get('b_admission') or {}
        self.shared_handover['b_admission'] = {
            'step': actual['step'], 'a_actual_q': actual['q'].tolist(),
            'a_actual_scanner': actual['scanner'].tolist(), 'a_off_clear': True,
            'a_retired_after_receipt': True,
            'require_available_checked': require_available or previous.get('require_available_checked', False)}

    def _run_setup_hold(self):
        from _cr12_shared_task_profile import SETUP_MAX_TICKS
        for c in self._ordered(): c.session.begin_setup_hold()
        self.recorder.phase = 'shared_setup_settling'
        self.recorder.emit('shared_setup_begin', global_step=0)
        stable, start_time = 0, None
        record = self.shared_handover['setup'] = {'status': 'SETUP_SETTLING',
            'limit_ticks': SETUP_MAX_TICKS, 'claim_count': 0, 'authority_transitions': 0}
        self.recorder.result['shared_handover'] = self.shared_handover
        for _ in range(SETUP_MAX_TICKS):
            try:
                ticks = self._advance_physics(setup=True)
            except BaseException as exc:
                record.update(status='SETUP_HOLD_FAIL', ticks=self.setup_ticks,
                              failure_category=getattr(exc, 'category', type(exc).__name__),
                              failure_message=str(exc))
                raise
            self.setup_ticks = ticks[0]['step']
            together = all(t['setup_stable_now'] is True for t in ticks)
            if together:
                if stable == 0: start_time = ticks[0]['physics_time_s']
                stable += 1
            else:
                stable, start_time = 0, None
            span = 0. if start_time is None else ticks[0]['physics_time_s']-start_time
            record.update(ticks=self.setup_ticks, stable_samples=stable, stable_span_s=span,
                          stable_start_time=start_time, final_time=ticks[0]['physics_time_s'])
            if (stable >= 121 and span >= 1.-1e-6
                    and all(c.session.setup_hold_ready for c in self._ordered())):
                record['sessions'] = []
                for c in self._ordered():
                    state = c.session.complete_setup_hold()
                    record['sessions'].append({'robot_id': c.robot_id, 'step': state['step'],
                        'q_cmd': np.asarray(state['q_cmd']).tolist(), 'scanner': state['scanner'].tolist(),
                        'setup_stable_samples': state['setup_stable_samples'],
                        'setup_stable_span_s': state['setup_stable_span_s']})
                record['status'] = 'SETUP_HOLD_READY'
                record['final_q'] = [t['q'].tolist() for t in ticks]
                record['final_dq'] = [t['dq'].tolist() for t in ticks]
                self.recorder.emit('shared_setup_hold_ready', global_step=self.setup_ticks,
                                   stable_samples=stable, stable_span_s=span)
                self.recorder.save()
                return
        record['status'] = 'SETUP_HOLD_FAIL'
        raise DriveCheckError('SETUP_HOLD_FAIL', 'Both nonzero park holds did not stabilize in 360 ticks',
                              evidence=record)

    def _record_pending(self, c, tick):
        runner = c.runner
        if runner.request.failure is not None and runner.request.failure['category'] != 'CANCELLED':
            raise DriveCheckError('unexpected_request_failure', str(runner.request.failure))
        custody = None if runner.snapshot is None else RawCaptureCustody(
            rgba=runner.snapshot['rgba'], metadata=runner.snapshot['metadata'])
        metadata = {'request': runner.request.summary(), 'terminal_physics_step': tick['step']}
        if self.shared:
            metadata = runner.pending_metadata()
        self.adapter.record_pending(runner.binding,
            outcome='completed' if runner.request.acquired else 'cancelled',
            acquired=runner.request.acquired, custody=custody, physics_step=tick['step'], metadata=metadata)
        runner.pending_recorded = True
        if self.shared and not runner.request.acquired:
            self.shared_handover['clear_release'] = {
                'pending_step': tick['step'], 'binding': runner.binding.summary(),
                'clear_actual_q': tick['q'].tolist(), 'clear_actual_scanner': tick['scanner'].tolist()}

    def _logical_rebuild(self, outcome):
        for c in self._ordered():
            bound = self.adapter.binding_for(c.robot_id) if self.dual else self.adapter.binding
            if c.runner is not None or bound is not None or self.adapter.pending_result(c.robot_id) is not None:
                raise DriveCheckError('terminal_live_request', 'Rebuild requires all receipt-backed retirements')
            if self.dual: self._idle_boundary(c)
            else: c.capture.assert_off('terminal_rebuild')
        current = self.domain.current_read_port.read_current()
        if bool((current.lifecycle_state.robot_state == int(RobotLifecycleState.UNAVAILABLE)).any()):
            raise DriveCheckError('unsafe_terminal', 'Unavailable robot cannot become healthy through reset')
        self.terminal_before_reset = publication_summary(current)
        self.terminal_before_reset.update(facts_consume_token=tensor_list(outcome.result.facts_consume_token),
                                         authority_receipt_id=tensor_list(outcome.result.authority_receipt_id))
        before = [c.session.current_state() for c in self._ordered()]
        clock_before = _clock(self.scene['sim'])
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(**self._reset_args()) as rebuild:
            self.episode_steps = 0
            rebuild.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        self._new_episode_context()
        after = [c.session.current_state() for c in self._ordered()]
        same = clock_before == _clock(self.scene['sim']) and all(
            np.array_equal(a[k], b[k]) for a, b in zip(before, after) for k in ('q', 'dq', 'q_cmd', 'scanner'))
        if not same:
            raise DriveCheckError('reset_state_changed', 'Logical rebuild changed physics or control state')
        self.rebuilds.append({'kind': 'safe_terminal_logical', 'physics_unchanged': same,
            'clock_before': list(clock_before), 'clock_after': list(_clock(self.scene['sim'])),
            'robots_before': [{k: np.asarray(s[k]).tolist() for k in ('q', 'dq', 'q_cmd', 'scanner')} for s in before],
            'robots_after': [{k: np.asarray(s[k]).tolist() for k in ('q', 'dq', 'q_cmd', 'scanner')} for s in after],
            'new_publication': publication_summary(self.domain.current_read_port.read_current())})
        self.finished = True

    def _check_cross(self, poses, phase):
        if not self.dual: return
        if self._cross_checker is None:
            from _cr12_runtime_support import check_cross_geometry
            checker = check_cross_geometry
        else:
            checker = self._cross_checker
        result = checker(self.contexts[0].scene, poses[0], self.contexts[1].scene, poses[1])
        stats = self.cross_summary
        stats['calls'] += 1
        stats['actual_checks' if phase == 'actual' else 'command_checks'] += int(phase != 'initial')
        stats['logical_pair_checks'] += result['logical_pairs']
        stats['coarse_tests'] += result['coarse_tests']
        stats['fine_pairs_checked'] += result['fine_pairs_checked']
        gap = result['minimum_axis_gap_m']
        if stats['minimum_axis_gap_m'] is None or gap < stats['minimum_axis_gap_m']:
            stats['minimum_axis_gap_m'] = gap
            stats['minimum_evidence'] = {'phase': phase,
                                         'step': _clock(self.scene['sim'])[0]-self.initial['baseline'][0],
                                         **copy.deepcopy(result)}
        if phase == 'initial': stats['initial'] = copy.deepcopy(result)

    def _cross_commands(self, proposals):
        if not self.dual: return
        samples = [c.session.model.sanity_samples(c.session.q, p.q, c.session.poses['agv'])
                   for c, p in zip(self._ordered(), proposals)]
        if [x[0] for x in samples[0]] != ['midpoint', 'endpoint'] or [x[0] for x in samples[1]] != ['midpoint', 'endpoint']:
            raise DriveCheckError('cross_reference', 'Cross guard must use both current quantized command references')
        for i in range(2):
            self._check_cross([s[i][1] for s in samples], 'command')

    def _record_parallel(self, before, ticks, phases_before):
        if not self.dual: return
        step = ticks[0]['step']
        moving = [p == 'MOVING_OFF' and float(np.max(np.abs(t['q']-s['q']))) > 1e-8
                  for p, t, s in zip(phases_before, ticks, before)]
        if all(moving):
            self.parallel['simultaneous_actual_motion_ticks'] += 1
            if self.parallel['first_motion_overlap_step'] is None: self.parallel['first_motion_overlap_step'] = step
            self.parallel['last_motion_overlap_step'] = step
        phases = [c.runner.request.state if c.runner else 'IDLE_HOLD' for c in self._ordered()]
        intervals = self.parallel['phase_intervals']
        if intervals and intervals[-1]['states'] == phases: intervals[-1]['end_step'] = step
        else: intervals.append({'states': phases, 'start_step': step, 'end_step': step})
        if 'MOVING_OFF' in phases and any(p in ('WAITING_DATA', 'CAPTURE_CLOSING', 'IDLE_HOLD') for p in phases):
            self.parallel['mixed_stage_observed'] = True

    def _record_isolation(self, before, after, ticks):
        if self.parallel['off_a_fresh_b']: return
        for a, b in ((0, 1), (1, 0)):
            ca, cb = self.contexts[a], self.contexts[b]
            if cb.runner is None or not cb.runner.request.acquired: continue
            metadata = cb.runner.snapshot['metadata']
            received = metadata.get('received_context', {})
            if (before[a]['updates_enabled'] is False and after[a]['updates_enabled'] is False
                and before[a]['own_unique_completions'] == after[a]['own_unique_completions']
                and before[a]['observer_active'] and after[a]['observer_active']
                and before[b]['updates_enabled'] is True
                and after[b]['own_unique_completions'] > before[b]['own_unique_completions']
                and received.get('controlled_step') == ticks[b]['step']
                and metadata['capture_id'] == cb.runner.binding.capture_id):
                self.parallel['off_a_fresh_b'].append({'global_step': ticks[b]['step'],
                    'global_render_index': self.session.stats['render_calls'],
                    'off_robot': a, 'fresh_robot': b, 'before': copy.deepcopy(before),
                    'after': copy.deepcopy(after), 'fresh_metadata': copy.deepcopy(metadata),
                    'data_acquired_then_closed': cb.runner.request.acquired})
                self.recorder.emit('dual_product_isolation_observed', **self.parallel['off_a_fresh_b'][-1])
                return

    def _advance_physics(self, *, setup=False):
        """The sole physics dispatcher for both locked setup and admitted tasks."""
        from run_cr12_single_view_capture import native_validity, receive_context_callback
        ordered = self._ordered()
        callbacks = [receive_context_callback(c.initial, c.run['receive_context']) for c in ordered]
        try:
                if self.shared:
                    from _cr12_shared_task_profile import TOTAL_CONTROLLED_TICKS
                    if self.session.current_state()['step'] >= TOTAL_CONTROLLED_TICKS:
                        raise DriveCheckError('total_physics_budget', 'Shared controlled physics budget exhausted')
                previous = [c.session.current_state() for c in ordered]
                phases = [c.runner.request.state if c.runner else 'IDLE_HOLD' for c in ordered]
                for c in ordered:
                    self._set_runtime_phase('before_tick', c, setup=setup)
                    if setup: self._shared_camera_health(c)
                    elif c.runner is not None: c.runner.before_tick()
                    else: self._idle_boundary(c)
                    native_validity(c.scene['robot'], c.scene['sim'])
                proposals = []
                for c in ordered:
                    self._set_runtime_phase('prepare', c, setup=setup)
                    proposals.append(c.session.prepare_tick())
                self._set_runtime_phase('command_cross_geometry', setup=setup)
                self._cross_commands(proposals)
                for c, token in zip(ordered, proposals):
                    self._set_runtime_phase('submit', c, setup=setup)
                    c.session.submit_prepared(token)
                before = _clock(self.scene['sim'])
                if not self.recorder.result['controlled_step_attempted']:
                    self.recorder.result['controlled_step_attempted'] = True
                    self.recorder.save()
                    self.recorder.emit('controlled_step_begin', step=1, shared_robot_count=self.num_robots)
                self._set_runtime_phase('physics_step', setup=setup)
                self.scene['sim'].step(render=False)
                after = _clock(self.scene['sim'])
                # This global tick happened even if either subsequent native guard fails.
                self.recorder.result['completed_physics_steps'] = after[0]-self.initial['baseline'][0]
                self.recorder.result['controlled_simulation_time_s'] = after[1]-self.initial['baseline'][1]
                if setup: self.setup_ticks = self.recorder.result['completed_physics_steps']
                else: self.partial_block_ticks += 1
                contexts = []
                for c in ordered:
                    context = self._set_runtime_phase('observe_physics', c, setup=setup)
                    c.session.contact_context = {**context,
                        'global_physics_step': self.recorder.result['completed_physics_steps'],
                        'physics_clock': list(after),
                        'controlled_time_s': after[1]-self.initial['baseline'][1]}
                    contexts.append(c.session.observe_physics(before, after))
                self.recorder.result['completed_physics_steps'] = contexts[0]['step']
                self.recorder.result['controlled_simulation_time_s'] = contexts[0]['controlled_time_s']
                if len({ctx['step'] for ctx in contexts}) != 1:
                    raise DriveCheckError('global_clock', 'Per-robot tick counters diverged')
                self._check_cross([ctx['poses'] for ctx in contexts], 'actual')
                rendered = ordered[0].session.render_due
                if any(c.session.render_due != rendered for c in ordered):
                    raise DriveCheckError('global_clock', 'Render cadence differs between robots')
                pre_render = None
                if rendered:
                    self._set_runtime_phase('render', setup=setup)
                    for callback, context in zip(callbacks, contexts): callback(context)
                    if self.dual: pre_render = [c.capture.render_evidence() for c in ordered]
                    self.scene['sim'].render()
                ticks = []
                for c in ordered:
                    self._set_runtime_phase('finish_tick', c, setup=setup)
                    ticks.append(c.session.finish_tick(rendered))
                for c, tick in zip(ordered, ticks):
                    self._set_runtime_phase('execution_observe', c, setup=setup)
                    c.resources['latest_capture_tick'] = tick
                    if setup:
                        self._shared_camera_health(c)
                        continue
                    runner = c.runner
                    if runner is None:
                        self._idle_boundary(c, rendered=rendered)
                        continue
                    if self.shared:
                        peer = self.contexts[1-c.robot_id]
                        runner.observe_tick(tick, peer_tick=ticks[1-c.robot_id],
                                            peer_status=self._shared_camera_health(peer))
                        if runner.needs_retreat:
                            switched = c.session.submit_bound_segment(kind='retreat', latest_actual_boundary=tick)
                            runner.begin_retreat(switched['control_segment_id'], tick)
                            self.shared_handover['retreat_switch'] = copy.deepcopy(switched)
                            self.recorder.emit('shared_bound_retreat_begin', robot_id=c.robot_id,
                                               global_step=tick['step'], binding=runner.binding.summary())
                    else:
                        runner.observe_tick(tick)
                        if runner.terminal and not runner.pending_recorded:
                            self._record_pending(c, tick)
                if not setup: self._record_parallel(previous, ticks, phases)
                if not setup and self.dual and rendered:
                    self._record_isolation(pre_render, [c.capture.render_evidence() for c in ordered], ticks)
                return ticks
        except BaseException as exc:
            for c in ordered: c.session.abort(exc)
            raise

    def _set_runtime_phase(self, operation, context=None, *, setup=False):
        """Record the live stage without reading native state or lifecycle ports."""
        committed = operation in ('receipt_and_retirement', 'terminal_rebuild')
        row = {'run_id': self.args.output_dir.name,
               'host_transition': None if setup else self.total_transitions+(0 if committed else 1),
               'operation': operation, 'phase': 'SETUP_SETTLING' if setup else 'HOST_TRANSITION',
               'robot_id': None, 'control_segment_id': None}
        if context is not None:
            state = context.session.current_state()
            row.update(robot_id=context.robot_id, control_segment_id=state.get('control_segment_id'))
            if setup:
                row['phase'] = state.get('execution_phase', 'SETUP_SETTLING')
            elif context.runner is not None:
                row['phase'] = (context.runner.execution_phase if self.shared else context.runner.request.state)
            else:
                row['phase'] = 'IDLE_HOLD'
        label = f"{'shared' if self.shared else 'dual' if self.dual else 'single'}:{row['phase']}:{operation}"
        if context is not None:
            label += f':robot_{context.robot_id}'
            context.recorder.phase = label
        self.recorder.phase = label
        self.recorder.result['runtime_context'] = copy.deepcopy(row)
        return row

    def step(self, binding):
        self.validation.validate_physical_step_entry_for_active_call()
        if binding is not self._action_binding:
            raise DriveCheckError('admission_identity', 'Step did not receive the admitted binding batch')
        if self.total_transitions >= self.horizon:
            raise DriveCheckError('case_budget', 'Host transition limit reached')
        ordered = self._ordered()
        self.partial_block_ticks = 0
        for _ in range(DECIMATION):
            self._advance_physics()
        self._set_runtime_phase('block_boundary')
        boundaries = {c.robot_id: self._runner_boundary(c) if c.runner else self._idle_boundary(c) for c in ordered}
        if self.shared:
            for c in ordered:
                if c.runner is not None and c.runner.delivery_ready and not c.runner.pending_recorded:
                    self._record_pending(c, c.runner.latest_tick)
        else:
            self.total_transitions += 1
        self.episode_steps += 1
        current = self.domain.current_read_port.read_current()
        coverage = current.lifecycle_state.task_state == int(TaskLifecycleState.COMPLETED)
        physical = capture_pre_reset_critic_physical_snapshot_v2(
            assignment_problem=self.assignment_problem(), episode_progress_steps=self.i([self.episode_steps]),
            scale_contract=self.scale, physical_problem_source='CR12IntegrationHost.assignment_problem guarded actual state')
        deadline = self.episode_steps >= self.horizon
        if deadline and any(not (b.off_confirmed and b.holding and b.resource_healthy) for b in boundaries.values()):
            raise DriveCheckError('case_deadline', 'Cannot publish a healthy terminal at an unsafe deadline')
        self.validation.validate_physical_finalization_for_active_call()
        report = self.adapter.build_report(
            **({'boundaries_by_robot': boundaries} if self.dual else {'boundary': boundaries[0]}),
            coverage_before_transition=coverage, physical_truncated=self.b([deadline]),
            time_limit_reached=self.b([deadline]), pre_reset_critic_physical_snapshot=physical)
        self._set_runtime_phase('authority_finalize')
        outcome = self.lifecycle.finalize_execution_transition(report)
        if self.shared: self.total_transitions += 1
        self.partial_block_ticks = 0
        try:
            self._set_runtime_phase('receipt_and_retirement')
            self._deliver(outcome)
            terminated, truncated = outcome.terminated, outcome.truncated
            if bool((terminated | truncated).any()):
                self._set_runtime_phase('terminal_rebuild')
                self._logical_rebuild(outcome)
        except BaseException as exc:
            self.lifecycle.report_post_authority_bookkeeping_failure(outcome, exc)
            raise
        self.recorder.result.update(host_summary=self.summary(), requests=self.requests,
            authority_claims=self.claims, authority_deliveries=self.deliveries,
            cross_robot_geometry=self.cross_summary, parallel_evidence=self.parallel)
        if self.shared:
            self.recorder.result['shared_handover'] = self.shared_handover
        for c in ordered:
            if c.runner is not None: c.recorder.result['active_request'] = c.runner.request.summary()
        if self.total_transitions % 10 == 0 or any(c.runner is None for c in ordered): self.recorder.save()
        return (self.observation(), {n: self.f([0.]) for n in self.agent_names},
                {n: terminated for n in self.agent_names}, {n: truncated for n in self.agent_names},
                {'private_host': True, 'reward_semantics': 'unused interface placeholder; no learner'})

    def summary(self):
        actual = self.session.current_state()
        return {'case': self.case, 'num_envs': 1, 'robots': self.num_robots, 'tasks': self.num_tasks,
            'control_decimation': DECIMATION, 'dt': pc.DT, 'render_interval': 2,
            'total_transitions': self.total_transitions,
            'global_physics_ticks': (self.recorder.result.get('completed_physics_steps', actual['step'])
                                     if self.shared else actual['step']),
            'last_completed_guarded_tick': actual['step'],
            'render_count': actual['render_count'], 'request_count': len(self.claims),
            'bind_count': self.adapter.bind_count, 'continuation_count': self.adapter.continuation_count,
            'transaction_count': self.adapter.transition_count, 'delivered_count': len(self.deliveries),
            'setup_ticks': self.setup_ticks, 'partial_block_ticks': self.partial_block_ticks,
            'task_physics_ticks': self.recorder.result.get('completed_physics_steps', actual['step'])-self.setup_ticks,
            'shared_handover': copy.deepcopy(self.shared_handover) if self.shared else None,
            'terminal_finished': self.finished, 'cancel_consumed': self.cancel_consumed,
            'single_control_context': not self.dual, 'control_context_count': self.num_robots,
            'proxy_env_constructed': False,
            'feasibility_source': 'fixed local fixture allowlist; not arbitrary IK/obstacle or cross-owner reachability',
            'arm_reach_source': 'URDF chain translation norm sum including scanner offset; geometric bound only',
            'rebuilds': copy.deepcopy(self.rebuilds)}

