"""One bounded real-Isaac private learner transaction for Phase B2-R5I."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
SCAN = (
    ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
QUALIFIED_R3_SHA256 = "08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3"
QUALIFIED_REPO_SHA256 = {
    "assignment_event_training_evidence.py": "1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9",
    "assignment_event_training_gradient_probe.py": "5501947f64ebe33c003b0e08b2fbacd6ccd826c3e5e78d115401ed11061dd985",
    "assignment_event_training_actor_mutation.py": QUALIFIED_R3_SHA256,
    "assignment_event_training_critic_mutation.py": "9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde",
    "assignment_event_training_full_transaction.py": "ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35",
    "assignment_value_normalizer_checkpoint.py": "baa339431fa2b2c1933c468091f47b818f3fea7e2ce1394ffdd18c94265d11c1",
}
QUALIFIED_R5I_BASELINE_SHA256 = (
    "336dfdad1c6246b5e7b1b9ff6258cd9c7b87c19982007b442abca680f7cd339d"
)
ATTEMPT4_R5I_OBSERVABILITY_SHA256 = "bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e"
QUALIFIED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}
DEVICE = "cuda:0"
PASS = (
    "PHASE-B2-R5I-REAL-ISAAC-SINGLE-TRANSACTION-ATTEMPT4-"
    "COMPLETE-AWAITING-GPT-REVIEW"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke as V2  # noqa: E402


def _normal_path(path: Path | str) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    V2.atomic_json(path, payload)


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"STOP — B2-R5I-RE2 REPOSITORY_AUTHORITY: git {' '.join(args)}: "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout


def _repository_authority() -> dict[str, object]:
    branch = _git_output("branch", "--show-current").strip()
    head = _git_output("rev-parse", "HEAD").strip()
    origin_main = _git_output("rev-parse", "origin/main").strip()
    merge_base = _git_output("merge-base", "HEAD", "origin/main").strip()
    status = _git_output("status", "--porcelain=v1", "--untracked-files=all")
    staged_text = _git_output("diff", "--cached", "--name-only")
    staged_paths = tuple(line for line in staged_text.splitlines() if line)
    monthly = tuple(
        path
        for path in staged_paths
        if "/AgentRead/" in f"/{path}" and "/2026" in f"/{path}"
    )
    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "merge_base": merge_base,
        "head_origin_merge_base_equal": head == origin_main == merge_base,
        "working_tree_porcelain_line_count": len(status.splitlines()),
        "working_tree_status": tuple(status.splitlines()),
        "working_tree_porcelain_sha256": hashlib.sha256(
            status.encode("utf-8")
        ).hexdigest(),
        "staged_path_count": len(staged_paths),
        "staged_paths": staged_paths,
        "staged_index_sha256": hashlib.sha256(
            _git_output("ls-files", "--stage").encode("utf-8")
        ).hexdigest(),
        "staged_paths_sha256": hashlib.sha256(
            staged_text.encode("utf-8")
        ).hexdigest(),
        "preexisting_monthly_archive_migration_entry_count": len(monthly),
        "preexisting_monthly_archive_migration_paths_sha256": hashlib.sha256(
            "\n".join(monthly).encode("utf-8")
        ).hexdigest(),
    }


def _source_authority(E: object) -> tuple[tuple[object, ...], tuple[object, ...]]:
    repo_names = (
        "assignment_event_actor_collection.py",
        "assignment_event_critic_buffer.py",
        "assignment_event_gae_returns.py",
        "assignment_event_happo_policy_math.py",
        "assignment_event_learned_route.py",
        "assignment_event_terminal_learner_transport.py",
        "assignment_event_training_actor_mutation.py",
        "assignment_event_training_critic_mutation.py",
        "assignment_event_training_evidence.py",
        "assignment_event_training_gradient_probe.py",
        "assignment_event_training_full_transaction.py",
        "assignment_event_training_plans.py",
        "assignment_event_training_real_isaac_adapter.py",
        "assignment_value_normalizer_checkpoint.py",
    )
    harl_names = (
        Path("algorithms/actors/happo.py"),
        Path("algorithms/critics/v_critic.py"),
        Path("common/buffers/on_policy_critic_buffer_ep.py"),
        Path("common/valuenorm.py"),
    )
    repo = tuple(
        E.B2RSourceDigestV1(name, _sha(SCAN / name)) for name in sorted(repo_names)
    )
    installed = tuple(
        E.B2RSourceDigestV1(path.as_posix(), _sha(HARL / path))
        for path in sorted(harl_names, key=lambda item: item.as_posix())
    )
    return repo, installed


def _run_real_transaction(
    checkpoints: object,
    resources: dict[str, object],
    *,
    pre_mutation_path: Path,
    post_failure_path: Path,
    factor_progress_path: Path,
    critic_progress_path: Path,
    final_receipt_path: Path,
) -> dict[str, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import EventOnPolicyCriticBufferEPV2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import (
        _compose_dormant_event_learned_policy_route_v2,
        get_dormant_event_learned_policy_route_descriptor_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import seal_current_event_policy_decision_bundle_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import (
        capture_current_event_policy_evidence_snapshot_v2,
        capture_event_policy_physical_problem_evidence_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_assignment_event_profile_schema_v2_descriptor
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_evidence import canonical_digest_v1, fingerprint_tensor_v1
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_real_isaac_adapter import execute_real_isaac_single_transaction_v1
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TerminationReason
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
        AssignmentProfileName,
        AssignmentProfileResolutionOrigin,
        resolve_assignment_profile,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import assignment_to_env_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg
    from isaaclab_tasks.direct.scan_mobile_manipulator import assignment_event_training_evidence as E

    algo_args = V2.load_production_algo_args()
    seed_args = dict(algo_args["seed"])
    set_seed(seed_args)
    cfg = ScanMobileManipulatorEnvCfg()
    profile = resolve_assignment_profile(
        AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
        AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )
    resolved_E = 2
    resolved_T = 2
    cfg.scene.num_envs = resolved_E
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    timing = V2.build_pd2_integral_horizon_fixture_v1(
        float(cfg.sim.dt),
        int(cfg.decimation),
        semantic_horizon_steps=V2.PD2_SEMANTIC_HORIZON_STEPS,
    )
    V2.adjudicate_pd2_s1_preconstruction_timing_v1(timing)
    cfg.episode_length_s = timing.candidate_episode_length_seconds
    device = torch.device(cfg.sim.device)
    if device != torch.device(DEVICE):
        raise RuntimeError(f"STOP — B2-R5I CONFIG_DEVICE: {device}")
    resolved_M = len(cfg.possible_agents)
    resolved_N = len(cfg.viewpoint_poses)
    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(
            profile,
            device=device,
            env_ids=torch.arange(resolved_E, dtype=torch.int64, device=device),
            num_robots=resolved_M,
            num_tasks=resolved_N,
        )
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    resources["environment_constructions"] = 1
    guard = V2.WrapperGuard(env)
    resources["guard"] = guard
    raw = env.unwrapped
    post_timing = V2.build_pd2_s1_postconstruction_timing_evidence_v1(
        fixture=timing,
        configured_episode_length_seconds=float(cfg.episode_length_s),
        configured_sim_dt_seconds=float(cfg.sim.dt),
        configured_control_decimation=int(cfg.decimation),
        raw_max_episode_length=int(raw.max_episode_length),
        raw_max_episode_length_seconds=float(raw.max_episode_length_s),
        raw_step_dt_seconds=float(raw.step_dt),
        scale_contract=raw._event_terminal_critic_scale_contract_v2,
        expected_ordered_agent_names=tuple(cfg.possible_agents),
        expected_ordered_task_ids=tuple(range(resolved_N)),
        expected_scene_env_spacing=float(cfg.scene.env_spacing),
    )
    V2.adjudicate_pd2_s1_postconstruction_timing_v1(post_timing, timing)
    checkpoints.emit(
        "S1",
        "real_environment_constructed",
        {
            "environment": type(raw).__name__,
            "profile": profile.profile_name.value,
            "T": resolved_T,
            "E": resolved_E,
            "M": resolved_M,
            "N": resolved_N,
            "device": str(device),
        },
    )

    facade_events: list[tuple[str, object | None]] = []
    route_events: list[tuple[str, object | None]] = []
    terminal_slots_before_ack: list[tuple[object, ...]] = []
    control_assignments: list[torch.Tensor] = []

    def facade_observer(stage: str, detail: object | None) -> None:
        facade_events.append((stage, detail))
        if stage == "S14_WINDOW_OPEN":
            slots = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
            if slots:
                terminal_slots_before_ack.append(slots)

    wrapper = _compose_event_assignment_harl_wrapper(
        env=guard,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=facade_observer,
        assignment_profile_entrypoint="B2-R5I.real_isaac_single_transaction",
    )

    def current_bundle():
        current = domain.current_read_port.read_current()
        open_view = domain.interstep_fence_read_port.read()
        scale = raw._event_terminal_critic_scale_contract_v2
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
        if environment is not raw:
            raise RuntimeError("STOP — B2-R5I P2_CONTROLLER_IDENTITY")
        controls = assignment_to_env_actions(environment, assignment)
        if not all(value.device == device and bool(torch.isfinite(value).all()) for value in controls.values()):
            raise RuntimeError("STOP — B2-R5I CONTROLLER_TENSOR")
        control_assignments.append(assignment.detach().clone())
        return controls

    def forbidden_actor_trainer(**_kwargs):
        raise RuntimeError("STOP — B2-R5I PARALLEL_ACTOR_TRAINER")

    def forbidden_critic_trainer(_buffer, _normalizer):
        raise RuntimeError("STOP — B2-R5I PARALLEL_CRITIC_TRAINER")

    scale = raw._event_terminal_critic_scale_contract_v2
    schema = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)
    actor_dim = int(schema["actor_schema"]["dimension"])
    critic_dim = int(schema["critic_schema"]["dimension"])
    model_args = dict(algo_args["model"])
    algorithm_args = dict(algo_args["algo"])
    actor_args = {**model_args, **algorithm_args}
    critic_args = {**model_args, **algorithm_args}
    actors_raw = [
        HAPPO(actor_args, V2.Box((actor_dim,)), gym.spaces.Discrete(resolved_N + 1), device=device)
        for _ in range(resolved_M)
    ]
    critic_raw = VCritic(critic_args, V2.Box((critic_dim,)), device=device)
    live_value_normalizer = ValueNorm(1, device=device)
    actors = [V2.ActorRecorder(actor, index) for index, actor in enumerate(actors_raw)]
    critic = V2.CriticRecorder(critic_raw)
    buffer_args = {
        **algo_args["train"],
        **model_args,
        **algorithm_args,
        "episode_length": resolved_T,
        "n_rollout_threads": resolved_E,
    }
    buffer = EventOnPolicyCriticBufferEPV2(
        buffer_args, V2.Box((critic_dim,)), device=device
    )
    for actor in actors_raw:
        actor.prep_rollout()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    critic_raw.prep_rollout()
    critic_raw.critic_optimizer.zero_grad(set_to_none=True)

    def route_observer(stage: str, detail: object | None) -> None:
        route_events.append((stage, detail))

    route = _compose_dormant_event_learned_policy_route_v2(
        episode_length=resolved_T,
        actors=tuple(actors),
        critic=critic,
        critic_buffer=buffer,
        admitted_reset=wrapper.reset,
        current_decision_supplier=current_bundle,
        current_decision_validator=validate_current,
        capture_i42_decision=wrapper._capture_event_proposal_decision,
        step_i42_proposals=wrapper._step_event_proposals,
        action_builder=action_builder,
        actor_trainer=forbidden_actor_trainer,
        critic_trainer=forbidden_critic_trainer,
        value_normalizer=live_value_normalizer,
        actor_rnn_shape=(1, 256),
        call_observer=route_observer,
    )
    resources["route"] = route
    reset_result = route.reset()
    resources["real_resets"] = 1
    if type(reset_result) is not tuple or len(reset_result) != 3:
        raise RuntimeError("STOP — B2-R5I REAL_RESET_CONTRACT")
    initial = route.current_decision_bundle
    initial_shapes = {
        "actor_obs": tuple(initial.evidence_snapshot.actor_obs.shape),
        "critic_obs": tuple(initial.evidence_snapshot.runner_share_obs.shape),
        "available_actions": tuple(initial.runner_available_actions.shape),
        "dvm_rows": int(initial.decision_valid_mask.sum().item()),
    }
    dummy = torch.full(
        (resolved_E, resolved_M, 1),
        resolved_N,
        dtype=torch.float32,
        device=device,
    )
    step_before = int(raw.common_step_counter)
    try:
        wrapper.step(dummy)
    except RuntimeError as exc:
        if "not runtime-ready" not in str(exc):
            raise
    else:
        raise RuntimeError("STOP — B2-R5I PUBLIC_ROUTE_OPEN")
    if int(raw.common_step_counter) != step_before:
        raise RuntimeError("STOP — B2-R5I PUBLIC_FENCE_MUTATION")

    first = route.collect_step()
    resources["real_rollout_steps"] = 1
    if bool(first.harl_step_result[3].any()):
        raise RuntimeError("STOP — B2-R5I FIRST_STEP_TERMINAL")
    first_effective = V2.expected_assignment(first.facade_result.admitted_publication, torch)
    if len(control_assignments) != 1 or not torch.equal(control_assignments[0], first_effective):
        raise RuntimeError("STOP — B2-R5I FINAL_P2_CONTROLLER")
    first_actor_calls = tuple(len(actor.calls) for actor in actors)
    if first_actor_calls != tuple(1 for _ in range(resolved_M)):
        raise RuntimeError("STOP — B2-R5I REAL_ACTOR_COLLECTION")
    for actor_id, actor in enumerate(actors):
        call = actor.calls[0]
        if not torch.equal(call["actions"], first.proposal_envelope.action_ids[:, actor_id]):
            raise RuntimeError("STOP — B2-R ACTOR_EVIDENCE_BINDING")
        if not torch.equal(call["logprobs"], first.proposal_envelope.action_logprobs[:, actor_id]):
            raise RuntimeError("STOP — B2-R ACTOR_EVIDENCE_BINDING")

    critic_start = len(critic.calls)
    route_event_start = len(route_events)
    second = route.collect_step()
    resources["real_rollout_steps"] = 2
    if not bool(second.harl_step_result[3].all()):
        raise RuntimeError("STOP — B2-R5I TERMINAL_NOT_REACHED")
    second_effective = V2.expected_assignment(second.facade_result.admitted_publication, torch)
    if len(control_assignments) != 2 or not torch.equal(control_assignments[1], second_effective):
        raise RuntimeError("STOP — B2-R5I CONTINUATION_CONTROLLER")
    second_events = route_events[route_event_start:]
    timeout_events = [detail for stage, detail in second_events if stage == "I5a_critic_buffer_insert"]
    timeout_call_count = (
        int(timeout_events[0].critic_batch_calls)
        if len(timeout_events) == 1 and hasattr(timeout_events[0], "critic_batch_calls")
        else 0
    )
    timeout_identity = V2.identify_pd2_s6_timeout_critic_call_v1(
        second_collect_start_call_index=critic_start,
        second_collect_end_call_index=len(critic.calls),
        timeout_batch_event_count=len(timeout_events),
        observed_timeout_call_count=timeout_call_count,
    )
    history = second.facade_result.terminal_historical_payload
    resources["terminal_autoreset_events"] = len(history)
    if len(history) != resolved_E or not all(row.optional_sidecar is not None for row in history):
        raise RuntimeError("STOP — B2-R5I HISTORICAL_TERMINAL")
    if len(terminal_slots_before_ack) != 1 or len(terminal_slots_before_ack[0]) != resolved_E:
        raise RuntimeError("STOP — B2-R5I TERMINAL_COPY_BEFORE_ACK")
    if domain.terminal_consumer_port.capture_pending_terminal_artifacts() != ():
        raise RuntimeError("STOP — B2-R5I RUNTIME_ACK")
    pre_reset_obs = torch.stack(
        [row.optional_sidecar.bootstrap_critic_obs for row in history], dim=0
    )
    post_reset_obs = second.next_decision_bundle.evidence_snapshot.runner_share_obs[:, 0]
    observed_timeout = critic.observed_input(timeout_identity.timeout_call_global_index)
    correlation = V2.compare_pd2_s6_timeout_critic_input_exact_v1(
        pre_reset_obs,
        observed_timeout,
        invocation_identity=timeout_identity,
    )
    V2.adjudicate_pd2_s6_timeout_critic_input_correlation_v1(correlation)
    if torch.equal(pre_reset_obs, post_reset_obs):
        raise RuntimeError("STOP — B2-R5I HISTORICAL_CURRENT_ALIAS")
    reason_grid = buffer.termination_reason.detach().clone()
    if not bool((reason_grid[0] == int(TerminationReason.NONE)).all()):
        raise RuntimeError("STOP — B2-R5I TERMINATION_REASON")
    if not bool((reason_grid[1] == int(TerminationReason.TIME_LIMIT)).all()):
        raise RuntimeError("STOP — B2-R5I TERMINATION_REASON")
    if [len(actor.calls) for actor in actors] != [1] * resolved_M:
        raise RuntimeError("STOP — B2-R5I FORCED_CONTINUATION_RESAMPLED")
    if bool(second.proposal_envelope.policy_proposal_present_mask.any()):
        raise RuntimeError("STOP — B2-R5I FORCED_CONTINUATION_PROPOSAL")

    effective_digest = canonical_digest_v1(
        (
            fingerprint_tensor_v1(first_effective).content_digest,
            fingerprint_tensor_v1(second_effective).content_digest,
            "effective assignment from final environment-owned P2",
        )
    )
    precedence_digest = canonical_digest_v1(
        (
            fingerprint_tensor_v1(reason_grid).content_digest,
            (
                "ALL_TASKS_COMPLETED",
                "NO_FEASIBLE_TASKS_REMAIN",
                "TIME_LIMIT",
                "NONE",
            ),
            "environment-owned selected reason",
        )
    )
    history_keys = tuple(
        (row.env_id, row.episode_generation, row.transition_generation)
        for row in history
    )
    correlation_digest = canonical_digest_v1(
        (
            history_keys,
            fingerprint_tensor_v1(pre_reset_obs).content_digest,
            fingerprint_tensor_v1(post_reset_obs).content_digest,
            bool(correlation.exact_value_match),
            correlation.expected_input_sha256,
            correlation.observed_input_sha256,
        )
    )
    timeout_digest = canonical_digest_v1(
        (
            fingerprint_tensor_v1(pre_reset_obs).content_digest,
            fingerprint_tensor_v1(observed_timeout).content_digest,
            timeout_identity.timeout_call_global_index,
            timeout_identity.observed_timeout_call_count,
        )
    )
    repo_hashes, harl_hashes = _source_authority(E)
    update_id = f"b2-r5i-re3-fresh-{os.getpid()}"
    identity = {
        "attempt_number": 4,
        "run_identity": update_id,
        "update_id": update_id,
        "process_id": os.getpid(),
        "fresh_process": True,
        "historical_route_reused": False,
    }
    resources["attempt_identity"] = identity
    factor_events: list[object] = []
    critic_events: list[object] = []
    progress_counts = {
        "cumulative_actor_backward_count": 0,
        "cumulative_actor_optimizer_step_count": 0,
        "cumulative_critic_backward_count": 0,
        "cumulative_critic_optimizer_step_count": 0,
        "cumulative_live_valuenorm_update_count": 0,
    }

    def persist_progress(
        path: Path, events: list[object], payload: Mapping[str, object]
    ) -> None:
        for key in progress_counts:
            if key in payload:
                progress_counts[key] = int(payload[key])
        event = V2.normalize({**identity, **progress_counts, **payload})
        events.append(event)
        _atomic_json(
            path,
            {**identity, **progress_counts, "stage": payload["stage"],
             "events": events, "event_count": len(events)},
        )

    def persist_factor(payload: Mapping[str, object]) -> None:
        persist_progress(factor_progress_path, factor_events, payload)

    def persist_critic(payload: Mapping[str, object]) -> None:
        persist_progress(critic_progress_path, critic_events, payload)

    def persist_pre_mutation(payload: Mapping[str, object]) -> None:
        _atomic_json(
            pre_mutation_path,
            {
                **payload,
                **identity,
                **progress_counts,
                "stage": "S5_ENTRY_BEFORE_FIRST_MUTATION",
                "repository_authority": resources["repository_authority"],
                "terminal_pre_reset_critic_digest": fingerprint_tensor_v1(pre_reset_obs).content_digest,
                "terminal_post_reset_current_critic_digest": fingerprint_tensor_v1(post_reset_obs).content_digest,
                "terminal_history_keys": history_keys,
                "post_reset_episode_generations": second.next_decision_bundle.evidence_identity.episode_generations,
                "timeout_critic_exact_identity": bool(correlation.exact_value_match),
                "runtime_ack_complete": True,
                "learner_ledger_retained_after_ack": bool(route.collector.consumed_terminal_keys),
                "event_return_result_equals_training_slice": True,
                "event_return_result_training_slice_non_alias": True,
                "stock_compute_returns_calls": 0,
            },
        )

    def persist_post_failure(payload: Mapping[str, object]) -> None:
        failure = {
            **identity, **progress_counts, **payload,
            "stage": "FAILED",
            "factor_progress_event_count": len(factor_events),
            "critic_progress_event_count": len(critic_events),
        }
        _atomic_json(post_failure_path, failure)
        _atomic_json(final_receipt_path, failure)

    transaction = execute_real_isaac_single_transaction_v1(
        repository_head=EXPECTED_HEAD,
        dirty_state_classification=(
            "reviewed uncommitted B2-R0-R5 plus authorized private B2-R5I"
        ),
        repo_source_hashes=repo_hashes,
        installed_harl_source_hashes=harl_hashes,
        route=route,
        actors=tuple(actors_raw),
        critic=critic_raw,
        live_value_normalizer=live_value_normalizer,
        algo_args=algo_args,
        environment_identity="Isaac-Scan-Mobile-Manipulator-Direct-v0",
        profile_name=profile.profile_name.value,
        real_environment_resets=1,
        real_rollout_steps=resolved_T,
        precedence_resolution_evidence_digest=precedence_digest,
        terminal_correlation_evidence_digest=correlation_digest,
        timeout_critic_evidence_digest=timeout_digest,
        effective_assignment_evidence_digest=effective_digest,
        proposal_effective_authority_separate=True,
        update_id=update_id,
        order_seed=int(algo_args["seed"]["seed"]),
        classification=PASS,
        pre_mutation_observer=persist_pre_mutation,
        factor_segment_observer=persist_factor,
        critic_progress_observer=persist_critic,
        post_failure_observer=persist_post_failure,
    )
    resources["completed_transaction"] = transaction
    if not pre_mutation_path.is_file():
        raise RuntimeError("STOP — B2-R5I-RE PRE_MUTATION_ARTIFACT_MISSING")
    descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
    if descriptor["route"] != "private_test_only_dormant" or descriptor["public_activation"] != "blocked_pending_B2_V1_V2_R":
        raise RuntimeError("STOP — B2-R5I PUBLIC_ROUTE_OPEN")
    segments = [item for item in factor_events if item["stage"] == "S5_ACTOR_SEGMENT_COMPLETE"]
    minibatches = [item for item in critic_events if item["stage"] == "S6_CRITIC_MINIBATCH_COMPLETE"]
    vn_updates = [item for item in critic_events if item["stage"] == "S6_VALUENORM_POST_UPDATE_OBSERVED"]
    if (
        len(segments) != resolved_M
        or not factor_events[-1].get("complete_actor_sequence")
        or not critic_events[-1].get("complete_critic_sequence")
        or len(minibatches) != transaction.real_audit.critic_expected_step
        or len(vn_updates) != transaction.real_audit.valuenorm_expected_update
        or any(not item["canonical_mutation"] or not item["canonical_state_finite"] for item in vn_updates)
    ):
            raise RuntimeError("STOP — B2-R5I-RE3 DURABLE_RECEIPTS_INCOMPLETE")
    _atomic_json(
        final_receipt_path,
        {
            **identity, **progress_counts,
            "stage": "S10_QUIESCENT_NEXT_ROLLOUT_CHECK_PASSED",
            "classification": PASS,
            "partial_update": False,
            "route_poisoned": False,
            "s10_entries": 1,
            "next_rollout_ready": transaction.next_rollout_ready,
            "transaction_evidence_digest": transaction.evidence_digest,
            "transaction": transaction,
            "factor_segment_receipt_count": len(segments),
            "critic_minibatch_receipt_count": len(minibatches),
            "canonical_valuenorm_mutation_receipt_count": len(vn_updates),
            "checkpoint_weight_io": 0,
            "training_campaigns": 0,
            "evaluation_playback": 0,
            "public_route_activations": 0,
        },
    )
    checkpoints.emit(
        "S10",
        "real_private_transaction_quiescent",
        {
            "classification": transaction.classification,
            "evidence_digest": transaction.evidence_digest,
            "counts": transaction.exact_execution_counts,
        },
    )
    return {
        **identity,
        "classification": transaction.classification,
        "transaction": transaction,
        "durable_artifacts": {
            name: {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha(path)}
            for name, path in (
                ("pre_mutation", pre_mutation_path),
                ("factor_progress", factor_progress_path),
                ("critic_progress", critic_progress_path),
                ("final_receipt", final_receipt_path),
            )
        },
        "pre_mutation_durable_evidence": {
            "path": str(pre_mutation_path),
            "bytes": pre_mutation_path.stat().st_size,
            "sha256": _sha(pre_mutation_path),
        },
        "real_collection": {
            "environment": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
            "environment_type": type(raw).__name__,
            "profile": profile.profile_name.value,
            "resolved_T": resolved_T,
            "resolved_E": resolved_E,
            "resolved_M": resolved_M,
            "resolved_N": resolved_N,
            "reset_count": 1,
            "rollout_steps": 2,
            "initial_shapes": initial_shapes,
            "first_actor_calls": first_actor_calls,
            "second_actor_calls_total": tuple(len(actor.calls) for actor in actors),
            "dvm_rows": int(first.proposal_envelope.decision_valid_mask.sum().item()),
            "forced_rows": int(second.proposal_envelope.forced_row_mask.sum().item()),
            "terminal_history_keys": history_keys,
            "terminal_slots_before_ack": len(terminal_slots_before_ack[0]),
            "terminal_slots_after_ack": 0,
            "pre_reset_critic_digest": fingerprint_tensor_v1(pre_reset_obs).content_digest,
            "post_reset_current_digest": fingerprint_tensor_v1(post_reset_obs).content_digest,
            "timeout_exact_match": bool(correlation.exact_value_match),
        },
        "proposal_logprob_dvm_identity": {
            "original_proposal_digest": transaction.real_audit.original_proposal_action_digest,
            "original_behavior_logprob_digest": transaction.real_audit.original_behavior_logprob_digest,
            "dvm_digest": transaction.real_audit.dvm_digest,
            "availability_digest": transaction.real_audit.historical_available_action_mask_digest,
            "effective_assignment_digest": effective_digest,
            "proposal_effective_authority_separate": True,
            "behavior_logprob_recomputed": False,
        },
        "terminal": {
            "classification": transaction.real_audit.terminal_coverage_classification,
            "selected_reason_digest": transaction.real_audit.selected_reason_grid_digest,
            "precedence_digest": precedence_digest,
            "correlation_digest": correlation_digest,
            "timeout_digest": timeout_digest,
        },
        "public_route": "DORMANT / BLOCKED",
        "checkpoint_weight_io": 0,
        "training_campaigns": 0,
        "evaluation_playback": 0,
        "route_stage_names": tuple(stage for stage, _ in route_events),
        "facade_stage_names": tuple(stage for stage, _ in facade_events),
    }


def run_worker(args: argparse.Namespace) -> int:
    result_path = Path(args.result_file)
    checkpoints = V2.Checkpoints(Path(args.checkpoint_file))
    simulation_app = None
    resources: dict[str, object] = {}
    result: dict[str, object] = {
        "status": "failed",
        "classification": "STOP — B2-R5I STARTUP",
    }
    try:
        pre_mutation_path = Path(args.pre_mutation_file).resolve()
        post_failure_path = Path(args.post_failure_file).resolve()
        factor_progress_path = Path(args.factor_progress_file).resolve()
        critic_progress_path = Path(args.critic_progress_file).resolve()
        final_receipt_path = Path(args.final_receipt_file).resolve()
        artifact_paths = (
            pre_mutation_path, post_failure_path, factor_progress_path,
            critic_progress_path, final_receipt_path, result_path.resolve(),
        )
        if len(set(artifact_paths)) != len(artifact_paths) or any(path.exists() for path in artifact_paths):
            raise RuntimeError("STOP — B2-R5I-RE DIAGNOSTIC_ARTIFACT_ALREADY_EXISTS")
        worker_sources = _qualified_source_identity()
        if not worker_sources["pass"]:
            raise RuntimeError("STOP — B2-R5I-RE3 QUALIFIED-SOURCE-DRIFT")
        resources["repository_authority"] = _repository_authority()
        if resources["repository_authority"]["head"] != EXPECTED_HEAD:
            raise RuntimeError("STOP — B2-R5I-RE3 QUALIFIED-SOURCE-DRIFT")
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        device = V2._warm_start_torch_cuda(DEVICE, checkpoints)
        if device is None or str(device) != DEVICE:
            raise RuntimeError("STOP — B2-R5I CUDA_WARMUP")
        launcher = AppLauncher(
            headless=True,
            device=DEVICE,
            enable_cameras=False,
            livestream=0,
            xr=False,
            experience="",
        )
        simulation_app = launcher.app
        evidence = _run_real_transaction(
            checkpoints,
            resources,
            pre_mutation_path=pre_mutation_path,
            post_failure_path=post_failure_path,
            factor_progress_path=factor_progress_path,
            critic_progress_path=critic_progress_path,
            final_receipt_path=final_receipt_path,
        )
        result = {
            "status": "passed",
            "classification": PASS,
            "authoritative_attempts": 1,
            "worker_count": 1,
            "app_launcher_lifetimes": 1,
            "evidence": evidence,
        }
    except BaseException as exc:
        result = {
            "status": "failed",
            "classification": getattr(exc, "stop_code", "STOP — B2-R5I RUNTIME"),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "durable_observer_error": getattr(exc, "durable_observer_error", None),
            "authoritative_attempts": 1,
            "worker_count": 1,
            "app_launcher_lifetimes": int(simulation_app is not None),
        }
        if args.pre_mutation_file and Path(args.pre_mutation_file).is_file():
            path = Path(args.pre_mutation_file)
            result["pre_mutation_durable_evidence"] = {
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
        if args.post_failure_file and Path(args.post_failure_file).is_file():
            path = Path(args.post_failure_file)
            result["post_failure_durable_evidence"] = {
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
            failure = json.loads(path.read_text(encoding="utf-8"))
            result["failure_receipt"] = failure
            history = failure.get("state_history", ())
            boundary = str(history[-1] if history else "RUNTIME").replace("_", "-")
            result["classification"] = f"PHASE-B2-R5I-RE3-STOP-{boundary}-NOT-COMPLETE"
        if resources.get("completed_transaction") is not None:
            resources["route"]._poisoned = True
            completed = resources["completed_transaction"]
            result["completed_transaction_before_harness_failure"] = completed
            failure = {
                **resources["attempt_identity"], "stage": "POST_S10_HARNESS_FAILURE",
                "error": result["error"], "partial_update": True,
                "route_poisoned": True, "s10_entries": 1,
                "exact_execution_counts": completed.exact_execution_counts,
                "further_use_forbidden": True,
            }
            _atomic_json(Path(args.final_receipt_file), failure)
    result["process_id"] = os.getpid()
    result["attempt_number"] = 4
    result["real_runtime_counts"] = {
        key: int(resources.get(key, 0)) for key in (
            "environment_constructions", "real_resets", "real_rollout_steps",
            "terminal_autoreset_events",
        )
    }
    _atomic_json(result_path, result)
    guard = resources.get("guard")
    if guard is not None:
        try:
            guard.close()
            result["environment_close"] = "RETURNED"
        except BaseException as exc:
            result["environment_close"] = f"FAILED: {type(exc).__name__}: {exc}"
    if simulation_app is not None:
        simulation_app.close()
        result["simulation_app_close"] = "RETURNED"
    _atomic_json(result_path, result)
    return 0 if result["status"] == "passed" else 20


def _qualified_source_identity() -> dict[str, object]:
    repo = {name: _sha(SCAN / name) for name in QUALIFIED_REPO_SHA256}
    installed = {name: _sha(HARL / name) for name in QUALIFIED_HARL_SHA256}
    adapter_hash = _sha(SCAN / "assignment_event_training_real_isaac_adapter.py")
    return {
        "repo_hashes": repo,
        "installed_harl_hashes": installed,
        "qualified_repo_sources_exact": repo == QUALIFIED_REPO_SHA256,
        "qualified_installed_sources_exact": installed == QUALIFIED_HARL_SHA256,
        "qualified_r5i_baseline_sha256": QUALIFIED_R5I_BASELINE_SHA256,
        "attempt4_logging_only_r5i_sha256": adapter_hash,
        "audited_logging_only_adapter_exact": adapter_hash == ATTEMPT4_R5I_OBSERVABILITY_SHA256,
        "pass": repo == QUALIFIED_REPO_SHA256 and installed == QUALIFIED_HARL_SHA256
        and adapter_hash == ATTEMPT4_R5I_OBSERVABILITY_SHA256,
    }


def run_static() -> dict[str, object]:
    import _assignment_phase_b2_r1_contract_helpers as R1

    guards_module = R1.load_canonical(
        "assignment_event_training_real_isaac_adapter_guards.py"
    )

    interpreter = _normal_path(sys.executable) == _normal_path(EXPECTED_PYTHON)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()
    r3_sha256 = _sha(SCAN / "assignment_event_training_actor_mutation.py")
    guards = guards_module.validate_r5i_static_guards_v1(ROOT)
    # Import executes no fixture: invoke only its existing static guard function.
    import test_assignment_phase_b2_r5_controlled_private_full_learner_transaction as R5_TEST

    executors = R5_TEST.test_static_private_public_guards()
    sources = _qualified_source_identity()
    repository = _repository_authority()
    result = {
        "interpreter_exact": interpreter,
        "head": head,
        "head_exact": head == EXPECTED_HEAD,
        "qualified_r3_sha256": r3_sha256,
        "qualified_r3_source_exact": r3_sha256 == QUALIFIED_R3_SHA256,
        "static_private_guards": guards,
        "qualified_source_identity": sources,
        "repository_authority": repository,
        "executor_cardinality": executors,
    }
    result["pass"] = (
        interpreter
        and head == EXPECTED_HEAD
        and r3_sha256 == QUALIFIED_R3_SHA256
        and bool(guards["pass"])
        and bool(sources["pass"])
        and bool(repository["head_origin_merge_base_equal"])
        and repository["staged_path_count"] == 359
    )
    return result


def run_supervisor(args: argparse.Namespace) -> int:
    static = run_static()
    if not static["pass"]:
        result = {"status": "failed", "classification": "STOP — B2-R5I STATIC", "static": static}
        if args.json_output:
            _atomic_json(Path(args.json_output), result)
        print(json.dumps(V2.normalize(result), indent=2, sort_keys=True))
        return 2
    with tempfile.TemporaryDirectory(prefix="b2_r5i_real_single_") as directory:
        temp = Path(directory)
        primary = temp / "primary.json"
        checkpoints = temp / "checkpoints.json"
        command = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--worker",
            "--result-file",
            str(primary),
            "--checkpoint-file",
            str(checkpoints),
            "--pre-mutation-file",
            str(Path(args.pre_mutation_json).resolve()),
            "--post-failure-file",
            str(Path(args.post_failure_json).resolve()),
            "--factor-progress-file",
            str(Path(args.factor_progress_json).resolve()),
            "--critic-progress-file",
            str(Path(args.critic_progress_json).resolve()),
            "--final-receipt-file",
            str(Path(args.final_receipt_json).resolve()),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=args.timeout_seconds,
                check=False,
            )
            valid, worker = V2._read_json(primary)
            result = {
                "status": "passed" if valid and worker.get("status") == "passed" and completed.returncode == 0 else "failed",
                "classification": worker.get("classification", "STOP — B2-R5I WORKER_RESULT"),
                "static": static,
                "formal_supervisor_attempts": 1,
                "formal_workers": 1,
                "app_launcher_lifetimes": worker.get("app_launcher_lifetimes", 0),
                "retry_count": 0,
                "worker_exit_code": completed.returncode,
                "worker_result_valid": valid,
                "worker_checkpoints": V2._read_json(checkpoints)[1],
                "worker": worker,
                "worker_stdout_tail": completed.stdout[-12000:],
                "worker_stderr_tail": completed.stderr[-12000:],
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "status": "failed",
                "classification": "STOP — B2-R5I TIMEOUT",
                "static": static,
                "formal_supervisor_attempts": 1,
                "formal_workers": 1,
                "retry_count": 0,
                "timeout_seconds": args.timeout_seconds,
                "stdout_tail": (exc.stdout or "")[-12000:],
                "stderr_tail": (exc.stderr or "")[-12000:],
            }
    if args.json_output:
        _atomic_json(Path(args.json_output), result)
    print(json.dumps(V2.normalize(result), indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", help=argparse.SUPPRESS)
    parser.add_argument("--checkpoint-file", help=argparse.SUPPRESS)
    parser.add_argument("--pre-mutation-file", help=argparse.SUPPRESS)
    parser.add_argument("--post-failure-file", help=argparse.SUPPRESS)
    parser.add_argument("--factor-progress-file", help=argparse.SUPPRESS)
    parser.add_argument("--critic-progress-file", help=argparse.SUPPRESS)
    parser.add_argument("--final-receipt-file", help=argparse.SUPPRESS)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--json-output")
    parser.add_argument(
        "--pre-mutation-json",
        default=str(Path(tempfile.gettempdir()) / "b2_r5i_re3_attempt4_pre_mutation.json"),
    )
    parser.add_argument(
        "--post-failure-json",
        default=str(Path(tempfile.gettempdir()) / "b2_r5i_re3_attempt4_post_failure.json"),
    )
    parser.add_argument("--factor-progress-json", default=str(Path(tempfile.gettempdir()) / "b2_r5i_re3_attempt4_factor_progress.json"))
    parser.add_argument("--critic-progress-json", default=str(Path(tempfile.gettempdir()) / "b2_r5i_re3_attempt4_critic_progress.json"))
    parser.add_argument("--final-receipt-json", default=str(Path(tempfile.gettempdir()) / "b2_r5i_re3_attempt4_final_receipt.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.worker:
        return run_worker(args)
    if args.static_only:
        result = run_static()
        if args.json_output:
            _atomic_json(Path(args.json_output), result)
        print(json.dumps(V2.normalize(result), indent=2, sort_keys=True))
        return 0 if result["pass"] else 2
    return run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
