"""CPU-only camera mounting/unit checks; no Kit imports or synthetic frame claims."""
import dataclasses
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import _cr12_pose_control as pc
import _cr12_camera_mount as cm

URDF = ROOT / 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf'


class MountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = cm.resolve_virtual_mount(URDF)

    def test_exact_source_bounds_and_single_scale(self):
        np.testing.assert_allclose(self.config.source_bounds_max_s_m, [.148921722410, .0375, .3848079834], atol=1e-12)
        self.assertAlmostEqual(self.config.translation_sc_m[0] - self.config.source_bounds_max_s_m[0], .02)
        np.testing.assert_allclose(self.config.t_ec[:3, 3], [-.027925398586, .210965992226, .192403900145], atol=1e-12)

    def test_world_optical_basis(self):
        t = cm.usd_camera_transform(np.eye(4))
        np.testing.assert_array_equal(t[:3, :3] @ [0, 0, -1], [1, 0, 0])
        np.testing.assert_array_equal(t[:3, :3] @ [0, 1, 0], [0, 0, 1])
        np.testing.assert_array_equal(t[:3, :3] @ [1, 0, 0], [0, -1, 0])

    def test_nonidentity_root_and_quaternion_sign(self):
        t = np.eye(4); t[:3, :3] = pc.rotation_axis_angle([1, 2, 3], .7); t[:3, 3] = [2, -3, .5]
        p, q = pc.pose_to_wxyz(t)
        for sign in (-1, 1):
            root = pc.pose_from_wxyz(p, sign*q)
            camera = root @ self.config.t_ec
            usd = cm.usd_camera_transform(camera)
            np.testing.assert_allclose(usd[:3, :3] @ [0, 0, -1], camera[:3, 0], atol=1e-12)
            np.testing.assert_allclose(usd[:3, :3] @ cm.WORLD_TO_USD_AXES.T, camera[:3, :3], atol=1e-12)
            np.testing.assert_allclose(usd[:3, 3], camera[:3, 3], atol=1e-12)

    def test_fixture_frozen_nominal_and_independent_of_actual(self):
        model = pc.KinematicModel.from_derived_urdf(URDF)
        root = pc.pose_from_wxyz([0, 0, .053], [1, 0, 0, 0])
        board = cm.nominal_fixture_pose(self.config, model, root)
        before = board.copy()
        actual = model.forward(np.array([0, .01, -.02, 0, .01, 0]), root)['link_6']
        self.assertGreater(np.linalg.norm(actual[:3, 3]), 0)
        np.testing.assert_array_equal(board, before)
        initial = pc.scanner_from_ee(model.forward(np.zeros(6), root)['link_6'])
        target = pc.FrozenPoseTarget(initial)
        expected_camera = target.target @ self.config.t_sc
        delta = np.linalg.inv(expected_camera) @ board
        np.testing.assert_allclose(delta[:3, 3], [.5, 0, 0], atol=1e-12)
        np.testing.assert_allclose(delta[:3, :3], np.eye(3), atol=1e-12)
        np.testing.assert_array_equal(target.target, pc.FrozenPoseTarget(initial).target)

    def test_optics_units_and_fov(self):
        record = self.config.record()
        self.assertAlmostEqual(self.config.focal_length_m, .031176914536239792)
        self.assertAlmostEqual(record['expected_intrinsics_px'][0][0], 554.2562584220408)
        self.assertAlmostEqual(2*np.degrees(np.arctan(.036/(2*self.config.focal_length_m))), 60)
        self.assertEqual(record['resolution'], (640, 480))
        self.assertEqual(record['channel'], 'RGBA')

    def test_immutable_and_defensive_transforms(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.config.near_m = .1
        one = self.config.t_sc; one[0, 3] = 99
        self.assertNotEqual(self.config.t_sc[0, 3], 99)


if __name__ == '__main__':
    unittest.main()
