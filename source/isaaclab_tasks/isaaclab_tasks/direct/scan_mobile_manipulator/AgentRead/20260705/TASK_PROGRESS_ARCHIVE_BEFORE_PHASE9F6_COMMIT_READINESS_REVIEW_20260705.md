# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-5 is complete.

This phase ran one limited playback-only validation with the Phase 9F-4B redirect guardrail explicitly enabled through a debug-only scenario. Classification:

```text
GUARDRAIL-P
```

No training was run. No broad playback sweep was run. No commit was made.

No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, path-crossing-aware redirect, active-task lifecycle, installed `site-packages`, or default scenario behavior were changed.

## Latest Completed Phase

Phase 9F-5: redirect guardrail playback validation.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
```

## Active Implementation Path

The Phase 9F-4B guardrail is implemented in `AssignmentHarlWrapper` only and remains disabled by default.

Boundary:

```text
supported context: recent_budget_trigger
default window_steps = 1
uses _previous_assignment as teammate claim snapshot
uses problem["viewpoint_pos"][..., :2] for spacing
derives default threshold from 2 * inter_robot_target_conflict_radius + inter_robot_target_conflict_safety_margin
applies after existing cooldown overlay
does not modify _apply_assignment_cooldown_to_available_mask()
does not mutate base env available_mask
preserves noop
fails open on over-mask by default
logs suppression / over-mask / fail-open diagnostics
```

Debug-only guardrail-enabled scenario used for Phase 9F-5:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

Original/default scenarios remain guardrail-disabled.

## Phase 9F-5 Result

Playback output:

```text
results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/
```

Generated history:

```text
assignment_history.csv rows = 897
assignment_history.csv columns = 71
budget_trigger_row_count = 6
trigger_pairs = r1->36: 4, r2->44: 2
schema validation = passed
```

Guardrail activation:

```text
redirect_guardrail_active_row_count = 6
guardrail_active_trigger_count = 6
active_rows_with_suppression_count = 6
claimed_target_suppression_total = 12
spacing_suppression_total = 74
fail_open_count = 0
overmask_count = 0
only_noop_remaining_count = 0
threshold = 0.85 m
```

Comparison against Phase 9F-2C disabled reference:

```text
next_exact_duplicate_direct_count: 4/6 -> 0/6
next_nearby_selected_target_direct_count: 5/6 -> 0/6
next_inter_robot_overlap_direct_count: 6/6 -> 6/6
next_path_crossing_direct_count: 1/6 -> 0/6
next_path_near_miss_direct_count: 5/6 -> 6/6
coverage_gain_within_20_count: 0/6 -> 0/6
return_to_triggered_pair_after_cooldown_count: 6/6 -> 6/6
final_coverage_ratio: 0.5 -> 0.5
coverage_auc: 0.330434779 -> 0.330434779
noop_when_available_rate: 0.0 -> 0.0
noop_action_rate: 0.0 -> 0.0
```

Interpretation:

```text
The local guardrail is promising for short-term exact/nearby redirect conflict mitigation in this limited validation.
It is not a lifecycle solution.
Row-level overlap and return-to-triggered-pair remain unresolved.
Near-miss proxy did not improve in this one playback.
No final performance claim should be made from this single run.
```

## Key Files

Changed/created Python and config files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
```

Existing Phase 9F-4B implementation files remain changed from the previous phase:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

Created/updated documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F5_GUARDRAIL_PLAYBACK_VALIDATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated result files:

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

## Latest Verification

Phase 9F-5 validation:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py
result: passed

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --output_dir results/assignment_diagnostics/phase9f5_redirect_guardrail_validation --stop_on_done
result: passed

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9f5_redirect_guardrail_validation.py --enabled_history results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --reference_history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9f5_redirect_guardrail_validation
result: passed

git diff --check
result: passed
notes: Git reported LF-to-CRLF working-copy warnings for existing touched files only.
```

## Known Issues / Limitations

```text
single episode / single checkpoint / limited playback only
same-step simultaneous new claims are not solved
path-crossing-aware redirect is not implemented
active-task lifecycle is not implemented
return-to-triggered-pair remains high
row-level overlap remains high
near-miss proxy did not improve in this one validation
performance is not claimed until broader playback validation
guardrail remains disabled unless a scenario/config explicitly enables it
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run training.

Do not run broad playback sweeps unless explicitly authorized.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, cooldown trigger logic, existing cooldown mask behavior, default scenario behavior, path-crossing-aware redirect, active-task lifecycle, or installed `site-packages`.

## Next Step

Recommended next decision:

```text
Phase 9F-6 or commit review:
  decide whether to run a slightly broader playback-only validation,
  or prepare a commit discussion for the disabled-by-default guardrail and diagnostics.

Phase 9G-0 remains needed:
  design active-task lifecycle or explicit failed-target state,
  because return-to-triggered-pair was unchanged at 6/6.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F5_GUARDRAIL_PLAYBACK_VALIDATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_REDIRECT_GUARDRAIL_IMPLEMENTATION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F4B_PATH_CORRECTION_20260705.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F4A_REDIRECT_GUARDRAIL_IMPLEMENTATION_BOUNDARY_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F3_DESIGN_DECISION_CONFLICT_REDIRECT_VS_LIFECYCLE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2C_TRIGGER_WINDOW_ROW_LEVEL_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F2A_ROW_LEVEL_CONFLICT_LOGGING_REPORT.md
```
