# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-6C passive lifecycle runtime diagnostics integration is complete.

Phase 9G-6C attached the passive/shared lifecycle transition logger to:

```text
RL playback diagnostics path
generic comparison-method evaluation path
```

The integration is behind default-off diagnostics flags:

```text
--log_assignment_lifecycle
--assignment_lifecycle_output_dir
```

The same shared adapter and standardized `assignment_proposal [E, M]` interface are used by current RL, random/nearest/greedy paths, and future SOTA method paths.

No runtime simulation was run. No formal playback was run. No comparison-method evaluation episode was run. No training was run. No commit was made.

## Latest Completed Phase

Phase 9G-6C: passive lifecycle runtime integration, diagnostics only.

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_20260707.md
```

Updated:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Runtime Integration Boundary

The lifecycle diagnostics adapter consumes only standardized decoded proposals:

```text
assignment_proposal [num_envs, num_robots]
0..N-1 = target id
-1 = decoded noop / no proposed target
```

The adapter does not consume raw HARL action ids and rejects raw discrete noop id `N`. Method-specific outputs must be decoded by their own adapter before lifecycle diagnostics:

```text
method-specific output -> method adapter / decoder -> assignment_proposal [E, M] -> shared lifecycle diagnostics adapter
```

The adapter writes, only when enabled:

```text
assignment_lifecycle_events.jsonl
assignment_lifecycle_summary.json
```

Every event and summary records:

```text
behavior_changed = false
```

## Behavior Preservation

No assignment behavior changed.

No actions, masks, observations, rewards, controller commands, env dynamics, HARL behavior, solver behavior, scenario YAML, cooldown behavior, redirect guardrail behavior, or failed-pair memory behavior changed.

The adapter does not:

```text
modify proposals
produce effective assignments
latch active targets
enforce ownership
apply hypothetical arbitration
modify available_actions or available_mask
invoke controller or env functions in smoke tests
```

## Integration Smoke Results

New smoke test:

```text
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

Passed coverage:

```text
disabled identity
pre/post step ordering
completion before done-env reset
subset reset for E=3
decoded RL noop -1 accepted
raw discrete noop id N rejected before adapter entry
random/nearest/greedy/future method metadata equivalence
unified event and summary schemas
event draining
idempotent finalize
input non-mutation
exact conflict remains passive
output JSONL/JSON parsing
arbitrary method name new_sota_method_v1
variable M/N: (E=1,M=1,N=3), (E=2,M=3,N=5), (E=2,M=4,N=8)
```

Existing Phase 9G-6B logger smoke also still passed.

## Latest Verification

Commands run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
git diff --check
git status --short --untracked-files=all
```

Result:

```text
py_compile assignment_lifecycle.py: passed
py_compile assignment_lifecycle_diagnostics.py: passed
py_compile test_assignment_lifecycle_transition_logger_smoke.py: passed
py_compile test_assignment_lifecycle_runtime_integration_smoke.py: passed
py_compile evaluate_assignment_rl_playback_diagnostics.py: passed
py_compile evaluate_assignment_methods.py: passed
test_assignment_lifecycle_transition_logger_smoke.py: passed
test_assignment_lifecycle_runtime_integration_smoke.py: passed
git diff --check: passed
git status --short --untracked-files=all: completed
```

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run formal playback or comparison-method evaluation unless explicitly authorized.

Do not treat the passive logger as env-owned lifecycle truth.

Do not implement action latching, Contract C behavior, effective assignment resolution, ownership enforcement, mask changes, observation changes, reward changes, controller/env changes, HARL changes, baseline behavior changes, scenario YAML changes, cooldown tuning, redirect tuning, or failed-pair memory tuning without a separate explicit phase.

## Next Step

Recommended Phase 9G-6D:

```text
bounded runtime validation of passive lifecycle diagnostics
```

Recommended boundary:

```text
one RL playback diagnostic run with lifecycle logging enabled
one or more current comparison-method diagnostic runs with lifecycle logging enabled
verify lifecycle event and summary files are populated
compare RL/baseline/future-method-compatible schemas
confirm diagnostics remain behavior-neutral
no training
no action latching
no ownership enforcement
no mask, observation, reward, controller, env, HARL, solver, or scenario changes
```

After Phase 9G-6D passes, perform a Phase 9G-6 commit-readiness review covering 9G-6A through 9G-6D before the user manually commits the complete block.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_20260707.md
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
