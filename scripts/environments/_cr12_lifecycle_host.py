"""Private E1/M1/N2 CR12 host using the retained production lifecycle domain.

The host owns the only twelve-substep clock. No legacy proxy environment, RL
policy, task-state dictionary, or alternative authority is constructed here.
"""
from __future__ import annotations

import copy
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
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_cr12_execution_adapter import Cr12ExecutionAdapter, RawCaptureCustody
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_event_policy_scale_contract_v2
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_terminal_critic_sidecar import capture_pre_reset_critic_physical_snapshot_v2

DECIMATION = 12
CASE_LIMITS = {'normal': (320, 2), 'cancel_then_reclaim': (480, 3)}


def tensor_list(value):
    return value.detach().cpu().tolist()


def publication_summary(pub):
    state = pub.lifecycle_state
    return {'store_version': pub.store_version, 'episode_generation': tensor_list(pub.episode_generation),
            'transition_generation': tensor_list(pub.transition_generation),
            'task_state': tensor_list(state.task_state), 'robot_state': tensor_list(state.robot_state),
            'ownership': tensor_list(state.ownership), 'completion_count': tensor_list(state.completion_count),
            'failed_pairs': tensor_list(state.cumulative_failed_pairs),
            'result_present': pub.result is not None, 'termination_reason': tensor_list(state.termination_reason)}


class CR12IntegrationHost:
    def __init__(self, args, app, recorder, resources, expected, camera_config, *,
                 setup=None, session_factory=Cr12PoseControlSession, runner_factory=CaptureRequestRunner):
        self.args, self.app, self.recorder, self.resources = args, app, recorder, resources
        self.expected, self.config = expected, camera_config
        self.device = torch.device(args.device)
        self.case = args.integration_case
        self.horizon, self.request_limit = CASE_LIMITS[self.case]
        self._setup, self._session_factory, self._runner_factory = setup, session_factory, runner_factory
        self.profile = resolve_assignment_profile('event_gated_local_mrta',
                            AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        self.domain = _EventProfileLifecycleRuntimeDomain(_EventProfileLifecycleDomainSpec(
            self.profile, device=self.device, env_ids=self.i([0]), num_robots=1, num_tasks=2))
        self.validation = self.domain.environment_admission_validation_port
        self.lifecycle = self.domain.environment_port
        self.adapter = Cr12ExecutionAdapter(current_read_port=self.domain.current_read_port,
                                             run_instance_id=args.output_dir.name)
        self.scale = build_event_policy_scale_contract_v2(M=1, N=2,
            ordered_agent_names=('cr12',), ordered_task_ids=(0, 1), scene_env_spacing=1.,
            sim_dt_seconds=pc.DT, control_decimation=DECIMATION, episode_time_limit_seconds=self.horizon*.1)
        self.run = self.session = self.runner = None
        self.total_transitions = self.episode_steps = 0
        self.finished = False
        self.cancel_consumed = False
        self.requests = []
        self.claims = []
        self.deliveries = []
        self.rebuilds = []
        self.terminal_before_reset = None
        self._action_binding = None
        self.identities = []
        self.start_wall = time.monotonic()

    def i(self, data): return torch.tensor(data, dtype=torch.int64, device=self.device)
    def f(self, data): return torch.tensor(data, dtype=torch.float32, device=self.device)
    def b(self, data): return torch.tensor(data, dtype=torch.bool, device=self.device)

    def _reset_args(self):
        return dict(selected_env_ids=self.i([0]), initial_task_state=self.i([[int(TaskLifecycleState.AVAILABLE)]*2]),
                    initial_robot_state=self.i([[int(RobotLifecycleState.NEEDS_ASSIGNMENT)]]),
                    initial_ownership=self.i([[-1, -1]]))

    def _new_episode_context(self):
        actual = self.session.current_state()
        self.episode_context = {
            'generation': tensor_list(self.domain.current_read_port.read_current().episode_generation),
            'initial_actual_scanner': actual['scanner'].copy(),
            'initial_actual_q': actual['q'].copy(), 'initial_q_cmd': actual['q_cmd'].copy(),
            'global_step_origin': actual['step'], 'pending_goal': None}
        self.episode_steps = 0

    def reset(self):
        if self.run is not None:
            raise DriveCheckError('reset_scope', 'Only initial standalone reset is supported')
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(**self._reset_args()) as rebuild:
            if self._setup is None:
                from run_cr12_single_view_capture import initialize_capture_run
                self.run = initialize_capture_run(self.args, self.app, self.recorder, self.resources,
                    self.expected, self.config, camera_request_limit=self.request_limit, camera_integration=True)
            else:
                self.run = self._setup()
            self.scene, self.initial = self.run['scene'], self.run['initial']
            self.capture = self.resources['capture']
            self.session = self._session_factory(self.args, self.app, self.recorder, self.resources,
                self.expected, scene=self.scene, initial=self.initial, integration=True)
            actual = self.session.current_state()
            original = actual['scanner'].copy()
            first = pc.FrozenPoseTarget(original).target
            self.targets = (first, original)
            for target in self.targets: target.setflags(write=False)
            self.recorder.result['frozen_tasks'] = [
                {'task_id': i, 'matrix': t.tolist(), 'position_m': pc.pose_to_wxyz(t)[0].tolist(),
                 'quaternion_wxyz': pc.pose_to_wxyz(t)[1].tolist()} for i, t in enumerate(self.targets)]
            self.arm_reach = float(sum(np.linalg.norm(v) for v in self.session.model.origins)
                                   + np.linalg.norm(pc.scanner_from_ee(np.eye(4))[:3, 3]))
            self.identities.append(self.capture.device_identity())
            before, after = self.recorder.result['initialization']['before_reset_clock'], self.initial['baseline']
            if after[0]-before[0] > 2:
                raise DriveCheckError('initialization_budget', 'More than two initialization physics ticks')
            # Context exists before reset completion; final generation observed after commit.
            self.episode_context = {'initial_actual_scanner': original.copy(), 'global_step_origin': actual['step']}
            rebuild.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        self._new_episode_context()
        self.rebuilds.append({'kind': 'initial', 'publication': publication_summary(self.domain.current_read_port.read_current()),
                              'physics_clock': list(_clock(self.scene['sim']))})
        return self.observation(), {'private_execution_backend': 'cr12'}

    def observation(self):
        actual = self.session.current_state()
        p, q = pc.pose_to_wxyz(actual['scanner'])
        # Actual seven-component pose for this private synchronous host; no RL network/reward.
        return {'cr12': self.f([np.concatenate((p, q)).tolist()])}

    def assignment_problem(self):
        actual = self.session.current_state()
        scanner_p, scanner_q = pc.pose_to_wxyz(actual['scanner'])
        base = actual['poses']['agv']
        targets = [pc.pose_to_wxyz(t) for t in self.targets]
        return dict(num_envs=1, num_agents=1, agent_names=('cr12',), num_viewpoints=2, viewpoint_ids=(0, 1),
            base_pos=self.f([[base[:3, 3].tolist()]]),
            base_yaw=self.f([[math.atan2(base[1, 0], base[0, 0])]]),
            scanner_pos=self.f([[scanner_p.tolist()]]), scanner_quat=self.f([[scanner_q.tolist()]]),
            viewpoint_pos=self.f([[p.tolist() for p, _ in targets]]),
            viewpoint_quat=self.f([[q.tolist() for _, q in targets]]),
            arm_reach=self.f([self.arm_reach]), scanner_min_range=self.f([self.config.near_m]),
            scanner_max_range=self.f([self.config.far_m]), scanner_fov_deg=self.f([self.config.horizontal_fov_deg]),
            feasible_mask=self.b([[[True, True]]]),
            cost_matrix=self.f([[[float(np.linalg.norm(scanner_p-p)) for p, _ in targets]]]))

    def bind_effective_assignment(self, environment, assignment):
        if environment is not self or self.finished:
            raise DriveCheckError('host_identity', 'Unexpected host or post-terminal step')
        binding, is_new = self.adapter.bind_effective_assignment(assignment)
        if binding is None:
            raise DriveCheckError('assignment_missing', 'Bounded case requires a real active claim')
        if is_new:
            if self.runner is not None or len(self.claims) >= self.request_limit:
                raise DriveCheckError('request_budget', 'Previous request remains or request budget exhausted')
            # Reserve the complete original request budget plus block-tail allowance.
            if (self.horizon-self.episode_steps)*DECIMATION < 1800+DECIMATION:
                raise DriveCheckError('case_budget', 'Insufficient time to admit a safe bounded request')
            actual = self.session.current_state()
            self.session.submit_goal(binding.goal_id, self.targets[binding.task_id],
                                     latest_actual_boundary=actual)
            self.runner = self._runner_factory(binding, self.capture, self.scene, self.config,
                start_tick=actual, output_dir=self.args.output_dir / f'request_{len(self.claims)+1:02d}',
                recorder=self.recorder, mount_aggregate=self.run['mount_aggregate'],
                initial_camera=self.run['initial_camera'],
                cancel_at_wait=self.case == 'cancel_then_reclaim' and not self.cancel_consumed)
            self.resources['request'] = self.runner.request
            self.claims.append({**binding.summary(), 'global_start_step': actual['step'],
                'q_cmd_at_accept': np.asarray(actual['q_cmd']).tolist(), 'actual_scanner_at_accept': actual['scanner'].tolist(),
                'target_matrix': self.targets[binding.task_id].tolist()})
            self.recorder.emit('authority_claim_bound', **self.claims[-1])
        self._action_binding = binding
        return binding

    def _deliver(self, outcome):
        receipt = self.adapter.ack_authority_delivery(outcome)
        if receipt is None:
            return
        runner, binding = self.runner, self.runner.binding
        runner.record['authority_receipt'] = receipt.summary()
        runner.record['authority_after'] = publication_summary(self.domain.current_read_port.read_current())
        self.deliveries.append(receipt.summary())  # preserve commit even if recheck/retire fails
        self.recorder.result['authority_deliveries'] = self.deliveries
        runner.boundary()  # no step: recheck before local retirement, after commit.
        def validate(candidate, ids):
            return (candidate is receipt and candidate.binding is binding and candidate.pending is self.adapter.pending_result()
                    and ids == runner.request.ids and candidate.result is outcome.result)
        self.capture.retire_request(runner.request.ids, authority_receipt=receipt,
                                    receipt_validator=validate, hold_verified=True)
        runner.retired = True
        self.adapter.retire_request(binding, receipt)
        runner.record['retired_after_receipt'] = True
        runner.record['receipt_then_retire_step'] = runner.latest_tick['step']
        row = runner.finalize_record()
        self.requests.append(row)
        self.resources['last_integration_request'] = runner.request
        if runner.cancel_issued:
            self.cancel_consumed = True
        self.identities.append(self.capture.device_identity())
        self.recorder.emit('authority_result_delivered_and_retired', **receipt.summary())
        self.runner = None
        self._action_binding = None

    def _logical_rebuild(self, outcome):
        if self.runner is not None or self.adapter.binding is not None:
            raise DriveCheckError('terminal_live_request', 'Terminal rebuild requires receipt-backed retirement')
        current = self.domain.current_read_port.read_current()
        if int(current.lifecycle_state.robot_state[0, 0]) == int(RobotLifecycleState.UNAVAILABLE):
            raise DriveCheckError('unsafe_terminal', 'Unavailable robot cannot become healthy through reset')
        self.terminal_before_reset = publication_summary(current)
        self.terminal_before_reset.update(facts_consume_token=tensor_list(outcome.result.facts_consume_token),
                                         authority_receipt_id=tensor_list(outcome.result.authority_receipt_id))
        before = self.session.current_state()
        clock_before = _clock(self.scene['sim'])
        self.capture.assert_off('terminal_rebuild')
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(**self._reset_args()) as rebuild:
            self.episode_context = {'initial_actual_scanner': before['scanner'].copy(),
                                    'initial_actual_q': before['q'].copy(), 'initial_q_cmd': before['q_cmd'].copy(),
                                    'global_step_origin': before['step'], 'pending_goal': None}
            self.episode_steps = 0
            rebuild.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        self.episode_context['generation'] = tensor_list(self.domain.current_read_port.read_current().episode_generation)
        after = self.session.current_state()
        same = clock_before == _clock(self.scene['sim']) and all(
            np.array_equal(before[k], after[k]) for k in ('q', 'dq', 'q_cmd', 'scanner'))
        if not same:
            raise DriveCheckError('reset_state_changed', 'Logical rebuild changed physics or control state')
        self.rebuilds.append({'kind': 'safe_terminal_logical', 'physics_unchanged': same,
            'clock_before': list(clock_before), 'clock_after': list(_clock(self.scene['sim'])),
            'new_publication': publication_summary(self.domain.current_read_port.read_current())})
        self.finished = True

    def step(self, binding):
        from run_cr12_single_view_capture import native_validity, receive_context_callback
        self.validation.validate_physical_step_entry_for_active_call()
        if binding is not self._action_binding or self.runner is None:
            raise DriveCheckError('admission_identity', 'Step did not receive its admitted request')
        if self.total_transitions >= self.horizon:
            raise DriveCheckError('case_budget', 'Host transition limit reached')
        runner = self.runner
        before_render = receive_context_callback(self.initial, self.run['receive_context'])
        for _ in range(DECIMATION):
            try:
                runner.before_tick()
                native_validity(self.scene['robot'], self.scene['sim'])
                token = self.session.prepare_tick()
                self.session.submit_prepared(token)
                before = _clock(self.scene['sim'])
                self.scene['sim'].step(render=False)
                after = _clock(self.scene['sim'])
                context = self.session.observe_physics(before, after)
                rendered = self.session.render_due
                if rendered:
                    before_render(context)
                    self.scene['sim'].render()
                tick = self.session.finish_tick(rendered)
                self.resources['latest_capture_tick'] = tick
                runner.observe_tick(tick)
            except BaseException as exc:
                self.session.abort(exc)
                raise
            if runner.terminal and not runner.pending_recorded:
                if runner.request.failure is not None and runner.request.failure['category'] != 'CANCELLED':
                    raise DriveCheckError('unexpected_request_failure', str(runner.request.failure))
                custody = (None if runner.snapshot is None else RawCaptureCustody(
                    rgba=runner.snapshot['rgba'], metadata=runner.snapshot['metadata']))
                self.adapter.record_pending(binding,
                    outcome='completed' if runner.request.acquired else 'cancelled',
                    acquired=runner.request.acquired, custody=custody, physics_step=tick['step'],
                    metadata={'request': runner.request.summary(), 'terminal_physics_step': tick['step']})
                runner.pending_recorded = True
        boundary = runner.boundary()
        self.total_transitions += 1
        self.episode_steps += 1
        current = self.domain.current_read_port.read_current()
        coverage = current.lifecycle_state.task_state == int(TaskLifecycleState.COMPLETED)
        physical = capture_pre_reset_critic_physical_snapshot_v2(
            assignment_problem=self.assignment_problem(), episode_progress_steps=self.i([self.episode_steps]),
            scale_contract=self.scale, physical_problem_source='CR12IntegrationHost.assignment_problem guarded actual state')
        # No unsafe late time-limit synthetic terminal. Hard request/case limits fail closed.
        deadline = self.episode_steps >= self.horizon
        if deadline and not (runner.terminal and boundary.off_confirmed and boundary.holding and boundary.resource_healthy):
            raise DriveCheckError('case_deadline', 'Cannot publish a healthy terminal at an unsafe deadline')
        self.validation.validate_physical_finalization_for_active_call()
        report = self.adapter.build_report(boundary=boundary, coverage_before_transition=coverage,
            physical_truncated=self.b([deadline]), time_limit_reached=self.b([deadline]),
            pre_reset_critic_physical_snapshot=physical)
        outcome = self.lifecycle.finalize_execution_transition(report)
        try:
            self._deliver(outcome)
            terminated, truncated = outcome.terminated, outcome.truncated
            if bool((terminated | truncated).any()):
                self._logical_rebuild(outcome)
        except BaseException as exc:
            self.lifecycle.report_post_authority_bookkeeping_failure(outcome, exc)
            raise
        self.recorder.result.update(host_summary=self.summary(), requests=self.requests,
                                    authority_claims=self.claims, authority_deliveries=self.deliveries)
        if self.runner is not None:
            self.recorder.result['active_request'] = self.runner.request.summary()
        if self.total_transitions % 10 == 0 or self.runner is None:
            self.recorder.save()
        return (self.observation(), {'cr12': self.f([0.])}, {'cr12': terminated},
                {'cr12': truncated}, {'private_host': True, 'reward_semantics': 'unused interface placeholder; no learner'})

    def summary(self):
        actual = self.session.current_state()
        return {'case': self.case, 'num_envs': 1, 'robots': 1, 'tasks': 2,
            'control_decimation': DECIMATION, 'dt': pc.DT, 'render_interval': 2,
            'total_transitions': self.total_transitions, 'global_physics_ticks': actual['step'],
            'render_count': actual['render_count'], 'request_count': len(self.claims),
            'bind_count': self.adapter.bind_count, 'continuation_count': self.adapter.continuation_count,
            'transaction_count': self.adapter.transition_count, 'delivered_count': len(self.deliveries),
            'terminal_finished': self.finished, 'cancel_consumed': self.cancel_consumed,
            'single_control_context': True, 'proxy_env_constructed': False,
            'feasibility_source': 'only the accepted fixed local task0 and task1; not arbitrary IK/obstacle feasibility',
            'arm_reach_source': 'URDF chain translation norm sum including scanner offset; geometric bound only',
            'rebuilds': copy.deepcopy(self.rebuilds)}

