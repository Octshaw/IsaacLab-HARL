# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-0 is complete.

This was a design audit only for active-task lifecycle / explicit failed-target-state handling. No code behavior was implemented. No commit was made.

No training or playback was run. No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, installed `site-packages`, cooldown behavior, redirect guardrail behavior, or scenario behavior were changed.

Pre-existing worktree notes observed before Phase 9G-0 doc edits:

```text
M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202607.zip
```

These were not modified by Phase 9G-0.

## Latest Completed Phase

Phase 9G-0: active-task lifecycle / explicit failed-target-state design audit.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```

## Main Finding

Current state flow:

```text
env-level task_status / robot_status exist as problem fields, but are derived snapshots only
task_status currently represents unassigned/completed from viewpoints_covered
robot_status currently represents all idle
viewpoints_covered is the persistent completion source
available_mask is derived from feasible_mask and viewpoints_covered
wrapper-level previous_assignment, assignment diagnostics, cooldown, budget, and redirect guardrail state are persistent
Phase 9F redirect guardrail is short-window target-candidate suppression, not lifecycle ownership/failure state
```

Phase 9F-5 remains correctly interpreted:

```text
exact/nearby next-redirect conflicts improved
row-level overlap did not improve
return-to-triggered-pair remained 6/6
coverage_gain_within_20 remained 0/6
final coverage and coverage AUC were unchanged
```

## Recommended Phase 9G Path

```text
Phase 9G-1:
  diagnostic-only lifecycle reconstruction from existing assignment_history.csv files.
  Prefer a standalone analyzer first.
  Do not change env/wrapper behavior.

Phase 9G-2:
  only if 9G-1 supports it, add disabled-by-default wrapper-local failed-pair/release memory.
  Preserve observation shape, available_actions shape, reward formulas, and action semantics.

Phase 9G-3:
  playback-only validation if explicitly authorized.

Phase 9G-4:
  env-level task_status / robot_status / pair lifecycle only if wrapper-local evidence is insufficient or hidden-state risk becomes limiting.
```

## First Implementation Boundary

Recommended first implementation file:

```text
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
```

Use existing Phase 9F history columns first. No config fields or scenario YAML should be needed for Phase 9G-1.

Recommended analyzer outputs:

```text
lifecycle_reconstructed_state
lifecycle_state_reason
active_assignment_age_steps
failed_pair_memory_start_step
released_after_budget_trigger
returned_to_failed_pair_after_release
coverage_gain_within_20_after_release
same_owner_reacquire_step
teammate_reacquire_step
```

Add a tiny fixture/fake-history smoke test before any playback.

## Key Files

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_20260705.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Code behavior changed:

```text
no
```

## Latest Verification

Phase 9G-0 is documentation-only, so no `py_compile` was needed.

Final validation:

```text
git diff --check
result: passed
notes: Git reported LF-to-CRLF working-copy warnings for existing touched Markdown files only.
```

No training or playback was run.

## Known Issues / Risks

```text
Current task_status / robot_status names are richer than current live behavior.
Wrapper-local failed-pair memory would be hidden state if used for training without observation exposure.
Any future behavior mask can create overmask/noop pressure.
Cooldown, redirect guardrail, and future failed-pair memory need clear overlay ordering.
Lifecycle completion must remain tied to viewpoints_covered; failed/released states must not imply coverage.
Overlap and near-miss may require later ownership/path-aware design; failed-pair memory alone may not solve them.
```

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not implement lifecycle behavior during Phase 9G-1 diagnostics.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, installed `site-packages`, cooldown behavior, redirect guardrail behavior, or scenario behavior.

Do not tune the Phase 9F redirect guardrail as part of Phase 9G.

## Next Step

Start Phase 9G-1 with a standalone diagnostic analyzer that reconstructs active/failed/released/returned pair states from existing `assignment_history.csv` rows.

Recommended first check before coding:

```text
Read PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md.
Confirm whether to use existing Phase 9F-2C / Phase 9F-5 histories or a small checked-in fixture as the first analyzer input.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F6_COMMIT_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
```
