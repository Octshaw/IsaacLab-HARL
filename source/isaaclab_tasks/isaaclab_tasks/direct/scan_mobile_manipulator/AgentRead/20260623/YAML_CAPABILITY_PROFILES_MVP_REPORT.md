# YAML Capability Profiles MVP Report

## Purpose

Phase 7A externalized the existing task-space proxy capability profile parameters from
`scan_mobile_manipulator_env.py` into YAML.

This phase is a configuration refactor only. It does not change assignment behavior, reward logic, controller math,
visual mesh spawning/following, HARL core, training, articulation, IK, collision, joint limits, raycast coverage, or
final real CSV validation.

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/capability_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml
```

## Files Modified

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Old Profile Source

The previous hard-coded source was:

```text
ROBOT_CAPABILITY_PROFILES in scan_mobile_manipulator_env.py
```

It contained three profiles:

```text
mobile_scanner_a
mobile_scanner_b
mobile_scanner_c
```

Each profile supplied:

```text
scanner_start_offset
arm_reach
scanner_min_range
scanner_max_range
scanner_fov_deg
scan_pos_tolerance
scan_rot_tolerance
max_base_xy_step
max_base_yaw_step
max_ee_xyz_step
max_ee_rpy_step
```

## New YAML Profile Source

The new default YAML source is:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml
```

The YAML preserves the previous numeric values exactly for all three profiles.

`real_scene_proxy_headless.yaml` now explicitly references the default capability YAML:

```yaml
capabilities:
  config_path: source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml
```

Scenarios may omit `capabilities.config_path`; the loader then uses the same default YAML path.

## Loader Validation Rules

`capability_config.py` validates:

- top-level `capability_profiles` mapping exists and is non-empty;
- profile names are non-empty strings;
- `scanner_start_offset` has exactly three finite floats;
- scalar profile fields are finite positive floats;
- `scanner_max_range` is greater than `scanner_min_range`;
- YAML order is preserved through the returned profile mapping.

The loader does not import Isaac Sim or Isaac Lab. It can be checked directly with:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/capability_config.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml
```

## Environment Wiring

`scan_mobile_manipulator_env.py` now loads capability profiles during config preparation.

Robot configs still reference profile names through:

```yaml
capability_profile: mobile_scanner_a
```

The environment resolves those names against the YAML capability config and fills the same cfg fields as before:

```text
cfg.scanner_start_offsets
cfg.arm_reach
cfg.scanner_min_range
cfg.scanner_max_range
cfg.scanner_fov_deg
cfg.scan_pos_tolerance
cfg.scan_rot_tolerance
cfg.max_base_xy_step
cfg.max_base_yaw_step
cfg.max_ee_xyz_step
cfg.max_ee_rpy_step
```

The legacy three-proxy fallback keeps the same profile-name mapping:

```text
robot_0 -> mobile_scanner_a
robot_1 -> mobile_scanner_b
robot_2 -> mobile_scanner_c
```

but the numeric profile values now come from YAML.

## Diagnostics Added

The assignment problem, wrapper smoke JSON, and evaluator diagnostics now include:

```text
capability_config_path
capability_profile_names
capability_profiles
capability_profile_by_robot
capability_profiles_by_robot
```

These diagnostics are metadata only. Baseline solvers continue to consume:

```text
available_mask
cost_matrix
noop_id
```

## Smoke Results

Wrapper smoke:

```text
results/assignment_diagnostics/yaml_capability_profiles_phase7a_smoke.json
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

Evaluator smoke:

```text
results/assignment_evaluation/yaml_capability_profiles_phase7a_eval_smoke
methods=random, nearest, greedy
num_envs=1, num_episodes=1, max_steps=1
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
capability diagnostics present
```

All three baseline methods completed the one-step smoke.

## Known Limitations

- No new capability profiles were introduced.
- No GUI visual inspection was rerun in this phase.
- The fixed/default no-scenario wrapper path was not rerun; the default capability loader path was verified directly.
- Temporary and synthetic viewpoint CSVs remain smoke/interface validation data only, not final benchmark evidence.

## Next Recommended Step

Phase 7B can add obstacle-aware or component-aware path-cost extension points using the YAML capability/profile layer.
Start with diagnostics and cost-field plumbing only, and keep solver/reward/controller behavior unchanged until the
interface is validated.
