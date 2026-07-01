# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-3E is complete.

This phase inspected Phase 9E-3D budget-aware cooldown trigger traces.

No training was run.

Main result:

```text
All m15_slack5_d5 budget-triggered pairs matched the Phase 9E-3C known over-budget no-completion pairs.
Triggers fired at or after budget exhaustion.
Coverage was preserved or improved, and noop_when_available stayed at 0.0.
Post-trigger returns to the same target are common, and duplicate/crossing proxy pressure is concentrated near trigger windows.
```

Interpretation category:

```text
TRACE-PARTIAL
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline solver behavior, default scenario cooldown setting, cooldown trigger logic, cooldown mask behavior, budget model, budget parameters, or scenario YAMLs were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-3E: trace-level inspection of budget-aware cooldown trigger events.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3E_BUDGET_TRIGGER_TRACE_INSPECTION_REPORT.md
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

Phase 9E-3E inspected the Phase 9E-3D `m15_slack5_d5` playback traces:

```text
models:
  total trigger rows across 5 episodes = 100
  per-episode mean trigger count = 20
  known stuck-pair trigger fraction = 1.00
  unique triggered pairs = r0->44, r1->44, r2->15
  trigger budget ratio range = 1.00 to 1.00
  triggers followed by coverage gain within 20 steps = 45/100

best_model:
  total trigger rows across 5 episodes = 110
  per-episode mean trigger count = 22
  known stuck-pair trigger fraction = 1.00
  unique triggered pairs = r0->39, r1->0, r2->15
  trigger budget ratio range = 1.00 to 1.25
  triggers followed by coverage gain within 20 steps = 50/110
```

Post-trigger redirect summary:

```text
models:
  next target distribution = 48:60, 0:35, 28:5
  next target equals another robot current target = 0/100
  returned to triggered target later = 95/100

best_model:
  next target distribution = 48:70, 0:35, 34:5
  next target equals another robot current target = 25/110
  returned to triggered target later = 110/110
```

Conflict/spatial proxy summary:

```text
row-level selected-target conflict and inter-robot overlap are unavailable in assignment_history.csv
exact duplicate selected-target proxy is concentrated inside trigger windows:
  models: 0.1531 inside windows vs 0.0000 outside
  best_model: 0.1244 inside windows vs 0.0000 outside
base-motion crossing proxy is somewhat higher inside trigger windows:
  models: 0.0909 inside vs 0.0593 outside
  best_model: 0.1212 inside vs 0.0926 outside
```

m15 vs strict budget comparison:

```text
m15_slack5_d5 is safer than m10_slack0_d5 for any next debug-training probe:
  lower suppression
  fewer budget triggers
  fewer over-budget selected events
  higher coverage/AUC
strict budget reduces max streak further but intervenes more aggressively
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
scripts/environments/analyze_budget_cooldown_traces.py
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

Phase 9E-3E documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3E_BUDGET_TRIGGER_TRACE_INSPECTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3E_BUDGET_TRACE_INSPECTION_20260701.md
```

Generated Phase 9E-3E outputs:

```text
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/budget_trigger_events.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/budget_trigger_windows.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/post_trigger_redirect_summary.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/conflict_after_trigger_summary.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/phase9e3e_budget_trigger_trace_summary.json
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/phase9e3e_trace_notes.md
```

## Latest Verification

Python compile:

```text
assignment_harl_wrapper.py: passed
scenario_config.py scan_mobile_manipulator_env.py: passed
evaluate_assignment_rl_playback_diagnostics.py test_assignment_cooldown_mask_smoke.py analyze_assignment_stuck_budget.py: passed
analyze_budget_cooldown_traces.py: passed
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

Trace inspection:

```text
Phase 9E-3E analyzer completed
6 trace output files written under results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/
classification = TRACE-PARTIAL
```

Final repository checks after Phase 9E-3E docs:

```text
py_compile scripts/environments/analyze_budget_cooldown_traces.py: passed
git diff --check: passed with known LF-to-CRLF warnings on changed files
git status --short: expected Phase 9E modified files plus untracked 20260701 reports/scenarios/analysis scripts
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-3E limitations:

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not full planner path length
budget trigger does not implement active-task lifecycle
budget state is not in actor/shared observations
validation is playback-only on one seed/checkpoint family
row-level selected-target conflict and inter-robot overlap are unavailable in assignment_history.csv
duplicate selected target is only an exact-target conflict proxy
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run broad training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
One scoped 100k single-seed debug training may be run manually with m15_slack5_d5, then playback diagnostics and trace comparison.
```

Use:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
```

After training, compare against:

```text
Phase 9D-3 no cooldown
Phase 9E-3A aggressive cooldown
Phase 9E-3B weak_d5_s30 and short_d3_s50
Phase 9E-3D m15 playback
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E3E_BUDGET_TRIGGER_TRACE_INSPECTION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E3E_BUDGET_TRACE_INSPECTION_20260701.md
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
