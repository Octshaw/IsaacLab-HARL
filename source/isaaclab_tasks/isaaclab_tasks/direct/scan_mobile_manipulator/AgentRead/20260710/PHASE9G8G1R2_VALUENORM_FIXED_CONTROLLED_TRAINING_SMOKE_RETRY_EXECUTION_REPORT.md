# Phase 9G-8G-1R-2: ValueNorm-Fixed Controlled Training Smoke Retry Execution

Date: 2026-07-10

## Classification

`FAIL`

The one authorized frozen training command was executed exactly once after the committed-baseline preflight passed. Its process wrapper timed out after 124.3 seconds with exit code `124` before returning its recorded start/end/elapsed echo. No automatic retry was performed.

## Committed Baseline And Preflight

| Check | Result |
| --- | --- |
| HEAD | `3f79af53b731dd880dcda22766000313c317b93a` |
| Commit | `3f79af53 fix(assignment): persist runtime ValueNorm state in native checkpoints` |
| Adapter/v2 production and test changes in HEAD | PASS |
| Uncommitted production/test/YAML behavior changes | None before execution |
| Prior AgentRead documents | Committed baseline documentation; allowed |
| New semantic experiment parent before run | Absent |
| Previous failed result | Exists and was isolated |
| Python interpreter | `C:\isaacenvs\isaac45_harl\python.exe` |

The HEAD stat includes the project ValueNorm adapter, v2 contract/save/load integration, global rollback regression, and matching tests. The original failed result was only checked for path/timestamp isolation.

## Frozen Command Execution

The command below was executed once from the repository root:

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
  --exp_name assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh `
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

Observed command result:

```text
process wrapper exit code: 124
wrapper elapsed time: 124.3 seconds
start/end timestamps: not emitted before timeout
console output: no training output was returned before timeout
```

## Runtime And Artifact Result

No `python`, `pythonw`, Isaac Sim, or Kit process remained after the timeout check. The new experiment parent did not exist after the command. Therefore there is no retry result directory and none of the following were created or inspectable:

- Runtime-profile, interface, reset/warmup, resolver/mask, or historical-mask evidence.
- 300-step, HAPPO, VCritic, logger, TensorBoard, or numerical-health evidence.
- Best, regular, or final checkpoint evidence.
- Contract v2 manifests, fingerprints, completion markers, artifact sizes/SHA-256 values, or tensor inventories.
- `value_normalizer.pt`, actor, or critic artifacts.

Actual actor metrics: not emitted. Actual critic metrics: not emitted. Actual environment/assignment metrics: not emitted. Nonblocking anomalies: none observed; the timeout is a blocking execution failure.

## Failed-Result Isolation

The prior failed result remains:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh/
seed-00001-2026-07-10-09-44-31
```

Its directory timestamp remained `2026-07-10T01:44:37.3925953Z`. It was not loaded, copied, renamed, moved, deleted, or modified. No checkpoint restore occurred.

## Evidence Preservation And Next Recommendation

The timeout is the final result of this phase. Do not rerun automatically, change the experiment name, patch source, or alter parameters. Review why the execution wrapper reached its 120-second limit before the process returned, then explicitly authorize any future fresh-preflight attempt with an execution mechanism that can observe the complete bounded run without creating a second unauthorized retry.

## Files

Created:

- `AgentRead/20260710/PHASE9G8G1R2_VALUENORM_FIXED_CONTROLLED_TRAINING_SMOKE_RETRY_EXECUTION_REPORT.md`
- `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2_SMOKE_RETRY_EXECUTION_20260710.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

Explicitly not modified:

- Production Python, tests, YAML/runtime defaults
- Installed HARL and Conda environment
- Previous failed result and any new runtime result directory
- Resolver, Contract C, lifecycle observation/mask behavior, rewards, or checkpoint implementation

No checkpoint restore, playback, evaluation, visual inspection, continuation, second seed, longer training, automatic retry, or commit occurred.
