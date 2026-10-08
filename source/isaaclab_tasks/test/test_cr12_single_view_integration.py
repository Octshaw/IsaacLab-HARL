"""CPU entry/FSM wiring with fake clock, scene and camera; never sensor evidence."""
import copy
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/environments"))
import run_cr12_single_view_capture as entry
import run_cr12_pose_target as pose_entry
import _cr12_camera_capture as backend
import _cr12_camera_mount as mount
import _cr12_external_forces as forces


class FakeRecorder(entry.Recorder):
    def __init__(self):
        super().__init__()
        self.events, self.saved, self.save_count = [], None, 0

    def emit(self, event, **facts):
        self.events.append((event, copy.deepcopy(facts)))

    def save(self):
        self.save_count += 1
        self.saved = copy.deepcopy(self.result)

    def secondary(self, exc, phase):
        self.result["secondary_failures"].append({"phase": phase, "message": str(exc)})


class FakeCamera:
    """Only the already-unit-tested backend contract is simulated here."""
    product_path = "/Render/HydraTextures/OnlyThisCamera"

    def __init__(self, harness):
        self.h = harness
        self.camera = object()
        self.enabled, self.started, self.off_requested = False, False, False
        self.ids, self.frame, self.events, self.boundary = None, None, 0, None
        self.opportunities, self.release_count = 0, 0

    def read_updates_enabled(self):
        return self.enabled

    def assert_off(self, phase):
        if self.enabled:
            raise backend.CameraCaptureError("camera_render_switch", "Fake expected OFF")
        return {"updates_enabled": False, "render_product_path": self.product_path}

    def begin_capture(self, ids, boundary):
        self.ids, self.started = dict(ids), True
        self.boundary = copy.deepcopy(boundary)
        self.h.order.append(("camera_on_attempt", self.h.step))
        if self.h.mode == "on_failure":
            raise backend.CameraCaptureError("camera_render_switch", "Synthetic ON readback failure")
        self.enabled = True
        return {"actual": True, "updates_enabled": True, "render_product_path": self.product_path}

    def on_render(self, context):
        if not self.enabled:
            return
        if self.h.mode in ("no_data", "wall_timeout", "callback_failure"):
            return
        self.events += 1
        if self.frame is None:
            self.frame = {"rgba": np.zeros((3, 4, 4), dtype=np.uint8),
                "metadata": {**self.ids, "fresh": True, "render_product_path": self.product_path,
                    "camera_prim_path": "/Robot/TestCamera", "rendering_frame": 1000+self.h.step,
                    "source_time": self.h.sim.current_time, "received_wall_time": 10000+self.h.now,
                    "received_context": copy.deepcopy(context)}}

    def poll_snapshot(self):
        if self.h.mode == "callback_failure":
            raise backend.CameraCaptureError("camera_frame_mismatch", "Synthetic event/buffer mismatch")
        return self.frame

    def request_off(self, boundary=None):
        if not self.off_requested:
            self.h.order.append(("camera_off", self.h.step))
        self.off_requested, self.enabled = True, False
        return {"updates_enabled": False}

    def observe_close(self, render_opportunity=True):
        if not self.off_requested:
            raise AssertionError("Close observation must follow actual OFF request")
        if render_opportunity:
            self.opportunities += 1
        confirmed = self.opportunities >= 30 and self.h.mode != "close_timeout"
        return {"confirmed": confirmed, "updates_enabled": False,
            "opportunity_count": self.opportunities, "quiet_opportunities": self.opportunities,
            "product_event_count": self.events, "independent_observer_active": True}

    def summary(self):
        return {"product_event_count": self.events, "acquired": self.frame is not None,
                "updates_enabled": self.enabled, "release_count": self.release_count,
                "request": None if self.ids is None else {**self.ids, "boundary": copy.deepcopy(self.boundary),
                    "product_event_baseline": 0, "source_frame_baseline": 0,
                    "on_source_time_numerator": 602, "on_source_time_denominator": 120}}

    def release(self):
        self.release_count += 1
        self.h.order.append(("release", self.h.step))
        return {"complete": True}


class Harness:
    def __init__(self, mode, output):
        self.mode, self.step, self.now = mode, 0, 100.0
        self.sim = SimpleNamespace(current_time_step_index=2, current_time=2/120)
        self.robot, self.order = object(), []
        self.capture = FakeCamera(self)
        self.recorder, self.resources = FakeRecorder(), {}
        self.args = SimpleNamespace(output_dir=output)
        self.config = SimpleNamespace(record=lambda: {"name": "CPU_FAKE_NOT_SENSOR_EVIDENCE"})
        self.native_calls = 0
        self.generator_closed = False

    def prepare(self, args, app, recorder, resources, expected, config, receive_context):
        self.receive_context = receive_context
        self.scene = {"sim": self.sim, "robot": self.robot, "configuration": object(),
                      "selected_pd": {}, "stage": object(), "setup": {},
                      "physx_schema": object(), "usd_physics": object(), "default_time": object()}
        self.initial = {"poses": {"link_6": np.eye(4)}, "baseline": (2, 2/120)}
        resources.update(capture=self.capture, sim=self.sim,
                         visual_override=SimpleNamespace(verify_stable=lambda phase: {"pass": True, "phase": phase}))
        recorder.result.update(physx_readback={"accepted_parameter": 17},
            camera_mount={"camera_prim": "/Robot/TestCamera"},
            visual_preinit={"apply_count": 1, "stage_checks": []},
            pose_summary={"guard_pass_counts": {name: 0 for name in ("clock", "state", "contact", "geometry", "frame", "command")}})
        return self.scene, self.initial

    def pose_ticks(self, args, app, recorder, resources, expected, *, scene, initial,
                   continue_after_arrival, before_render):
        if not continue_after_arrival:
            raise AssertionError("Capture must keep the same controller after arrival")
        try:
            for step in range(1, 1801):
                if self.mode == "physical_failure" and step == 610:
                    raise entry.DriveCheckError("geometry_guard", "Synthetic physical guard failure")
                self.step = step
                self.now += .001
                if self.mode == "wall_timeout" and step == 610:
                    self.now += 61
                self.sim.current_time_step_index, self.sim.current_time = step+2, (step+2)/120
                poststep_failure = {"poststep_pose_failure": 590, "poststep_capture_failure": 601,
                                    "poststep_close_failure": 610}.get(self.mode)
                if step == poststep_failure:
                    # A real step was already accounted for, then a guard
                    # rejected it before the iterator/FSM received the sample.
                    recorder.result["completed_physics_steps"] = step
                    raise entry.DriveCheckError("geometry_guard", "Synthetic post-step guard failure before yield")
                sample = {"step": step, "physics_time_s": self.sim.current_time, "controlled_time_s": step/120,
                    "phase": "HOLD" if step >= 600 else "MOVING", "target_position_error_m": .0001,
                    "target_orientation_error_rad": .0001, "stable_samples": max(0, min(121, step-479)),
                    "stable_span_s": max(0, min(1., (step-480)/120)), "status": "POSE_REACHED" if step == 600 else "RUNNING",
                    "dq": [0.]*6}
                tick = {"step": step, "physics_time_s": self.sim.current_time, "controlled_time_s": step/120,
                    "sample": sample, "dq": np.zeros(6), "scanner": np.eye(4),
                    "poses": {"link_6": np.eye(4)}, "rendered": step % 2 == 0, "pose_reached": step >= 600}
                if tick["rendered"]:
                    before_render(tick)
                    self.capture.on_render(self.receive_context)
                recorder.result["completed_physics_steps"] = step
                for key in recorder.result["pose_summary"]["guard_pass_counts"]:
                    recorder.result["pose_summary"]["guard_pass_counts"][key] = step
                resources["trace"].append(sample)
                yield tick
        finally:
            self.generator_closed = True

    def read_native(self, *args):
        self.native_calls += 1
        self.order.append(("native_final", self.step))
        return [], [], {"accepted_parameter": 17}

    def camera_pose(self, *args, clock, phase):
        return {"position_error_m": 0., "orientation_error_rad": 0.,
                "phase": phase, "physics_clock": list(clock), "pass": True}

    def refresh_camera(self, scene, initial, capture, config, recorder, resources):
        return self.camera_pose(clock=entry._clock(scene["sim"]), phase="initial_after_fabric_publication")

    def run(self):
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(entry, "prepare_scene", side_effect=self.prepare))
            patches.enter_context(mock.patch.object(entry, "refresh_initial_camera_publication", side_effect=self.refresh_camera))
            patches.enter_context(mock.patch.object(entry, "native_validity", return_value={"valid": True}))
            patches.enter_context(mock.patch.object(entry, "_read_physics", side_effect=self.read_native))
            patches.enter_context(mock.patch.object(entry.time, "monotonic", side_effect=lambda: self.now))
            patches.enter_context(mock.patch.object(pose_entry, "_pose_ticks", side_effect=self.pose_ticks))
            patches.enter_context(mock.patch.object(mount, "actual_camera_pose", side_effect=self.camera_pose))
            patches.enter_context(mock.patch.object(mount, "read_optics", return_value={"resolution": [4, 3]}))
            patches.enter_context(mock.patch.object(forces, "read_scene_external_forces", return_value={"resolved": True}))
            if self.mode == "save_failure":
                patches.enter_context(mock.patch.object(backend, "save_rgba_png", side_effect=OSError("Synthetic disk failure")))
            try:
                entry.run_capture(self.args, object(), self.recorder, self.resources, {"bodies": {}}, self.config)
            except BaseException as exc:
                return exc
        return None


class EntryIntegrationTests(unittest.TestCase):
    def execute(self, mode, assertions):
        with tempfile.TemporaryDirectory() as directory:
            harness = Harness(mode, Path(directory))
            error = harness.run()
            self.assertTrue(harness.generator_closed)
            assertions(harness, harness.recorder.result, error)

    def test_success_600_motion_two_capture_60_close_ticks_and_real_schema(self):
        def check(h, r, error):
            self.assertIsNone(error)
            self.assertEqual(r["stage_counts"], {"pose_steps": 600, "capture_steps": 2, "close_steps": 60,
                "total_controlled_steps": 662, "fsm_observed_steps": 662, "unaccepted_poststep_count": 0})
            self.assertEqual(r["capture_summary"]["state"], "SUCCEEDED_OFF")
            self.assertTrue(all(r["capture_summary"][key] for key in ("acquired", "saved", "confirmed_off", "fresh_frame_confirmed")))
            self.assertEqual(r["off_confirmation"]["render_opportunities"], 30)
            self.assertEqual(r["camera_artifact"]["channels"], 4)
            self.assertTrue(Path(r["capture_metadata_path"]).is_file())
            self.assertEqual(r["moving_camera_off"]["checked_poststep_samples"], 600)
            self.assertEqual(h.order, [("camera_on_attempt", 600), ("camera_off", 602), ("native_final", 662), ("release", 662)])
            self.assertEqual(h.native_calls, 1)
            self.assertTrue(r["native_parameters_unchanged"])
            self.assertEqual(h.capture.frame["metadata"]["received_context"]["controlled_step"], 602)
        self.execute("success", check)

    def test_data_timeout_still_closes_and_retains_no_data_failure(self):
        def check(h, r, error):
            self.assertIsNotNone(error)
            self.assertEqual(getattr(error, "category", None), "CAPTURE_TIMEOUT")
            self.assertEqual(r["stage_counts"]["capture_steps"], 600)
            self.assertEqual(r["stage_counts"]["close_steps"], 60)
            self.assertEqual(r["capture_summary"]["state"], "FAILED_OFF")
            self.assertFalse(r["capture_summary"]["acquired"])
            self.assertTrue(r["capture_summary"]["confirmed_off"])
            self.assertEqual(h.native_calls, 0)
        self.execute("no_data", check)

    def test_wall_capture_timeout_also_enters_bounded_close(self):
        def check(h, r, error):
            self.assertEqual(getattr(error, "category", None), "CAPTURE_TIMEOUT")
            self.assertEqual(r["capture_summary"]["state"], "FAILED_OFF")
            self.assertTrue(r["capture_summary"]["confirmed_off"])
            self.assertEqual(r["stage_counts"]["close_steps"], 60)
        self.execute("wall_timeout", check)

    def test_on_readback_failure_runs_close_without_extra_capture(self):
        def check(h, r, error):
            self.assertEqual(getattr(error, "category", None), "camera_render_switch")
            self.assertEqual(r["capture_summary"]["state"], "FAILED_OFF")
            self.assertFalse(r["capture_summary"]["acquired"])
            self.assertEqual(r["stage_counts"]["close_steps"], 60)
            self.assertEqual(h.order, [("camera_on_attempt", 600), ("camera_off", 600)])
        self.execute("on_failure", check)

    def test_callback_failure_is_distinct_from_off_confirmation(self):
        def check(h, r, error):
            self.assertEqual(getattr(error, "category", None), "camera_frame_mismatch")
            self.assertEqual(r["capture_summary"]["state"], "FAILED_OFF")
            self.assertTrue(r["capture_summary"]["confirmed_off"])
            self.assertFalse(r["capture_summary"]["acquired"])
            self.assertEqual(r["off_confirmation"]["render_opportunities"], 30)
        self.execute("callback_failure", check)

    def test_save_failure_keeps_acquired_and_confirmed_off(self):
        def check(h, r, error):
            self.assertIsNotNone(error)
            self.assertEqual(r["capture_summary"]["state"], "FAILED_OFF")
            self.assertTrue(r["capture_summary"]["acquired"])
            self.assertTrue(r["capture_summary"]["confirmed_off"])
            self.assertFalse(r["capture_summary"]["saved"])
            self.assertIn("Synthetic disk failure", r["artifact_error"])
            self.assertEqual(r["single_view_request"]["failure"]["category"], "ARTIFACT")
        self.execute("save_failure", check)

    def test_close_timeout_preserves_real_acquired_sample_and_saved_artifact(self):
        def check(h, r, error):
            self.assertEqual(getattr(error, "category", None), "CLOSE_TIMEOUT")
            self.assertEqual(r["capture_summary"]["state"], "STOP_UNCONFIRMED")
            self.assertTrue(r["capture_summary"]["acquired"])
            self.assertTrue(r["capture_summary"]["saved"])
            self.assertFalse(r["capture_summary"]["confirmed_off"])
            self.assertEqual(r["stage_counts"]["close_steps"], 240)
            self.assertEqual(h.native_calls, 0)
        self.execute("close_timeout", check)

    def test_physical_failure_never_advances_an_extra_tick_for_close(self):
        def check(h, r, error):
            self.assertEqual(getattr(error, "category", None), "geometry_guard")
            self.assertEqual(h.step, 609)
            self.assertEqual(r["capture_summary"]["state"], "STOP_UNCONFIRMED")
            self.assertTrue(r["capture_summary"]["acquired"])
            self.assertFalse(r["capture_summary"]["confirmed_off"])
            self.assertEqual(h.native_calls, 0)
        self.execute("physical_failure", check)

    def test_poststep_rejection_counts_actual_tick_in_its_real_phase(self):
        cases = (("poststep_pose_failure", 590, 590, 0, 0),
                 ("poststep_capture_failure", 601, 600, 1, 0),
                 ("poststep_close_failure", 610, 600, 2, 8))
        for mode, actual, pose_steps, capture_steps, close_steps in cases:
            def check(h, r, error):
                self.assertEqual(getattr(error, "category", None), "geometry_guard")
                self.assertEqual(h.step, actual)
                self.assertEqual(r["completed_physics_steps"], actual)
                self.assertEqual(r["stage_counts"], {"pose_steps": pose_steps, "capture_steps": capture_steps,
                    "close_steps": close_steps, "total_controlled_steps": actual,
                    "fsm_observed_steps": actual-1, "unaccepted_poststep_count": 1})
                self.assertEqual(sum(r["stage_counts"][k] for k in ("pose_steps", "capture_steps", "close_steps")), actual)
                self.assertEqual(r["capture_summary"]["state"], "STOP_UNCONFIRMED")
                self.assertFalse(r["capture_summary"]["confirmed_off"])
                self.assertEqual(h.native_calls, 0)
                if mode != "poststep_close_failure":
                    self.assertEqual(r["capture_off_request"]["native_physics_clock"][0], actual+2)
            with self.subTest(mode=mode):
                self.execute(mode, check)

    def test_import_did_not_load_runtime_or_gpu_packages(self):
        self.assertFalse(any(name == "torch" or name.startswith(("isaacsim", "omni", "pxr")) for name in sys.modules))


class InitialPublicationTests(unittest.TestCase):
    """Publication wiring only: fake Fabric/native state, never a Kit forward."""

    def exercise(self, mutation=None, *, publish=True, starts_on=False, local_error=False):
        arrays = [np.zeros((1, 6)), np.zeros((1, 6)), np.zeros((1, 7, 7))]
        clones, order = [0, 0, 0], []
        state = {"published": False, "enabled": starts_on, "forward_calls": 0}
        resources = {"app_update_counter": {"count": 5}}
        sim = SimpleNamespace(current_time_step_index=2, current_time=2/120)
        recorder = FakeRecorder()

        def getter(index):
            def clone():
                clones[index] += 1
                return arrays[index].copy()
            return SimpleNamespace(clone=clone)

        view = SimpleNamespace(get_dof_positions=lambda: getter(0),
            get_dof_velocities=lambda: getter(1), get_link_transforms=lambda: getter(2))
        scene = {"sim": sim, "robot": SimpleNamespace(root_physx_view=view)}

        def forward():
            state["forward_calls"] += 1
            order.append("forward")
            state["published"] = publish
            if mutation is not None:
                mutation(arrays, sim, resources, state)

        def assert_off(phase):
            order.append(phase)
            if state["enabled"]:
                raise backend.CameraCaptureError("camera_render_switch", "Synthetic RP unexpectedly ON")
            return {"updates_enabled": False}

        def camera_pose(camera, pose, config, *, clock, phase, require_match=True):
            order.append((phase, require_match))
            matched = state["published"]
            if require_match and not matched:
                raise ValueError("Camera actual mount mismatch: synthetic stale Fabric")
            return {"phase": phase, "physics_clock": list(clock), "pass": matched,
                "position_error_m": 0. if matched else .00012455800111410833,
                "orientation_error_rad": 0. if matched else .0005791877710578032}

        sim.forward = forward
        sim.step = mock.Mock(side_effect=AssertionError("Publication cannot step"))
        sim.render = mock.Mock(side_effect=AssertionError("Publication cannot render"))
        capture = SimpleNamespace(camera=object(), assert_off=assert_off)
        local = mock.Mock(return_value={"pass": True, "reset_xform_stack": False})
        if local_error:
            local.side_effect = ValueError("Camera authored local mounting differs")
        error, result = None, None
        with mock.patch.object(entry, "native_validity", return_value={"valid": True}), \
                mock.patch.object(mount, "actual_camera_pose", side_effect=camera_pose), \
                mock.patch.object(mount, "read_local_mount", local):
            try:
                result = entry.refresh_initial_camera_publication(scene, {"poses": {"link_6": np.eye(4)}},
                    capture, object(), recorder, resources)
            except Exception as exc:
                error = exc
        sim.step.assert_not_called()
        sim.render.assert_not_called()
        return SimpleNamespace(error=error, result=result, recorder=recorder, state=state,
            arrays=arrays, clones=clones, order=order, local=local)

    def test_stale_before_correct_after_one_forward_without_time_or_native_change(self):
        case = self.exercise()
        self.assertIsNone(case.error)
        record = case.recorder.result["initial_fabric_publication"]
        self.assertFalse(record["before_camera"]["pass"])
        self.assertGreater(record["before_camera"]["position_error_m"], 1e-4)
        self.assertGreater(record["before_camera"]["orientation_error_rad"], 1e-4)
        self.assertTrue(case.result["pass"])
        self.assertTrue(record["pass_"])
        self.assertEqual(record["native_arrays_equal"], [True, True, True])
        self.assertEqual(record["native_array_shapes"], [[1, 6], [1, 6], [1, 7, 7]])
        self.assertEqual(record["before_clock"], record["after_clock"])
        self.assertEqual(record["app_updates_before"], record["app_updates_after"])
        self.assertEqual((record["forward_calls"], record["extra_physics_steps"], record["extra_app_updates"]), (1, 0, 0))
        self.assertEqual(case.clones, [2, 2, 2])
        self.assertEqual(case.order, ["initial_fabric_publication", ("initial_before_fabric_publication", False),
            "forward", "after_initial_fabric_publication", ("initial_after_fabric_publication", True)])
        self.assertEqual(case.recorder.save_count, 2)

    def test_any_native_array_change_rejects_instead_of_accepting_published_pose(self):
        for index in range(3):
            with self.subTest(native_array=index):
                def change(arrays, sim, resources, state):
                    arrays[index].flat[0] = 1e-12
                case = self.exercise(change)
                self.assertEqual(getattr(case.error, "category", None), "physical_invariance")
                record = case.recorder.result["initial_fabric_publication"]
                self.assertFalse(record["native_arrays_equal"][index])
                self.assertNotIn("after_camera", record)
                self.assertNotIn("pass_", record)

    def test_physics_step_time_or_app_update_change_rejects(self):
        changes = {
            "physics_step": lambda a, s, r, t: setattr(s, "current_time_step_index", 3),
            "physics_time": lambda a, s, r, t: setattr(s, "current_time", 3/120),
            "app_update": lambda a, s, r, t: r["app_update_counter"].update(count=6),
        }
        for name, mutation in changes.items():
            with self.subTest(change=name):
                case = self.exercise(mutation)
                self.assertEqual(getattr(case.error, "category", None), "physical_invariance")
                self.assertNotIn("pass_", case.recorder.result["initial_fabric_publication"])

    def test_still_stale_after_publication_fails_original_mount_acceptance(self):
        case = self.exercise(publish=False)
        self.assertIsInstance(case.error, ValueError)
        self.assertIn("actual mount mismatch", str(case.error))
        self.assertEqual(case.state["forward_calls"], 1)
        self.assertEqual(case.order[-1], ("initial_after_fabric_publication", True))
        self.assertNotIn("pass_", case.recorder.result["initial_fabric_publication"])

    def test_product_must_remain_off_before_and_after_forward(self):
        case = self.exercise(starts_on=True)
        self.assertEqual(getattr(case.error, "category", None), "camera_render_switch")
        self.assertEqual(case.state["forward_calls"], 0)
        case = self.exercise(lambda a, s, r, t: t.update(enabled=True))
        self.assertEqual(getattr(case.error, "category", None), "camera_render_switch")
        self.assertEqual(case.state["forward_calls"], 1)
        self.assertNotIn("pass_", case.recorder.result["initial_fabric_publication"])

    def test_local_mount_error_prevents_forward_and_forward_error_is_preserved(self):
        case = self.exercise(local_error=True)
        self.assertIn("authored local mounting", str(case.error))
        self.assertEqual(case.state["forward_calls"], 0)
        original = RuntimeError("Synthetic forward failure")
        def fail_forward(*args):
            raise original
        case = self.exercise(fail_forward)
        self.assertIs(case.error, original)
        self.assertFalse(case.recorder.result["initial_fabric_publication"]["before_camera"]["pass"])
        self.assertNotIn("pass_", case.recorder.result["initial_fabric_publication"])

    def test_authored_local_mount_keeps_optical_rotation_and_no_reset_stack(self):
        config = SimpleNamespace(t_ec=np.eye(4))
        expected = mount.usd_camera_transform(config.t_ec)
        local = SimpleNamespace(GetLocalTransformation=lambda: expected.T.copy(), GetResetXformStack=lambda: False)
        pxr = SimpleNamespace(UsdGeom=SimpleNamespace(Xformable=lambda prim: local))
        with mock.patch.dict(sys.modules, {"pxr": pxr}):
            record = mount.read_local_mount(SimpleNamespace(prim=object()), config)
            self.assertTrue(record["pass"])
            np.testing.assert_array_equal(record["actual_local_usd_matrix"], expected)
            local.GetResetXformStack = lambda: True
            with self.assertRaisesRegex(ValueError, "authored local mounting"):
                mount.read_local_mount(SimpleNamespace(prim=object()), config)
            local.GetResetXformStack = lambda: False
            shifted = expected.copy(); shifted[0, 3] += 2e-6
            local.GetLocalTransformation = lambda: shifted.T
            with self.assertRaisesRegex(ValueError, "authored local mounting"):
                mount.read_local_mount(SimpleNamespace(prim=object()), config)


if __name__ == "__main__":
    unittest.main(verbosity=2)
