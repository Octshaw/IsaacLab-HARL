# Phase 9C-2 Training-Entry Readiness Fixes Report

Date: 2026-06-29

## 1. Scope and Boundaries

Phase 9C-2 resolved small training-entry readiness blockers for fixed `N=50 / M=3` assignment RL before any training smoke.

This phase did not run RL training, formal RL evaluation, checkpoint play, checkpoint evaluation, checkpoint loading, checkpoint saving, or `runner.run()`.

Hard boundaries preserved:

- no reward formula or reward scale default changes
- no observation semantic changes
- no `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask` semantic changes
- no solver, controller, HARL internals, installed site-packages, or environment dynamics changes
- no robot motion, collision, IK, raycast, local avoidance, path planning, retry, fallback, or cooldown changes
- no handcrafted baseline rules
- no commit

## 2. Files Changed

Phase 9C-2 files changed or created:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py`
- `scripts/reinforcement_learning/harl/train.py`
- `scripts/reinforcement_learning/harl/play_assignment.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py`
- `scripts/environments/test_assignment_harl_fresh_policy_smoke.py`
- `scripts/environments/test_assignment_training_entry_readiness.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

Pre-existing Phase 9B/9C uncommitted files were kept.

## 3. Scenario Config Bridge Details

### Shared Helper

`scenario_config.py` now exposes `apply_scenario_config_to_env_cfg(...)`, which applies the same scenario defaults/CLI overrides used by the existing evaluator and smoke scripts to a `ScanMobileManipulator` env cfg.

The helper centralizes the fixed-N scenario bridge instead of duplicating a long list of env cfg assignments in every entry point.

### `train.py` Behavior

`scripts/reinforcement_learning/harl/train.py` now accepts:

```text
--scenario_config <path>
```

For safety, `train.py` allows `--scenario_config` only together with `--assignment_rl`. Non-assignment HARL training paths are not changed by this bridge.

When `--assignment_rl --scenario_config ...` is provided, the script:

- loads the scenario config before AppLauncher parsing,
- applies scenario defaults to CLI args,
- validates the scenario config,
- applies the config to `env_cfg` before creating the assignment HARL runner.

Future fixed-N assignment training command shape, not run in this phase:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name phase9c_fixedn_assignment_tiny_smoke
```

Do not run that command until a later task explicitly scopes a tiny training smoke.

### `play_assignment.py` Behavior

`scripts/reinforcement_learning/harl/play_assignment.py` now accepts:

```text
--scenario_config <path>
```

When provided, it loads, validates, and applies the same fixed-N scenario config before constructing the assignment play wrapper.

Future fixed-N assignment play command shape, not run in this phase:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/play_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --dir <fresh_n50_assignment_checkpoint_dir> --max_steps 300 --stop_on_done
```

Do not use old fixed-12 assignment or old 9D scan checkpoints with this path.

## 4. Episode Length Alignment

The task-local HARL HAPPO config still has:

```text
train.episode_length = 1000
```

That was risky for fixed-N assignment RL because the current scenario/env horizon is approximately 300 decision steps. A rollout length of 1000 can blur episode-end behavior, no-progress signals, and logging expectations during the first tiny training smoke.

Phase 9C-2 added an assignment-only CLI override:

```text
--assignment_episode_length 300
```

Behavior:

- default config remains unchanged
- override is accepted only with `--assignment_rl`
- `apply_assignment_episode_length_override(...)` sets `algo_args["train"]["episode_length"]`
- recommended future smoke value is `300`

The Phase 9C-2 readiness smoke verified:

```text
episode_length_default_value = 1000
episode_length_override_supported = true
episode_length_override_value = 300
```

## 5. `assignment_rl_reward` Logger Flattening

`AssignmentIsaacLabEnv._update_log_info(...)` now flattens `info["assignment_rl_reward"]` into scalar log keys for HARL training logger inputs.

Added log keys:

```text
assignment_rl_reward/base_env_reward_mean
assignment_rl_reward/repeated_same_target_no_progress_mean
assignment_rl_reward/global_no_progress_mean
assignment_rl_reward/selected_path_cost_mean
assignment_rl_reward/total_assignment_reward_adjustment_mean
assignment_rl_reward/final_reward_mean
assignment_rl_reward/steps_since_global_coverage_gain_mean
assignment_rl_reward/global_coverage_gain_mean
```

The flattening handles tensor, NumPy, list/tuple, scalar, and bool-like values where possible. It does not change reward computation.

Validation result:

```text
assignment_rl_reward_log_keys_present = true
reward log keys present = 8
```

## 6. No-Training Validation Results

### Py Compile

Command:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/test_assignment_harl_fresh_policy_smoke.py scripts/environments/test_assignment_training_entry_readiness.py scripts/reinforcement_learning/harl/train.py scripts/reinforcement_learning/harl/play_assignment.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

Result: passed.

### Phase 9C-1 Smoke After Changes

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_fresh_policy_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3_after_9c2.json
```

Result JSON:

```text
results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3_after_9c2.json
```

Result summary:

```text
num_agents = 3
num_viewpoints = 50
noop_id = 50
actor_observation_shape = [1, 909]
shared_observation_shape = [1, 3, 2727]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
actor_head_width_per_agent = 51 for all robots
sampled actions available = true for all robots
reward_shape = [1, 3, 1]
reward_finite = true
assignment_rl_reward decomposition present = true
no_checkpoint_loaded = true
no_training_run = true
```

### Phase 9C-2 Readiness Smoke

Command:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_training_entry_readiness.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --result_file results/assignment_diagnostics/phase9c2_training_entry_readiness_n50_m3.json
```

Result JSON:

```text
results/assignment_diagnostics/phase9c2_training_entry_readiness_n50_m3.json
```

Result summary:

```text
scenario_config_applied = true
num_agents = 3
num_viewpoints = 50
noop_id = 50
actor_observation_shape = [1, 909]
shared_observation_shape = [1, 3, 2727]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
episode_length_default_value = 1000
episode_length_override_supported = true
episode_length_override_value = 300
assignment_rl_reward_log_keys_present = true
reward_shape = [1, 3, 1]
reward_finite = true
wrapper_step_success = true
no_checkpoint_loaded = true
no_checkpoint_saved = true
no_training_run = true
runner_run_called = false
```

## 7. Remaining Limitations

- Still no RL training was run.
- No learned-policy quality claim is made.
- Still fixed `N=50 / M=3` only.
- Only HAPPO was verified in the smoke path.
- Old fixed-12 assignment checkpoints remain incompatible because they use 13 logits, not 51.
- Old scan checkpoints remain incompatible because they target 9D continuous actions, not discrete assignment actions.
- `play_assignment.py` still requires a future fresh N=50 checkpoint directory; none was created in this phase.

## 8. Explicit Non-Changes

Phase 9C-2 did not change:

- reward formulas
- reward scale defaults
- observation semantics
- `available_mask` semantics
- `feasible_mask` semantics
- `static_geometric_feasible_mask` semantics
- solver behavior
- controller logic
- HARL internals or installed site-packages
- environment dynamics
- robot motion
- collision, IK, raycast, local avoidance, or path planning
- retry, fallback, or cooldown behavior
- checkpoint loading or saving
- `runner.run()`
- RL training
- formal RL evaluation
- checkpoint evaluation
- handcrafted baseline rules

## 9. Next Recommended Step

If Phase 9C-2 is accepted, either prepare a single coherent commit for the fixed-N assignment RL readiness checkpoint, or explicitly scope a very tiny training smoke.

Do not start training, formal evaluation, checkpoint play, or old-checkpoint evaluation unless a later task explicitly asks for it.
