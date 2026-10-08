"""Pure CPU geometry tests: no Isaac, USD, torch, rendering or physics imports."""

import ast
import copy
import itertools
import math
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts/environments"))
import _cr12_collision_refinement as geometry
from _cr12_asset_math import rpy_matrix
from _cr12_pose_control import KinematicModel

URDF = REPO / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf"


def pose(rotation=None, position=(0, 0, 0)):
    result = np.eye(4)
    if rotation is not None:
        result[:3, :3] = rotation
    result[:3, 3] = position
    return result


def box(center=(0, 0, 0), half=(.5, .5, .5), rotation=None):
    return {"center": np.asarray(center, dtype=np.float64), "half_extents": np.asarray(half, dtype=np.float64),
            "axes": np.eye(3) if rotation is None else rotation}


def corners(item):
    local = np.asarray(list(itertools.product(*zip(-item["half_extents"], item["half_extents"]))))
    return local @ item["axes"].T + item["center"]


def fixture():
    colliders = [{"path": f"/World/CR12/{body}/collisions/{name}/mesh", "body": body,
                  "local_bbox_min": [-.5, -.5, -.5], "local_bbox_max": [.5, .5, .5]}
                 for name, body in geometry.SHAPE_BODIES.items()]
    poses = {body: pose(position=(20*i, 0, 5)) for i, body in enumerate(geometry.BODY_NAMES)}
    return colliders, poses


class BoxMathTests(unittest.TestCase):
    def test_nonzero_local_center_nonidentity_rotation_eight_corners(self):
        lower, upper = np.array([1., 2., 3.]), np.array([2., 5., 7.])
        transform = pose(rpy_matrix((.3, -.4, .7)), (4, -2, 8))
        actual = geometry.box_from_bounds(lower, upper, transform)
        expected = np.array(list(itertools.product(*zip(lower, upper)))) @ transform[:3, :3].T + transform[:3, 3]
        np.testing.assert_allclose(corners(actual), expected, atol=2e-15)
        # No second scale/origin operation occurs inside box_from_bounds.
        np.testing.assert_allclose(actual["half_extents"], (upper-lower)/2)

    def test_aabb_overlap_but_obb_separates(self):
        rotation = rpy_matrix((0, 0, math.pi/4))
        a = box(half=(1., .1, .1), rotation=rotation)
        b = box(center=rotation[:, 1]*.3, half=(1., .1, .1), rotation=rotation)
        self.assertTrue(np.all(np.minimum(corners(a).max(0), corners(b).max(0)) > np.maximum(corners(a).min(0), corners(b).min(0))))
        result = geometry.pair_separation(a, b)
        self.assertTrue(result["separated"])
        self.assertFalse(result["contact_proven"])

    def test_overlap_containment_touch_and_tolerance_reject(self):
        for b in (box(center=(.8, 0, 0)), box(half=(.1, .1, .1)), box(center=(1, 0, 0))):
            self.assertFalse(geometry.pair_separation(box(), b, margin=0)["separated"])
        for gap in (0, .5e-6, 1e-6):
            self.assertFalse(geometry.pair_separation(box(), box(center=(1+gap, 0, 0)), margin=0)["separated"])
        self.assertTrue(geometry.pair_separation(box(), box(center=(1+2e-6, 0, 0)), margin=0)["separated"])

    def test_cross_axis_is_required(self):
        a = box(half=(.5643971311828444, .5575912007708316, .20000568439238792), rotation=np.array([
            [-.4700669334765423, .8172205883300498, .33344802902618453],
            [.8569794993473799, .5129993794635902, -.0491708691024014],
            [-.2112420785503542, .26264452531788796, -.9414853358232763]]))
        b = box(center=(-.2241853893722392, -.6588424930037977, .7869217278398586),
                half=(.26828714773503043, .538519480962039, .5814224586312791), rotation=np.array([
                    [-.31955184205917314, .33878955484982426, .8849340414749832],
                    [.20723579013307925, .9362782915076344, -.28361291955667967],
                    [-.9246296272154098, .09276097442461018, -.3693987738194176]]))
        # Independent vertex projections prove all six face tests fail.
        for axis in list(a["axes"].T) + list(b["axes"].T):
            pa, pb = corners(a) @ axis, corners(b) @ axis
            self.assertLess(max(pa.min()-pb.max(), pb.min()-pa.max()), 0)
        result = geometry.pair_separation(a, b)
        self.assertTrue(result["separated"])
        self.assertTrue(result["axis_source"].startswith("AxB"))
        self.assertEqual(result["tested_axes"], 15)

    def test_parallel_and_nearly_parallel_skip_is_not_pass(self):
        for rotation in (np.eye(3), rpy_matrix((1e-10, 0, 0))):
            result = geometry.pair_separation(box(), box(rotation=rotation))
            self.assertFalse(result["separated"])
            self.assertGreaterEqual(result["skipped_near_parallel_cross_axes"], 3)
            self.assertEqual(result["tested_axes"]+result["skipped_near_parallel_cross_axes"], 15)

    def test_world_margin_l1_by_independent_cube_corners(self):
        a = box(center=(3, -2, 7), half=(.7, .3, .2), rotation=rpy_matrix((.4, .8, -.5)))
        axis = np.array([1., 2., -3.]); axis /= np.linalg.norm(axis)
        cube = np.array(list(itertools.product((-.002, .002), repeat=3)))
        expanded = (corners(a)[:, None, :] + cube[None, :, :]).reshape(-1, 3)
        expected_radius = np.max((expanded-a["center"]) @ axis)
        self.assertAlmostEqual(geometry.projection_radius(a, axis), expected_radius, places=14)
        self.assertAlmostEqual(np.max(cube @ axis), .002*np.abs(axis).sum(), places=15)
        wrong_local = np.dot(a["half_extents"]+.002, abs(a["axes"].T @ axis))
        self.assertGreater(abs(wrong_local-expected_radius), 1e-5)

    def test_unexpanded_separation_is_removed_by_world_margin(self):
        a, b = box(), box(center=(1.003, 0, 0))
        self.assertTrue(geometry.pair_separation(a, b, margin=0)["separated"])
        self.assertFalse(geometry.pair_separation(a, b)["separated"])

    def test_pair_swap_symmetry(self):
        a = box(rotation=rpy_matrix((.3, .2, .7)))
        b = box(center=(1.1, .8, .2), half=(.2, .3, .7), rotation=rpy_matrix((.5, -.4, .1)))
        ab, ba = geometry.pair_separation(a, b), geometry.pair_separation(b, a)
        self.assertEqual(ab["separated"], ba["separated"])
        self.assertAlmostEqual(ab["gap_m"], ba["gap_m"], places=14)

    def test_zero_margin_common_rigid_transform_invariance(self):
        a, b = box(), box(center=(1.4, .8, -.2), rotation=rpy_matrix((.2, .8, -.4)))
        before = geometry.pair_separation(a, b, margin=0)
        rotation, translation = rpy_matrix((.5, -.2, .7)), np.array((3, -4, 2))
        for item in (a, b):
            item["center"] = rotation @ item["center"] + translation
            item["axes"] = rotation @ item["axes"]
        after = geometry.pair_separation(a, b, margin=0)
        self.assertEqual(before["separated"], after["separated"])
        self.assertAlmostEqual(before["gap_m"], after["gap_m"], places=14)

    def test_bad_rotations_nonfinite_and_shapes_rejected(self):
        for rotation in (np.diag((1, 1, -1)), np.diag((1, 1, 1.01)), np.array([[1, .1, 0], [0, 1, 0], [0, 0, 1]])):
            with self.assertRaises(ValueError):
                geometry.box_from_bounds([0]*3, [1]*3, pose(rotation))
        for values in ([0, 0, np.nan], [0, 0, np.inf], [0, 0]):
            with self.assertRaises(ValueError):
                geometry.box_from_bounds(values, [1]*3, np.eye(4))
        with self.assertRaises(ValueError):
            geometry.box_from_bounds([0]*3, [0, 1, 1], np.eye(4))


class FullGuardTests(unittest.TestCase):
    def test_all_pairs_exemptions_and_reordering(self):
        colliders, poses = fixture()
        result = geometry.GeometryGuard(colliders).check(poses)
        expected_exempt = sum(abs(geometry.BODY_NAMES.index(a["body"])-geometry.BODY_NAMES.index(b["body"])) <= 1
                              for a, b in itertools.combinations(colliders, 2))
        self.assertEqual(result["counters"]["total_shape_pairs"], 45)
        self.assertEqual(result["counters"]["exempt_pairs"], expected_exempt)
        self.assertEqual(result["counters"]["forbidden_pairs"], 45-expected_exempt)
        other = geometry.GeometryGuard(list(reversed(colliders))).check(dict(reversed(list(poses.items()))))
        self.assertEqual(result["counters"], other["counters"])

    def test_missing_duplicate_wrong_body_and_units(self):
        colliders, _ = fixture()
        variants = [colliders[:-1], colliders+[copy.deepcopy(colliders[0])]]
        for key, value in (("body", "link_5"), ("units", "mm"), ("bounds_frame", "mesh"), ("shape_id", "invented")):
            bad = copy.deepcopy(colliders); bad[-1][key] = value; variants.append(bad)
        bad = copy.deepcopy(colliders); bad[-1] = copy.deepcopy(bad[0]); variants.append(bad)
        for bad in variants:
            with self.assertRaises(geometry.GeometryRefinementError) as caught:
                geometry.GeometryGuard(bad)
            self.assertEqual(caught.exception.summary["status"], "INVALID_GEOMETRY")

    def test_missing_bad_pose_invalid_never_passes(self):
        colliders, poses = fixture()
        guard = geometry.GeometryGuard(colliders)
        bad = dict(poses); bad.pop("link_6")
        self.assertFalse(guard.inspect(bad)["input_valid"])
        bad = copy.deepcopy(poses); bad["link_2"][0, 0] = 1.01
        with self.assertRaises(geometry.GeometryRefinementError):
            guard.check(bad)

    def test_original_inputs_are_copied(self):
        colliders, poses = fixture()
        guard = geometry.GeometryGuard(colliders)
        colliders[-1]["local_bbox_max"][2] = float("nan")
        self.assertTrue(guard.check(poses)["passed"])

    def test_collect_all_unresolved_instead_of_first(self):
        colliders, poses = fixture()
        poses = {name: pose(position=(0, 0, 5)) for name in poses}
        result = geometry.GeometryGuard(colliders).inspect(poses)
        self.assertFalse(result["passed"])
        self.assertEqual(result["counters"]["unresolved_pairs"], result["counters"]["forbidden_pairs"])
        self.assertEqual(len(result["failures"]), result["counters"]["forbidden_pairs"])
        self.assertTrue(all(not item["contact_proven"] for item in result["failures"]))

    def test_original_unexpanded_ground_rule(self):
        colliders, poses = fixture()
        guard = geometry.GeometryGuard(colliders)
        poses["link_1"][2, 3] = .5  # Expanded box reaches -.002, raw box is exactly zero.
        self.assertTrue(guard.check(poses)["passed"])
        poses["link_1"][2, 3] = .5 - 2e-6
        result = guard.inspect(poses)
        self.assertFalse(result["passed"])
        self.assertEqual(result["counters"]["ground_failures"], 1)

    def test_aggregate_bounded_and_failure_sticky(self):
        colliders, poses = fixture(); guard = geometry.GeometryGuard(colliders)
        aggregate = geometry.GeometrySummary()
        good = guard.check(poses); aggregate.add(good)
        bad = guard.inspect({}); aggregate.add(bad); aggregate.add(good)
        result = aggregate.summary()
        self.assertEqual(result["checks"], 3)
        self.assertEqual(result["failed_checks"], 1)
        self.assertEqual(result["invalid_checks"], 1)
        self.assertFalse(result["input_valid"])
        self.assertEqual(result["counters"]["total_shape_pairs"], 90)
        result["counters"]["total_shape_pairs"] = 0
        self.assertEqual(aggregate.summary()["counters"]["total_shape_pairs"], 90)

    def test_old_default_policy_remains_explicit(self):
        source = (REPO / "scripts/environments/_cr12_runtime_support.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "initialize_fixed_cr12_state")
        defaults = dict(zip((arg.arg for arg in function.args.kwonlyargs), function.args.kw_defaults))
        self.assertIsNone(defaults["geometry_check"].value)
        self.assertIn("_check_geometry if geometry_check is None else geometry_check", ast.unparse(function))
        old = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_check_geometry")
        old_text = ast.unparse(old)
        self.assertIn("lo[2] < -1e-06", old_text)
        self.assertIn("np.minimum(left_hi, right_hi) - np.maximum(left_lo, right_lo) > 0", old_text)


class AcceptedAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = geometry.load_accepted_inputs(URDF)
        cls.model = KinematicModel.from_derived_urdf(URDF)

    def test_existing_inertials_and_collision_only_reader(self):
        self.assertEqual(len(self.inputs["bodies"]), 7)
        self.assertEqual(len(self.inputs["colliders"]), 10)
        self.assertAlmostEqual(self.inputs["bodies"]["agv"]["mass"], 63.44074938)
        self.assertTrue(all(item["kind"] == "collision" for items in self.inputs["geometries"].values() for item in items))
        source = ast.unparse(ast.parse(Path(geometry.__file__).read_text(encoding="utf-8")))
        self.assertNotIn("validate_derived(", source)
        self.assertNotIn("analyze_source(", source)
        self.assertNotIn("findall('visual')", source)

    def test_actual_link4_scanner_pair_by_independent_corner_projections(self):
        items = [next(item for item in self.inputs["colliders"] if item["shape_id"] == name)
                 for name in ("link_4_collision", "scanner_collision")]
        root = pose(position=(0, 0, .053))
        for degrees in (0, 10.6, 15, 20):
            q = np.zeros(6); q[2] = math.radians(degrees)
            poses = self.model.forward(q, root)
            boxes = [geometry.box_from_bounds(item["local_bbox_min"], item["local_bbox_max"], poses[item["body"]]) for item in items]
            axis = poses["link_4"][:3, 2]
            pa, pb = corners(boxes[0]) @ axis, corners(boxes[1]) @ axis
            independent_gap = max(pa.min()-pb.max(), pb.min()-pa.max()) - .004*np.abs(axis).sum()
            # This independently derived direction is a separation witness at each checkpoint.
            self.assertGreater(independent_gap, geometry.GAP_TOLERANCE_M)
            actual = geometry.pair_separation(*boxes)
            self.assertTrue(actual["separated"])
            self.assertGreaterEqual(actual["gap_m"]+1e-14, independent_gap)


if __name__ == "__main__":
    unittest.main()
