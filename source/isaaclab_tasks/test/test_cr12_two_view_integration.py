"""CPU wiring: real sequence/FSM/capture logic with one fake physical iterator.

Reuse the single-view harness and Camera API fixture. Generated temporary PNGs
are synthetic test artifacts, not camera/runtime evidence.
"""
import copy
from contextlib import ExitStack
from fractions import Fraction
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

import test_cr12_single_view_integration as single
from test_cr12_camera_capture import runtime_fixture, event
import _cr12_camera_capture as backend
import _cr12_camera_mount as mount
import _cr12_external_forces as forces
import _cr12_pose_control as pc
import _cr12_two_view_capture as sequence
import run_cr12_pose_target as pose_entry
import run_cr12_single_view_capture as shared


class TwoHarness(single.Harness):
    def __init__(self, mode, output):
        super().__init__(mode, output)
        self.sim.physics_sim_view = object()
        self.robot = SimpleNamespace(root_physx_view=object())
        self.runtime = runtime_fixture()
        self.prepare_count = self.refresh_count = self.generator_count = 0
        self.handoff_reads = []
        self.latest = None
        self.render_steps = []
        self.goal_first_steps = {}
        self.snapshots = {}
        self.first_saved = None

    def prepare(self, *args, camera_request_limit=1):
        self.prepare_count += 1
        if camera_request_limit != 2:
            raise AssertionError("New sequence must opt into two requests")
        scene, initial = super().prepare(*args)
        self.capture = backend.OwnedCameraCapture.prepare("/World/CR12/link_6/SingleViewCamera", (4, 3),
            lambda: self.receive_context, runtime=self.runtime, max_requests=camera_request_limit)
        self.capture.initialize_off()
        self.resources["capture"] = self.capture
        self.recorder.result["pose_summary"].update(render_calls=0, submitted_target_checks=0, sanity_checks=0)
        self.recorder.result["initialization"] = {
            "reset_calls": 1, "joint_state_writes": 1, "root_state_writes": 0}
        return scene, initial

    def refresh_camera(self, *args):
        self.refresh_count += 1
        self.recorder.result["initial_fabric_publication"] = {"forward_calls": self.refresh_count}
        return super().refresh_camera(*args)

    def handoff_native(self, scene):
        self.handoff_reads.append(self.step)
        if self.first_saved is None:
            directory = self.args.output_dir / "view_01"
            self.first_saved = {name: (directory / name).read_bytes() for name in ("camera_rgba.png", "capture_metadata.json")}
        return {"native_clock": list(shared._clock(self.sim)),
            "q": self.latest["q"].tolist(), "dq": self.latest["dq"].tolist(),
            "scanner": self.latest["scanner"].tolist()}

    def pose_ticks(self, args, app, recorder, resources, expected, *, scene, initial,
                   continue_after_arrival, before_render, continuation):
        self.generator_count += 1
        if not continue_after_arrival:
            raise AssertionError("Same controller must hold during capture/close")
        controller, integrator = object(), pc.CommandIntegrator(np.zeros(6))
        self.integrator = integrator
        q, dq = np.zeros(6), np.zeros(6)
        scanner = pc.scanner_from_ee(initial["poses"]["link_6"])
        target = continuation.initial_target(scanner)
        continuation.bind_control(controller, integrator, self.sim.current_time)
        self.control_identity = (id(controller), id(integrator))
        try:
            for step in range(1, 3601):
                next_target = continuation.activate_pending(global_step=self.step, physics_time=self.sim.current_time,
                    actual_scanner=scanner, q=q, dq=dq, controller=controller, integrator=integrator)
                if next_target is not None:
                    target = next_target
                local = step-continuation.goal_start_step
                goal = continuation.goal_index
                self.goal_first_steps.setdefault(goal, (step, local))
                self.step, self.now = step, self.now+.001
                self.sim.current_time_step_index, self.sim.current_time = step+2, (step+2)/120
                proposal = integrator.propose(q, dq, np.full(6, .001))
                integrator.commit(proposal, proposal.q, proposal.dq)
                scanner = target.reference(local/120)
                # Simulate a small tracking offset so latest handoff actual is
                # neither ideal target nor the earlier arrival snapshot.
                scanner[2, 3] += 1e-5 + local*1e-9
                arrival_step = 600 if goal == 1 else 611
                reached = local >= arrival_step
                error = .003 if self.mode == "first_hold_failure" and goal == 1 and local == 601 else .0001
                sample = {"step": step, "physics_time_s": self.sim.current_time, "controlled_time_s": step/120,
                    "phase": "HOLD" if reached else "MOVING", "target_position_error_m": error,
                    "target_orientation_error_rad": .0001, "stable_samples": 121 if reached else 0,
                    "stable_span_s": 1. if reached else 0., "status": "POSE_REACHED" if local == arrival_step else "RUNNING",
                    "dq": dq.tolist(), "goal_id": continuation.goal_id, "local_step": local}
                tick = {"step": step, "physics_time_s": self.sim.current_time, "controlled_time_s": step/120,
                    "sample": sample, "q": q.copy(), "dq": dq.copy(), "scanner": scanner.copy(),
                    "poses": {"link_6": pc.ee_from_scanner(scanner)}, "rendered": step % 2 == 0,
                    "pose_reached": reached, "q_cmd": proposal.q.copy(), "dq_cmd": proposal.dq.copy(),
                    "local_step": local, "local_time_s": local/120, "render_count": step//2,
                    "goal_id": continuation.goal_id, "goal_index": goal}
                self.runtime.source_now = Fraction(step+1000, 30)  # Distinct from physical seconds.
                if tick["rendered"]:
                    self.render_steps.append(step)
                    before_render(tick)
                    if self.capture.read_updates_enabled():
                        if self.mode == "second_frame_failure" and goal == 2:
                            self.runtime.buffer_frame_override = 1
                        self.runtime.stream.emit(event(product=self.capture.product_path, frame=step+1000,
                            source_time=self.runtime.source_now), reverse=(goal == 2))
                        snapshot = self.capture._snapshot
                        if snapshot is not None:
                            self.snapshots.setdefault(goal, snapshot)
                if self.mode == "mutate_first_png" and goal == 2 and local == 10:
                    with (args.output_dir / "view_01/camera_rgba.png").open("ab") as stream:
                        stream.write(b"synthetic-corruption")
                if goal == 2 and local == 10:
                    if self.mode == "replace_simulation_view":
                        self.sim.physics_sim_view = object()
                    elif self.mode == "replace_articulation_view":
                        self.robot.root_physx_view = object()
                recorder.result["completed_physics_steps"] = step
                stats = recorder.result["pose_summary"]
                for key in stats["guard_pass_counts"]:
                    stats["guard_pass_counts"][key] = step
                stats.update(render_calls=step//2, submitted_target_checks=step, sanity_checks=2*step)
                resources["trace"].append(sample)
                continuation.observe_yield(tick)
                self.latest = tick
                yield tick
        finally:
            self.generator_closed = True

    def run(self):
        real_save, real_open = backend.save_rgba_png, Path.open
        def save(path, pixels):
            if self.mode == "first_png_failure" and Path(path).parent.name == "view_01":
                raise OSError("Synthetic first PNG failure")
            return real_save(path, pixels)
        def file_open(path, *args, **kwargs):
            if (self.mode == "first_metadata_failure" and path.name == "capture_metadata.json"
                    and path.parent.name == "view_01" and args and args[0] == "x"):
                raise OSError("Synthetic first metadata failure")
            return real_open(path, *args, **kwargs)
        with ExitStack() as patches:
            for module, name, side_effect in ((shared, "prepare_scene", self.prepare),
                    (shared, "refresh_initial_camera_publication", self.refresh_camera),
                    (shared, "_read_physics", self.read_native), (pose_entry, "_pose_ticks", self.pose_ticks),
                    (mount, "actual_camera_pose", self.camera_pose), (sequence, "read_handoff_native", self.handoff_native),
                    (backend, "save_rgba_png", save), (Path, "open", file_open)):
                patches.enter_context(mock.patch.object(module, name, side_effect=side_effect, autospec=(module is Path)))
            patches.enter_context(mock.patch.object(shared, "native_validity", return_value={"valid": True}))
            patches.enter_context(mock.patch.object(shared.time, "monotonic", side_effect=lambda: self.now))
            patches.enter_context(mock.patch.object(mount, "read_optics", return_value={"resolution": [4, 3]}))
            patches.enter_context(mock.patch.object(forces, "read_scene_external_forces", return_value={"resolved": True}))
            try:
                sequence.run_two_capture(self.args, object(), self.recorder, self.resources, {"bodies": {}}, self.config)
            except BaseException as exc:
                return exc
        return None


class TwoViewIntegrationTests(unittest.TestCase):
    def execute(self, mode, assertions):
        with tempfile.TemporaryDirectory() as directory:
            harness = TwoHarness(mode, Path(directory))
            error = harness.run()
            self.assertEqual((harness.prepare_count, harness.refresh_count, harness.generator_count), (1, 1, 1))
            self.assertTrue(harness.generator_closed)
            assertions(harness, harness.recorder.result, error)
            # Failure cleanup is a main() responsibility, not an invented tick.
            if not harness.capture.summary()["released"]:
                harness.capture.release()

    def test_success_same_device_two_independent_closes_and_continuous_context(self):
        def check(h, result, error):
            self.assertIsNone(error)
            first, second = result["views"]
            self.assertEqual([v["status"] for v in result["views"]], ["SUCCEEDED_OFF"]*2)
            self.assertEqual((first["global_end_step"], second["global_start_step"], second["global_end_step"]), (662, 662, 1334))
            self.assertEqual(first["stage_counts"]["total_controlled_steps"], 662)
            self.assertEqual(second["stage_counts"]["total_controlled_steps"], 672)
            self.assertEqual(second["stage_counts"]["pose_steps"], 611)
            self.assertEqual(second["stage_counts"]["capture_steps"], 1)
            for view in (first, second):
                self.assertEqual(view["off_confirmation"]["opportunity_count"], 30)
                self.assertEqual(view["off_confirmation"]["quiet_opportunities"], 30)
                self.assertEqual(view["stage_counts"]["close_steps"], 60)
                self.assertTrue(view["moving_camera_off"]["pass"])
            self.assertEqual(h.goal_first_steps, {1: (1, 1), 2: (663, 1)})
            self.assertEqual(h.render_steps, list(range(2, 1335, 2)))
            self.assertEqual(h.handoff_reads, [662, 662])
            self.assertTrue(result["handoff"]["pass"])
            self.assertTrue(result["first_view_immutability"]["pass"])
            self.assertTrue(result["resource_continuity"]["unchanged"])
            self.assertEqual(len(result["scene_identity_samples"]), 3)
            self.assertTrue(all(row == result["scene_identity_samples"][0] for row in result["scene_identity_samples"]))
            self.assertEqual(result["scene_lifecycle"], {"identity_unchanged": True, "scene_create_calls": 1,
                "reset_calls": 1, "joint_state_writes": 1, "root_state_writes": 0, "initial_publication_calls": 1})
            self.assertTrue(result["sequence_summary"]["complete"])
            self.assertEqual(result["sequence_summary"]["completed_views"], 2)
            self.assertEqual(result["resource_continuity"]["release_count"], 1)
            self.assertEqual(h.native_calls, 1)
            np.testing.assert_array_equal(h.integrator.initial_q, np.zeros(6))
            np.testing.assert_array_equal(result["two_view_profile"]["targets"][1]["matrix"], pc.scanner_from_ee(np.eye(4)))
            np.testing.assert_array_equal(result["handoff"]["trajectory_start"], second["trajectory_start"])
            self.assertNotEqual(result["handoff"]["q_cmd"], result["handoff"]["before"]["q"])
            for name, contents in h.first_saved.items():
                self.assertEqual((h.args.output_dir/"view_01"/name).read_bytes(), contents)
            np.testing.assert_array_equal(h.snapshots[1]["rgba"], h.snapshots[2]["rgba"])
            self.assertNotEqual(h.snapshots[1]["metadata"]["capture_id"], h.snapshots[2]["metadata"]["capture_id"])
            one = json.loads((h.args.output_dir/"view_01/capture_metadata.json").read_text())
            two = json.loads((h.args.output_dir/"view_02/capture_metadata.json").read_text())
            self.assertEqual((one["source_frame"], two["source_frame"]), (1602, 2274))
            self.assertGreater(two["source_time"], Fraction(two["source_on_baseline"]["on_source_time_numerator"],
                two["source_on_baseline"]["on_source_time_denominator"]))
        self.execute("success", check)

    def test_first_hold_failure_blocks_second_without_extra_physics_to_close(self):
        def check(h, result, error):
            self.assertIsNotNone(error)
            self.assertEqual(h.step, 601)
            self.assertFalse(result["sequence_summary"]["complete"])
            self.assertEqual(result["views"][1]["status"], "NOT_STARTED")
            self.assertTrue(result["views"][1]["blocked_by_previous_failure"])
            self.assertFalse((h.args.output_dir/"view_02").exists())
            self.assertFalse(h.handoff_reads)
            self.assertEqual(h.native_calls, 0)
        self.execute("first_hold_failure", check)

    def test_first_artifact_failures_keep_acquired_off_but_never_submit_second(self):
        for mode in ("first_png_failure", "first_metadata_failure"):
            def check(h, result, error):
                self.assertIsNotNone(error)
                first, second = result["views"]
                self.assertTrue(first["capture_summary"]["acquired"])
                self.assertTrue(first["capture_summary"]["confirmed_off"])
                self.assertEqual(first["status"], "FAILED_OFF")
                self.assertEqual(second["status"], "NOT_STARTED")
                self.assertFalse(h.handoff_reads)
                self.assertFalse((h.args.output_dir/"view_02").exists())
                self.assertEqual(h.capture.summary()["request_count"], 1)
                self.assertEqual(h.native_calls, 0)
            with self.subTest(mode=mode):
                self.execute(mode, check)

    def test_second_frame_failure_preserves_first_files_data_and_success(self):
        def check(h, result, error):
            self.assertIsNotNone(error)
            first, second = result["views"]
            self.assertEqual(first["status"], "SUCCEEDED_OFF")
            self.assertEqual(second["status"], "FAILED_OFF")
            self.assertFalse(second["capture_summary"]["acquired"])
            self.assertTrue(second["capture_summary"]["confirmed_off"])
            self.assertEqual(result["sequence_summary"]["completed_views"], 1)
            self.assertFalse(result["sequence_summary"]["complete"])
            for name, contents in h.first_saved.items():
                self.assertEqual((h.args.output_dir/"view_01"/name).read_bytes(), contents)
            self.assertEqual(h.snapshots[1]["metadata"]["capture_id"], "capture_1")
            self.assertEqual(h.capture.summary()["request_count"], 2)
            self.assertEqual(h.native_calls, 0)
        self.execute("second_frame_failure", check)

    def test_first_saved_file_mutation_cannot_pass_sequence(self):
        def check(h, result, error):
            self.assertEqual(getattr(error, "category", None), "sequence_immutable")
            self.assertFalse(result["sequence_summary"]["complete"])
            self.assertEqual([v["status"] for v in result["views"]], ["SUCCEEDED_OFF"]*2)
            self.assertEqual(h.native_calls, 0)
        self.execute("mutate_first_png", check)

    def test_replaced_native_view_identity_cannot_pass_final_lifecycle_check(self):
        for mode, field in (("replace_simulation_view", "simulation_view_id"),
                            ("replace_articulation_view", "articulation_view_id")):
            def check(h, result, error):
                self.assertEqual(getattr(error, "category", None), "NATIVE_VIEW_INVALID")
                self.assertFalse(result["sequence_summary"]["complete"])
                self.assertNotEqual(result["scene_identity_samples"][0][field], result["scene_identity_samples"][-1][field])
                self.assertEqual(h.native_calls, 0)
                self.assertEqual(h.capture.summary()["lifecycle"]["release_effective_count"], 0)
                self.assertEqual([view["status"] for view in result["views"]], ["SUCCEEDED_OFF"]*2)
            with self.subTest(mode=mode):
                self.execute(mode, check)

    def test_no_runtime_or_gpu_imports(self):
        self.assertFalse(any(name == "torch" or name.startswith(("isaacsim", "omni", "pxr")) for name in sys.modules))


if __name__ == "__main__":
    unittest.main(verbosity=2)
