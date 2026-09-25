# Stage 4B Real Component N24 Uncovered Level 2 Report

Date: 2026-06-15

## Scope

This is a diagnostic report only. It does not change the controller, reward, random / nearest / greedy baselines, HARL
core, assignment-RL, the 9D action path, robot articulation, IK, collision, or raycast coverage.

The generated `real_component_bbox_sample.csv` is still temporary pipeline sanity / smoke data. The results below should
not be treated as final scientific performance for viewpoint planning or assignment methods.

## Source Artifacts

Scenario config:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
```

Level 2 JSON:

```text
results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json
```

Diagnostic command:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\diagnose_assignment_controller_feasibility.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --viewpoint_ids 1 2 8 12 13 14 20 --agent_ids 0 1 2 --max_steps 320 --output_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json
```

## Scenario Summary

```text
num_viewpoints: 24
noop_id: 24
available_actions_shape: [1, 3, 25]
target_viewpoint_ids: [1, 2, 8, 12, 13, 14, 20]
target_agent_ids: [0, 1, 2]
max_steps_per_pair: 320
stop_on_covered: true
```

Viewpoint CSV:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
```

Component mesh:

```text
E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj
```

Component proxy:

```text
center: [-1.1102230246251565e-16, 0.0, 1.1824831542949998]
half_extents: [1.8000000267049998, 0.842999997615, 1.1824831542949998]
```

## Pair-Level Results

Each row forced exactly one agent-viewpoint pair through the existing assignment wrapper/controller path. Other agents
were noop.

| viewpoint | agent | covered | first covered step | controller converged | gates observed | best pos err | best rot err | best range margin | reason |
|---:|---|---:|---:|---:|---|---:|---:|---:|---|
| 1 | robot_0 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.038535 | 0.555707 | position_rotation_gates_never_simultaneously_satisfied |
| 1 | robot_1 | true | 32 | true | all coverage gates true | 0.230001 | 0.012361 | 0.804561 | covered |
| 1 | robot_2 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.179076 | 0.300000 | position_rotation_gates_never_simultaneously_satisfied |
| 2 | robot_0 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.038535 | 0.555707 | position_rotation_gates_never_simultaneously_satisfied |
| 2 | robot_1 | true | 25 | true | all coverage gates true | 0.017001 | 0.541593 | 0.804561 | covered |
| 2 | robot_2 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.179076 | 0.300000 | position_rotation_gates_never_simultaneously_satisfied |
| 8 | robot_0 | true | 70 | true | all coverage gates true | 0.130000 | 0.000000 | 0.555707 | covered |
| 8 | robot_1 | true | 14 | true | all coverage gates true | 0.207001 | 0.070796 | 0.812999 | covered |
| 8 | robot_2 | true | 89 | true | all coverage gates true | 0.143002 | 0.000000 | 0.449963 | covered |
| 12 | robot_0 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.038535 | 0.555707 | position_rotation_gates_never_simultaneously_satisfied |
| 12 | robot_1 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.012361 | 0.804561 | position_rotation_gates_never_simultaneously_satisfied |
| 12 | robot_2 | true | 45 | true | all coverage gates true | 0.000000 | 0.381668 | 0.300000 | covered |
| 13 | robot_0 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.038535 | 0.555707 | position_rotation_gates_never_simultaneously_satisfied |
| 13 | robot_1 | true | 32 | true | all coverage gates true | 0.230001 | 0.012361 | 0.804561 | covered |
| 13 | robot_2 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.179076 | 0.300000 | position_rotation_gates_never_simultaneously_satisfied |
| 14 | robot_0 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.038535 | 0.555707 | position_rotation_gates_never_simultaneously_satisfied |
| 14 | robot_1 | true | 25 | true | all coverage gates true | 0.017001 | 0.541593 | 0.804561 | covered |
| 14 | robot_2 | false | null | false | pos/rot/range/fov individually true, pos+rot simultaneous false | 0.000000 | 0.179076 | 0.300000 | position_rotation_gates_never_simultaneously_satisfied |
| 20 | robot_0 | true | 70 | true | all coverage gates true | 0.130000 | 0.000000 | 0.555707 | covered |
| 20 | robot_1 | true | 14 | true | all coverage gates true | 0.207001 | 0.070796 | 0.812999 | covered |
| 20 | robot_2 | true | 88 | true | all coverage gates true | 0.114369 | 0.000000 | 0.435631 | covered |

## Viewpoint-Level Coverability

| viewpoint | Level 2 covering agents | interpretation |
|---:|---|---|
| 1 | robot_1 | coverable by at least one robot |
| 2 | robot_1 | coverable by at least one robot |
| 8 | robot_0, robot_1, robot_2 | coverable by all robots |
| 12 | robot_2 | coverable by at least one robot |
| 13 | robot_1 | coverable by at least one robot |
| 14 | robot_1 | coverable by at least one robot |
| 20 | robot_0, robot_1, robot_2 | coverable by all robots |

All seven previously uncovered viewpoints are coverable by at least one robot under the current controller and coverage
gates. Under the requested interpretation rule, this points to baseline assignment / retry / history diagnostics as the
next thing to inspect, rather than declaring these viewpoints globally unreachable.

## Failure Mode Analysis

The failing pairs are not failing because range or FOV was never satisfied. In all failing pairs:

```text
ever_position_gate_ok = true
ever_rotation_gate_ok = true
ever_range_ok = true
ever_fov_alignment_ok = true
ever_position_rotation_gate_ok = false
ever_all_coverage_gates_ok = false
```

This means position and rotation gates are individually reached, but not at the same step. This resembles the earlier
fixed-12 `robot_2 -> viewpoint_5` issue: the controller can visit the right ingredients over time, but the coverage gate
requires them to be simultaneously true.

The agent-specific subset is strong:

```text
robot_0 covers: [8, 20]
robot_1 covers: [1, 2, 8, 13, 14, 20]
robot_2 covers: [8, 12, 20]
```

So static feasibility is not too optimistic at the viewpoint level for these seven ids, because every viewpoint has at
least one successful agent. It is too optimistic at the agent-viewpoint pair level, because static feasibility reported
all target pairs feasible while Level 2 failed several pairs within the 320-step diagnostic horizon.

## Report Questions

1. Can each uncovered viewpoint be covered by at least one robot under current controller/gates?

Yes. All target viewpoints `[1, 2, 8, 12, 13, 14, 20]` have at least one successful Level 2 agent.

2. Are failures caused by range, position, rotation, FOV, simultaneous gate timing, or horizon/step limit?

The direct observed failure mode is simultaneous position-rotation gate timing. Range and FOV were individually satisfied
for all failing pairs. Position and rotation were also individually satisfied, but never simultaneously.

3. Do all agents fail similarly, or is there an agent-specific feasible subset?

There is an agent-specific feasible subset. `robot_1` is the strongest for the positive-X face ids, `robot_2` is required
for viewpoint `12`, and all robots can cover side ids `8` and `20`.

4. Is static feasibility too optimistic for these viewpoints?

At viewpoint level, no. At agent-viewpoint pair level, yes. The static mask says these target viewpoints are feasible for
all three agents, but Level 2 shows several static-feasible pairs do not satisfy coverage gates.

5. What should the next step be?

Primary next step: add evaluator assignment-history logging for the generated N=24 baseline runs. Since every target
viewpoint is coverable by at least one agent, we need to know whether nearest/greedy never assign these viewpoints,
assign them to agents that fail Level 2, abandon them too early, or keep retrying without coverage.

Secondary next step: after assignment history is available, consider using these Level 2 results to refine static
feasibility or add a diagnostic-only pair mask. Do not change the generated CSV, controller, coverage gates, or baseline
retry behavior until the baseline assignment history is visible.

## Bottom Line

The generated N=24 baseline issue is not explained by globally unreachable viewpoints. The current controller/gates can
cover every one of the seven problematic viewpoint ids with at least one robot. The more likely issue is that the current
baseline methods lack enough assignment-history / retry visibility and may be selecting agent-viewpoint pairs that are
static-feasible but Level-2 infeasible due to non-simultaneous position and rotation gates.
