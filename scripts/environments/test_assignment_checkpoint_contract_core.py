"""Phase 9G-8F-1 pure checkpoint contract core tests."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from decimal import Decimal
from pathlib import Path
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

from assignment_checkpoint_contract import (  # noqa: E402
    ArtifactFileInventoryEntry,
    AssignmentCheckpointContractManifest,
    AssignmentTrainingStateManifest,
    CompatibilityPurpose,
    CompatibilityRequest,
    ContractValidationError,
    MANIFEST_FORMAT_VERSION,
    NAMED_LIFECYCLE_ABLATION,
    StateDictTensorInventoryEntry,
    canonical_decimal,
    canonical_manifest_bytes,
    compare_state_dict_inventories,
    compute_manifest_sha256,
    compute_tensor_inventory_sha256,
    decide_missing_metadata,
    evaluate_compatibility,
    verify_manifest_sha256,
)


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
TAIL_FIELDS = (
    "agent_has_any_available_viewpoint",
    "team_has_any_available_viewpoint",
    "all_viewpoints_covered",
    "previous_assignment_was_noop",
    "episode_progress_norm",
    "previous_assignment_one_hot",
    "dynamic_scalars",
    "covered_vector",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(func: Callable[[], Any], expected: str) -> None:
    try:
        func()
    except (AttributeError, ContractValidationError, TypeError, ValueError) as exc:
        if expected not in str(exc):
            raise AssertionError(f"expected error containing {expected!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected error containing {expected!r}")


def _feature(name: str, shape: list[int], *, source: str) -> dict[str, Any]:
    return {
        "name": name,
        "source": source,
        "shape": shape,
        "dtype": "float32",
        "normalization": "schema_defined",
        "snapshot_timing": "next_policy_decision",
        "padding_semantics": "fixed_n_no_padding",
    }


def _manifest_mapping(
    *,
    profile: str = "lifecycle_contract_c",
    m: int = 3,
    n: int = 50,
    agent_names: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    names = agent_names or tuple(f"robot_{index}" for index in range(m))
    lifecycle = profile != "legacy"
    actor_dim = 100 + 3 * m + (19 if lifecycle else 16) * n
    shared_dim = m * actor_dim + (2 * m if lifecycle else 0)
    task_rows = TASK_ROW_LIFECYCLE if lifecycle else TASK_ROW_LEGACY
    actor_blocks = [
        _feature("raw_env_observation", [87 + 3 * m], source="ScanMobileManipulatorEnv._get_observations"),
        _feature("per_task_rows", [n, len(task_rows)], source="AssignmentHarlWrapper"),
        _feature("noop_context", [5], source="AssignmentHarlWrapper"),
        _feature("previous_assignment_one_hot", [n + 1], source="AssignmentHarlWrapper"),
        _feature("dynamic_scalars", [7], source="AssignmentHarlWrapper"),
        _feature("covered_vector", [n], source="AssignmentHarlWrapper"),
    ]
    shared_blocks = [
        _feature(f"actor_obs_robot_{index}", [actor_dim], source=f"actor_obs[{name}]")
        for index, name in enumerate(names)
    ]
    if lifecycle:
        for index in range(m):
            shared_blocks.extend(
                (
                    _feature(
                        f"budget_progress_robot_{index}",
                        [1],
                        source="LifecycleDecisionSnapshot.budget_attempt_steps",
                    ),
                    _feature(
                        f"budget_step_fraction_robot_{index}",
                        [1],
                        source="LifecycleDecisionSnapshot.budget_attempt_budget_steps",
                    ),
                )
            )
    if profile == "legacy":
        resolver_version = "disabled"
        mask_version = "legacy_mask_v1"
        budget_version = "disabled"
        guardrail = "legacy_guardrails_v1"
        actor_schema_version = "legacy_v1"
        shared_schema_version = "legacy_v1_shared_actor_concat"
        critic_budget_version = None
        sequence_version = "legacy_feed_forward_v1"
    else:
        resolver_version = "assignment_lifecycle_resolver_contract_c_v1"
        mask_version = "lifecycle_contract_c_mask_v1"
        budget_version = "budget_release_v1"
        guardrail = "lifecycle_no_legacy_guardrails_v1"
        actor_schema_version = "lifecycle_v1_actor_3n"
        shared_schema_version = "lifecycle_v1_shared_option_a_budget2m"
        critic_budget_version = "lifecycle_critic_budget_v1"
        sequence_version = "lifecycle_feed_forward_v1"
    return {
        "manifest_format_version": MANIFEST_FORMAT_VERSION,
        "identity": {
            "profile_name": profile,
            "training_time_profile": profile,
            "algorithm_name": "happo",
            "harl_state_type": "EP",
            "harl_shared_observation_mode": "environment_provided",
            "serialization_mode": "state_dict",
        },
        "scale": {
            "M": m,
            "N": n,
            "num_agents": m,
            "ordered_agent_names": list(names),
        },
        "actor_schema": {
            "actor_schema_version": actor_schema_version,
            "actor_dimension": actor_dim,
            "actor_dimension_by_agent": {name: actor_dim for name in names},
            "actor_ordered_feature_manifest": actor_blocks,
            "actor_task_row_field_order": list(task_rows),
            "actor_tail_field_order": list(TAIL_FIELDS),
        },
        "shared_schema": {
            "shared_schema_version": shared_schema_version,
            "shared_dimension": shared_dim,
            "shared_construction_mode": (
                "actor_concat_plus_critic_budget_2m" if lifecycle else "actor_concat"
            ),
            "shared_ordered_blocks": shared_blocks,
            "critic_budget_schema_version": critic_budget_version,
        },
        "action_contract": {
            "action_space_type": "Discrete",
            "action_dimension": n + 1,
            "target_action_min": 0,
            "target_action_max": n - 1,
            "noop_raw_id": n,
            "noop_decoded_value": -1,
        },
        "lifecycle_behavior_contract": {
            "snapshot_contract_version": (
                "lifecycle_decision_snapshot_v1" if lifecycle else "legacy_no_snapshot_v1"
            ),
            "resolver_contract_version": resolver_version,
            "mask_contract_version": mask_version,
            "budget_release_contract_version": budget_version,
            "legacy_guardrail_profile": guardrail,
            "ownership_contract_version": "exclusive_owner_active_equivalence_v1",
            "arbitration_contract_version": "lowest_cost_then_robot_id_v1",
        },
        "policy_sequence_contract": {
            "policy_sequence_contract_version": sequence_version,
            "policy_sequence_mode": "feed_forward",
            "use_recurrent_policy": False,
            "use_naive_recurrent_policy": False,
            "supported_actor_buffer_generator": "feed_forward_generator_actor",
        },
        "model_structure": {
            "actor_class": "HAPPO/StochasticPolicy",
            "critic_class": "VCritic/VNet",
            "action_distribution_class": "Categorical",
            "actor_hidden_sizes": [256, 256],
            "critic_hidden_sizes": [256, 256],
            "activation": "relu",
            "feature_normalization": True,
            "share_param": False,
            "number_of_actor_networks": m,
            "ordered_actor_network_names": list(names),
            "critic_architecture": "centralized_v_network",
            "harl_state_type": "EP",
            "recurrent_n": 1,
            "initialization_method": "orthogonal_",
            "action_gain": 0.01,
        },
        "training_contract": {
            "optimizer_class": "Adam",
            "actor_learning_rate": 0.0005,
            "critic_learning_rate": Decimal("0.0005000"),
            "optimizer_epsilon": 1e-5,
            "weight_decay": 0,
            "ppo_epochs": 5,
            "actor_minibatches": 2,
            "critic_minibatches": 2,
            "clip_coefficient": 0.2,
            "value_loss_coefficient": 1.0,
            "entropy_coefficient": 0.01,
            "gradient_clipping_enabled": True,
            "max_gradient_norm": 10.0,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "value_norm_enabled": True,
            "value_normalizer_contract": {
                "enabled": True,
                "adapter_contract_version": "harl_valuenorm_runtime_state_v1",
                "artifact_state_format": "harl_runtime_attribute_tensor_mapping_v1",
                "implementation_id": "harl.common.valuenorm.ValueNorm",
                "input_shape": [1],
                "norm_axes": 1,
                "beta": 0.99999,
                "epsilon": 0.00001,
                "per_element_update": False,
                "tensor_dtype": "float32",
                "canonical_state_keys": [
                    "running_mean",
                    "running_mean_sq",
                    "debiasing_term",
                ],
            },
            "proper_time_limits": True,
            "episode_length": 1000,
            "rollout_thread_count": 20,
        },
    }


def _manifest(**kwargs: Any) -> AssignmentCheckpointContractManifest:
    return AssignmentCheckpointContractManifest.from_mapping(_manifest_mapping(**kwargs))


def _changed(
    manifest: AssignmentCheckpointContractManifest,
    path: str,
    value: Any,
) -> AssignmentCheckpointContractManifest:
    mapping = copy.deepcopy(manifest.to_mapping())
    target = mapping
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    return AssignmentCheckpointContractManifest.from_mapping(mapping)


def _ablation_manifest() -> AssignmentCheckpointContractManifest:
    mapping = _manifest().to_mapping()
    mapping["identity"]["profile_name"] = "lifecycle_ablation"
    mapping["identity"]["training_time_profile"] = "lifecycle_ablation"
    behavior = mapping["lifecycle_behavior_contract"]
    behavior["resolver_contract_version"] = "disabled"
    behavior["mask_contract_version"] = "lifecycle_ablation_physical_mask_v1"
    behavior["budget_release_contract_version"] = "disabled"
    return AssignmentCheckpointContractManifest.from_mapping(mapping)


def _tensor_entries() -> tuple[StateDictTensorInventoryEntry, ...]:
    return (
        StateDictTensorInventoryEntry("act.linear.bias", (51,), "float32"),
        StateDictTensorInventoryEntry("base.mlp.fc.0.weight", (256, 1059), "torch.float32"),
    )


def _artifact(
    role: str,
    filename: str,
    *,
    actor_identity: str | None = None,
) -> ArtifactFileInventoryEntry:
    tensors = _tensor_entries()
    return ArtifactFileInventoryEntry(
        artifact_role=role,
        relative_file_name=filename,
        file_size=1234,
        file_sha256=("a" if role == "actor" else "b") * 64,
        serialization_mode="state_dict",
        actor_identity=actor_identity,
        tensor_inventory=tensors,
        tensor_inventory_sha256=compute_tensor_inventory_sha256(tensors),
    )


def _training_state(
    manifest: AssignmentCheckpointContractManifest,
    *,
    include_critic: bool = True,
    include_value_norm: bool = True,
) -> AssignmentTrainingStateManifest:
    fingerprint = compute_manifest_sha256(manifest)
    names = tuple(manifest.scale["ordered_agent_names"])
    return AssignmentTrainingStateManifest(
        contract_fingerprint=fingerprint,
        checkpoint_kind="temporary_test",
        checkpoint_generation=3,
        episode_or_update_index=7,
        continuation_classification="validated_weight_continuation",
        ordered_actor_identities=names,
        actor_artifacts=tuple(
            _artifact("actor", f"actor_agent_{name}.pt", actor_identity=name) for name in names
        ),
        critic_artifact=_artifact("critic", "critic_agent.pt") if include_critic else None,
        value_normalizer_artifact=(
            _artifact("value_normalizer", "value_normalizer.pt") if include_value_norm else None
        ),
        actor_optimizer_available=False,
        critic_optimizer_available=False,
        training_counters_available=False,
        rng_state_available=False,
        environment_resolver_state_available=False,
        rollout_buffer_state_available=False,
    )


def _request(
    purpose: CompatibilityPurpose,
    *,
    checkpoint: AssignmentCheckpointContractManifest | None = None,
    current: AssignmentCheckpointContractManifest | None = None,
    ablation_name: str | None = None,
    training_state: AssignmentTrainingStateManifest | None = None,
    acknowledged: bool = False,
) -> CompatibilityRequest:
    checkpoint = checkpoint or _manifest()
    return CompatibilityRequest(
        purpose=purpose,
        checkpoint_manifest=checkpoint,
        current_manifest=current or _manifest(),
        checkpoint_fingerprint=compute_manifest_sha256(checkpoint),
        explicit_ablation_name=ablation_name,
        training_state_manifest=training_state,
        continuation_reset_acknowledged=acknowledged,
    )


def test_manifest_lifecycle_and_legacy_fixtures() -> None:
    lifecycle = _manifest()
    legacy = _manifest(profile="legacy")
    _assert(lifecycle.actor_schema["actor_dimension"] == 1059, "lifecycle actor dimension")
    _assert(lifecycle.shared_schema["shared_dimension"] == 3183, "lifecycle shared dimension")
    _assert(legacy.actor_schema["actor_dimension"] == 909, "legacy actor dimension")
    _assert(legacy.shared_schema["shared_dimension"] == 2727, "legacy shared dimension")
    _assert(lifecycle.action_contract["action_dimension"] == 51, "action dimension")
    _assert(tuple(lifecycle.scale["ordered_agent_names"]) == ("robot_0", "robot_1", "robot_2"), "agent order")
    _expect_raises(lambda: lifecycle.scale.__setitem__("M", 4), "object has no attribute")
    _expect_raises(lambda: setattr(lifecycle.scale, "_items", ()), "immutable")


def test_manifest_general_m_n_formulas() -> None:
    manifest = _manifest(m=2, n=5)
    _assert(manifest.actor_schema["actor_dimension"] == 201, "general actor formula")
    _assert(manifest.shared_schema["shared_dimension"] == 406, "general shared formula")
    _assert(manifest.action_contract["noop_raw_id"] == 5, "general noop formula")


def test_canonical_object_key_order_determinism() -> None:
    manifest = _manifest()
    reversed_mapping = dict(reversed(list(manifest.to_mapping().items())))
    rebuilt = AssignmentCheckpointContractManifest.from_mapping(reversed_mapping)
    _assert(canonical_manifest_bytes(manifest) == canonical_manifest_bytes(rebuilt), "canonical bytes")
    _assert(compute_manifest_sha256(manifest) == compute_manifest_sha256(rebuilt), "canonical fingerprint")
    _assert(not canonical_manifest_bytes(manifest).endswith(b"\n"), "canonical bytes have no final newline")


def test_ordered_lists_remain_semantic() -> None:
    manifest = _manifest()
    mapping = manifest.to_mapping()
    rows = mapping["actor_schema"]["actor_task_row_field_order"]
    rows[0], rows[1] = rows[1], rows[0]
    reordered = AssignmentCheckpointContractManifest.from_mapping(mapping)
    _assert(canonical_manifest_bytes(manifest) != canonical_manifest_bytes(reordered), "list order changes bytes")
    _assert(compute_manifest_sha256(manifest) != compute_manifest_sha256(reordered), "list order changes hash")


def test_canonical_file_reparse_ignores_human_newline() -> None:
    manifest = _manifest()
    parsed = json.loads(canonical_manifest_bytes(manifest).decode("utf-8") + "\n")
    reparsed = AssignmentCheckpointContractManifest.from_mapping(parsed)
    _assert(canonical_manifest_bytes(reparsed) == canonical_manifest_bytes(manifest), "recanonicalization")


def test_contract_machine_specific_values_rejected() -> None:
    mapping = _manifest_mapping()
    mapping["identity"]["hostname"] = "worker-01"
    _expect_raises(lambda: AssignmentCheckpointContractManifest.from_mapping(mapping), "unexpected")
    mapping = _manifest_mapping()
    mapping["actor_schema"]["actor_ordered_feature_manifest"][0]["source"] = r"C:\repo\env.py"
    _expect_raises(lambda: AssignmentCheckpointContractManifest.from_mapping(mapping), "path value")
    mapping = _manifest_mapping()
    mapping["identity"]["training_time_profile"] = "run-2026-07-09T10"
    _expect_raises(lambda: AssignmentCheckpointContractManifest.from_mapping(mapping), "timestamp-like")


def test_number_canonicalization() -> None:
    cases = (
        (0, "0"),
        (-0.0, "0"),
        (0.0005, "0.0005"),
        ("5e-4", "0.0005"),
        (Decimal("0.0005000"), "0.0005"),
        (1.0, "1"),
        ("1.5000", "1.5"),
        ("1000000000000000000000", "1000000000000000000000"),
    )
    for value, expected in cases:
        _assert(canonical_decimal(value) == expected, f"canonical decimal {value!r}")
    _expect_raises(lambda: canonical_decimal(float("nan")), "finite")
    _expect_raises(lambda: canonical_decimal(float("inf")), "finite")
    _expect_raises(lambda: canonical_decimal("not-a-number"), "invalid numeric string")
    manifest = _manifest()
    _assert(manifest.training_contract["actor_learning_rate"] == "0.0005", "manifest decimal")
    _assert(isinstance(manifest.training_contract["episode_length"], int), "integer preserved")
    _assert(isinstance(manifest.training_contract["value_norm_enabled"], bool), "boolean preserved")


def test_fingerprint_integrity_and_strict_format() -> None:
    manifest = _manifest()
    fingerprint = compute_manifest_sha256(manifest)
    _assert(len(fingerprint) == 64 and fingerprint == fingerprint.lower(), "lowercase SHA-256")
    _assert(verify_manifest_sha256(manifest, fingerprint), "valid fingerprint")
    changed = _changed(manifest, "model_structure.action_gain", "0.02")
    _assert(not verify_manifest_sha256(changed, fingerprint), "changed field fails integrity")
    _expect_raises(lambda: verify_manifest_sha256(manifest, fingerprint.upper()), "lowercase")


def test_valuenorm_v2_contract_fingerprint_and_exact_validation() -> None:
    manifest = _manifest()
    _assert(manifest.manifest_format_version == MANIFEST_FORMAT_VERSION, "v2 manifest format")
    value_contract = manifest.training_contract["value_normalizer_contract"]
    _assert(value_contract["enabled"] is True, "ValueNorm enabled contract")
    _assert(value_contract["tensor_dtype"] == "float32", "canonical ValueNorm dtype")
    _assert(
        tuple(value_contract["canonical_state_keys"])
        == ("running_mean", "running_mean_sq", "debiasing_term"),
        "ValueNorm state key order",
    )
    fingerprint = compute_manifest_sha256(manifest)
    for path, value in (
        ("training_contract.value_normalizer_contract.beta", "0.99"),
        ("training_contract.value_normalizer_contract.epsilon", "0.00002"),
        ("training_contract.value_normalizer_contract.input_shape", [2]),
        ("training_contract.value_normalizer_contract.per_element_update", True),
        ("training_contract.value_normalizer_contract.tensor_dtype", "float64"),
    ):
        changed = _changed(manifest, path, value)
        _assert(compute_manifest_sha256(changed) != fingerprint, f"fingerprint binds {path}")
    changed_norm_axes = _changed(
        _changed(manifest, "training_contract.value_normalizer_contract.input_shape", [2, 2]),
        "training_contract.value_normalizer_contract.norm_axes",
        2,
    )
    _assert(
        compute_manifest_sha256(changed_norm_axes) != fingerprint,
        "fingerprint binds ValueNorm norm_axes",
    )
    mapping = manifest.to_mapping()
    mapping["training_contract"]["value_normalizer_contract"]["canonical_state_keys"] = [
        "running_mean_sq",
        "running_mean",
        "debiasing_term",
    ]
    _expect_raises(
        lambda: AssignmentCheckpointContractManifest.from_mapping(mapping),
        "canonical state-key order",
    )
    for field, value, expected in (
        ("adapter_contract_version", "other_adapter", "adapter contract version"),
        ("artifact_state_format", "other_format", "artifact state format"),
        ("implementation_id", "other.ValueNorm", "implementation identity"),
        ("tensor_dtype", "torch.float32", "canonical representation"),
    ):
        mapping = manifest.to_mapping()
        mapping["training_contract"]["value_normalizer_contract"][field] = value
        _expect_raises(
            lambda mapping=mapping: AssignmentCheckpointContractManifest.from_mapping(mapping),
            expected,
        )
    disabled = manifest.to_mapping()
    disabled["training_contract"]["value_norm_enabled"] = False
    disabled["training_contract"]["value_normalizer_contract"] = {"enabled": False}
    parsed_disabled = AssignmentCheckpointContractManifest.from_mapping(disabled)
    _assert(parsed_disabled.training_contract["value_normalizer_contract"] == {"enabled": False}, "disabled exact object")


def test_json_mapping_round_trip_and_structured_invalid_fingerprint() -> None:
    manifest = _manifest()
    training_state = _training_state(manifest)
    restored = AssignmentTrainingStateManifest.from_mapping(
        json.loads(json.dumps(training_state.to_mapping()))
    )
    _assert(restored.to_mapping() == training_state.to_mapping(), "training-state JSON round trip")

    request = _request(
        CompatibilityPurpose.NORMAL_EVALUATION,
        checkpoint=manifest,
        current=manifest,
    )
    json.dumps(request.to_mapping())
    invalid_request = CompatibilityRequest(
        purpose=CompatibilityPurpose.NORMAL_EVALUATION,
        checkpoint_manifest=manifest,
        current_manifest=manifest,
        checkpoint_fingerprint="not-a-sha256",
    )
    decision = evaluate_compatibility(invalid_request)
    _assert(
        not decision.allowed and decision.classification == "invalid_fingerprint",
        "malformed fingerprint must produce a structured rejection",
    )
    decision_mapping = decision.to_mapping()
    json.dumps(decision_mapping)
    _assert(decision_mapping["first_mismatch"] is None, "structured first mismatch")
    _expect_raises(lambda: verify_manifest_sha256(manifest, "z" * 64), "lowercase")
    _expect_raises(lambda: verify_manifest_sha256(manifest, "a" * 63), "lowercase")


def test_structural_compatibility_matching() -> None:
    decision = evaluate_compatibility(_request(CompatibilityPurpose.STRUCTURAL_INSPECTION))
    _assert(decision.allowed and decision.classification == "structurally_compatible", "structural match")
    _assert(decision.next_action == "weights_only_state_dict_inventory_inspection", "structural next stage")


def test_structural_compatibility_mismatches() -> None:
    checkpoint = _manifest()
    fp_mapping = checkpoint.to_mapping()
    fp_mapping["identity"]["harl_state_type"] = "FP"
    fp_mapping["model_structure"]["harl_state_type"] = "FP"
    variants = (
        _changed(checkpoint, "model_structure.actor_hidden_sizes", [128, 128]),
        _changed(checkpoint, "model_structure.critic_hidden_sizes", [512, 256]),
        _changed(checkpoint, "model_structure.share_param", True),
        AssignmentCheckpointContractManifest.from_mapping(fp_mapping),
    )
    for current in variants:
        decision = evaluate_compatibility(
            _request(CompatibilityPurpose.STRUCTURAL_INSPECTION, checkpoint=checkpoint, current=current)
        )
        _assert(not decision.allowed and decision.first_mismatch is not None, "structural mismatch")


def test_structural_agent_order_and_recurrent_mismatch() -> None:
    checkpoint = _manifest()
    reversed_names = ("robot_2", "robot_1", "robot_0")
    current = _manifest(agent_names=reversed_names)
    decision = evaluate_compatibility(
        _request(CompatibilityPurpose.STRUCTURAL_INSPECTION, checkpoint=checkpoint, current=current)
    )
    _assert(not decision.allowed, "agent order mismatch")

    legacy_checkpoint = _manifest(profile="legacy")
    mapping = legacy_checkpoint.to_mapping()
    mapping["policy_sequence_contract"]["use_recurrent_policy"] = True
    mapping["policy_sequence_contract"]["policy_sequence_mode"] = "recurrent"
    mapping["policy_sequence_contract"]["supported_actor_buffer_generator"] = "recurrent_generator_actor"
    mapping["model_structure"]["recurrent_n"] = 2
    recurrent = AssignmentCheckpointContractManifest.from_mapping(mapping)
    decision = evaluate_compatibility(
        _request(
            CompatibilityPurpose.STRUCTURAL_INSPECTION,
            checkpoint=legacy_checkpoint,
            current=recurrent,
        )
    )
    _assert(not decision.allowed, "recurrent structure mismatch")


def test_normal_evaluation_matching_and_training_only_differences() -> None:
    checkpoint = _manifest()
    current = _changed(checkpoint, "training_contract.actor_learning_rate", "0.001")
    current = _changed(current, "training_contract.ppo_epochs", 9)
    current = _changed(current, "training_contract.rollout_thread_count", 4)
    _assert(compute_manifest_sha256(checkpoint) != compute_manifest_sha256(current), "full fingerprints differ")
    decision = evaluate_compatibility(
        _request(CompatibilityPurpose.NORMAL_EVALUATION, checkpoint=checkpoint, current=current)
    )
    _assert(decision.allowed, "evaluation ignores training-only fields")


def test_normal_evaluation_semantic_mismatches() -> None:
    checkpoint = _manifest()
    variants = []
    mapping = checkpoint.to_mapping()
    rows = mapping["actor_schema"]["actor_task_row_field_order"]
    rows[0], rows[1] = rows[1], rows[0]
    variants.append(AssignmentCheckpointContractManifest.from_mapping(mapping))
    mapping = checkpoint.to_mapping()
    blocks = mapping["shared_schema"]["shared_ordered_blocks"]
    blocks[0], blocks[1] = blocks[1], blocks[0]
    variants.append(AssignmentCheckpointContractManifest.from_mapping(mapping))
    variants.append(_changed(checkpoint, "lifecycle_behavior_contract.mask_contract_version", "other_mask_v1"))
    variants.append(_changed(checkpoint, "lifecycle_behavior_contract.budget_release_contract_version", "other_budget_v1"))
    for current in variants:
        decision = evaluate_compatibility(
            _request(CompatibilityPurpose.NORMAL_EVALUATION, checkpoint=checkpoint, current=current)
        )
        _assert(not decision.allowed, "evaluation semantic mismatch")
    mapping = checkpoint.to_mapping()
    mapping["action_contract"]["noop_raw_id"] = 49
    _expect_raises(lambda: AssignmentCheckpointContractManifest.from_mapping(mapping), "action contract")


def test_normal_evaluation_agent_order_mismatch() -> None:
    decision = evaluate_compatibility(
        _request(
            CompatibilityPurpose.NORMAL_EVALUATION,
            checkpoint=_manifest(),
            current=_manifest(agent_names=("robot_2", "robot_1", "robot_0")),
        )
    )
    _assert(not decision.allowed, "evaluation agent order mismatch")


def test_named_ablation_exact_policy() -> None:
    checkpoint = _manifest()
    current = _ablation_manifest()
    decision = evaluate_compatibility(
        _request(
            CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            checkpoint=checkpoint,
            current=current,
            ablation_name=NAMED_LIFECYCLE_ABLATION,
        )
    )
    _assert(decision.allowed and decision.classification == "explicit_ablation_evaluation", "named ablation")


def test_named_ablation_rejects_missing_name_and_extra_difference() -> None:
    checkpoint = _manifest()
    current = _ablation_manifest()
    missing = evaluate_compatibility(
        _request(
            CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            checkpoint=checkpoint,
            current=current,
        )
    )
    _assert(not missing.allowed, "ablation name required")
    current = _changed(current, "lifecycle_behavior_contract.legacy_guardrail_profile", "other_guardrail")
    extra = evaluate_compatibility(
        _request(
            CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION,
            checkpoint=checkpoint,
            current=current,
            ablation_name=NAMED_LIFECYCLE_ABLATION,
        )
    )
    _assert(not extra.allowed and extra.first_mismatch is not None, "unauthorized ablation difference")
    continuation = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=checkpoint,
            current=_ablation_manifest(),
            ablation_name=NAMED_LIFECYCLE_ABLATION,
            training_state=_training_state(checkpoint),
            acknowledged=True,
        )
    )
    _assert(not continuation.allowed, "ablation cannot authorize continuation")


def test_validated_continuation_acknowledgement() -> None:
    manifest = _manifest()
    state = _training_state(manifest)
    pending = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=manifest,
            current=manifest,
            training_state=state,
        )
    )
    _assert(not pending.allowed and pending.required_acknowledgement, "acknowledgement required")
    accepted = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=manifest,
            current=manifest,
            training_state=state,
            acknowledged=True,
        )
    )
    _assert(accepted.allowed and accepted.classification == "validated_weight_continuation", "continuation")


def test_validated_continuation_rejects_training_changes() -> None:
    checkpoint = _manifest()
    paths = (
        ("training_contract.actor_learning_rate", "0.001"),
        ("training_contract.optimizer_epsilon", "0.0001"),
        ("training_contract.gamma", "0.9"),
        ("training_contract.gae_lambda", "0.8"),
    )
    state = _training_state(checkpoint)
    for path, value in paths:
        current = _changed(checkpoint, path, value)
        decision = evaluate_compatibility(
            _request(
                CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
                checkpoint=checkpoint,
                current=current,
                training_state=state,
                acknowledged=True,
            )
        )
        _assert(not decision.allowed and decision.first_mismatch is not None, f"continuation rejects {path}")
    mapping = checkpoint.to_mapping()
    mapping["training_contract"]["value_norm_enabled"] = False
    mapping["training_contract"]["value_normalizer_contract"] = {"enabled": False}
    current = AssignmentCheckpointContractManifest.from_mapping(mapping)
    decision = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=checkpoint,
            current=current,
            training_state=state,
            acknowledged=True,
        )
    )
    _assert(not decision.allowed and decision.first_mismatch is not None, "continuation rejects ValueNorm")


def test_validated_continuation_requires_critic_and_value_norm() -> None:
    manifest = _manifest()
    missing_critic = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=manifest,
            current=manifest,
            training_state=_training_state(manifest, include_critic=False),
            acknowledged=True,
        )
    )
    _assert(missing_critic.classification == "missing_critic_inventory", "critic required")
    missing_norm = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=manifest,
            current=manifest,
            training_state=_training_state(manifest, include_value_norm=False),
            acknowledged=True,
        )
    )
    _assert(missing_norm.classification == "missing_value_normalizer_inventory", "ValueNorm required")
    mapping = manifest.to_mapping()
    mapping["identity"]["serialization_mode"] = "pickle_full_model"
    _expect_raises(lambda: AssignmentCheckpointContractManifest.from_mapping(mapping), "state_dict")


def test_validated_continuation_rejects_actor_identity_inventory_mismatch() -> None:
    manifest = _manifest()
    state_mapping = _training_state(manifest).to_mapping()
    wrong_identities = ("agent_0", "agent_1", "agent_2")
    state_mapping["ordered_actor_identities"] = list(wrong_identities)
    for artifact, identity in zip(state_mapping["actor_artifacts"], wrong_identities, strict=True):
        artifact["actor_identity"] = identity
    mismatched_state = AssignmentTrainingStateManifest.from_mapping(state_mapping)
    decision = evaluate_compatibility(
        _request(
            CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION,
            checkpoint=manifest,
            current=manifest,
            training_state=mismatched_state,
            acknowledged=True,
        )
    )
    _assert(
        not decision.allowed and decision.classification == "actor_inventory_identity_mismatch",
        "continuation must bind ordered actor inventory to the checkpoint contract",
    )


def test_fine_tuning_and_exact_resume_unsupported() -> None:
    fine_tune = evaluate_compatibility(_request(CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING))
    _assert(not fine_tune.allowed and fine_tune.classification == "unsupported_deferred", "fine-tuning deferred")
    exact = evaluate_compatibility(_request(CompatibilityPurpose.EXACT_TRAINING_RESUME))
    _assert(not exact.allowed and "optimizer" in exact.reason, "exact resume unsupported")


def test_missing_metadata_and_legacy_policy() -> None:
    structural = decide_missing_metadata(
        purpose=CompatibilityPurpose.STRUCTURAL_INSPECTION,
        current_profile="lifecycle_contract_c",
        resolver_enabled=True,
        explicit_unversioned_legacy_fallback=False,
    )
    _assert(structural.allowed and structural.classification == "structural_inspection_only", "structural fallback")
    legacy = decide_missing_metadata(
        purpose=CompatibilityPurpose.NORMAL_EVALUATION,
        current_profile="legacy",
        resolver_enabled=False,
        explicit_unversioned_legacy_fallback=True,
    )
    _assert(legacy.allowed and legacy.classification == "legacy_evaluation_fallback", "legacy fallback")
    for purpose, profile in (
        (CompatibilityPurpose.NORMAL_EVALUATION, "lifecycle_contract_c"),
        (CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION, "legacy"),
        (CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING, "legacy"),
        (CompatibilityPurpose.EXACT_TRAINING_RESUME, "legacy"),
    ):
        decision = decide_missing_metadata(
            purpose=purpose,
            current_profile=profile,
            resolver_enabled=profile != "legacy",
            explicit_unversioned_legacy_fallback=True,
        )
        _assert(not decision.allowed, f"missing metadata rejects {purpose.value}")


def test_tensor_inventory_exact_and_mismatches() -> None:
    expected = _tensor_entries()
    exact = compare_state_dict_inventories(expected, tuple(reversed(expected)))
    _assert(exact.allowed, "inventory sorting and exact match")
    missing = compare_state_dict_inventories(expected, expected[:-1])
    _assert(not missing.allowed and missing.first_mismatch.category == "missing_tensor_key", "missing key")
    unexpected_entry = StateDictTensorInventoryEntry("unexpected.weight", (1,), "float32")
    unexpected = compare_state_dict_inventories(expected, (*expected, unexpected_entry))
    _assert(not unexpected.allowed, "unexpected key")
    shape = compare_state_dict_inventories(
        expected,
        (StateDictTensorInventoryEntry(expected[0].key, (52,), expected[0].dtype), expected[1]),
    )
    _assert(not shape.allowed and any(item.category == "tensor_shape" for item in shape.mismatches), "shape")
    dtype = compare_state_dict_inventories(
        expected,
        (StateDictTensorInventoryEntry(expected[0].key, expected[0].shape, "float64"), expected[1]),
    )
    _assert(not dtype.allowed and any(item.category == "tensor_dtype" for item in dtype.mismatches), "dtype")
    duplicate = compare_state_dict_inventories(expected, (expected[0], expected[0]))
    _assert(not duplicate.allowed and duplicate.classification == "invalid_tensor_inventory", "duplicate")


def test_artifact_paths_and_inventory_digest() -> None:
    artifact = _artifact("actor", r"models\actor_agent_robot_0.pt", actor_identity="robot_0")
    _assert(artifact.relative_file_name == "models/actor_agent_robot_0.pt", "path separator normalization")
    _assert(artifact.tensor_inventory_sha256 == compute_tensor_inventory_sha256(_tensor_entries()), "digest")
    _expect_raises(
        lambda: _artifact("actor", r"C:\models\actor.pt", actor_identity="robot_0"),
        "relative",
    )
    _expect_raises(
        lambda: _artifact("actor", "../actor.pt", actor_identity="robot_0"),
        "traversal",
    )


def test_training_state_manifest_and_actor_inventory() -> None:
    manifest = _manifest()
    state = _training_state(manifest)
    mapping = state.to_mapping()
    _assert(mapping["training_state_format_version"] == "assignment_training_state_v1", "state version")
    _assert(mapping["contract_fingerprint"] == compute_manifest_sha256(manifest), "fingerprint binding")
    _assert(
        [entry["actor_identity"] for entry in mapping["actor_artifacts"]]
        == ["robot_0", "robot_1", "robot_2"],
        "actor inventory order",
    )
    _expect_raises(
        lambda: AssignmentTrainingStateManifest(
            contract_fingerprint=compute_manifest_sha256(manifest),
            checkpoint_kind="temporary_test",
            checkpoint_generation=0,
            continuation_classification="weights",
            ordered_actor_identities=("robot_0", "robot_1", "robot_2"),
            actor_artifacts=state.actor_artifacts[:-1],
            critic_artifact=state.critic_artifact,
            value_normalizer_artifact=state.value_normalizer_artifact,
            actor_optimizer_available=False,
            critic_optimizer_available=False,
            training_counters_available=False,
            rng_state_available=False,
            environment_resolver_state_available=False,
            rollout_buffer_state_available=False,
        ),
        "complete",
    )
    _expect_raises(
        lambda: AssignmentTrainingStateManifest(
            contract_fingerprint="A" * 64,
            checkpoint_kind="temporary_test",
            checkpoint_generation=0,
            continuation_classification="weights",
            ordered_actor_identities=("robot_0",),
            actor_artifacts=(_artifact("actor", "actor.pt", actor_identity="robot_0"),),
            critic_artifact=None,
            value_normalizer_artifact=None,
            actor_optimizer_available=False,
            critic_optimizer_available=False,
            training_counters_available=False,
            rng_state_available=False,
            environment_resolver_state_available=False,
            rollout_buffer_state_available=False,
        ),
        "lowercase",
    )


def test_runtime_integration_absent() -> None:
    source = (SCAN_TASK_SOURCE / "assignment_checkpoint_contract.py").read_text(encoding="utf-8")
    for forbidden in ("import torch", "import harl", "import isaaclab", "AppLauncher", "load_state_dict", "torch.load"):
        _assert(forbidden not in source, f"pure core must not contain {forbidden!r}")
    wrapper_source = (SCAN_TASK_SOURCE / "assignment_harl_wrapper.py").read_text(encoding="utf-8")
    _assert("assignment_checkpoint_contract" not in wrapper_source, "wrapper has no checkpoint contract coupling")
    _assert("assignment_checkpoint_load" not in wrapper_source, "wrapper has no checkpoint loader coupling")
    assignment_load_entry_files = (
        REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play.py",
        REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py",
        REPO_ROOT / "scripts" / "environments" / "evaluate_assignment_rl_playback_diagnostics.py",
        REPO_ROOT / "scripts" / "environments" / "evaluate_assignment_methods.py",
    )
    for path in assignment_load_entry_files:
        text = path.read_text(encoding="utf-8")
        _assert("torch.load(" not in text, f"no direct assignment torch.load: {path}")


TESTS = (
    test_manifest_lifecycle_and_legacy_fixtures,
    test_manifest_general_m_n_formulas,
    test_canonical_object_key_order_determinism,
    test_ordered_lists_remain_semantic,
    test_canonical_file_reparse_ignores_human_newline,
    test_contract_machine_specific_values_rejected,
    test_number_canonicalization,
    test_fingerprint_integrity_and_strict_format,
    test_valuenorm_v2_contract_fingerprint_and_exact_validation,
    test_json_mapping_round_trip_and_structured_invalid_fingerprint,
    test_structural_compatibility_matching,
    test_structural_compatibility_mismatches,
    test_structural_agent_order_and_recurrent_mismatch,
    test_normal_evaluation_matching_and_training_only_differences,
    test_normal_evaluation_semantic_mismatches,
    test_normal_evaluation_agent_order_mismatch,
    test_named_ablation_exact_policy,
    test_named_ablation_rejects_missing_name_and_extra_difference,
    test_validated_continuation_acknowledgement,
    test_validated_continuation_rejects_training_changes,
    test_validated_continuation_requires_critic_and_value_norm,
    test_validated_continuation_rejects_actor_identity_inventory_mismatch,
    test_fine_tuning_and_exact_resume_unsupported,
    test_missing_metadata_and_legacy_policy,
    test_tensor_inventory_exact_and_mismatches,
    test_artifact_paths_and_inventory_digest,
    test_training_state_manifest_and_actor_inventory,
    test_runtime_integration_absent,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable results.")
    args = parser.parse_args()
    results = []
    failed = False
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone contract test runner.
            failed = True
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    output = {
        "status": "failed" if failed else "passed",
        "num_tests": len(results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
        "canonical_determinism": "passed" if not failed else "see individual tests",
        "compatibility_matrix": "passed" if not failed else "see individual tests",
        "tests": results,
    }
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        for result in results:
            prefix = "PASS" if result["status"] == "passed" else "FAIL"
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{prefix} {result['name']}{suffix}")
        print(f"{'FAIL' if failed else 'PASS'} {output['passed']}/{output['num_tests']} tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
