# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Repo-local HARL training shim for assignment-based scan RL.

The installed HARL package already supports Discrete policies and available action
masks, but its IsaacLab env facade forwards raw continuous actions and its base
runner assumes every action space has ``shape[0]``. This module keeps the
assignment integration local to this repository: it constructs the normal scan
env, wraps it with ``AssignmentHarlWrapper``, and uses a runner subclass whose
initialization computes scalar action storage dims through the Phase 2 adapter.
"""

import time
from collections.abc import Collection
from typing import Any, Mapping

import gymnasium as gym
import numpy as np
import setproctitle
import torch

from harl.algorithms.actors import ALGO_REGISTRY
from harl.algorithms.critics.v_critic import VCritic
from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer
from harl.common.buffers.on_policy_critic_buffer_ep import OnPolicyCriticBufferEP
from harl.common.buffers.on_policy_critic_buffer_fp import OnPolicyCriticBufferFP
from harl.common.valuenorm import ValueNorm
from harl.envs import LOGGER_REGISTRY
from harl.envs.isaaclab.Isaac_lab_logger import IsaacLabLogger
from harl.runners.on_policy_ha_runner import OnPolicyHARunner
from harl.utils.configs_tools import init_dir, save_config
from harl.utils.envs_tools import make_eval_env, make_render_env, make_train_env, set_seed
from harl.utils.models_tools import init_device

try:
    from .assignment_checkpoint_contract import CompatibilityPurpose
    from .assignment_checkpoint_load import load_assignment_checkpoint
    from .assignment_checkpoint_save import (
        AssignmentCheckpointSaveCoordinator,
        AssignmentCheckpointSaveError,
        build_assignment_checkpoint_contract_manifest,
        capture_assignment_checkpoint_runtime_state,
        infer_assignment_checkpoint_kind,
    )
    from .assignment_harl_adapter import get_harl_scalar_action_dim
    from .assignment_harl_wrapper import AssignmentHarlWrapper
    from .assignment_lifecycle_training_contract import validate_assignment_lifecycle_policy_sequence
    from .assignment_value_normalizer_checkpoint import export_value_normalizer_checkpoint_state
except ImportError:  # Allows direct file-based smoke tests after adding this directory to sys.path.
    from assignment_checkpoint_contract import CompatibilityPurpose  # type: ignore
    from assignment_checkpoint_load import load_assignment_checkpoint  # type: ignore
    from assignment_checkpoint_save import (  # type: ignore
        AssignmentCheckpointSaveCoordinator,
        AssignmentCheckpointSaveError,
        build_assignment_checkpoint_contract_manifest,
        capture_assignment_checkpoint_runtime_state,
        infer_assignment_checkpoint_kind,
    )
    from assignment_harl_adapter import get_harl_scalar_action_dim  # type: ignore
    from assignment_harl_wrapper import AssignmentHarlWrapper  # type: ignore
    from assignment_lifecycle_training_contract import validate_assignment_lifecycle_policy_sequence  # type: ignore
    from assignment_value_normalizer_checkpoint import export_value_normalizer_checkpoint_state  # type: ignore


SUPPORTED_ASSIGNMENT_ALGORITHMS = ("happo", "hatrpo", "haa2c")
ASSIGNMENT_REWARD_LOG_FIELDS = (
    "base_env_reward",
    "repeated_same_target_no_progress",
    "global_no_progress",
    "selected_path_cost",
    "total_assignment_reward_adjustment",
    "final_reward",
    "steps_since_global_coverage_gain",
    "global_coverage_gain",
)
ASSIGNMENT_REWARD_ACCUMULATOR_KEYS = frozenset({"assignment_rl_reward/final_reward_mean"})


def apply_assignment_episode_length_override(algo_args: dict[str, Any], episode_length: int | None) -> int | None:
    """Apply an assignment-only HARL rollout length override without touching global defaults."""

    if episode_length is None:
        return None
    value = int(episode_length)
    if value <= 0:
        raise ValueError(f"assignment_episode_length must be positive, got {episode_length!r}")
    algo_args["train"]["episode_length"] = value
    return value


def _to_scalar(value: Any) -> float | None:
    if isinstance(value, torch.Tensor):
        if value.numel() == 0:
            return None
        return float(value.detach().to(dtype=torch.float32).mean().cpu().item())
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return None
        return float(np.asarray(value, dtype=np.float32).mean())
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return None
        try:
            array = np.asarray(value, dtype=np.float32)
        except (TypeError, ValueError):
            return None
        if array.size == 0:
            return None
        return float(array.mean())
    if isinstance(value, (np.integer, np.floating)):
        return float(value.item())
    if isinstance(value, (int, float, bool)):
        return float(value)
    return None


def _flatten_numeric_log(data: Mapping[str, Any], prefix: str = "") -> dict[str, float]:
    log: dict[str, float] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            log.update(_flatten_numeric_log(value, full_key))
            continue
        scalar = _to_scalar(value)
        if scalar is not None:
            log[full_key] = scalar
    return log


def _flatten_assignment_reward_log(data: Mapping[str, Any]) -> dict[str, float]:
    log: dict[str, float] = {}
    for key in ASSIGNMENT_REWARD_LOG_FIELDS:
        if key not in data:
            continue
        scalar = _to_scalar(data[key])
        if scalar is not None:
            log[f"assignment_rl_reward/{key}_mean"] = scalar
    return log


def _should_accumulate_reward_key(key: str, reward_accumulator_keys: Collection[str] | None) -> bool:
    """Return whether a scalar key contributes to the logger's Total_Reward accumulator."""

    if reward_accumulator_keys is None:
        return "reward" in key.lower()
    return key in reward_accumulator_keys


def _compute_reward_accumulator_total(
    other_data_log: Mapping[str, Collection[float]],
    reward_accumulator_keys: Collection[str] | None,
) -> float:
    """Compute Total_Reward from logged scalars using an optional exact-key whitelist."""

    total_reward = 0.0
    for key, values in other_data_log.items():
        if _should_accumulate_reward_key(key, reward_accumulator_keys):
            total_reward += float(np.sum(values))
    return total_reward


class AssignmentIsaacLabLogger(IsaacLabLogger):
    """IsaacLab logger with exact reward-accounting keys for assignment RL."""

    def __init__(self, *args, reward_accumulator_keys: Collection[str] | None = None, **kwargs) -> None:
        self.reward_accumulator_keys = (
            frozenset(reward_accumulator_keys) if reward_accumulator_keys is not None else None
        )
        super().__init__(*args, **kwargs)
        if self.reward_accumulator_keys is not None:
            print(
                "[INFO]: Assignment RL Total_Reward accumulator whitelist: "
                f"{sorted(self.reward_accumulator_keys)}"
            )

    def episode_log(
        self,
        actor_train_infos,
        critic_train_info,
        actor_buffer,
        critic_buffer,
    ):
        """Log one episode, using the assignment reward whitelist for Total_Reward."""

        self.total_num_steps = (
            self.episode
            * self.algo_args["train"]["episode_length"]
            * self.algo_args["train"]["n_rollout_threads"]
        )
        self.end = time.time()

        self.total_reward = 0.0
        if self.other_data_log:
            print("\n===== Averages for the episode =====")
            self.total_reward = _compute_reward_accumulator_total(
                self.other_data_log,
                self.reward_accumulator_keys,
            )
            for key, values in self.other_data_log.items():
                mean_val = np.mean(values)
                print(f"{key}: {mean_val}")
                self.writter.add_scalar(key, mean_val, self.total_num_steps)

            self.other_data_log.clear()

            self.writter.add_scalar("Total_Reward", self.total_reward, self.total_num_steps)
            print("Total Reward is {}.".format(self.total_reward))

        print("==============================================")
        print(
            "Env {} Task {} Algo {} Exp {} episodes {}/{} total num timesteps {}/{}, FPS {}.".format(
                self.args["env"],
                self.task_name,
                self.args["algo"],
                self.args["exp_name"],
                self.episode,
                self.episodes,
                self.total_num_steps,
                self.algo_args["train"]["num_env_steps"],
                int(self.total_num_steps / (self.end - self.start)),
            )
        )

        self.log_actor(actor_train_infos)
        if isinstance(critic_buffer, dict):
            for team, buffer in critic_buffer.items():
                critic_train_info[team][f"average_step_rewards_{team}"] = buffer.get_mean_rewards()
                print(
                    "Average step reward for {} is {}.\n".format(
                        team, critic_train_info[team][f"average_step_rewards_{team}"]
                    )
                )
                for k, v in critic_train_info[team].items():
                    critic_k = f"critic/{team}/" + k
                    self.writter.add_scalar(critic_k, v, self.total_num_steps)
        else:
            critic_train_info["average_step_rewards"] = critic_buffer.get_mean_rewards()
            print(
                "Average step reward is {}.\n".format(
                    critic_train_info["average_step_rewards"]
                )
            )
            self.log_critic(critic_train_info)


class AssignmentIsaacLabEnv:
    """HARL-facing env facade that routes Discrete ids through assignment control."""

    def __init__(self, env_args: dict[str, Any]) -> None:
        if not env_args.get("assignment_rl", False):
            raise ValueError("AssignmentIsaacLabEnv requires env_args['assignment_rl']=True")

        self.env_args = env_args
        render_mode = "rgb_array" if env_args.get("video_settings", {}).get("video", False) else None
        raw_env = gym.make(env_args["task"], cfg=env_args["config"], render_mode=render_mode)

        if env_args.get("video_settings", {}).get("video", False):
            video_settings = env_args["video_settings"]
            raw_env = gym.wrappers.RecordVideo(
                raw_env,
                video_folder=video_settings["log_dir"],
                step_trigger=lambda step: step % video_settings["video_interval"] == 0,
                video_length=video_settings["video_length"],
                disable_logger=True,
            )

        self.assignment_env = AssignmentHarlWrapper(raw_env)
        profile_config = self.assignment_env.assignment_lifecycle_profile_config
        if not bool(profile_config.get("training_allowed", True)):
            raise RuntimeError(
                str(
                    profile_config.get(
                        "training_blocked_reason",
                        f"assignment_lifecycle_profile={profile_config.get('profile_name')!r} is not training-ready.",
                    )
                )
            )
        # HARL save() and video finalization traverse runner.env.env.*.
        self.env = self.assignment_env
        self.unwrapped = self.assignment_env.unwrapped
        self.log_info: dict[str, float] = {}

        self.n_envs = int(env_args["n_threads"])
        self.n_agents = self.assignment_env.num_agents
        self.num_agents = self.assignment_env.num_agents
        self.num_viewpoints = self.assignment_env.num_viewpoints
        self.noop_action_id = self.assignment_env.noop_action_id
        self.share_observation_space = self.assignment_env.share_observation_space
        self.observation_space = self.assignment_env.observation_space
        self.action_space = self.assignment_env.action_space
        self.last_available_actions: torch.Tensor | None = None
        self._printed_reset_summary = False

    def reset(self):
        obs, shared_obs, available_actions = self.assignment_env.reset()
        self.last_available_actions = available_actions
        self._assert_available_actions(available_actions)
        if not self._printed_reset_summary:
            print(
                "[INFO]: Assignment RL reset returned available_actions "
                f"shape={tuple(available_actions.shape)} device={available_actions.device}"
            )
            self._printed_reset_summary = True
        return self._ordered_obs(obs), shared_obs, available_actions

    def step(self, actions):
        if not isinstance(actions, torch.Tensor):
            actions = torch.as_tensor(actions, device=self.assignment_env.device)

        obs, shared_obs, rewards, dones, info, available_actions = self.assignment_env.step(actions)
        self.last_available_actions = available_actions
        self._assert_available_actions(available_actions)
        self._update_log_info(info)
        return self._ordered_obs(obs), shared_obs, rewards, dones, self._empty_infos(), available_actions

    def close(self) -> None:
        sim = getattr(self.unwrapped, "sim", None)
        if sim is not None:
            try:
                sim._disable_app_control_on_stop_handle = True
            except Exception:
                pass
        self.assignment_env.close()

    def _ordered_obs(self, obs: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        return {agent: obs[agent] for agent in self.assignment_env.agents}

    def _empty_infos(self) -> list[list[dict]]:
        return [[{} for _ in range(self.n_agents)] for _ in range(self.n_envs)]

    def _assert_available_actions(self, available_actions: torch.Tensor | None) -> None:
        if available_actions is None:
            raise RuntimeError("assignment_rl requires available_actions, got None")
        expected_shape = (self.n_envs, self.n_agents, self.num_viewpoints + 1)
        if tuple(available_actions.shape) != expected_shape:
            raise RuntimeError(
                f"assignment_rl available_actions must have shape {expected_shape}, "
                f"got {tuple(available_actions.shape)}"
            )
        if bool((available_actions.sum(dim=-1) <= 0.0).any()):
            raise RuntimeError("assignment_rl available_actions contains an all-zero row")
        if not bool(torch.all(available_actions[..., -1] > 0.0)):
            raise RuntimeError("assignment_rl no-op action must remain available")

    def _update_log_info(self, info: Any) -> None:
        log_info: dict[str, float] = {}
        if isinstance(info, Mapping):
            raw_log = info.get("log")
            if isinstance(raw_log, Mapping):
                log_info.update(_flatten_numeric_log(raw_log))
            assignment_log = info.get("assignment_rl")
            if isinstance(assignment_log, Mapping):
                log_info.update(_flatten_numeric_log(assignment_log, "assignment_rl"))
            cooldown_log = info.get("assignment_cooldown")
            if isinstance(cooldown_log, Mapping):
                log_info.update(_flatten_numeric_log(cooldown_log, "assignment_cooldown"))
            assignment_reward_log = info.get("assignment_rl_reward")
            if isinstance(assignment_reward_log, Mapping):
                log_info.update(_flatten_assignment_reward_log(assignment_reward_log))
        self.log_info = log_info


def make_assignment_train_env(env_name: str, seed: int, n_threads: int, env_args: dict[str, Any]):
    if env_name == "isaaclab" and env_args.get("assignment_rl", False):
        return AssignmentIsaacLabEnv({"n_threads": n_threads, **env_args})
    return make_train_env(env_name, seed, n_threads, env_args)


def get_assignment_num_agents(env_name: str, env_args: dict[str, Any], envs: Any) -> int:
    if env_name == "isaaclab" and env_args.get("assignment_rl", False):
        return envs.n_agents

    from harl.utils.envs_tools import get_num_agents

    return get_num_agents(env_name, env_args, envs)


class AssignmentOnPolicyHARunner(OnPolicyHARunner):
    """HARL HA runner with repo-local assignment env and Discrete action dim support."""

    def __init__(self, args, algo_args, env_args):
        self.assignment_rl = bool(env_args.get("assignment_rl", False))
        self._assignment_checkpoint_generation = 0
        self._assignment_checkpoint_coordinator: AssignmentCheckpointSaveCoordinator | None = None
        self.assignment_checkpoint_load_result = None
        self.assignment_policy_sequence_contract = (
            validate_assignment_lifecycle_policy_sequence(algo_args=algo_args, env_args=env_args)
            if self.assignment_rl
            else None
        )
        self._assignment_collect_mask_printed = False

        self.args = args
        self.algo_args = algo_args
        self.env_args = env_args
        self.best_avg_reward = -torch.inf
        self.hidden_sizes = algo_args["model"]["hidden_sizes"]
        self.hidden_sizes_critic = algo_args["model"]["hidden_sizes"]
        self.rnn_hidden_size = self.hidden_sizes[-1]
        self.rnn_hidden_size_critic = self.hidden_sizes_critic[-1]
        self.recurrent_n = algo_args["model"]["recurrent_n"]
        self.action_aggregation = algo_args["algo"]["action_aggregation"]
        self.state_type = env_args.get("state_type", "EP")
        self.share_param = algo_args["algo"]["share_param"]
        self.fixed_order = algo_args["algo"]["fixed_order"]
        self.save_entire_model = (
            algo_args["train"]["save_entire_model"] if "save_entire_model" in algo_args["train"] else False
        )
        set_seed(algo_args["seed"])
        self.device = init_device(algo_args["device"])

        if not self.algo_args["render"]["use_render"]:
            self.run_dir, self.log_dir, self.save_dir, self.writter = init_dir(
                args["env"],
                env_args,
                args["algo"],
                args["exp_name"],
                algo_args["seed"]["seed"],
                logger_path=algo_args["logger"]["log_dir"],
            )
            save_config(args, algo_args, env_args, self.run_dir)

        setproctitle.setproctitle(
            str(args["algo"]) + "-" + str(args["env"]) + "-" + str(args["exp_name"])
        )

        if self.algo_args["render"]["use_render"]:
            (
                self.env,
                self.manual_render,
                self.manual_expand_dims,
                self.manual_delay,
                self.env_num,
            ) = make_render_env(args["env"], algo_args["seed"]["seed"], env_args)
        else:
            self.env = make_assignment_train_env(
                args["env"],
                algo_args["seed"]["seed"],
                algo_args["train"]["n_rollout_threads"],
                env_args,
            )
            self.eval_envs = (
                make_eval_env(
                    args["env"],
                    algo_args["seed"]["seed"],
                    algo_args["eval"]["n_eval_rollout_threads"],
                    env_args,
                )
                if algo_args["eval"]["use_eval"]
                else None
            )

        self.num_agents = get_assignment_num_agents(args["env"], env_args, self.env)

        print("share_observation_space: ", self.env.share_observation_space)
        print("observation_space: ", self.env.observation_space)
        print("action_space: ", self.env.action_space)

        self.is_heter_action_space = False
        self.max_action_space = 0

        if hasattr(self.env.unwrapped.cfg, "teams"):
            raise Exception(
                "It looks like you are trying to run an adversarial environment with "
                "a cooperative algorithm which is not allowed, please retry with an adversial "
                "algorithm (i.e happo_adv instead of happo)"
            )

        first_act_space = self.env.action_space[0]
        for _, val in self.env.action_space.items():
            scalar_action_dim = get_harl_scalar_action_dim(val)
            if scalar_action_dim > self.max_action_space:
                self.max_action_space = scalar_action_dim
            if val != first_act_space and not self.is_heter_action_space:
                self.is_heter_action_space = True

        if self.assignment_rl:
            self._print_assignment_env_summary()

        if self.share_param:
            self.actor = []
            agent = ALGO_REGISTRY[args["algo"]](
                {**algo_args["model"], **algo_args["algo"]},
                self.env.observation_space[0],
                self.env.action_space[0],
                device=self.device,
            )
            self.actor.append(agent)
            for agent_id in range(1, self.num_agents):
                assert (
                    self.env.observation_space[agent_id] == self.env.observation_space[0]
                ), "Agents have heterogeneous observation spaces, parameter sharing is not valid."
                assert (
                    self.env.action_space[agent_id] == self.env.action_space[0]
                ), "Agents have heterogeneous action spaces, parameter sharing is not valid."
                self.actor.append(self.actor[0])
        else:
            self.actor = []
            for agent_id in range(self.num_agents):
                agent = ALGO_REGISTRY[args["algo"]](
                    {**algo_args["model"], **algo_args["algo"]},
                    self.env.observation_space[agent_id],
                    self.env.action_space[agent_id],
                    device=self.device,
                )
                self.actor.append(agent)

        if self.assignment_rl:
            self._print_assignment_actor_summary()

        algo_args["model"]["hidden_sizes"] = self.hidden_sizes_critic
        if self.algo_args["render"]["use_render"] is False:
            self.actor_buffer = []
            for agent_id in range(self.num_agents):
                ac_bu = OnPolicyActorBuffer(
                    {**algo_args["train"], **algo_args["model"]},
                    self.env.observation_space[agent_id],
                    self.env.action_space[agent_id],
                    device=self.device,
                )
                self.actor_buffer.append(ac_bu)

            share_observation_space = self.env.share_observation_space[0]

            self.critic = VCritic(
                {**algo_args["model"], **algo_args["algo"]},
                share_observation_space,
                device=self.device,
            )

            if self.state_type == "EP":
                self.critic_buffer = OnPolicyCriticBufferEP(
                    {**algo_args["train"], **algo_args["model"], **algo_args["algo"]},
                    share_observation_space,
                    device=self.device,
                )
            elif self.state_type == "FP":
                self.critic_buffer = OnPolicyCriticBufferFP(
                    {**algo_args["train"], **algo_args["model"], **algo_args["algo"]},
                    share_observation_space,
                    self.num_agents,
                )
            else:
                raise NotImplementedError

            if self.algo_args["train"]["use_valuenorm"] is True:
                self.value_normalizer = ValueNorm(1, device=self.device)
            else:
                self.value_normalizer = None

            if self.assignment_rl and args["env"] == "isaaclab":
                env_args["reward_accumulator_mode"] = "exact_whitelist"
                env_args["reward_accumulator_keys"] = sorted(ASSIGNMENT_REWARD_ACCUMULATOR_KEYS)
                self.logger = AssignmentIsaacLabLogger(
                    args,
                    algo_args,
                    env_args,
                    self.num_agents,
                    self.writter,
                    self.run_dir,
                    reward_accumulator_keys=ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
                )
            else:
                self.logger = LOGGER_REGISTRY[args["env"]](
                    args, algo_args, env_args, self.num_agents, self.writter, self.run_dir
                )
        self.algo_args["model"]["hidden_sizes"] = self.hidden_sizes
        if self.algo_args["train"]["model_dir"] is not None:
            self.restore()

    def warmup(self):
        super().warmup()
        if not self.assignment_rl:
            return
        available_actions = getattr(self.env, "last_available_actions", None)
        if available_actions is None:
            raise RuntimeError("assignment_rl warmup expected last_available_actions, got None")
        expected_shape = (self.env.n_envs, self.num_agents, self.env.num_viewpoints + 1)
        if tuple(available_actions.shape) != expected_shape:
            raise RuntimeError(
                f"assignment_rl warmup available_actions shape mismatch: "
                f"expected {expected_shape}, got {tuple(available_actions.shape)}"
            )
        for agent_id, actor_buffer in enumerate(self.actor_buffer):
            if actor_buffer.available_actions is None:
                raise RuntimeError(f"assignment_rl actor_buffer[{agent_id}] has no available_actions buffer")
        print(
            "[INFO]: Assignment RL warmup stored available_actions "
            f"env_shape={tuple(available_actions.shape)} "
            f"per_agent_buffer_shape={tuple(self.actor_buffer[0].available_actions.shape)}"
        )

    def collect(self, step):
        if self.assignment_rl and not self._assignment_collect_mask_printed:
            for agent_id, actor_buffer in enumerate(self.actor_buffer):
                if actor_buffer.available_actions is None:
                    raise RuntimeError(f"assignment_rl collect has no mask buffer for agent {agent_id}")
            print("[INFO]: Assignment RL collect passes available_actions[:, agent_id, :] to each actor policy")
            self._assignment_collect_mask_printed = True
        return super().collect(step)

    def save(
        self,
        directory,
        *,
        checkpoint_kind: str | None = None,
        episode_or_update_index: int | None = None,
    ):
        """Route supported assignment state-dict saves through project-owned metadata coordination."""

        if not self.assignment_rl:
            return super().save(directory)
        profile = str(
            self.env.assignment_env.assignment_lifecycle_profile_config["profile_name"]
        )
        if profile in {"lifecycle_ablation", "diagnostics_hidden_state"}:
            raise AssignmentCheckpointSaveError(
                f"profile {profile!r} is not a native assignment training checkpoint profile"
            )
        if profile == "lifecycle_contract_c" and self.save_entire_model:
            raise AssignmentCheckpointSaveError(
                "lifecycle_contract_c checkpoint v1 requires save_entire_model=False "
                "and state_dict serialization"
            )
        if profile == "legacy" and (
            self.save_entire_model
            or str(self.args["algo"]).lower() != "happo"
            or bool(self.share_param)
        ):
            # Preserve legacy full-model and non-native legacy configurations without
            # claiming assignment_checkpoint_contract_v2 compatibility.
            return super().save(directory)
        if profile not in {"legacy", "lifecycle_contract_c"}:
            raise AssignmentCheckpointSaveError(
                f"unknown assignment lifecycle profile {profile!r}"
            )

        inferred_index = episode_or_update_index
        if checkpoint_kind is None:
            checkpoint_kind, inferred_index = infer_assignment_checkpoint_kind(
                self.run_dir,
                directory,
            )
        runtime_state = capture_assignment_checkpoint_runtime_state(self)
        manifest = build_assignment_checkpoint_contract_manifest(runtime_state)
        if self._assignment_checkpoint_coordinator is None:
            self._assignment_checkpoint_coordinator = AssignmentCheckpointSaveCoordinator(
                self.run_dir
            )

        actor_state_dicts = tuple(
            (name, self.actor[index].actor.state_dict())
            for index, name in enumerate(runtime_state.ordered_agent_names)
        )
        critic_state_dict = self.critic.critic.state_dict()
        value_normalizer_state_dict = (
            None
            if self.value_normalizer is None
            else export_value_normalizer_checkpoint_state(self.value_normalizer)
        )
        result = self._assignment_checkpoint_coordinator.save_checkpoint(
            checkpoint_directory=directory,
            checkpoint_kind=checkpoint_kind,
            checkpoint_generation=self._assignment_checkpoint_generation,
            manifest=manifest,
            actor_state_dicts=actor_state_dicts,
            critic_state_dict=critic_state_dict,
            value_normalizer_state_dict=value_normalizer_state_dict,
            episode_or_update_index=inferred_index,
        )
        self._assignment_checkpoint_generation += 1
        return result

    def restore(self):
        """Use the shared strict loader for assignment weight continuation."""

        if not self.assignment_rl:
            return super().restore()
        model_dir = self.algo_args["train"]["model_dir"]
        if model_dir is None:
            return None
        acknowledged = self.env_args.get(
            "acknowledge_weight_continuation_reset",
            False,
        )
        if acknowledged is not True:
            raise RuntimeError(
                "Assignment weight continuation requires explicit "
                "--acknowledge-weight-continuation-reset before any checkpoint load."
            )
        runtime_state = capture_assignment_checkpoint_runtime_state(self)
        current_manifest = build_assignment_checkpoint_contract_manifest(runtime_state)
        actor_modules = tuple(
            (name, self.actor[index].actor)
            for index, name in enumerate(runtime_state.ordered_agent_names)
        )
        self.assignment_checkpoint_load_result = load_assignment_checkpoint(
            checkpoint_directory=model_dir,
            purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            current_manifest=current_manifest,
            actor_modules=actor_modules,
            critic_module=self.critic.critic,
            value_normalizer_module=self.value_normalizer,
            continuation_reset_acknowledged=True,
        )
        return self.assignment_checkpoint_load_result

    def _print_assignment_env_summary(self) -> None:
        print("[INFO]: Assignment RL mode enabled: using repo-local AssignmentIsaacLabEnv/AssignmentHarlWrapper")
        print(f"[INFO]: Assignment RL num_viewpoints={self.env.num_viewpoints}")
        print(f"[INFO]: Assignment RL no-op action id={self.env.noop_action_id}")
        print(f"[INFO]: Assignment RL scalar action storage dim={self.max_action_space}")
        print(f"[INFO]: Assignment RL cooldown config={self.env.assignment_env.assignment_cooldown_config}")
        for agent_id, action_space in self.env.action_space.items():
            print(f"[INFO]: Assignment RL agent {agent_id} action_space={action_space}")

    def _print_assignment_actor_summary(self) -> None:
        for agent_id, actor in enumerate(self.actor):
            policy = getattr(actor, "actor", None)
            act_layer = getattr(policy, "act", None)
            action_type = getattr(act_layer, "action_type", None)
            action_head = getattr(act_layer, "action_out", None)
            action_head_name = action_head.__class__.__name__ if action_head is not None else None
            print(
                f"[INFO]: Assignment RL actor agent {agent_id} "
                f"action_type={action_type} distribution_head={action_head_name}"
            )
            if action_type != "Discrete" or action_head_name != "Categorical":
                raise RuntimeError(
                    "assignment_rl expected HARL Categorical actor for Discrete action space, "
                    f"got action_type={action_type}, distribution_head={action_head_name}"
                )


def register_assignment_harl_runner(runner_registry: dict[str, Any], algorithm: str) -> None:
    """Register the repo-local assignment runner for a tiny training smoke."""
    algorithm = algorithm.lower()
    if algorithm not in SUPPORTED_ASSIGNMENT_ALGORITHMS:
        raise ValueError(
            "--assignment_rl currently supports HA algorithms only "
            f"{SUPPORTED_ASSIGNMENT_ALGORITHMS}, got {algorithm!r}"
        )
    runner_registry[algorithm] = AssignmentOnPolicyHARunner


__all__ = [
    "ASSIGNMENT_REWARD_ACCUMULATOR_KEYS",
    "AssignmentIsaacLabEnv",
    "AssignmentIsaacLabLogger",
    "AssignmentOnPolicyHARunner",
    "SUPPORTED_ASSIGNMENT_ALGORITHMS",
    "apply_assignment_episode_length_override",
    "_compute_reward_accumulator_total",
    "_should_accumulate_reward_key",
    "register_assignment_harl_runner",
    "validate_assignment_lifecycle_policy_sequence",
]
