"""Controlled plain-Torch fixtures for B2-R4 critic and live ValueNorm mutation."""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
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
R4 = R1.load_canonical("assignment_event_training_critic_mutation.py")
SG = R1.load_canonical("assignment_event_training_critic_mutation_guards.py")

from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.algorithms.critics.v_critic import VCritic  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


DEVICE = torch.device("cpu")
ACTORS, TASKS = 3, 4
OBS_DIM, SHARED_DIM, HIDDEN = 8, 12, 32
ACTION_DIM = TASKS + 1


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


def _args(*, critic_epoch: int, critic_minibatches: int) -> dict[str, object]:
    return {
        "hidden_sizes": [HIDDEN, HIDDEN], "activation_func": "relu",
        "use_feature_normalization": True, "initialization_method": "orthogonal_",
        "gain": 0.01, "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False, "recurrent_n": 1, "data_chunk_length": 2,
        "lr": 0.0005, "critic_lr": 0.0005, "opti_eps": 0.00001,
        "weight_decay": 0, "std_x_coef": 1, "std_y_coef": 0.5,
        "ppo_epoch": 1, "critic_epoch": critic_epoch, "clip_param": 0.2,
        "actor_num_mini_batch": 1, "critic_num_mini_batch": critic_minibatches,
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
    inputs: Any
    T: int
    E_count: int
    B: int


def make_components(
    *,
    critic_epoch: int,
    critic_minibatches: int,
    seed: int,
    device: torch.device = DEVICE,
) -> Components:
    torch.manual_seed(seed)
    obs_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(OBS_DIM,), dtype=np.float32)
    shared_space = gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(SHARED_DIM,), dtype=np.float32)
    action_space = gymnasium.spaces.Discrete(ACTION_DIM)
    args = _args(critic_epoch=critic_epoch, critic_minibatches=critic_minibatches)
    actors = [HAPPO(args, obs_space, action_space, device=device) for _ in range(ACTORS)]
    critic = VCritic(args, shared_space, device=device)
    return Components(actors, critic, ValueNorm(1, device=device))


def make_context(
    *,
    valuenorm_enabled: bool = True,
    remainder_safe: bool = False,
    suffix: str = "main",
    device: torch.device = DEVICE,
) -> Context:
    T = 1 if remainder_safe else 2
    environments = 7 if remainder_safe else 3
    B = T * environments
    critic_epoch = 1 if remainder_safe or not valuenorm_enabled else 2
    critic_minibatches = 3 if remainder_safe else 2
    seed = 2404 + (1 if remainder_safe else 0) + (2 if not valuenorm_enabled else 0)
    components = make_components(
        critic_epoch=critic_epoch,
        critic_minibatches=critic_minibatches,
        seed=seed,
        device=device,
    )
    policy = "reviewed_exact_coverage" if remainder_safe else "exact_divisible"
    config = E.B2RResolvedConfigV1(
        resolved_T=T, resolved_E=environments, resolved_M=ACTORS, resolved_N=TASKS,
        actor_epoch_count=1, actor_minibatch_count=1,
        actor_partition_policy="reviewed_exact_coverage",
        critic_epoch_count=critic_epoch, critic_minibatch_count=critic_minibatches,
        critic_partition_policy=policy,
        fixed_order=False, valuenorm_enabled=valuenorm_enabled,
        ppo_happo_settings=(("clip_param", 0.2), ("max_grad_norm", 10.0), ("value_loss_coef", 1.0)),
    )
    repo_files = tuple(sorted((
        R1.SCAN_SOURCE / "assignment_event_training_evidence.py",
        R1.SCAN_SOURCE / "assignment_event_training_plans.py",
        R1.SCAN_SOURCE / "assignment_event_training_control.py",
        R1.SCAN_SOURCE / "assignment_event_training_gradient_probe.py",
        R1.SCAN_SOURCE / "assignment_event_training_critic_mutation.py",
    ), key=lambda path: path.as_posix()))
    harl_root = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
    harl_files = tuple(sorted((
        harl_root / "algorithms" / "critics" / "v_critic.py",
        harl_root / "common" / "valuenorm.py",
    ), key=lambda path: path.as_posix()))
    base = E.B2RUpdateAuthorityV1(
        update_id=f"b2-r4-controlled-critic-{suffix}",
        slice_identity="B2-R1",
        repository_head="b71d85a32f51be6ada324f870813a56bb45dd396",
        dirty_state_classification="reviewed uncommitted B2-R0-R3 plus authorized private B2-R4",
        repo_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(R1.REPO_ROOT).as_posix(), _sha(path)) for path in repo_files),
        installed_harl_source_hashes=tuple(E.B2RSourceDigestV1(path.relative_to(harl_root).as_posix(), _sha(path)) for path in harl_files),
        resolved_config=config,
        authorization_scope=("r1_critic_plan", "r2_backward_seam", "r4_live_valuenorm", "r4_critic_optimizer_mutation"),
        forbidden_operations=("actor_backward", "actor_optimizer_step", "scheduler_step", "full_learner_update", "isaac", "training", "evaluation_playback", "checkpoint_weight_io", "public_route_activation"),
    )
    authority = R4.B2R4MutationAuthorityV1(
        base_authority=base,
        mutation_id=f"controlled-{device.type}-real-critic-{suffix}",
        slice_identity="B2-R4",
        allowed_operations=("live_valuenorm_update", "critic_backward", "critic_gradient_clip", "critic_optimizer_step"),
        forbidden_operations=("actor_backward", "actor_optimizer_step", "actor_parameter_mutation", "scheduler_step", "full_learner_update", "isaac", "training", "evaluation_playback", "checkpoint_weight_io", "public_route_activation"),
    )
    shared_obs = torch.arange(
        B * SHARED_DIM, dtype=torch.float32, device=device
    ).reshape(B, SHARED_DIM) / 70.0 - 0.6
    rnn_states = torch.zeros((B, 1, HIDDEN), dtype=torch.float32, device=device)
    masks = torch.ones((B, 1), dtype=torch.float32, device=device)
    # Bind the clipped-value baseline to the real critic's frozen pre-update
    # predictions.  A constant zero baseline can make HARL's clipped branch
    # locally constant after the first minibatch and therefore creates a
    # degenerate (all-zero-gradient) fixture rather than a useful R4 probe.
    with torch.no_grad():
        value_preds, _ = components.critic.get_values(shared_obs, rnn_states, masks)
    value_preds = value_preds.detach().clone()
    returns_storage = torch.zeros(
        (T + 1, environments, 1), dtype=torch.float32, device=device
    )
    returns_storage[:-1].copy_(
        torch.linspace(-1.5, 3.0, B, dtype=torch.float32, device=device).reshape(
            T, environments, 1
        )
    )
    returns_storage[-1].fill_(321.0)
    inputs = R4.B2R4CriticInputsV1(shared_obs, rnn_states, masks, value_preds, returns_storage)
    raw_target = returns_storage[:-1].reshape(B, 1)
    target_digest = E.fingerprint_tensor_v1(raw_target).content_digest
    partitions = P.build_exact_partitions_v1(B=B, epoch_count=critic_epoch, minibatch_count=critic_minibatches, partition_policy=policy)
    plan = P.build_critic_update_plan_v1(
        authority=base,
        authority_config_digest=base.config_digest,
        approved_partitions_by_epoch=partitions,
        raw_target_digest=target_digest,
        optimizer_step_policy="match_backward",
    )
    values = {name: R1.digest(f"r4-{suffix}-{name}") for name in (
        "historical_actor_observation_digest", "historical_available_action_mask_digest",
        "original_proposal_action_digest", "original_behavior_logprob_digest",
        "dvm_digest", "active_mask_digest", "selected_reason_grid_digest",
        "precedence_resolution_evidence_digest", "terminal_correlation_evidence_digest",
        "timeout_critic_evidence_digest", "event_return_result_digest",
        "final_structural_return_slot_digest", "baseline_value_digest", "advantage_digest",
    )}
    frozen = E.B2RFrozenTrainingInputsV1(
        update_id=base.update_id,
        authority_config_digest=base.config_digest,
        actor_canonical_identities=tuple((actor, t, env) for actor in range(ACTORS) for t in range(T) for env in range(environments)),
        critic_training_slice_digest=target_digest,
        termination_domain_valid=True,
        exactly_one_selected_category=True,
        return_equality_proof="controlled event result exact-equal returns[:-1]",
        return_no_alias_proof="controlled distinct event result and critic storage",
        **values,
    )
    return Context(components, base, authority, plan, frozen, inputs, T, environments, B)


def rebind_critic_targets(
    context: Context,
    *,
    training_returns: torch.Tensor,
    frozen_value_predictions: torch.Tensor,
) -> Context:
    """Rebind a controlled target while preserving the reviewed R4 plan shape."""

    expected = (context.B, 1)
    if tuple(training_returns.shape) != expected or tuple(
        frozen_value_predictions.shape
    ) != expected:
        raise ValueError(
            f"controlled critic rebind requires {expected}, got "
            f"{tuple(training_returns.shape)} and "
            f"{tuple(frozen_value_predictions.shape)}"
        )
    storage = context.inputs.returns_storage.detach().clone()
    storage[:-1].copy_(training_returns.reshape(context.T, context.E_count, 1))
    target_digest = E.fingerprint_tensor_v1(
        storage[:-1].reshape(context.B, 1)
    ).content_digest
    inputs = replace(
        context.inputs,
        value_preds=frozen_value_predictions.detach().clone(),
        returns_storage=storage,
    )
    plan = replace(context.plan, raw_target_digest=target_digest)
    frozen = replace(
        context.frozen_inputs,
        critic_training_slice_digest=target_digest,
    )
    return Context(
        context.components,
        context.base_authority,
        context.authority,
        plan,
        frozen,
        inputs,
        context.T,
        context.E_count,
        context.B,
    )


def snapshot_mutable_state(context: Context) -> Any:
    return (
        copy.deepcopy(context.components.critic.critic.state_dict()),
        copy.deepcopy(context.components.critic.critic_optimizer.state_dict()),
        copy.deepcopy(context.components.live_value_normalizer.state_dict()),
    )


def restore_mutable_state(context: Context, snapshot: Any) -> None:
    critic_state, optimizer_state, valuenorm_state = snapshot
    context.components.critic.critic.load_state_dict(critic_state)
    context.components.critic.critic_optimizer.load_state_dict(optimizer_state)
    context.components.live_value_normalizer.load_state_dict(valuenorm_state)
    context.components.critic.critic_optimizer.zero_grad(set_to_none=True)
