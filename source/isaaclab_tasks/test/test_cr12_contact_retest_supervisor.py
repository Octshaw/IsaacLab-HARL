"""Targeted CPU supervisor contracts; synthetic evidence, no processes or App."""
from contextlib import ExitStack
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT/'logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py'
spec = importlib.util.spec_from_file_location('_contact_retest_supervisor_tests', PATH)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def contact_entry(total=9000):
    instances = []
    for robot in (0, 1):
        paths, sensors = {}, {}
        for index, body in enumerate(S.BODY_NAMES):
            path = paths[body] = f'/World/CR12_{robot}/CR12/{body}'
            identity = 1+7*robot+index
            current = dict(value=75., dtype='float32', device='cuda:0', shape=[1], finite=True)
            sample = dict(passed=True, sensor_object_id=identity, generation=f'sensor_{identity}',
                context={'global_physics_step':total, 'physics_clock':[total+2,(total+2)/120]},
                current=current, last_update=copy.deepcopy(current), outdated={'value':False},
                read_state={'force':'READ','clock':'READ'},
                checks={k:True for k in ('sensor_initialized','sensor_identity','mapping','force_shape',
                    'force_finite','force_device','clock_metadata','call_mode','time','force_threshold')},
                time_validation={'passed':True,'old_shadow_pass':True})
            shadow = copy.deepcopy(sample); shadow['time_validation']['old_shadow_pass'] = False
            bounds = {str(edge): [dict(passed=True,current={'value':edge-.008}),
                                 dict(passed=True,current={'value':edge+.008})] for edge in (32,64)}
            sensors[body] = dict(body_path=path, sensor_object_id=identity, generation=f'sensor_{identity}', updates=total,
                diagnostics=dict(schema='contact_freshness_v1', first_failure=None, advance_pass_count=total,
                    update_call_count=total+1, baseline_pass_count=1, check_attempt_count=total+1,
                    readonly_pass_count=0, first_baseline=copy.deepcopy(sample), last_sample=sample,
                    boundary_samples=bounds, first_shadow_disagreements={'old_reject_new_accept':shadow}, max_force_n=0.))
        instances.append(dict(robot_id=robot, usd_readback={'body_paths':paths}, contact_summary=sensors))
    return dict(completed_physics_steps=total, instance_setup=instances)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.output = self.root/'output'; (self.output/'repro').mkdir(parents=True)
        self.stack.enter_context(patch.object(S, 'REPO_ROOT', self.root))
        self.stack.enter_context(patch.object(S, 'OUTPUT_ROOT', self.output))
        self.profile = self.root/S.PROFILE_PATH
        self.profile.parent.mkdir(parents=True); self.profile.write_text('fixed physics\n', encoding='utf-8')
        self.code = self.root/'direct.py'; self.code.write_text('version1\n',encoding='utf-8')
        self.cpu = self.root/'cpu.txt'; self.cpu.write_text('PASS synthetic CPU fixture\n',encoding='utf-8')
        self.stack.enter_context(patch.object(S, 'required_code_paths', lambda: {'direct.py'}))
        self.select(1)
    def tearDown(self): self.stack.close()

    def select(self, index):
        S._ACTIVE_ATTEMPT = self.output/f'attempt_{index:02d}'
        S._ACTIVE_PREFLIGHT = self.output/'repro'/f'preflight_attempt_{index:02d}.json'

    def preflight(self):
        value = dict(task=S.TASK,attempt=S._ACTIVE_ATTEMPT.name,all_passed=True,
            checks={key:True for key in S.REQUIRED_CHECKS},code_sha256={'direct.py':S.sha256(self.code)},
            frozen_contract_sha256=S.sha256(self.profile), frozen_physics_inputs={S.PROFILE_PATH:S.sha256(self.profile)},
            contact_numeric_contract={'all_passed':True,'path':'cpu.txt','sha256':S.sha256(self.cpu)})
        S.write_json(S._ACTIVE_PREFLIGHT, value)
        return value

    def previous(self, index, *, success=False, active=False):
        self.select(index); value = self.preflight()
        attempt = S._ACTIVE_ATTEMPT; attempt.mkdir()
        S.write_json(attempt/'preflight.json',value)
        result = dict(integration_runtime_pass=success,classification=S.PASS_LABEL if success else S.FAIL_LABEL,
            all_owned_processes_exited=not active,remaining_owned_pids=[41] if active else [],
            seen_owned_pids=[41],ended_at='synthetic complete',stage_names=['app_constructor_begin'],
            controlled_attempt_counted=True)
        S.write_json(attempt/'supervisor_result.json',result)
        return attempt

    def repair(self, previous):
        self.code.write_text(self.code.read_text(encoding='utf-8')+'targeted fix\n',encoding='utf-8')
        value = self.preflight()
        evidence = dict(previous_attempt=previous.name,cause='Synthetic verified local wiring mismatch',
            failure_kind='local_wiring',requires_new_app=True,within_authorized_scope=True,
            unresolved_safety_or_semantic_issue=False,
            direct_evidence=[{'path':(previous/'supervisor_result.json').relative_to(self.root).as_posix(),
                              'sha256':S.sha256(previous/'supervisor_result.json')}],
            fix={'symbols':['affected_symbol'],'changed_files':['direct.py'],'restores_existing_contract':True},
            cpu_validation={'passed':True,'command':'python -B targeted_test.py','path':'cpu.txt','sha256':S.sha256(self.cpu)})
        path = self.output/'repro'/('repair_'+S._ACTIVE_ATTEMPT.name+'.json')
        S.write_json(path,evidence)
        return value,path

    def test_original_entry_command_physics_and_GUI_values_are_preserved(self):
        command = S.build_command(self.output/'attempt_01',S.CASE)
        self.assertIn('scripts/environments/run_cr12_shared_task_handover.py',command)
        self.assertEqual(command[command.index('--device')+1],'cuda:0')
        self.assertEqual(command[command.index('--external-forces-every-iteration')+1],'on')
        self.assertEqual(len([x for x in command if x.startswith('--kit_args=')]),1)
        for token in S.DPI_TOKENS: self.assertIn(token,command[-1])
        self.assertEqual((S.APP_LIMIT_SECONDS,S.CASE_LIMITS[S.CASE]['total_seconds']),(180,2400))

    def test_primary_fresh_exact_directory_and_no_automatic_retry(self):
        result = S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE)
        self.assertEqual(result['max_apps'],3); self.assertFalse(result['automatic_retry'])
        with self.assertRaises(ValueError): S.budget_for_attempt(self.output/'attempt_02',S.CASE)
        S._ACTIVE_ATTEMPT.mkdir()
        with self.assertRaises(FileExistsError): S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE)

    def test_two_evidenced_repairs_then_budget_exhausted(self):
        first = self.previous(1); self.select(2); value,repair = self.repair(first)
        second = S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:True)
        self.assertEqual(second['automatic_apps'],1)
        prior = self.previous(2); self.select(3); value,repair = self.repair(prior)
        third = S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:True)
        self.assertEqual(third['automatic_apps'],2)
        with self.assertRaises(ValueError): S.budget_for_attempt(self.output/'attempt_04',S.CASE)

    def test_success_or_live_previous_tree_blocks_even_with_remaining_budget(self):
        previous = self.previous(1,success=True); self.select(2); value,repair = self.repair(previous)
        with self.assertRaisesRegex(ValueError,'complete pass'):
            S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:True)
        row = json.loads((previous/'supervisor_result.json').read_text()); row['integration_runtime_pass']=False; row['classification']=S.FAIL_LABEL
        S.write_json(previous/'supervisor_result.json',row)
        with self.assertRaisesRegex(ValueError,'still alive'):
            S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:False)

    def test_unproven_or_unchanged_rerun_denied(self):
        previous = self.previous(1); self.select(2); value = self.preflight()
        with self.assertRaisesRegex(ValueError,'specific cause'):
            S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,pid_exited=lambda pid:True)
        value,repair = self.repair(previous)
        value['code_sha256']=json.loads((previous/'preflight.json').read_text())['code_sha256']
        with self.assertRaisesRegex(ValueError,'unchanged reruns'):
            S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:True)

    def test_retry_cannot_refreeze_changed_physics_contract(self):
        self.previous(1); self.select(2)
        self.profile.write_text('unauthorized altered profile\n',encoding='utf-8'); self.preflight()
        with self.assertRaisesRegex(ValueError,'original physics/business'): S.shared_preflight()

    def test_each_attempt_freezes_changed_code_and_passing_CPU_bytes(self):
        self.preflight(); S.shared_preflight()
        self.code.write_text('unfrozen edit\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'bytes changed'): S.shared_preflight()
        self.preflight(); self.cpu.write_text('changed evidence\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'bytes changed'): S.shared_preflight()

    def test_full_fourteen_sensor_contract_allows_nested_body_paths(self):
        result = S.contact_runtime_checks(contact_entry())
        self.assertTrue(result['complete']); self.assertEqual(result['sensor_count'],14)
        self.assertEqual(result['passed_actual_steps'],9000)

    def test_partial_second_robot_coverage_is_not_complete(self):
        entry = contact_entry()
        entry['instance_setup'][1]['contact_summary']['agv']['diagnostics']['advance_pass_count']-=1
        result=S.contact_runtime_checks(entry)
        self.assertFalse(result['complete']); self.assertEqual(result['passed_actual_steps'],8999)

    def test_real_stale_invalid_force_or_identity_cannot_be_overridden_by_exit_zero(self):
        mutations = [lambda s:s['diagnostics'].update(first_failure={'failed_condition':'time'}),
            lambda s:s['diagnostics']['last_sample']['checks'].update(time=False),
            lambda s:s['diagnostics'].update(max_force_n=.101),
            lambda s:s['diagnostics']['last_sample']['current'].update(dtype='float16'),
            lambda s:s.update(body_path='/World/CR12_0/other'),
            lambda s:s['diagnostics']['last_sample'].update(generation='wrong'),
            lambda s:s['diagnostics']['last_sample']['checks'].update(force_finite=False)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                entry=contact_entry(); mutation(entry['instance_setup'][0]['contact_summary']['agv'])
                self.assertFalse(S.contact_runtime_checks(entry)['complete'])

    def test_missing_boundary_or_shadow_read_is_not_fabricated(self):
        entry=contact_entry(); diag=entry['instance_setup'][1]['contact_summary']['link_6']['diagnostics']
        diag['boundary_samples']['64']=[]
        self.assertFalse(S.contact_runtime_checks(entry)['complete'])
        entry=contact_entry(); entry['instance_setup'][0]['contact_summary']['agv']['diagnostics']['first_shadow_disagreements']={}
        self.assertFalse(S.contact_runtime_checks(entry)['complete'])

    def test_internal_business_fail_stays_fail_with_valid_contact_and_natural_exit(self):
        pre=self.preflight(); entry=contact_entry()
        result=dict(integration_runtime_pass=False,process_exit_pass=True,
            completion_checks={'terminal_transport':False,'work_and_exit':False},budget_before={})
        S.extend_result(entry,result,pre)
        self.assertEqual(result['validation_layers']['CONTACT_RUNTIME_FRESHNESS'],'PASS')
        self.assertFalse(result['integration_runtime_pass'])
        self.assertEqual(result['classification'],S.FAIL_LABEL)

    def test_offline_reanalysis_is_new_output_preserves_raw_failure_and_stops_extra_App_after_pass(self):
        attempt=self.previous(1); self.preflight()
        S.write_json(attempt/'result.json',{'failures':[{'category':'forbidden_contact'}], 'completed_physics_steps':3842})
        original={p.name:S.sha256(p) for p in attempt.iterdir() if p.is_file()}
        out=attempt/'reanalysis_tool_fix.json'
        S.reanalyze(attempt,out)
        self.assertTrue(out.is_file()); self.assertFalse(json.loads(out.read_text())['integration_runtime_pass'])
        self.assertEqual(original,{name:S.sha256(attempt/name) for name in original})
        with self.assertRaises(ValueError): S.reanalyze(attempt,out)
        S.write_json(attempt/'reanalysis_verified_pass.json',{'integration_runtime_pass':True})
        self.select(2); value,repair=self.repair(attempt)
        with self.assertRaisesRegex(ValueError,'offline pass'):
            S.budget_for_attempt(S._ACTIVE_ATTEMPT,S.CASE,preflight=value,repair=repair,pid_exited=lambda pid:True)

    def test_zero_step_App_attempt_counts_and_prePopen_only_does_not(self):
        self.assertTrue(S.app_counted({'stage_names':['app_constructor_begin']}))
        self.assertTrue(S.app_counted({'stage_names':[], 'conda_pid':42,'process_resumed':True}))
        self.assertFalse(S.app_counted({'stage_names':[],'conda_pid':None}))

    def test_final_output_never_publishes_old_business_pass_before_contact_check(self):
        pre=self.preflight(); attempt=S._ACTIVE_ATTEMPT; attempt.mkdir()
        S.write_json(attempt/'preflight.json',pre)
        result={}
        def old_finish(entry,result,attempt,*unused):
            result.update(integration_runtime_pass=True,classification=S.old.PASS_LABEL,
                completion_checks={'work_and_exit':True,'terminal_transport':True},process_exit_pass=True)
            S.old.write_json(attempt/'supervisor_result.json',result)
            self.assertFalse((attempt/'supervisor_result.json').exists())
        with patch.object(S,'_old_finish',old_finish):
            S.finish_result({},result,attempt,{},None,None)
        final=json.loads((attempt/'supervisor_result.json').read_text())
        self.assertFalse(final['integration_runtime_pass']); self.assertEqual(final['classification'],S.FAIL_LABEL)

    def test_final_analysis_failure_is_saved_without_replacing_runtime_facts(self):
        pre=self.preflight(); attempt=S._ACTIVE_ATTEMPT; attempt.mkdir()
        S.write_json(attempt/'preflight.json',pre)
        result={'failure_events':[{'category':'native_failure'}],'process_exit_pass':False}
        with patch.object(S,'_old_finish',side_effect=KeyError('missing output field')):
            S.finish_result({},result,attempt,{},None,None)
        final=json.loads((attempt/'supervisor_result.json').read_text())
        self.assertEqual(final['failure_events'],result['failure_events'])
        self.assertFalse(final['integration_runtime_pass']); self.assertTrue(final['supervisor_errors'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
