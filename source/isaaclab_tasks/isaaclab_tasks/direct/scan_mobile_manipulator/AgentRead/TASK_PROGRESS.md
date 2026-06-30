# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-0 stuck-target recovery / failed-target cooldown mechanism design is complete.

This was design-only. No Python code, training, checkpoint playback, formal evaluation, reward tuning, mask/controller/solver/env dynamics/HARL behavior, or commit was performed.

## Design Report

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
```

## Recommended Mechanism

Use a config-gated per-robot-target temporary cooldown in the assignment RL wrapper.

Core idea:

```text
If robot_i repeatedly selects viewpoint_j,
and viewpoint_j is available, feasible, and uncovered,
and repeated attempts produce no global coverage gain,
then temporarily remove viewpoint_j from robot_i's available action mask.
```

Keep `viewpoint_j` available to other robots unless a future team-level cooldown is explicitly enabled.

## Key Design Decisions

```text
default enabled = false
scope = per_robot_target first
location = AssignmentHarlWrapper, assignment RL only
effect = available_actions mask only
noop = always remains available
reward = unchanged for Phase 9E-1
observation dimensions = unchanged for Phase 9E-1
static feasibility = unchanged
controller / solver / env dynamics = unchanged
baseline solvers = unchanged unless explicitly enabled in a future ablation
```

Proposed state:

```text
_per_robot_target_failed_attempt_count: [num_envs, num_agents, num_viewpoints]
_per_robot_target_cooldown_remaining: [num_envs, num_agents, num_viewpoints]
```

Proposed default config pattern:

```yaml
assignment_cooldown_enabled: false
assignment_cooldown_scope: per_robot_target
assignment_cooldown_trigger_attempts: 3
assignment_cooldown_trigger_same_target_streak: 10
assignment_cooldown_trigger_steps_since_global_gain: 10
assignment_cooldown_duration_steps: 20
assignment_cooldown_apply_to_action_mask: true
assignment_cooldown_log_diagnostics: true
```

## Next Recommendation

```text
Phase 9E-1: implement config-gated per-robot-target cooldown as an assignment-RL wrapper-local mask mechanism with diagnostics, reward unchanged.
```

First validation should be smoke-scale only:

```text
unit-like cooldown state/mask smoke
episode reset smoke
tiny training-entry smoke
then one scoped 100k single-seed debug run only if smokes pass
```

## Validation

No Python/code files were changed for Phase 9E-0, so no `py_compile` was required.

```text
git diff --check = passed, with TASK_PROGRESS.md LF/CRLF warning only
git status --short = TASK_PROGRESS modified and new Phase 9E-0 design report
```

## Do Not Do

Do not commit unless explicitly asked.

Do not proceed to implementation, training, checkpoint playback, formal evaluation, reward tuning, observation-dimension changes, controller/mask/solver/env dynamics changes, path planning, collision/local avoidance, arbitrary-N architecture work, or new handcrafted baselines from this task.

Do not enable cooldown globally by default. Preserve previous behavior unless an explicit Phase 9E-1 experiment config or flag enables the mechanism.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
```
