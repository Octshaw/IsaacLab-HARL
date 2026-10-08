"""Small fake-event CPU checks; no Isaac import, renderer or generated test image claim."""
import ast
import copy
from fractions import Fraction
import importlib.util
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
import weakref
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "scripts/environments/_cr12_camera_capture.py"
spec = importlib.util.spec_from_file_location("cr12_camera_cpu", MODULE)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class Subscription:
    def __init__(self, callback, name, order):
        self.callback, self.name, self.order = callback, name, order


class Stream:
    def __init__(self):
        self.subscriptions = []

    def create_subscription_to_pop_by_type(self, event_type, callback, name="", order=0):
        subscription = Subscription(callback, name, order)
        self.subscriptions.append(weakref.ref(subscription))
        return subscription

    def emit(self, event, reverse=False):
        live = [r() for r in self.subscriptions if r() is not None]
        for subscription in sorted(live, key=lambda s: s.order, reverse=reverse):
            subscription.callback(event)


def runtime_fixture():
    runtime = SimpleNamespace(log=[], source_now=Fraction(5), buffer_frame_override=None,
                              pixels=np.zeros((3, 4, 4), dtype=np.uint8), stream=Stream(), new_frame_type=1)
    runtime.context = SimpleNamespace(get_rendering_event_stream=lambda: runtime.stream, get_stage_id=lambda: 7)

    class Texture:
        def __init__(self):
            self.value, self.ignore_switch = True, False

        @property
        def updates_enabled(self):
            return self.value

        @updates_enabled.setter
        def updates_enabled(self, value):
            runtime.log.append(("updates", value))
            if not self.ignore_switch:
                self.value = value

    class Product:
        path = "/Render/HydraTextures/CR12Owned"
        def __init__(self):
            self.hydra_texture, self.destroy_count = Texture(), 0

        def destroy(self):
            runtime.log.append("destroy_owned")
            self.destroy_count += 1

    runtime.product = Product()
    def create_product(path, resolution, force_new, name):
        runtime.log.append(("create", path, resolution, force_new, name))
        return runtime.product
    runtime.create_product = create_product

    class Camera:
        def __init__(self, prim_path, name, frequency, resolution, render_product_path):
            runtime.log.append("camera_construct")
            self._render_product, self.path, self._frequency = None, render_product_path, frequency
            self._acquisition_callback = self._stage_open_callback = self._timer_reset_callback = None
            self._rgb_annotator = self._fabric_time_annotator = None
            self.resolution = resolution
            self._current_frame = {"rendering_frame": 0, "rendering_time": 0}
            self._sdg_interface = SimpleNamespace(
                parse_rendered_simulation_event=lambda handle, results: results,
                get_rational_time_of_simulation=lambda stage, offset: (runtime.source_now.numerator, runtime.source_now.denominator))

        def get_render_product_path(self):
            return self.path

        def get_frequency(self):
            return self._frequency

        def initialize(self, physics_sim_view=None):
            runtime.log.append("initialize")
            self._current_frame["rgba"] = np.zeros((*self.resolution, 4), dtype=np.int32)
            self._rgb_annotator = SimpleNamespace(detach=lambda paths: runtime.log.append(("detach_rgb", paths)))
            self._fabric_time_annotator = SimpleNamespace(detach=lambda paths: runtime.log.append(("detach_time", paths)))
            self.resume()

        def resume(self):
            runtime.log.append("resume")
            self._acquisition_callback = runtime.stream.create_subscription_to_pop_by_type(
                1, self._data_acquisition_callback, name="camera", order=0)

        def pause(self):
            runtime.log.append("pause")
            self._acquisition_callback = None

        def is_paused(self):
            return self._acquisition_callback is None

        def get_current_frame(self, clone=False):
            return copy.deepcopy(self._current_frame) if clone else self._current_frame

        def _data_acquisition_callback(self, event):
            runtime.log.append("camera_original_update")
            self._current_frame.update(rendering_frame=runtime.buffer_frame_override or event.payload["swh_frame_number"],
                rendering_time=event.payload["results"][1]/event.payload["results"][2], rgba=runtime.pixels)

    runtime.Camera = Camera
    return runtime


def event(product="/Render/HydraTextures/CR12Owned", frame=101, source_time=Fraction(51, 10)):
    return SimpleNamespace(payload={"product_path_handle": 11,
        "results": (product, source_time.numerator, source_time.denominator), "swh_frame_number": frame})


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.runtime = runtime_fixture()
        self.context = {"physics_step": 600, "simulation_time": 5.0, "actual_pose": [1, 2, 3]}
        self.owner = capture.OwnedCameraCapture.prepare("/World/CR12/link_6/tool/scanner/camera",
            (4, 3), lambda: self.context, runtime=self.runtime)
        self.ids = {"goal_id": "g1", "attempt_id": "a1", "capture_id": "c1"}

    def start(self):
        self.owner.initialize_off()
        self.owner.begin_capture(self.ids, self.context)

    def test_create_forces_new_and_switches_off_before_camera_constructor(self):
        log = self.runtime.log
        self.assertTrue(log[0][3])
        self.assertEqual(log[1], ("updates", False))
        self.assertEqual(log[2], "camera_construct")
        self.assertEqual(self.owner.camera.get_frequency(), -1)
        self.assertIsNone(self.owner.camera._render_product)

    def test_initialize_and_play_resume_cannot_enable_product(self):
        self.owner.initialize_off()
        self.owner.camera.resume()  # Real Camera PLAY callback resumes only reception.
        self.assertFalse(self.owner.assert_off("moving")["updates_enabled"])
        self.assertIsNone(self.owner.poll_snapshot())

    def test_only_one_active_request_and_all_ids_required(self):
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(self.ids, self.context)
        self.owner.initialize_off()
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture({"goal_id": "g1"}, self.context)
        self.owner.begin_capture(self.ids, self.context)
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(self.ids, self.context)

    def test_wrong_product_never_poisons_receiver_or_observer(self):
        self.start()
        wrong = SimpleNamespace(payload={"product_path_handle": 7, "results": ("/Viewport",)})
        self.runtime.stream.emit(wrong)
        self.assertIsNone(self.owner.poll_snapshot())
        self.assertEqual(self.owner.summary()["product_event_count"], 0)

    def test_stale_source_time_rejected_even_when_received_after_on(self):
        self.start()
        self.runtime.stream.emit(event(frame=102, source_time=Fraction(49, 10)))
        self.assertIsNone(self.owner.poll_snapshot())
        self.assertEqual(self.owner.summary()["frame_rejections"], {"source_time_before_on": 1})

    def test_original_callback_updates_first_independent_of_observer_order(self):
        self.start()
        self.runtime.stream.emit(event(), reverse=True)
        snapshot = self.owner.poll_snapshot()
        self.assertEqual(snapshot["metadata"]["rendering_frame"], 101)
        self.assertEqual(snapshot["metadata"]["source_time"], 5.1)
        self.assertEqual(snapshot["metadata"]["capture_id"], "c1")
        self.assertTrue(snapshot["metadata"]["fresh"])

    def test_matching_pixels_are_valid_and_snapshot_cannot_follow_buffer(self):
        self.start()
        self.runtime.stream.emit(event())
        first = self.owner.poll_snapshot()
        self.assertTrue(np.all(first["rgba"] == 0))  # No image-quality gate.
        self.runtime.pixels.fill(255)
        self.context["actual_pose"][0] = 999
        self.runtime.stream.emit(event(frame=102, source_time=Fraction(52, 10)))
        self.assertIs(self.owner.poll_snapshot(), first)
        self.assertEqual(first["metadata"]["received_context"]["actual_pose"], [1, 2, 3])
        self.assertTrue(np.all(first["rgba"] == 0))
        self.assertFalse(first["rgba"].flags.writeable)
        self.assertEqual(first["metadata"]["data_received_count"], 1)

    def test_mismatching_buffer_frame_is_sticky_failure(self):
        self.start()
        self.runtime.buffer_frame_override = 99
        self.runtime.stream.emit(event())
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.poll_snapshot()

    def test_acquisition_failure_can_close_with_failure_preserved(self):
        self.start()
        self.runtime.buffer_frame_override = 99
        self.runtime.stream.emit(event())
        self.assertTrue(self.owner.read_updates_enabled())
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off()
        for _ in range(30):
            result = self.owner.observe_close()
        self.assertTrue(result["confirmed"])
        self.assertFalse(self.owner.read_updates_enabled())
        self.assertFalse(self.owner.summary()["acquired"])
        self.assertTrue(self.owner.summary()["errors"])
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.poll_snapshot()
        self.runtime.buffer_frame_override = None
        self.runtime.stream.emit(event(frame=102))
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.poll_snapshot()

    def test_none_buffer_waits_with_reason_then_accepts_real_data(self):
        self.start()
        self.runtime.pixels = None
        self.runtime.stream.emit(event())
        self.assertIsNone(self.owner.poll_snapshot())
        self.assertEqual(self.owner.summary()["frame_rejections"], {"buffer_not_ready_or_initial_zero": 1})
        self.runtime.pixels = np.zeros((3, 4, 4), np.uint8)
        self.runtime.stream.emit(event(frame=102))
        self.assertTrue(self.owner.poll_snapshot()["metadata"]["fresh"])

    def test_initial_zero_buffer_and_wrong_dtype_are_not_fresh_data(self):
        frame = {"rendering_frame": 0, "rendering_time": 0, "rgba": np.zeros((4, 3, 4), np.int32)}
        evidence = capture.event_evidence(event(), lambda handle, results: results)
        self.assertIsNone(capture.validate_frame(frame, evidence, (4, 3), baseline_frame=0, on_source_time=Fraction(5)))
        frame.update(rendering_frame=101, rendering_time=5.1, rgba=np.zeros((3, 4, 4), np.float32))
        with self.assertRaises(capture.CameraCaptureError):
            capture.validate_frame(frame, evidence, (4, 3), baseline_frame=0, on_source_time=Fraction(5))

    def test_initial_cuda_buffer_not_converted_and_real_tensor_is_independently_copied(self):
        evidence = capture.event_evidence(event(), lambda handle, results: results)
        class Untouchable:
            def __array__(self, *args):
                raise AssertionError("Must reject initialization before touching CUDA zero buffer")
        self.assertIsNone(capture.validate_frame({"rendering_frame": 0, "rgba": Untouchable()},
            evidence, (4, 3), baseline_frame=0, on_source_time=Fraction(5)))
        calls = []
        class Tensor:
            def detach(self): calls.append("detach"); return self
            def clone(self): calls.append("clone"); return self
            def cpu(self): calls.append("cpu"); return self
            def numpy(self): calls.append("numpy"); return np.zeros((3, 4, 4), np.uint8)
        pixels = capture.validate_frame({"rendering_frame": 101, "rendering_time": 5.1, "rgba": Tensor()},
            evidence, (4, 3), baseline_frame=0, on_source_time=Fraction(5))
        self.assertEqual(calls, ["detach", "clone", "cpu", "numpy"])
        self.assertEqual(pixels.dtype, np.uint8)

    def test_close_keeps_independent_observer_and_requires_30_opportunities(self):
        self.start()
        self.runtime.stream.emit(event())
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off(self.context)
        self.assertTrue(self.owner.camera.is_paused())
        for _ in range(29):
            self.assertFalse(self.owner.observe_close()["confirmed"])
        self.assertTrue(self.owner.observe_close()["confirmed"])
        self.assertEqual(self.owner.summary()["off"]["quiet_opportunities"], 30)

    def test_inflight_completion_resets_quiet_but_gui_events_do_not(self):
        self.start()
        self.runtime.stream.emit(event())
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off()
        for _ in range(29):
            self.owner.observe_close()
        self.runtime.stream.emit(event(frame=102, source_time=Fraction(52, 10)))
        self.assertEqual(self.owner.observe_close()["quiet_opportunities"], 0)
        for index in range(6):
            self.runtime.stream.emit(event(product="/Viewport", frame=200+index))
            result = self.owner.observe_close()
        self.assertTrue(result["confirmed"])
        self.assertEqual(result["in_flight_event_count"], 1)
        self.assertEqual(self.owner.summary()["camera_update_count"], 1)

    def test_new_source_after_off_never_confirms(self):
        self.start()
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off()
        self.runtime.stream.emit(event(frame=103, source_time=Fraction(53, 10)))
        for _ in range(35):
            result = self.owner.observe_close()
        self.assertFalse(result["confirmed"])
        self.assertEqual(self.owner.summary()["errors"][0]["category"], "camera_output_after_off")

    def test_actual_hydra_readback_mismatch_fails(self):
        self.owner.initialize_off()
        self.runtime.product.hydra_texture.ignore_switch = True
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(self.ids, self.context)

    def test_off_and_release_idempotent_and_only_owned_resources(self):
        self.start()
        off = self.owner.request_off()
        self.assertEqual(self.owner.request_off(), off)
        self.assertTrue(self.owner.release()["complete"])
        self.assertTrue(self.owner.release()["complete"])
        self.assertEqual(self.runtime.product.destroy_count, 1)
        self.assertIn(("detach_rgb", [self.owner.product_path]), self.runtime.log)
        self.assertIn(("detach_time", [self.owner.product_path]), self.runtime.log)
        self.assertIsNone(self.owner._observer)
        self.assertFalse(self.owner.summary()["off"]["confirmed"])

    def test_save_raw_png_once_without_mutating_snapshot(self):
        pixels = np.arange(48, dtype=np.uint8).reshape(3, 4, 4)
        before = pixels.copy()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.png"
            metadata = capture.save_rgba_png(path, pixels)
            data = path.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual((metadata["width"], metadata["height"]), (4, 3))
            length = struct.unpack(">I", data[33:37])[0]
            self.assertEqual(zlib.decompress(data[41:41+length]), b"".join(b"\0"+row.tobytes() for row in pixels))
            with self.assertRaises(FileExistsError):
                capture.save_rgba_png(path, pixels)
        np.testing.assert_array_equal(pixels, before)

    def test_module_has_no_runtime_import_or_clock_advancement(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        forbidden = {"step", "step_async", "update", "next_update_async", "play", "stop", "reset", "commit"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                # dict.update is bookkeeping, never app/simulation.update.
                if node.func.attr == "update":
                    continue
                self.assertNotIn(node.func.attr, forbidden)
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                self.assertFalse(node.module.startswith(("omni", "isaacsim", "pxr", "torch")))


class SequentialCaptureTests(unittest.TestCase):
    def setUp(self):
        self.runtime = runtime_fixture()
        self.context = {"physics_step": 600, "simulation_time": 5.0}
        self.owner = capture.OwnedCameraCapture.prepare("/World/CR12/link_6/SingleViewCamera", (4, 3),
            lambda: self.context, runtime=self.runtime, max_requests=2)
        self.ids = {"goal_id": "g1", "attempt_id": "a1", "capture_id": "c1"}
        self.second_ids = {"goal_id": "g2", "attempt_id": "a1", "capture_id": "c2"}

    start = CaptureTests.start

    def first_confirmed(self):
        self.start()
        self.runtime.stream.emit(event())
        first = self.owner.poll_snapshot()
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off(self.context)
        for _ in range(30):
            closed = self.owner.observe_close()
        self.assertTrue(closed["confirmed"])
        return first

    def second_begin(self):
        self.runtime.source_now = Fraction(10)
        self.owner.begin_capture(self.second_ids, {"physics_step": 1200, "simulation_time": 10.0})

    def test_two_requests_reuse_device_freeze_first_and_release_only_finally(self):
        prepared_identity = self.owner.device_identity()
        first = self.first_confirmed()
        identity = self.owner.device_identity()
        for key in ("camera_id", "product_id", "hydra_texture_id", "observer_id"):
            self.assertEqual(identity[key], prepared_identity[key])
        self.assertIsNotNone(identity["rgb_annotator_id"])
        self.assertIsNotNone(identity["reference_time_annotator_id"])
        first_metadata = copy.deepcopy(first["metadata"])
        first_pixels = first["rgba"].copy()
        history = self.owner.summary()["request_history"]
        self.second_begin()
        self.assertIsNone(self.owner.poll_snapshot())  # Old Camera buffer still exists.
        self.assertEqual(self.owner.camera.get_current_frame()["rendering_frame"], 101)
        self.assertEqual(self.owner.summary()["request"]["source_frame_baseline"], 101)
        self.runtime.stream.emit(event(frame=900, source_time=Fraction(101, 10)))
        second = self.owner.poll_snapshot()
        self.assertEqual(second["metadata"]["capture_id"], "c2")
        self.assertEqual(second["metadata"]["rendering_frame"], 900)  # No +1 assumption.
        np.testing.assert_array_equal(first_pixels, second["rgba"])  # Identical pixels are valid.
        np.testing.assert_array_equal(first_pixels, first["rgba"])
        self.assertEqual(first["metadata"], first_metadata)
        self.runtime.source_now = Fraction(102, 10)
        self.owner.request_off()
        for _ in range(29):
            self.assertFalse(self.owner.observe_close()["confirmed"])
        self.assertTrue(self.owner.observe_close()["confirmed"])
        summary = self.owner.summary()
        self.assertEqual(summary["request_count"], 2)
        self.assertEqual(len(summary["request_history"]), 2)
        self.assertEqual(summary["request_history"][0], history[0])
        self.assertEqual(summary["unique_product_event_count"], 2)
        self.assertEqual(summary["device_identity"], identity)
        self.assertEqual(self.runtime.product.destroy_count, 0)
        for key in ("prepare_calls", "product_create_calls", "camera_create_calls", "observer_create_calls", "initialize_calls"):
            self.assertEqual(summary["lifecycle"][key], 1)
        for key in ("begin_calls", "off_requests", "request_resume_calls", "request_pause_calls"):
            self.assertEqual(summary["lifecycle"][key], 2)
        self.assertEqual(summary["lifecycle"]["off_confirmed_count"], 2)
        self.assertEqual(summary["lifecycle"]["release_effective_count"], 0)
        self.assertTrue(self.owner.release()["complete"])
        self.assertTrue(self.owner.release()["complete"])
        released = self.owner.summary()
        self.assertEqual(released["device_identity"], identity)
        self.assertEqual(released["lifecycle"]["release_calls"], 2)
        self.assertEqual(released["lifecycle"]["release_effective_count"], 1)
        self.assertEqual(self.runtime.product.destroy_count, 1)
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture({"goal_id": "g3", "attempt_id": "a1", "capture_id": "c3"}, {})

    def test_second_begin_requires_data_and_full_off_confirmation(self):
        self.start()
        self.runtime.stream.emit(event())
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off()
        for _ in range(29):
            self.owner.observe_close()
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        self.assertTrue(self.owner.observe_close()["confirmed"])
        self.second_begin()
        self.assertEqual(self.owner.summary()["lifecycle"]["begin_calls"], 2)

    def test_confirmed_off_without_data_is_not_successful_handoff(self):
        self.start()
        self.owner.request_off()
        for _ in range(30):
            self.owner.observe_close()
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        self.assertEqual(self.owner.summary()["request_count"], 1)

    def test_goal_capture_ids_must_change_but_attempt_id_must_not(self):
        self.first_confirmed()
        for fields in ({"goal_id": "g1"}, {"capture_id": "c1"}, {"attempt_id": "a2"}):
            with self.subTest(fields=fields), self.assertRaises(capture.CameraCaptureError):
                self.owner.begin_capture({**self.second_ids, **fields}, {})
        self.assertEqual(self.owner.summary()["request_count"], 1)
        self.second_begin()

    def test_old_duplicate_equal_boundary_and_late_first_frames_do_not_become_capture_two(self):
        first = self.first_confirmed()
        self.second_begin()
        self.runtime.stream.emit(event(), reverse=True)
        self.assertIsNone(self.owner.poll_snapshot())
        self.runtime.stream.emit(event(frame=99, source_time=Fraction(49, 10)))
        self.assertIsNone(self.owner.poll_snapshot())
        self.runtime.stream.emit(event(frame=500, source_time=Fraction(10)))
        self.assertIsNone(self.owner.poll_snapshot())
        self.runtime.stream.emit(event(frame=901, source_time=Fraction(101, 10)), reverse=True)
        self.assertEqual(self.owner.poll_snapshot()["metadata"]["capture_id"], "c2")
        self.assertEqual(first["metadata"]["capture_id"], "c1")
        summary = self.owner.summary()
        self.assertEqual(summary["product_event_count"], 5)
        self.assertEqual(summary["unique_product_event_count"], 4)
        self.assertEqual(summary["event_classification"]["duplicate_notifications"], 1)
        self.assertEqual(summary["event_classification"]["late_source_notifications"], 1)
        self.assertEqual(summary["frame_rejections"]["duplicate_receiver_notification"], 1)
        self.assertEqual(summary["frame_rejections"]["source_time_not_after_on"], 1)

    def test_duplicate_callback_cannot_relabel_previously_empty_buffer(self):
        self.start()
        self.runtime.pixels = None
        self.runtime.stream.emit(event())
        self.runtime.pixels = np.zeros((3, 4, 4), np.uint8)
        self.runtime.stream.emit(event())
        self.assertIsNone(self.owner.poll_snapshot())
        self.assertEqual(self.owner.summary()["camera_update_count"], 1)
        self.runtime.stream.emit(event(frame=102, source_time=Fraction(52, 10)))
        self.assertIsNotNone(self.owner.poll_snapshot())

    def test_duplicate_after_confirmed_off_is_recorded_without_new_completion(self):
        self.first_confirmed()
        self.runtime.stream.emit(event())
        summary = self.owner.summary()
        self.assertEqual(summary["product_event_count"], 2)
        self.assertEqual(summary["unique_product_event_count"], 1)
        self.assertEqual(summary["event_classification"]["duplicate_notifications"], 1)
        self.assertTrue(summary["off"]["confirmed"])
        self.assertFalse(summary["errors"])
        self.second_begin()

    def test_unseen_completion_after_confirmed_off_is_sticky_even_with_old_source_time(self):
        for source in (Fraction(51, 10), Fraction(53, 10)):
            with self.subTest(source=source):
                self.setUp()
                self.first_confirmed()
                self.runtime.stream.emit(event(frame=102, source_time=source))
                summary = self.owner.summary()
                self.assertEqual(summary["errors"][0]["category"], "camera_output_after_confirmed_off")
                self.assertEqual(summary["event_classification"]["new_completions_after_confirmed_off"], 1)
                self.assertFalse(summary["off"]["confirmed"])
                with self.assertRaises(capture.CameraCaptureError):
                    self.second_begin()
                self.assertEqual(summary["request_history"][0]["off"]["confirmed"], True)  # Historical observation retained.

    def test_source_frame_cannot_change_time_between_notifications(self):
        self.first_confirmed()
        self.runtime.stream.emit(event(frame=101, source_time=Fraction(52, 10)))
        self.assertEqual(self.owner.summary()["errors"][0]["category"], "camera_event_identity")
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()

    def test_each_on_has_one_receiver_and_same_independent_observer(self):
        observer = self.owner._observer
        self.first_confirmed()
        self.second_begin()
        live = [ref() for ref in self.runtime.stream.subscriptions if ref() is not None]
        self.assertEqual(sum(sub.name == "camera" for sub in live), 1)
        self.assertEqual(sum(sub.name == "cr12.camera.independent_completion" for sub in live), 1)
        self.assertIs(self.owner._observer, observer)
        self.assertEqual(self.runtime.log.count("initialize"), 1)
        self.assertFalse(any(isinstance(row, tuple) and row[0].startswith("detach") for row in self.runtime.log))

    def test_failure_is_not_cleared_by_closing_or_new_begin(self):
        self.start()
        self.runtime.buffer_frame_override = 99
        self.runtime.stream.emit(event())
        self.runtime.source_now = Fraction(52, 10)
        self.owner.request_off()
        for _ in range(30):
            self.owner.observe_close()
        self.assertTrue(self.owner.summary()["off"]["confirmed"])
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        self.assertEqual(self.owner.summary()["request_count"], 1)

    def test_identity_replacement_is_detected_and_diagnostic_summary_survives(self):
        self.first_confirmed()
        self.owner._observer = object()
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        summary = self.owner.summary()
        self.assertFalse(summary["device_identity_valid"])
        self.assertEqual(summary["errors"][0]["category"], "camera_device_identity")

    def test_default_request_limit_and_final_release_cannot_be_reopened(self):
        self.owner._max_requests = 1  # Same value as the unchanged prepare default.
        self.first_confirmed()
        with self.assertRaises(capture.CameraCaptureError):
            self.second_begin()
        self.owner.release()
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.initialize_off()
        for invalid in (0, 3, True, 1.0):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                capture.OwnedCameraCapture.prepare("/Camera", runtime=self.runtime, max_requests=invalid)


class IntegrationCaptureTests(unittest.TestCase):
    def setUp(self):
        self.runtime = runtime_fixture()
        self.owner = capture.OwnedCameraCapture.prepare('/Camera', (4, 3), runtime=self.runtime,
                                                       max_requests=3, integration_mode=True)
        self.owner.initialize_off()
        self.ids = dict(goal_id='g1', attempt_id='case', capture_id='c1')
        self.owner.begin_capture(self.ids, {'physics_step': 600})

    def close(self):
        self.runtime.source_now += 1
        self.owner.request_off()
        for _ in range(30):
            self.owner.observe_close()

    def retire(self, ids=None, receipt=None, validator=None):
        receipt = object() if receipt is None else receipt
        return self.owner.retire_request(ids or self.ids, authority_receipt=receipt,
            receipt_validator=validator or (lambda value, ids: value is receipt), hold_verified=True)

    def test_no_data_retirement_needs_receipt_and_then_three_requests_share_device(self):
        identity = self.owner.device_identity()
        self.close()
        before = self.owner.summary()
        self.assertTrue(self.owner.eligible_to_retire(self.ids, hold_verified=True)['eligible'])
        next_ids = dict(goal_id='g2', attempt_id='case', capture_id='c2')
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(next_ids, {})
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.retire_request(self.ids, authority_receipt=None,
                receipt_validator=lambda *_: True, hold_verified=True)
        self.assertEqual(self.owner.summary()['request'], before['request'])
        self.assertFalse(self.owner.summary()['request_retired'])
        self.retire()
        retained = []
        for number in (2, 3):
            ids = dict(goal_id=f'g{number}', attempt_id='case', capture_id=f'c{number}')
            self.owner.begin_capture(ids, {})
            self.runtime.stream.emit(event(frame=100+number, source_time=self.runtime.source_now+Fraction(1, 10)))
            retained.append(self.owner.poll_snapshot())
            self.owner.mark_snapshot_accepted(ids)
            self.close()
            self.retire(ids)
        summary = self.owner.summary()
        self.assertEqual(self.owner.device_identity(), identity)
        self.assertEqual(summary['request_count'], 3)
        self.assertEqual(summary['unique_product_event_count'], 2)
        self.assertEqual(summary['lifecycle']['retire_effective_count'], 3)
        self.assertEqual(summary['lifecycle']['off_confirmed_count'], 3)
        self.assertEqual([row['has_data'] for row in summary['retirements']], [False, True, True])
        self.assertEqual(retained[0]['metadata']['capture_id'], 'c2')
        self.assertFalse(retained[0]['rgba'].flags.writeable)
        self.assertEqual(self.runtime.log.count('initialize'), 1)
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(dict(goal_id='g4', attempt_id='case', capture_id='c4'), {})
        self.owner.release()
        self.owner.release()
        self.assertEqual(self.owner.summary()['lifecycle']['release_effective_count'], 1)

    def test_raw_peek_is_python_only_and_separates_fresh_and_fsm_acceptance(self):
        self.runtime.stream.emit(event())
        self.owner.camera.get_current_frame = lambda **_: self.fail('peek called Camera')
        self.owner._updates_enabled = lambda: self.fail('peek called Hydra')
        first = self.owner.peek_retained_snapshot()
        self.assertTrue(first['raw_copy_present'])
        self.assertTrue(first['fresh_identity_validated'])
        self.assertFalse(first['fsm_acquired_accepted'])
        self.owner.mark_snapshot_accepted(self.ids)
        first['snapshot']['metadata']['capture_id'] = 'changed-copy'
        self.assertTrue(self.owner.peek_retained_snapshot()['fsm_acquired_accepted'])
        self.assertEqual(self.owner.peek_retained_snapshot()['snapshot']['metadata']['capture_id'], 'c1')

    def test_invalid_identity_keeps_raw_copy_but_never_calls_it_valid_data(self):
        self.runtime.buffer_frame_override = 99
        self.runtime.stream.emit(event())
        retained = self.owner.peek_retained_snapshot()
        self.assertTrue(retained['raw_copy_present'])
        self.assertFalse(retained['fresh_identity_validated'])
        self.assertFalse(retained['fsm_acquired_accepted'])
        self.assertFalse(retained['snapshot']['metadata']['fresh'])
        self.close()
        errors = copy.deepcopy(self.owner.summary()['errors'])
        with self.assertRaises(capture.CameraCaptureError):
            self.retire()
        self.assertEqual(self.owner.summary()['errors'], errors)
        self.assertEqual(self.owner.summary()['request_count'], 1)

    def test_fresh_output_without_ready_buffer_is_not_no_data_retirable(self):
        self.runtime.pixels = None
        self.runtime.stream.emit(event())
        self.close()
        eligibility = self.owner.eligible_to_retire(self.ids, hold_verified=True)
        self.assertEqual(eligibility['fresh_product_event_count'], 1)
        self.assertFalse(eligibility['eligible'])
        self.assertIn('fresh_product_output_without_retained_data', eligibility['reasons'])
        with self.assertRaises(capture.CameraCaptureError):
            self.retire()

    def test_backend_fresh_but_not_fsm_accepted_cannot_retire(self):
        self.runtime.stream.emit(event())
        self.close()
        self.assertFalse(self.owner.eligible_to_retire(self.ids, hold_verified=True)['eligible'])
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.mark_snapshot_accepted({**self.ids, 'capture_id': 'other'})
        self.owner.mark_snapshot_accepted(self.ids)
        self.assertTrue(self.owner.eligible_to_retire(self.ids, hold_verified=True)['eligible'])

    def test_hold_and_live_switch_rechecked_after_off_confirmation(self):
        self.close()
        self.assertFalse(self.owner.eligible_to_retire(self.ids, hold_verified=False)['eligible'])
        self.runtime.product.hydra_texture.value = True
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.eligible_to_retire(self.ids, hold_verified=True)
        self.runtime.product.hydra_texture.value = False
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.eligible_to_retire(self.ids, hold_verified=True)
        self.assertTrue(self.owner.summary()['errors'])

    def test_receipt_rejection_and_exception_preserve_current_request(self):
        self.close()
        request = self.owner.summary()['request']
        with self.assertRaises(capture.CameraCaptureError):
            self.retire(validator=lambda *_: False)
        def broken(*_):
            raise RuntimeError('receipt association failed')
        with self.assertRaisesRegex(RuntimeError, 'receipt association'):
            self.retire(validator=broken)
        self.assertEqual(self.owner.summary()['request'], request)
        self.assertFalse(self.owner.summary()['request_retired'])
        receipt = object()
        first = self.retire(receipt=receipt)
        self.assertEqual(self.retire(receipt=receipt), first)
        with self.assertRaises(capture.CameraCaptureError):
            self.retire(receipt=object())
        self.assertEqual(self.owner.summary()['lifecycle']['retire_effective_count'], 1)

    def test_post_retirement_output_stays_sticky_and_cannot_reopen(self):
        self.close()
        self.retire()
        self.runtime.stream.emit(event())
        with self.assertRaises(capture.CameraCaptureError):
            self.owner.begin_capture(dict(goal_id='g2', attempt_id='case', capture_id='c2'), {})
        self.assertEqual(self.owner.summary()['errors'][0]['category'], 'camera_output_after_confirmed_off')

    def test_integration_source_boundary_strict_and_request_budget_explicit(self):
        self.runtime.stream.emit(event(source_time=Fraction(5)))
        self.assertIsNone(self.owner.poll_snapshot())
        self.assertEqual(self.owner.summary()['frame_rejections']['source_time_not_after_on'], 1)
        for budget in (0, 1, 4, True, 2.0):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                capture.OwnedCameraCapture.prepare('/Camera', runtime=self.runtime,
                    max_requests=budget, integration_mode=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
