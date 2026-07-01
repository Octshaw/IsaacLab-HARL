# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-3D is complete.

This phase implemented a config-gated budget-aware cooldown trigger for Assignment RL and validated it with playback only.

No training was run.

Main result:

```text
Budget-aware cooldown reduced max_same_target_streak from 282 to 93-110 while preserving coverage.
Noop_when_available stayed at 0.0.
The main 1.5x+5 budget scenario preserved models coverage and improved best_model coverage.
Spatial diagnostics are mixed, so the result is a partial tradeoff rather than final success.
```

Interpretation category:

```text
BA-P: partial tradeoff
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline solver behavior, or default scenario cooldown setting were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-3D: budget-aware cooldown trigger implementation plus playback-only validation.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3D_BUDGET_AWARE_COOLDOWN_TRIGGER_REPORT.md
```

## Key Results

Budget model:

```text
expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)
budget_steps = ceil(expected_steps * assignment_cooldown_budget_multiplier + assignment_cooldown_budget_slack_steps)

robot_0 max_base_xy_step = 0.08
robot_1 max_base_xy_step = 0.10
robot_2 max_base_xy_step = 0.06
```

Phase 9E-3D playback summary:

```text
budget_m15_slack5_d5 models:
  final_coverage = 0.50
  coverage_auc = 0.3675
  max_same_target_streak = 110
  noop_when_available_rate = 0.0000
  budget_trigger_count = 20

budget_m15_slack5_d5 best_model:
  final_coverage = 0.46
  coverage_auc = 0.3387
  max_same_target_streak = 110
  noop_when_available_rate = 0.0000
  budget_trigger_count = 22

budget_m10_slack0_d5 models:
  final_coverage = 0.48
  coverage_auc = 0.3528
  max_same_target_streak = 93
  noop_when_available_rate = 0.0000
  budget_trigger_count = 32

budget_m10_slack0_d5 best_model:
  final_coverage = 0.42
  coverage_auc = 0.3224
  max_same_target_streak = 93
  noop_when_available_rate = 0.0000
  budget_trigger_count = 34
```

Reference comparison:

```text
Phase 9D-3 no cooldown:
  models final_coverage = 0.50, max_streak = 282
  best_model final_coverage = 0.40, max_streak = 282

Phase 9E-3A aggressive cooldown:
  models final_coverage = 0.02, max_streak = 10
  best_model final_coverage = 0.04, max_streak = 10

Phase 9E-3D main budget cooldown:
  models final_coverage = 0.50, max_streak = 110
  best_model final_coverage = 0.46, max_streak = 110
```

## Active Architecture / Implementation Path

Budget-aware cooldown remains config-gated and assignment-wrapper-local:

```text
AssignmentHarlWrapper-local per-robot-target cooldown
trigger_mode = streak | budget | budget_and_streak
available_actions mask only
reward unchanged
observations unchanged
noop always available
base env available_mask not mutated
default scenario cooldown-disabled
debug/ablation scenarios cooldown-enabled
```

Current budget trigger:

```text
same robot-target segment attempt_steps >= cost-derived budget_steps
AND selected target remains uncovered/available/feasible when configured
AND no global coverage gain when configured
AND same_target_streak >= budget_min_streak in budget_and_streak mode
```

Important interpretation:

```text
Cooldown is a wrapper-local action-mask guardrail.
It does not prove a target is unreachable.
It only suppresses repeated selection of the same robot-target pair under configured conditions.
```

## Key Files

Changed Python files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

New Phase 9E-3D scenario files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m10_slack0_d5.yaml
```

Phase 9E-3D documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3D_BUDGET_AWARE_COOLDOWN_TRIGGER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3D_BUDGET_COOLDOWN_TRIGGER_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated Phase 9E-3D outputs:

```text
results/assignment_diagnostics/phase9e3d_budget_cooldown_mask_smoke.json
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback/
results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_best_model_playback/
results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.csv
results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.json
```

## Latest Verification

Python compile:

```text
assignment_harl_wrapper.py: passed
scenario_config.py scan_mobile_manipulator_env.py: passed
evaluate_assignment_rl_playback_diagnostics.py test_assignment_cooldown_mask_smoke.py analyze_assignment_stuck_budget.py: passed
```

Smoke:

```text
scripts/environments/test_assignment_cooldown_mask_smoke.py
passed
actor obs = 909
shared obs = 2727
available_actions = [2, 3, 51]
budget trigger waited until budget exhaustion
```

Playback:

```text
4/4 Phase 9E-3D playback runs completed
summary CSV/JSON written under results/assignment_diagnostics/
```

Final repository checks after Phase 9E-3D docs:

```text
git diff --check: passed; LF-to-CRLF warnings on changed Python/docs files only
git status --short: expected Phase 9E modified/untracked files; no commit made
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-3D limitations:

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not full planner path length
budget trigger does not implement active-task lifecycle
budget state is not in actor/shared observations
validation is playback-only on one seed/checkpoint family
selected-target conflict increased in some budget playback runs
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run broad training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Phase 9E-3E: inspect budget-trigger assignment_history traces for m15_slack5_d5 before any training.
```

Questions for Phase 9E-3E:

```text
Do budget-triggered pairs match Phase 9E-3C over-budget no-completion targets?
Does selected-target conflict increase because robots rotate into the same alternatives?
Is m15_slack5_d5 safe enough for one scoped 100k single-seed debug training?
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3D_BUDGET_AWARE_COOLDOWN_TRIGGER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3D_BUDGET_COOLDOWN_TRIGGER_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3C_BUDGET_AWARE_STUCK_TARGET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3C_BUDGET_AWARE_STUCK_DIAGNOSTICS_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3B_COOLDOWN_STRENGTH_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3B_COOLDOWN_ABLATION_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3A_CROSS_PLAYBACK_COOLDOWN_ATTRIBUTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3A_CROSS_PLAYBACK_20260701.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
```
