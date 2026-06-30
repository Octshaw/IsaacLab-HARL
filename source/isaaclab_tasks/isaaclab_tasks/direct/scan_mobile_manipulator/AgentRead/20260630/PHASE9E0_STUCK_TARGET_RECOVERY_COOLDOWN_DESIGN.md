# Phase 9E-0 Stuck-Target Recovery / Failed-Target Cooldown Design

## 1. Scope And Boundaries

Phase 9E-0 is a design-only phase for a narrow stuck-target recovery / failed-target cooldown mechanism.

The mechanism is motivated by Phase 9D-3 evidence that assignment RL can repeatedly select targets that are statically valid from the action interface but dynamically fail to produce new coverage.

This document does not implement the mechanism. It does not change training, reward formulas, reward scales, observation dimensions, masks, static feasibility, solver/controller behavior, environment dynamics, robot motion, collision, local avoidance, path planning, retry/fallback behavior, cooldown behavior, HARL algorithms, or installed site-packages.

No training, checkpoint playback, formal evaluation, reward tuning, or commit was performed for this phase.

## 2. Evidence From Phase 9D-3

Phase 9D-3 confirmed the post-logger-fix 100k training path is numerically healthy:

- `Total_Reward` now uses `assignment_rl_reward/final_reward_mean`.
- `steps_since_global_coverage_gain_mean` remains episode-scale after the Phase 9D-1A reset fix.
- No TensorBoard NaN/Inf was found in inspected scalar tags.
- Fixed assignment path remains N=50/M=3, noop id 50, `Discrete(51)` per robot.

However, deterministic playback showed severe late repeated assignment:

```text
100k models:
  final_coverage = 0.50
  max_same_target_streak = 282
  late targets = robot_0->44, robot_1->44, robot_2->15
  late targets remain available=true, feasible=true, covered_before=false, new_gain=false

100k best_model:
  final_coverage = 0.40
  max_same_target_streak = 282
  late targets = robot_0->39, robot_1->0, robot_2->15
  late targets remain available=true, feasible=true, covered_before=false, new_gain=false
```

The important evidence is not just repetition. It is repetition of targets that remain available, feasible, and uncovered according to the static assignment interface, while repeated selections do not produce coverage gain. This points to a dynamic progress failure that the current action mask cannot express.

Phase 8 baseline diagnostics showed a related plateau pattern: nearest/greedy reached about 45/50 coverage and then repeated late uncovered targets. RL currently covers less, but the bottleneck class is aligned: late targets can remain statically plausible while dynamically failing.

## 3. Problem Definition

A selected target should be considered dynamically non-progressing only when all of the following are true for a robot-target pair `(robot_i, viewpoint_j)`:

```text
selected_action != noop_id
selected_available == true in the pre-step assignment action mask
selected_feasible == true
covered_before == false
global_coverage_gain == 0 for the step
the same robot-target pair has repeated enough times, or has accumulated enough failed attempts
```

The mechanism should distinguish these cases:

- Static infeasible target: `feasible_mask=false` or `static_geometric_feasible_mask=false`; not a cooldown case because it should already be unavailable.
- Already covered target: `covered_before=true`; not a cooldown case because it is no longer a useful uncovered target.
- Duplicate same-step target: multiple robots select the same non-noop viewpoint in the same step; this is a coordination issue, not necessarily a failed-target issue.
- Temporary no-progress target: one or a few valid uncovered attempts with no gain; this is normal exploration and should not immediately trigger cooldown.
- Valid but dynamically non-progressing target: repeated valid uncovered attempts by a robot produce no global coverage gain past a threshold; this is the primary Phase 9E target.
- Permanently unreachable target: should not be inferred from one short horizon or one robot alone. Treat this as a diagnostic category only, or as a future team-level escalation after multiple robots and episodes fail.

The Phase 9E-1 design should be conservative: it should interrupt obvious repeated local failure without permanently hiding viewpoints.

## 4. Existing Signals And Current Limitations

Existing wrapper-local signals in `AssignmentHarlWrapper`:

```text
_per_viewpoint_attempted_count: [num_envs, num_viewpoints]
_last_viewpoint_attempt_step: [num_envs, num_viewpoints]
_previous_assignment: [num_envs, num_agents]
_same_target_streak: [num_envs, num_agents]
_steps_since_global_coverage_gain: [num_envs]
_per_robot_completed_count: [num_envs, num_agents]
_per_robot_repeated_assignment_count: [num_envs, num_agents]
_per_robot_selected_count: [num_envs, num_agents]
_last_covered_mask: [num_envs, num_viewpoints]
```

Existing observation extension already includes:

- per-viewpoint covered flag
- per-agent available flag
- feasible and static-feasible flags
- normalized selected path cost
- per-viewpoint attempted count
- per-viewpoint last-attempt age
- previous assignment one-hot
- same-target streak
- steps since last global coverage gain
- per-robot completed/repeated counts
- global coverage ratio
- covered vector

Existing action mask path:

```text
env.get_assignment_problem()["available_mask"]
  = feasible_mask & ~viewpoints_covered

make_assignment_action_mask(problem, include_noop=True)
  -> [num_envs, num_agents, num_viewpoints + 1]
  -> appends always-available noop
```

Current limitation:

The mask represents static feasibility and already-covered status, but not dynamic execution failure. A viewpoint can remain available/feasible/uncovered even after repeated selected attempts fail to produce new coverage.

Existing reward shaping has mild repeated/no-progress penalties, but Phase 9D-3 shows reward-only shaping is not currently enough to break severe repeated assignment.

There is also an evaluator-only retry/fallback cooldown path inside `evaluate_assignment_methods.py`. That is useful as a design precedent, but it is not part of the assignment RL training wrapper and should not be mistaken for a trained-policy mechanism.

## 5. Candidate Mechanisms

| option | behavior | expected benefit | risk | coverage effect | exploration effect | fixed N now / variable N later | changes |
|---|---|---|---|---|---|---|---|
| A. Per-robot-target cooldown | After repeated failures, only `robot_i` cannot select `viewpoint_j` for C steps | Breaks local repeated loops while allowing other robots to try the target | May hide a difficult but solvable target from the most capable robot temporarily | Should reduce late streaks; coverage should not decrease if duration/threshold are conservative | Encourages per-robot exploration of alternatives | Natural tensor shape `[E,A,V]`; works for variable N/M if allocated dynamically | RL action mask + diagnostics |
| B. Team-target cooldown | After team-level failures, all robots avoid `viewpoint_j` for C steps | Prevents all robots from piling onto one stuck viewpoint | Can prematurely suppress a target that another robot could solve | May improve duplicate/conflict metrics but can lower coverage | Stronger exploration pressure, but also stronger target hiding | Tensor shape `[E,V]`; variable N simple | RL action mask + diagnostics |
| C. Hybrid cooldown | Start per-robot; promote to team cooldown only after multiple robots fail | Balances local recovery and team-level stuck handling | More state and harder attribution | Could help cases like `robot_0` and `robot_1` both stuck on 44 | More structured exploration | Needs `[E,A,V]` plus optional `[E,V]`; still scalable | RL action mask + diagnostics |
| D. Reward-only stronger penalty | Keep masks unchanged; increase penalties for failed/repeated targets | No action-space intervention; policy can still choose target | Phase 9D evidence suggests reward-only may not break loops; tuning can destabilize or bias to noop | Uncertain; could reduce coverage if too punitive | Leaves exploration entirely learned | Architecture-independent | Reward formula/scale change |
| E. Diagnostic-only first | Add failed-attempt/cooldown diagnostics, no behavior change | Low risk and useful instrumentation | Does not address stuck behavior | No expected behavior improvement | No effect | Fully compatible | Diagnostics only |

Recommended for Phase 9E-1: Option A, per-robot-target temporary cooldown, config-gated and disabled by default. It is the smallest behavior change that directly addresses the observed repeated robot-target loops while avoiding immediate team-level target suppression.

Option C should remain a future escalation if multiple robots repeatedly fail the same target after per-robot cooldown is validated. Option D should remain future work; do not tune reward in the first cooldown implementation.

## 6. Recommended Minimal Phase 9E-1 Mechanism

Implement a configurable, wrapper-local, assignment-RL-only per-robot-target temporary cooldown.

Concept:

```text
If robot_i selects viewpoint_j,
and viewpoint_j was available/feasible/uncovered before the step,
and no global coverage gain occurs after the step,
and the robot-target pair has failed K times or repeated for S same-target streak steps,
then mark (robot_i, viewpoint_j) as cooldown for C assignment steps.

While cooldown is active:
  remove viewpoint_j from robot_i's available action mask
  keep noop available
  keep viewpoint_j available for other robots
  decrement cooldown each assignment step
  clear cooldown if viewpoint_j becomes covered
```

Recommended Phase 9E-1 boundaries:

- Assignment RL wrapper-local only.
- Config-gated.
- Disabled by default globally.
- No static feasibility change.
- No physical controller change.
- No viewpoint generation change.
- No baseline solver behavior change.
- No reward formula or reward scale change.
- No observation dimension change.
- Add diagnostics so the effect is visible in training logs and playback outputs.

This mechanism modifies only the HARL `available_actions` mask for assignment RL when explicitly enabled. It does not make a physical claim about reachability or collision.

## 7. Proposed State Variables

Required state:

```text
_per_robot_target_failed_attempt_count: [num_envs, num_agents, num_viewpoints], torch.long
_per_robot_target_cooldown_remaining: [num_envs, num_agents, num_viewpoints], torch.long
```

Recommended diagnostic counters:

```text
_assignment_cooldown_trigger_count: [num_envs], torch.float32
_assignment_cooldown_active_count: [num_envs], torch.float32 or derived on demand
_assignment_cooldown_suppressed_count: [num_envs, num_agents], torch.float32 or derived on demand
_assignment_cooldown_last_triggered_viewpoint: [num_envs, num_agents], torch.long
```

Optional future team-level state:

```text
_team_target_failed_attempt_count: [num_envs, num_viewpoints]
_team_target_cooldown_remaining: [num_envs, num_viewpoints]
```

Reset behavior:

- Full reset: zero failed-attempt counts and cooldown remaining.
- Done-env partial reset: zero only the completed env ids, using the same partial reset path fixed in Phase 9D-1A.
- Target covered: clear failed-attempt counts and cooldown remaining for that viewpoint across all robots in the env.
- Global coverage gain: do not necessarily clear all state; clear only selected target failures that succeeded or all current same-target streak state if the implementation follows the existing wrapper logic. Keep this conservative and document it in the implementation report.
- Episode boundary: all cooldown state is episode-local and must reset.
- Checkpoint/playback consistency: state is runtime wrapper state only, not model state. Checkpoints remain shape-compatible if observation dimensions do not change.

Trigger update timing:

1. Build the pre-step available action mask with current cooldowns.
2. Decode selected assignment.
3. Step the env and compute terminal reward/logs from pre-reset state.
4. Update failed-attempt and cooldown state from pre/post coverage.
5. If done envs exist, reset cooldown/history state before next observation/mask.
6. Build the returned next available action mask with updated cooldowns.

This preserves terminal-step reward timing while making the next policy decision see the cooldown-filtered mask.

## 8. Proposed Action-Mask Interaction

Cooldown should be applied after static feasibility and covered-state masking, and before the noop column is appended.

Current logical mask:

```text
base_available_mask = feasible_mask & ~viewpoints_covered
available_actions = concat(base_available_mask, noop_column)
```

Proposed enabled path:

```text
cooldown_mask = _per_robot_target_cooldown_remaining > 0
filtered_available_mask = base_available_mask & ~cooldown_mask
available_actions = concat(filtered_available_mask, noop_column)
```

Important details:

- Keep noop available.
- Preserve shape `[num_envs, num_agents, num_viewpoints + 1]`.
- Avoid all-zero action rows by preserving noop. If `include_noop=False` is ever used, cooldown must either be disabled or must guarantee at least one viewpoint remains available.
- Do not mutate the environment's `available_mask`; keep cooldown filtering inside the wrapper.
- `selected_available_mask` should be computed against the filtered pre-step action mask so diagnostics reflect the actual RL action availability.
- `viewpoint_j` remains available to other robots unless team cooldown is explicitly enabled in a later phase.

Recommended diagnostic fields:

```text
assignment_cooldown/enabled
assignment_cooldown/active_count_mean
assignment_cooldown/trigger_count_mean
assignment_cooldown/suppressed_action_count_mean
assignment_cooldown/failed_attempt_count_mean
assignment_cooldown/max_cooldown_remaining_mean
assignment_cooldown/selected_target_was_in_cooldown_count
```

For playback history, add fields such as:

```text
cooldown_active_for_selected_pair
cooldown_remaining_for_selected_pair
cooldown_triggered_after_step
cooldown_suppressed_available_count_for_robot
failed_attempt_count_for_selected_pair
```

`cooldown_selected_target_before_mask` is hard to observe after masked policy sampling because the policy should not select masked actions. If logits or unmasked candidate preferences are later needed, that should be a separate diagnostic.

## 9. Proposed Observation And Checkpoint-Compatibility Decision

Phase 9E-1 should not add observation dimensions.

Preferred Phase 9E-1 behavior:

- No new per-viewpoint cooldown flag in the actor observation.
- No new scalar cooldown counts in the actor observation.
- Keep actor obs at `[1, 909]` and shared obs at `[1, 3, 2727]` for fixed N=50/M=3.
- Apply cooldown only through `available_actions`.
- Log cooldown state through diagnostics and TensorBoard/log_info instead.

This keeps old and new actor network shapes compatible. Old checkpoints can still be loaded for diagnostic playback with cooldown enabled, though behavior can differ because the action mask differs.

Observation caveat:

The current observation includes an `available_flag` in the viewpoint rows. A strict mask-only implementation may leave this flag as the raw environment availability, while the action mask removes cooldown targets. This preserves observation semantics but means cooldown is visible only through the policy's action mask. That is acceptable for Phase 9E-1 because it isolates the intervention and avoids checkpoint incompatibility.

Future option:

If mask-only cooldown causes policy confusion, add an explicit per-viewpoint cooldown flag or cooldown remaining value. That would be a new observation semantic and may break old checkpoint compatibility; it should be a separate phase.

## 10. Proposed Reward Decision

Do not change reward formulas or reward scale defaults in Phase 9E-1.

Reasons:

- Phase 9D-3 already shows a behavior-level stuck loop even with existing repeated/no-progress penalties.
- A mask-only cooldown is easier to isolate than simultaneous mask and reward changes.
- Reward changes would complicate comparison to Phase 9D-3 and could incentivize conservative noop behavior.

Future reward options, not Phase 9E-1:

```text
cooldown_trigger_penalty
failed-target penalty
path-risk penalty
overlap/crossing penalty
team duplicate penalty
```

If these are explored later, they should be separate ablations with their own TensorBoard/accounting checks.

## 11. Proposed Config Parameters

Suggested config names:

```yaml
assignment_cooldown_enabled: false
assignment_cooldown_scope: per_robot_target
assignment_cooldown_trigger_attempts: 3
assignment_cooldown_trigger_same_target_streak: 10
assignment_cooldown_trigger_steps_since_global_gain: 10
assignment_cooldown_duration_steps: 20
assignment_cooldown_require_uncovered: true
assignment_cooldown_require_available: true
assignment_cooldown_require_feasible: true
assignment_cooldown_require_no_global_gain: true
assignment_cooldown_clear_on_covered: true
assignment_cooldown_apply_to_action_mask: true
assignment_cooldown_log_diagnostics: true
assignment_cooldown_team_promotion_enabled: false
assignment_cooldown_team_promotion_failed_robot_count: 2
```

Default policy:

- Global/default config disabled to preserve previous behavior.
- A dedicated Phase 9E-1 experiment scenario or explicit override can enable it.
- Do not enable cooldown in `algorithm_proxy_component_mesh.yaml` by default unless the phase explicitly creates a new experiment variant.

Initial value rationale:

- `trigger_attempts=3` avoids cooling after a single transient failure.
- `trigger_same_target_streak=10` is far below observed 282-step streaks but high enough to avoid immediate overreaction.
- `trigger_steps_since_global_gain=10` avoids cooldown while the team is still making frequent coverage progress.
- `duration_steps=20` is long enough to force alternative choices but short enough to retry later.

These values are starting points for a smoke/debug experiment, not tuned final values.

## 12. Diagnostics And Metrics

Minimum success criteria for Phase 9E-1:

```text
max_same_target_streak decreases substantially
late_repeated_assignment_count decreases
final_coverage does not decrease versus Phase 9D-3 no-cooldown reference
coverage_auc does not decrease
selected_available_mask remains valid
no all-zero action mask
no NaN/Inf in obvious scalar logs
episode reset remains correct
```

Secondary metrics:

```text
final_uncovered_viewpoint_ids
cooldown_trigger_count
cooldown_active_count
cooldown_suppressed_count
cooldown_failed_attempt_count
duplicate_selected_target_rate
noop_when_available_rate
selected_target_conflict_rate
inter_robot_overlap_rate
actual_base_motion_intersection_rate
selected_path_cost_mean
selected_path_cost_max
per_robot_selected_count
per_robot_completed_count
per_robot_repeated_assignment_count
```

Failure modes to watch:

```text
cooldown causes excessive noop
cooldown hides too many valid targets
robots oscillate between cooldown targets
coverage falls
coverage AUC falls
conflict/crossing improves only because robots do less useful work
best_model becomes conservative, low-conflict, low-coverage behavior
cooldown state leaks across episode resets
old checkpoints load but behave unexpectedly due mask-only intervention
```

## 13. Evaluation Plan

Phase 9E-1 validation should be staged:

1. Unit-like mask/state smoke:
   - Directly exercise cooldown state update and mask filtering.
   - Confirm noop remains available.
   - Confirm target-covered and reset clearing.

2. Wrapper reset smoke:
   - Run slightly past one 300-step horizon.
   - Confirm cooldown state resets on done-env partial reset.
   - Confirm actor obs/shared obs shapes remain unchanged if mask-only.

3. Tiny training-entry smoke:
   - Very small fixed N=50/M=3 run.
   - Confirm no shape crash, no all-zero mask, cooldown diagnostics logged.

4. One 100k single-seed debug run with cooldown enabled:
   - Same fixed scenario.
   - Reward unchanged.
   - Compare against Phase 9D-3 no-cooldown 100k.

5. Playback diagnostics:
   - Run `evaluate_assignment_rl_playback_diagnostics.py` on `models` and `best_model`.
   - Add cooldown fields to playback output if implemented.
   - Compare deterministic metrics to Phase 9D-3.

6. Only if promising:
   - Multi-seed debug training.
   - Baseline comparison using aligned Phase 7/8/9D metrics.

Do not treat a single deterministic playback as policy-quality proof.

## 14. Risks And Failure Modes

Main risks:

- The cooldown masks a difficult but ultimately solvable target from the robot most capable of covering it.
- Cooldown reduces repeated assignment but increases noop or aimless target switching.
- Coverage remains low because the true blocker is controller/geometry/path execution rather than assignment choice.
- Team-level issues persist because per-robot cooldown lets another robot repeatedly try the same failing target.
- Conflict/crossing metrics improve only because useful work decreases.
- Mask-only cooldown may be opaque to the observation, causing policy learning friction.
- Adding diagnostics to logs without careful naming could pollute future accounting if logger whitelisting is bypassed.

Mitigations:

- Keep cooldown temporary, not permanent.
- Keep it per-robot first, not team-wide.
- Keep reward unchanged for the first ablation.
- Keep global default disabled.
- Log cooldown activation/suppression counts.
- Require no coverage regression as a primary success criterion.
- Continue using exact reward accumulator whitelist.

## 15. Explicit Non-Goals

Phase 9E is not:

- physical collision avoidance
- local avoidance
- path planning
- IK or controller repair
- raycast coverage repair
- static feasibility change
- viewpoint generation change
- solver rewrite
- new handcrafted baseline rule
- reward tuning phase
- arbitrary-N Transformer/GNN phase
- formal evaluation phase
- policy-quality claim phase

Cooldown is a task-assignment recovery mechanism, not a motion-planning solution.

## 16. Recommended Phase 9E-1 Implementation Plan

Recommended next phase:

```text
Phase 9E-1: implement config-gated per-robot-target cooldown as an assignment-RL wrapper-local mask mechanism with diagnostics, reward unchanged.
```

Implementation outline:

1. Add config fields with global defaults disabled.
2. Read config in `AssignmentHarlWrapper` from the wrapped env cfg.
3. Add wrapper-local cooldown state tensors allocated from runtime `num_envs`, `num_agents`, and `num_viewpoints`.
4. Extend the existing assignment diagnostics reset helper so full and partial env-id resets clear cooldown state.
5. Apply cooldown filtering inside wrapper available-action construction, without mutating env `available_mask`.
6. Keep noop available and assert no all-zero action rows.
7. Update cooldown state after each env step using pre-step selected target and pre/post coverage.
8. Clear cooldown/failed counts when a viewpoint becomes covered.
9. Add diagnostics to `info["assignment_rl"]` or a dedicated `assignment_cooldown` block.
10. Extend no-training wrapper smokes and playback diagnostics to record cooldown state.
11. Run tiny smoke and one scoped debug training run only after the implementation passes shape/reset checks.

First implementation should not change observation dimensions or reward formulas. If the first ablation shows reduced streaks but poor coverage, decide separately whether team-target cooldown, cooldown observation features, path-risk filtering, or reward changes are justified.

## 17. Validation

No Python/code files were changed in Phase 9E-0, so no `py_compile` was required.

Repository checks:

```text
git diff --check = passed, with TASK_PROGRESS.md LF/CRLF warning only
```

Observed `git status --short`:

```text
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
```

No commit was made.
