# Phase 9G-8G-0: Controlled Training Smoke Design and Preflight

Date: 2026-07-10

## 1. Classification

```text
SMOKE-PLAN-READY
```

An exact, bounded, fresh-start command can exercise one complete
`lifecycle_contract_c` rollout/update and the native assignment checkpoint path
without further source or configuration-file changes.

This phase performed static inspection and lightweight configuration/path checks
only. It did not run the command.

## 2. Accepted Baseline

Inspected clean commit baseline:

```text
8a5f46cb feat(assignment): complete lifecycle training checkpoint readiness
```

`git status --short --untracked-files=all` was empty before this documentation
phase. Accepted prior Phase 9G-8F-6R classifications were
`CONTROLLED-TRAINING-SMOKE-READY` and `COMMIT-READY`. The user committed the
reviewed Phase 9G-8 implementation before this design phase.

## 3. Files

Created:

```text
AgentRead/20260710/PHASE9G8G0_CONTROLLED_TRAINING_SMOKE_DESIGN_AND_PREFLIGHT.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G0_SMOKE_DESIGN_20260710.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

Explicitly not modified:

```text
production Python
project tests
YAML/runtime defaults
installed HARL
Conda environment
resolver or Contract C behavior
observation, mask, reward, controller, checkpoint, or loader behavior
```

## 4. Source Boundaries Inspected

Project source/configuration:

```text
scripts/reinforcement_learning/harl/train.py
assignment_harl_training.py
assignment_harl_wrapper.py
assignment_lifecycle_training_contract.py
assignment_checkpoint_save.py
scenario_config.py
scan_mobile_manipulator_env.py
agents/harl_happo_cfg.yaml
configs/scenarios/algorithm_proxy_component_mesh.yaml
configs/viewpoints/component_mesh_jittered_n50.csv
configs/robots/robots_real_proxy.yaml
isaaclab_tasks/utils/hydra.py
isaaclab/app/app_launcher.py
```

Installed HARL, read-only:

```text
harl/runners/on_policy_base_runner.py
harl/runners/on_policy_ha_runner.py
harl/algorithms/actors/happo.py
harl/algorithms/critics/v_critic.py
harl/common/buffers/on_policy_actor_buffer.py
harl/common/buffers/on_policy_critic_buffer_ep.py
harl/common/base_logger.py
harl/envs/isaaclab/Isaac_lab_logger.py
harl/utils/configs_tools.py
harl/utils/envs_tools.py
harl/utils/models_tools.py
```

Phase 9G-8F-4 and Phase 9G-8F-5 reports were read completely for the accepted
model, buffer, state-dict save/load, ValueNorm, and continuation boundaries.

## 5. Actual CLI and Configuration Audit

`train.py` uses `argparse.parse_known_args()`. Recognized options stay in
`args_cli`; remaining `env.*` and `agent.*` tokens are passed to Hydra. Hydra
registers a root dictionary with `env` and `agent` blocks and updates the
environment config and HARL dictionary before `main()` runs.

The selected scenario provides N=50 and M=3, but provides neither a lifecycle
profile nor a cooldown profile. Its scenario-bridge values are therefore
`assignment_lifecycle_profile=None` and `assignment_cooldown_enabled=None`.
Environment class defaults remain in force unless the command supplies Hydra
overrides.

| planned value | exact syntax/source | consumer | effective value | default difference |
|---|---|---|---|---|
| Task | `--task Isaac-Scan-Mobile-Manipulator-Direct-v0` | parser/Hydra registry | registered scan task | Explicit; scenario agrees |
| Algorithm | `--algorithm happo` | parser/runner registry | HAPPO | Explicit default |
| Assignment mode | `--assignment_rl` | `train.py` | project assignment runner/wrapper | Changes false |
| Scenario | `--scenario_config .../algorithm_proxy_component_mesh.yaml` | pre-parser/scenario bridge | fixed N=50 scenario | Explicit |
| Lifecycle profile | `env.assignment_lifecycle_profile=lifecycle_contract_c` | Hydra/wrapper | Contract C observation, mask, resolver | Changes `legacy` |
| Budget source | `env.assignment_cooldown_enabled=true` | wrapper budget tracker | enabled | Changes false |
| Budget trigger | `env.assignment_cooldown_trigger_mode=budget` | wrapper budget trigger | budget-only | Changes `streak` |
| Legacy cooldown mask | `env.assignment_cooldown_apply_to_action_mask=false` | profile validation | disabled | Changes true |
| Redirect guardrail | `env.assignment_redirect_guardrail_enabled=false` | wrapper | disabled | Explicit default |
| Legacy failed-pair TTL | no override | wrapper absent-field fallback | disabled | Default false |
| Environments | `--num_envs 1` | scene and HARL threads | one vector environment | Explicit scenario value |
| Environment steps | `--num_env_steps 300` | HARL train config | 300 | Changes 10,000,000 |
| Rollout length | `--assignment_episode_length 300` | assignment helper | 300 | Changes 1000 |
| Log interval | `--log_interval 1` | HARL train config | every update | Changes 5 |
| Save interval | `--save_interval 1` | mapped to `train.eval_interval` | every update | Changes 25 |
| Evaluation | source forces `algo_args["eval"]["use_eval"]=False` | `train.py` | disabled | Changes YAML true |
| Video | omit `--video` | `train.py` | disabled | Default false |
| Headless | `--headless` | AppLauncher parser | true | Overrides scenario false |
| Simulation device | `--device cuda:0` | AppLauncher/environment | CUDA 0 | Explicit default |
| HARL CUDA | `agent.device.cuda=true` | Hydra/HARL | enabled | Explicit YAML |
| CUDA deterministic | `agent.device.cuda_deterministic=true` | HARL | deterministic cuDNN setting | Explicit YAML |
| Seed | `--seed 1` | HARL `set_seed` | 1 | Explicit first seed |
| Experiment | `--exp_name assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh` | HARL `init_dir` | unique parent | Changes `test` |
| Recurrent | `agent.model.use_recurrent_policy=false` | guard/HAPPO | false | Explicit YAML |
| Naive recurrent | `agent.model.use_naive_recurrent_policy=false` | guard/HAPPO | false | Explicit YAML |
| Sharing | `agent.algo.share_param=false` | guard/runner | three actors | Explicit YAML |
| State type | no CLI field; `env_args.get("state_type", "EP")` | guard/runner | EP | Project default |
| Full-model save | absent-key fallback false | guard/runner | state_dict only | Project fallback |
| Continuation | omit `--dir` | `train.py` | `model_dir=None` | Fresh start |

The command does not add undeclared resolver logging fields to the structured
Hydra environment config. The profile is the authoritative resolver-enable
boundary.

## 6. Frozen Lifecycle Configuration

The command resolves:

```text
profile: lifecycle_contract_c
training_allowed: true
resolver: enabled by profile
lifecycle observation and Contract C mask: enabled
budget tracker: enabled
budget trigger mode: budget
legacy cooldown mask overlay: disabled
redirect guardrail: disabled
legacy failed-pair TTL memory: disabled by wrapper default
algorithm/state: HAPPO / EP
policy sequence: feed-forward
share_param: false
checkpoint serialization: state_dict
```

`budget` is selected instead of `budget_and_streak` so this smoke exercises the
frozen budget-release source without adding the legacy streak condition. It does
not change the integer budget formula or release predicate.

## 7. Minimal Environment Count

Decision:

```text
n_rollout_threads = num_envs = 1
M = 3 robots inside that environment
N = 50 tasks/viewpoints
```

The installed feed-forward generators calculate:

```text
batch_size = episode_length * n_rollout_threads
           = 300 * 1
           = 300
actor_num_mini_batch = 2
critic_num_mini_batch = 2
mini_batch_size = 300 // 2 = 150
```

Both generators require `batch_size >= num_mini_batch`. All 300 samples are
consumed, so one vector environment is valid. The three agents have separate
300-sample actor buffers; they are not three rollout threads. The EP critic has
one 300-sample shared-state trajectory. ValueNorm imposes no larger thread
minimum on this feed-forward path.

## 8. Episode-Length Decision

Decision:

```text
--assignment_episode_length 300
```

The environment uses a 30-second horizon, `dt=1/60`, and decimation 6, giving a
policy step near 0.1 seconds and an environment horizon near 300 policy steps.
The existing assignment-only override has been used for earlier N=50 smokes. It
aligns one HARL rollout with that horizon and permits warmup, resolver steps,
buffer insertion, lifecycle transitions, and an update.

No environment episode semantics change; only the HARL rollout-buffer length is
selected through the supported assignment option.

## 9. Step and Update Calculation

Installed HARL computes:

```text
episodes = floor(num_env_steps / episode_length / n_rollout_threads)
         = floor(300 / 300 / 1)
         = 1

steps per runner update = 300
completed rollout/update cycles = 1
```

That cycle performs three HAPPO actor train calls and one centralized VCritic
train call. With five epochs and two minibatches, each actor receives 10 optimizer
minibatch updates and the critic receives 10. A value below 300 would produce
zero HARL episodes and is invalid.

## 10. Save and Checkpoint Schedule

Planned:

```text
log_interval = 1
save_interval = 1
```

`train.py` maps save interval to HARL `eval_interval`. Installed HARL saves on a
matching interval even though evaluation itself is disabled.

Expected successful save order:

```text
1. episode_log sets finite Total_Reward; initial best_avg_reward is -Inf
2. best_model/ native save: kind=best, generation=0
3. models/ interval native save: kind=regular, generation=1
4. runner.run() returns
5. train.py models/ explicit save: kind=final, generation=2
```

The final save replaces the regular `models/` state and commits its completion
marker last. Final `models/assignment_training_state_manifest.json` should report
`checkpoint_kind=final`, `checkpoint_generation=2`, and a null update index.

Expected run-root files:

```text
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
configs.json
progress.txt
logs/<TensorBoard event file>
models/
best_model/
```

Expected files in each complete native checkpoint child:

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

Any `*_full.pt` artifact or inherited checkpoint behavior is prohibited. No
episode snapshot is configured.

## 11. Unique Experiment and Output Safety

Frozen experiment name:

```text
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh
```

Expected result pattern:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh/
seed-00001-YYYY-MM-DD-HH-MM-SS/
```

Static preflight confirmed the semantic experiment parent does not exist. It is
under the established results root, not source. The next phase must recheck
immediately before execution and choose another unique name rather than delete or
reuse a collision.

## 12. Exact Recommended Command

Run from repository root in the next reviewed phase only:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python -u scripts/reinforcement_learning/harl/train.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --algorithm happo `
  --assignment_rl `
  --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml `
  --num_envs 1 `
  --num_env_steps 300 `
  --assignment_episode_length 300 `
  --save_interval 1 `
  --log_interval 1 `
  --exp_name assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh `
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

Each command line except the last ends with PowerShell's backtick continuation character.

The command contains no `--dir`, continuation acknowledgement, `--video`,
playback option, evaluation-enabling option, recurrent mode, or full-model save
option. `save_entire_model=false` and `state_type=EP` are not ordinary
`train.py` flags; they resolve through the reviewed defaults above, and the
lifecycle startup validator hard-fails an incompatible effective contract.

## 13. Seed and Determinism

Seed 1 is frozen. HARL seeds Python, NumPy, PyTorch CPU, and PyTorch CUDA.
`cuda_deterministic=true` disables cuDNN benchmarking and enables deterministic
cuDNN behavior.

Isaac simulation, GPU scheduling, and sampled trajectories are not promised to
match bitwise across systems. Expected repeatability is limited to configuration,
contract, dimensions, schedule, and artifact layout. Reward and coverage need not
match predetermined numbers.

## 14. Runtime Evidence Checklist

Startup:

```text
[ ] profile lifecycle_contract_c and training gate accepted
[ ] HAPPO, EP, share_param=false
[ ] both recurrent flags false; feed_forward_generator_actor selected
[ ] save_entire_model=false; no restore/model_dir
[ ] M=3 and N=50
```

Interface/mask:

```text
[ ] actor observation width 1059
[ ] shared observation width 3183
[ ] Discrete action width 51 and raw noop id 50
[ ] reset available_actions [1,3,51]
[ ] no all-zero row; noop always available
[ ] collect forwards per-agent available_actions
[ ] actor buffers store historical available_actions
```

Progression:

```text
[ ] environment construction and reset/warmup succeed
[ ] 300 resolver-enabled steps complete
[ ] actor actions and actor/critic buffer insertions succeed
[ ] one HAPPO runner update and one VCritic runner update occur
[ ] logger reports update 1/1 and timesteps 300/300
```

Numerical health requires all emitted reward, assignment, loss, entropy, ratio,
gradient-norm, and average-step-reward scalars to be finite. Current logging does
not emit every raw observation or raw critic value. Their health is checked
indirectly by successful finite forward/loss/backward/optimizer paths and absence
of tensor/runtime exceptions; do not claim exhaustive raw-tensor telemetry.

Checkpoint:

```text
[ ] best, regular, and explicit final native saves complete
[ ] final models marker is kind=final, generation=2
[ ] run-root and models manifest/fingerprint pairs exist
[ ] three actor, one critic, and one ValueNorm state_dict exist
[ ] completion marker exists and no full-model artifact exists
```

A successful feed-forward update is evidence that sampling masks stored in the
actor buffer reach the generator and `evaluate_actions`; no historical mask may
be regenerated from current resolver state.

## 15. Existing Metrics Audit

Hard health metrics actually logged:

| source | metrics |
|---|---|
| Environment `info["log"]` | `coverage_ratio`, `new_viewpoints`, `duplicate_scans`, `reach_violation`, `mean_reward` |
| Assignment reward | `base_env_reward_mean`, `repeated_same_target_no_progress_mean`, `global_no_progress_mean`, `selected_path_cost_mean`, `total_assignment_reward_adjustment_mean`, `final_reward_mean`, `steps_since_global_coverage_gain_mean`, `global_coverage_gain_mean` |
| HAPPO per actor | `policy_loss`, `dist_entropy`, `actor_grad_norm`, `ratio` |
| VCritic | `value_loss`, `critic_grad_norm`, `average_step_rewards` |

Informational metrics actually logged when present:

```text
assignment_rl.duplicate_count
assignment_rl.noop_count
assignment_rl.valid_action_count
assignment_rl.selected_available_mask
assignment_cooldown.enabled
assignment_cooldown.trigger_count
assignment_cooldown.triggered_pair_count
assignment_cooldown.budget_trigger_count
assignment_cooldown.budget_triggered_pair_count
assignment_cooldown.budget_attempt_steps_mean/max
assignment_cooldown.budget_steps_mean/max
assignment_cooldown.budget_ratio_mean/max
```

The wrapper retains the latest resolver resolution in memory, but
`AssignmentIsaacLabEnv._update_log_info()` does not flatten it into the training
logger. Resolver CSV/JSON fields are not declared in this structured training env
config. The smoke therefore proves resolver activation through the profile,
manifest, lifecycle dimensions/mask, uninterrupted stepping, and budget
diagnostics, but cannot claim a persisted per-event resolver audit.

Coverage, reward magnitude if finite, duplicate count, noop rate, allocation
quality, curve direction, and complete N=50 coverage are performance observations,
not PASS gates.

## 16. Hard Failure Conditions

Stop and classify FAIL for:

```text
profile, HAPPO, EP, feed-forward, share-param, or serialization mismatch
training gate rejection or unexpected restore/continuation
environment construction/reset failure
M/N or 1059/3183/51/50 mismatch
snapshot, resolver, ownership, mask, or generation exception
empty mask row, unavailable noop, or sampled action invalid under mask
actor/critic buffer or HAPPO/VCritic update exception
NaN/Inf in required emitted runtime values
native save exception or missing/invalid metadata/artifacts
unexpected full-model artifact
process crash or nonzero exit
```

Do not continue after contract or numerical-integrity failure merely to collect
logs. Manual interruption is emergency-only.

## 17. Non-Failure Conditions

These do not automatically fail this one-update integration smoke:

```text
low coverage or low finite reward
high duplicate count or many noops
no budget release in one sampled trajectory
unstable-looking one-point reward curve
poor allocation quality or lack of convergence
```

Pathological finite values must still be reported and may yield
`PASS WITH FOLLOW-UP`.

## 18. Normal Stop Condition

Normal success is bounded by `num_env_steps=300`:

```text
300 steps reached
one rollout/update completes
runner.run() returns
explicit final save completes
runner and simulation app close
process exits 0
```

Do not use Ctrl+C, a wall-clock timeout, or episode completion as the normal stop.

## 19. Post-Run Inspection

The next phase must:

1. Record process exit code and exact printed run/model directories.
2. Confirm exactly one new timestamped child under the frozen experiment parent.
3. Inspect console for contract, shape, mask, resolver, buffer, update, and save errors.
4. Confirm update 1/1 and 300/300 timesteps.
5. Inspect TensorBoard tags/scalars and reject NaN/Inf required metrics.
6. Inspect `models/` and `best_model/` names without deserializing `.pt` files.
7. Parse run-root and `models/assignment_contract_manifest.json`.
8. Read/compare root and child fingerprints and recompute canonical manifest SHA-256 with the accepted contract utility.
9. Parse `models/assignment_training_state_manifest.json` and verify final kind, generation, binding, actor order, artifact sizes/digests, and tensor inventory metadata.
10. Confirm all declared artifacts and absence of full-model artifacts.
11. Check the completion marker is not older than artifacts; source/test evidence remains authoritative for exact write order.
12. Record `best_model/` metadata separately.
13. Run no playback, evaluation, comparison, checkpoint load, or continuation.

## 20. Smoke Classification

`PASS` requires exit 0, construction/warmup, all contract guards, active
1059/3183/51/50 interfaces, 300 resolver-enabled steps, one HAPPO/VCritic update,
finite required emitted values, regular and final native saves, and valid final
completion metadata.

`PASS WITH FOLLOW-UP` applies only when integration/numerical gates pass but
finite nonblocking anomalies such as high noop rate or surprising diagnostic
counters need interpretation.

Any hard failure in Section 16 is `FAIL`.

## 21. Remaining Risks

- One update and seed cannot establish learning quality, convergence, or lifecycle behavior distribution.
- Raw observations and raw critic values are not persisted; finite update statistics are indirect evidence.
- Per-event resolver rows are not persisted by this training entry.
- The natural best save adds I/O but validates another inherited save call site.
- Isaac/GPU execution is not guaranteed bitwise deterministic.
- Exact resume, recurrent lifecycle, FP, sharing, HATRPO, HAA2C, and long/general training remain unsupported or unauthorized.

## 22. Static Preflight Results

```text
Python: C:\isaacenvs\isaac45_harl\python.exe
scenario/default resolution: PASS
required source/config/data paths: PASS
N=50 CSV: 51 text lines including header
M=3 robot config: robot_0, robot_1, robot_2 enabled
semantic experiment parent collision: absent
git diff --check before documentation edits: PASS
TASK_PROGRESS archive matches committed pre-edit handoff: PASS
final documentation git diff --check: PASS (line-ending warning only)
final git status scope: exactly this report, the archive, and TASK_PROGRESS
```

`train.py --help` was not run because executing that module proceeds toward
AppLauncher construction. Parser behavior was established from source.

## 23. Next-Phase Boundary

The next reviewed phase may execute exactly the command in Section 12 after
rechecking the committed source baseline and experiment collision. It may collect
console/log/checkpoint metadata and classify the result. It may not run playback,
evaluation, checkpoint continuation, multiple seeds, a longer run, or performance
comparison.

A successful smoke must be reviewed before deciding whether to allow a slightly
longer controlled run, require a corrective phase, or require more diagnostics.
General or long resolver-enabled training remains prohibited.

## 24. Final Recommendation

```text
SMOKE-PLAN-READY
```

Execute one fresh-start, 300-step, one-environment, one-update
`lifecycle_contract_c` HAPPO/EP/feed-forward smoke in the next phase using the
exact command, then stop for review.

Confirmation:

```text
training: not run
AppLauncher / Isaac Sim: not launched
assignment environment: not constructed
checkpoint: not created or loaded
playback/evaluation: not run
production/test/YAML behavior: not modified
installed HARL/Conda: not modified
commit: not made
```
