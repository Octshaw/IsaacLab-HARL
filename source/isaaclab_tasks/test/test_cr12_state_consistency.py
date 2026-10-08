"""Synthetic CPU tests only: no Isaac, CUDA, assets, or runtime are loaded."""

import argparse
import ast
import csv
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("_cr12_state_consistency", ROOT / "scripts/environments/_cr12_state_consistency.py")
state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state)
HOLD_SPEC = importlib.util.spec_from_file_location("_cr12_hold_diagnostics", ROOT / "scripts/environments/_cr12_hold_diagnostics.py")
hold = importlib.util.module_from_spec(HOLD_SPEC)
HOLD_SPEC.loader.exec_module(hold)
DRIVE_SPEC = importlib.util.spec_from_file_location("_cr12_drive_state_checks", ROOT / "scripts/environments/run_cr12_joint_drive.py")
drive = importlib.util.module_from_spec(DRIVE_SPEC)
DRIVE_SPEC.loader.exec_module(drive)
BODIES = ["agv", *(f"link_{i}" for i in range(1, 7))]
JOINTS = [f"joint_{i}" for i in range(1, 7)]


def quat(axis, angle):
    return np.r_[math.cos(angle/2), np.asarray(axis)*math.sin(angle/2)]


def mul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array([aw*bw-ax*bx-ay*by-az*bz, aw*bx+ax*bw+ay*bz-az*by,
                     aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw])


def records():
    return [{"name": name, "body0": BODIES[i], "body1": BODIES[i+1], "axis": "Z",
             "localPos0": [0, 0, 0], "localPos1": [0, 0, 0],
             "localRot0": [1, 0, 0, 0], "localRot1": [1, 0, 0, 0]} for i, name in enumerate(JOINTS)]


def physical_sample():
    poses = np.zeros((7, 7))
    poses[:, 6] = 1
    return poses, np.zeros((7, 6))


class StateConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cr12_state_cpu_")
        self.addCleanup(self.temp.cleanup)
        self.bindings = state.bind_joint_frames(records(), JOINTS, BODIES)
        self.metadata = {"body_names": BODIES, "joint_names": JOINTS, "synthetic_test_only": True}

    def trace(self, filename="links.csv"):
        trace = state.StateConsistencyTrace(Path(self.temp.name) / filename, self.metadata)
        self.addCleanup(trace.close)
        return trace

    def append(self, trace, step, **kwargs):
        poses, velocities = physical_sample()
        data = dict(poses=poses, velocities=velocities, analysis=state.analyze_links(self.bindings, poses, velocities),
                    clock_before=(step+2, (step+2)/120), clock_after=(step+2, (step+2)/120), comparison_valid=True)
        data.update(kwargs)
        trace.append(step, (step+2)/120, step/120, step/120, **data)

    def test_reused_getter_buffer_does_not_overwrite_copied_cache(self):
        buffer = np.arange(6, dtype=np.float64)
        calls = []
        def getter(label, amount=0):
            def call():
                calls.append(label)
                buffer[:] += amount
                return buffer
            return call
        sample = state.snapshot_read(
            {"q": getter("cache_q"), "dq": getter("cache_dq")},
            {"q": getter("native_q", 10), "dq": getter("native_dq", 20)},
            lambda value: np.array(value, copy=True), lambda: calls.append("sync"), lambda: (17, .5))
        np.testing.assert_equal(sample["cached"]["q"], np.arange(6))
        np.testing.assert_equal(sample["cached"]["dq"], np.arange(6))
        np.testing.assert_equal(sample["native"]["q"], np.arange(6)+10)
        np.testing.assert_equal(sample["native"]["dq"], np.arange(6)+30)
        self.assertEqual(calls, ["cache_q", "cache_dq", "sync", "native_q", "sync", "sync",
                                 "native_dq", "sync", "sync"])
        self.assertTrue(sample["clock_unchanged"])
        self.assertTrue(sample["complete"])

    def test_nonfinite_cached_or_failed_native_stops_reads_and_keeps_partial_sample(self):
        native = mock.Mock(return_value=np.zeros(6))
        with self.assertRaises(state.SnapshotReadError) as caught:
            state.snapshot_read({"q": lambda: [0]*6, "dq": lambda: [float("nan")]*6},
                                {"q": native}, lambda value: np.array(value, copy=True), lambda: None, lambda: (0, 0))
        native.assert_not_called()
        self.assertIsNone(caught.exception.sample["native"]["q"])
        self.assertIsNone(caught.exception.sample["clock_after"])
        self.assertFalse(caught.exception.sample["complete"])
        later = mock.Mock()
        first = ValueError("invalid physical handle")
        with self.assertRaises(state.SnapshotReadError) as caught:
            state.snapshot_read({"q": lambda: [0]*6}, {"q": mock.Mock(side_effect=first), "dq": later},
                                lambda value: np.array(value, copy=True), lambda: None, lambda: (0, 0))
        self.assertIs(caught.exception.__cause__, first)
        later.assert_not_called()
        np.testing.assert_equal(caught.exception.sample["cached"]["q"], np.zeros(6))

    def test_clock_change_is_recorded_without_inserting_any_physics_call(self):
        clock = mock.Mock(side_effect=[(22, .3), (23, .3+1/120)])
        sample = state.snapshot_read({"q": lambda: [0]*6}, {"q": lambda: [0]*6},
                                    lambda value: list(value), lambda: None, clock)
        self.assertFalse(sample["clock_unchanged"])
        self.assertEqual(clock.call_count, 2)
        trace = self.trace()
        self.append(trace, 0, clock_before=(2, 2/120), clock_after=(3, 3/120))
        self.assertEqual(trace.summary()["invalid_sample_count"], 1)

    def test_joint_and_body_name_reordering_preserves_mapping(self):
        poses, velocities = physical_sample()
        for index in range(7):
            q = quat([0, 0, 1], index*.17)
            poses[index, 3:] = q[[1, 2, 3, 0]]
            velocities[index, 5] = index*.23
        expected = state.analyze_links(self.bindings, poses, velocities)
        order = [4, 0, 6, 2, 1, 5, 3]
        joints = list(reversed(JOINTS))
        mapped = state.bind_joint_frames(list(reversed(records())), joints, [BODIES[i] for i in order])
        actual = state.analyze_links(mapped, poses[order], velocities[order])
        np.testing.assert_allclose(actual["angle_rad"], expected["angle_rad"][::-1], atol=1e-14)
        np.testing.assert_allclose(actual["dq_projected_rad_s"], expected["dq_projected_rad_s"][::-1])
        with self.assertRaisesRegex(ValueError, "Missing"):
            state.bind_joint_frames(records()[:-1], JOINTS, BODIES)
        broken = records()
        broken[0]["body0"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown body"):
            state.bind_joint_frames(broken, JOINTS, BODIES)

    def test_nonidentity_parent_frame_and_nonzero_parent_omega(self):
        rows = records()
        local0, local1 = quat([1, 0, 0], math.pi/2), quat([0, 1, 0], math.pi/2)
        rows[0].update(localRot0=local0.tolist(), localRot1=local1.tolist())
        bindings = state.bind_joint_frames(rows, JOINTS, BODIES)
        poses, velocities = physical_sample()
        parent = quat([0, 0, 1], math.pi/2)
        child = mul(mul(mul(parent, local0), quat([0, 0, 1], -.4)), local1*[1, -1, -1, -1])
        poses[0, 3:] = parent[[1, 2, 3, 0]]
        poses[1, 3:] = child[[1, 2, 3, 0]]
        velocities[0, 3:] = [.2, -.3, .4]
        velocities[1, 3:] = [.9, -.25, .4]
        actual = state.analyze_links(bindings, poses, velocities)
        np.testing.assert_allclose(actual["axis_world"][0], [1, 0, 0], atol=1e-14)
        self.assertAlmostEqual(actual["angle_rad"][0], -.4)
        self.assertAlmostEqual(actual["dq_projected_rad_s"][0], .7)
        self.assertAlmostEqual(actual["omega_off_axis_rad_s"][0], .05)
        self.assertAlmostEqual(actual["off_axis_rad"][0], 0)
        self.assertAlmostEqual(actual["axis_alignment_rad"][0], 0, places=7)
        # Nonidentity local frames encode zero correctly without subtracting q.
        child_zero = mul(mul(parent, local0), local1*[1, -1, -1, -1])
        poses[1, 3:] = child_zero[[1, 2, 3, 0]]
        self.assertAlmostEqual(state.analyze_links(bindings, poses, velocities)["angle_rad"][0], 0)

    def test_signed_angles_double_cover_unwrap_and_binding_direction(self):
        poses, velocities = physical_sample()
        q = quat([0, 0, 1], -3.12)
        poses[1, 3:] = q[[1, 2, 3, 0]]
        result = state.analyze_links(self.bindings, poses, velocities, [3.12, None, None, None, None, None])
        self.assertAlmostEqual(result["angle_rad"][0], 2*math.pi-3.12)
        poses[1, 3:] *= -1
        double = state.analyze_links(self.bindings, poses, velocities, result["angle_rad"])
        np.testing.assert_allclose(double["angle_rad"], result["angle_rad"], atol=1e-14)
        rows = records()
        rows[0]["body0"], rows[0]["body1"] = rows[0]["body1"], rows[0]["body0"]
        reverse = state.analyze_links(state.bind_joint_frames(rows, JOINTS, BODIES), poses, velocities)
        self.assertAlmostEqual(reverse["angle_rad"][0], 3.12)

    def test_off_axis_residual_and_singular_twist_are_not_hidden(self):
        poses, velocities = physical_sample()
        q = quat([1, 0, 0], .07)
        poses[1, 3:] = q[[1, 2, 3, 0]]
        actual = state.analyze_links(self.bindings, poses, velocities)
        self.assertAlmostEqual(actual["off_axis_rad"][0], .07)
        self.assertAlmostEqual(actual["axis_alignment_rad"][0], .07)
        poses[1, 3:] = [1, 0, 0, 0]
        actual = state.analyze_links(self.bindings, poses, velocities)
        self.assertIsNone(actual["angle_rad"][0])
        self.assertIsNone(actual["off_axis_rad"][0])
        self.assertFalse(actual["valid"][0])

    def test_missing_fields_remain_null_and_observed_failure_is_preserved(self):
        trace = self.trace()
        trace.append(0, 2/120, 0, 0, status="NOT_OBSERVED")
        self.append(trace, 600)
        trace.mark_failure("joint", "original hold acceptance failed", step=600)
        trace.close()
        summary = trace.summary()
        self.assertFalse(summary["complete_requested_comparison"])
        self.assertEqual(summary["windows"]["strict_hold"]["sample_count"], 1)
        self.assertIsNone(summary["windows"]["motion"]["max_abs"]["angle_rad"])
        self.assertEqual(summary["failures"][0]["category"], "joint")
        self.assertNotIn("acceptance_pass", summary)
        json.dumps(summary, allow_nan=False)
        with trace.path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["agv_x_m"], "")
        self.assertEqual(rows[0]["joint_1_angle_rad"], "")
        self.assertEqual(rows[1]["step"], "600")

    def test_complete_diagnostic_coverage_does_not_overwrite_original_failure(self):
        trace = self.trace()
        poses, velocities = physical_sample()
        analysis = state.analyze_links(self.bindings, poses, velocities)
        for step in range(1, 601):
            trace.append(step, (step+2)/120, step/120, step/120, poses, velocities, analysis,
                         (step+2, (step+2)/120), (step+2, (step+2)/120), comparison_valid=True)
        trace.mark_failure("joint", "original hold acceptance failed", step=600)
        summary = trace.summary()
        self.assertTrue(summary["complete_requested_comparison"])
        self.assertTrue(summary["windows"]["motion"]["complete"])
        self.assertTrue(summary["windows"]["hold_3_4"]["complete"])
        self.assertTrue(summary["windows"]["hold_4_5"]["complete"])
        self.assertFalse(summary["windows"]["strict_hold"]["complete"])
        self.assertEqual(summary["windows"]["strict_hold"]["expected_sample_count"], 121)
        self.assertEqual(summary["failures"][0]["message"], "original hold acceptance failed")
        self.assertEqual(summary["sample_count"], 600)
        self.assertEqual((summary["first_step"], summary["last_step"]), (1, 600))
        trace.flush()
        self.assertTrue(trace.summary()["trace_saved"])
        for field in ("unchanged", "acceptance_snapshot_unchanged"):
            trace.metadata["snapshot_rechecks"] = [{"saved_step": 1, "checked_at_step": 600, field: False}]
            self.assertFalse(trace.summary()["complete_requested_comparison"])
            self.assertTrue(trace.summary()["snapshot_recheck_failed"])
        trace.metadata["snapshot_rechecks"] = [{"unchanged": True, "acceptance_snapshot_unchanged": True}]
        self.assertTrue(trace.summary()["complete_requested_comparison"])
        trace.mark_failure("read", "invalid physical handle", step=600, affects_comparison=True)
        self.assertFalse(trace.summary()["complete_requested_comparison"])

    def test_trace_snapshot_and_io_failure_keep_current_acquired_state(self):
        trace = self.trace()
        poses, velocities = physical_sample()
        analysis = state.analyze_links(self.bindings, poses, velocities)
        self.append(trace, 0, poses=poses, velocities=velocities, analysis=analysis)
        poses[0, 0] = 123
        analysis["angle_rad"][0] = 10
        with mock.patch.object(trace, "_writer") as writer:
            writer.writerow.side_effect = OSError("disk")
            with self.assertRaisesRegex(OSError, "disk"):
                self.append(trace, 1)
        summary = trace.summary()
        self.assertEqual(summary["controlled_sample_count"], 1)
        self.assertIn("disk", summary["recording_error"])
        self.assertEqual(trace._rows[0]["poses"][0][0], 0)
        self.assertEqual(trace._rows[0]["analysis"]["angle_rad"][0], 0)

    def test_nonfinite_or_malformed_observation_is_invalid_without_fabricated_values(self):
        trace = self.trace()
        poses, velocities = physical_sample()
        poses[0, 0] = float("nan")
        self.append(trace, 0, poses=poses)
        summary = trace.summary()
        self.assertEqual(summary["invalid_sample_count"], 1)
        json.dumps(summary, allow_nan=False)
        trace.close()
        with trace.path.open(newline="", encoding="utf-8") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["agv_x_m"], "")
        self.assertFalse(any(name == "torch" or name == "pxr" or name.startswith(("isaaclab", "isaacsim", "omni.")) for name in sys.modules))

    def test_joint_csv_missing_native_is_blank_and_acceptance_failure_stays_failed(self):
        trace = hold.JointTrace(Path(self.temp.name) / "joint.csv", state_consistency=True)
        self.addCleanup(trace.close)
        for step in (0, 1):
            trace.append(step, (step+2)/120, step/120, step/120, [0]*6, [0]*6, [.2]*6, [.03]*6,
                         q_reference=[0]*6)
        trace.mark_check("joint", "FAIL", step=1, details="original velocity failure")
        native = np.arange(6, dtype=float)
        trace.set_state_comparison(1, native, None)
        native[:] = -100
        trace.close()
        with trace.path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["native_q_1_rad"], "")
        self.assertEqual(rows[1]["native_dq_1_rad_s"], "")
        self.assertEqual(float(rows[1]["native_q_2_rad"]), 1)
        self.assertEqual(float(rows[1]["q_1_rad"]), .2)
        self.assertEqual(float(rows[1]["dq_1_rad_s"]), .03)
        self.assertEqual(rows[1]["check_joint"], "FAIL")
        self.assertTrue(trace.summary()["has_failure"])
        with self.assertRaises(ValueError):
            trace.set_state_comparison(1, [0]*6, [0]*6)

    def test_actual_cli_requires_baseline_and_joint_trace_for_state_probe(self):
        class FakeLauncher:
            @staticmethod
            def add_app_launcher_args(parser):
                parser.add_argument("--device", default="cuda:0")
                parser.add_argument("--headless", action="store_true")
                parser.add_argument("--enable_cameras", action="store_true")
                parser.add_argument("--livestream", type=int, default=-1)
                parser.add_argument("--xr", action="store_true")
        usd = Path(self.temp.name) / "parse_only.usd"
        usd.write_text("CPU parser fixture", encoding="utf-8")
        argv = ["run_cr12_joint_drive.py", "--usd-path", str(usd), "--output-dir", self.temp.name,
                "--diagnose-state-consistency", "--record-joint-trace", "--pd-profile", "baseline"]
        with mock.patch.dict(sys.modules, {"_cr12_hold_diagnostics": hold}), mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(sys, "argv", argv):
                args = drive._parse_args(FakeLauncher)
            self.assertTrue(args.diagnose_state_consistency)
            self.assertTrue(args.record_joint_trace)
            self.assertEqual(args.pd_profile, "baseline")
            for invalid in (argv[:-1]+["hold_tune_01"], [arg for arg in argv if arg != "--record-joint-trace"]):
                with mock.patch.object(sys, "argv", invalid), mock.patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
                    drive._parse_args(FakeLauncher)

    def test_actual_probe_with_fake_runtime_uses_bindings_and_never_advances(self):
        poses, velocities = physical_sample()
        view = SimpleNamespace(get_dof_positions=mock.Mock(return_value=np.full((1, 6), .1)),
                               get_dof_velocities=mock.Mock(return_value=np.full((1, 6), .02)),
                               get_link_transforms=mock.Mock(return_value=poses[None]),
                               get_link_velocities=mock.Mock(return_value=velocities[None]))
        robot = SimpleNamespace(root_physx_view=view, device="cuda:0")
        sim = SimpleNamespace(current_time_step_index=3, current_time=3/120)
        q, dq = [.2]*6, [.03]*6
        trace = hold.JointTrace(None, state_consistency=True)
        self.addCleanup(trace.close)
        for step in (0, 1):
            trace.append(step, (step+2)/120, step/120, step/120, [0]*6, [0]*6, q, dq, q_reference=[0]*6)
        link_trace = state.StateConsistencyTrace(None, {**self.metadata, "bindings": self.bindings})
        self.addCleanup(link_trace.close)
        fake_torch = SimpleNamespace(Tensor=type("UnusedTensor", (), {}), cuda=SimpleNamespace(synchronize=mock.Mock()))
        with mock.patch.dict(sys.modules, {"torch": fake_torch, "_cr12_state_consistency": state}):
            drive._probe_state(robot, list(range(6)), sim, q, dq, (3, 3/120), link_trace, trace, 1, (2, 2/120), 1/120)
        self.assertEqual(fake_torch.cuda.synchronize.call_count, 9)
        self.assertEqual((sim.current_time_step_index, sim.current_time), (3, 3/120))
        self.assertEqual(link_trace.summary()["first_step"], 1)
        self.assertEqual(link_trace.summary()["last_step"], 1)
        self.assertEqual(link_trace.summary()["invalid_sample_count"], 0)
        self.assertEqual(trace._rows[1]["q"], tuple(q))
        self.assertEqual(trace._state_comparisons[1]["native_q"], (.1,)*6)
        self.assertTrue(link_trace.metadata["snapshot_rechecks"][0]["acceptance_snapshot_unchanged"])
        tree = ast.parse((ROOT / "scripts/environments/run_cr12_joint_drive.py").read_text(encoding="utf-8"))
        probe = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_probe_state")
        forbidden = {"step", "render", "update", "reset", "write_data_to_sim", "write_joint_state_to_sim",
                     "write_root_state_to_sim", "set_joint_position_target", "set_joint_velocity_target"}
        calls = {node.func.attr for node in ast.walk(probe) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & forbidden)

    def test_actual_probe_preserves_native_failure_when_diagnostic_recording_fails(self):
        primary = ValueError("invalid physical handle")
        view = SimpleNamespace(get_dof_positions=mock.Mock(side_effect=primary),
                               get_dof_velocities=mock.Mock())
        robot = SimpleNamespace(root_physx_view=view, device="cuda:0")
        sim = SimpleNamespace(current_time_step_index=3, current_time=3/120)
        trace = mock.Mock()
        link_trace = mock.Mock()
        link_trace.append.side_effect = OSError("secondary disk error")
        fake_torch = SimpleNamespace(Tensor=type("UnusedTensor", (), {}), cuda=SimpleNamespace(synchronize=mock.Mock()))
        with mock.patch.dict(sys.modules, {"torch": fake_torch, "_cr12_state_consistency": state}):
            with self.assertRaises(drive.DriveCheckError) as caught:
                drive._probe_state(robot, list(range(6)), sim, [0]*6, [0]*6, (3, 3/120),
                                   link_trace, trace, 1, (2, 2/120), 1/120)
        self.assertEqual(caught.exception.category, "state_invalid")
        self.assertIn("invalid physical handle", caught.exception.details["error"])
        self.assertIn("secondary disk error", caught.exception.details["secondary_recording_error"])
        self.assertIs(caught.exception.__cause__.__cause__, primary)
        view.get_dof_velocities.assert_not_called()
        self.assertIsNone(link_trace.append.call_args.kwargs["clock_after"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
