"""YAML loader for task-space proxy capability profiles."""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal Python envs.
    yaml = None


DEFAULT_CAPABILITY_CONFIG_PATH = (
    Path(__file__).resolve().parent / "configs" / "capabilities" / "mobile_scanner_profiles.yaml"
)

_REQUIRED_FIELDS = (
    "scanner_start_offset",
    "arm_reach",
    "scanner_min_range",
    "scanner_max_range",
    "scanner_fov_deg",
    "scan_pos_tolerance",
    "scan_rot_tolerance",
    "max_base_xy_step",
    "max_base_yaw_step",
    "max_ee_xyz_step",
    "max_ee_rpy_step",
)


@dataclass(frozen=True)
class CapabilityProfile:
    """Validated task-space proxy capability profile."""

    name: str
    scanner_start_offset: tuple[float, float, float]
    arm_reach: float
    scanner_min_range: float
    scanner_max_range: float
    scanner_fov_deg: float
    scan_pos_tolerance: float
    scan_rot_tolerance: float
    max_base_xy_step: float
    max_base_yaw_step: float
    max_ee_xyz_step: float
    max_ee_rpy_step: float

    def to_dict(self) -> dict[str, object]:
        return {
            "scanner_start_offset": list(self.scanner_start_offset),
            "arm_reach": self.arm_reach,
            "scanner_min_range": self.scanner_min_range,
            "scanner_max_range": self.scanner_max_range,
            "scanner_fov_deg": self.scanner_fov_deg,
            "scan_pos_tolerance": self.scan_pos_tolerance,
            "scan_rot_tolerance": self.scan_rot_tolerance,
            "max_base_xy_step": self.max_base_xy_step,
            "max_base_yaw_step": self.max_base_yaw_step,
            "max_ee_xyz_step": self.max_ee_xyz_step,
            "max_ee_rpy_step": self.max_ee_rpy_step,
        }


@dataclass(frozen=True)
class CapabilityConfig:
    """Validated collection of capability profiles loaded from YAML."""

    config_path: Path
    profiles: dict[str, CapabilityProfile]

    def to_diagnostics(self) -> dict[str, object]:
        return {
            "capability_config_path": str(self.config_path),
            "capability_profile_names": list(self.profiles.keys()),
            "capability_profiles": {
                profile_name: profile.to_dict() for profile_name, profile in self.profiles.items()
            },
        }


def load_capability_profiles(
    config_path: str | Path | None = None,
    *,
    base_dir: str | Path | None = None,
) -> CapabilityConfig:
    """Load and validate capability profiles from YAML.

    When ``config_path`` is omitted, the repo-local default mobile scanner profile file is used. Relative paths are
    resolved against ``base_dir`` first, then against the current working directory.
    """

    resolved_path = _resolve_config_path(config_path, base_dir=base_dir)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Capability profile config does not exist: {resolved_path}")
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Capability profile config path is not a file: {resolved_path}")
    if yaml is None:
        raise RuntimeError(
            f"PyYAML is required to load capability profile YAML but is not available: {resolved_path}"
        )

    with resolved_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise ValueError(f"Capability profile config must contain a mapping at top level: {resolved_path}")

    raw_profiles = data.get("capability_profiles")
    if not isinstance(raw_profiles, Mapping) or not raw_profiles:
        raise ValueError(f"Capability profile config must define non-empty 'capability_profiles': {resolved_path}")

    profiles: dict[str, CapabilityProfile] = {}
    for profile_name, raw_profile in raw_profiles.items():
        name = _validate_profile_name(profile_name)
        if name in profiles:
            raise ValueError(f"Duplicate capability profile name {name!r} in {resolved_path}")
        profiles[name] = _parse_profile(name, raw_profile, config_path=resolved_path)

    return CapabilityConfig(config_path=resolved_path, profiles=profiles)


def _resolve_config_path(config_path: str | Path | None, *, base_dir: str | Path | None) -> Path:
    if config_path is None:
        return DEFAULT_CAPABILITY_CONFIG_PATH.resolve()

    raw_path = Path(config_path).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()

    candidates = []
    if base_dir is not None:
        candidates.append(Path(base_dir).expanduser() / raw_path)
    candidates.append(Path.cwd() / raw_path)
    candidates.append(DEFAULT_CAPABILITY_CONFIG_PATH.parent.parent.parent / raw_path)

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return candidates[0].resolve()


def _validate_profile_name(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Capability profile names must be non-empty strings, got {value!r}")
    return value.strip()


def _parse_profile(name: str, raw_profile: object, *, config_path: Path) -> CapabilityProfile:
    if not isinstance(raw_profile, Mapping):
        raise ValueError(
            f"capability_profiles.{name} must be a mapping in {config_path}, got {type(raw_profile).__name__}."
        )
    missing = [field for field in _REQUIRED_FIELDS if field not in raw_profile]
    if missing:
        raise ValueError(f"capability_profiles.{name} missing required fields {missing!r} in {config_path}.")

    scanner_min_range = _finite_positive_float(raw_profile["scanner_min_range"], label=f"{name}.scanner_min_range")
    scanner_max_range = _finite_positive_float(raw_profile["scanner_max_range"], label=f"{name}.scanner_max_range")
    if scanner_max_range <= scanner_min_range:
        raise ValueError(
            f"{name}.scanner_max_range must be greater than scanner_min_range, "
            f"got min={scanner_min_range} max={scanner_max_range}."
        )

    return CapabilityProfile(
        name=name,
        scanner_start_offset=_finite_float_tuple(
            raw_profile["scanner_start_offset"],
            label=f"{name}.scanner_start_offset",
            length=3,
            positive=False,
        ),
        arm_reach=_finite_positive_float(raw_profile["arm_reach"], label=f"{name}.arm_reach"),
        scanner_min_range=scanner_min_range,
        scanner_max_range=scanner_max_range,
        scanner_fov_deg=_finite_positive_float(raw_profile["scanner_fov_deg"], label=f"{name}.scanner_fov_deg"),
        scan_pos_tolerance=_finite_positive_float(
            raw_profile["scan_pos_tolerance"], label=f"{name}.scan_pos_tolerance"
        ),
        scan_rot_tolerance=_finite_positive_float(
            raw_profile["scan_rot_tolerance"], label=f"{name}.scan_rot_tolerance"
        ),
        max_base_xy_step=_finite_positive_float(
            raw_profile["max_base_xy_step"], label=f"{name}.max_base_xy_step"
        ),
        max_base_yaw_step=_finite_positive_float(
            raw_profile["max_base_yaw_step"], label=f"{name}.max_base_yaw_step"
        ),
        max_ee_xyz_step=_finite_positive_float(raw_profile["max_ee_xyz_step"], label=f"{name}.max_ee_xyz_step"),
        max_ee_rpy_step=_finite_positive_float(raw_profile["max_ee_rpy_step"], label=f"{name}.max_ee_rpy_step"),
    )


def _finite_positive_float(value: object, *, label: str) -> float:
    number = _finite_float(value, label=label)
    if number <= 0.0:
        raise ValueError(f"{label} must be positive, got {value!r}.")
    return number


def _finite_float(value: object, *, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number, got {value!r}.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number, got {value!r}.")
    return number


def _finite_float_tuple(value: object, *, label: str, length: int, positive: bool) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list/tuple of {length} finite numbers, got {value!r}.")
    if len(value) != length:
        raise ValueError(f"{label} must contain {length} values, got {len(value)}: {value!r}.")
    values = tuple(_finite_float(item, label=f"{label}[{index}]") for index, item in enumerate(value))
    if positive and any(item <= 0.0 for item in values):
        raise ValueError(f"{label} values must be positive, got {value!r}.")
    return values


def _main(argv: list[str]) -> int:
    config_path = argv[1] if len(argv) > 1 else None
    config = load_capability_profiles(config_path)
    print(json.dumps(config.to_diagnostics(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
