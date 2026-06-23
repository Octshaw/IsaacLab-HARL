# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2 Obstacle-Aware Candidate Comparison is complete.

The evaluator can now optionally compare baseline assignment outputs against diagnostic obstacle-aware candidate outputs
using the hybrid algorithm component-mesh scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

The comparison is diagnostic-only. It does not promote `mesh_footprint_aware_cost_matrix` into solver inputs and does
not change `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver default behavior,
reward, controller math, HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast
coverage, or final real CSV validation.

## Latest Completed Phase

Phase 7B-2: compare obstacle-aware cost candidates against baseline assignments.

Modified files:

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B2_OBSTACLE_CANDIDATE_COMPARISON_20260623.md
```

## Evaluator Comparison Flag

New optional evaluator flag:

```text
--compare_obstacle_aware_candidates
```

When the flag is absent, the evaluator does not write the comparison block.

When the flag is present:

1. baseline solvers still run on the normal prepared problem using `cost_matrix`;
2. selected-pair intersection and penalty metrics are recorded;
3. `nearest` and `greedy` are also run on a copied problem dictionary where only `cost_matrix` is replaced with
   `mesh_footprint_aware_cost_matrix`;
4. random is reported as baseline selected-pair intersection statistics only.

## Metrics Added

The optional diagnostics block includes compact per-method summaries:

```text
selected_pair_count
selected_intersection_count
selected_intersection_rate
selected_baseline_cost_sum
selected_obstacle_aware_cost_sum
candidate_changed_assignment_count
candidate_changed_assignment_rate
candidate_intersection_count
candidate_intersection_rate
candidate_baseline_cost_sum
candidate_obstacle_aware_cost_sum
obstacle_penalty_sum_for_baseline_selection
obstacle_penalty_sum_for_candidate_selection
baseline_selected_pairs_sample
candidate_selected_pairs_sample
changed_pairs_sample
blocked_baseline_pairs_sample
```

Full matrices and occupancy grids are not dumped into JSON.

## Latest Verification

Interpreter check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Output:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Syntax check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
```

Phase 7B-1 wrapper regression passed:

```text
result_file=results/assignment_diagnostics/mesh_footprint_obstacle_phase7b2_regression_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
mesh_footprint_aware_cost_matrix present
mesh_footprint_intersection_mask present
```

Candidate comparison evaluator smoke passed:

```text
output_dir=results/assignment_evaluation/obstacle_aware_candidate_phase7b2_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
mesh_footprint_intersection_count=54
methods_compared=[nearest, greedy]
methods_baseline_only=[random]
```

Observed one-step comparison summary:

```text
random:  selected_pair_count=3, selected_intersection_count=0, candidate_available=false
nearest: selected_pair_count=3, selected_intersection_count=0, candidate_changed_assignment_count=0
greedy:  selected_pair_count=3, selected_intersection_count=0, candidate_changed_assignment_count=0
```

Default evaluator regression passed:

```text
output_dir=results/assignment_evaluation/obstacle_aware_candidate_phase7b2_default_regression
comparison block absent without --compare_obstacle_aware_candidates
random/nearest/greedy completed
```

Bbox scenario regression passed:

```text
output_dir=results/assignment_evaluation/obstacle_aware_candidate_phase7b2_bbox_regression
obstacle diagnostics disabled
comparison available=false
skip reason=missing mesh-footprint tensors
random/nearest/greedy completed
```

Visual scenario regression passed:

```text
result_file=results/assignment_diagnostics/visual_real_scene_phase7b2_regression_smoke.json
robot_visual_mesh_enabled=true
visual_mesh_spawned_by_robot=true for all three robots
visual_follow_enabled_by_robot=true for all three robots
obstacle diagnostics disabled
assignment smoke passed
```

## Known Issues / Limitations

- This is a one-step smoke, not a benchmark.
- Candidate comparison uses a copied assignment problem only; the live solver path remains unchanged.
- Candidate comparison uses the same prepared `available_mask` as the baseline for the step.
- Random is not treated as an obstacle-aware optimizer.
- The mesh footprint is still an approximate XY projection, not 3D collision, PhysX collision, or path planning.
- Synthetic N=50 viewpoints remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into actual solver inputs yet.
- Do not replace `cost_matrix`, `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver default behavior, reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add bbox hard blocking, mesh-footprint hard blocking, inter-robot conflict avoidance, or dynamic reassignment yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Phase 7B-3: run a longer diagnostic-only obstacle-aware candidate comparison and inspect changed/blocked pair samples.
```

Keep the next phase diagnostic-only unless a separate gated task explicitly promotes an obstacle-aware cost candidate into
solver inputs.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B2_OBSTACLE_CANDIDATE_COMPARISON_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
