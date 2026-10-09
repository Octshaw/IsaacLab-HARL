"""Targeted shared-profile executor protocol tests with CPU fake native boundaries."""
from pathlib import Path
import sys
import unittest
from unittest import mock
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/environments'))
import _cr12_pose_control as pc
import _cr12_shared_task_profile as sp
import _cr12_scan_executor as ex
import test_cr12_scan_executor as base_tests
from test_cr12_scan_executor import ArrayTensor

URDF=ROOT/'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf'


class SharedExecutorTests(unittest.TestCase):
    def fixture(self, robot=0):
        s=base_tests.SessionTests.fixture(self)
        s.shared_robot_id=robot
        s.allow_unbound_hold=True;s._idle_hold=True
        s._setup_phase='SETUP_PENDING';s._setup_stable_count=0
        s._setup_stable_start=None;s._setup_stable_now=False
        s.segment_start_step=0;s.segment_start_physics_time=s.baseline[1]
        s.control_segment_id=None;s.control_segment_kind=None
        s.profile=pc.select_motion_profile(sp.PROFILE_NAME)
        s.q=sp.initial_q(robot).astype(np.float32);s.dq=np.zeros(6,dtype=np.float32)
        s.q_tensor=ArrayTensor([s.q]);s.dq_tensor=ArrayTensor([s.dq])
        s.controller_ref=pc.CommandIntegrator(sp.initial_q(robot),profile=s.profile)
        s.submitted_q=s.controller_ref.previous.tolist()
        s.model=pc.KinematicModel.from_derived_urdf(URDF)
        s.poses=s.model.forward(s.q,sp.root_pose(robot));s.initial_root=sp.root_pose(robot)
        s.actual_scanner=pc.scanner_from_ee(s.poses['link_6'])
        s.target=sp.segment(s.model,robot,'park')
        s.scanner_task_target=sp.scanner_target();s.cleanup_target=s.target.target.copy()
        s.monitor=pc.PoseMonitor(s.profile)
        s.stats.update(q_min_rad=s.q.tolist(),q_max_rad=s.q.tolist())
        return s

    def advance(self,s,count=1):
        return base_tests.SessionTests.advance(self,s,count)

    def ready(self,s):
        s.begin_setup_hold();self.advance(s,121);s.complete_setup_hold()

    def pretend_arrived(self,s):
        # A fake valid guarded boundary, not a state-write implementation.
        s.q=sp.goal_q(s.shared_robot_id).astype(np.float32)
        s.q_tensor=ArrayTensor([s.q]);s.dq=np.zeros(6,dtype=np.float32)
        s.poses=s.model.forward(s.q,sp.root_pose(s.shared_robot_id))
        s.actual_scanner=pc.scanner_from_ee(s.poses['link_6'])
        s.monitor.reached=True

    def test_setup_must_begin_and_claim_waits_until_complete(self):
        s=self.fixture()
        with self.assertRaises(pc.PoseCheckError):s.prepare_tick()
        t=self.fixture()
        with self.assertRaises(pc.PoseCheckError):t.submit_goal('A',sp.scanner_target(),t.current_state())

    def test_setup_completion_rejects_unobserved_physics_advance(self):
        s=self.fixture();s.begin_setup_hold();self.advance(s,121)
        s.sim.clock=(s.sim.clock[0]+1,s.sim.clock[1]+pc.DT)
        with self.assertRaises(pc.PoseCheckError):s.complete_setup_hold()

    def test_setup_121_same_window_keeps_global_parity_and_control_memory(self):
        s=self.fixture();integ=s.controller_ref;controller=s.controller;anchor=integ.initial_q.copy()
        s.begin_setup_hold();self.advance(s,120)
        self.assertFalse(s.setup_hold_ready)
        _,tick=self.advance(s)
        self.assertTrue(s.setup_hold_ready);self.assertTrue(tick['setup_stable_now'])
        self.assertEqual(tick['step'],121);self.assertFalse(tick['rendered'])
        record=s.complete_setup_hold()
        self.assertEqual(record['setup_stable_samples'],121)
        previous=integ.previous.copy()
        s.submit_goal('A',sp.scanner_target(),s.current_state())
        self.assertIs(s.controller_ref,integ);self.assertIs(s.controller,controller)
        np.testing.assert_array_equal(integ.initial_q,anchor)
        np.testing.assert_array_equal(integ.previous,previous)
        self.assertEqual(integ.generation,121);self.assertEqual(s.goal_start_step,121)
        s.prepare_tick()
        self.assertAlmostEqual(s.reference_time,pc.DT)
        self.assertTrue(s.render_due)
        np.testing.assert_array_equal(s.reference,sp.segment(s.model,0).reference(pc.DT))

    def test_settling_allows_unstable_pose_but_not_unsafe_joint_tube(self):
        s=self.fixture();s.begin_setup_hold()
        s.poses['link_6'][0,3]+=.003
        self.advance(s,2)
        self.assertEqual(s._setup_stable_count,0)
        self.assertEqual(s.index,2)
        s.q[2]+=np.deg2rad(.51)
        with self.assertRaises(pc.PoseCheckError):s.prepare_tick()

    def test_settling_window_resets_then_qualified_hold_loss_stops(self):
        s=self.fixture();s.begin_setup_hold();self.advance(s,20)
        original=s.poses['link_6'].copy();s.poses['link_6'][0,3]+=.003
        self.advance(s);self.assertEqual(s._setup_stable_count,0)
        s.poses['link_6']=original;self.advance(s,121)
        self.assertTrue(s.setup_hold_ready)
        s.poses['link_6'][0,3]+=.003
        with self.assertRaises(pc.PoseCheckError):self.advance(s)
        self.assertEqual(s.recorder.result['completed_physics_steps'],143)
        self.assertEqual(s.trace.rows[-1]['status'],'FAIL')

    def test_setup_timeout_at360_preserves_failed_poststep(self):
        s=self.fixture();s.begin_setup_hold();s.poses['link_6'][0,3]+=.003
        with self.assertRaises(pc.PoseCheckError) as e:self.advance(s,360)
        self.assertEqual(e.exception.category,'SETUP_HOLD_FAIL')
        self.assertEqual(s.recorder.result['completed_physics_steps'],360)
        self.assertEqual(s.trace.count,360)
        self.assertEqual(s.failure['observed_physics_steps'],360)

    def test_actual_path_is_not_fixed_park_and_command_bias_is_allowed(self):
        s=self.fixture();self.ready(s)
        s.controller.compute.side_effect=lambda *unused:ArrayTensor([s.q+np.array([0,0,0,.03,0,0])])
        for _ in range(20):self.advance(s)
        self.assertAlmostEqual(s.current_state()['setup_stable_span_s'],1.)
        self.assertTrue(s.current_state()['setup_hold_completed'])
        self.assertGreater(abs(s.controller_ref.previous[3]),np.deg2rad(.5))
        self.assertAlmostEqual(s.q[3],0.)
        s.q=(sp.initial_q(0)+sp.goal_q(0))/2
        with self.assertRaises(pc.PoseCheckError):s._shared_actual_guard()

    def test_shared_target_is_exact_immutable_global_target(self):
        s=self.fixture();self.ready(s)
        changed=sp.scanner_target();changed[0,3]+=1e-9
        with self.assertRaises(pc.PoseCheckError):s.submit_goal('A',changed,s.current_state())

    def test_retreat_preserves_claim_clock_memory_and_fixed_anchor(self):
        s=self.fixture();self.ready(s);s.submit_goal('A',sp.scanner_target(),s.current_state())
        self.pretend_arrived(s)
        controller,integ=s.controller,s.controller_ref
        previous=integ.previous.copy();gen=integ.generation;goal_start=s.goal_start_step
        record=s.submit_bound_segment(latest_actual_boundary=s.current_state())
        self.assertEqual(record['control_segment_id'],'A:retreat')
        self.assertEqual(s.goal_id,'A');self.assertEqual(s.goal_start_step,goal_start)
        self.assertIs(s.controller,controller);self.assertIs(s.controller_ref,integ)
        np.testing.assert_array_equal(previous,integ.previous)
        self.assertEqual(integ.generation,gen);self.assertFalse(s.monitor.reached)
        np.testing.assert_array_equal(s.target.target,s.cleanup_target)
        np.testing.assert_array_equal(s.scanner_task_target,sp.scanner_target())
        self.assertEqual(s.current_state()['segment_step'],0)

    def test_retreat_rejects_stale_qcmd_and_unarrived_or_robot1(self):
        for robot,arrived,stale in ((0,False,False),(1,True,False),(0,True,True)):
            s=self.fixture(robot);self.ready(s)
            s.submit_goal('goal',sp.scanner_target(),s.current_state())
            if arrived:self.pretend_arrived(s)
            boundary=s.current_state()
            if stale:boundary['q_cmd'][0]+=.001
            with self.assertRaises(pc.PoseCheckError):s.submit_bound_segment(latest_actual_boundary=boundary)

    def test_retreat_monitor_uses_segment_tick_while_claim_age_continues(self):
        s=self.fixture();self.ready(s);s.submit_goal('A',sp.scanner_target(),s.current_state())
        self.pretend_arrived(s)
        # Model an already-admitted arrived boundary; no runtime state write API is called.
        s.controller_ref._previous=s.q.astype(np.float32)
        s.submitted_q=s.q.tolist()
        s.goal_start_step=s.index-20
        s.goal_start_physics_time=s._clock_boundary[1]-20*pc.DT
        s.submit_bound_segment(latest_actual_boundary=s.current_state())
        _,tick=self.advance(s)
        self.assertEqual(tick['segment_step'],1)
        self.assertEqual(tick['local_step'],21)
        self.assertEqual(tick['goal_id'],'A')
        self.assertEqual(s.monitor.last_step,1)
        self.assertAlmostEqual(s.monitor.last_sample['time'],pc.DT)
        np.testing.assert_array_equal(s.reference,sp.segment(s.model,0,'retreat').reference(pc.DT))
        np.testing.assert_array_equal(tick['scanner_task_target'],sp.scanner_target())

    def test_retreat_arrival_requires_fixed_clear_not_whole_path(self):
        s=self.fixture();self.ready(s);s.submit_goal('A',sp.scanner_target(),s.current_state())
        self.pretend_arrived(s);s.submit_bound_segment(latest_actual_boundary=s.current_state())
        s.monitor.reached=True
        with self.assertRaises(pc.PoseCheckError):s._shared_actual_guard()

    def test_setup_safety_failure_not_downgraded_to_settling(self):
        s=self.fixture();s.begin_setup_hold()
        with mock.patch.object(ex,'_check_contacts',side_effect=pc.PoseCheckError('PHYSICS_GUARD','contact')):
            with self.assertRaises(pc.PoseCheckError):self.advance(s)
        self.assertEqual(s.trace.rows[-1]['guard_contact'],'FAIL')
        self.assertEqual(s.recorder.result['completed_physics_steps'],1)
        self.assertEqual(s._setup_stable_count,0)

    def test_complete_setup_never_calls_domain_or_native_state_write(self):
        s=self.fixture();self.ready(s)
        self.assertEqual(s.robot.write_data_to_sim.call_count,121)
        self.assertEqual(s.monitor.last_step,0)
        self.assertIsNone(s.goal_id)
        self.assertEqual(s.controller_ref.generation,121)


if __name__=='__main__':unittest.main(verbosity=2)
