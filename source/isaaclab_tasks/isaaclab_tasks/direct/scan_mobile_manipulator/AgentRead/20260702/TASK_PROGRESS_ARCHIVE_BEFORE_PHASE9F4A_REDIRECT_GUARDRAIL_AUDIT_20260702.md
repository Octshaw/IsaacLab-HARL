# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-3 is complete.

This phase was design-only. No code behavior changed. No training was run. No playback was run. No broad evaluation was run.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger/mask logic, scenario YAML behavior, conflict-aware redirect implementation, active-task lifecycle implementation, or installed `site-packages` were changed.

No commit was made.

## Latest Completed Phase

Phase 9F-3: design decision for conflict redirect versus active-task lifecycle.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
```

## Key Decision

Recommended next implementation phase:

```text
Phase 9F-4:
  Implement a minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail.
  Keep it wrapper-local if possible.
  Keep reward unchanged.
  Keep observations unchanged.
  Keep available_actions shape unchanged.
  Keep assignment action semantics unchanged.
  Keep base environment available_mask semantics unchanged.
  Keep noop always available.
  Keep default scenarios disabled.
  Add diagnostic logging for suppression and over-mask/noop-pressure cases.
```

Recommended follow-up design phase:

```text
Phase 9G-0:
  Design active-task lifecycle or explicit failed-target state.
  Treat repeated return-to-triggered-pair as a first-class lifecycle problem.
```

## Evidence Basis

Phase 9F-1 broad attribution:

```text
models + budget:
  exact next target already claimed = 20/30
  nearby distinct next-target conflict = 25/30
  coverage gain within 20 steps = 0/30
  return to triggered pair after cooldown = 30/30
  cause labels = A+B+C+D

best_model + budget:
  exact next target already claimed = 0/70
  nearby distinct next-target conflict = 50/70
  coverage gain within 20 steps = 25/70
  return to triggered pair after cooldown = 65/70
  cause labels = B
```

Phase 9F-2C direct row-level validation:

```text
assignment_history.csv rows = 897
assignment_history.csv columns = 61
budget_trigger_row_count = 6
trigger_pairs = r1->36:4, r2->44:2
next_exact_duplicate_direct_count = 4 / 6
next_nearby_selected_target_direct_count = 5 / 6
next_inter_robot_overlap_direct_count = 6 / 6
next_path_crossing_direct_count = 1 / 6
next_path_near_miss_direct_count = 5 / 6
coverage_gain_within_20_count = 0 / 6
return_to_triggered_pair_after_cooldown_count = 6 / 6
```

Direct fields agreed with old reconstructed selected-target proxies:

```text
exact_direct_reconstructed_mismatch_count = 0
nearby_direct_reconstructed_mismatch_count = 0
selected_target_pair_count_direct_reconstructed_mismatch_count = 0
```

## Active Architecture / Implementation Path

Phase 9F remains diagnostic-first and config-gated.

Budget-aware cooldown remains assignment-wrapper-local:

```text
per-robot-target cooldown
trigger_mode = budget_and_streak for the Phase 9E debug scenario
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
```

Phase 9F-4, if authorized, should add a local redirect guardrail only around budget/cooldown redirect contexts. It should not globally mask normal assignment decisions.

## Key Files

Files created or updated in Phase 9F-3:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F3_DESIGN_DECISION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No Python files were changed in Phase 9F-3.

Python files still modified or untracked from earlier Phase 9F work:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
scripts/environments/analyze_phase9f2c_trigger_windows.py
```

## Latest Verification

Phase 9F-3 validation:

```text
git diff --check
result: passed
note: emitted LF/CRLF warnings for evaluate_assignment_rl_playback_diagnostics.py and TASK_PROGRESS.md only
```

No `py_compile` was required for Phase 9F-3 because no Python files were changed in this phase.

No playback or training was run.

## Known Issues / Limitations

```text
local redirect guardrail is not a final lifecycle solution
path crossing / near-miss remains an observed straight pre/post base-segment proxy
Phase 9F-2C evidence is one episode, one checkpoint, one limited playback
repeated return-to-triggered-pair remains strong evidence for active-task lifecycle or explicit failed-target state
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training or broad playback sweeps.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, scenario YAML behavior, path-crossing-aware redirect, or active-task lifecycle without a new explicit phase request.

## Next Step

Recommended next phase:

```text
Phase 9F-4:
  Implement the minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail.
  Add diagnostics for claimed-target suppression, spacing suppression, over-mask fallback, and only-noop remaining cases.
  Preserve noop availability and base env available_mask semantics.
  Keep default scenarios disabled.
```

Recommended validation after implementation:

```text
py_compile changed Python files
git diff --check
no training
playback only if explicitly authorized for validation
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F3_DESIGN_DECISION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2B_ROW_LEVEL_LOGGING_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
```
