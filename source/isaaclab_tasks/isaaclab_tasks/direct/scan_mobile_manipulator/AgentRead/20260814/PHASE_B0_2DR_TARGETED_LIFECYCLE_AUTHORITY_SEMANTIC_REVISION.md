# Phase B0-2D-R Targeted Lifecycle Authority Semantic Revision

## 1. Classification

```text
classification:
  PHASE-B0-2DR-TARGETED-SEMANTIC-REVISION-COMPLETE-AWAITING-GPT-REVIEW

starting/ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch:
  main

B0-1A:
  review passed

B0-1B:
  review passed

B0-2D:
  conditional review completed
  PHASE-B0-2D-DESIGN-CONDITIONAL-PASS

B0-2D-R:
  targeted design revision complete

active-owner permanent-failed invariant:
  frozen

success-tail reader/publication atomicity:
  frozen

Phase-A contract revision:
  none

B0 contract/runtime gap:
  none

Python/test/runtime changes:
  none

B0-2 implementation:
  not authorized

B0-3+:
  not authorized

Phase B/C/D/E:
  not entered

training/playback/evaluation:
  not run

commit:
  none
```

This is a documentation-only targeted revision. It implements no lifecycle
authority, state store, coordinator lock, environment hook, reader port,
ledger/result path, scheduler, resolver, or runtime integration.

## 2. Base authority, scope, and precedence

Base authority:

```text
AgentRead/20260814/
PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md
```

This revision controls only:

```text
C1:
  active owned pair MUST NOT already be cumulative permanently failed

C2:
  store-swap -> generation-commit intermediate state MUST be externally
  unobservable
```

Where the base B0-2D design conflicts with C1 or C2, this B0-2D-R document
controls. Every other D1-D6 semantic, matrix row, state projection, event rule,
reason rule, capability owner, and deferred boundary remains controlled by the
base document.

The two conditions are implementable using the already planned versioned
state-store snapshot, retained B0-1B clock, coordinator capability boundary,
and existing immutable result/handoff. No frozen facts, result, event,
generation, profile, or public transaction field is missing. Therefore neither
prescribed STOP condition is triggered.

## 3. C1 — Active ownership cannot use a permanent-failed pair

### 3.1 Exact normative invariant

The symbols retain the base B0-2D meanings:

```text
task0[e,j]:
  immutable pre-transition task state

owner0[e,j]:
  immutable pre-transition task owner

failed0[e,i,j]:
  immutable state-store episode-cumulative permanent failed-pair snapshot

active task state:
  CLAIMED, NAVIGATING, or ALIGNING
```

For every selected environment `e`, task `j`, and robot `i`:

```text
if:
  task0[e,j] in {CLAIMED, NAVIGATING, ALIGNING}
  AND owner0[e,j] == i

then:
  failed0[e,i,j] MUST be false
```

Because every active task already MUST have exactly one owner, the equivalent
form is:

```text
for every active task j:
  failed0[e, owner0[e,j], j] MUST be false
```

An active task may never be owned or executed by a robot-task pair already
recorded as episode-cumulative permanent structural failure. This rule applies
independently of the current transition's `C/F/R/U/Rc` bits; even an all-zero
raw-cause row cannot continue an invalid active ownership prestate.

### 3.2 Validation point and failure behavior

C1 is a Stage-1 full-state prevalidation invariant. The authority evaluates it
against the same immutable, exact-version store snapshot whose task and owner
projection has already been cross-checked against the facts batch.

Any selected row with:

```text
active task j
owner0[e,j] == i
failed0[e,i,j] == true
```

makes the entire selected batch **INVALID** before:

```text
candidate derivation
ledger consume
result finalization
state mutation
generation commit
event/result/handoff construction
publication
```

The failure path emits no lifecycle event and publishes no partial result. It
MUST NOT:

- silently release the task;
- repair or clear ownership;
- clear or downgrade the permanent failed-pair bit;
- select another owner;
- reinterpret the row as TEAM_INFEASIBLE;
- continue execution;
- consume the ledger and attempt correction later.

One invalid row rejects the complete selected batch; valid rows are not
mutated or committed first.

### 3.3 C1 is distinct from TEAM_INFEASIBLE

C1 and the frozen TEAM equation are complementary checks:

```text
C1:
  pair-local active-ownership coherence

TEAM_INFEASIBLE:
  task-global terminal classification
  task != COMPLETED AND all_i updated_failed[e,i,j]
```

For example:

```text
task j is active
owner0[e,j] == i
failed0[e,i,j] == true
at least one other robot k has failed0[e,k,j] == false
```

The all-robot TEAM condition is false, but C1 still rejects the batch
immediately. The authority does not wait for TEAM derivation to discover that
the current owner itself is permanently failed.

If every pair is already failed while the task is active, the pre-transition
TEAM equation is also violated. That additional violation does not replace or
weaken C1; both invariants are part of Stage-1 validation and neither authorizes
repair.

### 3.4 Targeted effect on the B0-2D matrix

The 32 `C/F/R/U/Rc` bit classifications remain unchanged. B0-2D-R narrows the
base phrase “valid active owned pair” to mean, additionally:

```text
failed0[e,i,j] == false
```

Consequently, for every valid active owned-pair matrix row with `F=1`:

```text
new_failed[e,i,j]
  = F[e,i,j] & ~failed0[e,i,j]
  = true
```

The existing permanent-failure event is therefore emitted for every valid
`F=1` row, subject to the base canonical event order. The frozen equation
`new_failed = F & ~failed0` is unchanged.

The base B0-2D paragraph that permits repeated structural input against an
already cumulative-failed active owner pair to produce `new_failed=false` plus
an owner-gated release is superseded. Under C1, that prestate is invalid before
D3 derivation. Because frozen facts already owner-gate `F`, an unowned repeated
`F` is independently invalid as well. No “duplicate failure release” reaches
the B0 lifecycle result path.

This is the authorized C1 precondition tightening, not a redesign of legal
simultaneous-cause precedence or the frozen failed-pair equation.

### 3.5 Future assignment validation is independent

The future Phase-B staged assignment commit MUST reject any claim, assignment,
or transfer that would place a task on a pair whose cumulative failed bit is
true. That future validation prevents creation of an invalid state.

B0 Stage-1 lifecycle prevalidation independently detects and rejects such a
state if it nevertheless exists. Upstream prevention and downstream detection
are both mandatory; neither is a substitute for the other, and neither grants
the lifecycle authority a repair/reassignment capability.

### 3.6 Why C1 needs no frozen schema change

The required values already exist at the authority boundary:

- `ExecutionTransitionFacts` carries exact pre-transition task state and
  ownership;
- `LifecycleStateStore` is already the single owner of cumulative failed pairs
  and supplies the exact-version `failed0` snapshot;
- the result factory already accepts `prior_failed_pairs` and validates
  `updated_failed = prior_failed | new_failed`.

C1 is a stronger B0 runtime cross-state invariant before factory use. It does
not add a facts field, result field, event type, state enum, generation, or
descriptor.

## 4. C2 — Success-tail reader and publication atomicity

### 4.1 Authority ownership remains unchanged

```text
LifecycleAuthorityRuntime:
  sole lifecycle derivation authority

LifecycleStateStore:
  sole lifecycle-state storage writer boundary

LifecycleGenerationClock:
  sole episode/transition generation writer for its retained domain

Coordinator:
  transaction/order/publication capability owner
  not a semantic authority
```

The coordinator's publication lock controls visibility and ordering only. It
does not derive completion, failure, state, events, or reason, and does not
become another lifecycle authority.

### 4.2 Exact external-reader boundary

The coordinator owns one exclusive transaction/publication lock. It acquires
that lock no later than the final pre-Stage-6 StateStore-version and
generation-context revalidation, then holds it continuously across ledger
consume, result finalization, StateStore swap, clock commit,
authoritative-success marking, and installation of the new published immutable
view.

Every external acquisition of current lifecycle state MUST participate in that
same publication boundary. At minimum, external/observable readers include:

```text
event observation builder
event shared-observation builder
scheduler
local-set builder
resolver
controller assignment reader
diagnostics/logger/debug current-state snapshot
wrapper/facade handoff reader
terminal-sidecar builder when it reads published lifecycle state
```

“External” is determined by capability and output visibility, not by thread.
A builder running on the coordinator thread is external for this rule if it
returns, caches, or publishes a current-state artifact outside the transaction.

These consumers MUST NOT receive a raw `LifecycleStateStore` snapshot
capability, the store object, the retained clock object, or a direct
`LifecycleGenerationClock.snapshot()` capability. The StateStore writer lock
and clock's private lock are separate inner locks and are not, individually or
together through two independent calls, a publication boundary.

A fresh external current-state read is obtained only through the coordinator's
publication/read port. State and generation MUST be acquired in the same
publication-lock acquisition; two separate calls are invalid even if each call
individually takes the lock, because a transition could linearize between them.
The single read returns one no-alias immutable view containing:

```text
one published lifecycle snapshot
the exact committed transition generation for that snapshot
```

This is a B0-private runtime projection of existing state/result/generation
data, not a new frozen public DTO or schema. The coordinator replaces the
single current published view only after the matching state and clock commits
succeed. The clock's outstanding-candidate generation is transaction-private
and is never part of the published current view.

For a newly finalized physical transition, its immutable result/handoff is
installed under the same publication lock; if a current view exposes that
transition handoff, its generation MUST match the paired committed generation.
Historical handoffs remain separate immutable generation-bound artifacts and
are not mandatory fields of every current view. In particular, an episode
rebuild does not invent a fake transition result, and a future post-`a0`
assignment commit does not rewrite the historical lifecycle result.

The outer lock order is fixed:

```text
coordinator publication/transaction lock
  -> LifecycleStateStore internal lock
  -> LifecycleGenerationClock internal lock
```

No internal capability holder may acquire the coordinator publication lock in
the reverse direction.

A consumer may retain and later read an old immutable published view without
holding the lock; it remains an internally consistent old-state/old-generation
historical snapshot. Obtaining the current published view or building a new
consumer artifact from live current state must cross the publication/read
port.

### 4.3 Internal transaction-private reads

The authority/coordinator may read candidate or newly swapped internal state
while the exclusive publication lock is held. A terminal-sidecar builder may
also consume staged/new state as an internal transaction participant if its
artifact is not exposed until publication succeeds.

These are transaction-private reads. They do not expose a current-state handle
to an external consumer and are permitted between store swap and clock commit.
“Unobservable” therefore does not prohibit internal candidate validation or
artifact construction; it prohibits external visibility and capability
bypass. A transaction-private artifact MUST NOT escape through a callback,
cache, logger, debug hook, or return value before Stage 9 publication.

### 4.4 Exact observable snapshot invariant

For every externally observable lifecycle view:

```text
(published lifecycle state,
 published transition generation)

MUST correspond to one authoritative committed transition boundary
```

The following pairs MUST never be externally observable:

```text
new lifecycle state + old committed transition generation
old lifecycle state + new committed transition generation
```

If a reader requests current state while the coordinator is in the success
tail, it blocks on the publication lock. After success it receives the new/new
pair. If the transaction becomes poisoned, it receives a fatal/poisoned error
and no current state. It never receives the internal intermediate pair.

### 4.5 Revised Stage 8 and Stage 9

The base state-swap-before-clock-commit order remains exact:

```text
8. While continuing to hold the coordinator's exclusive
   transaction/publication lock acquired before Stage 6:

   a. revalidate the prepared LifecycleStateStore version and the exact
      outstanding B0-1B transition-generation context;

   b. perform the already prevalidated, no-fail LifecycleStateStore internal
      pointer/state swap;

   c. commit the exact B0-1B transition generation; this clears the outstanding
      candidate and is the final internal success marker;

   d. only after both operations succeed, mark the authority transaction
      authoritative-successful.

   No external lifecycle-state reader may observe between (b) and (c), and the
   coordinator retains the publication lock through Stage 9.

9. Still under that publication lock, project the finalized reason, install
   and expose the immutable result/handoff plus matching published lifecycle
   view, then release the lock. Only afterward may external readers obtain the
   new view or the environment enter autoreset.
```

All fresh external read paths use the same outer lock/read port. Inner
StateStore and clock locks may protect their own state, but no external path
may acquire an inner capability and then bypass or invert the coordinator
publication boundary.

### 4.6 Failure after StateStore swap and before clock commit

Stage 8 is designed as a fully prevalidated no-fail success tail. If the
theoretically impossible sequence nevertheless occurs:

```text
StateStore internal swap succeeds
clock commit unexpectedly fails
```

then the coordinator, while still excluding readers:

```text
publishes nothing
does not install a new current view
marks the runtime poisoned/fatal
permits no normal continuation or external current-state read
requires teardown
does not roll back state
does not roll back the clock
does not consume again
does not silently retry
does not cancel the candidate through a new generic API
```

The internal store may already contain the candidate, but it cannot become a
legal observable runtime state. After the publication lock is released in the
poison path, every fresh read/operation fails on the poison guard instead of
returning either the internal state or the prior view. An already retained old
immutable view remains coherent historical data but cannot authorize runtime
continuation.

This is a fatal invariant violation, not a rollback protocol.

### 4.7 Why C2 needs no frozen public transaction schema

The existing `LifecycleTransitionResult` already binds transition generation,
updated task/robot/ownership state, failed pairs, reason, events, token, and
receipt. The B0-1B generation context and snapshot rows are explicitly
runtime-private. The planned coordinator already owns exclusive transaction
ordering and immutable handoff publication.

C2 therefore requires capability confinement and a shared outer publication
boundary, not a new result field, generation field, event, state, or frozen
transaction DTO. Source inspection also confirms that the current dormant
clock has no production consumer; its direct `snapshot()` use is confined to
the pure B0-1B tests, so no existing event runtime read path must be preserved.

## 5. Semantics not reopened by B0-2D-R

The following base B0-2D decisions remain unchanged:

```text
all 32 C/F/R/U/Rc bit classifications
completion masks legal release
C & F invalid
U & Rc invalid
release-cause deduplication
robot projection P
healthy ALL_TASKS_COMPLETED/NO_FEASIBLE_TASKS_REMAIN robots WAITING_FOR_TASK
TIME_LIMIT does not release active work
TEAM_INFEASIBLE only from cumulative permanent structural failure
CLAIMED -> NAVIGATING -> ALIGNING progression deferred
canonical lifecycle-event ordering
TerminationReason priority
frozen same-receipt retry capability
normal coordinator fail-stop policy
single lifecycle-state writer
future typed post-a0 assignment commit separation
```

The C1 refinement changes only what qualifies as a valid active owned-pair
prestate and the now-unreachable repeated-failure wording. C2 changes only the
visibility contract around the already frozen success-tail order.

## 6. Future implementation verification oracle

No implementation or test is authorized now. A later authorized B0-2 test
slice must, at minimum, prove:

### C1

- active `CLAIMED`, `NAVIGATING`, and `ALIGNING` owners each reject when their
  own `failed0` pair is true;
- rejection still occurs when another robot remains feasible and TEAM is
  false;
- rejection with one bad row mutates/consumes/commits/publishes no selected
  row;
- no release, event, repair, or alternate owner is produced;
- every valid owner-gated `F=1` row starts with `failed0=false`, produces
  `new_failed=true`, and emits the canonical new-pair event;
- future assignment commit rejects creation of the same invalid pair state,
  independently of lifecycle prevalidation.

### C2

- a controlled reader attempting access after store swap but before clock
  commit blocks and observes no intermediate state;
- after success, the reader obtains only the new-state/new-generation view;
- a retained immutable prior view remains old-state/old-generation;
- no external consumer holds direct store/clock snapshot capability;
- an injected impossible clock-commit failure after store swap publishes
  nothing, poisons the coordinator, and makes every fresh read/operation fail;
- there is no rollback, second consume, silent retry, or cancellation path.

These are later pure concurrency/capability tests, not evidence run by this
documentation phase.

## 7. Numeric and phase boundary

All eleven method numeric parameters remain unresolved:

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

B0-2D-R chooses no value. It adds no lifecycle state, event, result field,
generation field, threshold, retry rule, or runtime-ready switch.

Still unauthorized are B0-2 implementation, B0-3+, environment integration,
state/authority/ledger/result runtime, external reader wiring, sidecar/HARL
transport, Phase B/C/D/E, checkpoint-ready V3, training, playback, evaluation,
and commit.

## 8. Evidence and final handoff

The revision rechecked without modification:

- frozen task/robot/reason identities and facts owner/conflict validation;
- result-factory `prior_failed_pairs` input and cumulative failure equations;
- event rule that a pair-failure event represents only a newly recorded pair;
- event-profile interface-only/default-off readiness;
- B0-1A producer-only responsibility and absence of derived failed state;
- B0-1B retained clock, outstanding candidate, private snapshot, and explicit
  success-only commit;
- base B0 state ownership, candidate derivation, Stage-8 order, and immutable
  handoff design.

Documentation/scope verification is limited to status, diff/whitespace/fence,
classification, path, and changed-file checks. No Python implementation test,
Isaac, AppLauncher, training, playback, evaluation, or checkpoint tensor I/O
is run.

Final decision:

```text
STOP — B0 CONTRACT/RUNTIME GAP:
  not triggered

STOP — B0-2D-R DESIGN CONFLICT:
  not triggered

B0-2D-R controls:
  C1 and C2 only

next action:
  GPT/user review

implementation authorization inferred:
  none
```

Work stops at this targeted design revision. Do not begin B0-2 implementation
without new explicit authorization.
