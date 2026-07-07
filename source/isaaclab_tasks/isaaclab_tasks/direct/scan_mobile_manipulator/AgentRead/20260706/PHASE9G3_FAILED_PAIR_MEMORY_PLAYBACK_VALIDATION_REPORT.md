# Phase 9G-3 Failed-Pair Memory Playback Validation Report

Date: 2026-07-06

## Scope And Boundary

Phase 9G-3 ran playback-only validation for the Phase 9G-2 disabled-by-default wrapper-local failed-pair/release-memory guardrail.

This phase did not run training. It did not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, installed packages, cooldown tuning, Phase 9F redirect guardrail tuning, or env-level lifecycle behavior.

The only source code change made during Phase 9G-3 was diagnostic-only playback logging plus an offline comparison helper. No env or wrapper behavior was changed.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
scripts/environments/analyze_phase9f2c_trigger_windows.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv
```

## Files Created Or Updated

Updated:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Created:

```text
scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_20260706.md
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/configs/phase9g3_failed_pair_memory_enabled.json
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/
```

`evaluate_assignment_rl_playback_diagnostics.py` was updated only to expose existing failed-pair memory diagnostics in playback CSV/JSON outputs. This was required to validate the Phase 9G-2 mechanism and did not alter masks, policy inputs, rewards, actions, env dynamics, controller behavior, HARL, or baselines.

## Playback Setup

Checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
```

Default-disabled scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

Enabled run-local config:

```text
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/configs/phase9g3_failed_pair_memory_enabled.json
```

The enabled config preserved the Phase 9F-5 cooldown and redirect-guardrail setup and only enabled the Phase 9G-2 failed-pair memory fields:

```text
assignment_failed_pair_memory_enabled = True
assignment_failed_pair_memory_duration_steps = 5
assignment_failed_pair_memory_apply_to_action_mask = True
assignment_failed_pair_memory_source = "budget_trigger"
assignment_failed_pair_memory_fail_open = True
assignment_failed_pair_memory_clear_on_coverage = True
assignment_failed_pair_memory_log_diagnostics = True
```

Both playback runs used `num_episodes=1`, `max_steps=300`, `num_envs=1`, `device=cuda:0`, and `--stop_on_done`, matching the Phase 9F reference pattern.

## Exact Playback Commands

Phase 9G-3A default-disabled identity playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled --stop_on_done
```

Phase 9G-3B enabled failed-pair memory playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/configs/phase9g3_failed_pair_memory_enabled.json --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled --stop_on_done
```

Both commands completed one playback episode and wrote `assignment_history.csv`, `summary.csv`, `per_episode.csv`, and `diagnostics.json`. Isaac/Omni/Gym emitted expected runtime warnings, but the runs completed successfully.

## Offline Analyzer Commands

Lifecycle reconstruction across all comparison histories:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/lifecycle_all
```

Trigger-window analyzers:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/reference_phase9f2c_trigger_windows

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/reference_phase9f5_trigger_windows

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled_trigger_windows

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled_trigger_windows
```

Redirect-guardrail comparison analyzers:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled_vs_phase9f5_reference

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_enabled_vs_phase9f5_reference

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_enabled_vs_phase9f2c_reference
```

Phase 9G-3 offline comparison aggregation:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
```

Generated:

```text
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/phase9g3_comparison_table.csv
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/phase9g3_ttl_boundary_rows.csv
results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_comparison/phase9g3_comparison_summary.json
```

## Comparison Table

| run | final coverage | coverage auc | same-owner returns | teammate reacquires | gain after release | gain within 20 | noop action rate | noop when available | next exact duplicate | next nearby selected | next overlap | next crossing | next near miss | memory triggers | memory suppressed | fail-open | only-noop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reference_phase9f2c_disabled | 0.5 | 0.330434589 | 6 | 2 | 0 | 0 | 0.0 | 0.0 | 4 | 5 | 6 | 1 | 5 | 0 | 0 | 0 | 0 |
| reference_phase9f5_redirect_guardrail | 0.5 | 0.330434589 | 6 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0 |
| phase9g3_default_disabled | 0.5 | 0.330434589 | 6 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0 |
| phase9g3_failed_pair_memory_enabled | 0.5 | 0.330434589 | 6 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 6 | 0 | 0 | 0 |

## Default-Disabled Identity Result

Default-disabled behavior passed the identity check against the Phase 9F-5 redirect-guardrail reference at the measured playback/analyzer level.

Observed identity points:

```text
assignment_failed_pair_memory_enabled = False
available_actions_shape = [1, 3, 51]
failed_pair_memory_trigger_count = 0
failed_pair_memory_suppressed_count = 0
failed_pair_memory_fail_open_count = 0
failed_pair_memory_only_noop_remaining_count = 0
final_coverage_ratio = 0.5
coverage_auc = 0.33043458868428616
same_owner_returns = 6
coverage_gain_after_release_count = 0
coverage_gain_within_20_count = 0
noop_action_rate = 0.0
noop_when_available_rate = 0.0
next_exact_duplicate_direct_count = 0
next_nearby_selected_target_direct_count = 0
next_inter_robot_overlap_direct_count = 6
next_path_crossing_direct_count = 0
next_path_near_miss_direct_count = 6
```

## Enabled Failed-Pair Memory Result

The enabled guardrail triggered but did not suppress any selected/action-mask options in this playback.

Enabled diagnostics:

```text
assignment_failed_pair_memory.enabled = True
assignment_failed_pair_memory.duration_steps = 5
assignment_failed_pair_memory.source = budget_trigger
assignment_failed_pair_memory.apply_to_action_mask = True
assignment_failed_pair_memory.fail_open = True
assignment_failed_pair_memory.clear_on_coverage = True
assignment_failed_pair_memory.trigger_count = 6
assignment_failed_pair_memory.active_pair_step_total = 30
assignment_failed_pair_memory.active_step_count = 22
assignment_failed_pair_memory.active_count_mean = 0.10033444816053512
assignment_failed_pair_memory.suppressed_count = 0
assignment_failed_pair_memory.fail_open_count = 0
assignment_failed_pair_memory.only_noop_remaining_count = 0
assignment_failed_pair_memory.selected_pair_active_count = 0
assignment_failed_pair_memory.selected_pair_ttl_mean = 0
assignment_failed_pair_memory.selected_pair_ttl_max = 0
trigger_pairs = r1->36 x4, r2->44 x2
last_trigger_reason = budget_trigger
```

Enabled outcome:

```text
same_owner_returns: 6 -> 6
teammate_reacquires: 2 -> 2
coverage_gain_after_release_count: 0 -> 0
coverage_gain_within_20_count: 0 -> 0
final_coverage_ratio: 0.5 -> 0.5
coverage_auc: 0.33043458868428616 -> 0.33043458868428616
noop_action_rate: 0.0 -> 0.0
noop_when_available_rate: 0.0 -> 0.0
```

Interpretation: the mechanism activated from the budget trigger source, but the active memory window did not overlap the same-owner reacquisition step, so no mask suppression occurred.

## Same-Owner Return Analysis

The Phase 9G-1 lifecycle reconstruction analyzer reported identical repeated-return structure in both G3 playback histories:

```text
phase9g3_default_disabled:
  budget_failed_segments = 6
  released_segments = 6
  same_owner_returns = 6
  median_same_owner_return_delay_steps = 5

phase9g3_failed_pair_memory_enabled:
  budget_failed_segments = 6
  released_segments = 6
  same_owner_returns = 6
  median_same_owner_return_delay_steps = 5
```

The enabled guardrail therefore did not reduce return-to-triggered-pair in the tested configuration.

## Coverage-Gain Analysis

Coverage remained unchanged:

```text
coverage_gain_after_release_count = 0
coverage_gain_within_20_count = 0
final_coverage_ratio = 0.5
coverage_auc = 0.33043458868428616
```

The enabled memory produced no post-release coverage gain and no coverage gain within 20 steps.

## Noop, Fail-Open, And Overmask Analysis

No new noop pressure was observed:

```text
noop_action_rate = 0.0
noop_when_available_rate = 0.0
failed_pair_memory_fail_open_count = 0
failed_pair_memory_only_noop_remaining_count = 0
```

This should not be read as evidence that the mask is always safe under enabled memory. In this playback, memory suppression never fired, so no meaningful overmask/noop stress was exercised.

## Overlap, Crossing, And Near-Miss Analysis

Relative to Phase 9F-5 and G3 default-disabled, enabled failed-pair memory did not change row-level overlap or near-miss outcomes:

```text
next_inter_robot_overlap_direct_count = 6
next_path_crossing_direct_count = 0
next_path_near_miss_direct_count = 6
```

The result is consistent with the Phase 9G design expectation: wrapper-local failed-pair memory targets repeated same-owner reacquisition, not row-level overlap by itself.

## TTL Boundary Analysis

Phase 9G-1 found same-owner return delay was consistently 5 steps. Phase 9G-2 default `assignment_failed_pair_memory_duration_steps` is also 5, so Phase 9G-3 inspected whether the TTL covered the reacquisition step.

It did not. For all six repeated returns, `selected_pair_active_at_return=False`, `ttl_remaining_at_return=0`, and `active_count_at_return_step=0`.

| trigger step | pair | return step | trigger-to-return delta | selected pair active at return | ttl at return | last active memory step |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 240 | r1->36 | 246 | 6 | False | 0 | 244 |
| 256 | r1->36 | 262 | 6 | False | 0 | 260 |
| 271 | r2->44 | 277 | 6 | False | 0 | 276 |
| 272 | r1->36 | 278 | 6 | False | 0 | 276 |
| 287 | r2->44 | 293 | 6 | False | 0 | 292 |
| 288 | r1->36 | 294 | 6 | False | 0 | 292 |

Boundary finding: `duration_steps=5` records active memory for the immediate post-trigger window, but the same-owner reacquisition rows arrive after that memory has expired. The current default duration therefore misses the target failure pattern observed in Phase 9G-1/9G-3.

## Conclusion

Result: **FAIL** for enabled Phase 9G-2 failed-pair memory under the tested default `duration_steps=5`.

Reason:

```text
memory_triggered = True
memory_suppressed_any_action = False
same_owner_returns = 6 -> 6
coverage_gain_after_release_count = 0 -> 0
coverage_gain_within_20_count = 0 -> 0
```

The default-disabled identity result passed, and no noop/fail-open/coverage/overlap regression was observed. However, the enabled guardrail did not solve the repeated-return pattern because the TTL boundary missed the reacquisition step.

## Validation

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f2c_trigger_windows.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
result: passed, conclusion=FAIL

git diff --check
result: passed
notes: Git emitted LF-to-CRLF working-copy warnings for evaluate_assignment_rl_playback_diagnostics.py, TASK_PROGRESS.md, assignment_harl_wrapper.py, and scenario_config.py.
```

## Recommendation

Do not adopt the current enabled failed-pair memory default as successful.

Recommended next phase:

```text
Phase 9G-4A: TTL-boundary design review and fake-env validation.
```

The next step should decide, without training, whether the intended semantics are:

```text
extend the disabled-by-default playback experiment duration, for example duration_steps=6 or 10, only if explicitly authorized
or adjust TTL decrement timing so duration_steps=5 covers the observed return delay
```

Any follow-up playback should remain playback-only and user-authorized. No reward, observation, action-shape, env dynamics, controller, HARL, baseline, scenario YAML, cooldown tuning, or redirect-guardrail tuning changes are recommended from this phase.
