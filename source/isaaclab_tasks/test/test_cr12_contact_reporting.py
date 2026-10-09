"""CPU checks of actual phase/context and separate resource snapshots."""
from pathlib import Path
import copy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/environments'))
import _cr12_lifecycle_host as hosts
import run_cr12_single_view_capture as entry
import _cr12_scan_executor as executor
import test_cr12_scan_executor as old_executor
import test_cr12_shared_lifecycle_host as shared


class ReportingTests(unittest.TestCase):
    def test_live_phase_changes_with_control_not_fixed_retreat_label(self):
        h = hosts.CR12IntegrationHost.__new__(hosts.CR12IntegrationHost)
        h.args = SimpleNamespace(output_dir=Path('attempt_01'))
        h.total_transitions = 12; h.shared = h.dual = True
        h.recorder = SimpleNamespace(result={})
        state = dict(execution_phase='SETUP_SETTLING', control_segment_id='setup_robot_1')
        c = SimpleNamespace(robot_id=1, recorder=SimpleNamespace(), runner=None,
                            session=SimpleNamespace(current_state=lambda: copy.deepcopy(state)))
        row = h._set_runtime_phase('observe_physics', c, setup=True)
        self.assertIsNone(row['host_transition'])
        self.assertIn('SETUP_SETTLING', h.recorder.phase)
        c.runner = SimpleNamespace(execution_phase='APPROACHING')
        state['control_segment_id'] = 'binding:approach'
        row = h._set_runtime_phase('observe_physics', c)
        self.assertEqual(row['host_transition'], 13)
        self.assertIn('APPROACHING', h.recorder.phase)
        c.runner.execution_phase = 'RETREATING_BOUND'; state['control_segment_id'] = 'binding:retreat'
        row = h._set_runtime_phase('observe_physics', c)
        self.assertIn('RETREATING_BOUND', h.recorder.phase)
        self.assertIn('robot_1', h.recorder.phase)
        row['phase'] = 'foreign mutation'
        self.assertEqual(h.recorder.result['runtime_context']['phase'], 'RETREATING_BOUND')
        c.runner = None
        self.assertEqual(h._set_runtime_phase('before_tick', c)['phase'], 'IDLE_HOLD')
        self.assertEqual(h._set_runtime_phase('receipt_and_retirement')['host_transition'], 12)

    def test_actual_host_failure_keeps_current_observe_phase_and_partial_tick(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(shared.startup, 'native_validity', lambda *a: {'CPU_FAKE': True}), \
                patch.object(shared.runners, 'actual_camera_pose',
                             lambda *a, **k: {'position_error_m':0., 'orientation_error_rad':0.}):
            f = shared.SharedFixture(tmp); h = f.host
            with patch.object(h.session, 'observe_physics', side_effect=RuntimeError('contact sample rejected')):
                with self.assertRaisesRegex(RuntimeError, 'contact sample rejected'): f.step()
            self.assertEqual(h.recorder.phase, 'shared:APPROACHING:observe_physics:robot_0')
            context = h.session.contact_context
            self.assertEqual(context['global_physics_step'], h.setup_ticks+1)
            self.assertEqual(context['host_transition'], 1)
            self.assertEqual(context['robot_id'], 0)
            self.assertEqual(context['phase'], 'APPROACHING')
            self.assertEqual(h.partial_block_ticks, 1)

    def test_executor_forwards_same_tick_context_once(self):
        s = old_executor.SessionTests.fixture(self)
        s.contact_context = {'run_id':'run','robot_id':1,'host_transition':7,'phase':'APPROACHING'}
        s.submit_goal('claim', s.actual_scanner)
        seen=[]
        def read(contacts, dt, *, context):
            seen.append(copy.deepcopy(context)); contacts['sensor']['updates'] += 1
            return 0.
        with patch.object(executor, '_check_contacts', read):
            old_executor.SessionTests.advance(self, s)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]['global_physics_step'], 1)
        self.assertEqual(seen[0]['physics_clock'], list(s.sim.clock))
        self.assertEqual((seen[0]['robot_id'],seen[0]['host_transition']), (1,7))

    def test_release_snapshots_are_distinct_from_mutated_live_buffers(self):
        state={'lifecycle':{'release_effective_count':0},'released':False}
        def release():
            state['lifecycle']['release_effective_count']=1; state['released']=True
            return {'complete':True,'errors':[]}
        capture=SimpleNamespace(summary=lambda:state,release=release)
        recorder=SimpleNamespace(result={})
        returned=entry.release_capture_with_record(capture,recorder)
        self.assertTrue(returned['complete'])
        self.assertFalse(recorder.result['camera_backend']['released'])
        self.assertFalse(recorder.result['camera_backend_pre_release']['released'])
        self.assertTrue(recorder.result['camera_backend_post_release']['released'])
        self.assertEqual(recorder.result['camera_backend_snapshot_at'],'pre_release')
        state['lifecycle']['release_effective_count']=99
        self.assertEqual(recorder.result['camera_backend_post_release']['lifecycle']['release_effective_count'],1)

    def test_release_failure_does_not_invent_a_post_release_snapshot(self):
        def release(): raise RuntimeError('owned release failed')
        capture=SimpleNamespace(summary=lambda:{'released':False},release=release)
        recorder=SimpleNamespace(result={})
        with self.assertRaisesRegex(RuntimeError,'owned release failed'):
            entry.release_capture_with_record(capture,recorder)
        self.assertEqual(recorder.result['camera_backend_post_release'],'NOT_READ')
        self.assertNotIn('camera_release',recorder.result)


if __name__ == '__main__': unittest.main()
