"""Pure permit, failure, ordering, and repository-local AST guard tests."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as H  # noqa: E402


def _permit(*, sequence: int = 0, permit_id: str = "permit-0", operation=None):
    C = H.C
    return C.B2RMutationPermitV1(
        permit_id=permit_id,
        update_id="update-r1-0001",
        authority_config_digest=H.authority().config_digest,
        component_kind="actor",
        owner_identity="actor0",
        actor_id=0,
        stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        epoch=0,
        minibatch=1,
        canonical_index_digest=H.digest("rows-0"),
        allowed_operations=(C.B2RPermitOperationV1.BACKWARD if operation is None else operation,),
        expected_call_count=1,
        precondition_fingerprint_digest=H.digest("precondition"),
        issuance_sequence=sequence,
    )


def _consume(ledger, **changes):
    C = H.C
    values = dict(
        permit_id="permit-0", operation=C.B2RPermitOperationV1.BACKWARD,
        update_id="update-r1-0001", authority_config_digest=H.authority().config_digest,
        component_kind="actor", owner_identity="actor0", actor_id=0,
        stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE, epoch=0, minibatch=1,
        canonical_index_digest=H.digest("rows-0"), precondition_fingerprint_digest=H.digest("precondition"),
    )
    values.update(changes)
    return ledger.consume(**values)


def test_permit_ledger() -> dict[str, object]:
    C, E = H.C, H.E
    ledger = C.B2RPermitLedgerV1((_permit(),))
    receipt = _consume(ledger)
    H.assert_true(receipt.consumed_count == 1 and ledger.pending_count == 0, "permit consume")
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: _consume(ledger))
    fault_cases = (
        (C.STOP_UNAUTHORIZED_BACKWARD, {"owner_identity": "actor1"}),
        (C.STOP_UNAUTHORIZED_BACKWARD, {"actor_id": 1}),
        (C.STOP_MODE_ORDER, {"stage": C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE}),
        (C.STOP_UNAUTHORIZED_OPTIMIZER_STEP, {"operation": C.B2RPermitOperationV1.OPTIMIZER_STEP}),
        (C.STOP_UNAUTHORIZED_BACKWARD, {"minibatch": 2}),
        (C.STOP_UNAUTHORIZED_BACKWARD, {"canonical_index_digest": H.digest("wrong-rows")}),
        (E.STOP_AUTHORITY_DRIFT, {"update_id": "stale"}),
        (E.STOP_AUTHORITY_DRIFT, {"authority_config_digest": H.digest("stale")}),
    )
    for stop, changes in fault_cases:
        H.expect_stop(stop, lambda changes=changes: _consume(C.B2RPermitLedgerV1((_permit(),)), **changes))
    expired = C.B2RPermitLedgerV1((_permit(),)); expired.expire("permit-0")
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: _consume(expired))
    poisoned = C.B2RPermitLedgerV1((_permit(),)); poisoned.poison()
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: _consume(poisoned))
    out_of_order = C.B2RPermitLedgerV1((_permit(), _permit(sequence=1, permit_id="permit-1")))
    H.expect_stop(C.STOP_MODE_ORDER, lambda: _consume(out_of_order, permit_id="permit-1"))
    H.expect_stop(C.STOP_VALUENORM, lambda: _consume(C.B2RPermitLedgerV1((_permit(),)), operation=C.B2RPermitOperationV1.VALUENORM_UPDATE))
    return {"valid_consumption": 1, "permit_faults": len(fault_cases) + 5, "real_operations": 0}


def test_ordering_receipt_failure() -> dict[str, object]:
    C = H.C
    stages = tuple(C.B2RUpdateStageV1)
    machine = C.B2RUpdateStateMachineV1()
    for stage in stages[1:]:
        machine.transition(stage)
    machine.require_checkpoint_eligible(pending_permit_count=0)
    H.assert_true(machine.evidence(pending_permit_count=0).checkpoint_eligible, "legal S0-S10")
    skipped = C.B2RUpdateStateMachineV1()
    H.expect_stop(C.STOP_MODE_ORDER, lambda: skipped.transition(C.B2RUpdateStageV1.S2_EVENT_RETURNS_FROZEN))
    actor_before_plan = C.B2RUpdateStateMachineV1()
    H.expect_stop(C.STOP_MODE_ORDER, lambda: actor_before_plan.transition(C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE))
    critic_before_actor_complete = C.B2RUpdateStateMachineV1()
    for stage in stages[1:5]:
        critic_before_actor_complete.transition(stage)
    H.expect_stop(C.STOP_MODE_ORDER, lambda: critic_before_actor_complete.transition(C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE))
    rollover_before_audit = C.B2RUpdateStateMachineV1()
    for stage in stages[1:7]:
        rollover_before_audit.transition(stage)
    H.expect_stop(C.STOP_ROLLOVER_ORDER, lambda: rollover_before_audit.transition(C.B2RUpdateStageV1.S9_ROLLOVER_COMPLETE))
    reverse = C.B2RUpdateStateMachineV1(); reverse.transition(stages[1])
    H.expect_stop(C.STOP_MODE_ORDER, lambda: reverse.transition(stages[0]))
    precheckpoint = C.B2RUpdateStateMachineV1()
    H.expect_stop(C.STOP_CHECKPOINT_BOUNDARY, lambda: precheckpoint.require_checkpoint_eligible(pending_permit_count=0))
    H.expect_stop(C.STOP_CHECKPOINT_BOUNDARY, lambda: machine.require_checkpoint_eligible(pending_permit_count=1))
    poisoned = C.B2RUpdateStateMachineV1()
    for stage in stages[1:6]:
        poisoned.transition(stage)
    poisoned.poison()
    H.expect_stop(C.STOP_MODE_ORDER, lambda: poisoned.transition(C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE))
    synthetic = C.B2RStepReceiptV1(
        consumed_permit_id="permit-0", stage=stages[5], owner_identity="actor0", actor_id=0, epoch=0, minibatch=0,
        canonical_row_digest=H.digest("rows"), pre_loss_fingerprint=H.digest("loss-pre"), loss_summary="synthetic finite",
        gradient_fingerprint=H.digest("gradient-absent"), clip_summary="not executed", pre_parameter_fingerprint=H.digest("p0"),
        post_parameter_fingerprint=H.digest("p0"), optimizer_fingerprint=H.digest("opt"), valuenorm_fingerprint=H.digest("vn"),
        mutation_classification="no real mutation", no_foreign_mutation=True, stage_transition_result="synthetic only", synthetic_fixture=True,
    )
    H.assert_true(len(synthetic.receipt_digest) == 64, "synthetic receipt")
    expectation = C.B2RMutationExpectationV1(
        component_kind="actor", owner_identity="actor0", condition_identity="nonempty active-and-DVM minibatch",
        expected_backward_count=2, expected_optimizer_step_count=0, expected_valuenorm_update_count=0,
        parameter_mutation_classification="R2 backward-only expects none", optimizer_mutation_classification="disabled",
        valuenorm_mutation_classification="not applicable", forced_or_no_policy_rows_excluded=True,
    )
    H.assert_true(expectation.expected_backward_count == 2 and expectation.expected_optimizer_step_count == 0, "R2 expectation representation")
    H.expect_stop(C.STOP_UNEXPECTED_STEP_COUNT, lambda: C.B2RMutationExpectationV1(
        component_kind="actor", owner_identity="actor0", condition_identity="bad", expected_backward_count=-1,
        expected_optimizer_step_count=0, expected_valuenorm_update_count=0, parameter_mutation_classification="none",
        optimizer_mutation_classification="none", valuenorm_mutation_classification="none", forced_or_no_policy_rows_excluded=True,
    ))
    H.expect_stop(C.STOP_MUTATION_ATTRIBUTION, lambda: C.B2RStepReceiptV1(**{name: getattr(synthetic, name) for name in synthetic.__dataclass_fields__ if name != "schema_version" and name != "synthetic_fixture"}, synthetic_fixture=False))
    pure_failure = C.B2RFailureEvidenceV1(
        stop_code=C.STOP_MODE_ORDER, stage="S4", owner_identity=None, component_kind=None, actor_id=None, epoch=None, minibatch=None,
        canonical_index_identity=None, parameter_identity=None, expected_summary="S5", observed_summary="S6", last_completed_receipt=None,
        irreversible_mutation_occurred=False, partial_update=False, route_poisoned=True, restoration_classification="none needed",
        quarantine_classification="synthetic fixture", rollover_allowed=False, checkpoint_allowed=False, next_rollout_allowed=False,
        public_use_allowed=False, prohibited_next_actions=("continue",),
    )
    future_partial = C.B2RFailureEvidenceV1(
        stop_code=C.STOP_MUTATION_ATTRIBUTION, stage="S5", owner_identity="actor0", component_kind="actor", actor_id=0, epoch=0, minibatch=0,
        canonical_index_identity="k0", parameter_identity="actor0.linear.weight", expected_summary="attributed mutation", observed_summary="future mismatch",
        last_completed_receipt=synthetic.receipt_digest, irreversible_mutation_occurred=True, partial_update=True, route_poisoned=True,
        restoration_classification="no rollback claim", quarantine_classification="mandatory", rollover_allowed=False, checkpoint_allowed=False,
        next_rollout_allowed=False, public_use_allowed=False, prohibited_next_actions=("rollover", "checkpoint", "public_use"),
    )
    H.assert_true(len(pure_failure.failure_digest) == 64 and len(future_partial.failure_digest) == 64, "failure schema")
    H.expect_stop(C.STOP_MUTATION_ATTRIBUTION, lambda: C.B2RFailureEvidenceV1(**{name: getattr(future_partial, name) for name in future_partial.__dataclass_fields__ if name not in {"schema_version", "route_poisoned"}}, route_poisoned=False))
    return {"legal_transitions": 10, "ordering_faults": 8, "synthetic_receipts": 1, "mutation_expectations": 1, "failure_schemas": 2}


def test_static_and_public_guards() -> dict[str, object]:
    G = H.G
    contract_files = tuple(H.SCAN_SOURCE / name for name in (
        "assignment_event_training_evidence.py", "assignment_event_training_plans.py",
        "assignment_event_training_control.py", "assignment_event_training_static_guards.py",
    ))
    guarded_private_files = contract_files + (H.SCAN_SOURCE / "assignment_event_learned_route.py",)
    contract_test_files = tuple(Path(__file__).resolve().parent / name for name in (
        "_assignment_phase_b2_r1_contract_helpers.py",
        "test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py",
        "test_assignment_phase_b2_r1_update_plans_factor_pure.py",
        "test_assignment_phase_b2_r1_permits_ordering_static_guards_pure.py",
    ))
    guarded_source_and_tests = guarded_private_files + contract_test_files
    stock = G.validate_no_stock_trainer_calls_v1(guarded_source_and_tests)
    mutation = G.validate_no_training_mutation_calls_v1(guarded_source_and_tests)
    H.assert_true(stock.violation_count == 0 and mutation.violation_count == 0, "R1 source guard")
    private_extension_files = tuple(sorted(H.SCAN_SOURCE.glob("assignment_event_training_*.py")))
    public_files = tuple(sorted(path for path in H.SCAN_SOURCE.glob("*.py") if path not in private_extension_files))
    tokens = tuple(path.stem for path in contract_files)
    public = G.validate_public_route_isolation_v1(public_files, private_module_tokens=tokens)
    H.assert_true(public.violation_count == 0, "public route isolation")
    stock_snippets = (
        (G.STOP_STOCK_FULL_ROW_ACTOR_PATH, "OnPolicyHARunner.train()"),
        (G.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.train()"),
        (G.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.update()"),
        (G.STOP_CRITIC_TRAINING_SLICE, "VCritic.train()"),
        (G.STOP_CRITIC_TRAINING_SLICE, "VCritic.update()"),
        (G.STOP_STOCK_RETURNS_BYPASS, "critic_buffer.compute_returns()"),
    )
    for index, (stop, source) in enumerate(stock_snippets):
        H.expect_stop(stop, lambda index=index, source=source: G.validate_stock_trainer_source_text_v1(source, identity=f"stock-{index}"))
    mutation_snippets = (
        (G.STOP_UNAUTHORIZED_BACKWARD, "loss.backward()"),
        (G.STOP_UNAUTHORIZED_BACKWARD, "torch.autograd.backward(loss)"),
        (G.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "optimizer.step()"),
        (G.STOP_VALUENORM, "valuenorm.update(values)"),
    )
    for stop, source in mutation_snippets:
        H.expect_stop(stop, lambda stop=stop, source=source: G.validate_training_mutation_source_text_v1(source, identity=stop))
    H.expect_stop(G.STOP_PUBLIC_ROUTE_OPEN, lambda: G.validate_public_route_source_text_v1("from x import assignment_event_training_control", identity="public-fixture", private_module_tokens=tokens))
    H.assert_true(all(module.__all__ == () for module in (H.E, H.P, H.C, H.G)), "private export fence")
    return {"guarded_event_source_files": len(guarded_private_files), "guarded_contract_test_files": len(contract_test_files), "guarded_production_files": len(public_files), "private_exports": 0, "stock_faults": len(stock_snippets), "mutation_faults": len(mutation_snippets), "public_faults": 1}


if __name__ == "__main__":
    H.run([
        ("permit_ledger", test_permit_ledger),
        ("ordering_receipt_failure", test_ordering_receipt_failure),
        ("static_public_guards", test_static_and_public_guards),
    ])
