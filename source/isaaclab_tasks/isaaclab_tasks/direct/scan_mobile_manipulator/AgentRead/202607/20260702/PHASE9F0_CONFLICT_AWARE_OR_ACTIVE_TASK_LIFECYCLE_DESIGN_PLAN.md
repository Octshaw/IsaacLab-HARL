# Phase 9F-0 Conflict-Aware Redirect / Active-Task Lifecycle Design Plan

Date: 2026-07-02

## 1. Scope and Boundaries

This is a design-only plan for the next phase after Phase 9E.

No code was implemented. No training was run. No playback was run. This plan does not modify reward formulas, reward scales/defaults, `Total_Reward` accounting, actor/shared observation dimensions, `available_actions` shape, assignment action semantics, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithms, installed site-packages, baseline solver behavior, scenario behavior, cooldown trigger logic, cooldown mask behavior, or budget parameters.

This phase stays inside the project contribution boundary:

```text
dynamic assignment
load balancing
path cost
robot state changes
task state updates
```

This phase does not address viewpoint generation, ROI importance modeling, or model-free NBV.

## 2. Phase 9E Final Conclusion Recap

Phase 9E produced a guarded intermediate budget-aware cooldown mechanism for assignment RL.

Key result from Phase 9E-4B:

```text
classification = TRAIN-P
models + budget: coverage 0.50, AUC 0.3304, max_same_target_streak 112, noop_when_available 0.0000
best_model + budget: coverage 0.48, AUC 0.3113, max_same_target_streak 110, noop_when_available 0.0000
models no cooldown: coverage 0.50, max_same_target_streak 140
best_model no cooldown: coverage 0.46, max_same_target_streak 189
```

Interpretation:

```text
The trained policy is useful.
Runtime budget-aware cooldown still helps reduce worst same-target streak.
Coverage is preserved.
Noop_when_available remains stable.
```

But Phase 9E is not a final solution:

```text
late repeated assignment counts remain high
new budget-triggered pairs appear after training
models/ playback has high selected-target conflict / inter-robot overlap / crossing diagnostics
budget-aware cooldown remains mask-only, not active-task lifecycle
```

Important interpretation to preserve:

```text
Budget-aware cooldown does not prove a target is unreachable.
It only suppresses repeated selection of the same robot-target pair after configured budget-aware stuck evidence.
```

## 3. Remaining Failure Modes

The exact failure after Phase 9E is no longer only "a robot repeats one target forever." Budget-aware cooldown reduces the worst uninterrupted streaks. The remaining failure is a compound assignment/execution coordination problem:

```text
1. Robots still produce high late repeated assignment counts.
2. Budget-triggered pairs change after training, meaning the policy can move stuck behavior to new robot-target pairs.
3. Budget-trigger redirects can send robots toward targets that are already selected, nearby, or geometrically conflicting.
4. Some conflict/overlap/crossing diagnostics are high, especially for the Phase 9E-4B models/ checkpoint.
5. The policy still re-decides every step, so normal task execution, retries, failure, release, and reassignment are implicit rather than explicit.
```

The evidence suggests the next problem is coordination around target ownership and task lifecycle, not just stuck-target detection.

## 4. Why Not Continue Cooldown Tuning

Cooldown threshold tuning is no longer the best next step.

Reasons:

```text
Phase 9E-3C showed pure same-target streak thresholds confuse normal multi-step task persistence with failure.
Phase 9E-3B showed weaker streak cooldowns trade coverage for streak reduction but do not solve the underlying lifecycle issue.
Phase 9E-3D showed budget-aware cooldown is safer than pure streak cooldown.
Phase 9E-4B showed budget-aware training preserves coverage and reduces max streak, but late repeats and coordination side effects remain.
```

More cooldown tuning can reduce one symptom while hiding two important questions:

```text
Are robots being redirected into targets already claimed by teammates?
Are robots reselecting every step because there is no explicit active-task lifecycle?
```

The next diagnostic should explain those questions before more trigger parameters are changed.

## 5. Route A: Conflict-Aware Redirect

Goal:

```text
Reduce duplicate target selection, inter-robot overlap, and crossing after budget-aware cooldown redirects a robot away from a stuck pair.
```

Possible mechanisms:

```text
avoid redirecting a robot to a target currently selected by another robot
add short-horizon target reservation for currently selected or recently released targets
temporarily mask targets already claimed by teammates during redirect windows
prefer uncovered, feasible, non-claimed alternatives with lower path conflict risk
add diagnostics for redirect target ownership, target proximity, and path-crossing risk
keep reward unchanged initially
keep observations unchanged initially
keep available_actions shape unchanged
keep default scenario disabled
keep implementation AssignmentHarlWrapper-local if possible
```

What Route A can solve:

```text
same-step duplicate selected targets after redirect
robots immediately redirecting into a teammate's current target
some short-horizon target-ownership churn
some post-trigger exact-target conflicts
```

What Route A cannot solve:

```text
the deeper every-step re-selection semantics
normal navigation persistence being represented as repeated decisions
explicit success/failure/timeout lifecycle
credit assignment for task completion versus task abandonment
policy preference for geometrically nearby but conflicting alternatives
path crossing caused by geometry rather than target identity
```

Risks:

```text
over-masking useful alternatives
reducing coverage if too strict
creating noop pressure if too many targets are reserved
hiding the real lifecycle problem behind another local guardrail
making policy behavior depend on runtime masks that are not observed
```

## 6. Route B: Active-Task Lifecycle

Goal:

```text
Change assignment from every-step target re-selection into a task lifecycle model.
```

Potential task states:

```text
unassigned
assigned / active
completed
failed
timeout / cooldown
released back to task pool
```

Potential robot states:

```text
idle
executing active target
scanning / completing
blocked or over-budget
released and ready for reassignment
```

Potential semantics:

```text
once a robot receives a target, it continues execution until completion, timeout, explicit failure, or release
RL action assigns only when the robot is idle or released
repeated same target during execution becomes normal task persistence, not a new decision every step
failure/timeout becomes explicit rather than inferred from repeated action choices
target ownership becomes a first-class task state
```

What Route B can solve:

```text
normal task persistence versus repeated retry ambiguity
explicit target ownership and release
explicit failure/timeout semantics
cleaner distinction between assignment decisions and low-level execution
policy churn from every-step reassignment
```

What Route B changes:

```text
Action semantics:
  action may mean "start a task when idle" rather than "select current target every step"
  noop may mean "continue active task" or "remain idle", requiring clear separation

Observations:
  likely need robot active/idle state
  likely need active target id/status
  likely need target ownership/status features
  may need remaining budget or elapsed active-task time

Reward:
  may need credit for assignment start, task progress, completion, abandonment, timeout, and failed release
  current reward can be preserved initially for diagnostics, but full lifecycle learning likely needs redesign

Evaluation:
  must report assignment starts, active durations, completions, failures, releases, timeouts, target ownership conflicts, coverage, and path/spatial side effects
```

Risks:

```text
larger implementation risk than Route A
MDP changes and observation dimension changes are likely
HARL checkpoint compatibility may break
reward and credit assignment may need redesign
harder to compare directly with Phase 9D/9E fixed-interface baselines
```

## 7. Route C: Staged Hybrid Route

Goal:

```text
Use diagnostics and a minimal conflict-aware guardrail to learn whether redirect conflict is the near-term blocker, then design active-task lifecycle if needed.
```

Proposed sequence:

```text
Phase 9F-1:
  post-budget-redirect conflict diagnostics
  no training
  no behavior changes

Phase 9F-2:
  conflict-aware redirect design
  config-gated
  wrapper-local if possible
  reward unchanged
  observations unchanged initially
  available_actions shape unchanged
  default scenario disabled

Phase 9F-3:
  playback-only validation of conflict-aware redirect
  compare against Phase 9D-3, Phase 9E-3D, and Phase 9E-4B

Phase 9G-0:
  active-task lifecycle design if conflict-aware redirect is insufficient
```

Why Route C is safer:

```text
It avoids jumping directly into action-semantics and observation changes.
It answers whether Phase 9E-4B's high conflict/overlap/crossing is caused by redirect choices, persistent policy preference, or geometry/path interaction.
It keeps Phase 9F-1 entirely diagnostic.
It preserves comparability with Phase 9E outputs before any new guardrail is implemented.
```

## 8. Recommended Immediate Next Step

Recommended route: Route C, starting with Phase 9F-1 post-budget-redirect conflict diagnostics.

Reason:

```text
Direct active-task lifecycle work is probably the right eventual direction, but it is too large to start without sharper evidence.
Conflict-aware redirect may be a useful near-term guardrail, but implementing it before diagnosing redirect failure modes risks another mask-only patch.
Phase 9F-1 can determine whether conflicts are caused by same-target redirects, nearby-target redirects, persistent policy preference, or geometry/path crossing.
```

This recommendation does not implement Phase 9F-1. It only defines the plan.

## 9. Detailed Phase 9F-1 Plan

Phase 9F-1 name:

```text
Post-budget-redirect conflict diagnostics
```

Purpose:

```text
Analyze whether conflicts after budget trigger are caused by redirect target choices, persistent policy preference, or geometry/path crossing.
```

Primary inputs:

```text
results/assignment_diagnostics/phase9e4b_budget_trained_models_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_best_model_with_budget_playback/
results/assignment_diagnostics/phase9e4b_budget_trained_trace_inspection/
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.csv
results/assignment_diagnostics/phase9e4b_budget_trained_playback_summary.json
```

Optional comparison inputs:

```text
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_models/
results/assignment_diagnostics/phase9d3_rl_playback_diagnostics_100k_best_model/
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_models_playback/
results/assignment_diagnostics/phase9e3d_budget_m15_slack5_d5_best_model_playback/
```

Questions to answer:

```text
1. After a budget trigger, what target does the robot choose next?
2. Is the next target already selected by another robot at that step?
3. Is the next target recently released or repeatedly selected by another robot?
4. Is the next target uncovered, feasible, and available?
5. Is conflict exact-target duplicate, nearby-target spatial overlap, or path crossing?
6. Do conflicts concentrate in the 20 steps after budget triggers or persist globally?
7. Are conflicts driven by one checkpoint, one robot, or one target family?
8. Are robots redirected into targets that later produce coverage gain?
9. Do robots return to the original triggered target after cooldown expiry?
10. Would a simple reservation mask have prevented the conflict without hiding all useful alternatives?
```

Expected outputs:

```text
conflict windows around budget triggers
next-target distribution after budget triggers
duplicate/overlap/crossing concentration tables
same-target versus nearby-target versus crossing-path attribution
robot-target pair ownership timeline
redirect target availability/feasibility/covered status
recommendation for whether conflict-aware redirect is justified
```

Suggested diagnostics:

```text
post_trigger_next_target_is_claimed
post_trigger_next_target_claimed_by_robot
post_trigger_next_target_duplicate_within_k_steps
post_trigger_next_target_distance_to_other_selected_targets
post_trigger_path_crossing_proxy
claimed_target_count_per_step
claim_churn_count
target_owner_switch_count
coverage_gain_after_redirect
return_to_triggered_pair_after_cooldown
```

No training. No playback unless a required file is missing and rerun is explicitly approved. No behavior changes.

## 10. Success Metrics

Phase 9F-1 succeeds if it produces a clear attribution of Phase 9E-4B conflict side effects:

```text
same-target redirect conflict:
  many post-trigger redirects select a target already selected by another robot

nearby-target spatial conflict:
  post-trigger target is not identical but is spatially close enough to cause overlap/crossing

path-crossing conflict:
  targets are distinct and not near, but base motion paths intersect

persistent policy preference:
  conflicts occur outside trigger windows and are not primarily caused by redirect

insufficient trace fields:
  assignment_history lacks enough row-level conflict/overlap/path data to attribute cause
```

Recommended thresholds for a future conflict-aware guardrail:

```text
must preserve coverage near Phase 9E-4B levels
must not increase noop_when_available
must reduce duplicate selected target rate after triggers
should reduce selected-target conflict / overlap / crossing without aggressive over-masking
should not make late repeated assignment counts worse
```

## 11. Risks and Limitations

```text
assignment_history currently lacks row-level selected-target conflict and inter-robot overlap fields
duplicate selected target is only an exact-target conflict proxy
base-motion crossing proxy may not fully explain planner/controller interactions
playback traces may be deterministic and not representative of multi-seed behavior
conflict-aware masking may create hidden state if the policy cannot observe reservations
active-task lifecycle likely changes action semantics and may require observation/reward changes
```

## 12. Files to Inspect in the Next Implementation Phase

For Phase 9F-1 diagnostics:

```text
scripts/environments/analyze_budget_cooldown_traces.py
scripts/environments/summarize_phase9e4b_playback.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
results/assignment_diagnostics/phase9e4b_budget_trained_*_playback/assignment_history.csv
results/assignment_diagnostics/phase9e4b_budget_trained_*_playback/summary.csv
```

For any later conflict-aware guardrail:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5.yaml
```

For active-task lifecycle design:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
```

## 13. Explicit No-Training / No-Code-Change Statement

Phase 9F-0 is planning only.

```text
No code was implemented.
No training was run.
No playback was run.
No reward/observation/action/env/HARL/baseline/scenario/cooldown behavior was changed.
No active-task lifecycle was implemented.
No commit was made.
```

## 14. Recommended Phase 9F Structure

```text
Phase 9F-1:
  Post-budget-redirect conflict diagnostics.
  Diagnostic analysis only.
  No training, no behavior changes.

Phase 9F-2:
  Conflict-aware redirect design.
  Decide whether a minimal config-gated wrapper-local guardrail is justified.

Phase 9F-3:
  Playback-only validation if a guardrail is implemented.
  Compare against Phase 9D-3, Phase 9E-3D, and Phase 9E-4B.

Phase 9G-0:
  Active-task lifecycle design if conflict-aware redirect is insufficient or hides the deeper assignment lifecycle issue.
```
