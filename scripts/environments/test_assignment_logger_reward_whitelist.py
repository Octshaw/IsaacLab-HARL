# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Unit-like smoke for assignment HARL logger reward-accumulator whitelisting."""

import argparse
import json
import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ISAACLAB_TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks"
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
for source_path in (ISAACLAB_TASKS_SOURCE, SCAN_TASK_SOURCE):
    if str(source_path) not in sys.path:
        sys.path.insert(0, str(source_path))

from assignment_harl_training import (  # noqa: E402
    ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
    _compute_reward_accumulator_total,
    _should_accumulate_reward_key,
)


def _build_sample_log(logged_steps: int) -> dict[str, list[float]]:
    sample_means = {
        "assignment_rl_reward/final_reward_mean": 0.1438,
        "assignment_rl_reward/steps_since_global_coverage_gain_mean": 148.84,
        "assignment_rl_reward/base_env_reward_mean": 0.4255,
        "assignment_rl_reward/repeated_same_target_no_progress_mean": -0.2324,
        "assignment_rl_reward/global_no_progress_mean": -0.0493,
        "assignment_rl_reward/selected_path_cost_mean": 0.0,
        "assignment_rl_reward/total_assignment_reward_adjustment_mean": -0.2817,
        "assignment_rl_reward/global_coverage_gain_mean": 0.0,
        "mean_reward": 0.4255,
        "critic/average_step_rewards": 0.4384,
        "coverage_ratio": 0.3193,
    }
    return {key: [value] * logged_steps for key, value in sample_means.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logged_steps",
        type=int,
        default=1500,
        help="Number of per-step scalar samples in the synthetic logging interval.",
    )
    parser.add_argument("--result_file", type=str, default=None, help="Optional JSON result path.")
    args = parser.parse_args()

    sample_log = _build_sample_log(args.logged_steps)
    legacy_total = _compute_reward_accumulator_total(sample_log, reward_accumulator_keys=None)
    whitelist_total = _compute_reward_accumulator_total(
        sample_log,
        reward_accumulator_keys=ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
    )
    expected_whitelist_total = sum(sample_log["assignment_rl_reward/final_reward_mean"])
    steps_since_sum = sum(sample_log["assignment_rl_reward/steps_since_global_coverage_gain_mean"])

    if not math.isclose(whitelist_total, expected_whitelist_total, rel_tol=1e-7, abs_tol=1e-7):
        raise AssertionError(
            f"whitelist_total={whitelist_total} expected {expected_whitelist_total}"
        )
    if whitelist_total >= legacy_total:
        raise AssertionError(f"whitelist_total={whitelist_total} must be below legacy_total={legacy_total}")
    if steps_since_sum <= 100_000.0:
        raise AssertionError(f"sample steps_since contribution unexpectedly small: {steps_since_sum}")
    if _should_accumulate_reward_key(
        "assignment_rl_reward/steps_since_global_coverage_gain_mean",
        ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
    ):
        raise AssertionError("steps_since_global_coverage_gain_mean must not accumulate")
    if not _should_accumulate_reward_key(
        "assignment_rl_reward/final_reward_mean",
        ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
    ):
        raise AssertionError("final_reward_mean must accumulate")
    if _should_accumulate_reward_key("mean_reward", ASSIGNMENT_REWARD_ACCUMULATOR_KEYS):
        raise AssertionError("mean_reward must not accumulate in assignment whitelist mode")
    if len(sample_log) != len(_build_sample_log(args.logged_steps)):
        raise AssertionError("diagnostic keys were unexpectedly filtered")

    result = {
        "logged_steps": args.logged_steps,
        "reward_accumulator_keys": sorted(ASSIGNMENT_REWARD_ACCUMULATOR_KEYS),
        "legacy_substring_total": legacy_total,
        "whitelist_total": whitelist_total,
        "expected_whitelist_total": expected_whitelist_total,
        "steps_since_sum_if_legacy_accumulated": steps_since_sum,
        "steps_since_contributes_with_whitelist": _should_accumulate_reward_key(
            "assignment_rl_reward/steps_since_global_coverage_gain_mean",
            ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
        ),
        "final_reward_contributes_with_whitelist": _should_accumulate_reward_key(
            "assignment_rl_reward/final_reward_mean",
            ASSIGNMENT_REWARD_ACCUMULATOR_KEYS,
        ),
        "diagnostic_keys_still_present": sorted(sample_log.keys()),
    }

    if args.result_file is not None:
        result_path = Path(args.result_file)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        "[OK] assignment logger reward whitelist smoke passed "
        f"legacy_total={legacy_total:.6f} whitelist_total={whitelist_total:.6f} "
        f"steps_since_legacy_contribution={steps_since_sum:.6f}"
    )


if __name__ == "__main__":
    main()
