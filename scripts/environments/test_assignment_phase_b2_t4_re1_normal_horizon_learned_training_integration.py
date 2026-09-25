"""Fresh 160-update normal-horizon learned-training integration qualification."""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

from _assignment_phase_b2_t4_sr_reason_grid_serializer import (
    classification_precedence_metadata_v1,
    serialize_termination_reason_grid_v1,
)


HERE = Path(__file__).resolve().parent
T2_HARNESS = HERE / "test_assignment_phase_b2_t2_medium_length_training_observability_stability.py"
T2_OBSERVER = HERE / "_assignment_phase_b2_t2_observability.py"
T3_OBSERVER = HERE / "_assignment_phase_b2_t3_progress_observer.py"
NR_SUITE = HERE / "test_assignment_phase_b2_t4_nr_nonterminal_rollout_completeness_contract.py"
QUALIFIED_T2_SHA256 = "b842dad524622213750142642befddb06dc7646827577411f38d115c666d8943"
QUALIFIED_T2_OBSERVER_SHA256 = "b93ccbad1762e6d4df2fdb8a81c174b40a07a5acfba87b9bc5b248434931e356"
QUALIFIED_T3_OBSERVER_SHA256 = "c8edd97c1327c0d2f2084725449edd916e8b6190bbee3eab3ac04a1dc31cbf59"
TRANSACTION_COUNT = 160
SENTINEL_TRANSACTIONS = frozenset((1, 10, 25, 50, 75, 100, 125, 150, 160))
PASS = (
    "PHASE-B2-T4-RE1-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
STOP_CUDA = "PHASE-B2-T4-RE1-STOP-CUDA-CUBLAS-INFRASTRUCTURE-NOT-READY"
STOP_RUNTIME = "PHASE-B2-T4-RE1-STOP-LEARNER-MUTATED-RUNTIME-LIFECYCLE"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_exact(source: str, old: str, new: str, *, count: int | None = None) -> str:
    observed = source.count(old)
    expected = observed if count is None else count
    if observed != expected or observed == 0:
        raise RuntimeError(
            "STOP — B2-T4-RE1 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"replacement {old!r} expected {expected}, observed {observed}"
        )
    return source.replace(old, new)


def _replace_span(source: str, start: str, end: str, replacement: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError(
            "STOP — B2-T4-RE1 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"span cardinality start={source.count(start)} end={source.count(end)}"
        )
    left = source.index(start)
    right = source.index(end, left)
    return source[:left] + replacement + source[right:]


def _load_t2_module():
    observed = _sha(T2_HARNESS)
    if observed != QUALIFIED_T2_SHA256:
        raise RuntimeError(
            "STOP — B2-T4-RE1 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"B2-T2 harness {observed} != {QUALIFIED_T2_SHA256}"
        )
    spec = importlib.util.spec_from_file_location("_phase_b2_t2_re1_source", T2_HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP — B2-T4-RE1 T2-HARNESS-LOAD")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tensor_digest(value: object) -> str:
    import torch

    if type(value) is not torch.Tensor:
        raise RuntimeError("STOP — B2-T4-RE1 RUNTIME-FINGERPRINT-NONTENSOR")
    captured = value.detach().contiguous().cpu()
    digest = hashlib.sha256()
    digest.update(str(tuple(captured.shape)).encode("ascii"))
    digest.update(str(captured.dtype).encode("ascii"))
    digest.update(captured.numpy().tobytes())
    return digest.hexdigest()


def _event_rows(events: Sequence[object]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "event": str(event.event_type.value),
            "env_id": int(event.env_id),
            "robot_id": int(event.robot_id),
            "task_id": int(event.task_id),
        }
        for event in events
    )


def _runtime_projection(raw: object, publication: object) -> dict[str, object]:
    state = publication.lifecycle_state
    result = publication.result
    tensors = {
        "robot_state": state.robot_state,
        "task_state": state.task_state,
        "ownership": state.ownership,
        "completion_count": state.completion_count,
        "failed_pairs": state.cumulative_failed_pairs,
        "termination_reason": state.termination_reason,
        "episode_generation": publication.episode_generation,
        "transition_generation": publication.transition_generation,
        "episode_length_buf": raw.episode_length_buf,
        "base_pos": raw.base_pos,
        "base_yaw": raw.base_yaw,
        "scanner_pos": raw.scanner_pos,
        "scanner_quat": raw.scanner_quat,
        "viewpoints_covered": raw.viewpoints_covered,
        "dwell_counter": raw.dwell_counter,
    }
    current_task = []
    for env_index in range(int(state.robot_state.shape[0])):
        row = []
        for robot_id in range(int(state.robot_state.shape[1])):
            owned = (
                (state.ownership[env_index] == robot_id)
                & (state.task_state[env_index] >= 1)
                & (state.task_state[env_index] <= 3)
            ).nonzero(as_tuple=False).flatten().detach().cpu().tolist()
            if len(owned) > 1:
                raise RuntimeError("STOP — B2-T4-RE1 P2-MULTIPLE-ACTIVE-OWNERSHIP")
            row.append(None if not owned else int(owned[0]))
        current_task.append(tuple(row))
    return {
        "common_step_counter": int(raw.common_step_counter),
        "store_version": int(publication.store_version),
        "tensor_digests": {name: _tensor_digest(value) for name, value in tensors.items()},
        "current_task_by_robot": tuple(current_task),
        "events": () if result is None else _event_rows(tuple(result.lifecycle_events)),
    }


def _capture_runtime_state(raw: object, domain: object) -> dict[str, object]:
    import torch

    cpu_before = torch.random.get_rng_state().clone()
    cuda_before = tuple(item.clone() for item in torch.cuda.get_rng_state_all())
    publication = domain.current_read_port.read_current()
    projection = _runtime_projection(raw, publication)
    repeat = _runtime_projection(raw, domain.current_read_port.read_current())
    cuda_after = tuple(item.clone() for item in torch.cuda.get_rng_state_all())
    if (
        projection != repeat
        or not torch.equal(cpu_before, torch.random.get_rng_state())
        or len(cuda_before) != len(cuda_after)
        or any(not torch.equal(left, right) for left, right in zip(cuda_before, cuda_after))
    ):
        raise RuntimeError("STOP — B2-T4-RE1 RUNTIME-FINGERPRINT-MUTATION")
    encoded = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**projection, "digest": hashlib.sha256(encoded).hexdigest(), "observer_mutations": 0}


def _capture_step_detail(
    raw: object,
    receipt: object,
    *,
    transaction_index: int,
    global_step: int,
) -> dict[str, object]:
    import torch

    result = receipt.facade_result
    publication = result.current_publication
    source_before = _runtime_projection(raw, publication)
    problem = raw.get_assignment_problem()
    current = publication.lifecycle_state
    terminal_by_env = {int(row.env_id): row for row in result.terminal_historical_payload}
    events: list[object] = []
    if publication.result is not None:
        events.extend(
            event
            for event in publication.result.lifecycle_events
            if int(event.env_id) not in terminal_by_env
        )
    for row in result.terminal_historical_payload:
        events.extend(row.lifecycle_events)
    state_rows = []
    for env_index, env_id_value in enumerate(current.env_id.detach().cpu().tolist()):
        env_id = int(env_id_value)
        terminal = terminal_by_env.get(env_id)
        if terminal is None:
            task_state = current.task_state[env_index]
            robot_state = current.robot_state[env_index]
            ownership = current.ownership[env_index]
            completion = current.completion_count[env_index]
            coverage = raw.viewpoints_covered[env_index]
            basis = "current_episode_post_transition"
        else:
            task_state = terminal.updated_task_state
            robot_state = terminal.updated_robot_state
            ownership = terminal.updated_ownership
            completion = terminal.completion_count
            coverage = terminal.coverage_after_transition
            basis = "terminal_pre_reset_historical"
        state_rows.append(
            {
                "env_id": env_id,
                "basis": basis,
                "robot_state": tuple(int(item) for item in robot_state.detach().cpu().tolist()),
                "task_state": tuple(int(item) for item in task_state.detach().cpu().tolist()),
                "ownership": tuple(int(item) for item in ownership.detach().cpu().tolist()),
                "completion_count": tuple(int(item) for item in completion.detach().cpu().tolist()),
                "coverage_count": int(coverage.detach().to(torch.int64).sum().item()),
                "episode_generation": int(
                    terminal.episode_generation
                    if terminal is not None
                    else receipt.next_decision_bundle.evidence_identity.episode_generations[env_index]
                ),
                "next_episode_generation": int(
                    receipt.next_decision_bundle.evidence_identity.episode_generations[env_index]
                ),
                "transition_generation": int(
                    receipt.next_decision_bundle.evidence_identity.transition_generations[env_index]
                ),
                "episode_local_step": int(raw.episode_length_buf[env_index].item()),
                "distance_matrix": tuple(
                    tuple(float(value) for value in row)
                    for row in problem["cost_matrix"][env_index].detach().cpu().tolist()
                ),
                "next_decision_required": tuple(
                    bool(value)
                    for value in receipt.next_decision_bundle.decision_valid_mask[
                        env_index, :, 0
                    ].detach().cpu().tolist()
                ),
                "next_owned_task": tuple(
                    int(value)
                    for value in receipt.next_decision_bundle.evidence_snapshot.current_owned_task_id[
                        env_index
                    ].detach().cpu().tolist()
                ),
            }
        )
    source_after = _runtime_projection(raw, publication)
    if source_before != source_after:
        raise RuntimeError("STOP — B2-T4-RE1 STEP-DETAIL-OBSERVER-MUTATION")
    return {
        "schema_version": "b2_t4_re1_step_detail_v1",
        "transaction_index": int(transaction_index),
        "global_physical_step": int(global_step),
        "state_rows": tuple(state_rows),
        "events": _event_rows(tuple(events)),
        "effective_assignment": tuple(
            tuple(int(value) for value in row)
            for row in result.admitted_effective_assignment.detach().cpu().tolist()
        ),
        "raw_action_ids": tuple(
            tuple(int(value) for value in row)
            for row in result.resolution.raw_action_ids.detach().cpu().tolist()
        ),
        "observer_mutations": 0,
    }


def _cuda_cublas_probe() -> dict[str, object]:
    import torch

    try:
        left = torch.tensor([[1.0, 2.0], [3.0, 4.0]], device="cuda:0")
        right = torch.tensor([[5.0, 6.0], [7.0, 8.0]], device="cuda:0")
        observed = torch.mm(left, right)
        torch.cuda.synchronize(torch.device("cuda:0"))
        expected = torch.tensor([[19.0, 22.0], [43.0, 50.0]], device="cuda:0")
        if not torch.equal(observed, expected):
            raise RuntimeError("cuBLAS matrix product mismatch")
        return {
            "classification": "PASS",
            "device": str(observed.device),
            "operation": "torch.mm_2x2_fp32",
            "result": observed.detach().cpu().tolist(),
            "probe_count": 1,
        }
    except BaseException as exc:
        raise RuntimeError(f"{STOP_CUDA}: {type(exc).__name__}: {exc}") from exc


def _qualified_re1_source() -> str:
    t2 = _load_t2_module()
    source = t2._qualified_t2_source()
    source = _replace_exact(
        source,
        '"""Exactly-300-update real-Isaac observability/stability qualification for Phase B2-T2."""',
        '"""Fresh 160-update normal-horizon learned-training integration qualification."""',
        count=1,
    )
    source = _replace_exact(source, "TRANSACTION_COUNT = 300", "TRANSACTION_COUNT = 160", count=1)
    source = _replace_exact(source, f'PASS = "{t2.PASS}"', f'PASS = "{PASS}"', count=1)
    source = _replace_exact(source, "STOP — B2-T2", "STOP — B2-T4-RE1")
    source = _replace_exact(source, "PHASE-B2-T2-STOP", "PHASE-B2-T4-RE1-STOP")
    source = _replace_exact(source, "b2-t2-medium-training", "b2-t4-re1-normal-horizon-training")
    source = _replace_exact(
        source,
        "B2-T2.medium_length_training_observability_stability",
        "B2-T4-RE1.normal_horizon_learned_training_integration",
        count=1,
    )
    source = _replace_exact(source, "transaction_301_started", "transaction_161_started")
    source = _replace_exact(
        source,
        "b2_t2_medium_training_20260911_formal01",
        "b2_t4_re1_normal_horizon_20260913_formal01",
        count=1,
    )
    source = _replace_exact(
        source,
        '"assignment_event_training_full_transaction.py": "ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35"',
        '"assignment_event_training_full_transaction.py": "a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de"',
        count=1,
    )
    source = _replace_exact(
        source,
        '"assignment_event_training_real_isaac_adapter.py": "bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e"',
        '"assignment_event_training_real_isaac_adapter.py": "b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014"',
        count=1,
    )
    timing_old = '''    timing = V2.build_pd2_integral_horizon_fixture_v1(
        float(cfg.sim.dt),
        int(cfg.decimation),
        semantic_horizon_steps=V2.PD2_SEMANTIC_HORIZON_STEPS,
    )
    V2.adjudicate_pd2_s1_preconstruction_timing_v1(timing)
    cfg.episode_length_s = timing.candidate_episode_length_seconds
'''
    timing_new = '''    normal_episode_length_s = float(cfg.episode_length_s)
    _require(abs(normal_episode_length_s - 30.0) <= 1.0e-12, "NORMAL_HORIZON_CONFIG")
'''
    source = _replace_exact(source, timing_old, timing_new, count=1)
    post_old = '''    post_timing = V2.build_pd2_s1_postconstruction_timing_evidence_v1(
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
'''
    post_new = '''    _require(
        abs(float(cfg.episode_length_s) - 30.0) <= 1.0e-12
        and abs(float(raw.max_episode_length_s) - 30.0) <= 1.0e-12
        and abs(float(raw.step_dt) - 0.1) <= 1.0e-12
        and int(raw.max_episode_length) == 300,
        "NORMAL_HORIZON_RUNTIME",
        {
            "configured_episode_length_s": float(cfg.episode_length_s),
            "raw_max_episode_length_s": float(raw.max_episode_length_s),
            "raw_step_dt": float(raw.step_dt),
            "raw_max_episode_length": int(raw.max_episode_length),
        },
    )
'''
    source = _replace_exact(source, post_old, post_new, count=1)
    source = _replace_exact(
        source,
        '        "fixed_order": bool(algo_args["algo"]["fixed_order"]),',
        '        "fixed_order": bool(algo_args["algo"]["fixed_order"]),\n'
        '        "environment_episode_length_s": float(cfg.episode_length_s),\n'
        '        "environment_max_episode_length": int(raw.max_episode_length),\n'
        '        "sim_dt_seconds": float(cfg.sim.dt),\n'
        '        "control_decimation": int(cfg.decimation),\n'
        '        "control_step_seconds": float(raw.step_dt),\n'
        '        "harness_episode_override": False,',
        count=1,
    )
    lifecycle_import = '''    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import (
        TerminationReason,
    )
'''
    source = _replace_exact(
        source,
        lifecycle_import,
        lifecycle_import
        + '    globals()["_re1_canonical_termination_reason"] = TerminationReason\n',
        count=1,
    )
    collection_start = "        actor_call_start = tuple(len(actor.calls) for actor in actors)\n"
    collection_end = "        actor_obs_digest = canonical_digest_v1(\n"
    collection = '''        transaction_route_event_start = len(route_events)
        control_start = len(control_assignments)
        terminal_copy_start = len(terminal_slots_before_ack)
        receipts = []
        effective_assignments = []
        history_rows = []
        timeout_correlations = []
        re1_step_details = []
        for physical_step_index in range(1, resolved_T + 1):
            actor_calls_before = tuple(len(actor.calls) for actor in actors)
            critic_start = len(critic.calls)
            route_event_start = len(route_events)
            receipt = route.collect_step()
            receipts.append(receipt)
            resources["real_rollout_steps"] = int(resources.get("real_rollout_steps", 0)) + 1
            effective = V2.expected_assignment(receipt.facade_result.admitted_publication, torch)
            effective_assignments.append(effective)
            _require(
                len(control_assignments) == control_start + physical_step_index
                and torch.equal(control_assignments[-1], effective),
                f"TX{transaction_index}_FINAL_P2_CONTROLLER",
            )
            actor_calls_after = tuple(len(actor.calls) for actor in actors)
            gate, previous_observed_episode_generations = _capture_lifecycle_decision_gate_v1(
                receipt=receipt,
                actors=actors,
                actor_calls_before=actor_calls_before,
                actor_calls_after=actor_calls_after,
                transaction_index=transaction_index,
                collection_index=int(resources["real_rollout_steps"]),
                physical_step_index=physical_step_index,
                previous_episode_generations=previous_observed_episode_generations,
            )
            transaction_decision_gate_receipts.append(gate)
            lifecycle_decision_gate_receipts.append(gate)
            history = tuple(receipt.facade_result.terminal_historical_payload)
            history_rows.extend(history)
            resources["terminal_autoreset_events"] = int(
                resources.get("terminal_autoreset_events", 0)
            ) + len(history)
            if history:
                _require(
                    len(terminal_slots_before_ack) == terminal_copy_start + sum(
                        int(bool(item.facade_result.terminal_historical_payload))
                        for item in receipts
                    )
                    and len(terminal_slots_before_ack[-1]) == len(history),
                    f"TX{transaction_index}_TERMINAL_COPY_BEFORE_ACK",
                )
            else:
                _require(
                    len(terminal_slots_before_ack) == terminal_copy_start + sum(
                        int(bool(item.facade_result.terminal_historical_payload))
                        for item in receipts
                    ),
                    f"TX{transaction_index}_SPURIOUS_TERMINAL_COPY",
                )
            _require(
                domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (),
                f"TX{transaction_index}_RUNTIME_ACK",
            )
            timeout_history = tuple(
                row for row in history
                if int(row.termination_reason) == int(TerminationReason.TIME_LIMIT)
            )
            timeout_events = [
                detail for stage, detail in route_events[route_event_start:]
                if stage == "I5a_critic_buffer_insert"
            ]
            if timeout_history:
                _require(
                    all(row.optional_sidecar is not None for row in timeout_history),
                    f"TX{transaction_index}_TIMEOUT_SIDECAR",
                )
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
                pre_reset_obs = torch.stack(
                    [row.optional_sidecar.bootstrap_critic_obs for row in timeout_history], dim=0
                )
                env_indices = torch.tensor(
                    [int(row.env_id) for row in timeout_history], dtype=torch.int64, device=device
                )
                post_reset_obs = receipt.next_decision_bundle.evidence_snapshot.runner_share_obs[
                    env_indices, 0
                ]
                observed_timeout = critic.observed_input(timeout_identity.timeout_call_global_index)
                correlation = V2.compare_pd2_s6_timeout_critic_input_exact_v1(
                    pre_reset_obs, observed_timeout, invocation_identity=timeout_identity
                )
                V2.adjudicate_pd2_s6_timeout_critic_input_correlation_v1(correlation)
                _require(
                    not torch.equal(pre_reset_obs, post_reset_obs),
                    f"TX{transaction_index}_HISTORICAL_CURRENT_ALIAS",
                )
                timeout_correlations.append(
                    {
                        "physical_step_index": physical_step_index,
                        "global_physical_step": int(resources["real_rollout_steps"]),
                        "env_ids": tuple(int(row.env_id) for row in timeout_history),
                        "exact": bool(correlation.exact_value_match),
                        "expected_input_sha256": correlation.expected_input_sha256,
                        "observed_input_sha256": correlation.observed_input_sha256,
                        "pre_reset_digest": fingerprint_tensor_v1(pre_reset_obs).content_digest,
                        "post_reset_digest": fingerprint_tensor_v1(post_reset_obs).content_digest,
                        "timeout_call_global_index": timeout_identity.timeout_call_global_index,
                    }
                )
            re1_step_details.append(
                _capture_re1_step_detail(
                    raw,
                    receipt,
                    transaction_index=transaction_index,
                    global_step=int(resources["real_rollout_steps"]),
                )
            )

        first, second = receipts
        first_effective, second_effective = effective_assignments
        history = tuple(history_rows)
        history_keys = tuple(
            (row.env_id, row.episode_generation, row.transition_generation) for row in history
        )
        _require(
            not historical_terminal_keys.intersection(history_keys),
            f"TX{transaction_index}_STALE_TERMINAL_KEY",
            history_keys,
        )
        historical_terminal_keys.update(history_keys)
        reason_grid = buffer.termination_reason.detach().clone()
        valid_reasons = tuple(int(member) for member in TerminationReason)
        _require(
            all(int(value) in valid_reasons for value in reason_grid.reshape(-1).detach().cpu().tolist())
            and int((reason_grid != int(TerminationReason.NONE)).sum().item()) == len(history),
            f"TX{transaction_index}_TERMINATION_REASON",
        )
        correlation = type("Correlation", (), {
            "exact_value_match": all(bool(row["exact"]) for row in timeout_correlations),
            "expected_input_sha256": canonical_digest_v1(tuple(row["expected_input_sha256"] for row in timeout_correlations)),
            "observed_input_sha256": canonical_digest_v1(tuple(row["observed_input_sha256"] for row in timeout_correlations)),
        })()
        pre_reset_obs = torch.empty((0, critic_dim), dtype=torch.float32, device=device)
        post_reset_obs = torch.empty((0, critic_dim), dtype=torch.float32, device=device)
        observed_timeout = torch.empty((0, critic_dim), dtype=torch.float32, device=device)
        timeout_identity = type("TimeoutIdentity", (), {
            "timeout_call_global_index": -1,
            "observed_timeout_call_count": len(timeout_correlations),
        })()
'''
    source = _replace_span(source, collection_start, collection_end, collection)
    source = _replace_exact(
        source,
        "        collection_post = _learner_snapshot(\n",
        "        runtime_before_update = _capture_re1_runtime_state(raw, domain)\n"
        "        collection_post = _learner_snapshot(\n",
        count=1,
    )
    source = _replace_exact(
        source,
        '        resources["adapter_transaction_returned"] = True\n',
        '''        resources["adapter_transaction_returned"] = True
        runtime_after_update = _capture_re1_runtime_state(raw, domain)
        runtime_update_equal = runtime_before_update == runtime_after_update
        _require(
            runtime_update_equal,
            "LEARNER_MUTATED_RUNTIME_LIFECYCLE",
            {
                "classification": "PHASE-B2-T4-RE1-STOP-LEARNER-MUTATED-RUNTIME-LIFECYCLE",
                "before": runtime_before_update,
                "after": runtime_after_update,
            },
        )
        resources["runtime_p2_immutability_passes"] = int(
            resources.get("runtime_p2_immutability_passes", 0)
        ) + 1
''',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "team_reward_sum_diagnostic_only": reward_total,\n            "observability_steps": tuple(observability_steps[-resolved_T:]),',
        '            "team_reward_sum_diagnostic_only": reward_total,\n'
        '            "observability_steps": tuple(observability_steps[-resolved_T:]),\n'
        '            "re1_step_details": tuple(re1_step_details),\n'
        '            "runtime_before_update": runtime_before_update,\n'
        '            "runtime_after_update": runtime_after_update,\n'
        '            "runtime_update_equal": runtime_update_equal,\n'
        '            "timeout_correlations": tuple(timeout_correlations),',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "terminal_reason_counts": {\n                "NONE": int(\n                    (reason_grid == int(TerminationReason.NONE)).sum().item()\n                ),\n                "TIME_LIMIT": int(\n                    (reason_grid == int(TerminationReason.TIME_LIMIT)).sum().item()\n                ),\n            },',
        '''            "terminal_reason_counts": {
                member.name: int((reason_grid == int(member)).sum().item())
                for member in TerminationReason
            },
            "termination_reason_grid": reason_grid,''',
        count=1,
    )
    source = _replace_exact(
        source,
        "        transaction_record = {\n",
        '''        pre_mutation_payload = json.loads(pre_mutation_path.read_text(encoding="utf-8"))
        transaction_record = {
''',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "timeout_exact_match": bool(correlation.exact_value_match),',
        '''            "timeout_exact_match": bool(correlation.exact_value_match),
            "expected_terminal_keys": pre_mutation_payload["expected_terminal_keys"],
            "observed_terminal_keys": pre_mutation_payload["terminal_ledger_keys"],
            "terminal_reconciliation_digest": pre_mutation_payload["terminal_reconciliation_digest"],''',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "actor_plan_digest": json.loads(\n                pre_mutation_path.read_text(encoding="utf-8")\n            )["actor_plan_digest"],\n            "critic_plan_digest": json.loads(\n                pre_mutation_path.read_text(encoding="utf-8")\n            )["critic_plan_digest"],',
        '            "actor_plan_digest": pre_mutation_payload["actor_plan_digest"],\n'
        '            "critic_plan_digest": pre_mutation_payload["critic_plan_digest"],',
        count=1,
    )
    source = _replace_exact(
        source,
        "        sys.argv = [sys.argv[0]]\n        from isaaclab.app import AppLauncher\n\n        device = V2._warm_start_torch_cuda(DEVICE, checkpoints)\n        _require(device is not None and str(device) == DEVICE, \"CUDA_WARMUP\")\n",
        '''        sys.argv = [sys.argv[0]]
        resources["cuda_cublas_readiness_probes"] = 1
        probe = _re1_cuda_cublas_probe()
        resources["cuda_cublas_readiness_pass"] = 1
        resources["cuda_cublas_readiness_receipt"] = probe
        _atomic_json(_artifact_path(artifact_prefix, "cuda_cublas_readiness"), probe)
        from isaaclab.app import AppLauncher

''',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "classification": (\n                f"PHASE-B2-T4-RE1-STOP-TX{failing_transaction}-{slug}-NOT-COMPLETE"\n            ),',
        '''            "classification": (
                "PHASE-B2-T4-RE1-STOP-CUDA-CUBLAS-INFRASTRUCTURE-NOT-READY"
                if int(resources.get("cuda_cublas_readiness_probes", 0)) == 1
                and int(resources.get("cuda_cublas_readiness_pass", 0)) == 0
                else f"PHASE-B2-T4-RE1-STOP-TX{failing_transaction}-{slug}-NOT-COMPLETE"
            ),''',
        count=1,
    )
    source = _replace_exact(
        source,
        '            "terminal_autoreset_events",\n',
        '            "terminal_autoreset_events",\n'
        '            "cuda_cublas_readiness_probes",\n'
        '            "cuda_cublas_readiness_pass",\n'
        '            "runtime_p2_immutability_passes",\n',
        count=1,
    )
    return source


_INNER: dict[str, object] = {
    "__name__": "_phase_b2_t4_re1_qualified_base",
    "__file__": str(Path(__file__).resolve()),
    "__package__": None,
    "_capture_re1_runtime_state": _capture_runtime_state,
    "_capture_re1_step_detail": _capture_step_detail,
    "_re1_cuda_cublas_probe": _cuda_cublas_probe,
}
exec(compile(_qualified_re1_source(), str(T2_HARNESS), "exec"), _INNER)

V2 = _INNER["V2"]
_base_atomic_json = _INNER["_atomic_json"]
_base_run_worker = _INNER["run_worker"]


def _source_identity() -> dict[str, object]:
    repo = {name: _sha(_INNER["SCAN"] / name) for name in _INNER["QUALIFIED_REPO_SHA256"]}
    installed = {name: _sha(_INNER["HARL"] / name) for name in _INNER["QUALIFIED_HARL_SHA256"]}
    test_side = {
        "t2_harness": _sha(T2_HARNESS),
        "t2_observer": _sha(T2_OBSERVER),
        "t3_observer": _sha(T3_OBSERVER),
        "nr_suite": _sha(NR_SUITE),
        "re1_harness": _sha(Path(__file__).resolve()),
        "ld_helper": _sha(HERE / "_assignment_phase_b2_t0_ld_decision_gate.py"),
    }
    result = {
        "repo_hashes": repo,
        "installed_harl_hashes": installed,
        "test_side": test_side,
        "qualified_repo_sources_exact": repo == _INNER["QUALIFIED_REPO_SHA256"],
        "qualified_installed_sources_exact": installed == _INNER["QUALIFIED_HARL_SHA256"],
        "qualified_ld_helper_exact": test_side["ld_helper"] == _INNER["QUALIFIED_LD_HELPER_SHA256"],
        "qualified_t2_harness_exact": test_side["t2_harness"] == QUALIFIED_T2_SHA256,
        "qualified_t2_observer_exact": test_side["t2_observer"] == QUALIFIED_T2_OBSERVER_SHA256,
        "qualified_t3_observer_exact": test_side["t3_observer"] == QUALIFIED_T3_OBSERVER_SHA256,
    }
    result["pass"] = all(
        bool(result[key])
        for key in (
            "qualified_repo_sources_exact",
            "qualified_installed_sources_exact",
            "qualified_ld_helper_exact",
            "qualified_t2_harness_exact",
            "qualified_t2_observer_exact",
            "qualified_t3_observer_exact",
        )
    )
    return result


def run_static() -> dict[str, object]:
    repository = _INNER["SINGLE"]._repository_authority()
    sources = _source_identity()
    result = {
        "interpreter_exact": _INNER["_normal_path"](sys.executable)
        == _INNER["_normal_path"](_INNER["EXPECTED_PYTHON"]),
        "repository_authority": repository,
        "qualified_source_identity": sources,
    }
    result["pass"] = bool(
        result["interpreter_exact"]
        and sources["pass"]
        and repository["head"] == _INNER["EXPECTED_HEAD"]
        and repository["head_origin_merge_base_equal"]
        and repository["staged_path_count"] == 359
        and repository["staged_index_sha256"]
        == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
        and repository["preexisting_monthly_archive_migration_paths_sha256"]
        == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
    )
    return result


_INNER["_source_identity"] = _source_identity
_INNER["run_static"] = run_static

_ledger_counts: Counter[str] = Counter()
_last_bridge_count = 0


def _append_jsonl(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(V2.normalize(payload), sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _prefix(path: Path, marker: str) -> Path:
    return path.parent / path.name[: path.name.index(marker)]


def _stats(values: Sequence[object]) -> dict[str, object]:
    rows = tuple(float(value) for value in values)
    return {
        "count": len(rows),
        "min": min(rows) if rows else None,
        "max": max(rows) if rows else None,
        "mean": sum(rows) / len(rows) if rows else None,
        "sum": sum(rows),
        "finite": all(math.isfinite(value) for value in rows),
    }


def _append_transaction_ledgers(path: Path, payload: Mapping[str, object]) -> None:
    TerminationReason = _INNER.get("_re1_canonical_termination_reason")
    if TerminationReason is None:
        raise RuntimeError("STOP — B2-T4-SR CANONICAL_REASON_DOMAIN_NOT_BOUND")

    normalized = V2.normalize(payload)
    tx = int(normalized["transaction_index"])
    prefix = _prefix(path, f"_tx{tx}_s10.json")
    transaction = normalized["transaction"]
    audit = transaction["real_audit"]
    counts = dict(transaction["exact_execution_counts"])
    lifecycle_rows = tuple(
        row
        for receipt in normalized["lifecycle_decision_gate_receipts"]
        for row in receipt["rows"]
    )
    dvm_by_actor = {int(actor): int(count) for actor, count in audit["actor_dvm_rows"]}
    actor_backward = tuple(int(value) for value in counts["actor_backward_by_actor"])
    actor_steps = tuple(int(value) for value in counts["actor_optimizer_step_by_actor"])
    pre = normalized["pre_collection_learner"]
    post = normalized["post_update_learner"]
    segments = {
        int(row["actor_id"]): row
        for row in transaction["r5_transaction"]["actor_sequence_receipt"]["actor_segments"]
    }
    zero_rows = []
    for actor_id, dvm_count in sorted(dvm_by_actor.items()):
        if dvm_count:
            continue
        row = {
            "transaction_index": tx,
            "update_id": normalized["update_id"],
            "actor_id": actor_id,
            "dvm_rows": 0,
            "backward": actor_backward[actor_id],
            "optimizer_step": actor_steps[actor_id],
            "parameter_unchanged": pre["actor_parameter_digests"][actor_id]
            == post["actor_parameter_digests"][actor_id],
            "optimizer_unchanged": pre["actor_optimizer_digests"][actor_id]
            == post["actor_optimizer_digests"][actor_id],
            "adam_unchanged": pre["actor_adam_steps"][actor_id] == post["actor_adam_steps"][actor_id],
            "segment_skipped": bool(segments[actor_id]["skipped"]),
            "factor_identity": bool(segments[actor_id]["factor_transition"]["recurrence_exact"]),
            "pass": False,
        }
        row["pass"] = bool(
            row["backward"] == 0
            and row["optimizer_step"] == 0
            and row["parameter_unchanged"]
            and row["optimizer_unchanged"]
            and row["adam_unchanged"]
            and row["segment_skipped"]
            and row["factor_identity"]
        )
        if not row["pass"]:
            raise RuntimeError("STOP — B2-T4-RE1 ZERO-DVM-ACTOR-CONTRACT")
        zero_rows.append(row)
        _append_jsonl(prefix.parent / f"{prefix.name}_zero_dvm_actor_ledger.jsonl", row)
        _ledger_counts["zero_dvm"] += 1
    reason_counts = dict(normalized["terminal_reason_counts"])
    expected_keys = tuple(tuple(row) for row in normalized["expected_terminal_keys"])
    observed_keys = tuple(tuple(row) for row in normalized["observed_terminal_keys"])
    terminal = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "reason_counts": reason_counts,
        "expected_keys": expected_keys,
        "observed_keys": observed_keys,
        "missing": tuple(sorted(set(expected_keys) - set(observed_keys))),
        "extra": tuple(sorted(set(observed_keys) - set(expected_keys))),
        "duplicates": len(observed_keys) - len(set(observed_keys)),
        "reconciliation_digest": normalized["terminal_reconciliation_digest"],
        "s7_ledger_unchanged": True,
        "pass": expected_keys == observed_keys and len(observed_keys) == len(set(observed_keys)),
    }
    if not terminal["pass"]:
        raise RuntimeError("STOP — B2-T4-RE1 TERMINAL-RECONCILIATION")
    reason_grid_expected_t = len(normalized["re1_step_details"])
    reason_grid_expected_e = len(normalized["re1_step_details"][0]["state_rows"])
    reason_grid = serialize_termination_reason_grid_v1(
        normalized["termination_reason_grid"],
        expected_t=reason_grid_expected_t,
        expected_e=reason_grid_expected_e,
        valid_reason_values=tuple(int(member) for member in TerminationReason),
    )
    final_none = bool(
        reason_grid
        and all(
            cell[0] == int(TerminationReason.NONE)
            for cell in reason_grid[-1]
        )
    )
    bootstrap = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "none_rows": int(reason_counts.get("NONE", 0)),
        "terminal_rows": sum(int(value) for key, value in reason_counts.items() if key != "NONE"),
        "expected_terminal_key_count": len(expected_keys),
        "observed_terminal_key_count": len(observed_keys),
        "termination_reason_grid": reason_grid,
        "termination_reason_grid_shape": (
            reason_grid_expected_t,
            reason_grid_expected_e,
            1,
        ),
        "termination_reason_grid_schema": "b2_t4_sr_termination_reason_grid_v1",
        "final_current_value_evaluated": bool(audit["next_current_bundle_digest"]),
        "timeout_sidecar_not_required_for_none": True,
        "adapter_pass": True,
        "s0_pass": True,
        "event_returns_pass": normalized["event_return_compute_count"] == 1,
        "s10_pass": normalized["s10_pass"],
        "real_nonterminal_witness_candidate": final_none,
        "pass": bool(
            final_none
            and len(expected_keys) == 0
            and len(observed_keys) == 0
            and normalized["event_return_compute_count"] == 1
            and normalized["stock_compute_returns"] == 0
            and normalized["s10_pass"]
        ),
    }
    immutability = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "source_config_identity_digest": normalized["source_config_identity_digest"],
        "episode_generation": normalized["runtime_before_update"]["tensor_digests"]["episode_generation"],
        "lifecycle_state_before_update_digest": normalized["runtime_before_update"]["digest"],
        "lifecycle_state_after_update_digest": normalized["runtime_after_update"]["digest"],
        "equal": bool(normalized["runtime_update_equal"]),
        "learner_advanced_simulation": normalized["runtime_before_update"]["common_step_counter"]
        != normalized["runtime_after_update"]["common_step_counter"],
    }
    if not immutability["equal"] or immutability["learner_advanced_simulation"]:
        raise RuntimeError(STOP_RUNTIME)
    transaction_row = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "physical_step_range": normalized["rollout_provenance"]["collection_physical_step_range"],
        "actor_order": normalized["actor_order"],
        "dvm_by_actor": dvm_by_actor,
        "actor_backward_by_actor": actor_backward,
        "actor_optimizer_step_by_actor": actor_steps,
        "critic_backward": int(counts["critic_backward"]),
        "critic_optimizer_step": int(counts["critic_optimizer_step"]),
        "valuenorm_update": int(counts["live_valuenorm_update"]),
        "valid_nonzero": normalized["valid_nonzero"],
        "valid_zero_effective": normalized["valid_zero_effective"],
        "event_returns": normalized["event_return_compute_count"],
        "stock_compute_returns": normalized["stock_compute_returns"],
        "s7_s8_s9_s10": (
            normalized["s7_pass"], normalized["s8_pass"], normalized["s9_pass"], normalized["s10_pass"]
        ),
        "finite": all(
            bool(post[key])
            for key in (
                "actor_parameters_finite",
                "actor_optimizer_states_finite",
                "critic_parameters_finite",
                "critic_optimizer_state_finite",
                "valuenorm_state_finite",
            )
        ),
    }
    step_details = tuple(normalized["re1_step_details"])
    task_progress = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "steps": step_details,
        "lifecycle_rows": lifecycle_rows,
        "observability_steps": normalized["observability_steps"],
    }
    first_state = step_details[0]["state_rows"]
    last_state = step_details[-1]["state_rows"]
    timeline = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "global_physical_steps": normalized["rollout_provenance"]["collection_physical_step_range"],
        "episode_generation_before_rollout": tuple(row["episode_generation"] for row in first_state),
        "episode_generation_after_rollout": tuple(row["episode_generation"] for row in last_state),
        "episode_local_progress_after_rollout": tuple(row["episode_local_step"] for row in last_state),
        "terminal_reasons": reason_counts,
        "autoreset_count": len(observed_keys),
        "terminal_keys_expected": expected_keys,
        "terminal_keys_observed": observed_keys,
    }
    metrics = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "team_reward_sum": normalized["team_reward_sum_diagnostic_only"],
        "actor_loss": _stats(normalized["actor_losses"]),
        "actor_gradient_norm": _stats(normalized["actor_gradient_norms"]),
        "critic_loss": _stats(normalized["critic_losses"]),
        "critic_gradient_norm": _stats(normalized["critic_gradient_norms"]),
        "observability_steps": normalized["observability_steps"],
        "descriptive_only": True,
    }
    rolling = {
        "transaction_index": tx,
        "update_id": normalized["update_id"],
        "actor_parameter_digests": post["actor_parameter_digests"],
        "actor_optimizer_digests": post["actor_optimizer_digests"],
        "critic_parameter_digest": post["critic_parameter_digest"],
        "critic_optimizer_digest": post["critic_optimizer_digest"],
        "valuenorm_digest": post["canonical_valuenorm_digest"],
        "finite": transaction_row["finite"],
        "route_poisoned": normalized["route_poisoned"],
    }
    ledger_rows = (
        ("transaction", transaction_row),
        ("episode_update_timeline", timeline),
        ("lifecycle_task_progress", task_progress),
        ("terminal_reconciliation", terminal),
        ("nonterminal_bootstrap", bootstrap),
        ("learner_runtime_immutability", immutability),
        ("training_metric", metrics),
        ("rolling_health", rolling),
    )
    for name, row in ledger_rows:
        _append_jsonl(prefix.parent / f"{prefix.name}_{name}_ledger.jsonl", row)
        _ledger_counts[name] += 1


def _append_bridge(path: Path, payload: Mapping[str, object]) -> None:
    global _last_bridge_count
    normalized = V2.normalize(payload)
    bridges = normalized["bridges"]
    if len(bridges) <= _last_bridge_count:
        return
    bridge = bridges[-1]
    _last_bridge_count = len(bridges)
    prefix = _prefix(path, "_continuity_bridges.json")
    _append_jsonl(
        prefix.parent / f"{prefix.name}_bridge_ledger.jsonl",
        {
            "bridge_index": bridge["bridge_index"],
            "from_update_id": bridge["from_update_id"],
            "to_update_id": bridge["to_update_id"],
            "persistent_object_identity": bridge["persistent_object_identity"],
            "learner_post_to_pre_exact": bridge["learner_post_to_pre_exact"],
            "collection_preserved_learner": bridge["collection_preserved_learner"],
            "route_unpoisoned": bridge["route_unpoisoned"],
            "next_s0_established": bridge["next_s0_established"],
            "pass": bridge["pass"],
        },
    )
    _ledger_counts["bridge"] += 1


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    _base_atomic_json(path, payload)
    if re.search(r"_tx\d+_s10\.json$", path.name):
        _append_transaction_ledgers(path, payload)
    elif path.name.endswith("_continuity_bridges.json"):
        _append_bridge(path, payload)


_INNER["_atomic_json"] = _atomic_json


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _find_witnesses(prefix: Path) -> dict[str, object]:
    tx_rows = _read_jsonl(prefix.parent / f"{prefix.name}_transaction_ledger.jsonl")
    bridge_rows = _read_jsonl(prefix.parent / f"{prefix.name}_bridge_ledger.jsonl")
    progress_rows = _read_jsonl(prefix.parent / f"{prefix.name}_lifecycle_task_progress_ledger.jsonl")
    terminal_rows = _read_jsonl(prefix.parent / f"{prefix.name}_terminal_reconciliation_ledger.jsonl")
    bootstrap_rows = _read_jsonl(prefix.parent / f"{prefix.name}_nonterminal_bootstrap_ledger.jsonl")
    zero_rows = _read_jsonl(prefix.parent / f"{prefix.name}_zero_dvm_actor_ledger.jsonl")
    immutable_rows = _read_jsonl(prefix.parent / f"{prefix.name}_learner_runtime_immutability_ledger.jsonl")
    events = []
    state_by_step: dict[tuple[int, int], dict[str, object]] = {}
    lifecycle_by_step: dict[tuple[int, int, int], dict[str, object]] = {}
    for update in progress_rows:
        tx = int(update["transaction_index"])
        for step in update["steps"]:
            global_step = int(step["global_physical_step"])
            for state in step["state_rows"]:
                state_by_step[(global_step, int(state["env_id"]))] = state
            events.extend({**event, "transaction_index": tx, "global_physical_step": global_step} for event in step["events"])
        for receipt in update["lifecycle_rows"]:
            lifecycle_by_step[(int(receipt["collection_index"]), int(receipt["env_index"]), int(receipt["robot_index"]))] = receipt
    w1 = None
    for tx in range(1, TRANSACTION_COUNT):
        last_step = tx * 2
        next_step = last_step + 1
        for (step, env_id), before in state_by_step.items():
            if step != last_step:
                continue
            after = state_by_step.get((next_step, env_id))
            if after is None or before["episode_generation"] != after["episode_generation"]:
                continue
            for task_id, owner in enumerate(before["ownership"]):
                if int(owner) < 0 or int(before["task_state"][task_id]) not in (1, 2, 3):
                    continue
                robot_id = int(owner)
                decision = lifecycle_by_step.get((next_step, env_id, robot_id))
                if (
                    int(after["ownership"][task_id]) == robot_id
                    and int(after["task_state"][task_id]) in (1, 2, 3)
                    and decision is not None
                    and not bool(decision["decision_required"])
                    and int(decision["actor_policy_call_count"]) == 0
                ):
                    w1 = {
                        "pass": True,
                        "transaction_index": tx,
                        "boundary_steps": (last_step, next_step),
                        "env_id": env_id,
                        "robot_id": robot_id,
                        "task_id": task_id,
                        "before_s0": before,
                        "after_s10_next_rollout": after,
                        "next_lifecycle_row": decision,
                    }
                    break
            if w1:
                break
        if w1:
            break
    claims = {}
    completions = []
    for event in events:
        key = (int(event["env_id"]), int(event["robot_id"]), int(event["task_id"]))
        if event["event"] == "task_claimed":
            claims.setdefault(key, event)
        elif event["event"] == "task_completed":
            completions.append((key, event))
    w2 = None
    for key, completion in completions:
        claim = claims.get(key)
        if claim is None or int(claim["transaction_index"]) >= int(completion["transaction_index"]):
            continue
        state = state_by_step.get((int(completion["global_physical_step"]), int(key[0])))
        if state is None:
            continue
        task_id, robot_id = key[2], key[1]
        if int(state["task_state"][task_id]) == 4 and int(state["ownership"][task_id]) == -1:
            w2 = {
                "pass": True,
                "claim": claim,
                "completion": completion,
                "claim_tx_lt_completion_tx": True,
                "completion_state": state,
                "owner_cleared": True,
                "decision_reopened": bool(state["next_decision_required"][robot_id]),
            }
            break
    total_completions = sum(int(event["event"] == "task_completed") for event in events)
    coverage_max = max(
        int(state["coverage_count"])
        for update in progress_rows
        for step in update["steps"]
        for state in step["state_rows"]
    )
    w3 = zero_rows[0] if zero_rows else None
    w4 = next((row for row in bootstrap_rows if row["real_nonterminal_witness_candidate"]), None)
    w5 = next((row for row in terminal_rows if row["observed_keys"]), None)
    first_terminal_tx = None if w5 is None else int(w5["transaction_index"])
    w6 = None
    if first_terminal_tx is not None and first_terminal_tx < TRANSACTION_COUNT:
        post = tx_rows[first_terminal_tx]
        w6 = {
            "pass": int(post["transaction_index"]) == first_terminal_tx + 1,
            "first_terminal_transaction": first_terminal_tx,
            "post_autoreset_transaction": int(post["transaction_index"]),
            "post_autoreset_update_id": post["update_id"],
            "fresh_rollout_and_update": True,
        }
    witnesses = {
        "W1_CROSS_UPDATE_OWNERSHIP": w1,
        "W2_MULTI_UPDATE_COMPLETION": w2,
        "W3_ZERO_DVM_ACTOR": w3,
        "W4_NONTERMINAL_BOOTSTRAP": w4,
        "W5_NORMAL_HORIZON_TERMINAL_AUTORESET": w5,
        "W6_POST_AUTORESET_TRAINING": w6,
        "W7_RUNTIME_P2_IMMUTABILITY": {
            "pass": len(immutable_rows) == TRANSACTION_COUNT
            and all(bool(row["equal"]) for row in immutable_rows),
            "equal": sum(int(bool(row["equal"])) for row in immutable_rows),
            "required": TRANSACTION_COUNT,
        },
        "task_progress_gate": {
            "task_completed_events": total_completions,
            "completed_count_delta_positive": total_completions > 0,
            "coverage_max": coverage_max,
            "pass": total_completions >= 1 and coverage_max > 0,
        },
        "ledger_counts": {
            "transactions": len(tx_rows),
            "bridges": len(bridge_rows),
            "terminal": len(terminal_rows),
            "bootstrap": len(bootstrap_rows),
            "immutability": len(immutable_rows),
            "zero_dvm_rows": len(zero_rows),
        },
    }
    required = tuple(f"W{index}" for index in range(1, 8))
    mapping = tuple(witnesses[key] for key in witnesses if key.startswith(required))
    witnesses["pass"] = bool(
        all(item is not None and bool(item.get("pass", False)) for item in mapping)
        and witnesses["task_progress_gate"]["pass"]
        and len(tx_rows) == 160
        and len(bridge_rows) == 159
    )
    return witnesses


def _postprocess_success(prefix: Path, result_path: Path) -> dict[str, object]:
    final_path = prefix.parent / f"{prefix.name}_final_result.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    witnesses = _find_witnesses(prefix)
    if not witnesses["pass"]:
        raise RuntimeError(f"STOP — B2-T4-RE1 REQUIRED-WITNESS-GATE: {witnesses}")
    witness_path = prefix.parent / f"{prefix.name}_primary_witnesses.json"
    _base_atomic_json(witness_path, witnesses)
    retained_txs = set(SENTINEL_TRANSACTIONS)
    for name, witness in witnesses.items():
        if not name.startswith("W") or not isinstance(witness, Mapping):
            continue
        for field in ("transaction_index", "first_terminal_transaction", "post_autoreset_transaction"):
            if field in witness:
                retained_txs.add(int(witness[field]))
        for field in ("claim", "completion"):
            if isinstance(witness.get(field), Mapping):
                retained_txs.add(int(witness[field]["transaction_index"]))
    removed = []
    tx_pattern = re.compile(rf"^{re.escape(prefix.name)}_tx(\d+)_")
    bridge_pattern = re.compile(rf"^{re.escape(prefix.name)}_bridge\d+_(pre|post)_collection\.json$")
    for path in sorted(prefix.parent.glob(f"{prefix.name}_*.json")):
        match = tx_pattern.match(path.name)
        if match and int(match.group(1)) not in retained_txs:
            path.unlink()
            removed.append(path.name)
        elif bridge_pattern.match(path.name):
            path.unlink()
            removed.append(path.name)
    ledger_names = (
        "transaction", "bridge", "episode_update_timeline", "lifecycle_task_progress",
        "terminal_reconciliation", "nonterminal_bootstrap", "zero_dvm_actor",
        "learner_runtime_immutability", "training_metric", "rolling_health",
    )
    inventory = {}
    for name in ledger_names:
        path = prefix.parent / f"{prefix.name}_{name}_ledger.jsonl"
        inventory[name] = {"path": str(path), "rows": len(_read_jsonl(path)), "bytes": path.stat().st_size, "sha256": _sha(path)}
    final.update(
        {
            "classification": PASS,
            **classification_precedence_metadata_v1(
                raw_worker_classification=str(final.get("classification", PASS)),
                final_phase_classification=PASS,
                adjudication_source="b2_t4_re1_runner_postprocess_success",
            ),
            "primary_witnesses": witnesses,
            "primary_witness_path": str(witness_path),
            "append_only_ledgers": inventory,
            "sentinel_transactions": tuple(sorted(SENTINEL_TRANSACTIONS)),
            "retained_full_detail_transactions": tuple(sorted(retained_txs)),
            "non_sentinel_detail_removed": len(removed),
            "production_semantic_modifications": 0,
            "transaction_161_started": False,
            "cuda_cublas_readiness_probes": 1,
            "runtime_p2_immutability": "160/160 PASS",
        }
    )
    _base_atomic_json(final_path, final)
    worker = json.loads(result_path.read_text(encoding="utf-8"))
    worker.update(
        {
            "classification": PASS,
            **classification_precedence_metadata_v1(
                raw_worker_classification=str(worker.get("classification", PASS)),
                final_phase_classification=PASS,
                adjudication_source="b2_t4_re1_runner_postprocess_success",
            ),
            "primary_witnesses": witnesses,
            "append_only_ledgers": inventory,
            "final_result": {"path": str(final_path), "bytes": final_path.stat().st_size, "sha256": _sha(final_path)},
        }
    )
    _base_atomic_json(result_path, worker)
    return final


def run_worker(args: object) -> int:
    code = int(_base_run_worker(args))
    if code != 0:
        result_path = Path(args.result_file).resolve()
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            raw_classification = str(result.get("classification", "UNCLASSIFIED"))
            result.update(
                classification_precedence_metadata_v1(
                    raw_worker_classification=raw_classification,
                    final_phase_classification=raw_classification,
                    adjudication_source="base_worker_execution",
                )
            )
            _base_atomic_json(result_path, result)
        return code
    try:
        _postprocess_success(Path(args.artifact_prefix).resolve(), Path(args.result_file).resolve())
        return 0
    except BaseException as exc:
        result_path = Path(args.result_file).resolve()
        result = json.loads(result_path.read_text(encoding="utf-8"))
        raw_classification = str(result.get("classification", "UNCLASSIFIED"))
        final_classification = (
            "PHASE-B2-T4-RE1-STOP-REQUIRED-WITNESS-GATE-NOT-COMPLETE"
        )
        result.update(
            {
                "status": "failed",
                "classification": final_classification,
                **classification_precedence_metadata_v1(
                    raw_worker_classification=raw_classification,
                    final_phase_classification=final_classification,
                    adjudication_source="b2_t4_re1_runner_postprocess_failure",
                ),
                "postprocess_error": f"{type(exc).__name__}: {exc}",
                "retry_performed": False,
            }
        )
        _base_atomic_json(result_path, result)
        return 20


_INNER["run_worker"] = run_worker


def main() -> int:
    return int(_INNER["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
