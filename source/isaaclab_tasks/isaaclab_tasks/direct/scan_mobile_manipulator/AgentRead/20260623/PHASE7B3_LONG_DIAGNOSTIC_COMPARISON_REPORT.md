# Phase 7B-3 Long Diagnostic Comparison Report

Date: 2026-06-23

## Scope

Phase 7B-3 ran longer diagnostic-only obstacle-aware candidate comparisons for:

```text
scenario = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
methods = random nearest greedy
num_envs = 1
compare_obstacle_aware_candidates = true
obstacle_diagnostics.mode = diagnostics_only
obstacle_source = component_mesh_footprint
```

This phase did not promote obstacle-aware costs into the live solver path. Baseline solver behavior still uses
`available_mask`, `cost_matrix`, and `noop_id`. Candidate comparison uses a copied assignment problem where only the
copied `cost_matrix` is replaced by `mesh_footprint_aware_cost_matrix`.

## Commands Run

Interpreter check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Syntax check after the reporting-only evaluator patch:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
```

Short diagnostic run:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 3 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e3_s50 --no-write_assignment_history --compare_obstacle_aware_candidates
```

Larger diagnostic run:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 10 --max_steps 100 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e10_s100 --no-write_assignment_history --compare_obstacle_aware_candidates
```

Note: both diagnostic runs were first executed successfully before a small reporting-only evaluator patch. They were
then rerun so the final output directories include compact `per_step_summary` and `per_episode_summary` fields.

## Code Changed

One Python file was changed:

```text
scripts/environments/evaluate_assignment_methods.py
```

Change summary:

```text
- Added reporting aliases for baseline_selected_intersection_rate, candidate_selected_intersection_rate,
  baseline_obstacle_penalty_sum, and candidate_obstacle_penalty_sum.
- Added compact obstacle-aware per_step_summary grouped by method and step index.
- Added compact obstacle-aware per_episode_summary grouped by method and episode index.
- Added episode-index tracking for comparison rows.
```

No solver semantics, masks, rewards, controller logic, HARL code, training code, or environment dynamics were changed.

## Output Directories

```text
results/assignment_evaluation/phase7b3_long_diag_n50_e3_s50/
results/assignment_evaluation/phase7b3_long_diag_n50_e10_s100/
```

Each contains:

```text
diagnostics.json
per_episode.csv
summary.csv
```

These `results/` files were generated locally and should not be committed unless explicitly requested.

## Scenario Diagnostics

From the larger run:

```text
N = 50
M = 3
noop_id = 50
available_actions_shape = 1x3x51
available_mask_shape = 1x3x50
cost_matrix_shape = 1x3x50
mesh_footprint_intersection_shape = 1x3x50
mesh_footprint_aware_cost_shape = 1x3x50
mesh_footprint_intersection_count = 54
obstacle_diagnostics_mode = diagnostics_only
obstacle_source = component_mesh_footprint
```

Comparison metadata:

```text
methods_compared = nearest, greedy
methods_baseline_only = random
mode = diagnostic_only_copied_problem_cost_swap
baseline_cost_field = cost_matrix
candidate_cost_field = mesh_footprint_aware_cost_matrix
solver_behavior_changed = false
```

## Short Run Metrics

Run settings:

```text
num_envs = 1
num_episodes = 3
max_steps = 50
per_step_summary_count = 150
per_episode_summary_count = 9
```

Obstacle-aware comparison summary:

| method | baseline_selected_intersection_rate | candidate_selected_intersection_rate | candidate_changed_assignment_rate | baseline_obstacle_penalty_sum | candidate_obstacle_penalty_sum |
|---|---:|---:|---:|---:|---:|
| random | 0.540000 | 0.000000 | 0.000000 | 24300.0 | 0.0 |
| nearest | 0.000000 | 0.000000 | 0.000000 | 0.0 | 0.0 |
| greedy | 0.000000 | 0.000000 | 0.000000 | 0.0 | 0.0 |

## Larger Run Metrics

Run settings:

```text
num_envs = 1
num_episodes = 10
max_steps = 100
per_step_summary_count = 300
per_episode_summary_count = 30
```

Obstacle-aware comparison summary:

| method | baseline_selected_intersection_rate | candidate_selected_intersection_rate | candidate_changed_assignment_rate | baseline_obstacle_penalty_sum | candidate_obstacle_penalty_sum |
|---|---:|---:|---:|---:|---:|
| random | 0.670000 | 0.000000 | 0.000000 | 201000.0 | 0.0 |
| nearest | 0.043333 | 0.043333 | 0.000000 | 13000.0 | 13000.0 |
| greedy | 0.043333 | 0.043333 | 0.000000 | 13000.0 | 13000.0 |

Standard method summary for the larger run:

| method | episodes | success_rate | mean_final_coverage | mean_coverage_auc |
|---|---:|---:|---:|---:|
| random | 10 | 0.0 | 0.0 | 0.0 |
| nearest | 10 | 0.0 | 0.52 | 0.28740009665489197 |
| greedy | 10 | 0.0 | 0.52 | 0.28740009665489197 |

## Samples

`blocked_baseline_pairs_sample` from the larger run includes these first entries:

| robot | viewpoint_id | baseline_cost | obstacle_aware_cost | obstacle_penalty |
|---|---:|---:|---:|---:|
| robot_1 | 39 | 5.286993503570557 | 105.28699493408203 | 100.0 |
| robot_2 | 26 | 8.430153846740723 | 108.4301528930664 | 100.0 |
| robot_1 | 47 | 6.216582298278809 | 106.21658325195312 | 100.0 |
| robot_1 | 48 | 4.979719161987305 | 104.97972106933594 | 100.0 |
| robot_1 | 44 | 5.826666831970215 | 105.82666778564453 | 100.0 |

`changed_pairs_sample` is empty in both final runs because nearest and greedy candidate assignments did not differ from
their baseline assignments.

## Interpretation

Random baseline selections intersect the mesh footprint often, but random is baseline-only and is not a meaningful
obstacle-aware candidate comparison.

For nearest and greedy, the short run had zero selected intersections. The larger run had a low intersection rate
of 4.3333 percent for both baseline and candidate selections. The obstacle-aware candidate cost did not change any
nearest or greedy assignment decisions, and candidate obstacle penalty did not decrease.

This indicates that the current synthetic N=50 scenario does not strongly stress obstacle effects for nearest/greedy.
The diagnostic pipeline is working, but these data do not provide strong benchmark evidence that obstacle-aware solver
costs would improve this scenario. They suggest using a more obstacle-stressing viewpoint/robot-start setup before
making algorithmic claims.

## Gated Solver-Cost Experiment Decision

Phase 7B-3 supports a later gated solver-cost experiment from a tooling-readiness perspective: the copied-problem
candidate comparison works, compact summaries are available, and solver behavior remains unchanged.

It does not strongly justify a solver-cost experiment from the current synthetic N=50 evidence alone, because baseline
nearest/greedy intersection rates are low and candidate assignments did not reduce obstacle penalties. A later
experiment should remain explicitly gated and should preferably use a scenario where baseline methods select more
mesh-footprint-intersecting pairs.

## Known Limitations

- Synthetic N=50 viewpoints are smoke/interface data only, not final benchmark evidence.
- Mesh footprint diagnostics are approximate XY projected geometry, not 3D collision.
- Direct robot-base-XY to viewpoint-XY segments are diagnostic lines, not planned robot paths.
- No real collision avoidance, articulation, IK, raycast coverage, joint limits, reward changes, controller changes,
  HARL changes, or training changes were implemented.
- The per-step obstacle summary is compact and grouped by method plus step index across episodes; it is not a full
  history dump.

## Final Verification

`git diff --check` result:

```text
passed
```

Git emitted line-ending warnings for edited text files:

```text
warning: in the working copy of 'scripts/environments/evaluate_assignment_methods.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md', LF will be replaced by CRLF the next time Git touches it
```

`git status` summary:

```text
modified: scripts/environments/evaluate_assignment_methods.py
modified: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
untracked: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B3_LONG_DIAGNOSTIC_COMPARISON_REPORT.md
```

Generated `results/assignment_evaluation/...` outputs are local run artifacts and were not staged or committed.
