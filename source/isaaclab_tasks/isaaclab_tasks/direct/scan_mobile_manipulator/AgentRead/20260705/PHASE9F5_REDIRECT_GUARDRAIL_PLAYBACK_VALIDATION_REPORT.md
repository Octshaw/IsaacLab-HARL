# Phase 9F-5 Redirect Guardrail Playback Validation Report

Date: 2026-07-05

## 1. Scope and Boundaries

Phase 9F-5 ran one limited playback-only validation with the Phase 9F-4B redirect guardrail explicitly enabled.

No training was run. No broad playback sweep was run. No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, environment dynamics, controller behavior, HARL code, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, path-crossing-aware redirect, active-task lifecycle, installed `site-packages`, or default scenario behavior were changed.

The guardrail remains disabled by default. This phase created one debug-only scenario YAML to enable it for validation.

## 2. Files Changed or Created

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F5_GUARDRAIL_PLAYBACK_VALIDATION_20260705.md
```

Generated outputs:

```text
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/diagnostics.json
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/per_episode.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/summary.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/phase9f5_schema_validation_summary.json
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/phase9f5_trigger_window_attribution.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/phase9f5_reference_comparison.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/phase9f5_redirect_guardrail_validation_summary.json
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## 3. Guardrail-Enabled Scenario

Scenario path:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

The scenario copies the Phase 9E/9F budget scenario and adds only this guardrail block:

```yaml
assignment_redirect_guardrail:
  enabled: true
  apply_context: recent_budget_trigger
  window_steps: 1
  claimed_target_enabled: true
  spacing_enabled: true
  spacing_threshold: null
  fail_open_spacing: true
  fail_open_claimed: true
  log_diagnostics: true
```

The original budget scenario was not modified.

## 4. Playback Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9f5_redirect_guardrail_validation --stop_on_done
```

Result: passed. The run completed one episode at step 299 and wrote diagnostics to:

```text
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/
```

## 5. Schema Validation

Generated `assignment_history.csv`:

```text
rows = 897
columns = 71
budget_trigger_row_count = 6
```

Schema result:

```text
required Phase 9F-2A columns exist = true
required Phase 9F-4B guardrail columns exist = true
numeric_validation_passed = true
count_nonnegative_validation_passed = true
threshold_positive_validation_passed = true
json_list_parse_validation_passed = true
step_level_repeated_consistency_passed = true
guardrail_active_threshold_positive_validation_passed = true
guardrail_inactive_default_validation_passed = true
noop_when_available_reported = true
validation_passed = true
```

`available_actions` shape is not logged in `assignment_history.csv`, so the analyzer reports `available_actions_shape_validation = not_logged`. The playback reset log reported the expected shape `(1, 3, 51)`.

## 6. Guardrail Activation and Suppression

```text
redirect_guardrail_active_row_count = 6
guardrail_active_trigger_count = 6
active_rows_with_suppression_count = 6
claimed_target_suppression_total = 12
spacing_suppression_total = 74
fail_open_count = 0
overmask_count = 0
only_noop_remaining_count = 0
active_threshold_min = 0.8500000238418579
active_threshold_max = 0.8500000238418579
```

Interpretation:

```text
The guardrail activated exactly on the six post-trigger next-decision rows.
Each active row suppressed at least one candidate.
No fail-open, over-mask, or only-noop cases occurred in this limited playback.
The derived threshold matched the expected 0.85 m Phase 9E/9F budget-scenario value.
```

## 7. Trigger-Window Attribution

Enabled Phase 9F-5 trigger summary:

```text
trigger_count = 6
trigger_pairs = r1->36: 4, r2->44: 2
```

Next non-noop selections after each trigger:

| Trigger step | Trigger pair | Next step | Next target | Exact duplicate | Nearby selected target | Overlap | Path crossing | Near-miss | Claimed suppressed | Spacing suppressed | Return after cooldown |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 240 | r1->36 | 241 | 7 | 0 | 0 | 1 | 0 | 1 | 2 | 10 | true |
| 256 | r1->36 | 257 | 7 | 0 | 0 | 1 | 0 | 1 | 2 | 10 | true |
| 271 | r2->44 | 272 | 14 | 0 | 0 | 1 | 0 | 1 | 2 | 14 | true |
| 272 | r1->36 | 273 | 7 | 0 | 0 | 1 | 0 | 1 | 2 | 13 | true |
| 287 | r2->44 | 288 | 14 | 0 | 0 | 1 | 0 | 1 | 2 | 14 | true |
| 288 | r1->36 | 289 | 7 | 0 | 0 | 1 | 0 | 1 | 2 | 13 | true |

Aggregate enabled attribution:

```text
next_exact_duplicate_direct_count = 0 / 6
next_nearby_selected_target_direct_count = 0 / 6
next_inter_robot_overlap_direct_count = 6 / 6
next_path_crossing_direct_count = 0 / 6
next_path_near_miss_direct_count = 6 / 6
coverage_gain_within_20_count = 0 / 6
return_to_triggered_pair_after_cooldown_count = 6 / 6
```

The enabled playback kept the same trigger count and trigger-pair distribution as Phase 9F-2C, but one r2 trigger shifted in step timing. Metrics are compared by normalized rate rather than one-to-one trigger matching.

## 8. Comparison Against Phase 9F-2C Disabled Reference

Phase 9F-2C disabled reference:

```text
rows = 897
columns = 61
budget_trigger_row_count = 6
trigger_pairs = r1->36: 4, r2->44: 2
```

Normalized comparison:

| Metric | 9F-5 enabled | 9F-2C disabled | Delta |
| --- | ---: | ---: | ---: |
| next exact duplicate rate | 0.000000 | 0.666667 | -0.666667 |
| next nearby selected-target rate | 0.000000 | 0.833333 | -0.833333 |
| next inter-robot overlap rate | 1.000000 | 1.000000 | 0.000000 |
| next path crossing rate | 0.000000 | 0.166667 | -0.166667 |
| next path near-miss rate | 1.000000 | 0.833333 | +0.166667 |
| coverage gain within 20 rate | 0.000000 | 0.000000 | 0.000000 |
| return to triggered pair after cooldown rate | 1.000000 | 1.000000 | 0.000000 |

Interpretation:

```text
The local guardrail removed the exact duplicate and nearby selected-target next-redirect conflicts in this limited playback.
It did not reduce row-level inter-robot overlap.
It removed the one direct crossing proxy instance, but near-miss proxy rate increased from 5/6 to 6/6.
It did not create coverage gain within 20 steps.
It did not reduce return-to-triggered-pair after cooldown.
```

## 9. Coverage and Noop Summary

| Metric | 9F-5 enabled | 9F-2C disabled | Delta |
| --- | ---: | ---: | ---: |
| final_coverage_ratio | 0.500000 | 0.500000 | 0.000000 |
| coverage_auc | 0.330435 | 0.330435 | 0.000000 |
| noop_when_available_rate | 0.000000 | 0.000000 | 0.000000 |
| noop_action_rate | 0.000000 | 0.000000 | 0.000000 |

The limited validation did not show coverage loss or added noop pressure.

## 10. Limitations

```text
This is one episode, one checkpoint, one limited playback.
This is guardrail behavior evidence, not a final performance claim.
The guardrail is local to recent budget-trigger redirect windows.
Same-step simultaneous new claims are not solved.
Path-crossing-aware redirect is not implemented.
Active-task lifecycle is not implemented.
Return-to-triggered-pair remains 6/6 and is not expected to be solved by this local guardrail.
Coverage gain is global per step, not proof that the redirected target itself was completed.
The path crossing / near-miss fields remain straight pre/post base-segment proxies, not planner-internal paths.
```

## 11. Classification

```text
classification = GUARDRAIL-P
```

Rationale:

```text
Exact duplicate next-redirect conflict decreased from 4/6 to 0/6.
Nearby selected-target next-redirect conflict decreased from 5/6 to 0/6.
Final coverage ratio, coverage AUC, noop_when_available, and noop_action rate remained unchanged in this limited run.
No fail-open, over-mask, or only-noop cases occurred.
```

This classification is limited to the Phase 9F-5 validation scope and should not be read as a broad policy-performance claim.

## 12. Recommendation

Proceed to a small Phase 9F-6 review or playback-validation decision point:

```text
Option 1: run a slightly broader playback-only validation if explicitly authorized, still no training;
Option 2: prepare a commit discussion for the disabled-by-default guardrail plus diagnostics;
Option 3: start Phase 9G-0 active-task lifecycle / failed-target-state design, because return-to-triggered-pair remains unchanged.
```

Do not train from this result alone. Do not treat the local guardrail as the lifecycle solution.

## 13. Validation Commands and Results

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
```

Result: passed.

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9f5_redirect_guardrail_validation --stop_on_done
```

Result: passed.

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9f5_redirect_guardrail_validation
```

Result: passed.

```powershell
git diff --check
```

Result: passed, with LF-to-CRLF working-copy warnings only for existing touched files.
