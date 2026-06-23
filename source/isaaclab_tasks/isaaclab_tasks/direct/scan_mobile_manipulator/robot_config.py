"""Robot configuration loading for the scan-mobile-manipulator Robot Config MVP."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal Python envs.
    yaml = None


REQUIRED_ROBOT_FIELDS = (
    "name",
    "enabled",
    "model_type",
    "initial_pose_world",
    "capability_profile",
    "speed_weight",
    "cost_weight",
)


@dataclass(frozen=True)
class RobotSpec:
    """Validated robot entry from a robot config YAML file."""

    name: str
    enabled: bool
    model_type: str
    initial_pose_world: tuple[float, float, float, float, float, float, float]
    capability_profile: str
    speed_weight: float
    cost_weight: float
    source_index: int
    visual_usd_path: str | None = None
    visual_mesh_path: str | None = None
    visual_mesh_scale: tuple[float, float, float] | None = None
    visual_mesh_position_offset: tuple[float, float, float] | None = None
    visual_mesh_yaw_offset: float | None = None
    visual_mesh_align_bottom_to_proxy_z: bool = False


@dataclass(frozen=True)
class RobotConfig:
    """Validated robot config with deterministic enabled-agent mapping."""

    config_path: Path
    robots: tuple[RobotSpec, ...]
    enabled_robots: tuple[RobotSpec, ...]
    agent_id_by_name: dict[str, int]

    def to_diagnostics(self) -> dict[str, object]:
        enabled = self.enabled_robots
        return {
            "robot_config_path": str(self.config_path),
            "num_configured_robots": len(self.robots),
            "num_enabled_robots": len(enabled),
            "enabled_robot_names": [robot.name for robot in enabled],
            "agent_id_by_name": dict(self.agent_id_by_name),
            "model_type_by_robot": {robot.name: robot.model_type for robot in enabled},
            "capability_profile_by_robot": {robot.name: robot.capability_profile for robot in enabled},
            "speed_weight_by_robot": {robot.name: robot.speed_weight for robot in enabled},
            "cost_weight_by_robot": {robot.name: robot.cost_weight for robot in enabled},
            "initial_pose_world_by_robot": {
                robot.name: list(robot.initial_pose_world) for robot in enabled
            },
            "visual_usd_path_by_robot": {robot.name: robot.visual_usd_path for robot in enabled},
            "visual_mesh_path_by_robot": {robot.name: robot.visual_mesh_path for robot in enabled},
            "visual_mesh_scale_by_robot": {
                robot.name: list(robot.visual_mesh_scale) if robot.visual_mesh_scale is not None else None
                for robot in enabled
            },
            "visual_mesh_position_offset_by_robot": {
                robot.name: (
                    list(robot.visual_mesh_position_offset)
                    if robot.visual_mesh_position_offset is not None
                    else None
                )
                for robot in enabled
            },
            "visual_mesh_yaw_offset_by_robot": {
                robot.name: robot.visual_mesh_yaw_offset for robot in enabled
            },
            "visual_mesh_align_bottom_to_proxy_z_by_robot": {
                robot.name: robot.visual_mesh_align_bottom_to_proxy_z for robot in enabled
            },
        }


def load_robot_config(config_path: str | Path, *, base_dir: str | Path | None = None) -> RobotConfig:
    """Load and validate a robot config YAML file.

    Relative paths are resolved using the current working directory first and
    then ``base_dir`` when provided, matching the scenario config path style.
    """

    resolved_path = _resolve_config_path(config_path, base_dir=base_dir)
    data = _load_yaml_mapping(resolved_path)
    robots_value = data.get("robots")
    if robots_value is None:
        raise ValueError(f"robot config requires top-level 'robots' key: {resolved_path}")
    if not isinstance(robots_value, list) or not robots_value:
        raise ValueError(f"robot config 'robots' must be a non-empty list: {resolved_path}")

    seen_names: set[str] = set()
    robots: list[RobotSpec] = []
    for index, entry in enumerate(robots_value):
        if not isinstance(entry, Mapping):
            raise ValueError(f"robots[{index}] must be a mapping/object, got {type(entry).__name__}.")
        missing = [field for field in REQUIRED_ROBOT_FIELDS if field not in entry]
        if missing:
            raise ValueError(f"robots[{index}] is missing required field(s): {', '.join(missing)}.")

        name = _non_empty_string(entry["name"], label=f"robots[{index}].name")
        if name in seen_names:
            raise ValueError(f"robot names must be unique; duplicate name {name!r} at robots[{index}].")
        seen_names.add(name)

        enabled = entry["enabled"]
        if not isinstance(enabled, bool):
            raise ValueError(f"robots[{index}].enabled must be boolean, got {enabled!r}.")

        robots.append(
            RobotSpec(
                name=name,
                enabled=enabled,
                model_type=_non_empty_string(entry["model_type"], label=f"robots[{index}].model_type"),
                initial_pose_world=_numeric_tuple(
                    entry["initial_pose_world"],
                    length=7,
                    label=f"robots[{index}].initial_pose_world",
                ),
                capability_profile=_non_empty_string(
                    entry["capability_profile"],
                    label=f"robots[{index}].capability_profile",
                ),
                speed_weight=_positive_float(entry["speed_weight"], label=f"robots[{index}].speed_weight"),
                cost_weight=_positive_float(entry["cost_weight"], label=f"robots[{index}].cost_weight"),
                source_index=index,
                visual_usd_path=_optional_non_empty_string(
                    entry.get("visual_usd_path"),
                    label=f"robots[{index}].visual_usd_path",
                ),
                visual_mesh_path=_optional_non_empty_string(
                    entry.get("visual_mesh_path"),
                    label=f"robots[{index}].visual_mesh_path",
                ),
                visual_mesh_scale=_optional_numeric_tuple(
                    entry.get("visual_mesh_scale"),
                    length=3,
                    label=f"robots[{index}].visual_mesh_scale",
                ),
                visual_mesh_position_offset=_optional_numeric_tuple(
                    entry.get("visual_mesh_position_offset"),
                    length=3,
                    label=f"robots[{index}].visual_mesh_position_offset",
                ),
                visual_mesh_yaw_offset=_optional_float(
                    entry.get("visual_mesh_yaw_offset"),
                    label=f"robots[{index}].visual_mesh_yaw_offset",
                ),
                visual_mesh_align_bottom_to_proxy_z=_optional_bool(
                    entry.get("visual_mesh_align_bottom_to_proxy_z"),
                    default=False,
                    label=f"robots[{index}].visual_mesh_align_bottom_to_proxy_z",
                ),
            )
        )

    robots_tuple = tuple(robots)
    enabled_robots = tuple(robot for robot in robots_tuple if robot.enabled)
    agent_id_by_name = {robot.name: agent_id for agent_id, robot in enumerate(enabled_robots)}
    return RobotConfig(
        config_path=resolved_path,
        robots=robots_tuple,
        enabled_robots=enabled_robots,
        agent_id_by_name=agent_id_by_name,
    )


def _load_yaml_mapping(path: Path) -> Mapping[str, Any]:
    if yaml is None:
        raise RuntimeError(
            f"PyYAML is not available, so robot configs cannot be loaded: {path}. "
            "Install/use an environment with PyYAML."
        )
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        raise ValueError(f"robot config is empty: {path}")
    if not isinstance(data, Mapping):
        raise ValueError(f"robot config must contain a mapping/object at top level: {path}")
    return data


def _resolve_config_path(config_path: str | Path, *, base_dir: str | Path | None) -> Path:
    if not isinstance(config_path, (str, Path)):
        raise ValueError(f"robot config path must be a string or Path, got {config_path!r}.")
    raw_path = Path(config_path).expanduser()
    candidates: list[Path]
    if raw_path.is_absolute():
        candidates = [raw_path]
    else:
        candidates = [Path.cwd() / raw_path]
        if base_dir is not None:
            if not isinstance(base_dir, (str, Path)):
                raise ValueError(f"base_dir must be a string or Path when provided, got {base_dir!r}.")
            base_path = Path(base_dir).expanduser()
            if base_path.exists() and base_path.is_file():
                base_path = base_path.parent
            elif base_path.suffix:
                base_path = base_path.parent
            candidates.append(base_path / raw_path)

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            unique_candidates.append(resolved)
            seen.add(resolved)
    for resolved in unique_candidates:
        if resolved.exists():
            if not resolved.is_file():
                raise FileNotFoundError(f"robot config path is not a file: {resolved}")
            return resolved

    searched = ", ".join(str(candidate) for candidate in unique_candidates)
    raise FileNotFoundError(f"robot config does not exist. searched: {searched}")


def _non_empty_string(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string, got {value!r}.")
    return value.strip()


def _optional_non_empty_string(value: Any, *, label: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, label=label)


def _numeric_tuple(value: Any, *, length: int, label: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list/tuple of {length} finite numbers, got {value!r}.")
    if len(value) != length:
        raise ValueError(f"{label} must contain {length} values, got {len(value)}: {value!r}.")
    values: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{label} must contain numeric values, got {value!r}.")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"{label} must contain finite numbers, got {value!r}.")
        values.append(number)
    return tuple(values)


def _optional_numeric_tuple(value: Any, *, length: int, label: str) -> tuple[float, ...] | None:
    if value is None:
        return None
    return _numeric_tuple(value, length=length, label=label)


def _optional_float(value: Any, *, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number, got {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number, got {value!r}.")
    return number


def _optional_bool(value: Any, *, default: bool, label: str) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean, got {value!r}.")
    return value


def _positive_float(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive finite number, got {value!r}.")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be a positive finite number, got {value!r}.")
    return number


def _main() -> int:
    parser = argparse.ArgumentParser(description="Load a robot config YAML and print diagnostics as JSON.")
    parser.add_argument("config_path", type=str, help="Path to robots.yaml.")
    parser.add_argument(
        "--base_dir",
        type=str,
        default=None,
        help="Optional base directory used after the current working directory for relative paths.",
    )
    args = parser.parse_args()
    config = load_robot_config(args.config_path, base_dir=args.base_dir)
    print(json.dumps(config.to_diagnostics(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
