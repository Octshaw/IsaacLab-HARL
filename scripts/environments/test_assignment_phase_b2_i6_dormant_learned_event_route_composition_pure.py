"""Pure/synthetic B2-I6 dormant learned event-route composition verification.

No Isaac/AppLauncher, real HARL rollout, optimizer, training, playback,
evaluation, or checkpoint path is executed.  The fixture uses the existing
task-local fake exact-event environment, synthetic Torch actors/critic, and
call-recording trainer seams.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
I4_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b2_i4_authoritative_prereset_terminal_critic_sidecar_pure.py"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEVICE = torch.device("cpu")
E, M, N, T = 4, 3, 4, 2

PROTECTED_REPO_HASHES = {
    "assignment_event_actor_collection.py": "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
    "assignment_event_happo_policy_math.py": "3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4",
    "assignment_event_terminal_critic_sidecar.py": "655ecafeaf6d08eb856725023572438976a381fb7ffe0a5cadf16d61a4bfe49f",
    "assignment_event_terminal_learner_transport.py": "e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4",
    "assignment_event_critic_buffer.py": "682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f",
    "assignment_event_gae_returns.py": "7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379",
    "assignment_event_policy_evidence.py": "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
    "assignment_event_policy_decision.py": "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
    "assignment_event_runtime_facade.py": "036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478",
    "assignment_event_proposal_adapter.py": "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
PROTECTED_HARL_HASHES = {
    "runners/on_policy_base_runner.py": "5d99e0fa6f70f0bbff4d5b0f00f45faa3e4b543e1531f5259900480f1842044f",
    "runners/on_policy_ha_runner.py": "14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a",
    "common/buffers/on_policy_critic_buffer_ep.py": "0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _load_path(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    _assert(spec is not None and spec.loader is not None, f"loader missing: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


I4 = _load_path("_phase_b2_i6_i4_helpers", I4_PATH)
BASE = I4.BASE
TRANSITION = I4.TRANSITION
EVIDENCE = _load_path(f"{PREFIX}.assignment_event_policy_evidence", SCAN_SOURCE / "assignment_event_policy_evidence.py")
DECISION = _load_path(f"{PREFIX}.assignment_event_policy_decision", SCAN_SOURCE / "assignment_event_policy_decision.py")
COLLECTION = _load_path(f"{PREFIX}.assignment_event_actor_collection", SCAN_SOURCE / "assignment_event_actor_collection.py")
LT = _load_path(f"{PREFIX}.assignment_event_terminal_learner_transport", SCAN_SOURCE / "assignment_event_terminal_learner_transport.py")
CB = _load_path(f"{PREFIX}.assignment_event_critic_buffer", SCAN_SOURCE / "assignment_event_critic_buffer.py")
ROUTE = _load_path(f"{PREFIX}.assignment_event_learned_route", SCAN_SOURCE / "assignment_event_learned_route.py")
Reason = TRANSITION.TerminationReason


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class ScriptedActor:
    def __init__(self, batches: list[list[int]], base_logprob: float) -> None:
        self.batches = list(batches)
        self.base_logprob = base_logprob
        self.calls: list[dict[str, Any]] = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        index = len(self.calls)
        _assert(index < len(self.batches), "unexpected actor call")
        actions = torch.tensor(self.batches[index], dtype=torch.int64, device=obs.device).view(-1, 1)
        _assert(actions.shape[0] == obs.shape[0], "scripted actor batch mismatch")
        self.calls.append({
            "obs": obs.detach().clone(),
            "available": available_actions.detach().clone(),
            "deterministic": deterministic,
        })
        logs = torch.full((obs.shape[0], 1), self.base_logprob - index * 0.01, dtype=torch.float32, device=obs.device)
        return actions, logs, rnn_states.detach().clone() + 1.0


class RecordingCritic(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.ones((1,), dtype=torch.float32))
        self.calls: list[dict[str, Any]] = []

    def get_values(self, obs, rnn, masks):
        self.calls.append({"obs": obs.detach().clone(), "rnn": rnn.detach().clone(), "masks": masks.detach().clone(), "grad": torch.is_grad_enabled()})
        values = obs[:, :1].detach().clone()
        return values, rnn.detach().clone() + 0.25


class MixedTerminalEventEnvironment(BASE._EventEnvironment):
    """Task-local physical stub with one timeout and one true terminal at step 0."""

    def __init__(self, profile: Any, domain: Any) -> None:
        super().__init__(profile, domain)
        self.problem = I4._problem(E=E, M=M, N=N)
        feasible = self.problem["feasible_mask"]
        feasible.zero_()
        feasible[0, 0, 0] = True
        feasible[0, 1, 0] = True
        feasible[1, 0, 1] = True
        feasible[3, 0, 2] = True
        feasible[3, 1, 2] = True
        costs = self.problem["cost_matrix"]
        costs.fill_(20.0)
        costs[0, 0, 0] = 3.0
        costs[0, 1, 0] = 1.0
        costs[3, 0, 2] = 1.0
        costs[3, 1, 2] = 2.0
        self.progress = torch.zeros((E,), dtype=torch.int64)
        self.coverage = torch.zeros((E, N), dtype=torch.bool)
        self.route_steps = 0

    def reset(self):
        result = super().reset()
        self.progress.zero_()
        self.coverage.zero_()
        self.route_steps = 0
        return result

    def step(self, actions: object):
        self.step_calls += 1
        self.last_actions = actions.detach().clone() if type(actions) is torch.Tensor else actions
        self.validation.validate_physical_step_entry_for_active_call()
        self.validation.validate_physical_finalization_for_active_call()
        completion = torch.zeros((E, M, N), dtype=torch.bool)
        truncated = torch.zeros((E,), dtype=torch.bool)
        if self.route_steps == 0:
            completion[2, 0, N - 1] = True
            truncated[1] = True
        report = I4._report(
            self.domain,
            problem=self.problem,
            step=int(self.progress.max().item()) + 1,
            completion=completion,
            coverage=self.coverage,
            truncated=truncated,
        )
        outcome = self.lifecycle.finalize_physical_transition(report)
        if self.route_steps == 0:
            self.coverage[2, N - 1] = True
        done = outcome.terminated | outcome.truncated
        done_ids = torch.nonzero(done, as_tuple=False).flatten().tolist()
        if done_ids:
            self.validation.validate_reset_entry_for_active_call()
            I4._reset(self.domain, done_ids)
            self.coverage[done] = False
            self.progress[done] = 0
        self.progress[~done] += 1
        self.route_steps += 1
        rewards = {name: torch.full((E,), float(agent + 1), dtype=torch.float32) for agent, name in enumerate(self.possible_agents)}
        terminated = {name: outcome.terminated.detach().clone() for name in self.possible_agents}
        truncated_map = {name: outcome.truncated.detach().clone() for name in self.possible_agents}
        return self._obs(), rewards, terminated, truncated_map, {"route": "mixed_event_step"}


class Harness:
    def __init__(self) -> None:
        self.profile = BASE._profile()
        self.domain = BASE._domain(self.profile, envs=E, robots=M, tasks=N)
        self.raw = MixedTerminalEventEnvironment(self.profile, self.domain)
        self.view = BASE._WrapperView(self.raw)
        self.wrapper = BASE.WRAPPER._compose_event_assignment_harl_wrapper(
            env=self.view,
            resolved_assignment_profile=self.profile,
            runtime_domain=self.domain,
        )
        self.scale = I4._scale(M=M, N=N)
        self.events: list[str] = []
        self.actors = (
            ScriptedActor([[0, N, 2], [N]], -0.10),
            ScriptedActor([[0, 2]], -0.20),
            ScriptedActor([], -0.30),
        )
        self.critic = RecordingCritic()
        critic_dim = I4.SCHEMA.build_assignment_event_profile_schema_v2_descriptor(
            scale_contract=self.scale
        )["critic_schema"]["dimension"]
        args = {
            "episode_length": T,
            "n_rollout_threads": E,
            "hidden_sizes": [4],
            "recurrent_n": 1,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "use_gae": True,
            "use_proper_time_limits": True,
        }
        self.buffer = CB.EventOnPolicyCriticBufferEPV2(args, Box((critic_dim,)), device=DEVICE)
        self.actor_train_calls: list[dict[str, Any]] = []
        self.critic_train_calls: list[dict[str, Any]] = []
        self.route = ROUTE._compose_dormant_event_learned_policy_route_v2(
            episode_length=T,
            actors=self.actors,
            critic=self.critic,
            critic_buffer=self.buffer,
            admitted_reset=self._admitted_reset,
            current_decision_supplier=self._current_bundle,
            current_decision_validator=self._validate_current,
            capture_i42_decision=self.wrapper._capture_event_proposal_decision,
            step_i42_proposals=self.wrapper._step_event_proposals,
            action_builder=lambda env, assignment: assignment.detach().clone(),
            actor_trainer=self._actor_trainer,
            critic_trainer=self._critic_trainer,
            actor_rnn_shape=(1, 4),
            call_observer=lambda stage, detail: self.events.append(stage),
        )

    def _admitted_reset(self):
        result = self.wrapper.reset()
        # Precondition env 2 with N-1 completed tasks and one authoritative
        # final-task ownership.  These are real lifecycle transactions in the
        # task-local synthetic runtime, not wrapper state.
        for task in range(N - 1):
            I4._seed(self.domain, env_id=2, task_id=task)
            completion = torch.zeros((E, M, N), dtype=torch.bool)
            completion[2, 0, task] = True
            self.domain.environment_port.finalize_physical_transition(
                I4._report(
                    self.domain,
                    problem=self.raw.problem,
                    step=task + 1,
                    completion=completion,
                    coverage=self.raw.coverage,
                )
            )
            self.raw.coverage[2, task] = True
        I4._seed(self.domain, env_id=2, task_id=N - 1)
        return result

    def _current_bundle(self):
        self.events.append("I1")
        current = self.domain.current_read_port.read_current()
        open_view = self.domain.interstep_fence_read_port.read()
        physical = EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=self.raw.problem,
            episode_progress_steps=self.raw.progress,
            scale_contract=self.scale,
        )
        snapshot = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(
            current_publication=current,
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=self.scale,
        )
        self.events.append("I2")
        return DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)

    def _validate_current(self, bundle):
        bundle.evidence_snapshot.validate_current(
            current_publication=self.domain.current_read_port.read_current(),
            current_open_window_view=self.domain.interstep_fence_read_port.read(),
        )

    def _actor_trainer(self, **kwargs):
        self.actor_train_calls.append(kwargs)
        return {"route": "I3b_recorder", "factor_shape": tuple(kwargs["initial_factor"].shape)}

    def _critic_trainer(self, buffer, value_normalizer):
        self.critic_train_calls.append({"buffer": buffer, "value_normalizer": value_normalizer})
        return {"route": "critic_recorder", "optimizer_calls": 0}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect(call: Callable[[], object], code: str) -> None:
    try:
        call()
    except BaseException as exc:
        _assert(getattr(exc, "failure_code", None) == code, f"expected {code}, got {exc}")
    else:
        raise AssertionError(f"expected failure {code}")


def _run_rollout() -> tuple[Harness, Any, Any, Any]:
    harness = Harness()
    reset_result = harness.route.reset()
    first = harness.route.collect_step()
    second = harness.route.collect_step()
    rollout = harness.route.finish_rollout(agent_order=(0, 1, 2))
    return harness, reset_result, (first, second), rollout


def test_i6_1_reset_exact_slot0_and_no_sampling() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    bundle = harness.route.current_decision_bundle
    _assert(tuple(len(actor.calls) for actor in harness.actors) == (0, 0, 0), "reset sampled actor")
    _assert(all(storage.decision_bundle_refs[0] is bundle for storage in harness.route.actor_storages), "actor slot0 binding")
    _assert(torch.equal(harness.buffer.share_obs[0], bundle.evidence_snapshot.runner_share_obs[:, 0]), "critic slot0 binding")
    _assert(harness.events.index("I1") < harness.events.index("I2") < harness.events.index("slot0_initialized"), "reset call order")
    return {"E": E, "M": M, "N": N, "actor_calls": 0, "slot0": "same current I1/I2"}


def test_i6_2_mixed_rows_noop_conflict_and_proposal_effective_separation() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    receipt = harness.route.collect_step()
    envelope = receipt.proposal_envelope
    bundle = receipt.decision_bundle
    _assert(tuple(len(actor.calls) for actor in harness.actors) == (1, 1, 0), "forced/full-row sampling")
    _assert(int(envelope.action_ids[1, 0, 0]) == N and bool(envelope.policy_proposal_present_mask[1, 0, 0]), "policy noop")
    _assert(int(envelope.action_ids[1, 1, 0]) == N and not bool(envelope.policy_proposal_present_mask[1, 1, 0]), "forced noop")
    _assert(int(envelope.action_ids[2, 0, 0]) == N - 1 and not bool(envelope.policy_proposal_present_mask[2, 0, 0]), "continuation routing")
    _assert(tuple(int(item) for item in envelope.original_policy_proposal_ids[0, :2, 0]) == (0, 0), "same-task samples lost")
    _assert(torch.allclose(envelope.action_logprobs[0, :2, 0], torch.tensor([-0.10, -0.20])), "original logprobs lost")
    _assert(int(receipt.facade_result.admitted_effective_assignment[0, 0]) == -1 and int(receipt.facade_result.admitted_effective_assignment[0, 1]) == 0, "cost arbitration winner")
    _assert(not torch.equal(receipt.facade_result.admitted_effective_assignment.unsqueeze(-1), envelope.original_policy_proposal_ids), "effective overwrote proposal evidence")
    statuses = receipt.facade_result.resolution.interpretations
    _assert(statuses[2][0].name == "CONTINUE_EXISTING", "continuation became claim")
    _assert(bundle.forced_continuation_mask[2, 0, 0], "missing continuation DVM evidence")
    return {"policy_noop": True, "forced_noop": True, "conflict_winner": 1, "continuation": "no reclaim"}


def test_i6_3_terminal_transport_autoreset_timeout_once_and_six_tuple() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    receipt = harness.route.collect_step()
    step = receipt.harl_step_result
    _assert(len(step) == 6, "HARL arity changed")
    _assert(step[3][:, 0].tolist() == [False, True, True, False], "mixed E done rows")
    records = [step[4][env][0].get(LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2) for env in range(E)]
    _assert(records[0] is None and records[3] is None, "nonterminal DTO")
    _assert(records[1].termination_reason == int(Reason.TIME_LIMIT), "timeout reason")
    _assert(records[2].termination_reason == int(Reason.ALL_TASKS_COMPLETED), "true terminal reason")
    _assert(receipt.next_decision_bundle.evidence_identity.episode_generations[1:3] == (1, 1), "autoreset current generation")
    _assert(receipt.next_decision_bundle is harness.route.current_decision_bundle, "next current not retained")
    _assert(harness.buffer.timeout_bootstrap_masks[0, :, 0].tolist() == [False, True, False, False], "timeout critic selection")
    compact_calls = [call for call in harness.critic.calls if call["obs"].shape[0] == 1]
    _assert(len(compact_calls) == 1, "timeout critic not exactly once")
    _assert(harness.domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "runtime ACK delayed to learner")
    return {"normal": [0, 3], "TIME_LIMIT": [1], "true_terminal": [2], "timeout_critic_calls": 1, "arity": 6}


def test_i6_4_rollout_returns_train_order_and_rollover() -> dict[str, object]:
    harness, _, receipts, rollout = _run_rollout()
    _assert(len(harness.actor_train_calls) == 1 and len(harness.critic_train_calls) == 1, "trainer selection")
    actor_call = harness.actor_train_calls[0]
    _assert(tuple(actor_call["initial_factor"].shape) == (T, E, 1), "factor is not full [T,E,1]")
    _assert(torch.equal(actor_call["advantages"], rollout.advantages), "advantage transport")
    order = harness.events
    required = ["I5a_critic_buffer_insert", "ordinary_final_next_value", "I5b_compute_event_returns", "event_advantages", "I3b_actor_train", "critic_train", "critic_after_update", "terminal_ledger_reset", "rollout_slot0_rebuilt"]
    positions = [max(index for index, item in enumerate(order) if item == stage) for stage in required]
    _assert(positions == sorted(positions), f"train/rollover order: {positions}")
    _assert(harness.buffer.step == 0 and not bool(harness.buffer._event_slot_written.any().item()), "critic event slots not cleared")
    _assert(not bool(harness.buffer.timeout_bootstrap_masks.any().item()), "timeout masks leaked")
    _assert(harness.route.collector.consumed_terminal_keys == (), "terminal ledger leaked")
    final_bundle = receipts[-1].next_decision_bundle
    _assert(all(storage.next_action_slot == 0 and storage.decision_bundle_refs[0] is final_bundle for storage in harness.route.actor_storages), "actor rollover slot0")
    _assert(all(storage is not old for storage, old in zip(harness.route.actor_storages, rollout.completed_actor_storages)), "completed actor storage reused")
    return {"event_returns": 1, "I3b_recorder": 1, "critic_recorder": 1, "optimizer_calls": 0, "ledger": 0}


def test_i6_5_call_order_exact_binding_and_no_alias() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    receipt = harness.route.collect_step()
    stages = harness.events
    expected = ("learner_expectation", "I3a_actor_collection", "I42_proposal_adapter", "runtime_proposal_effective_step", "next_I1_I2_current", "I5a_terminal_infos", "I5a_critic_buffer_insert", "actor_slot_insert")
    positions = [stages.index(item) for item in expected]
    _assert(positions == sorted(positions), f"step order: {positions}")
    _assert(receipt.proposal_envelope.decision_bundle is receipt.decision_bundle, "I2/I3a rebound")
    _assert(receipt.decision_bundle.evidence_snapshot is receipt.decision_bundle.proposal_source_binding.evidence_snapshot, "I1/I2/I4 binding")
    before = receipt.next_decision_bundle.evidence_snapshot.actor_obs
    receipt.harl_step_result[0]["agent_0"].fill_(999.0)
    _assert(torch.equal(receipt.next_decision_bundle.evidence_snapshot.actor_obs, before), "HARL obs aliases next bundle")
    dto = receipt.harl_step_result[4][1][0][LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2]
    dto.bootstrap_critic_obs.fill_(777.0)
    _assert(not torch.equal(dto.bootstrap_critic_obs, torch.full_like(dto.bootstrap_critic_obs, 777.0)), "DTO getter aliases storage")
    return {"exact_binding": True, "ordered_stages": len(expected), "mutable_alias": False}


def test_i6_6_continuation_second_step_zero_b1_and_current_tplus1() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    first = harness.route.collect_step()
    second = harness.route.collect_step()
    _assert(first.facade_result.claim_artifact is not None, "first proposal batch did not claim")
    _assert(second.facade_result.claim_artifact is None, "continuation/noop repeated B1")
    _assert(second.facade_result.resolution.claim_count == 0, "continuation entered M1 request")
    _assert(second.next_decision_bundle.evidence_identity.transition_generations == tuple(item + 1 for item in second.decision_bundle.evidence_identity.transition_generations), "t+1 transition identity")
    return {"first_B1": 1, "second_B1": 0, "next_current": "t+1"}


def test_i6_7_stale_and_partial_failure_fail_closed() -> dict[str, object]:
    harness = Harness()
    harness.route.reset()
    stale = harness.route.current_decision_bundle
    # Move authoritative state without inserting an actor or critic transition.
    harness.domain.environment_port.finalize_physical_transition(
        I4._report(harness.domain, problem=harness.raw.problem, step=9)
    )
    actor_slots = tuple(storage.next_action_slot for storage in harness.route.actor_storages)
    critic_slot = harness.buffer.step
    _expect(harness.route.collect_step, "source_publication_mismatch")
    _assert(harness.route.current_decision_bundle is stale, "stale bundle rebound")
    _assert(tuple(storage.next_action_slot for storage in harness.route.actor_storages) == actor_slots and harness.buffer.step == critic_slot, "pre-step failure partially inserted")

    broken = Harness()
    broken.route.reset()
    original_supplier = broken.route._current_decision_supplier
    calls = 0
    def fail_after_step():
        nonlocal calls
        calls += 1
        if calls >= 1:
            raise RuntimeError("synthetic post-step capture failure")
        return original_supplier()
    broken.route._current_decision_supplier = fail_after_step
    try:
        broken.route.collect_step()
    except RuntimeError as exc:
        _assert("synthetic post-step" in str(exc), "wrong synthetic failure")
    else:
        raise AssertionError("expected post-step failure")
    _assert(broken.route.poisoned, "irreversible post-step failure did not poison")
    _assert(broken.buffer.step == 0 and all(storage.next_action_slot == 0 for storage in broken.route.actor_storages), "post-step failure partially inserted")
    _expect(broken.route.collect_step, "route_poisoned")
    return {"stale_rebind": False, "preinsert_partial": False, "poststep_poison": True}


def test_i6_8_private_gate_default_isolation_and_public_block() -> dict[str, object]:
    descriptor = ROUTE.get_dormant_event_learned_policy_route_descriptor_v2()
    _assert(ROUTE.__all__ == (), "I6 route publicly exported")
    _assert(descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R", "readiness opened")
    wrapper_source = (SCAN_SOURCE / "assignment_harl_wrapper.py").read_text(encoding="utf-8")
    training_source = (SCAN_SOURCE / "assignment_harl_training.py").read_text(encoding="utf-8")
    _assert("assignment_event_learned_route" not in wrapper_source + training_source, "public/default route wired")
    harness = Harness()
    harness.wrapper.reset()
    before = harness.raw.step_calls
    try:
        harness.wrapper.step(torch.zeros((E, M, 1), dtype=torch.float32))
    except RuntimeError as exc:
        _assert("not runtime-ready" in str(exc), "wrong public readiness failure")
    else:
        raise AssertionError("public event step opened")
    _assert(harness.raw.step_calls == before, "public block reached physical step")
    return {"default_composition_calls": 0, "private_exports": 0, "public_step": "fail_closed"}


def test_i6_9_no_stock_fallback_no_math_duplication_static() -> dict[str, object]:
    source = (SCAN_SOURCE / "assignment_event_learned_route.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    attrs = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    _assert("compute_returns" not in attrs, "stock compute_returns selected")
    _assert("train" not in attrs, "stock actor/critic train called directly")
    _assert("backward" not in attrs and "step" not in {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute) and node.func.value.attr.endswith("optimizer")}, "optimizer math duplicated")
    _assert("compute_event_returns" in attrs, "event returns not explicitly selected")
    _assert("collect_event_policy_proposals_v2" in source and "train_event_policy_happo_sequence_v2" in source, "reviewed actor seams absent")
    return {"stock_actor_sampling": 0, "stock_returns": 0, "stock_happo_train": 0, "duplicated_math": 0}


def test_i6_10_protected_hashes() -> dict[str, object]:
    for name, expected in PROTECTED_REPO_HASHES.items():
        _assert(_sha256(SCAN_SOURCE / name) == expected, f"protected repo hash changed: {name}")
    for name, expected in PROTECTED_HARL_HASHES.items():
        _assert(_sha256(HARL_ROOT / name) == expected, f"installed HARL hash changed: {name}")
    return {"repo_protected": len(PROTECTED_REPO_HASHES), "installed_harl": len(PROTECTED_HARL_HASHES)}


TESTS = (
    ("B2-I6-T1", test_i6_1_reset_exact_slot0_and_no_sampling),
    ("B2-I6-T2", test_i6_2_mixed_rows_noop_conflict_and_proposal_effective_separation),
    ("B2-I6-T3", test_i6_3_terminal_transport_autoreset_timeout_once_and_six_tuple),
    ("B2-I6-T4", test_i6_4_rollout_returns_train_order_and_rollover),
    ("B2-I6-T5", test_i6_5_call_order_exact_binding_and_no_alias),
    ("B2-I6-T6", test_i6_6_continuation_second_step_zero_b1_and_current_tplus1),
    ("B2-I6-T7", test_i6_7_stale_and_partial_failure_fail_closed),
    ("B2-I6-T8", test_i6_8_private_gate_default_isolation_and_public_block),
    ("B2-I6-T9", test_i6_9_no_stock_fallback_no_math_duplication_static),
    ("B2-I6-T10", test_i6_10_protected_hashes),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = []
    for name, test in TESTS:
        detail = test()
        results.append({"name": name, "status": "PASS", "detail": detail})
    payload = {"suite": "assignment_phase_b2_i6_dormant_learned_event_route_composition_pure", "passed": len(results), "total": len(TESTS), "results": results}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for result in results:
            print(f"[PASS] {result['name']}: {result['detail']}")
        print(f"SUMMARY: {len(results)}/{len(TESTS)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
