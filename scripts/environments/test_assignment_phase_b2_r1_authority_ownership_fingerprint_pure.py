"""Pure authority, digest, termination, fingerprint, and ownership tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as H  # noqa: E402


def test_digest_and_authority() -> dict[str, object]:
    E = H.E
    tensor = torch.arange(6, dtype=torch.float32).reshape(2, 3)
    base = E.canonical_digest_v1(("ordered", 1.0, tensor))
    H.assert_true(base == E.canonical_digest_v1(("ordered", 1.0, tensor.clone())), "copied digest")
    for changed in (
        ("ordered", 2.0, tensor),
        ("ordered", 1.0, tensor.to(torch.float64)),
        ("ordered", 1.0, tensor.reshape(3, 2)),
        ("ordered", 1.0, tensor + 1),
        (1.0, "ordered", tensor),
    ):
        H.assert_true(base != E.canonical_digest_v1(changed), "semantic digest difference lost")
    authority = H.authority()
    args = dict(
        expected_update_id=authority.update_id,
        expected_repository_head=authority.repository_head,
        expected_config_digest=authority.config_digest,
        expected_repo_source_hashes=authority.repo_source_hashes,
        expected_installed_harl_source_hashes=authority.installed_harl_source_hashes,
    )
    H.assert_true(E.validate_update_authority_binding_v1(authority, **args) == authority.authority_digest, "authority binding")
    drifts = (
        {**args, "expected_update_id": "wrong"},
        {**args, "expected_repository_head": "0" * 40},
        {**args, "expected_config_digest": H.digest("wrong-config")},
        {**args, "expected_repo_source_hashes": (E.B2RSourceDigestV1("repo/event.py", H.digest("changed")),)},
    )
    for drift in drifts:
        H.expect_stop(E.STOP_AUTHORITY_DRIFT, lambda drift=drift: E.validate_update_authority_binding_v1(authority, **drift))
    H.assert_true(H.config(resolved_E=5).config_digest != authority.config_digest, "dimension must bind config")
    return {"digest_equivalence": 2, "digest_differences": 6, "authority_faults": len(drifts) + 1}


def test_termination_and_inputs_schema() -> dict[str, object]:
    E = H.E
    R = E.B2RTerminationReasonV1
    cases = (
        (False, False, False, R.NONE),
        (True, False, False, R.ALL_TASKS_COMPLETED),
        (False, True, False, R.NO_FEASIBLE_TASKS_REMAIN),
        (False, False, True, R.TIME_LIMIT),
        (True, True, True, R.ALL_TASKS_COMPLETED),
    )
    for complete, infeasible, timeout, expected in cases:
        H.assert_true(E.select_authoritative_termination_reason_v1(all_tasks_completed=complete, no_feasible_tasks_remain=infeasible, time_limit=timeout) is expected, "precedence")
    valid = E.B2RTerminationSelectionEvidenceV1(R.TIME_LIMIT, False, False, True, True, "timeout-correlated")
    H.assert_true(len(valid.precedence_digest) == 64, "precedence digest")
    H.expect_stop(E.STOP_TERMINATION_PRECEDENCE, lambda: E.B2RTerminationSelectionEvidenceV1("UNKNOWN", False, False, False, False, "bad"))
    H.expect_stop(E.STOP_TERMINATION_PRECEDENCE, lambda: E.B2RTerminationSelectionEvidenceV1(R.TIME_LIMIT, True, False, True, True, "bad"))
    H.expect_stop(E.STOP_TERMINATION_PRECEDENCE, lambda: E.B2RTerminationSelectionEvidenceV1(R.ALL_TASKS_COMPLETED, True, False, True, True, "bad-timeout-use"))
    values = {field: H.digest(field) for field in (
        "authority_config_digest", "historical_actor_observation_digest", "historical_available_action_mask_digest",
        "original_proposal_action_digest", "original_behavior_logprob_digest", "dvm_digest", "active_mask_digest",
        "selected_reason_grid_digest", "precedence_resolution_evidence_digest", "terminal_correlation_evidence_digest",
        "timeout_critic_evidence_digest", "event_return_result_digest", "critic_training_slice_digest",
        "final_structural_return_slot_digest", "baseline_value_digest", "advantage_digest",
    )}
    frozen = E.B2RFrozenTrainingInputsV1(
        update_id="update-r1-0001", actor_canonical_identities=((0, 0, 0), (1, 2, 3)),
        termination_domain_valid=True, exactly_one_selected_category=True,
        return_equality_proof="exact tensor equality", return_no_alias_proof="distinct storage", **values,
    )
    H.assert_true(len(frozen.evidence_digest) == 64, "frozen inputs digest")
    return {"precedence_cases": len(cases), "faults": 3, "frozen_schema": 1}


def test_fingerprint_and_ownership() -> dict[str, object]:
    E = H.E
    torch.manual_seed(11)
    module = H.Tiny()
    optimizer = torch.optim.Adam(module.parameters(), lr=1e-3)
    valuenorm = H.TinyValueNorm()
    before = E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=module, optimizer=optimizer, value_normalizer=valuenorm)
    after = E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=module, optimizer=optimizer, value_normalizer=valuenorm)
    H.assert_true(before.fingerprint_digest == after.fingerprint_digest, "read-only fingerprint drift")
    H.assert_true(all(not item.present for item in before.gradients), "gradient state should remain absent")
    clone = H.Tiny()
    clone.load_state_dict(module.state_dict())
    clone.train(module.training)
    clone_fp = E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=clone, optimizer=torch.optim.Adam(clone.parameters(), lr=1e-3), value_normalizer=valuenorm)
    H.assert_true(before.fingerprint_digest == clone_fp.fingerprint_digest, "equivalent component")
    clone.eval()
    H.assert_true(before.fingerprint_digest != E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=clone, optimizer=torch.optim.Adam(clone.parameters(), lr=1e-3), value_normalizer=valuenorm).fingerprint_digest, "mode distinction")

    actors = [(f"actor{i}", H.Tiny(), None) for i in range(3)]
    actors = [(name, mod, torch.optim.Adam(mod.parameters(), lr=1e-3)) for name, mod, _ in actors]
    critic = H.Tiny()
    critic_opt = torch.optim.Adam(critic.parameters(), lr=1e-3)
    own = E.validate_parameter_ownership_v1(actor_bindings=actors, critic_binding=("critic", critic, critic_opt), shared_parameter_mode=False)
    H.assert_true(own.exact_ownership and own.actor_optimizers_disjoint and own.critic_disjoint_from_actors, "valid ownership")
    a0, a1 = H.Tiny(), H.Tiny()
    faults = [
        lambda: E.validate_parameter_ownership_v1(actor_bindings=(("actor0", a0, torch.optim.Adam(list(a0.parameters()) + list(critic.parameters()), lr=1e-3)),), critic_binding=("critic", critic, critic_opt), shared_parameter_mode=False),
        lambda: E.validate_parameter_ownership_v1(actor_bindings=(("actor0", a0, torch.optim.Adam(a0.parameters(), lr=1e-3)), ("actor1", a0, torch.optim.Adam(a0.parameters(), lr=1e-3))), critic_binding=("critic", critic, critic_opt), shared_parameter_mode=False),
        lambda: E.validate_parameter_ownership_v1(actor_bindings=(("actor0", a0, torch.optim.Adam(a0.parameters(), lr=1e-3)),), critic_binding=("critic", a0, torch.optim.Adam(a0.parameters(), lr=1e-3)), shared_parameter_mode=False),
        lambda: E.validate_parameter_ownership_v1(actor_bindings=(("actor0", a0, torch.optim.Adam([next(a0.parameters())], lr=1e-3)),), critic_binding=("critic", critic, critic_opt), shared_parameter_mode=False),
        lambda: E.validate_parameter_ownership_v1(actor_bindings=(("actor0", a0, torch.optim.Adam(list(a0.parameters()) + list(a1.parameters()), lr=1e-3)),), critic_binding=("critic", critic, critic_opt), shared_parameter_mode=False),
        lambda: E.validate_parameter_ownership_v1(actor_bindings=actors, critic_binding=("critic", critic, critic_opt), shared_parameter_mode=True),
    ]
    for fault in faults:
        H.expect_stop(E.STOP_OWNERSHIP, fault)
    final = E.fingerprint_component_v1(component_kind="actor", owner_identity="actor0", module=module, optimizer=optimizer, value_normalizer=valuenorm)
    H.assert_true(before.fingerprint_digest == final.fingerprint_digest, "fault tests mutated live fixture")
    return {"read_only_fingerprints": 4, "valid_ownership": 1, "ownership_faults": len(faults), "executed_mutations": 0}


def test_valuenorm_canonical_runtime_fingerprint() -> dict[str, object]:
    E = H.E
    registered = H.TinyValueNorm()
    old_dtype = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        runtime_style = H.TinyValueNorm()
    finally:
        torch.set_default_dtype(old_dtype)

    registered_one = E.fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=registered,
    )
    registered_two = E.fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=registered,
    )
    runtime_fp = E.fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=runtime_style,
    )
    H.assert_true(registered_one == registered_two, "canonical fingerprint must be deterministic")
    H.assert_true(len(registered_one.valuenorm_state) == 3, "canonical state must contain three fields")
    H.assert_true(
        tuple(item.name.split(".")[-1] for item in registered_one.valuenorm_state)
        == ("running_mean", "running_mean_sq", "debiasing_term"),
        "canonical ValueNorm field order",
    )
    H.assert_true(registered_one.fingerprint_digest == runtime_fp.fingerprint_digest, "Parameter/Tensor logical identity")
    H.assert_true(tuple(item.tensor.shape for item in registered_one.valuenorm_state) == ((1,), (1,), ()), "scalar debias shape")

    before = runtime_fp.fingerprint_digest
    runtime_style.debiasing_term.add_(1.0)
    after = E.fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=runtime_style,
    ).fingerprint_digest
    H.assert_true(before != after, "scalar live-state change must alter fingerprint")
    return {"assertions": 6, "canonical_fields": 3, "representations": 2}


if __name__ == "__main__":
    H.run([
        ("digest_authority", test_digest_and_authority),
        ("termination_inputs", test_termination_and_inputs_schema),
        ("fingerprint_ownership", test_fingerprint_and_ownership),
        ("valuenorm_runtime_fingerprint", test_valuenorm_canonical_runtime_fingerprint),
    ])
