# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8D is complete.

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

Phase 9G-8C was accepted as:

```text
PASS
```

Phase 9G-8D integrated lifecycle tensors into actor observations and Option A shared observations.

Legacy observation/shared paths remain exact and default.

Resolver-enabled training remains prohibited.

## Latest Completed Phase

Phase 9G-8D added project-local observation profile/schema selection:

```text
legacy
lifecycle_ablation
lifecycle_contract_c
diagnostics_hidden_state
```

Default:

```text
legacy
```

Lifecycle actor task-row fields are inserted at per-task row indices:

```text
14 self_active_target
15 task_owned_by_teammate
16 self_pair_failed_or_released
```

Lifecycle actor dimension:

```text
100 + 3M + 19N
M=3,N=50 -> 1059
```

Lifecycle shared dimension:

```text
M * (100 + 3M + 19N) + 2M
M=3,N=50 -> 3183
```

Option A shared observation is:

```text
concat(all lifecycle actor observations in agent order)
+
critic budget flat [E,2M]
```

The wrapper now owns lifecycle snapshot and episode generation metadata for observation construction. Actor and shared lifecycle tensors are built from the same captured snapshot generation.

Available-action masks were not changed.

PPO historical-mask replay was not implemented.

Checkpoint compatibility/loaders were not implemented.

No lifecycle tensors have been integrated into available-action masks.

No HARL installed package was modified.

No resolver, Contract C, ownership, budget trigger/release, retry, TTL, or infeasibility-release behavior changed.

No training, short training smoke, playback, evaluation, or Isaac Sim run occurred.

## Latest Verification

Commands run:

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

No bounded Isaac Sim/AppLauncher runtime smoke was run.

## Next Step

The next possible phase is:

```text
Phase 9G-8E:
Lifecycle Available-Action Mask and PPO Historical-Mask Replay Integration
```

Do not start Phase 9G-8E until the Phase 9G-8D report is reviewed and accepted.

## Detailed Reports / Archives

Phase 9G-8D report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
```

Phase 9G-8D TASK_PROGRESS archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8D_OBSERVATION_INTEGRATION_20260708.md
```

Phase 9G-8C report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
```

Phase 9G-8B report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```
