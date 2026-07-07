# Phase 9G-4B Failed-Pair Memory D=6 Playback Validation Report

Date: 2026-07-06

## Scope And Boundary

Phase 9G-4B ran one playback-only validation with failed-pair memory enabled and `assignment_failed_pair_memory_duration_steps = 6`.

No training was run. The failed-pair memory mechanism code was not changed. TTL decrement timing was not changed. No D=10 playback was run.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, installed packages, repository scenario YAML, cooldown tuning, Phase 9F redirect guardrail tuning, new failure criteria, or env-level lifecycle behavior were changed.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

## Files Created Or Updated

Created:

```text
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/configs/phase9g4b_failed_pair_memory_d6.json
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/lifecycle_all/
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_trigger_windows/
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_vs_phase9f5_reference/
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/comparison/
scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_20260706.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Not changed in Phase 9G-4B:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
repository scenario YAML files
```

## Run-Local D=6 Config

Config path:

```text
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/configs/phase9g4b_failed_pair_memory_d6.json
```

The config preserved the Phase 9F-5 cooldown and redirect-guardrail setup. The only intended failed-pair memory settings were:

```json
{
  "assignment_failed_pair_memory": {
    "enabled": true,
    "duration_steps": 6,
    "apply_to_action_mask": true,
    "source": "budget_trigger",
    "fail_open": true,
    "clear_on_coverage": true,
    "log_diagnostics": true
  }
}
```

No repository scenario YAML was modified.

## Playback Command

Checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
```

Exact playback command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/configs/phase9g4b_failed_pair_memory_d6.json --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6 --stop_on_done
```

Result: playback completed one episode at step 299 and wrote diagnostics.

## Offline Analyzer Commands

Lifecycle reconstruction:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/lifecycle_all
```

Trigger-window analysis:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_trigger_windows
```

Redirect-guardrail comparison:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_vs_phase9f5_reference
```

D=6 comparison aggregation:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
```

Generated:

```text
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/comparison/phase9g4b_d6_comparison_table.csv
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/comparison/phase9g4b_d6_boundary_rows.csv
results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/comparison/phase9g4b_d6_comparison_summary.json
```

## Comparison Table

| run | coverage | auc | same-owner returns | return delay proxy | teammate reacquires | gain after release | gain <=20 | noop rate | noop avail rate | next exact | next nearby | next overlap | next crossing | next near miss | memory triggers | active pair-step total | memory suppressed | fail-open | only-noop | T+6 suppressed | T+6 original selected | shifted after T+6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| reference_phase9f2c_disabled | 0.5 | 0.330434589 | 6 | 5 | 2 | 0 | 0 | 0.0 | 0.0 | 4 | 5 | 6 | 1 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| reference_phase9f5_redirect_guardrail | 0.5 | 0.330434589 | 6 | 5 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| phase9g3_default_disabled | 0.5 | 0.330434589 | 6 | 5 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| phase9g3_failed_pair_memory_d5 | 0.5 | 0.330434589 | 6 | 5 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 6 | 30 | 0 | 0 | 0 | 0 | 6 | 0 |
| phase9g4b_failed_pair_memory_d6 | 0.5 | 0.330434589 | 6 | 6 | 2 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 6 | 0 | 6 | 6 | 36 | 6 | 0 | 0 | 6 | 0 | 6 |

## D=6 Suppression Result

D=6 produced failed-pair memory suppression:

```text
failed_pair_memory_trigger_count = 6
failed_pair_memory_active_pair_step_total = 36
failed_pair_memory_active_step_count = 30
failed_pair_memory_suppressed_count = 6
failed_pair_memory_fail_open_count = 0
failed_pair_memory_only_noop_remaining_count = 0
```

This confirms that the Phase 9G-4A TTL boundary prediction was correct: the previously missed T+6 rows were now inside the suppressible window.

## Same-Owner Return Result

D=6 did not reduce same-owner returns:

```text
phase9g3_failed_pair_memory_d5 same_owner_returns = 6
phase9g4b_failed_pair_memory_d6 same_owner_returns = 6
delta = 0
```

The lifecycle proxy return delay shifted:

```text
D=5 median_same_owner_return_delay_steps = 5
D=6 median_same_owner_return_delay_steps = 6
```

Trigger-window direct return deltas shifted:

```text
D=5 return_step_delta = 6 for all 6 trigger rows
D=6 return_step_delta = 7 for all 6 trigger rows
```

## T+6 Boundary Analysis

For D=6, all six previously missed T+6 boundary rows were suppressed:

| trigger | pair | T+6 step | selected at T+6 | original pair selected at T+6 | memory suppressed at T+6 | return step | return delta |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 240 | r1->36 | 246 | 44 | False | 1 | 247 | 7 |
| 257 | r1->36 | 263 | 44 | False | 1 | 264 | 7 |
| 271 | r2->44 | 277 | 24 | False | 1 | 278 | 7 |
| 274 | r1->36 | 280 | 44 | False | 1 | 281 | 7 |
| 288 | r2->44 | 294 | 24 | False | 1 | 295 | 7 |
| 291 | r1->36 | 297 | 44 | False | 1 | 298 | 7 |

Interpretation:

```text
The T+6 same-owner reacquisition rows were absent because memory suppressed the original pair.
The policy then returned to the same failed pair at T+7 after memory expired.
```

At the actual D=6 return rows:

```text
selected_pair_active_at_return_count = 0
ttl_remaining_at_return_min = 0
ttl_remaining_at_return_max = 0
ttl_remaining_at_return_mean = 0
```

This is expected because the returns moved one step past the D=6 window.

## Coverage Analysis

No coverage improvement was observed:

```text
final_coverage_ratio = 0.5
coverage_auc = 0.33043458868428616
coverage_gain_after_release_count = 0
coverage_gain_within_20_count = 0
```

The D=6 suppression redirected one decision row per trigger but did not produce new coverage after release.

## Noop, Fail-Open, And Overmask Analysis

No noop or fail-open regression was observed:

```text
noop_action_rate = 0.0
noop_when_available_rate = 0.0
failed_pair_memory_fail_open_count = 0
failed_pair_memory_only_noop_remaining_count = 0
selected_available_mask_mean = 1.0
available_actions_shape = [1, 3, 51]
```

This means D=6 did not create immediate noop pressure in this playback. It also means the failure is not caused by fail-open preserving the original pair at T+6.

## Overlap, Crossing, And Near-Miss Analysis

The required next-step conflict metrics did not worsen relative to G3 D=5:

```text
next_exact_duplicate_direct_count = 0
next_nearby_selected_target_direct_count = 0
next_inter_robot_overlap_direct_count = 6
next_path_crossing_direct_count = 0
next_path_near_miss_direct_count = 6
```

The broader playback summary did show a higher duplicate-selected-target rate:

```text
D=5 duplicate_selected_target_rate_mean = 0.07357859531772576
D=6 duplicate_selected_target_rate_mean = 0.09698996655518395
```

This was not the primary pass/fail criterion, but it reinforces that D=6 did not create a useful improvement.

## Conclusion

Result: **FAIL**.

Reason:

```text
failed_pair_memory_suppressed_count > 0: yes, 6 suppressions
same_owner_returns decreased: no, 6 -> 6
coverage gain after release: no, 0
coverage gain within 20: no, 0
returns shifted later: yes, all 6 shifted from T+6 to T+7
```

D=6 validated the TTL mechanics but not the intended lifecycle outcome. The guardrail can delay the repeated same-owner return by one decision row, but with the current policy and temporary TTL semantics it does not prevent reacquisition or create coverage gain.

## Validation

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
result: C:\isaacenvs\isaac45_harl\python.exe

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f2c_trigger_windows.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
result: passed, conclusion=FAIL

git diff --check
result: passed with LF-to-CRLF working-copy warnings only
```

## Recommendation

Do not treat the TTL-only failed-pair memory guardrail as successful based on D=6.

Recommended next phase:

```text
Phase 9G-5: design decision review for whether temporary failed-pair memory should be stopped, extended to an explicitly longer playback-only stress test, or replaced by a more explicit active-task/release lifecycle mechanism.
```

The D=6 result does not justify training. A D=10 playback could test whether a longer temporary delay changes behavior, but it should not be run automatically: D=6 already showed the policy returns immediately after memory expiry, so further TTL escalation carries overmask/noop/reacquisition risk without evidence of coverage gain.
