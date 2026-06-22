# Stage 4B Real Component N24 Pair-Filter + Retry/Fallback Report

Date: 2026-06-15

## Scope

This is a diagnostic-only evaluator baseline experiment. It does not train assignment-RL, modify HARL core, change reward, change controller math, edit `assignment_controller.py`, alter the 9D action path, modify default environment feasibility, add retry/fallback as default behavior, add real robot articulation, IK, collision, or raycast coverage.

`real_component_bbox_sample.csv` remains temporary pipeline sanity data, not final viewpoint planning output.

## Pre-Task Cleanup

The filtered assignment-Level2 join report was corrected:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_JOIN_REPORT.md
```

The corrected interpretation is that the pair-filtered run has `known_level2_failing_pair = 0`; remaining failures are known-coverable pairs that stall in the full baseline episode plus skipped target viewpoints.

## Implementation Summary

`scripts/environments/evaluate_assignment_methods.py` now supports evaluator-only retry/fallback diagnostics:

```text
--assignment_retry_fallback
--assignment_stall_window 30
--assignment_pair_cooldown 60
```

The policy is:

```text
retry_fallback_policy = consecutive_same_pair_no_coverage_gain
```

For each env/agent, if the same non-noop, not-yet-covered viewpoint is assigned for `assignment_stall_window` consecutive steps without coverage gain, that env/agent/viewpoint pair is blocked for `assignment_pair_cooldown` evaluator steps. The cooldown affects only the evaluator baseline solver candidate mask.

This mode remains compatible with:

```text
--level2_pair_filter_json results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json
--viewpoint_candidate_top_k -1
--write_assignment_history
```

## Output Artifacts

Pair-filter control:

```text
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/assignment_history.csv
```

Pair-filter + retry/fallback:

```text
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/retry_fallback_events.csv
```

Retry/fallback Level2 join:

```text
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_level2_join/assignment_history_joined.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_level2_join/assignment_history_pair_summary.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_JOIN_REPORT.md
```

## Coverage Comparison

| run | method | final_covered_count | final_coverage | success | final_uncovered_viewpoint_ids | noop_rate |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| pair-filter control | nearest | 19/24 | 0.791667 | 0 | [1, 2, 12, 13, 14] | 0.125975 |
| pair-filter control | greedy | 19/24 | 0.791667 | 0 | [1, 2, 12, 13, 14] | 0.125975 |
| pair-filter + retry/fallback | nearest | 19/24 | 0.791667 | 0 | [1, 2, 12, 13, 14] | 0.185061 |
| pair-filter + retry/fallback | greedy | 19/24 | 0.791667 | 0 | [1, 2, 12, 13, 14] | 0.185061 |

Retry/fallback does not improve coverage beyond the pair-filter-only result.

## Target Assignment Counts

Target ids:

```text
[1, 2, 8, 12, 13, 14, 20]
```

Pair-filter control, per method:

| viewpoint | assignment_count |
| ---: | ---: |
| 1 | 190 |
| 2 | 0 |
| 8 | 9 |
| 12 | 253 |
| 13 | 0 |
| 14 | 0 |
| 20 | 45 |

Never assigned in control:

```text
[2, 13, 14]
```

Pair-filter + retry/fallback, per method:

| viewpoint | assignment_count |
| ---: | ---: |
| 1 | 61 |
| 2 | 30 |
| 8 | 15 |
| 12 | 155 |
| 13 | 45 |
| 14 | 54 |
| 20 | 84 |

Never assigned in retry/fallback:

```text
[]
```

Retry/fallback changes the assignment behavior: previously skipped target viewpoints `2`, `13`, and `14` are now assigned. However, they are still not covered by the end of the episode.

## Cooldown Diagnostics

Retry/fallback diagnostics:

```text
num_cooldown_events_total = 16
cooldown_events_by_method = {"nearest": 8, "greedy": 8}
```

Cooldown events by pair:

| pair | cooldown_events |
| --- | ---: |
| agent_0 -> viewpoint_20 | 2 |
| agent_1 -> viewpoint_1 | 2 |
| agent_2 -> viewpoint_12 | 4 |
| agent_1 -> viewpoint_13 | 2 |
| agent_2 -> viewpoint_20 | 2 |
| agent_1 -> viewpoint_14 | 2 |
| agent_1 -> viewpoint_2 | 2 |

The known-coverable stuck pairs from the filtered run were cooled down:

```text
robot_1 -> viewpoint_1
robot_2 -> viewpoint_12
```

`robot_2 -> viewpoint_12` cooled down twice per method. The final active cooldowns include `agent_1 -> viewpoint_2`, `agent_1 -> viewpoint_14`, and `agent_2 -> viewpoint_12` for both nearest and greedy.

## Final Stuck Pattern

Pair-filter control final pattern, per method:

```text
robot_0 -> noop
robot_1 -> viewpoint_1
robot_2 -> viewpoint_12
```

Pair-filter + retry/fallback final pattern, per method:

```text
robot_0 -> noop
robot_1 -> viewpoint_1
robot_2 -> noop
```

The stuck pattern changes, but full coverage is still not reached. At timeout, `robot_1 -> viewpoint_1` has only rebuilt an 8-step stall streak, so it has not reached the 30-step cooldown window again.

## Level2 Join Result

Retry/fallback Level2 join summary:

```text
known_coverable_pair = 888
known_level2_failing_pair = 0
unchecked_pair = 574
noop = 332
already_covered = 0
```

Target-only summary:

```text
known_coverable_pair = 888
known_level2_failing_pair = 0
unchecked_pair = 0
noop = 0
already_covered = 0
```

The remaining target assignments are not known Level-2-failing pairs. They are known-coverable pairs that do not produce coverage in this full multi-agent baseline rollout.

## Questions Answered

1. Does retry/fallback improve coverage beyond pair-filter only?

No. Coverage remains `19/24` for both nearest and greedy.

2. Does it reduce repeated known-coverable stuck assignments?

Partially. It reduces assignments to `viewpoint_1` and `viewpoint_12`, and it triggers cooldown for the previous stuck pairs. However, the episode still times out with `robot_1 -> viewpoint_1` and remaining active cooldowns.

3. Are previously skipped viewpoints `[2, 13, 14]` assigned?

Yes. They are no longer skipped. Per method, retry/fallback assigns `viewpoint_2` 30 times, `viewpoint_13` 45 times, and `viewpoint_14` 54 times.

4. Does the final stuck pattern change?

Yes. It changes from:

```text
robot_0 -> noop
robot_1 -> viewpoint_1
robot_2 -> viewpoint_12
```

to:

```text
robot_0 -> noop
robot_1 -> viewpoint_1
robot_2 -> noop
```

5. Does no-op increase or decrease?

No-op increases from `0.125975` to `0.185061`. This is expected because cooldown can temporarily remove stalled candidate pairs.

6. Is retry/fallback a promising next direction?

It is useful diagnostically because it proves skipped viewpoints can be forced into the assignment sequence without changing controller or reward. However, this simple consecutive-stall cooldown is not sufficient to improve final coverage.

7. What remains unresolved?

The remaining issue is no longer explained by candidate visibility, static Level-2 failing pairs, or never-assigned target viewpoints. The unresolved behavior is that known-coverable target pairs can be assigned and cooled down in the full episode but still fail to satisfy coverage before timeout.

8. Recommended next step.

Run a targeted controller-state / target-switching diagnostic for known-coverable pairs in the full multi-agent evaluator context, especially:

```text
robot_1 -> viewpoint_1
robot_2 -> viewpoint_12
robot_1 -> viewpoint_2
robot_1 -> viewpoint_14
```

The diagnostic should compare Level 2 single-pair success against full-episode state when the pair is assigned, including current base pose, end-effector pose, position/rotation/range/FOV gates, and whether repeated target switching or cooldown-induced no-op changes the controller state enough to prevent gate satisfaction.
