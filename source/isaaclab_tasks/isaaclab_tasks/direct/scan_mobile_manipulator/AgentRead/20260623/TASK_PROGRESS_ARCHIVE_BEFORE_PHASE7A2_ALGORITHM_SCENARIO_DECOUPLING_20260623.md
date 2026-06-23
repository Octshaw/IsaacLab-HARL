# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7A YAML Capability Profiles MVP is complete.

The task-space proxy capability profile parameters for:

```text
mobile_scanner_a
mobile_scanner_b
mobile_scanner_c
```

now live in YAML instead of the hard-coded `ROBOT_CAPABILITY_PROFILES` table in
`scan_mobile_manipulator_env.py`.

This is a configuration refactor only. Assignment tensors, controller math, reward logic, proxy state, HARL core,
training behavior, evaluator solver logic, visual mesh spawning/following, collision, IK, raycast coverage, and final
real CSV validation were not changed.

## Latest Completed Phase

Phase 7A: YAML Capability Profiles MVP.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/capability_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A_YAML_CAPABILITIES_20260623.md
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Implementation Summary

- Added `configs/capabilities/mobile_scanner_profiles.yaml` with the exact old profile values.
- Added `capability_config.py`, a dependency-light YAML loader with validation and JSON diagnostics.
- `scan_mobile_manipulator_env.py` now loads capability profiles from YAML by default.
- The legacy three-proxy path still uses the legacy profile names, but the numeric values are read from YAML.
- Scenario configs and smoke/evaluator scripts now support optional `capabilities.config_path` / `--capability_config_path`.
- `real_scene_proxy_headless.yaml` explicitly references the default capability YAML.
- Assignment problem diagnostics now include:

```text
capability_config_path
capability_profile_names
capability_profiles
capability_profile_by_robot
capability_profiles_by_robot
```

## Verification

Passed syntax checks:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile capability_config.py scan_mobile_manipulator_env.py scenario_config.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile test_assignment_harl_wrapper_smoke.py evaluate_assignment_methods.py
```

Passed loader checks:

```text
capability_config.py configs/capabilities/mobile_scanner_profiles.yaml
capability_config.py with omitted path
robot_config.py configs/robots/robots_real_proxy.yaml
```

Passed one-step CPU/headless wrapper smoke:

```text
result_file=results/assignment_diagnostics/yaml_capability_profiles_phase7a_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
capability_profile_names=[mobile_scanner_a, mobile_scanner_b, mobile_scanner_c]
capability_profile_by_robot={robot_0: mobile_scanner_a, robot_1: mobile_scanner_b, robot_2: mobile_scanner_c}
visual_mesh_spawned_by_robot=true for robot_0, robot_1, robot_2
```

Passed minimal evaluator smoke:

```text
output_dir=results/assignment_evaluation/yaml_capability_profiles_phase7a_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
capability diagnostics present
```

## Known Issues / Limitations

- This phase did not add custom capability profiles beyond the existing three.
- GUI visual inspection was not rerun by Codex.
- The fixed/default no-scenario wrapper path was not rerun; the default capability loader path was verified directly.
- Temporary and synthetic CSVs remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not add obstacle-aware path cost or inter-robot conflict avoidance in this phase.
- Do not add dynamic reassignment policy yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Phase 7B: add obstacle-aware or component-aware path-cost extension points using the YAML capability/profile layer,
starting with diagnostics and cost fields only. Keep solver/reward/controller behavior unchanged until the interface is
validated.
```

Manual GUI visual inspection remains useful before any user-facing scene screenshots or visual tuning claims.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7A_YAML_CAPABILITIES_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S4_AUTO_BOTTOM_ALIGN_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S3_VISUAL_INSPECTION_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S2_VISUAL_MESH_FOLLOW_20260622.md
```
