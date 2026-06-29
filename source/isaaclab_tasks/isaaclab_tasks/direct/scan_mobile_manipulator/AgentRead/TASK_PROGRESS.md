# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9C-2 training-entry readiness fixes are complete.

No commit has been made. Phase 9C-2 did not run RL training, formal RL evaluation, checkpoint play, checkpoint
evaluation, checkpoint loading, checkpoint saving, or `runner.run()`.

Latest report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
```

Latest result JSONs:

```text
results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3_after_9c2.json
results/assignment_diagnostics/phase9c2_training_entry_readiness_n50_m3.json
```

## Latest Completed Phase

Phase 9C-2 resolved the small fixed-N assignment RL training-entry blockers identified by Phase 9C-0 and Phase 9C-1:

```text
1. Added a shared scenario_config-to-env_cfg bridge for fixed N=50 assignment entry points.
2. Added --scenario_config support to scripts/reinforcement_learning/harl/train.py for --assignment_rl only.
3. Added --scenario_config support to scripts/reinforcement_learning/harl/play_assignment.py.
4. Added --assignment_episode_length for assignment train entry, with recommended future value 300.
5. Flattened assignment_rl_reward.* terms into AssignmentIsaacLabEnv.log_info for HARL logging.
6. Added a no-training readiness smoke for scenario_config, episode_length override, shapes, wrapper step, and reward log keys.
```

The phase stayed entry/logging-only. It did not change reward formulas, observation semantics, mask semantics, solver
behavior, controller logic, HARL internals, installed site-packages, or environment dynamics.

## Active Architecture

Current fixed-N assignment RL interface:

```text
num_agents = 3
num_viewpoints = 50
viewpoint action ids = 0..49
noop action id = 50
available_actions shape = [num_envs, 3, 51]
available_mask shape = [num_envs, 3, 50]
actor observation shape in N=50 smoke = [1, 909]
shared observation shape in N=50 smoke = [1, 3, 2727]
action_space = Discrete(51) per robot
```

Reward smoke defaults remain:

```text
repeated_assignment_penalty_scale = 0.01
repeated_assignment_grace_steps = 2
no_progress_penalty_scale = 0.01
no_progress_grace_steps = 2
no_progress_penalty_cap = 0.05
selected_path_cost_penalty_scale = 0.0
```

Reward shaping remains wrapper-local in `AssignmentHarlWrapper.step()` and does not change the base environment reward
path or non-RL baseline evaluator reward behavior.

## Key Files

Phase 9C-2 files changed or created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/environments/test_assignment_harl_fresh_policy_smoke.py
scripts/environments/test_assignment_training_entry_readiness.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Earlier Phase 9B/9C uncommitted files remain in the working tree.

Important path note:

```text
scripts/reinforcement_learning/harl/assignment_harl_training.py does not exist.
The actual assignment training shim is:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
```

## Latest Verification

Compile check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/test_assignment_harl_fresh_policy_smoke.py scripts/environments/test_assignment_training_entry_readiness.py scripts/reinforcement_learning/harl/train.py scripts/reinforcement_learning/harl/play_assignment.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

Result: passed.

Phase 9C-1 smoke after 9C-2 changes:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_fresh_policy_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9c1_fresh_policy_tensor_flow_smoke_n50_m3_after_9c2.json
```

Result: passed.

Key tensor-flow result:

```text
actor_observation_shape = [1, 909]
shared_observation_shape = [1, 3, 2727]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
fresh actor head width = 51 per robot
sampled actions available = true for all robots
reward_shape = [1, 3, 1]
reward_finite = true
assignment_rl_reward decomposition present = true
no_checkpoint_loaded = true
no_training_run = true
```

Phase 9C-2 readiness smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_training_entry_readiness.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --result_file results/assignment_diagnostics/phase9c2_training_entry_readiness_n50_m3.json
```

Result: passed.

Key readiness result:

```text
scenario_config_applied = true
num_agents = 3
num_viewpoints = 50
noop_id = 50
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

Final checks for this handoff:

```text
git diff --check: passed with Windows LF-to-CRLF warnings only
git status --short: expected uncommitted Phase 9B/9C files remain; no commit made
```

## Known Issues / Blockers

Remaining limitations:

```text
No RL training has been run yet.
No learned-policy quality claim has been made.
Still fixed N=50/M=3 only.
Only HAPPO has been smoke-tested in the fresh-policy/readiness path.
Old fixed-12 assignment checkpoints have 13 logits and remain incompatible with N=50.
Old scan checkpoints are 9D continuous and remain incompatible with assignment RL.
play_assignment.py now has the scenario_config bridge, but it still requires a future fresh N=50 checkpoint directory.
```

## Do Not Do

Do not commit until the user asks.

Do not start RL training, formal RL evaluation, checkpoint play, checkpoint evaluation, checkpoint loading, or checkpoint
saving yet.

Do not use old assignment_happo fixed-12 checkpoints or scan_happo continuous checkpoints for N=50 assignment play or
training.

Do not change available_mask, feasible_mask, static_geometric_feasible_mask, solver behavior, controller logic, HARL
internals, installed site-packages, environment dynamics, robot motion, collision, IK, raycast, local avoidance, path
planning, retry, fallback, or cooldown behavior.

Do not add new handcrafted baseline rules.

## Next Step

Recommended next task: either prepare a single coherent commit for the fixed-N assignment RL readiness checkpoint, or
explicitly scope a very tiny training smoke.

If tiny training is scoped later, use a fresh N=50 assignment run only, with no checkpoint loading and with:

```text
--assignment_rl
--scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
--assignment_episode_length 300
```

Do not start training unless a later task explicitly asks for it.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B_FIXEDN_DYNAMIC_POLICY_INTERFACE_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C0_TRAINING_CONFIG_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C1_FRESH_POLICY_TENSOR_FLOW_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9C2_TRAINING_ENTRY_READINESS_FIXES_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9B3_REWRITE_20260629.md
```
