# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8C is complete.

Classification:

```text
PASS
```

Phase 9G-7 is committed.

Commit:

```text
feat(assignment): add default-off lifecycle resolver
```

Phase 9G-8A completed the initial lifecycle-aware observation and training-readiness audit.

Phase 9G-8A final review classification:

```text
PASS WITH REQUIRED REVISIONS
```

Phase 9G-8B was accepted as:

```text
CONTRACT-FREEZE READY
```

Phase 9G-8C implemented only the pure lifecycle decision snapshot and tensor builders.

Resolver-enabled training remains prohibited.

## Latest Completed Phase

Phase 9G-8C added a pure, project-local lifecycle snapshot/tensor module:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
```

Implemented:

```text
LifecycleDecisionSnapshot
capture_lifecycle_decision_snapshot
capture_lifecycle_decision_snapshot_from_mappings
validate_lifecycle_decision_snapshot
build_actor_lifecycle_tensors
build_critic_budget_tensors
```

Frozen pure outputs:

```text
actor_lifecycle_features: [E,M,N,3]
actor_lifecycle_flat:     [E,M,3N]
feature order:            self_active_target / task_owned_by_teammate / self_pair_failed_or_released

critic_budget_features:   [E,M,2]
critic_budget_flat:       [E,2M]
feature order:            active_budget_progress_norm / active_budget_step_fraction
```

The snapshot copies tensors with `detach().clone()` and validates:

```text
task_owned_by_self == self_active_target
budget_attempt_target == active_target_id for active robots
idle budget state is target=-1, steps=0, budget_steps=0
required shapes, devices, dtypes, sentinels, and pair-state values
```

## Files Created / Updated

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
scripts/environments/test_assignment_lifecycle_observation_pure.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8C_PURE_BUILDERS_20260708.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Not modified:

```text
AssignmentHarlWrapper runtime observation integration
shared observation construction
available-action masks
observation/action spaces
HARL installed package files
checkpoint loaders/manifests
runtime YAML behavior
resolver behavior
Contract C
budget trigger/release behavior
retry/TTL/infeasibility-release behavior
```

## Latest Verification

Commands run:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py scripts/environments/test_assignment_lifecycle_observation_pure.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_pure.py --json

git diff --check

git status --short --untracked-files=all
```

Results:

```text
interpreter: C:\isaacenvs\isaac45_harl\python.exe
py_compile: passed
pure synthetic smoke: passed, 11 cases
git diff --check: passed
git status: documentation plus new pure module/test files only
```

No Isaac Sim, AppLauncher, environment construction, training, short training smoke, playback, or evaluation was run.

## Known Issues / Blockers

No Phase 9G-8C pure-builder blocker remains.

Lifecycle tensors are not yet integrated into actor observations, shared observations, or available-action masks.

Checkpoint manifests/loaders and PPO historical-mask replay enforcement remain future work.

Resolver-enabled training is still blocked until the frozen training-readiness gate from the 9G-8B report is implemented and validated.

## Do Not Do

Do not run resolver-enabled training yet.

Do not run short training smoke, playback, comparison-method evaluation, or Isaac Sim from this handoff.

Do not modify HARL installed package files.

Do not change resolver behavior, Contract C, budget trigger/release behavior, retry, TTL, or infeasibility-release semantics.

Do not commit unless explicitly asked.

## Next Step

The next possible phase is:

```text
Phase 9G-8D:
Lifecycle Actor/Shared Observation Integration
```

Phase 9G-8D should begin only after the Phase 9G-8C report is reviewed and accepted.

## Detailed Reports / Archives

Phase 9G-8C report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
```

Phase 9G-8C TASK_PROGRESS archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8C_PURE_BUILDERS_20260708.md
```

Phase 9G-8B report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```

Phase 9G-8A report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md
```
