# TASK_PROGRESS

This file is the compact handoff for the assignment-based RL work.

## Current Status

Status: fixed-12 assignment-RL MVP and Phase 5 comparison complete; next stage is real component proxy + external viewpoint file + automatic feasibility generator planning.

Latest completed work:
- Summarized the completed fixed-12 assignment-RL MVP.
- Planned the next stage toward real component proxy, external viewpoint file, and automatic feasibility generation.
- Added two handoff/planning documents:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

No code was modified in this documentation/planning task.

Important unchanged constraints:
- No installed `site-packages` files were modified.
- No HARL runner core logic was modified.
- No scan env reward code was modified.
- No scan env underlying 9D action space was modified.
- No `assignment_controller.py` control math was modified.
- No arbitrary/variable viewpoint-count support was added.
- No Phase 6 sequential duplicate mask was added.
- No training or simulation was run in this task.

## Fixed-12 MVP Status

The fixed 12-viewpoint assignment-RL MVP is complete.

Current assignment-RL path:

```text
train.py --assignment_rl
  -> AssignmentOnPolicyHARunner
  -> AssignmentIsaacLabEnv
  -> AssignmentHarlWrapper
  -> Discrete(num_viewpoints + 1)
  -> available_actions mask
  -> scalar discrete action
  -> assignment
  -> viewpoint_assignment_to_actions()
  -> unchanged scan env.step(9D action dict)
```

Current fixed-scenario capability override:

```python
fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
```

This is a fixed-12 MVP scenario-level capability override. It is not a general feasibility model for arbitrary viewpoint sets.

Current result scope:

```text
fixed 12-viewpoint MVP only
not arbitrary / variable viewpoint-count generalization
not real robot articulation / IK / collision
```

## Phase 5 Comparison Status

Phase 5 unified comparison is complete.

CSV outputs:

```text
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
```

CSV completeness:
- `per_episode.csv` has 20 rows.
- Each method has 5 episodes:

```text
random: 5
nearest: 5
greedy: 5
assignment_rl: 5
```

- `summary.csv` has 4 rows:

```text
random
nearest
greedy
assignment_rl
```

Phase 5 summary:

```text
method         success  coverage  steps_full  auc    duplicate  noop   valid  return
random         1.000    1.000     299.0       0.052  0.000      0.000  1.000  8.440
nearest        1.000    1.000     126.0       0.612  0.000      0.243  1.000  175.585
greedy         1.000    1.000     126.0       0.612  0.000      0.243  1.000  175.585
assignment_rl  1.000    1.000     118.0       0.485  0.415      0.031  1.000  198.785
```

Main conclusions:
- Assignment-RL reaches 100% coverage in all 5 fixed-scenario episodes.
- Assignment-RL is faster than nearest/greedy in mean steps to full coverage: `118` vs `126`.
- Assignment-RL has the highest mean return: `198.785`.
- Assignment-RL has lower coverage AUC than nearest/greedy: `0.485` vs `0.612`.
- Assignment-RL still has visible duplicate assignment: `0.415`.
- Assignment-RL no-op rate is low: `0.031`.
- All methods have valid action rate `1.000`.

Detailed Phase 5 analysis:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
```

## Phase 6 Status

Phase 6 duplicate avoidance is deferred.

Current recommendation:

```text
keep Phase 6 duplicate sequential mask as optional optimization
do not implement it before the real component proxy / external viewpoint / feasibility-generator stage
```

Why:
- Assignment-RL already reaches 100% fixed-scenario coverage.
- Assignment-RL finishes slightly faster than nearest/greedy.
- Valid action rate is already 1.0.
- No-op rate is low.
- The next bigger blocker is scenario realism and automatic feasibility, not duplicate masking.

## Next-Stage Plan

Next stage should not directly connect the real robot model.

Recommended sequence:

```text
Stage 1: Replace measured object with real component proxy.
Stage 2: Load fixed-N viewpoint set from external file.
Stage 3: Add automatic feasibility generator.
Stage 4: Re-run baselines and assignment-RL on real component proxy.
Stage 5: Introduce real robot USD / articulation / IK / collision later.
```

Planning document:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

Near-term non-goals:
- Do not directly enter Phase 6 duplicate avoidance.
- Do not directly build arbitrary / variable viewpoint-count policy support.
- Do not directly connect real robot articulation.
- Do not treat the fixed-12 scenario override as a general capability model.
- Do not load old 9D continuous checkpoints into assignment mode.
- Do not modify HARL site-packages.
- Do not advance mesh, collision, IK, and RL generalization all at once.

## Key Files

Assignment implementation:

```text
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
```

Latest reports:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

## Latest Verification

This documentation/planning task only performed read-only file checks and Markdown updates.

Read:

```text
AGENTS.md
TASK_PROGRESS.md
PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
assignment-RL key implementation references
```

No training was run.
No simulation was run.
No Python source was modified.

## Recommended Next Codex Task

Start with Stage 1 + Stage 2 as a design/minimal implementation task:

```text
real component proxy config
+ external fixed-N viewpoint file loader
+ reset-only viewpoint/mask diagnostics
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

After Stage 1/2 are stable, implement Stage 3 automatic feasibility generation and replace the manual fixed-12 override.

## Do Not Do

- Do not modify installed `site-packages`.
- Do not modify HARL runner core logic.
- Do not change scan env reward unless explicitly requested.
- Do not change scan env underlying 9D action space.
- Do not change `assignment_controller.py` control math.
- Do not test assignment mode with old 9D continuous checkpoints.
- Do not run long training directly.
- Do not add arbitrary/variable viewpoint-count policy support.
- Do not add Phase 6 sequential duplicate mask unless explicitly requested.
- Do not connect real robot articulation before component proxy, external viewpoints, and feasibility generation are stable.

## Detailed Reports / Archives

Latest summary and plan:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

Latest Phase 5 analysis:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
```

Full historical progress archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260605/TASK_PROGRESS_ARCHIVE_FULL_HISTORY_BEFORE_COMPACT_20260605.md
```

Earlier copy of the full archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/TASK_PROGRESS_ARCHIVE_FULL_HISTORY_BEFORE_COMPACT_20260605.md
```
