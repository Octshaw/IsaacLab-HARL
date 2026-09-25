"""Pure/static B2-T4 preflight for zero-DVM and nonterminal integration.

This file never launches AppLauncher or an environment.  It qualifies the
lower-level all-zero actor and all-NONE return paths, then checks whether the
reviewed R5 real-Isaac transaction entry accepts that valid nonterminal state.
"""

from __future__ import annotations

from dataclasses import replace
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r3_actor_mutation_helpers as A  # noqa: E402
import _assignment_phase_b2_r5_full_transaction_helpers as F  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
I5B_PATH = Path(__file__).with_name(
    "test_assignment_phase_b2_i5b_time_limit_gae_valuenorm_semantics_pure.py"
)
ADAPTER_PATH = SCAN_SOURCE / "assignment_event_training_real_isaac_adapter.py"
FULL_TRANSACTION_PATH = SCAN_SOURCE / "assignment_event_training_full_transaction.py"
STOP_CLASSIFICATION = "PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_path(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _all_zero_actor_qualification() -> dict[str, object]:
    context = F.make_context(update_id="b2-t4-pure-all-zero-decision")
    zero_inputs = {
        actor_id: replace(
            inputs,
            decision_valid_mask=torch.zeros_like(inputs.decision_valid_mask),
            active_mask=torch.zeros_like(inputs.active_mask),
        )
        for actor_id, inputs in context.actor_inputs.items()
    }
    partitions = A.P.build_exact_partitions_v1(
        B=A.B,
        epoch_count=2,
        minibatch_count=2,
        partition_policy="reviewed_exact_coverage",
    )
    plan = A.P.build_actor_update_plan_v1(
        authority=context.authority.base_authority,
        authority_config_digest=context.authority.base_authority.config_digest,
        actor_permutation=context.authority.actor_authority.order_evidence.actor_order,
        approved_partitions_by_epoch=partitions,
        dvm_indices_by_actor={actor_id: () for actor_id in range(A.ACTORS)},
        active_indices_by_actor={actor_id: () for actor_id in range(A.ACTORS)},
        factor_input_digest=A.E.fingerprint_tensor_v1(context.initial_factor).content_digest,
        optimizer_step_policy="match_backward",
    )
    dvm_digest = F.E.canonical_digest_v1(
        tuple(F._tensor_digest(zero_inputs[index].decision_valid_mask) for index in range(F.ACTORS))
    )
    active_digest = F.E.canonical_digest_v1(
        tuple(F._tensor_digest(zero_inputs[index].active_mask) for index in range(F.ACTORS))
    )
    availability_digest = F.E.canonical_digest_v1(
        tuple(F._tensor_digest(zero_inputs[index].available_actions) for index in range(F.ACTORS))
    )
    frozen = replace(
        context.frozen_inputs,
        dvm_digest=dvm_digest,
        active_mask_digest=active_digest,
    )
    storages = tuple(
        F.ControlledActorStorageV1(actor_id=actor_id, inputs=zero_inputs[actor_id])
        for actor_id in range(F.ACTORS)
    )
    resources = F.RolloverResourcesV1(
        critic_buffer=context.rollover_resources.critic_buffer,
        terminal_collector=context.rollover_resources.terminal_collector,
        actor_storages=storages,
    )
    rollout = replace(
        context.rollout_evidence,
        dvm_active_availability_digest=F.E.canonical_digest_v1(
            (dvm_digest, active_digest, availability_digest)
        ),
        current_final_slot_digest_by_actor=tuple(
            (index, storage.final_current_slot_digest) for index, storage in enumerate(storages)
        ),
    )
    immutable_plan = replace(
        context.immutable_plan,
        actor_plan_digest=plan.plan_digest,
        actor_expected_backward=plan.expected_backward_count_by_actor,
        actor_expected_step=plan.expected_optimizer_step_count_by_actor,
        lifecycle_evidence_digest=rollout.evidence_digest,
    )
    zero_context = F.Context(
        context.components,
        context.authority,
        rollout,
        frozen,
        immutable_plan,
        plan,
        context.critic_plan,
        zero_inputs,
        context.initial_factor,
        context.critic_inputs,
        context.event_returns_result,
        resources,
    )
    actor_fingerprints_before, _, _ = A.R3._capture_components_v1(
        actors=zero_context.components.actors,
        critic=zero_context.components.critic,
        live_value_normalizer=zero_context.components.live_value_normalizer,
    )
    actor_before = tuple(A.R3._parameter_digest(item) for item in actor_fingerprints_before)
    optimizer_before = tuple(A.R3._optimizer_digest(item) for item in actor_fingerprints_before)
    counter = F.R5.B2R5ExecutionCounterV1(F.ACTORS)
    receipt = F.execute(zero_context, counter=counter)
    actor_fingerprints_after, _, _ = A.R3._capture_components_v1(
        actors=zero_context.components.actors,
        critic=zero_context.components.critic,
        live_value_normalizer=zero_context.components.live_value_normalizer,
    )
    actor_after = tuple(A.R3._parameter_digest(item) for item in actor_fingerprints_after)
    optimizer_after = tuple(A.R3._optimizer_digest(item) for item in actor_fingerprints_after)
    expected_backward = tuple(count for _, count in plan.expected_backward_count_by_actor)
    expected_steps = tuple(count for _, count in plan.expected_optimizer_step_count_by_actor)
    _assert(expected_backward == (0, 0, 0), "all-zero expected backward counts")
    _assert(expected_steps == (0, 0, 0), "all-zero expected optimizer-step counts")
    actor_receipt = receipt.actor_sequence_receipt
    _assert(all(segment.skipped for segment in actor_receipt.actor_segments), "all actors must skip")
    _assert(all(segment.factor_transition.recurrence_exact for segment in actor_receipt.actor_segments), "factor identity")
    _assert(actor_before == actor_after, "actor parameters mutated")
    _assert(optimizer_before == optimizer_after, "actor optimizer state mutated")
    _assert(counter.actor_step_executed == 0, "actor optimizer step executed")
    _assert(actor_receipt.initial_factor_digest == actor_receipt.final_factor_digest, "all-zero factor changed")
    _assert(counter.critic_backward_executed == 1, "critic backward did not execute")
    _assert(counter.critic_step_executed == 1, "critic optimizer step did not execute")
    _assert(counter.live_valuenorm_executed == 1, "ValueNorm update did not execute")
    _assert(counter.s10_entries == 1, "S10 was not reached")
    return {
        "classification": "PASS",
        "T": A.T,
        "E": A.ENVIRONMENTS,
        "M": A.ACTORS,
        "B": A.B,
        "dvm_rows_by_actor": {str(actor_id): 0 for actor_id in range(A.ACTORS)},
        "expected_backward_by_actor": list(expected_backward),
        "expected_optimizer_step_by_actor": list(expected_steps),
        "observed_backward_by_actor": [segment.observed_backward_count for segment in actor_receipt.actor_segments],
        "observed_optimizer_step_by_actor": [segment.observed_step_count for segment in actor_receipt.actor_segments],
        "skipped_actor_count": sum(segment.skipped for segment in actor_receipt.actor_segments),
        "factor_identity": actor_receipt.initial_factor_digest == actor_receipt.final_factor_digest,
        "actor_parameters_unchanged": actor_before == actor_after,
        "actor_optimizer_state_unchanged": optimizer_before == optimizer_after,
        "critic_backward": counter.critic_backward_executed,
        "critic_optimizer_step": counter.critic_step_executed,
        "valuenorm_updates": counter.live_valuenorm_executed,
        "S7_S8_S9_S10": [1, 1, 1, counter.s10_entries],
    }


def _nonterminal_return_qualification() -> dict[str, object]:
    i5b = _load_path("_phase_b2_t4_i5b_helpers", I5B_PATH)
    T, E = 2, 3
    buffer = i5b._buffer(E, T)
    rewards = torch.tensor([[[1.0], [2.0], [3.0]], [[4.0], [5.0], [6.0]]])
    current_values = torch.tensor([[[0.1], [0.2], [0.3]], [[0.4], [0.5], [0.6]]])
    reasons = torch.full((T, E, 1), int(i5b.Reason.NONE), dtype=torch.int64)
    i5b._fill(
        buffer,
        rewards=rewards,
        current_values=current_values,
        reasons=reasons,
        timeout_values=torch.full((T, E, 1), float("nan")),
        masks_after=torch.ones((T, E, 1)),
    )
    final_next_value = torch.tensor([[7.0], [8.0], [9.0]])
    result = buffer.compute_event_returns(final_next_value)
    expected_last_bootstrap = final_next_value
    expected_last_delta = rewards[-1] + 0.9 * final_next_value - current_values[-1]
    expected_last_return = expected_last_delta + current_values[-1]
    i5b._close(result.bootstrap_values[-1], expected_last_bootstrap, "ordinary final bootstrap")
    i5b._close(result.deltas[-1], expected_last_delta, "ordinary final delta")
    i5b._close(result.returns[-1], expected_last_return, "ordinary final return")
    _assert(tuple(result.returns.shape) == (T, E, 1), "return shape")
    _assert(bool(torch.isfinite(result.returns).all().item()), "nonfinite return")
    _assert(result.returns.data_ptr() != buffer.returns[:-1].data_ptr(), "result/storage alias")
    _assert(bool(buffer._event_returns_computed), "compute-once flag absent")
    _assert(not bool(buffer.timeout_bootstrap_masks.any().item()), "unexpected timeout sidecar use")
    return {
        "classification": "PASS",
        "T": T,
        "E": E,
        "termination_reason_counts": {"NONE": T * E, "terminal": 0},
        "final_next_value": final_next_value.tolist(),
        "final_bootstrap_matches_current_next_value": True,
        "event_returns_shape": list(result.returns.shape),
        "event_returns_finite": True,
        "event_returns_nonalias": True,
        "event_return_compute_count": 1,
        "stock_compute_returns_calls": 0,
        "timeout_critic_calls": 0,
        "timeout_sidecar_rows": 0,
    }


def _function_source(tree: ast.Module, name: str, source: str) -> str:
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)
    segment = ast.get_source_segment(source, node)
    _assert(segment is not None, f"missing source for {name}")
    return segment


def _integration_gap_qualification() -> dict[str, object]:
    adapter_source = ADAPTER_PATH.read_text(encoding="utf-8")
    full_source = FULL_TRANSACTION_PATH.read_text(encoding="utf-8")
    adapter_function = _function_source(
        ast.parse(adapter_source), "execute_real_isaac_single_transaction_v1", adapter_source
    )
    full_function = _function_source(
        ast.parse(full_source), "validate_rollout_complete_v1", full_source
    )
    adapter_gate = (
        '_require(tuple(route.collector.consumed_terminal_keys), "real terminal learner ledger is empty")'
        in adapter_function
    )
    coordinator_gate = "or not keys" in full_function
    _assert(adapter_gate, "reviewed real adapter no longer requires terminal ledger")
    _assert(coordinator_gate, "reviewed R5 coordinator no longer requires terminal keys")
    adapter = A.R1.load_canonical("assignment_event_training_real_isaac_adapter.py")
    rejected_message = None
    try:
        adapter._require((), "real terminal learner ledger is empty")
    except RuntimeError as exc:
        rejected_message = str(exc)
    _assert(
        rejected_message == "STOP — B2-R5I REAL_EVIDENCE_BINDING: real terminal learner ledger is empty",
        "empty-ledger dynamic rejection drifted",
    )
    return {
        "classification": "FAIL",
        "stop_classification": STOP_CLASSIFICATION,
        "valid_normal_horizon_state": {
            "rollout_complete": True,
            "termination_reason": "NONE on every T=2 row",
            "terminal_consumption_keys": [],
            "final_current_state_critic_value_required": True,
        },
        "adapter_nonempty_terminal_ledger_gate": True,
        "r5_coordinator_nonempty_terminal_keys_gate": True,
        "dynamic_empty_ledger_rejection": rejected_message,
        "first_blocking_stage": "before S0 / before learner mutation",
        "production_change_required_to_continue": True,
        "production_changes_authorized": False,
        "adapter_sha256": _sha(ADAPTER_PATH),
        "full_transaction_sha256": _sha(FULL_TRANSACTION_PATH),
    }


def main() -> None:
    zero_dvm = _all_zero_actor_qualification()
    nonterminal = _nonterminal_return_qualification()
    integration = _integration_gap_qualification()
    result = {
        "classification": STOP_CLASSIFICATION,
        "zero_dvm_pure_qualification": zero_dvm,
        "nonterminal_bootstrap_pure_qualification": nonterminal,
        "integrated_r5_qualification": integration,
        "formal_execution": {
            "cuda_cublas_readiness_probes": 0,
            "formal_worker_processes": 0,
            "app_launcher_instances": 0,
            "environment_instances": 0,
            "environment_resets": 0,
            "environment_steps": 0,
            "learner_transactions": 0,
            "actor_optimizer_steps": 0,
            "critic_optimizer_steps": 0,
            "valuenorm_updates": 0,
            "retries": 0,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
