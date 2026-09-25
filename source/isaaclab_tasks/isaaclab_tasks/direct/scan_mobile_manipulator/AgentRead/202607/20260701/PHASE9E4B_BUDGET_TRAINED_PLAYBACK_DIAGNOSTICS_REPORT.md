# Phase 9E-4B Budget-Aware Trained Checkpoint Playback Diagnostics

Date: 2026-07-01

## 1. Scope and Boundaries

This phase ran playback diagnostics for the user-run Phase 9E-4A budget-aware cooldown trained checkpoint.

No reward formulas/default scales, `Total_Reward` whitelist, actor/shared observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller/solver/path planning/collision/local avoidance/environment dynamics, HARL algorithms, installed site-packages, baseline solver behavior, default scenario cooldown setting, cooldown trigger logic, cooldown mask behavior, budget model, budget parameters, or scenario YAMLs were changed.

## 2. No-Training Statement

No training was run in Phase 9E-4B. This phase used existing Phase 9E-4A checkpoints only.

## 3. Phase 9E-4A Training Context

Training run:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47
```

Console/TensorBoard context:

```text
console log found = true
training completed = true
last console progress = episodes 330/333, timesteps 99000/100000
models exists = true
best_model exists = true
TensorBoard scalar tags = 63
non-finite scalar count = 0
final coverage_ratio = 0.3778
final assignment_rl_reward/final_reward_mean = 0.4179305
final Total_Reward = 626.8958
Total_Reward / final_reward_mean = 1500.0
final assignment_rl.noop_count = 0.00733
final assignment_cooldown.budget_trigger_count = 0.856
final assignment_cooldown.suppressed_action_count_mean = 0.06333
final duplicate_scans = 0.04244
final reach_violation = 0.03089
```

Training scalars are context only. Playback is required for max same-target streak, late repeated targets, and conflict/spatial diagnostics.

## 4. Checkpoint Path Inspected

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/best_model
```

Both checkpoint directories were present.

## 5. Playback Commands

Command template:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config <SCENARIO_PATH> --dir <CHECKPOINT_DIR> --num_episodes 5 --max_steps 300 --output_dir <OUTPUT_DIR> --stop_on_done
```

Concrete runs:

```text
models + budget:
  scenario = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
  dir = .../seed-00001-2026-07-01-14-40-47/models
  output = results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback
  log = results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback_console.log

best_model + budget:
  scenario = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
  dir = .../seed-00001-2026-07-01-14-40-47/best_model
  output = results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback
  log = results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback_console.log

models + no cooldown:
  scenario = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
  dir = .../seed-00001-2026-07-01-14-40-47/models
  output = results/assignment_diagnostics/phase9e4b_budget_trained_models_no_cooldown_playback
  log = results/assignment_diagnostics/phase9e4b_budget_trained_models_no_cooldown_playback_console.log

best_model + no cooldown:
  scenario = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
  dir = .../seed-00001-2026-07-01-14-40-47/best_model
  output = results/assignment_diagnostics/phase9e4b_budget_trained_best_model_no_cooldown_playback
  log = results/assignment_diagnostics/phase9e4b_budget_trained_best_model_no_cooldown_playback_console.log
```

## 6. Playback Completion Status

All four playback diagnostics completed successfully.

## 7. Four-Run Summary

`late targets` are the mode of selected non-noop targets in the last 100 playback steps.

| Run | Coverage | AUC | New VPs | Max Streak | Late Targets | Final Targets | NoopAvail | Conflict | Overlap | Crossing | Duplicate | Budget Triggers | Suppressed |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| models + budget | 0.50 | 0.3304 | 25 | 112 | r0->24, r1->36, r2->44 | r0->25, r1->36, r2->44 | 0.0000 | 1.0903 | 0.4482 | 0.2553 | 0.0836 | 6 | 0.1003 |
| best_model + budget | 0.48 | 0.3113 | 24 | 110 | r0->15, r1->36, r2->11 | r0->25, r1->36, r2->24 | 0.0000 | 0.2642 | 0.0870 | 0.0948 | 0.0401 | 14 | 0.2341 |
| models + no cooldown | 0.50 | 0.3304 | 25 | 140 | r0->24, r1->36, r2->44 | r0->25, r1->36, r2->44 | 0.0000 | 1.0903 | 0.4482 | 0.2553 | 0.0268 | 0 | 0.0000 |
| best_model + no cooldown | 0.46 | 0.3108 | 23 | 189 | r0->15, r1->36, r2->11 | r0->15, r1->36, r2->11 | 0.0000 | 0.1271 | 0.0635 | 0.0981 | 0.0401 | 0 | 0.0000 |

Playback does not expose `duplicate_scans` or `reach_violation`; those are available in the Phase 9E-4A training console only.

## 8. Reference Comparison

### Phase 9D-3 No-Cooldown Trained Reference

| Checkpoint | Phase 9D-3 Coverage | Phase 9E-4B Best Coverage | Phase 9D-3 Max Streak | Phase 9E-4B Best Max Streak |
| --- | ---: | ---: | ---: | ---: |
| models | 0.50 | 0.50 | 282 | 112 |
| best_model | 0.40 | 0.48 | 282 | 110 |

Coverage is preserved or improved relative to Phase 9D-3, and max same-target streak is substantially reduced. AUC is lower than Phase 9D-3 for this trained policy (`models` 0.3304 vs 0.3675, `best_model` 0.3113 vs 0.3234), so this is not a clean overall improvement.

### Phase 9E-3A Aggressive Runtime Cooldown Reference

Aggressive cooldown collapsed no-cooldown checkpoint playback coverage to 0.02/0.04. Phase 9E-4B does not show that failure mode: coverage is 0.50/0.48 with budget playback and noop_when_available remains 0.0.

### Phase 9E-3B Weak Runtime Cooldown Candidates

Compared with weak runtime cooldown candidates, Phase 9E-4B budget-trained playback preserves coverage better but leaves higher max streak:

```text
weak_d5_s30:
  models: coverage 0.44, max streak 30
  best_model: coverage 0.28, max streak 30

short_d3_s50:
  models: coverage 0.46, max streak 50
  best_model: coverage 0.38, max streak 50

Phase 9E-4B budget-trained + budget:
  models: coverage 0.50, max streak 112
  best_model: coverage 0.48, max streak 110
```

### Phase 9E-3D No-Cooldown Trained + Budget Runtime Playback Reference

Phase 9E-3D budget runtime playback on the no-cooldown trained checkpoint had:

```text
models: coverage 0.50, AUC 0.3675, max streak 110, budget triggers 20
best_model: coverage 0.46, AUC 0.3387, max streak 110, budget triggers 22
```

Phase 9E-4B budget-trained playback has comparable coverage and max streak, fewer budget triggers, but lower AUC:

```text
models + budget: coverage 0.50, AUC 0.3304, max streak 112, budget triggers 6
best_model + budget: coverage 0.48, AUC 0.3113, max streak 110, budget triggers 14
```

## 9. With-Budget vs No-Cooldown Cross-Playback Interpretation

This most closely matches Case A: trained policy is useful, and the runtime budget mask still helps.

Evidence:

```text
models:
  budget playback: coverage 0.50, max streak 112
  no-cooldown playback: coverage 0.50, max streak 140

best_model:
  budget playback: coverage 0.48, max streak 110
  no-cooldown playback: coverage 0.46, max streak 189
```

The policy does not collapse without cooldown, so it is not purely dependent on the mask. However, disabling cooldown worsens max streak, especially for `best_model`.

## 10. Stuck-Target Analysis

Max same-target streak is reduced from the Phase 9D-3 282 reference:

```text
models + budget: 112
models + no cooldown: 140
best_model + budget: 110
best_model + no cooldown: 189
```

Late repeated assignment counts remain high:

```text
models + budget: 765
models + no cooldown: 777
best_model + budget: 790
best_model + no cooldown: 811
```

The budget-trained policy improves the worst streak length, but it does not eliminate late repeated target behavior.

## 11. Cooldown and Budget Trigger Analysis

Budget playback trigger counts are much lower than the Phase 9E-3D runtime-only budget playback reference:

```text
models: 6 vs Phase 9E-3D 20
best_model: 14 vs Phase 9E-3D 22
```

Trace inspection on the Phase 9E-4B budget playback found new budget-triggered pairs, not the old Phase 9E-3C known stuck pairs:

```text
models:
  total trigger rows = 30
  unique triggered pairs = r1->36, r2->44
  old known-pair trigger fraction = 0.00
  triggers followed by coverage gain within 20 steps = 0/30
  returned to triggered target later = 30/30

best_model:
  total trigger rows = 70
  unique triggered pairs = r0->15, r1->36, r2->11
  old known-pair trigger fraction = 0.00
  triggers followed by coverage gain within 20 steps = 25/70
  returned to triggered target later = 65/70
```

This suggests training changed the late stuck/over-budget pairs rather than simply fixing all late retry behavior.

## 12. Conflict / Duplicate / Spatial Diagnostics

The main concern is spatial/coordination side effects, especially for `models`.

```text
models + budget:
  selected_target_conflict_rate = 1.0903
  inter_robot_overlap_rate = 0.4482
  base_motion_crossing_rate = 0.2553
  duplicate_selected_target_rate = 0.0836

best_model + budget:
  selected_target_conflict_rate = 0.2642
  inter_robot_overlap_rate = 0.0870
  base_motion_crossing_rate = 0.0948
  duplicate_selected_target_rate = 0.0401
```

For `models`, conflict and overlap are substantially worse than the Phase 9D-3 reference and the Phase 9E-3D runtime-budget reference. For `best_model`, spatial diagnostics are more manageable but still not cleanly better than all references.

## 13. Trace Inspection Result

Trace inspection was performed with:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\analyze_budget_cooldown_traces.py --models_dir results\assignment_diagnostics\phase9e4b_budget_trained_models_with_budget_playback --best_model_dir results\assignment_diagnostics\phase9e4b_budget_trained_best_model_with_budget_playback --output_dir results\assignment_diagnostics\phase9e4b_budget_trained_trace_inspection --summary_filename phase9e4b_budget_trained_trace_summary.json --notes_filename phase9e4b_trace_notes.md
```

Outputs:

```text
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/budget_trigger_events.csv
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/budget_trigger_windows.csv
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/post_trigger_redirect_summary.csv
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/conflict_after_trigger_summary.csv
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/phase9e4b_budget_trained_trace_summary.json
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/phase9e4b_trace_notes.md
```

The trace analyzer preserves the Phase 9E-3C known-pair comparison, so Phase 9E-4B triggered pairs are correctly reported as non-known relative to the old no-cooldown checkpoint evidence.

## 14. Classification

Classification: `TRAIN-P`.

Reason:

```text
Coverage is acceptable and preserved.
Max same-target streak is substantially reduced from 282.
Noop_when_available remains 0.0.
Runtime budget cooldown still helps reduce max streak.
However, late repeated assignments remain high, new budget-triggered pairs appear after training, and models/ has high conflict/overlap/crossing diagnostics.
```

This is partially promising, but not strong enough to treat budget-aware cooldown training as a final Phase 9E outcome.

## 15. Known Limitations

- This is one 100k single-seed debug run.
- Playback is deterministic/repeated across the five episodes in these diagnostics, so per-episode variance is not informative.
- `duplicate_scans` and `reach_violation` are not present in playback diagnostics; training-console values are reported only as context.
- Row-level selected-target conflict and inter-robot overlap are not present in `assignment_history.csv`; trace inspection uses duplicate-selected-target and base-motion crossing proxies.
- The budget-trained policy changes the late trigger pairs, so old Phase 9E-3C known-pair matching is a reference, not a correctness criterion.

## 16. Recommended Follow-Up

Budget-aware cooldown training is partially promising. Recommended next step: commit diagnostic implementation and reports, but treat the mechanism as a guarded intermediate result.

Before broad training, investigate conflict-aware redirect or active-task lifecycle design, because the current budget-aware mask reduces worst streaks while leaving substantial repeated-target and coordination side effects.
