# Scene Visual Inspection Guide

## Purpose

This guide prepares the Phase 6S-3 visual inspection workflow for the real-scene proxy setup.

The goal is to inspect the display-only robot OBJ visual relative to the task-space proxy robots and component visual. This guide is not a real robot, IK, collision, raycast, dynamics, reward, controller, training, assignment-RL, or final benchmark validation.

## Visual Transform Fields

`robots_real_proxy.yaml` exposes per-robot visual-only transform fields:

```yaml
visual_mesh_scale: [0.001, 0.001, 0.001]
visual_mesh_position_offset: [0.0, 0.0, 0.0]
visual_mesh_yaw_offset: 0.0
visual_mesh_align_bottom_to_proxy_z: true
```

Current values preserve the Phase 6S-2 behavior for `ScanRobot.obj`.

- `visual_mesh_scale` is baked into the OBJ vertex payload before USD mesh creation.
- `visual_mesh_position_offset` is a local proxy-frame offset applied when syncing the visual prim.
- `visual_mesh_yaw_offset` is added to the proxy yaw when syncing the visual prim.
- `visual_mesh_align_bottom_to_proxy_z` automatically subtracts the scaled OBJ minimum Z from the configured offset.

For the current `ScanRobot.obj`, the automatic values are approximately:

```text
scaled local minimum Z=2.279909 m
automatic bottom offset Z=-2.279909 m
effective position offset=[0.0, 0.0, -2.279909]
```

These values only affect display-only robot visual prims.

## Headless Smoke Command

Use this command after visual transform edits to verify that assignment/evaluator-facing shapes remain stable:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml --result_file results/assignment_diagnostics/scene_visual_inspection_phase6s3_smoke.json
```

Expected smoke shapes:

```text
N=50
M=3
noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
```

Expected visual diagnostics:

```text
visual_mesh_exists_by_robot=true for robot_0/robot_1/robot_2
visual_mesh_spawned_by_robot=true for robot_0/robot_1/robot_2
visual_follow_enabled_by_robot=true for robot_0/robot_1/robot_2
visual_mesh_scale_by_robot present for robot_0/robot_1/robot_2
visual_mesh_position_offset_by_robot present for robot_0/robot_1/robot_2
visual_mesh_yaw_offset_by_robot present for robot_0/robot_1/robot_2
```

## GUI Inspection Command Pattern

The current committed scenario is intentionally named `real_scene_proxy_headless.yaml` and contains:

```yaml
headless: true
```

For manual GUI inspection, create a local temporary copy of that scenario with `headless: false`, keep the same robot/config/viewpoint paths, and run the same smoke script for a few steps.

Command pattern:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 20 --device cpu --scenario_config <local_gui_scene_yaml> --result_file results/assignment_diagnostics/scene_visual_inspection_phase6s3_gui_manual.json
```

If the local AppLauncher build supports a command-line headless override, the same scenario may be usable with that override instead of creating a local GUI copy. This guide leaves that as a manual launch adjustment because the committed smoke scenario is headless by design.

## What To Inspect

Check the following visually:

```text
robot scale relative to the component and proxy base markers
robot origin/alignment relative to proxy base x/y/z
robot yaw direction relative to proxy yaw and movement direction
robot placement around the component
visual follow after several steps
whether the large OBJ blocks inspection of scanner/viewpoint markers
```

Suggested tuning order:

1. Adjust `visual_mesh_scale` until the robot looks plausible in meters.
2. Adjust `visual_mesh_position_offset` until the visual base aligns with the proxy base marker.
3. Adjust `visual_mesh_yaw_offset` until the robot forward direction matches proxy yaw.
4. Re-run the headless smoke after every config change.

## What Not To Conclude

Do not treat this inspection as evidence of:

```text
IK correctness
collision correctness
joint-limit correctness
raycast coverage correctness
real robot dynamics
controller quality
reward quality
assignment-RL behavior
algorithm performance
final real CSV readiness
```

Temporary and synthetic viewpoint CSVs remain smoke/interface validation data only, not final benchmark evidence.
