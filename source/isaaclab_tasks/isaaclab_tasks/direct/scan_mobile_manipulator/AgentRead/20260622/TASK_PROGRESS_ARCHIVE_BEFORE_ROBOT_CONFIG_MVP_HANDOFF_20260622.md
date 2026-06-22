# TASK_PROGRESS

This is the compact handoff for the assignment-based RL scan-mobile-manipulator work.

## Current Status

Status: Stage 4A evaluator extension is complete after a metric-correctness follow-up fix. Manual broader/visual
validation found that timeout/done handling could falsely report full coverage. `evaluate_assignment_methods.py` now
supports scenario YAML config input and external fixed-N viewpoint CSVs for baseline-only evaluation (`random`,
`nearest`, `greedy`) and records coverage/success from actual covered viewpoint state. The fixed-12 default evaluator
path remains available as a regression path.

Current real component assets and scenario entrypoints:

```text
OBJ:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj

Generated pipeline sanity CSV:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv

Scenario YAMLs:
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_visual.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/generate_real_component_bbox_sample_csv.yaml
```

Important current facts:

- Real component world convention: `model base center = world origin`.
- Real generated sample scenario: `N=24`, `noop_id=24`, `available_actions_shape=(1, 3, 25)`.
- `real_component_bbox_sample.csv` is pipeline sanity / smoke data only, not final viewpoint planning output and not a
  final algorithm performance benchmark.
- Fixed-12 default path is preserved; the fixed-12 manual override for the known `robot_2 -> viewpoint_5` special case
  remains active with cached Level 2 reason:
  `level2_controller_diagnostic_position_rotation_gates_never_simultaneously_satisfied`.
- `evaluate_assignment_methods.py` is Stage 4A fixed-N capable for `random`, `nearest`, and `greedy` only.
- Evaluator coverage metrics must be interpreted from the fixed metric outputs, not the earlier
  `stage4b_real_component_n24_bounded_eval` files generated before this fix.
- Stage 4B issue assessment has been documented for the generated real-component N=24 scenario. With the fixed
  evaluator, nearest/greedy cover 17/24 viewpoints and leave `[1, 2, 8, 12, 13, 14, 20]` uncovered; this is a
  diagnostic finding on temporary generated bbox-side data, not a final algorithm performance conclusion.
- Stage 4B Level 2 controller diagnostics have been run for those seven uncovered N=24 viewpoint ids across agents
  `0/1/2`. All seven viewpoints are coverable by at least one robot under current controller/gates, but several
  static-feasible agent-viewpoint pairs fail because position and rotation gates are satisfied individually but not
  simultaneously.
- Assignment-history diagnostics have been added to `evaluate_assignment_methods.py` and verified on generated
  real-component N=24. Nearest/greedy skip target viewpoints `2/8/14/20`, repeatedly assign `1/12/13`, and remain stuck
  at `17/24` coverage through timeout.
- Stage 4B top-k candidate ablation is complete. The original nearest-8 limit affects RL/local observation only, not the
  evaluator baseline solver candidate set or `available_actions`; explicit top-k=8 and all-viewpoints evaluator runs both
  remain at `17/24`, and `2/8/14/20` are still never assigned.
- Stage 4B assignment-history/Level-2 join is complete. For target assignments, nearest/greedy send `760` rows to known
  Level-2-failing pairs and `460` rows to known-coverable pairs; the final stuck pattern has two known failing pairs and
  one known-coverable pair per method. Primary next step is a controlled pair-level feasibility filtering experiment.
- Stage 4B controlled pair-level feasibility filtering experiment is complete. The optional evaluator-only
  `--level2_pair_filter_json` mode removes known Level-2-failing target assignments (`760 -> 0`) and improves
  nearest/greedy generated N=24 coverage from `17/24` to `19/24`, but full coverage is still not reached.
- Stage 4B controlled pair-filter + retry/fallback experiment is complete. The optional evaluator-only
  `--assignment_retry_fallback` mode makes previously skipped target ids `2/13/14` get assigned, but coverage remains
  `19/24`; no-op rate increases and the remaining issue is known-coverable pairs that still fail in full-episode
  multi-agent context.
- Stage 4B full-episode controller-state trace is complete. For traced known-coverable pairs, nearest/greedy still remain
  at `19/24`; `robot_1 -> viewpoint_1/2/13/14` reach position/range but never rotation, while `robot_2 -> viewpoint_12`
  reaches position/rotation/range/FOV individually but never position+rotation simultaneously.

No assignment-RL training or evaluation was added. No HARL core, reward, `assignment_controller.py`, underlying 9D action
space, real robot, IK, collision, raycast, or installed `site-packages` change was performed.

## Latest Completed Phase

Stage 4B full-episode controller-state / target-switching trace for generated real-component N=24:

- Modified `scripts/environments/evaluate_assignment_methods.py` to add optional full-rollout trace flags:
  `--write_controller_state_trace`, `--controller_trace_pairs`, and `--controller_trace_agent_viewpoint_pairs`.
- The trace is diagnostic-only and records selected target pairs at every evaluator step; it does not change baseline
  action selection, controller behavior, reward, environment feasibility, HARL core, or the 9D action path.
- Generated `controller_state_trace.csv` and `controller_state_trace_summary.csv` for traced pairs
  `robot_1 -> viewpoint_1`, `robot_2 -> viewpoint_12`, `robot_1 -> viewpoint_2`, `robot_1 -> viewpoint_14`, and
  `robot_1 -> viewpoint_13`.
- All requested pose/gate fields were available in the full evaluator rollout; no trace fields were unavailable.
- Key result: nearest and greedy remain at `19/24` coverage with uncovered ids `[1, 2, 12, 13, 14]`.
- Key result: for `robot_1 -> viewpoint_1/2/13/14`, position and range gates become true but rotation never becomes true;
  several also never satisfy FOV alignment.
- Key result: for `robot_2 -> viewpoint_12`, position, rotation, range, and FOV gates each become true at some point, but
  `position_rotation_gate_ok` never becomes true. This resembles the earlier fixed-12 simultaneous-gate timing issue.
- Interpretation: the remaining issue is no longer never-assigned targets or known Level-2-failing pairs. It is now a
  full-episode controller/gate timing or orientation-convergence issue for Level-2-coverable pairs.

Stage 4B controlled pair-filter + retry/fallback experiment for generated real-component N=24:

- Fixed a text-only inconsistency in
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_JOIN_REPORT.md`:
  the filtered run has `known_level2_failing_pair=0`, so the remaining issue is not dominated by known failing pairs.
- Modified `scripts/environments/evaluate_assignment_methods.py` to add optional evaluator-only retry/fallback mode:
  `--assignment_retry_fallback`, `--assignment_stall_window`, and `--assignment_pair_cooldown`.
- The retry/fallback policy is `consecutive_same_pair_no_coverage_gain`: if one env/agent holds the same uncovered
  viewpoint for the stall window without coverage gain, only that env/agent/viewpoint pair is cooled down in the
  evaluator solver mask for the configured cooldown duration.
- This mode is episode-local, affects only baseline solver candidate selection, and does not modify default environment
  feasibility, controller math, reward, HARL core, or the 9D action path.
- Diagnostics now include retry/fallback enable flag, stall window, cooldown duration, policy name, cooldown event counts
  by method and pair, final active cooldowns, and `retry_fallback_events.csv`.
- Key result: pair-filter + retry/fallback still gives `19/24` coverage for both nearest and greedy; final uncovered ids
  remain `[1, 2, 12, 13, 14]`.
- Key result: previously skipped target ids `2/13/14` are now assigned. Per method assignment counts become
  `1=61`, `2=30`, `8=15`, `12=155`, `13=45`, `14=54`, `20=84`.
- Key result: cooldown events total `16` (`8` nearest, `8` greedy). The previous stuck pairs
  `robot_1 -> viewpoint_1` and `robot_2 -> viewpoint_12` are cooled down, but full coverage is still not reached.
- No-op rate increases from `0.125975` to `0.185061`; final pattern changes to `robot_0 -> noop`,
  `robot_1 -> viewpoint_1`, `robot_2 -> noop`.
- Interpretation: retry/fallback is useful diagnostically because it removes the never-assigned issue, but this simple
  cooldown rule is insufficient. The remaining issue likely needs controller-state / target-switching / multi-agent
  context diagnostics for known-coverable pairs in the full evaluator episode.

Stage 4B controlled pair-level feasibility filtering experiment for generated real-component N=24:

- Modified `scripts/environments/evaluate_assignment_methods.py` to add optional evaluator-only
  `--level2_pair_filter_json`.
- The filter reads Level 2 diagnostic JSON and denies only `(agent_id, viewpoint_id)` pairs with `covered=false`.
  Pairs with `covered=true` stay allowed; unchecked pairs remain unchanged. This affects baseline solver candidate
  selection only and does not modify environment static feasibility.
- Diagnostics now include `level2_pair_filter_enabled`, `level2_pair_filter_json`, loaded/denied/allowed pair counts,
  `denied_pairs`, `allowed_pairs`, and `unchecked_pairs_policy="unchanged"`.
- Ran all-viewpoints control and pair-filtered nearest/greedy N=24 bounded evaluations with assignment history enabled.
- Key result: pair filtering improves both nearest and greedy from `17/24` to `19/24`, with uncovered ids changing from
  `[1, 2, 8, 12, 13, 14, 20]` to `[1, 2, 12, 13, 14]`.
- Key result: known Level-2-failing target assignments drop from `760` to `0`; known-coverable target assignments rise
  from `460` to `994`; no-op rows appear (`226` total).
- New filtered stuck pattern for both nearest and greedy:
  - `robot_0 -> noop`
  - `robot_1 -> viewpoint_1`: `known_coverable_pair`
  - `robot_2 -> viewpoint_12`: `known_coverable_pair`
- Interpretation: pair-level controller-aware feasibility is useful but insufficient. The remaining issue now involves
  skipped coverable targets (`2/13/14`) and known-coverable pairs that still fail to cover in the multi-agent episode
  (`1/12`).

Stage 4B assignment-history / Level 2 pair-coverability join for generated real-component N=24:

- Added `scripts/environments/analyze_assignment_history_with_level2.py`.
- The script joins `assignment_history.csv` rows with Level 2 pair diagnostics and labels each assignment as
  `known_coverable_pair`, `known_level2_failing_pair`, `unchecked_pair`, `noop`, or `already_covered`.
- Generated:
  - `results/assignment_evaluation/stage4b_real_component_n24_assignment_level2_join/assignment_history_joined.csv`
  - `results/assignment_evaluation/stage4b_real_component_n24_assignment_level2_join/assignment_history_pair_summary.csv`
  - `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_LEVEL2_JOIN_REPORT.md`
- Overall counts: `known_coverable_pair=460`, `known_level2_failing_pair=760`, `unchecked_pair=574`, `noop=0`,
  `already_covered=0`. The unchecked rows are non-target assignments because Level 2 was run only on target ids.
- Target-only counts: `known_coverable_pair=460`, `known_level2_failing_pair=760`, `unchecked_pair=0`, `noop=0`,
  `already_covered=0`.
- Target summary: never assigned ids remain `[2, 8, 14, 20]`; repeatedly assigned but not covered ids are `[1, 12, 13]`.
- Final stuck pattern for both nearest and greedy:
  - `robot_0 -> viewpoint_12`: `known_level2_failing_pair`
  - `robot_1 -> viewpoint_13`: `known_coverable_pair`
  - `robot_2 -> viewpoint_1`: `known_level2_failing_pair`
- Interpretation: nearest/greedy are substantially affected by assigning known Level-2-failing pairs, while still also
  skipping coverable viewpoints and failing to realize at least one known-coverable stuck pair in the multi-agent episode.

Stage 4B top-k candidate ablation for generated real-component N=24:

- Inspected the candidate path. `num_viewpoints_in_observation=8` is used for nearest-slot observation features, while
  `get_assignment_problem()` exposes the full fixed-N available mask to baseline solvers.
- Added `--viewpoint_candidate_top_k` to `scripts/environments/evaluate_assignment_methods.py`.
  - `K > 0`: restrict each env/agent solver candidate mask to nearest currently available `K` viewpoints.
  - `K <= 0`: use all currently available/feasible/uncovered viewpoints.
- Added diagnostics fields `viewpoint_candidate_top_k` and `candidate_mode`; diagnostics still report `num_viewpoints`,
  `noop_id`, and `available_actions_shape`.
- Added optional scenario-config smoke default support for `viewpoint_candidate_top_k` in `scenario_config.py`.
- Ran top-k=8 and all-viewpoints nearest/greedy ablations on generated real-component N=24.
- Finding: both candidate modes produce the same result, `final_covered_count=17`, `final_coverage=0.7083333333333334`,
  `success=0`, `final_uncovered_viewpoint_ids=[1, 2, 8, 12, 13, 14, 20]`.
- Finding: target assignment counts are unchanged across modes:
  `v1=167`, `v2=0`, `v8=0`, `v12=253`, `v13=190`, `v14=0`, `v20=0`.
- Interpretation: viewpoint candidate visibility alone does not explain the generated N=24 failure; future Stage 4B
  baseline diagnostics should use all-viewpoints mode for conceptual consistency.

Stage 4B assignment-history diagnostics for generated real-component N=24:

- Modified `scripts/environments/evaluate_assignment_methods.py` to write optional/default `assignment_history.csv`
  beside `per_episode.csv`, `summary.csv`, and `diagnostics.json`.
- The history CSV records method, episode, step, env id, agent id, assigned viewpoint id, no-op, selected availability,
  before/after coverage counts, newly covered viewpoint ids, coverage ratio, and whether the assigned viewpoint was
  already/afterward covered.
- Ran nearest/greedy for one generated real-component N=24 episode with `max_steps=300`.
- Initial finding: nearest and greedy produced the same trace. They never assigned uncovered ids `2`, `8`, `14`, or `20`.
- Initial finding: they repeatedly assigned `1`, `12`, and `13`, but none of those target assignments produced coverage.
- Final repeated stuck pattern:
  - `robot_0 -> viewpoint_12`
  - `robot_1 -> viewpoint_13`
  - `robot_2 -> viewpoint_1`
- Interpretation: the issue includes both skipped coverable viewpoints and retrying/holding stuck assignments without
  fallback; no baseline behavior was changed.

Stage 4B Level 2 controller diagnostics for generated real-component N=24 uncovered viewpoints:

- Extended `scripts/environments/diagnose_assignment_controller_feasibility.py` minimally to support
  `--scenario_config`, `--viewpoint_ids`, and `--agent_ids`, while preserving the existing forced pair rollout through
  the assignment wrapper/controller path.
- Ran target diagnostics for viewpoint ids `[1, 2, 8, 12, 13, 14, 20]` and agent ids `[0, 1, 2]`.
- Main finding: every target viewpoint is coverable by at least one robot:
  - `robot_0` covers `[8, 20]`
  - `robot_1` covers `[1, 2, 8, 13, 14, 20]`
  - `robot_2` covers `[8, 12, 20]`
- Pair-level failures are consistently `position_rotation_gates_never_simultaneously_satisfied`, while position,
  rotation, range, and FOV gates are each individually observed as true.
- Interpretation: static feasibility is not too optimistic at the viewpoint level, but is too optimistic at the
  agent-viewpoint pair level for several target pairs.
- Recommended next step is to join assignment-history rows with Level 2 pair-coverability status.

Stage 4B generated real-component N=24 baseline issue assessment:

- Created a diagnostic report for why the current `random` / `nearest` / `greedy` baselines do not fully cover the
  generated N=24 scenario.
- Main finding: the consistently uncovered viewpoints are clustered on the positive-X face and positive-Y near +X edge;
  static feasibility reports them available for all three agents and no viewpoints are permanently unavailable.
- Assignment-history output now distinguishes skipped viewpoints, repeated stuck assignments, and Level-2-failing pair
  selections for the generated N=24 nearest/greedy run.
- Recommended next diagnostic step: join assignment history with Level 2 pair-coverability status before selecting a
  behavioral fix.

Stage 4A evaluator metric fix after manual validation:

- Manual validation of a broader/visual real-component N=24 run found a metric bug: timeout/done handling could report
  `success=1`, `final_coverage=1.0`, and `final_covered_count=24` even when all 24 viewpoints were not actually covered.
- Fixed evaluator coverage accounting so `final_covered_count` comes from actual `viewpoints_covered` state captured
  before any automatic reset.
- `final_coverage` is now computed as `final_covered_count / num_viewpoints`.
- `success=1` now requires `final_covered_count == num_viewpoints`.
- `steps_to_full_coverage` / `first_full_coverage_step` stay `-1` when full coverage is not reached.
- Added per-episode final covered/uncovered viewpoint id lists and metric consistency checks.

Previously completed Stage 4A evaluator implementation:

- Added `--scenario_config` support to `scripts/environments/evaluate_assignment_methods.py`.
- Reused existing `scenario_config.py` loading, defaults, and validation helpers.
- Added direct fixed-N CSV support via `--viewpoint_csv_path` and `--expect_num_viewpoints`.
- Removed the fixed-12 assertion from external CSV/YAML paths while preserving fixed-12 regression checks for the built-in
  default path.
- Wrote `per_episode.csv`, `summary.csv`, and `diagnostics.json` for evaluator runs.
- Intentionally limited supported methods to `random`, `nearest`, and `greedy`; assignment-RL evaluation is disabled in
  Stage 4A.

Previously completed implementation capabilities:

- Visual-only real OBJ mesh loading.
- Explicit OBJ unit handling (`mm`).
- Scale / rotation / translation-aware world AABB.
- Base-center-to-world-origin alignment.
- Auto bbox proxy from transformed mesh bounds.
- Optional bbox debug visual hiding via `component_proxy_visual_visible`.
- Strict external fixed-N viewpoint CSV loading.
- Generated bbox-side sample viewpoint CSV.
- `static_geometric_v1` feasibility generation.
- Stage 3B bounded Level 2 controller diagnostic.
- Scenario YAML config support for smoke, visual, inspect, and CSV generation scripts.

## Active Architecture / Implementation Path

Assignment path remains:

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

Fixed-N rule:

```text
N loaded viewpoints
noop_id = N
action width = N + 1
available_actions shape = [num_envs, num_agents, N + 1]
```

Checkpoint compatibility:

- Old fixed-12 assignment-RL checkpoints are incompatible with `N=24` or any different N.
- Old 9D continuous checkpoints are incompatible with assignment mode.
- New assignment-RL training should wait until Stage 4 baseline evaluation works on the final fixed-N viewpoint set.

## Key Files

Current handoff and plans:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
```

Core scenario and data files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_mesh.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/viewpoint_csv.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/static_feasibility.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv
```

Useful scripts:

```text
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/generate_bbox_viewpoint_csv.py
scripts/environments/inspect_component_mesh_bounds.py
scripts/environments/test_viewpoint_csv_loader.py
scripts/environments/diagnose_assignment_controller_feasibility.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/analyze_assignment_history_with_level2.py
```

## Latest Verification

Stage 4B controller-state trace verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Full-episode controller-state trace run passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --level2_pair_filter_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --assignment_retry_fallback --assignment_stall_window 30 --assignment_pair_cooldown 60 --write_assignment_history --write_controller_state_trace --controller_trace_pairs 1:1 2:12 1:2 1:14 1:13 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_controller_state_trace`
- Required output files exist under:
  `results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/`
- Markdown report exists:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_CONTROLLER_STATE_TRACE_REPORT.md`

Stage 4B pair-filter + retry/fallback verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Pair-filter control-for-retry evaluator run passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --level2_pair_filter_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_pair_filter_control_for_retry --write_assignment_history`
- Pair-filter + retry/fallback evaluator run passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --level2_pair_filter_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --assignment_retry_fallback --assignment_stall_window 30 --assignment_pair_cooldown 60 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_pair_filter_retry_fallback_ablation --write_assignment_history`
- Retry/fallback Level 2 join analysis passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\analyze_assignment_history_with_level2.py --assignment_history_csv results\assignment_evaluation\stage4b_real_component_n24_pair_filter_retry_fallback_ablation\assignment_history.csv --level2_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --output_dir results\assignment_evaluation\stage4b_real_component_n24_pair_filter_retry_fallback_level2_join --target_viewpoint_ids 1 2 8 12 13 14 20 --report_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\AgentRead\20260615\STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_JOIN_REPORT.md`
- Required output files exist under:
  `results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/`
  `results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/`
  `results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_level2_join/`
- Markdown report exists:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_REPORT.md`

Stage 4B pair-filter ablation verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Control evaluator run passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_no_pair_filter_control --write_assignment_history`
- Pair-filtered evaluator run passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --level2_pair_filter_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_pair_filter_ablation --write_assignment_history`
- Level 2 join summaries were generated for both control and filtered outputs with
  `scripts/environments/analyze_assignment_history_with_level2.py`.
- Required evaluator output files exist under:
  `results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/`
  `results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/`
- Markdown report exists:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_ABLATION_REPORT.md`

Stage 4B assignment-history / Level 2 join verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\analyze_assignment_history_with_level2.py`
- Join analysis passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\analyze_assignment_history_with_level2.py --assignment_history_csv results\assignment_evaluation\stage4b_real_component_n24_assignment_history_check\assignment_history.csv --level2_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json --output_dir results\assignment_evaluation\stage4b_real_component_n24_assignment_level2_join --target_viewpoint_ids 1 2 8 12 13 14 20 --report_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\AgentRead\20260615\STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_LEVEL2_JOIN_REPORT.md`
- Required output files exist under:
  `results/assignment_evaluation/stage4b_real_component_n24_assignment_level2_join/`
- Markdown report exists:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_LEVEL2_JOIN_REPORT.md`

Stage 4B top-k candidate ablation verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scenario_config.py`
- Generated real-component N=24 top-k=8 nearest/greedy bounded ablation passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k 8 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_topk8_ablation --write_assignment_history`
- Generated real-component N=24 all-viewpoints nearest/greedy bounded ablation passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --viewpoint_candidate_top_k -1 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_all_viewpoints_ablation --write_assignment_history`
- Required output files exist under:
  `results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/`
  `results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/`

Stage 4B assignment-history verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Fixed-12 smoke passed and wrote assignment history:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4b_assignment_history_fixed12_smoke --write_assignment_history`
- Generated real-component N=24 nearest/greedy bounded diagnostic passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --methods nearest greedy --num_episodes 1 --max_steps 300 --output_dir results\assignment_evaluation --output_name stage4b_real_component_n24_assignment_history_check --write_assignment_history`
- Required output files exist under
  `results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/`.

Stage 4B Level 2 diagnostic verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\diagnose_assignment_controller_feasibility.py`
- Level 2 diagnostic run passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\diagnose_assignment_controller_feasibility.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --viewpoint_ids 1 2 8 12 13 14 20 --agent_ids 0 1 2 --max_steps 320 --output_json results\assignment_diagnostics\real_component_n24_uncovered_level2_diagnostics.json`
- JSON result exists:
  `results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json`
- Markdown report exists:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_UNCOVERED_LEVEL2_REPORT.md`

Stage 4A metric-fix verification completed by Codex:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Fixed-12 metric regression smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4a_metrics_fixed12_smoke`
- Sample external N=6 metric smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --output_dir results\assignment_evaluation --output_name stage4a_metrics_sample_n6_smoke`
- Real component generated N=24 metric smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4a_metrics_real_component_n24_smoke`
- Real component generated N=24 bounded metric check passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --num_episodes 1 --max_steps 300 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4a_metrics_real_component_n24_bounded_check`

Important bounded metric result after the fix:

```text
random:
  final_covered_count=0
  final_coverage=0.0
  success=0
  steps_to_full_coverage=-1

nearest / greedy:
  final_covered_count=17
  final_coverage=0.7083333333333334
  success=0
  steps_to_full_coverage=-1
  final_uncovered_viewpoint_ids=[1, 2, 8, 12, 13, 14, 20]
```

Earlier Stage 4A verification completed by Codex before the metric follow-up:

- Syntax check passed:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_methods.py`
- Fixed-12 regression smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4a_fixed12_smoke`
- Sample external N=6 smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --headless --device cpu --disable_fabric --num_envs 1 --num_episodes 1 --max_steps 1 --methods random nearest greedy --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --output_dir results\assignment_evaluation --output_name stage4a_sample_n6_smoke`
- Real component generated N=24 scenario smoke passed:
  `D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\evaluate_assignment_methods.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --num_episodes 1 --max_steps 1 --methods random nearest greedy --output_dir results\assignment_evaluation --output_name stage4a_real_component_n24_smoke`

Smoke outcomes:

```text
real component generated sample:
  num_viewpoints=24
  noop_id=24
  available_actions_shape=(1, 3, 25)
  component_proxy_visual_visible=False in mesh-only visual smoke

fixed-12 default:
  num_viewpoints=12
  noop_id=12
  available_actions_shape=(1, 3, 13)
  fixed-12 manual override remains active

sample external N=6:
  num_viewpoints=6
  noop_id=6
  available_actions_shape=(1, 3, 7)
```

Generated evaluator outputs:

```text
results/assignment_evaluation/stage4a_metrics_fixed12_smoke/per_episode.csv
results/assignment_evaluation/stage4a_metrics_fixed12_smoke/summary.csv
results/assignment_evaluation/stage4a_metrics_fixed12_smoke/diagnostics.json
results/assignment_evaluation/stage4a_metrics_sample_n6_smoke/per_episode.csv
results/assignment_evaluation/stage4a_metrics_sample_n6_smoke/summary.csv
results/assignment_evaluation/stage4a_metrics_sample_n6_smoke/diagnostics.json
results/assignment_evaluation/stage4a_metrics_real_component_n24_smoke/per_episode.csv
results/assignment_evaluation/stage4a_metrics_real_component_n24_smoke/summary.csv
results/assignment_evaluation/stage4a_metrics_real_component_n24_smoke/diagnostics.json
results/assignment_evaluation/stage4a_metrics_real_component_n24_bounded_check/per_episode.csv
results/assignment_evaluation/stage4a_metrics_real_component_n24_bounded_check/summary.csv
results/assignment_evaluation/stage4a_metrics_real_component_n24_bounded_check/diagnostics.json
results/assignment_evaluation/stage4a_fixed12_smoke/per_episode.csv
results/assignment_evaluation/stage4a_fixed12_smoke/summary.csv
results/assignment_evaluation/stage4a_fixed12_smoke/diagnostics.json
results/assignment_evaluation/stage4a_sample_n6_smoke/per_episode.csv
results/assignment_evaluation/stage4a_sample_n6_smoke/summary.csv
results/assignment_evaluation/stage4a_sample_n6_smoke/diagnostics.json
results/assignment_evaluation/stage4a_real_component_n24_smoke/per_episode.csv
results/assignment_evaluation/stage4a_real_component_n24_smoke/summary.csv
results/assignment_evaluation/stage4a_real_component_n24_smoke/diagnostics.json
results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json
results/assignment_evaluation/stage4b_assignment_history_fixed12_smoke/per_episode.csv
results/assignment_evaluation/stage4b_assignment_history_fixed12_smoke/summary.csv
results/assignment_evaluation/stage4b_assignment_history_fixed12_smoke/diagnostics.json
results/assignment_evaluation/stage4b_assignment_history_fixed12_smoke/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_assignment_history_check/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_topk8_ablation/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_all_viewpoints_ablation/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_level2_join/assignment_history_joined.csv
results/assignment_evaluation/stage4b_real_component_n24_assignment_level2_join/assignment_history_pair_summary.csv
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control_level2_join/assignment_history_joined.csv
results/assignment_evaluation/stage4b_real_component_n24_no_pair_filter_control_level2_join/assignment_history_pair_summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation_level2_join/assignment_history_joined.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_ablation_level2_join/assignment_history_pair_summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_control_for_retry/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_ablation/retry_fallback_events.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_level2_join/assignment_history_joined.csv
results/assignment_evaluation/stage4b_real_component_n24_pair_filter_retry_fallback_level2_join/assignment_history_pair_summary.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/per_episode.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/summary.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/diagnostics.json
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/assignment_history.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/retry_fallback_events.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/controller_state_trace.csv
results/assignment_evaluation/stage4b_real_component_n24_controller_state_trace/controller_state_trace_summary.csv
```

## Known Issues / Blockers

- Stage 4A evaluator support is baseline-only. It intentionally does not evaluate assignment-RL checkpoints.
- Do not use pre-fix broader outputs such as `results/assignment_evaluation/stage4b_real_component_n24_bounded_eval/` for
  reporting conclusions; those files contain the timeout/full-coverage metric bug.
- In the fixed generated real-component N=24 bounded check, nearest/greedy currently stop at 17/24 coverage with
  uncovered ids `[1, 2, 8, 12, 13, 14, 20]`.
- Level 2 diagnostics show every one of those seven viewpoint ids is coverable by at least one robot, so the generated
  N=24 issue is not explained by globally unreachable viewpoints.
- Assignment-history, top-k ablation, and Level 2 join diagnostics now show nearest/greedy skip coverable ids
  `2/8/14/20`, repeatedly assign `1/12/13` without coverage, and send more target assignments to known
  Level-2-failing pairs (`760`) than known-coverable pairs (`460`). Explicit all-viewpoints candidate mode does not
  improve coverage.
- The final stuck pattern for both nearest and greedy includes two known Level-2-failing pairs
  (`robot_0 -> viewpoint_12`, `robot_2 -> viewpoint_1`) and one known-coverable pair (`robot_1 -> viewpoint_13`).
- Pair-level filtering removes known Level-2-failing target assignments and improves coverage to `19/24`, but it creates
  a new timeout pattern with `robot_0 -> noop`, `robot_1 -> viewpoint_1`, and `robot_2 -> viewpoint_12`. The remaining
  assigned target pairs are known-coverable, so the unresolved issue is no longer explained by known failing pairs alone.
- Pair-filter + retry/fallback assigns previously skipped ids `2/13/14` and cools down the previous stuck pairs, but still
  ends at `19/24`. The final pattern becomes `robot_0 -> noop`, `robot_1 -> viewpoint_1`, `robot_2 -> noop`, and no-op
  rate increases from `0.125975` to `0.185061`.
- Full-episode controller-state trace shows `robot_1 -> viewpoint_1/2/13/14` never reaches the rotation gate during
  selected assignment steps, even though position/range gates become true. `robot_2 -> viewpoint_12` reaches individual
  position/rotation/range/FOV gates, but never reaches position and rotation simultaneously.
- Static feasibility remains optimistic at agent-viewpoint pair level for several target pairs.
- `real_component_bbox_sample.csv` is temporary bbox-side pipeline sanity data, not final planned viewpoints and not a
  final algorithm performance conclusion.
- Static geometry does not model controller convergence, IK, collision, joint limits, occlusion, or real robot
  articulation.
- Stage 3B explains fixed-12 `robot_2 -> viewpoint_5` as a controller/coverage gate issue; keep the manual override
  until intentionally re-diagnosed.
- Isaac/Kit emitted the usual startup warnings and Gym deprecation notice during smoke checks; the evaluator checks passed.

## Do Not Do

- Do not modify installed `site-packages`.
- Do not modify HARL runner core logic.
- Do not change scan env reward.
- Do not change scan env underlying 9D action space.
- Do not change `assignment_controller.py` control math.
- Do not train assignment-RL or add assignment-RL evaluator support in Stage 4A.
- Do not use fixed-12 assignment checkpoints with a different external N.
- Do not treat `real_component_bbox_sample.csv` as final viewpoint planning output.
- Do not add arbitrary/variable-N policy generalization.
- Do not add Phase 6 duplicate avoidance unless explicitly requested.
- Do not connect real robot articulation, IK, collision, raycast coverage, or joint limits yet.

## Next Step

Recommended next Codex implementation task:

```text
Run a targeted comparison between the successful single-pair Level 2 runs and the full-episode trace for the same
known-coverable pairs. Focus on scanner quaternion trajectories, target quaternion conventions, rotation/FOV errors, and
simultaneous position-rotation timing for robot_1 -> viewpoints 1/2/13/14 and robot_2 -> viewpoint_12. Do not add
assignment-RL, reward changes, or controller changes in the same step.
```

Rationale: pair-level filtering improves coverage from `17/24` to `19/24`, and retry/fallback removes the
never-assigned issue for `2/13/14`, while full-episode trace shows remaining known-coverable pairs fail at rotation/FOV
or simultaneous gate timing.

Continue treating `real_component_bbox_sample.csv` as pipeline sanity data only. Do not train assignment-RL until the
external fixed-N baseline path is accepted and the final planned viewpoint CSV is available or explicitly selected.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_BASELINE_ISSUE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_UNCOVERED_LEVEL2_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_HISTORY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_TOPK_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_LEVEL2_JOIN_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_NO_PAIR_FILTER_CONTROL_JOIN_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_JOIN_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_JOIN_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_CONTROLLER_STATE_TRACE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/TASK_PROGRESS_ARCHIVE_BEFORE_STAGE4_PLAN_20260610.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/FIXED12_ASSIGNMENT_RL_MVP_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/NEXT_STAGE_REAL_COMPONENT_AND_VIEWPOINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260606/PHASE5_FIXED12_EVAL_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260605/TASK_PROGRESS_ARCHIVE_FULL_HISTORY_BEFORE_COMPACT_20260605.md
```
