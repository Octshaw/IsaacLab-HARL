# Next Stage Plan: Algorithm Scenario Decoupling and Proxy Constraint MVP

## 1. Purpose

This plan defines the next stage after Phase 7A YAML Capability Profiles MVP.

The project has already completed:

* CSV-based viewpoint input.
* YAML-based robot configuration.
* YAML-based robot capability profiles.
* Visual-only real robot mesh spawning and proxy-following.
* Real-scene proxy smoke validation.
* Conservative task and robot status interface fields.

The next goal is to prepare a clean algorithm-testing path before modifying the core task allocation logic.

The immediate priority is:

```text
Separate algorithm evaluation scenarios from visual demonstration scenarios.
```

Then the project can safely add:

```text
obstacle-aware path cost
robot footprint constraints
inter-robot separation
dynamic task lifecycle states
```

without mixing visual-only assets, large OBJ loading, GUI inspection, and algorithm evaluation.

---

## 2. Current State

The current system has these configurable inputs:

```text
Viewpoints:
  CSV input is supported.

Robots:
  robots YAML controls enabled robots, initial poses, profile names, visual metadata.

Robot capabilities:
  capability YAML controls scanner offsets, reach, range, FOV, tolerances, and step sizes.

Scene visual assets:
  component OBJ and robot OBJ can be used for visual-only scene inspection.

Assignment interface:
  available_actions
  available_mask
  cost_matrix
  task_status
  robot_status
```

The current real-scene visual path is useful for GUI inspection and demo videos, but it should not be used as the default algorithm evaluation path because it may load large visual assets.

---

## 3. Design Principle

The project should keep two scenario families:

```text
Algorithm scenarios:
  lightweight
  no large robot OBJ
  no real visual mesh dependency
  uses simple robot markers / proxy bbox
  uses component proxy bbox
  used for smoke, baseline comparison, training, and algorithm evaluation

Visual scenarios:
  may load component OBJ
  may load robot OBJ
  used for GUI inspection, screenshots, videos, and presentation
  not used as final algorithm benchmark
```

This keeps algorithm development focused on:

```text
dynamic task allocation
load balancing
path cost
robot state changes
task state updates
```

instead of being blocked by visual asset size, rendering, GUI behavior, or real robot mesh details.

---

## 4. Stage Overview

Recommended next stages:

```text
Phase 7A-2: Algorithm Scenario Decoupling
Phase 7B: Obstacle-Aware Proxy Path Cost MVP
Phase 7C: Inter-Robot Separation / Conflict MVP
Phase 7D: Lifecycle-Backed Dynamic Assignment State MVP
```

The immediate next implementation should be Phase 7A-2.

---

# Phase 7A-2: Algorithm Scenario Decoupling

## 5. Goal

Create a lightweight algorithm-testing scenario that does not load large real visual assets.

The scenario should still use:

```text
robots_real_proxy.yaml
mobile_scanner_profiles.yaml
synthetic or fixed viewpoint CSV
component bbox proxy
task-space proxy robots
```

but should not load:

```text
ScanRobot.obj
real robot visual mesh
large component visual mesh
GUI-only visual assets
```

## 6. Required Scenario Split

Add or formalize two scenario types.

### 6.1 Algorithm Scenario

Suggested file:

```text
configs/scenarios/algorithm_proxy_bbox.yaml
```

Expected behavior:

```text
component_proxy_type: bbox
component_proxy_visual_visible: true or false
component_mesh_path: null
robot visual mesh disabled
robot debug markers enabled
viewpoint CSV enabled
capability YAML enabled
```

Purpose:

```text
baseline solver testing
future obstacle-aware cost testing
future dynamic assignment testing
lightweight smoke validation
eventual RL training/evaluation
```

### 6.2 Visual Demo Scenario

Existing or future visual scenario:

```text
configs/scenarios/real_scene_proxy_headless.yaml
```

or a GUI-local copy.

Expected behavior:

```text
component visual OBJ may be loaded
robot ScanRobot.obj may be loaded
visual mesh follows proxy pose
used for GUI inspection and demo output
```

Purpose:

```text
visual sanity check
PPT screenshots
video recording
human inspection
```

It should not be used as the primary algorithm benchmark.

---

## 7. Visual Asset Control

Add one simple control mechanism so algorithm scenarios can disable robot mesh visuals without modifying robot YAML each time.

Possible design:

```yaml
visualization:
  robot_visual_mode: debug_marker
  component_visual_mode: bbox
```

Recommended initial values:

```yaml
visualization:
  robot_visual_mode: debug_marker   # debug_marker / mesh / none
  component_visual_mode: bbox       # bbox / mesh / none
```

Minimum acceptable alternative:

```yaml
enable_robot_visual_mesh: false
```

For Phase 7A-2, prefer the smallest safe change.

## 8. Expected Algorithm Scenario Diagnostics

Wrapper/evaluator diagnostics should clearly report:

```text
scenario_type: algorithm_proxy_bbox
robot_visual_mesh_enabled: false
component_mesh_enabled: false
component_proxy_type: bbox
robot_config_path
capability_config_path
viewpoint_source
N
M
noop_id
available_actions_shape
available_mask_shape
cost_matrix_shape
task_status_shape
robot_status_shape
```

If robot mesh visual is disabled, diagnostics should not report this as an error.

---

## 9. Phase 7A-2 Validation

Minimum smoke checks:

```text
algorithm_proxy_bbox.yaml wrapper smoke
algorithm_proxy_bbox.yaml evaluator smoke with random / nearest / greedy
real_scene_proxy_headless.yaml smoke still passes
```

Expected algorithm scenario shape:

```text
N = loaded viewpoints
M = enabled robots
noop_id = N
available_actions = [1, M, N + 1]
available_mask = [1, M, N]
cost_matrix = [1, M, N]
task_status = [1, N]
robot_status = [1, M]
```

For the current synthetic N=50 and M=3 setup:

```text
available_actions = [1, 3, 51]
available_mask = [1, 3, 50]
cost_matrix = [1, 3, 50]
task_status = [1, 50]
robot_status = [1, 3]
```

---

# Phase 7B: Obstacle-Aware Proxy Path Cost MVP

## 10. Goal

Prevent the assignment layer from treating paths that pass through the component as cheap straight-line paths.

This phase should not add real physics collision.

It should add algorithm-level proxy obstacle awareness.

## 11. Component Obstacle Proxy

Use the existing component bbox proxy as the first obstacle model:

```text
component_proxy_center
component_proxy_half_extents
component_proxy_padding
```

Treat this bbox as a static obstacle for path-cost diagnostics.

## 12. Robot Footprint Proxy

Add simple robot footprint parameters.

Possible fields:

```yaml
base_footprint_radius: 0.4
path_safety_margin: 0.2
```

These may belong in:

```text
capability profile YAML
```

or a separate obstacle/path-cost config.

Recommended first step:

```text
add obstacle/path-cost config separately
```

to avoid mixing scanning capability with navigation constraints too early.

## 13. Interface Fields to Add First

Do not immediately replace `cost_matrix`.

Add new fields first:

```text
straight_line_cost_matrix: [num_envs, M, N]
obstacle_intersection_mask: [num_envs, M, N]
obstacle_penalty_matrix: [num_envs, M, N]
obstacle_aware_cost_matrix: [num_envs, M, N]
```

Keep existing:

```text
cost_matrix
available_mask
feasible_mask
```

unchanged in Phase 7B-1.

## 14. Cost Logic MVP

Initial logic:

```text
straight_line_cost = Euclidean distance from robot/scanner/base to viewpoint

if line segment intersects component bbox expanded by safety margin:
    obstacle_penalty = configured penalty
else:
    obstacle_penalty = 0

obstacle_aware_cost = straight_line_cost + obstacle_penalty
```

Do not add A*, RRT, true path planning, physics collision, or mesh collision in this phase.

## 15. Optional Future Cost Mode

After diagnostics are validated, add a config switch:

```yaml
assignment_cost:
  mode: euclidean        # euclidean / obstacle_aware
  obstacle_penalty: 100.0
  mask_blocked_paths: false
```

Initial default should remain:

```yaml
mode: euclidean
```

This preserves baseline behavior.

---

# Phase 7C: Inter-Robot Separation / Conflict MVP

## 16. Goal

Reduce obvious robot overlap and target crowding without adding full multi-robot motion planning.

This phase should remain algorithm-level and proxy-based.

## 17. Initial Constraints

Add diagnostics first:

```text
inter_robot_distance_matrix: [num_envs, M, M]
min_robot_separation_violation: [num_envs, M]
target_proximity_conflict_mask: [num_envs, M, N]
inter_robot_conflict_penalty_matrix: [num_envs, M, N]
```

Initial behavior should be diagnostics-only.

## 18. Recommended Constraints

Start with:

```text
minimum distance between robot bases
minimum distance between simultaneously assigned target viewpoints
penalty for selecting targets too close to another robot's current/assigned target
```

Do not implement continuous-time path crossing avoidance yet.

---

# Phase 7D: Lifecycle-Backed Dynamic Assignment State MVP

## 19. Goal

Start filling the reserved status enums with real lifecycle meaning.

Current conservative behavior:

```text
viewpoints_covered == true  -> completed
viewpoints_covered == false -> unassigned
active robot rows           -> idle
```

Future behavior should add:

```text
TASK_ASSIGNED
TASK_IN_PROGRESS
ROBOT_MOVING
ROBOT_SCANNING
```

## 20. Runtime State Fields

Add optional fields only after ownership signals are reliable:

```text
task_runtime_state
robot_runtime_state
assigned_robot_id
current_task_id
remaining_distance
elapsed_on_task
retry_count
```

Do not add full reassignment policy until lifecycle states are stable.

---

## 21. Non-Goals

The next stages should not include:

```text
real robot articulation
IK
joint limits
mesh collision
PhysX robot collision
raycast coverage
reward redesign
controller redesign
HARL core changes
assignment-RL training
final real CSV validation
```

Temporary and synthetic CSVs remain interface validation data only.

---

## 22. Recommended Immediate Next Task

Implement:

```text
Phase 7A-2: Algorithm Scenario Decoupling
```

Before obstacle-aware cost.

Reason:

```text
Algorithm tests should run in a lightweight proxy/bbox scenario without loading ScanRobot.obj or large visual meshes.
```

After Phase 7A-2 passes, implement:

```text
Phase 7B-1: Obstacle-Aware Path-Cost Diagnostics
```

with additional fields only, keeping solver/reward/controller behavior unchanged.

---

## 23. Acceptance Criteria for Phase 7A-2

Phase 7A-2 is complete when:

```text
algorithm_proxy_bbox.yaml exists
algorithm_proxy_bbox.yaml does not load ScanRobot.obj
algorithm_proxy_bbox.yaml uses bbox component proxy
wrapper smoke passes
evaluator smoke passes with random / nearest / greedy
real visual scenario still passes or remains unchanged
diagnostics clearly distinguish algorithm vs visual scenario
TASK_PROGRESS.md is updated
```

Expected final statement:

```text
Algorithm evaluation can now proceed without real visual mesh loading, while visual demo scenarios remain available for GUI inspection and videos.
```
