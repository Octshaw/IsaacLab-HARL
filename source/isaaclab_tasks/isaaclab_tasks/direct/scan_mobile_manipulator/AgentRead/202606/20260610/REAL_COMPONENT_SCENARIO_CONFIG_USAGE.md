# Real Component Scenario Config Usage

These scenario configs shorten the real OBJ smoke and visual commands. They do not change the underlying scan task:
the OBJ is still visual-only, and the bbox proxy remains the algorithmic geometry source for feasibility, range, and
coverage diagnostics.

## Headless Smoke

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml
```

Expected key diagnostics:

```text
num_viewpoints=24
noop_id=24
available_actions_shape=(1, 3, 25)
component_proxy_visual_visible=False
```

## Visual Check

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_visual.yaml
```

The visual config hides the translucent bbox cuboid and shows the measured OBJ mesh. The script still exits after
`max_steps`; override it from the CLI if you want more viewing time.

## Generate Sample CSV

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\generate_bbox_viewpoint_csv.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\generate_real_component_bbox_sample_csv.yaml
```

This regenerates:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/real_component_bbox_sample.csv
results/assignment_diagnostics/real_component_bbox_sample_generation.json
```

## Inspect Mesh Bounds

The same real component YAML can seed the mesh bounds inspector:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\inspect_component_mesh_bounds.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --output_json results\assignment_diagnostics\real_component_bounds_from_yaml.json
```

## CLI Overrides

Scenario config values are defaults. Explicit CLI arguments override them:

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_harl_wrapper_smoke.py --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\real_component_bbox_sample_headless.yaml --max_steps 3 --device cuda:0
```

Boolean values also support explicit negation where useful, for example:

```powershell
--component_proxy_visual_visible
--no-component_proxy_visual_visible
--align_base_center_to_world_origin
--no-align_base_center_to_world_origin
```

## Important Notes

- `real_component_bbox_sample.csv` is a temporary bbox-side smoke CSV, not final viewpoint planning output.
- The world-frame convention in these configs is `model base center = world origin`.
- The OBJ mesh is not used for collision, IK, raycast, or mesh coverage.
- Fixed-12 assignment checkpoints are not compatible with `num_viewpoints=24`.
