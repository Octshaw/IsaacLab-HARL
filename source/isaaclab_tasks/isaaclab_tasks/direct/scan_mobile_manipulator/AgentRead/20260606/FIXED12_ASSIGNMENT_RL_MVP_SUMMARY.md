# Fixed-12 Assignment-RL MVP Summary

## 1. Project Goal Recap

The assignment-RL work changed the scan mobile manipulator task from direct 9D continuous policy output to a higher-level assignment interface:

```text
RL selects viewpoint ids
  -> assignment tensor [num_envs, num_agents]
  -> existing assignment controller
  -> unchanged 9D scan env action dict
  -> unchanged scan env.step()
```

The goal was not to replace the scan environment, reward, or controller. The goal was to make RL, random, nearest, and greedy methods use the same assignment-controller-env path.

Current stage:

```text
fixed 12-viewpoint MVP
```

This means the current result proves the assignment-RL path works for the fixed 12-viewpoint scenario. It does not prove arbitrary viewpoint-set generalization.

## 2. Current Fixed-12 Assignment-RL Implementation Path

Current assignment training path:

```text
train.py --assignment_rl
  -> AssignmentOnPolicyHARunner
  -> AssignmentIsaacLabEnv
  -> AssignmentHarlWrapper
  -> Discrete(num_viewpoints + 1)
  -> available_actions mask
  -> scalar discrete action
  -> assignment
  -> viewpoint_assignment_to_actions()
  -> unchanged scan env.step(9D action dict)
```

Current assignment eval/play path:

```text
play_assignment.py / evaluate_assignment_methods.py
  -> restore assignment checkpoint
  -> HARL Categorical actor
  -> deterministic scalar discrete action
  -> available_actions[:, agent_id, :]
  -> AssignmentHarlWrapper
  -> decode/controller/env.step
  -> bounded max_steps run
  -> assignment diagnostics / CSV metrics
```

Default non-assignment HARL behavior remains the original raw 9D continuous action path.

## 3. Completed Phase 1-5 Overview

### Phase 1: Shared assignment RL utilities

Implemented assignment utility functions:

```text
make_assignment_action_mask()
decode_discrete_assignment()
assignment_to_env_actions()
compute_assignment_duplicate_count()
```

These utilities provide the shared mask, decode, controller entrypoint, and duplicate-count behavior used by later wrappers and tests.

### Phase 2: HARL Discrete action shape investigation and adapter

Confirmed HARL can use Discrete/Categorical policies, but repo-local shape helpers were needed so scalar Discrete actions are stored as width `1`, not `action_space.n`.

Implemented repo-local helpers for:

```text
Discrete(num_viewpoints + 1)
scalar action dim = 1
available_actions dim = num_viewpoints + 1
HARL action tensor allocation
```

No installed HARL package was modified.

### Phase 3A: Assignment-aware wrapper smoke

Implemented `AssignmentHarlWrapper`, which exposes per-agent `Discrete(num_viewpoints + 1)` action spaces while keeping the scan env's underlying 9D action interface unchanged.

Validated:

```text
reset -> obs, shared_obs, available_actions
step(discrete_actions)
  -> decode assignment
  -> viewpoint_assignment_to_actions()
  -> underlying env.step(9D dict)
```

### Phase 3B: Tiny assignment training smoke

Integrated assignment mode into the project training entry path through repo-local shim/runner logic.

Validated tiny HAPPO smoke:

```text
train.py --assignment_rl
```

The actor was Discrete/Categorical, `available_actions` was passed into policy, and the wrapper decode/controller/env.step path executed.

### Phase 4: Assignment play/eval smoke

Added dedicated bounded assignment play/eval script:

```text
scripts/reinforcement_learning/harl/play_assignment.py
```

Validated:

```text
assignment checkpoint restore
deterministic scalar discrete action
available_actions[:, agent_id, :]
AssignmentHarlWrapper decode/controller/env.step
bounded max_steps run
assignment diagnostics
```

### Phase 5: Fixed-12 baseline comparison

Added unified evaluator:

```text
scripts/environments/evaluate_assignment_methods.py
```

Compared:

```text
random
nearest
greedy
assignment_rl
```

Outputs:

```text
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
```

Phase 5 analysis report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
```

## 4. Key Files

Training and play/eval entrypoints:

```text
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_methods.py
```

Assignment-RL interface and wrappers:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
```

Scan environment and baselines:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/random_solver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/nearest_solver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/greedy_solver.py
```

Reports:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/ASSIGNMENT_BASED_RL_INTERFACE_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260605/ASSIGNMENT_BASED_RL_PHASE2_HARL_DISCRETE_SHAPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
```

## 5. Fixed-12 Scenario Capability Constraint

The current scenario has 12 fixed viewpoints. Viewpoint 11 was moved so it satisfies scanner min-range constraints and enters `available_mask`.

The current fixed scenario includes one manual capability override:

```python
fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
```

Reason:

Bounded diagnostics showed `robot_2` could not stably complete viewpoint 5 under the current high-level controller and coverage gates.

This override is:

```text
fixed-12 MVP scenario-level capability override
```

It is not:

```text
an arbitrary-viewpoint feasibility model
an IK/collision feasibility solver
a general rule for future viewpoint files
```

The next-stage feasibility generator should replace this manual override with automatic checks based on viewpoint pose and robot capability.

## 6. Phase 5 Baseline Comparison Results

Phase 5 summary:

| method | success | coverage | steps_full | auc | duplicate | noop | valid | return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 1.000 | 1.000 | 299.0 | 0.052 | 0.000 | 0.000 | 1.000 | 8.440 |
| nearest | 1.000 | 1.000 | 126.0 | 0.612 | 0.000 | 0.243 | 1.000 | 175.585 |
| greedy | 1.000 | 1.000 | 126.0 | 0.612 | 0.000 | 0.243 | 1.000 | 175.585 |
| assignment_rl | 1.000 | 1.000 | 118.0 | 0.485 | 0.415 | 0.031 | 1.000 | 198.785 |

CSV completeness:

```text
per_episode.csv: 20 rows
random: 5 episodes
nearest: 5 episodes
greedy: 5 episodes
assignment_rl: 5 episodes
summary.csv: 4 rows
```

## 7. Current Conclusions

Assignment-RL is successful in the fixed-12 MVP:

```text
success_rate = 1.0
mean_final_coverage = 1.0
mean_steps_to_full_coverage = 118.0
```

Compared with nearest/greedy:

```text
assignment_rl finishes earlier: 118 vs 126 steps
assignment_rl has higher return: 198.785 vs 175.585
assignment_rl has lower AUC: 0.485 vs 0.612
assignment_rl has nonzero duplicate assignment: 0.415 vs 0.000
```

No-op is not the main current issue:

```text
assignment_rl mean_noop_rate = 0.031
```

The current main behavior issue is duplicate assignment, but it does not prevent completion in the fixed MVP.

## 8. Current Limitations

- This is a fixed 12-viewpoint MVP.
- Viewpoints are still configured inside the env.
- The measured object is still a simplified box proxy.
- `robot_2 -> viewpoint_5` is still a fixed-scenario manual feasibility override.
- The scan env remains a high-level task-space skeleton.
- No real robot articulation, IK, collision, joint limits, or real motion controller is connected.
- Different viewpoint counts imply different Discrete action spaces and incompatible checkpoints.
- Arbitrary / variable viewpoint-count policy generalization is not complete.

## 9. Why Phase 6 Is Deferred

Phase 6 duplicate avoidance is useful, but not urgent.

Reasons to defer:

- Assignment-RL already reaches 100% coverage.
- Assignment-RL finishes faster than nearest/greedy.
- Valid action rate is 1.0.
- No-op rate is low.
- The next larger blocker is moving from fixed toy/MVP geometry to real component proxy and external viewpoint files.

Phase 6 should remain:

```text
optional optimization
```

It can be revisited after the next-stage scenario and feasibility generator are stable.

## 10. Recommended Next Direction

Recommended next stage:

```text
real component proxy
+ external viewpoint file
+ automatic feasibility generator
```

Do not jump directly to real robot articulation yet.

Recommended order:

1. Replace the measured object with a real component proxy.
2. Load a fixed-N viewpoint set from an external file.
3. Generate feasible masks automatically from geometry and robot capability.
4. Re-run random / nearest / greedy / assignment-RL on the new scenario.
5. Only later connect real robot USD / articulation / IK / collision / low-level motion control.

The next stage should preserve the current assignment-controller-env architecture while making the scene and feasibility model more realistic.
