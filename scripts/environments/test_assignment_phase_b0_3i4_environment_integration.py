"""B0-3I4 environment hook audit with an optional focused headless smoke."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
ENV_PATH = SCAN_SOURCE / "scan_mobile_manipulator_env.py"
DOMAIN_PATH = SCAN_SOURCE / "assignment_event_profile_runtime_domain.py"
TRANSACTION_PATH = SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py"
WRAPPER_PATH = SCAN_SOURCE / "assignment_harl_wrapper.py"
FACADE_PATH = SCAN_SOURCE / "assignment_event_runtime_facade.py"
DIRECT_ENV_PATH = REPO_ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


ENV_SOURCE = ENV_PATH.read_text(encoding="utf-8")
DIRECT_SOURCE = DIRECT_ENV_PATH.read_text(encoding="utf-8")
ENV_TREE = ast.parse(ENV_SOURCE)
DIRECT_TREE = ast.parse(DIRECT_SOURCE)


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    return next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == name)


def _method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef:
    cls = _class(tree, class_name)
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == method_name)


def _segment(source: str, node: ast.AST) -> str:
    value = ast.get_source_segment(source, node)
    if value is None:
        raise AssertionError("missing AST source segment")
    return value


def _calls(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                names.append(child.func.attr)
            elif isinstance(child.func, ast.Name):
                names.append(child.func.id)
    return names


def test_e1_exact_profile_domain_transport() -> dict[str, Any]:
    init = _method(ENV_TREE, "ScanMobileManipulatorEnv", "__init__")
    source = _segment(ENV_SOURCE, init)
    _assert('kwargs.pop("resolved_assignment_profile", None)' in source, "profile transport missing")
    _assert('kwargs.pop("event_lifecycle_runtime_domain", None)' in source, "domain transport missing")
    _assert('kwargs.pop("event_admission_validation_port", None)' in source, "validation port transport missing")
    _assert("resolve_assignment_profile" not in source and "normalize_assignment_profile" not in source, "environment re-resolves profile")
    _assert("identity.profile is not resolved_assignment_profile" in source, "same-object profile gate missing")
    _assert(
        "is not event_lifecycle_runtime_domain.environment_admission_validation_port" in source,
        "same-domain validation capability gate missing",
    )
    return {"canonical_profile_same_object": True, "validation_port_same_domain": True, "parallel_resolver": False}


def test_e2_existing_routes_do_not_receive_domain() -> dict[str, Any]:
    init = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "__init__"))
    _assert("event_domain_on_existing_route" in init, "existing domain rejection missing")
    _assert("type(resolved_assignment_profile) is ResolvedEventGatedAssignmentProfile" in init, "exact event branch missing")
    return {"event_exact_type": True, "existing_domain": "rejected"}


def test_e3_zero_work_action_noise_gate() -> dict[str, Any]:
    init = _method(ENV_TREE, "ScanMobileManipulatorEnv", "__init__")
    source = _segment(ENV_SOURCE, init)
    noise = source.index("event_action_noise_not_supported")
    super_call = source.index("super().__init__")
    _assert(noise < super_call, "action-noise rejection occurs after environment construction")
    return {"action_noise": None, "rejection_before_super": True}


def test_e4_admission_validation_first_hook_statement() -> dict[str, Any]:
    method = _method(ENV_TREE, "ScanMobileManipulatorEnv", "_pre_physics_step")
    first = method.body[0]
    _assert(isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), "first hook statement is not a call")
    _assert(isinstance(first.value.func, ast.Attribute) and first.value.func.attr == "_validate_event_physical_step_entry", "Ak validation is not first")
    helper = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_validate_event_physical_step_entry"))
    _assert("validate_physical_step_entry_for_active_call" in helper, "active-call entry validation missing")
    return {"first_statement": "validate_event_physical_step_entry", "defensive_r3": "validation_port"}


def test_e5_direct_step_action_order_and_noise_boundary() -> dict[str, Any]:
    step = _segment(DIRECT_SOURCE, _method(DIRECT_TREE, "DirectMARLEnv", "step"))
    to_index = step.index("action.to(self.device)")
    noise_index = step.index("if self.cfg.action_noise_model")
    hook_index = step.index("self._pre_physics_step(actions)")
    _assert(to_index < noise_index < hook_index, "DirectMARLEnv action order changed")
    return {"direct_order": ["to_device", "noise", "pre_physics_step"], "event_noise_gate": "constructor"}


def test_e6_staged_detector_is_nonmutating() -> dict[str, Any]:
    method = _method(ENV_TREE, "ScanMobileManipulatorEnv", "_stage_event_scan_progress")
    assigned_self = []
    for node in ast.walk(method):
        targets: list[ast.AST] = []
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = list(getattr(node, "targets", ())) or [getattr(node, "target", None)]
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                assigned_self.append(target.attr)
    _assert(not assigned_self, f"staged detector mutates self: {assigned_self}")
    calls = _calls(method)
    _assert("_compute_scan_candidate" in calls and "_StagedPreResetPhysicalReport" in calls, "staging path incomplete")
    return {"self_mutations": [], "report": "immutable raw candidate+dwell evidence"}


def test_e7_authority_before_bookkeeping() -> dict[str, Any]:
    method = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_get_dones"))
    order = [
        method.index("_stage_event_scan_progress"),
        method.index("validate_physical_finalization_for_active_call"),
        method.index("finalize_physical_transition"),
        method.index("_commit_event_scan_progress"),
    ]
    _assert(order == sorted(order), "event done order differs from stage->Ak validation->authority->bookkeeping")
    _assert("report_post_authority_bookkeeping_failure" in method, "post-authority bookkeeping poison path missing")
    return {"order": ["stage", "authority_terminal_publish", "bookkeeping", "return_done"]}


def test_e8_authoritative_coverage_and_reward_evidence() -> dict[str, Any]:
    commit = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_commit_event_scan_progress"))
    _assert("outcome.coverage_after_transition" in commit, "coverage reconstructed outside authority")
    _assert("outcome.result.completed_tasks" in commit, "global reward evidence not authoritative")
    _assert("outcome.completion_signals" in commit, "own reward attribution missing")
    rewards = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_get_rewards"))
    for term in ("last_global_coverage_gain", "last_own_coverage_gain", "last_duplicate_scans", "last_reach_violation", "action_rate"):
        _assert(term in rewards, f"legacy reward term lost: {term}")
    return {"coverage_source": "outcome", "reward_formula_terms_preserved": 5}


def test_e9_authoritative_done_only() -> dict[str, Any]:
    method = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_get_dones"))
    event_branch = method.split("if port is not None:", 1)[1].split("# DirectMARLEnv", 1)[0]
    _assert("outcome.terminated" in event_branch and "outcome.truncated" in event_branch, "authoritative done missing")
    _assert("torch.all(self.viewpoints_covered" not in event_branch, "legacy done leaked into event branch")
    return {"terminated": "authority", "truncated": "authority"}


def test_e10_episode_rebuild_wraps_native_reset() -> dict[str, Any]:
    node = _method(ENV_TREE, "ScanMobileManipulatorEnv", "_reset_idx")
    first = node.body[0]
    _assert(isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), "reset first statement is not a call")
    _assert(isinstance(first.value.func, ast.Attribute) and first.value.func.attr == "_validate_event_reset_entry", "reset admission validation is not first")
    method = _segment(ENV_SOURCE, node)
    with_index = method.index("with port.episode_rebuild")
    native_index = method.index("super()._reset_idx(selected_env_ids)", with_index)
    buffers_index = method.index("self._reset_scan_task_buffers(selected_env_ids)", native_index)
    commit_index = method.index("rebuild.commit_physical_reset_complete()", buffers_index)
    _assert(with_index < native_index < buffers_index < commit_index, "reset transaction order")
    return {"order": ["validate_admission", "prepare", "native_reset", "task_buffers", "physical_complete"]}


def test_e11_legacy_branch_preserved() -> dict[str, Any]:
    dones = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_get_dones"))
    reset = _segment(ENV_SOURCE, _method(ENV_TREE, "ScanMobileManipulatorEnv", "_reset_idx"))
    _assert("self._update_scan_progress()" in dones, "legacy scan path removed")
    _assert("if port is None:" in reset and "super()._reset_idx(selected_env_ids)" in reset, "legacy reset path removed")
    return {"legacy_scan": "unchanged path retained", "legacy_reset": "direct native path retained"}


def test_e12_scope_readiness_and_transport_boundary() -> dict[str, Any]:
    wrapper = WRAPPER_PATH.read_text(encoding="utf-8")
    wrapper_tree = ast.parse(wrapper)
    composition = next(
        node
        for node in wrapper_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_compose_event_assignment_harl_wrapper"
    )
    composition_source = _segment(wrapper, composition)
    facade = FACADE_PATH.read_text(encoding="utf-8")
    facade_tree = ast.parse(facade)
    facade_methods = {
        node.name
        for node in _class(facade_tree, "EventAssignmentRuntimeFacade").body
        if isinstance(node, ast.FunctionDef)
    }
    domain = DOMAIN_PATH.read_text(encoding="utf-8")
    transaction = TRANSACTION_PATH.read_text(encoding="utf-8")
    _assert("require_assignment_profile_runtime_ready" not in ENV_SOURCE, "environment flips readiness")
    _assert("acknowledge_terminal" not in _segment(ENV_SOURCE, _class(ENV_TREE, "ScanMobileManipulatorEnv")), "environment owns ack")
    _assert("assignment_event_profile_runtime_domain" in wrapper, "I4-1 private domain composition missing")
    _assert("terminal_consumer_port=runtime_domain.terminal_consumer_port" in composition_source, "exact O1 composition missing")
    _assert("assignment_event_terminal_transport" in facade, "I4-3 historical transport missing")
    _assert(
        "_copy_and_validate_terminal_history" in facade
        and "acknowledge_terminal_artifacts" in facade,
        "I4-3 copy/ACK handoff missing",
    )
    _assert(
        not facade_methods.intersection(
            {
                "capture_pending_terminal_artifacts",
                "acknowledge_terminal_artifact",
                "acknowledge_terminal_artifacts",
            }
        ),
        "raw terminal capability exposed on facade",
    )
    _assert("capture_pending_terminal_artifacts" not in wrapper, "wrapper owns raw capture")
    _assert("AssignmentHarlWrapper" not in domain + transaction, "HARL terminal transport added")
    return {
        "runtime_readiness": "interface_only",
        "wrapper_harl_transport": "private_bounded_historical_DTO",
        "terminal_ack_transport": "private_i4_3_exact_batch",
        "environment_ack": False,
    }


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("ENV-T1_exact_profile_domain_transport", test_e1_exact_profile_domain_transport),
    ("ENV-T2_existing_routes_do_not_receive_domain", test_e2_existing_routes_do_not_receive_domain),
    ("ENV-T3_zero_work_action_noise_gate", test_e3_zero_work_action_noise_gate),
    ("ENV-T4_admission_validation_first_hook", test_e4_admission_validation_first_hook_statement),
    ("ENV-T5_direct_step_action_order", test_e5_direct_step_action_order_and_noise_boundary),
    ("ENV-T6_staged_detector_nonmutating", test_e6_staged_detector_is_nonmutating),
    ("ENV-T7_authority_before_bookkeeping", test_e7_authority_before_bookkeeping),
    ("ENV-T8_authoritative_coverage_reward", test_e8_authoritative_coverage_and_reward_evidence),
    ("ENV-T9_authoritative_done_only", test_e9_authoritative_done_only),
    ("ENV-T10_episode_rebuild_wraps_reset", test_e10_episode_rebuild_wraps_native_reset),
    ("ENV-T11_legacy_branch_preserved", test_e11_legacy_branch_preserved),
    ("ENV-T12_scope_readiness_transport", test_e12_scope_readiness_and_transport_boundary),
)


def run_static_suite() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = 0
    for name, operation in TESTS:
        try:
            evidence = operation()
        except BaseException as exc:
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            passed += 1
            results.append({"name": name, "status": "passed", "evidence": evidence})
    failed = len(TESTS) - passed
    return {"status": "passed" if failed == 0 else "failed", "num_tests": len(TESTS), "passed": passed, "failed": failed, "tests": results}


def run_headless_smoke() -> dict[str, Any]:
    """Construct event and legacy environments only after pure gates are green."""

    from isaaclab.app import AppLauncher

    app_launcher = AppLauncher(headless=True)
    simulation_app = app_launcher.app
    event_env = None
    legacy_env = None
    try:
        import gymnasium as gym
        import torch

        import isaaclab_tasks  # noqa: F401
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import (
            _EventProfileLifecycleDomainSpec,
            _EventProfileLifecycleRuntimeDomain,
        )
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transaction_runtime import _TerminalTransitionKey
        from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (
            AssignmentProfileName,
            AssignmentProfileResolutionOrigin,
            resolve_assignment_profile,
        )
        from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

        profile = resolve_assignment_profile(
            AssignmentProfileName.EVENT_GATED_LOCAL_MRTA,
            AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
        )
        cfg = ScanMobileManipulatorEnvCfg()
        cfg.scene.num_envs = 2
        device = torch.device(cfg.sim.device)
        domain = _EventProfileLifecycleRuntimeDomain(
            _EventProfileLifecycleDomainSpec(
                profile,
                device=device,
                env_ids=torch.arange(2, dtype=torch.int64, device=device),
                num_robots=len(cfg.possible_agents),
                num_tasks=len(cfg.viewpoint_poses),
            )
        )
        event_env = gym.make(
            "Isaac-Scan-Mobile-Manipulator-Direct-v0",
            cfg=cfg,
            resolved_assignment_profile=profile,
            event_lifecycle_runtime_domain=domain,
        )
        event_env.reset()
        raw = event_env.unwrapped
        _assert(tuple(domain.current_read_port.read_current().episode_generation.tolist()) == (0, 0), "initial reset generation")
        raw.episode_length_buf.fill_(raw.max_episode_length - 2)
        actions = {
            agent: torch.zeros((raw.num_envs, raw.cfg.action_spaces[agent]), device=raw.device)
            for agent in raw.cfg.possible_agents
        }
        _, _, _, truncated, _ = event_env.step(actions)
        _assert(all(bool(value.all().item()) for value in truncated.values()), "timeout not authoritative")
        _assert(tuple(domain.current_read_port.read_current().episode_generation.tolist()) == (1, 1), "autoreset rebuild")
        before_actions = {name: value.clone() for name, value in raw.actions.items()}
        blocked = False
        try:
            event_env.step(actions)
        except BaseException as exc:
            blocked = getattr(exc, "failure_code", None) == "terminal_ack_required"
        _assert(blocked, "R3 did not block next physical step")
        _assert(all(torch.equal(raw.actions[name], value) for name, value in before_actions.items()), "blocked step mutated actions")
        for env_id in range(2):
            domain.terminal_consumer_port.acknowledge_terminal(_TerminalTransitionKey(env_id, 0, 0))
        event_env.step(actions)
        event_env.close()
        event_env = None

        legacy_cfg = ScanMobileManipulatorEnvCfg()
        legacy_cfg.scene.num_envs = 2
        legacy_env = gym.make("Isaac-Scan-Mobile-Manipulator-Direct-v0", cfg=legacy_cfg)
        legacy_env.reset()
        legacy_raw = legacy_env.unwrapped
        legacy_actions = {
            agent: torch.zeros((legacy_raw.num_envs, legacy_raw.cfg.action_spaces[agent]), device=legacy_raw.device)
            for agent in legacy_raw.cfg.possible_agents
        }
        legacy_env.step(legacy_actions)
        return {
            "status": "passed",
            "event_num_envs": 2,
            "first_reset_episode": 0,
            "terminal_autoreset_episode": 1,
            "r3_zero_work": True,
            "legacy_smoke": True,
        }
    finally:
        if event_env is not None:
            event_env.close()
        if legacy_env is not None:
            legacy_env.close()
        simulation_app.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--headless-smoke", action="store_true")
    args = parser.parse_args()
    result = run_headless_smoke() if args.headless_smoke else run_static_suite()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
