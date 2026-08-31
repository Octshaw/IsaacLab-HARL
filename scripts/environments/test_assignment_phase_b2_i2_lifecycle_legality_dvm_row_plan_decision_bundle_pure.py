"""Pure synthetic B2-I2 legality, DVM, row-plan, and bundle regressions."""

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
DEVICE = torch.device("cpu")
PATHS = {
    "profile": SCAN_SOURCE / "assignment_profile_contract.py",
    "transition": SCAN_SOURCE / "assignment_lifecycle_transition_contract.py",
    "event": SCAN_SOURCE / "assignment_event_contract.py",
    "authority": SCAN_SOURCE / "assignment_lifecycle_authority_runtime.py",
    "claim": SCAN_SOURCE / "assignment_initial_claim_runtime.py",
    "lifecycle": SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py",
    "fence": SCAN_SOURCE / "assignment_interstep_claim_window_runtime.py",
    "schema_v2": SCAN_SOURCE / "assignment_event_profile_schema_contract_v2.py",
    "evidence": SCAN_SOURCE / "assignment_event_policy_evidence.py",
    "decision": SCAN_SOURCE / "assignment_event_policy_decision.py",
}

PROTECTED_HASHES = {
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


def _load(short_name: str):
    path = PATHS[short_name]
    key = f"{PACKAGE}.{path.stem}"
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
PROFILE = _load("profile")
TRANSITION = _load("transition")
EVENT = _load("event")
AUTHORITY = _load("authority")
CLAIM = _load("claim")
LIFECYCLE = _load("lifecycle")
FENCE = _load("fence")
SCHEMA = _load("schema_v2")
EVIDENCE = _load("evidence")
DECISION = _load("decision")

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason
RowKind = DECISION.EventPolicyRowKind


class CountingProblem(dict):
    def __init__(self, values: dict[str, object]) -> None:
        super().__init__(values)
        self.reads: dict[str, int] = {}

    def __getitem__(self, key: str) -> object:
        self.reads[key] = self.reads.get(key, 0) + 1
        return super().__getitem__(key)


def _scale(*, M: int, N: int):
    return SCHEMA.build_event_policy_scale_contract_v2(
        M=M,
        N=N,
        ordered_agent_names=tuple(f"robot_{index}" for index in range(M)),
        ordered_task_ids=tuple(range(N)),
        scene_env_spacing=12.0,
        sim_dt_seconds=0.01,
        control_decimation=4,
        episode_time_limit_seconds=40.0,
    )


def _problem(*, E: int, M: int, N: int) -> CountingProblem:
    base_pos = torch.arange(E * M * 3, dtype=torch.float32).reshape(E, M, 3) / 10.0
    scanner_quat = torch.zeros((E, M, 4), dtype=torch.float32)
    scanner_quat[..., 0] = 1.0
    task_quat = torch.zeros((E, N, 4), dtype=torch.float32)
    task_quat[..., 0] = 1.0
    return CountingProblem(
        {
            "num_envs": E,
            "num_agents": M,
            "agent_names": tuple(f"robot_{index}" for index in range(M)),
            "num_viewpoints": N,
            "viewpoint_ids": tuple(range(N)),
            "base_pos": base_pos,
            "base_yaw": torch.zeros((E, M), dtype=torch.float32),
            "scanner_pos": base_pos + 0.5,
            "scanner_quat": scanner_quat,
            "viewpoint_pos": torch.arange(E * N * 3, dtype=torch.float32).reshape(E, N, 3) / 20.0,
            "viewpoint_quat": task_quat,
            "arm_reach": torch.ones((M,), dtype=torch.float32),
            "scanner_min_range": torch.full((M,), 0.1, dtype=torch.float32),
            "scanner_max_range": torch.full((M,), 1.5, dtype=torch.float32),
            "scanner_fov_deg": torch.full((M,), 90.0, dtype=torch.float32),
            "feasible_mask": torch.ones((E, M, N), dtype=torch.bool),
            "cost_matrix": torch.arange(1, E * M * N + 1, dtype=torch.float32).reshape(E, M, N),
            "robot_status": torch.full((E, M), 99, dtype=torch.int64),
            "task_status": torch.full((E, N), 99, dtype=torch.int64),
        }
    )


def _state(*, E: int, M: int, N: int):
    return (
        torch.full((E, N), int(TaskState.AVAILABLE), dtype=torch.int64),
        torch.full((E, M), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64),
        torch.full((E, N), -1, dtype=torch.int64),
        torch.zeros((E, M, N), dtype=torch.bool),
        torch.zeros((E, M), dtype=torch.int64),
        torch.full((E,), int(Reason.NONE), dtype=torch.int64),
    )


def _publication(*, E: int, M: int, N: int, tensors, domain=None, serial: int = 7):
    actual_domain = object() if domain is None else domain
    task, robot, owner, failed, completed, reason = tensors
    store_state = LIFECYCLE._LifecycleStoreState(
        version=serial,
        task_state=task,
        robot_state=robot,
        ownership=owner,
        cumulative_failed_pairs=failed,
        completion_count=completed,
        termination_reason=reason,
    )
    lifecycle_snapshot = LIFECYCLE.LifecycleStateSnapshot._create(
        store_identity=object(),
        device=DEVICE,
        env_id=torch.arange(E, dtype=torch.int64),
        state=store_state,
    )
    view = LIFECYCLE.PublishedLifecycleView._create(
        state_snapshot=lifecycle_snapshot,
        episode_generation=torch.arange(3, 3 + E, dtype=torch.int64),
        transition_generation=torch.arange(5, 5 + E, dtype=torch.int64),
        result=None,
    )
    capability = object()
    identity = CLAIM._CurrentPublicationIdentity._create(
        serial=serial,
        domain_identity=actual_domain,
        factory_capability=capability,
    )
    provenance = tuple(
        CLAIM._CurrentPublicationProvenance._create(
            kind=CLAIM._CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
            lifecycle_result=None,
            assignment_artifact=None,
            immediate_predecessor_identity=None,
            root_kind=CLAIM._CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
            root_publication_identity=identity,
            root_lifecycle_result=None,
            factory_capability=capability,
        )
        for _ in range(E)
    )
    publication = CLAIM._EventRuntimeCurrentPublication._create(
        lifecycle_view=view,
        publication_identity=identity,
        provenance=provenance,
        factory_capability=capability,
    )
    return publication, actual_domain, lifecycle_snapshot


def _open_view(domain: object, *, serial: int = 11):
    capability = object()
    window = FENCE._ClaimWindowIdentity._create(
        serial=serial,
        domain_identity=domain,
        factory_capability=capability,
    )
    view = FENCE._ClaimWindowFenceView(
        phase=FENCE._ClaimWindowFencePhase.OPEN,
        window=window,
        active_step=None,
        active_reset=None,
        next_window_serial=serial + 1,
        next_admission_serial=0,
        next_envelope_serial=0,
    )
    return view, window


def _snapshot(*, E: int, M: int, N: int, tensors=None, problem=None, serial: int = 7):
    actual_tensors = _state(E=E, M=M, N=N) if tensors is None else tensors
    actual_problem = _problem(E=E, M=M, N=N) if problem is None else problem
    publication, domain, lifecycle_snapshot = _publication(
        E=E, M=M, N=N, tensors=actual_tensors, serial=serial
    )
    open_view, window = _open_view(domain, serial=serial + 4)
    physical = EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
        assignment_problem=actual_problem,
        episode_progress_steps=torch.arange(E, dtype=torch.int64),
        scale_contract=_scale(M=M, N=N),
    )
    snapshot = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(
        current_publication=publication,
        current_open_window_view=open_view,
        physical_evidence=physical,
        scale_contract=_scale(M=M, N=N),
    )
    return snapshot, actual_problem, publication, lifecycle_snapshot, open_view, window


def _expect_decision_failure(code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except DECISION.EventPolicyDecisionError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    else:
        raise AssertionError(f"expected decision failure {code}")


def _expect_evidence_failure(code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except EVIDENCE.EventPolicyEvidenceError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    else:
        raise AssertionError(f"expected evidence failure {code}")


def _true_ids(row: torch.Tensor) -> tuple[int, ...]:
    return tuple(int(item) for item in row.nonzero(as_tuple=False).flatten().tolist())


def test_bundle_schema_shapes_dtypes_and_factory_boundary() -> None:
    snapshot, *_ = _snapshot(E=2, M=3, N=12)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    descriptor = DECISION.get_event_policy_decision_descriptor_v2()
    _assert(bundle.evidence_snapshot is snapshot, "snapshot reference rebound")
    _assert(bundle.evidence_identity is snapshot.identity, "identity reference rebound")
    _assert(tuple(bundle.available_actions_bool.shape) == (2, 3, 13), "available shape")
    _assert(tuple(bundle.decision_valid_mask.shape) == (2, 3, 1), "DVM shape")
    _assert(tuple(bundle.row_kind.shape) == (2, 3), "row kind shape")
    _assert(tuple(bundle.forced_action_id.shape) == (2, 3, 1), "forced shape")
    _assert(bundle.available_actions_bool.dtype is torch.bool, "canonical mask dtype")
    _assert(bundle.runner_available_actions.dtype is torch.float32, "runner dtype")
    _assert(bundle.row_kind.dtype is torch.int64, "row kind dtype")
    _assert(descriptor["readiness_change_authorized"] is False, "readiness changed")
    _expect_decision_failure("decision_bundle_factory_required", lambda: DECISION.EventPolicyDecisionBundle())


def test_four_robot_states_and_exact_row_semantics() -> None:
    E, M, N = 1, 4, 4
    tensors = list(_state(E=E, M=M, N=N))
    tensors[0][0, 0] = int(TaskState.CLAIMED)
    tensors[1][0] = torch.tensor(
        [int(RobotState.EXECUTING), int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK), int(RobotState.UNAVAILABLE)]
    )
    tensors[2][0, 0] = 0
    tensors[3][0, 1, 2] = True
    problem = _problem(E=E, M=M, N=N)
    problem["feasible_mask"][0, 1, 3] = False
    snapshot, *_ = _snapshot(E=E, M=M, N=N, tensors=tuple(tensors), problem=problem)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    kinds = tuple(int(item) for item in bundle.row_kind[0].tolist())
    _assert(kinds == (int(RowKind.FORCED_CONTINUATION_ROW), int(RowKind.POLICY_DECISION_ROW), int(RowKind.FORCED_NOOP_ROW), int(RowKind.FORCED_NOOP_ROW)), f"row kinds {kinds}")
    _assert(_true_ids(bundle.available_actions_bool[0, 0]) == (0,), "continuation mask")
    _assert(_true_ids(bundle.available_actions_bool[0, 1]) == (1, N), "policy mask")
    _assert(_true_ids(bundle.available_actions_bool[0, 2]) == (N,), "waiting mask")
    _assert(_true_ids(bundle.available_actions_bool[0, 3]) == (N,), "unavailable mask")
    _assert(tuple(bool(item) for item in bundle.decision_valid_mask[0, :, 0]) == (False, True, False, False), "DVM rows")


def test_needs_with_zero_legal_target_is_forced_noop() -> None:
    problem = _problem(E=1, M=1, N=3)
    problem["feasible_mask"].zero_()
    snapshot, *_ = _snapshot(E=1, M=1, N=3, problem=problem)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(int(bundle.row_kind[0, 0]) == int(RowKind.FORCED_NOOP_ROW), "no-target row")
    _assert(_true_ids(bundle.available_actions_bool[0, 0]) == (3,), "no-target mask")
    _assert(int(bundle.forced_action_id[0, 0, 0]) == 3, "noop raw ID")
    _assert(not bool(bundle.decision_valid_mask[0, 0, 0]), "no-target DVM")


def test_executing_continuation_and_contradictions_fail_closed() -> None:
    tensors = list(_state(E=1, M=1, N=3))
    tensors[1][0, 0] = int(RobotState.EXECUTING)
    tensors[0][0, 1] = int(TaskState.NAVIGATING)
    tensors[2][0, 1] = 0
    problem = _problem(E=1, M=1, N=3)
    problem["feasible_mask"][0, 0, 1] = False
    snapshot, *_ = _snapshot(E=1, M=1, N=3, tensors=tuple(tensors), problem=problem)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(_true_ids(bundle.available_actions_bool[0, 0]) == (1,), "continuation changed by feasibility")
    _assert(int(bundle.forced_action_id[0, 0, 0]) == 1, "continuation forced ID")
    _assert(not bool(bundle.policy_proposal_present_mask[0, 0, 0]), "continuation proposal")

    missing = list(_state(E=1, M=1, N=2))
    missing[1][0, 0] = int(RobotState.EXECUTING)
    missing_snapshot, *_ = _snapshot(E=1, M=1, N=2, tensors=tuple(missing))
    _expect_decision_failure("executing_ownership_cardinality", lambda: DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=missing_snapshot))

    inactive = list(_state(E=1, M=1, N=2))
    inactive[1][0, 0] = int(RobotState.EXECUTING)
    inactive[0][0, 0] = int(TaskState.COMPLETED)
    inactive[2][0, 0] = 0
    inactive_snapshot, *_ = _snapshot(E=1, M=1, N=2, tensors=tuple(inactive))
    _expect_decision_failure("executing_task_not_active", lambda: DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=inactive_snapshot))

    corrupt = list(_state(E=1, M=1, N=2))
    corrupt[1][0, 0] = int(RobotState.EXECUTING)
    corrupt[0][0, 0] = int(TaskState.CLAIMED)
    corrupt[2][0, 0] = 0
    corrupt_snapshot, *_ = _snapshot(E=1, M=1, N=2, tensors=tuple(corrupt))
    object.__setattr__(corrupt_snapshot, "_ownership", torch.tensor([[0, 0]], dtype=torch.int64))
    _expect_decision_failure("executing_ownership_cardinality", lambda: DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=corrupt_snapshot))


def test_i1_multiple_ownership_boundary_also_fails_closed() -> None:
    tensors = list(_state(E=1, M=1, N=2))
    tensors[1][0, 0] = int(RobotState.EXECUTING)
    tensors[0][0] = int(TaskState.CLAIMED)
    tensors[2][0] = 0
    _expect_evidence_failure("multiple_owned_tasks", lambda: _snapshot(E=1, M=1, N=2, tensors=tuple(tensors)))


def test_task_lifecycle_matrix_allows_only_available() -> None:
    E, M, N = 1, 1, len(TaskState)
    tensors = list(_state(E=E, M=M, N=N))
    tensors[0][0] = torch.tensor([int(item) for item in TaskState], dtype=torch.int64)
    snapshot, *_ = _snapshot(E=E, M=M, N=N, tensors=tuple(tensors))
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(_true_ids(bundle.available_actions_bool[0, 0]) == (int(TaskState.AVAILABLE), N), "task state legality")


def test_ownership_failed_pair_and_explicit_feasibility_conjunction() -> None:
    E, M, N = 1, 2, 4
    tensors = list(_state(E=E, M=M, N=N))
    tensors[2][0, 0] = 1
    tensors[3][0, 0, 1] = True
    problem = _problem(E=E, M=M, N=N)
    problem["feasible_mask"][0, 0, 2] = False
    snapshot, *_ = _snapshot(E=E, M=M, N=N, tensors=tuple(tensors), problem=problem)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(_true_ids(bundle.available_actions_bool[0, 0]) == (3, N), "legality conjunction")
    _assert(float(problem["cost_matrix"][0, 0, 2]) > 0, "finite-cost control")


def test_finite_geometric_cost_never_changes_legality() -> None:
    problem_a = _problem(E=1, M=2, N=3)
    problem_b = _problem(E=1, M=2, N=3)
    problem_b["cost_matrix"].mul_(100.0).add_(7.0)
    snapshot_a, *_ = _snapshot(E=1, M=2, N=3, problem=problem_a, serial=20)
    snapshot_b, *_ = _snapshot(E=1, M=2, N=3, problem=problem_b, serial=30)
    bundle_a = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot_a)
    bundle_b = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot_b)
    _assert(torch.equal(bundle_a.available_actions_bool, bundle_b.available_actions_bool), "cost changed legality")
    _assert(torch.equal(bundle_a.row_kind, bundle_b.row_kind), "cost changed row kind")
    _assert(bundle_a.provenance["geometric_ranking_cost_used_for_legality"] is False, "cost provenance")


def test_same_task_multi_robot_conflict_is_preserved() -> None:
    snapshot, *_ = _snapshot(E=1, M=2, N=1)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(bool(bundle.available_actions_bool[0, 0, 0]), "robot 0 task masked")
    _assert(bool(bundle.available_actions_bool[0, 1, 0]), "robot 1 task masked")
    _assert(bool(bundle.policy_row_mask.all().item()), "same-task policy rows lost")
    _assert(bundle.provenance["same_task_multi_robot_conflict_preserved"] is True, "resolver preemption")


def test_proposal_presence_forced_ids_and_storage_plan() -> None:
    tensors = list(_state(E=1, M=3, N=3))
    tensors[1][0] = torch.tensor([int(RobotState.EXECUTING), int(RobotState.NEEDS_ASSIGNMENT), int(RobotState.WAITING_FOR_TASK)])
    tensors[0][0, 0] = int(TaskState.ALIGNING)
    tensors[2][0, 0] = 0
    snapshot, *_ = _snapshot(E=1, M=3, N=3, tensors=tuple(tensors))
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(tuple(bool(item) for item in bundle.policy_proposal_present_mask[0, :, 0]) == (False, True, False), "proposal presence")
    _assert(tuple(int(item) for item in bundle.forced_action_id[0, :, 0]) == (0, -1, 3), "forced IDs")
    _assert(torch.equal(bundle.policy_row_mask, bundle.decision_valid_mask), "DVM definition")
    _assert(torch.equal(bundle.forced_row_mask, bundle.forced_continuation_mask | bundle.forced_noop_mask), "forced union")
    _assert(bool(bundle.storage_row_mask.all().item()), "current storage rows")
    _assert(not bool(bundle.terminal_no_row_mask.any().item()), "terminal current row")
    _assert(bool((bundle.available_actions_bool.sum(dim=-1) >= 1).all().item()), "all-zero current row")


def test_terminal_no_row_descriptor_stays_outside_i1() -> None:
    terminal = DECISION.build_terminal_no_row_semantics_v2(E=2, M=3, N=12, device=DEVICE)
    _assert(not bool(terminal.available_actions_bool.any().item()), "terminal actions")
    _assert(not bool(terminal.decision_valid_mask.any().item()), "terminal DVM")
    _assert(not bool(terminal.policy_proposal_present_mask.any().item()), "terminal proposal")
    _assert(bool(terminal.terminal_no_row_mask.all().item()), "terminal row mask")
    _assert(not bool(terminal.storage_row_mask.any().item()), "terminal storage row")
    _assert(bool((terminal.row_kind == int(RowKind.TERMINAL_NO_ROW)).all().item()), "terminal kind")
    _assert(bool((terminal.forced_action_id == -1).all().item()), "terminal forced route")
    _assert(not hasattr(terminal, "evidence_snapshot"), "terminal consumed I1")


def test_no_p2_physical_or_window_recapture() -> None:
    problem = _problem(E=1, M=2, N=3)
    snapshot, _, _, lifecycle_snapshot, open_view, _ = _snapshot(E=1, M=2, N=3, problem=problem)
    reads_before = dict(problem.reads)
    actor_before = snapshot.actor_obs
    critic_before = snapshot.semantic_share_obs
    dict.__getitem__(problem, "feasible_mask").zero_()
    dict.__getitem__(problem, "cost_matrix").add_(10000.0)
    lifecycle_snapshot._robot_state.fill_(int(RobotState.UNAVAILABLE))
    object.__setattr__(open_view, "window", object())
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    _assert(problem.reads == reads_before, f"physical reread: {problem.reads}")
    _assert(bool(bundle.policy_row_mask.all().item()), "P2 or physical source reread")
    _assert(torch.equal(snapshot.actor_obs, actor_before), "actor evidence modified")
    _assert(torch.equal(snapshot.semantic_share_obs, critic_before), "critic evidence modified")
    source = PATHS["decision"].read_text(encoding="utf-8")
    _assert("source_publication" not in source and "source_window_identity" not in source, "runtime identity recapture path")


def test_exact_snapshot_and_i42_pre_inference_binding() -> None:
    snapshot_a, *_ = _snapshot(E=1, M=2, N=3, serial=40)
    snapshot_b, *_ = _snapshot(E=1, M=2, N=3, serial=50)
    _assert(torch.equal(snapshot_a.actor_obs, snapshot_b.actor_obs), "same-value control")
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot_a)
    bundle.validate_evidence_snapshot(snapshot_a)
    _expect_decision_failure("evidence_snapshot_identity_mismatch", lambda: bundle.validate_evidence_snapshot(snapshot_b))
    binding = bundle.proposal_source_binding
    _assert(binding.evidence_snapshot is snapshot_a, "I4-2 binding snapshot")
    _assert(binding.identity is snapshot_a.identity, "I4-2 binding identity")
    _assert(binding.p2_publication_identity is snapshot_a.identity.p2_publication_identity, "I4-2 P2 identity")
    _assert(binding.open_window_identity is snapshot_a.identity.open_window_identity, "I4-2 OPEN identity")
    _assert(binding.provenance["actual_adapter_snapshot_created"] is False, "I4-2 executed")


def test_bundle_immutability_and_no_alias() -> None:
    snapshot, *_ = _snapshot(E=1, M=3, N=4)
    actor_before = snapshot.actor_obs
    share_before = snapshot.runner_share_obs
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    available_before = bundle.available_actions_bool
    dvm_before = bundle.decision_valid_mask
    returned_available = bundle.available_actions_bool
    returned_available.zero_()
    returned_dvm = bundle.decision_valid_mask
    returned_dvm.logical_not_()
    returned_forced = bundle.forced_action_id
    returned_forced.fill_(999)
    _assert(torch.equal(bundle.available_actions_bool, available_before), "available alias")
    _assert(torch.equal(bundle.decision_valid_mask, dvm_before), "DVM alias")
    _assert(not bool((bundle.forced_action_id == 999).any().item()), "forced alias")
    _assert(torch.equal(snapshot.actor_obs, actor_before), "actor mutated by I2")
    _assert(torch.equal(snapshot.runner_share_obs, share_before), "share mutated by I2")


def test_proposal_effective_and_learner_boundaries() -> None:
    snapshot, *_ = _snapshot(E=1, M=2, N=3)
    bundle = DECISION.seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)
    provenance = bundle.provenance
    _assert(provenance["actual_sample_or_logprob_present"] is False, "sample/logprob created")
    _assert(provenance["resolver_or_arbitration_result_present"] is False, "resolver result created")
    _assert(provenance["effective_assignment_present"] is False, "effective assignment created")
    _assert(provenance["lifecycle_or_ownership_mutation"] is False, "ownership mutation")
    _assert(provenance["learner_active_mask_semantics"] is False, "DVM became active mask")
    _assert(not hasattr(bundle, "action") and not hasattr(bundle, "action_log_prob"), "actor envelope leaked")


def test_scope_static_oracle_and_protected_hashes() -> None:
    source = PATHS["decision"].read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    _assert(not any(name.endswith(("assignment_initial_claim_runtime", "assignment_interstep_claim_window_runtime", "assignment_event_proposal_adapter")) for name in imported_modules), "runtime/proposal adapter imported")
    _assert(not any(name.startswith(("omni", "isaaclab", "harl")) for name in imported_modules), "forbidden runtime import")
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    _assert(not called_names.intersection({"get_actions", "evaluate_actions", "resolve", "commit", "step"}), f"forbidden call: {called_names}")
    _assert("assignment_tick_generation" not in source and "decision_tick" not in source, "clock introduced")
    for filename, expected in PROTECTED_HASHES.items():
        actual = hashlib.sha256((SCAN_SOURCE / filename).read_bytes()).hexdigest()
        _assert(actual == expected, f"protected file drift: {filename}")


def test_canonical_alias_and_isolated_import() -> None:
    alias = "assignment_event_policy_decision_alias"
    spec = importlib.util.spec_from_file_location(alias, PATHS["decision"])
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
for stem in ('assignment_profile_contract','assignment_lifecycle_transition_contract','assignment_event_contract','assignment_lifecycle_authority_runtime','assignment_initial_claim_runtime','assignment_lifecycle_transaction_runtime','assignment_interstep_claim_window_runtime','assignment_event_profile_schema_contract_v2','assignment_event_policy_evidence','assignment_event_policy_decision'): load(stem)
added=set(sys.modules)-before
print(json.dumps({{'canonical':package+'.assignment_event_policy_decision' in sys.modules,'bare':'assignment_event_policy_decision' not in sys.modules,'forbidden':not any(name.startswith(('omni','isaaclab.app','harl')) for name in added)}}))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run([sys.executable, "-c", child], cwd=temp_dir, capture_output=True, text=True, check=False)
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(all(payload.values()), f"isolation failed: {payload}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("bundle_schema_shapes_dtypes_and_factory_boundary", test_bundle_schema_shapes_dtypes_and_factory_boundary),
    ("four_robot_states_and_exact_row_semantics", test_four_robot_states_and_exact_row_semantics),
    ("needs_with_zero_legal_target_is_forced_noop", test_needs_with_zero_legal_target_is_forced_noop),
    ("executing_continuation_and_contradictions_fail_closed", test_executing_continuation_and_contradictions_fail_closed),
    ("i1_multiple_ownership_boundary_also_fails_closed", test_i1_multiple_ownership_boundary_also_fails_closed),
    ("task_lifecycle_matrix_allows_only_available", test_task_lifecycle_matrix_allows_only_available),
    ("ownership_failed_pair_and_explicit_feasibility_conjunction", test_ownership_failed_pair_and_explicit_feasibility_conjunction),
    ("finite_geometric_cost_never_changes_legality", test_finite_geometric_cost_never_changes_legality),
    ("same_task_multi_robot_conflict_is_preserved", test_same_task_multi_robot_conflict_is_preserved),
    ("proposal_presence_forced_ids_and_storage_plan", test_proposal_presence_forced_ids_and_storage_plan),
    ("terminal_no_row_descriptor_stays_outside_i1", test_terminal_no_row_descriptor_stays_outside_i1),
    ("no_p2_physical_or_window_recapture", test_no_p2_physical_or_window_recapture),
    ("exact_snapshot_and_i42_pre_inference_binding", test_exact_snapshot_and_i42_pre_inference_binding),
    ("bundle_immutability_and_no_alias", test_bundle_immutability_and_no_alias),
    ("proposal_effective_and_learner_boundaries", test_proposal_effective_and_learner_boundaries),
    ("scope_static_oracle_and_protected_hashes", test_scope_static_oracle_and_protected_hashes),
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
            results.append(
                {"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
            )
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_phase_b2_i2_lifecycle_legality_dvm_row_plan_decision_bundle_pure",
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
