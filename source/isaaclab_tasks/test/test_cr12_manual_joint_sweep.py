"""CPU-only fixed joint-sweep checks; synthetic measured inputs are not runtime proof."""

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
SCRIPTS = ROOT / "scripts/environments"


def load(name, filename, dependencies=None):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {name: module, **(dependencies or {})}):
        spec.loader.exec_module(module)
    return module


am = load("_cr12_sweep_asset_math_cpu", "_cr12_asset_math.py")
sweep = load("_cr12_sweep_cpu", "_cr12_manual_joint_sweep.py", {"_cr12_asset_math": am})
support = load("_cr12_sweep_support_cpu", "_cr12_runtime_support.py")


def pose(x=0.0, y=0.0, z=0.0):
    result = np.eye(4)
    result[:3, 3] = [x, y, z]
    return result


def synthetic_sample(plan, step, scanner_amplitude=.23):
    """Independent synthetic sensor values supplied to the monitor, without FK."""
    ref = plan.reference(step)
    measured = pose(x=scanner_amplitude * (ref.q[plan.moving_index]-plan.q_start[plan.moving_index])
                    / math.radians(sweep.PROFILE.angle_deg))
    return ref, measured


def observe_until(monitor, last_step, scanner_amplitude=.23):
    for step in range(monitor.summary()["completed_physics_steps"]+1, last_step+1):
        ref, measured = synthetic_sample(monitor.plan, step, scanner_amplitude)
        monitor.observe(step, ref.time_s, ref.q, ref.dq, measured)


class SweepReferenceTests(unittest.TestCase):
    def setUp(self):
        self.plan = sweep.SweepPlan(np.zeros(6))

    def test_profile_is_fixed_manual_twenty_one_seconds(self):
        self.assertIs(sweep.select_profile(), sweep.PROFILE)
        self.assertEqual(sweep.PROFILE.joint_name, "joint_3")
        self.assertIn(sweep.PROFILE.angle_deg, (15.0, 20.0))
        self.assertEqual(sweep.PROFILE.geometry_mode, "aabb_then_obb_margin_v1")
        self.assertTrue(sweep.PROFILE.manual_joint_visual_only)
        self.assertEqual((sweep.PROFILE.motion_seconds, sweep.PROFILE.max_seconds, sweep.MAX_STEPS), (8, 21, 2520))
        with self.assertRaises(FrozenInstanceError):
            sweep.PROFILE.angle_deg = 30
        with self.assertRaises(TypeError):
            sweep.SweepProfile(angle_deg=15)
        with self.assertRaises(sweep.SweepCheckError):
            sweep.select_profile("formal")

    def test_shuffled_names_control_joint_three_not_third_array_element(self):
        names = ("joint_6", "joint_3", "joint_1", "joint_5", "joint_2", "joint_4")
        start = np.array([.01, .02, .03, .04, .05, .06])
        plan = sweep.SweepPlan(start, names)
        self.assertEqual(plan.moving_index, 1)
        expected = start.copy()
        expected[1] += math.radians(sweep.PROFILE.angle_deg)
        np.testing.assert_allclose(plan.q_out, expected, atol=1e-15)
        np.testing.assert_array_equal(plan.reference(1080).dq, np.zeros(6))
        for index in (0, 2, 3, 4, 5):
            self.assertEqual(plan.reference(600).q[index], start[index])
            self.assertEqual(plan.reference(600).dq[index], 0)

    def test_missing_duplicate_extra_and_alias_names_rejected(self):
        names = list(am.JOINT_NAMES)
        for bad in (names[:-1], names+["joint_0"], names[:-1]+[names[0]], ["joint3"]+names[1:]):
            with self.subTest(names=bad), self.assertRaises(sweep.SweepCheckError):
                sweep.SweepPlan(np.zeros(6), bad)

    def test_reference_degrees_to_radians_and_independent_start_snapshot(self):
        start = np.zeros(6)
        plan = sweep.SweepPlan(start)
        start[:] = 5
        self.assertAlmostEqual(plan.q_out[2], math.radians(sweep.PROFILE.angle_deg), places=15)
        self.assertLess(plan.q_out[2], .36)
        np.testing.assert_array_equal(plan.q_start, np.zeros(6))
        reference = plan.reference(600)
        with self.assertRaises(ValueError):
            reference.q[2] = 99

    def test_quintic_endpoints_and_analytic_velocity_against_numeric_derivative(self):
        self.assertEqual(sweep.quintic(0), (0, 0))
        self.assertEqual(sweep.quintic(1), (1, 0))
        for u in (.1, .27, .5, .78, .9):
            epsilon = 1e-6
            numerical = (sweep.quintic(u+epsilon)[0]-sweep.quintic(u-epsilon)[0])/(2*epsilon)
            self.assertAlmostEqual(sweep.quintic(u)[1], numerical, places=8)
        ref = self.plan.reference(600)  # t=5, middle of the outbound motion.
        self.assertAlmostEqual(ref.dq[2], 1.875*math.radians(sweep.PROFILE.angle_deg)/8, places=14)

    def test_phase_and_zero_velocity_at_every_join(self):
        expected = {0: "START_HOLD", 119: "START_HOLD", 120: "OUTBOUND", 1079: "OUTBOUND",
                    1080: "OUTBOUND_HOLD", 1319: "OUTBOUND_HOLD", 1320: "RETURN",
                    2279: "RETURN", 2280: "RETURN_HOLD", 2520: "RETURN_HOLD"}
        for step, phase in expected.items():
            self.assertEqual(self.plan.reference(step).phase, phase)
        for step in (0, 120, 1080, 1320, 2280, 2520):
            np.testing.assert_allclose(self.plan.reference(step).dq, np.zeros(6), atol=1e-14)
        for step in (120, 1080, 1320, 2280):
            middle = self.plan.reference(step)
            for neighbor in (step-1, step+1):
                self.assertLess(float(np.max(np.abs(self.plan.reference(neighbor).q-middle.q))), 1e-8)

    def test_return_traverses_same_reference_in_reverse(self):
        for outbound in range(120, 1081, 37):
            reverse = 2400-outbound
            a, b = self.plan.reference(outbound), self.plan.reference(reverse)
            np.testing.assert_allclose(a.q, b.q, atol=1e-14)
            np.testing.assert_allclose(a.dq, -b.dq, atol=1e-14)

    def test_command_pair_float32_all_2520_steps_stays_within_fixed_limits(self):
        previous = self.plan.q_start.astype(np.float32)
        peak_increment = peak_speed = 0.0
        for step in range(1, 2521):
            command = self.plan.command(step, previous)
            self.assertEqual(command.q.dtype, np.float32)
            self.assertEqual(command.dq.dtype, np.float32)
            np.testing.assert_array_equal(command.q, self.plan.reference(step).q.astype(np.float32))
            np.testing.assert_array_equal(command.dq, self.plan.reference(step).dq.astype(np.float32))
            peak_increment = max(peak_increment, float(np.max(np.abs(command.q-previous))))
            peak_speed = max(peak_speed, float(np.max(np.abs(command.dq))))
            previous = command.q
        self.assertLessEqual(peak_increment, .00125)
        self.assertLessEqual(peak_speed, .15)
        np.testing.assert_array_equal(previous, self.plan.q_start)
        for bad in (-1, 2521, .5, True):
            with self.assertRaises(sweep.SweepCheckError):
                self.plan.reference(bad)

    def test_command_rejects_nonfinite_shape_speed_delta_and_margin_without_clamp(self):
        baseline = np.zeros(6)
        for q, dq, previous in (([np.nan]*6, baseline, baseline), (baseline, [np.inf]*6, baseline),
                                 ([0]*5, baseline, baseline), ([.002]*6, baseline, baseline),
                                 (baseline, [.1501]*6, baseline), ([4]*6, baseline, [4]*6)):
            with self.subTest(q=q, dq=dq), self.assertRaises(sweep.SweepCheckError) as caught:
                self.plan.validate_command(q, dq, previous)
            self.assertEqual(caught.exception.category, "COMMAND_REJECTED")
        outside = np.zeros(6)
        outside[2] = am.JOINT_LIMITS[2][1] - math.radians(sweep.PROFILE.angle_deg) - .019
        with self.assertRaises(sweep.SweepCheckError):
            sweep.SweepPlan(outside)


class SweepMonitorTests(unittest.TestCase):
    def setUp(self):
        self.plan = sweep.SweepPlan(np.zeros(6))
        self.monitor = sweep.SweepMonitor(self.plan, pose())

    def test_complete_roundtrip_needs_2520_steps_and_two_121_sample_windows(self):
        observe_until(self.monitor, 1320)
        middle = self.monitor.summary()
        self.assertFalse(middle["complete"])
        self.assertFalse(middle["all_passed"])
        self.assertEqual(middle["endpoint_windows"]["outbound"]["count"], 121)
        self.assertEqual(middle["endpoint_windows"]["return"]["count"], 0)
        observe_until(self.monitor, 2520)
        final = self.monitor.summary()
        self.assertEqual(final["status"], "INTERNAL_CHECKS_PASS")
        self.assertTrue(final["complete"] and final["all_passed"])
        self.assertEqual(final["completed_physics_steps"], 2520)
        for label, bounds in (("outbound", (1200, 1320)), ("return", (2400, 2520))):
            window = final["endpoint_windows"][label]
            self.assertEqual((window["start_step"], window["end_step"]), bounds)
            self.assertEqual(window["count"], 121)
            self.assertAlmostEqual(window["span_s"], 1, places=12)
            self.assertTrue(window["complete"] and window["all_passed"])
            self.assertEqual(final["endpoints"][label]["step"], bounds[1])

    def test_return_net_zero_does_not_replace_peak_measured_excursion(self):
        observe_until(self.monitor, 2520)
        final = self.monitor.summary()
        self.assertAlmostEqual(final["joint_excursion_deg"], sweep.PROFILE.angle_deg)
        self.assertAlmostEqual(final["scanner_excursion_m"], .23)
        self.assertTrue(final["direction_pass"])
        self.assertEqual(final["endpoints"]["return"]["scanner_position_m"], [0, 0, 0])
        self.assertEqual(final["scanner_excursion_step"], 1080)
        self.assertAlmostEqual(final["scanner_excursion_time_s"], 9.0)

    def test_measured_scanner_threshold_is_strict_and_cannot_be_replaced_by_reference(self):
        with self.assertRaises(sweep.SweepCheckError) as caught:
            observe_until(self.monitor, 2520, scanner_amplitude=.10)
        self.assertEqual(caught.exception.category, "VISIBLE_AMPLITUDE_NOT_MET")
        summary = self.monitor.summary()
        self.assertTrue(summary["complete"])
        self.assertFalse(summary["all_passed"] or summary["amplitude_pass"])
        self.assertAlmostEqual(summary["joint_excursion_deg"], sweep.PROFILE.angle_deg)
        self.assertAlmostEqual(summary["scanner_excursion_m"], .10)
        self.assertEqual(self.monitor.last_sample["step"], 2520)

    def test_no_actual_joint_motion_cannot_be_counted_as_command_amplitude(self):
        with self.assertRaises(sweep.SweepCheckError) as caught:
            for step in range(1, 1081):
                ref = self.plan.reference(step)
                self.monitor.observe(step, ref.time_s, np.zeros(6), np.zeros(6), pose())
        self.assertEqual(caught.exception.category, "tracking")
        self.assertEqual(self.monitor.summary()["joint_excursion_deg"], 0)
        self.assertEqual(self.monitor.summary()["scanner_excursion_m"], 0)

    def test_measured_joint_ten_degree_threshold_is_strict(self):
        threshold_step = next(step for step in range(1, 1081)
                              if self.plan.reference(step).q[2] >= math.radians(10))
        observe_until(self.monitor, threshold_step-1)
        ref = self.plan.reference(threshold_step)
        actual = ref.q.copy()
        actual[2] = math.radians(10)
        self.monitor.observe(threshold_step, ref.time_s, actual, ref.dq, pose(x=.11))
        summary = self.monitor.summary()
        self.assertEqual(summary["joint_excursion_deg"], 10)
        self.assertGreater(summary["scanner_excursion_m"], .10)
        self.assertFalse(summary["amplitude_pass"] or summary["direction_pass"])

    def test_nonfinite_failure_preserves_raw_sample_without_polluting_statistics(self):
        q = np.zeros(6)
        dq = np.zeros(6)
        dq[5] = math.nan
        with self.assertRaises(sweep.SweepCheckError):
            self.monitor.observe(1, sweep.DT, q, dq, pose())
        self.assertTrue(math.isnan(self.monitor.last_sample["dq_rad_s"][5]))
        self.assertEqual(self.monitor.last_sample["step"], 1)
        self.assertEqual(self.monitor.summary()["completed_physics_steps"], 1)
        self.assertEqual(self.monitor.summary()["max_abs_dq_rad_s"], [0.0]*6)
        self.assertFalse(self.monitor.summary()["all_passed"])

    def test_hold_uses_every_native_velocity_without_filter_and_keeps_failed_sample(self):
        observe_until(self.monitor, 1199)
        ref, measured = synthetic_sample(self.plan, 1200)
        dq = np.zeros(6)
        dq[5] = .010001
        with self.assertRaises(sweep.SweepCheckError) as caught:
            self.monitor.observe(1200, 10, ref.q, dq, measured)
        self.assertEqual(caught.exception.category, "holding")
        self.assertEqual(self.monitor.last_sample["step"], 1200)
        self.assertEqual(self.monitor.last_sample["dq_rad_s"][5], .010001)
        self.assertEqual(self.monitor.summary()["endpoint_windows"]["outbound"]["count"], 1)

    def test_skipped_duplicate_wrong_clock_or_extra_step_cannot_complete(self):
        for step, seconds in ((2, 2*sweep.DT), (0, 0), (1, sweep.DT+.001), (1, float("nan")), (2521, 21)):
            monitor = sweep.SweepMonitor(self.plan, pose())
            with self.subTest(step=step, seconds=seconds), self.assertRaises(sweep.SweepCheckError):
                monitor.observe(step, seconds, np.zeros(6), np.zeros(6), pose())
            self.assertFalse(monitor.summary()["all_passed"])

    def test_actual_guards_keep_original_hard_limit_priority_and_manual_speed(self):
        cases = [(np.array([4, 0, 0, 0, 0, 0]), np.zeros(6), "joint_limit"),
                 (np.zeros(6), np.array([.250001, 0, 0, 0, 0, 0]), "tracking"),
                 (np.radians([0, 0, 0, 1.01, 0, 0]), np.zeros(6), "tracking"),
                 (np.array([np.nan]*6), np.zeros(6), "state_invalid")]
        for q, dq, category in cases:
            monitor = sweep.SweepMonitor(self.plan, pose())
            with self.subTest(category=category), self.assertRaises(sweep.SweepCheckError) as caught:
                monitor.observe(1, sweep.DT, q, dq, pose())
            self.assertEqual(caught.exception.category, category)
            self.assertFalse(monitor.summary()["all_passed"])

    def test_invalid_scanner_transform_or_marker_like_point_is_not_measurement(self):
        for invalid in ([0, 0, 0], np.full((4, 4), np.nan), np.diag([2, 1, 1, 1])):
            with self.subTest(shape=np.shape(invalid)), self.assertRaises(sweep.SweepCheckError):
                sweep.SweepMonitor(self.plan, invalid)

    def test_first_failure_stays_failed_even_after_external_success_or_exit_zero(self):
        observe_until(self.monitor, 2520)
        self.monitor.mark_failure("forbidden_contact", "post-physics contact guard failed", force=.2)
        self.monitor.mark_failure("later_close_error", "secondary")
        with self.assertRaises(sweep.SweepCheckError) as caught:
            self.monitor.observe(2520, 21, np.zeros(6), np.zeros(6), pose())
        self.assertEqual(caught.exception.category, "forbidden_contact")
        exit_code = 0
        evidence = self.monitor.summary()
        self.assertFalse(exit_code == 0 and evidence["all_passed"])
        self.assertEqual(evidence["failure"]["category"], "forbidden_contact")
        evidence["failure"]["category"] = "mutated_copy"
        self.assertEqual(self.monitor.summary()["failure"]["category"], "forbidden_contact")


class FakeClock:
    def __init__(self):
        self.value = 100.0
        self.sleeps = []

    def clock(self):
        return self.value

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.value += duration


class PacingAndBoundaryTests(unittest.TestCase):
    def test_fake_clock_full_duration_not_fast_playback_or_real_sleep(self):
        clock = FakeClock()
        pacer = sweep.RealtimePacer(clock.clock, clock.sleep)
        for step in range(1, 2521):
            clock.value += .001  # Fake physics/render work.
            pacer.pace(step*sweep.DT)
        report = pacer.summary(21)
        self.assertEqual(report["pace_calls"], 2520)
        self.assertAlmostEqual(report["controlled_wall_time_s"], 21, places=10)
        self.assertAlmostEqual(report["playback_ratio"], 1, places=10)
        self.assertGreater(report["total_sleep_s"], 18)
        self.assertTrue(all(value > 0 for value in clock.sleeps))

    def test_late_clock_does_not_sleep_or_insert_catchup_work(self):
        clock = FakeClock()
        pacer = sweep.RealtimePacer(clock.clock, clock.sleep)
        clock.value += .1
        self.assertEqual(pacer.pace(sweep.DT), 0)
        self.assertEqual(pacer.pace(2*sweep.DT), 0)
        self.assertEqual(clock.sleeps, [])
        self.assertEqual(pacer.pace_calls, 2)
        self.assertLess(pacer.summary(2*sweep.DT)["playback_ratio"], 1)

    def test_pacer_uses_absolute_deadlines_and_rejects_bad_clocks_or_skips(self):
        clock = FakeClock()
        pacer = sweep.RealtimePacer(clock.clock, clock.sleep)
        pacer.pace(sweep.DT)
        clock.value += .002
        pacer.pace(2*sweep.DT)
        self.assertAlmostEqual(clock.value, 100+2*sweep.DT, places=12)
        with self.assertRaises(sweep.SweepCheckError):
            pacer.pace(4*sweep.DT)
        clock.value = 99
        with self.assertRaises(sweep.SweepCheckError):
            pacer.pace(3*sweep.DT)

    def test_module_has_no_simulation_or_state_setter_or_fk_calls(self):
        tree = ast.parse((SCRIPTS / "_cr12_manual_joint_sweep.py").read_text(encoding="utf-8"))
        forbidden = {"step", "render", "update", "write_joint_state_to_sim", "write_root_state_to_sim",
                     "AppLauncher", "SimulationApp", "DifferentialIKController", "forward", "compute"}
        # dict.update is pure statistics; every other forbidden simulation spelling is absent.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                self.assertFalse(any(n.startswith(("torch", "isaac", "omni", "pxr")) for n in names))
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                self.assertNotIn(name, forbidden-{"update"})
        pacer = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RealtimePacer")
        attributes = {n.func.attr for n in ast.walk(pacer) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertTrue(attributes <= {"_now", "_clock", "_sleep", "isfinite"})

    def test_existing_clock_guard_still_rejects_extra_step_and_nonfinite_time(self):
        support.check_clock(17, 3.0, 18, 3.0+sweep.DT, sweep.DT)
        for before, after, time_after in ((17, 19, 3+sweep.DT), (17, 18, math.nan)):
            with self.assertRaises(support.DriveCheckError):
                support.check_clock(before, 3.0, after, time_after, sweep.DT)

    def test_existing_recorder_preserves_internal_failure_with_zero_exit_fact(self):
        recorder = support.Recorder()
        with contextlib.redirect_stdout(io.StringIO()):
            recorder.fail(support.DriveCheckError("geometry_guard", "synthetic failed guard"))
        recorder.result["target_exit_code"] = 0
        self.assertEqual(recorder.result["status"], "FAILED")
        self.assertFalse(recorder.result["work_completed"])
        self.assertEqual(recorder.result["failures"][0]["category"], "geometry_guard")


if __name__ == "__main__":
    unittest.main(verbosity=2)
