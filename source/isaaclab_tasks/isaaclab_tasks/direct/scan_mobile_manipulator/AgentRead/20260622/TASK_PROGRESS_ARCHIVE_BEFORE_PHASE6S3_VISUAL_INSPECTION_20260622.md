# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Scene Assembly Phase 6S-2 is complete.

The project now supports optional display-only robot OBJ mesh spawning for task-space proxy robots in the real-scene proxy smoke path. The mesh follows the proxy base pose kinematically, while assignment, controller, reward, evaluator, and task-space proxy behavior remain unchanged.

This remains a visual/proxy scene path. No real robot articulation, IK, collision, joint limits, raycast coverage, controller math, reward logic, `assignment_controller.py`, HARL core, training behavior, assignment-RL evaluation, or final real CSV validation was changed or run.

The final real planned viewpoint CSV remains intentionally reserved for later final validation. Temporary and synthetic CSV results are interface smoke evidence only, not final benchmark evidence.

## Latest Completed Phase

Scene Assembly Phase 6S-2: OBJ visual robot follows task-space proxy.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S2_VISUAL_MESH_FOLLOW_20260622.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_real_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/README.md
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Implementation summary:

- Added optional `visual_mesh_path` preservation to `robot_config.py`.
- Added `visual_mesh_path_by_robot` to robot config diagnostics.
- Updated `robots_real_proxy.yaml` so each enabled task-space proxy robot references the existing OBJ visual mesh.
- Added guarded OBJ visual spawning in `scan_mobile_manipulator_env.py`.
- Added kinematic visual follow after reset/step updates: visual x/y/z and yaw follow the proxy base pose.
- Added visual diagnostics to assignment problem metadata, wrapper smoke JSON, and evaluator diagnostics.
- Updated scene asset documentation and added the Phase 6S-2 report.

## Visual Mesh Config Summary

The requested path name was:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/robot_visual.obj
```

That exact file was not present. The actual OBJ in the directory is:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/robot_visual/ScanRobot.obj
```

`robots_real_proxy.yaml` now references `ScanRobot.obj` for all three enabled proxy robots. The OBJ existed and spawned successfully during wrapper and evaluator smoke checks.

## Visual Diagnostics

Diagnostics now include:

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

Phase 6S-2 smoke diagnostics:

```text
visual_mesh_exists_by_robot=true for robot_0, robot_1, robot_2
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
visual_follow_enabled_by_robot=true for robot_0, robot_1, robot_2
visual_mesh_prim_path_by_robot:
  robot_0=/World/envs/env_0/RobotVisuals/robot_0_visual
  robot_1=/World/envs/env_0/RobotVisuals/robot_1_visual
  robot_2=/World/envs/env_0/RobotVisuals/robot_2_visual
visual_usd_exists_by_robot=false for robot_0, robot_1, robot_2
visual_usd_spawned_by_robot=false for robot_0, robot_1, robot_2
```

USD visual paths remain metadata only. USD visual spawning was not implemented.

## Latest Verification

Phase 6S checks were rerun before Phase 6S-2 changes and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: assignment_state.py, scan_mobile_manipulator_env.py, test_assignment_harl_wrapper_smoke.py,
evaluate_assignment_methods.py
wrapper smoke: real_scene_proxy_headless.yaml
evaluator smoke: real_scene_proxy_headless.yaml with random/nearest/greedy
```

Phase 6S-2 checks passed:

```text
py_compile robot_config.py, scan_mobile_manipulator_env.py, test_assignment_harl_wrapper_smoke.py,
evaluate_assignment_methods.py
robot_config.py loader check for robots_real_proxy.yaml
wrapper smoke with real_scene_proxy_headless.yaml
evaluator smoke with real_scene_proxy_headless.yaml and random/nearest/greedy
```

Wrapper smoke result:

```text
result_file=results/assignment_diagnostics/scene_visual_mesh_follow_phase6s2_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
visual mesh exists/spawned/follow enabled for robot_0, robot_1, robot_2
```

Evaluator smoke result:

```text
diagnostics=results/assignment_evaluation/scene_visual_mesh_follow_phase6s2_eval_smoke/diagnostics.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
methods=random, nearest, greedy completed one CPU/headless step
visual mesh exists/spawned/follow enabled for robot_0, robot_1, robot_2
```

## Known Issues / Limitations

- The requested `robot_visual.obj` filename is absent; the actual smoke-validated OBJ is `ScanRobot.obj`.
- The OBJ is large, so scene creation is slower than the no-robot-visual path.
- Visual follow is translation plus yaw. Full 7D visual orientation remains future work.
- Visual smoke coverage used `num_envs=1`; multi-env visual replication remains unverified.
- Robot visual USD paths are preserved in diagnostics but the files are not present and are not spawned.
- The component OBJ and robot OBJ are visual-only. They do not participate in collision, IK, raycast coverage, reward, controller behavior, assignment masks, cost matrix, task status, or robot status.
- No `task_runtime_state` or `robot_runtime_state` vector fields exist yet.
- Dynamic assignment lifecycle statuses beyond conservative Phase 5 `unassigned/completed` and `idle` remain future work.
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
Review visual scale/origin for ScanRobot.obj, then decide whether to add a lighter converted USD visual, validate
multi-env visual replication, or return to dynamic assignment lifecycle/runtime-state interfaces.
```

Possible next implementation slice:

1. Add a lightweight converted USD or lower-poly visual mesh for faster scene startup.
2. Validate robot visual spawn/follow behavior for multiple environments.
3. Identify a reliable current-task ownership signal for `TASK_ASSIGNED` or `TASK_IN_PROGRESS`.
4. Keep fixed/default, temporary, and synthetic inputs as interface-validation data until final real CSV validation is intentionally scheduled.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S2_VISUAL_MESH_FOLLOW_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S_SCENE_ASSEMBLY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE5_STATE_INTERFACE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
