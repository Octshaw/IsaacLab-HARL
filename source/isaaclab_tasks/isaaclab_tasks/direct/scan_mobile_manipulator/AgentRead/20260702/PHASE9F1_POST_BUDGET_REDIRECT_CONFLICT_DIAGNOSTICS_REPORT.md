# Phase 9F-1 Post-Budget-Redirect Conflict Diagnostics Report

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-1 is diagnostic-only.

No training was run. No playback was run. No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, HARL code, baseline solvers, cooldown logic, scenario YAML behavior, conflict-aware redirect logic, or active-task lifecycle logic were changed.

No commit was made.

## 2. Inputs Inspected

Primary documents:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
```

Primary playback outputs:

```text
results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.csv
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.json
```

Optional comparison outputs were present and included in schema inventory:

```text
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback/
```

Diagnostic script added:

```text
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
```

Generated output directory:

```text
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/
```

## 3. Schema / Field Inventory

Both Phase 9E-4B primary `assignment_history.csv` files exist and each has:

```text
rows = 4485
columns = 42
episodes = 5
num_envs = 1
num_agents = 3
```

Schema sufficiency:

```text
DIAG-PARTIAL
```

The current traces are sufficient for budget-trigger rows, triggered robot-target pairs, next selected target, exact duplicate target claims, selected-target distance conflict reconstruction, coverage gain, and return-to-triggered-pair checks.

They are not sufficient for true row-level inter-robot overlap attribution, because `inter_robot_overlap_pair_count` / pair samples are not stored in `assignment_history.csv`. Base-motion crossing is only a component/obstacle intersection proxy, not true inter-robot path crossing.

| Question | Result | Notes |
| --- | --- | --- |
| selected target per robot per step | sufficient | `episode`, `env_id`, `step`, `robot_id`, `selected_viewpoint_id`, `is_noop` are present. |
| budget trigger step | sufficient | `budget_triggered_by_budget` and `step` are present. |
| triggered robot-target pair | sufficient | trigger row has `robot_id` and `selected_viewpoint_id`. |
| next selected target after trigger | sufficient | inferred from later rows for the same robot. |
| whether next target is already selected by another robot | sufficient | inferred from same-step teammate rows. |
| target/viewpoint positions | partial | selected target `target_x,target_y` are present; full unselected viewpoint table is not in history. |
| robot base positions | partial | `robot_base_x,robot_base_y` are pre-step playback positions. |
| duplicate selected target proxy | sufficient | `duplicate_selected_target_on_step` is present. |
| base motion crossing proxy | partial | `actual_base_motion_intersects_component` is present but is component-crossing, not inter-robot path crossing. |
| coverage gain after redirect | sufficient | `new_coverage_gain_after_step`, `coverage_ratio_after_step`, `newly_covered_viewpoint_ids` are present. |
| return to triggered pair after cooldown | sufficient | inferred from later rows after the 5-step cooldown duration. |
| row-level selected-target conflict | partial | not stored directly, but reconstructable from selected target coordinates with threshold 0.85 m. |
| row-level inter-robot overlap | insufficient | only aggregate `summary.csv` overlap is available. |

Extra logging needed for a fully sufficient future pass:

```text
row-level selected_target_conflict_pair_count and conflicting robot-target pairs
row-level inter_robot_overlap_pair_count, pair ids, min distance, and threshold
true inter-robot path segment crossing / near-miss diagnostics
post-step robot base positions in assignment_history.csv
optional next-step action-mask / claimed-target snapshot for redirect-specific ownership analysis
```

## 4. Generated Outputs

```text
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/assignment_history_schema_inventory.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_conflict_windows.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_next_target_summary.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/conflict_cause_attribution_summary.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_summary.json
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_notes.md
```

## 5. Post-Trigger Attribution Summary

Selected-target conflict was reconstructed from stored selected target coordinates using the Phase 9E budget scenario threshold:

```text
target_conflict_radius = 0.35
target_conflict_safety_margin = 0.15
selected-target conflict threshold = 0.85 m
```

The reconstructed selected-target conflict rates exactly match the playback summaries:

```text
models: 1.090301 reconstructed vs 1.090301 summary
best_model: 0.264214 reconstructed vs 0.264214 summary
```

| Run | Budget triggers | Trigger pairs | Next targets | Exact next claim | Nearby next conflict | Coverage gain within 20 | Return after cooldown | Cause labels |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| models + budget | 30 | r1->36:20; r2->44:10 | 44:20; 24:10 | 20/30 | 25/30 | 0/30 | 30/30 | A+B+C+D |
| best_model + budget | 70 | r2->11:45; r1->36:20; r0->15:5 | 24:45; 27:20; 25:5 | 0/70 | 50/70 | 25/70 | 65/70 | B |

## 6. Conflict Concentration

| Run | selected-target conflict overall | within 20 post-trigger | outside trigger windows | exact duplicate within/outside | nearby distinct within/outside | component crossing within/outside |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| models + budget | 1.090301 | 1.983051 | 0.870833 | 0.288136 / 0.033333 | 1.694915 / 0.837500 | 0.333333 / 0.236111 |
| best_model + budget | 0.264214 | 0.426752 | 0.084507 | 0.000000 / 0.084507 | 0.426752 / 0.000000 | 0.080679 / 0.110329 |

Interpretation:

```text
models:
  Post-trigger windows are much worse than outside windows.
  Exact duplicate next-target claims are frequent.
  Nearby distinct-target conflict is also high.
  Conflict is not exclusively post-trigger, because outside-window selected-target conflict remains high.
  No post-trigger coverage gain was observed within 20 steps.
  Every trigger returned to the triggered pair after cooldown expiry.

best_model:
  Exact duplicate redirect conflict is not observed.
  Nearby distinct-target conflict is the dominant post-trigger issue.
  Outside-window nearby conflict is low, so this looks more redirect-window-specific.
  25/70 triggers are followed by global coverage gain within 20 steps, but the next redirected target itself was not covered within 20 steps.
  65/70 triggers returned to the triggered pair after cooldown expiry.
```

## 7. Cause Classification

Cause labels:

```text
A = exact duplicate redirect conflict
B = nearby-target spatial conflict
C = path/base-motion crossing proxy conflict
D = persistent policy preference not primarily caused only by budget redirect
E = insufficient trace fields
```

Observed categories:

```text
models + budget: A+B+C+D
best_model + budget: B
global trace limitation: E applies to row-level overlap / true path-crossing attribution only
```

Detailed classification:

```text
1. Exact duplicate target selection:
   models yes: 20/30 next redirected selections were already selected by another robot.
   best_model no: 0/70.

2. Nearby target selection:
   models yes: 25/30 next redirected selections were near a teammate's distinct target.
   best_model yes: 50/70.

3. Path crossing:
   partial/proxy only.
   models has elevated component-crossing proxy within trigger windows: 0.333333 vs 0.236111 outside.
   best_model does not show elevated post-trigger crossing proxy: 0.080679 within vs 0.110329 outside.

4. Persistent policy preference unrelated to budget redirect:
   models partially yes: outside-window selected-target conflict is still high at 0.870833.
   best_model weaker/no: outside-window selected-target conflict is 0.084507 and nearby distinct conflict is 0.0.

5. Insufficient trace fields:
   yes for row-level inter-robot overlap and true inter-robot path crossing.
   no for exact duplicate and nearby selected-target attribution.
```

## 8. Mechanism Recommendation Table

| Diagnosis | Possible next mechanism |
| --- | --- |
| exact duplicate conflict | target reservation / claimed-target mask |
| nearby target conflict | target proximity exclusion or spacing-aware redirect |
| path crossing conflict | path-crossing-aware redirect diagnostics |
| persistent policy preference | policy/reward/lifecycle issue, do not solve with another local mask only |
| repeated return to triggered pair | active-task lifecycle or explicit failed-target state |
| insufficient fields | add diagnostics before mechanism changes |

Immediate recommendation:

```text
Do not implement active-task lifecycle or conflict-aware redirect yet in this phase.
If Phase 9F-2 proceeds with a local guardrail, it should target claimed-target and spacing-aware redirect behavior first.
However, because models/ also has high outside-window conflict and 30/30 returns to triggered pairs, another local mask alone is unlikely to solve the whole lifecycle problem.
Before claiming overlap/path causality, add row-level overlap and true path-crossing diagnostics.
```

## 9. Final Classification

```text
DIAG-P
```

Reason:

```text
The fields are sufficient for useful attribution of exact duplicate redirects, nearby target conflicts, post-trigger coverage gain, and return-to-triggered-pair behavior.
The fields are not sufficient for full row-level inter-robot overlap or true inter-robot path-crossing attribution.
The result is therefore partial but actionable.
```

## 10. Validation

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed

git diff --check
result: passed
note: emitted LF/CRLF warning for TASK_PROGRESS.md only

git status --short
result:
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? scripts/environments/analyze_phase9f1_post_budget_conflicts.py
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/
```
