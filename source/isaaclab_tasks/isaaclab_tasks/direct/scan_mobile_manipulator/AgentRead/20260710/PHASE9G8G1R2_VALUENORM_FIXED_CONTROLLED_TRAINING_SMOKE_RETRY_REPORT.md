# Phase 9G-8G-1R-2: ValueNorm-Fixed Controlled Training Smoke Retry

Date: 2026-07-10

## Classification

`FAIL-PREFLIGHT`

The one permitted training command was not executed. The required ValueNorm adapter/checkpoint-v2 corrective production baseline is present in the worktree but is not committed. The phase contract prohibits launching the retry in that state.

## Committed Baseline Preflight

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `8a5f46cbce252df554cb5ea961ed2bd25875bfd2` |
| `git log -1 --oneline` | `8a5f46cb feat(assignment): complete lifecycle training checkpoint readiness` |
| New semantic experiment parent | Absent; no collision. |
| Failed 9G-8G-1 result | Exists and was not opened, loaded, moved, renamed, or modified. |
| Corrective adapter/v2 production source | Uncommitted. Hard preflight failure. |
| Corrective tests | Uncommitted. Hard preflight failure. |

The exact uncommitted production paths include:

- `assignment_value_normalizer_checkpoint.py`
- `assignment_checkpoint_contract.py`
- `assignment_checkpoint_save.py`
- `assignment_checkpoint_load.py`
- `assignment_harl_training.py`

Uncommitted checkpoint regression changes are also present. The remaining uncommitted `AgentRead` reports, archives, and `TASK_PROGRESS.md` are expected documentation handoff material, but documentation does not satisfy the requirement that the production corrective source be committed.

## Command

The frozen command below was intentionally not executed:

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

Start time, end time, elapsed time, process exit code, runtime profile/dimensions, reset/step/update evidence, numerical metrics, checkpoint artifacts, manifests, fingerprints, inventories, and ValueNorm artifact inspection are all `not applicable`: no process was started and no new result directory was created.

## Result Safety

The requested parent was verified absent:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh
```

The failed result remains at:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh/
seed-00001-2026-07-10-09-44-31
```

It was checked for path existence only. Its recorded directory timestamp before this phase was `2026-07-10T01:44:37.3925953Z`; no training, loading, artifact inspection, copy, deletion, or mutation occurred.

## Required Next Action

Commit the reviewed ValueNorm adapter/checkpoint-v2 production and matching regression changes. Then begin a fresh preflight that rechecks the committed hash, clean production/test behavior paths, the new-name collision, and failed-result isolation before considering the single frozen command again. Do not reuse this preflight as authorization after any worktree change.

## Files

Created:

- `AgentRead/20260710/PHASE9G8G1R2_VALUENORM_FIXED_CONTROLLED_TRAINING_SMOKE_RETRY_REPORT.md`
- `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2_SMOKE_RETRY_20260710.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

Explicitly not modified:

- Production Python, tests, YAML/runtime defaults
- Installed HARL and Conda environment
- Failed result and any results directory
- Resolver, Contract C, observations, masks, rewards, or checkpoint behavior

No training, AppLauncher, Isaac Sim, assignment environment, checkpoint creation, checkpoint restore, playback, evaluation, visual inspection, second seed, longer training, automatic retry, or commit occurred.
