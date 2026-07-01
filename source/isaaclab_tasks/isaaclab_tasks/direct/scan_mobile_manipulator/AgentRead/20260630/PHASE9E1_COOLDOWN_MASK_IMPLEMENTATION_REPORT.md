# Phase 9E-1 Cooldown Mask Implementation Report

Date: 2026-06-30

## 1. Scope And Boundaries

Phase 9E-1 implemented a config-gated, per-robot-target temporary cooldown for assignment RL only.

The mechanism is wrapper-local to `AssignmentHarlWrapper` and affects only HARL `available_actions` when explicitly enabled. It does not change reward formulas, reward scales, actor/shared observation dimensions, static feasibility, controller behavior, solver behavior, path planning, collision/local avoidance, environment dynamics, HARL algorithms, installed site-packages, or baseline solver behavior.

Cooldown remains globally/default disabled. No commit was made.

## 2. Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E0_STUCK_TARGET_RECOVERY_COOLDOWN_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D3_100K_TRAINING_AND_PLAYBACK_DIAGNOSTIC_ANALYSIS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2B_RL_PLAYBACK_DIAGNOSTICS_SETUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9D2A_LOGGER_REWARD_WHITELIST_CLEANUP_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260629/PHASE9D1A_ASSIGNMENT_HISTORY_RESET_DIAGNOSTIC_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml
```

## 3. Files Changed

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260630/PHASE9E1_COOLDOWN_MASK_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## 4. Config Fields And Defaults

Defaults were added to `ScanMobileManipulatorEnvCfg` and read by `AssignmentHarlWrapper`.

```yaml
assignment_cooldown_enabled: false
assignment_cooldown_scope: per_robot_target
assignment_cooldown_trigger_attempts: 3
assignment_cooldown_trigger_same_target_streak: 10
assignment_cooldown_trigger_steps_since_global_gain: 10
assignment_cooldown_duration_steps: 20
assignment_cooldown_require_uncovered: true
assignment_cooldown_require_available: true
assignment_cooldown_require_feasible: true
assignment_cooldown_require_no_global_gain: true
assignment_cooldown_clear_on_covered: true
assignment_cooldown_apply_to_action_mask: true
assignment_cooldown_log_diagnostics: true
```

`scenario_config.py` now allows these fields as flat scenario keys and also supports an `assignment_cooldown:` block with shorter names.

The default scenario `algorithm_proxy_component_mesh.yaml` was not enabled. A dedicated smoke/debug scenario was added:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

## 5. Cooldown State Variables

`AssignmentHarlWrapper` now allocates runtime-device tensors:

```text
_per_robot_target_failed_attempt_count: [num_envs, num_agents, num_viewpoints], torch.long
_per_robot_target_cooldown_remaining: [num_envs, num_agents, num_viewpoints], torch.long
```

Additional diagnostics:

```text
_assignment_cooldown_trigger_count: [num_envs]
_assignment_cooldown_suppressed_count: [num_envs, num_agents]
_assignment_cooldown_selected_target_was_in_cooldown_count: [num_envs]
_assignment_cooldown_last_triggered_viewpoint: [num_envs, num_agents]
_last_cooldown_active_for_selected_pair: [num_envs, num_agents]
_last_cooldown_remaining_for_selected_pair: [num_envs, num_agents]
_last_cooldown_triggered_after_step: [num_envs, num_agents]
_last_failed_attempt_count_for_selected_pair: [num_envs, num_agents]
_last_cooldown_suppressed_available_count_for_robot: [num_envs, num_agents]
```

## 6. Mask Filtering Logic

Disabled path remains the previous implementation:

```python
make_assignment_action_mask(problem, include_noop=True)
```

Enabled path:

```text
base_available_mask = problem["available_mask"]
cooldown_mask = _per_robot_target_cooldown_remaining > 0
filtered_available_mask = base_available_mask & ~cooldown_mask
available_actions = concat(filtered_available_mask, noop_column)
```

The base env `available_mask` is not mutated. The noop column remains available. The wrapper and HARL facade both guard against all-zero rows. Shape remains `[num_envs, num_agents, num_viewpoints + 1]`, i.e. `[1, 3, 51]` for the fixed N=50/M=3 path.

## 7. Trigger Condition

Cooldown updates after each assignment step, using selected actions and pre/post coverage.

For selected non-noop `(robot_i, viewpoint_j)`, a failed attempt is counted only when:

```text
selected_available was true in the pre-step filtered mask
selected_feasible was true
covered_before was false
global_coverage_gain == 0
steps_since_global_coverage_gain >= configured threshold, when threshold > 0
```

A cooldown triggers when the selected pair has enough failed attempts or enough same-target streak:

```text
failed_attempt_count >= assignment_cooldown_trigger_attempts
or same_target_streak >= assignment_cooldown_trigger_same_target_streak
```

When triggered:

```text
_per_robot_target_cooldown_remaining[env, agent, viewpoint] = duration_steps
_assignment_cooldown_trigger_count += triggered_pair_count
_assignment_cooldown_last_triggered_viewpoint[env, agent] = viewpoint
```

The implementation uses global coverage gain as the progress signal, as scoped in Phase 9E-0. It does not attempt robot-target-specific coverage attribution.

## 8. Reset Behavior

The existing `_reset_assignment_diagnostics(...)` helper now also clears cooldown state.

Confirmed behavior:

- Explicit `AssignmentHarlWrapper.reset()` clears cooldown state.
- Done-env partial reset clears cooldown state only for completed env ids.
- Cooldown and failed-attempt state clear for viewpoints that become covered.
- Returned next `available_actions` are built after done-env wrapper reset, preventing terminal cooldown state from leaking into the next episode mask.

## 9. Diagnostics Added

Wrapper `info` now includes an `assignment_cooldown` block when diagnostics are enabled:

```text
assignment_cooldown/enabled
assignment_cooldown/active_count_mean
assignment_cooldown/trigger_count_mean
assignment_cooldown/triggered_pair_count
assignment_cooldown/suppressed_action_count_mean
assignment_cooldown/failed_attempt_count_mean
assignment_cooldown/max_cooldown_remaining_mean
assignment_cooldown/selected_target_was_in_cooldown_count
assignment_cooldown/last_triggered_viewpoint
```

`assignment_harl_training.py` flattens this namespace into TensorBoard as `assignment_cooldown.*`.

This does not pollute `Total_Reward`: the Phase 9D-2A exact whitelist remains only:

```text
assignment_rl_reward/final_reward_mean
```

Playback diagnostics were extended with:

```text
cooldown_enabled
cooldown_trigger_count
cooldown_active_count
cooldown_suppressed_count
max_cooldown_remaining
cooldown_active_for_selected_pair
cooldown_remaining_for_selected_pair
cooldown_triggered_after_step
cooldown_suppressed_available_count_for_robot
failed_attempt_count_for_selected_pair
```

## 10. Observation And Reward Compatibility

Observation dimensions were not changed:

```text
actor obs = 909
shared obs per agent = 2727
available_actions = [num_envs, 3, 51]
```

No cooldown fields were added to actor observations or shared observations.

Reward formulas and defaults were not changed. No cooldown penalty was added. `Total_Reward` remains based on `assignment_rl_reward/final_reward_mean`.

## 11. Smoke/Test Results

Python compile passed:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_wrapper.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_training.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scenario_config.py source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_assignment_rl_playback_diagnostics.py scripts\environments\test_assignment_cooldown_mask_smoke.py
```

Cooldown mask smoke passed:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts\environments\test_assignment_cooldown_mask_smoke.py --result_file results\assignment_diagnostics\phase9e1_assignment_cooldown_mask_smoke.json
```

Smoke JSON:

```text
results/assignment_diagnostics/phase9e1_assignment_cooldown_mask_smoke.json
```

Confirmed:

```text
disabled mask matches baseline = true
manual selected robot-target pair masked = true
same viewpoint remains available to other robots = true
noop available = true
no all-zero rows = true
cooldown decrements = true
covered target clears cooldown/failed count = true
full reset clears state = true
done-env partial reset clears completed env only = true
actor obs shape = [2, 909]
shared obs shape = [2, 3, 2727]
available_actions shape = [2, 3, 51]
```

## 12. Training-Entry Re-Check Results

Cooldown disabled smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9e1_cooldown_disabled_recheck_1k2 --save_interval 5 --log_interval 1
```

Result: passed.

Key evidence:

```text
cooldown config enabled = False
available_actions shape = (1, 3, 51)
assignment_cooldown.enabled = 0.0
assignment_cooldown.active_count = 0.0
assignment_cooldown.triggered_pair_count = 0.0
nonfinite scalar values = 0
final Total_Reward = -19.7488689
final assignment_rl_reward/final_reward_mean = -0.06582956
models and best_model directories exist
```

Output:

```text
results/assignment_diagnostics/phase9e1_cooldown_disabled_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e1_cooldown_disabled_recheck_1k2/seed-00001-2026-06-30-23-04-38
```

Cooldown enabled smoke:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/reinforcement_learning/harl/train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --num_env_steps 1200 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml --assignment_episode_length 300 --exp_name assignment_happo_n50_phase9e1_cooldown_enabled_recheck_1k2 --save_interval 5 --log_interval 1
```

Result: passed.

Key evidence:

```text
cooldown config enabled = True
available_actions shape = (1, 3, 51)
assignment_cooldown.enabled = 1.0
final assignment_cooldown.active_count = 35.8867
final assignment_cooldown.triggered_pair_count = 1.8833
assignment_cooldown.selected_target_was_in_cooldown_count = 0.0
nonfinite scalar values = 0
final Total_Reward = -19.8166389
final assignment_rl_reward/final_reward_mean = -0.06605546
models and best_model directories exist
```

Output:

```text
results/assignment_diagnostics/phase9e1_cooldown_enabled_recheck_1k2_console.log
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e1_cooldown_enabled_recheck_1k2/seed-00001-2026-06-30-23-08-09
```

TensorBoard scalar sanity for both tiny runs:

```text
scalar_tags = 46
nonfinite_scalar_values = 0
```

## 13. Explicit Non-Changes

- No reward formula or reward scale default changes.
- No cooldown reward penalty.
- No actor/shared observation dimension changes.
- No cooldown observation features.
- No static feasibility changes.
- No base env `available_mask` mutation.
- No controller, path planning, solver, collision, local avoidance, or environment dynamics changes.
- No HARL algorithm or installed site-package changes.
- No baseline solver behavior changes.
- No default scenario cooldown enablement.
- No formal evaluation or long training.
- No commit.

## 14. Known Limitations

- Progress attribution is global coverage gain only, not robot-target-specific.
- Failed-attempt counts are episode-local and are cleared on covered targets/reset, but are not promoted to team-level cooldown.
- Per-robot cooldown can still allow another robot to try the same difficult target.
- Mask-only cooldown is not visible in actor observations except through HARL available-actions masking.
- The enabled 1.2k training smoke validates plumbing only; it is not policy-quality evidence.
- Playback cooldown diagnostics were extended, but no checkpoint playback was run in this phase.

## 15. Next Recommendation

If smokes remain clean, run one scoped 100k single-seed cooldown-enabled debug training with the explicit debug scenario:

```text
algorithm_proxy_component_mesh_assignment_cooldown_debug.yaml
```

Then run playback diagnostics on `models/` and `best_model`, compare against the Phase 9D-3 no-cooldown 100k reference, and specifically check:

```text
max_same_target_streak
late_repeated_assignment_count
final_coverage
coverage_auc
noop_when_available_rate
selected_target_conflict_rate
assignment_cooldown trigger/active/suppressed counts
```

Do not run 100k training until after reviewing this Phase 9E-1 implementation and smoke report.
