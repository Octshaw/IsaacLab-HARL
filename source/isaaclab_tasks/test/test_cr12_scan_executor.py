"""CPU protocol regression for the shared pose session; no Isaac or torch imports."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest import mock
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/environments'))
import _cr12_pose_control as pc
import _cr12_scan_executor as ex
import run_cr12_pose_target as entry
from _cr12_pose_continuation import FrozenPoseSegment


class ArrayTensor:
    """Only the copy/conversion protocol used at the native boundary."""
    def __init__(self, value):
        self.value = np.array(value, dtype=np.float32, copy=True)
    def __getitem__(self, key):
        return ArrayTensor(self.value[key])
    def cpu(self):
        return self
    def detach(self):
        return self
    def numpy(self):
        return self.value


class MemoryTrace:
    def __init__(self):
        self.rows = []
        self.count = 0
    def append(self, row):
        self.rows.append(copy.deepcopy(row))
        self.count += 1


class SessionTests(unittest.TestCase):
    def fixture(self, *, integration=True):
        # Exercise production methods while substituting only native/CUDA boundaries.
        s = ex.Cr12PoseControlSession.__new__(ex.Cr12PoseControlSession)
        s.app = object()
        s.sim = SimpleNamespace(clock=(2, 2*pc.DT))
        s.baseline = s.sim.clock
        s._clock_boundary = s.baseline
        s.index = 0
        s._phase = 'ready'
        s.failure = None
        s._sample_written = True
        s._latest_tick = None
        s._goal_ids = set()
        s.goal_id, s.goal_index, s.goal_start_step = None, 0, 0
        s.goal_start_physics_time = s.baseline[1]
        s.integration = integration
        s.continue_after_arrival = True
        s.continuation = None
        s._goal_submitted = not integration
        s.profile = pc.select_motion_profile('formal')
        s.q, s.dq = np.zeros(6, dtype=np.float32), np.zeros(6, dtype=np.float32)
        s.q_tensor, s.dq_tensor = ArrayTensor([s.q]), ArrayTensor([s.dq])
        from _cr12_asset_math import JOINT_LIMITS
        s.controller_ref = pc.CommandIntegrator(s.q, np.asarray(JOINT_LIMITS))
        s.poses = {'agv': np.eye(4), 'link_6': np.eye(4)}
        s.initial_scanner = pc.scanner_from_ee(s.poses['link_6'])
        s.actual_scanner = s.initial_scanner.copy()
        s.target = FrozenPoseSegment(s.initial_scanner, s.initial_scanner)
        s.controlled_time = 0.
        s.submitted_q, s.submitted_dq = [0.]*6, [0.]*6
        s.monitor = pc.PoseMonitor(s.profile)
        s.trace = MemoryTrace()
        s.counts = {key: 0 for key in ex.PoseTrace.GUARDS}
        s.stats = dict(guard_pass_counts=s.counts, submitted_target_checks=0, sanity_checks=0,
                      render_calls=0, maximum_forbidden_contact_n=0., maximum_root_translation_m=0.,
                      maximum_root_rotation_rad=0., minimum_arm_collision_z_m=1.,
                      q_min_rad=[0.]*6, q_max_rad=[0.]*6, max_abs_dq_rad_s=[0.]*6,
                      max_raw_dls_update_rad=0., max_command_step_rad=0., stable_samples=0,
                      stable_span_s=0., all_guards_passed=False)
        s.recorder = SimpleNamespace(result={'failures': [], 'secondary_failures': []},
                                     save=mock.Mock(), emit=mock.Mock(), secondary=mock.Mock())
        s.robot = SimpleNamespace(set_joint_position_target=mock.Mock(),
                                  set_joint_velocity_target=mock.Mock(),
                                  write_data_to_sim=mock.Mock(), update=mock.Mock())
        s.joint_ids, s.body_ids, s.mapping = list(range(6)), list(range(7)), {}
        s.controller = SimpleNamespace(set_command=mock.Mock(),
            compute=mock.Mock(side_effect=lambda *unused: ArrayTensor([s.q])))
        s.tensor = lambda value: ArrayTensor([value])
        s.model = SimpleNamespace(sanity_samples=lambda *unused: [('midpoint', s.poses), ('endpoint', s.poses)])
        s.adapter = {'reference_point': 'actor'}
        s.com = np.zeros(3)
        s.info, s.config = {'colliders': []}, SimpleNamespace(CONTACT_OFFSET=.002)
        s.stage, s.frames, s.initial_root = None, {}, np.eye(4)
        s.visuals = None
        s.contacts = {'sensor': {'updates': 0}}

        def contacts(*unused):
            s.contacts['sensor']['updates'] += 1
            return 0.
        replacements = {
            '_clock': lambda sim: sim.clock,
            '_assert_active': lambda *unused: None,
            '_native_jacobian': lambda *unused: (np.eye(6), {}),
            '_native_state': lambda *unused: (ArrayTensor([s.q]), ArrayTensor([s.dq])),
            '_body_poses': lambda *unused: copy.deepcopy(s.poses),
            '_check_frames': lambda *unused: (0., 0., {}),
            '_check_geometry': lambda *unused: 1.,
            '_check_contacts': contacts,
            '_capture_submitted_targets': lambda robot, ids, q, dq: (q.value[0].tolist(), dq.value[0].tolist()),
        }
        for name, replacement in replacements.items():
            patch = mock.patch.object(ex, name, replacement)
            patch.start()
            self.addCleanup(patch.stop)
        return s

    def advance(self, s, count=1, *, rendered=None):
        for _ in range(count):
            token = s.prepare_tick()
            s.submit_prepared(token)
            before = s.sim.clock
            s.sim.clock = (before[0] + 1, s.baseline[1] + (s.index+1)*pc.DT)
            context = s.observe_physics(before, s.sim.clock)
            tick = s.finish_tick(s.render_due if rendered is None else rendered)
        return context, tick

    def test_initial_state_and_goal_use_copies_without_control_reset(self):
        s = self.fixture()
        state = s.current_state()
        state['q'][0] = 7
        self.assertEqual(s.q[0], 0)
        control, integrator = s.controller, s.controller_ref
        record = s.submit_goal('claim_1', s.actual_scanner, s.current_state())
        self.assertIs(s.controller, control)
        self.assertIs(s.controller_ref, integrator)
        self.assertEqual(record['integrator_generation'], 0)
        self.assertEqual(s.sim.clock, s.baseline)

    def test_compute_proposal_has_no_writes_and_commit_once(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.controller.compute.side_effect = lambda *unused: ArrayTensor([s.q + .0001])
        token = s.prepare_tick()
        s.robot.write_data_to_sim.assert_not_called()
        self.assertEqual(s.controller_ref.generation, 0)
        s.submit_prepared(token)
        self.assertEqual(s.controller_ref.generation, 1)
        s.robot.write_data_to_sim.assert_called_once()
        s.robot.set_joint_position_target.assert_called_once()
        s.robot.set_joint_velocity_target.assert_called_once()
        np.testing.assert_array_equal(s.controller_ref.previous, token.q)
        np.testing.assert_array_equal(np.asarray(s.submitted_dq, dtype=np.float32), token.dq)

    def test_duplicate_submit_is_sticky_and_does_not_repeat_write(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        token = s.prepare_tick()
        s.submit_prepared(token)
        with self.assertRaises(pc.PoseCheckError):
            s.submit_prepared(token)
        s.robot.write_data_to_sim.assert_called_once()
        with self.assertRaises(pc.PoseCheckError):
            s.prepare_tick()
        self.assertEqual(s.phase, 'failed')

    def test_no_step_is_rejected_and_failure_row_survives(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.submit_prepared(s.prepare_tick())
        with self.assertRaises(Exception):
            s.observe_physics()
        self.assertEqual(s.trace.count, 1)
        self.assertEqual(s.trace.rows[0]['guard_clock'], 'FAIL')
        self.assertEqual(s.trace.rows[0]['status'], 'FAIL')
        self.assertIsNotNone(s.monitor.failure)

    def test_extra_step_is_rejected(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.submit_prepared(s.prepare_tick())
        s.sim.clock = (s.baseline[0]+2, s.baseline[1]+2*pc.DT)
        with self.assertRaises(Exception):
            s.observe_physics()
        self.assertEqual(s.recorder.result['completed_physics_steps'], 2)
        self.assertEqual(s.trace.count, 1)

    def test_poststep_context_current_and_finish_only_once(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        context, tick = self.advance(s)
        self.assertEqual(context['step'], 1)
        self.assertEqual(context['physics_time_s'], s.sim.clock[1])
        self.assertEqual(context['local_step'], 1)
        np.testing.assert_array_equal(context['q'], tick['q'])
        self.assertEqual(tick['render_count'], 0)
        _, tick = self.advance(s)
        self.assertEqual(tick['render_count'], 1)
        self.assertEqual(s.trace.count, 2)
        with self.assertRaises(pc.PoseCheckError):
            s.finish_tick(True)
        self.assertEqual(s.trace.count, 2)

    def test_wrong_render_parity_fails_closed(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        with self.assertRaises(pc.PoseCheckError):
            self.advance(s, rendered=True)
        self.assertEqual(s.trace.count, 1)
        self.assertEqual(s.phase, 'failed')

    def test_render_clock_advance_preserves_failure_row(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.submit_prepared(s.prepare_tick())
        s.sim.clock = (3, s.baseline[1]+pc.DT)
        s.observe_physics()
        s.sim.clock = (4, s.baseline[1]+2*pc.DT)
        with self.assertRaises(pc.PoseCheckError):
            s.finish_tick(False)
        self.assertEqual(s.trace.rows[0]['guard_render_clock'], 'FAIL')

    def test_arrived_hold_exceeds_pose_timeout_then_new_goal_restarts_window(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        _, arrived = self.advance(s, 600)
        self.assertTrue(arrived['pose_reached'])
        self.assertEqual(s.stats['stable_samples'], 121)
        monitor = s.monitor
        controller, integrator, anchor = s.controller, s.controller_ref, s.controller_ref.initial_q.copy()
        _, held = self.advance(s, 370)
        self.assertEqual(held['step'], 970)
        self.assertTrue(held['pose_reached'])
        self.assertEqual(monitor.last_step, 600)
        previous, generation = integrator.previous, integrator.generation
        changed_target = s.actual_scanner.copy()
        changed_target[0, 3] += .001
        s.submit_goal('claim_2', changed_target, s.current_state())
        self.assertEqual(s.monitor.last_step, 0)
        self.assertFalse(s.monitor.reached)
        self.assertIs(s.controller, controller)
        self.assertIs(s.controller_ref, integrator)
        np.testing.assert_array_equal(integrator.previous, previous)
        np.testing.assert_array_equal(integrator.initial_q, anchor)
        self.assertEqual(integrator.generation, generation)
        np.testing.assert_array_equal(s.target.reference(0), s.actual_scanner)
        _, tick = self.advance(s)
        self.assertEqual((tick['step'], tick['local_step'], tick['goal_id']), (971, 1, 'claim_2'))
        self.assertFalse(tick['pose_reached'])
        self.assertEqual(tick['render_count'], 485)

    def test_arrived_hold_violation_cannot_be_reclaimed(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.monitor.reached = True
        s.dq[0] = .011
        with self.assertRaises(Exception):
            self.advance(s)
        self.assertEqual(s.phase, 'failed')
        with self.assertRaises(pc.PoseCheckError):
            s.submit_goal('claim_2', s.actual_scanner)

    def test_primary_guard_failure_is_not_replaced_by_csv_failure(self):
        s = self.fixture()
        s.submit_goal('claim_1', s.actual_scanner)
        s.submit_prepared(s.prepare_tick())
        primary = pc.PoseCheckError('PHYSICS_GUARD', 'native failure')
        s.trace.append = mock.Mock(side_effect=OSError('CSV failure'))
        with mock.patch.object(ex, 'check_clock', side_effect=primary):
            with self.assertRaises(pc.PoseCheckError) as error:
                s.observe_physics()
        self.assertIs(error.exception, primary)
        s.recorder.secondary.assert_called_once()
        self.assertEqual(s.failure['message'], 'native failure')

    def test_stale_handoff_is_rejected(self):
        s = self.fixture()
        state = s.current_state()
        state['step'] += 1
        with self.assertRaises(pc.PoseCheckError):
            s.submit_goal('claim_1', s.actual_scanner, state)
        self.assertEqual(s.controller_ref.generation, 0)

    def test_original_two_view_context_uses_same_session_control_and_global_parity(self):
        from _cr12_pose_continuation import TwoViewPoseContinuation
        s = self.fixture(integration=False)
        ctx = TwoViewPoseContinuation(s.initial_scanner)
        ctx.bind_control(s.controller, s.controller_ref, s.baseline[1])
        s.continuation = ctx
        s.target = ctx.initial_target(s.initial_scanner)
        s.poses['link_6'] = pc.ee_from_scanner(s.target.target)
        _, tick = self.advance(s, 600)
        self.assertTrue(tick['pose_reached'])
        request = {'state': 'SUCCEEDED_OFF', 'goal_id': 'goal_1', 'acquired': True,
                   'artifact_saved': True, 'off_confirmed': True, 'failure': None}
        ctx.queue_goal_2(tick, completed_request=request)
        identity = id(s.controller), id(s.controller_ref)
        old_command = s.controller_ref.previous
        token = s.prepare_tick()
        self.assertEqual(ctx.goal_id, 'goal_2')
        self.assertEqual(s.monitor.last_step, 0)
        self.assertEqual((id(s.controller), id(s.controller_ref)), identity)
        np.testing.assert_array_equal(s.controller_ref.previous, old_command)
        np.testing.assert_array_equal(s.target.reference(0), tick['scanner'])
        self.assertAlmostEqual(s.reference_time, pc.DT)
        self.assertFalse(s.render_due)
        self.assertEqual(s.controller_ref.generation, 600)
        s.submit_prepared(token)
        self.assertEqual(s.controller_ref.generation, 601)


class StructureAndCompatibilityTests(unittest.TestCase):
    def test_executor_never_owns_step_render_reset_scene(self):
        tree = ast.parse((ROOT/'scripts/environments/_cr12_scan_executor.py').read_text(encoding='utf-8'))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertFalse(any(c.rsplit('.', 1)[-1] in
                             ('step', 'render', 'reset', 'write_joint_state_to_sim',
                              'create_fixed_cr12_scene', 'initialize_fixed_cr12_state') for c in calls))
        for name in ('DifferentialIKController', 'pc.CommandIntegrator', 'self.controller.compute',
                     'self.robot.set_joint_position_target', 'self.robot.set_joint_velocity_target',
                     'self.robot.write_data_to_sim', 'self.controller_ref.commit'):
            self.assertEqual(calls.count(name), 1, name)
        imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertNotIn('torch', '\n'.join(map(ast.unparse, imports)))
        self.assertNotIn('isaaclab', '\n'.join(map(ast.unparse, imports)))

    def test_original_wrapper_order_and_final_arrival_no_extra_tick(self):
        calls = []
        class FakeSession:
            def __init__(self, *args, **kwargs):
                self.sim = SimpleNamespace(step=lambda **kw: calls.append('step'),
                                           render=lambda: calls.append('render'))
                self.render_due = True
                self.kwargs = kwargs
                calls.append(kwargs)
            def prepare_tick(self):
                calls.append('prepare')
                return 'token'
            def submit_prepared(self, token):
                self.assert_token = token
                calls.append('submit')
            def observe_physics(self):
                calls.append('observe')
                return {'current': True}
            def finish_tick(self, rendered):
                calls.append('finish')
                return None
            def abort(self, exc):
                calls.append('abort')
        with mock.patch.object(entry, 'Cr12PoseControlSession', FakeSession):
            ticks = list(entry._pose_ticks(SimpleNamespace(motion_profile='formal'), None, None, {}, {},
                                          scene={}, initial={}, before_render=lambda ctx: calls.append('callback')))
        self.assertEqual(ticks, [])
        self.assertEqual(calls[1:], ['prepare', 'submit', 'step', 'observe', 'callback', 'render', 'finish'])
        self.assertFalse(calls[0]['continue_after_arrival'])
        self.assertFalse(calls[0]['integration'])
        self.assertIsNone(calls[0]['continuation'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

