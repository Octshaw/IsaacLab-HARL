# GUI-Safe Inspection Pause Patch Report

## Purpose

The previous GUI inspection pause in `test_assignment_harl_wrapper_smoke.py` used terminal `input()` after setup. In an Isaac Sim GUI run, blocking the main Python thread can make the Kit window appear unresponsive. This patch replaces that blocking pause with a timed loop that keeps the SimulationApp / Kit UI updating.

This is tooling-only. It does not change environment behavior, assignment logic, solver behavior, costs, masks, reward, controller behavior, HARL, training, collision, IK, raycast coverage, or task lifecycle semantics.

## Files Modified

```text
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Files Added

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_SAFE_PAUSE_PATCH_20260623.md
```

## Why `input()` Was Removed

The old pause waited for terminal input:

```text
input()
```

That can block the main Python thread while Isaac Sim / Kit needs periodic app updates to keep the GUI responsive. A GUI inspection pause should not freeze the viewport or Stage panel.

## New CLI Behavior

Existing flags remain:

```text
--pause_after_setup
--gui_pause
```

New timed pause flag:

```text
--pause_after_setup_seconds <seconds>
```

Behavior:

```text
no pause flags and seconds <= 0:
  no pause, mode=disabled

--pause_after_setup or --gui_pause with seconds <= 0:
  non-headless uses 300 seconds

--pause_after_setup_seconds > 0:
  non-headless pauses for the requested duration

headless with any pause request:
  no blocking, mode=headless_skip
```

## GUI Responsiveness

The pause loop uses:

```text
simulation_app.update()
```

until the timer expires. It does not step the environment during the pause.

Pause start message:

```text
[PAUSE] GUI inspection pause for <N> seconds.
The GUI should remain responsive.
Inspect:
  /World/envs/env_0/ObstacleDebugLines
  /World/envs/env_0/ObstacleDebugLines/BlockedPath_000
Use Frame Selected in the Stage panel.
The smoke run will continue automatically when the timer expires.
```

The loop prints a remaining-time message every 30 seconds. At the end it prints:

```text
[PAUSE-END] GUI inspection pause finished; continuing smoke run.
```

## Result JSON Fields

The result JSON now includes:

```text
pause_after_setup_requested
pause_after_setup_applied
pause_after_setup_seconds
pause_after_setup_mode
```

Expected values:

```text
GUI timed pause:
  requested=true
  applied=true
  pause_after_setup_seconds=300.0 or requested value
  pause_after_setup_mode=timed_app_update

Headless requested:
  requested=true
  applied=false
  pause_after_setup_mode=headless_skip

No pause:
  requested=false
  applied=false
  pause_after_setup_seconds=0.0
  pause_after_setup_mode=disabled
```

## Verification

Syntax check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Normal headless smoke without pause passed:

```text
result_file=results/assignment_diagnostics/gui_safe_pause_normal_smoke.json
pause_after_setup_requested=false
pause_after_setup_applied=false
pause_after_setup_seconds=0
pause_after_setup_mode=disabled
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

Headless pause skip passed:

```text
result_file=results/assignment_diagnostics/gui_safe_pause_headless_skip.json
pause_after_setup_requested=true
pause_after_setup_applied=false
pause_after_setup_seconds=0
pause_after_setup_mode=headless_skip
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
```

The headless run printed:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

## Manual Command

Run without `--headless`:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 20 --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/gui_safe_pause_manual.json --pause_after_setup_seconds 300
```

Expected manual result:

```text
GUI opens
script pauses for 300 seconds
GUI remains responsive
Stage can inspect /World/envs/env_0/ObstacleDebugLines/BlockedPath_000
smoke continues automatically after timer
pause_after_setup_requested=true
pause_after_setup_applied=true
pause_after_setup_mode=timed_app_update
```

## Known Limitations

- The manual GUI timed pause was not run from Codex because it requires interactive GUI inspection.
- The timed loop pumps the app UI but does not step the environment during the pause.
- The smoke script does not provide an interactive early-exit key; use a shorter `--pause_after_setup_seconds` for quick checks.

## Scope Confirmation

This patch does not change:

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

Run the manual GUI timed pause command and inspect:

```text
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

After visual confirmation, continue with Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
