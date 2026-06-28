# Phase 8 Real-Component Proxy Baseline Validation Report

Date: 2026-06-28

## Why Phase 8 Was Started

Phase 8 returns from obstacle/conflict diagnostic tooling to the main task-allocation question:

```text
In a real-component mesh + proxy-robot environment, do the baseline task-allocation methods remain stable, and do the
previous no-progress / repeated-assignment issues still appear?
```

Phase 7E added actual proxy base-motion mesh-footprint crossing diagnostics. Phase 8 carries those diagnostics forward
while evaluating existing baseline methods only.

This phase is evaluation and reporting only. It does not change solver behavior, masks, costs, rewards, controller
logic, HARL, training, environment dynamics, robot motion, collision, IK, path planning, hard blocking, or final real
CSV validation.

## Scenario And Viewpoint Source

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Task:

```text
Isaac-Scan-Mobile-Manipulator-Direct-v0
```

Viewpoint source:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv
```

The run uses N=50 and M=3. This is real-component proxy validation data, not final algorithm benchmark evidence and
not the final real planned CSV.

Active diagnostic blocks included:

```text
obstacle_diagnostics.enabled: true
actual_base_motion_obstacle_diagnostics.enabled: true
obstacle_debug_visualization.line_source: selected_assignments
inter_robot_conflict_diagnostics.enabled: true
selected_target_conflict_candidate_comparison.enabled: true
conflict_aware_baseline.enabled: true
```

## Methods Evaluated

Primary baselines:

```text
random
nearest
greedy
```

Phase 7D-2 ablation baselines:

```text
nearest_conflict_aware
greedy_conflict_aware
```

The original `random`, `nearest`, and `greedy` methods remain unchanged. The conflict-aware methods remain labeled
baseline ablations.

## Commands Run

Interpreter check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Smoke validation:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 2 --max_steps 80 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase8_baseline_smoke_n50_e2_s80 --write_assignment_history --compare_obstacle_aware_candidates
```

Main validation:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 10 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase8_baseline_n50_e10_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

Output inspection used stdlib CSV/JSON readers over:

```text
summary.csv
per_episode.csv
assignment_history.csv
diagnostics.json
```

## Output Directories

```text
results/assignment_evaluation/phase8_baseline_smoke_n50_e2_s80/
results/assignment_evaluation/phase8_baseline_n50_e10_s300/
```

Each output directory contains:

```text
summary.csv
per_episode.csv
assignment_history.csv
diagnostics.json
```

## Smoke Result

The 2-episode, 80-step smoke completed for all five methods.

| method | final coverage | coverage AUC | target conflict rate | overlap rate | actual base-motion crossing rate |
|---|---:|---:|---:|---:|---:|
| random | 0.020 | 0.0157 | 0.475 | 0.2125 | 0.6813 |
| nearest | 0.700 | 0.3758 | 0.000 | 0.0000 | 0.0000 |
| greedy | 0.700 | 0.3758 | 0.000 | 0.0000 | 0.0000 |
| nearest_conflict_aware | 0.700 | 0.3758 | 0.000 | 0.0000 | 0.0000 |
| greedy_conflict_aware | 0.700 | 0.3758 | 0.000 | 0.0000 | 0.0000 |

## Main Coverage Table

Main run: `num_envs=1`, `num_episodes=10`, `max_steps=300`, N=50, M=3.

| method | episodes | success rate | mean return | final coverage | final covered count | coverage AUC | steps to full | valid action rate | noop rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 10 | 0.000 | -11.601 | 0.004 | 0.2 / 50 | 0.0038 | -1.0 | 1.000 | 0.000 |
| nearest | 10 | 0.000 | 737.657 | 0.900 | 45.0 / 50 | 0.7468 | -1.0 | 1.000 | 0.000 |
| greedy | 10 | 0.000 | 737.657 | 0.900 | 45.0 / 50 | 0.7468 | -1.0 | 1.000 | 0.000 |
| nearest_conflict_aware | 10 | 0.000 | 738.006 | 0.900 | 45.0 / 50 | 0.7468 | -1.0 | 1.000 | 0.000 |
| greedy_conflict_aware | 10 | 0.000 | 738.006 | 0.900 | 45.0 / 50 | 0.7468 | -1.0 | 1.000 | 0.000 |

No method reached full coverage in the 300-step horizon.

## Spatial Diagnostics Table

| method | selected-target conflict rate | selected-target pairs | target min clearance | inter-robot overlap rate | overlap pairs | overlap min clearance |
|---|---:|---:|---:|---:|---:|---:|
| random | 0.4157 | 1,444 | -0.8391 | 0.6759 | 4,282 | -0.8482 |
| nearest | 0.7191 | 5,790 | -0.7757 | 0.6689 | 5,210 | -0.7757 |
| greedy | 0.7191 | 5,790 | -0.7757 | 0.6689 | 5,210 | -0.7757 |
| nearest_conflict_aware | 0.6622 | 5,620 | -0.7757 | 0.5753 | 5,000 | -0.7757 |
| greedy_conflict_aware | 0.6622 | 5,620 | -0.7757 | 0.5753 | 5,000 | -0.7757 |

Conflict-aware ablations reduced selected-target conflict count and inter-robot overlap count versus nearest/greedy:

```text
selected_target_conflict_pair_count_total: 5790 -> 5620
inter_robot_overlap_pair_count_total: 5210 -> 5000
```

They did not improve worst clearance, coverage, coverage AUC, or full-coverage success.

## Actual Base-Motion Crossing Table

Actual base-motion crossing measures executed proxy base segments:

```text
previous robot base XY -> current robot base XY
```

This is not the selected assignment line and not full 3D collision checking.

| method | crossing steps | crossing rate | crossing pairs | min dist to footprint | mean min dist | valid robot count mean | skipped robot count | crossing by robot |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| random | 2,706 | 0.9050 | 7,565 | 0.0 | 0.0927 | 2.990 | 30 | r0: 2562, r1: 2704, r2: 2299 |
| nearest | 50 | 0.0167 | 50 | 0.0 | 0.7406 | 0.926 | 6,200 | r0: 50, r1: 0, r2: 0 |
| greedy | 50 | 0.0167 | 50 | 0.0 | 0.7406 | 0.926 | 6,200 | r0: 50, r1: 0, r2: 0 |
| nearest_conflict_aware | 370 | 0.1237 | 370 | 0.0 | 0.5936 | 1.040 | 5,860 | r0: 50, r1: 320, r2: 0 |
| greedy_conflict_aware | 370 | 0.1237 | 370 | 0.0 | 0.5936 | 1.040 | 5,860 | r0: 50, r1: 320, r2: 0 |

Conflict-aware ablations increased actual base-motion crossing relative to nearest/greedy:

```text
actual_base_motion_intersection_step_count_total: 50 -> 370
actual_base_motion_intersection_rate_mean: 0.0167 -> 0.1237
```

This is the main Phase 8 trade-off: the conflict-aware ablations reduce selected-target/inter-robot conflict metrics but
increase component-footprint crossing risk under the current proxy execution model.

## Obstacle Diagnostic Candidate Analysis

Obstacle-aware candidate comparison remains diagnostic-only and does not feed the live solvers.

| method | selected pairs | selected intersections | selected intersection rate | selected obstacle penalty | candidate changed count | candidate intersection rate | candidate obstacle penalty |
|---|---:|---:|---:|---:|---:|---:|---:|
| random | 8,970 | 8,392 | 0.9356 | 839,200 | 0 | unavailable | unavailable |
| nearest | 8,970 | 70 | 0.0078 | 7,000 | 10 | 0.0067 | 6,000 |
| greedy | 8,970 | 70 | 0.0078 | 7,000 | 10 | 0.0067 | 6,000 |
| nearest_conflict_aware | 8,970 | 450 | 0.0502 | 45,000 | 0 | unavailable | unavailable |
| greedy_conflict_aware | 8,970 | 450 | 0.0502 | 45,000 | 0 | unavailable | unavailable |

The copied-problem obstacle-aware candidate was only compared for nearest/greedy. It changed 10 robot-step decisions
across 10 episodes and reduced selected-intersection count from 70 to 60. It was not executed.

## Conflict-Aware Ablation Details

The executed conflict-aware baseline variants changed 100 robot-step decisions versus their base method:

```text
conflict_aware_changed_vs_base_count_total = 100
conflict_aware_changed_vs_base_rate_mean = 0.011148272350081633
conflict_aware_fallback_step_count_total = 0
```

Typical changed pair:

```text
robot_1: base viewpoint 48 -> conflict-aware viewpoint 7
```

They reduced target/overlap conflict metrics but did not improve coverage and increased actual base-motion footprint
crossing.

## Coverage And Stagnation Analysis

Nearest, greedy, and both conflict-aware ablations were deterministic and identical in coverage:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
```

Late repeated selected assignments were visible in `assignment_history.csv`:

```text
robot_0 -> viewpoint 20
robot_1 -> viewpoint 48
robot_2 -> viewpoint 36
```

These repeated assignments occurred for the final 182 post-gain steps in every episode. Consecutive repeated
assignment count was approximately:

```text
nearest / greedy: 854 per episode
conflict-aware variants: 852 per episode
```

Random behaved differently: it had very low coverage (`0.004` mean final coverage), high actual base-motion crossing
rate, and no stable useful coverage progression. It is a weak lower bound in this scenario.

## Uncovered Viewpoint Analysis

For nearest, greedy, nearest_conflict_aware, and greedy_conflict_aware, the same five viewpoints remained uncovered in
all 10 episodes:

```text
[0, 20, 24, 36, 48]
```

The repeated late assignments targeted three of those uncovered viewpoints:

```text
robot_0 -> 20
robot_1 -> 48
robot_2 -> 36
```

This suggests a dynamic execution/no-progress and baseline strategy limitation, rather than a simple static
availability problem. The current outputs do not include `per_robot_completed_count`; adding that as a future
reporting-only metric would help load-balance analysis.

## Required Analysis Answers

1. Best final coverage: nearest, greedy, and both conflict-aware ablations tie at 0.90.
2. Best coverage AUC: nearest, greedy, and both conflict-aware ablations tie at 0.7468.
3. Highest success rate: all methods are 0.0; no method reached full coverage.
4. Conflict-aware baselines reduce selected-target conflict versus nearest/greedy: yes, 5790 -> 5620 conflict pairs.
5. Conflict-aware baselines reduce inter-robot overlap versus nearest/greedy: yes, 5210 -> 5000 overlap pairs.
6. Conflict-aware baselines increase actual base-motion mesh-footprint crossing: yes, 50 -> 370 crossing steps.
7. Random behaves differently: it has almost no coverage, high selected-intersection and actual base-motion crossing,
   and high overlap. It is not competitive.
8. Baselines get stuck at a late-stage plateau: yes, 45/50 coverage after step 116 with 182 no-progress steps.
9. Most frequent uncovered viewpoints: `[0, 20, 24, 36, 48]` for all non-random methods.
10. Late repeated assignments are visible: yes, `robot_0 -> 20`, `robot_1 -> 48`, `robot_2 -> 36`.
11. The failure appears related to dynamic execution/no-progress and baseline strategy limitations, with selected-target
    conflict, inter-robot overlap, and component crossing as important diagnostics. It is not solved by static feasibility.
12. Conflict-aware baselines look better on selected-target conflict and overlap, but worse on actual base-motion
    component crossing and unchanged on coverage.
13. Phase 8 supports moving toward RL/dynamic policy design rather than adding more handcrafted baseline rules.

## Interpretation Framework

Selected assignment lines are direct robot-base-XY to selected-viewpoint-XY diagnostic segments. They are not planned
robot trajectories.

Selected-target conflict measures proximity between selected target viewpoint XY positions for different robots.

Inter-robot overlap measures proxy robot footprint overlap.

Actual base-motion crossing measures whether the executed proxy base segment from previous XY to current XY intersects
the diagnostic component mesh footprint.

Actual base-motion crossing is an approximate 2D diagnostic, not full 3D collision checking. It does not imply Isaac
physics collision exists or has been solved.

Obstacle diagnostics remain diagnostic-only. `mesh_footprint_aware_cost_matrix` was not promoted into solver inputs.

## Phase 8 Conclusion

The real-component proxy baseline is stable enough for further task-allocation research, but the existing baselines are
not sufficient final policies:

- nearest/greedy reach 45/50 coverage and then stall.
- conflict-aware ablations reduce selected-target and overlap diagnostics but do not improve coverage.
- conflict-aware ablations increase actual proxy base-motion component-crossing risk.
- random is a weak lower bound with poor coverage and high crossing.

This supports proceeding toward RL/dynamic policy work with these diagnostics included, rather than adding more
handcrafted baseline rules.

## What Remains Before RL Evaluation / Retraining

- Keep Phase 8 metrics in the baseline comparison table for future RL work.
- Add reporting-only `per_robot_completed_count` and clearer load-balance summaries if needed.
- Keep actual base-motion crossing as a proxy-execution limitation in all claims.
- Verify RL observation/action compatibility with N=50 and current M=3 before any RL evaluation.
- Do not start retraining until compatibility and baseline reporting are cleanly documented.

## Known Limitations

- N=50 `component_mesh_jittered_n50.csv` is proxy validation data, not final benchmark evidence.
- Actual base-motion crossing is XY-only and approximate.
- No physical collision, local avoidance, path planning, IK, ORCA, retry fallback, cooldown, or hard blocking is present.
- Conflict-aware variants are ablations, not collision-avoidance solvers.
- `per_robot_completed_count` and direct load-balance completion metrics are unavailable in the current outputs.

## Explicitly Not Changed

Phase 8 did not change:

```text
solver behavior
random / nearest / greedy behavior
greedy_conflict_aware / nearest_conflict_aware behavior
available_mask
feasible_mask
static_geometric_feasible_mask
base cost_matrix generation
mesh_footprint_aware_cost_matrix usage
reward
controller
assignment_controller.py
HARL
training
environment dynamics
robot movement behavior
new solvers
new avoidance rules
retry fallback
cooldown behavior
hard obstacle / robot / viewpoint blocking
physical collision
Isaac collision bodies
IK
joint limits
motion planning
ORCA / local avoidance
raycast planner
RL evaluation
RL training
final real CSV validation
```

## Final Checks

Final `git diff --check`:

```text
passed
```

Git emitted LF-to-CRLF working-copy warnings on Windows; no whitespace errors were reported.

Final `git status --short` summary:

```text
 M scripts/environments/evaluate_assignment_methods.py
 M scripts/environments/test_assignment_harl_wrapper_smoke.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py
```
