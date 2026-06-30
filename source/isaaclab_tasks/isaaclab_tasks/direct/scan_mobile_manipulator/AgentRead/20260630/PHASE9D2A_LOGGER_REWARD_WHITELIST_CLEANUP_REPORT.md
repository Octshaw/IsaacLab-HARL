# Phase 9D-2A Logger Reward Whitelist Cleanup Report

Date: 2026-06-30

## 1. Scope and Boundaries

Phase 9D-2A cleaned up HARL IsaacLab logger reward accounting for assignment RL. The goal was to stop assignment diagnostic scalars from polluting `Total_Reward` and `best_model` selection.

This was a logging/accounting cleanup only. It was not reward tuning, policy training, formal evaluation, checkpoint play, baseline modification, or behavior-claim work.

Hard boundaries observed:

- No long training.
- No formal evaluation.
- No checkpoint play.
- No checkpoint loading.
- No reward formula or reward scale default changes.
- No TensorBoard tag renames.
- No observation, mask, feasibility, solver, controller, HARL algorithm, environment dynamics, robot motion, collision, local avoidance, path planning, retry/fallback, or cooldown changes.
- No handcrafted baselines.
- No commit.

## 2. Root Cause Summary From the 300k Run

The 300k debug run completed and showed no NaN/Inf, but `Total_Reward` reached about `2.26e+5`.

Root cause: the installed HARL IsaacLab logger accumulated `self.total_reward` with substring matching:

```python
if "reward" in key.lower():
    self.total_reward += np.sum(values)
```

This included every logged scalar whose key contained `"reward"`, including assignment diagnostics under:

```text
assignment_rl_reward/...
```

The largest pollution source was not a reward:

```text
assignment_rl_reward/steps_since_global_coverage_gain_mean
```

In the 300k run, the last logged value was about:

```text
steps_since_global_coverage_gain_mean = 148.839996
episode_length = 300
log_interval = 5
num_envs = 1
```

So this one diagnostic counter contributed roughly:

```text
148.839996 * 300 * 5 = 223259.99
```

That almost entirely explains:

```text
Total_Reward ~= 223906.89
```

The previous 300k `Total_Reward` and `best_model` selection are therefore polluted accounting artifacts, not true reward explosions or trustworthy best-policy indicators.

## 3. Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/reinforcement_learning/harl/train.py
C:/isaacenvs/isaac45_harl/lib/site-packages/harl/envs/isaaclab/Isaac_lab_logger.py
C:/isaacenvs/isaac45_harl/lib/site-packages/harl/runners/on_policy_ha_runner.py
```

Search terms used included:

```text
Total_Reward
total_reward
best_model
reward in key
average_step_rewards
assignment_rl_reward
```

## 4. Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/environments/test_assignment_logger_reward_whitelist.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Installed HARL package files were inspected but not modified.

## 5. Whitelist Design

Assignment RL now uses a repo-local `AssignmentIsaacLabLogger` subclass in `assignment_harl_training.py`.

Active assignment RL accumulator key:

```text
assignment_rl_reward/final_reward_mean
```

Implementation details:

- `ASSIGNMENT_REWARD_ACCUMULATOR_KEYS = {"assignment_rl_reward/final_reward_mean"}`
- `_should_accumulate_reward_key(key, reward_accumulator_keys)` uses exact-key matching when a whitelist is configured.
- `_compute_reward_accumulator_total(...)` sums only whitelisted keys when the whitelist is present.
- `AssignmentOnPolicyHARunner` uses `AssignmentIsaacLabLogger` only for `--assignment_rl` IsaacLab runs.
- Non-assignment tasks still use the installed HARL logger from `LOGGER_REGISTRY`.
- Legacy behavior is preserved when no whitelist is configured: `_should_accumulate_reward_key(key, None)` still uses the old `"reward" in key.lower()` rule.

The assignment runner records the active mode/key in `env_args`, and the re-check `configs.json` includes:

```text
reward_accumulator_mode = exact_whitelist
reward_accumulator_keys = ["assignment_rl_reward/final_reward_mean"]
```

The console also prints:

```text
[INFO]: Assignment RL Total_Reward accumulator whitelist: ['assignment_rl_reward/final_reward_mean']
```

Because HARL's runner saves `best_model` when `logger.total_reward` improves, assignment RL `best_model` selection now uses the cleaned `Total_Reward` accumulator.

## 6. Test and Smoke Results

Python compile:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_training.py scripts\environments\test_assignment_logger_reward_whitelist.py
```

Result: passed.

Logger whitelist smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_logger_reward_whitelist.py --result_file results\assignment_diagnostics\phase9d2a_logger_reward_whitelist_smoke.json
```

Result: passed.

Smoke JSON:

```text
results/assignment_diagnostics/phase9d2a_logger_reward_whitelist_smoke.json
```

Key smoke values:

```text
legacy_substring_total = 224564.7
whitelist_total = 215.7
expected_whitelist_total = 215.7
steps_since_sum_if_legacy_accumulated = 223260.0
steps_since_contributes_with_whitelist = false
final_reward_contributes_with_whitelist = true
```

The smoke kept all diagnostic keys present in the synthetic log data; only reward accumulation was filtered.

## 7. 1200-Step Training Logging Re-Check

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2 --save_interval 5 --log_interval 1
```

Console log:

```text
results/assignment_diagnostics/phase9d2a_logger_whitelist_recheck_1k2_console.log
```

Result: passed.

Output directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00
```

TensorBoard event:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/logs/events.out.tfevents.1782807600.xxsys203-1
```

Model artifacts were written:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/best_model
```

Both directories contain actor, critic, and value normalizer artifacts.

No checkpoint was loaded:

```text
--dir was not used
configs.json has model_dir = null
no restore/load message appeared
```

## 8. Evidence That `steps_since_global_coverage_gain_mean` No Longer Contributes

TensorBoard scalar values from the 1200-step re-check:

```text
Total_Reward:
  step 300  = -19.66063690185547
  step 600  = -19.75667953491211
  step 900  = -19.514137268066406
  step 1200 = -19.748868942260742

assignment_rl_reward/final_reward_mean:
  step 300  = -0.06553545594215393
  step 600  = -0.06585559993982315
  step 900  = -0.06504712253808975
  step 1200 = -0.0658295601606369

assignment_rl_reward/steps_since_global_coverage_gain_mean:
  step 300  = 148.5066680908203
  step 600  = 148.50999450683594
  step 900  = 148.51333618164062
  step 1200 = 148.51666259765625
```

With `log_interval=1`, `assignment_episode_length=300`, and `num_envs=1`, `Total_Reward` now equals the per-step sum of `assignment_rl_reward/final_reward_mean`, e.g.:

```text
-0.0655354559 * 300 ~= -19.6606
```

If `steps_since_global_coverage_gain_mean` still contributed, the first log would include roughly:

```text
148.506668 * 300 ~= 44552.0
```

It did not. The logged `Total_Reward` stayed near `-20`, not tens of thousands.

## 9. Diagnostic Keys Still Present

The 1200-step TensorBoard event still had `33` scalar tags, including:

```text
assignment_rl_reward/final_reward_mean
assignment_rl_reward/steps_since_global_coverage_gain_mean
assignment_rl_reward/base_env_reward_mean
assignment_rl_reward/total_assignment_reward_adjustment_mean
mean_reward
critic/average_step_rewards
```

So diagnostic logging remains visible; only `Total_Reward` accumulation changed.

## 10. Non-Finite Check

TensorBoard scalar check from the 1200-step event:

```text
scalar_tags = 33
nonfinite_scalar_values = []
```

No NaN/Inf appeared in the obvious scalar logs.

## 11. Repository Checks

Commands:

```powershell
git diff --check
git status --short
```

Result:

```text
git diff --check = passed, with line-ending warnings only
git status --short = expected Phase 9D-2A modified/untracked files, plus pre-existing/unrelated untracked AgentRead/task_log.zip
```

No commit was made.

## 12. Explicit Non-Changes

- No reward formula/default scale change.
- No observation semantic change.
- No mask/feasibility change.
- No solver/controller change.
- No environment dynamics, robot motion, collision, local avoidance, path planning, retry/fallback, or cooldown change.
- No HARL algorithm change and no installed HARL site-package modification.
- No checkpoint loading.
- No formal evaluation.
- No long training.

## 13. Remaining Limitation

The previously produced 300k `Total_Reward` and `best_model` remain polluted by legacy substring accumulation and should not be interpreted as true best-model accounting.

The final `models/` checkpoint from that 300k run remains usable as a debug artifact, but behavior should be diagnosed separately before any stronger policy-quality claim.

## 14. Next Recommendation

After this cleanup is committed, run RL playback diagnostics using the existing Phase 7/8 conflict, crossing, stagnation, coverage, and clearance metrics.

Do not proceed directly to longer training before behavior diagnostics.
