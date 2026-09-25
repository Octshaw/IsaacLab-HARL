# Phase 9E-3A Cross-Playback Cooldown Attribution Report

Date: 2026-07-01

## 1. Scope and Boundaries

Phase 9E-3A performed playback-only cross diagnostics to attribute the negative Phase 9E-2 cooldown side effect.

Question:

```text
Did Phase 9E-2 fail mainly because of training-time policy bias, runtime cooldown masking, or the specific cooldown configuration/mask-only design?
```

This phase used existing checkpoints only.

No reward formula, reward scale/default, `Total_Reward` whitelist, actor/shared observation dimension, `available_actions` shape, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithm, installed site-package, baseline behavior, default scenario cooldown setting, cooldown parameter, or cooldown mechanism was changed.

The default scenario was not edited. The cooldown debug scenario was not edited.

## 2. No-Training Statement

No training was run in Phase 9E-3A.

All experiments used deterministic playback diagnostics with:

```text
num_envs = 1
num_episodes = 5
max_steps = 300
stop_on_done = true
headless = true
device = cuda:0
```

## 3. Located Checkpoint Paths

Phase 9D-3 no-cooldown checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
```

Exists:

```text
models/: yes
best_model/: yes
```

Phase 9E-2 cooldown-trained checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19
```

Exists:

```text
models/: yes
best_model/: yes
```

Scenario confirmation:

```text
default scenario: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
  cooldown override: absent; default remains disabled

debug scenario: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
  assignment_cooldown.enabled: true
```

## 4. Exact Commands Run

Pre-flight:

```powershell
git status --short
git diff --check
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_rl_playback_diagnostics.py
```

Experiment A1, no-cooldown trained `models/` with cooldown-enabled playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/models --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e3a_no_cooldown_models_with_cooldown_playback --stop_on_done
```

Experiment A2, no-cooldown trained `best_model/` with cooldown-enabled playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/best_model --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e3a_no_cooldown_best_model_with_cooldown_playback --stop_on_done
```

Experiment B1, cooldown-trained `models/` with cooldown-disabled playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19/models --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e3a_cooldown_models_without_cooldown_playback --stop_on_done
```

Experiment B2, cooldown-trained `best_model/` with cooldown-disabled playback:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19/best_model --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e3a_cooldown_best_model_without_cooldown_playback --stop_on_done
```

## 5. Experiment Completion

All four cross-playback experiments completed with exit code `0`.

Output directories:

```text
results/assignment_diagnostics/phase9e3a_no_cooldown_models_with_cooldown_playback
results/assignment_diagnostics/phase9e3a_no_cooldown_best_model_with_cooldown_playback
results/assignment_diagnostics/phase9e3a_cooldown_models_without_cooldown_playback
results/assignment_diagnostics/phase9e3a_cooldown_best_model_without_cooldown_playback
```

Console logs:

```text
results/assignment_diagnostics/phase9e3a_no_cooldown_models_with_cooldown_playback_console.log
results/assignment_diagnostics/phase9e3a_no_cooldown_best_model_with_cooldown_playback_console.log
results/assignment_diagnostics/phase9e3a_cooldown_models_without_cooldown_playback_console.log
results/assignment_diagnostics/phase9e3a_cooldown_best_model_without_cooldown_playback_console.log
```

Derived summaries:

```text
results/assignment_diagnostics/phase9e3a_cross_playback_comparison_summary.json
results/assignment_diagnostics/phase9e3a_cross_playback_trace_summary.csv
```

## 6. Cross-Playback Result Table

| experiment | training checkpoint | playback scenario | final coverage | coverage AUC | new viewpoints | max streak | late repeated count | representative late targets | final targets | noop-when-available |
|---|---|---|---:|---:|---:|---:|---:|---|---|---:|
| A1 | Phase 9D-3 `models/` no-cooldown trained | cooldown enabled | 0.0200 | 0.0189 | 1 | 10 | 81 | r0->18, r1->48, r2->49 | r0->46, r1->17, r2->35 | 0.0000 |
| A2 | Phase 9D-3 `best_model/` no-cooldown trained | cooldown enabled | 0.0400 | 0.0374 | 2 | 10 | 80 | r0->18, r1->48, r2->0 | r0->35, r1->45, r2->47 | 0.1371 |
| B1 | Phase 9E-2 `models/` cooldown trained | cooldown disabled | 0.3600 | 0.2755 | 18 | 243 | 843 | r0->36, r1->2, r2->38 | r0->36, r1->2, r2->38 | 0.0000 |
| B2 | Phase 9E-2 `best_model/` cooldown trained | cooldown disabled | 0.4400 | 0.2863 | 22 | 243 | 734 | r0->36, r1->11, r2->noop_or_none | r0->36, r1->20, r2->noop | 0.1104 |

Additional spatial/conflict diagnostics:

| experiment | selected-target conflict | inter-robot overlap | base-motion crossing | duplicate selected target |
|---|---:|---:|---:|---:|
| A1 | 0.3913 | 0.8528 | 0.8239 | 0.1070 |
| A2 | 0.2508 | 0.6689 | 0.7291 | 0.0000 |
| B1 | 0.2341 | 0.0870 | 0.2018 | 0.0000 |
| B2 | 0.2174 | 0.1104 | 0.2297 | 0.1605 |

## 7. Comparison Against Phase 9D-3 and Phase 9E-2 References

### Phase 9D-3 no-cooldown trained policy under cooldown at playback

| checkpoint | Phase 9D-3 original final coverage | Phase 9E-3A cooldown playback final coverage | original AUC | cooldown playback AUC | original max streak | cooldown playback max streak |
|---|---:|---:|---:|---:|---:|---:|
| `models/` | 0.5000 | 0.0200 | 0.3675 | 0.0189 | 282 | 10 |
| `best_model/` | 0.4000 | 0.0400 | 0.3234 | 0.0374 | 282 | 10 |

The cooldown mask reduced the repeated same-target streak, but inference-time coverage collapsed far below the original no-cooldown playback reference.

### Phase 9E-2 cooldown-trained policy with cooldown removed at playback

| checkpoint | Phase 9E-2 cooldown playback final coverage | Phase 9E-3A cooldown-disabled playback final coverage | cooldown playback AUC | cooldown-disabled playback AUC | cooldown playback max streak | cooldown-disabled playback max streak |
|---|---:|---:|---:|---:|---:|---:|
| `models/` | 0.1200 | 0.3600 | 0.1042 | 0.2755 | 10 | 243 |
| `best_model/` | 0.1000 | 0.4400 | 0.0868 | 0.2863 | 10 | 243 |

Removing cooldown at playback restored much of the coverage and reduced the extreme noop-when-available behavior, but the repeated-stuck-target pattern returned.

## 8. Cooldown Intervention Metrics

Cooldown-enabled cross-playback:

| experiment | cooldown enabled | trigger count | active count | suppressed count | max remaining | selected pair active count | trigger events total | unique triggered robot-target pairs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A1 | true | 747.0 | 48.0602 | 47.8595 | 20.0 | 0 | 3735 | 63 |
| A2 | true | 646.0 | 41.6254 | 41.4582 | 20.0 | 0 | 3230 | 52 |

Selected-pair failed-attempt diagnostics:

| experiment | failed-attempt mean | failed-attempt max |
|---|---:|---:|
| A1 | 7.0201 | 11 |
| A2 | 6.0602 | 11 |

The selected pair active count stayed zero, which means the cooldown mask was preventing cooldown-active robot-target pairs before policy selection. However, active/suppressed counts were very high: A1 suppressed about 47.9 actions per robot row on average, and A2 suppressed about 41.5.

## 9. Noop Behavior Analysis

Noop behavior did not explain all coverage collapse.

| experiment | noop-when-available rate | noop-when-available count | mean available viewpoints during noop-when-available | mean cooldown-suppressed count during noop-when-available |
|---|---:|---:|---:|---:|
| A1 | 0.0000 | 0 | 0.0 | 0.0 |
| A2 | 0.1371 | 205 | 47.5854 | 12.9675 |
| B1 | 0.0000 | 0 | 0.0 | 0.0 |
| B2 | 0.1104 | 165 | 27.3030 | 0.0 |

Observations:

- A1 coverage collapsed to 0.02 even with no noop-when-available selections. This points to action redirection/over-masking, not just noop bias.
- A2 selected noop sometimes despite many real targets still being available on average.
- B1 removed cooldown and recovered to 0.36 coverage with no noop-when-available selections.
- B2 removed cooldown and recovered to 0.44 coverage, with noop-when-available only 0.1104 rather than the Phase 9E-2 cooldown-playback 0.4671.
- Phase 9E-2 high noop behavior appears to be strongly tied to runtime cooldown playback/training interaction, not a permanent policy-only noop collapse.

The cooldown-enabled A runs suppressed many different robot-target pairs rather than a tiny stuck set:

```text
A1 unique triggered robot-target pairs = 63
A2 unique triggered robot-target pairs = 52
```

This suggests the configured cooldown was broad enough to reshape the available action surface aggressively.

## 10. Interpretation

Phase 9E-3A matches a combined **Case 2 + Case 4** pattern, with runtime cooldown masking as the dominant attribution.

Case 2 evidence:

```text
No-cooldown trained checkpoints + cooldown-enabled playback:
  streak decreases from 282 to 10
  coverage collapses from 0.50/0.40 to 0.02/0.04
  cooldown active/suppressed counts are very high
```

Interpretation:

```text
The runtime cooldown mask itself damages action selection under the current configuration.
```

Case 4 evidence:

```text
Cooldown-trained checkpoints + cooldown-disabled playback:
  coverage recovers from 0.12/0.10 to 0.36/0.44
  noop-when-available drops from 0.4805/0.4671 to 0.0000/0.1104
  max same-target streak rises back to 243
```

Interpretation:

```text
The Phase 9E-2 trained policy is not inherently stuck in the same low-coverage/noop behavior once the runtime mask is removed.
The mask is the main immediate cause of the Phase 9E-2 playback collapse, while removing it also brings back the late repeated-target failure.
```

Do not overclaim: this does not prove any target is unreachable. Cooldown remains only a wrapper-local action-mask guardrail.

## 11. Known Limitations

- This is playback-only diagnostics, not formal evaluation.
- Playback episodes are deterministic fixed-scenario repeats.
- Only one no-cooldown 100k checkpoint family and one cooldown-trained 100k checkpoint family were tested.
- Cooldown parameters were not tuned or ablated.
- The cooldown signal is still global-coverage-gain based, with no robot-target-specific attribution.
- The actor/shared observations do not include cooldown state.
- These results isolate the current configured runtime mask behavior more than they fully explain training dynamics.

## 12. Recommended Follow-Up

Do not run more 100k cooldown-enabled training with the current cooldown debug configuration.

Recommended Phase 9E-3B:

```text
Design a smaller cooldown ablation plan before new training.
```

Candidate ablations to design, not implement here:

```text
reduce cooldown duration
raise trigger thresholds
require a stricter repeated-failure signal
limit maximum concurrently cooled targets per robot
mask cooldown only after a stronger late-stagnation condition
evaluate whether cooldown state must be observable before training with a mask
consider inference-only guardrails only after a much less aggressive mask design is validated
```

No follow-up was implemented in Phase 9E-3A.
