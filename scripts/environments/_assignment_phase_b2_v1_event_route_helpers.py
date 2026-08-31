"""Shared pure/synthetic helpers for the Phase B2-V1 verification gate.

This is test support only.  It composes the reviewed I1--I6 production
primitives around a task-local physical boundary and recording actor/critic
seams.  It does not import or launch Isaac/AppLauncher and it never invokes an
optimizer, training runner, playback, evaluation, or checkpoint path.
"""

from __future__ import annotations

import importlib.util
import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts" / "environments"
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
I6_FIXTURE = SCRIPTS / "test_assignment_phase_b2_i6_dormant_learned_event_route_composition_pure.py"
DEVICE = torch.device("cpu")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_path(name: str, path: Path) -> Any:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    assert_true(spec is not None and spec.loader is not None, f"loader missing: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


I6 = load_path("_phase_b2_v1_i6_fixture", I6_FIXTURE)
I4 = I6.I4
BASE = I6.BASE
TRANSITION = I6.TRANSITION
EVIDENCE = I6.EVIDENCE
DECISION = I6.DECISION
COLLECTION = I6.COLLECTION
LT = I6.LT
CB = I6.CB
ROUTE = I6.ROUTE
HAPPO = load_path(
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_happo_policy_math",
    SCAN_SOURCE / "assignment_event_happo_policy_math.py",
)
Reason = TRANSITION.TerminationReason
RobotState = TRANSITION.RobotLifecycleState
TaskState = TRANSITION.TaskLifecycleState


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class ScriptedActor:
    """Installed-HARL-shaped recorder with exact compact-subset scripts."""

    def __init__(self, batches: list[list[int]], base_logprob: float) -> None:
        self.batches = [list(batch) for batch in batches]
        self.base_logprob = float(base_logprob)
        self.calls: list[dict[str, Any]] = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        call_id = len(self.calls)
        assert_true(call_id < len(self.batches), "unexpected actor call")
        actions = torch.tensor(self.batches[call_id], dtype=torch.int64, device=obs.device).view(-1, 1)
        assert_true(actions.shape[0] == obs.shape[0], "scripted compact actor batch mismatch")
        self.calls.append(
            {
                "obs": obs.detach().clone(),
                "rnn": rnn_states.detach().clone(),
                "masks": masks.detach().clone(),
                "available": available_actions.detach().clone(),
                "deterministic": bool(deterministic),
            }
        )
        logprobs = torch.full(
            (obs.shape[0], 1),
            self.base_logprob - 0.01 * call_id,
            dtype=torch.float32,
            device=obs.device,
        )
        return actions, logprobs, rnn_states.detach().clone() + 1.0


class FirstLegalActor:
    """Select the first legal task on each compact DVM row."""

    def __init__(self, base_logprob: float) -> None:
        self.base_logprob = float(base_logprob)
        self.calls: list[dict[str, Any]] = []

    def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
        legal_tasks = available_actions[:, :-1]
        assert_true(bool(legal_tasks.any(dim=1).all().item()), "policy row lacks a legal task")
        actions = legal_tasks.to(torch.int64).argmax(dim=1, keepdim=True)
        self.calls.append(
            {
                "obs": obs.detach().clone(),
                "available": available_actions.detach().clone(),
                "deterministic": bool(deterministic),
            }
        )
        logs = torch.full((obs.shape[0], 1), self.base_logprob, dtype=torch.float32, device=obs.device)
        return actions, logs, rnn_states.detach().clone() + 1.0


class RecordingSumCritic(torch.nn.Module):
    """No-grad recorder; its output makes pre/post-reset contamination visible."""

    def __init__(self) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.ones((1,), dtype=torch.float32))
        self.calls: list[dict[str, Any]] = []

    def get_values(self, obs, rnn, masks):
        self.calls.append(
            {
                "obs": obs.detach().clone(),
                "rnn": rnn.detach().clone(),
                "masks": masks.detach().clone(),
                "grad": torch.is_grad_enabled(),
            }
        )
        values = obs.detach().sum(dim=1, keepdim=True)
        return values, rnn.detach().clone() + 0.25


class SyntheticEventEnvironment(BASE._EventEnvironment):
    """Fixed-cardinality physical boundary for V1 lifecycle and scale cases."""

    def __init__(self, profile: Any, domain: Any, *, scenario: str) -> None:
        super().__init__(profile, domain)
        self.E = domain.identity.num_envs
        self.M = domain.identity.num_robots
        self.N = domain.identity.num_tasks
        self.scenario = scenario
        self.problem = I4._problem(E=self.E, M=self.M, N=self.N)
        self.progress = torch.zeros((self.E,), dtype=torch.int64)
        self.coverage = torch.zeros((self.E, self.N), dtype=torch.bool)
        self.route_steps = 0
        feasible = self.problem["feasible_mask"]
        costs = self.problem["cost_matrix"]
        feasible.zero_()
        costs.fill_(50.0)
        if scenario == "lifecycle":
            assert_true((self.E, self.M, self.N) == (4, 3, 4), "lifecycle scenario scale")
            feasible[0, 0, 0] = True
            feasible[0, 1, 0] = True
            feasible[1, 0, 1] = True
            feasible[3, 0, 2] = True
            feasible[3, 1, 2] = True
            feasible[3, 0, 3] = True
            costs[0, 0, 0], costs[0, 1, 0] = 3.0, 1.0
            costs[1, 0, 1] = 1.0
            costs[3, 0, 2], costs[3, 1, 2], costs[3, 0, 3] = 1.0, 2.0, 4.0
        elif scenario == "scale":
            feasible[:, :, 0] = True
            for robot_id in range(self.M):
                costs[:, robot_id, 0] = float(robot_id + 1)
        else:
            raise AssertionError(f"unknown synthetic scenario: {scenario}")

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
        completion = torch.zeros((self.E, self.M, self.N), dtype=torch.bool)
        truncated = torch.zeros((self.E,), dtype=torch.bool)
        if self.scenario == "lifecycle":
            if self.route_steps == 0:
                completion[2, 0, self.N - 1] = True
                truncated[1] = True
            elif self.route_steps == 1:
                completion[3, 0, 2] = True
            elif self.route_steps == 2:
                truncated[1] = True
            # A is captured in the pre-reset sidecar; B is written only after
            # autoreset and is therefore the next current actor/critic state.
            if bool(truncated[1].item()):
                self.problem["base_pos"][1].fill_(100.0 + self.route_steps)
                self.problem["scanner_pos"][1].fill_(120.0 + self.route_steps)
        report = I4._report(
            self.domain,
            problem=self.problem,
            step=self.route_steps + 1,
            completion=completion,
            coverage=self.coverage,
            truncated=truncated,
        )
        outcome = self.lifecycle.finalize_physical_transition(report)
        self.coverage |= completion.any(dim=1)
        done = outcome.terminated | outcome.truncated
        done_ids = torch.nonzero(done, as_tuple=False).flatten().tolist()
        if done_ids:
            self.validation.validate_reset_entry_for_active_call()
            I4._reset(self.domain, done_ids)
            self.coverage[done] = False
            self.progress[done] = 0
            if self.scenario == "lifecycle" and bool(done[1].item()):
                self.problem["base_pos"][1].fill_(-100.0 - self.route_steps)
                self.problem["scanner_pos"][1].fill_(-120.0 - self.route_steps)
            if self.scenario == "lifecycle" and self.route_steps == 0 and bool(done[2].item()):
                # A forced-noop row at t0 becomes a genuine policy row at t1.
                self.problem["feasible_mask"][2, 1, 0] = True
                self.problem["cost_matrix"][2, 1, 0] = 1.0
        self.progress[~done] += 1
        self.route_steps += 1
        rewards = {
            name: torch.full((self.E,), float(agent_id + 1), dtype=torch.float32)
            for agent_id, name in enumerate(self.possible_agents)
        }
        terminated = {name: outcome.terminated.detach().clone() for name in self.possible_agents}
        truncated_map = {name: outcome.truncated.detach().clone() for name in self.possible_agents}
        return self._obs(), rewards, terminated, truncated_map, {"route": self.scenario}


class RouteHarness:
    """Reusable production I1--I6 composition at one fixed scale."""

    def __init__(self, *, E: int, M: int, N: int, T: int, scenario: str) -> None:
        self.E, self.M, self.N, self.T = E, M, N, T
        self.profile = BASE._profile()
        self.domain = BASE._domain(self.profile, envs=E, robots=M, tasks=N)
        self.raw = SyntheticEventEnvironment(self.profile, self.domain, scenario=scenario)
        self.view = BASE._WrapperView(self.raw)
        self.wrapper = BASE.WRAPPER._compose_event_assignment_harl_wrapper(
            env=self.view,
            resolved_assignment_profile=self.profile,
            runtime_domain=self.domain,
        )
        self.scale = I4._scale(M=M, N=N)
        self.events: list[tuple[str, object | None]] = []
        if scenario == "lifecycle":
            self.actors = (
                ScriptedActor([[0, N, 2], [N], [1, 3], [N]], -0.10),
                ScriptedActor([[0, 2], [0]], -0.20),
                ScriptedActor([], -0.30),
            )
        else:
            self.actors = tuple(FirstLegalActor(-0.10 - 0.10 * agent_id) for agent_id in range(M))
        self.critic = RecordingSumCritic()
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
            call_observer=self._observe,
        )
        self.scenario = scenario

    def _observe(self, stage: str, detail: object | None) -> None:
        self.events.append((stage, detail))

    def _admitted_reset(self):
        result = self.wrapper.reset()
        if self.scenario == "lifecycle":
            # Make env2's first transition a genuine ALL_TASKS_COMPLETED row.
            for task_id in range(self.N - 1):
                I4._seed(self.domain, env_id=2, task_id=task_id)
                completion = torch.zeros((self.E, self.M, self.N), dtype=torch.bool)
                completion[2, 0, task_id] = True
                self.domain.environment_port.finalize_physical_transition(
                    I4._report(
                        self.domain,
                        problem=self.raw.problem,
                        step=task_id + 1,
                        completion=completion,
                        coverage=self.raw.coverage,
                    )
                )
                self.raw.coverage[2, task_id] = True
            I4._seed(self.domain, env_id=2, task_id=self.N - 1)
        return result

    def _current_bundle(self):
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
        return DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)

    def _validate_current(self, bundle):
        bundle.evidence_snapshot.validate_current(
            current_publication=self.domain.current_read_port.read_current(),
            current_open_window_view=self.domain.interstep_fence_read_port.read(),
        )

    def _actor_trainer(self, **kwargs):
        self.actor_train_calls.append(kwargs)
        return {"route": "V1_actor_recorder", "optimizer_calls": 0}

    def _critic_trainer(self, buffer, value_normalizer):
        self.critic_train_calls.append({"buffer": buffer, "value_normalizer": value_normalizer})
        return {"route": "V1_critic_recorder", "optimizer_calls": 0}

    def run_rollout(self):
        reset_result = self.route.reset()
        receipts = tuple(self.route.collect_step() for _ in range(self.T))
        rollout = self.route.finish_rollout(agent_order=tuple(range(self.M)))
        return reset_result, receipts, rollout


def expect_failure(call: Callable[[], object], code: str | None = None) -> BaseException:
    try:
        call()
    except BaseException as exc:
        if code is not None:
            assert_true(getattr(exc, "failure_code", None) == code, f"expected {code}, got {exc}")
        return exc
    raise AssertionError(f"expected failure {code or ''}")


def lifecycle_harness() -> RouteHarness:
    return RouteHarness(E=4, M=3, N=4, T=3, scenario="lifecycle")


def scale_harness() -> RouteHarness:
    return RouteHarness(E=2, M=2, N=4, T=2, scenario="scale")


def run_tests(*, suite: str, tests: tuple[tuple[str, Callable[[], dict[str, object]]], ...]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = []
    for name, test in tests:
        detail = test()
        results.append({"name": name, "status": "PASS", "detail": detail})
    payload = {"suite": suite, "passed": len(results), "total": len(tests), "results": results}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for result in results:
            print(f"[PASS] {result['name']}: {result['detail']}")
        print(f"SUMMARY: {len(results)}/{len(tests)} PASS")
    return 0
