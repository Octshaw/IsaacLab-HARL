# Phase 9G-8D Lifecycle Actor / Shared Observation Integration Report

Date: 2026-07-08

## Classification

```text
PASS
```

Phase 9G-8D integrated the accepted Phase 9G-8C lifecycle decision snapshot and pure tensor builders into the project-local HARL wrapper actor-observation and Option A shared-observation paths.

No lifecycle-aware available-action mask, PPO historical-mask replay, checkpoint compatibility loader, checkpoint manifest file, training enablement, playback, evaluation, or Isaac Sim runtime was added or run.

## Files Created / Modified

Created:

```text
scripts/environments/test_assignment_lifecycle_observation_integration.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8D_OBSERVATION_INTEGRATION_20260708.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Inspected and reused without changing the accepted pure feature contract:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
scripts/environments/test_assignment_lifecycle_observation_pure.py
```

## Source Boundaries Inspected

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
assignment_lifecycle_observation.py
assignment_harl_wrapper.py
assignment_lifecycle_resolver.py
assignment_lifecycle_resolver_runtime.py
assignment_rl_interface.py
assignment_state.py
scenario_config.py
scan_mobile_manipulator_env.py
assignment_harl_training.py
```

## Profile / Schema Implementation

Added the high-level assignment lifecycle profile boundary:

```text
assignment_lifecycle_profile
```

Recognized profiles:

```text
legacy
lifecycle_ablation
lifecycle_contract_c
diagnostics_hidden_state
```

Default profile:

```text
legacy
```

`legacy` resolves to:

```text
actor schema: legacy_v1
shared schema: legacy_v1_shared_actor_concat
resolver: disabled
lifecycle observation: disabled
mask behavior: existing legacy behavior
training: allowed
```

`lifecycle_ablation` resolves to:

```text
actor schema: lifecycle_v1_actor_3n
shared schema: lifecycle_v1_shared_option_a_budget2m
resolver: disabled
lifecycle observation: enabled
mask behavior: existing legacy behavior
training: not used in this phase
```

`lifecycle_contract_c` is recognized but normal training is blocked with a clear error because lifecycle mask and PPO historical-mask replay are not implemented yet:

```text
lifecycle_contract_c observation integration exists, but lifecycle mask / PPO historical-mask replay is not yet ready;
resolver-enabled training remains prohibited.
```

`diagnostics_hidden_state` preserves the legacy observation schema with resolver diagnostics enabled and is not training-ready.

## Legacy-Path Isolation

The legacy branch does not append zero lifecycle fields and does not route actor observations through lifecycle task-row composition.

Frozen legacy dimensions remain:

```text
legacy_actor_dim = 100 + 3M + 16N
legacy_shared_dim = M * legacy_actor_dim

M=3, N=50:
legacy_actor_dim = 909
legacy_shared_dim = 2727
```

Regression checks passed for:

```text
legacy actor shape: [E,909]
legacy shared shape: [E,M,2727]
legacy action space: Discrete(51)
legacy available_actions == make_assignment_action_mask(...)
legacy lifecycle generation metadata absent
legacy task-row width: 14
```

## Snapshot Ownership And Timing

The wrapper now owns lifecycle decision metadata for lifecycle observation profiles:

```text
_lifecycle_snapshot_generation
_lifecycle_episode_generation [E]
_last_lifecycle_decision_snapshot
_last_actor_lifecycle_tensor_result
_last_critic_budget_tensor_result
_last_actor_observation_generation
_last_shared_observation_generation
```

Snapshot generation rule:

```text
starts at 0
increments once for each newly captured lifecycle decision snapshot
is copied into the LifecycleDecisionSnapshot
is propagated through actor/shared build results
is diagnostics metadata only and is not appended to network input
```

Episode generation rule:

```text
starts at 0 per environment
increments for all environments on wrapper reset
increments only for done/reset env ids during step cleanup
is copied into the LifecycleDecisionSnapshot
is diagnostics metadata only and is not appended to network input
```

Reset capture order implemented:

```text
env reset
problem capture
wrapper diagnostic/budget reset
resolver reset
episode generation increment
lifecycle snapshot capture
actor observation build
shared observation build
existing available-actions build
return
```

Step capture order implemented:

```text
pre-step problem
existing available-actions build
proposal decode
resolver resolve_pre_step
effective assignment
environment step
post-step problem
wrapper diagnostics/budget update
resolver observe_post_step
done-env resolver reset
done-env diagnostic/budget reset
done-env episode generation increment
single lifecycle snapshot capture
actor observation build
shared observation build
existing available-actions build
return
```

Phase 9G-8D claims only:

```text
actor observation generation == shared observation generation
```

It does not claim available-actions generation equality; lifecycle available-action integration remains Phase 9G-8E work.

## Actor Observation Layout

The wrapper reuses:

```text
capture_lifecycle_decision_snapshot(...)
build_actor_lifecycle_tensors(...)
```

The lifecycle fields are inserted inside each task row. They are not appended as independent tail blocks.

Lifecycle task-row order:

```text
0  relative_viewpoint_position_x
1  relative_viewpoint_position_y
2  relative_viewpoint_position_z
3  viewpoint_quaternion_w
4  viewpoint_quaternion_x
5  viewpoint_quaternion_y
6  viewpoint_quaternion_z
7  covered_flag
8  available_flag
9  feasible_flag
10 static_geometric_feasible_flag
11 normalized_selected_path_cost
12 per_viewpoint_attempted_count_norm
13 per_viewpoint_last_attempt_age_norm
14 self_active_target
15 task_owned_by_teammate
16 self_pair_failed_or_released
```

Lifecycle actor dimension:

```text
lifecycle_actor_dim = 100 + 3M + 19N

M=3, N=50:
lifecycle_actor_dim = 1059
```

Each agent observation remains:

```text
obs[agent_id]: [E, lifecycle_actor_dim]
```

## Shared Observation Layout

The wrapper implements frozen Option A:

```text
shared_flat =
    concat(all revised lifecycle actor observations in agent order)
    +
    critic_budget_flat
```

Budget features are built with:

```text
build_critic_budget_tensors(snapshot)
```

Frozen final shared order:

```text
actor_obs_robot_0
actor_obs_robot_1
...
actor_obs_robot_M-1
active_budget_progress_norm_robot_0
active_budget_step_fraction_robot_0
active_budget_progress_norm_robot_1
active_budget_step_fraction_robot_1
...
active_budget_progress_norm_robot_M-1
active_budget_step_fraction_robot_M-1
```

Lifecycle shared dimension:

```text
lifecycle_shared_dim = M * (100 + 3M + 19N) + 2M

M=3, N=50:
lifecycle_shared_dim = 3183
```

HARL EP convention is preserved:

```text
shared_flat: [E,3183]
share_obs:   [E,M,3183]
```

Every agent receives the same repeated shared tensor.

## Observation Spaces

Legacy profile:

```text
actor observation space: unchanged, [909] for M=3,N=50
shared observation space: unchanged, [2727] for M=3,N=50
action space: unchanged, Discrete(51)
```

Lifecycle observation profiles:

```text
actor observation space: [1059] for M=3,N=50
shared observation space: [3183] for M=3,N=50
action space: unchanged, Discrete(51)
noop raw id: 50
noop decoded value: -1
```

Startup/runtime assertions check generated actor/shared tensor shapes against declared spaces.

## Available-Actions Non-Change Evidence

Phase 9G-8D did not modify:

```text
_build_available_actions()
make_assignment_action_mask(...)
available_actions shape
available_actions dtype
noop availability
legacy cooldown/redirect/failed-pair guardrail behavior
```

Synthetic integration tests assert:

```text
legacy available_actions == make_assignment_action_mask(problem, include_noop=True)
lifecycle_ablation available_actions == make_assignment_action_mask(problem, include_noop=True)
```

Lifecycle masks and PPO historical-mask replay remain unimplemented.

## In-Memory Schema Manifest

`AssignmentHarlWrapper.assignment_observation_schema_manifest` now exposes ordered, in-memory schema metadata:

```text
profile_name
actor_schema_version
actor_task_row_order
actor_tail_field_order
actor_dimension
actor_dimension_by_agent
shared_schema_version
critic_budget_schema_version
shared_construction_mode
shared_ordered_blocks
shared_dimension
M
N
action_dimension
noop_raw_id
noop_decoded_value
snapshot_contract_version
```

No checkpoint manifest file is saved in this phase. Stable SHA-256 checkpoint fingerprints and project-level loader compatibility validation remain Phase 9G-8F work.

## Tests And Results

Commands run with Conda environment:

```powershell
conda run -n isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py scripts/environments/test_assignment_lifecycle_observation_pure.py scripts/environments/test_assignment_lifecycle_observation_integration.py

conda run -n isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_pure.py --json

conda run -n isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_integration.py --json
```

Results:

```text
py_compile: passed
Phase 9G-8C pure tests: passed, 11 cases
Phase 9G-8D integration tests: passed, 6 cases
```

Integration test coverage:

```text
legacy actor/shared/action-space shape regression
legacy available-actions non-change
lifecycle actor shape and task-row placement
lifecycle shared shape and actor/budget block ordering
same-snapshot actor/shared generation propagation
partial reset episode-generation update
post-update/reset state alignment
lifecycle-ablation zero state
observation-space consistency
in-memory manifest ordering
```

## Runtime Smoke Details

No Isaac Sim/AppLauncher bounded runtime smoke was run.

The integration coverage uses synthetic tensors and a lightweight fake wrapper environment only.

## Known Limitations

Lifecycle-aware available-action masks are not implemented.

PPO historical-mask replay is not implemented.

Checkpoint schema manifests are in-memory only; no manifest file saving, fingerprinting, or loader compatibility validation is implemented.

Resolver-enabled training remains prohibited.

`lifecycle_contract_c` observation integration is recognized, but normal training is blocked until Phase 9G-8E and Phase 9G-8F readiness work is complete.

Compact shared Option B was not implemented.

No retry, TTL, infeasibility-release, abort/switch/release action, explicit continue action, resolver behavior, Contract C, or budget trigger/release behavior changed.

## Next-Phase Boundary

The next possible phase is:

```text
Phase 9G-8E:
Lifecycle Available-Action Mask and PPO Historical-Mask Replay Integration
```

Phase 9G-8E remains separate. It must not be inferred as complete from this observation-only integration.
