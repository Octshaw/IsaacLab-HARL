# Phase 9A RL Dynamic-Policy Readiness Plan

Date: 2026-06-28

## 1. Purpose

Phase 9A checks whether the current real-component proxy task-allocation environment is ready for RL/dynamic-policy
evaluation planning.

This plan does not start training. It does not start RL evaluation. It does not change rewards, observations, masks,
solvers, controllers, HARL, or environment behavior. It is an audit/readiness phase.

The target research direction remains:

```text
dynamic multi-robot task allocation for arbitrary-size viewpoint sets and variable numbers of robots
```

with emphasis on:

```text
dynamic assignment
load balancing
path cost
robot state changes
task state updates
```

## 2. Why Phase 9A Is Needed After Phase 8

Phase 8 showed that the real-component proxy baseline is stable enough for further task-allocation research, but the
existing baselines are not sufficient final policies.

Key Phase 8 findings:

- nearest, greedy, and both conflict-aware ablations plateau at 45/50 coverage;
- no method reaches full success;
- late repeated assignment persists after step 116;
- conflict-aware ablations reduce selected-target and inter-robot conflict metrics;
- conflict-aware ablations increase actual proxy base-motion component-footprint crossing risk.

This means the next step should not be another handcrafted baseline rule. The next step should check whether the RL
interface exposes enough state, action masking, and reward signal to learn dynamic behavior.

## 3. Current Baseline Reference Table

Main Phase 8 run: N=50, M=3, 10 episodes, 300 steps.

| method | success rate | final coverage | coverage AUC | selected-target conflict rate | inter-robot overlap rate | actual base-motion crossing rate |
|---|---:|---:|---:|---:|---:|---:|
| random | 0.0 | 0.004 | 0.0038 | 0.4157 | 0.6759 | 0.9050 |
| nearest | 0.0 | 0.900 | 0.7468 | 0.7191 | 0.6689 | 0.0167 |
| greedy | 0.0 | 0.900 | 0.7468 | 0.7191 | 0.6689 | 0.0167 |
| nearest_conflict_aware | 0.0 | 0.900 | 0.7468 | 0.6622 | 0.5753 | 0.1237 |
| greedy_conflict_aware | 0.0 | 0.900 | 0.7468 | 0.6622 | 0.5753 | 0.1237 |

Stagnation baseline:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
late repeated assignments:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
```

Phase 9A should use this table as the non-RL baseline reference.

## 4. RL Interface Compatibility Checks

Inspect whether the current RL/HARL wrapper supports:

```text
N = 50 viewpoints
M = 3 robots
action_dim = N + noop, where noop_id = N
available_actions shape = [num_envs, M, N + 1]
per-agent action masks
done/reset semantics
episode length = 300
current observation shape
current shared observation shape, if used
current reward fields
```

Recommended files to inspect:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/agents/harl_happo_cfg.yaml
scripts/environments/evaluate_assignment_methods.py
```

Questions to answer:

1. Does the wrapper infer N and M dynamically from the environment?
2. Does the HARL config assume fixed action width or fixed agent count?
3. Are old fixed-12 checkpoints incompatible with N=50, as expected?
4. Can a policy be evaluated without shape mismatch?
5. Are masks passed in the format expected by HARL/MAPPO?

## 5. Observation-Space Audit

Separate observation fields into four groups.

Already present:

```text
coverage/completion state, if present in observations
robot/scanner pose state, if present in observations
available action mask, if exposed to policy path
task/robot status fields, if exposed beyond diagnostics
```

Present only in diagnostics:

```text
selected-target conflict
inter-robot overlap
actual base-motion component crossing
mesh-footprint selected-intersection diagnostics
late repeated assignment patterns from assignment_history.csv
```

Missing but probably needed:

```text
no-progress state
attempted viewpoint history
repeated selection history
current assigned target or selected target memory
robot-to-viewpoint cost matrix or compact cost features
load-balance proxy
inter-robot proximity risk as observation, not only diagnostics
component crossing / obstacle risk as observation, not only diagnostics
```

Optional future features:

```text
learned or generated viewpoint importance
ROI weights
path-planning features
3D collision/raycast features
real robot articulation state
```

Phase 9A should audit what the policy can actually see before deciding whether current RL evaluation is meaningful.

## 6. Action-Space And Mask Audit

Check:

```text
whether covered viewpoints are masked
whether unavailable viewpoints are masked
whether static feasible mask is used
whether duplicate assignment is prevented, penalized, or allowed
whether noop is allowed and when
whether action masks are compatible with HARL/MAPPO
whether conflict-aware or obstacle-aware costs remain diagnostics-only
whether the policy can distinguish covered-but-still-available, failed, timeout, unreachable, and no-progress states
```

Expected invariant:

```text
N = number of loaded viewpoints
M = number of enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

Do not change masks in Phase 9A. Audit and report only.

## 7. Reward Audit

Check whether the current reward captures:

```text
coverage gain
completion bonus
invalid action penalty
duplicate assignment penalty
noop penalty or neutrality
no-progress penalty
repeated assignment penalty
selected-target conflict penalty
inter-robot overlap penalty
actual base-motion crossing penalty
load-balance reward / penalty
path-cost penalty
task failure / timeout / unreachable handling
```

Do not add reward changes in Phase 9A. The output should be a table:

```text
reward concept | current status | evidence/source | recommendation
```

Use Phase 8 as motivation: a reward that does not penalize no-progress or repeated late selections may reproduce the
same plateau under RL.

## 8. Diagnostic Metrics To Carry Into RL Evaluation

Carry forward Phase 8 metrics:

```text
final_coverage
coverage_auc
success_rate
selected_target_conflict_rate
inter_robot_overlap_rate
actual_base_motion_intersection_rate
last_coverage_gain_step
no_progress_steps_after_last_gain
final_uncovered_viewpoint_ids
late_repeated_assignment_pattern
selected_intersection_rate
selected_obstacle_penalty_sum
valid_action_rate
noop_rate
```

Add later if reporting-only:

```text
per_robot_completed_count
per_robot_selected_count
load_balance proxy
per_robot repeated assignment count
per-viewpoint attempted count
```

These metrics should be used for RL evaluation reporting, not necessarily as rewards.

## 9. N=50, M=3 Fixed-Scale Compatibility Smoke

Before RL evaluation, run only a compatibility smoke that checks shapes and mask plumbing. Do not run training.

Suggested lightweight checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Inspect or run the smallest existing wrapper smoke that can report:

```text
num_agents == 3
num_viewpoints == 50
noop_id == 50
available_actions shape == [1, 3, 51]
available_mask shape == [1, 3, 50]
observation shape
share_observation shape, if applicable
```

If a HARL policy checkpoint is considered, first verify whether its action dimension matches N=50. Do not attempt
evaluation if it is an old fixed-12 checkpoint.

## 10. Risks / Limitations

- Existing trained checkpoints may be fixed to N=12 and incompatible with N=50.
- The current observation may not include no-progress, repeated-attempt, conflict, crossing, or load-balance state.
- Diagnostics may exist only in evaluator outputs, not in the policy observation.
- Reward may not penalize the exact failure modes seen in Phase 8.
- Proxy base-motion crossing remains approximate XY-only.
- N=50 proxy validation is not final benchmark evidence.

## 11. Do-Not-Do Boundaries

Do not do any of the following in Phase 9A:

```text
start RL training
start long RL evaluation
modify HARL internals or installed site-packages
change solver behavior
add new solver rules
change available_mask / feasible_mask / static_geometric_feasible_mask
promote obstacle or conflict diagnostic costs into live solver inputs
change reward
change controller logic
change assignment_controller.py
add physical collision, IK, path planning, ORCA, local avoidance, raycast planner, retry fallback, or cooldown
use final real planned CSV
claim N=50 proxy results are final benchmark evidence
```

## 12. Success Criteria

Phase 9A is complete when it produces a report that answers:

1. Whether the current RL/HARL interface supports N=50, M=3 without shape mismatch.
2. Whether current observations expose the information needed to avoid Phase 8 stagnation.
3. Whether current action masks reflect the intended dynamic assignment semantics.
4. Whether reward currently encourages coverage without reinforcing repeated/no-progress behavior.
5. Which Phase 8 diagnostics should be included in any RL comparison.
6. Whether an existing checkpoint can be evaluated or must be considered incompatible.
7. What minimum changes, if any, should be scoped before RL evaluation or retraining.

## 13. Recommended Commands / Files To Inspect

Files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/agents/harl_happo_cfg.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
```

Commands should be limited to interpreter checks, syntax checks if files change, and the smallest wrapper smoke needed
to inspect RL interface shapes.

## 14. Expected Next Step After Phase 9A

If the interface is compatible and observations/rewards are adequate:

```text
Phase 9B: short RL evaluation smoke against the Phase 8 baseline table
```

If the interface is compatible but observations/rewards are inadequate:

```text
Scope a small observation/reward design phase before RL evaluation or retraining
```

If old checkpoints are incompatible with N=50:

```text
Document incompatibility and prepare a carefully scoped retraining plan; do not launch training automatically
```
