# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9A RL/dynamic-policy readiness check is complete at audit/smoke level.

Phase 7B through Phase 8 wrap-up is complete and documented. Phase 9A confirms that the N=50, M=3 RL wrapper is
shape-compatible, but current observations/rewards are not yet strong enough for meaningful dynamic-policy evaluation
against the Phase 8 stagnation pattern.

Do not start RL training or formal RL evaluation until a future task explicitly scopes Phase 9B or later. Do not add
more handcrafted baseline rules unless a future task explicitly scopes them.

## Latest Documentation

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
```

Archived the previous progress file:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B8_WRAPUP_20260628.md
```

The Phase 9A readiness check changed markdown only. No Python, solver, environment, reward, controller, HARL, or
training files were changed.

Phase 9A ran one wrapper compatibility smoke and wrote:

```text
results/assignment_diagnostics/phase9a_rl_readiness_n50_m3_smoke.json
```

## Phase 8 Baseline Reference

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Run shape:

```text
N = 50
M = 3
num_episodes = 10
max_steps = 300
methods = random, nearest, greedy, nearest_conflict_aware, greedy_conflict_aware
```

Main table:

```text
random:
  success_rate = 0.0
  final_coverage = 0.004
  coverage_auc = 0.0038
  selected_target_conflict_rate = 0.4157
  inter_robot_overlap_rate = 0.6759
  actual_base_motion_intersection_rate = 0.9050

nearest / greedy:
  success_rate = 0.0
  final_coverage = 0.900
  coverage_auc = 0.7468
  selected_target_conflict_rate = 0.7191
  inter_robot_overlap_rate = 0.6689
  actual_base_motion_intersection_rate = 0.0167

nearest_conflict_aware / greedy_conflict_aware:
  success_rate = 0.0
  final_coverage = 0.900
  coverage_auc = 0.7468
  selected_target_conflict_rate = 0.6622
  inter_robot_overlap_rate = 0.5753
  actual_base_motion_intersection_rate = 0.1237
```

Stagnation:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
late repeated assignments:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
```

Interpretation: conflict-aware ablations reduce selected-target and inter-robot conflict metrics, but they do not
improve final coverage and they increase actual proxy base-motion component-footprint crossing risk. The evidence now
points toward RL/dynamic-policy readiness work rather than more handcrafted baseline variants.

## Diagnostic Boundaries

The following remain diagnostic-only:

```text
mesh_footprint_aware_cost_matrix
selected assignment lines
selected_target_conflict metrics
inter_robot_overlap metrics
actual proxy base-motion crossing metrics
```

The following were not changed by the wrap-up:

```text
cost_matrix
available_mask
feasible_mask
static_geometric_feasible_mask
solver behavior
reward
controller
assignment_controller.py
HARL
training
environment dynamics
collision / IK / raycast / path planning
```

## Verification

No `py_compile` was required because this task changed markdown only.

Phase 9A smoke:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9a_rl_readiness_n50_m3_smoke.json
```

Result:

```text
[OK] assignment HARL wrapper smoke passed
num_agents = 3
num_viewpoints = 50
noop_id = 50
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
cost_matrix_shape = [1, 3, 50]
```

Required final checks for this handoff:

```text
git diff --check
git status --short
```

## Next Step

Recommended next task: scoped Phase 9B technical RL smoke planning or an observation/reward design phase.

Start from:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
```

Do not evaluate old checkpoints on N=50. Old assignment checkpoints found in `results/isaaclab/.../assignment_happo_*`
have 13-class categorical heads, which means fixed N=12 plus noop. Old `scan_happo` checkpoints are 9D continuous
policies.

If proceeding to Phase 9B, first decide whether it is only a no-checkpoint action/mask technical smoke or whether an
observation/reward design update is needed before any meaningful dynamic-policy evaluation.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B8_WRAPUP_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE8_BASELINE_VALIDATION_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
```
