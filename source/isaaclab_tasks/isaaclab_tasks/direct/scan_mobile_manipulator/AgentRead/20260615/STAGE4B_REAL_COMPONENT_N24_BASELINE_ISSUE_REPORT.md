# Stage 4B Real Component N24 Baseline Issue Report

Date: 2026-06-15

## Scope

This report assesses why the generated real-component fixed-N scenario is not fully covered by the current baseline
methods. It uses the fixed Stage 4A evaluator outputs and does not attempt to fix the behavior.

Important boundary: `real_component_bbox_sample.csv` is generated bbox-side pipeline sanity data. It is useful for
pipeline, baseline, visualization, and diagnostic validation, but it is not final viewpoint planning output and must not
be used as a scientific algorithm-performance conclusion.

## Source Artifacts

Primary fixed evaluator output:

```text
results/assignment_evaluation/stage4a_metrics_real_component_n24_bounded_check/
```

Scenario config:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
```

Viewpoint CSV:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
```

No additional evaluator or simulation run was needed for this report.

## Scenario Summary

```text
scenario_config:
  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml

viewpoint_csv:
  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv

num_viewpoints: 24
noop_id: 24
available_actions_shape: [1, 3, 25]

component_mesh_path:
  E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj

component_proxy_center:
  [-1.1102230246251565e-16, 0.0, 1.1824831542949998]

component_proxy_half_extents:
  [1.8000000267049998, 0.842999997615, 1.1824831542949998]
```

The bbox proxy therefore spans approximately:

```text
x: [-1.800000026705, 1.800000026705]
y: [-0.842999997615, 0.842999997615]
z: [0.0, 2.36496630859]
```

The generated viewpoint CSV samples two height layers around the bbox sides:

```text
low layer z ~= 0.7883221029
high layer z ~= 1.576644206
```

## Baseline Result Summary

From `stage4a_metrics_real_component_n24_bounded_check` with `num_episodes=1`, `max_steps=300`:

| method | final_covered_count | final_coverage | success | steps_to_full_coverage | final uncovered viewpoint ids |
| --- | ---: | ---: | ---: | ---: | --- |
| random | 0 | 0.0 | 0 | -1 | [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23] |
| nearest | 17 | 0.7083333333333334 | 0 | -1 | [1, 2, 8, 12, 13, 14, 20] |
| greedy | 17 | 0.7083333333333334 | 0 | -1 | [1, 2, 8, 12, 13, 14, 20] |

Nearest and greedy produced identical final coverage in this bounded check.

## Uncovered Viewpoint Analysis

Nearest and greedy consistently left these viewpoints uncovered:

```text
[1, 2, 8, 12, 13, 14, 20]
```

CSV poses:

| id | x | y | z | qw | qx | qy | qz | inferred bbox side / region |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 2.600000027 | 0.0 | 0.7883221029 | 0 | 0 | 0 | 1 | +X side, low layer, center-y |
| 2 | 2.600000027 | 0.8429999976 | 0.7883221029 | 0 | 0 | 0 | 1 | +X side, low layer, +Y edge |
| 8 | 1.800000027 | 1.642999998 | 0.7883221029 | 0.7071067812 | 0 | 0 | -0.7071067812 | +Y side, low layer, +X edge |
| 12 | 2.600000027 | -0.8429999976 | 1.576644206 | 0 | 0 | 0 | 1 | +X side, high layer, -Y edge |
| 13 | 2.600000027 | 0.0 | 1.576644206 | 0 | 0 | 0 | 1 | +X side, high layer, center-y |
| 14 | 2.600000027 | 0.8429999976 | 1.576644206 | 0 | 0 | 0 | 1 | +X side, high layer, +Y edge |
| 20 | 1.800000027 | 1.642999998 | 1.576644206 | 0.7071067812 | 0 | 0 | -0.7071067812 | +Y side, high layer, +X edge |

Pattern:

- The uncovered set is concentrated on the positive-X face and the positive-Y face near the positive-X edge.
- All high-layer positive-X viewpoints are uncovered: 12, 13, 14.
- The positive-Y side fails at the positive-X edge for both height layers: 8 and 20.
- The negative-X side and negative-Y side are covered by nearest/greedy in this bounded check.

Feasibility:

- Static/final feasibility diagnostics report all seven uncovered viewpoints as feasible for all three agents.
- `permanently_unavailable_viewpoints=[]`.
- `manual_feasibility_override_rows=[]` for this external N=24 scenario.
- `infeasible_rows=[]`.

Interpretation:

The baseline failure is not explained by the static feasibility mask. The current static feasibility layer is optimistic
for these poses, or the baseline/controller sequence is unable to convert feasible targets into coverage under the current
controller and coverage gates.

## Assignment vs Coverage Distinction

The fixed evaluator output records final covered and uncovered viewpoint ids, but it does not yet record assignment
history per step.

Therefore, the current artifacts cannot determine whether each uncovered viewpoint was:

- never assigned by nearest/greedy, or
- assigned one or more times but not covered, or
- repeatedly selected in a way that stalled progress because the controller could not satisfy the scan gates.

Evidence available now:

- `new_viewpoints_total=17` for nearest/greedy.
- `final_covered_count=17` for nearest/greedy.
- Final uncovered ids are `[1, 2, 8, 12, 13, 14, 20]`.

Evidence missing:

- per-step assignment tensor;
- per-step selected viewpoint ids per agent;
- per-step selected-valid mask;
- per-step coverage gain by viewpoint id;
- per-viewpoint assignment attempts and first/last attempt step.

Recommendation: add evaluator assignment-history diagnostics before making a final causal claim about whether the issue is
assignment selection or controller/coverage execution.

## Hypotheses

### 1. Viewpoint Pose / Generator Issue

The uncovered viewpoints cluster on generated bbox-side poses around the positive-X side and positive-X/+Y edge. The
generated CSV may include poses that are geometrically valid in the coarse bbox generator but awkward for the current
task-space controller and scanner coverage gates.

### 2. Controller Cannot Satisfy Gates for Those Poses

The scan controller may not be able to bring the scanner position and orientation inside the required tolerances for the
uncovered positive-X/high-layer viewpoints within the bounded episode. This is plausible because static feasibility is not
a Level 2 controller convergence proof.

### 3. Coverage Gate Too Strict

The current coverage condition depends on simultaneous position, rotation, reach, sensor range, and FOV gates. A viewpoint
can be statically feasible but never count as covered if one gate remains slightly outside tolerance.

### 4. Nearest/Greedy Lacks Retry / Failure Handling

Nearest and greedy use the available mask, but they do not track failed attempts, retry budgets, or alternative-agent
fallbacks. If a target remains uncovered after being assigned, a deterministic baseline may keep selecting locally
attractive but hard-to-cover viewpoints.

### 5. Static Feasibility Too Optimistic

Static feasibility reports all seven uncovered viewpoints as feasible for all agents and reports no permanently
unavailable viewpoints. The observed coverage failure suggests static feasibility is only a necessary pre-check, not a
sufficient condition for controller-level coverage.

### 6. Episode Limit or Task Sequencing Issue

The bounded check used `max_steps=300` and ended with nearest/greedy at `17/24`. It is possible that additional steps,
different ordering, or retry-aware sequencing could cover more viewpoints. However, the current evidence does not prove
that because assignment history is not logged.

## Recommended Next Diagnostic Step

Primary recommendation: add evaluator assignment-history logging for bounded diagnostic runs.

Justification:

- The current report can identify which viewpoints remain uncovered, but cannot say whether they were never assigned or
  assigned but failed to satisfy coverage.
- Assignment-history logging is the smallest missing diagnostic layer and does not require changing HARL core, reward,
  `assignment_controller.py`, or the 9D action path.
- Once assignment history is available, the next diagnostic can be targeted:
  - if the seven viewpoints are assigned but not covered, run Level 2 controller diagnostics on those viewpoint-agent
    pairs;
  - if they are never assigned, inspect nearest/greedy sequencing and available-mask evolution;
  - if they are assigned repeatedly without progress, add retry/failure diagnostics before any algorithmic changes.

Suggested fields for a future diagnostics JSON or CSV:

```text
step
method
env_id
agent_id
assigned_viewpoint_id
selected_available
covered_before
covered_after
newly_covered_viewpoint_ids
coverage_count
coverage_ratio
```

Secondary recommendation after assignment history exists: run bounded Level 2 controller diagnostics for the uncovered
viewpoints `[1, 2, 8, 12, 13, 14, 20]`, especially positive-X high-layer ids `[12, 13, 14]`.

## Do Not Conclude Yet

Do not interpret this generated N=24 CSV as final algorithm performance data. The current conclusion is narrower:

```text
The Stage 4A fixed evaluator is now metric-consistent, and on the temporary generated real-component N=24 smoke CSV,
nearest/greedy cover 17/24 viewpoints in the bounded diagnostic run. The uncovered viewpoints are feasible according to
static geometry but require assignment-history and likely Level 2 controller diagnostics before a causal fix is chosen.
```
