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

## Stage 0: Freeze Fixed-12 MVP Regression Baseline

### Purpose

Keep the current fixed-12 assignment-RL MVP as a regression test.

Before and after major next-stage changes, verify that the original fixed-12 path still works. Do not delete, overwrite, or silently replace the fixed-12 scenario until the real-component scenario is stable.

### Reference Behavior

The current fixed-12 reference behavior is:

```text
assignment_rl success_rate = 1.0
assignment_rl mean_steps_to_full_coverage ~= 118
nearest / greedy mean_steps_to_full_coverage ~= 126
assignment_rl mean_final_coverage = 1.0
```

These values are not a formal benchmark for all future scenarios. They are a practical regression reference for the current fixed-12 MVP.

### Suggested Checks

Before and after major changes, run bounded checks that confirm:

```text
baseline-only evaluator smoke
assignment-RL checkpoint eval smoke
reset available_actions shape check
fixed-12 feasible_mask sanity check
```

The important point is to preserve the existing assignment-controller-env path while adding new scenario inputs.

## Stage 1: Replace Measured Object With Real Component Proxy

### Goal

Replace the current box component with a real measured component or a simplified component proxy:

```text
current box proxy
  -> real component proxy / measured object proxy
```

### First Implementation Boundary

The first implementation should be minimal.

Do not support all proxy types at once. Do not introduce mesh raycast, IK, collision, or real articulation in the first implementation.

Recommended minimum:

```text
component_proxy_type = bbox
component_proxy_center
component_proxy_half_extents
```

This is enough to validate config plumbing, geometry conventions, distance checks, and reset diagnostics without mixing in mesh, collision, or real robot mechanics.

### Recommended Proxy Types

Start with:

```text
bbox
```

Extend later in this order if needed:

```text
multi_box
sampled_surface_points
convex hull
mesh/raycast
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

The goal is not to make the robot physically realistic in Stage 1. The goal is to make the measured component representation configurable and geometrically inspectable.

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

The file loader must document and validate:

```text
pose_type:
  scanner_pose_in_world
  scanner_pose_in_component_frame

coordinate_frame:
  world
  component_local

units:
  meters
  radians or degrees

quaternion_order:
  qw,qx,qy,qz

euler_convention:
  roll,pitch,yaw
  intrinsic/extrinsic convention if Euler is supported

scanner_forward_axis:
  e.g. +X or another explicitly documented axis

scanner_up_axis:
  explicitly documented axis

viewpoint quaternion meaning:
  scanner frame orientation
  not object target orientation unless explicitly stated
```

The loader must not silently guess frame or quaternion conventions.

Invalid or ambiguous viewpoint files should fail with a clear error before environment reset or training starts.

### Minimal Loader Boundary

The first implementation should be minimal.

Do not support every viewpoint format at once. Do not introduce mesh raycast, IK, collision, or real articulation in the first loader implementation.

Recommended minimum:

```text
one CSV format
one explicit frame convention
one explicit pose_type
quaternion format preferred
fixed-N only
reset-only diagnostics
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

### Level 1: Static Geometric Feasibility

Start with Level 1 only.

Inputs:

```text
viewpoint pose
component proxy / surface distance
robot sensor min/max range
arm reach
rough FOV / normal alignment
height/workspace bounds
scan tolerance margins if available
```

Outputs:

```text
feasible_mask[num_envs, num_agents, num_viewpoints]
diagnostic table with reason_if_false
```

The Level 1 generator should be deterministic, reset-safe, and inspectable before training. It should explain every `False` entry rather than only returning a mask.

### Level 2: Controller Feasibility Diagnostic

Level 2 is optional and should not be mandatory in the first implementation.

Inputs:

```text
candidate robot-viewpoint pairs from Level 1
bounded rollout or controller convergence check
pos_error / rot_error / range gate over time
```

Outputs:

```text
optional refined feasible_mask
convergence report
cached feasibility result if needed
```

Use Level 2 when static geometry is not enough to explain persistent coverage failures. Do not make Level 2 part of the first implementation gate.

Recommended first step:

```text
Level 1 static feasibility
reset-only diagnostics
no controller rollout requirement
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

## Scenario Config Entrypoint

Future real-component experiments should be controlled by a scenario config rather than scattering component, viewpoint, robot capability, and feasibility parameters directly inside env code.

Example:

```yaml
scenario_name: real_component_fixedN_v1

component:
  proxy_type: bbox
  center: [0.0, 0.0, 1.0]
  half_extents: [3.0, 1.0, 1.0]

viewpoints:
  file: configs/viewpoints/real_component_v1.csv
  format: qwxyz_quat
  frame: world
  pose_type: scanner_pose_in_world
  fixed_n: true

robots:
  capability_file: configs/robots/scan_robot_capabilities.yaml

feasibility:
  generator: static_geometric_v1
  require_each_viewpoint_feasible: true
```

Purpose:

```text
avoid scattering component/viewpoint/robot capability parameters directly inside env code
make future experiments reproducible
make fixed-N scenario identity explicit
make checkpoint compatibility easier to reason about
```

The scenario config should make it obvious when two runs use different viewpoint counts, component proxies, or feasibility rules.

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

Implement minimal Stage 1 + Stage 2 support:

```text
Keep fixed-12 default scenario working.
Add bbox component proxy config entrypoint.
Add external fixed-N viewpoint CSV loader.
Add one sample viewpoint CSV.
Print loaded num_viewpoints and no-op id.
Validate viewpoint file frame/quaternion conventions.
Add reset-only diagnostics:
  - viewpoint ids
  - available_actions shape
  - feasible agents per viewpoint
  - permanently unavailable viewpoints
Do not train.
Do not change RL wrapper.
Do not change HARL.
Do not add real robot articulation.
Do not implement arbitrary-N policy generalization.
```

Suggested first deliverable:

```text
1. Preserve the fixed-12 default path and regression checks.
2. Add a minimal bbox component proxy config.
3. Add one explicit fixed-N viewpoint CSV format.
4. Add one sample viewpoint CSV.
5. Print loaded viewpoint count and no-op id.
6. Validate frame, pose_type, units, and quaternion convention.
7. Run reset-only mask diagnostics.
8. Do not train.
9. Do not add real robot articulation.
10. Do not implement Phase 6 duplicate avoidance.
```

After that, implement Stage 3 automatic feasibility generation and replace the manual fixed-12 override.
