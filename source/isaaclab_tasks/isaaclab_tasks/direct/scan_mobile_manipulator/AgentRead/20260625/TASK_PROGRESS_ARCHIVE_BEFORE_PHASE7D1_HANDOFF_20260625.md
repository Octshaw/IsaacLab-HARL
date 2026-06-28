# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7C diagnostic-only inter-robot proxy conflict metrics are implemented and headless-smoke validated. Phase 7B-4A
manual GUI validation was also recorded: the user completed a 300-step greedy GUI inspection, and green
`SelectedAssignment_*` lines matched selected-assignment semantics. These green lines are direct robot-base-XY to
selected-viewpoint-XY diagnostic segments, not planned robot trajectories.

The active `algorithm_proxy_component_mesh.yaml` GUI inspection scenario uses:

```text
obstacle_debug_visualization.line_source: selected_assignments
inter_robot_conflict_diagnostics.enabled: true
inter_robot_conflict_diagnostics.mode: diagnostics_only
```

This draws/stores actual solver-selected robot-viewpoint pairs rather than blocked candidate pairs. The previous
blocked-candidate visualization remains available by setting:

```text
obstacle_debug_visualization.line_source: mesh_footprint_intersections
```

Current milestone:

```text
mesh-footprint obstacle diagnostics
obstacle-aware candidate comparison
blocked candidate debug line visualization
selected assignment debug line visualization
inter-robot proxy conflict diagnostics
BasisCurves visibility fix
GUI-safe timed inspection pause
longer diagnostic-only candidate comparison summaries
OBJ mesh-sampled jittered viewpoint CSV generation
side-balanced OBJ-derived proxy-surface viewpoint placement
configurable GUI debug camera pose
visual-only USD ground grid for GUI inspection
```

## Latest Completed Work

Phase 7C added proxy-level inter-robot conflict diagnostics without changing solver behavior, masks, costs, rewards,
controller logic, HARL, training, environment dynamics, or robot movement. It reports current robot overlap metrics and
selected-target conflict metrics in `diagnostics.json`, `summary.csv`, and `per_episode.csv`.

Phase 7C validation:

```text
py_compile passed:
- scripts/environments/evaluate_assignment_methods.py
- scripts/environments/test_assignment_harl_wrapper_smoke.py
- source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
- source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py

greedy 50-step headless smoke passed:
results/assignment_evaluation/phase7c_inter_robot_conflict_greedy_headless_smoke/
inter_robot_overlap_rate_mean = 0.0
selected_target_conflict_rate_mean = 0.0
inter_robot_min_clearance_min = 2.0934362411499023
selected_target_min_clearance_min = 2.527442455291748

nearest 50-step headless smoke passed:
results/assignment_evaluation/phase7c_inter_robot_conflict_nearest_headless_smoke/
inter_robot_overlap_rate_mean = 0.0
selected_target_conflict_rate_mean = 0.0
inter_robot_min_clearance_min = 2.0934362411499023
selected_target_min_clearance_min = 2.527442455291748
```

GUI inter-robot conflict visualization was skipped; metrics were implemented instead. Existing Phase 7B-4A selected
assignment line visualization remains available.

Detailed Phase 7C report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
```

Phase 7B-4A added `selected_assignments` as a diagnostic-only `obstacle_debug_visualization.line_source`.

Implementation summary:

```text
- scenario_config.py accepts selected_assignments as a valid obstacle debug line source.
- scan_mobile_manipulator_env.py stores latest solver-selected assignment pairs through
  set_obstacle_debug_selected_assignments(...).
- selected assignment lines use green SelectedAssignment_* USD BasisCurves.
- mesh_footprint_intersections still uses the existing red BlockedPath_* USD BasisCurves.
- evaluate_assignment_methods.py calls the new debug hook after solver.solve(...) and before action conversion.
- diagnostics.json now includes selected_assignment_debug_visualization_latest and compact selected-pair fields.
- test_assignment_harl_wrapper_smoke.py preserves those fields in obstacle diagnostics summaries.
```

Changed files:

```text
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Validation summary:

```text
py_compile passed for evaluate_assignment_methods.py, scan_mobile_manipulator_env.py, scenario_config.py, and
test_assignment_harl_wrapper_smoke.py.

Headless greedy smoke passed:
results/assignment_evaluation/phase7b4a_selected_lines_greedy_headless_smoke/
selected pairs [(0, 5), (1, 42), (2, 8)] matched assignment_history last-step pairs.

Headless nearest smoke passed:
results/assignment_evaluation/phase7b4a_selected_lines_nearest_headless_smoke/
selected pairs [(0, 5), (1, 42), (2, 8)] matched assignment_history last-step pairs.
```

Manual GUI inspection was later completed by the user with a 300-step greedy GUI run. Green `SelectedAssignment_*`
lines were visible and matched selected-assignment semantics. Most did not cross the component footprint; a few direct
diagnostic segments did, but playback showed proxy robot motion may move around the component rather than following the
straight green segment. Interpret green lines as assignment-level base-XY to viewpoint-XY diagnostics, not planned robot
trajectories or real collision paths.

Local supporting output exists at `results/assignment_evaluation/gui_nearest_n50_e1_s300/` (directory name says nearest,
files record `method=greedy`): 1 episode, episode_length=299, final_coverage=0.88, 44/50 covered, assignment_history
rows=897, selected_intersection_count=5, selected_intersection_rate=0.005574136008918618, and
candidate_changed_assignment_rate=0.0.

No solver behavior changed. The patch does not modify:

```text
available_mask, feasible_mask, static_geometric_feasible_mask, cost_matrix, reward, controller,
assignment_controller.py, HARL, training, or environment dynamics.
```

## Active Architecture / Implementation Path

Obstacle diagnostics are still diagnostic-only:

```text
component OBJ -> approximate XY mesh footprint -> diagnostic line-intersection tensors
```

Important active fields:

```text
straight_line_cost_matrix
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
```

`mesh_footprint_aware_cost_matrix` is not promoted into live solver inputs.

The Phase 7B-3 evaluator comparison still uses:

```text
baseline: normal assignment problem with cost_matrix
candidate: copied assignment problem with cost_matrix replaced by mesh_footprint_aware_cost_matrix
```

The component bbox remains metadata/debug only and is not used as hard obstacle blocking.

Red obstacle debug lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned robot paths. Robot
motion may differ from red lines; this is expected.

The mesh-sampled viewpoint generator is an offline CSV-generation utility. It does not change solver inputs, masks,
reward, controller behavior, HARL, or training.

## Latest Verification

Latest verification:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 5 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b4a_selected_lines_greedy_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
conda run -p C:\isaacenvs\isaac45_harl python -c "<compare greedy diagnostics selected pairs against assignment_history last-step rows>"
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 5 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b4a_selected_lines_nearest_headless_smoke --write_assignment_history --compare_obstacle_aware_candidates
conda run -p C:\isaacenvs\isaac45_harl python -c "<compare nearest diagnostics selected pairs against assignment_history last-step rows>"
```

Results passed. Both greedy and nearest produced `selected_assignment_debug_visualization_line_count=3`,
`selected_assignment_debug_visualization_intersection_count=0`, and selected pairs
`[(robot_0, 5), (robot_1, 42), (robot_2, 8)]`, matching `assignment_history.csv` last-step rows exactly.

Final `git diff --check` passed. Git status shows the expected modified code/docs plus the new Phase 7B-4A report; the
pre-existing untracked `AgentRead/20260624/` folder is still present.

GUI/manual viewport inspection for Phase 7B-4A is complete.

## Known Issues / Limitations

- Synthetic N=50 viewpoints remain smoke/interface data only, not final benchmark evidence.
- Current synthetic N=50 scenario does not strongly stress nearest/greedy obstacle effects.
- `component_mesh_jittered_n50.csv` is a diagnostic OBJ-derived candidate set, not a final planned benchmark CSV.
- The default jittered generator config filters z to a mobile-scan-friendly band; remove/adjust `min_z` and `max_z`
  for full-surface sampling.
- Obstacle-aware candidate assignments did not differ from baseline nearest/greedy in Phase 7B-3.
- Mesh footprint is approximate XY diagnostic geometry, not 3D collision.
- Selected assignment debug lines are direct diagnostic segments, not planned robot paths.
- Selected assignment visualization depends on a caller providing the assignment tensor through
  `set_obstacle_debug_selected_assignments(...)`; the baseline evaluator now does this.
- Inter-robot overlap remains a proxy-level validation diagnostic only. Phase 7C measures it, but does not add physical
  collision, hard blocking, local avoidance, or path planning.
- Current hybrid scenario keeps obstacle debug visualization enabled for manual GUI inspection; set it false for
  smoke-only runs if desired.

## Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into solver inputs yet.
- Do not replace `cost_matrix`.
- Do not change `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver default behavior, reward, controller, `assignment_controller.py`, HARL, or training.
- Do not add RL evaluation.
- Do not add bbox hard blocking or mesh-footprint hard blocking.
- Do not add inter-robot conflict avoidance or dynamic reassignment yet.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSVs as final benchmark evidence.

## Next Step

Recommended next task:

```text
Proceed to Phase 8 real-component proxy-robot baseline validation using the existing obstacle and inter-robot metrics
as diagnostics only.
```

No additional Phase 7B-4A GUI validation is required before Phase 8; the user already completed the 300-step greedy GUI
inspection recorded in the 7B-4A report.

Do not commit `results/` unless explicitly requested.

Interpretation:

```text
Obstacle diagnostics are sufficiently clarified for current task-allocation experiments. Inter-robot conflict
diagnostics are now proxy-level checks for baseline validation. Further obstacle or inter-robot behavior work should
only happen if later Phase 8 validation shows a clear need. Do not add physical collision, hard blocking, local
avoidance, or path planning unless a later task explicitly changes scope.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B3_LONG_DIAGNOSTIC_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B_OBSTACLE_DIAGNOSTICS_CHECKPOINT_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_PHASE_7B3_LONG_DIAGNOSTIC_COMPARISON_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/NEXT_PHASE_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B_CHECKPOINT_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
```
