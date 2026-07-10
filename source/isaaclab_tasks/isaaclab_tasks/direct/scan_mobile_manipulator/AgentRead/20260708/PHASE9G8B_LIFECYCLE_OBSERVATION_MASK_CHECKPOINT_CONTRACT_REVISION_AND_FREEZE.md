# Phase 9G-8B Lifecycle Observation / Mask / Checkpoint Contract Revision and Freeze

Date: 2026-07-08

Scope: documentation/design only, static source inspection only, contract revision and freeze only.

## Files And Boundaries Inspected

Required docs:

- `AgentRead/AGENTS.md`
- `AgentRead/TASK_PROGRESS.md`
- `AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md`
- `AgentRead/20260708/PHASE9G8A_GPT_REVISED_FINAL_DESIGN_REVIEW.md.md`
- Phase 9G-7A through Phase 9G-7F reports under `AgentRead/20260708/`

Note: the requested review file was present on disk with the suffix `.md.md`. It was read as the current Phase 9G-8A revised final design review. No file was renamed in this phase.

Project source boundaries:

- `assignment_lifecycle_resolver.py`
- `assignment_lifecycle_resolver_runtime.py`
- `assignment_harl_wrapper.py`
- `assignment_rl_interface.py`
- `assignment_state.py`
- `scan_mobile_manipulator_env.py`
- `assignment_harl_training.py`
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`

Installed HARL boundaries used by this project:

- `harl/runners/on_policy_base_runner.py`
- `harl/common/buffers/on_policy_actor_buffer.py`
- `harl/common/buffers/on_policy_critic_buffer_ep.py`
- `harl/common/buffers/on_policy_critic_buffer_fp.py`
- `harl/algorithms/actors/on_policy_base.py`
- `harl/algorithms/actors/happo.py`
- `harl/algorithms/actors/hatrpo.py`
- `harl/algorithms/actors/haa2c.py`
- `harl/algorithms/critics/v_critic.py`
- `harl/models/policy_models/stochastic_policy.py`
- `harl/models/value_function_models/v_net.py`
- `harl/models/base/act.py`
- `harl/models/base/distributions.py`

No Python source, YAML/runtime behavior, model loading, checkpoint loading, observation builder, mask builder, resolver behavior, training, playback, evaluation, Isaac Sim process, or commit was changed in this phase.

## 1. Executive Decision

Classification:

```text
CONTRACT-FREEZE READY
```

Phase 9G-8A classification is reaffirmed as:

```text
PASS WITH REQUIRED REVISIONS
```

Phase 9G-8B resolves the required revisions by freezing:

- the real wrapper budget-progress source of truth;
- the distinction between actor-required and critic/shared-required budget state;
- the ownership / active-target invariant that removes `task_owned_by_self` from actor network input;
- the final actor schema as exactly three new per-task fields;
- the first shared observation migration as current HARL-compatible concatenation plus exact budget sufficient statistic;
- lifecycle Contract C available-action masks;
- immutable decision snapshots and generation ids;
- PPO historical mask replay;
- the official lifecycle guardrail profile;
- high-level lifecycle profiles instead of freely combinable user booleans;
- ordered schema manifests and stable SHA-256 fingerprints;
- strict loader compatibility boundaries;
- the revised resolver-enabled training gate.

Every required source-of-truth, invariant, configuration boundary, checkpoint boundary, and training gate can be stated from current static source inspection. No unresolved question blocks Phase 9G-8C.

## 2. Current Behavior-State Classification

Do not place a field in an observation only because it exists in a resolver snapshot. The table below classifies fields by current behavior.

| state | source owner | current role | actor destination | critic/shared destination | mask destination | builder/internal | future-policy | diagnostics-only |
|---|---|---|---|---|---|---|---|---|
| `active_target_id [E,M]` | Resolver | Current resolver behavior-driving state; controls Contract C continuation/rejection | Required as `self_active_target[j]` | Required via all actors in shared concat | Required for executing mask | Also used to derive idle/executing | Future action semantics still need it | No |
| `task_owner_robot_id [E,N]` | Resolver | Current resolver behavior-driving state; owner conflict rejection | Teammate ownership required; self ownership derived | Required via actor concat | Required for teammate-owned target mask | `task_owned_by_self == self_active_target` assertion | Owner id may matter for future architectures | No |
| Resolver `pair_state [E,M,N]` active | Resolver | Behavior-driving through active target | Represented by `self_active_target` | Required via actor concat | Required through executing mask | Derived from active target for actor | Full enum may matter later | No |
| Resolver `pair_state` completed | Resolver/env | Completion/coverage behavior | Already covered by existing coverage fields | Already in shared concat | Existing physical mask | Derived from coverage | No | No |
| Same-robot failed/released pair memory | Resolver `pair_state` values `FAILED_BUDGET` / `RELEASED_BUDGET` | Current resolver behavior-driving state; same-pair rejection | Required as `self_pair_failed_or_released[j]` | Required via actor concat | Required for idle target mask | Pair enum collapsed to binary | Retry policy later must re-audit | No |
| Resolver `attempt_start_step [E,M]` | Resolver | Not used by current proposal interpretation | Excluded | Excluded | Excluded | May support assertions only | Future timeout/release policy | Mostly diagnostic |
| Resolver `attempt_age [E,M]` | Resolver | Not used by current proposal interpretation or budget release predicate | Excluded | Excluded | Excluded | Not a budget substitute | Future timeout/release policy | Diagnostic |
| Wrapper `_budget_attempt_target [E,M]` | AssignmentHarlWrapper budget tracker | Current wrapper budget behavior-driving state | Excluded under current controllability | Required indirectly; active target plus budget statistic must assert target match | Excluded | Snapshot/invariant input | Actor-required if abort/switch/release/retry added | No |
| Wrapper `_budget_attempt_steps [E,M]` | AssignmentHarlWrapper budget tracker | Current wrapper budget behavior-driving state | Excluded under current controllability | Required in exact normalized budget statistic | Excluded | Source for budget statistic | Actor-required if budget-controllable actions added | No |
| Wrapper `_budget_attempt_expected_steps [E,M]` | AssignmentHarlWrapper budget tracker | Latched diagnostic denominator precursor | Excluded | Excluded if exact budget statistic present | Excluded | Optional validation/debug | Future budget shaping | Diagnostic |
| Wrapper `_budget_attempt_budget_steps [E,M]` | AssignmentHarlWrapper budget tracker | Latched budget-release denominator | Excluded under current controllability | Required in exact normalized budget statistic | Excluded | Source for budget statistic | Actor-required if budget-controllable actions added | No |
| Budget progress / remaining budget | Derived from wrapper budget tracker | Current transition/release predictor | Not required under current Contract C action set | Required exactly | Not directly used | Derived tensor block | Actor-required if abort/switch/release/retry added | No |
| Completion/coverage state | Env `viewpoints_covered` plus resolver completion | Current behavior-driving state | Already present | Already present via concat | Already in physical mask | No duplicate | No | No |
| Physical feasibility/availability | Env `feasible_mask`, `available_mask` | Current behavior-driving state | Already present | Already present via concat | Required | No duplicate | No | No |
| Failure reason | Resolver `last_failure_reason` | Does not drive current behavior beyond pair state | Excluded | Excluded from minimum | Excluded | No | Future policy explanations | Diagnostic |
| Release reason | Resolver `last_release_reason` | Does not drive current behavior beyond pair state | Excluded | Excluded from minimum | Excluded | No | Future policy explanations | Diagnostic |
| Active-target infeasibility streak | Runtime adapter monitor | Does not change resolver behavior | Excluded | Excluded | Excluded | No | Future release policy only after re-audit | Diagnostic |
| Stranded failed-pair streak | Runtime adapter monitor | Does not change resolver behavior | Excluded | Excluded | Excluded | No | Future retry policy only after re-audit | Diagnostic |
| Resolver event history | Resolver/runtime adapter | Does not drive current behavior except persistent state already stored | Excluded | Excluded | Excluded | No | May support supervised/debug tasks | Diagnostic |

## 3. Real Budget-Progress Source-of-Truth Audit

The real budget release source of truth is the wrapper-local assignment cooldown/budget tracker, not the resolver attempt metadata.

Owner object:

```text
AssignmentHarlWrapper
```

Primary source fields:

| field | shape | dtype | meaning |
|---|---:|---|---|
| `_budget_attempt_target` | `[E,M]` | `torch.long` | Current budget-tracked target for each robot, `-1` inactive |
| `_budget_attempt_steps` | `[E,M]` | `torch.long` | Number of effective selected steps in the current budget segment |
| `_budget_attempt_initial_cost` | `[E,M]` | `torch.float32` | Selected path cost at segment start, diagnostic/source history |
| `_budget_attempt_expected_steps` | `[E,M]` | `torch.long` | Latched `ceil(initial_cost / per_agent_step)` |
| `_budget_attempt_budget_steps` | `[E,M]` | `torch.long` | Latched release threshold for the budget segment |
| `_last_budget_attempt_steps_for_selected_pair` | `[E,M]` | `torch.long` | Last selected-pair diagnostic numerator |
| `_last_budget_steps_for_selected_pair` | `[E,M]` | `torch.long` | Last selected-pair diagnostic threshold |
| `_last_budget_expected_steps_for_selected_pair` | `[E,M]` | `torch.long` | Last selected-pair diagnostic expected steps |
| `_last_budget_ratio_for_selected_pair` | `[E,M]` | `torch.float32` | Last selected-pair diagnostic ratio |
| `_last_budget_triggered_by_budget` | `[E,M]` | `torch.bool` | Post-step mask consumed by resolver runtime adapter |

Configuration fields that affect the budget release contract:

```text
assignment_cooldown_enabled
assignment_cooldown_trigger_mode
assignment_cooldown_duration_steps
assignment_cooldown_budget_multiplier
assignment_cooldown_budget_slack_steps
assignment_cooldown_budget_min_streak
assignment_cooldown_budget_require_no_global_gain
assignment_cooldown_budget_require_uncovered
assignment_cooldown_budget_require_available
assignment_cooldown_budget_require_feasible
assignment_cooldown_apply_to_action_mask
```

Initialization:

```text
AssignmentHarlWrapper._reset_assignment_diagnostics()
  initializes all _budget_attempt_* fields
  target = -1
  steps = 0
  initial_cost = 0
  expected_steps = 0
  budget_steps = 0
  _last_budget_triggered_by_budget = False
```

Per-step update path:

```text
AssignmentHarlWrapper.step()
  -> lifecycle resolver resolve_pre_step()
  -> effective_assignment
  -> env.step(controller(effective_assignment))
  -> post_step_problem
  -> _update_assignment_diagnostics(assignment=effective_assignment)
  -> _update_assignment_cooldown(...)
  -> _update_budget_attempt_tracking(...)
  -> _last_budget_triggered_by_budget
  -> _augment_info()["assignment_cooldown"]["budget_last_triggered_by_budget"]
  -> AssignmentLifecycleResolverRuntimeAdapter.budget_failure_diagnostics(...)
  -> build_resolver_budget_failure_diagnostics(effective_assignment, info)
  -> resolver observe_post_step(... external_diagnostics={"budget_failure_pairs": ...})
  -> resolver _apply_budget_failure_release(...)
```

Attempt-start update:

```text
same_segment = valid_viewpoint & (_budget_attempt_target == assignment)
new_segment = valid_viewpoint & (~same_segment)

new_segment:
  _budget_attempt_target = assignment
  _budget_attempt_steps = 1
  _budget_attempt_initial_cost = selected_cost
  _budget_attempt_expected_steps = expected_steps
  _budget_attempt_budget_steps = budget_steps
```

Continuation update:

```text
same_segment:
  _budget_attempt_steps += 1
  _budget_attempt_budget_steps remains unchanged
```

Inactive update:

```text
inactive_segment = ~valid_viewpoint
  clears target, steps, initial_cost, expected_steps, budget_steps
```

Completion cleanup:

```text
_clear_assignment_cooldown_for_covered_targets(covered_after)
  -> _clear_budget_attempts_for_covered_targets(...)
  -> _reset_budget_attempt_pairs(env_indices, agent_indices)
```

Budget-release cleanup:

```text
if trigger:
  _last_budget_triggered_by_budget[env, robot] = True
  optional legacy redirect/failed-pair memories may be activated if enabled
  _reset_budget_attempt_pairs(trigger_envs, trigger_agents)
```

Resolver release cleanup:

```text
_apply_budget_failure_release(...)
  pair_state[env, robot, target] = FAILED_BUDGET then RELEASED_BUDGET
  last_failure_reason = BUDGET_FAILURE
  last_release_reason = BUDGET_FAILURE
  active target clears if it matches target
  owner clears if owner is robot
```

Done-env reset:

```text
AssignmentHarlWrapper.step()
  resolver observe_post_step(... done_env_ids=done_env_ids)
    -> resolver reset for done env ids
  then wrapper _reset_assignment_diagnostics(env_ids=done_env_ids, problem=post_step_problem)
```

Partial reset:

```text
_reset_assignment_diagnostics(env_ids=ids)
AssignmentLifecycleResolverRuntimeAdapter.reset_envs(env_ids=ids)
```

Full reset:

```text
AssignmentHarlWrapper.reset()
  env.reset()
  problem = get_assignment_problem()
  _reset_assignment_diagnostics(problem=problem)
  resolver_runtime.reset_envs(env_ids=None)
```

Current release predicate, simplified pseudocode:

```text
selected_cost, expected_steps, computed_budget_steps =
    _budget_expected_and_limit_steps(effective_assignment, pre_step_problem)

same_segment =
    valid_viewpoint
    and _budget_attempt_target == effective_assignment

new_segment =
    valid_viewpoint
    and not same_segment

inactive_segment = not valid_viewpoint

if inactive_segment:
    clear budget attempt state

if same_segment:
    _budget_attempt_steps += 1

if new_segment:
    _budget_attempt_target = effective_assignment
    _budget_attempt_steps = 1
    _budget_attempt_expected_steps = expected_steps
    _budget_attempt_budget_steps = computed_budget_steps

over_budget =
    _budget_attempt_steps >= max(_budget_attempt_budget_steps, 1)

budget_candidate = valid_viewpoint
if budget_require_available:
    budget_candidate &= selected_available_mask
if budget_require_feasible:
    budget_candidate &= selected_feasible
if budget_require_uncovered:
    budget_candidate &= not selected_covered_after
if budget_require_no_global_gain:
    budget_candidate &= not global_gain

budget_mode_trigger = budget_candidate & over_budget

if trigger_mode == "budget_and_streak":
    budget_mode_trigger &= same_target_streak >= budget_min_streak

if trigger_mode == "budget":
    budget_trigger = budget_mode_trigger
elif trigger_mode == "budget_and_streak":
    budget_trigger = budget_mode_trigger
else:
    budget_trigger = false

if duration_steps <= 0:
    budget_trigger = false

_last_budget_triggered_by_budget = budget_trigger
```

Budget steps are latched for the attempt. `_budget_attempt_budget_steps` is set only on `new_segment`, then held through `same_segment` continuations until inactive, completion cleanup, budget trigger cleanup, or reset.

Single-ratio audit:

```text
active_budget_progress_norm =
    clamp(_budget_attempt_steps / max(_budget_attempt_budget_steps, 1), 0, 1)
```

This single ratio is not an exact sufficient statistic for the next budget-release transition. Two attempts can have the same ratio but different denominators, for example `9/10` and `90/100`. The next continuation crosses the threshold in the first case but not the second.

Frozen exact normalized budget sufficient statistic:

```text
active_budget_progress_norm =
    clamp(_budget_attempt_steps / max(_budget_attempt_budget_steps, 1), 0, 1)

active_budget_step_fraction =
    1 / max(_budget_attempt_budget_steps, 1)
```

Shape:

```text
[E, M, 2]
```

Flattened critic/shared add-on:

```text
[E, 2M]
```

Inactive robots:

```text
active_budget_progress_norm = 0
active_budget_step_fraction = 0
```

The active-target matrix already disambiguates inactive robots from just-started active attempts. For a same-segment continuation under the official `lifecycle_contract_c` budget profile, the hidden tracker part of the next over-budget predicate is exactly:

```text
active_budget_progress_norm + active_budget_step_fraction >= 1
```

The remaining budget-candidate gates depend on observed physical/coverage state, post-step transition outcome, and frozen profile constants. They are not substitutes for the hidden budget tracker statistic.

Can current actor observation reconstruct the predicate exactly?

```text
No.
```

Current actor observation contains selected path cost and some legacy dynamic scalars, but it does not contain the latched `_budget_attempt_budget_steps` denominator or the budget attempt target/steps. Current cost can differ from the latched initial cost after movement.

Can current shared observation reconstruct the predicate exactly?

```text
No.
```

Current shared observation is only concatenated current actor observations, so it has the same missing latched budget state.

Can resolver `attempt_age` substitute for the wrapper budget state?

```text
No.
```

Resolver `attempt_age` is updated by resolver pre-step continuation logic and is not used by the budget trigger. Wrapper budget state is updated after the environment step, uses effective assignment, starts at 1 on a new valid segment, latches a budget denominator, applies budget-candidate gates, resets on trigger/completion/inactive/done, and feeds `_last_budget_triggered_by_budget`. These semantics are not equivalent to resolver `attempt_age`.

Frozen conclusion:

```text
resolver attempt_age is not a substitute
exact active budget progress is critic/shared-required
the exact first migration block is two normalized scalars per robot
```

## 4. Actor Budget-Progress Controllability Analysis

Under current Contract C, an executing robot with active target `k` has no legal switch, abort, manual release, or retry action.

Action cases:

| robot state | sampled action | current resolver result | budget-progress controllability |
|---|---|---|---|
| Executing target `k` | target `k` | Continue `k` | Budget progress affects future release, but action choice cannot alter continuation |
| Executing target `k` | noop raw id `N` | Continue `k` | Same effective transition class as target `k` |
| Executing target `k` | different target `j` | Switch rejected, continue `k` | Not a legal controllable transition; lifecycle mask will remove it |

Frozen conclusion:

```text
actor budget progress not required under current action controllability
```

This does not mean budget progress is transition-irrelevant. Budget progress affects the next release transition and therefore centralized value estimation. It is critic/shared-required.

Future action-semantic changes that force re-audit:

- explicit abort action;
- switch while executing;
- manual release;
- retry action;
- explicit continue action that differs from noop/current-target continuation;
- budget-dependent action masks;
- timeout/release policy driven by attempt age or budget progress.

## 5. Ownership / Active-Target Invariant Audit

Invariant checked for legal decision snapshots:

```text
task_owned_by_self[j] == self_active_target[j]
```

Transition audit:

| transition | code path | invariant result |
|---|---|---|
| Full reset / partial reset | `AssignmentLifecycleResolver.reset()` clears `active_target_id` and `task_owner_robot_id` | Holds |
| Idle noop | `resolve_pre_step()` sets effective noop only, no owner/active mutation | Holds |
| Idle claim | `_start_claim()` sets `active_target_id[env,robot]=target` and `task_owner_robot_id[env,target]=robot` together | Holds |
| Simultaneous arbitration | only winner calls `_start_claim()`; losers get no owner/active | Holds |
| Same-target continuation | `_resolve_executing_robot()` leaves active and owner unchanged | Holds |
| Noop continuation | `_resolve_executing_robot()` leaves active and owner unchanged | Holds |
| Rejected switch | `_resolve_executing_robot()` leaves active and owner unchanged | Holds |
| Completion | `_complete_target()` clears robot attempts for active/owner robots and then sets task owner to `NO_OWNER` | Holds after transition; internal transient is not a decision snapshot |
| Budget failure/release | `_apply_budget_failure_release()` clears matching active attempt and clears owner if owner is robot | Holds after transition; internal transient is not a decision snapshot |
| Done-env reset | `observe_post_step()` calls resolver reset for done env ids | Holds |

No legal resolver transition creates a decision snapshot where:

```text
task owned by self but robot has no active target
robot has active target but task owner is not self
```

The resolver includes defensive completion logic that can clear an owner even if it was not in `active_robots`, but that is robustness against inconsistent internal state, not a legal decision snapshot produced by current transitions.

Frozen actor-schema consequence:

```text
task_owned_by_self:
  builder-internal derived tensor and invariant assertion
  not an actor network input
```

If a future implementation introduces owner transfer, queued ownership, manual release, or target reservation without active execution, this invariant must be re-audited before changing observations.

## 6. Frozen Actor Observation Contract

Frozen actor add-on:

```text
exactly three new per-task actor fields
```

Fields:

```text
self_active_target
task_owned_by_teammate
self_pair_failed_or_released
```

Do not add:

```text
raw normalized target id
owner robot id
owner one-hot
separate task_owned_by_self network field
```

Layout decision:

```text
Place the fields inside each existing per-task row.
Do not append unrelated tail vectors.
```

Static inspection confirms compatibility with the current wrapper because `_assignment_observation_extension()` already builds a per-task `viewpoint_rows` tensor by concatenating row fields and flattening `[E,N,row_dim]` to `[E,N*row_dim]`. The lifecycle builder can extend the row dimension from 14 to 17 under `lifecycle_v1`.

Frozen lifecycle task-row field order:

| index | field |
|---:|---|
| 0 | relative_viewpoint_position_x |
| 1 | relative_viewpoint_position_y |
| 2 | relative_viewpoint_position_z |
| 3 | viewpoint_quaternion_w |
| 4 | viewpoint_quaternion_x |
| 5 | viewpoint_quaternion_y |
| 6 | viewpoint_quaternion_z |
| 7 | covered_flag |
| 8 | available_flag |
| 9 | feasible_flag |
| 10 | static_geometric_feasible_flag |
| 11 | normalized_selected_path_cost |
| 12 | per_viewpoint_attempted_count_norm |
| 13 | per_viewpoint_last_attempt_age_norm |
| 14 | self_active_target |
| 15 | task_owned_by_teammate |
| 16 | self_pair_failed_or_released |

Field contract:

| field | semantic meaning | source tensor | shape per actor | dtype | normalization | padding behavior | reset semantics | snapshot timing |
|---|---|---|---:|---|---|---|---|---|
| `self_active_target[j]` | Acting robot is executing task `j`; also derived self ownership | `active_target_id[e, robot] == j` | `[E,N,1]` | float32 binary | none | future invalid task slots 0 | 0 after reset/release/completion | immutable next-decision snapshot |
| `task_owned_by_teammate[j]` | Any other robot owns task `j` | `task_owner_robot_id[e,j] not in {NO_OWNER, robot}` | `[E,N,1]` | float32 binary | none | future invalid task slots 0 | 0 after reset/release/completion | immutable next-decision snapshot |
| `self_pair_failed_or_released[j]` | This robot-task pair is in resolver failed/released budget memory | `pair_state[e,robot,j] in {PAIR_FAILED_BUDGET, PAIR_RELEASED_BUDGET}` | `[E,N,1]` | float32 binary | none | future invalid task slots 0 | 0 after reset; clears on task completion/reset | immutable next-decision snapshot |

Dimension formulas:

```text
legacy_actor_dim = 100 + 3M + 16N

lifecycle_actor_dim
  = legacy_actor_dim + 3N
  = 100 + 3M + 19N
```

For:

```text
M = 3
N = 50
```

verified:

```text
legacy_actor_dim = 909
lifecycle_actor_dim = 1059
```

Intentionally excluded from actor input:

| excluded state | reason |
|---|---|
| `task_owned_by_self` | Proven equivalent to `self_active_target` for legal decision snapshots |
| Raw active target id | Per-task indicator avoids ordinal id bias and aligns with task rows |
| Owner robot id / owner one-hot | Actor only needs self/teammate/unowned effect; exact owner id is privileged and count-dependent |
| Resolver `attempt_start_step` / `attempt_age` | Not used by current resolver proposal interpretation or budget release |
| Wrapper budget progress | Transition-relevant but actor-uncontrollable under Contract C |
| Teammate failed-pair matrix | Does not affect this actor's proposal acceptance |
| Failure/release reason | Pair state drives behavior; reason is logging-only |
| Active-target infeasibility streak | Diagnostics-only; no release behavior |
| Stranded failed-pair streak | Diagnostics-only; no retry behavior |
| Resolver event history | Logging-only beyond persistent state already exposed |

## 7. Critic/Shared Observation Alternatives

### Option A: Current HARL-compatible concatenation plus exact budget block

Definition:

```text
shared observation =
concat(all revised lifecycle actor observations)
+
exact active budget sufficient statistic
```

Budget block:

```text
active_budget_progress_norm [E,M]
active_budget_step_fraction [E,M]
flattened budget block [E,2M]
```

General dimension:

```text
shared_dim_A =
    M * (100 + 3M + 19N) + 2M
```

For `M=3, N=50`:

```text
shared_dim_A =
    3 * 1059 + 6 =
    3183
```

The value `3180` would apply only if one budget scalar per robot were exact. Static inspection rejects that single-ratio assumption.

Evaluation:

| criterion | result |
|---|---|
| Markov sufficiency | Sufficient for current lifecycle state when paired with exact two-scalar budget block and existing physical/coverage fields |
| Implementation complexity | Lowest-risk; extends current wrapper pattern |
| Current HARL EP convention | Preserved; EP critic still consumes `share_obs[:,0]` |
| Rollout-buffer compatibility | Shape changes only; same buffer type |
| Critic model migration | Critic input dim changes; action dim unchanged |
| Checkpoint migration | Requires new shared schema manifest/fingerprint |
| Field redundancy | High, because all actor task rows are repeated |
| Future variable M/N | Still fixed-shape MLP; broader architecture needed later |

### Option B: Compact global lifecycle block

Definition:

```text
shared observation =
legacy shared flat
+
all-robot active-target matrix
+
all-robot failed-pair matrix
+
exact active budget sufficient statistic
+
only other proven-required global lifecycle fields
```

Minimum compact lifecycle block under current invariants:

```text
active_target_matrix: [E,M,N]
failed_pair_matrix:   [E,M,N]
budget_statistic:     [E,M,2]
```

General dimension if no other global lifecycle fields are needed:

```text
shared_dim_B =
    M * (100 + 3M + 16N)
    + 2MN
    + 2M
```

For `M=3, N=50`:

```text
shared_dim_B =
    3 * 909 + 300 + 6 =
    3033
```

Evaluation:

| criterion | result |
|---|---|
| Markov sufficiency | Can be sufficient if every compact field and ordering is implemented correctly |
| Implementation complexity | Higher; new shared construction path separate from actor concat |
| Current HARL EP convention | Still possible, but no longer mirrors wrapper's actor-concat convention |
| Rollout-buffer compatibility | Shape change only, but more custom schema logic |
| Critic model migration | Critic input dim changes; field order differs from actor concat |
| Checkpoint migration | Requires separate actor and critic manifests |
| Field redundancy | Lower |
| Future variable M/N | Somewhat cleaner, but still fixed-shape unless architecture changes |

### Required Selection

Frozen first migration selection:

```text
Option A
```

Reason:

- It preserves the current HARL shared-observation structure.
- It automatically puts every actor-visible lifecycle field for every robot into the critic.
- It adds only one explicit critic-only block: exact active budget sufficient statistic.
- It minimizes wrapper, buffer, and checkpoint migration risk.
- Redundancy is acceptable for the first training-readiness migration.

Compact global critic state is deferred to a separate future architecture phase.

## 8. Frozen Available-Action Mask Contract

Action space remains:

```text
action dimension = N + 1
raw target ids = 0 ... N-1
raw noop id = N
decoded noop = -1
```

### Idle robot

Target `j` is available only if:

```text
valid task slot
physically feasible/available
uncovered
not owned by teammate
not failed/released for this same robot
```

Noop is always available.

### Executing robot with active target `k`

Only these raw actions are available:

```text
target k
noop raw id N
```

All `j != k` switch actions are masked.

Retained Contract C semantics:

```text
executing + target k = continue k
executing + noop = continue k
```

Do not mask noop.

If the current active target becomes physically unavailable or infeasible, the mask must still allow:

```text
target k
noop
```

Current resolver behavior does not release active targets on infeasibility. It emits diagnostics-only `active_target_infeasible_deferred` and continues the active target.

If a stale covered-active state is observed at a decision snapshot, that is an invariant/order violation to surface in validation. The mask must not silently invent a release policy.

### Simultaneous claims

Multiple idle actors may all see the same currently unowned target as available before joint action sampling.

Winner selection remains resolver-side:

```text
lowest cost
then robot-id tie-break
```

### Final safety boundary

The resolver must continue to reject:

- invalid ids;
- covered targets;
- ownership conflicts;
- same-robot failed/released pairs;
- executing switches;
- simultaneous claim losers;
- stale or inconsistent mask cases.

The mask defines the policy support and improves training stability. It does not replace resolver safety.

## 9. Immutable Atomic Snapshot Contract

Current wrapper ordering is procedural, not snapshot-object based:

```text
reset:
  env.reset()
  get_assignment_problem()
  reset wrapper diagnostics/budget
  reset resolver
  build actor obs
  build shared obs
  build available_actions

step:
  pre_step_problem = get_assignment_problem()
  pre_step_available_actions = build mask from pre_step_problem
  decode policy actions
  resolver resolve_pre_step()
  effective_assignment -> controller -> env.step()
  post_step_problem = get_assignment_problem()
  update wrapper diagnostics/budget from effective_assignment
  build budget diagnostics from wrapper info and effective_assignment
  resolver observe_post_step(), including done-env resolver reset
  reset wrapper diagnostics/budget for done envs
  build actor obs from post_step_problem and current wrapper state
  build shared obs
  build available_actions from post_step_problem
```

Frozen semantic decision-cycle ordering for lifecycle implementation:

```text
environment post-step
-> completion/budget signals collected
-> resolver observe_post_step
-> active/owner/pair state updated
-> done-environment reset
-> resolver and budget reset for done environments
-> immutable lifecycle decision snapshot captured
-> actor observation built
-> shared observation built
-> available_actions built
-> policy sampling
```

The implementation may use one immutable snapshot object or an equivalent immutable tensor bundle. The preferred design is a single immutable snapshot object.

Snapshot must contain at least:

```text
generation id
episode/reset identity
active targets
ownership
failed/released pair state
exact budget sufficient statistic
coverage/completion
physical feasibility/availability required by observation and mask
configured M/N/action/noop ids
```

Freeze this metadata name unless a clearly equivalent name is selected in implementation:

```text
lifecycle_snapshot_generation
```

Generation values are diagnostics metadata and must not be appended to actor network input.

Smoke assertions:

```text
actor_obs_generation
==
share_obs_generation
==
available_actions_generation
```

Also assert that snapshot tensors are not read separately from mutable resolver/wrapper/env state during the same policy decision.

## 10. PPO Historical Mask Replay Audit and Contract

Static trace:

| boundary | function/class | tensor | shape | dtype/device | copy/view | time index | agent index |
|---|---|---|---:|---|---|---|---|
| Env reset | `AssignmentIsaacLabEnv.reset()` | `available_actions` | `[E,M,N+1]` | torch float32, wrapper device | returned tensor | decision `t=0` | all agents |
| Warmup storage | `OnPolicyBaseRunner.warmup()` | `actor_buffer[i].available_actions[0]` | `[E,N+1]` | buffer device | `.clone()` | `t=0` | `i` |
| Sampling | `OnPolicyBaseRunner.collect(step)` | `actor_buffer[i].available_actions[step]` | `[E,N+1]` | buffer device -> actor device | buffer read | `t=step` | `i` |
| Policy mask application | `StochasticPolicy.forward()` -> `ACTLayer.forward()` -> `Categorical.forward()` | `available_actions` | `[E,N+1]` | checked to actor device float32 | used in logits | `t=step` | per actor |
| Logit masking | `Categorical.forward()` | logits where mask == 0 | `[E,N+1]` | torch | in-place logits set to `-1e10` | `t=step` | per actor |
| Env step result | `AssignmentIsaacLabEnv.step()` | next `available_actions` | `[E,M,N+1]` | torch float32 | returned tensor | `t+1` | all agents |
| Buffer insert | `OnPolicyBaseRunner.insert()` -> `OnPolicyActorBuffer.insert()` | `available_actions[:,i]` | `[E,N+1]` | buffer device | `.clone()` | stored at `step+1` | `i` |
| Feed-forward generator | `OnPolicyActorBuffer.feed_forward_generator_actor()` | `self.available_actions[:-1]` | `[T*E,N+1]` then minibatch | buffer device | reshape then indexed | historical `t` | per actor buffer |
| Naive recurrent generator | `OnPolicyActorBuffer.naive_recurrent_generator_actor()` | `self.available_actions[:-1, ids]` | flattened `[T*num_envs_per_batch,N+1]` | buffer device | `_flatten` | historical `t` | per actor buffer |
| Recurrent generator | `OnPolicyActorBuffer.recurrent_generator_actor()` | `_sa_cast(self.available_actions[:-1])` | chunked then flattened | buffer device | transpose/reshape/chunk stack | historical chunks | per actor buffer |
| PPO/HAPPO update | `HAPPO.update()` | `available_actions_batch` | minibatch `[B,N+1]` | actor device after `check()` | sample tensor | historical `t` | per actor |
| Actor evaluation | `OnPolicyBase.evaluate_actions()` -> `StochasticPolicy.evaluate_actions()` -> `ACTLayer.evaluate_actions()` | `available_actions_batch` | `[B,N+1]` | actor device float32 | used directly | historical `t` | per actor |
| Old log-prob | actor buffer | `old_action_log_probs_batch` | `[B,act_shape]` | actor device | stored from sampling | historical `t` | per actor |

HATRPO and HAA2C also pass `available_actions_batch` from the actor buffer into `evaluate_actions()` in their update paths.

Frozen PPO/HARL contract:

```text
sampling available_actions[t]
==
buffer available_actions[t]
==
evaluate_actions available_actions[t]
```

PPO update must not regenerate historical lifecycle masks from current resolver state.

Required future smoke coverage:

- feed-forward actor generator;
- naive recurrent actor generator;
- recurrent actor generator;
- recurrent chunk boundaries;
- mini-batch shuffling;
- HAPPO update path;
- HATRPO update path if enabled for assignment runs;
- HAA2C update path if enabled for assignment runs;
- save/load/resume startup followed by fresh warmup mask storage.

Checkpoint save/load does not preserve rollout buffers in current HARL. Resume starts a fresh rollout after env reset, so resume validation must verify fresh mask generation and storage, not historical buffer restoration.

## 11. Legacy Guardrail Freeze

Current guardrails and behavior sources:

| mechanism | current source fields | behavior effect | official lifecycle profile decision |
|---|---|---|---|
| Legacy cooldown action-mask suppression | `_per_robot_target_cooldown_remaining`, `assignment_cooldown_apply_to_action_mask` | Masks targets before policy sampling | Disable mask overlay |
| Redirect guardrail | `_assignment_redirect_guardrail_remaining`, `_assignment_redirect_guardrail_triggered_target`, previous assignments, spacing/claimed diagnostics | Masks claimed/nearby targets after budget trigger | Disable |
| Legacy failed-pair TTL memory | `_assignment_failed_pair_memory_remaining`, `_assignment_failed_pair_memory_trigger_step` | Masks same robot-target pairs for TTL | Disable |
| Resolver failed-pair state | `pair_state == FAILED_BUDGET/RELEASED_BUDGET` | Episode-persistent same-pair rejection | Keep as sole failed-pair behavior |
| Budget tracker / trigger | `_budget_attempt_*`, `_last_budget_triggered_by_budget` | Emits resolver budget-failure/release signal | Keep as resolver release source |

Frozen first official resolver-enabled training profile:

```text
KEEP:
  budget tracker / trigger only as the source of resolver budget release
  shared AssignmentLifecycleResolver
  Contract C
  resolver episode-persistent failed-pair rejection

DISABLE:
  legacy cooldown action-mask suppression overlay
  redirect guardrail
  legacy failed-pair TTL eligibility memory
```

Concrete profile intent:

```text
assignment_cooldown_enabled = True
assignment_cooldown_trigger_mode = "budget"
assignment_cooldown_apply_to_action_mask = False
assignment_redirect_guardrail_enabled = False
assignment_failed_pair_memory_enabled = False
assignment_lifecycle_resolver_enabled = True
```

The exact budget multiplier, slack, and budget-candidate gates are part of the budget-release contract and checkpoint manifest.

Explicit prohibition:

```text
legacy failed-pair TTL mask
and
resolver episode-persistent failed-pair rejection
must not be simultaneous behavior owners
```

Any future re-enabled guardrail must have its own hidden-state audit, observation destination, mask effect, snapshot timing, checkpoint metadata, and validation gate.

## 12. Configuration Design

Comparison:

| design | benefit | risk | decision |
|---|---|---|---|
| Independently configurable contract versions | Flexible for diagnostics | Many illegal combinations; easy to silently train with hidden state | Not the normal user path |
| High-level profiles plus internally resolved immutable contracts | Smaller user surface, easier validation, clearer checkpoint metadata | Requires profile resolver and startup validation | Selected |

Selected design:

```text
user-facing high-level profile
+
internally resolved immutable contract versions
```

Profiles:

| profile | observation schema | shared schema | resolver | mask contract | budget-release contract | legacy guardrail profile | training allowed? | evaluation allowed? | checkpoint resume allowed? |
|---|---|---|---|---|---|---|---|---|---|
| `legacy` | `legacy_v1` | legacy actor concat | disabled | legacy physical/noop mask; current explicit legacy settings only | none for resolver | legacy defaults/exact legacy config | Yes for legacy training | Yes | Only exact metadata match; unversioned legacy resume prohibited by default |
| `lifecycle_ablation` | `lifecycle_v1_actor_3n` | Option A shared plus budget block, resolver-disabled values | disabled | explicit ablation mask contract | disabled or exact ablation budget contract | no implicit resolver-on guardrails | Explicit ablation only, not normal | Yes, explicit ablation/evaluation only | Only if checkpoint was trained under exact same ablation fingerprint |
| `lifecycle_contract_c` | `lifecycle_v1_actor_3n` | `lifecycle_v1_shared_option_a_budget2m` | enabled | `lifecycle_contract_c_mask_v1` | `budget_release_v1` | `lifecycle_no_legacy_guardrails_v1` | Only after full training-readiness gate | Yes after validation | Yes only exact fingerprint |
| `diagnostics_hidden_state` | legacy or explicit diagnostic schema | diagnostic only | optional | diagnostic only | diagnostic only | diagnostic only | No | Bounded diagnostics only | No normal checkpoint save/resume |

Low-level override fields may remain for diagnostics, but startup validation must resolve and validate them against a profile. Normal training/evaluation should not be driven by free combinations of booleans.

## 13. Legal / Illegal Configuration Matrix

| combination | classification | decision |
|---|---|---|
| Resolver enabled + legacy observation | Hard error | Training/evaluation cannot hide resolver state |
| Lifecycle mask + legacy observation | Hard error | Mask uses lifecycle state actor cannot observe |
| Resolver disabled + legacy observation | Normal legacy training/evaluation | Old legacy path preserved |
| Resolver disabled + lifecycle observation | Explicit ablation/evaluation only unless exact lifecycle-ablation training profile | Shape compatibility is not contract compatibility |
| Legacy checkpoint + legacy mode | Legacy playback/evaluation only for unversioned; exact metadata required for resume | Supported with resolver disabled and exact shape/action/noop |
| Legacy checkpoint + lifecycle schema | Hard error | Shape/contract mismatch |
| Legacy checkpoint + resolver enabled | Hard error for normal playback/evaluation/training | No hidden/fabricated lifecycle state |
| Lifecycle checkpoint + resolver disabled | Explicit ablation/evaluation only unless originally trained under exact resolver-disabled lifecycle profile | Never infer resume legality from shape compatibility |
| Lifecycle checkpoint + resolver enabled | Normal lifecycle evaluation/training resume only after gate and exact fingerprint | Supported future path |
| Checkpoint metadata missing | Legacy playback/evaluation only under explicit `legacy` profile, resolver disabled, exact shapes | No default training resume |
| Schema fingerprint mismatch | Hard error for resume; explicit evaluation only if compatibility validator allows | Prevent silent field-order drift |
| Mask contract mismatch | Hard error for resume; explicit ablation/evaluation only if allowed | PPO support changed |
| Guardrail profile mismatch | Hard error for resume | Behavior source changed |
| Budget-release contract mismatch | Hard error for resume | Transition rule changed |
| `M`/`N` mismatch | Hard error | MLP input/action dimensions and semantics differ |
| Action dimension mismatch | Hard error | Policy head incompatible |
| Noop raw id mismatch | Hard error | Action semantics differ |
| Noop decoded value mismatch | Hard error | Resolver/controller semantics differ |
| Resolver mode differs from training-time profile | Hard error for resume; explicit ablation/evaluation only if declared | Contract changed |

Required hard boundaries are frozen exactly as above.

## 14. Checkpoint Manifest and Fingerprint Contract

Each new checkpoint must include an ordered schema manifest.

Minimum manifest fields:

```text
profile_name

actor_schema_version
actor_ordered_feature_manifest
actor_task_row_field_ordering
actor_dimension

shared_schema_version
shared_construction_mode
shared_ordered_feature_manifest
shared_dimension

feature_dtype
feature_normalization
feature_source
feature_snapshot_timing
padding_semantics

snapshot_contract_version
resolver_contract_version
mask_contract_version
budget_release_contract_version
legacy_guardrail_profile

M
N
action_dimension
noop_raw_id
noop_decoded_value

training_time_resolver_state
training_time_profile
HARL_state_type
HARL_shared_observation_mode
```

Feature entries must preserve order:

```text
name
source
shape
dtype
normalization
snapshot_timing
padding_semantics
```

Stable fingerprint:

```text
canonical JSON manifest
+
SHA-256
```

Canonicalization rule:

- Object keys may be sorted for stable JSON.
- Ordered lists, especially feature lists and task-row field lists, must retain their list order.
- The fingerprint is generated metadata, not a user-entered bypass value.

Compatibility distinctions:

| compatibility kind | meaning | requirement |
|---|---|---|
| Structural load compatibility | PyTorch shapes can load | Necessary but not sufficient |
| Evaluation/ablation compatibility | Intentional cross-contract evaluation | Requires explicit profile permission |
| Training-resume compatibility | Same observation, transition, mask, budget, guardrail, action, M/N contract | Requires exact fingerprint unless an explicit future migration policy exists |

Compatibility decision pseudocode:

```text
env_manifest = build_current_manifest(profile, env, algo_args)
ckpt_manifest = find_checkpoint_manifest(model_dir)

if ckpt_manifest is missing:
    if profile == "legacy"
       and resolver disabled
       and legacy mask
       and actor/critic/action/noop shapes match:
        allow legacy playback/evaluation only
        disallow training resume
    else:
        hard error

ckpt_fingerprint = sha256(canonical_json(ckpt_manifest))
env_fingerprint = sha256(canonical_json(env_manifest))

if structural shapes mismatch:
    hard error

if mode == "training_resume":
    require ckpt_fingerprint == env_fingerprint
    require training_time_profile == current profile
    require resolver/mask/budget/guardrail contracts equal
    otherwise hard error

if mode == "normal_evaluation":
    require ckpt_fingerprint == env_fingerprint
    otherwise hard error

if mode == "explicit_ablation_evaluation":
    require structural compatibility
    require validator-approved profile transition
    record source and target manifests in output
    otherwise hard error
```

Metadata discovery:

```text
model_dir/assignment_contract_manifest.json
model_dir/assignment_contract_fingerprint.txt
model_dir.parent/assignment_contract_manifest.json
model_dir.parent/assignment_contract_fingerprint.txt
```

For `models/` and `best_model/`, loaders must search the checkpoint directory and then the run root parent. If both `models/` and `best_model/` exist, each checkpoint directory may contain a copy, but the run-root manifest is the authoritative fallback if it matches.

All loaders must use one project-level compatibility validator before state-dict loading:

- training restore in `AssignmentOnPolicyHARunner` / inherited HARL restore path;
- manual RL playback actor loading;
- comparison-method actor loading;
- `models/`;
- `best_model/`;
- checkpoint subdirectories if enabled later.

Do not rely on PyTorch shape mismatch, HARL warning prints, silent observation slicing, partial load, zero-fill, or truncation as schema validation.

Old unversioned checkpoints:

```text
support only explicit legacy profile
resolver disabled
legacy mask
exact actor/critic/action/noop shape
legacy playback/evaluation
```

Default training resume for unversioned legacy checkpoints is prohibited unless a separate explicit legacy-resume policy is approved later.

## 15. Revised Training-Readiness Gate

Resolver-enabled training remains illegal until all are later implemented and validated:

1. Frozen `lifecycle_v1` actor schema is implemented.
2. Frozen shared-observation Option A is implemented.
3. Exact two-scalar budget sufficient statistic is present in critic/shared input.
4. Actor/shared/mask use one immutable snapshot generation.
5. Lifecycle Contract C mask is implemented.
6. Sampling-time `available_actions` are stored in the rollout buffer.
7. PPO/HARL `evaluate_actions` reuses the stored historical mask.
8. Feed-forward and recurrent generator mask alignment pass.
9. Official lifecycle profile disables unaudited legacy guardrails.
10. Ordered schema manifest and stable fingerprint are saved.
11. All loaders enforce structural/evaluation/resume compatibility.
12. Resolver-disabled legacy observation/mask identity remains exact.
13. Invalid configuration combinations fail at startup.
14. Actor/critic/buffer forward-backward shape smokes pass.
15. Checkpoint save/load/resume smokes pass.
16. Bounded resolver-enabled snapshot/mask consistency validation passes.
17. Only then may a very short resolver-enabled training smoke run.

No runtime validation from this list was performed in Phase 9G-8B.

## 16. Explicitly Deferred Topics

Deferred and not allowed to change frozen Contract C:

- active-target infeasibility release;
- failed-pair TTL;
- retry eligibility;
- retry policy;
- stranded-task recovery;
- explicit abort/switch/release action;
- explicit continue action redesign;
- failure/release reason actor features;
- Transformer/GNN implementation;
- true variable M/N policy architecture;
- compact critic implementation under Option B;
- owner-id or owner-one-hot actor features.

## 17. Revised Follow-On Phase Plan

Phase 9G-8C: Pure Lifecycle Snapshot and Tensor Builders

- Allowed changes: immutable snapshot data contract, actor 3N lifecycle task-row builder, critic two-scalar budget statistic builder, generation validation, pure tensor/invariant tests.
- Forbidden changes: HARL observation integration, mask integration, checkpoint loader integration, training, playback, evaluation, resolver behavior changes.
- Required evidence: pure tensor shape checks, ownership-active invariant checks, budget statistic exactness checks, generation metadata checks.
- Training/playback/evaluation: not allowed.

Phase 9G-8D: Lifecycle Actor/Shared Observation Integration

- Allowed changes: `legacy_v1` exact isolation, `lifecycle_v1` actor integration, Option A shared integration, observation spaces, snapshot ordering, schema manifest generation.
- Forbidden changes: lifecycle mask integration unless explicitly scoped, checkpoint resume, training, playback/evaluation sweeps, resolver behavior changes.
- Required evidence: reset/step observation shape checks, shared dimension checks, manifest/fingerprint generation checks, disabled legacy identity checks.
- Training/playback/evaluation: no training; only bounded non-playback shape/runtime smokes if explicitly scoped.

Phase 9G-8E: Lifecycle Mask and PPO Historical-Mask Replay Integration

- Allowed changes: Contract C mask, same-snapshot validation, rollout available-actions storage assertions, generator/evaluate_actions mask replay checks, resolver final boundary assertions.
- Forbidden changes: checkpoint compatibility implementation beyond mask metadata, training, playback/evaluation sweeps, action dimension changes.
- Required evidence: mask/resolver consistency, feed-forward/naive recurrent/recurrent historical mask replay smokes.
- Training/playback/evaluation: no training; no formal playback/evaluation.

Phase 9G-8F: Checkpoint / Loader / Buffer / Forward-Backward Readiness

- Allowed changes: manifest/fingerprint validator, all model loaders, actor/critic construction guards, rollout buffer guards, synthetic forward/backward smoke, checkpoint save/load compatibility matrix.
- Forbidden changes: formal environment training, long simulation, performance evaluation, resolver behavior changes.
- Required evidence: invalid combination hard errors, structural/evaluation/resume compatibility checks, forward/backward shape smoke, checkpoint save/load smoke.
- Training/playback/evaluation: no formal training; synthetic or minimal non-environment smokes only unless explicitly scoped.

Phase 9G-8G: Bounded Runtime Lifecycle Validation

- Allowed changes: validation scripts/reports if needed, bounded resolver-disabled and resolver-enabled runtime validation.
- Forbidden changes: training, performance evaluation, new behavior semantics, retry/TTL/infeasibility release.
- Required evidence: resolver-disabled legacy exact identity, resolver-enabled snapshot consistency, budget progress consistency, mask/resolver consistency, reset ordering, passive diagnostics coexistence.
- Training/playback/evaluation: no training; bounded runtime validation only as scoped.

Phase 9G-8H: Very Short Resolver-Enabled Training and Checkpoint Smoke

- Allowed changes: minimal smoke configuration or scripts if needed, very short training/checkpoint smoke after prior gates pass.
- Forbidden changes: long training, hyperparameter tuning, performance claims, formal comparison.
- Required evidence: buffer insertion, historical mask replay, actor/critic optimizer step, save/load/resume, invalid checkpoint hard-error validation.
- Training/playback/evaluation: very short training smoke allowed; no performance evaluation.

Phase 9G-8I: Commit-Readiness Review

- Allowed changes: review report and progress update.
- Forbidden changes: implementation changes unless a specific defect fix is requested.
- Required evidence: default-off legacy identity, single lifecycle behavior source, frozen schema/fingerprint, frozen mask replay contract, checkpoint boundaries, training-readiness evidence, no retry/TTL/infeasibility-release scope drift.
- Training/playback/evaluation: no new runtime runs unless a specific inconsistency requires it.

Phase 9G-8C may begin only after this Phase 9G-8B report is reviewed and accepted.

## Frozen Final Recommendation

```text
CONTRACT-FREEZE READY
```

Freeze the first lifecycle training-readiness migration as:

```text
actor schema:
  lifecycle_v1_actor_3n
  per-task row adds:
    self_active_target
    task_owned_by_teammate
    self_pair_failed_or_released
  lifecycle_actor_dim = 100 + 3M + 19N
  M=3,N=50 -> 1059

shared schema:
  Option A
  concat(all revised lifecycle actor observations)
  + exact two-scalar active budget statistic per robot
  shared_dim = M * (100 + 3M + 19N) + 2M
  M=3,N=50 -> 3183

budget statistic:
  active_budget_progress_norm
  active_budget_step_fraction

mask:
  action_dim = N + 1
  noop raw id = N
  decoded noop = -1
  idle target requires physical availability, uncovered, not teammate-owned, not self failed/released
  executing robot allows only current target and noop

profiles:
  legacy
  lifecycle_ablation
  lifecycle_contract_c
  diagnostics_hidden_state

checkpoint:
  ordered canonical JSON manifest
  SHA-256 fingerprint
  project-level compatibility validator before all state-dict loads

training:
  resolver-enabled training remains prohibited until the revised 17-point gate passes
```
