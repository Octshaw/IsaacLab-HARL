# Phase 7C Inter-Robot Proxy Conflict Diagnostics Report

Date: 2026-06-25

## Why Phase 7C Was Added

Phase 7B obstacle diagnostics clarified that selected assignment lines are direct robot-base-XY to viewpoint-XY
diagnostic segments, not planned robot trajectories. Manual GUI inspection also showed one remaining proxy-environment
credibility issue before Phase 8: proxy/debug robots do not have physical collision and may visually overlap.

Phase 7C adds diagnostic-only inter-robot conflict metrics so Phase 8 baseline validation can report proxy overlap and
selected-target conflicts without changing task allocation behavior.

## Phase 7B-4A Manual GUI Summary

The user completed a 300-step greedy GUI inspection. Green `SelectedAssignment_*` lines were visible and matched selected
assignment semantics. Most green lines did not cross the component mesh footprint. A small number visually crossed the
component footprint, but actual proxy motion could move around the component; the green lines are assignment-level
diagnostic segments, not planned robot trajectories or real collision paths.

This supports keeping mesh-footprint obstacle diagnostics diagnostic-only. Do not promote
`mesh_footprint_aware_cost_matrix` into live solver inputs based on this observation.

## What Was Implemented

- Added scenario-level `inter_robot_conflict_diagnostics` config support.
- Added environment-side current proxy overlap diagnostics from robot base XY positions.
- Added evaluator-side selected target conflict diagnostics after solver assignments are available.
- Added per-episode and summary CSV fields for current robot overlap and selected target conflicts.
- Added compact diagnostics JSON snapshots and smoke-wrapper reset diagnostics support.
- Enabled the diagnostics in `algorithm_proxy_component_mesh.yaml`.

## Configuration Fields

```yaml
inter_robot_conflict_diagnostics:
  enabled: true
  mode: diagnostics_only
  robot_footprint_radius: 0.35
  safety_margin: 0.15
  target_conflict_enabled: true
  target_conflict_radius: 0.35
  target_conflict_safety_margin: 0.15
  debug_visualization:
    enabled: true
    draw_in_headless: false
    max_lines: 10
    line_width: 0.03
```

The `debug_visualization` block is parsed and reported for config compatibility. Phase 7C implemented metrics only; it
did not add new inter-robot USD lines.

## Files Changed

```text
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
```

## Commands Run

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7c_inter_robot_conflict_greedy_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7c_inter_robot_conflict_nearest_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
```

Final commands are recorded after `git diff --check` and `git status --short` are run.

## Headless Smoke Results

Output directories:

```text
results/assignment_evaluation/phase7c_inter_robot_conflict_greedy_headless_smoke
results/assignment_evaluation/phase7c_inter_robot_conflict_nearest_headless_smoke
```

Both directories contain:

```text
diagnostics.json
summary.csv
per_episode.csv
assignment_history.csv
```

Both smoke runs passed and generated the new inter-robot fields in `diagnostics.json`, `summary.csv`, and
`per_episode.csv`.

## Key Metrics

Greedy, 1 episode, 50 steps:

```text
inter_robot_overlap_step_count_total = 0
inter_robot_overlap_rate_mean = 0.0
inter_robot_overlap_pair_count_total = 0
inter_robot_min_distance_min = 2.9434361457824707
inter_robot_min_clearance_min = 2.0934362411499023
selected_target_conflict_step_count_total = 0
selected_target_conflict_rate_mean = 0.0
selected_target_conflict_pair_count_total = 0
selected_target_min_distance_min = 3.3774425983428955
selected_target_min_clearance_min = 2.527442455291748
selected_target_skipped_robot_count_total = 0
selected_target_valid_robot_count_mean = 3.0
assignment_history_rows = 150
```

Nearest, 1 episode, 50 steps:

```text
inter_robot_overlap_step_count_total = 0
inter_robot_overlap_rate_mean = 0.0
inter_robot_overlap_pair_count_total = 0
inter_robot_min_distance_min = 2.9434361457824707
inter_robot_min_clearance_min = 2.0934362411499023
selected_target_conflict_step_count_total = 0
selected_target_conflict_rate_mean = 0.0
selected_target_conflict_pair_count_total = 0
selected_target_min_distance_min = 3.3774425983428955
selected_target_min_clearance_min = 2.527442455291748
selected_target_skipped_robot_count_total = 0
selected_target_valid_robot_count_mean = 3.0
assignment_history_rows = 150
```

Latest diagnostics snapshots were also present in `diagnostics.json` for both methods.

## GUI Visualization

No new inter-robot GUI visualization was implemented in Phase 7C. Metrics were prioritized to avoid unnecessary USD
authoring changes. Existing selected-assignment green lines from Phase 7B-4A remain available.

## Solver Behavior

Solver behavior did not change.

The patch does not modify:

```text
solver behavior
assignment semantics
available_mask
feasible_mask
static_geometric_feasible_mask
cost_matrix
reward
controller
assignment_controller.py
HARL
training
environment dynamics
robot movement behavior
```

No hard inter-robot blocking, viewpoint blocking, local avoidance, collision bodies, motion planning, IK, joint limits,
cooldowns, or retry fallback behavior were added.

## Known Limitations

- Inter-robot conflict diagnostics are proxy-level checks only.
- They are not Isaac physics collision simulation.
- They do not imply real robot collision avoidance.
- Selected target conflicts measure selected viewpoint XY proximity, not path conflicts.
- The short smoke runs found no overlap or target conflict; Phase 8 should keep these as reported diagnostics.
- GUI inter-robot conflict visualization remains unimplemented.

## Final Checks

```text
git diff --check: passed
```

Git emitted LF-to-CRLF warnings for edited text files; no whitespace errors were reported.

`git status --short`:

```text
 M scripts/environments/evaluate_assignment_methods.py
 M scripts/environments/test_assignment_harl_wrapper_smoke.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/
```
