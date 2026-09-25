# Phase B1 Pure Initial-Claim Transaction Implementation Report

## Classification

~~~text
classification:
  PHASE-B1-PURE-INITIAL-CLAIM-TRANSACTION-COMPLETE-AWAITING-GPT-REVIEW

B0:
  CLOSED

B1D:
  REVIEW PASS / FROZEN

P2 current publication:
  IMPLEMENTED

per-env provenance:
  IMPLEMENTED

reset / lifecycle / assignment publication unification:
  IMPLEMENTED

independent assignment tick:
  NOT USED

single-use request context:
  IMPLEMENTED

request token allocator:
  IMPLEMENTED

initial claim deriver:
  IMPLEMENTED

C2 batched independent claims:
  IMPLEMENTED

G2 terminal gating:
  IMPLEMENTED

StateStore assignment-owned typed mutation:
  IMPLEMENTED

EffectiveAssignmentCommitArtifact:
  IMPLEMENTED

historical lifecycle result immutability:
  VERIFIED

assignment -> lifecycle compatibility:
  VERIFIED

assignment -> reset compatibility:
  VERIFIED

P2 publication atomicity:
  VERIFIED

terminal publication regression:
  PASS

B0 regressions:
  PASS

existing profiles:
  unchanged

production environment assignment wiring:
  NOT IMPLEMENTED

inter-step claim-window fence:
  NOT IMPLEMENTED
  REQUIRED BEFORE PRODUCTION WIRING

wrapper/HARL:
  NOT IMPLEMENTED

runtime readiness:
  still blocked

Isaac:
  not run

training/playback/evaluation:
  not run

numeric TBD:
  unresolved

commit:
  none
~~~

## Repository boundary

~~~text
starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch:
  main

starting index:
  empty

ending index:
  empty

commit:
  none
~~~

The worktree already contained the reviewed B0 cohort and Phase-A fixture
change before B1 began. Those changes were preserved. B1 did not reset,
discard, stage, or commit any user/pre-existing work.

## Changed and new files

Implementation:

~~~text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_initial_claim_runtime.py                         new
  assignment_lifecycle_transaction_runtime.py                 modified
  assignment_event_profile_runtime_domain.py                  modified
~~~

Pure verification:

~~~text
scripts/environments/
  test_assignment_phase_b1_initial_claim_transaction_pure.py  new
  test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
  test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py
  test_assignment_phase_b0_3i4_terminal_handoff_pure.py
~~~

The three B0 runners changed only their expected P2/current-read or newly
authorized narrow claim-capability surface. Their B0 semantic oracles remain
unchanged.

Documentation:

~~~text
AgentRead/202608/20260821/PHASE_B1_PURE_INITIAL_CLAIM_TRANSACTION_IMPLEMENTATION_REPORT.md
AgentRead/TASK_PROGRESS.md
~~~

No TASK_PROGRESS archive was created. The existing 300-line handoff could be
updated in place without discarding linked B0/B1D history.

## Explicitly unchanged production and frozen scope

The following remained byte-identical to B1 preflight:

~~~text
scan_mobile_manipulator_env.py
assignment_harl_wrapper.py
assignment_lifecycle_transition_contract.py
assignment_event_contract.py
assignment_profile_contract.py
assignment_event_profile_schema_contract.py
~~~

No resolver, controller, runner, buffer, configuration/YAML, training,
playback/evaluation, checkpoint, installed package, or site-packages file was
changed.

## P2 unified current-publication authority

`_EventRuntimeCurrentPublication` is now the one coordinator-owned fresh
current object. It contains:

~~~text
one exact immutable PublishedLifecycleView
one opaque coordinator/domain-lifetime publication identity
one exact full-domain Store version
one immutable provenance entry per environment row
~~~

The retained coordinator has one stored current pointer, `_published_view`,
whose value is now the P2 aggregate. The legacy private name was retained to
avoid creating a second pointer. There is no assignment-only current cache,
side provenance registry, parallel lifecycle-current API, or second
publication coordinator.

`read_published_view()` and the retained-domain `current_read_port.read_current()`
return the exact P2 object. The nested immutable lifecycle view is available as
`publication.lifecycle_view`. Compatibility projections such as
`publication.lifecycle_state`, generations, done flags, and result all delegate
to that one nested object and create no second current truth.

## P2 producer migration

All four producers use the original coordinator publication lock and success
tail:

| Producer | Installed selected-row provenance |
|---|---|
| coordinator construction | `PREBOOTSTRAP` |
| lifecycle transition | `FINALIZED_LIFECYCLE_TRANSITION` |
| episode rebuild | `CANONICAL_EPISODE_RESET` |
| initial claim | `ASSIGNMENT_COMMIT` |

Construction creates one P2 publication with episode and transition
generations `-1` and all rows `PREBOOTSTRAP`. No request token, facts token,
transition candidate, receipt, or lifecycle result is created.

A lifecycle transaction installs a new full-domain P2 publication whose rows
all bind the exact finalized `LifecycleTransitionResult`. A terminal lifecycle
tail still installs:

~~~text
StateStore replacement
generation commit
P2 lifecycle publication
matching terminal slot(s)
~~~

under the same publication lock before any reader can proceed. The terminal
artifact retains the exact nested lifecycle view and result. It does not retain
a competing current pointer.

Episode rebuild creates one new P2 identity. Selected rows become canonical
reset provenance rooted at that publication identity; unselected provenance
entry objects remain exact-identical. The reset lifecycle view has `result=None`
by construction. I1 reset equations, Store-version increment, episode advance,
and transition preservation are unchanged.

Initial claim creates one new P2 identity. Selected rows bind the exact
`EffectiveAssignmentCommitArtifact`, immediate predecessor publication
identity, and exact root provenance. Unselected provenance entries remain
exact-identical.

## Per-row provenance variants

The private sealed enum is:

~~~text
PREBOOTSTRAP
FINALIZED_LIFECYCLE_TRANSITION
CANONICAL_EPISODE_RESET
ASSIGNMENT_COMMIT
~~~

Variant construction is coordinator-capability-bound and rejects incoherent
field combinations. In particular:

- prebootstrap and reset carry no lifecycle result or assignment artifact;
- lifecycle provenance carries an exact `LifecycleTransitionResult`;
- assignment provenance carries an exact effective artifact;
- assignment provenance retains the exact immediate predecessor identity;
- every assignment row retains its reset-or-lifecycle root identity and exact
  root result when the root is a lifecycle transition.

Mixed full-domain publications are supported. Tests establish one current
publication containing reset, assignment, and lifecycle provenance rows at the
same time.

## Publication identity

The coordinator owns a domain-lifetime monotonic serial allocator. Each
identity also binds the exact opaque domain and publication-factory capability.
Serials are never reused; preparation gaps are legal. The publication identity
is not a Store version, episode generation, physical transition generation,
request token, or assignment tick.

## Initial-claim source baseline

`_InitialClaimSourceBaseline` is factory-only and captured inside the retained
coordinator publication boundary. The caller supplies only selected env IDs
and the requested task-by-robot tensor.

The baseline binds:

~~~text
exact canonical profile object
exact retained domain identity
exact current P2 object and opaque identity
exact StateStore identity/version
selected env IDs and domain rows
full episode and physical-transition generation vectors
full task/robot/ownership/failure/count/reason state
terminated/truncated projection
selected-row source kinds and exact provenance objects
~~~

The legal private source kinds are:

~~~text
FINALIZED_LIFECYCLE_TRANSITION
CANONICAL_EPISODE_RESET
POST_ASSIGNMENT
~~~

Source discrimination uses the exact P2 provenance enum. It never infers reset
from `view.result is None`.

Transition source capture validates the exact retained result and its current
row state. Terminal or truncated rows are rejected before commit. Reset source
capture validates canonical reset state and accepts episode `>=0`, including
the first reset at physical transition generation `-1`. No fake result,
transition zero, event, facts, receipt, or Phase-A DTO is created.

POST_ASSIGNMENT binds the exact immediate prior artifact. Consecutive
assignment artifacts retain exact predecessor provenance and reuse the exact
original root provenance object.

## InitialClaimRequest and request identity

The narrow dormant domain capability is:

~~~text
initial_claim_port.prepare_initial_claim(
  selected_env_ids,
  requested_task_by_robot,
)

initial_claim_port.commit_initial_claim(request)
~~~

It does not expose the Store, coordinator, baseline constructor, raw snapshot,
Store version constructor, registry, allocator, publication lock, or provenance
writer. The environment port does not contain or receive this capability.

The request representation is exact:

~~~text
selected_env_ids:         [K] int64, K >= 1, unique
requested_task_by_robot:  [K,M] int64
NO_CLAIM:                 -1
legal task IDs:           0..N-1
~~~

Every selected row has at least one claim. Empty transactions, all-NO_CLAIM
selected rows, duplicate env IDs, duplicate nonnegative task IDs, invalid IDs,
and wrong shape/dtype/device are rejected without Store/publication mutation.

The coordinator owns a monotonic domain-lifetime request-token allocator.
Tokens are never reset or reused; gaps are legal and no RNG is used. The opaque
context binds the token, exact baseline object, request identity, selected IDs,
profile/domain identity, and a content digest over the captured selected/request
tensors.

## Request registry resource policy

The active registry stores:

~~~text
token -> exact unconsumed context identity
~~~

The context retains only the exact identity metadata, baseline reference, and
request digest needed for validation; the registry does not duplicate the full
request tensor. The issued immutable request owns its captured tensor.

On success, the active context is removed and the consumed token is merged into
a tuple of inclusive integer intervals. Consumed state therefore retains no
request tensor, source state, or artifact. Interval membership gives permanent
duplicate/replay rejection without reusing token numbers. Active abandoned
contexts remain valid only for the lifetime of the domain and are removed at
domain teardown; no cancellation API exists in this first slice.

Correct provenance history is carried by immutable effective artifacts, not by
the request registry.

## Pure InitialClaimDeriver

`InitialClaimDeriver` holds only the exact profile object. It has no Store
writer, lock, lifecycle authority stamp, ledger, result factory, terminal
consumer, generation writer, token allocator, registry, environment, resolver,
or policy capability.

For every requested pair `(e,i,j)`, it requires:

~~~text
termination reason NONE
terminated false
truncated false
robot i NEEDS_ASSIGNMENT
robot i owns no active task
task j AVAILABLE
task j unowned
pair (i,j) not cumulatively failed
~~~

C2 uses one task slot per robot and rejects duplicate task IDs within an env.
No arbitration, ordering winner, cost, distance, Top-K, mask, DVM, scheduler,
resolver, retry cadence, or policy value participates.

The deriver changes only selected assignment-owned projections:

~~~text
task:       AVAILABLE -> CLAIMED
ownership:  -1 -> robot ID
~~~

It then recomputes every robot in each selected row:

~~~text
prior UNAVAILABLE                           -> UNAVAILABLE
owns exactly one active task                -> EXECUTING
has structurally available nonfailed work   -> NEEDS_ASSIGNMENT
otherwise                                   -> WAITING_FOR_TASK
~~~

Unselected state is bit-identical. Failed pairs, completion counts, reasons,
events, facts, receipts, terminal artifacts, coverage/reward evidence,
episode generations, and physical transition generations are unchanged.

## Typed StateStore prepare route

`LifecycleStateStore._prepare_initial_claim_swap()` is the only new Store
mutation preparation route. It requires the already retained unique writer
capability and exact old snapshot identity/version. It independently rebuilds
the expected task/ownership/robot projection from the effective request,
verifies all unselected and lifecycle-owned fields, runs the canonical state
invariants, checks version overflow, and prepares one version-plus-one complete
replacement.

No `set_state`, `write_snapshot`, generic tensor setter, second Store, second
writer, or assignment writer lock was added.

## EffectiveAssignmentCommitArtifact

The immutable factory-only artifact retains:

~~~text
exact profile/domain identity
exact request and request-context identity
exact token
exact source P2 object and opaque identity
selected source kinds and exact predecessor provenance
source and committed Store versions
selected env IDs
unchanged episode/transition generations
separate requested and effective tensors
pre/post task, robot, and ownership projections
exact root provenance and root lifecycle result when applicable
~~~

Requested and effective values are equal in this conflict-free slice, but are
separate cloned tensor objects. Accessors return clones. Caller input/accessor
mutation cannot change the request, artifact, Store, current publication, or a
future transaction.

The artifact is the only B1 claim history marker. No `TASK_CLAIMED` event or
fake `LifecycleTransitionResult` was added. Historical lifecycle results,
events, tokens, receipts, and ownership tensors remain unchanged.

## G2 terminal gating

Request issuance is allowed from an otherwise legal exact current source even
when a selected row still has a historical occupied terminal slot. Commit
always rechecks under the coordinator publication lock.

If any selected row is occupied, the whole selected C2 batch rejects with no
Store mutation, request consumption, artifact, P2 publication, or poison. An
occupied unselected row does not invalidate G2 claim semantics. R3 remains a
separate full-domain physical-step block.

After exact terminal ack, the same request may be explicitly retried only when
its P2 source remains exact-current. Any intervening successful reset,
lifecycle, or assignment publication makes it stale.

## Stale and replay semantics

Commit revalidates:

~~~text
exact active context/token/request digest
exact P2 object and opaque identity
exact Store identity/version and state
exact episode/transition generations
exact selected-row provenance objects
G2 selected-row terminal capacity
~~~

Mismatch rejects as stale or invalid before the Store swap. There is no
rebasing, source refresh, task replacement, arbitration, automatic retry, or
cancellation.

Multiple requests may share one source. The domain operation lock and
coordinator publication lock serialize commits. The first success changes the
global Store version and P2 identity; all competing old-source requests reject
as stale.

Consumed-token interval membership is checked before source staleness, so an
exact replay reports consumed even though its source is also stale.

## Exact transaction and no-fail tail

The dormant domain route acquires:

~~~text
domain operation lock
  -> coordinator publication lock
     -> StateStore internal lock
~~~

Before the no-fail tail it completes:

~~~text
poison/profile/domain guard
request/context/token validation
current P2, Store, clock, and provenance revalidation
G2 selected-row check
pure C2 derivation and state invariant validation
typed Store replacement preparation
result-absent nested lifecycle view preparation
effective artifact allocation
selected-row provenance merge and P2 allocation
active-registry replacement allocation
consumed-interval replacement allocation
final exact source/context/G2 revalidation
~~~

The success tail is:

~~~text
prepared StateStore pointer swap
prepared active/consumed request-state swaps
prepared P2 current-publication pointer install
return the exact artifact installed in selected provenance rows
~~~

Every success contains at least one claim, increments the Store version once,
and leaves episode and physical transition generations unchanged.

Ordinary failures before Store swap leave Store, P2, request consumption,
terminal slots, generations, and poison unchanged. A transient G2 request may
be retried explicitly.

An unexpected failure after Store swap poisons the coordinator/domain. There is
no rollback, unconsume/reconsume, alternate publication, substitute artifact,
second consume, normal retry, or fresh continuation. The deterministic failure
injection is private, default-off, and absent from configuration.

## P2 reader and terminal atomicity

All current reads use the coordinator publication lock. `threading.Event`
interlocks prove that a reader attempting to enter after the claim Store swap
cannot observe until the prepared P2 pointer is installed. The observable pair
is therefore old Store/old P2 or new Store/new P2, never mixed.

The B0 terminal interlock separately proves that a reader cannot observe a new
terminal lifecycle P2 before its matching terminal slot is installed. I4
synchronous exact-key ack and R3 semantics remain unchanged.

## Assignment compatibility

Assignment followed by lifecycle transition was exercised through the retained
pure I3/B0 path. The I3 execution prestate sees post-assignment ownership; an
owner-qualified completion is attributed to the claimed robot. The successful
lifecycle transition installs new lifecycle provenance while the prior
assignment artifact remains immutable history.

Assignment followed by partial episode rebuild resets only selected state and
provenance, advances only selected episode generation, preserves physical
transition generation, and leaves unselected P2 provenance exact-identical.

Assignment followed by a terminal lifecycle transition preserves same-lock
P2-plus-terminal-slot visibility. The I4 terminal suite remains 16/16.

## Concurrency boundary

Deterministic `threading.Event` tests cover:

~~~text
assignment vs assignment:
  one success; the competing old-source request becomes stale

assignment vs episode rebuild:
  domain operation lock serializes claim then reset

assignment vs lifecycle finalization:
  domain operation lock serializes claim then finalize;
  the next I3 prestate sees claimed ownership
~~~

This remains a pure/dormant domain guarantee. The operation lock covers claim,
finalization, and rebuild transactions; it does not cover a real environment's
earlier action/physics interval. No inter-step claim-window fence was
implemented. Production assignment wiring remains forbidden and blocked until
that separate fence is designed and integrated at the real step-admission
boundary.

## Dedicated B1 suite

~~~text
test_assignment_phase_b1_initial_claim_transaction_pure.py

normal:  23/23 passed
-I -B:   23/23 passed
~~~

The suite covers B1-T1 through B1-T23:

~~~text
canonical reset source including transition -1
nonterminal lifecycle source
POST_ASSIGNMENT chaining
C2 multi-robot one-version batch
robot/task/failed-pair illegality
structural request rejection
G2 selected-row block and ack retry
stale source and competing requests
request/effective no-alias
assignment-owned-only delta
historical lifecycle-result immutability
P2 reader atomicity
post-swap poison
duplicate consume/replay
default-off/no production wiring
frozen hash and global side-effect audit
no-op/mixed-batch atomicity
assignment concurrency
all P2 producers and mixed-row provenance
assignment -> lifecycle transition
assignment -> reset
~~~

The runner imports no Isaac, AppLauncher, Omni, PXr, HARL, or task discovery
module and uses no sleep-based race.

## B0 regression results

~~~text
I4 terminal handoff pure                  16/16 passed
I4 environment integration static         12/12 passed
I3 staged pre-reset facts adapter          16/16 passed
I2 runtime domain capabilities             12/12 passed
I1 episode rebuild                         12/12 passed
B0-2 lifecycle authority transaction       18/18 passed
B0-1A execution facts producer              9/9 passed
B0-1B generation clock                     12/12 passed
                                                ---
                                               107/107 passed
~~~

No I4 runtime smoke was run because B1 changes no production environment route
and the authorization explicitly excludes Isaac/AppLauncher.

## Frozen Phase-A and contract regressions

~~~text
lifecycle transition contract              12/12 passed
assignment profile contract                16/16 passed
event-profile schema                        9/9 passed
Phase-A default-off identity               16/16 passed
profile production wiring                  10/10 passed
event-gated MRTA contract                  13/13 passed
                                                ---
                                                76/76 passed
~~~

## Frozen hashes

~~~text
assignment_lifecycle_transition_contract.py
  1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9

assignment_event_contract.py
  22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A

assignment_profile_contract.py
  ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500

assignment_event_profile_schema_contract.py
  04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF
~~~

All four match B1 preflight exactly.

Production boundary hashes also match preflight:

~~~text
scan_mobile_manipulator_env.py
  030EFB1BE030C6F1BB22BB2DCF5918D0235305CB5D543D01569C1066836501D5

assignment_harl_wrapper.py
  DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A
~~~

## Other verification

~~~text
interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

py_compile:
  7 changed/new implementation and pure-runner files passed

production no-wiring search:
  passed

capability surface audit:
  passed

public export audit:
  passed; B1 module __all__ is empty

forbidden runtime symbol audit:
  no TASK_CLAIMED
  no AssignmentGenerationClock / assignment tick
  no claim-window implementation

trailing whitespace:
  passed

git diff --check:
  passed; pre-existing line-ending warnings only

HEAD/index:
  unchanged / empty
~~~

## Deferred and unresolved

The following remain deliberately absent:

~~~text
production environment assignment port
inter-step claim-window fence
scheduler/opportunity cadence
resolver arbitration
policy proposal/log-probability
Top-K/local sets/cost/masks/DVM
transfer/preemption/swap/chain/cycle
CLAIMED -> NAVIGATING -> ALIGNING progression
wrapper/HARL transport
runtime-ready activation
terminal optional sidecar
checkpoint-ready V3
Transformer/Set Transformer/GNN/variable cardinality
training/playback/evaluation
~~~

The eleven numeric TBD values remain unresolved and unchanged.

## Next gate

Phase B1 pure/default-off implementation is complete and awaits GPT/user
review. This report does not authorize production claim-window work,
environment assignment wiring, scheduler/resolver/policy work, wrapper/HARL,
runtime-ready activation, Isaac smoke, training, playback, evaluation, or a
commit.

