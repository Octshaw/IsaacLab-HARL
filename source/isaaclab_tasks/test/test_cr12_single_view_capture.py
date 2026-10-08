"""CPU lifecycle and extraction checks; synthetic evidence is not camera runtime proof."""
import ast
import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / 'scripts/environments/_cr12_single_view_capture.py'
SPEC = importlib.util.spec_from_file_location('cr12_capture_cpu', PATH)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


def tick(step, reached=False, **sample):
    return {'step': step, 'physics_time_s': 2/120 + step/120,
            'controlled_time_s': step/120, 'dq': [0.] * 6, 'pose_reached': reached,
            'sample': {'stable_samples': 121, 'stable_span_s': 1.,
                       'target_position_error_m': .0004,
                       'target_orientation_error_rad': .0007, **sample}}


def frame(**changes):
    return {'goal_id': 'g', 'attempt_id': 'a', 'capture_id': 'c', 'render_product_path': '/product',
            'fresh': True, 'rendering_frame': 101, 'source_time': 5.2,
            'received_wall_time': 1000., 'received_context': {'physics_step': 601}, **changes}


def closed(**changes):
    return {'confirmed': True, 'updates_enabled': False, 'opportunity_count': 30,
            'quiet_opportunities': 6, 'product_event_count': 1, **changes}


class CaptureRequestTests(unittest.TestCase):
    def request(self):
        request = capture.SingleViewRequest('g', 'a', '/product', 'c')
        request.start_motion({'updates_enabled': False}, 0.)
        return request

    def arrived(self):
        request = self.request()
        for step in range(1, 601):
            request.observe_tick(tick(step, reached=step == 600), False, step/120)
        self.assertEqual(request.state, 'ARRIVED_HOLD_OFF')
        return request

    def waiting(self):
        request = self.arrived()
        begin = request.capture_starting(5.)
        self.assertEqual(begin['ids'], {'goal_id': 'g', 'attempt_id': 'a', 'capture_id': 'c'})
        self.assertEqual(begin['boundary']['physics_step'], 600)
        request.capture_started({'updates_enabled': True, 'render_product_path': '/product'})
        return request

    def acquired(self):
        request = self.waiting()
        request.accept_frame(frame(), now=5.1)
        request.record_artifact('frame.png')
        return request

    def assert_error(self, category, function, *args, **kwargs):
        with self.assertRaises(capture.CaptureRequestError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.category, category)

    def test_motion_requires_actual_off(self):
        request = capture.SingleViewRequest('g', 'a', '/product', 'c')
        self.assert_error('OFF_REQUIRED', request.start_motion, {'updates_enabled': 0}, 0.)
        self.assertFalse(request.acquired)

    def test_camera_cannot_start_before_arrival(self):
        request = self.request()
        self.assert_error('STATE', request.capture_starting, 0.)
        self.assertEqual(request.state, 'CLOSING_AFTER_FAILURE')

    def test_motion_detects_product_enabled(self):
        request = self.request()
        self.assert_error('OFF_REQUIRED', request.observe_tick, tick(1), True, .01)

    def test_real_tick_sequence_and_clock_required(self):
        for value in (tick(2), tick(1, controlled_time_s=0)):
            if value['step'] == 1:
                value['controlled_time_s'] = math.nan
            request = self.request()
            self.assert_error('CLOCK', request.observe_tick, value, False, .01)

    def test_arrival_requires_both_121_and_one_second(self):
        for changes in ({'stable_samples': 120}, {'stable_span_s': .999}):
            request = self.request()
            self.assert_error('ARRIVAL_EVIDENCE', request.observe_tick, tick(1, True, **changes), False, .01)

    def test_arrival_hold_failure_immediate_and_sticky(self):
        request = self.arrived()
        bad = tick(601, True, target_position_error_m=.002001)
        self.assert_error('CAPTURE_HOLD_LOST', request.observe_tick, bad, False, 5.1)
        request.fail('SECONDARY', 'later failure')
        self.assertEqual(request.failure['category'], 'CAPTURE_HOLD_LOST')
        self.assertEqual(request.state, 'CLOSING_AFTER_FAILURE')

    def test_hold_uses_native_speed_and_angle_and_finite(self):
        capture.check_arrived_hold(.002, math.radians(.25), [.01] * 6)
        for p, r, dq in ((.001, 0., [.0100001]*6), (.001, math.radians(.251), [0.]*6),
                         (.001, 0., [math.nan]*6), (.001, 0., [0.]*5)):
            self.assert_error('CAPTURE_HOLD_LOST', capture.check_arrived_hold, p, r, dq)

    def test_hold_continues_past_old_pose_timeout(self):
        request = self.waiting()
        for step in range(601, 1101):
            request.check_before_tick(step/120)
            request.observe_tick(tick(step, True), True, step/120)
        self.assertEqual(request.state, 'WAITING_DATA')
        self.assertEqual(request.step, 1100)

    def test_wrong_product_old_capture_and_missing_fresh_rejected(self):
        for changes in ({'render_product_path': '/viewport'}, {'capture_id': 'old'}, {'fresh': False},
                        {'goal_id': 'other'}, {'rendering_frame': None}, {'source_time': None}):
            request = self.waiting()
            self.assert_error('FRAME_IDENTITY', request.accept_frame, frame(**changes))
            self.assertFalse(request.acquired)

    def test_metadata_copy_and_source_receive_times_separate(self):
        request = self.waiting()
        metadata = frame()
        request.accept_frame(metadata)
        metadata['received_context']['physics_step'] = 999
        self.assertEqual(request.frame['received_context']['physics_step'], 601)
        self.assertEqual(request.frame['source_time'], 5.2)
        self.assertEqual(request.frame['received_wall_time'], 1000.)

    def test_data_received_once(self):
        request = self.waiting()
        request.accept_frame(frame())
        self.assert_error('STATE', request.accept_frame, frame(rendering_frame=102))
        self.assertEqual(request.frame['rendering_frame'], 101)
        self.assertEqual(sum(row['state'] == 'DATA_RECEIVED' for row in request.transitions), 1)

    def test_success_requires_data_save_and_real_off(self):
        request = self.acquired()
        request.request_close(5.1)
        self.assertEqual(request.observe_close(closed(confirmed=False), 5.2), 'CAPTURE_CLOSING')
        self.assertEqual(request.observe_close(closed(), 5.3), 'SUCCEEDED_OFF')
        self.assertTrue(all(request.summary()[k] for k in ('acquired', 'artifact_saved', 'off_confirmed')))

    def test_off_minimum_and_inflight_quiet_evidence(self):
        for evidence in (closed(opportunity_count=29), closed(quiet_opportunities=5)):
            request = self.acquired()
            request.request_close(5.1)
            self.assert_error('OFF_EVIDENCE', request.observe_close, evidence, 5.2)
        request = self.acquired()
        request.request_close(5.1)
        request.observe_close(closed(confirmed=False, quiet_opportunities=0, product_event_count=2), 5.2)
        request.observe_close(closed(opportunity_count=36, quiet_opportunities=6, product_event_count=2), 5.3)
        self.assertEqual(request.state, 'SUCCEEDED_OFF')

    def test_enabled_product_cannot_confirm_off(self):
        request = self.acquired()
        request.request_close(5.1)
        self.assert_error('OFF_REQUIRED', request.observe_close, closed(updates_enabled=True), 5.2)
        self.assertFalse(request.off_confirmed)

    def test_save_failure_preserves_acquisition(self):
        request = self.waiting()
        request.accept_frame(frame())
        request.record_artifact(error=OSError('disk full'))
        request.request_close(5.1)
        request.observe_close(closed(), 5.2)
        self.assertTrue(request.acquired)
        self.assertFalse(request.artifact_saved)
        self.assertEqual(request.state, 'FAILED_OFF')
        self.assertEqual(request.failure['category'], 'ARTIFACT')

    def test_close_failure_preserves_acquisition(self):
        request = self.acquired()
        request.request_close(5.1)
        self.assert_error('CLOSE_TIMEOUT', request.check_before_tick, 35.1)
        self.assertTrue(request.acquired)
        self.assertEqual(request.state, 'STOP_UNCONFIRMED')

    def test_close_idempotent_does_not_restart_budget(self):
        request = self.acquired()
        first = request.request_close(5.1)
        self.assertEqual(first, request.request_close(20.))
        self.assert_error('CLOSE_TIMEOUT', request.observe_close, closed(), 35.1)

    def test_cancel_off_preserves_failure_despite_exit_zero(self):
        request = self.waiting()
        request.cancel(5.1)
        request.request_close(5.1)
        request.observe_close(closed(), 5.2)
        self.assertEqual(request.state, 'FAILED_OFF')
        self.assertEqual(request.failure['category'], 'CANCELLED')
        self.assertFalse(request.acquired)

    def test_capture_simulation_endpoint_allowed_next_tick_forbidden(self):
        request = self.waiting()
        for step in range(601, 1201):
            request.observe_tick(tick(step, True), True, step/120)
        request.accept_frame(frame(), now=10.)
        request.record_artifact('frame.png')
        request.request_close(10.)
        self.assertEqual(request.summary()['capture_steps'], 600)
        waiting = self.waiting()
        for step in range(601, 1201):
            waiting.observe_tick(tick(step, True), True, step/120)
        self.assert_error('CAPTURE_TIMEOUT', waiting.check_before_tick, 10.1)

    def test_capture_wall_budget_includes_render_delay(self):
        request = self.waiting()
        self.assert_error('CAPTURE_TIMEOUT', request.accept_frame, frame(), now=65.)
        self.assertFalse(request.acquired)

    def test_close_endpoint_and_total_cannot_borrow_budget(self):
        request = self.acquired()
        request.request_close(5.1)
        for step in range(601, 841):
            request.observe_tick(tick(step, True), False, 5.1+(step-600)/120)
        request.observe_close(closed(), 7.1)
        self.assertEqual(request.summary()['close_steps'], 240)
        request = self.acquired()
        request.request_close(5.1)
        request.step = 1800  # Isolate the independent hard total gate.
        self.assert_error('TOTAL_BUDGET', request.check_before_tick, 5.2)
        self.assertEqual(request.state, 'STOP_UNCONFIRMED')

    def test_pose_timeout_is_separate_from_capture_timeout(self):
        request = self.request()
        for step in range(1, 961):
            request.observe_tick(tick(step), False, step/120)
        self.assert_error('POSE_TIMEOUT', request.check_before_tick, 8.)

    def test_bad_wall_clock_and_second_request_forbidden(self):
        request = self.request()
        self.assert_error('CLOCK', request.check_before_tick, math.nan)
        request = self.acquired()
        request.request_close(5.1)
        request.observe_close(closed(), 5.2)
        self.assert_error('STATE', request.start_motion, {'updates_enabled': False}, 5.3)
        self.assertEqual(request.state, 'FAILED_OFF')


class RawCustodyTests(unittest.TestCase):
    arrived = CaptureRequestTests.arrived
    waiting = CaptureRequestTests.waiting

    def request(self):
        request = capture.SingleViewRequest('g', 'a', '/product', 'c', delivery_policy='raw-held-with-custody')
        request.start_motion({'updates_enabled': False}, 0.)
        return request

    @staticmethod
    def raw(**changes):
        import numpy as np
        rgba = np.arange(48, dtype=np.uint8).reshape(3, 4, 4)
        rgba.setflags(write=False)
        return {'rgba': rgba, 'metadata': frame(**changes)}

    def acquire_raw(self):
        request = self.waiting()
        snapshot = self.raw()
        request.retain_custody(snapshot)
        self.assertFalse(request.acquired)
        request.accept_frame(snapshot['metadata'], 5.1)
        return request

    def test_raw_custody_succeeds_without_artifact_and_is_actually_immutable(self):
        request = self.acquire_raw()
        held = request.peek_custody()
        with self.assertRaises(ValueError):
            held['rgba'].setflags(write=True)
        held['metadata']['capture_id'] = 'changed-copy'
        request.request_close(5.1)
        self.assertEqual(request.observe_close(closed(), 5.2), 'SUCCEEDED_OFF')
        self.assertTrue(request.summary()['custody_held'])
        self.assertFalse(request.artifact_saved)
        self.assertEqual(request.peek_custody()['metadata']['capture_id'], 'c')

    def test_png_failure_is_separate_from_held_data_success(self):
        request = self.acquire_raw()
        request.record_artifact(error=OSError('disk full'))
        self.assertIsNone(request.failure)
        request.request_close(5.1)
        self.assertEqual(request.observe_close(closed(), 5.2), 'SUCCEEDED_OFF')
        self.assertIn('disk full', request.artifact_error)
        self.assertTrue(request.acquired)

    def test_metadata_alone_or_lost_custody_cannot_succeed(self):
        for lost in (False, True):
            with self.subTest(lost=lost):
                request = self.acquire_raw() if lost else self.waiting()
                if lost:
                    request._custody = None
                else:
                    request.accept_frame(frame(), 5.1)
                request.request_close(5.1)
                self.assertEqual(request.observe_close(closed(), 5.2), 'FAILED_OFF')
                self.assertEqual(request.failure['category'], 'CUSTODY')
                self.assertTrue(request.acquired)

    def test_wrong_or_mutable_raw_rejected_without_overwriting_custody(self):
        request = self.waiting()
        for snapshot in ({'metadata': frame()}, self.raw(capture_id='wrong')):
            with self.assertRaises(capture.CaptureRequestError):
                request.retain_custody(snapshot)
        mutable = self.raw()
        mutable['rgba'].setflags(write=True)
        with self.assertRaises(capture.CaptureRequestError):
            request.retain_custody(mutable)
        request.retain_custody(self.raw())
        with self.assertRaises(capture.CaptureRequestError):
            request.retain_custody(self.raw())
        self.assertTrue(request.summary()['custody_held'])

    def test_cancel_after_acquisition_preserves_normal_close(self):
        request = self.acquire_raw()
        request.request_close(5.1)
        request.cancel(5.15)
        self.assertIsNone(request.failure)
        self.assertEqual(request.observe_close(closed(), 5.2), 'SUCCEEDED_OFF')
        self.assertTrue(request.summary()['cancel_requested']['superseded_by_acquisition'])

    def test_cancel_then_valid_retained_frame_race_preserves_data_and_c_priority(self):
        request = self.waiting()
        request.cancel(5.05)
        request.request_close(5.05)
        snapshot = self.raw()
        request.retain_custody(snapshot)
        request.accept_frame(snapshot['metadata'], 5.1)
        self.assertTrue(request.acquired)
        self.assertIsNone(request.failure)
        self.assertEqual(request.observe_close(closed(), 5.2), 'SUCCEEDED_OFF')
        self.assertTrue(request.summary()['cancel_requested']['superseded_by_acquisition'])

    def test_resource_failure_is_not_cleared_by_frame_or_cancel(self):
        request = self.waiting()
        request.fail('CAMERA_RESOURCE', 'sticky source failure')
        request.cancel(5.05)
        with self.assertRaises(capture.CaptureRequestError):
            request.accept_frame(frame(), 5.1)
        self.assertEqual(request.failure['category'], 'CAMERA_RESOURCE')
        request.request_close(5.1)
        self.assertEqual(request.observe_close(closed(), 5.2), 'FAILED_OFF')

    def test_no_data_cancel_has_no_fabricated_snapshot(self):
        request = self.waiting()
        request.cancel(5.05)
        request.request_close(5.05)
        self.assertEqual(request.observe_close(closed(), 5.2), 'FAILED_OFF')
        self.assertEqual(request.failure['category'], 'CANCELLED')
        self.assertFalse(request.acquired)
        self.assertIsNone(request.peek_custody())


class PoseExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT/'scripts/environments/run_cr12_pose_target.py').read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)
        cls.function = next(node for node in cls.tree.body if isinstance(node, ast.FunctionDef) and node.name == '_pose_ticks')
        cls.session_source = (ROOT/'scripts/environments/_cr12_scan_executor.py').read_text(encoding='utf-8')
        cls.session = next(node for node in ast.parse(cls.session_source).body
                           if isinstance(node, ast.ClassDef) and node.name == 'Cr12PoseControlSession')
        cls.methods = {node.name: node for node in cls.session.body if isinstance(node, ast.FunctionDef)}

    def test_single_physics_step_site_and_no_capture_runtime_in_fsm(self):
        calls = [ast.unparse(n.func) for n in ast.walk(self.function) if isinstance(n, ast.Call)]
        self.assertEqual(calls.count('session.sim.step'), 1)
        submit_calls = [ast.unparse(n.func) for n in ast.walk(self.methods['submit_prepared']) if isinstance(n, ast.Call)]
        init_calls = [ast.unparse(n.func) for n in ast.walk(self.methods['__init__']) if isinstance(n, ast.Call)]
        self.assertEqual(submit_calls.count('self.controller_ref.commit'), 1)
        self.assertEqual(init_calls.count('pc.CommandIntegrator'), 1)
        self.assertFalse(any(n in calls for n in ('sim.reset', 'sim.pause', 'sim.stop', 'app.update')))
        session_calls = [ast.unparse(n.func) for n in ast.walk(self.session) if isinstance(n, ast.Call)]
        self.assertFalse(any(n.endswith(('.step', '.render', '.reset')) for n in session_calls))
        pure_calls = [ast.unparse(n.func) for n in ast.walk(ast.parse(PATH.read_text())) if isinstance(n, ast.Call)]
        self.assertFalse(any(n.endswith(('.step', '.render', '.update', '.sleep')) for n in pure_calls))

    def test_before_render_receives_poststep_native_pose(self):
        driver = ast.unparse(self.function)
        self.assertLess(driver.index('session.sim.step('), driver.index('session.observe_physics('))
        self.assertLess(driver.index('session.observe_physics('), driver.index('before_render('))
        self.assertLess(driver.index('before_render('), driver.index('session.sim.render('))
        observe = ast.unparse(self.methods['observe_physics'])
        self.assertIn('_native_state(', observe)
        self.assertIn('_body_poses(', observe)
        self.assertIn('check_arrived_hold(self.ep, self.er, self.dq)', observe)
        self.assertLess(driver.index('session.sim.render('), driver.index('session.finish_tick('))

    def test_default_continuation_off_and_old_wrapper_consumes(self):
        defaults = dict(zip((a.arg for a in self.function.args.kwonlyargs), self.function.args.kw_defaults))
        self.assertIs(ast.literal_eval(defaults['continue_after_arrival']), False)
        self.assertIsNone(ast.literal_eval(defaults['before_render']))
        wrapper = next(n for n in self.tree.body if isinstance(n, ast.FunctionDef) and n.name == '_run_pose')
        self.assertEqual(ast.unparse(wrapper.body[0].iter), '_pose_ticks(args, app, recorder, resources, expected)')
        self.assertEqual(ast.unparse(wrapper.body[0].body[0]), 'pass')

    def test_reached_holds_skip_only_old_monitor_timeout(self):
        candidates = [n for n in ast.walk(self.session) if isinstance(n, ast.If)
                      and ast.unparse(n.test) == 'self.continue_after_arrival and self.monitor.reached']
        self.assertEqual(len(candidates), 2)
        monitor_branch = next(n for n in candidates if n.orelse)
        self.assertIn('monitor.observe', ast.unparse(monitor_branch.orelse[0]))
        self.assertNotIn('CommandIntegrator', ast.unparse(monitor_branch))
        completion = next(n for n in ast.walk(self.session) if isinstance(n, ast.If)
                          and ast.unparse(n.test) == "self.observation['status'] == 'POSE_REACHED'")
        split = completion.body[-1]
        self.assertEqual(ast.unparse(split.test), 'self.continue_after_arrival')
        self.assertNotIn('work_completed', ast.unparse(split.body))
        self.assertIn('work_completed', ast.unparse(split.orelse))


if __name__ == '__main__':
    unittest.main(verbosity=2)
