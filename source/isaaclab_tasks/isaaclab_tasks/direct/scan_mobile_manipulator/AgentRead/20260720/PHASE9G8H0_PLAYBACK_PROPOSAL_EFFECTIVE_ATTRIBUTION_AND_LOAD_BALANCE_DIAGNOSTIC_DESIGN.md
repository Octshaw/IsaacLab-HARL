# Phase 9G-8H-0: Playback Proposal-Effective Attribution and Load-Balance Diagnostic Design

Date: 2026-07-20

## 1. Classification

`DIAGNOSTIC-DESIGN-READY`

Both decoded proposals and effective assignments are already available without changing assignment behavior. Resolver events have a single existing drain chain and are exposed to playback as cloned step payloads. A playback-only, default-off collector can join those values with immutable pre/post physical snapshots, distinguish idle noop from Contract-C continuation, attribute resolver rejection, and summarize per-robot work distribution.

Phase 9G-8H-1 does not need a resolver, wrapper-state-machine, observation, mask, reward, controller, checkpoint, or training change.

## 2. Scope And Accepted Evidence

Accepted checkpoint and playback context:

```text
checkpoint parent:
  assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh

checkpoint child:
  final models generation 2

playback:
  lifecycle_contract_c
  E = 1
  M = 3
  N = 50
  max_steps = 300
  seed = 1
```

Accepted visual and console observations:

- One robot appeared motionless for almost all playback.
- One robot sometimes remained near a target before changing target.
- Robots no longer appeared to crowd onto one exact target.
- Displayed effective rows included values such as `[-1, 17, 28]`.
- Displayed duplicate count remained zero in the observed trajectory.
- Some robot rows exposed many available raw target ids while the displayed effective assignment was noop.

These observations establish a question, not a cause. In particular, many available ids plus an effective noop does not distinguish a policy noop from a resolver rejection. Low motion also does not distinguish idle state from an executing active target whose controller command is zero.

## 3. Files Inspected

Read-first documents:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
AgentRead/20260708/PHASE9G7D_DEFAULT_OFF_RESOLVER_RUNTIME_ADAPTER_INTEGRATION_REPORT.md
AgentRead/20260710/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md
```

Runtime and playback source:

```text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Relevant static tests:

```text
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

No script was executed and no checkpoint was loaded during this audit.

## 4. Current Playback Data Flow

### 4.1 Exact call sequence

For decision step `t`, `play_assignment.py` currently performs:

```text
actor.act(..., available_actions_t, deterministic=True)
  -> action [E,1] for each robot
  -> packed actions [E,M,1]

actor.evaluate_actions(..., action, available_actions_t)
  -> action_log_prob
  -> selected_action_probability = exp(action_log_prob) [E,M]

playback pre-step diagnostics
  -> raw_action_id = actions[...,0].long() [E,M]
  -> selected availability and selected distance use raw action ids

AssignmentHarlWrapper.step(actions)
  -> pre_step_problem = env.get_assignment_problem()
  -> pre_step_available_actions = wrapper._build_available_actions(...)
  -> decode_actions(actions)
  -> assignment_proposal [E,M], raw noop N becomes decoded noop -1
  -> resolver_runtime.resolve_pre_step(problem, assignment_proposal)
  -> effective_assignment [E,M]
  -> assignment_to_env_actions(effective_assignment)
  -> viewpoint_assignment_to_actions(env, effective_assignment)
  -> controller action dict, one [E,9] float tensor per robot
  -> env.step(controller actions)
  -> post_step_problem
  -> wrapper diagnostics/reward use effective_assignment
  -> budget failure handoff uses effective_assignment
  -> resolver_runtime.observe_post_step(...)
  -> resolver completion, budget release, and done-reset updates
  -> wrapper drains adapter event batch once
  -> wrapper stores cloned lifecycle-resolution payload
  -> next actor/shared/mask decision snapshot

playback after wrapper.step
  -> reads wrapper.last_assignment
  -> prints aggregate step line
```

### 4.2 Value inventory

| Value | Current symbol and owner | Shape / dtype | Noop | Timing | Accessible to `play_assignment.py` | Printed now | Written now |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Policy action tensor | `actions`, playback | `[E,M,1]`, packing tensor normally float32 | raw id `N` | After actor sampling, before wrapper step | Yes | No | No |
| Raw discrete id | `actions[...,0].long()`, playback helper | `[E,M]`, long | raw id `N` | Pre-step | Yes | Only indirectly through selected diagnostics | No |
| Selected action probability | `exp(action_log_prob)`, playback | `[E,M]`, float32 | probability of raw id `N` when selected | Pre-step | Yes | Yes | No |
| Decoded proposal | `assignment_proposal`, wrapper | `[E,M]`, long | `-1` | Immediately before resolver pre-step | Yes after step through `get_last_assignment_lifecycle_resolution()` and `last_assignment_proposal` | No | Resolver event/row files only when resolver logging is separately enabled |
| Active/owner state before | resolver snapshot captured inside runtime adapter | active `[E,M]`, owner `[E,N]`, long | `-1` sentinel | Before resolver pre-step mutation | Not directly exposed in the current wrapper payload | No | Environment-level resolver row CSV when logging is enabled |
| Effective assignment | `effective_assignment`, wrapper/runtime result | `[E,M]`, long | `-1` | After resolver pre-step, before controller | Yes after step through lifecycle payload and `last_effective_assignment` | Yes as `assignment=[...]` | Resolver files only when separately enabled |
| Controller input assignment | argument to `assignment_to_env_actions()` | `[E,M]`, long | `-1` | Immediately after resolver | Equal by construction to effective assignment | Printed only under the effective alias | No independent assignment file |
| Controller command | `last_env_actions`, wrapper | dict of robot name to `[E,9]` float32 | decoded noop or invalid physical target produces a zero 9D command | Before environment step | Yes after step | No | No |
| Resolver events | resolver -> runtime adapter -> wrapper payload | list of JSON-safe dicts | Event dependent | Pre events before `env.step`; post events after `env.step`; reset after post events | Yes after step via cloned payload | No | JSONL only when resolver logging is enabled |
| Active/owner/pair state after | payload `resolver_snapshot` | active `[E,M]`, owner `[E,N]`, pair `[E,M,N]` | canonical sentinels | After completion, budget release, and done reset | Yes | No | Resolver row/summary when logging is enabled |
| Post physical state | `env.get_assignment_problem()` | tensor mapping | n/a | After wrapper step; done envs may already be reset | Yes | Coverage subset only | Existing playback diagnostics files, not `play_assignment.py` |

### 4.3 Meaning of the current `assignment=[...]` line

The current display is unambiguous in source:

```python
assignment = wrapper.last_assignment
```

and the wrapper assigns:

```python
self.last_assignment = effective_assignment
```

Therefore:

```text
current play_assignment.py assignment=[...]
  = effective_assignment
  = assignment passed into assignment_to_env_actions()
  = high-level controller input assignment
```

It is not the raw action id and not the decoded actor proposal.

The same console line currently mixes semantics:

```text
assignment                      -> effective/controller assignment
selected_available              -> raw selected action against pre-step mask
selected_action_prob            -> raw selected action probability
distance_to_selected_viewpoint  -> raw selected target distance
```

This mixture is the main reason the existing console cannot answer the motionless-robot question.

### 4.4 Current playback diagnostics script

`evaluate_assignment_rl_playback_diagnostics.py` already writes detailed assignment and motion records, but its `assignment_history.csv` receives the decoded proposal as `assignment`, while aggregate buffers use the effective assignment after resolver integration. It does not join the wrapper's resolver flags/events into one per-robot attribution row and does not record selected action probability. It is reusable as a source of output and pre-reset-capture patterns, but it is not the requested attribution diagnostic.

## 5. Existing Resolver Accessors And Event Ownership

### 5.1 Reusable state and results

| Existing item | Before step | After step | Read mutates state? | Current playback access | Decision |
| --- | --- | --- | --- | --- | --- |
| `assignment_proposal` | Created inside wrapper | Cloned into wrapper payload | No through accessor | Yes after step | Reuse |
| `effective_assignment` | Created by resolver pre-step | Cloned into wrapper payload | No through accessor | Yes after step | Reuse |
| Pre-result booleans and rejection code | Created before env step | Cloned into payload | No | Yes after step | Reuse |
| Post completed/released/reason tensors | Not yet available | Cloned into payload | No | Yes after step | Reuse |
| `resolver_snapshot` | Runtime adapter has a pre snapshot internally | Payload contains post/reset snapshot | Snapshot is clone-based | Post snapshot accessible | Reuse post state; reconstruct validated pre state from prior post state |
| `active_target_id` | Runtime adapter captures internally | Payload post snapshot | No | Post state only | Maintain collector state across rows |
| `task_owner_robot_id` | Runtime adapter captures internally | Payload post snapshot | No | Post state only | Maintain collector state across rows |
| `pair_state` | Resolver owns it | Payload post snapshot | No | Post state only | Maintain collector state across rows |
| Resolver event JSONL | Written by adapter if enabled | Complete raw event stream | Reading file is nonmutating | Not used by current console | Optional cross-check, not required input |
| Resolver environment row CSV | Written after post-step | Array-valued per environment | Reading file is nonmutating | Not used by current console | Insufficient as joined per-robot source |
| Resolver summary | Finalize-time counts | Global only | Finalize is idempotent | Wrapper can finalize | Retain as independent resolver summary |
| Passive lifecycle logger | Separate proxy state/events | Separate proxy files | Its adapter drains only its own logger | Optional in playback diagnostics script | Never use as authoritative resolver attribution |

### 5.2 Frozen event-draining owner

There are two deliberate layers in the current implementation:

```text
1. AssignmentLifecycleResolverRuntimeAdapter._drain_resolver_events()
   is the only owner that calls AssignmentLifecycleResolver.pop_events().

2. AssignmentHarlWrapper.step()
   is the only runtime owner that calls resolver_runtime.pop_events().
   It copies that batch into _last_assignment_lifecycle_resolution.
```

Frozen 9G-8H design:

```text
the playback attribution collector consumes only
wrapper.get_last_assignment_lifecycle_resolution()

the collector never calls resolver.pop_events()
the collector never calls resolver_runtime.pop_events()
the collector never drains the passive logger
```

All payload tensors and nested values are clone-based through the wrapper accessor. The collector must clone/normalize inputs again at its boundary and never retain mutable environment aliases.

### 5.3 Reset and step alignment finding

Current initial `wrapper.reset()` calls `resolver_runtime.reset_envs()` but does not drain the adapter event buffer. Consequently, initial reset events can appear at the front of the first subsequent step payload. During a done step, completion/budget events are emitted before per-robot reset events in the same payload.

The collector will use playback-owned `episode_id`, 1-based `decision_step`, event order, and the one-payload-per-wrapper-step boundary:

- Leading reset events after an explicit playback reset are stored as episode-boundary events and not treated as the first policy decision's cause.
- Done-step reset events are attached to that same decision row with `reset=true`.
- Completion and budget release remain attached to the decision that just executed.
- The full event list is retained even when one primary label is selected.

Existing resolver JSONL/CSV cannot be the sole join source because:

- Wrapper calls do not supply playback episode ids to the runtime adapter, so its episode ids remain the adapter default.
- Resolver event `step` is the resolver pre/post step value, while runtime row `step` is read after the resolver increments or resets its counter.
- A done reset sets resolver step back to zero before the environment-level row is written.
- Initial reset and first pre-step events can share event step zero.
- Raw action id, selected probability, controller command norm, physical motion, and per-robot joined attribution are absent.

The existing files remain authoritative raw resolver evidence, but they are not sufficient alone for deterministic playback attribution.

## 6. Hypothesis Matrix

| Hypothesis | Exact row signature | Primary attribution | Work/idle accounting |
| --- | --- | --- | --- |
| H1 policy idle noop | proposal `-1`, active before `-1`, effective `-1`, `noop_idle` | `noop_idle` | Idle |
| H2 Contract-C noop continuation | proposal `-1`, active before `j`, effective `j`, `attempt_continued_noop_contract_c` | `attempt_continued_noop_contract_c` unless a higher-priority post event occurs | Executing, never idle |
| H3 exact-target conflict loss | proposal `j`, active before `-1`, effective `-1`, `claim_lost`; global conflict event names winner | `claim_lost` | Idle for this executed step; proposal attempted work |
| H4 teammate-owned target rejection | proposal `j`, owner before is teammate, effective `-1`, `owned_target_rejected` | `owned_target_rejected` | Idle if proposer was idle |
| H5 same-robot failed-pair rejection | proposal `j`, pair state failed/released, effective `-1`, `failed_pair_reclaim_rejected` | `failed_pair_reclaim_rejected` | Idle if proposer was idle |
| H6 covered target rejection | proposal `j`, covered before true, effective `-1`, `covered_target_rejected` | `covered_target_rejected` | Idle if proposer was idle |
| H6b unavailable target rejection | proposal `j`, physical availability false, effective `-1`, `unavailable_target_rejected` | `unavailable_target_rejected` | Idle if proposer was idle |
| H7 executing switch rejection | proposal `k`, active before `j`, effective `j`, `switch_rejected_executing` | `switch_rejected_executing` unless a higher-priority post event occurs | Executing, never idle |
| H8 active target completed | active/effective `j`, post completion clears active target, `target_completed` | `target_completed` unless post reset has higher priority | Executing for this step; idle for next decision |
| H8b budget release | active/effective `j`, budget and release events, active after `-1` | `release_budget_failure` | Executing for this step; idle for next decision |
| H9 active target infeasible deferred | active/effective remains `j`, `active_target_infeasible_deferred`; controller command may be zero | `active_target_infeasible_deferred` | Resolver-executing even if physical motion is zero |

The table deliberately separates `effective idle` from `physical motion`. H2, H7, H8, and H9 are executing rows even if the base remains still.

## 7. Architecture Options

| Option | Attribution completeness | Aggregation | Event-drain risk | Timing risk | Default-off isolation | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| A. Console extension only | Medium | Poor | High if it reads adapter directly | Medium | Good | Reject as sole design |
| B. Existing resolver JSONL plus offline join | Medium | Good | Low | High because current ids/steps are insufficient | Good | Retain only as optional cross-check |
| C. Playback-only joined collector fed immutable copies | High | High | None when it consumes wrapper payload | Low with explicit decision ids and reset handling | Strong | Selected |

### 7.1 Selected minimal combination

Select Option C with reuse from Option B:

```text
play_assignment.py
  owns CLI, actor raw actions/probabilities, pre/post physical snapshots,
  decision ids, and optional compact printing

wrapper-owned lifecycle resolution payload
  remains the authoritative copied proposal/effective/pre-result/post-result/event source

new project-local pure playback attribution collector
  joins copied values into per-robot rows and derived summaries

existing resolver JSONL/summary
  remains optional independent raw lifecycle evidence when separately enabled
```

Recommended pure diagnostics module for Phase 9G-8H-1:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
assignment_playback_attribution_diagnostics.py
```

Recommended fake regression:

```text
scripts/environments/test_assignment_playback_attribution_diagnostics.py
```

The collector must have no resolver reference and no environment command method. Its update API accepts immutable/copy-owned values only.

### 7.2 Playback-only feasibility

Implementation can remain playback-only. No wrapper change is required:

- After explicit reset, canonical resolver reset state is known and asserted as all idle, unowned, and pair-none.
- For each later decision, pre active/owner/pair state equals the previous payload's post/reset `resolver_snapshot`.
- Current-step proposal/effective/pre flags/post flags/events come from the cloned wrapper payload.
- Pre physical masks and poses are captured by playback before `wrapper.step()`.
- Post physical values are captured by playback after `wrapper.step()`.

For done environments, automatic reset can erase final poses and coverage before the caller reads them. If exact done-step physical fields are implemented, use a playback-local, diagnostics-only pre-reset clone hook modeled on the existing `_install_prereset_coverage_capture()` pattern. It may copy only coverage/base/scanner tensors and must call the original reset exactly once. If such a capture is unavailable, affected post fields must be null with `post_state_pre_reset_available=false`; they must never be filled from reset state as if it were the executed post state.

## 8. Immutable Input And Timing Contract

One collector update represents one completed policy decision:

```text
actor output and selected probability
-> capture raw action ids and immutable pre_problem subset
-> capture pre lifecycle generation/episode generation metadata
-> wrapper.step(raw actions)
-> read one cloned lifecycle-resolution payload
-> capture post state or marked pre-reset capture
-> build all M rows for each environment atomically
-> update collector state from payload post resolver snapshot
```

Required assertions:

```text
payload.assignment_proposal == wrapper.last_assignment_proposal
payload.effective_assignment == wrapper.last_effective_assignment
payload.effective_assignment == wrapper.last_assignment
controller_assignment == payload.effective_assignment
raw noop id N decodes to -1
payload dimensions are [E,M]
resolver snapshot dimensions are active [E,M], owner [E,N], pair [E,M,N]
all rows for one environment decision share episode_id and decision_step
previous active/owner/pair post state == current maintained pre state
```

Input tensors are detached/cloned at collector entry. Derived rows are CPU scalar/JSON values. The collector never mutates caller tensors.

## 9. Frozen Per-Step Row Schema

Schema version:

```text
phase9g8h1_assignment_proposal_effective_attribution_v1
```

One row is emitted per `(method_name, episode_id, env_id, decision_step, robot_id)`.

### 9.1 Required attribution fields

| Field | Type | Exact meaning/source | Classification |
| --- | --- | --- | --- |
| `schema_version` | string | Frozen row schema name | Required for attribution |
| `method_name` | string | Playback algorithm, e.g. `happo` | Required for attribution |
| `episode_id` | int | Playback-owned episode id | Required for attribution |
| `env_id` | int | Vector environment row | Required for attribution |
| `decision_step` | int | 1-based decision index within episode/env | Required for attribution |
| `robot_id` | int | Stable agent order index | Required for attribution |
| `robot_name` | string | `wrapper.agents[robot_id]` | Required for attribution |
| `raw_action_id` | int | Raw policy id, targets `0..N-1`, noop `N` | Required for attribution |
| `decoded_proposal` | int | Wrapper payload proposal, targets or `-1` noop | Required for attribution |
| `proposal_is_noop` | bool | `decoded_proposal == -1` | Required for attribution |
| `selected_action_probability` | float | `exp(evaluate_actions log-prob)` for sampled raw action and historical mask | Required for attribution |
| `active_target_before` | int | Maintained prior post resolver active id; `-1` idle | Required for attribution |
| `robot_execution_state_before` | string | `idle` iff active id is `-1`, else `executing` | Required for attribution |
| `proposal_target_owner_before` | nullable int | Maintained owner at proposal target; null for noop | Required for attribution |
| `proposal_available_before` | nullable bool | `pre_problem.available_mask[e,r,j]`; null for noop | Required for attribution |
| `proposal_feasible_before` | nullable bool | `pre_problem.feasible_mask[e,r,j]`; null for noop | Required for attribution |
| `proposal_covered_before` | nullable bool | `pre_problem.viewpoints_covered[e,j]`; null for noop | Required for attribution |
| `self_pair_failed_or_released_before` | nullable bool | Pair state equals canonical failed/released values; null for noop | Required for attribution |
| `effective_assignment` | int | Wrapper payload resolver output | Required for attribution |
| `effective_is_noop` | bool | `effective_assignment == -1` | Required for attribution |
| `proposal_effective_changed` | bool | Payload flag and equality cross-check | Required for attribution |
| `controller_assignment` | int | Exact high-level assignment passed to controller; asserted equal to effective | Required for attribution |
| `primary_attribution` | string | Deterministic priority rule in Section 10 | Required for attribution |
| `resolver_event_types` | JSON list[string] | All events projected onto this robot row, in source order | Required for attribution |
| `resolver_events` | JSON list[object] | Full copied projected events; secondary events are not hidden | Required for attribution |
| `proposal_rejected` | bool | Pre-result rejection code is not `REJECT_NONE` | Required for attribution |
| `proposal_rejected_reason` | string | Canonical resolver rejection name | Required for attribution |
| `arbitration_winner_robot_id` | nullable int | Winner from exact-conflict event, projected to claimant rows | Required for attribution when applicable |
| `owner_robot_id` | nullable int | Relevant pre owner/winner/self owner after accepted new claim | Required for attribution when applicable |
| `active_target_after` | int | Post completion/release/reset resolver snapshot | Required for attribution |
| `target_completed_this_step` | bool | Post-result flag or robot-specific `target_completed` event | Required for attribution |
| `budget_failure_this_step` | bool | Robot-specific `budget_failure` event/post failure reason | Required for attribution |
| `release_budget_failure_this_step` | bool | Post released flag or release event | Required for attribution |
| `active_target_infeasible_deferred` | bool | Event present for this robot | Required for attribution |
| `newly_covered_ids` | nullable JSON list[int] | Pre/post covered-mask delta from true pre-reset state | Required when reliable; null on uncaptured autoreset |
| `coverage_ratio` | nullable float | True post-step covered ratio, before reset | Required when reliable; null on uncaptured autoreset |
| `done` | bool | Environment done on this decision | Required for attribution |
| `reset` | bool | Resolver post-step reset attached to this row | Required for attribution |

### 9.2 Motion and distance fields

These fields are needed to answer why a resolver-executing robot appeared motionless:

| Field | Type | Definition | Classification |
| --- | --- | --- | --- |
| `controller_action_l2_norm` | float | L2 norm of the robot's 9D controller command before env step | Required for motion attribution |
| `base_motion_distance` | nullable float | XY norm between true pre- and post-step base positions | Required for motion attribution when post state is reliable |
| `distance_to_effective_target_before` | nullable float | Pre-step scanner-to-effective-target Euclidean distance | Required when effective target exists |
| `distance_to_effective_target_after` | nullable float | True post-step scanner-to-the-same-effective-target distance | Required when post state is reliable |
| `distance_to_effective_target` | nullable float | Alias of the post value for compact analysis | Useful optional diagnostic |
| `distance_progress` | nullable float | Before distance minus after distance; positive means approach | Required when both distances are finite |
| `post_state_pre_reset_available` | bool | Distinguishes real post state from auto-reset state | Required validity metadata |

`distance_to_effective_target` is not the current console's raw-proposal distance. The frozen field always refers to the effective/controller target.

### 9.3 Useful optional fields

```text
pre_lifecycle_snapshot_generation
post_lifecycle_snapshot_generation
episode_generation_before
episode_generation_after
proposal_raw_action_available_before
available_target_ids_before
claim_conflict
claim_winner
claim_loser
continued_from_active_target
new_claim_started
switch_requested
switch_rejected
reset_before_decision
unprojected_env_event_types
```

The lifecycle generation values are alignment metadata only. They are never network inputs.

### 9.4 Deferred or unavailable without extra instrumentation

```text
wheel/joint-level physical cause of zero base motion
exact scan eligibility decomposition for every viewpoint after auto reset
physics contact forces
camera/sensor frame attribution
counterfactual action probabilities for actions not selected
```

These are not required for the first attribution diagnostic.

## 10. Primary Attribution Rule

Initial reset boundary events are removed from the first decision's candidate event list and retained separately. For actual decision events, use this priority:

```text
1.  reset
2.  target_completed
3.  release_budget_failure
4.  budget_failure
5.  active_target_infeasible_deferred
6.  switch_rejected_executing
7.  claim_lost
8.  owned_target_rejected
9.  failed_pair_reclaim_rejected
10. covered_target_rejected
11. unavailable_target_rejected
12. attempt_started
13. attempt_continued_same_target
14. attempt_continued_noop_contract_c
15. noop_idle
16. unclassified
```

Rationale:

- Reset, completion, and release end state segments and explain the next decision state.
- `release_budget_failure` outranks its paired `budget_failure` because it is the behavior-changing terminal event; both remain in `resolver_events` and both counters increment.
- Active infeasibility can coexist with same-target, noop, or switch handling and is more explanatory for zero controller motion.
- Rejections outrank ordinary starts/continuations.
- `attempt_continued_noop_contract_c` and `noop_idle` remain distinct stable labels.

Known coexistence rules:

```text
exact_claim_conflict_resolved + attempt_started        -> winner row primary attempt_started
exact_claim_conflict_resolved + claim_lost             -> loser row primary claim_lost
active_target_infeasible_deferred + continuation       -> primary infeasible_deferred
active_target_infeasible_deferred + switch_rejected    -> primary infeasible_deferred
budget_failure + release_budget_failure                -> primary release_budget_failure
continuation/start + target_completed                  -> primary target_completed
completion/release + done reset                        -> primary reset; terminal flags preserve completion/release
```

Robot-less exact-conflict events are projected to every `claiming_robot_id`. Robot-less stranded events remain environment-level secondary diagnostics. A robot-less completion that has no authoritative owner is retained as an unprojected environment event and must not be assigned to an arbitrary robot.

## 11. Frozen Per-Robot Summary

Each `(method_name, episode_id, env_id, robot_id)` summary contains:

```text
total_decision_steps

proposal_noop_count
proposal_target_count
effective_idle_noop_count
effective_target_count
proposal_effective_changed_count
proposal_rejected_count

noop_idle_count
noop_continue_active_count
attempt_started_count
same_target_continue_count
switch_rejected_count

exact_conflict_win_count
exact_conflict_loss_count
owned_target_rejected_count
covered_target_rejected_count
failed_pair_reclaim_rejected_count
unavailable_target_rejected_count

active_target_infeasible_deferred_count
target_completed_count
budget_failure_count
release_budget_failure_count

idle_step_count
executing_step_count
idle_fraction
executing_fraction

unique_targets_started
unique_targets_completed
total_new_viewpoints_credited

zero_controller_command_count
zero_base_motion_step_count
zero_progress_step_count
active_target_segment_count
```

Exact accounting definitions:

```text
idle_step_count      = count(effective_assignment == -1)
executing_step_count = count(effective_assignment >= 0)
idle + executing     = total_decision_steps

noop_continue_active counts Contract-C noop continuation and is executing.
switch_rejected counts as executing because the active target continues.
proposal rejection and proposal/effective change are separate counts.
```

`total_new_viewpoints_credited` counts unique robot-specific `target_completed` events. Unowned/environment-only completions are reported as `unattributed_new_viewpoints` at episode level, not assigned heuristically.

This summary directly supports statements such as:

```text
robot_0 was effectively idle for X/Y steps;
its actor proposed noop on A steps and targets on B steps;
C target proposals were rejected, split by exact reason;
robot_1 executed Z target segments and had K budget releases;
robot_2 was resolver-executing but had Q zero-command or zero-motion steps.
```

## 12. Frozen Target-Segment Schema

One segment is a continuous resolver-active `(episode, env, robot, target)` interval.

Required fields:

```text
schema_version
method_name
episode_id
env_id
robot_id
robot_name
segment_id
target_id
start_step
end_step
duration_steps
release_type
minimum_distance
zero_distance_dwell_steps
coverage_gain_during_segment
```

Additional selected fields:

```text
start_distance
final_distance
cumulative_positive_distance_progress
zero_progress_steps
zero_base_motion_steps
active_infeasible_steps
noop_continue_steps
same_target_continue_steps
switch_rejected_steps
start_raw_action_id
start_decoded_proposal
terminal_event_types
```

Segment rules:

- Start on `attempt_started`.
- Continue across same-target action, noop continuation, and rejected switch while the active target remains unchanged.
- End inclusively on `target_completed`, `release_budget_failure`, or reset.
- At collector finalize, an active segment ends with `release_type=playback_truncated`.
- An active target change without an accepted terminal event closes with `release_type=invariant_break` and fails the fake regression.
- `duration_steps = end_step - start_step + 1`.

`zero_distance_dwell_steps` means steps whose finite scanner-to-target post distance is within that robot's configured scan-position tolerance. It is a spatial dwell diagnostic, not proof of scan completion because orientation, reach, sensor range, FOV, and env dwell gates also apply. `zero_progress_steps` separately counts finite steps with absolute distance progress at or below a recorded numerical epsilon. `zero_base_motion_steps` uses the configured minimum-motion threshold.

`coverage_gain_during_segment` counts uniquely completed targets credited to this segment. Nearby unowned completions remain uncredited rather than being assigned by proximity.

## 13. Episode Load-Balance Summary

Required per-robot vectors:

```text
executing_steps
idle_steps
target_starts
target_completions
budget_releases
new_viewpoint_credit
```

Required derived values:

```text
executing_step_range = max(executing_steps) - min(executing_steps)
completion_count_range = max(completions) - min(completions)
executing_fraction_of_team_total_by_robot
completion_fraction_of_team_total_by_robot
robots_with_zero_target_starts
robots_with_zero_completions
```

Selected optional values:

```text
jain_executing_steps
jain_completion_count
```

For vector `x`, Jain fairness is:

```text
(sum(x) ** 2) / (M * sum(x ** 2))
```

If the vector total is zero, report null rather than defining a misleading perfect-fairness value.

These are playback diagnostics only. They are not reward terms, optimizer targets, automatic failure criteria, or evidence that equal work is always optimal.

## 14. Default-Off CLI Contract

Add only to `play_assignment.py` in the future implementation:

```text
--log_assignment_proposal_effective
--assignment_proposal_effective_output_dir PATH
--print_assignment_proposal_effective
```

Frozen behavior:

- With all three unset, no collector is constructed, no new state copies are made for this feature, no new event read occurs, no files are created, and the current aggregate console schema is unchanged.
- `--log_assignment_proposal_effective` requires an explicit output directory and writes all three output files.
- `--assignment_proposal_effective_output_dir` without logging is a startup error rather than a silent no-op.
- `--print_assignment_proposal_effective` constructs the in-memory collector and prints compact rows at the existing `print_steps` / `diagnostic_interval` cadence; it does not write files unless logging is also enabled.
- Existing `--log_assignment_lifecycle_resolver` behavior, where available in the other diagnostics script, remains independent. The new collector does not require it.
- No scenario YAML change is required.
- Existing output files must not be overwritten silently; the future implementation should fail if any target filename already exists.

## 15. Output File Contract

### 15.1 `assignment_proposal_effective_rows.csv`

Owner: new playback attribution collector.

Authoritative joined source for one per-robot decision row. Written incrementally after each complete environment decision. It contains scalar columns plus JSON cells for event lists and id lists.

Join key:

```text
(schema_version, method_name, episode_id, env_id, decision_step, robot_id)
```

### 15.2 `assignment_proposal_effective_summary.json`

Owner: new collector. Derived from finalized joined rows and segments. Contains:

```text
schema/version metadata
E/M/N and noop encodings
per-robot summaries
episode load-balance summaries
unprojected environment events
validity/null counters
output artifact paths
```

Written by idempotent `finalize()`.

### 15.3 `assignment_target_segments.csv`

Owner: new collector. Derived from the row stream using the segment rules in Section 12. Written at finalize after any open segment receives `playback_truncated`.

### 15.4 Existing resolver files

```text
assignment_lifecycle_resolver_events.jsonl
assignment_lifecycle_resolver_rows.csv
assignment_lifecycle_resolver_summary.json
```

These remain owned by `AssignmentLifecycleResolverRuntimeAdapter`. They are authoritative raw resolver outputs when separately enabled. The new collector does not rewrite or consume-drain them. Its rows retain full projected event copies because that is necessary for a self-contained joined record, while the existing JSONL remains the independent raw audit trail.

## 16. Compact Console Design

Keep the existing aggregate step line. Add per-robot lines only under `--print_assignment_proposal_effective`:

```text
[STEP 051][env_0][robot_0] proposal=-1 effective=-1 active=-1->-1 attr=noop_idle p=0.8123 cmd=0.0000 move=0.0000
[STEP 051][env_0][robot_1] proposal=35 effective=35 active=-1->35 attr=attempt_started p=0.4412 cmd=2.1341 move=0.0800
[STEP 051][env_0][robot_2] proposal=-1 effective=-1 active=-1->-1 attr=noop_idle p=0.7310 cmd=0.0000 move=0.0000
```

Rejected proposal:

```text
[STEP 120][env_0][robot_0] proposal=25 effective=-1 active=-1->-1 attr=owned_target_rejected owner=1 p=0.3921
```

Contract-C continuation:

```text
[STEP 120][env_0][robot_1] proposal=-1 effective=25 active=25->25 attr=attempt_continued_noop_contract_c p=0.6210
```

Do not print full event JSON by default. The CSV retains it.

## 17. Future Fake-Sequence Test Plan

Required synthetic sequences:

```text
idle actor noop
idle target accepted
executing same target
executing noop continuation
executing switch rejected
exact conflict winner and loser
owned target rejected
covered target rejected
failed-pair reclaim rejected
unavailable target rejected
active target infeasible deferred
target completion
budget failure plus release
done reset
explicit episode reset before first decision
```

Required exact summary assertions:

```text
idle + executing == total decisions for every robot
proposal noop + proposal target == total decisions
proposal/effective changed count exact
proposal rejection count and reason split exact
Contract-C noop continuation never increments idle count
switch rejection never increments idle count
conflict winner/loss counts exact without double counting global event
completion and release counts exact
segment start/end/duration/release exact
open segment finalizes as playback_truncated
per-robot totals sum to episode totals
Jain values and zero-total null behavior exact
```

Required architecture regressions:

```text
default-off identity and collector factory not called
no output files when disabled
collector API has no pop_events/drain dependency
one wrapper payload consumed exactly once
input tensors and payload remain unchanged
variable E/M/N
multiple environments
subset reset
initial reset event separation
post-step reset alignment
global-event projection and unprojected-event retention
post-reset physical fields null unless pre-reset capture is supplied
idempotent finalize
no duplicate event or completion credit
rows and segments parse with frozen schema
existing aggregate console remains unchanged when flags are off
```

The known installed/runtime resolver behavior tests should remain unchanged. Phase 9G-8H-1 may run only `py_compile` and fake/non-environment tests.

## 18. Future Bounded Runtime Validation

Requires separate authorization after Phase 9G-8H-1 review:

```text
checkpoint:
  assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh
  final models generation 2

runtime:
  lifecycle_contract_c
  one environment
  three robots
  N = 50
  seed = 1
  max_steps = 300
  deterministic actor playback
  no training
  no continuation
```

Validation must assert:

```text
one row per executed robot decision
raw action decodes to payload proposal
payload effective equals controller assignment
every rejection has a canonical reason/event
idle noop and Contract-C continuation are distinguishable
all effective-target rows are counted executing
completion/release closes segments on the same decision
no duplicate event counting
summary totals reconcile with rows/segments
default-off playback remains output/console identical in a separate approved identity run
```

Codex may run headless playback only after explicit authorization. The user retains visual inspection.

## 19. Implementation Risks And Static Findings

1. The current resolver runtime `RESOLVER_EVENT_TYPES` summary list omits `noop_idle` and `unavailable_target_rejected`, although those events can exist and are still recorded dynamically in the event buffer/JSONL. The new collector must count event names dynamically from the received batch and must not rely on that summary list.
2. Initial resolver reset events can be carried into the first wrapper step payload. They require boundary separation before primary attribution.
3. Existing resolver row `step` is not a safe playback decision join key after increment/reset. Playback-owned ids are mandatory.
4. A robot-less resolver event must never be assigned to a robot by guess. Exact-conflict events have explicit claimant/winner fields; unowned completion/stranded events remain environment-level.
5. `effective_assignment >= 0` can coexist with a zero controller command when the target is covered or infeasible at controller conversion. Record command norm and active infeasibility separately.
6. A visually motionless robot may still move its scanner/arm. Base motion and 9D command are different diagnostics.
7. Automatic environment reset can erase final post-step poses/coverage. Use a diagnostics-only pre-reset clone or explicit null validity.
8. Selected action probability is the masked categorical probability of the chosen raw action. It is diagnostic and must not be interpreted as an unmasked preference.
9. Short playback workload imbalance is descriptive, not proof of a reward defect or need for forced equal assignment.

None of these findings blocks the selected default-off design.

## 20. Explicit Non-Goals

The diagnostic does not:

```text
penalize noop
change actor logits or sampling
force work onto idle robots
rebalance workload
change exact-target arbitration or tie-breaking
allow target stealing
allow executing switches
release targets early
change budget thresholds
clear failed pairs
add failed-pair TTL or retry
change observations, shared observations, masks, or rewards
change controller commands or environment dynamics
change checkpoint loading or saving
```

## 21. Frozen Decisions

| Required decision | Frozen result |
| --- | --- |
| Current `play_assignment` assignment output | Effective assignment and controller input, not raw/decoded proposal |
| Raw proposal source | Raw action in playback; authoritative decoded proposal in wrapper lifecycle payload |
| Effective assignment source | Wrapper lifecycle payload / `last_effective_assignment` |
| Event source | Cloned `resolver_events` in wrapper lifecycle payload |
| Event-draining owner | Runtime adapter drains resolver; wrapper drains adapter once; collector never drains |
| Pre/post alignment | Playback-owned episode/decision ids plus one wrapper payload per completed step |
| Existing resolver JSONL sufficient alone? | No; retain as optional raw cross-check |
| New collector needed? | Yes, pure playback-only joined collector |
| Per-step schema | Frozen in Section 9 |
| Per-robot summary | Frozen in Section 11 |
| Target segments | Frozen in Section 12 |
| Default-off CLI | Three explicit flags in Section 14 |
| Output files | Rows CSV, summary JSON, segments CSV |
| Test strategy | Fake sequences and non-environment architecture regressions first |
| Runtime validation | Separate-authorized one-env, seed-1, 300-step actor playback |
| Can implementation remain playback-only? | Yes |

## 22. Boundary Confirmation

This phase modified documentation only.

No production Python, tests, YAML, installed HARL, or Conda files were modified. No resolver, Contract C, ownership, failed-pair, budget, observation, shared-observation, mask, reward, controller, environment, or checkpoint behavior changed.

No training, short training smoke, playback, evaluation, comparison method, checkpoint load, AppLauncher, Isaac Sim, visual inspection, or commit occurred.

## 23. Next Phase

Recommended only after this report is reviewed and accepted:

```text
Phase 9G-8H-1:
Playback Proposal-Effective Attribution Diagnostic Implementation
and Fake Regression
```

That phase may implement the default-off playback-only collector and run `py_compile` plus fake/non-environment regressions. It must not run playback, launch Isaac Sim, train, evaluate, or change assignment behavior.
