# Phase 7B-3: Longer Diagnostic-Only Obstacle-Aware Candidate Comparisons

Date: 2026-06-23

## 1. Background

Phase 7B-1 added diagnostic-only mesh-footprint obstacle tensors from the measured component OBJ.

Phase 7B-2 added optional evaluator comparison between baseline assignment choices and obstacle-aware candidate choices
computed on a copied assignment problem.

Phase 7B-2.5 added GUI red-line visualization for sampled footprint-intersecting pairs, fixed USD `BasisCurves` line
visibility, and added a GUI-safe timed inspection pause.

The project is now ready for a longer diagnostic comparison pass. This is still not a behavior-changing phase.

## 2. Goal

Run longer diagnostic-only evaluations to determine whether baseline assignment choices select robot-viewpoint pairs
whose straight-line diagnostic segment intersects the component mesh footprint, and whether obstacle-aware candidate
costs would reduce those selections.

Keep Phase 7B-3 diagnostic-only.

## 3. Inputs

Primary scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Expected scenario properties:

```text
robots = task-space proxy/debug markers
component = measured OBJ visual mesh
viewpoints = synthetic_smoke_n50.csv
obstacle_diagnostics.enabled = true
obstacle_diagnostics.mode = diagnostics_only
obstacle_source = component_mesh_footprint
```

Optional regression scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_bbox.yaml
```

Use this only to verify that missing obstacle tensors are skipped gracefully.

## 4. Metrics

Collect compact per-step, per-episode, and per-method summaries.

Required metrics:

```text
baseline_selected_intersection_count
baseline_selected_intersection_rate
candidate_selected_intersection_count
candidate_selected_intersection_rate
candidate_changed_assignment_count
candidate_changed_assignment_rate
baseline_obstacle_penalty_sum
candidate_obstacle_penalty_sum
baseline_selected_pairs_sample
candidate_selected_pairs_sample
blocked_baseline_pairs_sample
changed_pairs_sample
per_step_summary
per_episode_summary
per_method_summary
```

Also preserve existing shape and scenario diagnostics:

```text
N
M
noop_id
available_actions shape
available_mask shape
cost_matrix shape
mesh_footprint_intersection_mask shape
mesh_footprint_intersection_count
mesh_footprint_aware_cost_matrix shape
```

Do not write huge full matrices or occupancy grids.

## 5. Methods to Compare

Run:

```text
random
nearest
greedy
```

Interpretation by method:

```text
random:
  report baseline selected-pair intersection statistics only

nearest:
  compare baseline nearest against copied-problem obstacle-aware candidate nearest

greedy:
  compare baseline greedy against copied-problem obstacle-aware candidate greedy
```

The real solver path must continue to consume:

```text
available_mask
cost_matrix
noop_id
```

## 6. Recommended Experiment Sizes

First diagnostic run:

```text
scenario = algorithm_proxy_component_mesh.yaml
methods = random nearest greedy
num_envs = 1
num_episodes = 3
max_steps = 50
compare_obstacle_aware_candidates = true
write compact JSON/CSV summaries
do not write huge full matrices
```

Suggested command pattern:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 3 --max_steps 50 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e3_s50 --no-write_assignment_history --compare_obstacle_aware_candidates
```

Larger follow-up run after checking the first output:

```text
num_episodes = 10
max_steps = 100
```

Suggested command pattern:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random nearest greedy --num_envs 1 --num_episodes 10 --max_steps 100 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase7b3_long_diag_n50_e10_s100 --no-write_assignment_history --compare_obstacle_aware_candidates
```

## 7. Output Files

Recommended output directories:

```text
results/assignment_evaluation/phase7b3_long_diag_n50_e3_s50/
results/assignment_evaluation/phase7b3_long_diag_n50_e10_s100/
```

Expected compact outputs:

```text
diagnostics.json
method summary CSV/JSON already produced by evaluator
per-step/per-episode/per-method obstacle-aware comparison summaries, if already supported
```

Avoid committing `results/` unless explicitly requested.

## 8. Verification

Before running longer diagnostics, verify the interpreter:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Run syntax checks only if Python files are changed:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_harl_wrapper_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

After each diagnostic run, inspect:

```text
diagnostics.json
methods_compared
methods_baseline_only
baseline_selected_intersection_rate
candidate_selected_intersection_rate
candidate_changed_assignment_rate
blocked_baseline_pairs_sample
changed_pairs_sample
```

Run:

```powershell
git diff --check
git status
```

## 9. Do Not Do

- Do not promote `mesh_footprint_aware_cost_matrix` into solver inputs.
- Do not replace `cost_matrix`.
- Do not change `available_mask`.
- Do not change `feasible_mask`.
- Do not change `static_geometric_feasible_mask`.
- Do not change solver default behavior.
- Do not change reward.
- Do not change controller.
- Do not change HARL or training.
- Do not add RL evaluation.
- Do not add collision, IK, raycast, real articulation, or joint limits.
- Do not hard-block viewpoints based on bbox or mesh footprint.
- Do not treat synthetic N=50 as final benchmark evidence.
- Do not dump full matrices or full occupancy grids into JSON.

## 10. Expected Interpretation

If baseline selected-intersection rate is high and candidate rate is lower:

```text
Obstacle-aware cost may be worth testing in a gated solver-cost experiment.
```

If baseline selected-intersection rate is low:

```text
The current simple scenario may not stress obstacle effects enough; use more challenging viewpoints or robot starts.
```

If candidate changes many assignments but penalty reduction is small:

```text
The penalty may be too aggressive or the diagnostic cost may be noisy.
```

If red-line diagnostics and data disagree:

```text
Revisit footprint resolution, inflation radius, and line-sampling parameters.
```

Remember:

```text
Red debug lines are direct diagnostic segments, not planned robot paths.
Robot motion may differ from the red lines.
```

## 11. Next Phase After 7B-3

Recommended next phase:

```text
Phase 7B-4:
  gated solver-cost experiment using obstacle-aware cost as an explicit opt-in solver input,
  still without touching reward/controller/RL.
```

Phase 7B-4 should only happen after Phase 7B-3 diagnostic evidence is reviewed.
