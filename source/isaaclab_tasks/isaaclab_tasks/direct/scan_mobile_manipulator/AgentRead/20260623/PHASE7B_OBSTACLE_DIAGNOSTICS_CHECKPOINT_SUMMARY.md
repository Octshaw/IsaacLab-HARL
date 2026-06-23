# Phase 7B Obstacle Diagnostics Checkpoint Summary

Date: 2026-06-23

## 1. Project Goal Reminder

The scan-mobile-manipulator project is moving toward assignment-based dynamic task allocation for arbitrary-size
viewpoint sets and variable robot counts.

Current validated foundations include:

```text
N = loaded viewpoints
M = enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

The current obstacle work is still diagnostic-only. It is intended to inform later gated cost experiments without
changing assignment behavior yet.

## 2. Current Completed Milestone

Phase 7B-2.5 is complete.

Completed milestone:

```text
mesh-footprint obstacle diagnostics
obstacle-aware candidate comparison
GUI red-line debug visualization
BasisCurves visibility fix
GUI-safe timed inspection pause
```

The user manually confirmed that red debug lines are visible and reasonable in GUI after the visibility and GUI-safe
pause patches.

## 3. Files Modified / Added Across Phase 7B-1 to Phase 7B-2.5

Primary source/config files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_obstacle_footprint.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
```

Phase reports and handoff documents:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B_OBSTACLE_DIAGNOSTICS_CHECKPOINT_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_PHASE_7B3_LONG_DIAGNOSTIC_COMPARISON_PLAN.md
```

## 4. Mesh-Footprint Obstacle Diagnostic Method

`component_obstacle_footprint.py` builds a dependency-light diagnostic footprint from the measured component OBJ.

Method summary:

```text
1. Load the component OBJ with the existing lightweight OBJ loader.
2. Apply configured mesh scale, position, and qwxyz orientation.
3. Project transformed mesh triangles into XY.
4. Rasterize projected triangles and edges into a 2D grid.
5. Inflate occupied cells by footprint_inflation_radius.
6. Sample direct robot-base-XY to viewpoint-XY line segments by line_sample_step.
7. Report whether each segment intersects the inflated footprint.
```

The component OBJ is used for mesh-footprint diagnostics and visual inspection.

## 5. Why Bbox Hard Blocking Was Avoided

The measured component is irregular. The overall component bbox is too coarse for hard obstacle blocking because some
legal viewpoints may lie inside the overall bbox while still being reachable near the real component shape.

Therefore:

```text
component bbox remains metadata/debug only
component bbox is not used as hard obstacle blocking
viewpoints are not marked unavailable because they are inside the bbox
line segments are not blocked by bbox intersection
```

## 6. New Diagnostic Tensors

When obstacle diagnostics are enabled, `get_assignment_problem()` includes these additional diagnostic fields:

```text
straight_line_cost_matrix
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
obstacle_diagnostics_enabled
obstacle_diagnostics_mode
obstacle_source
component_obstacle_footprint_diagnostics
```

Definitions:

```text
straight_line_cost_matrix:
  clone/copy of the current baseline Euclidean assignment cost

mesh_footprint_intersection_mask:
  bool tensor [num_envs, M, N], true when the direct diagnostic segment intersects the inflated mesh footprint

mesh_footprint_penalty_matrix:
  blocked_path_penalty where the intersection mask is true, otherwise 0

mesh_footprint_aware_cost_matrix:
  straight_line_cost_matrix + mesh_footprint_penalty_matrix
```

Important: `mesh_footprint_aware_cost_matrix` is diagnostic-only and is not promoted into solver inputs.

## 7. Candidate Comparison Status

`evaluate_assignment_methods.py` now supports:

```text
--compare_obstacle_aware_candidates
```

When enabled, the evaluator compares baseline assignments against diagnostic obstacle-aware candidates:

```text
baseline:
  uses normal cost_matrix, available_mask, noop_id

nearest/greedy candidate:
  uses a copied assignment problem where only copied cost_matrix is replaced by mesh_footprint_aware_cost_matrix
```

The live solver path is unchanged. `random` is reported only for selected-pair intersection statistics.

Compact comparison metrics include selected intersection counts/rates, changed assignment counts/rates, baseline and
candidate cost sums, penalty sums, and small samples of blocked/changed pairs.

## 8. GUI Debug-Line Visualization Status

Obstacle debug visualization draws sampled red line segments for pairs already marked by
`mesh_footprint_intersection_mask`.

The current hybrid scenario contains:

```yaml
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

Red obstacle debug lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned robot paths.
Robot motion may differ from red lines; this is expected.

## 9. BasisCurves Visibility Patch Status

The first GUI run produced valid line diagnostics but the red lines were not visible, and Hydra emitted invalid
`widths` primvar warnings.

Patch status:

```text
two-point BasisCurves now author widths = [line_width, line_width]
line_width is configurable and defaults to 0.03
line_z_mode supports max_endpoint and fixed
hybrid scenario uses fixed z near 0.25 for easier GUI inspection
line prim path samples are included in diagnostics
```

After the patch, the non-headless smoke no longer showed the repeated invalid widths warning in captured output, and
the user later confirmed the red lines are visible and reasonable.

## 10. GUI-Safe Timed Pause Status

`test_assignment_harl_wrapper_smoke.py` no longer uses terminal `input()` for GUI inspection pause.

Current pause behavior:

```text
--pause_after_setup
--gui_pause
--pause_after_setup_seconds <seconds>
```

If a pause is requested in GUI mode, the script runs a timed pause and repeatedly calls:

```text
simulation_app.update()
```

This keeps the Isaac Sim / Kit UI responsive without stepping the environment. Headless pause requests skip
immediately.

Result JSON fields:

```text
pause_after_setup_requested
pause_after_setup_applied
pause_after_setup_seconds
pause_after_setup_mode
```

## 11. Verification Commands and Results

Representative checks completed during Phase 7B:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Result:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Syntax checks passed for changed Python files in the relevant phases:

```text
component_obstacle_footprint.py
scan_mobile_manipulator_env.py
scenario_config.py
test_assignment_harl_wrapper_smoke.py
evaluate_assignment_methods.py
```

Representative smoke results:

```text
Hybrid obstacle wrapper smoke:
  N=50, M=3, noop_id=50
  available_actions=[1, 3, 51]
  available_mask=[1, 3, 50]
  cost_matrix=[1, 3, 50]
  mesh_footprint_intersection_mask=[1, 3, 50]
  mesh_footprint_intersection_count=54

Candidate comparison evaluator smoke:
  methods=random, nearest, greedy
  --compare_obstacle_aware_candidates enabled
  nearest/greedy candidate comparison present
  random baseline-only intersection statistics present

Debug-line visibility smoke:
  obstacle_debug_visualization_enabled=true
  obstacle_debug_visualization_line_z_mode=fixed
  obstacle_debug_visualization_line_width=0.03
  obstacle_debug_visualization_drawn_line_count=15
  line prim path samples include /World/envs/env_0/ObstacleDebugLines/BlockedPath_000

GUI-safe pause normal smoke:
  pause_after_setup_mode=disabled
  assignment shapes unchanged

GUI-safe pause headless skip:
  pause_after_setup_mode=headless_skip
  assignment shapes unchanged
```

The user manually confirmed the GUI red lines are visible and reasonable after the visibility and GUI-safe pause
patches.

## 12. What Remains Diagnostic-Only

The following remain diagnostic-only:

```text
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
obstacle-aware candidate comparison
red obstacle debug lines
component mesh footprint occupancy proxy
```

No solver is currently required to consume the obstacle-aware candidate matrix.

## 13. What Was Explicitly Not Changed

The following were not changed by Phase 7B obstacle diagnostics:

```text
cost_matrix
available_mask
feasible_mask
static_geometric_feasible_mask
solver default behavior
reward
controller
assignment_controller.py
9D action path
HARL core
training behavior
assignment-RL evaluation
real robot articulation
IK
collision
mesh collision bodies
joint limits
raycast coverage
final real CSV validation
```

Temporary and synthetic viewpoint sets remain interface validation data only and are not final benchmark evidence.

## 14. Known Limitations

- The mesh footprint is an approximate XY projection, not 3D collision.
- The diagnostic line segment is direct robot-base-XY to viewpoint-XY, not a navigation planner output.
- Red lines indicate diagnostic intersections only; actual robot motion may differ.
- Current candidate comparison smokes are short and not enough for algorithm conclusions.
- Synthetic N=50 viewpoints are smoke data only.
- The current hybrid scenario has obstacle debug visualization enabled for manual GUI inspection; set `enabled: false`
  for smoke-only runs if desired.
- There is no early-exit key for the GUI-safe timed pause; use a shorter `--pause_after_setup_seconds` for quick checks.

## 15. Git Checkpoint Recommendation

Suggested commit message:

```text
feat(scan-assignment): checkpoint obstacle diagnostics and GUI inspection tooling
```

Recommended to include:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/generate_synthetic_viewpoints.py
AgentRead reports/plans
```

Recommended to exclude unless explicitly wanted:

```text
results/
*.log
temporary local GUI scenario copies
large binary assets not already intended for source control
```

## 16. Next Phase Pointer

Proceed to:

```text
Phase 7B-3: Longer Diagnostic-Only Obstacle-Aware Candidate Comparisons
```

The next phase should run longer diagnostic-only evaluations using the existing candidate comparison path. It should
not promote `mesh_footprint_aware_cost_matrix` into real solver inputs yet.
