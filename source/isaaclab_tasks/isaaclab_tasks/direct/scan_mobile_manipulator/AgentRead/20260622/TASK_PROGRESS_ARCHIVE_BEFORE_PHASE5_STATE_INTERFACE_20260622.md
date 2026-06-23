# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Simulation Readiness Phase 4 is complete. The task-space proxy environment and baseline evaluator were smoke-verified
across fixed/default, temporary, and synthetic legal viewpoint sources without using the final real planned viewpoint
CSV.

Verified invariant:

```text
N = loaded viewpoints
M = enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

No controller math, reward logic, HARL core, training behavior, assignment-RL evaluation, real robot articulation, IK,
collision, joint limits, raycast coverage, or final real CSV validation was changed or run.

The final real planned viewpoint CSV is intentionally reserved for later final validation. Its absence is not a blocker
for Robot Config MVP or simulation-readiness validation.

## Latest Completed Phase

Simulation Readiness Phase 4: multi-`N` smoke validation.

Added files:

```text
scripts/environments/generate_synthetic_viewpoints.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n50.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n100.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n200.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Implementation summary:

- Added a deterministic synthetic viewpoint CSV generator with no Isaac Lab, GPU, or GUI dependency.
- Generated `synthetic_smoke` CSVs for `N=50`, `N=100`, and `N=200`.
- Used the existing fixed/default path for `N=12`.
- Used `real_component_bbox_sample.csv` through `real_component_bbox_sample_headless.yaml` for temporary `N=24`, so the
  matching mesh-derived component proxy is present.
- Verified wrapper and evaluator interface shapes across selected `N` and `M` values.

## Synthetic CSV Schema

The strict viewpoint CSV format is `scanner_pose_world_quat_wxyz_v1`.

Columns:

```text
id, pose_type, coordinate_frame, units, quaternion_order, scanner_forward_axis, scanner_up_axis,
viewpoint_quaternion_meaning, x, y, z, qw, qx, qy, qz
```

Required row conventions:

```text
pose_type=scanner_pose_in_world
coordinate_frame=world
units=meters
quaternion_order=qw,qx,qy,qz
scanner_forward_axis=+X
scanner_up_axis=+Z
viewpoint_quaternion_meaning=scanner_frame_orientation_in_world
```

IDs are contiguous zero-based file-order IDs. Pose values are stored as `[x, y, z, qw, qx, qy, qz]` with unit
quaternions.

## Latest Verification

Phase 3 lightweight checks were rerun before Phase 4 work and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: robot_config.py, scenario_config.py, scan_mobile_manipulator_env.py, wrapper/evaluator/diagnostic scripts
loader checks: robots_two_proxy.yaml, robots_three_proxy.yaml, robots_four_proxy.yaml
fixed-12 wrapper smokes: M=2, M=3, M=4
fixed-12 evaluator smoke: M=3 random/nearest/greedy
```

Generated CSV loader checks passed:

```text
real_component_bbox_sample.csv: N=24
synthetic_smoke_n50.csv: N=50
synthetic_smoke_n100.csv: N=100
synthetic_smoke_n200.csv: N=200
```

Wrapper smoke results:

```text
N=12, M=2: noop_id=12, available_actions=[1, 2, 13]
N=12, M=3: noop_id=12, available_actions=[1, 3, 13]
N=12, M=4: noop_id=12, available_actions=[1, 4, 13]
N=24, M=3: noop_id=24, available_actions=[1, 3, 25]
N=50, M=2: noop_id=50, available_actions=[1, 2, 51]
N=50, M=3: noop_id=50, available_actions=[1, 3, 51]
N=50, M=4: noop_id=50, available_actions=[1, 4, 51]
N=100, M=3: noop_id=100, available_actions=[1, 3, 101]
N=200, M=3: noop_id=200, available_actions=[1, 3, 201]
```

Evaluator smoke results:

```text
N=12, M=3: noop_id=12, available_actions=[1, 3, 13], available_mask=[1, 3, 12], cost_matrix=[1, 3, 12]
N=24, M=3: noop_id=24, available_actions=[1, 3, 25], available_mask=[1, 3, 24], cost_matrix=[1, 3, 24]
N=50, M=3: noop_id=50, available_actions=[1, 3, 51], available_mask=[1, 3, 50], cost_matrix=[1, 3, 50]
N=100, M=3: noop_id=100, available_actions=[1, 3, 101], available_mask=[1, 3, 100], cost_matrix=[1, 3, 100]
N=200, M=3: noop_id=200, available_actions=[1, 3, 201], available_mask=[1, 3, 200], cost_matrix=[1, 3, 200]
```

For each evaluator smoke, `random`, `nearest`, and `greedy` completed one CPU/headless step and wrote diagnostics.
These one-step outputs are not benchmark evidence.

Additional verification:

```text
py_compile scripts/environments/generate_synthetic_viewpoints.py: passed
git diff --check: passed with LF-to-CRLF normalization warnings only
custom whitespace check for new Phase 4 files: passed
```

## Known Issues / Blockers

- No current blocker for simulation-interface smoke validation.
- A direct CSV-only `N=24` attempt with the default component proxy was not used as the validating path because the
  temporary bbox-side sample expects the real-component mesh-derived proxy. The matching scenario path passed.
- `real_component_bbox_sample.csv` is temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Temporary and synthetic CSVs must not be used as final algorithm-performance benchmarks.
- Stage 4B temporary-sample diagnostics exposed controller/gate/orientation timing issues, but those should not be tuned
  as final benchmark failures.
- Only `mobile_scanner_a`, `mobile_scanner_b`, and `mobile_scanner_c` are supported task-space proxy capability profiles.
- Full 7D `initial_pose_world` is preserved in diagnostics, but the current proxy state remains yaw-only.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not tune controller/gate/orientation behavior specifically to temporary or synthetic CSV samples.
- Do not introduce unknown capability profiles unless explicitly adding and testing profile support.

## Next Step

Recommended next task:

```text
Review and accept the simulation-readiness smoke evidence, then plan the next dynamic assignment extension without
expanding into controller/reward/HARL/training or final real CSV work.
```

Possible next implementation slice after acceptance:

1. Add a small repeatable smoke-runner or documentation command block for the accepted `N/M` matrix.
2. Decide the first dynamic assignment extension point to expose, such as runtime task/robot status fields, without
   implementing reassignment policy training.
3. Keep fixed/default, temporary, and synthetic inputs as interface-validation data until final real CSV validation is
   intentionally scheduled.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
