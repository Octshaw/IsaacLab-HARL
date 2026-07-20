#!/usr/bin/env python3
"""Offline CLI for assignment training-run metadata and scalar audits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
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

from assignment_training_run_audit import (  # noqa: E402
    AuditExpectations,
    AuditPreflightError,
    audit_assignment_training_run,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit one timestamped assignment-HARL training run offline. "
            "Checkpoint files are read only as opaque bytes for size and SHA-256."
        )
    )
    parser.add_argument("--run_dir", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--scope", choices=("full", "events", "checkpoints"), default="full")
    parser.add_argument("--expected-exp-name", required=True)
    parser.add_argument("--expected-algorithm", required=True)
    parser.add_argument("--expected-seed", type=int, required=True)
    parser.add_argument("--expected-num-envs", type=int, required=True)
    parser.add_argument("--expected-num-agents", type=int, required=True)
    parser.add_argument("--expected-num-tasks", type=int, required=True)
    parser.add_argument("--expected-episode-length", type=int, required=True)
    parser.add_argument("--expected-configured-num-env-steps", type=int, required=True)
    parser.add_argument("--expected-final-step", type=int, required=True)
    parser.add_argument("--expected-rollouts", type=int, required=True)
    parser.add_argument("--expected-log-points", type=int, required=True)
    parser.add_argument("--expected-save-interval", type=int, required=True)
    parser.add_argument("--expected-log-interval", type=int, required=True)
    parser.add_argument("--expected-profile", required=True)
    parser.add_argument("--expected-actor-obs-width", type=int, required=True)
    parser.add_argument("--expected-shared-obs-width", type=int, required=True)
    parser.add_argument("--expected-action-width", type=int, required=True)
    parser.add_argument("--expected-raw-noop-id", type=int, required=True)
    parser.add_argument(
        "--expected-task",
        default="Isaac-Scan-Mobile-Manipulator-Direct-v0",
        help="Expected registered task name.",
    )
    parser.add_argument(
        "--expected-state-type",
        default="EP",
        help="Expected HARL centralized-state convention.",
    )
    return parser


def _expectations(args: argparse.Namespace) -> AuditExpectations:
    return AuditExpectations(
        exp_name=args.expected_exp_name,
        algorithm=args.expected_algorithm,
        seed=args.expected_seed,
        num_envs=args.expected_num_envs,
        num_agents=args.expected_num_agents,
        num_tasks=args.expected_num_tasks,
        episode_length=args.expected_episode_length,
        configured_num_env_steps=args.expected_configured_num_env_steps,
        final_step=args.expected_final_step,
        rollouts=args.expected_rollouts,
        log_points=args.expected_log_points,
        save_interval=args.expected_save_interval,
        log_interval=args.expected_log_interval,
        profile=args.expected_profile,
        actor_obs_width=args.expected_actor_obs_width,
        shared_obs_width=args.expected_shared_obs_width,
        action_width=args.expected_action_width,
        raw_noop_id=args.expected_raw_noop_id,
        task=args.expected_task,
        state_type=args.expected_state_type,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        expectations = _expectations(args)
        result = audit_assignment_training_run(
            run_dir=args.run_dir,
            output_dir=args.output_dir,
            scope=args.scope,
            expectations=expectations,
        )
    except (AuditPreflightError, OSError, ValueError) as exc:
        print(f"OFFLINE AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"classification: {result['classification']}")
    print(f"json: {result['output_files']['json']}")
    print(f"markdown: {result['output_files']['markdown']}")
    return 1 if result["classification"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
