# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-1 Mesh-Footprint Obstacle Diagnostics MVP is complete.

The hybrid algorithm scenario now computes diagnostic-only obstacle fields from the measured component OBJ footprint:

```text
configs/scenarios/algorithm_proxy_component_mesh.yaml
```

The bbox proxy remains metadata/debug visualization only. It is not used as a hard blocker.

This phase did not change `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver
behavior, reward, controller math, HARL core, training behavior, real robot articulation, IK, collision, joint limits,
raycast coverage, or final real CSV validation.

## Latest Completed Phase

Phase 7B-1: Mesh-Footprint Obstacle Diagnostics MVP.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_obstacle_footprint.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B1_MESH_FOOTPRINT_DIAGNOSTICS_20260623.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Obstacle Diagnostic Config

`algorithm_proxy_component_mesh.yaml` now has:

```yaml
obstacle_diagnostics:
  enabled: true
  mode: diagnostics_only
  obstacle_source: component_mesh_footprint
  footprint_resolution: 0.10
  footprint_inflation_radius: 0.30
  line_sample_step: 0.10
  blocked_path_penalty: 100.0
```

`algorithm_proxy_bbox.yaml` and `real_scene_proxy_headless.yaml` keep obstacle diagnostics disabled by default.

## New Diagnostic Fields

When enabled, `get_assignment_problem()` adds:

```text
straight_line_cost_matrix
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
obstacle_diagnostics_enabled
obstacle_diagnostics_mode
obstacle_source
component_obstacle_footprint_diagnostics
```

These are diagnostic-only fields. Baseline `random`, `nearest`, and `greedy` still consume the existing
`available_mask`, `cost_matrix`, and `noop_id`.

## Latest Verification

Phase 7A-3 preflight checks passed before implementation:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scenario_config.py scan_mobile_manipulator_env.py test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py ... --scenario_config configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/algorithm_proxy_component_mesh_phase7a3_prerun_smoke.json
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py ... --scenario_config configs/scenarios/algorithm_proxy_component_mesh.yaml --output_name algorithm_proxy_component_mesh_phase7a3_prerun_eval_smoke --no-write_assignment_history
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py ... --scenario_config configs/scenarios/algorithm_proxy_bbox.yaml --result_file results/assignment_diagnostics/algorithm_proxy_bbox_phase7a3_prerun_regression_smoke.json
```

Syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile component_obstacle_footprint.py scan_mobile_manipulator_env.py scenario_config.py test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
```

Hybrid obstacle wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/mesh_footprint_obstacle_phase7b1_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
straight_line_cost_matrix=[1, 3, 50]
mesh_footprint_intersection_mask=[1, 3, 50]
mesh_footprint_penalty_matrix=[1, 3, 50]
mesh_footprint_aware_cost_matrix=[1, 3, 50]
mesh_footprint_intersection_count=54
footprint_grid_shape=[25, 45]
occupied_cell_count=598
inflated_occupied_cell_count=963
```

Hybrid evaluator smoke passed:

```text
output_dir=results/assignment_evaluation/mesh_footprint_obstacle_phase7b1_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
random/nearest/greedy completed
same obstacle diagnostic shapes and counts as wrapper smoke
```

Bbox scenario regression smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7b1_regression_smoke.json
obstacle_diagnostics_enabled=false
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

Visual scenario regression smoke passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7b1_regression_smoke.json
obstacle_diagnostics_enabled=false
robot_visual_mesh_enabled=true
component_mesh_enabled=true
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

## Known Issues / Limitations

- The footprint is an approximate XY projection of the measured component OBJ.
- The path diagnostic samples direct robot-base-XY to viewpoint-XY segments only.
- This is not a planner, raycast, 3D collision test, or PhysX collision body.
- `blocked_path_penalty` affects only `mesh_footprint_aware_cost_matrix`; it does not replace `cost_matrix`.
- Synthetic N=50 viewpoints remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not use component bbox as hard obstacle blocking.
- Do not mark viewpoints unavailable because they are inside the overall component bbox.
- Do not replace `cost_matrix`, `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver behavior, reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add inter-robot conflict avoidance or dynamic reassignment yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Phase 7B-2: compare diagnostic obstacle-aware cost candidates against baseline assignment outputs.
```

Keep the comparison diagnostic-only until the cost design is reviewed. Do not promote `mesh_footprint_aware_cost_matrix`
into solver inputs without a separate gated phase.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B1_MESH_FOOTPRINT_DIAGNOSTICS_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
