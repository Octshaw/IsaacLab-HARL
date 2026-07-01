# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-1 is complete at smoke scale.

A config-gated per-robot-target cooldown is implemented as an assignment-RL wrapper-local `available_actions` mask mechanism. It is disabled by default and enabled only through explicit config/scenario override.

No reward formulas/default scales, observation dimensions, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, or baseline solver behavior were changed. No commit was made.

## Latest Completed Phase

Phase 9E-1: cooldown mask implementation with diagnostics.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
```

## Active Architecture / Implementation Path

Cooldown lives in `AssignmentHarlWrapper` only.

State:

```text
_per_robot_target_failed_attempt_count: [num_envs, num_agents, num_viewpoints], torch.long
_per_robot_target_cooldown_remaining: [num_envs, num_agents, num_viewpoints], torch.long
```

Mask behavior when enabled:

```text
filtered_available_mask = problem["available_mask"] & ~(_per_robot_target_cooldown_remaining > 0)
available_actions = concat(filtered_available_mask, always_available_noop)
```

Default config:

```yaml
assignment_cooldown_enabled: false
assignment_cooldown_scope: per_robot_target
assignment_cooldown_trigger_attempts: 3
assignment_cooldown_trigger_same_target_streak: 10
assignment_cooldown_trigger_steps_since_global_gain: 10
assignment_cooldown_duration_steps: 20
assignment_cooldown_require_uncovered: true
assignment_cooldown_require_available: true
assignment_cooldown_require_feasible: true
assignment_cooldown_require_no_global_gain: true
assignment_cooldown_clear_on_covered: true
assignment_cooldown_apply_to_action_mask: true
assignment_cooldown_log_diagnostics: true
```

Dedicated enabled debug scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

The default scenario remains cooldown-disabled.

## Key Files

Changed:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
```

Added:

```text
scripts/environments/test_assignment_cooldown_mask_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E1_COOLDOWN_20260630.md
```

## Latest Verification

Python compile passed for changed Python files.

Cooldown mask smoke passed:

```text
results/assignment_diagnostics/phase9e1_assignment_cooldown_mask_smoke.json
```

Confirmed:

```text
disabled mask matches baseline
selected robot-target cooldown masks only that pair
same viewpoint remains available to other robots
noop remains available
no all-zero action rows
cooldown decrements
covered target clears cooldown/failed count
full reset clears state
done-env partial reset clears done env only
actor obs shape = [2, 909]
shared obs shape = [2, 3, 2727]
available_actions shape = [2, 3, 51]
```

Tiny training-entry smoke with cooldown disabled passed:

```text
results/assignment_diagnostics/phase9e1_cooldown_disabled_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e1_cooldown_disabled_recheck_1k2/seed-00001-2026-06-30-23-04-38
```

Tiny training-entry smoke with cooldown enabled passed:

```text
results/assignment_diagnostics/phase9e1_cooldown_enabled_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e1_cooldown_enabled_recheck_1k2/seed-00001-2026-06-30-23-08-09
```

TensorBoard scalar sanity:

```text
disabled run: scalar_tags=46, nonfinite=0, final assignment_cooldown.enabled=0.0
enabled run:  scalar_tags=46, nonfinite=0, final assignment_cooldown.enabled=1.0
```

Both tiny runs wrote `models/` and `best_model/`.

Repository checks after docs should be rerun before handoff if any file changes continue:

```text
git diff --check
git status --short
```

## Known Issues / Blockers

No current blocker.

Known limitations:

```text
cooldown progress signal is global coverage gain only
no robot-target-specific coverage attribution
no team-level target cooldown
cooldown is mask-only and not included in observations
enabled 1.2k run is plumbing smoke only, not policy-quality evidence
playback diagnostics were extended but checkpoint playback was not run in Phase 9E-1
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run 100k training, checkpoint playback, or formal evaluation until the Phase 9E-1 implementation/report is reviewed.

Do not tune rewards, change observation dimensions, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

## Next Step

Recommended next phase:

```text
Run one scoped 100k single-seed cooldown-enabled debug training using algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml, then run playback diagnostics on models/best_model and compare against Phase 9D-3 no-cooldown 100k.
```

Primary comparison targets:

```text
max_same_target_streak
late_repeated_assignment_count
final_coverage
coverage_auc
noop_when_available_rate
selected_target_conflict_rate
assignment_cooldown trigger/active/suppressed counts
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E1_COOLDOWN_20260630.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
```
