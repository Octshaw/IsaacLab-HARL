# Phase 9B Fixed-N Dynamic-Policy Interface Wrap-Up

Date: 2026-06-29

## Scope And Boundaries

Phase 9B closes the fixed-scale RL/dynamic-policy interface preparation chain for the assignment-based
scan-mobile-manipulator task.

Scope:

```text
N = 50 fixed viewpoint ids
M = 3 fixed robots / HARL agents
action ids = 0..49 for viewpoints, 50 for noop
```

This is not arbitrary-N Transformer, GNN, or set-policy work yet. It is not RL training, formal RL evaluation, old
checkpoint evaluation, solver work, controller work, mask work, environment-dynamics work, or handcrafted baseline
development.

Phase 9B intentionally keeps these boundaries:

```text
available_mask semantics unchanged
feasible_mask semantics unchanged
static_geometric_feasible_mask semantics unchanged
solver behavior unchanged
controller logic unchanged
HARL internals and installed site-packages unchanged
environment dynamics unchanged
baseline solver path unchanged
no RL training
no formal RL evaluation
no old checkpoint rollout/evaluation
```

## Motivation From Phase 8 And Phase 9A

Phase 8 established that the real-component proxy baselines can make strong early progress but then plateau:

```text
nearest / greedy / conflict-aware variants:
  final_coverage = 0.900
  final covered viewpoints = 45 / 50
  final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
```

The late-stage plateau pattern was stable. The last coverage gain happened around step 116 in the Phase 8 validation,
and the Phase 9B-1A short rerun measured:

```text
last_global_coverage_gain_step = 117
no_progress_steps_after_last_gain = 182
```

Late repeated pairs included:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

The conflict-aware baseline variants reduced selected-target and inter-robot proxy conflict metrics, but they did not
improve final coverage and they increased actual proxy base-motion crossing:

```text
selected_target_conflict_rate: 0.7191 -> 0.6622
inter_robot_overlap_rate: 0.6689 -> 0.5753
actual_base_motion_intersection_rate: 0.0167 -> 0.1237
coverage: unchanged at 0.900
```

Phase 9A confirmed shape-level wrapper compatibility for N=50, M=3:

```text
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
noop_id = 50
```

But Phase 9A also identified semantic gaps: the policy observation was still the compact 96D per-agent observation
with nearest uncovered viewpoint slots, no id-aligned full viewpoint table, no full task status vector, no assignment
history, no no-progress memory, and no reward terms for repeated/no-progress assignment behavior. Existing checkpoints
were also incompatible with N=50 because old assignment checkpoints used 13-class heads for fixed N=12 plus noop.

## Phase 9B-0 Design Summary

Phase 9B-0 defined the fixed N=50, M=3 observation/reward bridge before any training.

Core design decisions:

```text
actor action logit j must correspond to viewpoint row j
noop action id N must use a separate noop context block
hard masks should remain hard-validity masks only
soft coordination, repeated attempts, path cost, conflict, and load balance should be observation/reward/reporting concepts
metrics should be reporting-only before promotion to reward
fixed-N MLP observations are a bridge, not the final arbitrary-N architecture
```

The design separated:

```text
Action masks:
  covered viewpoints
  infeasible viewpoints
  future padded rows for arbitrary-N policies
  strict out-of-range ids

Observation / reward / reporting:
  duplicate selected target
  repeated assignment
  no-progress state
  path cost
  load balance
  selected-target conflict
  inter-robot overlap
  actual base-motion crossing
  obstacle-aware diagnostics
```

The future arbitrary-N path remains a set/token policy with robot and viewpoint tokens, such as a Transformer encoder
or GNN. Phase 9B deliberately keeps feature semantics aligned with that future transition while using a fixed flattened
representation for the current N=50 smoke chain.

## Phase 9B-1 Reporting-Only Counters

Phase 9B-1 added online/offline reporting-only counters to make the Phase 8 failure modes measurable before changing
observations or rewards.

Counters added included:

```text
per_robot_selected_count
per_robot_completed_count
per_robot_repeated_assignment_count
per_viewpoint_attempted_count
steps_since_last_global_coverage_gain
no_progress_steps_after_last_gain
duplicate_selected_target_count
duplicate_selected_target_rate
noop_when_available_count
noop_when_available_rate
selected_path_cost_mean
selected_path_cost_max
selected_path_cost_sum
load_balance_selected_std
load_balance_completed_std
final_uncovered_viewpoint_ids
late_repeated_assignment_pattern
```

Output files updated:

```text
diagnostics.json
per_episode.csv
summary.csv
assignment_history.csv
```

Phase 9B-1 was behavior-neutral. It did not change reward, observations, masks, solver behavior, controller logic,
HARL internals, environment dynamics, training, or formal evaluation.

## Phase 9B-1A Plateau Counter Diagnostic

Phase 9B-1A reran a scoped non-RL baseline diagnostic using the new counters.

The result reproduced the Phase 8 plateau:

```text
final_coverage = 0.900 for nearest / greedy / conflict-aware variants
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
last_global_coverage_gain_step = 117
no_progress_steps_after_last_gain = 182
```

The late repeated assignment pattern concentrated on:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

Per-viewpoint attempts concentrated on final uncovered viewpoints 20, 36, and 48, while viewpoints 0 and 24 remained
uncovered and unattempted.

Other Phase 9B-1A signals:

```text
duplicate_selected_target_count_total = 0
noop_when_available_count_total = 0
selected-count load balance std = 0.0
completed-count load balance std = 7.4087
```

Implication:

```text
The primary issue is not exact duplicate target selection or noop abuse.
The main plateau mechanism is repeated no-progress assignment to a small set of uncovered targets,
ignored uncovered viewpoints, and productive completion imbalance across robots.
```

Phase 9B-1A also reinforced that selected-target conflict, inter-robot overlap, and actual base-motion crossing should
remain reporting-only before reward promotion because improving one proxy conflict metric worsened another execution
risk diagnostic.

## Phase 9B-2 Observation Update

Phase 9B-2 implemented a fixed N=50, M=3 wrapper-level observation extension for the assignment HARL interface.

Smoke shapes:

```text
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
```

The original 96D per-agent environment observation is preserved. The assignment extension adds:

```text
id-aligned 50 x 14 viewpoint rows
noop context block
previous assignment one-hot over 51 ids
per-viewpoint attempted counts
per-viewpoint last-attempt age
steps since last global coverage gain
per-robot completed count
per-robot repeated assignment count
full covered vector
```

Viewpoint row fields:

```text
relative_viewpoint_position_x/y/z
viewpoint_quaternion_w/x/y/z
covered_flag
available_flag
feasible_flag
static_geometric_feasible_flag
normalized_selected_path_cost
per_viewpoint_attempted_count_norm
per_viewpoint_last_attempt_age_norm
```

The row/action alignment smoke passed for:

```text
robot_0, viewpoint/action id 0
row_start = 96
row_dim = 14
```

The smoke also verified that assignment-history fields update online. For viewpoint 0, attempted count normalized
changed from `0.0` to `0.0033333334` after the first step.

Phase 9B-2 did not change reward, masks, solver behavior, controller logic, HARL internals, environment dynamics,
training, formal evaluation, or handcrafted rules.

## Phase 9B-3 Reward Smoke

Phase 9B-3 added wrapper-level reward-shaping terms and decomposition logging for the assignment RL path only.

Reward terms:

```text
repeated_same_target_no_progress
global_no_progress
selected_path_cost, implemented but disabled by default
```

Default config values:

```text
repeated_assignment_penalty_scale = 0.01
repeated_assignment_grace_steps = 2
no_progress_penalty_scale = 0.01
no_progress_grace_steps = 2
no_progress_penalty_cap = 0.05
selected_path_cost_penalty_scale = 0.0
```

Reward decomposition keys:

```text
config
base_env_reward
repeated_same_target_no_progress
global_no_progress
selected_path_cost
selected_path_cost_raw
selected_path_cost_norm
total_assignment_reward_adjustment
final_reward
same_target_streak
steps_since_global_coverage_gain
global_coverage_gain
```

The scripted smoke repeated:

```text
robot_0 -> viewpoint 0
robot_1 -> viewpoint 1
robot_2 -> noop
```

Smoke result:

```text
repeated_same_target_no_progress first negative step = 3
global_no_progress first negative step = 3
selected_path_cost disabled zero = true
```

This matches the grace threshold of 2. The smoke only verifies reward decomposition signs, magnitudes, and shapes. It
does not claim learned-policy quality.

Phase 9B-3 did not change the base environment reward computation or non-RL baseline solver reward behavior. The
reward shaping is applied in `AssignmentHarlWrapper.step()` after the base env reward is stacked.

## Current Fixed-N Architecture

The current fixed-N assignment RL interface is:

```text
Discrete action ids:
  0..49 = viewpoint ids
  50 = noop

Actor observation:
  original 96D env observation
  fixed flattened id-aligned viewpoint table
  noop context
  assignment-history state
  no-progress / completion / repeated-count state

Shared observation:
  concatenated augmented actor observations, repeated for each agent

Reward shaping:
  wrapper-local assignment-history reward terms
  decomposition logged under info["assignment_rl_reward"]

Masks:
  available_actions remains [num_envs, 3, 51]
  available_mask remains [num_envs, 3, 50]
```

No baseline solver path, controller path, mask semantics, feasibility logic, or environment dynamics were changed by
the observation/reward smoke chain.

## Still Reporting-Only

These signals remain reporting-only and do not affect reward in Phase 9B:

```text
duplicate selected target
noop when available
selected-target conflict
inter-robot overlap
actual base-motion crossing
obstacle selected-intersection
hard load-balance reward
```

Reasons:

```text
duplicate selected target and noop were zero in Phase 9B-1A
conflict-aware baselines showed proxy trade-offs and worse actual crossing
path/cost/overlap signals need calibration before reward promotion
hard load-balance could fight coverage unless feasibility/productivity are handled carefully
```

## Known Limitations

```text
fixed N=50/M=3 only
observation dimension grows linearly with N
not arbitrary-N Transformer/GNN/set policy yet
reward terms are smoke-tested only
no learned-policy quality claim
repeated no-progress gating may still need tuning for valid dwell/retry behavior
selected path cost is disabled because path cost alone can reinforce low-cost stuck behavior
```

The observation/reward interface is now suitable for the next small technical smoke, but it is not yet evidence that a
learned policy will outperform the Phase 8 baselines.

## Recommended Next Phase Options

Do not implement either option as part of this wrap-up. Both should be separately scoped.

### Option A: Phase 9C-0 Fresh-Policy Construction / Tensor-Flow Smoke

Goal:

```text
instantiate a fresh N=50 assignment actor path
verify augmented obs/action/mask/reward tensors pass through HARL-facing code
verify 51-class action head construction
verify available_actions reaches actor distribution
make no policy-quality claim
```

This is the smallest next technical check before any training.

### Option B: Phase 9C Training-Config Readiness Review

Goal:

```text
review episode_length and rollout horizon alignment
review reward scales and grace thresholds
review logging keys and output directories
review config naming and checkpoint compatibility
review smoke-vs-training command separation
run no training yet
```

Recommended path:

```text
Do Phase 9C-0 or a config readiness review before any actual N=50 training is scoped.
Do not evaluate old checkpoints on N=50.
```

## Explicit Non-Changes

Across Phase 9B, the following were not changed:

```text
available_mask semantics
feasible_mask semantics
static_geometric_feasible_mask semantics
solver behavior
controller logic
HARL internals or installed site-packages
environment dynamics
robot motion
collision, IK, raycast, local avoidance, path planning
retry/fallback/cooldown
RL training
formal RL evaluation
old checkpoint evaluation
handcrafted baseline rules
```

## Primary References

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
```
