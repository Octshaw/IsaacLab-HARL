# Phase 9G-8G-1: Controlled Resolver-Enabled Training Smoke Execution Report

## Classification

```text
FAIL
```

The one permitted fresh-start smoke reached a full 300-step rollout and the
first HAPPO/VCritic updates with finite TensorBoard metrics. It then failed at
the first native `best_model` save because the runtime ValueNorm `state_dict`
was empty. No retry was run.

## Baseline And Preflight

```text
HEAD: 8a5f46cbce252df554cb5ea961ed2bd25875bfd2
subject: feat(assignment): complete lifecycle training checkpoint readiness
```

The working tree contained only the permitted uncommitted Phase 9G-8G-0
documentation handoff. No production Python, tests, YAML, or runtime
configuration files differed from the committed baseline. The frozen semantic
experiment parent was absent before execution.

## Exact Command

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

The command was executed once from the repository root, without output
redirection, continuation directory, checkpoint load, or parameter alteration.

## Process And Result Location

```text
process exit code: 1
measured process elapsed time: 137.5 seconds
console-emitted start timestamp: 2026-07-10 01:42:59
last console runtime timestamp: 2026-07-10 01:45:09
```

The console timestamps did not declare a timezone. The runner-created directory
uses the local run-name timestamp below; its TensorBoard event was last written
at local filesystem time `2026-07-10 09:45:08.264`.

```text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh\
seed-00001-2026-07-10-09-44-31
```

The result directory is preserved. Nothing in it was deleted, moved, loaded, or
modified during inspection.

## Active Runtime Contract

Runtime console output and the persisted `configs.json` establish:

| Contract item | Observed value |
| --- | --- |
| Assignment profile | `lifecycle_contract_c` |
| Lifecycle training gate | accepted (`training_allowed=true`) |
| Lifecycle policy sequence | `lifecycle_feed_forward_v1`; `feed_forward_generator_actor` |
| Algorithm / state | HAPPO / EP |
| Recurrent flags | both `false` |
| `share_param` | `false` |
| `save_entire_model` | `false` |
| Continuation directory | `None` / no `--dir` |
| Vector environments | 1 |
| Robots / viewpoints | 3 / 50 |
| HARL episode length / environment steps | 300 / 300 |
| Actor observation width | 1059 |
| Shared observation width | 3183 |
| Action width / raw noop | 51 / 50 |
| Reset available-action tensor | `[1, 3, 51]` |

The lifecycle profile, feed-forward generator, actor/shared widths, action
width, and raw noop value all matched the frozen smoke contract. No checkpoint
was loaded, and no full-model checkpoint path was requested.

## Runtime Progression

The following stages completed before the save failure:

1. AppLauncher and headless Isaac Sim initialized on `cuda:0`.
2. The assignment environment constructed with one vectorized environment,
   three robots, and 50 viewpoints.
3. Initial reset and HARL warmup succeeded; the actor buffer recorded
   available-actions with per-agent buffer shape `(301, 1, 51)`.
4. The three categorical actors and centralized critic constructed.
5. The resolver-enabled lifecycle profile collected 300 policy steps.
6. The logger reached `episodes 1/1` and `total num timesteps 300/300`.
7. The HAPPO actor updates and the VCritic update completed, producing the
   TensorBoard metrics below.

The first native `best_model` checkpoint save began after those successful
updates. `runner.run()` did not return normally, the regular `models/` interval
save did not occur, and the explicit final save did not run.

## Mask And Resolver Evidence

No empty-mask assertion, sampled-action-under-mask exception, resolver
ownership/arbitration exception, or lifecycle snapshot-generation exception was
emitted. The completed feed-forward collection and update are runtime evidence
that sampled available-actions reached the actor buffer and update path.

Logged values at step 300 were:

```text
assignment_rl.valid_action_count: 2.99333333969
assignment_rl.selected_available_mask: 0.997777760029
assignment_rl.noop_count: 0.0066666668281
assignment_rl.duplicate_count: 0
assignment_cooldown.enabled: 1
assignment_cooldown.trigger_mode_code: 1
assignment_cooldown.budget_trigger_count: 2.24666666985
assignment_cooldown.budget_ratio_mean: 0.41631513834
assignment_cooldown.budget_ratio_max: 0.628273785114
```

These logs do not contain raw per-decision resolver records, so they are not
evidence of exhaustive resolver telemetry. They do establish that the enabled
collection, mask, historical-mask buffer, and update path remained operational
through the first update.

## Numerical Health And Emitted Metrics

The TensorBoard event file was parsed read-only. Every scalar tag at step 300
was finite (`NONFINITE=[]`). `progress.txt` is zero bytes; it contained no
additional metrics.

| Metric | Value |
| --- | ---: |
| `agent0/policy_loss` | -0.0115504423 |
| `agent0/dist_entropy` | 0.753697932 |
| `agent0/actor_grad_norm` | 1.03380108 |
| `agent0/ratio` | 0.99821198 |
| `agent1/policy_loss` | -0.0476728156 |
| `agent1/dist_entropy` | 0.76975584 |
| `agent1/actor_grad_norm` | 1.12176597 |
| `agent1/ratio` | 1.00383878 |
| `agent2/policy_loss` | -0.0822565109 |
| `agent2/dist_entropy` | 0.757230282 |
| `agent2/actor_grad_norm` | 0.873426616 |
| `agent2/ratio` | 0.988938153 |
| `critic/value_loss` | 1.78450978 |
| `critic/critic_grad_norm` | 27.3145943 |
| `critic/average_step_rewards` | 0.0193992741 |
| `coverage_ratio` | 0.322666645 |
| `new_viewpoints` | 0.0866666660 |
| `duplicate_scans` | 0.0433333330 |
| `reach_violation` | 0 |
| `mean_reward` | 0.477627277 |
| `Total_Reward` | 21.9448433 |
| `assignment_rl_reward/final_reward_mean` | 0.0731494799 |
| `assignment_rl_reward/total_assignment_reward_adjustment_mean` | -0.404477775 |

The finite values are runtime-health evidence only. Coverage, reward, duplicate
scans, no-op count, and allocation quality are not performance pass/fail
criteria for this one-update integration smoke.

## Hard Failure: Native ValueNorm Save

The process failed during the first native `best_model` save with:

```text
AssignmentCheckpointSaveError: value normalizer state_dict must not be empty
```

The recorded stack reached:

```text
harl.runners.on_policy_base_runner.OnPolicyBaseRunner.save (best_model)
assignment_harl_training.py:664
assignment_checkpoint_save.py:849
assignment_checkpoint_save.py:502
```

`build_tensor_inventory_from_state_dict()` rejects an empty state dictionary at
`assignment_checkpoint_save.py:501-502`. The runtime passed an empty ValueNorm
state dictionary into that validation at lines 846-852. Read-only inspection of
the installed `harl/common/valuenorm.py` also found the ValueNorm running fields
created as `nn.Parameter(...).to(**self.tpdv)` at lines 28-35, a source pattern
consistent with the observed empty registration/state-dictionary result under
the pinned environment. This is an investigation lead, not a replacement for a
separate root-cause/corrective review.

This failure is a checkpoint save-path failure. It is not evidence of a
lifecycle observation, lifecycle mask, resolver, action-space, actor-update, or
critic-update failure.

## Artifact And Manifest Inspection

Read-only file inspection found only these run artifacts:

```text
configs.json                                  47,408 bytes
progress.txt                                  0 bytes
logs/events.out.tfevents.1783647871.xxsys203-1 4,621 bytes
logs/summary.json                             2 bytes
models/                                       empty directory
```

The following required artifacts are absent:

```text
run-root assignment_contract_manifest.json
run-root assignment_contract_fingerprint.txt
best_model/
models/ actor_agent_robot_0.pt through actor_agent_robot_2.pt
models/ critic_agent.pt
models/ value_normalizer.pt
models/ assignment_training_state_manifest.json
best_model/ assignment_training_state_manifest.json
```

No `.pt`, `*_full.pt`, contract manifest, fingerprint, or training-state
completion marker exists below the run root. Consequently there was no manifest
or fingerprint to parse, no artifact size/SHA-256 digest to verify, no checkpoint
generation to validate, and no completion-marker ordering evidence. The absence
of any `*_full.pt` artifact is confirmed.

## Checkpoint Outcome And Hard-Failure Scan

| Required boundary | Result |
| --- | --- |
| Best checkpoint, generation 0 | Failed before any artifact write |
| Regular `models/` save, generation 1 | Not reached |
| Explicit final `models/` save, generation 2 | Not reached |
| Run-root contract manifest and fingerprint | Not written |
| Child training-state completion markers | Not written |
| Artifact hash/size verification | Not applicable; no checkpoint artifacts exist |
| Full-model artifact scan | Passed; no `*_full.pt` artifact exists |

The `AssignmentCheckpointSaveError` above is the hard failure that determines
the classification. Isaac shutdown emitted warnings about outstanding stage
history and recursive plugin unload after the exception; they are not the
recorded cause of the nonzero exit and do not replace the checkpoint failure.

## Nonblocking Observations

No nonblocking anomaly changes the `FAIL` classification. The short-run
coverage, reward, no-op, and duplicate-scan values are informational only and
must not be used to infer convergence or policy quality. Cooldown budget
diagnostics were emitted and finite; raw observation, raw critic-value, and
per-event resolver telemetry are not persisted by the current logger.

## Remaining Limitations

This one-run result validates only the collection and first update portion of
the enabled runtime path. It does not validate a native checkpoint save, a
fingerprint/manifests pair, checkpoint loading, continuation, playback,
evaluation, longer training, or any performance claim. Those boundaries remain
unvalidated because the checkpoint coordinator rejected the empty ValueNorm
state before writing the first best-model artifact.

## Failure Boundary And Next Decision

This phase is `FAIL` because the process exited nonzero and did not produce the
required generation-0 best checkpoint or generation-2 final checkpoint. The
last successful stage is the first completed rollout, actor update, critic
update, and logger cycle at 300/300 steps.

No second run, no source patch, no checkpoint load, and no continuation is
authorized by this result. The required next decision is a review of the empty
ValueNorm checkpoint-state boundary followed, if accepted, by a narrowly scoped
corrective design/implementation phase. General training, longer training,
multiple seeds, playback, evaluation, and comparison work remain prohibited.

## Scope Confirmation

```text
frozen command executed at most once: yes
automatic retry: no
source/test/YAML/runtime-default modification: no
checkpoint loading or continuation: no
playback/evaluation/comparison: no
second seed or longer training: no
installed HARL modification: no
Conda environment modification: no
commit: no
```
