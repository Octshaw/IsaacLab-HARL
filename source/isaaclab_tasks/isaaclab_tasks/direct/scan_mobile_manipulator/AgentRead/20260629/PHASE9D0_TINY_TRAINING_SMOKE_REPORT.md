# Phase 9D-0 Tiny Fixed-N Assignment Training Smoke Report

Date: 2026-06-29

## 1. Scope and Boundaries

Phase 9D-0 ran a very small fresh fixed `N=50 / M=3` HAPPO assignment-RL training-entry smoke for:

- `Isaac-Scan-Mobile-Manipulator-Direct-v0`
- `--assignment_rl`
- fixed scenario config `algorithm_proxy_component_mesh.yaml`
- no checkpoint loading
- no `--dir`
- no play/checkpoint evaluation/formal evaluation

The smoke only checked training-entry wiring, rollout collection, logging, update execution, and save behavior. It does not make a learned-policy quality claim, coverage-improvement claim, or arbitrary-`N` claim.

No solver, controller, mask/feasibility logic, environment dynamics, reward formula, observation semantics, HARL internals, installed `site-packages`, handcrafted baselines, or experiment config files were changed.

## 2. Exact Commands Run

Initial CPU-targeted attempt:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1000 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d0_tiny_train_smoke --save_interval 500 --log_interval 1
```

Console log:

```text
results/assignment_diagnostics/phase9d0_tiny_train_smoke_console.log
```

Result: failed before the first env step with `RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED`. Although the Isaac launcher accepted `--device cpu`, HARL still selected CUDA from the algorithm config (`choose to use gpu...`), and the train.py CUDA warm-up path was skipped because the CLI device was `cpu`.

Minimal rerun with only the device target changed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1000 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9d0_tiny_train_smoke --save_interval 500 --log_interval 1
```

Console log:

```text
results/assignment_diagnostics/phase9d0_tiny_train_smoke_cuda_console.log
```

Result: passed.

## 3. Code or Config Changes

No Python code, scenario config, solver/controller/mask/env/HARL files, or installed package files were changed.

Files created/updated for documentation only:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D0_TINY_TRAINING_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Run artifacts were written under `results/`.

## 4. Training Smoke Result

Status: passed on the CUDA rerun after the CPU-targeted attempt exposed a device mismatch.

Runtime summary:

- initial CPU-targeted attempt: about 53 seconds, failed before rollout collection due CUDA/cuBLAS initialization
- CUDA rerun: about 372 seconds wall time
- on-policy episodes: `1000 // 300 // 1 = 3`
- collected rollout/update cycles: 3
- reported timesteps: `300/1000`, `600/1000`, `900/1000`
- reported FPS: about 19-21
- process exit: clean, exit code 0

Successful output directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36
```

Successful log paths:

```text
results/assignment_diagnostics/phase9d0_tiny_train_smoke_cuda_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/logs/events.out.tfevents.1782725496.xxsys203-1
```

Checkpoint/model paths created:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/best_model
```

The configured `--save_interval 500` did not trigger a periodic episode-interval save because the run had only 3 episodes. `scripts/reinforcement_learning/harl/train.py` saved a final HARL model to `models`, and HARL also wrote `best_model` after the logged reward improved from its initial sentinel.

The failed CPU-targeted attempt created a partial run directory with only config/log scaffolding:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-25-10
```

## 5. Confirmed Configuration

Confirmed from command, console output, and `configs.json`:

```text
task = Isaac-Scan-Mobile-Manipulator-Direct-v0
algorithm = happo
assignment_rl = true
scenario_config = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
resolved scenario_config_path = E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml
assignment_episode_length = 300
num_envs = 1
num_env_steps = 1000
device = cuda:0 for the passing run
exp_name = assignment_happo_n50_phase9d0_tiny_train_smoke
save_interval = 500
log_interval = 1
model_dir = null
```

`model_dir = null` and absence of `--dir` confirm no checkpoint was requested for loading.

## 6. Confirmed Tensor and Action Path

The passing run printed:

```text
Scan viewpoints loaded ... num_viewpoints=50 no-op id=50 viewpoint_ids=[0, ..., 49]
share_observation_space: {0: Box(-inf, inf, (2727,), float32), ...}
observation_space: {0: Box(-inf, inf, (909,), float32), ...}
action_space: {0: Discrete(51), 1: Discrete(51), 2: Discrete(51)}
Assignment RL num_viewpoints=50
Assignment RL no-op action id=50
Assignment RL actor agent 0 action_type=Discrete distribution_head=Categorical
Assignment RL actor agent 1 action_type=Discrete distribution_head=Categorical
Assignment RL actor agent 2 action_type=Discrete distribution_head=Categorical
Scan reset diagnostics num_envs=1 num_agents=3 num_viewpoints=50 no-op id=50 available_actions shape=(1, 3, 51)
Assignment RL reset returned available_actions shape=(1, 3, 51) device=cuda:0
Assignment RL warmup stored available_actions env_shape=(1, 3, 51) per_agent_buffer_shape=(301, 1, 51)
Assignment RL collect passes available_actions[:, agent_id, :] to each actor policy
```

Confirmed path:

```text
N = 50
M = 3
viewpoint ids = 0..49
noop id = 50
action dim = 51
per-agent action space = Discrete(51)
actor head/distribution path = Discrete/Categorical, not old 13-logit assignment checkpoints and not 9D continuous
actor observation dim = 909
shared observation dim = 2727
available_actions shape = [1, 3, 51]
```

No rollout shape crash occurred in the passing CUDA run.

## 7. Logger Check

Console and TensorBoard event logs include `assignment_rl_reward/*` keys.

Observed TensorBoard scalar tags from the passing run included:

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

Each listed assignment reward scalar appeared 3 times, once per logged episode.

A scalar finite-value check over the event file found:

```text
scalar_tags = 33
scalar_values = 99
nonfinite_scalar_values = []
```

No NaN/Inf was observed in the obvious logged rewards/losses. Logged loss scalars included 3 entries each for `agent0/policy_loss`, `agent1/policy_loss`, `agent2/policy_loss`, and `critic/value_loss`.

## 8. Checkpoint Check

No checkpoint was loaded:

- command omitted `--dir`
- saved `configs.json` has `model_dir = null`
- no restore/load message appeared in the console log
- old fixed-12 assignment and old 9D scan checkpoints were not used

Checkpoint/model artifacts were saved by the passing smoke:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models/actor_agent_robot_0.pt
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models/actor_agent_robot_1.pt
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models/actor_agent_robot_2.pt
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models/critic_agent.pt
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d0_tiny_train_smoke/seed-00001-2026-06-29-17-31-36/models/value_normalizer.pt
```

`best_model` contains the same artifact types.

## 9. Known Limitations

- This was a very tiny training-entry smoke only.
- It is not formal training.
- It is not formal RL evaluation.
- It is not checkpoint play.
- It is not enough to judge coverage improvement.
- It does not establish learned-policy quality.
- It only covers fixed `N=50 / M=3`.
- It does not address arbitrary-`N`, Transformer, or GNN policy work.
- The initial CPU-targeted command is not currently viable because HARL still selected CUDA from the config while train.py skipped CUDA warm-up for `--device cpu`.

## 10. Next Recommendation

Phase 9D-0 passed on `cuda:0`. Do not jump directly to full training.

Recommended next phase: Phase 9D-1 short debug training with a fresh N=50 assignment run, still no old checkpoint loading, no formal evaluation, no checkpoint play, and no reward/solver/controller/mask tuning based on the tiny smoke.
