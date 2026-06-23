# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2.5 obstacle diagnostic GUI validation and GUI-safe pause are complete.

The user manually confirmed that the red debug lines are visible and reasonable. The project is ready for Phase 7B-3:
longer diagnostic-only obstacle-aware candidate comparisons.

Current milestone:

```text
mesh-footprint obstacle diagnostics
obstacle-aware candidate comparison
GUI red-line debug visualization
BasisCurves visibility fix
GUI-safe timed inspection pause
```

## Latest Completed Work

Created a clean checkpoint summary and next-stage plan for continuing in a new conversation/window.

Added:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B_OBSTACLE_DIAGNOSTICS_CHECKPOINT_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_PHASE_7B3_LONG_DIAGNOSTIC_COMPARISON_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B_CHECKPOINT_20260623.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No Python code was changed by this checkpoint task.

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

The component bbox remains metadata/debug only and is not used as hard obstacle blocking.

Red obstacle debug lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned robot paths. Robot
motion may differ from red lines; this is expected.

## Latest Verification

Checkpoint verification:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
git diff --check
git status
```

Results should be checked at the end of this checkpoint task. No syntax checks are required for this documentation-only
checkpoint unless Python files are modified.

Most recent Phase 7B smoke state before this checkpoint:

```text
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
mesh_footprint_intersection_count=54
obstacle debug lines visible and reasonable in manual GUI
GUI-safe pause uses simulation_app.update()
```

## Known Issues / Limitations

- Phase 7B-3 has not yet run longer diagnostic comparisons.
- Current short candidate-comparison smoke is not benchmark evidence.
- Synthetic N=50 viewpoints remain smoke/interface data only.
- Mesh footprint is approximate XY diagnostic geometry, not 3D collision.
- Red debug lines are direct diagnostic segments, not planned robot paths.
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
Phase 7B-3: Longer Diagnostic-Only Obstacle-Aware Candidate Comparisons
```

Start with:

```text
scenario = algorithm_proxy_component_mesh.yaml
methods = random nearest greedy
num_envs = 1
num_episodes = 3
max_steps = 50
compare_obstacle_aware_candidates = true
```

Then review whether baseline selected-intersection rates and candidate selected-intersection rates justify a later
gated solver-cost experiment.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B_OBSTACLE_DIAGNOSTICS_CHECKPOINT_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_PHASE_7B3_LONG_DIAGNOSTIC_COMPARISON_PLAN.md
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
