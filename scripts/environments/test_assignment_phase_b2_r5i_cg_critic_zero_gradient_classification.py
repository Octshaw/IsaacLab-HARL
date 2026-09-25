"""B2-R5I-CG controlled critic zero-effective-gradient qualification."""

from __future__ import annotations

from dataclasses import asdict
import json

import torch

import _assignment_phase_b2_r4_critic_mutation_helpers as R4H
import _assignment_phase_b2_r5_full_transaction_helpers as R5H


R4, G, E = R4H.R4, R4H.G, R4H.E


def _execute_r4(context):
    counter = R4.B2R4ExecutionCounterV1()
    receipt = R4.execute_critic_sequence_v1(
        authority=context.authority,
        frozen_inputs=context.frozen_inputs,
        critic_plan=context.plan,
        actors=context.components.actors,
        critic=context.components.critic,
        live_value_normalizer=context.components.live_value_normalizer,
        inputs=context.inputs,
        route_state=R4.B2R4RouteStateV1(),
        counter=counter,
    )
    return receipt, counter


def _zero_critic(critic) -> None:
    with torch.no_grad():
        for parameter in critic.critic.parameters():
            parameter.zero_()


def _gradient_rows(step) -> list[dict[str, object]]:
    return [asdict(item) for item in step.gradient_audit.parameters]


def exact_target_witness(*, device: torch.device, suffix: str) -> dict[str, object]:
    context = R4H.make_context(
        valuenorm_enabled=False, suffix=suffix, device=device
    )
    _zero_critic(context.components.critic)
    zeros = torch.zeros((context.B, 1), dtype=torch.float32, device=device)
    context = R4H.rebind_critic_targets(
        context, training_returns=zeros, frozen_value_predictions=zeros
    )
    receipt, counter = _execute_r4(context)
    R4H.assert_true(
        receipt.valid_nonzero_count == 0
        and receipt.valid_zero_effective_count == 2,
        "exact-target classes",
    )
    R4H.assert_true(
        (counter.critic_backward_executed, counter.critic_step_executed,
         counter.live_valuenorm_executed) == (2, 2, 0),
        "exact-target counts",
    )
    R4H.assert_true(
        all(
            step.loss_value == 0.0
            and step.loss_graph_evidence.d_loss_d_values_exact_zero
            and step.loss_decomposition.zero_effective_reason == "EXACT_TARGET"
            and step.gradient_audit.all_required_gradients_present
            and step.gradient_audit.all_present_gradients_exact_zero
            and not step.critic_parameter_mutated
            and step.critic_optimizer_mutated
            for step in receipt.step_receipts
        ),
        "exact-target evidence",
    )
    first = receipt.step_receipts[0]
    return {
        "device": str(device),
        "classification": [step.gradient_classification for step in receipt.step_receipts],
        "counts": [receipt.observed_backward_count, receipt.observed_step_count,
                   receipt.observed_valuenorm_count],
        "loss": [step.loss_value for step in receipt.step_receipts],
        "dLoss_dValues_norm": [step.loss_graph_evidence.d_loss_d_values_norm for step in receipt.step_receipts],
        "parameter_mutated": [step.critic_parameter_mutated for step in receipt.step_receipts],
        "optimizer_mutated": [step.critic_optimizer_mutated for step in receipt.step_receipts],
        "parameter_gradients": _gradient_rows(first),
        "loss_decomposition": asdict(first.loss_decomposition),
        "adam_state_before": [asdict(item) for item in first.adam_state_before],
        "adam_state_after": [asdict(item) for item in first.adam_state_after],
    }


def mixed_adam_witness() -> tuple[dict[str, object], object]:
    context = R4H.make_context(valuenorm_enabled=False, suffix="cg-mixed-adam")
    with torch.no_grad():
        initial, _ = context.components.critic.get_values(
            context.inputs.shared_obs, context.inputs.rnn_states, context.inputs.masks
        )
    initial = initial.detach().clone()
    training_returns = initial.clone()
    frozen = initial.clone()
    first_rows, second_rows = context.plan.partitions_by_epoch[0]
    training_returns[list(first_rows)] += 1.0
    frozen[list(second_rows)] -= 1.0
    context = R4H.rebind_critic_targets(
        context,
        training_returns=training_returns,
        frozen_value_predictions=frozen,
    )
    receipt, counter = _execute_r4(context)
    classes = tuple(step.gradient_classification for step in receipt.step_receipts)
    R4H.assert_true(
        classes == (G.VALID_NONZERO_UPDATE, G.VALID_ZERO_EFFECTIVE_UPDATE),
        f"mixed Adam classes: {classes}",
    )
    second = receipt.step_receipts[1]
    R4H.assert_true(
        second.loss_value > 0.0
        and second.loss_graph_evidence.d_loss_d_values_exact_zero
        and second.loss_decomposition.zero_effective_reason == "CLIPPED_VALUE_PLATEAU"
        and all(
            sample.selected_branch == "clipped"
            and sample.zero_derivative_reason == "CLIPPED_VALUE_PLATEAU"
            and sample.d_loss_d_current_value == 0.0
            for sample in second.loss_decomposition.samples
        ),
        "clipped plateau evidence",
    )
    before_by_name = {item.parameter_name: item for item in second.adam_state_before}
    after_by_name = {item.parameter_name: item for item in second.adam_state_after}
    nonempty_moment_names = tuple(
        name for name, item in before_by_name.items()
        if item.state_present and item.exp_avg_norm is not None and item.exp_avg_norm > 0.0
    )
    R4H.assert_true(nonempty_moment_names, "Adam moments were not initialized")
    R4H.assert_true(
        all(
            after_by_name[name].step == before_by_name[name].step + 1.0
            for name in before_by_name
        ),
        "Adam step counters",
    )
    R4H.assert_true(
        second.critic_parameter_mutated and second.critic_optimizer_mutated,
        "existing Adam moments must produce attributable state/parameter movement",
    )
    return ({
        "classification": list(classes),
        "counts": [counter.critic_backward_executed, counter.critic_step_executed,
                   counter.live_valuenorm_executed],
        "second_loss": second.loss_value,
        "second_dLoss_dValues_norm": second.loss_graph_evidence.d_loss_d_values_norm,
        "second_parameter_mutated": second.critic_parameter_mutated,
        "second_optimizer_mutated": second.critic_optimizer_mutated,
        "nonempty_moment_parameter_count": len(nonempty_moment_names),
        "adam_step_before_after": {
            name: [before_by_name[name].step, after_by_name[name].step]
            for name in nonempty_moment_names
        },
        "adam_state_before": [asdict(item) for item in second.adam_state_before],
        "adam_state_after": [asdict(item) for item in second.adam_state_after],
        "parameter_gradients": _gradient_rows(second),
        "loss_decomposition": asdict(second.loss_decomposition),
    }, context)


def r5_mixed_s10_witness() -> dict[str, object]:
    context = R5H.make_context(
        update_id="b2-r5i-cg-mixed-s10",
        critic_minibatches=2,
        valuenorm_enabled=False,
    )
    with torch.no_grad():
        initial, _ = context.components.critic.get_values(
            context.critic_inputs.shared_obs,
            context.critic_inputs.rnn_states,
            context.critic_inputs.masks,
        )
    initial = initial.detach().clone()
    training_returns = initial.clone()
    frozen = initial.clone()
    first_rows, second_rows = context.critic_plan.partitions_by_epoch[0]
    training_returns[list(first_rows)] += 1.0
    frozen[list(second_rows)] -= 1.0
    context = R5H.rebind_critic_targets(
        context,
        training_returns=training_returns,
        frozen_value_predictions=frozen,
    )
    counter = R5H.R5.B2R5ExecutionCounterV1(R5H.ACTORS)
    receipt = R5H.execute(context, counter=counter)
    critic_receipt = receipt.critic_sequence_receipt
    classes = tuple(item.gradient_classification for item in critic_receipt.step_receipts)
    R5H.assert_true(
        classes == (G.VALID_NONZERO_UPDATE, G.VALID_ZERO_EFFECTIVE_UPDATE),
        f"R5 mixed classes: {classes}",
    )
    R5H.assert_true(counter.s10_entries == counter.successful_transactions == 1, "R5 S10")
    R5H.assert_true(
        (critic_receipt.observed_backward_count, critic_receipt.observed_step_count,
         critic_receipt.observed_valuenorm_count) == (2, 2, 0),
        "R5 critic counts",
    )
    second = critic_receipt.step_receipts[1]
    R5H.assert_true(
        second.critic_parameter_mutated
        and second.critic_optimizer_mutated
        and all(item.step == 1.0 for item in second.adam_state_before)
        and all(item.step == 2.0 for item in second.adam_state_after),
        "R5 mixed existing-moment Adam evidence",
    )
    return {
        "classification": list(classes),
        "critic_counts": [critic_receipt.observed_backward_count,
                          critic_receipt.observed_step_count,
                          critic_receipt.observed_valuenorm_count],
        "S6_complete": True,
        "S7_pass": True,
        "S8_pass": True,
        "S9_rollover": counter.critic_rollovers == 1,
        "S10": counter.s10_entries,
        "successful_transactions": counter.successful_transactions,
        "zero_step_parameter_mutated": second.critic_parameter_mutated,
        "zero_step_optimizer_mutated": second.critic_optimizer_mutated,
        "adam_step_before_after": [
            second.adam_state_before[0].step, second.adam_state_after[0].step
        ],
    }


class _TwoParameterModule(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.used = torch.nn.Parameter(torch.tensor([1.0]))
        self.unused = torch.nn.Parameter(torch.tensor([2.0]))


class _FiniteForwardInfiniteBackward(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value):
        ctx.input_shape = value.shape
        return value.new_zeros(())

    @staticmethod
    def backward(ctx, grad_output):
        return torch.full(
            ctx.input_shape,
            float("inf"),
            dtype=grad_output.dtype,
            device=grad_output.device,
        )


def negative_classification_witnesses() -> dict[str, object]:
    faults: dict[str, str] = {}

    values = torch.zeros((2, 1), requires_grad=True)
    target = torch.zeros_like(values)
    frozen = torch.zeros_like(values)
    unrelated = torch.ones((2, 1), requires_grad=True)
    cases = {
        "loss_detached": lambda: G.classify_loss_graph_v1(
            value_loss=torch.tensor(0.0), current_values=values,
            frozen_value_predictions=frozen, normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("loss-detached"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
        "current_values_detached": lambda: G.classify_loss_graph_v1(
            value_loss=torch.tensor(0.0, requires_grad=True),
            current_values=values.detach(), frozen_value_predictions=frozen,
            normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("values-detached"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
        "current_values_unused": lambda: G.classify_loss_graph_v1(
            value_loss=unrelated.sum(), current_values=values,
            frozen_value_predictions=frozen, normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("values-unused"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
        "all_zero_without_proof": lambda: G.classify_loss_graph_v1(
            value_loss=(values * 0.0).sum(), current_values=values,
            frozen_value_predictions=frozen, normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("zero-no-proof"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
        "nan_loss": lambda: G.classify_loss_graph_v1(
            value_loss=(values * float("nan")).sum(), current_values=values,
            frozen_value_predictions=frozen, normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("nan-loss"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
        "inf_derivative": lambda: G.classify_loss_graph_v1(
            value_loss=_FiniteForwardInfiniteBackward.apply(values).sum(),
            current_values=values, frozen_value_predictions=frozen,
            normalized_targets=target,
            source_faithful_loss_evidence_digest=R4H.R1.digest("inf-derivative"),
            mathematical_zero_effective_proved=False, zero_effective_reason=None,
        ),
    }
    for name, function in cases.items():
        try:
            function()
        except E.B2RContractError as exc:
            faults[name] = exc.stop_code
        else:
            raise AssertionError(f"negative case did not STOP: {name}")

    module = _TwoParameterModule()
    current = torch.tensor([[1.0]], requires_grad=True)
    loss = ((current - current.detach()) ** 2).mean()
    graph = G.classify_loss_graph_v1(
        value_loss=loss, current_values=current,
        frozen_value_predictions=torch.zeros_like(current),
        normalized_targets=current.detach(),
        source_faithful_loss_evidence_digest=R4H.R1.digest("missing-grad"),
        mathematical_zero_effective_proved=True,
        zero_effective_reason="EXACT_TARGET",
    )
    try:
        G._execute_backward_v1(
            loss=loss, component_kind="critic", owner_identity="critic",
            target_module=module, foreign_bindings=(),
            counter=G.B2RProbeExecutionCounterV1(), require_nonzero=False,
            allow_proved_zero_effective=True, loss_graph_evidence=graph,
        )
    except E.B2RContractError as exc:
        faults["all_parameter_grads_none"] = exc.stop_code
    else:
        raise AssertionError("missing required parameter grad did not STOP")

    critic_module = torch.nn.Linear(1, 1)
    actor_module = torch.nn.Linear(1, 1)
    current = critic_module(torch.ones((1, 1)))
    foreign_loss = current.sum() + actor_module(torch.ones((1, 1))).sum()
    graph = G.classify_loss_graph_v1(
        value_loss=foreign_loss, current_values=current,
        frozen_value_predictions=torch.zeros_like(current),
        normalized_targets=torch.zeros_like(current),
        source_faithful_loss_evidence_digest=R4H.R1.digest("foreign-gradient"),
        mathematical_zero_effective_proved=False, zero_effective_reason=None,
    )
    try:
        G._execute_backward_v1(
            loss=foreign_loss, component_kind="critic", owner_identity="critic",
            target_module=critic_module, foreign_bindings=(("actor0", actor_module),),
            counter=G.B2RProbeExecutionCounterV1(), require_nonzero=False,
            loss_graph_evidence=graph,
        )
    except E.B2RContractError as exc:
        faults["foreign_actor_gradient"] = exc.stop_code
    else:
        raise AssertionError("foreign gradient did not STOP")

    ownership_context = R4H.make_context(
        valuenorm_enabled=False, suffix="cg-ownership"
    )
    try:
        E.validate_parameter_ownership_v1(
            actor_bindings=((
                "actor0",
                ownership_context.components.actors[0].actor,
                ownership_context.components.critic.critic_optimizer,
            ),),
            critic_binding=(
                "critic", ownership_context.components.critic.critic,
                ownership_context.components.critic.critic_optimizer,
            ),
            shared_parameter_mode=False,
        )
    except E.B2RContractError as exc:
        faults["parameter_ownership_broken"] = exc.stop_code
    else:
        raise AssertionError("broken ownership did not STOP")

    expected = {
        "loss_detached": G.STOP_MUTATION_ATTRIBUTION,
        "current_values_detached": G.STOP_MUTATION_ATTRIBUTION,
        "current_values_unused": G.STOP_MUTATION_ATTRIBUTION,
        "all_zero_without_proof": G.STOP_MUTATION_ATTRIBUTION,
        "nan_loss": G.STOP_NONFINITE_LOSS,
        "inf_derivative": G.STOP_NONFINITE_GRADIENT,
        "all_parameter_grads_none": G.STOP_MUTATION_ATTRIBUTION,
        "foreign_actor_gradient": G.STOP_MUTATION_ATTRIBUTION,
        "parameter_ownership_broken": E.STOP_OWNERSHIP,
    }
    R4H.assert_true(faults == expected, f"negative classifications: {faults}")
    return faults


def main() -> None:
    results: dict[str, object] = {}
    try:
        results["cpu_exact_target"] = exact_target_witness(
            device=torch.device("cpu"), suffix="cg-exact-cpu"
        )
        results["cpu_mixed_adam"] = mixed_adam_witness()[0]
        results["negative"] = negative_classification_witnesses()
        results["r5_mixed_s10"] = r5_mixed_s10_witness()
        if torch.cuda.is_available():
            results["cuda_exact_target"] = exact_target_witness(
                device=torch.device("cuda:0"), suffix="cg-exact-cuda"
            )
            cuda_status = "PASS"
        else:
            results["cuda_exact_target"] = {"status": "NOT_FEASIBLE"}
            cuda_status = "NOT_FEASIBLE"
    except BaseException:
        print(json.dumps({"status": "FAIL", "tests": results}, sort_keys=True))
        raise
    print(json.dumps({
        "status": "PASS",
        "tests": results,
        "counts": {
            "controlled_nonzero_critic_witnesses": 2,
            "controlled_valid_zero_effective_witnesses": 4 if cuda_status == "PASS" else 3,
            "graph_disconnect_faults": 3,
            "grad_none_faults": 1,
            "nonfinite_faults": 2,
            "dLoss_dValues_nonzero_cases": 2,
            "dLoss_dValues_exact_zero_cases": 4 if cuda_status == "PASS" else 3,
            "dLoss_dValues_None_cases": 1,
            "adam_existing_state_zero_gradient_probes": 2,
            "r4_successful_controlled_sequences": 3 if cuda_status == "PASS" else 2,
            "r4_valid_zero_effective_cases": 5 if cuda_status == "PASS" else 3,
            "r5_successful_controlled_full_transactions": 1,
            "r5_S10": 1,
            "cuda_critic_classification_probes": 1 if cuda_status == "PASS" else 0,
            "isaac_applauncher": 0,
            "checkpoint_weight_io": 0,
            "training_evaluation_playback": 0,
            "public_route": 0,
        },
    }, sort_keys=True))


if __name__ == "__main__":
    main()
