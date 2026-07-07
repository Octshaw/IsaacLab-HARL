# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-6A active-task / release lifecycle transition interface audit is complete.

Phase 9G-6A was documentation/design only. No code behavior changed. No Python source files were modified. No training was run. No playback was run. No evaluation or simulation rollout was run. No commit was made.

No reward formula/scale, actor/shared observation, `available_actions` shape or contents, assignment action id semantics, env dynamics, controller behavior, HARL code, baseline solver, scenario YAML, installed package, cooldown tuning, redirect guardrail tuning, failed-pair memory tuning, wrapper behavior, or env behavior was changed.

## Latest Completed Phase

Phase 9G-6A: explicit active-task / release lifecycle transition and interface contract audit.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md
```

Archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT_20260707.md
```

## Key Findings

Current cadence:

```text
The policy or baseline currently produces one target/noop assignment for every robot on every env step.
Robot motion depends on the current step assignment.
The env/controller does not retain an active target internally.
Selecting noop after a target produces no target-directed command for that step.
_previous_assignment is policy context/diagnostic/masking state, not execution-control state.
```

Selected future contract direction:

```text
Use a shape-preserving Contract C for a future prototype:
  target action starts or switches an assignment when allowed
  noop while idle means remain idle / no assignment
  noop while executing means continue current active target
  release is not overloaded onto noop in the first lifecycle design
```

This contract changes action semantics when enabled even though `available_actions` can remain `[M, N+1]`. Observation migration is required before training with it.

Selected source-of-truth direction:

```text
Completion and physical state remain env-owned.
Lifecycle state should start as a shared passive lifecycle transition logger used by RL and baseline paths.
If lifecycle behavior becomes core environment semantics, promote the source of truth toward env/shared ownership later.
The controller should consume effective assignments, not own lifecycle.
```

Selected same-step arbitration direction:

```text
For future exact same-target claims, use a centralized deterministic lowest-path-cost winner with robot-id tie-breaker.
Do not claim lifecycle ownership solves nearby target conflict, path overlap, or near-miss behavior.
```

Current failed-pair memory relationship:

```text
Keep failed-pair memory disabled-by-default as diagnostic/experimental guardrail code.
Do not continue TTL-only memory as the main solution path.
If promoted later, fold it into lifecycle-owned pair_failed/released state or keep it diagnostic-only.
Do not create two competing pair-failure sources of truth.
```

## Recommended Next Smallest Phase

Recommended Phase 9G-6B:

```text
Passive/shared lifecycle transition logger.
No behavior change.
No action latching.
No mask changes.
No observation changes.
No reward changes.
No controller/env changes.
No training.
No playback unless explicitly authorized later.
```

Likely Phase 9G-6B files:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/PHASE9G6B_*.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Phase 9G-6B should log only passive proxy transitions first:

```text
idle selects open target
executing repeats/continues target
noop while idle
noop while previously active under current target-every-step behavior
target covered
target covered by teammate
budget failure proxy
release proxy
switch-target request
reset
same-step exact target conflict diagnostics
```

Observation changes, lifecycle action semantics, and training remain deferred.

## Latest Verification

Allowed validation for Phase 9G-6A:

```text
git status --short --untracked-files=all
git diff --check
```

No Python validation is required because Phase 9G-6A modified documentation only and did not modify Python source files.

## Known Issues / Blockers

TTL-only failed-pair memory can delay same-owner reacquisition but has not reduced total same-owner returns or improved coverage.

A true lifecycle will likely change action semantics even if `available_actions` shape remains `[M, N+1]`. Training-ready lifecycle work must expose robot state, active target, ownership, attempt age, and failure/release state in observations.

Wrapper-only lifecycle behavior would weaken baseline comparability. The next implementation should use a shared passive logger or shared manager interface before any RL-only behavior prototype.

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not implement active-task lifecycle, ownership tables, action latching, noop behavior changes, reward changes, observation changes, available-action changes, action semantics changes, env dynamics changes, controller changes, HARL changes, baseline changes, scenario YAML changes, cooldown tuning, redirect guardrail tuning, or failed-pair memory tuning without a separate explicit phase.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT_20260707.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
