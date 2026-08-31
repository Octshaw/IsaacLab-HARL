"""Bounded B2-V2 real Isaac/CUDA and installed-HARL interface smoke.

Verification-only.  This executable composes the private dormant B2-I6 route
with a real DirectMARLEnv, fresh installed HAPPO/VCritic components, and the
repo-local event buffers.  It never runs backward, an optimizer, or a public
training runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from typing import Any


STARTED = time.monotonic()
RESULT_PREFIX = "__B2_V2_WORKER_RESULT__"
PASS = "PHASE-B2-V2-FOCUSED-REAL-ISAAC-HARL-INTERFACE-VERIFICATION-PASS-AWAITING-GPT-REVIEW"
STOP = "PHASE-B2-V2-STOP-REAL-ISAAC-HARL-INTERFACE-GAP"
E, M, N, T = 2, 3, 12, 2
EPISODE_HORIZON_CONTROL_STEPS = 3
SEED = 260826

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
PROTECTED = tuple(
    SCAN / name
    for name in (
        "assignment_event_profile_schema_contract_v2.py",
        "assignment_event_policy_evidence.py",
        "assignment_event_policy_decision.py",
        "assignment_event_actor_collection.py",
        "assignment_event_happo_policy_math.py",
        "assignment_event_terminal_critic_sidecar.py",
        "assignment_event_terminal_learner_transport.py",
        "assignment_event_critic_buffer.py",
        "assignment_event_gae_returns.py",
        "assignment_event_learned_route.py",
        "assignment_event_runtime_facade.py",
        "assignment_event_proposal_adapter.py",
        "assignment_lifecycle_transaction_runtime.py",
        "assignment_lifecycle_authority_runtime.py",
        "assignment_harl_wrapper.py",
        "assignment_harl_training.py",
        "scan_mobile_manipulator_env.py",
    )
) + (
    REPO_ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py",
) + tuple(
    HARL / name
    for name in (
        "algorithms/actors/happo.py",
        "algorithms/actors/on_policy_base.py",
        "algorithms/critics/v_critic.py",
        "common/valuenorm.py",
        "common/buffers/on_policy_actor_buffer.py",
        "common/buffers/on_policy_critic_buffer_ep.py",
        "runners/on_policy_base_runner.py",
        "runners/on_policy_ha_runner.py",
    )
)


class SmokeGap(RuntimeError):
    def __init__(self, message: str, *, stage: str) -> None:
        self.classification = STOP
        self.failure_code = stage
        super().__init__(f"{message}; stage={stage!r}")


def require(condition: bool, message: str, *, stage: str) -> None:
    if not condition:
        raise SmokeGap(message, stage=stage)


def jsonable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if hasattr(value, "detach") and hasattr(value, "cpu") and hasattr(value, "tolist"):
        return value.detach().cpu().tolist()  # type: ignore[union-attr]
    if hasattr(value, "value"):
        return jsonable(value.value)  # type: ignore[union-attr]
    return str(value)


def record(stage: str, message: str, **evidence: object) -> None:
    print(
        json.dumps(
            {
                "elapsed_seconds": round(time.monotonic() - STARTED, 3),
                "message": message,
                "stage": stage,
                **{key: jsonable(value) for key, value in evidence.items()},
            },
            sort_keys=True,
        ),
        flush=True,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str]:
    return {str(path): sha256(path) for path in PROTECTED}


def tensor_fingerprint(tensor: Any) -> str:
    data = tensor.detach().contiguous().cpu().numpy().tobytes()
    return hashlib.sha256(data).hexdigest()


def parameter_fingerprint(modules: list[Any]) -> str:
    digest = hashlib.sha256()
    for module in modules:
        for parameter in module.parameters():
            digest.update(parameter.detach().contiguous().cpu().numpy().tobytes())
            digest.update(str((id(parameter), parameter.data_ptr(), parameter._version)).encode())
    return digest.hexdigest()


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class WrapperGuard:
    def __init__(self, env: object) -> None:
        self._env = env
        self.unwrapped = env.unwrapped  # type: ignore[attr-defined]
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self._env, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("event wrapper used the public raw reset path")

    def step(self, *args: object, **kwargs: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("event wrapper used the public raw step path")

    def close(self) -> None:
        self._env.close()  # type: ignore[attr-defined]


class ActorRecorder:
    def __init__(self, actor: object, agent_id: int) -> None:
        self.actor = actor
        self.agent_id = agent_id
        self.calls: list[dict[str, object]] = []

    def get_actions(self, obs, rnn, masks, available_actions, deterministic=False):
        actions, logprobs, next_rnn = self.actor.get_actions(
            obs, rnn, masks, available_actions, deterministic
        )
        self.calls.append(
            {
                "obs": obs.detach().clone(),
                "available": available_actions.detach().clone(),
                "actions": actions.detach().clone(),
                "logprobs": logprobs.detach().clone(),
                "next_rnn": next_rnn.detach().clone(),
                "grad_enabled": bool(__import__("torch").is_grad_enabled()),
            }
        )
        return actions, logprobs, next_rnn


class CriticRecorder:
    def __init__(self, critic: object) -> None:
        self.wrapped = critic
        self.calls: list[dict[str, object]] = []

    def __getattr__(self, name: str) -> object:
        return getattr(self.wrapped, name)

    def get_values(self, obs, rnn, masks):
        values, next_rnn = self.wrapped.get_values(obs, rnn, masks)
        self.calls.append(
            {
                "obs": obs.detach().clone(),
                "rnn": rnn.detach().clone(),
                "masks": masks.detach().clone(),
                "values": values.detach().clone(),
                "grad_enabled": bool(__import__("torch").is_grad_enabled()),
            }
        )
        return values, next_rnn


def happo_args() -> dict[str, object]:
    return {
        "hidden_sizes": [32, 32],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "gain": 0.01,
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "data_chunk_length": 2,
        "lr": 0.0005,
        "opti_eps": 0.00001,
        "weight_decay": 0,
        "std_x_coef": 1,
        "std_y_coef": 0.5,
        "ppo_epoch": 1,
        "clip_param": 0.2,
        "actor_num_mini_batch": 1,
        "entropy_coef": 0.01,
        "use_max_grad_norm": True,
        "max_grad_norm": 10.0,
        "use_policy_active_masks": True,
        "action_aggregation": "prod",
    }


def critic_args() -> dict[str, object]:
    return {
        "hidden_sizes": [32, 32],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "clip_param": 0.2,
        "critic_epoch": 1,
        "critic_num_mini_batch": 1,
        "data_chunk_length": 2,
        "value_loss_coef": 1.0,
        "max_grad_norm": 10.0,
        "huber_delta": 10.0,
        "use_max_grad_norm": True,
        "use_clipped_value_loss": True,
        "use_huber_loss": True,
        "use_policy_active_masks": True,
        "critic_lr": 0.0005,
        "opti_eps": 0.00001,
        "weight_decay": 0,
    }


def expected_assignment(publication: object, torch: Any) -> object:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TaskLifecycleState

    state = publication.lifecycle_state
    assignment = torch.full(
        (state.robot_state.shape[0], state.robot_state.shape[1]),
        -1,
        dtype=torch.int64,
        device=state.robot_state.device,
    )
    active = {int(TaskLifecycleState.CLAIMED), int(TaskLifecycleState.NAVIGATING), int(TaskLifecycleState.ALIGNING)}
    for env_id in range(state.task_state.shape[0]):
        for task_id in range(state.task_state.shape[1]):
            if int(state.task_state[env_id, task_id]) in active:
                robot_id = int(state.ownership[env_id, task_id])
                require(robot_id >= 0, "active task lacks owner", stage="R3_P2_AK")
                assignment[env_id, robot_id] = task_id
    return assignment


def run_real_smoke() -> dict[str, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import EventOnPolicyCriticBufferEPV2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import _compose_dormant_event_learned_policy_route_v2, get_dormant_event_learned_policy_route_descriptor_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import seal_current_event_policy_decision_bundle_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import capture_current_event_policy_evidence_snapshot_v2, capture_event_policy_physical_problem_evidence_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import _EventProfileLifecycleDomainSpec, _EventProfileLifecycleRuntimeDomain
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TerminationReason
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import AssignmentProfileName, AssignmentProfileResolutionOrigin, resolve_assignment_profile
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import assignment_to_env_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    profile = resolve_assignment_profile(AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = E
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    cfg.episode_length_s = float(cfg.sim.dt) * int(cfg.decimation) * EPISODE_HORIZON_CONTROL_STEPS
    device = torch.device(cfg.sim.device)
    require((len(cfg.possible_agents), len(cfg.viewpoint_poses)) == (M, N), "canonical M/N changed", stage="R0_SCALE")
    require(device == torch.device("cuda:0") and torch.cuda.is_available(), "cuda:0 unavailable", stage="R0_DEVICE")

    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(E, dtype=torch.int64, device=device),
            num_robots=M,
            num_tasks=N,
        )
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw = env.unwrapped
    guard = WrapperGuard(env)
    facade_events: list[tuple[str, object | None]] = []
    slots_before_ack: list[tuple[object, ...]] = []

    def facade_observer(stage: str, detail: object | None) -> None:
        facade_events.append((stage, detail))
        if stage == "S14_WINDOW_OPEN":
            slots = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
            if slots:
                slots_before_ack.append(slots)

    wrapper = _compose_event_assignment_harl_wrapper(
        env=guard,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=facade_observer,
        assignment_profile_entrypoint="B2-V2.real_interface_smoke",
    )
    route_events: list[tuple[str, object | None]] = []
    control_assignments: list[torch.Tensor] = []
    actor_train_calls: list[dict[str, object]] = []
    critic_train_calls: list[dict[str, object]] = []
    optimizer_calls = {"actor": 0, "critic": 0}

    def current_bundle():
        current = domain.current_read_port.read_current()
        open_view = domain.interstep_fence_read_port.read()
        scale = raw._event_terminal_critic_scale_contract_v2
        require(scale is not None, "real environment lacks I4 scale contract", stage="R1_I1")
        physical = capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=raw.get_assignment_problem(),
            episode_progress_steps=raw.episode_length_buf,
            scale_contract=scale,
        )
        snapshot = capture_current_event_policy_evidence_snapshot_v2(
            current_publication=current,
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=scale,
        )
        return seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)

    def validate_current(bundle):
        bundle.evidence_snapshot.validate_current(
            current_publication=domain.current_read_port.read_current(),
            current_open_window_view=domain.interstep_fence_read_port.read(),
        )

    def action_builder(environment: object, assignment: torch.Tensor):
        require(environment is raw, "controller builder received foreign env", stage="R3_P2_AK")
        controls = assignment_to_env_actions(environment, assignment)
        require(all(value.device == device and bool(torch.isfinite(value).all()) for value in controls.values()), "controller tensors violate CUDA/finite contract", stage="R3_P2_AK")
        control_assignments.append(assignment.detach().clone())
        return controls

    def actor_trainer(**kwargs):
        actor_train_calls.append(kwargs)
        return {"kind": "recorder", "optimizer_calls": 0, "factor_shape": tuple(kwargs["initial_factor"].shape)}

    def critic_trainer(buffer, value_normalizer):
        critic_train_calls.append({"buffer": buffer, "value_normalizer": value_normalizer})
        return {"kind": "recorder", "optimizer_calls": 0}

    try:
        scale = raw._event_terminal_critic_scale_contract_v2
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_assignment_event_profile_schema_v2_descriptor

        schema = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)
        actor_dim = int(schema["actor_schema"]["dimension"])
        critic_dim = int(schema["critic_schema"]["dimension"])
        actors_raw = []
        actors = []
        for agent_id in range(M):
            torch.manual_seed(SEED + 10 + agent_id)
            actor = HAPPO(happo_args(), Box((actor_dim,)), gym.spaces.Discrete(N + 1), device=device)
            actor.prep_rollout()
            actor.actor_optimizer.step = lambda *args, **kwargs: optimizer_calls.__setitem__("actor", optimizer_calls["actor"] + 1)
            actors_raw.append(actor)
            actors.append(ActorRecorder(actor, agent_id))
        torch.manual_seed(SEED + 20)
        critic_raw = VCritic(critic_args(), Box((critic_dim,)), device=device)
        critic_raw.prep_rollout()
        critic_raw.critic_optimizer.step = lambda *args, **kwargs: optimizer_calls.__setitem__("critic", optimizer_calls["critic"] + 1)
        critic = CriticRecorder(critic_raw)
        value_normalizer = ValueNorm(1, device=device)
        buffer_args = {
            "episode_length": T,
            "n_rollout_threads": E,
            "hidden_sizes": [32, 32],
            "recurrent_n": 1,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "use_gae": True,
            "use_proper_time_limits": True,
        }
        buffer = EventOnPolicyCriticBufferEPV2(buffer_args, Box((critic_dim,)), device=device)
        parameter_before = parameter_fingerprint([actor.actor for actor in actors_raw] + [critic_raw.critic, value_normalizer])
        valuenorm_before = tuple(parameter.detach().clone() for parameter in value_normalizer.parameters())

        route = _compose_dormant_event_learned_policy_route_v2(
            episode_length=T,
            actors=tuple(actors),
            critic=critic,
            critic_buffer=buffer,
            admitted_reset=wrapper.reset,
            current_decision_supplier=current_bundle,
            current_decision_validator=validate_current,
            capture_i42_decision=wrapper._capture_event_proposal_decision,
            step_i42_proposals=wrapper._step_event_proposals,
            action_builder=action_builder,
            actor_trainer=actor_trainer,
            critic_trainer=critic_trainer,
            value_normalizer=value_normalizer,
            actor_rnn_shape=(1, 32),
            call_observer=lambda stage, detail: route_events.append((stage, detail)),
        )

        reset_result = route.reset()
        require(type(reset_result) is tuple and len(reset_result) == 3, "admitted reset arity changed", stage="R1_RESET")
        initial = route.current_decision_bundle
        initial_p2 = domain.current_read_port.read_current()
        require(initial.evidence_identity.p2_publication_identity is initial_p2.publication_identity, "I1 identity is not current P2", stage="R1_I1")
        require(tuple(initial.evidence_snapshot.actor_obs.shape) == (E, M, actor_dim), "actor obs shape", stage="R1_I1")
        require(tuple(initial.evidence_snapshot.runner_share_obs.shape) == (E, M, critic_dim), "critic obs shape", stage="R1_I1")
        require(tuple(initial.runner_available_actions.shape) == (E, M, N + 1), "I2 mask shape", stage="R1_I2")
        for tensor in (initial.evidence_snapshot.actor_obs, initial.evidence_snapshot.runner_share_obs, initial.runner_available_actions):
            require(tensor.device == device, "I1/I2 device mismatch", stage="R1_DEVICE")
        require(bool(initial.decision_valid_mask.any()), "canonical reset has no DVM policy row", stage="R2_DVM")
        record("R1", "real reset and exact current I1/I2 passed", actor_shape=initial.evidence_snapshot.actor_obs.shape, critic_shape=initial.evidence_snapshot.runner_share_obs.shape, dvm_rows=int(initial.decision_valid_mask.sum()))

        dummy = torch.full((E, M, 1), N, dtype=torch.float32, device=device)
        step_counter = int(raw.common_step_counter)
        try:
            wrapper.step(dummy)
        except RuntimeError as exc:
            require("not runtime-ready" in str(exc), "public fence returned wrong error", stage="R9_PUBLIC_FENCE")
        else:
            raise SmokeGap("public event wrapper.step opened", stage="R9_PUBLIC_FENCE")
        require(int(raw.common_step_counter) == step_counter, "blocked public step mutated env", stage="R9_PUBLIC_FENCE")

        receipts = [route.collect_step(), route.collect_step()]
        require(all(len(item.harl_step_result) == 6 for item in receipts), "HARL six tuple lost", stage="R3_SIX_TUPLE")
        require(not bool(receipts[0].harl_step_result[3].any()), "first physical step was terminal", stage="R3_NONTERMINAL")
        terminal_dones = receipts[1].harl_step_result[3]
        require(bool(terminal_dones.all()), "second step did not terminate all synchronized rows", stage="R5_TIME_LIMIT")
        reasons = buffer.termination_reason.detach().clone()
        require(bool((reasons[0] == int(TerminationReason.NONE)).all()), "ordinary row reason changed", stage="R5_REASON")
        require(bool((reasons[1] == int(TerminationReason.TIME_LIMIT)).all()), "real terminal was not TIME_LIMIT", stage="R5_REASON")
        require(len(receipts[1].facade_result.terminal_historical_payload) == E, "terminal history cardinality", stage="R5_HISTORY")
        history = receipts[1].facade_result.terminal_historical_payload
        require(all(row.optional_sidecar is not None for row in history), "pre-reset sidecar missing", stage="R5_SIDECAR")
        require(len(slots_before_ack) == 1 and len(slots_before_ack[0]) == E, "pre-ACK slots not observed once", stage="R5_ACK")
        require(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "runtime slots survived ACK", stage="R5_ACK")

        pre_obs = torch.stack([row.optional_sidecar.bootstrap_critic_obs for row in history], dim=0)
        post_obs = receipts[1].next_decision_bundle.evidence_snapshot.runner_share_obs[:, 0]
        pre_fp = tensor_fingerprint(pre_obs)
        post_fp = tensor_fingerprint(post_obs)
        require(pre_fp != post_fp, "pre-reset and post-reset critic fingerprints are indistinguishable", stage="R5_PRE_POST")
        old_episodes = tuple(row.episode_generation for row in history)
        new_episodes = receipts[1].next_decision_bundle.evidence_identity.episode_generations
        require(all(new == old + 1 for old, new in zip(old_episodes, new_episodes)), "autoreset episode generation did not advance", stage="R5_GENERATION")
        require(all(row.transition_generation == receipts[1].next_decision_bundle.evidence_identity.transition_generations[index] for index, row in enumerate(history)), "historical/current transition generations differ", stage="R5_GENERATION")

        actor_calls = [call for actor in actors for call in actor.calls]
        require(actor_calls, "real HAPPO was never called on a DVM row", stage="R2_ACTOR")
        sampled_rows = 0
        for call in actor_calls:
            actions = call["actions"]
            available = call["available"]
            selected = available.to(torch.bool).gather(1, actions.to(torch.int64))
            require(bool(selected.all()), "real HAPPO sampled an illegal masked action", stage="R2_ACTOR_MASK")
            require(actions.device == device and call["logprobs"].device == device, "actor output device mismatch", stage="R2_ACTOR_DEVICE")
            require(bool(torch.isfinite(call["logprobs"]).all()), "actor logprob nonfinite", stage="R2_ACTOR_LOGPROB")
            require(not call["grad_enabled"], "actor collection enabled gradients", stage="R2_ACTOR_GRAD")
            sampled_rows += int(actions.shape[0])
        for receipt in receipts:
            for call_record in receipt.proposal_envelope.actor_call_records:
                if not call_record.actor_called:
                    require(call_record.actor_batch_size == 0, "forced/empty actor row was sampled", stage="R2_FORCED_BYPASS")

        require(len(control_assignments) == T, "physical controller call count", stage="R3_P2_AK")
        for receipt, assignment in zip(receipts, control_assignments):
            expected = expected_assignment(receipt.facade_result.admitted_publication, torch)
            require(torch.equal(assignment, expected), "controller assignment differs from final current P2/Ak", stage="R3_P2_AK")

        timeout_call_matches = [torch.equal(call["obs"], pre_obs) for call in critic.calls]
        require(sum(timeout_call_matches) == 1, "timeout critic input was not evaluated exactly once", stage="R6_TIMEOUT_CRITIC")
        require(all(not call["grad_enabled"] and bool(torch.isfinite(call["values"]).all()) and call["values"].device == device for call in critic.calls), "real critic forward contract", stage="R2_CRITIC")
        require(torch.equal(buffer.share_obs[2], post_obs), "critic t+1 slot is not post-reset current share_obs", stage="R6_BUFFER_ALIGNMENT")
        require(bool(buffer.timeout_bootstrap_masks[1].all()) and bool(torch.isfinite(buffer.timeout_bootstrap_value_preds[1]).all()), "timeout buffer fields missing", stage="R6_BUFFER_TIMEOUT")

        rollout = route.finish_rollout(agent_order=(0, 1, 2))
        require(tuple(rollout.advantages.shape) == (T, E, 1), "event advantage shape", stage="R7_RETURNS")
        require(bool(torch.isfinite(rollout.advantages).all()), "event advantages nonfinite", stage="R7_RETURNS")
        require(tuple(rollout.event_returns_result.returns.shape) == (T + 1, E, 1), "event return shape", stage="R7_RETURNS")
        require(bool(torch.isfinite(rollout.event_returns_result.returns).all()), "event returns nonfinite", stage="R7_RETURNS")
        require(len(actor_train_calls) == 1 and len(critic_train_calls) == 1, "recorder trainer seam call count", stage="R8_TRAINER_SEAM")
        require(optimizer_calls == {"actor": 0, "critic": 0}, "optimizer was called", stage="R8_OPTIMIZER")
        require(all(len(actor.actor_optimizer.state) == 0 for actor in actors_raw) and len(critic_raw.critic_optimizer.state) == 0, "optimizer state was created", stage="R8_OPTIMIZER")
        require(all(parameter.grad is None for actor in actors_raw for parameter in actor.actor.parameters()) and all(parameter.grad is None for parameter in critic_raw.critic.parameters()), "gradient tensor was created", stage="R8_BACKWARD")
        require(parameter_fingerprint([actor.actor for actor in actors_raw] + [critic_raw.critic, value_normalizer]) == parameter_before, "actor/critic/ValueNorm parameters changed", stage="R8_PARAMETERS")
        require(all(torch.equal(old, new) for old, new in zip(valuenorm_before, value_normalizer.parameters())), "ValueNorm statistics changed", stage="R8_VALUENORM")
        require(buffer.step == 0 and not bool(buffer._event_slot_written.any()), "event buffer did not roll over", stage="R8_ROLLOVER")

        descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
        require(descriptor["route"] == "private_test_only_dormant" and descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R", "public readiness fence opened", stage="R9_PUBLIC_FENCE")
        step_counter = int(raw.common_step_counter)
        try:
            wrapper.step(dummy)
        except RuntimeError as exc:
            require("not runtime-ready" in str(exc), "post-smoke public fence error", stage="R9_PUBLIC_FENCE")
        else:
            raise SmokeGap("post-smoke public event wrapper.step opened", stage="R9_PUBLIC_FENCE")
        require(int(raw.common_step_counter) == step_counter, "post-smoke blocked public step mutated env", stage="R9_PUBLIC_FENCE")

        history_keys = [(row.env_id, row.episode_generation, row.transition_generation) for row in history]
        record("R9", "real I0-I6 interface smoke passed", actor_calls=len(actor_calls), sampled_rows=sampled_rows, critic_calls=len(critic.calls), history_keys=history_keys)
        return {
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "torch_version": torch.__version__,
            "environment_id": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
            "environment_type": type(raw).__name__,
            "profile": profile.profile_name.value,
            "E": E,
            "M": M,
            "N": N,
            "T": T,
            "device": str(device),
            "seed": SEED,
            "actor_initialization_seeds": [SEED + 10 + item for item in range(M)],
            "critic_initialization_seed": SEED + 20,
            "episode_horizon_control_steps": EPISODE_HORIZON_CONTROL_STEPS,
            "episode_length_s": float(cfg.episode_length_s),
            "actor_dim": actor_dim,
            "critic_dim": critic_dim,
            "reset_arity": 3,
            "step_arity": [len(item.harl_step_result) for item in receipts],
            "initial_dvm_rows": int(initial.decision_valid_mask.sum()),
            "actor_forward_calls": [len(actor.calls) for actor in actors],
            "actor_sampled_rows": sampled_rows,
            "critic_forward_calls": len(critic.calls),
            "timeout_critic_exact_matches": sum(timeout_call_matches),
            "termination_reason": reasons.detach().cpu().tolist(),
            "history_keys": history_keys,
            "pre_reset_fingerprint": pre_fp,
            "post_reset_fingerprint": post_fp,
            "old_episode_generations": old_episodes,
            "new_episode_generations": new_episodes,
            "terminal_slots_before_ack": len(slots_before_ack[0]),
            "terminal_slots_after_ack": 0,
            "critic_buffer_alignment": "share_obs[t+1]=post-reset current; timeout[t]=pre-reset sidecar value",
            "event_returns_shape": tuple(rollout.event_returns_result.returns.shape),
            "stock_compute_returns_calls": 0,
            "actor_trainer_recorder_calls": len(actor_train_calls),
            "critic_trainer_recorder_calls": len(critic_train_calls),
            "optimizer_calls": optimizer_calls,
            "backward_calls": 0,
            "valuenorm_updates": 0,
            "parameter_fingerprint_unchanged": True,
            "controller_calls": len(control_assignments),
            "public_event_step": "blocked_before_and_after",
            "public_runner": "not_constructed",
            "runtime_readiness": "blocked",
            "guard_direct_calls": {"reset": guard.direct_reset_calls, "step": guard.direct_step_calls},
            "facade_stage_count": len(facade_events),
            "route_stage_count": len(route_events),
        }
    finally:
        guard.close()


def write_result(path: str | None, result: dict[str, object]) -> None:
    if path:
        Path(path).write_text(json.dumps(jsonable(result), sort_keys=True), encoding="utf-8")


def run_worker(args: argparse.Namespace) -> int:
    simulation_app = None
    result: dict[str, object] = {"classification": STOP, "status": "failed", "error": "worker did not start"}
    code = 1
    try:
        record("R0", "before AppLauncher", python=sys.executable)
        from isaaclab.app import AppLauncher

        simulation_app = AppLauncher(headless=True).app
        record("R0", "AppLauncher initialized")
        evidence = run_real_smoke()
        result = {"classification": PASS, "status": "passed", "evidence": evidence}
        code = 0
    except BaseException as exc:
        trace = traceback.format_exc()
        print(trace, file=sys.stderr, flush=True)
        result = {
            "classification": getattr(exc, "classification", STOP),
            "status": "failed",
            "failure_code": getattr(exc, "failure_code", None),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": trace,
        }
    finally:
        write_result(args.result_file, result)
        print(RESULT_PREFIX + json.dumps(jsonable(result), sort_keys=True), flush=True)
        record("R10", "before SimulationApp shutdown")
        if simulation_app is not None:
            try:
                simulation_app.close()
            except BaseException as exc:
                result = {"classification": STOP, "status": "failed", "error": f"shutdown {type(exc).__name__}: {exc}"}
                write_result(args.result_file, result)
                code = 1
    return code


def read_lines(pipe: Any, lines: queue.Queue[str | None]) -> None:
    try:
        for line in pipe:
            lines.put(line)
    finally:
        lines.put(None)


def terminate_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    elif process.poll() is None:
        process.kill()


def run_supervisor(args: argparse.Namespace) -> int:
    before = protected_hashes()
    with tempfile.TemporaryDirectory(prefix="b2_v2_smoke_") as temp:
        result_path = os.path.join(temp, "result.json")
        command = [sys.executable, "-u", os.path.abspath(__file__), "--worker", "--result-file", result_path]
        record("SUPERVISOR", "launching one bounded worker", timeout_seconds=args.timeout_seconds)
        process = subprocess.Popen(command, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert process.stdout is not None
        lines: queue.Queue[str | None] = queue.Queue()
        reader = threading.Thread(target=read_lines, args=(process.stdout, lines), daemon=True)
        reader.start()
        deadline = time.monotonic() + args.timeout_seconds
        worker_result: dict[str, object] | None = None
        reader_done = False
        timed_out = False
        while not reader_done or process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0 and process.poll() is None:
                timed_out = True
                terminate_tree(process)
                break
            try:
                line = lines.get(timeout=min(0.25, max(0.01, remaining)))
            except queue.Empty:
                continue
            if line is None:
                reader_done = True
            elif line.startswith(RESULT_PREFIX):
                worker_result = json.loads(line[len(RESULT_PREFIX):])
            else:
                print(line, end="", flush=True)
        try:
            child_code = process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_tree(process)
            child_code = process.wait(timeout=15)
        reader.join(timeout=5)
        if os.path.isfile(result_path):
            worker_result = json.loads(Path(result_path).read_text(encoding="utf-8"))
        after = protected_hashes()
        hashes_unchanged = before == after
        if timed_out:
            result = {"classification": STOP, "status": "failed", "error": "bounded worker timeout"}
        elif worker_result is None:
            result = {"classification": STOP, "status": "failed", "error": "worker produced no result"}
        else:
            result = dict(worker_result)
        result.update(
            {
                "child_exit_code": child_code,
                "shutdown_observed": child_code == 0,
                "worker_process_alive_after_wait": process.poll() is None,
                "protected_hash_count": len(before),
                "protected_hashes_unchanged": hashes_unchanged,
                "protected_hashes_before": before,
                "protected_hashes_after": after,
                "timeout": timed_out,
            }
        )
        if child_code != 0 or not hashes_unchanged:
            result["status"] = "failed"
            result["classification"] = STOP
        print(json.dumps(jsonable(result), sort_keys=True) if args.json else json.dumps(jsonable(result), indent=2, sort_keys=True), flush=True)
        return 0 if result.get("status") == "passed" and child_code == 0 and hashes_unchanged else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.worker and not args.result_file:
        parser.error("worker requires --result-file")
    return args


def main() -> int:
    args = parse_args()
    return run_worker(args) if args.worker else run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
