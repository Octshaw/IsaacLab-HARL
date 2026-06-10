"""Unit-style checks for OBJ component mesh bounds."""

from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

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

from component_mesh import compute_base_center_alignment_translation, compute_component_mesh_bounds  # noqa: E402


def _write_box_obj(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "v 0 0 0",
                "v 2000 0 0",
                "v 0 1000 0",
                "v 2000 1000 0",
                "v 0 0 500",
                "v 2000 0 500",
                "v 0 1000 500",
                "v 2000 1000 500",
                "f 1 2 4 3",
                "f 5 7 8 6",
                "f 1 5 6 2",
                "f 3 4 8 7",
                "f 1 3 7 5",
                "f 2 6 8 4",
            )
        ),
        encoding="utf-8",
    )


def _assert_close(actual, expected, *, label: str, tol: float = 1.0e-6) -> None:
    if len(actual) != len(expected):
        raise AssertionError(f"{label} length mismatch: {actual!r} vs {expected!r}")
    for index, (a_value, e_value) in enumerate(zip(actual, expected)):
        if abs(a_value - e_value) > tol:
            raise AssertionError(f"{label}[{index}] expected {e_value}, got {a_value}")


def _expect_raises(label: str, func, expected_text: str) -> None:
    try:
        func()
    except Exception as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"{label} raised {type(exc).__name__}, but message lacked {expected_text!r}: {exc}")
        return
    raise AssertionError(f"{label} did not raise")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        obj_path = tmp_path / "box.obj"
        _write_box_obj(obj_path)

        identity = compute_component_mesh_bounds(mesh_path=obj_path)
        _assert_close(identity.raw_bounds_obj_units_min, (0.0, 0.0, 0.0), label="identity raw min")
        _assert_close(identity.raw_bounds_obj_units_max, (2000.0, 1000.0, 500.0), label="identity raw max")
        _assert_close(identity.scaled_local_bounds_m_min, (0.0, 0.0, 0.0), label="identity scaled min")
        _assert_close(identity.scaled_local_bounds_m_max, (2.0, 1.0, 0.5), label="identity scaled max")
        _assert_close(identity.auto_component_proxy_center, (1.0, 0.5, 0.25), label="identity center")
        _assert_close(identity.auto_component_proxy_half_extents, (1.0, 0.5, 0.25), label="identity half extents")

        translated = compute_component_mesh_bounds(mesh_path=obj_path, mesh_position=(10.0, 20.0, 30.0))
        _assert_close(translated.auto_component_proxy_center, (11.0, 20.5, 30.25), label="translated center")
        _assert_close(translated.auto_component_proxy_half_extents, (1.0, 0.5, 0.25), label="translated half extents")

        qz_90 = (math.sqrt(0.5), 0.0, 0.0, math.sqrt(0.5))
        rotated = compute_component_mesh_bounds(mesh_path=obj_path, mesh_orientation=qz_90)
        _assert_close(rotated.world_bounds_m_min, (-1.0, 0.0, 0.0), label="rotated world min")
        _assert_close(rotated.world_bounds_m_max, (0.0, 2.0, 0.5), label="rotated world max")
        _assert_close(rotated.auto_component_proxy_center, (-0.5, 1.0, 0.25), label="rotated center")
        _assert_close(rotated.auto_component_proxy_half_extents, (0.5, 1.0, 0.25), label="rotated half extents")

        alignment = compute_base_center_alignment_translation(mesh_path=obj_path)
        _assert_close(
            alignment.base_center_before_translation,
            (1.0, 0.5, 0.0),
            label="base-center before translation",
        )
        _assert_close(alignment.auto_translation, (-1.0, -0.5, -0.0), label="base-center auto translation")
        aligned = compute_component_mesh_bounds(mesh_path=obj_path, mesh_position=alignment.auto_translation)
        _assert_close(aligned.world_bounds_m_min, (-1.0, -0.5, 0.0), label="aligned world min")
        _assert_close(aligned.world_bounds_m_max, (1.0, 0.5, 0.5), label="aligned world max")

        missing_path = tmp_path / "missing.obj"
        _expect_raises(
            "missing file",
            lambda: compute_component_mesh_bounds(mesh_path=missing_path),
            "does not exist",
        )

        no_vertices = tmp_path / "no_vertices.obj"
        no_vertices.write_text("f 1 2 3\n", encoding="utf-8")
        _expect_raises(
            "no vertices",
            lambda: compute_component_mesh_bounds(mesh_path=no_vertices),
            "no valid vertex rows",
        )

        invalid_values = tmp_path / "invalid_values.obj"
        invalid_values.write_text("v nan 0 0\n", encoding="utf-8")
        _expect_raises(
            "invalid values",
            lambda: compute_component_mesh_bounds(mesh_path=invalid_values),
            "non-finite",
        )

        _expect_raises(
            "unsupported unit",
            lambda: compute_component_mesh_bounds(mesh_path=obj_path, mesh_unit="cm"),
            "Unsupported component_mesh_unit",
        )
        _expect_raises(
            "unsupported orientation format",
            lambda: compute_component_mesh_bounds(mesh_path=obj_path, mesh_orientation_format="xyzw"),
            "Unsupported component_mesh_orientation_format",
        )

    print("[OK] component mesh bounds tests passed")


if __name__ == "__main__":
    main()
