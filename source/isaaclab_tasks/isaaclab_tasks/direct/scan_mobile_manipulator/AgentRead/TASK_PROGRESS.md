# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9D-1A assignment-history episode-reset diagnostic is complete.

Result: passed after a minimal wrapper reset fix. The fixed `N=50 / M=3` assignment-RL path now resets wrapper-local assignment-history state for done env ids during HARL rollout episodes.

## Root Cause

`AssignmentHarlWrapper.reset()` reset assignment-history state at startup, but HARL rollout episodes do not call wrapper `reset()` after every done. Isaac Lab auto-resets done envs inside `DirectMARLEnv.step()` before returning observations, so the wrapper was augmenting next-episode observations with stale history.

Affected state included per-viewpoint attempted counts, last-attempt ages, previous assignment ids, same-target streaks, steps since global coverage gain, per-robot completed/repeated/selected counts, last covered mask, and assignment step.

## Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_harl_episode_reset_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No reward formulas/default scales, masks, feasibility logic, solver/controller behavior, HARL internals, installed site-packages, or environment dynamics were changed.

## Validation

Python compile passed:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_wrapper.py scripts\environments\test_assignment_harl_episode_reset_smoke.py
```

Episode-reset smoke passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_episode_reset_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 330 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3.json
```

Key smoke results:

```text
first_done_step = 299
episode_horizon = 300
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
available_actions shape = [1, 3, 51]
available_mask shape = [1, 3, 50]
reward shape = [1, 3, 1]
max_reward_steps_since_global_coverage_gain = 298.0
max_next_episode_state_steps_since_global_coverage_gain = 2.0
history_reset_after_boundary = true
done_boundary_attempted_sum = 0.0
done_boundary_previous_assignment = [-1, -1, -1]
done_boundary_same_target = [0.0, 0.0, 0.0]
```

Optional 1200-step training re-check passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d1a_reset_recheck_1k2 --save_interval 5 --log_interval 1
```

Training re-check output:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22
```

TensorBoard scalar check:

```text
assignment_rl_reward/steps_since_global_coverage_gain_mean max = 148.51666259765625
scalar_tags = 33
scalar_values = 132
nonfinite_scalar_values = []
```

No checkpoint was loaded: `--dir` was not used and no restore/load message appeared.

Repository checks:

```text
git diff --check = passed, with line-ending warnings only
git status --short = expected modified wrapper/progress files plus untracked smoke/report artifacts
```

## Output Artifacts

```text
results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3.json
results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3_console.log
results/assignment_diagnostics/phase9d1a_reset_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/logs/events.out.tfevents.1782745942.xxsys203-1
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/best_model
```

## Next Step

Recommended next phase: rerun Phase 9D-1 short debug training, or proceed only to a scoped 30k debug run if the next goal is longer stability. Do not jump directly to full training yet.

## Do Not Do

Do not commit unless explicitly asked.

Do not proceed to formal evaluation, checkpoint play, checkpoint evaluation, old-checkpoint loading, full training, reward tuning, arbitrary-N architecture work, or new handcrafted baselines from this task.

Do not change solver/controller/mask/feasibility/environment dynamics/HARL internals unless a future blocking bug explicitly requires a scoped fix.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C1_FRESH_POLICY_TENSOR_FLOW_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
```
