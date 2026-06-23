# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Scene Assembly Phase 6S-3 is complete.

The real-scene proxy path now supports optional visual-only robot mesh transform parameters for GUI inspection:

```text
visual_mesh_scale
visual_mesh_position_offset
visual_mesh_yaw_offset
```

These parameters affect only the display-only robot OBJ visual. Assignment tensors, controller math, reward logic, proxy state, HARL core, training behavior, evaluator solver logic, and final real CSV validation were not changed.

The final real planned viewpoint CSV remains intentionally reserved for later final validation. Temporary and synthetic CSV results are interface smoke evidence only, not final benchmark evidence.

## Latest Completed Phase

Scene Assembly Phase 6S-3: visual inspection parameters and GUI inspection guide.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S3_VISUAL_INSPECTION_20260622.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_real_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/README.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Implementation Summary

- Added optional `visual_mesh_scale`, `visual_mesh_position_offset`, and `visual_mesh_yaw_offset` fields to `RobotSpec`.
- Added diagnostics:
  - `visual_mesh_scale_by_robot`
  - `visual_mesh_position_offset_by_robot`
  - `visual_mesh_yaw_offset_by_robot`
- Kept absent-field defaults equivalent to Phase 6S-2:
  - scale `[0.001, 0.001, 0.001]`
  - position offset `[0.0, 0.0, 0.0]`
  - yaw offset `0.0`
- Updated `robots_real_proxy.yaml` to make those current values explicit for all three enabled task-space proxy robots.
- Updated OBJ spawn/follow so local position offset rotates with proxy yaw and yaw offset is added to proxy yaw.
- Added `SCENE_VISUAL_INSPECTION_GUIDE.md` with headless smoke and manual GUI inspection command patterns.
- Updated `assets/scene/README.md` with visual transform tuning notes.

## Visual Mesh Config Summary

The actual smoke-validated robot OBJ remains:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
```

`robots_real_proxy.yaml` now contains, for each robot:

```yaml
visual_mesh_path: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
visual_mesh_scale: [0.001, 0.001, 0.001]
visual_mesh_position_offset: [0.0, 0.0, 0.0]
visual_mesh_yaw_offset: 0.0
```

The requested `robot_visual.obj` filename is still absent; `ScanRobot.obj` is the existing visual asset.

## Latest Verification

Phase 6S-2 checks were rerun before Phase 6S-3 changes and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: robot_config.py, scan_mobile_manipulator_env.py, test_assignment_harl_wrapper_smoke.py,
evaluate_assignment_methods.py
robot_config.py loader check for robots_real_proxy.yaml
wrapper smoke: results/assignment_diagnostics/scene_visual_mesh_follow_phase6s2_rerun_before_phase6s3_smoke.json
evaluator smoke: results/assignment_evaluation/scene_visual_mesh_follow_phase6s2_rerun_before_phase6s3_eval_smoke/diagnostics.json
```

Phase 6S-3 checks passed:

```text
py_compile robot_config.py, scan_mobile_manipulator_env.py
robot_config.py loader check for robots_real_proxy.yaml
wrapper smoke with real_scene_proxy_headless.yaml
evaluator smoke with real_scene_proxy_headless.yaml and random/nearest/greedy
```

Wrapper smoke result:

```text
result_file=results/assignment_diagnostics/scene_visual_inspection_phase6s3_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
visual_mesh_exists_by_robot=true for robot_0, robot_1, robot_2
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
visual_follow_enabled_by_robot=true for robot_0, robot_1, robot_2
visual_mesh_scale_by_robot=[0.001, 0.001, 0.001] for robot_0, robot_1, robot_2
visual_mesh_position_offset_by_robot=[0.0, 0.0, 0.0] for robot_0, robot_1, robot_2
visual_mesh_yaw_offset_by_robot=0.0 for robot_0, robot_1, robot_2
```

Evaluator smoke result:

```text
diagnostics=results/assignment_evaluation/scene_visual_inspection_phase6s3_eval_smoke/diagnostics.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
methods=random, nearest, greedy completed one CPU/headless step
visual mesh exists/spawned/follow enabled for robot_0, robot_1, robot_2
visual transform diagnostics present for robot_0, robot_1, robot_2
```

## Known Issues / Limitations

- GUI inspection was not run by Codex. The guide provides a manual command pattern because the committed scenario is explicitly headless.
- The existing GUI assignment viewer does not currently consume scenario YAML, so the recommended GUI workflow is a local temporary GUI copy of the smoke scenario.
- The requested `robot_visual.obj` filename is absent; the actual smoke-validated OBJ is `ScanRobot.obj`.
- The OBJ is large, so scene creation is slower than the no-robot-visual path.
- Visual follow is translation plus yaw. Full 7D visual orientation remains future work.
- Visual smoke coverage used `num_envs=1`; multi-env visual replication remains unverified.
- Robot visual USD paths are preserved in diagnostics but the files are not present and are not spawned.
- The component OBJ and robot OBJ are visual-only. They do not participate in collision, IK, raycast coverage, reward, controller behavior, assignment masks, cost matrix, task status, or robot status.
- Temporary and synthetic CSVs must not be used as final algorithm-performance benchmarks.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not commit large STEP, USD, mesh, or generated binary assets without explicit approval.

## Next Step

Recommended next task:

```text
Run manual GUI visual inspection using SCENE_VISUAL_INSPECTION_GUIDE.md, tune visual_mesh_scale/position_offset/yaw_offset
if needed, and rerun the Phase 6S-3 headless smoke after each visual-only config adjustment.
```

Possible next implementation slice:

1. Add a committed non-headless GUI scenario only if the team wants a repeatable GUI launch file.
2. Add a lightweight converted USD or lower-poly visual mesh for faster scene startup.
3. Validate robot visual spawn/follow behavior for multiple environments.
4. Return to dynamic assignment lifecycle/runtime-state interfaces after visual scene acceptance.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S3_VISUAL_INSPECTION_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S2_VISUAL_MESH_FOLLOW_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S_SCENE_ASSEMBLY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE5_STATE_INTERFACE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
