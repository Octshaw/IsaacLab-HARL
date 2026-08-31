"""Synthetic B2-I3a DVM subset collection, storage, and envelope regressions."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
I2_FIXTURE_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b2_i2_lifecycle_legality_dvm_row_plan_decision_bundle_pure.py"
COLLECTION_PATH = SCAN_SOURCE / "assignment_event_actor_collection.py"
DEVICE = torch.device("cpu")

REPO_PROTECTED_HASHES = {
    "assignment_event_policy_decision.py": "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
    "assignment_event_policy_evidence.py": "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
    "assignment_event_profile_schema_contract_v2.py": "9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955",
    "assignment_event_profile_schema_contract.py": "04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef",
    "assignment_mrta_contract.py": "73881d20903873ddaaf7b6b6636d008771c030f739d3d2cc8ebb32b79bd1e17c",
    "assignment_profile_contract.py": "ece4a58c1636ea3f710775eaac25e12df4097972ef57ec0d15cefec5e6702500",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    "assignment_event_runtime_facade.py": "036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478",
    "assignment_event_proposal_adapter.py": "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    "assignment_initial_claim_runtime.py": "c74868c84a803108c424827afe9326393428938dce4f6cbd46693da3d4d94fda",
    "assignment_lifecycle_transaction_runtime.py": "2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de",
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
HARL_PROTECTED_HASHES = {
    "algorithms/actors/on_policy_base.py": "ab5a1c785402efd4bd8a56b0b60503a12b365dbb422ca06ba9afee648471cd2c",
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "common/buffers/on_policy_actor_buffer.py": "a7352b59d8fa28b96e28e3021ddeaa9f8da5944c686651b1c04b0ec26c96f8cc",
    "models/policy_models/stochastic_policy.py": "e8744557a8c9ed79261702660836e7e3ff55e78de1d18e3b77cdd7cec9f52c35",
    "models/base/act.py": "807342555af8819894750c5171cf3c0ba2b7f18e913cc51b3e0faa7991211915",
    "models/base/distributions.py": "086b4c05eb3ad511b0728c9720d1bec70354a967d62a01fe854b3ca4503576cf",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_namespace_packages() -> None:
    for name, path in (
        ("isaaclab_tasks", TASKS_SOURCE),
        ("isaaclab_tasks.direct", DIRECT_SOURCE),
        (PACKAGE, SCAN_SOURCE),
    ):
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]
        sys.modules[name] = module


def _load_path(key: str, path: Path):
    existing = sys.modules.get(key)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(key, path)
    _assert(spec is not None and spec.loader is not None, f"loader missing: {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace_packages()
I2HELP = _load_path("assignment_b2_i2_fixture_helpers", I2_FIXTURE_PATH)
DECISION = I2HELP.DECISION
EVIDENCE = I2HELP.EVIDENCE
TRANSITION = I2HELP.TRANSITION
COLLECTION = _load_path(f"{PACKAGE}.assignment_event_actor_collection", COLLECTION_PATH)
TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
RowKind = DECISION.EventPolicyRowKind


def _bundle(*, E: int, M: int, N: int, tensors=None, problem=None, serial: int = 7):
    snapshot, raw_problem, publication, lifecycle, open_view, window = I2HELP._snapshot(
        E=E, M=M, N=N, tensors=tensors, problem=problem, serial=serial
    )
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(
        evidence_snapshot=snapshot
    )
    return bundle, raw_problem, publication, lifecycle, open_view, window


def _mixed_bundle(*, serial: int = 10):
    E, M, N = 4, 3, 4
    tensors = list(I2HELP._state(E=E, M=M, N=N))
    tensors[1][:] = torch.tensor(
        [
            [int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK), int(RobotState.UNAVAILABLE)],
            [int(RobotState.WAITING_FOR_TASK), int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK)],
            [int(RobotState.EXECUTING), int(RobotState.UNAVAILABLE), int(RobotState.UNAVAILABLE)],
            [int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK), int(RobotState.NEEDS_ASSIGNMENT)],
        ],
        dtype=torch.int64,
    )
    tensors[0][2, 0] = int(TaskState.NAVIGATING)
    tensors[2][2, 0] = 0
    problem = I2HELP._problem(E=E, M=M, N=N)
    problem["feasible_mask"][3, 2].zero_()
    return _bundle(E=E, M=M, N=N, tensors=tuple(tensors), problem=problem, serial=serial)


class ScriptedActor:
    def __init__(self, actions, logprobs, *, rnn_increment: float = 1.0, mode: str = "ok") -> None:
        self.actions = actions
        self.logprobs = logprobs
        self.rnn_increment = rnn_increment
        self.mode = mode
        self.calls = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        self.calls.append(
            {
                "obs": obs.clone(),
                "rnn_states": rnn_states.clone(),
                "masks": masks.clone(),
                "available_actions": available_actions.clone(),
                "deterministic": deterministic,
            }
        )
        K = obs.shape[0]
        if self.mode == "wrong_tuple":
            return (torch.zeros((K, 1), dtype=torch.int64),)
        action = torch.as_tensor(self.actions, device=obs.device).reshape(-1, 1)
        logprob = torch.as_tensor(self.logprobs, dtype=torch.float32, device=obs.device).reshape(-1, 1)
        next_rnn = rnn_states + self.rnn_increment
        if self.mode == "wrong_batch":
            action = torch.zeros((K + 1, 1), dtype=torch.int64, device=obs.device)
        elif self.mode == "wrong_shape":
            action = torch.zeros((K,), dtype=torch.int64, device=obs.device)
        elif self.mode == "nonintegral":
            action = torch.full((K, 1), 0.5, dtype=torch.float32, device=obs.device)
        elif self.mode == "nan_logprob":
            logprob = torch.full((K, 1), float("nan"), dtype=torch.float32, device=obs.device)
        elif self.mode == "inf_logprob":
            logprob = torch.full((K, 1), float("inf"), dtype=torch.float32, device=obs.device)
        elif self.mode == "wrong_rnn":
            next_rnn = torch.zeros((K + 1, *rnn_states.shape[1:]), dtype=torch.float32, device=obs.device)
        return action, logprob, next_rnn


def _state_inputs(bundle, *, R: int = 1, H: int = 5):
    E, M = bundle.evidence_identity.num_envs, bundle.evidence_identity.M
    rnn = torch.arange(E * M * R * H, dtype=torch.float32).reshape(E, M, R, H)
    masks = torch.ones((E, M, 1), dtype=torch.float32)
    return rnn, masks


def _collect(bundle, actors, *, R: int = 1, H: int = 5):
    rnn, masks = _state_inputs(bundle, R=R, H=H)
    envelope = COLLECTION.collect_event_policy_proposals_v2(
        decision_bundle=bundle,
        actors=actors,
        rnn_states=rnn,
        masks=masks,
    )
    return envelope, rnn, masks


def _expect_failure(code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except COLLECTION.EventPolicyActorCollectionError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    else:
        raise AssertionError(f"expected failure {code}")


def test_policy_subset_mixed_rows_zero_valid_and_fixed_scatter() -> None:
    bundle, *_ = _mixed_bundle()
    actors = (
        ScriptedActor([1, 2], [-0.11, -0.22], rnn_increment=10.0),
        ScriptedActor([3], [-0.33], rnn_increment=20.0),
        ScriptedActor([], [], rnn_increment=30.0),
    )
    envelope, initial_rnn, _ = _collect(bundle, actors)
    _assert(tuple(record.valid_env_indices for record in envelope.actor_call_records) == ((0, 3), (1,), ()), "per-agent gather indices")
    _assert(tuple(len(actor.calls) for actor in actors) == (1, 1, 0), "actor bypass counts")
    _assert(actors[0].calls[0]["obs"].shape[0] == 2, "agent0 full-E call")
    _assert(actors[1].calls[0]["obs"].shape[0] == 1, "agent1 full-E call")
    _assert(actors[0].calls[0]["deterministic"] is False, "actor not stochastic")
    actions = envelope.action_ids[..., 0]
    _assert((int(actions[0, 0]), int(actions[3, 0])) == (1, 2), "agent0 scatter")
    _assert(int(actions[1, 1]) == 3, "agent1 scatter")
    _assert(int(actions[2, 0]) == 0, "continuation forced route")
    _assert(int(actions[1, 0]) == 4, "forced noop route")
    logs = envelope.action_logprobs[..., 0]
    _assert(torch.allclose(logs[[0, 3], 0], torch.tensor([-0.11, -0.22])), "agent0 logprob scatter")
    _assert(float(logs[1, 1]) == torch.tensor(-0.33).item(), "agent1 logprob scatter")
    _assert(bool((logs[envelope.forced_row_mask[..., 0]] == 0.0).all().item()), "forced sentinel")
    _assert(torch.equal(envelope.next_rnn_states[1, 0], initial_rnn[1, 0]), "forced RNN changed")
    _assert(torch.equal(envelope.next_rnn_states[0, 0], initial_rnn[0, 0] + 10.0), "policy RNN not scattered")


def test_fixed_shapes_dtypes_and_original_proposal_ledger() -> None:
    bundle, *_ = _mixed_bundle()
    actors = (ScriptedActor([1, 2], [-1.1, -1.2]), ScriptedActor([3], [-1.3]), ScriptedActor([], []))
    envelope, *_ = _collect(bundle, actors)
    _assert(tuple(envelope.action_ids.shape) == (4, 3, 1), "action shape")
    _assert(tuple(envelope.action_logprobs.shape) == (4, 3, 1), "logprob shape")
    _assert(envelope.action_ids.dtype is torch.int64, "action dtype")
    _assert(envelope.runner_actions.dtype is torch.float32, "runner action dtype")
    _assert(envelope.action_logprobs.dtype is torch.float32, "logprob dtype")
    _assert(torch.equal(envelope.policy_proposal_present_mask, bundle.policy_proposal_present_mask), "proposal mask")
    _assert(torch.equal(envelope.sampled_policy_row_mask, bundle.decision_valid_mask), "sampled row mask")
    policy_rows = bundle.decision_valid_mask
    _assert(bool((bundle.forced_action_id[policy_rows] == -1).all().item()), "policy forced sentinel")
    _assert(bool((envelope.action_ids[policy_rows] >= 0).all().item()), "policy used forced sentinel")
    proposal = envelope.original_policy_proposal_ids
    _assert(torch.equal(proposal >= 0, envelope.policy_proposal_present_mask), "proposal ledger mask")
    _assert(bool((proposal[envelope.forced_row_mask] == -1).all().item()), "fake forced proposal")
    _assert(envelope.provenance["original_action_and_behavior_logprob_preserved"] is True, "proposal substitution")


def test_same_task_conflict_preserves_both_samples_and_logprobs() -> None:
    bundle, *_ = _bundle(E=1, M=2, N=2, serial=30)
    actors = (ScriptedActor([0], [-0.4]), ScriptedActor([0], [-0.8]))
    envelope, *_ = _collect(bundle, actors)
    _assert(tuple(int(item) for item in envelope.action_ids[0, :, 0]) == (0, 0), "same-task arbitration occurred")
    _assert(torch.allclose(envelope.action_logprobs[0, :, 0], torch.tensor([-0.4, -0.8])), "original logprobs lost")
    _assert(bool(envelope.policy_proposal_present_mask.all().item()), "conflict row became forced")
    _assert(envelope.provenance["resolver_i4_2_m1_b1_controller_or_env_step"] is False, "resolver executed")


def test_forced_rows_never_call_actor_or_become_policy_evidence() -> None:
    E, M, N = 2, 2, 3
    tensors = list(I2HELP._state(E=E, M=M, N=N))
    tensors[1][:] = torch.tensor(
        [[int(RobotState.EXECUTING), int(RobotState.WAITING_FOR_TASK)], [int(RobotState.UNAVAILABLE), int(RobotState.WAITING_FOR_TASK)]],
        dtype=torch.int64,
    )
    tensors[0][0, 1] = int(TaskState.CLAIMED)
    tensors[2][0, 1] = 0
    bundle, *_ = _bundle(E=E, M=M, N=N, tensors=tuple(tensors), serial=40)
    actors = (ScriptedActor([], []), ScriptedActor([], []))
    envelope, *_ = _collect(bundle, actors)
    _assert(tuple(len(actor.calls) for actor in actors) == (0, 0), "forced actor called")
    _assert(tuple(int(item) for item in envelope.action_ids[:, 0, 0]) == (1, N), "forced routing")
    _assert(not bool(envelope.policy_proposal_present_mask.any().item()), "forced proposal present")
    _assert(bool((envelope.action_logprobs == 0.0).all().item()), "forced logprob sentinel")
    _assert(envelope.provenance["forced_logprob_is_behavior_evidence"] is False, "sentinel became logprob")


def test_historical_available_action_validation_and_masked_sample_failure() -> None:
    problem = I2HELP._problem(E=1, M=1, N=3)
    problem["feasible_mask"].zero_()
    problem["feasible_mask"][0, 0, 0] = True
    bundle, *_ = _bundle(E=1, M=1, N=3, problem=problem, serial=50)
    valid = (ScriptedActor([0], [-0.1]),)
    envelope, *_ = _collect(bundle, valid)
    _assert(int(envelope.action_ids[0, 0, 0]) == 0, "legal sample lost")
    invalid = (ScriptedActor([1], [-0.1]),)
    _expect_failure("actor_sampled_masked_action", lambda: _collect(bundle, invalid))


def test_malformed_actor_outputs_fail_closed() -> None:
    problem = I2HELP._problem(E=1, M=1, N=2)
    bundle, *_ = _bundle(E=1, M=1, N=2, problem=problem, serial=60)
    cases = (
        ("actor_result_contract", ScriptedActor([0], [-0.1], mode="wrong_tuple")),
        ("actor_action_contract", ScriptedActor([0], [-0.1], mode="wrong_batch")),
        ("actor_action_contract", ScriptedActor([0], [-0.1], mode="wrong_shape")),
        ("actor_action_not_integral", ScriptedActor([0], [-0.1], mode="nonintegral")),
        ("actor_action_out_of_range", ScriptedActor([3], [-0.1])),
        ("nonfinite_collection_tensor", ScriptedActor([0], [-0.1], mode="nan_logprob")),
        ("nonfinite_collection_tensor", ScriptedActor([0], [-0.1], mode="inf_logprob")),
        ("collection_tensor_contract", ScriptedActor([0], [-0.1], mode="wrong_rnn")),
    )
    for code, actor in cases:
        _expect_failure(code, lambda actor=actor: _collect(bundle, (actor,)))


def test_exact_bundle_identity_chain_and_no_rebind() -> None:
    bundle_a, *_ = _bundle(E=1, M=2, N=2, serial=70)
    bundle_b, *_ = _bundle(E=1, M=2, N=2, serial=80)
    _assert(torch.equal(bundle_a.evidence_snapshot.actor_obs, bundle_b.evidence_snapshot.actor_obs), "same-value control")
    actors = (ScriptedActor([0], [-0.1]), ScriptedActor([1], [-0.2]))
    envelope, *_ = _collect(bundle_a, actors)
    envelope.validate_decision_bundle(bundle_a)
    _expect_failure("decision_bundle_identity_mismatch", lambda: envelope.validate_decision_bundle(bundle_b))
    _assert(envelope.evidence_identity is bundle_a.evidence_identity, "I0-I3 identity chain")
    _assert(envelope.decision_bundle is bundle_a, "I2-I3 bundle chain")
    _assert(envelope.decision_bundle.evidence_snapshot is bundle_a.evidence_snapshot, "I1-I2 chain")


def test_envelope_immutability_and_historical_binding() -> None:
    bundle, *_ = _mixed_bundle(serial=90)
    actors = (ScriptedActor([1, 2], [-0.1, -0.2]), ScriptedActor([3], [-0.3]), ScriptedActor([], []))
    envelope, *_ = _collect(bundle, actors)
    action_before = envelope.action_ids
    log_before = envelope.action_logprobs
    proposal_before = envelope.policy_proposal_present_mask
    envelope.action_ids.fill_(99)
    envelope.action_logprobs.fill_(float("nan"))
    envelope.policy_proposal_present_mask.logical_not_()
    envelope.historical_available_actions.zero_()
    envelope.historical_actor_obs.zero_()
    _assert(torch.equal(envelope.action_ids, action_before), "action alias")
    _assert(torch.equal(envelope.action_logprobs, log_before), "logprob alias")
    _assert(torch.equal(envelope.policy_proposal_present_mask, proposal_before), "proposal mask alias")
    _assert(torch.equal(envelope.historical_available_actions, bundle.runner_available_actions), "historical mask alias")


def test_slot_zero_and_t_tplus1_alignment() -> None:
    current, *_ = _mixed_bundle(serial=100)
    actors = (ScriptedActor([1, 2], [-0.1, -0.2]), ScriptedActor([3], [-0.3]), ScriptedActor([], []))
    envelope, *_ = _collect(current, actors)
    initial_active = torch.tensor([[0.0], [1.0], [0.0], [1.0]], dtype=torch.float32)
    storage = COLLECTION.create_event_policy_actor_slot_storage_v2(
        episode_length=2,
        agent_id=0,
        current_decision_bundle=current,
        initial_active_masks=initial_active,
    )
    current_obs = current.evidence_snapshot.actor_obs[:, 0]
    current_available = current.runner_available_actions[:, 0]
    current_dvm = current.decision_valid_mask[:, 0]
    _assert(torch.equal(storage.obs[0], current_obs), "slot0 obs")
    _assert(torch.equal(storage.available_actions[0], current_available), "slot0 available")
    _assert(torch.equal(storage.decision_valid_masks[0], current_dvm), "slot0 DVM")
    _assert(torch.equal(storage.active_masks[0], initial_active), "active mask replaced")
    _assert(not torch.equal(storage.active_masks[0].to(torch.bool), storage.decision_valid_masks[0]), "active mask equals DVM")

    next_tensors = list(I2HELP._state(E=4, M=3, N=4))
    next_tensors[1].fill_(int(RobotState.WAITING_FOR_TASK))
    next_problem = I2HELP._problem(E=4, M=3, N=4)
    next_problem["base_pos"].add_(100.0)
    next_bundle, *_ = _bundle(E=4, M=3, N=4, tensors=tuple(next_tensors), problem=next_problem, serial=110)
    next_active = torch.tensor([[1.0], [0.0], [1.0], [0.0]], dtype=torch.float32)
    storage.insert_transition(
        slot=0,
        proposal_envelope=envelope,
        next_decision_bundle=next_bundle,
        next_active_masks=next_active,
    )
    _assert(torch.equal(storage.action_ids[0], envelope.action_ids[:, 0]), "action slot t")
    _assert(torch.equal(storage.action_logprobs[0], envelope.action_logprobs[:, 0]), "logprob slot t")
    _assert(torch.equal(storage.decision_valid_masks[0], current_dvm), "DVM shifted from t")
    _assert(torch.equal(storage.available_actions[0], current_available), "historical mask overwritten")
    _assert(torch.equal(storage.decision_valid_masks[1], next_bundle.decision_valid_mask[:, 0]), "next DVM not at t+1")
    _assert(torch.equal(storage.available_actions[1], next_bundle.runner_available_actions[:, 0]), "next mask not at t+1")
    _assert(torch.equal(storage.active_masks[1], next_active), "next active mask")
    _assert(storage.decision_bundle_refs[0] is current and storage.decision_bundle_refs[1] is next_bundle, "slot bundle identity")


def test_slot_rejects_shift_and_wrong_current_envelope() -> None:
    current, *_ = _bundle(E=1, M=1, N=2, serial=120)
    other, *_ = _bundle(E=1, M=1, N=2, serial=130)
    envelope, *_ = _collect(other, (ScriptedActor([0], [-0.2]),))
    storage = COLLECTION.create_event_policy_actor_slot_storage_v2(
        episode_length=2,
        agent_id=0,
        current_decision_bundle=current,
        initial_active_masks=torch.ones((1, 1), dtype=torch.float32),
    )
    _expect_failure(
        "slot_alignment",
        lambda: storage.insert_transition(slot=1, proposal_envelope=envelope, next_decision_bundle=other, next_active_masks=torch.ones((1, 1))),
    )
    _expect_failure(
        "decision_bundle_identity_mismatch",
        lambda: storage.insert_transition(slot=0, proposal_envelope=envelope, next_decision_bundle=other, next_active_masks=torch.ones((1, 1))),
    )


def test_no_lifecycle_recapture_or_i42_execution_static() -> None:
    source = COLLECTION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    forbidden_import_suffixes = (
        "assignment_initial_claim_runtime",
        "assignment_interstep_claim_window_runtime",
        "assignment_event_proposal_adapter",
        "assignment_lifecycle_transaction_runtime",
        "scan_mobile_manipulator_env",
    )
    _assert(not any(name.endswith(forbidden_import_suffixes) for name in imports), "lifecycle/I4 import")
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    _assert(not calls.intersection({"resolve", "commit", "step", "evaluate_actions", "update", "backward"}), f"forbidden execution call: {calls}")
    _assert("source_publication" not in source and "source_window_identity" not in source, "identity recapture")
    _assert("active_masks = decision_valid" not in source, "active mask replacement")


def test_no_lifecycle_problem_or_open_recapture_dynamic() -> None:
    bundle, problem, _, lifecycle, open_view, _ = _bundle(E=1, M=2, N=3, serial=135)
    reads_before = dict(problem.reads)
    actor_obs_before = bundle.evidence_snapshot.actor_obs
    available_before = bundle.available_actions_bool
    dict.__getitem__(problem, "feasible_mask").zero_()
    dict.__getitem__(problem, "cost_matrix").add_(10000.0)
    lifecycle._robot_state.fill_(int(RobotState.UNAVAILABLE))
    object.__setattr__(open_view, "window", object())
    actors = (ScriptedActor([0], [-0.1]), ScriptedActor([1], [-0.2]))
    envelope, *_ = _collect(bundle, actors)
    _assert(problem.reads == reads_before, f"problem recaptured: {problem.reads}")
    _assert(tuple(len(actor.calls) for actor in actors) == (1, 1), "P2/OPEN recapture changed DVM")
    _assert(torch.equal(envelope.historical_actor_obs, actor_obs_before), "actor obs recaptured")
    _assert(torch.equal(envelope.decision_bundle.available_actions_bool, available_before), "legality recaptured")


class Box:
    def __init__(self, shape) -> None:
        self.shape = shape


class Discrete:
    def __init__(self, n: int) -> None:
        self.n = n


class CountingInstalledActor:
    def __init__(self, actor) -> None:
        self.actor = actor
        self.calls = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        self.calls.append((obs.clone(), available_actions.clone(), deterministic))
        return self.actor.get_actions(obs, rnn_states, masks, available_actions, deterministic)


def _happo_args():
    return {
        "hidden_sizes": [32, 32],
        "activation_func": "relu",
        "use_feature_normalization": True,
        "initialization_method": "orthogonal_",
        "gain": 0.01,
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "data_chunk_length": 10,
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


def test_installed_harl_happo_component_subset_smoke_no_update() -> None:
    from harl.algorithms.actors.happo import HAPPO

    bundle, *_ = _mixed_bundle(serial=140)
    O = int(bundle.evidence_snapshot.actor_obs.shape[-1])
    N = bundle.evidence_identity.N
    torch.manual_seed(1234)
    raw_actors = [HAPPO(_happo_args(), Box((O,)), Discrete(N + 1), device=DEVICE) for _ in range(3)]
    actors = tuple(CountingInstalledActor(actor) for actor in raw_actors)
    before = [tuple(parameter.detach().clone() for parameter in actor.actor.actor.parameters()) for actor in actors]
    envelope, *_ = _collect(bundle, actors, R=1, H=32)
    _assert(tuple(len(actor.calls) for actor in actors) == (1, 1, 0), "installed actor subset calls")
    _assert(tuple(call[0].shape[0] for actor in actors for call in actor.calls) == (2, 1), "installed actor batch sizes")
    for agent_id, actor in enumerate(actors):
        for old, new in zip(before[agent_id], actor.actor.actor.parameters()):
            _assert(torch.equal(old, new.detach()), f"installed actor {agent_id} mutated")
        _assert(len(actor.actor.actor_optimizer.state) == 0, "optimizer state created by collection")
    selected = envelope.historical_available_actions.to(torch.bool).gather(2, envelope.action_ids)
    _assert(bool(selected.all().item()), "installed actor sampled masked action")


def test_protected_repo_and_installed_harl_hashes() -> None:
    for filename, expected in REPO_PROTECTED_HASHES.items():
        actual = hashlib.sha256((SCAN_SOURCE / filename).read_bytes()).hexdigest()
        _assert(actual == expected, f"protected repo file drift: {filename}")
    for relative, expected in HARL_PROTECTED_HASHES.items():
        actual = hashlib.sha256((HARL_ROOT / relative).read_bytes()).hexdigest()
        _assert(actual == expected, f"installed HARL drift: {relative}")


def test_canonical_alias_and_isolated_import() -> None:
    alias = "assignment_event_actor_collection_alias"
    spec = importlib.util.spec_from_file_location(alias, COLLECTION_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:
        _assert("CanonicalModuleIdentityError" in str(exc), "wrong alias failure")
    else:
        raise AssertionError("alias import accepted")
    finally:
        sys.modules.pop(alias, None)
    child = f"""
import importlib.util,json,pathlib,sys
from types import ModuleType
root=pathlib.Path({str(REPO_ROOT)!r}); tasks=root/'source'/'isaaclab_tasks'/'isaaclab_tasks'; direct=tasks/'direct'; scan=direct/'scan_mobile_manipulator'; package={PACKAGE!r}
for name,path in (("isaaclab_tasks",tasks),("isaaclab_tasks.direct",direct),(package,scan)):
 m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
def load(stem):
 key=package+'.'+stem; path=scan/(stem+'.py'); spec=importlib.util.spec_from_file_location(key,path); module=importlib.util.module_from_spec(spec); sys.modules[key]=module; before=sys.dont_write_bytecode
 try: sys.dont_write_bytecode=True; spec.loader.exec_module(module)
 finally: sys.dont_write_bytecode=before
 return module
before=set(sys.modules)
for stem in ('assignment_profile_contract','assignment_lifecycle_transition_contract','assignment_event_contract','assignment_lifecycle_authority_runtime','assignment_initial_claim_runtime','assignment_lifecycle_transaction_runtime','assignment_interstep_claim_window_runtime','assignment_event_profile_schema_contract_v2','assignment_event_policy_evidence','assignment_event_policy_decision','assignment_event_actor_collection'): load(stem)
added=set(sys.modules)-before
print(json.dumps({{'canonical':package+'.assignment_event_actor_collection' in sys.modules,'bare':'assignment_event_actor_collection' not in sys.modules,'forbidden':not any(name.startswith(('omni','isaaclab.app','harl')) for name in added)}}))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run([sys.executable, "-c", child], cwd=temp_dir, capture_output=True, text=True, check=False)
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(all(payload.values()), f"isolation failed: {payload}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("policy_subset_mixed_rows_zero_valid_and_fixed_scatter", test_policy_subset_mixed_rows_zero_valid_and_fixed_scatter),
    ("fixed_shapes_dtypes_and_original_proposal_ledger", test_fixed_shapes_dtypes_and_original_proposal_ledger),
    ("same_task_conflict_preserves_both_samples_and_logprobs", test_same_task_conflict_preserves_both_samples_and_logprobs),
    ("forced_rows_never_call_actor_or_become_policy_evidence", test_forced_rows_never_call_actor_or_become_policy_evidence),
    ("historical_available_action_validation_and_masked_sample_failure", test_historical_available_action_validation_and_masked_sample_failure),
    ("malformed_actor_outputs_fail_closed", test_malformed_actor_outputs_fail_closed),
    ("exact_bundle_identity_chain_and_no_rebind", test_exact_bundle_identity_chain_and_no_rebind),
    ("envelope_immutability_and_historical_binding", test_envelope_immutability_and_historical_binding),
    ("slot_zero_and_t_tplus1_alignment", test_slot_zero_and_t_tplus1_alignment),
    ("slot_rejects_shift_and_wrong_current_envelope", test_slot_rejects_shift_and_wrong_current_envelope),
    ("no_lifecycle_recapture_or_i42_execution_static", test_no_lifecycle_recapture_or_i42_execution_static),
    ("no_lifecycle_problem_or_open_recapture_dynamic", test_no_lifecycle_problem_or_open_recapture_dynamic),
    ("installed_harl_happo_component_subset_smoke_no_update", test_installed_harl_happo_component_subset_smoke_no_update),
    ("protected_repo_and_installed_harl_hashes", test_protected_repo_and_installed_harl_hashes),
    ("canonical_alias_and_isolated_import", test_canonical_alias_and_isolated_import),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_phase_b2_i3a_dvm_actor_collection_storage_proposal_envelope_pure",
        "passed": passed,
        "total": len(results),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for item in results:
            suffix = "" if item["status"] == "passed" else f": {item['error']}"
            print(f"{item['status'].upper():6} {item['name']}{suffix}")
        print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
