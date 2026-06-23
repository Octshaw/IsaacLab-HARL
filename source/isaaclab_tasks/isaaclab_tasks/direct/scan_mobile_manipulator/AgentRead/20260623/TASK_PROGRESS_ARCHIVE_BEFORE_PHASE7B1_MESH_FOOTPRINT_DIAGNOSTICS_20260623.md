# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7A-3 Hybrid Algorithm Component-Mesh Scenario is complete.

The project now has three scenario roles:

```text
Fast algorithm regression:
  configs/scenarios/algorithm_proxy_bbox.yaml
  robot markers, component bbox/proxy, no large OBJ visual assets

Hybrid algorithm visual debugging:
  configs/scenarios/algorithm_proxy_component_mesh.yaml
  robot markers, measured component OBJ mesh, bbox/proxy metadata
  no ScanRobot.obj robot visual mesh spawn

Full visual/demo scenario:
  configs/scenarios/real_scene_proxy_headless.yaml
  component OBJ + ScanRobot.obj robot visuals
  for GUI inspection, screenshots, videos, and presentation material
```

This remains scenario/config work. Assignment tensors, feasible masks, cost matrix semantics, controller math, reward
logic, HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast coverage, and final
real CSV validation were not changed.

## Latest Completed Phase

Phase 7A-3: Hybrid Algorithm Component-Mesh Scenario.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A3_HYBRID_COMPONENT_MESH_20260623.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No Python files were changed for Phase 7A-3.

## Active Architecture / Implementation Path

Scenario YAML visual controls from Phase 7A-2 remain active:

```yaml
visualization:
  robot_visual_mode: mesh        # mesh / debug_marker / none
  component_visual_mode: mesh    # mesh / bbox / none
```

`algorithm_proxy_bbox.yaml` uses:

```yaml
visualization:
  robot_visual_mode: debug_marker
  component_visual_mode: bbox
```

`algorithm_proxy_component_mesh.yaml` uses:

```yaml
visualization:
  robot_visual_mode: debug_marker
  component_visual_mode: mesh
```

`real_scene_proxy_headless.yaml` uses:

```yaml
visualization:
  robot_visual_mode: mesh
  component_visual_mode: mesh
```

All three scenarios use `robots_real_proxy.yaml`, `mobile_scanner_profiles.yaml`, and the synthetic N=50 smoke
viewpoint CSV unless explicitly overridden.

## Latest Verification

Pre-change Phase 7A-2 checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scenario_config.py scan_mobile_manipulator_env.py test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py ... --scenario_config configs/scenarios/algorithm_proxy_bbox.yaml --result_file results/assignment_diagnostics/algorithm_proxy_bbox_phase7a2_prerun_smoke.json
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py ... --scenario_config configs/scenarios/algorithm_proxy_bbox.yaml --output_name algorithm_proxy_bbox_phase7a2_prerun_eval_smoke --no-write_assignment_history
```

Hybrid wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_component_mesh_phase7a3_smoke.json
scenario_name=algorithm_proxy_component_mesh
scenario_type=algorithm_visual_debug
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mode=debug_marker
component_visual_mode=mesh
robot_visual_mesh_enabled=false
component_mesh_enabled=true
visual_mesh_spawned_by_robot=false for robot_0, robot_1, robot_2
component mesh diagnostics present
```

Hybrid evaluator smoke passed:

```text
output_dir=results/assignment_evaluation/algorithm_proxy_component_mesh_phase7a3_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
random/nearest/greedy completed
```

Fast algorithm bbox regression smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7a3_regression_smoke.json
robot_visual_mode=debug_marker
component_visual_mode=bbox
robot_visual_mesh_enabled=false
component_mesh_enabled=false
available_actions=[1, 3, 51]
```

Visual scenario regression smoke passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7a3_regression_smoke.json
robot_visual_mode=mesh
component_visual_mode=mesh
robot_visual_mesh_enabled=true
component_mesh_enabled=true
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
visual_follow_enabled_by_robot=true for robot_0, robot_1, robot_2
available_actions=[1, 3, 51]
```

Whitespace check passed for the Phase 7A-3 changed files after the report and handoff update.

## Known Issues / Limitations

- `algorithm_proxy_component_mesh.yaml` loads the measured component OBJ only as visual geometry.
- The bbox proxy remains the only component proxy used by assignment diagnostics.
- No obstacle-aware path cost, mesh-footprint occupancy, or hard blocking has been added.
- GUI visual inspection was not run.
- Temporary and synthetic CSVs remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not add obstacle-aware path cost or mesh-footprint occupancy without keeping diagnostics separate first.
- Do not add bbox-based hard blocking, inter-robot conflict avoidance, or dynamic reassignment yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Phase 7B-1: obstacle-aware path-cost diagnostics only.
```

Start by adding diagnostic fields such as:

```text
straight_line_cost_matrix
obstacle_intersection_mask
obstacle_penalty_matrix
obstacle_aware_cost_matrix
```

Keep existing `cost_matrix`, `available_mask`, solver behavior, reward, and controller behavior unchanged until the new
diagnostics are validated.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A3_HYBRID_COMPONENT_MESH_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A2_ALGORITHM_SCENARIO_DECOUPLING_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A_YAML_CAPABILITIES_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
