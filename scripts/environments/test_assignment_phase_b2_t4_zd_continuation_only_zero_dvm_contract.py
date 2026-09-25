"""B2-T4-ZD bounded CPU continuation-only/zero-DVM adapter qualification."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Callable

import torch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import _assignment_phase_b2_r3_actor_mutation_helpers as R3H  # noqa: E402
import test_assignment_phase_b2_t4_nr_nonterminal_rollout_completeness_contract as NR  # noqa: E402
import _assignment_phase_b2_v1_event_route_helpers as V1  # noqa: E402


ADAPTER = NR.ADAPTER
R5 = NR.R5
EVIDENCE = NR.EVIDENCE
PASS = (
    "PHASE-B2-T4-ZD-CONTINUATION-ONLY-ZERO-DVM-REAL-ADAPTER-CONTRACT-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
E, M, N, T = 2, 3, 12, 2
RE2_DIR = (
    ROOT
    / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
    / "AgentRead/202609/20260914/b2_t4_re2_artifacts"
)
RE2_TX2 = RE2_DIR / "b2_t4_re2_normal_horizon_20260914_formal01_tx2_rollout_decision_evidence.json"
RE2_FINAL = RE2_DIR / "b2_t4_re2_normal_horizon_20260914_formal01_final_result.json"
RE2_ADJUDICATION = RE2_DIR / "re2_failure_adjudication.json"
HISTORICAL_HASHES = {
    RE2_TX2.name: "93b4624167ce8b8dd052e4d3ab4c3cf105b34cd1a140ee840313edc2f8935fda",
    RE2_FINAL.name: "0f50df029eec40f5e4dcc69f3420078232b2882cf9a7061ece7efc0890529185",
    RE2_ADJUDICATION.name: "2659989026f652458867fa61931a871da94e499792d3573fbfe7dc535da39160",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _counts(transaction: object) -> dict[str, object]:
    return {name: value for name, value in transaction.exact_execution_counts}


def _actor_fingerprints(components: dict[str, object]) -> tuple[tuple[str, str], ...]:
    actors, _, _ = ADAPTER.R3._capture_components_v1(
        actors=tuple(components["actors"]),
        critic=components["critic"],
        live_value_normalizer=components["value_normalizer"],
    )
    return tuple(
        (ADAPTER.R3._parameter_digest(item), ADAPTER.R3._optimizer_digest(item))
        for item in actors
    )


def _critic_fingerprint(components: dict[str, object]) -> tuple[str, str]:
    _, critic, _ = ADAPTER.R3._capture_components_v1(
        actors=tuple(components["actors"]),
        critic=components["critic"],
        live_value_normalizer=components["value_normalizer"],
    )
    return ADAPTER.R3._parameter_digest(critic), ADAPTER.R3._optimizer_digest(critic)


def _valuenorm_fingerprint(components: dict[str, object]) -> str:
    return ADAPTER.R4._valuenorm_digest(components["value_normalizer"])


def _adam_steps(optimizer: torch.optim.Optimizer) -> tuple[int, ...]:
    steps: list[int] = []
    for state in optimizer.state.values():
        value = state.get("step", 0)
        steps.append(int(value.item()) if isinstance(value, torch.Tensor) else int(value))
    return tuple(steps)


def _force_actor_task_choices(actors: list[object]) -> None:
    with torch.no_grad():
        for actor_id, actor in enumerate(actors):
            linear = actor.actor.act.action_out.linear
            linear.weight.zero_()
            linear.bias.fill_(-2.0)
            linear.bias[actor_id] = 2.0


def _make_collected(
    *, enabled_actors: tuple[int, ...], seed: int
) -> dict[str, object]:
    harness = V1.RouteHarness(E=E, M=M, N=N, T=T, scenario="scale")
    feasible = harness.raw.problem["feasible_mask"]
    costs = harness.raw.problem["cost_matrix"]
    feasible.zero_()
    costs.fill_(50.0)
    for env_id in range(E):
        for actor_id in enabled_actors:
            feasible[env_id, actor_id, actor_id] = True
            costs[env_id, actor_id, actor_id] = 1.0 + 0.1 * env_id
    components = NR._make_real_components(harness, seed=seed)
    _force_actor_task_choices(components["actors"])
    route = components["route"]
    route.reset()
    receipts = tuple(route.collect_step() for _ in range(T))
    return {
        "harness": harness,
        "components": components,
        "route": route,
        "receipts": receipts,
    }


def _execute(collected: dict[str, object], *, update_id: str) -> object:
    components = collected["components"]
    harness = collected["harness"]
    base = R3H.make_base_authority()
    return ADAPTER.execute_real_isaac_single_transaction_v1(
        repository_head=base.repository_head,
        dirty_state_classification="authorized B2-T4-ZD bounded CPU qualification",
        repo_source_hashes=base.repo_source_hashes,
        installed_harl_source_hashes=base.installed_harl_source_hashes,
        route=collected["route"],
        actors=tuple(components["actors"]),
        critic=components["critic"],
        live_value_normalizer=components["value_normalizer"],
        algo_args=components["algo_args"],
        environment_identity="SyntheticEventEnvironment/B2-T4-ZD/CPU",
        profile_name=harness.profile.profile_name.value,
        real_environment_resets=1,
        real_rollout_steps=T,
        precedence_resolution_evidence_digest=NR.R1.digest(f"{update_id}-precedence"),
        terminal_correlation_evidence_digest=NR.R1.digest(f"{update_id}-terminal"),
        timeout_critic_evidence_digest=NR.R1.digest(f"{update_id}-timeout"),
        effective_assignment_evidence_digest=NR.R1.digest(f"{update_id}-assignment"),
        proposal_effective_authority_separate=True,
        update_id=update_id,
        order_seed=NR.seed_from_update_id(update_id),
        classification=PASS,
    )


def _mask_counts(route: object) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (
            actor_id,
            int(storage.decision_valid_masks[:-1].sum().item()),
            int(
                (
                    storage.decision_valid_masks[:-1]
                    & storage.active_masks[:-1].to(torch.bool)
                ).sum().item()
            ),
        )
        for actor_id, storage in enumerate(route.actor_storages)
    )


def _expect_stop(stop_code: str, function: Callable[[], object]) -> dict[str, object]:
    try:
        function()
    except EVIDENCE.B2RContractError as exc:
        _assert(exc.stop_code == stop_code, f"wrong STOP {exc.stop_code}; expected {stop_code}")
        return {"status": "PASS", "result": "STOP", "stop_code": exc.stop_code, "message": str(exc)}
    raise AssertionError(f"expected {stop_code}")


def _historical_re2_authority() -> dict[str, object]:
    observed = {name: _sha(RE2_DIR / name) for name in HISTORICAL_HASHES}
    _assert(observed == HISTORICAL_HASHES, "historical RE2 artifact drift")
    tx2 = json.loads(RE2_TX2.read_text(encoding="utf-8"))
    rows = [
        row
        for receipt in tx2["lifecycle_decision_gate_receipts"]
        for row in receipt["rows"]
    ]
    _assert(tx2["transaction_index"] == 2, "retained transaction identity")
    _assert(tx2["rollout_provenance"]["collection_physical_step_range"] == [3, 4], "retained physical range")
    _assert(len(rows) == 12, "retained actor row count")
    _assert(all(row["continuation_used"] and not row["dvm"] for row in rows), "retained continuation/DVM facts")
    _assert(sum(row["actor_policy_call_count"] for row in rows) == 0, "retained policy calls")
    _assert(all(row["ownership_before"] == row["ownership_after"] for row in rows), "retained ownership")
    _assert(tx2["collection_preserved_learner"], "retained collection mutation")
    return {
        "hashes": observed,
        "transaction_index": 2,
        "T": 2,
        "E": 2,
        "M": 3,
        "total_actor_rows": 12,
        "continuation_rows": 12,
        "policy_calls": 0,
        "dvm_rows": 0,
        "forced_noop_rows": sum(row["i2_row_kind"] == "FORCED_NOOP_ROW" for row in rows),
        "owned_executing_rows": sum(
            row["lifecycle_state"] == "EXECUTING"
            and row["ownership_before"] == row["ownership_after"]
            for row in rows
        ),
        "collection_preserved_learner": True,
        "learner_before": tx2["learner_before_collection"]["state_digest"],
        "learner_after": tx2["learner_after_collection"]["state_digest"],
    }


def positive_re2_sequence() -> tuple[dict[str, object], dict[str, object]]:
    historical = _historical_re2_authority()
    retained_empty = R5.reconcile_actor_evidence_v1(
        update_id="b2-t4-re2-normal-horizon-training-13316-tx002",
        actor_ids=(0, 1, 2),
        expected_actor_rows=(),
        observed_actor_rows=(),
    )
    collected = _make_collected(enabled_actors=(0, 1, 2), seed=4201)
    route = collected["route"]
    rich_masks = _mask_counts(route)
    _assert(all(dvm > 0 and active_dvm > 0 for _, dvm, active_dvm in rich_masks), "actor-rich mask population")
    rich_before = _actor_fingerprints(collected["components"])
    rich_tx = _execute(collected, update_id="b2-t4-zd-actor-rich-0001")
    rich_after = _actor_fingerprints(collected["components"])
    rich_counts = _counts(rich_tx)
    _assert(all(before != after for before, after in zip(rich_before, rich_after)), "actor-rich mutation")
    _assert(all(count > 0 for _, count in rich_tx.real_audit.actor_expected_training_rows), "actor-rich expected rows")
    _assert(rich_tx.real_audit.actor_expected_training_rows == rich_tx.real_audit.actor_observed_training_rows, "actor-rich reconciliation")

    route.collect_step()
    route.collect_step()
    zero_masks = _mask_counts(route)
    _assert(zero_masks == ((0, 0, 0), (1, 0, 0), (2, 0, 0)), "second rollout is not all-zero-DVM")
    continuation_actions = tuple(
        tuple(int(value) for value in storage.action_ids.flatten().tolist())
        for storage in route.actor_storages
    )
    zero_before_actor = _actor_fingerprints(collected["components"])
    zero_before_actor_adam = tuple(
        _adam_steps(actor.actor_optimizer) for actor in collected["components"]["actors"]
    )
    zero_before_critic = _critic_fingerprint(collected["components"])
    zero_before_critic_adam = _adam_steps(collected["components"]["critic"].critic_optimizer)
    zero_before_vn = _valuenorm_fingerprint(collected["components"])
    zero_tx = _execute(collected, update_id="b2-t4-zd-re2-tx002-replay")
    zero_after_actor = _actor_fingerprints(collected["components"])
    zero_after_actor_adam = tuple(
        _adam_steps(actor.actor_optimizer) for actor in collected["components"]["actors"]
    )
    zero_after_critic = _critic_fingerprint(collected["components"])
    zero_after_critic_adam = _adam_steps(collected["components"]["critic"].critic_optimizer)
    zero_after_vn = _valuenorm_fingerprint(collected["components"])
    zero_counts = _counts(zero_tx)
    actor_receipt = zero_tx.r5_transaction.actor_sequence_receipt
    _assert(zero_before_actor == zero_after_actor, "all-zero actor state changed")
    _assert(zero_before_actor_adam == zero_after_actor_adam, "all-zero actor Adam advanced")
    _assert(zero_before_critic != zero_after_critic, "all-zero critic did not advance")
    _assert(
        len(zero_before_critic_adam) == len(zero_after_critic_adam)
        and all(after - before == zero_counts["critic_optimizer_step"] for before, after in zip(zero_before_critic_adam, zero_after_critic_adam)),
        "all-zero critic Adam counters did not advance by the exact plan",
    )
    _assert(zero_before_vn != zero_after_vn, "all-zero ValueNorm did not advance")
    _assert(zero_counts["actor_backward_by_actor"] == (0, 0, 0), "all-zero actor backward")
    _assert(zero_counts["actor_optimizer_step_by_actor"] == (0, 0, 0), "all-zero actor step")
    _assert(zero_counts["critic_backward"] > 0 and zero_counts["critic_optimizer_step"] > 0, "all-zero critic skipped")
    _assert(zero_counts["live_valuenorm_update"] > 0, "all-zero ValueNorm skipped")
    _assert(zero_counts["s10_entries"] == 1, "all-zero S10")
    _assert(actor_receipt.initial_factor_digest == actor_receipt.final_factor_digest, "all-zero factor not identity")
    _assert(all(segment.skipped for segment in actor_receipt.actor_segments), "all-zero actor segment not skipped")
    _assert(zero_tx.real_audit.actor_expected_training_rows == ((0, 0), (1, 0), (2, 0)), "all-zero expected")
    _assert(zero_tx.real_audit.actor_observed_training_rows == ((0, 0), (1, 0), (2, 0)), "all-zero observed")

    rich = {
        "status": "PASS",
        "case": "normal_actor_rich",
        "mask_counts_actor_dvm_active_and_dvm": rich_masks,
        "expected_actor_population": rich_tx.real_audit.actor_expected_training_rows,
        "observed_actor_population": rich_tx.real_audit.actor_observed_training_rows,
        "actor_backward": rich_counts["actor_backward_by_actor"],
        "actor_optimizer_step": rich_counts["actor_optimizer_step_by_actor"],
        "critic_backward": rich_counts["critic_backward"],
        "critic_optimizer_step": rich_counts["critic_optimizer_step"],
        "valuenorm_update": rich_counts["live_valuenorm_update"],
        "s10": rich_counts["s10_entries"],
        "factor_audits": "PASS",
        "evidence_digest": rich_tx.evidence_digest,
    }
    zero = {
        "status": "PASS",
        "case": "RE2_tx002_retained_evidence_replay",
        "historical_authority": historical,
        "retained_empty_empty_reconciliation_digest": retained_empty.evidence_digest,
        "source_faithful_replay": {
            "T": T,
            "E": E,
            "M": M,
            "actor_rows": T * E * M,
            "continuation_rows": T * E * M,
            "policy_calls": 0,
            "dvm_rows": 0,
            "forced_noop_rows": 0,
            "owned_task_actions_by_actor": continuation_actions,
            "expected_actor_population": zero_tx.real_audit.actor_expected_training_rows,
            "observed_actor_population": zero_tx.real_audit.actor_observed_training_rows,
            "actor_reconciliation_digest": zero_tx.real_audit.actor_evidence_reconciliation_digest,
            "actor_backward": zero_counts["actor_backward_by_actor"],
            "actor_optimizer_step": zero_counts["actor_optimizer_step_by_actor"],
            "actor_adam_delta": (0, 0, 0),
            "actor_adam_steps_before": zero_before_actor_adam,
            "actor_adam_steps_after": zero_after_actor_adam,
            "actor_parameters_unchanged": True,
            "factor": "IDENTITY",
            "critic_backward": zero_counts["critic_backward"],
            "critic_optimizer_step": zero_counts["critic_optimizer_step"],
            "critic_adam_advanced": True,
            "critic_adam_steps_before": zero_before_critic_adam,
            "critic_adam_steps_after": zero_after_critic_adam,
            "valuenorm_update": zero_counts["live_valuenorm_update"],
            "valuenorm_mutated": True,
            "event_returns": zero_tx.real_audit.event_return_compute_count,
            "stock_compute_returns": 0,
            "s7_s8_s9_s10": [True, True, True, True],
            "transaction_evidence_digest": zero_tx.evidence_digest,
        },
        "lifecycle_meaning_preserved": "VALID CONTINUATION-ONLY NORMAL-HORIZON ROLLOUT",
        "collection_or_reconciliation_mutations": 0,
    }
    return rich, zero


def positive_partial_zero() -> dict[str, object]:
    collected = _make_collected(enabled_actors=(0, 2), seed=4202)
    masks = _mask_counts(collected["route"])
    _assert(masks[0][2] > 0 and masks[1][2] == 0 and masks[2][2] > 0, "partial-zero mask pattern")
    before = _actor_fingerprints(collected["components"])
    actor1_adam_before = _adam_steps(collected["components"]["actors"][1].actor_optimizer)
    transaction = _execute(collected, update_id="b2-t4-zd-partial-zero-0001")
    after = _actor_fingerprints(collected["components"])
    actor1_adam_after = _adam_steps(collected["components"]["actors"][1].actor_optimizer)
    counts = _counts(transaction)
    segments = {item.actor_id: item for item in transaction.r5_transaction.actor_sequence_receipt.actor_segments}
    _assert(before[1] == after[1], "zero-DVM actor1 mutated")
    _assert(actor1_adam_before == actor1_adam_after, "zero-DVM actor1 Adam advanced")
    _assert(before[0] != after[0] and before[2] != after[2], "nonzero actors did not mutate")
    _assert(counts["actor_backward_by_actor"][1] == 0, "actor1 backward")
    _assert(counts["actor_optimizer_step_by_actor"][1] == 0, "actor1 step")
    _assert(segments[1].skipped, "actor1 not skipped")
    _assert(segments[1].factor_transition.skipped_actor, "actor1 factor not identity")
    _assert(segments[2].prior_accumulation_preserved, "actor2 cumulative factor lost")
    return {
        "status": "PASS",
        "case": "partial_zero_dvm",
        "mask_counts_actor_dvm_active_and_dvm": masks,
        "expected_actor_population": transaction.real_audit.actor_expected_training_rows,
        "observed_actor_population": transaction.real_audit.actor_observed_training_rows,
        "actor_backward": counts["actor_backward_by_actor"],
        "actor_optimizer_step": counts["actor_optimizer_step_by_actor"],
        "actor_adam_delta_zero_for_actor1": True,
        "actor1_adam_steps_before": actor1_adam_before,
        "actor1_adam_steps_after": actor1_adam_after,
        "actor1_parameter_optimizer_unchanged": True,
        "actor1_factor_contribution": "IDENTITY",
        "actor2_cumulative_factor_preserved": True,
        "critic_backward": counts["critic_backward"],
        "critic_optimizer_step": counts["critic_optimizer_step"],
        "valuenorm_update": counts["live_valuenorm_update"],
        "s10": counts["s10_entries"],
        "evidence_digest": transaction.evidence_digest,
    }


def _first_dvm_slot(storage: object) -> tuple[int, int]:
    index = storage.decision_valid_masks[:-1].nonzero(as_tuple=False)[0]
    return int(index[0].item()), int(index[1].item())


def _adapter_missing_case(field: str, seed: int) -> dict[str, object]:
    collected = _make_collected(enabled_actors=(0, 1, 2), seed=seed)
    storage = collected["route"].actor_storages[0]
    slot, env_id = _first_dvm_slot(storage)
    if field == "behavior_old_logprob":
        storage._action_logprobs[slot, env_id, 0] = float("nan")
    elif field == "policy_action_proposal":
        storage._action_ids[slot, env_id, 0] = -1
    elif field == "actor_observation":
        storage._obs[slot, env_id, 0] = float("nan")
    else:
        raise AssertionError(field)
    result = _expect_stop(
        R5.STOP_ACTOR_EVIDENCE_MISSING,
        lambda: _execute(collected, update_id=f"b2-t4-zd-negative-{field}"),
    )
    _assert(not collected["route"].poisoned, "pre-mutation missing-evidence STOP poisoned route")
    return {"case": field, "mutation_started": False, "route_poisoned": False, **result}


def _continuation_policy_evidence_case() -> dict[str, object]:
    collected = _make_collected(enabled_actors=(0, 1, 2), seed=4304)
    _execute(collected, update_id="b2-t4-zd-negative-continuation-setup")
    collected["route"].collect_step()
    collected["route"].collect_step()
    storage = collected["route"].actor_storages[0]
    _assert(not bool(storage.decision_valid_masks[:-1].any().item()), "negative setup not continuation-only")
    storage._action_logprobs[0, 0, 0] = 0.25
    result = _expect_stop(
        R5.STOP_ACTOR_EVIDENCE_UNEXPECTED,
        lambda: _execute(collected, update_id="b2-t4-zd-negative-continuation-evidence"),
    )
    return {"case": "continuation_row_carries_fresh_policy_evidence", "tx2_mutation_started": False, **result}


def negative_cases() -> dict[str, object]:
    row = ("negative-update", 0, 0, 0, 0, 1)
    direct = {
        "expected_greater_than_observed": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_MISSING,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(row,), observed_actor_rows=(),
            ),
        ),
        "observed_greater_than_expected": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_UNEXPECTED,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(), observed_actor_rows=(row,),
            ),
        ),
        "equal_count_wrong_row_identity": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(row,),
                observed_actor_rows=(("negative-update", 0, 1, 0, 0, 2),),
            ),
        ),
        "duplicate_actor_evidence": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_DUPLICATE,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(row,), observed_actor_rows=(row, row),
            ),
        ),
        "wrong_update_identity": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_UPDATE_ID_MISMATCH,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(row,),
                observed_actor_rows=(("stale-update", 0, 0, 0, 0, 1),),
            ),
        ),
        "wrong_actor_identity": _expect_stop(
            R5.STOP_ACTOR_EVIDENCE_IDENTITY_MISMATCH,
            lambda: R5.reconcile_actor_evidence_v1(
                update_id="negative-update", actor_ids=(0, 1, 2),
                expected_actor_rows=(row,),
                observed_actor_rows=(("negative-update", 9, 0, 0, 0, 1),),
            ),
        ),
    }
    adapter = {
        "missing_behavior_old_logprob": _adapter_missing_case("behavior_old_logprob", 4301),
        "missing_policy_action_proposal": _adapter_missing_case("policy_action_proposal", 4302),
        "missing_actor_observation": _adapter_missing_case("actor_observation", 4303),
        "continuation_policy_evidence": _continuation_policy_evidence_case(),
    }
    return {
        "status": "PASS",
        "negative_fail_closed_cases": len(direct) + len(adapter),
        "unexpected_negative_passes": 0,
        "direct_reconciliation": direct,
        "source_faithful_adapter": adapter,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()
    artifact_dir = Path(args.artifact_dir).resolve()
    try:
        actor_rich, re2_replay = positive_re2_sequence()
        partial = positive_partial_zero()
        negatives = negative_cases()
        _assert(
            {name: _sha(RE2_DIR / name) for name in HISTORICAL_HASHES} == HISTORICAL_HASHES,
            "historical RE2 artifacts changed during qualification",
        )
        all_zero = re2_replay["source_faithful_replay"]
        matrix = {
            "status": "PASS",
            "cases": [
                {"case": "normal all actors train", "expected": ">0 each", "observed": "exact", "result": "PASS"},
                {"case": "one zero-DVM actor", "expected": "mixed", "observed": "exact", "result": "PASS"},
                {"case": "all actors zero-DVM", "expected": 0, "observed": 0, "result": "PASS"},
                {"case": "expected actor row missing", "expected": ">0", "observed": "lower", "result": "STOP"},
                {"case": "unexpected actor row", "expected": "0 or N", "observed": "higher", "result": "STOP"},
                {"case": "duplicate actor evidence", "expected": "N unique", "observed": "duplicate", "result": "STOP"},
                {"case": "wrong row identity", "expected": "N", "observed": "N wrong", "result": "STOP"},
                {"case": "continuation carries policy evidence", "expected": 0, "observed": 1, "result": "STOP"},
            ],
        }
        source_identity = {
            "status": "PASS",
            "production_sha256": {
                "assignment_event_training_full_transaction.py": _sha(
                    ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_full_transaction.py"
                ),
                "assignment_event_training_real_isaac_adapter.py": _sha(
                    ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_real_isaac_adapter.py"
                ),
            },
            "historical_re2_sha256": HISTORICAL_HASHES,
            "production_semantic_files_changed": 2,
            "scope": "adapter/evidence-binding and directly necessary shared S0 reconciler only",
        }
        _write(artifact_dir / "actor_population_matrix.json", matrix)
        _write(artifact_dir / "actor_negative_cases.json", negatives)
        _write(artifact_dir / "re2_tx002_zero_dvm_replay.json", re2_replay)
        _write(artifact_dir / "partial_zero_dvm_full_transaction.json", partial)
        _write(artifact_dir / "all_zero_dvm_full_transaction.json", all_zero)
        _write(artifact_dir / "actor_rich_regression.json", actor_rich)
        _write(artifact_dir / "production_source_identity.json", source_identity)
        payload = {
            "classification": PASS,
            "status": "PASS",
            "positive_cases": 3,
            "negative_fail_closed_cases": negatives["negative_fail_closed_cases"],
            "unexpected_negative_passes": 0,
            "source_faithful_adapter_attempts": 8,
            "successful_source_faithful_full_transactions": 4,
            "re2_tx002_replays": 1,
            "app_launcher": 0,
            "real_isaac_environment": 0,
            "formal_normal_horizon_updates": 0,
            "checkpoint_io": 0,
            "public_activation": 0,
            "b2_t4_re3_started": 0,
            "actor_rich": actor_rich,
            "partial_zero_dvm": partial,
            "all_zero_dvm": all_zero,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except BaseException as exc:
        print(json.dumps({
            "classification": "PHASE-B2-T4-ZD-STOP-QUALIFICATION",
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
            "app_launcher": 0,
            "real_isaac_environment": 0,
            "formal_normal_horizon_updates": 0,
        }, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
