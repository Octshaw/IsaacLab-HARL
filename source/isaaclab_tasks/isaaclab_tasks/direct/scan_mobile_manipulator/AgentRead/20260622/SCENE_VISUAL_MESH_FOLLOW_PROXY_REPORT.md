# Scene Visual Mesh Follow Proxy Report

## Purpose

Phase 6S-2 adds optional display-only robot OBJ mesh support for task-space proxy robots.

The task-space proxy remains the control, assignment, reward, and evaluator model. The robot mesh is visual-only and follows the proxy pose kinematically.

## Asset Used

Requested phase input:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/robot_visual.obj
```

Observed asset directory contents:

```text
ScanRobot.obj
ScanRobot.mtl
ScanRobot.usd.back
```

Because `robot_visual.obj` was not present, the smoke-validated config uses the existing OBJ:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
```

The OBJ exists and was spawned successfully in the headless smoke path.

## Config Field Added

`robot_config.py` now preserves optional robot metadata:

```yaml
visual_mesh_path: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
```

Diagnostics now include:

```text
visual_mesh_path_by_robot
```

The loader does not require `visual_mesh_path` or `visual_usd_path` to exist. Missing visual assets are reported by environment diagnostics instead of failing robot config loading.

## Spawn Behavior

`scan_mobile_manipulator_env.py` resolves optional mesh paths and, when the OBJ exists, spawns a non-articulated USD mesh under:

```text
/World/envs/env_0/RobotVisuals/robot_0_visual
/World/envs/env_0/RobotVisuals/robot_1_visual
/World/envs/env_0/RobotVisuals/robot_2_visual
```

The mesh is loaded through the existing OBJ mesh path style used for visual scene geometry. The robot visual mesh scale is currently:

```text
(0.001, 0.001, 0.001)
```

This is visual geometry only. It is not a physics body, collision body, articulation, IK model, joint-limit model, raycast target, reward input, controller input, assignment input, or solver input.

## Pose Follow Behavior

After reset and step updates, spawned robot visual meshes follow the corresponding task-space proxy base pose:

```text
visual x/y/z follows proxy x/y/z
visual yaw follows proxy yaw
```

Full 7D robot visual orientation remains future work. The current task-space proxy state is still yaw-based.

## Diagnostics Added

Environment, wrapper smoke, and evaluator diagnostics expose:

```text
visual_mesh_path_by_robot
visual_mesh_resolved_path_by_robot
visual_mesh_exists_by_robot
visual_mesh_spawned_by_robot
visual_mesh_prim_path_by_robot
visual_follow_enabled_by_robot
visual_mesh_error_by_robot
visual_usd_path_by_robot
visual_usd_resolved_path_by_robot
visual_usd_exists_by_robot
visual_usd_spawned_by_robot
```

For Phase 6S-2, USD visual paths remain metadata only and are not spawned.

## Smoke Results

Wrapper smoke:

```text
command: test_assignment_harl_wrapper_smoke.py with real_scene_proxy_headless.yaml
result_file: results/assignment_diagnostics/scene_visual_mesh_follow_phase6s2_smoke.json
status: passed
N=50
M=3
noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
visual_mesh_exists_by_robot=true for robot_0/robot_1/robot_2
visual_mesh_spawned_by_robot=true for robot_0/robot_1/robot_2
visual_follow_enabled_by_robot=true for robot_0/robot_1/robot_2
```

Evaluator smoke:

```text
command: evaluate_assignment_methods.py with real_scene_proxy_headless.yaml and random/nearest/greedy
diagnostics: results/assignment_evaluation/scene_visual_mesh_follow_phase6s2_eval_smoke/diagnostics.json
status: passed
N=50
M=3
noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
random/nearest/greedy completed one CPU/headless step
visual_mesh_exists_by_robot=true for robot_0/robot_1/robot_2
visual_mesh_spawned_by_robot=true for robot_0/robot_1/robot_2
visual_follow_enabled_by_robot=true for robot_0/robot_1/robot_2
```

## Limitations

- The requested `robot_visual.obj` filename was not present; `ScanRobot.obj` is the actual smoke-validated OBJ.
- Visual smoke coverage used one headless environment. Multi-env visual replication is not yet validated.
- Robot visual pose sync is yaw-only plus translation.
- The large OBJ adds scene creation time, but the one-step headless smoke remained lightweight enough for this phase.
- No visual USD spawning is implemented; USD paths remain future metadata.
- Temporary and synthetic viewpoint CSVs remain smoke/interface validation data only, not final benchmark evidence.

## Next Recommended Step

Review the visual scale/origin of `ScanRobot.obj` in a rendering pass, then decide whether to:

1. add a lighter converted USD visual asset for faster headless scene assembly;
2. validate multi-env visual spawning/following;
3. return to dynamic assignment lifecycle status work.

Do not add real articulation, IK, collision, raycast coverage, reward changes, controller changes, HARL changes, training, assignment-RL evaluation, or final real CSV validation as part of this visual-only path.
