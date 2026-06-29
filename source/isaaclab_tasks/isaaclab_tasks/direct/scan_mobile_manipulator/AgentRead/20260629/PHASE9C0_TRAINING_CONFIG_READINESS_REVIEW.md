# Phase 9C-0 Training-Config Readiness Review

Date: 2026-06-29

## Scope And Boundaries

Phase 9C-0 reviews whether the current fixed N=50, M=3 assignment-RL configuration is ready for a future
fresh-policy tensor-flow smoke and later very short training smoke.

This is a readiness/audit phase only. It did not train, did not run formal RL evaluation, did not evaluate old
checkpoints, did not instantiate a long training run, and did not modify solver behavior, controller logic, masks,
HARL internals, installed site-packages, environment dynamics, reward behavior, observation behavior, or handcrafted
baseline rules.

Scope remains fixed-scale:

```text
num_viewpoints = 50
num_agents = 3
viewpoint action ids = 0..49
noop action id = 50
```

This is not arbitrary-N Transformer/GNN/set-policy work yet.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B_FIXEDN_DYNAMIC_POLICY_INTERFACE_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/agents/harl_happo_cfg.yaml
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/test_assignment_harl_discrete_shape.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
```

Path note:

```text
scripts/reinforcement_learning/harl/assignment_harl_training.py does not exist.
The actual assignment runner shim is:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
```

## Training Entry-Point Recommendation

Recommended future training entry point:

```powershell
scripts/reinforcement_learning/harl/train.py --assignment_rl --algorithm happo
```

Reason:

```text
train.py registers the repo-local AssignmentOnPolicyHARunner when --assignment_rl is set.
AssignmentOnPolicyHARunner constructs AssignmentIsaacLabEnv.
AssignmentIsaacLabEnv wraps the normal scan environment with AssignmentHarlWrapper.
The runner creates Discrete/Categorical actors instead of the old 9D continuous action path.
train.py forces algo_args["eval"]["use_eval"] = False.
```

Do not use the generic HARL training path without `--assignment_rl` for N=50 assignment learning. Without that flag,
the script uses the normal continuous scan-action environment path.

Readiness caveat:

```text
train.py does not currently expose --scenario_config.
```

The N=50 real-component proxy setup used by Phase 9B smokes is loaded through
`algorithm_proxy_component_mesh.yaml` by the smoke/evaluator scripts. The training script only receives Hydra
arguments after parsing known CLI flags. Before any actual training, either:

```text
1. confirm a complete Hydra override set for viewpoint_csv_path, robot_config_path, capability_config_path,
   component mesh, diagnostics, and related N=50 scenario fields; or
2. add a small scenario_config bridge to the assignment training/play scripts in a later phase.
```

No config bridge was added in Phase 9C-0.

## Play / Smoke Entry-Point Recommendation

Recommended checkpoint play path, after a fresh same-N checkpoint exists:

```powershell
scripts/reinforcement_learning/harl/play_assignment.py --assignment_rl
```

Reason:

```text
play_assignment.py is assignment-specific.
It builds AssignmentHarlWrapper directly through make_assignment_harl_env().
It instantiates HARL actors from wrapper observation/action spaces.
It passes available_actions[:, agent_id, :] into each actor.
It rejects non-Discrete/non-Categorical actors.
```

However, `play_assignment.py` is checkpoint-based and requires `--dir`. It should not be used for Phase 9C-1
fresh-policy construction, because using it now would require loading a checkpoint. It also does not expose
`--scenario_config`, so the same N=50 scenario-configuration caveat applies before any future N=50 play smoke.

For no-checkpoint wrapper checks, keep using:

```powershell
scripts/environments/test_assignment_harl_wrapper_smoke.py
```

That script already accepts `--scenario_config`, loads the N=50 scenario, verifies wrapper observation/mask/action
shapes, and checks reward decomposition signs.

## HARL Wrapper Compatibility Summary

Phase 9B-2 and Phase 9B-3 smokes confirmed the current fixed-N assignment wrapper shapes:

```text
num_agents = 3
num_viewpoints = 50
noop_id = 50
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
action dimension = Discrete(51)
available_actions shape = [1, 3, 51]
available_mask shape = [1, 3, 50]
```

The actor observation is:

```text
96D original scan observation
+ 50 x 14 id-aligned viewpoint rows
+ noop context
+ previous-assignment one-hot over 51 ids
+ dynamic assignment scalar state
+ full covered vector
```

`AssignmentOnPolicyHARunner` uses the repo-local scalar action-dim adapter, so HARL buffers store scalar Discrete ids
with width 1 while policy logits remain 51-way Categorical distributions.

## Checkpoint Compatibility Risks

Do not load old checkpoints for fixed N=50 assignment RL.

Known incompatible checkpoint families:

```text
old assignment checkpoints: fixed N=12 plus noop, 13 logits
old scan checkpoints: 9D continuous scan actions
```

Risk locations:

```text
train.py --dir <path> sets algo_args["train"]["model_dir"] and triggers runner.restore().
play_assignment.py --dir <path> loads actor_agent_*.pt checkpoint files.
evaluate_assignment_methods.py has an assignment_rl checkpoint path, but assignment-RL evaluation is disabled in main().
```

Recommendation:

```text
For Phase 9C-1 and the first tiny training smoke, leave --dir unset.
Use a fresh experiment name.
Do not point --dir at assignment_happo fixed-12 runs, scan_happo continuous runs, or any old checkpoint directory.
```

## Horizon / Config Review

Environment horizon:

```text
ScanMobileManipulatorEnvCfg.episode_length_s = 30.0
ScanMobileManipulatorEnvCfg.decimation = 6
Simulation dt = 1 / 60
control step = 0.1 s
effective env episode horizon = about 300 control steps
```

HARL config:

```text
source/.../agents/harl_happo_cfg.yaml:
  train.episode_length = 1000
  train.num_env_steps = 10000000
  train.n_rollout_threads = 20
```

`train.py` overrides:

```text
train.n_rollout_threads = --num_envs
train.num_env_steps = --num_env_steps
train.eval_interval = --save_interval
train.log_interval = --log_interval
train.model_dir = --dir
```

`train.py` does not currently override:

```text
train.episode_length
```

Readiness conclusion:

```text
The default HARL rollout length of 1000 is longer than the env's approximately 300-step episode horizon.
This is not necessarily a shape blocker, but it is a training-smoke readiness risk.
For the first tiny training smoke, set or document train.episode_length around 300, or explicitly justify a longer
rollout buffer with proper time-limit handling.
```

No config was changed in Phase 9C-0.

## Eval-Path Review

Safe default for future `train.py --assignment_rl`:

```text
train.py forces algo_args["eval"]["use_eval"] = False.
```

Risky path:

```text
AssignmentOnPolicyHARunner still calls HARL make_eval_env(...) if algo_args["eval"]["use_eval"] is True.
That eval path is generic and is not the assignment wrapper path.
```

Therefore:

```text
Do not re-enable HARL generic eval for assignment RL until a wrapper-aware assignment eval path is designed.
Do not use evaluate_assignment_methods.py for assignment_rl policy evaluation in this phase.
```

`evaluate_assignment_methods.py` currently rejects `--assignment_rl` or `--assignment_checkpoint_dir` in `main()`, so
formal assignment-RL evaluation remains disabled.

## Reward / Config Review

Phase 9B-3 reward-shaping fields are visible on `ScanMobileManipulatorEnvCfg` and consumed by
`AssignmentHarlWrapper`:

```text
repeated_assignment_penalty_scale = 0.01
repeated_assignment_grace_steps = 2
no_progress_penalty_scale = 0.01
no_progress_grace_steps = 2
no_progress_penalty_cap = 0.05
selected_path_cost_penalty_scale = 0.0
```

Recommendation for Phase 9C-1:

```text
Keep these smoke defaults unchanged.
Do not tune reward scales during fresh-policy construction/tensor-flow smoke.
Keep selected_path_cost disabled at 0.0 because path cost alone can reinforce low-cost stuck behavior.
```

Reward decomposition is present in wrapper `info["assignment_rl_reward"]` and in the Phase 9B wrapper smoke JSON.
Keys include:

```text
config
base_env_reward
repeated_same_target_no_progress
global_no_progress
selected_path_cost
selected_path_cost_raw
selected_path_cost_norm
total_assignment_reward_adjustment
final_reward
same_target_streak
steps_since_global_coverage_gain
global_coverage_gain
```

Logging caveat:

```text
AssignmentIsaacLabEnv._update_log_info currently flattens info["assignment_rl"] and env info["log"].
It does not yet flatten info["assignment_rl_reward"] into HARL logger scalars.
```

This is not a tensor-flow blocker, because the wrapper exposes the reward decomposition and the smoke result JSON
checks it. Before real training, add or verify explicit HARL logger scalar handling for the most important
`assignment_rl_reward.*` terms.

## Logging / Output Naming Recommendation

Avoid old or ambiguous output names:

```text
do not use exp_name=test
do not reuse assignment_happo_1m_len320_night
do not reuse scan_happo output folders
do not load old seed directories through --dir
```

Recommended fresh names:

```text
Phase 9C-1 no-training tensor-flow smoke result:
  results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3.json

Future tiny training smoke experiment name:
  assignment_happo_n50_phase9c_tiny_train_smoke
```

HARL training output would be under:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/<exp_name>/seed-xxxxx-<timestamp>/
```

## Recommended Phase 9C-1 Command

Current readiness conclusion:

```text
The repository has wrapper smokes and a fixed-12 Discrete adapter smoke, but it does not yet have a dedicated
N=50 fresh-policy construction/tensor-flow smoke that instantiates fresh HARL actors against the 909D wrapper obs
and runs one masked Categorical action pass without training.
```

Phase 9C-1 should add the smallest no-training helper for that purpose, then run:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_fresh_policy_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3.json
```

Required Phase 9C-1 behavior:

```text
instantiate AssignmentHarlWrapper with N=50 scenario_config
instantiate fresh HARL actors from wrapper.observation_space/action_space
verify Categorical action head width is 51
reset wrapper and read obs/shared_obs/available_actions
call actor.act once per agent with available_actions[:, agent_id, :]
step wrapper for 1-2 scripted or sampled masked actions
inspect reward decomposition
write a JSON result
do not call runner.run()
do not save a checkpoint
do not claim policy quality
```

Do not use `train.py --assignment_rl` as Phase 9C-1, because `runner.run()` begins training.

## Commands Not To Run Yet

Do not run actual training yet:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl ...
```

Do not run checkpoint play yet:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/play_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --dir <old-or-unknown-checkpoint> ...
```

Do not run formal assignment-RL evaluation or old checkpoint evaluation:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --assignment_rl --assignment_checkpoint_dir <checkpoint> ...
```

Do not load:

```text
old fixed-12 assignment checkpoints
old 9D continuous scan checkpoints
generic HARL eval paths that bypass AssignmentHarlWrapper
```

## Required Minimal Changes

No code or config changes were required for Phase 9C-0.

Readiness recommendations for later phases:

```text
1. Add a dedicated Phase 9C-1 no-training fresh-policy tensor-flow smoke helper.
2. Before any training, add or document a scenario_config bridge or complete Hydra overrides for N=50 training/play.
3. Before any training, align or explicitly document train.episode_length versus the env's approximately 300-step horizon.
4. Before any real training run, expose assignment_rl_reward.* scalars to the HARL training logger if those curves are
   expected in training logs.
```

## Verification

No `py_compile` was required because Phase 9C-0 changed documentation only.

Planned final checks for this phase:

```powershell
git diff --check
git status --short
```

These checks are recorded in `TASK_PROGRESS.md`.

## Explicit Non-Changes

Phase 9C-0 did not change:

```text
Python code
YAML/config behavior
reward behavior
observation behavior
available_mask semantics
feasible_mask semantics
static_geometric_feasible_mask semantics
solver behavior
controller logic
HARL internals or installed site-packages
environment dynamics
robot motion
collision, IK, raycast, local avoidance, path planning
retry, fallback, cooldown
RL training
formal RL evaluation
old checkpoint evaluation
handcrafted baseline rules
```
