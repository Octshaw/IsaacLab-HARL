# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-1 is complete.

This phase ran diagnostic-only post-budget-redirect conflict attribution on existing Phase 9E-4B playback outputs.

No training was run.
No playback was run.
No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, HARL, baseline solvers, cooldown logic, scenario YAML behavior, conflict-aware redirect, or active-task lifecycle logic were changed.

No commit was made.

Final classification:

```text
DIAG-P
```

Meaning:

```text
Attribution is useful and actionable for exact duplicate redirects, nearby target conflict, post-trigger coverage gain, and return-to-triggered-pair behavior.
Attribution remains partial because row-level inter-robot overlap and true inter-robot path crossing are not present in assignment_history.csv.
```

## Latest Completed Phase

Phase 9F-1: post-budget-redirect conflict diagnostics.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
```

## Key Results

Schema sufficiency:

```text
DIAG-PARTIAL
```

Fields sufficient for:

```text
selected target per robot per step
budget trigger step
triggered robot-target pair
next selected target after trigger
whether next target is already selected by another robot
selected target position proxy
duplicate selected target proxy
coverage gain after redirect
return to triggered pair after cooldown
reconstructed selected-target distance conflict
```

Fields insufficient or partial for:

```text
row-level inter-robot overlap
true inter-robot path crossing
full unselected viewpoint positions inside assignment_history.csv
post-step robot base positions
```

Conflict attribution:

```text
models + budget:
  triggers = 30
  trigger pairs = r1->36:20; r2->44:10
  next targets = 44:20; 24:10
  exact next target already claimed = 20/30
  nearby distinct next-target conflict = 25/30
  coverage gain within 20 steps = 0/30
  return to triggered pair after cooldown = 30/30
  cause labels = A+B+C+D

best_model + budget:
  triggers = 70
  trigger pairs = r2->11:45; r1->36:20; r0->15:5
  next targets = 24:45; 27:20; 25:5
  exact next target already claimed = 0/70
  nearby distinct next-target conflict = 50/70
  coverage gain within 20 steps = 25/70
  return to triggered pair after cooldown = 65/70
  cause labels = B
```

Cause labels:

```text
A = exact duplicate redirect conflict
B = nearby-target spatial conflict
C = component/base-motion crossing proxy elevated post-trigger
D = persistent policy preference / conflict also outside trigger windows
E = insufficient trace fields
```

Important interpretation:

```text
models/ has strong post-trigger exact duplicate and nearby conflicts, but also high outside-window selected-target conflict.
best_model/ has no exact duplicate redirect conflict; the main post-trigger issue is nearby-target conflict.
Repeated return to triggered pairs is high in both runs, which points toward active-task lifecycle or explicit failed-target state as an eventual concern.
```

## Active Architecture / Implementation Path

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

Phase 9F-1 did not implement conflict-aware redirect or active-task lifecycle.

## Key Files

Added diagnostic script:

```text
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
```

Added Phase 9F-1 report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
```

Archived previous task progress:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F1_CONFLICT_DIAGNOSTICS_20260702.md
```

Updated current handoff:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9F-1 outputs:

```text
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/assignment_history_schema_inventory.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_conflict_windows.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/post_trigger_next_target_summary.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/conflict_cause_attribution_summary.csv
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_summary.json
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/phase9f1_conflict_diagnostics_notes.md
```

## Latest Verification

Phase 9F-1 analyzer run:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed
classification: DIAG-P
```

Final validation:

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

## Known Issues / Blockers

No execution blocker.

Known diagnostic limitations:

```text
row-level inter-robot overlap is unavailable in assignment_history.csv
true inter-robot path crossing is unavailable
actual_base_motion_intersects_component is a component/obstacle crossing proxy only
robot_base_x/y are pre-step playback positions
playback traces are deterministic/repeated across five episodes
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training.
Do not run playback unless a required file is missing and the need is explicitly reported first.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, HARL, baseline solvers, cooldown logic, scenario YAML behavior, conflict-aware redirect, or active-task lifecycle logic without a new explicit phase request.

## Next Step

Recommended next phase:

```text
Phase 9F-2 design decision.
Decide whether to first add missing row-level overlap/path diagnostics or design a minimal config-gated claimed-target + spacing-aware redirect guardrail.
```

Recommendation from Phase 9F-1:

```text
For models/, a local claimed-target or spacing-aware redirect may reduce exact/nearby redirect conflict, but it will not fully solve persistent outside-window conflict or repeated return-to-triggered-pair behavior.
For best_model/, spacing-aware redirect is the more relevant local mechanism than exact target reservation.
Before claiming overlap/path causality, add row-level overlap and true path-crossing diagnostics.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F1_CONFLICT_DIAGNOSTICS_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E4B_BUDGET_TRAINED_PLAYBACK_20260701.md
```
