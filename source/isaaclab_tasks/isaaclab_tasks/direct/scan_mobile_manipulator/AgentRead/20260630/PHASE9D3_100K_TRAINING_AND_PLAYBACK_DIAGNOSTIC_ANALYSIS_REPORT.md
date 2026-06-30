# Phase 9D-3 100k Training and Playback Diagnostic Analysis Report

## 1. Scope And Boundaries

Phase 9D-3 is a report-only analysis of the post-logger-fix 100k fixed-N assignment RL run and its playback diagnostics.

This report combines:

- 100k training health after the Phase 9D-2A logger whitelist fix.
- TensorBoard and console scalar sanity.
- RL playback diagnostics for `models/`.
- RL playback diagnostics for `best_model/`.
- A reference comparison to the old pre-logger-fix 300k final `models/` debug-artifact smoke.
- Remaining bottlenecks and the recommended next mechanism-design phase.

No code, reward, mask, solver, controller, environment dynamics, path planning, collision, cooldown, retry/fallback, or HARL algorithm behavior was changed. No training, new formal evaluation, checkpoint play rerun, reward tuning, or commit was performed in this phase.

## 2. Inputs Inspected

Reports:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
```

Training artifacts:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/configs.json
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23/logs/events.out.tfevents.1782810743.xxsys203-1
results/assignment_diagnostics/phase9d3_debug_train_100k_after_logger_fix_console.log
```

Playback diagnostic artifacts:

```text
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/diagnostics.json
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/summary.csv
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/per_episode.csv
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/assignment_history.csv

results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/diagnostics.json
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/summary.csv
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/per_episode.csv
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/assignment_history.csv

results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/summary.csv
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/per_episode.csv
results/assignment_diagnostics/phase9d2b_rl_playback_diagnostics_smoke/assignment_history.csv
```

## 3. Training Run Metadata

Run:

```text
exp_name = assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix
run_dir = results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d3_debug_train_100k_after_logger_fix/seed-00001-2026-06-30-17-12-23
task = Isaac-Scan-Mobile-Manipulator-Direct-v0
algorithm = happo
assignment_rl = true
num_env_steps = 100000
num_envs = 1
assignment_episode_length = 300
device = cuda:0
scenario_config = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
log_interval = 5
```

Configuration and console evidence confirm the fixed assignment path:

```text
num_agents = 3
num_viewpoints = 50
noop_id = 50
action spaces = Discrete(51) per robot
available_actions shape = [1, 3, 51]
actor obs dims = 909 per robot in playback diagnostics
shared obs dim = 2727 in playback diagnostics
```

Console evidence:

```text
Scan viewpoints loaded ... num_viewpoints=50 no-op id=50
action_space: {0: Discrete(51), 1: Discrete(51), 2: Discrete(51)}
Assignment RL reset returned available_actions shape=(1, 3, 51)
```

No checkpoint was loaded:

```text
configs.json: Algo Args/train/model_dir = None
--dir was not used for training
```

Model artifacts exist in both:

```text
.../seed-00001-2026-06-30-17-12-23/models
.../seed-00001-2026-06-30-17-12-23/best_model
```

## 4. Logger Whitelist / Total_Reward Sanity

The run used the Phase 9D-2A exact whitelist:

```text
reward_accumulator_mode = exact_whitelist
reward_accumulator_keys = ["assignment_rl_reward/final_reward_mean"]
```

Console evidence:

```text
[INFO]: Assignment RL Total_Reward accumulator whitelist: ['assignment_rl_reward/final_reward_mean']
```

`Total_Reward` now tracks:

```text
assignment_rl_reward/final_reward_mean * assignment_episode_length * log_interval
```

With `assignment_episode_length=300` and `log_interval=5`, a late console sample is:

```text
assignment_rl_reward/final_reward_mean = 0.1741243339277183
Total Reward = 261.18650089157745
```

Sanity check:

```text
0.1741243339277183 * 300 * 5 = 261.18650089157745
```

This confirms `Total_Reward` is no longer polluted by `assignment_rl_reward/steps_since_global_coverage_gain_mean`. No `2e5`-scale accounting artifact appeared in this run.

## 5. Training Scalar Summary

TensorBoard event parsing found:

```text
scalar_tags = 33
scalar_points_per_main_tag = 66
first_logged_step = 1500
last_logged_step = 99000
nonfinite_scalar_values = 0
```

Selected scalar summaries:

| tag | first | first-20 mean | last-20 mean | max | final |
|---|---:|---:|---:|---:|---:|
| `coverage_ratio` | 0.0000 | 0.1119 | 0.3119 | 0.3725 | 0.3362 |
| `new_viewpoints` | 0.0000 | 0.0254 | 0.0719 | 0.0847 | 0.0780 |
| `mean_reward` | -0.0163 | 0.1244 | 0.3880 | 0.4604 | 0.4236 |
| `assignment_rl_reward/final_reward_mean` | -0.0656 | 0.0652 | 0.2037 | 0.3137 | 0.1741 |
| `Total_Reward` | -98.3301 | 97.8477 | 305.6058 | 470.5081 | 261.1865 |
| `assignment_rl_reward/steps_since_global_coverage_gain_mean` | 148.5133 | 148.6717 | 149.1194 | 149.4800 | 148.6000 |
| `assignment_rl_reward/repeated_same_target_no_progress_mean` | -0.0000 | -0.0099 | -0.1350 | -0.0000 | -0.2001 |
| `assignment_rl.selected_available_mask` | 0.9840 | 0.9806 | 0.9951 | 0.9996 | 0.9989 |
| `assignment_rl.valid_action_count` | 2.9520 | 2.9419 | 2.9852 | 2.9987 | 2.9967 |
| `reach_violation` | 0.0009 | 0.0196 | 0.0000 | 0.0471 | 0.0000 |
| `critic/value_loss` | 0.2246 | 0.2228 | 0.0108 | 0.8214 | 0.0047 |
| `critic/average_step_rewards` | -0.0659 | 0.0859 | 0.3694 | 0.5536 | 0.4715 |
| `agent0/dist_entropy` | 3.7692 | 2.1448 | 0.7800 | 3.7692 | 1.1832 |
| `agent1/dist_entropy` | 3.7557 | 2.0757 | 1.0057 | 3.7557 | 0.9791 |
| `agent2/dist_entropy` | 3.8185 | 2.2265 | 0.7032 | 3.8185 | 0.0478 |

Interpretation:

- Training was numerically healthy at scalar-log level: no NaN/Inf was found.
- Coverage-related training scalars improved over the run, but remained far below full coverage.
- `selected_available_mask` rose toward ~1.0, so the learned action path generally selected available actions late in training.
- `reach_violation` fell to 0 in the last 20 logged windows.
- Critic value loss fell sharply by the final windows.
- Entropy decreased, especially for agent 2, indicating increasingly deterministic policies.
- `steps_since_global_coverage_gain_mean` stayed around half the 300-step horizon and did not grow into thousands, so the Phase 9D-1A reset fix remains valid.

## 6. Playback Diagnostics Comparison

The following rows are deterministic fixed-scenario playback diagnostics, not formal stochastic evaluation.

| checkpoint | final coverage | coverage AUC | new viewpoints | total return mean | target conflict rate | overlap rate | base-motion crossing rate | late repeated pattern | late repeated count | max same-target streak | representative late targets |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| 100k `models/` | 0.5000 | 0.3675 | 25 | -308.17 | 0.2910 | 0.2375 | 0.0814 | true | 814 | 282 | r0->44, r1->44, r2->15 |
| 100k `best_model/` | 0.4000 | 0.3234 | 20 | -502.46 | 0.0000 | 0.0702 | 0.0502 | true | 836 | 282 | r0->39, r1->0, r2->15 |
| old 300k final `models/` smoke | 0.4600 | 0.3141 | 23 | -224.02 | 0.5819 | 0.3545 | 0.1728 | true | 704 | 278 | r0->0, r1->44, r2->noop |

Additional 100k diagnostic fields:

| checkpoint | duplicate selected target rate | noop-when-available rate | selected available mean | selected path cost mean | selected path cost max |
|---|---:|---:|---:|---:|---:|
| 100k `models/` | 0.1538 | 0.0000 | 1.0000 | 0.9574 | 5.5211 |
| 100k `best_model/` | 0.0000 | 0.0000 | 1.0000 | 0.7695 | 5.5211 |
| old 300k final `models/` smoke | 0.0669 | 0.1327 | 0.8673 | 1.4981 | 7.4210 |

The 100k `models/` checkpoint is better than 100k `best_model/` on coverage, coverage AUC, new viewpoints, and total return in this deterministic playback. The 100k `best_model/` is cleaner on selected-target conflict, overlap, and crossing, but it sacrifices coverage and return.

Compared with the old 300k final `models/` debug-artifact smoke, the 100k `models/` checkpoint has slightly better deterministic final coverage and substantially lower selected-target conflict, inter-robot overlap, and component-footprint crossing. The old 300k `best_model/` remains excluded as true best evidence because it was selected under polluted pre-9D-2A `Total_Reward` accounting.

## 7. Deterministic Playback Note

Both 100k diagnostic directories contain 5 episodes. For both `models/` and `best_model/`, the per-episode rows are identical after excluding the episode index:

```text
100k models: identical_excluding_episode = true
100k best_model: identical_excluding_episode = true
```

This means the 5 episodes should be treated as repeated deterministic fixed-scenario playback, not as 5 independent stochastic samples.

## 8. Stuck / Late Repeated Assignment Analysis

The dominant failure mode remains late repeated assignment to uncovered but still available/feasible viewpoints.

100k `models/`:

```text
final_uncovered_viewpoint_ids =
[0, 4, 8, 10, 11, 12, 15, 16, 19, 20, 24, 25, 26, 27, 28, 29, 32, 36, 38, 40, 41, 42, 44, 47, 48]

per_robot_selected_count = [299.0, 299.0, 299.0]
per_robot_completed_count = [9.0, 1.0, 1.0]
per_robot_repeated_assignment_count = [287.0, 297.0, 297.0]
max_same_target_streak = 282
max_steps_since_global_coverage_gain = 57
```

Late target status over the final 50 steps across 5 deterministic episodes:

```text
robot_0 -> viewpoint 44, 230/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
robot_1 -> viewpoint 44, 250/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
robot_2 -> viewpoint 15, 250/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
```

This shows a repeated two-robot convergence onto the same uncovered target (`44`) plus a persistent third-robot target (`15`), with no new coverage despite availability/feasibility flags.

100k `best_model/`:

```text
final_uncovered_viewpoint_ids =
[0, 2, 4, 8, 10, 11, 12, 15, 16, 19, 20, 23, 24, 25, 26, 27, 28, 29, 32, 34, 36, 38, 39, 40, 41, 42, 43, 44, 47, 48]

per_robot_selected_count = [299.0, 299.0, 299.0]
per_robot_completed_count = [5.0, 1.0, 1.0]
per_robot_repeated_assignment_count = [293.0, 297.0, 297.0]
max_same_target_streak = 282
max_steps_since_global_coverage_gain = 154
```

Late target status:

```text
robot_0 -> viewpoint 39, 250/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
robot_1 -> viewpoint 0, 250/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
robot_2 -> viewpoint 15, 250/250 late rows, available=true, feasible=true, covered_before=false, new_gain=false
```

This checkpoint avoids duplicate late target selection but still repeats non-progressing uncovered targets for most of the episode tail.

## 9. Comparison With Old 300k Debug Artifact

Phase 9D-2B old 300k final `models/` smoke:

```text
final_coverage = 0.4599999785
coverage_auc = 0.3141133235
selected_target_conflict_rate = 0.5819397993
inter_robot_overlap_rate = 0.3545150502
actual_base_motion_intersection_rate = 0.1727982163
late_repeated_assignment_pattern = true
max_same_target_streak = 278
```

The post-logger-fix 100k `models/` deterministic playback is cleaner on the diagnostic spatial-risk proxies:

```text
target conflict: 0.5819 -> 0.2910
overlap:         0.3545 -> 0.2375
crossing:        0.1728 -> 0.0814
coverage:        0.4600 -> 0.5000
```

This is useful diagnostic evidence, but not a formal checkpoint-quality claim. The old 300k run also had polluted `Total_Reward` / `best_model` accounting before Phase 9D-2A.

## 10. Interpretation

Training health:

- The 100k run is numerically healthy at inspected scalar level.
- Logger accounting is fixed: `Total_Reward` is clean and tied to `assignment_rl_reward/final_reward_mean`.
- The assignment-history reset fix is still valid: `steps_since_global_coverage_gain_mean` stays episode-scale, not thousands.

Checkpoint behavior:

- In deterministic playback, 100k `models/` is better than 100k `best_model/` for coverage and return.
- In deterministic playback, 100k `best_model/` reduces target conflict, robot overlap, and component-footprint crossing, but sacrifices coverage and return.
- The 100k `models/` checkpoint improves over the old 300k debug artifact on conflict/overlap/crossing and slightly improves final coverage in this fixed-scenario playback.

Remaining bottleneck:

- Severe late repeated assignment remains the main bottleneck.
- The stuck targets are usually still available, feasible, and uncovered in the diagnostic fields, yet repeated attempts do not produce coverage.
- Continuing longer training alone may not solve this, because the policy can repeatedly choose plausible-looking but dynamically non-progressing targets.

Baseline context:

- Phase 8 nearest/greedy baselines reached about 45/50 coverage (`0.90`) before plateauing.
- The 100k RL `models/` checkpoint reaches 25/50 coverage (`0.50`) in deterministic playback.
- Therefore this is not yet a strong policy-quality result, even though training is stable and diagnostic spatial-risk metrics improved versus the old 300k debug artifact.

## 11. Explicit Non-Claims And Limitations

- This is not formal RL evaluation.
- The 5 playback episodes are deterministic repeats, not independent stochastic samples.
- No learned-policy quality claim is made beyond this fixed-scenario diagnostic.
- Conflict, overlap, and actual base-motion crossing are proxy diagnostics only.
- No physical collision avoidance, local avoidance, path planning, retry/fallback, cooldown, or hard blocking is implemented or claimed.
- Old 300k final `models/` remains only a debug artifact.
- Old 300k `best_model/` remains polluted by pre-9D-2A logger accounting and should not be treated as true best-policy evidence.
- No reward formula/default-scale, observation, mask, feasibility, solver, controller, environment dynamics, HARL algorithm, or installed package changes were made.

## 12. Recommended Next Phase

Recommended next phase:

```text
Phase 9E-0: design a scoped stuck-target recovery / failed-target cooldown mechanism, using Phase 9D-3 evidence.
```

The mechanism-design phase should start from the observed facts:

- Repeated late targets remain available and feasible but do not yield coverage.
- Two robots can converge onto the same non-progressing target in `models/`.
- `best_model/` can reduce conflict/crossing while still failing coverage.
- Baselines still cover more viewpoints but plateau at hard late targets.

Do not jump directly to longer training. First design a narrow, diagnostic-backed mechanism for stuck-target recovery, failed-target cooldown, or path-risk-aware recovery, and keep it scoped so reward tuning, controller changes, mask changes, and dynamics changes remain explicit decisions rather than accidental side effects.

## 13. Validation

No Python/code files were changed in Phase 9D-3, so no `py_compile` was required.

Repository checks:

```text
git diff --check = passed, with TASK_PROGRESS.md LF/CRLF warning only
```

Observed `git status --short`:

```text
 M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
?? scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
```

The untracked Phase 9D-2B script/report entries were already present in the local working tree and were not modified for this report except as referenced/inspected. No commit was made.
