# Mesh-Footprint Obstacle Diagnostics MVP Report

Date: 2026-06-23

## Purpose

Phase 7B-1 adds diagnostic-only obstacle fields derived from the measured component OBJ footprint.

The intent is to inspect whether simple robot-base-XY to viewpoint-XY path segments cross the inflated measured
component footprint, without changing assignment behavior.

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_obstacle_footprint.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B1_MESH_FOOTPRINT_DIAGNOSTICS_20260623.md
```

## Files Modified

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Why Bbox Hard Blocking Was Avoided

The measured component is irregular. The overall component bbox is a coarse metadata/debug proxy, and some legal
viewpoints may fall inside that overall bbox while still being useful around the real component shape.

This phase does not use the component bbox as an obstacle. It does not mark viewpoints unavailable because they are
inside the bbox, and it does not block line segments using bbox intersection.

## Mesh Footprint Method

The helper in `component_obstacle_footprint.py`:

1. Loads the component OBJ with the existing lightweight OBJ loader.
2. Applies the configured mesh scale, position, and `qwxyz` orientation.
3. Projects transformed mesh triangles into XY.
4. Rasterizes projected triangles and triangle edges into a 2D grid.
5. Inflates occupied cells by `footprint_inflation_radius`.
6. Checks candidate XY line segments by sampling points every `line_sample_step`.

The footprint is a diagnostic-only proxy. It does not create PhysX collision, mesh collision bodies, raycasts, or
planner geometry.

## Path Segment Definition

For this MVP:

```text
segment start = robot base XY
segment end = viewpoint XY
```

This is not a full navigation planner. It is only a direct-path diagnostic for future obstacle-aware cost work.

## New Config Fields

Enabled in `algorithm_proxy_component_mesh.yaml`:

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

## New Assignment Problem Fields

When obstacle diagnostics are enabled, `get_assignment_problem()` now includes:

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

The existing fields are preserved:

```text
cost_matrix
available_mask
feasible_mask
static_geometric_feasible_mask
task_status
robot_status
noop_id
```

The diagnostic cost is separate:

```text
mesh_footprint_aware_cost_matrix = straight_line_cost_matrix + mesh_footprint_penalty_matrix
```

It is not fed back into `cost_matrix`.

## Diagnostics Added

Wrapper and evaluator JSON summaries now include compact obstacle diagnostics:

```text
obstacle_diagnostics_enabled
obstacle_source
obstacle_diagnostics_mode
footprint_resolution
footprint_inflation_radius
line_sample_step
footprint_bounds_xy
footprint_grid_shape
occupied_cell_count
inflated_occupied_cell_count
straight_line_cost_matrix_shape
mesh_footprint_intersection_shape
mesh_footprint_intersection_count
mesh_footprint_penalty_matrix_shape
mesh_footprint_aware_cost_shape
blocked_pairs_sample
```

Full occupancy grids are not dumped to JSON.

## Smoke Results

Hybrid obstacle wrapper smoke:

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

Hybrid evaluator smoke:

```text
output_dir=results/assignment_evaluation/mesh_footprint_obstacle_phase7b1_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
random/nearest/greedy completed
same obstacle diagnostic shapes and counts as wrapper smoke
```

Bbox scenario regression:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7b1_regression_smoke.json
obstacle_diagnostics_enabled=false
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

Visual scenario regression:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7b1_regression_smoke.json
obstacle_diagnostics_enabled=false
robot_visual_mesh_enabled=true
component_mesh_enabled=true
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

## Known Limitations

- The footprint is an approximate XY projection, not 3D collision.
- The segment definition is direct base XY to viewpoint XY, not a planned navigation path.
- The footprint rasterization is diagnostic-only and does not yet drive solver costs.
- `blocked_path_penalty` is only used in the diagnostic `mesh_footprint_aware_cost_matrix`.
- Synthetic N=50 viewpoints remain smoke/interface data, not benchmark evidence.

## Next Recommended Step

Phase 7B-2 should compare diagnostic obstacle-aware cost candidates against baseline assignments without replacing the
solver inputs. If promoted later, any behavior-changing obstacle-aware path cost should be gated, measured, and reported
as a separate phase.

## Explicit Non-Changes

This phase did not change `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver
behavior, reward, controller math, `assignment_controller.py`, HARL core, training, real robot articulation, IK,
collision, raycast coverage, or final real CSV validation.
