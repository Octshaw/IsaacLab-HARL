# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9D-2A HARL IsaacLab logger reward whitelist cleanup is complete.

Result: passed. Assignment RL `Total_Reward` and `best_model` selection now use an exact reward accumulator whitelist instead of HARL's legacy substring rule.

## Root Cause

The installed HARL IsaacLab logger accumulated `self.total_reward` with:

```python
if "reward" in key.lower():
    self.total_reward += np.sum(values)
```

This polluted assignment RL `Total_Reward` with diagnostic keys such as:

```text
assignment_rl_reward/steps_since_global_coverage_gain_mean
```

In the Phase 9D-2 300k run, that diagnostic counter alone contributed roughly:

```text
148.839996 * 300 * 5 = 223259.99
```

So the old 300k `Total_Reward ~= 223906.89` and its `best_model` selection were polluted and should not be interpreted as true best-model accounting.

## Whitelist

Assignment RL now accumulates only:

```text
assignment_rl_reward/final_reward_mean
```

All other scalar diagnostics remain logged to TensorBoard. Non-assignment tasks still use the installed HARL logger behavior.

The 1200-step re-check `configs.json` records:

```text
reward_accumulator_mode = exact_whitelist
reward_accumulator_keys = ["assignment_rl_reward/final_reward_mean"]
```

## Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/environments/test_assignment_logger_reward_whitelist.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Installed HARL site-packages were inspected but not modified.

No reward formulas/default scales, observation semantics, masks, feasibility logic, solver/controller behavior, HARL algorithms, or environment dynamics were changed.

## Validation

Python compile passed:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_training.py scripts\environments\test_assignment_logger_reward_whitelist.py
```

Logger whitelist smoke passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_logger_reward_whitelist.py --result_file results\assignment_diagnostics\phase9d2a_logger_reward_whitelist_smoke.json
```

Smoke result:

```text
legacy_substring_total = 224564.7
whitelist_total = 215.7
steps_since_sum_if_legacy_accumulated = 223260.0
steps_since_contributes_with_whitelist = false
final_reward_contributes_with_whitelist = true
```

1200-step assignment RL logging re-check passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2 --save_interval 5 --log_interval 1
```

Output path:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00
```

TensorBoard evidence:

```text
Total_Reward = [-19.6606, -19.7567, -19.5141, -19.7489]
assignment_rl_reward/final_reward_mean = [-0.065535, -0.065856, -0.065047, -0.065830]
assignment_rl_reward/steps_since_global_coverage_gain_mean = [148.5067, 148.5100, 148.5133, 148.5167]
scalar_tags = 33
nonfinite_scalar_values = []
```

`Total_Reward` now matches `final_reward_mean * 300` and is no longer dominated by `steps_since_global_coverage_gain_mean`.

Model artifacts were saved:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/best_model
```

No checkpoint was loaded: `--dir` was not used and `configs.json` has `model_dir = null`.

Repository checks:

```text
git diff --check = passed, with line-ending warnings only
git status --short = expected Phase 9D-2A files, plus unrelated untracked AgentRead/task_log.zip
```

## Output Artifacts

```text
results/assignment_diagnostics/phase9d2a_logger_reward_whitelist_smoke.json
results/assignment_diagnostics/phase9d2a_logger_whitelist_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d2a_logger_whitelist_recheck_1k2/seed-00001-2026-06-30-16-20-00/logs/events.out.tfevents.1782807600.xxsys203-1
```

## Next Step

Recommended next phase after commit: run RL playback diagnostics using existing Phase 7/8 conflict, crossing, stagnation, coverage, and clearance metrics.

Do not proceed directly to longer training before behavior diagnostics.

## Do Not Do

Do not commit unless explicitly asked.

Do not proceed to RL playback diagnostics, longer training, formal evaluation, checkpoint play/evaluation, old-checkpoint loading, reward tuning, arbitrary-N architecture work, or new handcrafted baselines from this task.

Do not change solver/controller/mask/feasibility/environment dynamics/HARL algorithms unless a future blocking bug explicitly requires a scoped fix.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C1_FRESH_POLICY_TENSOR_FLOW_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
```
