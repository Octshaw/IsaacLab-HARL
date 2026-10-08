"""Focused CPU integration with real resolver/claim/domain/authority/facade.

Only the physics sample and camera custody are fixtures.  No Isaac/Kit import,
historical harness import, repository inventory, or runtime launch occurs.
"""
from dataclasses import replace
import importlib
from pathlib import Path
import sys
from types import ModuleType
import unittest

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "source/isaaclab_tasks/isaaclab_tasks"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
# Same canonical namespace bootstrap used by the current pure component tests.
# Never replace an existing module or load a production source under an alias.
for name, path in (("isaaclab_tasks", SOURCE), ("isaaclab_tasks.direct", SOURCE / "direct"),
                   (PREFIX, SOURCE / "direct/scan_mobile_manipulator")):
    if name not in sys.modules:
        package = ModuleType(name)
        package.__package__ = name
        package.__path__ = [str(path)]
        sys.modules[name] = package

def module(name): return importlib.import_module(f"{PREFIX}.{name}")

A = module("assignment_cr12_execution_adapter")
D = module("assignment_event_profile_runtime_domain")
P = module("assignment_profile_contract")
S = module("assignment_event_profile_synchronous_runtime")
F = module("assignment_event_runtime_facade")
C = module("assignment_lifecycle_transition_contract")
SC = module("assignment_event_profile_schema_contract_v2")
TS = module("assignment_event_terminal_critic_sidecar")
PE = module("assignment_event_policy_evidence")
DEVICE = torch.device("cpu")

def i(value): return torch.tensor(value, dtype=torch.int64)

def physical_problem():
    return {"num_envs": 1, "num_agents": 1, "agent_names": ("cr12",),
        "num_viewpoints": 2, "viewpoint_ids": (0, 1),
        "base_pos": torch.zeros((1, 1, 3)), "base_yaw": torch.zeros((1, 1)),
        "scanner_pos": torch.tensor([[[0., 0., 1.]]]),
        "scanner_quat": torch.tensor([[[1., 0., 0., 0.]]]),
        "viewpoint_pos": torch.tensor([[[.01, 0., 1.], [0., 0., 1.]]]),
        "viewpoint_quat": torch.tensor([[[1., 0., 0., 0.], [1., 0., 0., 0.]]]),
        "arm_reach": torch.tensor([1.5]), "scanner_min_range": torch.tensor([0.]),
        "scanner_max_range": torch.tensor([2.]), "scanner_fov_deg": torch.tensor([60.]),
        "feasible_mask": torch.ones((1, 1, 2), dtype=torch.bool),
        "cost_matrix": torch.tensor([[[.01, 0.]]])}

def scale():
    return SC.build_event_policy_scale_contract_v2(M=1, N=2,
        ordered_agent_names=("cr12",), ordered_task_ids=(0, 1), scene_env_spacing=4.,
        sim_dt_seconds=1/120, control_decimation=12, episode_time_limit_seconds=32.)

def custody(binding):
    return A.RawCaptureCustody(rgba=np.full((2, 3, 4), 125, np.uint8),
        metadata={"goal_id": binding.goal_id, "capture_id": binding.capture_id,
            "attempt_id": binding.attempt_id, "fresh": True,
            "source_frame": 42, "rendering_frame": 42})


class FakePhysicsHost:
    """Explicit fake physical samples, using unmocked production lifecycle."""
    def __init__(self):
        self.profile = P.resolve_assignment_profile("event_gated_local_mrta",
            P.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        self.domain = D._EventProfileLifecycleRuntimeDomain(D._EventProfileLifecycleDomainSpec(
            self.profile, device=DEVICE, env_ids=i([0]), num_robots=1, num_tasks=2))
        self.adapter = A.Cr12ExecutionAdapter(current_read_port=self.domain.current_read_port,
            run_instance_id="cpu_fixture")
        self.validation = self.domain.environment_admission_validation_port
        self.port = self.domain.environment_port
        self.mode = None
        self.step_count = 0
        self.boundary_overrides = {}
        self.before_finalize = None
        self.after_finalize = None
        self.latest = self.receipt = self.report = None
        self.new_bindings = []
        self.auto_retire = True
        self.legacy_report = False
        runtime = S.EventProfileSynchronousRuntimeCoordinator(environment=self,
            current_read_port=self.domain.current_read_port,
            production_claim_port=self.domain.production_claim_port,
            physical_step_admission_port=self.domain.physical_step_admission_port,
            standalone_reset_admission_port=self.domain.standalone_reset_admission_port,
            terminal_consumer_port=self.domain.terminal_consumer_port,
            fence_read_port=self.domain.interstep_fence_read_port)
        self.facade = F._compose_event_assignment_runtime_facade(resolved_assignment_profile=self.profile,
            runtime_domain=self.domain, synchronous_runtime=runtime)
        self.facade.reset()

    def reset(self):
        self.validation.validate_reset_entry_for_active_call()
        with self.port.episode_rebuild(selected_env_ids=i([0]),
                initial_task_state=i([[int(C.TaskLifecycleState.AVAILABLE)] * 2]),
                initial_robot_state=i([[int(C.RobotLifecycleState.NEEDS_ASSIGNMENT)]]),
                initial_ownership=i([[-1, -1]])) as reset:
            reset.commit_physical_reset_complete()
        self.adapter.observe_episode_reset()
        return {"cr12": torch.zeros((1, 1))}, {"physics": "explicit CPU fixture"}

    def builder(self, environment, assignment):
        assert environment is self
        binding, new = self.adapter.bind_effective_assignment(assignment)
        if new: self.new_bindings.append(binding)
        return binding

    def step(self, binding):
        self.validation.validate_physical_step_entry_for_active_call()
        self.step_count += 12  # fake physics, never a simulation API
        if self.mode:
            self.adapter.record_pending(binding, outcome=self.mode,
                acquired=self.mode != "cancelled", custody=None if self.mode == "cancelled" else custody(binding),
                physics_step=self.step_count - 3, metadata={"artifact_saved": False, "fake_physics": True})
        boundary = A.ExecutionBoundaryEvidence(self.step_count, binding.goal_id, binding.capture_id,
            True, True, True, True, True, True)
        boundary = replace(boundary, **self.boundary_overrides)
        current = self.domain.current_read_port.read_current()
        snapshot = TS.capture_pre_reset_critic_physical_snapshot_v2(
            assignment_problem=physical_problem(), episode_progress_steps=i([self.step_count // 12]),
            scale_contract=scale(), physical_problem_source="FakePhysicsHost CPU fixture")
        self.report = self.adapter.build_report(boundary=boundary,
            coverage_before_transition=current.lifecycle_state.task_state == int(C.TaskLifecycleState.COMPLETED),
            physical_truncated=torch.zeros(1, dtype=torch.bool),
            time_limit_reached=torch.zeros(1, dtype=torch.bool), pre_reset_critic_physical_snapshot=snapshot)
        self.validation.validate_physical_finalization_for_active_call()
        if self.before_finalize: self.before_finalize(self)
        self.latest = (self.port.finalize_physical_transition(self.report._physical_report)
            if self.legacy_report else self.port.finalize_execution_transition(self.report))
        if self.after_finalize: self.after_finalize(self)
        self.receipt = None if self.legacy_report else self.adapter.ack_authority_delivery(self.latest)
        if self.receipt and self.auto_retire:
            self.adapter.retire_request(binding, self.receipt)
        terminated, truncated = self.latest.terminated, self.latest.truncated
        if bool((terminated | truncated).any()):
            if not boundary.off_confirmed or not boundary.resource_healthy or not boundary.holding:
                raise RuntimeError("Unsafe terminal cannot healthy-reset")
            self.reset()
        return ({"cr12": torch.zeros((1, 1))}, {"cr12": torch.zeros(1)},
            {"cr12": terminated}, {"cr12": truncated}, {"physics": "explicit CPU fixture"})

    def claim(self, task, mode=None):
        self.mode = mode
        decision = self.facade.capture_proposal_decision(
            feasible_mask=physical_problem()["feasible_mask"], cost_matrix=physical_problem()["cost_matrix"])
        return self.facade.resolve_and_step_proposals(raw_action_ids=i([[task]]),
            decoded_proposal=i([[task]]), decision=decision, action_builder=self.builder)

    def continue_step(self, mode=None):
        self.mode = mode
        return self.facade.step_without_new_claim(action_builder=self.builder)


class AdapterTests(unittest.TestCase):
    def test_normal_real_authority_continuation_terminal_reset_and_ack(self):
        h = FakePhysicsHost(); h.claim(0); binding = h.adapter.binding
        first = h.domain.current_read_port.read_current()
        self.assertIsNone(first.provenance[0].assignment_artifact)
        h.continue_step(); self.assertIs(h.adapter.binding, binding)
        h.continue_step("completed")
        r0 = h.receipt
        self.assertEqual(h.adapter.bind_count, 1)
        self.assertEqual(h.adapter.continuation_count, 2)
        self.assertEqual(int(h.latest.result.transition_generation[0]), int(first.transition_generation[0]) + 2)
        self.assertTrue(bool(h.latest.result.completed_tasks[0, 0]))
        result = h.claim(1, "completed")
        self.assertIsNotNone(result.terminal_historical_payload)
        current = h.domain.current_read_port.read_current()
        self.assertIsNone(current.result)
        self.assertEqual(int(current.episode_generation[0]), 1)
        self.assertEqual(int(current.transition_generation[0]), int(first.transition_generation[0]) + 3)
        self.assertEqual(len(h.adapter.history), 2)
        self.assertEqual(int(h.latest.published_view.lifecycle_state.completion_count[0, 0]), 2)
        self.assertFalse(r0.pending.custody.rgba.flags.writeable)
        self.assertEqual(h.adapter.transition_count, 4)
        self.assertEqual(h.domain.terminal_consumer_port.capture_pending_terminal_artifacts(), ())

    def test_cancel_release_reclaim_has_new_real_identity_and_no_failed_pair(self):
        h = FakePhysicsHost(); h.claim(0, "cancelled"); a = h.receipt
        self.assertTrue(bool(h.latest.result.released_tasks[0, 0]))
        self.assertFalse(bool(h.latest.result.completed_tasks.any()))
        self.assertFalse(bool(h.latest.result.updated_failed_pairs.any()))
        h.claim(0); b = h.adapter.binding
        self.assertNotEqual(a.binding.claim_token, b.claim_token)
        self.assertNotEqual(a.binding.capture_id, b.capture_id)
        self.assertEqual(a.binding.attempt_id, b.attempt_id)
        h.continue_step("completed"); h.claim(1, "completed")
        self.assertEqual([x.pending.outcome for x in h.adapter.history], ["cancelled", "completed", "completed"])

    def test_block_end_loss_rejects_completion_and_release_before_authority(self):
        for mode in ("completed", "cancelled"):
            for key in ("holding", "continuous_hold", "resource_healthy", "off_confirmed", "native_valid"):
                with self.subTest(mode=mode, key=key):
                    h = FakePhysicsHost(); h.boundary_overrides[key] = False
                    with self.assertRaises(A.Cr12ExecutionAdapterError): h.claim(0, mode)
                    self.assertEqual(len(h.adapter.history), 0)
                    self.assertIsNotNone(h.adapter.pending_result())
                    with self.assertRaises(Exception): h.continue_step()

    def test_cancel_racing_data_cannot_be_relabelled_no_data(self):
        h = FakePhysicsHost(); h.boundary_overrides["no_pending_data"] = False
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "cancel_data_race"):
            h.claim(0, "cancelled")
        self.assertEqual(len(h.adapter.history), 0)

    def test_retire_before_receipt_rejected_and_data_survives_retire(self):
        h = FakePhysicsHost(); seen = []
        def before(host):
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "retire_before_receipt"):
                host.adapter.retire_request(host.adapter.binding, None)
            seen.append(host.adapter.pending_result())
        h.before_finalize = before; h.claim(0, "completed")
        self.assertIs(h.adapter.history[0].pending, seen[0])
        self.assertIsNone(h.adapter.binding)
        with self.assertRaises(ValueError): seen[0].custody.rgba.setflags(write=True)

    def test_duplicate_ack_returns_original_without_second_delivery(self):
        h = FakePhysicsHost(); h.claim(0, "completed")
        self.assertIs(h.adapter.ack_authority_delivery(h.latest), h.receipt)
        self.assertEqual(len(h.adapter.history), 1)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "report_once"):
            h.port.finalize_execution_transition(h.report)

    def test_foreign_outcome_cannot_ack_or_retire(self):
        h = FakePhysicsHost(); other = FakePhysicsHost(); other.claim(0, "completed")
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "receipt_source"):
            h.adapter.ack_authority_delivery(other.latest)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "retire_before_receipt"):
            h.adapter.retire_request(other.receipt.binding, other.receipt)

    def test_missing_claim_and_without_admission_rejected(self):
        h = FakePhysicsHost()
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "execution_admission"):
            h.adapter.bind_effective_assignment(i([[0]]))
        with self.assertRaises(A.Cr12ExecutionAdapterError): h.continue_step()

    def test_old_binding_after_reclaim_rejected(self):
        h = FakePhysicsHost(); h.claim(0, "cancelled"); old = h.receipt.binding
        def check(host):
            with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "result_binding"):
                host.adapter.record_pending(old, outcome="completed", acquired=True, custody=custody(old),
                    physics_step=host.step_count, metadata={})
        h.before_finalize = check; h.claim(0)
        self.assertIsNot(h.adapter.binding, old)

    def test_post_commit_failure_preserves_real_receipt_and_poison(self):
        h = FakePhysicsHost()
        def fail(host): raise RuntimeError("CPU local bookkeeping failure after actual transaction")
        h.after_finalize = fail
        with self.assertRaisesRegex(RuntimeError, "CPU local bookkeeping"):
            h.claim(0, "completed")
        self.assertTrue(bool(h.latest.result.completed_tasks[0, 0]))
        self.assertIsNotNone(h.adapter.pending_result().custody)
        with self.assertRaises(Exception): h.continue_step()

    def test_explicit_source_and_old_default_are_preserved(self):
        kwargs = dict(assignment_problem=physical_problem(), episode_progress_steps=i([0]), scale_contract=scale())
        old = PE.capture_event_policy_physical_problem_evidence_v2(**kwargs)
        self.assertEqual(old.provenance["physical_problem_source"], "ScanMobileManipulatorEnv.get_assignment_problem current mapping")
        new = TS.capture_pre_reset_critic_physical_snapshot_v2(**kwargs,
            physical_problem_source="CR12LifecycleHost.get_assignment_problem current mapping")
        self.assertEqual(new.physical_evidence.provenance["physical_problem_source"],
            "CR12LifecycleHost.get_assignment_problem current mapping")
        for bad in (None, "", " ", False):
            with self.assertRaises(PE.EventPolicyEvidenceError):
                PE.capture_event_policy_physical_problem_evidence_v2(**kwargs, physical_problem_source=bad)

    def test_raw_custody_is_independent_and_requires_real_fresh_same_frame(self):
        h = FakePhysicsHost(); h.claim(0); b = h.adapter.binding
        raw = np.ones((2, 3, 4), np.uint8); md = dict(custody(b).metadata)
        held = A.RawCaptureCustody(rgba=raw, metadata=md); raw[:] = 0; md["fresh"] = False
        self.assertTrue(np.all(held.rgba == 1)); self.assertTrue(held.metadata["fresh"])
        for change in ({"fresh": False}, {"source_frame": 43}, {"capture_id": ""}):
            bad = {**dict(custody(b).metadata), **change}
            with self.assertRaises(A.Cr12ExecutionAdapterError): A.RawCaptureCustody(rgba=raw, metadata=bad)

    def test_old_episode_and_nonowner_binding_rejected(self):
        h = FakePhysicsHost(); h.claim(0); b = h.adapter.binding
        pub = h.domain.current_read_port.read_current()
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "binding_episode"):
            h.adapter._active_matches(pub, replace(b, episode_generation=b.episode_generation - 1))
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "binding_owner"):
            h.adapter._active_matches(pub, replace(b, task_id=1))

    def test_lost_birth_binding_cannot_reconstruct_from_physical_p2(self):
        h = FakePhysicsHost(); h.claim(0)
        late = A.Cr12ExecutionAdapter(current_read_port=h.domain.current_read_port, run_instance_id="late")
        def builder(environment, assignment): return late.bind_effective_assignment(assignment)
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "claim_source"):
            h.facade.step_without_new_claim(action_builder=builder)

    def test_current_prestate_is_revalidated_before_producer(self):
        h = FakePhysicsHost()
        def alter_report(host):
            # Accidental private tensor alteration must not become authority input.
            host.report._physical_report._coverage_before_transition[0, 1] = True
        h.before_finalize = alter_report
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "report_coverage"):
            h.claim(0, "completed")
        self.assertIsNone(h.latest)
        self.assertIsNotNone(h.adapter.pending_result().custody)

    def test_stale_block_boundary_is_not_new_evidence(self):
        h = FakePhysicsHost(); h.claim(0)
        h.boundary_overrides["physics_step"] = 12
        with self.assertRaisesRegex(A.Cr12ExecutionAdapterError, "boundary_native"):
            h.continue_step("completed")

    def test_normal_terminal_sidecar_is_audit_not_timeout_bootstrap(self):
        h = FakePhysicsHost(); h.claim(0, "completed"); captured = []
        def capture(host):
            if bool(host.latest.terminated.any()):
                captured.extend(host.domain.terminal_consumer_port.capture_pending_terminal_artifacts())
        h.after_finalize = capture
        h.claim(1, "completed")
        sidecar = captured[0].optional_sidecar
        self.assertIsNotNone(sidecar)
        expected = SC.build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale())["critic_schema"]["dimension"]
        self.assertEqual(sidecar.critic_dimension, expected)
        self.assertEqual(sidecar.terminal_audit_projection.semantic_evidence.numel(), expected)
        self.assertIsNone(sidecar.bootstrap_critic_obs)
        self.assertFalse(sidecar.bootstrap_projection_valid)

    def test_completed_unavailable_keeps_data_and_refuses_healthy_reset(self):
        h = FakePhysicsHost(); h.claim(0, "completed")
        h.boundary_overrides.update(off_confirmed=False, resource_healthy=False)
        with self.assertRaisesRegex(RuntimeError, "Unsafe terminal"):
            h.claim(1, "completed_unavailable")
        self.assertTrue(bool((h.latest.result.updated_task_state == int(C.TaskLifecycleState.COMPLETED)).all()))
        self.assertEqual(int(h.latest.result.updated_robot_state[0, 0]), int(C.RobotLifecycleState.UNAVAILABLE))
        self.assertEqual(len(h.adapter.history), 2)
        self.assertIsNotNone(h.adapter.history[1].pending.custody)
        self.assertEqual(int(h.latest.result.episode_generation[0]), 0)

    def test_old_physical_report_remains_zero_signal_continuation(self):
        h = FakePhysicsHost(); h.legacy_report = True; h.claim(0)
        self.assertFalse(bool(h.latest.result.completed_tasks.any()))
        self.assertFalse(bool(h.latest.result.released_tasks.any()))
        self.assertFalse(bool(h.latest.result.updated_failed_pairs.any()))
        self.assertEqual(h.latest.result.updated_ownership.tolist(), [[0, -1]])

    def test_new_proposal_cannot_enter_active_physical_admission(self):
        h = FakePhysicsHost(); checked = []
        def during_step(host):
            with self.assertRaises(Exception):
                host.facade.capture_proposal_decision(
                    feasible_mask=physical_problem()["feasible_mask"], cost_matrix=physical_problem()["cost_matrix"])
            checked.append(True)
        h.before_finalize = during_step; h.claim(0)
        self.assertEqual(checked, [True])
        self.assertEqual(h.adapter.bind_count, 1)

    def test_ack_then_local_retire_failure_keeps_binding_and_committed_data(self):
        h = FakePhysicsHost()
        def fail_after_ack(host):
            host.adapter.ack_authority_delivery(host.latest)
            raise RuntimeError("CPU backend local retire failed")
        h.after_finalize = fail_after_ack
        with self.assertRaisesRegex(RuntimeError, "local retire failed"):
            h.claim(0, "completed")
        self.assertEqual(len(h.adapter.history), 1)
        self.assertIsNotNone(h.adapter.binding)
        self.assertIs(h.adapter.pending_result(), h.adapter.history[0].pending)
        self.assertTrue(bool(h.latest.result.completed_tasks[0, 0]))
        with self.assertRaises(Exception): h.continue_step()


if __name__ == "__main__": unittest.main()
