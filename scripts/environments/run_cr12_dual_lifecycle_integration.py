"""One bounded fixed E1/M2/N4 case; no policy, device, or simulator at import."""
from __future__ import annotations

import hashlib

from run_cr12_single_view_capture import main as capture_main

CASE = 'dual_normal_staggered'
PASS = 'CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PASS'
STAGGER_TICKS = 72


def instance_specs():
    """Independent expected transforms; never derive placement from native actual."""
    return tuple(dict(robot_id=r, agent_id=f'cr12_{r}', prim_path=f'/World/CR12_{r}',
        expected_root_pose=[[1., 0., 0., 0.], [0., 1., 0., 2.*r],
                            [0., 0., 1., .053], [0., 0., 0., 1.]],
        fixture_path=f'/World/CameraInterfaceFixture_R{r}', product_name=f'CR12_R{r}_Capture',
        camera_name=f'cr12_r{r}_camera', observer_name=f'cr12.r{r}.independent_completion') for r in (0, 1))


def configure_parser(parser):
    parser.add_argument('--integration-case', choices=(CASE,), required=True)


def validate_case(args):
    if args.integration_case != CASE or args.manual_check:
        raise ValueError('Only the fixed dual normal case is admitted; no manual mode')


def next_proposals(host, publication):
    """Schedule new proposals at OPEN; executing columns retain their real task."""
    from _cr12_lifecycle_host import TaskLifecycleState, RobotLifecycleState
    state = publication.lifecycle_state
    raw, has_new = [4, 4], False
    second = next((r for r in host.claims if r['robot_id'] == 0 and r['task_id'] == 1), None)
    step = host.session.current_state()['step']
    for robot_id in (0, 1):
        context = host.contexts[robot_id]
        if context.runner is not None:
            binding = context.runner.binding
            if (int(state.ownership[0, binding.task_id]) != robot_id
                    or int(state.robot_state[0, robot_id]) != int(RobotLifecycleState.EXECUTING)):
                raise RuntimeError('Live request differs from current authority ownership/state')
            raw[robot_id] = binding.task_id
            continue
        available = [task for task in (2*robot_id, 2*robot_id+1)
                     if int(state.task_state[0, task]) == int(TaskLifecycleState.AVAILABLE)]
        if not available:
            continue
        task = available[0]
        if task == 3 and (second is None or step-second['global_start_step'] < STAGGER_TICKS):
            continue
        raw[robot_id], has_new = task, True
    if not has_new:
        return None
    return raw, [task if task != 4 else -1 for task in raw]


def coverage_complete(parallel):
    return bool(parallel.get('simultaneous_actual_motion_ticks', 0) > 0
                and parallel.get('mixed_stage_observed') is True and parallel.get('off_a_fresh_b'))


def run_dual(args, app, recorder, resources, expected, camera_config):
    from _cr12_lifecycle_host import (CR12IntegrationHost, EventProfileSynchronousRuntimeCoordinator,
        _compose_event_assignment_runtime_facade, publication_summary)
    from _cr12_runtime_support import DriveCheckError, _clock
    from run_cr12_lifecycle_integration import historical_summary
    from run_cr12_single_view_capture import verify_final_capture_scene, phase_saved
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import (
        build_assignment_event_profile_schema_v2_descriptor)
    host = CR12IntegrationHost(args, app, recorder, resources, expected, camera_config,
                               instance_specs=instance_specs())
    resources['integration_host'] = host
    layers = recorder.result['validation_layers'] = {
        'SETUP_AND_MAPPING': 'NOT_REACHED', 'BUSINESS_EXECUTION': 'NOT_REACHED',
        'PARALLEL_AND_PRODUCT_ISOLATION': 'NOT_REACHED', 'TERMINAL_AND_SHUTDOWN': 'NOT_REACHED'}
    recorder.result.update(integration_case=CASE, case_work_pass=False,
        fixed_case={'stagger_ticks': STAGGER_TICKS, 'dt': 1/120, 'decimation': 12,
                    'horizon': 420, 'instance_specs': instance_specs()})
    runtime = EventProfileSynchronousRuntimeCoordinator(environment=host,
        current_read_port=host.domain.current_read_port, production_claim_port=host.domain.production_claim_port,
        physical_step_admission_port=host.domain.physical_step_admission_port,
        standalone_reset_admission_port=host.domain.standalone_reset_admission_port,
        terminal_consumer_port=host.domain.terminal_consumer_port, fence_read_port=host.domain.interstep_fence_read_port)
    facade = _compose_event_assignment_runtime_facade(resolved_assignment_profile=host.profile,
                                                     runtime_domain=host.domain, synchronous_runtime=runtime)
    resources['integration_facade'] = facade
    try:
        facade.reset()
        layers['SETUP_AND_MAPPING'] = 'PASS'
        descriptor = build_assignment_event_profile_schema_v2_descriptor(scale_contract=host.scale)
        schema = {key: descriptor[key+'_schema']['dimension'] for key in ('actor', 'critic')}
        if schema != {'actor': 145, 'critic': 143}:
            raise DriveCheckError('schema', 'Actual fixed-scale builder dimensions differ', actual=schema)
        recorder.result['schema_dimensions'] = schema
        while not host.finished:
            current = facade.read_current()
            proposal = next_proposals(host, current)
            if proposal is None:
                receipt = facade.step_without_new_claim(action_builder=host.bind_effective_assignment)
            else:
                raw, decoded = proposal
                problem = host.assignment_problem()
                decision = facade.capture_proposal_decision(feasible_mask=problem['feasible_mask'],
                                                            cost_matrix=problem['cost_matrix'])
                recorder.result.setdefault('proposal_batches', []).append({
                    'global_start_step': host.session.current_state()['step'], 'raw': raw, 'decoded': decoded})
                receipt = facade.resolve_and_step_proposals(raw_action_ids=host.i([raw]),
                    decoded_proposal=host.i([decoded]), decision=decision, action_builder=host.bind_effective_assignment)
            if receipt.terminal_historical_payload:
                if not host.finished or len(receipt.terminal_historical_payload) != 1:
                    raise DriveCheckError('terminal_history', 'Only one environment terminal row is permitted')
                recorder.result['terminal_history'] = [historical_summary(row) for row in receipt.terminal_historical_payload]
        pending = host.domain.terminal_consumer_port.capture_pending_terminal_artifacts()
        recorder.result['terminal_transport'] = {'historical_rows': len(recorder.result.get('terminal_history', [])),
            'pending_slots_after_facade': len(pending), 'ack_completed': not pending}
        recorder.result['terminal_before_reset'] = host.terminal_before_reset
        recorder.result['current_after_reset'] = publication_summary(facade.read_current())
        history = recorder.result['terminal_history'][0]
        by_task = {r['task_id']: r for r in host.requests}
        if (pending or len(host.requests) != 4 or sorted(by_task) != [0, 1, 2, 3]
            or len(host.deliveries) != 4 or len(host.claims) != 4
            or any(r['outcome'] != 'completed' or not r['acquired'] for r in host.deliveries)
            or history['completion_count'] != [2, 2]
            or history['coverage_after_transition'] != [True]*4
            or any(any(row) for row in history['updated_failed_pairs'])
            or history['sidecar_critic_dimension'] != 143 or history['sidecar_audit_dimension'] != 143
            or not history['terminated'] or history['truncated']):
            raise DriveCheckError('case_authority_outcome', 'Four-task global authority/terminal outcome differs')
        for task, row in by_task.items():
            if (row['robot_id'] != task//2 or not row['request']['acquired']
                or not row['request']['off_confirmed'] or not row['retired_after_receipt']):
                raise DriveCheckError('case_attribution', 'Task/capture/retirement attribution differs', task=task)
        start1 = next(r['global_start_step'] for r in host.claims if r['task_id'] == 1)
        start3 = next(r['global_start_step'] for r in host.claims if r['task_id'] == 3)
        if start3-start1 < STAGGER_TICKS:
            raise DriveCheckError('stagger', 'Second robot was admitted before the fixed legal stagger')
        recorder.result['stagger_actual'] = {'task1_start_step': start1, 'task3_start_step': start3,
                                            'delta_ticks': start3-start1}
        custody = [r.pending.custody for r in host.adapter.history if r.pending.custody is not None]
        recorder.result['custody_after_rebuild'] = {'count': len(custody),
            'all_readonly': all(not c.rgba.flags.writeable for c in custody),
            'rgba_sha256': [hashlib.sha256(c.rgba.tobytes()).hexdigest() for c in custody]}
        if len(custody) != 4 or not recorder.result['custody_after_rebuild']['all_readonly']:
            raise DriveCheckError('data_custody', 'Four immutable captures must survive retirement/rebuild')
        layers['BUSINESS_EXECUTION'] = 'PASS'
        # Finish ALL native reads before the first product detach/release.
        before_final = _clock(host.scene['sim'])
        for c in host._ordered():
            verify_final_capture_scene(c.scene, expected, c.recorder, c.resources,
                c.run['initial_parameters'], c.resources['last_integration_request'],
                total_steps=recorder.result['completed_physics_steps'])
        if _clock(host.scene['sim']) != before_final:
            raise DriveCheckError('final_clock', 'Final parameter checks advanced physics')
        backends, releases = {}, {}
        for c in host._ordered():
            release = c.capture.release()
            c.recorder.result.update(camera_release=release, camera_resources_released=True,
                                     resource_release_before_stop=True)
            c.recorder.save()
            backends[str(c.robot_id)] = c.capture.summary()
            releases[str(c.robot_id)] = release
            identities = [r['identity'] for r in host.identities if r['robot_id'] == c.robot_id]
            counts = backends[str(c.robot_id)]['lifecycle']
            if (len(identities) != 3 or any(row != identities[0] for row in identities)
                or any(counts.get(k) != n for k, n in (
                    ('prepare_calls', 1), ('initialize_calls', 1), ('begin_calls', 2),
                    ('off_confirmed_count', 2), ('retire_effective_count', 2), ('release_effective_count', 1)))):
                raise DriveCheckError('resource_continuity', 'Per-robot resources changed or counts differ', robot_id=c.robot_id)
        recorder.result.update(camera_backends_final=backends, camera_releases=releases,
            device_identity_samples=host.identities, device_identity_unchanged=True,
            camera_resources_released=True, resource_release_before_stop=True,
            host_summary=host.summary(), requests=host.requests, authority_claims=host.claims,
            authority_deliveries=host.deliveries, cross_robot_geometry=host.cross_summary,
            parallel_evidence=host.parallel)
        if any(release.get('complete') is not True or release.get('errors') != [] for release in releases.values()):
            raise DriveCheckError('resource_release', 'An owned backend did not release completely', releases=releases)
        # Artifact delivery is required for this run's handoff, but never rewrites C/acquired.
        if any(not row['artifact_saved'] or not row['metadata_saved'] for row in host.requests):
            raise DriveCheckError('artifact_delivery', 'Business data exists but four-file handoff is incomplete')
        recorder.result['artifact_delivery_pass'] = True
        covered = coverage_complete(host.parallel)
        layers['PARALLEL_AND_PRODUCT_ISOLATION'] = 'PASS' if covered else 'COVERAGE_INCOMPLETE'
        layers['TERMINAL_AND_SHUTDOWN'] = 'TERMINAL_PASS_PENDING_PROCESS_EXIT'
        recorder.result.update(case_work_pass=covered, business_execution_pass=True,
            coverage_complete=covered, case_classification=PASS if covered else 'COVERAGE_INCOMPLETE')
        phase_saved(recorder, 'integration_case_completed', case=CASE,
                    transitions=host.total_transitions, requests=4, coverage_complete=covered)
    except BaseException:
        recorder.result.update(requests=host.requests, authority_claims=host.claims,
            authority_deliveries=host.deliveries, parallel_evidence=host.parallel,
            cross_robot_geometry=host.cross_summary,
            acknowledged_receipts_on_failure=[r.summary() for r in host.adapter.history])
        # Preserve existing backend copies, including a frame received before a
        # different robot's guard failed. Never promote unaccepted raw to acquired.
        from _cr12_camera_capture import save_rgba_png
        retained = recorder.result['retained_on_failure'] = {}
        for c in host.contexts.values():
            try:
                peek = c.capture.peek_retained_snapshot()
                row = {k: v for k, v in peek.items() if k != 'snapshot'}
                retained[str(c.robot_id)] = row
                if c.runner is not None:
                    c.recorder.result['active_request_diagnostic'] = {
                        'record': c.runner.record, 'request': c.runner.request.summary()}
                if peek['snapshot'] is not None:
                    directory = args.output_dir / f'robot_{c.robot_id}'
                    directory.mkdir(parents=True, exist_ok=True)
                    path = directory / 'retained_on_failure.png'
                    row['artifact'] = save_rgba_png(path, peek['snapshot']['rgba'])
                    row['artifact_path'] = str(path)
                    row['metadata'] = peek['snapshot']['metadata']
                    row['status_note'] = 'backend retained copy; fresh/FSM acquired/authority status remain separate'
                c.recorder.save()
            except Exception as preserve_error:
                recorder.secondary(preserve_error, f'robot_{c.robot_id}_retained_failure_data')
        try:
            if host.session is not None: recorder.result['host_summary'] = host.summary()
            recorder.save()
        except Exception:
            pass
        raise


def main():
    return capture_main(capture_runner=run_dual, configure_parser=configure_parser,
        pre_app_validator=validate_case, success_label=PASS, entry_source=__file__,
        completion_label=lambda result: result['case_classification'])


if __name__ == '__main__':
    raise SystemExit(main())
