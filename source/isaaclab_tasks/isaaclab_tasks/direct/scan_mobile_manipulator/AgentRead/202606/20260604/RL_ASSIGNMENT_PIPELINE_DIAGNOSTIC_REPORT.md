# RL Assignment-to-Motion Pipeline Diagnostic Report

## 1. Executive summary

- Most likely failure cases:
  - Case F: RL evaluation/training does not use `assignment_controller` at all.
  - Case K: Existing RL play/eval logs are insufficient to determine raw action, movement, distance decrease, or coverage failure without adding diagnostics.
- Confidence:
  - Case F: high.
  - Case K: high.
- Main evidence:
  - The scan env exposes each robot as a 9D continuous action agent: `action_spaces = {"robot_0": 9, "robot_1": 9, "robot_2": 9}` in `scan_mobile_manipulator_env.py:45-47`.
  - Latest 10M actor checkpoint output layer is 9D: `act.action_out.fc_mean.weight (9, 256)`, `bias (9,)`, `log_std (9,)`.
  - HARL `play.py` calls `runner.actor[agent_id].get_actions(..., None, True)` and then `runner.env.step(actions)` directly; there is no assignment decoding step in `scripts/reinforcement_learning/harl/play.py:123-134`.
  - HARL IsaacLab wrapper converts the tensor action directly into a per-agent action dict and calls the underlying env: `env_wrappers.py:488-490`.
  - `viewpoint_assignment_to_actions` is only used by baseline/viewer scripts, not by HARL train/play.
- What could not be verified without code changes:
  - RL raw 9D actions during play/eval.
  - Whether RL 9D actions are near zero, saturated, oscillatory, or otherwise ineffective.
  - Per-step base/scanner displacement under the 10M checkpoint.
  - Distance-to-nearest/target viewpoint decrease for RL.
  - Why RL play visually appears not to reach viewpoints, beyond the fact that it is not using the assignment controller.

## 2. Repository state

- Initial `git status --short`:

```text
 M assets/instanceable.py
 M scripts/reinforcement_learning/harl/play.py
 M scripts/reinforcement_learning/harl/train.py
?? assets/assets.zip
?? scripts/environments/codex_compare_assignment_baselines.md
?? scripts/environments/env_readme.md
?? scripts/environments/evaluate_scan_assignment.py
?? scripts/environments/view_direct_marl_env.py
?? scripts/environments/view_scan_assignment.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
```

- Final `git status --short`:

```text
 M assets/instanceable.py
 M scripts/reinforcement_learning/harl/play.py
 M scripts/reinforcement_learning/harl/train.py
?? assets/assets.zip
?? scripts/environments/codex_compare_assignment_baselines.md
?? scripts/environments/env_readme.md
?? scripts/environments/evaluate_scan_assignment.py
?? scripts/environments/view_direct_marl_env.py
?? scripts/environments/view_scan_assignment.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
```

  The final status text is the same as the initial status because the report lives inside the already-untracked `scan_mobile_manipulator/` parent directory.
- Files modified by this task:
  - None in source code, configs, README, controller, solver, reward, or training logic.
- Files created by this task:
  - `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/RL_ASSIGNMENT_PIPELINE_DIAGNOSTIC_REPORT.md`
- Existing dirty state:
  - The repository was already dirty before this task. Existing `.py` modifications and untracked files were not changed or reverted.

## 3. Commands run

| Command | Purpose | Result |
|---|---|---|
| `Get-Content AgentRead/AGENTS.md` | Read project/task rules | Passed |
| `Get-Content AgentRead/TASK_PROGRESS.md` | Read assignment implementation status | Passed |
| `Get-Content AgentRead/RL_ASSIGNMENT_PIPELINE_READONLY_DIAGNOSTIC_TASK.md` | Read current diagnostic task | Passed |
| `git status --short` | Record initial repository state | Passed; dirty state shown above |
| `rg --files source/.../scan_mobile_manipulator` | Locate scan task files | Passed |
| `rg --files scripts/reinforcement_learning/harl` | Locate HARL train/play scripts | Passed |
| `rg --files scripts/environments` | Locate baseline/viewer scripts | Passed |
| `rg -n "viewpoint_assignment_to_actions|get_assignment_problem|..." ...` | Locate assignment/controller usage | Passed; controller used by baseline/viewer only |
| `rg -n "deterministic|sample|argmax|..." ...` | Locate RL action/checkpoint code | Passed |
| `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"` | Verify project Python | Passed: `C:\isaacenvs\isaac45_harl\python.exe` |
| `python -c "import harl; print(...)"` | Locate installed HARL package | Passed: `C:\isaacenvs\isaac45_harl\lib\site-packages\harl` |
| `Get-Content` on `assignment_controller.py`, `scan_mobile_manipulator_env.py`, solvers, evaluator, HARL play/train, HARL wrapper/model files | Read key implementation | Passed |
| `Get-ChildItem results/.../scan_happo` | Locate scan HAPPO runs and model files | Passed; found 1M and 10M runs |
| `rg -n "10000000|num_env_steps" results/.../configs.json` | Confirm run config | Passed; latest run config has `num_env_steps: 10000000` |
| TensorBoard `EventAccumulator` max-step read | Confirm latest run logged to 10M | Passed: `max_scalar_step 10000000` |
| TensorBoard scalar tail read | Inspect existing aggregate RL metrics | Passed; last coverage `0.0733`, reach violation `0.5002`, entropy still high |
| `torch.load(...actor_agent_robot_0.pt...)` state dict shape read | Confirm checkpoint action output dimension | Passed: 9D Gaussian output |
| `evaluate_scan_assignment.py --solver nearest --num_envs 1 --num_episodes_per_env 1 --max_steps_per_episode 20 --headless` | Lightweight baseline smoke | Passed with exit code 0; stdout dominated by Isaac/Kit startup logs |
| Same nearest command with `--save_csv` to temp file | Get stable baseline result | Passed; temp CSV outside repo |
| Same greedy command with `--save_csv` to temp file | Get stable baseline result | Passed; temp CSV outside repo |
| `Get-Content` temp nearest/greedy CSVs | Read baseline metrics | Passed; both covered 1/12 viewpoint within 20 steps |
| Multi-line TensorBoard scalar command | Attempt scalar tail read | Failed due `conda run` not supporting newlines in `python -c`; retried as one line and passed |

## 4. Pipeline map

```text
Actual RL play path:
10M model_dir
  -> HARL runner restore()
  -> per-agent stochastic Gaussian actor in eval mode
  -> deterministic mean 9D continuous action
  -> HARL IsaacLabEnv.step(actions)
  -> IsaacLabWrapper maps tensor to {robot_i: [num_envs, 9]}
  -> ScanMobileManipulatorEnv.step(actions)
  -> _integrate_high_level_actions()
  -> coverage checks
```

There is no actual RL pipeline of:

```text
RL policy -> viewpoint id assignment -> viewpoint_assignment_to_actions -> 9D action -> env.step
```

The assignment-controller pipeline exists for baselines and viewer scripts, but HARL train/play do not call it.

## 5. Checkpoint and eval mode

- Latest 10M run directory:

```text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\scan_happo\seed-00001-2026-06-03-22-31-48
```

- Latest run config evidence:
  - `configs.json:12`: `"num_env_steps": 10000000`
  - `configs.json:40-49`: train section also records `n_rollout_threads: 4`, `num_env_steps: 10000000`, `model_dir: null`.
- TensorBoard evidence:
  - Event file scalar max step: `10000000`.
  - Last logged values at step 10M:
    - `coverage_ratio`: `0.0733333379`
    - `new_viewpoints`: `0.0040000002`
    - `duplicate_scans`: `0.0013333333`
    - `reach_violation`: `0.5001666546`
    - `mean_reward`: `-0.0075162561`
    - `agent0/dist_entropy`: `6.4261`
    - `agent1/dist_entropy`: `4.5859`
    - `agent2/dist_entropy`: `6.3725`
- Model files found in latest 10M run:
  - `best_model/actor_agent_robot_0.pt`
  - `best_model/actor_agent_robot_1.pt`
  - `best_model/actor_agent_robot_2.pt`
  - `best_model/critic_agent.pt`
  - `best_model/value_normalizer.pt`
  - same filenames under `models/`.
- Loading method:
  - `play.py:78-80` sets `algo_args["train"]["model_dir"] = args["dir"]`.
  - HARL runner calls `restore()` when `model_dir` is not `None` in `on_policy_base_runner.py:185-187`.
  - `restore()` loads `actor_agent_{robot_id}.pt` from `model_dir` in `on_policy_base_runner.py:845-879`.
- Is the loaded checkpoint path printed clearly?
  - Not on successful restore. The code prints errors if a file cannot be loaded, but it does not print a positive "loaded checkpoint" message.
  - `play.py` has a comment example pointing to the latest 10M `best_model` path at `play.py:8`.
- Is the actor placed in eval mode?
  - Yes. `play.py:120-121` calls `actor.prep_rollout()`, and HARL `OnPolicyBase.prep_rollout()` calls `self.actor.eval()` in `on_policy_base.py:136-138`.
- Deterministic or stochastic?
  - `play.py` passes `True` as the deterministic argument in `get_actions(..., None, True)` at `play.py:127-129`.
  - HARL `get_actions(..., deterministic=False)` documents this parameter as "mode of distribution" vs sampled in `on_policy_base.py:53-68`.
  - For Box actions, HARL uses `DiagGaussian`; deterministic mode returns the Normal mean via `FixedNormal.mode()` in `distributions.py:33-34`.
  - Training collection is stochastic because HARL `collect()` does not pass `deterministic=True` in `on_policy_base_runner.py:347-354`.

## 6. RL action semantics

- RL action space shape:
  - Per agent: 9.
  - HARL action tensor in play: `[num_envs, num_agents, max_action_space]` from `play.py:101`.
- Action type:
  - Continuous Box action.
  - HARL `ACTLayer` maps Box spaces to `DiagGaussian` in `act.py:29-33`.
- Checkpoint actor output:
  - `act.action_out.fc_mean.weight`: `(9, 256)`
  - `act.action_out.fc_mean.bias`: `(9,)`
  - `act.action_out.log_std`: `(9,)`
- Semantics:
  - The 9D action is `[base_dx, base_dy, base_dyaw, ee_dx, ee_dy, ee_dz, ee_droll, ee_dpitch, ee_dyaw]` per `scan_mobile_manipulator_env.py:34-36`.
  - These are normalized increments, clamped in `_pre_physics_step()` and integrated in `_integrate_high_level_actions()`.
- There is no decoded `assignment: torch.long`.
- Therefore the checks `dtype == torch.long`, `shape == [num_envs, num_agents]`, and viewpoint id range do not apply to the current RL path.

## 7. Whether RL calls assignment_controller

- RL training path:
  - `scripts/reinforcement_learning/harl/train.py` does not import or call `viewpoint_assignment_to_actions`.
  - It creates a HARL runner and calls `runner.run()` in `train.py:153-164`.
  - HARL `collect()` samples/records continuous actions from actor policies in `on_policy_base_runner.py:334-398`.
- RL play path:
  - `scripts/reinforcement_learning/harl/play.py` does not import or call `viewpoint_assignment_to_actions`.
  - It calls each actor, writes the raw action into `actions`, and calls `runner.env.step(actions)` in `play.py:123-134`.
- Baseline path:
  - `scripts/environments/evaluate_scan_assignment.py:53` imports `viewpoint_assignment_to_actions`.
  - `evaluate_scan_assignment.py:344-354` calls `get_assignment_problem()`, solver, assignment validation, controller, action validation, then `env.step(actions)`.
- Pipeline classification:
  - Current RL is Pipeline B: `RL policy -> 9D continuous action directly -> env.step`.
  - Baseline is: `solver assignment -> assignment_controller -> 9D action -> env.step`.

## 8. Assignment validity and zero-action behavior

- Controller contract:
  - `assignment_controller.py:39-49` expects `assignment` as a long tensor `[num_envs, num_agents]`.
  - `assignment_controller.py:58-61` raises if dtype or shape is wrong.
- Invalid conditions:
  - Out of range: `assignment < 0` or `assignment >= num_viewpoints` fails `in_range`.
  - Already covered target: `target_covered`.
  - Infeasible target for that robot: `not target_feasible`.
  - Valid mask is `in_range & (~target_covered) & target_feasible` in `assignment_controller.py:73-80`.
- Invalid behavior:
  - Invalid, covered, infeasible, or `-1` no-op entries are converted to exact zero action by `torch.where(valid.unsqueeze(-1), actions, torch.zeros_like(actions))` in `assignment_controller.py:106-108`.
- Duplicate handling:
  - The controller does not prevent duplicate assignments across robots.
  - Baseline solvers avoid duplicates within each env step using a per-env `selected` mask:
    - nearest: `nearest_solver.py:32-44`
    - greedy: `greedy_solver.py:34-46`
    - random: `random_solver.py:31-43`
- RL duplicate/covered/infeasible assignment behavior:
  - Not applicable to the current RL path because RL does not output assignment ids.
  - If future RL is changed to output assignment ids, these invalid cases would matter immediately.

## 9. Action mask / feasibility mask usage

- Assignment problem masks exist:
  - `get_assignment_problem()` returns `feasible_mask` and `available_mask` in `scan_mobile_manipulator_env.py:211-231`.
- Baselines use masks:
  - Solvers consume `available_mask`.
  - Evaluator validates solver choices against `available_mask` in `evaluate_scan_assignment.py:116-135`.
- RL does not use assignment masks:
  - HARL wrapper `reset()` returns `available_actions = None` in `env_wrappers.py:459-475`.
  - HARL wrapper `step()` also returns `available_actions = None` in `env_wrappers.py:488-513`.
  - `play.py` passes `None` for available actions in `get_actions()` at `play.py:127-129`.
  - HARL Categorical masking exists only when `available_actions` is passed, but the scan task action space is Box/Gaussian, not Discrete/Categorical.
- RL observation includes some target information but not an action mask:
  - Coverage ratio.
  - Robot capability terms.
  - 8 nearest uncovered viewpoint slots with relative pose and a valid flag.
  - Other scanners.
  - Previous action.
  - It does not expose `available_mask` or `feasible_mask` as a policy action mask.

## 10. Baseline vs RL pipeline comparison

| Pipeline stage | nearest/greedy | RL | Same or different? | Evidence |
|---|---|---|---|---|
| assignment problem source | Uses `env.unwrapped.get_assignment_problem()` | Not used | Different | evaluator `344`; play has no call |
| action type | Discrete viewpoint assignment first, then 9D action | Direct 9D continuous Gaussian action | Different | solvers return long assignment; actor output layer is 9D |
| assignment decode | No decode from policy; solver directly returns ids | None | Different | `play.py:127-134` |
| assignment dtype/shape | Validated as `torch.long [num_envs, num_agents]` | No assignment tensor | Different | evaluator `116-127` |
| validity filtering | `available_mask` in solver plus controller validity | None at assignment level | Different | solvers and controller |
| duplicate avoidance | Solver prevents duplicate same-step viewpoint claims | No assignment-level duplicates exist | Different | solver `selected` masks |
| controller call | Calls `viewpoint_assignment_to_actions` | Does not call | Different | evaluator `350`; rg found no HARL import/call |
| env.step action | 9D action dict from controller | 9D action tensor mapped to dict by HARL wrapper | Partly same after action dict | wrapper `488-490`; evaluator `354` |
| movement model | Same env high-level tensor integration | Same env high-level tensor integration | Same after `env.step` | env `_integrate_high_level_actions()` |
| coverage tracking | Same env coverage buffers | Same env coverage buffers | Same after `env.step` | env `_update_scan_progress()` |
| eval metrics | action norm, coverage, duplicates, reach violations | Only average reward printed by play | Different | evaluator metrics; play `139` |

Short baseline smoke results with 1 env, 1 episode, 20 steps:

| Solver | Coverage | Success | Assignment duplicates | Scan duplicates | Reach violations | Mean action norm |
|---|---:|---:|---:|---:|---:|---:|
| nearest | 0.0833333 | 0 | 0.0 | 1.0 | 0.0 | 2.2549 |
| greedy | 0.0833333 | 0 | 0.0 | 1.0 | 0.0 | 2.2549 |

This 20-step run is intentionally short and does not prove full traversal. It does confirm that the baseline-controller-env path produces nonzero actions and covers at least one viewpoint under the current workspace state.

## 11. Movement and coverage semantics

- State tensors:
  - `base_pos`: `[num_envs, num_agents, 3]`
  - `base_yaw`: `[num_envs, num_agents]`
  - `scanner_pos`: `[num_envs, num_agents, 3]`
  - `scanner_quat`: `[num_envs, num_agents, 4]`
  - `viewpoints_covered`: `[num_envs, num_viewpoints]`
  - Defined in `scan_mobile_manipulator_env.py:161-167`.
- Movement:
  - `_pre_physics_step()` clamps action values to `[-1, 1]` and calls `_integrate_high_level_actions()` in `scan_mobile_manipulator_env.py:412-419`.
  - `_integrate_high_level_actions()` integrates base xy/yaw and scanner xyz/rpy deltas into task-space buffers in `scan_mobile_manipulator_env.py:421-450`.
  - `_apply_action()` does not actuate real simulator robots; it mirrors high-level buffers into USD debug visuals when needed in `scan_mobile_manipulator_env.py:452-457`.
- Coverage:
  - `_update_scan_progress()` checks scanner position error, orientation error, arm reach, sensor range, and FOV in `scan_mobile_manipulator_env.py:534-586`.
  - A viewpoint is covered when dwell is met and at least one robot satisfies all candidate conditions.
  - Duplicate scans are counted when candidate views are already covered.
- Important interpretation:
  - Visible robot marker motion and internal task-space tensor motion are related only through debug marker sync. The current environment is not yet a real PhysX articulation control task.

## 12. Reward and learning signal inspection

- Reward terms in `_get_rewards()`:
  - Positive global coverage gain.
  - Positive own robot coverage contribution.
  - Negative duplicate scan penalty.
  - Negative reach violation penalty.
  - Negative action-rate penalty.
  - Negative time penalty.
  - Implemented in `scan_mobile_manipulator_env.py:588-599`.
- Logs exposed through `info["log"]`:
  - `coverage_ratio`
  - `new_viewpoints`
  - `duplicate_scans`
  - `reach_violation`
  - `mean_reward`
  - Implemented in `scan_mobile_manipulator_env.py:603-612`.
- No distance-to-target shaping reward was found.
- No assignment-validity reward exists because the RL action is not an assignment.
- Analytical note:
  - Before the first viewpoint is covered, the reward can be weak or mostly negative. This may make the direct 9D continuous control problem hard, especially because coverage requires position, orientation, FOV, range, and reach conditions simultaneously.

## 13. Observation content inspection

- Per-agent observation is 96D in `scan_mobile_manipulator_env.py:49-51`.
- Observation layout is documented in code at `scan_mobile_manipulator_env.py:463-499`:
  - own base relative position
  - own yaw sin/cos
  - own scanner relative position
  - own scanner quaternion
  - global coverage ratio
  - capability terms: arm reach, scanner min/max range, FOV cosine
  - nearest viewpoint slots: 8 slots times `[rel_x, rel_y, rel_z, qw, qx, qy, qz, valid]`
  - other scanners relative positions
  - previous action
- The nearest-viewpoint observation masks covered viewpoints by setting their distance high, then returns up to 8 nearest uncovered slots in `scan_mobile_manipulator_env.py:504-526`.
- Limitations for choosing valid high-level viewpoints:
  - There are 12 total viewpoints but only 8 nearest slots in observation.
  - The observation does not include discrete viewpoint ids.
  - The observation does not include `available_mask`/`feasible_mask` as a policy action mask.
  - It may still contain enough geometry for direct continuous control, but it is not an assignment policy interface.

## 14. Failure-case classification

| Case | Applies? | Confidence | Evidence | Missing evidence |
|---|---|---|---|---|
| Case A: RL assignments are mostly invalid and converted to zero actions | No for current RL path | High | RL has no assignment ids and does not call controller | If future assignment-RL exists, raw assignment/valid logs are needed |
| Case B: RL assignments are valid, but controller actions are near zero | No for current RL path | High | Controller not used by RL | Future assignment-controller action norms |
| Case C: RL assignments are valid and controller actions are nonzero, but env.step produces little/no movement | No for assignment path; unknown for direct 9D RL | Medium | Env integrates direct 9D actions; no RL action/movement logs | RL action norms and base/scanner delta |
| Case D: RL assignments are valid and robots move, but distance to assigned viewpoints does not decrease | No for assignment path; unknown for direct 9D RL | Medium | RL has no assigned viewpoint id | A target definition for direct 9D RL and distance logs |
| Case E: RL assignments are valid, robots move toward viewpoints, but coverage is not triggered | No for assignment path; possible direct-control symptom | Low | Coverage requires strict pose/range/FOV checks; no RL movement logs | Per-step pose error, rot error, FOV, range, dwell logs |
| Case F: RL eval/training does not use assignment_controller at all | Yes | High | HARL train/play do not call `viewpoint_assignment_to_actions`; wrapper passes 9D actions directly to env | None |
| Case G: RL eval is stochastic and high-entropy | Current play/evaluate: no; training: stochastic | High for play being deterministic | `play.py` passes deterministic `True`; HARL evaluate also passes deterministic `True`; training collect samples | If a different eval script was used, inspect that command |
| Case H: RL repeatedly assigns duplicate viewpoints | No for current RL path | High | No assignment ids | Future assignment logs if interface changes |
| Case I: RL repeatedly assigns already covered viewpoints | No for current RL path | High | No assignment ids | Future assignment logs if interface changes |
| Case J: RL assigns infeasible viewpoints to heterogeneous robots | No for current RL path | High | No assignment ids | Future assignment logs if interface changes |
| Case K: Existing logs/scripts are insufficient to determine runtime failure without diagnostics | Yes | High | Existing RL play prints only average reward; TensorBoard logs aggregate reward/coverage/entropy only | Raw action, movement, distance, coverage condition logs |

Selected cases:

- Case F:
  - confidence: high
  - evidence: RL policy outputs 9D continuous Gaussian actions and passes them directly to env.
  - missing evidence: none for pipeline classification.
  - recommended next task: decide whether RL should learn assignment ids or direct 9D control.
- Case K:
  - confidence: high
  - evidence: no existing RL play/eval log exposes raw action, action norm, movement, distance decrease, or per-condition coverage checks.
  - missing evidence: runtime tensors listed in Section 15.
  - recommended next task: add a minimal diagnostic eval mode or separate read-only evaluator script once code changes are allowed.

## 15. Minimal future diagnostic instrumentation, if needed

Only future changes are listed here. Nothing below was implemented in this task.

For direct 9D RL evaluation, add or expose:

- checkpoint path successfully loaded
- per-agent raw 9D action
- clamped 9D action
- action norm and action delta
- base position/yaw before and after `env.step`
- scanner position/quaternion before and after `env.step`
- per-step base/scanner displacement
- nearest-uncovered viewpoint id and distance before/after step
- min pose error, min rotation error, FOV pass, sensor-range pass, arm-reach pass
- newly covered viewpoint count
- coverage ratio
- reach violation

If the intended design is assignment-based RL instead, add or expose:

- raw policy logits/probabilities
- action mask before sampling/selection
- decoded `assignment`
- assignment dtype, shape, device
- `in_range`
- `target_covered`
- `target_feasible`
- duplicate assignment count
- controller output action norm
- distance-to-assigned-viewpoint before/after

## 16. Commands not run and reasons

- Did not run HARL `play.py` with the 10M checkpoint.
  - Reason: current `play.py` loops while `simulation_app.is_running()` and has no visible max-step or max-episode CLI cap. Running it would not be a bounded lightweight diagnostic.
- Did not run training or resume training.
  - Reason: explicitly forbidden by task.
- Did not run long baseline evaluation.
  - Reason: the requested diagnosis only needed a short smoke plus code inspection; longer runs would be outside the minimal read-only scope.
- Did not add debug prints, CLI flags, wrappers, masks, reward changes, or controller changes.
  - Reason: explicitly forbidden by task.

## 17. Conclusion

The strongest conclusion is that the reported RL checkpoint is not failing because its discrete viewpoint assignments are invalid and zeroed by `assignment_controller`. In the current code, RL does not produce discrete viewpoint assignments and does not call `viewpoint_assignment_to_actions`.

The current RL path is a direct 9D continuous control policy. Baselines succeed through a different front half of the pipeline: they solve a masked viewpoint assignment problem, avoid duplicates, convert assignments through the scripted controller, and then use the same env 9D action interface. Therefore baseline success proves the controller-env path can work for valid handcrafted assignments, but it does not prove that the RL policy is using that path.

The latest scan HAPPO run is confirmed as a 10M-step run by both `configs.json` and TensorBoard max scalar step. The available play/eval code uses deterministic actor means, not stochastic sampling, but it does not log enough runtime tensors to determine whether the direct 9D policy outputs near-zero actions, ineffective actions, movement that does not reduce viewpoint distance, or motion that reaches pose but fails coverage conditions.
