# Copyright (c) 2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Pure offline audit for assignment-HARL training result directories.

The module reads configuration, TensorBoard events, JSON contract metadata,
and checkpoint artifacts as opaque bytes. It has no environment, runner,
model, CUDA, or checkpoint-deserialization dependency.
"""

import hashlib
import json
import math
import os
import re
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from .assignment_checkpoint_contract import (
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        ContractValidationError,
        canonical_manifest_bytes,
        compute_manifest_sha256,
    )
except ImportError:  # Supports the thin script and standalone tests.
    from assignment_checkpoint_contract import (  # type: ignore
        AssignmentCheckpointContractManifest,
        AssignmentTrainingStateManifest,
        ContractValidationError,
        canonical_manifest_bytes,
        compute_manifest_sha256,
    )


AUDIT_SCHEMA_VERSION = "phase9g8i0a_assignment_training_run_audit_v1"
AUDIT_TOOL_VERSION = "phase9g8i0a_offline_audit_v1"
AUDIT_JSON_FILE = "assignment_training_run_audit.json"
AUDIT_MARKDOWN_FILE = "assignment_training_run_audit.md"
SUPPORTED_SCOPES = ("full", "events", "checkpoints")

CONTRACT_MANIFEST_FILE = "assignment_contract_manifest.json"
CONTRACT_FINGERPRINT_FILE = "assignment_contract_fingerprint.txt"
TRAINING_STATE_MANIFEST_FILE = "assignment_training_state_manifest.json"
EXPECTED_MANIFEST_VERSION = "assignment_checkpoint_contract_v2"
EXPECTED_TRAINING_STATE_VERSION = "assignment_training_state_v1"
EXPECTED_TASK = "Isaac-Scan-Mobile-Manipulator-Direct-v0"

EXPECTED_SCALAR_TAGS = (
    "coverage_ratio",
    "new_viewpoints",
    "duplicate_scans",
    "reach_violation",
    "mean_reward",
    "assignment_rl.duplicate_count",
    "assignment_rl.noop_count",
    "assignment_rl.valid_action_count",
    "assignment_rl.selected_available_mask",
    "assignment_cooldown.enabled",
    "assignment_cooldown.trigger_mode_code",
    "assignment_cooldown.active_count",
    "assignment_cooldown.active_count_mean",
    "assignment_cooldown.trigger_count",
    "assignment_cooldown.trigger_count_mean",
    "assignment_cooldown.triggered_pair_count",
    "assignment_cooldown.suppressed_action_count",
    "assignment_cooldown.suppressed_action_count_mean",
    "assignment_cooldown.failed_attempt_count_mean",
    "assignment_cooldown.max_cooldown_remaining",
    "assignment_cooldown.max_cooldown_remaining_mean",
    "assignment_cooldown.selected_target_was_in_cooldown_count",
    "assignment_cooldown.last_triggered_viewpoint",
    "assignment_cooldown.budget_multiplier",
    "assignment_cooldown.budget_slack_steps",
    "assignment_cooldown.budget_min_streak",
    "assignment_cooldown.budget_trigger_count",
    "assignment_cooldown.budget_over_budget_selected_count",
    "assignment_cooldown.budget_triggered_pair_count",
    "assignment_cooldown.budget_attempt_steps_mean",
    "assignment_cooldown.budget_attempt_steps_max",
    "assignment_cooldown.budget_steps_mean",
    "assignment_cooldown.budget_steps_max",
    "assignment_cooldown.budget_budget_steps_mean",
    "assignment_cooldown.budget_budget_steps_max",
    "assignment_cooldown.budget_ratio_mean",
    "assignment_cooldown.budget_ratio_max",
    "assignment_cooldown.budget_last_triggered_by_budget",
    "assignment_cooldown.budget_last_triggered_by_budget_count",
    "assignment_rl_reward/base_env_reward_mean",
    "assignment_rl_reward/repeated_same_target_no_progress_mean",
    "assignment_rl_reward/global_no_progress_mean",
    "assignment_rl_reward/selected_path_cost_mean",
    "assignment_rl_reward/total_assignment_reward_adjustment_mean",
    "assignment_rl_reward/final_reward_mean",
    "assignment_rl_reward/steps_since_global_coverage_gain_mean",
    "assignment_rl_reward/global_coverage_gain_mean",
    "Total_Reward",
    "agent0/policy_loss",
    "agent0/dist_entropy",
    "agent0/actor_grad_norm",
    "agent0/ratio",
    "agent1/policy_loss",
    "agent1/dist_entropy",
    "agent1/actor_grad_norm",
    "agent1/ratio",
    "agent2/policy_loss",
    "agent2/dist_entropy",
    "agent2/actor_grad_norm",
    "agent2/ratio",
    "critic/value_loss",
    "critic/critic_grad_norm",
    "critic/average_step_rewards",
)

PRINCIPAL_TAG_DIRECTIONS = {
    "coverage_ratio": "higher-is-better",
    "new_viewpoints": "higher-is-better",
    "mean_reward": "higher-is-better",
    "Total_Reward": "higher-is-better",
    "assignment_rl_reward/final_reward_mean": "higher-is-better",
    "assignment_rl.noop_count": "lower-is-better",
    "assignment_rl.valid_action_count": "higher-is-better",
    "assignment_rl_reward/global_no_progress_mean": "higher-is-better",
    "assignment_cooldown.budget_trigger_count": "descriptive-only",
    "assignment_cooldown.budget_ratio_mean": "descriptive-only",
    "agent0/policy_loss": "descriptive-only",
    "agent1/policy_loss": "descriptive-only",
    "agent2/policy_loss": "descriptive-only",
    "agent0/dist_entropy": "descriptive-only",
    "agent1/dist_entropy": "descriptive-only",
    "agent2/dist_entropy": "descriptive-only",
    "agent0/actor_grad_norm": "descriptive-only",
    "agent1/actor_grad_norm": "descriptive-only",
    "agent2/actor_grad_norm": "descriptive-only",
    "critic/value_loss": "lower-is-better",
    "critic/critic_grad_norm": "descriptive-only",
    "critic/average_step_rewards": "higher-is-better",
}

_TIMESTAMPED_RUN = re.compile(r"^seed-\d{5}-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$")
_PROFILE_IN_CONFIG = re.compile(r"assignment_lifecycle_profile=(?:'([^']+)'|\"([^\"]+)\")")
_LEGACY_ACTOR = re.compile(
    r"^(?:\d+|actor\d+|actor_agent_?\d+|actor_\d+)\.pt$",
    re.IGNORECASE,
)
_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MISSING = object()


class AuditPreflightError(RuntimeError):
    """Raised before analysis when safe output cannot be guaranteed."""


@dataclass(frozen=True)
class AuditExpectations:
    exp_name: str
    algorithm: str
    seed: int
    num_envs: int
    num_agents: int
    num_tasks: int
    episode_length: int
    configured_num_env_steps: int
    final_step: int
    rollouts: int
    log_points: int
    save_interval: int
    log_interval: int
    profile: str
    actor_obs_width: int
    shared_obs_width: int
    action_width: int
    raw_noop_id: int
    task: str = EXPECTED_TASK
    state_type: str = "EP"

    def __post_init__(self) -> None:
        text_fields = ("exp_name", "algorithm", "profile", "task", "state_type")
        for field in text_fields:
            if not str(getattr(self, field)).strip():
                raise ValueError(f"expected {field} must be non-empty")
        positive_fields = (
            "num_envs",
            "num_agents",
            "num_tasks",
            "episode_length",
            "configured_num_env_steps",
            "final_step",
            "rollouts",
            "log_points",
            "save_interval",
            "log_interval",
            "actor_obs_width",
            "shared_obs_width",
            "action_width",
        )
        for field in positive_fields:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"expected {field} must be a positive integer")
        if self.raw_noop_id < 0:
            raise ValueError("expected raw_noop_id must be nonnegative")
        if self.final_step != self.episode_length * self.num_envs * self.rollouts:
            raise ValueError(
                "expected final_step must equal episode_length * num_envs * rollouts"
            )
        if self.log_points != self.rollouts // self.log_interval:
            raise ValueError("expected log_points must equal rollouts // log_interval")

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _ScalarPoint:
    tag: str
    step: int
    wall_time: float
    value: float
    event_file: str


class _Issues:
    def __init__(self) -> None:
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []

    def error(self, code: str, message: str, **evidence: Any) -> None:
        self.errors.append({"code": code, "message": message, "evidence": _json_safe(evidence)})

    def warning(self, code: str, message: str, **evidence: Any) -> None:
        self.warnings.append({"code": code, "message": message, "evidence": _json_safe(evidence)})


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "NaN"
        return "+Infinity" if value > 0 else "-Infinity"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=str)]
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _nested(mapping: Mapping[str, Any], path: Sequence[str], default: Any = _MISSING) -> Any:
    current: Any = mapping
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def _read_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _preflight(
    run_dir: Path,
    output_dir: Path,
    scope: str,
) -> tuple[Path, Path, Mapping[str, Any], list[Path]]:
    if scope not in SUPPORTED_SCOPES:
        raise AuditPreflightError(f"unsupported audit scope {scope!r}")
    run_dir = run_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not run_dir.exists():
        raise AuditPreflightError(f"run_dir does not exist: {run_dir}")
    if not run_dir.is_dir():
        raise AuditPreflightError(f"run_dir is not a directory: {run_dir}")
    if _TIMESTAMPED_RUN.fullmatch(run_dir.name) is None:
        seed_children = sorted(
            child.name
            for child in run_dir.iterdir()
            if child.is_dir() and _TIMESTAMPED_RUN.fullmatch(child.name)
        )
        detail = f"; timestamped children={seed_children}" if seed_children else ""
        raise AuditPreflightError(
            "run_dir must be the exact timestamped seed directory, not an experiment parent"
            f": {run_dir}{detail}"
        )
    try:
        output_dir.relative_to(run_dir)
    except ValueError:
        pass
    else:
        raise AuditPreflightError("output_dir must be outside the audited run_dir")
    if output_dir == run_dir:
        raise AuditPreflightError("output_dir must not alias run_dir")
    for name in (AUDIT_JSON_FILE, AUDIT_MARKDOWN_FILE):
        target = output_dir / name
        if target.exists():
            raise AuditPreflightError(f"audit output already exists: {target}")

    config_path = run_dir / "configs.json"
    if not config_path.is_file():
        raise AuditPreflightError(f"configs.json is missing: {config_path}")
    try:
        config = _read_json(config_path)
    except Exception as exc:
        raise AuditPreflightError(f"configs.json is unreadable: {config_path}: {exc}") from exc

    event_files: list[Path] = []
    if scope in {"full", "events"}:
        logs = run_dir / "logs"
        if not logs.is_dir():
            raise AuditPreflightError(f"logs directory is missing: {logs}")
        event_files = sorted(
            (path.resolve() for path in logs.rglob("events.out.tfevents.*") if path.is_file()),
            key=lambda path: path.as_posix(),
        )
        if not event_files:
            raise AuditPreflightError(f"no TensorBoard event files found under {logs}")
    if scope in {"full", "checkpoints"}:
        for child in ("models", "best_model"):
            path = run_dir / child
            if not path.is_dir():
                raise AuditPreflightError(f"required checkpoint directory is missing: {path}")
    return run_dir, output_dir, config, event_files


def _record_check(
    checks: list[dict[str, Any]],
    issues: _Issues,
    *,
    name: str,
    path: str,
    actual: Any,
    expected: Any,
    hard: bool = True,
) -> bool:
    present = actual is not _MISSING
    passed = present and actual == expected
    record = {
        "name": name,
        "canonical_path": path,
        "expected": _json_safe(expected),
        "actual": None if actual is _MISSING else _json_safe(actual),
        "present": present,
        "result": "PASS" if passed else "FAIL",
    }
    checks.append(record)
    if not passed:
        method = issues.error if hard else issues.warning
        method(
            "config_mismatch" if present else "config_field_missing",
            f"configuration check failed for {name}",
            canonical_path=path,
            expected=expected,
            actual=None if actual is _MISSING else actual,
        )
    return passed


def _extract_profile(config: Mapping[str, Any]) -> tuple[Any, str]:
    direct = _nested(config, ("Env Args", "assignment_lifecycle_profile"))
    if direct is not _MISSING:
        return direct, "Env Args.assignment_lifecycle_profile"
    config_repr = _nested(config, ("Env Args", "config"))
    if isinstance(config_repr, str):
        match = _PROFILE_IN_CONFIG.search(config_repr)
        if match is not None:
            return match.group(1) or match.group(2), "Env Args.config::assignment_lifecycle_profile"
    return _MISSING, "Env Args.config::assignment_lifecycle_profile"


def _audit_config(
    config: Mapping[str, Any], expectations: AuditExpectations, issues: _Issues
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    args = config.get("Args") if isinstance(config.get("Args"), Mapping) else {}
    algo = config.get("Algo Args") if isinstance(config.get("Algo Args"), Mapping) else {}
    env = config.get("Env Args") if isinstance(config.get("Env Args"), Mapping) else {}

    direct_checks = (
        ("task", "Args.task", _nested(args, ("task",)), expectations.task),
        ("experiment name", "Args.exp_name", _nested(args, ("exp_name",)), expectations.exp_name),
        ("algorithm", "Args.algorithm", _nested(args, ("algorithm",)), expectations.algorithm),
        ("assignment RL enabled", "Args.assignment_rl", _nested(args, ("assignment_rl",)), True),
        ("CLI seed", "Args.seed", _nested(args, ("seed",)), expectations.seed),
        ("CLI environments", "Args.num_envs", _nested(args, ("num_envs",)), expectations.num_envs),
        (
            "CLI episode length",
            "Args.assignment_episode_length",
            _nested(args, ("assignment_episode_length",)),
            expectations.episode_length,
        ),
        (
            "CLI configured environment steps",
            "Args.num_env_steps",
            _nested(args, ("num_env_steps",)),
            expectations.configured_num_env_steps,
        ),
        ("CLI save interval", "Args.save_interval", _nested(args, ("save_interval",)), expectations.save_interval),
        ("CLI log interval", "Args.log_interval", _nested(args, ("log_interval",)), expectations.log_interval),
        ("fresh CLI directory", "Args.dir", _nested(args, ("dir",)), None),
        (
            "continuation acknowledgement",
            "Args.acknowledge_weight_continuation_reset",
            _nested(args, ("acknowledge_weight_continuation_reset",)),
            False,
        ),
        ("video disabled", "Args.video", _nested(args, ("video",)), False),
        ("HARL seed", "Algo Args.seed.seed", _nested(algo, ("seed", "seed")), expectations.seed),
        (
            "rollout threads",
            "Algo Args.train.n_rollout_threads",
            _nested(algo, ("train", "n_rollout_threads")),
            expectations.num_envs,
        ),
        (
            "HARL episode length",
            "Algo Args.train.episode_length",
            _nested(algo, ("train", "episode_length")),
            expectations.episode_length,
        ),
        (
            "HARL configured environment steps",
            "Algo Args.train.num_env_steps",
            _nested(algo, ("train", "num_env_steps")),
            expectations.configured_num_env_steps,
        ),
        (
            "HARL save interval",
            "Algo Args.train.eval_interval",
            _nested(algo, ("train", "eval_interval")),
            expectations.save_interval,
        ),
        (
            "HARL log interval",
            "Algo Args.train.log_interval",
            _nested(algo, ("train", "log_interval")),
            expectations.log_interval,
        ),
        ("fresh HARL model directory", "Algo Args.train.model_dir", _nested(algo, ("train", "model_dir")), None),
        ("evaluation disabled", "Algo Args.eval.use_eval", _nested(algo, ("eval", "use_eval")), False),
        (
            "recurrent policy disabled",
            "Algo Args.model.use_recurrent_policy",
            _nested(algo, ("model", "use_recurrent_policy")),
            False,
        ),
        (
            "naive recurrent policy disabled",
            "Algo Args.model.use_naive_recurrent_policy",
            _nested(algo, ("model", "use_naive_recurrent_policy")),
            False,
        ),
        ("parameter sharing disabled", "Algo Args.algo.share_param", _nested(algo, ("algo", "share_param")), False),
    )
    for name, path, actual, expected in direct_checks:
        _record_check(checks, issues, name=name, path=path, actual=actual, expected=expected)

    expected_n = _nested(args, ("expect_num_viewpoints",))
    if expected_n is not _MISSING:
        _record_check(
            checks,
            issues,
            name="configured viewpoint count",
            path="Args.expect_num_viewpoints",
            actual=expected_n,
            expected=expectations.num_tasks,
        )

    profile, profile_path = _extract_profile(config)
    _record_check(
        checks,
        issues,
        name="lifecycle profile",
        path=profile_path,
        actual=profile,
        expected=expectations.profile,
    )

    state_type = _nested(env, ("state_type",))
    state_path = "Env Args.state_type"
    if state_type is _MISSING:
        state_type = "EP"
        state_path += " (project runner default)"
    _record_check(
        checks,
        issues,
        name="HARL state type",
        path=state_path,
        actual=state_type,
        expected=expectations.state_type,
    )

    fresh_names = {
        "cli_dir_null": _nested(args, ("dir",)) is None,
        "model_dir_null": _nested(algo, ("train", "model_dir")) is None,
        "continuation_acknowledgement_false": _nested(
            args, ("acknowledge_weight_continuation_reset",)
        )
        is False,
    }
    return {
        "checks": checks,
        "passed": sum(item["result"] == "PASS" for item in checks),
        "failed": sum(item["result"] == "FAIL" for item in checks),
        "fresh_start": {
            **fresh_names,
            "result": "PASS" if all(fresh_names.values()) else "FAIL",
        },
        "contract_summary": {
            "task": _nested(args, ("task",), None),
            "algorithm": _nested(args, ("algorithm",), None),
            "profile": None if profile is _MISSING else profile,
            "state_type": state_type,
            "seed": _nested(args, ("seed",), None),
            "num_envs": _nested(args, ("num_envs",), None),
            "episode_length": _nested(algo, ("train", "episode_length"), None),
            "configured_num_env_steps": _nested(algo, ("train", "num_env_steps"), None),
        },
    }


def _load_event_points(
    run_dir: Path,
    event_files: Sequence[Path],
    issues: _Issues,
) -> tuple[dict[str, list[_ScalarPoint]], dict[str, Any]]:
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    except Exception as exc:  # pragma: no cover - dependency failure is environment-specific.
        issues.error("tensorboard_import_failed", "TensorBoard event_accumulator could not be imported", error=repr(exc))
        return {}, {"ignored_non_scalar_tags": {}, "load_errors": [repr(exc)]}

    gathered: dict[str, list[_ScalarPoint]] = {}
    ignored: dict[str, set[str]] = {}
    load_errors: list[dict[str, str]] = []
    for path in event_files:
        relative = path.relative_to(run_dir).as_posix()
        try:
            accumulator = EventAccumulator(str(path), size_guidance={"scalars": 0})
            accumulator.Reload()
            tags = accumulator.Tags()
            for category, names in tags.items():
                if category == "scalars" or not names:
                    continue
                if isinstance(names, (list, tuple, set)):
                    ignored.setdefault(category, set()).update(str(name) for name in names)
                else:
                    ignored.setdefault(category, set()).add("<present>")
            for tag in sorted(tags.get("scalars", [])):
                for event in accumulator.Scalars(tag):
                    gathered.setdefault(tag, []).append(
                        _ScalarPoint(
                            tag=tag,
                            step=int(event.step),
                            wall_time=float(event.wall_time),
                            value=float(event.value),
                            event_file=relative,
                        )
                    )
        except Exception as exc:
            load_errors.append({"event_file": relative, "error": repr(exc)})
            issues.error("event_file_unreadable", "TensorBoard event file could not be read", event_file=relative, error=repr(exc))
    return gathered, {
        "ignored_non_scalar_tags": {
            category: sorted(names) for category, names in sorted(ignored.items())
        },
        "load_errors": load_errors,
    }


def _merge_scalar_points(
    gathered: Mapping[str, Sequence[_ScalarPoint]], issues: _Issues
) -> tuple[dict[str, list[_ScalarPoint]], list[dict[str, Any]]]:
    merged: dict[str, list[_ScalarPoint]] = {}
    duplicate_records: list[dict[str, Any]] = []
    for tag in sorted(gathered):
        by_step: dict[int, _ScalarPoint] = {}
        for point in sorted(gathered[tag], key=lambda item: (item.step, item.event_file, item.wall_time)):
            existing = by_step.get(point.step)
            if existing is None:
                by_step[point.step] = point
                continue
            identical = (
                math.isfinite(existing.value)
                and math.isfinite(point.value)
                and existing.value == point.value
            )
            record = {
                "tag": tag,
                "step": point.step,
                "retained_value": _json_safe(existing.value),
                "duplicate_value": _json_safe(point.value),
                "retained_file": existing.event_file,
                "duplicate_file": point.event_file,
                "identical_finite": identical,
            }
            duplicate_records.append(record)
            if identical:
                issues.warning(
                    "identical_duplicate_scalar",
                    "identical finite duplicate scalar point was deterministically deduplicated",
                    **record,
                )
            else:
                issues.error(
                    "conflicting_duplicate_scalar",
                    "duplicate scalar tag/step has conflicting or nonfinite values",
                    **record,
                )
        merged[tag] = [by_step[step] for step in sorted(by_step)]
    return merged, duplicate_records


def _stats(points: Sequence[_ScalarPoint]) -> dict[str, Any]:
    if not points:
        return {
            "point_count": 0,
            "mean": None,
            "minimum": None,
            "maximum": None,
            "standard_deviation": None,
            "first": None,
            "last": None,
            "first_step": None,
            "last_step": None,
        }
    values = [point.value for point in points]
    return {
        "point_count": len(points),
        "mean": statistics.fmean(values),
        "minimum": min(values),
        "maximum": max(values),
        "standard_deviation": statistics.pstdev(values),
        "first": values[0],
        "last": values[-1],
        "first_step": points[0].step,
        "last_step": points[-1].step,
    }


def _trend_windows(
    points: Sequence[_ScalarPoint], expectations: AuditExpectations
) -> tuple[dict[str, Sequence[_ScalarPoint]], str]:
    if expectations.log_points == 333:
        return {
            "early": points[0:33],
            "middle": points[150:183],
            "late": points[300:333],
        }, "frozen_333_point_windows"
    width = min(33, len(points))
    return {
        "early": points[:width],
        "middle": (),
        "late": points[-width:] if width else (),
    }, "reduced_evidence_windows"


def _trend_summary(
    tag: str,
    points: Sequence[_ScalarPoint],
    expectations: AuditExpectations,
) -> dict[str, Any]:
    direction = PRINCIPAL_TAG_DIRECTIONS[tag]
    windows, window_mode = _trend_windows(points, expectations)
    summaries = {name: _stats(window) for name, window in windows.items()}
    early_mean = summaries["early"]["mean"]
    late_mean = summaries["late"]["mean"]
    delta = None if early_mean is None or late_mean is None else late_mean - early_mean
    relative = None
    if delta is not None and early_mean != 0.0 and direction != "descriptive-only":
        relative = delta / abs(early_mean)
    best_value: float | None = None
    best_step: int | None = None
    if points and direction in {"higher-is-better", "lower-is-better"}:
        chooser = max if direction == "higher-is-better" else min
        best_value = chooser(point.value for point in points)
        best_step = next(point.step for point in points if point.value == best_value)
    return {
        "tag": tag,
        "direction": direction,
        "window_mode": window_mode,
        "all": _stats(points),
        "windows": summaries,
        "best_observed_value": best_value,
        "best_step": best_step,
        "final_value": points[-1].value if points else None,
        "final_step": points[-1].step if points else None,
        "late_mean_minus_early_mean": delta,
        "relative_change": relative,
    }


def _audit_tensorboard(
    run_dir: Path,
    event_files: Sequence[Path],
    expectations: AuditExpectations,
    issues: _Issues,
) -> dict[str, Any]:
    gathered, load_metadata = _load_event_points(run_dir, event_files, issues)
    merged, duplicate_points = _merge_scalar_points(gathered, issues)
    expected = set(EXPECTED_SCALAR_TAGS)
    present = set(merged)
    missing = sorted(expected - present)
    extras = sorted(present - expected)
    empty = sorted(tag for tag, points in merged.items() if not points)
    for tag in missing:
        issues.error("expected_scalar_tag_missing", "expected TensorBoard scalar tag is missing", tag=tag)
    for tag in extras:
        issues.warning("unexpected_scalar_tag", "unexpected extra TensorBoard scalar tag is present", tag=tag)
    for tag in empty:
        issues.error("scalar_tag_empty", "TensorBoard scalar tag has no points", tag=tag)

    nonfinite: list[dict[str, Any]] = []
    for tag in sorted(merged):
        for point in merged[tag]:
            if math.isfinite(point.value):
                continue
            item = {
                "tag": tag,
                "step": point.step,
                "wall_time": point.wall_time,
                "value": _json_safe(point.value),
                "event_file": point.event_file,
            }
            nonfinite.append(item)
            issues.error("nonfinite_scalar", "TensorBoard scalar is nonfinite", **item)

    expected_steps = [
        expectations.episode_length * expectations.num_envs * expectations.log_interval * index
        for index in range(1, expectations.log_points + 1)
    ]
    step_coverage: dict[str, dict[str, Any]] = {}
    for tag in EXPECTED_SCALAR_TAGS:
        points = merged.get(tag, [])
        steps = [point.step for point in points]
        missing_steps = sorted(set(expected_steps) - set(steps))
        unexpected_steps = sorted(set(steps) - set(expected_steps))
        increasing = all(left < right for left, right in zip(steps, steps[1:]))
        valid_bounds = all(0 <= step <= expectations.final_step for step in steps)
        complete = steps == expected_steps
        status = "complete" if complete else "unexpectedly_sparse_or_misaligned"
        step_coverage[tag] = {
            "status": status,
            "point_count": len(points),
            "expected_point_count": expectations.log_points,
            "first_step": steps[0] if steps else None,
            "final_step": steps[-1] if steps else None,
            "strictly_increasing": increasing,
            "within_expected_bounds": valid_bounds,
            "missing_steps": missing_steps,
            "unexpected_steps": unexpected_steps,
        }
        if tag in present and not complete:
            issues.error(
                "scalar_step_coverage_mismatch",
                "expected scalar tag does not cover every frozen rollout step",
                tag=tag,
                point_count=len(points),
                expected_point_count=expectations.log_points,
                first_step=steps[0] if steps else None,
                final_step=steps[-1] if steps else None,
                missing_steps=missing_steps,
                unexpected_steps=unexpected_steps,
            )
        if not increasing:
            issues.error("scalar_steps_not_increasing", "scalar steps are not strictly increasing", tag=tag)
        if not valid_bounds:
            issues.error("scalar_step_out_of_bounds", "scalar step is negative or above expected final step", tag=tag)

    cross_tag = _audit_cross_tag_invariants(merged, expectations, issues)
    trend_summaries: dict[str, Any] = {}
    if nonfinite:
        trend_status = "skipped_due_to_nonfinite_scalars"
    else:
        trend_status = "computed"
        for tag in PRINCIPAL_TAG_DIRECTIONS:
            if tag in merged and merged[tag]:
                trend_summaries[tag] = _trend_summary(tag, merged[tag], expectations)
    if expectations.log_points != 333:
        issues.warning(
            "non_333_trend_evidence",
            "frozen early/middle/late windows are unavailable for this non-333-point evidence run",
            expected_log_points=expectations.log_points,
        )

    return {
        "event_files": [path.relative_to(run_dir).as_posix() for path in event_files],
        "event_file_count": len(event_files),
        "tag_inventory": {
            "expected_count": len(EXPECTED_SCALAR_TAGS),
            "expected_and_present": sorted(expected & present),
            "expected_but_missing": missing,
            "unexpected_extra_scalar_tags": extras,
            "present_but_empty": empty,
            "present_with_nonfinite_values": sorted({item["tag"] for item in nonfinite}),
            "present_with_duplicate_steps": sorted({item["tag"] for item in duplicate_points}),
            "allowed_sparse_expected_tags": [],
        },
        "step_coverage": step_coverage,
        "expected_step_sequence": {
            "first": expected_steps[0] if expected_steps else None,
            "final": expected_steps[-1] if expected_steps else None,
            "increment": expectations.episode_length * expectations.num_envs * expectations.log_interval,
            "point_count": len(expected_steps),
        },
        "duplicate_points": duplicate_points,
        "nonfinite_points": nonfinite,
        "cross_tag_invariants": cross_tag,
        "trend_windows": {
            "future_333_point_contract": {
                "early": {"point_indices": [1, 33], "steps": [300, 9900]},
                "middle": {"point_indices": [151, 183], "steps": [45300, 54900]},
                "late": {"point_indices": [301, 333], "steps": [90300, 99900]},
            }
        },
        "principal_tag_summaries": trend_summaries,
        "trend_status": trend_status,
        **load_metadata,
    }


def _audit_cross_tag_invariants(
    merged: Mapping[str, Sequence[_ScalarPoint]],
    expectations: AuditExpectations,
    issues: _Issues,
) -> dict[str, Any]:
    tolerance = 1.0e-5
    noop = {point.step: point.value for point in merged.get("assignment_rl.noop_count", ())}
    valid = {point.step: point.value for point in merged.get("assignment_rl.valid_action_count", ())}
    compared_steps = sorted(set(noop) & set(valid))
    residuals = {step: abs(noop[step] + valid[step] - expectations.num_agents) for step in compared_steps}
    violating = [step for step, residual in residuals.items() if residual > tolerance]
    if violating:
        issues.error(
            "noop_valid_count_invariant",
            "noop_count + valid_action_count differs from expected agent count",
            tolerance=tolerance,
            violating_steps=violating,
            maximum_residual=max(residuals.values()),
        )

    range_contracts = {
        "coverage_ratio": (0.0, 1.0),
        "assignment_rl.selected_available_mask": (0.0, 1.0),
        "assignment_rl.noop_count": (0.0, float(expectations.num_agents)),
        "assignment_rl.valid_action_count": (0.0, float(expectations.num_agents)),
    }
    range_results: dict[str, Any] = {}
    for tag, (lower, upper) in range_contracts.items():
        violations = [
            {"step": point.step, "value": point.value}
            for point in merged.get(tag, ())
            if math.isfinite(point.value) and not (lower - tolerance <= point.value <= upper + tolerance)
        ]
        range_results[tag] = {
            "minimum_allowed": lower,
            "maximum_allowed": upper,
            "violations": violations,
            "result": "PASS" if not violations else "FAIL",
        }
        if violations:
            issues.error("scalar_range_violation", "scalar violates a source-established range", tag=tag, violations=violations)

    budget_tags = (
        "assignment_cooldown.budget_ratio_mean",
        "assignment_cooldown.budget_ratio_max",
    )
    budget_results: dict[str, Any] = {}
    for tag in budget_tags:
        violations = [
            {"step": point.step, "value": point.value}
            for point in merged.get(tag, ())
            if math.isfinite(point.value) and point.value < -tolerance
        ]
        budget_results[tag] = {"minimum_allowed": 0.0, "violations": violations, "result": "PASS" if not violations else "FAIL"}
        if violations:
            issues.error("budget_ratio_negative", "budget ratio must be nonnegative", tag=tag, violations=violations)

    return {
        "noop_plus_valid_action": {
            "expected_sum": expectations.num_agents,
            "tolerance": tolerance,
            "compared_steps": len(compared_steps),
            "maximum_residual": max(residuals.values()) if residuals else None,
            "violating_steps": violating,
            "result": "PASS" if not violating and len(compared_steps) == expectations.log_points else "FAIL",
        },
        "range_contracts": range_results,
        "budget_nonnegative": budget_results,
    }


def _load_contract_manifest(path: Path, issues: _Issues, label: str) -> tuple[Mapping[str, Any] | None, str | None]:
    try:
        mapping = _read_json(path)
        validated = AssignmentCheckpointContractManifest.from_mapping(mapping)
        normalized = validated.to_mapping()
        fingerprint = compute_manifest_sha256(validated)
        return normalized, fingerprint
    except (OSError, ValueError, json.JSONDecodeError, ContractValidationError) as exc:
        issues.error("contract_manifest_invalid", "contract manifest is invalid", label=label, path=path, error=repr(exc))
        return None, None


def _read_fingerprint(path: Path, issues: _Issues, label: str) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        issues.error("fingerprint_unreadable", "contract fingerprint is unreadable", label=label, path=path, error=repr(exc))
        return None
    if _HEX_SHA256.fullmatch(value) is None:
        issues.error("fingerprint_invalid", "contract fingerprint is not lowercase SHA-256", label=label, path=path, value=value)
        return None
    return value


def _contract_check(
    checks: list[dict[str, Any]],
    issues: _Issues,
    manifest: Mapping[str, Any],
    path: Sequence[str],
    expected: Any,
) -> None:
    dotted = ".".join(path)
    _record_check(
        checks,
        issues,
        name=dotted,
        path=f"assignment_contract_manifest.json::{dotted}",
        actual=_nested(manifest, path),
        expected=expected,
    )


def _audit_contract_values(
    manifest: Mapping[str, Any], expectations: AuditExpectations, issues: _Issues
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    expected_names = [f"robot_{index}" for index in range(expectations.num_agents)]
    contract_checks = (
        (("manifest_format_version",), EXPECTED_MANIFEST_VERSION),
        (("identity", "profile_name"), expectations.profile),
        (("identity", "training_time_profile"), expectations.profile),
        (("identity", "algorithm_name"), expectations.algorithm),
        (("identity", "harl_state_type"), expectations.state_type),
        (("identity", "serialization_mode"), "state_dict"),
        (("scale", "M"), expectations.num_agents),
        (("scale", "N"), expectations.num_tasks),
        (("scale", "num_agents"), expectations.num_agents),
        (("scale", "ordered_agent_names"), expected_names),
        (("actor_schema", "actor_dimension"), expectations.actor_obs_width),
        (("shared_schema", "shared_dimension"), expectations.shared_obs_width),
        (("action_contract", "action_dimension"), expectations.action_width),
        (("action_contract", "noop_raw_id"), expectations.raw_noop_id),
        (("action_contract", "noop_decoded_value"), -1),
        (("policy_sequence_contract", "policy_sequence_mode"), "feed_forward"),
        (("policy_sequence_contract", "use_recurrent_policy"), False),
        (("policy_sequence_contract", "use_naive_recurrent_policy"), False),
        (("model_structure", "share_param"), False),
        (("model_structure", "number_of_actor_networks"), expectations.num_agents),
        (("model_structure", "ordered_actor_network_names"), expected_names),
        (("training_contract", "episode_length"), expectations.episode_length),
        (("training_contract", "rollout_thread_count"), expectations.num_envs),
        (("training_contract", "value_norm_enabled"), True),
        (("training_contract", "value_normalizer_contract", "enabled"), True),
        (
            ("training_contract", "value_normalizer_contract", "adapter_contract_version"),
            "harl_valuenorm_runtime_state_v1",
        ),
        (
            ("training_contract", "value_normalizer_contract", "artifact_state_format"),
            "harl_runtime_attribute_tensor_mapping_v1",
        ),
        (
            ("training_contract", "value_normalizer_contract", "canonical_state_keys"),
            ["running_mean", "running_mean_sq", "debiasing_term"],
        ),
    )
    for path, expected in contract_checks:
        _contract_check(checks, issues, manifest, path, expected)
    actor_dims = _nested(manifest, ("actor_schema", "actor_dimension_by_agent"), {})
    expected_actor_dims = {name: expectations.actor_obs_width for name in expected_names}
    _record_check(
        checks,
        issues,
        name="actor dimensions by agent",
        path="assignment_contract_manifest.json::actor_schema.actor_dimension_by_agent",
        actual=actor_dims,
        expected=expected_actor_dims,
    )
    return checks


def _audit_artifact_entry(
    child: Path,
    entry: Any,
    issues: _Issues,
    label: str,
) -> dict[str, Any]:
    path = child / entry.relative_file_name
    exists = path.is_file()
    actual_size = path.stat().st_size if exists else None
    actual_sha = _sha256_file(path) if exists else None
    size_ok = exists and actual_size == entry.file_size
    sha_ok = exists and actual_sha == entry.file_sha256
    if not exists:
        issues.error("checkpoint_artifact_missing", "declared checkpoint artifact is missing", checkpoint=label, artifact=entry.relative_file_name)
    elif actual_size == 0:
        issues.error("checkpoint_artifact_empty", "required checkpoint artifact is zero bytes", checkpoint=label, artifact=entry.relative_file_name)
    if exists and not size_ok:
        issues.error(
            "checkpoint_artifact_size_mismatch",
            "checkpoint artifact byte size differs from completion marker",
            checkpoint=label,
            artifact=entry.relative_file_name,
            expected_size=entry.file_size,
            actual_size=actual_size,
        )
    if exists and not sha_ok:
        issues.error(
            "checkpoint_artifact_sha256_mismatch",
            "checkpoint artifact SHA-256 differs from completion marker",
            checkpoint=label,
            artifact=entry.relative_file_name,
            expected_sha256=entry.file_sha256,
            actual_sha256=actual_sha,
        )
    inventory_ok = bool(entry.tensor_inventory) and bool(entry.tensor_inventory_sha256)
    if not inventory_ok:
        issues.error(
            "checkpoint_tensor_inventory_missing",
            "checkpoint artifact must declare a nonempty validated tensor inventory",
            checkpoint=label,
            artifact=entry.relative_file_name,
        )
    return {
        "artifact_role": entry.artifact_role,
        "actor_identity": entry.actor_identity,
        "relative_file_name": entry.relative_file_name,
        "exists": exists,
        "expected_size": entry.file_size,
        "actual_size": actual_size,
        "expected_sha256": entry.file_sha256,
        "actual_sha256": actual_sha,
        "size_result": "PASS" if size_ok else "FAIL",
        "sha256_result": "PASS" if sha_ok else "FAIL",
        "tensor_inventory_count": len(entry.tensor_inventory),
        "tensor_inventory_sha256": entry.tensor_inventory_sha256,
        "tensor_inventory_result": "PASS" if inventory_ok else "FAIL",
    }


def _audit_checkpoint_child(
    run_dir: Path,
    child_name: str,
    expected_kind: str,
    run_manifest: Mapping[str, Any] | None,
    run_fingerprint: str | None,
    expectations: AuditExpectations,
    issues: _Issues,
) -> dict[str, Any]:
    child = run_dir / child_name
    label = child_name
    required_files = {
        *(f"actor_agent_robot_{index}.pt" for index in range(expectations.num_agents)),
        "critic_agent.pt",
        "value_normalizer.pt",
        CONTRACT_MANIFEST_FILE,
        CONTRACT_FINGERPRINT_FILE,
        TRAINING_STATE_MANIFEST_FILE,
    }
    actual_files = {path.name for path in child.iterdir() if path.is_file()}
    missing_files = sorted(required_files - actual_files)
    extra_files = sorted(actual_files - required_files)
    for name in missing_files:
        issues.error("required_checkpoint_file_missing", "required checkpoint child file is missing", checkpoint=label, file=name)
    for name in extra_files:
        issues.warning("extra_checkpoint_file", "unrecognized non-forbidden checkpoint child file is present", checkpoint=label, file=name)
    for name in sorted(required_files & actual_files):
        if (child / name).stat().st_size == 0:
            issues.error("required_checkpoint_file_empty", "required checkpoint child file is zero bytes", checkpoint=label, file=name)

    child_manifest, computed_fingerprint = _load_contract_manifest(
        child / CONTRACT_MANIFEST_FILE, issues, label
    ) if (child / CONTRACT_MANIFEST_FILE).is_file() else (None, None)
    child_fingerprint = _read_fingerprint(
        child / CONTRACT_FINGERPRINT_FILE, issues, label
    ) if (child / CONTRACT_FINGERPRINT_FILE).is_file() else None
    if computed_fingerprint is not None and child_fingerprint != computed_fingerprint:
        issues.error(
            "child_fingerprint_mismatch",
            "checkpoint child fingerprint does not match canonical manifest",
            checkpoint=label,
            expected=computed_fingerprint,
            actual=child_fingerprint,
        )
    if run_fingerprint is not None and child_fingerprint != run_fingerprint:
        issues.error(
            "run_child_fingerprint_mismatch",
            "checkpoint child fingerprint differs from run-root fingerprint",
            checkpoint=label,
            run_root=run_fingerprint,
            child=child_fingerprint,
        )
    if run_manifest is not None and child_manifest is not None:
        try:
            same = canonical_manifest_bytes(run_manifest) == canonical_manifest_bytes(child_manifest)
        except ContractValidationError:
            same = False
        if not same:
            issues.error("run_child_manifest_mismatch", "checkpoint child contract differs from run-root contract", checkpoint=label)

    training_mapping: Mapping[str, Any] | None = None
    training_state: AssignmentTrainingStateManifest | None = None
    marker = child / TRAINING_STATE_MANIFEST_FILE
    if marker.is_file():
        try:
            training_mapping = _read_json(marker)
            training_state = AssignmentTrainingStateManifest.from_mapping(training_mapping)
        except Exception as exc:
            issues.error("training_state_manifest_invalid", "training-state completion marker is invalid", checkpoint=label, path=marker, error=repr(exc))
    artifacts: list[dict[str, Any]] = []
    if training_state is not None:
        if training_state.training_state_format_version != EXPECTED_TRAINING_STATE_VERSION:
            issues.error("training_state_version_mismatch", "training-state manifest version is wrong", checkpoint=label, actual=training_state.training_state_format_version)
        if training_state.checkpoint_kind != expected_kind:
            issues.error("checkpoint_kind_mismatch", "checkpoint child has the wrong checkpoint kind", checkpoint=label, expected=expected_kind, actual=training_state.checkpoint_kind)
        if training_state.contract_fingerprint != run_fingerprint:
            issues.error("training_state_contract_binding_mismatch", "training-state marker fingerprint differs from run-root contract", checkpoint=label, marker=training_state.contract_fingerprint, run_root=run_fingerprint)
        expected_identities = tuple(f"robot_{index}" for index in range(expectations.num_agents))
        if training_state.ordered_actor_identities != expected_identities:
            issues.error(
                "training_state_actor_identity_mismatch",
                "training-state actor identities must match the canonical agent order",
                checkpoint=label,
                expected=list(expected_identities),
                actual=list(training_state.ordered_actor_identities),
            )
        expected_actor_files = {
            identity: f"actor_agent_{identity}.pt" for identity in expected_identities
        }
        actual_actor_files = {
            entry.actor_identity: entry.relative_file_name for entry in training_state.actor_artifacts
        }
        if actual_actor_files != expected_actor_files:
            issues.error(
                "training_state_actor_artifact_mapping_mismatch",
                "actor identities must map to canonical actor artifact file names",
                checkpoint=label,
                expected=expected_actor_files,
                actual=actual_actor_files,
            )
        if training_state.critic_artifact is None:
            issues.error(
                "training_state_critic_artifact_missing",
                "training-state completion marker must declare the critic artifact",
                checkpoint=label,
            )
        elif training_state.critic_artifact.relative_file_name != "critic_agent.pt":
            issues.error(
                "training_state_critic_artifact_mapping_mismatch",
                "critic role must map to critic_agent.pt",
                checkpoint=label,
                actual=training_state.critic_artifact.relative_file_name,
            )
        if training_state.value_normalizer_artifact is None:
            issues.error(
                "training_state_value_normalizer_artifact_missing",
                "training-state completion marker must declare the ValueNorm artifact",
                checkpoint=label,
            )
        elif training_state.value_normalizer_artifact.relative_file_name != "value_normalizer.pt":
            issues.error(
                "training_state_value_normalizer_artifact_mapping_mismatch",
                "ValueNorm role must map to value_normalizer.pt",
                checkpoint=label,
                actual=training_state.value_normalizer_artifact.relative_file_name,
            )
        if training_state.continuation_classification != "validated_weight_continuation_candidate":
            issues.error(
                "training_state_continuation_classification_mismatch",
                "native lifecycle checkpoint must declare validated weight-continuation candidacy",
                checkpoint=label,
                expected="validated_weight_continuation_candidate",
                actual=training_state.continuation_classification,
            )
        unavailable_state = {
            "actor_optimizer_available": training_state.actor_optimizer_available,
            "critic_optimizer_available": training_state.critic_optimizer_available,
            "training_counters_available": training_state.training_counters_available,
            "rng_state_available": training_state.rng_state_available,
            "environment_resolver_state_available": training_state.environment_resolver_state_available,
            "rollout_buffer_state_available": training_state.rollout_buffer_state_available,
        }
        unexpected_available = sorted(name for name, available in unavailable_state.items() if available)
        if unexpected_available:
            issues.error(
                "training_state_availability_mismatch",
                "state-dict-only lifecycle checkpoint must not claim unavailable resume state",
                checkpoint=label,
                unexpectedly_available=unexpected_available,
            )
        entries = (
            *training_state.actor_artifacts,
            training_state.critic_artifact,
            training_state.value_normalizer_artifact,
        )
        for entry in entries:
            if entry is not None:
                artifacts.append(_audit_artifact_entry(child, entry, issues, label))

    tensor_inventory_metadata_valid = (
        training_state is not None
        and len(artifacts) == expectations.num_agents + 2
        and all(item["tensor_inventory_result"] == "PASS" for item in artifacts)
    )
    return {
        "path": str(child),
        "expected_kind": expected_kind,
        "required_files": sorted(required_files),
        "missing_files": missing_files,
        "extra_files": extra_files,
        "contract_manifest_valid": child_manifest is not None,
        "computed_fingerprint": computed_fingerprint,
        "fingerprint_file": child_fingerprint,
        "training_state_manifest_valid": training_state is not None,
        "checkpoint_kind": training_state.checkpoint_kind if training_state else None,
        "checkpoint_generation": training_state.checkpoint_generation if training_state else None,
        "continuation_classification": training_state.continuation_classification if training_state else None,
        "artifact_hashes": artifacts,
        "artifact_count": len(artifacts),
        "tensor_inventory_metadata_valid": tensor_inventory_metadata_valid,
    }


def _scan_legacy_and_temp(run_dir: Path, issues: _Issues) -> dict[str, Any]:
    temp_files: list[str] = []
    legacy_files: list[str] = []
    full_model_files: list[str] = []
    wrong_manifest_versions: list[dict[str, str]] = []
    for path in sorted((item for item in run_dir.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        relative = path.relative_to(run_dir).as_posix()
        name = path.name
        lower = name.lower()
        if lower.endswith((".tmp", ".partial", ".part")) or ".tmp." in lower:
            temp_files.append(relative)
        if _LEGACY_ACTOR.fullmatch(name):
            legacy_files.append(relative)
        if lower.endswith("_full.pt"):
            full_model_files.append(relative)
        if name == CONTRACT_MANIFEST_FILE:
            try:
                version = _read_json(path).get("manifest_format_version")
            except Exception:
                continue
            if version != EXPECTED_MANIFEST_VERSION:
                wrong_manifest_versions.append({"path": relative, "version": str(version)})
    for path in temp_files:
        issues.error("temporary_checkpoint_artifact", "temporary or partial checkpoint artifact remains", path=path)
    for path in legacy_files:
        issues.error("legacy_actor_artifact", "legacy numeric actor checkpoint artifact is forbidden", path=path)
    for path in full_model_files:
        issues.error("full_model_artifact", "inherited full-model checkpoint artifact is forbidden", path=path)
    for item in wrong_manifest_versions:
        issues.error("wrong_manifest_version", "checkpoint manifest is not native contract v2", **item)
    return {
        "temporary_or_partial_files": temp_files,
        "legacy_actor_files": legacy_files,
        "full_model_files": full_model_files,
        "wrong_manifest_versions": wrong_manifest_versions,
        "result": "PASS" if not (temp_files or legacy_files or full_model_files or wrong_manifest_versions) else "FAIL",
    }


def _audit_checkpoints(
    run_dir: Path, expectations: AuditExpectations, issues: _Issues
) -> dict[str, Any]:
    root_manifest_path = run_dir / CONTRACT_MANIFEST_FILE
    root_fingerprint_path = run_dir / CONTRACT_FINGERPRINT_FILE
    if not root_manifest_path.is_file():
        issues.error("run_root_manifest_missing", "run-root contract manifest is missing", path=root_manifest_path)
    if not root_fingerprint_path.is_file():
        issues.error("run_root_fingerprint_missing", "run-root contract fingerprint is missing", path=root_fingerprint_path)
    run_manifest, computed = _load_contract_manifest(
        root_manifest_path, issues, "run_root"
    ) if root_manifest_path.is_file() else (None, None)
    fingerprint = _read_fingerprint(
        root_fingerprint_path, issues, "run_root"
    ) if root_fingerprint_path.is_file() else None
    if computed is not None and fingerprint != computed:
        issues.error("run_root_fingerprint_mismatch", "run-root fingerprint does not match canonical manifest", expected=computed, actual=fingerprint)
    contract_checks = _audit_contract_values(run_manifest, expectations, issues) if run_manifest is not None else []

    best = _audit_checkpoint_child(
        run_dir, "best_model", "best", run_manifest, fingerprint, expectations, issues
    )
    final = _audit_checkpoint_child(
        run_dir, "models", "final", run_manifest, fingerprint, expectations, issues
    )
    best_generation = best["checkpoint_generation"]
    final_generation = final["checkpoint_generation"]
    ordered = (
        isinstance(best_generation, int)
        and not isinstance(best_generation, bool)
        and isinstance(final_generation, int)
        and not isinstance(final_generation, bool)
        and best_generation >= 0
        and final_generation > best_generation
    )
    if not ordered:
        issues.error(
            "checkpoint_generation_order",
            "final checkpoint generation must be a nonnegative integer newer than retained best",
            best_generation=best_generation,
            final_generation=final_generation,
        )
    regular_opportunities = expectations.rollouts // expectations.save_interval
    minimum_final_generation = 1 + regular_opportunities
    minimum_ok = isinstance(final_generation, int) and final_generation >= minimum_final_generation
    if not minimum_ok:
        issues.error(
            "checkpoint_generation_lower_bound",
            "final checkpoint generation is below the source-derived minimum",
            final_generation=final_generation,
            minimum_final_generation=minimum_final_generation,
            initial_best_saves=1,
            regular_save_opportunities=regular_opportunities,
        )

    legacy_scan = _scan_legacy_and_temp(run_dir, issues)
    return {
        "run_root_contract": {
            "manifest_path": str(root_manifest_path),
            "fingerprint_path": str(root_fingerprint_path),
            "manifest_valid": run_manifest is not None,
            "computed_fingerprint": computed,
            "fingerprint_file": fingerprint,
            "contract_checks": contract_checks,
        },
        "best_model": best,
        "final_models": final,
        "generation_order": {
            "best_generation": best_generation,
            "final_generation": final_generation,
            "final_newer_than_best": ordered,
            "regular_save_opportunities": regular_opportunities,
            "source_derived_minimum_final_generation": minimum_final_generation,
            "minimum_result": "PASS" if minimum_ok else "FAIL",
        },
        "artifact_hashes": {
            "best_model": best["artifact_hashes"],
            "models": final["artifact_hashes"],
        },
        "legacy_or_temp_scan": legacy_scan,
    }


def _progress_audit(run_dir: Path, issues: _Issues) -> dict[str, Any]:
    path = run_dir / "progress.txt"
    if not path.exists():
        issues.warning("progress_file_missing", "progress.txt is absent; authoritative completion evidence is used", path=path)
        return {"path": str(path), "exists": False, "size": None, "empty": None}
    size = path.stat().st_size
    if size == 0:
        issues.warning("progress_file_empty", "progress.txt is empty; authoritative completion evidence is used", path=path)
    return {"path": str(path), "exists": True, "size": size, "empty": size == 0}


def _classification(issues: _Issues) -> str:
    if issues.errors:
        return "FAIL"
    if issues.warnings:
        return "PASS WITH WARNINGS"
    return "PASS"


def render_assignment_training_run_audit_json(result: Mapping[str, Any]) -> str:
    """Render one already-built result deterministically and reject JSON non-finites."""

    return json.dumps(_json_safe(result), indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def _md_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_assignment_training_run_audit_markdown(result: Mapping[str, Any]) -> str:
    """Render a compact human-readable view of the machine-readable result."""

    lines = [
        "# Assignment Training Run Offline Audit",
        "",
        f"- Classification: `{result['classification']}`",
        f"- Audited path: `{result['run_dir']}`",
        f"- Scope: `{result['scope']}`",
        f"- Schema: `{result['schema_version']}`",
        f"- Tool: `{result['tool_metadata']['tool_version']}`",
        f"- Audit time: `{result['tool_metadata']['audit_timestamp']}`",
        "",
        "## Expected Contract",
        "",
        "```json",
        json.dumps(result["resolved_expectations"], indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
        "## Configuration And Fresh Start",
        "",
    ]
    config = result.get("config_audit", {})
    lines.extend(
        (
            f"- Checks passed/failed: `{config.get('passed', 0)}/{config.get('failed', 0)}`",
            f"- Fresh-start result: `{config.get('fresh_start', {}).get('result', 'not audited')}`",
            "",
        )
    )

    tensorboard = result.get("tensorboard_audit")
    if tensorboard is not None:
        inventory = tensorboard["tag_inventory"]
        nonfinite = tensorboard["nonfinite_points"]
        step_sequence = tensorboard["expected_step_sequence"]
        invariant = tensorboard["cross_tag_invariants"]["noop_plus_valid_action"]
        lines.extend(
            (
                "## TensorBoard",
                "",
                f"- Event files: `{tensorboard['event_file_count']}`",
                f"- Expected tags present: `{len(inventory['expected_and_present'])}/{inventory['expected_count']}`",
                f"- Missing/extra tags: `{len(inventory['expected_but_missing'])}/{len(inventory['unexpected_extra_scalar_tags'])}`",
                f"- Expected first/final step: `{step_sequence['first']}/{step_sequence['final']}`",
                f"- Nonfinite points: `{len(nonfinite)}`",
                f"- Noop + valid-action invariant: `{invariant['result']}`, max residual `{_md_value(invariant['maximum_residual'])}`",
                "",
                "### Early / Middle / Late Trends",
                "",
                "| Tag | Direction | Early mean | Middle mean | Late mean | Final | Best | Best step |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            )
        )
        for tag, summary in tensorboard["principal_tag_summaries"].items():
            windows = summary["windows"]
            lines.append(
                "| "
                + " | ".join(
                    (
                        tag,
                        summary["direction"],
                        _md_value(windows["early"]["mean"]),
                        _md_value(windows["middle"]["mean"]),
                        _md_value(windows["late"]["mean"]),
                        _md_value(summary["final_value"]),
                        _md_value(summary["best_observed_value"]),
                        _md_value(summary["best_step"]),
                    )
                )
                + " |"
            )
        lines.append("")

    checkpoint = result.get("checkpoint_audit")
    if checkpoint is not None:
        best = checkpoint["best_model"]
        final = checkpoint["final_models"]
        generation = checkpoint["generation_order"]
        artifact_failures = sum(
            item["size_result"] != "PASS" or item["sha256_result"] != "PASS"
            for child in (best, final)
            for item in child["artifact_hashes"]
        )
        lines.extend(
            (
                "## Checkpoints",
                "",
                f"- Best: kind `{best['checkpoint_kind']}`, generation `{best['checkpoint_generation']}`, marker valid `{best['training_state_manifest_valid']}`",
                f"- Final: kind `{final['checkpoint_kind']}`, generation `{final['checkpoint_generation']}`, marker valid `{final['training_state_manifest_valid']}`",
                f"- Final newer than best: `{generation['final_newer_than_best']}`",
                f"- Source-derived minimum final generation: `{generation['source_derived_minimum_final_generation']}`",
                f"- Artifact size/hash failures: `{artifact_failures}`",
                f"- Legacy/temp scan: `{checkpoint['legacy_or_temp_scan']['result']}`",
                "",
            )
        )

    lines.extend(("## Hard Failures", ""))
    if result["errors"]:
        for item in result["errors"]:
            lines.append(f"- `{item['code']}`: {item['message']} Evidence: `{json.dumps(item['evidence'], sort_keys=True)}`")
    else:
        lines.append("- None.")
    lines.extend(("", "## Warnings", ""))
    if result["warnings"]:
        for item in result["warnings"]:
            lines.append(f"- `{item['code']}`: {item['message']} Evidence: `{json.dumps(item['evidence'], sort_keys=True)}`")
    else:
        lines.append("- None.")
    lines.extend(("", "## Interpretation Boundary", ""))
    for limitation in result["limitations"]:
        lines.append(f"- {limitation}")
    lines.extend(("", "## Next Action", "", result["next_recommended_action"], ""))
    return "\n".join(lines)


def _write_outputs(output_dir: Path, result: Mapping[str, Any]) -> tuple[Path, Path]:
    json_text = render_assignment_training_run_audit_json(result)
    markdown_text = render_assignment_training_run_audit_markdown(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / AUDIT_JSON_FILE
    markdown_path = output_dir / AUDIT_MARKDOWN_FILE
    if json_path.exists() or markdown_path.exists():
        raise AuditPreflightError("audit output collision detected during final write")
    json_path.write_text(json_text, encoding="utf-8", newline="\n")
    try:
        markdown_path.write_text(markdown_text, encoding="utf-8", newline="\n")
    except Exception:
        json_path.unlink(missing_ok=True)
        raise
    return json_path, markdown_path


def audit_assignment_training_run(
    *,
    run_dir: str | Path,
    output_dir: str | Path,
    scope: str,
    expectations: AuditExpectations,
    audit_timestamp: str | None = None,
) -> dict[str, Any]:
    """Audit one timestamped run and write JSON/Markdown after safe preflight."""

    resolved_run, resolved_output, config, event_files = _preflight(
        Path(run_dir), Path(output_dir), scope
    )
    issues = _Issues()
    config_audit = _audit_config(config, expectations, issues)
    tensorboard_audit = (
        _audit_tensorboard(resolved_run, event_files, expectations, issues)
        if scope in {"full", "events"}
        else None
    )
    checkpoint_audit = (
        _audit_checkpoints(resolved_run, expectations, issues)
        if scope in {"full", "checkpoints"}
        else None
    )
    progress_audit = _progress_audit(resolved_run, issues)
    classification = _classification(issues)
    timestamp = audit_timestamp or datetime.now(timezone.utc).isoformat()
    limitations = [
        "Aggregate TensorBoard noop_count cannot identify which actor proposed noop.",
        "Per-agent execution, completion fairness, and resolver rejection causes require separately authorized attribution playback.",
        "Checkpoint artifacts were validated only as opaque bytes and were not restored or deserialized.",
        "Trend summaries do not establish convergence, generalization, or production readiness.",
    ]
    next_action = (
        "Review technical completion and trends, then authorize separate best/final attribution playback if appropriate."
        if classification in {"PASS", "PASS WITH WARNINGS"}
        else "Resolve the reported hard failures before policy-quality interpretation or playback authorization."
    )
    result: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "classification": classification,
        "run_dir": str(resolved_run),
        "scope": scope,
        "tool_metadata": {
            "tool_version": AUDIT_TOOL_VERSION,
            "audit_timestamp": timestamp,
            "offline_only": True,
            "checkpoint_tensor_deserialization": False,
        },
        "resolved_expectations": expectations.to_mapping(),
        "config_audit": config_audit,
        "tensorboard_audit": tensorboard_audit,
        "checkpoint_audit": checkpoint_audit,
        "progress_audit": progress_audit,
        "evidence": {
            "config_path": str(resolved_run / "configs.json"),
            "event_file_count": len(event_files),
            "checkpoint_children": ["best_model", "models"] if checkpoint_audit else [],
        },
        "trend_summaries": None if tensorboard_audit is None else tensorboard_audit["principal_tag_summaries"],
        "checkpoint_summaries": None
        if checkpoint_audit is None
        else {
            "best_model": checkpoint_audit["best_model"],
            "final_models": checkpoint_audit["final_models"],
            "generation_order": checkpoint_audit["generation_order"],
        },
        "artifact_inventory": None if checkpoint_audit is None else checkpoint_audit["artifact_hashes"],
        "errors": issues.errors,
        "warnings": issues.warnings,
        "limitations": limitations,
        "next_recommended_action": next_action,
        "output_files": {
            "json": str(resolved_output / AUDIT_JSON_FILE),
            "markdown": str(resolved_output / AUDIT_MARKDOWN_FILE),
        },
    }
    safe_result = _json_safe(result)
    _write_outputs(resolved_output, safe_result)
    return safe_result


__all__ = [
    "AUDIT_JSON_FILE",
    "AUDIT_MARKDOWN_FILE",
    "AUDIT_SCHEMA_VERSION",
    "AUDIT_TOOL_VERSION",
    "EXPECTED_SCALAR_TAGS",
    "PRINCIPAL_TAG_DIRECTIONS",
    "AuditExpectations",
    "AuditPreflightError",
    "audit_assignment_training_run",
    "render_assignment_training_run_audit_json",
    "render_assignment_training_run_audit_markdown",
]
