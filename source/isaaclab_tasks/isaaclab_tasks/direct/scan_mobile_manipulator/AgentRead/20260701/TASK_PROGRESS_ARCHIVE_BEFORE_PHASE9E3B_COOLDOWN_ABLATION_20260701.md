# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-3A is complete.

This was a playback-only cross-diagnostic phase. No training was run.

Phase 9E-3A attribution result:

```text
Combined Case 2 + Case 4.

Runtime cooldown masking is the dominant immediate cause of the Phase 9E-2 playback collapse.
Removing cooldown at playback lets cooldown-trained checkpoints recover much of their coverage,
but the old repeated stuck-target behavior returns.
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline behavior, default scenario cooldown setting, cooldown parameters, or cooldown mechanism were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-3A: cross-playback diagnostics for cooldown side-effect attribution.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3A_CROSS_PLAYBACK_COOLDOWN_ATTRIBUTION_REPORT.md
```

## Key Results

Phase 9D-3 no-cooldown checkpoint found:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
```

Phase 9E-2 cooldown-trained checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19
```

Cross-playback summary:

```text
A1 no-cooldown models + cooldown playback:
  final_coverage = 0.02
  coverage_auc = 0.0189
  max_same_target_streak = 10
  noop_when_available_rate = 0.0000

A2 no-cooldown best_model + cooldown playback:
  final_coverage = 0.04
  coverage_auc = 0.0374
  max_same_target_streak = 10
  noop_when_available_rate = 0.1371

B1 cooldown-trained models + cooldown-disabled playback:
  final_coverage = 0.36
  coverage_auc = 0.2755
  max_same_target_streak = 243
  noop_when_available_rate = 0.0000

B2 cooldown-trained best_model + cooldown-disabled playback:
  final_coverage = 0.44
  coverage_auc = 0.2863
  max_same_target_streak = 243
  noop_when_available_rate = 0.1104
```

Interpretation:

```text
No-cooldown policies collapse when cooldown is applied at playback.
Cooldown-trained policies recover much of coverage when cooldown is removed.
Cooldown still suppresses repeated streaks, but current mask behavior is too damaging.
```

## Active Architecture / Implementation Path

Phase 9E-1 cooldown remains implemented but should be treated as diagnostics-only:

```text
AssignmentHarlWrapper-local per-robot-target cooldown
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
debug scenario cooldown-enabled
```

Important interpretation:

```text
Cooldown is a wrapper-local action-mask guardrail.
It does not prove a target is unreachable.
It only suppresses repeated selection of the same robot-target pair under configured conditions.
```

## Key Files

Phase 9E-1 implementation files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

Phase 9E-3A documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3A_CROSS_PLAYBACK_COOLDOWN_ATTRIBUTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3A_CROSS_PLAYBACK_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9E-3A outputs:

```text
results/assignment_diagnostics/phase9e3a_no_cooldown_models_with_cooldown_playback/
results/assignment_diagnostics/phase9e3a_no_cooldown_best_model_with_cooldown_playback/
results/assignment_diagnostics/phase9e3a_cooldown_models_without_cooldown_playback/
results/assignment_diagnostics/phase9e3a_cooldown_best_model_without_cooldown_playback/
results/assignment_diagnostics/phase9e3a_cross_playback_comparison_summary.json
results/assignment_diagnostics/phase9e3a_cross_playback_trace_summary.csv
```

## Latest Verification

Pre-flight:

```text
git status --short: clean at phase start
git diff --check: clean at phase start
py_compile evaluate_assignment_rl_playback_diagnostics.py: passed
```

Playback diagnostics:

```text
A1 no-cooldown models + cooldown playback: passed, exit code 0
A2 no-cooldown best_model + cooldown playback: passed, exit code 0
B1 cooldown-trained models + cooldown-disabled playback: passed, exit code 0
B2 cooldown-trained best_model + cooldown-disabled playback: passed, exit code 0
```

Final repository checks after Phase 9E-3A docs:

```text
git diff --check: passed, with LF-to-CRLF warning on TASK_PROGRESS.md only
git status --short: TASK_PROGRESS.md modified and AgentRead/20260701/ untracked
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-3A result issue:

```text
The current cooldown debug configuration/mask-only behavior is too aggressive.
It can cap repeated streaks, but it can also collapse coverage at playback.
```

Known implementation limitations:

```text
cooldown progress signal is global coverage gain only
no robot-target-specific coverage attribution
no team-level target cooldown
cooldown is mask-only and not included in observations
playback episodes are deterministic fixed-scenario repeats
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run another 100k cooldown-enabled training job with the current cooldown debug configuration.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Phase 9E-3B: design a smaller cooldown ablation/redesign plan before any new training.
```

Candidate questions:

```text
Should cooldown duration be shorter?
Should trigger thresholds be higher?
Should maximum concurrently cooled targets per robot be capped?
Should cooldown require a stricter repeated-failure signal?
Should cooldown state be observable before training with a mask?
Is an inference-only guardrail viable only after a much less aggressive mask design?
```

## Detailed Reports / Archives

```text
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
