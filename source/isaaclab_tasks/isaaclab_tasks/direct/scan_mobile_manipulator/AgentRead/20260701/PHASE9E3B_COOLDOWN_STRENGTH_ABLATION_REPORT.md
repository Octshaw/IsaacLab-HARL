# Phase 9E-3B Cooldown Strength Ablation Report

Date: 2026-07-01

## 1. Scope and Boundaries

Phase 9E-3B ran a playback-only cooldown strength ablation on the Phase 9D-3 no-cooldown 100k checkpoint.

Goal:

```text
Test whether weaker runtime cooldown configurations can reduce repeated same-target streaks without collapsing coverage.
```

This phase did not modify reward formulas, reward scales/defaults, `Total_Reward` accounting, actor/shared observation dimensions, `available_actions` shape, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithms, installed site-packages, baseline behavior, the default scenario, or core cooldown implementation logic.

The default scenario and existing aggressive cooldown debug scenario were not edited.

## 2. No-Training Statement

No training was run in Phase 9E-3B.

All results are deterministic playback diagnostics from existing checkpoints:

```text
num_envs = 1
num_episodes = 5
max_steps = 300
stop_on_done = true
headless = true
device = cuda:0
```

## 3. Checkpoints Used

Phase 9D-3 no-cooldown 100k run:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
```

Checkpoint dirs:

```text
models/
best_model/
```

## 4. Ablation Scenario Files Created

New debug-only scenarios:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s30.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s50.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_short_d3_s50.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_ablate_strict_attempt20_d5_s50.yaml
```

They are based on:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

Only cooldown strength values and diagnostic labels/result filenames were changed. Geometry, robots, viewpoints, diagnostics, task setup, and non-cooldown config remain inherited from the aggressive debug scenario.

Cooldown settings:

| variant | trigger attempts | same-target streak | steps since global gain | duration |
|---|---:|---:|---:|---:|
| `weak_d5_s30` | 10 | 30 | 30 | 5 |
| `weak_d5_s50` | 15 | 50 | 50 | 5 |
| `short_d3_s50` | 15 | 50 | 50 | 3 |
| `strict_attempt20_d5_s50` | 20 | 50 | 50 | 5 |

All variants keep:

```text
enabled = true
scope = per_robot_target
require_uncovered = true
require_available = true
require_feasible = true
require_no_global_gain = true
clear_on_covered = true
apply_to_action_mask = true
log_diagnostics = true
```

## 5. Playback Commands

Command template:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config <SCENARIO_PATH> --dir <CHECKPOINT_DIR> --num_episodes 5 --max_steps 300 --output_dir <OUTPUT_DIR> --stop_on_done
```

Concrete run table:

| run | scenario | checkpoint | output dir |
|---|---|---|---|
| `weak_d5_s30_models` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s30.yaml` | Phase 9D-3 `models/` | `results/assignment_diagnostics/phase9e3b_weak_d5_s30_models_playback` |
| `weak_d5_s30_best_model` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s30.yaml` | Phase 9D-3 `best_model/` | `results/assignment_diagnostics/phase9e3b_weak_d5_s30_best_model_playback` |
| `weak_d5_s50_models` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s50.yaml` | Phase 9D-3 `models/` | `results/assignment_diagnostics/phase9e3b_weak_d5_s50_models_playback` |
| `weak_d5_s50_best_model` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_weak_d5_s50.yaml` | Phase 9D-3 `best_model/` | `results/assignment_diagnostics/phase9e3b_weak_d5_s50_best_model_playback` |
| `short_d3_s50_models` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_short_d3_s50.yaml` | Phase 9D-3 `models/` | `results/assignment_diagnostics/phase9e3b_short_d3_s50_models_playback` |
| `short_d3_s50_best_model` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_short_d3_s50.yaml` | Phase 9D-3 `best_model/` | `results/assignment_diagnostics/phase9e3b_short_d3_s50_best_model_playback` |
| `strict_attempt20_d5_s50_models` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_strict_attempt20_d5_s50.yaml` | Phase 9D-3 `models/` | `results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_models_playback` |
| `strict_attempt20_d5_s50_best_model` | `algorithm_proxy_component_mesh_assignment_cooldown_ablate_strict_attempt20_d5_s50.yaml` | Phase 9D-3 `best_model/` | `results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_best_model_playback` |

Console logs follow the same output name plus `_console.log`.

Queue status:

```text
results/assignment_diagnostics/phase9e3b_playback_queue_status.csv
results/assignment_diagnostics/phase9e3b_playback_queue.exitcode
```

Summary outputs:

```text
results/assignment_diagnostics/phase9e3b_cooldown_ablation_summary.json
results/assignment_diagnostics/phase9e3b_cooldown_ablation_summary.csv
results/assignment_diagnostics/phase9e3b_trace_notes.md
```

## 6. Completion Status

All eight playback runs completed with exit code `0`.

| run | exit code |
|---|---:|
| `weak_d5_s30_models` | 0 |
| `weak_d5_s30_best_model` | 0 |
| `weak_d5_s50_models` | 0 |
| `weak_d5_s50_best_model` | 0 |
| `short_d3_s50_models` | 0 |
| `short_d3_s50_best_model` | 0 |
| `strict_attempt20_d5_s50_models` | 0 |
| `strict_attempt20_d5_s50_best_model` | 0 |

## 7. Summary Table for `models/`

| variant | final coverage | coverage AUC | new viewpoints | max streak | late repeated count | noop avail | suppressed | active | triggers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Phase 9D-3 no cooldown ref | 0.5000 | 0.3675 | 25 | 282 | n/a | 0.0000 | 0.00 | 0.00 | 0 |
| Phase 9E-3A aggressive ref | 0.0200 | 0.0189 | 1 | 10 | 81 | 0.0000 | 47.90 | 48.06 | 747 |
| `weak_d5_s30` | 0.4400 | 0.3272 | 22 | 30 | 167 | 0.0000 | 9.04 | 9.09 | 552 |
| `weak_d5_s50` | 0.6000 | 0.4106 | 30 | 50 | 297 | 0.0000 | 6.08 | 6.12 | 372 |
| `short_d3_s50` | 0.4600 | 0.3604 | 23 | 50 | 241 | 0.0000 | 4.86 | 4.89 | 490 |
| `strict_attempt20_d5_s50` | 0.4200 | 0.3441 | 21 | 50 | 324 | 0.0000 | 5.98 | 6.02 | 366 |

Late/final targets for `models/`:

| variant | representative late targets | final selected targets |
|---|---|---|
| Phase 9D-3 no cooldown ref | r0->44, r1->44, r2->15 | n/a |
| `weak_d5_s30` | r0->44, r1->29, r2->25 | r0->34, r1->27, r2->32 |
| `weak_d5_s50` | r0->11, r1->20, r2->4 | r0->35, r1->3, r2->35 |
| `short_d3_s50` | r0->2, r1->29, r2->0 | r0->28, r1->48, r2->3 |
| `strict_attempt20_d5_s50` | r0->28, r1->29, r2->35 | r0->2, r1->27, r2->35 |

## 8. Summary Table for `best_model/`

| variant | final coverage | coverage AUC | new viewpoints | max streak | late repeated count | noop avail | suppressed | active | triggers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Phase 9D-3 no cooldown ref | 0.4000 | 0.3234 | 20 | 282 | n/a | 0.0000 | 0.00 | 0.00 | 0 |
| Phase 9E-3A aggressive ref | 0.0400 | 0.0374 | 2 | 10 | 80 | 0.1371 | 41.50 | 41.63 | 646 |
| `weak_d5_s30` | 0.2800 | 0.2334 | 14 | 30 | 152 | 0.0000 | 9.83 | 9.88 | 599 |
| `weak_d5_s50` | 0.3400 | 0.2932 | 17 | 50 | 251 | 0.0000 | 7.79 | 7.84 | 475 |
| `short_d3_s50` | 0.3800 | 0.3169 | 19 | 50 | 224 | 0.0000 | 5.34 | 5.37 | 538 |
| `strict_attempt20_d5_s50` | 0.4000 | 0.3185 | 20 | 50 | 340 | 0.0000 | 6.21 | 6.25 | 380 |

Late/final targets for `best_model/`:

| variant | representative late targets | final selected targets |
|---|---|---|
| Phase 9D-3 no cooldown ref | r0->39, r1->0, r2->15 | n/a |
| `weak_d5_s30` | r0->4, r1->27, r2->0 | r0->43, r1->29, r2->19 |
| `weak_d5_s50` | r0->39, r1->0, r2->47 | r0->7, r1->29, r2->25 |
| `short_d3_s50` | r0->34, r1->27, r2->0 | r0->4, r1->48, r2->3 |
| `strict_attempt20_d5_s50` | r0->35, r1->29, r2->0 | r0->4, r1->34, r2->47 |

## 9. Comparison Against Phase 9D-3 No-Cooldown Reference

Compared with no cooldown:

- All weak variants reduced max same-target streak from 282 to 30 or 50.
- `models/` coverage stayed at or above 0.42 for all weak variants; `weak_d5_s50` improved it to 0.60.
- `best_model/` coverage stayed at or above the minimum 0.25 criterion for all weak variants; `short_d3_s50` and `strict_attempt20_d5_s50` preserved near-reference coverage at 0.38 and 0.40.
- Noop-when-available remained 0.0 for all weak variants.
- Suppressed counts dropped from the aggressive 41-48 range to about 4.9-9.8.

Spatial diagnostics are mixed:

| variant | checkpoint | target conflict | overlap | crossing | duplicate target |
|---|---|---:|---:|---:|---:|
| Phase 9D-3 ref | `models/` | 0.2910 | 0.2375 | 0.0814 | 0.1538 |
| `weak_d5_s30` | `models/` | 0.5184 | 0.4214 | 0.1828 | 0.1405 |
| `weak_d5_s50` | `models/` | 0.7023 | 0.5418 | 0.0502 | 0.1706 |
| `short_d3_s50` | `models/` | 0.5117 | 0.1104 | 0.3166 | 0.1538 |
| `strict_attempt20_d5_s50` | `models/` | 0.6054 | 0.1405 | 0.3824 | 0.0401 |
| Phase 9D-3 ref | `best_model/` | 0.0000 | 0.0702 | 0.0502 | 0.0000 |
| `weak_d5_s30` | `best_model/` | 0.3913 | 0.3144 | 0.3902 | 0.0669 |
| `weak_d5_s50` | `best_model/` | 0.4548 | 0.1171 | 0.2954 | 0.0134 |
| `short_d3_s50` | `best_model/` | 0.3278 | 0.1003 | 0.2999 | 0.0167 |
| `strict_attempt20_d5_s50` | `best_model/` | 0.4181 | 0.0803 | 0.3200 | 0.0368 |

The weak cooldowns solve the coverage-collapse problem, but several spatial-risk proxies worsen relative to the no-cooldown reference. This keeps the result diagnostic rather than final.

## 10. Comparison Against Phase 9E-3A Aggressive Cooldown Reference

The weak variants are dramatically less destructive than the aggressive cooldown reference.

For `models/`:

```text
aggressive: coverage 0.02, max streak 10, suppressed about 47.9
weak variants: coverage 0.42-0.60, max streak 30-50, suppressed about 4.9-9.0
```

For `best_model/`:

```text
aggressive: coverage 0.04, max streak 10, suppressed about 41.5
weak variants: coverage 0.28-0.40, max streak 30-50, suppressed about 5.3-9.8
```

The aggressive mask was over-masking. The weaker configurations preserve action diversity enough to avoid the Phase 9E-3A collapse.

## 11. Cooldown Intervention Metrics

| variant | checkpoint | trigger events total | unique robot-target pairs | failed attempt mean | failed attempt max | late suppressed mean |
|---|---|---:|---:|---:|---:|---:|
| `weak_d5_s30` | `models/` | 2760 | 27 | 7.0669 | 16 | 4.33 |
| `weak_d5_s30` | `best_model/` | 2995 | 22 | 7.5652 | 20 | 4.68 |
| `weak_d5_s50` | `models/` | 1860 | 21 | 5.2007 | 15 | 3.53 |
| `weak_d5_s50` | `best_model/` | 2375 | 19 | 6.0769 | 15 | 4.40 |
| `short_d3_s50` | `models/` | 2450 | 15 | 5.6589 | 15 | 2.77 |
| `short_d3_s50` | `best_model/` | 2690 | 13 | 6.0669 | 15 | 2.94 |
| `strict_attempt20_d5_s50` | `models/` | 1830 | 17 | 5.5351 | 20 | 3.72 |
| `strict_attempt20_d5_s50` | `best_model/` | 1900 | 17 | 5.8027 | 20 | 3.64 |

Selected pair active count was `0` for all variants, meaning cooldown-active selected pairs were suppressed before selection.

## 12. Best Candidate

Best guardrail candidate: `weak_d5_s30`.

Reason:

```text
models:     final_coverage 0.44, max_streak 30, noop 0.0, suppressed 9.04
best_model: final_coverage 0.28, max_streak 30, noop 0.0, suppressed 9.83
```

It is the only ablation with max streak 30 rather than 50 while still meeting the minimum coverage floors and keeping noop-when-available at 0.0.

Coverage-friendlier alternatives:

- `weak_d5_s50`: best `models/` coverage, 0.60, but higher spatial conflict/overlap and streak 50.
- `short_d3_s50`: balanced `best_model/` coverage, 0.38, lowest suppression among the non-strict variants, and streak 50.

None should be promoted directly to a final algorithm. The spatial diagnostics still need follow-up.

## 13. Interpretation Category

Category: **S. Promising weak guardrail**, with caveats.

The best weak cooldown variants:

- preserve reasonable coverage,
- reduce max same-target streak far below 282,
- keep noop-when-available at 0.0,
- keep suppressed counts far below the aggressive 41-48 range.

Caveat:

Spatial side-effect metrics are mixed, especially selected-target conflict and base-motion crossing. This phase supports a weaker cooldown direction, not a finished design.

This does not prove targets are unreachable. It only evaluates runtime action-mask cooldown strength.

## 14. Known Limitations

- Playback-only deterministic diagnostics; not formal stochastic evaluation.
- No training was performed with the weak variants.
- The tested policy was trained without cooldown.
- Cooldown remains global-coverage-gain based, with no robot-target-specific attribution.
- Cooldown state is still not part of observations.
- The weak variants were hand-picked threshold/duration probes, not a full grid search.
- Spatial diagnostics are proxies and need careful interpretation before using any variant in training.

## 15. Recommended Follow-Up

Do not run 100k training yet.

Recommended Phase 9E-3C:

```text
Design a small, bounded validation plan around weak_d5_s30 and short_d3_s50.
```

Suggested next diagnostics before training:

- replay `weak_d5_s30` and `short_d3_s50` on a second seed/checkpoint if available,
- inspect assignment history around spatial conflicts and crossings,
- consider adding a cap on concurrently cooled robot-target pairs per robot,
- consider a stricter trigger that combines streak and failed attempts rather than either signal becoming too broad,
- define a tiny-training smoke only after the runtime guardrail behavior is accepted.

No follow-up was implemented in Phase 9E-3B.
