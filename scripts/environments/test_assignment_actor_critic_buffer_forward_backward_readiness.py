"""Phase 9G-8F-4 synthetic HARL actor/critic/buffer readiness tests.

The suite exercises the installed HARL feed-forward HAPPO and EP critic paths
with deterministic CPU data. It does not construct an environment, run a
training loop, or save/load checkpoints.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterator

import gymnasium
import numpy as np
import torch
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
HARL_CONFIG_PATH = SCAN_TASK_SOURCE / "agents" / "harl_happo_cfg.yaml"
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from assignment_lifecycle_training_contract import (  # noqa: E402
    FEED_FORWARD_GENERATOR,
    resolve_installed_harl_actor_buffer_generator,
    validate_assignment_lifecycle_policy_sequence,
)
from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.algorithms.critics.v_critic import VCritic  # noqa: E402
from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer  # noqa: E402
from harl.common.buffers.on_policy_critic_buffer_ep import OnPolicyCriticBufferEP  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


NUM_AGENTS = 3
NUM_TASKS = 50
ACTION_DIM = NUM_TASKS + 1
NOOP_RAW_ID = NUM_TASKS
LIFECYCLE_ACTOR_DIM = 1059
LIFECYCLE_SHARED_DIM = 3183
LEGACY_ACTOR_DIM = 909
LEGACY_SHARED_DIM = 2727
ROLLOUT_LENGTH = 4
ROLLOUT_THREADS = 2
DEVICE = torch.device("cpu")


@dataclass(frozen=True)
class ReadinessResult:
    profile: str
    actor_dimension: int
    shared_dimension: int
    action_dimension: int
    actor_parameter_count: int
    critic_parameter_count: int
    actor_parameters_with_gradients: int
    critic_parameters_with_gradients: int
    actor_gradient_norm_pre_clip: float
    actor_gradient_norm_post_clip: float
    critic_gradient_norm_pre_clip: float
    critic_gradient_norm_post_clip: float
    actor_loss: float
    actor_entropy: float
    critic_loss: float
    actor_forward_passed: bool
    critic_forward_passed: bool
    actor_buffer_passed: bool
    critic_buffer_passed: bool
    actor_generator_passed: bool
    critic_generator_passed: bool
    actor_parameter_changed: bool
    critic_parameter_changed: bool
    independent_actors_unchanged: bool
    value_norm_changed: bool


@dataclass
class ReadinessComponents:
    profile: str
    actor_dim: int
    shared_dim: int
    config: dict[str, Any]
    actors: list[HAPPO]
    actor_buffers: list[OnPolicyActorBuffer]
    critic: VCritic
    critic_buffer: OnPolicyCriticBufferEP
    value_normalizer: ValueNorm


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], expected: str) -> None:
    try:
        func()
    except Exception as exc:  # noqa: BLE001 - negative tests validate the public failure boundary.
        if expected not in str(exc):
            raise AssertionError(f"expected {expected!r} in {str(exc)!r}") from exc
        return
    raise AssertionError(f"expected an exception containing {expected!r}")


@contextmanager
def _isolated_seed(seed: int) -> Iterator[None]:
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.random.get_rng_state()
    try:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.random.set_rng_state(torch_state)


def _load_effective_config() -> dict[str, Any]:
    with HARL_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    _assert(config["model"]["hidden_sizes"] == [256, 256], "effective hidden sizes")
    _assert(config["model"]["hidden_sizes_critic"] == [512, 256], "raw unused critic hidden sizes")
    _assert(config["model"]["activation_func"] == "relu", "activation function")
    _assert(config["model"]["use_feature_normalization"] is True, "feature normalization")
    _assert(config["model"]["initialization_method"] == "orthogonal_", "initialization method")
    _assert(config["model"]["gain"] == 0.01, "action gain")
    _assert(config["model"]["lr"] == 0.0005, "actor learning rate")
    _assert(config["model"]["critic_lr"] == 0.0005, "critic learning rate")
    _assert(config["model"]["opti_eps"] == 0.00001, "optimizer epsilon")
    _assert(config["model"]["weight_decay"] == 0, "weight decay")
    _assert(config["algo"]["clip_param"] == 0.2, "clip parameter")
    _assert(config["algo"]["entropy_coef"] == 0.01, "entropy coefficient")
    _assert(config["algo"]["max_grad_norm"] == 10.0, "maximum gradient norm")
    _assert(config["algo"]["ppo_epoch"] == 5, "PPO epochs")
    _assert(config["algo"]["actor_num_mini_batch"] == 2, "actor minibatches")
    _assert(config["algo"]["critic_num_mini_batch"] == 2, "critic minibatches")
    _assert(config["algo"]["gamma"] == 0.99, "gamma")
    _assert(config["algo"]["gae_lambda"] == 0.95, "GAE lambda")
    _assert(config["train"]["use_valuenorm"] is True, "ValueNorm enabled")
    _assert(config["train"]["use_proper_time_limits"] is True, "proper time limits")
    _assert(config["model"]["recurrent_n"] == 1, "recurrent_n")
    _assert(config["algo"]["share_param"] is False, "independent actors")
    return config


def _profile_dimensions(profile: str) -> tuple[int, int]:
    if profile == "lifecycle_contract_c":
        return LIFECYCLE_ACTOR_DIM, LIFECYCLE_SHARED_DIM
    if profile == "legacy":
        return LEGACY_ACTOR_DIM, LEGACY_SHARED_DIM
    raise ValueError(f"unsupported readiness profile: {profile}")


def _validate_official_support(
    *,
    profile: str,
    actor_dim: int,
    shared_dim: int,
    actor_count: int = NUM_AGENTS,
    action_dim: int = ACTION_DIM,
    state_type: str = "EP",
    share_param: bool = False,
    use_recurrent_policy: bool = False,
    use_naive_recurrent_policy: bool = False,
) -> None:
    expected_actor_dim, expected_shared_dim = _profile_dimensions(profile)
    if actor_dim != expected_actor_dim:
        raise ValueError(f"{profile} actor observation width must be {expected_actor_dim}, got {actor_dim}")
    if shared_dim != expected_shared_dim:
        raise ValueError(f"{profile} shared observation width must be {expected_shared_dim}, got {shared_dim}")
    if action_dim != ACTION_DIM:
        raise ValueError(f"assignment action width must be {ACTION_DIM}, got {action_dim}")
    if actor_count != NUM_AGENTS:
        raise ValueError(f"assignment actor count must be {NUM_AGENTS}, got {actor_count}")
    if state_type != "EP":
        raise ValueError(f"lifecycle readiness supports EP state type only, got {state_type}")
    if share_param:
        raise ValueError("lifecycle readiness requires share_param=false")

    model = {
        "use_recurrent_policy": use_recurrent_policy,
        "use_naive_recurrent_policy": use_naive_recurrent_policy,
        "data_chunk_length": 10,
        "recurrent_n": 1,
    }
    validate_assignment_lifecycle_policy_sequence(
        algo_args={"model": model},
        env_args={
            "assignment_rl": True,
            "config": SimpleNamespace(assignment_lifecycle_profile=profile),
        },
    )
    if profile == "lifecycle_contract_c":
        selected = resolve_installed_harl_actor_buffer_generator(
            use_recurrent_policy=use_recurrent_policy,
            use_naive_recurrent_policy=use_naive_recurrent_policy,
        )
        if selected != FEED_FORWARD_GENERATOR:
            raise ValueError(f"lifecycle readiness requires {FEED_FORWARD_GENERATOR}, got {selected}")


def _validate_batch(
    *,
    actor_obs: torch.Tensor,
    shared_obs: torch.Tensor,
    available_actions: torch.Tensor,
    actions: torch.Tensor,
    advantages: torch.Tensor,
    returns: torch.Tensor,
    actor_dim: int,
    shared_dim: int,
) -> None:
    if actor_obs.ndim != 2 or actor_obs.shape[-1] != actor_dim:
        raise ValueError(f"actor observation width must be {actor_dim}, got {tuple(actor_obs.shape)}")
    if shared_obs.ndim != 2 or shared_obs.shape[-1] != shared_dim:
        raise ValueError(f"shared observation width must be {shared_dim}, got {tuple(shared_obs.shape)}")
    if available_actions.ndim != 2 or available_actions.shape[-1] != ACTION_DIM:
        raise ValueError(f"available_actions width must be {ACTION_DIM}, got {tuple(available_actions.shape)}")
    if not torch.isfinite(actor_obs).all():
        raise ValueError("actor observation must be finite")
    if not torch.isfinite(shared_obs).all():
        raise ValueError("shared observation must be finite")
    if not torch.isfinite(advantages).all():
        raise ValueError("advantages must be finite")
    if not torch.isfinite(returns).all():
        raise ValueError("returns must be finite")
    if torch.any(available_actions.sum(dim=-1) <= 0):
        raise ValueError("available_actions rows must contain at least one enabled action")
    if not torch.all(available_actions[:, NOOP_RAW_ID] == 1):
        raise ValueError("noop raw action 50 must remain available")
    action_ids = actions.long().squeeze(-1)
    if torch.any(action_ids < 0) or torch.any(action_ids >= ACTION_DIM):
        raise ValueError("action id is outside the assignment action space")
    selected = available_actions.gather(1, action_ids.unsqueeze(-1)).squeeze(-1)
    if not torch.all(selected == 1):
        raise ValueError("selected action is unavailable under its historical mask")


def _space(width: int) -> gymnasium.spaces.Box:
    return gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(width,), dtype=np.float32)


def _combined_model_algo_args(config: dict[str, Any]) -> dict[str, Any]:
    return {**copy.deepcopy(config["model"]), **copy.deepcopy(config["algo"])}


def _buffer_args(config: dict[str, Any]) -> dict[str, Any]:
    args = {
        **copy.deepcopy(config["train"]),
        **copy.deepcopy(config["model"]),
        **copy.deepcopy(config["algo"]),
    }
    args["episode_length"] = ROLLOUT_LENGTH
    args["n_rollout_threads"] = ROLLOUT_THREADS
    args["hidden_sizes"] = list(config["model"]["hidden_sizes"])
    return args


def _construct_components(profile: str) -> ReadinessComponents:
    config = _load_effective_config()
    actor_dim, shared_dim = _profile_dimensions(profile)
    _validate_official_support(profile=profile, actor_dim=actor_dim, shared_dim=shared_dim)

    actor_space = _space(actor_dim)
    shared_space = _space(shared_dim)
    action_space = gymnasium.spaces.Discrete(ACTION_DIM)
    model_algo_args = _combined_model_algo_args(config)
    actors = [
        HAPPO(model_algo_args, actor_space, action_space, device=DEVICE)
        for _ in range(NUM_AGENTS)
    ]
    actor_buffers = [
        OnPolicyActorBuffer(_buffer_args(config), actor_space, action_space, device=DEVICE)
        for _ in range(NUM_AGENTS)
    ]
    critic = VCritic(model_algo_args, shared_space, device=DEVICE)
    critic_buffer = OnPolicyCriticBufferEP(_buffer_args(config), shared_space, device=DEVICE)
    value_normalizer = ValueNorm(1, device=DEVICE)

    _assert(actors[0].actor.base.mlp.fc[0].in_features == actor_dim, "actor input layer width")
    _assert(critic.critic.base.mlp.fc[0].in_features == shared_dim, "critic input layer width")
    _assert(not hasattr(actors[0].actor, "rnn"), "feed-forward actor has no RNN module")
    _assert(not hasattr(critic.critic, "rnn"), "feed-forward critic has no RNN module")
    _assert(len({id(actor) for actor in actors}) == NUM_AGENTS, "independent HAPPO wrappers")
    _assert(len({id(actor.actor) for actor in actors}) == NUM_AGENTS, "independent actor networks")
    _assert(
        len({id(actor.actor_optimizer) for actor in actors}) == NUM_AGENTS,
        "independent actor optimizers",
    )
    parameter_storages = [
        next(actor.actor.parameters()).untyped_storage().data_ptr() for actor in actors
    ]
    _assert(len(set(parameter_storages)) == NUM_AGENTS, "independent actor parameter storage")

    for actor in actors:
        optimizer_ids = {
            id(parameter)
            for group in actor.actor_optimizer.param_groups
            for parameter in group["params"]
        }
        _assert(
            optimizer_ids == {id(parameter) for parameter in actor.actor.parameters()},
            "actor optimizer parameter binding",
        )
        _assert(actor.actor_optimizer.param_groups[0]["lr"] == config["model"]["lr"], "actor optimizer lr")
    critic_optimizer_ids = {
        id(parameter)
        for group in critic.critic_optimizer.param_groups
        for parameter in group["params"]
    }
    _assert(
        critic_optimizer_ids == {id(parameter) for parameter in critic.critic.parameters()},
        "critic optimizer parameter binding",
    )
    _assert(
        critic.critic_optimizer.param_groups[0]["lr"] == config["model"]["critic_lr"],
        "critic optimizer lr",
    )

    return ReadinessComponents(
        profile=profile,
        actor_dim=actor_dim,
        shared_dim=shared_dim,
        config=config,
        actors=actors,
        actor_buffers=actor_buffers,
        critic=critic,
        critic_buffer=critic_buffer,
        value_normalizer=value_normalizer,
    )


def _observation(sample_id: int, width: int) -> torch.Tensor:
    row = torch.linspace(-0.25, 0.25, width, dtype=torch.float32)
    row = row + float(sample_id) * 0.001
    row[0] = float(sample_id)
    return row


def _observations_for_time(time_index: int, width: int) -> torch.Tensor:
    return torch.stack(
        [_observation(time_index * ROLLOUT_THREADS + env_index, width) for env_index in range(ROLLOUT_THREADS)]
    )


def _available_actions_for_id(sample_id: int) -> torch.Tensor:
    available = torch.zeros(ACTION_DIM, dtype=torch.float32)
    active_target = (sample_id * 7 + 3) % NUM_TASKS
    available[active_target] = 1.0
    available[NOOP_RAW_ID] = 1.0
    if sample_id % 2 == 0:
        available[(active_target + 11) % NUM_TASKS] = 1.0
    return available


def _available_actions_for_time(time_index: int) -> torch.Tensor:
    return torch.stack(
        [
            _available_actions_for_id(time_index * ROLLOUT_THREADS + env_index)
            for env_index in range(ROLLOUT_THREADS)
        ]
    )


def _actions_for_ids(sample_ids: torch.Tensor) -> torch.Tensor:
    actions = []
    for sample_id_tensor in sample_ids:
        sample_id = int(sample_id_tensor.item())
        if sample_id % 3 == 1:
            actions.append(NOOP_RAW_ID)
        else:
            actions.append((sample_id * 7 + 3) % NUM_TASKS)
    return torch.tensor(actions, dtype=torch.float32).unsqueeze(-1)


def _next_masks(time_index: int) -> tuple[torch.Tensor, torch.Tensor]:
    masks = torch.ones(ROLLOUT_THREADS, 1, dtype=torch.float32)
    active_masks = torch.ones_like(masks)
    if time_index == 1:
        masks[1, 0] = 0.0
    if time_index == 2:
        active_masks[0, 0] = 0.0
    return masks, active_masks


def _populate_actor_buffer(
    actor: HAPPO,
    buffer: OnPolicyActorBuffer,
) -> torch.Tensor:
    buffer.obs[0] = _observations_for_time(0, buffer.obs.shape[-1])
    buffer.available_actions[0] = _available_actions_for_time(0)
    buffer.rnn_states[0].zero_()
    buffer.masks[0].fill_(1.0)
    buffer.active_masks[0].fill_(1.0)

    for time_index in range(ROLLOUT_LENGTH):
        current_obs = buffer.obs[time_index]
        current_available = buffer.available_actions[time_index]
        current_rnn = buffer.rnn_states[time_index]
        current_masks = buffer.masks[time_index]
        sample_ids = current_obs[:, 0].round().long()
        actions = _actions_for_ids(sample_ids)
        with torch.no_grad():
            action_log_probs, _, _ = actor.evaluate_actions(
                current_obs,
                current_rnn,
                actions,
                current_masks,
                current_available,
                buffer.active_masks[time_index],
            )
        next_obs = _observations_for_time(time_index + 1, buffer.obs.shape[-1])
        next_available = _available_actions_for_time(time_index + 1)
        next_masks, next_active_masks = _next_masks(time_index)
        buffer.insert(
            next_obs,
            torch.zeros_like(current_rnn),
            actions,
            action_log_probs.detach(),
            next_masks,
            next_active_masks,
            next_available,
        )

    advantages = torch.empty(ROLLOUT_LENGTH, ROLLOUT_THREADS, 1, dtype=torch.float32)
    factor = torch.empty_like(advantages)
    for time_index in range(ROLLOUT_LENGTH):
        for env_index in range(ROLLOUT_THREADS):
            sample_id = time_index * ROLLOUT_THREADS + env_index
            advantages[time_index, env_index, 0] = -0.75 + 0.2 * sample_id
            factor[time_index, env_index, 0] = 1.0 + 0.01 * sample_id
    buffer.update_factor(factor)
    _assert(buffer.step == 0, "actor buffer step wraps after one full synthetic rollout")
    return advantages


def _populate_critic_buffer(components: ReadinessComponents) -> torch.Tensor:
    buffer = components.critic_buffer
    critic = components.critic
    buffer.share_obs[0] = _observations_for_time(0, components.shared_dim)
    buffer.rnn_states_critic[0].zero_()
    buffer.masks[0].fill_(1.0)
    buffer.bad_masks[0].fill_(1.0)

    for time_index in range(ROLLOUT_LENGTH):
        current_share_obs = buffer.share_obs[time_index]
        with torch.no_grad():
            values, _ = critic.get_values(
                current_share_obs,
                buffer.rnn_states_critic[time_index],
                buffer.masks[time_index],
            )
        sample_ids = current_share_obs[:, 0].round()
        rewards = (0.1 + sample_ids * 0.03).unsqueeze(-1)
        next_share_obs = _observations_for_time(time_index + 1, components.shared_dim)
        next_masks, _ = _next_masks(time_index)
        bad_masks = torch.ones_like(next_masks)
        if time_index == 1:
            bad_masks[1, 0] = 0.0
        buffer.insert(
            next_share_obs,
            torch.zeros_like(buffer.rnn_states_critic[time_index]),
            values.detach(),
            rewards,
            next_masks,
            bad_masks,
        )

    with torch.no_grad():
        next_value, _ = critic.get_values(
            buffer.share_obs[-1],
            buffer.rnn_states_critic[-1],
            buffer.masks[-1],
        )
    buffer.compute_returns(next_value.detach(), components.value_normalizer)
    _assert(buffer.step == 0, "critic buffer step wraps after one full synthetic rollout")
    _assert(torch.isfinite(buffer.returns).all(), "critic returns are finite")
    advantages = buffer.returns[:-1] - components.value_normalizer.denormalize(buffer.value_preds[:-1])
    _assert(torch.isfinite(advantages).all(), "computed advantages are finite")
    return advantages


def _assert_actor_generator_alignment(
    buffer: OnPolicyActorBuffer,
    advantages: torch.Tensor,
) -> tuple[torch.Tensor, ...]:
    flattened_log_probs = buffer.action_log_probs.reshape(-1, 1)
    flattened_advantages = advantages.reshape(-1, 1)
    flattened_factor = buffer.factor.reshape(-1, 1)
    seen: set[int] = set()
    first_sample: tuple[torch.Tensor, ...] | None = None
    torch.manual_seed(1201)
    for sample in buffer.feed_forward_generator_actor(advantages, actor_num_mini_batch=2):
        _assert(len(sample) == 9, "HAPPO actor generator includes factor")
        if first_sample is None:
            first_sample = sample
        (
            obs_batch,
            rnn_states_batch,
            actions_batch,
            masks_batch,
            active_masks_batch,
            old_action_log_probs_batch,
            adv_targ,
            available_actions_batch,
            factor_batch,
        ) = sample
        _assert(rnn_states_batch.shape[1:] == (1, 256), "actor generator RNN placeholder shape")
        _assert(masks_batch.shape[-1] == 1, "actor generator masks")
        _assert(active_masks_batch.shape[-1] == 1, "actor generator active masks")
        for row_index in range(obs_batch.shape[0]):
            sample_id = int(round(float(obs_batch[row_index, 0].item())))
            seen.add(sample_id)
            expected_available = _available_actions_for_id(sample_id)
            expected_action = int(_actions_for_ids(torch.tensor([sample_id]))[0, 0].item())
            _assert(
                torch.equal(available_actions_batch[row_index].cpu(), expected_available),
                f"historical available-actions alignment for sample {sample_id}",
            )
            _assert(int(actions_batch[row_index, 0].item()) == expected_action, "action/sample alignment")
            _assert(
                torch.equal(old_action_log_probs_batch[row_index], flattened_log_probs[sample_id]),
                "old log-prob/sample alignment",
            )
            _assert(
                torch.equal(adv_targ[row_index], flattened_advantages[sample_id]),
                "advantage/sample alignment",
            )
            _assert(
                torch.equal(factor_batch[row_index], flattened_factor[sample_id]),
                "factor/sample alignment",
            )
            action_id = int(actions_batch[row_index, 0].item())
            _assert(available_actions_batch[row_index, action_id] == 1, "sampled action remains available")
    _assert(seen == set(range(ROLLOUT_LENGTH * ROLLOUT_THREADS)), "actor generator covers every sample")
    _assert(first_sample is not None, "actor generator yielded a batch")
    return first_sample


def _assert_critic_generator_alignment(
    buffer: OnPolicyCriticBufferEP,
) -> tuple[torch.Tensor, ...]:
    flat_value_preds = buffer.value_preds[:-1].reshape(-1, 1)
    flat_returns = buffer.returns[:-1].reshape(-1, 1)
    flat_masks = buffer.masks[:-1].reshape(-1, 1)
    seen: set[int] = set()
    first_sample: tuple[torch.Tensor, ...] | None = None
    torch.manual_seed(1202)
    for sample in buffer.feed_forward_generator_critic(critic_num_mini_batch=2):
        if first_sample is None:
            first_sample = sample
        share_obs, rnn_states, value_preds, returns, masks = sample
        _assert(rnn_states.shape[1:] == (1, 256), "critic generator RNN placeholder shape")
        for row_index in range(share_obs.shape[0]):
            sample_id = int(round(float(share_obs[row_index, 0].item())))
            seen.add(sample_id)
            _assert(torch.equal(value_preds[row_index], flat_value_preds[sample_id]), "value/sample alignment")
            _assert(torch.equal(returns[row_index], flat_returns[sample_id]), "return/sample alignment")
            _assert(torch.equal(masks[row_index], flat_masks[sample_id]), "critic mask/sample alignment")
    _assert(seen == set(range(ROLLOUT_LENGTH * ROLLOUT_THREADS)), "critic generator covers every sample")
    _assert(first_sample is not None, "critic generator yielded a batch")
    return first_sample


def _parameter_snapshot(module: torch.nn.Module) -> list[torch.Tensor]:
    return [parameter.detach().clone() for parameter in module.parameters()]


def _parameters_changed(before: list[torch.Tensor], module: torch.nn.Module) -> bool:
    return any(not torch.equal(old, new.detach()) for old, new in zip(before, module.parameters()))


def _parameters_equal(before: list[torch.Tensor], module: torch.nn.Module) -> bool:
    return all(torch.equal(old, new.detach()) for old, new in zip(before, module.parameters()))


def _gradient_evidence(module: torch.nn.Module) -> tuple[int, float]:
    gradients = [parameter.grad for parameter in module.parameters() if parameter.grad is not None]
    _assert(gradients, "at least one trainable parameter receives a gradient")
    for parameter, gradient in [
        (parameter, parameter.grad)
        for parameter in module.parameters()
        if parameter.grad is not None
    ]:
        _assert(gradient.shape == parameter.shape, "gradient shape matches parameter shape")
        _assert(torch.isfinite(gradient).all(), "gradient is finite")
    squared_norm = sum(float(torch.sum(gradient.detach() ** 2).item()) for gradient in gradients)
    return len(gradients), math.sqrt(squared_norm)


def _assert_finite_parameters(module: torch.nn.Module) -> None:
    for parameter in module.parameters():
        _assert(torch.isfinite(parameter).all(), "updated model parameter is finite")


def _run_profile(profile: str) -> ReadinessResult:
    seed = 8404 if profile == "lifecycle_contract_c" else 8405
    with _isolated_seed(seed):
        components = _construct_components(profile)
        actors = components.actors
        critic = components.critic
        actor = actors[0]

        batch_size = 4
        actor_obs = torch.stack([_observation(index, components.actor_dim) for index in range(batch_size)])
        shared_obs = torch.stack([_observation(index, components.shared_dim) for index in range(batch_size)])
        available_actions = torch.stack([_available_actions_for_id(index) for index in range(batch_size)])
        action_ids = _actions_for_ids(torch.arange(batch_size))
        rnn_states = torch.zeros(batch_size, 1, 256)
        masks = torch.ones(batch_size, 1)
        active_masks = torch.ones(batch_size, 1)
        advantages_for_validation = torch.linspace(-1.0, 1.0, batch_size).unsqueeze(-1)
        returns_for_validation = torch.linspace(0.1, 0.4, batch_size).unsqueeze(-1)
        _validate_batch(
            actor_obs=actor_obs,
            shared_obs=shared_obs,
            available_actions=available_actions,
            actions=action_ids,
            advantages=advantages_for_validation,
            returns=returns_for_validation,
            actor_dim=components.actor_dim,
            shared_dim=components.shared_dim,
        )

        with torch.no_grad():
            sampled_actions, sampled_log_probs, returned_rnn = actor.get_actions(
                actor_obs,
                rnn_states,
                masks,
                available_actions,
                deterministic=False,
            )
            evaluated_log_probs, entropy, distribution = actor.evaluate_actions(
                actor_obs,
                rnn_states,
                action_ids,
                masks,
                available_actions,
                active_masks,
            )
        _assert(sampled_actions.shape == (batch_size, 1), "actor action shape")
        _assert(sampled_log_probs.shape == (batch_size, 1), "actor log-prob shape")
        _assert(returned_rnn.shape == (batch_size, 1, 256), "actor returned RNN placeholder shape")
        _assert(torch.isfinite(sampled_log_probs).all(), "sampled log probabilities are finite")
        _assert(torch.isfinite(evaluated_log_probs).all(), "evaluated log probabilities are finite")
        _assert(torch.isfinite(entropy), "actor entropy is finite")
        _assert(
            torch.all(available_actions.gather(1, sampled_actions.long()) == 1),
            "sampled actions obey available-actions",
        )
        masked_probabilities = distribution.probs[available_actions == 0]
        _assert(torch.all(masked_probabilities <= 1.0e-12), "unavailable categorical probability is zero")
        _assert(torch.all(distribution.probs[:, NOOP_RAW_ID] > 0), "noop remains sampleable")

        with torch.no_grad():
            values, critic_rnn = critic.get_values(shared_obs, rnn_states, masks)
        _assert(values.shape == (batch_size, 1), "critic value shape")
        _assert(critic_rnn.shape == (batch_size, 1, 256), "critic returned RNN placeholder shape")
        _assert(torch.isfinite(values).all(), "critic values are finite")

        actor_advantages = _populate_actor_buffer(actor, components.actor_buffers[0])
        for other_actor, other_buffer in zip(actors[1:], components.actor_buffers[1:]):
            _populate_actor_buffer(other_actor, other_buffer)
        critic_advantages = _populate_critic_buffer(components)
        _assert(torch.isfinite(critic_advantages).all(), "critic-derived advantages are finite")

        actor_sample = _assert_actor_generator_alignment(
            components.actor_buffers[0],
            actor_advantages,
        )
        critic_sample = _assert_critic_generator_alignment(components.critic_buffer)

        actor_before = _parameter_snapshot(actor.actor)
        actor_1_before = _parameter_snapshot(actors[1].actor)
        actor_2_before = _parameter_snapshot(actors[2].actor)
        policy_loss, update_entropy, actor_grad_norm, importance_ratio = actor.update(actor_sample)
        _assert(torch.isfinite(policy_loss), "HAPPO policy loss is finite")
        _assert(torch.isfinite(update_entropy), "HAPPO update entropy is finite")
        _assert(torch.isfinite(actor_grad_norm), "HAPPO pre-clip gradient norm is finite")
        _assert(torch.isfinite(importance_ratio).all(), "HAPPO importance ratio is finite")
        actor_gradient_count, actor_post_clip_norm = _gradient_evidence(actor.actor)
        _assert(_parameters_changed(actor_before, actor.actor), "actor optimizer changes a parameter")
        _assert(_parameters_equal(actor_1_before, actors[1].actor), "actor 1 remains unchanged")
        _assert(_parameters_equal(actor_2_before, actors[2].actor), "actor 2 remains unchanged")
        _assert_finite_parameters(actor.actor)
        _assert(actor.actor_optimizer.state, "actor optimizer state exists after first step")

        with torch.no_grad():
            _, _, post_update_distribution = actor.evaluate_actions(
                actor_sample[0],
                actor_sample[1],
                actor_sample[2],
                actor_sample[3],
                actor_sample[7],
                actor_sample[4],
            )
        _assert(
            torch.all(post_update_distribution.probs[actor_sample[7] == 0] <= 1.0e-12),
            "historical unavailable actions remain excluded after actor update",
        )

        critic_before = _parameter_snapshot(critic.critic)
        value_norm_before = components.value_normalizer.debiasing_term.detach().clone()
        value_loss, critic_grad_norm = critic.update(
            critic_sample,
            value_normalizer=components.value_normalizer,
        )
        _assert(torch.isfinite(value_loss), "VCritic value loss is finite")
        _assert(torch.isfinite(critic_grad_norm), "VCritic pre-clip gradient norm is finite")
        critic_gradient_count, critic_post_clip_norm = _gradient_evidence(critic.critic)
        _assert(_parameters_changed(critic_before, critic.critic), "critic optimizer changes a parameter")
        _assert_finite_parameters(critic.critic)
        _assert(critic.critic_optimizer.state, "critic optimizer state exists after first step")
        value_norm_changed = not torch.equal(value_norm_before, components.value_normalizer.debiasing_term)
        _assert(value_norm_changed, "ValueNorm updates through the real critic update path")
        mean, variance = components.value_normalizer.running_mean_var()
        _assert(torch.isfinite(mean).all() and torch.isfinite(variance).all(), "ValueNorm state is finite")

        actor_buffer = components.actor_buffers[0]
        actor_last_obs = actor_buffer.obs[-1].clone()
        actor_last_available = actor_buffer.available_actions[-1].clone()
        actor_buffer.after_update()
        _assert(torch.equal(actor_buffer.obs[0], actor_last_obs), "actor after_update observation copy")
        _assert(
            torch.equal(actor_buffer.available_actions[0], actor_last_available),
            "actor after_update available-actions copy",
        )
        critic_last_share_obs = components.critic_buffer.share_obs[-1].clone()
        components.critic_buffer.after_update()
        _assert(
            torch.equal(components.critic_buffer.share_obs[0], critic_last_share_obs),
            "critic after_update shared observation copy",
        )

        return ReadinessResult(
            profile=profile,
            actor_dimension=components.actor_dim,
            shared_dimension=components.shared_dim,
            action_dimension=ACTION_DIM,
            actor_parameter_count=sum(parameter.numel() for parameter in actor.actor.parameters()),
            critic_parameter_count=sum(parameter.numel() for parameter in critic.critic.parameters()),
            actor_parameters_with_gradients=actor_gradient_count,
            critic_parameters_with_gradients=critic_gradient_count,
            actor_gradient_norm_pre_clip=float(actor_grad_norm.detach().item()),
            actor_gradient_norm_post_clip=actor_post_clip_norm,
            critic_gradient_norm_pre_clip=float(critic_grad_norm.detach().item()),
            critic_gradient_norm_post_clip=critic_post_clip_norm,
            actor_loss=float(policy_loss.detach().item()),
            actor_entropy=float(update_entropy.detach().item()),
            critic_loss=float(value_loss.detach().item()),
            actor_forward_passed=True,
            critic_forward_passed=True,
            actor_buffer_passed=True,
            critic_buffer_passed=True,
            actor_generator_passed=True,
            critic_generator_passed=True,
            actor_parameter_changed=True,
            critic_parameter_changed=True,
            independent_actors_unchanged=True,
            value_norm_changed=value_norm_changed,
        )


_RESULTS: dict[str, ReadinessResult] = {}


def _result(profile: str) -> ReadinessResult:
    if profile not in _RESULTS:
        _RESULTS[profile] = _run_profile(profile)
    return _RESULTS[profile]


def test_effective_config_and_real_harl_construction() -> None:
    result = _result("lifecycle_contract_c")
    _assert(result.actor_dimension == LIFECYCLE_ACTOR_DIM, "lifecycle actor dimension")
    _assert(result.shared_dimension == LIFECYCLE_SHARED_DIM, "lifecycle shared dimension")
    _assert(result.action_dimension == ACTION_DIM, "lifecycle action dimension")


def test_lifecycle_actor_forward_and_masked_categorical() -> None:
    result = _result("lifecycle_contract_c")
    _assert(result.actor_forward_passed, "lifecycle actor forward")


def test_lifecycle_critic_forward() -> None:
    _assert(_result("lifecycle_contract_c").critic_forward_passed, "lifecycle critic forward")


def test_lifecycle_actor_buffer_insertion_and_after_update() -> None:
    _assert(_result("lifecycle_contract_c").actor_buffer_passed, "lifecycle actor buffer")


def test_lifecycle_ep_critic_buffer_returns_and_after_update() -> None:
    _assert(_result("lifecycle_contract_c").critic_buffer_passed, "lifecycle critic buffer")


def test_lifecycle_actor_generator_alignment() -> None:
    _assert(_result("lifecycle_contract_c").actor_generator_passed, "actor generator alignment")


def test_lifecycle_critic_generator_alignment() -> None:
    _assert(_result("lifecycle_contract_c").critic_generator_passed, "critic generator alignment")


def test_lifecycle_happo_backward_and_optimizer() -> None:
    result = _result("lifecycle_contract_c")
    _assert(math.isfinite(result.actor_loss), "finite lifecycle actor loss")
    _assert(result.actor_parameters_with_gradients > 0, "lifecycle actor gradients")
    _assert(result.actor_parameter_changed, "lifecycle actor parameter change")


def test_lifecycle_vcritic_backward_and_optimizer() -> None:
    result = _result("lifecycle_contract_c")
    _assert(math.isfinite(result.critic_loss), "finite lifecycle critic loss")
    _assert(result.critic_parameters_with_gradients > 0, "lifecycle critic gradients")
    _assert(result.critic_parameter_changed, "lifecycle critic parameter change")


def test_lifecycle_independent_actor_update_isolation() -> None:
    _assert(_result("lifecycle_contract_c").independent_actors_unchanged, "independent actor isolation")


def test_lifecycle_valuenorm_path() -> None:
    _assert(_result("lifecycle_contract_c").value_norm_changed, "lifecycle ValueNorm update")


def test_legacy_actor_critic_buffer_readiness() -> None:
    result = _result("legacy")
    _assert(result.actor_dimension == LEGACY_ACTOR_DIM, "legacy actor dimension")
    _assert(result.shared_dimension == LEGACY_SHARED_DIM, "legacy shared dimension")
    _assert(result.actor_forward_passed and result.critic_forward_passed, "legacy forward readiness")
    _assert(result.actor_buffer_passed and result.critic_buffer_passed, "legacy buffer readiness")


def test_legacy_forward_backward_optimizer_readiness() -> None:
    result = _result("legacy")
    _assert(result.actor_parameter_changed, "legacy actor optimizer readiness")
    _assert(result.critic_parameter_changed, "legacy critic optimizer readiness")
    _assert(result.independent_actors_unchanged, "legacy independent actor isolation")
    _assert(result.value_norm_changed, "legacy ValueNorm path")


def test_negative_dimensions_masks_and_finite_checks() -> None:
    actor_obs = torch.zeros(2, LIFECYCLE_ACTOR_DIM)
    shared_obs = torch.zeros(2, LIFECYCLE_SHARED_DIM)
    available = torch.stack([_available_actions_for_id(0), _available_actions_for_id(1)])
    actions = _actions_for_ids(torch.tensor([0, 1]))
    advantages = torch.ones(2, 1)
    returns = torch.ones(2, 1)

    def validate(
        *,
        actor: torch.Tensor = actor_obs,
        shared: torch.Tensor = shared_obs,
        mask: torch.Tensor = available,
        selected_actions: torch.Tensor = actions,
        adv: torch.Tensor = advantages,
        ret: torch.Tensor = returns,
    ) -> None:
        _validate_batch(
            actor_obs=actor,
            shared_obs=shared,
            available_actions=mask,
            actions=selected_actions,
            advantages=adv,
            returns=ret,
            actor_dim=LIFECYCLE_ACTOR_DIM,
            shared_dim=LIFECYCLE_SHARED_DIM,
        )

    for width in (LIFECYCLE_ACTOR_DIM - 1, LIFECYCLE_ACTOR_DIM + 1):
        _expect_raises(lambda width=width: validate(actor=torch.zeros(2, width)), "actor observation width")
    for width in (LIFECYCLE_SHARED_DIM - 1, LIFECYCLE_SHARED_DIM + 1):
        _expect_raises(lambda width=width: validate(shared=torch.zeros(2, width)), "shared observation width")
    for width in (ACTION_DIM - 1, ACTION_DIM + 1):
        _expect_raises(lambda width=width: validate(mask=torch.ones(2, width)), "available_actions width")
    _expect_raises(lambda: validate(mask=torch.zeros_like(available)), "at least one enabled action")
    invalid_actions = actions.clone()
    invalid_actions[0, 0] = 0 if available[0, 0] == 0 else 1
    if available[0, int(invalid_actions[0, 0].item())] != 0:
        invalid_actions[0, 0] = int(torch.nonzero(available[0] == 0)[0, 0].item())
    _expect_raises(lambda: validate(selected_actions=invalid_actions), "selected action is unavailable")
    nan_actor = actor_obs.clone()
    nan_actor[0, 1] = torch.nan
    _expect_raises(lambda: validate(actor=nan_actor), "actor observation must be finite")
    nan_shared = shared_obs.clone()
    nan_shared[0, 1] = torch.nan
    _expect_raises(lambda: validate(shared=nan_shared), "shared observation must be finite")
    nan_advantages = advantages.clone()
    nan_advantages[0, 0] = torch.nan
    _expect_raises(lambda: validate(adv=nan_advantages), "advantages must be finite")
    nan_returns = returns.clone()
    nan_returns[0, 0] = torch.nan
    _expect_raises(lambda: validate(ret=nan_returns), "returns must be finite")

    components = _construct_components("lifecycle_contract_c")
    actor = components.actors[0]
    rnn_states = torch.zeros(2, 1, 256)
    masks = torch.ones(2, 1)
    _expect_raises(
        lambda: actor.get_actions(torch.zeros(2, LIFECYCLE_ACTOR_DIM - 1), rnn_states, masks, available),
        "normalized_shape",
    )
    _expect_raises(
        lambda: components.critic.get_values(
            torch.zeros(2, LIFECYCLE_SHARED_DIM + 1),
            rnn_states,
            masks,
        ),
        "normalized_shape",
    )


def test_unsupported_actor_count_share_param_recurrent_and_fp_guards() -> None:
    common = {
        "profile": "lifecycle_contract_c",
        "actor_dim": LIFECYCLE_ACTOR_DIM,
        "shared_dim": LIFECYCLE_SHARED_DIM,
    }
    _expect_raises(lambda: _validate_official_support(**common, actor_count=2), "actor count")
    _expect_raises(lambda: _validate_official_support(**common, share_param=True), "share_param=false")
    _expect_raises(lambda: _validate_official_support(**common, state_type="FP"), "EP state type only")
    _expect_raises(
        lambda: _validate_official_support(**common, use_recurrent_policy=True),
        "feed-forward policies only",
    )
    _expect_raises(
        lambda: _validate_official_support(**common, use_naive_recurrent_policy=True),
        "feed-forward policies only",
    )


TESTS = (
    test_effective_config_and_real_harl_construction,
    test_lifecycle_actor_forward_and_masked_categorical,
    test_lifecycle_critic_forward,
    test_lifecycle_actor_buffer_insertion_and_after_update,
    test_lifecycle_ep_critic_buffer_returns_and_after_update,
    test_lifecycle_actor_generator_alignment,
    test_lifecycle_critic_generator_alignment,
    test_lifecycle_happo_backward_and_optimizer,
    test_lifecycle_vcritic_backward_and_optimizer,
    test_lifecycle_independent_actor_update_isolation,
    test_lifecycle_valuenorm_path,
    test_legacy_actor_critic_buffer_readiness,
    test_legacy_forward_backward_optimizer_readiness,
    test_negative_dimensions_masks_and_finite_checks,
    test_unsupported_actor_count_share_param_recurrent_and_fp_guards,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary.")
    args = parser.parse_args()
    torch.set_num_threads(1)
    results = []
    failed = False
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone runner records every readiness failure.
            failed = True
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    payload = {
        "status": "failed" if failed else "passed",
        "python": sys.executable,
        "torch": torch.__version__,
        "device": str(DEVICE),
        "effective_classes": {
            "actor": f"{HAPPO.__module__}.{HAPPO.__name__}",
            "critic": f"{VCritic.__module__}.{VCritic.__name__}",
            "actor_buffer": f"{OnPolicyActorBuffer.__module__}.{OnPolicyActorBuffer.__name__}",
            "critic_buffer": f"{OnPolicyCriticBufferEP.__module__}.{OnPolicyCriticBufferEP.__name__}",
            "value_normalizer": f"{ValueNorm.__module__}.{ValueNorm.__name__}",
        },
        "readiness": {profile: asdict(result) for profile, result in sorted(_RESULTS.items())},
        "tests": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            prefix = "PASS" if result["status"] == "passed" else "FAIL"
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{prefix} {result['name']}{suffix}")
        for profile, readiness in sorted(_RESULTS.items()):
            print(
                f"METRICS {profile}: actor_params={readiness.actor_parameter_count}, "
                f"critic_params={readiness.critic_parameter_count}, "
                f"actor_grad={readiness.actor_gradient_norm_pre_clip:.6f}, "
                f"critic_grad={readiness.critic_gradient_norm_pre_clip:.6f}"
            )
        print(f"{'FAIL' if failed else 'PASS'} {len(results)} actor/critic/buffer readiness tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
