# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-4B playback-only validation is complete.

Phase 9G-4B ran one new playback configuration:

```text
phase9g4b_failed_pair_memory_d6
assignment_failed_pair_memory_enabled = True
assignment_failed_pair_memory_duration_steps = 6
```

No training was run. No commit was made.

The failed-pair memory mechanism code was not changed. TTL decrement timing was not changed. `assignment_harl_wrapper.py`, `scenario_config.py`, and repository scenario YAML files were not changed in Phase 9G-4B.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, installed `site-packages`, cooldown tuning, Phase 9F redirect guardrail tuning, new failure criteria, or env-level lifecycle behavior were changed.

## Latest Result

Phase 9G-4B result: **FAIL**.

D=6 validated the TTL boundary prediction but did not solve the repeated return pattern:

```text
failed_pair_memory_trigger_count = 6
failed_pair_memory_suppressed_count = 6
same_owner_returns = 6
coverage_gain_after_release_count = 0
coverage_gain_within_20_count = 0
noop_action_rate = 0.0
noop_when_available_rate = 0.0
failed_pair_memory_fail_open_count = 0
failed_pair_memory_only_noop_remaining_count = 0
```

Interpretation:

```text
D=6 suppressed the previously missed T+6 same-owner reacquisition rows.
The policy then returned to the same failed pair at T+7 after memory expired.
Same-owner returns did not decrease relative to Phase 9G-3 D=5.
No coverage gain was produced.
No immediate noop or fail-open pressure was observed.
```

Required next-step conflict metrics stayed unchanged relative to G3 D=5:

```text
next_exact_duplicate_direct_count = 0
next_nearby_selected_target_direct_count = 0
next_inter_robot_overlap_direct_count = 6
next_path_crossing_direct_count = 0
next_path_near_miss_direct_count = 6
```

The broader duplicate-selected-target playback summary increased:

```text
D=5 duplicate_selected_target_rate_mean = 0.07357859531772576
D=6 duplicate_selected_target_rate_mean = 0.09698996655518395
```

## Latest Completed Phase

Phase 9G-4B: playback-only validation with failed-pair memory enabled at `duration_steps = 6`.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
```

Archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_20260706.md
```

## Files Created Or Updated In Phase 9G-4B

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

Note: the worktree still contains earlier uncommitted Phase 9G-1/9G-2/9G-3/9G-4A files and modifications.

## Playback Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/configs/phase9g4b_failed_pair_memory_d6.json --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6 --stop_on_done
```

Playback completed one episode at step 299 and wrote diagnostics.

## Analyzer Commands

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_default_disabled/assignment_history.csv results/assignment_diagnostics/phase9g3_failed_pair_memory_validation/phase9g3_failed_pair_memory_enabled/assignment_history.csv results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/lifecycle_all

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f2c_trigger_windows.py --history results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_trigger_windows

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_failed_pair_memory_d6/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/phase9g4b_d6_vs_phase9f5_reference

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
```

## Latest Verification

Passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f2c_trigger_windows.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
git diff --check
```

The Phase 9G-4B helper reported:

```text
conclusion=FAIL
d6_suppressed_any_action=True
same_owner_return_delta_d6_minus_d5=0.0
d6_returns_shifted_after_t_plus_6_count=6
```

`git diff --check` passed with LF-to-CRLF working-copy warnings only.

## Known Issues / Blockers

Temporary TTL-only failed-pair memory can delay same-owner reacquisition by one row, but did not reduce total same-owner returns in this playback.

The result suggests the current policy is willing to reacquire the same failed pair immediately after memory expiry. Longer TTL may delay the return further, but Phase 9G-4B provides no evidence that this creates coverage gain.

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run another playback sweep unless explicitly authorized.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or redirect guardrail tuning.

Do not change TTL decrement semantics without a separate implementation phase and fake-env update.

## Next Step

Recommended Phase 9G-5:

```text
Design decision review: decide whether to stop the TTL-only failed-pair memory path, run one explicitly authorized longer-duration playback stress test, or move back toward a clearer active-task/release lifecycle mechanism.
```

The D=6 result does not justify training. A D=10 playback may answer whether a longer delay merely shifts the return again, but it should be treated as a bounded diagnostic, not as a proven lifecycle solution.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
