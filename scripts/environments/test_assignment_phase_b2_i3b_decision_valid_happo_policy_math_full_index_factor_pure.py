"""B2-I3b decision-valid HAPPO math and full-index factor oracles."""

from __future__ import annotations

import argparse
import ast
import copy
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
I3A_FIXTURE_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b2_i3a_dvm_actor_collection_storage_proposal_envelope_pure.py"
MATH_PATH = SCAN_SOURCE / "assignment_event_happo_policy_math.py"
DEVICE = torch.device("cpu")

REPO_PROTECTED_HASHES = {
    "assignment_event_actor_collection.py": "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
    "assignment_event_policy_decision.py": "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
    "assignment_event_policy_evidence.py": "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
    "assignment_event_profile_schema_contract_v2.py": "9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_event_proposal_adapter.py": "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    "assignment_initial_claim_runtime.py": "c74868c84a803108c424827afe9326393428938dce4f6cbd46693da3d4d94fda",
    "assignment_lifecycle_transaction_runtime.py": "2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de",
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
HARL_PROTECTED_HASHES = {
    "runners/on_policy_ha_runner.py": "14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a",
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
I3AHELP = _load_path("assignment_b2_i3a_fixture_helpers", I3A_FIXTURE_PATH)
COLLECTION = I3AHELP.COLLECTION
I2HELP = I3AHELP.I2HELP
MATH = _load_path(f"{PACKAGE}.assignment_event_happo_policy_math", MATH_PATH)
RobotState = I3AHELP.RobotState
TaskState = I3AHELP.TaskState


def _expect_failure(code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except MATH.EventPolicyHAPPOMathError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    else:
        raise AssertionError(f"expected failure {code}")


def _bundle_from_dvm(dvm: torch.Tensor, *, N: int, serial: int):
    E, M = int(dvm.shape[0]), int(dvm.shape[1])
    tensors = list(I2HELP._state(E=E, M=M, N=N))
    tensors[1].fill_(int(RobotState.WAITING_FOR_TASK))
    tensors[1][dvm] = int(RobotState.NEEDS_ASSIGNMENT)
    problem = I2HELP._problem(E=E, M=M, N=N)
    return I3AHELP._bundle(
        E=E,
        M=M,
        N=N,
        tensors=tuple(tensors),
        problem=problem,
        serial=serial,
    )[0]


class TinyPolicy(torch.nn.Module):
    def __init__(self, obs_dim: int, action_dim: int) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(obs_dim, action_dim)

    def distribution(self, obs: torch.Tensor, available: torch.Tensor):
        logits = self.linear(obs)
        logits = logits.masked_fill(available == 0, -1.0e10)
        return torch.distributions.Categorical(logits=logits)


class TrackingHAPPO:
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        *,
        ppo_epoch: int = 1,
        actor_num_mini_batch: int = 1,
        lr: float = 5.0e-3,
    ) -> None:
        self.actor = TinyPolicy(obs_dim, action_dim)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=lr, eps=1.0e-5)
        self.ppo_epoch = ppo_epoch
        self.actor_num_mini_batch = actor_num_mini_batch
        self.clip_param = 0.2
        self.entropy_coef = 0.01
        self.use_max_grad_norm = True
        self.max_grad_norm = 10.0
        self.use_policy_active_masks = True
        self.use_recurrent_policy = False
        self.use_naive_recurrent_policy = False
        self.action_aggregation = "prod"
        self.get_calls = []
        self.evaluate_calls = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        self.get_calls.append((obs.clone(), available_actions.clone()))
        distribution = self.actor.distribution(obs, available_actions)
        action = available_actions[:, :-1].argmax(dim=-1, keepdim=True).to(torch.int64)
        logprob = distribution.log_prob(action[:, 0]).unsqueeze(-1)
        return action, logprob, rnn_states.clone()

    def evaluate_actions(self, obs, rnn_states, actions, masks, available_actions, active_masks=None):
        self.evaluate_calls.append(
            {
                "obs": obs.detach().clone(),
                "actions": actions.detach().clone(),
                "available_actions": available_actions.detach().clone(),
                "active_masks": None if active_masks is None else active_masks.detach().clone(),
            }
        )
        distribution = self.actor.distribution(obs, available_actions)
        logprob = distribution.log_prob(actions[:, 0].to(torch.int64)).unsqueeze(-1)
        entropy_each = distribution.entropy()
        if active_masks is None:
            entropy = entropy_each.mean()
        else:
            entropy = (entropy_each * active_masks[:, 0]).sum() / active_masks.sum()
        return logprob, entropy, distribution


def _fake_actors(bundle, *, ppo_epoch: int = 1, mini_batches: int = 1, seed: int = 11):
    torch.manual_seed(seed)
    O = int(bundle.evidence_snapshot.actor_obs.shape[-1])
    A = bundle.evidence_identity.N + 1
    return tuple(
        TrackingHAPPO(O, A, ppo_epoch=ppo_epoch, actor_num_mini_batch=mini_batches)
        for _ in range(bundle.evidence_identity.M)
    )


def _complete_rollout(
    *,
    dvm_steps: list[torch.Tensor],
    actors,
    active_steps: list[torch.Tensor] | None = None,
    N: int = 3,
    serial: int = 200,
    hidden: int = 8,
):
    T = len(dvm_steps) - 1
    E, M = tuple(dvm_steps[0].shape)
    bundles = [
        _bundle_from_dvm(dvm.to(torch.bool), N=N, serial=serial + index * 10)
        for index, dvm in enumerate(dvm_steps)
    ]
    if active_steps is None:
        active_steps = [torch.ones((E, M), dtype=torch.float32) for _ in range(T + 1)]
    storages = tuple(
        COLLECTION.create_event_policy_actor_slot_storage_v2(
            episode_length=T,
            agent_id=agent_id,
            current_decision_bundle=bundles[0],
            initial_active_masks=active_steps[0][:, agent_id].reshape(E, 1),
        )
        for agent_id in range(M)
    )
    for step in range(T):
        rnn = torch.zeros((E, M, 1, hidden), dtype=torch.float32)
        masks = torch.ones((E, M, 1), dtype=torch.float32)
        envelope = COLLECTION.collect_event_policy_proposals_v2(
            decision_bundle=bundles[step],
            actors=actors,
            rnn_states=rnn,
            masks=masks,
        )
        for agent_id, storage in enumerate(storages):
            storage.insert_transition(
                slot=step,
                proposal_envelope=envelope,
                next_decision_bundle=bundles[step + 1],
                next_active_masks=active_steps[step + 1][:, agent_id].reshape(E, 1),
            )
    rnn_by_agent = tuple(
        torch.zeros((T + 1, E, 1, hidden), dtype=torch.float32) for _ in range(M)
    )
    masks_by_agent = tuple(
        torch.ones((T + 1, E, 1), dtype=torch.float32) for _ in range(M)
    )
    return bundles, storages, rnn_by_agent, masks_by_agent


def _parameter_snapshot(actor) -> tuple[torch.Tensor, ...]:
    return tuple(parameter.detach().clone() for parameter in actor.actor.parameters())


def _same_parameters(left, right, *, atol: float = 0.0) -> bool:
    return all(
        torch.equal(a.detach(), b.detach()) if atol == 0.0 else torch.allclose(a.detach(), b.detach(), atol=atol, rtol=atol)
        for a, b in zip(left.actor.parameters(), right.actor.parameters())
    )


def test_descriptor_population_and_factory_boundaries() -> None:
    descriptor = MATH.get_event_policy_happo_math_descriptor_v2()
    _assert(descriptor["policy_evaluation_population"] == "decision_valid_masks[:-1]", "evaluation population")
    _assert("active_masks" in descriptor["policy_loss_population"], "loss population")
    _assert(descriptor["installed_harl_modified"] is False, "installed HARL mutation")
    _assert(descriptor["public_runner_integration"] is False, "public route opened")
    _expect_failure(
        "happo_result_factory_required",
        lambda: MATH.EventPolicyAdvantageNormalizationV2(
            MATH.EVENT_POLICY_HAPPO_POLICY_MATH_V2,
            0,
            "bad",
            None,
            None,
            torch.zeros((1, 1, 1)),
            object(),
        ),
    )


def test_mixed_rows_forced_bypass_and_sentinel_exclusion() -> None:
    dvm = [
        torch.tensor([[True], [False], [True]]),
        torch.tensor([[False], [True], [False]]),
        torch.zeros((3, 1), dtype=torch.bool),
    ]
    first = _bundle_from_dvm(dvm[0], N=3, serial=300)
    actor = _fake_actors(first, mini_batches=2, seed=21)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=3, serial=300)
    storage = storages[0]
    forced = ~storage.decision_valid_masks[:-1]
    storage._action_logprobs[forced] = float("nan")
    actor.evaluate_calls.clear()
    factor = torch.arange(1, 7, dtype=torch.float32).reshape(2, 3, 1)
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storage,
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.tensor([[[1.0], [99.0], [2.0]], [[88.0], [3.0], [77.0]]]),
        factor_before=factor,
        minibatch_permutations=(torch.tensor([5, 1, 4, 0, 3, 2], dtype=torch.int64),),
    )
    _assert(result.canonical_evaluation_indices == (0, 2, 4), "DVM evaluation indices")
    _assert(result.canonical_policy_loss_indices == (0, 2, 4), "loss indices")
    _assert(all(call["obs"].shape[0] <= 3 for call in actor.evaluate_calls), "full forced evaluation")
    forced_flat = torch.tensor([1, 3, 5], dtype=torch.int64)
    _assert(torch.equal(result.ratio_full.reshape(-1, 1)[forced_flat], torch.ones((3, 1))), "forced ratio not exact one")
    _assert(torch.equal(result.factor_after.reshape(-1, 1)[forced_flat], factor.reshape(-1, 1)[forced_flat]), "forced factor changed")
    _assert(result.processed_minibatches == 2, "processed minibatch denominator")


def test_zero_dvm_actor_bitwise_no_evaluate_no_optimizer() -> None:
    dvm = [torch.zeros((3, 1), dtype=torch.bool) for _ in range(3)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=400)
    actor = _fake_actors(first, mini_batches=2, seed=31)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=2, serial=400)
    before = _parameter_snapshot(actor)
    factor = torch.randn((2, 3, 1), dtype=torch.float32)
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.full((2, 3, 1), float("nan")),
        factor_before=factor,
        minibatch_permutations=(torch.arange(6, dtype=torch.int64),),
    )
    _assert(len(actor.evaluate_calls) == 0, "zero-DVM actor evaluated")
    _assert(result.optimizer_steps == 0 and len(actor.actor_optimizer.state) == 0, "zero-DVM optimizer mutated")
    _assert(all(torch.equal(old, new.detach()) for old, new in zip(before, actor.actor.parameters())), "zero-DVM parameters changed")
    _assert(torch.equal(result.factor_after, factor), "zero-DVM factor not bitwise identity")
    _assert(torch.equal(result.ratio_full, torch.ones_like(factor)), "zero-DVM ratio not ones")


def test_active_and_dvm_populations_remain_distinct() -> None:
    dvm = [
        torch.tensor([[True], [True], [False]]),
        torch.zeros((3, 1), dtype=torch.bool),
    ]
    active = [
        torch.tensor([[0.0], [1.0], [1.0]]),
        torch.ones((3, 1), dtype=torch.float32),
    ]
    first = _bundle_from_dvm(dvm[0], N=2, serial=500)
    actor = _fake_actors(first, seed=41)[0]
    _, storages, rnn, masks = _complete_rollout(
        dvm_steps=dvm,
        actors=(actor,),
        active_steps=active,
        N=2,
        serial=500,
    )
    actor.evaluate_calls.clear()
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.tensor([[[50.0], [2.0], [70.0]]]),
        factor_before=torch.ones((1, 3, 1)),
        minibatch_permutations=(torch.tensor([0, 1, 2], dtype=torch.int64),),
    )
    _assert(result.canonical_evaluation_indices == (0, 1), "DVM identity lost")
    _assert(result.canonical_policy_loss_indices == (1,), "active&DVM loss population wrong")
    update_calls = [call for call in actor.evaluate_calls if call["active_masks"] is not None]
    _assert(len(update_calls) == 1 and update_calls[0]["obs"].shape[0] == 1, "inactive DVM entered loss/entropy")
    _assert(result.normalization_rule == "singleton_raw_finite", "singleton guard")


def test_all_inactive_dvm_rows_skip_actor_update_and_factor_eval() -> None:
    dvm = [torch.ones((2, 1), dtype=torch.bool), torch.zeros((2, 1), dtype=torch.bool)]
    active = [torch.zeros((2, 1)), torch.ones((2, 1))]
    first = _bundle_from_dvm(dvm[0], N=2, serial=550)
    actor = _fake_actors(first, seed=45)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), active_steps=active, N=2, serial=550)
    before = _parameter_snapshot(actor)
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.full((1, 2, 1), float("nan")),
        factor_before=torch.tensor([[[2.0], [3.0]]]),
        minibatch_permutations=(torch.arange(2, dtype=torch.int64),),
    )
    _assert(result.canonical_evaluation_indices == (0, 1), "evaluation identity absent")
    _assert(result.canonical_policy_loss_indices == tuple(), "inactive rows entered loss")
    _assert(not result.factor_evaluation_performed and len(actor.evaluate_calls) == 0, "no-update actor evaluated")
    _assert(result.optimizer_steps == 0 and len(actor.actor_optimizer.state) == 0, "inactive optimizer mutation")
    _assert(all(torch.equal(old, new.detach()) for old, new in zip(before, actor.actor.parameters())), "inactive parameters changed")


def test_different_agent_dvm_full_index_sequential_factor() -> None:
    dvm = [
        torch.tensor([[True, False, False], [False, False, False], [False, True, False]]),
        torch.tensor([[False, False, False], [True, False, False], [False, False, False]]),
        torch.zeros((3, 3), dtype=torch.bool),
    ]
    first = _bundle_from_dvm(dvm[0], N=3, serial=600)
    actors = _fake_actors(first, mini_batches=2, seed=51)
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=actors, N=3, serial=600)
    for actor in actors:
        actor.evaluate_calls.clear()
    permutations = {
        0: (torch.tensor([5, 4, 3, 2, 1, 0], dtype=torch.int64),),
        1: (torch.tensor([1, 3, 5, 0, 2, 4], dtype=torch.int64),),
        2: (torch.arange(6, dtype=torch.int64),),
    }
    sequence = MATH.train_event_policy_happo_sequence_v2(
        actors=actors,
        actor_storages=storages,
        rnn_states_by_agent=rnn,
        masks_by_agent=masks,
        advantages=torch.arange(1, 7, dtype=torch.float32).reshape(2, 3, 1),
        initial_factor=torch.ones((2, 3, 1)),
        agent_order=(0, 1, 2),
        minibatch_permutations_by_agent=permutations,
    )
    a0, a1, a2 = sequence.actor_results
    _assert(a0.canonical_evaluation_indices == (0, 4), "agent0 canonical DVM")
    _assert(a1.canonical_evaluation_indices == (2,), "agent1 canonical DVM")
    _assert(a2.canonical_evaluation_indices == tuple(), "agent2 zero DVM")
    _assert(torch.equal(a1.factor_before, a0.factor_after), "sequential factor reinitialized")
    _assert(torch.equal(a2.factor_before, a1.factor_after), "agent2 factor input wrong")
    _assert(torch.equal(a2.factor_after, a2.factor_before), "zero actor changed full factor")
    for result, allowed in ((a0, {0, 4}), (a1, {2})):
        flat = result.ratio_full.reshape(-1)
        for index in range(6):
            if index not in allowed:
                _assert(float(flat[index]) == 1.0, f"agent factor leaked to k={index}")
    _assert(len(actors[2].evaluate_calls) == 0 and len(actors[2].actor_optimizer.state) == 0, "zero agent mutated")


def test_canonical_scatter_survives_minibatch_permutation() -> None:
    dvm = [
        torch.tensor([[False], [True], [False], [False]]),
        torch.tensor([[True], [False], [False], [True]]),
        torch.zeros((4, 1), dtype=torch.bool),
    ]
    first = _bundle_from_dvm(dvm[0], N=2, serial=700)
    actor = _fake_actors(first, mini_batches=2, seed=61)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=2, serial=700)
    permutation = torch.tensor([7, 1, 4, 6, 0, 3, 2, 5], dtype=torch.int64)
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.arange(1, 9, dtype=torch.float32).reshape(2, 4, 1),
        factor_before=torch.ones((2, 4, 1)),
        minibatch_permutations=(permutation,),
    )
    _assert(result.canonical_evaluation_indices == (1, 4, 7), "canonical k ledger")
    processed = tuple(index for record in result.minibatch_records for index in record.policy_loss_canonical_indices)
    _assert(processed == (7, 1, 4), f"minibatch order not retained: {processed}")
    expected = torch.ones((8, 1), dtype=torch.float32)
    expected[torch.tensor([1, 4, 7])] = torch.exp(result.post_update_logprobs - result.pre_update_logprobs)
    _assert(torch.allclose(result.ratio_full.reshape(8, 1), expected), "factor compact ordinal scatter")


def test_empty_filtered_minibatch_skips_and_logging_uses_processed_count() -> None:
    dvm = [torch.tensor([[True], [False]]), torch.zeros((2, 1), dtype=torch.bool), torch.zeros((2, 1), dtype=torch.bool)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=800)
    actor = _fake_actors(first, mini_batches=2, seed=71)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=2, serial=800)
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.ones((2, 2, 1)),
        factor_before=torch.ones((2, 2, 1)),
        minibatch_permutations=(torch.tensor([1, 2, 0, 3], dtype=torch.int64),),
    )
    _assert(result.planned_minibatches == 2 and result.processed_minibatches == 1, "empty batch counting")
    _assert(not result.minibatch_records[0].processed and result.minibatch_records[1].processed, "empty batch not skipped")
    _assert(result.train_info["processed_updates"] == 1, "logging denominator planned rather than processed")


def test_advantage_singleton_zero_variance_and_nonfinite_guards() -> None:
    singleton = MATH.normalize_event_policy_advantages_v2(
        advantages=torch.tensor([[[7.0], [float("nan")]]]),
        policy_loss_mask=torch.tensor([[[True], [False]]]),
    )
    _assert(singleton.rule == "singleton_raw_finite", "singleton rule")
    _assert(float(singleton.normalized_advantages[0, 0, 0]) == 7.0, "singleton changed")
    _assert(float(singleton.normalized_advantages[0, 1, 0]) == 0.0, "invalid advantage leaked")
    zero_variance = MATH.normalize_event_policy_advantages_v2(
        advantages=torch.tensor([[[5.0], [5.0]]]),
        policy_loss_mask=torch.ones((1, 2, 1), dtype=torch.bool),
    )
    _assert(zero_variance.rule == "zero_variance_raw_finite", "zero variance rule")
    _assert(torch.equal(zero_variance.normalized_advantages, torch.full((1, 2, 1), 5.0)), "zero variance nonfinite")
    huge = MATH.normalize_event_policy_advantages_v2(
        advantages=torch.tensor([[[3.0e38], [-3.0e38]]]),
        policy_loss_mask=torch.ones((1, 2, 1), dtype=torch.bool),
    )
    _assert("fallback" in huge.rule and bool(torch.isfinite(huge.normalized_advantages).all().item()), "nonfinite std fallback")
    _expect_failure(
        "nonfinite_actor_advantage",
        lambda: MATH.normalize_event_policy_advantages_v2(
            advantages=torch.tensor([[[float("inf")]]]),
            policy_loss_mask=torch.ones((1, 1, 1), dtype=torch.bool),
        ),
    )


def test_slot_t_dvm_and_historical_mask_not_next_slot() -> None:
    dvm = [torch.tensor([[True], [False]]), torch.tensor([[False], [True]]), torch.zeros((2, 1), dtype=torch.bool)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=900)
    actor = _fake_actors(first, seed=81)[0]
    bundles, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=2, serial=900)
    historical = storages[0].available_actions[:-1].clone()
    storages[0]._available_actions[1:, :, :-1] = 0.0
    storages[0]._available_actions[1:, :, -1] = 1.0
    storages[0]._available_actions[1, 1] = historical[1, 1]
    result = MATH.train_event_policy_happo_actor_v2(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.ones((2, 2, 1)),
        factor_before=torch.ones((2, 2, 1)),
        minibatch_permutations=(torch.arange(4, dtype=torch.int64),),
    )
    _assert(result.canonical_evaluation_indices == (0, 3), "DVM shifted to [1:]")
    evaluated_masks = torch.cat([call["available_actions"] for call in actor.evaluate_calls], dim=0)
    _assert(bool((evaluated_masks.sum(dim=-1) >= 2).all().item()), "historical mask replaced by next slot")
    _assert(bundles[0] is storages[0].decision_bundle_refs[0], "slot identity lost")


def test_original_action_and_conflict_loser_both_train() -> None:
    dvm = [torch.ones((1, 2), dtype=torch.bool), torch.zeros((1, 2), dtype=torch.bool)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=1000)
    actors = _fake_actors(first, seed=91)
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=actors, N=2, serial=1000)
    _assert(tuple(int(storage.action_ids[0, 0, 0]) for storage in storages) == (0, 0), "same-task proposal control")
    sequence = MATH.train_event_policy_happo_sequence_v2(
        actors=actors,
        actor_storages=storages,
        rnn_states_by_agent=rnn,
        masks_by_agent=masks,
        advantages=torch.ones((1, 1, 1)),
        initial_factor=torch.ones((1, 1, 1)),
        agent_order=(0, 1),
        minibatch_permutations_by_agent={0: (torch.tensor([0]),), 1: (torch.tensor([0]),)},
    )
    _assert(tuple(result.canonical_policy_loss_indices for result in sequence.actor_results) == ((0,), (0,)), "conflict loser filtered")
    for actor in actors:
        update_actions = [call["actions"] for call in actor.evaluate_calls if call["active_masks"] is not None]
        _assert(len(update_actions) == 1 and int(update_actions[0][0, 0]) == 0, "original action substituted")


def _installed_args():
    args = I3AHELP._happo_args()
    args["ppo_epoch"] = 1
    args["actor_num_mini_batch"] = 1
    return args


def test_all_policy_matches_stock_installed_happo_update() -> None:
    from harl.algorithms.actors.happo import HAPPO
    from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer

    dvm = [torch.ones((2, 1), dtype=torch.bool) for _ in range(3)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=1100)
    O = int(first.evidence_snapshot.actor_obs.shape[-1])
    torch.manual_seed(101)
    collector_actor = HAPPO(_installed_args(), I3AHELP.Box((O,)), I3AHELP.Discrete(3), device=DEVICE)
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(collector_actor,), N=2, serial=1100, hidden=32)
    stock_actor = copy.deepcopy(collector_actor)
    event_actor = copy.deepcopy(collector_actor)
    storage = storages[0]
    buffer_args = {
        "episode_length": 2,
        "n_rollout_threads": 2,
        "hidden_sizes": [32, 32],
        "recurrent_n": 1,
    }
    stock_buffer = OnPolicyActorBuffer(buffer_args, I3AHELP.Box((O,)), I3AHELP.Discrete(3), device=DEVICE)
    stock_buffer.obs.copy_(storage.obs)
    stock_buffer.rnn_states.copy_(rnn[0])
    stock_buffer.available_actions.copy_(storage.available_actions)
    stock_buffer.actions.copy_(storage.runner_actions)
    stock_buffer.action_log_probs.copy_(storage.action_logprobs)
    stock_buffer.masks.copy_(masks[0])
    stock_buffer.active_masks.copy_(storage.active_masks)
    stock_buffer.update_factor(torch.ones((2, 2, 1)))
    advantages = torch.tensor([[[1.0], [2.0]], [[4.0], [8.0]]])
    seed = 12345
    torch.manual_seed(seed)
    stock_info = stock_actor.train(stock_buffer, advantages.clone(), "EP")
    torch.manual_seed(seed)
    event_result = MATH.train_event_policy_happo_actor_v2(
        actor=event_actor,
        actor_storage=storage,
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=advantages,
        factor_before=torch.ones((2, 2, 1)),
    )
    _assert(_same_parameters(stock_actor, event_actor, atol=2.0e-7), "all-policy parameter update differs from stock")
    for key in ("policy_loss", "dist_entropy", "ratio"):
        stock_value = float(stock_info[key])
        event_value = float(event_result.train_info[key])
        _assert(abs(stock_value - event_value) <= 2.0e-6, f"stock {key} mismatch: {stock_value} vs {event_value}")


def test_malformed_contracts_fail_closed() -> None:
    dvm = [torch.ones((2, 1), dtype=torch.bool), torch.zeros((2, 1), dtype=torch.bool)]
    first = _bundle_from_dvm(dvm[0], N=2, serial=1200)
    actor = _fake_actors(first, seed=111)[0]
    _, storages, rnn, masks = _complete_rollout(dvm_steps=dvm, actors=(actor,), N=2, serial=1200)
    args = dict(
        actor=actor,
        actor_storage=storages[0],
        rnn_states=rnn[0],
        masks=masks[0],
        advantages=torch.ones((1, 2, 1)),
        factor_before=torch.ones((1, 2, 1)),
    )
    actor.use_recurrent_policy = True
    _expect_failure("recurrent_policy_forbidden", lambda: MATH.train_event_policy_happo_actor_v2(**args))
    actor.use_recurrent_policy = False
    _expect_failure(
        "minibatch_permutation_contract",
        lambda: MATH.train_event_policy_happo_actor_v2(
            **args,
            minibatch_permutations=(torch.tensor([0, 0], dtype=torch.int64),),
        ),
    )
    _expect_failure(
        "happo_tensor_contract",
        lambda: MATH.train_event_policy_happo_actor_v2(
            **{**args, "factor_before": torch.ones((2, 1, 1))}
        ),
    )


def test_no_lifecycle_recapture_proposal_execution_or_critic_math_static() -> None:
    source = MATH_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    from_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    forbidden = ("harl", "proposal_adapter", "runtime", "lifecycle_transaction", "scan_mobile_manipulator_env")
    _assert(not any(any(token in name for token in forbidden) for name in imports | from_modules), f"forbidden import: {imports | from_modules}")
    for token in ("evaluate_actions(", "actor_optimizer.step()", "decision_valid_masks[:-1]", "ratio_full"):
        _assert(token in source, f"required math seam absent: {token}")
    for token in ("directmarlenv", "time_limit", "bad_masks", "value_normalizer", "construct_m1", "final_p2"):
        _assert(token not in source.lower(), f"forbidden later/runtime seam: {token}")


def test_protected_repo_and_installed_harl_hashes() -> None:
    for filename, expected in REPO_PROTECTED_HASHES.items():
        actual = hashlib.sha256((SCAN_SOURCE / filename).read_bytes()).hexdigest()
        _assert(actual == expected, f"protected repo drift: {filename}")
    for relative, expected in HARL_PROTECTED_HASHES.items():
        actual = hashlib.sha256((HARL_ROOT / relative).read_bytes()).hexdigest()
        _assert(actual == expected, f"installed HARL drift: {relative}")


def test_canonical_alias_and_isolated_import() -> None:
    alias = "assignment_event_happo_policy_math_alias"
    spec = importlib.util.spec_from_file_location(alias, MATH_PATH)
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
import importlib,json,pathlib,sys
from types import ModuleType
root=pathlib.Path({str(REPO_ROOT)!r}); tasks=root/'source'/'isaaclab_tasks'/'isaaclab_tasks'; direct=tasks/'direct'; scan=direct/'scan_mobile_manipulator'; package={PACKAGE!r}
for name,path in [('isaaclab_tasks',tasks),('isaaclab_tasks.direct',direct),(package,scan)]:
 m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
before=set(sys.modules); module=importlib.import_module(package+'.assignment_event_happo_policy_math'); added=set(sys.modules)-before
print(json.dumps({{'canonical':package+'.assignment_event_happo_policy_math' in sys.modules,'bare':'assignment_event_happo_policy_math' not in sys.modules,'harl':not any(name.startswith('harl') for name in added),'environment':not any((name.startswith('omni') or name.startswith('isaaclab.app') or name.endswith('scan_mobile_manipulator_env')) for name in added)}}))
"""
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "isolated_i3b.py"
        path.write_text(child, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, "-I", "-B", str(path)],
            cwd=temp,
            capture_output=True,
            text=True,
            check=False,
        )
    _assert(completed.returncode == 0, f"isolated import failed: {completed.stderr}")
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    _assert(all(payload.values()), f"isolated import boundary: {payload}")


TESTS = (
    ("descriptor_population_and_factory_boundaries", test_descriptor_population_and_factory_boundaries),
    ("mixed_rows_forced_bypass_and_sentinel_exclusion", test_mixed_rows_forced_bypass_and_sentinel_exclusion),
    ("zero_dvm_actor_bitwise_no_evaluate_no_optimizer", test_zero_dvm_actor_bitwise_no_evaluate_no_optimizer),
    ("active_and_dvm_populations_remain_distinct", test_active_and_dvm_populations_remain_distinct),
    ("all_inactive_dvm_rows_skip_actor_update_and_factor_eval", test_all_inactive_dvm_rows_skip_actor_update_and_factor_eval),
    ("different_agent_dvm_full_index_sequential_factor", test_different_agent_dvm_full_index_sequential_factor),
    ("canonical_scatter_survives_minibatch_permutation", test_canonical_scatter_survives_minibatch_permutation),
    ("empty_filtered_minibatch_skips_and_logging_uses_processed_count", test_empty_filtered_minibatch_skips_and_logging_uses_processed_count),
    ("advantage_singleton_zero_variance_and_nonfinite_guards", test_advantage_singleton_zero_variance_and_nonfinite_guards),
    ("slot_t_dvm_and_historical_mask_not_next_slot", test_slot_t_dvm_and_historical_mask_not_next_slot),
    ("original_action_and_conflict_loser_both_train", test_original_action_and_conflict_loser_both_train),
    ("all_policy_matches_stock_installed_happo_update", test_all_policy_matches_stock_installed_happo_update),
    ("malformed_contracts_fail_closed", test_malformed_contracts_fail_closed),
    ("no_lifecycle_recapture_proposal_execution_or_critic_math_static", test_no_lifecycle_recapture_proposal_execution_or_critic_math_static),
    ("protected_repo_and_installed_harl_hashes", test_protected_repo_and_installed_harl_hashes),
    ("canonical_alias_and_isolated_import", test_canonical_alias_and_isolated_import),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    passed = []
    failed = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            failed.append((name, f"{type(exc).__name__}: {exc}"))
        else:
            passed.append(name)
    payload = {"passed": len(passed), "total": len(TESTS), "failed": failed}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for name in passed:
            print(f"PASS {name}")
        for name, failure in failed:
            print(f"FAIL {name}: {failure}")
        print(f"RESULT {len(passed)}/{len(TESTS)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
