# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7D-2 is implemented and headless validated. The evaluator now supports explicit gated conflict-aware baseline
variants:

```text
greedy_conflict_aware
nearest_conflict_aware
```

The original `random`, `nearest`, and `greedy` baselines remain unchanged.

Active visual/debug scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Important active diagnostic/config blocks:

```text
obstacle_debug_visualization.line_source: selected_assignments
inter_robot_conflict_diagnostics.enabled: true
selected_target_conflict_candidate_comparison.enabled: true
conflict_aware_baseline.enabled: true
conflict_aware_baseline.mode: gated_solver_variant
conflict_aware_baseline.top_k: 10
conflict_aware_baseline.target_conflict_penalty: 100.0
```

## Latest Completed Phase

Phase 7D-2 added a top-K joint selected-target conflict-aware search for the new explicit method names only.

For each env-step and conflict-aware method:

```text
1. Build each robot's top-K available non-noop viewpoint candidates using base unary distance cost.
2. Enumerate joint combinations.
3. Score by unary cost + selected-target conflict penalty + duplicate target penalty.
4. Execute the best scored assignment only for the requested conflict-aware method.
5. Fall back to the original base method if no valid combination exists.
```

No physical collision, local avoidance, ORCA, IK, joint limits, path planning, retry fallback, cooldown behavior, or hard
environment blocking was added.

## Key Files

Changed/added in Phase 7D-2:

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7D2_HANDOFF_20260625.md
```

The working tree still includes prior Phase 7B/7C/7D-1 modified files and untracked report directories.

## Latest Verification

Syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
```

Headless runs passed:

```text
results/assignment_evaluation/phase7d2_conflict_aware_baseline_smoke_e1_s50/
results/assignment_evaluation/phase7d2_conflict_aware_baseline_e1_s300/
```

300-step key metrics:

```text
greedy / nearest:
  final_coverage = 0.90
  final_covered_count = 45 / 50
  coverage_auc = 0.7467540502548218
  selected_target_conflict_pair_count_total = 579
  selected_target_conflict_rate_mean = 0.7190635451505016
  inter_robot_overlap_pair_count_total = 521
  inter_robot_overlap_rate_mean = 0.6688963210702341

greedy_conflict_aware / nearest_conflict_aware:
  final_coverage = 0.90
  final_covered_count = 45 / 50
  coverage_auc = 0.7467540502548218
  selected_target_conflict_pair_count_total = 562
  selected_target_conflict_rate_mean = 0.6622073578595318
  inter_robot_overlap_pair_count_total = 500
  inter_robot_overlap_rate_mean = 0.5752508361204013
  conflict_aware_changed_vs_base_count_total = 10
  conflict_aware_changed_vs_base_rate_mean = 0.011148271150887012
  conflict_aware_fallback_step_count_total = 0
```

Worst selected-target/inter-robot clearance stayed unchanged:

```text
-0.775663435459137
```

Final repeated cluster stayed unchanged for all four methods:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

`git diff --check` passed before report/handoff write and will be rerun at final verification.

## Interpretation

Conflict-aware variants reduce selected-target conflict and proxy overlap counts modestly, but do not improve final
coverage, coverage AUC, worst clearance, or the final late-stage clustered repeated-target pattern.

Keep `greedy_conflict_aware` and `nearest_conflict_aware` as labeled baseline ablations. Do not claim collision
avoidance or path planning is solved.

## Do Not Do

- Do not start Phase 8 automatically.
- Do not start RL evaluation or training automatically.
- Do not change original `random`, `nearest`, or `greedy` behavior.
- Do not modify `assignment_controller.py`, HARL, rewards, masks, base `cost_matrix`, or environment dynamics.
- Do not add physical collision, IK, joint limits, motion planning, ORCA, local avoidance, retry fallback, cooldown, or
  hard blocking.
- Do not commit `results/` unless explicitly requested.

## Next Step

Recommended next task: begin Phase 8 real-component proxy baseline validation only if the user requests it. Include
original `random`, `nearest`, and `greedy`; optionally include `greedy_conflict_aware` and `nearest_conflict_aware` as
clearly labeled ablations. Continue reporting inter-robot overlap and selected-target conflict diagnostics.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7D2_HANDOFF_20260625.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/NEXT_PHASE_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_PLAN.md
```
