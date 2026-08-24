# TASK_PROGRESS

## Current status

```text
classification:
  PHASE-B0-2DR-TARGETED-SEMANTIC-REVISION-COMPLETE-AWAITING-GPT-REVIEW

latest authorization:
  B0-2D-R TARGETED DESIGN REVISION ONLY

Phase A:
  complete at the accepted pure/static/manifest evidence level
  final review passed
  committed by user

Phase B0 design:
  PHASE-B0-DESIGN-CONDITIONAL-PASS

B0-1A:
  review passed
  pure/default-off ExecutionTransitionFacts producer foundation complete
  dedicated evidence 9/9

B0-1B:
  review passed
  pure/default-off retained generation-clock foundation complete
  dedicated evidence 12/12

B0-2D:
  conditional review completed
  PHASE-B0-2D-DESIGN-CONDITIONAL-PASS

B0-2D-R:
  targeted revision complete
  awaiting GPT/user review

C1 active-owner permanent-failed invariant:
  frozen

C2 success-tail reader/publication atomicity:
  frozen

Phase-A contract revision:
  none

B0 contract/runtime gap:
  none

B0-2 implementation:
  not entered
  not authorized

B0-3+ and Phase B/C/D/E:
  not entered
  not authorized

event-profile runtime readiness:
  interface_only / Phase-A blocked

Python/test/runtime changes in B0-2D-R:
  none

Isaac/AppLauncher/training/playback/evaluation:
  not run

commit:
  none
```

## Latest completed phase

B0-2D-R closes only the two conditions from the B0-2D conditional review.

### C1 — active owner versus cumulative permanent failure

For every active task `j` owned by robot `i`:

```text
task0[j] in {CLAIMED, NAVIGATING, ALIGNING}
AND owner0[j] == i
=> failed0[i,j] MUST be false
```

A violation rejects the complete selected batch during Stage-1 prestate
validation, before candidate derivation, ledger consume, result finalization,
state mutation, generation commit, event/handoff construction, or publication.
There is no release, repair, failure-bit clearing, reassignment, event, or
continuation.

This pair-local invariant is independent of the all-robot TEAM_INFEASIBLE
equation. Future Phase-B assignment validation must prevent creation of an
active known-failed pair; B0 lifecycle prevalidation independently detects it
if it nevertheless exists.

The revision narrowly supersedes B0-2D's repeated-F wording. All 32 matrix rows
remain unchanged, but “valid active owned pair” now includes `failed0=false`;
therefore every valid owner-gated `F=1` row is newly recorded.

### C2 — success-tail publication atomicity

The StateStore-swap-before-clock-commit order remains unchanged. One
coordinator publication/transaction lock excludes every external current-state
reader across final revalidation, StateStore internal swap, clock commit,
authoritative-success marking, and immutable handoff/current-view publication.

External readers receive state and committed transition generation together
through the coordinator read/publication boundary. They cannot hold or invoke
raw StateStore or clock snapshot capabilities. Internal transaction-private
reads are allowed, but no artifact may escape before publication succeeds.

Every observable current view is either old-state/old-generation or
new-state/new-generation. If StateStore swap succeeds and clock commit
unexpectedly fails, nothing is published, the coordinator becomes
fatal/poisoned, every fresh read fails closed, and there is no rollback,
cancellation, second consume, silent retry, or normal continuation.

## Active architecture / implementation path

```text
physical environment
  -> future CoordinatorPreResetPort invocation only

EnvironmentExecutionFactsProducer
  -> constructs canonical ExecutionTransitionFacts only

LifecycleAuthorityRuntime / LIFECYCLE_AUTHORITY_V1
  -> future sole lifecycle semantic derivation authority

LifecycleStateStore
  -> future sole lifecycle-state storage writer boundary

LifecycleGenerationClock
  -> retained B0-1B sole generation writer for one opaque env domain

Coordinator
  -> future transaction/order/publication owner
  -> not a second semantic authority

future Phase-B resolver
  -> typed staged post-a0 assignment request only
  -> never a lifecycle authority or direct state writer
```

Implemented today is only the dormant, default-off producer and generation
clock foundation. There is no StateStore, lifecycle authority, ledger/result
runtime, coordinator lock, environment hook, handoff, sidecar, reader wiring,
scheduler, or event-profile production entrypoint.

## Key files

Current targeted revision:

- `AgentRead/20260814/PHASE_B0_2DR_TARGETED_LIFECYCLE_AUTHORITY_SEMANTIC_REVISION.md`
- `AgentRead/20260814/PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md`
- `AgentRead/TASK_PROGRESS.md`

Preserved pure/default-off foundations:

- `assignment_lifecycle_authority_runtime.py`
- `scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py`
- `scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py`

Frozen authorities, unchanged:

- `assignment_lifecycle_transition_contract.py`
- `assignment_event_contract.py`
- `assignment_profile_contract.py`

## Repository and changed-file scope

```text
HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

HEAD subject:
  feat(assignment): complete lifecycle-aware MRTA Phase A interface contracts

branch:
  main

index at B0-2D-R preflight:
  empty

preflight worktree:
  preserved uncommitted B0 design/B0-1A/B0-1B/B0-2D cohort

B0-2D-R documentation delta:
  new targeted revision report
  archived previous 598-line TASK_PROGRESS
  rewrote top-level TASK_PROGRESS as concise current handoff

code/test/runtime/frozen/HARL/config/checkpoint delta in B0-2D-R:
  none
```

## Latest verification

B0-2D-R uses documentation/scope verification only:

```text
git status:
  expected B0-2D-R docs plus preserved preflight B0 cohort only

git diff --check:
  passed

trailing whitespace:
  passed for report/progress/archive

Markdown fences:
  balanced: report 48 / progress 14 / archive 16 markers

classification/path consistency:
  passed; exact classification once in report and current handoff

pre-existing Python/test/runtime hashes:
  passed; 7/7 captured paths byte-identical to preflight
```

No Python command or implementation test is authorized or run in B0-2D-R.
Earlier reviewed baselines are preserved, not rerun:

```text
B0-1A producer suite:
  9/9 passed

B0-1B generation-clock suite:
  12/12 passed

Phase-A lifecycle-transition contract regression:
  12/12 passed

Phase-A profile contract regression:
  16/16 passed

focused Phase-A default-off identity regression:
  16/16 passed
```

## Known issues / unfinished work

- B0-2 implementation remains absent and unauthorized.
- Real pre-reset owner-gated completion/failure/health reporters remain absent.
- StateStore, authority, ledger/result, publication lock, immutable reader view,
  terminal sidecar, and environment integration remain unimplemented.
- Event runtime readiness remains fail-closed.
- `CLAIMED -> NAVIGATING -> ALIGNING` progression remains not implemented/not
  claimed because frozen facts have no progress edges.
- Isaac runtime identity, HARL transport, training, playback, evaluation,
  checkpoint-ready V3, and weight use remain deferred.
- No performance or method-readiness claim is made.

All eleven method numeric TBDs remain unresolved:

```text
top_k_tasks_per_robot
local_robot_cap
local_task_cap
pair_abs_threshold
pair_rel_threshold
component_abs_threshold
component_rel_threshold
transfer_penalty
rejection_penalty_scale
alignment_time_constant
assignment_retry_cadence
```

## Do not do

Without new explicit authorization:

- do not implement B0-2 or begin B0-3+;
- do not add/wire the environment hook, StateStore, lifecycle authority,
  ledger/result, coordinator publication lock, sidecar, reader port, scheduler,
  resolver, or event runtime;
- do not modify frozen contracts, environment, wrapper, controller, resolver,
  HARL, YAML/config, checkpoint behavior, or installed packages;
- do not weaken the event-profile readiness barrier;
- do not choose any of the eleven numeric TBD values;
- do not run Isaac, AppLauncher, training, playback, evaluation, checkpoint
  tensor I/O, or commit.

## Next step

Send the B0-2D-R targeted revision to GPT/user review. Do not infer B0-2
implementation readiness or authorization from the completed design revision.

## Detailed reports / archives

- `AgentRead/20260814/PHASE_B0_2DR_TARGETED_LIFECYCLE_AUTHORITY_SEMANTIC_REVISION.md`
- `AgentRead/20260814/PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md`
- `AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_2DR_TARGETED_SEMANTIC_REVISION_20260814.md`
- `AgentRead/20260809/PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md`
- `AgentRead/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md`
- `AgentRead/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md`

The archive preserves the full prior handoff before the AGENTS-compliant
condensation. The top-level file is now the concise current handoff.
