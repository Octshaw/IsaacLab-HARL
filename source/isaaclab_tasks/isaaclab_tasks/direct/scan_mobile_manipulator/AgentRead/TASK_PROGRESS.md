# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Stage 4A fixed-N evaluator support is implemented and metric-correct. The evaluator supports scenario YAML input and
external fixed-N viewpoint CSVs for baseline-only evaluation with `random`, `nearest`, and `greedy`. The fixed-12 default
path remains available as a regression path.

Stage 4B generated real-component N=24 diagnostics are now paused. The temporary CSV:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
```

is pipeline sanity / smoke data only. It is useful for validating scenario loading, evaluator outputs, visualization,
assignment-history diagnostics, and controller trace plumbing, but it is not final viewpoint planning output and must not
be treated as a final algorithm-performance benchmark.

Recent Stage 4B findings on this temporary sample:

- Generated N=24 scenario loads with `N=24`, `noop_id=24`, `available_actions_shape=[num_envs, 3, 25]`.
- Initial nearest/greedy bounded baseline reached `17/24`.
- Level 2 diagnostics showed all originally uncovered target viewpoints were coverable by at least one robot.
- Pair-level Level 2 filtering improved nearest/greedy to `19/24`.
- Retry/fallback made previously skipped target ids assigned, but coverage remained `19/24`.
- Full-episode controller-state trace showed remaining failures are mainly controller/gate/orientation timing issues in
  the temporary bbox sample.

Decision: do not continue optimizing or deeply diagnosing controller gates against `real_component_bbox_sample.csv`
unless explicitly requested. The final real planned viewpoint CSV is intentionally out of scope until the simulation
environment, robot configuration interface, assignment interface, and evaluator are validated. Its absence is not a
blocker for Robot Config MVP or simulation-readiness validation. Current progress should continue with fixed/default,
temporary, and synthetic viewpoint sets.

## Latest Completed Work

Documentation-only planning correction completed:

- Updated the next-stage task plan to clarify that Robot Config MVP remains the immediate target and the final real CSV
  is reserved for later final validation:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md`
- Updated this handoff with the corrected pre-real-CSV validation policy.
- Existing archive remains available:
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md`

No code, simulation logic, reward, controller, HARL core, training path, or installed `site-packages` files were changed
for this documentation-only correction.

## Active Architecture / Implementation Path

Current assignment path remains:

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

Current fixed-N invariant:

```text
N = loaded viewpoints
noop_id = N
action width = N + 1
available_actions shape = [num_envs, num_agents, N + 1]
```

Next-stage target invariant:

```text
N = loaded viewpoints
M = enabled robots from robots.yaml
noop_id = N
available_actions shape = [num_envs, M, N + 1]
```

## Key Files

Current handoff:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
```

Relevant implementation files:

```text
scripts/environments/evaluate_assignment_methods.py
scripts/environments/diagnose_assignment_controller_feasibility.py
scripts/environments/analyze_assignment_history_with_level2.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
```

Temporary generated real-component sample files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

## Latest Verification

Documentation-only task. No Python code was changed and no simulation/evaluator smoke was run.

Verification performed:

- Read `AGENTS.md`.
- Read `TASK_PROGRESS.md`.
- Read `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md`.
- Updated documentation only.
- Ran `git status --short` to inspect the worktree.
- Ran `git diff -- ...` for the two edited documentation files.
- Ran `rg -n` over the two edited documentation files for stale real-CSV blocker wording and new section markers.

## Known Issues / Blockers

- Final real planned viewpoint CSV is intentionally reserved for later final validation; its absence is not a blocker for
  Robot Config MVP or simulation-readiness validation.
- Current progress should continue with fixed/default, temporary, and synthetic viewpoint sets.
- `real_component_bbox_sample.csv` is temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Stage 4B diagnostics on the temporary sample exposed controller/gate/orientation timing issues, but these should not be
  optimized as if they were final benchmark failures.
- Assignment-RL should not be trained or evaluated for external `N` until the baseline/interface path is accepted and a
  later validation stage explicitly selects the dataset.
- Current robot count is still effectively a 3-robot task-space proxy setup; next stage should make this YAML-driven and
  M-ready.

## Do Not Do

- Do not train assignment-RL.
- Do not add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward.
- Do not change `assignment_controller.py`.
- Do not change controller math or the 9D action path.
- Do not add full real robot articulation yet.
- Do not add IK, collision, joint limits, or raycast coverage yet.
- Do not wait for final real CSV.
- Do not require real CSV for Robot Config MVP.
- Do not use real CSV availability as a blocker for simulation-interface validation.
- Do not treat `real_component_bbox_sample.csv` as final viewpoint planning output.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not tune controller/gate/orientation behavior specifically to temporary or synthetic CSV samples.
- Do not continue deep controller-gate diagnostics on the temporary bbox sample unless explicitly requested.

## Next Step

Recommended next Codex implementation task:

```text
Start Robot Config MVP: add a YAML robot config schema/loader and scenario YAML reference path, initially for three
enabled task-space proxy robots but with code structured around M = len(enabled_robots).
```

First minimal slice:

1. Add `robot_config.py`.
2. Add `configs/robots/robots_three_proxy.yaml`.
3. Add scenario YAML support for referencing `robots.yaml`.
4. Load, validate, and expose enabled robot diagnostics.
5. Do not yet add IK, collision, real robot articulation, assignment-RL training, reward changes, or controller changes.

After the loader is verified, wire enabled robot count into the task-space proxy environment and evaluator so:

```text
M=3, M=2, and M=4 smoke configs produce available_actions shape [num_envs, M, N+1].
```

These smoke checks can use fixed/default, temporary, or synthetic viewpoint CSVs. No final real planned viewpoint CSV is
required for Robot Config MVP. After Robot Config MVP, the next documentation/implementation target should be
simulation-readiness validation using fixed/default, temporary, and synthetic viewpoint CSVs, not the real CSV.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_BASELINE_ISSUE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_UNCOVERED_LEVEL2_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_HISTORY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_TOPK_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_ASSIGNMENT_LEVEL2_JOIN_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_ABLATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_PAIR_FILTER_RETRY_FALLBACK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260615/STAGE4B_REAL_COMPONENT_N24_CONTROLLER_STATE_TRACE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
