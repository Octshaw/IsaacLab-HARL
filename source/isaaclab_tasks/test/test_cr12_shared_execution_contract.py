"""Shared cancellation/clear contracts; real CPU authority, fake physical samples."""
from dataclasses import replace
from pathlib import Path
import copy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from test_cr12_lifecycle_execution_adapter import A, D, P, S, F, C, SC, TS, DEVICE, custody, i, ROOT

sys.path.insert(0, str(ROOT / 'scripts/environments'))
import _cr12_shared_task_profile as PROFILE
import _cr12_pose_control as PC
from _cr12_capture_runner import CaptureRequestRunner
from _cr12_single_view_capture import SingleViewRequest, CaptureRequestError
from _cr12_runtime_support import DriveCheckError


def physical_problem():
    positions = [PROFILE.scanner_target()[:3, 3].tolist()]
    return dict(num_envs=1, num_agents=2, agent_names=('cr12_0', 'cr12_1'),
        num_viewpoints=1, viewpoint_ids=(0,), base_pos=torch.tensor([PROFILE.ROOT_TRANSLATIONS]),
        base_yaw=torch.tensor([[0., np.pi]], dtype=torch.float32),
        scanner_pos=torch.tensor([positions * 2]), scanner_quat=torch.tensor([[[1., 0., 0., 0.]] * 2]),
        viewpoint_pos=torch.tensor([positions]), viewpoint_quat=torch.tensor([[[1., 0., 0., 0.]]]),
        arm_reach=torch.tensor([3., 3.]), scanner_min_range=torch.zeros(2), scanner_max_range=torch.ones(2)*5,
        scanner_fov_deg=torch.ones(2)*60, feasible_mask=torch.ones((1, 2, 1), dtype=torch.bool),
        cost_matrix=torch.zeros((1, 2, 1)))


def scale():
    return SC.build_event_policy_scale_contract_v2(M=2, N=1,
        ordered_agent_names=('cr12_0', 'cr12_1'), ordered_task_ids=(0,), scene_env_spacing=1.,
        sim_dt_seconds=1/120, control_decimation=12, episode_time_limit_seconds=112.)


class SharedAuthorityHost:
    """Fake physical boundaries through the unmocked production facade and domain."""
    def __init__(self):
        self.profile = P.resolve_assignment_profile('event_gated_local_mrta', P.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        self.domain = D._EventProfileLifecycleRuntimeDomain(D._EventProfileLifecycleDomainSpec(
            self.profile, device=DEVICE, env_ids=i([0]), num_robots=2, num_tasks=1))
        self.adapter = A.Cr12ExecutionAdapter(current_read_port=self.domain.current_read_port,
            run_instance_id='shared_cpu', execution_profile='shared_m2n1')
        self.validation = self.domain.environment_admission_validation_port
        self.port = self.domain.environment_port
        self.step_count = 120
        self.modes, self.overrides = {}, {}
        self.receipts, self.births = (), []
        self.auto_retire = True
        self.before_finalize = self.after_ack = self.before_bind = None
        runtime = S.EventProfileSynchronousRuntimeCoordinator(environment=self,
            current_read_port=self.domain.current_read_port, production_claim_port=self.domain.production_claim_port,
            physical_step_admission_port=self.domain.physical_step_admission_port,
            standalone_reset_admission_port=self.domain.standalone_reset_admission_port,
            terminal_consumer_port=self.domain.terminal_consumer_port, fence_read_port=self.domain.interstep_fence_read_port)
        self.facade = F._compose_event_assignment_runtime_facade(resolved_assignment_profile=self.profile,
            runtime_domain=self.domain, synchronous_runtime=runtime)
        self.facade.reset()

    def reset(self):
        self.validation.validate_reset_entry_for_active_call()
        if any(self.adapter.binding_for(r) or self.adapter.pending_result(r) for r in (0, 1)):
            raise RuntimeError('Live request forbids reset')
        with self.port.episode_rebuild(selected_env_ids=i([0]), initial_task_state=i([[int(C.TaskLifecycleState.AVAILABLE)]]),
                initial_robot_state=i([[int(C.RobotLifecycleState.NEEDS_ASSIGNMENT)]*2]), initial_ownership=i([[-1]])) as reset:
            reset.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        return {'cpu': torch.zeros((1, 1))}, {}

    def builder(self, environment, assignment):
        assert environment is self
        if self.before_bind: self.before_bind(self)
        entries = self.adapter.bind_effective_assignments(assignment)
        self.births.extend(b for b, new in entries if new)
        return tuple(b for b, _ in entries)

    def step(self, bindings):
        self.validation.validate_physical_step_entry_for_active_call()
        self.step_count += 12
        boundaries = {}
        for robot, binding in enumerate(bindings):
            mode = self.modes.get(robot)
            if mode:
                self.adapter.record_pending(binding, outcome=mode, acquired=mode != 'cancelled',
                    custody=None if mode == 'cancelled' else custody(binding), physics_step=self.step_count,
                    metadata={'cancellation_source': 'stable_waiting_data', 'camera_failure_category': 'CANCELLED',
                              'control_segment_id': 'bound_retreat'})
            b = A.ExecutionBoundaryEvidence(self.step_count, None if binding is None else binding.goal_id,
                None if binding is None else binding.capture_id, True, True, True, True, mode != 'completed', True)
            if mode == 'cancelled':
                b = replace(b, hold_basis='clear', control_segment_id='bound_retreat', physical_clear=True,
                    clear_stable_samples=121, clear_stable_span_s=1., clear_window_start_step=self.step_count-120,
                    clear_window_end_step=self.step_count, peer_park_verified=True, peer_physics_step=self.step_count)
            boundaries[robot] = replace(b, **self.overrides.get(robot, {}))
        current = self.domain.current_read_port.read_current()
        snapshot = TS.capture_pre_reset_critic_physical_snapshot_v2(assignment_problem=physical_problem(),
            episode_progress_steps=i([self.step_count//12]), scale_contract=scale(), physical_problem_source='CPU fake boundary')
        self.report = self.adapter.build_report(boundaries_by_robot=boundaries,
            coverage_before_transition=current.lifecycle_state.task_state == int(C.TaskLifecycleState.COMPLETED),
            physical_truncated=torch.zeros(1, dtype=torch.bool), time_limit_reached=torch.zeros(1, dtype=torch.bool),
            pre_reset_critic_physical_snapshot=snapshot)
        self.validation.validate_physical_finalization_for_active_call()
        if self.before_finalize: self.before_finalize(self)
        self.latest = self.port.finalize_execution_transition(self.report)
        self.receipts = self.adapter.ack_authority_deliveries(self.latest)
        if self.after_ack: self.after_ack(self)
        if self.auto_retire:
            for receipt in self.receipts: self.adapter.retire_request(receipt.binding, receipt)
        terminated, truncated = self.latest.terminated, self.latest.truncated
        if bool((terminated | truncated).any()): self.reset()
        return ({'cpu': torch.zeros((1, 1))}, {'cpu': torch.zeros(1)},
                {'cpu': terminated}, {'cpu': truncated}, {})

    def claim(self, raw, modes=None):
        self.modes = modes or {}
        problem = physical_problem()
        decision = self.facade.capture_proposal_decision(feasible_mask=problem['feasible_mask'], cost_matrix=problem['cost_matrix'])
        return self.facade.resolve_and_step_proposals(raw_action_ids=i([raw]),
            decoded_proposal=i([[-1 if x == 1 else x for x in raw]]), decision=decision, action_builder=self.builder)

    def advance(self, modes=None):
        self.modes = modes or {}
        return self.facade.step_without_new_claim(action_builder=self.builder)


class RealAuthorityTests(unittest.TestCase):
    def test_cancel_clear_release_then_other_robot_completes_real_terminal(self):
        h = SharedAuthorityHost(); h.claim([0, 1]); a = h.adapter.binding_for(0)
        h.advance(); self.assertIs(h.adapter.binding_for(0), a)
        self.assertIsNone(h.adapter.pending_result(0))
        h.advance({0: 'cancelled'})
        self.assertEqual(h.latest.result.updated_ownership.tolist(), [[-1]])
        self.assertFalse(bool(h.latest.result.updated_failed_pairs.any()))
        self.assertEqual(h.latest.published_view.lifecycle_state.completion_count.tolist(), [[0, 0]])
        result = h.claim([1, 0], {1: 'completed'}); b = h.births[-1]
        self.assertNotEqual(a.claim_token, b.claim_token)
        self.assertEqual((a.task_id, b.task_id, b.robot_id), (0, 0, 1))
        self.assertEqual(h.latest.published_view.lifecycle_state.completion_count.tolist(), [[0, 1]])
        self.assertTrue(bool(h.latest.terminated[0]))
        self.assertEqual(len(result.terminal_historical_payload), 1)
        self.assertEqual(len(h.domain.terminal_consumer_port.capture_pending_terminal_artifacts()), 0)
        self.assertEqual([r.pending.outcome for r in h.adapter.history], ['cancelled', 'completed'])
        self.assertFalse(h.adapter.history[-1].pending.custody.rgba.flags.writeable)
        descriptor = SC.build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale())
        self.assertEqual((descriptor['actor_schema']['dimension'], descriptor['critic_schema']['dimension']), (73, 71))

    def test_peer_cannot_claim_before_real_clear_release(self):
        h = SharedAuthorityHost(); h.claim([0, 1]); a = h.adapter.binding_for(0)
        result = h.claim([0, 0])
        self.assertEqual(result.admitted_effective_assignment.tolist(), [[0, -1]])
        self.assertIs(h.adapter.binding_for(0), a)
        self.assertIsNone(h.adapter.binding_for(1))

    def test_raw_no_claim_is_one_not_old_four(self):
        h = SharedAuthorityHost()
        with self.assertRaises(Exception): h.claim([0, 4])

    def test_each_clear_evidence_failure_rejects_before_authority_mutation(self):
        invalid = dict(hold_basis='scanner_task', physical_clear=False, clear_stable_samples=120,
            clear_stable_span_s=.99, clear_window_start_step=130, clear_window_end_step=120,
            peer_park_verified=False, peer_physics_step=0, control_segment_id=None,
            off_confirmed=False, no_pending_data=False)
        for field, value in invalid.items():
            with self.subTest(field=field):
                h = SharedAuthorityHost(); h.claim([0, 1]); h.overrides[0] = {field: value}
                before = h.domain.current_read_port.read_current().lifecycle_state.ownership.clone()
                with self.assertRaises(A.Cr12ExecutionAdapterError): h.advance({0: 'cancelled'})
                self.assertEqual(before.tolist(), [[0]])
                self.assertEqual(h.adapter.history, ())

    def test_no_completion_can_be_fabricated_for_cancelled_A(self):
        h = SharedAuthorityHost()
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, 'shared_completion_source'):
            h.claim([0, 1], {0: 'completed'})

    def test_retirement_before_receipt_rejected(self):
        h = SharedAuthorityHost(); h.claim([0, 1]); binding = h.adapter.binding_for(0)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, 'retire_before_receipt'):
            h.adapter.retire_request(binding, None)

    def test_duplicate_ack_and_post_receipt_failure_preserve_real_release(self):
        h = SharedAuthorityHost(); h.claim([0, 1]); h.auto_retire = False
        def failed_retirement(host):
            self.assertIs(host.adapter.ack_authority_deliveries(host.latest), host.receipts)
            raise RuntimeError('CPU local retirement failure')
        h.after_ack = failed_retirement
        with self.assertRaisesRegex(RuntimeError, 'retirement failure'): h.advance({0: 'cancelled'})
        self.assertEqual(len(h.adapter.history), 1)
        self.assertTrue(bool(h.latest.result.released_tasks[0, 0]))
        self.assertIsNotNone(h.adapter.binding_for(0))
        with self.assertRaises(Exception): h.advance()

    def test_old_A_result_cannot_touch_new_B_claim(self):
        h = SharedAuthorityHost(); h.claim([0, 1]); old = h.adapter.binding_for(0)
        h.advance({0: 'cancelled'}); h.claim([1, 0])
        def stale(host):
            host.adapter.record_pending(old, outcome='cancelled', acquired=False, custody=None,
                physics_step=host.step_count, metadata={})
        h.before_finalize = stale
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, 'result_binding'): h.advance()


class RequestBudgetTests(unittest.TestCase):
    def request(self, profile=None):
        return SingleViewRequest('g', 'a', '/p', 'c', delivery_policy='raw-held-with-custody', execution_profile=profile)

    def test_old_default_and_only_trusted_new_limits(self):
        old, new = self.request(), self.request('shared_m2n1')
        self.assertEqual((old.pose_steps, old.total_steps), (960, 1800))
        self.assertEqual((new.pose_steps, new.total_steps), (3840, 4680))
        with self.assertRaises(ValueError): self.request('arbitrary_long')

    def test_new_pose_endpoint_not_old960_and_next_tick_rejected(self):
        r = self.request('shared_m2n1'); r.start_motion({'updates_enabled': False}, 0)
        for step in range(1, 3841):
            r.observe_tick(dict(step=step, controlled_time_s=step/120, physics_time_s=step/120,
                                pose_reached=False), False, step/120)
        with self.assertRaisesRegex(CaptureRequestError, '3840'): r.check_before_tick(32.)
        self.assertEqual(r.failure['category'], 'POSE_TIMEOUT')

    def test_cancel_cannot_erase_acquisition(self):
        r = self.request('shared_m2n1'); r.state = 'WAITING_DATA'; r.acquired = True
        r.cancel(0.)
        self.assertTrue(r.acquired); self.assertIsNone(r.failure)
        self.assertTrue(r.cancel_requested['superseded_by_acquisition'])


class FakeCapture:
    product_path = '/owned_A_product'
    camera = object()
    def __init__(self): self.raw = None; self.errors = []; self.on = False; self.ids = None; self.accepted = False
    def summary(self): return {'unique_product_event_count': 0, 'request': self.ids}
    def assert_off(self, phase):
        if self.on: raise RuntimeError('fake product unexpectedly ON')
        return {'updates_enabled': False}
    def begin_capture(self, ids, boundary): self.ids = ids; self.on = True; return {'actual': True}
    def read_updates_enabled(self): return self.on
    def request_off(self, boundary): self.on = False
    def peek_retained_snapshot(self):
        return dict(snapshot=self.raw, raw_copy_present=self.raw is not None,
            fresh_identity_validated=self.raw is not None, fsm_acquired_accepted=self.accepted, errors=list(self.errors))
    def poll_snapshot(self): return self.raw
    def mark_snapshot_accepted(self, ids): self.accepted = True
    def observe_close(self, render_opportunity=False):
        return dict(confirmed=True, updates_enabled=False, opportunity_count=30, quiet_opportunities=30)
    def eligible_to_retire(self, ids, hold_verified):
        reasons = [] if hold_verified else ['latest_actual_hold_not_verified']
        return dict(eligible=not reasons, reasons=reasons, resource_healthy=not self.errors,
                    fresh_product_event_count=0, has_data=self.raw is not None)


class RunnerCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = PC.KinematicModel.from_derived_urdf(ROOT/'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.host = SharedAuthorityHost(); self.host.claim([0, 1]); self.binding = self.host.adapter.binding_for(0)
        self.capture = FakeCapture()
        self.sim = SimpleNamespace(current_time_step_index=0, current_time=0.)
        recorder = SimpleNamespace(emit=lambda *a, **k: None)
        start = self.tick(0)
        self.runner = CaptureRequestRunner(self.binding, self.capture, {'sim': self.sim, 'robot': object()}, None,
            start_tick=start, output_dir=Path(self.temp.name)/'request', recorder=recorder,
            mount_aggregate={'count': 0}, initial_camera=None, cancel_at_wait=True,
            execution_profile='shared_m2n1', shared_model=self.model)

    def tick(self, step, clear=False, reached=True):
        return dict(step=step, physics_time_s=step/120, q=PROFILE.clear_q(0) if clear else PROFILE.goal_q(0),
            dq=np.zeros(6), scanner=PROFILE.park_pose(self.model, 0) if clear else PROFILE.scanner_target(),
            target=PROFILE.park_pose(self.model, 0) if clear else PROFILE.scanner_target(),
            scanner_task_target=PROFILE.scanner_target(), goal_id=self.binding.goal_id,
            control_segment_id='retreat', q_cmd=PROFILE.goal_q(0).tolist(), rendered=False,
            pose_reached=reached, sample={'stable_samples': 121, 'stable_span_s': 1.,
                'target_position_error_m': 0., 'target_orientation_error_rad': 0.,
                **{'guard_'+n:'PASS' for n in ('clock','joint','contact','geometry','frame','render_clock')}})

    def peer(self, step):
        return dict(step=step, physics_time_s=step/120, q=PROFILE.initial_q(1), dq=np.zeros(6),
                    scanner=PROFILE.park_pose(self.model, 1))

    def observe(self, step, clear=False, reached=True):
        self.sim.current_time_step_index, self.sim.current_time = step, step/120
        self.runner.observe_tick(self.tick(step, clear, reached), peer_tick=self.peer(step),
            peer_status={k:True for k in ('off','resource_healthy','native_valid','guards_passed')})

    def cancel_and_retreat(self):
        self.observe(1)
        self.assertEqual(self.runner.request.state, 'WAITING_DATA')
        self.runner.before_tick(); self.observe(2)
        self.assertTrue(self.runner.needs_retreat); self.assertFalse(self.runner.delivery_ready)
        self.runner.begin_retreat('retreat', self.runner.latest_tick)

    def boundary(self):
        module = SimpleNamespace(native_validity=lambda *a: None)
        with patch.dict(sys.modules, {'run_cr12_single_view_capture': module}):
            return self.runner.boundary(peer_tick=self.peer(self.runner.latest_tick['step']),
                peer_status={k:True for k in ('off','resource_healthy','native_valid','guards_passed')})

    def test_camera_terminal_not_delivery_then_exact121_clear_samples(self):
        self.cancel_and_retreat()
        with self.assertRaisesRegex(DriveCheckError, 'Camera terminal'): self.runner.pending_metadata()
        for step in range(3, 123): self.observe(step, clear=True)
        self.assertFalse(self.runner.delivery_ready)
        self.observe(123, clear=True)
        self.assertTrue(self.runner.delivery_ready)
        b = self.boundary(); self.assertEqual(b.clear_stable_samples, 121)
        self.assertEqual((b.clear_window_start_step, b.clear_window_end_step), (3,123))
        self.assertEqual(self.runner.request.step, 2)  # terminal camera deadline is frozen
        self.assertIs(self.host.adapter.binding_for(0), self.binding)
        self.assertIsNone(self.host.adapter.pending_result(0))
        self.assertEqual(self.runner.pending_metadata()['camera_failure_category'], 'CANCELLED')

    def test_executor_arrival_required_even_with_clear_window(self):
        self.cancel_and_retreat()
        for step in range(3, 124): self.observe(step, clear=True, reached=False)
        self.assertFalse(self.runner.delivery_ready)

    def test_clear_tail_deterioration_rejects_and_no_pending_exists(self):
        self.cancel_and_retreat()
        for step in range(3, 124): self.observe(step, clear=True)
        bad = self.tick(124, clear=True); bad['dq'][0] = .011
        with self.assertRaises(DriveCheckError):
            self.runner.observe_tick(bad, peer_tick=self.peer(124),
                peer_status={k:True for k in ('off','resource_healthy','native_valid','guards_passed')})
        self.assertIsNone(self.host.adapter.pending_result(0))

    def test_wrong_peer_clock_or_fixed_neighborhood_rejected(self):
        self.cancel_and_retreat()
        with self.assertRaises(DriveCheckError):
            self.runner.observe_tick(self.tick(3, clear=True), peer_tick=self.peer(2), peer_status={})

    def test_late_raw_kept_and_classified_not_hit(self):
        self.cancel_and_retreat()
        raw = {'rgba':np.ones((2,2,4),np.uint8),'metadata':{'fresh':True}}
        self.capture.raw = raw
        with self.assertRaisesRegex(DriveCheckError, 'retained data'): self.observe(3, clear=True)
        self.assertIs(self.capture.raw, raw); self.assertTrue(self.runner.cancel_raced)

    def test_non_cancel_failure_cannot_start_bound_retreat(self):
        self.runner.request.state = 'FAILED_OFF'; self.runner.request.failure = {'category':'CAPTURE_TIMEOUT'}
        with self.assertRaises(DriveCheckError): self.runner.begin_retreat('retreat', self.runner.latest_tick)

    def test_changed_task_matrix_rejected(self):
        tick = self.tick(1); tick['scanner_task_target'][0,3] += .001
        with self.assertRaisesRegex(DriveCheckError, 'immutable'): self.runner.observe_tick(tick)

    def test_final_metadata_keeps_task_separate_from_clear(self):
        self.cancel_and_retreat()
        for step in range(3, 124): self.observe(step, clear=True)
        record = self.runner.finalize_record()
        self.assertEqual(record['pose_target'], PROFILE.scanner_target().tolist())
        self.assertNotEqual(record['pose_target'], record['cleanup_target'])


if __name__ == '__main__':
    unittest.main()
