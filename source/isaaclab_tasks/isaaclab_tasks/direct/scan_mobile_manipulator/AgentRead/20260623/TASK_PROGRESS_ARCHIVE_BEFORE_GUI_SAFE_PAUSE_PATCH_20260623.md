# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-2.5 Patch 2: GUI Inspection Pause is complete.

The wrapper smoke script now has a tooling-only pause option so a GUI run can stop after reset and initial diagnostics, letting the user inspect obstacle debug line prims under:

```text
/World/envs/env_0/ObstacleDebugLines
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

No assignment behavior changed: `cost_matrix`, `available_mask`, `feasible_mask`, `static_geometric_feasible_mask`, solver default behavior, reward, controller math, `assignment_controller.py`, the 9D action path, HARL core, training behavior, real robot articulation, IK, collision, joint limits, raycast coverage, and final real CSV validation were not changed.

## Latest Completed Phase

Phase 7B-2.5 Patch 2: GUI Inspection Pause.

Modified files:

```text
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_PAUSE_PATCH_20260623.md
```

## Implementation Summary

New smoke-script flags:

```text
--pause_after_setup
--gui_pause
```

When requested in a non-headless run, the script pauses after:

```text
environment creation
wrapper reset
initial obs/shared_obs/available_actions validation
manual assignment decode validation
initial assignment diagnostics call that populates obstacle debug line visuals
```

The pause prints the Stage paths to inspect and waits for Enter before continuing the original smoke loop.

When requested with `--headless`, the script prints:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

and continues without blocking.

Result JSON now includes:

```text
pause_after_setup_requested
pause_after_setup_applied
```

## Manual GUI Usage

Use:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 20 --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/gui_pause_patch_manual.json --pause_after_setup
```

At the pause, inspect:

```text
/World/envs/env_0/ObstacleDebugLines
/World/envs/env_0/ObstacleDebugLines/BlockedPath_000
```

Select `BlockedPath_000` and use Frame Selected if needed, then press Enter in the terminal to continue.

## Latest Verification

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

The headless pause-skip run printed:

```text
[PAUSE-SKIP] --pause_after_setup requested but the run is headless.
```

Evaluator regression passed:

```text
output_dir=results/assignment_evaluation/gui_pause_patch_eval_regression
methods=random, nearest, greedy
compare_obstacle_aware_candidates=true
```

## Known Issues / Limitations

- Manual GUI pause was not run from Codex because it requires interactive GUI inspection and terminal input.
- The pause is only in `test_assignment_harl_wrapper_smoke.py`; it is not an environment feature.
- The pause occurs once after setup. It does not pause after every step.
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
Run the manual GUI pause command and inspect /World/envs/env_0/ObstacleDebugLines/BlockedPath_000, then proceed to Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons.
```

Keep Phase 7B-3 diagnostic-only unless a later gated task explicitly promotes an obstacle-aware candidate into solver inputs.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_GUI_PAUSE_PATCH_20260623.md
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
