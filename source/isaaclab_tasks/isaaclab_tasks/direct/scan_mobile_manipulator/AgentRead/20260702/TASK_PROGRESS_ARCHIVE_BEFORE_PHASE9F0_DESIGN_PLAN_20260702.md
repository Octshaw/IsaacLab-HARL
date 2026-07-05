# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9E-4B is complete.

This phase ran playback diagnostics for the user-run Phase 9E-4A budget-aware cooldown trained checkpoint.

No training was run in Phase 9E-4B.

Main result:

```text
Phase 9E-4A trained policy preserved coverage and reduced max_same_target_streak versus the Phase 9D-3 282-step reference.
Runtime budget-aware cooldown still helped reduce max streak:
  models: 140 without cooldown -> 112 with budget cooldown
  best_model: 189 without cooldown -> 110 with budget cooldown
Noop_when_available stayed at 0.0 in all four playback runs.
However, late repeated assignment counts remain high and models/ has high selected-target conflict/overlap/crossing diagnostics.
```

Interpretation category:

```text
TRAIN-P
```

No reward formulas/default scales, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller/solver/path planning/collision/local avoidance/env dynamics, HARL algorithms, installed site-packages, baseline solver behavior, default scenario cooldown setting, cooldown trigger logic, cooldown mask behavior, budget model, budget parameters, or scenario YAMLs were changed.

No commit was made.

## Latest Completed Phase

Phase 9E-4B: playback diagnostics for Phase 9E-4A budget-aware trained checkpoint.

Detailed report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260701/PHASE9E4B_BUDGET_TRAINED_PLAYBACK_DIAGNOSTICS_REPORT.md
```

## Key Results

Checkpoint inspected:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47
models/ exists = true
best_model/ exists = true
```

Four-run playback summary:

```text
models + budget:
  final_coverage = 0.50
  coverage_auc = 0.3304
  max_same_target_streak = 112
  late targets = r0->24, r1->36, r2->44
  noop_when_available_rate = 0.0000
  selected_target_conflict_rate = 1.0903
  inter_robot_overlap_rate = 0.4482
  base_motion_crossing_rate = 0.2553
  budget_trigger_count = 6
  cooldown_suppressed_count = 0.1003

best_model + budget:
  final_coverage = 0.48
  coverage_auc = 0.3113
  max_same_target_streak = 110
  late targets = r0->15, r1->36, r2->11
  noop_when_available_rate = 0.0000
  selected_target_conflict_rate = 0.2642
  inter_robot_overlap_rate = 0.0870
  base_motion_crossing_rate = 0.0948
  budget_trigger_count = 14
  cooldown_suppressed_count = 0.2341

models + no cooldown:
  final_coverage = 0.50
  coverage_auc = 0.3304
  max_same_target_streak = 140
  noop_when_available_rate = 0.0000

best_model + no cooldown:
  final_coverage = 0.46
  coverage_auc = 0.3108
  max_same_target_streak = 189
  noop_when_available_rate = 0.0000
```

Cross-playback interpretation:

```text
Case A: trained policy is useful, and runtime budget mask still helps.
The policy does not collapse without cooldown, but disabling cooldown worsens max streak.
```

Trace inspection on budget playback:

```text
models:
  total budget trigger rows = 30
  unique triggered pairs = r1->36, r2->44
  triggers matching old Phase 9E-3C known stuck pairs = 0/30
  triggers followed by coverage gain within 20 steps = 0/30
  returned to triggered target later = 30/30

best_model:
  total budget trigger rows = 70
  unique triggered pairs = r0->15, r1->36, r2->11
  triggers matching old Phase 9E-3C known stuck pairs = 0/70
  triggers followed by coverage gain within 20 steps = 25/70
  returned to triggered target later = 65/70
```

Training scalar context from Phase 9E-4A:

```text
TensorBoard scalar tags = 63
non-finite scalar count = 0
final coverage_ratio = 0.3778
final assignment_rl_reward/final_reward_mean = 0.4179305
final Total_Reward = 626.8958
Total_Reward / final_reward_mean = 1500.0
final assignment_rl.noop_count = 0.00733
final assignment_cooldown.budget_trigger_count = 0.856
final assignment_cooldown.suppressed_action_count_mean = 0.06333
```

Decision:

```text
Budget-aware cooldown training is partially promising but not final.
Commit-worthy as a diagnostic/intermediate result, but broad training should wait for conflict-aware redirect or active-task lifecycle investigation.
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

Final repository checks after Phase 9E-4B docs:

```text
py_compile analyze_budget_cooldown_traces.py summarize_phase9e4b_playback.py: passed
git diff --check: failed only on pre-existing modified default scenario trailing whitespace:
  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml:17
  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml:75
  plus known LF-to-CRLF warnings
git status --short: expected Phase 9E modified/untracked files plus modified default scenario YAML
```

## Known Issues / Blockers

No current execution blocker.

Known Phase 9E-4B limitations:

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
```

## Do Not Do

Do not commit unless explicitly asked.

Do not run broad training yet.

Do not tune rewards, change reward scales/defaults, change observation dimensions, change `available_actions` shape, change static feasibility, change controller/solver/path planning/collision/local avoidance/env dynamics, modify HARL algorithms or installed site-packages, change baseline solver behavior, or enable cooldown in the default scenario.

Do not describe cooldown as proving targets are unreachable.

## Next Step

Recommended next phase:

```text
Commit diagnostic implementation and reports if desired, but treat budget-aware cooldown training as a guarded intermediate result.
Investigate conflict-aware redirect or active-task lifecycle before broad training.
```

Keep comparisons anchored against:

```text
Phase 9D-3 no cooldown
Phase 9E-3A aggressive cooldown
Phase 9E-3B weak_d5_s30 and short_d3_s50
Phase 9E-3D m15 playback
Phase 9E-4B budget-trained playback
```

## Detailed Reports / Archives

```text
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
