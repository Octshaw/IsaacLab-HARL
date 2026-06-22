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
    _put(defaults, "task", config.get("task"))
    _put(defaults, "num_envs", config.get("num_envs"))
    _put(defaults, "max_steps", config.get("max_steps"))
    _put(defaults, "seed", config.get("seed"))
    _put(defaults, "headless", config.get("headless"))
    _put(defaults, "device", config.get("device"))
    _put(defaults, "disable_fabric", config.get("disable_fabric"))
    _put(defaults, "viewpoint_candidate_top_k", config.get("viewpoint_candidate_top_k"))

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

    assignment = _mapping(config.get("assignment"), "assignment", required=False)
    _put(defaults, "viewpoint_candidate_top_k", assignment.get("viewpoint_candidate_top_k"))

    output = _mapping(config.get("output"), "output", required=False)
    _put(defaults, "result_file", output.get("result_file"))
    return defaults


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
