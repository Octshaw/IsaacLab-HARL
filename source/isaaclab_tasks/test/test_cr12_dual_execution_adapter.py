"""Fixed two-slot adapter checks with real claim/domain/authority/facade.

Only physical samples are fake.  No Kit, Isaac or CUDA calls, historical harness
imports, or repository inventories are part of this focused test fixture.
"""
from dataclasses import replace
import unittest
from unittest.mock import patch

import torch

from test_cr12_lifecycle_execution_adapter import A, D, P, S, F, C, SC, TS, DEVICE, custody, i


def physical_problem():
    return {"num_envs": 1, "num_agents": 2, "agent_names": ("cr12_0", "cr12_1"),
        "num_viewpoints": 4, "viewpoint_ids": (0, 1, 2, 3),
        "base_pos": torch.tensor([[[0., 0., 0.], [0., 2., 0.]]]), "base_yaw": torch.zeros((1, 2)),
        "scanner_pos": torch.tensor([[[0., 0., 1.], [0., 2., 1.]]]),
        "scanner_quat": torch.tensor([[[1., 0., 0., 0.]] * 2]),
        "viewpoint_pos": torch.tensor([[[.01, 0., 1.], [0., 0., 1.], [.01, 2., 1.], [0., 2., 1.]]]),
        "viewpoint_quat": torch.tensor([[[1., 0., 0., 0.]] * 4]),
        "arm_reach": torch.tensor([1.5, 1.5]), "scanner_min_range": torch.tensor([0., 0.]),
        "scanner_max_range": torch.tensor([2., 2.]), "scanner_fov_deg": torch.tensor([60., 60.]),
        "feasible_mask": torch.tensor([[[True, True, False, False], [False, False, True, True]]]),
        "cost_matrix": torch.tensor([[[.01, 0., 2., 2.], [2., 2., .01, 0.]]])}


def scale():
    return SC.build_event_policy_scale_contract_v2(M=2, N=4,
        ordered_agent_names=("cr12_0", "cr12_1"), ordered_task_ids=(0, 1, 2, 3),
        scene_env_spacing=4., sim_dt_seconds=1/120, control_decimation=12,
        episode_time_limit_seconds=42.)


class DualFakeHost:
    """CPU samples around one unmocked production lifecycle domain."""
    def __init__(self):
        self.profile = P.resolve_assignment_profile("event_gated_local_mrta", P.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        self.domain = D._EventProfileLifecycleRuntimeDomain(D._EventProfileLifecycleDomainSpec(
            self.profile, device=DEVICE, env_ids=i([0]), num_robots=2, num_tasks=4))
        self.adapter = A.Cr12ExecutionAdapter(current_read_port=self.domain.current_read_port,
            run_instance_id="dual_cpu_fixture", execution_profile="dual_m2n4")
        self.validation = self.domain.environment_admission_validation_port
        self.port = self.domain.environment_port
        self.step_count = 0
        self.modes = {}
        self.overrides = {}
        self.new_bindings = []
        self.latest = self.report = None
        self.receipts = ()
        self.before_bind = self.before_finalize = self.after_finalize = self.after_ack = None
        self.auto_retire = True
        self.captured_terminal = []
        runtime = S.EventProfileSynchronousRuntimeCoordinator(environment=self,
            current_read_port=self.domain.current_read_port, production_claim_port=self.domain.production_claim_port,
            physical_step_admission_port=self.domain.physical_step_admission_port,
            standalone_reset_admission_port=self.domain.standalone_reset_admission_port,
            terminal_consumer_port=self.domain.terminal_consumer_port, fence_read_port=self.domain.interstep_fence_read_port)
        self.facade = F._compose_event_assignment_runtime_facade(resolved_assignment_profile=self.profile,
            runtime_domain=self.domain, synchronous_runtime=runtime)
        self.facade.reset()

    def reset(self):
        self.validation.validate_reset_entry_for_active_call()
        # Host guards must run before the authority reset, not after it.
        if any(self.adapter.binding_for(r) is not None or self.adapter.pending_result(r) is not None for r in (0, 1)):
            raise RuntimeError("CPU reset with a live request")
        with self.port.episode_rebuild(selected_env_ids=i([0]),
                initial_task_state=i([[int(C.TaskLifecycleState.AVAILABLE)] * 4]),
                initial_robot_state=i([[int(C.RobotLifecycleState.NEEDS_ASSIGNMENT)] * 2]),
                initial_ownership=i([[-1] * 4])) as reset:
            reset.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        return {name: torch.zeros((1, 1)) for name in ("cr12_0", "cr12_1")}, {"physics": "CPU fixture"}

    def builder(self, environment, assignment):
        assert environment is self
        if self.before_bind:
            self.before_bind(self, assignment)
        choices = self.adapter.bind_effective_assignments(assignment)
        self.new_bindings.extend(b for b, new in choices if new)
        return tuple(b for b, _ in choices)

    def step(self, bindings):
        self.validation.validate_physical_step_entry_for_active_call()
        self.step_count += 12  # Explicit CPU fixture, not a physics call.
        boundaries = {}
        for robot, binding in enumerate(bindings):
            mode = self.modes.get(robot)
            if mode:
                self.adapter.record_pending(binding, outcome=mode, acquired=mode != "cancelled",
                    custody=None if mode == "cancelled" else custody(binding), physics_step=self.step_count - 3,
                    metadata={"cpu_fixture": True, "artifact_saved": False})
            boundary = A.ExecutionBoundaryEvidence(self.step_count,
                None if binding is None else binding.goal_id, None if binding is None else binding.capture_id,
                True, True, True, True, True, True)
            boundaries[robot] = replace(boundary, **self.overrides.get(robot, {}))
        current = self.domain.current_read_port.read_current()
        snapshot = TS.capture_pre_reset_critic_physical_snapshot_v2(assignment_problem=physical_problem(),
            episode_progress_steps=i([self.step_count // 12]), scale_contract=scale(),
            physical_problem_source="DualFakeHost CPU fixture")
        self.report = self.adapter.build_report(boundaries_by_robot=boundaries,
            coverage_before_transition=current.lifecycle_state.task_state == int(C.TaskLifecycleState.COMPLETED),
            physical_truncated=torch.zeros(1, dtype=torch.bool), time_limit_reached=torch.zeros(1, dtype=torch.bool),
            pre_reset_critic_physical_snapshot=snapshot)
        self.validation.validate_physical_finalization_for_active_call()
        if self.before_finalize:
            self.before_finalize(self)
        self.latest = self.port.finalize_execution_transition(self.report)
        if self.after_finalize:
            self.after_finalize(self)
        self.receipts = self.adapter.ack_authority_deliveries(self.latest)
        if self.after_ack:
            self.after_ack(self)
        if self.auto_retire:
            for receipt in self.receipts:
                self.adapter.retire_request(receipt.binding, receipt)
        terminated, truncated = self.latest.terminated, self.latest.truncated
        if bool((terminated | truncated).any()):
            self.captured_terminal.extend(self.domain.terminal_consumer_port.capture_pending_terminal_artifacts())
            if not all(b.off_confirmed and b.resource_healthy and b.holding and b.continuous_hold for b in boundaries.values()):
                raise RuntimeError("CPU unsafe terminal")
            self.reset()
        names = ("cr12_0", "cr12_1")
        return ({name: torch.zeros((1, 1)) for name in names}, {name: torch.zeros(1) for name in names},
            {name: terminated for name in names}, {name: truncated for name in names}, {"physics": "CPU fixture"})

    def claim(self, raw, modes=None):
        self.modes = modes or {}
        decision = self.facade.capture_proposal_decision(feasible_mask=physical_problem()["feasible_mask"],
            cost_matrix=physical_problem()["cost_matrix"])
        return self.facade.resolve_and_step_proposals(raw_action_ids=i([raw]),
            decoded_proposal=i([[-1 if task == 4 else task for task in raw]]),
            decision=decision, action_builder=self.builder)

    def continue_step(self, modes=None):
        self.modes = modes or {}
        return self.facade.step_without_new_claim(action_builder=self.builder)


class DualAdapterTests(unittest.TestCase):
    def test_two_births_share_batch_token_but_have_distinct_real_identity(self):
        h = DualFakeHost(); h.claim([0, 2])
        a, b = h.new_bindings
        self.assertEqual((a.robot_id, a.task_id, b.robot_id, b.task_id), (0, 0, 1, 2))
        self.assertIs(a.birth_artifact, b.birth_artifact)
        self.assertEqual(a.claim_token, b.claim_token)
        self.assertNotEqual(a.capture_id, b.capture_id)
        self.assertEqual(h.latest.result.updated_ownership.tolist(), [[0, -1, 1, -1]])
        self.assertEqual(h.adapter.bind_count, 2)

    def test_two_completions_use_one_real_receipt_and_independent_retirement(self):
        h = DualFakeHost(); h.auto_retire = False; h.claim([0, 2], {0: "completed", 1: "completed"})
        a, b = h.receipts
        self.assertIs(a.result, b.result)
        self.assertEqual((a.facts_consume_token, a.authority_receipt_id, a.transition_generation),
                         (b.facts_consume_token, b.authority_receipt_id, b.transition_generation))
        self.assertEqual(h.adapter.transition_count, 1)
        self.assertEqual(h.latest.result.completed_tasks.tolist(), [[True, False, True, False]])
        self.assertEqual(h.latest.published_view.lifecycle_state.completion_count.tolist(), [[1, 1]])
        self.assertEqual(h.report._physical_report._raw_new_candidate.shape, (1, 2, 4))
        h.adapter.retire_request(a.binding, a)
        self.assertIsNone(h.adapter.binding_for(0)); self.assertIs(h.adapter.binding_for(1), b.binding)
        self.assertIs(h.adapter.pending_result(1), b.pending)
        self.assertIs(h.adapter.ack_authority_deliveries(h.latest), h.receipts)
        self.assertEqual(len(h.adapter.history), 2)
        h.adapter.retire_request(b.binding, b)
        self.assertIsNone(h.adapter.binding_for(1))
        self.assertFalse(a.pending.custody.rgba.flags.writeable)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "report_once"):
            h.port.finalize_execution_transition(h.report)

    def test_one_completion_then_other_robot_claim_keeps_continuing_birth(self):
        h = DualFakeHost(); h.claim([0, 2], {0: "completed"})
        old = h.adapter.binding_for(1)
        h.claim([1, 2])
        fresh = h.adapter.binding_for(0)
        self.assertIs(h.adapter.binding_for(1), old)
        self.assertIsNot(fresh.birth_artifact, old.birth_artifact)
        self.assertEqual(fresh.birth_artifact.effective_task_by_robot.tolist(), [[1, -1]])
        self.assertEqual(h.latest.result.updated_ownership.tolist(), [[-1, 0, 1, -1]])
        self.assertEqual(len(h.adapter.history), 1)
        h.continue_step()
        self.assertIs(h.adapter.binding_for(1), old)
        self.assertIsNone(h.domain.current_read_port.read_current().provenance[0].assignment_artifact)

    def test_idle_no_claim_is_legal_healthy_hold_not_unavailable(self):
        h = DualFakeHost(); h.claim([0, 4])
        self.assertIsNone(h.adapter.binding_for(1))
        self.assertEqual(h.report.boundaries_by_robot[1].goal_id, None)
        self.assertEqual(int(h.latest.result.updated_robot_state[0, 1]), int(C.RobotLifecycleState.NEEDS_ASSIGNMENT))
        self.assertFalse(bool(h.latest.result.updated_failed_pairs.any()))
        h.continue_step({0: "completed"})
        h.continue_step()
        self.assertEqual(h.receipts, ())

    def test_executing_raw_no_claim_is_rejected_by_real_resolver(self):
        h = DualFakeHost(); h.claim([0, 2])
        original = h.adapter.binding_for(0)
        result = h.claim([4, 2])
        self.assertTrue(bool(result.resolution.structural_rejection_mask[0, 0]))
        self.assertEqual(result.resolution.interpretations[0][0].name, "ILLEGAL_EXECUTING_NOOP")
        self.assertIs(h.adapter.binding_for(0), original)
        self.assertEqual(result.admitted_effective_assignment.tolist(), [[0, 2]])

    def test_local_two_tasks_do_not_end_environment_global_four_do(self):
        h = DualFakeHost()
        initial_generation = int(h.domain.current_read_port.read_current().transition_generation[0])
        h.claim([0, 4], {0: "completed"}); h.claim([1, 4], {0: "completed"})
        self.assertFalse(bool(h.latest.terminated.any()))
        self.assertEqual(h.domain.current_read_port.read_current().episode_generation.tolist(), [0])
        first_data = tuple(x.pending.custody.rgba.tobytes() for x in h.adapter.history)
        h.claim([4, 2], {1: "completed"})
        final = h.claim([4, 3], {1: "completed"})
        self.assertIsNotNone(final.terminal_historical_payload)
        self.assertEqual(len(h.captured_terminal), 1)
        self.assertEqual(h.latest.published_view.lifecycle_state.completion_count.tolist(), [[2, 2]])
        self.assertEqual(h.latest.result.completed_tasks.tolist(), [[False, False, False, True]])
        self.assertEqual(h.latest.result.updated_task_state.tolist(), [[int(C.TaskLifecycleState.COMPLETED)] * 4])
        current = h.domain.current_read_port.read_current()
        self.assertIsNone(current.result)
        self.assertEqual(current.episode_generation.tolist(), [1])
        self.assertEqual(current.transition_generation.tolist(), [initial_generation + 4])
        self.assertEqual(current.lifecycle_state.ownership.tolist(), [[-1] * 4])
        self.assertEqual(h.domain.terminal_consumer_port.capture_pending_terminal_artifacts(), ())
        sidecar = h.captured_terminal[0].optional_sidecar
        schema = SC.build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale())
        self.assertEqual((schema["actor_schema"]["dimension"], schema["critic_schema"]["dimension"]), (145, 143))
        self.assertEqual(sidecar.critic_dimension, 143)
        self.assertEqual(sidecar.terminal_audit_projection.semantic_evidence.numel(), 143)
        self.assertIsNone(sidecar.bootstrap_critic_obs)
        self.assertEqual(tuple(x.pending.custody.rgba.tobytes() for x in h.adapter.history[:2]), first_data)

    def test_idle_unsafe_or_fake_request_evidence_rejects_whole_report(self):
        for change in ({"holding": False}, {"resource_healthy": False}, {"off_confirmed": False},
                       {"continuous_hold": False}, {"no_pending_data": False}, {"goal_id": "old", "capture_id": "old"}):
            with self.subTest(change=change):
                h = DualFakeHost(); h.overrides[1] = change
                with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "idle_boundary"):
                    h.claim([0, 4], {0: "completed"})
                self.assertEqual(h.adapter.history, ())
                self.assertIsNotNone(h.adapter.pending_result(0))

    def test_bad_second_completion_boundary_cannot_partially_commit_first(self):
        for key in ("off_confirmed", "holding", "resource_healthy", "continuous_hold", "native_valid"):
            with self.subTest(key=key):
                h = DualFakeHost(); h.overrides[1] = {key: False}
                with self.assertRaises(A.Cr12ExecutionAdapterError):
                    h.claim([0, 2], {0: "completed", 1: "completed"})
                self.assertIsNone(h.latest)
                self.assertEqual(h.adapter.history, ())
                self.assertTrue(all(h.adapter.pending_result(r).custody is not None for r in (0, 1)))

    def test_boundary_clock_must_be_global_and_all_robots_present(self):
        h = DualFakeHost(); h.overrides[1] = {"physics_step": 13}
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "boundary_clock"):
            h.claim([0, 2])
        h = DualFakeHost(); original = h.adapter.build_report
        def missing_robot(**kwargs):
            kwargs["boundaries_by_robot"].pop(1)
            return original(**kwargs)
        with patch.object(h.adapter, "build_report", missing_robot):
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "boundary_shape"):
                h.claim([0, 2])

    def test_full_typed_signals_cover_one_prestate_with_exact_robot_task_pairs(self):
        h = DualFakeHost(); signals = []
        def inspect(host):
            pub = host.domain.current_read_port.read_current()
            signals.append(host.report._validate_for_domain(host.adapter.domain_identity, pub, pub.lifecycle_state))
        h.before_finalize = inspect; h.claim([0, 2], {0: "completed", 1: "completed"})
        completion, release, unavailable = signals[0]
        self.assertEqual(tuple(completion.shape), (1, 2, 4))
        self.assertEqual(completion.dtype, torch.bool)
        self.assertEqual(completion.nonzero().tolist(), [[0, 0, 0], [0, 1, 2]])
        self.assertEqual(tuple(release.shape), (1, 2, 4)); self.assertFalse(bool(release.any()))
        self.assertEqual(tuple(unavailable.shape), (1, 2)); self.assertFalse(bool(unavailable.any()))

    def test_all_receipt_slots_validate_before_any_history_or_delivery_write(self):
        h = DualFakeHost()
        def damage_local_slot(host):
            host.adapter._pendings[1] = replace(host.adapter.pending_result(1), metadata={"invalid replacement": True})
        h.after_finalize = damage_local_slot
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "receipt_binding"):
            h.claim([0, 2], {0: "completed", 1: "completed"})
        self.assertEqual(h.adapter.history, ())
        self.assertEqual(h.adapter._deliveries, [None, None])
        self.assertIs(h.adapter._committed[1], h.latest)
        self.assertTrue(all(p.custody is not None for p in h.report._pendings))
        with self.assertRaises(Exception): h.continue_step()

    def test_retained_terminal_result_rejects_changed_clock_or_metadata(self):
        h = DualFakeHost(); observed = []
        def inspect(host):
            p = host.adapter.pending_result(0)
            kwargs = dict(outcome=p.outcome, acquired=p.acquired, custody=p.custody,
                          physics_step=p.physics_step, metadata=p.metadata)
            self.assertIs(host.adapter.record_pending(p.binding, **kwargs), p)
            for replacement in ({"physics_step": p.physics_step + 1}, {"metadata": {"changed": True}}):
                with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "result_replacement"):
                    host.adapter.record_pending(p.binding, **{**kwargs, **replacement})
            observed.append(True)
        h.before_finalize = inspect; h.claim([0, 2], {0: "completed"})
        self.assertEqual(observed, [True])

    def test_wrong_robot_custody_and_stale_binding_cannot_replace_result(self):
        h = DualFakeHost(); checked = []
        def before(host):
            a, b = (host.adapter.binding_for(r) for r in (0, 1))
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "result_capture_identity"):
                host.adapter.record_pending(a, outcome="completed", acquired=True, custody=custody(b), physics_step=12, metadata={})
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "result_binding"):
                host.adapter.record_pending(replace(a, robot_id=1), outcome="completed", acquired=True,
                    custody=custody(a), physics_step=12, metadata={})
            checked.append(True)
        h.before_finalize = before; h.claim([0, 2]); self.assertEqual(checked, [True])

    def test_lost_provenance_is_not_reconstructed_from_live_owner(self):
        h = DualFakeHost(); h.claim([0, 2])
        late = A.Cr12ExecutionAdapter(current_read_port=h.domain.current_read_port,
            run_instance_id="late", execution_profile="dual_m2n4")
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "claim_source"):
            h.facade.step_without_new_claim(action_builder=lambda environment, assignment: late.bind_effective_assignments(assignment))

    def test_missing_prior_publication_is_rejected_even_with_same_owners(self):
        h = DualFakeHost(); h.claim([0, 2])
        # Emulate losing the already observed publication, without changing authority.
        h.adapter._observed = h.new_bindings[0].birth_artifact.source_publication
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "publication_gap"):
            h.continue_step()

    def test_atomic_binding_validation_does_not_install_first_before_bad_second(self):
        h = DualFakeHost()
        def corrupt(host, assignment): assignment[0, 1] = 3
        h.before_bind = corrupt
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "claim_assignment"):
            h.claim([0, 2])
        self.assertEqual(h.adapter.bind_count, 0)
        self.assertTrue(all(h.adapter.binding_for(r) is None for r in (0, 1)))

    def test_receipt_swap_duplicate_retire_and_unretired_second_block_next_step(self):
        h = DualFakeHost(); h.auto_retire = False; h.claim([0, 2], {0: "completed", 1: "completed"})
        a, b = h.receipts
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "retire_before_receipt"):
            h.adapter.retire_request(a.binding, b)
        h.adapter.retire_request(a.binding, a)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "retire_before_receipt"):
            h.adapter.retire_request(a.binding, a)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "unacknowledged_transition"):
            h.continue_step()
        self.assertIs(h.adapter.pending_result(1), b.pending)
        self.assertEqual(len(h.adapter.history), 2)

    def test_retirement_failure_preserves_whole_batch_and_poison(self):
        for fail_robot in (0, 1):
            with self.subTest(fail_robot=fail_robot):
                h = DualFakeHost()
                def fail(host):
                    for receipt in host.receipts:
                        if receipt.binding.robot_id == fail_robot:
                            raise RuntimeError("CPU backend retirement failure")
                        host.adapter.retire_request(receipt.binding, receipt)
                h.after_ack = fail
                with self.assertRaisesRegex(RuntimeError, "retirement failure"):
                    h.claim([0, 2], {0: "completed", 1: "completed"})
                self.assertEqual(len(h.adapter.history), 2)
                self.assertEqual(h.latest.result.completed_tasks.tolist(), [[True, False, True, False]])
                self.assertTrue(all(r.pending.custody is not None for r in h.adapter.history))
                self.assertIsNotNone(h.adapter.pending_result(fail_robot))
                with self.assertRaises(Exception): h.continue_step()

    def test_pending_request_blocks_episode_reset_observation(self):
        h = DualFakeHost(); h.auto_retire = False; h.claim([0, 2], {0: "completed", 1: "completed"})
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "reset_live_request"):
            h.adapter.observe_episode_reset()

    def test_c_and_r_are_aggregated_without_marking_failed_pairs(self):
        h = DualFakeHost(); h.claim([0, 2], {0: "completed", 1: "cancelled"})
        self.assertEqual(h.latest.result.completed_tasks.tolist(), [[True, False, False, False]])
        self.assertEqual(h.latest.result.released_tasks.tolist(), [[False, False, True, False]])
        self.assertFalse(bool(h.latest.result.updated_failed_pairs.any()))
        self.assertEqual(tuple(r.pending.outcome for r in h.receipts), ("completed", "cancelled"))

    def test_only_fixed_profiles_and_plural_dual_interfaces(self):
        h = DualFakeHost()
        for kwargs in ({}, {"execution_profile": "anything"}):
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "integration_scale"):
                A.Cr12ExecutionAdapter(current_read_port=h.domain.current_read_port, run_instance_id="bad", **kwargs)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "singular_api"):
            h.adapter.bind_effective_assignment(i([[0, 2]]))


if __name__ == "__main__":
    unittest.main()
