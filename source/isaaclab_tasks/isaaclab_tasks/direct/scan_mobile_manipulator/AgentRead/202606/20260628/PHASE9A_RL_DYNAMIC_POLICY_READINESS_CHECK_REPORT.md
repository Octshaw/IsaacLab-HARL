# Phase 9A RL Dynamic-Policy Readiness Check Report

Date: 2026-06-28

## Scope

This report audits the current RL/dynamic-policy interface for the real-component proxy assignment task.

It does not start RL training. It does not start formal RL evaluation. It does not change observations, action masks,
reward, solvers, controllers, HARL internals, or environment behavior.

The checked scenario is:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

## Commands Run

Interpreter check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Output:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

One-step wrapper compatibility smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9a_rl_readiness_n50_m3_smoke.json
```

Result:

```text
[OK] assignment HARL wrapper smoke passed
```

Static checkpoint shape inspection was also run by loading actor state dicts only. No policy rollout was performed.

## Executive Summary

Shape-level RL wrapper compatibility for N=50, M=3 is OK. The wrapper dynamically infers the number of agents and
viewpoints, exposes `Discrete(num_viewpoints + 1)` per agent, appends noop as action id `N`, and returns
`available_actions` in HARL-compatible shape.

Semantic readiness is not yet sufficient for meaningful dynamic-policy evaluation against the Phase 8 plateau. The
policy observation is still a compact 96D per-agent vector with only the nearest 8 uncovered viewpoint slots, no
viewpoint ids in those slots, no full cost matrix, no no-progress/retry history, no load-balance state, and no conflict
or obstacle-risk features. The reward encourages coverage but does not directly penalize the Phase 8 failure modes:
late repeated assignment, no-progress behavior, selected-target conflict, inter-robot overlap, actual base-motion
crossing, or load imbalance.

Existing checkpoints should be treated as incompatible with N=50. The assignment checkpoints found under
`results/isaaclab/.../assignment_happo_*` have 13-class categorical action heads, meaning old fixed N=12 plus noop.
The older `scan_happo` checkpoints are 9D continuous-control policies, not assignment policies. N=50 assignment play
would require a 51-class categorical head.

## Interface Compatibility

Evidence:

```text
assignment_harl_wrapper.py
  __init__: infers agents, num_envs, num_viewpoints, and builds Discrete action spaces
  reset: returns obs, shared_obs, available_actions
  step: decodes scalar actions, calls assignment controller, returns rewards/dones/info/available_actions

assignment_rl_interface.py
  make_assignment_action_mask: converts available_mask to float mask and appends noop
  decode_discrete_assignment: maps 0..N-1 to viewpoints and N to -1 noop
```

Smoke result:

| field | value |
|---|---:|
| num_envs | 1 |
| num_agents | 3 |
| num_viewpoints | 50 |
| noop_id | 50 |
| available_actions_shape | [1, 3, 51] |
| available_mask_shape | [1, 3, 50] |
| cost_matrix_shape | [1, 3, 50] |
| task_status_shape | [1, 50] |
| robot_status_shape | [1, 3] |
| permanently_unavailable_viewpoints | [] |
| available_viewpoints_per_agent at reset | [50, 50, 47] |

Verdict:

```text
N=50, M=3 wrapper plumbing is compatible at reset and one step.
```

## HARL Config And Runner Notes

The current `agents/harl_happo_cfg.yaml` does not hard-code action width or agent count directly. The assignment runner
constructs actors from the wrapped environment action spaces.

Important caveats:

- `harl_happo_cfg.yaml` currently has `train.episode_length = 1000`, while the env episode horizon is 300 control steps
  from `episode_length_s = 30.0` and 0.1 second control steps. Future RL runs should align rollout/evaluation horizon
  deliberately.
- `scripts/reinforcement_learning/harl/train.py` sets `algo_args["eval"]["use_eval"] = False`, so the normal training
  entry point avoids HARL's unwrapped eval env path.
- If `assignment_harl_training.py` is used directly while keeping `eval.use_eval = True`, its eval env construction
  still calls HARL's generic `make_eval_env` rather than the assignment wrapper. Do not use that path for Phase 9B
  without a separate eval-wrapper check.
- `scripts/reinforcement_learning/harl/play_assignment.py` is the assignment-specific play path. It builds the
  assignment wrapper, constructs actors with the current action space, loads actor weights, and passes
  `available_actions[:, agent_id, :]` to each actor.

## Checkpoint Compatibility

Static actor state dict inspection:

```text
assignment_happo_1m_len320_night/.../actor_agent_robot_0.pt
  act.action_out.linear.weight: (13, 256)
  act.action_out.linear.bias:   (13,)

assignment_happo_5k_len256_test/.../actor_agent_robot_0.pt
  act.action_out.linear.weight: (13, 256)
  act.action_out.linear.bias:   (13,)

scan_happo/.../actor_agent_robot_0.pt
  act.action_out.fc_mean.weight: (9, 256)
  act.action_out.fc_mean.bias:   (9,)
  act.action_out.log_std:        (9,)
```

Interpretation:

- Old assignment checkpoints are fixed N=12 assignment checkpoints: `12 viewpoints + noop = 13`.
- Old scan checkpoints are raw 9D continuous policies.
- N=50 assignment would need `51` categorical logits per agent.

Verdict:

```text
No existing checkpoint inspected here should be evaluated on N=50.
```

## Observation-Space Audit

Current per-agent observation is 96D for the three-agent setup. The shared observation is code-inferred as the
concatenation of per-agent observations and then repeated per agent, so M=3 gives a 288D shared vector per agent.

Current per-agent observation fields:

| field | present | notes |
|---|---|---|
| robot base relative position | yes | normalized by env spacing |
| robot yaw sin/cos | yes | local robot state |
| scanner relative position | yes | normalized by env spacing |
| scanner quaternion | yes | local scanner state |
| global coverage ratio | yes | scalar only, not per-viewpoint completion vector |
| robot capability features | yes | reach/range/FOV summary |
| nearest uncovered viewpoint slots | yes | 8 slots, each rel xyz + quat + valid |
| viewpoint id for nearest slots | no | important gap because actions are absolute ids |
| other scanner relative positions | yes | current inter-robot geometry only |
| previous 9D continuous action | yes | previous low-level action, not previous assignment id |
| full available action mask | separate mask | used by HARL policy distribution, not part of observation features |
| full cost matrix | no | available only in assignment problem/evaluator |
| task status vector | no | problem has unassigned/completed, obs does not |
| robot status beyond current pose | no | problem reports idle at reset; dynamic statuses are not used as policy state |
| no-progress state | no | not exposed |
| attempted/repeated viewpoint history | no | not exposed |
| current assigned target memory | no | not exposed |
| selected-target conflict | diagnostics only | not exposed to policy |
| inter-robot overlap risk | diagnostics only | not exposed to policy |
| actual base-motion crossing risk | evaluator diagnostics only | not exposed to policy |
| load-balance proxy | no | not exposed |

Readiness interpretation:

```text
The observation can support a fixed-size smoke, but it is weak for learning dynamic assignment at N=50 and is not
designed for arbitrary-size viewpoint sets.
```

The biggest mismatch is that the policy outputs an absolute viewpoint id, but the nearest-viewpoint observation slots
do not include the corresponding viewpoint ids. For fixed N, a policy may memorize id-specific logits from a static
scenario. For arbitrary N or shuffled/generated viewpoint sets, this representation is not robust.

## Action And Mask Audit

| question | current status | evidence |
|---|---|---|
| Are covered viewpoints masked? | yes | `available_mask = feasible_mask & (~viewpoints_covered[:, None, :])` |
| Are infeasible viewpoints masked? | yes | `available_mask` is based on `assignment_feasible_mask_base` |
| Is static feasibility used? | yes | `assignment_feasible_mask_base` is cloned from static geometric feasibility |
| Is noop available? | always | mask appends an all-ones noop column |
| Is duplicate assignment prevented? | no | masks are per-agent; two agents may select same uncovered viewpoint |
| Is duplicate assignment diagnosed? | yes | wrapper computes `duplicate_count` in `info["assignment_rl"]` |
| Are invalid out-of-range ids accepted? | no in strict decode | strict decode raises outside `[0, N]` |
| Are unavailable but in-range ids hard-blocked after decode? | controller returns zero action | if bypassed, covered/infeasible targets become zero actions |
| Can policy distinguish why an action is masked? | no | mask merges covered and infeasible reasons |
| Can policy distinguish failed/timeout/unreachable states? | no meaningful current path | status constants exist, but current task state is unassigned/completed |

Mask verdict:

```text
Mask shape and HARL plumbing are ready. Mask semantics are minimal and do not encode conflict, progress, retry, or
load-balance state.
```

## Reward Audit

| reward concept | current status | evidence/source | recommendation |
|---|---|---|---|
| coverage gain | present | `global_coverage_reward_scale * last_global_coverage_gain` | keep as core signal |
| per-agent own coverage credit | present | `own_coverage_reward_scale * last_own_coverage_gain` | keep, but review credit assignment for simultaneous scans |
| completion bonus | absent | termination on all covered, no separate bonus | consider later if sparse success remains hard |
| invalid action penalty | absent | strict decode rejects out-of-range; covered/infeasible target becomes zero action if bypassed | add only in a scoped reward phase if invalid choices are possible in policy path |
| duplicate assignment penalty | absent | wrapper logs duplicate assignment, reward does not use it | important Phase 8 failure-mode candidate |
| duplicate scan penalty | present | `duplicate_scan_penalty_scale * last_duplicate_scans` | this is not the same as duplicate assignment |
| noop penalty | absent | noop is zero action; only time penalty applies | consider if noop abuse appears |
| no-progress penalty | absent | no coverage-gain stagnation term | important before meaningful RL eval |
| repeated assignment penalty | absent | no assignment history in reward | important before meaningful RL eval |
| selected-target conflict penalty | absent | diagnostic/evaluator only | keep diagnostic for comparison; consider later reward feature |
| inter-robot overlap penalty | absent | diagnostic only | keep diagnostic for comparison; consider later reward feature |
| actual base-motion crossing penalty | absent | evaluator diagnostic only | keep diagnostic for comparison; consider later reward feature |
| load-balance reward/penalty | absent | no per-robot completion balance term | add reporting first; reward later if needed |
| path-cost penalty | absent | `cost_matrix` not used in reward | consider compact cost shaping later |
| reach violation penalty | present | `reach_violation_penalty_scale * last_reach_violation` | keep |
| action smoothness/rate penalty | present | `action_rate_penalty_scale * action_rate` | keep |
| time penalty | present | constant `time_penalty` | keep |

Reward verdict:

```text
Reward is coverage-oriented and can train basic scanning behavior, but it does not directly address the Phase 8
plateau mechanisms.
```

## Diagnostics To Carry Into RL Reporting

Carry forward from Phase 8:

```text
final_coverage
coverage_auc
success_rate
selected_target_conflict_rate
inter_robot_overlap_rate
actual_base_motion_intersection_rate
last_coverage_gain_step
no_progress_steps_after_last_gain
final_uncovered_viewpoint_ids
late_repeated_assignment_pattern
selected_intersection_rate
selected_obstacle_penalty_sum
valid_action_rate
noop_rate
```

Add as reporting-only before reward changes:

```text
per_robot_completed_count
per_robot_selected_count
load_balance proxy
per_robot repeated assignment count
per-viewpoint attempted count
assignment duplicate rate
masked-action selection diagnostics, if policy path can surface them
```

## Readiness Answers

1. Current RL/HARL wrapper supports N=50, M=3 without shape mismatch in the one-step smoke.
2. Current observations do not expose enough state to confidently avoid Phase 8 stagnation.
3. Current action masks reflect basic feasible-and-uncovered assignment semantics.
4. Current reward encourages coverage but does not penalize repeated/no-progress behavior directly.
5. Phase 8 diagnostics should be carried into any RL comparison, especially conflict, overlap, crossing, stagnation,
   noop, and valid-action metrics.
6. Existing checkpoints are incompatible with N=50.
7. Minimum pre-Phase-9B decision: either run only a no-checkpoint N=50 actor/wrapper construction smoke, or first scope
   an observation/reward design phase before any meaningful RL evaluation/retraining.

## Recommended Next Step

Do not evaluate old checkpoints on N=50.

For a very small Phase 9B technical smoke, instantiate a fresh N=50 assignment actor path and verify action/mask tensor
flow without claiming policy quality.

For meaningful dynamic-policy work, first scope a compact observation/reward design update that addresses:

```text
viewpoint id/action mapping
full or compact cost features
no-progress and repeated-attempt memory
current assignment/target memory
load-balance reporting
conflict/crossing risk as observation or reward-design candidate
episode horizon alignment around 300 steps
```

