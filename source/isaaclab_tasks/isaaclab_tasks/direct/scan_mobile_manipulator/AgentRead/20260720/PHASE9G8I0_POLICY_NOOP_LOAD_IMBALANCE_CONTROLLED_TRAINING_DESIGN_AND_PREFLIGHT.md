# Phase 9G-8I-0: Policy-Noop and Load-Imbalance Controlled Training Design and Preflight

Date: 2026-07-20

## 1. Classification

`CONTROLLED-TRAINING-READY`

One fresh-start, user-executed, 100k-configured-step HAPPO run can be launched with the exact command frozen below without source or configuration changes. The current committed baseline is clean, the result parent is absent, the CLI and installed HARL runner semantics are unambiguous, one environment is a proven valid buffer configuration, and the logging, save, checkpoint, and post-training review boundaries are defined.

This classification authorizes only the separately reviewed Phase 9G-8I-1 manual run. It does not authorize Codex to launch it, a retry, checkpoint continuation, playback, evaluation, 300k training, or a mechanism change.

## 2. Repository Baseline

Pre-documentation preflight:

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `7875612117fbf617aa5f740ebca6dfbd0280485b` |
| `git log -1 --oneline` | `78756121 feat(assignment): add validated playback attribution diagnostics` |
| `git status --short --untracked-files=all` | Empty |
| `git diff --name-status` | Empty |
| `git diff --check` | PASS |

The Phase 9G-8H implementation and reports are therefore committed. No unexpected production Python, test, YAML, or documentation change was present at the design baseline.

## 3. Accepted Baseline And Research Question

Accepted Phase 9G-8H-2 one-update checkpoint playback:

| Metric | robot_0 | robot_1 | robot_2 |
| --- | ---: | ---: | ---: |
| Proposal noop | 300 | 0 | 248 |
| Proposal target | 0 | 300 | 52 |
| Effective idle | 300 | 0 | 239 |
| Effective executing | 0 | 300 | 61 |
| Target starts | 0 | 8 | 4 |
| Target completions | 0 | 5 | 2 |
| Budget releases | 0 | 1 | 1 |
| Contract-C noop continuation | 0 | 0 | 9 |
| Resolver rejections | 0 | 0 | 0 |

Team baseline:

```text
executing steps:          [0, 300, 61]
target completions:       [0, 5, 2]
Jain executing fairness:  0.4635069337
Jain completion fairness: 0.5632183908
```

The accepted diagnosis is policy-driven noop and workload asymmetry. The observed trajectory had no resolver rejection, exact-claim loss, ownership rejection, unavailable-target rejection, failed-pair rejection, or switch rejection. This phase does not reopen that resolver diagnosis.

Research question:

```text
Does the severe policy-noop and robot workload imbalance observed
after one rollout/update improve naturally with sufficient training,
without changing reward, resolver, observations, masks, or controller?
```

Hypotheses:

```text
H0: the imbalance is mainly an under-trained-policy artifact and
    improves through ordinary training.

H1: strong asymmetry persists after meaningful training, indicating
    a credit, reward, exploration, or actor-specialization issue.
```

This is a learning-sufficiency experiment, not a load-balancing algorithm experiment.

## 4. Source And Evidence Inspected

Current authority and accepted reports were read completely:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md
AgentRead/20260720/PHASE9G8H1_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_DIAGNOSTIC_IMPLEMENTATION_AND_FAKE_REGRESSION.md
AgentRead/20260710/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md
```

Current project source and configuration inspected:

```text
scripts/reinforcement_learning/harl/train.py
source/.../agents/harl_happo_cfg.yaml
source/.../assignment_harl_training.py
source/.../assignment_harl_wrapper.py
source/.../assignment_checkpoint_contract.py
source/.../assignment_checkpoint_save.py
source/.../assignment_lifecycle_training_contract.py
source/.../configs/scenarios/algorithm_proxy_component_mesh.yaml
```

The instruction's historical names `assignment_checkpoint_manager.py` and `assignment_training_snapshot.py` do not exist in current HEAD. Their relevant current ownership is explicit:

```text
checkpoint coordinator and atomic save:
  assignment_checkpoint_save.py

training-state completion-marker contract:
  AssignmentTrainingStateManifest
  in assignment_checkpoint_contract.py
```

Installed HARL was inspected read-only:

```text
C:/isaacenvs/isaac45_harl/Lib/site-packages/harl/
  runners/on_policy_base_runner.py
  runners/on_policy_ha_runner.py
  algorithms/actors/happo.py
  algorithms/critics/v_critic.py
  envs/isaaclab/Isaac_lab_logger.py
  utils/configs_tools.py
```

Earlier project evidence inspected:

```text
AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
AgentRead/20260630/PHASE9E2_COOLDOWN_100K_TRAINING_AND_PLAYBACK_ANALYSIS_REPORT.md
existing 9D-3, 9E-2, and 9E-4A configs and TensorBoard event metadata
existing 9G-8G-1R-2T native-v2 smoke artifacts
```

No installed file or existing result artifact was modified or loaded as a checkpoint.

## 5. Frozen Training Contract

| Field | Frozen value | Source/resolution |
| --- | --- | --- |
| Task | `Isaac-Scan-Mobile-Manipulator-Direct-v0` | CLI |
| Algorithm | HAPPO | `--algorithm happo` |
| Assignment interface | Enabled | `--assignment_rl` |
| Lifecycle profile | `lifecycle_contract_c` | Hydra override |
| HARL state type | EP | project runner default when `state_type` is absent |
| Policy sequence | Feed-forward | both recurrent flags false |
| Parameter sharing | `false` | Hydra override |
| Save mode | State dict only | `save_entire_model` absent, runner default false |
| Start mode | Fresh | no `--dir`; resolved `model_dir=None` |
| Environments | 1 | CLI |
| Robots/tasks | M=3, N=50 | scenario/robot/viewpoint configuration |
| Actor/shared/action widths | 1059 / 3183 / 51 | lifecycle contract v1 |
| Raw/decoded noop | 50 / -1 | fixed-N assignment action contract |
| Episode/rollout length | 300 | CLI override |
| Configured environment-step budget | 100000 | CLI |
| Seed | 1 | CLI |
| Device | `cuda:0` | CLI and Hydra device override |
| CUDA deterministic flag | `true` | Hydra override |
| Evaluation | Disabled | `train.py` forces `algo_args["eval"]["use_eval"] = False` |
| Video | Disabled | `--video` absent |

Frozen lifecycle behavior overrides are exactly:

```text
env.assignment_lifecycle_profile=lifecycle_contract_c
env.assignment_cooldown_enabled=true
env.assignment_cooldown_trigger_mode=budget
env.assignment_cooldown_apply_to_action_mask=false
env.assignment_redirect_guardrail_enabled=false

agent.device.cuda=true
agent.device.cuda_deterministic=true
agent.model.use_recurrent_policy=false
agent.model.use_naive_recurrent_policy=false
agent.algo.share_param=false
```

No reward, resolver, observation, mask, lifecycle, controller, optimizer, or network override is added.

## 6. Environment Count Decision

Selected value:

```text
num_envs = n_rollout_threads = 1
```

Reasons:

- The accepted lifecycle Contract C smoke used one environment successfully through collection, all actor updates, the critic update, historical-mask replay, and native checkpoint save.
- The accepted attribution baseline also used one environment, so the training and later deterministic playback remain directly comparable.
- Earlier successful 100k assignment runs used one environment and episode length 300.
- One 300-step rollout supplies 300 samples. With `actor_num_mini_batch=2` and `critic_num_mini_batch=2`, each feed-forward minibatch has 150 samples; no divisibility workaround is needed.
- M=3 robots are agents inside one environment. They are not three rollout environments.
- Increasing vectorization would change the number of updates at a fixed `num_env_steps`, memory demand, and comparison semantics merely to reduce wall-clock time.

GPU preflight at design time found an RTX 4060 Ti with 8,188 MiB total and 6,977 MiB free. The accepted one-environment lifecycle smoke already proved this model/buffer/environment configuration fits. This is a point-in-time check and must be repeated immediately before the manual run.

## 7. Step, Rollout, And Update Calculation

The installed runner computes:

```python
episodes = int(num_env_steps) // episode_length // n_rollout_threads
```

For the frozen contract:

```text
episodes/rollouts = 100000 // 300 // 1 = 333
transitions per rollout = 300 * 1 = 300
actual collected environment transitions = 333 * 300 = 99,900
unused configured remainder = 100
robot decision rows = 99,900 * 3 = 299,700
```

There is no final partial rollout. A normal successful console terminus is therefore:

```text
episodes 333/333 total num timesteps 99900/100000
```

This is the installed runner's successful completion semantics for `num_env_steps=100000`; changing the command to 100200 merely to print an exact 100000 is out of scope.

Per complete rollout the runner calls all three independent HAPPO actors once and the centralized VCritic once:

```text
actor train calls per actor: 333
actor train calls across three actors: 999
critic train calls: 333
```

With the frozen YAML values `ppo_epoch=5`, `critic_epoch=5`, and two minibatches:

```text
actor minibatch optimizer passes per actor: 333 * 5 * 2 = 3,330
actor minibatch optimizer passes total:     9,990
critic minibatch optimizer passes:          3,330
```

These are optimizer-pass counts, distinct from the 333 runner update cycles.

## 8. Episode Length And Runtime Expectation

`assignment_episode_length=300` is frozen. It matches the accepted smoke and attribution horizon and aligns with the current environment's 300-decision episode. At a done/reset boundary the environment, resolver, budget tracker, lifecycle snapshot identity, and recurrent masks follow their existing reset paths. Training then begins the next 300-step rollout from reset state. The plan expects 333 complete rollout/update boundaries.

Historical first-to-last TensorBoard log spans for comparable one-environment 100k runs were:

| Run | Log interval | First/last logged step | Log span |
| --- | ---: | --- | ---: |
| Phase 9E-2 | 1 | 300 / 99,900 | 67.0 min |
| Phase 9D-3 | 5 | 1,500 / 99,000 | 117.4 min |
| Phase 9E-4A budget | 5 | 1,500 / 99,000 | 154.3 min |

Startup, final save, machine load, and the larger lifecycle observation/model path are outside those spans. A practical planning expectation is roughly 1.25 to 3 hours, but this is not a completion promise. The user should reserve an uninterrupted multi-hour window and use no short external timeout. Normal termination is the internal runner limit, not manual interruption.

Seed 1 and deterministic CUDA mode improve repeatability of the software path. Isaac simulation and GPU execution are not claimed bitwise deterministic, and policy-quality values are not expected to match a predetermined number.

## 9. Experiment And Result Path

Frozen experiment name:

```text
assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis
```

It includes the phase, fresh-start status, configured length, and research purpose without claiming balance, success, or improvement.

Semantic parent, verified absent on 2026-07-20:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/
```

Expected run directory pattern:

```text
.../assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/
seed-00001-YYYY-MM-DD-HH-MM-SS/
```

The user must recheck parent absence immediately before execution. If it exists, do not delete, overwrite, rename, or choose a replacement automatically; stop for review.

## 10. Save Cadence

Frozen value:

```text
save_interval = 20 runner rollouts
```

`train.py` maps CLI `--save_interval` to installed HARL `train.eval_interval`. Evaluation remains disabled, but the runner still saves whenever `episode % eval_interval == 0`.

For 333 rollouts:

```text
regular save rollouts: 20, 40, ..., 320
regular save opportunities: 16
environment transitions between regular saves: 20 * 300 * 1 = 6,000
```

Save behavior:

- Each regular save targets the same `models/` directory and overwrites its state-dict artifacts atomically. No 16-checkpoint history is retained.
- `best_model/` is saved whenever the current logged `Total_Reward` exceeds the runner's prior best. With `log_interval=1`, the comparison uses the current 300-step window. The first finite window necessarily establishes an initial best; later save count is data-dependent.
- After `runner.run()` returns, project `train.py` explicitly invokes `runner.save(..., checkpoint_kind="final")`, overwriting `models/` with the final state.
- All best, regular, and final saves share one monotonically increasing generation counter. Because best-save frequency is data-dependent, no exact final generation is frozen.

Source scheduling implies one initial finite best save, 16 regular opportunities, and one final save. Thus a healthy run should have a final generation at least 17, with extra best improvements increasing it. This is a lower-bound consistency check, not an exact generation requirement. The retained `models/` child must say `checkpoint_kind=final`; the retained `best_model/` child must say `checkpoint_kind=best`; and the final generation must be newer than the retained best generation.

This cadence matches earlier successful 100k runs. Existing run-root sizes were 13.304 to 25.686 MiB, and the current native-v2 one-update lifecycle run is 14.992 MiB. Since the two checkpoint children are overwritten, disk use does not multiply by 16. Allowing for atomic temporary files, events, console/Kit logs, and safety margin, the conservative pre-run recommendation is at least 1 GiB free on both the repository drive and the system/temp drive. Design-time free space was approximately 156.9 GiB on E: and 137.3 GiB on C:.

## 11. Log Cadence And Global Step

Frozen value:

```text
log_interval = 1 runner rollout
```

Expected behavior:

```text
log emissions: 333
TensorBoard steps: 300, 600, ..., 99,900
```

For environment/assignment keys, `per_step()` accumulates one scalar per environment step. `episode_log()` records their arithmetic mean over the 300-step window and clears the accumulator. `Total_Reward` is the sum of the exact-whitelisted `assignment_rl_reward/final_reward_mean` values over that window. Actor and critic metrics summarize the update that follows the same rollout.

`log_interval=1` is selected because:

- It gives one trend point per update rather than only 66 points as in a five-rollout cadence.
- It keeps `best_model` comparison tied to the current rollout instead of a stale logger value.
- It was already used successfully in the Phase 9E-2 100k run.
- 333 points across 63 scalar tags are modest relative to simulation and optimizer cost.

No new logger or attribution path is enabled during training.

## 12. TensorBoard Tag Inventory

The accepted lifecycle smoke emitted 63 scalar tags, and current source constructs the same path. Exact inventory:

### Environment and assignment

```text
coverage_ratio
new_viewpoints
duplicate_scans
reach_violation
mean_reward
assignment_rl.duplicate_count
assignment_rl.noop_count
assignment_rl.valid_action_count
assignment_rl.selected_available_mask
```

### Budget/cooldown diagnostics

```text
assignment_cooldown.enabled
assignment_cooldown.trigger_mode_code
assignment_cooldown.active_count
assignment_cooldown.active_count_mean
assignment_cooldown.trigger_count
assignment_cooldown.trigger_count_mean
assignment_cooldown.triggered_pair_count
assignment_cooldown.suppressed_action_count
assignment_cooldown.suppressed_action_count_mean
assignment_cooldown.failed_attempt_count_mean
assignment_cooldown.max_cooldown_remaining
assignment_cooldown.max_cooldown_remaining_mean
assignment_cooldown.selected_target_was_in_cooldown_count
assignment_cooldown.last_triggered_viewpoint
assignment_cooldown.budget_multiplier
assignment_cooldown.budget_slack_steps
assignment_cooldown.budget_min_streak
assignment_cooldown.budget_trigger_count
assignment_cooldown.budget_over_budget_selected_count
assignment_cooldown.budget_triggered_pair_count
assignment_cooldown.budget_attempt_steps_mean
assignment_cooldown.budget_attempt_steps_max
assignment_cooldown.budget_steps_mean
assignment_cooldown.budget_steps_max
assignment_cooldown.budget_budget_steps_mean
assignment_cooldown.budget_budget_steps_max
assignment_cooldown.budget_ratio_mean
assignment_cooldown.budget_ratio_max
assignment_cooldown.budget_last_triggered_by_budget
assignment_cooldown.budget_last_triggered_by_budget_count
```

### Reward decomposition

```text
assignment_rl_reward/base_env_reward_mean
assignment_rl_reward/repeated_same_target_no_progress_mean
assignment_rl_reward/global_no_progress_mean
assignment_rl_reward/selected_path_cost_mean
assignment_rl_reward/total_assignment_reward_adjustment_mean
assignment_rl_reward/final_reward_mean
assignment_rl_reward/steps_since_global_coverage_gain_mean
assignment_rl_reward/global_coverage_gain_mean
Total_Reward
```

### Actor and critic updates

```text
agent0/policy_loss
agent0/dist_entropy
agent0/actor_grad_norm
agent0/ratio
agent1/policy_loss
agent1/dist_entropy
agent1/actor_grad_norm
agent1/ratio
agent2/policy_loss
agent2/dist_entropy
agent2/actor_grad_norm
agent2/ratio
critic/value_loss
critic/critic_grad_norm
critic/average_step_rewards
```

Requested-name mapping:

| Requested concept | Canonical availability |
| --- | --- |
| Total reward | `Total_Reward` |
| Final reward | `assignment_rl_reward/final_reward_mean` |
| Base environment reward | `assignment_rl_reward/base_env_reward_mean` |
| Assignment adjustment | `assignment_rl_reward/total_assignment_reward_adjustment_mean` |
| Global no-progress adjustment | `assignment_rl_reward/global_no_progress_mean` |
| Repeated-target adjustment | `assignment_rl_reward/repeated_same_target_no_progress_mean` |
| Agent entropy | `agent{0,1,2}/dist_entropy` |
| Critic average reward | `critic/average_step_rewards` |
| Budget progress/threshold | budget ratio, attempt-step, and budget-step tags above |
| Budget trigger | `assignment_cooldown.budget_trigger_count` and related trigger tags |
| Exact resolver budget release count | Not currently a TensorBoard tag |
| Per-agent raw proposal noop | Not currently a TensorBoard tag |
| Per-agent executing/start/completion/rejection | Not currently TensorBoard tags |

Important semantic limit: `assignment_rl.noop_count` is computed from `effective_assignment < 0`. It is the number of effectively idle/noop robots per environment step, in the range 0 to 3, not a per-agent raw policy-noop counter. Under Contract C, an active robot's raw noop proposal can become target continuation and is not counted as effective noop. Divide by M=3 for a team effective-idle fraction. Raw proposal noop and per-agent workload remain post-training attribution questions.

Despite its historical name, `assignment_rl.valid_action_count` is computed as `effective_assignment >= 0` summed over robots. It is the number of robots with an effective real target, not the number of unmasked actions in a policy row, and it should satisfy `noop_count + valid_action_count = 3` for this run. `assignment_rl.selected_available_mask` is the direct sampled/effective-action availability check. No TensorBoard tag currently reports full mask cardinality per actor.

Likewise, the budget TensorBoard tags expose wrapper budget diagnostics, not authoritative per-agent resolver release-event counts. Exact releases and rejection causes come from the attribution collector.

Frozen evaluation architecture:

```text
TensorBoard -> global learning and numerical-health trends
attribution playback -> exact per-agent proposal/effective behavior
```

## 13. Numerical Health And Technical Pass Criteria

The future training is technically healthy only if:

- The foreground process exits naturally with code 0.
- All 333 complete rollouts run and the console reaches `99900/100000` under the proven floor semantics.
- No traceback, resolver exception, buffer/model shape error, or empty available-action row occurs.
- Every emitted TensorBoard scalar is finite.
- All actor policy losses, entropies, ratios, and gradient norms are finite.
- Critic value loss, gradient norm, and average step reward are finite.
- Coverage, reward, noop, availability, no-progress, and budget diagnostics are finite.
- Native best, regular, and final saves complete without a manifest, ValueNorm, hash, inventory, or marker exception.

A large but finite critic gradient norm is not by itself a failure. It becomes a concern when paired with nonfinite values, persistent divergence, loss explosion, or runtime failure.

Previously observed nonblocking warning categories include SimulationApp import-order advice, missing optional crash reporter/render settings, MaterialX advice, unavailable OmniHub, deprecated dynamic control, unsupported Intel-GPU notices, and Gym maintenance advice. They remain nonblocking only when construction, updates, saves, shutdown, and exit code are healthy.

Low early reward, low coverage, high noop, or asymmetric work is not a technical training failure. Those are the experiment's policy outcomes.

## 14. Learning-Trend Review Plan

Review all trajectories, not just the final scalar. With 333 equal-length log windows, compute finite summary statistics for:

```text
early:  points 1-33,   global steps 300-9,900
middle: points 151-183, global steps 45,300-54,900
late:   points 301-333, global steps 90,300-99,900
best observed: tag-appropriate maximum or minimum, clearly labeled
final: last emitted point at 99,900
```

For each principal tag report early/middle/late means, final, best, and a simple direction-of-change summary. The mean of all equally weighted `coverage_ratio` rollout means is the run-level rollout-resolution coverage AUC proxy; it is not a formal evaluation score.

Required trend groups:

| Question | Tags and interpretation |
| --- | --- |
| Coverage learning | `coverage_ratio`, `new_viewpoints`, `assignment_rl_reward/global_coverage_gain_mean` |
| Reward learning | `mean_reward`, final/base/adjustment reward tags, `Total_Reward` |
| Effective participation/idleness | `assignment_rl.valid_action_count / 3` and `assignment_rl.noop_count / 3`; aggregate only, not raw policy noop |
| Selected-action mask health | `assignment_rl.selected_available_mask`; full mask cardinality is not logged |
| Stagnation | steps-since-gain and global/repeated no-progress adjustment tags |
| Budget pressure | budget ratio/steps and trigger tags; no direct release count |
| Environment costs | `duplicate_scans`, `reach_violation` |
| Actor behavior | policy loss, entropy, grad norm, and ratio separately for each agent |
| Critic behavior | value loss, grad norm, and average step reward |

Interpretation guardrails:

- A falling aggregate effective-noop signal supports more team execution but cannot prove which actor changed.
- Different actor entropy trajectories can indicate specialization or collapse, but entropy alone does not establish useful participation.
- Improving team reward with one actor near-zero entropy and later near-100% proposal noop is compatible with subset capture of team reward.
- Coverage/reward improvement does not prove load balance or convergence.
- Budget triggers increasing alongside participation may reflect harder task attempts rather than a resolver defect.
- Resolver release/rejection conclusions require post-training attribution rows, not TensorBoard inference.

## 15. Checkpoint Expectations

The run root is expected to contain:

```text
configs.json
progress.txt
logs/
models/
best_model/
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
```

`init_dir()` creates `models/` before training starts, and `progress.txt` may be empty. Neither path alone is completion evidence.

Completed `models/` and `best_model/` children must each contain:

```text
actor_agent_robot_0.pt
actor_agent_robot_1.pt
actor_agent_robot_2.pt
critic_agent.pt
value_normalizer.pt
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
assignment_training_state_manifest.json
```

Post-run integrity requirements:

- Manifest format is `assignment_checkpoint_contract_v2` and training-state format is `assignment_training_state_v1`.
- Run-root and child canonical manifests/fingerprints agree.
- `best_model` has `checkpoint_kind=best`.
- Final `models` has `checkpoint_kind=final` and a later valid generation than retained best.
- Contract binds lifecycle profile, 1059/3183/51 interfaces, feed-forward sequence, M=3, N=50, EP, three independent actors, episode length 300, one rollout thread, and ValueNorm v2 semantics.
- All actor, critic, and canonical ValueNorm artifacts exist; sizes, SHA-256 values, tensor inventories, and inventory hashes match the completion marker.
- The completion marker is present and no temporary artifact remains.
- No `*_full.pt`, numeric legacy actor filename, v1 lifecycle manifest, or inherited HARL checkpoint name exists.

These are validated weight-continuation candidates, not exact training-resume snapshots. Optimizer, counter, RNG, environment/resolver, and rollout-buffer states remain unavailable by contract.

## 16. Exact Manual PowerShell Command

Run exactly from `E:\Project\IsaacLab_HARL` in a foreground PowerShell session:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python -u scripts\reinforcement_learning\harl\train.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --algorithm happo `
  --assignment_rl `
  --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml `
  --num_envs 1 `
  --num_env_steps 100000 `
  --assignment_episode_length 300 `
  --save_interval 20 `
  --log_interval 1 `
  --exp_name assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis `
  --seed 1 `
  --headless `
  --device cuda:0 `
  env.assignment_lifecycle_profile=lifecycle_contract_c `
  env.assignment_cooldown_enabled=true `
  env.assignment_cooldown_trigger_mode=budget `
  env.assignment_cooldown_apply_to_action_mask=false `
  env.assignment_redirect_guardrail_enabled=false `
  agent.device.cuda=true `
  agent.device.cuda_deterministic=true `
  agent.model.use_recurrent_policy=false `
  agent.model.use_naive_recurrent_policy=false `
  agent.algo.share_param=false
```

There is no `--dir`, continuation acknowledgement, playback flag, evaluation flag, video flag, recurrent mode, full-model override, attribution logger, reward override, or mask override.

The command must remain attached and visible. Do not run it through a short Codex/tool timeout, detach it, or close the terminal. If console persistence is desired, start a uniquely named PowerShell transcript or `Tee-Object` target outside the repository before launch without changing the frozen training arguments. Record the log path and preserve the native process exit code.

## 17. Manual Pre-Run Checklist

Immediately before launch:

1. Record `git rev-parse HEAD` and `git log -1 --oneline`.
2. Require a clean source/test/YAML worktree; reviewed AgentRead-only handoff changes may be documented separately.
3. Confirm the semantic experiment parent remains absent.
4. Confirm no same-name result or console transcript will be overwritten.
5. Confirm at least 1 GiB free on E: and C: under the evidence-based assumptions above.
6. Confirm GPU 0 is visible and has capacity comparable to the accepted smoke.
7. Confirm no residual repository Python, conda-run, Isaac Sim, or Kit process exists.
8. Confirm `D:\miniconda3\Scripts\conda.exe`, `C:\isaacenvs\isaac45_harl\python.exe`, the training script, scenario, and HAPPO YAML exist.
9. Start from repository root `E:\Project\IsaacLab_HARL`.
10. Visually confirm the frozen command contains no `--dir`.
11. Record console transcript location, start time, and intended foreground terminal.

Design-time checks passed: all five required paths existed, the experiment parent was absent, no relevant process was found, and disk/GPU headroom exceeded the recommendation. These checks expire as machine state changes.

## 18. During-Run Monitoring And Failure Handling

Safe observations:

- The single foreground process remains active.
- GPU utilization and memory remain plausible.
- Exactly one timestamped seed directory appears under the semantic parent.
- The TensorBoard event file grows and rollout log emissions continue.
- Console global steps progress by 300 toward `99900/100000`.
- At rollout 20 and later save points, `models/assignment_training_state_manifest.json` reappears after each atomic save.
- `best_model/` appears after the first finite logged window.

Do not edit result files, overwrite checkpoints, launch another same-name run, change source/config while training, or interrupt only because early policy/reward values are noisy.

Hard stop/failure conditions include process crash, nonzero exit, traceback, nonfinite scalar, model/buffer/mask/resolver exception, checkpoint exception, contract mismatch, or corrupt/missing completion metadata. On failure:

```text
do not retry automatically
do not patch and relaunch
preserve the console and partial result directory
record exit code and last printed rollout/global step
send the evidence for review
```

## 19. Post-Run Review Checklist

Before any playback:

1. Record natural process exit code, end time, elapsed time, and exact timestamped run directory.
2. Verify console reached rollout 333 and `99900/100000` with no traceback.
3. Parse the TensorBoard event file; require expected step coverage and finite values for every tag.
4. Produce early/middle/late/best/final trend summaries from Section 14.
5. Confirm `configs.json` records `dir=null`, `model_dir=null`, the frozen profile, seed, dimensions, feed-forward flags, one environment, and the exact cadence.
6. Validate run-root and child contract-v2 manifests and canonical fingerprints.
7. Validate final and best checkpoint kinds/generations, actor order, artifact sizes, SHA-256 values, tensor inventories, ValueNorm mapping, and completion markers.
8. Scan for temporary, full-model, legacy numeric actor, or v1 artifacts.
9. Do not load either checkpoint during this integrity review.
10. Do not infer success merely from the eagerly created `models/` directory.

## 20. Separate Best/Final Attribution Plan

Only after the training and checkpoint/TensorBoard review passes may a later explicitly authorized phase run two separate deterministic attribution playbacks:

```text
A. best_model/
B. models/ final
```

Each must use one environment, seed 1, max steps 300, the same scenario, `lifecycle_contract_c`, feed-forward policy, `share_param=false`, and the accepted attribution collector. Each must use a fresh noncolliding output directory. They are not automatically launched at training completion.

Required per-checkpoint outputs:

```text
per-agent proposal noop and target counts
per-agent effective idle and executing steps
proposal/effective changed counts
resolver rejection counts and reasons
Contract-C noop continuation counts
target starts, completions, budget releases, and segments
zero-command and zero-motion diagnostics
Jain executing and completion fairness
```

Frozen comparison baseline is exactly:

```text
proposal noop:            [300, 0, 248]
effective idle:           [300, 0, 239]
executing steps:          [0, 300, 61]
target completions:       [0, 5, 2]
Jain executing fairness:  0.4635069337
Jain completion fairness: 0.5632183908
resolver rejections:      all zero
```

## 21. Decision Framework After 100k

### Outcome A: Natural Participation Improvement

Robot 0 proposes and executes real targets, robot 2 effective idleness falls, all robots start targets, team coverage/reward trends improve, and numerical health remains sound. Do not change reward or resolver. Review whether a separately named 300k experiment and later multi-seed evaluation are justified; do not launch them automatically.

### Outcome B: Team Learning Improves But Robot 0 Remains Noop-Collapsed

Coverage/reward improve while robot 1 performs most work and robot 0 remains near 100% proposal noop with zero or almost zero starts. Candidate explanations are team-reward capture by a subset, weak per-agent credit, insufficient noop opportunity cost, or asymmetric specialization. Enter a policy-noop/load-participation design phase; do not modify the resolver.

### Outcome C: High Noop And Weak Team Learning Persist

Investigate relative noop utility, actor exploration/entropy, reward scale, credit delay from long execution, and global no-progress shaping. This is still not evidence for a resolver change.

### Outcome D: Participation Improves But Budget Failure Dominates

Investigate task feasibility, completion conditions, controller execution, and cost-model versus execution-difficulty mismatch. Do not automatically classify this as a load-balancing failure.

### Outcome E: Numerical Or Checkpoint Instability

For any nonfinite scalar, crash, invalid metric, or checkpoint corruption, stop policy-quality interpretation and diagnose runtime/training integrity first.

Healthy load use does not mean equal work. Robots have heterogeneous capability and path constraints. The objective is to use capable available robots, exploit useful parallel execution, avoid unnecessary long idle periods and avoidable bottlenecks, and reduce team completion time. Exactly one-third of completions, identical executing steps, or Jain fairness 1.0 are not requirements. Fairness is diagnostic, not an optimizer target or standalone pass criterion.

## 22. Non-Goals And Remaining Risks

This phase does not:

```text
change reward, resolver, Contract C, observations, masks, controller, or environment
change optimizer/model/YAML defaults
load or continue a checkpoint
run training, playback, evaluation, GUI, video, AppLauncher, or Isaac Sim
claim convergence, policy quality, balance, or deterministic reproducibility
authorize automatic retry, 300k extension, second seed, or mechanism tuning
```

Known planning limits:

- Current training TensorBoard cannot identify per-agent raw noop or exact resolver releases.
- `num_env_steps=100000` intentionally produces 99,900 collected transitions under installed floor semantics.
- Intermediate regular checkpoints are overwritten.
- `best_model` is selected by rollout `Total_Reward`, not by attribution fairness or deterministic playback quality.
- One seed cannot establish generalization or statistical significance.
- Wall-clock duration varies substantially across existing runs.

Required order after the user-run experiment:

```text
fresh 100k execution
-> checkpoint and TensorBoard review
-> separately authorized best/final attribution playbacks
-> exact comparison with the 8H-2 baseline
-> decision on 300k, diagnostics, or mechanism design
```

## 23. Files And Next Boundary

Created in Phase 9G-8I-0:

```text
AgentRead/20260720/PHASE9G8I0_POLICY_NOOP_LOAD_IMBALANCE_CONTROLLED_TRAINING_DESIGN_AND_PREFLIGHT.md
AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I0_CONTROLLED_TRAINING_DESIGN_20260720.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

No production source, test, YAML, installed HARL, Conda environment, checkpoint behavior, or runtime result was changed.

Next phase, after review only:

```text
Phase 9G-8I-1:
User-Executed Fresh 100k Controlled Training
```

The user, not Codex, executes the frozen command manually. No automatic retry or code/config change is permitted.
