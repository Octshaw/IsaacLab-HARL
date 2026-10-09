"""Fixed shared task 0: A cancel/clear/release, then B fresh capture; one real host."""
from __future__ import annotations

import hashlib
import numpy as np
import _cr12_shared_task_profile as shared
from run_cr12_single_view_capture import main as capture_main

CASE = shared.CASE
PASS = 'CR12_SHARED_TASK_HANDOVER_INTEGRATION_PASS'
LAYERS = ('IMPLEMENTATION_CPU', 'STARTUP_AND_INSTANCE_SETUP', 'NONZERO_SETUP_HOLD',
          'A_APPROACH_AND_CANCEL_OFF', 'A_BOUND_RETREAT_AND_CLEAR_RELEASE',
          'B_SHARED_TASK_CAPTURE', 'AUTHORITY_TERMINAL_AND_SHUTDOWN')


def instance_specs():
    return tuple(dict(robot_id=r, agent_id=f'cr12_{r}', prim_path=f'/World/CR12_{r}',
        expected_root_pose=shared.root_pose(r).tolist(), fixture_path=shared.SHARED_FIXTURE_PATH,
        product_name=f'CR12_R{r}_Capture', camera_name=f'cr12_r{r}_camera',
        observer_name=f'cr12.r{r}.independent_completion') for r in (0, 1))


def configure_parser(parser):
    parser.add_argument('--integration-case', choices=(CASE,), required=True)


def validate_case(args):
    if args.integration_case != CASE or args.manual_check:
        raise ValueError('Only the reviewed fixed shared handover case is authorized')
    args.motion_profile = shared.PROFILE_NAME
    args.physics_steps = shared.TOTAL_CONTROLLED_MAX_STEPS


def next_proposals(host, publication):
    from _cr12_lifecycle_host import TaskLifecycleState, RobotLifecycleState
    state = publication.lifecycle_state
    active = [c for c in host._ordered() if c.runner is not None]
    if active:
        if len(active) != 1:
            raise RuntimeError('Two robots cannot enter the unique shared target')
        c = active[0]
        if (int(state.ownership[0, 0]) != c.robot_id
                or int(state.robot_state[0, c.robot_id]) != int(RobotLifecycleState.EXECUTING)
                or c.runner.binding.task_id != 0):
            raise RuntimeError('Bound execution differs from actual task ownership')
        return None
    if int(state.task_state[0, 0]) != int(TaskLifecycleState.AVAILABLE) or int(state.ownership[0, 0]) != -1:
        raise RuntimeError('A new shared claim requires the actual AVAILABLE task')
    if not host.claims:
        return [0, 1], [0, -1]
    host.check_shared_successor_ready()
    return [1, 0], [-1, 0]


def update_layers(host, layers):
    if len(host.contexts) == 2:
        layers['STARTUP_AND_INSTANCE_SETUP'] = 'PASS'
    setup = host.shared_handover.get('setup') or {}
    if setup.get('status') == 'SETUP_HOLD_READY':
        layers['NONZERO_SETUP_HOLD'] = 'PASS'
    a = host.contexts.get(0)
    record = a.runner.record if a is not None and a.runner is not None else (
        next((row for row in host.requests if row['robot_id'] == 0), None))
    if record:
        request = a.runner.request.summary() if a.runner is not None else record['request']
        cancelled = a.runner.cancel_issued if a.runner is not None else record.get('cancel_issued')
        if (request.get('off_confirmed') and not request.get('acquired') and cancelled):
            layers['A_APPROACH_AND_CANCEL_OFF'] = 'PASS'
    if (len(host.deliveries) >= 1 and host.deliveries[0]['outcome'] == 'cancelled'
            and any(row.get('retired_after_receipt') and row['robot_id'] == 0 for row in host.requests)):
        layers['A_BOUND_RETREAT_AND_CLEAR_RELEASE'] = 'PASS'
    if any(row['robot_id'] == 1 and row['request'].get('acquired')
           and row['request'].get('off_confirmed') and row.get('retired_after_receipt') for row in host.requests):
        layers['B_SHARED_TASK_CAPTURE'] = 'PASS'


def check_business(host, history, pending):
    from _cr12_runtime_support import DriveCheckError
    rows = {row['robot_id']: row for row in host.requests}
    if (pending or len(host.claims) != 2 or len(host.deliveries) != 2 or set(rows) != {0, 1}
            or [r['robot_id'] for r in host.claims] != [0, 1]
            or any(r['task_id'] != 0 for r in host.claims)
            or [r['outcome'] for r in host.deliveries] != ['cancelled', 'completed']
            or [r['acquired'] for r in host.deliveries] != [False, True]
            or history['completion_count'] != [0, 1]
            or history['coverage_after_transition'] != [True]
            or any(any(row) for row in history['updated_failed_pairs'])
            or history['sidecar_critic_dimension'] != 71 or history['sidecar_audit_dimension'] != 71
            or not history['terminated'] or history['truncated']):
        raise DriveCheckError('shared_authority_outcome', 'Real shared task attribution/terminal differs')
    for row in (*host.claims, *host.requests):
        target = row.get('target_matrix', row.get('scanner_task_target'))
        if not np.array_equal(np.asarray(target), shared.scanner_target()):
            raise DriveCheckError('shared_target_changed', 'The one task matrix changed across owners')
    a, b = rows[0], rows[1]
    if (a['request']['acquired'] or a.get('artifact_saved') or not a['cancel_issued']
            or not a['request']['off_confirmed'] or not a['retired_after_receipt']
            or not b['request']['acquired'] or not b['request']['off_confirmed']
            or not b['retired_after_receipt'] or not b['artifact_saved']
            or not all(row['metadata_saved'] for row in rows.values())):
        raise DriveCheckError('shared_capture_attribution', 'No-data A / fresh B result or artifact differs')
    clear = host.shared_handover['clear_release']
    if (clear is None or not a.get('clear_evidence')
            or clear['pending_step'] > a['receipt_then_retire_step']
            or a['receipt_then_retire_step'] > host.claims[1]['global_start_step']):
        raise DriveCheckError('shared_clear_order', 'Actual clear/release/next claim ordering differs')
    summary = host.summary()
    if (summary['global_physics_ticks'] != host.setup_ticks + shared.BLOCK_STEPS*host.total_transitions
            or summary['global_physics_ticks'] > shared.TOTAL_CONTROLLED_MAX_STEPS
            or summary['render_count'] != summary['global_physics_ticks']//shared.RENDER_INTERVAL
            or host.total_transitions > shared.HOST_MAX_TRANSITIONS):
        raise DriveCheckError('shared_clock_budget', 'Setup/task/render counts or budgets differ')
    return rows


def preserve_failure(host, args, recorder):
    """Preserve real retained data; never manufacture or erase a cancelled image."""
    from _cr12_camera_capture import save_rgba_png
    retained = recorder.result.setdefault('retained_on_failure', {})
    for c in host.contexts.values():
        try:
            peek = c.capture.peek_retained_snapshot()
            row = retained[str(c.robot_id)] = {k: v for k, v in peek.items() if k != 'snapshot'}
            if c.runner is not None:
                c.recorder.result['active_request_diagnostic'] = {
                    'record': c.runner.record, 'request': c.runner.request.summary()}
            if peek['snapshot'] is not None:
                path = args.output_dir / f'robot_{c.robot_id}' / 'retained_on_failure.png'
                path.parent.mkdir(parents=True, exist_ok=True)
                row.update(artifact=save_rgba_png(path, peek['snapshot']['rgba']),
                           artifact_path=str(path), metadata=peek['snapshot']['metadata'],
                           note='retained raw, FSM acquired and authority completion are separate')
        except Exception as exc:
            recorder.secondary(exc, f'shared_preserve_robot_{c.robot_id}')


def run_shared(args, app, recorder, resources, expected, camera_config):
    from _cr12_lifecycle_host import (CR12IntegrationHost, EventProfileSynchronousRuntimeCoordinator,
        _compose_event_assignment_runtime_facade, publication_summary)
    from _cr12_runtime_support import DriveCheckError, _clock
    from run_cr12_lifecycle_integration import historical_summary
    from run_cr12_single_view_capture import verify_final_capture_scene, phase_saved, release_capture_with_record
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import (
        build_assignment_event_profile_schema_v2_descriptor)
    host = CR12IntegrationHost(args, app, recorder, resources, expected, camera_config,
                              instance_specs=instance_specs())
    resources['integration_host'] = host
    layers = recorder.result['validation_layers'] = dict.fromkeys(LAYERS, 'NOT_REACHED')
    recorder.result.update(integration_case=CASE, fixed_case=shared.record(), case_work_pass=False)
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
        update_layers(host, layers)
        descriptor = build_assignment_event_profile_schema_v2_descriptor(scale_contract=host.scale)
        schema = {key: descriptor[key+'_schema']['dimension'] for key in ('actor', 'critic')}
        recorder.result['schema_dimensions'] = schema
        if schema != {'actor': 73, 'critic': 71}:
            raise DriveCheckError('shared_schema', 'Actual fixed M2/N1 dimensions differ', actual=schema)
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
            update_layers(host, layers)
            if receipt.terminal_historical_payload:
                if not host.finished or len(receipt.terminal_historical_payload) != 1:
                    raise DriveCheckError('terminal_history', 'Only one terminal shared-task row is permitted')
                recorder.result['terminal_history'] = [historical_summary(row) for row in receipt.terminal_historical_payload]
        pending = host.domain.terminal_consumer_port.capture_pending_terminal_artifacts()
        recorder.result.update(terminal_before_reset=host.terminal_before_reset,
            current_after_reset=publication_summary(facade.read_current()),
            terminal_transport={'historical_rows': len(recorder.result.get('terminal_history', [])),
                                'pending_slots_after_facade': len(pending), 'ack_completed': not pending})
        rows = check_business(host, recorder.result['terminal_history'][0], pending)
        custody = [receipt.pending.custody for receipt in host.adapter.history if receipt.pending.custody is not None]
        if len(custody) != 1 or custody[0].rgba.flags.writeable:
            raise DriveCheckError('shared_custody', 'Exactly one immutable B capture must survive rebuild')
        recorder.result['custody_after_rebuild'] = {'count': 1, 'all_readonly': True,
            'rgba_sha256': [hashlib.sha256(custody[0].rgba.tobytes()).hexdigest()]}
        before = _clock(host.scene['sim'])
        for c in host._ordered():
            verify_final_capture_scene(c.scene, expected, c.recorder, c.resources,
                c.run['initial_parameters'], c.resources['last_integration_request'],
                total_steps=recorder.result['completed_physics_steps'])
        if _clock(host.scene['sim']) != before:
            raise DriveCheckError('final_clock', 'Final native reads advanced physics')
        backends, releases = {}, {}
        for c in host._ordered():
            release = release_capture_with_record(c.capture, c.recorder)
            c.recorder.result.update(camera_release=release, camera_resources_released=True,
                                    resource_release_before_stop=True)
            backend = c.capture.summary()
            counts = backend['lifecycle']
            identities = [row['identity'] for row in host.identities if row['robot_id'] == c.robot_id]
            if (len(identities) != 2 or identities[0] != identities[1]
                    or any(counts.get(k) != n for k, n in (('prepare_calls', 1), ('initialize_calls', 1),
                        ('begin_calls', 1), ('off_confirmed_count', 1), ('retire_effective_count', 1),
                        ('release_effective_count', 1)))
                    or release.get('complete') is not True or release.get('errors') != []):
                raise DriveCheckError('shared_resources', 'Independent camera lifetime/one-request counts differ',
                                      robot_id=c.robot_id)
            backends[str(c.robot_id)], releases[str(c.robot_id)] = backend, release
        recorder.result.update(camera_backends_final=backends, camera_releases=releases,
            device_identity_samples=host.identities, device_identity_unchanged=True,
            camera_resources_released=True, resource_release_before_stop=True,
            host_summary=host.summary(), requests=host.requests, authority_claims=host.claims,
            authority_deliveries=host.deliveries, shared_handover=host.shared_handover,
            cross_robot_geometry=host.cross_summary, artifact_delivery_pass=True,
            case_work_pass=True, business_execution_pass=True, case_classification=PASS)
        layers['AUTHORITY_TERMINAL_AND_SHUTDOWN'] = 'TERMINAL_PASS_PENDING_PROCESS_EXIT'
        phase_saved(recorder, 'integration_case_completed', case=CASE,
                    transitions=host.total_transitions, requests=2, coverage_complete=True)
    except BaseException as exc:
        update_layers(host, layers)
        category = getattr(exc, 'category', '')
        recorder.result['case_classification'] = 'NOT_HIT' if category == 'cancel_not_hit' else PASS.removesuffix('_PASS')+'_FAIL'
        recorder.result.update(requests=host.requests, authority_claims=host.claims,
            authority_deliveries=host.deliveries, shared_handover=host.shared_handover,
            cross_robot_geometry=host.cross_summary,
            acknowledged_receipts_on_failure=[row.summary() for row in host.adapter.history])
        preserve_failure(host, args, recorder)
        if host.session is not None: recorder.result['host_summary'] = host.summary()
        recorder.save()
        raise


def main():
    return capture_main(capture_runner=run_shared, configure_parser=configure_parser,
        pre_app_validator=validate_case, success_label=PASS, entry_source=__file__,
        completion_label=lambda result: result['case_classification'])


if __name__ == '__main__':
    raise SystemExit(main())
