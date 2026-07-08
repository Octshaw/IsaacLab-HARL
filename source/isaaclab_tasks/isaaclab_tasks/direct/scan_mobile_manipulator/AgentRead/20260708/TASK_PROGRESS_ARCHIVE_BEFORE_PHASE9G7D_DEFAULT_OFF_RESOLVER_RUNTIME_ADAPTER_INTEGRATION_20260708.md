# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-7C default-off resolver runtime integration design/readiness audit is complete.

Phase 9G-7C was documentation/design only.

No Python source files were modified.

No runtime integration occurred.

No playback, comparison-method evaluation, training, or short training smoke ran.

No commit was made.

## Current Worktree Context

Phase 9G-7A and 9G-7B outputs remain uncommitted in the worktree, as expected.

Phase 9G-7B implemented:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
```

Phase 9G-7B passed disabled identity, Contract C, ownership, exact-conflict arbitration, completion release, budget release, failed-pair reclaim rejection, teammate reclaim, active-target infeasibility deferred behavior, variable E/M/N, method-agnostic behavior, and input non-mutation in fake-sequence smoke tests.

## Files Created In Phase 9G-7C

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7C_RESOLVER_RUNTIME_INTEGRATION_DESIGN_20260708.md
```

## Files Updated

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Selected Runtime Architecture

Selected architecture:

```text
one shared resolver runtime adapter used by AssignmentHARLWrapper and comparison-method paths
```

Recommended future module:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
```

The adapter should own resolver construction, default-off configuration, pre-step proposal resolution, post-step lifecycle observation, event draining, reset coordination, and optional resolver output serialization.

The adapter must not own policy inference, solver decisions, controller behavior, env physics, task completion truth, reward formulas, masks, or observations.

## Selected RL Integration Point

Resolver behavior must be inserted inside `AssignmentHarlWrapper.step()` through the shared adapter, not only in playback scripts.

Selected RL order:

```text
raw policy action
  -> decode_actions()
  -> assignment_proposal [E, M]
  -> resolver adapter resolve_pre_step()
  -> effective_assignment [E, M]
  -> assignment_to_env_actions(effective_assignment)
  -> env.step()
  -> wrapper diagnostics/reward using effective_assignment for executed-action semantics
  -> resolver adapter observe_post_step()
  -> done-env resolver reset after final post-step events
```

Reason:

```text
future training reuse requires the wrapper path;
script-only playback integration would create semantic drift.
```

## Selected Comparison-Method Integration Point

Comparison methods should call the same shared adapter after solver output and before controller conversion:

```text
solver/method output
  -> assignment_proposal [E, M]
  -> resolver adapter resolve_pre_step()
  -> effective_assignment [E, M]
  -> viewpoint_assignment_to_actions(effective_assignment)
  -> env.step()
  -> resolver adapter observe_post_step()
```

Each method gets a fresh resolver instance, fresh state, and method-specific output directory.

Do not hardcode a random/nearest/greedy whitelist. Future SOTA adapters must enter through the same standardized proposal boundary.

## Selected Pre/Post-Step Ordering

For each decision row:

```text
pre_problem_t
assignment_proposal_t
resolver.resolve_pre_step()
effective_assignment_t
controller conversion from effective_assignment_t
env.step()
post_problem_t with pre-reset coverage preserved
existing diagnostics using effective_assignment_t where they describe executed behavior
budget_failure_pairs built from effective_assignment_t
resolver.observe_post_step()
resolver event drain / output
done-env resolver reset
runtime buffer reset
```

This ordering is intended to prevent off-by-one release, completion-after-reset loss, proposal/effective mismatch, and wrong episode ids.

## Selected Budget Handoff

Current wrapper budget triggers are computed after `env.step()` through cooldown diagnostics.

When resolver is enabled:

```text
budget failure must release the currently active effective robot-target pair
not the raw proposal pair
```

Future handoff:

```text
for each env/robot with budget_last_triggered_by_budget=True,
target_id = effective_assignment[env, robot]
external_diagnostics["budget_failure_pairs"] receives env_id, robot_id, target_id, reason="budget_trigger"
```

Failed-pair-memory trigger target ids are secondary metadata only unless they match the effective pair.

## Selected Proposal / Effective Logging Schema

Resolver runtime diagnostics should distinguish:

```text
assignment_proposal
effective_assignment
proposal_effective_changed
proposal_accepted
proposal_rejected_reason
continued_from_active_target
new_claim_started
switch_requested
switch_rejected
claim_conflict
claim_winner
claim_loser
active_target_before
active_target_after
task_owner_before
task_owner_after
resolver_events
behavior_changed
```

Do not silently replace existing assignment-history assignment fields with effective assignments.

Recommended resolver output files:

```text
assignment_lifecycle_resolver_events.jsonl
assignment_lifecycle_resolver_summary.json
assignment_lifecycle_resolver_rows.csv   # optional
```

Passive proxy diagnostics should remain in their existing separate files.

## Selected Resolver / Passive Logger Coexistence

Selected principle:

```text
resolver is behavior source of truth when enabled
passive logger remains proxy-only
```

Coexistence:

```text
resolver off + passive off: original behavior
resolver off + passive on: Phase 9G-6 passive proposal diagnostics
resolver on + passive on: resolver drives behavior; passive logger may observe effective_assignment only as proxy diagnostics
resolver on + passive off: supported but not recommended for first enabled validation
```

Resolver behavior summaries must not be summed with passive proxy summaries.

## Selected Config / CLI Boundary

Recommended code-default config fields:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_resolver_strict_proposals = True
assignment_lifecycle_resolver_log_diagnostics = False
```

Recommended CLI flags:

```text
--assignment_lifecycle_resolver_enabled
--log_assignment_lifecycle_resolver
--assignment_lifecycle_resolver_output_dir
```

Phase 9G-7D should not require scenario YAML edits.

Default-off invariant:

```text
resolver disabled by default
proposal passes through unchanged
no resolver behavior state accumulates
no resolver output files unless logging is enabled
existing checkpoints remain behavior-identical
random/nearest/greedy remain behavior-identical
```

## Selected Disabled Identity Plan

Future disabled validation should compare:

```text
old path / resolver absent
resolver adapter present but disabled
```

For RL and one deterministic baseline, compare:

```text
assignment_history.csv
per_episode.csv
summary.csv
coverage ratio
coverage AUC
episode length
budget trigger count
controller input assignments
decoded assignment proposal sequence
```

Preferred criterion:

```text
exact SHA equality for deterministic artifacts
```

Resolver-specific disabled checks:

```text
proposal == effective_assignment
resolver snapshot remains default/empty
resolver event count = 0
behavior_changed = false
```

## Selected Enabled Runtime Invariant Plan

Enabled resolver behavior is expected to differ from old trajectories.

Do not require identity.

Required invariants:

```text
controller receives effective_assignment
proposal tensor remains unchanged
every proposal/effective difference has an explaining resolver event
one robot has at most one active target
one task has at most one owner
noop while executing continues active target
switch requests do not change effective target
completion clears owner and active target
budget failure releases owner and active target
done reset clears selected env state after final events
raw proposal and effective assignment are both logged
```

No performance claim should be made from the first enabled runtime.

## Selected Infeasibility And Stranded-Task Monitoring

Active-target infeasibility:

```text
log only
do not auto-release in first runtime integration
track active_target_infeasible_step_count
track active_target_infeasible_streak
track active_target_infeasible_without_motion_count
```

Stranded failed-pair tasks:

```text
detect and log only
do not clear failed pair automatically
do not add TTL expiry
track streak/duration before treating as meaningful
```

Candidate stranded condition:

```text
task uncovered
task unowned
failed/released pair exists for the task
all non-failed robot-target pairs are infeasible/unavailable
all feasible robots are blocked by resolver failed-pair state
```

## Selected Guardrail Interaction

For first resolver-enabled runtime validation:

```text
cooldown budget diagnostics may remain as the budget failure source
legacy failed-pair memory should remain disabled
redirect guardrail should remain disabled unless explicitly testing interaction
resolver owns final failed-pair behavior when enabled
do not tune cooldown, redirect, or failed-pair memory
```

Do not enable two competing behavior mechanisms for failed-pair semantics.

## Observation / Training Gate

No training with resolver enabled.

The policy still cannot observe:

```text
active target
idle/executing state
task ownership
failed/released pair state
attempt age
release/failure reason
```

No resolver-enabled training until lifecycle behavior-driving state is represented in actor/critic observations as needed.

## Recommended Next Phase

Recommended next phase:

```text
Phase 9G-7D:
default-off shared resolver runtime adapter and integration smoke
```

Likely scope:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
minimal default-off wiring hooks in AssignmentHARLWrapper
minimal default-off wiring hooks in evaluate_assignment_methods.py
report and TASK_PROGRESS update
```

Phase 9G-7D should not run playback, evaluation, training, or short training smoke.

Later sequence:

```text
Phase 9G-7E:
bounded disabled identity and enabled runtime diagnostics

Phase 9G-7F:
commit-readiness review
```

## Validation

Documentation-only validation:

```powershell
git status --short --untracked-files=all
git diff --check
```

Result:

```text
git status --short --untracked-files=all: completed; expected uncommitted Phase 9G-7A/7B/7C docs plus 7B resolver/test files are present
git diff --check: passed with LF-to-CRLF warning for TASK_PROGRESS.md only
```

## Do Not Do

Do not run playback, comparison-method evaluation, training, or short training smoke.

Do not integrate the resolver into runtime paths before the explicitly authorized Phase 9G-7D.

Do not change observations, masks, rewards, action semantics, controller behavior, env dynamics, HARL, solvers, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior without a separate explicit phase.

Do not commit unless explicitly asked.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7C_RESOLVER_RUNTIME_INTEGRATION_DESIGN_20260708.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_20260708.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_DESIGN_20260708.md
```
