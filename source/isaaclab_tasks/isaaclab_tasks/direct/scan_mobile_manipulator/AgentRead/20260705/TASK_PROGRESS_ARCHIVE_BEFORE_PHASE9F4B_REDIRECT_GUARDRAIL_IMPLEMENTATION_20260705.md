# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-4A is complete.

This phase was an implementation-boundary audit only. No guardrail was implemented. No code behavior changed. No training was run. No playback was run. No broad evaluation was run.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, scenario YAML behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages` were changed.

No commit was made.

## Latest Completed Phase

Phase 9F-4A: redirect guardrail implementation-boundary audit.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
```

## Key Audit Finding

No stop-condition blocker was found.

Phase 9F-4B can implement the claimed-target + spacing-aware redirect guardrail wrapper-locally if it stays inside this boundary:

```text
config-gated and disabled by default
active only in a recent budget-trigger redirect window
uses _previous_assignment as the teammate claim snapshot
uses problem["viewpoint_pos"][..., :2] for spacing
uses 0.85 m derived threshold by default for the Phase 9E/9F budget scenario
applies after the existing cooldown overlay
does not mutate base env available_mask
preserves noop
fails open on over-mask
logs suppression and over-mask diagnostics
does not implement path-crossing-aware redirect
does not implement active-task lifecycle
```

## Cooldown / Mask Insertion Point

Current cooldown mask path:

```text
assignment_harl_wrapper.py
  _build_available_actions()
    reads problem["available_mask"]
    applies _apply_assignment_cooldown_to_available_mask()
    appends noop as an always-available final column
    checks shape, all-zero rows, and noop availability

  _apply_assignment_cooldown_to_available_mask()
    returns available_mask & (~cooldown_mask)
```

Recommended Phase 9F-4B insertion:

```text
add a separate _apply_assignment_redirect_guardrail_to_available_mask()
call it after the existing cooldown overlay inside _build_available_actions()
do not modify _apply_assignment_cooldown_to_available_mask()
```

## Recommended Phase 9F-4B Sequence

```text
1. Add disabled-by-default redirect-guardrail config fields in scenario_config.py.
2. Add AssignmentHarlWrapper _assignment_redirect_guardrail_config with disabled defaults.
3. Add wrapper-local redirect-window state reset with assignment diagnostics.
4. Set redirect-window state only when _update_assignment_cooldown() observes a budget_trigger.
5. Add separate guardrail mask overlay after the existing cooldown overlay.
6. Compute claimed-target suppression from _previous_assignment teammate targets.
7. Compute spacing suppression from problem["viewpoint_pos"][..., :2].
8. Fail open spacing first; fail open claimed-target if configured or only-noop would remain.
9. Preserve noop and base env available_mask semantics.
10. Add wrapper/playback diagnostics.
11. Add or extend a fake-env smoke test similar to test_assignment_cooldown_mask_smoke.py.
12. Run py_compile on changed Python files and git diff --check.
```

Recommended initial config values:

```text
assignment_redirect_guardrail_enabled = false
assignment_redirect_guardrail_apply_context = recent_budget_trigger
assignment_redirect_guardrail_window_steps = 1
assignment_redirect_guardrail_claimed_target_enabled = true
assignment_redirect_guardrail_spacing_enabled = true
assignment_redirect_guardrail_spacing_threshold = null
assignment_redirect_guardrail_fail_open_spacing = true
assignment_redirect_guardrail_fail_open_claimed = true
assignment_redirect_guardrail_log_diagnostics = true
```

## Evidence Basis

Phase 9F-2C direct row-level validation:

```text
trigger_count = 6
trigger_pairs = r1->36:4, r2->44:2
next_exact_duplicate_direct_count = 4 / 6
next_nearby_selected_target_direct_count = 5 / 6
next_inter_robot_overlap_direct_count = 6 / 6
next_path_crossing_direct_count = 1 / 6
next_path_near_miss_direct_count = 5 / 6
coverage_gain_within_20_count = 0 / 6
return_to_triggered_pair_after_cooldown_count = 6 / 6
```

## Key Files

Files created or updated in Phase 9F-4A:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4A_REDIRECT_GUARDRAIL_AUDIT_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No Python files were changed in Phase 9F-4A.

Python files still modified or untracked from earlier Phase 9F work:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f1_post_budget_conflicts.py
scripts/environments/analyze_phase9f2c_trigger_windows.py
```

## Latest Verification

Phase 9F-4A validation:

```text
git diff --check
result: passed
notes: Git reported LF-to-CRLF working-copy warnings for existing touched files only.
```

No `py_compile` was required for Phase 9F-4A because no Python files were changed in this phase.

No playback or training was run.

## Known Issues / Limitations

```text
Phase 9F-4A did not implement the guardrail
same-step simultaneous new claims cannot be solved by previous-assignment snapshots
local redirect guardrail is not an active-task lifecycle solution
path crossing / near-miss remains diagnostic-only
return-to-triggered-pair remains a Phase 9G-0 lifecycle design issue
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training or broad playback sweeps.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, scenario YAML behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages` without a new explicit phase request.

## Next Step

Recommended next phase:

```text
Phase 9F-4B:
  Implement the minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail.
  Keep it wrapper-local and disabled by default.
  Add diagnostics and fake-env smoke coverage.
  Do not run playback unless explicitly authorized.
  Do not train.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4A_REDIRECT_GUARDRAIL_AUDIT_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F3_DESIGN_DECISION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```
