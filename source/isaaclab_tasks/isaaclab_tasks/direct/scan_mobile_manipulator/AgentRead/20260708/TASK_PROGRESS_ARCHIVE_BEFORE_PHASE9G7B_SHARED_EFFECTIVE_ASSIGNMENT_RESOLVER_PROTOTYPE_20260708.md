# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-7A effective-assignment resolver / active-target latch design audit is complete.

The user manually committed the complete Phase 9G-6 block before Phase 9G-7A.

Post-commit baseline:

```text
git status --short: clean
git log -1 --oneline: 91c731af feat(assignment): add passive shared lifecycle diagnostics
```

Phase 9G-6 is closed. Phase 9G-7A begins from the committed passive lifecycle diagnostics baseline.

Phase 9G-7A was documentation/design only.

No Python source files were modified. No assignment behavior changed. No playback or comparison-method evaluation ran. No training or short training smoke ran. No commit was made.

## Latest Completed Phase

Phase 9G-7A created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_DESIGN_20260708.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Selected Resolver Architecture

Selected architecture:

```text
shared standalone resolver first
later env promotion only after validation
```

The future resolver should sit between standardized method proposal and controller conversion:

```text
method-specific output
  -> method adapter / decoder
  -> assignment_proposal [E, M]
  -> shared AssignmentLifecycleResolver
  -> effective_assignment [E, M]
  -> viewpoint_assignment_to_actions()
  -> controller / environment
```

The resolver, not the RL wrapper, should own first-prototype behavior-driving active-target state.

The env remains authoritative for physical state and `viewpoints_covered`.

The controller remains a consumer of `effective_assignment`; it does not own lifecycle state.

## Selected Contract C Semantics

Selected Contract C:

```text
target action starts an assignment when idle
repeating the active target explicitly counts as continue
noop while idle means remain idle
noop while executing means continue current active target
noop never means release in the first prototype
release is event-driven
```

First prototype release events:

```text
completion from viewpoints_covered
budget-trigger failure/release from existing diagnostics
reset
```

Deferred:

```text
no-progress failure
reach violation failure
infeasibility release
explicit release action
timeout independent of budget
```

## Selected Switching, Ownership, And Arbitration Rules

Switching:

```text
switching while executing is rejected in the first prototype
effective assignment continues the current active target
switching may become configuration-gated later
```

Ownership:

```text
at most one active target per robot
at most one owner per task
ownership created only by accepted idle/released target claim
ownership cleared on completion, budget release, or reset
completed tasks retain no owner
one robot failure never globally fails a task
pair failure is robot-target scoped
```

Same-step arbitration:

```text
existing active ownership has priority over new claims
lowest path cost wins simultaneous new claims on an unowned open target
robot id breaks exact cost ties
robot id fallback is used when costs are unavailable or non-finite
losing idle robots get effective noop and remain idle
```

The resolver should not claim to solve nearby target conflict, path crossing, overlap, or near-miss behavior.

## Selected Default-Off Boundary

Recommended future config:

```text
assignment_lifecycle_resolver_enabled = False
```

When disabled:

```text
effective_assignment == assignment_proposal
current target-every-step behavior is preserved
current noop semantics are preserved
no persistent active target affects control
no ownership affects control
old checkpoints remain behavior-identical
random/nearest/greedy remain behavior-identical
```

When enabled:

```text
proposal is interpreted through the resolver
active-target latch may change effective assignment
Contract C semantics become active
the MDP changes even if action shape remains [M, N+1]
```

## Observation / Training Gate

No lifecycle training until the policy can observe all behavior-driving lifecycle state.

Training-ready lifecycle requires at least:

```text
robot_is_idle
robot_is_executing
active_target_id or embedding
task_claimed
task_owner relation
attempt age
pair failed/released state
failure/release reason if behavior depends on it
```

Short training smoke may be allowed only in a later observation-integration phase. Long training remains user-run only.

## Recommended Next Phase

Recommended Phase 9G-7B:

```text
pure shared effective-assignment resolver prototype
disabled by default
fake-sequence smoke tests only
no runtime integration
```

Likely files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/PHASE9G7B_..._REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Required fake-sequence coverage:

```text
default-off identity
idle target claim
idle noop
executing same-target continuation
noop-as-continue
switch while executing rejected
completion release
budget failure release
same-robot failed-pair retry rejection
teammate claim after another robot budget-fails the target
subset/full reset
simultaneous exact-target arbitration
owned-target proposal rejection
covered-target proposal rejection
invalid proposal handling
variable E/M/N
input non-mutation
```

Do not integrate into runtime paths in 9G-7B unless the user explicitly changes scope.

## Latest Verification

Documentation-only validation:

```powershell
git status --short --untracked-files=all
git diff --check
```

Result:

```text
git status --short --untracked-files=all: completed; only Phase 9G-7A documentation files are modified/untracked
git diff --check: passed with LF-to-CRLF warning for TASK_PROGRESS.md only
```

## Known Issues / Blockers

No blockers.

Phase 9G-7B must remain fake-sequence-only unless explicitly authorized.

## Do Not Do

Do not modify Python source files for Phase 9G-7A.

Do not run training, short training smoke, playback, or comparison-method evaluation.

Do not commit unless explicitly asked.

Do not implement action latching, Contract C behavior, effective assignment resolution, ownership enforcement, applied arbitration, mask changes, observation changes, reward changes, controller/env changes, HARL changes, baseline behavior changes, scenario YAML changes, cooldown tuning, redirect tuning, or failed-pair memory tuning without a separate explicit phase.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_DESIGN_20260708.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6E_COMMIT_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6D_PASSIVE_LIFECYCLE_BOUNDED_RUNTIME_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md
```
