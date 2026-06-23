# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2.5 Patch: Fix Obstacle Debug Line Visibility is complete.

The obstacle diagnostic GUI line path now authors valid USD `BasisCurves.widths` data for two-point line curves and exposes GUI-friendly line width / line height controls. The patch is visualization-only.

No assignment behavior changed: `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver default behavior, reward, controller math, `assignment_controller.py`, the 9D action path, HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast coverage, and final real CSV validation were not changed.

## Latest Completed Phase

Phase 7B-2.5 Patch: Fix Obstacle Debug Line Visibility.

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B25_VISIBILITY_PATCH_20260623.md
```

## Patch Summary

The previous USD curve authoring used one width value for a two-point `BasisCurves` line, which could trigger Hydra warnings:

```text
Processing 'widths' primvar ... Not enough data size for HdInterpolationVertex.
Curve ... widths primvar is not valid
```

The line authoring now uses:

```text
points length = 2
curveVertexCounts = [2]
widths = [line_width, line_width]
widths interpolation = vertex when supported by the USD API
```

New optional config fields:

```yaml
obstacle_debug_visualization:
  line_z_mode: fixed        # fixed / max_endpoint
  line_z_value: 0.20
  line_z_offset: 0.05
  line_width: 0.03
```

Default environment behavior preserves old height logic with `line_z_mode=max_endpoint`. The current hybrid component-mesh scenario is enabled for manual GUI inspection and uses `line_z_mode=fixed`, so debug lines are near `z=0.25`.

## Diagnostics Added

New compact diagnostics:

```text
obstacle_debug_visualization_line_width
obstacle_debug_visualization_line_z_mode
obstacle_debug_visualization_line_z_value
obstacle_debug_visualization_line_prim_paths_sample
```

Existing diagnostics remain:

```text
obstacle_debug_visualization_enabled
obstacle_debug_visualization_drawn_line_count
obstacle_debug_visualization_skipped_reason
obstacle_debug_visualization_pairs_sample
```

## Latest Verification

Interpreter check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Output:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Syntax check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/evaluate_assignment_methods.py
```

Current hybrid scenario smoke passed:

```text
result_file=results/assignment_diagnostics/obstacle_debug_line_visibility_patch_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
mesh_footprint_intersection_count=54
obstacle_debug_visualization_enabled=true
obstacle_debug_visualization_line_z_mode=fixed
obstacle_debug_visualization_line_z_value=0.2
obstacle_debug_visualization_line_width=0.03
obstacle_debug_visualization_drawn_line_count=15
obstacle_debug_visualization_skipped_reason=null
line_prim_paths_sample includes /World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

The captured non-headless smoke output did not show the repeated invalid `widths` primvar Hydra warnings.

Evaluator regression passed:

```text
output_dir=results/assignment_evaluation/obstacle_debug_line_visibility_patch_eval_regression
methods=random, nearest, greedy
compare_obstacle_aware_candidates=true
obstacle_debug_visualization_enabled=true
obstacle_debug_visualization_drawn_line_count=0
obstacle_debug_visualization_skipped_reason=headless_without_draw_in_headless
```

Bbox scenario regression passed:

```text
result_file=results/assignment_diagnostics/obstacle_debug_line_visibility_patch_bbox_regression.json
obstacle_diagnostics_enabled=false
obstacle_debug_visualization_enabled=false
assignment shapes unchanged
```

Visual real-scene regression passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_obstacle_debug_line_visibility_patch_regression.json
robot_visual_mesh_enabled=true
visual_mesh_spawned_by_robot=true for all three robots
visual_follow_enabled_by_robot=true for all three robots
obstacle_diagnostics_enabled=false
assignment shapes unchanged
```

## Manual GUI Check

For GUI inspection, open the Stage path:

```text
/World/envs/env_0/ObstacleDebugLines
```

Frame selected on:

```text
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

Expected visible result:

```text
red lines near z about 0.25
```

If the prim paths exist but curves are still difficult to see in a local viewport, the next fallback should be a visual-only cylinder/mesh line primitive or an available debug draw API.

## Known Issues / Limitations

- A fresh manual GUI inspection after this patch was not run from Codex.
- Current hybrid scenario keeps obstacle debug visualization enabled for manual GUI inspection; set `enabled: false` for smoke-only runs.
- Lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned paths.
- Mesh-footprint diagnostics remain approximate and do not hard-block viewpoints or paths.
- This patch does not create collision bodies, physics interactions, IK, raycast coverage, or assignment behavior changes.
- Synthetic N=50 viewpoints remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into actual solver inputs.
- Do not replace `cost_matrix`, `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver default behavior, reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add bbox hard blocking, mesh-footprint hard blocking, inter-robot conflict avoidance, or dynamic reassignment yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Manual GUI verification of /World/envs/env_0/ObstacleDebugLines/BlockedPath_000 with fixed-height red lines, then Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
```

Keep Phase 7B-3 diagnostic-only unless a later gated task explicitly promotes an obstacle-aware candidate into solver inputs.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B25_VISIBILITY_PATCH_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
