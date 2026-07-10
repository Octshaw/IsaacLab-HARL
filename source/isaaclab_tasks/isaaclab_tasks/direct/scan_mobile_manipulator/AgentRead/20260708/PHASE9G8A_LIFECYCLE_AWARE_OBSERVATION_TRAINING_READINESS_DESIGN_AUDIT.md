# Phase 9G-8A Lifecycle-Aware Observation and Training-Readiness Design Audit

Date: 2026-07-08

Status: design audit complete. No implementation in this phase.

## Scope

Phase 9G-8A audits the committed default-off assignment lifecycle resolver and the current HARL-facing observation, mask, action, rollout, playback, and checkpoint boundaries. The goal is to define the minimum migration required before resolver-enabled training can be legal.

This phase intentionally does not change Python source, policy networks, HARL code, resolver behavior, action dimensions, Contract C, ownership semantics, failed-pair persistence, retry policy, checkpoint loading, playback, evaluation, or training.

## Files Inspected

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7E_BOUNDED_RESOLVER_RUNTIME_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7F_COMMIT_READINESS_REVIEW.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`
- Installed HARL runner, actor, critic, buffer, policy, MLP, and categorical action distribution boundaries reached from the project code.

## Executive Decision

The minimum safe migration before resolver-enabled training is Option B:

1. Add a lifecycle observation schema that exposes behavior-driving resolver state to the decentralized actor.
2. Preserve the current action dimension `N + 1`.
3. Add lifecycle-aware available-action masks for deterministic resolver rejections.
4. Keep the resolver as the final safety boundary.
5. Keep resolver-disabled legacy observation mode as the default and preserve old checkpoint compatibility.
6. Add strict observation schema and checkpoint compatibility guards so old checkpoints cannot silently run with resolver-enabled hidden lifecycle state.

Option A, observation only, is Markov-sufficient if all actor-required lifecycle state is exposed, but it leaves training to sample many deterministic rejects. Option C, an explicit continue/hold action redesign, is deferred because it changes action semantics and breaks action/checkpoint compatibility.

## Current Observation Architecture

The current HARL-facing environment is `AssignmentHarlWrapper`.

The raw Isaac Lab direct multi-agent observation is produced by `ScanMobileManipulatorEnv._get_observations()`. For `M` robots, the raw per-agent dimension is:

```text
raw_actor_dim = 90 + 3 * (M - 1)
```

The wrapper appends assignment-specific features:

```text
per-task rows:            N * 14
noop context:             5
previous assignment:      N + 1
dynamic scalars:          7
covered vector:           N
wrapper extension:        16N + 13
current actor dim:        90 + 3(M - 1) + 16N + 13
                         = 100 + 3M + 16N
```

For the current fixed configuration `M = 3`, `N = 50`:

```text
raw actor observation:        96
wrapper extension:           813
current actor observation:   909
```

The per-task row currently contains:

```text
relative_viewpoint_position_x
relative_viewpoint_position_y
relative_viewpoint_position_z
viewpoint_quaternion_w
viewpoint_quaternion_x
viewpoint_quaternion_y
viewpoint_quaternion_z
covered_flag
available_flag
feasible_flag
static_geometric_feasible_flag
normalized_selected_path_cost
per_viewpoint_attempted_count_norm
per_viewpoint_last_attempt_age_norm
```

The current actor observation does expose physical feasibility, coverage, selected path cost, previous assignment, and legacy cooldown/assignment diagnostics. It does not expose resolver-owned active target, execution latch, task ownership, or resolver failed/released pair memory.

## Current Actor Observation Shape and Schema

Current actor observation returned to HARL:

```text
obs[agent_id]: [E, 100 + 3M + 16N]
```

For `M = 3`, `N = 50`:

```text
obs[agent_id]: [E, 909]
```

Every robot receives its own agent-conditioned actor observation. The observation includes relative features from that robot's perspective and per-task rows for all `N` configured tasks.

The current actor observation is not lifecycle-Markov when the resolver is enabled because the same visible tensor can map the same sampled action to different resolver outcomes.

## Current Critic/Shared Observation Shape and Schema

The wrapper builds shared observation by concatenating all actor observations in agent order, then repeating the same flattened vector for each agent:

```text
shared_flat: [E, M * actor_dim]
share_obs:   [E, M, M * actor_dim]
```

For `M = 3`, `N = 50`:

```text
shared_flat dim: 2727
share_obs:       [E, 3, 2727]
```

This is a common flattened state per agent under the current HARL convention. In EP mode, the HARL runner stores `share_obs[:, 0]` in the critic buffer.

Because shared observation is currently only a concatenation of actor observations, the critic also does not observe resolver-owned lifecycle state unless the actor observation is extended.

## Current Available-Action Mask Construction

Current mask source:

```text
AssignmentHarlWrapper._build_available_actions()
  -> make_assignment_action_mask(problem, include_noop=True)
```

Current mask shape:

```text
available_actions: [E, M, N + 1]
```

Raw action ids:

```text
0 .. N - 1   target ids
N            raw HARL noop action
```

The raw HARL noop action `N` decodes to resolver/controller noop `-1`.

Current mask semantics:

- Target actions are available when the environment assignment problem says the target is physically feasible and uncovered for that robot.
- Noop is always available.
- Optional legacy wrapper guardrails may additionally mask cooldown, redirect, or legacy failed-pair memory when those older features are enabled.
- The lifecycle resolver's active target, ownership, failed/released pair memory, and Contract C continuation state do not currently affect `available_actions`.

## Current Checkpoint and Model-Loading Boundary

The relevant boundaries are:

- Actor model input dimension is constructed from `env.observation_space[agent_id]`.
- Critic input dimension is constructed from `env.share_observation_space[0]`.
- Actor rollout buffers allocate `obs` from the actor observation space.
- Critic rollout buffers allocate `share_obs` from the shared observation space.
- Discrete action distribution uses `action_space.n`, currently `N + 1`, and applies `available_actions` by masking logits.
- Training restore is inherited from the installed HARL on-policy runner. It loads actor, critic, and optional value normalizer state dicts from `model_dir`.
- Manual RL playback and comparison-method loaders construct actors from the current wrapper observation/action spaces and then load `actor_agent_*.pt`.

Checkpoint risk:

- Any actor observation shape change changes the first actor MLP input layer and optional LayerNorm shapes.
- Any shared observation shape change changes the critic MLP input layer and optional LayerNorm shapes.
- Rollout buffer shapes are determined from env spaces at runner construction.
- Existing HARL actor forward paths slice incoming observations to the model observation-space size, so schema guards must fail before silent truncation or fabricated compatibility can occur.
- Manual playback loaders already re-raise state-dict shape mismatches, but they do not yet distinguish legacy and lifecycle observation schemas.
- The installed training restore path can print restore errors without a project-level lifecycle schema diagnosis, so the project wrapper/runner needs explicit guards before model loading.

## Contract C and Resolver State Summary

Committed resolver behavior:

```text
idle + target                 -> start target if lifecycle checks pass
idle + noop                   -> remain idle
executing + same target       -> continue active target
executing + noop              -> continue active target
executing + different target  -> reject switch, continue active target
noop                          -> not a release action
completion                    -> releases owner/active attempt
budget failure                -> releases effective robot-target pair
same robot-target failed pair -> episode-persistent rejection
```

Diagnostics-only behavior:

- Active-target infeasibility monitoring does not release the target.
- Stranded failed-pair monitoring does not change resolver output.

## POMDP Examples Caused by Hidden Lifecycle State

1. Two observations look identical to the policy. In one state the robot is idle, so raw noop `N` decodes to idle noop. In another state the robot has active target `j`, so raw noop `N` is accepted as active-target continuation. Without active-target visibility, noop has hidden state-dependent semantics.

2. Two observations look identical. In one state target `j` is unowned, so proposing raw target `j` may start a claim. In another state target `j` is owned by a teammate, so proposing `j` is rejected and the robot remains idle or continues its active target. Without ownership visibility, the same proposal has hidden state-dependent interpretation.

3. The same robot-target proposal is valid early in an episode but later rejected because that same robot-target pair previously failed by budget and was released. Without same-robot failed/released-pair visibility, the policy sees the same physical task but cannot know that the resolver will reject it.

4. An executing robot sees another attractive target become available. Proposing that target is rejected by Contract C and the effective assignment remains the active target. Without active-target/execution visibility, the policy cannot distinguish a valid idle assignment from a rejected switch.

5. The critic receives only concatenated actor observations. If the actor observations do not include lifecycle state, the critic cannot value states with different latent ownership, active target, or failed-pair memory even when those states have different future transitions.

## Table 1: Hidden-State Inventory

| resolver/env state | currently observed by actor? | currently observed by critic? | changes proposal interpretation? | changes transition/reward? | recommended destination | required in minimum migration? |
|---|---:|---:|---:|---:|---|---:|
| Robot idle / executing state | No | No | Yes | Yes, through effective assignment and continuation | Behavior-driving and actor-required, represented by active-target indicator | Yes |
| `active_target_id[E,M]` | No | No | Yes | Yes | Behavior-driving and actor-required; per-task self-active indicator for actor, all robots through shared concat | Yes |
| `task_owner_robot_id[E,N]` | No | No | Yes | Yes | Behavior-driving and actor-required as self-owned / teammate-owned / unowned | Yes |
| `pair_state` active | No | No | Yes for executing continuation | Yes | Derived from active-target indicator; do not duplicate separately in actor | Yes, via active-target encoding |
| `pair_state` completed | Yes, as covered/completion | Yes, through actor concat | Yes, because covered targets are unavailable | Yes | Already represented by covered flags and masks | No new field |
| Same-robot `PAIR_FAILED_BUDGET` / `PAIR_RELEASED_BUDGET` | No | No | Yes | Yes | Behavior-driving and actor-required; per-task self failed/released bit | Yes |
| Teammate failed/released pair state | No | No | No for this actor's proposal acceptance | Possibly for team value/coordination | Critic-only optional full matrix; not actor minimum | No |
| `attempt_start_step[E,M]` | No | No | No in current resolver | Indirect diagnostic/history only | Diagnostics/critic-only optional | No |
| `attempt_age[E,M]` | No | No | No in current resolver | Not directly in resolver; budget diagnostics may release after environment step | Critic/diagnostic optional; not first actor migration | No |
| `last_failure_reason[E,M]` | No | No | No, pair state drives rejection | Useful for analysis only | Diagnostics-only, optional critic feature later | No |
| `last_release_reason[E,M]` | No | No | No, pair state drives rejection | Useful for analysis only | Diagnostics-only, optional critic feature later | No |
| Current resolver `step[E]` | No | No | No | No direct proposal effect | Diagnostics-only or critic-only normalized episode context later | No |
| Proposal acceptance/rejection history | Partly, legacy previous assignment only; resolver events not observed | Partly, via actor concat only | No persistent rule except pair state | Can explain behavior after the fact | Logging-only; failed-pair memory is the persistent state to expose | No |
| Current target feasibility/availability | Yes, per actor-task | Yes, through actor concat | Yes | Yes | Already actor-visible and mask-required | No new field |
| Active-target infeasibility state/streak | No | No | No, monitor does not release | No resolver behavior change | Diagnostics-only logging | No |
| Stranded failed-pair state/streak | No | No | No, monitor does not retry/release | No resolver behavior change | Diagnostics-only logging | No |
| Completion state | Yes, covered flags and coverage ratio | Yes, through actor concat | Yes | Yes | Already represented; do not duplicate | No new field |
| Budget trigger state | Partly via legacy dynamic scalars, not exact resolver release trigger | Partly through actor concat | No pre-step proposal interpretation | Yes, can release effective pair post-step | Keep release result visible via failed/released pair; budget internals optional critic/diagnostic | No exact trigger field in first migration |
| Pending exact-target claim arbitration | No, simultaneous proposals are not state before action | No | Resolver uses same-step proposals and costs | Yes | Resolver safety boundary; not an observation field | No |
| Effective assignment from previous step | Partly through legacy previous assignment one-hot, but not proposal/effective split | Partly through actor concat | No direct current rule except active/pair state | Helps diagnostics | Logging-only; active/pair state is canonical | No |

## Behavior-Driving State Classification

Actor-required:

- Robot execution state, represented by active target.
- Active target id, encoded as a per-task self-active indicator.
- Task ownership, encoded as self-owned and teammate-owned per task.
- Same-robot failed/released pair state, encoded as a per-task binary.
- Existing completion, availability, and feasibility fields, already present.

Mask-required:

- Existing physical availability/feasibility/coverage.
- Active target state for executing robots.
- Teammate-owned task state.
- Same-robot failed/released pair state.
- Noop availability under Contract C.

Critic-only optional:

- Teammate failed-pair matrix.
- Global attempt ages.
- Last failure and release reasons.
- Resolver step or normalized lifecycle episode counters.

Diagnostics-only:

- Active-target infeasibility streaks.
- Stranded failed-pair streaks.
- Resolver event history beyond persistent state.
- Proposal/effective explanation rows.

Derived and should not be duplicated in the minimum actor schema:

- `is_idle` can be derived from no self-active target.
- `is_executing` can be derived from any self-active target.
- Pair active can be derived from self-active target.
- Pair completed can be derived from covered/completion state already in the observation.
- Owned-by-any can be derived from self-owned or teammate-owned.

Not needed in the first training-ready migration:

- Attempt start step.
- Raw resolver step.
- Last reason ids.
- Full teammate failed-pair state for decentralized actor.
- Retry/stranded-task policy state.

## Consequences of Omitting Behavior-Driving Fields

Omitting active target or execution state makes Contract C hidden. The same raw noop action means idle hold in one state and target continuation in another. The same non-current target action can be valid when idle and rejected as a disabled switch when executing.

Omitting task ownership makes target claims hidden. The actor cannot tell whether target `j` is unowned, self-owned, or teammate-owned, even though those cases have different resolver outcomes.

Omitting same-robot failed/released pair state makes episode-persistent rejection hidden. A target can look physically available and uncovered, while the resolver rejects it because this robot already budget-failed that pair.

Omitting existing availability/feasibility/coverage would hide physical task validity and completion state. These are already exposed and already contribute to the current mask.

Omitting active-target continuation from the mask does not make the policy non-Markov if it is observed, but it harms exploration by allowing deterministic rejected switches to be sampled frequently.

Omitting budget internals is acceptable in the first migration because current pre-step proposal interpretation does not depend on `attempt_age` or `attempt_start_step`. The release outcome that affects future decisions must be visible through failed/released pair state after it occurs.

## Minimum Actor-Visible Lifecycle State

The actor should receive the minimum state needed for decentralized Markov action interpretation, not privileged team internals.

Selected actor lifecycle block:

```text
per task, for the acting robot:
  self_active_target[j]
  task_owned_by_self[j]
  task_owned_by_teammate[j]
  self_pair_failed_or_released[j]
```

Shape:

```text
actor_lifecycle_task_features: [E, N, 4]
flattened actor lifecycle add-on: [E, 4N]
```

For `N = 50`, this adds `200` actor dimensions.

New lifecycle actor dimension under the selected minimum schema:

```text
lifecycle_actor_dim = legacy_actor_dim + 4N
                    = 100 + 3M + 20N
```

For `M = 3`, `N = 50`:

```text
lifecycle_actor_dim = 1109
```

No separate scalar `is_idle`, `is_executing`, or `has_active_target` is needed in the first schema because these are derivable from `self_active_target`. An implementation may compute those internally for validation, but they should not be appended unless a later phase shows a concrete training benefit.

### Table 2: Actor Lifecycle Features

| feature | semantic meaning | shape | encoding | normalization | padding/mask behavior | required/optional |
|---|---|---:|---|---|---|---|
| `self_active_target` | Task `j` is the acting robot's latched active target | `[E,N,1]` per actor | float32 binary 0/1 | None | Padded tasks 0; masked by future `task_valid` | Required |
| `task_owned_by_self` | Task `j` is owned by the acting robot | `[E,N,1]` per actor | float32 binary 0/1 | None | Padded tasks 0 | Required |
| `task_owned_by_teammate` | Task `j` is owned by any other robot | `[E,N,1]` per actor | float32 binary 0/1 | None | Padded tasks 0 | Required |
| `self_pair_failed_or_released` | This robot-task pair is episode-persistently rejected after budget failure/release | `[E,N,1]` per actor | float32 binary 0/1 | None | Padded tasks 0 | Required |
| Existing `covered_flag` | Task already completed/covered | Already `[E,N,1]` in current task row | float32 binary 0/1 | None | Padded tasks should be treated as unavailable | Existing required |
| Existing `available_flag` | Task is currently available to this robot under physical/env constraints | Already `[E,N,1]` in current task row | float32 binary 0/1 | None | Padded tasks 0 | Existing required |
| Existing `feasible_flag` | Task is feasible to this robot | Already `[E,N,1]` in current task row | float32 binary 0/1 | None | Padded tasks 0 | Existing required |
| Existing `normalized_selected_path_cost` | Resolver arbitration cost proxy and control effort proxy | Already `[E,N,1]` in current task row | float32 scalar | Existing cost normalization | Padded tasks 0 or high-cost with mask 0 | Existing required |
| `task_valid` | Future variable-`N` padding indicator | `[E,N_max,1]` | float32 binary 0/1 | None | Invalid tasks 0 and masked unavailable | Optional future, not current fixed-`N` blocker |
| `active_attempt_age_norm` | Current active attempt age for this robot | `[E,1]` or `[E,N,1]` active-only | float32 | Divide by budget horizon or episode horizon | 0 when no active target | Optional, not first migration |
| Last failure/release reason | Reason enum for most recent robot release/failure | `[E,K]` one-hot or `[E,1]` id | One-hot preferred if added | None | 0 when none | Optional diagnostics, not actor minimum |

## Active Target Encoding Decision

Options considered:

| encoding | benefit | problem | decision |
|---|---|---|---|
| Raw normalized target id | Very small | Imposes false ordinal structure; awkward sentinel; weak with variable `N`; MLP must learn id-to-row lookup | Reject |
| One-hot over maximum task count | Simple and expressive | Separate from existing per-task rows; duplicates future task padding logic | Acceptable but not selected |
| Per-task active-target indicator | Aligns with current per-task task rows; fixed-`N` MLP compatible; variable-`N` padding compatible; no ordinal bias | Adds `N` dims per actor | Selected |
| Gathered active-target feature embedding | Compact active target context | Duplicates current per-task row; needs sentinel handling; less direct for masks | Defer |
| Attention/query token | Good future Transformer/GNN pattern | Oversized for current HAPPO/MLP migration | Defer |

Selected first implementation:

```text
self_active_target[j] in the per-task lifecycle block
```

This keeps the current fixed `N = 50` MLP path straightforward while avoiding an encoding that would be regrettable for future variable task counts.

## Task Ownership Encoding Decision

The actor must distinguish:

```text
unowned task
task owned by itself
task owned by another robot
```

Those cases produce different resolver behavior:

- Unowned target can be claimed if other checks pass.
- Self-owned target is the robot's continuation target under normal invariants.
- Teammate-owned target is rejected for an idle robot and masked in the selected migration.

Selected actor encoding:

```text
task_owned_by_self[j]
task_owned_by_teammate[j]
```

Unowned is represented by both bits equal to 0. This avoids exposing a raw owner robot id or owner one-hot to the decentralized actor. It is also more compatible with variable robot counts because the actor does not need a fixed owner-id dimension.

The critic can reconstruct fuller ownership from concatenated actor lifecycle blocks. A compact owner matrix may be added later as critic-only state if value estimation needs it.

## Failed-Pair Encoding Decision

The current resolver enforces episode-persistent same-robot failed-pair rejection. Therefore the acting robot needs:

```text
self_pair_failed_or_released[j]
```

This bit should be 1 when this actor's robot-target pair is in either budget-failed or released-budget terminal pair memory that causes future same-pair rejection.

Actors do not need teammates' failed-pair state in the minimum schema because a teammate's failed pair does not directly reject this actor's proposal. The centralized critic may benefit from the full failed-pair matrix, but that is not required for decentralized action interpretation.

This exposure does not solve the stranded-task retry-policy limitation. A task can still become stranded if all robots have failed the pair and no retry TTL or release policy exists. The selected observation only makes the current rule visible.

## Attempt-Age Encoding Decision

Current resolver inspection shows:

- `attempt_start_step` and `attempt_age` are stored and reported.
- Current pre-step proposal interpretation does not depend on attempt age.
- Budget release is applied from post-step wrapper cooldown/budget diagnostics for the effective pair.
- The resolver does not use `attempt_age` to release, retry, or reject proposals.

Therefore, attempt age is not actor-required in the first training-ready migration.

Comparison:

| encoding | benefit | problem | first migration decision |
|---|---|---|---|
| Raw step count | Exact | Scale depends on episode horizon; poor for learning | Reject |
| Normalized age | Stable scalar | Only useful if policy needs budget timing | Optional later |
| Remaining budget ratio | Better action relevance | Requires coupling to budget calculation and expected duration semantics | Defer |
| Threshold proximity | Strong signal for budget release | Bakes a specific heuristic into observation | Defer |

If later validation shows budget releases are too unpredictable for the actor, the least redundant addition is a normalized active-pair remaining budget ratio or normalized active attempt age. It should not be added in 9G-8B unless the implementation proves current existing dynamic scalars are insufficient.

## Minimum Critic/Shared Lifecycle State

The current HARL wrapper uses one common flattened shared state per agent by concatenating all actor observations. The smallest safe migration keeps that convention:

```text
share_obs = concat(lifecycle_actor_obs for all M robots)
```

New lifecycle shared dimension under the selected minimum schema:

```text
lifecycle_shared_dim = M * lifecycle_actor_dim
                     = M * (100 + 3M + 20N)
```

For `M = 3`, `N = 50`:

```text
lifecycle_shared_dim = 3327
share_obs shape: [E, 3, 3327]
```

This already gives the centralized critic the actor-required lifecycle state for every robot:

- All robots' active targets.
- All robots' self failed/released pairs.
- Ownership from every robot's self/teammate perspective.
- Existing availability, feasibility, coverage, cost, and robot-local physical context.

No additional critic-only lifecycle fields are strictly required for the minimum safe first migration.

### Table 3: Critic/Shared Lifecycle Features

| feature | semantic meaning | shape | encoding | normalization | padding/mask behavior | required/optional |
|---|---|---:|---|---|---|---|
| Concatenated actor lifecycle blocks | All actor-required lifecycle state for all robots | `[E, M * 4N]` inside shared flat state | float32 binary features | None | Same as actor block | Required |
| Full active-target matrix | Which task each robot is executing | Logically `[E,M,N]` | Represented by each actor's `self_active_target` in concat | None | Padded tasks 0 | Required, via concat |
| Full ownership matrix | Which robot owns each task | Logically `[E,M,N]` plus unowned | Reconstructable from actor ownership bits | None | Padded tasks unowned/unavailable | Required, via concat |
| Full failed/released pair matrix | Which robot-task pairs are rejected by pair memory | Logically `[E,M,N]` | Represented by each actor's self pair bit in concat | None | Padded tasks 0 | Required, via concat |
| Existing completion/coverage state | Which tasks are done | Existing actor concat | float32 binary/ratio | Existing | Padded tasks unavailable | Required, existing |
| Existing availability/feasibility/cost | Physical assignment constraints and arbitration cost | Existing actor concat | Existing | Existing | Padded tasks unavailable | Required, existing |
| Attempt age matrix | All active attempt ages | `[E,M]` or `[E,M,N]` active-only | float32 | Normalize by horizon or budget | 0 when inactive | Optional critic-only |
| Last failure/release reason matrix | Diagnostic reason by robot | `[E,M,K]` one-hot | float32 one-hot | None | 0 when none | Optional diagnostics |
| Resolver step | Current lifecycle step | `[E,1]` | float32 | Divide by episode length | Reset to 0 on reset | Optional diagnostics |
| Active infeasibility streaks | Monitor-only unresolved infeasibility | `[E,M]` or event log | float32/int | Optional normalization | 0 when inactive | Logging-only |
| Stranded failed-pair streaks | Monitor-only stranded-task detector | `[E,N]` or event log | float32/int | Optional normalization | 0 when inactive | Logging-only |

## Available-Action Mask Migration Decision

Selected: Option B, observation plus lifecycle-aware masks.

The lifecycle-aware mask should proactively remove actions that the resolver will deterministically reject under the current state, while leaving the resolver as the authoritative safety boundary for stale masks, simultaneous claims, race conditions, invalid raw actions, and any future behavior.

The mask must use raw HARL action ids:

```text
target j: raw id j
noop:     raw id N
```

Noop must remain available for both idle and executing robots because Contract C gives it valid semantics in both states:

```text
idle + noop       -> remain idle
executing + noop  -> continue active target
```

### Table 4: Available-Action Rules

| robot execution state | candidate action | mask result | resolver result if sampled | reason |
|---|---|---:|---|---|
| Idle | Target `j` physically available, uncovered, unowned, and not self failed/released | 1 | Candidate claim, subject to exact-target arbitration | Valid new assignment |
| Idle | Covered target `j` | 0 | Reject no available task / covered | Completed task should not be claimed |
| Idle | Physically infeasible or unavailable target `j` | 0 | Reject unavailable/infeasible | Existing physical constraint |
| Idle | Target `j` owned by teammate | 0 | Reject owner conflict | Lifecycle ownership constraint |
| Idle | Target `j` failed/released for this same robot | 0 | Reject same-pair failed/released | Episode-persistent pair memory |
| Idle | Noop raw id `N` | 1 | Remain idle | Contract C valid idle hold |
| Executing target `k` | Current active target `k` | 1 | Continue active target | Contract C same-target continuation |
| Executing target `k` | Noop raw id `N` | 1 | Continue active target `k` | Contract C noop continuation |
| Executing target `k` | Different target `j != k` | 0 | Reject switch and continue `k` | Contract C disables switching |
| Executing target `k` | Different target `j` owned by teammate | 0 | Reject switch and/or owner conflict, continue `k` | Switch is already invalid |
| Executing target `k` | Different target `j` failed/released for self | 0 | Reject switch and/or pair memory, continue `k` | Switch is already invalid |
| Any state | Invalid/padded target id | 0 | Strict path should reject invalid id | Variable-`N` padding safety |

Executing robot mask decision:

```text
Only current active target and noop remain available.
```

This is candidate approach A from the prompt. It is selected because it is compatible with Contract C and preserves the current action space. Candidate B, only current active target, is rejected because noop is a valid continuation action. Candidate C, leave all physical targets available, is rejected for training because it invites deterministic switch rejections. Candidate D, add an explicit continue action, is deferred because it changes action semantics and checkpoint/action compatibility.

The current active target should remain mask-available for an executing robot even if the physical `available_mask` has become false, because the current resolver does not release active targets on infeasibility. It emits diagnostics and continues. Completion should normally clear active targets in `observe_post_step`; any stale covered-active inconsistency should remain guarded by the resolver and validation.

Ownership mask semantics:

- Teammate-owned target actions should be masked for idle robots.
- Self-owned current active target should remain available for the executing owner.
- Resolver-side owner rejection remains required as a safety boundary because masks can be stale and simultaneous claims are resolved after proposals are sampled.

Failed-pair mask semantics:

- Same-robot failed/released pairs should be masked for idle robots.
- Resolver-side pair rejection remains required because failed-pair memory is safety-critical and may change after post-step budget release.

## Variable Robot and Task Count Representation

Current implementation is effectively fixed-shape for model construction. For the current expected `M = 3`, `N = 50`, lifecycle observation can use fixed MLP inputs.

The first lifecycle schema should still avoid encodings that make variable counts harder:

- Use per-task binary lifecycle features instead of raw normalized target ids.
- Use self/teammate ownership instead of owner id or owner one-hot in actor observations.
- Reserve a future `task_valid` mask for padded task slots.
- Keep noop as raw id `N_configured` for the configured action space.
- Do not change action dimension in 9G-8.

Future variable `N` policy:

```text
N_configured = maximum task slots for the run
valid tasks  = first N_actual slots or explicit task_valid mask
invalid task features = 0
invalid target actions = mask 0
noop raw id = N_configured
```

Future variable `M` policy:

- Actor lifecycle ownership remains self/teammate/unowned, independent of teammate count.
- Shared observation with current concatenation still depends on configured `M`.
- True variable `M` across checkpoints requires a separate architecture migration, likely Transformer/GNN or fixed maximum robot slots with robot-valid masks. That is out of scope for the first MLP migration.

## Resolver-Disabled Legacy Compatibility Plan

Default behavior must stay legacy-compatible:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_observation_enabled = False
assignment_lifecycle_mask_enabled = False
assignment_observation_schema_version = "legacy_v1"
```

In this mode:

- Actor observation tensors remain exactly the legacy shape and ordering.
- Shared observation tensors remain exactly the legacy concatenation.
- Available-action masks remain the existing physical/cooldown/legacy-guardrail masks.
- Old checkpoints remain playable.
- Resolver-disabled deterministic identity remains testable against previous hashes.

Do not append zero lifecycle fields to the default resolver-disabled path. That would break old checkpoint loading and would make the default-off guarantee weaker.

Lifecycle schema mode may be supported with resolver disabled for explicit ablations or new lifecycle checkpoints:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_observation_enabled = True
assignment_lifecycle_mask_enabled = False or True
assignment_observation_schema_version = "lifecycle_v1"
```

In that mode, lifecycle fields should represent actual disabled resolver state: no active targets, no ownership, and no resolver failed-pair memory. This mode is not a legacy checkpoint mode.

## Invalid Configuration Combinations

Training-invalid:

- `resolver_enabled=True` and `lifecycle_observation_enabled=False`
- `resolver_enabled=True` and `assignment_observation_schema_version="legacy_v1"`
- `resolver_enabled=True` and `lifecycle_mask_enabled=False` for the selected training-ready path, unless an explicit ablation flag is introduced later
- `lifecycle_mask_enabled=True` and `lifecycle_observation_enabled=False`
- Checkpoint schema metadata missing or not equal to environment schema when loading for training
- Legacy checkpoint with lifecycle observation schema
- Lifecycle checkpoint with legacy observation schema

Playback/evaluation-invalid by default:

- Legacy checkpoint with resolver enabled and hidden lifecycle state.
- Any checkpoint whose actor or critic input dimensions do not match the configured schema.

Diagnostics-only explicit override:

- A future flag may allow hidden-state resolver playback for bounded diagnostics only, not training. This should require a conspicuous name such as `assignment_lifecycle_allow_hidden_state_playback=True` and should emit a warning in logs.

## Checkpoint Compatibility Policy

Selected policy: Policy 3, dual legacy/lifecycle model mode.

Hard version breaks are too blunt because old checkpoints must remain useful with resolver disabled. Zero-filled compatibility adapters are unsafe because zeros would fabricate idle/unowned/unfailed lifecycle state when resolver hidden state may actually differ.

Required checkpoint metadata for new lifecycle runs:

```text
assignment_observation_schema_version
assignment_lifecycle_resolver_enabled at training start
assignment_lifecycle_observation_enabled
assignment_lifecycle_mask_enabled
num_robots M
num_tasks N
actor_observation_dim
shared_observation_dim
action_dim
noop_action_id
resolver_contract_version or lifecycle schema contract version
```

This metadata can live in a small sidecar file in the run/model directory and should also be reflected in the saved run config where practical.

Loading rules:

- Old checkpoints remain supported only when the environment is in `legacy_v1` observation mode and resolver is disabled.
- Old checkpoints must fail clearly when resolver is enabled for normal playback, evaluation, or training.
- New lifecycle checkpoints require `lifecycle_v1` observation mode.
- Model loading must fail before HARL silently slices observations or before a state-dict mismatch is merely printed without a project-level explanation.

### Table 5: Checkpoint Compatibility Matrix

| checkpoint | resolver off | resolver on | support decision |
|---|---|---|---|
| Legacy checkpoint | Supported with `legacy_v1` observation and legacy mask behavior | Unsupported by default; diagnostics-only explicit hidden-state override may be allowed for bounded playback, not training | Preserve old playback only in resolver-disabled legacy mode |
| New lifecycle checkpoint | Supported only with `lifecycle_v1` observation shape; useful for ablations | Supported after lifecycle observation, lifecycle masks, guards, and smokes pass | Normal lifecycle mode |
| Legacy checkpoint with lifecycle observation enabled | Unsupported | Unsupported | Actor/critic input shape mismatch; fail clearly |
| New lifecycle checkpoint with legacy observation enabled | Unsupported | Unsupported | Actor/critic input shape mismatch; fail clearly |

## Minimal Migration Options Compared

| option | Markov sufficiency | implementation scope | checkpoint compatibility | training stability | exploration | baseline comparability | future variable M/N support | decision |
|---|---|---|---|---|---|---|---|---|
| A. Observation only | Sufficient if all actor-required state is exposed | Moderate | Actor/critic shape break only | Weaker, many deterministic rejects | Poorer, switch/owned/failed actions sampled | Good action compatibility | Good if per-task encoding used | Not selected |
| B. Observation plus lifecycle-aware masks | Sufficient and more aligned with resolver | Moderate plus mask integration | Actor/critic shape break, action dim unchanged | Stronger | Better, removes impossible lifecycle actions | Good action compatibility | Good with per-task/padded masks | Selected |
| C. Explicit continue/hold action redesign | Could be clean semantically | Large | Breaks action semantics and checkpoints | Unknown | Potentially better long-term | Poor for existing baselines | Requires broader architecture design | Defer |

## Observation Schema Versioning

Recommended schema names:

```text
legacy_v1
lifecycle_v1
```

`legacy_v1`:

- Current actor observation order and shape.
- Current shared observation order and shape.
- Current available-action semantics.
- Resolver disabled for training/playback unless diagnostics override is explicitly selected.

`lifecycle_v1`:

- Appends the selected per-task lifecycle block to each actor observation.
- Shared observation remains current common flattened concatenation of all lifecycle actor observations.
- Action dimension remains `N + 1`.
- Noop raw id remains `N`.
- Lifecycle-aware masks are the training-ready default when resolver is enabled.

The schema version should be part of env metadata, runner logs, saved run config, and checkpoint compatibility metadata.

## Implementation-Ready Lifecycle Tensor Builder

The next implementation phase should introduce a pure tensor builder before integration. It should accept:

```text
resolver state snapshot
assignment problem
agent index / robot index
configured M
configured N
device
dtype
```

It should return:

```text
actor_lifecycle_block[agent_id]: [E, 4N]
optional debug named tensors:
  self_active_target[E,N]
  task_owned_by_self[E,N]
  task_owned_by_teammate[E,N]
  self_pair_failed_or_released[E,N]
```

It should also expose validation assertions:

- At most one active target per robot.
- At most one owner per task.
- `self_active_target` agrees with resolver `active_target_id`.
- Self-owned active targets agree with task ownership under normal invariants.
- Failed/released pair bits match resolver pair memory.
- No padded/invalid task can be marked active, owned, or failed.

The builder should not modify resolver state.

## Lifecycle-Aware Mask Builder

The later mask integration phase should build on the existing physical mask:

```text
base_mask = physical_available_and_uncovered_mask plus existing configured legacy guardrails
```

Then apply lifecycle constraints:

```text
if robot idle:
  target j available iff base target j is available
                         and not teammate-owned
                         and not self failed/released
  noop available

if robot executing target k:
  target k available
  noop available
  all other targets unavailable
```

The lifecycle-aware mask builder should retain no-all-zero-row checks. Since noop remains always available, rows should remain valid.

## Training-Readiness Gate

Resolver-enabled training remains illegal until all of the following are true:

1. `lifecycle_v1` observation schema is implemented.
2. Actor observation exposes all actor-required behavior-driving resolver state.
3. Shared observation exposes required centralized lifecycle state through the current shared convention.
4. Lifecycle-aware mask semantics are implemented for the selected Option B path.
5. Observation and mask shape smokes pass for reset and step without Isaac Sim training.
6. Checkpoint/schema guards fail clearly for invalid combinations.
7. Rollout buffer construction passes with lifecycle actor and critic spaces.
8. Actor and critic forward/backward smoke passes with lifecycle shapes.
9. Resolver-disabled legacy identity passes with exact legacy observations and checkpoint compatibility.
10. Resolver-enabled observation consistency validation passes, including active target, ownership, failed-pair, noop continuation, and mask consistency.
11. Very short resolver-enabled training/checkpoint save-load smoke passes.

Allowed for later implementation phases:

- Shape smoke.
- Forward/backward smoke.
- Checkpoint save/load smoke.
- Very short training smoke.
- Bounded runtime validation without playback/evaluation where scoped by phase.

User-run or later formal validation:

- Long training.
- Performance comparison.
- Hyperparameter tuning.
- Formal playback/evaluation sweeps.

## Recommended Phased Implementation Sequence

### Phase 9G-8B: Lifecycle Observation Schema and Pure Tensor Builder

- Add config fields for schema mode, lifecycle observation, lifecycle mask, and strict checkpoint policy.
- Implement pure lifecycle observation tensor builder.
- Add unit/shape-level validation for active target, ownership, and failed-pair features.
- Do not integrate into HARL observations yet.
- Do not change masks yet.
- Do not train.

### Phase 9G-8C: Actor/Shared Observation Integration and Schema Guards

- Integrate lifecycle builder into actor observations only when `lifecycle_v1` is enabled.
- Keep default `legacy_v1` byte-for-byte compatible.
- Update shared observation dimensions through existing concatenation.
- Add schema metadata reporting.
- Add checkpoint/load guards before HARL model loading.
- Run observation shape smokes and disabled legacy identity checks.
- Do not change lifecycle masks yet unless explicitly scoped.
- Do not train.

### Phase 9G-8D: Lifecycle-Aware Available-Action Mask Integration

- Add lifecycle mask builder.
- Preserve noop raw id `N`.
- Enforce executing robot mask: current active target plus noop.
- Mask teammate-owned and same-robot failed/released target actions.
- Keep resolver as final safety boundary.
- Validate mask/resolver consistency.
- Do not train.

### Phase 9G-8E: Disabled Legacy Identity and Enabled Observation/Mask Runtime Validation

- Re-run deterministic resolver-disabled legacy identity checks.
- Validate resolver-enabled observation consistency over bounded scripted/random/nearest/greedy paths.
- Validate schema/output isolation.
- Validate passive logger coexistence.
- Validate no Python source behavior unrelated to lifecycle mode changed.
- No playback/evaluation unless explicitly scoped.
- No training.

### Phase 9G-8F: Short Resolver-Enabled Training and Checkpoint Smoke

- Run a very short training smoke only after 9G-8B through 9G-8E pass.
- Validate rollout buffer insertion, actor sampling with lifecycle masks, critic forward, optimizer step, save, and load.
- Confirm invalid checkpoint combinations fail clearly.
- This is not a performance run.

### Phase 9G-8G: Commit-Readiness Review

- Review diffs against the design.
- Confirm default-off legacy compatibility.
- Confirm resolver-enabled training gate evidence.
- Confirm documentation and validation artifacts are complete.
- Prepare commit only after review approval.

## Known Limitations

- The selected migration does not add retry TTL, infeasibility release, or stranded-task recovery.
- The selected actor schema does not expose teammate failed-pair memory, because it is not required for this actor's proposal interpretation.
- The selected actor schema does not expose attempt age, because the current resolver does not use it for pre-step proposal interpretation.
- Budget release prediction may still be imperfect; the first migration exposes the resulting failed/released pair memory rather than every budget diagnostic input.
- The current shared observation remains a redundant concatenation of actor observations, not a compact global graph/state representation.
- Variable `M` and `N` across checkpoints remain unsupported without a broader model architecture migration.
- Simultaneous exact-target claim arbitration cannot be fully pre-masked because it depends on same-step proposals from all actors. Resolver arbitration remains required.
- Active-target infeasibility monitoring remains logging-only and should not be treated as a release condition.

## Final 9G-8A Recommendation

Proceed to Phase 9G-8B with a pure `lifecycle_v1` observation schema builder that appends exactly four per-task actor lifecycle bits:

```text
self_active_target
task_owned_by_self
task_owned_by_teammate
self_pair_failed_or_released
```

Keep the default path:

```text
resolver disabled
lifecycle observation disabled
lifecycle mask disabled
schema legacy_v1
```

Implement lifecycle-aware masks in a separate later phase, with noop always available and executing robots limited to current active target plus noop.

Do not permit resolver-enabled training until lifecycle observation, lifecycle masks, schema guards, checkpoint guards, shape smokes, disabled legacy identity, enabled observation/mask validation, and short training/checkpoint smoke have all passed.
