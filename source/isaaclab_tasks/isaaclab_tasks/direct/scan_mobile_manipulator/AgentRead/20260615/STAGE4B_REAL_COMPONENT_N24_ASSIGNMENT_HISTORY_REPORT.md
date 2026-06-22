# Stage 4B Real Component N24 Assignment History Report

Date: 2026-06-15

## Scope

This report documents diagnostic logging added to the evaluator and the first bounded generated real-component N=24
assignment-history run. It does not change random / nearest / greedy behavior, controller behavior, reward, environment
coverage logic, HARL core, assignment-RL, the 9D action path, or the generated viewpoint CSV.

`real_component_bbox_sample.csv` remains temporary pipeline sanity data and should not be treated as final viewpoint
planning output.

## Implementation Summary

`scripts/environments/evaluate_assignment_methods.py` now writes:

```text
assignment_history.csv
```

beside:

```text
per_episode.csv
summary.csv
diagnostics.json
```

The new file is enabled by default through `--write_assignment_history` / `--no-write_assignment_history`.

Each history row records one method / episode / step / env / agent assignment decision, including:

```text
method
episode
step
env_id
agent_id
assigned_viewpoint_id
is_noop
selected_available
covered_before_count
covered_after_count
newly_covered_viewpoint_ids
coverage_count
coverage_ratio
assigned_viewpoint_was_covered_before
assigned_viewpoint_covered_after
```

Coverage state is captured before the action and after the action. The after-action state uses the same pre-reset
coverage snapshot path as the fixed evaluator metrics, so timeout or automatic reset does not fabricate full coverage.

## Verification Commands

Syntax check:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py
```

Fixed-12 smoke:

```text
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4b_assignment_history_fixed12_smoke --write_assignment_history
```

Generated real-component N=24 assignment-history diagnostic:

```text
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_assignment_history_check --write_assignment_history
```

## Generated Outputs

```text
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/assignment_history.csv
```

The N=24 diagnostic wrote `1794` assignment-history rows:

```text
2 methods * 299 steps * 1 env * 3 agents = 1794 rows
```

The fixed evaluator metrics remained:

| method | final covered count | final coverage | success | final uncovered ids |
|---|---:|---:|---:|---|
| nearest | 17/24 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |
| greedy | 17/24 | 0.7083333333333334 | 0 | [1, 2, 8, 12, 13, 14, 20] |

## Level 2 Coverable Agents

From the previous Level 2 report:

| viewpoint | Level 2 coverable agents |
|---:|---|
| 1 | robot_1 |
| 2 | robot_1 |
| 8 | robot_0, robot_1, robot_2 |
| 12 | robot_2 |
| 13 | robot_1 |
| 14 | robot_1 |
| 20 | robot_0, robot_1, robot_2 |

## Assignment-History Findings

Nearest and greedy produced the same assignment pattern in this bounded run.

| viewpoint | nearest assignments | greedy assignments | initial interpretation |
|---:|---:|---:|---|
| 1 | 167 | 167 | repeatedly assigned, but only to Level-2-failing `robot_2` |
| 2 | 0 | 0 | never assigned |
| 8 | 0 | 0 | never assigned |
| 12 | 253 | 253 | repeatedly assigned; mix of Level-2-coverable and Level-2-failing agents |
| 13 | 190 | 190 | repeatedly assigned; mix of Level-2-coverable and Level-2-failing agents |
| 14 | 0 | 0 | never assigned |
| 20 | 0 | 0 | never assigned |

Agent distribution for assigned target viewpoints:

| viewpoint | Level 2 coverable agent(s) | observed assignment distribution |
|---:|---|---|
| 1 | robot_1 | robot_2: 167 |
| 12 | robot_2 | robot_0: 167, robot_1: 23, robot_2: 63 |
| 13 | robot_1 | robot_1: 167, robot_2: 23 |

No target assignment row ended with `assigned_viewpoint_covered_after=True`, and no target id appeared in
`newly_covered_viewpoint_ids`.

At the end of both nearest and greedy episodes, the last repeated assignment pattern was:

```text
robot_0 -> viewpoint_12
robot_1 -> viewpoint_13
robot_2 -> viewpoint_1
coverage_count = 17
coverage_ratio = 0.7083333333333334
newly_covered_viewpoint_ids = []
```

This pattern persisted through the final logged steps, so the bounded run is not merely skipping all uncovered ids. It
also repeatedly retries a stuck set of assignments without fallback.

## Answers to Diagnostic Questions

1. Are coverable viewpoints skipped?

Yes. Viewpoints `2`, `8`, `14`, and `20` were never assigned by nearest or greedy in this run, even though Level 2 found
at least one coverable robot for each.

2. Are viewpoints assigned to Level-2-failing agents?

Yes. Viewpoint `1` was assigned only to `robot_2`, while Level 2 found it coverable by `robot_1`. Viewpoints `12` and
`13` were also assigned to failing agents for part of the run.

3. Are viewpoints assigned to Level-2-coverable agents but still not covered?

Yes. Viewpoint `12` was assigned to its Level-2-coverable `robot_2` for 63 rows, and viewpoint `13` was assigned to its
Level-2-coverable `robot_1` for 167 rows. Neither became covered in the multi-agent baseline episode. This suggests
episode context, simultaneous multi-agent motion, target switching history, or controller state may matter beyond the
single-pair Level 2 checks.

4. Are failing pairs retried without fallback?

Yes. The final repeated pattern keeps assigning `12/13/1` while coverage remains at `17/24` and no new target viewpoint
is covered.

5. Are viewpoints abandoned?

Some are effectively abandoned by never being assigned (`2`, `8`, `14`, `20`). Others are not abandoned but remain stuck
under repeated assignments (`1`, `12`, `13`).

## Recommended Next Step

Do not change baseline behavior yet. The next diagnostic should compare the baseline assignment trace against Level 2
pair coverability and controller gate traces for the repeated stuck pattern:

```text
robot_0 -> viewpoint_12
robot_1 -> viewpoint_13
robot_2 -> viewpoint_1
```

The most useful next implementation is a diagnostic-only evaluator summary that joins assignment history with a
Level-2-derived pair status table, so each step can be labeled as:

```text
assigned_to_known_coverable_pair
assigned_to_known_level2_failing_pair
assigned_to_unchecked_pair
```

After that, choose between pair-level feasibility filtering, retry/fallback logic, or a targeted controller/coverage gate
investigation. Do not add those behavior changes until the diagnostic join is reviewed.
