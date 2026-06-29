# Phase 9B-1A Plateau Counter Diagnostic Report

Date: 2026-06-29

## Scope And Boundaries

Phase 9B-1A is a scoped non-RL baseline diagnostic rerun using the Phase 9B-1 reporting-only counters. The goal is to
make the Phase 8 late-stage plateau more explicit before any observation or reward implementation.

This is not RL training, not formal RL evaluation, not observation implementation, not reward implementation, and not a
new solver or controller phase.

No Python code was changed in this phase. No reward, observation, mask, feasibility, solver, controller, HARL,
environment dynamics, robot motion, collision, IK, raycast, local avoidance, path planning, retry, fallback, cooldown,
or handcrafted baseline behavior was changed. No commit was made.

## Command Run

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 2 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase9b1a_plateau_diagnostic_n50_e2_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

The full requested command completed successfully, so no reduced fallback run was needed.

## Output Directory

```text
results/assignment_evaluation/phase9b1a_plateau_diagnostic_n50_e2_s300/
```

Files:

```text
summary.csv
per_episode.csv
assignment_history.csv
diagnostics.json
```

`assignment_history.csv` contains 1,794 rows per method, matching 2 episodes x 299 effective decision steps x 3
robots.

## Compact Counter Table

All four methods reproduce the Phase 8 plateau: 45/50 final coverage, no full success, same final uncovered viewpoint
ids, and 182 no-progress steps after the last global coverage gain.

| method group | final coverage | final uncovered ids | last gain step | no-progress after last gain | per-robot selected mean | per-robot completed mean | per-robot repeated mean |
|---|---:|---|---:|---:|---|---|---|
| nearest / greedy | 0.900 | [0, 20, 24, 36, 48] | 117 | 182 | [299, 299, 299] | [23, 12, 5] | [275, 286, 293] |
| nearest_conflict_aware / greedy_conflict_aware | 0.900 | [0, 20, 24, 36, 48] | 117 | 182 | [299, 299, 299] | [23, 12, 5] | [275, 284, 293] |

| method group | duplicate selected target total/rate | noop when available total | selected path cost mean/max/sum | selected std | completed std |
|---|---:|---:|---|---:|---:|
| nearest / greedy | 0 / 0.0000 | 0 | 0.3153 / 2.9464 / 565.61 | 0.0000 | 7.4087 |
| nearest_conflict_aware / greedy_conflict_aware | 0 / 0.0000 | 0 | 0.3894 / 3.6101 / 698.66 | 0.0000 | 7.4087 |

| method group | selected-target conflict rate | inter-robot overlap rate | actual base-motion crossing rate |
|---|---:|---:|---:|
| nearest / greedy | 0.7191 | 0.6689 | 0.0167 |
| nearest_conflict_aware / greedy_conflict_aware | 0.6622 | 0.5753 | 0.1237 |

## Late-Stage Plateau Analysis

The new counters reproduce the Phase 8 plateau pattern cleanly.

Per episode:

```text
final_coverage = 0.900
final_covered_count = 45
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
last_global_coverage_gain_step = 117
no_progress_steps_after_last_gain = 182
episode_length = 299
```

The effective episode length is 299 decision steps in this evaluator path. The plateau length is therefore:

```text
299 - 117 = 182
```

This matches the Phase 8 stagnation conclusion.

## Repeated-Assignment Analysis

The late repeated assignment pattern is stable and method-group-specific only in ordering/count by one step:

Nearest / greedy, per episode:

```text
robot_1 -> viewpoint 48: 182 late repeated selections
robot_2 -> viewpoint 36: 182 late repeated selections
robot_0 -> viewpoint 20: 181 late repeated selections
```

Conflict-aware variants, per episode:

```text
robot_2 -> viewpoint 36: 182 late repeated selections
robot_0 -> viewpoint 20: 181 late repeated selections
robot_1 -> viewpoint 48: 181 late repeated selections
```

The per-robot repeated-assignment counts are very high across the whole episode:

```text
nearest / greedy: [275, 286, 293]
conflict-aware variants: [275, 284, 293]
```

This confirms that the plateau is not a coverage-count artifact. The baselines keep selecting the same non-progress
targets for most of the episode after the last coverage gain.

## Per-Viewpoint Attempt Analysis

Top attempted viewpoints across two episodes:

| method group | top attempted viewpoints |
|---|---|
| nearest / greedy | 36: 496, 48: 430, 20: 364, 8: 92, 2: 64 |
| conflict-aware variants | 36: 496, 20: 370, 48: 364, 8: 92, 7: 66 |

The final uncovered set is:

```text
[0, 20, 24, 36, 48]
```

The attempted-count concentration is mainly on three of those five final uncovered viewpoints:

```text
20, 36, 48
```

The other two final uncovered viewpoints:

```text
0, 24
```

receive zero attempts in these episodes. That means the failure has two components:

1. repeated no-progress attempts on selected uncovered viewpoints;
2. complete neglect of some remaining uncovered viewpoints.

Phase 9B-2 observations should expose both per-viewpoint attempted history and full uncovered/available state, not only
nearest slots.

## Duplicate And Noop Analysis

Exact duplicate selected targets are not meaningful for these baselines:

```text
duplicate_selected_target_count_total = 0
duplicate_selected_target_rate_mean = 0.0
```

This does not contradict the high selected-target conflict rate. The conflict metric is mostly about target proximity
or clustering, not identical viewpoint ids.

Noop is also not a failure mode in this rerun:

```text
noop_when_available_count_total = 0
noop_when_available_rate_mean = 0.0
```

For Phase 9B-2, duplicate-selected-target and noop-when-available should remain reporting/diagnostic features. They
are not the primary plateau explanation for these baselines.

## Selected Path Cost Analysis

The conflict-aware variants have higher selected path cost while achieving identical coverage:

```text
nearest / greedy:
  selected_path_cost_mean = 0.3153
  selected_path_cost_max = 2.9464
  selected_path_cost_sum_total = 565.61

conflict-aware variants:
  selected_path_cost_mean = 0.3894
  selected_path_cost_max = 3.6101
  selected_path_cost_sum_total = 698.66
```

The late repeated pairs often have low or zero selected path cost once the robot is already near the repeated target.
For example, after the plateau starts:

```text
robot_1 -> viewpoint 48: mean cost 0.00 in nearest/greedy
robot_2 -> viewpoint 36: mean cost 0.00 in all method groups
robot_0 -> viewpoint 20: mean cost 0.26
```

So path cost alone is not enough to break the plateau. A policy needs no-progress and repeated-attempt context, not
just a shorter selected target distance.

## Load-Balance Analysis

All methods select equally often:

```text
per_robot_selected_count_mean = [299, 299, 299]
load_balance_selected_std_mean = 0.0
```

But completed coverage credit is imbalanced:

```text
per_robot_completed_count_mean = [23, 12, 5]
load_balance_completed_std_mean = 7.4087
```

This suggests selected workload balance is not enough. Phase 9B-2 should expose productive completion balance, not only
assignment count balance.

## Conflict / Crossing Trade-Off Recap

The conflict-aware ablations still show the Phase 8 trade-off:

```text
selected_target_conflict_rate: 0.7191 -> 0.6622
inter_robot_overlap_rate: 0.6689 -> 0.5753
actual_base_motion_intersection_rate: 0.0167 -> 0.1237
coverage: unchanged at 0.900
```

They reduce selected-target and inter-robot proxy conflict metrics, but they do not improve final coverage and they
increase actual proxy base-motion crossing.

This is strong evidence to keep these conflict/crossing metrics reporting-only before using them as reward. Optimizing
one proxy conflict metric can worsen another execution-risk diagnostic.

## Required Analysis Answers

1. The new counters reproduce the Phase 8 plateau pattern: yes.
2. Final uncovered viewpoint ids are `[0, 20, 24, 36, 48]` for every method and episode.
3. `last_global_coverage_gain_step = 117`; `no_progress_steps_after_last_gain = 182`.
4. Dominant late repeated pairs are `robot_0 -> 20`, `robot_1 -> 48`, and `robot_2 -> 36`.
5. Per-robot repeated assignment values are high: around `[275, 286, 293]` or `[275, 284, 293]`.
6. Per-viewpoint attempts concentrate on final uncovered viewpoints 20, 36, and 48; viewpoints 0 and 24 remain uncovered
   with zero attempts.
7. Exact duplicate selected target count/rate are not meaningful for these baselines because they remain zero.
8. `noop_when_available_count` is zero.
9. Selected path cost shows conflict-aware variants choose costlier targets overall, while late repeated targets can
   have low/zero cost; path cost alone will not solve plateau behavior.
10. Selected-count balance is perfect, but completion balance is poor, so productive load balance matters.
11. Conflict-aware baselines reduce selected-target/inter-robot conflict while still failing coverage.
12. Conflict-aware baselines still increase actual base-motion crossing compared with nearest/greedy.
13. Phase 9B-2 observation should prioritize id-aligned viewpoint state, per-viewpoint attempted counts, previous
   assignment id, repeated-target count, steps since last coverage gain, per-robot completion counts, full uncovered
   state, and selected-target/crossing diagnostics as observable risk context.
14. Selected-target conflict, inter-robot overlap, actual base-motion crossing, exact duplicate target, noop, and path
   cost should remain reporting-only before immediate reward promotion.

## Observation-Design Implications

Prioritize these Phase 9B-2 observation signals:

```text
id-aligned full viewpoint rows for action ids 0..49
covered / uncovered flag per viewpoint
available and feasible state per robot-viewpoint pair
per-viewpoint attempted count
per-viewpoint last-attempt age
previous assignment id per robot
consecutive same-target count per robot
steps since last global coverage gain
per-robot completed count
per-robot repeated assignment count
selected-target proximity/conflict diagnostic context
actual base-motion crossing diagnostic context, likely critic/reporting first
selected path cost plus normalized cost-rank/advantage
```

The key missing state is not just geometry. The policy needs to know which targets have been tried repeatedly without
progress and which uncovered targets have been ignored.

## Reward-Design Caution Notes

Signals that look suitable for eventual reward candidates after observation/reporting stabilization:

```text
no-progress penalty with a grace window
repeated same-target penalty with dwell-aware gating
small path-cost shaping only as secondary objective
completion/load-balance shaping after feasibility-aware validation
```

Signals that should remain reporting-only for now:

```text
selected-target conflict
inter-robot overlap
actual base-motion crossing
exact duplicate selected target
noop when available
obstacle-aware selected-intersection metrics
```

Reasons:

- exact duplicate target and noop are zero in this rerun;
- conflict-aware target choices reduce some conflicts but increase actual base-motion crossing;
- actual base-motion crossing is still an approximate XY proxy;
- path cost alone can reinforce sitting on a repeated no-progress target.

## Verification Notes

No `py_compile` was required because Phase 9B-1A did not modify Python files.

The output files were inspected:

```text
summary.csv
per_episode.csv
assignment_history.csv
diagnostics.json
```

Spot checks:

```text
assignment_history rows per method = 1794
2 episodes x 299 decision steps x 3 robots = 1794
final_covered_count = 45 for all rows
new_viewpoints_total = 45 for all rows
duplicate_selected_target_count_total = 0
noop_when_available_count_total = 0
load_balance_selected_std_mean = 0.0
load_balance_completed_std_mean = 7.4087
```

Final checks:

```text
git diff --check: passed
git status --short:
  M scripts/environments/evaluate_assignment_methods.py
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
```

`git diff --check` emitted Windows LF-to-CRLF warnings only; no whitespace errors were reported.

## Explicit Non-Changes

Phase 9B-1A did not change:

```text
Python code
reward behavior
observation behavior
available_mask
feasible_mask
static_geometric_feasible_mask
solver behavior
controller logic
HARL internals
installed site-packages
environment dynamics
robot motion
collision / IK / raycast / local avoidance / path planning
retry / fallback / cooldown behavior
RL training
formal RL evaluation
handcrafted baseline rules
git commits
```

## Recommended Next Step

Use this report to scope Phase 9B-2 observation update smoke. Do not proceed directly to reward changes, RL training,
formal RL evaluation, new solvers, controller changes, masks, or fallback behavior.
