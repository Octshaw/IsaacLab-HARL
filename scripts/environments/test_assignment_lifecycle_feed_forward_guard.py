"""Phase 9G-8E-R feed-forward support and recurrent guardrail tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
if str(SCAN_TASK_SOURCE) not in sys.path:
    sys.path.insert(0, str(SCAN_TASK_SOURCE))

from assignment_harl_training import AssignmentOnPolicyHARunner  # noqa: E402
from assignment_harl_wrapper import AssignmentHarlWrapper  # noqa: E402
from assignment_lifecycle_training_contract import (  # noqa: E402
    CHUNKED_RECURRENT_GENERATOR,
    FEED_FORWARD_GENERATOR,
    LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION,
    NAIVE_RECURRENT_GENERATOR,
    resolve_installed_harl_actor_buffer_generator,
    validate_assignment_lifecycle_policy_sequence,
)
from test_assignment_lifecycle_observation_integration import (  # noqa: E402
    FakeAssignmentEnv,
    _contract_c_overrides,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], expected_substrings: tuple[str, ...]) -> None:
    try:
        func()
    except (RuntimeError, TypeError, ValueError) as exc:
        message = str(exc)
        for expected in expected_substrings:
            if expected not in message:
                raise AssertionError(f"expected error containing {expected!r}, got {message!r}") from exc
        return
    raise AssertionError(f"expected an error containing {expected_substrings!r}")


def _algo_args(*, recurrent: bool, naive_recurrent: bool) -> dict[str, Any]:
    return {
        "model": {
            "use_recurrent_policy": recurrent,
            "use_naive_recurrent_policy": naive_recurrent,
            "data_chunk_length": 10,
            "recurrent_n": 1,
        }
    }


def _env_args(profile: str) -> dict[str, Any]:
    return {
        "assignment_rl": True,
        "config": SimpleNamespace(assignment_lifecycle_profile=profile),
    }


def test_valid_lifecycle_feed_forward_contract() -> None:
    contract = validate_assignment_lifecycle_policy_sequence(
        algo_args=_algo_args(recurrent=False, naive_recurrent=False),
        env_args=_env_args("lifecycle_contract_c"),
    )
    _assert(
        contract["policy_sequence_contract_version"] == LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION,
        "sequence contract version",
    )
    _assert(contract["policy_sequence_mode"] == "feed_forward", "feed-forward sequence mode")
    _assert(contract["supported_actor_buffer_generator"] == FEED_FORWARD_GENERATOR, "supported generator")
    selected = resolve_installed_harl_actor_buffer_generator(
        use_recurrent_policy=False,
        use_naive_recurrent_policy=False,
    )
    _assert(selected == FEED_FORWARD_GENERATOR, "installed branch resolves to feed-forward generator")


def test_chunked_recurrent_hard_error_before_runner_setup() -> None:
    algo_args = _algo_args(recurrent=True, naive_recurrent=False)
    env_args = _env_args("lifecycle_contract_c")
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(algo_args=algo_args, env_args=env_args),
        ("feed-forward policies only", CHUNKED_RECURRENT_GENERATOR),
    )

    runner = AssignmentOnPolicyHARunner.__new__(AssignmentOnPolicyHARunner)
    _expect_raises(
        lambda: AssignmentOnPolicyHARunner.__init__(runner, {}, algo_args, env_args),
        ("feed-forward policies only", CHUNKED_RECURRENT_GENERATOR),
    )
    _assert(not hasattr(runner, "env"), "runner guard fires before environment construction")
    _assert(not hasattr(runner, "actor"), "runner guard fires before actor construction")
    _assert(not hasattr(runner, "actor_buffer"), "runner guard fires before actor-buffer construction")


def test_naive_recurrent_hard_error() -> None:
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(recurrent=False, naive_recurrent=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("feed-forward policies only", NAIVE_RECURRENT_GENERATOR),
    )


def test_contradictory_recurrent_flags_hard_error() -> None:
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(recurrent=True, naive_recurrent=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("Contradictory lifecycle recurrent flags", CHUNKED_RECURRENT_GENERATOR),
    )


def test_ambiguous_recurrent_flag_hard_error() -> None:
    algo_args = _algo_args(recurrent=False, naive_recurrent=False)
    algo_args["model"]["use_recurrent_policy"] = "False"
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=algo_args,
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("model.use_recurrent_policy", "resolve to a boolean"),
    )


def test_legacy_profile_recurrent_flags_are_not_rejected() -> None:
    contract = validate_assignment_lifecycle_policy_sequence(
        algo_args=_algo_args(recurrent=True, naive_recurrent=True),
        env_args=_env_args("legacy"),
    )
    _assert(contract["policy_sequence_mode"] == "existing_legacy_behavior", "legacy mode remains unchanged")


def test_lifecycle_manifest_records_feed_forward_contract() -> None:
    wrapper = AssignmentHarlWrapper(
        FakeAssignmentEnv(profile="lifecycle_contract_c", config_overrides=_contract_c_overrides())
    )
    manifest = wrapper.assignment_observation_schema_manifest
    _assert(
        manifest["policy_sequence_contract_version"] == LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION,
        "manifest sequence contract version",
    )
    _assert(manifest["policy_sequence_mode"] == "feed_forward", "manifest sequence mode")
    _assert(manifest["use_recurrent_policy"] is False, "manifest chunked recurrent flag")
    _assert(manifest["use_naive_recurrent_policy"] is False, "manifest naive recurrent flag")
    _assert(
        manifest["supported_actor_buffer_generator"] == FEED_FORWARD_GENERATOR,
        "manifest supported generator",
    )
    _assert(
        manifest["unsupported_actor_buffer_generators"]
        == [NAIVE_RECURRENT_GENERATOR, CHUNKED_RECURRENT_GENERATOR],
        "manifest unsupported generators",
    )


def test_non_training_profiles_remain_non_training() -> None:
    ablation = AssignmentHarlWrapper(FakeAssignmentEnv(profile="lifecycle_ablation"))
    diagnostics = AssignmentHarlWrapper(
        FakeAssignmentEnv(
            profile="diagnostics_hidden_state",
            config_overrides={"assignment_lifecycle_resolver_enabled": True},
        )
    )
    _assert(not ablation.assignment_lifecycle_profile_config["training_allowed"], "ablation training stays disabled")
    _assert(
        not diagnostics.assignment_lifecycle_profile_config["training_allowed"],
        "diagnostics training stays disabled",
    )


def test_train_entry_guard_precedes_runner_construction() -> None:
    train_source = (REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py").read_text(
        encoding="utf-8"
    )
    guard_call = train_source.index("sequence_contract = validate_assignment_lifecycle_policy_sequence(")
    runner_construction = train_source.index('runner = RUNNER_REGISTRY[args["algo"]]')
    _assert(guard_call < runner_construction, "resolved lifecycle guard must precede runner construction")


TESTS = (
    test_valid_lifecycle_feed_forward_contract,
    test_chunked_recurrent_hard_error_before_runner_setup,
    test_naive_recurrent_hard_error,
    test_contradictory_recurrent_flags_hard_error,
    test_ambiguous_recurrent_flag_hard_error,
    test_legacy_profile_recurrent_flags_are_not_rejected,
    test_lifecycle_manifest_records_feed_forward_contract,
    test_non_training_profiles_remain_non_training,
    test_train_entry_guard_precedes_runner_construction,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary.")
    args = parser.parse_args()
    results = []
    failed = False
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - test runner records all contract failures.
            failed = True
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    if args.json:
        print(json.dumps({"status": "failed" if failed else "passed", "tests": results}, indent=2))
    else:
        for result in results:
            prefix = "PASS" if result["status"] == "passed" else "FAIL"
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{prefix} {result['name']}{suffix}")
        print(f"{'FAIL' if failed else 'PASS'} {len(results)} lifecycle feed-forward guard tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
