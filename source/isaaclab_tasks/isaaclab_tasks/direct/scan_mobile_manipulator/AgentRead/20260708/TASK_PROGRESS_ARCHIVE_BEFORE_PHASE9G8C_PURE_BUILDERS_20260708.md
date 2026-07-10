# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8B is complete.

Classification:

```text
CONTRACT-FREEZE READY
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

Phase 9G-8B completed the documentation-only lifecycle observation, shared-observation, available-action-mask, PPO historical-mask replay, budget-progress, checkpoint compatibility, configuration, and training-readiness contract revision/freeze.

Resolver-enabled training remains prohibited.

## Frozen Contract Summary

Selected actor schema:

```text
lifecycle_v1_actor_3n

per-task row adds:
  self_active_target
  task_owned_by_teammate
  self_pair_failed_or_released

task_owned_by_self is builder-internal only because:
  task_owned_by_self[j] == self_active_target[j]
  for legal current resolver decision snapshots

lifecycle_actor_dim = 100 + 3M + 19N
M=3, N=50 -> 1059
```

Selected shared observation:

```text
Option A

concat(all revised lifecycle actor observations)
+
two-scalar exact active budget statistic per robot:
  active_budget_progress_norm
  active_budget_step_fraction

shared_dim = M * (100 + 3M + 19N) + 2M
M=3, N=50 -> 3183
```

Selected mask contract:

```text
action_dim = N + 1
raw target ids = 0 ... N-1
raw noop id = N
decoded noop = -1

idle robot:
  target j available only if valid, physically available/feasible,
  uncovered, not teammate-owned, and not self failed/released
  noop always available

executing robot:
  only current active target and noop are available
  executing + target k = continue k
  executing + noop = continue k
```

Selected official lifecycle profile:

```text
lifecycle_contract_c

KEEP:
  AssignmentLifecycleResolver
  Contract C
  budget tracker / trigger as resolver budget-release source
  resolver episode-persistent failed-pair rejection

DISABLE:
  legacy cooldown action-mask suppression
  redirect guardrail
  legacy failed-pair TTL memory
```

Selected checkpoint policy:

```text
ordered canonical JSON schema manifest
SHA-256 fingerprint
one project-level compatibility validator before all state-dict loads

unversioned legacy checkpoints:
  explicit legacy playback/evaluation only
  resolver disabled only
  exact shape/action/noop match required
  no default training resume
```

Selected PPO/HARL mask replay contract:

```text
sampling available_actions[t]
==
buffer available_actions[t]
==
evaluate_actions available_actions[t]

PPO update must not regenerate historical lifecycle masks
from current resolver state.
```

## Files Created / Updated

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md

source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8B_CONTRACT_FREEZE_20260708.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Not modified:

```text
Python source files
YAML/runtime configuration behavior
HARL installed package files
checkpoint loaders
observation builders
mask builders
resolver behavior
Contract C
budget behavior
```

## Validation

Documentation-only validation commands for Phase 9G-8B:

```powershell
git status --short --untracked-files=all
git diff --check
```

Result:

```text
git status --short --untracked-files=all:
  documentation-only changes:
    M  AgentRead/TASK_PROGRESS.md
    ?? AgentRead/20260708/PHASE9G8A_GPT_REVISED_FINAL_DESIGN_REVIEW.md.md
    ?? AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md
    ?? AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
    ?? AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8A_LIFECYCLE_OBSERVATION_DESIGN_AUDIT_20260708.md
    ?? AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8B_CONTRACT_FREEZE_20260708.md

git diff --check:
  passed
  warning only: TASK_PROGRESS.md LF will be replaced by CRLF the next time Git touches it
```

No `py_compile` is required because no Python source or helper script was added.

## Known Issues / Blockers

No unresolved 9G-8B contract question blocks the next phase.

Resolver-enabled training is still blocked until the frozen 17-point training-readiness gate in the 9G-8B report is implemented and validated.

## Next Step

The next allowed phase is:

```text
Phase 9G-8C:
Pure Lifecycle Snapshot and Tensor Builders
```

Phase 9G-8C may begin only after the 9G-8B report is reviewed and accepted.

## Do Not Do

Do not implement observations or masks before Phase 9G-8C is accepted and scoped.

Do not modify Python source outside the accepted phase scope.

Do not run training, short training smoke, playback, comparison-method evaluation, or Isaac Sim from this handoff.

Do not commit unless explicitly asked.

## Detailed Reports / Archives

Phase 9G-8B report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```

Phase 9G-8B TASK_PROGRESS archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8B_CONTRACT_FREEZE_20260708.md
```

Phase 9G-8A report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md
```

Phase 9G-8A final review:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8A_GPT_REVISED_FINAL_DESIGN_REVIEW.md.md
```
