# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-3 playback-only validation is complete.

No training was run. Playback was run only for validation:

```text
phase9g3_default_disabled
phase9g3_failed_pair_memory_enabled
```

Default-disabled behavior passed the Phase 9F-5 identity check at the measured playback/analyzer level. Enabled failed-pair memory triggered, but did not reduce same-owner returns because the default `duration_steps=5` TTL expired before the reacquisition rows.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or Phase 9F redirect guardrail tuning were changed.

No commit was made.

## Latest Completed Phase

Phase 9G-3: failed-pair/release-memory playback validation.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
```

Archived previous progress:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_20260706.md
```

## Validation Summary

Comparison table:

```text
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/phase9g3_comparison_table.csv
```

Key metrics:

```text
reference_phase9f5_redirect_guardrail:
  final_coverage_ratio = 0.5
  coverage_auc = 0.33043458868428616
  same_owner_returns = 6
  coverage_gain_within_20_count = 0
  noop_action_rate = 0.0
  next_exact_duplicate_direct_count = 0
  next_nearby_selected_target_direct_count = 0
  next_inter_robot_overlap_direct_count = 6
  next_path_crossing_direct_count = 0
  next_path_near_miss_direct_count = 6

phase9g3_default_disabled:
  matched Phase 9F-5 measured metrics above
  failed_pair_memory_trigger_count = 0
  failed_pair_memory_suppressed_count = 0

phase9g3_failed_pair_memory_enabled:
  final_coverage_ratio = 0.5
  coverage_auc = 0.33043458868428616
  same_owner_returns = 6
  coverage_gain_after_release_count = 0
  coverage_gain_within_20_count = 0
  noop_action_rate = 0.0
  noop_when_available_rate = 0.0
  failed_pair_memory_trigger_count = 6
  failed_pair_memory_active_pair_step_total = 30
  failed_pair_memory_active_step_count = 22
  failed_pair_memory_suppressed_count = 0
  failed_pair_memory_fail_open_count = 0
  failed_pair_memory_only_noop_remaining_count = 0
```

TTL boundary finding:

```text
duration_steps = 5
same-owner return delay proxy = 5
trigger-to-return delta in trigger-window rows = 6
selected_pair_active_at_return = False for all 6 returns
ttl_remaining_at_return = 0 for all 6 returns
```

Conclusion:

```text
default-disabled identity: PASS
enabled failed-pair memory: FAIL
reason: memory triggered but expired before same-owner reacquisition, so no action-mask suppression occurred
```

## Validation Commands

Completed successfully:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f2c_trigger_windows.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
git diff --check
```

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run more playback unless explicitly authorized.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or redirect guardrail tuning.

## Next Step

Recommended next phase:

```text
Phase 9G-4A: TTL-boundary design review and fake-env validation before any further playback.
```

The current evidence does not justify adopting enabled failed-pair memory as successful. It does justify a narrow TTL semantics review because `duration_steps=5` misses the observed same-owner return rows.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
