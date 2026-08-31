"""Phase A6 pure/static/manifest default-off identity closeout suite.

The suite deliberately does not launch Isaac Lab, construct a policy, execute
an actor update, deserialize weights, or run training/playback/evaluation.
Runtime-only rows are retained as explicit deferred evidence.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib
import importlib.util
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
import textwrap
import types
import zlib
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping

import gymnasium
import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
HARL_ROOT = Path(sys.executable).resolve().parent / "Lib" / "site-packages" / "harl"

BYTE_EXACT = "BYTE/TENSOR-EXACT"
STATIC_EXACT = "STATIC-ROUTE-EXACT"
MANIFEST_EXACT = "MANIFEST-EXACT"
NOT_EXECUTABLE = "NOT-EXECUTABLE-IN-PHASE-A"
DEFERRED = "DEFERRED-RUNTIME-IDENTITY-EVIDENCE"
EVIDENCE_VOCABULARY = (
    BYTE_EXACT,
    STATIC_EXACT,
    MANIFEST_EXACT,
    NOT_EXECUTABLE,
    DEFERRED,
)
COHORTS = ("D0_ABSENT", "D1_PRE_RESOLVED_VALID", "SCENARIO_CORRECTION")

EXPECTED_MASTER_SURFACES = (
    "resolved runtime route",
    "observation",
    "shared observation",
    "action dimension / action space",
    "action mask",
    "sampled-action route",
    "log-prob route",
    "proposal",
    "effective assignment",
    "reward",
    "GAE / return input",
    "ValueNorm input",
    "sequential factor",
    "RNG path",
    "minibatch order",
    "logger output",
    "file side effects",
    "checkpoint V2",
    "playback route",
)

SURFACE_EVIDENCE: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("resolved runtime route", (STATIC_EXACT, DEFERRED)),
    ("observation", (BYTE_EXACT, DEFERRED)),
    ("shared observation", (BYTE_EXACT, DEFERRED)),
    ("action dimension / action space", (BYTE_EXACT, DEFERRED)),
    ("action mask", (BYTE_EXACT, DEFERRED)),
    ("sampled-action route", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("log-prob route", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("proposal", (BYTE_EXACT, DEFERRED)),
    ("effective assignment", (BYTE_EXACT, DEFERRED)),
    ("reward", (BYTE_EXACT, DEFERRED)),
    ("GAE / return input", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("ValueNorm input", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("sequential factor", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("RNG path", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("minibatch order", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
    ("logger output", (BYTE_EXACT, DEFERRED)),
    ("file side effects", (BYTE_EXACT, STATIC_EXACT, DEFERRED)),
    ("checkpoint V2", (MANIFEST_EXACT,)),
    ("playback route", (STATIC_EXACT, NOT_EXECUTABLE, DEFERRED)),
)
EXPECTED_LABEL_COUNTS = {
    BYTE_EXACT: 9,
    STATIC_EXACT: 10,
    MANIFEST_EXACT: 1,
    NOT_EXECUTABLE: 8,
    DEFERRED: 18,
}

DEFERRED_RUNTIME_ROWS: tuple[tuple[str, str, str], ...] = (
    ("real Isaac startup identity", "B0/E", DEFERRED),
    ("real env observation", "B/C", DEFERRED),
    ("real env shared observation", "B/C", DEFERRED),
    ("real env action mask", "B/C", DEFERRED),
    ("sampled action trajectory", "C", DEFERRED),
    ("runtime log-prob", "C", DEFERRED),
    ("rollout proposal/effective stream", "B/C", DEFERRED),
    ("base env reward identity", "D", DEFERRED),
    ("GAE execution", "C/D", DEFERRED),
    ("ValueNorm execution", "C/D", DEFERRED),
    ("sequential factor execution", "C", DEFERRED),
    ("rollout RNG sequence", "C/E", DEFERRED),
    ("optimizer/minibatch execution order", "C/E", DEFERRED),
    ("real logger output", "B0/B/C/D", DEFERRED),
    ("real filesystem side effects", "B0/B/C/D/E", DEFERRED),
    ("actual playback", "E", DEFERRED),
    ("runtime same-object propagation", "B0", DEFERRED),
    ("pre-reset lifecycle authority", "B0", DEFERRED),
    ("event scheduler/local-set/cost/Top-K", "B", DEFERRED),
    ("event DVM/buffer/trainer", "B/C", DEFERRED),
    ("team reward runtime", "D", DEFERRED),
    ("diagnostic runtime producers", "B0/B/C/D", DEFERRED),
    ("checkpoint-ready V3/state-dict inventory", "later checkpoint gate", DEFERRED),
)

V2_SOURCE_SHA256 = "8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0"
V2_LEGACY_LENGTH = 5509
V2_LEGACY_SHA256 = "1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f"
V2_CONTRACT_C_LENGTH = 7234
V2_CONTRACT_C_SHA256 = "88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398"
V3_LENGTH = 67794
V3_SHA256 = "03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a"

# Secondary reproducibility fixtures only.  Primary identity evidence below is
# an independent tensor assembly followed by exact torch.equal comparisons.
EXPECTED_TENSOR_DIGESTS = {
    "legacy_actor": "cdfe63ac39f4ddf2077210233d7bf691edc241fec3bacc3596591e5a54a911c1",
    "legacy_shared": "6146fe0f2896761c8dc346b5bbc4186674c4a2304bd1e0e95434b7e6a33a23ea",
    "legacy_mask": "4b26f6b5d1bacf75b50941062f6173376d9b34d27a80c073597fe2b5d8b7d88c",
    "contract_c_actor": "f00d28070f3b36a236efea81f104048a0d501f367d1b78c73d24badfbb5895e5",
    "contract_c_shared": "bfc02838cee39bc3d4acf8491334fc70f9fa1ad7d45a9ad06af4289e75967d00",
    "contract_c_mask": "8119192e6c2cd590b206e1c3d8bb811e4eb42318b1a1922cab412b7d707f1eb8",
}

PRODUCTION_SHA256 = {
    "assignment_profile_contract.py": "ece4a58c1636ea3f710775eaac25e12df4097972ef57ec0d15cefec5e6702500",
    "scenario_config.py": "36f80d920fdce818979fe1ad1e6f32e322d925c1984141f675826edf6ed1fc01",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_lifecycle_training_contract.py": "066b120d6451d6f50b8b3c145b988c1f97d5f9b6048493420c1b20e0b0cb1c47",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    "assignment_lifecycle_transition_contract.py": "1bf66c6c6b51adb8a44292910c1b11dfb1e43f31d711d3320285f3df587b0cc9",
    "assignment_event_contract.py": "22194ad8671dd299bd7acd0b837325b4c85f50b8636cb285ff4f76879467086a",
    "assignment_mrta_contract.py": "73881d20903873ddaaf7b6b6636d008771c030f739d3d2cc8ebb32b79bd1e17c",
    "assignment_team_reward_contract.py": "21c27d60ade6008fdeaa77e726bfdb7930fa1acf84a02c9a9457bab6335ca97c",
    "assignment_event_gated_diagnostics_contract.py": "d013044170914df3b62bbb09dfbce34f29497ab644b7fb47225cbc4496e19a0a",
    "assignment_event_profile_schema_contract.py": "04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef",
    "assignment_checkpoint_contract_v3.py": "7995432b63c5e0befd8eae1d6f793889f681b07f61c53fadeba103932c787d16",
    "assignment_checkpoint_semantic_dispatch.py": "6db5855f155d2647df4474a64659a3bcf1a082f42725c01a630e7bf4d09fdbfc",
    "assignment_checkpoint_entry_guard.py": "335f1a485a3bc65e028ab11cf4ca80ad350120cf07fd404dc53b6ac01a96c983",
    "assignment_checkpoint_save.py": "f4383a7c51f03b2695e3122b49ee934f97214e76a9645f8b70274716ee89fc5c",
    "assignment_checkpoint_load.py": "87a936b7ad56294706c0c29992c29793d1bff505a0f3244eff759fb7f2257e9f",
    "assignment_training_run_audit.py": "3aa0bf1d81a36af3b493a3932c9c454249ac7185adc98ed7714f7f5ad90765db",
    "assignment_checkpoint_contract.py": V2_SOURCE_SHA256,
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    "assignment_state.py": "a7f83351ed3e360c0a077a66faeec8087cff89ee47123ead4ec045d3602c14c5",
    "assignment_lifecycle_observation.py": "af20d2862242ece6c49cadbd54651153590dc7831a76f47e73a722925b3e03d7",
    "assignment_lifecycle_resolver.py": "7f64183c638697f16efa45769978127c7e3575599e87cfa76a5ba26f20eabadb",
    "assignment_lifecycle_resolver_runtime.py": "03483727573974bb57f96309d9d8a1ec446d87580915747bc57014bb4cc7f754",
    "assignment_lifecycle_diagnostics.py": "16f9819d5df8b9182db1c38a50dd0a3878b00791b84317fa997d279e59b6d192",
    "assignment_playback_attribution_diagnostics.py": "2f4a0e8084eedb3d8150a417be63f7c49386282e3221015febecd26891908128",
    "assignment_initial_condition.py": "a8579b6a1b272df727eacb05afaeef0bc77bba78ed6781e9056f3c0930fb3657",
    "agents/harl_happo_cfg.yaml": "e84b2ee54f5ebd6d51fdf1a799a812bca4039b8cbef17b7eba3ef06337da44b5",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tensor_digest(tensors: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(tensors):
        value = tensors[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(value.dtype).encode("ascii") + b"\0")
        digest.update(json.dumps(list(value.shape), separators=(",", ":")).encode("ascii") + b"\0")
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _install_namespace() -> None:
    roots = (
        ("isaaclab_tasks", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"),
        ("isaaclab_tasks.direct", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct"),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in roots:
        existing = sys.modules.get(name)
        if existing is None:
            module = types.ModuleType(name)
            module.__package__ = name
            module.__path__ = [str(path)]  # type: ignore[attr-defined]
            sys.modules[name] = module
        else:
            paths = tuple(Path(item).resolve() for item in getattr(existing, "__path__", ()))
            _assert(path.resolve() in paths, f"namespace {name} has unexpected path")


def _canonical(basename: str) -> Any:
    _install_namespace()
    return importlib.import_module(f"{PACKAGE}.{basename}")


def _load_scenario() -> Any:
    key = "phase_a6_scenario_config_harness"
    module = sys.modules.get(key)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(key, SCAN_SOURCE / "scenario_config.py")
    _assert(spec is not None and spec.loader is not None, "scenario spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    inserted = False
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        if str(SCAN_SOURCE) not in sys.path:
            sys.path.insert(0, str(SCAN_SOURCE))
            inserted = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(key, None)
        raise
    finally:
        if inserted:
            sys.path.remove(str(SCAN_SOURCE))
        sys.dont_write_bytecode = previous
    return module


class FakeAssignmentEnv:
    """Synthetic primitive source; intentionally has no reset/step methods."""

    def __init__(self, profile: str | None) -> None:
        self.num_envs = 2
        self.num_viewpoints = 50
        self.device = torch.device("cpu")
        self.max_episode_length = 300
        self.possible_agents = ("agent_0", "agent_1", "agent_2")
        self.agents = list(self.possible_agents)
        self.cfg = SimpleNamespace(
            assignment_lifecycle_resolver_enabled=profile == "diagnostics_hidden_state",
            assignment_lifecycle_resolver_strict_proposals=True,
            assignment_lifecycle_resolver_log_diagnostics=False,
            assignment_lifecycle_resolver_output_dir=None,
            assignment_cooldown_enabled=profile == "lifecycle_contract_c",
            assignment_cooldown_trigger_mode="budget" if profile == "lifecycle_contract_c" else "streak",
            assignment_cooldown_apply_to_action_mask=profile != "lifecycle_contract_c",
            assignment_cooldown_duration_steps=20,
            assignment_redirect_guardrail_enabled=False,
            assignment_failed_pair_memory_enabled=False,
            max_base_xy_step=(0.08, 0.10, 0.06),
            scene=SimpleNamespace(env_spacing=1.0),
        )
        if profile is not None:
            self.cfg.assignment_lifecycle_profile = profile
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-float("inf"), float("inf"), shape=(96,), dtype=float)
            for agent in self.possible_agents
        }
        self._raw = {
            agent: torch.arange(192, dtype=torch.float32).reshape(2, 96) + float(index * 1000)
            for index, agent in enumerate(self.possible_agents)
        }
        env_offsets = torch.arange(2, dtype=torch.float32).view(2, 1, 1)
        task_ids = torch.arange(50, dtype=torch.float32).view(1, 50, 1)
        viewpoint_pos = torch.cat(
            (task_ids.repeat(2, 1, 1) / 100.0, env_offsets.repeat(1, 50, 1), torch.ones(2, 50, 1)),
            dim=-1,
        )
        viewpoint_quat = torch.zeros(2, 50, 4, dtype=torch.float32)
        viewpoint_quat[..., 0] = 1.0
        available = torch.ones(2, 3, 50, dtype=torch.bool)
        available[0, 1, 7] = False
        feasible = torch.ones_like(available)
        self._problem = {
            "num_envs": 2,
            "num_agents": 3,
            "num_viewpoints": 50,
            "viewpoint_pos": viewpoint_pos,
            "viewpoint_quat": viewpoint_quat,
            "scanner_pos": torch.zeros(2, 3, 3),
            "viewpoints_covered": torch.zeros(2, 50, dtype=torch.bool),
            "available_mask": available,
            "feasible_mask": feasible,
            "static_geometric_feasible_mask": feasible.clone(),
            "cost_matrix": torch.arange(300, dtype=torch.float32).reshape(2, 3, 50),
        }

    @property
    def unwrapped(self) -> "FakeAssignmentEnv":
        return self

    def raw_observations(self) -> dict[str, torch.Tensor]:
        return {key: value.clone() for key, value in self._raw.items()}

    def get_assignment_problem(self) -> dict[str, Any]:
        return {key: value.clone() if isinstance(value, torch.Tensor) else value for key, value in self._problem.items()}


def _make_wrapper(profile: str | None, *, pre_resolved: bool = False) -> Any:
    wrapper_module = _canonical("assignment_harl_wrapper")
    kwargs: dict[str, Any] = {}
    if pre_resolved:
        _assert(profile is not None, "pre-resolved fixture requires an explicit profile")
        profile_module = _canonical("assignment_profile_contract")
        origin = profile_module.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
        kwargs = {
            "resolved_assignment_profile": profile_module.resolve_assignment_profile(profile, origin),
            "profile_resolution_origin": origin,
            "assignment_profile_entrypoint": "phase_a6_pre_resolved_fixture",
        }
    return wrapper_module.AssignmentHarlWrapper(FakeAssignmentEnv(profile), **kwargs)


def _wrapper_fixture(profile: str | None) -> tuple[Any, dict[str, torch.Tensor], torch.Tensor, dict[str, Any]]:
    wrapper = _make_wrapper(profile)
    problem = wrapper.unwrapped.get_assignment_problem()
    if profile == "lifecycle_contract_c":
        # Explicit frozen lifecycle primitive fixture (numeric pair-state
        # values are the accepted Contract-C constants: active=1, failed=3,
        # released=4).  This makes lifecycle field ordering observable.
        resolver = wrapper._assignment_lifecycle_resolver_runtime.resolver
        resolver.active_target_id[0, 1] = 7
        resolver.task_owner_robot_id[0, 7] = 1
        resolver.pair_state[0, 1, 7] = 1
        resolver.pair_state[0, 0, 9] = 4
        resolver.pair_state[1, 2, 11] = 3
        wrapper._budget_attempt_target[0, 1] = 7
        wrapper._budget_attempt_steps[0, 1] = 3
        wrapper._budget_attempt_budget_steps[0, 1] = 10
    wrapper._capture_lifecycle_decision_snapshot(problem=problem)
    observations = wrapper._augment_assignment_observations(wrapper.unwrapped.raw_observations(), problem=problem)
    shared = wrapper._build_shared_obs(observations)
    mask = wrapper._build_available_actions(problem)
    return wrapper, observations, shared, problem | {"available_actions": mask}


def _independent_actor_oracle(env: FakeAssignmentEnv, *, lifecycle: bool) -> dict[str, torch.Tensor]:
    """Assemble the frozen actor schema without calling production builders."""

    problem = env.get_assignment_problem()
    dtype = torch.float32
    covered = problem["viewpoints_covered"].to(dtype=torch.bool)
    available = problem["available_mask"].to(dtype=torch.bool)
    feasible = problem["feasible_mask"].to(dtype=torch.bool)
    static = problem["static_geometric_feasible_mask"].to(dtype=torch.bool)
    viewpoint_pos = problem["viewpoint_pos"].to(dtype=dtype)
    viewpoint_quat = problem["viewpoint_quat"].to(dtype=dtype)
    cost = problem["cost_matrix"].to(dtype=dtype)
    scanner_pos = problem["scanner_pos"].to(dtype=dtype)
    expected: dict[str, torch.Tensor] = {}
    for agent_index, agent in enumerate(env.possible_agents):
        row_parts = [
            viewpoint_pos - scanner_pos[:, agent_index, :].unsqueeze(1),
            viewpoint_quat,
            covered.to(dtype=dtype).unsqueeze(-1),
            available[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
            feasible[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
            static[:, agent_index, :].to(dtype=dtype).unsqueeze(-1),
            cost[:, agent_index, :].unsqueeze(-1),
            torch.zeros(2, 50, 1, dtype=dtype),
            torch.ones(2, 50, 1, dtype=dtype),
        ]
        if lifecycle:
            lifecycle_fields = torch.zeros(2, 3, 50, 3, dtype=dtype)
            lifecycle_fields[0, 1, 7, 0] = 1.0  # robot 1 self-active target
            lifecycle_fields[0, 0, 7, 1] = 1.0  # task owned by teammate
            lifecycle_fields[0, 2, 7, 1] = 1.0
            lifecycle_fields[0, 0, 9, 2] = 1.0  # released self pair
            lifecycle_fields[1, 2, 11, 2] = 1.0  # failed self pair
            row_parts.append(lifecycle_fields[:, agent_index, :, :])
        task_rows = torch.cat(tuple(row_parts), dim=-1).reshape(2, -1)
        noop_context = torch.tensor(
            [[1.0, 1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 0.0, 1.0, 0.0]],
            dtype=dtype,
        )
        previous_one_hot = torch.zeros(2, 51, dtype=dtype)
        previous_one_hot[:, 50] = 1.0
        dynamic = torch.tensor(
            [[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]] * 2,
            dtype=dtype,
        )
        covered_vector = torch.zeros(2, 50, dtype=dtype)
        extension = torch.cat(
            (task_rows, noop_context, previous_one_hot, dynamic, covered_vector),
            dim=-1,
        )
        expected[agent] = torch.cat((env.raw_observations()[agent], extension), dim=-1)
    return expected


def _independent_shared_oracle(
    actor_oracle: Mapping[str, torch.Tensor],
    *,
    lifecycle: bool,
) -> torch.Tensor:
    shared = torch.cat(tuple(actor_oracle[name] for name in ("agent_0", "agent_1", "agent_2")), dim=-1)
    if lifecycle:
        # Frozen robot-major [progress, step_fraction] tail: env 0 robot 1
        # has 3/10 progress and 1/10 step fraction; all other robots are idle.
        budget = torch.zeros(2, 6, dtype=torch.float32)
        budget[0, 2:4] = torch.tensor([0.3, 0.1])
        shared = torch.cat((shared, budget), dim=-1)
    return torch.stack((shared, shared, shared), dim=1)


def _independent_mask_oracle(env: FakeAssignmentEnv, *, lifecycle: bool) -> torch.Tensor:
    problem = env.get_assignment_problem()
    available = problem["available_mask"].to(dtype=torch.bool)
    if lifecycle:
        task_valid = torch.ones(2, 50, dtype=torch.bool)
        uncovered = ~problem["viewpoints_covered"].to(dtype=torch.bool)
        base_target = (
            task_valid.unsqueeze(1)
            & available
            & problem["feasible_mask"].to(dtype=torch.bool)
            & uncovered.unsqueeze(1)
        )
        task_owned_by_teammate = torch.zeros_like(base_target)
        task_owned_by_teammate[0, 0, 7] = True
        task_owned_by_teammate[0, 2, 7] = True
        failed_or_released = torch.zeros_like(base_target)
        failed_or_released[0, 0, 9] = True
        failed_or_released[1, 2, 11] = True
        active_robot = torch.zeros(2, 3, dtype=torch.bool)
        active_robot[0, 1] = True
        self_active_target = torch.zeros_like(base_target)
        self_active_target[0, 1, 7] = True
        idle_target = base_target & ~task_owned_by_teammate & ~failed_or_released
        target = torch.where(active_robot.unsqueeze(-1), self_active_target, idle_target)
    else:
        target = available
    return torch.cat((target.to(dtype=torch.float32), torch.ones(2, 3, 1)), dim=-1)


def test_01_evidence_vocabulary_and_cohorts() -> dict[str, Any]:
    _assert(EVIDENCE_VOCABULARY == (
        "BYTE/TENSOR-EXACT", "STATIC-ROUTE-EXACT", "MANIFEST-EXACT",
        "NOT-EXECUTABLE-IN-PHASE-A", "DEFERRED-RUNTIME-IDENTITY-EVIDENCE"), "evidence vocabulary")
    _assert(COHORTS == ("D0_ABSENT", "D1_PRE_RESOLVED_VALID", "SCENARIO_CORRECTION"), "cohorts")
    actual_surfaces = tuple(name for name, _ in SURFACE_EVIDENCE)
    _assert(actual_surfaces == EXPECTED_MASTER_SURFACES, f"exact master surfaces {actual_surfaces}")
    _assert(len(actual_surfaces) == 19, "surface inventory length")
    _assert(len(set(actual_surfaces)) == 19, "surface inventory duplicate")
    counts = Counter(label for _, labels in SURFACE_EVIDENCE for label in labels)
    _assert(dict(counts) == EXPECTED_LABEL_COUNTS, f"label counts {counts}")
    return {"surfaces": 19, "label_counts": dict(counts)}


def test_02_d0_absent_profile_identity() -> dict[str, Any]:
    scenario = _load_scenario()
    config = {"scenario_name": "absent-profile"}
    before = json.dumps(config, sort_keys=True)
    actual = scenario.resolve_assignment_lifecycle_profile_declaration(config)
    _assert(actual == (None, "ABSENT", ()), f"D0 declaration {actual}")
    defaults = scenario.smoke_defaults_from_config(config)
    _assert("assignment_lifecycle_profile" not in defaults, "D0 injected profile")
    _assert(json.dumps(config, sort_keys=True) == before, "D0 mutated config")
    profile = _canonical("assignment_profile_contract")
    resolved = profile.resolve_assignment_profile("legacy", profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
    mapping = profile.resolved_assignment_profile_to_mapping(resolved)
    _assert(mapping["profile_name"] == "legacy", "D0 legacy")
    _assert(mapping["runtime_route"] == "existing_legacy_assignment_harl_v1", "D0 route")
    return {"cohort": "D0_ABSENT", "route": mapping["runtime_route"], "config_exact": True}


def test_03_valid_d1_existing_profile_mappings() -> dict[str, Any]:
    profile = _canonical("assignment_profile_contract")
    origin = profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    expected = {
        "legacy": ("existing_legacy_assignment_harl_v1", False, False, False, "assignment_checkpoint_contract_v2"),
        "lifecycle_contract_c": ("existing_lifecycle_contract_c_assignment_harl_v1", True, True, True, "assignment_checkpoint_contract_v2"),
    }
    actual: dict[str, Any] = {}
    for name, values in expected.items():
        resolved = profile.resolve_assignment_profile(name, origin)
        mapping = profile.resolved_assignment_profile_to_mapping(resolved)
        row = (mapping["runtime_route"], mapping["resolver_enabled"], mapping["lifecycle_observation_enabled"], mapping["lifecycle_mask_enabled"], mapping["checkpoint_family"])
        _assert(row == values, f"D1 {name}: {row}")
        actual[name] = row
    return {"cohort": "D1_PRE_RESOLVED_VALID", "mappings": actual}


def test_04_scenario_correction_matrix() -> dict[str, Any]:
    scenario = _load_scenario()
    resolve = scenario.resolve_assignment_lifecycle_profile_declaration
    top = "assignment_lifecycle_profile"
    nested = "assignment_lifecycle.profile"
    valid = (
        ("top-level only", {top: " lifecycle_ablation "}, ("lifecycle_ablation", "TOP_LEVEL", ((top, " lifecycle_ablation ", "lifecycle_ablation"),))),
        ("nested only", {"assignment_lifecycle": {"profile": "event_gated_local_mrta"}}, ("event_gated_local_mrta", "NESTED", ((nested, "event_gated_local_mrta", "event_gated_local_mrta"),))),
        ("top+nested canonical equal", {top: " lifecycle_contract_c", "assignment_lifecycle": {"profile": "lifecycle_contract_c "}}, ("lifecycle_contract_c", "TOP_LEVEL_AND_NESTED", ((top, " lifecycle_contract_c", "lifecycle_contract_c"), (nested, "lifecycle_contract_c ", "lifecycle_contract_c")))),
    )
    for label, config, expected in valid:
        _assert(resolve(config) == expected, label)
    invalid = (
        ("top+nested conflict", {top: "legacy", "assignment_lifecycle": {"profile": "lifecycle_ablation"}}),
        ("unknown", {top: "unknown"}),
        ("empty", {"assignment_lifecycle": {"profile": " "}}),
    )
    for label, config in invalid:
        try:
            resolve(config)
        except ValueError:
            pass
        else:
            raise AssertionError(f"scenario correction {label} did not fail")
    return {"cohort": "SCENARIO_CORRECTION", "rows": 6, "classification": "intentional_expected_change_not_identity"}


def _obs_evidence(profile_name: str, prefix: str, actor_dim: int, shared_dim: int) -> dict[str, Any]:
    wrapper, observations, shared, problem = _wrapper_fixture(profile_name)
    mask = problem["available_actions"]
    lifecycle = profile_name == "lifecycle_contract_c"
    expected_observations = _independent_actor_oracle(wrapper.unwrapped, lifecycle=lifecycle)
    expected_shared = _independent_shared_oracle(expected_observations, lifecycle=lifecycle)
    expected_mask = _independent_mask_oracle(wrapper.unwrapped, lifecycle=lifecycle)
    _assert(tuple(observations) == ("agent_0", "agent_1", "agent_2"), f"{prefix} order")
    for agent in ("agent_0", "agent_1", "agent_2"):
        actual_actor = observations[agent]
        expected_actor = expected_observations[agent]
        _assert(tuple(actual_actor.shape) == (2, actor_dim), f"{prefix} {agent} actor shape")
        _assert(actual_actor.dtype == expected_actor.dtype == torch.float32, f"{prefix} {agent} actor dtype")
        _assert(actual_actor.device == expected_actor.device, f"{prefix} {agent} actor device")
        _assert(torch.equal(actual_actor, expected_actor), f"{prefix} {agent} actor content/order")
    _assert(tuple(shared.shape) == (2, 3, shared_dim), f"{prefix} shared shape")
    _assert(shared.dtype == expected_shared.dtype == torch.float32, f"{prefix} shared dtype")
    _assert(shared.device == expected_shared.device, f"{prefix} shared device")
    _assert(torch.equal(shared, expected_shared), f"{prefix} shared content/order")
    _assert(tuple(mask.shape) == (2, 3, 51), f"{prefix} mask shape")
    _assert(mask.dtype == expected_mask.dtype == torch.float32, f"{prefix} mask dtype")
    _assert(mask.device == expected_mask.device, f"{prefix} mask device")
    _assert(torch.equal(mask, expected_mask), f"{prefix} every mask entry")
    _assert(all(space.__class__.__name__ == "Discrete" and int(space.n) == 51 for space in wrapper.action_space.values()), f"{prefix} action spaces")
    expected_mask_contract = "legacy_mask_v1" if profile_name == "legacy" else "lifecycle_contract_c_mask_v1"
    _assert(wrapper.assignment_observation_schema_manifest["mask_contract_version"] == expected_mask_contract, f"{prefix} mask route")
    actual = {
        f"{prefix}_actor": _tensor_digest(observations),
        f"{prefix}_shared": _tensor_digest({"shared": shared}),
        f"{prefix}_mask": _tensor_digest({"mask": mask}),
    }
    mismatches = {key: value for key, value in actual.items() if value != EXPECTED_TENSOR_DIGESTS[key]}
    _assert(not mismatches, f"{prefix} secondary tensor digests actual={actual}")
    return {
        "actor_dim": actor_dim,
        "shared_dim": shared_dim,
        "action_dim": 51,
        "mask_contract": expected_mask_contract,
        "primary_oracle": "independent_explicit_tensor_assembly_then_torch_equal",
        "secondary_digests": actual,
    }


def test_05_legacy_observation_shared_action_mask() -> dict[str, Any]:
    return _obs_evidence("legacy", "legacy", 909, 2727)


def test_06_contract_c_observation_shared_action_mask() -> dict[str, Any]:
    return _obs_evidence("lifecycle_contract_c", "contract_c", 1059, 3183)


def test_07_proposal_effective_reward_identity() -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    expected_proposal = torch.tensor([[0, -1, 3], [4, 5, -1]], dtype=torch.long)
    actions = torch.tensor([[[0], [50], [3]], [[4], [5], [50]]], dtype=torch.long)
    expected_base = torch.tensor([[[1.0], [2.0], [3.0]], [[4.0], [5.0], [6.0]]])
    for name in ("legacy", "lifecycle_contract_c"):
        wrapper = _make_wrapper(name)
        problem = wrapper.unwrapped.get_assignment_problem()
        proposal = wrapper.decode_actions(actions, layout="env_agent_action")
        _assert(torch.equal(proposal, expected_proposal), f"{name} proposal")
        if name == "legacy":
            effective = wrapper._assignment_lifecycle_resolver_runtime.resolve_pre_step(
                problem=problem,
                assignment_proposal=proposal,
            ).effective_assignment
            _assert(torch.equal(effective, expected_proposal), "legacy disabled resolver clone")
            effective_evidence = effective
            reported_proposal = proposal
        else:
            # Independent Contract-C arbitration oracle: all robots are idle,
            # duplicate proposals compete by lower cost then robot id.  In the
            # explicit row-major cost fixture robot 0 wins task 5/7 in each env.
            conflict_proposal = torch.tensor([[5, 5, -1], [7, 7, 7]], dtype=torch.long)
            expected_effective = torch.tensor([[5, -1, -1], [7, -1, -1]], dtype=torch.long)
            _assert(wrapper.assignment_lifecycle_profile_config["resolver_enabled"] is True, "Contract-C resolver flag")
            _assert(wrapper.resolved_assignment_profile.profile_name.value == "lifecycle_contract_c", "Contract-C identity")
            effective_evidence = wrapper._assignment_lifecycle_resolver_runtime.resolve_pre_step(
                problem=problem,
                assignment_proposal=conflict_proposal,
            ).effective_assignment
            _assert(torch.equal(effective_evidence, expected_effective), "Contract-C arbitration result")
            _assert(not torch.equal(conflict_proposal, effective_evidence), "Contract-C fixture discriminates clone")
            reported_proposal = conflict_proposal
        reward = wrapper._compute_assignment_reward_decomposition(
            base_reward_tensor=expected_base.clone(),
            assignment=torch.full((2, 3), -1, dtype=torch.long),
            pre_step_problem={"viewpoints_covered": torch.zeros(2, 50, dtype=torch.bool), "cost_matrix": problem["cost_matrix"]},
            post_step_problem={"viewpoints_covered": torch.zeros(2, 50, dtype=torch.bool), "cost_matrix": problem["cost_matrix"]},
        )["final_reward"]
        _assert(torch.equal(reward, expected_base), f"{name} reward")
        evidence[name] = {
            "proposal": reported_proposal.tolist(),
            "effective": effective_evidence.tolist(),
            "proposal_differs_from_effective": not torch.equal(reported_proposal, effective_evidence),
            "reward": reward.tolist(),
        }
    return evidence


def test_08_actor_logprob_gae_valuenorm_factor_static_routes() -> dict[str, Any]:
    base = (HARL_ROOT / "runners" / "on_policy_base_runner.py").read_text(encoding="utf-8")
    ha = (HARL_ROOT / "runners" / "on_policy_ha_runner.py").read_text(encoding="utf-8")
    actor_buffer = (HARL_ROOT / "common" / "buffers" / "on_policy_actor_buffer.py").read_text(encoding="utf-8")
    critic_buffer = (HARL_ROOT / "common" / "buffers" / "on_policy_critic_buffer_ep.py").read_text(encoding="utf-8")
    happo = (HARL_ROOT / "algorithms" / "actors" / "happo.py").read_text(encoding="utf-8")
    required = {
        "sampled_action": "self.actor[agent_id].get_actions(" in base,
        "log_prob": "action_log_prob_collector" in base and ".evaluate_actions(" in ha,
        "gae": "self.critic_buffer.compute_returns(next_value, self.value_normalizer)" in base,
        "valuenorm": "value_normalizer.denormalize" in critic_buffer,
        "factor": ".update_factor(" in ha and "torch.exp(" in ha,
        "minibatch": "feed_forward_generator_actor(" in happo and "torch.randperm" in actor_buffer,
    }
    _assert(all(required.values()), f"installed HARL static route drift {required}")
    return {"routes": required, "evidence": STATIC_EXACT, "execution": NOT_EXECUTABLE}


def _logger_state() -> tuple[Any, ...]:
    return tuple(sorted((name, type(value).__name__, getattr(value, "level", None), getattr(value, "propagate", None), getattr(value, "disabled", None), tuple(id(handler) for handler in getattr(value, "handlers", ()))) for name, value in logging.Logger.manager.loggerDict.items()))


def test_09_rng_minibatch_logger_files_identity() -> dict[str, Any]:
    py_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()
    cwd_before = Path.cwd()
    env_before = dict(os.environ)
    path_before = tuple(sys.path)
    root = logging.getLogger()
    root_before = (tuple(root.handlers), root.level, root.disabled)
    named_before = _logger_state()
    with tempfile.TemporaryDirectory() as directory:
        before = tuple(Path(directory).iterdir())
        profile = _canonical("assignment_profile_contract")
        for name in ("legacy", "lifecycle_contract_c"):
            profile.resolve_assignment_profile(name, profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
        after = tuple(Path(directory).iterdir())
    checks = {
        "python_rng": random.getstate() == py_before,
        "torch_rng": torch.equal(torch.random.get_rng_state(), torch_before),
        "cwd": Path.cwd() == cwd_before,
        "environment": dict(os.environ) == env_before,
        "sys_path": tuple(sys.path) == path_before,
        "root_logger": (tuple(root.handlers), root.level, root.disabled) == root_before,
        "named_loggers": _logger_state() == named_before,
        "files": before == after == (),
    }
    _assert(all(checks.values()), f"side effect drift {checks}")
    return checks


def _v2_frozen_bytes() -> tuple[bytes, bytes]:
    path = REPO_ROOT / "scripts" / "environments" / "test_assignment_checkpoint_semantic_dispatch.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    encoded: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"V2_LEGACY_CANONICAL_B85", "V2_CONTRACT_C_CANONICAL_B85"}:
                value = node.value
                if (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and value.func.attr == "strip"
                    and isinstance(value.func.value, ast.Constant)
                    and isinstance(value.func.value.value, str)
                ):
                    encoded[name] = value.func.value.value.strip()
                else:
                    encoded[name] = ast.literal_eval(value)
    _assert(set(encoded) == {"V2_LEGACY_CANONICAL_B85", "V2_CONTRACT_C_CANONICAL_B85"}, "V2 frozen fixtures")
    return tuple(zlib.decompress(base64.b85decode(encoded[name].strip().encode("ascii"))) for name in ("V2_LEGACY_CANONICAL_B85", "V2_CONTRACT_C_CANONICAL_B85"))  # type: ignore[return-value]


def test_10_v2_manifest_identity() -> dict[str, Any]:
    v2 = _canonical("assignment_checkpoint_contract")
    _assert(_sha(SCAN_SOURCE / "assignment_checkpoint_contract.py") == V2_SOURCE_SHA256, "V2 source")
    legacy, contract_c = _v2_frozen_bytes()
    expected = ((legacy, V2_LEGACY_LENGTH, V2_LEGACY_SHA256), (contract_c, V2_CONTRACT_C_LENGTH, V2_CONTRACT_C_SHA256))
    rows = []
    for payload, length, fingerprint in expected:
        _assert(len(payload) == length and hashlib.sha256(payload).hexdigest() == fingerprint, "V2 frozen bytes")
        mapping = json.loads(payload.decode("utf-8"))
        _assert(v2.canonical_manifest_bytes(mapping) == payload, "V2 canonical mapping")
        _assert(v2.compute_manifest_sha256(mapping) == fingerprint, "V2 production fingerprint")
        rows.append({"bytes": length, "sha256": fingerprint})
    return {"classification": MANIFEST_EXACT, "rows": rows}


def test_11_ablation_and_diagnostics_routes() -> dict[str, Any]:
    profile = _canonical("assignment_profile_contract")
    origin = profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    expected = {
        "lifecycle_ablation": ("existing_lifecycle_ablation_assignment_harl_v1", "existing_blocked", "explicit_ablation", "assignment_checkpoint_contract_v2_explicit_ablation_evaluation"),
        "diagnostics_hidden_state": ("existing_diagnostics_hidden_state_assignment_harl_v1", "existing_blocked", "diagnostics", "none"),
    }
    actual = {}
    for name, row in expected.items():
        mapping = profile.resolved_assignment_profile_to_mapping(profile.resolve_assignment_profile(name, origin))
        found = (mapping["runtime_route"], mapping["training_support"], mapping["playback_support"], mapping["checkpoint_family"])
        _assert(found == row, f"{name} route {found}")
        actual[name] = found
    return actual


def test_wrapper_schema_manifest_profile_name_binding() -> dict[str, Any]:
    """Regression for the A6 NameError and canonical authority binding."""

    expected_profiles = (
        "legacy",
        "lifecycle_contract_c",
        "lifecycle_ablation",
        "diagnostics_hidden_state",
    )
    actual: dict[str, str] = {}
    for profile_name in expected_profiles:
        wrapper = _make_wrapper(profile_name, pre_resolved=True)
        manifest = wrapper.assignment_observation_schema_manifest
        canonical_name = wrapper.resolved_assignment_profile.profile_name.value
        _assert(manifest["profile_name"] == canonical_name == profile_name, f"{profile_name} manifest binding")
        actual[profile_name] = manifest["profile_name"]

    profile = _canonical("assignment_profile_contract")
    try:
        _make_wrapper("event_gated_local_mrta", pre_resolved=True)
    except (profile.PhaseAExecutionNotAuthorizedError, ValueError):
        event_result = "fail_closed_before_existing_wrapper_schema"
    else:
        raise AssertionError("event profile silently entered existing wrapper schema route")
    return {"existing_profiles": actual, "event_profile": event_result}


def test_12_event_phase_a_block_and_v3_identity() -> dict[str, Any]:
    profile = _canonical("assignment_profile_contract")
    origin = profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
    event = profile.resolve_assignment_profile("event_gated_local_mrta", origin)
    mapping = profile.resolved_assignment_profile_to_mapping(event)
    _assert((mapping["runtime_route"], mapping["training_support"], mapping["playback_support"], mapping["runtime_readiness"], mapping["checkpoint_family"]) == ("event_gated_phase_a_interface_only_v1", "phase_a_blocked", "blocked", "interface_only", "assignment_checkpoint_contract_v3"), "event block")
    try:
        profile.require_assignment_profile_runtime_ready(
            event,
            consumer="phase_a6_pure_identity_test",
            entrypoint="standalone_pure_suite",
            barrier="before_any_event_runtime",
        )
    except profile.PhaseAExecutionNotAuthorizedError:
        pass
    else:
        raise AssertionError("event runtime was authorized")
    aggregate = _canonical("assignment_event_profile_schema_contract")
    v3 = _canonical("assignment_checkpoint_contract_v3")
    scale = aggregate.build_event_gated_scale_contract(M=3, N=50, ordered_agent_names=("robot_0", "robot_1", "robot_2"), ordered_task_ids=tuple(range(50)), scene_env_spacing=12.0, sim_dt_seconds=0.01, control_decimation=4, physical_control_step_seconds=0.04, episode_time_limit_seconds=40.01, episode_horizon_steps=1001)
    manifest = v3.build_interface_semantic_descriptor_v3(scale_contract=scale)
    payload = v3.canonical_assignment_checkpoint_manifest_v3_bytes(manifest)
    fingerprint = v3.compute_assignment_checkpoint_manifest_v3_sha256(manifest)
    _assert(len(payload) == V3_LENGTH and fingerprint == V3_SHA256, "V3 golden")
    readiness = manifest.runtime_readiness_contract
    _assert(not readiness.runtime_execution_authorized and not readiness.checkpoint_weight_use_authorized, "V3 readiness")
    return {"profile": mapping["profile_name"], "bytes": len(payload), "sha256": fingerprint, "runtime": "blocked"}


def test_13_playback_static_route() -> dict[str, Any]:
    path = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    _assert(source.count("load_assignment_checkpoint(") == 1, "playback canonical loader count")
    _assert("AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK" in source, "playback purpose")
    _assert("for agent_id, agent_name in enumerate(wrapper.agents):" in source, "all actor loop")
    _assert("torch.load" not in source and "load_state_dict" not in calls, "playback bypass")
    consumers = {
        "assignment_checkpoint_save.py": SCAN_SOURCE / "assignment_checkpoint_save.py",
        "assignment_checkpoint_load.py": SCAN_SOURCE / "assignment_checkpoint_load.py",
        "play_assignment.py": path,
    }
    consumer_counts: dict[str, int] = {}
    for label, consumer_path in consumers.items():
        consumer_tree = ast.parse(consumer_path.read_text(encoding="utf-8"))
        attributes = [node.attr for node in ast.walk(consumer_tree) if isinstance(node, ast.Attribute)]
        count = attributes.count("assignment_observation_schema_manifest")
        _assert(count == 1, f"{label} public schema-manifest consumer count {count}")
        _assert("resolved_assignment_profile" not in attributes, f"{label} added second resolved-profile path")
        consumer_counts[label] = count
    return {
        "loader_calls": 1,
        "purpose": "load_playback",
        "schema_manifest_consumers": consumer_counts,
        "classification": STATIC_EXACT,
        "execution": NOT_EXECUTABLE,
    }


def test_14_deferred_runtime_inventory_consistency() -> dict[str, Any]:
    required = {
        "real Isaac startup identity", "real env observation", "real env shared observation", "real env action mask",
        "sampled action trajectory", "runtime log-prob", "rollout proposal/effective stream", "base env reward identity",
        "GAE execution", "ValueNorm execution", "sequential factor execution", "rollout RNG sequence",
        "optimizer/minibatch execution order", "real logger output", "real filesystem side effects", "actual playback",
        "runtime same-object propagation", "pre-reset lifecycle authority", "event scheduler/local-set/cost/Top-K",
        "event DVM/buffer/trainer", "team reward runtime", "diagnostic runtime producers",
        "checkpoint-ready V3/state-dict inventory",
    }
    _assert(len(DEFERRED_RUNTIME_ROWS) == 23 and {row[0] for row in DEFERRED_RUNTIME_ROWS} == required, "deferred rows")
    _assert(all(row[2] == DEFERRED and "runtime verified" not in row[2].lower() and BYTE_EXACT not in row[2] for row in DEFERRED_RUNTIME_ROWS), "deferred classification")
    return {"rows": len(DEFERRED_RUNTIME_ROWS), "classification": DEFERRED}


def _clean_child() -> dict[str, Any]:
    source = f"""
import importlib.util,json,logging,os,pathlib,random,sys
from types import SimpleNamespace
import torch
test_path=pathlib.Path({str(Path(__file__).resolve())!r})
spec=importlib.util.spec_from_file_location('_phase_a6_clean_child_test',test_path)
module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
profile=module._canonical('assignment_profile_contract')
registry=profile.get_assignment_profile_registry(); registry_id=id(registry); registry_repr=repr(registry)
def named():
 return tuple(sorted((n,type(v).__name__,getattr(v,'level',None),tuple(id(h) for h in getattr(v,'handlers',())),getattr(v,'propagate',None),getattr(v,'disabled',None)) for n,v in logging.Logger.manager.loggerDict.items()))
def files():
 return tuple(sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob('*')))
root_logger=logging.getLogger()
before={{'python_rng':random.getstate(),'torch_rng':torch.random.get_rng_state().clone(),'cwd':os.getcwd(),'environment':dict(os.environ),'sys_path':tuple(sys.path),'root_logger':(root_logger.level,tuple(id(h) for h in root_logger.handlers),root_logger.disabled),'named_loggers':named(),'files':files(),'registry_id':registry_id,'registry_repr':registry_repr}}
origin=profile.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
d0_profile=profile.resolve_assignment_profile('legacy',origin)
legacy_d1=profile.resolve_assignment_profile('legacy',origin)
contract_d1=profile.resolve_assignment_profile('lifecycle_contract_c',origin)
scenario=module._load_scenario()
d0_decl=scenario.resolve_assignment_lifecycle_profile_declaration({{}})
d0_cfg=SimpleNamespace(); scenario.apply_scenario_config_to_env_cfg(d0_cfg,{{}})
legacy_cfg=SimpleNamespace(); scenario.apply_scenario_config_to_env_cfg(legacy_cfg,{{'assignment_lifecycle_profile':'legacy','assignment_lifecycle_resolver_enabled':False}})
contract_args={{'assignment_lifecycle_profile':'lifecycle_contract_c','assignment_cooldown_enabled':True,'assignment_cooldown_trigger_mode':'budget','assignment_cooldown_duration_steps':20,'assignment_cooldown_apply_to_action_mask':False,'assignment_redirect_guardrail_enabled':False,'assignment_failed_pair_memory_enabled':False}}
contract_cfg=SimpleNamespace(); scenario.apply_scenario_config_to_env_cfg(contract_cfg,contract_args)
d0_wrapper=module._make_wrapper(None)
legacy_wrapper=module._make_wrapper('legacy',pre_resolved=True)
contract_wrapper=module._make_wrapper('lifecycle_contract_c',pre_resolved=True)
manifests=(d0_wrapper.assignment_observation_schema_manifest,legacy_wrapper.assignment_observation_schema_manifest,contract_wrapper.assignment_observation_schema_manifest)
after={{'python_rng':random.getstate(),'torch_rng':torch.random.get_rng_state().clone(),'cwd':os.getcwd(),'environment':dict(os.environ),'sys_path':tuple(sys.path),'root_logger':(root_logger.level,tuple(id(h) for h in root_logger.handlers),root_logger.disabled),'named_loggers':named(),'files':files(),'registry_id':id(profile.get_assignment_profile_registry()),'registry_repr':repr(profile.get_assignment_profile_registry())}}
blocked=[]
for name in sorted(sys.modules):
 if name=='isaaclab' or name.startswith('isaaclab.') or name=='omni' or name.startswith('omni.') or name=='harl' or name.startswith('harl.'):
  blocked.append(name)
result={{'python_rng':after['python_rng']==before['python_rng'],'torch_rng':torch.equal(after['torch_rng'],before['torch_rng']),'cwd':after['cwd']==before['cwd'],'environment':after['environment']==before['environment'],'sys_path':after['sys_path']==before['sys_path'],'root_logger':after['root_logger']==before['root_logger'],'named_loggers':after['named_loggers']==before['named_loggers'],'files':after['files']==before['files'],'registry_identity':after['registry_id']==before['registry_id'],'registry_content':after['registry_repr']==before['registry_repr'],'blocked_modules':blocked,'d0':d0_decl==(None,'ABSENT',()) and not hasattr(d0_cfg,'assignment_lifecycle_profile') and d0_profile.profile_name.value=='legacy','legacy_d1':legacy_d1.profile_name.value=='legacy' and legacy_cfg.assignment_lifecycle_profile=='legacy','contract_c_d1':contract_d1.profile_name.value=='lifecycle_contract_c' and contract_cfg.assignment_lifecycle_profile=='lifecycle_contract_c','schema_manifests':[item['profile_name'] for item in manifests]}}
print(json.dumps(result,sort_keys=True,separators=(',',':')))
"""
    with tempfile.TemporaryDirectory() as directory:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", textwrap.dedent(source)],
            cwd=directory,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    _assert(completed.returncode == 0, f"clean child failed {completed.stdout!r} {completed.stderr!r}")
    _assert(completed.stderr == "", f"clean child unexpected stderr {completed.stderr!r}")
    stdout_lines = completed.stdout.splitlines()
    _assert(len(stdout_lines) == 1, f"clean child expected exactly one JSON stdout line {stdout_lines!r}")
    result = json.loads(stdout_lines[0])
    _assert(result.pop("schema_manifests") == ["legacy", "legacy", "lifecycle_contract_c"], "clean child schemas")
    _assert(not result.pop("blocked_modules") and all(result.values()), f"clean child drift {result}")
    return result


def test_15_production_scope_and_clean_child() -> dict[str, Any]:
    hashes = {}
    for relative, expected in PRODUCTION_SHA256.items():
        path = SCAN_SOURCE / relative
        actual = _sha(path)
        _assert(actual == expected, f"A6 production drift {relative}: {actual}")
        hashes[relative] = actual
    yaml_diff = subprocess.run(["git", "diff", "--name-only", "--", "*.yaml", "*.yml"], cwd=REPO_ROOT, text=True, capture_output=True, check=True).stdout.strip()
    _assert(not yaml_diff, f"YAML changed: {yaml_diff}")
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    def dotted(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = dotted(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""
    calls = {dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    forbidden_exact = {"gym.make", "torch.load", "torch.save", "torch.jit.load"}
    forbidden_suffixes = (".load_state_dict", ".backward", ".optimizer.step", ".actor.update", ".trainer.update")
    violations = {name for name in calls if name in forbidden_exact or name.endswith(forbidden_suffixes)}
    _assert(not violations, f"forbidden calls in A6 suite {violations}")
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    _assert("AppLauncher" not in identifiers, "AppLauncher identifier")
    child = _clean_child()
    return {"production_hashes": len(hashes), "yaml_diff": "none", "clean_child": child}


TESTS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("evidence_vocabulary_and_cohorts", test_01_evidence_vocabulary_and_cohorts),
    ("d0_absent_profile_identity", test_02_d0_absent_profile_identity),
    ("valid_d1_existing_profile_mappings", test_03_valid_d1_existing_profile_mappings),
    ("scenario_correction_matrix", test_04_scenario_correction_matrix),
    ("legacy_observation_shared_action_mask", test_05_legacy_observation_shared_action_mask),
    ("contract_c_observation_shared_action_mask", test_06_contract_c_observation_shared_action_mask),
    ("proposal_effective_reward_identity", test_07_proposal_effective_reward_identity),
    ("actor_logprob_gae_valuenorm_factor_static_routes", test_08_actor_logprob_gae_valuenorm_factor_static_routes),
    ("rng_minibatch_logger_files_identity", test_09_rng_minibatch_logger_files_identity),
    ("v2_manifest_identity", test_10_v2_manifest_identity),
    ("ablation_and_diagnostics_routes", test_11_ablation_and_diagnostics_routes),
    ("wrapper_schema_manifest_profile_name_binding", test_wrapper_schema_manifest_profile_name_binding),
    ("event_phase_a_block_and_v3_identity", test_12_event_phase_a_block_and_v3_identity),
    ("playback_static_route", test_13_playback_static_route),
    ("deferred_runtime_inventory_consistency", test_14_deferred_runtime_inventory_consistency),
    ("production_scope_and_clean_child", test_15_production_scope_and_clean_child),
)


def run_suite() -> dict[str, Any]:
    results = []
    evidence: dict[str, Any] = {}
    failed = 0
    for name, test in TESTS:
        try:
            value = test()
        except Exception as exc:  # noqa: BLE001 - standalone suite reports every group.
            failed += 1
            results.append({"name": name, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": name, "status": "passed"})
            evidence[name] = value
    return {
        "status": "passed" if failed == 0 else "failed",
        "total": len(TESTS),
        "passed": len(TESTS) - failed,
        "failed": failed,
        "evidence_label_counts": EXPECTED_LABEL_COUNTS,
        "runtime_identity": DEFERRED,
        "results": results,
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        for row in result["results"]:
            print(f"{row['status'].upper()} {row['name']}" + (f": {row['error']}" if "error" in row else ""))
        print(f"{result['status'].upper()} {result['passed']}/{result['total']} Phase A6 identity groups")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
