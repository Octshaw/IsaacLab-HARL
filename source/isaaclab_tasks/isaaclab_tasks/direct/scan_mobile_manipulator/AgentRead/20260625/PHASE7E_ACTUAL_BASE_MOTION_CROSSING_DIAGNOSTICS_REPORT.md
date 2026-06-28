# Phase 7E Actual Proxy Base Motion Crossing Diagnostics Report

## Purpose

Phase 7E was added after GUI playback suggested a visible task-space proxy robot could move through the component mesh.
This is different from the Phase 7B-4A selected-assignment line diagnostic:

```text
selected assignment line:
  current robot base XY -> selected viewpoint XY

actual proxy base motion:
  previous robot base XY -> current robot base XY
```

This phase implements diagnostic-only actual proxy base motion crossing checks. It does not implement obstacle
avoidance, path planning, collision, masking, reward changes, controller changes, or solver behavior changes.

## What Was Implemented

For each evaluator step, env, and robot, the evaluator now snapshots:

```text
previous_base_xy before env.step(...)
current_base_xy after env.step(...)
```

It then checks the executed proxy base segment against the existing diagnostic component mesh footprint. Terminal
auto-reset frames are skipped to avoid measuring reset displacement as robot motion.

The metric uses the existing `ComponentObstacleFootprint.intersects_segment(...)` helper. The component bbox remains
metadata/debug only and is not used as a hard obstacle.

## Configuration

Added to:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

```yaml
actual_base_motion_obstacle_diagnostics:
  enabled: true
  mode: diagnostics_only
  obstacle_source: component_mesh_footprint
  line_sample_step: 0.10
  min_motion_distance: 1.0e-6
  max_pairs_sample: 20
  debug_visualization:
    enabled: false
    draw_in_headless: false
    max_lines: 20
    line_width: 0.03
```

The debug visualization sub-block is parsed and carried as configuration metadata only in this phase.

## Files Changed

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
```

Archive created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7E_ACTUAL_BASE_MOTION_20260628.md
```

## Output Fields

Added to `diagnostics.json`:

```text
actual_base_motion_obstacle_diagnostics
actual_base_motion_obstacle_diagnostics_enabled
actual_base_motion_obstacle_diagnostics_mode
actual_base_motion_obstacle_source
actual_base_motion_intersection_pair_count
actual_base_motion_intersection_any
actual_base_motion_intersection_pairs_sample
actual_base_motion_min_distance_to_footprint
actual_base_motion_skipped_robot_count
actual_base_motion_valid_robot_count
actual_base_motion_intersection_count_by_robot
actual_base_motion_intersection_rate_by_robot
```

Added to `summary.csv` and `per_episode.csv`:

```text
actual_base_motion_intersection_step_count
actual_base_motion_intersection_rate
actual_base_motion_intersection_pair_count_total
actual_base_motion_intersection_pair_count_mean
actual_base_motion_min_distance_to_footprint_min
actual_base_motion_min_distance_to_footprint_mean
actual_base_motion_valid_robot_count_mean
actual_base_motion_skipped_robot_count_total
```

Added compactly to `assignment_history.csv`:

```text
actual_base_motion_intersects_component
actual_base_motion_distance
```

## Commands Run

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Short smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy greedy_conflict_aware --num_envs 1 --num_episodes 1 --max_steps 80 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7e_actual_base_motion_crossing_smoke_e1_s80 --write_assignment_history --compare_obstacle_aware_candidates
```

Main diagnostic run:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy greedy_conflict_aware nearest nearest_conflict_aware --num_envs 1 --num_episodes 1 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7e_actual_base_motion_crossing_e1_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

Output directories:

```text
results/assignment_evaluation/phase7e_actual_base_motion_crossing_smoke_e1_s80/
results/assignment_evaluation/phase7e_actual_base_motion_crossing_e1_s300/
```

## Key Metrics

300-step run, `num_envs=1`, `num_episodes=1`, N=50, M=3:

```text
greedy:
  actual_base_motion_intersection_step_count_total = 5
  actual_base_motion_intersection_rate_mean = 0.0167224080
  actual_base_motion_intersection_pair_count_total = 5
  actual_base_motion_min_distance_to_footprint_min = 0.0
  crossing robots = robot_0: 5, robot_1: 0, robot_2: 0
  crossing steps = 124-128

nearest:
  actual_base_motion_intersection_step_count_total = 5
  actual_base_motion_intersection_rate_mean = 0.0167224080
  actual_base_motion_intersection_pair_count_total = 5
  actual_base_motion_min_distance_to_footprint_min = 0.0
  crossing robots = robot_0: 5, robot_1: 0, robot_2: 0
  crossing steps = 124-128

greedy_conflict_aware:
  actual_base_motion_intersection_step_count_total = 37
  actual_base_motion_intersection_rate_mean = 0.1237458194
  actual_base_motion_intersection_pair_count_total = 37
  actual_base_motion_min_distance_to_footprint_min = 0.0
  crossing robots = robot_0: 5, robot_1: 32, robot_2: 0
  crossing steps = 90-112, 114-122, 124-128

nearest_conflict_aware:
  actual_base_motion_intersection_step_count_total = 37
  actual_base_motion_intersection_rate_mean = 0.1237458194
  actual_base_motion_intersection_pair_count_total = 37
  actual_base_motion_min_distance_to_footprint_min = 0.0
  crossing robots = robot_0: 5, robot_1: 32, robot_2: 0
  crossing steps = 90-112, 114-122, 124-128
```

The 80-step smoke detected no actual base-motion crossings for either `greedy` or `greedy_conflict_aware`.

## Samples

Baseline crossing sample:

```text
greedy, step 124, robot_0:
  prev_base_xy = [1.8189548254, -1.1744426489]
  current_base_xy = [1.8989548683, -1.0944426060]
  selected_viewpoint_id = 20
  motion_distance = 0.1131371457
```

Conflict-aware crossing sample:

```text
greedy_conflict_aware, step 90, robot_1:
  prev_base_xy = [1.3326447010, 1.2483578920]
  current_base_xy = [1.3326447010, 1.1483578682]
  selected_viewpoint_id = 7
  motion_distance = 0.1000000238
```

## Analysis Answers

1. Actual proxy base motion did cross the component mesh footprint in the 300-step diagnostic run.
2. All tested methods had some crossing. `greedy` and `nearest` had 5 crossing steps each; conflict-aware variants had 37 each.
3. `greedy_conflict_aware` did not merely reveal the same issue. It retained the 5 `robot_0` crossings also present in `greedy` and added 32 `robot_1` crossings in this scenario.
4. `robot_1` crossed most often under conflict-aware variants. `robot_0` crossed under all methods. `robot_2` did not cross in this run.
5. Crossings occurred in mid-episode ranges, mainly steps 90-128. They were not limited to late-stage repeated clustered targets.
6. The crossings did not occur only near the final repeated cluster; the main conflict-aware crossing block was around selected viewpoint 7, then later 20/48.
7. Actual base-motion crossing is correlated with selected assignment line intersections but is not identical. In the 300-step run, selected assignment line intersections were 7 for baseline methods and 45 for conflict-aware variants, while actual base-motion crossings were 5 and 37 respectively.
8. Actual base-motion crossing is also related to selected-target conflict/inter-robot overlap in this scenario, but not equivalent. Conflict-aware variants reduced selected-target conflict and overlap counts versus baseline while increasing actual base-motion crossing count.
9. This should not automatically block Phase 8, but it must be reported as a proxy execution limitation. If Phase 8 uses these proxy baselines, include this metric and avoid claiming obstacle avoidance.

## Diagnostic Scope

These checks are 2D mesh-footprint approximations. They are not full 3D collision checks and do not represent Isaac
physics collision. A crossing means:

```text
the sampled previous-base-XY -> current-base-XY proxy segment intersects the inflated diagnostic component footprint
```

It does not mean physical collision bodies exist, nor that path planning has been implemented.

## Explicitly Not Changed

The following were not changed:

```text
solver behavior
random / nearest / greedy behavior
greedy_conflict_aware / nearest_conflict_aware behavior
available_mask
feasible_mask
static_geometric_feasible_mask
cost_matrix
mesh_footprint_aware_cost_matrix usage
reward
controller
assignment_controller.py
HARL
training
environment dynamics
robot movement behavior
physical collision
hard obstacle blocking
path planning
IK / joint limits / raycast coverage
final real CSV validation
```

## Known Limitations

- The metric is approximate and XY-only.
- It uses sampled straight segments between previous and current proxy base positions, not true swept robot geometry.
- It skips terminal auto-reset frames to avoid false reset-motion crossings.
- Debug visualization for actual base-motion crossing lines was not added in Phase 7E.
- Conflict-aware variants are still baseline ablations, not collision avoidance or path planning methods.

## Recommendation for Phase 8

Phase 8 can proceed if this metric is carried forward and clearly reported. The 300-step result shows conflict-aware
baseline variants reduce selected-target conflict modestly but can increase actual proxy base-motion footprint crossings.
Do not claim obstacle avoidance. Consider a later gated experiment for path-crossing penalties or observations, but do
not add physical collision, local avoidance, or RL changes as part of this diagnostic handoff.

## Final Checks

Final verification was rerun after the report and `TASK_PROGRESS.md` update:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py scripts/environments/test_assignment_harl_wrapper_smoke.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
git diff --check
git status --short
```

`py_compile` passed. `git diff --check` passed with line-ending warnings only.
