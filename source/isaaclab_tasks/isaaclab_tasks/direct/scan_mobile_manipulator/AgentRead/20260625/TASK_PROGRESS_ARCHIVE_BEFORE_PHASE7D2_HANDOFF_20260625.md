# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7D-1 is implemented and headless-smoke validated. It adds a diagnostic-only selected-target
conflict-aware candidate comparison for `nearest` and `greedy`.

The live solver output remains unchanged. Candidate assignments are computed after `solver.solve(...)` and are only
stored in diagnostics; they are not sent to `env.step(...)`.

Active visual/debug scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Key diagnostic settings:

```text
obstacle_debug_visualization.line_source: selected_assignments
inter_robot_conflict_diagnostics.enabled: true
inter_robot_conflict_diagnostics.mode: diagnostics_only
selected_target_conflict_candidate_comparison.enabled: true
selected_target_conflict_candidate_comparison.mode: diagnostic_only
selected_target_conflict_candidate_comparison.candidate_generator: sequential_robot_order
selected_target_conflict_candidate_comparison.selected_target_conflict_penalty: 100.0
```

## Latest Completed Work

Phase 7D-1 compares baseline selected targets against a sequential robot-index-order candidate that scores each
available viewpoint as:

```text
baseline_cost(robot_i, viewpoint_j)
+ selected_target_conflict_penalty for each already-selected candidate target within threshold
```

The default conflict threshold is:

```text
2 * target_conflict_radius + target_conflict_safety_margin = 0.85 m
```

New compact metrics are written to `diagnostics.json`, `summary.csv`, and `per_episode.csv`, including:

```text
baseline_selected_target_conflict_step_count
baseline_selected_target_conflict_pair_count_total
baseline_selected_target_conflict_penalty_sum_total
candidate_selected_target_conflict_step_count
candidate_selected_target_conflict_pair_count_total
candidate_selected_target_conflict_penalty_sum_total
candidate_changed_assignment_rate_mean
candidate_changed_assignment_count_total
```

`assignment_history.csv` still records the actual executed baseline solver assignment only.

## Phase 7D-1 Validation

Syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Headless runs passed:

```text
results/assignment_evaluation/phase7d1_target_conflict_candidate_smoke_e1_s50/
results/assignment_evaluation/phase7d1_target_conflict_candidate_greedy_e1_s300/
results/assignment_evaluation/phase7d1_target_conflict_candidate_nearest_e1_s300/
```

Short 50-step smoke:

```text
greedy and nearest final_coverage = 0.60
baseline_selected_target_conflict_pair_count_total = 0
candidate_selected_target_conflict_pair_count_total = 0
candidate_changed_assignment_count_total = 0
```

300-step greedy:

```text
final_coverage = 0.90
baseline_selected_target_conflict_step_count = 215
baseline_selected_target_conflict_pair_count_total = 579
baseline_selected_target_conflict_penalty_sum_total = 57900.0
baseline_selected_target_min_clearance_min = -0.775663435459137
candidate_selected_target_conflict_step_count = 198
candidate_selected_target_conflict_pair_count_total = 562
candidate_selected_target_conflict_penalty_sum_total = 56200.0
candidate_selected_target_min_clearance_min = -0.775663435459137
candidate_changed_assignment_count_total = 17
candidate_changed_assignment_rate_mean = 0.018952064216136932
```

300-step nearest produced the same metrics in this deterministic headless scenario.

Interpretation:

```text
The diagnostic candidate reduces conflict steps/pairs/penalty slightly, mostly by changing robot_2 from viewpoint 36
to viewpoint 7 at steps 84-100. It does not improve the worst selected-target clearance and does not resolve the final
late-stage clustered targets. This is evidence for considering a later Phase 7D-2 gated solver variant, but not enough
to claim conflict avoidance is solved.
```

## Preserved Phase 7B / 7C Context

Phase 7B-4A selected assignment line visualization is complete. The user manually validated a 300-step greedy GUI run:
green `SelectedAssignment_*` lines matched selected-assignment semantics and should be interpreted only as direct
robot-base-XY to selected-viewpoint-XY diagnostic segments, not planned trajectories.

Phase 7C inter-robot proxy conflict diagnostics are complete and remain diagnostic-only. They measure proxy overlap and
selected-target conflicts but do not add physical collision, hard blocking, local avoidance, ORCA, path planning, or
retry/cooldown behavior.

Obstacle diagnostics remain diagnostic-only:

```text
straight_line_cost_matrix
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
```

`mesh_footprint_aware_cost_matrix` is not promoted into live solver inputs.

## Do Not Do

- Do not start Phase 7D-2 unless explicitly requested.
- Do not implement `greedy_conflict_aware` or `nearest_conflict_aware` yet.
- Do not start Phase 8 yet.
- Do not change live solver behavior, assignment semantics, masks, `cost_matrix`, reward, controller,
  `assignment_controller.py`, HARL, training, environment dynamics, or robot movement.
- Do not add hard inter-robot blocking, hard viewpoint blocking, physical collision, IK, joint limits, motion planning,
  ORCA, local avoidance, retry fallback, or cooldown behavior.
- Do not commit `results/` unless explicitly requested.

## Next Step

Recommended next task: decide whether Phase 7D-2 is justified. The Phase 7D-1 evidence supports testing a gated solver
variant, but the candidate only partially reduces selected-target conflict and does not improve worst clearance.

Do not proceed to Phase 8 until the user decides whether to run Phase 7D-2 first.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7D1_HANDOFF_20260625.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B3_LONG_DIAGNOSTIC_COMPARISON_REPORT.md
```
