# Phase 9B-1 Reporting-Only Counters Report

Date: 2026-06-28

## Scope And Boundaries

Phase 9B-1 adds reporting-only counters for RL/dynamic assignment diagnostics. The purpose is to make Phase 8 failure
modes measurable in existing evaluator outputs before any observation or reward changes.

This phase did not start RL training. It did not run formal RL evaluation. It did not change reward behavior,
observation behavior, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver behavior, controller
logic, HARL internals, environment dynamics, robot motion, collision, IK, raycast, local avoidance, path planning,
retry, fallback, cooldown behavior, or handcrafted baseline rules.

## Files Changed

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
```

No environment, reward, solver, controller, HARL, or installed package files were changed.

## Implementation Summary

The counters are derived in the evaluator/reporting pipeline from existing per-step data:

```text
assignment tensor
problem["available_mask"]
problem["cost_matrix"]
covered_before / covered_after masks
existing assignment_history rows
existing episode buffers
```

The implementation adds reporting buffers and CSV/JSON fields only. It does not feed these counters back into action
selection, masks, rewards, resets, dones, robot movement, solver choice, or controller behavior.

## Counters Added

Episode-level counters:

```text
per_robot_selected_count
per_robot_completed_count
per_robot_repeated_assignment_count
per_viewpoint_attempted_count
last_global_coverage_gain_step
steps_since_last_global_coverage_gain
no_progress_steps_after_last_gain
duplicate_selected_target_count
duplicate_selected_target_rate
noop_when_available_count
noop_when_available_rate
selected_path_cost_mean
selected_path_cost_max
selected_path_cost_sum
load_balance_selected_std
load_balance_completed_std
late_repeated_assignment_pattern
```

Definitions:

- `per_robot_selected_count`: non-noop selected assignments per robot.
- `per_robot_completed_count`: fractional credit for newly covered viewpoints selected by one or more robots. If
  several robots simultaneously select and complete the same newly covered viewpoint, that one viewpoint is split
  across those robots.
- `per_robot_repeated_assignment_count`: consecutive non-noop same-viewpoint selections by the same robot.
- `per_viewpoint_attempted_count`: number of non-noop selections per viewpoint id, aligned with `viewpoint_ids`.
- `steps_since_last_global_coverage_gain`: final episode step distance since the last global coverage increase.
- `no_progress_steps_after_last_gain`: same final plateau length as `steps_since_last_global_coverage_gain`.
- `duplicate_selected_target_count`: per-step sum of `max(0, selected_robot_count(viewpoint) - 1)`.
- `duplicate_selected_target_rate`: duplicate count divided by non-noop selections.
- `noop_when_available_count`: noop selections when the robot had at least one decision-time available viewpoint.
- `noop_when_available_rate`: noop-when-available count divided by noop selections.
- `selected_path_cost_*`: selected entries from the decision-time evaluator `cost_matrix`.
- `late_repeated_assignment_pattern`: repeated robot-viewpoint pairs accumulated after the last global coverage gain.

## Output Fields Added

`per_episode.csv` columns:

```text
per_robot_selected_count
per_robot_completed_count
per_robot_repeated_assignment_count
per_viewpoint_attempted_count
last_global_coverage_gain_step
steps_since_last_global_coverage_gain
no_progress_steps_after_last_gain
duplicate_selected_target_count
duplicate_selected_target_rate
noop_when_available_count
noop_when_available_rate
selected_path_cost_mean
selected_path_cost_max
selected_path_cost_sum
load_balance_selected_std
load_balance_completed_std
late_repeated_assignment_pattern
```

`summary.csv` columns:

```text
per_robot_selected_count_mean
per_robot_completed_count_mean
per_robot_repeated_assignment_count_mean
per_viewpoint_attempted_count_sum
mean_steps_since_last_global_coverage_gain
mean_no_progress_steps_after_last_gain
duplicate_selected_target_count_total
duplicate_selected_target_rate_mean
noop_when_available_count_total
noop_when_available_rate_mean
selected_path_cost_mean
selected_path_cost_max
selected_path_cost_sum_total
load_balance_selected_std_mean
load_balance_completed_std_mean
late_repeated_assignment_pattern_summary
```

`assignment_history.csv` columns:

```text
available_viewpoint_count
noop_when_available
is_repeated_assignment
selected_path_cost
duplicate_selected_target_count_step
```

`diagnostics.json` key:

```text
rl_dynamic_assignment_reporting_counters
```

The existing `episode_metric_diagnostics` entries also include the new per-episode counter values.

## Smoke Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 20 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase9b1_reporting_counters_smoke_n50_e1_s20 --write_assignment_history
```

Output directory:

```text
results/assignment_evaluation/phase9b1_reporting_counters_smoke_n50_e1_s20/
```

Files written:

```text
per_episode.csv
summary.csv
assignment_history.csv
diagnostics.json
```

This is a short reporting smoke only. It is not RL training and not formal RL evaluation.

## Smoke Result

The smoke completed successfully.

Key output values:

```text
method = nearest
episodes = 1
episode_length = 20
final_coverage = 0.060
per_robot_selected_count = [20, 20, 20]
per_robot_completed_count = [1.0, 2.0, 0.0]
per_robot_repeated_assignment_count = [19, 17, 19]
duplicate_selected_target_count = 0
noop_when_available_count = 0
selected_path_cost_mean = 1.0053210258483887
selected_path_cost_max = 1.7843612432479858
selected_path_cost_sum = 60.31926345825195
load_balance_selected_std = 0.0
load_balance_completed_std = 0.8164966106414795
late_repeated_assignment_pattern = []
```

The short 20-step smoke still had a coverage gain at the final step, so the post-last-gain
`late_repeated_assignment_pattern` is empty. Longer baseline runs are expected to expose the Phase 8 late plateau
pattern.

## Verification

Compilation:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
```

Result:

```text
passed
```

Spot checks over the smoke outputs:

```text
per_episode missing required new fields: none
assignment_history missing required new fields: none
summary missing required new fields: none
diagnostics key present: true
non_noop_history_count = 60
per_robot_selected_count sum = 60
per_viewpoint_attempted_count sum = 60
duplicate_selected_target_count = 0
load_balance_selected_std = 0.0
load_balance_completed_std = 0.816496610641479
selected_sum_matches_history = true
attempted_sum_matches_history = true
duplicate_nonnegative = true
load_std_finite = true
```

Final checks:

```text
git diff --check
git status --short
```

Results:

```text
git diff --check: passed
git status --short:
  M scripts/environments/evaluate_assignment_methods.py
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
```

`git diff --check` emitted Windows LF-to-CRLF warnings only; no whitespace errors were reported.

## Unavailable Counters

No required Phase 9B-1 counter is unavailable in the current evaluator path.

Notes:

- `noop_when_available_count` is computed from the decision-time `available_mask` in the evaluator problem. If future
  runs use evaluator-side filters, this reflects the effective solver input after those filters.
- `selected_path_cost_*` uses the decision-time evaluator `cost_matrix`.
- `per_robot_completed_count` is fractional to keep simultaneous duplicate completion credit from inflating total team
  completion.

## Explicit Non-Changes

Phase 9B-1 did not change:

```text
reward behavior
observation behavior
available_mask
feasible_mask
static_geometric_feasible_mask
solver behavior
controller logic
HARL internals
installed site-packages
environment dynamics
robot motion
collision / IK / raycast / local avoidance / path planning
retry / fallback / cooldown behavior
RL training
formal RL evaluation
handcrafted baseline rules
```

## Recommended Next Step

Use Phase 9B-1 counters in a short non-RL baseline diagnostic rerun only when explicitly scoped. Do not proceed to
Phase 9B-2 observation changes, Phase 9B-3 reward changes, RL training, or formal RL evaluation without a separate
task boundary.
