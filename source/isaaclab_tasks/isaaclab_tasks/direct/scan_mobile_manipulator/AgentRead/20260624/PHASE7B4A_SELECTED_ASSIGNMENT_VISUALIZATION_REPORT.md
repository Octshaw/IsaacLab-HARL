# Phase 7B-4A Selected Assignment Visualization Report

Date: 2026-06-24

## Scope

Phase 7B-4A adds a diagnostic-only line visualization mode for actual solver-selected assignment pairs:

```text
obstacle_debug_visualization_line_source = selected_assignments
```

This mode draws/stores only current solver-selected robot-viewpoint pairs:

```text
robot base XY -> selected viewpoint XY
```

The previous blocked-candidate mode remains available:

```text
obstacle_debug_visualization_line_source = mesh_footprint_intersections
```

## Why It Was Needed

The old GUI red lines came from `mesh_footprint_intersection_mask`, which visualizes blocked candidate pairs. Those
pairs are useful obstacle diagnostics, but they are not necessarily the pairs selected by nearest or greedy. The new
mode avoids visually confusing blocked candidates with actual solver output.

## Files Changed

```text
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
```

## What Changed

- Added `selected_assignments` as a supported `obstacle_debug_visualization.line_source`.
- Added an environment debug hook, `set_obstacle_debug_selected_assignments(...)`, that stores selected assignment
  pairs from the solver's current assignment/problem snapshot.
- Extended obstacle debug line drawing so `selected_assignments` draws only stored selected pairs.
- Kept `mesh_footprint_intersections` unchanged for blocked candidate-pair visualization.
- Added green `SelectedAssignment_*` USD curve prims for selected assignment lines; blocked candidate lines remain red
  `BlockedPath_*` curves.
- Added compact diagnostics:

```text
selected_assignment_debug_visualization_enabled
selected_assignment_debug_visualization_line_count
selected_assignment_debug_visualization_pairs_sample
selected_assignment_debug_visualization_intersection_count
selected_assignment_debug_visualization_skipped_reason
selected_assignment_debug_visualization_latest
```

- Updated `algorithm_proxy_component_mesh.yaml` to use `line_source: selected_assignments` for current GUI inspection.

## Commands Run

Interpreter check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Headless greedy smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 5 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b4a_selected_lines_greedy_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
```

Headless nearest smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 5 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b4a_selected_lines_nearest_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
```

Selected-pair checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "<read diagnostics.json and assignment_history.csv; compare selected pairs>"
```

## Validation Results

Syntax checks passed.

Headless greedy smoke passed:

```text
line_source = selected_assignments
selected_assignment_debug_visualization_line_count = 3
selected_assignment_debug_visualization_intersection_count = 0
selected pairs = [(robot_0, viewpoint 5), (robot_1, viewpoint 42), (robot_2, viewpoint 8)]
assignment_history last-step pairs = [(robot_0, viewpoint 5), (robot_1, viewpoint 42), (robot_2, viewpoint 8)]
pairs_match_history = True
```

Headless nearest smoke passed with the same selected pair sample and `pairs_match_history = True`.

Because the smokes were headless and `draw_in_headless: false`, USD `drawn_line_count` remains 0 in those runs. The
selected-pair diagnostics still confirm the correct solver-selected pairs are available for GUI drawing.

## GUI Inspection

Manual GUI inspection was completed by the user with a 300-step greedy GUI run.

The green `SelectedAssignment_*` lines were visible and matched the expected selected-assignment visualization
semantics.

Most green selected-assignment diagnostic lines did not cross the component mesh footprint.

A small number of green selected-assignment lines visually crossed the component footprint, but the actual proxy robot
motion did not necessarily follow the green straight line. In playback, the robot could move around the component and
the actual visible motion could avoid the component.

Therefore, green `SelectedAssignment_*` lines should be interpreted as direct assignment-level diagnostic segments from
robot base XY to selected viewpoint XY. They are not planned robot trajectories and should not be interpreted as real
collision paths.

This supports keeping mesh-footprint obstacle diagnostics diagnostic-only. Do not promote
`mesh_footprint_aware_cost_matrix` into the live solver path based on this observation.

Local supporting output was found at:

```text
results/assignment_evaluation/gui_nearest_n50_e1_s300/
```

Although the directory name contains `nearest`, the files record `method=greedy`. Compact local numbers:

```text
episodes = 1
episode_length = 299
assignment_history_rows = 897
mean_final_coverage = 0.88
final_covered_count = 44 / 50
final_uncovered_viewpoint_ids = [0, 4, 20, 24, 36, 48]
mean_coverage_auc = 0.7301014065742493
latest selected line count = 3
latest selected intersection count = 0
obstacle comparison selected_pair_count = 897
obstacle comparison selected_intersection_count = 5
obstacle comparison selected_intersection_rate = 0.005574136008918618
candidate_changed_assignment_rate = 0.0
```

## Interpretation

Phase 7B obstacle diagnostics are sufficiently clarified for current task-allocation experiments. Further obstacle work
should only happen if later baseline validation shows a clear need.

Before Phase 8 baseline validation, one remaining proxy-environment issue should be addressed: inter-robot overlap.
Robots are currently proxy/debug agents without physical collision, so they may overlap in the GUI. This should be
measured with diagnostic-only inter-robot proxy conflict metrics before Phase 8.

## Solver Behavior

Solver behavior did not change.

The patch does not modify:

```text
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
```

`mesh_footprint_aware_cost_matrix` remains diagnostic-only and is not promoted into solver inputs.

## Known Limitations

- Selected assignment visualization is fed by callers that know the assignment tensor. The baseline evaluator now calls
  the hook. Other callers can use the same environment hook when they compute discrete assignments.
- Manual viewport confirmation is complete for the user-run 300-step greedy GUI inspection recorded above.
- Selected lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned robot paths.
- Mesh-footprint intersection labels remain approximate XY diagnostics, not 3D collision checks.

## Final Checks

`git diff --check`:

```text
passed
```

Git emitted LF-to-CRLF warnings for edited text files; no whitespace errors were reported.

`git status` summary:

```text
modified: scripts/environments/evaluate_assignment_methods.py
modified: scripts/environments/test_assignment_harl_wrapper_smoke.py
modified: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
modified: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
modified: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
modified: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
untracked: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/
```
