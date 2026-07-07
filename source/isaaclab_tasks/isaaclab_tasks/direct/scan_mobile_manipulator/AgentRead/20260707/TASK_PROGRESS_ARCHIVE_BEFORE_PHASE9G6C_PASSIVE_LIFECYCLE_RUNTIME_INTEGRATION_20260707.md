# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-6B passive/shared lifecycle transition logger is complete.

Phase 9G-6B implemented a standalone method-agnostic logger and pure fake-sequence smoke test. The logger maintains proxy state only. It does not change assignments, masks, observations, rewards, controller commands, env dynamics, action ids, action semantics, HARL behavior, baseline decisions, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior.

No training was run. No playback was run. No evaluation or simulation rollout was run. No commit was made.

## Latest Completed Phase

Phase 9G-6B: passive shared lifecycle transition logger.

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_20260707.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Logger Boundary

The standardized proposal interface is:

```text
assignment_proposal [num_envs, num_robots]
0..N-1 = proposed target id
-1 = decoded noop / no proposed target
```

The logger is method-agnostic and is not tied to HARL actions, RL wrapper internals, or current random/nearest/greedy solvers. Future adapters can convert method-specific outputs into the standardized proposal:

```text
method-specific output -> method adapter -> assignment_proposal [E, M] -> passive lifecycle logger
```

Method metadata such as `method_name`, `proposal_type`, scores, costs, confidence, or external plan id is optional and does not affect transition reconstruction.

## Proxy State And Events

Proxy tensors:

```text
robot_state_proxy [E, M]
active_target_proxy [E, M]
task_owner_proxy [E, N]
task_state_proxy [E, N]
pair_state_proxy [E, M, N]
attempt_start_step_proxy [E, M]
attempt_age_proxy [E, M]
last_proposal [E, M]
```

Implemented events:

```text
attempt_started_proxy
attempt_continued_proxy
noop_idle_proxy
noop_after_active_ambiguous
target_completed_proxy
target_completed_by_teammate_proxy
active_target_became_covered_proxy
budget_failure_proxy
release_proxy
switch_request_proxy
exact_claim_conflict_proxy
reset_proxy
unavailable_target_proposal_proxy
invalid_assignment_proposal_proxy, only when strict_proposals=False
```

Exact same-target conflict diagnostics use hypothetical lowest path cost winner with robot-id tie-breaker. The logger reports the hypothetical winner/losers but does not change the proposal, masks, ownership behavior, or controller input.

## Latest Verification

Commands run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
git diff --check
git status --short --untracked-files=all
```

Result:

```text
py_compile assignment_lifecycle.py: passed
py_compile test_assignment_lifecycle_transition_logger_smoke.py: passed
test_assignment_lifecycle_transition_logger_smoke.py: passed
git diff --check: passed with LF-to-CRLF warning for TASK_PROGRESS.md only
git status --short --untracked-files=all: completed; shows Phase 9G-6A docs still untracked plus new Phase 9G-6B files
```

Smoke coverage passed for:

```text
normal attempt
noop idle
noop after active ambiguity
switch request
budget failure and release proxy
exact target conflict with lowest-cost winner
equal-cost robot-id tie-break
cost-unavailable robot-id fallback
teammate completion when completing robot id is supplied
subset and full reset
method-agnostic equivalence for happo, random, nearest, greedy, future_sota_placeholder
variable M/N: (M=1,N=3), (M=3,N=5), (M=4,N=8)
covered target diagnostic
invalid proposal validation
input non-mutation
```

## Active Architecture / Implementation Path

Current path:

```text
passive shared lifecycle transition logger
method-agnostic proposal interface
proxy state only
fake-sequence validated
no runtime integration yet
```

This is distinct from Phase 9G-1:

```text
Phase 9G-1 was offline CSV lifecycle reconstruction.
Phase 9G-6B is online passive reconstruction from pre/post problem snapshots and current standardized proposals.
```

## Known Issues / Blockers

The logger is not yet attached to RL playback diagnostics or current method-comparison evaluation. It has only been validated through fake sequences.

The logger does not implement Contract C, action latching, lifecycle ownership enforcement, mask generation, or effective assignment resolution.

Training-ready lifecycle behavior would still require observation migration and an explicit behavior phase.

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not treat the passive logger as env-owned lifecycle truth.

Do not implement action latching, Contract C behavior, effective assignment resolution, ownership enforcement, mask changes, observation changes, reward changes, controller/env changes, HARL changes, baseline behavior changes, scenario YAML changes, cooldown tuning, redirect tuning, or failed-pair memory tuning without a separate explicit phase.

## Next Step

Recommended Phase 9G-6C:

```text
Attach the passive lifecycle logger to RL playback diagnostics and current comparison-method evaluation as diagnostics only.
No behavior change.
No action latching.
No mask changes.
No observation changes.
No reward changes.
No controller/env changes.
No training.
Playback only if explicitly authorized.
```

Alternative Phase 9G-6C:

```text
Expand the generic assignment proposal adapter contract without runtime integration.
```

Do not automatically implement action latching or Contract C.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_20260707.md
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
