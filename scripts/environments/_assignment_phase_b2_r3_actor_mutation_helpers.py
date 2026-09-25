"""Controlled CPU fixtures for the private B2-R3 actor mutation slice."""

from __future__ import annotations

import copy
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


E, P, C = R1.E, R1.P, R1.C
G = R1.load_canonical("assignment_event_training_gradient_probe.py")
R3 = R1.load_canonical("assignment_event_training_actor_mutation.py")
SG = R1.load_canonical("assignment_event_training_actor_mutation_guards.py")

from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.algorithms.critics.v_critic import VCritic  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


DEVICE = torch.device("cpu")
T, ENVIRONMENTS, ACTORS, TASKS = 2, 3, 3, 4
B = T * ENVIRONMENTS
OBS_DIM, SHARED_DIM, HIDDEN = 8, 12, 32
ACTION_DIM = TASKS + 1
ORDER_SEED = 7


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_stop(stop_code: str, function) -> Any:
    try:
        function()
    except E.B2RContractError as exc:
        assert_true(exc.stop_code == stop_code, f"wrong STOP {exc.stop_code}; expected {stop_code}")
        return exc
    raise AssertionError(f"expected {stop_code}")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _args() -> dict[str, object]:
    return {
        "hidden_sizes": [HIDDEN, HIDDEN], "activation_func": "relu",
        "use_feature_normalization": True, "initialization_method": "orthogonal_",
        "gain": 0.01, "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False, "recurrent_n": 1, "data_chunk_length": 2,
        "lr": 0.0005, "critic_lr": 0.0005, "opti_eps": 0.00001,
        "weight_decay": 0, "std_x_coef": 1, "std_y_coef": 0.5,
        "ppo_epoch": 2, "critic_epoch": 1, "clip_param": 0.2,
        "actor_num_mini_batch": 2, "critic_num_mini_batch": 1,
        "entropy_coef": 0.01, "value_loss_coef": 1.0,
        "use_max_grad_norm": True, "max_grad_norm": 10.0,
        "use_gae": True, "gamma": 0.99, "gae_lambda": 0.95,
        "use_huber_loss": True, "use_clipped_value_loss": True,
        "use_policy_active_masks": True, "huber_delta": 10.0,
        "action_aggregation": "prod", "share_param": False,
        "fixed_order": False,
    }


@dataclass
class Components:
    actors: list[HAPPO]
    critic: VCritic
    live_value_normalizer: ValueNorm


@dataclass
class Context:
    components: Components
    base_authority: Any
    authority: Any
    plan: Any
    frozen_inputs: Any
    actor_inputs: dict[int, Any]
    factor: torch.Tensor


def make_components() -> Components:
    torch.manual_seed(2303)
    obs_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(OBS_DIM,), dtype=np.float32)
    shared_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(SHARED_DIM,), dtype=np.float32)
    action_space = gymnasium.spaces.Discrete(ACTION_DIM)
    args = _args()
    actors = [HAPPO(args, obs_space, action_space, device=DEVICE) for _ in range(ACTORS)]
    critic = VCritic(args, shared_space, device=DEVICE)
    return Components(actors, critic, ValueNorm(1, device=DEVICE))


def make_base_authority() -> Any:
    config = E.B2RResolvedConfigV1(
        resolved_T=T, resolved_E=ENVIRONMENTS, resolved_M=ACTORS, resolved_N=TASKS,
        actor_epoch_count=2, actor_minibatch_count=2,
        actor_partition_policy="reviewed_exact_coverage",
        critic_epoch_count=1, critic_minibatch_count=1,
        critic_partition_policy="reviewed_exact_coverage",
        fixed_order=False, valuenorm_enabled=True,
        ppo_happo_settings=(("clip_param", 0.2), ("entropy_coef", 0.01), ("max_grad_norm", 10.0)),
    )
    repo_files = tuple(sorted(
        (R1.SCAN_SOURCE / name
        for name in (
            "assignment_event_training_evidence.py",
            "assignment_event_training_plans.py",
            "assignment_event_training_control.py",
            "assignment_event_training_gradient_probe.py",
            "assignment_event_training_actor_mutation.py",
        )), key=lambda path: path.as_posix()))
    harl_root = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
    harl_files = tuple(sorted((
        harl_root / "algorithms" / "actors" / "happo.py",
        harl_root / "algorithms" / "actors" / "on_policy_base.py",
    ), key=lambda path: path.as_posix()))
    return E.B2RUpdateAuthorityV1(
        update_id="b2-r3-controlled-actor-mutation-0001",
        slice_identity="B2-R1",
        repository_head="b71d85a32f51be6ada324f870813a56bb45dd396",
        dirty_state_classification="reviewed uncommitted B2-R0/R1/R2 plus authorized private B2-R3",
        repo_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(R1.REPO_ROOT).as_posix(), _sha(path)) for path in repo_files),
        installed_harl_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(harl_root).as_posix(), _sha(path)) for path in harl_files),
        resolved_config=config,
        authorization_scope=("r1_contract_authority", "r2_backward_seam", "r3_actor_optimizer_mutation", "r3_factor_attribution"),
        forbidden_operations=("critic_backward", "critic_optimizer_step", "live_valuenorm_update", "scheduler_step", "isaac", "training", "checkpoint_weight_io", "public_route_activation"),
    )


def make_actor_inputs(components: Components) -> dict[int, Any]:
    masks_by_actor = {
        0: (
            torch.tensor([True, True, False, True, True, False]).reshape(B, 1),
            torch.tensor([True, False, False, True, False, False]).reshape(B, 1),
        ),
        1: (
            torch.tensor([True, True, False, False, True, True]).reshape(B, 1),
            torch.tensor([True, False, False, False, True, False]).reshape(B, 1),
        ),
        2: (
            torch.zeros((B, 1), dtype=torch.bool),
            torch.zeros((B, 1), dtype=torch.bool),
        ),
    }
    results: dict[int, Any] = {}
    for actor_id, actor in enumerate(components.actors):
        obs = torch.arange(B * OBS_DIM, dtype=torch.float32).reshape(B, OBS_DIM) / 40.0 - 0.5 + actor_id * 0.03
        rnn = torch.zeros((B, 1, HIDDEN), dtype=torch.float32)
        actions = torch.full((B, 1), TASKS, dtype=torch.int64)
        masks = torch.ones((B, 1), dtype=torch.float32)
        available = torch.ones((B, ACTION_DIM), dtype=torch.float32)
        behavior = torch.zeros((B, 1), dtype=torch.float32)
        dvm, active = masks_by_actor[actor_id]
        indices = R3._canonical_true_row_indices_v1(dvm)
        if indices:
            index_tensor = torch.tensor(indices, dtype=torch.long)
            with torch.no_grad():
                sampled_actions, sampled_logs, _ = actor.get_actions(
                    obs[index_tensor], rnn[index_tensor], masks[index_tensor],
                    available[index_tensor], deterministic=True
                )
            actions[index_tensor] = sampled_actions.to(dtype=torch.int64)
            behavior[index_tensor] = sampled_logs
        advantages = torch.tensor([[-1.0], [0.75], [-0.3], [1.5], [0.4], [-0.8]], dtype=torch.float32) + actor_id * 0.1
        results[actor_id] = R3.B2R3ActorInputsV1(obs, rnn, actions, masks, available, behavior, advantages, dvm, active)
    return results


def make_context() -> Context:
    components = make_components()
    base = make_base_authority()
    inputs = make_actor_inputs(components)
    freezer = R3.B2R3ActorOrderFreezerV1(base)
    order = freezer.freeze(rng_seed=ORDER_SEED)
    assert_true(order.actor_order == (0, 1, 2), "controlled RNG order drift")
    behavior_by_actor = tuple(
        (actor_id, E.fingerprint_tensor_v1(inputs[actor_id].behavior_old_logprobs).content_digest)
        for actor_id in range(ACTORS)
    )
    authority = R3.B2R3MutationAuthorityV1(
        base_authority=base,
        mutation_id="controlled-cpu-real-adam-0001",
        slice_identity="B2-R3",
        order_evidence=order,
        behavior_digest_by_actor=behavior_by_actor,
        allowed_operations=("actor_zero_grad", "actor_backward", "actor_gradient_clip", "actor_optimizer_step", "actor_post_step_evaluation", "factor_attribution"),
        forbidden_operations=("critic_backward", "critic_optimizer_step", "critic_parameter_mutation", "live_valuenorm_update", "scheduler_step", "full_learner_update", "isaac", "training", "evaluation_playback", "checkpoint_weight_io", "public_route_activation"),
    )
    factor = torch.ones((T, ENVIRONMENTS, 1), dtype=torch.float32)
    partitions = P.build_exact_partitions_v1(B=B, epoch_count=2, minibatch_count=2, partition_policy="reviewed_exact_coverage")
    dvm = {
        actor_id: R3._canonical_true_row_indices_v1(inputs[actor_id].decision_valid_mask)
        for actor_id in range(ACTORS)
    }
    active = {
        actor_id: R3._canonical_true_row_indices_v1(inputs[actor_id].active_mask)
        for actor_id in range(ACTORS)
    }
    plan = P.build_actor_update_plan_v1(
        authority=base, authority_config_digest=base.config_digest,
        actor_permutation=order.actor_order,
        approved_partitions_by_epoch=partitions,
        dvm_indices_by_actor=dvm, active_indices_by_actor=active,
        factor_input_digest=E.fingerprint_tensor_v1(factor).content_digest,
        optimizer_step_policy="match_backward",
    )
    combined = E.canonical_digest_v1(behavior_by_actor)
    values = {name: R1.digest(f"r3-{name}") for name in (
        "historical_actor_observation_digest", "historical_available_action_mask_digest",
        "original_proposal_action_digest", "dvm_digest", "active_mask_digest",
        "selected_reason_grid_digest", "precedence_resolution_evidence_digest",
        "terminal_correlation_evidence_digest", "timeout_critic_evidence_digest",
        "event_return_result_digest", "critic_training_slice_digest",
        "final_structural_return_slot_digest", "baseline_value_digest", "advantage_digest",
    )}
    frozen = E.B2RFrozenTrainingInputsV1(
        update_id=base.update_id, authority_config_digest=base.config_digest,
        actor_canonical_identities=tuple((actor, t, env) for actor in range(ACTORS) for t in range(T) for env in range(ENVIRONMENTS)),
        original_behavior_logprob_digest=combined,
        termination_domain_valid=True, exactly_one_selected_category=True,
        return_equality_proof="controlled unchanged R2-compatible return identity",
        return_no_alias_proof="controlled distinct storage identity",
        **values,
    )
    return Context(components, base, authority, plan, frozen, inputs, factor)


def snapshot_actor_mutable_state(context: Context) -> Any:
    return (
        tuple(copy.deepcopy(actor.actor.state_dict()) for actor in context.components.actors),
        tuple(copy.deepcopy(actor.actor_optimizer.state_dict()) for actor in context.components.actors),
    )


def restore_actor_mutable_state(context: Context, snapshot: Any) -> None:
    actor_states, optimizer_states = snapshot
    for actor, actor_state, optimizer_state in zip(context.components.actors, actor_states, optimizer_states):
        actor.actor.load_state_dict(actor_state)
        actor.actor_optimizer.load_state_dict(optimizer_state)
        actor.actor_optimizer.zero_grad(set_to_none=True)
