# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Dynamic Assignment State Interface MVP Phase 5 is complete.

The assignment problem interface now exposes conservative runtime status metadata for future dynamic task allocation:

```text
task_status shape = [num_envs, N]
robot_status shape = [num_envs, M]
task_status_names
robot_status_names
```

The existing shape invariant remains verified:

```text
N = loaded viewpoints
M = enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

No controller math, reward logic, `assignment_controller.py`, HARL core, training behavior, assignment-RL evaluation,
real robot articulation, IK, collision, joint limits, raycast coverage, or final real CSV validation was changed or run.

The final real planned viewpoint CSV remains intentionally reserved for later final validation. Its absence is not a
blocker for Robot Config MVP, simulation-readiness validation, or this state-interface MVP.

## Latest Completed Phase

Dynamic Assignment State Interface MVP Phase 5.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE5_STATE_INTERFACE_20260622.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Implementation summary:

- Added repo-local task and robot status constants plus diagnostic name maps.
- Added `task_status`, `robot_status`, `task_status_names`, and `robot_status_names` to `get_assignment_problem()`.
- Added status shape/count diagnostics to wrapper and evaluator smoke outputs.
- Added wrapper-side assertions and JSON fields for `available_mask_shape` and `cost_matrix_shape`.
- Preserved baseline solver behavior: `random`, `nearest`, and `greedy` still consume `available_mask`, `cost_matrix`,
  and `noop_id`.

## Status Semantics Implemented

Task status IDs:

```text
0 unassigned
1 assigned
2 in_progress
3 completed
4 failed
5 unreachable
6 timeout
```

Robot status IDs:

```text
0 idle
1 moving
2 scanning
3 blocked
4 failed
5 disabled
```

Current conservative mapping:

```text
viewpoints_covered == true  -> TASK_COMPLETED
viewpoints_covered == false -> TASK_UNASSIGNED
active enabled robot row     -> ROBOT_IDLE
```

Fields intentionally not inferred yet:

```text
TASK_ASSIGNED
TASK_IN_PROGRESS
TASK_FAILED
TASK_UNREACHABLE
TASK_TIMEOUT
ROBOT_MOVING
ROBOT_SCANNING
ROBOT_BLOCKED
ROBOT_FAILED
ROBOT_DISABLED
```

Existing signals inspected but not promoted yet:

```text
dwell_counter: coverage gate bookkeeping, not persistent assigned/in_progress state
last_reach_violation: penalty/debug signal, not persistent blocked/failed state
scanner/base pose buffers: useful future runtime state inputs, not status by themselves
available/feasible masks: assignment availability signals, not task lifecycle status
```

## Latest Verification

Phase 4 lightweight checks were rerun before Phase 5 changes and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: scan_mobile_manipulator_env.py, wrapper/evaluator scripts, generate_synthetic_viewpoints.py
baseline wrapper smoke: N=12/M=3 and N=50/M=3
baseline evaluator smoke: N=12/M=3 and N=50/M=3 with random/nearest/greedy
```

Phase 5 syntax checks passed:

```text
py_compile: assignment_state.py, scan_mobile_manipulator_env.py, test_assignment_harl_wrapper_smoke.py,
evaluate_assignment_methods.py
```

Wrapper smoke results:

```text
N=12, M=2: noop_id=12, available_actions=[1, 2, 13], available_mask=[1, 2, 12], cost_matrix=[1, 2, 12], task_status=[1, 12], robot_status=[1, 2]
N=12, M=3: noop_id=12, available_actions=[1, 3, 13], available_mask=[1, 3, 12], cost_matrix=[1, 3, 12], task_status=[1, 12], robot_status=[1, 3]
N=12, M=4: noop_id=12, available_actions=[1, 4, 13], available_mask=[1, 4, 12], cost_matrix=[1, 4, 12], task_status=[1, 12], robot_status=[1, 4]
N=50, M=3: noop_id=50, available_actions=[1, 3, 51], available_mask=[1, 3, 50], cost_matrix=[1, 3, 50], task_status=[1, 50], robot_status=[1, 3]
```

Evaluator smoke results:

```text
N=12, M=2: noop_id=12, available_actions=[1, 2, 13], available_mask=[1, 2, 12], cost_matrix=[1, 2, 12], task_status=[1, 12], robot_status=[1, 2]
N=12, M=3: noop_id=12, available_actions=[1, 3, 13], available_mask=[1, 3, 12], cost_matrix=[1, 3, 12], task_status=[1, 12], robot_status=[1, 3]
N=12, M=4: noop_id=12, available_actions=[1, 4, 13], available_mask=[1, 4, 12], cost_matrix=[1, 4, 12], task_status=[1, 12], robot_status=[1, 4]
N=50, M=3: noop_id=50, available_actions=[1, 3, 51], available_mask=[1, 3, 50], cost_matrix=[1, 3, 50], task_status=[1, 50], robot_status=[1, 3]
```

Status counts in all Phase 5 one-step smokes:

```text
task_status: unassigned=N, completed=0, all other task statuses=0
robot_status: idle=M, all other robot statuses=0
```

For each evaluator smoke, `random`, `nearest`, and `greedy` completed one CPU/headless step and wrote diagnostics.
These one-step outputs are not benchmark evidence.

## Known Issues / Limitations

- `TASK_ASSIGNED` and `TASK_IN_PROGRESS` are enum extension points only.
- `ROBOT_MOVING` and `ROBOT_SCANNING` are enum extension points only.
- Blocked, failed, unreachable, and timeout states are not populated yet.
- No `task_runtime_state` or `robot_runtime_state` vector fields were added in Phase 5.
- Disabled robots are filtered out before the active assignment problem and do not appear in `robot_status`.
- `real_component_bbox_sample.csv` remains temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Temporary and synthetic CSVs must not be used as final algorithm-performance benchmarks.
- Full 7D `initial_pose_world` is preserved in robot config diagnostics, but the current proxy state remains yaw-only.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not tune controller/gate/orientation behavior specifically to temporary or synthetic CSV samples.
- Do not implement full reassignment policy until lifecycle signals and policy boundaries are explicitly planned.

## Next Step

Recommended next task:

```text
Plan the next dynamic assignment extension around lifecycle-backed assigned/in-progress semantics or optional runtime
state vectors, while keeping baseline solvers and controller/reward/training paths unchanged.
```

Possible next implementation slice:

1. Identify a reliable current-task ownership signal for `TASK_ASSIGNED` or `TASK_IN_PROGRESS`.
2. Add optional `robot_runtime_state` diagnostics for pose and active target ID if it can be derived without behavior changes.
3. Keep fixed/default, temporary, and synthetic inputs as interface-validation data until final real CSV validation is
   intentionally scheduled.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE5_STATE_INTERFACE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
