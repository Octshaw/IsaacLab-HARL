# Stage 4B Real Component N24 Top-K Candidate Ablation Report

Date: 2026-06-15

## Scope

This diagnostic checks whether the remembered nearest-8 viewpoint restriction is responsible for the generated
real-component N=24 nearest/greedy baselines stopping at 17/24 coverage.

This is diagnostic-only. No assignment-RL training/evaluation, HARL core changes, reward changes,
`assignment_controller.py` changes, controller math changes, retry/fallback logic, pair-level Level 2 feasibility
filtering, real robot articulation, IK, collision, or raycast coverage were added.

`real_component_bbox_sample.csv` remains pipeline sanity/smoke data only, not final viewpoint planning output.

## Code Path Inspection

Relevant code paths:

- `scan_mobile_manipulator_env.py`
  - `num_viewpoints_in_observation = 8` is used by `_get_nearest_viewpoint_observation()` to select nearest slots for
    the RL/local observation.
  - `get_assignment_problem()` builds `available_mask = feasible_mask & (~viewpoints_covered[:, None, :])` across the
    full fixed-N viewpoint set.
- `nearest_solver.py` / `greedy_solver.py`
  - Both solvers consume `problem["available_mask"]` and `problem["cost_matrix"]`.
  - They do not read `num_viewpoints_in_observation`.
- `assignment_harl_wrapper.py`
  - `available_actions` is generated from the assignment problem/action mask and remains `[num_envs, num_agents, N+1]`.

Conclusion from inspection: the original nearest-8 behavior affected RL/local observation only. It did not restrict the
baseline/evaluator solver candidate set or the evaluator `available_actions` mask.

For explicit ablation support, `evaluate_assignment_methods.py` now exposes:

```text
--viewpoint_candidate_top_k K
```

Semantics:

- `K > 0`: restrict each env/agent solver candidate mask to nearest currently available `K` viewpoints.
- `K <= 0`: use all currently available/feasible/uncovered viewpoints.

The evaluator saves and prints:

```text
viewpoint_candidate_top_k
candidate_mode
num_viewpoints
noop_id
available_actions_shape
```

`scenario_config.py` also accepts optional smoke defaults from top-level `viewpoint_candidate_top_k`,
`viewpoints.candidate_top_k`, or `assignment.viewpoint_candidate_top_k`.

## Scenario

```text
scenario_config:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml

num_viewpoints: 24
noop_id: 24
available_actions_shape: [1, 3, 25]
methods: nearest, greedy
num_episodes: 1
max_steps: 300
```

## Runs

Top-k=8 ablation:

```text
results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/
candidate_mode: nearest_top_k
viewpoint_candidate_top_k: 8
```

All-viewpoints ablation:

```text
results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/
candidate_mode: all_viewpoints
viewpoint_candidate_top_k: -1
```

Both output directories contain:

```text
per_episode.csv
summary.csv
diagnostics.json
assignment_history.csv
```

## Result Summary

| candidate mode | method | final_covered_count | final_coverage | success | final_uncovered_viewpoint_ids |
| --- | --- | ---: | ---: | ---: | --- |
| nearest_top_k, K=8 | nearest | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| nearest_top_k, K=8 | greedy | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| all_viewpoints, K=-1 | nearest | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| all_viewpoints, K=-1 | greedy | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |

Coverage does not improve from 17/24 when all viewpoints are visible to the solver.

## Target Assignment Counts

Target uncovered ids:

```text
[1, 2, 8, 12, 13, 14, 20]
```

Assignment counts from `assignment_history.csv`:

| candidate mode | method | v1 | v2 | v8 | v12 | v13 | v14 | v20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nearest_top_k, K=8 | nearest | 167 | 0 | 0 | 253 | 190 | 0 | 0 |
| nearest_top_k, K=8 | greedy | 167 | 0 | 0 | 253 | 190 | 0 | 0 |
| all_viewpoints, K=-1 | nearest | 167 | 0 | 0 | 253 | 190 | 0 | 0 |
| all_viewpoints, K=-1 | greedy | 167 | 0 | 0 | 253 | 190 | 0 | 0 |

Answer to the key question: viewpoints `2 / 8 / 14 / 20` are still never assigned when all viewpoints are visible.

## Interpretation

The top-k limitation was not masking the assignment problem in the current evaluator/baseline path. The original top-8
restriction is an RL observation/local feature limit, not a solver candidate limit.

The new evaluator top-k option confirms this directly: explicitly forcing top-k=8 produces the same trace as
all-viewpoints mode for this generated N=24 scenario.

Future Stage 4B baseline evaluation should use all-viewpoints candidate mode (`--viewpoint_candidate_top_k -1`) because
it matches the project assumption:

```text
given a fixed viewpoint set + robot capability matrix, perform dynamic task allocation
```

However, all-viewpoints mode does not solve the current generated N=24 baseline issue.

## Remaining Unresolved Issue

Nearest/greedy still:

- skip `2 / 8 / 14 / 20` completely,
- repeatedly assign `1 / 12 / 13`,
- fail to convert those repeated assignments into coverage,
- remain at 17/24 through timeout.

Because Level 2 diagnostics showed all seven target viewpoints are coverable by at least one robot, the remaining issue is
more likely baseline ordering/retry/fallback behavior and/or pair-level controller/coverage-gate feasibility than global
candidate visibility.

## Recommended Next Step

Keep all-viewpoints mode for future Stage 4B baseline diagnostics, then run the diagnostic-only join that labels each
`assignment_history.csv` row using Level 2 pair-coverability:

```text
assigned_to_known_coverable_pair
assigned_to_known_level2_failing_pair
assigned_to_unchecked_pair
```

That join should quantify whether the stuck repeated assignments are going to known failing pairs before choosing between
pair-level feasibility filtering, retry/fallback logic, or targeted controller/coverage-gate investigation.
