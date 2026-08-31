"""B2-V1-A static authority and multi-scale fixed-cardinality gate."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_v1_event_route_helpers as H  # noqa: E402


REPO_HASHES = {
    "assignment_event_profile_schema_contract_v2.py": "9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955",
    "assignment_event_policy_evidence.py": "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
    "assignment_event_policy_decision.py": "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
    "assignment_event_actor_collection.py": "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
    "assignment_event_happo_policy_math.py": "3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4",
    "assignment_event_terminal_critic_sidecar.py": "655ecafeaf6d08eb856725023572438976a381fb7ffe0a5cadf16d61a4bfe49f",
    "assignment_event_terminal_learner_transport.py": "e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4",
    "assignment_event_critic_buffer.py": "682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f",
    "assignment_event_gae_returns.py": "7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379",
    "assignment_event_learned_route.py": "b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b",
    "assignment_event_runtime_facade.py": "036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478",
    "assignment_event_proposal_adapter.py": "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    "assignment_lifecycle_transaction_runtime.py": "2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de",
    "assignment_lifecycle_authority_runtime.py": "ca7774808fb8901dbc209f61a8915713106a5dc9da739d1bce30c8952a21e10e",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
HARL_HASHES = {
    "runners/on_policy_base_runner.py": "5d99e0fa6f70f0bbff4d5b0f00f45faa3e4b543e1531f5259900480f1842044f",
    "runners/on_policy_ha_runner.py": "14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a",
    "common/buffers/on_policy_actor_buffer.py": "a7352b59d8fa28b96e28e3021ddeaa9f8da5944c686651b1c04b0ec26c96f8cc",
    "common/buffers/on_policy_critic_buffer_ep.py": "0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f",
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}
DIRECT_MARL = H.REPO_ROOT / "source" / "isaaclab" / "isaaclab" / "envs" / "direct_marl_env.py"
DIRECT_MARL_HASH = "7f7714a6f32e24ce34ef184cb9eed87cc36d4db0744c44a816ce3da9cc505f31"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v1_a1_authority_and_no_duplicate_math_static() -> dict[str, object]:
    route_path = H.SCAN_SOURCE / "assignment_event_learned_route.py"
    source = route_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    required = {
        "collect_event_policy_proposals_v2",
        "train_event_policy_happo_sequence_v2",
        "attach_event_terminal_infos_to_harl_step_v2",
        "capture_event_learner_transition_expectation_v2",
        "EventOnPolicyCriticBufferEPV2",
    }
    H.assert_true(required.issubset(imported), f"reviewed seams missing: {required - imported}")
    attrs = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    H.assert_true("compute_event_returns" in attrs and "compute_returns" not in attrs, "return authority duplicated/fallback")
    H.assert_true("backward" not in attrs, "optimizer math entered composition")
    H.assert_true("ratio_full =" not in source and "delta_t =" not in source, "I3b/I5b math duplicated")
    H.assert_true("ownership" not in {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}, "second ownership authority")
    return {"I1_I6_seams": len(required), "duplicate_math": 0, "second_ownership_authority": 0}


def test_v1_a2_public_import_registry_and_default_off_isolation() -> dict[str, object]:
    references = []
    for path in H.SCAN_SOURCE.glob("*.py"):
        if path.name == "assignment_event_learned_route.py":
            continue
        if "assignment_event_learned_route" in path.read_text(encoding="utf-8"):
            references.append(path.name)
    H.assert_true(references == [], f"dormant route wired into production: {references}")
    H.assert_true(H.ROUTE.__all__ == (), "private module exported")
    descriptor = H.ROUTE.get_dormant_event_learned_policy_route_descriptor_v2()
    H.assert_true(descriptor["route"] == "private_test_only_dormant", "private route descriptor")
    H.assert_true(descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R", "readiness fence opened")
    default_result = H.BASE.test_t20_structural_owned_and_default_off_isolation()
    H.assert_true(default_result["event_objects"] == 0, "event object leaked to default profiles")
    return {"production_route_references": 0, "private_exports": 0, "default_profiles": 4}


def _check_contract(harness: H.RouteHarness, *, require_full: bool) -> dict[str, object]:
    harness.route.reset()
    bundle = harness.route.current_decision_bundle
    E, M, N, T = harness.E, harness.M, harness.N, harness.T
    actor = bundle.evidence_snapshot.actor_obs
    share = bundle.evidence_snapshot.runner_share_obs
    avail = bundle.runner_available_actions
    H.assert_true(tuple(actor.shape[:2]) == (E, M), "actor fixed scale")
    H.assert_true(tuple(share.shape[:2]) == (E, M), "critic fixed scale")
    H.assert_true(tuple(avail.shape) == (E, M, N + 1), "available fixed scale")
    for tensor in (actor, share, avail, bundle.decision_valid_mask):
        H.assert_true(tensor.device.type == "cpu" and not tensor.requires_grad, "CPU/no-grad contract")
    first = harness.route.collect_step()
    H.assert_true(first.transition_slot == 0 and harness.buffer.step == 1, "transition/storage insert")
    H.assert_true(len(first.harl_step_result) == 6, "six-element contract")
    if require_full:
        for _ in range(1, T):
            harness.route.collect_step()
        rollout = harness.route.finish_rollout(agent_order=tuple(range(M)))
        H.assert_true(tuple(rollout.advantages.shape) == (T, E, 1), "full rollout returns")
        H.assert_true(harness.buffer.step == 0, "rollover")
    return {"E": E, "M": M, "N": N, "T": T, "full_rollout": require_full}


def test_v1_a3_scale_a_reset_transition_storage() -> dict[str, object]:
    return _check_contract(H.lifecycle_harness(), require_full=False)


def test_v1_a4_scale_b_full_rollout_returns_rollover() -> dict[str, object]:
    return _check_contract(H.scale_harness(), require_full=True)


def test_v1_a5_shape_dtype_device_fail_closed() -> dict[str, object]:
    problem = H.I4._problem(E=2, M=2, N=4)
    scale = H.I4._scale(M=2, N=4)
    failures = 0
    wrong_shape = dict(problem)
    wrong_shape["cost_matrix"] = torch.zeros((2, 2, 3), dtype=torch.float32)
    H.expect_failure(
        lambda: H.EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=wrong_shape,
            episode_progress_steps=torch.zeros((2,), dtype=torch.int64),
            scale_contract=scale,
        ),
        "physical_tensor_contract",
    )
    failures += 1
    wrong_dtype = dict(problem)
    wrong_dtype["feasible_mask"] = problem["feasible_mask"].to(torch.int64)
    H.expect_failure(
        lambda: H.EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=wrong_dtype,
            episode_progress_steps=torch.zeros((2,), dtype=torch.int64),
            scale_contract=scale,
        ),
        "physical_tensor_contract",
    )
    failures += 1
    wrong_device = dict(problem)
    wrong_device["scanner_pos"] = torch.empty((2, 2, 3), dtype=torch.float32, device="meta")
    H.expect_failure(
        lambda: H.EVIDENCE.capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=wrong_device,
            episode_progress_steps=torch.zeros((2,), dtype=torch.int64),
            scale_contract=scale,
        ),
        "physical_tensor_contract",
    )
    failures += 1
    return {"CPU_accept": True, "shape_dtype_device_rejections": failures, "CUDA_run": False}


def test_v1_a6_protected_repo_and_installed_harl_hashes() -> dict[str, object]:
    for name, expected in REPO_HASHES.items():
        H.assert_true(sha256(H.SCAN_SOURCE / name) == expected, f"reviewed repo hash changed: {name}")
    for name, expected in HARL_HASHES.items():
        H.assert_true(sha256(HARL_ROOT / name) == expected, f"installed HARL hash changed: {name}")
    H.assert_true(sha256(DIRECT_MARL) == DIRECT_MARL_HASH, "DirectMARLEnv hash changed")
    return {"reviewed_repo": len(REPO_HASHES), "installed_harl": len(HARL_HASHES), "DirectMARLEnv": 1}


TESTS = (
    ("B2-V1-A1", test_v1_a1_authority_and_no_duplicate_math_static),
    ("B2-V1-A2", test_v1_a2_public_import_registry_and_default_off_isolation),
    ("B2-V1-A3", test_v1_a3_scale_a_reset_transition_storage),
    ("B2-V1-A4", test_v1_a4_scale_b_full_rollout_returns_rollover),
    ("B2-V1-A5", test_v1_a5_shape_dtype_device_fail_closed),
    ("B2-V1-A6", test_v1_a6_protected_repo_and_installed_harl_hashes),
)


if __name__ == "__main__":
    raise SystemExit(H.run_tests(suite="assignment_phase_b2_v1_a_static_scale_contract_gate_pure", tests=TESTS))
