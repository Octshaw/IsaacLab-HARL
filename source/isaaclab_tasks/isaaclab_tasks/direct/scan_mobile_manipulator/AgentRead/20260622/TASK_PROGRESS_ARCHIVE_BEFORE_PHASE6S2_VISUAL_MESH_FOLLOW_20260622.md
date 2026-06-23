# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Scene Assembly MVP Phase 6S is complete.

The project now has a repeatable scene-assembly smoke path with:

```text
component visual asset path: existing Model/aircraft_skin_with_frame.obj
robot proxy config: configs/robots/robots_real_proxy.yaml
scenario config: configs/scenarios/real_scene_proxy_headless.yaml
viewpoint source: configs/viewpoints/synthetic_smoke_n50.csv
```

This remains a task-space proxy scene. No real robot articulation, IK, collision, joint limits, raycast coverage,
controller math, reward logic, `assignment_controller.py`, HARL core, training behavior, assignment-RL evaluation, or
final real CSV validation was changed or run.

The final real planned viewpoint CSV remains intentionally reserved for later final validation. Temporary and synthetic
CSV results are interface smoke evidence only, not final benchmark evidence.

## Latest Completed Phase

Scene Assembly MVP Phase 6S.

Added files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S_SCENE_ASSEMBLY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/README.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_real_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_scene_proxy_headless.yaml
```

Modified files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/robot_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Implementation summary:

- Added a Phase 6S scene assembly plan.
- Added `robots_real_proxy.yaml` with three enabled task-space proxy robots using known capability profiles.
- Added optional `visual_usd_path` preservation to `robot_config.py`; this is diagnostics metadata only.
- Added an asset README documenting component/robot visual asset staging, units, frames, and current limitations.
- Added `real_scene_proxy_headless.yaml`, which references:
  - `robots_real_proxy.yaml`;
  - existing visual-only component OBJ `Model/aircraft_skin_with_frame.obj`;
  - synthetic smoke viewpoint CSV `synthetic_smoke_n50.csv`;
  - default bbox proxy behavior with `component_proxy.auto_from_mesh=false`.

No large binary assets were added.

## Scene Assumptions

- Runtime coordinates are meters.
- Quaternions use scalar-first `qw, qx, qy, qz`.
- Robot `initial_pose_world` uses `[x, y, z, qw, qx, qy, qz]`.
- STEP assets should be converted to mesh or USD before use.
- Component and robot visual assets are scene/proxy inputs only; they do not participate in collision, IK, raycast
  coverage, reward, or controller behavior.

## Robot Proxy Config Summary

`robots_real_proxy.yaml`:

```text
robot_0: enabled, task_space_proxy, mobile_scanner_a, pose=[-4.0, -2.0, 0.0, 1.0, 0.0, 0.0, 0.0]
robot_1: enabled, task_space_proxy, mobile_scanner_b, pose=[0.0, 3.5, 0.0, 0.70710678, 0.0, 0.0, -0.70710678]
robot_2: enabled, task_space_proxy, mobile_scanner_c, pose=[4.0, -2.0, 0.0, 0.0, 0.0, 0.0, 1.0]
```

Diagnostics include:

```text
num_configured_robots=3
num_enabled_robots=3
enabled_robot_names=["robot_0", "robot_1", "robot_2"]
agent_id_by_name={"robot_0": 0, "robot_1": 1, "robot_2": 2}
visual_usd_path_by_robot={...}
```

The `visual_usd_path` values are placeholders for future visual USD files and are not spawned in Phase 6S.

## Latest Verification

Phase 5 lightweight checks were rerun before Phase 6S changes and passed:

```text
Python interpreter check: C:\isaacenvs\isaac45_harl\python.exe
py_compile: assignment_state.py, scan_mobile_manipulator_env.py, test_assignment_harl_wrapper_smoke.py,
evaluate_assignment_methods.py
wrapper smoke: N=12, M=3
evaluator smoke: N=12, M=3 with random/nearest/greedy
```

Phase 6S checks passed:

```text
py_compile robot_config.py
robot_config.py loader check for robots_real_proxy.yaml
wrapper smoke with real_scene_proxy_headless.yaml
evaluator smoke with real_scene_proxy_headless.yaml and random/nearest/greedy
```

Wrapper smoke result:

```text
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
result_file=results/assignment_diagnostics/scene_assembly_phase6s_real_scene_proxy_smoke.json
```

Evaluator smoke result:

```text
N=50, M=3, noop_id=50
available_actions=[1, 3, 51]
available_mask=[1, 3, 50]
cost_matrix=[1, 3, 50]
task_status=[1, 50]
robot_status=[1, 3]
methods=random, nearest, greedy completed one CPU/headless step
diagnostics=results/assignment_evaluation/scene_assembly_phase6s_real_scene_proxy_eval_smoke/diagnostics.json
```

## Known Issues / Limitations

- Robot visual USD paths are preserved in diagnostics but the files are not present and are not spawned.
- The component OBJ is visual-only. The smoke scenario keeps bbox proxy behavior stable with `auto_from_mesh=false`.
- No `task_runtime_state` or `robot_runtime_state` vector fields exist yet.
- Dynamic assignment lifecycle statuses beyond conservative Phase 5 `unassigned/completed` and `idle` remain future work.
- `real_component_bbox_sample.csv` remains temporary bbox-side pipeline sanity data, not final viewpoint planning output.
- Temporary and synthetic CSVs must not be used as final algorithm-performance benchmarks.
- Full 7D `initial_pose_world` is preserved in robot config diagnostics, but the current proxy state remains yaw-only.

## Do Not Do

- Do not train assignment-RL or add assignment-RL evaluation.
- Do not modify HARL core or installed `site-packages`.
- Do not change reward, controller math, `assignment_controller.py`, or the 9D action path.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage yet.
- Do not wait for or require the final real planned CSV.
- Do not treat temporary/synthetic CSV results as final benchmark evidence.
- Do not commit large STEP, USD, mesh, or generated binary assets without explicit approval.

## Next Step

Recommended next task:

```text
Review and accept the Phase 6S scene assembly smoke path, then decide whether the next slice should add visual USD
asset ingestion/spawning for non-articulated robot visuals or return to dynamic assignment lifecycle/runtime-state
interfaces.
```

Possible next implementation slice:

1. If visual scene fidelity is next, add non-articulated robot visual USD spawning guarded behind optional existing paths.
2. If assignment semantics are next, identify a reliable current-task ownership signal for `TASK_ASSIGNED` or
   `TASK_IN_PROGRESS`.
3. Keep fixed/default, temporary, and synthetic inputs as interface-validation data until final real CSV validation is
   intentionally scheduled.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/DYNAMIC_ASSIGNMENT_STATE_INTERFACE_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/SIMULATION_READINESS_MULTI_N_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/NEXT_STAGE_ROBOT_CONFIG_MVP_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE6S_SCENE_ASSEMBLY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE5_STATE_INTERFACE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE4_SIM_READY_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE3_CONDENSE_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260622/TASK_PROGRESS_ARCHIVE_BEFORE_ROBOT_CONFIG_MVP_HANDOFF_20260622.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260610/REAL_COMPONENT_SCENARIO_CONFIG_USAGE.md
```
