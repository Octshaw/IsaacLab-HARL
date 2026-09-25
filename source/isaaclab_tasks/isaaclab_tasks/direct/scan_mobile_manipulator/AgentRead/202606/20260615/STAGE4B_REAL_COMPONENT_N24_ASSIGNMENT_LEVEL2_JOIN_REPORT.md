# Stage 4B Real Component N24 Assignment-Level2 Join Report

Date: 2026-06-15

## Scope

This is a diagnostic-only join between evaluator assignment history and Level 2 pair-coverability results. It does not change random/nearest/greedy behavior, controller behavior, reward logic, HARL core, the 9D action path, assignment-RL, pair-level filtering, retry/fallback logic, IK, collision, raycast, or robot articulation.

`real_component_bbox_sample.csv` remains temporary pipeline sanity data, not final viewpoint planning output.

## Source Artifacts

```text
assignment_history_csv: results\assignment_evaluation\stage4b_real_component_n24_assignment_history_check\assignment_history.csv
level2_json: results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json
assignment_history_joined_csv: results\assignment_evaluation\stage4b_real_component_n24_assignment_level2_join\assignment_history_joined.csv
assignment_history_pair_summary_csv: results\assignment_evaluation\stage4b_real_component_n24_assignment_level2_join\assignment_history_pair_summary.csv
```

## Overall Assignment Status Counts

- known_coverable_pair: 460
- known_level2_failing_pair: 760
- unchecked_pair: 574
- noop: 0
- already_covered: 0

By method:

| method | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |
| --- | ---: | ---: | ---: | ---: | ---: |
| greedy | 230 | 380 | 287 | 0 | 0 |
| nearest | 230 | 380 | 287 | 0 | 0 |

Note: `unchecked_pair` mostly covers non-target viewpoints because the Level 2 diagnostic JSON was generated only for target ids `[1, 2, 8, 12, 13, 14, 20]`.

## Target-Only Assignment Status Counts

- known_coverable_pair: 460
- known_level2_failing_pair: 760
- unchecked_pair: 0
- noop: 0
- already_covered: 0

By method, target ids only:

| method | known_coverable_pair | known_level2_failing_pair | unchecked_pair | noop | already_covered |
| --- | ---: | ---: | ---: | ---: | ---: |
| greedy | 230 | 380 | 0 | 0 | 0 |
| nearest | 230 | 380 | 0 | 0 | 0 |

## Target Viewpoint Summary

| viewpoint | assigned_count | assigned_agents | assigned_to_coverable_agent_count | assigned_to_failing_agent_count | any_assignment_covered_after | interpretation |
| ---: | ---: | --- | ---: | ---: | ---: | --- |
| 1 | 334 | [2] | 0 | 334 | false | repeatedly assigned but not covered |
| 2 | 0 | [] | 0 | 0 | false | never assigned |
| 8 | 0 | [] | 0 | 0 | false | never assigned |
| 12 | 506 | [0, 1, 2] | 126 | 380 | false | repeatedly assigned but not covered |
| 13 | 380 | [1, 2] | 334 | 46 | false | repeatedly assigned but not covered |
| 14 | 0 | [] | 0 | 0 | false | never assigned |
| 20 | 0 | [] | 0 | 0 | false | never assigned |

Never assigned ids: `[2, 8, 14, 20]`

Repeatedly assigned but not covered ids: `[1, 12, 13]`

## Final Stuck Pattern

| method | agent | assigned_viewpoint | pair_level2_status | level2_failure_reason |
| --- | ---: | ---: | --- | --- |
| greedy | 0 | 12 | known_level2_failing_pair | position_rotation_gates_never_simultaneously_satisfied |
| greedy | 1 | 13 | known_coverable_pair | covered |
| greedy | 2 | 1 | known_level2_failing_pair | position_rotation_gates_never_simultaneously_satisfied |
| nearest | 0 | 12 | known_level2_failing_pair | position_rotation_gates_never_simultaneously_satisfied |
| nearest | 1 | 13 | known_coverable_pair | covered |
| nearest | 2 | 1 | known_level2_failing_pair | position_rotation_gates_never_simultaneously_satisfied |

The requested stuck pattern is therefore:

```text
robot_0 -> viewpoint_12: known_level2_failing_pair
robot_1 -> viewpoint_13: known_coverable_pair
robot_2 -> viewpoint_1: known_level2_failing_pair
```

Nearest and greedy have the same final stuck pattern in this run.

## Diagnostic Answers

1. Are nearest/greedy mostly stuck because they assign Level-2-failing pairs?

For target assignments, yes: known Level-2-failing assignments outnumber known-coverable assignments. The final stuck pattern includes two known failing pairs and one known coverable pair per method.

2. Are they skipping coverable viewpoints entirely?

Yes. The never-assigned target ids are `[2, 8, 14, 20]`. Level 2 previously showed these viewpoints are coverable by at least one robot.

3. Do they repeatedly assign known-coverable pairs that still fail in multi-agent context?

Yes. The target summary includes known-coverable assignments that do not produce coverage in the multi-agent baseline episode, especially the stuck `robot_1 -> viewpoint_13` pair and repeated `robot_2 -> viewpoint_12` assignments before the final step.

4. Which next fix is most justified?

pair-level feasibility filtering is the most justified next step, because target assignments are dominated by known Level-2-failing pairs. Keep this as a controlled behavior change and re-run the same diagnostics.

## Recommendation

Primary recommendation: pair-level feasibility filtering. The join shows many repeated target assignments are to known Level-2-failing agent-viewpoint pairs, including two of the three final stuck pairs per method. This should be tested as a controlled behavior change, then followed by the same assignment-history diagnostics.

Residual risk: filtering alone may not solve skipped viewpoints `2 / 8 / 14 / 20` or known-coverable pairs that still fail in multi-agent context. If coverage remains at 17/24 after filtering, the next diagnostic should focus on retry/fallback sequencing and controller-state/target-switching behavior.
