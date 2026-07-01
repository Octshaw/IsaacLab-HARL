# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-3C is complete.

This was diagnostics-only analysis. No training was run.

Main result:

```text
Same-target streak alone is not a reliable stuck signal.
Aggressive cooldown at streak 10 fires while repeated selections are still inside expected motion budget.
True stuck evidence appears later as over-budget no-completion segments.
```

Phase 9E-3C supports the hypothesis:

```text
Aggressive cooldown collapsed coverage because it suppressed normal multi-step target persistence.
A better stuck signal should compare accumulated same robot-target selection effort against expected robot-target cost.
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline behavior, default scenario cooldown setting, cooldown parameters, reward tuning, or core cooldown implementation logic were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-3C: budget-aware stuck-target diagnostics.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3C_BUDGET_AWARE_STUCK_TARGET_DIAGNOSTIC_REPORT.md
```

## Key Results

Diagnostic budget model:

```text
expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)
budget_steps = ceil(expected_steps * 1.5 + 5)

robot_0 max_base_xy_step = 0.08
robot_1 max_base_xy_step = 0.10
robot_2 max_base_xy_step = 0.06
```

Original Phase 9D-3 no-cooldown playback:

```text
models:
  long segments >= 10 = 70
  completed long segments = 45
  over-budget no-completion segments = 15
  known late stuck pairs recovered: robot_0->44, robot_1->44, robot_2->15

best_model:
  long segments >= 10 = 40
  completed long segments = 25
  over-budget no-completion segments = 15
  known late stuck pairs recovered: robot_0->39, robot_1->0, robot_2->15
```

Cooldown trigger timing:

```text
Phase 9D-3 models:
  threshold 10 within budget = 70/70
  threshold 30 within budget = 40/40
  threshold 50 within budget = 10/15

Phase 9D-3 best_model:
  threshold 10 within budget = 40/40
  threshold 30 within budget = 30/30
  threshold 50 within budget = 20/25

Phase 9E-3A aggressive cooldown:
  max segment length = 10
  over-budget no-completion segments = 0
  threshold 10 within budget = 15/15 for both models and best_model
```

Interpretation:

```text
Aggressive cooldown prevents repeated selections from ever reaching over-budget evidence.
It cuts at streak 10 while selections are still normal budgeted persistence.
Weak cooldown variants preserve coverage because they allow more persistence,
but they are still streak-only guardrails rather than budget-aware stuck detectors.
```

## Active Architecture / Implementation Path

Phase 9E-1 cooldown remains implemented but should still be treated as diagnostics-only until a follow-up design is accepted:

```text
AssignmentHarlWrapper-local per-robot-target cooldown
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
debug/ablation scenarios cooldown-enabled
```

Recommended next design direction:

```text
Budget-aware stuck signal:
  same robot-target repeated
  selected target remains uncovered/available/feasible
  accumulated selection steps exceed expected cost-derived budget
  no selected-target completion occurred
  optionally require global stagnation
```

Important interpretation:

```text
Cooldown is a wrapper-local action-mask guardrail.
It does not prove a target is unreachable.
It only suppresses repeated selection of the same robot-target pair under configured conditions.
```

## Key Files

New Phase 9E-3C diagnostic script:

```text
scripts/environments/analyze_assignment_stuck_budget.py
```

Phase 9E-3C documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3C_BUDGET_AWARE_STUCK_TARGET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3C_BUDGET_AWARE_STUCK_DIAGNOSTICS_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9E-3C outputs:

```text
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/budget_aware_segment_summary.csv
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/budget_aware_source_summary.csv
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/budget_aware_summary.json
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics_strict_budget/
```

## Latest Verification

Pre-flight:

```text
git status --short: existing Phase 9E-3B docs/config state
git diff --check: passed, LF-to-CRLF warning on TASK_PROGRESS.md only
```

Script checks:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\analyze_assignment_stuck_budget.py
passed
```

Diagnostics:

```text
main budget analysis: processed 12 sources and 32000 segments
strict budget sensitivity: processed 12 sources and 32000 segments
```

Final repository checks after Phase 9E-3C docs:

```text
git diff --check: passed; LF-to-CRLF warning on TASK_PROGRESS.md only
git status --short: TASK_PROGRESS.md modified; Phase 9E-3C script/report/archive untracked under expected paths; Phase 9E-3B ablation scenario files still untracked
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-3C limitations:

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not full path length
actual_base_motion_distance in playback history is obstacle-footprint distance, not traveled distance
effort proxy is contiguous same robot-target decision count
no new cooldown rule was implemented
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run 100k training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Phase 9E-3D: design a config-gated budget-aware cooldown trigger, but do not train yet.
```

Design constraints:

```text
disabled by default
assignment RL only
wrapper-local if implemented
reward unchanged
observation dimensions unchanged unless a separate design explicitly approves observation changes
playback-only validation before any training
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3C_BUDGET_AWARE_STUCK_TARGET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3C_BUDGET_AWARE_STUCK_DIAGNOSTICS_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3B_COOLDOWN_STRENGTH_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3B_COOLDOWN_ABLATION_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3A_CROSS_PLAYBACK_COOLDOWN_ATTRIBUTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3A_CROSS_PLAYBACK_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
```
