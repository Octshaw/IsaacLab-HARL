"""CPU fake-scene tests; no USD, Isaac, CUDA, asset import, or physics is started."""

import argparse
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[3]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


forces = load("_cr12_external_forces", "scripts/environments/_cr12_external_forces.py")
state = load("_cr12_state_consistency", "scripts/environments/_cr12_state_consistency.py")
TIMING = {"before_first_physics_initialization": True, "physics_initialized": False,
          "physics_running": False, "timeline_playing": False, "reset_started": False, "physics_attached": False,
          "callsite": "synthetic CPU test before any initialization"}
DEFAULT_TIME = object()


class FakeSpec:
    def __init__(self, layer, path, value):
        self.layer, self.path, self.default = layer, path, value

    def HasInfo(self, key):
        return key == "default"


class FakeAttribute:
    def __init__(self, stage):
        self.stage = stage
        self.valid, self.type_name, self.value = True, "bool", False
        self.stack, self.calls, self.property_stack_times = [], [], []
        self.raise_on_set, self.ignore_set, self.set_return = None, False, True

    def __bool__(self):
        return self.valid

    def IsValid(self):
        return self.valid

    def GetTypeName(self):
        return self.type_name

    def GetPath(self):
        return "/physicsScene." + forces.PROPERTY_NAME

    def Get(self):
        return self.value

    def HasAuthoredValueOpinion(self):
        return bool(self.stack)

    def GetPropertyStack(self, time):
        if time is not DEFAULT_TIME:
            raise AssertionError("GetPropertyStack requires the caller's explicit default TimeCode")
        self.property_stack_times.append(time)
        return self.stack

    def Set(self, value):
        self.calls.append((self.stage.edit_target, value))
        if self.raise_on_set is not None:
            raise self.raise_on_set
        if not self.ignore_set:
            self.value = value
            self.stack = [FakeSpec(self.stage.edit_target, self.GetPath(), value)]
        return self.set_return


class FakeScene:
    pass


class FakeAPI:
    def __init__(self, prim):
        self.prim = prim

    def GetEnableExternalForcesEveryIterationAttr(self):
        return self.prim.stage.attr


class FakePrim:
    def __init__(self, stage):
        self.stage = stage
        self.valid, self.scene_type, self.applied = True, True, True

    def __bool__(self):
        return self.valid

    def IsValid(self):
        return self.valid

    def IsA(self, schema):
        return self.scene_type and schema is FakeScene

    def HasAPI(self, schema):
        return self.applied


class FakeStage:
    def __init__(self):
        self.session = SimpleNamespace(identifier="anon:session", anonymous=True)
        self.root = SimpleNamespace(identifier="anon:scene", anonymous=True)
        self.session.GetLayer = lambda: self.session
        self.root.GetLayer = lambda: self.root
        self.edit_target = self.root
        self.edit_calls = []
        self.attr = FakeAttribute(self)
        self.prim = FakePrim(self)

    def GetPrimAtPath(self, path):
        return self.prim if path == "/physicsScene" else None

    def GetSessionLayer(self):
        return self.session

    def GetEditTarget(self):
        return self.edit_target

    def SetEditTarget(self, target):
        self.edit_calls.append(target)
        self.edit_target = target


PHYSX = SimpleNamespace(PhysxSceneAPI=FakeAPI)
USD_PHYSICS = SimpleNamespace(Scene=FakeScene)


class ExternalForcesTests(unittest.TestCase):
    def apply(self, stage, mode="inherit", source="default_inherit", timing=None, physx=None):
        return forces.apply_scene_external_forces(stage, "/physicsScene", mode, source,
                                                 TIMING if timing is None else timing,
                                                 PHYSX if physx is None else physx, USD_PHYSICS,
                                                 default_time=DEFAULT_TIME)

    def test_explicit_default_time_is_required_and_forwarded_to_every_stack_read(self):
        for function in (forces.apply_scene_external_forces, forces.read_scene_external_forces, forces._snapshot):
            self.assertIs(inspect.signature(function).parameters["default_time"].default, inspect.Parameter.empty)
        stage = FakeStage()
        with self.assertRaises(TypeError):
            stage.attr.GetPropertyStack()
        record = self.apply(stage, "on", "explicit_cli")
        forces.read_scene_external_forces(stage, record, "after_first_reset", PHYSX, USD_PHYSICS, DEFAULT_TIME)
        self.assertEqual(len(stage.attr.property_stack_times), 3)
        self.assertTrue(all(value is DEFAULT_TIME for value in stage.attr.property_stack_times))

    def test_default_inherit_does_not_author_or_change_edit_target(self):
        stage = FakeStage()
        original = stage.GetEditTarget()
        result = self.apply(stage)
        self.assertEqual(stage.attr.calls, [])
        self.assertEqual(stage.edit_calls, [])
        self.assertIs(stage.GetEditTarget(), original)
        self.assertEqual(result["mode"], "inherit")
        self.assertEqual(result["source"], "default_inherit")
        self.assertFalse(result["before"]["resolved"])
        self.assertFalse(result["after"]["resolved"])
        self.assertFalse(result["after"]["authored"])
        self.assertFalse(result["authored_by_helper"])
        self.assertEqual(result["after"]["property_stack"], [])
        self.assertIn("no native", result["evidence_level"])
        json.dumps(result, allow_nan=False)

    def test_inherit_preserves_different_valid_initial_value_and_opinion(self):
        stage = FakeStage()
        stage.attr.value = True
        stage.attr.stack = [FakeSpec(stage.root, stage.attr.GetPath(), True)]
        result = self.apply(stage)
        self.assertFalse(result["initial_matches_false_baseline"])
        self.assertTrue(result["expected"])
        self.assertTrue(result["after"]["resolved"])
        self.assertTrue(result["after"]["authored"])
        self.assertEqual(stage.attr.calls, [])
        self.assertEqual(stage.edit_calls, [])
        self.assertEqual(result["after"]["property_stack"], result["before"]["property_stack"])

    def test_on_off_author_only_session_and_restore_original_target(self):
        for mode, expected in (("on", True), ("off", False)):
            with self.subTest(mode=mode):
                stage = FakeStage()
                original = stage.GetEditTarget()
                result = self.apply(stage, mode, "explicit_cli")
                self.assertEqual(stage.attr.calls, [(stage.session, expected)])
                self.assertEqual(stage.edit_calls, [stage.session, original])
                self.assertIs(stage.GetEditTarget(), original)
                self.assertTrue(result["authored_by_helper"])
                self.assertTrue(result["edit_target_restored"])
                self.assertIs(result["expected"], expected)
                self.assertIs(result["after"]["resolved"], expected)
                self.assertTrue(result["after"]["authored"])
                self.assertEqual(result["after"]["property_stack"][0]["layer"], "anon:session")
                self.assertEqual(result["source"], "explicit_cli")

    def test_set_exception_or_false_return_still_restores_original_target(self):
        for failure in (ValueError("synthetic set failure"), False):
            stage = FakeStage()
            original = stage.GetEditTarget()
            if failure is False:
                stage.attr.set_return = False
            else:
                stage.attr.raise_on_set = failure
            with self.assertRaises(forces.SceneExternalForcesError) as caught:
                self.apply(stage, "on", "explicit_cli")
            self.assertIs(stage.GetEditTarget(), original)
            self.assertTrue(caught.exception.record["edit_target_restored"])
            self.assertEqual(caught.exception.record["status"], "SETUP_CONFIG_FAILED")
            self.assertEqual(caught.exception.category, "external_forces_setup_config")

    def test_failed_session_target_switch_cannot_author_into_original_layer(self):
        stage = FakeStage()
        stage.SetEditTarget = lambda target: None
        with self.assertRaises(forces.SceneExternalForcesError) as caught:
            self.apply(stage, "on", "explicit_cli")
        self.assertIn("refusing to author", str(caught.exception))
        self.assertEqual(stage.attr.calls, [])
        self.assertIs(stage.GetEditTarget(), stage.root)

    def test_initial_baseline_difference_is_observed_but_never_overwritten(self):
        for resolved, authored in ((True, False), (False, True), (True, True)):
            stage = FakeStage()
            stage.attr.value = resolved
            if authored:
                stage.attr.stack = [FakeSpec(stage.root, stage.attr.GetPath(), resolved)]
            with self.assertRaises(forces.SceneExternalForcesError) as caught:
                self.apply(stage, "on", "explicit_cli")
            self.assertIs(caught.exception.record["before"]["resolved"], resolved)
            self.assertIs(caught.exception.record["before"]["authored"], authored)
            self.assertEqual(stage.attr.calls, [])
            self.assertEqual(stage.edit_calls, [])

    def test_late_or_missing_timing_guard_is_rejected_before_mutation(self):
        for key in ("before_first_physics_initialization", "physics_initialized", "physics_running", "timeline_playing",
                    "reset_started", "physics_attached"):
            timing = dict(TIMING)
            timing[key] = not timing[key]
            stage = FakeStage()
            with self.assertRaises(forces.SceneExternalForcesError):
                self.apply(stage, "on", "explicit_cli", timing)
            self.assertEqual(stage.attr.calls, [])
        with self.assertRaises(forces.SceneExternalForcesError):
            self.apply(FakeStage(), "on", "explicit_cli", {})

    def test_invalid_scene_api_and_attribute_do_not_silently_continue(self):
        cases = (("prim", "valid", False), ("prim", "scene_type", False), ("prim", "applied", False),
                 ("attr", "valid", False), ("attr", "type_name", "float"), ("attr", "value", None))
        for target, field, value in cases:
            stage = FakeStage()
            setattr(getattr(stage, target), field, value)
            with self.assertRaises(forces.SceneExternalForcesError):
                self.apply(stage, "on", "explicit_cli")
            self.assertEqual(stage.attr.calls, [])
        with self.assertRaises(forces.SceneExternalForcesError):
            self.apply(FakeStage(), "on", "explicit_cli", physx=SimpleNamespace(PhysxSceneAPI=lambda prim: object()))
        stage = FakeStage()
        stage.session.anonymous = False
        with self.assertRaises(forces.SceneExternalForcesError):
            self.apply(stage, "on", "explicit_cli")
        self.assertEqual(stage.attr.calls, [])

    def test_immediate_readback_mismatch_is_configuration_failure(self):
        stage = FakeStage()
        stage.attr.ignore_set = True
        with self.assertRaises(forces.SceneExternalForcesError) as caught:
            self.apply(stage, "on", "explicit_cli")
        self.assertFalse(caught.exception.record["last_readback"]["resolved"])
        self.assertFalse(caught.exception.record["last_readback"]["matches_expected"])
        self.assertIs(stage.GetEditTarget(), stage.root)

    def test_phased_readbacks_keep_last_value_and_mismatch_failure_sticky(self):
        stage = FakeStage()
        result = self.apply(stage, "on", "explicit_cli")
        for phase in ("after_first_reset", "before_motion", "before_exit"):
            actual = forces.read_scene_external_forces(stage, result, phase, PHYSX, USD_PHYSICS, DEFAULT_TIME)
            self.assertEqual(actual["phase"], phase)
            self.assertIs(actual["resolved"], True)
        stage.attr.value = False
        with self.assertRaises(forces.SceneExternalForcesError):
            forces.read_scene_external_forces(stage, result, "exit_last_read", PHYSX, USD_PHYSICS, DEFAULT_TIME)
        self.assertFalse(result["last_readback"]["resolved"])
        self.assertEqual(result["last_readback"]["phase"], "exit_last_read")
        stage.attr.value = True
        forces.read_scene_external_forces(stage, result, "later_read", PHYSX, USD_PHYSICS, DEFAULT_TIME)
        self.assertEqual(result["status"], "SETUP_CONFIG_FAILED")
        self.assertTrue(result["failures"])

    def test_wrong_opinion_source_is_not_accepted_as_session_override(self):
        stage = FakeStage()
        result = self.apply(stage, "on", "explicit_cli")
        stage.attr.stack[0].layer = stage.root
        with self.assertRaises(forces.SceneExternalForcesError):
            forces.read_scene_external_forces(stage, result, "before_controlled_steps", PHYSX, USD_PHYSICS, DEFAULT_TIME)
        self.assertEqual(result["last_readback"]["property_stack"][0]["layer"], "anon:scene")

    def test_state_600_failure_and_720_observed_coverage_do_not_change_acceptance(self):
        metadata = {"body_names": ["agv", *(f"link_{i}" for i in range(1, 7))],
                    "joint_names": [f"joint_{i}" for i in range(1, 7)]}
        poses, velocities = np.zeros((7, 7)), np.zeros((7, 6))
        poses[:, 6] = 1
        analysis = {name: [0.]*6 for name in state.DERIVED_FIELDS}
        analysis["valid"] = [True]*6
        for end in (600, 720):
            trace = state.StateConsistencyTrace(None, metadata)
            self.assertFalse(trace.summary()["observed_comparison_complete"])
            for step in range(1, end+1):
                trace.append(step, (step+2)/120, step/120, step/120, poses, velocities, analysis,
                             (step+2, (step+2)/120), (step+2, (step+2)/120), comparison_valid=True)
            outcome = {"status": "FAILED" if end == 600 else "PASSED", "exit_code": 0}
            if end == 600:
                trace.mark_failure("joint", "original strict-hold failure", step=600)
            outcome["state_consistency"] = trace.summary()
            summary = outcome["state_consistency"]
            self.assertTrue(summary["observed_comparison_complete"])
            self.assertTrue(summary["complete_requested_comparison"])
            self.assertEqual(summary["windows"]["all_controlled"]["complete"], end == 720)
            self.assertEqual(summary["windows"]["strict_hold"]["sample_count"], 1 if end == 600 else 121)
            self.assertEqual(outcome["status"], "FAILED" if end == 600 else "PASSED")
            if end == 600:
                self.assertEqual(summary["failures"][0]["category"], "joint")
            trace.metadata["snapshot_rechecks"] = [{"unchanged": False}]
            self.assertFalse(trace.summary()["observed_comparison_complete"])
            trace.close()

    def test_observed_coverage_rejects_gaps_invalid_rows_and_diagnostic_failure(self):
        metadata = {"body_names": [str(i) for i in range(7)], "joint_names": [str(i) for i in range(6)]}
        trace = state.StateConsistencyTrace(None, metadata)
        trace.append(2, 4/120, 2/120, 2/120, status="NOT_OBSERVED")
        self.assertFalse(trace.summary()["observed_comparison_complete"])
        trace.mark_failure("read", "diagnostic error", step=2, affects_comparison=True)
        self.assertFalse(trace.summary()["observed_comparison_complete"])
        trace.close()

    def test_cli_default_modes_and_source_helpers(self):
        parser = argparse.ArgumentParser()
        forces.add_external_forces_arguments(parser)
        self.assertEqual(parser.parse_args([]).external_forces_every_iteration, "inherit")
        self.assertEqual(forces.external_forces_source([]), "default_inherit")
        for mode in ("inherit", "on", "off"):
            for argv in (["--external-forces-every-iteration", mode], [f"--external-forces-every-iteration={mode}"]):
                self.assertEqual(parser.parse_args(argv).external_forces_every_iteration, mode)
                self.assertEqual(forces.external_forces_source(argv), "explicit_cli")
        with mock.patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["--external-forces-every-iteration", "unknown"])

    def test_real_drive_parser_keeps_pd_separate_from_explicit_scene_option(self):
        drive = load("_cr12_drive_external_checks", "scripts/environments/run_cr12_joint_drive.py")
        hold = load("_cr12_hold_diagnostics", "scripts/environments/_cr12_hold_diagnostics.py")
        class FakeLauncher:
            @staticmethod
            def add_app_launcher_args(parser):
                parser.add_argument("--device", default="cuda:0")
                parser.add_argument("--headless", action="store_true")
                parser.add_argument("--enable_cameras", action="store_true")
                parser.add_argument("--livestream", type=int, default=-1)
                parser.add_argument("--xr", action="store_true")
        with tempfile.TemporaryDirectory(prefix="cr12_external_cli_") as temp:
            usd = Path(temp) / "parser_fixture.usd"
            usd.write_text("CPU parser only", encoding="utf-8")
            argv = ["run_cr12_joint_drive.py", "--usd-path", str(usd), "--output-dir", temp,
                    "--record-joint-trace", "--diagnose-state-consistency", "--pd-profile", "baseline"]
            modules = {"_cr12_external_forces": forces, "_cr12_hold_diagnostics": hold}
            with mock.patch.dict(sys.modules, modules), mock.patch.dict(os.environ, {}, clear=True):
                for mode in (None, "inherit", "on", "off"):
                    actual_argv = argv if mode is None else argv + ["--external-forces-every-iteration", mode]
                    with mock.patch.object(sys, "argv", actual_argv):
                        args = drive._parse_args(FakeLauncher)
                    self.assertEqual(args.pd_profile, "baseline")
                    self.assertEqual(args.external_forces_every_iteration, "inherit" if mode is None else mode)
                    self.assertEqual(args.external_forces_source, "default_inherit" if mode is None else "explicit_cli")


if __name__ == "__main__":
    unittest.main(verbosity=2)
