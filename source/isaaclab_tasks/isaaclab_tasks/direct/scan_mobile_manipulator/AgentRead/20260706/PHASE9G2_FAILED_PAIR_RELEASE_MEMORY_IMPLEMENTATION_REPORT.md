# Phase 9G-2 Failed-Pair / Release-Memory Implementation Report

Date: 2026-07-06

## Scope And Boundary

Phase 9G-2 implemented a small disabled-by-default wrapper-local failed-pair/release-memory guardrail.

This is not a full active-task lifecycle implementation. It is not env-level `task_status` / `robot_status` lifecycle. It does not mark targets globally failed and never marks a target covered. Completion remains tied to `viewpoints_covered`.

No training was run. No playback was run. No broad evaluation was run.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
```

## Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/test_assignment_failed_pair_memory_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No scenario YAML was changed.

## Config Fields

Defaults are conservative and disabled:

```text
assignment_failed_pair_memory_enabled = False
assignment_failed_pair_memory_duration_steps = 5
assignment_failed_pair_memory_apply_to_action_mask = True
assignment_failed_pair_memory_source = "budget_trigger"
assignment_failed_pair_memory_fail_open = True
assignment_failed_pair_memory_clear_on_coverage = True
assignment_failed_pair_memory_log_diagnostics = True
```

`scenario_config.py` now accepts flattened fields and an optional nested `assignment_failed_pair_memory` block. The wrapper also supplies the same defaults through `getattr(...)`, so default behavior remains unchanged when the fields are absent.

## Memory State

Wrapper-local tensors added:

```text
_assignment_failed_pair_memory_remaining[env, robot, target]
_assignment_failed_pair_memory_trigger_step[env, robot, target]
```

Diagnostics added:

```text
assignment_failed_pair_memory.enabled
assignment_failed_pair_memory.source
assignment_failed_pair_memory.duration_steps
assignment_failed_pair_memory.apply_to_action_mask
assignment_failed_pair_memory.fail_open
assignment_failed_pair_memory.clear_on_coverage
assignment_failed_pair_memory.active_count
assignment_failed_pair_memory.suppressed_count
assignment_failed_pair_memory.suppressed_count_per_robot
assignment_failed_pair_memory.fail_open_count
assignment_failed_pair_memory.fail_open_count_per_robot
assignment_failed_pair_memory.only_noop_remaining_count
assignment_failed_pair_memory.only_noop_remaining_per_robot
assignment_failed_pair_memory.selected_pair_active
assignment_failed_pair_memory.selected_pair_ttl_remaining
assignment_failed_pair_memory.trigger_count
assignment_failed_pair_memory.last_trigger_robot_ids
assignment_failed_pair_memory.last_trigger_target_ids
assignment_failed_pair_memory.last_trigger_reason
```

## Trigger Source

The only trigger source is the existing cooldown budget trigger:

```text
assignment_failed_pair_memory_source = "budget_trigger"
```

When `_update_assignment_cooldown()` detects a budget-triggered robot-target failure, the wrapper records memory for exactly that `(env, robot, target)` pair. No new failure criteria were added. Same-target streak alone does not activate this memory.

## TTL And Clearing

Active memory TTL decrements once per wrapper diagnostic update step. Expired entries clear automatically.

If `assignment_failed_pair_memory_clear_on_coverage` is true, memory entries for covered targets are cleared. Reset clears all memory state for the reset envs.

Memory is temporary release memory, not permanent infeasibility labeling.

## Available-Action Overlay Order

Actual wrapper order:

```text
disabled fast path:
  make_assignment_action_mask(problem, include_noop)

enabled overlay path:
  clone base env problem["available_mask"]
  apply existing cooldown overlay when enabled
  apply existing Phase 9F redirect guardrail overlay when enabled
  apply failed-pair/release-memory overlay when enabled
  append/preserve noop column
  assert shape, nonzero rows, and noop availability
```

The guardrail never mutates the base env `available_mask` in place and never changes `available_actions` shape.

## Fail-Open And Noop Preservation

Noop remains available because the failed-pair memory overlay only suppresses target columns before the existing noop append.

If memory would remove all non-noop target options for a robot and `assignment_failed_pair_memory_fail_open` is true, the wrapper keeps that robot's pre-memory target options and logs a fail-open diagnostic. This avoids memory-induced all-noop pressure.

## Compatibility

Unchanged:

```text
reward formulas and reward scales
actor/shared observation shape and contents
available_actions shape
assignment action id semantics
env dynamics
controller behavior
HARL code
baseline solvers
scenario YAML
installed site-packages
existing cooldown behavior/tuning
Phase 9F redirect guardrail behavior/tuning
```

Default behavior is unchanged when `assignment_failed_pair_memory_enabled = False`.

## Smoke Test Coverage

Added:

```text
scripts/environments/test_assignment_failed_pair_memory_smoke.py
```

Covered cases:

```text
default-disabled identity
enabled suppression
pair-scoped behavior
same target remains available to a teammate
noop preservation
fail-open when memory would remove all non-noop targets
TTL expiry
coverage clear
reset clear
available_actions shape unchanged
base available_mask not mutated in-place
budget-trigger source records robot, target, and reason
existing cooldown/redirect smoke still passes
```

## Validation

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

## Final Recommendation

Phase 9G-3 playback-only validation is justified, but only if explicitly authorized by the user.

Recommended Phase 9G-3 boundary:

```text
playback only
use existing Phase 9F comparison structure
compare default-disabled identity first
then compare enabled failed-pair memory against Phase 9F guardrail/cooldown settings
do not train
do not change reward, observations, action shape, env dynamics, controller, HARL, baselines, scenario YAML, cooldown tuning, or redirect guardrail tuning
```

Primary metrics:

```text
same_owner_returns
teammate_reacquires
coverage_gain_after_release_count
coverage_gain_within_20_count
noop_action_rate
noop_when_available_rate
final_coverage_ratio
coverage_auc
next_exact_duplicate_direct_count
next_nearby_selected_target_direct_count
next_inter_robot_overlap_direct_count
next_path_crossing_direct_count
next_path_near_miss_direct_count
```
