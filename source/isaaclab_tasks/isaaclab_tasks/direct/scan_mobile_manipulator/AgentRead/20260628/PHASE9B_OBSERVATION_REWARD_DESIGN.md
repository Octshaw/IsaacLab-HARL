# Phase 9B Observation And Reward Design

Date: 2026-06-28

## Scope

This is Phase 9B-0: design document only.

It does not modify Python code. It does not start RL training. It does not start formal RL evaluation. It does not
change solver behavior, controller logic, HARL internals, environment dynamics, `available_mask`, `feasible_mask`, or
`static_geometric_feasible_mask`.

The near-term target is a fixed-scale assignment policy for:

```text
N = 50 viewpoints
M = 3 robots
action ids = 0..49 for viewpoints, 50 for noop
```

The long-term target remains dynamic multi-robot task allocation for arbitrary-size viewpoint sets and variable robot
counts.

## Starting Point From Phase 9A

Phase 9A found that shape-level RL plumbing is ready for N=50, M=3:

```text
available_actions shape = [num_envs, 3, 51]
available_mask shape = [num_envs, 3, 50]
cost_matrix shape = [num_envs, 3, 50]
noop_id = 50
```

But the current observation and reward are not yet strong enough for meaningful dynamic-policy evaluation. The main
semantic gap is:

```text
policy action j means absolute viewpoint id j
current nearest-viewpoint observation slots do not include viewpoint ids
```

For a fixed N=50 MLP-style policy, every action logit must have an id-aligned feature row that describes the same
viewpoint id.

## Design Principles

1. Keep masks for hard validity only.
2. Put soft preferences and trade-offs into observation, reward, and reporting.
3. Report new diagnostics before promoting them into reward.
4. Keep all fixed-N feature rows ordered exactly like the action ids.
5. Preserve the Phase 8 diagnostics as comparison metrics, not as automatic solver rules.
6. Avoid adding handcrafted fallback behavior while designing RL signals.

## Observation Design For Fixed N=50, M=3

The Phase 9B fixed-scale observation should be explicit rather than nearest-slot-only. A practical first design is a
flattened MLP observation with these groups.

### Per-Agent Local State

Keep the current local state fields:

| field | shape per agent | purpose |
|---|---:|---|
| base position relative to env origin | 3 | robot base location |
| base yaw sin/cos | 2 | heading without angle wrap |
| scanner position | 3 | current scanner location |
| scanner quaternion | 4 | scanner orientation |
| capability summary | 4 | reach, sensor min/max range, FOV |
| previous 9D low-level action | 9 | motion smoothness and recent command context |

Add assignment-specific local state:

| field | shape per agent | purpose |
|---|---:|---|
| previous assignment id one-hot including noop | 51 | links the last discrete decision to current outcome |
| consecutive same-target count, normalized | 1 | repeated assignment context |
| own steps since last coverage gain, normalized | 1 | no-progress context |
| own completed viewpoint count, normalized by N | 1 | load-balance state |
| own selected viewpoint count, normalized by episode step | 1 | workload / noop interpretation |

The previous 9D low-level action should remain useful for execution dynamics, but it is not a replacement for previous
assignment id.

### Id-Aligned Viewpoint Table

Add a full id-aligned table with one row for each viewpoint id `j in 0..49`. The row order must be identical to action
ids. After flattening, row `j` describes action `j`.

Recommended per-viewpoint fields for each agent:

| field | shape per viewpoint | notes |
|---|---:|---|
| relative viewpoint position from this scanner | 3 | normalized by env spacing |
| viewpoint quaternion or orientation error features | 4 or compact delta | use current quat initially for continuity |
| current cost for this robot to this viewpoint | 1 | normalized distance from `cost_matrix[:, agent, j]` |
| available mask for this robot | 1 | duplicate of action mask as observation context |
| feasible mask for this robot | 1 | distinguishes infeasible from covered when combined with covered |
| static geometric feasible mask | 1 | separate long-term geometry feasibility |
| covered flag | 1 | full task completion vector |
| task status code, normalized or one-hot | 1 to 4 | start with compact completed/unassigned if only two statuses are live |
| per-viewpoint attempted count, normalized | 1 | repeated target memory |
| per-viewpoint last attempted age, normalized | 1 | stale/retry context |
| per-viewpoint completed-by robot id, optional | 0 to M | reporting first; include only if stable |
| selected-by-other-last-step count | 1 | duplicate/conflict context without hard masking |
| selected-target conflict risk proxy | 1 | distance-to-other-selected-target risk, reporting validated first |
| obstacle/crossing diagnostic risk proxy | 1 | diagnostic feature candidate, not reward at first |

For the first fixed-N implementation, prefer a clear full table even if it is larger than the current compact 96D
observation. The cost of a larger MLP input is acceptable for N=50 and M=3, and the clarity is valuable.

### Global Task State

Include global fields available to every agent:

| field | shape | purpose |
|---|---:|---|
| global coverage ratio | 1 | keep current scalar |
| covered vector | 50 | lets the policy see which actions are already done |
| steps since last global coverage gain, normalized | 1 | plateau detection |
| episode progress, normalized | 1 | time-aware decisions and late-stage behavior |
| remaining available count per robot, normalized | 3 | endgame feasibility context |
| total uncovered count, normalized | 1 | completion pressure |

### Multi-Robot Context

For M=3, include compact pairwise and assignment-memory features:

| field | shape per agent | purpose |
|---|---:|---|
| other scanner positions relative to this scanner | `(M - 1) * 3` | keep current geometry context |
| other previous assignment ids one-hot including noop | `(M - 1) * 51` | tells the policy what others recently chose |
| other completed counts, normalized | `M - 1` | load balance |
| pairwise scanner distance / footprint clearance proxies | `M - 1` | overlap risk context |
| pairwise previous-base motion crossing flags, reporting-derived | `M - 1` | candidate observation after diagnostic validation |

For simultaneous decentralized actors, current actions of other robots are not known at action-selection time. Previous
assignment memory and centralized critic state are therefore the right first step. Duplicate selected target should be
penalized or reported after the joint action is sampled, not masked preemptively.

### Centralized Critic State

The critic can receive a larger shared state than the actor:

```text
all per-agent local states
all id-aligned viewpoint tables or a shared global viewpoint table
full [M, N] cost matrix
full [M, N] available/feasible/static masks
per-robot completed/selected/repeated/no-progress counters
Phase 8 diagnostic counters, while still reporting-only
```

This keeps the actor observation practical while letting the critic learn team-level credit assignment.

## Aligning Absolute Viewpoint Action Ids With Observation Features

The fixed N=50 policy should enforce these invariants:

```text
action 0  <-> viewpoint feature row 0
action 1  <-> viewpoint feature row 1
...
action 49 <-> viewpoint feature row 49
action 50 <-> noop feature block
```

The loaded `viewpoint_ids` order should define the action order. If the CSV order changes, the observation row order
and action ids must change together. Do not sort one and not the other.

Recommended fixed-N representation:

```text
actor_obs_i =
  local_robot_state_i
  global_task_state
  flatten(viewpoint_rows_i[0:50])
  multi_robot_context_i
  noop_context_i
```

The noop action should also have explicit context features, even if it is not part of the 50-row viewpoint table:

| noop feature | purpose |
|---|---|
| any available viewpoint for this robot | distinguishes necessary noop from useless noop |
| all robots have no available viewpoints | team terminal/stuck context |
| previous action was noop | noop repetition context |
| episode progress | late-stage waiting vs early inactivity |

The current nearest-8 viewpoint slots can be kept temporarily as auxiliary features, but they should no longer be the
only action-relevant viewpoint representation. If retained, each nearest slot must include the absolute viewpoint id
or a one-hot/id-normalized encoding so the policy can associate the slot with the correct action logit.

## Mask Versus Reward And Observation

### Keep In Action Masks

Action masks should represent hard validity:

| mask condition | reason |
|---|---|
| viewpoint is already covered | selecting it cannot create new task progress |
| viewpoint is infeasible for this robot | static/manual feasibility says the robot cannot cover it |
| future padding rows for arbitrary N | padded viewpoints are not real actions |
| strict out-of-range action ids | runner/policy bug, not a learnable choice |

For the current system, noop remains always available. Any future change to noop availability should be a separate,
explicitly scoped mask-policy change.

### Do Not Put In Action Masks Yet

These should remain observation/reward/reporting concepts rather than hard masks:

| concept | why it should not be a mask initially |
|---|---|
| duplicate selected target | simultaneous team coordination problem; useful learning signal |
| repeated assignment | sometimes a retry/dwell may be valid; needs context |
| no-progress state | should shape behavior, not erase actions |
| path cost | soft optimization trade-off against coverage |
| load balance | soft team objective |
| selected-target conflict | proxy metric with trade-offs seen in Phase 8 |
| inter-robot overlap | diagnostic/proxy risk, not hard physical collision |
| actual base-motion crossing | approximate XY diagnostic; promote carefully |
| obstacle-aware cost | diagnostic-only until separately scoped |

This separation prevents the mask from becoming a handcrafted solver.

## Reward Candidates

Reward terms should be introduced in stages. All new terms need reporting-only counters before they affect reward.

### Coverage Gain

Keep coverage as the primary positive signal:

```text
R_coverage =
  alpha_global * newly_covered_count
  + alpha_own * own_new_coverage_credit
```

Notes:

- Keep team coverage large enough to make completion the dominant objective.
- Keep own credit for decentralized assignment credit assignment.
- Continue splitting own credit when multiple robots scan the same newly covered viewpoint.

### Repeated Assignment

Candidate penalty:

```text
R_repeat =
  - beta_repeat * repeated_valid_same_target_without_new_coverage
```

Recommended gating:

- apply only to non-noop actions;
- apply only after a grace window compatible with dwell/scan completion;
- apply when the same robot repeatedly selects the same viewpoint and no new coverage follows;
- track per-robot and per-viewpoint counters separately.

This addresses the Phase 8 late pattern:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

### No-Progress

Candidate penalty:

```text
R_no_progress =
  - beta_no_progress * max(0, steps_since_last_global_gain - grace) / horizon
```

Notes:

- team-level no-progress should be visible to all agents;
- use a grace window so the policy is not punished during normal travel/dwell;
- consider a capped ramp to avoid swamping coverage reward late in the episode.

### Duplicate Selected Target

Candidate penalty:

```text
R_duplicate_target =
  - beta_duplicate * duplicate_non_noop_selected_target_count
```

Definition:

```text
duplicate_non_noop_selected_target_count =
  sum over viewpoints max(0, selected_robot_count(viewpoint) - 1)
```

This is different from duplicate scan penalty. Duplicate selected target happens at assignment time; duplicate scan is
detected at scan-completion time.

### Useless Noop

Candidate penalty:

```text
R_useless_noop =
  - beta_noop * noop_when_available_useful_target_exists
```

Do not penalize noop when:

- this robot has no available feasible uncovered viewpoint;
- the episode is effectively complete;
- a future robot-status model marks the robot unavailable, blocked, or waiting.

Because noop is always available today, this term should be introduced only after reporting shows noop abuse or a clear
policy need.

### Path Cost

Candidate shaping:

```text
R_path =
  - beta_path * normalized_selected_cost
```

Safer alternative:

```text
R_path_advantage =
  - beta_path * (selected_cost - best_available_cost_for_robot) / cost_scale
```

Notes:

- keep this small relative to coverage gain;
- path cost should not recreate a nearest-neighbor handcrafted policy;
- report selected cost distributions before reward promotion.

### Load Balance

Candidate penalty:

```text
R_load =
  - beta_load * variance(per_robot_completed_count / max(1, team_completed_count))
```

Alternative:

```text
R_load =
  - beta_load * (max_completed_count - min_completed_count) / N
```

Notes:

- report before reward;
- completed count is preferable to selected count, but selected count can reveal workload skew;
- avoid forcing balance when feasibility genuinely differs by robot.

### Selected-Target Conflict

Candidate penalty:

```text
R_selected_conflict =
  - beta_target_conflict * count(pairwise selected target distance < threshold)
```

Notes:

- use only for non-noop pairs;
- do not hard-mask conflicts;
- Phase 8 showed this metric can improve while actual crossing worsens, so promote cautiously.

### Inter-Robot Overlap

Candidate penalty:

```text
R_overlap =
  - beta_overlap * current_or_post_step_proxy_overlap_count
```

Notes:

- report current overlap and post-step overlap separately if possible;
- this remains proxy geometry, not full collision checking;
- should not override coverage until the metric is stable.

### Actual Base-Motion Crossing

Candidate penalty:

```text
R_crossing =
  - beta_crossing * actual_base_motion_component_crossing_event_count
```

Notes:

- keep reporting-only first because it is an approximate XY proxy;
- use post-step actual motion segments, not selected assignment lines;
- Phase 8 showed conflict-aware target choices increased this metric, so it is important but sensitive.

## Reporting-Only Metrics Before Reward Promotion

These metrics should be added to logs before being used in reward:

| metric | reporting-only reason | promotion condition |
|---|---|---|
| per_robot_completed_count | needed for load balance; currently absent | stable counts match coverage events |
| per_robot_selected_count | distinguishes workload from completion | useful skew signal over multiple runs |
| per_robot_repeated_assignment_count | needed for repeat penalty | repeat definition does not penalize valid dwell |
| per_viewpoint_attempted_count | needed for stuck target detection | aligns with assignment history |
| steps_since_last_global_coverage_gain | no-progress signal | grace window calibrated against normal travel/dwell |
| duplicate selected target count | assignment-time team conflict | distinct from duplicate scan count |
| noop_when_available_count | useless noop signal | only penalize if harmful noop behavior appears |
| selected path cost distribution | cost shaping calibration | cost normalization stable across episodes |
| selected-target conflict rate | Phase 8 comparison metric | stable threshold and no adverse crossing trade-off |
| inter-robot overlap rate | proxy safety metric | stable proxy clearance semantics |
| actual base-motion crossing rate | approximate XY execution metric | validated as robust enough for shaping |
| selected obstacle intersection rate | diagnostic-only obstacle metric | only after a separate obstacle-reward scope |

Coverage metrics are already reward-relevant, but they should still remain in reporting:

```text
final_coverage
coverage_auc
success_rate
last_coverage_gain_step
no_progress_steps_after_last_gain
final_uncovered_viewpoint_ids
```

## Staged Implementation Plan

### Phase 9B-0: Design Doc Only

Status of this document:

```text
design only
no Python changes
no RL training
no formal RL evaluation
no solver/controller/HARL/environment/mask changes
```

Exit criteria:

- observation fields are defined;
- action-id alignment is specified;
- mask versus reward responsibilities are separated;
- reward candidates are staged;
- reporting-only metrics are listed;
- arbitrary-N transition path is documented.

### Phase 9B-1: Reporting-Only Counters

Scope:

```text
add counters/logging only
do not change reward
do not change masks
do not change solver behavior
do not change controller logic
do not train
```

Recommended counters:

```text
per_robot_completed_count
per_robot_selected_count
per_robot_repeated_assignment_count
per_viewpoint_attempted_count
steps_since_last_global_coverage_gain
duplicate selected target count
noop_when_available_count
selected path cost summaries
load balance summaries
```

Validation:

- run only small deterministic smoke/evaluator checks when scoped;
- compare counters against existing assignment history and coverage summaries;
- keep Phase 8 diagnostics unchanged.

### Phase 9B-2: Observation Update Smoke

Scope:

```text
add fixed N=50, M=3 observation fields
keep action ids unchanged
keep available_actions unchanged
keep reward unchanged
do not train
do not run formal RL evaluation
```

Required smoke checks:

```text
num_agents = 3
num_viewpoints = 50
noop_id = 50
actor observation has id-aligned viewpoint rows
row j corresponds to action id j
available_actions shape remains [num_envs, 3, 51]
available_mask shape remains [num_envs, 3, 50]
covered/infeasible/noop semantics remain unchanged
```

The smoke should include a row-alignment assertion for a known viewpoint id.

### Phase 9B-3: Reward Implementation Smoke

Scope:

```text
introduce selected reward terms behind explicit config switches
default all new reward terms conservatively
do not start training
do not run formal RL evaluation
```

Recommended first reward smoke order:

1. coverage reward unchanged as baseline.
2. duplicate selected target penalty.
3. repeated assignment penalty with dwell/grace gating.
4. no-progress penalty with capped ramp.
5. useless noop penalty only if reporting shows noop abuse.
6. path/load/conflict/overlap/crossing shaping only after reporting is stable.

Validation:

- one-step or short scripted episodes only;
- verify signs and magnitudes of reward terms;
- verify reward logs decompose total reward clearly;
- verify no mask, solver, controller, or dynamics behavior changed accidentally.

## Future Transition To Arbitrary-N / Variable-M Policies

The fixed N=50 MLP design is a bridge, not the final representation.

### Fixed-N Bridge

Use a flattened table because it directly fixes the Phase 9A action-id mismatch:

```text
flattened viewpoint row j -> action logit j
fixed noop block -> action logit N
```

This is appropriate for N=50, M=3 smoke and early ablation work.

### Arbitrary-N Set / Transformer / GNN Path

The future policy should replace flattened id-aligned rows with permutation-aware tokens:

| component | future representation |
|---|---|
| viewpoint state | one token per viewpoint |
| robot state | one token per robot |
| robot-viewpoint relation | edge features: cost, feasibility, visibility, history |
| robot-robot relation | edge features: distance, overlap risk, crossing history |
| action logits | pointer-style logits over viewpoint tokens plus noop |
| mask | token mask over real feasible uncovered viewpoints plus noop |
| critic | pooled global set state with robot/viewpoint/edge aggregation |

Important properties:

- permutation equivariant over viewpoint ordering;
- supports variable N by padding or ragged batching;
- supports variable M with robot tokens and pooling;
- preserves hard masks as masks, not as hidden solver rules;
- keeps diagnostic/reward terms modular.

Possible architectures:

```text
Transformer encoder over robot and viewpoint tokens
bipartite robot-viewpoint attention
GNN with robot nodes, viewpoint nodes, and typed edges
set encoder for viewpoints plus cross-attention from each robot actor
```

Migration path:

1. Stabilize fixed N=50 observation/reward counters.
2. Train or smoke-test fixed-N policy only when explicitly scoped.
3. Convert viewpoint rows into tokens while keeping the same feature meanings.
4. Replace fixed action head with per-token/pointer logits.
5. Validate identical behavior on N=50 ordering before testing shuffled N=50.
6. Test variable N with padding masks.
7. Add variable M after robot-token batching and critic pooling are stable.

This avoids losing continuity between Phase 9B fixed-scale diagnostics and the eventual arbitrary-size research goal.

## Recommended Next Step

Proceed to Phase 9B-1 reporting-only counters before any reward implementation or training. The first implementation
work should make the Phase 8 stagnation pattern measurable online:

```text
per-robot completed count
per-viewpoint attempted count
repeated assignment count
steps since last coverage gain
duplicate selected target count
noop when useful target exists
```

Only after those counters are stable should Phase 9B-2 observation changes or Phase 9B-3 reward changes be scoped.
