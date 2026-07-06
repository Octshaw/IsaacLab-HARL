# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-6 is complete.

This phase reviewed the Phase 9F working tree for commit readiness. Classification:

```text
COMMIT-READY
```

No commit was made. No training was run. No playback was run during Phase 9F-6.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, path-crossing-aware redirect, active-task lifecycle, installed `site-packages`, or guardrail parameters were changed.

## Latest Completed Phase

Phase 9F-6: commit readiness review.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F6_COMMIT_READINESS_REVIEW.md
```

## Commit Readiness Summary

Recommended commit contents:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
scripts/environments/analyze_phase9f2c_trigger_windows.py
scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/*.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/*.md
```

Not recommended for commit:

```text
results/assignment_diagnostics/phase9f1_post_budget_redirect_conflict_diagnostics/
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/
```

These generated result files are ignored by the repository rule `**/results/*`; AgentRead reports summarize the needed results.

Unexpected files needing user decision:

```text
none found
```

## Guardrail Status

The Phase 9F-4B guardrail is implemented in `AssignmentHarlWrapper` only and remains disabled by default.

Boundary:

```text
supported context: recent_budget_trigger
default window_steps = 1
uses _previous_assignment as teammate claim snapshot
uses problem["viewpoint_pos"][..., :2] for spacing
derives default threshold from 2 * inter_robot_target_conflict_radius + inter_robot_target_conflict_safety_margin
applies after existing cooldown overlay
does not modify _apply_assignment_cooldown_to_available_mask()
does not mutate base env available_mask
preserves noop
fails open on over-mask by default
logs suppression / over-mask / fail-open diagnostics
```

Debug-only guardrail-enabled scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

Original/default scenarios remain guardrail-disabled.

## Phase 9F-5 Validation Result To Preserve

```text
classification = GUARDRAIL-P
next_exact_duplicate_direct_count: 4/6 -> 0/6
next_nearby_selected_target_direct_count: 5/6 -> 0/6
next_inter_robot_overlap_direct_count: 6/6 -> 6/6
next_path_crossing_direct_count: 1/6 -> 0/6
next_path_near_miss_direct_count: 5/6 -> 6/6
coverage_gain_within_20_count: 0/6 -> 0/6
return_to_triggered_pair_after_cooldown_count: 6/6 -> 6/6
final_coverage_ratio: 0.5 -> 0.5
coverage_auc: 0.330434779 -> 0.330434779
noop_when_available_rate: 0.0 -> 0.0
noop_action_rate: 0.0 -> 0.0
```

Interpretation:

```text
The disabled-by-default local guardrail is promising for exact/nearby redirect-conflict mitigation.
It is not a lifecycle solution.
It did not reduce row-level overlap.
It did not reduce return-to-triggered-pair.
It did not create coverage gain within 20 steps.
It is not a broad performance claim.
```

## Latest Verification

Phase 9F-6 validation:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py scripts/environments/evaluate_assignment_rl_playback_diagnostics.py scripts/environments/test_assignment_cooldown_mask_smoke.py scripts/environments/analyze_phase9f1_post_budget_conflicts.py scripts/environments/analyze_phase9f2c_trigger_windows.py scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_cooldown_mask_smoke.py
result: passed

git diff --check
result: passed
notes: Git reported LF-to-CRLF working-copy warnings for existing touched files only.
```

## Recommended Commit Message

```text
Phase 9F: add redirect guardrail diagnostics and validation

- add disabled-by-default assignment redirect guardrail config plumbing
- implement wrapper-local claimed-target and spacing-aware redirect guardrail
- extend playback assignment history with row-level conflict and guardrail diagnostics
- add Phase 9F CSV analyzers and fake-env smoke coverage
- document Phase 9F diagnostics, validation, and commit readiness
```

## Known Issues / Limitations

```text
Phase 9F-5 was one episode, one checkpoint, one limited playback
GUARDRAIL-P is not a broad performance claim
same-step simultaneous new claims are not solved
path-crossing-aware redirect is not implemented
active-task lifecycle is not implemented
return-to-triggered-pair remains high
row-level overlap remains high
near-miss proxy did not improve in Phase 9F-5
generated results should stay out of commit unless explicitly requested
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training.

Do not run playback or broad sweeps unless explicitly authorized.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, default scenario behavior, path-crossing-aware redirect, active-task lifecycle, installed `site-packages`, or guardrail parameters.

## Next Step

Recommended next action:

```text
If the user authorizes a commit:
  stage the recommended files from the Phase 9F-6 report;
  do not stage generated results under results/;
  use the recommended commit message or a concise equivalent.

After commit:
  start Phase 9G-0 active-task lifecycle / explicit failed-target-state design,
  because return-to-triggered-pair remains unresolved.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F6_COMMIT_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F6_COMMIT_READINESS_REVIEW_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F5_GUARDRAIL_PLAYBACK_VALIDATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_PATH_CORRECTION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2B_ROW_LEVEL_LOGGING_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
```
