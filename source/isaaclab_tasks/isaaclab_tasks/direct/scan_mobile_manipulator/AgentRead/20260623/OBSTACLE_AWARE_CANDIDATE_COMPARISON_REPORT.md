# Phase 7B-2 Obstacle-Aware Candidate Comparison Report

## Purpose

Phase 7B-2 compares baseline assignment choices against diagnostic obstacle-aware candidate choices without changing
environment or solver behavior.

The comparison answers:

- how often baseline-selected robot-viewpoint pairs intersect the component OBJ footprint;
- whether nearest/greedy would choose different pairs if the copied candidate problem used
  `mesh_footprint_aware_cost_matrix`;
- how much diagnostic obstacle penalty is present for selected pairs.

This phase does not promote `mesh_footprint_aware_cost_matrix` into actual solver inputs.

## Files Modified

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B2_OBSTACLE_CANDIDATE_COMPARISON_20260623.md
```

## Comparison Method

`evaluate_assignment_methods.py` now accepts:

```text
--compare_obstacle_aware_candidates
```

When the flag is absent, evaluator output is unchanged and no candidate comparison block is written.

When the flag is present, the evaluator:

1. runs the existing baseline solver on the normal prepared assignment problem;
2. records selected-pair footprint intersection and cost metrics;
3. for `nearest` and `greedy`, copies the prepared problem dictionary;
4. replaces only the copied dictionary's `cost_matrix` with `mesh_footprint_aware_cost_matrix`;
5. runs a fresh diagnostic solver on that copied dictionary;
6. writes compact comparison metrics and samples to `diagnostics.json`.

The live solver path still consumes:

```text
available_mask
cost_matrix
noop_id
```

## Methods Compared

```text
random:
  baseline selected-pair intersection statistics only

nearest:
  baseline vs copied-problem obstacle-aware candidate

greedy:
  baseline vs copied-problem obstacle-aware candidate
```

`random` is intentionally not reinterpreted as an obstacle-aware optimizer.

## Metrics Added

The optional diagnostics block includes:

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

The output does not dump full cost matrices or occupancy grids.

## Smoke Results

### Phase 7B-1 Wrapper Regression

```text
command: test_assignment_harl_wrapper_smoke.py with algorithm_proxy_component_mesh.yaml
result_file: results/assignment_diagnostics/mesh_footprint_obstacle_phase7b2_regression_smoke.json
status: passed
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
```

### Candidate Comparison Evaluator Smoke

```text
command: evaluate_assignment_methods.py with algorithm_proxy_component_mesh.yaml and --compare_obstacle_aware_candidates
output_dir: results/assignment_evaluation/obstacle_aware_candidate_phase7b2_eval_smoke
status: passed
methods: random, nearest, greedy
mesh_footprint_intersection_count=54
methods_compared=[nearest, greedy]
methods_baseline_only=[random]
```

Observed one-step comparison summary:

| Method | Baseline selected pairs | Baseline intersections | Candidate changed assignments | Candidate intersections | Baseline penalty sum | Candidate penalty sum |
|---|---:|---:|---:|---:|---:|---:|
| random | 3 | 0 | 0 | 0 | 0.0 | 0.0 |
| nearest | 3 | 0 | 0 | 0 | 0.0 | 0.0 |
| greedy | 3 | 0 | 0 | 0 | 0.0 | 0.0 |

In this one-step smoke, nearest and greedy candidate assignments matched their baseline assignments.

### Default Evaluator Regression

```text
command: evaluate_assignment_methods.py with algorithm_proxy_component_mesh.yaml without comparison flag
output_dir: results/assignment_evaluation/obstacle_aware_candidate_phase7b2_default_regression
status: passed
comparison block: absent
```

### Bbox Scenario Regression

```text
command: evaluate_assignment_methods.py with algorithm_proxy_bbox.yaml and --compare_obstacle_aware_candidates
output_dir: results/assignment_evaluation/obstacle_aware_candidate_phase7b2_bbox_regression
status: passed
comparison available=false
skip reason=missing mesh-footprint tensors
```

### Visual Scenario Regression

```text
command: test_assignment_harl_wrapper_smoke.py with real_scene_proxy_headless.yaml
result_file: results/assignment_diagnostics/visual_real_scene_phase7b2_regression_smoke.json
status: passed
robot visual mesh remains enabled/spawned/following
obstacle diagnostics remain disabled
```

## Known Limitations

- This is a one-step smoke, not a benchmark.
- The obstacle-aware candidate comparison only changes a copied problem dictionary inside evaluator diagnostics.
- Candidate comparisons use the same prepared `available_mask` as the baseline for that step.
- Random is reported only for selected-pair intersection statistics.
- The mesh footprint remains an approximate XY projection, not 3D collision or path planning.

## Next Recommended Step

Run a longer diagnostic-only comparison over the hybrid scenario to collect nonzero changed-pair samples and blocked
baseline samples before considering any gated obstacle-aware solver experiment.

Do not promote `mesh_footprint_aware_cost_matrix` into solver inputs until the diagnostic evidence is reviewed.
