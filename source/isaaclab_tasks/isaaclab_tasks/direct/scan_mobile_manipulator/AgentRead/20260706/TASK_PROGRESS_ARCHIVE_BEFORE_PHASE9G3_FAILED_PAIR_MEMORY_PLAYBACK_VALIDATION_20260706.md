# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-2 is complete.

Phase 9G-2 implemented a disabled-by-default wrapper-local failed-pair/release-memory guardrail. It is pair-scoped as `(env, robot, target)` and is triggered only by the existing budget-triggered cooldown failure signal.

No training was run. No playback was run. Default behavior is unchanged when the guardrail is disabled.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or Phase 9F redirect guardrail tuning were changed.

No commit was made.

## Latest Completed Phase

Phase 9G-2: disabled-by-default wrapper-local failed-pair/release-memory guardrail.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
```

## Implementation Summary

Changed:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/test_assignment_failed_pair_memory_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Archived previous progress:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_20260706.md
```

Config defaults:

```text
assignment_failed_pair_memory_enabled = False
assignment_failed_pair_memory_duration_steps = 5
assignment_failed_pair_memory_apply_to_action_mask = True
assignment_failed_pair_memory_source = "budget_trigger"
assignment_failed_pair_memory_fail_open = True
assignment_failed_pair_memory_clear_on_coverage = True
assignment_failed_pair_memory_log_diagnostics = True
```

Memory state:

```text
_assignment_failed_pair_memory_remaining[env, robot, target]
_assignment_failed_pair_memory_trigger_step[env, robot, target]
```

Actual available-action overlay order:

```text
base env available_mask clone
existing cooldown overlay
existing Phase 9F redirect guardrail overlay
new failed-pair/release-memory overlay
append/preserve noop
fail-open if memory would remove all non-noop targets for a robot
```

The disabled fast path still uses `make_assignment_action_mask(problem, include_noop)` when cooldown, redirect guardrail, and failed-pair memory masking are all disabled.

## Validation Result

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_failed_pair_memory_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_failed_pair_memory_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_cooldown_mask_smoke.py
result: passed

git diff --check
result: passed
notes: Git emitted LF-to-CRLF working-copy warnings for TASK_PROGRESS.md, assignment_harl_wrapper.py, and scenario_config.py.
```

## Smoke Test Coverage

```text
default-disabled identity
enabled pair-scoped suppression
same target remains available to a teammate
noop preservation
fail-open
TTL expiry
coverage clear
reset clear
available_actions shape unchanged
base available_mask not mutated in-place
budget-trigger source diagnostics
existing cooldown/redirect smoke still passes
```

## Known Risks

```text
Wrapper-local failed-pair memory is hidden state if later used for training without observation exposure.
Overmask/noop pressure must be watched in playback metrics.
The guardrail can target repeated same-owner return, but may not solve row-level overlap or near-miss by itself.
If cooldown budget triggering is disabled or not reached, failed-pair memory does not activate.
Env-level task_status / robot_status lifecycle remains deferred.
```

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not implement env-level lifecycle without a separate design phase.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or redirect guardrail tuning.

## Next Step

Recommended next phase:

```text
Phase 9G-3: fake-env/report review first, then playback-only validation only if explicitly authorized by the user.
```

Recommended Phase 9G-3 validation target:

```text
default-disabled identity check
enabled failed-pair memory playback comparison
same_owner_returns
teammate_reacquires
coverage_gain_after_release_count
coverage_gain_within_20_count
noop_action_rate
noop_when_available_rate
final_coverage_ratio
coverage_auc
overlap / crossing / near-miss diagnostics
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
