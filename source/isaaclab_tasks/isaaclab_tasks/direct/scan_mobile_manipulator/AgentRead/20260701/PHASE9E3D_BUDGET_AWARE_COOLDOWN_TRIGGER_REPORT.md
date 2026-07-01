# Phase 9E-3D Budget-Aware Cooldown Trigger Report

## 1. Scope and Boundaries

Phase 9E-3D implemented a config-gated budget-aware cooldown trigger for Assignment RL and validated it with playback only.

No training was run.

No reward formulas, reward scales/defaults, Total_Reward whitelist, actor/shared observation dimensions, `available_actions` shape, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithms, installed site-packages, baseline solver behavior, or default scenario cooldown setting were changed.

## 2. No-Training Statement

This phase used existing Phase 9D-3 no-cooldown checkpoints only:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/best_model
```

## 3. Phase 9E-3C Motivation

Phase 9E-3C showed that pure same-target streak is not enough to identify true stuck-target retry:

| Source | Long same-target segments >= 10 | Completed long segments | Over-budget no-completion segments | Recovered late stuck pairs |
|---|---:|---:|---:|---|
| Phase 9D-3 models | 70 | 45 | 15 | `r0->44`, `r1->44`, `r2->15` |
| Phase 9D-3 best_model | 40 | 25 | 15 | `r0->39`, `r1->0`, `r2->15` |
| Aggressive cooldown | max segment length 10 | n/a | 0 | threshold 10 fired inside budget |

Interpretation preserved from Phase 9E-3C: pure streak cooldown suppresses normal multi-step persistence before over-budget stuck evidence appears.

## 4. Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

New scenario files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m10_slack0_d5.yaml
```

The default scenario `algorithm_proxy_component_mesh.yaml` was not edited and has no cooldown block; cooldown remains disabled by env defaults.

## 5. Config Fields Added

Defaults preserve existing behavior:

```text
assignment_cooldown_trigger_mode: streak
assignment_cooldown_budget_multiplier: 1.5
assignment_cooldown_budget_slack_steps: 5
assignment_cooldown_budget_min_streak: 10
assignment_cooldown_budget_require_no_global_gain: true
assignment_cooldown_budget_require_uncovered: true
assignment_cooldown_budget_require_available: true
assignment_cooldown_budget_require_feasible: true
```

Allowed trigger modes:

```text
streak
budget
budget_and_streak
```

Existing aggressive and weak cooldown scenarios remain streak-mode unless explicitly changed.

## 6. Budget Model and Cost Source

Implementation model:

```text
expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)
budget_steps = ceil(expected_steps * assignment_cooldown_budget_multiplier + assignment_cooldown_budget_slack_steps)
```

The wrapper uses `problem["cost_matrix"]` through `_selected_path_cost(...)`, matching the playback `selected_path_cost` source. In the current env this is scanner-to-viewpoint Euclidean distance, not a full planned path length.

Robot step values come from `cfg.max_base_xy_step` when available. For the current fixed M=3 config they are:

```text
robot_0: 0.08
robot_1: 0.10
robot_2: 0.06
```

The initial cost and budget are frozen at the first selection in a contiguous same robot-target segment.

## 7. Wrapper State Added

Budget-aware tracking is wrapper-local:

```text
_budget_attempt_target: [num_envs, num_agents]
_budget_attempt_steps: [num_envs, num_agents]
_budget_attempt_initial_cost: [num_envs, num_agents]
_budget_attempt_expected_steps: [num_envs, num_agents]
_budget_attempt_budget_steps: [num_envs, num_agents]
_assignment_cooldown_budget_trigger_count: [num_envs]
_assignment_cooldown_budget_over_budget_selected_count: [num_envs]
_last_budget_attempt_steps_for_selected_pair: [num_envs, num_agents]
_last_budget_steps_for_selected_pair: [num_envs, num_agents]
_last_budget_expected_steps_for_selected_pair: [num_envs, num_agents]
_last_budget_ratio_for_selected_pair: [num_envs, num_agents]
_last_budget_triggered_by_budget: [num_envs, num_agents]
```

State clears on full reset, done-env partial reset, noop selection, target change, covered target, and cooldown trigger for the selected pair.

## 8. Trigger Logic

`streak` mode is the existing Phase 9E-1 behavior.

`budget` mode triggers when:

```text
same-pair attempt_steps >= budget_steps
AND selected target remains uncovered, if required
AND selected target was available in the pre-step filtered mask, if required
AND selected target was feasible, if required
AND no global coverage gain occurred, if required
```

`budget_and_streak` adds:

```text
same_target_streak >= assignment_cooldown_budget_min_streak
```

Once cooldown is active, mask filtering is unchanged: only the selected robot-target pair is suppressed, the same target remains available to other robots, and noop remains available.

## 9. Smoke Test Result

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_cooldown_mask_smoke.py --result_file results\assignment_diagnostics\phase9e3d_budget_cooldown_mask_smoke.json
```

Result:

```text
passed
actor obs shape: [2, 909]
shared obs shape: [2, 3, 2727]
available_actions shape: [2, 3, 51]
budget trigger waited until budget exhaustion: true
budget trigger masked selected pair only: true
noop remained available: true
reset cleared budget state: true
```

## 10. Playback Commands

Template:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config <SCENARIO_PATH> --dir <CHECKPOINT_DIR> --num_episodes 5 --max_steps 300 --output_dir <OUTPUT_DIR> --stop_on_done
```

Completed runs:

| Variant | Checkpoint | Output |
|---|---|---|
| `budget_m15_slack5_d5` | `models/` | `results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback` |
| `budget_m15_slack5_d5` | `best_model/` | `results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback` |
| `budget_m10_slack0_d5` | `models/` | `results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_models_playback` |
| `budget_m10_slack0_d5` | `best_model/` | `results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_best_model_playback` |

Console logs were saved beside the output directories with `_console.log` suffixes.

## 11. Playback Summary Table

Compact summary files:

```text
results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.csv
results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.json
```

| Variant | Checkpoint | Final Coverage | Coverage AUC | Max Streak | Noop When Available | Conflict | Overlap | Crossing | Suppressed | Budget Triggers |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `m15_slack5_d5` | `models` | 0.50 | 0.3675 | 110 | 0.0000 | 0.4381 | 0.2241 | 0.0814 | 0.3244 | 20 |
| `m15_slack5_d5` | `best_model` | 0.46 | 0.3387 | 110 | 0.0000 | 0.2274 | 0.1037 | 0.1126 | 0.3679 | 22 |
| `m10_slack0_d5` | `models` | 0.48 | 0.3528 | 93 | 0.0000 | 0.3512 | 0.2609 | 0.0814 | 0.5217 | 32 |
| `m10_slack0_d5` | `best_model` | 0.42 | 0.3224 | 93 | 0.0000 | 0.2107 | 0.1605 | 0.1126 | 0.5485 | 34 |

## 12. Comparison Against References

Phase 9D-3 no-cooldown reference:

| Checkpoint | Final Coverage | Coverage AUC | Max Streak | Noop |
|---|---:|---:|---:|---:|
| `models` | 0.50 | 0.3675 | 282 | 0.0000 |
| `best_model` | 0.40 | 0.3234 | 282 | 0.0000 |

Phase 9E-3A aggressive cooldown reference:

| Checkpoint | Final Coverage | Coverage AUC | Max Streak | Noop | Suppressed |
|---|---:|---:|---:|---:|---:|
| `models` | 0.02 | 0.0189 | 10 | 0.0000 | about 47.9 |
| `best_model` | 0.04 | 0.0374 | 10 | 0.1371 | about 41.5 |

Phase 9E-3B weak candidate reference:

| Variant | Checkpoint | Final Coverage | Coverage AUC | Max Streak | Noop | Suppressed |
|---|---|---:|---:|---:|---:|---:|
| `weak_d5_s30` | `models` | 0.44 | 0.3272 | 30 | 0.0000 | 9.04 |
| `weak_d5_s30` | `best_model` | 0.28 | 0.2334 | 30 | 0.0000 | 9.83 |
| `short_d3_s50` | `models` | 0.46 | 0.3604 | 50 | 0.0000 | 4.86 |
| `short_d3_s50` | `best_model` | 0.38 | 0.3169 | 50 | 0.0000 | 5.34 |

Phase 9E-3D budget-aware result:

| Variant | Checkpoint | Coverage vs 9D-3 | Streak vs 9D-3 | Noop | Notes |
|---|---|---:|---:|---:|---|
| `m15_slack5_d5` | `models` | 0.50 -> 0.50 | 282 -> 110 | 0.0000 | coverage/AUC preserved; conflict higher |
| `m15_slack5_d5` | `best_model` | 0.40 -> 0.46 | 282 -> 110 | 0.0000 | coverage/AUC improved; conflict/crossing higher |
| `m10_slack0_d5` | `models` | 0.50 -> 0.48 | 282 -> 93 | 0.0000 | stronger intervention, mild coverage/AUC drop |
| `m10_slack0_d5` | `best_model` | 0.40 -> 0.42 | 282 -> 93 | 0.0000 | stronger intervention, duplicate rate zero |

## 13. Budget Trigger Diagnostics

| Variant | Checkpoint | Budget Attempt Max | Budget Steps Max | Budget Ratio Max | Budget Over-Budget Selected | Budget Triggers |
|---|---|---:|---:|---:|---:|---:|
| `m15_slack5_d5` | `models` | 109 | 145 | 1.00 | 20 | 20 |
| `m15_slack5_d5` | `best_model` | 109 | 145 | 1.25 | 49 | 22 |
| `m10_slack0_d5` | `models` | 93 | 93 | 2.67 | 179 | 32 |
| `m10_slack0_d5` | `best_model` | 93 | 93 | 5.00 | 269 | 34 |

The main `1.5x + 5` budget trigger is the safer candidate in this playback-only phase. It reduced max streak to 110 while preserving coverage and avoiding noop bias. The strict `1.0x + 0` trigger reduced streak further to 93, but it produced more over-budget selected events and more suppression.

## 14. Interpretation Category

Category: **BA-P, partial tradeoff**.

Reason:

```text
coverage was preserved or improved
max_same_target_streak was substantially reduced from 282
noop_when_available stayed at 0.0
suppression was far below aggressive cooldown
budget diagnostics show triggers came through budget mode
but selected-target conflict and some spatial diagnostics are mixed, especially for models/
```

This does not prove any target is unreachable. It only shows that a wrapper-local cost-budget trigger is a better playback guardrail than pure streak cooldown under these fixed N=50/M=3 diagnostics.

## 15. Known Limitations

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not a planner path length
budget does not model active-task lifecycle or per-target completion ownership
budget state is not exposed to policy observations
budget validation is playback-only on one checkpoint seed
cooldown still masks actions and can perturb policy behavior
spatial diagnostics are proxy diagnostics only and do not affect controller/collision/path planning
best_model is a debug artifact and may not be a true best-policy checkpoint from older accounting context
```

## 16. Recommended Follow-Up

Do not start broad training yet.

Recommended next step:

```text
Phase 9E-3E: inspect assignment_history around budget-trigger events for m15_slack5_d5, especially steps 180-300, to verify whether suppressed pairs correspond to the Phase 9E-3C over-budget no-completion targets and to understand the increased selected-target conflict.
```

If that trace inspection is consistent, run one scoped 100k single-seed debug training with the `m15_slack5_d5` budget-aware scenario, then repeat playback diagnostics on `models/` and `best_model/`.
