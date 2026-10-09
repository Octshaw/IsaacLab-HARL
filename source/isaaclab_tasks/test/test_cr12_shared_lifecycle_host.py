"""Real shared Host/authority/capture plumbing with explicit fake physics/events.

Endpoint teleports below are CPU fixtures, never evidence of feasible motion,
settling, collision freedom, or physical capture. The nominal-motion audit is
separate. No Isaac application or GPU operation is used here.
"""
from __future__ import annotations

import copy
import json
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
from test_cr12_lifecycle_host import QuietRecorder
from test_cr12_dual_lifecycle_integration import SharedSim
import _cr12_camera_capture as camera
import _cr12_capture_runner as runners
import _cr12_lifecycle_host as hosts
import _cr12_pose_control as pc
import _cr12_shared_task_profile as profile
import run_cr12_single_view_capture as startup
import run_cr12_shared_task_handover as entry
from run_cr12_lifecycle_integration import historical_summary
from _cr12_runtime_support import Recorder

URDF = ROOT / ('source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/'
               'assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf')


class FakeSharedSession:
    """Synthetic endpoint states, real Host owns the only tick/render dispatch."""
    def __init__(self, args, app, recorder, resources, expected, *, scene, initial,
                 integration, allow_unbound_hold, set_view, shared_robot_id):
        self.robot_id, self.sim, self.recorder = shared_robot_id, scene['sim'], recorder
        self.model = pc.KinematicModel.from_derived_urdf(URDF)
        self.park_poses = self.model.forward(profile.initial_q(self.robot_id), profile.root_pose(self.robot_id))
        self.goal_poses = self.model.forward(profile.goal_q(self.robot_id), profile.root_pose(self.robot_id))
        # The test substitutes geometry only, not authority, runner or camera FSM.
        self.model.sanity_samples = lambda *a: [('midpoint', self.poses), ('endpoint', self.poses)]
        self.q = profile.initial_q(self.robot_id)
        self.poses = copy.deepcopy(self.park_poses)
        self.target = profile.park_pose(self.model, self.robot_id)
        self.goal_id = None
        self.goal_start = self.segment_start = 0
        self.segment_id, self.segment_kind = None, None
        self.setup, self.idle, self.aborted = False, True, False
        self.submissions = self.retreats = self.setup_completions = 0
        self.stats = {'render_calls': 0}
        self.state = dict(step=0, physics_time_s=self.sim.current_time, controlled_time_s=0.,
            q=self.q.copy(), dq=np.zeros(6), q_cmd=self.q.tolist(), dq_cmd=[0.]*6,
            poses=copy.deepcopy(self.poses), scanner=self.target.copy(), target=self.target.copy(),
            goal_id=None, local_step=0, local_time_s=0., render_count=0, pose_reached=False)

    def current_state(self): return copy.deepcopy(self.state)
    def begin_setup_hold(self): self.setup = True
    @property
    def setup_hold_ready(self): return self.setup and self.state['step'] >= 121
    def complete_setup_hold(self):
        assert self.setup_hold_ready
        self.setup, self.idle = False, True
        self.setup_completions += 1
        return {**self.current_state(),
                'setup_stable_samples': 121, 'setup_stable_span_s': 1.}
    def submit_goal(self, goal_id, target, *, latest_actual_boundary):
        assert latest_actual_boundary['step'] == self.state['step']
        self.goal_id, self.target = goal_id, target.copy()
        self.goal_start = self.segment_start = self.state['step']
        self.segment_kind, self.segment_id = 'approach', goal_id + ':approach'
        self.idle = False
        self.submissions += 1
    def submit_bound_segment(self, *, kind, latest_actual_boundary):
        assert kind == 'retreat' and self.robot_id == 0 and latest_actual_boundary['pose_reached']
        self.segment_start = self.state['step']
        self.segment_kind, self.segment_id = kind, self.goal_id + ':retreat'
        self.target = profile.park_pose(self.model, 0)
        self.retreats += 1
        return dict(control_segment_id=self.segment_id, global_step=self.state['step'],
                    physics_time_s=self.state['physics_time_s'], q_cmd=self.state['q_cmd'])
    def enter_idle_hold(self): self.idle = True
    def prepare_tick(self): return SimpleNamespace(q=self.q.copy(), generation=self.state['step'])
    def submit_prepared(self, token): assert token.generation == self.state['step']
    def observe_physics(self, before, after):
        assert after[0] == before[0] + 1
        if not self.setup and not self.idle:
            approach = self.segment_kind == 'approach'
            self.q = profile.goal_q(self.robot_id) if approach else profile.initial_q(self.robot_id)
            self.poses = copy.deepcopy(self.goal_poses if approach else self.park_poses)
        local_step, segment_step = self.sim.steps-self.goal_start, self.sim.steps-self.segment_start
        self.state.update(step=self.sim.steps, physics_time_s=self.sim.current_time,
            controlled_time_s=self.sim.steps/120, q=self.q.copy(), dq=np.zeros(6),
            q_cmd=self.q.tolist(), dq_cmd=[0.]*6, poses=copy.deepcopy(self.poses),
            scanner=self.target.copy(), target=self.target.copy(), goal_id=self.goal_id,
            local_step=local_step, local_time_s=local_step/120,
            segment_step=segment_step, segment_time_s=segment_step/120,
            scanner_task_target=profile.scanner_target(), control_segment_id=self.segment_id,
            control_segment_kind=self.segment_kind)
        self.render_due = self.sim.steps % 2 == 0
        return self.current_state()
    def finish_tick(self, rendered):
        self.state['render_count'] += int(rendered)
        self.stats['render_calls'] = self.state['render_count']
        reached = self.state['segment_step'] >= 121
        self.state.update(rendered=rendered, pose_reached=reached, setup_stable_now=True,
            sample=dict(target_position_error_m=0., target_orientation_error_rad=0.,
                stable_samples=121 if reached else 0, stable_span_s=1. if reached else 0.,
                **{'guard_'+k: 'PASS' for k in ('clock','joint','contact','geometry','frame','render_clock')}))
        return self.current_state()
    def abort(self, error): self.aborted = True


class SharedFixture:
    def __init__(self, directory):
        self.recorder, self.resources = QuietRecorder(), {}
        self.sim, self.stream = SharedSim(), events.Stream()
        self.args = SimpleNamespace(device='cpu', output_dir=Path(directory), integration_case=entry.CASE)
        self.config = SimpleNamespace(near_m=.01, far_m=10., horizontal_fov_deg=60.)
        self.runs = []
        for robot_id in (1, 0):  # mapping must not rely on construction order
            runtime = events.runtime_fixture()
            runtime.stream, runtime.source_now = self.stream, Fraction(2, 120)
            runtime.context = SimpleNamespace(get_rendering_event_stream=lambda: self.stream, get_stage_id=lambda: 7)
            runtime.product.path = f'/Render/Owned_R{robot_id}'
            runtime.product_path_for_name = lambda name, p=runtime.product.path: p
            runtime.prim_exists = lambda path: False
            runtime.product_camera_targets = lambda path, r=robot_id: [f'/World/CR12_{r}/Camera']
            receive = {}
            capture = camera.OwnedCameraCapture.prepare(f'/World/CR12_{robot_id}/Camera', (4, 3),
                lambda receive=receive: receive, runtime=runtime, max_requests=2, integration_mode=True,
                product_name=f'CR12_R{robot_id}_Capture', camera_name=f'camera{robot_id}', observer_name=f'obs{robot_id}')
            capture.initialize_off()
            self.sim.captures.append(capture); self.sim.runtimes.append(runtime)
            recorder = QuietRecorder()
            recorder.result['initialization'] = {'before_reset_clock': [0, 0.]}
            self.runs.append(dict(robot_id=robot_id, recorder=recorder, resources={'capture': capture},
                scene={'sim': self.sim, 'robot': object(), 'robot_id': robot_id, 'prim_path': f'/World/CR12_{robot_id}'},
                initial={'baseline': (2, 2/120)}, receive_context=receive,
                mount_aggregate={'count': 0, 'maximum_position_error_m': 0., 'maximum_orientation_error_rad': 0.},
                initial_camera={}, initial_parameters={}))
        self.host = hosts.CR12IntegrationHost(self.args, None, self.recorder, self.resources, {}, self.config,
            setup=lambda: self.runs, session_factory=FakeSharedSession, instance_specs=entry.instance_specs(),
            cross_checker=lambda *a: dict(logical_pairs=100, coarse_tests=1, coarse_separated=True,
                fine_pairs_checked=0, minimum_axis_gap_m=1., gap_basis='CPU FAKE geometry'))
        d = self.host.domain
        runtime = contracts.S.EventProfileSynchronousRuntimeCoordinator(environment=self.host,
            current_read_port=d.current_read_port, production_claim_port=d.production_claim_port,
            physical_step_admission_port=d.physical_step_admission_port,
            standalone_reset_admission_port=d.standalone_reset_admission_port,
            terminal_consumer_port=d.terminal_consumer_port, fence_read_port=d.interstep_fence_read_port)
        self.facade = contracts.F._compose_event_assignment_runtime_facade(
            resolved_assignment_profile=self.host.profile, runtime_domain=d, synchronous_runtime=runtime)
        self.facade.reset()

    def step(self, proposal=None):
        h = self.host
        if proposal is None: proposal = entry.next_proposals(h, self.facade.read_current())
        if proposal is None: return self.facade.step_without_new_claim(action_builder=h.bind_effective_assignment)
        problem = h.assignment_problem()
        decision = self.facade.capture_proposal_decision(feasible_mask=problem['feasible_mask'], cost_matrix=problem['cost_matrix'])
        return self.facade.resolve_and_step_proposals(raw_action_ids=h.i([proposal[0]]),
            decoded_proposal=h.i([proposal[1]]), decision=decision, action_builder=h.bind_effective_assignment)

    def until(self, predicate, limit=90):
        for _ in range(limit):
            if predicate(): return
            self.step()
        raise AssertionError('CPU orchestration fixture exceeded finite test limit')


class SharedHostTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.object(startup, 'native_validity', lambda *a: {'CPU_FAKE': True}))
        self.stack.enter_context(patch.object(runners, 'actual_camera_pose',
            lambda *a, **k: {'position_error_m': 0., 'orientation_error_rad': 0.}))
    def tearDown(self): self.stack.close()

    def test_full_real_host_cancel_bound_retreat_clear_R_B_C_sidecar_ACK(self):
        f = SharedFixture(self.directory); h = f.host
        self.assertEqual((h.setup_ticks, h.total_transitions, len(h.claims)), (121, 0, 0))
        json.dumps(h.shared_handover['setup'], allow_nan=False)
        self.assertEqual(h.shared_handover['setup']['sessions'][0]['setup_stable_span_s'], 1.)
        self.assertEqual(h.domain.current_read_port.read_current().lifecycle_state.ownership.tolist(), [[-1]])
        f.until(lambda: h.runner is not None and h.runner.execution_phase == 'RETREATING_BOUND')
        a = h.runner.binding
        self.assertTrue(h.runner.terminal); self.assertFalse(h.runner.delivery_ready)
        self.assertIsNone(h.adapter.pending_result(0)); self.assertEqual(h.deliveries, [])
        self.assertEqual(h.domain.current_read_port.read_current().lifecycle_state.ownership.tolist(), [[0]])
        f.until(lambda: len(h.deliveries) == 1)
        row = h.requests[0]
        self.assertEqual(row['request']['failure']['category'], 'CANCELLED')
        self.assertFalse(row['request']['acquired']); self.assertTrue(row['retired_after_receipt'])
        self.assertGreaterEqual(row['clear_evidence']['stable_samples'], 121)
        self.assertGreaterEqual(row['clear_evidence']['stable_span_s'], 1.-1e-6)
        self.assertEqual((h.shared_handover['clear_release']['pending_step']-h.setup_ticks) % 12, 0)
        self.assertEqual(h.adapter.history[0].binding, a)
        self.assertEqual(h.domain.current_read_port.read_current().lifecycle_state.ownership.tolist(), [[-1]])
        while not h.finished: last = f.step()
        history = historical_summary(last.terminal_historical_payload[0])
        pending = h.domain.terminal_consumer_port.capture_pending_terminal_artifacts()
        rows = entry.check_business(h, history, pending)
        self.assertEqual(history['completion_count'], [0, 1])
        self.assertEqual((history['sidecar_critic_dimension'], history['sidecar_audit_dimension']), (71, 71))
        self.assertEqual(pending, ()); self.assertEqual(len(h.adapter.history), 2)
        self.assertEqual([r['robot_id'] for r in h.claims], [0, 1])
        self.assertEqual([r['task_id'] for r in h.claims], [0, 0])
        self.assertNotEqual(h.claims[0]['claim_token'], h.claims[1]['claim_token'])
        self.assertTrue(rows[1]['artifact_saved']); self.assertFalse(rows[0].get('artifact_saved', False))
        self.assertEqual(len(list(Path(self.directory).glob('robot_*/task_*/claim_*/camera_rgba.png'))), 1)
        self.assertFalse(h.adapter.history[1].pending.custody.rgba.flags.writeable)
        self.assertEqual(f.sim.steps, h.setup_ticks+12*h.total_transitions)
        self.assertEqual(f.sim.renders, f.sim.steps//2)
        self.assertTrue(h.rebuilds[-1]['physics_unchanged'])
        self.assertEqual([c.session.submissions for c in h._ordered()], [1, 1])
        self.assertEqual([c.session.retreats for c in h._ordered()], [1, 0])

    def test_early_pending_R_is_rejected_with_real_binding_retained(self):
        f = SharedFixture(self.directory); h = f.host
        f.until(lambda: h.runner is not None and h.runner.execution_phase == 'RETREATING_BOUND')
        with self.assertRaisesRegex(Exception, 'Camera terminal'):
            h._record_pending(h.contexts[0], h.runner.latest_tick)
        self.assertIsNone(h.adapter.pending_result(0)); self.assertEqual(h.adapter.history, ())
        self.assertEqual(h.domain.current_read_port.read_current().lifecycle_state.ownership.tolist(), [[0]])

    def test_B_cannot_enter_before_clear_receipt_and_retirement(self):
        f = SharedFixture(self.directory); h = f.host
        f.step()
        with self.assertRaisesRegex(Exception, 'preceding real A release'): h.check_shared_successor_ready()
        receipt = f.step(([0, 0], [0, 0]))  # actual resolver suppresses B, not a scripted outcome
        self.assertEqual(receipt.admitted_effective_assignment.tolist(), [[0, -1]])
        self.assertEqual(len(h.claims), 1); self.assertIsNone(h.contexts[1].runner)

    def test_post_receipt_retirement_failure_is_preserved_and_poison_blocks_next_step(self):
        f = SharedFixture(self.directory); h = f.host
        f.until(lambda: h.runner is not None and h.runner.execution_phase == 'RETREATING_BOUND')
        with patch.object(h.contexts[0].capture, 'retire_request', side_effect=RuntimeError('CPU retire failure')):
            with self.assertRaisesRegex(RuntimeError, 'CPU retire failure'):
                f.until(lambda: len(h.deliveries) == 1)
        self.assertEqual(len(h.deliveries), 1); self.assertEqual(len(h.adapter.history), 1)
        self.assertIsNotNone(h.contexts[0].runner); self.assertFalse(h.finished)
        self.assertTrue(bool(h.adapter.history[0].result.released_tasks[0, 0]))
        previous_steps = f.sim.steps
        with self.assertRaises(Exception): f.facade.step_without_new_claim(action_builder=h.bind_effective_assignment)
        self.assertEqual(f.sim.steps, previous_steps)
        self.assertEqual(len(h.claims), 1)

    def test_live_clear_degradation_after_R_blocks_B_without_new_physics(self):
        f = SharedFixture(self.directory); h = f.host
        f.until(lambda: len(h.deliveries) == 1)
        h.contexts[0].session.state['dq'][4] = .011
        before = f.sim.steps
        with self.assertRaises(Exception): f.step()
        self.assertEqual(f.sim.steps, before); self.assertEqual(len(h.claims), 1)

    def test_setup_summary_saves_with_real_recorder_list_qcmd_array_scanner(self):
        f = SharedFixture(self.directory)
        recorder = Recorder(); recorder.path = Path(self.directory)/'setup_result.json'
        recorder.result['shared_handover'] = f.host.shared_handover
        recorder.save()
        saved = json.loads(recorder.path.read_text(encoding='utf-8'))['shared_handover']['setup']
        self.assertEqual(saved['status'], 'SETUP_HOLD_READY')
        self.assertEqual([r['setup_stable_span_s'] for r in saved['sessions']], [1., 1.])
        self.assertTrue(all(len(r['q_cmd']) == 6 and len(r['scanner']) == 4 for r in saved['sessions']))

    def test_post_step_failure_preserves_actual_tick_partial_block_and_reached_layers(self):
        f = SharedFixture(self.directory); h = f.host
        before = f.sim.steps
        with patch.object(h.session, 'observe_physics', side_effect=RuntimeError('CPU post-step guard')):
            with self.assertRaisesRegex(RuntimeError, 'CPU post-step guard'): f.step()
        self.assertEqual(f.sim.steps, before+1)
        self.assertEqual(f.recorder.result['completed_physics_steps'], before+1)
        self.assertEqual(h.summary()['global_physics_ticks'], before+1)
        self.assertEqual(h.summary()['last_completed_guarded_tick'], before)
        self.assertEqual(h.summary()['partial_block_ticks'], 1)
        self.assertTrue(all(c.session.aborted for c in h._ordered()))
        layers = dict.fromkeys(entry.LAYERS, 'NOT_REACHED')
        entry.update_layers(h, layers)
        self.assertEqual(layers['NONZERO_SETUP_HOLD'], 'PASS')
        self.assertEqual(layers['A_BOUND_RETREAT_AND_CLEAR_RELEASE'], 'NOT_REACHED')
        self.assertEqual(h.deliveries, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
