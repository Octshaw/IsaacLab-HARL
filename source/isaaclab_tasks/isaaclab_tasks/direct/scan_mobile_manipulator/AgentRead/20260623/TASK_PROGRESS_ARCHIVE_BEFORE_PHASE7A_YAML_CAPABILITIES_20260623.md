# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Scene Assembly Phase 6S-4 is complete.

The display-only robot OBJ path now supports automatic bottom alignment to each task-space proxy robot Z position:

```text
visual_mesh_align_bottom_to_proxy_z: true
```

The environment computes the scaled OBJ minimum Z and adds its negative value to the configured visual position offset.
This removes the need to hard-code a model-specific Z correction such as `-2.2799` in robot YAML.

This is a visual-only change. Assignment tensors, controller math, reward logic, proxy state, HARL core, training behavior,
evaluator solver logic, collision, IK, raycast coverage, and final real CSV validation were not changed.

## Latest Completed Phase

Scene Assembly Phase 6S-4: automatic robot visual bottom alignment.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S4_AUTO_BOTTOM_ALIGN_20260622.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_real_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/README.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Implementation Summary

- Added optional `RobotSpec.visual_mesh_align_bottom_to_proxy_z`, defaulting to `false` for backward compatibility.
- Added strict boolean YAML validation for the new field.
- Added config diagnostics:
  - `visual_mesh_align_bottom_to_proxy_z_by_robot`
- The OBJ visual payload now returns the minimum Z after applying `visual_mesh_scale`.
- When automatic alignment is enabled:

```text
auto_bottom_offset_z = -scaled_local_min_z
effective_position_offset_z = configured_position_offset_z + auto_bottom_offset_z
```

- Initial visual spawn and every subsequent visual-follow update use the same effective position offset.
- Added runtime diagnostics:
  - `visual_mesh_local_min_z_by_robot`
  - `visual_mesh_auto_bottom_offset_z_by_robot`
  - `visual_mesh_effective_position_offset_by_robot`
- Enabled automatic alignment for all three robots in `robots_real_proxy.yaml`.
- Updated scene asset and visual inspection documentation.

## Current Robot Visual Config

Each robot in `robots_real_proxy.yaml` now uses:

```yaml
visual_mesh_path: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
visual_mesh_scale: [0.001, 0.001, 0.001]
visual_mesh_position_offset: [0.0, 0.0, 0.0]
visual_mesh_yaw_offset: 0.0
visual_mesh_align_bottom_to_proxy_z: true
```

`visual_mesh_position_offset` remains available as an additional local-frame manual adjustment after automatic bottom
alignment. `initial_pose_world` is unchanged and still controls the task-space proxy pose.

## Verification

Passed syntax checks:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile robot_config.py scan_mobile_manipulator_env.py
```

Passed loader checks:

```text
robots_real_proxy.yaml
robots_two_proxy.yaml
robots_three_proxy.yaml
robots_four_proxy.yaml
```

The real proxy loader reports:

```text
visual_mesh_align_bottom_to_proxy_z_by_robot=true for robot_0, robot_1, robot_2
```

Passed one-step CPU/headless wrapper smoke:

```text
result_file=results/assignment_diagnostics/scene_visual_auto_bottom_align_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
```

Automatic alignment diagnostics for all three robots:

```text
visual_mesh_local_min_z=2.27990917969
visual_mesh_auto_bottom_offset_z=-2.27990917969
visual_mesh_effective_position_offset=[0.0, 0.0, -2.27990917969]
visual_mesh_exists=true
visual_mesh_spawned=true
visual_follow_enabled=true
visual_mesh_error=null
```

The smoke completed one environment step, confirming that the effective offset remains active during visual following.

## Known Issues / Limitations

- GUI visual inspection was not run by Codex; headless diagnostics verify transforms but not viewport appearance.
- The existing GUI assignment viewer does not consume scenario YAML directly.
- The requested `robot_visual.obj` filename is absent; the current asset is `ScanRobot.obj`.
- The OBJ is large, so scene creation remains slower than the no-robot-visual path.
- Automatic alignment currently targets the minimum scaled local Z. Full arbitrary roll/pitch visual orientation is not supported.
- Visual smoke coverage used `num_envs=1`; multi-env visual replication remains unverified.
- Robot visual USD paths remain metadata only and are not spawned.
- Temporary and synthetic CSVs remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Run manual GUI inspection using SCENE_VISUAL_INSPECTION_GUIDE.md. Keep automatic bottom alignment enabled and use
visual_mesh_position_offset only for small visual origin adjustments that remain after bottom alignment.
```

After visual acceptance, either validate multi-env visual replication or return to dynamic assignment lifecycle/runtime
state work.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S4_AUTO_BOTTOM_ALIGN_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S3_VISUAL_INSPECTION_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S2_VISUAL_MESH_FOLLOW_20260622.md
```
