"""CPU tests for the fixed sequence gate and immutable delivery boundaries."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import _cr12_two_view_capture as two
import run_cr12_two_view_capture as entry
import run_cr12_single_view_capture as shared


def complete(index=1):
    return {'status': 'SUCCEEDED_OFF', 'goal_id': f'goal_{index}',
        'capture_id': f'capture_{index}', 'capture_metadata_path': '/test/metadata.json',
        'single_view_request': {'state': 'SUCCEEDED_OFF', 'acquired': True,
            'artifact_saved': True, 'off_confirmed': True, 'failure': None},
        'capture_summary': {'fresh_frame_confirmed': True, 'product_identity_confirmed': True,
            'moving_off_verified': True}, 'off_confirmation': {'confirmed': True}}


class TwoViewSequenceTests(unittest.TestCase):
    def test_first_off_save_fresh_and_no_error_are_all_required(self):
        for key in ('acquired', 'artifact_saved', 'off_confirmed'):
            with self.subTest(key=key):
                seq = two.TwoViewSequence(); seq.start(0)
                row = complete(); row['single_view_request'][key] = False
                seq.finish(0, row)
                with self.assertRaises(two.DriveCheckError): seq.start(1)
        for key in ('artifact_error', 'metadata_error'):
            row = complete(); row[key] = 'CPU failure'
            with self.assertRaises(two.DriveCheckError): two.require_completed_view(row)
        row = complete(); row['capture_summary']['fresh_frame_confirmed'] = False
        with self.assertRaises(two.DriveCheckError): two.require_completed_view(row)

    def test_terminal_result_is_not_aliased_or_cleared_by_goal_two(self):
        seq = two.TwoViewSequence(); seq.start(0); row = complete()
        seq.finish(0, row); before = copy.deepcopy(seq.views[0])
        row['single_view_request']['acquired'] = False
        seq.start(1); seq.finish(1, complete(2))
        self.assertEqual(seq.views[0], before)
        records = seq.records(); records[0]['status'] = 'changed'
        self.assertEqual(seq.views[0], before)

    def test_first_failure_blocks_second_without_inventing_capture_failure(self):
        seq = two.TwoViewSequence(); seq.start(0)
        seq.finish(0, {'status': 'FAILED_OFF', 'acquired': True, 'artifact_saved': False})
        self.assertEqual(seq.views[1]['status'], 'NOT_STARTED')
        self.assertTrue(seq.views[1]['blocked_by_previous_failure'])
        with self.assertRaises(two.DriveCheckError): seq.start(1)
        self.assertTrue(seq.views[0]['acquired'])

    def test_second_failure_preserves_first_success_and_failure_is_sticky(self):
        seq = two.TwoViewSequence(); seq.start(0); seq.finish(0, complete())
        before = copy.deepcopy(seq.views[0]); seq.start(1)
        seq.finish(1, {'status': 'STOP_UNCONFIRMED', 'acquired': True})
        first_error = copy.deepcopy(seq.failure); seq.fail('later', 'cannot hide')
        self.assertEqual(seq.failure, first_error); self.assertEqual(seq.views[0], before)
        with self.assertRaises(two.DriveCheckError): seq.start(1)

    def test_no_parallel_request_or_third_goal(self):
        seq = two.TwoViewSequence(); seq.start(0)
        with self.assertRaises(two.DriveCheckError): seq.start(1)
        seq.finish(0, complete()); seq.start(1); seq.finish(1, complete(2))
        with self.assertRaises(two.DriveCheckError): seq.start(2)

    def test_pre_request_filesystem_or_record_failure_never_leaves_running(self):
        for index in (0, 1):
            with self.subTest(index=index):
                seq = two.TwoViewSequence()
                if index:
                    seq.start(0);seq.finish(0,complete())
                first=copy.deepcopy(seq.views[0]);seq.start(index)
                seq.fail('artifact_directory','CPU mkdir failure')
                self.assertEqual(seq.views[index]['status'],'FAILED')
                self.assertIsNone(seq.active)
                self.assertTrue(seq.views[index]['result_not_finalized'])
                if index:self.assertEqual(seq.views[0],first)
                else:self.assertEqual(seq.views[1]['status'],'NOT_STARTED')

    def test_first_image_metadata_request_and_result_mutation_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            png, metadata = Path(folder)/'camera.png', Path(folder)/'metadata.json'
            png.write_bytes(b'CPU fixture only'); metadata.write_text('{}')
            summary = {'goal_id': 'goal_1', 'state': 'SUCCEEDED_OFF'}
            request = SimpleNamespace(summary=lambda: copy.deepcopy(summary))
            snapshot = {'rgba': np.zeros((2,2,4),np.uint8), 'metadata': {'source_frame': 13}}
            row = {'camera_artifact': {'path': str(png)}, 'capture_metadata_path': str(metadata)}
            before = two.immutable_evidence(request, snapshot, row)
            self.assertTrue(two.verify_immutable(before,two.immutable_evidence(request,snapshot,row))['pass'])
            for kind in ('rgba', 'metadata', 'request', 'result', 'png', 'file_metadata'):
                with self.subTest(kind=kind):
                    frame = copy.deepcopy(snapshot); report = copy.deepcopy(row)
                    saved = dict(summary)
                    if kind=='rgba': frame['rgba'][0,0,0]=1
                    elif kind=='metadata': frame['metadata']['source_frame']=99
                    elif kind=='request': summary['state']='changed'
                    elif kind=='result': report['changed']=True
                    elif kind=='png': png.write_bytes(b'changed')
                    else: metadata.write_text('{"changed":true}')
                    with self.assertRaises(two.DriveCheckError):
                        two.verify_immutable(before,two.immutable_evidence(request,frame,report))
                    summary.clear(); summary.update(saved)
                    png.write_bytes(b'CPU fixture only'); metadata.write_text('{}')

    def test_zero_step_handoff_preserves_real_qcmd_and_identity(self):
        state = {'native_clock':[665,5.54], 'q':[.01]*6, 'dq':[.001]*6,'scanner':np.eye(4).tolist()}
        tick = {'step':663,'render_count':331,'q':np.array(state['q']), 'dq':np.array(state['dq']),
            'scanner':np.eye(4), 'q_cmd':[.012]*6, 'dq_cmd':[.0002]*6}
        identity={'camera_id':101,'product_id':102}
        capture=SimpleNamespace(assert_off=mock.Mock(return_value={'updates_enabled':False}),
            device_identity=lambda:dict(identity), summary=lambda:{'product_event_count':3,'unique_product_event_count':1})
        context=SimpleNamespace(queue_goal_2=mock.Mock(return_value={'pending':True}))
        request=SimpleNamespace(summary=lambda:complete()['single_view_request'])
        recorder=SimpleNamespace(result={},save=mock.Mock())
        with mock.patch.object(two,'read_handoff_native',side_effect=[copy.deepcopy(state),copy.deepcopy(state)]):
            row=two.handoff_goal_2(context,complete(),request,tick,{},capture,recorder)
        self.assertTrue(row['no_physics_advance']);self.assertTrue(row['native_state_unchanged'])
        self.assertEqual(row['q_cmd'],[.012]*6);self.assertNotEqual(row['q_cmd'],state['q'])
        self.assertFalse(row['pass'])  # activation must still independently verify before next command
        context.queue_goal_2.assert_called_once()
        wrong=copy.deepcopy(state);wrong['q'][0]+=.001
        with mock.patch.object(two,'read_handoff_native',return_value=wrong):
            with self.assertRaises(two.DriveCheckError):two.handoff_goal_2(context,complete(),request,tick,{},capture,recorder)

    def test_resource_path_equality_is_not_object_reuse(self):
        life=dict(prepare_calls=1,initialize_calls=1,begin_calls=2,off_confirmed_count=2,
            release_effective_count=1,camera_create_calls=1,product_create_calls=1,observer_create_calls=1,
            off_requests=2,request_resume_calls=2,request_pause_calls=2)
        rows=[{'camera_id':1,'product_id':2,'render_product_path':'same'} for _ in range(3)]
        self.assertTrue(two.resource_continuity({'lifecycle':life},rows)['unchanged'])
        rows[2]['product_id']=3
        self.assertFalse(two.resource_continuity({'lifecycle':life},rows)['unchanged'])
        rows[2]['product_id']=2;life['initialize_calls']=2
        self.assertFalse(two.resource_continuity({'lifecycle':life},rows)['unchanged'])

    def test_new_entry_selects_sequence_only_explicitly(self):
        with mock.patch.object(shared,'main',return_value=0) as main:
            self.assertEqual(entry.main(),0)
        self.assertIs(main.call_args.kwargs['capture_runner'],two.run_two_capture)
        self.assertEqual(main.call_args.kwargs['success_label'],'TWO_VIEW_CAPTURE_INTEGRATION_PASS')
        self.assertTrue(main.call_args.kwargs['entry_source'].endswith('run_cr12_two_view_capture.py'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
