"""Pure synthetic B2-I1 immutable evidence/current-projector regressions."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
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
}

PROTECTED_HASHES = {
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

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Reason = TRANSITION.TerminationReason


class CountingProblem(dict):
    def __init__(self, values: dict[str, object]) -> None:
        super().__init__(values)
        self.reads: dict[str, int] = {}

    def __getitem__(self, key: str) -> object:
        self.reads[key] = self.reads.get(key, 0) + 1
        return super().__getitem__(key)


def _scale(*, M: int = 3, N: int = 12):
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


def _problem(*, E: int = 2, M: int = 3, N: int = 12) -> CountingProblem:
    base_pos = torch.arange(E * M * 3, dtype=torch.float32).reshape(E, M, 3) / 10.0
    scanner_pos = base_pos + 0.5
    task_pos = torch.arange(E * N * 3, dtype=torch.float32).reshape(E, N, 3) / 20.0
    scanner_quat = torch.zeros((E, M, 4), dtype=torch.float32)
    scanner_quat[..., 0] = -1.0
    task_quat = torch.zeros((E, N, 4), dtype=torch.float32)
    task_quat[..., 0] = 1.0
    feasible = torch.ones((E, M, N), dtype=torch.bool)
    feasible[0, 0, 0] = False
    cost = torch.arange(1, E * M * N + 1, dtype=torch.float32).reshape(E, M, N)
    return CountingProblem(
        {
            "num_envs": E,
            "num_agents": M,
            "agent_names": tuple(f"robot_{index}" for index in range(M)),
            "num_viewpoints": N,
            "viewpoint_ids": tuple(range(N)),
            "base_pos": base_pos,
            "base_yaw": torch.linspace(0.0, 0.5, E * M, dtype=torch.float32).reshape(E, M),
            "scanner_pos": scanner_pos,
            "scanner_quat": scanner_quat,
            "viewpoint_pos": task_pos,
            "viewpoint_quat": task_quat,
            "arm_reach": torch.linspace(1.0, 2.0, M, dtype=torch.float32),
            "scanner_min_range": torch.linspace(0.1, 0.2, M, dtype=torch.float32),
            "scanner_max_range": torch.linspace(1.0, 1.5, M, dtype=torch.float32),
            "scanner_fov_deg": torch.linspace(60.0, 90.0, M, dtype=torch.float32),
            "feasible_mask": feasible,
            "cost_matrix": cost,
            "robot_status": torch.full((E, M), 99, dtype=torch.int64),
            "task_status": torch.full((E, N), 99, dtype=torch.int64),
        }
    )


def _physical(problem=None, *, E: int = 2, M: int = 3, N: int = 12):
    actual = _problem(E=E, M=M, N=N) if problem is None else problem
    progress = torch.arange(E, dtype=torch.int64) * 100
    return EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
        assignment_problem=actual,
        episode_progress_steps=progress,
        scale_contract=_scale(M=M, N=N),
    )


def _state_tensors(*, E: int = 2, M: int = 3, N: int = 12):
    task = torch.full((E, N), int(TaskState.AVAILABLE), dtype=torch.int64)
    robot = torch.full((E, M), int(RobotState.NEEDS_ASSIGNMENT), dtype=torch.int64)
    owner = torch.full((E, N), -1, dtype=torch.int64)
    failed = torch.zeros((E, M, N), dtype=torch.bool)
    completed = torch.zeros((E, M), dtype=torch.int64)
    reason = torch.full((E,), int(Reason.NONE), dtype=torch.int64)
    if M >= 1 and N >= 1:
        task[0, 0] = int(TaskState.CLAIMED)
        robot[0, 0] = int(RobotState.EXECUTING)
        owner[0, 0] = 0
    if N >= 2:
        failed[0, min(M - 1, 1), 1] = True
    if N >= 3 and M >= 2:
        task[0, N - 1] = int(TaskState.COMPLETED)
        completed[0, 1] = 1
    return task, robot, owner, failed, completed, reason


def _publication(
    *,
    E: int = 2,
    M: int = 3,
    N: int = 12,
    domain: object | None = None,
    serial: int = 7,
    episode: tuple[int, ...] | None = None,
    transition: tuple[int, ...] | None = None,
    tensors=None,
):
    actual_domain = object() if domain is None else domain
    task, robot, owner, failed, completed, reason = (
        _state_tensors(E=E, M=M, N=N) if tensors is None else tensors
    )
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
    episode_values = tuple(range(3, 3 + E)) if episode is None else episode
    transition_values = tuple(range(5, 5 + E)) if transition is None else transition
    view = LIFECYCLE.PublishedLifecycleView._create(
        state_snapshot=lifecycle_snapshot,
        episode_generation=torch.tensor(episode_values, dtype=torch.int64),
        transition_generation=torch.tensor(transition_values, dtype=torch.int64),
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
    return publication, actual_domain, lifecycle_snapshot, view


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


def _snapshot(*, E: int = 2, M: int = 3, N: int = 12, problem=None, tensors=None):
    publication, domain, lifecycle_snapshot, view = _publication(E=E, M=M, N=N, tensors=tensors)
    open_view, window = _open_view(domain)
    physical = _physical(problem, E=E, M=M, N=N)
    snapshot = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(
        current_publication=publication,
        current_open_window_view=open_view,
        physical_evidence=physical,
        scale_contract=_scale(M=M, N=N),
    )
    return snapshot, publication, open_view, window, physical, lifecycle_snapshot, view


def _layout(snapshot, *, actor: bool):
    values = snapshot.actor_block_layout if actor else snapshot.critic_block_layout
    return {item.name: item for item in values}


def _expect_failure(code: str, call: Callable[[], object]) -> None:
    try:
        call()
    except EVIDENCE.EventPolicyEvidenceError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    except SCHEMA.AssignmentEventProfileSchemaV2ContractError as exc:
        _assert(exc.failure_code == code, f"expected {code}, got {exc.failure_code}")
    else:
        raise AssertionError(f"expected failure {code}")


def test_exact_reference_shapes_and_dimensions() -> None:
    snapshot, _, _, _, _, _, _ = _snapshot()
    projector = EVIDENCE.get_event_policy_current_projector_descriptor_v2(
        scale_contract=_scale()
    )
    _assert(tuple(snapshot.actor_obs.shape) == (2, 3, 421), "actor shape")
    _assert(tuple(snapshot.semantic_share_obs.shape) == (2, 418), "semantic share shape")
    _assert(tuple(snapshot.runner_share_obs.shape) == (2, 3, 418), "runner share shape")
    _assert(snapshot.actor_obs.dtype is torch.float32, "actor dtype")
    _assert(snapshot.actor_obs.device == DEVICE, "actor device")
    _assert(snapshot.critic_projection_mode == EVIDENCE.CURRENT_POLICY_CRITIC_PROJECTION_V2, "critic mode")
    _assert(projector["actor_projection"]["dimension"] == 421, "projector actor descriptor")
    _assert(projector["critic_projection"]["dimension"] == 418, "projector critic descriptor")
    _assert(projector["public_runtime_integration"] is False, "runtime integration enabled")


def test_second_fixed_scale_oracle() -> None:
    snapshot, _, _, _, _, _, _ = _snapshot(E=3, M=2, N=4)
    _assert(tuple(snapshot.actor_obs.shape) == (3, 2, 145), "second actor shape")
    _assert(tuple(snapshot.semantic_share_obs.shape) == (3, 143), "second critic shape")
    _assert(tuple(snapshot.runner_share_obs.shape) == (3, 2, 143), "second runner shape")


def test_canonical_block_order_offsets_and_normalization() -> None:
    snapshot, _, _, _, physical, _, _ = _snapshot()
    descriptor = SCHEMA.build_assignment_event_profile_schema_v2_descriptor(scale_contract=_scale())
    for schema_name, layouts in (
        ("actor_schema", snapshot.actor_block_layout),
        ("critic_schema", snapshot.critic_block_layout),
    ):
        blocks = descriptor[schema_name]["blocks"]
        _assert(tuple(item.name for item in layouts) == tuple(block["name"] for block in blocks), "block names")
        _assert(tuple(item.order for item in layouts) == tuple(range(1, len(layouts) + 1)), "block order")
        _assert(layouts[0].start == 0, "first offset")
        _assert(all(left.stop == right.start for left, right in zip(layouts, layouts[1:])), "contiguous offsets")
        _assert(layouts[-1].stop == descriptor[schema_name]["dimension"], "final dimension")
    actor = snapshot.actor_obs
    blocks = _layout(snapshot, actor=True)
    physical_slice = actor[:, 0, blocks["global_robot_physical_state"].start:blocks["global_robot_physical_state"].stop]
    physical_table = physical_slice.reshape(2, 3, 16)
    _assert(torch.allclose(physical_table[..., :3], physical.base_pos / 12.0), "position normalization")
    _assert(torch.all(physical_table[..., 8] >= 0), "quaternion canonical sign")
    progress = actor[:, 0, blocks["episode_physical_progress_fraction"].start]
    _assert(torch.allclose(progress, torch.tensor((0.0, 0.1))), "episode progress normalization")


def test_identity_metadata_excluded_and_numerically_inert() -> None:
    physical = _physical()
    tensors = _state_tensors()
    publication_a, domain, _, _ = _publication(tensors=tensors, serial=10)
    publication_b, _, _, _ = _publication(tensors=tensors, domain=domain, serial=12, episode=(7, 8), transition=(9, 10))
    window_a, _ = _open_view(domain, serial=20)
    window_b, _ = _open_view(domain, serial=21)
    snapshot_a = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(current_publication=publication_a, current_open_window_view=window_a, physical_evidence=physical, scale_contract=_scale())
    snapshot_b = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(current_publication=publication_b, current_open_window_view=window_b, physical_evidence=physical, scale_contract=_scale())
    _assert(snapshot_a.identity is not snapshot_b.identity, "identity reused")
    _assert(snapshot_a.source_window_identity is not snapshot_b.source_window_identity, "window reused")
    _assert(torch.equal(snapshot_a.actor_obs, snapshot_b.actor_obs), "identity affected actor")
    _assert(torch.equal(snapshot_a.semantic_share_obs, snapshot_b.semantic_share_obs), "identity affected critic")
    numerical_names = {item.name for item in snapshot_a.actor_block_layout + snapshot_a.critic_block_layout}
    _assert(not numerical_names.intersection({"p2_publication_identity", "episode_generations", "transition_generations", "open_window_identity"}), "identity numerical block")


def test_lifecycle_truth_comes_from_p2_not_legacy_status() -> None:
    problem = _problem()
    problem["robot_status"].fill_(int(RobotState.UNAVAILABLE))
    problem["task_status"].fill_(int(TaskState.TEAM_INFEASIBLE))
    snapshot, _, _, _, _, _, _ = _snapshot(problem=problem)
    blocks = _layout(snapshot, actor=True)
    actor = snapshot.actor_obs
    robot_lifecycle = actor[:, 0, blocks["global_robot_lifecycle_state"].start:blocks["global_robot_lifecycle_state"].stop].reshape(2, 3, 5)
    task_lifecycle = actor[:, 0, blocks["task_lifecycle_state"].start:blocks["task_lifecycle_state"].stop].reshape(2, 12, 6)
    _assert(robot_lifecycle[0, 0, int(RobotState.EXECUTING)] == 1, "legacy robot status used")
    _assert(task_lifecycle[0, 0, int(TaskState.CLAIMED)] == 1, "legacy task status used")
    _assert(snapshot.provenance["physical_source"]["legacy_status_keys_excluded_from_lifecycle_truth"] == ("robot_status", "task_status"), "legacy exclusion provenance")


def test_current_owned_task_none_one_and_multiple_fail_closed() -> None:
    snapshot, _, _, _, _, _, _ = _snapshot()
    owned = snapshot.current_owned_task_id
    _assert(int(owned[0, 0]) == 0, "single ownership")
    _assert(int(owned[0, 1]) == 12, "none ownership")
    tensors = list(_state_tensors())
    tensors[0][0, 1] = int(TaskState.CLAIMED)
    tensors[2][0, 1] = 0
    _expect_failure("multiple_owned_tasks", lambda: _snapshot(tensors=tuple(tensors)))


def test_feasibility_and_geometric_cost_are_distinct() -> None:
    snapshot, _, _, _, _, _, _ = _snapshot()
    blocks = _layout(snapshot, actor=True)
    actor = snapshot.actor_obs
    feasible_start = blocks["explicit_physical_feasibility"].start
    cost_start = blocks["geometric_pair_ranking_cost"].start
    _assert(float(actor[0, 0, feasible_start]) == 0.0, "false feasibility lost")
    _assert(float(actor[0, 0, cost_start]) > 0.0, "finite ranking cost lost")
    problem = _problem()
    problem["cost_matrix"][0, 0, 0] = float("inf")
    _expect_failure("nonfinite_physical_evidence", lambda: _physical(problem))
    _assert(problem["feasible_mask"][0, 0, 0].item() is False, "cost changed feasibility")


def test_snapshot_is_detached_from_all_mutable_sources() -> None:
    problem = _problem()
    physical = _physical(problem)
    source_base = physical.base_pos
    problem["base_pos"].add_(1000.0)
    problem["feasible_mask"].logical_not_()
    problem["cost_matrix"].add_(1000.0)
    _assert(torch.equal(physical.base_pos, source_base), "problem aliases physical capture")
    publication, domain, lifecycle_snapshot, _ = _publication()
    open_view, _ = _open_view(domain)
    snapshot = EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(current_publication=publication, current_open_window_view=open_view, physical_evidence=physical, scale_contract=_scale())
    actor_before = snapshot.actor_obs
    share_before = snapshot.semantic_share_obs
    physical._base_pos.add_(500.0)
    lifecycle_snapshot._task_state.fill_(int(TaskState.TEAM_INFEASIBLE))
    returned = snapshot.actor_obs
    returned.zero_()
    runner = snapshot.runner_share_obs
    runner.zero_()
    _assert(torch.equal(snapshot.actor_obs, actor_before), "snapshot actor alias")
    _assert(torch.equal(snapshot.semantic_share_obs, share_before), "snapshot critic alias")
    _assert(bool(snapshot.actor_obs.any().item()), "returned actor mutates snapshot")
    _assert(bool(snapshot.runner_share_obs.any().item()), "runner transport alias")


def test_stale_identity_validation_fails_closed() -> None:
    snapshot, publication, open_view, _, _, _, lifecycle_view = _snapshot()
    snapshot.validate_current(current_publication=publication, current_open_window_view=open_view)
    other, domain, _, _ = _publication(serial=99)
    other_open, _ = _open_view(domain)
    _expect_failure("source_publication_mismatch", lambda: snapshot.validate_current(current_publication=other, current_open_window_view=other_open))
    old_episode = lifecycle_view._episode_generation
    object.__setattr__(lifecycle_view, "_episode_generation", old_episode + 1)
    _expect_failure("episode_generation_mismatch", lambda: snapshot.validate_current(current_publication=publication, current_open_window_view=open_view))
    object.__setattr__(lifecycle_view, "_episode_generation", old_episode)
    old_transition = lifecycle_view._transition_generation
    object.__setattr__(lifecycle_view, "_transition_generation", old_transition + 1)
    _expect_failure("transition_generation_mismatch", lambda: snapshot.validate_current(current_publication=publication, current_open_window_view=open_view))
    object.__setattr__(lifecycle_view, "_transition_generation", old_transition)
    wrong_open, _ = _open_view(publication.publication_identity._domain_identity, serial=500)
    _expect_failure("open_window_identity_mismatch", lambda: snapshot.validate_current(current_publication=publication, current_open_window_view=wrong_open))


def test_one_physical_read_and_one_sealed_projection_boundary() -> None:
    problem = _problem()
    snapshot, publication, open_view, window, _, _, _ = _snapshot(problem=problem)
    _assert(all(problem.reads.get(key) == 1 for key in EVIDENCE._PHYSICAL_PROBLEM_KEYS), f"physical reread: {problem.reads}")
    _assert(snapshot.source_publication is publication, "publication rebound")
    _assert(snapshot.source_window_identity is window, "window rebound")
    _assert(snapshot.provenance["actor_and_critic_share_exact_capture"] is True, "split capture")
    snapshot.validate_current(current_publication=publication, current_open_window_view=open_view)
    actor_common = _layout(snapshot, actor=True)
    critic_common = _layout(snapshot, actor=False)
    for name in critic_common:
        a = actor_common[name]
        c = critic_common[name]
        actor_value = snapshot.actor_obs[:, 0, a.start:a.stop]
        critic_value = snapshot.semantic_share_obs[:, c.start:c.stop]
        _assert(torch.equal(actor_value, critic_value), f"actor/critic split source: {name}")


def test_critic_is_global_state_not_actor_concat() -> None:
    snapshot, _, _, _, _, _, _ = _snapshot()
    actor_concat = snapshot.actor_obs.reshape(2, -1)
    _assert(actor_concat.shape[1] == 3 * 421, "actor concat control")
    _assert(snapshot.semantic_share_obs.shape[1] == 418, "critic width")
    _assert(snapshot.runner_share_obs.stride()[-1] == 1, "runner transport contiguous")
    _assert(torch.equal(snapshot.runner_share_obs[:, 0], snapshot.semantic_share_obs), "runner repeat")


def test_current_only_rejects_terminal_and_historical_inputs() -> None:
    tensors = list(_state_tensors())
    tensors[5].fill_(int(Reason.TIME_LIMIT))
    publication, domain, _, _ = _publication(tensors=tuple(tensors))
    open_view, _ = _open_view(domain)
    physical = _physical()
    _expect_failure(
        "terminal_evidence_unsupported",
        lambda: EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(
            current_publication=publication,
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=_scale(),
        ),
    )
    _expect_failure(
        "current_publication_type",
        lambda: EVIDENCE.capture_current_event_policy_evidence_snapshot_v2(
            current_publication=object(),
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=_scale(),
        ),
    )


def test_scope_static_oracle_and_protected_hashes() -> None:
    source = PATHS["evidence"].read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    _assert(not any(name.startswith(("omni", "isaaclab", "harl")) for name in imported), "forbidden runtime import")
    _assert("assignment_tick_generation" not in source, "tick restored")
    _assert("EventPolicyDecisionBundle" not in source, "I2 bundle implemented")
    _assert("available_actions" not in source, "DVM output implemented")
    for filename, expected in PROTECTED_HASHES.items():
        actual = hashlib.sha256((SCAN_SOURCE / filename).read_bytes()).hexdigest()
        _assert(actual == expected, f"protected file drift: {filename}")


def test_canonical_alias_and_isolated_import() -> None:
    alias = "assignment_event_policy_evidence_alias"
    spec = importlib.util.spec_from_file_location(alias, PATHS["evidence"])
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
for stem in ('assignment_profile_contract','assignment_lifecycle_transition_contract','assignment_event_contract','assignment_lifecycle_authority_runtime','assignment_initial_claim_runtime','assignment_lifecycle_transaction_runtime','assignment_interstep_claim_window_runtime','assignment_event_profile_schema_contract_v2','assignment_event_policy_evidence'): load(stem)
added=set(sys.modules)-before
print(json.dumps({{'canonical':package+'.assignment_event_policy_evidence' in sys.modules,'bare':'assignment_event_policy_evidence' not in sys.modules,'forbidden':not any(name.startswith(('omni','isaaclab.app','harl')) for name in added)}}))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run([sys.executable, "-c", child], cwd=temp_dir, capture_output=True, text=True, check=False)
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(all(payload.values()), f"isolation failed: {payload}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("exact_reference_shapes_and_dimensions", test_exact_reference_shapes_and_dimensions),
    ("second_fixed_scale_oracle", test_second_fixed_scale_oracle),
    ("canonical_block_order_offsets_and_normalization", test_canonical_block_order_offsets_and_normalization),
    ("identity_metadata_excluded_and_numerically_inert", test_identity_metadata_excluded_and_numerically_inert),
    ("lifecycle_truth_comes_from_p2_not_legacy_status", test_lifecycle_truth_comes_from_p2_not_legacy_status),
    ("current_owned_task_none_one_and_multiple_fail_closed", test_current_owned_task_none_one_and_multiple_fail_closed),
    ("feasibility_and_geometric_cost_are_distinct", test_feasibility_and_geometric_cost_are_distinct),
    ("snapshot_is_detached_from_all_mutable_sources", test_snapshot_is_detached_from_all_mutable_sources),
    ("stale_identity_validation_fails_closed", test_stale_identity_validation_fails_closed),
    ("one_physical_read_and_one_sealed_projection_boundary", test_one_physical_read_and_one_sealed_projection_boundary),
    ("critic_is_global_state_not_actor_concat", test_critic_is_global_state_not_actor_concat),
    ("current_only_rejects_terminal_and_historical_inputs", test_current_only_rejects_terminal_and_historical_inputs),
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
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {"suite": "assignment_phase_b2_i1_immutable_policy_evidence_current_projectors_pure", "passed": passed, "total": len(results), "results": results}
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
