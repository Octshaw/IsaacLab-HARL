"""B2-R2 real HARL autograd probes with optimizer/live-ValueNorm trapped."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r2_gradient_probe_helpers as H  # noqa: E402


def _actor_kwargs(ctx, *, data, frozen, batch, ledger=None, permit=None, machine=None, **changes):
    values = dict(
        authority=ctx["authority"],
        frozen_inputs=frozen,
        actor_plan=ctx["actor_plan"],
        minibatch_plan=batch,
        actor_id=batch.actor_id,
        actors=ctx["components"].actors,
        critic=ctx["components"].critic,
        live_value_normalizer=ctx["components"].live_value_normalizer,
        state_machine=H.actor_state_machine() if machine is None else machine,
        ledger=ledger,
        permit=permit,
        obs=data.obs,
        rnn_states=data.rnn_states,
        actions=data.actions,
        masks=data.masks,
        available_actions=data.available_actions,
        behavior_old_logprobs=data.behavior_old_logprobs,
        behavior_old_logprob_digest=H.E.fingerprint_tensor_v1(data.behavior_old_logprobs).content_digest,
        advantages=data.advantages,
        factor=data.factor,
        decision_valid_mask=data.decision_valid_mask,
        active_mask=data.active_mask,
        counter=ctx["counter"],
    )
    values.update(changes)
    return values


def _critic_kwargs(ctx, *, data, frozen, ledger=None, permit=None, machine=None, **changes):
    values = dict(
        authority=ctx["authority"],
        frozen_inputs=frozen,
        critic_plan=ctx["critic_plan"],
        epoch=0,
        minibatch=0,
        actors=ctx["components"].actors,
        critic=ctx["components"].critic,
        live_value_normalizer=ctx["components"].live_value_normalizer,
        state_machine=H.critic_state_machine() if machine is None else machine,
        ledger=ledger,
        permit=permit,
        shared_obs=data.shared_obs,
        rnn_states=data.rnn_states,
        masks=data.masks,
        value_preds=data.value_preds,
        critic_returns_storage=data.returns_storage,
        counter=ctx["counter"],
    )
    values.update(changes)
    return values


def _context():
    components = H.make_components()
    authority = H.make_probe_authority()
    actor_data = H.make_actor_data(components)
    critic_data = H.make_critic_data()
    actor_plan = H.make_actor_plan(authority, actor_data)
    critic_plan = H.make_critic_plan(authority, critic_data)
    behavior_digest = H.E.fingerprint_tensor_v1(actor_data.behavior_old_logprobs).content_digest
    target_digest = H.E.fingerprint_tensor_v1(critic_data.returns_storage[:-1].reshape(H.B, 1)).content_digest
    frozen = H.make_frozen_inputs(authority, behavior_digest=behavior_digest, critic_target_digest=target_digest)
    return {
        "components": components,
        "authority": authority,
        "actor_data": actor_data,
        "critic_data": critic_data,
        "actor_plan": actor_plan,
        "critic_plan": critic_plan,
        "frozen": frozen,
        "counter": H.G.B2RProbeExecutionCounterV1(),
    }


def _snapshot(ctx, *, frozen=None, plan=None, factor="actor"):
    return H.G.capture_probe_snapshot_v1(
        authority=ctx["authority"],
        frozen_inputs=ctx["frozen"] if frozen is None else frozen,
        plan_digest=(ctx["actor_plan"] if plan is None else plan).plan_digest,
        factor=ctx["actor_data"].factor if factor == "actor" else None,
        actor_bindings=H.actor_bindings(ctx["components"]),
        critic_binding=H.critic_binding(ctx["components"]),
        live_value_normalizer=ctx["components"].live_value_normalizer,
    )


def _permit(ctx, *, frozen, plan, factor, component_kind, owner, actor_id, stage, indices, permit_id, **changes):
    return H.make_permit(
        authority=ctx["authority"],
        components=ctx["components"],
        frozen_inputs=frozen,
        plan=plan,
        factor=factor,
        component_kind=component_kind,
        owner_identity=owner,
        actor_id=actor_id,
        stage=stage,
        epoch=0,
        minibatch=0,
        indices=indices,
        permit_id=permit_id,
        **changes,
    )


def run_actor_cases(ctx) -> dict[str, object]:
    C, G = H.C, H.G
    data = ctx["actor_data"]
    mixed = next(item for item in ctx["actor_plan"].minibatches if item.actor_id == 0)
    forced = next(item for item in ctx["actor_plan"].minibatches if item.actor_id == 1)
    forced_data = replace(
        data,
        actions=torch.full_like(data.actions, H.TASKS),
        behavior_old_logprobs=torch.zeros_like(data.behavior_old_logprobs),
        decision_valid_mask=torch.zeros_like(data.decision_valid_mask),
        active_mask=torch.zeros_like(data.active_mask),
    )
    forced_frozen = H.make_frozen_inputs(
        ctx["authority"],
        behavior_digest=H.E.fingerprint_tensor_v1(forced_data.behavior_old_logprobs).content_digest,
        critic_target_digest=ctx["critic_plan"].raw_target_digest,
    )
    forced_receipt = G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=forced_data, frozen=forced_frozen, batch=forced))
    H.assert_true(forced_receipt.backward_executed == 0 and forced_receipt.factor_unchanged, "forced-only skip")

    permit1, ledger1 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["actor_plan"], factor=data.factor,
        component_kind="actor", owner="actor0", actor_id=0, stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        indices=mixed.active_and_dvm_loss_indices, permit_id="actor-success-original",
    )
    original = G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, ledger=ledger1, permit=permit1))
    H.assert_true(original.backward_executed == 1 and original.gradient_audit.any_nonzero, "mixed real actor gradient")
    H.assert_true(mixed.dvm_evaluation_indices == (0, 1, 3, 4) and mixed.active_and_dvm_loss_indices == (0, 3), "mixed row plan")

    perturbed_behavior = data.behavior_old_logprobs.clone()
    perturbed_behavior[2, 0] = 17.0
    perturbed_behavior[5, 0] = -23.0
    perturbed_data = replace(data, behavior_old_logprobs=perturbed_behavior)
    perturbed_frozen = H.make_frozen_inputs(
        ctx["authority"],
        behavior_digest=H.E.fingerprint_tensor_v1(perturbed_behavior).content_digest,
        critic_target_digest=ctx["critic_plan"].raw_target_digest,
    )
    permit2, ledger2 = _permit(
        ctx, frozen=perturbed_frozen, plan=ctx["actor_plan"], factor=data.factor,
        component_kind="actor", owner="actor0", actor_id=0, stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        indices=mixed.active_and_dvm_loss_indices, permit_id="actor-success-excluded-perturbation",
    )
    perturbed = G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=perturbed_data, frozen=perturbed_frozen, batch=mixed, ledger=ledger2, permit=permit2))
    H.assert_true(original.loss_value == perturbed.loss_value, "off-DVM sentinel altered selected loss")
    H.assert_true(original.gradient_audit.evidence_digest == perturbed.gradient_audit.evidence_digest, "off-DVM sentinel altered selected gradient")

    foreign_term = next(ctx["components"].critic.critic.parameters()).sum() * 0.0
    permit3, ledger3 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["actor_plan"], factor=data.factor,
        component_kind="actor", owner="actor0", actor_id=0, stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        indices=mixed.active_and_dvm_loss_indices, permit_id="actor-foreign-gradient",
    )
    H.expect_stop(G.STOP_MUTATION_ATTRIBUTION, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, ledger=ledger3, permit=permit3, synthetic_fault_loss_term=foreign_term)))

    infinite_term = H.FiniteForwardInfiniteBackward.apply(next(ctx["components"].actors[0].actor.parameters()))
    permit4, ledger4 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["actor_plan"], factor=data.factor,
        component_kind="actor", owner="actor0", actor_id=0, stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        indices=mixed.active_and_dvm_loss_indices, permit_id="actor-nonfinite-gradient",
    )
    H.expect_stop(G.STOP_NONFINITE_GRADIENT, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, ledger=ledger4, permit=permit4, synthetic_fault_loss_term=infinite_term)))
    H.assert_true(ctx["counter"].actor_backward_executed == 4, "actor backward exact count")
    H.G.validate_gradients_clear_v1(tuple((f"actor{i}", actor.actor) for i, actor in enumerate(ctx["components"].actors)) + (("critic", ctx["components"].critic.critic),))
    return {
        "forced_backward": 0,
        "successful_backward": 2,
        "fault_backward": 2,
        "total_actor_backward": ctx["counter"].actor_backward_executed,
        "mixed_evaluation_rows": len(mixed.dvm_evaluation_indices),
        "mixed_loss_rows": len(mixed.active_and_dvm_loss_indices),
        "aggregate_gradient_norm": original.aggregate_gradient_norm,
        "excluded_perturbation_exact": True,
    }


def run_actor_faults(ctx) -> dict[str, object]:
    C, G = H.C, H.G
    data = ctx["actor_data"]
    mixed = next(item for item in ctx["actor_plan"].minibatches if item.actor_id == 0)
    forced = next(item for item in ctx["actor_plan"].minibatches if item.actor_id == 1)
    forced_data = replace(data, actions=torch.full_like(data.actions, H.TASKS), behavior_old_logprobs=torch.zeros_like(data.behavior_old_logprobs), decision_valid_mask=torch.zeros_like(data.decision_valid_mask), active_mask=torch.zeros_like(data.active_mask))
    forced_frozen = H.make_frozen_inputs(ctx["authority"], behavior_digest=H.E.fingerprint_tensor_v1(forced_data.behavior_old_logprobs).content_digest, critic_target_digest=ctx["critic_plan"].raw_target_digest)
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed)))
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, ledger=ctx["consumed_ledger"], permit=ctx["consumed_permit"])))
    for name, expected, changes in (
        ("wrong-actor", C.STOP_UNAUTHORIZED_BACKWARD, {"override_actor_id": 1}),
        ("wrong-minibatch", C.STOP_UNAUTHORIZED_BACKWARD, {"override_minibatch": 1}),
        ("stale-config", H.E.STOP_AUTHORITY_DRIFT, {"override_config_digest": H.R1.digest("stale-config")}),
        ("stale-update", H.E.STOP_AUTHORITY_DRIFT, {"override_update_id": "stale-update"}),
    ):
        permit, ledger = _permit(
            ctx, frozen=ctx["frozen"], plan=ctx["actor_plan"], factor=data.factor,
            component_kind="actor", owner="actor0", actor_id=0, stage=C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
            indices=mixed.active_and_dvm_loss_indices, permit_id=name, **changes,
        )
        H.expect_stop(expected, lambda permit=permit, ledger=ledger: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, ledger=ledger, permit=permit)))
    H.expect_stop(C.STOP_UNAUTHORIZED_BACKWARD, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=forced_data, frozen=forced_frozen, batch=forced, attempt_backward_when_empty=True)))
    H.expect_stop(H.P.STOP_FORCED_ROW_POLICY_LEAK, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, claimed_loss_indices=(0, 2, 3))))
    H.expect_stop(H.P.STOP_FORCED_ROW_POLICY_LEAK, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, claimed_loss_indices=(0, 1, 3))))
    H.expect_stop(H.E.STOP_ACTOR_EVIDENCE_BINDING, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, behavior_old_logprob_digest=H.R1.digest("wrong-behavior"))))
    H.expect_stop(H.E.STOP_ACTOR_EVIDENCE_BINDING, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, claimed_partition_indices=(0, 1, 2, 3, 4))))
    bad_advantages = data.advantages.clone(); bad_advantages[0, 0] = float("nan")
    H.expect_stop(G.STOP_NONFINITE_LOSS, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=replace(data, advantages=bad_advantages), frozen=ctx["frozen"], batch=mixed)))
    H.expect_stop(C.STOP_MODE_ORDER, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, machine=C.B2RUpdateStateMachineV1())))
    poisoned = H.actor_state_machine(); poisoned.poison()
    H.expect_stop(C.STOP_MODE_ORDER, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=data, frozen=ctx["frozen"], batch=mixed, machine=poisoned)))
    dirty = next(ctx["components"].actors[1].actor.parameters()); dirty.grad = torch.zeros_like(dirty)
    H.expect_stop(G.STOP_MUTATION_ATTRIBUTION, lambda: G.probe_actor_backward_v1(**_actor_kwargs(ctx, data=forced_data, frozen=forced_frozen, batch=forced)))
    dirty.grad = None
    dirty.grad = torch.ones_like(dirty)
    H.expect_stop(G.STOP_MUTATION_ATTRIBUTION, lambda: G.validate_gradients_clear_v1((("actor1", ctx["components"].actors[1].actor),)))
    dirty.grad = None
    H.assert_true(ctx["counter"].actor_backward_executed == 4, "actor faults executed extra backward")
    return {"faults": 16, "extra_backward": 0}


def run_critic_cases_and_faults(ctx) -> dict[str, object]:
    C, G = H.C, H.G
    data = ctx["critic_data"]
    partition = ctx["critic_plan"].partitions_by_epoch[0][0]
    permit1, ledger1 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["critic_plan"], factor=None,
        component_kind="critic", owner="critic", actor_id=None, stage=C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE,
        indices=partition, permit_id="critic-success",
    )
    success = G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=data, frozen=ctx["frozen"], ledger=ledger1, permit=permit1))
    H.assert_true(success.backward_executed == 1 and success.gradient_audit.any_nonzero, "real critic gradient")
    H.assert_true(success.raw_target_digest == ctx["critic_plan"].raw_target_digest, "returns[:-1] target binding")

    foreign_term = next(ctx["components"].actors[0].actor.parameters()).sum() * 0.0
    permit2, ledger2 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["critic_plan"], factor=None,
        component_kind="critic", owner="critic", actor_id=None, stage=C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE,
        indices=partition, permit_id="critic-foreign-gradient",
    )
    H.expect_stop(G.STOP_MUTATION_ATTRIBUTION, lambda: G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=data, frozen=ctx["frozen"], ledger=ledger2, permit=permit2, synthetic_fault_loss_term=foreign_term)))

    infinite_term = H.FiniteForwardInfiniteBackward.apply(next(ctx["components"].critic.critic.parameters()))
    permit3, ledger3 = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["critic_plan"], factor=None,
        component_kind="critic", owner="critic", actor_id=None, stage=C.B2RUpdateStageV1.S6_CRITIC_SEQUENCE,
        indices=partition, permit_id="critic-nonfinite-gradient",
    )
    H.expect_stop(G.STOP_NONFINITE_GRADIENT, lambda: G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=data, frozen=ctx["frozen"], ledger=ledger3, permit=permit3, synthetic_fault_loss_term=infinite_term)))
    H.assert_true(ctx["counter"].critic_backward_executed == 3, "critic backward exact count")

    H.expect_stop(G.STOP_CRITIC_TRAINING_SLICE, lambda: G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=data, frozen=ctx["frozen"], claimed_target_digest=H.R1.digest("wrong-target"))))
    nonfinite_storage = data.returns_storage.clone(); nonfinite_storage[0, 0, 0] = float("nan")
    H.expect_stop(G.STOP_NONFINITE_TARGET, lambda: G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=replace(data, returns_storage=nonfinite_storage), frozen=ctx["frozen"])))
    H.expect_stop(G.STOP_NONFINITE_LOSS, lambda: G.probe_critic_backward_v1(**_critic_kwargs(ctx, data=data, frozen=ctx["frozen"], synthetic_fault_loss_term=torch.tensor(float("nan")))))
    H.G.validate_gradients_clear_v1(tuple((f"actor{i}", actor.actor) for i, actor in enumerate(ctx["components"].actors)) + (("critic", ctx["components"].critic.critic),))
    return {
        "successful_backward": 1,
        "fault_backward": 2,
        "total_critic_backward": ctx["counter"].critic_backward_executed,
        "physical_target_rows": len(partition),
        "aggregate_gradient_norm": success.aggregate_gradient_norm,
        "target_faults": 3,
    }


def run_traps_and_guards(ctx) -> dict[str, object]:
    G, SG = H.G, H.SG
    actor = ctx["components"].actors[0]
    critic = ctx["components"].critic
    live = ctx["components"].live_value_normalizer
    actor_before = H.E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=actor.actor, optimizer=actor.actor_optimizer)
    actor_step_trap = G.B2ROptimizerStepTrapV1(component_kind="actor", owner_identity="actor0", module=actor.actor, optimizer=actor.actor_optimizer, counter=ctx["counter"])
    H.expect_stop(H.C.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda: actor_step_trap.step())
    actor_after = H.E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=actor.actor, optimizer=actor.actor_optimizer)
    H.assert_true(actor_before == actor_after, "actor step trap mutated state")
    critic_before = H.E.fingerprint_component_v1(component_kind="critic", owner_identity="critic", module=critic.critic, optimizer=critic.critic_optimizer)
    critic_step_trap = G.B2ROptimizerStepTrapV1(component_kind="critic", owner_identity="critic", module=critic.critic, optimizer=critic.critic_optimizer, counter=ctx["counter"])
    H.expect_stop(H.C.STOP_UNAUTHORIZED_OPTIMIZER_STEP, lambda: critic_step_trap.step())
    critic_after = H.E.fingerprint_component_v1(component_kind="critic", owner_identity="critic", module=critic.critic, optimizer=critic.critic_optimizer)
    H.assert_true(critic_before == critic_after, "critic step trap mutated state")
    vn_before = H.E.fingerprint_component_v1(component_kind="live_valuenorm", owner_identity="live_valuenorm", value_normalizer=live)
    live_valuenorm_trap = G.B2RLiveValueNormTrapV1(value_normalizer=live, counter=ctx["counter"])
    H.expect_stop(H.E.STOP_VALUENORM, lambda: live_valuenorm_trap.update(torch.ones((2, 1))))
    vn_after = H.E.fingerprint_component_v1(component_kind="live_valuenorm", owner_identity="live_valuenorm", value_normalizer=live)
    H.assert_true(vn_before == vn_after, "live ValueNorm trap mutated state")

    source_files = (
        H.R1.SCAN_SOURCE / "assignment_event_training_gradient_probe.py",
        H.R1.SCAN_SOURCE / "assignment_event_training_gradient_guards.py",
        Path(__file__).resolve().parent / "_assignment_phase_b2_r2_gradient_probe_helpers.py",
        Path(__file__).resolve(),
    )
    guard = SG.validate_r2_gradient_source_guards_v1(source_files)
    H.assert_true(guard.backward_call_count == 1 and guard.violation_count == 0, "R2 source guard")
    private_paths = set(source_files[:2])
    non_r2_files = tuple(sorted(path for path in H.R1.SCAN_SOURCE.glob("*.py") if path not in private_paths))
    private_training_files = set(H.R1.SCAN_SOURCE.glob("assignment_event_training_*.py"))
    production_files = tuple(sorted(path for path in H.R1.SCAN_SOURCE.glob("*.py") if path not in private_training_files))
    non_r2 = SG.validate_r2_public_isolation_v1(non_r2_files, private_tokens=("assignment_event_training_gradient_probe", "assignment_event_training_gradient_guards"))
    public = SG.validate_r2_public_isolation_v1(production_files, private_tokens=("assignment_event_training_gradient_probe", "assignment_event_training_gradient_guards"))
    H.assert_true(non_r2.violation_count == 0 and public.violation_count == 0, "R2 public isolation")
    for stop, source in (
        (SG.STOP_UNAUTHORIZED_BACKWARD, "loss.backward()"),
        (SG.STOP_UNAUTHORIZED_OPTIMIZER_STEP, "optimizer.step()"),
        (SG.STOP_VALUENORM, "live_valuenorm.update(values)"),
        (SG.STOP_STOCK_FULL_ROW_ACTOR_PATH, "HAPPO.update()"),
        (SG.STOP_CRITIC_TRAINING_SLICE, "VCritic.train()"),
        (SG.STOP_STOCK_RETURNS_BYPASS, "critic_buffer.compute_returns()"),
    ):
        H.expect_stop(stop, lambda stop=stop, source=source: SG.validate_r2_source_text_fault_v1(source, identity=stop))
    return {
        "optimizer_step_attempts_trapped": ctx["counter"].optimizer_step_attempted,
        "optimizer_step_executed": ctx["counter"].optimizer_step_executed,
        "live_valuenorm_attempts_trapped": ctx["counter"].live_valuenorm_update_attempted,
        "live_valuenorm_updates_executed": ctx["counter"].live_valuenorm_update_executed,
        "centralized_backward_calls_in_source": guard.backward_call_count,
        "guarded_r2_files": len(source_files),
        "guarded_non_r2_repo_files": len(non_r2_files),
        "guarded_production_files": len(production_files),
        "source_faults": 6,
    }


def main() -> None:
    ctx = _context()
    initial = _snapshot(ctx)
    actor_results = run_actor_cases(ctx)
    mixed = next(item for item in ctx["actor_plan"].minibatches if item.actor_id == 0)
    consumed_permit, consumed_ledger = _permit(
        ctx, frozen=ctx["frozen"], plan=ctx["actor_plan"], factor=ctx["actor_data"].factor,
        component_kind="actor", owner="actor0", actor_id=0, stage=H.C.B2RUpdateStageV1.S5_ACTOR_SEQUENCE,
        indices=mixed.active_and_dvm_loss_indices, permit_id="duplicate-control",
    )
    consumed_ledger.consume(
        permit_id=consumed_permit.permit_id,
        operation=H.C.B2RPermitOperationV1.BACKWARD,
        update_id=consumed_permit.update_id,
        authority_config_digest=consumed_permit.authority_config_digest,
        component_kind=consumed_permit.component_kind,
        owner_identity=consumed_permit.owner_identity,
        actor_id=consumed_permit.actor_id,
        stage=consumed_permit.stage,
        epoch=consumed_permit.epoch,
        minibatch=consumed_permit.minibatch,
        canonical_index_digest=consumed_permit.canonical_index_digest,
        precondition_fingerprint_digest=consumed_permit.precondition_fingerprint_digest,
    )
    ctx["consumed_permit"], ctx["consumed_ledger"] = consumed_permit, consumed_ledger
    actor_faults = run_actor_faults(ctx)
    critic_results = run_critic_cases_and_faults(ctx)
    trap_results = run_traps_and_guards(ctx)
    final = _snapshot(ctx)
    H.assert_true(initial == final, "global pre/post snapshot drift")
    counter = ctx["counter"]
    H.assert_true(counter.actor_backward_executed == ctx["authority"].expected_actor_backward_count, "authority actor count")
    H.assert_true(counter.critic_backward_executed == ctx["authority"].expected_critic_backward_count, "authority critic count")
    H.assert_true(counter.optimizer_step_executed == 0 and counter.live_valuenorm_update_executed == 0, "forbidden execution count")
    print(json.dumps({
        "status": "PASS",
        "real": {"installed_happo_actors": 3, "installed_vcritic": 1, "real_autograd": True, "real_gradients": True},
        "synthetic": {"rollout_rows": H.B, "dvm_fixture": True, "returns_fixture": True, "disposable_valuenorm": True},
        "actor": actor_results,
        "actor_faults": actor_faults,
        "critic": critic_results,
        "traps_guards": trap_results,
        "execution_counts": {
            "actor_backward": counter.actor_backward_executed,
            "critic_backward": counter.critic_backward_executed,
            "total_backward": counter.total_backward_executed,
            "optimizer_step": counter.optimizer_step_executed,
            "scheduler_step": 0,
            "actor_parameter_mutations": 0,
            "critic_parameter_mutations": 0,
            "optimizer_state_mutations": 0,
            "live_valuenorm_updates": counter.live_valuenorm_update_executed,
            "isaac_runtime_rollout_actions": 0,
            "training_actions": 0,
            "evaluation_playback_actions": 0,
            "checkpoint_weight_io": 0,
            "public_route_activations": 0,
        },
        "global_snapshot_exact": initial.snapshot_digest == final.snapshot_digest,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
