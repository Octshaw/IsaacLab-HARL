"""Project-local tests for strict HARL ValueNorm checkpoint state adaptation."""

from __future__ import annotations

import copy
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
import sys

import pytest
import torch
import torch.nn as nn


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

import assignment_value_normalizer_checkpoint as adapter  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


@contextmanager
def _default_dtype(dtype: torch.dtype):
    original = torch.get_default_dtype()
    torch.set_default_dtype(dtype)
    try:
        yield
    finally:
        torch.set_default_dtype(original)


def _value_norm(*, forced_conversion: bool = False, device: torch.device | None = None) -> ValueNorm:
    device = torch.device("cpu") if device is None else device
    if not forced_conversion:
        return ValueNorm(1, device=device)
    with _default_dtype(torch.float64):
        return ValueNorm(1, device=device)


def _update(value_norm: ValueNorm) -> None:
    value_norm.update(torch.tensor([[1.0], [-2.0], [3.5]], dtype=torch.float32))


def _snapshot(value_norm: ValueNorm):
    return {
        name: getattr(value_norm, name).detach().clone()
        for name in adapter.VALUE_NORMALIZER_STATE_KEYS
    }, {name: id(getattr(value_norm, name)) for name in adapter.VALUE_NORMALIZER_STATE_KEYS}


def _assert_snapshot(value_norm: ValueNorm, values, identities) -> None:
    for name in adapter.VALUE_NORMALIZER_STATE_KEYS:
        assert torch.equal(getattr(value_norm, name), values[name]), name
        assert id(getattr(value_norm, name)) == identities[name], name


def test_cpu_noop_and_forced_conversion_registration_diagnostic() -> None:
    registered = _value_norm()
    converted = _value_norm(forced_conversion=True)
    assert tuple(registered.state_dict()) == adapter.VALUE_NORMALIZER_STATE_KEYS
    assert not tuple(converted.state_dict())
    assert all(isinstance(getattr(registered, name), nn.Parameter) for name in adapter.VALUE_NORMALIZER_STATE_KEYS)
    assert all(not isinstance(getattr(converted, name), nn.Parameter) for name in adapter.VALUE_NORMALIZER_STATE_KEYS)
    for value_norm in (registered, converted):
        _update(value_norm)
        exported = adapter.export_value_normalizer_checkpoint_state(value_norm)
        assert tuple(exported) == adapter.VALUE_NORMALIZER_STATE_KEYS
        assert all(value.device.type == "cpu" and value.dtype == torch.float32 for value in exported.values())


def test_export_is_detached_cpu_clone_and_runtime_update_changes_state() -> None:
    value_norm = _value_norm(forced_conversion=True)
    before = adapter.export_value_normalizer_checkpoint_state(value_norm)
    _update(value_norm)
    after = adapter.export_value_normalizer_checkpoint_state(value_norm)
    assert any(not torch.equal(before[name], after[name]) for name in adapter.VALUE_NORMALIZER_STATE_KEYS)
    for name, value in after.items():
        live = getattr(value_norm, name)
        assert value.data_ptr() != live.detach().cpu().data_ptr() or live.device.type != "cpu"
        assert value.dtype == live.dtype


def test_forced_conversion_round_trip_preserves_objects_and_outputs() -> None:
    source = _value_norm(forced_conversion=True)
    target = _value_norm(forced_conversion=True)
    _update(source)
    state = adapter.export_value_normalizer_checkpoint_state(source)
    before_values, before_ids = _snapshot(target)
    adapter.restore_value_normalizer_checkpoint_state(target, state)
    for name in adapter.VALUE_NORMALIZER_STATE_KEYS:
        assert torch.equal(getattr(target, name).cpu(), state[name]), name
        assert id(getattr(target, name)) == before_ids[name], name
        assert not torch.equal(before_values[name], getattr(target, name)), name
    sample = torch.tensor([[0.5], [1.25]], dtype=torch.float32)
    assert torch.equal(source.normalize(sample).cpu(), target.normalize(sample).cpu())
    assert torch.equal(source.denormalize(sample).cpu(), target.denormalize(sample).cpu())


def test_registered_parameter_round_trip_preserves_objects_and_outputs() -> None:
    source = _value_norm()
    target = _value_norm()
    _update(source)
    state = adapter.export_value_normalizer_checkpoint_state(source)
    _, identities = _snapshot(target)
    adapter.restore_value_normalizer_checkpoint_state(target, state)
    assert all(isinstance(getattr(target, name), nn.Parameter) for name in adapter.VALUE_NORMALIZER_STATE_KEYS)
    for name in adapter.VALUE_NORMALIZER_STATE_KEYS:
        assert id(getattr(target, name)) == identities[name], name
        assert torch.equal(getattr(target, name).cpu(), state[name]), name
    sample = torch.tensor([[0.5], [1.25]], dtype=torch.float32)
    assert torch.equal(source.normalize(sample), target.normalize(sample))
    assert torch.equal(source.denormalize(sample), target.denormalize(sample))


def test_inspection_rejections_and_contract_target_validation() -> None:
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="must not be None"):
        adapter.inspect_value_normalizer_target(None)
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="unsupported ValueNorm implementation"):
        adapter.inspect_value_normalizer_target(object())

    missing = _value_norm()
    delattr(missing, "running_mean")
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="missing required field"):
        adapter.inspect_value_normalizer_target(missing)

    non_tensor = _value_norm()
    delattr(non_tensor, "running_mean")
    non_tensor.running_mean = "invalid"
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="must be Tensor"):
        adapter.inspect_value_normalizer_target(non_tensor)

    nonfinite = _value_norm()
    with torch.no_grad():
        nonfinite.running_mean.fill_(float("inf"))
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="nonfinite"):
        adapter.inspect_value_normalizer_target(nonfinite)

    source = _value_norm()
    contract = adapter.build_value_normalizer_contract(source, enabled=True)
    adapter.validate_value_normalizer_target_contract(
        adapter.inspect_value_normalizer_target(source), contract
    )
    for field, value in (("beta", 0.5), ("epsilon", 0.5), ("tensor_dtype", "float64")):
        invalid = copy.deepcopy(contract)
        invalid[field] = value
        with pytest.raises(adapter.ValueNormalizerCheckpointError, match=field):
            adapter.validate_value_normalizer_target_contract(
                adapter.inspect_value_normalizer_target(source), invalid
            )
    assert adapter.build_value_normalizer_contract(None, enabled=False) == {"enabled": False}
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="exists while contract is disabled"):
        adapter.build_value_normalizer_contract(source, enabled=False)


def test_restore_rejections_do_not_mutate_target() -> None:
    source = _value_norm(forced_conversion=True)
    target = _value_norm(forced_conversion=True)
    _update(source)
    state = adapter.export_value_normalizer_checkpoint_state(source)
    cases = (
        OrderedDict(),
        OrderedDict((name, state[name]) for name in adapter.VALUE_NORMALIZER_STATE_KEYS[:-1]),
        OrderedDict(
            (
                ("running_mean_sq", state["running_mean_sq"]),
                ("running_mean", state["running_mean"]),
                ("debiasing_term", state["debiasing_term"]),
            )
        ),
        OrderedDict((*state.items(), ("extra", torch.tensor(1.0)))),
        OrderedDict(
            (name, torch.ones(2, dtype=value.dtype) if name == "running_mean" else value)
            for name, value in state.items()
        ),
        OrderedDict((name, value.to(torch.float64)) for name, value in state.items()),
        OrderedDict((name, "non-tensor") for name in adapter.VALUE_NORMALIZER_STATE_KEYS),
        OrderedDict((name, torch.full_like(value, float("nan"))) for name, value in state.items()),
        OrderedDict((name, torch.full_like(value, float("inf"))) for name, value in state.items()),
    )
    for invalid in cases:
        values, identities = _snapshot(target)
        with pytest.raises(adapter.ValueNormalizerCheckpointError):
            adapter.restore_value_normalizer_checkpoint_state(target, invalid)
        _assert_snapshot(target, values, identities)
    values, identities = _snapshot(target)
    with pytest.raises(adapter.ValueNormalizerCheckpointError):
        adapter.restore_value_normalizer_checkpoint_state(target, state, strict=False)
    _assert_snapshot(target, values, identities)


def test_restore_rolls_back_an_injected_copy_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    source = _value_norm(forced_conversion=True)
    target = _value_norm(forced_conversion=True)
    _update(source)
    state = adapter.export_value_normalizer_checkpoint_state(source)
    values, identities = _snapshot(target)
    original = adapter._copy_target_field
    calls = 0

    def fail_second_copy(destination: torch.Tensor, value: torch.Tensor) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected copy failure")
        original(destination, value)

    monkeypatch.setattr(adapter, "_copy_target_field", fail_second_copy)
    with pytest.raises(adapter.ValueNormalizerCheckpointError, match="injected copy failure"):
        adapter.restore_value_normalizer_checkpoint_state(target, state)
    _assert_snapshot(target, values, identities)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA unavailable")
def test_cuda_runtime_style_export_and_round_trip() -> None:
    device = torch.device("cuda:0")
    source = _value_norm(device=device)
    target = _value_norm(device=device)
    assert not tuple(source.state_dict())
    _update(source)
    state = adapter.export_value_normalizer_checkpoint_state(source)
    assert tuple(state) == adapter.VALUE_NORMALIZER_STATE_KEYS
    assert all(value.device.type == "cpu" for value in state.values())
    identities = {name: id(getattr(target, name)) for name in adapter.VALUE_NORMALIZER_STATE_KEYS}
    adapter.restore_value_normalizer_checkpoint_state(target, state)
    for name in adapter.VALUE_NORMALIZER_STATE_KEYS:
        assert torch.equal(getattr(target, name).cpu(), state[name]), name
        assert id(getattr(target, name)) == identities[name], name
