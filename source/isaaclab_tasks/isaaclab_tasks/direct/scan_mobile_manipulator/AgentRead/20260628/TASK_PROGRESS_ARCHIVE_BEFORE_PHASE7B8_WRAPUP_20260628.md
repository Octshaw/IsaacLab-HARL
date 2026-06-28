# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 8 real-component proxy baseline validation is complete.

The evaluation used the real component mesh + task-space proxy robot scenario with N=50 viewpoints and M=3 enabled
robots:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Phase 8 evaluated:

```text
random
nearest
greedy
nearest_conflict_aware
greedy_conflict_aware
```

`random`, `nearest`, and `greedy` are primary baselines. `nearest_conflict_aware` and `greedy_conflict_aware` remain
Phase 7D-2 ablation baselines.

Phase 8 is evaluation/reporting only. Solver behavior, masks, costs, rewards, controller behavior, HARL, training,
environment dynamics, and robot movement behavior were not changed.

## Outputs

Smoke:

```text
results/assignment_evaluation/phase8_baseline_smoke_n50_e2_s80/
```

Main validation:

```text
results/assignment_evaluation/phase8_baseline_n50_e10_s300/
```

Each output contains:

```text
summary.csv
per_episode.csv
assignment_history.csv
diagnostics.json
```

## Key Phase 8 Results

Main run: `num_envs=1`, `num_episodes=10`, `max_steps=300`, N=50, M=3.

Coverage:

```text
random:
  success_rate = 0.0
  mean_final_coverage = 0.004
  mean_final_covered_count = 0.2 / 50
  mean_coverage_auc = 0.0038

nearest / greedy:
  success_rate = 0.0
  mean_final_coverage = 0.900
  mean_final_covered_count = 45 / 50
  mean_coverage_auc = 0.7468

nearest_conflict_aware / greedy_conflict_aware:
  success_rate = 0.0
  mean_final_coverage = 0.900
  mean_final_covered_count = 45 / 50
  mean_coverage_auc = 0.7468
```

Conflict / overlap diagnostics:

```text
nearest / greedy:
  selected_target_conflict_pair_count_total = 5790
  selected_target_conflict_rate_mean = 0.7191
  inter_robot_overlap_pair_count_total = 5210
  inter_robot_overlap_rate_mean = 0.6689

nearest_conflict_aware / greedy_conflict_aware:
  selected_target_conflict_pair_count_total = 5620
  selected_target_conflict_rate_mean = 0.6622
  inter_robot_overlap_pair_count_total = 5000
  inter_robot_overlap_rate_mean = 0.5753
```

Actual proxy base-motion component-footprint crossing:

```text
random:
  actual_base_motion_intersection_step_count_total = 2706
  actual_base_motion_intersection_rate_mean = 0.9050

nearest / greedy:
  actual_base_motion_intersection_step_count_total = 50
  actual_base_motion_intersection_rate_mean = 0.0167
  crossing robots = robot_0: 50, robot_1: 0, robot_2: 0

nearest_conflict_aware / greedy_conflict_aware:
  actual_base_motion_intersection_step_count_total = 370
  actual_base_motion_intersection_rate_mean = 0.1237
  crossing robots = robot_0: 50, robot_1: 320, robot_2: 0
```

Interpretation: conflict-aware ablations reduce selected-target and inter-robot conflict metrics, but they do not
improve coverage and they increase actual proxy base-motion component-footprint crossing risk.

## Stagnation Finding

Nearest, greedy, and both conflict-aware ablations plateaued at 45/50 coverage:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
late repeated assignments:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
```

This supports moving toward dynamic policy/RL design with diagnostics carried forward, rather than adding more
handcrafted baseline rules.

## Verification

Interpreter check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Smoke run passed:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 2 --max_steps 80 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase8_baseline_smoke_n50_e2_s80 --write_assignment_history --compare_obstacle_aware_candidates
```

Main run passed:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 10 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase8_baseline_n50_e10_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

No Python files were changed during Phase 8, so no new `py_compile` was required for this phase.

Final `git diff --check` passed with LF-to-CRLF warnings only.

## Do Not Do

- Do not start RL evaluation or retraining automatically.
- Do not add new handcrafted solver rules.
- Do not modify solvers.
- Do not promote obstacle or conflict diagnostic costs into live solver inputs.
- Do not modify masks, base `cost_matrix`, rewards, controller behavior, HARL, training, or environment dynamics.
- Do not add collision, local avoidance, ORCA, IK, path planning, retry fallback, cooldown, or hard blocking.
- Do not claim actual base-motion crossing is full 3D collision checking.
- Do not treat N=50 proxy validation results as final benchmark evidence.
- Do not commit `results/` unless explicitly requested.

## Next Step

Recommended next task: prepare RL/dynamic-policy readiness checks using the Phase 8 baseline table as the non-RL
reference. First verify current observation/action/mask compatibility for N=50, M=3. Do not start training until the
RL compatibility check and reporting plan are explicitly scoped.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE8_BASELINE_VALIDATION_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/NEXT_PHASE_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_PLAN.md
```
