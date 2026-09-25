# Stage 4 Plan: Real Component Fixed-N Evaluation

## Overview

The real-component task-space pipeline is now ready for fixed-N evaluation work. The system supports:

- visual-only real OBJ mesh loading;
- auto bbox proxy from transformed OBJ bounds;
- OBJ unit `mm`, scale, rotation, translation, and base-center world-origin alignment;
- external fixed-N viewpoint CSV loading with strict `scanner_pose_world_quat_wxyz_v1` conventions;
- generated bbox-side sample CSV for pipeline sanity checks;
- `static_geometric_v1` feasibility diagnostics;
- bounded Level 2 controller diagnostics for the fixed-12 special case;
- scenario YAML configs for headless smoke, visual smoke, mesh bounds inspection, and CSV generation.

The next goal is to restore and extend the algorithm evaluation pipeline for real component fixed-N scenarios. This is
still fixed-N experiment support, not arbitrary/variable-N policy generalization.

## Stage 4A: Extend Evaluator for External Fixed-N Scenario Configs

Goal: extend `scripts/environments/evaluate_assignment_methods.py` so it can evaluate scenario YAMLs and external
fixed-N viewpoint CSVs.

Current status: `evaluate_assignment_methods.py` is still fixed-12 oriented. It was written for the Phase 5 fixed-12
comparison and should not be treated as the real-component external-N evaluator until this stage is implemented.

First evaluator scope:

- Support scenario YAML config input, especially `real_component_bbox_sample_headless.yaml`.
- Support external fixed-N CSVs without asserting `num_viewpoints == 12`.
- Evaluate only `random`, `nearest`, and `greedy` first.
- Do not train RL in Stage 4A.
- Preserve the existing fixed-12 evaluation path as a regression scenario.

External fixed-N invariant:

```text
If the viewpoint CSV has N viewpoints:
  noop_id = N
  action width = N + 1
  available_actions shape = [num_envs, num_agents, N + 1]
```

Required evaluator diagnostics:

- scenario config path;
- viewpoint CSV path;
- loaded `num_viewpoints`;
- `noop_id`;
- `available_actions` shape;
- feasible agents per viewpoint;
- permanently unavailable viewpoints;
- manual override rows;
- infeasible rows.

## Stage 4B: Run Baselines on Generated Real Component Sample CSV

Use:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
```

Evaluate:

```text
random
nearest
greedy
```

Expected outputs:

```text
per_episode.csv
summary.csv
diagnostics.json
```

Important warning: `real_component_bbox_sample.csv` is only pipeline sanity / smoke CSV data generated from bbox-side
sample viewpoints. It is useful for validating plumbing, masks, controller path, and reporting, but it must not be used
as a final algorithm performance conclusion.

Baseline evaluation should first answer:

- Do all loaded viewpoints remain feasible for at least one agent?
- Are any viewpoints permanently unavailable?
- Do random / nearest / greedy run without fixed-12 assumptions?
- Do episode metrics and CSV outputs remain well-formed for `N=24`?

## Stage 4C: Replace Generated CSV With Real Planned Viewpoint CSV

When the final planned viewpoint CSV is provided, it should use the existing strict format:

```text
format = scanner_pose_world_quat_wxyz_v1
pose_type = scanner_pose_in_world
coordinate_frame = world
units = meters
world origin = model base center
quaternion_order = qw,qx,qy,qz
scanner_forward_axis = +X
scanner_up_axis = +Z
viewpoint_quaternion_meaning = scanner_frame_orientation_in_world
```

Run the same baseline evaluation sequence on the real planned CSV:

```text
random
nearest
greedy
```

Compare the planned-CSV results against the temporary generated sample only as a pipeline sanity reference, not as a
scientific performance benchmark.

## Stage 4D: Train New Assignment-RL Checkpoint for the Final Fixed-N Scenario

Train assignment-RL only after Stage 4A and Stage 4B/C baseline evaluation works.

Rules:

- Old fixed-12 assignment-RL checkpoints are incompatible with `N=24` or any different N because the discrete action
  head width changes.
- Old 9D continuous HARL checkpoints are incompatible with assignment mode.
- Train a new assignment-RL checkpoint for the final fixed-N scenario.
- Do not train on `real_component_bbox_sample.csv` unless explicitly running a pipeline test.
- Keep fixed-12 default scenario available as a regression path.

Before training, confirm:

- final CSV viewpoint count;
- no-op id;
- action width;
- available mask shape;
- feasible agents per viewpoint;
- no permanently unavailable viewpoints;
- baseline methods can complete bounded evaluation.

## Stage 4E: Evaluation Reporting and Visualization

Planned reporting artifacts:

```text
summary.csv
per_episode.csv
diagnostics.json
coverage curves
method comparison table
optional videos
PPT-ready figures
```

Recommended report contents:

- scenario name and config path;
- component mesh path and transform summary;
- viewpoint CSV path and viewpoint count;
- method-level success rate;
- mean final coverage;
- steps to full coverage when successful;
- no-op counts and duplicate assignment counts if available;
- permanently unavailable viewpoints;
- manual feasibility override rows;
- infeasible rows and reasons.

## Stage 5: Real Robot Model Later

Keep real robot integration outside the immediate Stage 4 work.

Later additions:

```text
real robot USD
articulation
IK
collision
joint limits
motion control
sensor frame alignment
```

Do not introduce these while extending baseline fixed-N evaluation. The current task-space skeleton should remain the
debuggable layer for evaluating assignment, viewpoint CSVs, feasibility masks, and controller/coverage gates.

## Recommended Next Codex Task

```text
Extend evaluate_assignment_methods.py for external fixed-N scenario configs and run random/nearest/greedy on the real component generated N=24 scenario.
```

Implementation should start with baselines only. Do not train assignment-RL, do not modify HARL core, do not change
`assignment_controller.py`, and do not introduce real robot articulation, IK, collision, or raycast coverage.
