# Phase 9G-0 Active-Task Lifecycle Design Audit

Date: 2026-07-05

## 1. Scope and Boundaries

Phase 9G-0 is a design audit only.

No code behavior was implemented. No training was run. No playback was run. No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, controller behavior, HARL code, baseline solvers, installed `site-packages`, cooldown behavior, redirect guardrail behavior, or scenario behavior were changed.

The audit goal is to decide whether an active-task lifecycle or explicit failed-target-state mechanism can address repeated return-to-triggered-pair and task execution state ambiguity without immediately requiring observation shape changes, action shape changes, action semantic changes, or env-level lifecycle changes.

Conclusion: a useful first phase does not require any immediate observation shape, `available_actions` shape, or assignment action semantic change. The recommended first implementation boundary is diagnostic-only lifecycle reconstruction from existing assignment history.

## 2. Files Inspected

Required handoff and Phase 9F reports:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F6_COMMIT_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
```

Primary source files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

Supplemental files inspected for status vocabulary and diagnostics context:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
```

## 3. Current State/Data Inventory

### 3.1 Env-level assignment problem fields

| Field | Defined / updated | Visible to policy observations | Affects `available_actions` | Env or wrapper | Persistent across steps |
| --- | --- | --- | --- | --- | --- |
| `task_status` | Status constants are defined in `assignment_state.py`. `get_assignment_problem()` builds a tensor in `scan_mobile_manipulator_env.py` by setting every task to `TASK_UNASSIGNED`, then replacing covered tasks with `TASK_COMPLETED`. | Not directly included in base env observations or wrapper assignment extension. Status names are returned in the problem for diagnostics. | No direct effect. `available_mask` uses `viewpoints_covered`, not `task_status`. | Env-level derived snapshot. | No. Recomputed from `viewpoints_covered` each call. |
| `robot_status` | Status constants are defined in `assignment_state.py`. `get_assignment_problem()` currently fills all robots with `ROBOT_IDLE`. | Not directly included in base env observations or wrapper assignment extension. Status names are returned in the problem for diagnostics. | No. | Env-level derived snapshot. | No. Recomputed as all idle each call. |
| `viewpoints_covered` | Env tensor initialized in `scan_mobile_manipulator_env.py`, updated by `_update_scan_progress()` when scan dwell gates are met, reset in `_reset_idx()`. | Yes. Base observations include coverage ratio and nearest-viewpoint masking. Wrapper observations include covered flags per viewpoint and a full covered vector. | Yes. `available_mask = feasible_mask & ~viewpoints_covered`. Also drives done and coverage rewards. | Env-level state. | Yes, until reset. |
| `available_mask` | Derived in `get_assignment_problem()` as `feasible_mask & ~viewpoints_covered`. | Yes in wrapper assignment extension as `available_flag`, but this is the base env mask before cooldown/redirect overlays. | Yes. `make_assignment_action_mask()` appends noop; wrapper may overlay cooldown/guardrail before appending noop. | Env-level derived snapshot consumed by wrapper. | No. Recomputed each call from persistent coverage and feasibility. |
| `feasible_mask` | Derived in `get_assignment_problem()` from `assignment_feasible_mask_base`, which is built from static geometric feasibility and manual overrides. | Yes in wrapper assignment extension as `feasible_flag`; static geometric feasibility is also exposed as `static_geometric_feasible_flag`. | Yes. It is the base for `available_mask`; cooldown trigger checks can require selected feasibility. | Env-level scenario/static state. | Yes as base feasibility; per-step returned mask is a broadcast snapshot. |

Key finding: `task_status` and `robot_status` already have a useful vocabulary, but the live env does not use them as a lifecycle machine. The only persistent task completion state today is `viewpoints_covered`.

### 3.2 Wrapper-level assignment memory

| State | Defined / updated | Visible to policy observations | Affects `available_actions` | Env or wrapper | Persistent across steps |
| --- | --- | --- | --- | --- | --- |
| `_previous_assignment` | Initialized/reset in `_reset_assignment_diagnostics()`. Updated to `assignment.clone()` in `_update_assignment_diagnostics()` after each env step. | Yes. Wrapper observations include `previous_assignment_was_noop`, previous assignment one-hot, same-target streak, repeated counts, and attempt-age context. | Indirectly. Used by same-target streak/cooldown logic, and by the Phase 9F redirect guardrail as a teammate claim snapshot. | Wrapper-level. | Yes, until reset or overwritten by next assignment. |
| `last_assignment` | Public diagnostic cache set in `step()` after decoding the policy action. | No. | No. | Wrapper-level diagnostic cache. | Yes until overwritten. Reset does not appear to clear it explicitly. |
| Assignment diagnostics | `_assignment_step`, per-viewpoint attempted counts, last attempt step, same-target streak, steps since global gain, per-robot completed/repeated/selected counts are initialized/reset in `_reset_assignment_diagnostics()` and updated in `_update_assignment_diagnostics()`. | Partly yes. Attempt counts, attempt age, same-target streak, steps since gain, completed count, repeated count, coverage ratio, and uncovered count are in the wrapper observation extension. | Indirectly. Same-target streak and failed-attempt fields feed cooldown triggers. | Wrapper-level. | Yes, until reset. |

Key finding: `_previous_assignment` is a single-step assignment snapshot. It does not encode ownership, execution, failure, release, timeout, or whether a target is still actively being pursued.

### 3.3 Cooldown, budget, and trigger state

| State | Defined / updated | Visible to policy observations | Affects `available_actions` | Env or wrapper | Persistent across steps |
| --- | --- | --- | --- | --- | --- |
| Cooldown config | Defaults live in `ScanMobileManipulatorEnvCfg`; scenario parsing/validation lives in `scenario_config.py`; wrapper normalizes config in `_build_assignment_cooldown_config()`. | No explicit config visibility in observations. | Yes if enabled and `apply_to_action_mask=True`. | Config consumed by wrapper. | Static per env instance. |
| `_per_robot_target_cooldown_remaining` | Initialized/reset in `_reset_assignment_diagnostics()`. Decremented in `_update_assignment_cooldown()`. Set to duration when a trigger fires. Cleared for covered targets. | Not directly visible in observations. The policy sees only the resulting `available_actions` mask when cooldown masking is enabled. | Yes. `_apply_assignment_cooldown_to_available_mask()` removes active per-robot target pairs. | Wrapper-level. | Yes, until countdown, coverage clear, or reset. |
| `_per_robot_target_failed_attempt_count` | Initialized/reset in `_reset_assignment_diagnostics()`. Incremented for failed attempts in `_update_assignment_cooldown()`. Cleared for covered targets. | No direct observation field. Diagnostics/info only. | Indirectly by triggering cooldown. | Wrapper-level. | Yes, until clear/reset. |
| `_same_target_streak` | Initialized/reset in `_reset_assignment_diagnostics()`. Updated in `_update_assignment_diagnostics()`. | Yes, normalized in observations. Also used in assignment reward decomposition. | Indirectly by cooldown trigger modes. | Wrapper-level. | Yes, until assignment changes/noop/reset. |
| `_budget_attempt_target`, `_budget_attempt_steps`, `_budget_attempt_initial_cost`, `_budget_attempt_expected_steps`, `_budget_attempt_budget_steps` | Initialized/reset in `_reset_assignment_diagnostics()`. Updated by `_update_budget_attempt_tracking()` for contiguous valid pair attempts. Cleared for covered targets and after trigger. | No direct observation field. Diagnostics/info only. | Indirectly by budget trigger and then cooldown/redirect guardrail activation. | Wrapper-level. | Yes, while the same robot-target segment continues. |
| Cooldown diagnostics | `_last_cooldown_*`, `_last_budget_*`, aggregate counts, and `assignment_cooldown` info are populated in `_update_assignment_cooldown()` and `_assignment_cooldown_info()`. Playback reads them for `assignment_history.csv`. | No direct observation field. | No direct effect except the underlying cooldown state. | Wrapper-level diagnostics. | Mostly last-step or aggregate persistent diagnostics. |

Key finding: cooldown can suppress a robot-target pair after a repeated failed attempt, but the state is a countdown mask, not an explicit task lifecycle. It does not remember why a task failed beyond counters and trigger diagnostics, and it intentionally releases the pair after the countdown.

### 3.4 Phase 9F redirect guardrail state

| State | Defined / updated | Visible to policy observations | Affects `available_actions` | Env or wrapper | Persistent across steps |
| --- | --- | --- | --- | --- | --- |
| Redirect guardrail config | Defaults live in `ScanMobileManipulatorEnvCfg`; scenario parsing/validation lives in `scenario_config.py`; wrapper normalizes config in `_build_assignment_redirect_guardrail_config()`. Default is disabled. Only `recent_budget_trigger` context is supported. | No. | Only when explicitly enabled. | Config consumed by wrapper. | Static per env instance. |
| `_assignment_redirect_guardrail_remaining` | Initialized/reset in `_reset_assignment_diagnostics()`. Activated by `_activate_assignment_redirect_guardrail_for_budget_triggers()` when a budget cooldown trigger occurs. Decremented by `_advance_assignment_redirect_guardrail_window_after_action()`. | No. | Yes, when enabled and active, by claimed-target and spacing-aware overlay in `_build_available_actions()`. | Wrapper-level. | Yes, but intentionally short-lived. Default window is one decision. |
| `_assignment_redirect_guardrail_triggered_target` | Initialized/reset with the guardrail state and set to the triggered target. | No. | Not used for candidate suppression in Phase 9F; diagnostic/state context only. | Wrapper-level. | Yes, while remaining window is active. |
| Redirect guardrail diagnostics | `_last_redirect_guardrail_*` and `_last_pre_step_redirect_guardrail_*` store active flags, suppression counts, fail-open reasons, thresholds, and teammate ids. Playback logs them. | No. | No direct effect beyond the mask overlay that produced them. | Wrapper-level diagnostics. | Last-mask / pre-step snapshots. |

Key finding: the guardrail is a local, short-window redirect candidate filter. It is not a persistent ownership, execution, failure, or release model.

### 3.5 Diagnostic scripts

`evaluate_assignment_rl_playback_diagnostics.py` reconstructs per-step reporting from env/wrapper snapshots, including selected availability, covered-before/after, same-target streak, cooldown fields, budget fields, redirect guardrail fields, selected-target conflict, inter-robot overlap, and path crossing/near-miss proxies.

This script does not change policy behavior. Its in-memory `previous_assignment` buffer is only for reporting. That makes it a good place to add Phase 9G-1 diagnostic-only lifecycle reconstruction without touching observations, action masks, reward, env dynamics, controller behavior, HARL, or baseline solvers.

## 4. Why Phase 9F Guardrail Does Not Solve Lifecycle

Phase 9F-5 result to preserve:

```text
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

Reasons the guardrail is insufficient:

1. Claimed-target suppression only affects redirect candidate target selection. It removes exact target ids that were claimed by teammates in `_previous_assignment`; it does not create target ownership, execution state, release state, or failed-pair memory.
2. Spacing-aware suppression only avoids candidates close to teammate-claimed targets. It can reduce nearby selected-target conflicts in the immediate redirect row, but it does not reason about whether the original target is still blocked, impossible, being executed, or should be abandoned.
3. `recent_budget_trigger` is intentionally short. The Phase 9F config uses `window_steps=1`, so the guardrail is scoped to the next decision after a budget trigger. It cannot prevent a later return once cooldown expires.
4. `_previous_assignment` is a snapshot, not ownership. It cannot represent "robot is executing target 36", "target 36 failed for robot 1", "target 36 was released", "target 36 is blocked", or "target 36 timed out".
5. The validation confirms the limit. Return-to-triggered-pair stayed `6/6`, coverage gain within 20 stayed `0/6`, and row-level overlap stayed `6/6`.
6. The guardrail does not change controller behavior or env dynamics. If the robot cannot execute/complete a target, local target redirection does not explain or fix that failure mode.

Interpretation: Phase 9F is promising for immediate exact/nearby redirect conflict mitigation, but repeated return-to-triggered-pair is a lifecycle/failure-memory issue.

## 5. Candidate Active-Task Lifecycle States

The existing `assignment_state.py` vocabulary already has most names needed for a lifecycle, but current live behavior only uses unassigned/completed and idle. A minimal design should separate task state, robot state, and pair state.

| State | Meaning | Entry condition | Exit condition | Belongs to | Should affect `available_actions` | Should be visible in observations | Reward or diagnostics |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `unassigned` | Target is uncovered and not owned by a robot. | Reset; release from ownership; failed/timeout memory expires; target becomes newly available. | Policy assigns a robot; target is completed; target becomes unreachable/blocked. | Task state. | Yes eventually: available to feasible robots. | Eventually yes if env-level lifecycle is trained. Diagnostic-first phase can keep it offline. | Diagnostics first. Reward unchanged in Phase 9G-1/2. |
| `assigned` | A robot-target pair has been selected and ownership is reserved, but execution progress is not yet established. | Non-noop assignment to an unassigned feasible target. | Robot starts moving/executing; reassignment; release; immediate invalid/blocked detection. | Pair state with task owner. | Yes if ownership masks teammates or failed returns. | Eventually yes if hidden ownership affects masks beyond one step. | Diagnostics first. |
| `executing` | Robot is actively pursuing a target and the target remains owned. | Assigned pair persists after one step, or controller/progress evidence indicates movement toward target. | Completed; failed; timeout; release; blocked. | Pair state plus robot state. | Yes if target is reserved from other robots or old owner is expected to continue. | Eventually yes, because hidden executing state changes availability. | Diagnostics first; reward only after a later design phase. |
| `completed` | Target has been covered. | `viewpoints_covered` flips true. | Episode reset only. | Task state. | Already yes through `available_mask`. | Already visible through coverage fields. | Already affects env rewards/dones. |
| `failed` | A robot-target pair has exceeded failure criteria without coverage. | Budget trigger, repeated failed attempts, no progress for configured window, or explicit diagnostic classifier. | Cooldown/failure TTL expires; target released to same or other robots; target marked blocked/unreachable; reset. | Pair state first; optionally task state if all feasible robots fail. | Yes in a later disabled-by-default suppression phase: mask the failed pair for a TTL. | If behavior changes are enabled for training, yes eventually. For playback-only guardrail validation, the mask itself is visible via available actions. | Diagnostics first; no reward change initially. |
| `timeout` | A robot-target pair or target has exceeded a time budget. | Budget attempt steps exceed expected budget plus slack. | Convert to failed, released, or blocked; reset. | Pair state first. | Yes if timeout creates temporary failed-pair memory. | Eventually yes if persistent. | Diagnostics first. |
| `released` | Ownership is intentionally dropped, target becomes available to others or after TTL to same robot. | Failure/timeout; policy noops/switches; coverage by another robot; explicit release rule. | Reassigned; failed-pair TTL expires; target completed; reset. | Pair/task transition state. | Yes if released means "same robot cannot immediately reacquire." | Eventually yes if long-lived. | Diagnostics first. |
| `blocked` | Target or robot-target pair appears geometrically or execution-wise blocked. | Repeated failure across one or more robots, infeasible gate, obstacle/path proxy, controller non-progress. | Manual clear; later feasible evidence; reset; mark unreachable. | Pair state first; task state if all robots blocked. | Yes if all feasible candidates for pair/task should be suppressed. | Eventually yes. | Diagnostics first because blocking evidence is not yet strong enough. |

Recommended minimal first live mechanism, if Phase 9G-1 diagnostics support it:

```text
pair_failed_memory[env, robot, target] with reason, ttl_remaining, source_event
```

This is smaller and safer than immediately making env-level `task_status` and `robot_status` persistent.

## 6. Design Alternatives

### Option A: wrapper-local failed-pair memory only

Implementation scope: small to medium. Add wrapper-local `[env, robot, target]` failed/released memory with TTL, reason, source trigger, fail-open diagnostics, and config disabled by default.

Risk: moderate. It is hidden state unless surfaced in observations, but a disabled-by-default playback guardrail can be evaluated before training.

Compatibility:

```text
existing checkpoints: compatible if disabled by default
observation changes: not needed for initial playback-only validation
available_actions shape changes: not needed
reward changes: not needed
action semantics: unchanged, but availability can be additionally masked when enabled
```

Can solve return-to-triggered-pair: likely yes for the measured pattern, because the same robot-target pair can remain suppressed/released after cooldown.

Can help overlap/near-miss: limited. It may reduce repeated convergence on one failing target, but it does not coordinate paths or same-step choices by itself.

Publishable/explainable: yes as a conservative failed-pair release guardrail if diagnostics show it targets a real failure mode and overmask/noop pressure is reported.

### Option B: wrapper-local active assignment ownership table

Implementation scope: medium. Track `owner_robot`, `owned_target`, age, last progress, release/failure reason, and owner state in the wrapper.

Risk: moderate to high. Hidden ownership can create policy/mask mismatch if used during training without observation exposure.

Compatibility:

```text
existing checkpoints: compatible if disabled by default
observation changes: not strictly needed for playback-only behavior tests, but likely needed before training on persistent ownership
available_actions shape changes: not needed
reward changes: not required initially
action semantics: same discrete target/noop ids, but mask semantics become more stateful
```

Can solve return-to-triggered-pair: yes if ownership/release rules prevent immediate reacquisition after failure.

Can help overlap/near-miss: partly. It can prevent duplicate/nearby ownership across teammates, but does not solve path geometry or same-step simultaneous claims unless ordering or conflict resolution is added.

Publishable/explainable: yes, but only if framed as an ownership model with clear release rules and diagnostics.

### Option C: env-level `task_status` / `robot_status` lifecycle

Implementation scope: high. Make task and robot statuses persistent, update them in reset/step/coverage/failure paths, and decide how statuses feed problem, observations, masks, rewards, and diagnostics.

Risk: high. This is the cleanest semantic model, but it touches core env state and may require retraining once observations expose the state.

Compatibility:

```text
existing checkpoints: compatible only if default behavior preserves old observations/masks
observation changes: likely needed before using lifecycle for training
available_actions shape changes: not needed; statuses can still mask existing target ids
reward changes: not inherently required, but likely tempting and should be deferred
action semantics: can remain target/noop if lifecycle is mask/status only
```

Can solve return-to-triggered-pair: yes, if failed/released/blocked states are explicit and used by availability.

Can help overlap/near-miss: potentially, if ownership and robot moving/scanning states are used to coordinate target reservation and release.

Publishable/explainable: strongest long-term option because lifecycle state lives where task state belongs.

### Option D: hybrid wrapper-local lifecycle first, env-level later

Implementation scope: staged. Start with diagnostic reconstruction, then disabled-by-default wrapper-local failed-pair/release memory, then decide whether env-level lifecycle is justified.

Risk: low to moderate. The early phases avoid changing policy observation shape or default behavior while collecting evidence.

Compatibility:

```text
existing checkpoints: compatible
observation changes: not needed for Phase 9G-1/9G-2 playback-only validation
available_actions shape changes: not needed
reward changes: not needed
action semantics: unchanged
```

Can solve return-to-triggered-pair: likely, if Phase 9G-2 memory suppresses the measured failed pair after cooldown.

Can help overlap/near-miss: possibly as a side effect; not guaranteed.

Publishable/explainable: yes. This is easiest to explain as evidence-driven migration from diagnostics to a minimal local guardrail, with env-level lifecycle only if needed.

### Option E: reward-only penalty for repeated failed return

Implementation scope: small in code, large in validation. It requires reward formula/scale changes and training to know whether the policy learns the desired behavior.

Risk: high for the current goal. It does not fix playback of an existing checkpoint and can create reward hacking or distribution shift.

Compatibility:

```text
existing checkpoints: behavior of old checkpoints unchanged, but new training not comparable
observation changes: not required
available_actions shape changes: not required
reward changes: required
action semantics: unchanged
```

Can solve return-to-triggered-pair: only after training, and not guaranteed.

Can help overlap/near-miss: only indirectly after training.

Publishable/explainable: weaker as the first Phase 9G mechanism because it hides the lifecycle issue inside reward shaping and violates the current no-reward-change boundary.

## 7. Recommended Staged Phase 9G Path

Recommended route: Option D.

```text
Phase 9G-1: diagnostic-only lifecycle reconstruction from existing assignment history
  - Reconstruct pair states such as assigned, executing_proxy, completed, failed_budget, released_after_failure, returned_after_release.
  - Use existing `assignment_history.csv` fields from Phase 9F-2C / 9F-5 first.
  - No env/wrapper behavior change.
  - No observation, action-shape, action-semantics, reward, controller, HARL, or baseline-solver change.

Phase 9G-2: disabled-by-default wrapper-local failed-pair release memory
  - Only if Phase 9G-1 confirms a robust repeated failed-return pattern.
  - Add config-gated memory with TTL, reason, fail-open, no-op preservation, and diagnostics.
  - Preserve `available_actions` shape and default behavior.
  - Do not change rewards or observations in the first behavior experiment.

Phase 9G-3: playback-only validation
  - Compare against Phase 9F-2C disabled reference and Phase 9F-5 redirect guardrail reference.
  - Report return-to-triggered-pair, coverage gain within 20, exact/nearby conflicts, overlap/near-miss, noop pressure, coverage ratio/AUC, overmask/fail-open.
  - No training.

Phase 9G-4: env-level lifecycle design
  - Only if wrapper-local memory is insufficient or hidden-state risks become unacceptable.
  - Promote proven concepts into persistent env-level `task_status`/`robot_status`/pair-state design.
  - Plan observation exposure and retraining explicitly.
```

Why this path: it answers the lifecycle question before adding behavior, keeps current checkpoints usable, and avoids making env-level lifecycle unavoidable before the failure modes are classified.

## 8. First Implementation Boundary

Recommended Phase 9G-1 boundary:

```text
Implement a standalone diagnostic analyzer for lifecycle reconstruction from existing `assignment_history.csv`.
Do not alter env, wrapper behavior, controller, reward, observations, action masks, HARL, or baseline solvers.
Do not run playback unless explicitly authorized.
```

Likely files to change in Phase 9G-1:

```text
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/PHASE9G1_*.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Optional but not required for Phase 9G-1:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
```

Only extend the playback script if future generated histories need lifecycle columns emitted during playback. For first diagnostics, existing Phase 9F histories already contain enough row-level fields to reconstruct approximate lifecycle states offline.

Config fields: not needed for Phase 9G-1.

Diagnostics fields: yes, but only in analyzer outputs, for example:

```text
lifecycle_reconstructed_state
lifecycle_state_reason
active_assignment_age_steps
failed_pair_memory_start_step
failed_pair_memory_ttl_proxy
released_after_budget_trigger
returned_to_failed_pair_after_release
coverage_gain_before_release
coverage_gain_within_20_after_release
same_owner_reacquire_step
teammate_reacquire_step
```

Fake-env or fixture smoke tests: yes. Prefer a tiny CSV fixture or in-memory row list covering:

```text
successful completion
budget-trigger failure
cooldown release
same-pair return
teammate claim
noop row
covered-before row
overlapping trigger windows
```

Playback analyzer changes: not required for the first analyzer-only implementation.

Scenario YAML: not needed for Phase 9G-1.

## 9. Compatibility Risks and Mitigations

| Risk | Assessment | Mitigation |
| --- | --- | --- |
| Observation compatibility | Phase 9G-1 needs no observation changes. Phase 9G-2 can stay playback-only without observation changes, but training on hidden persistent state is risky. | Keep Phase 9G-1 diagnostic-only. If Phase 9G-2 behavior is used for training, design observation exposure explicitly in a later phase. |
| Checkpoint compatibility | Existing checkpoints remain compatible if default behavior is unchanged. | Keep any future behavior disabled by default and preserve action/observation spaces. |
| `available_actions` shape compatibility | No shape change is needed. Existing target ids plus noop are sufficient. | Only mask existing entries; never add lifecycle action ids in Phase 9G. |
| Training distribution shift | Any new suppression changes the action distribution. | Do not train in Phase 9G-1/9G-2. Validate playback first. |
| Hidden state not visible to policy | Wrapper-local failed memory could affect masks without explanatory observations. | Limit first behavior phase to disabled-by-default playback validation; expose state before training if persistent memory is kept. |
| Overmask / noop pressure | Failed-pair memory could suppress too many targets. | Preserve noop, fail open when no non-noop alternatives remain, log overmask and only-noop counts. |
| Interaction with cooldown | Failed memory could duplicate cooldown or fight its release behavior. | Treat cooldown trigger as a source event; keep separate TTL and diagnostics; do not alter existing cooldown trigger/mask behavior in first behavior phase. |
| Interaction with redirect guardrail | Redirect guardrail already overlays local candidate suppression. | Apply any future failed-pair memory in a clearly ordered overlay, disabled by default, with independent diagnostics. Do not tune Phase 9F guardrail. |
| Interaction with `task_status` / `robot_status` | Current statuses are derived snapshots, not persistent lifecycle. | Do not write env-level statuses until Phase 9G-4. Use analyzer state names first. |
| Interaction with coverage update | Completion is currently `viewpoints_covered`; lifecycle must not create false completion. | Use coverage as the only completion source. Failed/released states must never mark a target covered. |
| Row-level overlap / near-miss | Failed-pair memory may not reduce geometric overlap. | Keep overlap/near-miss as validation metrics, not required success criteria for Phase 9G-1. |

## 10. Validation Plan

Phase 9G-1 validation:

```text
py_compile changed analyzer script
run analyzer on a tiny checked-in or generated fixture
optionally run analyzer on existing Phase 9F assignment_history.csv files if available locally, without running playback
git diff --check
```

Do not train. Do not run playback unless explicitly authorized.

Phase 9G-2 validation, if behavior is later implemented:

```text
py_compile changed Python files
fake-env smoke for default-disabled behavior
fake-env smoke for failed-pair suppression, TTL expiry, fail-open, noop preservation, base-mask immutability, and shape preservation
git diff --check
```

Phase 9G-3 playback validation, only if authorized:

```text
compare against Phase 9F-2C disabled reference and Phase 9F-5 redirect guardrail reference
return_to_triggered_pair_after_cooldown_count
coverage_gain_within_20_count
next_exact_duplicate_direct_count
next_nearby_selected_target_direct_count
next_inter_robot_overlap_direct_count
next_path_crossing_direct_count
next_path_near_miss_direct_count
final_coverage_ratio
coverage_auc
noop_when_available_rate
noop_action_rate
overmask_count
fail_open_count
only_noop_remaining_count
```

## 11. Final Recommendation

Proceed with a staged Phase 9G path:

```text
Phase 9G-1: diagnostic-only lifecycle reconstruction from existing histories.
Phase 9G-2: disabled-by-default wrapper-local failed-pair/release memory only if diagnostics support it.
Phase 9G-3: playback-only validation.
Phase 9G-4: env-level lifecycle only if wrapper-local evidence is insufficient or hidden-state risk becomes the limiting issue.
```

Recommended first implementation boundary:

```text
Add an offline lifecycle reconstruction analyzer only.
Do not change env, wrapper behavior, observations, rewards, `available_actions`, assignment action semantics, controller, HARL, baseline solvers, scenario YAML, or installed packages.
```

Stop conditions were not triggered in Phase 9G-0 because a useful diagnostic-first lifecycle phase can be designed without immediate observation shape changes, `available_actions` shape changes, action semantic changes, training, playback, or unavoidable env-level lifecycle implementation.
