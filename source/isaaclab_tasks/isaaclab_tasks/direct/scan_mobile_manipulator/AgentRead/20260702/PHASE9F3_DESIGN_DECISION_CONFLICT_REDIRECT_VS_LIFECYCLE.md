# Phase 9F-3 Design Decision: Conflict Redirect vs Active-Task Lifecycle

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-3 is design-only.

No code behavior was changed. No training was run. No playback was run. No broad evaluation was run.

This phase does not change reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, controller behavior, HARL code, baseline solvers, cooldown trigger or mask behavior, scenario YAML behavior, conflict-aware redirect logic, active-task lifecycle logic, or installed `site-packages`.

No commit was made.

## 2. Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2B_ROW_LEVEL_LOGGING_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
```

## 3. Evidence Summary

Phase 9F-1 broad attribution:

| Run | Exact next target already claimed | Nearby distinct next-target conflict | Coverage gain within 20 | Return after cooldown | Cause labels |
| --- | ---: | ---: | ---: | ---: | --- |
| models + budget | 20/30 | 25/30 | 0/30 | 30/30 | A+B+C+D |
| best_model + budget | 0/70 | 50/70 | 25/70 | 65/70 | B |

Phase 9F-2A added row-level direct diagnostic fields for future playback histories:

```text
selected-target conflict fields
same-step claimed/nearby claimed snapshot fields
inter-robot overlap fields
observed pre/post base-segment crossing and near-miss proxy fields
post-step base positions
```

Phase 9F-2B validated schema emission in a five-step playback:

```text
rows = 15
columns = 61
budget_trigger_row_count = 0
schema validation = passed
```

Phase 9F-2C validated trigger-window attribution with the new direct fields:

```text
rows = 897
columns = 61
budget_trigger_row_count = 6
trigger_pairs = r1->36:4, r2->44:2
next_exact_duplicate_direct_count = 4 / 6
next_nearby_selected_target_direct_count = 5 / 6
next_inter_robot_overlap_direct_count = 6 / 6
next_path_crossing_direct_count = 1 / 6
next_path_near_miss_direct_count = 5 / 6
coverage_gain_within_20_count = 0 / 6
return_to_triggered_pair_after_cooldown_count = 6 / 6
```

The Phase 9F-2C direct fields agreed with old reconstructed selected-target proxies:

```text
exact_direct_reconstructed_mismatch_count = 0
nearby_direct_reconstructed_mismatch_count = 0
selected_target_pair_count_direct_reconstructed_mismatch_count = 0
```

Interpretation:

```text
The evidence is now strong enough to justify a small local redirect guardrail experiment.
The evidence is not strong enough to treat a local guardrail as a final solution.
Repeated return-to-triggered-pair remains the clearest sign of a deeper lifecycle or failed-target-state problem.
Path crossing / near-miss evidence should remain diagnostic for now because it is an observed straight base-segment proxy, not a planner-internal path.
```

## 4. Decision Table

| Option | What it targets | Evidence support | Benefits | Risks / exclusions | Phase 9F-3 decision |
| --- | --- | --- | --- | --- | --- |
| A. Minimal claimed-target redirect guardrail | Exact duplicate redirect into a teammate's selected target | Strong for `models + budget`: 20/30 in 9F-1 and 4/6 in 9F-2C. Weak for `best_model + budget`: 0/70. | Low complexity; directly attacks exact duplicate redirects; likely improves the `models/` checkpoint. | Does not solve nearby conflict; does not solve repeated return; cannot catch simultaneous new duplicate choices unless based on an existing claim snapshot. | Useful but insufficient alone. |
| B. Spacing-aware redirect guardrail | Redirect into targets too close to teammate-selected targets | Strong for both runs: 25/30 models and 50/70 best_model in 9F-1; 5/6 in 9F-2C. | Addresses the broader nearby-target conflict; may indirectly reduce overlap and near-miss. | Can over-mask useful alternatives; can create noop pressure; threshold choice matters. | Justified if fail-open and tightly scoped. |
| C. Claimed-target + spacing-aware staged guardrail | Exact duplicates plus nearby selected-target conflict | Strongest fit to the combined evidence. | Covers both `models/` exact duplicate failure and `best_model/` nearby conflict; can be wrapper-local, config-gated, reward/observation/action-shape preserving. | Still mask-only; cannot solve every-step reselection or repeated return; must log suppression and over-mask cases. | Recommended next implementation boundary. |
| D. Path-crossing-aware redirect | Observed base-segment crossing / near-miss proxy | Partial support: 9F-2C saw next-step overlap 6/6, near-miss 5/6, crossing 1/6. | Could reduce geometric motion conflict if proxy is reliable. | Proxy is not planner-internal path; may become brittle or overly conservative; higher implementation risk. | Keep diagnostic-only for now. Do not implement first. |
| E. Active-task lifecycle | Repeated return, every-step reselection, implicit task ownership and failure | Very strong need signal: 30/30 returns in 9F-1 models, 65/70 best_model, 6/6 in 9F-2C. | Addresses the deeper problem: assignment persistence, target ownership, completion, failure, release. | Likely changes action semantics, observations, reward/evaluation, checkpoint compatibility, and training interface. | Design next after local guardrail; do not implement in Phase 9F-4. |

## 5. Recommended Next Implementation Phase

Recommended Phase 9F-4:

```text
Implement a minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail.
Keep it wrapper-local if possible.
Keep reward unchanged.
Keep observations unchanged.
Keep available_actions shape unchanged.
Keep assignment action semantics unchanged.
Keep base environment available_mask semantics unchanged.
Keep noop always available.
Keep default scenarios disabled.
Add diagnostic logging for suppression and over-mask/noop-pressure cases.
Do not implement path-crossing-aware redirect.
Do not implement active-task lifecycle.
```

Recommended Phase 9G-0:

```text
Design active-task lifecycle or explicit failed-target state.
Treat repeated return-to-triggered-pair as a lifecycle design input, not as something the local guardrail is expected to solve.
```

## 6. Explicit Non-Goals

Phase 9F-4 should not:

```text
change reward formulas or reward scales
change actor/shared observations
change available_actions shape
change assignment action semantics
change env dynamics
change controller behavior
change HARL
change baseline solvers
change cooldown trigger criteria
change the existing cooldown mask behavior
change scenario YAML behavior except adding disabled-by-default config keys if explicitly authorized
mutate the base env available_mask
make path-crossing-aware redirect decisions
add planner-internal path logic
add active-task lifecycle
add explicit failed-target state
claim performance improvement without playback validation
```

## 7. Proposed Phase 9F-4 Implementation Boundary

If implemented, the guardrail should apply only in budget/cooldown redirect contexts, not globally.

Recommended scope:

```text
activate only for a robot whose original selected robot-target pair is currently suppressed by budget-aware cooldown, or for a short configurable redirect window immediately after a budget-triggered cooldown event
do not change cooldown trigger or existing pair cooldown mask
do not alter masks for robots that are not in a redirect context
```

Claimed-target exclusion:

```text
exclude target ids currently claimed by teammate robots in the wrapper's previous/current assignment snapshot
use only information available before the current action is selected
do not infer future same-step choices
preserve noop availability
```

Spacing-aware exclusion:

```text
exclude candidate targets whose selected target position is closer than a config-gated threshold to a teammate-claimed target position
derive the initial threshold from existing target conflict diagnostics:
  selected_target_conflict_threshold = 2 * target_conflict_radius + target_conflict_safety_margin
  Phase 9E/9F budget scenario value = 0.85 m
```

Over-mask handling:

```text
if claimed-target + spacing-aware rules would leave no non-noop candidate that was otherwise available, fail open for spacing first and log the event
if exact claimed-target exclusion alone would leave only noop, preserve noop and log an over-mask case rather than mutating base env state
```

Configuration:

```text
default disabled
scenario-config gated
separate toggles for claimed-target and spacing-aware suppression
separate counters for claimed-target suppression, spacing suppression, and over-mask fallback
```

Logging:

```text
claimed_target_redirect_suppressed_count
spacing_redirect_suppressed_count
redirect_guardrail_active_for_robot
redirect_guardrail_context
redirect_guardrail_overmask_non_noop_count
redirect_guardrail_only_noop_remaining
redirect_guardrail_fail_open_reason
redirect_guardrail_threshold
redirect_guardrail_claimed_target_robot_ids
redirect_guardrail_nearby_target_robot_ids
```

These field names are suggestions for a future implementation. Phase 9F-3 does not add them.

## 8. Proposed Future Validation Metrics

Phase 9F-4 or Phase 9F-5 playback validation should report, at minimum:

```text
coverage ratio compared with Phase 9E-4B / Phase 9F-2C reference
coverage AUC
noop_when_available rate
post-trigger exact duplicate next-target conflict
post-trigger nearby selected-target conflict
row-level inter-robot overlap in trigger windows
observed base-segment near-miss/crossing proxy in trigger windows
return-to-triggered-pair after cooldown
coverage gain within 20 steps after redirect
claimed-target guardrail suppression count
spacing-aware guardrail suppression count
over-mask cases where only noop remains available
fail-open cases and reasons
whether direct row-level fields still agree with reconstructed selected-target proxies
```

Validation should include:

```text
one minimal schema/playback check for new logging if new fields are added
one limited trigger-window playback for attribution
no training unless a later phase explicitly authorizes it
no broad sweep until the minimal behavior is understood
```

Expected success criteria for a local guardrail experiment:

```text
post-trigger exact duplicate next-target conflict decreases
post-trigger nearby selected-target conflict decreases
row-level overlap and near-miss do not increase
coverage does not drop meaningfully relative to the Phase 9E-4B / 9F-2C reference
noop_when_available does not increase meaningfully
over-mask / only-noop cases remain rare and visible
return-to-triggered-pair is reported even if not solved
```

## 9. Risks and Failure Modes

Local guardrail risks:

```text
hidden state not represented in policy observations
over-masking useful alternatives
increased noop pressure
coverage loss if spacing threshold is too strict
apparent conflict reduction caused by fewer useful moves
global application accidentally changing normal assignment behavior
masking symptoms of missing active-task lifecycle
```

Evidence limitations:

```text
Phase 9F-2C is one episode, one checkpoint, one limited playback
Phase 9F-1 is broader but old histories lacked direct row-level overlap/path fields
path near-miss/crossing is an observed straight pre/post base-segment proxy
coverage gain is global per step, not proof that a redirected target was completed
```

Mitigations:

```text
keep guardrail budget-redirect scoped
keep it disabled by default
log every suppression and every over-mask fallback
preserve noop and base env available_mask semantics
compare against Phase 9E-4B and Phase 9F-2C reference outputs
do not interpret local guardrail results as final lifecycle evidence
```

## 10. Why Active-Task Lifecycle Is Deferred

Active-task lifecycle is likely important, but it is too large for the immediate next implementation phase.

Reason:

```text
The repeated return evidence is strong, but solving it properly likely requires explicit active/idle robot state, target ownership, completion, failure, timeout, and release semantics.
Those changes likely affect action semantics, observations, reward design, evaluation metrics, training compatibility, and checkpoint comparability.
```

Phase 9F-4 should not sneak lifecycle semantics into a local mask.

Instead:

```text
use Phase 9F-4 as a short-term, reversible guardrail experiment
continue reporting return-to-triggered-pair explicitly
start Phase 9G-0 as a dedicated active-task lifecycle / failed-target-state design phase
```

## 11. Final Recommendation

Phase 9F-3 recommends Option C:

```text
claimed-target + spacing-aware staged guardrail
```

This is justified because:

```text
exact duplicate redirects are confirmed for models + budget
nearby selected-target conflicts are confirmed for both models + budget and best_model + budget
direct 9F-2C fields validate that the attribution can be measured directly
the implementation can be scoped as wrapper-local, config-gated, diagnostic, and reversible
```

This is not the final solution because:

```text
the local guardrail does not solve repeated return-to-triggered-pair
the local guardrail does not create explicit target ownership lifecycle
the local guardrail does not distinguish active task execution from repeated reassignment
```

Recommended phase sequence:

```text
Phase 9F-4:
  Implement the minimal config-gated claimed-target + spacing-aware cooldown-redirect guardrail.
  Add suppression / over-mask diagnostics.
  No reward, observation, action-shape, action-semantics, env, controller, HARL, baseline, cooldown-trigger, or default-scenario behavior changes.

Phase 9F-5:
  Run playback-only validation against Phase 9E-4B / Phase 9F-2C references.
  Report direct row-level trigger-window attribution and over-mask/noop pressure.

Phase 9G-0:
  Design active-task lifecycle or explicit failed-target state.
  Treat repeated return-to-triggered-pair as a first-class lifecycle issue.
```
