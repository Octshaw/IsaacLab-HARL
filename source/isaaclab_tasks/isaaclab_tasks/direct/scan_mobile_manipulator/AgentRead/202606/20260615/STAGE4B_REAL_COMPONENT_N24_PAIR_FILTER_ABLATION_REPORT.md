# Stage 4B Real Component N24 Pair-Filter Ablation Report

Date: 2026-06-15

## Scope

This report compares generated real-component N=24 nearest/greedy baseline runs with and without a temporary
Level-2-derived pair-level feasibility filter.

This is a diagnostic experiment only. The filter is an optional evaluator mode and does not change environment default
static feasibility, controller behavior, reward logic, HARL core, the 9D action path, assignment-RL, IK, collision,
raycast coverage, or real robot articulation.

`real_component_bbox_sample.csv` remains temporary pipeline sanity data, not final viewpoint planning output.

## Implementation

`scripts/environments/evaluate_assignment_methods.py` now supports:

```text
--level2_pair_filter_json results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json
```

When provided, the evaluator loads Level 2 pair diagnostics and applies them only to the solver input
`problem["available_mask"]`:

- `covered == false`: deny that `(agent_id, viewpoint_id)` pair.
- `covered == true`: allow that pair.
- pair not present in the Level 2 JSON: leave unchanged.

This is pair-level filtering, not viewpoint-level filtering. A viewpoint remains assignable if at least one robot has an
allowed or unchecked pair.

Diagnostics now include:

```text
level2_pair_filter_enabled
level2_pair_filter_json
num_level2_pairs_loaded
num_level2_pairs_denied
num_level2_pairs_allowed
denied_pairs
allowed_pairs
unchecked_pairs_policy = "unchanged"
candidate_mode
viewpoint_candidate_top_k
num_viewpoints
noop_id
available_actions_shape
```

For the filtered run:

```text
num_level2_pairs_loaded: 21
num_level2_pairs_denied: 10
num_level2_pairs_allowed: 11
unchecked_pairs_policy: unchanged
candidate_mode: all_viewpoints
viewpoint_candidate_top_k: -1
available_actions_shape: [1, 3, 25]
```

## Runs

Control:

```text
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/
level2_pair_filter_enabled: false
```

Pair-filtered:

```text
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/
level2_pair_filter_enabled: true
```

Both runs used:

```text
scenario_config: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
methods: nearest greedy
num_episodes: 1
max_steps: 300
viewpoint_candidate_top_k: -1
assignment_history: enabled
```

## Coverage Comparison

| run | method | final_covered_count | final_coverage | success | final_uncovered_viewpoint_ids |
| --- | --- | ---: | ---: | ---: | --- |
| no pair filter | nearest | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| no pair filter | greedy | 17 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| pair filter | nearest | 19 | 0.7916666666666666 | 0 | [1, 2, 12, 13, 14] |
| pair filter | greedy | 19 | 0.7916666666666666 | 0 | [1, 2, 12, 13, 14] |

Pair-level filtering improves coverage from 17/24 to 19/24, but it does not reach full coverage.

The newly covered target viewpoints are:

```text
[8, 20]
```

## Level 2 Join Comparison

Assignment-history rows joined against Level 2 pair-coverability:

| run | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |
| --- | ---: | ---: | ---: | ---: | ---: |
| no pair filter | 460 | 760 | 574 | 0 | 0 |
| pair filter | 994 | 0 | 574 | 226 | 0 |

Target-only counts:

| run | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |
| --- | ---: | ---: | ---: | ---: | ---: |
| no pair filter | 460 | 760 | 0 | 0 | 0 |
| pair filter | 994 | 0 | 0 | 0 | 0 |

Pair filtering removes all assignments to known Level-2-failing target pairs in this run.

## Target Assignment Counts

Per-method counts are identical for nearest and greedy within each run.

| run | method | v1 | v2 | v8 | v12 | v13 | v14 | v20 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no pair filter | nearest | 167 | 0 | 0 | 253 | 190 | 0 | 0 |
| no pair filter | greedy | 167 | 0 | 0 | 253 | 190 | 0 | 0 |
| pair filter | nearest | 190 | 0 | 9 | 253 | 0 | 0 | 45 |
| pair filter | greedy | 190 | 0 | 9 | 253 | 0 | 0 | 45 |

Previously skipped viewpoints:

- `8` is now assigned and covered.
- `20` is now assigned and covered.
- `2` is still never assigned.
- `14` is still never assigned.

Newly skipped target:

- `13` was assigned in the control run but is never assigned after filtering.

## Final Stuck Pattern

Control:

```text
robot_0 -> viewpoint_12: known_level2_failing_pair
robot_1 -> viewpoint_13: known_coverable_pair
robot_2 -> viewpoint_1: known_level2_failing_pair
```

Pair-filtered:

```text
robot_0 -> noop
robot_1 -> viewpoint_1: known_coverable_pair
robot_2 -> viewpoint_12: known_coverable_pair
```

The final stuck pattern changes substantially. Pair filtering removes the known failing stuck pairs, but the run still
times out while repeatedly assigning known-coverable pairs that do not convert into coverage in the multi-agent episode.

## Answers

1. Does pair-level filtering improve nearest/greedy coverage?

Yes. Both nearest and greedy improve from 17/24 to 19/24.

2. Does it reduce assignments to known Level-2-failing pairs?

Yes. Known Level-2-failing target assignments drop from 760 to 0.

3. Are previously skipped viewpoints 2 / 8 / 14 / 20 assigned after filtering?

Partially. Viewpoints `8` and `20` are assigned and covered. Viewpoints `2` and `14` are still never assigned.

4. Does the final stuck pattern change?

Yes. The filtered run ends with one no-op and two known-coverable stuck pairs: `robot_1 -> viewpoint_1` and
`robot_2 -> viewpoint_12`.

5. Is pair-level controller-aware feasibility a promising next direction?

Yes, as a controlled evaluator/baseline option. It removes known failing pair assignments and improves coverage. It is
not sufficient by itself and should not be promoted to a permanent environment default from this temporary CSV alone.

6. What remains unresolved?

- Full coverage is still not reached.
- `2`, `13`, and `14` are never assigned after filtering.
- `1` and `12` are repeatedly assigned to known-coverable agents but still not covered in the multi-agent episode.
- Filtered run no-op rate rises to about `0.126`, with `robot_0` ending on no-op.

7. What is the recommended next step?

Run a controlled assignment-history-aware retry/fallback or coverage-aware baseline on top of the pair-filter mode. The
next experiment should keep the same diagnostics and check whether it can avoid repeatedly holding known-coverable pairs
that are not producing coverage, while also surfacing still-skipped viewpoints such as `2`, `13`, and `14`.

If that still times out on known-coverable pairs, the next diagnostic should focus on controller state, target switching,
and multi-agent context for `robot_1 -> viewpoint_1` and `robot_2 -> viewpoint_12`.
