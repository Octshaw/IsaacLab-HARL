"""Pure B2-I5b TIME_LIMIT bootstrap, event GAE, and ValueNorm oracles.

This fixture uses fixed CPU tensors and read-only installed HARL buffer/
ValueNorm components.  It never launches Isaac/AppLauncher, a rollout, actor or
critic inference, an optimizer, training, playback, evaluation, or checkpoint
code.
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
from harl.common.buffers.on_policy_critic_buffer_ep import OnPolicyCriticBufferEP
from harl.common.valuenorm import ValueNorm


REPO_ROOT = Path(__file__).resolve().parents[2]
I5A_PATH = (
    REPO_ROOT
    / "scripts"
    / "environments"
    / "test_assignment_phase_b2_i5a_historical_learner_transport_timeout_critic_buffer_pure.py"
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


I5A = _load_path("_phase_b2_i5b_i5a_helpers", I5A_PATH)
CB = I5A.CB
Reason = I5A.Reason
GAE = sys.modules[f"{PREFIX}.assignment_event_gae_returns"]
Box = I5A.Box


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _close(actual: torch.Tensor, expected: torch.Tensor, message: str) -> None:
    if not torch.allclose(actual, expected, atol=2e-5, rtol=2e-6):
        raise AssertionError(f"{message}: actual={actual}, expected={expected}")


def _expect(operation: Callable[[], object], *, code: str) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        _assert(getattr(exc, "failure_code", None) == code, f"wrong failure: {exc}")
        return exc
    raise AssertionError("expected failure")


def _buffer(E: int, T: int, *, gamma: float = 0.9, gae_lambda: float = 0.8) -> Any:
    args = {
        "episode_length": T,
        "n_rollout_threads": E,
        "hidden_sizes": [4],
        "recurrent_n": 1,
        "gamma": gamma,
        "gae_lambda": gae_lambda,
        "use_gae": True,
        "use_proper_time_limits": True,
    }
    return CB.EventOnPolicyCriticBufferEPV2(args, Box((5,)), device=DEVICE)


def _fill(
    buffer: Any,
    *,
    rewards: torch.Tensor,
    current_values: torch.Tensor,
    reasons: torch.Tensor,
    timeout_values: torch.Tensor,
    masks_after: torch.Tensor,
) -> None:
    T, E, _ = rewards.shape
    _assert((T, E) == (buffer.episode_length, buffer.n_rollout_threads), "buffer shape")
    buffer.rewards.copy_(rewards)
    buffer.value_preds[:-1].copy_(current_values)
    buffer.masks.fill_(1.0)
    buffer.masks[1:].copy_(masks_after)
    buffer.termination_reason.copy_(reasons)
    timeout_masks = reasons == int(Reason.TIME_LIMIT)
    buffer.timeout_bootstrap_masks.copy_(timeout_masks)
    buffer.timeout_bootstrap_value_preds.copy_(timeout_values)
    buffer._event_slot_written.fill_(True)


def _normalizer(*, cls: type[ValueNorm] = ValueNorm) -> ValueNorm:
    normalizer = cls(1, device=DEVICE)
    with torch.no_grad():
        normalizer.running_mean.fill_(10.0)
        normalizer.running_mean_sq.fill_(104.0)
        normalizer.debiasing_term.fill_(1.0)
    return normalizer


def _state(normalizer: ValueNorm) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in normalizer.state_dict().items()}


def test_i5b_01_mixed_reason_hand_computed_vector_gae() -> dict[str, object]:
    buffer = _buffer(4, 3)
    rewards = torch.tensor(
        [[[1.0], [2.0], [3.0], [4.0]], [[5.0], [6.0], [7.0], [8.0]], [[9.0], [10.0], [11.0], [12.0]]]
    )
    current = torch.tensor(
        [[[1.0]] * 4, [[2.0]] * 4, [[3.0]] * 4], dtype=torch.float32
    )
    reasons = torch.tensor(
        [
            [[int(Reason.NONE)], [int(Reason.TIME_LIMIT)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NO_FEASIBLE_TASKS_REMAIN)]],
            [[int(Reason.NONE)]] * 4,
            [[int(Reason.TIME_LIMIT)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NO_FEASIBLE_TASKS_REMAIN)], [int(Reason.NONE)]],
        ],
        dtype=torch.int64,
    )
    timeout = torch.zeros((3, 4, 1), dtype=torch.float32)
    timeout[0, 1, 0] = 10.0
    timeout[2, 0, 0] = 20.0
    masks = (reasons == int(Reason.NONE)).to(torch.float32)
    _fill(buffer, rewards=rewards, current_values=current, reasons=reasons, timeout_values=timeout, masks_after=masks)
    result = buffer.compute_event_returns(torch.full((4, 1), 4.0))
    expected_delta = torch.tensor(
        [[[1.8], [10.0], [2.0], [3.0]], [[5.7], [6.7], [7.7], [8.7]], [[24.0], [7.0], [8.0], [12.6]]]
    )
    expected_advantage = torch.tensor(
        [[[18.3456], [10.0], [2.0], [3.0]], [[22.98], [11.74], [13.46], [17.772]], [[24.0], [7.0], [8.0], [12.6]]]
    )
    expected_returns = expected_advantage + current
    _close(result.deltas, expected_delta, "mixed deltas")
    _close(result.advantages, expected_advantage, "mixed GAE")
    _close(result.returns, expected_returns, "mixed returns")
    _assert(torch.equal(result.trace_continue_masks, masks), "reason-specific trace masks")
    return {"T": 3, "E": 4, "reason_kinds": 4, "hand_computed": True}


def test_i5b_02_autoreset_trap_and_trace_stop() -> dict[str, object]:
    buffer = _buffer(3, 2)
    rewards = torch.tensor([[[1.0], [2.0], [3.0]], [[1000.0], [2000.0], [3000.0]]])
    current = torch.tensor([[[1.0], [1.0], [1.0]], [[999.0], [999.0], [999.0]]])
    reasons = torch.tensor(
        [
            [[int(Reason.TIME_LIMIT)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NONE)]],
            [[int(Reason.ALL_TASKS_COMPLETED)]] * 3,
        ],
        dtype=torch.int64,
    )
    timeout = torch.zeros((2, 3, 1))
    timeout[0, 0, 0] = 10.0
    masks = (reasons == int(Reason.NONE)).to(torch.float32)
    _fill(buffer, rewards=rewards, current_values=current, reasons=reasons, timeout_values=timeout, masks_after=masks)
    result = buffer.compute_event_returns(torch.full((3, 1), 777.0))
    _close(result.bootstrap_values[0, :, 0], torch.tensor([10.0, 0.0, 999.0]), "bootstrap source trap")
    _close(result.returns[0, :2, 0], torch.tensor([10.0, 2.0]), "terminal return ignores post-reset")
    expected_none = 3.0 + 0.9 * 999.0 + 0.9 * 0.8 * (3000.0 - 999.0)
    _close(result.returns[0, 2, 0], torch.tensor(expected_none), "NONE continues trace")
    return {"timeout_uses": 10, "post_reset_trap": 999, "trace_stop": True}


def test_i5b_03_reason_mask_mismatch_fail_closed() -> dict[str, object]:
    rewards = torch.ones((1, 1, 1))
    values = torch.zeros((2, 1, 1))
    masks = torch.ones((2, 1, 1))
    timeout_values = torch.zeros((1, 1, 1))

    def call(reason: int, timeout_mask: bool) -> object:
        local_masks = masks.clone()
        if reason != int(Reason.NONE):
            local_masks[1] = 0.0
        return GAE.compute_event_gae_returns_v2(
            rewards=rewards,
            value_preds=values,
            next_value=torch.zeros((1, 1)),
            masks=local_masks,
            termination_reason=torch.tensor([[[reason]]], dtype=torch.int64),
            timeout_bootstrap_masks=torch.tensor([[[timeout_mask]]]),
            timeout_bootstrap_value_preds=timeout_values,
            gamma=0.9,
            gae_lambda=0.8,
        )

    _expect(lambda: call(int(Reason.TIME_LIMIT), False), code="termination_timeout_mask_mismatch")
    _expect(lambda: call(int(Reason.NONE), True), code="termination_timeout_mask_mismatch")
    _expect(lambda: call(int(Reason.ALL_TASKS_COMPLETED), True), code="termination_timeout_mask_mismatch")
    _expect(lambda: call(99, False), code="termination_reason_value")
    return {"mismatches_rejected": 4}


def test_i5b_04_timeout_nonfinite_fail_closed() -> dict[str, object]:
    buffer = _buffer(1, 1)
    reason = torch.tensor([[[int(Reason.TIME_LIMIT)]]], dtype=torch.int64)
    for invalid in (float("nan"), float("inf")):
        _fill(
            buffer,
            rewards=torch.ones((1, 1, 1)),
            current_values=torch.zeros((1, 1, 1)),
            reasons=reason,
            timeout_values=torch.tensor([[[invalid]]]),
            masks_after=torch.zeros((1, 1, 1)),
        )
        _expect(
            lambda: GAE.compute_event_gae_returns_v2(
                rewards=buffer.rewards,
                value_preds=buffer.value_preds,
                next_value=torch.zeros((1, 1)),
                masks=buffer.masks,
                termination_reason=buffer.termination_reason,
                timeout_bootstrap_masks=buffer.timeout_bootstrap_masks,
                timeout_bootstrap_value_preds=buffer.timeout_bootstrap_value_preds,
                gamma=0.9,
                gae_lambda=0.8,
            ),
            code="timeout_value_nonfinite",
        )
    _expect(
        lambda: GAE.compute_event_gae_returns_v2(
            rewards=torch.ones((1, 1, 1)),
            value_preds=torch.zeros((2, 1, 1)),
            next_value=torch.zeros((1, 1)),
            masks=torch.tensor([[[1.0]], [[0.0]]]),
            termination_reason=reason,
            timeout_bootstrap_masks=torch.ones((1, 1, 1), dtype=torch.bool),
            timeout_bootstrap_value_preds=torch.ones((1, 2, 1)),
            gamma=0.9,
            gae_lambda=0.8,
        ),
        code="timeout_bootstrap_value_preds_contract",
    )
    return {"nan_rejected": True, "inf_rejected": True, "wrong_shape_rejected": True}


def test_i5b_05_invalid_timeout_slots_are_unread() -> dict[str, object]:
    rewards = torch.tensor([[[1.0], [2.0], [3.0]]])
    current = torch.tensor([[[4.0], [5.0], [6.0]], [[7.0], [8.0], [9.0]]])
    reasons = torch.tensor(
        [[[int(Reason.NONE)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NO_FEASIBLE_TASKS_REMAIN)]]],
        dtype=torch.int64,
    )
    timeout_masks = torch.zeros((1, 3, 1), dtype=torch.bool)
    masks = torch.ones((2, 3, 1))
    masks[1, 1:] = 0.0
    baseline = GAE.compute_event_gae_returns_v2(
        rewards=rewards,
        value_preds=current,
        next_value=torch.tensor([[7.0], [999.0], [999.0]]),
        masks=masks,
        termination_reason=reasons,
        timeout_bootstrap_masks=timeout_masks,
        timeout_bootstrap_value_preds=torch.zeros((1, 3, 1)),
        gamma=0.9,
        gae_lambda=0.8,
    )
    traps = torch.tensor([[[123456.0], [float("nan")], [-1.0e30]]])
    trapped = GAE.compute_event_gae_returns_v2(
        rewards=rewards,
        value_preds=current,
        next_value=torch.tensor([[7.0], [999.0], [999.0]]),
        masks=masks,
        termination_reason=reasons,
        timeout_bootstrap_masks=timeout_masks,
        timeout_bootstrap_value_preds=traps,
        gamma=0.9,
        gae_lambda=0.8,
    )
    _assert(torch.equal(baseline.returns, trapped.returns), "false-mask timeout sentinels were read")
    return {"nan_false_mask_ignored": True, "huge_false_mask_ignored": True}


def test_i5b_06_valuenorm_on_same_scale_numerical_oracle() -> dict[str, object]:
    buffer = _buffer(4, 1)
    rewards = torch.tensor([[[1.0], [2.0], [3.0], [4.0]]])
    current = torch.ones((1, 4, 1))
    reasons = torch.tensor(
        [[[int(Reason.NONE)], [int(Reason.TIME_LIMIT)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NO_FEASIBLE_TASKS_REMAIN)]]],
        dtype=torch.int64,
    )
    timeout = torch.zeros((1, 4, 1))
    timeout[0, 1, 0] = 3.0
    masks = (reasons == int(Reason.NONE)).to(torch.float32)
    _fill(buffer, rewards=rewards, current_values=current, reasons=reasons, timeout_values=timeout, masks_after=masks)
    normalizer = _normalizer()
    before = _state(normalizer)
    result = buffer.compute_event_returns(torch.full((4, 1), 2.0), normalizer)
    _close(result.arithmetic_value_preds[0, :, 0], torch.full((4,), 12.0), "V_t denorm")
    _close(result.bootstrap_values[0, :, 0], torch.tensor([14.0, 16.0, 0.0, 0.0]), "all bootstrap scales")
    _close(result.returns[0, :, 0], torch.tensor([13.6, 16.4, 3.0, 4.0]), "ValueNorm returns")
    _assert(all(torch.equal(before[k], v) for k, v in normalizer.state_dict().items()), "normalizer stats updated")
    return {"denormalize": "2*x+10", "normalizer_updates": 0}


def test_i5b_07_valuenorm_off_native_scale_oracle() -> dict[str, object]:
    buffer = _buffer(4, 1)
    reasons = torch.tensor(
        [[[int(Reason.NONE)], [int(Reason.TIME_LIMIT)], [int(Reason.ALL_TASKS_COMPLETED)], [int(Reason.NO_FEASIBLE_TASKS_REMAIN)]]],
        dtype=torch.int64,
    )
    timeout = torch.zeros((1, 4, 1))
    timeout[0, 1, 0] = 3.0
    _fill(
        buffer,
        rewards=torch.tensor([[[1.0], [2.0], [3.0], [4.0]]]),
        current_values=torch.ones((1, 4, 1)),
        reasons=reasons,
        timeout_values=timeout,
        masks_after=(reasons == int(Reason.NONE)).to(torch.float32),
    )
    result = buffer.compute_event_returns(torch.full((4, 1), 2.0))
    _close(result.returns[0, :, 0], torch.tensor([2.8, 4.7, 3.0, 4.0]), "native returns")
    return {"ValueNorm": "OFF", "native_arithmetic": True}


class MutatingValueNorm(ValueNorm):
    def denormalize(self, input_vector):
        output = super().denormalize(input_vector)
        with torch.no_grad():
            self.running_mean.add_(1.0)
        return output


def test_i5b_08_normalizer_snapshot_mutation_fails_before_commit() -> dict[str, object]:
    buffer = _buffer(1, 1)
    reasons = torch.tensor([[[int(Reason.NONE)]]], dtype=torch.int64)
    _fill(
        buffer,
        rewards=torch.ones((1, 1, 1)),
        current_values=torch.ones((1, 1, 1)),
        reasons=reasons,
        timeout_values=torch.zeros((1, 1, 1)),
        masks_after=torch.ones((1, 1, 1)),
    )
    returns_before = buffer.returns.clone()
    _expect(
        lambda: buffer.compute_event_returns(torch.ones((1, 1)), _normalizer(cls=MutatingValueNorm)),
        code="value_normalizer_mutated",
    )
    _assert(torch.equal(buffer.returns, returns_before), "failed computation partially committed returns")
    _assert(not buffer._event_returns_computed, "failed computation consumed once guard")
    return {"mutation_rejected": True, "partial_commit": False}


def _stock_and_event(*, normalizer: ValueNorm | None) -> tuple[torch.Tensor, torch.Tensor]:
    T, E = 3, 2
    args = {
        "episode_length": T,
        "n_rollout_threads": E,
        "hidden_sizes": [4],
        "recurrent_n": 1,
        "gamma": 0.9,
        "gae_lambda": 0.8,
        "use_gae": True,
        "use_proper_time_limits": True,
    }
    stock = OnPolicyCriticBufferEP(args, Box((5,)), device=DEVICE)
    event = CB.EventOnPolicyCriticBufferEPV2(args, Box((5,)), device=DEVICE)
    rewards = torch.tensor([[[1.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]]])
    values = torch.tensor([[[0.1], [0.2]], [[0.3], [0.4]], [[0.5], [0.6]]])
    next_value = torch.tensor([[0.7], [0.8]])
    for target in (stock, event):
        target.rewards.copy_(rewards)
        target.value_preds[:-1].copy_(values)
        target.masks.fill_(1.0)
        target.bad_masks.fill_(1.0)
    event.termination_reason.fill_(int(Reason.NONE))
    event.timeout_bootstrap_masks.zero_()
    event.timeout_bootstrap_value_preds.fill_(float("nan"))
    event._event_slot_written.fill_(True)
    if normalizer is None:
        stock_normalizer = None
        event_normalizer = None
    else:
        stock_normalizer = _normalizer()
        event_normalizer = _normalizer()
    stock.compute_returns(next_value, stock_normalizer)
    event.compute_event_returns(next_value, event_normalizer)
    return stock.returns[:-1].clone(), event.returns[:-1].clone()


def test_i5b_09_stock_consistency_all_none_off_and_on() -> dict[str, object]:
    stock_off, event_off = _stock_and_event(normalizer=None)
    stock_on, event_on = _stock_and_event(normalizer=_normalizer())
    _close(event_off, stock_off, "all-NONE stock parity ValueNorm OFF")
    _close(event_on, stock_on, "all-NONE stock parity ValueNorm ON")
    return {"stock_parity_off": True, "stock_parity_on": True}


def test_i5b_10_timeout_deliberately_differs_from_bad_mask_suppression() -> dict[str, object]:
    args = {
        "episode_length": 1,
        "n_rollout_threads": 1,
        "hidden_sizes": [4],
        "recurrent_n": 1,
        "gamma": 0.9,
        "gae_lambda": 0.8,
        "use_gae": True,
        "use_proper_time_limits": True,
    }
    stock = OnPolicyCriticBufferEP(args, Box((5,)), device=DEVICE)
    stock.rewards[0] = 2.0
    stock.value_preds[0] = 1.0
    stock.masks[1] = 0.0
    stock.bad_masks[1] = 0.0
    stock.compute_returns(torch.tensor([[999.0]]))
    event = _buffer(1, 1)
    reasons = torch.tensor([[[int(Reason.TIME_LIMIT)]]], dtype=torch.int64)
    _fill(
        event,
        rewards=torch.tensor([[[2.0]]]),
        current_values=torch.tensor([[[1.0]]]),
        reasons=reasons,
        timeout_values=torch.tensor([[[10.0]]]),
        masks_after=torch.zeros((1, 1, 1)),
    )
    event.compute_event_returns(torch.tensor([[999.0]]))
    _close(stock.returns[0], torch.tensor([[1.0]]), "stock bad-mask suppression")
    _close(event.returns[0], torch.tensor([[11.0]]), "event timeout target")
    return {"stock_target": 1.0, "event_target": 11.0, "deliberate_specialization": True}


def test_i5b_11_buffer_once_full_rollout_and_no_alias() -> dict[str, object]:
    buffer = _buffer(1, 2)
    reasons = torch.full((2, 1, 1), int(Reason.NONE), dtype=torch.int64)
    _fill(
        buffer,
        rewards=torch.ones((2, 1, 1)),
        current_values=torch.zeros((2, 1, 1)),
        reasons=reasons,
        timeout_values=torch.zeros((2, 1, 1)),
        masks_after=torch.ones((2, 1, 1)),
    )
    buffer._event_slot_written[1] = False
    _expect(lambda: buffer.compute_event_returns(torch.zeros((1, 1))), code="event_rollout_incomplete")
    buffer._event_slot_written[1] = True
    result = buffer.compute_event_returns(torch.zeros((1, 1)))
    stored = buffer.returns.clone()
    result.returns.fill_(999.0)
    _assert(torch.equal(buffer.returns, stored), "result aliases critic buffer")
    _expect(lambda: buffer.compute_event_returns(torch.zeros((1, 1))), code="event_returns_duplicate")
    buffer.after_update()
    _assert(not buffer._event_returns_computed, "after_update did not reset once guard")
    return {"incomplete_rejected": True, "once": True, "no_alias": True}


def test_i5b_12_terminal_liveness_and_binary_masks_fail_closed() -> dict[str, object]:
    reason = torch.tensor([[[int(Reason.TIME_LIMIT)]]], dtype=torch.int64)
    common = dict(
        rewards=torch.ones((1, 1, 1)),
        value_preds=torch.zeros((2, 1, 1)),
        next_value=torch.zeros((1, 1)),
        termination_reason=reason,
        timeout_bootstrap_masks=torch.ones((1, 1, 1), dtype=torch.bool),
        timeout_bootstrap_value_preds=torch.ones((1, 1, 1)),
        gamma=0.9,
        gae_lambda=0.8,
    )
    _expect(
        lambda: GAE.compute_event_gae_returns_v2(masks=torch.ones((2, 1, 1)), **common),
        code="terminal_liveness_mask",
    )
    nonbinary = torch.ones((2, 1, 1))
    nonbinary[1] = 0.5
    _expect(
        lambda: GAE.compute_event_gae_returns_v2(masks=nonbinary, **common),
        code="masks_binary",
    )
    return {"terminal_mask_mismatch": "rejected", "nonbinary": "rejected"}


def test_i5b_13_no_dvm_critic_forward_optimizer_or_runtime_capability() -> dict[str, object]:
    source = (SCAN_SOURCE / "assignment_event_gae_returns.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    forbidden_import_fragments = ("actor", "policy", "terminal_learner", "runtime", "wrapper")
    _assert(not any(any(fragment in name for fragment in forbidden_import_fragments) for name in imported), "forbidden I5b import")
    _assert("get_values" not in calls, "critic forward in I5b")
    _assert("step" not in calls and "train" not in calls and "update" not in calls, "optimizer/training in I5b")
    _assert("decision_valid_masks" not in source and "active_masks" not in source, "DVM/actor liveness in critic GAE")
    # These external actor row labels are deliberately false for both rows.
    # They are not inputs to I5b; both physical NONE transitions must remain in
    # critic arithmetic with their original rewards.
    external_dvm = torch.zeros((1, 2, 1), dtype=torch.bool)
    result = GAE.compute_event_gae_returns_v2(
        rewards=torch.tensor([[[5.0], [7.0]]]),
        value_preds=torch.zeros((2, 2, 1)),
        next_value=torch.zeros((2, 1)),
        masks=torch.ones((2, 2, 1)),
        termination_reason=torch.full((1, 2, 1), int(Reason.NONE), dtype=torch.int64),
        timeout_bootstrap_masks=torch.zeros((1, 2, 1), dtype=torch.bool),
        timeout_bootstrap_value_preds=torch.full((1, 2, 1), float("nan")),
        gamma=0.9,
        gae_lambda=0.8,
    )
    _assert(not bool(external_dvm.any().item()), "forced-row setup")
    _close(result.returns[0, :, 0], torch.tensor([5.0, 7.0]), "forced physical critic transitions")
    return {"critic_forward_calls": 0, "optimizer_calls": 0, "DVM_inputs": 0, "forced_critic_transitions": 2, "runtime_inputs": 0}


def test_i5b_14_protected_source_and_installed_hashes() -> dict[str, object]:
    protected = {
        SCAN_SOURCE / "assignment_event_profile_schema_contract_v2.py": "9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955",
        SCAN_SOURCE / "assignment_event_policy_evidence.py": "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
        SCAN_SOURCE / "assignment_event_policy_decision.py": "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
        SCAN_SOURCE / "assignment_event_actor_collection.py": "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
        SCAN_SOURCE / "assignment_event_happo_policy_math.py": "3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4",
        SCAN_SOURCE / "assignment_event_terminal_learner_transport.py": "e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4",
        SCAN_SOURCE / "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
        SCAN_SOURCE / "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
        Path("C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/common/buffers/on_policy_critic_buffer_ep.py"): "0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f",
        Path("C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/common/valuenorm.py"): "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
        Path("C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/algorithms/critics/v_critic.py"): "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    }
    for path, expected in protected.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        _assert(actual == expected, f"protected hash drift: {path}: {actual}")
    buffer_tree = ast.parse((SCAN_SOURCE / "assignment_event_critic_buffer.py").read_text(encoding="utf-8"))
    _assert(
        not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "compute_returns" for node in ast.walk(buffer_tree)),
        "I5b replaced the installed compute_returns method",
    )
    return {"protected_hashes": len(protected), "installed_changes": 0, "stock_override": False}


TESTS: tuple[tuple[str, Callable[[], dict[str, object]]], ...] = (
    ("B2-I5B-T01", test_i5b_01_mixed_reason_hand_computed_vector_gae),
    ("B2-I5B-T02", test_i5b_02_autoreset_trap_and_trace_stop),
    ("B2-I5B-T03", test_i5b_03_reason_mask_mismatch_fail_closed),
    ("B2-I5B-T04", test_i5b_04_timeout_nonfinite_fail_closed),
    ("B2-I5B-T05", test_i5b_05_invalid_timeout_slots_are_unread),
    ("B2-I5B-T06", test_i5b_06_valuenorm_on_same_scale_numerical_oracle),
    ("B2-I5B-T07", test_i5b_07_valuenorm_off_native_scale_oracle),
    ("B2-I5B-T08", test_i5b_08_normalizer_snapshot_mutation_fails_before_commit),
    ("B2-I5B-T09", test_i5b_09_stock_consistency_all_none_off_and_on),
    ("B2-I5B-T10", test_i5b_10_timeout_deliberately_differs_from_bad_mask_suppression),
    ("B2-I5B-T11", test_i5b_11_buffer_once_full_rollout_and_no_alias),
    ("B2-I5B-T12", test_i5b_12_terminal_liveness_and_binary_masks_fail_closed),
    ("B2-I5B-T13", test_i5b_13_no_dvm_critic_forward_optimizer_or_runtime_capability),
    ("B2-I5B-T14", test_i5b_14_protected_source_and_installed_hashes),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = []
    for name, test in TESTS:
        try:
            details = test()
            rows.append({"name": name, "status": "PASS", "details": details})
        except BaseException as exc:
            rows.append({"name": name, "status": "FAIL", "error": repr(exc)})
            if args.json:
                print(json.dumps({"tests": rows}, indent=2))
            else:
                print(f"{name}: FAIL: {exc!r}")
            return 1
    if args.json:
        print(json.dumps({"tests": rows}, indent=2))
    else:
        for row in rows:
            print(f"{row['name']}: PASS")
        print(f"B2-I5b pure verification: {len(rows)}/{len(TESTS)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
