"""Pure CPU fixed-target/continuation checks; no controller or simulator imports."""
import ast
import copy
import importlib.util
import math
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/environments'))
import _cr12_pose_control as pc
import _cr12_pose_continuation as continuation


def initial_pose():
    quaternion = np.array([.7, .1, .3, -.2])
    return pc.pose_from_wxyz([.2, -.3, 2.], quaternion/np.linalg.norm(quaternion))


def successful_request():
    return {'state': 'SUCCEEDED_OFF', 'goal_id': 'goal_1', 'acquired': True, 'artifact_saved': True,
            'off_confirmed': True, 'failure': None, 'frame': {'capture_id': 'capture_1'}}


class ContinuationTests(unittest.TestCase):
    def bound(self):
        initial = initial_pose()
        ctx = continuation.TwoViewPoseContinuation(initial)
        controller, integrator = object(), pc.CommandIntegrator(np.zeros(6))
        ctx.initial_target(initial)
        ctx.bind_control(controller, integrator, 2*pc.DT)
        return ctx, controller, integrator

    def boundary(self):
        ctx, controller, integrator = self.bound()
        actual = pc.FrozenPoseTarget(initial_pose()).target
        actual[:3, 3] += [.0002, -.0001, .00005]  # Latest actual differs from ideal and arrival.
        proposal = integrator.propose(np.zeros(6), np.zeros(6), np.full(6, .01))
        integrator.commit(proposal, proposal.q, proposal.dq)
        tick = {'step': 1, 'physics_time_s': 3*pc.DT, 'controlled_time_s': pc.DT,
                'scanner': actual, 'q': np.zeros(6), 'dq': np.zeros(6),
                'q_cmd': proposal.q.tolist(), 'dq_cmd': proposal.dq.tolist(), 'rendered': False,
                'pose_reached': True, 'local_step': 1, 'local_time_s': pc.DT, 'render_count': 0}
        ctx.observe_yield(tick)
        return ctx, controller, integrator, tick

    def activate(self, ctx, controller, integrator, tick):
        return ctx.activate_pending(global_step=tick['step'], physics_time=tick['physics_time_s'],
            actual_scanner=tick['scanner'], q=tick['q'], dq=tick['dq'], controller=controller, integrator=integrator)

    def test_targets_frozen_once_return_is_true_initial(self):
        start = initial_pose()
        original = start.copy()
        ctx = continuation.TwoViewPoseContinuation(start)
        start[:] = 0
        record = ctx.record()
        np.testing.assert_array_equal(record['targets'][1]['matrix'], original)
        expected = pc.FrozenPoseTarget(original).target
        np.testing.assert_array_equal(record['targets'][0]['matrix'], expected)
        record['targets'][1]['matrix'][0][3] = 999
        np.testing.assert_array_equal(ctx.record()['targets'][1]['matrix'], original)
        self.assertGreater(record['target_distance_m'], .01)
        self.assertAlmostEqual(record['target_angle_rad'], math.radians(1), places=12)

    def test_world_y_target_with_nonidentity_rotation_and_quaternion_sign(self):
        quaternion = np.array([.4, .3, -.2, .7])
        quaternion /= np.linalg.norm(quaternion)
        positive = pc.pose_from_wxyz([1, 2, 3], quaternion)
        negative = pc.pose_from_wxyz([1, 2, 3], -quaternion)
        a = continuation.TwoViewPoseContinuation(positive).record()
        b = continuation.TwoViewPoseContinuation(negative).record()
        np.testing.assert_array_equal(a['targets'][0]['matrix'], b['targets'][0]['matrix'])
        rotation = np.asarray(a['targets'][0]['matrix'])[:3, :3]
        np.testing.assert_allclose(rotation, pc.rotation_axis_angle([0, 1, 0], math.radians(1)) @ positive[:3, :3], atol=1e-15)

    def test_first_segment_is_original_formal_reference(self):
        ctx = continuation.TwoViewPoseContinuation(initial_pose())
        segment = ctx.initial_target(initial_pose())
        original = pc.FrozenPoseTarget(initial_pose())
        for time in (0, .1, 1, 2, 4, 9):
            np.testing.assert_array_equal(segment.reference(time), original.reference(time))

    def test_second_reference_from_latest_actual_not_first_target(self):
        ctx, controller, integrator, tick = self.boundary()
        ctx.queue_goal_2(tick, completed_request=successful_request())
        segment = self.activate(ctx, controller, integrator, tick)
        np.testing.assert_array_equal(segment.reference(0), tick['scanner'])
        np.testing.assert_allclose(segment.reference(4), initial_pose(), atol=1e-15)
        np.testing.assert_allclose(segment.reference(9), initial_pose(), atol=1e-15)
        self.assertGreater(pc.pose_error(segment.initial, pc.FrozenPoseTarget(initial_pose()).target)[0], 0)
        middle = segment.reference(2)
        np.testing.assert_allclose(middle[:3, 3], (segment.initial[:3, 3]+segment.target[:3, 3])/2, atol=1e-15)
        self.assertAlmostEqual(pc.pose_error(segment.initial, middle)[1], pc.pose_error(segment.initial, segment.target)[1]/2, places=12)

    def test_zero_rotation_reference_finite_and_no_alias(self):
        start = initial_pose()
        target = start.copy()
        target[:3, 3] += .001
        segment = continuation.FrozenPoseSegment(start, target)
        start[:] = math.nan
        target[:] = math.nan
        value = segment.reference(2)
        self.assertTrue(np.isfinite(value).all())
        value[:] = 100
        self.assertTrue(np.isfinite(segment.reference(2)).all())
        with self.assertRaises(pc.PoseCheckError):
            segment.reference(math.nan)

    def test_pending_handoff_copies_and_activates_only_on_next_tick(self):
        ctx, controller, integrator, tick = self.boundary()
        completed = successful_request()
        record = ctx.queue_goal_2(tick, completed_request=completed)
        self.assertEqual(ctx.goal_id, 'goal_1')
        self.assertTrue(ctx.record()['pending'])
        completed['frame']['capture_id'] = 'corrupted'
        record['q_cmd'][0] = 1
        self.assertEqual(ctx.record()['handoff']['submitted_after_request']['frame']['capture_id'], 'capture_1')
        before_command = integrator.previous
        generation = integrator.generation
        self.activate(ctx, controller, integrator, tick)
        self.assertEqual(ctx.goal_id, 'goal_2')
        self.assertEqual(ctx.goal_start_step, 1)
        self.assertEqual(ctx.goal_start_physics_time, tick['physics_time_s'])
        np.testing.assert_array_equal(integrator.previous, before_command)
        self.assertEqual(integrator.generation, generation)
        self.assertEqual(ctx.record()['handoff']['activation_count'], 1)

    def test_off_saved_fresh_and_no_failure_gate_next_goal(self):
        cases = ({'state': 'FAILED_OFF'}, {'acquired': False}, {'artifact_saved': False},
                 {'off_confirmed': False}, {'failure': {'category': 'IO'}}, {'goal_id': 'wrong'})
        for changes in cases:
            ctx, controller, integrator, tick = self.boundary()
            with self.assertRaises(pc.PoseCheckError):
                ctx.queue_goal_2(tick, completed_request={**successful_request(), **changes})
            self.assertIsNotNone(ctx.failure)
            self.assertEqual(ctx.goal_id, 'goal_1')

    def test_stale_sample_mutation_and_duplicate_queue_rejected(self):
        for key in ('step', 'q_cmd', 'scanner'):
            ctx, _, _, tick = self.boundary()
            bad = copy.deepcopy(tick)
            if key == 'step': bad[key] = 0
            elif key == 'q_cmd': bad[key][0] += .0001
            else: bad[key][0, 3] += .0001
            with self.assertRaises(pc.PoseCheckError):
                ctx.queue_goal_2(bad, completed_request=successful_request())
        ctx, _, _, tick = self.boundary()
        ctx.queue_goal_2(tick, completed_request=successful_request())
        with self.assertRaises(pc.PoseCheckError):
            ctx.queue_goal_2(tick, completed_request=successful_request())

    def test_controller_and_integrator_identity_cannot_change(self):
        for replacement in ('controller', 'integrator'):
            ctx, controller, integrator, tick = self.boundary()
            ctx.queue_goal_2(tick, completed_request=successful_request())
            if replacement == 'controller': controller = object()
            else: integrator = pc.CommandIntegrator(np.zeros(6))
            with self.assertRaises(pc.PoseCheckError):
                self.activate(ctx, controller, integrator, tick)

    def test_handoff_changed_clock_actual_or_submitted_offset_rejected(self):
        for key in ('physics_time_s', 'q', 'q_cmd'):
            ctx, controller, integrator, tick = self.boundary()
            ctx.queue_goal_2(tick, completed_request=successful_request())
            if key == 'physics_time_s': tick[key] += pc.DT
            elif key == 'q': tick[key][0] += .001
            else: integrator._previous[:] = 0  # Explicit forbidden caller fault.
            with self.assertRaises(pc.PoseCheckError):
                self.activate(ctx, controller, integrator, tick)

    def test_original_five_degree_trust_anchor_not_reset(self):
        ctx, controller, integrator, tick = self.boundary()
        initial_anchor = integrator.initial_q.copy()
        ctx.queue_goal_2(tick, completed_request=successful_request())
        self.activate(ctx, controller, integrator, tick)
        np.testing.assert_array_equal(integrator.initial_q, initial_anchor)
        with self.assertRaises(pc.PoseCheckError):
            integrator.check_actual(np.full(6, math.radians(5.01)), np.zeros(6))
        next_proposal = integrator.propose(np.zeros(6), np.zeros(6), np.zeros(6))
        np.testing.assert_array_equal(next_proposal.q, integrator.previous)
        self.assertTrue(np.any(next_proposal.q != 0))  # Existing carrying offset retained.

    def test_local_monitor_resets_but_global_step_render_phase_does_not(self):
        monitor = pc.PoseMonitor()
        for local in range(1, 601):
            result = monitor.observe(local, local*pc.DT, initial_pose(), initial_pose(), initial_pose(), np.zeros(6))
        self.assertEqual(result['status'], 'POSE_REACHED')
        monitor2 = pc.PoseMonitor()
        first = monitor2.observe(1, pc.DT, initial_pose(), initial_pose(), initial_pose(), np.zeros(6))
        self.assertEqual(first['stable_count'], 0)
        self.assertEqual(first['status'], 'RUNNING')
        ctx, controller, integrator, tick = self.boundary()  # Odd global boundary.
        ctx.queue_goal_2(tick, completed_request=successful_request())
        self.activate(ctx, controller, integrator, tick)
        next_tick = {**tick, 'step': 2, 'physics_time_s': 4*pc.DT, 'controlled_time_s': 2*pc.DT,
                     'local_step': 1, 'local_time_s': pc.DT, 'rendered': True, 'render_count': 1,
                     'pose_reached': False}
        ctx.observe_yield(next_tick)
        self.assertEqual(ctx.record()['last_global_step'], 2)
        self.assertEqual(ctx.record()['goal_start_step'], 1)
        with self.assertRaises(pc.PoseCheckError):
            ctx.observe_yield(next_tick)  # No reuse of the same post-step sample.

    def test_only_two_goals_and_sticky_failure(self):
        ctx, controller, integrator, tick = self.boundary()
        ctx.queue_goal_2(tick, completed_request=successful_request())
        self.activate(ctx, controller, integrator, tick)
        with self.assertRaises(pc.PoseCheckError):
            ctx.queue_goal_2(tick, completed_request=successful_request())
        first = ctx.failure.copy()
        ctx.fail('LATER', 'cannot overwrite first')
        self.assertEqual(ctx.failure, first)

    def test_initial_context_and_bind_cannot_be_replaced(self):
        ctx, controller, integrator = self.bound()
        with self.assertRaises(pc.PoseCheckError):
            ctx.bind_control(controller, integrator, 0.)
        ctx = continuation.TwoViewPoseContinuation(initial_pose())
        moved = initial_pose()
        moved[0, 3] += .001
        with self.assertRaises(pc.PoseCheckError):
            ctx.initial_target(moved)


class GeneratorStaticTests(unittest.TestCase):
    def test_one_controller_integrator_step_site_and_opt_in(self):
        source = (ROOT/'scripts/environments/run_cr12_pose_target.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        runner = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_pose_ticks')
        calls = [ast.unparse(n.func) for n in ast.walk(runner) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count('session.sim.step'), 1)
        self.assertEqual(calls.count('Cr12PoseControlSession'), 1)
        control_source = (ROOT/'scripts/environments/_cr12_scan_executor.py').read_text(encoding='utf-8')
        control_tree = ast.parse(control_source)
        calls = [ast.unparse(n.func) for n in ast.walk(control_tree) if isinstance(n, ast.Call)]
        for name in ('DifferentialIKController', 'pc.CommandIntegrator', 'self.robot.write_data_to_sim',
                     'self.robot.set_joint_position_target', 'self.robot.set_joint_velocity_target'):
            self.assertEqual(calls.count(name), 1, name)
        defaults = dict(zip((arg.arg for arg in runner.args.kwonlyargs), runner.args.kw_defaults))
        self.assertIsNone(ast.literal_eval(defaults['continuation']))
        self.assertIn("self.monitor.observe(self.sample['local_step'], self.sample['local_time_s']", control_source)
        self.assertIn('(self.index + 1) % 2 == 0', control_source)
        self.assertLess(control_source.index('self.continuation.activate_pending'), control_source.index('self.proposal = self.controller_ref.propose'))
        self.assertNotIn('self.controller_ref =', control_source[control_source.index('self.continuation.activate_pending'):])
        self.assertNotIn('sim.reset(', control_source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
