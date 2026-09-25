"""Three-update, one-process real-Isaac continuity retry for Phase B2-T0-RE1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
from typing import Mapping, Sequence


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
DEVICE = "cuda:0"
TRANSACTION_COUNT = 3
PASS = (
    "PHASE-B2-T0-RE1-BOUNDED-REPEATED-UPDATE-CONTINUITY-"
    "COMPLETE-AWAITING-GPT-REVIEW"
)
QUALIFIED_LD_HELPER_SHA256 = (
    "af607d6d24c908f7c78e1af3ed3843bd2c87921309a6eb36514e37be95aa6052"
)

QUALIFIED_REPO_SHA256 = {
    "assignment_event_training_evidence.py": "1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9",
    "assignment_event_training_plans.py": "4223b391de5e9302f6c7e895e4ee4da10b6dd8c8860a418036bad5f1441787ad",
    "assignment_event_training_control.py": "c3291a2abe94fba3170ecf5e79e6e8aeaa302dbb9c58cda488038323e9c6eb1a",
    "assignment_event_training_static_guards.py": "05fed8102340d0738a3af9bab178c1234e6ce8f349929147da1fefe0cd1975db",
    "assignment_event_training_gradient_probe.py": "5501947f64ebe33c003b0e08b2fbacd6ccd826c3e5e78d115401ed11061dd985",
    "assignment_event_training_actor_mutation.py": "08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3",
    "assignment_event_training_critic_mutation.py": "9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde",
    "assignment_event_training_full_transaction.py": "ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35",
    "assignment_event_training_real_isaac_adapter.py": "bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e",
    "assignment_value_normalizer_checkpoint.py": "baa339431fa2b2c1933c468091f47b818f3fea7e2ce1394ffdd18c94265d11c1",
}
QUALIFIED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_t0_ld_decision_gate as LD  # noqa: E402
import test_assignment_phase_b2_r5i_real_isaac_single_transaction as SINGLE  # noqa: E402

V2 = SINGLE.V2


def _normal_path(path: Path | str) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    V2.atomic_json(path, payload)


def _json_digest(payload: object) -> str:
    encoded = json.dumps(
        V2.normalize(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require(condition: bool, code: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T0 {code}: {detail!r}")


def _capture_lifecycle_decision_gate_v1(
    *,
    receipt: object,
    actors: Sequence[object],
    actor_calls_before: tuple[int, ...],
    actor_calls_after: tuple[int, ...],
    transaction_index: int,
    collection_index: int,
    physical_step_index: int,
    previous_episode_generations: tuple[int, ...] | None,
) -> tuple[dict[str, object], tuple[int, ...]]:
    """Bind one B2-T0 boundary to immutable I1/I2/I3a evidence."""

    import torch

    envelope = receipt.proposal_envelope
    bundle = envelope.decision_bundle
    next_bundle = receipt.next_decision_bundle
    evidence = bundle.evidence_snapshot
    E = bundle.evidence_identity.num_envs
    M = bundle.evidence_identity.M
    N = bundle.evidence_identity.N
    records = envelope.actor_call_records
    _require(
        len(records) == M
        and len(actors) == M
        and len(actor_calls_before) == M
        and len(actor_calls_after) == M,
        "DECISION_GATE_ACTOR_DOMAIN",
    )
    valid_envs_by_robot: list[tuple[int, ...]] = []
    for robot_index, record in enumerate(records):
        valid_envs = tuple(record.valid_env_indices)
        batch_call_delta = actor_calls_after[robot_index] - actor_calls_before[robot_index]
        _require(
            record.agent_id == robot_index
            and len(set(valid_envs)) == len(valid_envs)
            and all(0 <= env_index < E for env_index in valid_envs)
            and record.actor_batch_size == len(valid_envs)
            and record.actor_called is bool(valid_envs)
            and batch_call_delta == int(bool(valid_envs)),
            "DECISION_GATE_ACTOR_CALL_RECORD",
            {
                "robot": robot_index,
                "valid_envs": valid_envs,
                "batch_call_delta": batch_call_delta,
            },
        )
        if valid_envs:
            call = actors[robot_index].calls[actor_calls_before[robot_index]]
            indices = torch.tensor(valid_envs, dtype=torch.int64, device=envelope.action_ids.device)
            _require(
                torch.equal(call["actions"], envelope.action_ids[indices, robot_index])
                and torch.equal(
                    call["logprobs"], envelope.action_logprobs[indices, robot_index]
                ),
                "DECISION_GATE_ACTOR_EVIDENCE_BINDING",
                robot_index,
            )
        valid_envs_by_robot.append(valid_envs)

    row_kind_names = {
        0: LD.POLICY_DECISION_ROW,
        1: LD.FORCED_CONTINUATION_ROW,
        2: LD.FORCED_NOOP_ROW,
    }
    lifecycle_names = {
        0: "EXECUTING",
        1: "NEEDS_ASSIGNMENT",
        2: "WAITING_FOR_TASK",
        3: "UNAVAILABLE",
    }
    episodes = tuple(bundle.evidence_identity.episode_generations)
    transitions = tuple(bundle.evidence_identity.transition_generations)
    current_owned = evidence.current_owned_task_id
    next_owned = next_bundle.evidence_snapshot.current_owned_task_id
    dvm = bundle.decision_valid_mask
    proposal_mask = envelope.policy_proposal_present_mask
    original_proposals = envelope.original_policy_proposal_ids
    rows: list[LD.LifecycleDecisionRowEvidence] = []
    for env_index in range(E):
        terminal_context = (
            "CURRENT_NONTERMINAL"
            if previous_episode_generations is None
            else (
                "POST_AUTORESET_CURRENT_GENERATION"
                if episodes[env_index] != previous_episode_generations[env_index]
                else "SAME_EPISODE_CURRENT_NONTERMINAL"
            )
        )
        for robot_index in range(M):
            row_kind = row_kind_names[int(bundle.row_kind[env_index, robot_index].item())]
            called = int(env_index in valid_envs_by_robot[robot_index])
            owned_before_raw = int(current_owned[env_index, robot_index].item())
            owned_after_raw = int(next_owned[env_index, robot_index].item())
            actual_proposal = bool(
                original_proposals[env_index, robot_index, 0].item() >= 0
            )
            _require(
                bool(proposal_mask[env_index, robot_index, 0].item())
                is actual_proposal,
                "DECISION_GATE_PROPOSAL_LEDGER",
                (env_index, robot_index),
            )
            rows.append(
                LD.LifecycleDecisionRowEvidence(
                    collection_index=collection_index,
                    physical_step_index=physical_step_index,
                    env_index=env_index,
                    robot_index=robot_index,
                    episode_generation=episodes[env_index],
                    transition_generation=transitions[env_index],
                    lifecycle_state=lifecycle_names[
                        int(evidence.robot_state[env_index, robot_index].item())
                    ],
                    current_owned_task_id=(
                        None if owned_before_raw >= N else owned_before_raw
                    ),
                    decision_required=bool(dvm[env_index, robot_index, 0].item()),
                    decision_reason=row_kind,
                    actor_policy_call_count=called,
                    proposal_produced=actual_proposal,
                    behavior_logprob_produced=actual_proposal,
                    continuation_used=row_kind == LD.FORCED_CONTINUATION_ROW,
                    terminal_autoreset_context=terminal_context,
                    ownership_before=(None if owned_before_raw >= N else owned_before_raw),
                    ownership_after=(None if owned_after_raw >= N else owned_after_raw),
                )
            )
    gate_receipt = LD.qualify_lifecycle_decision_boundary(tuple(rows))
    result = gate_receipt.to_mapping()
    result["transaction_index"] = transaction_index
    result["rows"] = tuple(
        {
            **row,
            "transaction_index": transaction_index,
            "i2_row_kind": row["decision_reason"],
            "dvm": row["decision_required"],
            "i3a_actor_subset_participation": row["actor_policy_call_count"],
            "proposal_present": row["proposal_produced"],
            "behavior_logprob_present": row["behavior_logprob_produced"],
            "available_actions_class": (
                "POLICY_LEGAL_SET"
                if row["decision_reason"] == LD.POLICY_DECISION_ROW
                else (
                    "FORCED_CONTINUATION_SINGLETON"
                    if row["decision_reason"] == LD.FORCED_CONTINUATION_ROW
                    else "FORCED_NOOP_SINGLETON"
                )
            ),
            "available_action_count": int(
                bundle.runner_available_actions[
                    row["env_index"], row["robot_index"]
                ].sum().item()
            ),
        }
        for row in result["rows"]
    )
    result["actor_batch_call_deltas_supplemental"] = tuple(
        after - before
        for before, after in zip(actor_calls_before, actor_calls_after, strict=True)
    )
    result["authority"] = (
        "current P2 -> immutable I1 -> I2 POLICY_DECISION_ROW/DVM -> I3a subset call"
    )
    result["physical_step_is_decision_authority"] = False
    return result, episodes


def _artifact_path(prefix: Path, suffix: str) -> Path:
    return prefix.parent / f"{prefix.name}_{suffix}.json"


def _source_identity() -> dict[str, object]:
    repo = {name: _sha(SCAN / name) for name in QUALIFIED_REPO_SHA256}
    installed = {name: _sha(HARL / name) for name in QUALIFIED_HARL_SHA256}
    test_side = {
        "scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py": _sha(
            Path(__file__).resolve().parent
            / "_assignment_phase_b2_t0_ld_decision_gate.py"
        ),
        "scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py": _sha(
            Path(__file__).resolve()
        ),
    }
    return {
        "repo_hashes": repo,
        "installed_harl_hashes": installed,
        "test_side_hashes": test_side,
        "qualified_repo_sources_exact": repo == QUALIFIED_REPO_SHA256,
        "qualified_installed_sources_exact": installed == QUALIFIED_HARL_SHA256,
        "qualified_ld_helper_exact": (
            test_side[
                "scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py"
            ]
            == QUALIFIED_LD_HELPER_SHA256
        ),
        "re1_harness_identity_recorded": bool(
            test_side[
                "scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
            ]
        ),
        "pass": repo == QUALIFIED_REPO_SHA256
        and installed == QUALIFIED_HARL_SHA256
        and test_side[
            "scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py"
        ]
        == QUALIFIED_LD_HELPER_SHA256,
    }


def run_static() -> dict[str, object]:
    base = SINGLE.run_static()
    sources = _source_identity()
    repository = SINGLE._repository_authority()
    result = {
        "interpreter_exact": _normal_path(sys.executable)
        == _normal_path(EXPECTED_PYTHON),
        "repository_authority": repository,
        "qualified_source_identity": sources,
        "r5i_r7_static_authority": base,
    }
    result["pass"] = bool(
        result["interpreter_exact"]
        and sources["pass"]
        and base["pass"]
        and repository["head"] == EXPECTED_HEAD
        and repository["head_origin_merge_base_equal"]
        and repository["staged_path_count"] == 359
        and repository["staged_index_sha256"]
        == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
    )
    return result


def _optimizer_step_vector(
    module: object, optimizer: object
) -> tuple[tuple[str, int], ...]:
    values: list[tuple[str, int]] = []
    for name, parameter in module.named_parameters():
        state = optimizer.state.get(parameter, {})
        step = state.get("step", 0)
        if hasattr(step, "item"):
            step = step.item()
        values.append((name, int(step)))
    return tuple(values)


def _finite_module(module: object) -> bool:
    import torch

    return all(bool(torch.isfinite(value).all().item()) for value in module.parameters())


def _finite_optimizer(optimizer: object) -> bool:
    import torch

    return all(
        not torch.is_tensor(value) or bool(torch.isfinite(value).all().item())
        for state in optimizer.state.values()
        for value in state.values()
    )


def _learner_snapshot(
    *,
    actors: Sequence[object],
    critic: object,
    live_value_normalizer: object,
) -> dict[str, object]:
    from isaaclab_tasks.direct.scan_mobile_manipulator import (
        assignment_event_training_full_transaction as R5,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator import (
        assignment_event_training_critic_mutation as R4,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_gradient_probe import (
        validate_gradients_clear_v1,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_evidence import (
        canonical_digest_v1,
        canonical_live_valuenorm_state_v1,
    )
    import torch

    actor_values, critic_value, valuenorm_value = R5._parameter_optimizer_digests(
        actors, critic, live_value_normalizer
    )
    validate_gradients_clear_v1(
        tuple((f"actor{index}", actor.actor) for index, actor in enumerate(actors))
        + (("critic", critic.critic),)
    )
    canonical_valuenorm = R4._valuenorm_digest(live_value_normalizer)
    canonical_valuenorm_state = canonical_live_valuenorm_state_v1(
        live_value_normalizer
    )
    _require(canonical_valuenorm == valuenorm_value, "VALUENORM_FINGERPRINT_SPLIT")
    payload = {
        "actor_parameter_optimizer_digests": actor_values,
        "actor_parameter_digests": tuple(value[0] for value in actor_values),
        "actor_optimizer_digests": tuple(value[1] for value in actor_values),
        "critic_parameter_optimizer_digests": critic_value,
        "critic_parameter_digest": critic_value[0],
        "critic_optimizer_digest": critic_value[1],
        "canonical_valuenorm_digest": canonical_valuenorm,
        "actor_adam_steps": tuple(
            _optimizer_step_vector(actor.actor, actor.actor_optimizer)
            for actor in actors
        ),
        "critic_adam_steps": _optimizer_step_vector(
            critic.critic, critic.critic_optimizer
        ),
        "actor_object_ids": tuple(id(actor) for actor in actors),
        "actor_module_ids": tuple(id(actor.actor) for actor in actors),
        "actor_optimizer_ids": tuple(id(actor.actor_optimizer) for actor in actors),
        "critic_object_id": id(critic),
        "critic_module_id": id(critic.critic),
        "critic_optimizer_id": id(critic.critic_optimizer),
        "valuenorm_object_id": id(live_value_normalizer),
        "actor_modes_rollout": all(not actor.actor.training for actor in actors),
        "critic_mode_rollout": not critic.critic.training,
        "gradients_clean": True,
        "actor_parameters_finite": all(_finite_module(actor.actor) for actor in actors),
        "actor_optimizer_states_finite": all(
            _finite_optimizer(actor.actor_optimizer) for actor in actors
        ),
        "critic_parameters_finite": _finite_module(critic.critic),
        "critic_optimizer_state_finite": _finite_optimizer(
            critic.critic_optimizer
        ),
        "valuenorm_state_finite": all(
            bool(torch.isfinite(value).all().item())
            for value in canonical_valuenorm_state.values()
        ),
    }
    payload["state_digest"] = canonical_digest_v1(
        (
            actor_values,
            critic_value,
            canonical_valuenorm,
            payload["actor_adam_steps"],
            payload["critic_adam_steps"],
            payload["actor_module_ids"],
            payload["actor_optimizer_ids"],
            payload["critic_module_id"],
            payload["critic_optimizer_id"],
            payload["valuenorm_object_id"],
        )
    )
    return payload


def _step_map(values: Sequence[tuple[str, int]]) -> dict[str, int]:
    return {name: int(step) for name, step in values}


def _require_step_delta(
    *,
    before: Sequence[tuple[str, int]],
    after: Sequence[tuple[str, int]],
    expected_delta: int,
    code: str,
) -> None:
    left, right = _step_map(before), _step_map(after)
    _require(left.keys() == right.keys(), code, "optimizer parameter keys changed")
    drift = {
        name: (left[name], right[name])
        for name in left
        if right[name] - left[name] != expected_delta
    }
    _require(not drift, code, drift)


def _persistent_state_equal(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return all(
        left[key] == right[key]
        for key in (
            "actor_parameter_optimizer_digests",
            "actor_parameter_digests",
            "actor_optimizer_digests",
            "critic_parameter_optimizer_digests",
            "critic_parameter_digest",
            "critic_optimizer_digest",
            "canonical_valuenorm_digest",
            "actor_adam_steps",
            "critic_adam_steps",
            "actor_object_ids",
            "actor_module_ids",
            "actor_optimizer_ids",
            "critic_object_id",
            "critic_module_id",
            "critic_optimizer_id",
            "valuenorm_object_id",
        )
    )


def _run_repeated_smoke(
    checkpoints: object,
    resources: dict[str, object],
    *,
    artifact_prefix: Path,
) -> dict[str, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import (
        EventOnPolicyCriticBufferEPV2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import (
        _compose_dormant_event_learned_policy_route_v2,
        get_dormant_event_learned_policy_route_descriptor_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import (
        seal_current_event_policy_decision_bundle_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import (
        capture_current_event_policy_evidence_snapshot_v2,
        capture_event_policy_physical_problem_evidence_v2,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
        _EventProfileLifecycleDomainSpec,
        _EventProfileLifecycleRuntimeDomain,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import (
        build_assignment_event_profile_schema_v2_descriptor,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_evidence import (
        canonical_digest_v1,
        fingerprint_tensor_v1,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_real_isaac_adapter import (
        execute_real_isaac_single_transaction_v1,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import (
        _compose_event_assignment_harl_wrapper,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        TerminationReason,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
        AssignmentProfileName,
        AssignmentProfileResolutionOrigin,
        resolve_assignment_profile,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import (
        assignment_to_env_actions,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import (
        ScanMobileManipulatorEnvCfg,
    )
    from isaaclab_tasks.direct.scan_mobile_manipulator import (
        assignment_event_training_evidence as E,
    )

    algo_args = V2.load_production_algo_args()
    set_seed(dict(algo_args["seed"]))
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
    _require(device == torch.device(DEVICE), "CONFIG_DEVICE", str(device))
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
        assignment_profile_entrypoint="B2-T0.bounded_repeated_update_smoke",
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
        return seal_current_event_policy_decision_bundle_v2(
            evidence_snapshot=snapshot
        )

    def validate_current(bundle):
        bundle.evidence_snapshot.validate_current(
            current_publication=domain.current_read_port.read_current(),
            current_open_window_view=domain.interstep_fence_read_port.read(),
        )

    def action_builder(environment: object, assignment: torch.Tensor):
        _require(environment is raw, "P2_CONTROLLER_IDENTITY")
        controls = assignment_to_env_actions(environment, assignment)
        _require(
            all(
                value.device == device and bool(torch.isfinite(value).all())
                for value in controls.values()
            ),
            "CONTROLLER_TENSOR",
        )
        control_assignments.append(assignment.detach().clone())
        return controls

    def forbidden_actor_trainer(**_kwargs):
        raise RuntimeError("STOP — B2-T0 PARALLEL_ACTOR_TRAINER")

    def forbidden_critic_trainer(_buffer, _normalizer):
        raise RuntimeError("STOP — B2-T0 PARALLEL_CRITIC_TRAINER")

    scale = raw._event_terminal_critic_scale_contract_v2
    schema = build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=scale
    )
    actor_dim = int(schema["actor_schema"]["dimension"])
    critic_dim = int(schema["critic_schema"]["dimension"])
    model_args = dict(algo_args["model"])
    algorithm_args = dict(algo_args["algo"])
    actor_args = {**model_args, **algorithm_args}
    critic_args = {**model_args, **algorithm_args}
    actors_raw = [
        HAPPO(
            actor_args,
            V2.Box((actor_dim,)),
            gym.spaces.Discrete(resolved_N + 1),
            device=device,
        )
        for _ in range(resolved_M)
    ]
    critic_raw = VCritic(critic_args, V2.Box((critic_dim,)), device=device)
    live_value_normalizer = ValueNorm(1, device=device)
    actors = [
        V2.ActorRecorder(actor, index) for index, actor in enumerate(actors_raw)
    ]
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
    resources["private_route_constructions"] = 1
    resources["transaction_coordinator_instances"] = 0
    resources["distinct_learner_constructions"] = 1

    reset_result = route.reset()
    resources["real_resets"] = 1
    _require(
        type(reset_result) is tuple and len(reset_result) == 3,
        "REAL_RESET_CONTRACT",
    )
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
        _require("not runtime-ready" in str(exc), "PUBLIC_FENCE_ERROR", str(exc))
    else:
        raise RuntimeError("STOP — B2-T0 PUBLIC_ROUTE_OPEN")
    _require(
        int(raw.common_step_counter) == step_before,
        "PUBLIC_FENCE_MUTATION",
    )
    descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
    _require(
        descriptor["route"] == "private_test_only_dormant"
        and descriptor["public_activation"]
        == "blocked_pending_B2_V1_V2_R",
        "PUBLIC_ROUTE_OPEN",
        descriptor,
    )

    repo_hashes, harl_hashes = SINGLE._source_authority(E)
    run_identity = f"b2-t0-re1-repeated-smoke-{os.getpid()}"
    runtime_config = {
        "environment": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        "profile": profile.profile_name.value,
        "device": str(device),
        "T": resolved_T,
        "E": resolved_E,
        "M": resolved_M,
        "N": resolved_N,
        "actor_epochs": int(algo_args["algo"]["ppo_epoch"]),
        "actor_minibatches": int(algo_args["algo"]["actor_num_mini_batch"]),
        "critic_epochs": int(algo_args["algo"]["critic_epoch"]),
        "critic_minibatches": int(algo_args["algo"]["critic_num_mini_batch"]),
        "valuenorm_enabled": True,
        "fixed_order": bool(algo_args["algo"]["fixed_order"]),
    }
    source_config_identity = {
        "qualified_source_identity": resources["qualified_source_identity"],
        "runtime_repo_source_authority": repo_hashes,
        "runtime_installed_harl_source_authority": harl_hashes,
        "runtime_config": runtime_config,
    }
    source_config_identity_digest = _json_digest(source_config_identity)
    initial_learner = _learner_snapshot(
        actors=actors_raw,
        critic=critic_raw,
        live_value_normalizer=live_value_normalizer,
    )
    resources["run_identity"] = run_identity
    resources["initial_learner"] = initial_learner
    _atomic_json(
        _artifact_path(artifact_prefix, "process_config_authority"),
        {
            "schema_version": "b2_t0_re1_process_config_authority_v1",
            "run_identity": run_identity,
            "process_id": os.getpid(),
            "fresh_process": True,
            "historical_route_reused": False,
            "repository_authority": resources["repository_authority"],
            "qualified_source_identity": resources["qualified_source_identity"],
            "runtime_config": runtime_config,
            "source_config_identity": source_config_identity,
            "source_config_identity_digest": source_config_identity_digest,
            "learner_identity": initial_learner,
            "app_launcher_lifetimes": 1,
            "environment_constructions": 1,
            "distinct_learner_constructions": 1,
            "checkpoint_weight_io": 0,
            "public_route_activations": 0,
        },
    )

    transactions: list[dict[str, object]] = []
    bridges: list[dict[str, object]] = []
    prior_post_state: dict[str, object] | None = None
    prior_update_id: str | None = None
    prior_rollout_digest: str | None = None
    prior_s10_artifact: dict[str, object] | None = None
    historical_terminal_keys: set[tuple[int, int, int]] = set()
    lifecycle_decision_gate_receipts: list[dict[str, object]] = []
    previous_observed_episode_generations: tuple[int, ...] | None = None

    for transaction_index in range(1, TRANSACTION_COUNT + 1):
        transaction_decision_gate_receipts: list[dict[str, object]] = []
        resources["active_transaction"] = transaction_index
        resources["adapter_transaction_returned"] = False
        update_id = f"{run_identity}-tx{transaction_index}"
        _require(
            update_id not in {item["update_id"] for item in transactions},
            "UPDATE_ID_REUSE",
            update_id,
        )
        tx_identity = {
            "run_identity": run_identity,
            "transaction_index": transaction_index,
            "update_id": update_id,
            "process_id": os.getpid(),
            "source_config_identity_digest": source_config_identity_digest,
        }
        pre_collection = _learner_snapshot(
            actors=actors_raw,
            critic=critic_raw,
            live_value_normalizer=live_value_normalizer,
        )
        if prior_post_state is not None:
            _require(
                _persistent_state_equal(prior_post_state, pre_collection),
                "LEARNER_STATE_REINITIALIZATION",
                (prior_post_state["state_digest"], pre_collection["state_digest"]),
            )
        _require(not route.poisoned, "POISONED_ROUTE_CONTINUATION")
        _require(
            all(storage.next_action_slot == 0 for storage in route.actor_storages)
            and buffer.step == 0
            and not bool(buffer._event_slot_written.any().item())
            and not bool(buffer._event_returns_computed)
            and not route.collector.consumed_terminal_keys,
            "BRIDGE_START_NOT_QUIESCENT",
        )
        slot_zero_bundle = route.current_decision_bundle
        slot_zero_digest = canonical_digest_v1(
            (
                fingerprint_tensor_v1(
                    slot_zero_bundle.evidence_snapshot.actor_obs
                ).content_digest,
                fingerprint_tensor_v1(
                    slot_zero_bundle.evidence_snapshot.runner_share_obs
                ).content_digest,
                fingerprint_tensor_v1(
                    slot_zero_bundle.runner_available_actions
                ).content_digest,
                fingerprint_tensor_v1(
                    slot_zero_bundle.decision_valid_mask
                ).content_digest,
                slot_zero_bundle.evidence_identity.episode_generations,
                slot_zero_bundle.evidence_identity.transition_generations,
            )
        )

        bridge: dict[str, object] | None = None
        bridge_pre_path: Path | None = None
        bridge_pre_digest: str | None = None
        if prior_post_state is not None:
            bridge_index = transaction_index - 1
            previous_q = transactions[-1][
                "transaction"
            ].r5_transaction.quiescence_evidence
            _require(
                prior_s10_artifact is not None
                and previous_q.pending_backward_permits == 0
                and previous_q.pending_optimizer_permits == 0
                and previous_q.pending_valuenorm_permits == 0
                and previous_q.unconsumed_terminal_keys == 0
                and previous_q.actor_cursors_reset
                and previous_q.critic_cursor_reset
                and previous_q.event_returns_compute_once_reset
                and previous_q.next_rollout_guards_established,
                f"BRIDGE{bridge_index}_PRE_COLLECTION_NOT_QUIESCENT",
            )
            bridge_pre_path = _artifact_path(
                artifact_prefix, f"bridge{bridge_index}_pre_collection"
            )
            bridge_pre = {
                "schema_version": "b2_t0_re1_bridge_pre_collection_v1",
                "stage": "DURABLE_BEFORE_NEXT_TRANSACTION_PHYSICAL_STEP",
                "run_identity": run_identity,
                "bridge_index": bridge_index,
                "transaction_index": transaction_index,
                "from_update_id": prior_update_id,
                "next_intended_update_id": update_id,
                "process_id": os.getpid(),
                "source_config_identity_digest": source_config_identity_digest,
                "previous_s10_artifact": prior_s10_artifact,
                "previous_post_learner": prior_post_state,
                "next_pre_collection_learner": pre_collection,
                "learner_post_to_pre_exact": _persistent_state_equal(
                    prior_post_state, pre_collection
                ),
                "persistent_learner_object_identity": (
                    prior_post_state["actor_module_ids"]
                    == pre_collection["actor_module_ids"]
                    and prior_post_state["actor_optimizer_ids"]
                    == pre_collection["actor_optimizer_ids"]
                    and prior_post_state["critic_module_id"]
                    == pre_collection["critic_module_id"]
                    and prior_post_state["critic_optimizer_id"]
                    == pre_collection["critic_optimizer_id"]
                    and prior_post_state["valuenorm_object_id"]
                    == pre_collection["valuenorm_object_id"]
                ),
                "route_poisoned": bool(route.poisoned),
                "models_in_rollout_mode": bool(
                    pre_collection["actor_modes_rollout"]
                    and pre_collection["critic_mode_rollout"]
                ),
                "gradients_clean": bool(pre_collection["gradients_clean"]),
                "permits_zero": True,
                "terminal_ledger_empty": not bool(
                    route.collector.consumed_terminal_keys
                ),
                "actor_cursors_reset": all(
                    storage.next_action_slot == 0
                    for storage in route.actor_storages
                ),
                "critic_rollover_complete": bool(
                    buffer.step == 0
                    and not bool(buffer._event_slot_written.any().item())
                ),
                "event_return_compute_once_reset": not bool(
                    buffer._event_returns_computed
                ),
                "slot_zero_current_runtime_identity": {
                    "digest": slot_zero_digest,
                    "episode_generations": tuple(
                        slot_zero_bundle.evidence_identity.episode_generations
                    ),
                    "transition_generations": tuple(
                        slot_zero_bundle.evidence_identity.transition_generations
                    ),
                },
                "physical_steps_before_receipt": int(
                    resources.get("real_rollout_steps", 0)
                ),
                "next_collection_authorized": True,
                "pass": True,
            }
            _atomic_json(bridge_pre_path, bridge_pre)
            bridge_pre_digest = _sha(bridge_pre_path)
            bridge = {
                "bridge_index": bridge_index,
                "from_update_id": prior_update_id,
                "to_update_id": update_id,
                "update_id_changed": prior_update_id != update_id,
                "pre_collection_receipt": {
                    "path": str(bridge_pre_path),
                    "bytes": bridge_pre_path.stat().st_size,
                    "sha256": bridge_pre_digest,
                },
                "pre_collection_pass": True,
                "post_collection_pass": False,
                "next_s0_established": False,
                "pass": False,
            }
            bridges.append(bridge)

        actor_call_start = tuple(len(actor.calls) for actor in actors)
        control_start = len(control_assignments)
        terminal_copy_start = len(terminal_slots_before_ack)
        first = route.collect_step()
        resources["real_rollout_steps"] = int(
            resources.get("real_rollout_steps", 0)
        ) + 1
        _require(
            not bool(first.harl_step_result[3].any()),
            f"TX{transaction_index}_FIRST_STEP_TERMINAL",
        )
        first_effective = V2.expected_assignment(
            first.facade_result.admitted_publication, torch
        )
        _require(
            len(control_assignments) == control_start + 1
            and torch.equal(control_assignments[-1], first_effective),
            f"TX{transaction_index}_FINAL_P2_CONTROLLER",
        )
        first_actor_calls = tuple(len(actor.calls) for actor in actors)
        first_gate, previous_observed_episode_generations = (
            _capture_lifecycle_decision_gate_v1(
                receipt=first,
                actors=actors,
                actor_calls_before=actor_call_start,
                actor_calls_after=first_actor_calls,
                transaction_index=transaction_index,
                collection_index=int(resources["real_rollout_steps"]),
                physical_step_index=1,
                previous_episode_generations=previous_observed_episode_generations,
            )
        )
        transaction_decision_gate_receipts.append(first_gate)
        lifecycle_decision_gate_receipts.append(first_gate)

        critic_start = len(critic.calls)
        route_event_start = len(route_events)
        second_actor_call_start = first_actor_calls
        second = route.collect_step()
        resources["real_rollout_steps"] = int(
            resources.get("real_rollout_steps", 0)
        ) + 1
        _require(
            not bool(first.harl_step_result[3].any()),
            f"TX{transaction_index}_FIRST_STEP_TERMINAL",
        )
        _require(
            bool(second.harl_step_result[3].all()),
            f"TX{transaction_index}_TERMINAL_NOT_REACHED",
        )
        first_effective = V2.expected_assignment(
            first.facade_result.admitted_publication, torch
        )
        second_effective = V2.expected_assignment(
            second.facade_result.admitted_publication, torch
        )
        _require(
            len(control_assignments) == control_start + 2
            and torch.equal(control_assignments[control_start], first_effective)
            and torch.equal(
                control_assignments[control_start + 1], second_effective
            ),
            f"TX{transaction_index}_P2_CONTROLLER",
        )
        actor_calls_after = tuple(len(actor.calls) for actor in actors)
        second_gate, previous_observed_episode_generations = (
            _capture_lifecycle_decision_gate_v1(
                receipt=second,
                actors=actors,
                actor_calls_before=second_actor_call_start,
                actor_calls_after=actor_calls_after,
                transaction_index=transaction_index,
                collection_index=int(resources["real_rollout_steps"]),
                physical_step_index=2,
                previous_episode_generations=previous_observed_episode_generations,
            )
        )
        transaction_decision_gate_receipts.append(second_gate)
        lifecycle_decision_gate_receipts.append(second_gate)

        second_events = route_events[route_event_start:]
        timeout_events = [
            detail
            for stage, detail in second_events
            if stage == "I5a_critic_buffer_insert"
        ]
        timeout_call_count = (
            int(timeout_events[0].critic_batch_calls)
            if len(timeout_events) == 1
            and hasattr(timeout_events[0], "critic_batch_calls")
            else 0
        )
        timeout_identity = V2.identify_pd2_s6_timeout_critic_call_v1(
            second_collect_start_call_index=critic_start,
            second_collect_end_call_index=len(critic.calls),
            timeout_batch_event_count=len(timeout_events),
            observed_timeout_call_count=timeout_call_count,
        )
        history = second.facade_result.terminal_historical_payload
        resources["terminal_autoreset_events"] = int(
            resources.get("terminal_autoreset_events", 0)
        ) + len(history)
        _require(
            len(history) == resolved_E
            and all(row.optional_sidecar is not None for row in history),
            f"TX{transaction_index}_HISTORICAL_TERMINAL",
        )
        _require(
            len(terminal_slots_before_ack) == terminal_copy_start + 1
            and len(terminal_slots_before_ack[-1]) == resolved_E,
            f"TX{transaction_index}_TERMINAL_COPY_BEFORE_ACK",
        )
        _require(
            domain.terminal_consumer_port.capture_pending_terminal_artifacts()
            == (),
            f"TX{transaction_index}_RUNTIME_ACK",
        )
        pre_reset_obs = torch.stack(
            [row.optional_sidecar.bootstrap_critic_obs for row in history],
            dim=0,
        )
        post_reset_obs = (
            second.next_decision_bundle.evidence_snapshot.runner_share_obs[:, 0]
        )
        observed_timeout = critic.observed_input(
            timeout_identity.timeout_call_global_index
        )
        correlation = V2.compare_pd2_s6_timeout_critic_input_exact_v1(
            pre_reset_obs,
            observed_timeout,
            invocation_identity=timeout_identity,
        )
        V2.adjudicate_pd2_s6_timeout_critic_input_correlation_v1(correlation)
        _require(
            not torch.equal(pre_reset_obs, post_reset_obs),
            f"TX{transaction_index}_HISTORICAL_CURRENT_ALIAS",
        )
        reason_grid = buffer.termination_reason.detach().clone()
        _require(
            bool((reason_grid[0] == int(TerminationReason.NONE)).all())
            and bool(
                (reason_grid[1] == int(TerminationReason.TIME_LIMIT)).all()
            ),
            f"TX{transaction_index}_TERMINATION_REASON",
        )
        history_keys = tuple(
            (
                row.env_id,
                row.episode_generation,
                row.transition_generation,
            )
            for row in history
        )
        _require(
            not historical_terminal_keys.intersection(history_keys),
            f"TX{transaction_index}_STALE_TERMINAL_KEY",
            history_keys,
        )
        historical_terminal_keys.update(history_keys)

        actor_obs_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(storage.obs[:-1]).content_digest
                for storage in route.actor_storages
            )
        )
        critic_obs_digest = fingerprint_tensor_v1(
            buffer.share_obs[:-1]
        ).content_digest
        proposal_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(storage.action_ids).content_digest
                for storage in route.actor_storages
            )
        )
        behavior_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(storage.action_logprobs).content_digest
                for storage in route.actor_storages
            )
        )
        dvm_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(
                    storage.decision_valid_masks[:-1]
                ).content_digest
                for storage in route.actor_storages
            )
        )
        availability_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(storage.available_actions[:-1]).content_digest
                for storage in route.actor_storages
            )
        )
        active_mask_digest = canonical_digest_v1(
            tuple(
                fingerprint_tensor_v1(storage.active_masks[:-1]).content_digest
                for storage in route.actor_storages
            )
        )
        critic_mask_digest = canonical_digest_v1(
            (
                fingerprint_tensor_v1(buffer.masks[:-1]).content_digest,
                fingerprint_tensor_v1(buffer.bad_masks[:-1]).content_digest,
            )
        )
        transition_identity_digest = canonical_digest_v1(
            tuple(
                tuple(
                    (
                        bundle.evidence_identity.episode_generations,
                        bundle.evidence_identity.transition_generations,
                    )
                    for bundle in storage.decision_bundle_refs[:-1]
                )
                for storage in route.actor_storages
            )
        )
        rollout_digest = canonical_digest_v1(
            (
                slot_zero_digest,
                actor_obs_digest,
                critic_obs_digest,
                availability_digest,
                proposal_digest,
                behavior_digest,
                dvm_digest,
                active_mask_digest,
                critic_mask_digest,
                transition_identity_digest,
                history_keys,
            )
        )
        rollout_provenance = {
            "transaction_index": transaction_index,
            "update_id": update_id,
            "collection_physical_step_range": (
                int(resources["real_rollout_steps"]) - resolved_T + 1,
                int(resources["real_rollout_steps"]),
            ),
            "transition_identity_digest": transition_identity_digest,
            "terminal_history_keys": history_keys,
        }
        rollout_provenance_digest = _json_digest(rollout_provenance)
        collection_post = _learner_snapshot(
            actors=actors_raw,
            critic=critic_raw,
            live_value_normalizer=live_value_normalizer,
        )
        _require(
            _persistent_state_equal(pre_collection, collection_post),
            f"TX{transaction_index}_COLLECTION_MUTATED_LEARNER",
            (pre_collection["state_digest"], collection_post["state_digest"]),
        )
        _require(
            all(
                storage.next_action_slot == resolved_T
                for storage in route.actor_storages
            )
            # HARL's bounded critic cursor is cyclic: after exactly T inserts it
            # returns to zero.  Completion authority is the all-written ledger.
            and buffer.step == 0
            and bool(buffer._event_slot_written.all().item()),
            f"TX{transaction_index}_ROLLOUT_INCOMPLETE",
            {
                "actor_cursors": tuple(
                    storage.next_action_slot for storage in route.actor_storages
                ),
                "critic_cyclic_cursor": int(buffer.step),
                "event_slots_written": tuple(
                    bool(value) for value in buffer._event_slot_written.tolist()
                ),
            },
        )

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

        rollout_decision_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_rollout_decision_evidence"
        )
        rollout_decision_payload = {
            "schema_version": "b2_t0_re1_rollout_decision_evidence_v1",
            **tx_identity,
            "stage": "ROLLOUT_VALIDATED_BEFORE_LEARNER_MUTATION",
            "source_config_identity_digest": source_config_identity_digest,
            "rollout_evidence_digest": rollout_digest,
            "rollout_provenance": rollout_provenance,
            "rollout_provenance_digest": rollout_provenance_digest,
            "previous_rollout_evidence_digest": prior_rollout_digest,
            "numeric_digest_equal_to_previous": (
                prior_rollout_digest is not None
                and rollout_digest == prior_rollout_digest
            ),
            "fresh_rollout_provenance": True,
            "actor_observation_digest": actor_obs_digest,
            "critic_observation_digest": critic_obs_digest,
            "proposal_action_digest": proposal_digest,
            "behavior_logprob_digest": behavior_digest,
            "dvm_digest": dvm_digest,
            "active_mask_digest": active_mask_digest,
            "available_action_mask_digest": availability_digest,
            "critic_mask_digest": critic_mask_digest,
            "transition_identity_digest": transition_identity_digest,
            "lifecycle_decision_gate_receipts": tuple(
                transaction_decision_gate_receipts
            ),
            "actor_call_cardinality_receipts": tuple(
                receipt["policy_call_counts"]
                for receipt in transaction_decision_gate_receipts
            ),
            "terminal_autoreset_evidence": {
                "history_keys": history_keys,
                "history_keys_fresh": True,
                "runtime_ack_complete": True,
                "learner_ledger_retained": bool(
                    route.collector.consumed_terminal_keys
                ),
                "timeout_critic_exact_match": bool(correlation.exact_value_match),
                "pre_reset_critic_digest": fingerprint_tensor_v1(
                    pre_reset_obs
                ).content_digest,
                "post_reset_current_critic_digest": fingerprint_tensor_v1(
                    post_reset_obs
                ).content_digest,
            },
            "learner_before_collection": pre_collection,
            "learner_after_collection": collection_post,
            "collection_preserved_learner": _persistent_state_equal(
                pre_collection, collection_post
            ),
            "pass": True,
        }
        _atomic_json(rollout_decision_path, rollout_decision_payload)
        rollout_decision_digest = _sha(rollout_decision_path)

        if bridge is not None:
            bridge_post_path = _artifact_path(
                artifact_prefix,
                f"bridge{transaction_index - 1}_post_collection",
            )
            bridge_post = {
                "schema_version": "b2_t0_re1_bridge_post_collection_v1",
                "stage": "DURABLE_AFTER_COLLECTION_BEFORE_NEXT_LEARNER_MUTATION",
                **tx_identity,
                "bridge_index": transaction_index - 1,
                "source_config_identity_digest": source_config_identity_digest,
                "pre_collection_receipt_digest": bridge_pre_digest,
                "pre_collection_receipt_path": str(bridge_pre_path),
                "rollout_decision_evidence_digest": rollout_decision_digest,
                "rollout_decision_evidence_path": str(rollout_decision_path),
                "rollout_evidence_digest": rollout_digest,
                "rollout_provenance_digest": rollout_provenance_digest,
                "actor_observation_digest": actor_obs_digest,
                "critic_observation_digest": critic_obs_digest,
                "proposal_action_digest": proposal_digest,
                "behavior_logprob_digest": behavior_digest,
                "dvm_digest": dvm_digest,
                "active_mask_digest": active_mask_digest,
                "lifecycle_decision_gate_receipts": tuple(
                    transaction_decision_gate_receipts
                ),
                "terminal_autoreset_evidence": rollout_decision_payload[
                    "terminal_autoreset_evidence"
                ],
                "actor_call_cardinality_receipts": rollout_decision_payload[
                    "actor_call_cardinality_receipts"
                ],
                "learner_pre_collection": pre_collection,
                "learner_post_collection": collection_post,
                "collection_preserved_learner": _persistent_state_equal(
                    pre_collection, collection_post
                ),
                "fresh_rollout_provenance": True,
                "stale_rollout_evidence": False,
                "stale_terminal_evidence": False,
                "pass": True,
            }
            _atomic_json(bridge_post_path, bridge_post)
            bridge["post_collection_receipt"] = {
                "path": str(bridge_post_path),
                "bytes": bridge_post_path.stat().st_size,
                "sha256": _sha(bridge_post_path),
            }
            bridge["learner_post_to_pre_exact"] = _persistent_state_equal(
                prior_post_state, pre_collection
            )
            bridge["collection_preserved_learner"] = _persistent_state_equal(
                pre_collection, collection_post
            )
            bridge["persistent_object_identity"] = (
                prior_post_state["actor_module_ids"]
                == collection_post["actor_module_ids"]
                and prior_post_state["actor_optimizer_ids"]
                == collection_post["actor_optimizer_ids"]
                and prior_post_state["critic_module_id"]
                == collection_post["critic_module_id"]
                and prior_post_state["critic_optimizer_id"]
                == collection_post["critic_optimizer_id"]
                and prior_post_state["valuenorm_object_id"]
                == collection_post["valuenorm_object_id"]
            )
            bridge["route_unpoisoned"] = not route.poisoned
            bridge["rollout_modes_valid"] = bool(
                collection_post["actor_modes_rollout"]
                and collection_post["critic_mode_rollout"]
            )
            bridge["ledger_empty_before_collection"] = True
            bridge["slot_zero_current_state_digest"] = slot_zero_digest
            bridge["new_rollout_digest"] = rollout_digest
            bridge["previous_rollout_digest"] = prior_rollout_digest
            bridge["new_rollout_evidence"] = True
            bridge["new_rollout_provenance_digest"] = rollout_provenance_digest
            bridge["numeric_digest_equal_to_previous"] = (
                rollout_digest == prior_rollout_digest
            )
            bridge["stale_permits"] = 0
            bridge["stale_gradients"] = 0
            bridge["actor_cursors_after_collection"] = tuple(
                storage.next_action_slot for storage in route.actor_storages
            )
            bridge["critic_cursor_after_collection"] = int(buffer.step)
            bridge["post_collection_pass"] = True
        pre_mutation_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_pre_mutation"
        )
        factor_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_actor_factor_progress"
        )
        critic_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_critic_progress"
        )
        s10_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_s10"
        )
        failure_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_failure"
        )
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
            path: Path,
            events: list[object],
            payload: Mapping[str, object],
        ) -> None:
            for key in progress_counts:
                if key in payload:
                    progress_counts[key] = int(payload[key])
            event = V2.normalize(
                {**tx_identity, **progress_counts, **payload}
            )
            events.append(event)
            _atomic_json(
                path,
                {
                    **tx_identity,
                    **progress_counts,
                    "stage": payload["stage"],
                    "events": events,
                    "event_count": len(events),
                },
            )

        def persist_factor(payload: Mapping[str, object]) -> None:
            persist_progress(factor_path, factor_events, payload)

        def persist_critic(payload: Mapping[str, object]) -> None:
            persist_progress(critic_path, critic_events, payload)

        def persist_pre_mutation(payload: Mapping[str, object]) -> None:
            _atomic_json(
                pre_mutation_path,
                {
                    **payload,
                    **tx_identity,
                    **progress_counts,
                    "stage": "S5_ENTRY_BEFORE_FIRST_MUTATION",
                    "learner_state_before_collection": pre_collection,
                    "learner_state_after_collection": collection_post,
                    "collection_preserved_learner": _persistent_state_equal(
                        pre_collection, collection_post
                    ),
                    "slot_zero_current_state_digest": slot_zero_digest,
                    "rollout_evidence_digest": rollout_digest,
                    "previous_rollout_evidence_digest": prior_rollout_digest,
                    "fresh_rollout_provenance": True,
                    "rollout_provenance_digest": rollout_provenance_digest,
                    "numeric_digest_equal_to_previous": (
                        prior_rollout_digest is not None
                        and rollout_digest == prior_rollout_digest
                    ),
                    "terminal_history_keys": history_keys,
                    "terminal_keys_new": not bool(
                        set(history_keys).intersection(
                            historical_terminal_keys.difference(history_keys)
                        )
                    ),
                    "terminal_pre_reset_critic_digest": fingerprint_tensor_v1(
                        pre_reset_obs
                    ).content_digest,
                    "terminal_post_reset_current_critic_digest": (
                        fingerprint_tensor_v1(post_reset_obs).content_digest
                    ),
                    "timeout_critic_exact_identity": bool(
                        correlation.exact_value_match
                    ),
                    "runtime_ack_complete": True,
                    "learner_ledger_retained_after_ack": bool(
                        route.collector.consumed_terminal_keys
                    ),
                    "stock_compute_returns_calls": 0,
                    "bridge_receipt": bridge,
                    "rollout_decision_evidence": {
                        "path": str(rollout_decision_path),
                        "bytes": rollout_decision_path.stat().st_size,
                        "sha256": rollout_decision_digest,
                    },
                },
            )

        def persist_post_failure(payload: Mapping[str, object]) -> None:
            failure = {
                **tx_identity,
                **progress_counts,
                **payload,
                "stage": "FAILED",
                "factor_progress_event_count": len(factor_events),
                "critic_progress_event_count": len(critic_events),
            }
            _atomic_json(failure_path, failure)
            _atomic_json(_artifact_path(artifact_prefix, "failure"), failure)

        transaction = execute_real_isaac_single_transaction_v1(
            repository_head=EXPECTED_HEAD,
            dirty_state_classification=(
                "reviewed uncommitted B2-R0-R7 plus authorized B2-T0 harness"
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
            order_seed=int(algo_args["seed"]["seed"])
            + transaction_index
            - 1,
            classification=PASS,
            pre_mutation_observer=persist_pre_mutation,
            factor_segment_observer=persist_factor,
            critic_progress_observer=persist_critic,
            post_failure_observer=persist_post_failure,
        )
        resources["adapter_transaction_returned"] = True
        resources["transaction_coordinator_instances"] = int(
            resources["transaction_coordinator_instances"]
        ) + 1
        _require(
            pre_mutation_path.is_file(),
            f"TX{transaction_index}_PRE_MUTATION_ARTIFACT_MISSING",
        )
        segments = [
            item
            for item in factor_events
            if item["stage"] == "S5_ACTOR_SEGMENT_COMPLETE"
        ]
        minibatches = [
            item
            for item in critic_events
            if item["stage"] == "S6_CRITIC_MINIBATCH_COMPLETE"
        ]
        vn_updates = [
            item
            for item in critic_events
            if item["stage"] == "S6_VALUENORM_POST_UPDATE_OBSERVED"
        ]
        _require(
            len(segments) == resolved_M
            and factor_events[-1].get("complete_actor_sequence")
            and critic_events[-1].get("complete_critic_sequence")
            and len(minibatches) == transaction.real_audit.critic_expected_step
            and len(vn_updates) == transaction.real_audit.valuenorm_expected_update
            and all(
                item["canonical_mutation"]
                and item["canonical_state_finite"]
                for item in vn_updates
            ),
            f"TX{transaction_index}_DURABLE_RECEIPTS_INCOMPLETE",
        )

        post_update = _learner_snapshot(
            actors=actors_raw,
            critic=critic_raw,
            live_value_normalizer=live_value_normalizer,
        )
        expected_actor_steps = dict(transaction.real_audit.actor_expected_step)
        for actor_id in range(resolved_M):
            _require_step_delta(
                before=pre_collection["actor_adam_steps"][actor_id],
                after=post_update["actor_adam_steps"][actor_id],
                expected_delta=expected_actor_steps[actor_id],
                code=f"TX{transaction_index}_ACTOR_OPTIMIZER_STATE_RESET",
            )
        _require_step_delta(
            before=pre_collection["critic_adam_steps"],
            after=post_update["critic_adam_steps"],
            expected_delta=transaction.real_audit.critic_expected_step,
            code=f"TX{transaction_index}_CRITIC_OPTIMIZER_STATE_RESET",
        )

        critic_receipt = transaction.r5_transaction.critic_sequence_receipt
        valid_nonzero = int(critic_receipt.valid_nonzero_count)
        valid_zero = int(critic_receipt.valid_zero_effective_count)
        _require(
            valid_nonzero + valid_zero == len(minibatches)
            and critic_receipt.observed_backward_count == len(minibatches)
            and critic_receipt.observed_step_count == len(minibatches)
            and critic_receipt.observed_valuenorm_count == len(minibatches),
            f"TX{transaction_index}_CRITIC_COUNT_DRIFT",
        )
        actor_receipt = transaction.r5_transaction.actor_sequence_receipt
        actor_step_receipts = tuple(
            step
            for segment in actor_receipt.actor_segments
            for step in segment.step_receipts
        )
        actor_losses = tuple(float(item.loss_value) for item in actor_step_receipts)
        actor_gradient_norms = tuple(
            float(item.aggregate_gradient_norm) for item in actor_step_receipts
        )
        critic_losses = tuple(float(item["critic_loss"]) for item in minibatches)
        critic_gradient_norms = tuple(
            float(item["critic_gradient_norm"]) for item in minibatches
        )
        _require(
            all(
                math.isfinite(value)
                for value in (
                    *actor_losses,
                    *actor_gradient_norms,
                    *critic_losses,
                    *critic_gradient_norms,
                )
            )
            and all(
                bool(post_update[key])
                for key in (
                    "actor_parameters_finite",
                    "actor_optimizer_states_finite",
                    "critic_parameters_finite",
                    "critic_optimizer_state_finite",
                    "valuenorm_state_finite",
                    "gradients_clean",
                )
            ),
            f"TX{transaction_index}_NUMERICAL_HEALTH",
        )
        q = transaction.r5_transaction.quiescence_evidence
        _require(
            transaction.next_rollout_ready
            and q.gradients_clean
            and q.pending_backward_permits == 0
            and q.pending_optimizer_permits == 0
            and q.pending_valuenorm_permits == 0
            and q.unconsumed_terminal_keys == 0
            and q.incomplete_actor_receipts == 0
            and q.incomplete_critic_receipts == 0
            and not q.route_poisoned
            and q.actor_modes_rollout
            and q.critic_mode_rollout
            and q.critic_cursor_reset
            and q.actor_cursors_reset
            and q.event_returns_compute_once_reset
            and q.next_rollout_guards_established,
            f"TX{transaction_index}_S10_QUIESCENCE",
        )
        if bridge is not None:
            bridge["next_s0_established"] = (
                transaction.r5_transaction.ordering_evidence.history[0].value
                == "S0_ROLLOUT_COMPLETE"
            )
            bridge["pass"] = bool(
                bridge["pre_collection_pass"]
                and bridge["post_collection_pass"]
                and bridge["next_s0_established"]
            )
            _atomic_json(
                _artifact_path(artifact_prefix, "continuity_bridges"),
                {
                    "schema_version": "b2_t0_re1_continuity_bridges_v1",
                    "run_identity": run_identity,
                    "source_config_identity_digest": source_config_identity_digest,
                    "bridges": bridges,
                    "bridge_count": len(bridges),
                },
            )

        reward_total = float(
            first.harl_step_result[2].sum().item()
            + second.harl_step_result[2].sum().item()
        )
        transaction_record = {
            **tx_identity,
            "classification": transaction.classification,
            "transaction": transaction,
            "transaction_evidence_digest": transaction.evidence_digest,
            "actor_order": transaction.real_audit.actor_order,
            "actor_plan_digest": json.loads(
                pre_mutation_path.read_text(encoding="utf-8")
            )["actor_plan_digest"],
            "critic_plan_digest": json.loads(
                pre_mutation_path.read_text(encoding="utf-8")
            )["critic_plan_digest"],
            "rollout_evidence_digest": rollout_digest,
            "rollout_provenance": rollout_provenance,
            "rollout_provenance_digest": rollout_provenance_digest,
            "actor_observation_digest": actor_obs_digest,
            "critic_observation_digest": critic_obs_digest,
            "available_action_mask_digest": availability_digest,
            "proposal_action_digest": proposal_digest,
            "behavior_logprob_digest": behavior_digest,
            "dvm_digest": dvm_digest,
            "active_mask_digest": active_mask_digest,
            "critic_mask_digest": critic_mask_digest,
            "transition_identity_digest": transition_identity_digest,
            "lifecycle_decision_gate_receipts": tuple(
                transaction_decision_gate_receipts
            ),
            "terminal_history_keys": history_keys,
            "terminal_reason_counts": {
                "NONE": int(
                    (reason_grid == int(TerminationReason.NONE)).sum().item()
                ),
                "TIME_LIMIT": int(
                    (reason_grid == int(TerminationReason.TIME_LIMIT)).sum().item()
                ),
            },
            "timeout_exact_match": bool(correlation.exact_value_match),
            "pre_collection_learner": pre_collection,
            "post_collection_learner": collection_post,
            "post_update_learner": post_update,
            "actor_losses": actor_losses,
            "actor_gradient_norms": actor_gradient_norms,
            "critic_losses": critic_losses,
            "critic_gradient_norms": critic_gradient_norms,
            "valid_nonzero": valid_nonzero,
            "valid_zero_effective": valid_zero,
            "event_return_compute_count": 1,
            "stock_compute_returns": 0,
            "team_reward_sum_diagnostic_only": reward_total,
            "factor_initial_digest": actor_receipt.initial_factor_digest,
            "factor_final_digest": actor_receipt.final_factor_digest,
            "factor_segment_count": len(segments),
            "s7_pass": True,
            "s8_pass": True,
            "s9_pass": True,
            "s10_pass": True,
            "route_poisoned": False,
            "checkpoint_weight_io": 0,
            "public_route_activations": 0,
            "evaluation_playback": 0,
            "durable_artifacts": {
                name: {
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": _sha(path),
                }
                for name, path in (
                    ("rollout_decision_evidence", rollout_decision_path),
                    ("pre_mutation", pre_mutation_path),
                    ("actor_factor_progress", factor_path),
                    ("critic_progress", critic_path),
                )
            },
        }
        _atomic_json(
            s10_path,
            {
                **transaction_record,
                "schema_version": "b2_t0_re1_transaction_s10_v1",
                "stage": "S10_QUIESCENT",
                "transaction": transaction,
                "quiescence": q,
            },
        )
        transaction_record["durable_artifacts"]["s10"] = {
            "path": str(s10_path),
            "bytes": s10_path.stat().st_size,
            "sha256": _sha(s10_path),
        }
        prior_s10_artifact = transaction_record["durable_artifacts"]["s10"]
        transactions.append(transaction_record)
        resources["completed_transactions"] = transaction_index
        prior_post_state = post_update
        prior_update_id = update_id
        prior_rollout_digest = rollout_digest
        checkpoints.emit(
            f"TX{transaction_index}_S10",
            "b2_t0_transaction_quiescent",
            {
                "update_id": update_id,
                "evidence_digest": transaction.evidence_digest,
                "valid_nonzero": valid_nonzero,
                "valid_zero_effective": valid_zero,
            },
        )

    _require(
        len(transactions) == TRANSACTION_COUNT,
        "TRANSACTION_COUNT",
        len(transactions),
    )
    update_ids = tuple(item["update_id"] for item in transactions)
    _require(
        len(set(update_ids)) == TRANSACTION_COUNT,
        "UPDATE_ID_REUSE",
        update_ids,
    )
    _require(
        len(bridges) == TRANSACTION_COUNT - 1
        and all(bool(item["pass"]) for item in bridges),
        "BRIDGE_COUNT",
        bridges,
    )
    final_learner = _learner_snapshot(
        actors=actors_raw,
        critic=critic_raw,
        live_value_normalizer=live_value_normalizer,
    )
    _require(
        prior_post_state is not None
        and _persistent_state_equal(prior_post_state, final_learner),
        "FINAL_QUIESCENCE_CHANGED_LEARNER",
    )
    _require(
        not route.poisoned
        and not route.collector.consumed_terminal_keys
        and buffer.step == 0
        and not bool(buffer._event_returns_computed)
        and not bool(buffer._event_slot_written.any().item())
        and all(storage.next_action_slot == 0 for storage in route.actor_storages)
        and final_learner["actor_modes_rollout"]
        and final_learner["critic_mode_rollout"]
        and final_learner["gradients_clean"],
        "FINAL_S10_QUIESCENCE",
    )

    count_maps = [
        dict(item["transaction"].exact_execution_counts)
        for item in transactions
    ]
    actor_backward_by_tx = tuple(
        tuple(int(value) for value in counts["actor_backward_by_actor"])
        for counts in count_maps
    )
    actor_step_by_tx = tuple(
        tuple(int(value) for value in counts["actor_optimizer_step_by_actor"])
        for counts in count_maps
    )
    critic_backward_by_tx = tuple(
        int(counts["critic_backward"]) for counts in count_maps
    )
    critic_step_by_tx = tuple(
        int(counts["critic_optimizer_step"]) for counts in count_maps
    )
    valuenorm_by_tx = tuple(
        int(counts["live_valuenorm_update"]) for counts in count_maps
    )
    _require(
        all(int(counts["successful_real_full_learner_transactions"]) == 1 for counts in count_maps)
        and all(int(counts["s10_entries"]) == 1 for counts in count_maps)
        and all(int(counts["training_mode_entries"]) == 1 for counts in count_maps)
        and all(int(counts["rollout_mode_restorations"]) == 1 for counts in count_maps)
        and all(int(counts["critic_rollovers"]) == 1 for counts in count_maps)
        and all(int(counts["terminal_ledger_resets"]) == 1 for counts in count_maps)
        and all(int(counts["actor_storage_rollovers"]) == resolved_M for counts in count_maps),
        "TRANSACTION_LOCAL_S7_S10_COUNT",
        count_maps,
    )
    valid_nonzero_total = sum(int(item["valid_nonzero"]) for item in transactions)
    valid_zero_total = sum(
        int(item["valid_zero_effective"]) for item in transactions
    )
    actor_backward_total = sum(sum(values) for values in actor_backward_by_tx)
    actor_step_total = sum(sum(values) for values in actor_step_by_tx)
    critic_backward_total = sum(critic_backward_by_tx)
    critic_step_total = sum(critic_step_by_tx)
    valuenorm_total = sum(valuenorm_by_tx)
    _require(
        actor_backward_total == actor_step_total
        and critic_backward_total == critic_step_total
        and valid_nonzero_total + valid_zero_total == critic_step_total
        and valuenorm_total == critic_step_total,
        "AGGREGATE_COUNT_DRIFT",
    )

    continuity_table = {
        f"tx{index}_post_to_tx{index + 1}_pre": {
            "pre_collection_receipt_durable": bool(
                bridges[index - 1]["pre_collection_receipt"]["sha256"]
            ),
            "same_actor_objects": (
                transactions[index - 1]["post_update_learner"][
                    "actor_module_ids"
                ]
                == transactions[index]["pre_collection_learner"][
                    "actor_module_ids"
                ]
            ),
            "actor_parameters": (
                transactions[index - 1]["post_update_learner"][
                    "actor_parameter_digests"
                ]
                == transactions[index]["pre_collection_learner"][
                    "actor_parameter_digests"
                ]
            ),
            "actor_optimizer": (
                transactions[index - 1]["post_update_learner"][
                    "actor_optimizer_digests"
                ]
                == transactions[index]["pre_collection_learner"][
                    "actor_optimizer_digests"
                ]
            ),
            "actor_adam": (
                transactions[index - 1]["post_update_learner"]["actor_adam_steps"]
                == transactions[index]["pre_collection_learner"]["actor_adam_steps"]
            ),
            "same_critic_object": (
                transactions[index - 1]["post_update_learner"][
                    "critic_module_id"
                ]
                == transactions[index]["pre_collection_learner"][
                    "critic_module_id"
                ]
            ),
            "critic_parameters": (
                transactions[index - 1]["post_update_learner"][
                    "critic_parameter_digest"
                ]
                == transactions[index]["pre_collection_learner"][
                    "critic_parameter_digest"
                ]
            ),
            "critic_optimizer": (
                transactions[index - 1]["post_update_learner"][
                    "critic_optimizer_digest"
                ]
                == transactions[index]["pre_collection_learner"][
                    "critic_optimizer_digest"
                ]
            ),
            "critic_adam": (
                transactions[index - 1]["post_update_learner"]["critic_adam_steps"]
                == transactions[index]["pre_collection_learner"]["critic_adam_steps"]
            ),
            "same_valuenorm_object": (
                transactions[index - 1]["post_update_learner"][
                    "valuenorm_object_id"
                ]
                == transactions[index]["pre_collection_learner"][
                    "valuenorm_object_id"
                ]
            ),
            "valuenorm": (
                transactions[index - 1]["post_update_learner"][
                    "canonical_valuenorm_digest"
                ]
                == transactions[index]["pre_collection_learner"][
                    "canonical_valuenorm_digest"
                ]
            ),
            "ledger_at_s10_empty": True,
            "permits_at_s10_zero": True,
            "gradients_at_s10_zero": True,
            "actor_cursors_reset": True,
            "critic_buffer_rolled": True,
            "next_rollout_new_evidence": bridges[index - 1][
                "new_rollout_evidence"
            ],
            "lifecycle_decision_gate": all(
                receipt["classification"] == "PASS"
                for receipt in transactions[index][
                    "lifecycle_decision_gate_receipts"
                ]
            ),
            "collection_learner_mutation_zero": bridges[index - 1][
                "collection_preserved_learner"
            ],
            "post_collection_receipt_durable": bool(
                bridges[index - 1]["post_collection_receipt"]["sha256"]
            ),
            "update_id_changed": bridges[index - 1]["update_id_changed"],
            "next_s0_entered": bridges[index - 1]["next_s0_established"],
        }
        for index in (1, 2)
    }
    _require(
        all(
            all(bool(value) for value in row.values())
            for row in continuity_table.values()
        ),
        "CONTINUITY_TABLE",
        continuity_table,
    )

    lifecycle_rows = tuple(
        row
        for receipt in lifecycle_decision_gate_receipts
        for row in receipt["rows"]
    )
    policy_required_rows = sum(
        int(bool(row["decision_required"])) for row in lifecycle_rows
    )
    continuation_rows = sum(
        int(row["decision_reason"] == LD.FORCED_CONTINUATION_ROW)
        for row in lifecycle_rows
    )
    forced_noop_rows = sum(
        int(row["decision_reason"] == LD.FORCED_NOOP_ROW)
        for row in lifecycle_rows
    )
    _require(
        policy_required_rows + continuation_rows + forced_noop_rows
        == len(lifecycle_rows),
        "LIFECYCLE_ROW_COUNT_DRIFT",
    )

    artifact_inventory = {}
    for path in sorted(
        artifact_prefix.parent.glob(f"{artifact_prefix.name}_*.json")
    ):
        artifact_inventory[path.stem.removeprefix(f"{artifact_prefix.name}_")] = {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": _sha(path),
        }
    final = {
        "schema_version": "b2_t0_re1_final_result_v1",
        "status": "passed",
        "classification": PASS,
        "run_identity": run_identity,
        "process_id": os.getpid(),
        "fresh_process": True,
        "historical_route_reused": False,
        "repository_authority": resources["repository_authority"],
        "qualified_source_identity": resources["qualified_source_identity"],
        "source_config_identity_digest": source_config_identity_digest,
        "config": {**runtime_config, "initial_shapes": initial_shapes},
        "persistent_learner_identity": {
            "initial": initial_learner,
            "final": final_learner,
            "object_ids_stable": (
                initial_learner["actor_module_ids"]
                == final_learner["actor_module_ids"]
                and initial_learner["actor_optimizer_ids"]
                == final_learner["actor_optimizer_ids"]
                and initial_learner["critic_module_id"]
                == final_learner["critic_module_id"]
                and initial_learner["critic_optimizer_id"]
                == final_learner["critic_optimizer_id"]
                and initial_learner["valuenorm_object_id"]
                == final_learner["valuenorm_object_id"]
            ),
            "distinct_learner_constructions": 1,
            "private_route_constructions": 1,
            "transaction_local_coordinator_instances": int(
                resources["transaction_coordinator_instances"]
            ),
        },
        "transactions": transactions,
        "bridges": bridges,
        "lifecycle_decision_gate_receipts": tuple(
            lifecycle_decision_gate_receipts
        ),
        "continuity_table": continuity_table,
        "exact_execution_counts": {
            "fresh_process_workers": 1,
            "app_launcher_lifetimes": 1,
            "environment_constructions": 1,
            "environment_resets": 1,
            "distinct_learner_constructions": 1,
            "fresh_rollout_batches": 3,
            "real_rollout_steps": int(resources["real_rollout_steps"]),
            "lifecycle_decision_boundary_receipts": len(
                lifecycle_decision_gate_receipts
            ),
            "lifecycle_decision_row_receipts": len(lifecycle_rows),
            "policy_required_rows": policy_required_rows,
            "continuation_rows": continuation_rows,
            "forced_noop_nondecision_rows": forced_noop_rows,
            "missing_call_faults": 0,
            "duplicate_call_faults": 0,
            "continuation_resample_faults": 0,
            "terminal_autoreset_events": int(
                resources["terminal_autoreset_events"]
            ),
            "successful_full_transactions": len(transactions),
            "distinct_update_ids": len(set(update_ids)),
            "s0_entries": len(transactions),
            "s7_pass": len(transactions),
            "s8_pass": len(transactions),
            "s9_pass": len(transactions),
            "s10_pass": len(transactions),
            "s10_to_next_s0_bridges": len(bridges),
            "bridge_pre_collection_receipts": len(bridges),
            "bridge_post_collection_receipts": len(bridges),
            "event_return_computations": len(transactions),
            "stock_compute_returns": 0,
            "actor_backward_by_transaction": actor_backward_by_tx,
            "actor_optimizer_step_by_transaction": actor_step_by_tx,
            "actor_backward_total": actor_backward_total,
            "actor_optimizer_step_total": actor_step_total,
            "critic_backward_by_transaction": critic_backward_by_tx,
            "critic_optimizer_step_by_transaction": critic_step_by_tx,
            "critic_backward_total": critic_backward_total,
            "critic_optimizer_step_total": critic_step_total,
            "valid_nonzero_update": valid_nonzero_total,
            "valid_zero_effective_update": valid_zero_total,
            "valuenorm_update_by_transaction": valuenorm_by_tx,
            "valuenorm_update_total": valuenorm_total,
            "critic_rollovers": 3,
            "ledger_reset_invocations": 3,
            "actor_rollovers": 3 * resolved_M,
            "transaction_4_started": 0,
            "checkpoint_weight_io": 0,
            "public_route_activation": 0,
            "evaluation_playback": 0,
            "long_training_transactions": 0,
        },
        "final_read_only_quiescence_check": {
            "pass": True,
            "route_unpoisoned": not route.poisoned,
            "ledger_empty": not bool(route.collector.consumed_terminal_keys),
            "critic_cursor_reset": buffer.step == 0,
            "actor_cursors_reset": all(
                storage.next_action_slot == 0 for storage in route.actor_storages
            ),
            "event_return_compute_once_reset": not bool(
                buffer._event_returns_computed
            ),
            "gradients_clean": final_learner["gradients_clean"],
            "models_in_rollout_mode": (
                final_learner["actor_modes_rollout"]
                and final_learner["critic_mode_rollout"]
            ),
        },
        "artifact_inventory": artifact_inventory,
        "public_route": "DORMANT / BLOCKED",
        "checkpoint_weight_io": 0,
        "evaluation_playback": 0,
        "long_training": "NOT AUTHORIZED",
        "transaction_4_started": False,
    }
    _atomic_json(_artifact_path(artifact_prefix, "final_result"), final)
    return final


def _failure_slug(error: BaseException) -> str:
    message = str(error).upper()
    for candidate in (
        "QUALIFIED-SOURCE-DRIFT",
        "LEARNER-STATE-REINITIALIZATION",
        "OPTIMIZER-STATE-RESET",
        "COLLECTION-MUTATED-LEARNER",
        "STALE-TERMINAL-KEY",
        "ROLLOUT-EVIDENCE-REUSE",
        "S10-QUIESCENCE",
        "NUMERICAL-HEALTH",
    ):
        if candidate.replace("-", "_") in message or candidate in message:
            return candidate
    return "BOUNDED-SMOKE-FAILURE"


def run_worker(args: argparse.Namespace) -> int:
    result_path = Path(args.result_file).resolve()
    artifact_prefix = Path(args.artifact_prefix).resolve()
    checkpoints = V2.Checkpoints(Path(args.checkpoint_file).resolve())
    simulation_app = None
    resources: dict[str, object] = {}
    result: dict[str, object] = {
        "status": "failed",
        "classification": "PHASE-B2-T0-RE1-STOP-TX1-STARTUP-NOT-COMPLETE",
    }
    try:
        existing = tuple(
            artifact_prefix.parent.glob(f"{artifact_prefix.name}_*.json")
        )
        _require(not existing, "DIAGNOSTIC_ARTIFACT_ALREADY_EXISTS", existing)
        # The supervisor already ran the canonical static guard.  Re-running it
        # in the worker would install the pure-test package placeholders before
        # AppLauncher and shadow the real task package used by Gym registration.
        sources = _source_identity()
        repository = SINGLE._repository_authority()
        _require(
            bool(sources["pass"])
            and repository["head"] == EXPECTED_HEAD
            and repository["head_origin_merge_base_equal"]
            and repository["staged_path_count"] == 359
            and repository["staged_index_sha256"]
            == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
            "QUALIFIED-SOURCE-DRIFT",
            {"sources": sources, "repository": repository},
        )
        resources["repository_authority"] = repository
        resources["qualified_source_identity"] = sources
        _atomic_json(
            _artifact_path(artifact_prefix, "process_config_authority"),
            {
                "schema_version": "b2_t0_re1_pre_app_process_authority_v1",
                "process_id": os.getpid(),
                "fresh_process": True,
                "repository_authority": resources["repository_authority"],
                "qualified_source_identity": resources[
                    "qualified_source_identity"
                ],
                "app_launcher_lifetimes": 0,
                "environment_constructions": 0,
                "distinct_learner_constructions": 0,
            },
        )
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        device = V2._warm_start_torch_cuda(DEVICE, checkpoints)
        _require(device is not None and str(device) == DEVICE, "CUDA_WARMUP")
        launcher = AppLauncher(
            headless=True,
            device=DEVICE,
            enable_cameras=False,
            livestream=0,
            xr=False,
            experience="",
        )
        simulation_app = launcher.app
        evidence = _run_repeated_smoke(
            checkpoints,
            resources,
            artifact_prefix=artifact_prefix,
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
        completed_transactions = int(resources.get("completed_transactions", 0))
        failing_transaction = int(
            resources.get(
                "active_transaction",
                min(completed_transactions + 1, TRANSACTION_COUNT),
            )
        )
        failure_artifact = _artifact_path(
            artifact_prefix, f"tx{failing_transaction}_failure"
        )
        failure_payload: dict[str, object] = {}
        if failure_artifact.is_file():
            failure_payload = json.loads(
                failure_artifact.read_text(encoding="utf-8")
            )
        partial_update = bool(
            completed_transactions > 0
            or resources.get("adapter_transaction_returned", False)
            or failure_payload.get("partial_update", False)
        )
        route = resources.get("route")
        if partial_update and route is not None:
            route._poisoned = True
        slug = _failure_slug(exc)
        result = {
            "schema_version": "b2_t0_re1_failure_result_v1",
            "status": "failed",
            "classification": (
                f"PHASE-B2-T0-RE1-STOP-TX{failing_transaction}-{slug}-NOT-COMPLETE"
            ),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "successful_transactions_before_failure": completed_transactions,
            "failing_transaction": failing_transaction,
            "mutation_had_begun": partial_update,
            "partial_update": partial_update,
            "route_poisoned": bool(
                partial_update or failure_payload.get("route_poisoned", False)
            ),
            "last_completed_s_state": (
                "S10_QUIESCENT" if completed_transactions else "PRE_S10"
            ),
            "bridge_failed": completed_transactions in (1, 2),
            "retry_performed": False,
            "failure_receipt": failure_payload,
            "authoritative_attempts": 1,
            "worker_count": 1,
            "app_launcher_lifetimes": int(simulation_app is not None),
            "process_id": os.getpid(),
        }
        _atomic_json(_artifact_path(artifact_prefix, "final_result"), result)
    result["process_id"] = os.getpid()
    result["real_runtime_counts"] = {
        key: int(resources.get(key, 0))
        for key in (
            "environment_constructions",
            "real_resets",
            "real_rollout_steps",
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


def run_supervisor(args: argparse.Namespace) -> int:
    static = run_static()
    if not static["pass"]:
        result = {
            "status": "failed",
            "classification": (
                "PHASE-B2-T0-RE1-STOP-TX1-QUALIFIED-SOURCE-DRIFT-NOT-COMPLETE"
            ),
            "static": static,
            "formal_supervisor_attempts": 1,
            "formal_workers": 0,
            "retry_count": 0,
        }
        if args.json_output:
            _atomic_json(Path(args.json_output), result)
        print(json.dumps(V2.normalize(result), indent=2, sort_keys=True))
        return 2
    with tempfile.TemporaryDirectory(prefix="b2_t0_re1_repeated_smoke_") as directory:
        temp = Path(directory)
        primary = temp / "primary.json"
        checkpoints = temp / "diagnostic_checkpoints.json"
        command = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--worker",
            "--result-file",
            str(primary),
            "--checkpoint-file",
            str(checkpoints),
            "--artifact-prefix",
            str(Path(args.artifact_prefix).resolve()),
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
                "status": (
                    "passed"
                    if valid
                    and worker.get("status") == "passed"
                    and completed.returncode == 0
                    else "failed"
                ),
                "classification": worker.get(
                    "classification",
                    "PHASE-B2-T0-RE1-STOP-TX1-WORKER-RESULT-NOT-COMPLETE",
                ),
                "static": static,
                "formal_supervisor_attempts": 1,
                "formal_workers": 1,
                "app_launcher_lifetimes": worker.get(
                    "app_launcher_lifetimes", 0
                ),
                "retry_count": 0,
                "worker_exit_code": completed.returncode,
                "worker_result_valid": valid,
                "worker_checkpoints": V2._read_json(checkpoints)[1],
                "worker": worker,
                "worker_stdout_tail": completed.stdout[-16000:],
                "worker_stderr_tail": completed.stderr[-16000:],
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "status": "failed",
                "classification": (
                    "PHASE-B2-T0-RE1-STOP-TX1-TIMEOUT-NOT-COMPLETE"
                ),
                "static": static,
                "formal_supervisor_attempts": 1,
                "formal_workers": 1,
                "retry_count": 0,
                "timeout_seconds": args.timeout_seconds,
                "stdout_tail": (exc.stdout or "")[-16000:],
                "stderr_tail": (exc.stderr or "")[-16000:],
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
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--json-output")
    parser.add_argument(
        "--artifact-prefix",
        default=str(
            Path(tempfile.gettempdir())
            / "b2_t0_re1_repeated_smoke_20260910_formal01"
        ),
    )
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
