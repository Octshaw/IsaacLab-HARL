# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7E actual proxy base-motion mesh-footprint crossing diagnostics are implemented and headless validated.

The evaluator now measures executed proxy base motion segments:

```text
previous robot base XY -> current robot base XY
```

against the existing diagnostic component mesh footprint. This is separate from selected-assignment diagnostic lines:

```text
current robot base XY -> selected viewpoint XY
```

and separate from selected-target conflict diagnostics:

```text
distance between selected target viewpoint XY positions
```

Phase 7E is diagnostic-only. Solver behavior, masks, costs, rewards, controller behavior, HARL, training, and
environment dynamics remain unchanged.

## Active Scenario

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Active diagnostic blocks include:

```text
obstacle_diagnostics.enabled: true
actual_base_motion_obstacle_diagnostics.enabled: true
obstacle_debug_visualization.line_source: selected_assignments
inter_robot_conflict_diagnostics.enabled: true
selected_target_conflict_candidate_comparison.enabled: true
conflict_aware_baseline.enabled: true
```

## Files Changed In Phase 7E

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7E_ACTUAL_BASE_MOTION_20260628.md
```

## Verification

Syntax checks passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py scripts/environments/test_assignment_harl_wrapper_smoke.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/conflict_aware_solver.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py
```

Final lightweight checks:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
git diff --check
git status --short
```

`git diff --check` passed with line-ending warnings only.

Headless smoke passed:

```text
results/assignment_evaluation/phase7e_actual_base_motion_crossing_smoke_e1_s80/
```

Main 300-step diagnostic run passed:

```text
results/assignment_evaluation/phase7e_actual_base_motion_crossing_e1_s300/
```

Methods evaluated:

```text
greedy
greedy_conflict_aware
nearest
nearest_conflict_aware
```

## Phase 7E Key Metrics

300-step run, `num_envs=1`, `num_episodes=1`, N=50, M=3:

```text
greedy:
  actual_base_motion_intersection_step_count_total = 5
  actual_base_motion_intersection_rate_mean = 0.0167224080
  crossing robots = robot_0: 5, robot_1: 0, robot_2: 0
  crossing steps = 124-128

nearest:
  actual_base_motion_intersection_step_count_total = 5
  actual_base_motion_intersection_rate_mean = 0.0167224080
  crossing robots = robot_0: 5, robot_1: 0, robot_2: 0
  crossing steps = 124-128

greedy_conflict_aware:
  actual_base_motion_intersection_step_count_total = 37
  actual_base_motion_intersection_rate_mean = 0.1237458194
  crossing robots = robot_0: 5, robot_1: 32, robot_2: 0
  crossing steps = 90-112, 114-122, 124-128

nearest_conflict_aware:
  actual_base_motion_intersection_step_count_total = 37
  actual_base_motion_intersection_rate_mean = 0.1237458194
  crossing robots = robot_0: 5, robot_1: 32, robot_2: 0
  crossing steps = 90-112, 114-122, 124-128
```

Interpretation: actual proxy base-motion crossing was detected. Conflict-aware baseline variants retained the baseline
`robot_0` crossing block and added a `robot_1` crossing block in this scenario.

## Do Not Do

- Do not start Phase 8 automatically.
- Do not start RL evaluation or training automatically.
- Do not change original `random`, `nearest`, or `greedy` behavior.
- Do not promote obstacle or conflict diagnostic costs into live solver inputs.
- Do not modify `assignment_controller.py`, HARL, rewards, masks, base `cost_matrix`, or environment dynamics.
- Do not add physical collision, IK, joint limits, path planning, ORCA, local avoidance, retry fallback, cooldown, or
  hard blocking.
- Do not claim selected-assignment lines are robot trajectories.
- Do not claim actual base-motion crossing is full 3D collision checking.
- Do not commit `results/` unless explicitly requested.

## Next Step

Recommended next task: Phase 8 can proceed only with this diagnostic included and clearly reported as a proxy execution
limitation. Do not claim obstacle avoidance is solved. Consider later opt-in path-crossing penalty/observation
experiments, but do not add collision, planner, controller, reward, or RL changes without a new scoped task.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7E_ACTUAL_BASE_MOTION_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/NEXT_PHASE_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_PLAN.md
```
