# Phase 9B-2 Observation Update Smoke Report

Date: 2026-06-29

## Scope And Boundaries

Phase 9B-2 implements a minimal fixed-scale observation update for the assignment HARL wrapper at N=50, M=3.
The goal is to expose id-aligned viewpoint rows and lightweight dynamic assignment memory needed by the Phase 9B-1A
plateau diagnosis.

This phase did not start RL training, did not evaluate checkpoints, and did not run formal RL evaluation. It did not
change rewards, action mask semantics, feasible masks, static geometric feasibility, solver behavior, controller logic,
HARL internals, environment dynamics, robot motion, collision, IK, raycast, local avoidance, path planning, retry,
fallback, cooldown behavior, or handcrafted baseline rules.

## Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
```

The environment implementation, reward code, solver code, controller code, HARL package code, and mask/feasibility
construction were not modified.

## Observation Fields Added

The wrapper now preserves the original per-agent env observation as the first 96 fields, then appends an assignment
extension. For the N=50 smoke, actor observation is:

```text
raw env obs:                  96
id-aligned viewpoint rows:    50 * 14 = 700
noop context block:           5
previous assignment one-hot:  51
dynamic scalar block:         7
covered vector:               50
total actor obs:              909
```

Each viewpoint row `j` is ordered exactly by action id `j` and contains:

```text
relative_viewpoint_position_x
relative_viewpoint_position_y
relative_viewpoint_position_z
viewpoint_quaternion_w
viewpoint_quaternion_x
viewpoint_quaternion_y
viewpoint_quaternion_z
covered_flag
available_flag
feasible_flag
static_geometric_feasible_flag
normalized_selected_path_cost
per_viewpoint_attempted_count_norm
per_viewpoint_last_attempt_age_norm
```

The noop context block is separate from the viewpoint table:

```text
agent_has_any_available_viewpoint
team_has_any_available_viewpoint
all_viewpoints_covered
previous_assignment_was_noop
episode_progress_norm
```

The dynamic assignment block contains:

```text
previous_assignment_id_one_hot[0..50]
consecutive_same_target_count_norm
steps_since_last_global_coverage_gain_norm
per_robot_completed_count_norm
per_robot_repeated_assignment_count_norm
global_coverage_ratio
total_uncovered_count_norm
episode_progress_norm
covered_vector[0..49]
```

The new diagnostic state is maintained only inside `AssignmentHarlWrapper`, resets on wrapper reset, updates after each
decoded assignment step, and is used only to build observations.

## Layout Summary

Smoke output layout:

```text
raw_observation_dim = 96
assignment_extension_dim = 813
actor_observation_shape = [1, 909] per robot
shared_observation_shape = [1, 3, 2727]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
viewpoint_rows_start = 96
viewpoint_row_dim = 14
noop_context_start = 796
previous_assignment_one_hot_start = 801
dynamic_scalar_start = 852
covered_vector_start = 859
normalization_horizon = 300
```

The centralized shared observation remains the concatenation of the augmented actor observations, repeated for each
agent in HARL-compatible shape.

## Row / Action Alignment Verification

The smoke verifies row/action alignment for `robot_0`, viewpoint/action id `0`.

```text
row_start = 96
row_dim = 14
action_id = 0
viewpoint_id = 0
relative_position = [0.5918154120, 0.1356451660, 0.0425468870]
normalized_selected_path_cost = 0.6086503863
available_flag = 1.0
covered_flag = 0.0
```

The test directly compares the row values against `get_assignment_problem()` tensors for viewpoint id `0`: relative
position, quaternion, covered flag, available flag, feasible flag, static feasible flag, and normalized cost.

## Reset / Update Behavior

On wrapper reset:

```text
attempted counts = 0
previous assignment = noop/no previous
same-target streak = 0
steps since global gain = 0
per-robot completed/repeated counts = 0
last-attempt age = 1.0 for never-attempted rows
```

After the first manual step with assignment `[[0, 1, -1]]`, the observation changed and row 0 history updated:

```text
observation_changed_after_step = true
viewpoint 0 attempted_count_norm: 0.0 -> 0.0033333334
viewpoint 0 last_attempt_age_norm: 1.0 -> 0.0
```

This confirms the new history state updates online without altering rewards, masks, controller output, or env dynamics.

## Smoke Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9b2_observation_update_smoke_n50_m3.json
```

Output path:

```text
results/assignment_diagnostics/phase9b2_observation_update_smoke_n50_m3.json
```

Result:

```text
[OK] assignment HARL wrapper smoke passed
```

## Verification

Compile check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Result:

```text
passed
```

Smoke assertions covered:

```text
num_agents = 3
num_viewpoints = 50
noop_id = 50
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
observations finite = true
shared observation finite = true
observation changes after step = true
row/action alignment check = passed for viewpoint/action id 0
```

`git diff --check` passed with Windows LF-to-CRLF warnings only and no whitespace errors.

## Known Limitations

This is a fixed N=50 MLP-style flattened observation. It is not yet an arbitrary-N set, Transformer, or GNN policy
interface.

The wrapper tracks `per_robot_completed_count` from newly covered viewpoints and selected ids at the wrapper level.
It is observation-only and should not be treated as a replacement for environment reward credit.

Conflict, inter-robot overlap, and actual base-motion crossing remain reporting/diagnostic signals. They were not added
as reward terms or hard masks in this phase.

The noop action remains always available. Phase 9B-2 only exposes noop context; it does not change noop mask semantics.

## Explicit Non-Changes

Phase 9B-2 did not change:

```text
reward behavior
available_mask semantics
feasible_mask semantics
static_geometric_feasible_mask semantics
solver behavior
controller logic
HARL internals or installed site-packages
environment dynamics
robot motion
collision, IK, raycast, local avoidance, path planning
retry, fallback, or cooldown behavior
RL training
formal RL evaluation
handcrafted baseline rules
```

## Next Recommended Step

Proceed only to a scoped Phase 9B-3 reward implementation smoke after reviewing the observation JSON and deciding which
signals should remain reporting-only. Do not start RL training or formal RL evaluation yet.
