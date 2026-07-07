# Phase 9G-4A TTL Boundary Semantics Review

Date: 2026-07-06

## Scope And Boundary

Phase 9G-4A reviewed the TTL semantics of the Phase 9G-2 wrapper-local failed-pair/release-memory guardrail using fake-env/unit-style validation only.

No training was run. No playback was run. No broad evaluation was run.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, installed packages, scenario YAML, cooldown tuning, Phase 9F redirect guardrail tuning, new failure criteria, or env-level lifecycle behavior were changed.

`assignment_harl_wrapper.py` was not modified in Phase 9G-4A. No failed-pair memory behavior was changed.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_failed_pair_memory_smoke.py
scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
```

## Files Created Or Updated

Created:

```text
scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW_20260706.md
results/assignment_diagnostics/phase9g4a_ttl_boundary_smoke/ttl_boundary_trace.json
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No wrapper, config, scenario, reward, observation, controller, HARL, baseline, or installed package files were modified during Phase 9G-4A.

## Current Implementation Order

The relevant wrapper order is:

```text
step pre-action:
  _build_available_actions(pre_step_problem)
  decode selected assignment
  env.step(...)

step diagnostics:
  _update_assignment_diagnostics(...)
    _assignment_step = previous_step + 1
    _update_assignment_cooldown(...)
      reset step diagnostics
      capture selected failed-pair memory state before TTL decrement
      decrement existing failed-pair memory by 1
      clear covered targets if configured
      run cooldown/budget trigger logic
      activate new failed-pair memory for budget-triggered pairs

step post-action:
  _build_available_actions(post_step_problem)
```

The failed-pair memory mask itself suppresses a pair when:

```text
_assignment_failed_pair_memory_remaining[env, robot, target] > 0
and the target is still available in the incoming mask after base/cooldown/redirect overlays
and suppression does not trigger fail-open
```

Diagnostics nuance:

```text
selected_pair_active and selected_pair_ttl_remaining are captured before decrement.
active_count is reported from the current memory tensor after decrement.
```

This means row-level `active_count` can appear one row shorter than the decision/build-available-actions suppression window.

## Observed TTL Semantics

For a budget-triggered memory activation at logical trigger step `T` with `duration_steps = D`:

```text
The memorized pair is suppressible for subsequent decision/build_available_actions offsets T+1 through T+D.
The memorized pair is not suppressible at T+D+1.
```

So the current implementation means:

```text
duration_steps = D means active for D future decision/build_available_actions calls after the trigger step.
```

It does not mean active on the trigger row itself. It also does not mean active through `T + D + 1`.

## Fake-Env TTL Trace

Trace output:

```text
results/assignment_diagnostics/phase9g4a_ttl_boundary_smoke/ttl_boundary_trace.json
```

The test used `trigger_step = 100`, `robot_id = 0`, and `target_id = 2`.

For D=5:

| offset | before decrement | after decrement | selected active | selected ttl | suppressed | available before | available after |
| ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| T+1 | 5 | 4 | True | 5 | 1 | True | False |
| T+2 | 4 | 3 | True | 4 | 1 | True | False |
| T+3 | 3 | 2 | True | 3 | 1 | True | False |
| T+4 | 2 | 1 | True | 2 | 1 | True | False |
| T+5 | 1 | 0 | True | 1 | 1 | True | False |
| T+6 | 0 | 0 | False | 0 | 0 | True | True |
| T+7 | 0 | 0 | False | 0 | 0 | True | True |

For D=6:

| offset | before decrement | after decrement | selected active | selected ttl | suppressed |
| ---: | ---: | ---: | --- | ---: | ---: |
| T+1 | 6 | 5 | True | 6 | 1 |
| T+2 | 5 | 4 | True | 5 | 1 |
| T+3 | 4 | 3 | True | 4 | 1 |
| T+4 | 3 | 2 | True | 3 | 1 |
| T+5 | 2 | 1 | True | 2 | 1 |
| T+6 | 1 | 0 | True | 1 | 1 |
| T+7 | 0 | 0 | False | 0 | 0 |

For D=7:

```text
active/suppressed offsets = T+1, T+2, T+3, T+4, T+5, T+6, T+7
inactive at T+8
```

For D=10:

```text
active/suppressed offsets = T+1 through T+10
inactive at T+11
```

Coverage summary:

| duration | covers T+4 | covers T+5 | covers T+6 | active offsets |
| ---: | --- | --- | --- | --- |
| 5 | True | True | False | 1..5 |
| 6 | True | True | True | 1..6 |
| 7 | True | True | True | 1..7 |
| 10 | True | True | True | 1..10 |

## Additional Fake-Env Checks

The TTL boundary smoke also verified:

```text
selected_pair_active becomes true when the selected pair is exactly the memorized pair during active TTL.
selected_pair_ttl_remaining reports the pre-decrement TTL for that selected pair.
suppressed_count becomes positive when the memorized target is available and memory is active.
suppressed_count remains zero when the memorized target is already unavailable before memory overlay.
fail-open preserves the only non-noop target when suppression would remove all target options.
noop remains available.
TTL clears on coverage.
TTL clears on reset.
```

Observed side-case outputs:

```text
unavailable memorized target:
  available_before_memory_for_pair = False
  available_after_memory_for_pair = False
  suppressed_count = 0

fail-open:
  target_available_after_fail_open = True
  noop_available = True
  fail_open_count = 1
  suppressed_count = 0

coverage clear:
  remaining_after_coverage_clear = 0

reset clear:
  remaining_after_reset = 0
  nonnegative_trigger_steps_after_reset = 0
```

## Why Phase 9G-3 D=5 Missed Return Rows

Phase 9G-3 observed:

```text
duration_steps = 5
same-owner return delay proxy = 5
trigger-to-return delta in trigger-window rows = 6
selected_pair_active_at_return = False for all 6 return rows
ttl_remaining_at_return = 0 for all 6 return rows
```

Under the current fake-env-confirmed semantics, D=5 covers decision/build offsets `T+1` through `T+5`, but not `T+6`.

The G3 trigger-window return rows were at `T+6`:

```text
240 -> 246
256 -> 262
271 -> 277
272 -> 278
287 -> 293
288 -> 294
```

Therefore the D=5 memory expired before the repeated-return action row. The phrase `same-owner return delay proxy = 5` counts the reconstructed proxy delay differently from the direct trigger-to-return row delta. For action-mask suppression, the direct decision-row delta is the relevant boundary, and that boundary was `T+6`.

## Would Longer Duration Cover The G3 Returns?

Under current semantics:

```text
D=5: does not cover T+6 return rows.
D=6: covers T+6 return rows.
D=7: covers T+6 return rows.
D=10: covers T+6 return rows.
```

This does not prove that longer duration improves coverage or overlap outcomes. It only proves the mask would be active at the previously observed return row if the target remained otherwise available and fail-open did not apply.

## Decrement Timing Option

Changing decrement timing could make D=5 cover the observed T+6 row, but only by changing the behavior contract.

Current contract:

```text
D means D future decision/build_available_actions calls after trigger.
```

A delayed-decrement contract might become:

```text
D means D+1 future decision/build_available_actions calls after trigger
or D means active through a closed trigger-plus-D boundary.
```

That could align better with the lifecycle proxy phrase "return delay 5", but it introduces an off-by-one behavior change and would require updating fake-env smoke expectations plus rerunning default-disabled identity and playback-only validation.

## Risks Of Increasing Duration

```text
overmask pressure if a robot is blocked from useful reacquisition longer than needed
noop pressure if memory combines with cooldown/redirect masks and leaves few target choices
fail-open pressure if memory frequently attempts to remove all non-noop target options
hidden-state training risk if enabled during training without observation exposure
blocking useful same-robot reacquisition after transient obstruction clears
interaction risk with cooldown and redirect guardrail overlays, since memory applies after both
```

## Risks Of Changing Decrement Timing

```text
off-by-one behavior change for every enabled memory use
existing smoke-test expectations would need updates
default-disabled identity still needs confirmation even if disabled path should remain unchanged
enabled playback-only validation would need rerun
row-level diagnostics may need clearer before/after TTL naming
```

## Validation

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_failed_pair_memory_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_failed_pair_memory_smoke.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py --result_file results/assignment_diagnostics/phase9g4a_ttl_boundary_smoke/ttl_boundary_trace.json
result: passed

git diff --check
result: passed
notes: Git emitted LF-to-CRLF working-copy warnings for evaluate_assignment_rl_playback_diagnostics.py, TASK_PROGRESS.md, assignment_harl_wrapper.py, and scenario_config.py.
```

## Recommendation

Recommended Phase 9G-4B option: **Option A, keep current TTL semantics and, only if explicitly authorized, run a playback-only test with a longer disabled-by-default duration such as D=6 or D=10.**

Reason:

```text
Current semantics are internally coherent: D future decision/build calls.
The Phase 9G-3 miss was caused by D=5 being one decision row too short for the observed T+6 return.
Changing decrement timing is a broader behavior contract change than needed to answer the next empirical question.
```

Do not train. Do not run playback unless explicitly authorized. Do not change reward, observations, action shape, action semantics, env dynamics, controller, HARL, baselines, scenario YAML, cooldown tuning, redirect tuning, or env-level lifecycle.
