"""B2-V1-D pre/post-step failure, poison, fallback, and readiness gate."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_v1_event_route_helpers as H  # noqa: E402


PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"


def _fresh():
    harness = H.lifecycle_harness()
    harness.route.reset()
    return harness


def _assert_clean_pre_failure(harness: H.RouteHarness) -> None:
    H.assert_true(harness.raw.step_calls == 0, "pre-step failure reached physical boundary")
    H.assert_true(harness.buffer.step == 0 and not bool(harness.buffer._event_slot_written.any()), "pre-step critic commit")
    H.assert_true(all(storage.next_action_slot == 0 for storage in harness.route.actor_storages), "pre-step actor commit")
    H.assert_true(not harness.route.poisoned, "reversible pre-step failure poisoned route")


def _assert_poisoned_post_failure(harness: H.RouteHarness) -> None:
    H.assert_true(harness.raw.step_calls == 1, "post-step failure physical count")
    H.assert_true(harness.route.poisoned, "irreversible post-step failure did not poison")
    before = harness.raw.step_calls
    H.expect_failure(harness.route.collect_step, "route_poisoned")
    H.assert_true(harness.raw.step_calls == before, "poison retry executed a second physical step")


def test_v1_d1_pre_step_stale_p2_open_generation_matrix() -> dict[str, object]:
    # Stale P2: authoritative state changed externally, so the old bundle is
    # rejected cleanly but is intentionally not retryable without a rebind.
    stale = _fresh()
    stale.domain.environment_port.finalize_physical_transition(
        H.I4._report(stale.domain, problem=stale.raw.problem, step=90)
    )
    H.expect_failure(stale.route.collect_step, "source_publication_mismatch")
    _assert_clean_pre_failure(stale)

    # Stale OPEN: inject another valid domain's opaque OPEN identity, restore,
    # then prove the unchanged physical state can be retried successfully.
    window = _fresh()
    other_domain = _fresh().domain
    original_validator = window.route._current_decision_validator
    window.route._current_decision_validator = lambda bundle: bundle.evidence_snapshot.validate_current(
        current_publication=window.domain.current_read_port.read_current(),
        current_open_window_view=other_domain.interstep_fence_read_port.read(),
    )
    H.expect_failure(window.route.collect_step, "open_window_identity_mismatch")
    _assert_clean_pre_failure(window)
    window.route._current_decision_validator = original_validator
    window.route.collect_step()
    H.assert_true(window.raw.step_calls == 1 and window.buffer.step == 1, "OPEN retry did not recover")

    generation = _fresh()
    publication = generation.domain.current_read_port.read_current()
    lifecycle_view = publication.lifecycle_view
    original_generation = lifecycle_view._transition_generation
    object.__setattr__(lifecycle_view, "_transition_generation", original_generation + 1)
    try:
        H.expect_failure(generation.route.collect_step, "transition_generation_mismatch")
        _assert_clean_pre_failure(generation)
    finally:
        object.__setattr__(lifecycle_view, "_transition_generation", original_generation)
    generation.route.collect_step()
    H.assert_true(generation.raw.step_calls == 1, "generation retry did not recover")
    return {"stale_P2": "clean reject", "stale_OPEN": "retry-safe", "wrong_generation": "retry-safe"}


def test_v1_d2_pre_step_bad_i2_actor_output_i42_source_matrix() -> dict[str, object]:
    bad_i2 = _fresh()
    other = _fresh()
    original_validator = bad_i2.route._current_decision_validator
    bad_i2.route._current_decision_validator = lambda bundle: bundle.validate_evidence_snapshot(
        other.route.current_decision_bundle.evidence_snapshot
    )
    H.expect_failure(bad_i2.route.collect_step)
    _assert_clean_pre_failure(bad_i2)
    bad_i2.route._current_decision_validator = original_validator
    bad_i2.route.collect_step()

    class InvalidActor:
        def get_actions(self, obs, rnn_states, masks, available_actions, deterministic=False):
            return (
                torch.full((obs.shape[0], 1), 999, dtype=torch.int64),
                torch.zeros((obs.shape[0], 1), dtype=torch.float32),
                rnn_states.detach().clone(),
            )

    actor = _fresh()
    original_actors = actor.route.actors
    actor.route.actors = (InvalidActor(), *original_actors[1:])
    H.expect_failure(actor.route.collect_step, "actor_action_out_of_range")
    _assert_clean_pre_failure(actor)
    actor.route.actors = original_actors
    actor.route.collect_step()

    i42 = _fresh()
    wrong_source = _fresh()
    original_capture = i42.route._capture_i42_decision

    def capture_wrong(**_kwargs):
        physical = wrong_source.route.current_decision_bundle.evidence_snapshot.physical_evidence
        bundle = wrong_source.route.current_decision_bundle
        return wrong_source.wrapper._capture_event_proposal_decision(
            feasible_mask=physical.explicit_physical_feasibility,
            cost_matrix=physical.geometric_pair_ranking_cost,
            available_mask=(bundle.available_actions_bool[..., :4] & bundle.policy_row_mask.expand(-1, -1, 4)).contiguous(),
        )

    i42.route._capture_i42_decision = capture_wrong
    H.expect_failure(i42.route.collect_step, "i42_proposal_source_mismatch")
    _assert_clean_pre_failure(i42)
    i42.route._capture_i42_decision = original_capture
    for scripted in i42.route.actors:
        scripted.calls.clear()
    i42.route.collect_step()
    return {"bad_I2_identity": "clean/retry", "bad_actor_output": "clean/retry", "I4_source_mismatch": "clean/retry"}


def test_v1_d3_post_step_next_i1_and_next_i2_poison() -> dict[str, object]:
    next_i1 = _fresh()
    next_i1.route._current_decision_supplier = lambda: (_ for _ in ()).throw(RuntimeError("synthetic next I1 failure"))
    H.expect_failure(next_i1.route.collect_step)
    _assert_poisoned_post_failure(next_i1)
    H.assert_true(next_i1.buffer.step == 0 and all(storage.next_action_slot == 0 for storage in next_i1.route.actor_storages), "next I1 partial insert")

    next_i2 = _fresh()
    next_i2.route._current_decision_supplier = lambda: object()
    H.expect_failure(next_i2.route.collect_step, "decision_bundle_type")
    _assert_poisoned_post_failure(next_i2)
    H.assert_true(next_i2.buffer.step == 0 and all(storage.next_action_slot == 0 for storage in next_i2.route.actor_storages), "next I2 partial insert")
    return {"next_I1": "poison/no retry", "next_I2": "poison/no retry", "partial_commits": 0}


def test_v1_d4_post_step_dto_and_critic_insertion_poison() -> dict[str, object]:
    dto = _fresh()
    original_attach = H.ROUTE.attach_event_terminal_infos_to_harl_step_v2

    def bad_attach(**kwargs):
        result = original_attach(**kwargs)
        result[4][1][0].pop(H.LT.EVENT_TERMINAL_LEARNER_INFO_KEY_V2)
        return result

    H.ROUTE.attach_event_terminal_infos_to_harl_step_v2 = bad_attach
    try:
        H.expect_failure(dto.route.collect_step, "terminal_dto_missing")
    finally:
        H.ROUTE.attach_event_terminal_infos_to_harl_step_v2 = original_attach
    _assert_poisoned_post_failure(dto)
    H.assert_true(dto.buffer.step == 0 and all(storage.next_action_slot == 0 for storage in dto.route.actor_storages), "DTO mismatch partial commit")

    critic = _fresh()
    critic.buffer.insert_event = lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic critic insert failure"))
    H.expect_failure(critic.route.collect_step)
    _assert_poisoned_post_failure(critic)
    H.assert_true(critic.route.collector._poisoned, "collector not poisoned after reserved terminal failure")
    H.assert_true(critic.buffer.step == 0 and all(storage.next_action_slot == 0 for storage in critic.route.actor_storages), "critic insert partial commit")
    return {"terminal_DTO": "poison/no retry", "critic_insert": "poison/no retry", "duplicate_consumption": 0}


def test_v1_d5_actor_partial_commit_is_poisoned_and_cannot_continue() -> dict[str, object]:
    harness = _fresh()
    cls = H.COLLECTION.EventPolicyActorSlotStorageV2
    original_insert = cls.insert_transition

    def fail_second(self, **kwargs):
        if self.agent_id == 1:
            raise RuntimeError("synthetic actor insertion failure")
        return original_insert(self, **kwargs)

    cls.insert_transition = fail_second
    try:
        H.expect_failure(harness.route.collect_step)
    finally:
        cls.insert_transition = original_insert
    _assert_poisoned_post_failure(harness)
    slots = tuple(storage.next_action_slot for storage in harness.route.actor_storages)
    H.assert_true(harness.buffer.step == 1 and slots == (1, 0, 0), f"expected critic/actor partial commit evidence: {slots}")
    H.assert_true(len(harness.route.collector.consumed_terminal_keys) == 2, "terminal ledger reservation lost after partial commit")
    return {"critic_committed": 1, "actor_slots": slots, "route_poisoned": True, "continued_rollout": False}


def test_v1_d6_public_readiness_attacks_and_private_only_factory() -> dict[str, object]:
    harness = _fresh()
    before = harness.raw.step_calls
    H.expect_failure(lambda: harness.wrapper.step(torch.zeros((4, 3, 1), dtype=torch.float32)))
    H.assert_true(harness.raw.step_calls == before, "public wrapper event route opened")

    training = H.load_path(f"{PREFIX}.assignment_harl_training", H.SCAN_SOURCE / "assignment_harl_training.py")
    config = SimpleNamespace(assignment_lifecycle_profile="event_gated_local_mrta")
    env_args = {"assignment_rl": True, "config": config}
    H.expect_failure(
        lambda: training.AssignmentIsaacLabEnv(
            env_args,
            resolved_assignment_profile=harness.profile,
            profile_resolution_origin=harness.profile.resolution_origin,
        )
    )
    H.expect_failure(
        lambda: training.AssignmentOnPolicyHARunner(
            {}, {}, env_args, resolved_assignment_profile=harness.profile
        )
    )
    H.expect_failure(
        lambda: H.ROUTE.EventDormantLearnedPolicyRouteV2(
            episode_length=1,
            actors=(),
            critic=object(),
            critic_buffer=object(),
            admitted_reset=lambda: None,
            current_decision_supplier=lambda: None,
            current_decision_validator=lambda _x: None,
            capture_i42_decision=lambda: None,
            step_i42_proposals=lambda: None,
            action_builder=None,
            actor_trainer=lambda: None,
            critic_trainer=lambda: None,
            value_normalizer=None,
            actor_rnn_shape=(1, 1),
            call_observer=None,
            factory_capability=object(),
        ),
        "private_factory_required",
    )
    private = H.scale_harness()
    private.route.reset()
    H.assert_true(private.route.current_decision_bundle is not None, "private test factory unavailable")
    H.assert_true(H.ROUTE.__all__ == (), "private import became public export")
    return {"wrapper_step": "blocked", "env_construction": "blocked", "runner_construction": "blocked", "direct_constructor": "blocked", "private_test_factory": "callable"}


def test_v1_d7_no_stock_or_hidden_fallback_static_call_record() -> dict[str, object]:
    source = (H.SCAN_SOURCE / "assignment_event_learned_route.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    H.assert_true("compute_returns" not in calls, "stock critic returns fallback")
    H.assert_true("collect" not in calls and "get_actions" not in calls, "stock full-row actor sampling fallback")
    H.assert_true("train" not in calls, "stock full-row HAPPO train fallback")
    forbidden = ("legacy_assignment", "heuristic_action", "fallback_action", "post_reset_terminal_rebuild")
    H.assert_true(not any(token in source for token in forbidden), "hidden failure fallback")
    descriptor = H.ROUTE.get_dormant_event_learned_policy_route_descriptor_v2()
    H.assert_true(not descriptor["stock_full_row_actor_sampling"] and not descriptor["stock_compute_returns"] and not descriptor["stock_happo_train"], "descriptor stock fallback")
    return {"stock_actor_sampling": 0, "stock_HAPPO": 0, "stock_compute_returns": 0, "hidden_fallback": 0}


TESTS = (
    ("B2-V1-D1", test_v1_d1_pre_step_stale_p2_open_generation_matrix),
    ("B2-V1-D2", test_v1_d2_pre_step_bad_i2_actor_output_i42_source_matrix),
    ("B2-V1-D3", test_v1_d3_post_step_next_i1_and_next_i2_poison),
    ("B2-V1-D4", test_v1_d4_post_step_dto_and_critic_insertion_poison),
    ("B2-V1-D5", test_v1_d5_actor_partial_commit_is_poisoned_and_cannot_continue),
    ("B2-V1-D6", test_v1_d6_public_readiness_attacks_and_private_only_factory),
    ("B2-V1-D7", test_v1_d7_no_stock_or_hidden_fallback_static_call_record),
)


if __name__ == "__main__":
    raise SystemExit(H.run_tests(suite="assignment_phase_b2_v1_d_failure_readiness_gate_pure", tests=TESTS))
