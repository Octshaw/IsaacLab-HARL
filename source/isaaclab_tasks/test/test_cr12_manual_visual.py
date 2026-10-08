"""CPU-only manual profile and marker regressions; no simulator/controller execution."""

import ast
import contextlib
from dataclasses import FrozenInstanceError
import importlib.util
import io
import math
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[3]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/environments" / filename)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: module}):
        spec.loader.exec_module(module)
    return module


pc = load("_cr12_manual_control_cpu", "_cr12_pose_control.py")
visual = load("_cr12_manual_visual_cpu", "_cr12_pose_visuals.py")
URDF = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf"


def transform(axis=(0, 0, 1), angle=0, position=(0, 0, 0)):
    quaternion = np.r_[math.cos(angle/2), np.asarray(axis) * math.sin(angle/2)]
    return pc.pose_from_wxyz(position, quaternion)


class ManualProfileTests(unittest.TestCase):
    def setUp(self):
        self.model = pc.KinematicModel.from_derived_urdf(URDF)
        self.root = transform(position=[0, 0, .053])
        self.initial = pc.scanner_from_ee(self.model.forward(np.zeros(6), self.root)["link_6"])

    def test_default_is_formal_and_only_explicit_manual_selection_changes_time(self):
        formal = pc.select_motion_profile()
        self.assertIs(formal, pc.FORMAL_PROFILE)
        self.assertEqual(formal.name, "formal")
        self.assertFalse(formal.manual_visual_only)
        self.assertEqual((formal.reference_seconds, formal.max_seconds, formal.max_steps), (4.0, 8.0, 960))
        self.assertIsNone(formal.witness_deg)
        manual = pc.select_motion_profile("manual_visible_local_v1")
        self.assertTrue(manual.manual_visual_only)
        self.assertEqual((manual.reference_seconds, manual.max_seconds, manual.max_steps), (6.0, 10.0, 1200))
        for name in (None, "manual", "", "formal_pass"):
            with self.assertRaises(pc.PoseCheckError):
                pc.select_motion_profile(name)

    def test_witness_beta_and_profiles_are_fixed_not_caller_tunable(self):
        profile = pc.MANUAL_VISIBLE_LOCAL_V1
        self.assertEqual(profile.witness_deg, (0, 3, -4.5, 0, 4.5, 0))
        self.assertEqual(profile.beta, 1.0)
        self.assertLessEqual(max(map(abs, profile.witness_deg)), 4.75)
        self.assertGreaterEqual(5-max(map(abs, profile.witness_deg)), .25)
        with self.assertRaises(FrozenInstanceError):
            profile.name = "formal"
        with self.assertRaises(TypeError):
            pc.MotionProfile("manual_visible_local_v1", beta=.9)
        with self.assertRaises(TypeError):
            pc.FrozenManualPoseTarget(self.initial, self.root, self.model, beta=.9)

    def test_manual_target_root_fk_scanner_direction_and_nominal_amplitude(self):
        target = pc.FrozenManualPoseTarget(self.initial, self.root, self.model)
        witness = np.radians([0, 3, -4.5, 0, 4.5, 0])
        expected = self.root @ self.model.forward(witness, np.eye(4))["link_6"] @ pc.T_ES
        np.testing.assert_allclose(target.target, expected, atol=1e-14)
        distance, angle = pc.pose_error(self.initial, target.target)
        self.assertAlmostEqual(distance, .03210742368915616, places=13)
        self.assertAlmostEqual(math.degrees(angle), 3.0, places=11)
        self.assertTrue(.025 <= distance <= .040)
        self.assertTrue(math.radians(2) <= angle <= math.radians(4))
        margins = np.minimum(witness-pc.JOINT_LIMITS[:, 0], pc.JOINT_LIMITS[:, 1]-witness)
        self.assertGreater(float(np.min(margins)), math.radians(167))

    def test_actual_nonidentity_root_used_without_saved_world_pose(self):
        root = transform((0, 0, 1), 1.2, [3.2, -.8, .37])
        initial = pc.scanner_from_ee(self.model.forward(np.zeros(6), root)["link_6"])
        target = pc.FrozenManualPoseTarget(initial, root, self.model)
        root_local = pc.in_root(root, pc.ee_from_scanner(target.target))
        expected = self.model.forward(target.witness_q, np.eye(4))["link_6"]
        np.testing.assert_allclose(root_local, expected, atol=1e-13)
        nominal = pc.FrozenManualPoseTarget(self.initial, self.root, self.model)
        self.assertGreater(np.linalg.norm(target.target[:3, 3]-nominal.target[:3, 3]), 2)
        self.assertAlmostEqual(pc.pose_error(initial, target.target)[0], pc.pose_error(self.initial, nominal.target)[0], places=13)

    def test_manual_frozen_target_inputs_and_outputs_have_no_aliases(self):
        initial, root = self.initial.copy(), self.root.copy()
        target = pc.FrozenManualPoseTarget(initial, root, self.model)
        expected = target.target
        initial[:] = 0
        root[:] = 0
        target.target[:] = 0
        target.initial[:] = 0
        target.witness_q[:] = 0
        np.testing.assert_array_equal(target.target, expected)
        np.testing.assert_allclose(target.witness_q, np.radians([0, 3, -4.5, 0, 4.5, 0]))

    def test_manual_shortest_geodesic_six_second_endpoints_and_halfway(self):
        root = transform((0, 0, 1), .8, [1, -.4, .053])
        initial = pc.scanner_from_ee(self.model.forward(np.zeros(6), root)["link_6"])
        # A small actual-vs-nominal initial rotation makes this a generic geodesic.
        initial[:3, :3] = pc.rotation_axis_angle([1, 0, 0], .005) @ initial[:3, :3]
        target = pc.FrozenManualPoseTarget(initial, root, self.model)
        halfway = target.reference(3)
        np.testing.assert_allclose(target.reference(0), initial, atol=1e-14)
        np.testing.assert_allclose(target.reference(6), target.target, atol=1e-14)
        np.testing.assert_allclose(target.reference(10), target.target, atol=1e-14)
        self.assertAlmostEqual(pc.pose_error(initial, halfway)[1], pc.pose_error(initial, target.target)[1]/2, places=13)
        self.assertAlmostEqual(pc.pose_error(halfway, target.target)[1], pc.pose_error(initial, target.target)[1]/2, places=13)
        np.testing.assert_allclose(halfway[:3, 3], (initial[:3, 3]+target.target[:3, 3])/2, atol=1e-14)
        self.assertGreater(pc.pose_error(target.reference(4), target.target)[1], .001)
        self.assertLess(pc.pose_error(target.reference(pc.DT), initial)[1], 1e-7)
        neg_quaternion = -pc.pose_to_wxyz(initial)[1]
        signed_initial = pc.pose_from_wxyz(initial[:3, 3], neg_quaternion)
        signed = pc.FrozenManualPoseTarget(signed_initial, root, self.model)
        np.testing.assert_allclose(signed.reference(3), halfway, atol=1e-14)

    def test_zero_angle_manual_reference_is_finite(self):
        nominal = pc.FrozenManualPoseTarget(self.initial, self.root, self.model)
        zero = pc.FrozenManualPoseTarget(nominal.target, self.root, self.model)
        for time in (0, 3, 6):
            np.testing.assert_allclose(zero.reference(time), zero.target, atol=1e-14)

    def test_formal_target_still_one_degree_original_offset_four_seconds(self):
        target = pc.FrozenPoseTarget(self.initial)
        np.testing.assert_allclose(target.target[:3, 3]-self.initial[:3, 3], pc.TARGET_OFFSET, atol=1e-14)
        self.assertAlmostEqual(math.degrees(pc.pose_error(self.initial, target.target)[1]), 1.0, places=12)
        np.testing.assert_allclose(target.reference(4), target.target, atol=1e-14)
        self.assertAlmostEqual(math.degrees(pc.pose_error(self.initial, target.reference(2))[1]), .5, places=12)
        self.assertEqual(pc.PoseMonitor().profile.name, "formal")

    def test_manual_monitor_starts_stability_at_six_seconds_and_keeps_121_samples(self):
        monitor = pc.PoseMonitor(pc.MANUAL_VISIBLE_LOCAL_V1)
        for step in range(1, 840):
            result = monitor.observe(step, step*pc.DT, np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
            if step == 719:
                self.assertEqual(result["stable_count"], 0)
        self.assertEqual(result["stable_count"], 120)
        result = monitor.observe(840, 7.0, np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
        self.assertEqual(result["status"], "POSE_REACHED")
        self.assertNotIn("FORMAL", result["status"])
        self.assertEqual(result["stable_count"], 121)

    def test_manual_monitor_1200_budget_and_original_speed_tolerance(self):
        monitor = pc.PoseMonitor(pc.MANUAL_VISIBLE_LOCAL_V1)
        for step in range(1, 1200):
            monitor.observe(step, step*pc.DT, np.eye(4), np.eye(4), np.eye(4), np.full(6, .010001))
        self.assertFalse(monitor.reached)
        with self.assertRaises(pc.PoseCheckError) as caught:
            monitor.observe(1200, 10.0, np.eye(4), np.eye(4), np.eye(4), np.full(6, .010001))
        self.assertEqual(caught.exception.category, "TIMEOUT")
        self.assertEqual(monitor.last_sample["step"], 1200)

    def test_manual_uses_same_command_guard_no_profile_override(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        for ik in (np.full(6, .035001), np.full(6, math.radians(5.1))):
            with self.assertRaises(pc.PoseCheckError):
                integrator.propose(np.zeros(6), np.zeros(6), ik)
        with self.assertRaises(TypeError):
            pc.CommandIntegrator(np.zeros(6), profile=pc.MANUAL_VISIBLE_LOCAL_V1)
        np.testing.assert_array_equal(integrator.previous, np.zeros(6))


class ManualMarkerTests(unittest.TestCase):
    def setUp(self):
        self.actual = transform((0, 0, 1), math.radians(135), [.105, -.15, 2.888])
        self.target = transform((0, 1, 0), math.radians(3)) @ self.actual
        self.target[:3, 3] = self.actual[:3, 3] + [.0320770972763, 0, -.0013951653249]

    def test_marker_rgb_axis_endpoints_true_origins_and_no_input_mutation(self):
        initial_actual, initial_target = self.actual.copy(), self.target.copy()
        output = visual._marker_arrays(self.actual, self.target)
        self.assertEqual(output["marker_indices"], list(range(9)))
        self.assertEqual(output["translations"].shape, (9, 3))
        self.assertEqual(output["orientations"].shape, (9, 4))
        for base, pose, length in ((0, self.actual, .20), (3, self.target, .14)):
            for axis in range(3):
                index = base + axis
                center = output["translations"][index].astype(np.float64)
                rotation = pc.pose_from_wxyz([0, 0, 0], output["orientations"][index])[:3, :3]
                half = rotation[:, 2] * output["scales"][index, 2] / 2
                np.testing.assert_allclose(center-half, pose[:3, 3], atol=2e-7)
                np.testing.assert_allclose(center+half, pose[:3, 3]+length*pose[:3, axis], atol=2e-7)
        np.testing.assert_allclose(output["translations"][7], self.actual[:3, 3], atol=2e-7)
        np.testing.assert_allclose(output["translations"][8], self.target[:3, 3], atol=2e-7)
        np.testing.assert_array_equal(self.actual, initial_actual)
        np.testing.assert_array_equal(self.target, initial_target)

    def test_actual_target_line_endpoints_and_coincident_case(self):
        output = visual._marker_arrays(self.actual, self.target)
        center = output["translations"][6].astype(np.float64)
        rotation = pc.pose_from_wxyz([0, 0, 0], output["orientations"][6])[:3, :3]
        half = rotation[:, 2] * output["scales"][6, 2] / 2
        np.testing.assert_allclose(center-half, self.actual[:3, 3], atol=2e-7)
        np.testing.assert_allclose(center+half, self.target[:3, 3], atol=2e-7)
        zero = visual._marker_arrays(self.actual, self.actual)
        np.testing.assert_array_equal(zero["scales"][6], [0, 0, 0])
        self.assertTrue(np.isfinite(zero["orientations"]).all())

    def test_reference_marker_absent_and_origin_sizes_are_distinct(self):
        output = visual._marker_arrays(self.actual, self.target)
        self.assertEqual(len(output["marker_indices"]), 9)  # Six axes, one gap, two origins; no third frame.
        self.assertGreater(output["scales"][0, 2], output["scales"][3, 2])
        self.assertGreater(output["scales"][0, 0], output["scales"][3, 0])
        self.assertGreater(output["scales"][8, 0], output["scales"][7, 0])

    def test_wrist_and_arm_oblique_target_true_midpoint(self):
        midpoint = (self.actual[:3, 3]+self.target[:3, 3])/2
        wrist = visual.spectator_view(self.actual, "wrist-oblique", self.target)
        np.testing.assert_allclose(wrist["target"], midpoint, atol=1e-14)
        np.testing.assert_allclose(np.asarray(wrist["eye"])-midpoint, [.55, -.10, .42], atol=1e-14)
        arm = visual.spectator_view(self.actual, "arm-oblique", self.target)
        np.testing.assert_allclose(arm["target"], midpoint+[0, 0, -.75], atol=1e-14)
        np.testing.assert_allclose(np.asarray(arm["eye"])-arm["target"], [2.2, -2.6, 1.35], atol=1e-14)
        with self.assertRaises(ValueError):
            visual.spectator_view(self.actual, "wrist-oblique")

    def test_visual_helpers_only_consume_supplied_data_and_have_no_physics_calls(self):
        source = (ROOT / "scripts/environments/_cr12_pose_visuals.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        forbidden = {"step", "render", "reset", "write_joint_state_to_sim", "set_joint_position_target",
                     "set_joint_velocity_target", "update_articulations_kinematic", "sleep"}
        called = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(called & forbidden)
        # Top-level imports remain numpy/stdlib; Kit and marker APIs occur only inside runtime methods.
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        for node in imports:
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module]
            self.assertFalse(any(name.startswith(("isaac", "omni", "pxr")) for name in names))

    def test_invalid_marker_input_does_not_mutate_controller_target(self):
        before = self.target.copy()
        invalid = self.actual.copy()
        invalid[0, 0] = math.nan
        with self.assertRaises(ValueError):
            visual._marker_arrays(invalid, self.target)
        np.testing.assert_array_equal(self.target, before)


class ManualEntryBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.support = load("_cr12_runtime_support", "_cr12_runtime_support.py")
        with mock.patch.dict(sys.modules, {"_cr12_runtime_support": cls.support}), \
                mock.patch.object(sys, 'path', [str(ROOT / 'scripts/environments'), *sys.path]):
            cls.entry = load("_cr12_manual_entry_cpu", "run_cr12_pose_target.py")

    def test_manual_classification_never_claims_formal_pass(self):
        cases = {None: "MANUAL_VISUAL_MOTION_COMPLETED", "TIMEOUT": "MANUAL_VISUAL_MOTION_TIMEOUT",
                 "NO_PROGRESS": "MANUAL_VISUAL_MOTION_GUARD_FAIL", "DIVERGENCE": "MANUAL_VISUAL_MOTION_GUARD_FAIL",
                 "PHYSICS_GUARD": "MANUAL_VISUAL_MOTION_GUARD_FAIL", "COMMAND_REJECTED": "MANUAL_VISUAL_MOTION_GUARD_FAIL",
                 "SETUP": "MANUAL_VISUAL_RUNTIME_FAIL", "INFRASTRUCTURE": "MANUAL_VISUAL_RUNTIME_FAIL"}
        for category, expected in cases.items():
            self.assertEqual(self.entry.manual_motion_outcome(category), expected)
            self.assertNotIn("FORMAL", expected)

    def test_visual_false_does_not_import_or_construct_marker_runtime(self):
        tree = ast.parse((ROOT / "scripts/environments/run_cr12_pose_target.py").read_text(encoding="utf-8-sig"))
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_pose_ticks")
        # The original CLI only consumes default ticks; camera continuation is opt-in.
        wrapper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_run_pose")
        self.assertEqual(ast.unparse(wrapper.body[0].iter), "_pose_ticks(args, app, recorder, resources, expected)")
        defaults = dict(zip((arg.arg for arg in run.args.kwonlyargs), run.args.kw_defaults))
        self.assertIs(ast.literal_eval(defaults["continue_after_arrival"]), False)
        self.assertIsNone(ast.literal_eval(defaults["before_render"]))
        session_tree = ast.parse((ROOT / "scripts/environments/_cr12_scan_executor.py").read_text(encoding="utf-8"))
        session = next(node for node in session_tree.body if isinstance(node, ast.ClassDef)
                       and node.name == "Cr12PoseControlSession")
        guarded = []
        all_marker_sites = []
        for node in ast.walk(session):
            is_import = isinstance(node, ast.ImportFrom) and any(alias.name == "PoseDebugVisuals" for alias in node.names)
            is_create = isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "PoseDebugVisuals"
            if is_import or is_create:
                all_marker_sites.append(node)
            if isinstance(node, ast.If) and ast.unparse(node.test) == "self.args.visual_debug_pose":
                guarded.extend(ast.walk(ast.Module(body=node.body, type_ignores=[])))
        self.assertEqual(len(all_marker_sites), 2)
        self.assertTrue(all(node in guarded for node in all_marker_sites))
        # Runtime updates additionally require a successfully constructed, non-None marker object.
        update_sites = [node for node in ast.walk(session) if isinstance(node, ast.Call)
                        and ast.unparse(node.func) == "self.visuals.update"]
        guarded_updates = []
        for node in ast.walk(session):
            if isinstance(node, ast.If) and ast.unparse(node.test) == "self.visuals is not None":
                guarded_updates.extend(ast.walk(ast.Module(body=node.body, type_ignores=[])))
        self.assertTrue(update_sites)
        self.assertTrue(all(node in guarded_updates for node in update_sites))

    def test_visual_error_retained_separately_from_primary_motion_failure(self):
        recorder = self.support.Recorder()
        recorder.result.update(MANUAL_VISUAL_ONLY=True, visual_errors=["Synthetic marker failure"])
        primary = pc.PoseCheckError("PHYSICS_GUARD", "Synthetic contact remains primary")
        with contextlib.redirect_stdout(io.StringIO()):
            recorder.fail(primary)
        self.assertEqual(recorder.result["failures"][0]["category"], "PHYSICS_GUARD")
        self.assertEqual(recorder.result["failures"][0]["message"], str(primary))
        self.assertEqual(recorder.result["visual_errors"], ["Synthetic marker failure"])
        self.assertEqual(self.entry.manual_motion_outcome(recorder.result["failures"][0]["category"]),
                         "MANUAL_VISUAL_MOTION_GUARD_FAIL")

    def test_target_or_marker_error_cannot_mutate_existing_formal_target(self):
        formal = pc.FrozenPoseTarget(np.eye(4))
        expected = formal.target
        with self.assertRaises(pc.PoseCheckError):
            pc.FrozenManualPoseTarget(np.full((4, 4), math.nan), np.eye(4), None)
        with self.assertRaises(ValueError):
            visual._marker_arrays(np.full((4, 4), math.nan), expected)
        np.testing.assert_array_equal(formal.target, expected)
        # The shared entry refuses an already existing result before taking ownership of it.
        tree = ast.parse((ROOT / "scripts/environments/run_cr12_pose_target.py").read_text(encoding="utf-8-sig"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        guards = [node for node in ast.walk(main) if isinstance(node, ast.If)
                  and ast.unparse(node.test) == "result_path.exists()"]
        self.assertEqual(len(guards), 1)
        self.assertTrue(any(isinstance(node, ast.Raise) and "FileExistsError" in ast.unparse(node)
                            for node in ast.walk(guards[0])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
