# Phase 9B-3 Reward Smoke Report

Date: 2026-06-29

## Scope And Boundaries

Phase 9B-3 implements a minimal reward-shaping smoke path for fixed N=50, M=3 assignment RL. The reward terms target
the Phase 9B-1A plateau diagnosis: repeated same-target no-progress behavior and long global no-progress after the
last coverage gain.

This phase did not start RL training, did not evaluate old checkpoints, and did not run formal RL evaluation. It did
not change available-mask semantics, feasible-mask semantics, static geometric feasibility, solver behavior,
controller logic, HARL internals, installed site-packages, environment dynamics, robot motion, collision, IK, raycast,
local avoidance, path planning, retry, fallback, cooldown behavior, or handcrafted baseline rules.

## Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B3_REWARD_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9B3_REWRITE_20260629.md
```

The reward shaping is applied in `AssignmentHarlWrapper.step()` after the base env reward is stacked. The base
environment reward computation in `scan_mobile_manipulator_env.py` is not changed. Non-RL baseline evaluator reward
behavior is therefore not intentionally changed.

## Reward Terms Added

### repeated_same_target_no_progress

Applies only to non-noop assignment actions. It becomes active when the same robot repeatedly selects the same
viewpoint beyond `repeated_assignment_grace_steps` and the step produced no new global coverage.

Formula:

```text
- repeated_assignment_penalty_scale
  * max(0, same_target_streak - repeated_assignment_grace_steps)
```

The scripted noop agent receives zero repeated-assignment penalty.

### global_no_progress

Applies to all agents when global coverage has not increased beyond `no_progress_grace_steps`. The magnitude is capped.

Formula:

```text
- min(
    no_progress_penalty_scale * max(0, steps_since_global_coverage_gain - no_progress_grace_steps),
    no_progress_penalty_cap
  )
```

### selected_path_cost

Implemented as a logged, conservative candidate. It uses the decision-time selected cost from the pre-step assignment
problem and is multiplied by `selected_path_cost_penalty_scale`.

Default scale is `0.0`, so this term is disabled by default in Phase 9B-3.

## Config Fields

Added as assignment-wrapper reward smoke fields on `ScanMobileManipulatorEnvCfg`:

```text
repeated_assignment_penalty_scale = 0.01
repeated_assignment_grace_steps = 2
no_progress_penalty_scale = 0.01
no_progress_grace_steps = 2
no_progress_penalty_cap = 0.05
selected_path_cost_penalty_scale = 0.0
```

Default activity:

```text
repeated_same_target_no_progress: active, conservative scale
global_no_progress: active, conservative scale and cap
selected_path_cost: disabled by default
```

## Reward Decomposition Keys

The wrapper writes reward decomposition under `info["assignment_rl_reward"]` and stores the last decomposition in
`wrapper.last_assignment_reward_terms`.

Keys:

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

`final_reward` is the reward returned by the wrapper. `base_env_reward` is logged separately so the additive shaping
can be inspected.

## Scripted Smoke Behavior

The smoke uses the existing manual action pattern:

```text
robot_0 -> viewpoint 0
robot_1 -> viewpoint 1
robot_2 -> noop
```

The same action is repeated for 8 wrapper steps. This creates a short no-progress repeated-assignment script without
training or checkpoint evaluation.

Observed term means:

```text
step 1: repeat =  0.000000, no_progress =  0.000000, path_cost = 0.000000
step 2: repeat =  0.000000, no_progress =  0.000000, path_cost = 0.000000
step 3: repeat = -0.006667, no_progress = -0.010000, path_cost = 0.000000
step 4: repeat = -0.013333, no_progress = -0.020000, path_cost = 0.000000
step 5: repeat = -0.020000, no_progress = -0.030000, path_cost = 0.000000
step 6: repeat = -0.026667, no_progress = -0.040000, path_cost = 0.000000
step 7: repeat = -0.033333, no_progress = -0.050000, path_cost = 0.000000
step 8: repeat = -0.040000, no_progress = -0.050000, path_cost = 0.000000
```

The first negative step is 3 for both repeated same-target no-progress and global no-progress. This matches the grace
threshold of 2.

## Smoke Command

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 8 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9b3_reward_smoke_n50_m3.json
```

Output path:

```text
results/assignment_diagnostics/phase9b3_reward_smoke_n50_m3.json
```

Result:

```text
[OK] assignment HARL wrapper smoke passed
```

## Verification Results

Compile check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/evaluate_assignment_methods.py
```

Result:

```text
passed
```

Smoke assertions verified:

```text
reward output shape unchanged = [1, 3, 1]
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
actor observation shape = [1, 909]
shared observation shape = [1, 3, 2727]
reward decomposition present in info["assignment_rl_reward"]
repeated_same_target_no_progress is zero before grace
repeated_same_target_no_progress becomes negative after grace
global_no_progress is zero before grace
global_no_progress becomes negative after grace
selected_path_cost is zero because selected_path_cost_penalty_scale = 0.0
all logged reward terms are finite
```

`git diff --check` passed with Windows LF-to-CRLF warnings only and no whitespace errors.

## Known Limitations

This is a reward smoke, not a learned-policy quality claim.

The terms are assignment-wrapper reward shaping terms. They are intentionally not wired into the non-RL baseline
evaluator or the base environment reward path.

The repeated-same-target term is global-coverage gated. It does not yet distinguish all valid dwell/retry cases.

Selected path cost is logged and implemented but disabled by default because Phase 9B-1A showed path cost alone can
reinforce sitting on low-cost repeated targets.

Duplicate selected target, noop-when-available, selected-target conflict, inter-robot overlap, actual base-motion
crossing, obstacle selected-intersection, and hard load-balance terms remain reporting-only and do not affect reward in
Phase 9B-3.

## Explicit Non-Changes

Phase 9B-3 did not change:

```text
available_mask semantics
feasible_mask semantics
static_geometric_feasible_mask semantics
solver behavior
controller logic
HARL internals or installed site-packages
environment dynamics
robot motion
collision, IK, raycast, local avoidance, path planning
retry, fallback, or cooldown behavior
RL training
formal RL evaluation
handcrafted baseline rules
```

## Next Recommended Step

Do not start RL training yet. First review the fixed-N observation/reward smoke chain and decide whether the next phase
should be a very small fresh-policy construction/tensor-flow smoke or a config review for future N=50 training.
