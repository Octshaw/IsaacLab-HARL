# TASK_PROGRESS

This file is the compact handoff for the assignment-based RL work.

## Current Status

<<<<<<< HEAD
Status: fixed-12 assignment-RL MVP and Phase 5 comparison complete; next stage is real component proxy + external fixed-N viewpoint file + automatic feasibility generator.

Latest completed work:
- Refined the fixed-12 MVP summary.
- Refined the next-stage real component / viewpoint planning document.
- Added Stage 0: fixed-12 MVP regression baseline.
- Clarified that the next implementation should start with minimal Stage 1 + Stage 2 only.

Documentation changed in the latest task:
=======
Status: fixed-12 assignment-RL MVP and Phase 5 comparison complete; next stage is real component proxy + external viewpoint file + automatic feasibility generator planning.

Latest completed work:
- Summarized the completed fixed-12 assignment-RL MVP.
- Planned the next stage toward real component proxy, external viewpoint file, and automatic feasibility generation.
- Added two handoff/planning documents:
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
<<<<<<< HEAD
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No code was modified in the latest task.
=======
```

No code was modified in this documentation/planning task.
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

Important unchanged constraints:
- No installed `site-packages` files were modified.
- No HARL runner core logic was modified.
- No scan env reward code was modified.
- No scan env underlying 9D action space was modified.
- No `assignment_controller.py` control math was modified.
- No arbitrary/variable viewpoint-count support was added.
- No Phase 6 sequential duplicate mask was added.
<<<<<<< HEAD
- No training, simulation, or evaluation was run in the latest task.

## Fixed-12 MVP Regression Baseline

The fixed 12-viewpoint assignment-RL MVP should remain available as a regression scenario.

Reference behavior from Phase 5:

```text
assignment_rl success_rate = 1.0
assignment_rl mean_steps_to_full_coverage ~= 118
nearest / greedy mean_steps_to_full_coverage ~= 126
assignment_rl mean_final_coverage = 1.0
```

Before and after major next-stage changes, verify the fixed-12 path still works:

```text
baseline-only evaluator smoke
assignment-RL checkpoint eval smoke
reset available_actions shape check
fixed-12 feasible_mask sanity check
```

Do not delete or overwrite the fixed-12 scenario until the real-component scenario is stable.

Current fixed-scenario capability override:

```python
fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
```

This is a fixed-12 MVP scenario-level capability override. It is not a general feasibility model for arbitrary viewpoint sets.

## Active Architecture / Implementation Path
=======
- No training or simulation was run in this task.

## Fixed-12 MVP Status

The fixed 12-viewpoint assignment-RL MVP is complete.
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

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

<<<<<<< HEAD
Default non-assignment HARL behavior remains the original raw 9D continuous action path.

Current scope:

```text
fixed 12-viewpoint MVP only
not arbitrary / variable viewpoint-count policy generalization
=======
Current fixed-scenario capability override:

```python
fixed_12_mvp_infeasible_agent_viewpoints = {"robot_2": (5,)}
```

This is a fixed-12 MVP scenario-level capability override. It is not a general feasibility model for arbitrary viewpoint sets.

Current result scope:

```text
fixed 12-viewpoint MVP only
not arbitrary / variable viewpoint-count generalization
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
not real robot articulation / IK / collision
```

## Phase 5 Comparison Status

Phase 5 unified comparison is complete.

CSV outputs:

```text
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
```

<<<<<<< HEAD
=======
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

>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
Phase 5 summary:

```text
method         success  coverage  steps_full  auc    duplicate  noop   valid  return
random         1.000    1.000     299.0       0.052  0.000      0.000  1.000  8.440
nearest        1.000    1.000     126.0       0.612  0.000      0.243  1.000  175.585
greedy         1.000    1.000     126.0       0.612  0.000      0.243  1.000  175.585
assignment_rl  1.000    1.000     118.0       0.485  0.415      0.031  1.000  198.785
```

Main conclusions:
<<<<<<< HEAD
- Assignment-RL reaches 100% coverage in all fixed-scenario evaluation episodes.
- Assignment-RL is faster than nearest/greedy in mean steps to full coverage: `118` vs `126`.
- Assignment-RL has the highest mean return: `198.785`.
- Assignment-RL still has visible duplicate assignment: `0.415`.
- Assignment-RL no-op rate is low: `0.031`.
- Phase 6 duplicate avoidance remains optional and deferred.
=======
- Assignment-RL reaches 100% coverage in all 5 fixed-scenario episodes.
- Assignment-RL is faster than nearest/greedy in mean steps to full coverage: `118` vs `126`.
- Assignment-RL has the highest mean return: `198.785`.
- Assignment-RL has lower coverage AUC than nearest/greedy: `0.485` vs `0.612`.
- Assignment-RL still has visible duplicate assignment: `0.415`.
- Assignment-RL no-op rate is low: `0.031`.
- All methods have valid action rate `1.000`.
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

Detailed Phase 5 analysis:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
```

<<<<<<< HEAD
## Refined Next-Stage Plan

The next stage should not directly connect the real robot model.
=======
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
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

Recommended sequence:

```text
<<<<<<< HEAD
Stage 0: Freeze fixed-12 MVP regression baseline.
Stage 1: Add minimal real component proxy support.
=======
Stage 1: Replace measured object with real component proxy.
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
Stage 2: Load fixed-N viewpoint set from external file.
Stage 3: Add automatic feasibility generator.
Stage 4: Re-run baselines and assignment-RL on real component proxy.
Stage 5: Introduce real robot USD / articulation / IK / collision later.
```

<<<<<<< HEAD
Stage 1 + Stage 2 should start minimal:

```text
component_proxy_type = bbox
component_proxy_center
component_proxy_half_extents
one explicit fixed-N viewpoint CSV format
one explicit frame convention
reset-only diagnostics
```

Do not introduce mesh raycast, IK, collision, or real articulation in the first implementation.

Viewpoint file conventions must be explicit:

```text
pose_type
coordinate_frame
units
quaternion_order
euler_convention if supported
scanner_forward_axis
scanner_up_axis
viewpoint quaternion meaning
```

The loader must not silently guess frame or quaternion conventions. Invalid or ambiguous viewpoint files should fail with a clear error.

Feasibility generator plan:

```text
Level 1: static geometric feasibility
Level 2: optional controller feasibility diagnostic
```

Start with Level 1 static feasibility and reset-only diagnostics. Do not make Level 2 mandatory in the first implementation.

Scenario config should become the entrypoint for component, viewpoints, robot capabilities, and feasibility settings so future experiments are reproducible and fixed-N identity is explicit.

Detailed next-stage plan:
=======
Planning document:
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

<<<<<<< HEAD
=======
Near-term non-goals:
- Do not directly enter Phase 6 duplicate avoidance.
- Do not directly build arbitrary / variable viewpoint-count policy support.
- Do not directly connect real robot articulation.
- Do not treat the fixed-12 scenario override as a general capability model.
- Do not load old 9D continuous checkpoints into assignment mode.
- Do not modify HARL site-packages.
- Do not advance mesh, collision, IK, and RL generalization all at once.

>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
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

<<<<<<< HEAD
Latest task verification was documentation-only.

Checked that these files exist:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
=======
This documentation/planning task only performed read-only file checks and Markdown updates.

Read:

```text
AGENTS.md
TASK_PROGRESS.md
PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
assignment-RL key implementation references
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
```

No training was run.
No simulation was run.
<<<<<<< HEAD
No evaluation was run.
=======
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
No Python source was modified.

## Recommended Next Codex Task

<<<<<<< HEAD
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
Do not implement Phase 6 duplicate avoidance.
=======
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
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
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
<<<<<<< HEAD
- Do not run simulation for documentation-only tasks.
=======
>>>>>>> dcc2beb9f43abdeb5ab87c300a089b48f569e74d
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
