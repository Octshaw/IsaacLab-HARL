"""Pure regressions for the Phase A2 lifecycle transition contract.

This standalone suite loads exactly one source file under its sole canonical
module key.  It does not import the normal ``isaaclab_tasks`` package because
that package performs task discovery.  It never starts AppLauncher or Isaac,
constructs an assignment wrapper/resolver, touches a checkpoint, or runs
training, playback, diagnosis, or evaluation.

The suite intentionally imports torch because the A2 schema is tensor-valued.
All fixtures are deterministic tensor literals/aranges; no random samples are
used.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Mapping

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
CONTRACT_PATH = (
    SCAN_TASK_SOURCE / "assignment_lifecycle_transition_contract.py"
)
EVENT_CONTRACT_PATH = SCAN_TASK_SOURCE / "assignment_event_contract.py"
PROFILE_CONTRACT_PATH = SCAN_TASK_SOURCE / "assignment_profile_contract.py"

CANONICAL_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
BARE_MODULE = "assignment_lifecycle_transition_contract"
CANONICAL_EVENT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract"
)

FACTS_VERSION = "execution_transition_facts_v1"
RESULT_VERSION = "lifecycle_transition_result_v1"
RECEIPT_VERSION = "transition_consume_receipt_v1"
PRODUCER_VERSION = "execution_facts_producer_contract_v1"
AUTHORITY_VERSION = "unique_lifecycle_authority_v1"
PAIR_VERSION = "pair_attributed_execution_signals_v1"
IMMUTABILITY_VERSION = "assignment_tensor_alias_isolation_v1"
CONTRACT_VERSION = "assignment_lifecycle_transition_contract_v2"
FAILURE_TERMINATION_VERSION = (
    "event_gated_failure_termination_semantics_v1"
)
TASK_STATE_ORDER = (
    ("AVAILABLE", 0),
    ("CLAIMED", 1),
    ("NAVIGATING", 2),
    ("ALIGNING", 3),
    ("COMPLETED", 4),
    ("TEAM_INFEASIBLE", 5),
)
ROBOT_STATE_ORDER = (
    ("EXECUTING", 0),
    ("NEEDS_ASSIGNMENT", 1),
    ("WAITING_FOR_TASK", 2),
    ("UNAVAILABLE", 3),
)
TERMINATION_REASON_ORDER = (
    ("NONE", 0),
    ("ALL_TASKS_COMPLETED", 1),
    ("NO_FEASIBLE_TASKS_REMAIN", 2),
    ("TIME_LIMIT", 3),
)
FAILURE_TERMINATION_KEYS = (
    "projection_version",
    "task_state_enum_order",
    "robot_state_enum_order",
    "transient_event_exclusion",
    "termination_reason_order",
    "failed_pair_source",
    "new_failed_pairs_equation",
    "updated_failed_pairs_equation",
    "failed_pair_episode_reset_rule",
    "team_infeasible_equation",
    "new_team_infeasible_equation",
    "path_invalid_non_equivalence",
    "terminal_task_ownership_release_rule",
    "event_updated_baseline_order",
    "termination_priority",
    "physical_terminal_mapping_boundary",
    "bad_transition_boundary",
    "unmappable_physical_terminal_rule",
    "terminal_assignment_rule",
    "episode_generation_rule",
    "transition_generation_rule",
    "assignment_tick_generation_rule",
)

FACTS_TENSOR_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("physical_terminated", ("E",), torch.bool),
    ("physical_truncated", ("E",), torch.bool),
    ("time_limit_reached", ("E",), torch.bool),
    ("bad_transition", ("E",), torch.bool),
    ("completion_signals", ("E", "M", "N"), torch.bool),
    ("terminal_pair_failure_signals", ("E", "M", "N"), torch.bool),
    ("forced_release_signals", ("E", "M", "N"), torch.bool),
    ("robot_unavailable_signals", ("E", "M"), torch.bool),
    ("robot_recovered_signals", ("E", "M"), torch.bool),
    ("coverage_before_reset", ("E", "N"), torch.bool),
    ("task_state_before_transition", ("E", "N"), torch.int64),
    ("robot_state_before_transition", ("E", "M"), torch.int64),
    ("ownership_before_transition", ("E", "N"), torch.int64),
    ("consume_once_token", ("E",), torch.int64),
)
FACTS_FIELDS = (
    "schema_version",
    "producer_contract_version",
    "producer_id",
    *tuple(name for name, _, _ in FACTS_TENSOR_SPECS),
)
DERIVED_FORBIDDEN_FIELDS = (
    "TEAM_INFEASIBLE",
    "termination_reason",
    "updated_task_state",
    "updated_robot_state",
    "updated_ownership",
    "completed_tasks",
    "released_tasks",
    "new_failed_pairs",
    "updated_failed_pairs",
    "new_team_infeasible_tasks",
    "lifecycle_events",
    "authority_receipt_id",
)

RECEIPT_TENSOR_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    ("facts_consume_token", ("E",), torch.int64),
    ("authority_receipt_id", ("E",), torch.int64),
)
RECEIPT_FIELDS = (
    "schema_version",
    "producer_contract_version",
    "facts_producer_id",
    "authority_contract_version",
    "authority_id",
    *tuple(name for name, _, _ in RECEIPT_TENSOR_SPECS),
)

RESULT_INPUT_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("completed_tasks", ("E", "N"), torch.bool),
    ("released_tasks", ("E", "N"), torch.bool),
    ("new_failed_pairs", ("E", "M", "N"), torch.bool),
    ("prior_failed_pairs", ("E", "M", "N"), torch.bool),
    ("updated_failed_pairs", ("E", "M", "N"), torch.bool),
    ("new_team_infeasible_tasks", ("E", "N"), torch.bool),
    ("updated_task_state", ("E", "N"), torch.int64),
    ("updated_robot_state", ("E", "M"), torch.int64),
    ("updated_ownership", ("E", "N"), torch.int64),
    ("termination_reason", ("E",), torch.int64),
)
RESULT_TENSOR_SPECS: tuple[
    tuple[str, tuple[str, ...], torch.dtype], ...
] = (
    ("env_id", ("E",), torch.int64),
    ("episode_generation", ("E",), torch.int64),
    ("transition_generation", ("E",), torch.int64),
    *tuple(spec for spec in RESULT_INPUT_SPECS if spec[0] != "prior_failed_pairs"),
    ("facts_consume_token", ("E",), torch.int64),
    ("authority_receipt_id", ("E",), torch.int64),
)
RESULT_FIELDS = (
    "schema_version",
    "authority_contract_version",
    "facts_producer_id",
    "authority_id",
    *tuple(name for name, _, _ in RESULT_TENSOR_SPECS[:12]),
    "lifecycle_events",
    *tuple(name for name, _, _ in RESULT_TENSOR_SPECS[12:]),
)

PUBLIC_REQUIRED_TYPES = (
    "ExecutionFactsProducerId",
    "LifecycleAuthorityId",
    "TaskLifecycleState",
    "RobotLifecycleState",
    "TerminationReason",
    "ExecutionFactsProducerStamp",
    "LifecycleAuthorityStamp",
    "ExecutionTransitionFacts",
    "TransitionConsumeToken",
    "TransitionGenerationExpectation",
    "TransitionConsumeReceipt",
    "TransitionConsumeLedger",
    "LifecycleTransitionResult",
    "LifecycleTransitionResultFactory",
    "AssignmentTransitionContractError",
    "TransitionSchemaError",
    "TransitionGenerationError",
    "DuplicateTransitionConsumeError",
    "TransitionTokenMismatchError",
    "ExecutionFactsProducerMismatchError",
    "LifecycleAuthorityMismatchError",
    "FinalizedSnapshotMutationError",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_type: type[BaseException],
    failure_code: str | tuple[str, ...],
    *expected_text: str,
) -> BaseException:
    try:
        function()
    except exception_type as exc:
        allowed_codes = (
            (failure_code,) if isinstance(failure_code, str) else failure_code
        )
        actual_code = getattr(exc, "failure_code", None)
        _assert(
            actual_code in allowed_codes,
            f"expected failure_code in {allowed_codes!r}, got {actual_code!r}: {exc}",
        )
        rendered = str(exc)
        _assert(
            f"failure_code={actual_code!r}" in rendered,
            f"error omits stable failure code context: {rendered}",
        )
        _assert(
            "schema_version=" in rendered,
            f"error omits schema version context: {rendered}",
        )
        for text in expected_text:
            _assert(text in rendered, f"expected {text!r} in {rendered!r}")
        return exc
    except Exception as exc:
        raise AssertionError(
            f"expected {exception_type.__name__}, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {exception_type.__name__}")


def _load_contract() -> ModuleType:
    if not CONTRACT_PATH.is_file():
        raise RuntimeError(f"A2 contract source is absent: {CONTRACT_PATH}")
    existing = sys.modules.get(CANONICAL_MODULE)
    if existing is not None:
        existing_path = Path(str(getattr(existing, "__file__", ""))).resolve()
        _assert(
            existing_path == CONTRACT_PATH.resolve(),
            "canonical key points to a different source",
        )
        return existing
    spec = importlib.util.spec_from_file_location(
        CANONICAL_MODULE,
        CONTRACT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create canonical transition module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[CANONICAL_MODULE] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(CANONICAL_MODULE, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


CONTRACT = _load_contract()
CPU = torch.device("cpu")


def _load_event_contract() -> ModuleType:
    """Late-load A3 records without changing the A2 empty-event import path."""

    existing = sys.modules.get(CANONICAL_EVENT_MODULE)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(
        CANONICAL_EVENT_MODULE,
        EVENT_CONTRACT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create canonical event module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[CANONICAL_EVENT_MODULE] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(CANONICAL_EVENT_MODULE, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


def _producer_stamp() -> Any:
    return CONTRACT.ExecutionFactsProducerStamp(
        producer_id=(
            CONTRACT.ExecutionFactsProducerId
            .ENV_EXECUTION_FACTS_PRODUCER_V1
        ),
        producer_contract_version=CONTRACT.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
    )


def _authority_stamp() -> Any:
    return CONTRACT.LifecycleAuthorityStamp(
        authority_id=CONTRACT.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
        authority_contract_version=CONTRACT.LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
    )


def _shape(
    symbols: tuple[str, ...],
    *,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
) -> tuple[int, ...]:
    sizes = {"E": num_envs, "M": num_robots, "N": num_tasks}
    return tuple(sizes[symbol] for symbol in symbols)


def _valid_facts_values(
    num_envs: int = 2,
    num_robots: int = 3,
    num_tasks: int = 5,
) -> dict[str, object]:
    env_id = torch.arange(num_envs, dtype=torch.int64) * 104 + 101
    episode_generation = torch.arange(num_envs, dtype=torch.int64) + 7
    transition_generation = torch.arange(num_envs, dtype=torch.int64) + 40
    consume_once_token = torch.arange(num_envs, dtype=torch.int64) + 1000
    if num_robots > 0:
        ownership_row = (
            torch.arange(num_tasks, dtype=torch.int64) % num_robots
        )
    else:
        ownership_row = torch.full(
            (num_tasks,),
            -1,
            dtype=torch.int64,
        )
    ownership = ownership_row.view(1, num_tasks).expand(
        num_envs,
        num_tasks,
    ).clone()
    task_state = torch.arange(num_tasks, dtype=torch.int64).view(
        1,
        num_tasks,
    ).expand(num_envs, num_tasks).clone()
    robot_state = torch.arange(num_robots, dtype=torch.int64).view(
        1,
        num_robots,
    ).expand(num_envs, num_robots).clone()
    return {
        "schema_version": FACTS_VERSION,
        "producer_contract_version": PRODUCER_VERSION,
        "producer_id": (
            CONTRACT.ExecutionFactsProducerId
            .ENV_EXECUTION_FACTS_PRODUCER_V1
        ),
        "env_id": env_id,
        "episode_generation": episode_generation,
        "transition_generation": transition_generation,
        "physical_terminated": torch.zeros(
            (num_envs,),
            dtype=torch.bool,
        ),
        "physical_truncated": torch.zeros(
            (num_envs,),
            dtype=torch.bool,
        ),
        "time_limit_reached": torch.zeros(
            (num_envs,),
            dtype=torch.bool,
        ),
        "bad_transition": torch.zeros(
            (num_envs,),
            dtype=torch.bool,
        ),
        "completion_signals": torch.zeros(
            (num_envs, num_robots, num_tasks),
            dtype=torch.bool,
        ),
        "terminal_pair_failure_signals": torch.zeros(
            (num_envs, num_robots, num_tasks),
            dtype=torch.bool,
        ),
        "forced_release_signals": torch.zeros(
            (num_envs, num_robots, num_tasks),
            dtype=torch.bool,
        ),
        "robot_unavailable_signals": torch.zeros(
            (num_envs, num_robots),
            dtype=torch.bool,
        ),
        "robot_recovered_signals": torch.zeros(
            (num_envs, num_robots),
            dtype=torch.bool,
        ),
        "coverage_before_reset": torch.zeros(
            (num_envs, num_tasks),
            dtype=torch.bool,
        ),
        "task_state_before_transition": task_state,
        "robot_state_before_transition": robot_state,
        "ownership_before_transition": ownership,
        "consume_once_token": consume_once_token,
    }


def _facts(
    values: Mapping[str, object] | None = None,
    *,
    producer_stamp: Any | None = None,
    device: torch.device = CPU,
) -> Any:
    return CONTRACT.ExecutionTransitionFacts.from_mapping(
        _valid_facts_values() if values is None else values,
        producer_stamp=(
            _producer_stamp() if producer_stamp is None else producer_stamp
        ),
        device=device,
    )


def _expectations(
    facts: Any,
    *,
    episode_delta: int = 0,
    transition_delta: int = 0,
) -> tuple[Any, ...]:
    env_ids = facts.env_id
    episodes = facts.episode_generation
    transitions = facts.transition_generation
    return tuple(
        CONTRACT.TransitionGenerationExpectation(
            env_id=int(env_ids[row].item()),
            episode_generation=(
                int(episodes[row].item()) + episode_delta
            ),
            transition_generation=(
                int(transitions[row].item()) + transition_delta
            ),
        )
        for row in range(facts.num_envs)
    )


def _ledger() -> Any:
    return CONTRACT.TransitionConsumeLedger(
        authority_stamp=_authority_stamp(),
    )


def _consume(
    ledger: Any,
    facts: Any,
    *,
    producer_stamp: Any | None = None,
    expected_generations: tuple[Any, ...] | None = None,
) -> Any:
    return ledger.consume(
        facts,
        producer_stamp=(
            _producer_stamp() if producer_stamp is None else producer_stamp
        ),
        expected_generations=(
            _expectations(facts)
            if expected_generations is None
            else expected_generations
        ),
    )


def _slice_facts_values(
    values: Mapping[str, object],
    rows: list[int],
) -> dict[str, object]:
    sliced: dict[str, object] = {}
    for key, value in values.items():
        if type(value) is torch.Tensor:
            sliced[key] = value[rows].clone()
        else:
            sliced[key] = value
    return sliced


def _valid_result_inputs(
    facts: Any,
    *,
    completed_state_encoding: int = 17,
) -> dict[str, object]:
    completed = facts.completion_signals.any(dim=1)
    updated_task_state = facts.task_state_before_transition
    updated_robot_state = facts.robot_state_before_transition
    updated_ownership = facts.ownership_before_transition
    updated_task_state[completed] = completed_state_encoding
    updated_ownership[completed] = -1
    prior_failed_pairs = torch.zeros(
        (facts.num_envs, facts.num_robots, facts.num_tasks),
        dtype=torch.bool,
        device=facts.device,
    )
    new_failed_pairs = torch.zeros_like(prior_failed_pairs)
    return {
        "completed_tasks": completed,
        "released_tasks": torch.zeros(
            (facts.num_envs, facts.num_tasks),
            dtype=torch.bool,
            device=facts.device,
        ),
        "new_failed_pairs": new_failed_pairs,
        "prior_failed_pairs": prior_failed_pairs,
        "updated_failed_pairs": (
            prior_failed_pairs | new_failed_pairs
        ),
        "new_team_infeasible_tasks": torch.zeros(
            (facts.num_envs, facts.num_tasks),
            dtype=torch.bool,
            device=facts.device,
        ),
        "updated_task_state": updated_task_state,
        "updated_robot_state": updated_robot_state,
        "updated_ownership": updated_ownership,
        "termination_reason": torch.zeros(
            (facts.num_envs,),
            dtype=torch.int64,
            device=facts.device,
        ),
        "task_completed_state_encoding": completed_state_encoding,
        "lifecycle_events": (),
    }


def _lifecycle_event(
    facts: Any,
    *,
    row: int = 0,
    ordinal: int = 0,
    transition_delta: int = 0,
) -> Any:
    event_contract = _load_event_contract()
    env_id = int(facts.env_id[row].item())
    episode = int(facts.episode_generation[row].item())
    transition = (
        int(facts.transition_generation[row].item()) + transition_delta
    )
    token = int(facts.consume_once_token[row].item())
    return event_contract.LifecycleEventRecord(
        schema_version=(
            event_contract.LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION
        ),
        event_id=(env_id, episode, transition, ordinal),
        causal_source=(
            event_contract.LifecycleCausalSource.LIFECYCLE_DERIVATION
        ),
        event_type=event_contract.LifecycleEventType.ROBOT_NEEDS_ASSIGNMENT,
        env_id=env_id,
        episode_generation=episode,
        transition_generation=transition,
        ordinal=ordinal,
        robot_id=0,
        task_id=-1,
        trigger_eligible=True,
        facts_consume_token=token,
        authority_id=CONTRACT.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
        payload=event_contract.RobotLifecycleEventPayload(
            robot_id=0,
            previous_robot_state=3,
            updated_robot_state=4,
        ),
    )


def _consumed_context(
    values: Mapping[str, object] | None = None,
) -> tuple[Any, Any, Any, Any]:
    facts = _facts(values)
    ledger = _ledger()
    receipt = _consume(ledger, facts)
    factory = CONTRACT.LifecycleTransitionResultFactory(
        ledger=ledger,
        authority_stamp=ledger.authority_stamp,
    )
    return facts, ledger, receipt, factory


def _finalize(
    factory: Any,
    facts: Any,
    receipt: Any,
    inputs: Mapping[str, object] | None = None,
) -> Any:
    result_inputs = (
        _valid_result_inputs(facts)
        if inputs is None
        else dict(inputs)
    )
    return factory.finalize(
        facts=facts,
        receipt=receipt,
        **result_inputs,
    )


def _snapshot(ledger: Any) -> dict[str, object]:
    return dict(ledger.snapshot())


def _assert_frozen(instance: object, field_name: str, value: object) -> None:
    try:
        setattr(instance, field_name, value)
    except (FrozenInstanceError, AttributeError):
        return
    raise AssertionError(
        f"{type(instance).__name__}.{field_name} can be rebound"
    )


def _assert_mapping_readonly(mapping: Mapping[str, object]) -> None:
    try:
        mapping["__mutation_probe__"] = True  # type: ignore[index]
    except (TypeError, AttributeError):
        return
    raise AssertionError("mapping is writable")


def _assert_deep_readonly_primitive(value: object, label: str) -> None:
    if isinstance(value, Mapping):
        _assert_mapping_readonly(value)
        for key, nested in value.items():
            _assert(type(key) is str, f"{label} has non-string key")
            _assert_deep_readonly_primitive(
                nested,
                f"{label}.{key}",
            )
        return
    if isinstance(value, tuple):
        for index, nested in enumerate(value):
            _assert_deep_readonly_primitive(
                nested,
                f"{label}[{index}]",
            )
        return
    _assert(
        value is None or type(value) in {str, int, float, bool},
        f"{label} contains non-primitive {type(value).__name__}",
    )


def _private_corrupt_tensor(instance: object, field_name: str) -> None:
    """Implementation regression hook; private names are not semantic evidence."""

    snapshots = object.__getattribute__(instance, "_tensor_snapshots")
    snapshot = snapshots[field_name]
    tensor = object.__getattribute__(snapshot, "_tensor")
    if tensor.dtype is torch.bool:
        tensor.logical_not_()
    else:
        tensor.add_(1)


def _wrong_key_child_source() -> str:
    return r'''
import importlib.util
import json
from pathlib import Path
import sys

bare_name = "assignment_lifecycle_transition_contract"
canonical_name = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
module_path = Path(sys.argv[1]).resolve()
torch_before = "torch" in sys.modules
spec = importlib.util.spec_from_file_location(bare_name, module_path)
if spec is None or spec.loader is None:
    raise RuntimeError("could not create wrong-key spec")
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
except (ImportError, RuntimeError) as exc:
    error_type = type(exc).__name__
    error_text = str(exc)
else:
    raise AssertionError("wrong-key source execution succeeded")
public_types = {
    "ExecutionFactsProducerId",
    "LifecycleAuthorityId",
    "TerminationReason",
    "ExecutionFactsProducerStamp",
    "LifecycleAuthorityStamp",
    "ExecutionTransitionFacts",
    "TransitionConsumeReceipt",
    "TransitionConsumeLedger",
    "LifecycleTransitionResult",
}
print(json.dumps({
    "error_type": error_type,
    "error_text": error_text,
    "public_types_created": sorted(public_types & set(module.__dict__)),
    "torch_before": torch_before,
    "torch_after": "torch" in sys.modules,
    "bare_key_present": bare_name in sys.modules,
    "canonical_key_present": canonical_name in sys.modules,
}, sort_keys=True))
'''


def test_canonical_module_identity_and_source_guard() -> dict[str, Any]:
    _assert(CONTRACT.__name__ == CANONICAL_MODULE, "noncanonical __name__")
    _assert(
        sys.modules.get(CANONICAL_MODULE) is CONTRACT,
        "canonical key does not hold the loaded module",
    )
    _assert(BARE_MODULE not in sys.modules, "bare module key is active")
    source_keys = []
    for key, module in tuple(sys.modules.items()):
        module_path = getattr(module, "__file__", None)
        if not isinstance(module_path, str):
            continue
        try:
            same_source = Path(module_path).resolve() == CONTRACT_PATH.resolve()
        except (OSError, RuntimeError):
            same_source = False
        if same_source:
            source_keys.append(key)
    _assert(
        source_keys == [CANONICAL_MODULE],
        f"contract source has multiple keys: {source_keys}",
    )
    exported_public_types = {
        name
        for name in CONTRACT.__all__
        if isinstance(getattr(CONTRACT, name), type)
    }
    _assert(
        exported_public_types == set(PUBLIC_REQUIRED_TYPES),
        "public identity-bearing type inventory differs from __all__",
    )
    for name in PUBLIC_REQUIRED_TYPES:
        value = getattr(CONTRACT, name)
        _assert(
            value.__module__ == CANONICAL_MODULE,
            f"{name} has noncanonical __module__",
        )
    facts = _facts(_valid_facts_values(1, 1, 1))
    _assert(
        isinstance(facts, CONTRACT.ExecutionTransitionFacts),
        "strict canonical isinstance failed",
    )

    source = CONTRACT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(CONTRACT_PATH))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    _assert(classes, "contract declares no types")
    first_class_line = min(node.lineno for node in classes)
    guards = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and any(
            isinstance(candidate, ast.Name)
            and candidate.id == "__name__"
            for candidate in ast.walk(node.test)
        )
        and any(
            isinstance(candidate, ast.Raise)
            for candidate in ast.walk(node)
        )
    ]
    _assert(len(guards) == 1, "canonical guard is absent or ambiguous")
    torch_import_lines = [
        node.lineno
        for node in tree.body
        if isinstance(node, ast.Import)
        and any(alias.name == "torch" for alias in node.names)
    ]
    _assert(len(torch_import_lines) == 1, "torch import boundary is ambiguous")
    _assert(
        guards[0].lineno < torch_import_lines[0] < first_class_line,
        "canonical guard is not before torch and type declarations",
    )
    _assert(
        not any(
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
            and node.attr == "modules"
            for node in ast.walk(tree)
        ),
        "production contract accesses sys.modules",
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    forbidden_roots = {
        "isaaclab",
        "isaaclab_tasks",
        "omni",
        "pxr",
        "harl",
        "numpy",
        "random",
        "logging",
        "os",
        "pathlib",
        "pickle",
    }
    _assert(
        not (imported_roots & forbidden_roots),
        f"contract imports forbidden roots: "
        f"{sorted(imported_roots & forbidden_roots)}",
    )
    _assert(
        not any(
            isinstance(node, ast.Import)
            and any(alias.name == BARE_MODULE for alias in node.names)
            for node in ast.walk(tree)
        )
        and not any(
            isinstance(node, ast.ImportFrom)
            and node.module == BARE_MODULE
            for node in ast.walk(tree)
        ),
        "contract imports itself through a bare key",
    )

    child_source = _wrong_key_child_source()
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                child_source,
                str(CONTRACT_PATH.resolve()),
            ],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"wrong-key child failed: {completed.stdout!r} {completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(len(lines) == 1, "wrong-key child emitted non-JSON output")
    evidence = json.loads(lines[0])
    _assert(
        evidence["error_type"] in {"ImportError", "RuntimeError"},
        "wrong-key guard used an unexpected error",
    )
    for fragment in (CANONICAL_MODULE, BARE_MODULE, "purpose"):
        _assert(
            fragment in evidence["error_text"],
            f"wrong-key error omits {fragment!r}",
        )
    _assert(
        evidence["public_types_created"] == [],
        "wrong-key execution created identity-bearing types",
    )
    _assert(
        not evidence["torch_before"] and not evidence["torch_after"],
        "wrong-key execution imported torch",
    )
    _assert(
        not evidence["bare_key_present"]
        and not evidence["canonical_key_present"],
        "wrong-key child registered a source alias",
    )
    return {
        "canonical_module": CONTRACT.__name__,
        "sole_source_key": source_keys,
        "strict_isinstance": True,
        "guard_before_torch_and_types": True,
        "wrong_key_blocked_before_types": True,
    }


def test_versions_stamps_exceptions_and_schema_descriptor() -> dict[str, Any]:
    expected_constants = {
        "EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION": FACTS_VERSION,
        "LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION": RESULT_VERSION,
        "TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION": RECEIPT_VERSION,
        "EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION": PRODUCER_VERSION,
        "LIFECYCLE_AUTHORITY_CONTRACT_VERSION": AUTHORITY_VERSION,
        "PAIR_ATTRIBUTION_CONTRACT_VERSION": PAIR_VERSION,
        "OBSERVABLE_IMMUTABILITY_CONTRACT_VERSION": IMMUTABILITY_VERSION,
    }
    for name, expected in expected_constants.items():
        _assert(getattr(CONTRACT, name) == expected, f"{name} changed")
    _assert(
        tuple(member.value for member in CONTRACT.ExecutionFactsProducerId)
        == ("env_execution_facts_producer_v1",),
        "producer enum changed",
    )
    _assert(
        tuple(member.value for member in CONTRACT.LifecycleAuthorityId)
        == ("lifecycle_authority_v1",),
        "authority enum changed",
    )
    _assert(
        tuple((member.name, int(member)) for member in CONTRACT.TerminationReason)
        == (
            ("NONE", 0),
            ("ALL_TASKS_COMPLETED", 1),
            ("NO_FEASIBLE_TASKS_REMAIN", 2),
            ("TIME_LIMIT", 3),
        ),
        "termination enum changed",
    )
    producer = _producer_stamp()
    authority = _authority_stamp()
    _assert(is_dataclass(producer), "producer stamp is not a dataclass")
    _assert(is_dataclass(authority), "authority stamp is not a dataclass")
    _assert_frozen(producer, "producer_contract_version", "changed")
    _assert_frozen(authority, "authority_contract_version", "changed")
    producer_error = _expect_error(
        lambda: CONTRACT.ExecutionFactsProducerStamp(
            producer_id="env_execution_facts_producer_v1",
            producer_contract_version=PRODUCER_VERSION,
        ),
        CONTRACT.ExecutionFactsProducerMismatchError,
        "producer_stamp",
    )
    _assert(
        producer_error.expected_producer is not None
        and producer_error.actual_producer is not None,
        "producer stamp failure omits expected/actual producer",
    )
    authority_error = _expect_error(
        lambda: CONTRACT.LifecycleAuthorityStamp(
            authority_id="lifecycle_authority_v1",
            authority_contract_version=AUTHORITY_VERSION,
        ),
        CONTRACT.LifecycleAuthorityMismatchError,
        "authority_stamp",
    )
    _assert(
        authority_error.expected_authority is not None
        and authority_error.actual_authority is not None,
        "authority stamp failure omits expected/actual authority",
    )
    token = CONTRACT.TransitionConsumeToken(
        producer_id=producer.producer_id,
        env_id=101,
        episode_generation=7,
        transition_generation=40,
        consume_once_token=1000,
    )
    expectation = CONTRACT.TransitionGenerationExpectation(
        env_id=101,
        episode_generation=7,
        transition_generation=40,
    )
    _assert_frozen(token, "consume_once_token", 5)
    _assert_frozen(expectation, "transition_generation", 5)
    for error_name in (
        "TransitionSchemaError",
        "TransitionGenerationError",
        "DuplicateTransitionConsumeError",
        "TransitionTokenMismatchError",
        "ExecutionFactsProducerMismatchError",
        "LifecycleAuthorityMismatchError",
        "FinalizedSnapshotMutationError",
    ):
        _assert(
            issubclass(
                getattr(CONTRACT, error_name),
                CONTRACT.AssignmentTransitionContractError,
            ),
            f"{error_name} is outside the hierarchy",
        )

    descriptor = (
        CONTRACT.get_assignment_lifecycle_transition_schema_descriptor()
    )
    _assert(
        descriptor
        is CONTRACT.get_assignment_lifecycle_transition_schema_descriptor(),
        "descriptor is not deterministic",
    )
    _assert_deep_readonly_primitive(descriptor, "descriptor")
    _assert(
        descriptor["pair_attribution_contract_version"] == PAIR_VERSION,
        "pair descriptor version changed",
    )
    _assert(
        descriptor["observable_immutability_contract_version"]
        == IMMUTABILITY_VERSION,
        "immutability descriptor version changed",
    )
    facts_fields = tuple(
        field["name"] for field in descriptor["facts"]["fields"]
    )
    result_fields = tuple(
        field["name"] for field in descriptor["result"]["fields"]
    )
    _assert(facts_fields == FACTS_FIELDS, "facts descriptor order changed")
    _assert(result_fields == RESULT_FIELDS, "result descriptor order changed")
    rendered = json.dumps(
        _to_json_primitives(descriptor),
        sort_keys=True,
    ).lower()
    forbidden_private_terms = (
        "_mutation_version",
        "storage",
        "data_ptr",
        "digest",
        "_tensor_snapshots",
        "\"_tensor\"",
        "_finalization",
        "ledger_capability",
        "issuance_capability",
        "backing",
        "detector",
        "checkpoint",
        "runtime_class",
        "private_field",
    )
    for term in forbidden_private_terms:
        _assert(
            term not in rendered,
            f"descriptor exposes private term {term!r}",
        )
    return {
        "facts_version": FACTS_VERSION,
        "result_version": RESULT_VERSION,
        "receipt_version": RECEIPT_VERSION,
        "producer_id": producer.producer_id.value,
        "authority_id": authority.authority_id.value,
        "termination_reasons": [
            member.name for member in CONTRACT.TerminationReason
        ],
        "descriptor_deep_readonly": True,
        "descriptor_private_terms_absent": True,
    }


def test_v2_state_enums_and_failure_termination_projection() -> dict[str, Any]:
    """Freeze the A3x-1 additions without weakening the A2 DTO contract."""

    _assert(
        CONTRACT.ASSIGNMENT_LIFECYCLE_TRANSITION_CONTRACT_VERSION
        == CONTRACT_VERSION,
        "transition public descriptor version is not v2",
    )
    for enum_name, expected_order in (
        ("TaskLifecycleState", TASK_STATE_ORDER),
        ("RobotLifecycleState", ROBOT_STATE_ORDER),
        ("TerminationReason", TERMINATION_REASON_ORDER),
    ):
        enum_type = getattr(CONTRACT, enum_name)
        actual_order = tuple((member.name, int(member)) for member in enum_type)
        _assert(actual_order == expected_order, f"{enum_name} order drifted")
        _assert(
            len(enum_type.__members__) == len(expected_order),
            f"{enum_name} contains an alias",
        )
        _assert(
            enum_type.__module__ == CANONICAL_MODULE,
            f"{enum_name} has noncanonical identity",
        )
    _assert(
        "ROBOT_RECOVERED" not in CONTRACT.RobotLifecycleState.__members__,
        "transient recovery event became persistent robot state",
    )

    descriptor = (
        CONTRACT.get_assignment_lifecycle_transition_schema_descriptor()
    )
    _assert(
        descriptor["contract_version"] == CONTRACT_VERSION,
        "descriptor does not expose the v2 identity",
    )
    semantics = descriptor["failure_termination_semantics"]
    _assert(
        tuple(semantics) == FAILURE_TERMINATION_KEYS,
        "failure/termination projection key order drifted",
    )
    expected = {
        "projection_version": FAILURE_TERMINATION_VERSION,
        "task_state_enum_order": TASK_STATE_ORDER,
        "robot_state_enum_order": ROBOT_STATE_ORDER,
        "transient_event_exclusion": (
            "ROBOT_RECOVERED_is_a_transient_lifecycle_event_not_a_"
            "RobotLifecycleState"
        ),
        "termination_reason_order": TERMINATION_REASON_ORDER,
        "failed_pair_source": (
            "ExecutionTransitionFacts.terminal_pair_failure_signals_and_"
            "episode_cumulative_prior_failed_pairs"
        ),
        "new_failed_pairs_equation": (
            "new_failed_pairs=terminal_pair_failure_signals AND NOT "
            "prior_failed_pairs"
        ),
        "updated_failed_pairs_equation": (
            "updated_failed_pairs=prior_failed_pairs OR new_failed_pairs"
        ),
        "failed_pair_episode_reset_rule": (
            "updated_failed_pairs_is_episode_cumulative_and_clears_only_on_"
            "episode_reset"
        ),
        "team_infeasible_equation": (
            "TEAM_INFEASIBLE[j]=event_updated_task_state[j]!=COMPLETED AND "
            "all_i(updated_failed_pairs[i,j])"
        ),
        "new_team_infeasible_equation": (
            "new_team_infeasible_tasks[j]=NOT prior_team_infeasible[j] AND "
            "event_updated_task_state[j]!=COMPLETED AND "
            "all_i(updated_failed_pairs[i,j])"
        ),
        "path_invalid_non_equivalence": (
            "all_nominal_paths_invalid_does_not_imply_TEAM_INFEASIBLE"
        ),
        "terminal_task_ownership_release_rule": (
            "COMPLETED_or_TEAM_INFEASIBLE_task_ownership_is_NO_OWNER_"
            "before_a0"
        ),
        "event_updated_baseline_order": (
            "finalize_execution_and_lifecycle_facts",
            "write_completion_release_failed_pair_and_robot_availability",
            "derive_TEAM_INFEASIBLE_after_updated_failed_pairs",
            "release_terminal_task_ownership",
            "finalize_updated_task_robot_and_ownership_state_as_a0",
            "derive_termination_before_assignment",
        ),
        "termination_priority": (
            "ALL_TASKS_COMPLETED",
            "NO_FEASIBLE_TASKS_REMAIN",
            "TIME_LIMIT",
            "NONE",
        ),
        "physical_terminal_mapping_boundary": (
            "all_tasks_completed=>ALL_TASKS_COMPLETED",
            "all_tasks_completed_or_team_infeasible=>"
            "NO_FEASIBLE_TASKS_REMAIN",
            "time_limit_reached=>TIME_LIMIT",
        ),
        "bad_transition_boundary": (
            "bad_transition_is_a_bootstrap_transport_fact_not_a_"
            "TerminationReason"
        ),
        "unmappable_physical_terminal_rule": (
            "physical_terminated_or_truncated_with_final_reason_NONE_or_"
            "unsupported_non_time_limit_boundary=>typed_fail_closed_with_"
            "DVM_zero_no_proposal_no_commit"
        ),
        "terminal_assignment_rule": (
            "target_noop_available_action_masks_all_false",
            "semantic_legal_action_count=0",
            "forced_policy_action_id=-1",
            "no_actor_sampling_action_log_probability_proposal_"
            "forced_nondecision_resolver_or_component_row",
            "finalized_pre_reset_critic_shared_sidecar_only",
        ),
        "episode_generation_rule": (
            "increment_once_per_episode_reset_and_rebuild_all_episode_"
            "lifecycle_MRTA_retry_and_termination_state"
        ),
        "transition_generation_rule": (
            "per_env_process_lifetime_monotonic_increment_once_per_"
            "finalized_physical_transition_and_never_reset_on_episode_reset"
        ),
        "assignment_tick_generation_rule": (
            "per_env_process_lifetime_monotonic_increment_once_per_"
            "canonical_merged_assignment_tick;overlapping_same_transition_"
            "triggers_share_one_increment;no_tick_no_increment"
        ),
    }
    _assert(dict(semantics) == expected, "failure/termination literals drifted")

    _assert(
        CONTRACT.EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION == FACTS_VERSION
        and CONTRACT.LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION
        == RESULT_VERSION
        and CONTRACT.TRANSITION_CONSUME_RECEIPT_SCHEMA_VERSION
        == RECEIPT_VERSION,
        "A3x-1 changed an existing A2 record schema version",
    )
    _assert(
        tuple(item["name"] for item in descriptor["facts"]["fields"])
        == FACTS_FIELDS
        and tuple(item["name"] for item in descriptor["result"]["fields"])
        == RESULT_FIELDS,
        "A3x-1 changed an existing A2 record field order",
    )
    _assert_deep_readonly_primitive(semantics, "failure_termination_semantics")
    return {
        "contract_version": CONTRACT_VERSION,
        "task_state_order": TASK_STATE_ORDER,
        "robot_state_order": ROBOT_STATE_ORDER,
        "termination_reason_order": TERMINATION_REASON_ORDER,
        "failure_projection_keys": len(FAILURE_TERMINATION_KEYS),
        "old_record_schemas_unchanged": True,
        "terminal_assignment_no_row": True,
    }


def _to_json_primitives(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _to_json_primitives(nested)
            for key, nested in value.items()
        }
    if isinstance(value, tuple):
        return [_to_json_primitives(nested) for nested in value]
    if isinstance(value, Enum):
        return value.value
    return value


def test_execution_facts_valid_shapes_and_scale() -> dict[str, Any]:
    checked_scales = []
    for num_envs, num_robots, num_tasks in ((1, 1, 1), (2, 3, 5)):
        facts = _facts(
            _valid_facts_values(num_envs, num_robots, num_tasks)
        )
        facts.validate_integrity()
        _assert(facts.device == CPU, "facts moved device")
        _assert(facts.num_envs == num_envs, "facts E changed")
        _assert(facts.num_robots == num_robots, "facts M changed")
        _assert(facts.num_tasks == num_tasks, "facts N changed")
        for name, symbols, dtype in FACTS_TENSOR_SPECS:
            value = getattr(facts, name)
            _assert(
                tuple(value.shape)
                == _shape(
                    symbols,
                    num_envs=num_envs,
                    num_robots=num_robots,
                    num_tasks=num_tasks,
                ),
                f"{name} shape changed",
            )
            _assert(value.dtype is dtype, f"{name} dtype changed")
            _assert(value.device == CPU, f"{name} device changed")
            _assert(value.is_contiguous(), f"{name} is not contiguous")
            _assert(not value.requires_grad, f"{name} requires grad")
        mapping = facts.to_mapping()
        _assert(type(mapping) is MappingProxyType, "facts mapping is mutable")
        _assert(tuple(mapping) == FACTS_FIELDS, "facts mapping order changed")
        checked_scales.append([num_envs, num_robots, num_tasks])

    values = _valid_facts_values(2, 3, 5)
    noncontiguous = torch.zeros(
        (2, 5, 3),
        dtype=torch.bool,
    ).transpose(1, 2)
    _assert(not noncontiguous.is_contiguous(), "fixture is contiguous")
    values["completion_signals"] = noncontiguous
    facts = _facts(values)
    _assert(
        facts.completion_signals.is_contiguous(),
        "construction did not make an isolated contiguous clone",
    )
    _expect_error(
        lambda: CONTRACT.ExecutionTransitionFacts(),
        CONTRACT.TransitionSchemaError,
        "factory_required",
    )
    with torch.inference_mode():
        inference_facts = _facts(_valid_facts_values(1, 1, 1))
        inference_ledger = _ledger()
        inference_receipt = _consume(inference_ledger, inference_facts)
        inference_factory = CONTRACT.LifecycleTransitionResultFactory(
            ledger=inference_ledger,
            authority_stamp=inference_ledger.authority_stamp,
        )
        inference_result = _finalize(
            inference_factory,
            inference_facts,
            inference_receipt,
        )
        inference_facts.validate_integrity()
        inference_receipt.validate_integrity()
        inference_result.validate_finalized()
    return {
        "valid_scales": checked_scales,
        "exact_dtypes": True,
        "explicit_cpu_preserved": True,
        "contiguous_clone": True,
        "mapping_order_exact": True,
        "inference_mode_construct_consume_finalize": True,
    }


def test_execution_facts_schema_failure_matrix() -> dict[str, Any]:
    shape_failures = []
    for name, _, _ in FACTS_TENSOR_SPECS:
        values = _valid_facts_values()
        tensor = values[name]
        _assert(type(tensor) is torch.Tensor, f"fixture {name} is not tensor")
        values[name] = tensor.unsqueeze(0)
        _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "shape",
        )
        shape_failures.append(name)

    dtype_failures = []
    for name, _, dtype in FACTS_TENSOR_SPECS:
        values = _valid_facts_values()
        tensor = values[name]
        _assert(type(tensor) is torch.Tensor, f"fixture {name} is not tensor")
        wrong_dtype = torch.int64 if dtype is torch.bool else torch.int32
        values[name] = tensor.to(dtype=wrong_dtype)
        _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "dtype",
        )
        dtype_failures.append(name)

    values = _valid_facts_values()
    values["coverage_before_reset"] = torch.zeros(
        (2, 5),
        dtype=torch.bool,
        device="meta",
    )
    _expect_error(
        lambda: _facts(values),
        CONTRACT.TransitionSchemaError,
        "device",
    )
    _expect_error(
        lambda: CONTRACT.ExecutionTransitionFacts.from_mapping(
            _valid_facts_values(),
            producer_stamp=_producer_stamp(),
            device="cpu",
        ),
        CONTRACT.TransitionSchemaError,
        "device",
    )
    _expect_error(
        lambda: CONTRACT.ExecutionTransitionFacts.from_mapping(
            _valid_facts_values(),
            producer_stamp=_producer_stamp(),
            device=torch.device("meta"),
        ),
        CONTRACT.TransitionSchemaError,
        "device",
    )
    _expect_error(
        lambda: CONTRACT.ExecutionTransitionFacts.from_mapping(
            [],
            producer_stamp=_producer_stamp(),
            device=CPU,
        ),
        CONTRACT.TransitionSchemaError,
        "mapping_type",
    )

    missing = _valid_facts_values()
    missing.pop("bad_transition")
    _expect_error(
        lambda: _facts(missing),
        CONTRACT.TransitionSchemaError,
        "missing_fields",
    )
    for field_name in (*DERIVED_FORBIDDEN_FIELDS, "generic_unknown"):
        values = _valid_facts_values()
        values[field_name] = False
        exc = _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "unexpected_fields",
        )
        _assert(field_name in str(exc), f"error omits {field_name}")

    values = _valid_facts_values()
    values["schema_version"] = "wrong"
    _expect_error(
        lambda: _facts(values),
        CONTRACT.TransitionSchemaError,
        "schema_version",
    )
    values = _valid_facts_values()
    values["producer_contract_version"] = "wrong"
    _expect_error(
        lambda: _facts(values),
        CONTRACT.ExecutionFactsProducerMismatchError,
        "producer_contract_version",
    )
    values = _valid_facts_values()
    values["producer_id"] = "env_execution_facts_producer_v1"
    _expect_error(
        lambda: _facts(values),
        CONTRACT.ExecutionFactsProducerMismatchError,
        "producer_id",
    )
    _expect_error(
        lambda: _facts(
            _valid_facts_values(),
            producer_stamp=_authority_stamp(),
        ),
        CONTRACT.ExecutionFactsProducerMismatchError,
        "producer_stamp",
    )

    for dimensions in ((0, 1, 1), (1, 0, 1), (1, 1, 0)):
        _expect_error(
            lambda dimensions=dimensions: _facts(
                _valid_facts_values(*dimensions)
            ),
            CONTRACT.TransitionSchemaError,
            "dimensions",
        )
    values = _valid_facts_values()
    values["env_id"][1] = values["env_id"][0]
    _expect_error(
        lambda: _facts(values),
        CONTRACT.TransitionSchemaError,
        "env_id_unique",
    )
    for name in (
        "episode_generation",
        "transition_generation",
        "consume_once_token",
    ):
        values = _valid_facts_values()
        values[name][0] = -1
        _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "nonnegative",
        )
    for invalid_owner in (-2, 3):
        values = _valid_facts_values()
        values["ownership_before_transition"][0, 0] = invalid_owner
        _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "ownership_range",
        )
    for flag_name in ("time_limit_reached", "bad_transition"):
        values = _valid_facts_values()
        values[flag_name][0] = True
        _expect_error(
            lambda values=values: _facts(values),
            CONTRACT.TransitionSchemaError,
            "truncation_relation",
        )
    values = _valid_facts_values()
    values["env_id"] = torch.zeros(
        (2,),
        dtype=torch.float32,
        requires_grad=True,
    )
    _expect_error(
        lambda: _facts(values),
        CONTRACT.TransitionSchemaError,
        "dtype",
    )
    return {
        "shape_fields_rejected": shape_failures,
        "dtype_fields_rejected": dtype_failures,
        "derived_fields_rejected": list(DERIVED_FORBIDDEN_FIELDS),
        "no_implicit_cast_or_move": True,
        "nonnegative_and_ownership_assertions": True,
        "requires_grad_exact_dtype_note": (
            "bool/int64 cannot require grad; a requires-grad float is "
            "rejected without cast"
        ),
    }


def _construct_and_consume(
    values: Mapping[str, object],
    ledger: Any,
) -> Any:
    facts = _facts(values)
    return _consume(ledger, facts)


def test_pair_attribution_and_atomic_rejection_matrix() -> dict[str, Any]:
    valid = _valid_facts_values()
    valid["completion_signals"][0, 0, 0] = True
    valid["completion_signals"][1, 1, 1] = True
    facts = _facts(valid)
    ledger = _ledger()
    _consume(ledger, facts)

    cases: list[tuple[str, str, Callable[[dict[str, object]], None]]] = []

    def two_complete(values: dict[str, object]) -> None:
        values["completion_signals"][0, 0, 0] = True
        values["completion_signals"][0, 1, 0] = True

    cases.append(("two_complete_one_task", "completion_cardinality", two_complete))

    def pair_conflict(values: dict[str, object]) -> None:
        values["completion_signals"][0, 0, 0] = True
        values["terminal_pair_failure_signals"][0, 0, 0] = True

    cases.append(("completion_failure_same_pair", "pair_signal_conflict", pair_conflict))

    def completion_nonowner(values: dict[str, object]) -> None:
        values["completion_signals"][0, 1, 0] = True

    cases.append(("completion_nonowner", "completion_owner", completion_nonowner))

    def release_nonowner(values: dict[str, object]) -> None:
        values["forced_release_signals"][0, 1, 0] = True

    cases.append(("release_nonowner", "release_owner", release_nonowner))

    def failure_nonowner(values: dict[str, object]) -> None:
        values["terminal_pair_failure_signals"][0, 1, 0] = True

    cases.append(("failure_nonowner", "failure_owner", failure_nonowner))

    for field_name, code in (
        ("completion_signals", "completion_owner"),
        ("forced_release_signals", "release_owner"),
        ("terminal_pair_failure_signals", "failure_owner"),
    ):
        def unowned(
            values: dict[str, object],
            field_name: str = field_name,
        ) -> None:
            values["ownership_before_transition"][0, 0] = -1
            values[field_name][0, 0, 0] = True

        cases.append((f"unowned_{field_name}", code, unowned))

    def availability(values: dict[str, object]) -> None:
        values["robot_unavailable_signals"][0, 0] = True
        values["robot_recovered_signals"][0, 0] = True

    cases.append(("availability_edge_conflict", "availability_edge_conflict", availability))

    evidence: dict[str, str] = {}
    for case_name, code, mutate in cases:
        values = _valid_facts_values()
        mutate(values)
        ledger = _ledger()
        before = _snapshot(ledger)
        _expect_error(
            lambda values=values, ledger=ledger: _construct_and_consume(
                values,
                ledger,
            ),
            CONTRACT.TransitionSchemaError,
            code,
        )
        _assert(
            _snapshot(ledger) == before,
            f"{case_name} changed the ledger",
        )
        evidence[case_name] = code
    return {
        "valid_owner_attributed_completions": True,
        "failure_matrix": evidence,
        "ledger_unchanged_for_every_rejection": True,
    }


def test_generation_expectation_and_ledger_failure_matrix() -> dict[str, Any]:
    values = _valid_facts_values(1, 2, 3)
    facts = _facts(values)
    ledger = _ledger()
    receipt = _consume(ledger, facts)
    _assert(receipt.num_envs == 1, "first consume returned wrong batch")
    before_duplicate = _snapshot(ledger)
    duplicate_error = _expect_error(
        lambda: _consume(ledger, facts),
        CONTRACT.DuplicateTransitionConsumeError,
        "duplicate",
        "env_id=101",
    )
    for context_field in (
        "env_id",
        "expected_episode_generation",
        "actual_episode_generation",
        "expected_transition_generation",
        "actual_transition_generation",
        "expected_token",
        "actual_token",
        "expected_producer",
        "actual_producer",
    ):
        _assert(
            getattr(duplicate_error, context_field, None) is not None,
            f"duplicate failure omits {context_field}",
        )
    _assert(
        _snapshot(ledger) == before_duplicate,
        "duplicate consume mutated ledger",
    )

    changed_token_values = _valid_facts_values(1, 2, 3)
    changed_token_values["consume_once_token"][0] += 1
    changed_token = _facts(changed_token_values)
    token_error = _expect_error(
        lambda: _consume(ledger, changed_token),
        CONTRACT.TransitionTokenMismatchError,
        "generation_token",
    )
    _assert(
        token_error.expected_token is not None
        and token_error.actual_token is not None,
        "generation-token mismatch omits expected/actual token",
    )
    _assert(
        _snapshot(ledger) == before_duplicate,
        "generation-token mismatch mutated ledger",
    )

    matrix: dict[str, str] = {}
    for label, expectations, expected_code in (
        (
            "stale",
            _expectations(facts, transition_delta=1),
            "stale",
        ),
        (
            "future",
            _expectations(facts, transition_delta=-1),
            "future",
        ),
        (
            "wrong_episode",
            _expectations(facts, episode_delta=1),
            "episode",
        ),
        (
            "wrong_env",
            (
                CONTRACT.TransitionGenerationExpectation(
                    env_id=999,
                    episode_generation=7,
                    transition_generation=40,
                ),
            ),
            "env_id",
        ),
    ):
        fresh_ledger = _ledger()
        before = _snapshot(fresh_ledger)
        generation_error = _expect_error(
            lambda fresh_ledger=fresh_ledger, expectations=expectations: _consume(
                fresh_ledger,
                facts,
                expected_generations=expectations,
            ),
            CONTRACT.TransitionGenerationError,
            expected_code,
        )
        if label in {"stale", "future"}:
            _assert(
                generation_error.expected_transition_generation is not None
                and generation_error.actual_transition_generation is not None,
                f"{label} failure omits expected/actual transition",
            )
        elif label == "wrong_episode":
            _assert(
                generation_error.expected_episode_generation is not None
                and generation_error.actual_episode_generation is not None,
                "wrong episode failure omits expected/actual episode",
            )
        else:
            _assert(
                generation_error.expected is not None
                and generation_error.actual is not None,
                "wrong env failure omits expected/actual env set",
            )
        _assert(
            _snapshot(fresh_ledger) == before,
            f"{label} changed ledger",
        )
        matrix[label] = expected_code

    fresh_ledger = _ledger()
    before = _snapshot(fresh_ledger)
    _expect_error(
        lambda: fresh_ledger.consume(
            facts,
            producer_stamp=_authority_stamp(),
            expected_generations=_expectations(facts),
        ),
        CONTRACT.ExecutionFactsProducerMismatchError,
        "producer_stamp",
    )
    _assert(_snapshot(fresh_ledger) == before, "wrong producer mutated ledger")

    _expect_error(
        lambda: fresh_ledger.consume(
            facts,
            producer_stamp=_producer_stamp(),
            expected_generations=list(_expectations(facts)),
        ),
        CONTRACT.TransitionGenerationError,
        "expectation_type",
    )
    duplicate_expectation = _expectations(facts)[0]
    _expect_error(
        lambda: _consume(
            fresh_ledger,
            facts,
            expected_generations=(
                duplicate_expectation,
                duplicate_expectation,
            ),
        ),
        CONTRACT.TransitionGenerationError,
        "env_id",
    )
    _expect_error(
        lambda: _consume(
            fresh_ledger,
            facts,
            expected_generations=(object(),),
        ),
        CONTRACT.TransitionGenerationError,
        "expectation_type",
    )

    two_row_facts = _facts(_valid_facts_values())
    reverse_ledger = _ledger()
    reversed_expectations = tuple(reversed(_expectations(two_row_facts)))
    _consume(
        reverse_ledger,
        two_row_facts,
        expected_generations=reversed_expectations,
    )

    history_ledger = _ledger()
    first_values = _valid_facts_values(1, 2, 3)
    first = _facts(first_values)
    _consume(history_ledger, first)
    next_values = _valid_facts_values(1, 2, 3)
    next_values["transition_generation"][0] = 41
    next_values["consume_once_token"][0] = 1001
    next_facts = _facts(next_values)
    _consume(history_ledger, next_facts)
    rollback_values = _valid_facts_values(1, 2, 3)
    rollback_values["transition_generation"][0] = 39
    rollback_values["consume_once_token"][0] = 999
    rollback = _facts(rollback_values)
    before = _snapshot(history_ledger)
    _expect_error(
        lambda: _consume(history_ledger, rollback),
        CONTRACT.TransitionGenerationError,
        "stale",
    )
    _assert(
        _snapshot(history_ledger) == before,
        "history rollback mutated ledger",
    )
    return {
        "correct_first_consume": True,
        "duplicate": "duplicate",
        "generation_token_mismatch": "generation_token",
        "generation_matrix": matrix,
        "wrong_producer_atomic": True,
        "expectation_tuple_exact": True,
        "expectation_order_by_env_id": True,
        "last_consumed_monotonic_guard": True,
    }


def test_batch_atomicity_receipt_identity_and_rng() -> dict[str, Any]:
    facts = _facts(_valid_facts_values())
    ledger = _ledger()
    python_rng_before = random.getstate()
    torch_rng_before = torch.random.get_rng_state().clone()
    receipt = _consume(ledger, facts)
    _assert(random.getstate() == python_rng_before, "consume changed Python RNG")
    _assert(
        torch.equal(torch.random.get_rng_state(), torch_rng_before),
        "consume changed Torch RNG",
    )
    receipt.validate_integrity()
    _assert(receipt.schema_version == RECEIPT_VERSION, "receipt version changed")
    mapping = receipt.to_mapping()
    _assert(type(mapping) is MappingProxyType, "receipt mapping is mutable")
    _assert(tuple(mapping) == RECEIPT_FIELDS, "receipt mapping order changed")
    for name, symbols, dtype in RECEIPT_TENSOR_SPECS:
        value = getattr(receipt, name)
        _assert(value.dtype is dtype, f"receipt {name} dtype changed")
        _assert(
            tuple(value.shape)
            == _shape(
                symbols,
                num_envs=2,
                num_robots=1,
                num_tasks=1,
            ),
            f"receipt {name} shape changed",
        )
        clone = getattr(receipt, name)
        if clone.dtype is torch.bool:
            clone.logical_not_()
        else:
            clone.add_(100)
        _assert(
            torch.equal(getattr(receipt, name), value),
            f"receipt {name} accessor aliases backing",
        )
    _assert(
        not torch.equal(
            receipt.facts_consume_token,
            receipt.authority_receipt_id,
        ),
        "receipt IDs equal raw facts tokens",
    )
    _assert_frozen(receipt, "schema_version", "changed")
    _expect_error(
        lambda: CONTRACT.TransitionConsumeReceipt(),
        CONTRACT.LifecycleAuthorityMismatchError,
        "ledger_receipt_required",
    )

    invalid_ledger = _ledger()
    before = _snapshot(invalid_ledger)
    expectations = list(_expectations(facts))
    second = expectations[1]
    expectations[1] = CONTRACT.TransitionGenerationExpectation(
        env_id=second.env_id,
        episode_generation=second.episode_generation,
        transition_generation=second.transition_generation + 1,
    )
    _expect_error(
        lambda: _consume(
            invalid_ledger,
            facts,
            expected_generations=tuple(expectations),
        ),
        CONTRACT.TransitionGenerationError,
        "stale",
    )
    _assert(
        _snapshot(invalid_ledger) == before,
        "one invalid row partially committed",
    )
    retry_receipt = _consume(invalid_ledger, facts)
    control_ledger = _ledger()
    control_receipt = _consume(control_ledger, facts)
    _assert(
        torch.equal(
            retry_receipt.authority_receipt_id,
            control_receipt.authority_receipt_id,
        ),
        "failed batch skipped receipt IDs",
    )

    batch_values = _valid_facts_values()
    partial_ledger = _ledger()
    first_row = _facts(_slice_facts_values(batch_values, [0]))
    _consume(partial_ledger, first_row)
    before_mixed = _snapshot(partial_ledger)
    full_batch = _facts(batch_values)
    _expect_error(
        lambda: _consume(partial_ledger, full_batch),
        CONTRACT.DuplicateTransitionConsumeError,
        "duplicate",
    )
    _assert(
        _snapshot(partial_ledger) == before_mixed,
        "duplicate/new mixed batch partially committed",
    )
    second_row = _facts(_slice_facts_values(batch_values, [1]))
    second_receipt = _consume(partial_ledger, second_row)
    _assert(
        second_receipt.authority_receipt_id.tolist() == [1],
        "rejected mixed batch advanced the new env receipt counter",
    )

    next_values = _valid_facts_values()
    next_values["transition_generation"] += 1
    next_values["consume_once_token"] += 10
    next_facts = _facts(next_values)
    next_receipt = _consume(ledger, next_facts)
    _assert(
        torch.equal(
            next_receipt.authority_receipt_id,
            receipt.authority_receipt_id + 1,
        ),
        "receipt IDs are not per-env monotonic",
    )

    shared_token_values = _valid_facts_values()
    shared_token_values["consume_once_token"].fill_(777)
    shared_token_facts = _facts(shared_token_values)
    shared_token_ledger = _ledger()
    shared_token_receipt = _consume(
        shared_token_ledger,
        shared_token_facts,
    )
    _assert(
        shared_token_receipt.facts_consume_token.tolist() == [777, 777],
        "same token across envs was rewritten",
    )
    snapshot = ledger.snapshot()
    _assert(type(snapshot) is MappingProxyType, "ledger snapshot is writable")
    _assert_mapping_readonly(snapshot)
    return {
        "two_row_atomic_receipt": True,
        "failed_batch_no_state_or_id_change": True,
        "duplicate_plus_new_atomic": True,
        "receipt_id_per_env_monotonic": True,
        "composite_key_allows_same_token_across_envs": True,
        "receipt_alias_isolated": True,
        "python_rng_unchanged": True,
        "torch_rng_unchanged": True,
    }


def test_result_factory_binding_and_authority_matrix() -> dict[str, Any]:
    facts, ledger, receipt, factory = _consumed_context()
    result = _finalize(factory, facts, receipt)
    result.validate_finalized()
    _assert(
        _snapshot(ledger)["finalized_receipt_count"] == 1,
        "valid result did not claim finalization",
    )
    _assert(
        result.facts_producer_id is facts.producer_id,
        "result changed facts producer",
    )
    _assert(
        result.authority_id
        is CONTRACT.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
        "result authority changed",
    )
    _expect_error(
        lambda: CONTRACT.LifecycleTransitionResult(),
        CONTRACT.LifecycleAuthorityMismatchError,
        "factory_required",
    )
    forged = object.__new__(CONTRACT.LifecycleTransitionResult)
    _expect_error(
        forged.validate_finalized,
        CONTRACT.LifecycleAuthorityMismatchError,
        "result_uninitialized",
    )

    facts, ledger, receipt, factory = _consumed_context()
    _expect_error(
        lambda: _finalize(factory, facts, None),
        CONTRACT.LifecycleAuthorityMismatchError,
        "receipt_type",
    )
    _assert(
        _snapshot(ledger)["finalized_receipt_count"] == 0,
        "missing receipt changed finalization state",
    )

    other_ledger = _ledger()
    other_receipt = _consume(other_ledger, facts)
    _assert(
        other_receipt.authority_id is receipt.authority_id
        and other_receipt.authority_contract_version
        == receipt.authority_contract_version,
        "cross-ledger case changed the canonical authority identity",
    )
    factory_ledger_before = _snapshot(ledger)
    other_ledger_before = _snapshot(other_ledger)
    _expect_error(
        lambda: _finalize(factory, facts, other_receipt),
        CONTRACT.LifecycleAuthorityMismatchError,
        "receipt_issuer",
    )
    _assert(
        _snapshot(ledger) == factory_ledger_before
        and _snapshot(other_ledger) == other_ledger_before,
        "cross-ledger receipt rejection changed ledger state",
    )

    mismatch_cases: list[
        tuple[str, type[BaseException], str, Callable[[dict[str, object]], None]]
    ] = []

    def token_mismatch(values: dict[str, object]) -> None:
        values["consume_once_token"][0] += 99

    mismatch_cases.append(
        (
            "token",
            CONTRACT.TransitionTokenMismatchError,
            "result_token",
            token_mismatch,
        )
    )

    def env_mismatch(values: dict[str, object]) -> None:
        values["env_id"][0] += 1

    mismatch_cases.append(
        ("env", CONTRACT.TransitionGenerationError, "env_id", env_mismatch)
    )

    def episode_mismatch(values: dict[str, object]) -> None:
        values["episode_generation"][0] += 1

    mismatch_cases.append(
        (
            "episode",
            CONTRACT.TransitionGenerationError,
            "episode",
            episode_mismatch,
        )
    )

    def transition_mismatch(values: dict[str, object]) -> None:
        values["transition_generation"][0] += 1

    mismatch_cases.append(
        (
            "transition",
            CONTRACT.TransitionGenerationError,
            "transition",
            transition_mismatch,
        )
    )

    binding_evidence: dict[str, str] = {}
    binding_context_fields = {
        "episode": (
            "expected_episode_generation",
            "actual_episode_generation",
        ),
        "transition": (
            "expected_transition_generation",
            "actual_transition_generation",
        ),
        "token": ("expected_token", "actual_token"),
    }
    base_values = _valid_facts_values()
    base_facts = _facts(base_values)
    binding_ledger = _ledger()
    binding_receipt = _consume(binding_ledger, base_facts)
    binding_factory = CONTRACT.LifecycleTransitionResultFactory(
        ledger=binding_ledger,
        authority_stamp=binding_ledger.authority_stamp,
    )
    for label, error_type, code, mutate in mismatch_cases:
        changed = _valid_facts_values()
        mutate(changed)
        changed_facts = _facts(changed)
        before = _snapshot(binding_ledger)
        mismatch_error = _expect_error(
            lambda changed_facts=changed_facts: _finalize(
                binding_factory,
                changed_facts,
                binding_receipt,
            ),
            error_type,
            code,
        )
        _assert(
            getattr(mismatch_error, "env_id", None) is not None
            and getattr(mismatch_error, "expected", None) is not None
            and getattr(mismatch_error, "actual", None) is not None,
            f"{label} mismatch omits row/value context",
        )
        for context_field in binding_context_fields.get(label, ()):
            _assert(
                getattr(mismatch_error, context_field, None) is not None,
                f"{label} mismatch omits {context_field}",
            )
        _assert(
            _snapshot(binding_ledger) == before,
            f"{label} mismatch claimed receipt",
        )
        binding_evidence[label] = code

    _expect_error(
        lambda: CONTRACT.TransitionConsumeLedger(
            authority_stamp=_producer_stamp(),
        ),
        CONTRACT.LifecycleAuthorityMismatchError,
        "authority_stamp",
    )
    _expect_error(
        lambda: CONTRACT.LifecycleTransitionResultFactory(
            ledger=object(),
            authority_stamp=_authority_stamp(),
        ),
        CONTRACT.LifecycleAuthorityMismatchError,
        "ledger_type",
    )
    _expect_error(
        lambda: CONTRACT.LifecycleTransitionResultFactory(
            ledger=_ledger(),
            authority_stamp=_producer_stamp(),
        ),
        CONTRACT.LifecycleAuthorityMismatchError,
        "authority_stamp",
    )

    facts, ledger, receipt, factory = _consumed_context()
    bad_inputs = _valid_result_inputs(facts)
    bad_inputs["completed_tasks"] = ~bad_inputs["completed_tasks"]
    before = _snapshot(ledger)
    _expect_error(
        lambda: _finalize(factory, facts, receipt, bad_inputs),
        CONTRACT.TransitionSchemaError,
        "completed_derivation",
    )
    _assert(
        _snapshot(ledger) == before,
        "invalid finalize burned the receipt",
    )
    _finalize(factory, facts, receipt)
    _expect_error(
        lambda: _finalize(factory, facts, receipt),
        CONTRACT.DuplicateTransitionConsumeError,
        "duplicate_finalization",
    )
    return {
        "valid_factory_finalization": True,
        "direct_constructor_blocked": True,
        "uninitialized_forgery_rejected": True,
        "missing_receipt_rejected": True,
        "different_ledger_receipt_rejected": True,
        "facts_receipt_binding": binding_evidence,
        "producer_authority_types_not_interchangeable": True,
        "invalid_finalize_retry_succeeds": True,
        "successful_receipt_reuse_rejected": True,
    }


def _fresh_factory_failure(
    mutate: Callable[[dict[str, object]], None],
    exception_type: type[BaseException],
    failure_code: str,
) -> None:
    facts, ledger, receipt, factory = _consumed_context()
    inputs = _valid_result_inputs(facts)
    mutate(inputs)
    before = _snapshot(ledger)
    _expect_error(
        lambda: _finalize(factory, facts, receipt, inputs),
        exception_type,
        failure_code,
    )
    _assert(
        _snapshot(ledger) == before,
        f"{failure_code} changed ledger finalization state",
    )


def test_result_schema_and_derived_invariants() -> dict[str, Any]:
    completion_values = _valid_facts_values()
    completion_values["completion_signals"][0, 0, 0] = True
    facts, ledger, receipt, factory = _consumed_context(completion_values)
    result = _finalize(factory, facts, receipt)
    _assert(
        torch.equal(
            result.completed_tasks,
            facts.completion_signals.any(dim=1),
        ),
        "completed task derivation changed",
    )
    _assert(result.updated_ownership[0, 0].item() == -1, "completed owner kept")
    _assert(
        result.updated_task_state[0, 0].item() == 17,
        "completed state encoding changed",
    )

    def bad_completed(inputs: dict[str, object]) -> None:
        inputs["completed_tasks"][0, 0] = True

    _fresh_factory_failure(
        bad_completed,
        CONTRACT.TransitionSchemaError,
        "completed_derivation",
    )

    def completed_owner(inputs: dict[str, object]) -> None:
        inputs["updated_ownership"][0, 0] = 0

    facts_with_completion = completion_values
    facts, ledger, receipt, factory = _consumed_context(facts_with_completion)
    inputs = _valid_result_inputs(facts)
    completed_owner(inputs)
    before = _snapshot(ledger)
    _expect_error(
        lambda: _finalize(factory, facts, receipt, inputs),
        CONTRACT.TransitionSchemaError,
        "completed_task_ownership",
    )
    _assert(
        _snapshot(ledger) == before,
        "completed ownership failure burned the receipt",
    )
    _finalize(factory, facts, receipt, _valid_result_inputs(facts))

    facts, ledger, receipt, factory = _consumed_context(facts_with_completion)
    inputs = _valid_result_inputs(facts)
    inputs["updated_task_state"][0, 0] = 16
    before = _snapshot(ledger)
    _expect_error(
        lambda: _finalize(factory, facts, receipt, inputs),
        CONTRACT.TransitionSchemaError,
        "completed_task_state",
    )
    _assert(
        _snapshot(ledger) == before,
        "completed state failure burned the receipt",
    )
    _finalize(factory, facts, receipt, _valid_result_inputs(facts))

    def failed_pair_conflict(inputs: dict[str, object]) -> None:
        inputs["prior_failed_pairs"][0, 0, 0] = True
        inputs["new_failed_pairs"][0, 0, 0] = True
        inputs["updated_failed_pairs"][0, 0, 0] = True

    _fresh_factory_failure(
        failed_pair_conflict,
        CONTRACT.TransitionSchemaError,
        "new_failed_pair_conflict",
    )

    def updated_failed_wrong(inputs: dict[str, object]) -> None:
        inputs["new_failed_pairs"][0, 0, 0] = True

    _fresh_factory_failure(
        updated_failed_wrong,
        CONTRACT.TransitionSchemaError,
        "updated_failed_pairs_consistency",
    )

    def ownership_low(inputs: dict[str, object]) -> None:
        inputs["updated_ownership"][0, 0] = -2

    _fresh_factory_failure(
        ownership_low,
        CONTRACT.TransitionSchemaError,
        "ownership_range",
    )

    def ownership_high(inputs: dict[str, object]) -> None:
        inputs["updated_ownership"][0, 0] = 3

    _fresh_factory_failure(
        ownership_high,
        CONTRACT.TransitionSchemaError,
        "ownership_range",
    )

    for invalid_reason in (-1, 4):
        def bad_reason(
            inputs: dict[str, object],
            invalid_reason: int = invalid_reason,
        ) -> None:
            inputs["termination_reason"][0] = invalid_reason

        _fresh_factory_failure(
            bad_reason,
            CONTRACT.TransitionSchemaError,
            "termination_reason",
        )

    def mutable_events(inputs: dict[str, object]) -> None:
        inputs["lifecycle_events"] = []

    _fresh_factory_failure(
        mutable_events,
        CONTRACT.TransitionSchemaError,
        "lifecycle_events_type",
    )

    event_contract = _load_event_contract()

    def unknown_event(inputs: dict[str, object]) -> None:
        inputs["lifecycle_events"] = (object(),)

    _fresh_factory_failure(
        unknown_event,
        CONTRACT.TransitionSchemaError,
        "lifecycle_events_invalid",
    )

    _assert(
        event_contract.LifecycleAuthorityId
        is CONTRACT.LifecycleAuthorityId,
        "event contract duplicated LifecycleAuthorityId",
    )
    facts, ledger, receipt, factory = _consumed_context()
    typed_event = _lifecycle_event(facts)
    typed_inputs = _valid_result_inputs(facts)
    typed_inputs["lifecycle_events"] = (typed_event,)
    typed_result = _finalize(factory, facts, receipt, typed_inputs)
    _assert(
        typed_result.lifecycle_events == (typed_event,),
        "result did not retain the finalized typed lifecycle event",
    )

    facts, ledger, receipt, factory = _consumed_context()
    stale_event_inputs = _valid_result_inputs(facts)
    stale_event_inputs["lifecycle_events"] = (
        _lifecycle_event(facts, transition_delta=1),
    )
    before = _snapshot(ledger)
    _expect_error(
        lambda: _finalize(
            factory,
            facts,
            receipt,
            stale_event_inputs,
        ),
        CONTRACT.TransitionGenerationError,
        "lifecycle_event_transition",
    )
    _assert(
        _snapshot(ledger) == before,
        "event generation mismatch burned the receipt",
    )

    opportunity = event_contract.AssignmentOpportunityRecord(
        schema_version=(
            event_contract.ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION
        ),
        opportunity_id=(101, 7, 40, 1, 0),
        opportunity_type=(
            event_contract.AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE
        ),
        producer_id=(
            event_contract.AssignmentOpportunityProducerId.RETRY_SCHEDULER_V1
        ),
        env_id=101,
        episode_generation=7,
        transition_generation=40,
        assignment_tick_generation=1,
        ordinal=0,
        robot_id=0,
        retry_generation=1,
        trigger_eligible=True,
    )
    facts, ledger, receipt, factory = _consumed_context()
    opportunity_inputs = _valid_result_inputs(facts)
    opportunity_inputs["lifecycle_events"] = (opportunity,)
    _expect_error(
        lambda: _finalize(
            factory,
            facts,
            receipt,
            opportunity_inputs,
        ),
        CONTRACT.TransitionSchemaError,
        "lifecycle_events_invalid",
    )

    diagnostic = event_contract.ResolverDiagnosticRecord(
        schema_version=(
            event_contract.RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION
        ),
        diagnostic_id=(101, 7, 40, 1, 0),
        diagnostic_type=(
            event_contract.ResolverDiagnosticType.COMPONENT_REJECTED
        ),
        producer_id=(
            event_contract.ResolverDiagnosticProducerId
            .RESOLVER_DIAGNOSTIC_PRODUCER_V1
        ),
        env_id=101,
        episode_generation=7,
        transition_generation=40,
        assignment_tick_generation=1,
        ordinal=0,
        component_id="component-0",
        trigger_eligible=False,
        payload=event_contract.ResolverComponentRejectedPayload(
            rejection_reason="contention_loss",
            policy_caused=True,
            penalty_eligible=True,
            member_robot_ids=(0,),
            member_task_ids=(0,),
        ),
    )
    facts, ledger, receipt, factory = _consumed_context()
    diagnostic_inputs = _valid_result_inputs(facts)
    diagnostic_inputs["lifecycle_events"] = (diagnostic,)
    _expect_error(
        lambda: _finalize(
            factory,
            facts,
            receipt,
            diagnostic_inputs,
        ),
        CONTRACT.TransitionSchemaError,
        "lifecycle_events_invalid",
    )

    def bool_encoding(inputs: dict[str, object]) -> None:
        inputs["task_completed_state_encoding"] = True

    _fresh_factory_failure(
        bool_encoding,
        CONTRACT.TransitionSchemaError,
        "completed_state_encoding",
    )

    shape_fields = []
    for name, _, _ in RESULT_INPUT_SPECS:
        def wrong_shape(
            inputs: dict[str, object],
            name: str = name,
        ) -> None:
            inputs[name] = inputs[name].unsqueeze(0)

        _fresh_factory_failure(
            wrong_shape,
            CONTRACT.TransitionSchemaError,
            "shape",
        )
        shape_fields.append(name)

    dtype_fields = []
    for name, _, dtype in RESULT_INPUT_SPECS:
        def wrong_dtype(
            inputs: dict[str, object],
            name: str = name,
            dtype: torch.dtype = dtype,
        ) -> None:
            target = torch.int64 if dtype is torch.bool else torch.int32
            inputs[name] = inputs[name].to(dtype=target)

        _fresh_factory_failure(
            wrong_dtype,
            CONTRACT.TransitionSchemaError,
            "dtype",
        )
        dtype_fields.append(name)

    def wrong_device(inputs: dict[str, object]) -> None:
        inputs["released_tasks"] = torch.zeros(
            tuple(inputs["released_tasks"].shape),
            dtype=torch.bool,
            device="meta",
        )

    _fresh_factory_failure(
        wrong_device,
        CONTRACT.TransitionSchemaError,
        "device",
    )

    reason_values = _valid_facts_values(4, 2, 3)
    facts, ledger, receipt, factory = _consumed_context(reason_values)
    inputs = _valid_result_inputs(facts)
    inputs["termination_reason"] = torch.tensor(
        [0, 1, 2, 3],
        dtype=torch.int64,
    )
    inputs["released_tasks"][0, 0] = True
    inputs["new_team_infeasible_tasks"][1, 1] = True
    valid = _finalize(factory, facts, receipt, inputs)
    valid.validate_finalized()
    mapping = valid.to_mapping()
    _assert(type(mapping) is MappingProxyType, "result mapping is mutable")
    _assert(tuple(mapping) == RESULT_FIELDS, "result mapping order changed")
    for name, symbols, dtype in RESULT_TENSOR_SPECS:
        value = getattr(valid, name)
        _assert(value.dtype is dtype, f"result {name} dtype changed")
        _assert(
            tuple(value.shape)
            == _shape(
                symbols,
                num_envs=4,
                num_robots=2,
                num_tasks=3,
            ),
            f"result {name} shape changed",
        )
    return {
        "completion_derivation": True,
        "completed_ownership_and_state": True,
        "failed_pair_consistency": "updated == prior | new",
        "termination_domain": [0, 1, 2, 3],
        "lifecycle_events": (
            "empty or canonical typed LifecycleEventRecord tuple"
        ),
        "opportunity_and_resolver_diagnostic_rejected": True,
        "shape_fields_rejected": shape_fields,
        "dtype_fields_rejected": dtype_fields,
        "team_infeasible_not_derived_in_a2": True,
        "result_mapping_order_exact": True,
    }


def test_alias_isolation_and_mutation_detection() -> dict[str, Any]:
    values = _valid_facts_values()
    source_env = values["env_id"]
    expected_env = source_env.clone()
    facts = _facts(values)
    source_env.add_(500)
    _assert(
        torch.equal(facts.env_id, expected_env),
        "facts retained ingress alias",
    )
    accessor = facts.env_id
    accessor.add_(500)
    _assert(
        torch.equal(facts.env_id, expected_env),
        "facts accessor aliases backing",
    )
    mapped = facts.to_mapping()["env_id"]
    mapped.add_(500)
    _assert(
        torch.equal(facts.env_id, expected_env),
        "facts mapping aliases backing",
    )
    _assert_frozen(facts, "schema_version", "changed")

    corrupt_facts = _facts(_valid_facts_values())
    corrupt_ledger = _ledger()
    before = _snapshot(corrupt_ledger)
    _private_corrupt_tensor(corrupt_facts, "env_id")
    _expect_error(
        lambda: corrupt_facts.env_id,
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    _expect_error(
        lambda: _consume(corrupt_ledger, corrupt_facts),
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    _assert(
        _snapshot(corrupt_ledger) == before,
        "corrupt facts changed ledger",
    )

    facts, ledger, receipt, factory = _consumed_context()
    original_receipt_env = receipt.env_id
    receipt_clone = receipt.env_id
    receipt_clone.add_(7)
    _assert(
        torch.equal(receipt.env_id, original_receipt_env),
        "receipt accessor aliases backing",
    )
    _private_corrupt_tensor(receipt, "env_id")
    _expect_error(
        receipt.to_mapping,
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    _expect_error(
        lambda: _finalize(factory, facts, receipt),
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    _assert(
        _snapshot(ledger)["finalized_receipt_count"] == 0,
        "corrupt receipt claimed finalization",
    )

    facts, ledger, receipt, factory = _consumed_context()
    inputs = _valid_result_inputs(facts)
    source_released = inputs["released_tasks"]
    result = _finalize(factory, facts, receipt, inputs)
    expected_released = result.released_tasks
    source_released.logical_not_()
    _assert(
        torch.equal(result.released_tasks, expected_released),
        "result retained derived-input alias",
    )
    result_accessor = result.released_tasks
    result_accessor.logical_not_()
    _assert(
        torch.equal(result.released_tasks, expected_released),
        "result accessor aliases backing",
    )
    result_mapping_tensor = result.to_mapping()["released_tasks"]
    result_mapping_tensor.logical_not_()
    _assert(
        torch.equal(result.released_tasks, expected_released),
        "result mapping aliases backing",
    )
    _assert_frozen(result, "schema_version", "changed")

    facts, ledger, receipt, factory = _consumed_context()
    corrupt_result = _finalize(factory, facts, receipt)
    _private_corrupt_tensor(corrupt_result, "updated_task_state")
    _expect_error(
        lambda: corrupt_result.updated_task_state,
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    _expect_error(
        corrupt_result.to_mapping,
        CONTRACT.FinalizedSnapshotMutationError,
        "snapshot_mutation",
    )
    return {
        "facts_ingress_alias_isolated": True,
        "facts_accessor_and_mapping_cloned": True,
        "receipt_accessor_cloned": True,
        "result_ingress_alias_isolated": True,
        "result_accessor_and_mapping_cloned": True,
        "field_rebind_blocked": True,
        "facts_corruption_detected_before_consume": True,
        "receipt_corruption_detected_before_finalize": True,
        "result_corruption_detected_before_read_or_mapping": True,
        "private_corruption_hook_is_implementation_regression_only": True,
    }


def _canonical_side_effect_child_source() -> str:
    return r'''
import contextlib
import hashlib
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import MappingProxyType

import torch

canonical_name = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_lifecycle_transition_contract"
)
bare_name = "assignment_lifecycle_transition_contract"
module_path = Path(sys.argv[1]).resolve()
profile_path = Path(sys.argv[2]).resolve()
temporary_root = Path.cwd().resolve()

def source_keys():
    result = []
    for key, candidate in tuple(sys.modules.items()):
        candidate_path = getattr(candidate, "__file__", None)
        if not isinstance(candidate_path, str):
            continue
        try:
            if Path(candidate_path).resolve() == module_path:
                result.append(key)
        except (OSError, RuntimeError):
            pass
    return tuple(sorted(result))

def temp_snapshot():
    return tuple(sorted(
        (
            str(path.relative_to(temporary_root)),
            path.is_dir(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in temporary_root.rglob("*")
    ))

random_before = random.getstate()
torch_rng_before = torch.random.get_rng_state().clone()
numpy_before = "numpy" in sys.modules
environment_before = dict(os.environ)
cwd_before = os.getcwd()
sys_path_before = tuple(sys.path)
logger_names_before = tuple(sorted(logging.Logger.manager.loggerDict))
root_handlers_before = tuple(id(item) for item in logging.getLogger().handlers)
modules_before = set(sys.modules)
temp_before = temp_snapshot()
contract_stat_before = (
    module_path.stat().st_size,
    module_path.stat().st_mtime_ns,
)
profile_hash_before = hashlib.sha256(profile_path.read_bytes()).hexdigest()
stdout = io.StringIO()
stderr = io.StringIO()

with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    spec = importlib.util.spec_from_file_location(canonical_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create canonical module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[canonical_name] = module
    spec.loader.exec_module(module)
    producer = module.ExecutionFactsProducerStamp(
        producer_id=module.ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1,
        producer_contract_version=module.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
    )
    authority = module.LifecycleAuthorityStamp(
        authority_id=module.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1,
        authority_contract_version=module.LIFECYCLE_AUTHORITY_CONTRACT_VERSION,
    )
    values = {
        "schema_version": module.EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        "producer_contract_version": module.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION,
        "producer_id": producer.producer_id,
        "env_id": torch.tensor([5], dtype=torch.int64),
        "episode_generation": torch.tensor([2], dtype=torch.int64),
        "transition_generation": torch.tensor([9], dtype=torch.int64),
        "physical_terminated": torch.zeros((1,), dtype=torch.bool),
        "physical_truncated": torch.zeros((1,), dtype=torch.bool),
        "time_limit_reached": torch.zeros((1,), dtype=torch.bool),
        "bad_transition": torch.zeros((1,), dtype=torch.bool),
        "completion_signals": torch.zeros((1, 1, 1), dtype=torch.bool),
        "terminal_pair_failure_signals": torch.zeros((1, 1, 1), dtype=torch.bool),
        "forced_release_signals": torch.zeros((1, 1, 1), dtype=torch.bool),
        "robot_unavailable_signals": torch.zeros((1, 1), dtype=torch.bool),
        "robot_recovered_signals": torch.zeros((1, 1), dtype=torch.bool),
        "coverage_before_reset": torch.zeros((1, 1), dtype=torch.bool),
        "task_state_before_transition": torch.zeros((1, 1), dtype=torch.int64),
        "robot_state_before_transition": torch.zeros((1, 1), dtype=torch.int64),
        "ownership_before_transition": torch.zeros((1, 1), dtype=torch.int64),
        "consume_once_token": torch.tensor([100], dtype=torch.int64),
    }
    facts = module.ExecutionTransitionFacts.from_mapping(
        values,
        producer_stamp=producer,
        device=torch.device("cpu"),
    )
    ledger = module.TransitionConsumeLedger(authority_stamp=authority)
    receipt = ledger.consume(
        facts,
        producer_stamp=producer,
        expected_generations=(
            module.TransitionGenerationExpectation(
                env_id=5,
                episode_generation=2,
                transition_generation=9,
            ),
        ),
    )
    factory = module.LifecycleTransitionResultFactory(
        ledger=ledger,
        authority_stamp=authority,
    )
    result = factory.finalize(
        facts=facts,
        receipt=receipt,
        completed_tasks=torch.zeros((1, 1), dtype=torch.bool),
        released_tasks=torch.zeros((1, 1), dtype=torch.bool),
        new_failed_pairs=torch.zeros((1, 1, 1), dtype=torch.bool),
        prior_failed_pairs=torch.zeros((1, 1, 1), dtype=torch.bool),
        updated_failed_pairs=torch.zeros((1, 1, 1), dtype=torch.bool),
        new_team_infeasible_tasks=torch.zeros((1, 1), dtype=torch.bool),
        updated_task_state=torch.zeros((1, 1), dtype=torch.int64),
        updated_robot_state=torch.zeros((1, 1), dtype=torch.int64),
        updated_ownership=torch.zeros((1, 1), dtype=torch.int64),
        termination_reason=torch.zeros((1,), dtype=torch.int64),
        task_completed_state_encoding=17,
        lifecycle_events=(),
    )
    facts.validate_integrity()
    receipt.validate_integrity()
    result.validate_finalized()
    descriptor = module.get_assignment_lifecycle_transition_schema_descriptor()
    if not isinstance(descriptor, MappingProxyType):
        raise AssertionError("descriptor is not read-only")

new_modules = set(sys.modules) - modules_before
blocked_prefixes = ("isaaclab", "omni", "pxr", "harl")
blocked_names = (
    "assignment_profile_contract",
    "assignment_harl_wrapper",
    "assignment_lifecycle_resolver",
    "assignment_checkpoint_contract",
)
blocked_modules = sorted(
    name
    for name in new_modules
    if name != canonical_name
    and (
        name.startswith(blocked_prefixes)
        or any(blocked in name for blocked in blocked_names)
    )
)
print(json.dumps({
    "module_name": module.__name__,
    "source_keys": source_keys(),
    "bare_key_present": bare_name in sys.modules,
    "strict_isinstance": isinstance(facts, module.ExecutionTransitionFacts),
    "random_unchanged": random.getstate() == random_before,
    "torch_rng_unchanged": torch.equal(
        torch.random.get_rng_state(),
        torch_rng_before,
    ),
    "numpy_before": numpy_before,
    "numpy_after": "numpy" in sys.modules,
    "environment_unchanged": dict(os.environ) == environment_before,
    "cwd_unchanged": os.getcwd() == cwd_before,
    "sys_path_unchanged": tuple(sys.path) == sys_path_before,
    "logger_names_unchanged": (
        tuple(sorted(logging.Logger.manager.loggerDict)) == logger_names_before
    ),
    "root_handlers_unchanged": (
        tuple(id(item) for item in logging.getLogger().handlers)
        == root_handlers_before
    ),
    "temp_files_unchanged": temp_snapshot() == temp_before,
    "contract_source_unchanged": (
        module_path.stat().st_size,
        module_path.stat().st_mtime_ns,
    ) == contract_stat_before,
    "profile_source_unchanged": (
        hashlib.sha256(profile_path.read_bytes()).hexdigest()
        == profile_hash_before
    ),
    "profile_module_absent": not any(
        "assignment_profile_contract" in name for name in sys.modules
    ),
    "blocked_modules": blocked_modules,
    "stdout": stdout.getvalue(),
    "stderr": stderr.getvalue(),
    "receipt_id": receipt.authority_receipt_id.tolist(),
    "result_valid": result.schema_version
        == module.LIFECYCLE_TRANSITION_RESULT_SCHEMA_VERSION,
}, sort_keys=True))
'''


def test_clean_child_side_effect_boundary() -> dict[str, Any]:
    child_source = _canonical_side_effect_child_source()
    with tempfile.TemporaryDirectory() as temporary:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                child_source,
                str(CONTRACT_PATH.resolve()),
                str(PROFILE_CONTRACT_PATH.resolve()),
            ],
            cwd=temporary,
            check=False,
            capture_output=True,
            text=True,
        )
    _assert(
        completed.returncode == 0,
        f"canonical child failed: {completed.stdout!r} {completed.stderr!r}",
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(len(lines) == 1, "canonical child emitted non-JSON stdout")
    evidence = json.loads(lines[0])
    _assert(evidence["module_name"] == CANONICAL_MODULE, "child module key changed")
    _assert(
        evidence["source_keys"] == [CANONICAL_MODULE],
        "child source has multiple module keys",
    )
    _assert(not evidence["bare_key_present"], "child registered bare key")
    for key in (
        "strict_isinstance",
        "random_unchanged",
        "torch_rng_unchanged",
        "environment_unchanged",
        "cwd_unchanged",
        "sys_path_unchanged",
        "logger_names_unchanged",
        "root_handlers_unchanged",
        "temp_files_unchanged",
        "contract_source_unchanged",
        "profile_source_unchanged",
        "profile_module_absent",
        "result_valid",
    ):
        _assert(evidence[key], f"clean-child evidence failed: {key}")
    if not evidence["numpy_before"]:
        _assert(
            not evidence["numpy_after"],
            "contract imported NumPy when it was initially absent",
        )
    _assert(
        evidence["blocked_modules"] == [],
        f"child loaded forbidden modules: {evidence['blocked_modules']}",
    )
    _assert(not evidence["stdout"], "contract operations wrote stdout")
    _assert(not evidence["stderr"], "contract operations wrote stderr")
    return {
        "canonical_source_key_only": True,
        "python_rng_unchanged": True,
        "torch_rng_unchanged": True,
        "numpy_absence_preserved_when_applicable": True,
        "cwd_env_sys_path_logger_unchanged": True,
        "files_unchanged": True,
        "stdout_stderr_empty": True,
        "forbidden_runtime_modules_absent": True,
        "a1_profile_registry_not_imported_or_modified": True,
        "receipt_id": evidence["receipt_id"],
    }


TESTS = (
    test_canonical_module_identity_and_source_guard,
    test_versions_stamps_exceptions_and_schema_descriptor,
    test_v2_state_enums_and_failure_termination_projection,
    test_execution_facts_valid_shapes_and_scale,
    test_execution_facts_schema_failure_matrix,
    test_pair_attribution_and_atomic_rejection_matrix,
    test_generation_expectation_and_ledger_failure_matrix,
    test_batch_atomicity_receipt_identity_and_rng,
    test_result_factory_binding_and_authority_matrix,
    test_result_schema_and_derived_invariants,
    test_alias_isolation_and_mutation_detection,
    test_clean_child_side_effect_boundary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, str]] = []
    evidence: dict[str, Any] = {}
    for test in TESTS:
        try:
            evidence[test.__name__] = test()
        except Exception as exc:  # noqa: BLE001 - standalone pure regression runner.
            results.append(
                {
                    "name": test.__name__,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"name": test.__name__, "status": "passed"})
    failed = [result for result in results if result["status"] == "failed"]
    payload = {
        "status": "failed" if failed else "passed",
        "num_tests": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "tests": results,
        "evidence": evidence,
        "runtime_boundary": (
            "pure/schema Phase A2 evidence only; no normal isaaclab_tasks "
            "package import, AppLauncher, Isaac environment, assignment "
            "wrapper/resolver, checkpoint I/O, training, playback, diagnosis, "
            "or evaluation"
        ),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            suffix = (
                f": {result['error']}" if result["status"] == "failed" else ""
            )
            print(f"{result['status'].upper()} {result['name']}{suffix}")
        print(
            f"{'FAIL' if failed else 'PASS'} "
            f"{payload['passed']}/{payload['num_tests']} tests"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
