"""Controlled CPU fixtures for the private B2-R2 real-autograd probe."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Any

import gymnasium
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as R1  # noqa: E402


G = R1.load_canonical("assignment_event_training_gradient_probe.py")
SG = R1.load_canonical("assignment_event_training_gradient_guards.py")
E, P, C = R1.E, R1.P, R1.C

from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.algorithms.critics.v_critic import VCritic  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


DEVICE = torch.device("cpu")
T, ENVIRONMENTS, ACTORS, TASKS = 2, 3, 3, 4
B = T * ENVIRONMENTS
OBS_DIM, SHARED_DIM, HIDDEN = 8, 12, 32
ACTION_DIM = TASKS + 1


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_stop(stop_code: str, function) -> None:
    try:
        function()
    except E.B2RContractError as exc:
        assert_true(exc.stop_code == stop_code, f"wrong STOP {exc.stop_code}; expected {stop_code}")
    else:
        raise AssertionError(f"expected {stop_code}")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args() -> dict[str, object]:
    return {
        "hidden_sizes": [HIDDEN, HIDDEN],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "gain": 0.01,
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "data_chunk_length": 2,
        "lr": 0.0005,
        "critic_lr": 0.0005,
        "opti_eps": 0.00001,
        "weight_decay": 0,
        "std_x_coef": 1,
        "std_y_coef": 0.5,
        "ppo_epoch": 1,
        "critic_epoch": 1,
        "clip_param": 0.2,
        "actor_num_mini_batch": 1,
        "critic_num_mini_batch": 1,
        "entropy_coef": 0.01,
        "value_loss_coef": 1.0,
        "use_max_grad_norm": True,
        "max_grad_norm": 10.0,
        "use_gae": True,
        "gamma": 0.99,
        "gae_lambda": 0.95,
        "use_huber_loss": True,
        "use_clipped_value_loss": True,
        "use_policy_active_masks": True,
        "huber_delta": 10.0,
        "action_aggregation": "prod",
        "share_param": False,
        "fixed_order": True,
    }


@dataclass
class Components:
    actors: list[HAPPO]
    critic: VCritic
    live_value_normalizer: ValueNorm


@dataclass
class ActorData:
    obs: torch.Tensor
    rnn_states: torch.Tensor
    actions: torch.Tensor
    masks: torch.Tensor
    available_actions: torch.Tensor
    behavior_old_logprobs: torch.Tensor
    advantages: torch.Tensor
    factor: torch.Tensor
    decision_valid_mask: torch.Tensor
    active_mask: torch.Tensor


@dataclass
class CriticData:
    shared_obs: torch.Tensor
    rnn_states: torch.Tensor
    masks: torch.Tensor
    value_preds: torch.Tensor
    returns_storage: torch.Tensor


def make_components() -> Components:
    torch.manual_seed(2202)
    obs_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(OBS_DIM,), dtype=np.float32)
    shared_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(SHARED_DIM,), dtype=np.float32)
    action_space = gymnasium.spaces.Discrete(ACTION_DIM)
    args = _args()
    actors = [HAPPO(args, obs_space, action_space, device=DEVICE) for _ in range(ACTORS)]
    critic = VCritic(args, shared_space, device=DEVICE)
    live_value_normalizer = ValueNorm(1, device=DEVICE)
    return Components(actors, critic, live_value_normalizer)


def make_base_authority() -> Any:
    config = E.B2RResolvedConfigV1(
        resolved_T=T,
        resolved_E=ENVIRONMENTS,
        resolved_M=ACTORS,
        resolved_N=TASKS,
        actor_epoch_count=1,
        actor_minibatch_count=1,
        actor_partition_policy="reviewed_exact_coverage",
        critic_epoch_count=1,
        critic_minibatch_count=1,
        critic_partition_policy="reviewed_exact_coverage",
        fixed_order=True,
        valuenorm_enabled=True,
        ppo_happo_settings=(("clip_param", 0.2), ("entropy_coef", 0.01), ("max_grad_norm", 10.0)),
    )
    repo_files = tuple(
        sorted(
            (
                R1.SCAN_SOURCE / "assignment_event_happo_policy_math.py",
                R1.SCAN_SOURCE / "assignment_event_training_evidence.py",
                R1.SCAN_SOURCE / "assignment_event_training_plans.py",
                R1.SCAN_SOURCE / "assignment_event_training_control.py",
                R1.SCAN_SOURCE / "assignment_event_training_gradient_probe.py",
            ),
            key=lambda item: item.as_posix(),
        )
    )
    harl_root = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
    harl_files = tuple(
        sorted(
            (
                harl_root / "algorithms" / "actors" / "happo.py",
                harl_root / "algorithms" / "critics" / "v_critic.py",
                harl_root / "common" / "valuenorm.py",
            ),
            key=lambda item: item.as_posix(),
        )
    )
    return E.B2RUpdateAuthorityV1(
        update_id="b2-r2-controlled-probe-0001",
        slice_identity="B2-R1",
        repository_head="b71d85a32f51be6ada324f870813a56bb45dd396",
        dirty_state_classification="uncommitted reviewed B2-R0/R1 artifacts plus authorized B2-R2 additions",
        repo_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(R1.REPO_ROOT).as_posix(), _sha(path)) for path in repo_files),
        installed_harl_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(harl_root).as_posix(), _sha(path)) for path in harl_files),
        resolved_config=config,
        authorization_scope=("r1_contract_authority", "r2_controlled_backward", "r2_gradient_cleanup"),
        forbidden_operations=("optimizer_step", "live_valuenorm_update", "isaac", "training", "checkpoint_weight_io", "public_route_activation"),
    )


def make_probe_authority() -> Any:
    return G.B2R2ProbeAuthorityV1(
        base_authority=make_base_authority(),
        probe_id="controlled-cpu-real-autograd-0001",
        slice_identity="B2-R2",
        allowed_operations=("backward", "gradient_inspection", "gradient_cleanup"),
        forbidden_operations=("optimizer_step", "scheduler_step", "live_valuenorm_update", "parameter_mutation", "optimizer_state_mutation", "isaac", "training", "checkpoint_weight_io", "public_route_activation"),
        expected_actor_backward_count=4,
        expected_critic_backward_count=3,
        expected_optimizer_step_count=0,
        expected_live_valuenorm_update_count=0,
    )


def make_actor_data(components: Components) -> ActorData:
    obs = torch.arange(B * OBS_DIM, dtype=torch.float32).reshape(B, OBS_DIM) / 50.0 - 0.4
    rnn_states = torch.zeros((B, 1, HIDDEN), dtype=torch.float32)
    actions = torch.full((B, 1), TASKS, dtype=torch.int64)
    masks = torch.ones((B, 1), dtype=torch.float32)
    available_actions = torch.ones((B, ACTION_DIM), dtype=torch.float32)
    behavior = torch.zeros((B, 1), dtype=torch.float32)
    dvm = torch.tensor([True, True, False, True, True, False], dtype=torch.bool)
    active = torch.tensor([True, False, False, True, False, True], dtype=torch.bool)
    index = dvm.nonzero(as_tuple=False).flatten()
    with torch.no_grad():
        sampled_actions, sampled_logs, _ = components.actors[0].get_actions(
            obs[index], rnn_states[index], masks[index], available_actions[index], deterministic=True
        )
    actions[index] = sampled_actions.to(dtype=torch.int64)
    behavior[index] = sampled_logs
    advantages = torch.tensor([[-1.0], [0.5], [9.0], [2.0], [-0.25], [-7.0]], dtype=torch.float32)
    factor = torch.ones((T, ENVIRONMENTS, 1), dtype=torch.float32)
    return ActorData(obs, rnn_states, actions, masks, available_actions, behavior, advantages, factor, dvm, active)


def make_critic_data() -> CriticData:
    shared_obs = torch.arange(B * SHARED_DIM, dtype=torch.float32).reshape(B, SHARED_DIM) / 80.0 - 0.5
    rnn_states = torch.zeros((B, 1, HIDDEN), dtype=torch.float32)
    masks = torch.ones((B, 1), dtype=torch.float32)
    value_preds = torch.zeros((B, 1), dtype=torch.float32)
    returns_storage = torch.zeros((T + 1, ENVIRONMENTS, 1), dtype=torch.float32)
    returns_storage[:-1].copy_(torch.tensor([[[-1.0], [0.5], [1.5]], [[2.0], [-0.75], [3.0]]]))
    returns_storage[-1].fill_(123.0)
    return CriticData(shared_obs, rnn_states, masks, value_preds, returns_storage)


def make_actor_plan(authority: Any, data: ActorData) -> Any:
    partitions = P.build_exact_partitions_v1(B=B, epoch_count=1, minibatch_count=1, partition_policy="reviewed_exact_coverage")
    return P.build_actor_update_plan_v1(
        authority=authority.base_authority,
        authority_config_digest=authority.config_digest,
        actor_permutation=(0, 1, 2),
        approved_partitions_by_epoch=partitions,
        dvm_indices_by_actor={0: (0, 1, 3, 4), 1: (), 2: ()},
        active_indices_by_actor={0: (0, 3, 5), 1: (), 2: ()},
        factor_input_digest=E.fingerprint_tensor_v1(data.factor).content_digest,
        optimizer_step_policy="disabled",
    )


def make_critic_plan(authority: Any, data: CriticData) -> Any:
    partitions = P.build_exact_partitions_v1(B=B, epoch_count=1, minibatch_count=1, partition_policy="reviewed_exact_coverage")
    target = data.returns_storage[:-1].reshape(B, 1)
    return P.build_critic_update_plan_v1(
        authority=authority.base_authority,
        authority_config_digest=authority.config_digest,
        approved_partitions_by_epoch=partitions,
        raw_target_digest=E.fingerprint_tensor_v1(target).content_digest,
        optimizer_step_policy="disabled",
    )


def make_frozen_inputs(authority: Any, *, behavior_digest: str, critic_target_digest: str) -> Any:
    values = {name: R1.digest(name) for name in (
        "historical_actor_observation_digest", "historical_available_action_mask_digest", "original_proposal_action_digest",
        "dvm_digest", "active_mask_digest", "selected_reason_grid_digest", "precedence_resolution_evidence_digest",
        "terminal_correlation_evidence_digest", "timeout_critic_evidence_digest", "event_return_result_digest",
        "final_structural_return_slot_digest", "baseline_value_digest", "advantage_digest",
    )}
    return E.B2RFrozenTrainingInputsV1(
        update_id=authority.update_id,
        authority_config_digest=authority.config_digest,
        actor_canonical_identities=tuple((actor, t, env) for actor in range(ACTORS) for t in range(T) for env in range(ENVIRONMENTS)),
        original_behavior_logprob_digest=behavior_digest,
        critic_training_slice_digest=critic_target_digest,
        termination_domain_valid=True,
        exactly_one_selected_category=True,
        return_equality_proof="synthetic event result exact-equal to returns[:-1] fixture",
        return_no_alias_proof="synthetic fixture uses distinct storage",
        **values,
    )


def actor_state_machine() -> Any:
    machine = C.B2RUpdateStateMachineV1()
    for stage in tuple(C.B2RUpdateStageV1)[1:6]:
        machine.transition(stage)
    return machine


def critic_state_machine() -> Any:
    machine = C.B2RUpdateStateMachineV1()
    for stage in tuple(C.B2RUpdateStageV1)[1:7]:
        machine.transition(stage)
    return machine


def actor_bindings(components: Components):
    return tuple((f"actor{index}", actor.actor, actor.actor_optimizer) for index, actor in enumerate(components.actors))


def critic_binding(components: Components):
    return ("critic", components.critic.critic, components.critic.critic_optimizer)


def make_permit(
    *,
    authority: Any,
    components: Components,
    frozen_inputs: Any,
    plan: Any,
    factor: torch.Tensor | None,
    component_kind: str,
    owner_identity: str,
    actor_id: int | None,
    stage: Any,
    epoch: int,
    minibatch: int,
    indices: tuple[int, ...],
    permit_id: str,
    override_update_id: str | None = None,
    override_config_digest: str | None = None,
    override_actor_id: int | None | object = "use-default",
    override_minibatch: int | None = None,
):
    snapshot = G.capture_probe_snapshot_v1(
        authority=authority,
        frozen_inputs=frozen_inputs,
        plan_digest=plan.plan_digest,
        factor=factor,
        actor_bindings=actor_bindings(components),
        critic_binding=critic_binding(components),
        live_value_normalizer=components.live_value_normalizer,
    )
    selected_actor = actor_id if override_actor_id == "use-default" else override_actor_id
    permit = C.B2RMutationPermitV1(
        permit_id=permit_id,
        update_id=authority.update_id if override_update_id is None else override_update_id,
        authority_config_digest=authority.config_digest if override_config_digest is None else override_config_digest,
        component_kind=component_kind,
        owner_identity=owner_identity,
        actor_id=selected_actor,
        stage=stage,
        epoch=epoch,
        minibatch=minibatch if override_minibatch is None else override_minibatch,
        canonical_index_digest=E.canonical_digest_v1(indices),
        allowed_operations=(C.B2RPermitOperationV1.BACKWARD,),
        expected_call_count=1,
        precondition_fingerprint_digest=snapshot.snapshot_digest,
        issuance_sequence=0,
    )
    return permit, C.B2RPermitLedgerV1((permit,))


class FiniteForwardInfiniteBackward(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value):
        ctx.shape = value.shape
        return value.sum() * 0.0

    @staticmethod
    def backward(ctx, gradient):
        return torch.full(ctx.shape, float("inf"), dtype=gradient.dtype, device=gradient.device) * gradient
