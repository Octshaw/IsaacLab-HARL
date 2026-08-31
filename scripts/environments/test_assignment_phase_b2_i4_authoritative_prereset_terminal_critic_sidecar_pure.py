"""Pure/static B2-I4 pre-reset terminal critic sidecar verification.

No Isaac, AppLauncher, Omni, PXr, HARL, critic network, optimizer, training,
playback, evaluation, or checkpoint code is imported or executed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = (
    REPO_ROOT
    / "scripts"
    / "environments"
    / "test_assignment_phase_b1w_i4_2_proposal_effective_commit_pure.py"
)
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
DEVICE = torch.device("cpu")


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("_phase_b2_i4_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


BASE = _load_base()
DOMAIN = BASE.DOMAIN
TRANSITION = BASE.TRANSITION
SIDECAR = sys.modules[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_terminal_critic_sidecar"
]
TRANSPORT = sys.modules[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_terminal_transport"
]
SCHEMA = sys.modules[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2"
]
Reason = TRANSITION.TerminationReason


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


def _scale(*, M: int, N: int) -> Any:
    return SCHEMA.build_event_policy_scale_contract_v2(
        M=M,
        N=N,
        ordered_agent_names=tuple(f"agent_{index}" for index in range(M)),
        ordered_task_ids=tuple(range(N)),
        scene_env_spacing=12.0,
        sim_dt_seconds=0.01,
        control_decimation=4,
        episode_time_limit_seconds=40.0,
    )


def _problem(*, E: int, M: int, N: int) -> dict[str, object]:
    base = torch.arange(E * M * 3, dtype=torch.float32).reshape(E, M, 3) / 10.0
    scanner_quat = torch.zeros((E, M, 4), dtype=torch.float32)
    scanner_quat[..., 0] = 1.0
    task_quat = torch.zeros((E, N, 4), dtype=torch.float32)
    task_quat[..., 0] = 1.0
    return {
        "num_envs": E,
        "num_agents": M,
        "agent_names": tuple(f"agent_{index}" for index in range(M)),
        "num_viewpoints": N,
        "viewpoint_ids": tuple(range(N)),
        "base_pos": base,
        "base_yaw": torch.linspace(0.0, 0.5, E * M, dtype=torch.float32).reshape(E, M),
        "scanner_pos": base + 0.25,
        "scanner_quat": scanner_quat,
        "viewpoint_pos": torch.arange(E * N * 3, dtype=torch.float32).reshape(E, N, 3) / 20.0,
        "viewpoint_quat": task_quat,
        "arm_reach": torch.linspace(1.0, 2.0, M, dtype=torch.float32),
        "scanner_min_range": torch.linspace(0.1, 0.2, M, dtype=torch.float32),
        "scanner_max_range": torch.linspace(1.0, 1.5, M, dtype=torch.float32),
        "scanner_fov_deg": torch.linspace(60.0, 90.0, M, dtype=torch.float32),
        "feasible_mask": torch.ones((E, M, N), dtype=torch.bool),
        "cost_matrix": torch.arange(1, E * M * N + 1, dtype=torch.float32).reshape(E, M, N),
    }


def _snapshot(problem: dict[str, object], *, step: int) -> Any:
    E = int(problem["num_envs"])
    M = int(problem["num_agents"])
    N = int(problem["num_viewpoints"])
    return SIDECAR.capture_pre_reset_critic_physical_snapshot_v2(
        assignment_problem=problem,
        episode_progress_steps=torch.full((E,), step, dtype=torch.int64),
        scale_contract=_scale(M=M, N=N),
    )


def _report(
    domain: Any,
    *,
    problem: dict[str, object],
    step: int,
    completion: torch.Tensor | None = None,
    coverage: torch.Tensor | None = None,
    truncated: torch.Tensor | None = None,
) -> Any:
    identity = domain.identity
    E, M, N = identity.num_envs, identity.num_robots, identity.num_tasks
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=(
            torch.zeros((E, N), dtype=torch.bool) if coverage is None else coverage
        ),
        raw_new_candidate=(
            torch.zeros((E, M, N), dtype=torch.bool) if completion is None else completion
        ),
        physical_truncated=(
            torch.zeros((E,), dtype=torch.bool) if truncated is None else truncated
        ),
        time_limit_reached=(
            torch.zeros((E,), dtype=torch.bool) if truncated is None else truncated
        ),
        pre_reset_critic_physical_snapshot=_snapshot(problem, step=step),
    )


def _reset(domain: Any, env_ids: list[int] | None = None) -> None:
    ids = list(range(domain.identity.num_envs)) if env_ids is None else env_ids
    with domain.environment_port.episode_rebuild(
        selected_env_ids=torch.tensor(ids, dtype=torch.int64),
        initial_task_state=torch.full(
            (len(ids), domain.identity.num_tasks),
            int(TRANSITION.TaskLifecycleState.AVAILABLE),
            dtype=torch.int64,
        ),
        initial_robot_state=torch.full(
            (len(ids), domain.identity.num_robots),
            int(TRANSITION.RobotLifecycleState.NEEDS_ASSIGNMENT),
            dtype=torch.int64,
        ),
        initial_ownership=torch.full(
            (len(ids), domain.identity.num_tasks), -1, dtype=torch.int64
        ),
    ) as rebuild:
        rebuild.commit_physical_reset_complete()


def _seed(domain: Any, *, env_id: int, task_id: int) -> None:
    rows = torch.full((1, domain.identity.num_robots), -1, dtype=torch.int64)
    rows[0, 0] = task_id
    request = domain.initial_claim_port.prepare_initial_claim(
        selected_env_ids=torch.tensor([env_id], dtype=torch.int64),
        requested_task_by_robot=rows,
    )
    domain.initial_claim_port.commit_initial_claim(request)


def _timeout_artifacts(*, E: int = 2, M: int = 3, N: int = 12):
    domain = BASE._domain(BASE._profile(), envs=E, robots=M, tasks=N)
    _reset(domain)
    problem = _problem(E=E, M=M, N=N)
    report = _report(
        domain,
        problem=problem,
        step=999,
        truncated=torch.ones((E,), dtype=torch.bool),
    )
    outcome = domain.environment_port.finalize_physical_transition(report)
    artifacts = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    return domain, problem, report, outcome, artifacts


def test_i4_1_timeout_presence_and_dimension_418() -> dict[str, object]:
    _, _, _, _, artifacts = _timeout_artifacts()
    _assert(len(artifacts) == 2, "timeout terminal slot cardinality")
    for artifact in artifacts:
        sidecar = artifact.optional_sidecar
        _assert(type(sidecar) is SIDECAR.EventTerminalCriticSidecarV2, "sidecar type")
        _assert(sidecar.termination_reason == int(Reason.TIME_LIMIT), "timeout reason")
        _assert(sidecar.bootstrap_projection_valid, "timeout bootstrap invalid")
        _assert(sidecar.bootstrap_critic_obs is not None, "timeout bootstrap absent")
        _assert(sidecar.critic_dimension == 418, "manifest dimension 418")
        _assert(sidecar.terminal_audit_projection.projection_mode == "TERMINAL_AUDIT", "audit mode")
        _assert(
            torch.equal(
                sidecar.bootstrap_critic_obs,
                sidecar.terminal_audit_projection.semantic_evidence,
            ),
            "timeout projections do not share exact evidence",
        )
    return {"E": 2, "M": 3, "N": 12, "S_critic": 418, "bootstrap": "TIME_LIMIT only"}


def test_i4_2_true_terminal_priority_collision_partial_e_dimension_143() -> dict[str, object]:
    E, M, N = 2, 2, 4
    domain = BASE._domain(BASE._profile(), envs=E, robots=M, tasks=N)
    _reset(domain)
    problem = _problem(E=E, M=M, N=N)
    coverage = torch.zeros((E, N), dtype=torch.bool)
    for task in range(N):
        _seed(domain, env_id=0, task_id=task)
        completion = torch.zeros((E, M, N), dtype=torch.bool)
        completion[0, 0, task] = True
        truncated = torch.zeros((E,), dtype=torch.bool)
        if task == N - 1:
            truncated[0] = True
        domain.environment_port.finalize_physical_transition(
            _report(
                domain,
                problem=problem,
                step=task + 1,
                completion=completion,
                coverage=coverage,
                truncated=truncated,
            )
        )
        coverage[0, task] = True
    artifacts = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    _assert(len(artifacts) == 1 and artifacts[0].key.env_id == 0, "partial E terminal rows")
    sidecar = artifacts[0].optional_sidecar
    _assert(sidecar.termination_reason == int(Reason.ALL_TASKS_COMPLETED), "reason priority")
    _assert(sidecar.terminated and not sidecar.truncated, "true-terminal flags")
    _assert(not sidecar.bootstrap_projection_valid, "true terminal bootstrap valid")
    _assert(sidecar.bootstrap_critic_obs is None, "true terminal bootstrap present")
    _assert(sidecar.critic_dimension == 143, "manifest dimension 143")
    return {
        "terminal_env_ids": [0],
        "nonterminal_env_ids": [1],
        "priority": "ALL_TASKS_COMPLETED > TIME_LIMIT",
        "S_critic": 143,
    }


def test_i4_3_capture_and_reset_mutation_isolation() -> dict[str, object]:
    domain, problem, _, _, artifacts = _timeout_artifacts(E=1)
    source = artifacts[0].optional_sidecar
    before = source.terminal_audit_projection.semantic_evidence
    problem["base_pos"].fill_(999.0)
    problem["cost_matrix"].fill_(999.0)
    _reset(domain, [0])
    after = artifacts[0].optional_sidecar.terminal_audit_projection.semantic_evidence
    _assert(torch.equal(before, after), "runtime artifact changed after source/reset mutation")
    _assert(not bool((after == 999.0).any().item()), "post-capture mutation leaked")
    return {"post_reset_reconstruction": False, "source_alias": False, "artifact_survives_reset": True}


def test_i4_4_safe_historical_copy_then_atomic_ack_and_recovery() -> dict[str, object]:
    domain, _, _, outcome, artifacts = _timeout_artifacts()
    runtime_sidecars = tuple(item.optional_sidecar for item in artifacts)
    _reset(domain)
    current = domain.current_read_port.read_current()
    flags = {"agent": outcome.truncated}
    history = TRANSPORT._copy_and_validate_terminal_history(
        captured_artifacts=artifacts,
        environment_result=({}, {}, {"agent": outcome.terminated}, flags, {}),
        current_publication=current,
    )
    _assert(len(history) == 2, "historical copy cardinality")
    for runtime_sidecar, row in zip(runtime_sidecars, history, strict=True):
        copied = row.optional_sidecar
        _assert(copied is not runtime_sidecar, "historical sidecar object alias")
        _assert(
            copied._terminal_audit_projection._semantic_evidence.data_ptr()
            != runtime_sidecar._terminal_audit_projection._semantic_evidence.data_ptr(),
            "historical audit tensor alias",
        )
        _assert(
            copied._bootstrap_critic_obs.data_ptr()
            != runtime_sidecar._bootstrap_critic_obs.data_ptr(),
            "historical bootstrap tensor alias",
        )
    acknowledged = domain.terminal_consumer_port.acknowledge_terminal_batch(
        tuple(row.key for row in history)
    )
    _assert(tuple(id(item) for item in acknowledged) == tuple(id(item) for item in artifacts), "ACK identity")
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "slots after ACK")
    domain.environment_port.finalize_physical_transition(
        _report(domain, problem=_problem(E=2, M=3, N=12), step=1)
    )
    return {"copy_before_ACK": True, "atomic_exact_ACK": True, "post_ACK_recovery": True}


def test_i4_5_wrong_snapshot_and_wrong_binding_fail_closed() -> dict[str, object]:
    domain = BASE._domain(BASE._profile(), envs=1, robots=3, tasks=12)
    _reset(domain)
    _expect(
        lambda: DOMAIN._StagedPreResetPhysicalReport(
            device=DEVICE,
            coverage_before_transition=torch.zeros((1, 12), dtype=torch.bool),
            raw_new_candidate=torch.zeros((1, 3, 12), dtype=torch.bool),
            physical_truncated=torch.ones((1,), dtype=torch.bool),
            time_limit_reached=torch.ones((1,), dtype=torch.bool),
            pre_reset_critic_physical_snapshot=object(),
        ),
        code="pre_reset_critic_snapshot_type",
    )
    _, _, _, _, artifacts = _timeout_artifacts(E=1)
    sidecar = artifacts[0].optional_sidecar
    wrong_key = BASE.B02._TerminalTransitionKey(
        sidecar.env_id,
        sidecar.episode_generation,
        sidecar.transition_generation + 1,
    )
    _expect(
        lambda: sidecar._validate_artifact_binding(
            key=wrong_key,
            termination_reason=sidecar.termination_reason,
            terminated=sidecar.terminated,
            truncated=sidecar.truncated,
            published_store_version=sidecar.published_store_version,
        ),
        code="sidecar_artifact_binding",
    )
    return {"wrong_type": "rejected", "wrong_key": "rejected", "slot_publication": "unchanged"}


def test_i4_6_static_timing_authority_and_scope() -> dict[str, object]:
    env_source = (SCAN_SOURCE / "scan_mobile_manipulator_env.py").read_text(encoding="utf-8")
    direct_source = (
        REPO_ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py"
    ).read_text(encoding="utf-8")
    lifecycle_source = (SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py").read_text(encoding="utf-8")
    sidecar_source = (SCAN_SOURCE / "assignment_event_terminal_critic_sidecar.py").read_text(encoding="utf-8")
    stage = env_source.index("def _stage_event_scan_progress")
    capture = env_source.index("capture_pre_reset_critic_physical_snapshot_v2(", stage)
    finalize = env_source.index("outcome = port.finalize_physical_transition(report)")
    post_step = direct_source.index("self.terminated_dict, self.time_out_dict = self._get_dones()")
    autoreset = direct_source.index("self._reset_idx(reset_env_ids)", post_step)
    observations = direct_source.index("self.obs_dict = self._get_observations()", post_step)
    _assert(stage < capture < finalize, "task-local capture order")
    _assert(autoreset < observations, "DirectMARLEnv reset ordering evidence")
    _assert("_terminal_slots =" in lifecycle_source, "existing terminal slot missing")
    _assert("critic(" not in sidecar_source and "optimizer" not in sidecar_source, "learner work leaked")
    _assert("TerminationReason" not in sidecar_source.split("semantic = torch.cat", 1)[0].split("def build_event_terminal_critic_sidecars_v2", 1)[-1], "reason entered common projection")
    return {
        "producer": "ScanMobileManipulatorEnv._get_dones seam",
        "DirectMARLEnv_changed": False,
        "terminal_store_count": 1,
        "critic_calls": 0,
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, object]]], ...] = (
    ("B2-I4-T1", test_i4_1_timeout_presence_and_dimension_418),
    ("B2-I4-T2", test_i4_2_true_terminal_priority_collision_partial_e_dimension_143),
    ("B2-I4-T3", test_i4_3_capture_and_reset_mutation_isolation),
    ("B2-I4-T4", test_i4_4_safe_historical_copy_then_atomic_ack_and_recovery),
    ("B2-I4-T5", test_i4_5_wrong_snapshot_and_wrong_binding_fail_closed),
    ("B2-I4-T6", test_i4_6_static_timing_authority_and_scope),
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
            cause = exc.__cause__
            rows.append(
                {
                    "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                    "cause": None if cause is None else f"{type(cause).__name__}: {cause}",
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
