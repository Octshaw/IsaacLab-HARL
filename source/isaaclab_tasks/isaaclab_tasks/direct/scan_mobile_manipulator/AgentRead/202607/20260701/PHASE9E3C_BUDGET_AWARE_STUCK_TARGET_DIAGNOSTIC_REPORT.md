# Phase 9E-3C Budget-Aware Stuck-Target Diagnostic Report

Date: 2026-07-01

## 1. Scope and Boundaries

Phase 9E-3C implemented and ran diagnostics-only analysis to distinguish normal repeated target persistence from true stuck-target retry.

Hypothesis tested:

```text
Aggressive cooldown collapses coverage because it treats repeated target selection as failure evidence,
while many repeated selections are actually normal multi-step navigation/task persistence.
A better stuck signal should compare accumulated execution effort against the expected robot-target cost.
```

No training was run.

No reward formula, reward scale/default, `Total_Reward` whitelist, actor/shared observation dimension, `available_actions` shape, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithm, installed site-package, baseline behavior, default scenario cooldown setting, cooldown parameter, or cooldown implementation logic was changed.

## 2. Diagnostic Script

Added:

```text
scripts/environments/analyze_assignment_stuck_budget.py
```

The script reads existing playback `assignment_history.csv` files and emits:

```text
budget_aware_segment_summary.csv
budget_aware_source_summary.csv
budget_aware_summary.json
```

It is standalone Python and does not launch Isaac Sim.

## 3. Budget Model

`selected_path_cost` comes from `ScanMobileManipulatorEnv.get_assignment_problem()` and is scanner-to-viewpoint Euclidean distance.

Per-robot maximum base xy step from capability profiles:

```text
robot_0: 0.08 m/decision
robot_1: 0.10 m/decision
robot_2: 0.06 m/decision
```

Main budget model:

```text
expected_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)
budget_steps = ceil(expected_steps * 1.5 + 5)
```

Strict sensitivity model:

```text
budget_steps = expected_steps
```

Important limitation:

```text
assignment_history.csv field actual_base_motion_distance is an obstacle-footprint distance diagnostic,
not traveled base distance. This phase therefore uses decision-step budget as the execution-effort proxy.
```

## 4. Inputs Analyzed

The analyzer processed 12 playback histories and 32,000 contiguous non-noop same robot-target segments.

Primary inputs:

```text
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/
results/assignment_diagnostics/phase9e3a_no_cooldown_models_with_cooldown_playback/
results/assignment_diagnostics/phase9e3a_no_cooldown_best_model_with_cooldown_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s30_models_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s30_best_model_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s50_models_playback/
results/assignment_diagnostics/phase9e3b_weak_d5_s50_best_model_playback/
results/assignment_diagnostics/phase9e3b_short_d3_s50_models_playback/
results/assignment_diagnostics/phase9e3b_short_d3_s50_best_model_playback/
results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_models_playback/
results/assignment_diagnostics/phase9e3b_strict_attempt20_d5_s50_best_model_playback/
```

## 5. Commands Run

Compile:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\analyze_assignment_stuck_budget.py
```

Main analysis:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\analyze_assignment_stuck_budget.py --output_dir results\assignment_diagnostics\phase9e3c_budget_aware_stuck_diagnostics --budget_multiplier 1.5 --fixed_slack_steps 5 --trigger_thresholds 10 30 50 --history phase9d3_models=results\assignment_diagnostics\phase9d3_rl_playback_diagnostics_100k_models --history phase9d3_best_model=results\assignment_diagnostics\phase9d3_rl_playback_diagnostics_100k_best_model --history phase9e3a_aggressive_models=results\assignment_diagnostics\phase9e3a_no_cooldown_models_with_cooldown_playback --history phase9e3a_aggressive_best_model=results\assignment_diagnostics\phase9e3a_no_cooldown_best_model_with_cooldown_playback --history phase9e3b_weak_d5_s30_models=results\assignment_diagnostics\phase9e3b_weak_d5_s30_models_playback --history phase9e3b_weak_d5_s30_best_model=results\assignment_diagnostics\phase9e3b_weak_d5_s30_best_model_playback --history phase9e3b_weak_d5_s50_models=results\assignment_diagnostics\phase9e3b_weak_d5_s50_models_playback --history phase9e3b_weak_d5_s50_best_model=results\assignment_diagnostics\phase9e3b_weak_d5_s50_best_model_playback --history phase9e3b_short_d3_s50_models=results\assignment_diagnostics\phase9e3b_short_d3_s50_models_playback --history phase9e3b_short_d3_s50_best_model=results\assignment_diagnostics\phase9e3b_short_d3_s50_best_model_playback --history phase9e3b_strict_attempt20_d5_s50_models=results\assignment_diagnostics\phase9e3b_strict_attempt20_d5_s50_models_playback --history phase9e3b_strict_attempt20_d5_s50_best_model=results\assignment_diagnostics\phase9e3b_strict_attempt20_d5_s50_best_model_playback
```

Strict sensitivity pass used the same inputs with:

```text
--budget_multiplier 1.0 --fixed_slack_steps 0
```

## 6. Outputs

Main output directory:

```text
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/
```

Files:

```text
budget_aware_segment_summary.csv
budget_aware_source_summary.csv
budget_aware_summary.json
```

Strict sensitivity output:

```text
results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics_strict_budget/
```

## 7. Main Findings

### Original no-cooldown playback

| source | long segments >=10 | completed long segments | over-budget no-completion segments | max segment length | max budget ratio |
|---|---:|---:|---:|---:|---:|
| Phase 9D-3 `models/` | 70 | 45 | 15 | 282 | 4.97 |
| Phase 9D-3 `best_model/` | 40 | 25 | 15 | 282 | 4.97 |

This means repeated same-target selection is mixed:

- many long repeated selections are normal persistence and complete within budget,
- a smaller set are true over-budget stuck retries,
- the true stuck pairs match the Phase 9D-3 late targets.

Top over-budget no-completion pairs:

| source | over-budget pairs |
|---|---|
| Phase 9D-3 `models/` | `robot_0->44`, `robot_1->44`, `robot_2->15` |
| Phase 9D-3 `best_model/` | `robot_0->39`, `robot_1->0`, `robot_2->15` |

Representative top segment:

```text
robot_2->15
start_step = 111
end_step = 299
segment_length = 189
budget_steps = 38
budget_ratio = 4.97
selected_path_cost_first = 1.3127
```

### Cooldown trigger timing versus budget

Main budget model:

| source | threshold 10 within budget | threshold 30 within budget | threshold 50 within budget |
|---|---:|---:|---:|
| Phase 9D-3 `models/` | 70/70 | 40/40 | 10/15 |
| Phase 9D-3 `best_model/` | 40/40 | 30/30 | 20/25 |
| Phase 9E-3A aggressive `models/` | 15/15 | 0/0 | 0/0 |
| Phase 9E-3A aggressive `best_model/` | 15/15 | 0/0 | 0/0 |
| Phase 9E-3B `weak_d5_s30 models` | 25/25 | 5/5 | 0/0 |
| Phase 9E-3B `weak_d5_s30 best_model` | 25/25 | 5/5 | 0/0 |

The aggressive threshold 10 always fires inside budget in the analyzed histories. The weak threshold 30 also fires inside budget for observed `weak_d5_s30` segments. This strongly supports the idea that pure streak thresholding is not a true stuck signal.

### Aggressive cooldown behavior

Aggressive cooldown playback:

| source | total segments | max segment length | over-budget no-completion segments | max budget ratio |
|---|---:|---:|---:|---:|
| Phase 9E-3A aggressive `models/` | 4065 | 10 | 0 | 0.29 |
| Phase 9E-3A aggressive `best_model` | 3455 | 10 | 0 | 0.29 |

This is the diagnostic core:

```text
Aggressive cooldown prevents segments from ever reaching over-budget evidence.
It cuts repeated selections at streak 10, while those selections are still well within expected motion budget.
```

### Weak cooldown behavior

Main budget model:

| source | max segment length | over-budget no-completion segments | max budget ratio |
|---|---:|---:|---:|
| `weak_d5_s30 models` | 30 | 0 | 0.53 |
| `weak_d5_s30 best_model` | 30 | 0 | 0.53 |
| `weak_d5_s50 models` | 50 | 0 | 0.64 |
| `weak_d5_s50 best_model` | 50 | 0 | 0.64 |
| `short_d3_s50 models` | 50 | 0 | 0.64 |
| `short_d3_s50 best_model` | 50 | 0 | 0.64 |
| `strict_attempt20_d5_s50 models` | 50 | 0 | 0.68 |
| `strict_attempt20_d5_s50 best_model` | 50 | 0 | 0.68 |

The weak variants are better playback guardrails than aggressive cooldown because they preserve coverage, but under the main budget model they still trigger before true over-budget stuck evidence.

## 8. Strict Budget Sensitivity

Strict budget model:

```text
budget_steps = ceil(selected_path_cost / max_base_xy_step_by_robot)
```

Selected results:

| source | over-budget no-completion | threshold 10 within budget | threshold 30 within budget | threshold 50 within budget |
|---|---:|---:|---:|---:|
| Phase 9D-3 `models/` | 15 | 70/70 | 30/40 | 5/15 |
| Phase 9D-3 `best_model/` | 15 | 40/40 | 25/30 | 10/25 |
| Phase 9E-3A aggressive `models/` | 0 | 15/15 | 0/0 | 0/0 |
| Phase 9E-3A aggressive `best_model/` | 0 | 15/15 | 0/0 | 0/0 |
| `weak_d5_s30 models` | 10 | 25/25 | 5/5 | 0/0 |
| `weak_d5_s30 best_model` | 0 | 25/25 | 5/5 | 0/0 |

Even with no slack, threshold 10 still fires inside budget for all triggered segments. The aggressive cooldown conclusion is robust.

## 9. Interpretation

Phase 9E-3C supports the hypothesis.

What is normal persistence:

```text
Many long same-target runs in Phase 9D-3 complete within expected motion budget.
Thresholds 10 and 30 often occur while a robot is still plausibly navigating toward the target.
```

What is true stuck retry:

```text
The late Phase 9D-3 repeated targets become clear only after segment length exceeds budget.
The over-budget no-completion pairs exactly match the known late stuck targets.
```

Why aggressive cooldown collapsed coverage:

```text
It triggered at streak 10 before budget exhaustion.
It therefore suppressed normal task persistence, fragmented assignments, and prevented many segments from accumulating enough effort to complete.
```

Why weak cooldown helped but is not final:

```text
Weak variants preserve coverage because they allow more normal persistence.
However, they still use pure streak thresholds and can still fire before budget exhaustion.
They are useful guardrails, not budget-aware stuck detectors.
```

## 10. Diagnostic Recommendation

Future stuck-target logic should not trigger on same-target streak alone.

A better candidate signal:

```text
same_robot_target_streak >= min_streak
AND accumulated_selection_steps > ceil(selected_path_cost / max_base_xy_step_by_robot * multiplier + slack)
AND selected target remains uncovered
AND selected target remains available and feasible
AND no selected-target completion occurred
AND no recent global coverage gain, if global stagnation is still desired
```

Suggested initial design direction:

```text
Use budget-aware failed-attempt accumulation.
Keep weak cooldown variants as playback guardrail references.
Do not train with aggressive streak-only cooldown.
```

## 11. Known Limitations

- The analysis uses playback histories, not fresh simulation or formal evaluation.
- Playback episodes are deterministic repeats.
- Execution effort is approximated by decision steps spent selecting the same pair.
- `selected_path_cost` is scanner-to-viewpoint distance, not full path length or controller convergence time.
- Base step estimates ignore yaw, scanner arm movement, obstacle detours, and scan tolerance details.
- Segment analysis is contiguous same-target selection; non-contiguous repeated attempts are not the primary unit here.
- The analysis does not implement a new cooldown rule.

## 12. Recommended Follow-Up

Recommended Phase 9E-3D:

```text
Design a budget-aware cooldown trigger, but do not train yet.
```

Keep it diagnostics/config-gated and wrapper-local if implemented:

```text
disabled by default
assignment RL only
mask-only initially
reward unchanged
observations unchanged unless a separate design explicitly accepts observation changes
```

Before training, run playback-only comparison:

```text
no-cooldown checkpoint + budget-aware cooldown playback
compare against:
  Phase 9D-3 no cooldown
  Phase 9E-3A aggressive cooldown
  Phase 9E-3B weak_d5_s30 / short_d3_s50
```

No follow-up was implemented in Phase 9E-3C.
