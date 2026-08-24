"""Pure/static B1W-I4-3 terminal copy and atomic batch ACK proof.

No Isaac, AppLauncher, Omni, PXr, HARL, training, playback, or evaluation code
is imported or executed.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = REPO_ROOT / "scripts" / "environments" / "test_assignment_phase_b1w_i4_2_proposal_effective_commit_pure.py"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("_phase_b1w_i4_2_fixture", BASE_PATH)
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
B02 = BASE.B02
DOMAIN = BASE.DOMAIN
FACADE = BASE.FACADE
SYNC = BASE.SYNC
TRANSPORT = sys.modules[
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_terminal_transport"
]
Phase = BASE.Phase
Key = B02._TerminalTransitionKey
Row = TRANSPORT.EventTerminalHistoricalRow


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect(operation: Callable[[], Any], *, code: str | None = None) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure: {exc}")
        return exc
    raise AssertionError("expected failure")


def _direct_terminal_slots(
    *,
    envs: int = 2,
) -> tuple[Any, Any, Any, Any, tuple[Any, ...]]:
    wrapper, raw, _, domain = BASE._compose(envs=envs)
    wrapper.reset()
    raw.terminal_next = True
    receipt = wrapper._event_runtime_facade._runtime.step_environment_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    artifacts = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    _assert(len(artifacts) == envs, "terminal fixture slot cardinality")
    return wrapper, raw, domain, receipt, artifacts


def _slot_identities(domain: Any) -> tuple[int, ...]:
    return tuple(
        id(item) for item in domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    )


def _bad_second_key(artifacts: tuple[Any, ...]) -> tuple[Any, ...]:
    second = artifacts[1].key
    return (
        artifacts[0].key,
        Key(second.env_id, second.episode_generation, second.transition_generation + 1),
    )


def test_t1_atomic_batch_success_e2() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    returned = domain.terminal_consumer_port.acknowledge_terminal_batch(
        (artifacts[1].key, artifacts[0].key)
    )
    _assert(returned[0] is artifacts[0] and returned[1] is artifacts[1], "canonical identity")
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "slots remain")
    return {"E": 2, "returned_envs": [item.key.env_id for item in returned], "slot_count": 0}


def test_t2_wrong_second_key_all_retained() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    before = _slot_identities(domain)
    _expect(
        lambda: domain.terminal_consumer_port.acknowledge_terminal_batch(_bad_second_key(artifacts)),
        code="terminal_key_mismatch",
    )
    _assert(_slot_identities(domain) == before, "wrong key removed/reinserted a slot")
    return {"valid_first": True, "wrong_second": True, "exact_slots_retained": True}


def test_t3_duplicate_key_all_retained() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    before = _slot_identities(domain)
    _expect(
        lambda: domain.terminal_consumer_port.acknowledge_terminal_batch(
            (artifacts[0].key, artifacts[0].key)
        ),
        code="terminal_batch_duplicate",
    )
    _assert(_slot_identities(domain) == before, "duplicate batch mutated slots")
    return {"duplicate_rejected": True, "exact_slots_retained": True}


def test_t4_missing_slot_all_retained() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    before = _slot_identities(domain)
    missing = Key(99, artifacts[1].key.episode_generation, artifacts[1].key.transition_generation)
    _expect(
        lambda: domain.terminal_consumer_port.acknowledge_terminal_batch(
            (artifacts[0].key, missing)
        ),
        code="terminal_slot_empty",
    )
    _assert(_slot_identities(domain) == before, "missing batch mutated valid slot")
    return {"missing_env": 99, "exact_slots_retained": True}


def test_t5_foreign_consumer_rejected() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    foreign = BASE._domain(BASE._profile(), envs=2)
    before = _slot_identities(domain)
    _expect(
        lambda: domain._coordinator._acknowledge_terminal_batch(
            tuple(item.key for item in artifacts),
            capability=foreign.terminal_consumer_port._capability,
        ),
        code="terminal_batch_ack_capability",
    )
    _assert(_slot_identities(domain) == before, "foreign consumer mutated slots")
    return {"foreign_domain": "rejected", "slot_mutation": False}


def test_t6_empty_batch_noop() -> dict[str, object]:
    wrapper, _, _, domain = BASE._compose()
    wrapper.reset()
    current = domain.current_read_port.read_current()
    window = domain.interstep_fence_read_port.read().window
    returned = domain.terminal_consumer_port.acknowledge_terminal_batch(())
    _assert(returned == (), "empty batch return")
    _assert(domain.current_read_port.read_current() is current, "empty batch P2")
    _assert(domain.interstep_fence_read_port.read().window is window, "empty batch window")
    return {"return": [], "P2_window": "unchanged"}


def test_t7_single_key_ack_preserved() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots(envs=1)
    returned = domain.terminal_consumer_port.acknowledge_terminal(artifacts[0].key)
    _assert(returned is artifacts[0], "single-key identity changed")
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "single slot")
    return {"single_key": "preserved", "exact_identity": True}


def test_t8_capture_repeat_exact_identity() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    repeated = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
    _assert(all(left is right for left, right in zip(artifacts, repeated, strict=True)), "capture identity")
    return {"order": [item.key.env_id for item in artifacts], "repeat_identity": True}


def test_t9_historical_copy_no_alias() -> dict[str, object]:
    _, _, domain, receipt, artifacts = _direct_terminal_slots()
    history = TRANSPORT._copy_and_validate_terminal_history(
        captured_artifacts=artifacts,
        environment_result=receipt.environment_result,
        current_publication=domain.current_read_port.read_current(),
    )
    _assert(all(type(row) is Row for row in history), "historical type")
    result_row = artifacts[0].result.to_mapping()
    source_tensors = {
        "coverage_after_transition": artifacts[0].coverage_after_transition,
        "completion_count": artifacts[0].published_view.lifecycle_state.completion_count[0],
        **{
            name: result_row[name][0]
            for name in (
                "completed_tasks",
                "released_tasks",
                "new_failed_pairs",
                "updated_failed_pairs",
                "new_team_infeasible_tasks",
                "updated_task_state",
                "updated_robot_state",
                "updated_ownership",
            )
        },
    }
    for name, source in source_tensors.items():
        copied = getattr(history[0], name)
        if source.numel():
            _assert(source.data_ptr() != copied.data_ptr(), f"{name} alias")
        copied.fill_(7)
        _assert(not torch.equal(copied, getattr(history[0], name)), f"{name} getter alias")
    _assert(history[0] is not artifacts[0], "raw artifact retained")
    return {
        "rows": 2,
        "tensor_fields_checked": len(source_tensors),
        "tensor_alias": False,
        "raw_artifact_reference": False,
    }


def test_t10_full_copy_precedes_ack() -> dict[str, object]:
    _, _, domain, receipt, artifacts = _direct_terminal_slots()
    history = TRANSPORT._copy_and_validate_terminal_history(
        captured_artifacts=artifacts,
        environment_result=receipt.environment_result,
        current_publication=domain.current_read_port.read_current(),
    )
    _assert(len(history) == 2, "full copy")
    _assert(_slot_identities(domain) == tuple(id(item) for item in artifacts), "copy acknowledged")
    return {"copied": 2, "slots_before_ACK": 2}


def test_t11_copy_failure_no_ack_r3_retained() -> dict[str, object]:
    _, _, domain, receipt, artifacts = _direct_terminal_slots()
    result = receipt.environment_result
    false_flags = {
        key: torch.zeros_like(value) for key, value in result[3].items()
    }
    inconsistent = (result[0], result[1], result[2], false_flags, result[4])
    before = _slot_identities(domain)
    _expect(
        lambda: TRANSPORT._copy_and_validate_terminal_history(
            captured_artifacts=artifacts,
            environment_result=inconsistent,
            current_publication=domain.current_read_port.read_current(),
        ),
        code="terminal_return_capture_mismatch",
    )
    _assert(_slot_identities(domain) == before, "copy failure acknowledged")
    _expect(
        lambda: domain.physical_step_admission_port.begin_physical_step_admission(),
        code="terminal_ack_required",
    )
    return {"ACK": 0, "R3": "retained", "slot_identity": "unchanged"}


def test_t12_terminal_facade_success_path() -> dict[str, object]:
    wrapper, raw, _, domain = BASE._compose(envs=2)
    wrapper.reset()
    raw.terminal_next = True
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(len(result.terminal_historical_payload) == 2, "terminal history absent")
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "ACK absent")
    view = domain.interstep_fence_read_port.read()
    _assert(view.phase is Phase.OPEN and not domain._coordinator.poisoned, "post ACK state")
    return {"history": 2, "slots": 0, "fence": "OPEN", "poison": False}


def test_t13_historical_current_p2_separation() -> dict[str, object]:
    wrapper, raw, _, domain = BASE._compose()
    wrapper.reset()
    raw.terminal_next = True
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    historical = result.terminal_historical_payload[0]
    current = result.current_publication
    _assert(historical.episode_generation == 0, "historical episode")
    _assert(current.episode_generation.tolist() == [1], "current episode")
    _assert(current.result is None, "current P2 retained terminal result")
    _assert(historical.termination_reason == int(BASE.TRANSITION.TerminationReason.TIME_LIMIT), "reason")
    return {"historical_episode": 0, "current_episode": 1, "current_result": None}


def test_t14_ack_neutrality() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    current = domain.current_read_port.read_current()
    window = domain.interstep_fence_read_port.read().window
    before = (
        current.store_version,
        current.episode_generation.tolist(),
        current.transition_generation.tolist(),
        domain._coordinator.poisoned,
    )
    domain.terminal_consumer_port.acknowledge_terminal_batch(tuple(item.key for item in artifacts))
    after = domain.current_read_port.read_current()
    _assert(after is current and domain.interstep_fence_read_port.read().window is window, "authority mutation")
    _assert(
        (after.store_version, after.episode_generation.tolist(), after.transition_generation.tolist(), domain._coordinator.poisoned) == before,
        "ACK non-neutral",
    )
    return {"only_mutation": "terminal_slot_occupancy", "P2_window_poison": "unchanged"}


def test_t15_wrapper_payload_bounded_and_cache_clear() -> dict[str, object]:
    wrapper, raw, _, _ = BASE._compose()
    wrapper.reset()
    wrapper.last_assignment_proposal = BASE._i(((4, 4, 4),))
    wrapper.last_effective_assignment = BASE._i(((4, 4, 4),))
    raw.terminal_next = True
    terminal_result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(wrapper.last_assignment_proposal is None, "proposal cache survived autoreset")
    _assert(wrapper.last_effective_assignment is None, "effective cache survived autoreset")
    raw.terminal_next = False
    next_result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(wrapper._last_event_facade_step_result is next_result, "last result not replaced")
    _assert(next_result.terminal_historical_payload == (), "history accumulated")
    _assert(len(terminal_result.terminal_historical_payload) == 1, "value lifetime damaged")
    return {"wrapper_queue": False, "next_history": 0, "stale_caches": 0}


def test_t16_proposal_route_terminal_handoff() -> dict[str, object]:
    wrapper, raw, _, domain = BASE._compose()
    wrapper.reset()
    decision = BASE._decision(wrapper)
    raw.terminal_next = True
    result = BASE._step(wrapper, decision, [[4, 5, 5]])
    _assert(result.claim_artifact is not None, "proposal claim absent")
    _assert(len(result.terminal_historical_payload) == 1, "proposal terminal history")
    _assert(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), "proposal ACK")
    _assert(result.admitted_effective_assignment.tolist() == [[4, -1, -1]], "Ak source")
    return {"M1_artifact": 1, "history": 1, "slots": 0, "Ak": [4, -1, -1]}


def test_t17_continuation_terminal_current_observation() -> dict[str, object]:
    wrapper, raw, _, _ = BASE._compose()
    wrapper.reset()
    raw.terminal_next = True
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    returned_obs = result.environment_result[0]
    expected_obs = raw._obs()
    _assert(all(torch.equal(returned_obs[key], expected_obs[key]) for key in returned_obs), "current obs")
    _assert(result.terminal_historical_payload[0].episode_generation == 0, "history lifetime")
    return {"raw_obs": "post-reset current", "history": "previous terminal"}


def test_t18_post_ack_next_step_recovery() -> dict[str, object]:
    wrapper, raw, _, domain = BASE._compose()
    wrapper.reset()
    raw.terminal_next = True
    wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    first = domain.interstep_fence_read_port.read().window
    raw.terminal_next = False
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    view = domain.interstep_fence_read_port.read()
    _assert(result.terminal_historical_payload == (), "recovery terminal")
    _assert(view.phase is Phase.OPEN and view.window is not first, "recovery window")
    _assert(not domain._coordinator.poisoned, "recovery poison")
    return {"R3": "passed", "next_window": "OPEN", "poison": False}


def test_t19_public_event_step_still_blocked() -> dict[str, object]:
    wrapper, _, view, _ = BASE._compose()
    wrapper.reset()
    _expect(lambda: wrapper.step(BASE._actions([[4, 5, 5]])))
    _assert(view.direct_step_calls == 0, "public event step reached raw env")
    return {"public_step": "blocked", "obs_mask_DVM": "absent", "raw_step": 0}


def test_t20_optional_sidecar_none_no_synthesis() -> dict[str, object]:
    wrapper, raw, _, _ = BASE._compose()
    wrapper.reset()
    raw.terminal_next = True
    result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    row = result.terminal_historical_payload[0]
    _assert(row.optional_sidecar is None, "critic sidecar synthesized")
    source = BASE.PATHS["package_init"].read_text(encoding="utf-8")
    _assert("assignment_event_terminal_transport" not in source, "terminal module exported")
    _assert(TRANSPORT.__all__ == (), "terminal public exports")
    return {"optional_sidecar": None, "critic": "deferred", "public_exports": 0}


def test_t21_single_publication_static_audit() -> dict[str, object]:
    path = BASE.PATHS["b02"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    method = next(
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_acknowledge_terminal_batch"
    )
    publications = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "_terminal_slots"
            for target in node.targets
        )
    ]
    forbidden = [
        node for node in ast.walk(method)
        if isinstance(node, ast.Delete)
        or (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"pop", "popitem"}
        )
    ]
    _assert(len(publications) == 1 and not forbidden, "batch publication is sequential")
    terminal_source = (BASE.SCAN_SOURCE / "assignment_event_terminal_transport.py").read_text(encoding="utf-8")
    terminal_tree = ast.parse(terminal_source)
    locks = {
        node.func.id for node in ast.walk(terminal_tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in {"Lock", "RLock", "Condition", "Semaphore"}
    }
    _assert(not locks and "_terminal_slots" not in terminal_source, "second authority")
    return {"slot_map_publications": 1, "pop_delete": 0, "new_locks": 0}


def test_t22_default_off_profiles_isolated() -> dict[str, object]:
    profiles = []
    for name in (
        "legacy",
        "lifecycle_contract_c",
        "lifecycle_ablation",
        "diagnostics_hidden_state",
    ):
        profile = BASE._profile(BASE.PROFILE.AssignmentProfileName(name))
        wrapper = BASE.WRAPPER.AssignmentHarlWrapper(
            BASE._LegacyEnvironment(name),
            resolved_assignment_profile=profile,
            profile_resolution_origin=profile.resolution_origin,
        )
        _assert(wrapper._event_runtime_facade is None, f"event facade leaked to {name}")
        _assert(
            vars(wrapper).get("_last_event_facade_step_result") is None,
            f"terminal result leaked to {name}",
        )
        profiles.append(name)
    return {"profiles": profiles, "event_facades": 0, "terminal_DTOs": 0}


def test_t23_malformed_batch_type_no_mutation() -> dict[str, object]:
    _, _, domain, _, artifacts = _direct_terminal_slots()
    before = _slot_identities(domain)
    _expect(
        lambda: domain.terminal_consumer_port.acknowledge_terminal_batch(  # type: ignore[arg-type]
            [item.key for item in artifacts]
        ),
        code="terminal_batch_type",
    )
    _assert(_slot_identities(domain) == before, "malformed batch mutation")
    return {"exact_tuple_required": True, "slot_mutation": False}


def test_t24_historical_dto_factory_and_immutability() -> dict[str, object]:
    _expect(lambda: Row(), code="historical_factory_required")
    wrapper, raw, _, _ = BASE._compose()
    wrapper.reset()
    raw.terminal_next = True
    row = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    ).terminal_historical_payload[0]
    _expect(lambda: setattr(row, "env_id", 9))
    _assert(hasattr(row, "__slots__"), "historical DTO not slotted")
    return {"factory_controlled": True, "frozen": True, "slotted": True}


def test_t25_capability_chain_no_raw_facade_port() -> dict[str, object]:
    wrapper, _, _, _ = BASE._compose()
    facade = wrapper._event_runtime_facade
    fields = tuple(FACADE.EventAssignmentRuntimeFacade.__dataclass_fields__)
    _assert(fields == ("_runtime", "_resolved_profile", "_domain_identity"), "facade capability drift")
    for name in (
        "capture_pending_terminal_artifacts",
        "acknowledge_terminal_artifact",
        "acknowledge_terminal_artifacts",
    ):
        _assert(not hasattr(facade, name), f"raw terminal facade method {name}")
    _assert(hasattr(SYNC.EventProfileSynchronousRuntimeCoordinator, "acknowledge_terminal_artifacts"), "O1 batch")
    return {"chain": "coordinator -> consumer port -> O1 -> facade helper", "raw_port": False}


def test_t26_process_side_effects() -> dict[str, object]:
    evidence = BASE.test_t22_global_side_effects()
    heavy = tuple(name for name in sys.modules if name.startswith(("isaaclab.", "omni.", "pxr", "harl")))
    _assert(not heavy, f"heavy modules imported {heavy}")
    return {**evidence, "heavy_modules": []}


TESTS: tuple[tuple[str, Callable[[], dict[str, object]]], ...] = (
    ("I4-3-T1", test_t1_atomic_batch_success_e2),
    ("I4-3-T2", test_t2_wrong_second_key_all_retained),
    ("I4-3-T3", test_t3_duplicate_key_all_retained),
    ("I4-3-T4", test_t4_missing_slot_all_retained),
    ("I4-3-T5", test_t5_foreign_consumer_rejected),
    ("I4-3-T6", test_t6_empty_batch_noop),
    ("I4-3-T7", test_t7_single_key_ack_preserved),
    ("I4-3-T8", test_t8_capture_repeat_exact_identity),
    ("I4-3-T9", test_t9_historical_copy_no_alias),
    ("I4-3-T10", test_t10_full_copy_precedes_ack),
    ("I4-3-T11", test_t11_copy_failure_no_ack_r3_retained),
    ("I4-3-T12", test_t12_terminal_facade_success_path),
    ("I4-3-T13", test_t13_historical_current_p2_separation),
    ("I4-3-T14", test_t14_ack_neutrality),
    ("I4-3-T15", test_t15_wrapper_payload_bounded_and_cache_clear),
    ("I4-3-T16", test_t16_proposal_route_terminal_handoff),
    ("I4-3-T17", test_t17_continuation_terminal_current_observation),
    ("I4-3-T18", test_t18_post_ack_next_step_recovery),
    ("I4-3-T19", test_t19_public_event_step_still_blocked),
    ("I4-3-T20", test_t20_optional_sidecar_none_no_synthesis),
    ("I4-3-T21", test_t21_single_publication_static_audit),
    ("I4-3-T22", test_t22_default_off_profiles_isolated),
    ("I4-3-T23", test_t23_malformed_batch_type_no_mutation),
    ("I4-3-T24", test_t24_historical_dto_factory_and_immutability),
    ("I4-3-T25", test_t25_capability_chain_no_raw_facade_port),
    ("I4-3-T26", test_t26_process_side_effects),
)


def run_suite() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    passed = 0
    for name, test in TESTS:
        try:
            evidence = test()
        except BaseException as exc:
            rows.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            rows.append({"name": name, "status": "passed", "evidence": evidence})
            passed += 1
    return {
        "status": "passed" if passed == len(TESTS) else "failed",
        "passed": passed,
        "failed": len(TESTS) - passed,
        "num_tests": len(TESTS),
        "tests": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for row in result["tests"]:
            print(f"{row['name']}: {row['status']}")
            if row["status"] == "failed":
                print(f"  {row['error']}")
        print(f"passed {result['passed']}/{result['num_tests']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
