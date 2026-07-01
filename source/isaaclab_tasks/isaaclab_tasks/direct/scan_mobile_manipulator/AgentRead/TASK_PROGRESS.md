# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-2 is complete.

One scoped 100k single-seed cooldown-enabled assignment-RL debug training was run with:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

Training completed successfully, playback diagnostics completed for both `models/` and `best_model/`, and TensorBoard scalar sanity passed.

Result classification: **D. Negative side effect**.

The cooldown mask reduced the worst repeated same-target streak from 282 to 10, but coverage collapsed and noop-when-available rose sharply. This cooldown configuration should not be promoted as an improvement.

No commit was made.

## Latest Completed Phase

Phase 9E-2: cooldown-enabled 100k debug training plus playback comparison against the Phase 9D-3 no-cooldown 100k reference.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
```

## Key Results

Actual run directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19
```

Checkpoint directories:

```text
models/: yes
best_model/: yes
```

TensorBoard scalar sanity:

```text
scalar tags = 46
nonfinite scalars = 0
final Total_Reward = 3.9008512497
final assignment_rl_reward/final_reward_mean = 0.0130028371
Total_Reward ~= final_reward_mean * 300
assignment_cooldown.enabled = 1.0
```

Playback comparison:

```text
models:
  no-cooldown final_coverage = 0.50, cooldown final_coverage = 0.12
  no-cooldown coverage_auc = 0.3675, cooldown coverage_auc = 0.1042
  no-cooldown max_same_target_streak = 282, cooldown max_same_target_streak = 10
  no-cooldown late targets = r0->44, r1->44, r2->15
  cooldown late targets = r0->20, r1->5, r2->3
  cooldown noop_when_available_rate = 0.4805

best_model:
  no-cooldown final_coverage = 0.40, cooldown final_coverage = 0.10
  no-cooldown coverage_auc = 0.3234, cooldown coverage_auc = 0.0868
  no-cooldown max_same_target_streak = 282, cooldown max_same_target_streak = 10
  no-cooldown late targets = r0->39, r1->0, r2->15
  cooldown late targets = r0->20, r1->5, r2->3
  cooldown noop_when_available_rate = 0.4671
```

Cooldown playback intervention:

```text
models:     trigger_count_mean = 380.0, active_count_mean = 24.4548, suppressed_count_mean = 24.3612
best_model: trigger_count_mean = 388.0, active_count_mean = 25.0569, suppressed_count_mean = 24.9632
selected_pair_active_count = 0 for both playback runs
```

## Active Architecture / Implementation Path

Phase 9E-1 cooldown remains the active implementation path:

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

Phase 9E-1 implementation files remain modified or untracked:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

Phase 9E-2 documentation added/updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E2_REPORT_20260630.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9E-2 outputs:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_console.log
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_scalar_sanity.json
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_playback_comparison_summary.json
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/
```

## Latest Verification

Pre-flight:

```text
git status --short: only expected Phase 9E-1 dirty files were present
git diff --check: passed, with only LF-to-CRLF warnings
py_compile on changed Phase 9E-1 Python files: passed
```

Training:

```text
100k cooldown-enabled training: completed, exit code 0
models/ exists: yes
best_model/ exists: yes
```

Scalar sanity:

```text
passed: 46 scalar tags, 0 NaN/Inf, Total_Reward still tracks assignment_rl_reward/final_reward_mean
```

Playback diagnostics:

```text
models/ playback: passed with --headless --device cuda:0
best_model/ playback: passed with --headless --device cuda:0
```

Note:

```text
An initial playback attempt without --headless failed during Isaac Sim viewport startup.
The script supports AppLauncher flags, so playback was rerun successfully with --headless --device cuda:0.
```

Final repository checks after Phase 9E-2 docs:

```text
git diff --check: passed, with known LF-to-CRLF warnings only
git status --short: expected Phase 9E-1 dirty files plus Phase 9E-2 report/archive/docs
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-2 result issue:

```text
The current cooldown debug configuration reduces repeated streaks but badly harms coverage and increases noop-when-available.
```

Known implementation limitations:

```text
cooldown progress signal is global coverage gain only
no robot-target-specific coverage attribution
no team-level target cooldown
cooldown is mask-only and not included in observations
single-seed 100k debug run only
playback episodes are deterministic fixed-scenario repeats
```

## Do Not Do

Do not commit unless explicitly asked.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe the current cooldown configuration as a clear improvement.

Do not run another 100k job until a follow-up design/ablation question is explicit.

## Next Step

Recommended next phase:

```text
Phase 9E-3 design/ablation planning for cooldown side effects.
```

First inspect late playback traces around cooldown triggers and noop selections:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/assignment_history.csv
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/assignment_history.csv
```

Candidate questions:

```text
Is the cooldown trigger too aggressive?
Is the duration too long?
Should cooldown require a stronger repeated-failure signal?
Should policy observations include cooldown state before training with this guardrail?
Why does noop_when_available rise to about 47-48 percent?
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E2_REPORT_20260630.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E1_COOLDOWN_20260630.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
```
