# TASK_PROGRESS

This file is the compact handoff for the assignment-based RL work.

## Current Status

Status: Scenario YAML config support for long real component commands is implemented; core YAML paths are smoke-tested.

Latest completed work:
- Added `scenario_config.py` for YAML scenario config loading, flattening, and validation.
- Added `--scenario_config` support to:
  `test_assignment_harl_wrapper_smoke.py`, `generate_bbox_viewpoint_csv.py`, and `inspect_component_mesh_bounds.py`.
- Added real component scenario YAML files for visual smoke, headless smoke, and sample CSV generation.
- Added `REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md` with compact commands and override examples.
- Kept existing long CLI options working; scenario config values are parser defaults and explicit CLI values override them.
- Added `generate_bbox_viewpoint_csv.py` to create a strict temporary world-frame fixed-N viewpoint CSV around the real
  component's transformed auto bbox.
- Added `--align_base_center_to_world_origin` support so the scaled/rotated mesh base center can define world origin.
- Extended the component mesh helper, bounds inspection script, environment config, and wrapper smoke CLI with the same
  base-center alignment convention.
- Added `component_proxy_visual_visible` / `--no-component_proxy_visual_visible` so real OBJ visual checks can hide the
  translucent bbox debug cuboid while still using the bbox proxy for algorithmic geometry.
- Generated `real_component_bbox_sample.csv` for the measured aircraft skin/frame OBJ:
  `num_viewpoints=24`, `noop_id=24`, `available_actions_shape=(1, 3, 25)` in smoke.
- Preserved fixed-12 default and external sample N=6 regression scenarios.
- Added visual-only OBJ component mesh support for the measured aircraft skin/frame mesh.
- Added explicit OBJ unit handling (`mm`) and scale/rotation/translation-aware world AABB computation.
- Added `component_proxy_auto_from_mesh` so the transformed OBJ AABB can become the canonical bbox proxy.
- Added `inspect_component_mesh_bounds.py` and pure OBJ bounds tests for identity, translation, rotation, and invalid files.
- Extended wrapper smoke CLI/JSON diagnostics for component mesh and auto bbox fields.
- Preserved the fixed-12 assignment-RL default scenario.
- Preserved the external N=6 sample CSV scenario.
- Added `static_geometric_v1` Level 1 feasibility generation.
- Added deterministic diagnostic rows per agent-viewpoint pair.
- Added a bounded Level 2 controller diagnostic using the existing assignment wrapper/controller path.
- Tested fixed-12 `robot_2 -> viewpoint_5` and comparison `robot_0 -> viewpoint_5`.
- Kept the fixed-12 manual override because Level 2 confirms `robot_2 -> viewpoint_5` is not covered.
- Replaced the pending override rationale with the cached Level 2 reason:
  `level2_controller_diagnostic_position_rotation_gates_never_simultaneously_satisfied`.
- Extended wrapper smoke JSON diagnostics to compare raw static geometry vs final assignment feasibility.

No training was run.
No long simulation/evaluation was run.
No installed `site-packages` files were modified.
No HARL core files were modified.
No `assignment_controller.py` control math was modified.
No underlying 9D scan env action space was changed.

## Latest Completed Phase

Real component bbox sample viewpoint CSV generation:

```text
strict scanner_pose_world_quat_wxyz_v1 CSV generation
model base center as world origin
bbox-side sample viewpoints for smoke testing
```

Generated sample CSV:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
```

Generated diagnostics:

```text
results/assignment_diagnostics/real_component_bbox_sample_generation.json
results/assignment_diagnostics/real_component_generated_csv_smoke.json
results/assignment_diagnostics/real_component_mesh_only_visual_smoke.json
results/assignment_diagnostics/real_component_mesh_bounds_base_center_origin.json
results/assignment_diagnostics/real_component_bbox_sample_headless_smoke.json
results/assignment_diagnostics/real_component_bounds_from_yaml.json
```

With `--align_base_center_to_world_origin`, the real OBJ base-center alignment is:

```text
base_center_before_translation=(1.709499729155, 0.830778200625, 3.08981591797)
component_mesh_position=(-1.709499729155, -0.830778200625, -3.08981591797)
world_min=(-1.800000026705, -0.842999997615, 0.0)
world_max=(1.800000026705, 0.842999997615, 2.36496630859)
auto_proxy_center~=(-0.0, 0.0, 1.182483154295)
auto_proxy_half_extents=(1.800000026705, 0.842999997615, 1.182483154295)
```

The generated sample is only for smoke testing and early evaluation. It is not final measurement planning output.

Previous real component OBJ visual + auto bbox proxy:

```text
visual-only OBJ mesh loading
rotation-aware world AABB
auto component bbox proxy
```

The OBJ mesh path verified in this stage:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

Real OBJ raw bounds:

```text
unit=mm
raw_min=(-90.50029755, -12.22179699, 3089.81591797)
raw_max=(3509.49975586, 1673.77819824, 5454.78222656)
```

With `scale=(0.001, 0.001, 0.001)` and identity transform:

```text
world_min=(-0.09050029755, -0.01222179699, 3.08981591797)
world_max=(3.50949975586, 1.67377819824, 5.45478222656)
auto_proxy_center=(1.709499729155, 0.830778200625, 4.272299072265)
auto_proxy_half_extents=(1.800000026705, 0.842999997615, 1.182483154295)
```

For the real-mesh smoke with sample N=6 viewpoints, the mesh was translated by:

```text
component_mesh_position=(-1.709499729, -0.830778201, -3.272299072)
```

This aligns the auto bbox proxy center near `(0, 0, 1)` for compatibility with the existing sample CSV. Real measured
viewpoints should use their own world frame and matching mesh transform.

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

Default fixed-12 behavior:
- `viewpoint_csv_path = None`
- built-in 12 poses are used
- no-op id remains `12`
- available action width remains `13`
- Stage 3A raw geometry says `robot_2 -> viewpoint_5` is feasible
- final assignment mask still applies the fixed-12 manual override for `robot_2 -> viewpoint_5`
- that row now carries cached Level 2 diagnostics:

```text
level2_controller_diagnostic_position_rotation_gates_never_simultaneously_satisfied
```

External N=6 sample behavior:
- `viewpoint_csv_path = configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv`
- no-op id is `6`
- available action width is `7`
- no manual override is applied
- all 6 viewpoints are feasible for all 3 agents under Stage 3A geometry

## Key Files

Modified/added in sample viewpoint CSV generation stage:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_mesh.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/inspect_component_mesh_bounds.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/test_component_mesh_bounds.py
scripts/environments/generate_bbox_viewpoint_csv.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_visual.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/generate_real_component_bbox_sample_csv.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```

Modified in real OBJ mesh stage:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Added in real OBJ mesh stage:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/component_mesh.py
scripts/environments/inspect_component_mesh_bounds.py
scripts/environments/test_component_mesh_bounds.py
```

Still present from Stage 3B:

```text
scripts/environments/diagnose_assignment_controller_feasibility.py
```

Still present from Stage 3A:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/static_feasibility.py
scripts/environments/test_static_feasibility_generator.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Still present from Stage 1/2:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/viewpoint_csv.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv
scripts/environments/test_viewpoint_csv_loader.py
```

## Latest Verification

Pre-Stage-3A lightweight checks:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\viewpoint_csv.py scripts\environments\test_viewpoint_csv_loader.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_viewpoint_csv_loader.py --csv_path configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6
  -> passed
```

Stage 3A checks:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\static_feasibility.py scripts\environments\test_static_feasibility_generator.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_static_feasibility_generator.py
  -> passed
  -> verified feasible_mask shape, diagnostic row count, and reason_if_false for infeasible rows

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_viewpoint_csv_loader.py --csv_path configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_wrapper_smoke.py --num_envs 1 --max_steps 1 --headless --result_file stage3a_fixed12_smoke_result.json
  -> passed, exit code 0
  -> num_viewpoints=12, noop_id=12, available_actions_shape=[1, 3, 13]
  -> static geometry feasible agents for viewpoint 5: robot_0, robot_1, robot_2
  -> final feasible agents for viewpoint 5: robot_0, robot_1
  -> manual override row: robot_2 -> viewpoint_5, Level 2 diagnostic required
  -> permanently_unavailable_viewpoints=[]

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_wrapper_smoke.py --num_envs 1 --max_steps 1 --headless --viewpoint_csv_path configs/viewpoints/sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --result_file stage3a_external_smoke_result.json
  -> passed, exit code 0
  -> num_viewpoints=6, noop_id=6, available_actions_shape=[1, 3, 7]
  -> manual_feasibility_override_rows=[]
  -> infeasible_rows=[]
  -> permanently_unavailable_viewpoints=[]
```

The temporary Stage 3A smoke JSON files were deleted after inspection.

One wider final `py_compile` command was attempted after the smoke checks, but Codex tool escalation was rejected by the current usage limit. The Stage 3A changed files had already passed `py_compile` before the wrapper smokes.

Stage 3B checks:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\diagnose_assignment_controller_feasibility.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\diagnose_assignment_controller_feasibility.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 160 --pair robot_2:5 --pair robot_0:5 --output_json E:\Project\IsaacLab_HARL\results\assignment_diagnostics\stage3b\fixed12_robot2_robot0_vp5.json --headless --device cpu
  -> passed
  -> robot_2 -> viewpoint_5 covered=False
  -> reason=position_rotation_gates_never_simultaneously_satisfied
  -> robot_0 -> viewpoint_5 covered=True, first_covered_step=60

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --result_file E:\Project\IsaacLab_HARL\results\assignment_diagnostics\stage3b\fixed12_wrapper_smoke.json --headless --device cpu
  -> passed
  -> num_viewpoints=12, noop_id=12, available_actions_shape=(1, 3, 13)
  -> fixed-12 manual row reason_if_false=level2_controller_diagnostic_position_rotation_gates_never_simultaneously_satisfied

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --result_file E:\Project\IsaacLab_HARL\results\assignment_diagnostics\stage3b\sample_n6_wrapper_smoke.json --headless --device cpu
  -> passed
  -> num_viewpoints=6, noop_id=6, available_actions_shape=(1, 3, 7)
  -> manual_feasibility_override_rows=[]
  -> infeasible_rows=[]
```

Stage 3B diagnostic artifacts retained for inspection:

```text
results/assignment_diagnostics/stage3b/fixed12_robot2_robot0_vp5.json
results/assignment_diagnostics/stage3b/fixed12_wrapper_smoke.json
results/assignment_diagnostics/stage3b/sample_n6_wrapper_smoke.json
```

Real OBJ mesh stage checks:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\component_mesh.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py scripts\environments\inspect_component_mesh_bounds.py scripts\environments\test_component_mesh_bounds.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_component_mesh_bounds.py
  -> passed
  -> identity transform, translation, 90-degree rotation, missing file, no vertices, invalid vertex values, unsupported unit, and unsupported quaternion format checks passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\inspect_component_mesh_bounds.py --mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --mesh_format obj --mesh_unit mm --mesh_scale 0.001 0.001 0.001 --mesh_position 0.0 0.0 0.0 --mesh_orientation 1.0 0.0 0.0 0.0 --output_json results\assignment_diagnostics\real_component_mesh_bounds.json
  -> passed
  -> raw bounds are reported in millimeters
  -> scaled local and transformed world bounds are reported in meters

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --result_file results\assignment_diagnostics\stage_obj_fixed12_wrapper_smoke.json --headless --device cpu
  -> passed
  -> num_viewpoints=12, noop_id=12, available_actions_shape=(1, 3, 13)

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --result_file results\assignment_diagnostics\stage_obj_sample_n6_wrapper_smoke.json --headless --device cpu
  -> passed
  -> num_viewpoints=6, noop_id=6, available_actions_shape=(1, 3, 7)

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --component_mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --component_mesh_format obj --component_mesh_unit mm --component_mesh_scale 0.001 0.001 0.001 --component_mesh_position -1.709499729 -0.830778201 -3.272299072 --component_mesh_orientation 1.0 0.0 0.0 0.0 --component_proxy_auto_from_mesh --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --result_file results\assignment_diagnostics\real_component_obj_smoke.json
  -> passed
  -> real OBJ visual mesh loaded during scene setup
  -> auto bbox proxy center ~= (0, 0, 1)
  -> auto bbox half extents=(1.800000026705, 0.842999997615, 1.182483154295)
  -> num_viewpoints=6, noop_id=6, available_actions_shape=(1, 3, 7)
```

Real OBJ mesh stage artifacts retained for inspection:

```text
results/assignment_diagnostics/real_component_mesh_bounds.json
results/assignment_diagnostics/real_component_obj_smoke.json
results/assignment_diagnostics/stage_obj_fixed12_wrapper_smoke.json
results/assignment_diagnostics/stage_obj_sample_n6_wrapper_smoke.json
```

Sample viewpoint CSV generation stage checks:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\component_mesh.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py scripts\environments\inspect_component_mesh_bounds.py scripts\environments\generate_bbox_viewpoint_csv.py scripts\environments\test_component_mesh_bounds.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_component_mesh_bounds.py
  -> passed
  -> includes base-center-to-world-origin alignment check

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\generate_bbox_viewpoint_csv.py --mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --mesh_format obj --mesh_unit mm --mesh_scale 0.001 0.001 0.001 --mesh_orientation 1.0 0.0 0.0 0.0 --align_base_center_to_world_origin --component_proxy_auto_from_mesh --viewpoint_distance 0.8 --num_height_layers 2 --points_per_side 3 --output_csv source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\real_component_bbox_sample.csv --output_json results\assignment_diagnostics\real_component_bbox_sample_generation.json
  -> passed
  -> generated_num_viewpoints=24
  -> look_at_fallback_up_count=0

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_viewpoint_csv_loader.py --csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\real_component_bbox_sample.csv --expect_num_viewpoints 24
  -> passed
  -> format=scanner_pose_world_quat_wxyz_v1, no-op id=24, ids=0..23

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\inspect_component_mesh_bounds.py --mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --mesh_format obj --mesh_unit mm --mesh_scale 0.001 0.001 0.001 --mesh_orientation 1.0 0.0 0.0 0.0 --align_base_center_to_world_origin --output_json results\assignment_diagnostics\real_component_mesh_bounds_base_center_origin.json
  -> passed
  -> raw bounds in mm; transformed world AABB has min_z=0 under model-base-center origin

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --component_mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --component_mesh_format obj --component_mesh_unit mm --component_mesh_scale 0.001 0.001 0.001 --component_mesh_orientation 1.0 0.0 0.0 0.0 --align_base_center_to_world_origin --component_proxy_auto_from_mesh --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\real_component_bbox_sample.csv --expect_num_viewpoints 24 --result_file results\assignment_diagnostics\real_component_generated_csv_smoke.json
  -> passed
  -> num_viewpoints=24, noop_id=24, available_actions_shape=(1, 3, 25)
  -> permanently_unavailable_viewpoints=[]
  -> infeasible_rows=[]

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --result_file results\assignment_diagnostics\fixed12_regression_after_generated_csv.json
  -> passed
  -> num_viewpoints=12, noop_id=12, available_actions_shape=(1, 3, 13)
  -> fixed-12 manual override remains active

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\sample_bbox_fixed6_qwxyz_world.csv --expect_num_viewpoints 6 --result_file results\assignment_diagnostics\sample_n6_regression_after_generated_csv.json
  -> passed
  -> num_viewpoints=6, noop_id=6, available_actions_shape=(1, 3, 7)

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py scripts\environments\test_assignment_harl_wrapper_smoke.py
  -> passed

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --component_mesh_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\Model\aircraft_skin_with_frame.obj --component_mesh_format obj --component_mesh_unit mm --component_mesh_scale 0.001 0.001 0.001 --component_mesh_orientation 1.0 0.0 0.0 0.0 --align_base_center_to_world_origin --component_proxy_auto_from_mesh --no-component_proxy_visual_visible --viewpoint_csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\real_component_bbox_sample.csv --expect_num_viewpoints 24 --result_file results\assignment_diagnostics\real_component_mesh_only_visual_smoke.json
  -> passed
  -> component_proxy_visual_visible=False
  -> num_viewpoints=24, noop_id=24, available_actions_shape=(1, 3, 25)

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scenario_config.py scripts\environments\test_assignment_harl_wrapper_smoke.py scripts\environments\generate_bbox_viewpoint_csv.py scripts\environments\inspect_component_mesh_bounds.py
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\generate_bbox_viewpoint_csv.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\generate_real_component_bbox_sample_csv.yaml
  -> passed
  -> generated_num_viewpoints=24

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_viewpoint_csv_loader.py --csv_path source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\viewpoints\real_component_bbox_sample.csv --expect_num_viewpoints 24
  -> passed

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\inspect_component_mesh_bounds.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --output_json results\assignment_diagnostics\real_component_bounds_from_yaml.json
  -> passed

D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml
  -> passed
  -> num_viewpoints=24, noop_id=24, available_actions_shape=(1, 3, 25)
  -> component_proxy_visual_visible=False

The CLI override smoke command
`--scenario_config real_component_bbox_sample_headless.yaml --max_steps 3` could not be executed in the current Codex
turn because the escalation runner hit the usage limit and the normal Windows sandbox failed to spawn. The parser is
implemented with scenario values as defaults before `parse_args()`, so explicit CLI values have precedence by design.

Fixed-12 and sample N=6 smokes were not rerun after the scenario-config patch in this Codex turn for the same execution
limit reason. They had passed immediately before this task, and the no-scenario CLI path remains present.
```

## Known Issues / Blockers

- Stage 3B explains the fixed-12 `robot_2 -> viewpoint_5` failure as non-simultaneous position/rotation gates under the current high-level controller path. The manual override remains with this cached reason.
- `evaluate_assignment_methods.py` is still explicitly a Phase 5 fixed-12 evaluator and still validates `num_viewpoints == 12`; do not use it as the general external-N evaluator yet.
- Static geometry does not model controller convergence, IK, collision, joint limits, occlusion, or real robot articulation.
- `real_component_bbox_sample.csv` is a temporary bbox-side smoke CSV, not a final viewpoint planning result.
- The real OBJ coordinate frame places the mesh center around z=4.27 m with identity transform. Use a matching
  `component_mesh_position` or real world-frame viewpoints; do not assume the sample N=6 viewpoints are physically
  meaningful for the unshifted mesh.

## Do Not Do

- Do not modify installed `site-packages`.
- Do not modify HARL runner core logic.
- Do not change scan env reward unless explicitly requested.
- Do not change scan env underlying 9D action space.
- Do not change `assignment_controller.py` control math.
- Do not train or run long evaluation for this stage.
- Do not use fixed-12 assignment checkpoints with a different external N.
- Do not add arbitrary/variable-N policy generalization.
- Do not add Phase 6 duplicate avoidance unless explicitly requested.
- Do not connect real robot articulation, IK, collision, or joint limits before Stage 3B+ validation.

## Next Step

Recommended next task:

```text
Review the generated bbox-side sample CSV in simulation, then replace it with measured/planned real world-frame viewpoints.
```

Keep using the bbox proxy as the algorithmic geometry source; the OBJ is visual-only until collision/raycast/coverage
is explicitly introduced later.

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
