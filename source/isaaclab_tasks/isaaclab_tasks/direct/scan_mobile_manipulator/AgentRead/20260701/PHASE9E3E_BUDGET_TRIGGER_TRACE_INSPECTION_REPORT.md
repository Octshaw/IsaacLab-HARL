# Phase 9E-3E Trace Inspection of Budget-Aware Cooldown Trigger Events

## 1. Scope and Boundaries

Phase 9E-3E inspected existing Phase 9E-3D budget-aware cooldown playback traces. This phase did not run training and did not modify Assignment RL behavior.

No reward formulas/defaults, `Total_Reward` whitelist, observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithms, installed site-packages, baseline solver behavior, default scenario cooldown setting, cooldown trigger logic, cooldown mask behavior, budget model, budget parameters, or scenario YAMLs were changed.

## 2. No-Training Statement

No training was run.

This phase used existing playback outputs only.

## 3. Inputs Inspected

Primary Phase 9E-3D `m15_slack5_d5` playback outputs:

```text
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback/
```

Comparison Phase 9E-3D strict budget outputs:

```text
results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m10_slack0_d5_best_model_playback/
results/assignment_diagnostics/phase9e3d_budget_cooldown_playback_summary.csv
```

Known Phase 9E-3C over-budget no-completion pairs:

```text
models: robot_0->44, robot_1->44, robot_2->15
best_model: robot_0->39, robot_1->0, robot_2->15
```

## 4. Analysis Script / Method

Added standalone trace analyzer:

```text
scripts/environments/analyze_budget_cooldown_traces.py
```

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\analyze_budget_cooldown_traces.py --output_dir results\assignment_diagnostics\phase9e3e_budget_trigger_trace_inspection
```

The script reads existing `assignment_history.csv`, `summary.csv`, and existing Phase 9E-3D summary files. It does not import Isaac Sim.

Generated outputs:

```text
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/budget_trigger_events.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/budget_trigger_windows.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/post_trigger_redirect_summary.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/conflict_after_trigger_summary.csv
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/phase9e3e_budget_trigger_trace_summary.json
results/assignment_diagnostics/phase9e3e_budget_trigger_trace_inspection/phase9e3e_trace_notes.md
```

Field limitation:

```text
assignment_history.csv has row-level exact duplicate target and base-motion crossing fields.
It does not have row-level selected-target conflict or inter-robot overlap fields.
Therefore, selected-target conflict/overlap are available only as playback summary metrics, while duplicate selected target and crossing are used as local trace proxies.
```

## 5. Budget Trigger Event Summary

Phase 9E-3D summary reported per-episode mean budget triggers:

```text
models: 20
best_model: 22
```

The trace table contains all 5 episodes:

| Checkpoint | Total Trigger Rows | Per-Episode Trigger Rows | Unique Triggered Pairs |
|---|---:|---:|---|
| `models` | 100 | 20 | `r0->44`, `r1->44`, `r2->15` |
| `best_model` | 110 | 22 | `r0->39`, `r1->0`, `r2->15` |

Trigger pair counts:

| Checkpoint | Pair | Trigger Rows |
|---|---|---:|
| `models` | `r0->44` | 5 |
| `models` | `r1->44` | 60 |
| `models` | `r2->15` | 35 |
| `best_model` | `r0->39` | 5 |
| `best_model` | `r1->0` | 70 |
| `best_model` | `r2->15` | 35 |

Budget exhaustion check:

| Checkpoint | Trigger Rows | Budget Ratio Min | Budget Ratio Max | Attempt Steps Range | Budget Steps Range |
|---|---:|---:|---:|---|---|
| `models` | 100 | 1.00 | 1.00 | 13-73 | 13-73 |
| `best_model` | 110 | 1.00 | 1.25 | 10-73 | 8-73 |

This supports that triggers occurred at or after cost-derived budget exhaustion, not at arbitrary streak 10.

## 6. Known Stuck Pair Match

| Checkpoint | Known-Pair Triggers | Non-Known Triggers | Fraction Known |
|---|---:|---:|---:|
| `models` | 100 | 0 | 1.00 |
| `best_model` | 110 | 0 | 1.00 |

All m15 budget triggers matched Phase 9E-3C known over-budget no-completion pairs. This is the strongest positive trace result.

Non-known triggered pairs: none.

Triggered target later covered:

```text
models: 0/100 trigger rows
best_model: 5/110 trigger rows
```

This still does not prove targets are unreachable. It only confirms that the m15 trigger selected the same previously diagnosed over-budget no-completion pairs.

## 7. Trigger Window Analysis

Window definition:

```text
10 steps before trigger
trigger step
20 steps after trigger
```

Coverage and timing:

| Checkpoint | Trigger Rows | Before/At Last Coverage Gain | After Last Coverage Gain | Followed By Coverage Gain Within 20 |
|---|---:|---:|---:|---:|
| `models` | 100 | 70 | 30 | 45 |
| `best_model` | 110 | 90 | 20 | 50 |

Per episode:

```text
models: 20 triggers/episode, 14 before-or-at last gain, 6 after last gain, 9 followed by gain within 20
best_model: 22 triggers/episode, 18 before-or-at last gain, 4 after last gain, 10 followed by gain within 20
```

The triggers do not appear to end useful coverage. Many occur before the final coverage gain and are followed by additional coverage within 20 steps. Final coverage was preserved or improved relative to Phase 9D-3.

Post-trigger local streaks:

```text
No trigger window produced another same-target streak >= 30 within the next 20 steps.
```

## 8. Post-Trigger Redirect Analysis

Next non-noop target distribution:

| Checkpoint | Distribution |
|---|---|
| `models` | `48:60`, `0:35`, `28:5` |
| `best_model` | `48:70`, `0:35`, `34:5` |

Next target equals another robot's current target:

```text
models: 0/100
best_model: 25/110
```

Returned to the triggered target later:

```text
models: 95/100
best_model: 110/110
```

Interpretation:

```text
The cooldown redirects selection immediately and prevents long uninterrupted streaks.
However, robots often return to the same triggered target after cooldown expires.
This is expected for a mask guardrail and is not an active-task lifecycle solution.
```

## 9. Conflict / Spatial Side-Effect Analysis

Overall Phase 9E-3D summary:

| Checkpoint | Selected-Target Conflict Overall | Inter-Robot Overlap Overall | Crossing Overall | Duplicate Overall |
|---|---:|---:|---:|---:|
| `models` | 0.4381 | 0.2241 | 0.0814 | 0.1070 |
| `best_model` | 0.2274 | 0.1037 | 0.1126 | 0.0870 |

Trace-local proxy metrics:

| Checkpoint | Duplicate Rate In 20-Step Trigger Windows | Duplicate Rate Outside Windows | Crossing In Windows | Crossing Outside Windows |
|---|---:|---:|---:|---:|
| `models` | 0.1531 | 0.0000 | 0.0909 | 0.0593 |
| `best_model` | 0.1244 | 0.0000 | 0.1212 | 0.0926 |

Interpretation:

```text
Exact duplicate selected-target conflicts are concentrated inside trigger windows in this playback.
Crossing proxy rates are also somewhat higher inside trigger windows.
Row-level broader selected-target conflict and inter-robot overlap are unavailable, so direct attribution remains partial.
```

The trace suggests that m15 may create or expose coordination pressure after releasing a robot from a stuck pair, especially for `best_model`, where 25/110 redirects immediately target another robot's current target.

## 10. Coverage Safety Analysis

Coverage safety evidence:

```text
models final_coverage remained 0.50, matching Phase 9D-3 no-cooldown.
best_model final_coverage improved from 0.40 to 0.46.
noop_when_available stayed 0.0000 for both.
45/100 models trigger rows and 50/110 best_model trigger rows were followed by coverage gain within 20 steps.
```

Risk evidence:

```text
30/100 models trigger rows and 20/110 best_model trigger rows occurred after the last coverage gain.
Triggered pairs are often revisited after cooldown expiry.
Some duplicate/crossing proxy pressure is concentrated near trigger windows.
```

Overall, the m15 trigger does not appear to collapse coverage in playback, but it does not fully solve stuck-pair revisitation.

## 11. m15_slack5_d5 vs m10_slack0_d5

| Variant | Checkpoint | Coverage | AUC | Max Streak | Suppressed | Budget Triggers | Over-Budget Selected |
|---|---|---:|---:|---:|---:|---:|---:|
| `m15_slack5_d5` | `models` | 0.50 | 0.3675 | 110 | 0.3244 | 20 | 20 |
| `m15_slack5_d5` | `best_model` | 0.46 | 0.3387 | 110 | 0.3679 | 22 | 49 |
| `m10_slack0_d5` | `models` | 0.48 | 0.3528 | 93 | 0.5217 | 32 | 179 |
| `m10_slack0_d5` | `best_model` | 0.42 | 0.3224 | 93 | 0.5485 | 34 | 269 |

Strict budget reduces streak further, but it increases suppression and over-budget selected counts and slightly lowers coverage/AUC. The m15 scenario is safer for any next training probe.

## 12. Classification

Classification: **TRACE-PARTIAL**.

Reason:

```text
budget triggers are highly plausible: 100% match known Phase 9E-3C over-budget no-completion pairs
triggers occur after budget exhaustion
coverage is preserved or improved
noop does not increase
but post-trigger returns are common
duplicate/crossing proxy pressure is concentrated near trigger windows
row-level selected-target conflict and overlap are unavailable
```

## 13. Known Limitations

```text
selected_path_cost is scanner-to-viewpoint Euclidean distance, not planned path length
row-level selected-target conflict and inter-robot overlap are unavailable
duplicate selected target is only an exact-target conflict proxy
trace data are deterministic playback traces from one checkpoint family
cooldown remains a wrapper-local action-mask guardrail
no active-task lifecycle is implemented
```

## 14. Recommended Follow-Up

Because the result is TRACE-PARTIAL, the user may run one scoped 100k single-seed debug training manually using:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
```

Then run playback diagnostics on `models/` and `best_model/` and compare against:

```text
Phase 9D-3 no cooldown
Phase 9E-3A aggressive cooldown
Phase 9E-3B weak_d5_s30 and short_d3_s50
Phase 9E-3D m15 playback
```

If training shows increased conflict or repeated revisitation, defer further training and investigate conflict-aware redirect or active-task lifecycle design.
