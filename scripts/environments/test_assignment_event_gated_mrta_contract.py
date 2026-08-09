"""Pure regressions for Phase A3 event and local-MRTA DTO contracts.

The suite creates a namespace-only canonical import harness and never imports
the normal Isaac Lab task-discovery package.  It does not construct an Isaac
environment, scheduler, wrapper, actor, resolver runtime, reward path,
checkpoint, logger sink, training loop, playback, evaluation, or diagnosis
entrypoint.  All tensors are deterministic literals/aranges.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
from dataclasses import FrozenInstanceError
import hashlib
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
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
TRANSITION_PATH = SCAN_SOURCE / "assignment_lifecycle_transition_contract.py"
EVENT_PATH = SCAN_SOURCE / "assignment_event_contract.py"
MRTA_PATH = SCAN_SOURCE / "assignment_mrta_contract.py"

PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
TRANSITION_KEY = f"{PACKAGE}.assignment_lifecycle_transition_contract"
EVENT_KEY = f"{PACKAGE}.assignment_event_contract"
MRTA_KEY = f"{PACKAGE}.assignment_mrta_contract"
CPU = torch.device("cpu")

MRTA_DESCRIPTOR_VERSION = "assignment_mrta_contract_v2"
EVENT_DESCRIPTOR_VERSION = "assignment_event_contract_v2"
ACTION_CONTRACT_KEYS = (
    "contract_version",
    "num_agents",
    "action_dimension",
    "target_action_id_domain",
    "noop_raw_id",
    "noop_decoded_value",
    "available_action_order",
    "decision_valid_mask_contract_version",
    "proposal_mask_contract_version",
    "cross_section_invariants",
)
LOCAL_CANDIDATE_KEYS = (
    "projection_version",
    "seed_sources",
    "seed_robot_mask_equation",
    "trigger_record_robot_rule",
    "forbidden_trigger_records",
    "candidate_prefilter_order",
    "candidate_eligibility_equation",
    "top_k_sort_order",
    "occupied_task_candidate_rule",
    "current_task_retention_rule",
    "owner_expansion_rounds",
    "owner_expansion_equation",
    "second_layer_owner_recursion",
    "outside_set_owner_preemption_rule",
    "overlap_identity",
    "overlap_merge_rule",
    "post_merge_recomputation_order",
    "post_merge_owner_expansion",
    "global_robot_identity",
    "global_task_identity",
    "local_observation_repacking",
    "overflow_behavior",
    "request_result_association_key",
    "unresolved_parameters",
)
COST_PATH_KEYS = (
    "projection_version",
    "cost_unit",
    "tensor_shapes",
    "tensor_dtypes",
    "cost_generation_key",
    "refresh_rule",
    "snapshot_consistency_rule",
    "navigation_cost_semantics",
    "alignment_cost_semantics",
    "nominal_cost_equation",
    "current_owner_navigation_rule",
    "current_owner_alignment_rule",
    "nonowner_cost_rule",
    "alignment_fallback_rule",
    "unresolved_parameters",
    "path_valid_authority",
    "valid_pair_rule",
    "invalid_path_encoding",
    "finite_invalid_sentinel_allowed",
    "top_k_penalty_rule",
    "pair_gate_cost_source",
    "component_penalty_scope",
)
COMPONENT_KEYS = (
    "projection_version",
    "baseline_a0_identity",
    "component_scope",
    "proposal_source",
    "contention_order",
    "contention_loser_rule",
    "component_closure_rule",
    "whole_component_outcome",
    "partial_policy_acceptance_rule",
    "covered_continue_override_rule",
    "assigned_unfinished_count_equation",
    "assigned_count_gate",
    "active_preemption_definition",
    "pair_improvement_equations",
    "pair_gate_conjunction",
    "baseline_cost_equation",
    "staged_cost_equation",
    "owner_change_count_equation",
    "count_increase_rule",
    "count_equal_improvement_equations",
    "count_decrease_rule",
    "canonical_rejection_order",
    "nonpolicy_rejection_reasons",
    "policy_penalty_attribution_rule",
    "penalty_unit_equation",
    "invariant_failure_rule",
    "forbidden_resolver_behaviors",
    "unresolved_parameters",
)
SCHEDULED_OPPORTUNITY_KEYS = (
    "projection_version",
    "unresolved_parameter",
    "counter_source",
    "unit",
    "persistent_unassigned_equation",
    "anchor_initialization_rule",
    "anchor_refresh_rule",
    "due_equation",
    "retry_generation_rule",
    "lifecycle_early_trigger_rule",
    "unavailable_terminal_suppression",
    "output_record_schema",
)
TRIPLE_KEYS = ("name", "owner_phase", "semantic_purpose")
EXPECTED_MRTA_TRIPLES = {
    "top_k_tasks_per_robot": (
        "phase_b_e",
        "maximum_nominal_cost_ranked_tasks_per_local_robot_before_current_task_retention",
    ),
    "local_robot_cap": (
        "phase_b",
        "maximum_robots_in_merged_local_assignment_set",
    ),
    "local_task_cap": (
        "phase_b",
        "maximum_tasks_in_merged_local_assignment_set",
    ),
    "pair_abs_threshold": (
        "phase_b_e",
        "strict_absolute_expected_time_improvement_for_active_preemption",
    ),
    "pair_rel_threshold": (
        "phase_b_e",
        "strict_relative_expected_time_improvement_for_active_preemption",
    ),
    "component_abs_threshold": (
        "phase_b_e",
        "strict_absolute_expected_time_improvement_for_equal_count_component_acceptance",
    ),
    "component_rel_threshold": (
        "phase_b_e",
        "strict_relative_expected_time_improvement_for_equal_count_component_acceptance",
    ),
    "transfer_penalty": (
        "phase_b_e",
        "expected_time_regularizer_per_owner_change_in_equal_count_component_objective",
    ),
    "alignment_time_constant": (
        "phase_b_e",
        "robot_specific_expected_terminal_alignment_time",
    ),
}
MRTA_ROOT_KEYS = (
    "contract_version",
    "observable_immutability_contract_version",
    "unresolved_parameter_spec",
    "enum_order",
    "schemas",
    "nominal_cost_equation",
    "invalid_path_encoding",
    "local_trigger_records",
    "local_trigger_forbidden",
    "owner_expansion_rounds",
    "overflow_behavior",
    "global_task_identity",
    "target_mask_equation",
    "available_action_equation",
    "decision_valid_equation",
    "construction_legality_context",
    "four_mask_equations",
    "proposal_effective_separation",
    "resolver_policy_selection",
    "component_behavior",
    "penalty_unit_equation",
    "action_contract",
    "local_candidate_semantics",
    "cost_path_semantics",
    "component_semantics",
)
EVENT_ROOT_KEYS = (
    "contract_version",
    "record_systems",
    "payload_field_order",
    "placement_rules",
    "record_system_separation",
    "scheduled_assignment_opportunity_semantics",
)
PROJECTION_CANONICAL_SHA256 = {
    "action_contract": (
        "879590e8b2c23866704c4f4a0ab9ae42bd454b1b0d4c9176101338a122c82c5a"
    ),
    "local_candidate_semantics": (
        "721700c8670517535039a44e5e923a7f0f983a66f13a3fd84cb2259b68f8f84e"
    ),
    "cost_path_semantics": (
        "35edcd920df278b81813746391333aed8e00e96ddca22fd85e8740c5b4391177"
    ),
    "component_semantics": (
        "6d0a2fc413557468dfe128ea1af92814217248e87292af1df95b8173b9a8cad2"
    ),
    "scheduled_assignment_opportunity_semantics": (
        "a9a9fac93644dbd0edb00064cdcb791619f13f2ea8a826f24275f63478eaa681"
    ),
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_type: type[BaseException] | tuple[type[BaseException], ...],
    failure_code: str | tuple[str, ...] | None = None,
) -> BaseException:
    try:
        function()
    except exception_type as exc:
        if failure_code is not None:
            expected = (
                (failure_code,)
                if type(failure_code) is str
                else failure_code
            )
            actual = getattr(exc, "failure_code", None)
            _assert(
                actual in expected,
                f"expected failure code {expected!r}, got {actual!r}: {exc}",
            )
        return exc
    except Exception as exc:
        expected_name = (
            exception_type.__name__
            if isinstance(exception_type, type)
            else " | ".join(item.__name__ for item in exception_type)
        )
        raise AssertionError(
            f"expected {expected_name}, got "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    expected_name = (
        exception_type.__name__
        if isinstance(exception_type, type)
        else " | ".join(item.__name__ for item in exception_type)
    )
    raise AssertionError(f"expected {expected_name}")


def _install_namespace() -> None:
    packages = (
        (
            "isaaclab_tasks",
            REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks",
        ),
        (
            "isaaclab_tasks.direct",
            REPO_ROOT
            / "source"
            / "isaaclab_tasks"
            / "isaaclab_tasks"
            / "direct",
        ),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in packages:
        existing = sys.modules.get(name)
        if existing is not None:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_exact(key: str, path: Path) -> ModuleType:
    existing = sys.modules.get(key)
    if existing is not None:
        _assert(
            Path(str(getattr(existing, "__file__", ""))).resolve()
            == path.resolve(),
            f"{key} points to a different source",
        )
        return existing
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot create canonical spec for {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(key, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace()
TRANSITION = _load_exact(TRANSITION_KEY, TRANSITION_PATH)
EVENT = _load_exact(EVENT_KEY, EVENT_PATH)
MRTA = _load_exact(MRTA_KEY, MRTA_PATH)


def _generation(
    num_envs: int,
    *,
    env_start: int = 11,
    episode: int = 7,
    transition: int = 40,
    tick: int = 4,
) -> dict[str, torch.Tensor]:
    return {
        "env_id": torch.arange(
            env_start,
            env_start + num_envs,
            dtype=torch.int64,
        ),
        "episode_generation": torch.full(
            (num_envs,),
            episode,
            dtype=torch.int64,
        ),
        "transition_generation": torch.full(
            (num_envs,),
            transition,
            dtype=torch.int64,
        ),
        "assignment_tick_generation": torch.full(
            (num_envs,),
            tick,
            dtype=torch.int64,
        ),
    }


def _event(
    *,
    env_id: int = 11,
    episode: int = 7,
    transition: int = 40,
    ordinal: int = 0,
    task_id: int = 0,
    robot_id: int = 0,
    token: int = 1000,
) -> Any:
    return EVENT.LifecycleEventRecord(
        schema_version=EVENT.LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
        event_id=(env_id, episode, transition, ordinal),
        causal_source=EVENT.LifecycleCausalSource.EXECUTION_FACTS,
        event_type=EVENT.LifecycleEventType.TASK_COMPLETED,
        env_id=env_id,
        episode_generation=episode,
        transition_generation=transition,
        ordinal=ordinal,
        robot_id=robot_id,
        task_id=task_id,
        trigger_eligible=True,
        facts_consume_token=token,
        authority_id=(
            TRANSITION.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
        ),
        payload=EVENT.TaskLifecycleEventPayload(
            task_id=task_id,
            previous_task_state=1,
            updated_task_state=9,
            cause_robot_id=robot_id,
        ),
    )


def _opportunity(
    *,
    env_id: int = 11,
    episode: int = 7,
    transition: int = 40,
    tick: int = 4,
    ordinal: int = 0,
    robot_id: int = 0,
    opportunity_id: tuple[int, int, int, int, int] | None = None,
    producer_id: Any | None = None,
    retry_generation: int = 3,
) -> Any:
    return EVENT.AssignmentOpportunityRecord(
        schema_version=EVENT.ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION,
        opportunity_id=(
            (env_id, episode, transition, tick, ordinal)
            if opportunity_id is None
            else opportunity_id
        ),
        opportunity_type=(
            EVENT.AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE
        ),
        producer_id=(
            EVENT.AssignmentOpportunityProducerId.RETRY_SCHEDULER_V1
            if producer_id is None
            else producer_id
        ),
        env_id=env_id,
        episode_generation=episode,
        transition_generation=transition,
        assignment_tick_generation=tick,
        ordinal=ordinal,
        robot_id=robot_id,
        retry_generation=retry_generation,
        trigger_eligible=True,
    )


def _diagnostic(
    *,
    env_id: int = 11,
    episode: int = 7,
    transition: int = 40,
    tick: int = 4,
    ordinal: int = 0,
) -> Any:
    return EVENT.ResolverDiagnosticRecord(
        schema_version=EVENT.RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION,
        diagnostic_id=(env_id, episode, transition, tick, ordinal),
        diagnostic_type=EVENT.ResolverDiagnosticType.COMPONENT_ACCEPTED,
        producer_id=(
            EVENT.ResolverDiagnosticProducerId
            .RESOLVER_DIAGNOSTIC_PRODUCER_V1
        ),
        env_id=env_id,
        episode_generation=episode,
        transition_generation=transition,
        assignment_tick_generation=tick,
        ordinal=ordinal,
        component_id="component_0",
        trigger_eligible=False,
        payload=EVENT.ResolverComponentAcceptedPayload(
            member_robot_ids=(0,),
            member_task_ids=(0,),
            transfer_count=0,
        ),
    )


def _spec(name: str, owner: str = "phase_b") -> Any:
    return MRTA.UnresolvedParameterSpec(
        name=name,
        owner_phase=owner,
        semantic_purpose=f"{name}_semantic",
    )


def _nominal_values(
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    *,
    include_invalid: bool = True,
) -> dict[str, object]:
    navigation = torch.arange(
        1,
        num_envs * num_robots * num_tasks + 1,
        dtype=torch.float32,
    ).reshape(num_envs, num_robots, num_tasks)
    alignment = torch.full_like(navigation, 0.25)
    valid = torch.ones_like(navigation, dtype=torch.bool)
    if include_invalid:
        valid[-1, -1, -1] = False
        navigation[-1, -1, -1] = float("nan")
        alignment[-1, -1, -1] = float("nan")
    nominal = navigation + alignment
    return {
        "schema_version": MRTA.NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION,
        "navigation_cost": navigation,
        "alignment_cost": alignment,
        "nominal_cost": nominal,
        "path_valid": valid,
        "cost_unit": "expected_seconds",
        "estimator_version": "synthetic_fixture_v1",
        **_generation(num_envs),
    }


def _nominal_fixture(
    num_envs: int = 2,
    num_robots: int = 3,
    num_tasks: int = 5,
) -> tuple[Any, dict[str, object], str]:
    values = _nominal_values(num_envs, num_robots, num_tasks)
    return (
        MRTA.NominalPairCostResult.from_mapping(values, device=CPU),
        values,
        "navigation_cost",
    )


def _local_request_values(
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    *,
    with_triggers: bool = True,
) -> dict[str, object]:
    generation = _generation(num_envs)
    lifecycle: list[tuple[Any, ...]] = [() for _ in range(num_envs)]
    opportunities: list[tuple[Any, ...]] = [() for _ in range(num_envs)]
    seed = torch.zeros((num_envs, num_robots), dtype=torch.bool)
    if with_triggers:
        lifecycle[0] = (_event(),)
        opportunity_robot = min(1, num_robots - 1)
        opportunities[0] = (_opportunity(robot_id=opportunity_robot),)
        seed[0, 0] = True
        seed[0, opportunity_robot] = True
    return {
        "schema_version": MRTA.LOCAL_SET_REQUEST_SCHEMA_VERSION,
        "seed_robot_mask": seed,
        "needs_assignment_mask": torch.zeros(
            (num_envs, num_robots), dtype=torch.bool
        ),
        "robot_available_mask": torch.ones(
            (num_envs, num_robots), dtype=torch.bool
        ),
        "task_state": torch.zeros(
            (num_envs, num_tasks), dtype=torch.int64
        ),
        "event_updated_ownership": torch.full(
            (num_envs, num_tasks), -1, dtype=torch.int64
        ),
        "lifecycle_event_records": tuple(lifecycle),
        "assignment_opportunities": tuple(opportunities),
        "top_k_spec": _spec("top_k_tasks_per_robot"),
        "robot_cap_spec": _spec("local_robot_cap"),
        "task_cap_spec": _spec("local_task_cap"),
        "owner_expansion_rounds": 1,
        **generation,
    }


def _local_request_fixture() -> tuple[Any, dict[str, object], str]:
    values = _local_request_values(2, 3, 5)
    return (
        MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        values,
        "seed_robot_mask",
    )


def _local_result_values(
    num_envs: int = 2,
    num_robots: int = 3,
    num_tasks: int = 5,
) -> dict[str, object]:
    local_robot = torch.zeros((num_envs, num_robots), dtype=torch.bool)
    local_task = torch.zeros((num_envs, num_tasks), dtype=torch.bool)
    local_robot[:, 0] = True
    local_task[:, 0] = True
    owner_added = torch.zeros_like(local_robot)
    if num_robots > 1:
        local_robot[0, 1] = True
        owner_added[0, 1] = True
    overflowed = torch.zeros((num_envs,), dtype=torch.bool)
    overflowed[-1] = True
    disposition = torch.where(
        overflowed,
        torch.full(
            (num_envs,),
            int(MRTA.LocalSetOverflowDisposition.FAIL_CLOSED_NO_ASSIGNMENT),
            dtype=torch.int64,
        ),
        torch.zeros((num_envs,), dtype=torch.int64),
    )
    return {
        "schema_version": MRTA.LOCAL_SET_RESULT_SCHEMA_VERSION,
        "local_robot_mask": local_robot,
        "local_task_mask": local_task,
        "owner_added_robot_mask": owner_added,
        "overlap_merged": torch.tensor(
            [True] + [False] * (num_envs - 1), dtype=torch.bool
        ),
        "overflowed": overflowed,
        "overflow_disposition": disposition,
        "owner_expansion_rounds_used": torch.tensor(
            [1] + [0] * (num_envs - 1), dtype=torch.int64
        ),
        **_generation(num_envs),
    }


def _local_result_fixture() -> tuple[Any, dict[str, object], str]:
    values = _local_result_values()
    return (
        MRTA.LocalSetResult.from_mapping(values, device=CPU),
        values,
        "local_robot_mask",
    )


def _top_k_values(
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    top_k: int,
) -> dict[str, object]:
    ids = torch.full(
        (num_envs, num_robots, top_k), -1, dtype=torch.int64
    )
    valid = torch.zeros_like(ids, dtype=torch.bool)
    costs = torch.full_like(ids, float("nan"), dtype=torch.float32)
    valid_slots = min(num_tasks, top_k)
    for slot in range(valid_slots):
        ids[:, :, slot] = slot
        valid[:, :, slot] = True
        costs[:, :, slot] = float(slot + 1)
    current = torch.zeros((num_envs, num_robots), dtype=torch.int64)
    retained = torch.ones((num_envs, num_robots), dtype=torch.bool)
    return {
        "schema_version": MRTA.TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION,
        "global_task_ids": ids,
        "candidate_valid": valid,
        "candidate_nominal_cost": costs,
        "current_task_id": current,
        "current_task_retained": retained,
        **_generation(num_envs),
    }


def _top_k_fixture() -> tuple[Any, dict[str, object], str]:
    values = _top_k_values(2, 3, 5, 3)
    return (
        MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=5, device=CPU
        ),
        values,
        "global_task_ids",
    )


def _dvm_values() -> dict[str, object]:
    num_envs, num_robots, num_tasks = 1, 3, 2
    global_valid = torch.ones((num_envs, num_tasks), dtype=torch.bool)
    failed_legal = torch.ones(
        (num_envs, num_robots, num_tasks), dtype=torch.bool
    )
    path_valid = torch.ones_like(failed_legal)
    ownership_legal = torch.ones_like(failed_legal)
    local = torch.tensor(
        [[[True, True], [True, False], [False, False]]],
        dtype=torch.bool,
    )
    robot_available = torch.ones(
        (num_envs, num_robots), dtype=torch.bool
    )
    target = (
        global_valid.unsqueeze(1)
        & failed_legal
        & path_valid
        & local
        & ownership_legal
        & robot_available.unsqueeze(-1)
    )
    noop = torch.zeros((num_envs, num_robots, 1), dtype=torch.bool)
    available = torch.cat((target, noop), dim=-1)
    count = available.sum(dim=-1, keepdim=True, dtype=torch.int64)
    opportunity = torch.tensor(
        [[[True], [True], [False]]], dtype=torch.bool
    )
    dvm = opportunity & robot_available.unsqueeze(-1) & (count >= 2)
    forced = torch.tensor([[[-1], [0], [-1]]], dtype=torch.int64)
    return {
        "schema_version": (
            MRTA.DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION
        ),
        "global_task_valid_mask": global_valid,
        "failed_pair_legal_mask": failed_legal,
        "nominal_path_valid_mask": path_valid,
        "local_topk_or_continue_mask": local,
        "ownership_preemption_legal_mask": ownership_legal,
        "robot_available_mask": robot_available,
        "decision_opportunity_present": opportunity,
        "target_action_mask": target,
        "noop_action_mask": noop,
        "available_actions": available,
        "semantic_legal_action_count": count,
        "decision_valid_mask": dvm,
        "forced_policy_action_id": forced,
        **_generation(num_envs),
    }


def _dvm_context_values() -> dict[str, torch.Tensor]:
    return {
        "current_task_id": torch.tensor(
            [[0, 0, -1]], dtype=torch.int64
        ),
        "executing_mask": torch.tensor(
            [[True, True, False]], dtype=torch.bool
        ),
        "idle_or_needs_assignment_mask": torch.zeros(
            (1, 3), dtype=torch.bool
        ),
    }


def _dvm_from_mapping(
    values: Mapping[str, object],
    *,
    context: Mapping[str, torch.Tensor] | None = None,
    device: torch.device = CPU,
) -> Any:
    construction_context = (
        _dvm_context_values() if context is None else context
    )
    return MRTA.DecisionValidMaskSnapshot.from_mapping(
        values,
        device=device,
        current_task_id=construction_context["current_task_id"],
        executing_mask=construction_context["executing_mask"],
        idle_or_needs_assignment_mask=construction_context[
            "idle_or_needs_assignment_mask"
        ],
    )


def _refresh_dvm_derived(values: dict[str, object]) -> None:
    target = (
        values["global_task_valid_mask"].unsqueeze(1)
        & values["failed_pair_legal_mask"]
        & values["nominal_path_valid_mask"]
        & values["local_topk_or_continue_mask"]
        & values["ownership_preemption_legal_mask"]
        & values["robot_available_mask"].unsqueeze(-1)
    )
    available = torch.cat(
        (target, values["noop_action_mask"]),
        dim=-1,
    )
    count = available.sum(dim=-1, keepdim=True, dtype=torch.int64)
    opportunity = values["decision_opportunity_present"]
    dvm = (
        opportunity
        & values["robot_available_mask"].unsqueeze(-1)
        & (count >= 2)
    )
    forced = torch.full_like(count, -1, dtype=torch.int64)
    for env in range(int(count.shape[0])):
        for robot in range(int(count.shape[1])):
            if (
                bool(opportunity[env, robot, 0].item())
                and not bool(dvm[env, robot, 0].item())
                and int(count[env, robot, 0].item()) == 1
            ):
                forced[env, robot, 0] = int(
                    torch.nonzero(
                        available[env, robot],
                        as_tuple=False,
                    )[0, 0].item()
                )
    values["target_action_mask"] = target
    values["available_actions"] = available
    values["semantic_legal_action_count"] = count
    values["decision_valid_mask"] = dvm
    values["forced_policy_action_id"] = forced


def _dvm_fixture() -> tuple[Any, dict[str, object], str]:
    values = _dvm_values()
    return (
        _dvm_from_mapping(values),
        values,
        "target_action_mask",
    )


def _proposal_values() -> dict[str, object]:
    num_tasks = 2
    historical = torch.tensor(
        [[[True, True, True], [True, False, False], [False, False, False]]],
        dtype=torch.bool,
    )
    return {
        "schema_version": MRTA.PROPOSAL_SNAPSHOT_SCHEMA_VERSION,
        "storage_row_present_mask": torch.tensor(
            [[[True], [True], [False]]], dtype=torch.bool
        ),
        "policy_proposal_present_mask": torch.tensor(
            [[[True], [False], [False]]], dtype=torch.bool
        ),
        "forced_nondecision_mask": torch.tensor(
            [[[False], [True], [False]]], dtype=torch.bool
        ),
        "decision_valid_mask": torch.tensor(
            [[[True], [False], [False]]], dtype=torch.bool
        ),
        "nonterminal_mask": torch.tensor(
            [[[True], [True], [False]]], dtype=torch.bool
        ),
        "stored_action_id": torch.tensor(
            [[[num_tasks], [0], [-1]]], dtype=torch.int64
        ),
        "stored_action_log_prob": torch.tensor(
            [[[-0.4], [0.0], [0.0]]], dtype=torch.float32
        ),
        "stored_action_row_kind": (
            (
                MRTA.StoredActionRowKind.POLICY_PROPOSAL,
                MRTA.StoredActionRowKind.FORCED_NONDECISION,
                MRTA.StoredActionRowKind.NO_ROW,
            ),
        ),
        "proposal_kind": ((MRTA.ProposalKind.NOOP_IDLE, None, None),),
        "proposed_task_id": torch.tensor(
            [[[-1], [-1], [-1]]], dtype=torch.int64
        ),
        "historical_available_actions": historical,
        **_generation(1),
    }


def _proposal_fixture() -> tuple[Any, dict[str, object], str]:
    values = _proposal_values()
    return (
        MRTA.ProposalSnapshot.from_mapping(values, device=CPU),
        values,
        "stored_action_id",
    )


def _component_request_values(
    *,
    second_policy: bool = True,
) -> dict[str, object]:
    policy = torch.tensor([True, second_policy], dtype=torch.bool)
    proposed = torch.tensor([1, 0 if second_policy else -1], dtype=torch.int64)
    kinds = (
        MRTA.ProposalKind.SWITCH,
        MRTA.ProposalKind.SWITCH if second_policy else None,
    )
    return {
        "schema_version": MRTA.TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION,
        "component_id": "component_0",
        "member_robot_mask": torch.tensor([True, True], dtype=torch.bool),
        "member_task_mask": torch.tensor([True, True], dtype=torch.bool),
        "baseline_assignment_a0": torch.tensor([0, 1], dtype=torch.int64),
        "baseline_ownership_a0": torch.tensor([0, 1], dtype=torch.int64),
        "proposed_task_id": proposed,
        "proposal_kind": kinds,
        "policy_proposal_present_mask": policy,
        "task_state": torch.tensor([1, 1], dtype=torch.int64),
        "robot_state": torch.tensor([1, 1], dtype=torch.int64),
        "pair_legal_mask": torch.ones((2, 2), dtype=torch.bool),
        "nominal_cost": torch.tensor(
            [[4.0, 1.0], [1.0, 4.0]], dtype=torch.float32
        ),
        "pair_abs_threshold_spec": _spec("pair_abs_threshold"),
        "pair_rel_threshold_spec": _spec("pair_rel_threshold"),
        "component_abs_threshold_spec": _spec(
            "component_abs_threshold"
        ),
        "component_rel_threshold_spec": _spec(
            "component_rel_threshold"
        ),
        "transfer_penalty_spec": _spec("transfer_penalty"),
        "env_id": torch.tensor([11], dtype=torch.int64),
        "episode_generation": torch.tensor([7], dtype=torch.int64),
        "transition_generation": torch.tensor([40], dtype=torch.int64),
        "assignment_tick_generation": torch.tensor([4], dtype=torch.int64),
    }


def _three_robot_continue_override_request_values() -> dict[str, object]:
    return {
        "schema_version": MRTA.TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION,
        "component_id": "component_three_robot_override",
        "member_robot_mask": torch.tensor(
            [True, True, True], dtype=torch.bool
        ),
        "member_task_mask": torch.tensor([True, True], dtype=torch.bool),
        "baseline_assignment_a0": torch.tensor(
            [0, 1, -1], dtype=torch.int64
        ),
        "baseline_ownership_a0": torch.tensor(
            [0, 1], dtype=torch.int64
        ),
        "proposed_task_id": torch.tensor(
            [1, 1, 0], dtype=torch.int64
        ),
        "proposal_kind": (
            MRTA.ProposalKind.SWITCH,
            MRTA.ProposalKind.CONTINUE,
            MRTA.ProposalKind.CLAIM,
        ),
        "policy_proposal_present_mask": torch.tensor(
            [True, True, True], dtype=torch.bool
        ),
        "task_state": torch.tensor([1, 1], dtype=torch.int64),
        "robot_state": torch.tensor([1, 1, 1], dtype=torch.int64),
        "pair_legal_mask": torch.ones((3, 2), dtype=torch.bool),
        "nominal_cost": torch.tensor(
            [[4.0, 1.0], [2.0, 3.0], [1.0, 4.0]],
            dtype=torch.float32,
        ),
        "pair_abs_threshold_spec": _spec("pair_abs_threshold"),
        "pair_rel_threshold_spec": _spec("pair_rel_threshold"),
        "component_abs_threshold_spec": _spec(
            "component_abs_threshold"
        ),
        "component_rel_threshold_spec": _spec(
            "component_rel_threshold"
        ),
        "transfer_penalty_spec": _spec("transfer_penalty"),
        "env_id": torch.tensor([11], dtype=torch.int64),
        "episode_generation": torch.tensor([7], dtype=torch.int64),
        "transition_generation": torch.tensor([40], dtype=torch.int64),
        "assignment_tick_generation": torch.tensor([4], dtype=torch.int64),
    }


def _component_request_fixture() -> tuple[Any, dict[str, object], str]:
    values = _component_request_values()
    return (
        MRTA.TransferComponentRequest.from_mapping(values, device=CPU),
        values,
        "member_robot_mask",
    )


def _component_result_values(
    *,
    accepted: bool,
) -> dict[str, object]:
    if accepted:
        return {
            "schema_version": MRTA.TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION,
            "component_id": "component_0",
            "accepted": True,
            "rejection_reason": MRTA.ComponentRejectionReason.NONE,
            "all_rejection_reasons": (),
            "proposal_accepted": torch.tensor(
                [True, True], dtype=torch.bool
            ),
            "proposal_accepted_valid": torch.tensor(
                [True, True], dtype=torch.bool
            ),
            "effective_assignment": torch.tensor([1, 0], dtype=torch.int64),
            "effective_ownership": torch.tensor([1, 0], dtype=torch.int64),
            "owner_change_mask": torch.tensor([True, True], dtype=torch.bool),
            "assigned_count_before": 2,
            "assigned_count_after": 2,
            "local_cost_before": 8.0,
            "local_cost_after": 2.0,
            "transfer_count": 2,
            "commit_generation": 5,
            "env_id": torch.tensor([11], dtype=torch.int64),
            "episode_generation": torch.tensor([7], dtype=torch.int64),
            "transition_generation": torch.tensor([40], dtype=torch.int64),
            "assignment_tick_generation": torch.tensor(
                [4], dtype=torch.int64
            ),
        }
    return {
        "schema_version": MRTA.TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION,
        "component_id": "component_0",
        "accepted": False,
        "rejection_reason": (
            MRTA.ComponentRejectionReason.PAIR_IMPROVEMENT_NOT_MET
        ),
        "all_rejection_reasons": (
            MRTA.ComponentRejectionReason.PAIR_IMPROVEMENT_NOT_MET,
            MRTA.ComponentRejectionReason.COMPONENT_IMPROVEMENT_NOT_MET,
        ),
        "proposal_accepted": torch.tensor([False, False], dtype=torch.bool),
        "proposal_accepted_valid": torch.tensor([True, True], dtype=torch.bool),
        "effective_assignment": torch.tensor([0, 1], dtype=torch.int64),
        "effective_ownership": torch.tensor([0, 1], dtype=torch.int64),
        "owner_change_mask": torch.tensor([False, False], dtype=torch.bool),
        "assigned_count_before": 2,
        "assigned_count_after": 2,
        "local_cost_before": 8.0,
        "local_cost_after": 8.0,
        "transfer_count": 0,
        "commit_generation": -1,
        "env_id": torch.tensor([11], dtype=torch.int64),
        "episode_generation": torch.tensor([7], dtype=torch.int64),
        "transition_generation": torch.tensor([40], dtype=torch.int64),
        "assignment_tick_generation": torch.tensor([4], dtype=torch.int64),
    }


def _three_robot_continue_override_result_values() -> dict[str, object]:
    return {
        "schema_version": MRTA.TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION,
        "component_id": "component_three_robot_override",
        "accepted": True,
        "rejection_reason": MRTA.ComponentRejectionReason.NONE,
        "all_rejection_reasons": (),
        "proposal_accepted": torch.tensor(
            [True, False, True], dtype=torch.bool
        ),
        "proposal_accepted_valid": torch.tensor(
            [True, True, True], dtype=torch.bool
        ),
        "effective_assignment": torch.tensor(
            [1, -1, 0], dtype=torch.int64
        ),
        "effective_ownership": torch.tensor([2, 0], dtype=torch.int64),
        "owner_change_mask": torch.tensor(
            [True, True], dtype=torch.bool
        ),
        "assigned_count_before": 2,
        "assigned_count_after": 2,
        "local_cost_before": 8.0,
        "local_cost_after": 2.0,
        "transfer_count": 2,
        "commit_generation": 5,
        "env_id": torch.tensor([11], dtype=torch.int64),
        "episode_generation": torch.tensor([7], dtype=torch.int64),
        "transition_generation": torch.tensor([40], dtype=torch.int64),
        "assignment_tick_generation": torch.tensor([4], dtype=torch.int64),
    }


def _component_result_fixture() -> tuple[Any, dict[str, object], str]:
    request_values = _component_request_values()
    request = MRTA.TransferComponentRequest.from_mapping(
        request_values, device=CPU
    )
    values = _component_result_values(accepted=True)
    return (
        MRTA.TransferComponentResult.from_mapping(
            values, request=request, device=CPU
        ),
        values,
        "effective_assignment",
    )


def _transition_facts_and_result_inputs() -> tuple[Any, Any, Any, dict[str, Any]]:
    producer = TRANSITION.ExecutionFactsProducerStamp(
        producer_id=(
            TRANSITION.ExecutionFactsProducerId
            .ENV_EXECUTION_FACTS_PRODUCER_V1
        ),
        producer_contract_version=(
            TRANSITION.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
        ),
    )
    authority = TRANSITION.LifecycleAuthorityStamp(
        authority_id=(
            TRANSITION.LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1
        ),
        authority_contract_version=(
            TRANSITION.LIFECYCLE_AUTHORITY_CONTRACT_VERSION
        ),
    )
    facts_values = {
        "schema_version": TRANSITION.EXECUTION_TRANSITION_FACTS_SCHEMA_VERSION,
        "producer_contract_version": (
            TRANSITION.EXECUTION_FACTS_PRODUCER_CONTRACT_VERSION
        ),
        "producer_id": producer.producer_id,
        "env_id": torch.tensor([11], dtype=torch.int64),
        "episode_generation": torch.tensor([7], dtype=torch.int64),
        "transition_generation": torch.tensor([40], dtype=torch.int64),
        "physical_terminated": torch.tensor([False], dtype=torch.bool),
        "physical_truncated": torch.tensor([False], dtype=torch.bool),
        "time_limit_reached": torch.tensor([False], dtype=torch.bool),
        "bad_transition": torch.tensor([False], dtype=torch.bool),
        "completion_signals": torch.tensor([[[True]]], dtype=torch.bool),
        "terminal_pair_failure_signals": torch.tensor(
            [[[False]]], dtype=torch.bool
        ),
        "forced_release_signals": torch.tensor(
            [[[False]]], dtype=torch.bool
        ),
        "robot_unavailable_signals": torch.tensor(
            [[False]], dtype=torch.bool
        ),
        "robot_recovered_signals": torch.tensor(
            [[False]], dtype=torch.bool
        ),
        "coverage_before_reset": torch.tensor([[False]], dtype=torch.bool),
        "task_state_before_transition": torch.tensor(
            [[1]], dtype=torch.int64
        ),
        "robot_state_before_transition": torch.tensor(
            [[1]], dtype=torch.int64
        ),
        "ownership_before_transition": torch.tensor(
            [[0]], dtype=torch.int64
        ),
        "consume_once_token": torch.tensor([1000], dtype=torch.int64),
    }
    facts = TRANSITION.ExecutionTransitionFacts.from_mapping(
        facts_values, producer_stamp=producer, device=CPU
    )
    ledger = TRANSITION.TransitionConsumeLedger(authority_stamp=authority)
    receipt = ledger.consume(
        facts,
        producer_stamp=producer,
        expected_generations=(
            TRANSITION.TransitionGenerationExpectation(
                env_id=11,
                episode_generation=7,
                transition_generation=40,
            ),
        ),
    )
    factory = TRANSITION.LifecycleTransitionResultFactory(
        ledger=ledger, authority_stamp=authority
    )
    inputs = {
        "facts": facts,
        "receipt": receipt,
        "completed_tasks": torch.tensor([[True]], dtype=torch.bool),
        "released_tasks": torch.tensor([[False]], dtype=torch.bool),
        "new_failed_pairs": torch.tensor(
            [[[False]]], dtype=torch.bool
        ),
        "prior_failed_pairs": torch.tensor(
            [[[False]]], dtype=torch.bool
        ),
        "updated_failed_pairs": torch.tensor(
            [[[False]]], dtype=torch.bool
        ),
        "new_team_infeasible_tasks": torch.tensor(
            [[False]], dtype=torch.bool
        ),
        "updated_task_state": torch.tensor([[9]], dtype=torch.int64),
        "updated_robot_state": torch.tensor([[1]], dtype=torch.int64),
        "updated_ownership": torch.tensor([[-1]], dtype=torch.int64),
        "termination_reason": torch.tensor(
            [int(TRANSITION.TerminationReason.NONE)], dtype=torch.int64
        ),
        "task_completed_state_encoding": 9,
    }
    return factory, facts, receipt, inputs


def test_canonical_identity_and_enum_order() -> None:
    _assert(TRANSITION.__name__ == TRANSITION_KEY, "wrong transition key")
    _assert(EVENT.__name__ == EVENT_KEY, "wrong event key")
    _assert(MRTA.__name__ == MRTA_KEY, "wrong MRTA key")
    _assert(
        EVENT.LifecycleAuthorityId is TRANSITION.LifecycleAuthorityId,
        "event module duplicated lifecycle authority enum",
    )
    _assert(
        [item.name for item in EVENT.LifecycleEventType]
        == [
            "TASK_COMPLETED",
            "TASK_RELEASED",
            "TERMINAL_PAIR_FAILURE_RECORDED",
            "TASK_BECAME_TEAM_INFEASIBLE",
            "ROBOT_BECAME_UNAVAILABLE",
            "ROBOT_RECOVERED",
            "ROBOT_NEEDS_ASSIGNMENT",
        ],
        "lifecycle event order drifted",
    )
    _assert(
        [item.name for item in EVENT.AssignmentOpportunityType]
        == ["ASSIGNMENT_RETRY_DUE"],
        "opportunity enum drifted",
    )
    _assert(
        [item.name for item in EVENT.ResolverDiagnosticType]
        == [
            "COMPONENT_ACCEPTED",
            "COMPONENT_REJECTED",
            "OWNERSHIP_TRANSFER_COMMITTED",
        ],
        "diagnostic enum drifted",
    )
    _assert(
        [item.name for item in MRTA.ComponentRejectionReason]
        == [
            "NONE",
            "CONTENTION_LOSS",
            "INCOMPLETE_TRANSFER_CHAIN",
            "OWNERSHIP_COORDINATION_INVALID",
            "PREEMPTION_INELIGIBLE",
            "ASSIGNED_UNFINISHED_COUNT_DECREASE",
            "PAIR_IMPROVEMENT_NOT_MET",
            "COMPONENT_IMPROVEMENT_NOT_MET",
            "LOCAL_SET_OVERFLOW_FAIL_CLOSED",
            "POST_SNAPSHOT_SYSTEM_INVALIDATION",
            "TERMINAL_TRANSITION",
        ],
        "component rejection order drifted",
    )
    tree = ast.parse(MRTA_PATH.read_text(encoding="utf-8"))
    class_lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    torch_lines = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        and (
            any(alias.name == "torch" for alias in getattr(node, "names", ()))
            or getattr(node, "module", None) == "torch"
        )
    ]
    guard_line = next(
        node.lineno
        for node in tree.body
        if isinstance(node, ast.If)
        and "__name__" in ast.unparse(node.test)
    )
    _assert(guard_line < min(class_lines), "identity guard follows a class")
    _assert(guard_line < min(torch_lines), "identity guard follows torch import")

    child = (
        "import importlib.util,sys\n"
        f"p={str(MRTA_PATH)!r}\n"
        "before='torch' in sys.modules\n"
        "s=importlib.util.spec_from_file_location('wrong.mrta',p)\n"
        "m=importlib.util.module_from_spec(s)\n"
        "try:\n"
        " s.loader.exec_module(m)\n"
        "except ImportError:\n"
        " assert ('torch' in sys.modules)==before\n"
        "else:\n"
        " raise AssertionError('wrong key loaded')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", child],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _assert(result.returncode == 0, result.stderr)


def test_event_records_and_strict_placement() -> None:
    event = _event()
    opportunity = _opportunity()
    diagnostic = _diagnostic()
    _assert(
        diagnostic.trigger_eligible is False,
        "resolver diagnostic is incorrectly trigger eligible",
    )
    _assert(EVENT.validate_lifecycle_event_records((event,)) == (event,), "event validation failed")
    _assert(
        EVENT.validate_assignment_opportunity_records((opportunity,))
        == (opportunity,),
        "opportunity validation failed",
    )
    _assert(
        EVENT.validate_resolver_diagnostic_records((diagnostic,))
        == (diagnostic,),
        "diagnostic validation failed",
    )
    _assert(
        EVENT.validate_local_trigger_sources((event, opportunity))
        == (event, opportunity),
        "valid local trigger sources rejected",
    )
    _expect_error(
        lambda: EVENT.validate_local_trigger_sources((diagnostic,)),
        EVENT.EventPlacementError,
        "record_placement",
    )
    _expect_error(
        lambda: EVENT.validate_lifecycle_event_records((opportunity,)),
        EVENT.EventPlacementError,
        "record_placement",
    )
    duplicate = _event(ordinal=0)
    _expect_error(
        lambda: EVENT.validate_lifecycle_event_records((event, duplicate)),
        EVENT.EventGenerationError,
        ("record_order", "duplicate_ordinal"),
    )
    event_1 = _event(ordinal=1)
    _expect_error(
        lambda: EVENT.validate_lifecycle_event_records((event_1, event)),
        EVENT.EventGenerationError,
        "record_order",
    )
    _expect_error(
        lambda: EVENT.LifecycleEventRecord(
            schema_version=event.schema_version,
            event_id=event.event_id,
            causal_source=event.causal_source,
            event_type=event.event_type,
            env_id=event.env_id,
            episode_generation=event.episode_generation,
            transition_generation=event.transition_generation,
            ordinal=event.ordinal,
            robot_id=event.robot_id,
            task_id=event.task_id,
            trigger_eligible=event.trigger_eligible,
            facts_consume_token=event.facts_consume_token,
            authority_id=event.authority_id,
            payload={"task_id": 0},
        ),
        EVENT.EventSchemaError,
        "payload_type",
    )
    _expect_error(
        lambda: EVENT.LifecycleEventRecord(
            schema_version=event.schema_version,
            event_id=event.event_id,
            causal_source=event.causal_source,
            event_type=EVENT.LifecycleEventType.TASK_COMPLETED,
            env_id=event.env_id,
            episode_generation=event.episode_generation,
            transition_generation=event.transition_generation,
            ordinal=event.ordinal,
            robot_id=event.robot_id,
            task_id=event.task_id,
            trigger_eligible=event.trigger_eligible,
            facts_consume_token=event.facts_consume_token,
            authority_id=event.authority_id,
            payload=EVENT.RobotLifecycleEventPayload(
                robot_id=event.robot_id,
                previous_robot_state=1,
                updated_robot_state=2,
            ),
        ),
        EVENT.EventSchemaError,
        "payload_type",
    )
    _expect_error(
        lambda: _opportunity(
            opportunity_id=(11, 7, 40, 5, 0),
        ),
        EVENT.EventGenerationError,
        "record_id_binding",
    )
    _expect_error(
        lambda: _opportunity(
            producer_id=(
                EVENT.ResolverDiagnosticProducerId
                .RESOLVER_DIAGNOSTIC_PRODUCER_V1
            ),
        ),
        EVENT.EventAuthorityMismatchError,
        "producer_id",
    )
    _expect_error(
        lambda: _opportunity(tick=-1),
        EVENT.EventSchemaError,
        "integer_range",
    )
    _expect_error(
        lambda: _opportunity(retry_generation=-1),
        EVENT.EventSchemaError,
        "integer_range",
    )
    try:
        event.task_id = 9
    except (FrozenInstanceError, AttributeError, TypeError):
        pass
    else:
        raise AssertionError("lifecycle event record allowed field rebind")
    _assert(
        not hasattr(EVENT.LifecycleEventRecord, "from_mapping"),
        "canonical lifecycle record can be reconstructed from a mapping",
    )
    _assert(
        isinstance(event.to_mapping(), MappingProxyType),
        "event serialization is mutable",
    )


def test_lifecycle_result_typed_event_integration() -> None:
    factory, _, _, inputs = _transition_facts_and_result_inputs()
    opportunity = _opportunity()
    diagnostic = _diagnostic()
    _expect_error(
        lambda: factory.finalize(
            **inputs, lifecycle_events=(opportunity,)
        ),
        TRANSITION.TransitionSchemaError,
        "lifecycle_events_invalid",
    )
    _expect_error(
        lambda: factory.finalize(
            **inputs, lifecycle_events=(diagnostic,)
        ),
        TRANSITION.TransitionSchemaError,
        "lifecycle_events_invalid",
    )
    mismatch_cases = (
        (
            _event(env_id=12),
            TRANSITION.TransitionGenerationError,
            "lifecycle_event_env",
        ),
        (
            _event(episode=8),
            TRANSITION.TransitionGenerationError,
            "lifecycle_event_episode",
        ),
        (
            _event(transition=41),
            TRANSITION.TransitionGenerationError,
            "lifecycle_event_transition",
        ),
        (
            _event(token=1001),
            TRANSITION.TransitionTokenMismatchError,
            "lifecycle_event_token",
        ),
    )
    for mismatched, exception_type, failure_code in mismatch_cases:
        _expect_error(
            lambda mismatched=mismatched: factory.finalize(
                **inputs, lifecycle_events=(mismatched,)
            ),
            exception_type,
            failure_code,
        )
    _expect_error(
        lambda: EVENT.LifecycleEventRecord(
            schema_version=EVENT.LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION,
            event_id=(11, 7, 40, 0),
            causal_source=EVENT.LifecycleCausalSource.EXECUTION_FACTS,
            event_type=EVENT.LifecycleEventType.TASK_COMPLETED,
            env_id=11,
            episode_generation=7,
            transition_generation=40,
            ordinal=0,
            robot_id=0,
            task_id=0,
            trigger_eligible=True,
            facts_consume_token=1000,
            authority_id="lifecycle_authority_v1",
            payload=EVENT.TaskLifecycleEventPayload(0, 1, 9, 0),
        ),
        EVENT.EventAuthorityMismatchError,
        "authority_id",
    )
    event = _event()
    result = factory.finalize(**inputs, lifecycle_events=(event,))
    _assert(result.lifecycle_events == (event,), "typed event not retained")
    _assert(
        type(result.lifecycle_events[0]) is EVENT.LifecycleEventRecord,
        "result event class identity drifted",
    )
    _assert(
        result.lifecycle_events[0].authority_id is result.authority_id,
        "result/event authority identity differs",
    )


def test_nominal_cost_two_scales_and_invalid_paths() -> None:
    for scale in ((1, 1, 1), (2, 3, 5)):
        values = _nominal_values(*scale)
        result = MRTA.NominalPairCostResult.from_mapping(values, device=CPU)
        valid = result.path_valid
        _assert(
            torch.equal(
                result.nominal_cost[valid],
                (result.navigation_cost + result.alignment_cost)[valid],
            ),
            f"nominal sum failed at scale {scale}",
        )
        _assert(
            torch.isnan(result.nominal_cost[~valid]).all().item(),
            f"invalid cost is not NaN at scale {scale}",
        )
    values = _nominal_values(1, 1, 1, include_invalid=False)
    values["navigation_cost"] = torch.zeros(
        (1, 1), dtype=torch.float32
    )
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "shape",
    )
    values = _nominal_values(1, 1, 1, include_invalid=False)
    values["navigation_cost"] = values["navigation_cost"].to(
        dtype=torch.float64
    )
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "dtype",
    )
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(
            _nominal_values(1, 1, 1, include_invalid=False),
            device=torch.device("meta"),
        ),
        MRTA.MrtaSchemaError,
        "device",
    )
    values = _nominal_values(1, 1, 1, include_invalid=False)
    values["episode_generation"][0] = -1
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaGenerationError,
        "generation_nonnegative",
    )
    values = _nominal_values(2, 1, 1, include_invalid=False)
    values["env_id"][1] = values["env_id"][0]
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaGenerationError,
        "env_id_unique",
    )
    values = _nominal_values(1, 1, 1, include_invalid=False)
    values["navigation_cost"][0, 0, 0] = -1.0
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "valid_cost",
    )
    values = _nominal_values(1, 1, 1)
    values["path_valid"][0, 0, 0] = False
    for name in ("navigation_cost", "alignment_cost", "nominal_cost"):
        values[name][0, 0, 0] = 1.0e20
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "invalid_path_nan",
    )
    values = _nominal_values(1, 1, 1, include_invalid=False)
    values["nominal_cost"][0, 0, 0] += 0.5
    _expect_error(
        lambda: MRTA.NominalPairCostResult.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "nominal_sum",
    )


def test_local_set_contracts() -> None:
    for scale in ((1, 1, 1), (2, 3, 5)):
        values = _local_request_values(*scale)
        request = MRTA.LocalSetRequest.from_mapping(values, device=CPU)
        _assert(request.owner_expansion_rounds == 1, "owner round drift")
        _assert(request.num_envs == scale[0], "request E drift")
    values = _local_request_values(1, 1, 1)
    values["event_updated_ownership"][0, 0] = 1
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "ownership_range",
    )
    values = _local_request_values(1, 1, 1)
    values["owner_expansion_rounds"] = 2
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "owner_expansion_rounds",
    )
    values = _local_request_values(1, 1, 1)
    values["lifecycle_event_records"] = ((_diagnostic(),),)
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "trigger_placement",
    )
    values = _local_request_values(1, 1, 1)
    values["lifecycle_event_records"] = (
        (_event(transition=41),),
    )
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaGenerationError,
        "trigger_generation",
    )
    values = _local_request_values(1, 1, 1)
    values["assignment_opportunities"] = (
        (_opportunity(tick=5),),
    )
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaGenerationError,
        "trigger_generation",
    )
    values = _local_request_values(1, 1, 1, with_triggers=False)
    values["needs_assignment_mask"][0, 0] = True
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "needs_assignment_seed",
    )
    values = _local_request_values(1, 1, 1, with_triggers=False)
    values["lifecycle_event_records"] = ((_event(robot_id=1),),)
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "trigger_robot_range",
    )
    values = _local_request_values(1, 1, 1, with_triggers=False)
    values["lifecycle_event_records"] = ((_event(robot_id=0),),)
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "trigger_robot_seed",
    )
    values = _local_request_values(1, 1, 1, with_triggers=False)
    values["assignment_opportunities"] = (
        (_opportunity(robot_id=1),),
    )
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "trigger_robot_range",
    )
    values = _local_request_values(1, 1, 1, with_triggers=False)
    values["assignment_opportunities"] = (
        (_opportunity(robot_id=0),),
    )
    _expect_error(
        lambda: MRTA.LocalSetRequest.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "trigger_robot_seed",
    )
    result_values = _local_result_values()
    result = MRTA.LocalSetResult.from_mapping(result_values, device=CPU)
    _assert(
        int(result.overflow_disposition[-1].item())
        == int(MRTA.LocalSetOverflowDisposition.FAIL_CLOSED_NO_ASSIGNMENT),
        "overflow did not fail closed",
    )
    result_values["overflow_disposition"][-1] = int(
        MRTA.LocalSetOverflowDisposition.NONE
    )
    _expect_error(
        lambda: MRTA.LocalSetResult.from_mapping(
            result_values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "overflow_disposition",
    )
    result_values = _local_result_values()
    result_values["owner_expansion_rounds_used"][0] = 2
    _expect_error(
        lambda: MRTA.LocalSetResult.from_mapping(
            result_values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "owner_expansion_rounds",
    )


def test_top_k_global_ids_and_retention() -> None:
    for scale in ((1, 1, 1, 1), (2, 3, 5, 3)):
        values = _top_k_values(*scale)
        result = MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=scale[2], device=CPU
        )
        _assert(result.top_k == scale[3], "K drift")
    values = _top_k_values(1, 1, 2, 3)
    result = MRTA.TopKCandidateResult.from_mapping(
        values, num_tasks=2, device=CPU
    )
    _assert(result.global_task_ids[0, 0, 2].item() == -1, "invalid ID")
    _assert(torch.isnan(result.candidate_nominal_cost[0, 0, 2]), "invalid cost")
    values = _top_k_values(1, 1, 2, 2)
    values["global_task_ids"][0, 0] = torch.tensor([0, 0])
    _expect_error(
        lambda: MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=2, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "candidate_duplicate",
    )
    values = _top_k_values(1, 1, 2, 1)
    values["global_task_ids"][0, 0, 0] = 1
    values["current_task_id"][0, 0] = 0
    _expect_error(
        lambda: MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=2, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "current_task_retention",
    )
    values = _top_k_values(1, 1, 2, 2)
    values["current_task_retained"][0, 0] = False
    _expect_error(
        lambda: MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=2, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "current_task_retention",
    )
    values = _top_k_values(1, 1, 1, 1)
    values["candidate_valid"][0, 0, 0] = False
    values["global_task_ids"][0, 0, 0] = -1
    values["candidate_nominal_cost"][0, 0, 0] = 999999.0
    values["current_task_retained"][0, 0] = False
    _expect_error(
        lambda: MRTA.TopKCandidateResult.from_mapping(
            values, num_tasks=1, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "candidate_invalid_cost",
    )


def test_dvm_provenance_and_three_rows() -> None:
    values = _dvm_values()
    snapshot = _dvm_from_mapping(values)
    _assert(
        snapshot.decision_valid_mask.flatten().tolist()
        == [True, False, False],
        "DVM three-row truth table drifted",
    )
    _assert(
        snapshot.semantic_legal_action_count.flatten().tolist() == [2, 1, 0],
        "semantic action counts drifted",
    )
    _assert(
        snapshot.forced_policy_action_id.flatten().tolist() == [-1, 0, -1],
        "forced ID truth table drifted",
    )
    _assert(
        tuple(snapshot.to_mapping()) == tuple(MRTA._DVM_FIELD_ORDER)
        and all(
            name not in snapshot.to_mapping()
            for name in (
                "current_task_id",
                "executing_mask",
                "idle_or_needs_assignment_mask",
            )
        ),
        "construction context leaked into the DVM mapping",
    )
    _expect_error(
        lambda: MRTA.DecisionValidMaskSnapshot.from_mapping(
            _dvm_values(),
            device=CPU,
        ),
        TypeError,
    )
    values = _dvm_values()
    values["target_action_mask"][0, 0, 0] = False
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "target_mask_conjunction",
    )
    values = _dvm_values()
    values["semantic_legal_action_count"][0, 0, 0] = 1
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "semantic_action_count",
    )
    values = _dvm_values()
    values["decision_valid_mask"][0, 1, 0] = True
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "decision_valid_relation",
    )
    values = _dvm_values()
    values["decision_opportunity_present"][0, 2, 0] = False
    values["noop_action_mask"][0, 2, 0] = True
    values["available_actions"][0, 2, -1] = True
    values["semantic_legal_action_count"][0, 2, 0] = 1
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "no_opportunity_mask",
    )
    values = _dvm_values()
    values["local_topk_or_continue_mask"][0, 0, 0] = False
    _refresh_dvm_derived(values)
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "executing_continue_retention",
    )
    values = _dvm_values()
    values["noop_action_mask"][0, 0, 0] = True
    _refresh_dvm_derived(values)
    _expect_error(
        lambda: _dvm_from_mapping(values),
        MRTA.MrtaSchemaError,
        "executing_noop_forbidden",
    )
    values = _dvm_values()
    context = _dvm_context_values()
    context["executing_mask"][0, 1] = False
    context["idle_or_needs_assignment_mask"][0, 1] = True
    context["current_task_id"][0, 1] = -1
    _expect_error(
        lambda: _dvm_from_mapping(values, context=context),
        MRTA.MrtaSchemaError,
        "idle_noop_required",
    )
    values = _dvm_values()
    context = _dvm_context_values()
    context["idle_or_needs_assignment_mask"][0, 0] = True
    _expect_error(
        lambda: _dvm_from_mapping(values, context=context),
        MRTA.MrtaSchemaError,
        "construction_context_overlap",
    )
    values = _dvm_values()
    context = _dvm_context_values()
    context["executing_mask"][0, 0] = False
    _expect_error(
        lambda: _dvm_from_mapping(values, context=context),
        MRTA.MrtaSchemaError,
        "construction_context_unclassified",
    )
    context = _dvm_context_values()
    context["current_task_id"] = context["current_task_id"].to(
        dtype=torch.float32
    )
    _expect_error(
        lambda: _dvm_from_mapping(_dvm_values(), context=context),
        MRTA.MrtaSchemaError,
        "dtype",
    )
    context = _dvm_context_values()
    context["executing_mask"] = context["executing_mask"].unsqueeze(-1)
    _expect_error(
        lambda: _dvm_from_mapping(_dvm_values(), context=context),
        MRTA.MrtaSchemaError,
        "shape",
    )
    context = _dvm_context_values()
    context["current_task_id"] = torch.empty(
        (1, 3),
        dtype=torch.int64,
        device=torch.device("meta"),
    )
    _expect_error(
        lambda: _dvm_from_mapping(_dvm_values(), context=context),
        MRTA.MrtaSchemaError,
        "device",
    )
    context = _dvm_context_values()
    context["current_task_id"][0, 0] = 2
    _expect_error(
        lambda: _dvm_from_mapping(_dvm_values(), context=context),
        MRTA.MrtaSchemaError,
        "current_task_range",
    )
    context = _dvm_context_values()
    context["executing_mask"][0, 2] = False
    context["idle_or_needs_assignment_mask"][0, 2] = True
    context["current_task_id"][0, 2] = 0
    _expect_error(
        lambda: _dvm_from_mapping(_dvm_values(), context=context),
        MRTA.MrtaSchemaError,
        "idle_current_task",
    )
    values = _dvm_values()
    values["noop_action_mask"][0, 1, 0] = True
    _refresh_dvm_derived(values)
    context = _dvm_context_values()
    context["executing_mask"][0, 1] = False
    context["idle_or_needs_assignment_mask"][0, 1] = True
    context["current_task_id"][0, 1] = -1
    idle_snapshot = _dvm_from_mapping(values, context=context)
    _assert(
        bool(idle_snapshot.noop_action_mask[0, 1, 0].item()),
        "valid idle/needs-assignment noop context was rejected",
    )
    context = _dvm_context_values()
    context["executing_mask"][0, 2] = True
    context["current_task_id"][0, 2] = 1
    no_opportunity_executing = _dvm_from_mapping(
        _dvm_values(),
        context=context,
    )
    _assert(
        not bool(
            no_opportunity_executing.decision_opportunity_present[
                0, 2, 0
            ].item()
        ),
        "current retention was incorrectly required off opportunity rows",
    )
    values = _dvm_values()
    values["robot_available_mask"][0, 1] = False
    values["target_action_mask"][0, 1] = False
    values["available_actions"][0, 1] = False
    values["semantic_legal_action_count"][0, 1, 0] = 0
    values["forced_policy_action_id"][0, 1, 0] = -1
    values["decision_opportunity_present"][0, 1, 0] = False
    unavailable = _dvm_from_mapping(values)
    _assert(
        not unavailable.decision_valid_mask[0, 1, 0].item(),
        "unavailable robot became decision-valid",
    )


def test_proposal_four_mask_and_policy_only_selection() -> None:
    values = _proposal_values()
    snapshot = MRTA.ProposalSnapshot.from_mapping(values, device=CPU)
    _assert(
        snapshot.storage_row_present_mask.flatten().tolist()
        == [True, True, False],
        "storage truth table drifted",
    )
    _assert(
        snapshot.policy_proposal_present_mask.flatten().tolist()
        == [True, False, False],
        "policy truth table drifted",
    )
    _assert(
        snapshot.forced_nondecision_mask.flatten().tolist()
        == [False, True, False],
        "forced truth table drifted",
    )
    _assert(
        snapshot.proposal_kind[0][0] is MRTA.ProposalKind.NOOP_IDLE,
        "NOOP_IDLE was not retained as real proposal",
    )
    _assert(
        snapshot.resolver_policy_mask().flatten().tolist()
        == [True, False, False],
        "resolver policy-only selection drifted",
    )
    _assert(
        "effective_assignment" not in snapshot.to_mapping(),
        "effective assignment leaked into proposal DTO",
    )
    original_id = int(snapshot.stored_action_id[0, 0, 0].item())
    values = _proposal_values()
    values["policy_proposal_present_mask"][0, 0, 0] = False
    _expect_error(
        lambda: MRTA.ProposalSnapshot.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "four_mask_policy_dvm",
    )
    values = _proposal_values()
    values["stored_action_id"][0, 1, 0] = 1
    _expect_error(
        lambda: MRTA.ProposalSnapshot.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "historical_action_legality",
    )
    values = _proposal_values()
    values["proposal_kind"] = (
        (MRTA.ProposalKind.NOOP_IDLE, MRTA.ProposalKind.CLAIM, None),
    )
    values["proposed_task_id"][0, 1, 0] = 0
    _expect_error(
        lambda: MRTA.ProposalSnapshot.from_mapping(values, device=CPU),
        MRTA.MrtaSchemaError,
        "forced_not_proposal",
    )
    _assert(
        int(snapshot.stored_action_id[0, 0, 0].item()) == original_id,
        "rejected-policy diagnostic scenario rewrote stored proposal",
    )


def test_component_request_result_and_rejection_matrix() -> None:
    _assert(
        [item.value for item in MRTA.ComponentRejectionReason][0] == "none",
        "canonical rejection order changed",
    )
    request_values = _component_request_values()
    request = MRTA.TransferComponentRequest.from_mapping(
        request_values, device=CPU
    )
    _assert(request.num_robots == 2 and request.num_tasks == 2, "request dims")
    values = _component_request_values()
    values["member_robot_mask"][:] = False
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_empty",
    )
    values = _component_request_values(second_policy=False)
    values["proposal_kind"] = (
        MRTA.ProposalKind.SWITCH,
        MRTA.ProposalKind.CONTINUE,
    )
    values["proposed_task_id"][1] = 1
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "forced_not_component_proposal",
    )
    values = _component_request_values()
    values["baseline_assignment_a0"][0] = -1
    values["baseline_ownership_a0"][0] = -1
    values["proposed_task_id"][0] = 0
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_proposal_semantics",
    )
    values = _component_request_values()
    values["proposed_task_id"][0] = 0
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_proposal_semantics",
    )
    values = _component_request_values()
    values["proposal_kind"] = (
        MRTA.ProposalKind.CONTINUE,
        MRTA.ProposalKind.SWITCH,
    )
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_proposal_semantics",
    )
    values = _component_request_values(second_policy=False)
    values["baseline_assignment_a0"][0] = -1
    values["baseline_ownership_a0"][0] = -1
    values["proposed_task_id"][0] = -1
    values["proposal_kind"] = (MRTA.ProposalKind.CLAIM, None)
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_proposal_semantics",
    )
    values = _component_request_values(second_policy=False)
    values["member_task_mask"] = torch.tensor(
        [False, True], dtype=torch.bool
    )
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_membership_closure",
    )
    values = _component_request_values(second_policy=False)
    values["member_robot_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_membership_closure",
    )
    values = _component_request_values(second_policy=False)
    values["baseline_assignment_a0"][1] = -1
    values["baseline_ownership_a0"][1] = -1
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_dangling_robot",
    )
    values = _component_request_values(second_policy=False)
    values["member_robot_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    values["baseline_assignment_a0"][1] = -1
    values["baseline_ownership_a0"][1] = -1
    values["proposed_task_id"][0] = 0
    values["proposal_kind"] = (MRTA.ProposalKind.CONTINUE, None)
    _expect_error(
        lambda: MRTA.TransferComponentRequest.from_mapping(
            values, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "component_dangling_task",
    )
    accepted_values = _component_result_values(accepted=True)
    accepted = MRTA.TransferComponentResult.from_mapping(
        accepted_values, request=request, device=CPU
    )
    _assert(accepted.accepted and accepted.commit_generation == 5, "accept")
    rejected_values = _component_result_values(accepted=False)
    rejected = MRTA.TransferComponentResult.from_mapping(
        rejected_values, request=request, device=CPU
    )
    _assert(
        not rejected.accepted
        and rejected.rejection_reason
        is MRTA.ComponentRejectionReason.PAIR_IMPROVEMENT_NOT_MET
        and rejected.commit_generation == -1,
        "whole reject semantics drifted",
    )
    proposal_snapshot = MRTA.ProposalSnapshot.from_mapping(
        _proposal_values(),
        device=CPU,
    )
    stored_proposal_before = proposal_snapshot.stored_action_id
    MRTA.TransferComponentResult.from_mapping(
        _component_result_values(accepted=False),
        request=request,
        device=CPU,
    )
    _assert(
        torch.equal(
            proposal_snapshot.stored_action_id,
            stored_proposal_before,
        ),
        "rejected component rewrote the stored proposal action",
    )
    generation_mismatch = _component_result_values(accepted=True)
    generation_mismatch["transition_generation"][0] = 41
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            generation_mismatch,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaGenerationError,
        "request_generation",
    )
    bad_order = _component_result_values(accepted=False)
    bad_order["all_rejection_reasons"] = tuple(
        reversed(bad_order["all_rejection_reasons"])
    )
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            bad_order, request=request, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "rejection_reason_order",
    )
    proposal_mismatch = _component_result_values(accepted=True)
    proposal_mismatch["effective_assignment"][0] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            proposal_mismatch,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "proposal_effective_mismatch",
    )
    nonpolicy_request = MRTA.TransferComponentRequest.from_mapping(
        _component_request_values(second_policy=False),
        device=CPU,
    )
    nonpolicy_accepted = _component_result_values(accepted=True)
    nonpolicy_accepted["proposal_accepted_valid"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            nonpolicy_accepted,
            request=nonpolicy_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "proposal_accepted_validity",
    )
    nonpolicy_rewrite = _component_result_values(accepted=True)
    nonpolicy_rewrite["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    nonpolicy_rewrite["proposal_accepted_valid"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            nonpolicy_rewrite,
            request=nonpolicy_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "nonpolicy_member_assignment",
    )
    assignment_range = _component_result_values(accepted=False)
    assignment_range["effective_assignment"][0] = 2
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            assignment_range,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "assignment_range",
    )
    ownership_range = _component_result_values(accepted=False)
    ownership_range["effective_ownership"][0] = 2
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            ownership_range,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "ownership_range",
    )
    override_request_values = _component_request_values()
    override_request_values["proposal_kind"] = (
        MRTA.ProposalKind.SWITCH,
        MRTA.ProposalKind.CONTINUE,
    )
    override_request_values["proposed_task_id"][1] = 1
    override_request = MRTA.TransferComponentRequest.from_mapping(
        override_request_values,
        device=CPU,
    )
    continue_override = _component_result_values(accepted=True)
    continue_override["proposal_accepted"][1] = False
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            continue_override,
            request=override_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "continue_override_coverage",
    )
    three_robot_override_request = (
        MRTA.TransferComponentRequest.from_mapping(
            _three_robot_continue_override_request_values(),
            device=CPU,
        )
    )
    accepted_override = MRTA.TransferComponentResult.from_mapping(
        _three_robot_continue_override_result_values(),
        request=three_robot_override_request,
        device=CPU,
    )
    _assert(
        accepted_override.accepted
        and accepted_override.effective_assignment.tolist()
        == [1, -1, 0]
        and accepted_override.proposal_accepted.tolist()
        == [True, False, True],
        "three-robot covered CONTINUE semantics drifted",
    )
    uncovered_request_values = _component_request_values()
    uncovered_request_values["proposal_kind"] = (
        MRTA.ProposalKind.CONTINUE,
        MRTA.ProposalKind.CONTINUE,
    )
    uncovered_request_values["proposed_task_id"] = torch.tensor(
        [0, 1], dtype=torch.int64
    )
    uncovered_request = MRTA.TransferComponentRequest.from_mapping(
        uncovered_request_values,
        device=CPU,
    )
    uncovered_continue = _component_result_values(accepted=True)
    uncovered_continue["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    uncovered_continue["effective_assignment"] = torch.tensor(
        [0, 1], dtype=torch.int64
    )
    uncovered_continue["effective_ownership"] = torch.tensor(
        [0, 1], dtype=torch.int64
    )
    uncovered_continue["owner_change_mask"][:] = False
    uncovered_continue["local_cost_after"] = (
        uncovered_continue["local_cost_before"]
    )
    uncovered_continue["transfer_count"] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            uncovered_continue,
            request=uncovered_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "continue_override_coverage",
    )
    reviewer_partial = _component_result_values(accepted=True)
    reviewer_partial["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    reviewer_partial["effective_assignment"] = torch.tensor(
        [1, -1], dtype=torch.int64
    )
    reviewer_partial["effective_ownership"] = torch.tensor(
        [-1, 0], dtype=torch.int64
    )
    reviewer_partial["owner_change_mask"][:] = True
    reviewer_partial["assigned_count_after"] = 1
    reviewer_partial["transfer_count"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            reviewer_partial,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "accepted_policy_partial",
    )
    assigned_decrease = _component_result_values(accepted=True)
    assigned_decrease["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    assigned_decrease["effective_assignment"] = torch.tensor(
        [1, -1], dtype=torch.int64
    )
    assigned_decrease["effective_ownership"] = torch.tensor(
        [-1, 0], dtype=torch.int64
    )
    assigned_decrease["owner_change_mask"][:] = True
    assigned_decrease["assigned_count_after"] = 1
    assigned_decrease["transfer_count"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            assigned_decrease,
            request=override_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "accepted_assigned_count_decrease",
    )
    count_before = _component_result_values(accepted=True)
    count_before["assigned_count_before"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            count_before,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "assigned_count_before",
    )
    count_after = _component_result_values(accepted=False)
    count_after["assigned_count_after"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            count_after,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "assigned_count_after",
    )
    transfer_count = _component_result_values(accepted=True)
    transfer_count["transfer_count"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            transfer_count,
            request=request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "transfer_count",
    )
    claim_request_values = _component_request_values(second_policy=False)
    claim_request_values["baseline_assignment_a0"][0] = -1
    claim_request_values["baseline_ownership_a0"][0] = -1
    claim_request_values["proposed_task_id"][0] = 0
    claim_request_values["proposal_kind"] = (
        MRTA.ProposalKind.CLAIM,
        None,
    )
    claim_request = MRTA.TransferComponentRequest.from_mapping(
        claim_request_values,
        device=CPU,
    )
    claim_result = _component_result_values(accepted=True)
    claim_result["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    claim_result["proposal_accepted_valid"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    claim_result["effective_assignment"] = torch.tensor(
        [0, 1], dtype=torch.int64
    )
    claim_result["effective_ownership"] = torch.tensor(
        [0, 1], dtype=torch.int64
    )
    claim_result["owner_change_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    claim_result["assigned_count_before"] = 1
    claim_result["assigned_count_after"] = 2
    claim_result["transfer_count"] = 0
    accepted_claim = MRTA.TransferComponentResult.from_mapping(
        claim_result,
        request=claim_request,
        device=CPU,
    )
    _assert(
        accepted_claim.transfer_count == 0,
        "claim from unowned task was incorrectly counted as a transfer",
    )
    false_claim = _component_result_values(accepted=True)
    false_claim["proposal_accepted"] = torch.tensor(
        [False, False], dtype=torch.bool
    )
    false_claim["proposal_accepted_valid"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    false_claim["effective_assignment"] = torch.tensor(
        [-1, 1], dtype=torch.int64
    )
    false_claim["effective_ownership"] = torch.tensor(
        [-1, 1], dtype=torch.int64
    )
    false_claim["owner_change_mask"][:] = False
    false_claim["assigned_count_before"] = 1
    false_claim["assigned_count_after"] = 1
    false_claim["local_cost_after"] = false_claim["local_cost_before"]
    false_claim["transfer_count"] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            false_claim,
            request=claim_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "accepted_policy_partial",
    )
    noop_request_values = _component_request_values()
    noop_request_values["member_task_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    noop_request_values["baseline_assignment_a0"] = torch.tensor(
        [-1, -1], dtype=torch.int64
    )
    noop_request_values["baseline_ownership_a0"] = torch.tensor(
        [-1, -1], dtype=torch.int64
    )
    noop_request_values["proposed_task_id"] = torch.tensor(
        [0, -1], dtype=torch.int64
    )
    noop_request_values["proposal_kind"] = (
        MRTA.ProposalKind.CLAIM,
        MRTA.ProposalKind.NOOP_IDLE,
    )
    noop_request = MRTA.TransferComponentRequest.from_mapping(
        noop_request_values,
        device=CPU,
    )
    false_noop = _component_result_values(accepted=True)
    false_noop["proposal_accepted"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    false_noop["effective_assignment"] = torch.tensor(
        [0, -1], dtype=torch.int64
    )
    false_noop["effective_ownership"] = torch.tensor(
        [0, -1], dtype=torch.int64
    )
    false_noop["owner_change_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    false_noop["assigned_count_before"] = 0
    false_noop["assigned_count_after"] = 1
    false_noop["transfer_count"] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            false_noop,
            request=noop_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "accepted_policy_partial",
    )
    boundary_request_values = _component_request_values(
        second_policy=False
    )
    boundary_request_values["member_robot_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    boundary_request_values["member_task_mask"] = torch.tensor(
        [True, False], dtype=torch.bool
    )
    boundary_request_values["proposed_task_id"][0] = 0
    boundary_request_values["proposal_kind"] = (
        MRTA.ProposalKind.CONTINUE,
        None,
    )
    boundary_request = MRTA.TransferComponentRequest.from_mapping(
        boundary_request_values,
        device=CPU,
    )

    def boundary_result_values(*, accepted: bool) -> dict[str, object]:
        result = _component_result_values(accepted=accepted)
        result["proposal_accepted"] = torch.tensor(
            [accepted, False], dtype=torch.bool
        )
        result["proposal_accepted_valid"] = torch.tensor(
            [True, False], dtype=torch.bool
        )
        result["effective_assignment"] = torch.tensor(
            [0, 1], dtype=torch.int64
        )
        result["effective_ownership"] = torch.tensor(
            [0, 1], dtype=torch.int64
        )
        result["owner_change_mask"] = torch.tensor(
            [False, False], dtype=torch.bool
        )
        result["assigned_count_before"] = 1
        result["assigned_count_after"] = 1
        result["transfer_count"] = 0
        if accepted:
            result["local_cost_after"] = result["local_cost_before"]
        return result

    boundary_ownership = boundary_result_values(accepted=True)
    boundary_ownership["effective_ownership"][1] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            boundary_ownership,
            request=boundary_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "component_boundary_ownership",
    )
    boundary_assignment = boundary_result_values(accepted=False)
    boundary_assignment["effective_assignment"][1] = 0
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            boundary_assignment,
            request=boundary_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "component_boundary_assignment",
    )
    boundary_change = boundary_result_values(accepted=True)
    boundary_change["owner_change_mask"][1] = True
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            boundary_change,
            request=boundary_request,
            device=CPU,
        ),
        MRTA.MrtaSchemaError,
        "component_boundary_owner_change",
    )
    partial = _component_result_values(accepted=False)
    partial["effective_assignment"][0] = -1
    partial["effective_ownership"][0] = -1
    partial["owner_change_mask"][0] = True
    partial["assigned_count_after"] = 1
    _expect_error(
        lambda: MRTA.TransferComponentResult.from_mapping(
            partial, request=request, device=CPU
        ),
        MRTA.MrtaSchemaError,
        "whole_component_reject",
    )
    policy_record = MRTA.ComponentRejectionRecord(
        component_id="component_0",
        reason=MRTA.ComponentRejectionReason.CONTENTION_LOSS,
        policy_caused=True,
        penalty_eligible=True,
        penalty_unit_count=1,
        member_robot_ids=(0, 1),
        member_task_ids=(0,),
        env_id=11,
        episode_generation=7,
        transition_generation=40,
        assignment_tick_generation=4,
    )
    _assert(policy_record.penalty_unit_count == 1, "penalty component unit")
    system_record = MRTA.ComponentRejectionRecord(
        component_id="component_1",
        reason=(
            MRTA.ComponentRejectionReason
            .LOCAL_SET_OVERFLOW_FAIL_CLOSED
        ),
        policy_caused=False,
        penalty_eligible=False,
        penalty_unit_count=0,
        member_robot_ids=(0,),
        member_task_ids=(0,),
        env_id=11,
        episode_generation=7,
        transition_generation=40,
        assignment_tick_generation=4,
    )
    _assert(system_record.penalty_unit_count == 0, "system penalty unit")
    _expect_error(
        lambda: MRTA.ComponentRejectionRecord(
            component_id="component_2",
            reason=MRTA.ComponentRejectionReason.TERMINAL_TRANSITION,
            policy_caused=True,
            penalty_eligible=True,
            penalty_unit_count=1,
            member_robot_ids=(0,),
            member_task_ids=(0,),
            env_id=11,
            episode_generation=7,
            transition_generation=40,
            assignment_tick_generation=4,
        ),
        MRTA.MrtaSchemaError,
        "nonpolicy_rejection_attribution",
    )
    _expect_error(
        lambda: MRTA.ComponentRejectionRecord(
            component_id="component_3",
            reason=(
                MRTA.ComponentRejectionReason
                .POST_SNAPSHOT_SYSTEM_INVALIDATION
            ),
            policy_caused=True,
            penalty_eligible=False,
            penalty_unit_count=0,
            member_robot_ids=(0,),
            member_task_ids=(0,),
            env_id=11,
            episode_generation=7,
            transition_generation=40,
            assignment_tick_generation=4,
        ),
        MRTA.MrtaSchemaError,
        "nonpolicy_rejection_attribution",
    )


def _equal_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.dtype.is_floating_point:
        return bool(torch.equal(torch.isnan(left), torch.isnan(right))) and bool(
            torch.equal(left[~torch.isnan(left)], right[~torch.isnan(right)])
        )
    return bool(torch.equal(left, right))


def test_all_tensor_dto_alias_isolation_and_mutation_detection() -> None:
    factories = (
        _nominal_fixture,
        _local_request_fixture,
        _local_result_fixture,
        _top_k_fixture,
        _dvm_fixture,
        _proposal_fixture,
        _component_request_fixture,
        _component_result_fixture,
    )
    for fixture in factories:
        dto, values, tensor_name = fixture()
        baseline = getattr(dto, tensor_name)
        source = values[tensor_name]
        source.fill_(0)
        _assert(
            _equal_tensor(getattr(dto, tensor_name), baseline),
            f"{type(dto).__name__} retained a source alias",
        )
        accessor = getattr(dto, tensor_name)
        accessor.fill_(1)
        _assert(
            _equal_tensor(getattr(dto, tensor_name), baseline),
            f"{type(dto).__name__} exposed a writable accessor alias",
        )
        try:
            dto.schema_version = "mutated"
        except (FrozenInstanceError, AttributeError, TypeError):
            pass
        else:
            raise AssertionError(f"{type(dto).__name__} allowed field rebind")

        fresh, _, fresh_name = fixture()
        fresh._tensor_snapshots[fresh_name]._tensor.fill_(0)
        _expect_error(
            lambda fresh=fresh, fresh_name=fresh_name: getattr(
                fresh, fresh_name
            ),
            MRTA.MrtaSnapshotMutationError,
            "snapshot_mutation",
    )


def test_a3x1_domain_descriptor_v2_projections() -> None:
    """Freeze all A3x-1 domain projections and preserve every A3 DTO."""

    def primitive(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(key): primitive(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [primitive(item) for item in value]
        return value

    def canonical_sha256(value: object) -> str:
        payload = json.dumps(
            primitive(value),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    mrta = MRTA.get_assignment_mrta_contract_descriptor()
    event = EVENT.get_assignment_event_contract_descriptor()
    _assert(tuple(mrta) == MRTA_ROOT_KEYS, "MRTA v2 root order drifted")
    _assert(tuple(event) == EVENT_ROOT_KEYS, "event v2 root order drifted")
    _assert(
        MRTA.ASSIGNMENT_MRTA_CONTRACT_VERSION
        == mrta["contract_version"]
        == MRTA_DESCRIPTOR_VERSION,
        "MRTA descriptor version is not v2",
    )
    _assert(
        EVENT.ASSIGNMENT_EVENT_CONTRACT_VERSION
        == event["contract_version"]
        == EVENT_DESCRIPTOR_VERSION,
        "event descriptor version is not v2",
    )

    action = mrta["action_contract"]
    _assert(tuple(action) == ACTION_CONTRACT_KEYS, "action key order drifted")
    expected_action = {
        "contract_version": "event_gated_action_contract_v1",
        "num_agents": "scale_contract.M",
        "action_dimension": "scale_contract.N + 1",
        "target_action_id_domain": (
            "global_task_ids_0_through_scale_contract.N_minus_1"
        ),
        "noop_raw_id": "scale_contract.N",
        "noop_decoded_value": -1,
        "available_action_order": (
            "target_global_task_ids_ascending_then_noop"
        ),
        "decision_valid_mask_contract_version": (
            "decision_valid_mask_snapshot_v1"
        ),
        "proposal_mask_contract_version": "proposal_snapshot_v1",
        "cross_section_invariants": (
            "num_agents == scale_contract.M",
            "action_dimension == scale_contract.N + 1",
            "target_action_id_domain == global task IDs "
            "0..scale_contract.N-1",
            "noop_raw_id == scale_contract.N",
            "noop_decoded_value == -1",
            "available_action_order == target global task IDs followed by noop",
            "len(scale_contract.ordered_agent_names) == num_agents",
        ),
    }
    _assert(dict(action) == expected_action, "action literals drifted")

    projections = (
        ("local_candidate_semantics", LOCAL_CANDIDATE_KEYS),
        ("cost_path_semantics", COST_PATH_KEYS),
        ("component_semantics", COMPONENT_KEYS),
    )
    for name, expected_keys in projections:
        projection = mrta[name]
        _assert(
            tuple(projection) == expected_keys,
            f"{name} key order drifted",
        )
        _assert(
            canonical_sha256(projection)
            == PROJECTION_CANONICAL_SHA256[name],
            f"{name} exact literal inventory drifted",
        )

    triple_groups = (
        mrta["local_candidate_semantics"]["unresolved_parameters"],
        mrta["component_semantics"]["unresolved_parameters"],
        mrta["cost_path_semantics"]["unresolved_parameters"],
    )
    triples = tuple(item for group in triple_groups for item in group)
    _assert(len(triples) == 9, "MRTA must own exactly nine triples")
    _assert(
        tuple(item["name"] for item in triples)
        == tuple(EXPECTED_MRTA_TRIPLES),
        "MRTA triple name/order drifted",
    )
    for item in triples:
        _assert(tuple(item) == TRIPLE_KEYS, "MRTA triple field order drifted")
        expected_owner, expected_purpose = EXPECTED_MRTA_TRIPLES[item["name"]]
        _assert(
            (item["owner_phase"], item["semantic_purpose"])
            == (expected_owner, expected_purpose),
            f"MRTA triple {item['name']} drifted",
        )

    scheduled = event["scheduled_assignment_opportunity_semantics"]
    _assert(
        tuple(scheduled) == SCHEDULED_OPPORTUNITY_KEYS,
        "scheduled opportunity key order drifted",
    )
    _assert(
        canonical_sha256(scheduled)
        == PROJECTION_CANONICAL_SHA256[
            "scheduled_assignment_opportunity_semantics"
        ],
        "scheduled opportunity exact literals drifted",
    )
    retry = scheduled["unresolved_parameter"]
    _assert(tuple(retry) == TRIPLE_KEYS, "retry triple key order drifted")
    _assert(
        dict(retry)
        == {
            "name": "assignment_retry_cadence",
            "owner_phase": "phase_b",
            "semantic_purpose": (
                "physical_step_interval_for_persistent_unassigned_"
                "retry_opportunities"
            ),
        },
        "retry triple drifted",
    )
    _assert(
        scheduled["counter_source"]
        == "finalized_physical_transition_generation_delta"
        and scheduled["output_record_schema"]
        == (
            "AssignmentOpportunityRecord",
            "assignment_opportunity_record_v1",
            "assignment_retry_due",
            "retry_scheduler_v1",
        ),
        "retry projection moved from declarative existing-record semantics",
    )

    old_versions = {
        "NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION": "nominal_pair_cost_result_v1",
        "LOCAL_SET_REQUEST_SCHEMA_VERSION": "local_set_request_v1",
        "LOCAL_SET_RESULT_SCHEMA_VERSION": "local_set_result_v1",
        "TOP_K_CANDIDATE_RESULT_SCHEMA_VERSION": "top_k_candidate_result_v1",
        "DECISION_VALID_MASK_SNAPSHOT_SCHEMA_VERSION": (
            "decision_valid_mask_snapshot_v1"
        ),
        "PROPOSAL_SNAPSHOT_SCHEMA_VERSION": "proposal_snapshot_v1",
        "TRANSFER_COMPONENT_REQUEST_SCHEMA_VERSION": (
            "transfer_component_request_v1"
        ),
        "TRANSFER_COMPONENT_RESULT_SCHEMA_VERSION": (
            "transfer_component_result_v1"
        ),
        "COMPONENT_REJECTION_RECORD_SCHEMA_VERSION": (
            "component_rejection_record_v1"
        ),
    }
    for name, expected in old_versions.items():
        _assert(getattr(MRTA, name) == expected, f"old DTO {name} drifted")
    _assert(
        EVENT.LIFECYCLE_EVENT_RECORD_SCHEMA_VERSION
        == "lifecycle_event_record_v1"
        and EVENT.ASSIGNMENT_OPPORTUNITY_RECORD_SCHEMA_VERSION
        == "assignment_opportunity_record_v1"
        and EVENT.RESOLVER_DIAGNOSTIC_RECORD_SCHEMA_VERSION
        == "resolver_diagnostic_record_v1",
        "old event record version drifted",
    )
    _assert(
        len(event["record_systems"]) == 3,
        "v2 introduced a scheduler record system",
    )


def test_descriptor_privacy_and_no_algorithm_surface() -> None:
    descriptor = MRTA.get_assignment_mrta_contract_descriptor()
    _assert(isinstance(descriptor, MappingProxyType), "descriptor is mutable")

    def primitive_strings(value: object) -> tuple[str, ...]:
        collected: list[str] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                collected.append(str(key).lower())
                collected.extend(primitive_strings(item))
        elif isinstance(value, tuple):
            for item in value:
                collected.extend(primitive_strings(item))
        elif isinstance(value, str):
            collected.append(value.lower())
        return tuple(collected)

    strings = primitive_strings(descriptor)
    for forbidden in (
        "_version",
        "tensor._version",
        "storage_identity",
        "detector",
        "private_capability",
        "checkpoint_fingerprint",
        "logger_path",
        "numeric_tbd_value",
    ):
        _assert(forbidden not in strings, f"descriptor leaks {forbidden}")
    _assert(
        descriptor["four_mask_equations"]
        == MRTA.get_assignment_mrta_contract_descriptor()[
            "four_mask_equations"
        ],
        "descriptor is nondeterministic",
    )
    _expect_error(
        lambda: descriptor.__setitem__("x", 1),
        (TypeError, AttributeError),
    )
    construction_context = descriptor["construction_legality_context"]
    _expect_error(
        lambda: construction_context.__setitem__("x", 1),
        (TypeError, AttributeError),
    )
    _expect_error(
        lambda: construction_context["inputs"][0].__setitem__(
            "shape", ("M", "E")
        ),
        (TypeError, AttributeError),
    )
    _assert(
        tuple(
            item["name"] for item in construction_context["inputs"]
        )
        == (
            "current_task_id",
            "executing_mask",
            "idle_or_needs_assignment_mask",
        ),
        "DVM construction-context descriptor drifted",
    )
    dvm_schema_names = tuple(
        item["name"]
        for item in descriptor["schemas"]["decision_valid_mask"]["fields"]
    )
    _assert(
        all(
            name not in dvm_schema_names
            for name in (
                "current_task_id",
                "executing_mask",
                "idle_or_needs_assignment_mask",
            )
        ),
        "construction context became a persisted DVM schema field",
    )
    source_text = MRTA_PATH.read_text(encoding="utf-8")
    source = source_text.lower()
    for forbidden_call in (
        "appLauncher(".lower(),
        "optimizer.step(",
        "backward(",
        "torch.multinomial(",
        "categorical(",
        "open(",
    ):
        _assert(forbidden_call not in source, f"algorithm/side effect {forbidden_call}")
    _assert(
        "effective_assignment" not in MRTA._PROPOSAL_FIELD_ORDER,
        "proposal schema contains effective assignment",
    )
    tree = ast.parse(source_text)
    imported_modules: list[str] = []
    call_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(
                "." * node.level + (node.module or "")
            )
        elif isinstance(node, ast.Call):
            call_names.append(ast.unparse(node.func).lower())
    _assert(
        set(imported_modules)
        == {
            "__future__",
            "collections.abc",
            "dataclasses",
            "enum",
            "math",
            "re",
            "types",
            "typing",
            "torch",
            ".assignment_event_contract",
        },
        f"MRTA contract imports runtime/algorithm modules: {imported_modules}",
    )
    forbidden_algorithm_calls = {
        "argmin",
        "commit",
        "connected_components",
        "graph",
        "search",
        "shortest_path",
        "topk",
    }
    for call_name in call_names:
        leaf = call_name.rsplit(".", 1)[-1]
        _assert(
            leaf not in forbidden_algorithm_calls
            and "networkx" not in call_name,
            f"MRTA contract contains algorithm/runtime call {call_name}",
        )


def test_clean_child_side_effects() -> None:
    child = f"""
import contextlib, importlib.util, io, json, logging, os, random, sys
from pathlib import Path
from types import ModuleType
import torch
repo=Path({str(REPO_ROOT)!r})
scan=Path({str(SCAN_SOURCE)!r})
cwd_before=os.getcwd()
env_before=dict(os.environ)
path_before=tuple(sys.path)
handlers_before=tuple(logging.getLogger().handlers)
level_before=logging.getLogger().level
files_before=tuple(sorted(str(p.relative_to(Path.cwd())) for p in Path.cwd().rglob('*')))
py_rng_before=random.getstate()
torch_rng_before=torch.random.get_rng_state().clone()
numpy_before='numpy' in sys.modules
profile_before='isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract' in sys.modules
stdout=io.StringIO(); stderr=io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    for name,path in (
        ('isaaclab_tasks',repo/'source'/'isaaclab_tasks'/'isaaclab_tasks'),
        ('isaaclab_tasks.direct',repo/'source'/'isaaclab_tasks'/'isaaclab_tasks'/'direct'),
        ({PACKAGE!r},scan),
    ):
        m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
    sys.dont_write_bytecode=True
    for leaf in ('assignment_lifecycle_transition_contract','assignment_event_contract','assignment_mrta_contract'):
        key={PACKAGE!r}+'.'+leaf
        spec=importlib.util.spec_from_file_location(key,scan/(leaf+'.py'))
        module=importlib.util.module_from_spec(spec); sys.modules[key]=module
        spec.loader.exec_module(module)
    mrta=sys.modules[{MRTA_KEY!r}]
    spec_obj=mrta.UnresolvedParameterSpec('top_k_tasks_per_robot','phase_b','top_k_semantic')
    values={{
        'schema_version':mrta.NOMINAL_PAIR_COST_RESULT_SCHEMA_VERSION,
        'navigation_cost':torch.tensor([[[1.0]]],dtype=torch.float32),
        'alignment_cost':torch.tensor([[[0.5]]],dtype=torch.float32),
        'nominal_cost':torch.tensor([[[1.5]]],dtype=torch.float32),
        'path_valid':torch.tensor([[[True]]],dtype=torch.bool),
        'cost_unit':'expected_seconds',
        'estimator_version':'synthetic_fixture_v1',
        'env_id':torch.tensor([11],dtype=torch.int64),
        'episode_generation':torch.tensor([7],dtype=torch.int64),
        'transition_generation':torch.tensor([40],dtype=torch.int64),
        'assignment_tick_generation':torch.tensor([4],dtype=torch.int64),
    }}
    dto=mrta.NominalPairCostResult.from_mapping(values,device=torch.device('cpu'))
    assert dto.nominal_cost.item()==1.5 and spec_obj.name=='top_k_tasks_per_robot'
result={{
    'stdout':stdout.getvalue(),
    'stderr':stderr.getvalue(),
    'cwd':os.getcwd()==cwd_before,
    'env':dict(os.environ)==env_before,
    'path':tuple(sys.path)==path_before,
    'handlers':tuple(logging.getLogger().handlers)==handlers_before,
    'level':logging.getLogger().level==level_before,
    'files':tuple(sorted(str(p.relative_to(Path.cwd())) for p in Path.cwd().rglob('*')))==files_before,
    'py_rng':random.getstate()==py_rng_before,
    'torch_rng':torch.equal(torch.random.get_rng_state(),torch_rng_before),
    'numpy':('numpy' in sys.modules)==numpy_before,
    'profile':('isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract' in sys.modules)==profile_before,
    'forbidden':not any(
        name.startswith(('omni','isaaclab.app','harl'))
        or 'checkpoint' in name
        or name.endswith('assignment_harl_wrapper')
        or name.endswith('assignment_lifecycle_resolver')
        for name in sys.modules
    ),
}}
print(json.dumps(result,sort_keys=True))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [sys.executable, "-c", child],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(payload["stdout"] == "" and payload["stderr"] == "", "import output")
    for key, value in payload.items():
        if key not in {"stdout", "stderr"}:
            _assert(value is True, f"clean-child side effect failed: {key}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("canonical_identity_and_enum_order", test_canonical_identity_and_enum_order),
    ("event_records_and_strict_placement", test_event_records_and_strict_placement),
    ("lifecycle_result_typed_event_integration", test_lifecycle_result_typed_event_integration),
    ("nominal_cost_two_scales_and_invalid_paths", test_nominal_cost_two_scales_and_invalid_paths),
    ("local_set_contracts", test_local_set_contracts),
    ("top_k_global_ids_and_retention", test_top_k_global_ids_and_retention),
    ("dvm_provenance_and_three_rows", test_dvm_provenance_and_three_rows),
    ("proposal_four_mask_and_policy_only_selection", test_proposal_four_mask_and_policy_only_selection),
    ("component_request_result_and_rejection_matrix", test_component_request_result_and_rejection_matrix),
    ("all_tensor_dto_alias_isolation_and_mutation_detection", test_all_tensor_dto_alias_isolation_and_mutation_detection),
    ("a3x1_domain_descriptor_v2_projections", test_a3x1_domain_descriptor_v2_projections),
    ("descriptor_privacy_and_no_algorithm_surface", test_descriptor_privacy_and_no_algorithm_surface),
    ("clean_child_side_effects", test_clean_child_side_effects),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_event_gated_mrta_contract",
        "passed": passed,
        "total": len(results),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for item in results:
            suffix = (
                ""
                if item["status"] == "passed"
                else f": {item.get('error', '')}"
            )
            print(f"{item['status'].upper():6} {item['name']}{suffix}")
        print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
