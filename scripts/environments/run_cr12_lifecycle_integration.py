"""Private bounded CR12 execution-to-lifecycle integration, never a policy entry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from run_cr12_single_view_capture import main as capture_main

CASES = ('normal', 'cancel_then_reclaim')


def configure_parser(parser):
    parser.add_argument('--integration-case', choices=CASES, required=True)
    parser.add_argument('--normal-result', type=Path)


def validate_case_prerequisite(args):
    if args.manual_check:
        raise ValueError('This bounded authority entry does not provide a manual demo mode')
    if args.integration_case == 'cancel_then_reclaim':
        if args.normal_result is None:
            raise ValueError('A naturally exited NORMAL_CASE_PASS supervisor result is required')
        path = args.normal_result.resolve(strict=True)
        if path.name != 'supervisor_result.json' or path.parent.parent != args.output_dir.parent:
            raise ValueError('Normal evidence must come from a prior attempt in this task directory')
        evidence = json.loads(path.read_text(encoding='utf-8'))
        if (evidence.get('case') != 'normal' or evidence.get('classification') != 'NORMAL_CASE_PASS'
                or evidence.get('integration_runtime_pass') is not True
                or evidence.get('process_exit_pass') is not True or evidence.get('timed_out') is not False):
            raise ValueError('Normal runtime did not pass with natural owned-process exit')


def historical_summary(row):
    sidecar = row.optional_sidecar
    if sidecar is None:
        raise RuntimeError('Real pre-reset physical critic sidecar is mandatory')
    return dict(env_id=row.env_id, episode_generation=row.episode_generation,
        transition_generation=row.transition_generation, termination_reason=row.termination_reason,
        terminated=row.terminated, truncated=row.truncated, facts_consume_token=row.facts_consume_token,
        authority_receipt_id=row.authority_receipt_id,
        coverage_after_transition=row.coverage_after_transition.cpu().tolist(),
        completed_tasks=row.completed_tasks.cpu().tolist(), completion_count=row.completion_count.cpu().tolist(),
        updated_task_state=row.updated_task_state.cpu().tolist(),
        updated_ownership=row.updated_ownership.cpu().tolist(),
        updated_failed_pairs=row.updated_failed_pairs.cpu().tolist(),
        sidecar_critic_dimension=sidecar.critic_dimension,
        sidecar_audit_dimension=sidecar.terminal_audit_projection.semantic_evidence.numel(),
        sidecar_bootstrap_present=sidecar.bootstrap_critic_obs is not None,
        sidecar_bootstrap_projection_valid=sidecar.bootstrap_projection_valid)


def run_integration(args, app, recorder, resources, expected, camera_config):
    from _cr12_lifecycle_host import (CR12IntegrationHost, EventProfileSynchronousRuntimeCoordinator,
        _compose_event_assignment_runtime_facade, publication_summary, TaskLifecycleState)
    import run_cr12_single_view_capture as shared
    from _cr12_runtime_support import DriveCheckError
    host = CR12IntegrationHost(args, app, recorder, resources, expected, camera_config)
    resources['integration_host'] = host
    recorder.result['integration_case'] = args.integration_case
    recorder.result['case_work_pass'] = False
    runtime = EventProfileSynchronousRuntimeCoordinator(
        environment=host, current_read_port=host.domain.current_read_port,
        production_claim_port=host.domain.production_claim_port,
        physical_step_admission_port=host.domain.physical_step_admission_port,
        standalone_reset_admission_port=host.domain.standalone_reset_admission_port,
        terminal_consumer_port=host.domain.terminal_consumer_port,
        fence_read_port=host.domain.interstep_fence_read_port)
    facade = _compose_event_assignment_runtime_facade(resolved_assignment_profile=host.profile,
                        runtime_domain=host.domain, synchronous_runtime=runtime)
    resources['integration_facade'] = facade
    try:
        facade.reset()
        while not host.finished:
            current = facade.read_current()
            state = current.lifecycle_state
            if host.runner is None:
                # A deterministic proposal, never a direct effective assignment.
                available = [i for i in (0, 1) if int(state.task_state[0, i]) == int(TaskLifecycleState.AVAILABLE)]
                if not available:
                    raise DriveCheckError('proposal_state', 'No available task before normal terminal')
                task = available[0]
                problem = host.assignment_problem()
                decision = facade.capture_proposal_decision(feasible_mask=problem['feasible_mask'],
                                                           cost_matrix=problem['cost_matrix'])
                receipt = facade.resolve_and_step_proposals(raw_action_ids=host.i([[task]]),
                    decoded_proposal=host.i([[task]]), decision=decision, action_builder=host.bind_effective_assignment)
            else:
                receipt = facade.step_without_new_claim(action_builder=host.bind_effective_assignment)
            if receipt.terminal_historical_payload:
                if not host.finished or len(receipt.terminal_historical_payload) != 1:
                    raise DriveCheckError('terminal_history', 'Unexpected terminal history count/boundary')
                recorder.result['terminal_history'] = [historical_summary(row) for row in receipt.terminal_historical_payload]
        pending = host.domain.terminal_consumer_port.capture_pending_terminal_artifacts()
        if pending:
            raise DriveCheckError('terminal_ack', 'Facade did not acknowledge all terminal artifacts')
        recorder.result['terminal_transport'] = {'historical_rows': len(recorder.result.get('terminal_history', [])),
            'pending_slots_after_facade': len(pending), 'ack_completed': not pending}
        recorder.result['terminal_before_reset'] = host.terminal_before_reset
        recorder.result['current_after_reset'] = publication_summary(facade.read_current())
        final = recorder.result['terminal_history'][0]
        expected_requests = 2 if args.integration_case == 'normal' else 3
        completions = [r for r in host.deliveries if r['outcome'] == 'completed']
        releases = [r for r in host.deliveries if r['outcome'] == 'cancelled']
        if (len(host.requests) != expected_requests or len(completions) != 2
                or len(releases) != expected_requests-2 or sum(final['completion_count']) != 2
                or final['coverage_after_transition'] != [True, True]
                or any(any(row) for row in final['updated_failed_pairs'])
                or final['sidecar_critic_dimension'] != final['sidecar_audit_dimension']):
            raise DriveCheckError('case_authority_outcome', 'Final authority attribution/count differs from this case')
        if args.integration_case == 'cancel_then_reclaim':
            first, retry = host.claims[:2]
            if first['task_id'] != 0 or retry['task_id'] != 0 or first['claim_token'] == retry['claim_token']:
                raise DriveCheckError('reclaim_identity', 'Expected same-task new production claim')
        shared.finalize_capture_scene(host.scene, expected, recorder, resources, host.run['initial_parameters'],
            resources['last_integration_request'], total_steps=recorder.result['completed_physics_steps'])
        backend = host.capture.summary()
        recorder.result['camera_backend_final'] = backend
        identities = host.identities
        lc = backend['lifecycle']
        same = all(row == identities[0] for row in identities)
        if (not same or lc['prepare_calls'] != 1 or lc['initialize_calls'] != 1
                or lc['begin_calls'] != expected_requests or lc['off_confirmed_count'] != expected_requests
                or lc['release_effective_count'] != 1):
            raise DriveCheckError('resource_continuity', 'Device resources were recreated or counts differ')
        custody = [r.pending.custody for r in host.adapter.history if r.pending.custody is not None]
        recorder.result['custody_after_rebuild'] = {
            'count': len(custody), 'all_readonly': all(not c.rgba.flags.writeable for c in custody),
            'rgba_sha256': [hashlib.sha256(c.rgba.tobytes()).hexdigest() for c in custody]}
        if len(custody) != 2 or not recorder.result['custody_after_rebuild']['all_readonly']:
            raise DriveCheckError('data_custody', 'Old result data did not survive retirement/rebuild')
        recorder.result.update(host_summary=host.summary(), requests=host.requests,
            authority_claims=host.claims, authority_deliveries=host.deliveries,
            device_identity_samples=identities, device_identity_unchanged=same,
            case_work_pass=True, case_classification=('NORMAL_CASE_PASS' if args.integration_case == 'normal'
                                                   else 'CANCEL_THEN_RECLAIM_CASE_PASS'))
        shared.phase_saved(recorder, 'integration_case_completed', case=args.integration_case,
                           transitions=host.total_transitions, requests=expected_requests)
    except BaseException:
        # Diagnostics must never replace the first execution/authority exception.
        recorder.result.update(requests=host.requests, authority_claims=host.claims,
                               authority_deliveries=host.deliveries)
        recorder.result['acknowledged_receipts_on_failure'] = [r.summary() for r in host.adapter.history]
        try:
            recorder.result['host_summary'] = None if host.session is None else host.summary()
        except Exception as exc:
            recorder.result['host_summary_error'] = f'{type(exc).__name__}: {exc}'
        capture = resources.get('capture')
        if capture is not None:
            # A Python snapshot can survive a post-render physical failure. No native reads here.
            try:
                peek = capture.peek_retained_snapshot()
                recorder.result['retained_on_failure'] = {k: v for k, v in peek.items() if k != 'snapshot'}
                if peek['snapshot'] is not None:
                    from _cr12_camera_capture import save_rgba_png
                    save_rgba_png(args.output_dir / 'retained_on_failure.png', peek['snapshot']['rgba'])
                    recorder.result['retained_on_failure']['metadata'] = peek['snapshot']['metadata']
            except Exception as exc:
                recorder.result['retained_on_failure_error'] = f'{type(exc).__name__}: {exc}'
        try:
            recorder.save()
        except Exception:
            pass  # The shared entry records the original exception and closes resources.
        raise


def main():
    return capture_main(capture_runner=run_integration, configure_parser=configure_parser,
        pre_app_validator=validate_case_prerequisite,
        success_label='CR12_EXECUTION_LIFECYCLE_CASE_PASS', entry_source=__file__)


if __name__ == '__main__':
    raise SystemExit(main())

