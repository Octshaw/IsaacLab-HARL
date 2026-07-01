# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-3B is complete.

This was a playback-only cooldown strength ablation. No training was run.

Main result:

```text
Weaker runtime cooldown configurations avoided the Phase 9E-3A aggressive-mask coverage collapse.
The best guardrail candidate is weak_d5_s30:
  models:     final_coverage = 0.44, max_streak = 30, noop_when_available = 0.0
  best_model: final_coverage = 0.28, max_streak = 30, noop_when_available = 0.0

Interpretation category: S, promising weak guardrail, with spatial-diagnostic caveats.
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline behavior, default scenario cooldown setting, reward tuning, or core cooldown implementation logic were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-3B: playback-only cooldown strength ablation on the Phase 9D-3 no-cooldown 100k checkpoint.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3B_COOLDOWN_STRENGTH_ABLATION_REPORT.md
```

## Key Results

Checkpoint used:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
```

Ablation summary:

```text
weak_d5_s30:
  models:     coverage 0.44, AUC 0.3272, max_streak 30, suppressed 9.04
  best_model: coverage 0.28, AUC 0.2334, max_streak 30, suppressed 9.83

weak_d5_s50:
  models:     coverage 0.60, AUC 0.4106, max_streak 50, suppressed 6.08
  best_model: coverage 0.34, AUC 0.2932, max_streak 50, suppressed 7.79

short_d3_s50:
  models:     coverage 0.46, AUC 0.3604, max_streak 50, suppressed 4.86
  best_model: coverage 0.38, AUC 0.3169, max_streak 50, suppressed 5.34

strict_attempt20_d5_s50:
  models:     coverage 0.42, AUC 0.3441, max_streak 50, suppressed 5.98
  best_model: coverage 0.40, AUC 0.3185, max_streak 50, suppressed 6.21
```

All variants had:

```text
noop_when_available_rate = 0.0
selected_pair_active_count = 0
exit code = 0 for all playback runs
```

Comparison anchors:

```text
Phase 9D-3 no cooldown:
  models coverage 0.50, max_streak 282
  best_model coverage 0.40, max_streak 282

Phase 9E-3A aggressive cooldown:
  models coverage 0.02, max_streak 10, suppressed about 47.9
  best_model coverage 0.04, max_streak 10, suppressed about 41.5
```

Important caveat:

```text
Spatial diagnostics are mixed. Selected-target conflict and crossing often worsened relative to Phase 9D-3 no cooldown.
Do not treat weak_d5_s30 as final; it is a diagnostic candidate.
```

## Active Architecture / Implementation Path

Phase 9E-1 cooldown remains implemented but should still be treated as diagnostics-only until a follow-up design is accepted:

```text
AssignmentHarlWrapper-local per-robot-target cooldown
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
debug/ablation scenarios cooldown-enabled
```

Important interpretation:

```text
Cooldown is a wrapper-local action-mask guardrail.
It does not prove a target is unreachable.
It only suppresses repeated selection of the same robot-target pair under configured conditions.
```

## Key Files

New Phase 9E-3B ablation scenarios:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s30.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s50.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_short_d3_s50.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_strict_attempt20_d5_s50.yaml
```

Phase 9E-3B documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3B_COOLDOWN_STRENGTH_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3B_COOLDOWN_ABLATION_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9E-3B outputs:

```text
results/assignment_diagnostics/phase9e3b_weak_d5_s30_models_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s30_best_model_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s50_models_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s50_best_model_playback/
results/assignment_diagnostics/phase9e3b_short_d3_s50_models_playback/
results/assignment_diagnostics/phase9e3b_short_d3_s50_best_model_playback/
results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_models_playback/
results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_best_model_playback/
results/assignment_diagnostics/phase9e3b_cooldown_ablation_summary.json
results/assignment_diagnostics/phase9e3b_cooldown_ablation_summary.csv
results/assignment_diagnostics/phase9e3b_trace_notes.md
results/assignment_diagnostics/phase9e3b_playback_queue_status.csv
```

## Latest Verification

Pre-flight:

```text
git status --short: existing Phase 9E-3A docs state
git diff --check: passed, LF-to-CRLF warning on TASK_PROGRESS.md only
py_compile evaluate_assignment_rl_playback_diagnostics.py: passed
```

Playback diagnostics:

```text
8/8 Phase 9E-3B playback runs completed with exit code 0
```

Final repository checks after Phase 9E-3B docs:

```text
git diff --check: passed, with LF-to-CRLF warning on TASK_PROGRESS.md only
git status --short: TASK_PROGRESS.md modified; AgentRead/20260701/ and four ablation scenario YAMLs untracked
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-3B result issue:

```text
Weak cooldowns avoid coverage collapse and reduce streaks, but spatial side-effect metrics are mixed.
```

Known implementation limitations:

```text
cooldown progress signal is global coverage gain only
no robot-target-specific coverage attribution
no team-level target cooldown
cooldown is mask-only and not included in observations
playback episodes are deterministic fixed-scenario repeats
weak variants were playback-only, not trained
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run 100k training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Phase 9E-3C: design a bounded validation plan around weak_d5_s30 and short_d3_s50 before any training.
```

Suggested questions:

```text
Can spatial side effects be reduced without losing streak control?
Should max concurrently cooled robot-target pairs per robot be capped?
Should trigger logic require stricter combined conditions?
Should weak_d5_s30 and short_d3_s50 be replayed on any additional available no-cooldown checkpoint before training?
What tiny smoke training, if any, is justified after playback-only acceptance?
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3B_COOLDOWN_STRENGTH_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3B_COOLDOWN_ABLATION_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3A_CROSS_PLAYBACK_COOLDOWN_ATTRIBUTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3A_CROSS_PLAYBACK_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
```
