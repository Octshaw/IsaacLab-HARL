# Stage 4B Real Component N24 Controller-State Trace Report

Date: 2026-06-15

## Scope

This report covers a diagnostic-only full-episode controller-state / target-switching trace for generated real-component N=24 evaluator rollouts. It does not train assignment-RL, add assignment-RL evaluation, modify HARL core, change reward, change controller math, edit `assignment_controller.py`, alter the 9D action path, change environment default feasibility, make pair filtering or retry/fallback default behavior, add real robot articulation, IK, collision, or raycast coverage.

`real_component_bbox_sample.csv` remains temporary pipeline sanity data, not final viewpoint planning output or final algorithm performance data.

## Command

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py
```

```text
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --level2_pair_filter_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --assignment_retry_fallback --assignment_stall_window 30 --assignment_pair_cooldown 60 --write_assignment_history --write_controller_state_trace --controller_trace_pairs 1:1 2:12 1:2 1:14 1:13 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_controller_state_trace
```

## Output Files

```text
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/retry_fallback_events.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/controller_state_trace.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/controller_state_trace_summary.csv
```

## Trace Fields

Available fields:

```text
robot_base_x/y/z
ee_x/y/z
target_x/y/z
position_error
rotation_error
range_value
range_margin
fov_alignment
position_gate_ok
rotation_gate_ok
range_gate_ok
fov_alignment_gate_ok
position_rotation_gate_ok
all_coverage_gates_ok
controller_target_changed_this_step
consecutive_steps_assigned_to_same_viewpoint
cooldown_active_for_pair
cooldown_remaining
```

Unavailable fields:

```text
[]
```

Trace rows:

```text
controller_state_trace rows = 2990
controller_state_trace_summary rows = 10
```

The trace records each requested pair at every evaluator step, with `is_pair_selected_this_step` identifying whether the pair was actually assigned on that step.

## Rollout Result

Both nearest and greedy remain at:

```text
final_covered_count = 19/24
final_coverage = 0.7916666666666666
success = 0
final_uncovered_viewpoint_ids = [1, 2, 12, 13, 14]
```

Nearest and greedy have identical traced pair behavior in this run.

## Per-Pair Summary

| method | pair | assigned_steps | segments | max_consecutive | position ever | rotation ever | range ever | FOV ever | pos+rot ever | all gates ever | covered after assignment | cooldown segments | likely_failure_mode |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| nearest | robot_1 -> viewpoint_1 | 61 | 2 | 53 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |
| nearest | robot_2 -> viewpoint_12 | 155 | 2 | 116 | true | true | true | true | false | false | false | 2 | position_rotation_never_simultaneous |
| nearest | robot_1 -> viewpoint_2 | 30 | 1 | 30 | true | false | true | true | false | false | false | 1 | never_reaches_rotation_gate |
| nearest | robot_1 -> viewpoint_14 | 54 | 1 | 54 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |
| nearest | robot_1 -> viewpoint_13 | 45 | 1 | 45 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |
| greedy | robot_1 -> viewpoint_1 | 61 | 2 | 53 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |
| greedy | robot_2 -> viewpoint_12 | 155 | 2 | 116 | true | true | true | true | false | false | false | 2 | position_rotation_never_simultaneous |
| greedy | robot_1 -> viewpoint_2 | 30 | 1 | 30 | true | false | true | true | false | false | false | 1 | never_reaches_rotation_gate |
| greedy | robot_1 -> viewpoint_14 | 54 | 1 | 54 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |
| greedy | robot_1 -> viewpoint_13 | 45 | 1 | 45 | true | false | true | false | false | false | false | 1 | never_reaches_rotation_gate |

## Gate Count Details

Per method, selected-step gate counts were:

| pair | selected_steps | position_gate_ok count | rotation_gate_ok count | range_gate_ok count | fov_alignment_gate_ok count | position_rotation_gate_ok count | all_coverage_gates_ok count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| robot_1 -> viewpoint_1 | 61 | 39 | 0 | 60 | 0 | 0 | 0 |
| robot_2 -> viewpoint_12 | 155 | 104 | 7 | 155 | 9 | 0 | 0 |
| robot_1 -> viewpoint_2 | 30 | 25 | 0 | 30 | 13 | 0 | 0 |
| robot_1 -> viewpoint_14 | 54 | 48 | 0 | 54 | 0 | 0 | 0 |
| robot_1 -> viewpoint_13 | 45 | 40 | 0 | 45 | 0 | 0 | 0 |

## Pair Answers

### robot_1 -> viewpoint_1

- Assigned for 61 steps per method.
- Position gate becomes true.
- Rotation gate never becomes true.
- Range gate becomes true.
- FOV alignment gate never becomes true.
- Position+rotation gate never becomes true.
- All coverage gates never become true.
- The pair is interrupted by cooldown once and split into two assignment segments.

Primary diagnosis: rotation gate never reaches tolerance; FOV also never reaches the alignment threshold.

### robot_2 -> viewpoint_12

- Assigned for 155 steps per method.
- Position gate becomes true.
- Rotation gate becomes true.
- Range gate becomes true.
- FOV alignment gate becomes true.
- Position+rotation gate never becomes true.
- All coverage gates never become true.
- The pair is interrupted by cooldown twice and split into two assignment segments; robot_2 also spends 53 traced rows in noop while viewpoint 12 remains uncovered.

Primary diagnosis: position and rotation are individually reached but not simultaneously. This resembles the earlier fixed-12 gate-timing issue.

### robot_1 -> viewpoint_2

- Assigned for 30 steps per method.
- Position gate becomes true.
- Rotation gate never becomes true.
- Range gate becomes true.
- FOV alignment gate becomes true.
- Position+rotation gate never becomes true.
- All coverage gates never become true.
- The pair reaches the stall window and triggers cooldown once.

Primary diagnosis: rotation gate never reaches tolerance within the assignment window.

### robot_1 -> viewpoint_14

- Assigned for 54 steps per method.
- Position gate becomes true.
- Rotation gate never becomes true.
- Range gate becomes true.
- FOV alignment gate never becomes true.
- Position+rotation gate never becomes true.
- All coverage gates never become true.
- The pair is interrupted by cooldown once.

Primary diagnosis: rotation gate never reaches tolerance; FOV also never aligns.

### robot_1 -> viewpoint_13

- Assigned for 45 steps per method.
- Position gate becomes true.
- Rotation gate never becomes true.
- Range gate becomes true.
- FOV alignment gate never becomes true.
- Position+rotation gate never becomes true.
- All coverage gates never become true.
- The pair is interrupted by cooldown once.

Primary diagnosis: rotation gate never reaches tolerance; FOV also never aligns.

## Interpretation

The remaining `19/24` failure is not caused by known Level-2-failing pair assignment, candidate visibility, or never assigning the remaining targets.

For the traced `robot_1` pairs, the full-episode controller state reaches position and range but fails the rotation gate. Several of those pairs also never satisfy FOV alignment. This points toward controller orientation convergence, target orientation convention, or target-switching effects in the full rollout.

For `robot_2 -> viewpoint_12`, the trace confirms a gate timing problem: position, rotation, range, and FOV are individually achieved at some point, but position and rotation never overlap. Cooldown interrupts the pair, but the underlying failure is visible before and after cooldown.

## Recommended Next Step

Run a targeted controller/gate diagnostic in full-episode context for the traced known-coverable pairs, focused on orientation convergence and simultaneous gate timing:

```text
robot_1 -> viewpoint_1
robot_1 -> viewpoint_2
robot_1 -> viewpoint_13
robot_1 -> viewpoint_14
robot_2 -> viewpoint_12
```

The next diagnostic should compare full-episode target poses, scanner quaternion trajectories, rotation errors, FOV alignment, and target switching against the successful single-pair Level 2 runs. Do not change reward, controller math, assignment policy, or environment behavior until that comparison explains why Level 2 coverable pairs fail in the multi-agent evaluator rollout.
