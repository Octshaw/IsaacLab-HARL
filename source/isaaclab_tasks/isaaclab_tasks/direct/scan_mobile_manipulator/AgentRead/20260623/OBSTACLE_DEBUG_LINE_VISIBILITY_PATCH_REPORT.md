# Obstacle Debug Line Visibility Patch Report

## Purpose

Phase 7B-2.5 added visual-only obstacle diagnostic lines for sampled `mesh_footprint_intersection_mask` pairs. A manual GUI run reported:

```text
obstacle_debug_visualization_enabled=true
obstacle_debug_visualization_drawn_line_count=15
obstacle_debug_visualization_skipped_reason=null
```

but the red lines were not visible in the GUI, and Hydra repeatedly warned that the `widths` primvar on the USD curve was invalid.

This patch makes the diagnostic lines easier to see and fixes the invalid `BasisCurves.widths` authoring. It does not change assignment behavior, solver inputs, masks, costs, reward, controller behavior, collision, IK, raycast coverage, HARL, training, or final real CSV validation.

## Files Modified

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Root Cause

The previous obstacle debug line implementation authored each two-point USD `BasisCurves` line with:

```text
points length = 2
curveVertexCounts = [2]
widths = [0.035]
```

Hydra interpreted the curve widths with vertex interpolation, so one width value was not enough for a two-point curve. This produced warnings like:

```text
Processing 'widths' primvar ... Not enough data size for HdInterpolationVertex.
Curve ... widths primvar is not valid
```

## Width Fix

Each two-point blocked-path curve now authors:

```text
points length = 2
curveVertexCounts = [2]
widths = [line_width, line_width]
widths interpolation = vertex, when the USD API exposes SetWidthsInterpolation
```

The current configured width is:

```text
line_width = 0.03
```

The non-headless smoke run completed without the repeated invalid `widths` primvar warning in the captured command output.

## Line Height Mode

The previous line height behavior used:

```text
z = max(robot_z, viewpoint_z, 0.0) + line_z_offset
```

That remains the default through:

```yaml
line_z_mode: max_endpoint
line_z_value: 0.20
```

The hybrid component-mesh scenario now explicitly uses a GUI-friendly fixed-height mode:

```yaml
line_z_mode: fixed
line_z_value: 0.20
line_z_offset: 0.05
line_width: 0.03
```

This places lines near:

```text
z = 0.25
```

which is easier to inspect around the XY mesh footprint.

## Diagnostics Added

The assignment problem, wrapper smoke JSON, evaluator diagnostics, and scenario diagnostics now include:

```text
obstacle_debug_visualization_line_width
obstacle_debug_visualization_line_z_mode
obstacle_debug_visualization_line_z_value
obstacle_debug_visualization_line_prim_paths_sample
```

Existing compact diagnostics remain:

```text
obstacle_debug_visualization_enabled
obstacle_debug_visualization_drawn_line_count
obstacle_debug_visualization_skipped_reason
obstacle_debug_visualization_pairs_sample
```

## Verification Results

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
obstacle_debug_visualization_enabled=true
obstacle_debug_visualization_line_z_mode=fixed
obstacle_debug_visualization_line_z_value=0.2
obstacle_debug_visualization_line_width=0.03
obstacle_debug_visualization_drawn_line_count=15
obstacle_debug_visualization_skipped_reason=null
```

The smoke JSON included compact prim path diagnostics:

```text
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
/World/envs/env_0/ObstacleDebugLines/BlockedPath_001
/World/envs/env_0/ObstacleDebugLines/BlockedPath_002
...
```

Evaluator regression passed with `--compare_obstacle_aware_candidates`. The headless evaluator correctly skipped drawing because:

```text
draw_in_headless=false
skipped_reason=headless_without_draw_in_headless
```

Bbox scenario regression passed with obstacle diagnostics/debug visualization disabled.

Visual real-scene regression passed with robot visual mesh spawning/following still enabled and obstacle diagnostics/debug visualization disabled.

## Manual GUI Instructions

Use the hybrid component-mesh scenario for inspection:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

For manual GUI inspection, use:

```yaml
headless: false

obstacle_debug_visualization:
  enabled: true
  draw_in_headless: false
  line_source: mesh_footprint_intersections
  max_lines_per_robot: 5
  max_total_lines: 20
  prefer_shortest_blocked_pairs: true
  line_z_mode: fixed
  line_z_value: 0.20
  line_z_offset: 0.05
  line_width: 0.03
```

In the Stage panel, inspect:

```text
/World/envs/env_0/ObstacleDebugLines
```

Then frame selected on:

```text
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

If the prims exist but lines are still not visually obvious in a local viewport, the next fallback should be visible cylinder/mesh line primitives or a debug draw API. That fallback was not implemented in this patch because the `BasisCurves` authoring issue was the smallest likely cause.

## Known Limitations

- This only draws sampled diagnostic line segments for selected blocked pairs.
- The line segments are direct robot-base-XY to viewpoint-XY diagnostics, not navigation paths.
- The mesh footprint remains diagnostic-only and approximate.
- Current hybrid scenario debug lines are enabled for manual GUI inspection; set `enabled: false` for smoke-only runs.
- The patch does not make lines collision objects and does not affect physics or assignment logic.

## Next Recommended Step

Run one manual GUI inspection using the fixed-height line settings and check `/World/envs/env_0/ObstacleDebugLines/BlockedPath_000`. If curves remain hard to see despite valid prims, add a second visual-only fallback using cylinder/mesh line primitives or the available debug draw API.
