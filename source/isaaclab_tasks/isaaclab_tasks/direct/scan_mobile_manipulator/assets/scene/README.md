# Scene Asset Staging

This directory is the staging location for visual-only scene assets used by the scan-mobile-manipulator scene assembly path.

## Suggested Layout

```text
assets/scene/
  component/
    README.md or converted component mesh/USD files
  robots/
    robot_0_visual.usd
    robot_1_visual.usd
    robot_2_visual.usd
    robot_visual/
      ScanRobot.obj
      ScanRobot.mtl
```

## Component Assets

Place component visual assets under `assets/scene/component/` when they are ready to be tracked or referenced.

Current smoke scenarios may also reference existing project assets such as:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

STEP files should be converted to mesh or USD before use by the current scene path. The supported smoke path currently uses OBJ mesh loading for visual-only component geometry.

## Robot Assets

Place optional robot visual USD files under `assets/scene/robots/`.

Place optional robot visual mesh files under `assets/scene/robots/robot_visual/`.

The current Phase 6S-2 visual smoke path references:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
```

This OBJ is spawned as display-only USD mesh geometry and kinematically follows the task-space proxy robot pose. It is not an articulation, physics body, collision body, IK target, joint-limit model, or controller input.

Visual transform tuning is configured per robot in `robots_real_proxy.yaml`:

```yaml
visual_mesh_scale: [0.001, 0.001, 0.001]
visual_mesh_position_offset: [0.0, 0.0, 0.0]
visual_mesh_yaw_offset: 0.0
visual_mesh_align_bottom_to_proxy_z: true
```

When bottom alignment is enabled, the loader computes the scaled OBJ minimum Z and adds its negative value to the
configured position offset. With a configured Z offset of `0.0`, the visual mesh bottom therefore follows the proxy Z
without a model-specific hard-coded correction. These fields are visual-only inspection knobs. They do not affect
assignment, controller, reward, collision, IK, raycast, or task-space proxy state.

Robot visual USD paths in `robots_real_proxy.yaml` are metadata only for future work. They are not used to instantiate articulations, IK, collision bodies, joint limits, or physical robot state.

## Units And Frames

- Runtime scene coordinates are meters.
- Quaternion ordering is scalar-first `qw, qx, qy, qz`.
- Robot `initial_pose_world` uses `[x, y, z, qw, qx, qy, qz]`.
- Viewpoint CSVs use world-frame scanner poses with the existing `scanner_pose_world_quat_wxyz_v1` convention.

## Current Limitations

- Assets in this directory are visual/proxy inputs only.
- No large binary STEP, USD, or mesh files should be committed without an explicit decision.
- Visual assets do not participate in raycast coverage, collision, IK, real robot articulation, or reward logic.
- Phase 6S-3 smoke coverage uses one headless environment. GUI visual inspection and multi-env robot visual replication remain later/manual validation items.
