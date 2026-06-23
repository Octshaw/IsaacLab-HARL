# Hybrid Algorithm Component-Mesh Scenario Report

## Purpose

Phase 7A-3 adds a hybrid algorithm visual-debug scenario.

The goal is to inspect the measured component OBJ, simplified task-space proxy robot markers, viewpoint locations, and
component bbox/proxy metadata without spawning the heavier robot OBJ visual mesh.

This is still scenario/config work only. The component OBJ is visual-only in this phase. No mesh collision,
mesh-footprint occupancy, obstacle-aware path cost, bbox hard blocking, inter-robot avoidance, dynamic reassignment,
reward change, controller change, HARL change, training, articulation, IK, raycast coverage, or final real CSV
validation was added.

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A3_HYBRID_COMPONENT_MESH_20260623.md
```

## Files Modified

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No Python files were changed for this phase.

## Scenario Summary

New scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

It uses:

```text
robots_real_proxy.yaml
mobile_scanner_profiles.yaml
synthetic_smoke_n50.csv
task-space proxy robots
robot_visual_mode=debug_marker
component_visual_mode=mesh
component_proxy.type=bbox
component_proxy.visual_visible=true
```

The measured component visual OBJ is:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

The robot visual OBJ metadata remains in `robots_real_proxy.yaml`, but the scenario disables robot mesh spawning through
`robot_visual_mode=debug_marker`.

## Difference From algorithm_proxy_bbox.yaml

`algorithm_proxy_bbox.yaml` is the fastest algorithm smoke path:

```text
robot_visual_mode=debug_marker
component_visual_mode=bbox
robot_visual_mesh_enabled=false
component_mesh_enabled=false
```

`algorithm_proxy_component_mesh.yaml` keeps robot markers but enables the measured component OBJ:

```text
robot_visual_mode=debug_marker
component_visual_mode=mesh
robot_visual_mesh_enabled=false
component_mesh_enabled=true
```

Use the bbox scenario for fast regression and the hybrid scenario for visual debugging of the irregular component shape.

## Difference From real_scene_proxy_headless.yaml

`real_scene_proxy_headless.yaml` remains the full visual/demo path:

```text
robot_visual_mode=mesh
component_visual_mode=mesh
robot_visual_mesh_enabled=true
component_mesh_enabled=true
```

The hybrid scenario intentionally avoids `ScanRobot.obj` spawning and robot visual-follow, while still loading the
component OBJ.

## Diagnostics Verified

Wrapper/evaluator diagnostics report:

```text
scenario_name=algorithm_proxy_component_mesh
scenario_type=algorithm_visual_debug
robot_visual_mode=debug_marker
component_visual_mode=mesh
robot_visual_mesh_enabled=false
component_mesh_enabled=true
component_proxy_type=bbox
component_proxy_center=[0.0, 0.0, 1.0]
component_proxy_half_extents=[3.0, 1.0, 1.0]
visual_mesh_spawned_by_robot=false for robot_0, robot_1, robot_2
```

Component mesh diagnostics are present and include the resolved component mesh path and transformed mesh bounds.

## Smoke Results

Hybrid wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_component_mesh_phase7a3_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mesh_enabled=false
component_mesh_enabled=true
visual_mesh_spawned_by_robot=false for robot_0, robot_1, robot_2
```

Hybrid evaluator smoke passed:

```text
output_dir=results/assignment_evaluation/algorithm_proxy_component_mesh_phase7a3_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
```

Fast bbox regression wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7a3_regression_smoke.json
robot_visual_mode=debug_marker
component_visual_mode=bbox
robot_visual_mesh_enabled=false
component_mesh_enabled=false
```

Visual scenario regression wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7a3_regression_smoke.json
robot_visual_mode=mesh
component_visual_mode=mesh
robot_visual_mesh_enabled=true
component_mesh_enabled=true
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
```

## Known Limitations

- The hybrid scenario loads the component OBJ as visual geometry only.
- The bbox proxy remains the only component proxy used by the assignment diagnostics.
- `cost_matrix`, `available_mask`, and feasibility semantics were not changed.
- No GUI run was performed.
- Synthetic viewpoint CSV data remains smoke/interface validation data only, not benchmark evidence.

## Next Recommended Step

Phase 7B-1 should add obstacle-aware path-cost diagnostics only, preferably starting from the hybrid and bbox algorithm
scenarios:

```text
straight_line_cost_matrix
obstacle_intersection_mask
obstacle_penalty_matrix
obstacle_aware_cost_matrix
```

Keep existing solver behavior, reward, controller math, and `cost_matrix` unchanged until those diagnostics are
validated.
