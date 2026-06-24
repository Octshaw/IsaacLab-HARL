# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 7B-3 longer diagnostic-only obstacle-aware candidate comparisons are complete. A post-7B-3 Scheme B
mesh-sampled jittered viewpoint generator is also implemented, with side-balanced proxy placement for the active
N=50 GUI inspection CSV.

Current milestone:

```text
mesh-footprint obstacle diagnostics
obstacle-aware candidate comparison
GUI red-line debug visualization
BasisCurves visibility fix
GUI-safe timed inspection pause
longer diagnostic-only candidate comparison summaries
OBJ mesh-sampled jittered viewpoint CSV generation
side-balanced OBJ-derived proxy-surface viewpoint placement
configurable GUI debug camera pose
visual-only USD ground grid for GUI inspection
```

## Latest Completed Work

Added Scheme B irregular viewpoint generation from the component OBJ mesh, then refined the active N=50 CSV to avoid
two-cluster sampling by cycling scanner poses across the +X, -X, +Y, and -Y sides of the component proxy.

New files / outputs:

```text
scripts/environments/generate_mesh_viewpoint_csv.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/generate_component_mesh_jittered_viewpoints.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv
results/assignment_diagnostics/component_mesh_jittered_n50_generation.json
results/assignment_diagnostics/jittered_n50_side_balanced_smoke.json
```

The generator samples OBJ mesh triangles by area, creates jittered targets, offsets viewpoints using a configurable
direction mode, and writes the existing strict `scanner_pose_world_quat_wxyz_v1` CSV format. The default config uses
`normal_mode: radial_xy`, `placement_mode: proxy_surface_radial`, `sampling_mode: proxy_side_balanced`, and a moderate
z window so the generated views remain mobile-scan friendly while no longer forming a regular bbox grid. The current
generated side counts are +X=13, -X=13, +Y=12, -Y=12. `proxy_surface_radial` samples OBJ-derived target heights/directions
but places scanner poses outside the active bbox proxy and orients them toward the nearest proxy surface point, matching
the current static feasibility screen. `normal_mode: triangle_normal` is available for face-normal offset experiments.

Added GUI camera scenario settings for inspection runs:

```text
visualization.gui_camera_enabled
visualization.gui_camera_eye
visualization.gui_camera_target
```

The active `algorithm_proxy_component_mesh.yaml` sets a front-biased default camera at eye `[0.0, -7.5, 3.2]` looking at
`[0.0, 0.0, 1.1]`. This is synced into Isaac Lab's native `cfg.viewer.eye/lookat` before `DirectMARLEnv` creates its
`ViewportCameraController`; otherwise the default viewer controller overwrites camera changes made during `_setup_scene`.
The smoke/evaluator CLIs also accept `--gui_camera_eye`, `--gui_camera_target`, and `--no-gui_camera_enabled` overrides.

The same scenario now enables a visual-only USD ground grid under the debug scene. Relevant keys are:

```text
visualization.ground_grid_enabled
visualization.ground_grid_half_extent
visualization.ground_grid_spacing
visualization.ground_grid_z
visualization.ground_grid_line_width
```

This grid is a `UsdGeom.BasisCurves` visual aid only; it does not add a collision plane, physics object, reward term,
assignment cost, or mask change.

Ran Phase 7B-3 diagnostics on `algorithm_proxy_component_mesh.yaml` with `random`, `nearest`, and `greedy`.

Final output directories:

```text
results/assignment_evaluation/phase7b3_long_diag_n50_e3_s50/
results/assignment_evaluation/phase7b3_long_diag_n50_e10_s100/
```

Added:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B3_LONG_DIAGNOSTIC_COMPARISON_REPORT.md
```

Modified:

```text
scripts/environments/generate_mesh_viewpoint_csv.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/generate_component_mesh_jittered_viewpoints.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

The evaluator change is reporting-only: it adds compact obstacle-aware `per_step_summary`, `per_episode_summary`, and
alias metric names such as `baseline_selected_intersection_rate` and `candidate_selected_intersection_rate`. It does
not change solver semantics or environment behavior.

Latest verification:

```text
py_compile passed for the generator, smoke script, evaluator, scenario_config.py, and scan_mobile_manipulator_env.py.
Regenerated component_mesh_jittered_n50.csv with proxy_side_balanced side counts +X=13, -X=13, +Y=12, -Y=12.
Headless smoke passed with component_mesh_jittered_n50.csv; permanently_unavailable_viewpoints=[] and
available_viewpoints_per_agent=[[50.0, 50.0, 47.0]].
Follow-up camera fix py_compile passed after syncing gui_camera settings into cfg.viewer.eye/lookat.
Ground-grid GUI helper py_compile passed, and headless smoke confirmed `ground_grid_enabled=True` plus grid parameters in
scenario diagnostics.
```

## Active Architecture / Implementation Path

Obstacle diagnostics are still diagnostic-only:

```text
component OBJ -> approximate XY mesh footprint -> diagnostic line-intersection tensors
```

Important active fields:

```text
straight_line_cost_matrix
mesh_footprint_intersection_mask
mesh_footprint_penalty_matrix
mesh_footprint_aware_cost_matrix
```

`mesh_footprint_aware_cost_matrix` is not promoted into live solver inputs.

The Phase 7B-3 evaluator comparison still uses:

```text
baseline: normal assignment problem with cost_matrix
candidate: copied assignment problem with cost_matrix replaced by mesh_footprint_aware_cost_matrix
```

The component bbox remains metadata/debug only and is not used as hard obstacle blocking.

Red obstacle debug lines are direct robot-base-XY to viewpoint-XY diagnostic segments, not planned robot paths. Robot
motion may differ from red lines; this is expected.

The mesh-sampled viewpoint generator is an offline CSV-generation utility. It does not change solver inputs, masks,
reward, controller behavior, HARL, or training.

## Latest Verification

Latest verification:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/generate_mesh_viewpoint_csv.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/viewpoint_csv.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/generate_mesh_viewpoint_csv.py --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/generate_component_mesh_jittered_viewpoints.yaml
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/jittered_n50_proxy_nearest_aligned_smoke.json
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 3 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e3_s50 --no-write_assignment_history --compare_obstacle_aware_candidates
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 10 --max_steps 100 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e10_s100 --no-write_assignment_history --compare_obstacle_aware_candidates
```

Results passed. `component_mesh_jittered_n50.csv` was read back successfully with the strict CSV loader: N=50,
z range approximately 0.659-1.688 m. The first mesh-offset version placed scanner poses inside the active hardcoded
proxy bbox and produced all-infeasible viewpoints; the current proxy-radial/nearest-surface version passed wrapper smoke
with `permanently_unavailable_viewpoints=[]`. Final `git diff --check` and `git status` should be read from the latest
handoff or final Codex response after final checks.

Phase 7B-3 key diagnostic results:

```text
short run, e3/s50:
  random baseline_selected_intersection_rate=0.54
  nearest baseline/candidate selected_intersection_rate=0.0/0.0, changed_rate=0.0
  greedy baseline/candidate selected_intersection_rate=0.0/0.0, changed_rate=0.0

larger run, e10/s100:
  random baseline_selected_intersection_rate=0.67
  nearest baseline/candidate selected_intersection_rate=0.043333/0.043333, changed_rate=0.0
  greedy baseline/candidate selected_intersection_rate=0.043333/0.043333, changed_rate=0.0
```

## Known Issues / Limitations

- Synthetic N=50 viewpoints remain smoke/interface data only, not final benchmark evidence.
- Current synthetic N=50 scenario does not strongly stress nearest/greedy obstacle effects.
- `component_mesh_jittered_n50.csv` is a diagnostic OBJ-derived candidate set, not a final planned benchmark CSV.
- The default jittered generator config filters z to a mobile-scan-friendly band; remove/adjust `min_z` and `max_z`
  for full-surface sampling.
- Obstacle-aware candidate assignments did not differ from baseline nearest/greedy in Phase 7B-3.
- Mesh footprint is approximate XY diagnostic geometry, not 3D collision.
- Red debug lines are direct diagnostic segments, not planned robot paths.
- Current hybrid scenario keeps obstacle debug visualization enabled for manual GUI inspection; set it false for
  smoke-only runs if desired.

## Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into solver inputs yet.
- Do not replace `cost_matrix`.
- Do not change `available_mask`, `feasible_mask`, or `static_geometric_feasible_mask`.
- Do not change solver default behavior, reward, controller, `assignment_controller.py`, HARL, or training.
- Do not add RL evaluation.
- Do not add bbox hard blocking or mesh-footprint hard blocking.
- Do not add inter-robot conflict avoidance or dynamic reassignment yet.
- Do not add real robot articulation, IK, collision, joint limits, or raycast coverage.
- Do not require or use the final real planned CSV.
- Do not treat temporary/synthetic CSVs as final benchmark evidence.

## Next Step

Recommended next task:

```text
Use component_mesh_jittered_n50.csv in GUI/evaluator runs for nearest/greedy visual inspection, then decide whether
the irregular OBJ-derived viewpoints better stress obstacle diagnostics before starting Phase 7B-4.
```

Suggested override path for existing scenarios:

```text
--viewpoint_csv_path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv --expect_num_viewpoints 50
```

Interpretation:

```text
The diagnostic tooling is ready for a later gated solver-cost experiment, but current synthetic N=50 evidence alone is
weak because nearest/greedy baseline intersection rates were low and candidate costs did not change assignments or
reduce obstacle penalty. Prefer a more obstacle-stressing scenario before making solver-behavior claims.
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B3_LONG_DIAGNOSTIC_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE7B_OBSTACLE_DIAGNOSTICS_CHECKPOINT_SUMMARY.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/NEXT_PHASE_7B3_LONG_DIAGNOSTIC_COMPARISON_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B_CHECKPOINT_20260623.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_SAFE_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/GUI_INSPECTION_PAUSE_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DEBUG_LINE_VISIBILITY_PATCH_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_DIAGNOSTIC_GUI_LINE_VISUALIZATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/OBSTACLE_AWARE_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/MESH_FOOTPRINT_OBSTACLE_DIAGNOSTICS_MVP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/HYBRID_ALGORITHM_COMPONENT_MESH_SCENARIO_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/ALGORITHM_SCENARIO_DECOUPLING_REPORT.md
```
