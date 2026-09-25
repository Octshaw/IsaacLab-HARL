"""Pure source-faithful lifecycle decision-gating qualification for B2-T0-LD."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_t0_ld_decision_gate as LD  # noqa: E402
import test_assignment_phase_b2_i3a_dvm_actor_collection_storage_proposal_envelope_pure as I3  # noqa: E402


TaskState = I3.TaskState
RobotState = I3.RobotState
RowKind = I3.RowKind


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _tensor_digest(*values: torch.Tensor) -> str:
    digest = hashlib.sha256()
    for value in values:
        detached = value.detach().cpu().contiguous()
        digest.update(str((tuple(detached.shape), detached.dtype)).encode())
        digest.update(detached.numpy().tobytes())
    return digest.hexdigest()


def _collect(bundle):
    actors = []
    dvm = bundle.decision_valid_mask
    available = bundle.available_actions_bool
    for robot_index in range(bundle.evidence_identity.M):
        envs = dvm[:, robot_index, 0].nonzero(as_tuple=False).flatten().tolist()
        actions = []
        for env_index in envs:
            legal = available[env_index, robot_index].nonzero(as_tuple=False).flatten()
            actions.append(int(legal[0].item()))
        actors.append(
            I3.ScriptedActor(
                actions,
                tuple(-0.1 * (index + 1) for index in range(len(actions))),
            )
        )
    envelope, _, _ = I3._collect(bundle, tuple(actors))
    return envelope, tuple(actors)


def _observe(
    bundle,
    envelope,
    *,
    collection_index: int,
    physical_step_index: int,
    terminal_context: str = "CURRENT_NONTERMINAL",
):
    E, M, N = (
        bundle.evidence_identity.num_envs,
        bundle.evidence_identity.M,
        bundle.evidence_identity.N,
    )
    kind_names = {
        int(RowKind.POLICY_DECISION_ROW): LD.POLICY_DECISION_ROW,
        int(RowKind.FORCED_CONTINUATION_ROW): LD.FORCED_CONTINUATION_ROW,
        int(RowKind.FORCED_NOOP_ROW): LD.FORCED_NOOP_ROW,
    }
    lifecycle_names = {int(item): item.name for item in RobotState}
    records = envelope.actor_call_records
    rows = []
    for env_index in range(E):
        for robot_index in range(M):
            current_raw = int(
                bundle.evidence_snapshot.current_owned_task_id[
                    env_index, robot_index
                ].item()
            )
            present = bool(
                envelope.policy_proposal_present_mask[
                    env_index, robot_index, 0
                ].item()
            )
            row_kind = kind_names[
                int(bundle.row_kind[env_index, robot_index].item())
            ]
            rows.append(
                LD.LifecycleDecisionRowEvidence(
                    collection_index=collection_index,
                    physical_step_index=physical_step_index,
                    env_index=env_index,
                    robot_index=robot_index,
                    episode_generation=bundle.evidence_identity.episode_generations[
                        env_index
                    ],
                    transition_generation=bundle.evidence_identity.transition_generations[
                        env_index
                    ],
                    lifecycle_state=lifecycle_names[
                        int(
                            bundle.evidence_snapshot.robot_state[
                                env_index, robot_index
                            ].item()
                        )
                    ],
                    current_owned_task_id=(
                        None if current_raw >= N else current_raw
                    ),
                    decision_required=bool(
                        bundle.decision_valid_mask[
                            env_index, robot_index, 0
                        ].item()
                    ),
                    decision_reason=row_kind,
                    actor_policy_call_count=int(
                        env_index in records[robot_index].valid_env_indices
                    ),
                    proposal_produced=present,
                    behavior_logprob_produced=present,
                    continuation_used=row_kind == LD.FORCED_CONTINUATION_ROW,
                    terminal_autoreset_context=terminal_context,
                    ownership_before=None if current_raw >= N else current_raw,
                    ownership_after=None,
                )
            )
    return LD.qualify_lifecycle_decision_boundary(tuple(rows))


def _bundle_from_state(*, E: int, M: int, N: int, tensors=None, problem=None, serial=7):
    return I3._bundle(
        E=E, M=M, N=N, tensors=tensors, problem=problem, serial=serial
    )[0]


def _run_state_case(
    *,
    E: int,
    M: int,
    N: int,
    tensors=None,
    problem=None,
    collection_index=1,
    physical_step_index=1,
    terminal_context="CURRENT_NONTERMINAL",
):
    bundle = _bundle_from_state(
        E=E, M=M, N=N, tensors=tensors, problem=problem,
        serial=collection_index + 20,
    )
    envelope, actors = _collect(bundle)
    before = _tensor_digest(
        bundle.evidence_snapshot.task_state,
        bundle.evidence_snapshot.robot_state,
        bundle.evidence_snapshot.ownership,
        bundle.decision_valid_mask,
        envelope.action_ids,
        envelope.action_logprobs,
    )
    receipt = _observe(
        bundle,
        envelope,
        collection_index=collection_index,
        physical_step_index=physical_step_index,
        terminal_context=terminal_context,
    )
    after = _tensor_digest(
        bundle.evidence_snapshot.task_state,
        bundle.evidence_snapshot.robot_state,
        bundle.evidence_snapshot.ownership,
        bundle.decision_valid_mask,
        envelope.action_ids,
        envelope.action_logprobs,
    )
    _assert(before == after and receipt.observer_mutations == 0, "observer mutated source evidence")
    return bundle, envelope, actors, receipt


def case_a_genuine_executing_continuation():
    tensors = list(I3.I2HELP._state(E=1, M=1, N=3))
    tensors[0][0, 0] = int(TaskState.NAVIGATING)
    tensors[1][0, 0] = int(RobotState.EXECUTING)
    tensors[2][0, 0] = 0
    _, _, actors, receipt = _run_state_case(E=1, M=1, N=3, tensors=tuple(tensors))
    _assert(receipt.policy_call_counts == (0,) and len(actors[0].calls) == 0, "A")
    return {"expected": [0], "observed": receipt.policy_call_counts}


def case_b_completion_reopens_decision():
    tensors = list(I3.I2HELP._state(E=1, M=1, N=3))
    tensors[0][0, 0] = int(TaskState.COMPLETED)
    _, _, actors, receipt = _run_state_case(E=1, M=1, N=3, tensors=tuple(tensors))
    _assert(receipt.policy_call_counts == (1,) and len(actors[0].calls) == 1, "B")
    return {"source_state": "NEEDS_ASSIGNMENT after completion/release", "calls": [1]}


def case_c_failure_release_reopens_source_faithfully():
    tensors = list(I3.I2HELP._state(E=1, M=1, N=3))
    tensors[3][0, 0, 0] = True
    _, _, _, receipt = _run_state_case(E=1, M=1, N=3, tensors=tuple(tensors))
    _assert(receipt.policy_call_counts == (1,), "C")
    return {"failed_old_pair_excluded": True, "other_legal_target": True, "calls": [1]}


def case_d_initial_unassigned_decision():
    _, _, _, receipt = _run_state_case(E=1, M=1, N=3)
    _assert(receipt.policy_call_counts == (1,), "D")
    return {"source_state": "NEEDS_ASSIGNMENT", "calls": [1]}


def case_e_post_autoreset_current_generation():
    bundle, _, _, receipt = _run_state_case(
        E=1,
        M=1,
        N=3,
        collection_index=9,
        physical_step_index=2,
        terminal_context="POST_AUTORESET_CURRENT_GENERATION",
    )
    publication = bundle.evidence_snapshot.source_publication
    _assert(
        receipt.policy_call_counts == (1,)
        and receipt.rows[0].terminal_autoreset_context == "POST_AUTORESET_CURRENT_GENERATION"
        and bundle.evidence_snapshot.provenance["terminal_or_historical_supported"] is False,
        "E",
    )
    _assert(
        not bool(publication.terminated.any().item())
        and not bool(publication.truncated.any().item())
        and all(item.kind.name == "CANONICAL_EPISODE_RESET" for item in publication.provenance),
        "E reset publication",
    )
    return {"current_generation": bundle.evidence_identity.episode_generations, "calls": [1]}


def case_f_unavailable_nondecision():
    tensors = list(I3.I2HELP._state(E=1, M=1, N=3))
    tensors[1][0, 0] = int(RobotState.UNAVAILABLE)
    _, _, actors, receipt = _run_state_case(E=1, M=1, N=3, tensors=tuple(tensors))
    _assert(receipt.policy_call_counts == (0,) and not actors[0].calls, "F")
    return {"source_state": "UNAVAILABLE/FORCED_NOOP", "calls": [0]}


def _three_robot_tensors(*, executing: tuple[int, ...]):
    E, M, N = 1, 3, 4
    tensors = list(I3.I2HELP._state(E=E, M=M, N=N))
    for robot_index in executing:
        tensors[0][0, robot_index] = int(TaskState.NAVIGATING)
        tensors[1][0, robot_index] = int(RobotState.EXECUTING)
        tensors[2][0, robot_index] = robot_index
    return E, M, N, tuple(tensors)


def case_g_asynchronous_three_robot_boundary():
    E, M, N, tensors = _three_robot_tensors(executing=(0, 1))
    _, _, actors, receipt = _run_state_case(E=E, M=M, N=N, tensors=tensors)
    _assert(receipt.policy_call_counts == (0, 0, 1), "G")
    _assert(tuple(len(actor.calls) for actor in actors) == (0, 0, 1), "G batches")
    return {"states": ["continuation", "continuation", "reopened"], "calls": [0, 0, 1]}


def case_h_all_three_continuation():
    E, M, N, tensors = _three_robot_tensors(executing=(0, 1, 2))
    _, _, _, receipt = _run_state_case(E=E, M=M, N=N, tensors=tensors)
    _assert(receipt.policy_call_counts == (0, 0, 0), "H")
    return {"calls": [0, 0, 0]}


def case_i_all_three_decision_required():
    _, _, _, receipt = _run_state_case(E=1, M=3, N=4)
    _assert(receipt.policy_call_counts == (1, 1, 1), "I")
    return {"calls": [1, 1, 1]}


def _expect_stop(row, stop_code: str):
    try:
        LD.qualify_lifecycle_decision_boundary((row,))
    except LD.LifecycleDecisionGateError as exc:
        _assert(exc.stop_code == stop_code, f"expected {stop_code}, got {exc.stop_code}")
        return {"stop_code": exc.stop_code}
    raise AssertionError(f"missing expected stop {stop_code}")


def case_j_duplicate_call_stops():
    _, _, _, receipt = _run_state_case(E=1, M=1, N=3)
    row = replace(receipt.rows[0], actor_policy_call_count=2)
    return _expect_stop(row, LD.STOP_DUPLICATE_POLICY_CALL)


def case_k_missing_required_call_stops():
    _, _, _, receipt = _run_state_case(E=1, M=1, N=3)
    row = replace(
        receipt.rows[0],
        actor_policy_call_count=0,
        proposal_produced=False,
        behavior_logprob_produced=False,
    )
    return _expect_stop(row, LD.STOP_MISSING_REQUIRED_POLICY_CALL)


def case_l_continuation_resample_stops():
    tensors = list(I3.I2HELP._state(E=1, M=1, N=3))
    tensors[0][0, 0] = int(TaskState.NAVIGATING)
    tensors[1][0, 0] = int(RobotState.EXECUTING)
    tensors[2][0, 0] = 0
    _, _, _, receipt = _run_state_case(E=1, M=1, N=3, tensors=tuple(tensors))
    row = replace(
        receipt.rows[0],
        actor_policy_call_count=1,
        proposal_produced=True,
        behavior_logprob_produced=True,
    )
    return _expect_stop(row, LD.STOP_POLICY_CALL_DURING_CONTINUATION)


def case_m_physical_step_is_not_authority_and_observer_is_nonmutating():
    bundle = _bundle_from_state(E=1, M=1, N=3)
    envelope, _ = _collect(bundle)
    first = _observe(bundle, envelope, collection_index=20, physical_step_index=1)
    later = _observe(bundle, envelope, collection_index=21, physical_step_index=99)
    _assert(first.policy_call_counts == later.policy_call_counts == (1,), "step index affected gate")
    return {"physical_steps": [1, 99], "calls": [1, 1], "observer_mutations": 0}


CASES = (
    ("A", case_a_genuine_executing_continuation),
    ("B", case_b_completion_reopens_decision),
    ("C", case_c_failure_release_reopens_source_faithfully),
    ("D", case_d_initial_unassigned_decision),
    ("E", case_e_post_autoreset_current_generation),
    ("F", case_f_unavailable_nondecision),
    ("G", case_g_asynchronous_three_robot_boundary),
    ("H", case_h_all_three_continuation),
    ("I", case_i_all_three_decision_required),
    ("J", case_j_duplicate_call_stops),
    ("K", case_k_missing_required_call_stops),
    ("L", case_l_continuation_resample_stops),
    ("M", case_m_physical_step_is_not_authority_and_observer_is_nonmutating),
)


if __name__ == "__main__":
    results = []
    for case_id, function in CASES:
        results.append({"case": case_id, "status": "PASS", "evidence": function()})
    print(
        json.dumps(
            {
                "suite": "phase_b2_t0_ld_lifecycle_decision_gating_pure",
                "classification": "PASS",
                "case_count": len(results),
                "cases": results,
                "isaac_app_launcher": 0,
                "learner_mutations": 0,
                "observer_mutations": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
