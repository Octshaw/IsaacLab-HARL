"""Phase 9G-8F-5 native checkpoint save/load/continuation smoke tests.

The suite uses real installed HARL modules, the project save coordinator, the
shared project loader, synthetic CPU data, and temporary directories only.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import gymnasium
import numpy as np
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

import assignment_checkpoint_load as load_module  # noqa: E402
from assignment_checkpoint_contract import (  # noqa: E402
    NAMED_LIFECYCLE_ABLATION,
    AssignmentCheckpointContractManifest,
    AssignmentTrainingStateManifest,
    CompatibilityPurpose,
    compute_manifest_sha256,
    verify_manifest_sha256,
)
from assignment_checkpoint_load import (  # noqa: E402
    AssignmentCheckpointError,
    AssignmentCheckpointLoadResult,
    load_assignment_checkpoint,
)
from assignment_checkpoint_save import (  # noqa: E402
    CONTRACT_FINGERPRINT_FILE,
    CONTRACT_MANIFEST_FILE,
    TRAINING_STATE_MANIFEST_FILE,
    AssignmentCheckpointSaveCoordinator,
    AssignmentCheckpointSaveResult,
    build_tensor_inventory_from_state_dict,
    compute_file_sha256,
)
from assignment_value_normalizer_checkpoint import (  # noqa: E402
    export_value_normalizer_checkpoint_state,
)
from harl.algorithms.actors.happo import HAPPO  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402
from test_assignment_actor_critic_buffer_forward_backward_readiness import (  # noqa: E402
    ACTION_DIM,
    DEVICE,
    LEGACY_ACTOR_DIM,
    LEGACY_SHARED_DIM,
    LIFECYCLE_ACTOR_DIM,
    LIFECYCLE_SHARED_DIM,
    NUM_AGENTS,
    _actions_for_ids,
    _assert_actor_generator_alignment,
    _assert_critic_generator_alignment,
    _available_actions_for_id,
    _combined_model_algo_args,
    _construct_components,
    _gradient_evidence,
    _isolated_seed,
    _load_effective_config,
    _observation,
    _parameter_snapshot,
    _parameters_changed,
    _parameters_equal,
    _populate_actor_buffer,
    _populate_critic_buffer,
    _space,
)
from test_assignment_checkpoint_contract_core import _changed  # noqa: E402
from test_assignment_checkpoint_save_metadata_integration import _manifest  # noqa: E402


ACTOR_NAMES = tuple(f"robot_{index}" for index in range(NUM_AGENTS))
PROBE_BATCH = 4


@dataclass(frozen=True)
class ProbeResult:
    actor_log_probs: tuple[torch.Tensor, ...]
    actor_entropies: tuple[torch.Tensor, ...]
    actor_probabilities: tuple[torch.Tensor, ...]
    actor_rnn_states: tuple[torch.Tensor, ...]
    critic_values: torch.Tensor
    critic_rnn_states: torch.Tensor
    value_normalized: torch.Tensor
    value_denormalized: torch.Tensor


@dataclass(frozen=True)
class SmokeResult:
    source_actor_parameter_count: int
    source_critic_parameter_count: int
    target_actor_parameter_count: int
    target_critic_parameter_count: int
    checkpoint_artifacts: tuple[str, ...]
    checkpoint_total_size: int
    checkpoint_generation_first: int
    checkpoint_generation_second: int
    contract_fingerprint: str
    state_keys_compared: int
    state_keys_exact: int
    actor_output_max_abs_difference: float
    critic_output_max_abs_difference: float
    value_norm_output_max_abs_difference: float
    post_load_actor_loss: float
    post_load_critic_loss: float
    post_load_actor_gradient_norm: float
    post_load_critic_gradient_norm: float
    lifecycle_source_prepared: bool
    native_save_complete: bool
    metadata_verified: bool
    target_differed_before_load: bool
    continuation_loaded: bool
    exact_state_equal: bool
    actor_outputs_equal: bool
    critic_outputs_equal: bool
    value_norm_equal: bool
    target_optimizers_fresh: bool
    post_load_actor_updated: bool
    post_load_critic_updated: bool
    source_isolated: bool
    evaluation_actor_only: bool
    named_ablation_loaded: bool
    legacy_native_equal: bool
    corruption_rejected_without_mutation: bool
    missing_marker_rejected_before_deserialization: bool
    semantic_mismatch_rejected_before_deserialization: bool
    training_only_purpose_distinction: bool
    wrong_structure_rejected_without_mutation: bool
    resave_complete: bool
    generation_advanced: bool


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], expected: str) -> Exception:
    try:
        func()
    except Exception as exc:  # noqa: BLE001 - negative tests validate loader boundaries.
        if expected not in str(exc):
            raise AssertionError(f"expected {expected!r} in {str(exc)!r}") from exc
        return exc
    raise AssertionError(f"expected an exception containing {expected!r}")


def _actor_modules(components: Any) -> tuple[tuple[str, torch.nn.Module], ...]:
    return tuple(
        (name, actor.actor)
        for name, actor in zip(ACTOR_NAMES, components.actors, strict=True)
    )


def _checkpoint_state(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    if isinstance(module, ValueNorm):
        return dict(export_value_normalizer_checkpoint_state(module))
    return {key: value.detach().cpu().clone() for key, value in module.state_dict().items()}


def _module_states(modules: Sequence[torch.nn.Module]) -> tuple[dict[str, torch.Tensor], ...]:
    return tuple(_checkpoint_state(module) for module in modules)


def _assert_states_equal(
    expected: Sequence[Mapping[str, torch.Tensor]],
    modules: Sequence[torch.nn.Module],
) -> tuple[int, int]:
    compared = 0
    exact = 0
    _assert(len(expected) == len(modules), "state module count")
    for expected_state, module in zip(expected, modules, strict=True):
        actual_state = _checkpoint_state(module)
        _assert(tuple(expected_state) == tuple(actual_state), "state_dict key order/equality")
        for key, expected_value in expected_state.items():
            compared += 1
            actual_value = actual_state[key].detach().cpu()
            _assert(actual_value.shape == expected_value.shape, f"state shape {key}")
            _assert(actual_value.dtype == expected_value.dtype, f"state dtype {key}")
            if torch.equal(actual_value, expected_value):
                exact += 1
            else:
                raise AssertionError(f"state value mismatch: {key}")
    return compared, exact


def _assert_states_unchanged(
    before: Sequence[Mapping[str, torch.Tensor]],
    modules: Sequence[torch.nn.Module],
    message: str,
) -> None:
    try:
        compared, exact = _assert_states_equal(before, modules)
    except AssertionError as exc:
        raise AssertionError(f"{message}: {exc}") from exc
    _assert(compared == exact, message)


def _probe(components: Any) -> ProbeResult:
    actor_obs = torch.stack(
        [_observation(index + 30, components.actor_dim) for index in range(PROBE_BATCH)]
    )
    shared_obs = torch.stack(
        [_observation(index + 30, components.shared_dim) for index in range(PROBE_BATCH)]
    )
    available_actions = torch.stack(
        [_available_actions_for_id(index + 30) for index in range(PROBE_BATCH)]
    )
    actions = _actions_for_ids(torch.arange(30, 30 + PROBE_BATCH))
    rnn_states = torch.zeros(PROBE_BATCH, 1, 256)
    masks = torch.ones(PROBE_BATCH, 1)
    active_masks = torch.ones(PROBE_BATCH, 1)

    actor_log_probs = []
    actor_entropies = []
    actor_probabilities = []
    actor_rnn_outputs = []
    with torch.no_grad():
        for actor in components.actors:
            log_probs, entropy, distribution = actor.evaluate_actions(
                actor_obs,
                rnn_states,
                actions,
                masks,
                available_actions,
                active_masks,
            )
            _, returned_rnn = actor.act(
                actor_obs,
                rnn_states,
                masks,
                available_actions,
                deterministic=True,
            )
            actor_log_probs.append(log_probs.detach().cpu().clone())
            actor_entropies.append(entropy.detach().cpu().clone())
            actor_probabilities.append(distribution.probs.detach().cpu().clone())
            actor_rnn_outputs.append(returned_rnn.detach().cpu().clone())
        critic_values, critic_rnn = components.critic.get_values(
            shared_obs,
            rnn_states,
            masks,
        )
        value_input = torch.tensor([[-1.25], [0.0], [0.75], [2.0]], dtype=torch.float32)
        value_normalized = components.value_normalizer.normalize(value_input)
        value_denormalized = components.value_normalizer.denormalize(value_input)

    tensors = (
        *actor_log_probs,
        *actor_entropies,
        *actor_probabilities,
        *actor_rnn_outputs,
        critic_values,
        critic_rnn,
        value_normalized,
        value_denormalized,
    )
    _assert(all(torch.isfinite(tensor).all() for tensor in tensors), "probe outputs are finite")
    return ProbeResult(
        actor_log_probs=tuple(actor_log_probs),
        actor_entropies=tuple(actor_entropies),
        actor_probabilities=tuple(actor_probabilities),
        actor_rnn_states=tuple(actor_rnn_outputs),
        critic_values=critic_values.detach().cpu().clone(),
        critic_rnn_states=critic_rnn.detach().cpu().clone(),
        value_normalized=value_normalized.detach().cpu().clone(),
        value_denormalized=value_denormalized.detach().cpu().clone(),
    )


def _max_difference(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.max(torch.abs(left - right)).item())


def _assert_probe_equal(source: ProbeResult, target: ProbeResult) -> tuple[float, float, float]:
    actor_max = 0.0
    for source_group, target_group in (
        (source.actor_log_probs, target.actor_log_probs),
        (source.actor_entropies, target.actor_entropies),
        (source.actor_probabilities, target.actor_probabilities),
        (source.actor_rnn_states, target.actor_rnn_states),
    ):
        for source_tensor, target_tensor in zip(source_group, target_group, strict=True):
            actor_max = max(actor_max, _max_difference(source_tensor, target_tensor))
            _assert(torch.equal(source_tensor, target_tensor), "actor deterministic output equality")
    critic_max = max(
        _max_difference(source.critic_values, target.critic_values),
        _max_difference(source.critic_rnn_states, target.critic_rnn_states),
    )
    _assert(torch.equal(source.critic_values, target.critic_values), "critic value equality")
    _assert(torch.equal(source.critic_rnn_states, target.critic_rnn_states), "critic RNN placeholder equality")
    value_max = max(
        _max_difference(source.value_normalized, target.value_normalized),
        _max_difference(source.value_denormalized, target.value_denormalized),
    )
    _assert(torch.equal(source.value_normalized, target.value_normalized), "ValueNorm normalize equality")
    _assert(torch.equal(source.value_denormalized, target.value_denormalized), "ValueNorm denormalize equality")
    return actor_max, critic_max, value_max


def _prepare_source(components: Any) -> tuple[float, float]:
    actor_advantages = _populate_actor_buffer(components.actors[0], components.actor_buffers[0])
    actor_sample = _assert_actor_generator_alignment(components.actor_buffers[0], actor_advantages)
    actor_loss, _, actor_grad_norm, _ = components.actors[0].update(actor_sample)
    _assert(torch.isfinite(actor_loss) and torch.isfinite(actor_grad_norm), "source actor update finite")

    _populate_critic_buffer(components)
    critic_sample = _assert_critic_generator_alignment(components.critic_buffer)
    critic_loss, critic_grad_norm = components.critic.update(
        critic_sample,
        value_normalizer=components.value_normalizer,
    )
    _assert(torch.isfinite(critic_loss) and torch.isfinite(critic_grad_norm), "source critic update finite")
    _assert(components.actors[0].actor_optimizer.state, "source actor Adam state exists")
    _assert(components.critic.critic_optimizer.state, "source critic Adam state exists")
    return float(actor_loss.detach().item()), float(critic_loss.detach().item())


def _save(
    coordinator: AssignmentCheckpointSaveCoordinator,
    directory: Path,
    manifest: AssignmentCheckpointContractManifest,
    components: Any,
    *,
    generation: int,
    events: list[str],
) -> AssignmentCheckpointSaveResult:
    events.clear()
    result = coordinator.save_checkpoint(
        checkpoint_directory=directory,
        checkpoint_kind="final",
        checkpoint_generation=generation,
        manifest=manifest,
        actor_state_dicts=tuple(
            (name, actor.actor.state_dict())
            for name, actor in zip(ACTOR_NAMES, components.actors, strict=True)
        ),
        critic_state_dict=components.critic.critic.state_dict(),
        value_normalizer_state_dict=export_value_normalizer_checkpoint_state(
            components.value_normalizer
        ),
    )
    _assert(events and events[-1] == "training_state_manifest_committed", "completion marker committed last")
    return result


def _load(
    directory: Path,
    manifest: AssignmentCheckpointContractManifest,
    components: Any,
    *,
    purpose: CompatibilityPurpose,
    acknowledgement: bool = False,
    ablation_name: str | None = None,
) -> AssignmentCheckpointLoadResult:
    return load_assignment_checkpoint(
        checkpoint_directory=directory,
        purpose=purpose,
        current_manifest=manifest,
        actor_modules=_actor_modules(components),
        critic_module=components.critic.critic,
        value_normalizer_module=components.value_normalizer,
        explicit_ablation_name=ablation_name,
        continuation_reset_acknowledged=acknowledgement,
    )


def _verify_native_checkpoint(
    run_root: Path,
    directory: Path,
    manifest: AssignmentCheckpointContractManifest,
    components: Any,
    *,
    generation: int,
) -> tuple[tuple[str, ...], int, AssignmentTrainingStateManifest]:
    expected_files = {
        CONTRACT_MANIFEST_FILE,
        CONTRACT_FINGERPRINT_FILE,
        TRAINING_STATE_MANIFEST_FILE,
        "actor_agent_robot_0.pt",
        "actor_agent_robot_1.pt",
        "actor_agent_robot_2.pt",
        "critic_agent.pt",
        "value_normalizer.pt",
    }
    actual_files = {path.name for path in directory.iterdir() if path.is_file()}
    _assert(actual_files == expected_files, "native checkpoint artifact list")
    _assert((run_root / CONTRACT_MANIFEST_FILE).is_file(), "run-root contract manifest")
    _assert((run_root / CONTRACT_FINGERPRINT_FILE).is_file(), "run-root contract fingerprint")

    manifest_mapping = json.loads((directory / CONTRACT_MANIFEST_FILE).read_text(encoding="utf-8"))
    parsed_manifest = AssignmentCheckpointContractManifest.from_mapping(manifest_mapping)
    stored_fingerprint = (directory / CONTRACT_FINGERPRINT_FILE).read_text(encoding="utf-8").strip()
    _assert(verify_manifest_sha256(parsed_manifest, stored_fingerprint), "checkpoint fingerprint verifies")
    _assert(stored_fingerprint == compute_manifest_sha256(manifest), "checkpoint fingerprint expected")
    _assert(
        (run_root / CONTRACT_FINGERPRINT_FILE).read_text(encoding="utf-8").strip() == stored_fingerprint,
        "run-root/child fingerprint agreement",
    )

    training_mapping = json.loads((directory / TRAINING_STATE_MANIFEST_FILE).read_text(encoding="utf-8"))
    training_state = AssignmentTrainingStateManifest.from_mapping(training_mapping)
    _assert(training_state.contract_fingerprint == stored_fingerprint, "training-state fingerprint binding")
    _assert(training_state.checkpoint_kind == "final", "checkpoint kind")
    _assert(training_state.checkpoint_generation == generation, "checkpoint generation")
    _assert(
        training_state.continuation_classification == "validated_weight_continuation_candidate",
        "continuation classification",
    )
    _assert(training_state.ordered_actor_identities == ACTOR_NAMES, "actor identities")
    _assert(not training_state.actor_optimizer_available, "actor optimizer state is absent")
    _assert(not training_state.critic_optimizer_available, "critic optimizer state is absent")
    _assert(not training_state.training_counters_available, "training counters are absent")
    _assert(not training_state.rng_state_available, "RNG state is absent")
    _assert(not training_state.environment_resolver_state_available, "environment/resolver state is absent")
    _assert(not training_state.rollout_buffer_state_available, "rollout buffer state is absent")

    state_by_role: dict[tuple[str, str | None], Mapping[str, torch.Tensor]] = {
        ("actor", name): actor.actor.state_dict()
        for name, actor in zip(ACTOR_NAMES, components.actors, strict=True)
    }
    state_by_role[("critic", None)] = components.critic.critic.state_dict()
    state_by_role[("value_normalizer", None)] = export_value_normalizer_checkpoint_state(
        components.value_normalizer
    )
    entries = (
        *training_state.actor_artifacts,
        training_state.critic_artifact,
        training_state.value_normalizer_artifact,
    )
    for entry in entries:
        _assert(entry is not None, "required artifact inventory")
        assert entry is not None
        artifact_path = directory / entry.relative_file_name
        size, digest = compute_file_sha256(artifact_path)
        _assert(size == entry.file_size, f"file size {entry.relative_file_name}")
        _assert(digest == entry.file_sha256, f"file digest {entry.relative_file_name}")
        expected_inventory = build_tensor_inventory_from_state_dict(
            state_by_role[(entry.artifact_role, entry.actor_identity)],
            artifact_name=entry.relative_file_name,
        )
        _assert(entry.tensor_inventory == expected_inventory, f"tensor inventory {entry.relative_file_name}")
    total_size = sum(path.stat().st_size for path in directory.iterdir() if path.is_file())
    return tuple(sorted(actual_files)), total_size, training_state


def _ablation_manifest(checkpoint_manifest: AssignmentCheckpointContractManifest) -> AssignmentCheckpointContractManifest:
    mapping = checkpoint_manifest.to_mapping()
    mapping["identity"]["profile_name"] = "lifecycle_ablation"
    mapping["identity"]["training_time_profile"] = "lifecycle_ablation"
    behavior = mapping["lifecycle_behavior_contract"]
    behavior["resolver_contract_version"] = "disabled"
    behavior["mask_contract_version"] = "lifecycle_ablation_physical_mask_v1"
    behavior["budget_release_contract_version"] = "disabled"
    return AssignmentCheckpointContractManifest.from_mapping(mapping)


def _construct_wrong_actor() -> HAPPO:
    config = _load_effective_config()
    return HAPPO(
        _combined_model_algo_args(config),
        _space(LIFECYCLE_ACTOR_DIM - 1),
        gymnasium.spaces.Discrete(ACTION_DIM),
        device=DEVICE,
    )


def _runtime_style_value_normalizer(device: torch.device) -> ValueNorm:
    """Construct the unregistered-Tensor ValueNorm form seen in runtime use."""

    original_dtype = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        value_normalizer = ValueNorm(1, device=device)
    finally:
        torch.set_default_dtype(original_dtype)
    _assert(not tuple(value_normalizer.state_dict()), "runtime-style ValueNorm is unregistered")
    return value_normalizer


def _assert_runtime_style_value_normalizer_round_trip(device: torch.device) -> None:
    with tempfile.TemporaryDirectory() as temp:
        manifest = _manifest("lifecycle_contract_c")
        with _isolated_seed(9700):
            source = _construct_components("lifecycle_contract_c")
        with _isolated_seed(9701):
            target = _construct_components("lifecycle_contract_c")
        source.value_normalizer = _runtime_style_value_normalizer(device)
        target.value_normalizer = _runtime_style_value_normalizer(device)
        source.value_normalizer.update(
            torch.tensor([[-2.0], [0.5], [3.0]], dtype=torch.float32, device=device)
        )
        source_state = export_value_normalizer_checkpoint_state(source.value_normalizer)
        _assert(tuple(source_state) == ("running_mean", "running_mean_sq", "debiasing_term"), "adapter key order")
        _assert(source_state, "adapter export is nonempty")

        run_root = Path(temp) / "runtime_style"
        events: list[str] = []
        _save(
            AssignmentCheckpointSaveCoordinator(run_root, event_recorder=events.append),
            run_root / "models",
            manifest,
            source,
            generation=0,
            events=events,
        )
        result = _load(
            run_root / "models",
            manifest,
            target,
            purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            acknowledgement=True,
        )
        _assert(result.value_normalizer_loaded, "runtime-style ValueNorm restored")
        target_state = export_value_normalizer_checkpoint_state(target.value_normalizer)
        for name, source_value in source_state.items():
            _assert(torch.equal(target_state[name], source_value), f"runtime-style field {name}")
        probe = torch.tensor([[-1.0], [0.0], [1.0]], dtype=torch.float32, device=device)
        _assert(
            torch.equal(
                source.value_normalizer.normalize(probe),
                target.value_normalizer.normalize(probe),
            ),
            "runtime-style normalize equivalence",
        )
        _assert(
            torch.equal(
                source.value_normalizer.denormalize(probe),
                target.value_normalizer.denormalize(probe),
            ),
            "runtime-style denormalize equivalence",
        )


def test_runtime_style_valuenorm_checkpoint_round_trip_cpu_and_cuda() -> None:
    _assert_runtime_style_value_normalizer_round_trip(torch.device("cpu"))
    if torch.cuda.is_available():
        _assert_runtime_style_value_normalizer_round_trip(torch.device("cuda"))


def _corruption_smokes(
    temp_root: Path,
    manifest: AssignmentCheckpointContractManifest,
    source: Any,
) -> tuple[bool, bool, bool, bool, bool]:
    def fresh_targets(seed: int) -> Any:
        with _isolated_seed(seed):
            return _construct_components("lifecycle_contract_c")

    def save_case(name: str) -> tuple[Path, Path]:
        run_root = temp_root / name
        directory = run_root / "models"
        AssignmentCheckpointSaveCoordinator(run_root).save_checkpoint(
            checkpoint_directory=directory,
            checkpoint_kind="final",
            checkpoint_generation=0,
            manifest=manifest,
            actor_state_dicts=tuple(
                (identity, actor.actor.state_dict())
                for identity, actor in zip(ACTOR_NAMES, source.actors, strict=True)
            ),
            critic_state_dict=source.critic.critic.state_dict(),
            value_normalizer_state_dict=export_value_normalizer_checkpoint_state(
                source.value_normalizer
            ),
        )
        return run_root, directory

    corrupt_ok = True
    for name, same_size in (("different_size", False), ("same_size", True)):
        _, directory = save_case(name)
        actor_path = directory / "actor_agent_robot_1.pt"
        payload = bytearray(actor_path.read_bytes())
        if same_size:
            payload[len(payload) // 2] ^= 0x01
        else:
            payload.extend(b"corrupt")
        actor_path.write_bytes(payload)
        targets = fresh_targets(9500 + int(same_size))
        before = _module_states([actor.actor for actor in targets.actors])
        _expect_raises(
            lambda: _load(
                directory,
                manifest,
                targets,
                purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                acknowledgement=True,
            ),
            "artifact",
        )
        _assert_states_unchanged(before, [actor.actor for actor in targets.actors], "corruption no mutation")
        corrupt_ok = corrupt_ok and True

    _, missing_directory = save_case("missing_marker")
    (missing_directory / TRAINING_STATE_MANIFEST_FILE).unlink()
    missing_targets = fresh_targets(9510)
    missing_before = _module_states([actor.actor for actor in missing_targets.actors])
    original_load = load_module.torch.load
    load_calls = 0

    def spy_load(*args, **kwargs):
        nonlocal load_calls
        load_calls += 1
        return original_load(*args, **kwargs)

    load_module.torch.load = spy_load
    try:
        _expect_raises(
            lambda: _load(
                missing_directory,
                manifest,
                missing_targets,
                purpose=CompatibilityPurpose.NORMAL_EVALUATION,
            ),
            "incomplete",
        )
    finally:
        load_module.torch.load = original_load
    _assert(load_calls == 0, "missing marker rejects before deserialization")
    _assert_states_unchanged(
        missing_before,
        [actor.actor for actor in missing_targets.actors],
        "missing marker no mutation",
    )

    _, mismatch_directory = save_case("semantic_mismatch")
    semantic_mismatch = _changed(
        manifest,
        "lifecycle_behavior_contract.mask_contract_version",
        "wrong_mask_contract",
    )
    mismatch_targets = fresh_targets(9520)
    mismatch_before = _module_states([actor.actor for actor in mismatch_targets.actors])
    load_calls = 0
    load_module.torch.load = spy_load
    try:
        _expect_raises(
            lambda: _load(
                mismatch_directory,
                semantic_mismatch,
                mismatch_targets,
                purpose=CompatibilityPurpose.NORMAL_EVALUATION,
            ),
            "evaluation_semantic_mismatch",
        )
    finally:
        load_module.torch.load = original_load
    _assert(load_calls == 0, "semantic mismatch rejects before deserialization")
    _assert_states_unchanged(
        mismatch_before,
        [actor.actor for actor in mismatch_targets.actors],
        "semantic mismatch no mutation",
    )

    training_difference = _changed(manifest, "training_contract.actor_learning_rate", "0.001")
    evaluation_targets = fresh_targets(9530)
    evaluation_result = _load(
        mismatch_directory,
        training_difference,
        evaluation_targets,
        purpose=CompatibilityPurpose.NORMAL_EVALUATION,
    )
    _assert(evaluation_result.compatibility_decision.allowed, "training-only difference allows evaluation")
    continuation_targets = fresh_targets(9531)
    continuation_before = _module_states([actor.actor for actor in continuation_targets.actors])
    load_calls = 0
    load_module.torch.load = spy_load
    try:
        _expect_raises(
            lambda: _load(
                mismatch_directory,
                training_difference,
                continuation_targets,
                purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                acknowledgement=True,
            ),
            "continuation_contract_mismatch",
        )
    finally:
        load_module.torch.load = original_load
    _assert(load_calls == 0, "training-only continuation mismatch rejects before deserialization")
    _assert_states_unchanged(
        continuation_before,
        [actor.actor for actor in continuation_targets.actors],
        "training-only continuation no mutation",
    )

    _, wrong_directory = save_case("wrong_structure")
    wrong_targets = fresh_targets(9540)
    wrong_actor = _construct_wrong_actor()
    wrong_targets.actors[0] = wrong_actor
    wrong_modules = [actor.actor for actor in wrong_targets.actors]
    wrong_before = _module_states(wrong_modules)
    _expect_raises(
        lambda: _load(
            wrong_directory,
            manifest,
            wrong_targets,
            purpose=CompatibilityPurpose.NORMAL_EVALUATION,
        ),
        "live inventory mismatch",
    )
    _assert_states_unchanged(wrong_before, wrong_modules, "wrong target structure no mutation")
    return corrupt_ok, True, True, True, True


def _run_smoke() -> SmokeResult:
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        with _isolated_seed(9001):
            source = _construct_components("lifecycle_contract_c")
        _prepare_source(source)
        _assert(source.actors[0].actor_optimizer.state, "source actor optimizer populated")
        _assert(source.critic.critic_optimizer.state, "source critic optimizer populated")
        source_modules = (
            *[actor.actor for actor in source.actors],
            source.critic.critic,
            source.value_normalizer,
        )
        source_states = _module_states(source_modules)
        source_reference = _probe(source)

        manifest = _manifest("lifecycle_contract_c")
        run_root = temp_root / "lifecycle_run"
        directory = run_root / "models"
        events: list[str] = []
        coordinator = AssignmentCheckpointSaveCoordinator(run_root, event_recorder=events.append)
        first_save = _save(
            coordinator,
            directory,
            manifest,
            source,
            generation=0,
            events=events,
        )
        artifacts, checkpoint_size, first_marker = _verify_native_checkpoint(
            run_root,
            directory,
            manifest,
            source,
            generation=0,
        )
        first_digests = {
            (entry.artifact_role, entry.actor_identity): entry.file_sha256
            for entry in (
                *first_marker.actor_artifacts,
                first_marker.critic_artifact,
                first_marker.value_normalizer_artifact,
            )
            if entry is not None
        }

        with _isolated_seed(9002):
            target = _construct_components("lifecycle_contract_c")
        target_modules = (
            *[actor.actor for actor in target.actors],
            target.critic.critic,
            target.value_normalizer,
        )
        target_preload_states = _module_states(target_modules)
        target_preload_probe = _probe(target)
        target_differed = (
            any(
                not torch.equal(source_states[index][key], target_preload_states[index][key])
                for index in range(len(source_states))
                for key in source_states[index]
            )
            and any(
                not torch.equal(left, right)
                for left, right in zip(
                    source_reference.actor_probabilities,
                    target_preload_probe.actor_probabilities,
                    strict=True,
                )
            )
            and not torch.equal(source_reference.critic_values, target_preload_probe.critic_values)
        )
        _assert(target_differed, "fresh target differs before load")
        _assert(all(not actor.actor_optimizer.state for actor in target.actors), "fresh actor optimizers empty")
        _assert(not target.critic.critic_optimizer.state, "fresh critic optimizer empty")

        continuation = _load(
            directory,
            manifest,
            target,
            purpose=CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            acknowledgement=True,
        )
        _assert(continuation.loaded_actor_identities == ACTOR_NAMES, "all actors continuation-loaded")
        _assert(continuation.critic_loaded, "critic continuation-loaded")
        _assert(continuation.value_normalizer_loaded, "ValueNorm continuation-loaded")
        _assert(continuation.continuation_acknowledgement is not None, "reset acknowledgement recorded")
        _assert(not continuation.legacy_fallback_used, "native continuation is not legacy fallback")
        _assert(continuation.named_ablation_used is None, "continuation is not ablation")
        _assert(continuation.checkpoint_kind == "final", "load result kind")
        _assert(continuation.checkpoint_generation == 0, "load result generation")
        _assert(
            continuation.contract_fingerprint == compute_manifest_sha256(manifest),
            "load result contract fingerprint",
        )

        compared, exact = _assert_states_equal(source_states, target_modules)
        target_reference = _probe(target)
        actor_diff, critic_diff, value_diff = _assert_probe_equal(source_reference, target_reference)
        _assert(all(not actor.actor_optimizer.state for actor in target.actors), "actor optimizer moments not loaded")
        _assert(not target.critic.critic_optimizer.state, "critic optimizer moments not loaded")
        for actor in target.actors:
            optimizer_ids = {
                id(parameter)
                for group in actor.actor_optimizer.param_groups
                for parameter in group["params"]
            }
            _assert(
                optimizer_ids == {id(parameter) for parameter in actor.actor.parameters()},
                "target actor optimizer bindings",
            )
        critic_optimizer_ids = {
            id(parameter)
            for group in target.critic.critic_optimizer.param_groups
            for parameter in group["params"]
        }
        _assert(
            critic_optimizer_ids == {id(parameter) for parameter in target.critic.critic.parameters()},
            "target critic optimizer bindings",
        )

        with _isolated_seed(9003):
            evaluation_target = _construct_components("lifecycle_contract_c")
        evaluation_critic_before = _module_states(
            [evaluation_target.critic.critic, evaluation_target.value_normalizer]
        )
        evaluation = _load(
            directory,
            manifest,
            evaluation_target,
            purpose=CompatibilityPurpose.NORMAL_EVALUATION,
        )
        _assert(evaluation.loaded_actor_identities == ACTOR_NAMES, "evaluation actors loaded")
        _assert(not evaluation.critic_loaded and not evaluation.value_normalizer_loaded, "evaluation actor-only")
        _assert_states_unchanged(
            evaluation_critic_before,
            [evaluation_target.critic.critic, evaluation_target.value_normalizer],
            "evaluation global modules untouched",
        )
        evaluation_probe = _probe(evaluation_target)
        for source_probs, evaluation_probs in zip(
            source_reference.actor_probabilities,
            evaluation_probe.actor_probabilities,
            strict=True,
        ):
            _assert(torch.equal(source_probs, evaluation_probs), "evaluation actor output equality")

        with _isolated_seed(9004):
            ablation_target = _construct_components("lifecycle_contract_c")
        ablation = _load(
            directory,
            _ablation_manifest(manifest),
            ablation_target,
            purpose=CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            ablation_name=NAMED_LIFECYCLE_ABLATION,
        )
        _assert(ablation.named_ablation_used == NAMED_LIFECYCLE_ABLATION, "named ablation result")
        _assert(not ablation.critic_loaded and not ablation.value_normalizer_loaded, "ablation actor-only")
        ablation_probe = _probe(ablation_target)
        for source_probs, ablation_probs in zip(
            source_reference.actor_probabilities,
            ablation_probe.actor_probabilities,
            strict=True,
        ):
            _assert(torch.equal(source_probs, ablation_probs), "ablation actor output equality")

        source_before_target_update = _module_states(source_modules)
        target_actor_1_before = _parameter_snapshot(target.actors[1].actor)
        target_actor_2_before = _parameter_snapshot(target.actors[2].actor)
        target_actor_0_before = _parameter_snapshot(target.actors[0].actor)
        actor_advantages = _populate_actor_buffer(target.actors[0], target.actor_buffers[0])
        actor_sample = _assert_actor_generator_alignment(target.actor_buffers[0], actor_advantages)
        actor_loss, _, actor_grad_norm, _ = target.actors[0].update(actor_sample)
        actor_gradient_count, _ = _gradient_evidence(target.actors[0].actor)
        _assert(actor_gradient_count > 0 and torch.isfinite(actor_grad_norm), "post-load actor gradients")
        _assert(_parameters_changed(target_actor_0_before, target.actors[0].actor), "post-load actor changed")
        _assert(_parameters_equal(target_actor_1_before, target.actors[1].actor), "target actor 1 isolated")
        _assert(_parameters_equal(target_actor_2_before, target.actors[2].actor), "target actor 2 isolated")
        _assert(target.actors[0].actor_optimizer.state, "post-load actor Adam state created")

        target_critic_before = _parameter_snapshot(target.critic.critic)
        _populate_critic_buffer(target)
        critic_sample = _assert_critic_generator_alignment(target.critic_buffer)
        critic_loss, critic_grad_norm = target.critic.update(
            critic_sample,
            value_normalizer=target.value_normalizer,
        )
        critic_gradient_count, _ = _gradient_evidence(target.critic.critic)
        _assert(critic_gradient_count > 0 and torch.isfinite(critic_grad_norm), "post-load critic gradients")
        _assert(_parameters_changed(target_critic_before, target.critic.critic), "post-load critic changed")
        _assert(target.critic.critic_optimizer.state, "post-load critic Adam state created")
        _assert(
            all(
                torch.isfinite(parameter).all()
                for module in target_modules
                for parameter in module.parameters()
            ),
            "post-load updated parameters finite",
        )
        _assert_states_unchanged(source_before_target_update, source_modules, "source isolated from target update")

        second_save = _save(
            coordinator,
            directory,
            manifest,
            target,
            generation=1,
            events=events,
        )
        _, _, second_marker = _verify_native_checkpoint(
            run_root,
            directory,
            manifest,
            target,
            generation=1,
        )
        second_digests = {
            (entry.artifact_role, entry.actor_identity): entry.file_sha256
            for entry in (
                *second_marker.actor_artifacts,
                second_marker.critic_artifact,
                second_marker.value_normalizer_artifact,
            )
            if entry is not None
        }
        _assert(
            first_marker.contract_fingerprint == second_marker.contract_fingerprint,
            "contract fingerprint stable across continuation save",
        )
        _assert(first_digests[("actor", "robot_0")] != second_digests[("actor", "robot_0")], "actor digest changed")
        _assert(first_digests[("critic", None)] != second_digests[("critic", None)], "critic digest changed")
        _assert(second_marker.checkpoint_generation == 1, "second generation")

        with _isolated_seed(9010):
            legacy_source = _construct_components("legacy")
        legacy_manifest = _manifest("legacy")
        legacy_run = temp_root / "legacy_run"
        legacy_directory = legacy_run / "models"
        legacy_events: list[str] = []
        legacy_coordinator = AssignmentCheckpointSaveCoordinator(
            legacy_run,
            event_recorder=legacy_events.append,
        )
        _save(
            legacy_coordinator,
            legacy_directory,
            legacy_manifest,
            legacy_source,
            generation=0,
            events=legacy_events,
        )
        legacy_artifacts, _, _ = _verify_native_checkpoint(
            legacy_run,
            legacy_directory,
            legacy_manifest,
            legacy_source,
            generation=0,
        )
        _assert("actor_agent_robot_0.pt" in legacy_artifacts, "native legacy canonical actor")
        legacy_reference = _probe(legacy_source)
        with _isolated_seed(9011):
            legacy_target = _construct_components("legacy")
        legacy_result = _load(
            legacy_directory,
            legacy_manifest,
            legacy_target,
            purpose=CompatibilityPurpose.NORMAL_EVALUATION,
        )
        _assert(not legacy_result.legacy_fallback_used, "native legacy does not use fallback")
        legacy_probe = _probe(legacy_target)
        for source_probs, target_probs in zip(
            legacy_reference.actor_probabilities,
            legacy_probe.actor_probabilities,
            strict=True,
        ):
            _assert(torch.equal(source_probs, target_probs), "native legacy actor output equality")

        corruption, missing, semantic, training_distinction, wrong_structure = _corruption_smokes(
            temp_root / "negative",
            manifest,
            source,
        )

        return SmokeResult(
            source_actor_parameter_count=sum(
                parameter.numel() for parameter in source.actors[0].actor.parameters()
            ),
            source_critic_parameter_count=sum(
                parameter.numel() for parameter in source.critic.critic.parameters()
            ),
            target_actor_parameter_count=sum(
                parameter.numel() for parameter in target.actors[0].actor.parameters()
            ),
            target_critic_parameter_count=sum(
                parameter.numel() for parameter in target.critic.critic.parameters()
            ),
            checkpoint_artifacts=artifacts,
            checkpoint_total_size=checkpoint_size,
            checkpoint_generation_first=first_save.checkpoint_generation,
            checkpoint_generation_second=second_save.checkpoint_generation,
            contract_fingerprint=compute_manifest_sha256(manifest),
            state_keys_compared=compared,
            state_keys_exact=exact,
            actor_output_max_abs_difference=actor_diff,
            critic_output_max_abs_difference=critic_diff,
            value_norm_output_max_abs_difference=value_diff,
            post_load_actor_loss=float(actor_loss.detach().item()),
            post_load_critic_loss=float(critic_loss.detach().item()),
            post_load_actor_gradient_norm=float(actor_grad_norm.detach().item()),
            post_load_critic_gradient_norm=float(critic_grad_norm.detach().item()),
            lifecycle_source_prepared=True,
            native_save_complete=True,
            metadata_verified=True,
            target_differed_before_load=target_differed,
            continuation_loaded=True,
            exact_state_equal=compared == exact,
            actor_outputs_equal=actor_diff == 0.0,
            critic_outputs_equal=critic_diff == 0.0,
            value_norm_equal=value_diff == 0.0,
            target_optimizers_fresh=True,
            post_load_actor_updated=True,
            post_load_critic_updated=True,
            source_isolated=True,
            evaluation_actor_only=True,
            named_ablation_loaded=True,
            legacy_native_equal=True,
            corruption_rejected_without_mutation=corruption,
            missing_marker_rejected_before_deserialization=missing,
            semantic_mismatch_rejected_before_deserialization=semantic,
            training_only_purpose_distinction=training_distinction,
            wrong_structure_rejected_without_mutation=wrong_structure,
            resave_complete=True,
            generation_advanced=(
                first_save.checkpoint_generation == 0
                and second_save.checkpoint_generation == 1
            ),
        )


_SMOKE_RESULT: SmokeResult | None = None


def _result() -> SmokeResult:
    global _SMOKE_RESULT
    if _SMOKE_RESULT is None:
        _SMOKE_RESULT = _run_smoke()
    return _SMOKE_RESULT


def test_lifecycle_source_real_harl_preparation_update() -> None:
    _assert(_result().lifecycle_source_prepared, "source preparation")


def test_lifecycle_native_save_through_project_coordinator() -> None:
    _assert(_result().native_save_complete, "native save")


def test_native_metadata_completion_and_artifact_inventory() -> None:
    result = _result()
    _assert(result.metadata_verified, "metadata validation")
    _assert(len(result.checkpoint_artifacts) == 8, "artifact count")
    _assert(result.checkpoint_total_size > 0, "checkpoint size")


def test_fresh_target_differs_before_load() -> None:
    _assert(_result().target_differed_before_load, "fresh target difference")


def test_validated_weight_continuation_load() -> None:
    _assert(_result().continuation_loaded, "validated continuation")


def test_exact_source_target_state_equality() -> None:
    result = _result()
    _assert(result.exact_state_equal, "state equality")
    _assert(result.state_keys_compared == result.state_keys_exact, "all state keys exact")


def test_actor_deterministic_output_equivalence() -> None:
    result = _result()
    _assert(result.actor_outputs_equal and result.actor_output_max_abs_difference == 0.0, "actor outputs")


def test_critic_output_equivalence() -> None:
    result = _result()
    _assert(result.critic_outputs_equal and result.critic_output_max_abs_difference == 0.0, "critic outputs")


def test_valuenorm_state_and_output_equivalence() -> None:
    result = _result()
    _assert(result.value_norm_equal and result.value_norm_output_max_abs_difference == 0.0, "ValueNorm")


def test_target_optimizer_reset_semantics() -> None:
    _assert(_result().target_optimizers_fresh, "target optimizers fresh")


def test_post_load_happo_update() -> None:
    result = _result()
    _assert(result.post_load_actor_updated, "post-load actor update")
    _assert(math.isfinite(result.post_load_actor_loss), "post-load actor loss")


def test_post_load_vcritic_update() -> None:
    result = _result()
    _assert(result.post_load_critic_updated, "post-load critic update")
    _assert(math.isfinite(result.post_load_critic_loss), "post-load critic loss")


def test_source_target_parameter_isolation() -> None:
    _assert(_result().source_isolated, "source isolation")


def test_actor_only_normal_evaluation_restore() -> None:
    _assert(_result().evaluation_actor_only, "normal evaluation actor-only")


def test_named_lifecycle_ablation_smoke() -> None:
    _assert(_result().named_ablation_loaded, "named ablation")


def test_native_legacy_save_load_output_equivalence() -> None:
    _assert(_result().legacy_native_equal, "native legacy")


def test_artifact_corruption_rejected_without_mutation() -> None:
    _assert(_result().corruption_rejected_without_mutation, "artifact corruption")


def test_missing_completion_marker_rejected_before_deserialization() -> None:
    _assert(_result().missing_marker_rejected_before_deserialization, "missing marker")


def test_semantic_contract_mismatch_rejected_before_deserialization() -> None:
    _assert(_result().semantic_mismatch_rejected_before_deserialization, "semantic mismatch")


def test_training_only_evaluation_continuation_distinction() -> None:
    _assert(_result().training_only_purpose_distinction, "purpose distinction")


def test_wrong_target_structure_rejected_without_partial_mutation() -> None:
    _assert(_result().wrong_structure_rejected_without_mutation, "wrong target structure")


def test_resave_after_continuation_and_generation_advance() -> None:
    result = _result()
    _assert(result.resave_complete, "continuation re-save")
    _assert(result.generation_advanced, "generation advanced")
    _assert(
        result.checkpoint_generation_first == 0 and result.checkpoint_generation_second == 1,
        "generation values",
    )


TESTS = (
    test_runtime_style_valuenorm_checkpoint_round_trip_cpu_and_cuda,
    test_lifecycle_source_real_harl_preparation_update,
    test_lifecycle_native_save_through_project_coordinator,
    test_native_metadata_completion_and_artifact_inventory,
    test_fresh_target_differs_before_load,
    test_validated_weight_continuation_load,
    test_exact_source_target_state_equality,
    test_actor_deterministic_output_equivalence,
    test_critic_output_equivalence,
    test_valuenorm_state_and_output_equivalence,
    test_target_optimizer_reset_semantics,
    test_post_load_happo_update,
    test_post_load_vcritic_update,
    test_source_target_parameter_isolation,
    test_actor_only_normal_evaluation_restore,
    test_named_lifecycle_ablation_smoke,
    test_native_legacy_save_load_output_equivalence,
    test_artifact_corruption_rejected_without_mutation,
    test_missing_completion_marker_rejected_before_deserialization,
    test_semantic_contract_mismatch_rejected_before_deserialization,
    test_training_only_evaluation_continuation_distinction,
    test_wrong_target_structure_rejected_without_partial_mutation,
    test_resave_after_continuation_and_generation_advance,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print a machine-readable summary.")
    args = parser.parse_args()
    torch.set_num_threads(1)
    results = []
    failed = False
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone runner records every smoke failure.
            failed = True
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    payload = {
        "status": "failed" if failed else "passed",
        "python": sys.executable,
        "torch": torch.__version__,
        "device": str(DEVICE),
        "smoke": None if _SMOKE_RESULT is None else asdict(_SMOKE_RESULT),
        "tests": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            prefix = "PASS" if result["status"] == "passed" else "FAIL"
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{prefix} {result['name']}{suffix}")
        if _SMOKE_RESULT is not None:
            print(
                f"METRICS state_keys={_SMOKE_RESULT.state_keys_exact}/"
                f"{_SMOKE_RESULT.state_keys_compared}, "
                f"checkpoint_bytes={_SMOKE_RESULT.checkpoint_total_size}, "
                f"generations={_SMOKE_RESULT.checkpoint_generation_first}->"
                f"{_SMOKE_RESULT.checkpoint_generation_second}"
            )
        print(f"{'FAIL' if failed else 'PASS'} {len(results)} checkpoint continuation smoke tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
