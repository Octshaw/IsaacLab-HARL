"""Fixed dual Host on real authority/FSM and explicitly fake physics/events.

These CPU fixtures prove orchestration contracts, never real robot motion.
"""
from __future__ import annotations

import copy
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import test_cr12_lifecycle_execution_adapter as contracts
import test_cr12_lifecycle_host as single
import test_cr12_camera_capture as events
import test_cr12_scan_executor as execution_tests
import _cr12_camera_capture as camera
import _cr12_capture_runner as runners
import _cr12_lifecycle_host as hosts
import _cr12_pose_control as pc
import run_cr12_single_view_capture as shared
import run_cr12_dual_lifecycle_integration as entry


class SharedSim:
    def __init__(self):
        self.current_time_step_index, self.current_time = 2, 2/120
        self.steps = self.renders = 0
        self.captures, self.runtimes, self.order = [], [], []
    def step(self, render=False):
        assert render is False
        self.order.append(('step', self.steps+1))
        self.steps += 1
        self.current_time_step_index += 1
        self.current_time = self.current_time_step_index/120
        for runtime in self.runtimes:
            runtime.source_now = Fraction(self.current_time_step_index, 120)
    def render(self):
        self.order.append(('render', self.steps))
        self.renders += 1
        for capture, runtime in zip(self.captures, self.runtimes):
            if capture.read_updates_enabled():
                runtime.stream.emit(events.event(capture.product_path,
                    self.current_time_step_index, runtime.source_now))


class FakeDualSession(single.FakeSession):
    def __init__(self, args, app, recorder, resources, expected, *, scene, initial,
                 integration, allow_unbound_hold, set_view):
        super().__init__(args, app, recorder, resources, expected, scene=scene, initial=initial,
                         integration=integration)
        self.robot_id = scene['robot_id']
        self.state['poses']['agv'][:3, 3] = (0., 2.*self.robot_id, .053)
        self.state['scanner'][:3, 3] = (.105, 2.*self.robot_id-.15, 2.888)
        self.state['poses']['link_6'] = self.state['scanner'].copy()
        self.target = self.state['target'] = self.state['scanner'].copy()
        self.goal_id = None
        self.idle = True
        self.fail_submit = False
        self.q, self.poses = self.state['q'], self.state['poses']
        self.model.sanity_samples = lambda *args: [('midpoint', self.poses), ('endpoint', self.poses)]
        self.stats = {'render_calls': 0}
        self.held_targets = []
    def submit_goal(self, *args, **kwargs):
        from _cr12_pose_continuation import FrozenPoseSegment
        super().submit_goal(*args, **kwargs)
        self.start = self.state['scanner'].copy()
        self.segment = FrozenPoseSegment(self.start, self.target)
        self.idle = False
    def enter_idle_hold(self):
        self.idle = True
        self.held_targets.append(self.target.copy())
    def prepare_tick(self):
        self.sim.order.append(('prepare', self.robot_id))
        return SimpleNamespace(q=self.state['q'].copy(), generation=self.state['step'])
    def submit_prepared(self, token):
        self.sim.order.append(('submit', self.robot_id))
        if self.fail_submit: raise RuntimeError('second submit failed')
        assert token.generation == self.state['step']
    def observe_physics(self, before, after):
        if not self.idle:
            u = min((self.sim.steps-self.goal_start)/480, 1.)
            self.state['scanner'] = self.segment.reference((self.sim.steps-self.goal_start)/120)
            self.state['q'][0] = .01*(self.submissions-1+u)
            self.state['q_cmd'][0] = self.state['q'][0]+.001
        self.state.update(step=self.sim.steps, physics_time_s=self.sim.current_time,
            controlled_time_s=self.sim.steps/120, target=self.target.copy(),
            local_step=self.sim.steps-self.goal_start, local_time_s=(self.sim.steps-self.goal_start)/120,
            goal_id=self.goal_id)
        self.render_due = self.sim.steps % 2 == 0
        return self.current_state()
    def finish_tick(self, rendered):
        tick = super().finish_tick(rendered)
        self.stats['render_calls'] = self.state['render_count']
        return tick


class DualFixture:
    def __init__(self, directory, order=(0, 1)):
        self.recorder, self.resources = single.QuietRecorder(), {}
        self.sim, self.stream = SharedSim(), events.Stream()
        self.args = SimpleNamespace(device='cpu', output_dir=Path(directory), integration_case=entry.CASE)
        self.config = SimpleNamespace(near_m=.01, far_m=10., horizontal_fov_deg=60.)
        self.runs = []
        for robot_id in order:
            runtime = events.runtime_fixture()
            runtime.stream = self.stream
            runtime.source_now = Fraction(2, 120)
            runtime.context = SimpleNamespace(get_rendering_event_stream=lambda: self.stream, get_stage_id=lambda: 7)
            runtime.product.path = f'/Render/Owned_R{robot_id}'
            runtime.product_path_for_name = lambda name, path=runtime.product.path: path
            runtime.prim_exists = lambda path: False
            runtime.product_camera_targets = lambda path, r=robot_id: [f'/World/CR12_{r}/Camera']
            context = {}
            capture = camera.OwnedCameraCapture.prepare(f'/World/CR12_{robot_id}/Camera', (4, 3),
                lambda context=context: context, runtime=runtime, max_requests=2, integration_mode=True,
                product_name=f'CR12_R{robot_id}_Capture', camera_name=f'camera{robot_id}', observer_name=f'obs{robot_id}')
            capture.initialize_off()
            self.sim.captures.append(capture); self.sim.runtimes.append(runtime)
            rec = single.QuietRecorder()
            rec.result['initialization'] = {'before_reset_clock': [0, 0.]}
            self.runs.append(dict(robot_id=robot_id, recorder=rec, resources={'capture': capture},
                scene={'sim': self.sim, 'robot': object(), 'robot_id': robot_id,
                       'root_path': f'/World/CR12_{robot_id}'}, initial={'baseline': (2, 2/120)},
                receive_context=context, mount_aggregate={'count': 0, 'maximum_position_error_m': 0.,
                    'maximum_orientation_error_rad': 0.}, initial_camera={}, initial_parameters={}))
        self.host = hosts.CR12IntegrationHost(self.args, None, self.recorder, self.resources, {}, self.config,
            setup=lambda: self.runs, session_factory=FakeDualSession, instance_specs=entry.instance_specs(),
            cross_checker=lambda *args: dict(logical_pairs=100, coarse_tests=1, coarse_separated=True,
                fine_pairs_checked=0, minimum_axis_gap_m=1., gap_basis='CPU FAKE'))
        d = self.host.domain
        runtime = contracts.S.EventProfileSynchronousRuntimeCoordinator(environment=self.host,
            current_read_port=d.current_read_port, production_claim_port=d.production_claim_port,
            physical_step_admission_port=d.physical_step_admission_port,
            standalone_reset_admission_port=d.standalone_reset_admission_port,
            terminal_consumer_port=d.terminal_consumer_port, fence_read_port=d.interstep_fence_read_port)
        self.facade = contracts.F._compose_event_assignment_runtime_facade(resolved_assignment_profile=self.host.profile,
            runtime_domain=d, synchronous_runtime=runtime)
        self.facade.reset()
    def step(self):
        h = self.host
        proposal = entry.next_proposals(h, self.facade.read_current())
        if proposal is None:
            return self.facade.step_without_new_claim(action_builder=h.bind_effective_assignment)
        p = h.assignment_problem()
        decision = self.facade.capture_proposal_decision(feasible_mask=p['feasible_mask'], cost_matrix=p['cost_matrix'])
        return self.facade.resolve_and_step_proposals(raw_action_ids=h.i([proposal[0]]),
            decoded_proposal=h.i([proposal[1]]), decision=decision, action_builder=h.bind_effective_assignment)


class DualHostTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(shared, 'native_validity', lambda *a: {'CPU_FAKE': True}))
        self.stack.enter_context(patch.object(runners, 'actual_camera_pose',
            lambda *a, **k: {'position_error_m': 0., 'orientation_error_rad': 0.}))
    def tearDown(self): self.stack.close()

    def test_full_stagger_real_authority_reversed_creation_order_and_one_clock(self):
        f = DualFixture(self.directory, order=(1, 0))
        while not f.host.finished: last = f.step()
        h = f.host
        self.assertEqual(f.sim.steps, h.total_transitions*12)
        self.assertEqual(f.sim.renders, f.sim.steps//2)
        self.assertEqual(len(h.claims), 4)
        self.assertEqual([r['task_id'] for r in h.claims], [0, 2, 1, 3])
        self.assertEqual(h.claims[0]['claim_token'], h.claims[1]['claim_token'])
        self.assertEqual(h.claims[3]['global_start_step']-h.claims[2]['global_start_step'], 72)
        self.assertEqual(len(last.terminal_historical_payload), 1)
        history = last.terminal_historical_payload[0]
        self.assertEqual(history.completion_count.tolist(), [2, 2])
        self.assertEqual(history.coverage_after_transition.tolist(), [True]*4)
        self.assertEqual(history.optional_sidecar.critic_dimension, 143)
        self.assertEqual(h.domain.terminal_consumer_port.capture_pending_terminal_artifacts(), ())
        self.assertTrue(entry.coverage_complete(h.parallel))
        self.assertGreater(h.parallel['simultaneous_actual_motion_ticks'], 0)
        self.assertEqual(len(h.parallel['off_a_fresh_b']), 1)
        self.assertEqual(h.cross_summary['actual_checks'], f.sim.steps)
        self.assertEqual(h.cross_summary['command_checks'], 2*f.sim.steps)
        self.assertEqual(len(list(Path(self.directory).glob('robot_*/task_*/claim_*/camera_rgba.png'))), 4)
        self.assertTrue(all(r.pending.custody is not None and not r.pending.custody.rgba.flags.writeable
                            for r in h.adapter.history))
        self.assertTrue(all(c.session.submissions == 2 for c in h._ordered()))
        self.assertIsNot(h.contexts[0].run['receive_context'], h.contexts[1].run['receive_context'])
        self.assertEqual(f.sim.order[:5], [('prepare', 0), ('prepare', 1), ('submit', 0), ('submit', 1), ('step', 1)])

    def test_second_submit_failure_never_steps_or_rolls_back_first_command(self):
        f = DualFixture(self.directory)
        f.host.contexts[1].session.fail_submit = True
        with self.assertRaisesRegex(RuntimeError, 'second submit failed'): f.step()
        self.assertEqual(f.sim.steps, 0)
        self.assertEqual(f.sim.order, [('prepare', 0), ('prepare', 1), ('submit', 0), ('submit', 1)])
        self.assertTrue(all(c.session.aborted for c in f.host._ordered()))

    def test_block_tail_degradation_prevents_both_C_and_stops_at_bad_tick(self):
        f = DualFixture(self.directory)
        f.host.contexts[1].session.tail_bad_at = 665
        with self.assertRaises(Exception):
            for _ in range(56): f.step()
        self.assertEqual(f.sim.steps, 665)
        self.assertEqual(f.recorder.result['completed_physics_steps'], 665)
        self.assertEqual(f.host.deliveries, [])
        self.assertIsNotNone(f.host.adapter.pending_result(0).custody)
        self.assertIsNotNone(f.host.adapter.pending_result(1).custody)

    def test_retirement_failure_preserves_entire_double_C_and_blocks_rebuild(self):
        f = DualFixture(self.directory)
        with patch.object(f.host.contexts[0].capture, 'retire_request', side_effect=RuntimeError('local retire')):
            with self.assertRaisesRegex(RuntimeError, 'local retire'):
                for _ in range(56): f.step()
        self.assertEqual(len(f.host.deliveries), 2)
        self.assertEqual(len(f.host.adapter.history), 2)
        self.assertFalse(f.host.finished)
        self.assertIsNotNone(f.host.contexts[1].runner)
        self.assertTrue(all(r.pending.custody is not None for r in f.host.adapter.history))

    def test_one_local_pair_complete_does_not_end_environment(self):
        f = DualFixture(self.directory)
        while not any(r['task_id'] == 1 for r in f.host.requests): f.step()
        self.assertFalse(f.host.finished)
        self.assertIsNone(f.host.contexts[0].runner)
        self.assertIsNotNone(f.host.contexts[1].runner)
        before = f.sim.steps
        target = f.host.contexts[0].session.target.copy()
        f.step()
        self.assertEqual(f.sim.steps, before+12)
        np.testing.assert_array_equal(f.host.contexts[0].session.target, target)
        self.assertNotEqual(int(f.host.domain.current_read_port.read_current().lifecycle_state.robot_state[0, 0]),
                            int(contracts.C.RobotLifecycleState.UNAVAILABLE))

    def test_business_completion_does_not_substitute_isolation_coverage(self):
        for facts in ({}, {'simultaneous_actual_motion_ticks': 1, 'mixed_stage_observed': True, 'off_a_fresh_b': []}):
            self.assertFalse(entry.coverage_complete(facts))


class FixedUnboundHoldTests(unittest.TestCase):
    def fixture(self):
        helper = execution_tests.SessionTests()
        self.addCleanup(helper.doCleanups)
        session = helper.fixture()
        session.allow_unbound_hold = True
        session._idle_hold = True
        return helper, session

    def test_initial_unbound_target_is_frozen_not_actual_chasing(self):
        helper, s = self.fixture()
        target = s.target.target.copy()
        s.poses['link_6'][0, 3] += .00001
        helper.advance(s, 2)
        np.testing.assert_array_equal(s.target.target, target)
        np.testing.assert_array_equal(s.reference, target)
        self.assertIsNone(s.goal_id)
        self.assertEqual(s.goal_index, 0)
        self.assertEqual(s.monitor.last_step, 0)
        self.assertEqual(s.observation['status'], 'IDLE_HOLD')

    def test_retired_hold_preserves_integrator_and_stops_old_monitor_deadline(self):
        helper, s = self.fixture()
        s.submit_goal('real_claim_1', s.actual_scanner)
        helper.advance(s, 600)
        target, integrator = s.target.target.copy(), s.controller_ref
        s.enter_idle_hold()
        helper.advance(s, 400)
        self.assertEqual(s.monitor.last_step, 600)
        self.assertEqual(s.index, 1000)
        np.testing.assert_array_equal(s.target.target, target)
        previous = integrator.previous
        s.submit_goal('real_claim_2', s.actual_scanner)
        self.assertIs(s.controller_ref, integrator)
        np.testing.assert_array_equal(integrator.previous, previous)
        self.assertFalse(s.monitor.reached)
        self.assertEqual(s.monitor.last_step, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
