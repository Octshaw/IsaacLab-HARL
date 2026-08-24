"""Pure/static B1W-I4-2 proposal, feasibility, arbitration, and M1 proof.

No Isaac, AppLauncher, Omni, PXr, HARL, training, playback, or evaluation code
is imported or executed.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import logging
import os
from pathlib import Path
import random
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Callable

import gymnasium
import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"
DIRECT_SOURCE = TASKS_SOURCE / "direct"
SCAN_SOURCE = DIRECT_SOURCE / "scan_mobile_manipulator"
PREFIX = "isaaclab_tasks.direct.scan_mobile_manipulator"
DEVICE = torch.device("cpu")

PATHS = {
    "profile": SCAN_SOURCE / "assignment_profile_contract.py",
    "transition": SCAN_SOURCE / "assignment_lifecycle_transition_contract.py",
    "event": SCAN_SOURCE / "assignment_event_contract.py",
    "b01": SCAN_SOURCE / "assignment_lifecycle_authority_runtime.py",
    "claim": SCAN_SOURCE / "assignment_initial_claim_runtime.py",
    "b02": SCAN_SOURCE / "assignment_lifecycle_transaction_runtime.py",
    "fence": SCAN_SOURCE / "assignment_interstep_claim_window_runtime.py",
    "domain": SCAN_SOURCE / "assignment_event_profile_runtime_domain.py",
    "sync": SCAN_SOURCE / "assignment_event_profile_synchronous_runtime.py",
    "proposal": SCAN_SOURCE / "assignment_event_proposal_adapter.py",
    "facade": SCAN_SOURCE / "assignment_event_runtime_facade.py",
    "wrapper": SCAN_SOURCE / "assignment_harl_wrapper.py",
    "package_init": SCAN_SOURCE / "__init__.py",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _logging_state() -> tuple[object, ...]:
    named = tuple(
        sorted(
            (
                name,
                logger.level,
                tuple(id(handler) for handler in logger.handlers),
                logger.disabled,
                logger.propagate,
            )
            for name, logger in logging.root.manager.loggerDict.items()
            if isinstance(logger, logging.Logger)
        )
    )
    return logging.root.level, tuple(id(handler) for handler in logging.root.handlers), named


def _inventory() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(REPO_ROOT))
            for path in REPO_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    )


def _numpy_state() -> tuple[object, ...]:
    state = np.random.get_state()
    return state[0], state[1].copy(), state[2], state[3], state[4]


def _same_numpy_state(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return left[0] == right[0] and np.array_equal(left[1], right[1]) and left[2:] == right[2:]


_IMPORT_RANDOM = random.getstate()
_IMPORT_TORCH_RANDOM = torch.random.get_rng_state().clone()
_IMPORT_NUMPY_RANDOM = _numpy_state()
_IMPORT_CWD = Path.cwd()
_IMPORT_SYS_PATH = tuple(sys.path)
_IMPORT_ENV = dict(os.environ)
_IMPORT_LOGGING = _logging_state()
_IMPORT_INVENTORY = _inventory()


def _install_namespace_packages() -> None:
    for name, path in (
        ("isaaclab_tasks", TASKS_SOURCE),
        ("isaaclab_tasks.direct", DIRECT_SOURCE),
        (PREFIX, SCAN_SOURCE),
    ):
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load(short_name: str) -> ModuleType:
    name = f"{PREFIX}.{PATHS[short_name].stem}"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, PATHS[short_name])
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {PATHS[short_name]}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace_packages()
PROFILE = _load("profile")
TRANSITION = _load("transition")
EVENT = _load("event")
B01 = _load("b01")
CLAIM = _load("claim")
B02 = _load("b02")
FENCE = _load("fence")
DOMAIN = _load("domain")
SYNC = _load("sync")
PROPOSAL = _load("proposal")
FACADE = _load("facade")
WRAPPER = _load("wrapper")
_PROFILE_REGISTRY = PROFILE.get_assignment_profile_registry()
_PROFILE_REGISTRY_REPR = repr(_PROFILE_REGISTRY)

TaskState = TRANSITION.TaskLifecycleState
RobotState = TRANSITION.RobotLifecycleState
Phase = FENCE._ClaimWindowFencePhase
Interpretation = PROPOSAL._EventProposalInterpretation


def _i(values: Any) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.int64, device=DEVICE)


def _profile(name: Any = None) -> Any:
    actual = PROFILE.AssignmentProfileName.EVENT_GATED_LOCAL_MRTA if name is None else name
    return PROFILE.resolve_assignment_profile(
        actual,
        PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT,
    )


def _domain(profile: Any, *, envs: int = 1, robots: int = 3, tasks: int = 5) -> Any:
    return DOMAIN._EventProfileLifecycleRuntimeDomain(
        DOMAIN._EventProfileLifecycleDomainSpec(
            profile,
            device=DEVICE,
            env_ids=_i(tuple(range(envs))),
            num_robots=robots,
            num_tasks=tasks,
        )
    )


def _reset_args(domain: Any) -> dict[str, torch.Tensor]:
    identity = domain.identity
    return {
        "selected_env_ids": _i(tuple(range(identity.num_envs))),
        "initial_task_state": torch.full(
            (identity.num_envs, identity.num_tasks),
            int(TaskState.AVAILABLE),
            dtype=torch.int64,
        ),
        "initial_robot_state": torch.full(
            (identity.num_envs, identity.num_robots),
            int(RobotState.NEEDS_ASSIGNMENT),
            dtype=torch.int64,
        ),
        "initial_ownership": torch.full(
            (identity.num_envs, identity.num_tasks),
            -1,
            dtype=torch.int64,
        ),
    }


def _report(domain: Any, *, terminal: bool) -> Any:
    identity = domain.identity
    terminal_rows = torch.full((identity.num_envs,), terminal, dtype=torch.bool)
    return DOMAIN._StagedPreResetPhysicalReport(
        device=DEVICE,
        coverage_before_transition=torch.zeros(
            (identity.num_envs, identity.num_tasks), dtype=torch.bool
        ),
        raw_new_candidate=torch.zeros(
            (identity.num_envs, identity.num_robots, identity.num_tasks),
            dtype=torch.bool,
        ),
        physical_truncated=terminal_rows,
        time_limit_reached=terminal_rows,
    )


class _EventEnvironment:
    def __init__(self, profile: Any, domain: Any) -> None:
        self._resolved_assignment_profile = profile
        self.domain = domain
        self.validation = domain.environment_admission_validation_port
        self.lifecycle = domain.environment_port
        self.terminal_next = False
        self.autoreset_terminal = True
        self.num_envs = domain.identity.num_envs
        self.num_viewpoints = domain.identity.num_tasks
        self.device = DEVICE
        self.max_episode_length = 32
        self.possible_agents = tuple(
            f"agent_{index}" for index in range(domain.identity.num_robots)
        )
        self.agents = list(self.possible_agents)
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-np.inf, np.inf, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self.cfg = SimpleNamespace(assignment_lifecycle_profile=profile.profile_name.value)
        self.reset_calls = 0
        self.step_calls = 0
        self.last_actions: object | None = None

    @property
    def unwrapped(self) -> "_EventEnvironment":
        return self

    def _obs(self) -> dict[str, torch.Tensor]:
        return {
            agent: torch.full(
                (self.num_envs, 4), float(index), dtype=torch.float32
            )
            for index, agent in enumerate(self.possible_agents)
        }

    def reset(self) -> tuple[dict[str, torch.Tensor], dict[str, object]]:
        self.reset_calls += 1
        self.validation.validate_reset_entry_for_active_call()
        with self.lifecycle.episode_rebuild(**_reset_args(self.domain)) as rebuild:
            rebuild.commit_physical_reset_complete()
        return self._obs(), {"route": "event_reset"}

    def step(self, actions: object) -> tuple[object, object, object, object, object]:
        self.step_calls += 1
        self.last_actions = actions.detach().clone() if type(actions) is torch.Tensor else actions
        self.validation.validate_physical_step_entry_for_active_call()
        self.validation.validate_physical_finalization_for_active_call()
        terminal = self.terminal_next
        self.lifecycle.finalize_physical_transition(_report(self.domain, terminal=terminal))
        if terminal and self.autoreset_terminal:
            self.validation.validate_reset_entry_for_active_call()
            with self.lifecycle.episode_rebuild(**_reset_args(self.domain)) as rebuild:
                rebuild.commit_physical_reset_complete()
        terminated = {
            agent: torch.zeros((self.num_envs,), dtype=torch.bool)
            for agent in self.possible_agents
        }
        truncated = {
            agent: torch.full((self.num_envs,), terminal, dtype=torch.bool)
            for agent in self.possible_agents
        }
        rewards = {
            agent: torch.zeros((self.num_envs,), dtype=torch.float32)
            for agent in self.possible_agents
        }
        return self._obs(), rewards, terminated, truncated, {"route": "event_step"}

    def close(self) -> None:
        return None


class _WrapperView:
    def __init__(self, raw: _EventEnvironment) -> None:
        self.unwrapped = raw
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self.unwrapped, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("wrapper called raw reset directly")

    def step(self, actions: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("wrapper called raw step directly")

    def close(self) -> None:
        self.unwrapped.close()


class _LegacyEnvironment:
    def __init__(self, profile_name: str) -> None:
        self.num_envs = 1
        self.num_viewpoints = 5
        self.device = DEVICE
        self.max_episode_length = 32
        self.possible_agents = ("agent_0", "agent_1", "agent_2")
        self.agents = list(self.possible_agents)
        self.cfg = SimpleNamespace(
            assignment_lifecycle_profile=profile_name,
            assignment_lifecycle_resolver_enabled=profile_name == "diagnostics_hidden_state",
            assignment_lifecycle_resolver_strict_proposals=True,
            assignment_lifecycle_resolver_log_diagnostics=False,
            assignment_lifecycle_resolver_output_dir=None,
            assignment_cooldown_enabled=profile_name == "lifecycle_contract_c",
            assignment_cooldown_trigger_mode=(
                "budget" if profile_name == "lifecycle_contract_c" else "streak"
            ),
            assignment_cooldown_apply_to_action_mask=profile_name != "lifecycle_contract_c",
            assignment_cooldown_duration_steps=20,
            assignment_redirect_guardrail_enabled=False,
            assignment_failed_pair_memory_enabled=False,
            max_base_xy_step=(0.08, 0.10, 0.12),
            scene=SimpleNamespace(env_spacing=1.0),
        )
        self.observation_spaces = {
            agent: gymnasium.spaces.Box(-np.inf, np.inf, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        feasible = torch.ones((1, 3, 5), dtype=torch.bool)
        self._problem = {
            "num_envs": 1,
            "num_agents": 3,
            "num_viewpoints": 5,
            "viewpoint_pos": torch.zeros((1, 5, 3), dtype=torch.float32),
            "viewpoint_quat": torch.zeros((1, 5, 4), dtype=torch.float32),
            "scanner_pos": torch.zeros((1, 3, 3), dtype=torch.float32),
            "viewpoints_covered": torch.zeros((1, 5), dtype=torch.bool),
            "available_mask": feasible.clone(),
            "feasible_mask": feasible.clone(),
            "static_geometric_feasible_mask": feasible.clone(),
            "cost_matrix": torch.zeros((1, 3, 5), dtype=torch.float32),
        }

    @property
    def unwrapped(self) -> "_LegacyEnvironment":
        return self

    def get_assignment_problem(self) -> dict[str, object]:
        return {
            key: value.detach().clone() if type(value) is torch.Tensor else value
            for key, value in self._problem.items()
        }

    def close(self) -> None:
        return None


def _compose(
    *,
    envs: int = 1,
    robots: int = 3,
    tasks: int = 5,
    stages: list[str] | None = None,
    observer: Callable[[str, object | None], None] | None = None,
) -> tuple[Any, _EventEnvironment, _WrapperView, Any]:
    profile = _profile()
    domain = _domain(profile, envs=envs, robots=robots, tasks=tasks)
    raw = _EventEnvironment(profile, domain)
    view = _WrapperView(raw)
    actual_observer = observer
    if actual_observer is None and stages is not None:
        actual_observer = lambda stage, detail: stages.append(stage)
    wrapper = WRAPPER._compose_event_assignment_harl_wrapper(
        env=view,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=actual_observer,
    )
    return wrapper, raw, view, domain


def _seed(domain: Any, rows: list[list[int]], env_ids: list[int] | None = None) -> Any:
    selected = list(range(len(rows))) if env_ids is None else env_ids
    envelope = domain.production_claim_port.prepare_production_initial_claim(
        selected_env_ids=_i(selected),
        requested_task_by_robot=_i(rows),
    )
    return domain.production_claim_port.commit_production_initial_claim(envelope)


def _decision(
    wrapper: Any,
    *,
    feasible: torch.Tensor | None = None,
    costs: torch.Tensor | None = None,
) -> Any:
    shape = (wrapper.num_envs, wrapper.num_agents, wrapper.num_viewpoints)
    actual_feasible = torch.ones(shape, dtype=torch.bool) if feasible is None else feasible
    actual_costs = torch.zeros(shape, dtype=torch.float32) if costs is None else costs
    return wrapper._capture_event_proposal_decision(
        feasible_mask=actual_feasible,
        cost_matrix=actual_costs,
        available_mask=actual_feasible.clone(),
    )


def _actions(rows: list[list[int]]) -> torch.Tensor:
    return torch.tensor(rows, dtype=torch.float32).unsqueeze(-1)


def _step(wrapper: Any, decision: Any, rows: list[list[int]]) -> Any:
    return wrapper._step_event_proposals(
        _actions(rows),
        decision=decision,
        action_builder=lambda env, assignment: assignment.detach().clone(),
    )


def _expect(operation: Callable[[], Any], *, code: str | None = None) -> BaseException:
    try:
        operation()
    except BaseException as exc:
        if code is not None:
            _assert(getattr(exc, "failure_code", None) == code, f"wrong failure: {exc}")
        return exc
    raise AssertionError("expected failure")


def _status(result: Any, env_row: int, robot_id: int) -> Any:
    return result.resolution.interpretations[env_row][robot_id]


def test_t1_private_pure_construction_and_surface() -> dict[str, object]:
    profile = _profile()
    adapter = PROPOSAL.EventProposalAdapter(profile)
    _assert(adapter.__slots__ == ("_profile",), "adapter retained capability leak")
    _assert(PROPOSAL.__all__ == (), "proposal module public export")
    _expect(lambda: PROPOSAL.EventProposalDecisionSnapshot(), code="decision_factory_required")
    _expect(lambda: PROPOSAL.EventProposalResolution(), code="resolution_factory_required")
    package_source = PATHS["package_init"].read_text(encoding="utf-8")
    _assert("assignment_event_proposal_adapter" not in package_source, "package export")
    source = PATHS["proposal"].read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"Lock", "RLock", "Condition", "Semaphore"}
    }
    _assert(not forbidden, f"adapter synchronization leaked {forbidden}")
    return {"retained": ["exact_profile"], "public_exports": 0, "mutex": 0}


def test_t2_snapshot_binding_and_alias_safety() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    feasible = torch.ones((1, 3, 5), dtype=torch.bool)
    costs = torch.arange(15, dtype=torch.float32).reshape(1, 3, 5)
    decision = _decision(wrapper, feasible=feasible, costs=costs)
    feasible.zero_()
    costs.fill_(999.0)
    _assert(bool(decision.feasible_mask.all().item()), "feasible snapshot aliased")
    _assert(float(decision.cost_matrix[0, 0, 0].item()) == 0.0, "cost snapshot aliased")
    current = wrapper._event_runtime_facade.read_current()
    _assert(decision.proposal_source_publication_identity is current.publication_identity, "P2 identity")
    return {"P2_identity": True, "window_identity": True, "no_alias": True}


def test_t3_a_continuation_only() -> dict[str, object]:
    stages: list[str] = []
    wrapper, raw, view, domain = _compose(stages=stages)
    wrapper.reset()
    _seed(domain, [[2, -1, -1]])
    source = domain.current_read_port.read_current()
    result = _step(wrapper, _decision(wrapper), [[2, 5, 5]])
    _assert(_status(result, 0, 0) is Interpretation.CONTINUE_EXISTING, "continuation")
    _assert(result.claim_artifact is None and result.post_claim_publication is source, "K0 mutation")
    _assert(result.admitted_effective_assignment.tolist() == [[2, -1, -1]], "Ak continuation")
    _assert(stages.count("S5_PROPOSAL_M1_CLAIM_COMMITTED") == 0, "redundant B1")
    _assert(view.direct_step_calls == 0 and raw.step_calls == 1, "raw wrapper step")
    return {"classification": "CONTINUE_EXISTING", "K": 0, "Ak": [2, -1, -1]}


def test_t4_b_new_claim_store_window() -> dict[str, object]:
    stages: list[str] = []
    commit_windows: list[object] = []
    domain_ref: list[Any] = []

    def observer(stage: str, detail: object | None) -> None:
        stages.append(stage)
        if stage == "S5_PROPOSAL_M1_CLAIM_COMMITTED":
            commit_windows.append(domain_ref[0].interstep_fence_read_port.read().window)

    wrapper, raw, _, domain = _compose(observer=observer)
    domain_ref.append(domain)
    wrapper.reset()
    decision = _decision(wrapper)
    source = domain.current_read_port.read_current()
    source_window = decision.proposal_source_window_identity
    result = _step(wrapper, decision, [[4, 5, 5]])
    _assert(type(result.claim_artifact) is CLAIM.EffectiveAssignmentCommitArtifact, "artifact")
    _assert(result.post_claim_publication.store_version == source.store_version + 1, "B1 version")
    _assert(result.current_publication.store_version == source.store_version + 2, "physical version")
    _assert(commit_windows == [source_window], "B1 changed window")
    _assert(result.admitted_publication is result.post_claim_publication, "Ak final P2")
    _assert(result.admitted_effective_assignment.tolist() == [[4, -1, -1]], "Ak claim")
    _assert(raw.last_actions.tolist() == [[4, -1, -1]], "control source")
    _assert(stages.count("S5_PROPOSAL_M1_CLAIM_COMMITTED") == 1, "M1 count")
    return {"artifact": 1, "B1_version_delta": 1, "physical_version_delta": 1}


def test_t5_c_lower_cost_conflict() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    costs = torch.zeros((1, 3, 5), dtype=torch.float32)
    costs[0, 1, 4], costs[0, 2, 4] = 3.0, 2.0
    result = _step(wrapper, _decision(wrapper, costs=costs), [[5, 4, 4]])
    _assert(_status(result, 0, 1) is Interpretation.CONFLICT_LOSER, "loser")
    _assert(_status(result, 0, 2) is Interpretation.NEW_CLAIM_SELECTED, "winner")
    _assert(result.resolution.requested_task_by_robot.tolist() == [[-1, -1, 4]], "M1")
    return {"winner_robot": 2, "rule": "minimum_finite_cost"}


def test_t6_d_equal_cost_global_robot_id() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    costs = torch.zeros((1, 3, 5), dtype=torch.float32)
    costs[0, 0, 4] = costs[0, 2, 4] = 7.0
    result = _step(wrapper, _decision(wrapper, costs=costs), [[4, 5, 4]])
    _assert(result.resolution.requested_task_by_robot.tolist() == [[4, -1, -1]], "tie")
    return {"winner_robot": 0, "rng": False}


def test_t7_e_nonfinite_feasible_fallback() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    costs = torch.zeros((1, 3, 5), dtype=torch.float32)
    costs[0, 1, 4], costs[0, 2, 4] = float("inf"), float("nan")
    result = _step(wrapper, _decision(wrapper, costs=costs), [[5, 4, 4]])
    _assert(result.resolution.requested_task_by_robot.tolist() == [[-1, 4, -1]], "fallback")
    return {"winner_robot": 1, "NaN": "nonfinite", "eligibility": "preserved"}


def test_t8_f_infeasible_finite_never_reenters() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    feasible = torch.ones((1, 3, 5), dtype=torch.bool)
    feasible[0, 1, 4] = False
    costs = torch.zeros((1, 3, 5), dtype=torch.float32)
    costs[0, 1, 4], costs[0, 2, 4] = 1.0, 10.0
    result = _step(wrapper, _decision(wrapper, feasible=feasible, costs=costs), [[5, 4, 4]])
    _assert(_status(result, 0, 1) is Interpretation.PHYSICALLY_INFEASIBLE, "feasibility")
    _assert(result.resolution.requested_task_by_robot.tolist() == [[-1, -1, 4]], "re-entry")
    return {"winner_robot": 2, "infeasible_finite_reentry": False}


def test_t9_g_executing_switch_rejected_continues() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    _seed(domain, [[2, -1, -1]])
    result = _step(wrapper, _decision(wrapper), [[4, 5, 5]])
    _assert(_status(result, 0, 0) is Interpretation.INVALID_SWITCH_WHILE_EXECUTING, "switch")
    _assert(result.claim_artifact is None, "switch claimed")
    _assert(result.admitted_effective_assignment.tolist() == [[2, -1, -1]], "current task")
    return {"proposal": 4, "effective": 2, "release": False}


def test_t10_h_executing_noop_illegal() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    _seed(domain, [[2, -1, -1]])
    result = _step(wrapper, _decision(wrapper), [[5, 5, 5]])
    _assert(_status(result, 0, 0) is Interpretation.ILLEGAL_EXECUTING_NOOP, "noop")
    _assert(result.admitted_effective_assignment.tolist() == [[2, -1, -1]], "continuation rewrite")
    return {"classification": "ILLEGAL_EXECUTING_NOOP", "P2_mutation": False}


def test_t11_i_needs_noop_no_claim() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    source = domain.current_read_port.read_current()
    result = _step(wrapper, _decision(wrapper), [[5, 5, 5]])
    _assert(result.claim_artifact is None and result.post_claim_publication is source, "noop claim")
    _assert(result.admitted_effective_assignment.tolist() == [[-1, -1, -1]], "owner fabricated")
    return {"K": 0, "owner": None}


def test_t12_j_mixed_continuation_and_claim() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    _seed(domain, [[2, -1, -1]])
    result = _step(wrapper, _decision(wrapper), [[2, 4, 5]])
    _assert(_status(result, 0, 0) is Interpretation.CONTINUE_EXISTING, "mixed continuation")
    _assert(result.resolution.requested_task_by_robot.tolist() == [[-1, 4, -1]], "mixed M1")
    _assert(result.admitted_effective_assignment.tolist() == [[2, 4, -1]], "mixed Ak")
    return {"M1": [-1, 4, -1], "final_P2_Ak": [2, 4, -1]}


def test_t13_multi_env_single_m1() -> dict[str, object]:
    stages: list[str] = []
    wrapper, _, _, domain = _compose(envs=2, stages=stages)
    wrapper.reset()
    source = domain.current_read_port.read_current()
    result = _step(wrapper, _decision(wrapper), [[4, 5, 5], [3, 4, 5]])
    _assert(result.resolution.selected_env_ids.tolist() == [0, 1], "env order")
    _assert(result.resolution.requested_task_by_robot.tolist() == [[4, -1, -1], [3, 4, -1]], "C2")
    _assert(result.post_claim_publication.store_version == source.store_version + 1, "one version")
    _assert(stages.count("S5_PROPOSAL_M1_CLAIM_COMMITTED") == 1, "sequential M2")
    return {"selected_env_ids": [0, 1], "artifact_count": 1, "Store_delta": 1}


def test_t14_conflict_plus_independent_env_atomic() -> dict[str, object]:
    wrapper, _, _, _ = _compose(envs=2)
    wrapper.reset()
    costs = torch.zeros((2, 3, 5), dtype=torch.float32)
    costs[0, 0, 4], costs[0, 1, 4] = 8.0, 2.0
    result = _step(wrapper, _decision(wrapper, costs=costs), [[4, 4, 5], [3, 5, 5]])
    _assert(result.resolution.requested_task_by_robot.tolist() == [[-1, 4, -1], [3, -1, -1]], "atomic")
    _assert(type(result.claim_artifact) is CLAIM.EffectiveAssignmentCommitArtifact, "one artifact")
    return {"env0_winner": 1, "env1_preserved": True, "artifact_count": 1}


def test_t15_stale_p2_rejected_before_b1_ak_env() -> dict[str, object]:
    wrapper, raw, _, domain = _compose()
    wrapper.reset()
    decision = _decision(wrapper)
    _seed(domain, [[0, -1, -1]])
    post_seed = domain.current_read_port.read_current()
    exc = _expect(
        lambda: _step(wrapper, decision, [[5, 4, 5]]),
        code="stale_proposal_source",
    )
    _assert(raw.step_calls == 0, "stale proposal reached env")
    _assert(domain.current_read_port.read_current() is post_seed, "stale proposal mutated P2")
    return {"stage": getattr(exc, "stage", None), "B1": 0, "Ak": 0, "env": 0}


def test_t16_w2_stale_envelope_never_rebound() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    facade = wrapper._event_runtime_facade
    decision = _decision(wrapper)
    resolution = facade.resolve_proposals(
        raw_action_ids=_i(((4, 5, 5),)),
        decoded_proposal=_i(((4, -1, -1),)),
        decision=decision,
    )
    envelope = domain.production_claim_port.prepare_production_initial_claim(
        selected_env_ids=resolution.selected_env_ids,
        requested_task_by_robot=resolution.requested_task_by_robot,
    )
    wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _expect(
        lambda: domain.production_claim_port.commit_production_initial_claim(envelope),
        code="stale_claim_window",
    )
    return {"W1_to_W2": True, "rebind": False, "authority": "W2"}


def test_t17_terminal_handoff_then_next_window_recovers() -> dict[str, object]:
    wrapper, raw, _, domain = _compose()
    wrapper.reset()
    raw.terminal_next = True
    terminal_result = wrapper._step_event_without_new_claim(
        action_builder=lambda env, assignment: assignment.detach().clone()
    )
    _assert(len(terminal_result.terminal_historical_payload) == 1, "terminal history absent")
    _assert(
        domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (),
        "terminal slot retained after exact ACK",
    )
    terminal_window = domain.interstep_fence_read_port.read().window
    _assert(terminal_result.current_publication.result is None, "historical/current P2 leak")
    raw.terminal_next = False
    decision = _decision(wrapper)
    next_result = _step(wrapper, decision, [[4, 5, 5]])
    next_window = domain.interstep_fence_read_port.read().window
    _assert(next_result.terminal_historical_payload == (), "terminal history accumulated")
    _assert(next_window is not terminal_window, "next claim window did not advance")
    _assert(not domain._coordinator.poisoned, "post-ACK recovery poisoned")
    return {"terminal_history": 1, "slots": 0, "next_window": "OPEN", "poison": False}


def test_t18_hostile_wrapper_cache_cannot_control() -> dict[str, object]:
    wrapper, raw, _, domain = _compose()
    wrapper.reset()
    _seed(domain, [[2, -1, -1]])
    wrapper.last_assignment_proposal = _i(((0, 0, 0),))
    wrapper.last_assignment = _i(((1, 1, 1),))
    wrapper.last_effective_assignment = _i(((3, 3, 3),))
    result = _step(wrapper, _decision(wrapper), [[2, 4, 5]])
    _assert(result.admitted_effective_assignment.tolist() == [[2, 4, -1]], "cache control")
    _assert(raw.last_actions.tolist() == [[2, 4, -1]], "raw cache control")
    _assert(result.admitted_publication is result.post_claim_publication, "final P2")
    return {"controller_source": "final P2 -> Ak", "hostile_cache": "ignored"}


def test_t19_resolution_immutability_and_zero_one_artifact() -> dict[str, object]:
    wrapper, _, _, _ = _compose()
    wrapper.reset()
    decision = _decision(wrapper)
    facade = wrapper._event_runtime_facade
    raw = _i(((4, 5, 5),))
    decoded = _i(((4, -1, -1),))
    resolution = facade.resolve_proposals(
        raw_action_ids=raw,
        decoded_proposal=decoded,
        decision=decision,
    )
    raw.fill_(0)
    decoded.fill_(0)
    captured = resolution.decoded_proposal
    captured.fill_(1)
    _assert(resolution.raw_action_ids.tolist() == [[4, 5, 5]], "raw alias")
    _assert(resolution.decoded_proposal.tolist() == [[4, -1, -1]], "proposal alias")
    result = facade.step_resolved_proposals(
        resolution=resolution,
        action_builder=lambda env, assignment: assignment.detach().clone(),
    )
    _assert(not isinstance(result.claim_artifact, (list, tuple)), "artifact list")
    return {"DTO": "frozen/no-alias", "artifact_cardinality": 1}


def test_t20_structural_owned_and_default_off_isolation() -> dict[str, object]:
    wrapper, _, _, domain = _compose()
    wrapper.reset()
    _seed(domain, [[4, -1, -1]])
    result = _step(wrapper, _decision(wrapper), [[4, 4, 5]])
    _assert(_status(result, 0, 0) is Interpretation.CONTINUE_EXISTING, "owner continuation")
    _assert(_status(result, 0, 1) is Interpretation.TASK_OWNED, "owned rejection")
    _assert(result.claim_artifact is None, "owned duplicate claim")
    profiles = []
    for name in (
        "legacy",
        "lifecycle_contract_c",
        "lifecycle_ablation",
        "diagnostics_hidden_state",
    ):
        profile = _profile(PROFILE.AssignmentProfileName(name))
        legacy = WRAPPER.AssignmentHarlWrapper(
            _LegacyEnvironment(name),
            resolved_assignment_profile=profile,
            profile_resolution_origin=profile.resolution_origin,
        )
        _assert(legacy._event_runtime_facade is None, f"event facade leaked to {name}")
        profiles.append(name)
    return {"TASK_OWNED": "rejected", "legacy_profiles": profiles, "event_objects": 0}


def test_t21_public_and_deferred_boundaries() -> dict[str, object]:
    wrapper, raw, view, _ = _compose()
    wrapper.reset()
    _expect(lambda: wrapper.step(_actions([[4, 5, 5]])))
    _expect(wrapper.make_available_actions)
    _expect(lambda: getattr(wrapper, "assignment_observation_schema_manifest"))
    _assert(raw.step_calls == 0 and view.direct_step_calls == 0, "public mutation")
    facade = wrapper._event_runtime_facade
    for name in (
        "capture_pending_terminal_artifacts",
        "acknowledge_terminal_artifact",
        "acknowledge_terminal_batch",
    ):
        _assert(not hasattr(facade, name), f"terminal I4-3 surface leaked: {name}")
    return {
        "public_event_step": "blocked",
        "obs_mask": "absent",
        "raw_terminal_ack_surface": "absent",
        "private_terminal_handoff": "integrated",
    }


def test_t22_global_side_effects() -> dict[str, object]:
    blocked = sorted(
        name
        for name in sys.modules
        if name == "isaaclab" or name.startswith(("isaaclab.", "omni", "pxr", "harl"))
    )
    _assert(blocked == [], f"heavy modules imported {blocked}")
    _assert(random.getstate() == _IMPORT_RANDOM, "Python RNG changed")
    _assert(torch.equal(torch.random.get_rng_state(), _IMPORT_TORCH_RANDOM), "Torch RNG changed")
    _assert(_same_numpy_state(_numpy_state(), _IMPORT_NUMPY_RANDOM), "NumPy RNG changed")
    _assert(Path.cwd() == _IMPORT_CWD, "cwd changed")
    _assert(tuple(sys.path) == _IMPORT_SYS_PATH, "sys.path changed")
    _assert(dict(os.environ) == _IMPORT_ENV, "environment changed")
    _assert(_logging_state() == _IMPORT_LOGGING, "logging changed")
    _assert(_inventory() == _IMPORT_INVENTORY, "filesystem changed")
    _assert(PROFILE.get_assignment_profile_registry() is _PROFILE_REGISTRY, "registry identity")
    _assert(repr(PROFILE.get_assignment_profile_registry()) == _PROFILE_REGISTRY_REPR, "registry content")
    return {"heavy_modules": blocked, "rng": "unchanged", "process": "unchanged"}


TESTS = (
    ("I4-2-T1", test_t1_private_pure_construction_and_surface),
    ("I4-2-T2", test_t2_snapshot_binding_and_alias_safety),
    ("I4-2-T3-A", test_t3_a_continuation_only),
    ("I4-2-T4-B", test_t4_b_new_claim_store_window),
    ("I4-2-T5-C", test_t5_c_lower_cost_conflict),
    ("I4-2-T6-D", test_t6_d_equal_cost_global_robot_id),
    ("I4-2-T7-E", test_t7_e_nonfinite_feasible_fallback),
    ("I4-2-T8-F", test_t8_f_infeasible_finite_never_reenters),
    ("I4-2-T9-G", test_t9_g_executing_switch_rejected_continues),
    ("I4-2-T10-H", test_t10_h_executing_noop_illegal),
    ("I4-2-T11-I", test_t11_i_needs_noop_no_claim),
    ("I4-2-T12-J", test_t12_j_mixed_continuation_and_claim),
    ("I4-2-T13", test_t13_multi_env_single_m1),
    ("I4-2-T14", test_t14_conflict_plus_independent_env_atomic),
    ("I4-2-T15", test_t15_stale_p2_rejected_before_b1_ak_env),
    ("I4-2-T16", test_t16_w2_stale_envelope_never_rebound),
    ("I4-2-T17", test_t17_terminal_handoff_then_next_window_recovers),
    ("I4-2-T18", test_t18_hostile_wrapper_cache_cannot_control),
    ("I4-2-T19", test_t19_resolution_immutability_and_zero_one_artifact),
    ("I4-2-T20", test_t20_structural_owned_and_default_off_isolation),
    ("I4-2-T21", test_t21_public_and_deferred_boundaries),
    ("I4-2-T22", test_t22_global_side_effects),
)


def run_suite() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    passed = 0
    for name, operation in TESTS:
        try:
            evidence = operation()
        except BaseException as exc:
            rows.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            rows.append({"name": name, "status": "passed", "evidence": evidence})
            passed += 1
    return {
        "status": "passed" if passed == len(TESTS) else "failed",
        "passed": passed,
        "failed": len(TESTS) - passed,
        "num_tests": len(TESTS),
        "tests": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_suite()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for row in result["tests"]:
            print(f"{row['name']}: {row['status']}")
            if row["status"] == "failed":
                print(f"  {row['error']}")
        print(f"passed {result['passed']}/{result['num_tests']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
