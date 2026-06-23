# Obstacle Diagnostic GUI Line Visualization Report

## Purpose

Phase 7B-2.5 adds a visual-only inspection path for the existing diagnostic field:

```text
mesh_footprint_intersection_mask
```

The goal is to draw a small sampled set of robot-to-viewpoint line segments that already intersect the measured component
OBJ footprint. This is for GUI/debug inspection only.

This phase does not change `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver
behavior, reward, controller logic, HARL, training, articulation, IK, collision, raycast coverage, or final real CSV
validation.

## Files Added / Modified

Added:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B25_OBSTACLE_DEBUG_LINES_20260623.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Config Fields Added

The hybrid algorithm component-mesh scenario now includes this disabled-by-default block:

```yaml
obstacle_debug_visualization:
  enabled: false
  draw_in_headless: false
  line_source: mesh_footprint_intersections
  max_lines_per_robot: 5
  max_total_lines: 20
  prefer_shortest_blocked_pairs: true
  line_z_offset: 0.05
```

`scenario_config.py` validates:

```text
enabled: bool
draw_in_headless: bool
line_source: mesh_footprint_intersections
max_lines_per_robot: non-negative integer
max_total_lines: non-negative integer
prefer_shortest_blocked_pairs: bool
line_z_offset: finite non-negative float
```

## Line Selection Method

When explicitly enabled, the environment selects lines from:

```text
mesh_footprint_intersection_mask[num_envs, M, N]
```

Selection rules:

1. Iterate by environment and robot.
2. Find viewpoint IDs whose diagnostic mesh-footprint intersection mask is true.
3. If `prefer_shortest_blocked_pairs=true`, sort candidate pairs by `straight_line_cost_matrix`.
4. Select at most `max_lines_per_robot` for each robot.
5. Stop at `max_total_lines`.

The line segment is:

```text
start = robot base XY
end = viewpoint XY
z = max(robot_z, viewpoint_z, 0.0) + line_z_offset
```

The line is drawn as a red visual-only USD `BasisCurves` prim under each environment's `ObstacleDebugLines` path.

## Draw Conditions

Lines are drawn only when all of these are true:

```text
obstacle_debug_visualization.enabled == true
obstacle_diagnostics.enabled == true
line_source == mesh_footprint_intersections
USD debug visuals are enabled
the run has GUI, or draw_in_headless == true
mesh_footprint_intersection_mask exists
```

Committed smoke configs keep the feature disabled.

## Diagnostics Added

The assignment problem, wrapper smoke JSON, evaluator diagnostics, and scenario diagnostics now expose:

```text
obstacle_debug_visualization_enabled
obstacle_debug_visualization_draw_in_headless
obstacle_debug_visualization_line_source
obstacle_debug_visualization_max_lines_per_robot
obstacle_debug_visualization_max_total_lines
obstacle_debug_visualization_prefer_shortest_blocked_pairs
obstacle_debug_visualization_line_z_offset
obstacle_debug_visualization_drawn_line_count
obstacle_debug_visualization_skipped_reason
obstacle_debug_visualization_pairs_sample
```

The sample list is compact and full matrices are not dumped.

## Smoke Results

Python interpreter and syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/evaluate_assignment_methods.py
```

Disabled-default hybrid wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/obstacle_debug_lines_phase7b25_disabled_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
mesh_footprint_intersection_count=54
obstacle_debug_visualization_enabled=false
obstacle_debug_visualization_drawn_line_count=0
obstacle_debug_visualization_skipped_reason=disabled
```

Phase 7B-2 evaluator regression passed:

```text
output_dir=results/assignment_evaluation/obstacle_debug_lines_phase7b25_eval_regression
methods=random, nearest, greedy
compare_obstacle_aware_candidates=true
mesh_footprint_intersection_count=54
methods_compared=[nearest, greedy]
methods_baseline_only=[random]
obstacle_debug_visualization_enabled=false
obstacle_debug_visualization_drawn_line_count=0
```

Bbox scenario regression passed:

```text
result_file=results/assignment_diagnostics/obstacle_debug_lines_phase7b25_bbox_regression.json
N=50, M=3, noop_id=50
obstacle_diagnostics_enabled=false
obstacle_debug_visualization_enabled=false
assignment shapes unchanged
```

Visual scenario regression passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7b25_regression_smoke.json
N=50, M=3, noop_id=50
robot_visual_mesh_enabled=true
visual_mesh_spawned_by_robot=true for all three robots
visual_follow_enabled_by_robot=true for all three robots
obstacle_diagnostics_enabled=false
assignment smoke passed
```

## Manual GUI Usage

For manual GUI inspection, copy:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

to a local, uncommitted GUI config and set:

```yaml
headless: false

obstacle_debug_visualization:
  enabled: true
  draw_in_headless: false
  line_source: mesh_footprint_intersections
  max_lines_per_robot: 5
  max_total_lines: 20
  prefer_shortest_blocked_pairs: true
  line_z_offset: 0.05
```

Then run the wrapper/play command pattern with the local scenario config and no `--headless` override. The expected visual
inspection target is a small set of red direct robot-base-to-viewpoint diagnostic lines, not a path planner result.

## Known Limitations

- Enabled GUI line rendering was not run from Codex because committed configs keep the feature disabled and GUI inspection
  is intended as a manual local step.
- The drawn lines visualize direct XY diagnostic segments only; they are not A*, RRT, navigation, collision, IK, or 3D
  motion planning.
- Line height uses the max of robot/viewpoint Z plus an offset, so very high viewpoints may produce elevated lines.
- The mesh footprint remains approximate diagnostic data and does not hard-block viewpoints or paths.

## Next Recommended Step

Run a manual GUI inspection with a local enabled config, adjust only visualization sampling/height if needed, then proceed
to Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
