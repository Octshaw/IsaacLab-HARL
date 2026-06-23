# GUI Inspection Pause Patch Report

## Purpose

Phase 7B-2.5 can now author visible obstacle debug line prims under:

```text
/World/envs/env_0/ObstacleDebugLines
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

The GUI smoke command still continued into the smoke loop immediately, making manual Stage inspection awkward. This patch adds a tooling-only pause option to the wrapper smoke script so the user can inspect the Stage after reset and initial diagnostics have populated obstacle debug visuals.

This patch does not change assignment behavior, environment dynamics, solver behavior, costs, masks, reward, controller behavior, HARL, training, collision, IK, raycast coverage, or task lifecycle semantics.

## Files Modified

```text
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_PAUSE_PATCH_20260623.md
```

## CLI Flag Added

The smoke script now accepts:

```text
--pause_after_setup
```

It also accepts the optional alias:

```text
--gui_pause
```

Default behavior remains unchanged when the flag is omitted.

## Pause Location

The pause is applied after:

```text
environment creation
wrapper reset
initial obs/shared_obs/available_actions validation
manual action decode validation
initial assignment diagnostics call
```

The initial diagnostics call uses the existing `_reset_diagnostics()` path. This calls the existing assignment problem / diagnostics machinery so obstacle debug line prims are available before the pause begins.

The terminal prints:

```text
[PAUSE] GUI inspection pause.
Check the Stage panel for:
  /World/envs/env_0/ObstacleDebugLines
  /World/envs/env_0/ObstacleDebugLines/BlockedPath_000
Select BlockedPath_000 and use Frame Selected if needed.
Press Enter in this terminal to continue the smoke run...
```

After Enter, the original smoke loop continues unchanged.

## Headless Behavior

If `--pause_after_setup` is requested with `--headless`, the script does not block. It prints:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

Then the smoke loop continues normally.

## Result JSON Fields

The smoke result JSON now includes:

```text
pause_after_setup_requested
pause_after_setup_applied
```

Expected values:

```text
normal run without flag:
  requested=false
  applied=false

headless run with flag:
  requested=true
  applied=false

GUI non-headless run with flag:
  requested=true
  applied=true
```

## Verification Results

Interpreter check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Output:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Syntax check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Normal headless smoke without pause passed:

```text
result_file=results/assignment_diagnostics/gui_pause_patch_normal_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
pause_after_setup_requested=false
pause_after_setup_applied=false
```

Headless pause-skip smoke passed:

```text
result_file=results/assignment_diagnostics/gui_pause_patch_headless_skip_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
pause_after_setup_requested=true
pause_after_setup_applied=false
```

The command printed:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

Evaluator regression passed:

```text
output_dir=results/assignment_evaluation/gui_pause_patch_eval_regression
methods=random, nearest, greedy
compare_obstacle_aware_candidates=true
```

## Manual Command

Run without `--headless`:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 20 --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/gui_pause_patch_manual.json --pause_after_setup
```

Expected manual result:

```text
GUI opens
script pauses after setup and initial diagnostics
Stage contains /World/envs/env_0/ObstacleDebugLines
Frame Selected on /World/envs/env_0/ObstacleDebugLines/BlockedPath_000 works
pressing Enter resumes the smoke loop
```

## Known Limitations

- Codex did not run the manual GUI pause test because it requires interactive GUI inspection and terminal input.
- The pause is a smoke-script tool only; it is not part of the environment API.
- The pause does not keep the GUI open after the smoke finishes. Use a higher `--max_steps` or pause at setup for inspection, then press Enter when ready.

## Scope Confirmation

This patch is tooling-only. It does not change:

```text
cost_matrix
available_mask
feasible_mask
static_geometric_feasible_mask
solver default behavior
mesh_footprint_aware_cost_matrix usage
reward
controller math
assignment_controller.py
9D action path
HARL core
training
real robot articulation
IK
collision
joint limits
raycast coverage
final real CSV validation
```

## Next Recommended Step

Run the manual GUI pause command and inspect:

```text
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

After visual confirmation, continue with Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
