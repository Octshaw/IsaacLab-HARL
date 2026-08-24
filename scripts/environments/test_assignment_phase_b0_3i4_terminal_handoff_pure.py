"""Pure B0-3I4 synchronous terminal-handoff regressions."""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from threading import Event, Thread
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
I3_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py"
SCAN_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
DOMAIN_PATH = SCAN_SOURCE / "assignment_event_profile_runtime_domain.py"
TRANSACTION_PATH = SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py"
ENV_PATH = SCAN_SOURCE / "scan_mobile_manipulator_env.py"


def _load_i3() -> Any:
    spec = importlib.util.spec_from_file_location("_b0_3i4_i3_helpers", I3_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load I3 helper suite")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


I3 = _load_i3()
DOMAIN = I3.DOMAIN
B02 = I3.B02
Reason = I3.Reason


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    operation: Callable[[], Any],
    *,
    code: str,
) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        _assert(getattr(exc, "failure_code", None) == code, f"wrong failure code: {exc}")
        return exc
    raise AssertionError(f"expected failure_code={code}")


def _terminal_domain(*, env_ids: tuple[int, ...], timeout_rows: tuple[bool, ...] | None = None) -> tuple[Any, Any]:
    domain = I3._domain(env_ids=env_ids, num_robots=2, num_tasks=2)
    I3._reset(domain)
    timeout = torch.tensor(
        timeout_rows if timeout_rows is not None else tuple(True for _ in env_ids),
        dtype=torch.bool,
    )
    outcome = domain.environment_port.finalize_physical_transition(
        I3._report(domain, timeout=timeout)
    )
    return domain, outcome


def _reset_rows(domain: Any, env_ids: tuple[int, ...]) -> Any:
    identity = domain.identity
    selected = I3._i(env_ids)
    with domain.environment_port.episode_rebuild(
        selected_env_ids=selected,
        initial_task_state=torch.full(
            (len(env_ids), identity.num_tasks),
            int(I3.TaskState.AVAILABLE),
            dtype=torch.int64,
        ),
        initial_robot_state=torch.full(
            (len(env_ids), identity.num_robots),
            int(I3.RobotState.NEEDS_ASSIGNMENT),
            dtype=torch.int64,
        ),
        initial_ownership=torch.full(
            (len(env_ids), identity.num_tasks), -1, dtype=torch.int64
        ),
    ) as rebuild:
        return rebuild.commit_physical_reset_complete()


def test_t1_exact_terminal_install() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61000,))
    key = outcome.terminal_keys[0]
    _assert(type(key) is B02._TerminalTransitionKey, "terminal key type")
    artifact = domain.terminal_observer_port().read_terminal(key)
    _assert(artifact.key is key or artifact.key.env_id == key.env_id, "key binding")
    _assert(artifact.result is outcome.result, "result identity")
    _assert(artifact.published_view is outcome.published_view, "view identity")
    _assert(artifact.termination_reason == int(Reason.TIME_LIMIT), "reason")
    _assert(artifact.truncated and not artifact.terminated, "done projection")
    _assert(artifact.optional_sidecar is None, "sidecar")
    return {"key": [key.env_id, key.episode_generation, key.transition_generation], "sidecar": None}


def test_t2_terminal_survives_episode_rebuild() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61100,))
    key = outcome.terminal_keys[0]
    rebuilt = _reset_rows(domain, (61100,))
    artifact = domain.terminal_observer_port().read_terminal(key)
    _assert(int(rebuilt.episode_generation[0]) == 1, "episode did not advance")
    _assert(artifact.key.env_id == 61100, "slot lost across reset")
    return {"terminal_episode": key.episode_generation, "current_episode": 1}


def test_t3_observer_repeatable_non_destructive() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61200,))
    key = outcome.terminal_keys[0]
    observer_a = domain.terminal_observer_port()
    observer_b = domain.terminal_observer_port()
    first = observer_a.read_terminal(key)
    second = observer_a.read_terminal(key)
    third = observer_b.read_terminal(key)
    _assert(first is second is third, "observer read was destructive or reconstructed")
    return {"observer_ports": 2, "reads": 3, "destructive": False}


def test_t4_designated_consumer_exact_ack() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61300,))
    key = outcome.terminal_keys[0]
    consumer = domain.terminal_consumer_port
    _assert(consumer.read_terminal(key).key.env_id == 61300, "consumer read")
    acknowledged = consumer.acknowledge_terminal(key)
    _assert(acknowledged.result is outcome.result, "ack artifact")
    domain.environment_port.assert_physical_step_allowed()
    return {"designated_consumers": 1, "acknowledged": True}


def test_t5_wrong_stale_duplicate_rejection() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61400,))
    key = outcome.terminal_keys[0]
    stale = B02._TerminalTransitionKey(key.env_id, key.episode_generation, key.transition_generation + 1)
    wrong = B02._TerminalTransitionKey(key.env_id + 1, key.episode_generation, key.transition_generation)
    observer = domain.terminal_observer_port()
    consumer = domain.terminal_consumer_port
    _expect_error(lambda: observer.read_terminal(stale), code="terminal_key_mismatch")
    _expect_error(lambda: observer.read_terminal(wrong), code="terminal_slot_empty")
    _expect_error(lambda: consumer.acknowledge_terminal(stale), code="terminal_key_mismatch")
    consumer.acknowledge_terminal(key)
    _expect_error(lambda: consumer.acknowledge_terminal(key), code="terminal_slot_empty")
    return {"wrong": True, "stale": True, "duplicate": True}


def test_t6_foreign_consumer_cannot_ack() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61500,))
    foreign = I3._domain(env_ids=(61510,), num_robots=2, num_tasks=2)
    I3._reset(foreign)
    key = outcome.terminal_keys[0]
    _expect_error(
        lambda: domain._coordinator._acknowledge_terminal(
            key,
            capability=foreign.terminal_consumer_port._capability,
        ),
        code="terminal_ack_capability",
    )
    _assert(domain.terminal_observer_port().read_terminal(key).key.env_id == 61500, "foreign ack mutated slot")
    return {"foreign_ack": "rejected", "slot_preserved": True}


def test_t7_observer_has_no_ack() -> dict[str, Any]:
    observer_surface = tuple(
        sorted(
            name for name, member in inspect.getmembers(DOMAIN._EventProfileTerminalObserverPort)
            if not name.startswith("_") and (inspect.isfunction(member) or isinstance(member, property))
        )
    )
    _assert(observer_surface == ("read_terminal",), f"observer surface {observer_surface}")
    return {"observer_surface": list(observer_surface)}


def test_t8_ack_frees_exactly_one_row() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61600, 61601), timeout_rows=(True, True))
    key0, key1 = outcome.terminal_keys
    domain.terminal_consumer_port.acknowledge_terminal(key0)
    _expect_error(domain.environment_port.assert_physical_step_allowed, code="terminal_ack_required")
    _expect_error(lambda: domain.terminal_observer_port().read_terminal(key0), code="terminal_slot_empty")
    _assert(domain.terminal_observer_port().read_terminal(key1).key.env_id == 61601, "other row removed")
    domain.terminal_consumer_port.acknowledge_terminal(key1)
    domain.environment_port.assert_physical_step_allowed()
    return {"row0_freed": True, "row1_preserved_until_ack": True}


def test_t9_occupied_rejects_before_consume() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(61700,))
    key = outcome.terminal_keys[0]
    _reset_rows(domain, (61700,))
    before = I3._ledger_counts(domain)
    _expect_error(
        lambda: domain.environment_port.finalize_physical_transition(
            I3._report(domain, timeout=torch.ones(1, dtype=torch.bool))
        ),
        code="terminal_slot_occupied",
    )
    _assert(I3._ledger_counts(domain) == before, "occupied slot consumed ledger")
    _assert(domain.terminal_observer_port().read_terminal(key).result is outcome.result, "occupied slot replaced")
    return {"ledger_before_after": list(before), "receipt_free": True}


def test_t10_install_failure_poison() -> dict[str, Any]:
    domain = I3._domain(env_ids=(61800,), num_robots=2, num_tasks=2)
    I3._reset(domain)
    domain._coordinator._test_control = B02._CoordinatorTestControl(fail_terminal_install=True)
    _expect_error(
        lambda: domain.environment_port.finalize_physical_transition(
            I3._report(domain, timeout=torch.ones(1, dtype=torch.bool))
        ),
        code="fatal_post_receipt_failure",
    )
    _assert(domain._coordinator.poisoned, "coordinator not poisoned")
    _assert(I3._ledger_counts(domain) == (1, 1, 1), "receipt/finalize counts")
    _expect_error(domain.current_read_port.read_current, code="coordinator_poisoned")
    return {"poisoned": True, "consume_issue_finalize": [1, 1, 1]}


def test_t11_publication_slot_atomic_visibility() -> dict[str, Any]:
    reached, release, read_before = Event(), Event(), Event()
    domain = I3._domain(env_ids=(61900,), num_robots=2, num_tasks=2)
    I3._reset(domain)
    domain._coordinator._test_control = B02._CoordinatorTestControl(
        after_publication_reached=reached,
        after_publication_release=release,
        read_before_lock=read_before,
    )
    report = I3._report(domain, timeout=torch.ones(1, dtype=torch.bool))
    outcomes: dict[str, Any] = {}
    errors: list[BaseException] = []

    def writer() -> None:
        try:
            outcomes["transition"] = domain.environment_port.finalize_physical_transition(report)
        except BaseException as exc:
            errors.append(exc)

    def reader() -> None:
        try:
            outcomes["view"] = domain.current_read_port.read_current()
        except BaseException as exc:
            errors.append(exc)

    writer_thread = Thread(target=writer)
    reader_thread = Thread(target=reader)
    writer_thread.start()
    try:
        _assert(reached.wait(10.0), "writer did not reach publication interlock")
        reader_thread.start()
        _assert(read_before.wait(10.0), "reader did not approach publication lock")
        _assert("view" not in outcomes, "reader observed view before slot install")
    finally:
        release.set()
        writer_thread.join(10.0)
        if reader_thread.ident is not None:
            reader_thread.join(10.0)
    _assert(not errors and not writer_thread.is_alive() and not reader_thread.is_alive(), f"thread failure {errors}")
    outcome = outcomes["transition"]
    artifact = domain.terminal_observer_port().read_terminal(outcome.terminal_keys[0])
    _assert(outcomes["view"].lifecycle_view is outcome.published_view, "current view mismatch")
    _assert(artifact.published_view is outcome.published_view, "slot/view not atomic")
    return {"reader_blocked": True, "sleep": False, "new_view_and_slot": True}


def test_t12_reset_current_and_historical_coexist() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(62000,))
    key = outcome.terminal_keys[0]
    rebuilt = _reset_rows(domain, (62000,))
    historical = domain.terminal_observer_port().read_terminal(key)
    _assert(rebuilt.result is None and int(rebuilt.episode_generation[0]) == 1, "current reset view")
    _assert(historical.result is outcome.result and historical.published_view is outcome.published_view, "history rewritten")
    return {"current_episode": 1, "historical_episode": 0, "coexist": True}


def test_t13_r3_blocks_before_next_step() -> dict[str, Any]:
    domain, _ = _terminal_domain(env_ids=(62100,))
    _expect_error(domain.environment_port.assert_physical_step_allowed, code="terminal_ack_required")
    return {"synchronous": True, "wait_poll_autoack": False}


def test_t14_ack_releases_r3() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(62200,))
    domain.terminal_consumer_port.acknowledge_terminal(outcome.terminal_keys[0])
    domain.environment_port.assert_physical_step_allowed()
    return {"ack_then_step_allowed": True}


def test_t15_one_blocked_row_blocks_full_domain() -> dict[str, Any]:
    domain, outcome = _terminal_domain(env_ids=(62300, 62301), timeout_rows=(True, False))
    _assert(outcome.terminal_keys[1] is None, "nonterminal row gained slot")
    _expect_error(domain.environment_port.assert_physical_step_allowed, code="terminal_ack_required")
    domain.terminal_consumer_port.acknowledge_terminal(outcome.terminal_keys[0])
    domain.environment_port.assert_physical_step_allowed()
    return {"blocked_rows": 1, "physical_batch_rows": 2, "full_domain_block": True}


def test_t16_no_sidecar_harl_or_readiness_flip() -> dict[str, Any]:
    transaction_source = TRANSACTION_PATH.read_text(encoding="utf-8")
    domain_source = DOMAIN_PATH.read_text(encoding="utf-8")
    env_source = ENV_PATH.read_text(encoding="utf-8")
    _assert("optional_sidecar" in transaction_source and "_optional_sidecar", "sidecar absence not explicit")
    _assert("assignment_harl_wrapper" not in transaction_source + domain_source, "HARL terminal transport wired")
    _assert("from harl" not in transaction_source.lower() + domain_source.lower(), "HARL import wired")
    _assert("require_assignment_profile_runtime_ready" not in env_source, "environment flipped readiness")
    _assert("acknowledge_terminal" not in inspect.getsource(DOMAIN._EventProfileLifecycleEnvironmentPort), "environment gained ack")
    profile = I3._event_profile()
    _assert(profile.runtime_readiness.value == "interface_only", "readiness changed")
    return {"sidecar": None, "harl_transport": False, "runtime_readiness": "interface_only"}


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("I4-T1_exact_terminal_install", test_t1_exact_terminal_install),
    ("I4-T2_terminal_survives_episode_rebuild", test_t2_terminal_survives_episode_rebuild),
    ("I4-T3_observer_repeatable_non_destructive", test_t3_observer_repeatable_non_destructive),
    ("I4-T4_designated_consumer_exact_ack", test_t4_designated_consumer_exact_ack),
    ("I4-T5_wrong_stale_duplicate_rejection", test_t5_wrong_stale_duplicate_rejection),
    ("I4-T6_foreign_consumer_cannot_ack", test_t6_foreign_consumer_cannot_ack),
    ("I4-T7_observer_has_no_ack", test_t7_observer_has_no_ack),
    ("I4-T8_ack_frees_exactly_one_row", test_t8_ack_frees_exactly_one_row),
    ("I4-T9_occupied_rejects_before_consume", test_t9_occupied_rejects_before_consume),
    ("I4-T10_install_failure_poison", test_t10_install_failure_poison),
    ("I4-T11_publication_slot_atomic_visibility", test_t11_publication_slot_atomic_visibility),
    ("I4-T12_reset_current_and_historical_coexist", test_t12_reset_current_and_historical_coexist),
    ("I4-T13_r3_blocks_before_next_step", test_t13_r3_blocks_before_next_step),
    ("I4-T14_ack_releases_r3", test_t14_ack_releases_r3),
    ("I4-T15_one_blocked_row_blocks_full_domain", test_t15_one_blocked_row_blocks_full_domain),
    ("I4-T16_no_sidecar_harl_or_readiness_flip", test_t16_no_sidecar_harl_or_readiness_flip),
)


def run_suite() -> dict[str, Any]:
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
    return {
        "status": "passed" if failed == 0 else "failed",
        "num_tests": len(TESTS),
        "passed": passed,
        "failed": failed,
        "tests": results,
        "evidence": {"groups": "I4-T1..I4-T16", "protocol": "synchronous_exact_key_ack"},
        "runtime_boundary": {
            "harl_terminal_transport": "deferred",
            "runtime_readiness": "interface_only",
            "training_playback_evaluation": "not_run",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
