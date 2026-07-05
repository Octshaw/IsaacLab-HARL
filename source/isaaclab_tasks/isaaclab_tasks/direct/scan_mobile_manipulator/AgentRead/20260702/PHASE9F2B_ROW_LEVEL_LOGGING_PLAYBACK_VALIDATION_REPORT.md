# Phase 9F-2B Row-Level Logging Playback Validation Report

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-2B is a minimal playback-only validation of the Phase 9F-2A row-level logging fields.

This phase did not train. It did not implement conflict-aware redirect, active-task lifecycle, reward changes, observation changes, action-shape/action-semantics changes, environment dynamics changes, controller changes, HARL changes, baseline solver changes, cooldown behavior changes, scenario YAML behavior changes, or installed `site-packages` changes.

One short headless playback was run only to generate a new `assignment_history.csv` and validate that the new row-level diagnostic fields are emitted, parseable, and semantically reasonable.

No commit was made.

## 2. Playback Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 5 --output_dir results/assignment_diagnostics/phase9f2b_row_level_logging_validation --stop_on_done
```

Checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
```

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
```

Output directory:

```text
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/
```

## 3. Generated Playback Outputs

```text
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/assignment_history.csv
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/diagnostics.json
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/per_episode.csv
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/summary.csv
```

Generated history size:

```text
assignment_history.csv rows = 15
assignment_history.csv columns = 61
episodes = 1
steps = 5
robots = 3
```

## 4. Schema Validation

Schema validation output:

```text
results/assignment_diagnostics/phase9f2b_row_level_logging_validation/phase9f2b_schema_validation_summary.json
```

Required new columns all exist:

```text
robot_base_post_x
robot_base_post_y
selected_target_conflict_pair_count
selected_target_conflict_pairs
selected_target_min_distance_to_other_selected
selected_target_conflict_threshold
same_step_claimed_target_count
same_step_claimed_target_robot_ids
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
inter_robot_overlap_pair_count
inter_robot_overlap_pairs
inter_robot_min_base_distance
inter_robot_overlap_threshold
inter_robot_path_crossing_pair_count
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pair_count
inter_robot_path_near_miss_pairs
inter_robot_path_near_miss_threshold
```

Validation summary:

```text
required_new_columns_exist = true
pre_step_base_columns_exist = true
numeric_validation_passed = true
count_nonnegative_validation_passed = true
threshold_positive_validation_passed = true
json_list_parse_validation_passed = true
step_level_repeated_consistency_passed = true
validation_passed = true
```

## 5. Semantic Validation

`robot_base_x` and `robot_base_y` still exist and therefore preserve the pre-step base-position history interface.

`robot_base_post_x` and `robot_base_post_y` are present and numeric.

Count fields are numeric and non-negative:

```text
selected_target_conflict_pair_count
same_step_claimed_target_count
same_step_nearby_claimed_target_count
inter_robot_overlap_pair_count
inter_robot_path_crossing_pair_count
inter_robot_path_near_miss_pair_count
```

Threshold fields are numeric and positive:

```text
selected_target_conflict_threshold
inter_robot_overlap_threshold
inter_robot_path_near_miss_threshold
```

Pair-list fields are parseable JSON lists:

```text
selected_target_conflict_pairs
same_step_claimed_target_robot_ids
same_step_nearby_claimed_target_robot_ids
inter_robot_overlap_pairs
inter_robot_path_crossing_pairs
inter_robot_path_near_miss_pairs
```

Step/env-level repeated fields are consistent across robot rows for each `(episode, env_id, step)`.

Per-robot fields can differ by robot row; differences were observed for:

```text
inter_robot_min_base_distance
robot_base_post_x
robot_base_post_y
same_step_nearby_claimed_target_count
same_step_nearby_claimed_target_robot_ids
selected_target_min_distance_to_other_selected
```

## 6. Budget Trigger Result

The five-step validation run had:

```text
budget_trigger_row_count = 0
```

This is not a failure. Phase 9F-2B validates schema and row-level logging emission, not budget-trigger attribution or policy performance.

Because the minimal run had no budget triggers, the Phase 9F-1 attribution analyzer was not run against this new output as a trigger-window analysis. Old-history backward compatibility was still checked separately.

## 7. Backward Compatibility

The existing Phase 9F-1 analyzer was rerun on the old Phase 9E-4B histories:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/analyze_phase9f1_post_budget_conflicts.py
```

Result:

```text
passed
classification = DIAG-P
```

This confirms the schema inventory remains backward-compatible with old histories that do not have the Phase 9F-2A fields.

## 8. Validation Commands

Playback:

```text
minimal Phase 9F-2B playback command: passed
```

Schema validation:

```text
inline Python CSV validation command: passed
summary written to results/assignment_diagnostics/phase9f2b_row_level_logging_validation/phase9f2b_schema_validation_summary.json
```

Python compile:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f1_post_budget_conflicts.py
result: passed
```

Final git validation:

```text
git diff --check
result: passed
note: emitted LF/CRLF warnings for evaluate_assignment_rl_playback_diagnostics.py and TASK_PROGRESS.md only

git status --short --untracked-files=all
result:
  M scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? scripts/environments/analyze_phase9f1_post_budget_conflicts.py
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F1_POST_BUDGET_REDIRECT_CONFLICT_DIAGNOSTICS_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2B_ROW_LEVEL_LOGGING_PLAYBACK_VALIDATION_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F1_CONFLICT_DIAGNOSTICS_20260702.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_20260702.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F2B_ROW_LEVEL_LOGGING_PLAYBACK_VALIDATION_20260702.md
```

## 9. Limitations

```text
The validation run is intentionally short: one episode, five steps, one checkpoint.
It is not a performance evaluation.
It produced no budget triggers.
It does not prove conflict attribution quality in late-trigger windows.
The path-crossing fields remain observed straight pre/post base segment proxies, not true planner-internal paths.
```

## 10. Recommendation

Phase 9F-2B validates that the new row-level fields are emitted and parseable.

Recommended next phase:

```text
Phase 9F-2C or Phase 9F-3 design decision:
  Use a longer playback only if explicit trigger-window attribution with the new fields is needed.
  Otherwise proceed to a design-only decision for claimed-target / spacing-aware redirect versus active-task lifecycle.
```

Do not treat the five-step run as policy-performance evidence.
