"""CPU checks of the sole-App supervisor; no subprocess, Kit or CUDA operation."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT/'logs/scan_assignment/20261009_cr12_shared_task_handover/repro/supervise_cr12_shared_task.py'
spec = importlib.util.spec_from_file_location('shared_supervisor_test_subject', PATH)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class SharedSupervisorTests(unittest.TestCase):
    def test_command_uses_new_entry_case_and_original_gui_controls(self):
        attempt = S.OUTPUT_ROOT/'attempt_01'
        command = S.build_command(attempt, S.CASE)
        self.assertIn(S.ENTRY, command)
        self.assertEqual(command[command.index('--integration-case')+1], S.CASE)
        self.assertEqual(command[command.index('--device')+1], 'cuda:0')
        self.assertEqual(command[command.index('--external-forces-every-iteration')+1], 'on')
        self.assertIn('--enable_cameras', command)
        payload = next(v for v in command if v.startswith('--kit_args='))
        for token in S.DPI_TOKENS: self.assertEqual(payload.count(token), 1)
        self.assertIn('--/app/vulkan=false', S.expected_kit_tokens(attempt))
        self.assertEqual(S.MODE_OVERRIDES['PYTHONUTF8'], '1')
        self.assertEqual((S.APP_LIMIT_SECONDS, S.CASE_LIMITS[S.CASE]['total_seconds']), (180, 2400))
        with self.assertRaises(ValueError): S.build_command(attempt, 'staggered_normal')

    def test_only_new_attempt_one_is_authorized_and_existing_attempt_consumes_slot(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(S, 'OUTPUT_ROOT', Path(tmp)):
            attempt = Path(tmp)/'attempt_01'
            self.assertEqual(S.budget_for_attempt(attempt, S.CASE)['max_apps'], 1)
            self.assertFalse(S.budget_for_attempt(attempt, S.CASE)['retry_allowed'])
            with self.assertRaises(ValueError): S.budget_for_attempt(Path(tmp)/'attempt_02', S.CASE)
            attempt.mkdir()
            with self.assertRaises(FileExistsError): S.budget_for_attempt(attempt, S.CASE)

    def test_freeze_requires_every_check_and_unchanged_direct_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); output = root/'output'; (output/'repro').mkdir(parents=True)
            code = root/'direct.py'; code.write_text('x=1\n', encoding='utf-8')
            value = dict(task=S.TASK, all_passed=True,
                checks={k: True for k in S.REQUIRED_CHECKS}, code_sha256={'direct.py': S.sha256(code)})
            pre = output/'repro/preflight.json'
            with patch.object(S, 'REPO_ROOT', root), patch.object(S, 'OUTPUT_ROOT', output), \
                    patch.object(S, 'required_code_paths', lambda: {'direct.py'}):
                pre.write_text(json.dumps(value), encoding='utf-8'); S.shared_preflight()
                value['checks']['shared_supervisor_cpu'] = False
                pre.write_text(json.dumps(value), encoding='utf-8')
                with self.assertRaises(ValueError): S.shared_preflight()
                value['checks']['shared_supervisor_cpu'] = True
                pre.write_text(json.dumps(value), encoding='utf-8'); code.write_text('x=2\n', encoding='utf-8')
                with self.assertRaises(ValueError): S.shared_preflight()

    def test_missing_business_is_not_pass_even_if_exit_zero_and_png_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); (path/'camera_rgba.png').write_bytes(b'not evidence')
            checks = S.completion_checks({'classification': S.FAIL_LABEL, 'failures': []},
                {'case': S.CASE, 'process_exit_pass': True}, path)
            self.assertFalse(any(checks.values()))

    def test_setup_verifies_frozen_root_not_actual_derived_expectation(self):
        before, after = [0, 0.], [2, 2*S.profile.DT]
        instances = []
        for i in (0, 1):
            root = f'/World/CR12_{i}'
            instances.append(dict(robot_id=i, native_instance_mapping=dict(object_id=i+1, view_object_id=i+11,
                verified=True, prim_path=root, native_body_paths=[root+'/b'+str(j) for j in range(7)],
                native_dof_paths=[root+'/j'+str(j) for j in range(6)]),
                preinit_instance_mapping=dict(independent_expected_root=S.profile.root_pose(i).tolist(),
                    body_and_joint_paths_verified=True), initialization=dict(joint_state_writes=1, root_state_writes=0)))
        entry = dict(instance_setup=instances, initialization=dict(before_reset_clock=before, after_reset_clock=after,
            reset_calls=1, hidden_settle_steps=0), common_camera_publication=dict(pass_=True, forward_calls=1, instance_count=2))
        entry['common_camera_publication']['pass'] = True
        self.assertTrue(S.setup_valid(entry))
        instances[1]['preinit_instance_mapping']['independent_expected_root'] = S.profile.root_pose(0).tolist()
        self.assertFalse(S.setup_valid(entry))

    def test_real_cpu_authority_chain_satisfies_handover_supervision_with_retreat_blocks(self):
        # Reuse actual production Host/facade/FSM. Only physics/events are synthetic.
        import test_cr12_shared_lifecycle_host as H
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(H.startup, 'native_validity', lambda *a: {'CPU_FAKE': True}), \
                patch.object(H.runners, 'actual_camera_pose', lambda *a, **k: {'position_error_m': 0., 'orientation_error_rad': 0.}):
            f = H.SharedFixture(tmp); h = f.host
            while not h.finished: last = f.step()
            e = dict(instance_setup=[], shared_handover=h.shared_handover, host_summary=h.summary(),
                completed_physics_steps=f.sim.steps, requests=h.requests, authority_claims=h.claims,
                authority_deliveries=h.deliveries, schema_dimensions={'actor':73,'critic':71})
            result = dict(case=S.CASE)
            checks = S.completion_checks(e, result, Path(tmp))
            self.assertTrue(checks['nonzero_setup'])
            self.assertTrue(checks['host_and_authority'])
            self.assertTrue(checks['a_cancel_off'])
            self.assertTrue(checks['clear_release_handover'])
            self.assertTrue(checks['b_fresh_off'])
            a = e['requests'][0]
            self.assertTrue(any(not r['holding'] for r in a['block_end_checks']))
            a['clear_evidence']['fixed_q_error_rad'] = .02
            self.assertFalse(S.completion_checks(e, result, Path(tmp))['clear_release_handover'])

    def test_failed_setup_preserves_earlier_layer_and_not_hit_never_becomes_success(self):
        checks = {k: False for k in S.completion_checks({}, {}, Path('.'))}
        result = dict(case=S.CASE, console_evidence={}, kit_log={}, stage_names=['app_constructor_begin'],
                      process_exit_pass=True, supervisor_errors=[])
        entry = dict(case_classification='NOT_HIT', authority_claims=[{}], requests=[],
                     validation_layers={'A_APPROACH_AND_CANCEL_OFF':'PASS'})
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(S, 'completion_checks', lambda *a: checks), \
                patch.object(S, 'post_config_summary', lambda *a: {'source_status':'UNCHANGED','source_unchanged':True,'errors':[]}), \
                patch.object(S.base, 'startup_layers', lambda *a: {'GUI_APP_CONSTRUCTION':'PASS'}), \
                patch.object(S, 'shared_preflight', lambda: (None, {})):
            S.finish_result(entry, result, Path(tmp), {'all_passed':True}, {}, {})
            self.assertEqual(result['classification'], 'NOT_HIT')
            self.assertFalse(result['integration_runtime_pass'])
            self.assertEqual(result['validation_layers']['A_APPROACH_AND_CANCEL_OFF'], 'PASS')
            self.assertEqual(result['validation_layers']['B_SHARED_TASK_CAPTURE'], 'NOT_REACHED')


if __name__ == '__main__':
    unittest.main()
