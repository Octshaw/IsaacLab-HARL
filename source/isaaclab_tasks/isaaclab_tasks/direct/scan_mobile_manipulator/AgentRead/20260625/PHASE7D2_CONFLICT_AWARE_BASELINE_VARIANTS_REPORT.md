# Phase 7D-2 Conflict-Aware Baseline Variants Report

Date: 2026-06-25

## Why Phase 7D-2 Was Added

Phase 7D-1 showed that selected-target conflict is a real proxy-level task-allocation issue in longer runs. The
diagnostic sequential candidate reduced conflicts only slightly and did not resolve the final late-stage clustered
targets or improve worst clearance.

Phase 7D-2 adds explicit gated baseline variants for ablation:

```text
greedy_conflict_aware
nearest_conflict_aware
```

The original `random`, `nearest`, and `greedy` methods remain unchanged.

## Phase 7D-1 Evidence Summary

The 300-step greedy/nearest Phase 7D-1 diagnostic candidate produced:

```text
baseline_selected_target_conflict_step_count = 215
candidate_selected_target_conflict_step_count = 198
baseline_selected_target_conflict_pair_count_total = 579
candidate_selected_target_conflict_pair_count_total = 562
baseline_selected_target_conflict_penalty_sum_total = 57900.0
candidate_selected_target_conflict_penalty_sum_total = 56200.0
candidate_changed_assignment_count_total = 17
baseline/candidate worst selected-target clearance = -0.775663435459137
```

It helped, but did not solve the final clustered selected-target plateau.

## What Was Implemented

- Added `ConflictAwareAssignmentSolver`.
- Added solver factory names:

```text
greedy_conflict_aware
nearest_conflict_aware
```

- Added a top-K joint selected-target conflict-aware search.
- Added scenario config parsing/validation for `conflict_aware_baseline`.
- Added per-step JSON diagnostics and per-episode/summary CSV fields for the new solver variants.
- Preserved Phase 7C inter-robot metrics and Phase 7D-1 diagnostic candidate metrics.

## Method Semantics

`greedy_conflict_aware` uses the existing greedy baseline as its fallback/base comparison and the same distance-based
unary ordering as the current greedy solver.

`nearest_conflict_aware` uses the existing nearest baseline as its fallback/base comparison and the same distance-based
unary ordering as nearest.

In this environment, current `nearest` and `greedy` both rank unary candidates by `cost_matrix` distance. `greedy` uses
inverse distance as a score, which gives the same ordering.

## Top-K Search Design

For each env-step:

```text
1. Build each robot's top-K available non-noop viewpoint list from the base unary distance cost.
2. Enumerate joint combinations across robots.
3. Score each combination:
   sum unary costs
   + target_conflict_penalty * selected-target conflict pair count
   + duplicate_penalty * duplicate target pair count
4. Execute only the best scored joint assignment for the explicitly requested conflict-aware method.
5. Fall back to the original base method if no valid combination exists.
```

No masks, rewards, controller logic, environment dynamics, or original baseline solver behavior were changed.

## Configuration Fields Added

Added to `algorithm_proxy_component_mesh.yaml`:

```yaml
conflict_aware_baseline:
  enabled: true
  methods:
    - greedy_conflict_aware
    - nearest_conflict_aware
  mode: gated_solver_variant
  top_k: 10
  target_conflict_radius: 0.35
  target_conflict_safety_margin: 0.15
  target_conflict_penalty: 100.0
  duplicate_penalty: 1000000.0
  fallback_to_base_method: true
  max_pairs_sample: 20
```

Default selected-target conflict threshold:

```text
0.35 + 0.35 + 0.15 = 0.85 m
```

## Files Changed

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7D2_HANDOFF_20260625.md
```

The working tree also still contains prior Phase 7B/7C/7D-1 modified/untracked report files.

## Commands Run

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
```

Headless runs:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy nearest greedy_conflict_aware nearest_conflict_aware --num_envs 1 --num_episodes 1 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7d2_conflict_aware_baseline_smoke_e1_s50 --write_assignment_history --compare_obstacle_aware_candidates

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy nearest greedy_conflict_aware nearest_conflict_aware --num_envs 1 --num_episodes 1 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7d2_conflict_aware_baseline_e1_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

Inspection commands read:

```text
diagnostics.json
summary.csv
per_episode.csv
assignment_history.csv
```

Output directories:

```text
results/assignment_evaluation/phase7d2_conflict_aware_baseline_smoke_e1_s50/
results/assignment_evaluation/phase7d2_conflict_aware_baseline_e1_s300/
```

The result directories were not committed.

## 50-Step Smoke Results

All four methods completed.

```text
final_coverage = 0.60 for all methods
selected_target_conflict_pair_count_total = 0 for all methods
inter_robot_overlap_pair_count_total = 0 for all methods
conflict_aware_changed_vs_base_count_total = 0 for conflict-aware methods
fallback_step_count_total = 0 for conflict-aware methods
```

## 300-Step Comparison

| metric | greedy | greedy_conflict_aware | nearest | nearest_conflict_aware |
|---|---:|---:|---:|---:|
| final_coverage | 0.90 | 0.90 | 0.90 | 0.90 |
| final_covered_count | 45 / 50 | 45 / 50 | 45 / 50 | 45 / 50 |
| coverage_auc | 0.7467540502548218 | 0.7467540502548218 | 0.7467540502548218 | 0.7467540502548218 |
| episode_length | 299 | 299 | 299 | 299 |
| success | 0 | 0 | 0 | 0 |
| valid_action_rate | 1.0 | 1.0 | 1.0 | 1.0 |
| noop_rate | 0.0 | 0.0 | 0.0 | 0.0 |
| selected_target_conflict_rate_mean | 0.7190635451505016 | 0.6622073578595318 | 0.7190635451505016 | 0.6622073578595318 |
| selected_target_conflict_pair_count_total | 579 | 562 | 579 | 562 |
| selected_target_min_clearance_min | -0.775663435459137 | -0.775663435459137 | -0.775663435459137 | -0.775663435459137 |
| inter_robot_overlap_rate_mean | 0.6688963210702341 | 0.5752508361204013 | 0.6688963210702341 | 0.5752508361204013 |
| inter_robot_overlap_pair_count_total | 521 | 500 | 521 | 500 |
| inter_robot_min_clearance_min | -0.775663435459137 | -0.775663435459137 | -0.775663435459137 | -0.775663435459137 |
| conflict_aware_changed_vs_base_count_total | 0 | 10 | 0 | 10 |
| conflict_aware_changed_vs_base_rate_mean | 0.0 | 0.011148271150887012 | 0.0 | 0.011148271150887012 |
| conflict_aware_fallback_step_count_total | 0 | 0 | 0 | 0 |

Conflict-aware solver diagnostics:

```text
top_k = 10
mean candidate combination count = 442.95986622073576
selected target conflict penalty sum = 56200.0
selected duplicate pair count = 0
fallback rate = 0.0
changed_vs_base_count = 10 / 897 robot-decisions
```

Changed-pair sample:

```text
robot_1 base viewpoint 48 -> conflict-aware viewpoint 7
```

Final 15-step repeated assignments remained unchanged for all four methods:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

## Interpretation

The top-K conflict-aware variants reduced selected-target conflicts and inter-robot overlap counts:

```text
selected_target_conflict_pair_count_total: 579 -> 562
selected_target_conflict_rate_mean: 0.7190635451505016 -> 0.6622073578595318
inter_robot_overlap_pair_count_total: 521 -> 500
inter_robot_overlap_rate_mean: 0.6688963210702341 -> 0.5752508361204013
```

They did not improve:

```text
final_coverage
coverage_auc
worst selected-target clearance
worst inter-robot clearance
final clustered repeated-target pattern
```

This supports keeping `greedy_conflict_aware` and `nearest_conflict_aware` as baseline ablations. It does not show that
selected-target conflict mitigation alone solves late-stage no-progress completion.

## Original Baselines

Original `greedy` and `nearest` behavior was not changed. They still use their existing solver classes and were run in
the same 300-step comparison as controls.

No changes were made to:

```text
random behavior
nearest behavior
greedy behavior
available_mask
feasible_mask
static_geometric_feasible_mask
base cost_matrix generation
reward
controller
assignment_controller.py
HARL
training
environment dynamics
robot movement behavior
```

No physical collision, local avoidance, ORCA, IK, joint limits, motion planning, retry fallback, or cooldown behavior
was added.

## Known Limitations

- The top-K search is a small heuristic ablation, not a globally complete planner.
- It mitigates selected-target proximity but does not simulate physical collision avoidance.
- It does not plan robot paths.
- It does not resolve the final clustered target plateau in this 300-step run.
- It does not improve final coverage in the tested N=50 proxy scenario.
- Phase 7D-1 diagnostic candidate remains available and can produce candidate metrics for original `nearest`/`greedy`;
  for conflict-aware methods it is baseline-only and reports `method_not_in_compare_methods`.

## Phase 8 Readiness

Phase 7D-2 supports keeping conflict-aware baselines as ablations in future comparison tables. The evidence does not
justify adding more hard-coded avoidance, cooldown, or retry behavior before Phase 8.

Recommended next step: proceed to Phase 8 baseline validation with original baselines and optionally include
`greedy_conflict_aware` / `nearest_conflict_aware` as labeled ablations. Continue reporting inter-robot overlap and
selected-target conflict metrics.

## Final Checks

`git diff --check`:

```text
passed
```

Git emitted LF-to-CRLF working-copy warnings on Windows; no whitespace errors were reported.

`git status --short` summary before final report/handoff write:

```text
 M scripts/environments/evaluate_assignment_methods.py
 M scripts/environments/test_assignment_harl_wrapper_smoke.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
```

Final `git diff --check` and `git status --short` were rerun after report/handoff updates; see final Codex response for
the exact final command output.
