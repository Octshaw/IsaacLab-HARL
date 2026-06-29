# Phase 9D-1A Assignment-History Reset Diagnostic Report

Date: 2026-06-29

## 1. Scope and Boundaries

Phase 9D-1A diagnosed and fixed assignment-history reset behavior for the fixed `N=50 / M=3` assignment-RL path.

This was a diagnostic/fix phase only. It was not formal training, formal RL evaluation, checkpoint play/evaluation, policy-quality evaluation, reward tuning, solver/controller work, or arbitrary-N architecture work.

Hard boundaries observed:

- No long training.
- No checkpoint loading and no `--dir`.
- No checkpoint play or formal evaluation.
- No reward formula or reward scale default changes.
- No mask, feasibility, solver, controller, HARL internals, site-packages, environment dynamics, robot motion, collision, IK, raycast, local avoidance, path planning, retry, fallback, or cooldown changes.
- No handcrafted baselines.
- No commit.

## 2. Trigger Evidence From Manual Phase 9D-1 Debug Run

Manual 9D-1 short debug training was run with:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 10000 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d1_short_debug_train_10k --save_interval 5 --log_interval 1
```

That run completed 33 episodes and saved models, with TensorBoard showing no NaN. Late console logs included:

```text
assignment_rl_reward/steps_since_global_coverage_gain_mean: 6150.5
...
assignment_rl_reward/steps_since_global_coverage_gain_mean: 9750.5
assignment_rl_reward/global_no_progress_mean: -0.05000000447034836
assignment_rl_reward/global_coverage_gain_mean: 0.0
```

Because `--assignment_episode_length 300`, `steps_since_global_coverage_gain_mean` growing into the thousands indicated that wrapper-local assignment history was carrying across episodes.

## 3. Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C1_FRESH_POLICY_TENSOR_FLOW_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/test_assignment_harl_fresh_policy_smoke.py
scripts/environments/test_assignment_training_entry_readiness.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab/isaaclab/envs/direct_marl_env.py
```

## 4. Root-Cause Finding

Yes, wrapper-local assignment-history state was carrying across episodes during HARL training.

Affected wrapper-local state included:

- `_per_viewpoint_attempted_count`
- `_last_viewpoint_attempt_step`
- `_previous_assignment`
- `_same_target_streak`
- `_steps_since_global_coverage_gain`
- `_per_robot_completed_count`
- `_per_robot_repeated_assignment_count`
- `_per_robot_selected_count`
- `_last_covered_mask`
- `_assignment_step`

These states were reset by explicit `AssignmentHarlWrapper.reset()`, but the HARL rollout path calls wrapper `reset()` only at startup/warmup. During rollout, Isaac Lab's `DirectMARLEnv.step()` computes dones and rewards, identifies reset env ids, calls `_reset_idx(reset_env_ids)`, and then returns next observations. The underlying env therefore auto-resets done envs inside `step()` without reconstructing the assignment wrapper or calling `AssignmentHarlWrapper.reset()`.

Before the fix, `AssignmentHarlWrapper.step()` augmented the returned next observation using stale wrapper-local history. This made episode-local features and reward-shaping diagnostics, especially `steps_since_global_coverage_gain`, accumulate across episodes.

`steps_since_global_coverage_gain` is treated as episode-local for this path because it is used in wrapper observation/reward shaping and has no clear documentation indicating global lifetime semantics.

## 5. Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_harl_episode_reset_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No solver/controller/mask/feasibility/env dynamics/HARL internals/config reward formulas were changed.

## 6. Fix Details

`AssignmentHarlWrapper.step()` now detects done env ids from the stacked `terminated`/`truncated` tensors:

```text
done_env_ids = torch.nonzero(torch.all(dones, dim=1), as_tuple=False).flatten()
```

The existing `_reset_assignment_diagnostics(env_ids=..., problem=...)` helper is now reused for partial env-id resets. The same helper remains the full reset path from `AssignmentHarlWrapper.reset()`.

Timing was kept narrow:

1. Step assignment diagnostics are updated using the terminal step's pre-reset wrapper history.
2. Reward decomposition and `info` augmentation are built before resetting wrapper-local history.
3. Done env wrapper history is reset.
4. Returned observations are augmented after the reset, so the next episode sees reset assignment-history features.

This preserves terminal-step reward/log construction while making next-episode observations episode-local again.

Known timing limitation: Isaac Lab's `DirectMARLEnv.step()` already resets done base envs before returning observations. Phase 9D-1A did not attempt broader terminal-state reconstruction for the base assignment problem; it only fixed wrapper-local history carryover.

## 7. Episode-Reset Smoke Command and JSON

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_episode_reset_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 330 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3.json
```

Console log:

```text
results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3_console.log
```

JSON result:

```text
results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3.json
```

## 8. Episode-Reset Smoke Results

Result: passed.

Runtime summary:

```text
completed_steps = 330
first_done_step = 299
episode_horizon = 300
```

The first done occurred at wrapper step 299 because the env timeout condition follows the Isaac Lab convention of ending when the incremented `episode_length_buf >= max_episode_length - 1`.

Confirmed shapes:

```text
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
available_actions shape = [1, 3, 51]
available_mask shape = [1, 3, 50]
reward shape = [1, 3, 1]
```

State evidence:

```text
max_reward_steps_since_global_coverage_gain = 298.0
max_next_episode_state_steps_since_global_coverage_gain = 2.0
attempted_counts_positive_before_boundary = true
history_reset_after_boundary = true
before_done_attempted_sum = 894.0
done_boundary_attempted_sum = 0.0
done_boundary_previous_assignment = [-1, -1, -1]
done_boundary_same_target = [0.0, 0.0, 0.0]
```

The done-boundary snapshot also showed:

```text
assignment_step = 0
steps_since_global_coverage_gain = 0.0
never_attempted_count = 50
last_attempt_step_min = -1
per_robot_completed_count = [0.0, 0.0, 0.0]
per_robot_repeated_assignment_count = [0.0, 0.0, 0.0]
per_robot_selected_count = [0.0, 0.0, 0.0]
```

This confirms the partial wrapper reset path is active at the real done/reset boundary.

## 9. Optional 1200-Step Training Re-Check

Because a fix was made, a much smaller training re-check was run.

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d1a_reset_recheck_1k2 --save_interval 5 --log_interval 1
```

Result: passed.

Runtime summary:

```text
episodes = 4
process exit code = 0
```

Output directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22
```

TensorBoard event file:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/logs/events.out.tfevents.1782745942.xxsys203-1
```

Model artifacts:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1a_reset_recheck_1k2/seed-00001-2026-06-29-23-12-22/best_model
```

No checkpoint was loaded:

```text
--dir was not used
no restore/load message appeared
```

`assignment_rl_reward/steps_since_global_coverage_gain_mean` TensorBoard scalar values:

```text
step 300  = 148.5066680908203
step 600  = 148.50999450683594
step 900  = 148.51333618164062
step 1200 = 148.51666259765625
max       = 148.51666259765625
```

TensorBoard scalar check:

```text
scalar_tags = 33
scalar_values = 132
nonfinite_scalar_values = []
```

The re-check no longer shows `steps_since_global_coverage_gain_mean` growing beyond the 300-step episode horizon, and no NaN/Inf appeared in the obvious scalar logs.

## 10. Validation Commands

Python compile:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_wrapper.py scripts\environments\test_assignment_harl_episode_reset_smoke.py
```

Result: passed.

Episode-reset smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_episode_reset_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 330 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9d1a_assignment_history_episode_reset_smoke_n50_m3.json
```

Result: passed.

Training re-check:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d1a_reset_recheck_1k2 --save_interval 5 --log_interval 1
```

Result: passed.

Repository checks:

```powershell
git diff --check
git status --short
```

Result: `git diff --check` passed with line-ending warnings only. `git status --short` showed the expected modified wrapper/progress files and untracked smoke/report artifacts. No commit was made.

## 11. Explicit Non-Changes

- No reward formula/default scale changes.
- No observation semantic changes beyond reset consistency for existing wrapper-local state.
- No available-mask, feasible-mask, or static-geometric-feasible-mask changes.
- No solver/controller/HARL/env dynamics changes.
- No checkpoint loading.
- No formal evaluation.
- No long training.
- No policy-quality or coverage-improvement claim.

## 12. Next Recommendation

The reset bug is fixed and validated at smoke scale.

Recommended next step: rerun Phase 9D-1 short debug training, or proceed only to a scoped 30k debug run if the goal is to check longer-run stability. Do not jump directly to full training or formal evaluation yet.
