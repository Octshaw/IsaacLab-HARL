# Phase 9G-8G-1R-2T: Timeout-Corrected Controlled Smoke Execution

Date: 2026-07-10

## Classification

`PASS`

The corrected foreground execution completed naturally before the 600-second external limit. It confirms that the prior exit-124 event was an insufficient external-wrapper timeout, not a runtime ValueNorm checkpoint failure.

## Committed Baseline And Preflight

| Check | Result |
| --- | --- |
| Baseline | `3f79af53b731dd880dcda22766000313c317b93a` |
| Commit | `3f79af53 fix(assignment): persist runtime ValueNorm state in native checkpoints` |
| Adapter/v2 production and regression paths in HEAD | PASS |
| Uncommitted production/test/YAML behavior changes | None |
| Pre-existing uncommitted files | AgentRead handoff documentation only |
| Relevant residual smoke process | None |
| New experiment parent before launch | Absent |
| Previous failed-result timestamp before/after | `2026-07-10T01:44:37.3925953Z`, unchanged |

## Execution

Execution mechanism: attached foreground PowerShell process through the command tool, with a 600-second external timeout and temporary live console capture outside the repository:

`C:\Users\33506\AppData\Local\Temp\phase9g8g1r2t_timeout_corrected_console.log`

Frozen command executed exactly once:

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

| Field | Result |
| --- | --- |
| Start | `2026-07-10T15:57:52.1528385+08:00` |
| End | `2026-07-10T15:59:43.0901793+08:00` |
| Elapsed | `00:01:50.9373408` |
| External timeout | 600 seconds; not reached |
| Process exit | `0` |
| Result directory | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh/seed-00001-2026-07-10-15-59-12` |

## Runtime Contract And Progression

Resolved/runtime evidence:

- `lifecycle_contract_c`, HAPPO, EP, feed-forward, `share_param=false`.
- `use_recurrent_policy=false`, `use_naive_recurrent_policy=false`, `save_entire_model=false`, `model_dir=None`.
- One CUDA environment, M=3, N=50, seed=1, episode length=300, total environment steps=300.
- Actor/shared/action/noop widths: `1059 / 3183 / 51 / 50`.
- Reset `available_actions` shape: `[1, 3, 51]` on `cuda:0`.
- Console confirms actor-buffer warmup stored historical available-actions and policy collection passed per-agent masks.
- AppLauncher, headless Isaac Sim, environment construction, reset/warmup, three actors, centralized critic, and CUDA execution completed.
- Console reached `episodes 1/1 total num timesteps 300/300`; all three actor updates and the VCritic update emitted TensorBoard metrics.

The runtime ValueNorm construction was not separately logged by class name, but `use_valuenorm=true`, CUDA execution, the finite critic update, and the resulting nonempty canonical ValueNorm artifact collectively verify the intended runtime adapter boundary.

## Numerical Health And Actual Metrics

One TensorBoard event file emitted 63 scalar tags at step 300. Every recorded scalar was finite; the inspection found no NaN, `+Inf`, or `-Inf`.

| Metric | Value |
| --- | ---: |
| agent0 policy loss / entropy / grad norm / ratio | -0.01155044 / 0.75369793 / 1.03380108 / 0.99821198 |
| agent1 policy loss / entropy / grad norm / ratio | -0.04767282 / 0.76975584 / 1.12176597 / 1.00383878 |
| agent2 policy loss / entropy / grad norm / ratio | -0.08225651 / 0.75723028 / 0.87342662 / 0.98893815 |
| critic value loss / grad norm / average step reward | 1.78450978 / 27.31459427 / 0.01939927 |
| coverage ratio / new viewpoints / duplicate scans | 0.32266665 / 0.08666667 / 0.04333333 |
| reach violation / mean reward / total reward | 0 / 0.47762728 / 21.94484329 |
| noop count / valid action count / selected available mask | 0.00666667 / 2.99333334 / 0.99777776 |
| cooldown budget ratio mean / max | 0.41631514 / 0.62827379 |
| cooldown budget attempt steps mean / max | 37.29777908 / 56.29666519 |
| cooldown budget steps mean / max | 87.17111206 / 103.77333069 |

Additional finite assignment reward values were: base environment reward `0.47762728`, repeated-target adjustment `-0.35531113`, global-no-progress adjustment `-0.04916667`, total assignment adjustment `-0.40447778`, final reward mean `0.07314948`, and global coverage gain mean `0`.

Low one-update coverage and the finite cooldown/noop diagnostics are not performance conclusions and are not smoke failures.

## Native Save Sequence

- `best_model`: training-state manifest reports `checkpoint_kind=best`, generation `0`.
- Interval `models` save: generation `1` is established by the final generation progression; it is expected to be overwritten in the same `models/` directory.
- Explicit final `models` save: manifest reports `checkpoint_kind=final`, generation `2`.
- Console confirms final model save; `runner.run()` returned and the process exited normally.

Both checkpoint children have the exact required eight files: three canonical actor artifacts, critic, `value_normalizer.pt`, child manifest, fingerprint, and `assignment_training_state_manifest.json`. There are no full-model, numeric legacy actor, or temporary checkpoint artifacts.

## Contract, Artifact, And Marker Verification

Run-root, `best_model`, and `models` manifests all use `assignment_checkpoint_contract_v2`, are canonically identical, and match fingerprint:

`19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6`.

The immutable ValueNorm contract is enabled and exact: adapter `harl_valuenorm_runtime_state_v1`, artifact format `harl_runtime_attribute_tensor_mapping_v1`, implementation `harl.common.valuenorm.ValueNorm`, input shape `[1]`, norm axes `1`, beta `0.99999`, epsilon `0.00001`, per-element update false, dtype `float32`, and canonical keys `running_mean`, `running_mean_sq`, `debiasing_term`. Device is absent from immutable semantics.

Safe CPU `weights_only=True` inspection, without any live restore, verified both ValueNorm artifacts are nonempty ordered mappings with those exact keys. Every value is CPU float32 and finite; shapes are `[1]`, `[1]`, and `[]`. Each `value_normalizer.pt` is 1,684 bytes with SHA-256:

`d46726827332e41a41080077b08eebecdd78514a375f57b3657993bb2765a4cc`.

All declared artifact sizes, SHA-256 values, tensor inventories, and inventory SHA-256 values matched the training-state metadata for both children. Actor artifacts are 1,417,842 bytes each; critic artifacts are 3,558,194 bytes. Completion markers exist, are not older than their declared artifacts, and all training-state manifests bind the expected actor order, critic/ValueNorm artifacts, continuation-candidate classification, and unavailable optimizer/counter/RNG/environment-resolver/rollout state.

## Previous Failure Isolation And Limitations

The prior checkpoint-save failure directory was not opened for checkpoint loading, copied, moved, renamed, deleted, or written. Its timestamp remained unchanged. The prior exit-124 attempt created no new parent. The successful R-2T output is solely under the frozen R-2 experiment parent.

Startup emitted nonblocking Isaac/Gym infrastructure warnings, including OmniHub unavailability, missing optional crash reporter, a Gym maintenance warning, and an ignored Intel GPU. They did not prevent environment construction, rollout, update, native save, shutdown, or exit 0.

This one-update smoke establishes integration only. It does not establish convergence, policy quality, long-run stability, retry/stranded-task policy quality, or performance against baselines.

## Files And Boundaries

Created:

- `AgentRead/20260710/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md`
- `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2T_TIMEOUT_CORRECTED_SMOKE_20260710.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

Explicitly not modified:

- Production Python, tests, YAML/runtime defaults
- Installed HARL and Conda environment
- Previous failed result

No checkpoint restore, playback, evaluation, visual inspection, continuation, second seed, longer training, automatic retry, or commit occurred. The next decision requires review before any broader authorization.
