# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9B-2 fixed N=50, M=3 observation-update smoke is complete.

Phase 7B through Phase 8 wrap-up is complete and documented. Phase 9A confirms that the N=50, M=3 RL wrapper is
shape-compatible, but current observations/rewards are not yet strong enough for meaningful dynamic-policy evaluation
against the Phase 8 stagnation pattern. Phase 9B-0 now defines the fixed N=50, M=3 observation/reward design path,
including id-aligned viewpoint observation rows, mask-vs-reward boundaries, reporting-only metrics, and staged
implementation gates. Phase 9B-1 adds evaluator/reporting-only counters for repeated assignment, no-progress, duplicate
selected targets, noop-when-available, selected path cost, and load balance. Phase 9B-1A uses those counters in a
short non-RL baseline rerun to confirm the late-stage plateau. Phase 9B-2 adds a wrapper-level observation extension:
id-aligned viewpoint rows, noop context, previous-assignment memory, attempted/age counters, no-progress state, and
completion/repeated-count context.

Do not start RL training or formal RL evaluation until a future task explicitly scopes that work. Do not add more
handcrafted baseline rules unless a future task explicitly scopes them.

## Latest Documentation

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
```

Archived the previous progress file:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B8_WRAPUP_20260628.md
```

The Phase 9A readiness check changed markdown only. No Python, solver, environment, reward, controller, HARL, or
training files were changed.

The Phase 9B-0 design phase also changed markdown only. No Python, solver, environment, reward, controller, HARL,
training, formal RL evaluation, masks, feasibility logic, or dynamics were changed.

Phase 9B-1 changed only evaluator/reporting code and markdown documentation. No reward, observation, masks,
feasibility logic, solver behavior, controller logic, HARL internals, environment dynamics, RL training, or formal RL
evaluation were changed.

Phase 9B-1A changed markdown documentation only and generated diagnostic outputs. No Python files were changed.

Phase 9B-2 changed only the HARL assignment wrapper observation interface, the lightweight wrapper smoke test, and
markdown documentation. Reward behavior, available/feasible/static masks, solver behavior, controller logic, HARL
internals, environment dynamics, RL training, and formal RL evaluation were not changed.

Changed files:

```text
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_harl_wrapper_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
```

Phase 9B-1A output directory:

```text
results/assignment_evaluation/phase9b1a_plateau_diagnostic_n50_e2_s300/
```

Phase 9B-2 output file:

```text
results/assignment_diagnostics/phase9b2_observation_update_smoke_n50_m3.json
```

Phase 9A ran one wrapper compatibility smoke and wrote:

```text
results/assignment_diagnostics/phase9a_rl_readiness_n50_m3_smoke.json
```

## Phase 8 Baseline Reference

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

Run shape:

```text
N = 50
M = 3
num_episodes = 10
max_steps = 300
methods = random, nearest, greedy, nearest_conflict_aware, greedy_conflict_aware
```

Main table:

```text
random:
  success_rate = 0.0
  final_coverage = 0.004
  coverage_auc = 0.0038
  selected_target_conflict_rate = 0.4157
  inter_robot_overlap_rate = 0.6759
  actual_base_motion_intersection_rate = 0.9050

nearest / greedy:
  success_rate = 0.0
  final_coverage = 0.900
  coverage_auc = 0.7468
  selected_target_conflict_rate = 0.7191
  inter_robot_overlap_rate = 0.6689
  actual_base_motion_intersection_rate = 0.0167

nearest_conflict_aware / greedy_conflict_aware:
  success_rate = 0.0
  final_coverage = 0.900
  coverage_auc = 0.7468
  selected_target_conflict_rate = 0.6622
  inter_robot_overlap_rate = 0.5753
  actual_base_motion_intersection_rate = 0.1237
```

Stagnation:

```text
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
mean last coverage gain step = 116
mean no-progress steps after last gain = 182
late repeated assignments:
  robot_0 -> viewpoint 20
  robot_1 -> viewpoint 48
  robot_2 -> viewpoint 36
```

Interpretation: conflict-aware ablations reduce selected-target and inter-robot conflict metrics, but they do not
improve final coverage and they increase actual proxy base-motion component-footprint crossing risk. The evidence now
points toward RL/dynamic-policy readiness work rather than more handcrafted baseline variants.

## Diagnostic Boundaries

The following remain diagnostic-only:

```text
mesh_footprint_aware_cost_matrix
selected assignment lines
selected_target_conflict metrics
inter_robot_overlap metrics
actual proxy base-motion crossing metrics
```

The following were not changed by the wrap-up:

```text
cost_matrix
available_mask
feasible_mask
static_geometric_feasible_mask
solver behavior
reward
controller
assignment_controller.py
HARL
training
environment dynamics
collision / IK / raycast / path planning
```

## Verification

Phase 9B-1 compile check:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
```

Result:

```text
passed
```

Phase 9B-1 reporting smoke:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 20 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase9b1_reporting_counters_smoke_n50_e1_s20 --write_assignment_history
```

Result:

```text
passed
output_dir = results/assignment_evaluation/phase9b1_reporting_counters_smoke_n50_e1_s20
non_noop_history_count = 60
per_robot_selected_count sum = 60
per_viewpoint_attempted_count sum = 60
duplicate_selected_target_count = 0
load_balance_selected_std finite = true
load_balance_completed_std finite = true
```

Phase 9B-1A non-RL plateau diagnostic rerun:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest greedy nearest_conflict_aware greedy_conflict_aware --num_envs 1 --num_episodes 2 --max_steps 300 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --output_dir results/assignment_evaluation --output_name phase9b1a_plateau_diagnostic_n50_e2_s300 --write_assignment_history --compare_obstacle_aware_candidates
```

Result:

```text
passed
output_dir = results/assignment_evaluation/phase9b1a_plateau_diagnostic_n50_e2_s300
final_coverage = 0.900 for nearest/greedy/conflict-aware variants
final_uncovered_viewpoint_ids = [0, 20, 24, 36, 48]
last_global_coverage_gain_step = 117
no_progress_steps_after_last_gain = 182
dominant late repeated pairs = robot_0->20, robot_1->48, robot_2->36
duplicate_selected_target_count_total = 0
noop_when_available_count_total = 0
selected-count load balance std = 0.0
completed-count load balance std = 7.4087
```

Phase 9B-2 compile check:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py scripts/environments/test_assignment_harl_wrapper_smoke.py
```

Result:

```text
passed
```

Phase 9B-2 observation smoke:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless --device cpu --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --result_file results/assignment_diagnostics/phase9b2_observation_update_smoke_n50_m3.json
```

Result:

```text
passed
num_agents = 3
num_viewpoints = 50
noop_id = 50
available_actions_shape = [1, 3, 51]
available_mask_shape = [1, 3, 50]
actor_observation_shape = [1, 909]
shared_observation_shape = [1, 3, 2727]
row/action alignment passed for robot_0 viewpoint/action id 0
viewpoint 0 attempted_count_norm changed 0.0 -> 0.0033333334 after step 1
```

Final checks for this handoff:

```text
git diff --check: passed
git status --short:
  M scripts/environments/evaluate_assignment_methods.py
  M source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
  ?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
```

`git diff --check` reported Windows LF-to-CRLF warnings only; no whitespace errors.

## Next Step

Recommended next task: scope Phase 9B-3 reward implementation smoke only if the new Phase 9B-2 observation layout is
accepted. Keep it as a short smoke, not training or formal evaluation.

Start from:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
```

Do not evaluate old checkpoints on N=50. Old assignment checkpoints found in `results/isaaclab/.../assignment_happo_*`
have 13-class categorical heads, which means fixed N=12 plus noop. Old `scan_happo` checkpoints are 9D continuous
policies.

Known limitations:

```text
per_robot_completed_count uses fractional credit for simultaneous duplicate completion.
late_repeated_assignment_pattern is post-last-global-gain only; very short smoke runs may show [].
noop_when_available_count reflects the decision-time evaluator available_mask.
selected_path_cost_* reflects the decision-time evaluator cost_matrix.
Phase 9B-2 observation is fixed N=50/M=3 and flattened MLP-style, not arbitrary-N Transformer/GNN/set-based yet.
Conflict, inter-robot overlap, and actual base-motion crossing remain reporting/diagnostic signals, not reward or mask
logic.
```

Do not proceed directly to RL training, formal RL evaluation, solver behavior changes, controller changes, mask changes,
retry/fallback/cooldown behavior, or new handcrafted baseline rules. Do not implement reward changes unless a separate
Phase 9B-3 task explicitly scopes a smoke-only reward implementation.

Phase 9B-2 implemented observation support for:

```text
id-aligned full viewpoint rows
per-viewpoint attempted counts
previous assignment id and consecutive same-target count
steps since last global coverage gain
per-robot completed count
full uncovered/available state
conflict/crossing diagnostics as reporting or critic-side context first
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE7B_TO_PHASE8_BASELINE_DIAGNOSTIC_WRAPUP.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_PLAN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9A_RL_DYNAMIC_POLICY_READINESS_CHECK_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B_OBSERVATION_REWARD_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE9B1_REPORTING_COUNTERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B1A_PLATEAU_COUNTER_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9B2_OBSERVATION_UPDATE_SMOKE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE7B8_WRAPUP_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260628/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE8_BASELINE_VALIDATION_20260628.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7E_ACTUAL_BASE_MOTION_CROSSING_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D2_CONFLICT_AWARE_BASELINE_VARIANTS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260625/PHASE7D1_TARGET_CONFLICT_CANDIDATE_COMPARISON_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7C_INTER_ROBOT_PROXY_CONFLICT_DIAGNOSTICS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
```
