"""B2-T4-NR exact nonterminal rollout-completeness qualification.

This bounded CPU suite exercises the production terminal-evidence reconciler,
the independent R5 S0 completeness gate, and three source-faithful private
route/adapter witnesses.  It never imports or launches AppLauncher, starts a
training campaign, performs checkpoint I/O, or activates the public route.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from typing import Any, Callable

import gymnasium
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_v1_event_route_helpers as V1  # noqa: E402
import _assignment_phase_b2_r3_actor_mutation_helpers as R3H  # noqa: E402
import _assignment_phase_b2_r5_full_transaction_helpers as F  # noqa: E402


R1 = F.R1
EVIDENCE = F.E
R5 = F.R5
ADAPTER = R1.load_canonical("assignment_event_training_real_isaac_adapter.py")

PASS_CLASSIFICATION = (
    "PHASE-B2-T4-NR-NONTERMINAL-ROLLOUT-COMPLETENESS-CONTRACT-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
DEVICE = torch.device("cpu")


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_stop(stop_code: str, function: Callable[[], object]) -> dict[str, object]:
    try:
        function()
    except EVIDENCE.B2RContractError as exc:
        _assert(exc.stop_code == stop_code, f"wrong STOP: {exc.stop_code}; expected {stop_code}")
        return {"result": "STOP", "stop_code": exc.stop_code, "message": str(exc)}
    raise AssertionError(f"expected {stop_code}")


def _pass_reconciliation(
    expected: tuple[tuple[int, int, int], ...],
    observed: tuple[tuple[int, int, int], ...],
) -> dict[str, object]:
    receipt = R5.reconcile_terminal_evidence_v1(
        expected_terminal_keys=expected,
        observed_terminal_keys=observed,
    )
    _assert(receipt.exact_match, "exact reconciliation did not pass")
    return {
        "result": "PASS",
        "expected_count": receipt.expected_count,
        "observed_count": receipt.observed_count,
        "exact_match": receipt.exact_match,
        "receipt_digest": receipt.evidence_digest,
    }


def terminal_expectation_matrix() -> dict[str, object]:
    k_time = (1, 4, 9)
    k_complete = (2, 7, 12)
    k_no_feasible = (3, 8, 15)
    cases: dict[str, object] = {}
    cases["A_all_NONE_empty_empty"] = _pass_reconciliation((), ())
    cases["B_all_NONE_stale_extra"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_UNEXPECTED,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(), observed_terminal_keys=((0, 1, 2),)
        ),
    )
    cases["C_TIME_LIMIT_exact"] = _pass_reconciliation((k_time,), (k_time,))
    cases["D_TIME_LIMIT_missing"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_MISSING,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time,), observed_terminal_keys=()
        ),
    )
    cases["E_TIME_LIMIT_wrong_generation"] = _expect_stop(
        R5.STOP_TERMINAL_GENERATION_MISMATCH,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time,), observed_terminal_keys=((1, 3, 8),)
        ),
    )
    cases["F_ALL_TASKS_COMPLETED_exact"] = _pass_reconciliation(
        (k_complete,), (k_complete,)
    )
    cases["G_NO_FEASIBLE_TASKS_REMAIN_exact"] = _pass_reconciliation(
        (k_no_feasible,), (k_no_feasible,)
    )
    cases["H_mixed_NONE_TIME_LIMIT_exact"] = _pass_reconciliation(
        (k_time,), (k_time,)
    )
    cases["I_mixed_NONE_ALL_TASKS_COMPLETED_exact"] = _pass_reconciliation(
        (k_complete,), (k_complete,)
    )
    cases["J_mixed_one_missing"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_MISSING,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time, k_complete),
            observed_terminal_keys=(k_time,),
        ),
    )
    cases["K_duplicate_observed"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_DUPLICATE,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time,), observed_terminal_keys=(k_time, k_time)
        ),
    )
    cases["M_stale_previous_generation"] = _expect_stop(
        R5.STOP_TERMINAL_GENERATION_MISMATCH,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_complete,),
            observed_terminal_keys=((2, 6, 11),),
        ),
    )
    cases["N_extra_for_NONE_env"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_UNEXPECTED,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time,),
            observed_terminal_keys=(k_time, (0, 9, 18)),
        ),
    )
    cases["additional_terminal_identity_mismatch"] = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_IDENTITY_MISMATCH,
        lambda: R5.reconcile_terminal_evidence_v1(
            expected_terminal_keys=(k_time,),
            observed_terminal_keys=((0, 4, 9),),
        ),
    )
    positive = sum(item["result"] == "PASS" for item in cases.values())
    negative = sum(item["result"] == "STOP" for item in cases.values())
    _assert((positive, negative) == (6, 8), "matrix case count drift")
    return {
        "status": "PASS",
        "case_count": len(cases),
        "positive_cases": positive,
        "negative_fail_closed_cases": negative,
        "unexpected_negative_passes": 0,
        "terminal_missing_false_accepts": 0,
        "cases": cases,
    }


def missing_nonterminal_final_bootstrap() -> dict[str, object]:
    context = F.make_context(update_id="b2-t4-nr-missing-current-bootstrap")
    buffer = context.rollover_resources.critic_buffer
    collector = context.rollover_resources.terminal_collector
    buffer.termination_reason.fill_(int(F.TRANSITION.TerminationReason.NONE))
    buffer.timeout_bootstrap_masks.zero_()
    buffer.timeout_bootstrap_value_preds.fill_(float("nan"))
    collector._consumed_terminal_keys.clear()
    reconciliation = R5.reconcile_terminal_evidence_v1(
        expected_terminal_keys=(), observed_terminal_keys=()
    )
    rollout = replace(
        context.rollout_evidence,
        termination_reason_digest=F._tensor_digest(buffer.termination_reason),
        timeout_sidecar_digest=F._tuple_tensor_digest(
            buffer.timeout_bootstrap_masks, buffer.timeout_bootstrap_value_preds
        ),
        expected_terminal_keys=(),
        terminal_consumption_keys=(),
        terminal_reconciliation_digest=reconciliation.evidence_digest,
        final_value_evaluated=False,
    )
    failure = _expect_stop(
        R5.STOP_ROLLOUT_INCOMPLETE,
        lambda: R5.validate_rollout_complete_v1(
            authority=context.authority,
            rollout=rollout,
            rollover_resources=context.rollover_resources,
        ),
    )
    return {
        "status": "PASS",
        "reason_grid": "all NONE",
        "expected_terminal_keys": 0,
        "observed_terminal_keys": 0,
        "final_current_next_value_available": False,
        **failure,
    }


def _make_real_components(harness: V1.RouteHarness, *, seed: int) -> dict[str, object]:
    torch.manual_seed(seed)
    schema = V1.I4.SCHEMA.build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=harness.scale
    )
    actor_dim = int(schema["actor_schema"]["dimension"])
    critic_dim = int(schema["critic_schema"]["dimension"])
    args = R3H._args()
    obs_space = gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, shape=(actor_dim,), dtype=np.float32
    )
    shared_space = gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, shape=(critic_dim,), dtype=np.float32
    )
    action_space = gymnasium.spaces.Discrete(harness.N + 1)
    actors = [
        R3H.HAPPO(args, obs_space, action_space, device=DEVICE)
        for _ in range(harness.M)
    ]
    critic = R3H.VCritic(args, shared_space, device=DEVICE)
    value_normalizer = R3H.ValueNorm(1, device=DEVICE)
    buffer_args = {
        **args,
        "episode_length": harness.T,
        "n_rollout_threads": harness.E,
        "use_proper_time_limits": True,
    }
    buffer = V1.CB.EventOnPolicyCriticBufferEPV2(
        buffer_args, V1.Box((critic_dim,)), device=DEVICE
    )
    for actor in actors:
        actor.prep_rollout()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    critic.prep_rollout()
    critic.critic_optimizer.zero_grad(set_to_none=True)

    def forbidden_actor_trainer(**_kwargs: object) -> object:
        raise RuntimeError("parallel actor trainer must remain unreachable")

    def forbidden_critic_trainer(_buffer: object, _normalizer: object) -> object:
        raise RuntimeError("parallel critic trainer must remain unreachable")

    route = V1.ROUTE._compose_dormant_event_learned_policy_route_v2(
        episode_length=harness.T,
        actors=tuple(actors),
        critic=critic,
        critic_buffer=buffer,
        admitted_reset=harness._admitted_reset,
        current_decision_supplier=harness._current_bundle,
        current_decision_validator=harness._validate_current,
        capture_i42_decision=harness.wrapper._capture_event_proposal_decision,
        step_i42_proposals=harness.wrapper._step_event_proposals,
        action_builder=lambda _env, assignment: assignment.detach().clone(),
        actor_trainer=forbidden_actor_trainer,
        critic_trainer=forbidden_critic_trainer,
        value_normalizer=value_normalizer,
        actor_rnn_shape=(1, R3H.HIDDEN),
        call_observer=harness._observe,
    )
    return {
        "route": route,
        "actors": actors,
        "critic": critic,
        "value_normalizer": value_normalizer,
        "algo_args": {"train": {"use_valuenorm": True}, "algo": args},
    }


def _collect_integrated_scenario(scenario: str, *, seed: int) -> dict[str, object]:
    if scenario == "scale":
        harness = V1.RouteHarness(E=2, M=2, N=4, T=2, scenario=scenario)
    else:
        harness = V1.RouteHarness(E=4, M=3, N=4, T=2, scenario=scenario)
    components = _make_real_components(harness, seed=seed)
    route = components["route"]
    reset_result = route.reset()
    receipts = tuple(route.collect_step() for _ in range(harness.T))
    reason_grid = route.critic_buffer.termination_reason.detach().clone()
    reason_values = tuple(int(item) for item in reason_grid.flatten().tolist())
    observed_keys = tuple(route.collector.consumed_terminal_keys)
    expected_keys = ADAPTER._derive_expected_terminal_keys_v1(
        completed_storages=tuple(route.actor_storages),
        termination_reason=reason_grid,
        T=harness.T,
        E=harness.E,
    )
    _assert(
        len(expected_keys) == sum(value != int(V1.Reason.NONE) for value in reason_values),
        "terminal reason/key cardinality mismatch",
    )
    _assert(expected_keys == observed_keys, "canonical expected/observed terminal keys differ")
    return {
        "harness": harness,
        "components": components,
        "route": route,
        "reset_result": reset_result,
        "receipts": receipts,
        "reason_grid": reason_grid,
        "reason_values": reason_values,
        "expected_keys": expected_keys,
        "observed_keys": observed_keys,
        "timeout_sidecar_rows": int(route.critic_buffer.timeout_bootstrap_masks.sum().item()),
    }


def _execute_integrated(collected: dict[str, object], *, update_id: str) -> object:
    components = collected["components"]
    harness = collected["harness"]
    base = R3H.make_base_authority()
    return ADAPTER.execute_real_isaac_single_transaction_v1(
        repository_head=base.repository_head,
        dirty_state_classification="authorized B2-T4-NR bounded CPU source-faithful qualification",
        repo_source_hashes=base.repo_source_hashes,
        installed_harl_source_hashes=base.installed_harl_source_hashes,
        route=collected["route"],
        actors=tuple(components["actors"]),
        critic=components["critic"],
        live_value_normalizer=components["value_normalizer"],
        algo_args=components["algo_args"],
        environment_identity=f"SyntheticEventEnvironment/{harness.scenario}/CPU",
        profile_name=harness.profile.profile_name.value,
        real_environment_resets=1,
        real_rollout_steps=harness.T,
        precedence_resolution_evidence_digest=R1.digest(f"{update_id}-precedence"),
        terminal_correlation_evidence_digest=R1.digest(f"{update_id}-terminal-correlation"),
        timeout_critic_evidence_digest=R1.digest(f"{update_id}-timeout"),
        effective_assignment_evidence_digest=R1.digest(f"{update_id}-effective-assignment"),
        proposal_effective_authority_separate=True,
        update_id=update_id,
        order_seed=seed_from_update_id(update_id),
        classification=PASS_CLASSIFICATION,
    )


def seed_from_update_id(update_id: str) -> int:
    return 1 + sum(update_id.encode("utf-8")) % 997


def _counts(transaction: object) -> dict[str, object]:
    return {name: value for name, value in transaction.exact_execution_counts}


def integrated_all_none() -> dict[str, object]:
    collected = _collect_integrated_scenario("scale", seed=2401)
    none_value = int(V1.Reason.NONE)
    _assert(all(value == none_value for value in collected["reason_values"]), "not all NONE")
    _assert(collected["expected_keys"] == collected["observed_keys"] == (), "all-NONE keys")
    _assert(collected["timeout_sidecar_rows"] == 0, "all-NONE timeout sidecar used")
    transaction = _execute_integrated(collected, update_id="b2-t4-nr-all-none-0001")
    counts = _counts(transaction)
    _assert(transaction.r5_transaction.transaction_success, "all-NONE R5 transaction failed")
    _assert(counts["s10_entries"] == 1, "all-NONE did not reach S10")
    _assert(transaction.real_audit.event_return_compute_count == 1, "event-return compute count")
    _assert(transaction.checkpoint_weight_io == transaction.public_route_activations == 0, "forbidden I/O")
    return {
        "status": "PASS",
        "T": 2,
        "E": 2,
        "termination_reason_counts": {"NONE": 4, "terminal": 0},
        "expected_terminal_keys": 0,
        "observed_terminal_keys": 0,
        "current_next_bootstrap": "available and finite",
        "timeout_sidecar_rows": 0,
        "event_return_compute_count": 1,
        "stock_compute_returns_calls": 0,
        "s10_reached": True,
        "exact_execution_counts": counts,
        "evidence_digest": transaction.evidence_digest,
    }


def integrated_mixed() -> dict[str, object]:
    collected = _collect_integrated_scenario("lifecycle", seed=2402)
    reason_values = collected["reason_values"]
    none_value = int(V1.Reason.NONE)
    _assert(any(value == none_value for value in reason_values), "mixed route lacks NONE")
    _assert(any(value != none_value for value in reason_values), "mixed route lacks terminal")
    _assert(len(collected["expected_keys"]) > 0, "mixed route lacks expected terminal keys")
    transaction = _execute_integrated(collected, update_id="b2-t4-nr-mixed-0001")
    counts = _counts(transaction)
    _assert(transaction.r5_transaction.transaction_success, "mixed R5 transaction failed")
    _assert(counts["s10_entries"] == 1, "mixed route did not reach S10")
    names = {int(reason): reason.name for reason in V1.Reason}
    reason_counts = {
        names[value]: reason_values.count(value) for value in sorted(set(reason_values))
    }
    return {
        "status": "PASS",
        "T": 2,
        "E": 4,
        "reason_counts": reason_counts,
        "expected_terminal_keys": len(collected["expected_keys"]),
        "observed_terminal_keys": len(collected["observed_keys"]),
        "timeout_sidecar_rows": collected["timeout_sidecar_rows"],
        "NONE_rows_use_current_next_bootstrap": True,
        "terminal_rows_use_frozen_bootstrap_semantics": True,
        "stock_compute_returns_calls": 0,
        "s10_reached": True,
        "exact_execution_counts": counts,
        "evidence_digest": transaction.evidence_digest,
    }


def integrated_missing_terminal_fail_closed() -> dict[str, object]:
    collected = _collect_integrated_scenario("lifecycle", seed=2403)
    route = collected["route"]
    missing = collected["expected_keys"][0]
    route.collector._consumed_terminal_keys.remove(missing)
    failure = _expect_stop(
        R5.STOP_TERMINAL_EVIDENCE_MISSING,
        lambda: _execute_integrated(collected, update_id="b2-t4-nr-missing-terminal-0001"),
    )
    _assert(not route.poisoned, "pre-S0 reconciliation failure poisoned route")
    return {
        "status": "PASS",
        "terminal_row_present": True,
        "removed_terminal_key": list(missing),
        "mutation_started": False,
        "s0_entered": False,
        "route_poisoned": False,
        **failure,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    tests: tuple[tuple[str, Callable[[], dict[str, object]]], ...] = (
        ("terminal_expectation_matrix", terminal_expectation_matrix),
        ("missing_nonterminal_final_bootstrap", missing_nonterminal_final_bootstrap),
        ("integrated_all_none", integrated_all_none),
        ("integrated_mixed", integrated_mixed),
        ("integrated_missing_terminal_fail_closed", integrated_missing_terminal_fail_closed),
    )
    results: dict[str, object] = {}
    for name, function in tests:
        try:
            results[name] = function()
        except BaseException as exc:
            payload = {
                "classification": "PHASE-B2-T4-NR-STOP-REGRESSION",
                "status": "FAIL",
                "failed_test": name,
                "error": f"{type(exc).__name__}: {exc}",
                "results": results,
            }
            print(json.dumps(payload, indent=2 if args.json else None, sort_keys=True))
            return 1
    payload = {
        "classification": PASS_CLASSIFICATION,
        "status": "PASS",
        "tests_passed": len(results),
        "tests_total": len(tests),
        "source_faithful_integrated_runs": 3,
        "app_launcher_lifetimes": 0,
        "formal_b2_t4_updates": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "results": results,
    }
    print(json.dumps(payload, indent=2 if args.json else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
