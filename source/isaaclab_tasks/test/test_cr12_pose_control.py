"""Synthetic CPU checks for CR12 pose execution; never import Isaac, torch or a controller."""

import importlib.util
import contextlib
import csv
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("_cr12_pose_control", ROOT / "scripts/environments/_cr12_pose_control.py")
pc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pc)


def load_support_and_entry():
    """Only their stdlib top levels are executed, never main or a runtime function."""
    spec = importlib.util.spec_from_file_location("_cr12_runtime_support", ROOT / "scripts/environments/_cr12_runtime_support.py")
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    spec = importlib.util.spec_from_file_location("_cr12_pose_entry_cpu", ROOT / "scripts/environments/run_cr12_pose_target.py")
    entry = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"_cr12_runtime_support": support}), \
            mock.patch.object(sys, 'path', [str(ROOT / 'scripts/environments'), *sys.path]):
        spec.loader.exec_module(entry)
    return support, entry


def transform(axis=(0, 0, 1), angle=0, position=(0, 0, 0)):
    q = np.r_[math.cos(angle/2), np.asarray(axis)*math.sin(angle/2)]
    return pc.pose_from_wxyz(position, q)


def model():
    origins = ((.105, 0, 1.062), (0, 0, .35), (0, 0, .76), (0, 0, .54), (0, -.15, 0), (0, 0, .123))
    axes = ((0, 0, 1), (0, 1, 0), (0, 1, 0), (0, 0, 1), (0, 1, 0), (0, 0, 1))
    return pc.KinematicModel([{"name": name, "parent": pc.BODY_NAMES[i], "child": pc.BODY_NAMES[i+1],
                               "origin_xyz": origins[i], "origin_rpy": [0, 0, 0], "axis": axes[i]}
                              for i, name in enumerate(pc.JOINT_NAMES)])


class PoseControlTests(unittest.TestCase):
    def assert_category(self, category, function, *args, **kwargs):
        with self.assertRaises(pc.PoseCheckError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.category, category)
        return caught.exception

    def test_scanner_installation_inverse_direction(self):
        ee = transform((1, 0, 0), .4, [1, 2, 3])
        scanner = pc.scanner_from_ee(ee)
        np.testing.assert_allclose(scanner[:3, 3], ee[:3, 3], atol=1e-14)
        np.testing.assert_allclose(pc.ee_from_scanner(scanner), ee, atol=1e-14)
        np.testing.assert_allclose(pc.T_ES[:3, :3] @ [1, 0, 0], [-2**-.5, 2**-.5, 0], atol=1e-14)

    def test_nonidentity_root_pose_and_jacobian(self):
        root = transform(angle=math.pi/2, position=[3, -2, .053])
        local = transform((1, 0, 0), .3, [.2, .4, .7])
        np.testing.assert_allclose(pc.in_root(root, root @ local), local, atol=1e-14)
        native = np.eye(6)
        result = pc.adapt_jacobian(native, "actor", root, root @ local, [0, 0, 0])
        np.testing.assert_allclose(result[:3, :3], root[:3, :3].T, atol=1e-14)
        np.testing.assert_allclose(result[3:, 3:], root[:3, :3].T, atol=1e-14)
        np.testing.assert_array_equal(native, np.eye(6))

    def test_quaternion_sign_equivalence_and_no_input_mutation(self):
        q = np.array([.5, -.5, .5, -.5])
        before = q.copy()
        a, b = pc.pose_from_wxyz([0, 0, 0], q), pc.pose_from_wxyz([0, 0, 0], -q)
        np.testing.assert_array_equal(q, before)
        np.testing.assert_allclose(a, b, atol=1e-14)
        self.assertLess(pc.pose_error(a, b)[1], 1e-14)
        for axis in ([1, 0, 0], [0, 1, 0], [0, 0, 1]):
            pi_pose = transform(axis, math.pi)
            p, out = pc.pose_to_wxyz(pi_pose)
            np.testing.assert_allclose(pc.pose_from_wxyz(p, out), pi_pose, atol=1e-14)

    def test_target_uses_world_y_left_multiply_and_freezes_input(self):
        initial = transform(angle=math.radians(135), position=[.1, -.15, 2.888])
        frozen = pc.FrozenPoseTarget(initial)
        target = frozen.target
        expected_left = transform((0, 1, 0), math.radians(1))[:3, :3] @ initial[:3, :3]
        wrong_right = initial[:3, :3] @ transform((0, 1, 0), math.radians(1))[:3, :3]
        np.testing.assert_allclose(target[:3, :3], expected_left, atol=1e-14)
        self.assertGreater(float(np.max(np.abs(target[:3, :3] - wrong_right))), .01)
        initial[:] = 0
        target[:] = 0
        self.assertGreater(frozen.initial[3, 3], .99)
        self.assertGreater(frozen.target[3, 3], .99)

    def test_small_angle_geodesic_endpoints_and_four_second_hold(self):
        frozen = pc.FrozenPoseTarget(transform(angle=.3, position=[1, 2, 3]))
        np.testing.assert_allclose(frozen.reference(0), frozen.initial, atol=1e-14)
        np.testing.assert_allclose(frozen.reference(4), frozen.target, atol=1e-14)
        np.testing.assert_allclose(frozen.reference(8), frozen.target, atol=1e-14)
        midpoint = frozen.reference(2)
        self.assertAlmostEqual(pc.pose_error(frozen.initial, midpoint)[1], math.radians(.5), places=13)
        self.assertGreater(pc.pose_error(midpoint, frozen.target)[1], .008)
        np.testing.assert_allclose(midpoint[:3, 3] - frozen.initial[:3, 3], pc.TARGET_OFFSET/2, atol=1e-14)
        self.assertLess(pc.pose_error(frozen.reference(pc.DT), frozen.initial)[1], 1e-7)

    def test_shuffled_name_mapping_fixed_base_and_independent_clone(self):
        bodies = ["agv", "link_6", "link_2", "link_1", "link_5", "link_3", "link_4"]
        joints = list(reversed(pc.JOINT_NAMES))
        mapping = pc.resolve_mapping(bodies, joints, True)
        self.assertEqual(mapping["ee_body_index"], 1)
        self.assertEqual(mapping["jacobian_row"], 0)
        self.assertEqual(mapping["joint_ids"], [5, 4, 3, 2, 1, 0])
        raw = np.arange(216, dtype=np.float32).reshape(1, 6, 6, 6)
        extracted = pc.extract_jacobian(raw, mapping)
        np.testing.assert_array_equal(extracted, raw[0, 0, :, ::-1])
        raw[:] = -1
        self.assertGreater(float(extracted.max()), 0)
        for bad_bodies, bad_joints, fixed in ((bodies, joints, False), (bodies[:-1], joints, True),
                                              (bodies, [joints[0]] * 6, True)):
            self.assert_category("SETUP_JACOBIAN_SEMANTICS", pc.resolve_mapping, bad_bodies, bad_joints, fixed)

    def test_native_jacobian_shape_dtype_and_nonfinite(self):
        mapping = pc.resolve_mapping(pc.BODY_NAMES, pc.JOINT_NAMES, True)
        for value in (np.zeros((1, 6, 6)), np.zeros((1, 6, 6, 6), dtype=np.float64),
                      np.full((1, 6, 6, 6), np.nan, dtype=np.float32)):
            self.assert_category("SETUP_JACOBIAN_SEMANTICS", pc.extract_jacobian, value, mapping)

    def test_com_to_actor_sign_and_rotated_root(self):
        root = transform(angle=.7, position=[1, 2, 3])
        q = np.radians([2, 1, -1.5, -2, 1.5, 3])
        kin = model()
        com = [.060712673, .060718220, .118532829]
        actor, center = kin.jacobians(q, root, com)
        end = kin.forward(q, root)["link_6"]
        actual = pc.adapt_jacobian(center, "com", root, end, com)
        expected = pc.adapt_jacobian(actor, "actor", root, end, com)
        np.testing.assert_allclose(actual, expected, atol=1e-13)
        wrong = center.copy()
        wrong[:3] -= pc.skew(end[:3, :3] @ com) @ wrong[3:]
        self.assertGreater(float(np.max(np.abs(wrong - actor))), .1)

    def test_geometric_jacobian_matches_fk_finite_difference(self):
        kin = model()
        root = transform(angle=.6, position=[.2, .1, .053])
        q = np.radians([1, 2, -3, 1, 1, 1])
        actor, center = kin.jacobians(q, root, [.06, .06, .12])
        for index in range(6):
            offset = np.zeros(6)
            offset[index] = 1e-6
            plus, minus = kin.forward(q+offset, root)["link_6"], kin.forward(q-offset, root)["link_6"]
            numerical = (plus[:3, 3] - minus[:3, 3]) / 2e-6
            np.testing.assert_allclose(actor[:3, index], numerical, atol=1e-9)
        self.assertEqual(pc.select_jacobian_adapter(actor.astype(np.float32), actor, center)["reference_point"], "actor")
        self.assertEqual(pc.select_jacobian_adapter(center.astype(np.float32), actor, center)["reference_point"], "com")

    def test_zero_pose_rank_three_is_not_rejected_and_joint_six_discriminates(self):
        kin = model()
        actor, center = kin.jacobians(np.zeros(6), np.eye(4), [.060712673, .060718220, .118532829])
        self.assertEqual(np.linalg.matrix_rank(actor), 3)
        np.testing.assert_allclose(actor[:3, 5], 0, atol=1e-14)
        np.testing.assert_allclose(center[:3, 5], [-.060718220, .060712673, 0], atol=1e-14)
        self.assertEqual(pc.select_jacobian_adapter(actor, actor, center)["reference_point"], "actor")

    def test_ambiguous_and_neither_jacobian_matches_fail(self):
        identity = np.eye(6)
        self.assert_category("SETUP_JACOBIAN_SEMANTICS", pc.select_jacobian_adapter, identity, identity, identity)
        self.assert_category("SETUP_JACOBIAN_SEMANTICS", pc.select_jacobian_adapter, identity*2, identity, identity*3)
        bad_angular = identity.copy()
        bad_angular[5, 5] += .001
        self.assert_category("SETUP_JACOBIAN_SEMANTICS", pc.select_jacobian_adapter, bad_angular, identity, identity*3)

    def test_derived_urdf_loader_uses_current_source_not_logs(self):
        path = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf"
        kin = pc.KinematicModel.from_derived_urdf(path)
        end = kin.forward(np.zeros(6), transform(position=[0, 0, .053]))["link_6"]
        np.testing.assert_allclose(end[:3, 3], [.105, -.15, 2.888], atol=1e-14)

    def test_nan_inf_rejected_and_command_state_unchanged(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        for bad in (math.nan, math.inf, -math.inf):
            q = np.zeros(6)
            q[2] = bad
            self.assert_category("COMMAND_REJECTED", integrator.propose, np.zeros(6), np.zeros(6), q)
            self.assert_category("COMMAND_REJECTED", pc.pose_from_wxyz, [0, 0, bad], [1, 0, 0, 0])
            self.assert_category("PHYSICS_GUARD", pc.FrozenPoseTarget(np.eye(4)).reference, bad)
        np.testing.assert_array_equal(integrator.previous, np.zeros(6))
        self.assertEqual(integrator.generation, 0)
        self.assert_category("COMMAND_REJECTED", pc.pose_from_wxyz, [0, 0, 0], [0, 0, 0, 0])

    def test_hard_limit_margin_and_actual_limit_order(self):
        initial = np.zeros(6)
        initial[0] = 3.025
        integrator = pc.CommandIntegrator(initial)
        q_ik = initial.copy()
        q_ik[0] = 3.04
        error = self.assert_category("COMMAND_REJECTED", integrator.propose, initial, np.zeros(6), q_ik)
        self.assertIn("margin", str(error))
        actual = initial.copy()
        actual[0] = 3.1
        error = self.assert_category("PHYSICS_GUARD", integrator.propose, actual, np.zeros(6), actual)
        self.assertIn("hard limit", str(error))

    def test_raw_dls_update_limit(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        self.assert_category("COMMAND_REJECTED", integrator.propose, np.zeros(6), np.zeros(6), np.full(6, .035001))
        admitted = integrator.propose(np.zeros(6), np.zeros(6), np.full(6, .034))
        np.testing.assert_allclose(admitted.q, .034/60, atol=1e-10)

    def test_accumulated_command_error_and_rejected_proposal_not_committed(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        for _ in range(68):
            proposal = integrator.propose(np.zeros(6), np.zeros(6), np.full(6, .03))
            integrator.commit(proposal, proposal.q.tolist(), proposal.dq.tolist())
        previous, generation = integrator.previous, integrator.generation
        error = self.assert_category("COMMAND_REJECTED", integrator.propose, np.full(6, -.002), np.zeros(6), np.full(6, .028))
        self.assertIn("Accumulated", str(error))
        np.testing.assert_array_equal(integrator.previous, previous)
        self.assertEqual(integrator.generation, generation)

    def test_per_tick_position_guard_independent_of_stricter_raw_guard(self):
        # With approved alpha/raw-delta bounds this guard is redundant, but must independently reject a bad proposal.
        integrator = pc.CommandIntegrator(np.zeros(6))
        error = self.assert_category("COMMAND_REJECTED", integrator._proposal_limits, np.full(6, .001251), np.zeros(6))
        self.assertIn("position step", str(error))

    def test_velocity_uses_quantized_position_difference(self):
        initial = np.full(6, .07123456789)
        integrator = pc.CommandIntegrator(initial)
        previous = integrator.previous
        proposal = integrator.propose(initial, np.zeros(6), initial + .0123456789)
        expected = ((proposal.q.astype(np.float64) - previous.astype(np.float64))/pc.DT).astype(np.float32)
        np.testing.assert_array_equal(proposal.dq, expected)
        self.assertEqual(proposal.q.dtype, np.float32)
        self.assertEqual(proposal.dq.dtype, np.float32)
        self.assertGreater(float(np.max(np.abs(proposal.dq - .0123456789/pc.DT))), 1)
        integrator.commit(proposal, proposal.q.tolist(), proposal.dq.tolist())
        np.testing.assert_array_equal(integrator.previous, proposal.q)
        self.assert_category("COMMAND_REJECTED", integrator.commit, proposal, proposal.q, proposal.dq)

    def test_submission_mismatch_does_not_commit(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        proposal = integrator.propose(np.zeros(6), np.zeros(6), np.full(6, .01))
        altered = proposal.q.astype(np.float64)
        altered[0] += 1e-12
        self.assert_category("COMMAND_REJECTED", integrator.commit, proposal, altered, proposal.dq)
        np.testing.assert_array_equal(integrator.previous, np.zeros(6))
        self.assertEqual(integrator.generation, 0)

    def test_trust_region_native_velocity_and_fixed_dt(self):
        integrator = pc.CommandIntegrator(np.zeros(6))
        self.assert_category("COMMAND_REJECTED", integrator.check_actual, np.full(6, math.radians(5.01)), np.zeros(6))
        self.assert_category("PHYSICS_GUARD", integrator.check_actual, np.zeros(6), np.full(6, .25001))
        self.assert_category("SETUP", pc.CommandIntegrator, np.zeros(6), dt=1/60)

    def test_collision_sanity_checks_actual_to_proposal_midpoint_endpoint(self):
        kin = model()
        actual, proposal = np.zeros(6), np.radians([0, 1, -1, 0, 1, 0])
        root = transform(position=[0, 0, .053])
        samples = kin.sanity_samples(actual, proposal, root)
        self.assertEqual([name for name, _ in samples], ["midpoint", "endpoint"])
        np.testing.assert_allclose(samples[0][1]["link_6"], kin.forward(proposal*.5, root)["link_6"], atol=1e-14)
        np.testing.assert_allclose(samples[1][1]["link_6"], kin.forward(proposal, root)["link_6"], atol=1e-14)
        proposal[:] = 0
        self.assertGreater(float(np.max(np.abs(samples[1][1]["link_6"] - kin.forward(actual, root)["link_6"]))), .001)

    def observe_to(self, monitor, end, dq=None, actual=None):
        dq = np.zeros(6) if dq is None else dq
        actual = np.eye(4) if actual is None else actual
        result = None
        for step in range(monitor.last_step + 1, end + 1):
            result = monitor.observe(step, step*pc.DT, actual, np.eye(4), np.eye(4), dq)
        return result

    def test_arrival_requires_final_reference_and_121_inclusive_samples(self):
        monitor = pc.PoseMonitor()
        self.observe_to(monitor, 479)
        self.assertEqual(monitor.stable_count, 0)
        self.observe_to(monitor, 599)
        self.assertEqual(monitor.stable_count, 120)
        self.assertFalse(monitor.reached)
        result = self.observe_to(monitor, 600)
        self.assertEqual(result["status"], "POSE_REACHED")
        self.assertEqual(result["stable_count"], 121)
        self.assertAlmostEqual(result["stable_span_s"], 1.0)

    def test_failed_arrival_sample_resets_window_without_resetting_budget(self):
        monitor = pc.PoseMonitor()
        self.observe_to(monitor, 550)
        monitor.observe(551, 551*pc.DT, np.eye(4), np.eye(4), np.eye(4), np.full(6, .010001))
        self.assertEqual(monitor.stable_count, 0)
        self.assertEqual(monitor.last_step, 551)
        self.observe_to(monitor, 671)
        self.assertFalse(monitor.reached)
        self.assertEqual(self.observe_to(monitor, 672)["status"], "POSE_REACHED")

    def test_no_progress_full_window_but_pose_in_tolerance_waits_for_speed(self):
        monitor = pc.PoseMonitor()
        outside = transform(position=[.003, 0, 0])
        self.observe_to(monitor, 599, actual=outside)
        self.assert_category("NO_PROGRESS", self.observe_to, monitor, 600, actual=outside)
        self.assertEqual(monitor.last_sample["step"], 600)
        self.assertEqual(monitor.last_sample["failure_category"], "NO_PROGRESS")
        waiting = pc.PoseMonitor()
        self.observe_to(waiting, 800, dq=np.full(6, .02))
        self.assertIsNone(waiting.failure)
        self.assertFalse(waiting.reached)

    def test_ten_percent_progress_boundary(self):
        monitor = pc.PoseMonitor()
        start = transform(position=[.004, 0, 0])
        self.observe_to(monitor, 480, actual=start)
        for step in range(481, 601):
            distance = .004 * (1 - .1 * (step-480)/120)
            actual = transform(position=[distance, 0, 0])
            monitor.observe(step, step*pc.DT, actual, np.eye(4), np.eye(4), np.zeros(6))
        self.assertIsNone(monitor.failure)

    def test_timeout_at_960_unless_full_success_window(self):
        monitor = pc.PoseMonitor()
        self.observe_to(monitor, 959, dq=np.full(6, .02))
        self.assert_category("TIMEOUT", self.observe_to, monitor, 960, dq=np.full(6, .02))
        self.assertEqual(monitor.last_sample["step"], 960)
        success = pc.PoseMonitor()
        self.observe_to(success, 839, dq=np.full(6, .02))
        self.assertEqual(self.observe_to(success, 960)["status"], "POSE_REACHED")

    def test_divergence_twelve_consecutive_reference_errors(self):
        monitor = pc.PoseMonitor()
        divergent = transform(position=[.030001, 0, 0])
        self.observe_to(monitor, 11, actual=divergent)
        self.assert_category("DIVERGENCE", self.observe_to, monitor, 12, actual=divergent)
        monitor = pc.PoseMonitor()
        self.observe_to(monitor, 11, actual=divergent)
        self.observe_to(monitor, 12)
        self.assertEqual(monitor.divergent_count, 0)

    def test_guard_failure_latches_and_success_cannot_overwrite_it(self):
        monitor = pc.PoseMonitor()
        self.observe_to(monitor, 599)
        self.assert_category("PHYSICS_GUARD", monitor.observe, 600, 5.0, np.eye(4), np.eye(4), np.eye(4), np.zeros(6), False)
        first = monitor.failure
        self.assert_category("PHYSICS_GUARD", monitor.observe, 601, 601*pc.DT, np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
        self.assertIs(monitor.failure, first)
        self.assertFalse(monitor.reached)
        self.assertEqual(monitor.last_sample["status"], "FAIL")
        self.assertEqual(monitor.last_sample["step"], 600)

    def test_clock_and_nonfinite_post_state_failure_preserves_sample(self):
        for time in (math.nan, math.inf, 1.0):
            monitor = pc.PoseMonitor()
            self.assert_category("PHYSICS_GUARD", monitor.observe, 1, time, np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
            self.assertEqual(monitor.last_sample["step"], 1)
        monitor = pc.PoseMonitor()
        self.assert_category("PHYSICS_GUARD", monitor.observe, 2, 2*pc.DT, np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
        monitor = pc.PoseMonitor()
        self.assert_category("PHYSICS_GUARD", monitor.observe, 1, pc.DT, np.eye(4), np.eye(4), np.eye(4), np.full(6, math.nan))
        for step in (math.nan, math.inf, 1.5, True):
            self.assert_category("PHYSICS_GUARD", pc.PoseMonitor().observe, step, pc.DT,
                                 np.eye(4), np.eye(4), np.eye(4), np.zeros(6))
        self.assert_category("PHYSICS_GUARD", pc.PoseMonitor().observe, 1, pc.DT,
                             np.full((4, 4), math.nan), np.eye(4), np.eye(4), np.zeros(6))

    def test_recorder_internal_failure_survives_completed_work_and_recording_errors(self):
        support, _ = load_support_and_entry()
        recorder = support.Recorder()
        recorder.result.update(work_completed=True, status="WORK_COMPLETED_PENDING_NATURAL_EXIT", pose_outcome="POSE_REACHED")
        primary = pc.PoseCheckError("PHYSICS_GUARD", "Synthetic physical failure")
        with contextlib.redirect_stderr(io.StringIO()), mock.patch.object(recorder, "emit", side_effect=OSError("broken output")), \
                mock.patch.object(recorder, "save", side_effect=OSError("disk error")):
            recorder.fail(primary)
        self.assertEqual(recorder.result["status"], "FAILED")
        self.assertEqual(recorder.result["failures"][0]["category"], "PHYSICS_GUARD")
        self.assertEqual(len(recorder.result["secondary_failures"]), 2)
        with tempfile.TemporaryDirectory(prefix="cr12_pose_recorder_cpu_") as directory:
            recorder.path = Path(directory) / "result.json"
            recorder.save()
            saved = json.loads(recorder.path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "FAILED")
            self.assertTrue(saved["failures"])

    def test_pose_csv_preserves_named_values_and_partial_failing_step(self):
        _, entry = load_support_and_entry()
        with tempfile.TemporaryDirectory(prefix="cr12_pose_trace_cpu_") as directory:
            path = Path(directory) / "trace.csv"
            trace = entry.PoseTrace(path)
            trace.append({"step": 1, "physics_time_s": .025, "controlled_time_s": pc.DT,
                          "reference_time_s": pc.DT, "phase": "trajectory", "status": "RUNNING",
                          "actual_p": [1, 2, 3], "actual_qwxyz": [1, 0, 0, 0],
                          "q": np.arange(6)*.001, "dq": np.arange(6)*.002,
                          "q_cmd": np.arange(6)*.003, "dq_cmd": np.arange(6)*.004,
                          "guard_clock": "PASS", "stable_samples": 0})
            trace.append({"step": 2, "physics_time_s": 1/30, "controlled_time_s": 2*pc.DT,
                          "reference_time_s": 2*pc.DT, "phase": "trajectory", "status": "FAIL",
                          "q": [0]*6, "dq": [0]*6, "guard_clock": "PASS", "guard_contact": "FAIL",
                          "failure": "PHYSICS_GUARD: synthetic contact", "stable_samples": 0})
            self.assertEqual(trace.count, 2)
            trace.close()
            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertEqual(float(rows[0]["actual_p_2"]), 3)
            self.assertAlmostEqual(float(rows[0]["q_5"]), .005)
            self.assertAlmostEqual(float(rows[0]["dq_cmd_5"]), .02)
            self.assertEqual(rows[1]["actual_p_0"], "")
            self.assertEqual(rows[1]["guard_contact"], "FAIL")
            self.assertEqual(rows[1]["status"], "FAIL")
            self.assertIn("synthetic contact", rows[1]["failure"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
