"""Scenario YAML support for real-component scan smoke and helper scripts."""

from __future__ import annotations

import json
import math
from argparse import Namespace
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal Python envs.
    yaml = None

try:
    from .viewpoint_csv import VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv
except ImportError:  # Allows direct script imports after SCAN_TASK_SOURCE is added to sys.path.
    from viewpoint_csv import VIEWPOINT_CSV_FORMAT, load_fixed_viewpoint_csv


SUPPORTED_MESH_UNITS = {"mm"}
SUPPORTED_MESH_FORMATS = {"obj"}
SUPPORTED_ORIENTATION_FORMAT = "qwxyz"
SUPPORTED_ROBOT_VISUAL_MODES = {"mesh", "debug_marker", "none"}
SUPPORTED_COMPONENT_VISUAL_MODES = {"mesh", "bbox", "none"}
SUPPORTED_OBSTACLE_DIAGNOSTIC_MODES = {"diagnostics_only"}
SUPPORTED_OBSTACLE_SOURCES = {"component_mesh_footprint"}
SUPPORTED_OBSTACLE_DEBUG_LINE_SOURCES = {"mesh_footprint_intersections", "selected_assignments"}
SUPPORTED_OBSTACLE_DEBUG_LINE_Z_MODES = {"fixed", "max_endpoint"}
SUPPORTED_INTER_ROBOT_CONFLICT_MODES = {"diagnostics_only"}
SUPPORTED_TARGET_CONFLICT_CANDIDATE_COMPARISON_MODES = {"diagnostic_only"}
SUPPORTED_TARGET_CONFLICT_CANDIDATE_GENERATORS = {"sequential_robot_order"}
SUPPORTED_TARGET_CONFLICT_ROBOT_ORDERS = {"robot_index"}
SUPPORTED_TARGET_CONFLICT_COMPARE_METHODS = {"nearest", "greedy", "random"}
SUPPORTED_CONFLICT_AWARE_BASELINE_MODES = {"gated_solver_variant"}
SUPPORTED_CONFLICT_AWARE_BASELINE_METHODS = {"greedy_conflict_aware", "nearest_conflict_aware"}

ENV_CFG_SCENARIO_ATTRS = (
    "viewpoint_csv_path",
    "robot_config_path",
    "capability_config_path",
    "robot_visual_mode",
    "component_visual_mode",
    "gui_camera_enabled",
    "gui_camera_eye",
    "gui_camera_target",
    "ground_grid_enabled",
    "ground_grid_half_extent",
    "ground_grid_spacing",
    "ground_grid_z",
    "ground_grid_line_width",
    "component_mesh_path",
    "component_mesh_format",
    "component_mesh_unit",
    "component_mesh_scale",
    "component_mesh_position",
    "component_mesh_orientation",
    "component_mesh_orientation_format",
    "component_mesh_visible",
    "component_proxy_type",
    "component_proxy_auto_from_mesh",
    "component_proxy_padding",
    "component_proxy_visual_visible",
    "obstacle_diagnostics_enabled",
    "obstacle_diagnostics_mode",
    "obstacle_source",
    "obstacle_footprint_resolution",
    "obstacle_footprint_inflation_radius",
    "obstacle_line_sample_step",
    "obstacle_blocked_path_penalty",
    "actual_base_motion_obstacle_diagnostics_enabled",
    "actual_base_motion_obstacle_diagnostics_mode",
    "actual_base_motion_obstacle_source",
    "actual_base_motion_line_sample_step",
    "actual_base_motion_min_motion_distance",
    "actual_base_motion_max_pairs_sample",
    "actual_base_motion_debug_visualization_enabled",
    "actual_base_motion_debug_visualization_draw_in_headless",
    "actual_base_motion_debug_visualization_max_lines",
    "actual_base_motion_debug_visualization_line_width",
    "obstacle_debug_visualization_enabled",
    "obstacle_debug_visualization_draw_in_headless",
    "obstacle_debug_visualization_line_source",
    "obstacle_debug_visualization_max_lines_per_robot",
    "obstacle_debug_visualization_max_total_lines",
    "obstacle_debug_visualization_prefer_shortest_blocked_pairs",
    "obstacle_debug_visualization_line_z_mode",
    "obstacle_debug_visualization_line_z_value",
    "obstacle_debug_visualization_line_z_offset",
    "obstacle_debug_visualization_line_width",
    "inter_robot_conflict_diagnostics_enabled",
    "inter_robot_conflict_diagnostics_mode",
    "inter_robot_conflict_robot_footprint_radius",
    "inter_robot_conflict_safety_margin",
    "inter_robot_target_conflict_enabled",
    "inter_robot_target_conflict_radius",
    "inter_robot_target_conflict_safety_margin",
    "inter_robot_conflict_debug_visualization_enabled",
    "inter_robot_conflict_debug_visualization_draw_in_headless",
    "inter_robot_conflict_debug_visualization_max_lines",
    "inter_robot_conflict_debug_visualization_line_width",
)


def load_scenario_config(config_path: str | Path | None, *, repo_root: Path) -> dict[str, Any]:
    """Load a YAML scenario config. JSON is accepted as a no-PyYAML fallback."""

    if config_path is None:
        return {}
    resolved_path = resolve_path(config_path, repo_root=repo_root, must_exist=True, label="scenario_config")
    suffix = resolved_path.suffix.lower()
    with resolved_path.open("r", encoding="utf-8") as file:
        if suffix == ".json":
            data = json.load(file)
        else:
            if yaml is None:
                raise RuntimeError(
                    f"PyYAML is not available, so YAML scenario configs cannot be loaded: {resolved_path}. "
                    "Install/use an environment with PyYAML or provide a JSON scenario config."
                )
            data = yaml.safe_load(file)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"scenario_config must contain a mapping/object at top level: {resolved_path}")
    data = dict(data)
    data["_scenario_config_path"] = str(resolved_path)
    return data


def smoke_defaults_from_config(config: Mapping[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    _put(defaults, "scenario_config_path", config.get("_scenario_config_path"))
    _put(defaults, "scenario_name", config.get("scenario_name"))
    _put(defaults, "scenario_type", config.get("scenario_type"))
    _put(defaults, "task", config.get("task"))
    _put(defaults, "num_envs", config.get("num_envs"))
    _put(defaults, "max_steps", config.get("max_steps"))
    _put(defaults, "seed", config.get("seed"))
    _put(defaults, "headless", config.get("headless"))
    _put(defaults, "device", config.get("device"))
    _put(defaults, "disable_fabric", config.get("disable_fabric"))
    _put(defaults, "viewpoint_candidate_top_k", config.get("viewpoint_candidate_top_k"))

    visualization = _mapping(config.get("visualization"), "visualization", required=False)
    _put(defaults, "robot_visual_mode", visualization.get("robot_visual_mode"))
    _put(defaults, "component_visual_mode", visualization.get("component_visual_mode"))
    _put(defaults, "gui_camera_enabled", visualization.get("gui_camera_enabled"))
    _put(defaults, "gui_camera_eye", visualization.get("gui_camera_eye"))
    _put(defaults, "gui_camera_target", visualization.get("gui_camera_target"))
    _put(defaults, "ground_grid_enabled", visualization.get("ground_grid_enabled"))
    _put(defaults, "ground_grid_half_extent", visualization.get("ground_grid_half_extent"))
    _put(defaults, "ground_grid_spacing", visualization.get("ground_grid_spacing"))
    _put(defaults, "ground_grid_z", visualization.get("ground_grid_z"))
    _put(defaults, "ground_grid_line_width", visualization.get("ground_grid_line_width"))

    mesh = _mapping(config.get("component_mesh"), "component_mesh", required=False)
    _put(defaults, "component_mesh_path", mesh.get("path"))
    _put(defaults, "component_mesh_format", mesh.get("format"))
    _put(defaults, "component_mesh_unit", mesh.get("unit"))
    _put(defaults, "component_mesh_scale", mesh.get("scale"))
    _put(defaults, "component_mesh_position", mesh.get("position"))
    _put(defaults, "component_mesh_orientation", mesh.get("orientation"))
    _put(defaults, "component_mesh_orientation_format", mesh.get("orientation_format"))
    _put(defaults, "component_mesh_visible", mesh.get("visible"))
    _put(defaults, "align_base_center_to_world_origin", mesh.get("align_base_center_to_world_origin"))

    proxy = _mapping(config.get("component_proxy"), "component_proxy", required=False)
    _put(defaults, "component_proxy_type", proxy.get("type"))
    _put(defaults, "component_proxy_auto_from_mesh", proxy.get("auto_from_mesh"))
    _put(defaults, "component_proxy_padding", proxy.get("padding"))
    _put(defaults, "component_proxy_visual_visible", proxy.get("visual_visible"))

    viewpoints = _mapping(config.get("viewpoints"), "viewpoints", required=False)
    _put(defaults, "viewpoint_csv_path", viewpoints.get("csv_path"))
    _put(defaults, "expect_num_viewpoints", viewpoints.get("expect_num_viewpoints"))
    _put(defaults, "viewpoint_candidate_top_k", viewpoints.get("candidate_top_k"))

    robots = _mapping(config.get("robots"), "robots", required=False)
    _put(defaults, "robot_config_path", robots.get("config_path"))

    capabilities = _mapping(config.get("capabilities"), "capabilities", required=False)
    _put(defaults, "capability_config_path", capabilities.get("config_path"))

    assignment = _mapping(config.get("assignment"), "assignment", required=False)
    _put(defaults, "viewpoint_candidate_top_k", assignment.get("viewpoint_candidate_top_k"))

    obstacle = _mapping(config.get("obstacle_diagnostics"), "obstacle_diagnostics", required=False)
    _put(defaults, "obstacle_diagnostics_enabled", obstacle.get("enabled"))
    _put(defaults, "obstacle_diagnostics_mode", obstacle.get("mode"))
    _put(defaults, "obstacle_source", obstacle.get("obstacle_source"))
    _put(defaults, "obstacle_footprint_resolution", obstacle.get("footprint_resolution"))
    _put(defaults, "obstacle_footprint_inflation_radius", obstacle.get("footprint_inflation_radius"))
    _put(defaults, "obstacle_line_sample_step", obstacle.get("line_sample_step"))
    _put(defaults, "obstacle_blocked_path_penalty", obstacle.get("blocked_path_penalty"))

    actual_motion = _mapping(
        config.get("actual_base_motion_obstacle_diagnostics"),
        "actual_base_motion_obstacle_diagnostics",
        required=False,
    )
    _put(defaults, "actual_base_motion_obstacle_diagnostics_enabled", actual_motion.get("enabled"))
    _put(defaults, "actual_base_motion_obstacle_diagnostics_mode", actual_motion.get("mode"))
    _put(defaults, "actual_base_motion_obstacle_source", actual_motion.get("obstacle_source"))
    _put(defaults, "actual_base_motion_line_sample_step", actual_motion.get("line_sample_step"))
    _put(defaults, "actual_base_motion_min_motion_distance", actual_motion.get("min_motion_distance"))
    _put(defaults, "actual_base_motion_max_pairs_sample", actual_motion.get("max_pairs_sample"))
    actual_motion_debug = _mapping(
        actual_motion.get("debug_visualization"),
        "actual_base_motion_obstacle_diagnostics.debug_visualization",
        required=False,
    )
    _put(defaults, "actual_base_motion_debug_visualization_enabled", actual_motion_debug.get("enabled"))
    _put(defaults, "actual_base_motion_debug_visualization_draw_in_headless", actual_motion_debug.get("draw_in_headless"))
    _put(defaults, "actual_base_motion_debug_visualization_max_lines", actual_motion_debug.get("max_lines"))
    _put(defaults, "actual_base_motion_debug_visualization_line_width", actual_motion_debug.get("line_width"))

    obstacle_debug = _mapping(
        config.get("obstacle_debug_visualization"),
        "obstacle_debug_visualization",
        required=False,
    )
    _put(defaults, "obstacle_debug_visualization_enabled", obstacle_debug.get("enabled"))
    _put(defaults, "obstacle_debug_visualization_draw_in_headless", obstacle_debug.get("draw_in_headless"))
    _put(defaults, "obstacle_debug_visualization_line_source", obstacle_debug.get("line_source"))
    _put(defaults, "obstacle_debug_visualization_max_lines_per_robot", obstacle_debug.get("max_lines_per_robot"))
    _put(defaults, "obstacle_debug_visualization_max_total_lines", obstacle_debug.get("max_total_lines"))
    _put(
        defaults,
        "obstacle_debug_visualization_prefer_shortest_blocked_pairs",
        obstacle_debug.get("prefer_shortest_blocked_pairs"),
    )
    _put(defaults, "obstacle_debug_visualization_line_z_mode", obstacle_debug.get("line_z_mode"))
    _put(defaults, "obstacle_debug_visualization_line_z_value", obstacle_debug.get("line_z_value"))
    _put(defaults, "obstacle_debug_visualization_line_z_offset", obstacle_debug.get("line_z_offset"))
    _put(defaults, "obstacle_debug_visualization_line_width", obstacle_debug.get("line_width"))

    inter_robot = _mapping(
        config.get("inter_robot_conflict_diagnostics"),
        "inter_robot_conflict_diagnostics",
        required=False,
    )
    _put(defaults, "inter_robot_conflict_diagnostics_enabled", inter_robot.get("enabled"))
    _put(defaults, "inter_robot_conflict_diagnostics_mode", inter_robot.get("mode"))
    _put(defaults, "inter_robot_conflict_robot_footprint_radius", inter_robot.get("robot_footprint_radius"))
    _put(defaults, "inter_robot_conflict_safety_margin", inter_robot.get("safety_margin"))
    _put(defaults, "inter_robot_target_conflict_enabled", inter_robot.get("target_conflict_enabled"))
    _put(defaults, "inter_robot_target_conflict_radius", inter_robot.get("target_conflict_radius"))
    _put(defaults, "inter_robot_target_conflict_safety_margin", inter_robot.get("target_conflict_safety_margin"))
    inter_robot_debug = _mapping(
        inter_robot.get("debug_visualization"),
        "inter_robot_conflict_diagnostics.debug_visualization",
        required=False,
    )
    _put(defaults, "inter_robot_conflict_debug_visualization_enabled", inter_robot_debug.get("enabled"))
    _put(defaults, "inter_robot_conflict_debug_visualization_draw_in_headless", inter_robot_debug.get("draw_in_headless"))
    _put(defaults, "inter_robot_conflict_debug_visualization_max_lines", inter_robot_debug.get("max_lines"))
    _put(defaults, "inter_robot_conflict_debug_visualization_line_width", inter_robot_debug.get("line_width"))

    target_candidate = _mapping(
        config.get("selected_target_conflict_candidate_comparison"),
        "selected_target_conflict_candidate_comparison",
        required=False,
    )
    _put(defaults, "target_conflict_candidate_comparison_enabled", target_candidate.get("enabled"))
    _put(defaults, "target_conflict_candidate_comparison_mode", target_candidate.get("mode"))
    _put(defaults, "target_conflict_candidate_generator", target_candidate.get("candidate_generator"))
    _put(defaults, "target_conflict_candidate_robot_order", target_candidate.get("robot_order"))
    _put(defaults, "target_conflict_candidate_radius", target_candidate.get("target_conflict_radius"))
    _put(defaults, "target_conflict_candidate_safety_margin", target_candidate.get("target_conflict_safety_margin"))
    _put(defaults, "target_conflict_candidate_penalty", target_candidate.get("selected_target_conflict_penalty"))
    _put(defaults, "target_conflict_candidate_compare_methods", target_candidate.get("compare_methods"))
    _put(
        defaults,
        "target_conflict_candidate_include_random_as_baseline_only",
        target_candidate.get("include_random_as_baseline_only"),
    )
    _put(defaults, "target_conflict_candidate_max_pairs_sample", target_candidate.get("max_pairs_sample"))

    conflict_aware = _mapping(
        config.get("conflict_aware_baseline"),
        "conflict_aware_baseline",
        required=False,
    )
    _put(defaults, "conflict_aware_baseline_enabled", conflict_aware.get("enabled"))
    _put(defaults, "conflict_aware_baseline_methods", conflict_aware.get("methods"))
    _put(defaults, "conflict_aware_baseline_mode", conflict_aware.get("mode"))
    _put(defaults, "conflict_aware_baseline_top_k", conflict_aware.get("top_k"))
    _put(defaults, "conflict_aware_baseline_target_conflict_radius", conflict_aware.get("target_conflict_radius"))
    _put(
        defaults,
        "conflict_aware_baseline_target_conflict_safety_margin",
        conflict_aware.get("target_conflict_safety_margin"),
    )
    _put(defaults, "conflict_aware_baseline_target_conflict_penalty", conflict_aware.get("target_conflict_penalty"))
    _put(defaults, "conflict_aware_baseline_duplicate_penalty", conflict_aware.get("duplicate_penalty"))
    _put(defaults, "conflict_aware_baseline_fallback_to_base_method", conflict_aware.get("fallback_to_base_method"))
    _put(defaults, "conflict_aware_baseline_max_pairs_sample", conflict_aware.get("max_pairs_sample"))

    output = _mapping(config.get("output"), "output", required=False)
    _put(defaults, "result_file", output.get("result_file"))
    return defaults


def apply_scenario_config_to_env_cfg(env_cfg: Any, args: Namespace | Mapping[str, Any]) -> Any:
    """Apply loaded scenario defaults/CLI overrides to a ScanMobileManipulator env cfg."""

    getter = args.get if isinstance(args, Mapping) else lambda key, default=None: getattr(args, key, default)
    for attr in ("scenario_config_path", "scenario_name", "scenario_type"):
        value = getter(attr, None)
        if value is not None:
            setattr(env_cfg, attr, value)
    for attr in ENV_CFG_SCENARIO_ATTRS:
        value = getter(attr, None)
        if value is not None:
            if isinstance(value, list):
                value = tuple(value)
            setattr(env_cfg, attr, value)
    if bool(getter("align_base_center_to_world_origin", False)):
        env_cfg.component_mesh_align_base_center_to_world_origin = True
    return env_cfg


def mesh_bounds_defaults_from_config(config: Mapping[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    mesh = _mapping(config.get("component_mesh"), "component_mesh", required=False)
    _put(defaults, "mesh_path", mesh.get("path"))
    _put(defaults, "mesh_format", mesh.get("format"))
    _put(defaults, "mesh_unit", mesh.get("unit"))
    _put(defaults, "mesh_scale", mesh.get("scale"))
    _put(defaults, "mesh_position", mesh.get("position"))
    _put(defaults, "mesh_orientation", mesh.get("orientation"))
    _put(defaults, "mesh_orientation_format", mesh.get("orientation_format"))
    _put(defaults, "align_base_center_to_world_origin", mesh.get("align_base_center_to_world_origin"))

    proxy = _mapping(config.get("component_proxy"), "component_proxy", required=False)
    _put(defaults, "component_proxy_padding", proxy.get("padding"))

    output = _mapping(config.get("output"), "output", required=False)
    _put(defaults, "output_json", output.get("json_path") or output.get("output_json"))
    return defaults


def viewpoint_generation_defaults_from_config(config: Mapping[str, Any]) -> dict[str, Any]:
    defaults = mesh_bounds_defaults_from_config(config)
    proxy = _mapping(config.get("component_proxy"), "component_proxy", required=False)
    _put(defaults, "component_proxy_auto_from_mesh", proxy.get("auto_from_mesh"))

    generation = _mapping(config.get("viewpoint_generation"), "viewpoint_generation", required=False)
    _put(defaults, "viewpoint_distance", generation.get("viewpoint_distance"))
    _put(defaults, "num_height_layers", generation.get("num_height_layers"))
    _put(defaults, "points_per_side", generation.get("points_per_side"))
    _put(defaults, "include_top", generation.get("include_top"))

    output = _mapping(config.get("output"), "output", required=False)
    _put(defaults, "output_csv", output.get("csv_path") or output.get("output_csv"))
    _put(defaults, "output_json", output.get("json_path") or output.get("output_json"))
    return defaults


def validate_smoke_args(args: Namespace, *, repo_root: Path, config: Mapping[str, Any] | None = None) -> None:
    if config:
        _validate_viewpoint_metadata(config)
        _validate_robot_config_metadata(config, repo_root=repo_root)
        _validate_capability_config_metadata(config, repo_root=repo_root)
        _validate_visualization_metadata(config)
        _validate_obstacle_diagnostics_metadata(config)
        _validate_actual_base_motion_obstacle_diagnostics_metadata(config)
        _validate_obstacle_debug_visualization_metadata(config)
        _validate_inter_robot_conflict_diagnostics_metadata(config)
        _validate_target_conflict_candidate_comparison_metadata(config)
        _validate_conflict_aware_baseline_metadata(config)
    _validate_visual_mode_arg(
        getattr(args, "robot_visual_mode", None),
        label="visualization.robot_visual_mode",
        allowed=SUPPORTED_ROBOT_VISUAL_MODES,
    )
    _validate_visual_mode_arg(
        getattr(args, "component_visual_mode", None),
        label="visualization.component_visual_mode",
        allowed=SUPPORTED_COMPONENT_VISUAL_MODES,
    )
    proxy_type = getattr(args, "component_proxy_type", None)
    if proxy_type is not None and str(proxy_type).strip().lower() != "bbox":
        raise ValueError(f"Unsupported component_proxy.type={proxy_type!r}; only 'bbox' is supported.")
    _validate_common_mesh_args(
        mesh_path=getattr(args, "component_mesh_path", None),
        mesh_format=getattr(args, "component_mesh_format", None),
        mesh_unit=getattr(args, "component_mesh_unit", None),
        mesh_scale=getattr(args, "component_mesh_scale", None),
        mesh_position=getattr(args, "component_mesh_position", None),
        mesh_orientation=getattr(args, "component_mesh_orientation", None),
        mesh_orientation_format=getattr(args, "component_mesh_orientation_format", None),
        align_base_center_to_world_origin=getattr(args, "align_base_center_to_world_origin", False),
        component_proxy_auto_from_mesh=getattr(args, "component_proxy_auto_from_mesh", False),
        repo_root=repo_root,
        require_mesh_path=bool(getattr(args, "component_proxy_auto_from_mesh", False)),
    )
    csv_path = getattr(args, "viewpoint_csv_path", None)
    expect_num_viewpoints = getattr(args, "expect_num_viewpoints", None)
    if csv_path is not None:
        resolved_csv = resolve_path(csv_path, repo_root=repo_root, must_exist=True, label="viewpoints.csv_path")
        if expect_num_viewpoints is not None:
            loaded = load_fixed_viewpoint_csv(resolved_csv)
            if len(loaded.poses) != int(expect_num_viewpoints):
                raise ValueError(
                    f"viewpoints.expect_num_viewpoints mismatch for {resolved_csv}: "
                    f"expected {expect_num_viewpoints}, loaded {len(loaded.poses)}."
                )
    elif expect_num_viewpoints is not None:
        raise ValueError("expect_num_viewpoints requires viewpoint_csv_path; built-in fixed-12 has no CSV file.")
    robot_config_path = getattr(args, "robot_config_path", None)
    if robot_config_path is not None:
        resolve_path(robot_config_path, repo_root=repo_root, must_exist=True, label="robots.config_path")
    capability_config_path = getattr(args, "capability_config_path", None)
    if capability_config_path is not None:
        resolve_path(capability_config_path, repo_root=repo_root, must_exist=True, label="capabilities.config_path")
    _ensure_output_parent(getattr(args, "result_file", None), repo_root=repo_root, label="output.result_file")


def validate_generation_args(args: Namespace, *, repo_root: Path) -> None:
    _validate_common_mesh_args(
        mesh_path=getattr(args, "mesh_path", None),
        mesh_format=getattr(args, "mesh_format", None),
        mesh_unit=getattr(args, "mesh_unit", None),
        mesh_scale=getattr(args, "mesh_scale", None),
        mesh_position=getattr(args, "mesh_position", None),
        mesh_orientation=getattr(args, "mesh_orientation", None),
        mesh_orientation_format=getattr(args, "mesh_orientation_format", None),
        align_base_center_to_world_origin=getattr(args, "align_base_center_to_world_origin", False),
        component_proxy_auto_from_mesh=True,
        repo_root=repo_root,
        require_mesh_path=True,
    )
    _ensure_output_parent(getattr(args, "output_csv", None), repo_root=repo_root, label="output.csv_path", required=True)
    _ensure_output_parent(getattr(args, "output_json", None), repo_root=repo_root, label="output.json_path")


def validate_inspect_args(args: Namespace, *, repo_root: Path) -> None:
    _validate_common_mesh_args(
        mesh_path=getattr(args, "mesh_path", None),
        mesh_format=getattr(args, "mesh_format", None),
        mesh_unit=getattr(args, "mesh_unit", None),
        mesh_scale=getattr(args, "mesh_scale", None),
        mesh_position=getattr(args, "mesh_position", None),
        mesh_orientation=getattr(args, "mesh_orientation", None),
        mesh_orientation_format=getattr(args, "mesh_orientation_format", None),
        align_base_center_to_world_origin=getattr(args, "align_base_center_to_world_origin", False),
        component_proxy_auto_from_mesh=False,
        repo_root=repo_root,
        require_mesh_path=True,
    )
    _ensure_output_parent(getattr(args, "output_json", None), repo_root=repo_root, label="output.json_path")


def resolve_path(path_value: str | Path, *, repo_root: Path, must_exist: bool, label: str) -> Path:
    raw_path = Path(path_value).expanduser()
    candidates = [raw_path] if raw_path.is_absolute() else [Path.cwd() / raw_path, repo_root / raw_path]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    resolved = candidates[0].resolve()
    if must_exist:
        searched = ", ".join(str(candidate.resolve()) for candidate in candidates)
        raise FileNotFoundError(f"{label} does not exist. searched: {searched}")
    return resolved


def _validate_common_mesh_args(
    *,
    mesh_path: str | Path | None,
    mesh_format: str | None,
    mesh_unit: str | None,
    mesh_scale: Any,
    mesh_position: Any,
    mesh_orientation: Any,
    mesh_orientation_format: str | None,
    align_base_center_to_world_origin: bool,
    component_proxy_auto_from_mesh: bool,
    repo_root: Path,
    require_mesh_path: bool,
) -> None:
    if require_mesh_path or mesh_path is not None or component_proxy_auto_from_mesh:
        if mesh_path is None:
            raise ValueError("component_proxy.auto_from_mesh requires component_mesh.path.")
        resolve_path(mesh_path, repo_root=repo_root, must_exist=True, label="component_mesh.path")
    if mesh_format is not None and str(mesh_format).strip().lower() not in SUPPORTED_MESH_FORMATS:
        raise ValueError(f"Unsupported component_mesh.format={mesh_format!r}; only 'obj' is supported.")
    if mesh_unit is not None and str(mesh_unit).strip().lower() not in SUPPORTED_MESH_UNITS:
        raise ValueError(f"Unsupported component_mesh.unit={mesh_unit!r}; only 'mm' is supported.")
    if mesh_scale is not None:
        _validate_finite_sequence(mesh_scale, length=3, label="component_mesh.scale", positive=True)
    if mesh_orientation is not None:
        _validate_finite_sequence(mesh_orientation, length=4, label="component_mesh.orientation", positive=False)
    if mesh_orientation_format is not None and str(mesh_orientation_format).strip().lower() != SUPPORTED_ORIENTATION_FORMAT:
        raise ValueError(
            f"Unsupported component_mesh.orientation_format={mesh_orientation_format!r}; only 'qwxyz' is supported."
        )
    if align_base_center_to_world_origin and mesh_position is not None:
        raise ValueError(
            "component_mesh.align_base_center_to_world_origin cannot be combined with component_mesh.position. "
            "Use one world-origin convention at a time."
        )


def _validate_viewpoint_metadata(config: Mapping[str, Any]) -> None:
    viewpoints = _mapping(config.get("viewpoints"), "viewpoints", required=False)
    expected = {
        "format": VIEWPOINT_CSV_FORMAT,
        "frame": "world",
        "units": "meters",
    }
    for key, expected_value in expected.items():
        actual = viewpoints.get(key)
        if actual is not None and str(actual).strip() != expected_value:
            raise ValueError(f"Unsupported viewpoints.{key}={actual!r}; expected {expected_value!r}.")


def _validate_robot_config_metadata(config: Mapping[str, Any], *, repo_root: Path) -> None:
    robots = _mapping(config.get("robots"), "robots", required=False)
    config_path = robots.get("config_path")
    if config_path is not None:
        if not isinstance(config_path, (str, Path)):
            raise ValueError(f"robots.config_path must be a string path, got {config_path!r}.")
        resolve_path(config_path, repo_root=repo_root, must_exist=True, label="robots.config_path")


def _validate_visualization_metadata(config: Mapping[str, Any]) -> None:
    visualization = _mapping(config.get("visualization"), "visualization", required=False)
    _validate_visual_mode_arg(
        visualization.get("robot_visual_mode"),
        label="visualization.robot_visual_mode",
        allowed=SUPPORTED_ROBOT_VISUAL_MODES,
    )
    _validate_visual_mode_arg(
        visualization.get("component_visual_mode"),
        label="visualization.component_visual_mode",
        allowed=SUPPORTED_COMPONENT_VISUAL_MODES,
    )
    enabled = visualization.get("gui_camera_enabled")
    if enabled is not None and not isinstance(enabled, bool):
        raise ValueError(f"visualization.gui_camera_enabled must be boolean, got {enabled!r}.")
    grid_enabled = visualization.get("ground_grid_enabled")
    if grid_enabled is not None and not isinstance(grid_enabled, bool):
        raise ValueError(f"visualization.ground_grid_enabled must be boolean, got {grid_enabled!r}.")
    for key in ("gui_camera_eye", "gui_camera_target"):
        value = visualization.get(key)
        if value is not None:
            _validate_finite_sequence(value, length=3, label=f"visualization.{key}", positive=False)
    for key in ("ground_grid_half_extent", "ground_grid_spacing", "ground_grid_line_width"):
        value = visualization.get(key)
        if value is not None:
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(f"visualization.{key} must be a positive finite number, got {value!r}.")
    grid_z = visualization.get("ground_grid_z")
    if grid_z is not None and (not isinstance(grid_z, (int, float)) or not math.isfinite(float(grid_z))):
        raise ValueError(f"visualization.ground_grid_z must be finite, got {grid_z!r}.")


def _validate_visual_mode_arg(value: Any, *, label: str, allowed: set[str]) -> None:
    if value is None:
        return
    mode = str(value).strip().lower()
    if mode not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported {label}={value!r}; expected one of {{{allowed_text}}}.")


def _validate_capability_config_metadata(config: Mapping[str, Any], *, repo_root: Path) -> None:
    capabilities = _mapping(config.get("capabilities"), "capabilities", required=False)
    config_path = capabilities.get("config_path")
    if config_path is not None:
        if not isinstance(config_path, (str, Path)):
            raise ValueError(f"capabilities.config_path must be a string path, got {config_path!r}.")
        resolve_path(config_path, repo_root=repo_root, must_exist=True, label="capabilities.config_path")


def _validate_obstacle_diagnostics_metadata(config: Mapping[str, Any]) -> None:
    obstacle = _mapping(config.get("obstacle_diagnostics"), "obstacle_diagnostics", required=False)
    if not obstacle:
        return
    enabled = obstacle.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError(f"obstacle_diagnostics.enabled must be boolean, got {enabled!r}.")
    mode = obstacle.get("mode")
    if enabled:
        if str(mode).strip().lower() not in SUPPORTED_OBSTACLE_DIAGNOSTIC_MODES:
            raise ValueError(
                f"Unsupported obstacle_diagnostics.mode={mode!r}; expected one of "
                f"{sorted(SUPPORTED_OBSTACLE_DIAGNOSTIC_MODES)!r}."
            )
        source = obstacle.get("obstacle_source")
        if str(source).strip().lower() not in SUPPORTED_OBSTACLE_SOURCES:
            raise ValueError(
                f"Unsupported obstacle_diagnostics.obstacle_source={source!r}; expected one of "
                f"{sorted(SUPPORTED_OBSTACLE_SOURCES)!r}."
            )
        component_mesh = _mapping(config.get("component_mesh"), "component_mesh", required=False)
        if component_mesh.get("path") is None:
            raise ValueError(
                "obstacle_diagnostics with obstacle_source=component_mesh_footprint requires component_mesh.path."
            )
    for key, positive in (
        ("footprint_resolution", True),
        ("footprint_inflation_radius", False),
        ("line_sample_step", True),
        ("blocked_path_penalty", False),
    ):
        value = obstacle.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"obstacle_diagnostics.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"obstacle_diagnostics.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"obstacle_diagnostics.{key} must be positive, got {value!r}.")
        if not positive and numeric < 0.0:
            raise ValueError(f"obstacle_diagnostics.{key} must be non-negative, got {value!r}.")


def _validate_actual_base_motion_obstacle_diagnostics_metadata(config: Mapping[str, Any]) -> None:
    diagnostics = _mapping(
        config.get("actual_base_motion_obstacle_diagnostics"),
        "actual_base_motion_obstacle_diagnostics",
        required=False,
    )
    if not diagnostics:
        return
    enabled = diagnostics.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        raise ValueError(f"actual_base_motion_obstacle_diagnostics.enabled must be boolean, got {enabled!r}.")
    mode = diagnostics.get("mode")
    if diagnostics.get("enabled", False) and str(mode).strip().lower() not in SUPPORTED_OBSTACLE_DIAGNOSTIC_MODES:
        raise ValueError(
            f"Unsupported actual_base_motion_obstacle_diagnostics.mode={mode!r}; expected one of "
            f"{sorted(SUPPORTED_OBSTACLE_DIAGNOSTIC_MODES)!r}."
        )
    source = diagnostics.get("obstacle_source")
    if diagnostics.get("enabled", False) and str(source).strip().lower() not in SUPPORTED_OBSTACLE_SOURCES:
        raise ValueError(
            f"Unsupported actual_base_motion_obstacle_diagnostics.obstacle_source={source!r}; expected one of "
            f"{sorted(SUPPORTED_OBSTACLE_SOURCES)!r}."
        )
    if diagnostics.get("enabled", False):
        obstacle = _mapping(config.get("obstacle_diagnostics"), "obstacle_diagnostics", required=False)
        if not obstacle.get("enabled", False):
            raise ValueError(
                "actual_base_motion_obstacle_diagnostics requires obstacle_diagnostics.enabled=true so the "
                "component mesh footprint is available."
            )
        component_mesh = _mapping(config.get("component_mesh"), "component_mesh", required=False)
        if component_mesh.get("path") is None:
            raise ValueError(
                "actual_base_motion_obstacle_diagnostics with obstacle_source=component_mesh_footprint "
                "requires component_mesh.path."
            )
    for key, positive in (
        ("line_sample_step", True),
        ("min_motion_distance", False),
    ):
        value = diagnostics.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"actual_base_motion_obstacle_diagnostics.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"actual_base_motion_obstacle_diagnostics.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"actual_base_motion_obstacle_diagnostics.{key} must be positive, got {value!r}.")
        if not positive and numeric < 0.0:
            raise ValueError(f"actual_base_motion_obstacle_diagnostics.{key} must be non-negative, got {value!r}.")
    max_pairs = diagnostics.get("max_pairs_sample")
    if max_pairs is not None and (not isinstance(max_pairs, int) or max_pairs < 0):
        raise ValueError(
            "actual_base_motion_obstacle_diagnostics.max_pairs_sample must be a non-negative integer, "
            f"got {max_pairs!r}."
        )

    debug = _mapping(
        diagnostics.get("debug_visualization"),
        "actual_base_motion_obstacle_diagnostics.debug_visualization",
        required=False,
    )
    for key in ("enabled", "draw_in_headless"):
        value = debug.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(
                f"actual_base_motion_obstacle_diagnostics.debug_visualization.{key} must be boolean, got {value!r}."
            )
    max_lines = debug.get("max_lines")
    if max_lines is not None and (not isinstance(max_lines, int) or max_lines < 0):
        raise ValueError(
            "actual_base_motion_obstacle_diagnostics.debug_visualization.max_lines must be a non-negative integer, "
            f"got {max_lines!r}."
        )
    line_width = debug.get("line_width")
    if line_width is not None:
        try:
            numeric = float(line_width)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "actual_base_motion_obstacle_diagnostics.debug_visualization.line_width must be numeric, "
                f"got {line_width!r}."
            ) from exc
        if not math.isfinite(numeric) or numeric <= 0.0:
            raise ValueError(
                "actual_base_motion_obstacle_diagnostics.debug_visualization.line_width must be positive and finite, "
                f"got {line_width!r}."
            )


def _validate_obstacle_debug_visualization_metadata(config: Mapping[str, Any]) -> None:
    debug = _mapping(
        config.get("obstacle_debug_visualization"),
        "obstacle_debug_visualization",
        required=False,
    )
    if not debug:
        return
    for key in ("enabled", "draw_in_headless", "prefer_shortest_blocked_pairs"):
        value = debug.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"obstacle_debug_visualization.{key} must be boolean, got {value!r}.")
    source = debug.get("line_source")
    if source is not None and str(source).strip().lower() not in SUPPORTED_OBSTACLE_DEBUG_LINE_SOURCES:
        raise ValueError(
            f"Unsupported obstacle_debug_visualization.line_source={source!r}; expected one of "
            f"{sorted(SUPPORTED_OBSTACLE_DEBUG_LINE_SOURCES)!r}."
        )
    z_mode = debug.get("line_z_mode")
    if z_mode is not None and str(z_mode).strip().lower() not in SUPPORTED_OBSTACLE_DEBUG_LINE_Z_MODES:
        raise ValueError(
            f"Unsupported obstacle_debug_visualization.line_z_mode={z_mode!r}; expected one of "
            f"{sorted(SUPPORTED_OBSTACLE_DEBUG_LINE_Z_MODES)!r}."
        )
    for key in ("max_lines_per_robot", "max_total_lines"):
        value = debug.get(key)
        if value is None:
            continue
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"obstacle_debug_visualization.{key} must be a non-negative integer, got {value!r}.")
    for key, positive in (("line_z_value", False), ("line_z_offset", False), ("line_width", True)):
        value = debug.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"obstacle_debug_visualization.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"obstacle_debug_visualization.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"obstacle_debug_visualization.{key} must be positive, got {value!r}.")
        if not positive and key == "line_z_offset" and numeric < 0.0:
            raise ValueError(
                f"obstacle_debug_visualization.{key} must be finite and non-negative, got {value!r}."
            )


def _validate_inter_robot_conflict_diagnostics_metadata(config: Mapping[str, Any]) -> None:
    diagnostics = _mapping(
        config.get("inter_robot_conflict_diagnostics"),
        "inter_robot_conflict_diagnostics",
        required=False,
    )
    if not diagnostics:
        return
    for key in ("enabled", "target_conflict_enabled"):
        value = diagnostics.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"inter_robot_conflict_diagnostics.{key} must be boolean, got {value!r}.")
    mode = diagnostics.get("mode")
    if diagnostics.get("enabled", False) and str(mode).strip().lower() not in SUPPORTED_INTER_ROBOT_CONFLICT_MODES:
        raise ValueError(
            f"Unsupported inter_robot_conflict_diagnostics.mode={mode!r}; expected one of "
            f"{sorted(SUPPORTED_INTER_ROBOT_CONFLICT_MODES)!r}."
        )
    for key, positive in (
        ("robot_footprint_radius", True),
        ("safety_margin", False),
        ("target_conflict_radius", True),
        ("target_conflict_safety_margin", False),
    ):
        value = diagnostics.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"inter_robot_conflict_diagnostics.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"inter_robot_conflict_diagnostics.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"inter_robot_conflict_diagnostics.{key} must be positive, got {value!r}.")
        if not positive and numeric < 0.0:
            raise ValueError(f"inter_robot_conflict_diagnostics.{key} must be non-negative, got {value!r}.")

    debug = _mapping(
        diagnostics.get("debug_visualization"),
        "inter_robot_conflict_diagnostics.debug_visualization",
        required=False,
    )
    for key in ("enabled", "draw_in_headless"):
        value = debug.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"inter_robot_conflict_diagnostics.debug_visualization.{key} must be boolean, got {value!r}.")
    max_lines = debug.get("max_lines")
    if max_lines is not None and (not isinstance(max_lines, int) or max_lines < 0):
        raise ValueError(
            f"inter_robot_conflict_diagnostics.debug_visualization.max_lines must be a non-negative integer, got {max_lines!r}."
        )
    line_width = debug.get("line_width")
    if line_width is not None:
        try:
            numeric = float(line_width)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "inter_robot_conflict_diagnostics.debug_visualization.line_width must be numeric, "
                f"got {line_width!r}."
            ) from exc
        if not math.isfinite(numeric) or numeric <= 0.0:
            raise ValueError(
                "inter_robot_conflict_diagnostics.debug_visualization.line_width must be positive and finite, "
                f"got {line_width!r}."
            )


def _validate_target_conflict_candidate_comparison_metadata(config: Mapping[str, Any]) -> None:
    candidate = _mapping(
        config.get("selected_target_conflict_candidate_comparison"),
        "selected_target_conflict_candidate_comparison",
        required=False,
    )
    if not candidate:
        return
    for key in ("enabled", "include_random_as_baseline_only"):
        value = candidate.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"selected_target_conflict_candidate_comparison.{key} must be boolean, got {value!r}.")
    mode = candidate.get("mode")
    if candidate.get("enabled", False) and str(mode).strip().lower() not in SUPPORTED_TARGET_CONFLICT_CANDIDATE_COMPARISON_MODES:
        raise ValueError(
            f"Unsupported selected_target_conflict_candidate_comparison.mode={mode!r}; expected one of "
            f"{sorted(SUPPORTED_TARGET_CONFLICT_CANDIDATE_COMPARISON_MODES)!r}."
        )
    generator = candidate.get("candidate_generator")
    if generator is not None and str(generator).strip().lower() not in SUPPORTED_TARGET_CONFLICT_CANDIDATE_GENERATORS:
        raise ValueError(
            f"Unsupported selected_target_conflict_candidate_comparison.candidate_generator={generator!r}; "
            f"expected one of {sorted(SUPPORTED_TARGET_CONFLICT_CANDIDATE_GENERATORS)!r}."
        )
    robot_order = candidate.get("robot_order")
    if robot_order is not None and str(robot_order).strip().lower() not in SUPPORTED_TARGET_CONFLICT_ROBOT_ORDERS:
        raise ValueError(
            f"Unsupported selected_target_conflict_candidate_comparison.robot_order={robot_order!r}; "
            f"expected one of {sorted(SUPPORTED_TARGET_CONFLICT_ROBOT_ORDERS)!r}."
        )
    compare_methods = candidate.get("compare_methods")
    if compare_methods is not None:
        if not isinstance(compare_methods, (list, tuple)):
            raise ValueError(
                "selected_target_conflict_candidate_comparison.compare_methods must be a list of method names, "
                f"got {compare_methods!r}."
            )
        unsupported = [
            str(method)
            for method in compare_methods
            if str(method).strip().lower() not in SUPPORTED_TARGET_CONFLICT_COMPARE_METHODS
        ]
        if unsupported:
            raise ValueError(
                "selected_target_conflict_candidate_comparison.compare_methods contains unsupported methods: "
                f"{unsupported!r}; expected subset of {sorted(SUPPORTED_TARGET_CONFLICT_COMPARE_METHODS)!r}."
            )
    for key, positive in (
        ("target_conflict_radius", True),
        ("target_conflict_safety_margin", False),
        ("selected_target_conflict_penalty", False),
    ):
        value = candidate.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"selected_target_conflict_candidate_comparison.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"selected_target_conflict_candidate_comparison.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"selected_target_conflict_candidate_comparison.{key} must be positive, got {value!r}.")
        if not positive and numeric < 0.0:
            raise ValueError(f"selected_target_conflict_candidate_comparison.{key} must be non-negative, got {value!r}.")
    max_pairs = candidate.get("max_pairs_sample")
    if max_pairs is not None and (not isinstance(max_pairs, int) or max_pairs < 0):
        raise ValueError(
            "selected_target_conflict_candidate_comparison.max_pairs_sample must be a non-negative integer, "
            f"got {max_pairs!r}."
        )


def _validate_conflict_aware_baseline_metadata(config: Mapping[str, Any]) -> None:
    conflict_aware = _mapping(config.get("conflict_aware_baseline"), "conflict_aware_baseline", required=False)
    if not conflict_aware:
        return
    for key in ("enabled", "fallback_to_base_method"):
        value = conflict_aware.get(key)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"conflict_aware_baseline.{key} must be boolean, got {value!r}.")
    mode = conflict_aware.get("mode")
    if conflict_aware.get("enabled", False) and str(mode).strip().lower() not in SUPPORTED_CONFLICT_AWARE_BASELINE_MODES:
        raise ValueError(
            f"Unsupported conflict_aware_baseline.mode={mode!r}; expected one of "
            f"{sorted(SUPPORTED_CONFLICT_AWARE_BASELINE_MODES)!r}."
        )
    methods = conflict_aware.get("methods")
    if methods is not None:
        if not isinstance(methods, (list, tuple)):
            raise ValueError(f"conflict_aware_baseline.methods must be a list of method names, got {methods!r}.")
        unsupported = [
            str(method)
            for method in methods
            if str(method).strip().lower() not in SUPPORTED_CONFLICT_AWARE_BASELINE_METHODS
        ]
        if unsupported:
            raise ValueError(
                f"conflict_aware_baseline.methods contains unsupported methods: {unsupported!r}; expected subset of "
                f"{sorted(SUPPORTED_CONFLICT_AWARE_BASELINE_METHODS)!r}."
            )
    top_k = conflict_aware.get("top_k")
    if top_k is not None and (not isinstance(top_k, int) or top_k <= 0):
        raise ValueError(f"conflict_aware_baseline.top_k must be a positive integer, got {top_k!r}.")
    for key, positive in (
        ("target_conflict_radius", True),
        ("target_conflict_safety_margin", False),
        ("target_conflict_penalty", False),
        ("duplicate_penalty", False),
    ):
        value = conflict_aware.get(key)
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"conflict_aware_baseline.{key} must be numeric, got {value!r}.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"conflict_aware_baseline.{key} must be finite, got {value!r}.")
        if positive and numeric <= 0.0:
            raise ValueError(f"conflict_aware_baseline.{key} must be positive, got {value!r}.")
        if not positive and numeric < 0.0:
            raise ValueError(f"conflict_aware_baseline.{key} must be non-negative, got {value!r}.")
    max_pairs = conflict_aware.get("max_pairs_sample")
    if max_pairs is not None and (not isinstance(max_pairs, int) or max_pairs < 0):
        raise ValueError(
            f"conflict_aware_baseline.max_pairs_sample must be a non-negative integer, got {max_pairs!r}."
        )


def _validate_finite_sequence(value: Any, *, length: int, label: str, positive: bool) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list/tuple of {length} finite numbers, got {value!r}.")
    if len(value) != length:
        raise ValueError(f"{label} must contain {length} values, got {len(value)}: {value!r}.")
    try:
        values = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain finite numbers, got {value!r}.") from exc
    if not all(math.isfinite(item) for item in values):
        raise ValueError(f"{label} must contain finite numbers, got {value!r}.")
    if positive and any(item <= 0.0 for item in values):
        raise ValueError(f"{label} values must be positive, got {value!r}.")
    return values


def _ensure_output_parent(
    path_value: str | Path | None,
    *,
    repo_root: Path,
    label: str,
    required: bool = False,
) -> None:
    if path_value is None:
        if required:
            raise ValueError(f"{label} is required.")
        return
    output_path = resolve_path(path_value, repo_root=repo_root, must_exist=False, label=label)
    output_path.parent.mkdir(parents=True, exist_ok=True)


def _mapping(value: Any, label: str, *, required: bool) -> Mapping[str, Any]:
    if value is None:
        if required:
            raise ValueError(f"scenario_config requires a {label} mapping.")
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"scenario_config {label} must be a mapping, got {type(value).__name__}.")
    return value


def _put(defaults: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        defaults[key] = value
