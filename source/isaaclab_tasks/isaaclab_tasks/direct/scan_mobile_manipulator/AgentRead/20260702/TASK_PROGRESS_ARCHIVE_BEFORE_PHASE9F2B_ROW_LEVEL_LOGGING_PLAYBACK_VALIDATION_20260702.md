# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-2A is complete.

This phase implemented a logging-only extension for future playback `assignment_history.csv` files so row-level conflict attribution can distinguish exact duplicate target selection, nearby selected-target conflict, inter-robot base overlap, and observed inter-robot path segment crossing / near-miss proxy.

No training was run.
No playback was run.
No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger/mask logic, scenario YAML behavior, conflict-aware redirect, active-task lifecycle, or installed `site-packages` were changed.

No commit was made.

## Latest Completed Phase

Phase 9F-2A: row-level conflict logging data-sufficiency extension.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```

## Key Results

Future playback histories now include these added diagnostic-only fields:

```text
robot_base_post_x
robot_base_post_y
selected_target_conflict_pair_count
selected_target_conflict_pairs
selected_target_min_distance_to_other_selected
selected_target_conflict_threshold
same_step_claimed_target_count
same_step_claimed_target_robot_ids
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
inter_robot_overlap_pair_count
inter_robot_overlap_pairs
inter_robot_min_base_distance
inter_robot_overlap_threshold
inter_robot_path_crossing_pair_count
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pair_count
inter_robot_path_near_miss_pairs
inter_robot_path_near_miss_threshold
```

Existing `robot_base_x` and `robot_base_y` semantics are unchanged: they remain pre-step base positions.

List-like fields are written through the existing CSV writer as JSON strings.

Path crossing / near-miss is an observed straight segment proxy from pre-step base position to post-step base position. It is not a planner-internal path and does not change controller behavior.

## Active Architecture / Implementation Path

Phase 9F remains diagnostic-first.

Budget-aware cooldown remains config-gated and assignment-wrapper-local:

```text
AssignmentHarlWrapper-local per-robot-target cooldown
trigger_mode = budget_and_streak for the Phase 9E debug scenario
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
```

Phase 9F-2A did not implement conflict-aware redirect or active-task lifecycle.

## Key Files

Changed Python files:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
```

Added report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```

Archived previous task progress:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_20260702.md
```

Updated current handoff:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Phase 9F-1 generated outputs were refreshed by the CSV-only analyzer after the schema inventory was updated:

```text
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/assignment_history_schema_inventory.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_summary.json
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_notes.md
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/conflict_cause_attribution_summary.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_conflict_windows.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_next_target_summary.csv
```

## Latest Verification

Lightweight checks run:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed
classification on old histories: DIAG-P
```

Final validation:

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

## Known Issues / Blockers

No execution blocker.

Known limitations:

```text
new row-level fields will appear only in future playback histories
no new playback was run in Phase 9F-2A
old Phase 9E-4B / Phase 9F-1 histories remain partial
observed path crossing / near-miss is a straight pre/post base segment proxy, not true planned path
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training.
Do not run playback unless a required file is missing and the need is explicitly reported first.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger/mask logic, scenario YAML behavior, conflict-aware redirect, or active-task lifecycle logic without a new explicit phase request.

## Next Step

Recommended next phase:

```text
Phase 9F-2B: schema-only or playback-only validation of the new row-level fields when the user explicitly allows playback.
```

After future histories exist, rerun post-budget conflict attribution using the direct row-level fields before implementing any conflict-aware redirect or active-task lifecycle mechanism.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F1_CONFLICT_DIAGNOSTICS_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
```
