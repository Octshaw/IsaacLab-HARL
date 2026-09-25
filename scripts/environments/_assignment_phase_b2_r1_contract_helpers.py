"""Shared pure helpers for the B2-R1 contract-only verification slice."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any, Callable

import torch
from harl.common.valuenorm import ValueNorm


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
BASE = "isaaclab_tasks.direct.scan_mobile_manipulator"


def _namespace(name: str, path: Path) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


_namespace("isaaclab_tasks", SCAN_SOURCE.parents[2])
_namespace("isaaclab_tasks.direct", SCAN_SOURCE.parent)
_namespace(BASE, SCAN_SOURCE)


def load_canonical(filename: str) -> Any:
    stem = Path(filename).stem
    name = f"{BASE}.{stem}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCAN_SOURCE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


E = load_canonical("assignment_event_training_evidence.py")
P = load_canonical("assignment_event_training_plans.py")
C = load_canonical("assignment_event_training_control.py")
G = load_canonical("assignment_event_training_static_guards.py")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_stop(stop_code: str, function: Callable[[], object]) -> None:
    try:
        function()
    except E.B2RContractError as exc:
        assert_true(exc.stop_code == stop_code, f"wrong STOP: {exc.stop_code}; expected {stop_code}")
    else:
        raise AssertionError(f"expected {stop_code}")


def digest(label: str) -> str:
    return E.canonical_digest_v1(("fixture", label))


def config(**changes: object) -> Any:
    values: dict[str, object] = {
        "resolved_T": 3,
        "resolved_E": 4,
        "resolved_M": 3,
        "resolved_N": 5,
        "actor_epoch_count": 2,
        "actor_minibatch_count": 3,
        "actor_partition_policy": "reviewed_exact_coverage",
        "critic_epoch_count": 2,
        "critic_minibatch_count": 5,
        "critic_partition_policy": "reviewed_exact_coverage",
        "fixed_order": False,
        "valuenorm_enabled": True,
        "ppo_happo_settings": (("clip_param", 0.2), ("entropy_coef", 0.01)),
    }
    values.update(changes)
    return E.B2RResolvedConfigV1(**values)


def authority(*, cfg: object | None = None, update_id: str = "update-r1-0001") -> Any:
    resolved = config() if cfg is None else cfg
    return E.B2RUpdateAuthorityV1(
        update_id=update_id,
        slice_identity="B2-R1",
        repository_head="b71d85a32f51be6ada324f870813a56bb45dd396",
        dirty_state_classification="authorized R1 additions plus pre-existing AgentRead handoff edits",
        repo_source_hashes=(E.B2RSourceDigestV1("repo/event.py", digest("repo")),),
        installed_harl_source_hashes=(E.B2RSourceDigestV1("harl/happo.py", digest("harl")),),
        resolved_config=resolved,
        authorization_scope=("pure_static_contracts", "synthetic_tests"),
        forbidden_operations=("backward", "optimizer_step", "live_valuenorm_update", "isaac"),
    )


def run(tests: list[tuple[str, Callable[[], dict[str, object]]]]) -> None:
    results: dict[str, object] = {}
    for name, function in tests:
        results[name] = function()
    print(json.dumps({"status": "PASS", "tests": results}, sort_keys=True))


class Tiny(torch.nn.Module):
    def __init__(self, width: int = 2) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(width, 1)
        self.register_buffer("scale", torch.ones(1))


def TinyValueNorm() -> ValueNorm:
    return ValueNorm(1, device=torch.device("cpu"))
