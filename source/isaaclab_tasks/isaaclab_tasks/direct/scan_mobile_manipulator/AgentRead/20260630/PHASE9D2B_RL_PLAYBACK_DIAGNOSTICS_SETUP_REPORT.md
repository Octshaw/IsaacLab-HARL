# Phase 9D-2B RL Playback Diagnostics Setup Report

## 1. Scope And Boundaries

Phase 9D-2B prepared a diagnostic-only playback path for fixed N=50/M=3 assignment RL checkpoints. The goal was to reuse or mirror the existing Phase 7/8 baseline conflict, overlap, crossing, stagnation, uncovered-viewpoint, duplicate/noop, and path-cost metrics so RL checkpoint behavior can be inspected with aligned fields.

This phase did not train, tune rewards, run formal evaluation, change masks/feasibility, change solver/controller behavior, change environment dynamics, change HARL algorithms/site-packages, add handcrafted baselines, or claim learned-policy quality.

## 2. Why This Phase Was Needed

Manual playback of the Phase 9D-2 300k debug checkpoint showed three behavior issues:

- Robots often moved through the measured component/object.
- Robots often overlapped each other.
- After partial progress, robots tended to repeatedly try stuck/different viewpoints until the 300-step horizon.

Before changing rewards, masks, controller logic, or motion/collision behavior, the existing diagnostic metrics needed to be available for RL checkpoint playback.

## 3. Files Inspected

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7E_ACTUAL_BASE_MOTION_20260628.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md`
- `scripts/environments/evaluate_assignment_methods.py`
- `scripts/reinforcement_learning/harl/play_assignment.py`
- `scripts/reinforcement_learning/harl/train.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_obstacle_footprint.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py`

## 4. Files Changed

- Added `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- Added this report.
- Updated `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

No existing training, reward, mask, solver, controller, HARL, or environment-dynamics code was changed.

## 5. Baseline Metrics Reused Or Mirrored

The new script mirrors the baseline evaluator output shape and metric names where practical:

- Selected-target conflict: same target-footprint proxy threshold pattern, `2 * target_radius + target_margin`, using the scenario/env diagnostic settings.
- Inter-robot overlap: reused `unwrapped.get_inter_robot_conflict_diagnostics()` so the same robot footprint proxy settings drive overlap metrics.
- Actual base-motion crossing: mirrored the diagnostic XY segment check from previous robot base XY to current robot base XY against `component_obstacle_footprint.intersects_segment(...)`.
- Stagnation and late repeated assignments: local playback buffers track repeated selected targets after no global coverage gain.
- Uncovered viewpoints: `final_uncovered_viewpoint_ids` is written per episode.
- Duplicate/noop/path-cost metrics: duplicate selected target count, noop-when-available count/rate, selected-available mean, and selected path-cost sum/mean/max are written.
- Per-step assignment history: `assignment_history.csv` includes selected action/viewpoint, availability/feasibility, coverage gain, base/target XY, duplicate/noop flags, same-target streak, and steps since global coverage gain.

These remain proxy diagnostics. They are not physical collision checking and do not solve path planning, avoidance, or controller behavior.

## 6. Script Usage And CLI

Script:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
```

Representative CLI:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --max_steps 300 --num_episodes 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --dir <assignment_rl_model_dir> --output_dir <output_dir> --stop_on_done
```

The script loads assignment-mode Discrete/Categorical actor checkpoints and checks the fixed N=50/M=3 path:

- `num_agents = 3`
- `num_viewpoints = 50`
- `noop_id = 50`
- action spaces `Discrete(51)`
- available-actions shape `[1, 3, 51]` in the smoke

Old fixed-N=12 assignment checkpoints and old 9D continuous scan checkpoints are incompatible with this path.

## 7. Smoke Command Run

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --max_steps 300 --num_episodes 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2_debug_train_300k/seed-00001-2026-06-29-23-40-39/models --output_dir results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke --stop_on_done
```

Checkpoint used:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2_debug_train_300k/seed-00001-2026-06-29-23-40-39/models
```

This is the old 300k final `models/` checkpoint used as a debug artifact only. The old 300k `best_model/` remains polluted by pre-9D-2A logger accounting and was not used as true best-policy evidence.

## 8. Smoke Outputs

Output directory:

```text
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke
```

Files written:

```text
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/diagnostics.json
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/summary.csv
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/per_episode.csv
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/assignment_history.csv
```

Output sizes:

```text
diagnostics.json        10843 bytes
summary.csv               932 bytes
per_episode.csv          1890 bytes
assignment_history.csv 198336 bytes
```

## 9. Smoke Result Summary

Result: passed as a one-episode diagnostic wiring smoke.

Runtime summary:

- Environment initialized with N=50/M=3.
- Three actor checkpoints loaded as `action_type=Discrete`, `distribution_head=Categorical`.
- Action spaces were `{0: Discrete(51), 1: Discrete(51), 2: Discrete(51)}`.
- Reset logged `available_actions shape=(1, 3, 51)`.
- The episode completed at step 299 with `--stop_on_done`.
- `assignment_history.csv` contains 897 rows, equal to 299 steps times 3 robots.
- `summary.csv` and `per_episode.csv` had no numeric NaN/Inf values in the inspected scalar fields.

One-episode smoke metrics:

```text
final_coverage = 0.4599999785423279
coverage_auc = 0.3141133235051082
new_viewpoints_total = 23.0
duplicate_selected_target_rate = 0.06688963210702341
noop_when_available_rate = 0.1326644370122631
selected_available_mask_mean = 0.867335562987737
selected_target_conflict_rate = 0.5819397993311036
inter_robot_overlap_rate = 0.35451505016722407
actual_base_motion_intersection_rate = 0.17279821627647715
selected_path_cost_mean = 1.4980655464231203
selected_path_cost_max = 7.421009063720703
late_repeated_assignment_pattern = true
late_repeated_assignment_count = 704.0
max same_target_streak in assignment_history.csv = 278.0
max steps_since_global_coverage_gain in assignment_history.csv = 91.0
```

Final uncovered viewpoint ids:

```text
[0, 1, 2, 4, 8, 10, 11, 12, 16, 19, 20, 24, 25, 26, 28, 29, 32, 36, 39, 40, 41, 42, 43, 44, 45, 47, 48]
```

These metrics confirm that the playback diagnostic pipeline exposes the previously observed conflict/overlap/crossing/stagnation fields. They do not establish policy quality.

## 10. Validation

Python compile passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
```

Output inspection passed:

- All four expected files exist.
- `diagnostics.json` records `num_agents=3`, `num_viewpoints=50`, `noop_id=50`, and `available_actions_shape=[1, 3, 51]`.
- `summary.csv` and `per_episode.csv` include coverage, conflict, overlap, crossing, duplicate/noop, path-cost, and late repeated-assignment fields.
- `assignment_history.csv` includes per-step selected action/viewpoint, availability/feasibility, coverage gain, robot/target XY, duplicate/noop, same-target streak, and steps-since-gain fields.

Repository checks:

```text
git diff --check = passed, with TASK_PROGRESS.md LF/CRLF warning only
git status --short = expected Phase 9D-2B script/report/progress changes only
```

## 11. Explicit Limitations

- Proxy diagnostics only.
- No physical collision-checking claim.
- No path-planning or avoidance claim.
- One-episode smoke only.
- The old 300k final `models/` checkpoint is only a debug artifact.
- The old 300k `best_model/` remains polluted by pre-9D-2A `Total_Reward` accounting and is not true best-policy evidence.
- No learned-policy quality claim.

## 12. Explicit Non-Changes

- No training.
- No reward formula/default-scale changes.
- No observation semantic changes.
- No mask, feasibility, static feasibility, solver, controller, robot motion, environment dynamics, local avoidance, path-planning, retry/fallback, cooldown, or HARL algorithm changes.
- No installed HARL site-package changes.
- No formal evaluation.
- No checkpoint-quality claim.
- No commit.

## 13. Next Recommendation

After commit, use this diagnostic script on a post-logger-fix 100k or 300k checkpoint. Compare RL against baseline random/nearest/greedy using aligned metrics. Only then decide whether scoped cooldown, path-cost, crossing, overlap, mask, controller, or path-planning mechanisms are justified.

Do not proceed directly to longer training before behavior diagnostics.
