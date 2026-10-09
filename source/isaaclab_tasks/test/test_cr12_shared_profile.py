"""Targeted CPU checks for the one approved shared-task profile."""
from pathlib import Path
import math
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import _cr12_pose_control as pc
import _cr12_shared_task_profile as profile
import _cr12_camera_mount as mount

URDF = ROOT / 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf'


class SharedProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = pc.KinematicModel.from_derived_urdf(URDF)

    def test_frozen_pose_same_target_and_units(self):
        for robot in (0, 1):
            actual = pc.scanner_from_ee(self.model.forward(profile.goal_q(robot), profile.root_pose(robot))['link_6'])
            distance, angle = pc.pose_error(actual, profile.scanner_target())
            self.assertLess(distance, 1e-12)
            self.assertLess(angle, 1e-12)
        np.testing.assert_allclose(np.degrees(profile.initial_q(0)), [0, -16, 20, 0, -4, 90], atol=1e-13)
        np.testing.assert_allclose(profile.root_pose(1)[:3, 3], [1.0983385754148558, -.3, .053], atol=0)
        p = profile.scanner_target()[:3, 3]
        np.testing.assert_allclose(pc.pose_from_wxyz(p, profile.SCANNER_WXYZ), profile.scanner_target(), atol=1e-15)
        np.testing.assert_allclose(pc.pose_from_wxyz(p, -np.array(profile.SCANNER_WXYZ)), profile.scanner_target(), atol=1e-15)

    def test_accessors_do_not_mutate_frozen_inputs(self):
        first = profile.scanner_target(); first[:] = 0
        self.assertEqual(profile.scanner_target()[3, 3], 1)
        q = profile.initial_q(0); q[:] = 0
        self.assertNotEqual(profile.initial_q(0)[1], 0)
        with self.assertRaises(ValueError): profile.root_pose(True)
        with self.assertRaises(ValueError): profile.goal_q(2)

    def test_wrong_actual_root_does_not_redefine_target(self):
        frozen = profile.scanner_target()
        wrong = pc.scanner_from_ee(self.model.forward(profile.goal_q(1), profile.root_pose(0))['link_6'])
        # At this symmetric endpoint the positions coincide, but the complete
        # scanner orientation differs by pi; testing only position is unsafe.
        self.assertGreater(pc.pose_error(wrong, frozen)[1], 3.)
        np.testing.assert_array_equal(profile.scanner_target(), frozen)

    def test_three_fixed_references_and_park(self):
        for robot, kind in ((0, 'approach'), (0, 'retreat'), (1, 'approach')):
            item = profile.segment(self.model, robot, kind)
            np.testing.assert_allclose(item.reference(0), item.initial, atol=1e-15)
            np.testing.assert_allclose(item.reference(24), item.target, atol=1e-15)
            np.testing.assert_allclose(item.reference(100), item.target, atol=1e-15)
            midpoint = (profile.initial_q(robot)+profile.goal_q(robot))*.5
            np.testing.assert_allclose(item.reference(12), pc.scanner_from_ee(self.model.forward(midpoint, profile.root_pose(robot))['link_6']), atol=1e-15)
            with self.assertRaises(pc.PoseCheckError): item.reference(float('nan'))
        item = profile.segment(self.model, 0, 'park')
        np.testing.assert_array_equal(item.reference(12), profile.park_pose(self.model, 0))
        with self.assertRaises(ValueError): profile.segment(self.model, 1, 'retreat')

    def test_fixed_budgets_and_old_profiles_unchanged(self):
        for name, expected in (('formal', (4, 8, 960)), ('manual_visible_local_v1', (6, 10, 1200)),
                               (profile.PROFILE_NAME, (24, 32, 3840))):
            selected = pc.select_motion_profile(name)
            self.assertEqual((selected.reference_seconds, selected.max_seconds, selected.max_steps), expected)
        self.assertEqual(profile.REQUEST_STEPS, profile.POSE_STEPS+600+240)
        self.assertEqual(profile.A_BINDING_TICKS, profile.REQUEST_STEPS+profile.CLEANUP_STEPS)
        self.assertEqual(profile.TOTAL_CONTROLLED_TICKS, 360+1120*12)
        with self.assertRaises(pc.PoseCheckError): pc.select_motion_profile('shared_unbounded')

    def test_vector_trust_only_axes_two_five_and_anchor_unchanged(self):
        anchor = profile.initial_q(0)
        shared = pc.CommandIntegrator(anchor, profile=pc.SHARED_M2N1)
        for axis in range(6):
            q = anchor.copy(); q[axis] += math.radians(6)
            if axis in (1, 4): shared.check_actual(q, np.zeros(6))
            else:
                with self.assertRaises(pc.PoseCheckError): shared.check_actual(q, np.zeros(6))
        old = pc.CommandIntegrator(anchor)
        with self.assertRaises(pc.PoseCheckError): old.check_actual(profile.goal_q(0), np.zeros(6))
        np.testing.assert_array_equal(shared.initial_q, anchor)
        q = anchor.copy(); q[1] += math.radians(30.001)
        with self.assertRaises(pc.PoseCheckError): shared.check_actual(q, np.zeros(6))

    def test_common_progress_not_independent_axes_or_time(self):
        park, goal = profile.initial_q(0), profile.goal_q(0)
        actual = park+.3*(goal-park)
        result = pc.check_path_tube(actual, park, goal)
        self.assertLessEqual(result['s_interval'][0], .3)
        self.assertGreaterEqual(result['s_interval'][1], .3)
        actual[1] = park[1]+.7*(goal[1]-park[1])
        with self.assertRaises(pc.PoseCheckError): pc.check_path_tube(actual, park, goal)

    def test_tube_zero_axes_outside_endpoint_and_nonfinite(self):
        park, goal = profile.initial_q(0), profile.goal_q(0)
        for q in (park+np.array([.01, 0, 0, 0, 0, 0]), park-.1*(goal-park),
                  np.full(6, np.nan), np.zeros((1, 6))):
            with self.assertRaises(pc.PoseCheckError): pc.check_path_tube(q, park, goal)

    def test_clear_requires_fixed_neighborhood_and_command_is_separate(self):
        park, goal = profile.initial_q(0), profile.goal_q(0)
        pc.check_path_tube(goal, park, goal)
        with self.assertRaises(pc.PoseCheckError): pc.check_fixed_neighborhood(goal, park)
        pc.check_fixed_neighborhood(park, park)
        integrator = pc.CommandIntegrator(park, profile=pc.SHARED_M2N1)
        # q_IK can carry a >.5 degree correction; actual remains in fixed park.
        proposal = integrator.propose(park, np.zeros(6), park+np.array([0, 0, 0, .02, 0, 0]))
        self.assertGreater(proposal.raw_delta[3], math.radians(.5))
        integrator.commit(proposal, proposal.q, proposal.dq)
        np.testing.assert_array_equal(integrator.initial_q, park)
        with self.assertRaises(pc.PoseCheckError): integrator.propose(park, np.zeros(6), park+.04)

    def test_shared_fixture_optical_transform_is_once(self):
        config = mount.VirtualCameraConfig((.168921722410, -.129429244995, .192403900145), (0,0,0), (1,1,1), 'unused', 'unused')
        expected = profile.scanner_target() @ config.t_sc
        expected[:3, 3] += expected[:3, 0]*.5
        np.testing.assert_array_equal(mount.shared_fixture_pose(config, profile.scanner_target()), expected)
        with self.assertRaises(ValueError): mount.shared_fixture_pose(config, np.eye(4))


if __name__ == '__main__':
    unittest.main()
