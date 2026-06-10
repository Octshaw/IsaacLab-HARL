"""Bounded Level-2 controller feasibility diagnostic for assignment viewpoints.

This script drives selected agent-viewpoint pairs through the existing
high-level assignment controller, without a learned policy.  It is intended for
short smoke-style checks of static-feasible pairs that need controller/coverage
gate confirmation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from isaaclab.app import AppLauncher


def _parse_pair(text: str) -> tuple[str, int]:
    if ":" not in text:
        raise argparse.ArgumentTypeError("pair must use AGENT:VIEWPOINT_ID, for example robot_2:5")
    agent, viewpoint_text = text.split(":", 1)
    agent = agent.strip()
    if not agent:
        raise argparse.ArgumentTypeError("pair agent name is empty")
    try:
        viewpoint_id = int(viewpoint_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pair viewpoint id must be an integer") from exc
    return agent, viewpoint_id


parser = argparse.ArgumentParser(
    description="Run bounded controller feasibility diagnostics for assignment agent-viewpoint pairs."
)
parser.add_argument("--task", type=str, default="Isaac-Scan-Mobile-Manipulator-Direct-v0")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--max_steps", type=int, default=160)
parser.add_argument("--pair", action="append", type=_parse_pair, default=None)
parser.add_argument("--viewpoint_csv_path", type=str, default=None)
parser.add_argument("--expect_num_viewpoints", type=int, default=None)
parser.add_argument(
    "--output_json",
    type=str,
    default="results/assignment_diagnostics/stage3b/controller_feasibility.json",
)
parser.add_argument(
    "--bypass_manual_override_for_diagnostic",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Temporarily ignore fixed manual infeasibility rows when the static generator says the pair is feasible.",
)
parser.add_argument("--stop_on_covered", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

import sys  # noqa: E402

import torch  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ISAACLAB_TASKS_SOURCE = REPO_ROOT / "source" / "isaaclab_tasks"
if str(ISAACLAB_TASKS_SOURCE) not in sys.path:
    sys.path.insert(0, str(ISAACLAB_TASKS_SOURCE))

import isaaclab_tasks  # noqa: F401, E402
from isaaclab.utils.math import quat_apply, quat_error_magnitude  # noqa: E402
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import (  # noqa: E402
    make_assignment_harl_env,
)
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402


def _tensor_value(value: torch.Tensor | float | bool | int) -> float | bool | int:
    if isinstance(value, torch.Tensor):
        if value.dtype == torch.bool:
            return bool(value.item())
        if value.dtype in (torch.int8, torch.int16, torch.int32, torch.int64):
            return int(value.item())
        return float(value.item())
    return value


def _agent_names(env_unwrapped: Any) -> list[str]:
    names = getattr(env_unwrapped, "agent_names", None)
    if names is None:
        names = env_unwrapped.cfg.possible_agents
    return list(names)


def _agent_index(env_unwrapped: Any, agent_name: str) -> int:
    agent_names = _agent_names(env_unwrapped)
    try:
        return agent_names.index(agent_name)
    except ValueError as exc:
        raise ValueError(f"Unknown agent {agent_name!r}; available agents: {agent_names}") from exc


def _viewpoint_index(env_unwrapped: Any, viewpoint_id: int) -> int:
    viewpoint_ids = list(env_unwrapped.viewpoint_ids)
    if viewpoint_id not in viewpoint_ids:
        raise ValueError(f"Unknown viewpoint_id {viewpoint_id}; available viewpoint ids: {viewpoint_ids}")
    return viewpoint_ids.index(viewpoint_id)


def _maybe_bypass_manual_override(env_unwrapped: Any, agent_idx: int, viewpoint_idx: int) -> tuple[bool, bool, bool]:
    before_problem = env_unwrapped.get_assignment_problem()
    static_feasible = bool(before_problem["static_geometric_feasible_mask"][0, agent_idx, viewpoint_idx].item())
    final_feasible_before = bool(before_problem["feasible_mask"][0, agent_idx, viewpoint_idx].item())
    bypassed = False

    if args_cli.bypass_manual_override_for_diagnostic and static_feasible and not final_feasible_before:
        env_unwrapped._apply_fixed_12_mvp_override = False
        env_unwrapped.assignment_feasible_mask_base = env_unwrapped.static_geometric_feasible_mask.clone()
        env_unwrapped.manual_feasibility_override_rows = []
        env_unwrapped.feasibility_diagnostic_rows = env_unwrapped._build_final_feasibility_rows()
        bypassed = True

    return static_feasible, final_feasible_before, bypassed


def _restore_default_feasibility_mask(env_unwrapped: Any) -> None:
    env_unwrapped._apply_fixed_12_mvp_override = bool(
        getattr(env_unwrapped.cfg, "fixed_12_mvp_infeasible_agent_viewpoints", {})
    )
    env_unwrapped._build_static_feasibility()


def _collect_step_row(
    env_unwrapped: Any,
    agent_idx: int,
    viewpoint_idx: int,
    step_index: int,
    done_flag: bool,
) -> dict[str, Any]:
    device = env_unwrapped.device
    env_id = 0
    agent_name = _agent_names(env_unwrapped)[agent_idx]
    viewpoint_id = int(env_unwrapped.viewpoint_ids[viewpoint_idx])

    scanner_pos = env_unwrapped.scanner_pos[env_id, agent_idx]
    scanner_quat = env_unwrapped.scanner_quat[env_id, agent_idx]
    base_pos = env_unwrapped.base_pos[env_id, agent_idx]
    target_pos = env_unwrapped.viewpoint_pos_local[viewpoint_idx]
    target_quat = env_unwrapped.viewpoint_quat[viewpoint_idx]

    position_error = torch.linalg.norm(scanner_pos - target_pos)
    rotation_error = quat_error_magnitude(scanner_quat.unsqueeze(0), target_quat.unsqueeze(0))[0]
    scanner_target_distance = torch.linalg.norm(scanner_pos - target_pos)

    proxy_center = env_unwrapped.component_center.to(device=device)
    proxy_half_extents = env_unwrapped.component_half_extents.to(device=device)
    scanner_to_box = torch.clamp(torch.abs(scanner_pos - proxy_center) - proxy_half_extents, min=0.0)
    sensor_surface_distance = torch.linalg.norm(scanner_to_box)

    min_range = env_unwrapped.scanner_min_range[agent_idx]
    max_range = env_unwrapped.scanner_max_range[agent_idx]
    min_margin = sensor_surface_distance - min_range
    max_margin = max_range - sensor_surface_distance
    range_margin = torch.minimum(min_margin, max_margin)
    range_ok = (sensor_surface_distance >= min_range) & (sensor_surface_distance <= max_range)

    position_gate_ok = position_error < env_unwrapped.scan_pos_tolerance[agent_idx]
    rotation_gate_ok = rotation_error < env_unwrapped.scan_rot_tolerance[agent_idx]

    arm_distance = torch.linalg.norm(target_pos - base_pos)
    arm_margin = env_unwrapped.arm_reach[agent_idx] - arm_distance
    arm_reach_ok = arm_margin >= 0.0

    forward_axis = torch.tensor([1.0, 0.0, 0.0], device=device)
    scanner_forward = quat_apply(scanner_quat.unsqueeze(0), forward_axis.unsqueeze(0))[0]
    target_forward = quat_apply(target_quat.unsqueeze(0), forward_axis.unsqueeze(0))[0]
    alignment_cos = torch.dot(scanner_forward, target_forward)
    fov_alignment_ok = alignment_cos > env_unwrapped.scanner_fov_cos[agent_idx]

    all_coverage_gates_ok = (
        position_gate_ok & rotation_gate_ok & range_ok & arm_reach_ok & fov_alignment_ok
    )
    covered = env_unwrapped.viewpoints_covered[env_id, viewpoint_idx]

    return {
        "step": step_index,
        "assigned_agent": agent_name,
        "viewpoint_id": viewpoint_id,
        "scanner_position": [_tensor_value(v) for v in scanner_pos.detach().cpu()],
        "target_viewpoint_position": [_tensor_value(v) for v in target_pos.detach().cpu()],
        "position_error": _tensor_value(position_error),
        "rotation_error": _tensor_value(rotation_error),
        "scanner_target_distance": _tensor_value(scanner_target_distance),
        "sensor_surface_distance": _tensor_value(sensor_surface_distance),
        "range_margin": _tensor_value(range_margin),
        "range_ok": _tensor_value(range_ok),
        "position_gate_ok": _tensor_value(position_gate_ok),
        "rotation_gate_ok": _tensor_value(rotation_gate_ok),
        "arm_reach_ok": _tensor_value(arm_reach_ok),
        "arm_margin": _tensor_value(arm_margin),
        "fov_alignment_cos": _tensor_value(alignment_cos),
        "fov_alignment_ok": _tensor_value(fov_alignment_ok),
        "all_coverage_gates_ok": _tensor_value(all_coverage_gates_ok),
        "covered": _tensor_value(covered),
        "done": done_flag,
    }


def _diagnose_pair(wrapper: Any, agent_name: str, viewpoint_id: int) -> dict[str, Any]:
    _restore_default_feasibility_mask(wrapper.unwrapped)
    wrapper.reset(seed=args_cli.seed)
    env_unwrapped = wrapper.unwrapped
    agent_idx = _agent_index(env_unwrapped, agent_name)
    viewpoint_idx = _viewpoint_index(env_unwrapped, viewpoint_id)

    static_feasible, final_feasible_before, manual_override_bypassed = _maybe_bypass_manual_override(
        env_unwrapped, agent_idx, viewpoint_idx
    )
    final_feasible_after = bool(
        env_unwrapped.get_assignment_problem()["feasible_mask"][0, agent_idx, viewpoint_idx].item()
    )

    discrete_actions = wrapper.make_action_tensor()
    discrete_actions.fill_(float(wrapper.noop_action_id))
    discrete_actions[:, agent_idx, 0] = float(viewpoint_idx)

    rows: list[dict[str, Any]] = []
    first_covered_step: int | None = None
    done_flag = False
    last_action: list[float] | None = None

    for step_index in range(args_cli.max_steps):
        _, _, _, dones, _, _ = wrapper.step(discrete_actions)
        if wrapper.last_env_actions is not None:
            last_action = [_tensor_value(v) for v in wrapper.last_env_actions[agent_name][0].detach().cpu()]
        done_flag = bool(dones.any().item())

        row = _collect_step_row(env_unwrapped, agent_idx, viewpoint_idx, step_index, done_flag)
        rows.append(row)
        if row["covered"] and first_covered_step is None:
            first_covered_step = step_index
        if args_cli.stop_on_covered and row["covered"]:
            break

    ever_position_gate_ok = any(row["position_gate_ok"] for row in rows)
    ever_rotation_gate_ok = any(row["rotation_gate_ok"] for row in rows)
    ever_range_ok = any(row["range_ok"] for row in rows)
    ever_fov_alignment_ok = any(row["fov_alignment_ok"] for row in rows)
    ever_arm_reach_ok = any(row["arm_reach_ok"] for row in rows)
    ever_position_rotation_gate_ok = any(
        row["position_gate_ok"] and row["rotation_gate_ok"] for row in rows
    )
    ever_position_rotation_range_ok = any(
        row["position_gate_ok"] and row["rotation_gate_ok"] and row["range_ok"] for row in rows
    )
    ever_pose_range_arm_gate_ok = any(
        row["position_gate_ok"]
        and row["rotation_gate_ok"]
        and row["range_ok"]
        and row["arm_reach_ok"]
        for row in rows
    )
    ever_all_coverage_gates_ok = any(row["all_coverage_gates_ok"] for row in rows)

    best_position_error = min(row["position_error"] for row in rows) if rows else None
    best_rotation_error = min(row["rotation_error"] for row in rows) if rows else None
    best_range_margin = max(row["range_margin"] for row in rows) if rows else None

    if first_covered_step is not None:
        most_likely_failure_reason = "covered"
    elif not final_feasible_after:
        most_likely_failure_reason = "assignment_pair_not_feasible_after_diagnostic_mask"
    elif not ever_position_gate_ok:
        most_likely_failure_reason = "position_controller_did_not_reach_tolerance"
    elif not ever_rotation_gate_ok:
        most_likely_failure_reason = "rotation_controller_did_not_reach_tolerance"
    elif not ever_range_ok:
        most_likely_failure_reason = "scanner_surface_range_gate_never_satisfied"
    elif not ever_arm_reach_ok:
        most_likely_failure_reason = "arm_reach_gate_never_satisfied"
    elif not ever_fov_alignment_ok:
        most_likely_failure_reason = "fov_alignment_gate_never_satisfied"
    elif not ever_position_rotation_gate_ok:
        most_likely_failure_reason = "position_rotation_gates_never_simultaneously_satisfied"
    elif not ever_position_rotation_range_ok:
        most_likely_failure_reason = "pose_and_range_gates_never_simultaneously_satisfied"
    elif not ever_pose_range_arm_gate_ok:
        most_likely_failure_reason = "pose_range_and_arm_gates_never_simultaneously_satisfied"
    elif not ever_all_coverage_gates_ok:
        most_likely_failure_reason = "coverage_gates_never_simultaneously_satisfied"
    else:
        most_likely_failure_reason = "all_gates_ok_but_viewpoint_not_marked_covered"

    if manual_override_bypassed and first_covered_step is not None:
        manual_override_recommendation = "keep_override_pending_episode_interaction_review"
    elif manual_override_bypassed:
        manual_override_recommendation = "keep_override_with_level2_failure_reason"
    else:
        manual_override_recommendation = "not_a_manual_override_pair"

    result = {
        "assigned_agent": agent_name,
        "viewpoint_id": viewpoint_id,
        "viewpoint_index": viewpoint_idx,
        "max_steps": args_cli.max_steps,
        "steps_executed": len(rows),
        "target_static_geometric_feasible": static_feasible,
        "target_final_feasible_before_diagnostic_bypass": final_feasible_before,
        "target_final_feasible_after_diagnostic_bypass": final_feasible_after,
        "manual_override_bypassed_for_diagnostic": manual_override_bypassed,
        "other_agents_assignment": "noop",
        "last_target_agent_action": last_action,
        "controller_converged": ever_position_gate_ok and ever_rotation_gate_ok,
        "ever_position_gate_ok": ever_position_gate_ok,
        "ever_rotation_gate_ok": ever_rotation_gate_ok,
        "ever_range_ok": ever_range_ok,
        "ever_fov_alignment_ok": ever_fov_alignment_ok,
        "ever_position_rotation_gate_ok": ever_position_rotation_gate_ok,
        "ever_position_rotation_range_ok": ever_position_rotation_range_ok,
        "ever_pose_range_arm_gate_ok": ever_pose_range_arm_gate_ok,
        "ever_all_coverage_gates_ok": ever_all_coverage_gates_ok,
        "first_covered_step": first_covered_step,
        "target_viewpoint_covered": first_covered_step is not None,
        "best_position_error": best_position_error,
        "best_rotation_error": best_rotation_error,
        "best_range_margin": best_range_margin,
        "most_likely_failure_reason": most_likely_failure_reason,
        "manual_override_recommendation": manual_override_recommendation,
        "step_rows": rows,
    }
    return result


def main() -> None:
    pairs = args_cli.pair or [("robot_2", 5)]

    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
    )
    env_cfg.enable_reset_diagnostics = False
    if args_cli.viewpoint_csv_path:
        env_cfg.viewpoint_csv_path = args_cli.viewpoint_csv_path

    if args_cli.seed is not None:
        env_cfg.seed = args_cli.seed

    wrapper = make_assignment_harl_env(args_cli.task, cfg=env_cfg)
    try:
        if args_cli.expect_num_viewpoints is not None:
            actual_num_viewpoints = int(wrapper.unwrapped.num_viewpoints)
            if actual_num_viewpoints != args_cli.expect_num_viewpoints:
                raise RuntimeError(
                    f"Expected {args_cli.expect_num_viewpoints} viewpoints, got {actual_num_viewpoints}"
                )

        try:
            results = [_diagnose_pair(wrapper, agent_name, viewpoint_id) for agent_name, viewpoint_id in pairs]
        except BaseException as exc:
            print(f"[controller-feasibility] ERROR: {type(exc).__name__}: {exc}", flush=True)
            raise
        payload = {
            "task": args_cli.task,
            "num_envs": args_cli.num_envs,
            "viewpoint_source": wrapper.unwrapped.viewpoint_source,
            "num_viewpoints": int(wrapper.unwrapped.num_viewpoints),
            "viewpoint_ids": [int(v) for v in wrapper.unwrapped.viewpoint_ids],
            "noop_action_id": int(wrapper.unwrapped.noop_action_id),
            "bypass_manual_override_for_diagnostic": bool(args_cli.bypass_manual_override_for_diagnostic),
            "results": results,
        }

        output_path = Path(args_cli.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        print(
            "[controller-feasibility] "
            f"viewpoints={payload['num_viewpoints']} noop={payload['noop_action_id']} "
            f"pairs={len(results)} output={output_path}"
        )
        for result in results:
            print(
                "[controller-feasibility] "
                f"{result['assigned_agent']} -> viewpoint_{result['viewpoint_id']}: "
                f"covered={result['target_viewpoint_covered']} "
                f"best_pos={result['best_position_error']:.6f} "
                f"best_rot={result['best_rotation_error']:.6f} "
                f"best_range_margin={result['best_range_margin']:.6f} "
                f"reason={result['most_likely_failure_reason']}"
            )
    finally:
        wrapper.close()


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
