# Phase 9F-2C Trigger-Window Row-Level Validation Report

Date: 2026-07-02

## 1. Scope and Boundaries

Phase 9F-2C is diagnostic-only.

One limited playback-only run was executed to generate a new `assignment_history.csv` containing both Phase 9F-2A row-level conflict fields and budget trigger rows. No training was run.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, controller behavior, HARL code, baseline solvers, cooldown trigger/mask behavior, scenario YAML behavior, conflict-aware redirect logic, active-task lifecycle logic, or installed `site-packages` were changed.

No commit was made.

## 2. Playback Command

Prior Phase 9F-1 trigger-window output showed the first `models + budget` trigger at step 240, with later triggers around 256, 271, 272, 288, and 289. Because of that, `--max_steps 160` was likely insufficient. Phase 9F-2C used one limited 300-step playback.

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation --stop_on_done
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
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/
```

The run stopped at step 299 with `--stop_on_done`.

## 3. Generated Outputs

Playback outputs:

```text
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/diagnostics.json
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/per_episode.csv
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/summary.csv
```

Phase 9F-2C analyzer outputs:

```text
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/phase9f2c_schema_validation_summary.json
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/phase9f2c_trigger_window_attribution.csv
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/phase9f2c_trigger_window_summary.json
```

Generated history size:

```text
assignment_history.csv rows = 897
assignment_history.csv columns = 61
episodes = 1
envs = 1
robots = 3
steps = 299
budget_trigger_row_count = 6
```

## 4. Schema Validation

All Phase 9F-2A fields appeared in the generated CSV:

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
budget_triggered_by_budget_exists = true
numeric_validation_passed = true
count_nonnegative_validation_passed = true
threshold_positive_validation_passed = true
json_list_parse_validation_passed = true
step_level_repeated_consistency_passed = true
validation_passed = true
```

## 5. Trigger-Window Attribution

Budget triggers:

```text
trigger_count = 6
trigger_pairs = r1->36: 4, r2->44: 2
```

Next non-noop selections after each trigger:

| Trigger step | Trigger pair | Next step | Next target | Exact duplicate direct | Nearby target direct | Overlap direct | Path crossing direct | Near-miss direct | Return step |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 240 | r1->36 | 241 | 44 | 1 | 0 | 1 | 0 | 1 | 246 |
| 256 | r1->36 | 257 | 44 | 1 | 1 | 1 | 0 | 1 | 262 |
| 271 | r2->44 | 272 | 24 | 1 | 1 | 1 | 0 | 1 | 277 |
| 272 | r1->36 | 273 | 44 | 0 | 2 | 1 | 0 | 1 | 278 |
| 288 | r1->36 | 289 | 44 | 1 | 1 | 1 | 0 | 1 | 294 |
| 289 | r2->44 | 290 | 24 | 0 | 1 | 1 | 1 | 0 | 295 |

Aggregate direct-field attribution:

```text
next_exact_duplicate_direct_count = 4 / 6
next_nearby_selected_target_direct_count = 5 / 6
next_inter_robot_overlap_direct_count = 6 / 6
next_path_crossing_direct_count = 1 / 6
next_path_near_miss_direct_count = 5 / 6
coverage_gain_within_20_count = 0 / 6
return_to_triggered_pair_after_cooldown_count = 6 / 6
```

Twenty-step trigger-window direct-field totals, counted per trigger window:

```text
direct_exact_duplicate_step_count_20_total = 32
direct_nearby_selected_target_step_count_20_total = 94
direct_inter_robot_overlap_step_count_20_total = 99
direct_path_crossing_step_count_20_total = 11
direct_path_near_miss_step_count_20_total = 90
```

These window totals count overlapping trigger windows separately.

## 6. Direct Fields vs Old Reconstructed Proxies

The new direct fields agreed with the old selected-target reconstruction on every trigger next-step row:

```text
exact_direct_reconstructed_mismatch_count = 0
nearby_direct_reconstructed_mismatch_count = 0
selected_target_pair_count_direct_reconstructed_mismatch_count = 0
```

Interpretation:

```text
The new row-level selected-target fields preserve the Phase 9F-1 exact/nearby attribution while making it direct and cheaper to consume.
The new row-level inter-robot overlap and path proxy fields add attribution that old histories could not provide.
```

## 7. Diagnostic Interpretation

Phase 9F-2C confirms that budget-trigger windows can now be attributed with direct row-level fields.

This one-episode validation reproduces the Phase 9F-1 pattern for `models + budget`:

```text
exact duplicate redirects are present
nearby selected-target conflicts are present
row-level inter-robot overlap is present at every next redirected step
observed base-segment path near-misses are common
one next redirected step has an observed base-segment crossing proxy
coverage gain within 20 steps after trigger is absent
return to the triggered pair after cooldown is universal in this run
```

This remains diagnostic evidence only. It is not policy-performance evidence and should not be interpreted as a broad evaluation sweep.

## 8. Limitations

```text
single episode
single checkpoint directory
one limited playback, not a sweep
20-step windows overlap for closely spaced triggers
path crossing / near-miss remains an observed straight pre/post base segment proxy, not a planner-internal path
coverage-gain attribution is global per step, not proof that the redirected target itself was completed
```

## 9. Recommendation

Recommended next phase:

```text
Phase 9F-3 design decision.
Use the validated direct row-level fields to choose between claimed-target / spacing-aware redirect diagnostics and active-task lifecycle design.
Do not implement a mechanism until the next phase explicitly authorizes it.
```

The repeated return-to-triggered-pair result still points toward an active-task lifecycle or explicit failed-target state as a likely necessary companion to any local claimed-target or spacing-aware redirect mechanism.

## 10. Validation

Playback:

```text
Phase 9F-2C one limited playback command
result: passed
```

Schema and trigger attribution:

```text
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation
result: passed
validation_passed = true
budget_trigger_row_count = 6
trigger_attribution_rows = 6
```

Python compile and final git validation are recorded in `TASK_PROGRESS.md`.
