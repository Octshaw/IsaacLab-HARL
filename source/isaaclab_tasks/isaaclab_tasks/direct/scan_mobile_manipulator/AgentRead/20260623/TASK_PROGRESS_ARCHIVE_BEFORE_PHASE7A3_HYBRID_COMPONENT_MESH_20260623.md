# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7A-2 Algorithm Scenario Decoupling is complete.

The project now has two explicit scenario families:

```text
Algorithm scenario:
  configs/scenarios/algorithm_proxy_bbox.yaml
  lightweight bbox/debug-marker path
  no robot OBJ mesh spawn
  no component OBJ mesh load

Visual scenario:
  configs/scenarios/real_scene_proxy_headless.yaml
  component OBJ + ScanRobot.obj visual path preserved
  for GUI inspection, screenshots, videos, and presentation material
```

This is scenario/config decoupling only. Assignment tensors, cost matrix semantics, controller math, reward logic,
HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast coverage, and final real CSV
validation were not changed.

## Latest Completed Phase

Phase 7A-2: Algorithm Scenario Decoupling.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_bbox.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A2_ALGORITHM_SCENARIO_DECOUPLING_20260623.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Active Architecture / Implementation Path

Scenario YAML now supports:

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

`real_scene_proxy_headless.yaml` explicitly preserves:

```yaml
visualization:
  robot_visual_mode: mesh
  component_visual_mode: mesh
```

The algorithm scenario still uses:

```text
robots_real_proxy.yaml
mobile_scanner_profiles.yaml
synthetic_smoke_n50.csv
component_proxy.type=bbox
```

## Latest Verification

Pre-change Phase 7A lightweight checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile capability_config.py scan_mobile_manipulator_env.py scenario_config.py test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python capability_config.py configs/capabilities/mobile_scanner_profiles.yaml
conda run -p C:\isaacenvs\isaac45_harl python robot_config.py configs/robots/robots_real_proxy.yaml
```

Phase 7A-2 syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scenario_config.py scan_mobile_manipulator_env.py test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
```

Algorithm wrapper smoke passed:

```text
result_file=results/assignment_diagnostics/algorithm_proxy_bbox_phase7a2_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mode=debug_marker
component_visual_mode=bbox
robot_visual_mesh_enabled=false
component_mesh_enabled=false
visual_mesh_spawned_by_robot=false for robot_0, robot_1, robot_2
scene creation was about 0.026 seconds
```

Algorithm evaluator smoke passed:

```text
output_dir=results/assignment_evaluation/algorithm_proxy_bbox_phase7a2_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
robot_visual_mesh_enabled=false
component_mesh_enabled=false
```

Visual scenario regression smoke passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7a2_regression_smoke.json
robot_visual_mode=mesh
component_visual_mode=mesh
robot_visual_mesh_enabled=true
component_mesh_enabled=true
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
visual_follow_enabled_by_robot=true for robot_0, robot_1, robot_2
available_actions=[1, 3, 51]
```

## Known Issues / Limitations

- `visual_mesh_exists_by_robot` may still report `true` in algorithm scenarios because robot YAML metadata points to an
  existing OBJ path. The algorithm path is confirmed by `robot_visual_mesh_enabled=false`,
  `visual_mesh_enabled_by_robot=false`, and `visual_mesh_spawned_by_robot=false`.
- `diagnose_assignment_controller_feasibility.py` was not extended with visualization mode propagation in this phase.
- GUI visual inspection was not run.
- Temporary and synthetic CSVs remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not add obstacle-aware path cost or inter-robot conflict avoidance until the next phase.
- Do not add dynamic reassignment policy yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Phase 7B-1: add obstacle-aware path-cost diagnostics in algorithm_proxy_bbox.yaml only.
```

Start with additional diagnostic fields, for example:

```text
straight_line_cost_matrix
obstacle_intersection_mask
obstacle_penalty_matrix
obstacle_aware_cost_matrix
```

Keep existing `cost_matrix`, `available_mask`, solver behavior, reward, and controller behavior unchanged until the
new diagnostics are validated.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A2_ALGORITHM_SCENARIO_DECOUPLING_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A_YAML_CAPABILITIES_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
