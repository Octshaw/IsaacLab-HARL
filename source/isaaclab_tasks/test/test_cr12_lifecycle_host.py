"""CPU full-host wiring: real authority, real capture FSM/backend, fake physics/events.

No Isaac/CUDA runtime. Synthetic samples here are explicitly not robot evidence.
"""
from __future__ import annotations
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import test_cr12_lifecycle_execution_adapter as contracts
import test_cr12_camera_capture as events
import _cr12_camera_capture as camera
import _cr12_capture_runner as runner_module
import _cr12_lifecycle_host as host_module
import run_cr12_single_view_capture as shared
import run_cr12_lifecycle_integration as entry
from _cr12_runtime_support import Recorder


class QuietRecorder(Recorder):
    def emit(self, event, **facts): pass
    def save(self): pass


class FakeSim:
    def __init__(self, runtime):
        self.current_time_step_index, self.current_time = 2, 2/120
        self.runtime = runtime
        self.steps, self.renders = 0, 0
        self.capture = None
    def step(self, render=False):
        assert render is False
        self.steps += 1
        self.current_time_step_index += 1
        self.current_time = self.current_time_step_index/120
        self.runtime.source_now = Fraction(self.current_time_step_index, 120)
    def render(self):
        self.renders += 1
        if self.capture.read_updates_enabled():
            self.runtime.stream.emit(events.event(frame=self.current_time_step_index,
                                                  source_time=self.runtime.source_now))


class FakeSession:
    def __init__(self, args, app, recorder, resources, expected, *, scene, initial, integration):
        self.sim, self.recorder = scene['sim'], recorder
        self.model = SimpleNamespace(origins=[np.array([0., 0., 1.])])
        self.state = {'step': 0, 'physics_time_s': self.sim.current_time, 'controlled_time_s': 0.,
            'q': np.zeros(6), 'dq': np.zeros(6), 'q_cmd': [0.]*6, 'dq_cmd': [0.]*6,
            'poses': {'agv': np.eye(4), 'link_6': np.eye(4)}, 'scanner': np.eye(4),
            'target': np.eye(4), 'render_count': 0}
        self.submissions = 0
        self.goal_start = 0
        self.target = np.eye(4)
        self.aborted = False
        self.tail_bad_at = None
    def current_state(self):
        import copy
        return copy.deepcopy(self.state)
    def submit_goal(self, goal_id, target, latest_actual_boundary=None):
        self.goal_id, self.target = goal_id, target.copy()
        self.goal_start = self.state['step']
        self.submissions += 1
    def prepare_tick(self): return self.state['step']
    def submit_prepared(self, token): assert token == self.state['step']
    def observe_physics(self, before, after):
        assert after[0] == before[0]+1
        self.state.update(step=self.sim.steps, physics_time_s=self.sim.current_time,
            controlled_time_s=self.sim.steps/120, scanner=self.target.copy(), target=self.target.copy(),
            local_step=self.sim.steps-self.goal_start, local_time_s=(self.sim.steps-self.goal_start)/120,
            goal_id=self.goal_id)
        self.render_due = self.sim.steps % 2 == 0
        return self.current_state()
    def finish_tick(self, rendered):
        self.state['render_count'] += int(rendered)
        reached = self.sim.steps-self.goal_start >= 600
        err = .01 if self.tail_bad_at == self.sim.steps else 0.
        self.state.update(rendered=rendered, pose_reached=reached,
            sample={'target_position_error_m': err, 'target_orientation_error_rad': 0.,
                    'stable_samples': 121 if reached else 0, 'stable_span_s': 1. if reached else 0.})
        self.recorder.result['completed_physics_steps'] = self.sim.steps
        return self.current_state()
    def abort(self, exc): self.aborted = True


class HostFixture:
    def __init__(self, directory, case='normal'):
        self.resources, self.recorder = {}, QuietRecorder()
        self.args = SimpleNamespace(device='cpu', output_dir=Path(directory), integration_case=case)
        self.config = SimpleNamespace(near_m=.01, far_m=10., horizontal_fov_deg=60.)
        self.events = events.runtime_fixture()
        self.context = {}
        self.sim = FakeSim(self.events)
        self.scene = {'sim': self.sim, 'robot': object()}
        self.initial = {'baseline': (2, 2/120)}
        def setup():
            capture = camera.OwnedCameraCapture.prepare('/World/FakeCamera', (4, 3),
                context_provider=lambda: self.context, runtime=self.events,
                max_requests=2 if case == 'normal' else 3, integration_mode=True)
            capture.initialize_off()
            self.sim.capture = self.resources['capture'] = capture
            self.recorder.result['initialization'] = {'before_reset_clock': [0, 0.]}
            return {'scene': self.scene, 'initial': self.initial, 'receive_context': self.context,
                'mount_aggregate': {'count': 0, 'maximum_position_error_m': 0., 'maximum_orientation_error_rad': 0.},
                'initial_camera': {}, 'initial_parameters': {}}
        self.host = host_module.CR12IntegrationHost(self.args, None, self.recorder, self.resources, {}, self.config,
                                                   setup=setup, session_factory=FakeSession)
        d = self.host.domain
        runtime = contracts.S.EventProfileSynchronousRuntimeCoordinator(environment=self.host,
            current_read_port=d.current_read_port, production_claim_port=d.production_claim_port,
            physical_step_admission_port=d.physical_step_admission_port,
            standalone_reset_admission_port=d.standalone_reset_admission_port,
            terminal_consumer_port=d.terminal_consumer_port, fence_read_port=d.interstep_fence_read_port)
        self.facade = contracts.F._compose_event_assignment_runtime_facade(
            resolved_assignment_profile=self.host.profile, runtime_domain=d, synchronous_runtime=runtime)
        self.facade.reset()
    def step(self):
        h = self.host
        if h.runner is None:
            p = h.domain.current_read_port.read_current()
            task = next(i for i in (0, 1) if int(p.lifecycle_state.task_state[0, i]) == int(contracts.C.TaskLifecycleState.AVAILABLE))
            problem = h.assignment_problem()
            decision = self.facade.capture_proposal_decision(feasible_mask=problem['feasible_mask'], cost_matrix=problem['cost_matrix'])
            return self.facade.resolve_and_step_proposals(raw_action_ids=h.i([[task]]), decoded_proposal=h.i([[task]]),
                decision=decision, action_builder=h.bind_effective_assignment)
        return self.facade.step_without_new_claim(action_builder=h.bind_effective_assignment)


class FullHostTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(shared, 'native_validity', lambda *a: {'cpu_fixture': True}))
        self.stack.enter_context(patch.object(runner_module, 'actual_camera_pose',
            lambda *a, **k: {'position_error_m': 0., 'orientation_error_rad': 0.}))
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
    def tearDown(self): self.stack.close()
    def run_case(self, case):
        f = HostFixture(self.directory, case)
        receipt = None
        while not f.host.finished: receipt = f.step()
        h = f.host
        self.assertEqual(f.sim.steps, h.total_transitions*12)
        self.assertEqual(f.sim.renders, f.sim.steps//2)
        self.assertEqual(len(receipt.terminal_historical_payload), 1)
        history = entry.historical_summary(receipt.terminal_historical_payload[0])
        self.assertEqual(history['completion_count'], [2])
        self.assertEqual(history['coverage_after_transition'], [True, True])
        self.assertEqual(history['sidecar_critic_dimension'], 62)
        self.assertEqual(h.domain.terminal_consumer_port.capture_pending_terminal_artifacts(), ())
        self.assertFalse(h.domain.current_read_port.read_current().result)
        self.assertEqual(len(h.adapter.history), len(h.claims))
        self.assertTrue(all(r['retired_after_receipt'] for r in h.requests))
        self.assertTrue(all(not r.pending.custody.rgba.flags.writeable for r in h.adapter.history if r.pending.custody))
        self.assertEqual(h.session.submissions, len(h.claims))
        self.assertGreater(h.adapter.continuation_count, 20)
        self.assertEqual(h.capture.summary()['lifecycle']['initialize_calls'], 1)
        return f
    def test_normal_real_authority_and_terminal_transport(self):
        f = self.run_case('normal')
        self.assertEqual([x['outcome'] for x in f.host.deliveries], ['completed', 'completed'])
        self.assertEqual(len(list(Path(self.directory).glob('request_*/camera_rgba.png'))), 2)
    def test_cancel_reclaim_same_task_fresh_binding_and_data(self):
        f = self.run_case('cancel_then_reclaim')
        h = f.host
        self.assertEqual([x['outcome'] for x in h.deliveries], ['cancelled', 'completed', 'completed'])
        self.assertEqual([x['task_id'] for x in h.claims], [0, 0, 1])
        self.assertEqual(len({x['claim_token'] for x in h.claims}), 3)
        self.assertFalse(h.requests[0]['request']['acquired'])
        self.assertFalse((Path(self.directory)/'request_01/camera_rgba.png').exists())
        self.assertEqual(len(list(Path(self.directory).glob('request_*/camera_rgba.png'))), 2)
    def test_block_tail_guard_cannot_publish_cached_completion(self):
        f = HostFixture(self.directory)
        f.host.session.tail_bad_at = 665
        with self.assertRaises(Exception):
            for _ in range(56): f.step()
        self.assertTrue(f.host.session.aborted)
        self.assertEqual(len(f.host.deliveries), 0)
        self.assertIsNotNone(f.host.adapter.pending_result().custody)
        self.assertEqual(f.sim.steps, 665)
        with self.assertRaises(Exception): f.step()
        self.assertEqual(f.sim.steps, 665)
    def test_committed_receipt_survives_device_retirement_failure_and_poison(self):
        f = HostFixture(self.directory)
        with patch.object(f.host.capture, 'retire_request', side_effect=RuntimeError('local retire failure')):
            with self.assertRaisesRegex(RuntimeError, 'local retire failure'):
                for _ in range(56): f.step()
        h = f.host
        self.assertEqual(len(h.deliveries), 1)
        self.assertEqual(len(h.adapter.history), 1)
        self.assertEqual(h.deliveries[0]['outcome'], 'completed')
        self.assertIsNotNone(h.runner)
        self.assertIsNotNone(h.adapter.binding)
        self.assertIsNotNone(h.adapter.pending_result().custody)
        self.assertFalse(h.runner.retired)
        self.assertFalse(h.finished)
        self.assertEqual(int(h.adapter.history[0].result.updated_task_state[0, 0]),
                         int(contracts.C.TaskLifecycleState.COMPLETED))
        with self.assertRaises(Exception): h.domain.current_read_port.read_current()
        before = f.sim.steps
        with self.assertRaises(Exception): f.step()
        self.assertEqual(f.sim.steps, before)
    def test_cancel_requires_a_real_passed_normal_record_before_app(self):
        args = SimpleNamespace(manual_check=False, integration_case='cancel_then_reclaim',
                              normal_result=None, output_dir=Path(self.directory))
        with self.assertRaises(ValueError): entry.validate_case_prerequisite(args)


if __name__ == '__main__':
    unittest.main()

