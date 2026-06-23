# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Robot Config MVP Phase 3 is complete. The task-space proxy environment and baseline evaluator have now been
shape-verified on the fixed-12 regression path for `M=2`, `M=3`, and `M=4`, where `M` is the number of enabled robots in
the robot YAML.

Verified invariant:

```text
N = loaded viewpoints
M = enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

No controller math, reward logic, HARL core, training behavior, assignment-RL evaluation, real robot articulation, IK,
collision, joint limits, or raycast coverage was changed.

The final real planned viewpoint CSV is intentionally reserved for later final validation. Its absence is not a blocker
for Robot Config MVP or simulation-readiness validation. Continue using fixed/default, temporary, and synthetic
viewpoint sets until the simulation environment, robot configuration interface, assignment interface, and evaluator are
accepted.

## Latest Completed Phase

Robot Config MVP Phase 3: M=2/M=3/M=4 smoke coverage.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
```

Modified files in Phase 3:

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Earlier Robot Config MVP files still active from Phases 1-2:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/diagnose_assignment_controller_feasibility.py
```

Implementation summary:

- Added `robots_two_proxy.yaml` with three configured robots and `robot_2` disabled.
- Added `robots_four_proxy.yaml` with four enabled proxy robots; `robot_3` reuses `mobile_scanner_c`.
- Added `cost_matrix_shape` validation/reporting to evaluator fixed-N diagnostics.
- Verified deterministic enabled-agent mappings for M=2, M=3, and M=4.
- Verified wrapper and evaluator shapes for M=2, M=3, and M=4.

## Active Architecture

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

When `robot_config_path` is supplied, enabled robot YAML order drives `possible_agents`, action/observation/state
spaces, start poses, capability/profile parameters, assignment problem shapes, and diagnostics. When no robot config path
is supplied, the legacy three task-space proxy behavior is preserved.

The fixed-12 `robot_2 -> viewpoint_5` manual feasibility override remains active for fixed-12 diagnostics and is skipped
automatically when `robot_2` is disabled.

## Latest Verification

Phase 2 baseline checks were rerun before Phase 3 changes and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: robot_config.py, scenario_config.py, scan_mobile_manipulator_env.py, wrapper/evaluator/diagnostic scripts
loader check: robots_three_proxy.yaml
wrapper smoke: Phase 2 M=3 with robot config
wrapper smoke: legacy no-config fixed-12 fallback
evaluator smoke: Phase 2 M=3 random/nearest/greedy
```

Phase 3 loader diagnostics:

```text
M=2: num_configured_robots=3, num_enabled_robots=2, enabled_robot_names=["robot_0", "robot_1"], agent_id_by_name={"robot_0": 0, "robot_1": 1}
M=3: num_configured_robots=3, num_enabled_robots=3, enabled_robot_names=["robot_0", "robot_1", "robot_2"], agent_id_by_name={"robot_0": 0, "robot_1": 1, "robot_2": 2}
M=4: num_configured_robots=4, num_enabled_robots=4, enabled_robot_names=["robot_0", "robot_1", "robot_2", "robot_3"], agent_id_by_name={"robot_0": 0, "robot_1": 1, "robot_2": 2, "robot_3": 3}
```

Phase 3 wrapper smoke results:

```text
results/assignment_diagnostics/robot_config_phase3_m2_smoke.json: N=12, noop_id=12, available_actions=[1, 2, 13]
results/assignment_diagnostics/robot_config_phase3_m3_smoke.json: N=12, noop_id=12, available_actions=[1, 3, 13]
results/assignment_diagnostics/robot_config_phase3_m4_smoke.json: N=12, noop_id=12, available_actions=[1, 4, 13]
```

Phase 3 evaluator smoke results:

```text
results/assignment_evaluation/robot_config_phase3_m2_eval_smoke/diagnostics.json: available_mask=[1, 2, 12], available_actions=[1, 2, 13], cost_matrix=[1, 2, 12]
results/assignment_evaluation/robot_config_phase3_m3_eval_smoke/diagnostics.json: available_mask=[1, 3, 12], available_actions=[1, 3, 13], cost_matrix=[1, 3, 12]
results/assignment_evaluation/robot_config_phase3_m4_eval_smoke/diagnostics.json: available_mask=[1, 4, 12], available_actions=[1, 4, 13], cost_matrix=[1, 4, 12]
```

Additional checks:

```text
py_compile scripts/environments/evaluate_assignment_methods.py: passed after cost_matrix_shape diagnostics change
git diff --check for Phase 3 files: passed with CRLF normalization warnings only
```

No training, GUI, long simulation, assignment-RL evaluation, GPU-heavy evaluation, or final real CSV validation was run.

## Known Issues / Blockers

- No current blocker for Robot Config MVP shape validation.
- Phase 3 only verified fixed-12 shape behavior for M=2/M=3/M=4.
- Multi-`N` simulation-readiness validation remains unfinished.
- `real_component_bbox_sample.csv` is temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Stage 4B temporary-sample diagnostics exposed controller/gate/orientation timing issues, but those should not be tuned
  as final benchmark failures.
- Only `mobile_scanner_a`, `mobile_scanner_b`, and `mobile_scanner_c` are supported task-space proxy capability profiles.
- Full 7D `initial_pose_world` is preserved in diagnostics, but the current proxy state remains yaw-only.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not tune controller/gate/orientation behavior specifically to temporary or synthetic CSV samples.
- Do not introduce unknown capability profiles unless explicitly adding and testing profile support.

## Next Step

Recommended next task:

```text
Simulation-readiness validation pass across multiple legal viewpoint CSV sizes without using the final real planned CSV.
```

Suggested next slice:

1. Keep fixed-12 regression as the first check.
2. Run lightweight smokes for temporary/synthetic `N` values, such as temporary N=24, synthetic N=50, synthetic N=100,
   and synthetic N=200.
3. For selected `M` values, verify `noop_id=N`, `available_actions=[num_envs, M, N+1]`,
   `available_mask=[num_envs, M, N]`, and `cost_matrix=[num_envs, M, N]`.
4. Keep reward, controller math, HARL core, training, real robot articulation, IK, collision, joint limits, raycast
   coverage, and final real CSV validation out of scope.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
