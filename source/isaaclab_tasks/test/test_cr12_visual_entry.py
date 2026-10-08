"""Focused CPU boundaries for visual inspection; no real App or render calls."""
from __future__ import annotations

import io
import ast
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import zlib

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts/environments"))
import inspect_cr12_visual_geometry as entry


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

    def __init__(self, *_args, **_kwargs):
        raise AssertionError("CPU entry tests must never construct an App")


def png_bytes(width=1, height=1):
    """Small synthetic PNG, not a runtime screenshot or rendering evidence."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0\0\0\0"))
            + chunk(b"IEND", b""))


class VisualEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cr12_visual_entry_cpu_")
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name).resolve()
        self.private = self.output / "private_config/user.config.json"
        self.private.parent.mkdir()
        self.private.write_text(json.dumps({"persistent": {"app": {"window": {
            "width": 1440, "height": 900, "maximized": False}}}}), encoding="utf-8")
        self.env = patch.dict("os.environ", {"HEADLESS": "0", "ENABLE_CAMERAS": "0",
                                             "LIVESTREAM": "0", "XR": "0"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.stderr = patch("sys.stderr", new_callable=io.StringIO)
        self.stderr.start()
        self.addCleanup(self.stderr.stop)

    def argv(self):
        return ["--usd-path", str(entry.APPROVED_USD), "--output-dir", str(self.output),
                "--device", "cuda:0", "--external-forces-every-iteration", "on", "--info",
                "--kit_args=--/app/userConfigPath=" + self.private.as_posix()]

    def test_actual_cli_and_manual_flag(self):
        args = entry.parse_args(FakeLauncher, self.argv())
        self.assertEqual(args.private_user_config, str(self.private))
        self.assertEqual(args.external_forces_source, "explicit_cli")
        self.assertFalse(args.manual_check)
        self.assertTrue(entry.parse_args(FakeLauncher, self.argv() + ["--manual-check"]).manual_check)

    def test_missing_or_wrong_private_does_not_fall_back(self):
        with self.assertRaises(SystemExit):
            entry.parse_args(FakeLauncher, self.argv()[:-1])
        wrong = self.output / "wrong"
        argv = self.argv()
        argv[argv.index("--output-dir") + 1] = str(wrong)
        with self.assertRaises(SystemExit):
            entry.parse_args(FakeLauncher, argv)

    def test_gui_only_and_explicit_on(self):
        for extra in (["--device", "cpu"], ["--headless"], ["--enable_cameras"],
                      ["--livestream", "1"], ["--external-forces-every-iteration", "inherit"]):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, self.argv() + extra)

    def test_no_sweep_or_controlled_steps_cli(self):
        for extra in (["--profile", "j3_visible_roundtrip_v1"], ["--physics_steps", "2520"],
                      ["--geometry_mode", "aabb_then_obb_margin_v1"]):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, self.argv() + extra)

    def test_complete_png_metadata_without_modification(self):
        path = self.output / "agv_as_loaded.png"
        data = png_bytes()
        path.write_bytes(data)
        result = entry.png_complete(path)
        self.assertEqual((result["width"], result["height"], result["bytes"]), (1, 1, len(data)))
        self.assertEqual(path.read_bytes(), data)

    def test_png_missing_truncated_or_invalid_dimensions_not_complete(self):
        path = self.output / "incomplete.png"
        self.assertIsNone(entry.png_complete(path))
        for data in (b"", b"not PNG" * 8, png_bytes()[:-1], png_bytes()[:-12],
                     png_bytes(width=0), png_bytes(height=0)):
            with self.subTest(size=len(data)):
                path.write_bytes(data)
                self.assertIsNone(entry.png_complete(path))

    def test_pause_is_queued_until_commit_without_ui_update(self):
        class Timeline:
            playing, stopped = True, False
            calls = []
            def pause(self):
                self.calls.append("pause")
            def commit(self):
                self.calls.append("commit")
                self.playing = False
            def is_playing(self):
                return self.playing
            def is_stopped(self):
                return self.stopped
        timeline = Timeline()
        entry.commit_pause(timeline)
        self.assertEqual(timeline.calls, ["pause", "commit"])
        self.assertFalse(timeline.is_playing())
        self.assertFalse(timeline.is_stopped())

    def test_commit_pause_rejects_failed_pause_or_stop(self):
        for playing, stopped in ((True, False), (False, True)):
            timeline = types.SimpleNamespace(pause=lambda: None, commit=lambda: None,
                is_playing=lambda: playing, is_stopped=lambda: stopped)
            with self.assertRaises(entry.DriveCheckError):
                entry.commit_pause(timeline)

    def test_existing_result_rejected_before_app_without_overwrite(self):
        result_path = self.output / "result.json"
        original = b'{"previous":"do not replace"}\n'
        result_path.write_bytes(original)
        app_module = types.ModuleType("isaaclab.app")
        app_module.AppLauncher = FakeLauncher
        package = types.ModuleType("isaaclab")
        package.__path__ = []
        args = types.SimpleNamespace(output_dir=self.output)
        guarded = Mock(side_effect=AssertionError("No runtime check is allowed"))
        # main stops at the existing result branch before any runtime imports or App construction.
        with patch.dict(sys.modules, {"isaaclab": package, "isaaclab.app": app_module}), \
                patch.object(entry, "parse_args", return_value=args), \
                patch.object(entry, "_run_check", guarded), \
                patch.object(entry.Recorder, "emit"):
            with self.assertRaises(FileExistsError):
                entry.main()
        guarded.assert_not_called()
        self.assertEqual(result_path.read_bytes(), original)


class PreinitLifecycleTests(unittest.TestCase):
    def views(self, *, initialized=True, sim_valid=True, sim_check=True, art_check=True):
        self.calls = []
        simulation = types.SimpleNamespace(is_valid=sim_valid,
            check=lambda: self.calls.append("simulation_check") or sim_check)
        articulation = types.SimpleNamespace(check=lambda: self.calls.append("articulation_check") or art_check)
        return (types.SimpleNamespace(is_initialized=initialized, root_physx_view=articulation),
                types.SimpleNamespace(physics_sim_view=simulation, current_time_step_index=2, current_time=.02))

    def test_exposed_validity_queried_in_order(self):
        robot, sim = self.views()
        actual = entry.native_view_validity(robot, sim)
        self.assertEqual(self.calls, ["simulation_check", "articulation_check"])
        self.assertTrue(all(actual.values()))

    def test_cleanup_failure_preserves_primary_and_separate_secondary(self):
        recorder = entry.Recorder()
        first, second = ValueError("native read failed"), RuntimeError("close failed")
        with patch.object(recorder, "emit"), patch("sys.stderr", new_callable=io.StringIO):
            self.assertIs(entry.cleanup_failure(recorder, first, "native_initial", None), first)
            self.assertIs(entry.cleanup_failure(recorder, second, "app_close", first), first)
        self.assertEqual(recorder.result["failures"][0]["message"], "native read failed")
        self.assertEqual(recorder.result["secondary_failures"][0]["message"], "close failed")
        self.assertEqual(recorder.result["status"], "FAILED")

    def test_invalid_view_never_calls_parameter_reader(self):
        for parameters in ({"initialized": False}, {"sim_valid": False},
                           {"sim_check": False}, {"art_check": False}):
            robot, sim = self.views(**parameters)
            scene = {"robot": robot, "sim": sim}
            with self.subTest(parameters=parameters), patch.object(entry, "_read_physics") as read:
                with self.assertRaises(entry.DriveCheckError) as caught:
                    entry.read_native_snapshot(scene, {}, entry.Recorder(), "initial")
                self.assertEqual(caught.exception.category, "NATIVE_VIEW_INVALID")
                read.assert_not_called()

    def test_missing_view_is_invalid_not_not_exposed(self):
        robot, sim = self.views()
        sim.physics_sim_view = None
        with self.assertRaises(entry.DriveCheckError):
            entry.native_view_validity(robot, sim)

    def test_unexposed_query_is_explicit(self):
        robot = types.SimpleNamespace(is_initialized=True, root_physx_view=object())
        sim = types.SimpleNamespace(physics_sim_view=object())
        result = entry.native_view_validity(robot, sim)
        self.assertEqual(result["simulation_is_valid"], "NOT_EXPOSED")
        self.assertEqual(result["simulation_check"], "NOT_EXPOSED")
        self.assertEqual(result["articulation_check"], "NOT_EXPOSED")

    @staticmethod
    def snapshot():
        return {"raw": {"body_order": ["body"], "joint_order": ["joint"],
            "inertia_convention": "body axes", "mass": [2.0],
            "com_local_xyz_xyzw": [[0., 0., 0., 0., 0., 0., 1.]],
            "inertia_about_com_body_axes": [[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]],
            "joint_parameters": {"position_limits": [[-2., 2.]], "stiffness": [100.],
                                 "damping": [20.], "friction": [0.], "armature": [0.]}},
            "checked": {"body_order": ["body"], "joint_order": ["joint"],
                        "body_indices": [0], "joint_indices": [0], "is_fixed_base": True}}

    def test_native_snapshot_deepcopy_before_later_getter_reuses_buffers(self):
        robot, sim = self.views()
        scene = {"robot": robot, "sim": sim, "configuration": object(), "selected_pd": {}}
        recorder = entry.Recorder()
        sample = self.snapshot()
        def reader(*args):
            recorder.result["physx_raw_readback"] = sample["raw"]
            return [0], [0], sample["checked"]
        with patch.object(entry, "_read_physics", side_effect=reader), patch.object(recorder, "emit"):
            first = entry.read_native_snapshot(scene, {"bodies": {}}, recorder, "initial")
            sample["raw"]["mass"][0] = 9.
            sample["checked"]["body_indices"][0] = 3
            final = entry.read_native_snapshot(scene, {"bodies": {}}, recorder, "final")
        self.assertEqual(first["raw"]["mass"], [2.])
        self.assertEqual(first["checked"]["body_indices"], [0])
        self.assertEqual(final["raw"]["mass"], [9.])

    def test_compare_physical_parameters_not_runtime_states(self):
        first = self.snapshot()
        final = copy.deepcopy(first)
        first["runtime_q"] = [0.]
        final["runtime_q"] = [.001]
        result = entry.compare_native_parameters(first, final)
        self.assertTrue(result["equal"])
        self.assertFalse(result["runtime_q_dq_world_poses_compared_as_configuration"])
        final["raw"]["mass"][0] = 3.
        with self.assertRaises(entry.DriveCheckError):
            entry.compare_native_parameters(first, final)

    def test_hold_basic_guards_without_old_progress_or_precision_windows(self):
        limits = [[-3., 3.]]*6
        self.assertEqual(entry.check_hold_state([.01]*6, [.02]*6, limits), (.01, .02))
        for q, dq in (([float("nan")]*6, [0.]*6), ([4.]*6, [0.]*6), ([0.]*6, [.251]*6)):
            with self.assertRaises(entry.DriveCheckError):
                entry.check_hold_state(q, dq, limits)

    def test_paused_capture_has_no_native_getters_step_reset_or_layer_change(self):
        tree = ast.parse(Path(entry.__file__).read_text(encoding="utf-8"))
        render = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "render_corrected")
        calls = [n.func for n in ast.walk(render) if isinstance(n, ast.Call)]
        forbidden = {"step", "reset", "revoke", "apply", "_read_physics", "native_view_validity",
                     "read_native_snapshot", "get_masses", "get_dof_positions", "get_dof_velocities"}
        names = {f.attr if isinstance(f, ast.Attribute) else f.id for f in calls if isinstance(f, (ast.Attribute, ast.Name))}
        self.assertFalse(names & forbidden)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        finally_nodes = [part for n in ast.walk(main) if isinstance(n, ast.Try) for part in n.finalbody]
        for node in finally_nodes:
            for call in (n for n in ast.walk(node) if isinstance(n, ast.Call)):
                name = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                self.assertNotIn(name, forbidden - {"step", "reset"})

    def test_fake_lifecycle_order_and_failure_does_not_finish(self):
        # Drive the real orchestrator with fake scene/backend; no Isaac imports.
        events = []
        timeline = types.SimpleNamespace(is_playing=lambda: False, is_stopped=lambda: True)
        omni = types.ModuleType("omni"); omni.__path__ = []
        physx = types.ModuleType("omni.physx")
        physx.get_physx_interface = lambda: types.SimpleNamespace(is_running=lambda: False)
        physx.get_physx_simulation_interface = lambda: types.SimpleNamespace(get_attached_stage=lambda: 0)
        timeline_module = types.ModuleType("omni.timeline")
        timeline_module.get_timeline_interface = lambda: timeline
        omni.physx, omni.timeline = physx, timeline_module
        sim = types.SimpleNamespace(physics_sim_view=None, is_simulating=lambda: False)
        robot = types.SimpleNamespace(is_initialized=False)
        layer = types.SimpleNamespace(identifier="original")
        stage = types.SimpleNamespace(GetEditTarget=lambda: types.SimpleNamespace(GetLayer=lambda: layer))
        scene = {"sim": sim, "robot": robot, "stage": stage, "setup": {},
                 "physx_schema": None, "usd_physics": None, "default_time": None}
        override = Mock()
        override.apply.side_effect = lambda **kw: events.append("apply_preinit") or {"saved_to_disk": False}
        override.verify_stable.side_effect = lambda phase: {"collision_leaves_invisible": 10, "visuals_visible": 10}
        def create(*args, pre_physics, before_native_read):
            events.append("reference_exists")
            pre_physics(stage=stage, sim=sim, robot=robot, info={})
            events.append("first_reset_and_view_creation")
            before_native_read(robot=robot, sim=sim)
            return scene
        def read(scene, expected, recorder, label):
            events.append("native_"+label)
            return self.snapshot()
        args = types.SimpleNamespace(usd_path=entry.APPROVED_USD)
        import _cr12_visual_geometry as vg
        import _cr12_external_forces as ef
        for failed_stage in (None, "hold", "render"):
            events.clear(); override.reset_mock()
            recorder = entry.Recorder()
            def hold(*_):
                events.append("hold120")
                if failed_stage == "hold":
                    raise entry.DriveCheckError("geometry_guard", "synthetic failure")
            def render(*_):
                events.append("pause_then_screenshots")
                if failed_stage == "render":
                    raise entry.DriveCheckError("screenshot_timeout", "synthetic failure")
            with patch.dict(sys.modules, {"omni": omni, "omni.physx": physx, "omni.timeline": timeline_module}), \
                    patch.object(vg, "inspect_preinit_mapping", return_value={"pass": True}), \
                    patch.object(vg, "physical_snapshot", return_value={"physics": "unchanged"}), \
                    patch.object(vg, "CollisionVisualOverride", return_value=override), \
                    patch.object(ef, "read_scene_external_forces"), \
                    patch.object(entry, "source_protection", return_value={"asset": "unchanged"}), \
                    patch.object(entry, "create_fixed_cr12_scene", side_effect=create), \
                    patch.object(entry, "initialize_fixed_cr12_state", side_effect=lambda *_: events.append("initial_state_write") or {}), \
                    patch.object(entry, "native_view_validity", return_value={"initialized": True}), \
                    patch.object(entry, "read_native_snapshot", side_effect=read), \
                    patch.object(entry, "run_hold", side_effect=hold), \
                    patch.object(entry, "render_corrected", side_effect=render), patch.object(recorder, "emit"):
                if failed_stage:
                    with self.assertRaises(entry.DriveCheckError):
                        entry._run_check(args, object(), recorder, {}, {})
                    self.assertFalse(recorder.result["work_completed"])
                    if failed_stage == "hold":
                        self.assertNotIn("native_final", events)
                        self.assertNotIn("pause_then_screenshots", events)
                else:
                    entry._run_check(args, object(), recorder, {}, {})
                    self.assertEqual(events, ["reference_exists", "apply_preinit", "first_reset_and_view_creation",
                        "initial_state_write", "native_initial", "hold120", "native_final", "pause_then_screenshots"])
                    self.assertTrue(recorder.result["work_completed"])
                override.apply.assert_called_once_with(before_first_physics_initialization=True)
                override.revoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()

