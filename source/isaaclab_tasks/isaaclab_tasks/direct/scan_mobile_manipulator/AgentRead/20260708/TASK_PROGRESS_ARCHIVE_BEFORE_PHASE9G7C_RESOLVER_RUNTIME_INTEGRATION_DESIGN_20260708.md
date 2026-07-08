# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-7B shared effective-assignment resolver prototype is complete.

The user manually committed the complete Phase 9G-6 block before Phase 9G-7A. Phase 9G-6 is closed.

Phase 9G-7A completed the documentation/design audit for a future shared resolver, active-target latch, and Contract C execution semantics.

Phase 9G-7B implemented a pure shared resolver prototype with fake-sequence smoke tests only.

No runtime integration occurred. No playback, comparison-method evaluation, training, or short training smoke ran. No commit was made.

## Files Created In Phase 9G-7B

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_20260708.md
```

## Files Updated

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Existing untracked Phase 9G-7A documentation remains part of the current worktree:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_DESIGN_20260708.md
```

## Resolver Boundary

`AssignmentLifecycleResolver` is a standalone shared prototype.

It is method-agnostic and accepts decoded proposals:

```text
assignment_proposal [E, M]
0..N-1 = target id
-1 = noop / no new target proposal
```

It does not know about raw HARL noop id `N`.

It was not integrated into:

```text
assignment_harl_wrapper.py
assignment_controller.py
scan_mobile_manipulator_env.py
evaluate_assignment_rl_playback_diagnostics.py
evaluate_assignment_methods.py
```

No assignment wrapper, controller, environment, observation, mask, reward, HARL, solver, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior changed.

## Disabled-Mode Result

Disabled mode is absolute pass-through.

When `enabled=False`, the resolver:

```text
returns effective_assignment == assignment_proposal
does not interpret noop
does not arbitrate conflicts
does not reject switches
does not update active targets
does not update task owners
does not update pair state
does not accumulate attempt age
emits no events
returns behavior_changed = False
```

Smoke result: passed. The disabled full snapshot was identical before and after pre/post calls, including proposals outside enabled strict range.

## Enabled Contract C Result

Implemented enabled rules:

```text
idle + target -> start assignment
idle + noop -> remain idle
executing + same target -> continue active target
executing + noop -> continue active target
executing + different target -> reject switch and continue current active target
```

Smoke result: passed.

## Ownership And Arbitration Result

Implemented first-prototype invariants:

```text
at most one active target per robot
at most one owner per task
existing active owner has priority
lowest finite path cost wins simultaneous new claims on an unowned open target
lower robot id breaks exact cost ties
lower robot id fallback is used when costs are unavailable or non-finite
losers remain idle with effective noop
```

Smoke result: passed, including proposal non-mutation.

## Completion And Budget Release Result

Completion:

```text
detected only from newly covered viewpoints_covered
clears active target, owner, and attempt metadata
sets robot idle
marks pair state completed
clears failed/released pair states for that target by completion
```

Budget failure/release:

```text
uses only supplied external diagnostics
emits budget_failure and release_budget_failure
clears matching active target and owner
sets robot idle
records last failure/release reason
sets pair state RELEASED_BUDGET
leaves uncovered target open for teammates
```

Smoke result: passed.

## Failed-Pair Persistence And Limitation

The first prototype uses episode-persistent same-robot failed-pair rejection:

```text
budget-failed robot-target pair remains rejected until target completion or env reset
```

Smoke result: passed.

Known limitation: this can strand a task when only the failed robot can complete it. This is intentionally documented as a prototype limitation, not a final retry policy.

## Active-Target Infeasibility

If an already executing active target becomes infeasible in a later pre-step problem:

```text
effective_assignment remains the active target
owner remains
active target remains latched
active_target_infeasible_deferred event is emitted
```

Smoke result: passed. Runtime handling is deferred to a later phase.

## Variable E/M/N And Method-Agnostic Result

Variable shape smoke passed for:

```text
E=1, M=1, N=3
E=2, M=3, N=5
E=2, M=4, N=8
```

Method metadata smoke passed for:

```text
happo
random
nearest
greedy
future_sota_placeholder
```

State transitions and effective assignments were identical across method labels, excluding metadata.

## Input Non-Mutation Result

Smoke test verified no mutation of:

```text
AssignmentProblem-like problem tensors
assignment proposal
cost matrix
available/feasible masks
coverage tensor
external diagnostics
done env ids
method metadata
```

## Validation

Commands run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_resolver_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_smoke.py --json
```

Results:

```text
py_compile assignment_lifecycle_resolver.py: passed
py_compile test_assignment_lifecycle_resolver_smoke.py: passed
resolver smoke: passed, 20 grouped cases covering the required fake-sequence matrix
```

Final checks:

```text
git diff --check: passed
git status --short --untracked-files=all: completed; expected 9G-7A/9G-7B docs and new resolver/test files are present
```

## Known Issues / Blockers

No current blockers for the standalone fake-sequence prototype.

Known design limitations before runtime integration:

```text
episode-persistent failed-pair rejection can strand a task
active-target infeasibility release is deferred
no lifecycle-aware available_actions
no lifecycle-aware observations
no training-ready Markov state
no playback/evaluation identity evidence for enabled resolver behavior
```

## Recommended Next Phase

Recommended next phase:

```text
Phase 9G-7C:
default-off resolver runtime integration design/readiness audit
```

Do not automatically integrate the resolver.

The next audit should decide:

```text
how wrapper and comparison paths share one resolver adapter
where post-step budget diagnostics enter
how resolver and passive logger coexist
how enabled/disabled identity will be validated
how active-target infeasibility is handled
how stranded failed-pair tasks are detected
whether observation changes remain deferred
```

Training remains prohibited until lifecycle behavior-driving state is represented in observations.

## Do Not Do

Do not run training, short training smoke, playback, or comparison-method evaluation.

Do not integrate the resolver into runtime paths without a separate authorized phase.

Do not change assignment wrappers, controller behavior, env behavior, observations, masks, rewards, HARL, solvers, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior without a separate explicit phase.

Do not commit unless explicitly asked.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_20260708.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_DESIGN_20260708.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6E_COMMIT_READINESS_REVIEW.md
```
