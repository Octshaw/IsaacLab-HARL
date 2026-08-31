"""Pure/synthetic B2-I5a learner transport, critic, and buffer verification.

This fixture never launches Isaac/AppLauncher, an environment rollout, a HARL
runner, an optimizer, training, playback, evaluation, or checkpoint code.  It
uses the frozen I4 task-local fake producer, a synthetic no-grad critic, and the
repo-local EP buffer subclass only.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
I4_PATH = (
    REPO_ROOT
    / "scripts"
    / "environments"
    / "test_assignment_phase_b2_i4_authoritative_prereset_terminal_critic_sidecar_pure.py"
)
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEVICE = torch.device("cpu")


def _load_path(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


I4 = _load_path("_phase_b2_i5a_i4_helpers", I4_PATH)
BASE = I4.BASE
TRANSPORT = I4.TRANSPORT
SIDECAR = I4.SIDECAR
FACADE = sys.modules[f"{PREFIX}.assignment_event_runtime_facade"]
TRANSITION = I4.TRANSITION
Reason = TRANSITION.TerminationReason
LT = _load_path(
    f"{PREFIX}.assignment_event_terminal_learner_transport",
    SCAN_SOURCE / "assignment_event_terminal_learner_transport.py",
)
CB = _load_path(
    f"{PREFIX}.assignment_event_critic_buffer",
    SCAN_SOURCE / "assignment_event_critic_buffer.py",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect(operation: Callable[[], object], *, code: str) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        _assert(getattr(exc, "failure_code", None) == code, f"wrong failure: {exc}")
        return exc
    raise AssertionError("expected failure")


def _expectation_from_publication(publication: Any) -> Any:
    episodes = tuple(int(item) for item in publication.episode_generation.tolist())
    transitions = tuple(int(item) for item in publication.transition_generation.tolist())
    instance = object.__new__(LT.EventLearnerTransitionExpectationV2)
    for name, value in (
        ("schema_version", LT.EVENT_LEARNER_TRANSITION_EXPECTATION_V2),
        ("profile_name", "event_gated_local_mrta"),
        ("p2_publication_identity", publication.publication_identity),
        ("open_window_identity", object()),
        ("env_ids", tuple(range(len(episodes)))),
        ("episode_generations", episodes),
        ("source_transition_generations", transitions),
        ("expected_transition_generations", tuple(item + 1 for item in transitions)),
    ):
        object.__setattr__(instance, name, value)
    return instance


def _timeout_history(*, E: int = 2) -> tuple[Any, Any, tuple[Any, ...], tuple[Any, ...], Any]:
    domain = BASE._domain(BASE._profile(), envs=E, robots=3, tasks=12)
    I4._reset(domain)
    source = domain.current_read_port.read_current()
    problem = I4._problem(E=E, M=3, N=12)
    outcome = domain.environment_port.finalize_physical_transition(
        I4._report(
            domain,
            problem=problem,
            step=999,
            truncated=torch.ones((E,), dtype=torch.bool),
        )
    )
    artifacts = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    I4._reset(domain)
    current = domain.current_read_port.read_current()
    history = TRANSPORT._copy_and_validate_terminal_history(
        captured_artifacts=artifacts,
        environment_result=(
            {},
            {},
            {"agent": outcome.terminated},
            {"agent": outcome.truncated},
            {},
        ),
        current_publication=current,
    )
    acknowledged = domain.terminal_consumer_port.acknowledge_terminal_batch(
        tuple(row.key for row in history)
    )
    _assert(tuple(id(item) for item in acknowledged) == tuple(id(item) for item in artifacts), "ACK")
    return source, current, history, artifacts, domain


def _prototype_sidecar() -> Any:
    _, _, history, _, _ = _timeout_history(E=1)
    return history[0].optional_sidecar


PROTOTYPE_SIDECAR = _prototype_sidecar()
S = PROTOTYPE_SIDECAR.critic_dimension


def _synthetic_historical(
    *,
    env_id: int,
    episode_generation: int,
    transition_generation: int,
    reason: int,
    first_value: float = 0.0,
) -> Any:
    key = BASE.B02._TerminalTransitionKey(env_id, episode_generation, transition_generation)
    evidence = PROTOTYPE_SIDECAR.terminal_audit_projection.semantic_evidence
    evidence.zero_()
    evidence[0] = float(first_value)
    audit = SIDECAR.TerminalAuditProjectionV2._create(
        key=key,
        termination_reason=reason,
        critic_schema_version=PROTOTYPE_SIDECAR.critic_schema_version,
        semantic_evidence=evidence,
    )
    timeout = reason == int(Reason.TIME_LIMIT)
    terminated, truncated = ((False, True) if timeout else (True, False))
    sidecar = SIDECAR.EventTerminalCriticSidecarV2._create(
        key=key,
        reason=reason,
        terminated=terminated,
        truncated=truncated,
        published_store_version=100 + env_id,
        source_p2_publication_identity=object(),
        terminal_audit_projection=audit,
        bootstrap_critic_obs=evidence if timeout else None,
        critic_schema_version=PROTOTYPE_SIDECAR.critic_schema_version,
        critic_block_layout=PROTOTYPE_SIDECAR.critic_block_layout,
        physical_provenance=PROTOTYPE_SIDECAR.physical_provenance,
    )
    historical = object.__new__(TRANSPORT.EventTerminalHistoricalRow)
    for name, value in (
        ("env_id", env_id),
        ("episode_generation", episode_generation),
        ("transition_generation", transition_generation),
        ("termination_reason", reason),
        ("terminated", terminated),
        ("truncated", truncated),
        ("result_schema_version", "synthetic_exact_i5a_result_v2"),
        ("authority_contract_version", "synthetic_exact_i5a_authority_v2"),
        ("published_store_version", 100 + env_id),
        ("optional_sidecar", sidecar),
    ):
        object.__setattr__(historical, name, value)
    return historical


def _record(
    *, env_id: int, episode: int, transition: int, reason: int, first_value: float = 0.0
) -> Any:
    return LT.make_event_terminal_learner_record_v2(
        _synthetic_historical(
            env_id=env_id,
            episode_generation=episode,
            transition_generation=transition,
            reason=reason,
            first_value=first_value,
        )
    )


def _expectation(*, E: int, episode: int = 7, source_transition: int = 10) -> Any:
    instance = object.__new__(LT.EventLearnerTransitionExpectationV2)
    for name, value in (
        ("schema_version", LT.EVENT_LEARNER_TRANSITION_EXPECTATION_V2),
        ("profile_name", "event_gated_local_mrta"),
        ("p2_publication_identity", object()),
        ("open_window_identity", object()),
        ("env_ids", tuple(range(E))),
        ("episode_generations", (episode,) * E),
        ("source_transition_generations", (source_transition,) * E),
        ("expected_transition_generations", (source_transition + 1,) * E),
    ):
        object.__setattr__(instance, name, value)
    return instance


def _infos(*, E: int, M: int, records: dict[int, Any]) -> list[list[dict[str, object]]]:
    result = [[{} for _ in range(M)] for _ in range(E)]
    for env_id, record in records.items():
        result[env_id][0][LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2] = record
    return result


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class RecordingCritic(torch.nn.Module):
    def __init__(self, *, output_mode: str = "normal", mutate_parameter: bool = False) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.tensor([1.0], dtype=torch.float32))
        self.output_mode = output_mode
        self.mutate_parameter = mutate_parameter
        self.calls: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor, bool]] = []
        self.last_output: torch.Tensor | None = None

    def get_values(self, obs: torch.Tensor, rnn: torch.Tensor, masks: torch.Tensor):
        self.calls.append(
            (
                obs.detach().clone(),
                rnn.detach().clone(),
                masks.detach().clone(),
                torch.is_grad_enabled(),
            )
        )
        if self.mutate_parameter:
            with torch.no_grad():
                self.anchor.add_(1.0)
        if self.output_mode == "shape":
            values = obs[:, 0]
        elif self.output_mode == "nan":
            values = torch.full((obs.shape[0], 1), float("nan"), device=obs.device)
        elif self.output_mode == "dtype":
            values = obs[:, :1].to(torch.float64)
        elif self.output_mode == "device":
            values = torch.empty((obs.shape[0], 1), dtype=torch.float32, device="meta")
        else:
            values = obs[:, :1].detach().clone()
        self.last_output = values
        return values, rnn.detach().clone()


def _buffer(E: int, *, T: int = 3) -> Any:
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
    return CB.EventOnPolicyCriticBufferEPV2(args, Box((S,)), device=DEVICE)


def _step(
    *, E: int, M: int, dones: torch.Tensor, infos: object, current_share_value: float = -999.0
) -> tuple[object, torch.Tensor, torch.Tensor, torch.Tensor, object, object]:
    obs = {f"agent_{agent}": torch.full((E, 2), current_share_value) for agent in range(M)}
    share_obs = torch.full((E, M, S), current_share_value, dtype=torch.float32)
    rewards = torch.arange(E, dtype=torch.float32).reshape(E, 1, 1).expand(E, M, 1).clone()
    available = torch.ones((E, M, 2), dtype=torch.float32)
    return obs, share_obs, rewards, dones, infos, available


def _consume(
    *,
    expectation: Any,
    step_result: tuple[Any, ...],
    critic: RecordingCritic,
    buffer: Any,
    slot: int = 0,
) -> tuple[Any, Any]:
    guard = LT.capture_event_rollout_critic_guard_v2(critic)
    collector = CB.EventTerminalLearnerCollectorV2(critic_buffer=buffer)
    batch = collector.consume_before_optimizer_update(
        transition_slot=slot,
        expectation=expectation,
        harl_step_result=step_result,
        value_preds=torch.zeros((buffer.n_rollout_threads, 1), dtype=torch.float32),
        rnn_states_critic_after_current=torch.zeros(
            (buffer.n_rollout_threads, 1, 4), dtype=torch.float32
        ),
        critic=critic,
        rollout_critic_guard=guard,
    )
    return collector, batch


def test_i5a_1_copy_ack_six_tuple_and_no_alias() -> dict[str, object]:
    source, current, history, artifacts, domain = _timeout_history(E=2)
    expectation = _expectation_from_publication(source)
    facade = object.__new__(FACADE.EventFacadeStepResult)
    for name, value in (
        ("source_publication", source),
        ("current_publication", current),
        ("terminal_historical_payload", history),
    ):
        object.__setattr__(facade, name, value)
    dones = torch.ones((2, 3), dtype=torch.bool)
    base_infos = [[{} for _ in range(3)] for _ in range(2)]
    base = _step(E=2, M=3, dones=dones, infos=base_infos)
    transported = LT.attach_event_terminal_infos_to_harl_step_v2(
        harl_step_result=base,
        facade_result=facade,
        expectation=expectation,
    )
    _assert(len(transported) == 6, "six-element return changed")
    for index in (0, 1, 2, 3, 5):
        _assert(transported[index] is base[index], f"slot {index} replaced")
    records = tuple(
        transported[4][env][0][LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2]
        for env in range(2)
    )
    before = tuple(record.bootstrap_critic_obs for record in records)
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "ACK delayed")
    for artifact in artifacts:
        artifact.optional_sidecar._bootstrap_critic_obs.fill_(777.0)
        artifact.optional_sidecar._terminal_audit_projection._semantic_evidence.fill_(888.0)
    domain.environment_port.finalize_physical_transition(
        I4._report(domain, problem=I4._problem(E=2, M=3, N=12), step=1)
    )
    _assert(
        all(torch.equal(record.bootstrap_critic_obs, value) for record, value in zip(records, before)),
        "learner DTO aliases ACK-released runtime evidence",
    )
    return {"arity": 6, "infos_location": "infos[env][0]", "ACK_before_learner": True, "alias": False}


def test_i5a_2_missing_duplicate_stale_wrong_env_reason_and_sidecar() -> dict[str, object]:
    E, M = 2, 2
    expectation = _expectation(E=E)
    timeout = _record(env_id=0, episode=7, transition=11, reason=int(Reason.TIME_LIMIT))
    done0 = torch.tensor([[True, True], [False, False]])
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={})
        ),
        code="terminal_dto_missing",
    )
    duplicate = _infos(E=E, M=M, records={0: timeout})
    duplicate[0][1][LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2] = timeout
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=duplicate
        ),
        code="terminal_dto_location",
    )
    stale = copy.copy(timeout)
    object.__setattr__(stale, "correlation_key", LT.EventTerminalCorrelationKeyV2(0, 7, 12))
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={0: stale})
        ),
        code="terminal_dto_stale",
    )
    wrong_env = copy.copy(timeout)
    object.__setattr__(wrong_env, "correlation_key", LT.EventTerminalCorrelationKeyV2(1, 7, 11))
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={0: wrong_env})
        ),
        code="terminal_dto_env",
    )
    wrong_done = copy.copy(timeout)
    object.__setattr__(wrong_done, "terminated", True)
    object.__setattr__(wrong_done, "truncated", False)
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={0: wrong_done})
        ),
        code="terminal_dto_reason_done",
    )
    wrong_reason = copy.copy(timeout)
    object.__setattr__(wrong_reason, "termination_reason", int(Reason.ALL_TASKS_COMPLETED))
    object.__setattr__(wrong_reason, "terminated", True)
    object.__setattr__(wrong_reason, "truncated", False)
    object.__setattr__(wrong_reason, "bootstrap_projection_valid", False)
    object.__setattr__(wrong_reason, "_bootstrap_critic_obs", None)
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={0: wrong_reason})
        ),
        code="terminal_dto_audit_binding",
    )
    nonterminal = _infos(
        E=E,
        M=M,
        records={
            0: timeout,
            1: _record(
                env_id=1,
                episode=7,
                transition=11,
                reason=int(Reason.TIME_LIMIT),
            ),
        },
    )
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=nonterminal
        ),
        code="nonterminal_dto_present",
    )
    timeout_absent = copy.copy(timeout)
    object.__setattr__(timeout_absent, "_bootstrap_critic_obs", None)
    _expect(
        lambda: LT.correlate_event_terminal_infos_v2(
            expectation=expectation, dones=done0, infos=_infos(E=E, M=M, records={0: timeout_absent})
        ),
        code="terminal_dto_bootstrap_presence",
    )
    missing_sidecar = _synthetic_historical(
        env_id=0,
        episode_generation=7,
        transition_generation=11,
        reason=int(Reason.TIME_LIMIT),
    )
    object.__setattr__(missing_sidecar, "optional_sidecar", None)
    _expect(lambda: LT.make_event_terminal_learner_record_v2(missing_sidecar), code="learner_sidecar_missing")
    return {"missing": "rejected", "duplicate": "rejected", "stale": "rejected", "wrong_env": "rejected", "wrong_reason": "rejected", "wrong_done": "rejected", "nonterminal_DTO": "rejected", "timeout_sidecar_absent": "rejected", "sidecar_absent": "rejected"}


def test_i5a_3_mixed_e4_timeout_only_and_t_t1_alignment() -> dict[str, object]:
    E, M = 4, 3
    expectation = _expectation(E=E)
    records = {
        1: _record(env_id=1, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=10.0),
        2: _record(env_id=2, episode=7, transition=11, reason=int(Reason.ALL_TASKS_COMPLETED)),
        3: _record(env_id=3, episode=7, transition=11, reason=int(Reason.NO_FEASIBLE_TASKS_REMAIN)),
    }
    dones = torch.tensor(
        [[False] * M, [True] * M, [True] * M, [True] * M], dtype=torch.bool
    )
    step_result = _step(E=E, M=M, dones=dones, infos=_infos(E=E, M=M, records=records))
    critic = RecordingCritic()
    buffer = _buffer(E)
    _, batch = _consume(expectation=expectation, step_result=step_result, critic=critic, buffer=buffer)
    expected_reasons = torch.tensor(
        [int(Reason.NONE), int(Reason.TIME_LIMIT), int(Reason.ALL_TASKS_COMPLETED), int(Reason.NO_FEASIBLE_TASKS_REMAIN)],
        dtype=torch.int64,
    )
    _assert(len(critic.calls) == 1 and critic.calls[0][0].shape == (1, S), "critic row subset")
    _assert(float(critic.calls[0][0][0, 0].item()) == 10.0, "post-reset share_obs entered critic")
    _assert(critic.calls[0][3] is False, "timeout critic retained gradients")
    _assert(torch.equal(buffer.termination_reason[0, :, 0], expected_reasons), "reason[t]")
    _assert(torch.equal(buffer.timeout_bootstrap_masks[0, :, 0], torch.tensor([False, True, False, False])), "timeout masks")
    _assert(float(buffer.timeout_bootstrap_value_preds[0, 1, 0].item()) == 10.0, "timeout value")
    _assert(torch.equal(buffer.share_obs[1], step_result[1][:, 0]), "current share_obs not at t+1")
    _assert(not bool((buffer.share_obs[1] == 10.0).all().item()), "historical timeout overwrote t+1")
    _assert(torch.equal(buffer.bad_masks[1, :, 0], torch.tensor([1.0, 0.0, 1.0, 1.0])), "bad_masks compatibility")
    return {"E": 4, "critic_envs": [1], "reason_slot": 0, "current_state_slot": 1, "post_reset_trap": "passed"}


def test_i5a_4_batched_timeout_gather_scatter() -> dict[str, object]:
    E, M = 4, 2
    expectation = _expectation(E=E)
    records = {
        1: _record(env_id=1, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=10.0),
        3: _record(env_id=3, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=30.0),
    }
    dones = torch.tensor([[False] * M, [True] * M, [False] * M, [True] * M])
    critic = RecordingCritic()
    buffer = _buffer(E)
    _, batch = _consume(
        expectation=expectation,
        step_result=_step(E=E, M=M, dones=dones, infos=_infos(E=E, M=M, records=records)),
        critic=critic,
        buffer=buffer,
    )
    _assert(len(critic.calls) == 1 and batch.timeout_env_indices == (1, 3), "batched timeout call")
    _assert(torch.equal(buffer.timeout_bootstrap_value_preds[0, :, 0], torch.tensor([0.0, 10.0, 0.0, 30.0])), "scatter indices")
    _assert(torch.equal(buffer.timeout_bootstrap_masks[0, :, 0], torch.tensor([False, True, False, True])), "scatter masks")
    return {"critic_batch_calls": 1, "gather": [1, 3], "scatter": [0.0, 10.0, 0.0, 30.0]}


def test_i5a_5_true_terminals_zero_calls_and_audit_rejected() -> dict[str, object]:
    E, M = 2, 2
    expectation = _expectation(E=E)
    records = {
        0: _record(env_id=0, episode=7, transition=11, reason=int(Reason.ALL_TASKS_COMPLETED)),
        1: _record(env_id=1, episode=7, transition=11, reason=int(Reason.NO_FEASIBLE_TASKS_REMAIN)),
    }
    critic = RecordingCritic()
    buffer = _buffer(E)
    _, batch = _consume(
        expectation=expectation,
        step_result=_step(E=E, M=M, dones=torch.ones((E, M), dtype=torch.bool), infos=_infos(E=E, M=M, records=records)),
        critic=critic,
        buffer=buffer,
    )
    _assert(len(critic.calls) == 0 and batch.critic_batch_calls == 0, "true terminal critic call")
    _assert(not bool(buffer.timeout_bootstrap_masks.any().item()), "true terminal timeout mask")
    _expect(
        lambda: LT.evaluate_event_timeout_bootstrap_values_v2(
            timeout_input=records[0].terminal_audit,
            correlation=batch.correlation,
            critic=critic,
            rollout_critic_guard=LT.capture_event_rollout_critic_guard_v2(critic),
            rnn_states_critic_after_current=torch.zeros((E, 1, 4)),
        ),
        code="critic_input_type",
    )
    return {"true_terminal_critic_calls": 0, "TERMINAL_AUDIT_to_critic": "rejected"}


def test_i5a_6_exactly_once_duplicate_before_second_forward() -> dict[str, object]:
    E, M = 1, 2
    expectation = _expectation(E=E)
    record = _record(env_id=0, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=5.0)
    result = _step(E=E, M=M, dones=torch.ones((E, M), dtype=torch.bool), infos=_infos(E=E, M=M, records={0: record}))
    critic = RecordingCritic()
    buffer = _buffer(E)
    guard = LT.capture_event_rollout_critic_guard_v2(critic)
    collector = CB.EventTerminalLearnerCollectorV2(critic_buffer=buffer)
    kwargs = dict(
        expectation=expectation,
        harl_step_result=result,
        value_preds=torch.zeros((E, 1)),
        rnn_states_critic_after_current=torch.zeros((E, 1, 4)),
        critic=critic,
        rollout_critic_guard=guard,
    )
    collector.consume_before_optimizer_update(transition_slot=0, **kwargs)
    _expect(lambda: collector.consume_before_optimizer_update(transition_slot=1, **kwargs), code="terminal_dto_already_consumed")
    _assert(len(critic.calls) == 1, "duplicate caused a second critic call")
    return {"semantic_evaluations": 1, "duplicate_consumption": "fail_closed"}


def test_i5a_7_critic_guard_no_grad_and_no_mutation() -> dict[str, object]:
    E, M = 1, 1
    expectation = _expectation(E=E)
    record = _record(env_id=0, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=2.0)
    result = _step(E=E, M=M, dones=torch.ones((E, M), dtype=torch.bool), infos=_infos(E=E, M=M, records={0: record}))
    critic = RecordingCritic()
    guard = LT.capture_event_rollout_critic_guard_v2(critic)
    with torch.no_grad():
        critic.anchor.add_(1.0)
    collector = CB.EventTerminalLearnerCollectorV2(critic_buffer=_buffer(E))
    _expect(
        lambda: collector.consume_before_optimizer_update(
            transition_slot=0,
            expectation=expectation,
            harl_step_result=result,
            value_preds=torch.zeros((E, 1)),
            rnn_states_critic_after_current=torch.zeros((E, 1, 4)),
            critic=critic,
            rollout_critic_guard=guard,
        ),
        code="critic_snapshot_changed",
    )
    _assert(len(critic.calls) == 0, "changed critic was evaluated")
    mutating = RecordingCritic(mutate_parameter=True)
    mutating_guard = LT.capture_event_rollout_critic_guard_v2(mutating)
    _expect(
        lambda: CB.EventTerminalLearnerCollectorV2(critic_buffer=_buffer(E)).consume_before_optimizer_update(
            transition_slot=0,
            expectation=expectation,
            harl_step_result=result,
            value_preds=torch.zeros((E, 1)),
            rnn_states_critic_after_current=torch.zeros((E, 1, 4)),
            critic=mutating,
            rollout_critic_guard=mutating_guard,
        ),
        code="critic_snapshot_changed",
    )
    _assert(len(mutating.calls) == 1 and mutating.calls[0][3] is False, "no-grad forward")
    return {"pre_update_guard": "passed", "forward_no_grad": True, "forward_mutation": "rejected"}


def test_i5a_8_invalid_critic_outputs_fail_before_storage() -> dict[str, object]:
    E, M = 1, 1
    expectation = _expectation(E=E)
    record = _record(env_id=0, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=2.0)
    result = _step(E=E, M=M, dones=torch.ones((E, M), dtype=torch.bool), infos=_infos(E=E, M=M, records={0: record}))
    outcomes = {}
    for mode, code in (("shape", "critic_value_contract"), ("nan", "critic_value_nonfinite"), ("dtype", "critic_value_contract"), ("device", "critic_value_contract")):
        critic = RecordingCritic(output_mode=mode)
        buffer = _buffer(E)
        _expect(
            lambda c=critic, b=buffer: CB.EventTerminalLearnerCollectorV2(critic_buffer=b).consume_before_optimizer_update(
                transition_slot=0,
                expectation=expectation,
                harl_step_result=result,
                value_preds=torch.zeros((E, 1)),
                rnn_states_critic_after_current=torch.zeros((E, 1, 4)),
                critic=c,
                rollout_critic_guard=LT.capture_event_rollout_critic_guard_v2(c),
            ),
            code=code,
        )
        _assert(not bool(buffer._event_slot_written[0].item()), f"{mode} reached buffer")
        outcomes[mode] = "rejected"
    return outcomes


def test_i5a_9_buffer_and_source_no_alias() -> dict[str, object]:
    E, M = 1, 1
    expectation = _expectation(E=E)
    record = _record(env_id=0, episode=7, transition=11, reason=int(Reason.TIME_LIMIT), first_value=12.0)
    result = _step(E=E, M=M, dones=torch.ones((E, M), dtype=torch.bool), infos=_infos(E=E, M=M, records={0: record}), current_share_value=-44.0)
    critic = RecordingCritic()
    buffer = _buffer(E)
    _, batch = _consume(expectation=expectation, step_result=result, critic=critic, buffer=buffer)
    stored_value = buffer.timeout_bootstrap_value_preds.clone()
    stored_share = buffer.share_obs.clone()
    record._bootstrap_critic_obs.fill_(999.0)
    batch._timeout_bootstrap_value_preds.fill_(888.0)
    with torch.inference_mode():
        critic.last_output.fill_(777.0)
    result[1].fill_(666.0)
    _assert(torch.equal(buffer.timeout_bootstrap_value_preds, stored_value), "timeout value alias")
    _assert(torch.equal(buffer.share_obs, stored_share), "current share_obs alias")
    return {"DTO_alias": False, "bootstrap_obs_alias": False, "critic_output_alias": False, "current_share_alias": False}


def test_i5a_10_none_row_and_sanitized_infos() -> dict[str, object]:
    E, M = 2, 2
    expectation = _expectation(E=E)
    infos = [[{"ordinary": env + agent} for agent in range(M)] for env in range(E)]
    correlation = LT.correlate_event_terminal_infos_v2(
        expectation=expectation,
        dones=torch.zeros((E, M), dtype=torch.bool),
        infos=infos,
    )
    _assert(torch.equal(correlation.termination_reason, torch.zeros((E, 1), dtype=torch.int64)), "NONE reason")
    _assert(not bool(correlation.timeout_bootstrap_masks.any().item()), "NONE timeout")
    clean = correlation.sanitized_infos
    clean[0][0]["ordinary"] = 999
    _assert(correlation.sanitized_infos[0][0]["ordinary"] == 0, "sanitized info alias")
    return {"NONE_DTO_required": False, "timeout_mask": False, "sanitized_copy": True}


def test_i5a_11_no_gae_actor_hash_and_installed_hash_preservation() -> dict[str, object]:
    protected = {
        SCAN_SOURCE / "assignment_event_actor_collection.py": "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
        SCAN_SOURCE / "assignment_event_happo_policy_math.py": "3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4",
        SCAN_SOURCE / "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
        SCAN_SOURCE / "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
        Path("C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/common/buffers/on_policy_critic_buffer_ep.py"): "0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f",
        Path("C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/algorithms/critics/v_critic.py"): "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    }
    for path, expected in protected.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        _assert(actual == expected, f"protected hash drift: {path}")
    learner_tree = ast.parse((SCAN_SOURCE / "assignment_event_terminal_learner_transport.py").read_text(encoding="utf-8"))
    buffer_tree = ast.parse((SCAN_SOURCE / "assignment_event_critic_buffer.py").read_text(encoding="utf-8"))
    forbidden_calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for tree in (learner_tree, buffer_tree)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    _assert("compute_returns" not in forbidden_calls, "I5a calls compute_returns")
    _assert("train" not in forbidden_calls and "step" not in forbidden_calls, "optimizer/training call in I5a")
    _assert(not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "compute_returns" for node in ast.walk(buffer_tree)), "I5a overrides GAE")
    return {"protected_hashes": len(protected), "actor_changes": 0, "installed_changes": 0, "compute_returns_calls": 0, "optimizer_calls": 0}


TESTS: tuple[tuple[str, Callable[[], dict[str, object]]], ...] = (
    ("B2-I5A-T1", test_i5a_1_copy_ack_six_tuple_and_no_alias),
    ("B2-I5A-T2", test_i5a_2_missing_duplicate_stale_wrong_env_reason_and_sidecar),
    ("B2-I5A-T3", test_i5a_3_mixed_e4_timeout_only_and_t_t1_alignment),
    ("B2-I5A-T4", test_i5a_4_batched_timeout_gather_scatter),
    ("B2-I5A-T5", test_i5a_5_true_terminals_zero_calls_and_audit_rejected),
    ("B2-I5A-T6", test_i5a_6_exactly_once_duplicate_before_second_forward),
    ("B2-I5A-T7", test_i5a_7_critic_guard_no_grad_and_no_mutation),
    ("B2-I5A-T8", test_i5a_8_invalid_critic_outputs_fail_before_storage),
    ("B2-I5A-T9", test_i5a_9_buffer_and_source_no_alias),
    ("B2-I5A-T10", test_i5a_10_none_row_and_sanitized_infos),
    ("B2-I5A-T11", test_i5a_11_no_gae_actor_hash_and_installed_hash_preservation),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = []
    for name, test in TESTS:
        try:
            rows.append({"name": name, "status": "passed", "evidence": test()})
        except BaseException as exc:
            rows.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "cause": None if exc.__cause__ is None else f"{type(exc.__cause__).__name__}: {exc.__cause__}",
                }
            )
    passed = sum(row["status"] == "passed" for row in rows)
    payload = {
        "status": "passed" if passed == len(rows) else "failed",
        "passed": passed,
        "failed": len(rows) - passed,
        "num_tests": len(rows),
        "tests": rows,
    }
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload)
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
