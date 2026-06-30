# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9D-3 100k training and playback diagnostic analysis report is complete.

This was report-only. No code, training, reward tuning, checkpoint playback rerun, formal evaluation, mask/controller/solver/env dynamics/HARL change, or commit was performed.

## 100k Run

```text
run_dir = results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
console_log = results/assignment_diagnostics/phase9d3_debug_train_100k_after_logger_fix_console.log
```

Confirmed:

```text
assignment_rl = true
num_agents = 3
num_viewpoints = 50
noop_id = 50
action spaces = Discrete(51)
available_actions shape = [1, 3, 51]
model_dir = None, so no checkpoint was loaded
reward_accumulator_mode = exact_whitelist
reward_accumulator_keys = ["assignment_rl_reward/final_reward_mean"]
```

`Total_Reward` is clean. Late example:

```text
final_reward_mean = 0.1741243339277183
Total Reward = 261.18650089157745
0.1741243339277183 * 300 * 5 = 261.18650089157745
```

No `2e5`-scale logger pollution appeared.

## Diagnostic Outputs

```text
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/
```

Each contains:

```text
diagnostics.json
summary.csv
per_episode.csv
assignment_history.csv
```

## Key Conclusions

Deterministic playback summary:

```text
100k models:
  final_coverage = 0.50
  coverage_auc = 0.3675
  new_viewpoints = 25
  total_return_mean = -308.17
  selected_target_conflict_rate = 0.2910
  inter_robot_overlap_rate = 0.2375
  actual_base_motion_intersection_rate = 0.0814
  late repeated pattern = true
  max same_target_streak = 282
  late targets = robot_0->44, robot_1->44, robot_2->15

100k best_model:
  final_coverage = 0.40
  coverage_auc = 0.3234
  new_viewpoints = 20
  total_return_mean = -502.46
  selected_target_conflict_rate = 0.0000
  inter_robot_overlap_rate = 0.0702
  actual_base_motion_intersection_rate = 0.0502
  late repeated pattern = true
  max same_target_streak = 282
  late targets = robot_0->39, robot_1->0, robot_2->15
```

Interpretation:

- Training is numerically healthy and logger accounting is fixed.
- `models/` is better than `best_model/` for coverage and return in deterministic playback.
- `best_model/` has lower conflict/overlap/crossing but worse coverage and return.
- `models/` is cleaner than the old 300k debug artifact on conflict/overlap/crossing and slightly better on final coverage in this deterministic playback.
- Both 100k checkpoints still show severe late repeated assignment / stuck-target behavior.
- The five playback episodes are identical, so treat them as deterministic fixed-scenario playback, not independent stochastic evaluation.
- RL coverage is still far below the Phase 8 nearest/greedy baseline plateau around 45/50 coverage.

## Report

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
```

## Validation

No Python/code files were changed for Phase 9D-3, so no `py_compile` was required.

```text
git diff --check = passed, with TASK_PROGRESS.md LF/CRLF warning only
git status --short = TASK_PROGRESS modified, new Phase 9D-3 report, plus existing untracked Phase 9D-2B script/report in the local working tree
```

## Next Recommendation

```text
Phase 9E-0: design a scoped stuck-target recovery / failed-target cooldown mechanism, using Phase 9D-3 evidence.
```

Do not jump directly to longer training. First decide a narrow mechanism for repeated available/feasible targets that fail to produce coverage.

## Do Not Do

Do not commit unless explicitly asked.

Do not proceed to mechanism implementation, reward tuning, longer training, formal evaluation, checkpoint playback, old fixed-12 assignment checkpoints, old 9D continuous scan checkpoints, arbitrary-N architecture work, or new handcrafted baselines from this task.

Do not change reward formulas/default scales, observation semantics, masks, feasibility, solver/controller behavior, robot motion, environment dynamics, path planning, collision logic, cooldown, retry/fallback, HARL algorithms, or installed site-packages unless a future scoped task explicitly asks for it.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
```
