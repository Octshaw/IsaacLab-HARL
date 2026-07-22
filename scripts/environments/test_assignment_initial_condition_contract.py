"""Pure/fake/static regressions for controlled assignment initial conditions.

The suite does not import Isaac Lab, launch AppLauncher, construct an
environment, load a checkpoint, run playback/evaluation, or train.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
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

from assignment_initial_condition import (  # noqa: E402
    CONDITION_CONTRACT_SCHEMA,
    CONDITION_MANIFEST_SCHEMA,
    EXPECTED_ORDERED_ROBOT_IDS,
    EXPECTED_REPOSITORY_FILES,
    EXPECTED_SLOT_IDS,
    EXPECTED_TASK_ID,
    FROZEN_POLICY_INTERFACE,
    INITIAL_CONDITION_MANIFEST_FILENAME,
    INITIAL_CONDITION_PROFILE_CHOICES,
    InitialConditionContractError,
    InitialConditionManifestError,
    InitialConditionProfile,
    InitialConditionProfileError,
    InitialConditionRequest,
    InitialConditionRunProvenance,
    InitialConditionUsageError,
    ResolvedComponentIdentity,
    ResolvedInitialConditionConfig,
    ResolvedRobotIdentity,
    build_initial_condition_manifest,
    canonical_initial_condition_bytes,
    capability_binding_from_mapping,
    compute_condition_fingerprint,
    make_initial_condition_request,
    make_resolved_file_reference,
    resolve_assignment_initial_condition,
    source_pose_wxyz_to_reset_xyzyaw,
    validate_initial_condition_output_files,
    validate_initial_condition_playback_cli,
    validate_initial_condition_profile,
    validate_initial_condition_runtime_interface,
    validate_initial_condition_training_config,
    write_initial_condition_manifest_atomic,
)
from capability_config import load_capability_profiles  # noqa: E402
from component_mesh import (  # noqa: E402
    compute_base_center_alignment_translation,
    compute_component_mesh_bounds,
)
from robot_config import load_robot_config  # noqa: E402
from viewpoint_csv import VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv  # noqa: E402


ATTRIBUTION_FILES = (
    "assignment_proposal_effective_rows.csv",
    "assignment_proposal_effective_summary.json",
    "assignment_target_segments.csv",
)
CANONICAL_INITIAL_CONDITION_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition"
)
MODULE_IDENTITY_EVIDENCE: dict[str, Any] = {}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_raises(
    function: Callable[[], Any],
    exception_types: type[BaseException] | tuple[type[BaseException], ...],
    expected_text: str,
) -> None:
    try:
        function()
    except exception_types as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"expected error containing {expected_text!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected {exception_types!r} containing {expected_text!r}")


def _source_path(identity: str) -> Path:
    return REPO_ROOT / EXPECTED_REPOSITORY_FILES[identity][0]


def _reference_config() -> ResolvedInitialConditionConfig:
    robot_path = _source_path("robot_config")
    capability_path = _source_path("capability_config")
    viewpoint_path = _source_path("viewpoint_csv")
    component_path = _source_path("component_obj")
    robot_config = load_robot_config(robot_path)
    capabilities = load_capability_profiles(capability_path)
    viewpoints = load_fixed_viewpoint_csv(viewpoint_path)

    robots = []
    for index, robot in enumerate(robot_config.enabled_robots):
        profile = capabilities.profiles[robot.capability_profile]
        robots.append(
            ResolvedRobotIdentity(
                robot_id=robot.name,
                agent_index=index,
                model_type=robot.model_type,
                source_pose_world_wxyz=robot.initial_pose_world,
                baseline_reset_pose_world_xyzyaw=source_pose_wxyz_to_reset_xyzyaw(
                    robot.initial_pose_world,
                    field=f"{robot.name}.initial_pose_world",
                ),
                capability_profile=robot.capability_profile,
                capability=capability_binding_from_mapping(
                    profile.to_dict(), field=f"capability[{robot.name}]"
                ),
                speed_weight=robot.speed_weight,
                cost_weight=robot.cost_weight,
                visual_usd_path=robot.visual_usd_path,
                visual_mesh_path=robot.visual_mesh_path,
                visual_mesh_scale=robot.visual_mesh_scale,
                visual_mesh_position_offset=robot.visual_mesh_position_offset,
                visual_mesh_yaw_offset=robot.visual_mesh_yaw_offset,
                visual_mesh_align_bottom_to_proxy_z=robot.visual_mesh_align_bottom_to_proxy_z,
            )
        )

    alignment = compute_base_center_alignment_translation(
        mesh_path=component_path,
        mesh_format="obj",
        mesh_unit="mm",
        mesh_scale=(0.001, 0.001, 0.001),
        mesh_orientation=(1.0, 0.0, 0.0, 0.0),
        mesh_orientation_format="qwxyz",
    )
    bounds = compute_component_mesh_bounds(
        mesh_path=component_path,
        mesh_format="obj",
        mesh_unit="mm",
        mesh_scale=(0.001, 0.001, 0.001),
        mesh_position=alignment.auto_translation,
        mesh_orientation=(1.0, 0.0, 0.0, 0.0),
        mesh_orientation_format="qwxyz",
        component_proxy_padding=0.0,
    )
    component = ResolvedComponentIdentity(
        mesh_format="obj",
        mesh_unit="mm",
        mesh_scale=(0.001, 0.001, 0.001),
        mesh_position=alignment.auto_translation,
        mesh_orientation=(1.0, 0.0, 0.0, 0.0),
        mesh_orientation_format="qwxyz",
        align_base_center_to_world_origin=True,
        base_center_before_translation=alignment.base_center_before_translation,
        auto_translation_if_used=alignment.auto_translation,
        raw_bounds_min=bounds.raw_bounds_obj_units_min,
        raw_bounds_max=bounds.raw_bounds_obj_units_max,
        world_bounds_min=bounds.world_bounds_m_min,
        world_bounds_max=bounds.world_bounds_m_max,
        auto_proxy_center=bounds.auto_component_proxy_center,
        auto_proxy_half_extents=bounds.auto_component_proxy_half_extents,
        proxy_type="bbox",
        proxy_center=(0.0, 0.0, 1.0),
        proxy_half_extents=(3.0, 1.0, 1.0),
        proxy_auto_from_mesh=False,
        proxy_padding=0.0,
    )
    return ResolvedInitialConditionConfig(
        task_id=EXPECTED_TASK_ID,
        scenario_name="algorithm_proxy_component_mesh",
        scenario_type="algorithm_visual_debug",
        scenario_file=make_resolved_file_reference(
            _source_path("scenario"), repository_root=REPO_ROOT, field="scenario"
        ),
        robot_config_file=make_resolved_file_reference(
            robot_path, repository_root=REPO_ROOT, field="robot_config"
        ),
        capability_config_file=make_resolved_file_reference(
            capability_path, repository_root=REPO_ROOT, field="capability_config"
        ),
        viewpoint_csv_file=make_resolved_file_reference(
            viewpoint_path, repository_root=REPO_ROOT, field="viewpoint_csv"
        ),
        component_obj_file=make_resolved_file_reference(
            component_path, repository_root=REPO_ROOT, field="component_obj"
        ),
        ordered_robot_ids=EXPECTED_ORDERED_ROBOT_IDS,
        robots=tuple(robots),
        action_space_key_order=EXPECTED_ORDERED_ROBOT_IDS,
        observation_space_key_order=EXPECTED_ORDERED_ROBOT_IDS,
        state_space_key_order=EXPECTED_ORDERED_ROBOT_IDS,
        viewpoint_format=VIEWPOINT_CSV_FORMAT,
        viewpoint_source=f"csv:{viewpoints.path}",
        viewpoint_ids=viewpoints.ids,
        viewpoint_poses_world_wxyz=viewpoints.poses,
        component=component,
        num_robots=3,
        num_tasks=50,
        policy_interface_contract=FROZEN_POLICY_INTERFACE,
    )


def _request(profile_id: str) -> InitialConditionRequest:
    return make_initial_condition_request(
        profile_id=profile_id,
        task_id=EXPECTED_TASK_ID,
        repository_root=REPO_ROOT,
        policy_interface_contract=FROZEN_POLICY_INTERFACE,
    )


def _resolve(profile_id: str, config: ResolvedInitialConditionConfig | None = None):
    return resolve_assignment_initial_condition(_request(profile_id), config or _reference_config())


def _provenance(result, **overrides: Any) -> InitialConditionRunProvenance:
    values = {
        "repository_commit": "a" * 40,
        "selected_cli_field": "--assignment_initial_condition_profile",
        "profile_id": result.condition_contract.profile_id,
        "resolved_absolute_source_paths": result.resolved_absolute_source_paths,
        "command_seed": 1,
        "deterministic_actor_mode": True,
        "checkpoint_directory": "C:/results/run/best_model",
        "checkpoint_child": "best_model",
        "checkpoint_kind": "best",
        "checkpoint_generation": 10,
        "assignment_checkpoint_fingerprint": "b" * 64,
        "load_purpose": "normal_evaluation",
        "legacy_fallback": False,
        "attribution_schema": "phase9g8h1_assignment_proposal_effective_attribution_v1",
        "created_timestamp": "2026-07-21T00:00:00+00:00",
    }
    values.update(overrides)
    return InitialConditionRunProvenance(**values)


def test_profile_resolution_and_pose_multisets() -> None:
    expected = {
        "baseline_identity": (("robot_0", "S0"), ("robot_1", "S1"), ("robot_2", "S2")),
        "pose_cycle_forward": (("robot_0", "S1"), ("robot_1", "S2"), ("robot_2", "S0")),
        "pose_cycle_reverse": (("robot_0", "S2"), ("robot_1", "S0"), ("robot_2", "S1")),
    }
    baseline_source = None
    baseline_reset = None
    for profile_id, mapping in expected.items():
        result = _resolve(profile_id)
        _assert(result is not None, f"{profile_id} returned no result")
        _assert(result.condition_contract.robot_to_slot_mapping == mapping, f"{profile_id} mapping changed")
        sources = [pose.source_pose_world_wxyz for pose in result.condition_contract.resolved_robot_poses]
        resets = [pose.reset_pose_world_xyzyaw for pose in result.condition_contract.resolved_robot_poses]
        slot_sources = [slot.source_pose_world_wxyz for slot in result.condition_contract.baseline_slots]
        slot_resets = [slot.reset_pose_world_xyzyaw for slot in result.condition_contract.baseline_slots]
        _assert(sorted(sources) == sorted(slot_sources), f"{profile_id} source pose multiset changed")
        _assert(sorted(resets) == sorted(slot_resets), f"{profile_id} reset pose multiset changed")
        baseline_source = baseline_source or slot_sources
        baseline_reset = baseline_reset or slot_resets
    _assert(baseline_source[0] == (-4.0, -2.0, 0.0, 1.0, 0.0, 0.0, 0.0), "S0 source changed")
    _assert(math.isclose(baseline_reset[1][3], -math.pi / 2, abs_tol=1.0e-12), "S1 yaw changed")
    _assert(math.isclose(abs(baseline_reset[2][3]), math.pi, abs_tol=1.0e-12), "S2 yaw changed")


def test_fingerprint_stability_separation_and_provenance() -> None:
    results = {profile: _resolve(profile) for profile in (
        "baseline_identity", "pose_cycle_forward", "pose_cycle_reverse"
    )}
    fingerprints = {profile: result.condition_fingerprint for profile, result in results.items()}
    _assert(len(set(fingerprints.values())) == 3, "A/B/C fingerprints are not pairwise distinct")
    _assert(_resolve("baseline_identity").condition_fingerprint == fingerprints["baseline_identity"], "fingerprint unstable")
    result = results["baseline_identity"]
    variants = (
        _provenance(result),
        _provenance(result, checkpoint_child="models", checkpoint_kind="final", checkpoint_generation=17),
        _provenance(result, command_seed=9, created_timestamp="2030-01-01T00:00:00Z"),
        _provenance(result, repository_commit="c" * 40, checkpoint_directory="D:/other/output/models"),
    )
    for provenance in variants:
        manifest = build_initial_condition_manifest(result, provenance)
        _assert(manifest.condition_fingerprint == result.condition_fingerprint, "provenance changed condition hash")
    changed_contract = replace(result.condition_contract, task_id="changed-task")
    _assert(compute_condition_fingerprint(changed_contract) != result.condition_fingerprint, "semantic change not hashed")
    description_only = replace(result.condition_contract, profile_description="different prose")
    _assert(compute_condition_fingerprint(description_only) == result.condition_fingerprint, "description was fingerprinted")


def test_strict_profile_failures() -> None:
    _expect_raises(lambda: _request("unknown"), InitialConditionProfileError, "unknown")
    base = InitialConditionProfile(
        profile_id="test",
        description="test",
        ordered_robot_ids=EXPECTED_ORDERED_ROBOT_IDS,
        ordered_slot_ids=EXPECTED_SLOT_IDS,
        robot_to_slot_mapping=(("robot_0", "S0"), ("robot_1", "S1")),
    )
    _expect_raises(lambda: validate_initial_condition_profile(base), InitialConditionProfileError, "missing")
    extra = replace(base, robot_to_slot_mapping=base.robot_to_slot_mapping + (("robot_x", "S2"),))
    _expect_raises(lambda: validate_initial_condition_profile(extra), InitialConditionProfileError, "extra")
    duplicate = replace(
        base,
        robot_to_slot_mapping=(("robot_0", "S0"), ("robot_1", "S0"), ("robot_2", "S2")),
    )
    _expect_raises(lambda: validate_initial_condition_profile(duplicate), InitialConditionProfileError, "bijective")
    unknown_slot = replace(
        base,
        robot_to_slot_mapping=(("robot_0", "S0"), ("robot_1", "S1"), ("robot_2", "S9")),
    )
    _expect_raises(lambda: validate_initial_condition_profile(unknown_slot), InitialConditionProfileError, "unknown slot")


def test_strict_resolved_configuration_failures() -> None:
    config = _reference_config()
    request = _request("baseline_identity")

    def fails(changed: ResolvedInitialConditionConfig, text: str) -> None:
        _expect_raises(
            lambda: resolve_assignment_initial_condition(request, changed),
            InitialConditionContractError,
            text,
        )

    fails(replace(config, task_id="wrong"), "task_id")
    fails(replace(config, scenario_name="wrong"), "scenario_name")
    fails(replace(config, ordered_robot_ids=("robot_1", "robot_0", "robot_2")), "ordered_robot_ids")
    fails(replace(config, num_robots=4), "M mismatch")
    fails(replace(config, num_tasks=49), "N mismatch")
    fails(
        replace(config, scenario_file=replace(config.scenario_file, sha256="0" * 64)),
        "declared_sha256",
    )
    swapped_ids = list(config.viewpoint_ids)
    swapped_ids[0], swapped_ids[1] = swapped_ids[1], swapped_ids[0]
    fails(replace(config, viewpoint_ids=tuple(swapped_ids)), "viewpoint_ids")
    swapped_poses = list(config.viewpoint_poses_world_wxyz)
    swapped_poses[0], swapped_poses[1] = swapped_poses[1], swapped_poses[0]
    fails(replace(config, viewpoint_poses_world_wxyz=tuple(swapped_poses)), "ordering/values")

    robots = list(config.robots)
    robots[0] = replace(robots[0], source_pose_world_wxyz=robots[0].source_pose_world_wxyz[:6])
    fails(replace(config, robots=tuple(robots)), "shape")
    robots = list(config.robots)
    robots[0] = replace(robots[0], source_pose_world_wxyz=(-4.0, -2.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    fails(replace(config, robots=tuple(robots)), "non-zero")
    robots = list(config.robots)
    robots[0] = replace(robots[0], source_pose_world_wxyz=(float("nan"),) + robots[0].source_pose_world_wxyz[1:])
    fails(replace(config, robots=tuple(robots)), "NaN or Inf")
    robots = list(config.robots)
    robots[0] = replace(robots[0], baseline_reset_pose_world_xyzyaw=(float("inf"), 0.0, 0.0, 0.0))
    fails(replace(config, robots=tuple(robots)), "NaN or Inf")
    robots = list(config.robots)
    robots[0] = replace(robots[0], capability_profile="mobile_scanner_b")
    fails(replace(config, robots=tuple(robots)), "capability_profile")
    robots = list(config.robots)
    robots[0] = replace(
        robots[0],
        capability=replace(robots[0].capability, scanner_start_offset=(9.0, 0.0, 0.0)),
    )
    fails(replace(config, robots=tuple(robots)), "capability binding")
    fails(
        replace(config, policy_interface_contract=replace(FROZEN_POLICY_INTERFACE, assignment_lifecycle_profile="legacy")),
        "policy_interface_contract",
    )
    fails(replace(config, component=replace(config.component, proxy_type="sphere")), "component.proxy_type")


def test_identity_preservation_and_default_compatibility() -> None:
    config = _reference_config()
    result = _resolve("pose_cycle_forward", config)
    _assert(resolve_assignment_initial_condition(None, None) is None, "default-off resolution built state")
    _assert(result.condition_contract.ordered_robot_ids == config.ordered_robot_ids, "robot ids reordered")
    for before, after in zip(config.robots, result.condition_contract.robot_bindings, strict=True):
        _assert(before == after, f"identity binding changed for {before.robot_id}")
    fake = {
        "possible_agents": list(config.ordered_robot_ids),
        "actor_map": {name: f"actor_{name}" for name in config.ordered_robot_ids},
        "capabilities": tuple(robot.capability for robot in config.robots),
        "base_start_poses": tuple(robot.baseline_reset_pose_world_xyzyaw for robot in config.robots),
    }
    before = {key: value for key, value in fake.items()}
    fake["base_start_poses"] = result.resolved_base_start_poses
    changed = [key for key in fake if fake[key] != before[key]]
    _assert(changed == ["base_start_poses"], f"fake application changed identity fields: {changed!r}")
    identity = _resolve("baseline_identity", config)
    _assert(identity.resolved_base_start_poses == before["base_start_poses"], "baseline identity changed poses")


def test_manifest_atomicity_and_output_contract() -> None:
    result = _resolve("baseline_identity")
    best = build_initial_condition_manifest(result, _provenance(result))
    final = build_initial_condition_manifest(
        result,
        _provenance(result, checkpoint_child="models", checkpoint_kind="final", checkpoint_generation=17),
    )
    _assert(best.manifest_schema_version == CONDITION_MANIFEST_SCHEMA, "manifest schema changed")
    _assert(best.condition_contract.schema_version == CONDITION_CONTRACT_SCHEMA, "contract schema changed")
    _assert(best.condition_fingerprint == final.condition_fingerprint, "best/final provenance changed hash")
    parsed = json.loads(canonical_initial_condition_bytes(best.to_mapping()).decode("utf-8"))
    _assert(set(parsed) == {"manifest_schema_version", "condition_contract", "condition_fingerprint", "run_provenance"}, "manifest fields changed")
    _expect_raises(
        lambda: canonical_initial_condition_bytes({"bad": float("nan")}),
        InitialConditionContractError,
        "finite",
    )

    with tempfile.TemporaryDirectory() as temporary:
        output_dir = Path(temporary)
        for name in ATTRIBUTION_FILES:
            (output_dir / name).write_text("test\n", encoding="utf-8")
        validate_initial_condition_output_files(
            output_dir, attribution_filenames=ATTRIBUTION_FILES, manifest_expected=False
        )
        manifest_path = output_dir / INITIAL_CONDITION_MANIFEST_FILENAME
        write_initial_condition_manifest_atomic(manifest_path, best)
        validate_initial_condition_output_files(
            output_dir, attribution_filenames=ATTRIBUTION_FILES, manifest_expected=True
        )
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        _assert(stored["condition_fingerprint"] == result.condition_fingerprint, "stored fingerprint changed")
        _expect_raises(
            lambda: write_initial_condition_manifest_atomic(manifest_path, best),
            FileExistsError,
            "already exists",
        )
        original = manifest_path.read_bytes()
        _assert(manifest_path.read_bytes() == original, "collision overwrote manifest")

    with tempfile.TemporaryDirectory() as temporary:
        partial = Path(temporary) / INITIAL_CONDITION_MANIFEST_FILENAME
        partial.write_text("partial", encoding="utf-8")
        _expect_raises(lambda: write_initial_condition_manifest_atomic(partial, best), FileExistsError, "already exists")
        _assert(partial.read_text(encoding="utf-8") == "partial", "partial destination was overwritten")


def test_playback_cli_training_guard_and_runtime_manifest() -> None:
    validate_initial_condition_playback_cli(
        profile_id=None,
        attribution_logging_enabled=False,
        attribution_output_dir=None,
    )
    _expect_raises(
        lambda: validate_initial_condition_playback_cli(
            profile_id="baseline_identity",
            attribution_logging_enabled=False,
            attribution_output_dir="out",
        ),
        InitialConditionUsageError,
        "log_assignment",
    )
    _expect_raises(
        lambda: validate_initial_condition_playback_cli(
            profile_id="baseline_identity",
            attribution_logging_enabled=True,
            attribution_output_dir=None,
        ),
        InitialConditionUsageError,
        "output_dir",
    )
    with tempfile.TemporaryDirectory() as temporary:
        collision = Path(temporary) / INITIAL_CONDITION_MANIFEST_FILENAME
        collision.write_text("existing", encoding="utf-8")
        _expect_raises(
            lambda: validate_initial_condition_playback_cli(
                profile_id="baseline_identity",
                attribution_logging_enabled=True,
                attribution_output_dir=temporary,
            ),
            FileExistsError,
            "new/empty",
        )
    validate_initial_condition_training_config(
        SimpleNamespace(assignment_initial_condition_profile=None, assignment_initial_condition_request=None)
    )
    constructed = False
    try:
        validate_initial_condition_training_config(
            SimpleNamespace(
                assignment_initial_condition_profile="pose_cycle_forward",
                assignment_initial_condition_request=None,
            )
        )
        constructed = True
    except InitialConditionUsageError:
        pass
    _assert(not constructed, "training guard allowed fake runner/environment construction")

    result = _resolve("baseline_identity")
    runtime_manifest = {
        "profile_name": "lifecycle_contract_c",
        "actor_schema_version": "lifecycle_v1_actor_3n",
        "shared_schema_version": "lifecycle_v1_shared_option_a_budget2m",
        "mask_contract_version": "lifecycle_contract_c_mask_v1",
        "budget_release_contract": "budget_release_v1",
        "legacy_guardrail_profile": "lifecycle_no_legacy_guardrails_v1",
        "actor_dimension": 1059,
        "shared_dimension": 3183,
        "M": 3,
        "N": 50,
        "action_dimension": 51,
        "noop_raw_id": 50,
        "noop_decoded_value": -1,
        "policy_sequence_mode": "feed_forward",
        "use_recurrent_policy": False,
        "use_naive_recurrent_policy": False,
    }
    validate_initial_condition_runtime_interface(
        result,
        ordered_agent_ids=EXPECTED_ORDERED_ROBOT_IDS,
        observation_manifest=runtime_manifest,
    )
    _expect_raises(
        lambda: validate_initial_condition_runtime_interface(
            result,
            ordered_agent_ids=("robot_1", "robot_0", "robot_2"),
            observation_manifest=runtime_manifest,
        ),
        InitialConditionContractError,
        "actor ordering",
    )


def test_runtime_module_identity_and_import_boundary() -> None:
    play_path = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py"
    env_path = SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py"
    play_tree = ast.parse(play_path.read_text(encoding="utf-8"), filename=str(play_path))
    env_tree = ast.parse(env_path.read_text(encoding="utf-8"), filename=str(env_path))

    canonical_imports = [
        node
        for node in ast.walk(play_tree)
        if isinstance(node, ast.ImportFrom) and node.module == CANONICAL_INITIAL_CONDITION_MODULE
    ]
    _assert(len(canonical_imports) == 1, "playback must have exactly one canonical initial-condition import")
    canonical_import = canonical_imports[0]
    expected_symbols = {
        "INITIAL_CONDITION_MANIFEST_FILENAME",
        "INITIAL_CONDITION_PROFILE_CHOICES",
        "InitialConditionRunProvenance",
        "build_initial_condition_manifest",
        "make_initial_condition_request",
        "make_playback_policy_interface_contract",
        "validate_initial_condition_output_files",
        "validate_initial_condition_playback_cli",
        "validate_initial_condition_runtime_interface",
        "write_initial_condition_manifest_atomic",
    }
    _assert(
        {alias.name for alias in canonical_import.names} == expected_symbols,
        "canonical playback import symbols differ from the used runtime boundary",
    )

    top_level_from = [
        node
        for node in ast.walk(play_tree)
        if isinstance(node, ast.ImportFrom) and node.module == "assignment_initial_condition"
    ]
    top_level_plain = [
        alias
        for node in ast.walk(play_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "assignment_initial_condition"
    ]
    _assert(not top_level_from and not top_level_plain, "playback still imports the top-level target module")
    _assert(
        not any(
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
            and node.attr == "modules"
            for node in ast.walk(play_tree)
        ),
        "playback introduces a sys.modules alias boundary",
    )

    simulation_lines = [
        node.lineno
        for node in play_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "simulation_app" for target in node.targets)
    ]
    task_package_import_lines = [
        node.lineno
        for node in play_tree.body
        if isinstance(node, ast.Import)
        and any(alias.name == "isaaclab_tasks" for alias in node.names)
    ]
    _assert(len(simulation_lines) == 1, "simulation_app assignment boundary is ambiguous")
    _assert(len(task_package_import_lines) == 1, "isaaclab_tasks registration import boundary is ambiguous")
    _assert(
        canonical_import.lineno > simulation_lines[0]
        and canonical_import.lineno > task_package_import_lines[0],
        "canonical target import occurs before SimulationApp/task package registration",
    )

    def call_lines(function_name: str) -> list[int]:
        return [
            node.lineno
            for node in ast.walk(play_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == function_name
        ]

    app_launcher_lines = call_lines("AppLauncher")
    prelaunch_validation_lines = call_lines("_validate_initial_condition_prelaunch_cli")
    canonical_validation_lines = call_lines("validate_initial_condition_playback_cli")
    request_lines = call_lines("make_initial_condition_request")
    wrapper_lines = call_lines("make_assignment_harl_env")
    _assert(len(app_launcher_lines) == 1, "AppLauncher construction boundary is ambiguous")
    _assert(len(prelaunch_validation_lines) == 1, "prelaunch validation call boundary is ambiguous")
    _assert(len(canonical_validation_lines) == 1, "canonical validation call boundary is ambiguous")
    _assert(len(request_lines) == 1 and len(wrapper_lines) == 1, "request/wrapper boundary is ambiguous")
    _assert(
        prelaunch_validation_lines[0] < app_launcher_lines[0],
        "import-free initial-condition usage validation occurs after AppLauncher",
    )
    _assert(
        canonical_import.lineno < canonical_validation_lines[0] < request_lines[0]
        and canonical_validation_lines[0] < wrapper_lines[0],
        "canonical vocabulary validation does not precede request/environment construction",
    )

    choice_assignments = [
        node
        for node in play_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES"
            for target in node.targets
        )
    ]
    _assert(len(choice_assignments) == 1, "prelaunch profile vocabulary assignment is ambiguous")
    local_choices = ast.literal_eval(choice_assignments[0].value)
    _assert(local_choices == INITIAL_CONDITION_PROFILE_CHOICES, "local/canonical profile vocabularies differ")
    parser_choice_uses = [
        keyword
        for node in ast.walk(play_tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "choices"
        and isinstance(keyword.value, ast.Name)
        and keyword.value.id == "PRELAUNCH_INITIAL_CONDITION_PROFILE_CHOICES"
    ]
    _assert(len(parser_choice_uses) == 1, "argparse does not use the import-free profile vocabulary")

    prelaunch_functions = [
        node
        for node in play_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_initial_condition_prelaunch_cli"
    ]
    _assert(len(prelaunch_functions) == 1, "prelaunch helper definition is ambiguous")
    extracted = ast.Module(body=[choice_assignments[0], prelaunch_functions[0]], type_ignores=[])
    ast.fix_missing_locations(extracted)
    namespace: dict[str, Any] = {"Path": Path}
    exec(compile(extracted, str(play_path), "exec"), namespace)  # noqa: S102 - isolated pure helper extraction.
    prelaunch_validate = namespace["_validate_initial_condition_prelaunch_cli"]
    prelaunch_validate(
        profile_id=None,
        attribution_logging_enabled=False,
        attribution_output_dir=None,
    )
    _expect_raises(
        lambda: prelaunch_validate(
            profile_id="unknown",
            attribution_logging_enabled=True,
            attribution_output_dir="out",
        ),
        ValueError,
        "unknown",
    )
    _expect_raises(
        lambda: prelaunch_validate(
            profile_id="baseline_identity",
            attribution_logging_enabled=False,
            attribution_output_dir="out",
        ),
        ValueError,
        "log_assignment",
    )
    _expect_raises(
        lambda: prelaunch_validate(
            profile_id="baseline_identity",
            attribution_logging_enabled=True,
            attribution_output_dir=None,
        ),
        ValueError,
        "output_dir",
    )
    with tempfile.TemporaryDirectory() as temporary:
        output_path = Path(temporary)
        existing_file = output_path / "existing.txt"
        existing_file.write_text("occupied", encoding="utf-8")
        _expect_raises(
            lambda: prelaunch_validate(
                profile_id="baseline_identity",
                attribution_logging_enabled=True,
                attribution_output_dir=output_path,
            ),
            FileExistsError,
            "new/empty",
        )
        _expect_raises(
            lambda: prelaunch_validate(
                profile_id="baseline_identity",
                attribution_logging_enabled=True,
                attribution_output_dir=existing_file,
            ),
            NotADirectoryError,
            "not a directory",
        )
        existing_file.unlink()
        (output_path / "existing_directory").mkdir()
        _expect_raises(
            lambda: prelaunch_validate(
                profile_id="baseline_identity",
                attribution_logging_enabled=True,
                attribution_output_dir=output_path,
            ),
            FileExistsError,
            "new/empty",
        )

    relative_consumer_imports = [
        node
        for node in ast.walk(env_tree)
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module == "assignment_initial_condition"
        and any(alias.name == "InitialConditionRequest" for alias in node.names)
    ]
    _assert(len(relative_consumer_imports) == 1, "environment package-relative request import changed")
    strict_checks = [
        node
        for node in ast.walk(env_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "isinstance"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == "InitialConditionRequest"
    ]
    _assert(strict_checks, "environment strict InitialConditionRequest isinstance boundary changed")

    child_source = r'''
import importlib.util
import json
from pathlib import Path
import sys

canonical_name = "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition"
scan_task_source = Path(sys.argv[1]).resolve()
repository_root = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(scan_task_source))
module_path = scan_task_source / "assignment_initial_condition.py"
spec = importlib.util.spec_from_file_location(canonical_name, module_path)
if spec is None or spec.loader is None:
    raise RuntimeError("could not create canonical module spec")
module = importlib.util.module_from_spec(spec)
sys.modules[canonical_name] = module
spec.loader.exec_module(module)

ProducerClass = module.InitialConditionRequest
policy_interface = module.make_playback_policy_interface_contract(
    assignment_lifecycle_profile="lifecycle_contract_c",
    algorithm="happo",
    use_recurrent_policy=False,
    use_naive_recurrent_policy=False,
    share_param=False,
    cuda_deterministic=True,
)
request = module.make_initial_condition_request(
    profile_id="baseline_identity",
    task_id=module.EXPECTED_TASK_ID,
    repository_root=repository_root,
    policy_interface_contract=policy_interface,
)
consumer_module = sys.modules[canonical_name]
ConsumerClass = consumer_module.InitialConditionRequest
print(json.dumps({
    "canonical_module": canonical_name,
    "producer_class_is_consumer_class": ProducerClass is ConsumerClass,
    "request_class_is_consumer_class": request.__class__ is ConsumerClass,
    "strict_isinstance": isinstance(request, ConsumerClass),
    "request_class_module": request.__class__.__module__,
    "canonical_key_present": canonical_name in sys.modules,
    "top_level_key_present": "assignment_initial_condition" in sys.modules,
    "profile_id": request.profile_id,
}, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", child_source, str(SCAN_TASK_SOURCE), str(REPO_ROOT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    _assert(
        completed.returncode == 0,
        f"canonical child-process identity check failed: stdout={completed.stdout!r}, stderr={completed.stderr!r}",
    )
    child_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    _assert(child_lines, "canonical child-process identity check emitted no evidence")
    evidence = json.loads(child_lines[-1])
    _assert(evidence["canonical_module"] == CANONICAL_INITIAL_CONDITION_MODULE, "canonical module name changed")
    _assert(evidence["producer_class_is_consumer_class"], "ProducerClass is not ConsumerClass")
    _assert(evidence["request_class_is_consumer_class"], "request class is not ConsumerClass")
    _assert(evidence["strict_isinstance"], "strict request isinstance failed")
    _assert(
        evidence["request_class_module"] == CANONICAL_INITIAL_CONDITION_MODULE,
        "request class has a noncanonical __module__",
    )
    _assert(evidence["canonical_key_present"], "canonical sys.modules key is absent")
    _assert(not evidence["top_level_key_present"], "conflicting top-level module key is active")
    _assert(evidence["profile_id"] == "baseline_identity", "canonical factory returned the wrong profile")
    MODULE_IDENTITY_EVIDENCE.update(
        evidence,
        playback_canonical_import_present=True,
        playback_top_level_import_absent=True,
        playback_sys_modules_alias_absent=True,
        canonical_import_after_simulation_app=True,
        canonical_import_after_task_package=True,
        canonical_revalidation_before_request_and_wrapper=True,
        environment_package_relative_import_preserved=True,
        environment_strict_isinstance_preserved=True,
        local_canonical_vocabulary_equal=True,
    )


def test_static_application_order_default_off_and_isolation() -> None:
    play_path = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "play_assignment.py"
    train_path = REPO_ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py"
    env_path = SCAN_TASK_SOURCE / "scan_mobile_manipulator_env.py"
    play = play_path.read_text(encoding="utf-8")
    train = train_path.read_text(encoding="utf-8")
    env = env_path.read_text(encoding="utf-8")
    _assert('default=None,\n    help="Optional controlled playback-only' in play, "CLI default is not None")
    prelaunch_call = play.index(
        "_validate_initial_condition_prelaunch_cli(",
        play.index("ASSIGNMENT_ATTRIBUTION_OUTPUT_DIR ="),
    )
    canonical_call = play.index(
        "validate_initial_condition_playback_cli(",
        play.index("import isaaclab_tasks"),
    )
    _assert(prelaunch_call < play.index("app_launcher = AppLauncher(args_cli)"), "prelaunch profile validation occurs after AppLauncher")
    _assert(play.index("import isaaclab_tasks") < canonical_call < play.index("def _attach_initial_condition_request"), "canonical profile revalidation ordering changed")
    _assert(play.index("apply_scenario_config_to_env_cfg(env_cfg, args_cli)") < play.index("_attach_initial_condition_request(env_cfg, agent_cfg)"), "request attached before scenario")
    normal_finalize = play.index(
        "        if attribution_collector is not None:\n"
        "            attribution_collector.finalize()\n"
        "        if initial_condition_result is not None:"
    )
    manifest_call = play.index("            manifest_path = _write_initial_condition_manifest(", normal_finalize)
    _assert(normal_finalize < manifest_call, "manifest precedes attribution finalize")
    _assert("if profile_id is None:\n        return" in play, "play no-selector branch is not immediate")
    _assert("if profile_id is None and request is None:\n        return" in env, "env no-selector branch is not immediate")
    _assert(env.index("_prepare_viewpoint_cfg(cfg)") < env.index("_prepare_assignment_initial_condition_cfg(cfg)") < env.index("super().__init__(cfg, render_mode, **kwargs)"), "environment hook ordering changed")
    train_main = train.index("def main(")
    training_guard = train.index("validate_initial_condition_training_config(env_cfg)", train_main)
    runner_registration = train.index("register_assignment_harl_runner(", train_main)
    runner_construction = train.index("runner = RUNNER_REGISTRY", train_main)
    _assert(
        training_guard < runner_registration < runner_construction,
        "training guard occurs after runner setup",
    )
    _assert("assignment_initial_condition_profile" not in train.split("parser =", 1)[1].split("AppLauncher.add_app_launcher_args", 1)[0], "training exposes playback CLI")

    forbidden = (
        "assignment_harl_wrapper.py",
        "assignment_playback_attribution_diagnostics.py",
        "assignment_checkpoint_contract.py",
        "assignment_checkpoint_load.py",
        "assignment_checkpoint_save.py",
        "assignment_controller.py",
        "assignment_lifecycle_resolver.py",
        "assignment_lifecycle_resolver_runtime.py",
    )
    for name in forbidden:
        source = (SCAN_TASK_SOURCE / name).read_text(encoding="utf-8")
        _assert("assignment_initial_condition" not in source, f"forbidden module references new contract: {name}")
    scenario_files = list((SCAN_TASK_SOURCE / "configs").rglob("*.yaml"))
    for path in scenario_files:
        _assert("assignment_initial_condition" not in path.read_text(encoding="utf-8"), f"YAML changed: {path}")


TESTS = (
    test_profile_resolution_and_pose_multisets,
    test_fingerprint_stability_separation_and_provenance,
    test_strict_profile_failures,
    test_strict_resolved_configuration_failures,
    test_identity_preservation_and_default_compatibility,
    test_manifest_atomicity_and_output_contract,
    test_playback_cli_training_guard_and_runtime_manifest,
    test_runtime_module_identity_and_import_boundary,
    test_static_application_order_default_off_and_isolation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = []
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - standalone pure regression runner.
            results.append({"name": test.__name__, "status": "failed", "error": repr(exc)})
        else:
            results.append({"name": test.__name__, "status": "passed"})
    failed = [result for result in results if result["status"] == "failed"]
    output = {
        "status": "failed" if failed else "passed",
        "num_tests": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "tests": results,
        "module_identity_evidence": MODULE_IDENTITY_EVIDENCE,
        "runtime_boundary": "pure/fake/static only; no Isaac Lab or AppLauncher import",
    }
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for result in results:
            suffix = f": {result['error']}" if result["status"] == "failed" else ""
            print(f"{result['status'].upper()} {result['name']}{suffix}")
        if MODULE_IDENTITY_EVIDENCE:
            print(f"canonical module: {MODULE_IDENTITY_EVIDENCE['canonical_module']}")
            print(
                "ProducerClass is ConsumerClass: "
                f"{MODULE_IDENTITY_EVIDENCE['producer_class_is_consumer_class']}"
            )
            print(
                "request.__class__ is ConsumerClass: "
                f"{MODULE_IDENTITY_EVIDENCE['request_class_is_consumer_class']}"
            )
            print(f"isinstance(request, ConsumerClass): {MODULE_IDENTITY_EVIDENCE['strict_isinstance']}")
            print(f"request class __module__: {MODULE_IDENTITY_EVIDENCE['request_class_module']}")
            print(f"canonical sys.modules key present: {MODULE_IDENTITY_EVIDENCE['canonical_key_present']}")
            print(f"conflicting top-level key present: {MODULE_IDENTITY_EVIDENCE['top_level_key_present']}")
        print(f"{'FAIL' if failed else 'PASS'} {output['passed']}/{output['num_tests']} tests")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
