"""Pure B1W-I3 terminal discovery/capture/ack and O1 integration suite.

No Isaac, AppLauncher, Omni, PXr, HARL, training, playback, or evaluation
module is imported or executed.
"""

from __future__ import annotations

import argparse
from dataclasses import FrozenInstanceError
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
I1_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py"
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"


def _load_i1() -> Any:
    spec = importlib.util.spec_from_file_location("_b1w_i3_i1_helpers", I1_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load B1W-I1 helper suite")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


I1 = _load_i1()
SYNC = I1.SYNC
DOMAIN = I1.DOMAIN
B02 = I1.B02
Phase = I1.Phase


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect(operation: Callable[[], Any], *, code: str | None = None) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError("expected failure")


def _o1(domain: Any, env: Any) -> Any:
    return SYNC.EventProfileSynchronousRuntimeCoordinator(
        environment=env,
        current_read_port=domain.current_read_port,
        production_claim_port=domain.production_claim_port,
        physical_step_admission_port=domain.physical_step_admission_port,
        standalone_reset_admission_port=domain.standalone_reset_admission_port,
        terminal_consumer_port=domain.terminal_consumer_port,
        fence_read_port=domain.interstep_fence_read_port,
    )


def _terminal_runtime(*, env_ids: tuple[int, ...] = (0,)) -> tuple[Any, Any, Any]:
    domain = I1._domain(env_ids=env_ids, robots=2, tasks=3)
    env = I1._FakeEnvironment(domain)
    coordinator = _o1(domain, env)
    coordinator.reset_environment()
    env.autoreset = True
    coordinator.step_environment(action_builder=lambda _env, assignment: assignment)
    fence = domain.interstep_fence_read_port.read()
    _assert(fence.phase is Phase.OPEN, "terminal Ak did not complete to OPEN")
    _assert(domain.current_read_port.read_current().result is None, "autoreset P2 not current")
    return domain, env, coordinator


def _neutral_snapshot(domain: Any) -> tuple[object, ...]:
    publication = domain.current_read_port.read_current()
    fence = domain.interstep_fence_read_port.read()
    return (
        publication,
        publication.publication_identity,
        publication.store_version,
        tuple(publication.episode_generation.tolist()),
        tuple(publication.transition_generation.tolist()),
        fence.phase,
        fence.window,
        fence.active_step,
        fence.active_reset,
        domain._coordinator.poisoned,
    )


def test_i3_t1_empty_capture() -> dict[str, Any]:
    domain = I1._domain()
    env = I1._FakeEnvironment(domain)
    coordinator = _o1(domain, env)
    first = coordinator.capture_pending_terminal_artifacts()
    second = coordinator.capture_pending_terminal_artifacts()
    _assert(type(first) is tuple and first == () and second == (), "empty capture is not ordinary")
    return {"capture": [], "repeatable": True}


def test_i3_t2_one_pending_repeatable_exact() -> dict[str, Any]:
    _, _, coordinator = _terminal_runtime()
    first = coordinator.capture_pending_terminal_artifacts()
    second = coordinator.capture_pending_terminal_artifacts()
    _assert(len(first) == 1 and first[0] is second[0], "capture reconstructed or consumed artifact")
    _assert(first[0].key is second[0].key, "capture reconstructed key")
    return {"key": [first[0].key.env_id, first[0].key.episode_generation, first[0].key.transition_generation]}


def test_i3_t3_multirow_deterministic_order() -> dict[str, Any]:
    _, _, coordinator = _terminal_runtime(env_ids=(9, 2, 7))
    artifacts = coordinator.capture_pending_terminal_artifacts()
    env_ids = [artifact.key.env_id for artifact in artifacts]
    _assert(env_ids == [2, 7, 9], f"capture order is not env-id ascending: {env_ids}")
    return {"env_ids": env_ids}


def test_i3_t4_capture_is_read_only_and_r3_remains() -> dict[str, Any]:
    domain, _, coordinator = _terminal_runtime()
    before = _neutral_snapshot(domain)
    artifact = coordinator.capture_pending_terminal_artifacts()[0]
    after = _neutral_snapshot(domain)
    _assert(after == before, "capture changed lifecycle/fence authority")
    _expect(
        lambda: domain.physical_step_admission_port.begin_physical_step_admission(),
        code="terminal_ack_required",
    )
    _assert(coordinator.capture_pending_terminal_artifacts()[0] is artifact, "R3 rejection removed slot")
    return {"neutral": True, "r3_still_blocked": True}


def test_i3_t5_exact_ack_neutrality() -> dict[str, Any]:
    domain, _, coordinator = _terminal_runtime()
    artifact = coordinator.capture_pending_terminal_artifacts()[0]
    before = _neutral_snapshot(domain)
    acknowledged = coordinator.acknowledge_terminal_artifact(artifact.key)
    after = _neutral_snapshot(domain)
    _assert(acknowledged is artifact and after == before, "ack changed P2/Store/window or artifact identity")
    _assert(coordinator.capture_pending_terminal_artifacts() == (), "exact ack did not remove exactly one slot")
    return {"ack_exact": True, "authority_neutral": True}


def test_i3_t6_wrong_stale_duplicate_ack() -> dict[str, Any]:
    _, _, coordinator = _terminal_runtime()
    artifact = coordinator.capture_pending_terminal_artifacts()[0]
    key = artifact.key
    stale = B02._TerminalTransitionKey(key.env_id, key.episode_generation, key.transition_generation + 1)
    wrong = B02._TerminalTransitionKey(key.env_id + 1, key.episode_generation, key.transition_generation)
    _expect(lambda: coordinator.acknowledge_terminal_artifact(stale), code="terminal_key_mismatch")
    _expect(lambda: coordinator.acknowledge_terminal_artifact(wrong), code="terminal_slot_empty")
    _assert(coordinator.capture_pending_terminal_artifacts()[0] is artifact, "bad ack changed slot")
    coordinator.acknowledge_terminal_artifact(key)
    _expect(lambda: coordinator.acknowledge_terminal_artifact(key), code="terminal_slot_empty")
    return {"wrong": "rejected", "stale": "rejected", "duplicate": "rejected"}


def test_i3_t7_g2_preserved() -> dict[str, Any]:
    domain, _, coordinator = _terminal_runtime()
    before = _neutral_snapshot(domain)
    envelope = domain.production_claim_port.prepare_production_initial_claim(
        selected_env_ids=I1._i((0,)),
        requested_task_by_robot=I1._i(((0, -1),)),
    )
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="terminal_slot_occupied",
    )
    _assert(_neutral_snapshot(domain) == before, "G2 rejection changed shared authority")
    _assert(len(coordinator.capture_pending_terminal_artifacts()) == 1, "G2 rejection removed terminal")
    return {"g2": "preserved", "window_open": True}


def test_i3_t8_preack_o1_r3_neutrality() -> dict[str, Any]:
    domain, env, coordinator = _terminal_runtime()
    before = _neutral_snapshot(domain)
    before_assignment = env.last_assignment
    _expect(
        lambda: coordinator.step_environment(action_builder=lambda _env, assignment: assignment),
        code="terminal_ack_required",
    )
    _assert(_neutral_snapshot(domain) == before, "pre-ack O1 attempt changed authority or poisoned")
    _assert(env.last_assignment is before_assignment, "pre-ack R3 reached fake environment work")
    return {"r3": "rejected_before_Ak", "poisoned": False}


def test_i3_t9_postack_retry_and_nonterminal_completion() -> dict[str, Any]:
    domain, env, coordinator = _terminal_runtime()
    key = coordinator.capture_pending_terminal_artifacts()[0].key
    coordinator.acknowledge_terminal_artifact(key)
    env.autoreset = False
    before_window = domain.interstep_fence_read_port.read().window
    coordinator.step_environment(action_builder=lambda _env, assignment: assignment)
    fence = domain.interstep_fence_read_port.read()
    current = domain.current_read_port.read_current()
    _assert(fence.phase is Phase.OPEN and fence.window is not before_window, "post-ack step stranded Ak")
    _assert(current.result is not None and not bool(current.terminated.any()) and not bool(current.truncated.any()), "post-ack fake step not nonterminal")
    _assert(coordinator.capture_pending_terminal_artifacts() == (), "post-ack nonterminal step created terminal")
    return {"postack_r3": "passed", "next_step": "nonterminal_complete", "open": True}


def test_i3_t10_artifact_immutability_and_no_alias() -> dict[str, Any]:
    _, _, coordinator = _terminal_runtime()
    artifact = coordinator.capture_pending_terminal_artifacts()[0]
    coverage = artifact.coverage_after_transition
    coverage.fill_(True)
    _assert(not torch.equal(coverage, artifact.coverage_after_transition), "coverage accessor aliases stored artifact")
    _expect(lambda: setattr(artifact, "_terminated", False))
    _expect(lambda: setattr(artifact.key, "env_id", 999))
    return {"frozen": True, "coverage_no_alias": True, "frozen_error": FrozenInstanceError.__name__}


def test_i3_t11_cross_domain_consumer_rejected() -> dict[str, Any]:
    a, b = I1._domain(), I1._domain(env_ids=(10,))
    env = I1._FakeEnvironment(a)
    _expect(
        lambda: SYNC.EventProfileSynchronousRuntimeCoordinator(
            environment=env,
            current_read_port=a.current_read_port,
            production_claim_port=a.production_claim_port,
            physical_step_admission_port=a.physical_step_admission_port,
            standalone_reset_admission_port=a.standalone_reset_admission_port,
            terminal_consumer_port=b.terminal_consumer_port,
        ),
        code="coordinator_domain_identity",
    )
    return {"foreign_consumer": "rejected"}


def test_i3_t12_capability_confinement() -> dict[str, Any]:
    consumer_surface = tuple(
        sorted(
            name
            for name, member in inspect.getmembers(DOMAIN._EventProfileTerminalConsumerPort)
            if not name.startswith("_") and (inspect.isfunction(member) or isinstance(member, property))
        )
    )
    _assert(
        consumer_surface == (
            "acknowledge_terminal",
            "acknowledge_terminal_batch",
            "capture_pending_terminal_artifacts",
            "domain_identity",
            "read_terminal",
        ),
        f"consumer surface widened: {consumer_surface}",
    )
    o1_fields = tuple(SYNC.EventProfileSynchronousRuntimeCoordinator.__dataclass_fields__)
    _assert("_terminal_consumer_port" in o1_fields, "O1 lacks designated consumer")
    _assert(not any(name in o1_fields for name in ("_domain", "_store", "_terminal_cache", "_terminal_slots")), "O1 retained forbidden authority/cache")
    return {"consumer_surface": list(consumer_surface), "o1_terminal_cache": False}


def test_i3_t13_no_second_state_lock_or_tick_static() -> dict[str, Any]:
    transaction = (SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py").read_text(encoding="utf-8")
    domain = (SCAN_SOURCE / "assignment_event_profile_runtime_domain.py").read_text(encoding="utf-8")
    synchronous = (SCAN_SOURCE / "assignment_event_profile_synchronous_runtime.py").read_text(encoding="utf-8")
    _assert("self._terminal_slots: dict[int, _TerminalHandoffArtifact] = {}" in transaction, "canonical slot store missing")
    capture_body = transaction[transaction.index("def _capture_pending_terminal_artifacts"):transaction.index("def _acknowledge_terminal", transaction.index("def _capture_pending_terminal_artifacts"))]
    _assert("with self._publication_lock" in capture_body and "sorted(self._terminal_slots.items())" in capture_body, "capture does not use the canonical lock/store")
    _assert("Lock(" not in synchronous and "RLock(" not in synchronous, "O1 added a mutex")
    _assert("terminal_cache" not in synchronous and "assignment_tick" not in synchronous and "terminal_tick" not in synchronous, "O1 added cache/tick authority")
    _assert(domain.count("_terminal_consumer_port: _EventProfileTerminalConsumerPort") == 1, "domain gained second terminal consumer field")
    return {"slot_stores": 1, "new_locks": 0, "new_ticks": 0}


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I3-T1_empty_capture", test_i3_t1_empty_capture),
    ("I3-T2_one_pending_repeatable", test_i3_t2_one_pending_repeatable_exact),
    ("I3-T3_multirow_order", test_i3_t3_multirow_deterministic_order),
    ("I3-T4_capture_read_only", test_i3_t4_capture_is_read_only_and_r3_remains),
    ("I3-T5_ack_neutrality", test_i3_t5_exact_ack_neutrality),
    ("I3-T6_bad_ack", test_i3_t6_wrong_stale_duplicate_ack),
    ("I3-T7_g2", test_i3_t7_g2_preserved),
    ("I3-T8_preack_r3", test_i3_t8_preack_o1_r3_neutrality),
    ("I3-T9_postack_recovery", test_i3_t9_postack_retry_and_nonterminal_completion),
    ("I3-T10_immutability", test_i3_t10_artifact_immutability_and_no_alias),
    ("I3-T11_cross_domain", test_i3_t11_cross_domain_consumer_rejected),
    ("I3-T12_capability", test_i3_t12_capability_confinement),
    ("I3-T13_no_second_state", test_i3_t13_no_second_state_lock_or_tick_static),
)


def run_suite() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for name, test in TESTS:
        try:
            evidence = test()
        except BaseException as exc:
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"name": name, "status": "passed", "evidence": evidence})
    passed = sum(item["status"] == "passed" for item in results)
    return {
        "status": "passed" if passed == len(TESTS) else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": len(TESTS) - passed,
        "tests": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.json else json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
