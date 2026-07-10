# Phase 9G-8C Pure Lifecycle Snapshot And Tensor Builders Report

Date: 2026-07-08

## Classification

```text
PASS
```

Phase 9G-8C implemented only the pure lifecycle decision-snapshot and tensor-building layer. No lifecycle tensors were integrated into runtime actor observations, shared observations, available-action masks, HARL rollout execution, checkpoint loading, training, playback, or evaluation.

## Files Created / Modified

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
scripts/environments/test_assignment_lifecycle_observation_pure.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8C_PURE_BUILDERS_20260708.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No existing Python runtime file was modified. No HARL installed package file was modified.

## Source Boundaries Inspected

Required docs:

- `AgentRead/AGENTS.md`
- `AgentRead/TASK_PROGRESS.md`
- `AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md`
- `AgentRead/20260708/PHASE9G8A_GPT_REVISED_FINAL_DESIGN_REVIEW.md`
- `AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md`

Source boundaries:

- `assignment_lifecycle_resolver.py`
- `assignment_lifecycle_resolver_runtime.py`
- `assignment_harl_wrapper.py`
- `assignment_rl_interface.py`
- `assignment_state.py`
- `scan_mobile_manipulator_env.py`

The implementation imports canonical resolver constants from `assignment_lifecycle_resolver.py` and does not duplicate pair-state or sentinel numeric meanings.

## Snapshot Type And Field List

Implementation location:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
```

Snapshot type:

```text
LifecycleDecisionSnapshot
```

Metadata:

```text
snapshot_generation: int
episode_generation: [E] torch.long
num_envs: property from active_target_id
num_robots: property from active_target_id
num_tasks: property from task_owner_robot_id
device: property from active_target_id
contract_version: lifecycle_decision_snapshot_v1
```

Copied tensors:

```text
active_target_id: [E,M] torch.long
task_owner_robot_id: [E,N] torch.long
pair_state: [E,M,N] torch.long
budget_attempt_target: [E,M] torch.long
budget_attempt_steps: [E,M] torch.long
budget_attempt_budget_steps: [E,M] torch.long
viewpoints_covered: [E,N] torch.bool
available_mask: [E,M,N] torch.bool
feasible_mask: [E,M,N] torch.bool
task_valid: [E,N] torch.bool, defaults to all true for current fixed N
budget_attempt_expected_steps: optional [E,M] torch.long
budget_attempt_initial_cost: optional [E,M] torch.float32
```

Capture helpers:

```text
capture_lifecycle_decision_snapshot(...)
capture_lifecycle_decision_snapshot_from_mappings(...)
```

## No-Alias / Immutability Design

`LifecycleDecisionSnapshot.__post_init__` copies every supplied tensor with:

```text
detach().clone()
```

This prevents later in-place mutation of resolver, wrapper, or assignment-problem source tensors from altering an already captured snapshot. Builder outputs are also cloned into named result dataclasses. The dataclasses are frozen as Python objects, but the important Phase 9G-8C guarantee is no aliasing to authoritative mutable runtime tensors.

The synthetic no-alias test mutates source tensors after capture, including:

```text
active_target_id
task_owner_robot_id
pair_state
budget_attempt_steps
budget_attempt_budget_steps
viewpoints_covered
available_mask
feasible_mask
```

The captured snapshot and previously built actor/critic outputs remain unchanged.

## Generation Design

The caller supplies:

```text
snapshot_generation
episode_generation
```

Builder results propagate the exact `snapshot_generation`:

```text
actor_result.snapshot_generation == input_snapshot.snapshot_generation
critic_result.snapshot_generation == input_snapshot.snapshot_generation
```

Generation is diagnostics metadata only. It is not appended to actor or critic network tensors.

## Actor Feature Definitions And Order

Builder:

```text
build_actor_lifecycle_tensors(snapshot)
```

Canonical unflattened output:

```text
actor_lifecycle_features: [E,M,N,3] torch.float32
```

Flattened output:

```text
actor_lifecycle_flat: [E,M,3N] torch.float32
```

Feature order:

```text
0 self_active_target
1 task_owned_by_teammate
2 self_pair_failed_or_released
```

Definitions:

```text
self_active_target[e,r,j] =
    active_target_id[e,r] == j

task_owned_by_teammate[e,r,j] =
    task_owner_robot_id[e,j] != NO_OWNER
    and task_owner_robot_id[e,j] != r

self_pair_failed_or_released[e,r,j] =
    pair_state[e,r,j] in {PAIR_FAILED_BUDGET, PAIR_RELEASED_BUDGET}
```

Flattening preserves robot-major, task-major, feature-within-task order:

```text
task0_active, task0_teammate_owned, task0_failed_released,
task1_active, task1_teammate_owned, task1_failed_released,
...
```

Documented future dimensions, not activated at runtime:

```text
legacy_actor_dim = 100 + 3M + 16N
lifecycle_actor_dim = 100 + 3M + 19N

M=3, N=50:
actor lifecycle add-on = 150
legacy_actor_dim = 909
lifecycle_actor_dim = 1059
```

## Critic Budget Feature Definitions And Order

Builder:

```text
build_critic_budget_tensors(snapshot)
```

Canonical unflattened output:

```text
critic_budget_features: [E,M,2] torch.float32
```

Flattened output:

```text
critic_budget_flat: [E,2M] torch.float32
```

Feature order:

```text
0 active_budget_progress_norm
1 active_budget_step_fraction
```

Definitions for active robots:

```text
denominator = max(budget_attempt_budget_steps, 1)

active_budget_progress_norm =
    clamp(budget_attempt_steps / denominator, 0, 1)

active_budget_step_fraction =
    1 / denominator
```

Inactive robots output:

```text
0, 0
```

The integer source tensors remain the behavior source of truth. The normalized critic budget features do not replace or modify the wrapper release predicate.

Documented future shared Option A dimensions, not activated at runtime:

```text
shared_dim = M * (100 + 3M + 19N) + 2M

M=3, N=50:
critic budget add-on = 6
future shared dim = 3183
```

## Shape / Dtype / Device Contracts

Validator:

```text
validate_lifecycle_decision_snapshot(snapshot)
```

Validation covers:

```text
active_target_id [E,M] torch.long
task_owner_robot_id [E,N] torch.long
pair_state [E,M,N] torch.long
budget_attempt_target [E,M] torch.long
budget_attempt_steps [E,M] torch.long
budget_attempt_budget_steps [E,M] torch.long
viewpoints_covered [E,N] torch.bool
available_mask [E,M,N] torch.bool
feasible_mask [E,M,N] torch.bool
task_valid [E,N] torch.bool
all tensors on one device
indices either canonical sentinels or in range
pair_state values in known resolver pair states
```

Tests were run on CPU. CUDA was not required for completion.

## Ownership-Active Invariant

The validator derives:

```text
task_owned_by_self[e,r,j] =
    task_owner_robot_id[e,j] == r

self_active_target[e,r,j] =
    active_target_id[e,r] == j
```

It enforces:

```text
task_owned_by_self == self_active_target
```

`task_owned_by_self` remains builder-internal and is not exposed as an actor feature.

Additional active-pair validation enforces:

```text
active target -> pair_state == PAIR_ACTIVE
PAIR_ACTIVE -> active target
```

Invalid synthetic snapshots for both "owned by self but no active target" and "active target but owner differs" raise clear `ValueError`s.

## Budget-Target Alignment Invariant

For active robots, the validator enforces:

```text
budget_attempt_target == active_target_id
budget_attempt_steps >= 1
budget_attempt_budget_steps >= 1
```

For idle robots, it enforces the frozen inactive budget representation:

```text
budget_attempt_target == -1
budget_attempt_steps == 0
budget_attempt_budget_steps == 0
```

If optional budget diagnostics are supplied, idle robots must also have:

```text
budget_attempt_expected_steps == 0
budget_attempt_initial_cost == 0
```

Invalid synthetic snapshots for active target `k` with budget target `j != k`, and idle robots with non-empty budget attempts, raise clear `ValueError`s.

## Test Cases And Results

Test file:

```text
scripts/environments/test_assignment_lifecycle_observation_pure.py
```

Cases:

```text
idle_snapshot
active_claim
multiple_robots_tasks_and_flatten_order
failed_and_released_pair_encoding
budget_statistic_distinguishes_denominators
ownership_active_invariant_failure
budget_target_alignment_failure
reset_like_state
snapshot_immutability
generation_shape_dtype_and_dimensions
shape_device_dtype_validation
```

Result:

```text
11 / 11 passed
```

The budget statistic test confirms `9/10` and `90/100` have approximately equal progress values but different step fractions. It also covers `1/1`, `1/1000`, and inactive robot output.

## Validation Commands And Results

Interpreter check:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Result:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Syntax check:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py scripts/environments/test_assignment_lifecycle_observation_pure.py
```

Result:

```text
passed
```

Pure synthetic test:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_pure.py --json
```

Result:

```text
passed: 11 cases
```

Repository whitespace/status checks were run after documentation updates and are recorded in `TASK_PROGRESS.md`.

Whitespace check:

```powershell
git diff --check
```

Result:

```text
passed
warning only: TASK_PROGRESS.md LF will be replaced by CRLF the next time Git touches it
```

Status check:

```powershell
git status --short --untracked-files=all
```

Result:

```text
M  AgentRead/TASK_PROGRESS.md
?? scripts/environments/test_assignment_lifecycle_observation_pure.py
?? AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
?? AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8C_PURE_BUILDERS_20260708.md
?? assignment_lifecycle_observation.py
```

The status output also includes untracked Phase 9G-8A and 9G-8B documentation artifacts from earlier phases; those were preserved and not modified by Phase 9G-8C.

## Known Limitations

- The new module is not integrated into `AssignmentHarlWrapper`.
- Actor observation spaces and shared observation spaces remain unchanged.
- Available-action masks remain unchanged.
- Checkpoint manifests/loaders remain unimplemented.
- PPO historical mask replay remains a frozen contract only; no HARL package behavior was modified.
- The current implementation reserves `task_valid` with a fixed-N all-true default, but does not implement true variable-N policy behavior.
- Active-target infeasibility release, retry TTL, stranded-task recovery, abort/switch/release actions, explicit continue action redesign, and Transformer/GNN policy architecture remain deferred.

## Explicit Non-Integration Statement

Phase 9G-8C did not:

```text
integrate lifecycle tensors into actor observations
integrate lifecycle tensors into shared observations
integrate lifecycle-aware available-action masks
change observation spaces
change action spaces
modify HARL installed package files
modify checkpoint loading
modify runtime YAML behavior
change resolver behavior
change Contract C
change budget trigger or release behavior
change retry, TTL, or infeasibility-release behavior
run training
run short training smoke
run playback
run evaluation
launch Isaac Sim
commit
```

## Next-Phase Boundary

The next possible phase is:

```text
Phase 9G-8D:
Lifecycle Actor/Shared Observation Integration
```

Phase 9G-8D must not begin until this 9G-8C report is reviewed and accepted. Resolver-enabled training remains prohibited.
