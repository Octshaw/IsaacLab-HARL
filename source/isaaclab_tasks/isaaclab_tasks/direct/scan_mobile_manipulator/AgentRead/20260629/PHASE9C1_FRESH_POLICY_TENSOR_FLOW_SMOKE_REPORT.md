# Phase 9C-1 Fresh-Policy Tensor-Flow Smoke Report

Date: 2026-06-29

## Scope And Boundaries

Phase 9C-1 adds and runs the smallest no-training helper for fixed N=50, M=3 assignment RL fresh-policy tensor flow.

This phase verifies that a fresh HARL actor stack can be instantiated directly from the current
`AssignmentHarlWrapper` observation/action spaces, consume the wrapper's augmented observations and
`available_actions[:, agent_id, :]`, produce valid masked Discrete viewpoint ids, step the wrapper once, and expose
the Phase 9B-3 reward decomposition.

This is not RL training, formal RL evaluation, checkpoint play, checkpoint evaluation, or a policy-quality claim.

Phase 9C-1 did not call `runner.run()`, did not use `--dir`, did not load checkpoints, did not save checkpoints, and
did not modify reward behavior, observation behavior, mask semantics, feasibility logic, solver behavior, controller
logic, HARL internals, installed site-packages, environment dynamics, robot motion, collision, IK, raycast, local
avoidance, path planning, retry, fallback, cooldown, or handcrafted baseline rules.

## Files Changed

```text
scripts/environments/test_assignment_harl_fresh_policy_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C1_FRESH_POLICY_TENSOR_FLOW_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Existing Phase 9B files were left in place. Existing Phase 9B reports were not deleted, renamed, or recreated.

## Actor-Construction Approach

The helper intentionally does not create a HARL runner. It avoids `AssignmentOnPolicyHARunner` because runner
construction can create output directories and is coupled to training lifecycle state.

Instead, the helper follows the smallest safe path:

```text
1. Launch Isaac Lab through AppLauncher.
2. Load algorithm_proxy_component_mesh.yaml through the existing scenario_config helpers.
3. Build env_cfg with parse_env_cfg and apply the same N=50 scenario defaults used by wrapper smokes.
4. Create the normal task environment through make_assignment_harl_env(...), returning AssignmentHarlWrapper.
5. Load the task-local HARL actor config from agents/harl_happo_cfg.yaml.
6. Instantiate fresh ALGO_REGISTRY["happo"] actors from wrapper.observation_space/action_space.
7. Do not load any actor state_dict.
8. Do not call runner.run().
```

The helper uses the same HARL public actor interface used by `play_assignment.py`, but without checkpoint loading.

## HARL Wrapper Tensor-Flow Summary

Smoke result:

```text
num_envs = 1
num_agents = 3
num_viewpoints = 50
noop_id = 50
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
action space per agent = Discrete(51)
available_actions shape = [1, 3, 51]
available_mask shape = [1, 3, 50]
action tensor shape = [1, 3, 1]
```

The script asserts that actor observations and shared observations are finite, and that the wrapper continues to
return the expected available action and mask shapes after the wrapper step.

## Fresh Actor Action-Head Verification

Fresh HAPPO actors were instantiated for each robot from the wrapper spaces.

Action head widths:

```text
robot_0: 51
robot_1: 51
robot_2: 51
```

Each actor was verified as:

```text
action_type = Discrete
distribution_head = Categorical
head width = num_viewpoints + 1 = 51
```

No checkpoint was loaded:

```text
no_checkpoint_loaded = true
checkpoint_saved = false
no_training_run = true
runner_run_called = false
```

## Masked Action Verification

The helper called `actor.act(...)` once per agent with:

```text
available_actions[:, agent_id, :]
```

Sampled action ids from the successful smoke:

```text
robot_0: 31
robot_1: 6
robot_2: 44
```

Verification:

```text
per-agent action shape = [1, 1]
all sampled ids are scalar Discrete ids
all sampled ids are in range 0..50
all sampled ids respect available_actions
```

Result JSON fields:

```text
sampled_action_valid_per_agent = [[true], [true], [true]]
sampled_action_available_per_agent = [[true], [true], [true]]
```

## Wrapper Step Verification

The sampled fresh-policy actions were passed through `AssignmentHarlWrapper.step(...)` for one wrapper step.

Reward result:

```text
reward shape = [1, 3, 1]
reward finite = true
wrapper_step_success = true
```

Observed reward values:

```text
robot_0: -0.008785052224993706
robot_1: -0.009777777828276157
robot_2: -0.009777777828276157
```

Reward decomposition was present in `info["assignment_rl_reward"]`.

Keys:

```text
base_env_reward
config
final_reward
global_coverage_gain
global_no_progress
repeated_same_target_no_progress
same_target_streak
selected_path_cost
selected_path_cost_norm
selected_path_cost_raw
steps_since_global_coverage_gain
total_assignment_reward_adjustment
```

The helper also asserts that returned rewards match `assignment_rl_reward["final_reward"]`.

## Smoke Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_fresh_policy_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3.json
```

Result:

```text
[OK] fresh assignment policy tensor-flow smoke passed obs=[1, 909] shared=[1, 3, 2727] available=[1, 3, 51] head_widths={'robot_0': 51, 'robot_1': 51, 'robot_2': 51}
```

Result JSON:

```text
results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3.json
```

## Verification Results

Compile check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/test_assignment_harl_fresh_policy_smoke.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Result:

```text
passed
```

Fresh-policy tensor-flow smoke:

```text
passed
```

Final git checks are recorded in `TASK_PROGRESS.md`.

## Known Limitations

```text
No training was run.
No policy-quality claim is made.
No checkpoint was saved or loaded.
This remains fixed N=50/M=3 only.
The scenario_config bridge for train.py/play_assignment.py remains unresolved.
The train.episode_length versus env horizon readiness issue remains unresolved.
assignment_rl_reward logger flattening for HARL training logs remains unresolved.
Only HAPPO was smoke-tested because the task-local config inspected in this phase is harl_happo_cfg.yaml.
```

## Explicit Non-Changes

Phase 9C-1 did not change:

```text
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
formal RL evaluation
checkpoint evaluation
checkpoint play
checkpoint save/load
handcrafted baseline rules
```

## Next Recommended Step

If continuing toward a tiny training smoke, decide first whether to address these readiness blockers:

```text
scenario_config bridge or full Hydra override recipe for train.py/play_assignment.py
train.episode_length alignment/documentation against the approximately 300-step env horizon
assignment_rl_reward.* flattening into HARL training logger scalars
```

Do not start training yet unless a later task explicitly scopes it.
