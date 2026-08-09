# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

"""Project-local lifecycle policy-sequence contract and startup validation."""

from typing import Any, Mapping

if __package__:
    from .assignment_profile_contract import (
        LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON,
        AssignmentProfileName,
        AssignmentProfileSupport,
        ResolvedAssignmentProfile,
        ResolvedExistingAssignmentProfile,
        require_assignment_profile_runtime_ready,
    )
else:  # Direct test compatibility while retaining one canonical contract key.
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import (  # type: ignore
        LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON,
        AssignmentProfileName,
        AssignmentProfileSupport,
        ResolvedAssignmentProfile,
        ResolvedExistingAssignmentProfile,
        require_assignment_profile_runtime_ready,
    )


LIFECYCLE_CONTRACT_C_PROFILE = "lifecycle_contract_c"
LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION = "lifecycle_feed_forward_v1"
FEED_FORWARD_GENERATOR = "feed_forward_generator_actor"
NAIVE_RECURRENT_GENERATOR = "naive_recurrent_generator_actor"
CHUNKED_RECURRENT_GENERATOR = "recurrent_generator_actor"
LIFECYCLE_SUPPORTED_ALGORITHM = "happo"
LIFECYCLE_SUPPORTED_STATE_TYPE = "EP"

LIFECYCLE_RECURRENT_POLICY_ERROR = """lifecycle_contract_c_v1 supports feed-forward policies only.

The pinned installed HARL chunked recurrent generator is incompatible
with the current PyTorch tensor buffer, and recurrent modes are outside
the official lifecycle support matrix.

Set:
  use_recurrent_policy = False
  use_naive_recurrent_policy = False

No installed HARL package modification is required."""


def _require_resolved_bool(model_args: Mapping[str, Any], field: str) -> bool:
    if field not in model_args:
        raise ValueError(
            f"lifecycle_contract_c_v1 requires resolved HARL model.{field}; "
            "the field is missing from algo_args['model']."
        )
    value = model_args[field]
    if not isinstance(value, bool):
        raise ValueError(
            f"lifecycle_contract_c_v1 requires HARL model.{field} to resolve to a boolean, "
            f"got {value!r} ({type(value).__name__})."
        )
    return value


def _optional_resolved_bool(mapping: Mapping[str, Any] | None, field: str, default: bool) -> bool:
    if mapping is None or field not in mapping:
        return bool(default)
    value = mapping[field]
    if not isinstance(value, bool):
        raise ValueError(
            f"lifecycle_contract_c_v1 requires HARL {field} to resolve to a boolean, "
            f"got {value!r} ({type(value).__name__})."
        )
    return value


def _algorithm_name_from_runtime(
    *,
    algo_args: Mapping[str, Any],
    env_args: Mapping[str, Any],
) -> str:
    for candidate in (
        env_args.get("algorithm"),
        env_args.get("algo"),
        algo_args.get("algorithm_name"),
        algo_args.get("algorithm"),
        algo_args.get("algo_name"),
    ):
        if candidate is not None:
            return str(candidate).strip().lower()
    return LIFECYCLE_SUPPORTED_ALGORITHM


def resolve_installed_harl_actor_buffer_generator(
    *,
    use_recurrent_policy: bool,
    use_naive_recurrent_policy: bool,
) -> str:
    """Mirror the installed HARL actor-training branch precedence by name."""

    if use_recurrent_policy:
        return CHUNKED_RECURRENT_GENERATOR
    if use_naive_recurrent_policy:
        return NAIVE_RECURRENT_GENERATOR
    return FEED_FORWARD_GENERATOR


def policy_sequence_contract_for_profile(
    resolved_assignment_profile: ResolvedAssignmentProfile,
) -> dict[str, Any]:
    """Return immutable-by-convention sequence metadata for an observation manifest."""

    profile = require_assignment_profile_runtime_ready(
        resolved_assignment_profile,
        consumer="policy_sequence_contract_for_profile",
        entrypoint="resolved-profile consumer",
        barrier="before existing policy-sequence dispatch",
    )
    profile_name = profile.profile_name
    if profile_name is AssignmentProfileName.LIFECYCLE_CONTRACT_C:
        return {
            "policy_sequence_contract_version": LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION,
            "policy_sequence_mode": "feed_forward",
            "use_recurrent_policy": False,
            "use_naive_recurrent_policy": False,
            "supported_actor_buffer_generator": FEED_FORWARD_GENERATOR,
            "unsupported_actor_buffer_generators": [
                NAIVE_RECURRENT_GENERATOR,
                CHUNKED_RECURRENT_GENERATOR,
            ],
        }
    if profile_name is AssignmentProfileName.LEGACY:
        return {
            "policy_sequence_contract_version": "legacy_existing_policy_sequence_v1",
            "policy_sequence_mode": "existing_legacy_behavior",
            "use_recurrent_policy": None,
            "use_naive_recurrent_policy": None,
            "supported_actor_buffer_generator": "resolved_by_legacy_harl_config",
            "unsupported_actor_buffer_generators": [],
        }
    if profile_name is AssignmentProfileName.LIFECYCLE_ABLATION:
        return {
            "policy_sequence_contract_version": "lifecycle_ablation_no_training_v1",
            "policy_sequence_mode": "not_training_enabled",
            "use_recurrent_policy": None,
            "use_naive_recurrent_policy": None,
            "supported_actor_buffer_generator": None,
            "unsupported_actor_buffer_generators": [],
        }
    if profile_name is AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE:
        return {
            "policy_sequence_contract_version": "diagnostics_only_no_training_v1",
            "policy_sequence_mode": "diagnostics_only",
            "use_recurrent_policy": None,
            "use_naive_recurrent_policy": None,
            "supported_actor_buffer_generator": None,
            "unsupported_actor_buffer_generators": [],
        }
    raise TypeError(
        "existing assignment policy-sequence dispatch is not exhaustive: "
        f"{profile_name!r}"
    )


def _require_training_enabled(
    profile: ResolvedExistingAssignmentProfile,
) -> None:
    if profile.training_support is AssignmentProfileSupport.ALLOWED:
        return
    if profile.profile_name is AssignmentProfileName.LIFECYCLE_ABLATION:
        raise RuntimeError(LIFECYCLE_ABLATION_TRAINING_BLOCKED_REASON)
    if profile.profile_name is AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE:
        raise RuntimeError(
            "assignment_lifecycle_profile='diagnostics_hidden_state' is not training-ready."
        )
    raise RuntimeError(
        "resolved existing assignment profile is not training-enabled: "
        f"profile={profile.profile_name.value!r}; "
        f"training_support={profile.training_support.value!r}."
    )


def validate_assignment_lifecycle_policy_sequence(
    *,
    resolved_assignment_profile: ResolvedAssignmentProfile,
    algo_args: Mapping[str, Any],
    env_args: Mapping[str, Any],
) -> dict[str, Any]:
    """Reject unsupported lifecycle recurrent modes from fully resolved runtime config."""

    profile = require_assignment_profile_runtime_ready(
        resolved_assignment_profile,
        consumer="validate_assignment_lifecycle_policy_sequence",
        entrypoint="assignment training",
        barrier="before runner RNG, output, environment, actor, and checkpoint initialization",
    )
    contract = policy_sequence_contract_for_profile(profile)
    _require_training_enabled(profile)
    if profile.profile_name is not AssignmentProfileName.LIFECYCLE_CONTRACT_C:
        return contract

    algorithm_name = _algorithm_name_from_runtime(algo_args=algo_args, env_args=env_args)
    if algorithm_name != LIFECYCLE_SUPPORTED_ALGORITHM:
        raise RuntimeError(
            "lifecycle_contract_c_v1 supports HAPPO only; "
            f"got algorithm={algorithm_name!r}."
        )

    state_type = str(env_args.get("state_type", LIFECYCLE_SUPPORTED_STATE_TYPE)).strip().upper()
    if state_type != LIFECYCLE_SUPPORTED_STATE_TYPE:
        raise RuntimeError(
            "lifecycle_contract_c_v1 supports HARL state_type='EP' only; "
            f"got state_type={state_type!r}."
        )

    algo_section = algo_args.get("algo")
    if algo_section is not None and not isinstance(algo_section, Mapping):
        raise ValueError("lifecycle_contract_c_v1 requires resolved HARL algo_args['algo'] to be a mapping.")
    share_param = _optional_resolved_bool(algo_section, "share_param", False)
    if share_param:
        raise RuntimeError("lifecycle_contract_c_v1 requires algo.share_param=False.")

    train_section = algo_args.get("train")
    if train_section is not None and not isinstance(train_section, Mapping):
        raise ValueError("lifecycle_contract_c_v1 requires resolved HARL algo_args['train'] to be a mapping.")
    save_entire_model = _optional_resolved_bool(train_section, "save_entire_model", False)
    if save_entire_model:
        raise RuntimeError(
            "lifecycle_contract_c_v1 requires train.save_entire_model=False "
            "and state_dict checkpoint serialization."
        )

    model_args = algo_args.get("model")
    if not isinstance(model_args, Mapping):
        raise ValueError(
            "lifecycle_contract_c_v1 requires resolved HARL algo_args['model'] "
            "before runner construction."
        )
    use_recurrent_policy = _require_resolved_bool(model_args, "use_recurrent_policy")
    use_naive_recurrent_policy = _require_resolved_bool(model_args, "use_naive_recurrent_policy")
    selected_generator = resolve_installed_harl_actor_buffer_generator(
        use_recurrent_policy=use_recurrent_policy,
        use_naive_recurrent_policy=use_naive_recurrent_policy,
    )
    if use_recurrent_policy and use_naive_recurrent_policy:
        raise RuntimeError(
            "Contradictory lifecycle recurrent flags are enabled; installed HARL would prioritize "
            f"{CHUNKED_RECURRENT_GENERATOR}.\n\n{LIFECYCLE_RECURRENT_POLICY_ERROR}"
        )
    if use_recurrent_policy or use_naive_recurrent_policy:
        raise RuntimeError(
            f"Resolved installed HARL actor-buffer generator would be {selected_generator}.\n\n"
            f"{LIFECYCLE_RECURRENT_POLICY_ERROR}"
        )
    if selected_generator != FEED_FORWARD_GENERATOR:
        raise RuntimeError(
            "lifecycle_contract_c_v1 generator resolution is inconsistent: "
            f"expected {FEED_FORWARD_GENERATOR}, got {selected_generator}."
        )
    return contract


__all__ = [
    "CHUNKED_RECURRENT_GENERATOR",
    "FEED_FORWARD_GENERATOR",
    "LIFECYCLE_CONTRACT_C_PROFILE",
    "LIFECYCLE_POLICY_SEQUENCE_CONTRACT_VERSION",
    "LIFECYCLE_RECURRENT_POLICY_ERROR",
    "LIFECYCLE_SUPPORTED_ALGORITHM",
    "LIFECYCLE_SUPPORTED_STATE_TYPE",
    "NAIVE_RECURRENT_GENERATOR",
    "policy_sequence_contract_for_profile",
    "resolve_installed_harl_actor_buffer_generator",
    "validate_assignment_lifecycle_policy_sequence",
]
