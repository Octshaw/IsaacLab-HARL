# Phase 9E-2 Cooldown 100k Training and Playback Analysis Report

Date: 2026-06-30

## 1. Scope and Boundaries

Phase 9E-2 ran one scoped 100k single-seed assignment-RL debug training with the Phase 9E-1 per-robot-target cooldown enabled through the dedicated debug scenario. It then ran deterministic playback diagnostics on `models/` and `best_model/` and compared them against the Phase 9D-3 no-cooldown 100k reference.

This was an experiment and diagnostic phase only.

No code, reward formula, reward scale/default, actor/shared observation dimension, `available_actions` shape, static feasibility, controller, solver, path planning, collision/local avoidance, environment dynamics, HARL algorithm, installed site-package, baseline behavior, or default scenario cooldown setting was changed in this phase.

The cooldown mechanism should be interpreted only as a wrapper-local action-mask guardrail. It does not prove a target is unreachable; it temporarily suppresses repeated selection of the same robot-target pair under the configured cooldown conditions.

## 2. Exact Training Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 100000 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9e2_cooldown_enabled_100k --save_interval 20 --log_interval 1
```

Console output was captured to:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_console.log
```

Runner sidecar files:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_runner.ps1
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k.pid
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k.exitcode
```

## 3. Actual Run Directory

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19
```

Both checkpoint directories exist:

```text
models/:     yes
best_model/: yes
```

## 4. Training Result Summary

Training completed successfully with exit code `0`.

Final console progress:

```text
episodes 333/333 total num timesteps 99900/100000, FPS 24
Total Reward is 3.900851213838905
```

The run stopped at `99900/100000` because the assignment episode length is 300 and the runner completed 333 full episodes.

Shape compatibility observed in logs:

```text
actor observation shape = 909
shared observation shape = 2727
available_actions shape = (1, 3, 51)
num_viewpoints = 50
num_agents = 3
noop_id = 50
```

Cooldown was active in training logs. Sampled final scalar values are listed below.

## 5. TensorBoard Scalar Sanity

Scalar sanity JSON:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_scalar_sanity.json
```

Summary:

| check | result |
|---|---:|
| scalar tag count | 46 |
| non-finite scalar count | 0 |
| final `Total_Reward` | 3.9008512497 |
| final `assignment_rl_reward/final_reward_mean` | 0.0130028371 |
| `Total_Reward - final_reward_mean * 300` | 0.0000001267 |
| reward match tolerance | passed |

Final cooldown-related TensorBoard scalars:

| scalar tag | final value |
|---|---:|
| `assignment_cooldown.enabled` | 1.000000 |
| `assignment_cooldown.active_count` | 24.476667 |
| `assignment_cooldown.active_count_mean` | 24.476667 |
| `assignment_cooldown.trigger_count` | 175.056671 |
| `assignment_cooldown.trigger_count_mean` | 175.056671 |
| `assignment_cooldown.triggered_pair_count` | 1.280000 |
| `assignment_cooldown.suppressed_action_count` | 24.393333 |
| `assignment_cooldown.suppressed_action_count_mean` | 24.393333 |
| `assignment_cooldown.failed_attempt_count_mean` | 1.593222 |
| `assignment_cooldown.max_cooldown_remaining` | 19.139999 |
| `assignment_cooldown.max_cooldown_remaining_mean` | 19.139999 |
| `assignment_cooldown.selected_target_was_in_cooldown_count` | 0.000000 |

Final coverage-related TensorBoard scalars:

| scalar tag | final value |
|---|---:|
| `coverage_ratio` | 0.125067 |
| `new_viewpoints` | 0.013333 |
| `assignment_rl_reward/global_coverage_gain_mean` | 0.000000 |
| `assignment_rl_reward/steps_since_global_coverage_gain_mean` | 148.616669 |

Conclusion: scalar sanity passed. `Total_Reward` still tracks `assignment_rl_reward/final_reward_mean` at episode-length scale and was not polluted by cooldown diagnostics.

## 6. Playback Diagnostics Command for `models/`

The first playback attempt without `--headless` failed during Isaac Sim viewport startup with a swapchain height-zero crash. The script already supports launcher flags through `AppLauncher.add_app_launcher_args(parser)`, so playback was rerun headless.

Failed-attempt log:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback_attempt1_viewport_crash_console.log
```

Successful command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19/models --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback --stop_on_done
```

Outputs:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback_console.log
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/diagnostics.json
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/summary.csv
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/per_episode.csv
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_models_playback/assignment_history.csv
```

## 7. Playback Diagnostics Command for `best_model/`

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e2_cooldown_enabled_100k/seed-00001-2026-06-30-23-25-19/best_model --num_episodes 5 --max_steps 300 --output_dir results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback --stop_on_done
```

Outputs:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback_console.log
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/diagnostics.json
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/summary.csv
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/per_episode.csv
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_best_model_playback/assignment_history.csv
```

Derived comparison JSON:

```text
results/assignment_diagnostics/phase9e2_cooldown_enabled_100k_playback_comparison_summary.json
```

## 8. Comparison Against Phase 9D-3 No-Cooldown Reference

The 5 playback episodes were deterministic repeats for both cooldown-enabled checkpoint directories. Means below therefore describe repeated fixed-scenario playback, not independent stochastic evaluation.

### `models/`

| metric | Phase 9D-3 no cooldown | Phase 9E-2 cooldown enabled |
|---|---:|---:|
| final coverage | 0.5000 | 0.1200 |
| coverage AUC | 0.3675 | 0.1042 |
| new viewpoints | 25 | 6 |
| max same-target streak | 282 | 10 |
| late repeated assignment count | 814 | 70 |
| noop-when-available rate | 0.0000 | 0.4805 |
| selected-target conflict rate | 0.2910 | 0.2107 |
| inter-robot overlap rate | 0.2375 | 0.3645 |
| base-motion crossing rate | 0.0814 | 0.3333 |
| duplicate selected target rate | 0.1538 | 0.0502 |

Representative late targets:

| source | representative late targets |
|---|---|
| Phase 9D-3 no cooldown | `robot_0->44, robot_1->44, robot_2->15` |
| Phase 9E-2 cooldown enabled | `robot_0->20, robot_1->5, robot_2->3` |

For Phase 9E-2, late targets are the dominant non-noop selected target per robot in the last 50 playback steps. Final selected targets were `robot_0->noop`, `robot_1->8`, `robot_2->noop`.

### `best_model/`

| metric | Phase 9D-3 no cooldown | Phase 9E-2 cooldown enabled |
|---|---:|---:|
| final coverage | 0.4000 | 0.1000 |
| coverage AUC | 0.3234 | 0.0868 |
| new viewpoints | 20 | 5 |
| max same-target streak | 282 | 10 |
| late repeated assignment count | 836 | 70 |
| noop-when-available rate | 0.0000 | 0.4671 |
| selected-target conflict rate | 0.0000 | 0.1572 |
| inter-robot overlap rate | 0.0702 | 0.4548 |
| base-motion crossing rate | 0.0502 | 0.3423 |
| duplicate selected target rate | 0.0000 | 0.0535 |

Representative late targets:

| source | representative late targets |
|---|---|
| Phase 9D-3 no cooldown | `robot_0->39, robot_1->0, robot_2->15` |
| Phase 9E-2 cooldown enabled | `robot_0->20, robot_1->5, robot_2->3` |

For Phase 9E-2, late targets are the dominant non-noop selected target per robot in the last 50 playback steps. Final selected targets were `robot_0->noop`, `robot_1->2`, `robot_2->noop`.

## 9. Cooldown Intervention Metrics

Playback cooldown metrics:

| checkpoint | enabled | trigger count mean | active count mean | suppressed count mean | max cooldown remaining | selected pair active count | trigger events across 5 episodes |
|---|---|---:|---:|---:|---:|---:|---:|
| `models/` | true | 380.0 | 24.4548 | 24.3612 | 20.0 | 0 | 1900 |
| `best_model/` | true | 388.0 | 25.0569 | 24.9632 | 20.0 | 0 | 1940 |

Additional selected-pair cooldown fields:

| checkpoint | selected-pair failed attempt mean | selected-pair failed attempt max | selected-pair cooldown remaining max |
|---|---:|---:|---:|
| `models/` | 3.9153 | 16 | 0 |
| `best_model/` | 3.9900 | 16 | 0 |

The selected-pair active count stayed zero in playback, matching the training scalar `assignment_cooldown.selected_target_was_in_cooldown_count = 0.0`. This indicates the action mask suppressed cooldown-active robot-target pairs before policy selection.

## 10. Interpretation Category

Category: **D. Negative side effect**.

Evidence:

- The cooldown guardrail substantially reduced the worst same-target streak from 282 to 10.
- Late repeated assignment count fell from 814/836 to 70.
- However, final coverage collapsed from 0.50 to 0.12 for `models/`, and from 0.40 to 0.10 for `best_model/`.
- Coverage AUC also collapsed from 0.3675 to 0.1042 for `models/`, and from 0.3234 to 0.0868 for `best_model/`.
- Noop-when-available rate rose from 0.0 to 0.4805 for `models/` and 0.4671 for `best_model/`.
- Overlap and base-motion crossing worsened despite reduced repeated-target streaks.

The current cooldown configuration is effective as an anti-streak mask, but in this 100k single-seed debug run it appears to over-constrain or redirect the learned policy in a way that badly harms coverage and increases noop behavior.

## 11. Known Limitations

- This is one 100k single-seed debug run, not formal evaluation.
- Playback used five deterministic fixed-scenario repeats; the rows were identical apart from episode index.
- The cooldown progress signal remains global coverage gain only.
- There is no robot-target-specific coverage attribution.
- There is no team-level target cooldown.
- Cooldown state is not included in actor/shared observations.
- The report does not tune the cooldown thresholds or duration.
- The first non-headless playback attempt failed due Isaac Sim viewport startup; successful playback used the script-supported `--headless --device cuda:0` launcher flags.
- Results show this cooldown configuration's effect, not a general proof that cooldown masks are unusable.

## 12. Recommended Follow-Up

Do not promote the current cooldown-enabled debug scenario as an improvement.

Recommended next phase:

1. Analyze why cooldown drives high noop-when-available behavior and low coverage.
2. Inspect late `assignment_history.csv` traces around cooldown triggers to distinguish over-masking from policy preference for noop.
3. Design a smaller Phase 9E-3 ablation before any new 100k run. Candidate questions:
   - Is the trigger too aggressive?
   - Is duration too long?
   - Should cooldown require a stronger repeated-failure signal?
   - Should noop remain always available but receive separate diagnostics or training handling?
   - Does policy need observation access to cooldown state before using this guardrail in training?

No follow-up was implemented in Phase 9E-2.
