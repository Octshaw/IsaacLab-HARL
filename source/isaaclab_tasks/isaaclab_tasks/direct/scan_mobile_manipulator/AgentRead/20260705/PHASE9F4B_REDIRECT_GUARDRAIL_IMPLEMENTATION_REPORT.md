# Phase 9F-4B Redirect Guardrail Implementation Report

Date: 2026-07-05

Note: this report is stored under `AgentRead/20260705/` to match the current-date folder rule in `AGENTS.md`.

## 1. Scope and Boundaries

Phase 9F-4B implemented the minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail recommended by Phase 9F-3 and bounded by Phase 9F-4A.

No training was run. No playback was run. No broad evaluation was run. No commit was made.

The implementation does not change reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, default scenario YAML behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages`.

## 2. Files Changed

Python implementation and smoke coverage:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

Documentation and handoff:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## 3. Config Fields Added

Scenario/default config support was added for:

```text
assignment_redirect_guardrail_enabled
assignment_redirect_guardrail_apply_context
assignment_redirect_guardrail_window_steps
assignment_redirect_guardrail_claimed_target_enabled
assignment_redirect_guardrail_spacing_enabled
assignment_redirect_guardrail_spacing_threshold
assignment_redirect_guardrail_fail_open_spacing
assignment_redirect_guardrail_fail_open_claimed
assignment_redirect_guardrail_log_diagnostics
```

Defaults keep behavior disabled:

```text
enabled = false
apply_context = recent_budget_trigger
window_steps = 1
claimed_target_enabled = true
spacing_enabled = true
spacing_threshold = None
fail_open_spacing = true
fail_open_claimed = true
log_diagnostics = true
```

Only `recent_budget_trigger` is supported. Unsupported contexts fail validation clearly.

No default scenario YAML was modified or enabled.

## 4. Wrapper State Added

`AssignmentHarlWrapper` now keeps wrapper-local state:

```text
_assignment_redirect_guardrail_remaining: [num_envs, num_agents]
_assignment_redirect_guardrail_triggered_target: [num_envs, num_agents]
```

These are reset with assignment diagnostics. They are not part of observations, not part of env state, and not consumed by policy/training.

## 5. Insertion Point

The new guardrail overlay is applied inside:

```text
AssignmentHarlWrapper._build_available_actions()
```

Order:

```text
1. problem["available_mask"]
2. existing cooldown overlay via _apply_assignment_cooldown_to_available_mask()
3. new _apply_assignment_redirect_guardrail_to_available_mask()
4. append noop
5. existing shape / all-zero / noop checks
```

`_apply_assignment_cooldown_to_available_mask()` was not modified. The base env `available_mask` is cloned before filtering and is not mutated.

## 6. Claimed-Target Suppression

When the guardrail is enabled and a robot has an active recent budget-trigger redirect window:

```text
teammate claims are read from _previous_assignment
negative/noop/invalid targets are ignored
candidate targets exactly matching teammate claimed targets are suppressed
robots without active redirect-window state are not affected
same-step simultaneous new claims are not solved
```

Suppression counts and responsible teammate robot ids are logged.

## 7. Spacing-Aware Suppression

Spacing uses:

```text
problem["viewpoint_pos"][..., :2]
```

If `assignment_redirect_guardrail_spacing_threshold` is `None`, the threshold is derived as:

```text
2 * inter_robot_target_conflict_radius + inter_robot_target_conflict_safety_margin
```

For the Phase 9E/9F budget scenario this resolves to:

```text
2 * 0.35 + 0.15 = 0.85 m
```

Spacing suppression is applied after claimed-target suppression and does not double-count exact claimed targets as spacing suppressions.

## 8. Fail-Open Behavior

Mask order:

```text
base available_mask
existing cooldown overlay
claimed-target suppression
spacing-aware suppression
```

Fail-open behavior:

```text
spacing over-mask fails open first by default and logs spacing_overmask
claimed-target over-mask fails open by default and logs claimed_overmask
noop is never removed
only-noop remaining is logged if target columns become empty
actual suppression counts count actions that remain suppressed after fail-open
over-mask counts record would-have-suppressed target counts
```

## 9. Diagnostics Added

Wrapper info now includes:

```text
assignment_redirect_guardrail.enabled
assignment_redirect_guardrail.context
assignment_redirect_guardrail.active_count
assignment_redirect_guardrail.claimed_suppressed_count
assignment_redirect_guardrail.spacing_suppressed_count
assignment_redirect_guardrail.overmask_count
assignment_redirect_guardrail.only_noop_remaining_count
assignment_redirect_guardrail.fail_open_count
assignment_redirect_guardrail.threshold
```

Future playback `assignment_history.csv` rows now include:

```text
redirect_guardrail_active_for_robot
redirect_guardrail_context
claimed_target_redirect_suppressed_count
spacing_redirect_suppressed_count
redirect_guardrail_overmask_non_noop_count
redirect_guardrail_only_noop_remaining
redirect_guardrail_fail_open_reason
redirect_guardrail_threshold
redirect_guardrail_claimed_target_robot_ids
redirect_guardrail_nearby_target_robot_ids
```

List-like fields use the existing JSON serialization path.

## 10. Smoke Test Behavior

`scripts/environments/test_assignment_cooldown_mask_smoke.py` was extended to verify:

```text
default disabled guardrail matches baseline available_actions
noop remains available
claimed-target suppression works in an active redirect window
spacing suppression works in an active redirect window
robots without active redirect windows are not affected
spacing over-mask fails open
claimed over-mask fails open
budget trigger activates a one-decision redirect window
the redirect window decrements after the next action is consumed
base problem available_mask is not mutated
available_actions shape remains [num_envs, num_agents, num_viewpoints + 1]
actor/shared observation shapes remain unchanged in the fake-env smoke
```

## 11. Validation

Commands run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_cooldown_mask_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_cooldown_mask_smoke.py
git diff --check
```

Results:

```text
py_compile: passed for all changed Python files
fake-env smoke: passed
git diff --check: passed, with LF-to-CRLF working-copy warnings only
```

## 12. Known Limitations

```text
same-step simultaneous new claims are not solved
path-crossing-aware redirect is not implemented
active-task lifecycle is not implemented
return-to-triggered-pair is not expected to be solved by this local guardrail
performance is not claimed until playback validation
guardrail is disabled unless a future scenario/config explicitly enables it
```

## 13. Recommended Phase 9F-5 Validation Plan

Phase 9F-5 should be playback-only if authorized.

Recommended metrics:

```text
schema presence and parseability for the new guardrail columns
post-trigger exact duplicate next-target conflict
post-trigger nearby selected-target conflict
row-level inter-robot overlap
observed base-segment near-miss/crossing proxy
coverage ratio and coverage AUC
noop_when_available
return-to-triggered-pair after cooldown
coverage gain within 20 steps
claimed-target suppression counts
spacing-aware suppression counts
fail-open counts and reasons
over-mask / only-noop cases
direct row-level field agreement with reconstructed selected-target proxies
```

Do not train in Phase 9F-5. Do not broaden into performance claims until the guardrail behavior is understood.
