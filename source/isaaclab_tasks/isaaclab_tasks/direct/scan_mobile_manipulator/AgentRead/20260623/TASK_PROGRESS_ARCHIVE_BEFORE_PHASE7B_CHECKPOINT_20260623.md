# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2.5 Patch 3: GUI-Safe Inspection Pause is complete.

The wrapper smoke script no longer uses terminal `input()` for GUI inspection. It now supports a timed pause that keeps Isaac Sim / Kit responsive by calling `simulation_app.update()` during the pause.

No assignment behavior changed: `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver default behavior, reward, controller math, `assignment_controller.py`, the 9D action path, HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast coverage, and final real CSV validation were not changed.

## Latest Completed Phase

Phase 7B-2.5 Patch 3: GUI-Safe Inspection Pause.

Modified files:

```text
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_SAFE_PAUSE_PATCH_20260623.md
```

## Implementation Summary

Existing pause trigger flags remain:

```text
--pause_after_setup
--gui_pause
```

New timed pause flag:

```text
--pause_after_setup_seconds
```

Behavior:

```text
no pause request:
  pause_after_setup_mode=disabled

non-headless pause request:
  pause_after_setup_mode=timed_app_update
  pause duration is --pause_after_setup_seconds, or 300 seconds if only --pause_after_setup/--gui_pause is used

headless pause request:
  pause_after_setup_mode=headless_skip
  no blocking and no sleep
```

The timed pause happens after reset and initial diagnostics have populated obstacle debug line prims. It does not step the environment during the pause.

Result JSON fields:

```text
pause_after_setup_requested
pause_after_setup_applied
pause_after_setup_seconds
pause_after_setup_mode
```

## Manual GUI Usage

Run without `--headless`:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 20 --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/gui_safe_pause_manual.json --pause_after_setup_seconds 300
```

During the timed pause, inspect:

```text
/World/envs/env_0/ObstacleDebugLines
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

Use Frame Selected in the Stage panel. The smoke run resumes automatically when the timer expires.

## Latest Verification

Syntax check passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Normal headless smoke without pause passed:

```text
result_file=results/assignment_diagnostics/gui_safe_pause_normal_smoke.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
pause_after_setup_requested=false
pause_after_setup_applied=false
pause_after_setup_seconds=0
pause_after_setup_mode=disabled
```

Headless pause-skip smoke passed:

```text
result_file=results/assignment_diagnostics/gui_safe_pause_headless_skip.json
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
pause_after_setup_requested=true
pause_after_setup_applied=false
pause_after_setup_seconds=0
pause_after_setup_mode=headless_skip
```

The headless run printed:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

## Known Issues / Limitations

- Manual GUI timed pause was not run from Codex because it requires interactive GUI inspection.
- The timed pause pumps the SimulationApp / Kit UI and does not step the environment.
- There is no interactive early-exit key for the timed pause; use a shorter `--pause_after_setup_seconds` for quick checks.
- The current hybrid scenario keeps obstacle debug visualization enabled for manual GUI inspection; set `enabled: false` for smoke-only runs.
- Synthetic N=50 viewpoints remain interface smoke data, not final benchmark evidence.

## Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into actual solver inputs.
- Do not replace `cost_matrix`, `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver default behavior, reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add bbox hard blocking, mesh-footprint hard blocking, inter-robot conflict avoidance, or dynamic reassignment yet.
- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.

## Next Step

Recommended next task:

```text
Run the manual GUI timed pause command and inspect /World/envs/env_0/ObstacleDebugLines/BlockedPath_000, then proceed to Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
```

Keep Phase 7B-3 diagnostic-only unless a later gated task explicitly promotes an obstacle-aware candidate into solver inputs.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_SAFE_PAUSE_PATCH_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_STAGE_ALGORITHM_SCENARIO_AND_PROXY_CONSTRAINTS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/YAML_CAPABILITY_PROFILES_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_INSPECTION_GUIDE.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_VISUAL_MESH_FOLLOW_PROXY_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
```
