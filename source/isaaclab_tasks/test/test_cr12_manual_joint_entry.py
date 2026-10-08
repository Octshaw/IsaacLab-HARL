"""CPU entry-boundary checks; no App, CUDA, physics or package initialization."""
import argparse
import ast
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts/environments"))
import run_cr12_manual_joint_sweep as entry


class FakeLauncher:
    @staticmethod
    def add_app_launcher_args(parser):
        parser.add_argument("--device", default="cuda:0")
        parser.add_argument("--headless", action="store_true")
        parser.add_argument("--enable_cameras", action="store_true")
        parser.add_argument("--livestream", type=int, default=-1)
        parser.add_argument("--xr", action="store_true")
        parser.add_argument("--kit_args", default="")
        parser.add_argument("--info", action="store_true")


class EntryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cr12_sweep_entry_")
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.private = self.output / "private_config/user.config.json"
        self.private.parent.mkdir()
        self.private.write_text(json.dumps({"persistent": {"app": {"window": {
            "width": 1440, "height": 900, "maximized": False}}}}), encoding="utf-8")
        self.env = patch.dict("os.environ", {"HEADLESS": "0", "ENABLE_CAMERAS": "0", "LIVESTREAM": "0", "XR": "0"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.stderr = patch("sys.stderr", new_callable=io.StringIO)
        self.stderr.start()
        self.addCleanup(self.stderr.stop)

    def argv(self):
        return ["--usd-path", str(entry.APPROVED_USD), "--output-dir", str(self.output),
                "--external-forces-every-iteration", "on", "--profile", entry.PROFILE_NAME,
                "--geometry_mode", entry.GEOMETRY_MODE, "--view", "arm-oblique",
                "--kit_args=--/app/userConfigPath=" + self.private.as_posix()]

    def test_full_cli_private_forwarding_and_explicit_mode(self):
        args = entry.parse_args(FakeLauncher, self.argv())
        self.assertEqual(args.private_user_config, str(self.private.resolve()))
        self.assertEqual(args.external_forces_source, "explicit_cli")
        self.assertEqual(args.geometry_mode, entry.GEOMETRY_MODE)
        self.assertEqual(args.view, "arm-oblique")

    def test_no_private_never_falls_back(self):
        with self.assertRaises(SystemExit):
            entry.parse_args(FakeLauncher, self.argv()[:-1])

    def test_duplicate_private_rejected(self):
        token = "--/app/userConfigPath=" + self.private.as_posix()
        with self.assertRaises(ValueError):
            entry.validate_private_path(token + " " + token, self.output)

    def test_other_output_private_rejected(self):
        with self.assertRaises(ValueError):
            entry.validate_private_path("--/app/userConfigPath=" + self.private.as_posix(), self.output / "other")

    def test_unprepared_private_rejected(self):
        tree = json.loads(self.private.read_text())
        tree["persistent"]["app"]["window"]["width"] = -1
        self.private.write_text(json.dumps(tree))
        with self.assertRaises(ValueError):
            entry.validate_private_path("--/app/userConfigPath=" + self.private.as_posix(), self.output)

    def test_boolean_type_cannot_be_integer(self):
        tree = json.loads(self.private.read_text())
        tree["persistent"]["app"]["window"]["maximized"] = 0
        self.private.write_text(json.dumps(tree))
        with self.assertRaises(ValueError):
            entry.validate_private_path("--/app/userConfigPath=" + self.private.as_posix(), self.output)

    def test_no_runtime_angle_or_duration_override(self):
        for extra in (["--angle", "15"], ["--physics_steps", "10"], ["--motion-seconds", "2"]):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, self.argv() + extra)

    def test_gui_only_and_external_forces_explicit(self):
        for extra in (["--headless"], ["--enable_cameras"], ["--device", "cpu"],
                      ["--external-forces-every-iteration", "inherit"]):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, self.argv() + extra)

    def test_runtime_loop_has_one_step_and_no_state_or_ik_writes(self):
        tree = ast.parse(Path(entry.__file__).read_text(encoding="utf-8"))
        runner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_run_sweep")
        calls = [node.func.attr for node in ast.walk(runner) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertEqual(calls.count("step"), 1)
        for forbidden in ("write_joint_state_to_sim", "write_root_state_to_sim", "compute", "get_jacobians"):
            self.assertNotIn(forbidden, calls)
        self.assertIn("set_joint_position_target", calls)
        self.assertIn("set_joint_velocity_target", calls)
        self.assertIn("write_data_to_sim", calls)

    def test_post_step_geometry_consumes_physical_body_poses(self):
        source = Path(entry.__file__).read_text(encoding="utf-8")
        self.assertIn('poses = _body_poses(robot, body_ids)', source)
        self.assertIn('inspect(poses, "actual")', source)
        self.assertIn('inspect(model.forward(q + ratio*(ref.q-q), poses["agv"]), "pre_submit")', source)
        self.assertIn('geometry_check=initial_geometry', source)

    def test_trace_preserves_failed_sample_and_actual_fields(self):
        trace = entry.SweepTrace(self.output / "trace.csv")
        trace.append({"step": 1, "status": "FAIL", "failure": "contact",
                      "q": [0, 0, .1, 0, 0, 0], "actual_p": [1, 2, 3]})
        trace.close()
        self.assertEqual(trace.count, 1)
        import csv
        with (self.output / "trace.csv").open(newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual(float(row["q_2"]), .1)
        self.assertEqual(float(row["actual_p_2"]), 3)

    def test_secondary_summary_failure_keeps_primary_and_csv(self):
        monitor, pacer, recorder, trace = Mock(), Mock(), Mock(), Mock()
        recorder.result = {}
        monitor.summary.return_value = {"status": "FAILED"}
        pacer.summary.side_effect = ValueError("clock summary")
        sample = {"status": "FAIL", "failure": "original contact"}
        primary = RuntimeError("original contact")
        entry.finish_sweep_sample(trace, sample, recorder, monitor, pacer, .1, primary)
        recorder.secondary.assert_called_once()
        trace.append.assert_called_once_with(sample)
        self.assertEqual(sample["failure"], "original contact")

    def test_first_recording_failure_still_writes_csv_before_raise(self):
        monitor, pacer, recorder, trace = Mock(), Mock(), Mock(), Mock()
        recorder.result = {}
        monitor.summary.return_value = {}
        pacer.summary.side_effect = ValueError("clock summary")
        sample = {"status": "PASS"}
        with self.assertRaisesRegex(ValueError, "clock summary"):
            entry.finish_sweep_sample(trace, sample, recorder, monitor, pacer, .1, None)
        trace.append.assert_called_once_with(sample)
        self.assertEqual(sample["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
