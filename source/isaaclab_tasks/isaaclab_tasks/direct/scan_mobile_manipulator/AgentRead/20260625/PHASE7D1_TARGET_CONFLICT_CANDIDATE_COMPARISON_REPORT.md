# Phase 7D-1 Selected-Target Conflict Candidate Comparison Report

Date: 2026-06-25

## Why Phase 7D-1 Was Added

Phase 7C showed that inter-robot and selected-target conflicts are useful proxy-level diagnostics. A longer manual
300-step greedy GUI validation then exposed visible robot overlap and late-stage clustered selected targets.

Phase 7D-1 tests, without changing live behavior, whether a selected-target conflict-aware candidate assignment would
select less clustered target viewpoints.

This is evidence collection only. It does not implement a new solver method and does not execute the candidate
assignment.

## 300-Step Issue Summary

The user-reported 300-step greedy GUI run reached approximately 44/50 coverage and showed late repeated selected
targets around robot_0 -> 20, robot_1 -> 4, and robot_2 -> 36.

The local 300-step greedy headless diagnostic reproduced the general late-stage selected-target conflict pattern, but
the exact repeated robot_1 target differed in this run:

```text
final_coverage = 0.90
final_covered_count = 45 / 50
final repeated actual baseline assignments in assignment_history.csv:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
robot_0 -> 20 count = 182
robot_2 -> 36 count = 248
robot_1 -> 4 count = 0
robot_1 -> 48 count = 215
```

The selected-target conflict sample showed viewpoint 48 and viewpoint 36 only 0.104315 m apart under the 0.85 m
diagnostic threshold.

## What Was Implemented

Added diagnostic-only selected-target conflict-aware candidate comparison for baseline `nearest` and `greedy`.

For each baseline solver step:

```text
1. Keep the baseline solver assignment as the actual assignment.
2. Compute selected-target conflict metrics for the baseline assignment.
3. Build a candidate assignment in sequential robot index order.
4. For each robot, score available viewpoints by baseline cost plus a penalty for conflicts with already selected
   candidate targets.
5. Avoid duplicate viewpoints when a nonduplicate available option exists.
6. Store candidate metrics and compact samples in diagnostics only.
7. Send only the original baseline assignment to env.step(...).
```

The candidate is never executed, never replaces `assignment`, and never changes the action sent to the environment.

## Configuration Fields Added

Added to `algorithm_proxy_component_mesh.yaml`:

```yaml
selected_target_conflict_candidate_comparison:
  enabled: true
  mode: diagnostic_only
  candidate_generator: sequential_robot_order
  robot_order: robot_index
  target_conflict_radius: 0.35
  target_conflict_safety_margin: 0.15
  selected_target_conflict_penalty: 100.0
  compare_methods:
    - nearest
    - greedy
  include_random_as_baseline_only: true
  max_pairs_sample: 20
```

Default diagnostic threshold:

```text
2 * target_conflict_radius + target_conflict_safety_margin = 0.85 m
```

## Files Changed

Phase 7D-1 touched:

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7D1_HANDOFF_20260625.md
```

The working tree also still contains prior Phase 7B/7C modifications to `scan_mobile_manipulator_env.py` and
`test_assignment_harl_wrapper_smoke.py`.

## Commands Run

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Headless smoke and diagnostics:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy nearest --num_envs 1 --num_episodes 1 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7d1_target_conflict_candidate_smoke_e1_s50 --write_assignment_history --compare_obstacle_aware_candidates

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7d1_target_conflict_candidate_greedy_e1_s300 --write_assignment_history --compare_obstacle_aware_candidates

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7d1_target_conflict_candidate_nearest_e1_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

Inspection commands read:

```text
diagnostics.json
summary.csv
per_episode.csv
assignment_history.csv
```

## Output Directories

```text
results/assignment_evaluation/phase7d1_target_conflict_candidate_smoke_e1_s50/
results/assignment_evaluation/phase7d1_target_conflict_candidate_greedy_e1_s300/
results/assignment_evaluation/phase7d1_target_conflict_candidate_nearest_e1_s300/
```

These result directories were not committed.

## Methods Compared

Configured comparison methods:

```text
nearest
greedy
```

Configured baseline-only method:

```text
random
```

The validation runs compared `nearest` and `greedy`. `random` was not run in this task.

## Key Metrics

Short 50-step smoke:

```text
greedy final_coverage = 0.60
nearest final_coverage = 0.60
baseline_selected_target_conflict_pair_count_total = 0
candidate_selected_target_conflict_pair_count_total = 0
candidate_changed_assignment_count_total = 0
```

300-step greedy:

```text
steps = 299
final_coverage = 0.90
baseline_selected_target_conflict_step_count = 215
candidate_selected_target_conflict_step_count = 198
baseline_selected_target_conflict_pair_count_total = 579
candidate_selected_target_conflict_pair_count_total = 562
baseline_selected_target_conflict_rate = 0.6454849498327759
candidate_selected_target_conflict_rate = 0.6265328874024526
baseline_selected_target_conflict_penalty_sum_total = 57900.0
candidate_selected_target_conflict_penalty_sum_total = 56200.0
baseline_selected_target_min_clearance_min = -0.775663435459137
candidate_selected_target_min_clearance_min = -0.775663435459137
candidate_changed_assignment_count_total = 17
candidate_changed_assignment_rate_mean = 0.018952064216136932
```

300-step nearest:

```text
steps = 299
final_coverage = 0.90
baseline_selected_target_conflict_step_count = 215
candidate_selected_target_conflict_step_count = 198
baseline_selected_target_conflict_pair_count_total = 579
candidate_selected_target_conflict_pair_count_total = 562
baseline_selected_target_conflict_rate = 0.6454849498327759
candidate_selected_target_conflict_rate = 0.6265328874024526
baseline_selected_target_conflict_penalty_sum_total = 57900.0
candidate_selected_target_conflict_penalty_sum_total = 56200.0
baseline_selected_target_min_clearance_min = -0.775663435459137
candidate_selected_target_min_clearance_min = -0.775663435459137
candidate_changed_assignment_count_total = 17
candidate_changed_assignment_rate_mean = 0.018952064216136932
```

Changed pairs sample:

```text
steps 84-100:
  robot_2 baseline viewpoint 36 -> candidate viewpoint 7
  baseline_cost = 0.0
  candidate_cost = 2.938192129135132
```

Per-step diagnostics confirmed:

```text
steps 84-100: baseline conflict pair count 1 -> candidate conflict pair count 0
final steps 289-298: baseline conflict pair count 3 -> candidate conflict pair count 3
```

## Interpretation

The candidate comparison reduced selected-target conflicts slightly:

```text
conflict steps: 215 -> 198
conflict pairs: 579 -> 562
penalty sum: 57900 -> 56200
```

The candidate did change assignments, but only for 17 robot-step decisions. The changes were concentrated around
steps 84-100 and mainly moved robot_2 from viewpoint 36 to viewpoint 7.

The candidate did not improve the worst min clearance and did not resolve the final late-stage clustered targets.
Therefore, Phase 7D-1 supports considering a later Phase 7D-2 gated baseline variant, but it does not prove that the
heuristic solves the proxy conflict issue.

## Live Solver Behavior

No live solver behavior changed.

The patch does not change:

```text
solver behavior
assignment semantics
available_mask
feasible_mask
static_geometric_feasible_mask
cost_matrix
reward
controller
assignment_controller.py
HARL
training
environment dynamics
robot movement behavior
```

The diagnostic payload records:

```text
solver_behavior_changed = false
actual_assignment_changed = false
candidate_assignment_executed = false
live_solver_inputs_changed = false
```

## Known Limitations

- The candidate assignment is a sequential heuristic, not an optimizer over the full pairwise assignment objective.
- The candidate is not executed, so this phase does not answer whether coverage or robot motion would improve.
- It does not add physical collision, local avoidance, ORCA, path planning, IK, hard blocking, retry fallback, or
  cooldown behavior.
- In this local 300-step run, robot_1 repeatedly selected viewpoint 48, not viewpoint 4 as in the user-provided GUI
  observation. The overall clustered selected-target issue still reproduced.
- The candidate reduced early/mid-run conflicts but did not resolve the final worst clustered-target phase.
- GUI visualization for candidate assignments was not implemented; metrics and compact samples were implemented.

## Final Verification

Final `git diff --check` result:

```text
passed

Notes:
- Git printed LF-to-CRLF working-copy warnings for existing tracked text files on Windows.
- No whitespace errors were reported.
```

Final `git status --short` summary:

```text
 M scripts/environments/evaluate_assignment_methods.py
 M scripts/environments/test_assignment_harl_wrapper_smoke.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/
```
