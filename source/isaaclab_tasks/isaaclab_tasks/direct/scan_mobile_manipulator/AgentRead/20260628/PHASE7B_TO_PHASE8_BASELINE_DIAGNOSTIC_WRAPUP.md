# Phase 7B To Phase 8 Baseline Diagnostic Wrap-Up

Date: 2026-06-28

## Scope

This document closes the Phase 7B through Phase 8 diagnostic/baseline branch and prepares the project for a separate
Phase 9A RL/dynamic-policy readiness check.

The project goal remains:

```text
Given arbitrary-size viewpoint sets and variable robot numbers, implement dynamic multi-robot task allocation.
```

Viewpoints may come from CAD/model-based coverage view planning, manual design, or other upstream sources. The current
core contribution focus is dynamic assignment, load balancing, path cost, robot state changes, and task state updates.
Viewpoint generation, ROI importance modeling, model-free NBV, and full physical collision or low-level path planning
are not the main contribution in the current path.

## Phase Timeline

### Phase 7B / 7B-4A

Obstacle diagnostics and selected-assignment visualization were clarified:

- Mesh-footprint obstacle diagnostics are diagnostic-only.
- `mesh_footprint_aware_cost_matrix` is not used by live solvers.
- Selected assignment lines are direct `robot base XY -> selected viewpoint XY` diagnostics.
- Green `SelectedAssignment_*` lines are not planned robot trajectories.
- The component bbox remains metadata/debug only and is not used as hard obstacle blocking.

### Phase 7C

Inter-robot proxy conflict diagnostics were added:

- `inter_robot_overlap` metrics report proxy base footprint overlap.
- `selected_target_conflict` metrics report selected viewpoint XY proximity between robots.
- No physical collision, local avoidance, robot blocking, or solver behavior change was added.

### Phase 7D-1

Selected-target conflict-aware candidate comparison was added:

- The candidate comparison is diagnostic-only.
- The baseline assignment is executed unchanged.
- The candidate slightly reduced selected-target conflicts in the 300-step nearest/greedy runs.
- It did not resolve the late-stage clustered target pattern.

### Phase 7D-2

Conflict-aware ablation baselines were added:

```text
greedy_conflict_aware
nearest_conflict_aware
```

These methods use a top-K joint selected-target conflict score. The original `random`, `nearest`, and `greedy` methods
remain unchanged. The ablation baselines reduced selected-target and inter-robot conflict modestly, but did not improve
coverage and did not fix the final clustered target pattern.

### Phase 7E

Actual proxy base-motion crossing diagnostics were added:

```text
previous robot base XY -> current robot base XY
```

This is distinct from:

```text
selected assignment line:
  current robot base XY -> selected viewpoint XY

selected-target conflict:
  distance between selected target viewpoint XY positions
```

Phase 7E detected actual proxy base-motion component-footprint crossings. Conflict-aware variants increased this
crossing metric relative to nearest/greedy. The metric is diagnostic-only and approximate XY-only.

### Phase 8

Real-component proxy baseline validation evaluated:

```text
random
nearest
greedy
nearest_conflict_aware
greedy_conflict_aware
```

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Viewpoint source:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv
```

The run used N=50, M=3, 10 episodes, and 300 steps. This is proxy validation data, not final benchmark evidence.

## Diagnostics Now Available

The current evaluation pipeline can report:

- coverage, coverage AUC, success, final covered/uncovered viewpoints;
- selected assignment line diagnostics;
- mesh-footprint selected-intersection diagnostics;
- obstacle-aware copied-problem candidate comparison;
- selected-target conflict metrics;
- inter-robot proxy overlap metrics;
- conflict-aware baseline solver diagnostics;
- actual proxy base-motion component-footprint crossing metrics;
- assignment history with compact actual base-motion crossing columns.

These diagnostics are not physical collision, not planned paths, and not live solver masks or costs unless explicitly
stated otherwise.

## Baseline Variants Now Available

Primary baselines:

```text
random
nearest
greedy
```

Ablation baselines:

```text
nearest_conflict_aware
greedy_conflict_aware
```

The ablation baselines should be labeled as such in future tables. They are useful evidence but not final collision or
conflict-avoidance policies.

## Final Phase 8 Result Table

| method | success rate | final coverage | coverage AUC | selected-target conflict rate | inter-robot overlap rate | actual base-motion crossing rate |
|---|---:|---:|---:|---:|---:|---:|
| random | 0.0 | 0.004 | 0.0038 | 0.4157 | 0.6759 | 0.9050 |
| nearest | 0.0 | 0.900 | 0.7468 | 0.7191 | 0.6689 | 0.0167 |
| greedy | 0.0 | 0.900 | 0.7468 | 0.7191 | 0.6689 | 0.0167 |
| nearest_conflict_aware | 0.0 | 0.900 | 0.7468 | 0.6622 | 0.5753 | 0.1237 |
| greedy_conflict_aware | 0.0 | 0.900 | 0.7468 | 0.6622 | 0.5753 | 0.1237 |

Stagnation:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
late repeated assignments:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
```

## Main Interpretation

Nearest, greedy, and the conflict-aware ablations all reached 45/50 coverage but did not reach full success. They
plateaued after the last coverage gain around step 116 and repeated the same late assignments for the remaining
episode horizon.

Conflict-aware ablations improved one set of diagnostics:

```text
selected_target_conflict_rate: 0.7191 -> 0.6622
inter_robot_overlap_rate: 0.6689 -> 0.5753
```

But they worsened another important proxy-execution diagnostic:

```text
actual_base_motion_intersection_rate: 0.0167 -> 0.1237
```

They did not improve final coverage, coverage AUC, full-coverage success, worst clearance, or the late repeated target
pattern.

## Why Not Add More Handcrafted Baseline Rules Now

The Phase 7D/8 evidence shows that a handcrafted rule can improve a narrow metric while worsening another. The
conflict-aware ablations reduced selected-target and overlap diagnostics, but increased actual base-motion component
crossing and did not improve coverage. Adding more hard-coded rules risks chasing local metrics without addressing the
core dynamic assignment problem.

The next productive step is to audit RL/dynamic-policy readiness:

- confirm the interface supports N=50 and M=3;
- check whether observations contain enough state for dynamic assignment;
- check whether masks/rewards expose or hide the relevant failure modes;
- define metrics to compare RL against the Phase 8 baseline table.

## How This Motivates RL / Dynamic Policy Work

The Phase 8 plateau is consistent with dynamic assignment limitations:

- static feasibility is not enough;
- late-stage repeated assignment persists;
- no-progress state matters;
- conflict and crossing diagnostics reveal trade-offs rather than a single obvious rule;
- load balance and robot/task runtime state likely need to be part of policy reasoning.

Phase 9A should therefore audit readiness before evaluation or training. It should not start RL training directly.

## Known Limitations

- N=50 `component_mesh_jittered_n50.csv` is proxy validation data, not final benchmark evidence.
- Actual base-motion crossing is approximate XY-only and not full 3D collision checking.
- Selected assignment lines are diagnostic segments, not planned robot paths.
- Conflict-aware ablations are not collision-avoidance or path-planning methods.
- `per_robot_completed_count` and direct load-balance completion metrics are not yet reported.
- No RL evaluation has been run in this branch.

## Next Document

Proceed to:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
```

Do not start RL evaluation or training before Phase 9A readiness checks are completed.
