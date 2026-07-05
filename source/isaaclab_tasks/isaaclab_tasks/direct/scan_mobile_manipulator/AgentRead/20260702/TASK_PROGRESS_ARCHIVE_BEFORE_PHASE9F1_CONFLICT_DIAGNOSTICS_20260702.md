# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9F-0 is complete.

This phase created a design-only plan for the next step after the committed Phase 9E budget-aware cooldown work.

No code was implemented.
No training was run.
No playback was run.

Main result:

```text
Phase 9E is a guarded intermediate result, not a final solution.
Budget-aware cooldown preserved coverage and reduced worst max_same_target_streak, but late repeated assignments remain high.
Phase 9E-4B also showed high selected-target conflict / overlap / crossing diagnostics, especially for models/.
The next work should investigate conflict-aware redirect or active-task lifecycle before broad training.
```

Interpretation category:

```text
Phase 9F-0 recommendation = Route C staged hybrid
Immediate next phase = Phase 9F-1 post-budget-redirect conflict diagnostics
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline solver behavior, default scenario cooldown setting, cooldown trigger logic, cooldown mask behavior, budget model, budget parameters, or scenario YAMLs were changed.

No commit was made.

## Latest Completed Phase

Phase 9F-0: conflict-aware redirect / active-task lifecycle design plan.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
```

## Key Results

Phase 9E final conclusion preserved:

```text
budget-aware cooldown is partially promising
it preserves coverage and reduces worst max_same_target_streak
it does not eliminate late repeated assignments
it can create or expose coordination side effects
models/ playback had high selected-target conflict, inter-robot overlap, and crossing diagnostics
new budget-triggered pairs appeared after training
budget-aware cooldown remains mask-only, not active-task lifecycle
```

Route comparison:

```text
Route A conflict-aware redirect:
  useful for duplicate target selection and short-horizon ownership conflict
  cannot solve every-step re-selection semantics

Route B active-task lifecycle:
  directly addresses assignment/execution lifecycle
  likely changes action semantics, observations, reward, and evaluation

Route C staged hybrid:
  first run diagnostics, then design a minimal guardrail only if justified
  defer active-task lifecycle design until conflict attribution is clearer
```

Decision:

```text
Recommended immediate next step: Phase 9F-1 post-budget-redirect conflict diagnostics.
Reason: safer than implementing active-task lifecycle immediately, and it clarifies whether high conflict/overlap/crossing is caused by redirect choices, policy preference, or geometry/path interaction.
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
scripts/environments/summarize_phase9e4b_playback.py
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

Phase 9E-4B documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E4B_BUDGET_TRAINED_PLAYBACK_20260701.md
```

Generated Phase 9E-4B outputs:

```text
results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_models_no_cooldown_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_best_model_no_cooldown_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.csv
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.json
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/
```

Phase 9F-0 documentation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
```

## Latest Verification

Python compile:

```text
assignment_harl_wrapper.py: passed
scenario_config.py scan_mobile_manipulator_env.py: passed
evaluate_assignment_rl_playback_diagnostics.py test_assignment_cooldown_mask_smoke.py analyze_assignment_stuck_budget.py: passed
analyze_budget_cooldown_traces.py: passed
summarize_phase9e4b_playback.py: passed
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

Phase 9E-4B playback:

```text
4/4 playback runs completed
summary CSV/JSON written under results/assignment_diagnostics/
trace analyzer completed for budget-enabled playback outputs
classification = TRAIN-P
```

Phase 9F-0 design:

```text
design-only plan written
no code implemented
no training run
no playback run
no py_compile needed
git status --short:
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E / 9F-0 limitations:

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not full planner path length
budget trigger does not implement active-task lifecycle
budget state is not in actor/shared observations
Phase 9E-4B validation is playback-only on one user-trained 100k single-seed checkpoint
row-level selected-target conflict and inter-robot overlap are unavailable in assignment_history.csv
duplicate selected target is only an exact-target conflict proxy
duplicate_scans and reach_violation are unavailable in playback outputs and are only training-console context
models/ playback has high selected-target conflict/overlap/crossing diagnostics
late repeated assignment counts remain high despite max streak reduction
Phase 9F-0 is a plan only and does not implement diagnostics or guardrails
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run broad training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Phase 9F-1: post-budget-redirect conflict diagnostics.
Analyze whether conflicts after budget trigger are caused by redirect target choices, persistent policy preference, or geometry/path crossing.
No training, no playback unless a required file is missing and rerun is explicitly approved, and no behavior changes.
```

Keep comparisons anchored against:

```text
Phase 9D-3 no cooldown
Phase 9E-3A aggressive cooldown
Phase 9E-3B weak_d5_s30 and short_d3_s50
Phase 9E-3D m15 playback
Phase 9E-4B budget-trained playback
Phase 9F-0 design plan
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/PHASE9F0_CONFLICT_AWARE_OR_ACTIVE_TASK_LIFECYCLE_DESIGN_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260702/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9F0_DESIGN_PLAN_20260702.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9E4B_BUDGET_TRAINED_PLAYBACK_20260701.md
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
