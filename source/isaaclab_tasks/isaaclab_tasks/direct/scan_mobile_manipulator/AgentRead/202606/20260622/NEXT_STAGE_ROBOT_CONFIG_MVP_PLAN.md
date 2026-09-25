# Next Stage Robot Config MVP Plan

Date: 2026-06-22

## Stage Definition

Robot Config MVP: YAML-driven 3-robot setup with M-ready code path.

The current experiment can start with exactly three task-space proxy robots, but the implementation should not hard-code
three robots. The active robot count should come from enabled robot entries in a YAML robot config:

```text
M = number of enabled robots
```

Later, changing the robot count should be possible by editing YAML, not by refactoring environment code.

## Why This Stage Now

Stage 4B generated real-component N=24 diagnostics are paused. The temporary bbox-side viewpoint CSV:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
```

is useful for pipeline sanity, evaluator validation, visualization, and diagnostics, but it is not the final planned
viewpoint CSV and must not be treated as a final algorithm benchmark.

Recent diagnostics showed:

- external fixed-N evaluator path works;
- generated N=24 scenario loads correctly;
- nearest/greedy initially reached `17/24` coverage;
- pair-level Level 2 filtering improved this to `19/24`;
- retry/fallback made previously skipped target ids assigned, but coverage remained `19/24`;
- controller-state trace showed the remaining failures are mainly controller/gate/orientation timing issues in the
  temporary bbox sample.

The final real planned viewpoint CSV is intentionally out of scope for the current stage. It should be used only after
the simulation environment, robot configuration interface, assignment interface, and evaluator are validated with
fixed/default, temporary, and synthetic viewpoint sets. Therefore, the absence of the real CSV is not a blocker for Robot
Config MVP.

The current task is to make the environment robust to arbitrary legal viewpoint CSVs using simulation-only validation
data while improving the robot configuration and assignment interface. This avoids optimizing against the temporary
sample as if it were final planning output.

## Project Assumption

The long-term assignment problem is:

```text
Given arbitrary-size viewpoint sets and variable numbers of robots, perform dynamic task allocation with load balancing,
path cost, robot state changes, and task state updates.
```

The next stage should prepare the environment and evaluator for variable `M` while keeping current task-space proxy
robots.

## Viewpoint Input Policy Before Real CSV

The near-term validation should not depend on the final real planned viewpoint CSV.

Use the following viewpoint sources before final real CSV validation:

1. Fixed/default viewpoint sets, especially the fixed-12 regression path.
2. Temporary pipeline sanity data such as `real_component_bbox_sample.csv`.
3. Synthetic/generated viewpoint CSVs with different sizes, for example `N=24`, `N=50`, `N=100`, and `N=200`.

The purpose of these inputs is to verify that the simulation environment can accept arbitrary legal viewpoint CSVs and
keep assignment/evaluator interfaces stable.

Do not use temporary or synthetic viewpoint sets as final algorithm-performance benchmarks. They are for interface,
robustness, visualization, evaluator, and smoke validation only.

The final real planned viewpoint CSV should be reserved for later final validation after the simulation-only path is
accepted.

## Core Invariant

The active fixed-N / variable-M invariant should become:

```text
N = number of loaded viewpoints
M = number of enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
```

Avoid hard-coded assumptions such as:

```text
num_agents = 3
range(3)
[num_envs, 3, N + 1]
```

## Proposed Scope

Implement the minimum interface needed for YAML-driven robot configuration:

1. `robots.yaml` schema.
2. Robot config loader.
3. Scenario YAML support for referencing `robots.yaml`.
4. Enabled robot filtering.
5. Robot names and `agent_id` mapping.
6. Initial pose loading.
7. Simple capability/profile fields.
8. Cost weights or speed weights.
9. Evaluator diagnostics for robot config.
10. Smoke tests showing `num_agents` comes from config.

Current robots can still use task-space proxy models. This stage does not require real USD, URDF, IK, collision, or full
motion planning.

## Suggested robots.yaml Schema

Use a minimal schema:

```yaml
robots:
  - name: robot_0
    enabled: true
    model_type: task_space_proxy
    initial_pose_world: [0.0, -1.5, 0.0, 1.0, 0.0, 0.0, 0.0]
    capability_profile: mobile_scanner_a
    speed_weight: 1.0
    cost_weight: 1.0

  - name: robot_1
    enabled: true
    model_type: task_space_proxy
    initial_pose_world: [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    capability_profile: mobile_scanner_b
    speed_weight: 1.0
    cost_weight: 1.0

  - name: robot_2
    enabled: true
    model_type: task_space_proxy
    initial_pose_world: [0.0, 1.5, 0.0, 1.0, 0.0, 0.0, 0.0]
    capability_profile: mobile_scanner_c
    speed_weight: 1.0
    cost_weight: 1.0
```

`initial_pose_world` convention:

```text
[x, y, z, qw, qx, qy, qz]
```

Quaternion convention must be documented as `qwxyz`. If the environment still internally uses yaw-only task-space proxy
state, the MVP loader can initially convert or preserve only the fields currently supported, but it should validate and
store the full schema for future real robot support.

## Suggested File Locations

Candidate config path:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
```

Candidate loader path:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
```

Candidate scenario YAML field:

```yaml
robots:
  config_path: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
```

## Implementation Notes

- The loader should resolve relative paths from the repository root or scenario config path consistently with existing
  scenario/viewpoint config behavior.
- Disabled robots should be removed before constructing agent names, base start poses, scanner offsets, and assignment
  masks.
- Preserve deterministic ordering from the YAML file after filtering `enabled: true`.
- Add clear diagnostics:
  - `robot_config_path`
  - `num_configured_robots`
  - `num_enabled_robots`
  - `enabled_robot_names`
  - `agent_id_by_name`
  - `model_type_by_robot`
  - `capability_profile_by_robot`
  - `speed_weight_by_robot`
  - `cost_weight_by_robot`
  - `initial_pose_world_by_robot`
- Baseline solvers should continue to consume `problem["available_mask"]` and `problem["cost_matrix"]`, now sized by
  enabled robot count `M`.
- The fixed-12 regression path must remain available.

## Verification Plan

The next implementation should eventually verify:

These checks can use fixed/default, temporary, or synthetic viewpoint CSVs. No final real planned viewpoint CSV is
required for this stage. The fixed-12 regression path is mandatory and must remain available.

1. Three enabled robots produce `M=3` and `available_actions shape = [num_envs, 3, N+1]`.
2. Disabling one robot in `robots.yaml` produces `M=2` and `available_actions shape = [num_envs, 2, N+1]`.
3. Adding a fourth task-space proxy robot produces `M=4` and `available_actions shape = [num_envs, 4, N+1]`.
4. `random`, `nearest`, and `greedy` evaluator still run.
5. Fixed-12 regression path remains available.

Suggested smoke outputs:

```text
results/assignment_evaluation/stage_next_robot_config_m3_smoke/
results/assignment_evaluation/stage_next_robot_config_m2_smoke/
results/assignment_evaluation/stage_next_robot_config_m4_smoke/
```

## Simulation Readiness Follow-up

After Robot Config MVP is verified, the next planning target should be a simulation-readiness validation pass.

This follow-up should verify that the system can run with multiple legal viewpoint CSV sizes without requiring the real
planned CSV:

- fixed-12 regression path;
- temporary N=24 bbox-side sample;
- synthetic N=50;
- synthetic N=100;
- synthetic N=200.

The expected output is not a final benchmark conclusion. The expected output is evidence that scenario loading, robot
config loading, available-action shape, assignment masks, baseline evaluator output, assignment history, and basic
visualization remain stable across different `N` and `M`.

## Recommended First Implementation Task

Start with the smallest non-behavioral slice:

1. Add `robot_config.py`.
2. Add `configs/robots/robots_three_proxy.yaml`.
3. Add scenario YAML support for a robot config path.
4. Load and validate enabled robots.
5. Expose robot config diagnostics without changing controller math, reward, or real robot model behavior.
6. Run a config-loader unit/smoke check before touching broader environment shape logic.

After that, wire enabled robot count into the task-space proxy environment and evaluator.

## Future Dynamic Assignment Extension Points

Robot Config MVP should leave clear extension points for the later dynamic assignment stage, but should not implement
them yet.

Future task state candidates:

```text
task_status in {unassigned, assigned, in_progress, completed, failed, unreachable, timeout}
```

Future robot state candidates:

```text
robot_status in {idle, moving, scanning, blocked, failed, disabled}
```

Future assignment problem fields may include:

```text
capability_mask[M, N]
cost_matrix[M, N]
robot_runtime_state[M]
task_runtime_state[N]
```

Robot Config MVP should not implement full dynamic reassignment, retry semantics, controller changes, reward changes, or
assignment-RL training.

## Do Not Do Yet

- Do not train assignment-RL.
- Do not add assignment-RL evaluation.
- Do not modify HARL core.
- Do not change reward.
- Do not change `assignment_controller.py`.
- Do not change controller math.
- Do not add full real robot articulation yet.
- Do not add IK yet.
- Do not add collision yet.
- Do not add joint limits yet.
- Do not add raycast coverage yet.
- Do not wait for the final real planned viewpoint CSV.
- Do not require the final real planned viewpoint CSV for Robot Config MVP.
- Do not use real CSV availability as a blocker for simulation-interface validation.
- Do not treat `real_component_bbox_sample.csv` as final viewpoint planning output.
- Do not tune controller/gate/orientation behavior specifically to temporary or synthetic CSV samples.
- Do not continue deep controller-gate diagnostics on the temporary bbox sample unless explicitly requested.
