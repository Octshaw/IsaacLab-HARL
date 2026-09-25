# Dynamic Assignment State Interface MVP Report

Date: 2026-06-22

## Purpose

Phase 5 adds the first dynamic assignment extension point: explicit runtime task and robot status fields in the assignment problem interface and smoke diagnostics.

This is an interface and diagnostics MVP only. It does not implement dynamic reassignment policy, assignment-RL training, reward changes, controller changes, IK, collision, real robot articulation, raycast coverage, or final real planned CSV validation.

Temporary and synthetic viewpoint sets remain smoke-validation inputs only. They are not final algorithm-performance benchmark evidence.

## Status Enums

Task status IDs:

```text
0: unassigned
1: assigned
2: in_progress
3: completed
4: failed
5: unreachable
6: timeout
```

Robot status IDs:

```text
0: idle
1: moving
2: scanning
3: blocked
4: failed
5: disabled
```

The enum constants and diagnostic name maps live in:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
```

## Existing Signal Mapping

Implemented task mapping:

```text
viewpoints_covered == true  -> TASK_COMPLETED
viewpoints_covered == false -> TASK_UNASSIGNED
```

Implemented robot mapping:

```text
enabled robot rows in the active assignment problem -> ROBOT_IDLE
```

Signals inspected but not promoted to status semantics yet:

```text
dwell_counter: coverage gate bookkeeping, not persistent assigned/in_progress state
last_reach_violation: penalty/debug signal, not persistent blocked/failed state
scanner/base pose buffers: useful future runtime state inputs, not status by themselves
available/feasible masks: assignment availability signals, not task lifecycle status
```

Assigned, in-progress, moving, scanning, blocked, failed, unreachable, and timeout remain reserved extension points until the environment has reliable lifecycle signals for them.

## Assignment Problem Fields Added

`get_assignment_problem()` now returns additive metadata:

```text
task_status shape = [num_envs, N]
robot_status shape = [num_envs, M]
task_status_names
robot_status_names
```

The existing assignment fields remain unchanged:

```text
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

Baseline solvers continue to consume `available_mask`, `cost_matrix`, and `noop_id`.

## Diagnostics Added

Wrapper smoke diagnostics now report and assert:

```text
available_actions_shape
available_mask_shape
cost_matrix_shape
task_status_shape
robot_status_shape
task_status_counts
robot_status_counts
task_status_names
robot_status_names
```

Evaluator diagnostics now report and assert:

```text
available_actions_shape
available_mask_shape
cost_matrix_shape
task_status_shape
robot_status_shape
task_status_counts
robot_status_counts
task_status_names
robot_status_names
```

## Smoke Matrix

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

Status counts in all one-step smokes:

```text
task_status: unassigned=N, completed=0, all other task statuses=0
robot_status: idle=M, all other robot statuses=0
```

For every evaluator smoke, `random`, `nearest`, and `greedy` completed one CPU/headless step and wrote diagnostics.

## Commands

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/evaluate_assignment_methods.py
```

Representative wrapper smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --result_file results/assignment_diagnostics/state_interface_phase5_n12_m3_smoke.json
```

Representative evaluator smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --output_dir results/assignment_evaluation --output_name state_interface_phase5_n12_m3_eval_smoke --no-write_assignment_history
```

Synthetic N=50 smokes used:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n50.csv
```

## Limitations

- `TASK_ASSIGNED` and `TASK_IN_PROGRESS` are not populated yet.
- `ROBOT_MOVING` and `ROBOT_SCANNING` are not populated yet.
- Blocked, failed, unreachable, and timeout states are enum extension points only.
- No `task_runtime_state` or `robot_runtime_state` vector fields were added in this phase.
- Disabled robots are filtered out before the active assignment problem and do not appear in `robot_status`.
- The smokes are one-step interface checks, not performance benchmarks.

## Next Recommended Extension

Add lifecycle-backed assigned/in-progress semantics only after a stable source of current task ownership and task execution state is identified. A conservative next slice could expose optional runtime state vectors for robot pose and active target ID while keeping baseline solvers unchanged.
