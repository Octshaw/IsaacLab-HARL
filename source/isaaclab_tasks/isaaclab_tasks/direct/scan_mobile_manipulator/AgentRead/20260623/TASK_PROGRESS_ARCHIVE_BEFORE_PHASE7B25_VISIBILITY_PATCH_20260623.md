# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2.5 Obstacle Diagnostic GUI Line Visualization is complete.

The hybrid algorithm component-mesh scenario now has a disabled-by-default visual debug layer for sampled
mesh-footprint obstacle diagnostic lines:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

This phase only visualizes existing diagnostic data from `mesh_footprint_intersection_mask`. It does not change
`cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver behavior, reward, controller
math, `assignment_controller.py`, the 9D action path, HARL core, training behavior, real robot articulation, IK,
collision, joint limits, raycast coverage, or final real CSV validation.

## Latest Completed Phase

Phase 7B-2.5: obstacle diagnostic GUI line visualization.

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
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B25_OBSTACLE_DEBUG_LINES_20260623.md
```

## Config Summary

New optional scenario block:

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

Committed smoke configs keep this disabled. For GUI inspection, copy the hybrid scenario locally, set `headless: false`,
and set `obstacle_debug_visualization.enabled: true`.

## Diagnostics Added

The assignment problem, wrapper smoke JSON, evaluator diagnostics, and scenario diagnostics now report:

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

When enabled, selected blocked pairs are drawn as visual-only red USD `BasisCurves` under each environment's
`ObstacleDebugLines` path. Selection is capped by `max_lines_per_robot` and `max_total_lines`.

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
obstacle_diagnostics_enabled=false
obstacle_debug_visualization_enabled=false
assignment shapes unchanged
```

Visual scenario regression passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7b25_regression_smoke.json
robot_visual_mesh_enabled=true
visual_mesh_spawned_by_robot=true for all three robots
visual_follow_enabled_by_robot=true for all three robots
obstacle_diagnostics_enabled=false
assignment smoke passed
```

## Known Issues / Limitations

- Enabled GUI line rendering was not run from Codex; it is a manual GUI inspection step using a local scenario copy.
- The visual lines are direct robot-base-XY to viewpoint-XY diagnostic segments only.
- This is not path planning, PhysX collision, mesh collision, IK, raycast coverage, or real robot dynamics.
- The line Z value uses `max(robot_z, viewpoint_z, 0.0) + line_z_offset`; high viewpoints may make lines elevated.
- The mesh footprint remains approximate diagnostic data and does not hard-block paths or viewpoints.
- Synthetic N=50 viewpoints remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not enable obstacle debug lines by default in committed smoke scenarios.
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
Manual GUI inspection of obstacle diagnostic lines with a local enabled copy of algorithm_proxy_component_mesh.yaml,
then Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
```

Keep Phase 7B-3 diagnostic-only unless a separate gated task explicitly promotes an obstacle-aware cost candidate into
solver inputs.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B25_OBSTACLE_DEBUG_LINES_20260623.md
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
