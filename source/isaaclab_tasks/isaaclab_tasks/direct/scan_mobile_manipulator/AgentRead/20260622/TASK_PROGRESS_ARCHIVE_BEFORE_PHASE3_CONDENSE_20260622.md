# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Robot Config MVP Phase 3 is implemented and shape-verified for enabled robot counts `M=2`, `M=3`, and `M=4` on the
fixed-12 regression path.

The verified shape invariant is:

```text
M = len(enabled_robots)
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

Current fixed-12 smoke results:

```text
M=2: N=12, noop_id=12, available_actions=[1, 2, 13], available_mask=[1, 2, 12], cost_matrix=[1, 2, 12]
M=3: N=12, noop_id=12, available_actions=[1, 3, 13], available_mask=[1, 3, 12], cost_matrix=[1, 3, 12]
M=4: N=12, noop_id=12, available_actions=[1, 4, 13], available_mask=[1, 4, 12], cost_matrix=[1, 4, 12]
```

When `robot_config_path` is supplied, enabled robot YAML order drives the task-space proxy agent list, action spaces,
observation/state spaces, start poses, capability/profile parameters, assignment problem shapes, and diagnostics. When
no robot config path is supplied, the legacy three task-space proxy behavior is preserved.

No controller math, reward logic, HARL core, training behavior, real robot articulation, IK, collision, joint limits, or
raycast coverage was changed.

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

Robot Config MVP Phase 3 completed.

Added files for Phase 3:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
```

Modified files for Phase 3:

```text
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Implementation summary:

- Added `robots_two_proxy.yaml` with three configured robots and `robot_2` disabled, verifying enabled filtering.
- Added `robots_four_proxy.yaml` with four enabled task-space proxy robots; `robot_3` reuses the known
  `mobile_scanner_c` capability profile to keep Phase 3 shape-focused.
- Added evaluator diagnostics/validation for `cost_matrix_shape`.
- Verified loader diagnostics, wrapper available-action shape, evaluator available-mask/action shape, and evaluator
  cost-matrix shape for M=2/M=3/M=4.

Expected deterministic loader mappings were verified:

```text
M=2: enabled_robot_names=["robot_0", "robot_1"], agent_id_by_name={"robot_0": 0, "robot_1": 1}
M=3: enabled_robot_names=["robot_0", "robot_1", "robot_2"], agent_id_by_name={"robot_0": 0, "robot_1": 1, "robot_2": 2}
M=4: enabled_robot_names=["robot_0", "robot_1", "robot_2", "robot_3"], agent_id_by_name={"robot_0": 0, "robot_1": 1, "robot_2": 2, "robot_3": 3}
```

Robot Config MVP files active in the implementation:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
```

Intentionally unchanged:

- The class-level no-config defaults remain the legacy three proxy robots.
- The fixed-12 `robot_2 -> viewpoint_5` manual feasibility override remains for the fixed-12 regression path and is
  skipped automatically when `robot_2` is absent.
- `assignment_controller.py`, reward math, controller gates, the 9D action path, HARL core, and training paths were not
  modified.

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
M = enabled robots from robots.yaml
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
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
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
```

Temporary generated real-component sample files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

## Latest Verification

Robot Config MVP Phase 3 lightweight checks passed. No training, GUI run, assignment-RL evaluation, or long simulation
was run.

Phase 2 baseline was rerun before Phase 3 changes:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
  -> passed, printed C:\isaacenvs\isaac45_harl\python.exe

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
  -> passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
  -> passed

conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
  -> passed, printed diagnostics with 3 configured robots, 3 enabled robots, and robot_0/1/2 agent IDs 0/1/2

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
  -> passed

conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py scripts/environments/evaluate_assignment_methods.py scripts/environments/diagnose_assignment_controller_feasibility.py
  -> passed

conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
  -> passed, M=3 diagnostics

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --result_file results/assignment_diagnostics/robot_config_phase2_m3_smoke.json
  -> passed, available_actions_shape=[1, 3, 13], noop_id=12, robot_config_diagnostics reports 3 enabled robots

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --result_file results/assignment_diagnostics/robot_config_phase2_legacy_fixed12_smoke.json
  -> passed, legacy no-config fallback still loads fixed-12 with available_actions_shape=[1, 3, 13]

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --output_dir results/assignment_evaluation --output_name robot_config_phase2_m3_eval_smoke --no-write_assignment_history
  -> passed, evaluator diagnostics report num_agents=3, available_mask_shape=[1, 3, 12], available_actions_shape=[1, 3, 13], and robot_config_diagnostics
```

Phase 3 loader checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
  -> passed, num_configured_robots=3, num_enabled_robots=3, enabled_robot_names=["robot_0", "robot_1", "robot_2"]

conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
  -> passed, num_configured_robots=3, num_enabled_robots=2, enabled_robot_names=["robot_0", "robot_1"]

conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
  -> passed, num_configured_robots=4, num_enabled_robots=4, enabled_robot_names=["robot_0", "robot_1", "robot_2", "robot_3"]
```

Phase 3 wrapper smokes:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml --result_file results/assignment_diagnostics/robot_config_phase3_m2_smoke.json
  -> passed, num_agents=2, N=12, noop_id=12, available_actions_shape=[1, 2, 13]

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --result_file results/assignment_diagnostics/robot_config_phase3_m3_smoke.json
  -> passed, num_agents=3, N=12, noop_id=12, available_actions_shape=[1, 3, 13]

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml --result_file results/assignment_diagnostics/robot_config_phase3_m4_smoke.json
  -> passed, num_agents=4, N=12, noop_id=12, available_actions_shape=[1, 4, 13]
```

Phase 3 evaluator smokes:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml --output_dir results/assignment_evaluation --output_name robot_config_phase3_m2_eval_smoke --no-write_assignment_history
  -> passed, available_mask_shape=[1, 2, 12], available_actions_shape=[1, 2, 13], cost_matrix_shape=[1, 2, 12]

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml --output_dir results/assignment_evaluation --output_name robot_config_phase3_m3_eval_smoke --no-write_assignment_history
  -> passed, available_mask_shape=[1, 3, 12], available_actions_shape=[1, 3, 13], cost_matrix_shape=[1, 3, 12]

conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml --output_dir results/assignment_evaluation --output_name robot_config_phase3_m4_eval_smoke --no-write_assignment_history
  -> passed, available_mask_shape=[1, 4, 12], available_actions_shape=[1, 4, 13], cost_matrix_shape=[1, 4, 12]
```

Final shape summary from generated JSON diagnostics:

```text
M=2 wrapper: num_agents=2, N=12, noop_id=12, available_actions=[1, 2, 13]
M=2 evaluator: available_mask=[1, 2, 12], available_actions=[1, 2, 13], cost_matrix=[1, 2, 12]
M=3 wrapper: num_agents=3, N=12, noop_id=12, available_actions=[1, 3, 13]
M=3 evaluator: available_mask=[1, 3, 12], available_actions=[1, 3, 13], cost_matrix=[1, 3, 12]
M=4 wrapper: num_agents=4, N=12, noop_id=12, available_actions=[1, 4, 13]
M=4 evaluator: available_mask=[1, 4, 12], available_actions=[1, 4, 13], cost_matrix=[1, 4, 12]
```

Additional checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
  -> passed after adding cost_matrix_shape diagnostics
```

Notes:

- A direct no-AppLauncher env import check was attempted and failed on `ModuleNotFoundError: No module named
  'omni.kit'`; this is expected for Isaac Lab modules before `AppLauncher`, so the existing headless smoke was used
  instead.
- One evaluator command was rerun after correcting the BooleanOptionalAction spelling from `--write_assignment_history
  false` to `--no-write_assignment_history`.

## Known Issues / Blockers

- Final real planned viewpoint CSV is intentionally reserved for later final validation; its absence is not a blocker for
  Robot Config MVP or simulation-readiness validation.
- Current progress should continue with fixed/default, temporary, and synthetic viewpoint sets.
- `real_component_bbox_sample.csv` is temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Stage 4B diagnostics on the temporary sample exposed controller/gate/orientation timing issues, but these should not be
  optimized as if they were final benchmark failures.
- Assignment-RL should not be trained or evaluated for external `N` until the baseline/interface path is accepted and a
  later validation stage explicitly selects the dataset.
- Only known capability profiles `mobile_scanner_a`, `mobile_scanner_b`, and `mobile_scanner_c` are supported by the
  task-space proxy env. Unknown profiles fail fast.
- Full 7D `initial_pose_world` is preserved in diagnostics, but the current proxy state is still yaw-only.
- Phase 3 only verifies fixed-12 shape behavior for M=2/M=3/M=4. Multi-`N` simulation-readiness validation remains
  unfinished.

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
Simulation-readiness validation pass: verify robot config and assignment/evaluator interfaces across multiple legal
viewpoint CSV sizes without using the final real planned CSV.
```

Suggested next slice:

1. Keep fixed-12 regression as the first check.
2. Run lightweight smokes for temporary/synthetic `N` values such as:

```text
temporary N=24 bbox-side sample
synthetic N=50
synthetic N=100
synthetic N=200
```

3. Verify, for selected M values, that:

```text
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
noop_id = N
```

4. Keep reward, controller math, HARL core, training, real robot articulation, IK, collision, joint limits, raycast
   coverage, and final real CSV validation out of scope.

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
