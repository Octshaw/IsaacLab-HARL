# Phase B0-2 Pure Lifecycle Authority Transaction Implementation Report

## 1. Classification

```text
classification:
  PHASE-B0-2-PURE-LIFECYCLE-AUTHORITY-TRANSACTION-COMPLETE-AWAITING-GPT-REVIEW

B0-1A:
  review passed
  pure ExecutionTransitionFacts producer complete

B0-1B:
  review passed
  pure retained generation clock complete

B0-2D / B0-2D-R:
  semantic conditions closed

B0-2:
  complete at pure/default-off transaction-foundation level

LifecycleStateStore:
  implemented

LifecycleAuthorityRuntime:
  implemented

TransitionConsumeLedger integration:
  implemented using the frozen authority

LifecycleTransitionResult finalization:
  implemented using the frozen factory

generation success commit:
  implemented

coordinator transaction/publication boundary:
  implemented

C1 active-owner failed-pair invariant:
  implemented and tested

C2 publication/read atomicity:
  implemented and tested

environment pre-reset integration:
  not implemented

real execution reporters:
  not implemented

mailbox / terminal sidecar:
  not implemented

event-profile production readiness:
  still blocked

B0-3+ and Phase B/C/D/E:
  not entered
  not authorized

Isaac/AppLauncher/training/playback/evaluation:
  not run

commit:
  none
```

B0-2 required no frozen semantic-schema revision and no scope expansion into
the environment, wrapper, resolver, controller, HARL, or installed packages.
It stops at a dormant pure transaction foundation for GPT/user review.

## 2. Repository baseline and ending state

```text
starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch:
  main

HEAD subject:
  feat(assignment): complete lifecycle-aware MRTA Phase A interface contracts

index at B0-2 preflight and documentation closeout:
  empty

worktree:
  preserved uncommitted B0 design/B0-1A/B0-1B/B0-2D/B0-2D-R cohort
  plus the authorized uncommitted B0-2 runtime, test, and documentation cohort

commit made by B0-2:
  none
```

The existing worktree was preserved. No reset, checkout, cleanup, staging, or
commit operation was used.

## 3. Changed and new files

New pure/default-off production foundation:

- `assignment_lifecycle_transaction_runtime.py`

New standalone pure regression:

- `scripts/environments/test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py`

New implementation report:

- `AgentRead/202608/20260814/PHASE_B0_2_PURE_LIFECYCLE_AUTHORITY_TRANSACTION_IMPLEMENTATION_REPORT.md`

Updated concise handoff:

- `AgentRead/TASK_PROGRESS.md`

New byte-identical archive of the pre-rewrite handoff:

- `AgentRead/202608/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_2_IMPLEMENTATION_20260814.md`

The archive and the pre-rewrite top-level handoff both had SHA256:

```text
EC58E4774E64B64D7A47EB07EE58AF0D9B1B4FE02A76C6F19127900BF64297EA
```

No Python file was changed during the documentation landing itself.

## 4. Why B0-2 uses a separate runtime module

B0-2 was deliberately added as the narrow canonical module:

```text
assignment_lifecycle_transaction_runtime.py
```

instead of expanding:

```text
assignment_lifecycle_authority_runtime.py
```

The retained B0-1 module contains only the reviewed B0-1A facts producer and
B0-1B generation clock. Their dedicated static guards explicitly prove the
absence of later StateStore, authority, ledger/result, event, and coordinator
capabilities. Keeping B0-2 separate preserves those guards and avoids
retroactively widening the reviewed B0-1A/B0-1B surface.

The new module executes only under its canonical package key and imports the
canonical profile, transition, event, and B0-1 runtime modules. It defines no
alternate profile, state enum, termination enum, event enum, producer ID,
authority ID, facts DTO, result DTO, ledger, or clock family.

## 5. LifecycleStateStore API and state ownership

`LifecycleStateStore` is the sole lifecycle-state storage writer boundary. It
stores one immutable replacement state containing:

```text
task_state                  [E,N] int64
robot_state                 [E,M] int64
ownership                   [E,N] int64
cumulative_failed_pairs     [E,M,N] bool
completion_count            [E,M] int64
termination_reason          [E] int64
version                     Python int
```

Construction requires an explicit exact `torch.device`, explicit unique env
rows, exact tensor shapes/dtypes/devices, positive `E/M/N`, and the exact
canonical event-profile subtype. It reads no environment or wrapper state.

Initialization and every prepared replacement validate:

- canonical task, robot, and termination enum values;
- only active tasks may be owned, and every active task has one owner;
- one robot owns at most one active task;
- `EXECUTING` is the inverse of exactly one active owned task;
- other robot states own no active task;
- terminal/non-active tasks have owner `-1`;
- an active owner pair is not already cumulatively permanently failed;
- `TEAM_INFEASIBLE` equals the all-robot cumulative-failure equation;
- completion counters are exact nonnegative int64 values;
- stored termination reason is coherent with terminal task state.

The store begins at version `0`. A successful prepared state swap replaces
the complete immutable internal state exactly once and advances the version by
one. Validation, ledger, or finalization failure before the swap does not
advance it. There is no row-wise externally visible mutation.

## 6. Snapshot, writer capability, and read confinement

`LifecycleStateSnapshot` is a B0-private frozen, clone/detach/contiguous,
no-alias snapshot bound to an opaque store identity and exact store version.
Its tensor accessors return clones.

Before a coordinator claims the store, `store.snapshot()` supports trusted
bootstrap and pure invariant testing. The coordinator then claims the unique
lifecycle writer capability. After that claim:

```text
store.snapshot():
  fails closed with snapshot_capability_confined

store._snapshot_for_lifecycle(capability):
  accepts only the exact bound private writer capability
```

The coordinator does not accept a caller-supplied state snapshot in
`transact()`. It captures the transaction-private current snapshot itself
while holding the publication lock. This prevents a retained raw store
reference from becoming a supported external current-state read path.

## 7. LifecycleAuthorityRuntime responsibility

`LifecycleAuthorityRuntime` is the sole B0 lifecycle semantic derivation
authority and uses the unchanged frozen identity:

```text
LIFECYCLE_AUTHORITY_V1
unique_lifecycle_authority_v1
```

Its pure `derive_candidate()` boundary consumes only:

```text
canonical ExecutionTransitionFacts
exact LifecycleStateSnapshot
exact TransitionGenerationContext tuple
```

It validates facts integrity and producer identity, device and `E/M/N`, exact
env/prestate equality, state invariants, terminal-prestate exclusion, and
per-row facts/context generation binding before candidate derivation.

The exact simultaneous-cause equations are implemented without resolver,
path, cost, cooldown, retry, budget, or policy input:

```text
completed = any_robot(C)
new_failed = F AND NOT failed0
updated_failed = failed0 OR new_failed
unavailable_release = U AND exact_active_owner0
release_request = R OR F OR unavailable_release
released = any_robot(release_request) AND NOT completed
```

Completion dominates release, so `C+R`, `C+U`, and `C+R+U` complete and do
not set `released`. Frozen facts validation rejects `C+F` and `U+Rc`. Release
causes deduplicate naturally.

Task candidate state preserves an existing `CLAIMED`, `NAVIGATING`, or
`ALIGNING` phase unless an explicit completion or release/failure/unavailable
edge exists. B0-2 does not infer task progression.

Completion attribution increments only the completing pre-transition owner:

```text
completion_count1[i] = completion_count0[i] + sum_j C[i,j]
```

TEAM state is derived only from the cumulative structural equation after
completion/release processing. Robot state is then projected only from
unavailability, exact active ownership, and feasible unowned available work.

## 8. C1 active-owner permanently-failed invariant

The frozen B0-2D-R C1 condition is enforced in prestate validation:

```text
task0[j] in {CLAIMED, NAVIGATING, ALIGNING}
AND owner0[j] == i
=> failed0[i,j] MUST be false
```

It is checked before candidate derivation and before ledger consume. A
violation rejects the full selected batch even if another robot remains
feasible and the task is not TEAM-infeasible. It produces no release, event,
repair, state swap, generation commit, publication, or coordinator poison.

## 9. Termination and deterministic lifecycle events

Final reason uses the exact priority:

```text
all tasks COMPLETED
  -> ALL_TASKS_COMPLETED

else all tasks in {COMPLETED, TEAM_INFEASIBLE}
  -> NO_FEASIBLE_TASKS_REMAIN

else time_limit_reached
  -> TIME_LIMIT

else
  -> NONE
```

Unmappable physical termination and physical truncation without a time-limit
fact fail before consume. `bad_transition` does not create a new reason.

The authority constructs only frozen lifecycle event records for:

```text
TASK_COMPLETED
TASK_RELEASED
TERMINAL_PAIR_FAILURE_RECORDED
TASK_BECAME_TEAM_INFEASIBLE
ROBOT_BECAME_UNAVAILABLE
ROBOT_RECOVERED
ROBOT_NEEDS_ASSIGNMENT
```

Ordering is explicit rather than incidental:

```text
env_id ascending
  -> frozen LifecycleEventType declaration rank
  -> task/pair/robot canonical ID tie-break
  -> per-env ordinal 0..K-1
```

Every event binds the exact env, episode generation, transition generation,
ordinal, facts consume token, authority identity, causal source, and payload.

## 10. Receipt-independent full candidate validation

Before `TransitionConsumeLedger.consume()`, the authority constructs and
revalidates the complete candidate:

- completion, release, new/updated failure, and completion-count equations;
- task/owner/robot state invariants and ownership inverse;
- TEAM equation and exact new TEAM edge;
- termination priority and physical-flag mapping;
- exact logical event set, order, payload, generation, token, and authority;
- result-equivalent state fields.

This stage does not call the frozen result factory. Consequently all expected
semantic failures remain receipt-free, consume zero times, mutate no state,
commit no generation, and publish nothing.

## 11. Coordinator API and exact transaction stages

The public coordinator surface is exactly:

```python
coordinator.poisoned
coordinator.read_published_view()
coordinator.transact(
    facts=canonical_facts,
    transition_contexts=exact_context_tuple,
)
```

It exposes no raw store, clock, ledger, receipt, result factory, authority
stamp, writer capability, or caller-controlled snapshot parameter.

One transaction holds the coordinator publication lock across:

```text
1. reject if poisoned
2. capture writer-capability transaction-private StateStore snapshot
3. validate exact current store version/content
4. validate exact outstanding clock contexts
5. derive and fully prevalidate the authority candidate
6. prepare the complete version+1 store replacement and immutable view state
7. revalidate store version and clock contexts while still receipt-free
8. ledger.consume() exactly once for the full batch
9. frozen LifecycleTransitionResultFactory.finalize() exactly once normally
10. validate finalized result against the prepared candidate
11. prepare the matching immutable state/generation/result view
12. atomically install the prepared StateStore replacement
13. explicitly commit the exact generation contexts
14. validate committed generations and cleared outstanding reservations
15. install the prepared PublishedLifecycleView and return it
16. release the publication lock
```

The retained success order is therefore:

```text
StateStore swap -> clock commit -> publication
```

No generic rollback or candidate cancellation was added.

## 12. C2 publication/read capability and observable atomicity

`PublishedLifecycleView` is a B0-private immutable projection binding:

```text
one exact LifecycleStateSnapshot
store version
episode generation vector
committed transition generation vector
derived terminated/truncated vectors
optional latest finalized LifecycleTransitionResult
```

If a result is present, its env, generations, state, ownership, failed pairs,
and termination reason must exactly match the view.

All external fresh current-state readers must use:

```text
coordinator.read_published_view()
```

That method acquires the same publication lock used by transactions. A reader
attempting to read after the internal StateStore swap but before clock commit
blocks. It can observe only:

```text
old state + old committed generation
or
new state + new committed generation
```

Retained old views remain immutable historical snapshots. They are not a
fresh-current read capability and cannot continue a poisoned runtime.

Raw StateStore and raw generation-clock objects are confined to trusted
bootstrap/producer and transaction-private orchestration. The coordinator
does not return them. After writer claim, raw StateStore snapshot reads fail.
The raw clock may be used by trusted bootstrap/producer code to reserve exact
contexts, but external current-state readers receive generations only through
the coordinator publication port.

## 13. Poison and post-receipt failure behavior

A normal prevalidation failure occurs before receipt issuance and does not
poison the coordinator. Any unexpected exception after receipt issuance is a
fatal no-fail-tail violation:

```text
coordinator poisoned:
  true

new publication:
  none

fresh current read:
  rejected

new transaction:
  rejected

automatic retry / second consume:
  none

rollback / cancellation:
  none
```

If result finalization fails before the store swap, the issued receipt remains
unfinalized inside the poisoned coordinator and normal orchestration does not
retry it. The frozen lower-level contract still independently permits an
explicit same-receipt retry after an invalid finalization attempt.

If clock commit fails after the StateStore swap, the new internal store state
and version remain in place, the clock remains uncommitted with its candidate
outstanding, the old published view remains installed, and every fresh read
or transaction fails closed. No mixed current view escapes.

## 14. Dedicated T1-T18 pure evidence

The standalone suite uses namespace-only canonical loading, deterministic CPU
fixtures, and no task-package initializer, Isaac, AppLauncher, or HARL import.

| Group | Result | Primary evidence |
|---|---:|---|
| T1 StateStore initialization/invariants | pass | valid mixed state; 13 semantic and 3 shape/dtype/device invalid cases reject |
| T2 immutable/versioned snapshot | pass | source/accessor alias isolation; frozen metadata; failure delta 0; success delta 1 |
| T3 all 32 `C/F/R/U/Rc` rows | pass | 12 valid, 20 invalid; exact state/owner/robot/result/event outcomes |
| T4 C1 invariant | pass | CLAIMED/NAVIGATING/ALIGNING invalid owner-failed states consume/swap/commit/publish zero |
| T5 completion attribution | pass | C, C+R, C+U, C+R+U and multi-robot/task credit exact owner |
| T6 failure/TEAM | pass | new, cumulative, and last feasible failure; resolver-like inputs absent |
| T7 robot projection | pass | all four prior states; completion/release/failure/U/Rc; terminal projection exact |
| T8 task phase preservation | pass | three active phases preserved without edge; completion/release/TEAM edges exact |
| T9 event order | pass | 10 simultaneous events; repeat value exact; rank/ties/ordinals/generation/token exact |
| T10 reason/physical mapping | pass | four reasons and terminal-over-horizon priorities; invalid flags pre-consume |
| T11 success path | pass | one batch consume, one finalize, one swap, one clock commit, one matching publication |
| T12 full-batch rejection | pass | `E=2`; C1 and frozen C+F gates allow no partial commit |
| T13 token/generation independence | pass | burned token creates delta 2 while committed generation delta is 1 |
| T14 receipt versus fail-stop | pass | frozen same-receipt retry legal; coordinator post-consume failure poisons without retry |
| T15 C2 concurrency | pass | Event-controlled reader blocks between swap and clock commit; old/old then new/new |
| T16 post-swap poison | pass | no publication/rollback/cancel/reconsume; historical view remains immutable |
| T17 capability/static isolation | pass | exact public surface; post-claim raw snapshot rejected; no wiring/heavy imports |
| T18 profile/default-off | pass | four existing and five raw forms reject; readiness and global side effects unchanged |

Final results in both normal and isolated processes:

```text
status=passed
num_tests=18
passed=18
failed=0
```

T14-T16 use only explicit `threading.Event` synchronization. They contain no
sleep-based race and release/join every started worker in `finally` paths.

## 15. Verification commands and exact results

Compilation:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_authority_runtime.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_transaction_runtime.py scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py scripts/environments/test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py
```

Result: passed.

B0-2 dedicated normal and isolated runs:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py --json
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -I -B scripts/environments/test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py --json
```

Results: `18/18` passed in each mode.

Recorded regression results:

```text
B0-1A dedicated producer:
  9/9 passed

B0-1B dedicated generation clock:
  12/12 passed

Phase-A lifecycle-transition contract:
  12/12 passed

event-gated MRTA contract:
  13/13 passed

profile contract:
  16/16 passed

event-profile schema contract:
  9/9 passed

focused Phase-A default-off identity:
  16/16 passed

production-wiring regression:
  10/10 passed
```

Relevant regression scripts were:

```text
test_assignment_phase_b0_1a_execution_facts_producer_pure.py
test_assignment_phase_b0_1b_generation_clock_pure.py
test_assignment_lifecycle_transition_contract.py
test_assignment_event_gated_mrta_contract.py
test_assignment_profile_contract.py
test_assignment_event_profile_schema_contract.py
test_assignment_phase_a_default_off_identity.py
test_assignment_profile_production_wiring.py
```

Final B0-2 artifact hashes:

```text
assignment_lifecycle_transaction_runtime.py:
  478DD5045E8FA243CD2F9EAF1C9E88AEA824CB5C39C659A18F0BB6E4B9AFC936

test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py:
  F689138E57BE200AE069211549BCD9ECFE0616C7F0DDD3353BE6CCF847C7E46A
```

`git diff --check`, trailing-whitespace inspection, scope inspection, static
forbidden-wiring checks, and thread/sleep inspection passed.

## 16. Frozen authorities and scope audit

The B0-2 implementation did not edit or redefine:

```text
assignment_lifecycle_transition_contract.py
assignment_event_contract.py
assignment_profile_contract.py
assignment_event_profile_schema_contract.py
```

The final repository-wide hash audit passed. The four frozen authorities were
byte-identical to preflight:

```text
assignment_lifecycle_transition_contract.py:
  1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9

assignment_event_contract.py:
  22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A

assignment_profile_contract.py:
  ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500

assignment_event_profile_schema_contract.py:
  04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF
```

The retained B0-1 module and dedicated runners were also byte-identical to
preflight:

```text
assignment_lifecycle_authority_runtime.py:
  CA7774808FB8901DBC209F61A8915713106A5DC9DA739D1BCE30C8952A21E10E

test_assignment_phase_b0_1a_execution_facts_producer_pure.py:
  0DB8C9B0515D9227E252DCAEC8C8B2885FF8FF704B61FC92C01421A6F5833C8F

test_assignment_phase_b0_1b_generation_clock_pure.py:
  BD5BD49C481FF20C8B87D62378D5487F5D579D14C8E9773C9850E7CB5B9B214C
```

No contract/runtime gap or need to revise a frozen schema was found. The
final audit also confirmed unchanged HEAD, empty index, no production-wiring
repository references, no selected numeric TBD, and no runtime RNG use.

Production wiring remains absent. The new transaction module is not imported
or constructed by the environment, task package initializer, wrapper,
resolver, resolver runtime, controller, or HARL path. Event-profile runtime
readiness remains `interface_only`; training remains `phase_a_blocked` and
playback remains `blocked`.

No environment, wrapper, resolver, controller, HARL, YAML/config, checkpoint,
installed-package, or numeric-policy file was changed.

## 17. Explicit non-implementation inventory

```text
environment pre-reset caller:
  not implemented

_get_dones / _reset_idx / _get_rewards integration:
  none

real owner-attributed physical reporters:
  not implemented

autoreset integration:
  not implemented

mailbox / terminal critic sidecar:
  not implemented

assignment resolver / Top-K / local sets / cost / retry scheduler:
  not implemented

CLAIMED -> NAVIGATING -> ALIGNING progression:
  not implemented or claimed

wrapper / controller / HARL transport:
  none

checkpoint-ready V3 / weight use:
  not implemented

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

real checkpoint tensor I/O:
  none

commit:
  none
```

All eleven numeric method TBDs remain unresolved:

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

## 18. Stop boundary and next gate

The prescribed frozen-contract, transaction-atomicity, and scope-expansion
STOP conditions were not reached. Pure tests demonstrate old/old-or-new/new
external publication without rollback and without a frozen schema change.

The next action is independent GPT/user review of the uncommitted B0-2 pure
foundation. This report does not authorize environment pre-reset integration,
B0-3+, Phase B/C/D/E, Isaac, training, playback, evaluation, selection of any
numeric TBD, or a commit.

```text
B0-2:
  complete at pure/default-off transaction-foundation level
  awaiting GPT/user review

B0-3+:
  not entered
  not authorized

Phase B/C/D/E:
  not entered
  not authorized
```
