"""Inspect transformed OBJ mesh bounds for the scan component proxy."""

from __future__ import annotations

import argparse
import json
import sys
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
from scenario_config import load_scenario_config, mesh_bounds_defaults_from_config, validate_inspect_args  # noqa: E402


def main() -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--scenario_config", type=str, default=None, help="Optional scenario YAML/JSON config.")
    pre_args, _ = pre_parser.parse_known_args()
    scenario_config = load_scenario_config(pre_args.scenario_config, repo_root=REPO_ROOT)
    scenario_defaults = mesh_bounds_defaults_from_config(scenario_config)

    parser = argparse.ArgumentParser(
        description="Inspect OBJ component mesh bounds and auto bbox proxy.",
        parents=[pre_parser],
    )
    parser.add_argument("--mesh_path", default=None)
    parser.add_argument("--mesh_format", default="obj")
    parser.add_argument("--mesh_unit", default="mm")
    parser.add_argument("--mesh_scale", nargs=3, type=float, default=(0.001, 0.001, 0.001))
    parser.add_argument("--mesh_position", nargs=3, type=float, default=None)
    parser.add_argument("--mesh_orientation", nargs=4, type=float, default=(1.0, 0.0, 0.0, 0.0))
    parser.add_argument("--mesh_orientation_format", default="qwxyz")
    parser.add_argument(
        "--align_base_center_to_world_origin",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Set mesh translation so the scaled/rotated mesh base center is at world origin.",
    )
    parser.add_argument("--component_proxy_padding", type=float, default=0.0)
    parser.add_argument("--output_json", default=None)
    parser.set_defaults(**scenario_defaults)
    args = parser.parse_args()
    validate_inspect_args(args, repo_root=REPO_ROOT)

    if args.align_base_center_to_world_origin and args.mesh_position is not None:
        raise ValueError(
            "--align_base_center_to_world_origin cannot be combined with --mesh_position. "
            "Use one world-origin convention at a time."
        )
    alignment = None
    mesh_position = tuple(args.mesh_position) if args.mesh_position is not None else (0.0, 0.0, 0.0)
    if args.align_base_center_to_world_origin:
        alignment = compute_base_center_alignment_translation(
            mesh_path=args.mesh_path,
            mesh_format=args.mesh_format,
            mesh_unit=args.mesh_unit,
            mesh_scale=args.mesh_scale,
            mesh_orientation=args.mesh_orientation,
            mesh_orientation_format=args.mesh_orientation_format,
            search_roots=(REPO_ROOT,),
        )
        mesh_position = alignment.auto_translation

    bounds = compute_component_mesh_bounds(
        mesh_path=args.mesh_path,
        mesh_format=args.mesh_format,
        mesh_unit=args.mesh_unit,
        mesh_scale=args.mesh_scale,
        mesh_position=mesh_position,
        mesh_orientation=args.mesh_orientation,
        mesh_orientation_format=args.mesh_orientation_format,
        component_proxy_padding=args.component_proxy_padding,
        search_roots=(REPO_ROOT,),
    )
    payload_dict = bounds.to_dict()
    payload_dict["align_base_center_to_world_origin"] = bool(args.align_base_center_to_world_origin)
    payload_dict["world_origin_convention"] = (
        "model_base_center" if args.align_base_center_to_world_origin else "explicit_mesh_position"
    )
    payload_dict["base_center_before_translation"] = (
        list(alignment.base_center_before_translation) if alignment is not None else None
    )
    payload_dict["auto_translation_if_used"] = list(alignment.auto_translation) if alignment is not None else None
    payload = json.dumps(payload_dict, indent=2)
    print(payload)
    if args.output_json is not None:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
