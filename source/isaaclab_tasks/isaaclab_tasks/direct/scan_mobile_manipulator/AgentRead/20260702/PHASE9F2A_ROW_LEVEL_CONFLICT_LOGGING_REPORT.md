# Phase 9F-2A Row-Level Conflict Logging Report

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-2A is a data-sufficiency phase.

The implementation is logging-only. It extends future playback `assignment_history.csv` rows with row-level conflict attribution fields. It does not change action selection, rewards, observations, masks, environment dynamics, controller behavior, cooldown logic, HARL, baseline solvers, scenario YAML behavior, conflict-aware redirect, or active-task lifecycle behavior.

No training was run. No playback was run. No installed `site-packages` files were modified. No commit was made.

## 2. Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
scripts/environments/analyze_budget_cooldown_traces.py
scripts/environments/summarize_phase9e4b_playback.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

## 3. Field Availability Assessment

Already available at playback history logging time:

```text
selected assignment per robot
selected target positions from pre-step assignment problem
pre-step robot base positions
post-step robot base positions
selected-target conflict count/min-distance/threshold from existing playback diagnostics
inter-robot overlap count/min-distance/sample pairs from existing env diagnostics
component/base-motion obstacle crossing proxy
coverage before/after and newly covered target ids
cooldown/budget diagnostic fields
```

Reconstructable from existing same-step rows:

```text
exact duplicate selected target
same-step claimed target robot ids
same-step nearby selected target robot ids
selected-target conflict from target_x/target_y when target positions exist
```

Values that required adding post-step robot base positions:

```text
observed inter-robot path segment crossing proxy
observed inter-robot path segment near-miss proxy
post-step inter-robot base distance attribution
```

Not safely available without deeper behavior changes:

```text
controller/planner-internal intended path
true local-avoidance interaction cause
true collision/contact attribution beyond the existing diagnostic proxies
```

## 4. Files Changed

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
```

Documentation / handoff files added or updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## 5. Fields Added to Future assignment_history.csv Rows

Existing `robot_base_x` and `robot_base_y` semantics are unchanged: they remain pre-step base positions.

New post-step base position fields:

```text
robot_base_post_x
robot_base_post_y
```

Selected-target conflict fields:

```text
selected_target_conflict_pair_count
selected_target_conflict_pairs
selected_target_min_distance_to_other_selected
selected_target_conflict_threshold
```

Same-step target ownership snapshot fields:

```text
same_step_claimed_target_count
same_step_claimed_target_robot_ids
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
```

Inter-robot base overlap fields:

```text
inter_robot_overlap_pair_count
inter_robot_overlap_pairs
inter_robot_min_base_distance
inter_robot_overlap_threshold
```

Observed inter-robot path segment proxy fields:

```text
inter_robot_path_crossing_pair_count
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pair_count
inter_robot_path_near_miss_pairs
inter_robot_path_near_miss_threshold
```

List-like fields are emitted through the existing CSV writer as JSON strings.

## 6. Field Semantics

These fields are step/env-level values repeated on each robot row for the same step:

```text
selected_target_conflict_pair_count
selected_target_conflict_pairs
selected_target_conflict_threshold
inter_robot_overlap_pair_count
inter_robot_overlap_pairs
inter_robot_overlap_threshold
inter_robot_path_crossing_pair_count
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pair_count
inter_robot_path_near_miss_pairs
inter_robot_path_near_miss_threshold
```

These fields are per-robot row values:

```text
robot_base_post_x
robot_base_post_y
selected_target_min_distance_to_other_selected
same_step_claimed_target_count
same_step_claimed_target_robot_ids
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
inter_robot_min_base_distance
```

The inter-robot path fields use observed straight segments from pre-step base position to post-step base position. They are diagnostics only. They do not represent planner-internal intended paths and do not alter the controller.

Near-miss uses the same robot-footprint threshold used by inter-robot overlap diagnostics:

```text
threshold = 2.0 * inter_robot_conflict_robot_footprint_radius + inter_robot_conflict_safety_margin
```

`inter_robot_path_near_miss_pair_count` counts non-crossing segment pairs whose segment distance is below that threshold. Crossing pairs are counted separately.

## 7. Fields Intentionally Not Added

No planner-internal path or local-avoidance fields were added, because those are not safely available from the playback history writer without changing controller/env internals or adding new behavior hooks.

No scenario-config gates were added, because the phase requested no scenario YAML behavior change. The new fields are diagnostic playback output columns only.

No policy/training-consumed fields were added. These fields are only written to playback diagnostic CSV output.

## 8. How the Fields Help Future Attribution

Exact duplicate selected target:

```text
same_step_claimed_target_count
same_step_claimed_target_robot_ids
selected_target_conflict_pairs with exact_duplicate=true
```

Nearby selected target:

```text
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
selected_target_min_distance_to_other_selected
selected_target_conflict_pairs with exact_duplicate=false
selected_target_conflict_threshold
```

Row-level inter-robot overlap:

```text
inter_robot_overlap_pair_count
inter_robot_overlap_pairs
inter_robot_min_base_distance
inter_robot_overlap_threshold
```

Inter-robot path crossing or near-miss proxy:

```text
robot_base_x / robot_base_y
robot_base_post_x / robot_base_post_y
inter_robot_path_crossing_pair_count
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pair_count
inter_robot_path_near_miss_pairs
inter_robot_path_near_miss_threshold
```

Persistent outside-window conflict:

```text
future analyzers can group these row-level fields inside and outside budget-trigger windows without reconstructing from target positions or relying only on summary.csv aggregates
```

## 9. Lightweight Analyzer Update

`scripts/environments/analyze_phase9f1_post_budget_conflicts.py` was updated so its schema inventory recognizes the new Phase 9F-2A future-history fields while remaining backward-compatible with old Phase 9E-4B / Phase 9F-1 histories.

Running the analyzer on old histories remains valid and reports the new fields as noncritical future-history fields that are absent from old CSVs.

## 10. Validation

Validation is lightweight only. No playback or training was run.

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed
classification on old histories: DIAG-P
```

```text
git diff --check
result: passed
note: emitted LF/CRLF warnings for evaluate_assignment_rl_playback_diagnostics.py and TASK_PROGRESS.md only

git status --short --untracked-files=all
result:
  M scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? scripts/environments/analyze_phase9f1_post_budget_conflicts.py
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F1_CONFLICT_DIAGNOSTICS_20260702.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_20260702.md
```

## 11. Remaining Limitations

```text
New fields will appear only in future playback histories.
Old Phase 9E-4B / Phase 9F-1 histories remain partial.
Observed path crossing / near-miss is a straight pre/post base segment proxy, not true planned path.
No new playback was run, so no new assignment_history.csv with these columns exists yet.
```

## 12. Recommended Next Phase

Recommended next phase:

```text
Phase 9F-2B: schema-only or playback-only validation of the new row-level fields when the user explicitly allows playback.
```

After future histories exist, rerun post-budget conflict attribution using the direct row-level fields before implementing any conflict-aware redirect or active-task lifecycle mechanism.
