# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-4B is complete.

This phase implemented a minimal wrapper-local claimed-target + spacing-aware cooldown-redirect guardrail. It is config-gated and disabled by default.

No training was run. No playback was run. No broad evaluation was run. No commit was made.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, default scenario YAML behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages` were changed.

## Latest Completed Phase

Phase 9F-4B: minimal redirect guardrail implementation.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
```

## Active Implementation Path

The guardrail is implemented in `AssignmentHarlWrapper` only.

Boundary:

```text
disabled by default
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

New config keys:

```text
assignment_redirect_guardrail_enabled = false
assignment_redirect_guardrail_apply_context = recent_budget_trigger
assignment_redirect_guardrail_window_steps = 1
assignment_redirect_guardrail_claimed_target_enabled = true
assignment_redirect_guardrail_spacing_enabled = true
assignment_redirect_guardrail_spacing_threshold = None
assignment_redirect_guardrail_fail_open_spacing = true
assignment_redirect_guardrail_fail_open_claimed = true
assignment_redirect_guardrail_log_diagnostics = true
```

## Key Files

Changed Python files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

Created/updated documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Latest Verification

Phase 9F-4B validation:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_cooldown_mask_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_cooldown_mask_smoke.py
result: passed

git diff --check
result: passed
notes: Git reported LF-to-CRLF working-copy warnings for existing touched files only.
```

## Known Issues / Limitations

```text
same-step simultaneous new claims are not solved
path-crossing-aware redirect is not implemented
active-task lifecycle is not implemented
return-to-triggered-pair is not expected to be solved by this local guardrail
performance is not claimed until playback validation
guardrail is disabled unless a future scenario/config explicitly enables it
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training.

Do not run playback unless a future phase explicitly authorizes playback validation.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, default scenario YAML behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages`.

## Next Step

Recommended next phase:

```text
Phase 9F-5:
  Run playback-only validation if explicitly authorized.
  Use a guardrail-enabled config/run path.
  Validate new guardrail CSV fields, suppression counts, fail-open counts, noop pressure, exact/nearby post-trigger conflicts, overlap/near-miss proxies, coverage ratio/AUC, return-to-triggered-pair, and coverage gain within 20 steps.
  Do not train.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```
