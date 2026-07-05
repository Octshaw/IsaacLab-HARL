# Phase 9F-4A Redirect Guardrail Implementation-Boundary Audit

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-4A is an implementation-boundary audit only.

No guardrail was implemented. No code behavior was changed. No training was run. No playback was run. No broad evaluation was run.

This phase does not change reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, controller behavior, HARL code, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, scenario YAML behavior, path-crossing-aware redirect logic, active-task lifecycle logic, or installed `site-packages`.

No commit was made.

## 2. Files Inspected

Documents:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```

Code and config:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9f2c_trigger_windows.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
```

## 3. Evidence to Preserve

Phase 9F-2C direct row-level trigger-window validation:

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

Phase 9F-3 decision:

```text
short-term:
  local claimed-target + spacing-aware cooldown-redirect guardrail

medium-term:
  defer active-task lifecycle or explicit failed-target state to Phase 9G-0
```

## 4. Cooldown Mask Insertion Point

Current wrapper action-mask flow:

```text
AssignmentHarlWrapper.reset()
  gets problem = env.get_assignment_problem()
  calls _build_available_actions(problem)
  returns available_actions to the policy path

AssignmentHarlWrapper.step()
  gets pre_step_problem
  calls _build_available_actions(pre_step_problem)
  decodes already-selected discrete actions
  computes selected_available_mask against the pre-step mask
  steps the base env
  updates assignment diagnostics and cooldown state
  builds next available_actions from post_step_problem
  returns next available_actions to the policy path
```

Relevant code:

```text
assignment_harl_wrapper.py:247-257 reset returns available_actions
assignment_harl_wrapper.py:264-268 step rebuilds pre_step_available_actions before selected_available_mask reporting
assignment_harl_wrapper.py:274-279 step updates diagnostics/cooldown after env.step
assignment_harl_wrapper.py:317-319 step returns next available_actions
```

Available-actions construction:

```text
assignment_harl_wrapper.py:499-537 _build_available_actions()
assignment_rl_interface.py:11-37 make_assignment_action_mask()
```

Cooldown mask behavior:

```text
assignment_harl_wrapper.py:502-503
  if cooldown masking is disabled, use make_assignment_action_mask(problem, include_noop=True)

assignment_harl_wrapper.py:505-520
  if cooldown masking is enabled, read problem["available_mask"], apply cooldown overlay, then convert to float

assignment_harl_wrapper.py:521-529
  append an all-ones noop column

assignment_harl_wrapper.py:530-536
  enforce shape, non-empty rows, and noop availability

assignment_harl_wrapper.py:545-547
  _apply_assignment_cooldown_to_available_mask() returns available_mask & (~cooldown_mask)
```

Cooldown state update:

```text
assignment_harl_wrapper.py:888-1084 _update_assignment_cooldown()
assignment_harl_wrapper.py:906-915 computes active cooldown suppressions from pre_step_problem["available_mask"]
assignment_harl_wrapper.py:940-945 decrements active cooldown counters after selected-pair diagnostics
assignment_harl_wrapper.py:1028-1057 computes budget/streak trigger booleans
assignment_harl_wrapper.py:1070-1079 writes new per-robot-target cooldown state and budget-trigger diagnostics
```

Noop preservation:

```text
Noop id is wrapper.noop_action_id.
Noop is appended as an all-ones final column in _build_available_actions().
_build_available_actions() raises if any action row is all-zero or if noop is not available.
```

Base env mask mutation:

```text
The wrapper does not mutate problem["available_mask"] or the base env's available mask.
It reads problem["available_mask"], converts it to a bool tensor, and returns a filtered available_actions tensor.
The base env constructs available_mask in scan_mobile_manipulator_env.py:1374-1375 from feasible_mask & ~viewpoints_covered.
```

Policy timing:

```text
The policy selects actions using the available_actions returned by the previous reset/step.
The wrapper also recomputes pre_step_available_actions inside step() for selected_available_mask reporting.
New cooldown triggers from a step affect the next returned available_actions, not the already-selected action of that same step.
```

## 5. Available State / Data Inventory

Wrapper-local state:

| Item | Available | Location / notes |
| --- | --- | --- |
| `num_envs`, `num_agents`, `num_viewpoints` | yes | wrapper properties and `_num_*` fields |
| noop id | yes | `wrapper.noop_action_id` |
| previous selected assignment per robot | yes | `_previous_assignment`; updated in `assignment_harl_wrapper.py:876` |
| last assignment | yes | `last_assignment`; set in `assignment_harl_wrapper.py:293` |
| current available-actions tensor | yes | `last_available_actions`; set after reset/step |
| pre-step available-actions tensor | yes | `last_pre_step_available_actions`; set in `assignment_harl_wrapper.py:295` |
| per-robot-target cooldown remaining | yes | `_per_robot_target_cooldown_remaining` |
| last budget-triggered robot rows | yes, one-step diagnostic only | `_last_budget_triggered_by_budget` reset at start of each cooldown update |
| active cooldown budget origin | partial | trigger mode can imply origin for budget modes, but active cooldown tensor does not store origin separately |
| target/viewpoint coordinates | yes via problem | `problem["viewpoint_pos"]` |
| available/feasible target mask | yes via problem | `problem["available_mask"]`, `problem["feasible_mask"]` |

Base env assignment problem:

```text
scan_mobile_manipulator_env.py:1358-1430 get_assignment_problem()
  base_pos
  base_yaw
  scanner_pos
  scanner_quat
  viewpoint_pos
  viewpoint_quat
  viewpoints_covered
  cost_matrix
  static_geometric_feasible_mask
  feasible_mask
  available_mask
  task_status
  robot_status
  inter-robot diagnostic metadata
```

Spacing threshold data:

```text
scan_mobile_manipulator_env.py:1429 adds get_inter_robot_conflict_diagnostics() to the problem
evaluate_assignment_rl_playback_diagnostics.py:452-536 uses viewpoint_pos[..., :2]
selected_target_conflict_threshold = 2 * inter_robot_target_conflict_radius + inter_robot_target_conflict_safety_margin
Phase 9E/9F budget scenario value = 2 * 0.35 + 0.15 = 0.85 m
```

## 6. Redirect-Context Options

| Context definition | Existing state available? | New state needed? | Risk | Wrapper-local? | Audit result |
| --- | --- | --- | --- | --- | --- |
| Robot's originally selected target is currently suppressed by cooldown | No. The masked-out action is not observable after masked policy selection. | Would require unmasked policy action/logit inspection or alternate action selection. | High; risks changing policy/evaluation semantics. | Not cleanly. | Do not use. |
| Robot has any active cooldown suppression in a budget-trigger mode | Mostly. `_per_robot_target_cooldown_remaining > 0` plus `trigger_mode in {"budget", "budget_and_streak"}`. | No for current budget-only scenarios; yes if future mixed-origin cooldowns are allowed. | Medium; may apply to every active cooldown step rather than a narrow redirect window. | Yes. | Acceptable fallback, but not preferred. |
| Robot has a recently budget-triggered pair and is within a short redirect window | `_last_budget_triggered_by_budget` exists for the immediate next returned mask, but not for a multi-step window. | Yes: wrapper-local redirect-window counters and optional triggered-target ids. | Low if disabled by default and only set from budget triggers. | Yes. | Preferred. |
| Robot selects a non-triggered target immediately after budget suppression | Detectable after action selection in playback/history. | Not useful for pre-action mask construction. | Too late to guide action mask. | Diagnostic only. | Use for validation, not masking. |
| Apply guardrail globally to all assignment decisions | No special state needed. | No. | High; changes normal policy behavior and hides lifecycle problem. | Yes but not acceptable. | Do not use. |

Recommended Phase 9F-4B context:

```text
Use a wrapper-local recent budget redirect window.
Set the window when _update_assignment_cooldown() observes budget_trigger for a robot.
Apply the guardrail only while that robot's redirect window counter is positive.
Default window should match or be shorter than the cooldown duration unless explicitly configured.
```

Immediate-next-action-only variant:

```text
If Phase 9F-4B wants the smallest possible behavior surface, set window_steps = 1 by default.
This targets the exact "next non-noop after trigger" failure measured in Phase 9F-1 and Phase 9F-2C.
```

## 7. Claimed-Target Suppression Plan for Phase 9F-4B

Recommended snapshot:

```text
Use _previous_assignment as the teammate claim snapshot.
It represents the most recent executed assignment before the next policy action is selected.
It is already included in observations as previous_assignment_one_hot, so using it creates less hidden state than a new unobserved ownership table.
```

Algorithm sketch:

```text
base_mask = problem["available_mask"].bool()
cooldown_filtered = existing cooldown overlay result
if guardrail disabled:
  return existing behavior

for each env, robot in redirect_context:
  teammate_claimed_targets = _previous_assignment[env, other_robot] where target >= 0
  for each non-noop candidate target:
    suppress if candidate target equals a teammate_claimed_target
  never suppress noop
  do not mutate problem["available_mask"]
```

Important limitations:

```text
This cannot prevent two robots from simultaneously choosing the same new target if neither had claimed it in the previous assignment.
Avoiding same-step simultaneous claims would require sequential action resolution, policy logits, or action semantics changes. Phase 9F-4B should not do that.
```

Fail-open behavior:

```text
If claimed-target suppression would leave no non-noop target after existing cooldown filtering, preserve noop and log the over-mask.
Whether to fail open claimed-target suppression should be config-gated. The safest first implementation can fail open claimed-target only when it would leave no non-noop alternatives.
```

## 8. Spacing-Aware Suppression Plan for Phase 9F-4B

Coordinate source:

```text
problem["viewpoint_pos"] with XY distance, matching existing selected-target conflict diagnostics.
```

Threshold:

```text
Default to selected_target_conflict_threshold:
  2 * inter_robot_target_conflict_radius + inter_robot_target_conflict_safety_margin

For the Phase 9E/9F budget scenario:
  2 * 0.35 + 0.15 = 0.85 m
```

Algorithm sketch:

```text
for each env, robot in redirect_context:
  teammate_claimed_targets = _previous_assignment[env, other_robot] where target >= 0
  teammate_positions = viewpoint_pos[env, teammate_claimed_targets, :2]
  for each non-noop candidate target still available after cooldown and claimed-target overlay:
    candidate_xy = viewpoint_pos[env, candidate_target, :2]
    suppress if min distance to teammate_positions < threshold
  never suppress noop
```

Fail-open order:

```text
Apply existing cooldown first.
Apply claimed-target suppression second.
Apply spacing suppression third.
If spacing leaves no non-noop alternatives, fail open spacing first and log fail_open_reason = spacing_overmask.
If claimed-target suppression also leaves no non-noop alternatives, either fail open claimed-target or preserve only noop based on explicit config. The recommended first setting is fail_open_claimed=true to avoid changing noop pressure too much during the diagnostic experiment.
```

Separate accounting:

```text
claimed_target_redirect_suppressed_count should count exact target-id suppressions.
spacing_redirect_suppressed_count should count target-distance suppressions after excluding already claimed-target suppressions.
This prevents double-counting exact duplicates as spacing suppressions.
```

## 9. Proposed Config Keys

Do not modify scenario YAMLs in Phase 9F-4A.

Recommended future config shape:

```yaml
assignment_redirect_guardrail:
  enabled: false
  apply_context: recent_budget_trigger
  window_steps: 1
  claimed_target_enabled: true
  spacing_enabled: true
  spacing_threshold: null
  fail_open_spacing: true
  fail_open_claimed: true
  log_diagnostics: true
```

Flattened env cfg attrs should follow the existing scenario-config pattern:

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

Where to add them in Phase 9F-4B:

```text
scenario_config.py:
  add SUPPORTED_ASSIGNMENT_REDIRECT_GUARDRAIL_CONTEXTS
  add ASSIGNMENT_REDIRECT_GUARDRAIL_SCENARIO_ATTRS
  include them in ENV_CFG_SCENARIO_ATTRS
  parse a new assignment_redirect_guardrail mapping in smoke_defaults_from_config()
  apply via apply_scenario_config_to_env_cfg()
  validate with a new _validate_assignment_redirect_guardrail_metadata/args/values path

assignment_harl_wrapper.py:
  add _build_assignment_redirect_guardrail_config() with disabled defaults
```

Default behavior:

```text
enabled = false
apply_context = recent_budget_trigger
window_steps = 1
claimed_target_enabled = true
spacing_enabled = true
spacing_threshold = None, meaning derive from problem diagnostics or cfg target-conflict fields
fail_open_spacing = true
fail_open_claimed = true
log_diagnostics = true
```

## 10. Proposed Diagnostics

Wrapper debug/info fields:

```text
redirect_guardrail_enabled
redirect_guardrail_active_count
redirect_guardrail_claimed_suppressed_count
redirect_guardrail_spacing_suppressed_count
redirect_guardrail_overmask_count
redirect_guardrail_only_noop_remaining_count
redirect_guardrail_fail_open_count
redirect_guardrail_threshold
```

Per-robot playback `assignment_history.csv` fields:

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

Recommended placement:

```text
assignment_harl_wrapper.py:
  maintain wrapper-local tensors/counters and expose an assignment_redirect_guardrail info block, parallel to assignment_cooldown

evaluate_assignment_rl_playback_diagnostics.py:
  extend ASSIGNMENT_HISTORY_FIELDS and _append_assignment_history() to copy per-robot diagnostics
  optionally extend summary/per-episode outputs with aggregate suppression and over-mask rates

analyze_phase9f2c_trigger_windows.py or a Phase 9F-5 analyzer:
  validate presence/parseability of new guardrail fields and relate them to trigger-window attribution
```

## 11. Main Implementation Risks

| Risk | Mitigation |
| --- | --- |
| Guardrail accidentally becomes global | Apply only when a per-robot redirect-window state is active. Default disabled. |
| Hidden state not in observations | Use `_previous_assignment`, which is already represented in observations; log redirect-context state. Keep experiment diagnostic. |
| Over-masking and noop pressure | Fail open spacing first, optionally claimed-target second; count only-noop and fail-open cases. |
| Existing checkpoint behavior changes too much | Window default `1`; apply only after budget triggers; keep default scenarios disabled. |
| Threshold sensitivity | Default to validated 0.85 m derived from existing diagnostics; expose config override. |
| Simultaneous same-step claim ambiguity | Use previous assignment snapshot only; document that same-step new duplicate choices are not solved. |
| Interaction with existing cooldown pair mask | Do not modify `_apply_assignment_cooldown_to_available_mask()`; apply guardrail as a separate overlay after cooldown. |
| Interpreting local guardrail as lifecycle solution | Keep return-to-triggered-pair metrics in validation; schedule Phase 9G-0 lifecycle design. |

## 12. Recommended Phase 9F-4B Implementation Sequence

If authorized, implement in this order:

```text
1. Add disabled-by-default redirect-guardrail config fields in scenario_config.py.
2. Add AssignmentHarlWrapper _assignment_redirect_guardrail_config with disabled defaults.
3. Add wrapper-local redirect-window state:
     _assignment_redirect_guardrail_remaining: [num_envs, num_agents]
     optional _assignment_redirect_guardrail_triggered_target: [num_envs, num_agents]
   Reset it in _reset_assignment_diagnostics().
4. In _update_assignment_cooldown(), when budget_trigger is true, set redirect-window state.
   Do not change cooldown trigger logic or cooldown mask behavior.
5. Add a separate _apply_assignment_redirect_guardrail_to_available_mask() called after the existing cooldown overlay in _build_available_actions().
6. Compute claimed-target suppression from _previous_assignment teammate targets.
7. Compute spacing suppression from problem["viewpoint_pos"][..., :2] and the derived/configured threshold.
8. Apply fail-open rules:
     fail open spacing first
     fail open claimed-target only if configured or if the row would otherwise have no non-noop targets
     always preserve noop
9. Add wrapper diagnostics and playback history fields.
10. Add or extend a fake-env smoke test similar to test_assignment_cooldown_mask_smoke.py.
11. Run py_compile on changed Python files and git diff --check.
```

Recommended first implementation context:

```text
apply_context = recent_budget_trigger
window_steps = 1
claimed_target_enabled = true
spacing_enabled = true
fail_open_spacing = true
fail_open_claimed = true
```

Rationale:

```text
This targets the measured "next target after budget trigger" failure with the smallest behavior surface.
It avoids global masking and avoids pretending to solve active-task lifecycle.
```

## 13. Recommended Phase 9F-5 Validation Plan

Playback-only validation metrics after Phase 9F-4B:

```text
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

Suggested validation shape:

```text
one minimal schema playback if new history fields are added
one limited trigger-window playback, using the same checkpoint/scenario family as Phase 9F-2C
no training
no broad sweep until the minimal behavior is understood
```

Compare against:

```text
Phase 9E-4B broader reference
Phase 9F-2C one-episode direct-field reference
```

## 14. Final Recommendation

Phase 9F-4B can safely implement a wrapper-local claimed-target + spacing-aware redirect guardrail if it stays inside this boundary:

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

No stop-condition blocker was found. The implementation can remain wrapper-local and does not require observation, action-shape, assignment-action-semantics, env, controller, HARL, reward, baseline, or installed-package changes if the boundary above is followed.
