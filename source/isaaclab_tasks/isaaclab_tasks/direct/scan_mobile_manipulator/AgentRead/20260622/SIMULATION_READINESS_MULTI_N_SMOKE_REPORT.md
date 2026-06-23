# Simulation Readiness Multi-N Smoke Report

Date: 2026-06-22

## Purpose

This report records a simulation-readiness smoke pass for arbitrary legal viewpoint CSV sizes. It verifies interface
stability only:

```text
N = number of loaded viewpoints
M = number of enabled robots
noop_id = N
available_actions shape = [num_envs, M, N + 1]
available_mask shape = [num_envs, M, N]
cost_matrix shape = [num_envs, M, N]
```

This is not a final algorithm benchmark. The final real planned viewpoint CSV was not used.

## Viewpoint Sources

- Fixed/default fixed-12 regression path: `N=12`.
- Temporary bbox-side sample: `configs/viewpoints/real_component_bbox_sample.csv`, `N=24`, loaded through
  `configs/scenarios/real_component_bbox_sample_headless.yaml` so the matching mesh-derived component proxy is present.
- Synthetic smoke CSVs generated for interface validation only:
  - `configs/viewpoints/synthetic_smoke_n50.csv`
  - `configs/viewpoints/synthetic_smoke_n100.csv`
  - `configs/viewpoints/synthetic_smoke_n200.csv`

The inferred strict CSV schema is `scanner_pose_world_quat_wxyz_v1` with columns:

```text
id, pose_type, coordinate_frame, units, quaternion_order, scanner_forward_axis, scanner_up_axis,
viewpoint_quaternion_meaning, x, y, z, qw, qx, qy, qz
```

Required row conventions are `pose_type=scanner_pose_in_world`, `coordinate_frame=world`, `units=meters`,
`quaternion_order=qw,qx,qy,qz`, `scanner_forward_axis=+X`, `scanner_up_axis=+Z`, and
`viewpoint_quaternion_meaning=scanner_frame_orientation_in_world`. IDs are contiguous zero-based file-order IDs.

## Commands

Synthetic files were generated with:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/generate_synthetic_viewpoints.py --num_viewpoints <N> --output <synthetic_smoke_csv>
```

Wrapper smokes used:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 1 --headless --device cpu --robot_config_path <robots_yaml> --result_file <result_json>
```

For external CSV checks, the command also supplied `--viewpoint_csv_path <csv>` and `--expect_num_viewpoints <N>`.
For the temporary `N=24` sample, the command used `--scenario_config
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/real_component_bbox_sample_headless.yaml`.

Evaluator smokes used:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --methods random nearest greedy --num_envs 1 --num_episodes 1 --max_steps 1 --headless --device cpu --robot_config_path <robots_yaml> --output_dir results/assignment_evaluation --output_name <name> --no-write_assignment_history
```

## Wrapper Smoke Results

| Case | Source | N | M | noop_id | available_actions |
| --- | --- | ---: | ---: | ---: | --- |
| `sim_ready_n12_m2_smoke.json` | fixed/default | 12 | 2 | 12 | `[1, 2, 13]` |
| `sim_ready_n12_m3_smoke.json` | fixed/default | 12 | 3 | 12 | `[1, 3, 13]` |
| `sim_ready_n12_m4_smoke.json` | fixed/default | 12 | 4 | 12 | `[1, 4, 13]` |
| `sim_ready_n24_m3_smoke.json` | temporary bbox-side scenario | 24 | 3 | 24 | `[1, 3, 25]` |
| `sim_ready_n50_m2_smoke.json` | synthetic smoke | 50 | 2 | 50 | `[1, 2, 51]` |
| `sim_ready_n50_m3_smoke.json` | synthetic smoke | 50 | 3 | 50 | `[1, 3, 51]` |
| `sim_ready_n50_m4_smoke.json` | synthetic smoke | 50 | 4 | 50 | `[1, 4, 51]` |
| `sim_ready_n100_m3_smoke.json` | synthetic smoke | 100 | 3 | 100 | `[1, 3, 101]` |
| `sim_ready_n200_m3_smoke.json` | synthetic smoke | 200 | 3 | 200 | `[1, 3, 201]` |

All wrapper smokes passed.

## Evaluator Smoke Results

| Case | Source | N | M | noop_id | available_actions | available_mask | cost_matrix | Solver status |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `sim_ready_n12_m3_eval_smoke` | fixed/default | 12 | 3 | 12 | `[1, 3, 13]` | `[1, 3, 12]` | `[1, 3, 12]` | `random`, `nearest`, `greedy` completed |
| `sim_ready_n24_m3_eval_smoke` | temporary bbox-side scenario | 24 | 3 | 24 | `[1, 3, 25]` | `[1, 3, 24]` | `[1, 3, 24]` | `random`, `nearest`, `greedy` completed |
| `sim_ready_n50_m3_eval_smoke` | synthetic smoke | 50 | 3 | 50 | `[1, 3, 51]` | `[1, 3, 50]` | `[1, 3, 50]` | `random`, `nearest`, `greedy` completed |
| `sim_ready_n100_m3_eval_smoke` | synthetic smoke | 100 | 3 | 100 | `[1, 3, 101]` | `[1, 3, 100]` | `[1, 3, 100]` | `random`, `nearest`, `greedy` completed |
| `sim_ready_n200_m3_eval_smoke` | synthetic smoke | 200 | 3 | 200 | `[1, 3, 201]` | `[1, 3, 200]` | `[1, 3, 200]` | `random`, `nearest`, `greedy` completed |

All evaluator smokes passed. The reported coverage/success values are intentionally not interpreted because each smoke
uses only one step and synthetic or temporary inputs.

## Notes And Skips

- A direct CSV-only `N=24` wrapper attempt with the default component proxy was not used as the validating path because
  the temporary sample is tied to the real-component mesh-derived bbox proxy. The matching scenario path passed.
- Full `N x M` coverage was not attempted. The selected matrix covers fixed-12 `M=2/3/4`, temporary `N=24/M=3`,
  synthetic `N=50/M=2/3/4`, and synthetic `N=100/M=3` and `N=200/M=3`.
- No final real planned viewpoint CSV was used.
- No training, GUI, long simulation, assignment-RL evaluation, controller tuning, reward changes, HARL core changes, real
  robot articulation, IK, collision, joint limits, or raycast coverage work was performed.

## Conclusion

The simulation/evaluator interface remained stable across the tested fixed/default, temporary, and synthetic legal
viewpoint sets. The next recommended step is to decide whether this smoke evidence is sufficient to accept the
simulation-only interface path, then plan the next dynamic assignment extension without treating the temporary or
synthetic CSVs as final benchmark evidence.
