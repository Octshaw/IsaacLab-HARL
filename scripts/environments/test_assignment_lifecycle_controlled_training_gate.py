"""Phase 9G-8F-6R controlled lifecycle training gate tests.

These tests are project-local and synthetic. They do not launch AppLauncher,
construct the real assignment environment, run training, run playback, or load
checkpoints.
"""

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

import assignment_harl_training as training_module  # noqa: E402
from assignment_harl_training import AssignmentIsaacLabEnv  # noqa: E402
from assignment_harl_wrapper import AssignmentHarlWrapper  # noqa: E402
from assignment_lifecycle_training_contract import (  # noqa: E402
    FEED_FORWARD_GENERATOR,
    LIFECYCLE_SUPPORTED_ALGORITHM,
    LIFECYCLE_SUPPORTED_STATE_TYPE,
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
                raise AssertionError(f"expected {expected!r} in {message!r}") from exc
        return
    raise AssertionError(f"expected an error containing {expected_substrings!r}")


def _algo_args(
    *,
    recurrent: bool = False,
    naive_recurrent: bool = False,
    share_param: bool = False,
    save_entire_model: bool = False,
) -> dict[str, Any]:
    return {
        "model": {
            "use_recurrent_policy": recurrent,
            "use_naive_recurrent_policy": naive_recurrent,
            "data_chunk_length": 10,
            "recurrent_n": 1,
        },
        "algo": {
            "share_param": share_param,
        },
        "train": {
            "save_entire_model": save_entire_model,
        },
    }


def _env_args(
    profile: str,
    *,
    algorithm: str = LIFECYCLE_SUPPORTED_ALGORITHM,
    state_type: str = LIFECYCLE_SUPPORTED_STATE_TYPE,
) -> dict[str, Any]:
    return {
        "assignment_rl": True,
        "algorithm": algorithm,
        "state_type": state_type,
        "config": SimpleNamespace(assignment_lifecycle_profile=profile),
    }


def _wrapper_for_profile(profile: str) -> AssignmentHarlWrapper:
    overrides: dict[str, Any] = {}
    if profile == "lifecycle_contract_c":
        overrides.update(_contract_c_overrides())
    if profile == "diagnostics_hidden_state":
        overrides["assignment_lifecycle_resolver_enabled"] = True
    return AssignmentHarlWrapper(FakeAssignmentEnv(profile=profile, config_overrides=overrides))


def _cfg_for_profile(profile: str) -> SimpleNamespace:
    values: dict[str, Any] = {
        "assignment_lifecycle_profile": profile,
        "assignment_lifecycle_resolver_enabled": False,
    }
    if profile == "lifecycle_contract_c":
        values.update(_contract_c_overrides())
    if profile == "diagnostics_hidden_state":
        values["assignment_lifecycle_resolver_enabled"] = True
    return SimpleNamespace(**values)


def _fake_make(_task: str, *, cfg: Any, render_mode: str | None = None) -> FakeAssignmentEnv:
    del render_mode
    profile = str(getattr(cfg, "assignment_lifecycle_profile", "legacy"))
    overrides = dict(vars(cfg))
    overrides.pop("assignment_lifecycle_profile", None)
    return FakeAssignmentEnv(profile=profile, config_overrides=overrides)


def _call_assignment_env_with_fake_gym(profile: str) -> AssignmentIsaacLabEnv:
    original_make = training_module.gym.make
    training_module.gym.make = _fake_make
    try:
        return AssignmentIsaacLabEnv(
            {
                "assignment_rl": True,
                "n_threads": 2,
                "task": "Fake-Assignment-Task-v0",
                "config": _cfg_for_profile(profile),
                "video_settings": {"video": False},
            }
        )
    finally:
        training_module.gym.make = original_make


def test_official_profile_activation() -> None:
    wrapper = _wrapper_for_profile("lifecycle_contract_c")
    config = wrapper.assignment_lifecycle_profile_config
    _assert(config["profile_name"] == "lifecycle_contract_c", "official profile")
    _assert(config["training_allowed"] is True, "official profile training gate is active")
    _assert("training_blocked_reason" not in config, "allowed profile has no blocked reason")
    _assert(config["resolver_enabled"] is True, "resolver remains enabled")
    _assert(config["lifecycle_mask_enabled"] is True, "lifecycle mask remains enabled")


def test_evaluation_only_profile_preservation() -> None:
    wrapper = _wrapper_for_profile("lifecycle_ablation")
    config = wrapper.assignment_lifecycle_profile_config
    _assert(config["training_allowed"] is False, "ablation remains training-prohibited")
    _assert("observation/mask ablation profile" in config["training_blocked_reason"], "ablation reason")


def test_diagnostics_profile_preservation() -> None:
    wrapper = _wrapper_for_profile("diagnostics_hidden_state")
    config = wrapper.assignment_lifecycle_profile_config
    _assert(config["training_allowed"] is False, "diagnostics remains training-prohibited")
    _assert(config["resolver_enabled"] is True, "diagnostics resolver remains enabled")


def test_unknown_profile_rejected() -> None:
    _expect_raises(
        lambda: _wrapper_for_profile("unknown_profile"),
        ("assignment_lifecycle_profile must be one of", "unknown_profile"),
    )


def test_feed_forward_guard_remains_active() -> None:
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(recurrent=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("feed-forward policies only", "recurrent_generator_actor"),
    )
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(naive_recurrent=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("feed-forward policies only", "naive_recurrent_generator_actor"),
    )
    contract = validate_assignment_lifecycle_policy_sequence(
        algo_args=_algo_args(),
        env_args=_env_args("lifecycle_contract_c"),
    )
    _assert(contract["supported_actor_buffer_generator"] == FEED_FORWARD_GENERATOR, "feed-forward generator")


def test_state_and_sharing_guards_remain_active() -> None:
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(),
            env_args=_env_args("lifecycle_contract_c", state_type="FP"),
        ),
        ("state_type='EP' only", "FP"),
    )
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(share_param=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("share_param=False",),
    )


def test_algorithm_support_guard_remains_active() -> None:
    for algorithm in ("hatrpo", "haa2c"):
        _expect_raises(
            lambda algorithm=algorithm: validate_assignment_lifecycle_policy_sequence(
                algo_args=_algo_args(),
                env_args=_env_args("lifecycle_contract_c", algorithm=algorithm),
            ),
            ("HAPPO only", algorithm),
        )


def test_state_dict_serialization_guard_remains_active() -> None:
    _expect_raises(
        lambda: validate_assignment_lifecycle_policy_sequence(
            algo_args=_algo_args(save_entire_model=True),
            env_args=_env_args("lifecycle_contract_c"),
        ),
        ("save_entire_model=False", "state_dict"),
    )


def test_environment_training_gate_behavior_without_real_env() -> None:
    allowed = _call_assignment_env_with_fake_gym("lifecycle_contract_c")
    _assert(
        allowed.assignment_env.assignment_lifecycle_profile_config["training_allowed"] is True,
        "allowed lifecycle profile does not fail solely at training_allowed",
    )

    _expect_raises(
        lambda: _call_assignment_env_with_fake_gym("lifecycle_ablation"),
        ("lifecycle_ablation", "not enabled for normal training"),
    )
    _expect_raises(
        lambda: _call_assignment_env_with_fake_gym("diagnostics_hidden_state"),
        ("diagnostics_hidden_state", "not training-ready"),
    )


def test_train_entry_validation_ordering() -> None:
    train_source = (REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py").read_text(
        encoding="utf-8"
    )
    algorithm_assignment = train_source.index('env_args["algorithm"] = args["algo"]')
    guard_call = train_source.index("sequence_contract = validate_assignment_lifecycle_policy_sequence(")
    runner_construction = train_source.index('runner = RUNNER_REGISTRY[args["algo"]]')
    _assert(algorithm_assignment < guard_call < runner_construction, "resolved guard precedes runner")


TESTS = (
    test_official_profile_activation,
    test_evaluation_only_profile_preservation,
    test_diagnostics_profile_preservation,
    test_unknown_profile_rejected,
    test_feed_forward_guard_remains_active,
    test_state_and_sharing_guards_remain_active,
    test_algorithm_support_guard_remains_active,
    test_state_dict_serialization_guard_remains_active,
    test_environment_training_gate_behavior_without_real_env,
    test_train_entry_validation_ordering,
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
        except Exception as exc:  # noqa: BLE001 - standalone runner records every contract failure.
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
        print(f"{'FAIL' if failed else 'PASS'} {len(results)} controlled lifecycle gate tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
