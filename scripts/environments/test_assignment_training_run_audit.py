"""Pure regressions for the Phase 9G-8I-0A offline training-run audit."""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import math
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_TASK_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
HARL_SCRIPT_SOURCE = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl"
for source in (SCAN_TASK_SOURCE, HARL_SCRIPT_SOURCE):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from assignment_checkpoint_contract import (  # noqa: E402
    ArtifactFileInventoryEntry,
    AssignmentCheckpointContractManifest,
    AssignmentTrainingStateManifest,
    StateDictTensorInventoryEntry,
    canonical_manifest_bytes,
    compute_manifest_sha256,
    compute_tensor_inventory_sha256,
)
from assignment_training_run_audit import (  # noqa: E402
    AUDIT_JSON_FILE,
    AUDIT_MARKDOWN_FILE,
    AUDIT_SCHEMA_VERSION,
    EXPECTED_SCALAR_TAGS,
    AuditExpectations,
    render_assignment_training_run_audit_json,
    render_assignment_training_run_audit_markdown,
)
from audit_assignment_training_run import main as audit_cli_main  # noqa: E402
from test_assignment_checkpoint_contract_core import _manifest_mapping  # noqa: E402


RUN_NAME = "seed-00001-2026-07-20-00-00-00"
EXP_NAME = "assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis"
EXPECTATIONS = AuditExpectations(
    exp_name=EXP_NAME,
    algorithm="happo",
    seed=1,
    num_envs=1,
    num_agents=3,
    num_tasks=50,
    episode_length=300,
    configured_num_env_steps=100000,
    final_step=99900,
    rollouts=333,
    log_points=333,
    save_interval=20,
    log_interval=1,
    profile="lifecycle_contract_c",
    actor_obs_width=1059,
    shared_obs_width=3183,
    action_width=51,
    raw_noop_id=50,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _assert(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_snapshot(root: Path) -> dict[str, tuple[int, str]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, _sha256(path))
        for path in sorted((item for item in root.rglob("*") if item.is_file()))
    }


def _configs(expectations: AuditExpectations) -> dict[str, Any]:
    return {
        "Args": {
            "task": expectations.task,
            "algorithm": expectations.algorithm,
            "assignment_rl": True,
            "seed": expectations.seed,
            "num_envs": expectations.num_envs,
            "assignment_episode_length": expectations.episode_length,
            "num_env_steps": expectations.configured_num_env_steps,
            "save_interval": expectations.save_interval,
            "log_interval": expectations.log_interval,
            "exp_name": expectations.exp_name,
            "expect_num_viewpoints": expectations.num_tasks,
            "dir": None,
            "acknowledge_weight_continuation_reset": False,
            "video": False,
        },
        "Algo Args": {
            "seed": {"seed": expectations.seed},
            "train": {
                "n_rollout_threads": expectations.num_envs,
                "num_env_steps": expectations.configured_num_env_steps,
                "episode_length": expectations.episode_length,
                "log_interval": expectations.log_interval,
                "eval_interval": expectations.save_interval,
                "model_dir": None,
            },
            "eval": {"use_eval": False},
            "model": {
                "use_recurrent_policy": False,
                "use_naive_recurrent_policy": False,
            },
            "algo": {"share_param": False},
        },
        "Env Args": {
            "config": (
                "ScanMobileManipulatorEnvCfg("
                f"assignment_lifecycle_profile='{expectations.profile}')"
            )
        },
    }


def _scalar_value(tag: str, index: int, total: int) -> float:
    progress = index / total
    noop = float(index % 4)
    special = {
        "coverage_ratio": progress,
        "new_viewpoints": 1.0 + float(index % 3),
        "duplicate_scans": float(index % 2),
        "reach_violation": 0.0,
        "mean_reward": -1.0 + 2.0 * progress,
        "Total_Reward": -3.0 + 6.0 * progress,
        "assignment_rl.noop_count": noop,
        "assignment_rl.valid_action_count": 3.0 - noop,
        "assignment_rl.selected_available_mask": 1.0,
        "assignment_cooldown.budget_ratio_mean": progress,
        "assignment_cooldown.budget_ratio_max": 2.0 * progress,
        "assignment_rl_reward/final_reward_mean": -0.5 + progress,
        "assignment_rl_reward/global_no_progress_mean": -0.1 * (1.0 - progress),
        "critic/value_loss": 1.0 / (1.0 + index),
        "critic/critic_grad_norm": 0.5 + progress,
        "critic/average_step_rewards": -0.25 + progress,
    }
    if tag in special:
        return special[tag]
    if tag.endswith("dist_entropy"):
        return 1.5 - 0.5 * progress
    if tag.endswith("policy_loss"):
        return 0.1 * math.sin(index / 10.0)
    if tag.endswith("actor_grad_norm"):
        return 0.25 + progress
    if tag.endswith("/ratio"):
        return 1.0
    return 0.01 * float(index % 11)


def _write_events(
    logs: Path,
    expectations: AuditExpectations,
    *,
    omitted_tag: str | None = None,
    override: Callable[[str, int, float], float] | None = None,
    step_override: Callable[[int, int], int] | None = None,
    subdirectory: str | None = None,
) -> Path:
    from tensorboard.compat.proto.event_pb2 import Event
    from tensorboard.compat.proto.summary_pb2 import Summary
    from tensorboard.summary.writer.event_file_writer import EventFileWriter

    destination = logs if subdirectory is None else logs / subdirectory
    destination.mkdir(parents=True, exist_ok=True)
    writer = EventFileWriter(str(destination), max_queue_size=1, flush_secs=1)
    for index in range(1, expectations.log_points + 1):
        step = expectations.episode_length * expectations.num_envs * expectations.log_interval * index
        if step_override is not None:
            step = step_override(index, step)
        values = []
        for tag in EXPECTED_SCALAR_TAGS:
            if tag == omitted_tag:
                continue
            scalar = _scalar_value(tag, index, expectations.log_points)
            if override is not None:
                scalar = override(tag, index, scalar)
            values.append(Summary.Value(tag=tag, simple_value=float(scalar)))
        writer.add_event(
            Event(
                wall_time=1_750_000_000.0 + index,
                step=step,
                summary=Summary(value=values),
            )
        )
    writer.flush()
    writer.close()
    return next(destination.glob("events.out.tfevents.*"))


def _write_duplicate_event(logs: Path, tag: str, step: int, value: float) -> None:
    from tensorboard.compat.proto.event_pb2 import Event
    from tensorboard.compat.proto.summary_pb2 import Summary
    from tensorboard.summary.writer.event_file_writer import EventFileWriter

    destination = logs / "duplicate"
    destination.mkdir(parents=True, exist_ok=True)
    writer = EventFileWriter(str(destination), max_queue_size=1, flush_secs=1)
    writer.add_event(
        Event(
            wall_time=1_760_000_000.0,
            step=step,
            summary=Summary(value=[Summary.Value(tag=tag, simple_value=float(value))]),
        )
    )
    writer.flush()
    writer.close()


def _contract(expectations: AuditExpectations) -> AssignmentCheckpointContractManifest:
    mapping = _manifest_mapping(
        profile=expectations.profile,
        m=expectations.num_agents,
        n=expectations.num_tasks,
    )
    mapping["training_contract"]["episode_length"] = expectations.episode_length
    mapping["training_contract"]["rollout_thread_count"] = expectations.num_envs
    return AssignmentCheckpointContractManifest.from_mapping(mapping)


def _artifact(
    child: Path,
    *,
    role: str,
    filename: str,
    actor_identity: str | None = None,
) -> ArtifactFileInventoryEntry:
    payload = f"opaque synthetic {role} {actor_identity or 'shared'}\n".encode("ascii")
    path = child / filename
    path.write_bytes(payload)
    if role == "value_normalizer":
        tensors = (
            StateDictTensorInventoryEntry("running_mean", (1,), "float32"),
            StateDictTensorInventoryEntry("running_mean_sq", (1,), "float32"),
            StateDictTensorInventoryEntry("debiasing_term", (), "float32"),
        )
    else:
        tensors = (
            StateDictTensorInventoryEntry("base.0.weight", (2, 2), "float32"),
            StateDictTensorInventoryEntry("base.0.bias", (2,), "float32"),
        )
    return ArtifactFileInventoryEntry(
        artifact_role=role,
        relative_file_name=filename,
        file_size=path.stat().st_size,
        file_sha256=_sha256(path),
        serialization_mode="state_dict",
        actor_identity=actor_identity,
        tensor_inventory=tensors,
        tensor_inventory_sha256=compute_tensor_inventory_sha256(tensors),
    )


def _write_checkpoint_child(
    child: Path,
    manifest: AssignmentCheckpointContractManifest,
    *,
    kind: str,
    generation: int,
    expectations: AuditExpectations,
) -> None:
    child.mkdir(parents=True, exist_ok=True)
    fingerprint = compute_manifest_sha256(manifest)
    (child / "assignment_contract_manifest.json").write_bytes(
        canonical_manifest_bytes(manifest) + b"\n"
    )
    (child / "assignment_contract_fingerprint.txt").write_text(
        fingerprint + "\n", encoding="ascii", newline="\n"
    )
    actor_entries = tuple(
        _artifact(
            child,
            role="actor",
            filename=f"actor_agent_robot_{index}.pt",
            actor_identity=f"robot_{index}",
        )
        for index in range(expectations.num_agents)
    )
    critic_entry = _artifact(child, role="critic", filename="critic_agent.pt")
    value_entry = _artifact(child, role="value_normalizer", filename="value_normalizer.pt")
    state = AssignmentTrainingStateManifest(
        contract_fingerprint=fingerprint,
        checkpoint_kind=kind,
        checkpoint_generation=generation,
        episode_or_update_index=None,
        continuation_classification="validated_weight_continuation_candidate",
        ordered_actor_identities=tuple(f"robot_{index}" for index in range(expectations.num_agents)),
        actor_artifacts=actor_entries,
        critic_artifact=critic_entry,
        value_normalizer_artifact=value_entry,
        actor_optimizer_available=False,
        critic_optimizer_available=False,
        training_counters_available=False,
        rng_state_available=False,
        environment_resolver_state_available=False,
        rollout_buffer_state_available=False,
    )
    _write_json(child / "assignment_training_state_manifest.json", state.to_mapping())


def _create_fixture(parent: Path, expectations: AuditExpectations = EXPECTATIONS) -> Path:
    run = parent / RUN_NAME
    run.mkdir(parents=True)
    _write_json(run / "configs.json", _configs(expectations))
    (run / "progress.txt").write_text("synthetic completed run\n", encoding="ascii", newline="\n")
    _write_events(run / "logs", expectations)
    manifest = _contract(expectations)
    fingerprint = compute_manifest_sha256(manifest)
    (run / "assignment_contract_manifest.json").write_bytes(
        canonical_manifest_bytes(manifest) + b"\n"
    )
    (run / "assignment_contract_fingerprint.txt").write_text(
        fingerprint + "\n", encoding="ascii", newline="\n"
    )
    _write_checkpoint_child(
        run / "best_model",
        manifest,
        kind="best",
        generation=0,
        expectations=expectations,
    )
    _write_checkpoint_child(
        run / "models",
        manifest,
        kind="final",
        generation=1 + expectations.rollouts // expectations.save_interval,
        expectations=expectations,
    )
    return run


def _cli_args(
    run: Path,
    output: Path,
    *,
    scope: str = "full",
    expectations: AuditExpectations = EXPECTATIONS,
) -> list[str]:
    return [
        "--run_dir",
        str(run),
        "--output_dir",
        str(output),
        "--scope",
        scope,
        "--expected-exp-name",
        expectations.exp_name,
        "--expected-algorithm",
        expectations.algorithm,
        "--expected-seed",
        str(expectations.seed),
        "--expected-num-envs",
        str(expectations.num_envs),
        "--expected-num-agents",
        str(expectations.num_agents),
        "--expected-num-tasks",
        str(expectations.num_tasks),
        "--expected-episode-length",
        str(expectations.episode_length),
        "--expected-configured-num-env-steps",
        str(expectations.configured_num_env_steps),
        "--expected-final-step",
        str(expectations.final_step),
        "--expected-rollouts",
        str(expectations.rollouts),
        "--expected-log-points",
        str(expectations.log_points),
        "--expected-save-interval",
        str(expectations.save_interval),
        "--expected-log-interval",
        str(expectations.log_interval),
        "--expected-profile",
        expectations.profile,
        "--expected-actor-obs-width",
        str(expectations.actor_obs_width),
        "--expected-shared-obs-width",
        str(expectations.shared_obs_width),
        "--expected-action-width",
        str(expectations.action_width),
        "--expected-raw-noop-id",
        str(expectations.raw_noop_id),
        "--expected-task",
        expectations.task,
        "--expected-state-type",
        expectations.state_type,
    ]


def _run_cli(
    run: Path,
    output: Path,
    *,
    scope: str = "full",
    expectations: AuditExpectations = EXPECTATIONS,
) -> tuple[int, dict[str, Any] | None, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = audit_cli_main(_cli_args(run, output, scope=scope, expectations=expectations))
    report = (
        _read_json(output / AUDIT_JSON_FILE)
        if code != 2 and (output / AUDIT_JSON_FILE).is_file()
        else None
    )
    return code, report, stdout.getvalue(), stderr.getvalue()


def _replace_events(
    run: Path,
    *,
    omitted_tag: str | None = None,
    override: Callable[[str, int, float], float] | None = None,
    step_override: Callable[[int, int], int] | None = None,
) -> None:
    shutil.rmtree(run / "logs")
    _write_events(
        run / "logs",
        EXPECTATIONS,
        omitted_tag=omitted_tag,
        override=override,
        step_override=step_override,
    )


def _mutate_json(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    value = _read_json(path)
    mutate(value)
    _write_json(path, value)


def test_success_fixture_and_deterministic_outputs() -> None:
    with tempfile.TemporaryDirectory(prefix="assignment_audit_success_") as temp:
        root = Path(temp)
        run = _create_fixture(root / "input")
        before = _tree_snapshot(run)
        output = root / "output"
        code, report, _, stderr = _run_cli(run, output)
        _assert(code == 0, f"success CLI exit: {code}; {stderr}")
        _assert(report is not None and report["classification"] == "PASS", "success classification")
        _assert(report["schema_version"] == AUDIT_SCHEMA_VERSION, "schema version")
        _assert(set(path.name for path in output.iterdir()) == {AUDIT_JSON_FILE, AUDIT_MARKDOWN_FILE}, "exact outputs")
        _assert(len(report["tensorboard_audit"]["tag_inventory"]["expected_and_present"]) == 63, "63 tags")
        _assert(all(item["point_count"] == 333 for item in report["tensorboard_audit"]["step_coverage"].values()), "333 points each")
        coverage = report["trend_summaries"]["coverage_ratio"]
        _assert(coverage["windows"]["early"]["point_count"] == 33, "early window")
        _assert(coverage["windows"]["middle"]["first_step"] == 45300, "middle start")
        _assert(coverage["windows"]["late"]["last_step"] == 99900, "late end")
        _assert(report["checkpoint_audit"]["generation_order"]["source_derived_minimum_final_generation"] == 17, "generation floor")
        for child in report["artifact_inventory"].values():
            _assert(all(item["size_result"] == "PASS" for item in child), "artifact sizes")
            _assert(all(item["sha256_result"] == "PASS" for item in child), "artifact hashes")
            _assert(all(item["tensor_inventory_result"] == "PASS" for item in child), "inventory digests")
        first_json = render_assignment_training_run_audit_json(report)
        second_json = render_assignment_training_run_audit_json(report)
        first_md = render_assignment_training_run_audit_markdown(report)
        second_md = render_assignment_training_run_audit_markdown(report)
        _assert(first_json == second_json and first_md == second_md, "deterministic rendering")
        json.loads(first_json)
        _assert("NaN" not in first_json and "Infinity" not in first_json, "standard finite JSON tokens")
        _assert(_tree_snapshot(run) == before, "audited input tree unchanged")


def _failure_case(
    template: Path,
    cases_root: Path,
    *,
    name: str,
    mutate: Callable[[Path, Path], Path | None],
    expected_evidence: str,
    scope: str = "full",
    expectations: AuditExpectations = EXPECTATIONS,
    preflight: bool = False,
) -> None:
    case_root = cases_root / name
    run = case_root / "input" / RUN_NAME
    shutil.copytree(template, run)
    output = case_root / "output"
    candidate = mutate(run, output)
    selected = candidate if isinstance(candidate, Path) else run
    before = _tree_snapshot(run)
    output_before = _tree_snapshot(output) if output.exists() else None
    code, report, stdout, stderr = _run_cli(
        selected,
        output,
        scope=scope,
        expectations=expectations,
    )
    _assert(code != 0, f"{name}: failure must return nonzero")
    evidence = stdout + stderr + (json.dumps(report, sort_keys=True) if report is not None else "")
    _assert(expected_evidence in evidence, f"{name}: missing evidence {expected_evidence!r}")
    if preflight:
        _assert(report is None, f"{name}: preflight must not produce a report")
        output_after = _tree_snapshot(output) if output.exists() else None
        _assert(output_after == output_before, f"{name}: preflight changed output state")
    else:
        _assert(report is not None and report["classification"] == "FAIL", f"{name}: FAIL report")
        _assert((output / AUDIT_MARKDOWN_FILE).is_file(), f"{name}: Markdown failure report")
    _assert(_tree_snapshot(run) == before, f"{name}: audit changed input")


def test_required_failure_matrix() -> None:
    with tempfile.TemporaryDirectory(prefix="assignment_audit_failures_") as temp:
        root = Path(temp)
        template = _create_fixture(root / "template_parent")
        cases = root / "cases"

        def remove(path: str) -> Callable[[Path, Path], None]:
            def mutate(run: Path, _output: Path) -> None:
                target = run / path
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()

            return mutate

        def config_change(path: tuple[str, ...], value: Any) -> Callable[[Path, Path], None]:
            def mutate(run: Path, _output: Path) -> None:
                def apply(mapping: dict[str, Any]) -> None:
                    target: dict[str, Any] = mapping
                    for key in path[:-1]:
                        target = target[key]
                    target[path[-1]] = value

                _mutate_json(run / "configs.json", apply)

            return mutate

        cases_spec: list[dict[str, Any]] = [
            dict(name="missing_configs", mutate=remove("configs.json"), expected_evidence="configs.json is missing", preflight=True),
            dict(name="nonfresh_cli_dir", mutate=config_change(("Args", "dir"), "old/models"), expected_evidence="Args.dir", scope="checkpoints"),
            dict(name="nonfresh_model_dir", mutate=config_change(("Algo Args", "train", "model_dir"), "old/models"), expected_evidence="model_dir", scope="checkpoints"),
            dict(name="wrong_algorithm", mutate=config_change(("Args", "algorithm"), "hatrpo"), expected_evidence="Args.algorithm", scope="checkpoints"),
            dict(name="wrong_seed", mutate=config_change(("Args", "seed"), 7), expected_evidence="Args.seed", scope="checkpoints"),
            dict(name="wrong_profile", mutate=lambda run, _out: _mutate_json(run / "configs.json", lambda cfg: cfg["Env Args"].__setitem__("config", "ScanMobileManipulatorEnvCfg(assignment_lifecycle_profile='legacy')")), expected_evidence="lifecycle profile", scope="checkpoints"),
            dict(name="wrong_m", mutate=lambda _run, _out: None, expected_evidence="scale.M", scope="checkpoints", expectations=replace(EXPECTATIONS, num_agents=4)),
            dict(name="wrong_n", mutate=lambda _run, _out: None, expected_evidence="scale.N", scope="checkpoints", expectations=replace(EXPECTATIONS, num_tasks=49)),
            dict(name="wrong_actor_width", mutate=lambda _run, _out: None, expected_evidence="actor_schema.actor_dimension", scope="checkpoints", expectations=replace(EXPECTATIONS, actor_obs_width=1060)),
            dict(name="missing_event_file", mutate=remove("logs"), expected_evidence="logs directory is missing", scope="events", preflight=True),
            dict(name="missing_expected_tag", mutate=lambda run, _out: _replace_events(run, omitted_tag="coverage_ratio"), expected_evidence="expected_scalar_tag_missing", scope="events"),
            dict(name="nonfinite_scalar", mutate=lambda run, _out: _replace_events(run, override=lambda tag, index, value: float("nan") if tag == "mean_reward" and index == 5 else value), expected_evidence="nonfinite_scalar", scope="events"),
            dict(name="wrong_final_step", mutate=lambda run, _out: _replace_events(run, step_override=lambda index, step: step + 300 if index == 333 else step), expected_evidence="scalar_step_coverage_mismatch", scope="events"),
            dict(name="conflicting_duplicate", mutate=lambda run, _out: _write_duplicate_event(run / "logs", "coverage_ratio", 300, 0.75), expected_evidence="conflicting_duplicate_scalar", scope="events"),
            dict(name="noop_invariant", mutate=lambda run, _out: _replace_events(run, override=lambda tag, index, value: 0.0 if tag == "assignment_rl.valid_action_count" and index == 1 else value), expected_evidence="noop_valid_count_invariant", scope="events"),
            dict(name="coverage_out_of_range", mutate=lambda run, _out: _replace_events(run, override=lambda tag, index, value: 1.5 if tag == "coverage_ratio" and index == 10 else value), expected_evidence="scalar_range_violation", scope="events"),
            dict(name="missing_best_model", mutate=remove("best_model"), expected_evidence="required checkpoint directory is missing", scope="checkpoints", preflight=True),
            dict(name="missing_models", mutate=remove("models"), expected_evidence="required checkpoint directory is missing", scope="checkpoints", preflight=True),
            dict(name="wrong_checkpoint_kind", mutate=lambda run, _out: _mutate_json(run / "models" / "assignment_training_state_manifest.json", lambda state: state.__setitem__("checkpoint_kind", "regular")), expected_evidence="checkpoint_kind_mismatch", scope="checkpoints"),
            dict(name="generation_order", mutate=lambda run, _out: _mutate_json(run / "best_model" / "assignment_training_state_manifest.json", lambda state: state.__setitem__("checkpoint_generation", 17)), expected_evidence="checkpoint_generation_order", scope="checkpoints"),
            dict(name="missing_actor", mutate=remove("models/actor_agent_robot_1.pt"), expected_evidence="required_checkpoint_file_missing", scope="checkpoints"),
            dict(name="missing_critic", mutate=remove("models/critic_agent.pt"), expected_evidence="required_checkpoint_file_missing", scope="checkpoints"),
            dict(name="missing_valuenorm", mutate=remove("models/value_normalizer.pt"), expected_evidence="required_checkpoint_file_missing", scope="checkpoints"),
            dict(name="missing_completion_marker", mutate=remove("models/assignment_training_state_manifest.json"), expected_evidence="required_checkpoint_file_missing", scope="checkpoints"),
            dict(name="fingerprint_mismatch", mutate=lambda run, _out: (run / "models" / "assignment_contract_fingerprint.txt").write_text("a" * 64 + "\n", encoding="ascii"), expected_evidence="child_fingerprint_mismatch", scope="checkpoints"),
            dict(name="artifact_size_mismatch", mutate=lambda run, _out: _mutate_json(run / "models" / "assignment_training_state_manifest.json", lambda state: state["actor_artifacts"][0].__setitem__("file_size", state["actor_artifacts"][0]["file_size"] + 1)), expected_evidence="checkpoint_artifact_size_mismatch", scope="checkpoints"),
            dict(name="artifact_sha_mismatch", mutate=lambda run, _out: _mutate_json(run / "models" / "assignment_training_state_manifest.json", lambda state: state["actor_artifacts"][0].__setitem__("file_sha256", "a" * 64)), expected_evidence="checkpoint_artifact_sha256_mismatch", scope="checkpoints"),
            dict(name="temporary_artifact", mutate=lambda run, _out: (run / "models" / "checkpoint.partial").write_bytes(b"partial"), expected_evidence="temporary_checkpoint_artifact", scope="checkpoints"),
            dict(name="legacy_actor", mutate=lambda run, _out: (run / "models" / "actor_agent0.pt").write_bytes(b"legacy"), expected_evidence="legacy_actor_artifact", scope="checkpoints"),
            dict(name="output_collision", mutate=lambda _run, output: (output.mkdir(parents=True), (output / AUDIT_JSON_FILE).write_text("{}", encoding="ascii")), expected_evidence="audit output already exists", preflight=True),
            dict(name="experiment_parent", mutate=lambda run, _out: run.parent, expected_evidence="exact timestamped seed directory", preflight=True),
        ]
        for spec in cases_spec:
            _failure_case(template, cases, **spec)


def test_warning_and_deduplication_classification() -> None:
    with tempfile.TemporaryDirectory(prefix="assignment_audit_warning_") as temp:
        root = Path(temp)
        run = _create_fixture(root / "input")
        expected = _scalar_value("coverage_ratio", 1, EXPECTATIONS.log_points)
        _write_duplicate_event(run / "logs", "coverage_ratio", 300, expected)
        code, report, _, _ = _run_cli(run, root / "output", scope="events")
        _assert(code == 0, "warning exit code")
        _assert(report is not None and report["classification"] == "PASS WITH WARNINGS", "warning classification")
        _assert(any(item["code"] == "identical_duplicate_scalar" for item in report["warnings"]), "dedup warning")


def test_architecture_and_import_isolation() -> None:
    module_path = SCAN_TASK_SOURCE / "assignment_training_run_audit.py"
    cli_path = HARL_SCRIPT_SOURCE / "audit_assignment_training_run.py"
    module_text = module_path.read_text(encoding="utf-8")
    cli_text = cli_path.read_text(encoding="utf-8")
    forbidden_call = "torch" + ".load("
    for text, label in ((module_text, "module"), (cli_text, "CLI")):
        _assert(forbidden_call not in text, f"{label} checkpoint deserialization boundary")
        _assert("AppLauncher" not in text, f"{label} AppLauncher isolation")
        _assert("import omni" not in text and "from omni" not in text, f"{label} omni isolation")
        _assert("import isaac" not in text and "from isaac" not in text, f"{label} Isaac runtime isolation")
        _assert("import harl" not in text and "from harl" not in text, f"{label} HARL runtime isolation")
    for entry in (
        HARL_SCRIPT_SOURCE / "train.py",
        HARL_SCRIPT_SOURCE / "play_assignment.py",
    ):
        text = entry.read_text(encoding="utf-8")
        _assert("assignment_training_run_audit" not in text, f"offline module not imported by {entry.name}")
        _assert("audit_assignment_training_run" not in text, f"offline CLI not imported by {entry.name}")


TESTS = (
    test_success_fixture_and_deterministic_outputs,
    test_required_failure_matrix,
    test_warning_and_deduplication_classification,
    test_architecture_and_import_isolation,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone regression runner.
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    failed = sum(item["status"] == "failed" for item in results)
    output = {
        "status": "failed" if failed else "passed",
        "num_test_groups": len(results),
        "passed": len(results) - failed,
        "failed": failed,
        "synthetic_success_fixtures": 1,
        "required_failure_cases": 31,
        "tests": results,
    }
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        for item in results:
            suffix = "" if item["status"] == "passed" else f": {item['error']}"
            print(f"{item['status'].upper()} {item['name']}{suffix}")
        print(f"{'FAIL' if failed else 'PASS'} {len(results) - failed}/{len(results)} groups")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
