# Next Stage Plan: Real Component Proxy, External Viewpoints, Automatic Feasibility

## Overview

The fixed 12-viewpoint assignment-RL MVP is complete enough to move beyond the toy scenario. The next stage should not jump directly to real robot articulation. Instead, it should make the measured object, viewpoint source, and feasibility model more realistic while preserving the current high-level task-space skeleton.

Target next-stage architecture:

```text
real component / component proxy
  + external fixed-N viewpoint file
  + automatic feasibility generator
  -> feasible_mask[num_envs, num_agents, num_viewpoints]
  -> available_mask = feasible_mask & ~covered_mask
  -> existing assignment-controller-env path
```

Important scope:

```text
This is still fixed-N experiment support, not arbitrary / variable viewpoint-count policy generalization.
```

Different viewpoint counts imply:

```text
no-op id = N
action space = Discrete(N + 1)
different policy head size
checkpoint incompatibility across different N
```

## Stage 1: Replace Measured Object With Real Component Proxy

### Goal

Replace the current box component with a real measured component or a simplified component proxy:

```text
current box proxy
  -> real component proxy / measured object proxy
```

### Recommended Proxy Types

Start simple:

```text
bbox
multiple boxes
convex hull
sampled surface proxy
coarse signed-distance / distance-to-surface proxy
```

Avoid starting with full mesh collision or full raycast coverage unless absolutely needed.

### Keep Unchanged Initially

Do not connect real robot articulation yet.

Keep:

```text
high-level task-space scanner/base buffers
existing assignment controller
existing assignment-RL wrapper
existing reward for the first proxy validation
```

### Validation Focus

Validate whether geometry-derived quantities make sense:

```text
surface distance
scanner min/max range
FOV alignment
coverage position gate
coverage rotation gate
coverage target visibility
```

The goal is to prove that the component proxy gives reasonable coverage and feasibility signals before adding robot mechanics.

### Risks

- A proxy that is too simple may accept unrealistic scan poses.
- A proxy that is too detailed may make feasibility/debugging hard too early.
- Surface distance and FOV conventions must match the viewpoint coordinate frame.
- Coverage failures should be debugged geometrically before blaming RL.

## Stage 2: Load Viewpoint Set From External File

### Goal

Move viewpoint definitions out of the environment config:

```text
hard-coded env viewpoint_poses
  -> external viewpoint file
```

### Suggested Formats

CSV with Euler angles:

```text
id,x,y,z,roll,pitch,yaw
```

CSV with quaternion:

```text
id,x,y,z,qw,qx,qy,qz
```

Recommendation:

Use quaternion format internally and allow Euler format only if conversion is explicit and tested.

### Required Conventions

The file loader must document:

```text
coordinate frame
units
quaternion order
Euler angle convention if used
whether poses are local to component, env, or world
whether scanner forward axis is +X as in the current env
```

### Fixed-N Experiment Rule

For each experiment:

```text
N = number of viewpoints loaded from file
no-op id = N
action space = Discrete(N + 1)
available_actions shape = [num_envs, num_agents, N + 1]
assignment shape = [num_envs, num_agents]
```

Do not treat this as arbitrary-N policy generalization.

If `N` changes:

```text
the actor output head changes
the checkpoint is incompatible
training/eval configs must clearly identify N
```

### Minimal Loader Plan

1. Add a config field for viewpoint file path.
2. Load fixed-N viewpoint poses during env initialization.
3. Validate ids are unique and ordered or explicitly remap them.
4. Convert all poses to the internal `[x, y, z, qw, qx, qy, qz]` tensor.
5. Keep `num_viewpoints = len(loaded_viewpoints)`.
6. Print/log viewpoint count and no-op id.
7. Add a reset mask diagnostic for each loaded file.

## Stage 3: Automatic Feasibility Generator

### Goal

Replace fixed scenario manual overrides with automatic feasibility generation:

```python
fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
```

should become:

```text
feasible_mask = feasibility_generator(viewpoints, component_proxy, robot_capabilities)
```

### Inputs

The generator should use at least:

```text
viewpoint pose
component proxy / surface distance
robot sensor min/max range
robot arm reach
FOV constraints
scan position tolerance
scan rotation tolerance
robot capability profile
optional controller feasibility diagnostics
```

Optional later inputs:

```text
collision proxy
base reach region
IK reachability
joint limits
viewpoint normal / incidence angle
occlusion / raycast visibility
```

### Output

The generator should output:

```text
feasible_mask[num_envs, num_agents, num_viewpoints]
available_mask = feasible_mask & ~covered_mask
```

For static component/viewpoint/capability checks, the same base feasible mask can be broadcast across envs.

For state-dependent checks, the mask can include current robot/base/scanner state, but this should be introduced carefully.

### Required Behavior

Every coverage target must be checked:

```text
each viewpoint must be feasible for at least one agent
no coverage target should be permanently unavailable for all agents
```

If a viewpoint has no feasible agent, the generator should fail loudly with a report:

```text
viewpoint id
pose
surface distance
failed agents
failed conditions
```

### Replacing Manual Overrides

The current manual override exists because `robot_2` could not stably cover viewpoint 5 in the fixed MVP.

In the next stage, this should be represented by automatic checks, such as:

```text
controller convergence diagnostic
rotation tolerance feasibility
arm reach margin
sensor range margin
FOV margin
```

Future arbitrary viewpoint files must not depend on viewpoint id hard-coding. Feasibility must come from:

```text
viewpoint pose
component geometry
robot capability
controller/coverage feasibility diagnostics
```

### Suggested Feasibility Report

Generate a small diagnostic table:

```text
viewpoint_id
agent
feasible
surface_distance
range_ok
height_reach_ok
arm_margin
fov_possible
rotation_margin
controller_converged_optional
reason_if_false
```

This report should be available before training.

## Stage 4: Re-Run Baselines and Assignment-RL on Real Component Proxy

### Goal

Evaluate the existing assignment architecture on:

```text
real component proxy
+ external fixed-N viewpoint file
+ automatic feasible_mask
```

### Recommended Order

1. Run reset mask diagnostics.
2. Confirm each viewpoint is feasible for at least one agent.
3. Confirm no coverage target is permanently unavailable.
4. Run `random`, `nearest`, and `greedy` first.
5. Inspect coverage failures before training RL.
6. Train a new assignment-RL checkpoint for that fixed-N viewpoint set.
7. Evaluate with `evaluate_assignment_methods.py` or a minimally extended version.
8. Generate `per_episode.csv` and `summary.csv`.

### Why Baselines First

Baselines validate:

```text
viewpoint file
component proxy
feasible_mask
available_mask
controller path
coverage gates
episode accounting
```

If baselines cannot reach coverage, RL training is unlikely to diagnose the root cause cleanly.

### Assignment-RL Notes

For fixed-N assignment-RL:

```text
N viewpoints
Discrete(N + 1)
no-op id = N
new checkpoint required
old fixed-12 checkpoint is not compatible if N changes
old 9D continuous checkpoints are not compatible with assignment mode
```

Do not mix checkpoints across viewpoint counts.

## Stage 5: Introduce Real Robot Model Later

### Goal

Only after the real component proxy, viewpoint file, and feasibility generator are stable, introduce:

```text
real robot USD
articulation
IK
collision
joint limits
motion control
sensor frame alignment
```

### Why This Comes Last

Real robot integration adds several new failure modes:

```text
IK infeasibility
joint limit violations
robot-component collision
base/arm coordination
sensor frame mismatch
controller tuning
simulation asset issues
low-level actuation delay
```

If this is introduced too early, it becomes difficult to separate:

```text
MRTA / assignment policy problem
vs
viewpoint feasibility problem
vs
geometry/coverage problem
vs
low-level robot control problem
```

Keep the high-level task-space skeleton until the viewpoint and feasibility layers are reliable.

## Near-Term Non-Goals

Do not do these in the immediate next stage:

```text
1. Do not directly enter Phase 6 duplicate avoidance.
2. Do not directly build arbitrary / variable viewpoint-count policy support.
3. Do not directly connect real robot articulation.
4. Do not treat the fixed-12 scenario override as a general capability model.
5. Do not load old 9D continuous checkpoints into assignment mode.
6. Do not modify HARL site-packages.
7. Do not advance mesh, collision, IK, and RL generalization all at once.
```

## Recommended Next Codex Task

Start with Stage 1 and Stage 2 as a design + minimal implementation phase:

```text
real component proxy config
+ external fixed-N viewpoint file loader
+ reset-only diagnostics
```

Suggested first deliverable:

```text
1. Add a sample external viewpoint CSV.
2. Add a config option to load viewpoints from that CSV.
3. Keep fixed-N semantics.
4. Print viewpoint count and no-op id.
5. Run reset-only mask diagnostics.
6. Do not train.
7. Do not add real robot articulation.
```

After that, implement Stage 3 automatic feasibility generation and replace the manual fixed-12 override.
