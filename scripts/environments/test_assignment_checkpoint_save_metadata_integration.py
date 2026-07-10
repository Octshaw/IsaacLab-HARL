"""Phase 9G-8F-2 assignment checkpoint save metadata integration tests."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import torch


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
from assignment_checkpoint_contract import (  # noqa: E402
    AssignmentCheckpointContractManifest,
    AssignmentTrainingStateManifest,
    canonical_manifest_bytes,
    compute_manifest_sha256,
)
from assignment_checkpoint_save import (  # noqa: E402
    CONTRACT_FINGERPRINT_FILE,
    CONTRACT_MANIFEST_FILE,
    FAIL_AFTER_ALL_ACTORS,
    FAIL_AFTER_CHILD_CONTRACT,
    FAIL_AFTER_CRITIC,
    FAIL_AFTER_FIRST_ACTOR,
    FAIL_AFTER_MARKER_INVALIDATION,
    FAIL_AFTER_VALUE_NORMALIZER,
    TRAINING_STATE_MANIFEST_FILE,
    AssignmentCheckpointRuntimeState,
    AssignmentCheckpointSaveCoordinator,
    AssignmentCheckpointSaveError,
    build_assignment_checkpoint_contract_manifest,
    build_tensor_inventory_from_state_dict,
    capture_assignment_checkpoint_runtime_state,
    ensure_contract_metadata_pair,
    infer_assignment_checkpoint_kind,
)
from assignment_harl_training import AssignmentOnPolicyHARunner  # noqa: E402
from harl.runners.on_policy_ha_runner import OnPolicyHARunner  # noqa: E402


TASK_ROW_LEGACY = (
    "relative_viewpoint_position_x",
    "relative_viewpoint_position_y",
    "relative_viewpoint_position_z",
    "viewpoint_quaternion_w",
    "viewpoint_quaternion_x",
    "viewpoint_quaternion_y",
    "viewpoint_quaternion_z",
    "covered_flag",
    "available_flag",
    "feasible_flag",
    "static_geometric_feasible_flag",
    "normalized_selected_path_cost",
    "per_viewpoint_attempted_count_norm",
    "per_viewpoint_last_attempt_age_norm",
)
TASK_ROW_LIFECYCLE = TASK_ROW_LEGACY + (
    "self_active_target",
    "task_owned_by_teammate",
    "self_pair_failed_or_released",
)
NOOP_FIELDS = (
    "agent_has_any_available_viewpoint",
    "team_has_any_available_viewpoint",
    "all_viewpoints_covered",
    "previous_assignment_was_noop",
    "episode_progress_norm",
)
DYNAMIC_FIELDS = (
    "consecutive_same_target_count_norm",
    "steps_since_last_global_coverage_gain_norm",
    "per_robot_completed_count_norm",
    "per_robot_repeated_assignment_count_norm",
    "global_coverage_ratio",
    "total_uncovered_count_norm",
    "episode_progress_norm",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], *expected: str) -> None:
    try:
        func()
    except (AssignmentCheckpointSaveError, RuntimeError, TypeError, ValueError) as exc:
        message = str(exc)
        for text in expected:
            if text not in message:
                raise AssertionError(f"expected {text!r} in {message!r}") from exc
        return
    raise AssertionError(f"expected an error containing {expected!r}")


def _wrapper_contract(profile: str) -> tuple[dict[str, Any], dict[str, Any]]:
    lifecycle = profile == "lifecycle_contract_c"
    m, n = 3, 50
    names = tuple(f"robot_{index}" for index in range(m))
    row_fields = TASK_ROW_LIFECYCLE if lifecycle else TASK_ROW_LEGACY
    raw_dim = 87 + 3 * m
    actor_dim = raw_dim + n * len(row_fields) + 5 + (n + 1) + 7 + n
    shared_dim = m * actor_dim + (2 * m if lifecycle else 0)
    shared_blocks: list[dict[str, Any]] = [
        {"name": f"actor_obs_robot_{index}", "agent": name, "shape": [actor_dim]}
        for index, name in enumerate(names)
    ]
    if lifecycle:
        for index in range(m):
            shared_blocks.extend(
                (
                    {
                        "name": f"active_budget_progress_norm_robot_{index}",
                        "robot_id": index,
                        "shape": [1],
                    },
                    {
                        "name": f"active_budget_step_fraction_robot_{index}",
                        "robot_id": index,
                        "shape": [1],
                    },
                )
            )
    schema = {
        "profile_name": profile,
        "actor_schema_version": "lifecycle_v1_actor_3n" if lifecycle else "legacy_v1",
        "actor_task_row_order": list(row_fields),
        "actor_tail_field_order": (
            list(NOOP_FIELDS)
            + [f"previous_assignment_one_hot_{index}" for index in range(n + 1)]
            + list(DYNAMIC_FIELDS)
            + [f"covered_vector_{index}" for index in range(n)]
        ),
        "actor_dimension": actor_dim,
        "actor_dimension_by_agent": {name: actor_dim for name in names},
        "shared_schema_version": (
            "lifecycle_v1_shared_option_a_budget2m"
            if lifecycle
            else "legacy_v1_shared_actor_concat"
        ),
        "critic_budget_schema_version": "lifecycle_v1_critic_budget_2m" if lifecycle else None,
        "shared_construction_mode": (
            "actor_concat_plus_critic_budget_2m" if lifecycle else "actor_concat"
        ),
        "shared_ordered_blocks": shared_blocks,
        "shared_dimension": shared_dim,
        "mask_contract_version": "lifecycle_contract_c_mask_v1" if lifecycle else "legacy_mask_v1",
        "budget_release_contract": "budget_release_v1" if lifecycle else "disabled",
        "legacy_guardrail_profile": (
            "lifecycle_no_legacy_guardrails_v1" if lifecycle else "legacy_guardrails_v1"
        ),
        "M": m,
        "N": n,
        "action_dimension": n + 1,
        "noop_raw_id": n,
        "noop_decoded_value": -1,
        "snapshot_contract_version": "lifecycle_decision_snapshot_v1",
    }
    layout = {
        "raw_observation_dim": raw_dim,
        "viewpoint_row_dim": len(row_fields),
        "noop_context_dim": len(NOOP_FIELDS),
        "previous_assignment_one_hot_dim": n + 1,
        "dynamic_scalar_fields": list(DYNAMIC_FIELDS),
        "covered_vector_dim": n,
    }
    return schema, layout


def _runtime_state(
    profile: str = "lifecycle_contract_c",
    *,
    value_norm: bool = True,
) -> AssignmentCheckpointRuntimeState:
    schema, layout = _wrapper_contract(profile)
    names = tuple(schema["actor_dimension_by_agent"])
    return AssignmentCheckpointRuntimeState(
        wrapper_schema_manifest=schema,
        wrapper_observation_layout=layout,
        profile_name=profile,
        algorithm_name="happo",
        harl_state_type="EP",
        ordered_agent_names=names,
        actor_input_dimensions_by_agent=dict(schema["actor_dimension_by_agent"]),
        critic_input_dimension=schema["shared_dimension"],
        actor_action_dimensions_by_agent={name: 51 for name in names},
        actor_class="HAPPO/StochasticPolicy",
        critic_class="VCritic/VNet",
        action_distribution_class="Categorical",
        actor_hidden_sizes=(256, 256),
        critic_hidden_sizes=(256, 256),
        activation="relu",
        feature_normalization=True,
        share_param=False,
        number_of_actor_networks=3,
        ordered_actor_network_names=names,
        critic_architecture="centralized_v_network",
        recurrent_n=1,
        initialization_method="orthogonal_",
        action_gain=0.01,
        use_recurrent_policy=False,
        use_naive_recurrent_policy=False,
        actor_buffer_generator="feed_forward_generator_actor",
        optimizer_class="Adam",
        actor_learning_rate=0.0005,
        critic_learning_rate=0.0005,
        optimizer_epsilon=0.00001,
        weight_decay=0.0,
        ppo_epochs=5,
        actor_minibatches=2,
        critic_minibatches=2,
        clip_coefficient=0.2,
        value_loss_coefficient=1.0,
        entropy_coefficient=0.01,
        gradient_clipping_enabled=True,
        max_gradient_norm=10.0,
        gamma=0.99,
        gae_lambda=0.95,
        value_norm_enabled=value_norm,
        proper_time_limits=True,
        episode_length=1000,
        rollout_thread_count=20,
    )


def _manifest(
    profile: str = "lifecycle_contract_c",
    *,
    value_norm: bool = True,
) -> AssignmentCheckpointContractManifest:
    return build_assignment_checkpoint_contract_manifest(
        _runtime_state(profile, value_norm=value_norm)
    )


def _state_dict(seed: int) -> dict[str, torch.Tensor]:
    return {
        "base.weight": torch.arange(seed, seed + 6, dtype=torch.float32).reshape(2, 3),
        "base.bias": torch.tensor([seed, seed + 1], dtype=torch.float32),
        "counter": torch.tensor(seed, dtype=torch.int64),
    }


def _artifacts(
    manifest: AssignmentCheckpointContractManifest,
    *,
    value_norm: bool = True,
) -> tuple[
    tuple[tuple[str, dict[str, torch.Tensor]], ...],
    dict[str, torch.Tensor],
    dict[str, torch.Tensor] | None,
]:
    actors = tuple(
        (name, _state_dict(index + 1))
        for index, name in enumerate(manifest.scale["ordered_agent_names"])
    )
    critic = _state_dict(20)
    normalizer = _state_dict(30) if value_norm else None
    return actors, critic, normalizer


def _read_training_state(directory: Path) -> AssignmentTrainingStateManifest:
    mapping = json.loads((directory / TRAINING_STATE_MANIFEST_FILE).read_text(encoding="utf-8"))
    return AssignmentTrainingStateManifest.from_mapping(mapping)


def _save(
    coordinator: AssignmentCheckpointSaveCoordinator,
    manifest: AssignmentCheckpointContractManifest,
    directory: Path,
    *,
    kind: str,
    generation: int,
    index: int | None = None,
    value_norm: bool = True,
):
    actors, critic, normalizer = _artifacts(manifest, value_norm=value_norm)
    return coordinator.save_checkpoint(
        checkpoint_directory=directory,
        checkpoint_kind=kind,
        checkpoint_generation=generation,
        manifest=manifest,
        actor_state_dicts=actors,
        critic_state_dict=critic,
        value_normalizer_state_dict=normalizer,
        episode_or_update_index=index,
    )


def test_runtime_manifest_lifecycle_and_legacy() -> None:
    lifecycle = _manifest()
    legacy = _manifest("legacy")
    _assert(lifecycle.actor_schema["actor_dimension"] == 1059, "lifecycle actor dim")
    _assert(lifecycle.shared_schema["shared_dimension"] == 3183, "lifecycle shared dim")
    _assert(legacy.actor_schema["actor_dimension"] == 909, "legacy actor dim")
    _assert(legacy.shared_schema["shared_dimension"] == 2727, "legacy shared dim")
    _assert(lifecycle.model_structure["critic_hidden_sizes"] == (256, 256), "effective critic sizes")
    _assert("hidden_sizes_critic" not in lifecycle.to_mapping()["model_structure"], "unused YAML excluded")
    _assert(
        tuple(lifecycle.scale["ordered_agent_names"]) == ("robot_0", "robot_1", "robot_2"),
        "actor identity order",
    )


def test_runtime_manifest_consistency_rejections() -> None:
    runtime = _runtime_state()
    changed = copy.copy(runtime)
    object.__setattr__(changed, "critic_input_dimension", 3182)
    _expect_raises(
        lambda: build_assignment_checkpoint_contract_manifest(changed),
        "critic input dimension",
    )
    changed = copy.copy(runtime)
    object.__setattr__(changed, "share_param", True)
    _expect_raises(
        lambda: build_assignment_checkpoint_contract_manifest(changed),
        "share_param=False",
    )
    changed = copy.copy(runtime)
    object.__setattr__(changed, "use_recurrent_policy", True)
    object.__setattr__(changed, "actor_buffer_generator", "recurrent_generator_actor")
    _expect_raises(
        lambda: build_assignment_checkpoint_contract_manifest(changed),
        "recurrent flags",
    )
    changed = copy.copy(runtime)
    object.__setattr__(changed, "harl_state_type", "FP")
    _expect_raises(
        lambda: build_assignment_checkpoint_contract_manifest(changed),
        "requires HARL EP",
    )


class Adam:
    pass


class Categorical:
    def __init__(self, outputs: int) -> None:
        self.linear = SimpleNamespace(out_features=outputs)


class StochasticPolicy:
    def __init__(self) -> None:
        self.hidden_sizes = [256, 256]
        self.base = SimpleNamespace(activation_func="relu", use_feature_normalization=True)
        self.initialization_method = "orthogonal_"
        self.gain = 0.01
        self.use_recurrent_policy = False
        self.use_naive_recurrent_policy = False
        self.recurrent_n = 1
        self.act = SimpleNamespace(action_out=Categorical(51))

    def state_dict(self):
        return _state_dict(1)


class HAPPO:
    def __init__(self) -> None:
        self.actor = StochasticPolicy()
        self.obs_space_size = 1059
        self.act_space = SimpleNamespace(n=51)
        self.actor_optimizer = Adam()
        self.lr = 0.0005
        self.opti_eps = 0.00001
        self.weight_decay = 0.0
        self.ppo_epoch = 5
        self.actor_num_mini_batch = 2
        self.clip_param = 0.2
        self.use_max_grad_norm = True
        self.max_grad_norm = 10.0
        self.entropy_coef = 0.01


class VNet:
    def __init__(self) -> None:
        self.hidden_sizes = [256, 256]
        self.base = SimpleNamespace(activation_func="relu", use_feature_normalization=True)
        self.initialization_method = "orthogonal_"
        self.use_recurrent_policy = False
        self.use_naive_recurrent_policy = False
        self.recurrent_n = 1

    def state_dict(self):
        return _state_dict(20)


class VCritic:
    def __init__(self) -> None:
        self.critic = VNet()
        self.share_obs_space = SimpleNamespace(shape=(3183,))
        self.critic_optimizer = Adam()
        self.critic_lr = 0.0005
        self.opti_eps = 0.00001
        self.weight_decay = 0.0
        self.clip_param = 0.2
        self.use_max_grad_norm = True
        self.max_grad_norm = 10.0
        self.critic_num_mini_batch = 2
        self.value_loss_coef = 1.0


def test_capture_effective_constructed_runtime_values() -> None:
    schema, layout = _wrapper_contract("lifecycle_contract_c")
    wrapper = SimpleNamespace(
        assignment_observation_schema_manifest=schema,
        assignment_observation_layout=layout,
        assignment_lifecycle_profile_config={"profile_name": "lifecycle_contract_c"},
        agents=("robot_0", "robot_1", "robot_2"),
    )
    runner = SimpleNamespace(
        env=SimpleNamespace(assignment_env=wrapper),
        actor=[HAPPO(), HAPPO(), HAPPO()],
        critic=VCritic(),
        critic_buffer=SimpleNamespace(
            gamma=0.99,
            gae_lambda=0.95,
            use_proper_time_limits=True,
            episode_length=1000,
            n_rollout_threads=20,
        ),
        value_normalizer=SimpleNamespace(),
        algo_args={
            "model": {"hidden_sizes_critic": [512, 256]},
            "train": {"use_valuenorm": True},
        },
        args={"algo": "happo"},
        state_type="EP",
        share_param=False,
    )
    runtime = capture_assignment_checkpoint_runtime_state(runner)
    manifest = build_assignment_checkpoint_contract_manifest(runtime)
    _assert(runtime.critic_hidden_sizes == (256, 256), "constructed critic sizes")
    _assert(manifest.model_structure["critic_hidden_sizes"] == (256, 256), "manifest critic sizes")
    _assert(manifest.model_structure["actor_class"] == "HAPPO/StochasticPolicy", "actual classes")
    _assert(manifest.model_structure["critic_class"] == "VCritic/VNet", "actual critic classes")


def test_run_root_metadata_pair() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest()
        expected_manifest = canonical_manifest_bytes(manifest) + b"\n"
        expected_fingerprint = compute_manifest_sha256(manifest).encode("ascii") + b"\n"
        first = ensure_contract_metadata_pair(root, manifest)
        second = ensure_contract_metadata_pair(root, manifest)
        _assert(first == second, "idempotent pair")
        _assert((root / CONTRACT_MANIFEST_FILE).read_bytes() == expected_manifest, "canonical manifest bytes")
        _assert((root / CONTRACT_FINGERPRINT_FILE).read_bytes() == expected_fingerprint, "fingerprint bytes")

        partial_manifest = Path(temp) / "partial_manifest"
        partial_manifest.mkdir()
        (partial_manifest / CONTRACT_MANIFEST_FILE).write_bytes(expected_manifest)
        _expect_raises(
            lambda: ensure_contract_metadata_pair(partial_manifest, manifest),
            "partial assignment contract metadata",
        )
        partial_fingerprint = Path(temp) / "partial_fingerprint"
        partial_fingerprint.mkdir()
        (partial_fingerprint / CONTRACT_FINGERPRINT_FILE).write_bytes(expected_fingerprint)
        _expect_raises(
            lambda: ensure_contract_metadata_pair(partial_fingerprint, manifest),
            "partial assignment contract metadata",
        )
        _expect_raises(
            lambda: ensure_contract_metadata_pair(root, _manifest("legacy")),
            "differs from current runtime contract",
        )


def test_native_save_artifacts_digests_inventory_and_marker_order() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        directory = root / "models"
        events: list[str] = []
        manifest = _manifest()
        coordinator = AssignmentCheckpointSaveCoordinator(root, event_recorder=events.append)
        result = _save(coordinator, manifest, directory, kind="regular", generation=0)
        expected_files = {
            "actor_agent_robot_0.pt",
            "actor_agent_robot_1.pt",
            "actor_agent_robot_2.pt",
            "critic_agent.pt",
            "value_normalizer.pt",
            CONTRACT_MANIFEST_FILE,
            CONTRACT_FINGERPRINT_FILE,
            TRAINING_STATE_MANIFEST_FILE,
        }
        _assert(expected_files <= {path.name for path in directory.iterdir()}, "native files")
        _assert(not list(directory.glob("actor_agent_[0-9].pt")), "no numeric actor fallback")
        _assert(not list(directory.glob("*_full.pt")), "no full model")
        _assert(events.count("critic_saved") == 1, "critic saved exactly once")
        _assert(events.count("value_normalizer_saved") == 1, "ValueNorm saved exactly once")
        _assert(events[-1] == "training_state_manifest_committed", "completion marker committed last")
        state = result.training_state_manifest
        _assert(state.checkpoint_kind == "regular" and state.checkpoint_generation == 0, "kind/generation")
        _assert(state.continuation_classification != "exact_resume", "not exact resume")
        _assert(all(not value for value in (
            state.actor_optimizer_available,
            state.critic_optimizer_available,
            state.training_counters_available,
            state.rng_state_available,
            state.environment_resolver_state_available,
            state.rollout_buffer_state_available,
        )), "unavailable continuation state")
        for artifact in (*state.actor_artifacts, state.critic_artifact, state.value_normalizer_artifact):
            assert artifact is not None
            path = directory / artifact.relative_file_name
            _assert(artifact.file_size == path.stat().st_size, "file size")
            _assert(
                artifact.file_sha256 == hashlib.sha256(path.read_bytes()).hexdigest(),
                "file digest",
            )
            _assert(not Path(artifact.relative_file_name).is_absolute(), "relative artifact name")
            _assert(tuple(entry.key for entry in artifact.tensor_inventory) == (
                "base.bias",
                "base.weight",
                "counter",
            ), "sorted tensor inventory")
        _assert(not list(directory.glob(".*.assignment-tmp-*")), "temporary files cleaned")


def test_file_digest_changes_with_artifact_content() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        directory = root / "models"
        manifest = _manifest()
        coordinator = AssignmentCheckpointSaveCoordinator(root)
        first = _save(coordinator, manifest, directory, kind="regular", generation=0)
        first_digest = first.training_state_manifest.actor_artifacts[0].file_sha256
        actors, critic, normalizer = _artifacts(manifest)
        actors = ((actors[0][0], _state_dict(100)), *actors[1:])
        second = coordinator.save_checkpoint(
            checkpoint_directory=directory,
            checkpoint_kind="final",
            checkpoint_generation=1,
            manifest=manifest,
            actor_state_dicts=actors,
            critic_state_dict=critic,
            value_normalizer_state_dict=normalizer,
        )
        _assert(second.training_state_manifest.actor_artifacts[0].file_sha256 != first_digest, "digest changed")


def test_save_kind_and_child_metadata_coverage() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest()
        coordinator = AssignmentCheckpointSaveCoordinator(root)
        cases = (
            (root / "models", "regular", 0, None),
            (root / "best_model", "best", 1, None),
            (root / "models" / "checkpoints" / "episode_7", "episode_snapshot", 2, 7),
            (root / "models", "final", 3, None),
        )
        for directory, kind, generation, index in cases:
            result = _save(
                coordinator,
                manifest,
                directory,
                kind=kind,
                generation=generation,
                index=index,
            )
            state = _read_training_state(directory)
            _assert(state.checkpoint_kind == kind, f"{kind} marker")
            _assert(state.checkpoint_generation == generation, f"{kind} generation")
            _assert(state.episode_or_update_index == index, f"{kind} index")
            _assert(
                (directory / CONTRACT_MANIFEST_FILE).read_bytes()
                == (root / CONTRACT_MANIFEST_FILE).read_bytes(),
                f"{kind} child manifest",
            )
            _assert(result.checkpoint_kind == kind, f"{kind} result")
        _assert(infer_assignment_checkpoint_kind(root, root / "models") == ("regular", None), "regular infer")
        _assert(infer_assignment_checkpoint_kind(root, root / "best_model") == ("best", None), "best infer")
        _assert(
            infer_assignment_checkpoint_kind(root, root / "models/checkpoints/episode_7")
            == ("episode_snapshot", 7),
            "episode infer",
        )


def test_child_partial_and_disagreement_fail_before_replacement() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest()
        ensure_contract_metadata_pair(root, manifest)
        child = root / "models"
        child.mkdir(parents=True)
        (child / CONTRACT_MANIFEST_FILE).write_bytes(canonical_manifest_bytes(manifest) + b"\n")
        _expect_raises(
            lambda: _save(
                AssignmentCheckpointSaveCoordinator(root),
                manifest,
                child,
                kind="regular",
                generation=0,
            ),
            "partial assignment contract metadata",
        )

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest()
        coordinator = AssignmentCheckpointSaveCoordinator(root)
        child = root / "models"
        _save(coordinator, manifest, child, kind="regular", generation=0)
        legacy = _manifest("legacy")
        (child / CONTRACT_MANIFEST_FILE).write_bytes(canonical_manifest_bytes(legacy) + b"\n")
        (child / CONTRACT_FINGERPRINT_FILE).write_bytes(
            compute_manifest_sha256(legacy).encode("ascii") + b"\n"
        )
        _expect_raises(
            lambda: _save(coordinator, manifest, child, kind="regular", generation=1),
            "disagrees with run-root contract",
        )


def test_value_norm_enabled_and_disabled() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest(value_norm=False)
        result = _save(
            AssignmentCheckpointSaveCoordinator(root),
            manifest,
            root / "models",
            kind="regular",
            generation=0,
            value_norm=False,
        )
        _assert(result.training_state_manifest.value_normalizer_artifact is None, "ValueNorm absent")
        _assert(not (root / "models/value_normalizer.pt").exists(), "ValueNorm file absent")
        actors, critic, normalizer = _artifacts(manifest, value_norm=True)
        _expect_raises(
            lambda: AssignmentCheckpointSaveCoordinator(root).save_checkpoint(
                checkpoint_directory=root / "best_model",
                checkpoint_kind="best",
                checkpoint_generation=1,
                manifest=manifest,
                actor_state_dicts=actors,
                critic_state_dict=critic,
                value_normalizer_state_dict=normalizer,
            ),
            "ValueNorm runtime state presence",
        )


def test_unsupported_state_entries_and_conflicting_artifacts() -> None:
    _expect_raises(
        lambda: build_tensor_inventory_from_state_dict(
            {"tensor": torch.ones(1), "metadata": "unsupported"},
            artifact_name="actor",
        ),
        "unsupported non-tensor",
    )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        directory = root / "models"
        directory.mkdir(parents=True)
        (directory / "actor_agent_0.pt").write_bytes(b"legacy")
        _expect_raises(
            lambda: _save(
                AssignmentCheckpointSaveCoordinator(root),
                _manifest(),
                directory,
                kind="regular",
                generation=0,
            ),
            "numeric-fallback",
        )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        directory = root / "models"
        directory.mkdir(parents=True)
        (directory / "critic_agent_full.pt").write_bytes(b"full")
        _expect_raises(
            lambda: _save(
                AssignmentCheckpointSaveCoordinator(root),
                _manifest(),
                directory,
                kind="regular",
                generation=0,
            ),
            "full-model artifacts",
        )


def test_failure_injection_removes_completion_marker() -> None:
    points = (
        FAIL_AFTER_MARKER_INVALIDATION,
        FAIL_AFTER_FIRST_ACTOR,
        FAIL_AFTER_ALL_ACTORS,
        FAIL_AFTER_CRITIC,
        FAIL_AFTER_VALUE_NORMALIZER,
        FAIL_AFTER_CHILD_CONTRACT,
    )
    for point in points:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            directory = root / "models"
            manifest = _manifest()
            _save(
                AssignmentCheckpointSaveCoordinator(root),
                manifest,
                directory,
                kind="regular",
                generation=0,
            )
            _assert((directory / TRAINING_STATE_MANIFEST_FILE).exists(), "old marker")

            def inject(current: str, expected: str = point) -> None:
                if current == expected:
                    raise RuntimeError(f"injected {current}")

            coordinator = AssignmentCheckpointSaveCoordinator(root, failure_injector=inject)
            _expect_raises(
                lambda: _save(
                    coordinator,
                    manifest,
                    directory,
                    kind="final",
                    generation=1,
                ),
                f"injected {point}",
            )
            _assert(not (directory / TRAINING_STATE_MANIFEST_FILE).exists(), f"no marker after {point}")
            _assert(not list(directory.glob(".*.assignment-tmp-*")), f"no temp after {point}")


class _SpyCoordinator:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = fail

    def save_checkpoint(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise AssignmentCheckpointSaveError("injected runner save failure")
        return SimpleNamespace(checkpoint_kind=kwargs["checkpoint_kind"])


class _StateProvider:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def state_dict(self):
        return _state_dict(self.seed)


def _routing_runner(root: Path, manifest: AssignmentCheckpointContractManifest) -> AssignmentOnPolicyHARunner:
    runner = AssignmentOnPolicyHARunner.__new__(AssignmentOnPolicyHARunner)
    runner.assignment_rl = True
    runner.save_entire_model = False
    runner.share_param = False
    runner.args = {"algo": "happo"}
    runner.run_dir = root
    runner._assignment_checkpoint_generation = 0
    runner._assignment_checkpoint_coordinator = _SpyCoordinator()
    runner.env = SimpleNamespace(
        assignment_env=SimpleNamespace(
            assignment_lifecycle_profile_config={"profile_name": "lifecycle_contract_c"}
        )
    )
    runner.actor = [
        SimpleNamespace(actor=_StateProvider(1)),
        SimpleNamespace(actor=_StateProvider(2)),
        SimpleNamespace(actor=_StateProvider(3)),
    ]
    runner.critic = SimpleNamespace(critic=_StateProvider(20))
    runner.value_normalizer = _StateProvider(30)
    runner._test_runtime_state = _runtime_state()
    runner._test_manifest = manifest
    return runner


def test_runner_save_hook_routing_and_generation() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        manifest = _manifest()
        runner = _routing_runner(root, manifest)
        original_capture = training_module.capture_assignment_checkpoint_runtime_state
        original_build = training_module.build_assignment_checkpoint_contract_manifest
        training_module.capture_assignment_checkpoint_runtime_state = lambda current: current._test_runtime_state
        training_module.build_assignment_checkpoint_contract_manifest = lambda runtime: manifest
        try:
            runner.save(root / "models")
            runner.save(root / "best_model")
            runner.save(root / "models/checkpoints/episode_9")
            runner.save(root / "models", checkpoint_kind="final")
            calls = runner._assignment_checkpoint_coordinator.calls
            _assert(
                [call["checkpoint_kind"] for call in calls]
                == ["regular", "best", "episode_snapshot", "final"],
                "four runner save kinds",
            )
            _assert(
                [call["checkpoint_generation"] for call in calls] == [0, 1, 2, 3],
                "monotonic successful generations",
            )
            _assert(calls[2]["episode_or_update_index"] == 9, "episode index routed")
            _assert(runner._assignment_checkpoint_generation == 4, "runner generation advanced")

            runner._assignment_checkpoint_coordinator = _SpyCoordinator(fail=True)
            _expect_raises(
                lambda: runner.save(root / "models", checkpoint_kind="final"),
                "runner save failure",
            )
            _assert(runner._assignment_checkpoint_generation == 4, "failed save did not increment")
        finally:
            training_module.capture_assignment_checkpoint_runtime_state = original_capture
            training_module.build_assignment_checkpoint_contract_manifest = original_build


def test_legacy_state_dict_and_full_model_boundary() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "run"
        legacy = _manifest("legacy")
        result = _save(
            AssignmentCheckpointSaveCoordinator(root),
            legacy,
            root / "models",
            kind="regular",
            generation=0,
        )
        _assert(result.training_state_manifest.contract_fingerprint == compute_manifest_sha256(legacy), "legacy native")

        runner = AssignmentOnPolicyHARunner.__new__(AssignmentOnPolicyHARunner)
        runner.assignment_rl = True
        runner.save_entire_model = True
        runner.share_param = False
        runner.args = {"algo": "happo"}
        runner.env = SimpleNamespace(
            assignment_env=SimpleNamespace(
                assignment_lifecycle_profile_config={"profile_name": "legacy"}
            )
        )
        calls: list[Path] = []
        original_save = OnPolicyHARunner.save
        OnPolicyHARunner.save = lambda self, directory: calls.append(Path(directory))
        try:
            runner.save(root / "legacy_full")
        finally:
            OnPolicyHARunner.save = original_save
        _assert(calls == [root / "legacy_full"], "legacy full-model path preserved")
        _assert(not (root / "legacy_full" / CONTRACT_MANIFEST_FILE).exists(), "no native metadata claim")


def test_lifecycle_full_model_and_non_training_profiles_rejected() -> None:
    runner = AssignmentOnPolicyHARunner.__new__(AssignmentOnPolicyHARunner)
    runner.assignment_rl = True
    runner.save_entire_model = True
    runner.args = {"algo": "happo"}
    runner.share_param = False
    runner.env = SimpleNamespace(
        assignment_env=SimpleNamespace(
            assignment_lifecycle_profile_config={"profile_name": "lifecycle_contract_c"}
        )
    )
    _expect_raises(lambda: runner.save(Path("models")), "save_entire_model=False")
    for profile in ("lifecycle_ablation", "diagnostics_hidden_state"):
        runner.env.assignment_env.assignment_lifecycle_profile_config["profile_name"] = profile
        _expect_raises(lambda: runner.save(Path("models")), "not a native assignment training")


def test_no_loader_or_runtime_execution_integration() -> None:
    save_source = (SCAN_TASK_SOURCE / "assignment_checkpoint_save.py").read_text(encoding="utf-8")
    for forbidden in ("torch.load(", ".load_state_dict(", "backward(", "optimizer.step("):
        _assert(forbidden not in save_source, f"save module must not contain {forbidden}")
    loader_files = (
        REPO_ROOT / "scripts/reinforcement_learning/harl/play.py",
        REPO_ROOT / "scripts/reinforcement_learning/harl/play_assignment.py",
        REPO_ROOT / "scripts/environments/evaluate_assignment_rl_playback_diagnostics.py",
        REPO_ROOT / "scripts/environments/evaluate_assignment_methods.py",
    )
    for path in loader_files:
        _assert("assignment_checkpoint_save" not in path.read_text(encoding="utf-8"), f"no loader import: {path}")
    train_source = (REPO_ROOT / "scripts/reinforcement_learning/harl/train.py").read_text(encoding="utf-8")
    _assert('checkpoint_kind="final"' in train_source, "final save explicitly classified")


TESTS = (
    test_runtime_manifest_lifecycle_and_legacy,
    test_runtime_manifest_consistency_rejections,
    test_capture_effective_constructed_runtime_values,
    test_run_root_metadata_pair,
    test_native_save_artifacts_digests_inventory_and_marker_order,
    test_file_digest_changes_with_artifact_content,
    test_save_kind_and_child_metadata_coverage,
    test_child_partial_and_disagreement_fail_before_replacement,
    test_value_norm_enabled_and_disabled,
    test_unsupported_state_entries_and_conflicting_artifacts,
    test_failure_injection_removes_completion_marker,
    test_runner_save_hook_routing_and_generation,
    test_legacy_state_dict_and_full_model_boundary,
    test_lifecycle_full_model_and_non_training_profiles_rejected,
    test_no_loader_or_runtime_execution_integration,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    failures: list[str] = []
    for test in TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failures.append(test.__name__)
            print(f"FAIL {test.__name__}: {exc!r}")
    passed = len(TESTS) - len(failures)
    if failures:
        print(f"FAIL {passed}/{len(TESTS)} tests; failures={failures}")
        return 1
    print(f"PASS {passed}/{len(TESTS)} tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
