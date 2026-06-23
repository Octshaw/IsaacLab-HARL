# Algorithm Scenario Decoupling Report

## Purpose

Phase 7A-2 separates lightweight algorithm evaluation scenarios from visual demonstration scenarios.

Algorithm scenarios should avoid large visual assets such as `ScanRobot.obj` and the measured component OBJ. Visual
scenarios remain available for GUI inspection, screenshots, and presentation material.

This phase is scenario/config decoupling only. It does not add obstacle-aware path cost, inter-robot avoidance, dynamic
reassignment, reward changes, controller changes, HARL changes, training, assignment-RL evaluation, articulation, IK,
collision, joint limits, raycast coverage, or final real CSV validation.

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_bbox.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A2_ALGORITHM_SCENARIO_DECOUPLING_20260623.md
```

## Files Modified

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Algorithm Scenario Summary

New scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_bbox.yaml
```

It uses:

```text
robots_real_proxy.yaml
mobile_scanner_profiles.yaml
synthetic_smoke_n50.csv
component_proxy.type=bbox
robot_visual_mode=debug_marker
component_visual_mode=bbox
```

It intentionally does not load:

```text
ScanRobot.obj
aircraft_skin_with_frame.obj
robot mesh visuals
component mesh visuals
```

The algorithm scenario still keeps task-space proxy robots, debug markers, the bbox component proxy, and the existing
assignment interface.

## Visual Scenario Preservation

Existing visual scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
```

now explicitly declares:

```yaml
visualization:
  robot_visual_mode: mesh
  component_visual_mode: mesh
```

The visual scenario still loads the component visual OBJ and `ScanRobot.obj` when those assets exist. It remains the
path for GUI inspection, screenshots, videos, and presentation material.

## Visual Mode Controls Added

Scenario YAML supports:

```yaml
visualization:
  robot_visual_mode: mesh        # mesh / debug_marker / none
  component_visual_mode: mesh    # mesh / bbox / none
```

Behavior:

```text
robot_visual_mode=mesh
  spawn display-only robot OBJ mesh when configured, and keep debug markers

robot_visual_mode=debug_marker
  skip robot OBJ mesh loading/spawning and keep simple proxy markers

robot_visual_mode=none
  skip robot OBJ mesh loading/spawning and robot debug markers

component_visual_mode=mesh
  preserve existing component mesh behavior when component_mesh.path is configured

component_visual_mode=bbox
  skip component mesh loading when mesh is not required for proxy generation and use bbox/debug marker path

component_visual_mode=none
  skip component mesh visualization and component proxy marker visualization
```

## Diagnostics Added

Environment assignment problem, wrapper smoke JSON, and evaluator diagnostics now include scenario/visual mode fields:

```text
scenario_config_path
scenario_name
scenario_type
robot_visual_mode
component_visual_mode
robot_visual_mesh_enabled
component_mesh_enabled
component_proxy_type
component_proxy_center
component_proxy_half_extents
component_proxy_visual_visible
robot_config_path
capability_config_path
viewpoint_source
viewpoint_csv_path
```

Robot visual diagnostics also include:

```text
robot_visual_mode
robot_visual_mesh_enabled
visual_mesh_enabled_by_robot
```

## Smoke Results

Algorithm wrapper smoke:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7a2_smoke.json
status=passed
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mesh_enabled=false
component_mesh_enabled=false
component_proxy_type=bbox
visual_mesh_spawned_by_robot=false for robot_0, robot_1, robot_2
scene_creation_time_approximately=0.026 seconds
```

Algorithm evaluator smoke:

```text
output_dir=results/assignment_evaluation/algorithm_proxy_bbox_phase7a2_eval_smoke
status=passed
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mesh_enabled=false
component_mesh_enabled=false
scene_creation_time_approximately=0.024 seconds
```

Visual scenario regression smoke:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7a2_regression_smoke.json
status=passed
robot_visual_mode=mesh
component_visual_mode=mesh
robot_visual_mesh_enabled=true
component_mesh_enabled=true
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
visual_follow_enabled_by_robot=true for robot_0, robot_1, robot_2
available_actions=[1, 3, 51]
scene_creation_time_approximately=19.079 seconds
```

## Known Limitations

- `visual_mesh_exists_by_robot` can still report `true` in algorithm scenarios because robot YAML metadata points to an
  existing OBJ path. The important algorithm-path diagnostics are `robot_visual_mesh_enabled=false`,
  `visual_mesh_enabled_by_robot=false`, and `visual_mesh_spawned_by_robot=false`.
- The diagnostic helper script `diagnose_assignment_controller_feasibility.py` was not extended in this phase; the
  required wrapper/evaluator paths were updated.
- No GUI visual inspection was run.
- Synthetic viewpoint CSVs remain interface validation data only, not final benchmark evidence.

## Next Recommended Step

Implement Phase 7B-1: obstacle-aware path-cost diagnostics in the lightweight `algorithm_proxy_bbox.yaml` scenario.
Start with additional diagnostic fields only and keep existing `cost_matrix`, `available_mask`, solver behavior,
reward, and controller behavior unchanged.
