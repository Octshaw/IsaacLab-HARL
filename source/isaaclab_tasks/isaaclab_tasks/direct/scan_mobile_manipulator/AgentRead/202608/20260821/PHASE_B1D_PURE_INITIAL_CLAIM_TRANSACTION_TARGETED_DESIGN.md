# Phase B1D Pure Initial-Claim Transaction Targeted Design

## Classification

~~~text
classification:
  PHASE-B1D-PURE-INITIAL-CLAIM-TRANSACTION-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

B0:
  CLOSED

Phase-B entry:
  CONDITIONAL PASS
  targeted design condition satisfied
  implementation still requires explicit authorization

post-assignment provenance:
  FROZEN

current publication architecture:
  P2 / B-private discriminated full-domain publication aggregate
  FROZEN

baseline source kinds:
  FINALIZED_LIFECYCLE_TRANSITION
  CANONICAL_EPISODE_RESET
  POST_ASSIGNMENT
  FROZEN

independent assignment tick clock:
  NOT REQUIRED

terminal-slot gating:
  G2 / per-environment-row block
  FROZEN

first transaction granularity:
  C2 / batched independent non-conflicting claims
  FROZEN

assignment authority ownership:
  existing coordinator remains sole writer/order owner
  separate pure assignment deriver has no writer capability
  FROZEN

StateStore:
  one existing retained identity

publication lock:
  one existing coordinator boundary

request/effective separation:
  FROZEN

consume-once semantics:
  FROZEN

StateStore/publication atomicity:
  FROZEN

frozen Phase-A/B0 contract changes:
  none

environment/wrapper/HARL wiring:
  none

runtime readiness:
  interface_only / blocked

numeric TBD:
  unresolved

implementation:
  none

training/playback/evaluation:
  not run

commit:
  none
~~~

This is a targeted design-only closeout. It authorizes no Python, test, runtime,
environment, wrapper, resolver, HARL, profile-gate, checkpoint, training, or
simulation change. B0 remains closed.

No B1D provenance, publication-authority, bootstrap-generation, terminal
dependency, frozen-contract, or scope-expansion STOP condition was reached.

## Authority and evidence basis

This design retains the exact B0 authority split:

~~~text
LifecycleAuthorityRuntime
  sole execution-lifecycle semantic authority

LifecycleStateStore
  sole stored task/robot/ownership/failure/count/reason truth

LifecycleAuthorityTransactionCoordinator
  sole StateStore writer-capability holder
  sole transaction/publication/poison ordering owner

retained EventProfileLifecycleRuntimeDomain
  sole live composition root
  sole narrow-port distributor

future B1 initial-claim deriver
  assignment-owned candidate semantics only
  no lifecycle authority stamp
  no StateStore/publication capability
~~~

The current runtime already supplies:

- one retained domain and one operation lock;
- one StateStore identity and global version;
- one coordinator publication lock;
- immutable PublishedLifecycleView state/generation snapshots;
- exact terminal slots and designated acknowledgement;
- canonical reset publications whose result is absent;
- exact lifecycle transition publications whose result is finalized;
- writer-capability-only prepared StateStore swaps;
- poison-on-impossible-post-swap failure semantics.

The frozen B0-2D separation already permits a later typed post-a0 assignment
commit that changes only ownership, claim state, robot assignment state, and
their inverse. B0-2D-R C1 independently requires rejection of every cumulative
failed pair. No frozen contract field is missing for the initial claim.

## Final verdict table

| Question | Selected verdict | Permanent or slice-local |
|---|---|---|
| Post-assignment current publication | P2, one discriminated full-domain aggregate with per-row provenance | permanent B-private current-publication model |
| Legal source baselines | transition, reset, post-assignment | permanent for this claim family |
| Independent assignment tick clock | NOT REQUIRED | permanent for initial-claim transaction identity |
| Terminal-slot gating | G2, selected env row blocked by its own occupied slot | permanent for initial-claim route; not a rewrite of R3 |
| Transaction granularity | C2 batched independent claims | first implementation |
| Claim representation | selected env IDs plus dense task-per-robot rows with NO_CLAIM sentinel | first implementation |
| Maximum claims per env | at most min(M,N), with unique robots and tasks | structural |
| Empty transaction | invalid | first implementation |
| Empty selected row | invalid; omit that env from selected IDs | first implementation |
| Invalid selected row/pair | reject the whole selected batch | first implementation |
| StateStore version | global version plus one exactly once on success | permanent |
| Episode/physical transition generation | unchanged | permanent |
| Assignment authority | pure deriver plus existing coordinator private route | permanent responsibility split |
| Request identity | opaque single-use request context/token | permanent |
| Proposal versus effective | always separate | permanent |
| Lifecycle event for claim | none | first claim semantics; frozen enum unchanged |

## Q1 verdict: select P2

### Why P2 is selected

P2 introduces one B-private discriminated current-publication aggregate. It is
not a second StateStore and not a second current-state truth. The aggregate is
the only fresh current-read artifact and is installed under the existing
coordinator publication lock after the one StateStore swap.

Conceptual role:

~~~text
_EventRuntimeCurrentPublication
  exact full-domain PublishedLifecycleView state/generation projection
  exact opaque publication identity
  per-env immutable provenance entry
~~~

The nested PublishedLifecycleView remains the canonical no-alias state and
generation projection. For an assignment publication its result is absent,
because a historical LifecycleTransitionResult cannot match post-assignment
ownership/task/robot state. The outer discriminator supplies provenance rather
than asking callers to infer provenance from result absence.

### Per-row provenance is required

A full-domain publication cannot use only one global source kind. Partial
episode rebuild and selected-row assignment commit can leave different rows at
different semantic origins. The aggregate therefore carries exactly one
provenance entry per retained env row.

Conceptual exact variants:

~~~text
PREBOOTSTRAP
  construction-only
  episode_generation == -1
  never a legal assignment source

FINALIZED_LIFECYCLE_TRANSITION
  exact finalized LifecycleTransitionResult
  row ownership derives from finalized a0

CANONICAL_EPISODE_RESET
  result absent by design
  exact reset publication installed by episode rebuild

ASSIGNMENT_COMMIT
  exact EffectiveAssignmentCommitArtifact
  exact immediate source publication identity
  exact root lifecycle/reset provenance
~~~

PREBOOTSTRAP is a publication variant but not one of the three legal assignment
source kinds. Legal assignment source kinds are:

~~~text
FINALIZED_LIFECYCLE_TRANSITION
CANONICAL_EPISODE_RESET
POST_ASSIGNMENT
~~~

POST_ASSIGNMENT is the source-baseline name corresponding to an
ASSIGNMENT_COMMIT current-publication row.

### Why P1 is rejected

P1 would publish a new PublishedLifecycleView with result absent and place the
assignment artifact elsewhere. Reset and assignment publications would then be
indistinguishable through the current-read artifact. A second lookup or side
registry would be required to recover provenance, creating either an
ambiguous source or two independently read current authorities.

Adding an external discriminator beside P1 would effectively recreate P2.
P1 is therefore not the minimal complete model.

### Why no alternative P3 is needed

The existing StateStore, PublishedLifecycleView, and publication lock already
supply the state and atomicity substrate. P2 adds only a B-private provenance
envelope and does not require a new public/frozen schema.

## Exact current reader contract

The retained domain evolves its B-private current-read port to return the exact
current publication aggregate under the existing coordinator publication lock.

A fresh read returns one immutable object containing:

- the exact full-domain state snapshot;
- exact store version;
- exact episode-generation vector;
- exact physical-transition-generation vector;
- exact per-row source kind;
- exact per-row provenance reference;
- derived terminal projection already carried by the nested lifecycle view.

Tensor accessors remain detached/no-alias. Retained older publications are
coherent historical artifacts, never fresh-current capabilities.

The current reader does not return:

- StateStore or a raw snapshot capability;
- clock or clock snapshot capability;
- writer capability or publication lock;
- request allocator/consume state;
- assignment coordinator/deriver;
- mutable provenance storage.

## Provenance identification and chaining

### Reset baseline

A reset baseline is identified only by an exact per-row
CANONICAL_EPISODE_RESET provenance installed by the episode-rebuild route.

It is not inferred from:

~~~text
view.result is None
task state happens to be AVAILABLE
ownership happens to be -1
~~~

The row must also be nonterminal, episode generation nonnegative, and match the
exact current StateStore state/version.

### Lifecycle-transition baseline

A transition baseline is identified only by an exact per-row
FINALIZED_LIFECYCLE_TRANSITION provenance. It retains the exact canonical
LifecycleTransitionResult. The row state, generation, reason, and ownership
must match that result, and its source baseline ownership is the finalized a0.

### Post-assignment baseline

A post-assignment baseline is identified only by an exact per-row
ASSIGNMENT_COMMIT provenance. It retains the exact preceding
EffectiveAssignmentCommitArtifact and the current assignment-owned projection.

It never reconstructs provenance from result absence.

### Consecutive commits

Every successful assignment publication binds:

- the immediate source aggregate identity;
- each selected row's immediate source provenance;
- the root origin kind, transition or reset;
- the exact root LifecycleTransitionResult when the root is a transition;
- the exact prior assignment artifact when the immediate source is
  post-assignment;
- the source and committed StateStore versions.

A second claim captures the new current aggregate, produces a new request
context, and commits from POST_ASSIGNMENT. The previous artifact remains
immutable. Unselected row provenance is copied exactly into the replacement
aggregate.

The first implementation may retain the exact immediate prior artifact object
and root provenance in the new immutable artifact. Long-run archival or
compaction policy is outside this pure initial-claim slice; it cannot alter
current-source identity or historical lifecycle-result immutability.

### Historical lifecycle result

A lifecycle result is never patched, regenerated, or attached as the matching
result of post-assignment state. It remains reachable through transition-root
provenance and through every descendant effective assignment artifact.

### Later physical transition

I3 continues to capture task/robot/ownership state directly from the one
StateStore under the coordinator boundary. It does not need to understand an
assignment artifact to see post-assignment ownership.

When the physical transition finalizes, the resulting current row provenance
becomes FINALIZED_LIFECYCLE_TRANSITION with its new exact result. The prior
assignment publication remains an immutable predecessor artifact; it does not
become lifecycle result content.

## B-private assignment source baseline

The conceptual AssignmentSourceBaseline is factory-only and cannot be directly
constructed by environment, resolver, or caller.

The retained domain/coordinator captures it under the publication lock from the
exact current aggregate. It binds:

~~~text
exact canonical resolved profile object
exact retained domain identity
exact current aggregate object identity
exact current aggregate opaque publication identity
exact StateStore identity
exact source global store version
selected env IDs and domain-row order
episode generations
physical transition generations
task state
robot state
source ownership
cumulative failed pairs
completion count
termination reason
per-row source kind
per-row immediate provenance
per-row root provenance
~~~

Source-specific bindings:

~~~text
transition:
  exact finalized LifecycleTransitionResult
  source ownership == result.updated_ownership == a0

reset:
  result absent
  exact CANONICAL_EPISODE_RESET provenance

post-assignment:
  exact prior EffectiveAssignmentCommitArtifact
  current ownership/task/robot projection from that publication
~~~

Every tensor is captured/no-alias. Source kind uses a private exact enum or
sealed variant, never a raw string supplied by the caller.

A baseline becomes stale if current aggregate identity, Store identity/version,
episode generation, transition generation, or any bound selected-row state
differs.

## Canonical reset and transition generation minus one

The first episode reset legally yields:

~~~text
episode_generation == 0
physical transition_generation == -1
result == None
robot state == NEEDS_ASSIGNMENT
~~~

The B-private baseline/request protocol accepts exact transition generation
minus one only for:

- a canonical reset source before any physical transition; or
- a post-assignment source descended from that canonical reset while the
  physical transition generation remains minus one.

It never fabricates transition zero, facts, receipt, lifecycle result, or event.

A finalized lifecycle-transition source always has nonnegative episode and
transition generation.

The initial claim protocol does not instantiate Phase-A LocalSetRequest,
LocalSetResult, ProposalSnapshot, TransferComponentRequest, or
TransferComponentResult. Those frozen DTOs require nonnegative transition and
assignment-tick generations.

If later policy sampling must use those DTOs before the first physical
transition, that future phase must STOP for a targeted generation-contract
review. B1D does not weaken or reinterpret their validation.

## Q2 verdict: no independent assignment tick clock

~~~text
independent assignment tick clock:
  NOT REQUIRED
~~~

### Exact rationale

The initial-claim transaction is uniquely bound by the conjunction of:

~~~text
exact current aggregate identity
exact StateStore identity and global version
exact selected env IDs
exact episode generations
exact physical transition generations
exact immutable source baseline
exact opaque request context identity
single-use request token/capability
~~~

A successful claim necessarily changes the Store version and aggregate
identity. Replaying the request is therefore both consumed and stale.
Unrelated successful StateStore mutation also makes the exact global source
version stale. There is no successful no-op transaction that could reuse the
same state/version.

An independent clock would add a third generation family before its semantic
owner exists. It would also risk conflating:

- scheduler assignment opportunity;
- deterministic transaction request;
- committed assignment batch.

These are not the same concept. The initial-claim transaction needs the latter
two identities only.

### Request identity and consume-once semantics

The retained domain/coordinator owns a private process/domain-lifetime monotonic
request-token allocator. Tokens are never reset or reused. Gaps are legal.

An opaque immutable request context binds one token to:

- exact source baseline identity;
- exact selected env IDs;
- exact requested pair tensor identity/content;
- exact domain/profile identity.

The coordinator retains the authoritative issued/consumed capability state.
The request object carries no writer or ledger capability.

Semantics:

~~~text
context issuance:
  allocates a unique token
  does not mutate StateStore/publication/generation

ordinary validation rejection:
  does not consume the context
  does not mutate or poison

successful commit:
  consumes exactly that context once in the no-fail success tail

successful replay:
  impossible; consumed and stale

unexpected post-swap failure:
  coordinator/domain poisoned
  no retry, rollback, second consume, or fresh read
~~~

Keeping a context unconsumed after ordinary rejection permits a transient G2
terminal fence to clear and the exact still-current request to be retried. An
immutable semantically invalid or stale request remains invalid. No cancellation
API is added in the first slice.

Multiple outstanding contexts may bind the same source publication. The shared
operation/publication locks serialize them. The first success changes the
global version/publication; every competing old-source context then rejects as
stale. No arbitration or runner-up selection occurs.

### Later scheduler identity

A future scheduler remains free to define assignment opportunity generation and
cadence under the frozen Phase-A scheduler contracts. That opportunity
generation is not this request token and is not a StateStore version.

When the scheduler is implemented, it may bind one opportunity to one or more
deterministic requests without changing B1 consume-once semantics. B1D therefore
does not pre-allocate, reset, or interpret the future assignment-tick clock.

## Q3 verdict: G2 per-env terminal fence

~~~text
terminal-slot gating:
  G2

rule:
  terminal slot occupied for env e
  -> no initial-claim commit for env e
  -> other env rows may commit
~~~

### Rationale

G2 preserves the causal boundary for one environment: the old episode terminal
artifact must be captured and acknowledged before the new episode receives an
assignment claim. It also preserves vector-environment independence and does
not turn the full-domain physical-step R3 rule into a global assignment rule.

The terminal artifact is keyed by old env/episode/transition generation and
remains historical. The current reset publication is keyed by the new episode.
P2 distinguishes both exactly, but G2 still enforces consumer-before-new-claim
ordering for the same env.

G1 is rejected because one unacknowledged terminal row would unnecessarily
prevent independent nonterminal rows from committing claims. The B0 StateStore
version is global, but that requires serialization and recapture, not semantic
global blocking.

G3 is rejected for the initial-claim route because it would allow new-episode
assignment progress before the designated consumer completes the old-episode
terminal boundary. Exact keys prevent data corruption, but they do not provide
the desired synchronous consumer ordering.

### Relationship to R3

R3 remains unchanged:

~~~text
any occupied terminal slot
-> no next physical step anywhere in the synchronous vector domain
~~~

G2 is an assignment-transaction rule, not a rewrite of R3.

### Selected-batch behavior

The assignment coordinator checks terminal occupancy for every selected env row
under the publication lock. If any selected row is occupied, the whole selected
assignment batch rejects receipt-free/no-mutation. The caller may construct a
new request omitting blocked rows. There is no partial success inside one
request.

For env e after terminal autoreset:

~~~text
old terminal artifact unacknowledged:
  claim forbidden for e

exact terminal ack completed:
  a newly captured current reset baseline may claim for e
~~~

This is frozen for the initial-claim route. A later transfer route must inherit
it or explicitly request a targeted semantic review.

## Q4 verdict: C2 batched independent claims

~~~text
first B1 implementation:
  C2

transaction:
  each selected env has one or more independent pairs;
  a selected env with zero pairs is not allowed

maximum claims per selected env:
  min(M,N)

arbitration:
  none
~~~

### Exact request representation

The first implementation uses:

~~~text
selected_env_ids:          [K] int64, nonempty, unique
requested_task_by_robot:   [K,M] int64
NO_CLAIM sentinel:         -1
legal task IDs:            0..N-1
~~~

Every selected env row must contain at least one non-sentinel claim. An env with
no claim is omitted from selected_env_ids. The entire transaction must contain
at least one pair.

This is a B-private deterministic transaction input, not the fixed policy
action DTO and not a Phase-A proposal/local-set/component DTO.

One task slot per robot structurally prevents one robot from requesting two
tasks. Validation rejects duplicate non-sentinel task IDs within an env row.
It also rejects duplicate selected env IDs, invalid task IDs, wrong
shape/dtype/device, aliases that violate capture rules, and any pair that is not
independently legal.

### Why C2 is selected

C2 assigns multiple initially idle robots in one atomic batch without requiring
M sequential Store-version changes and provenance hops. It still supports a
later POST_ASSIGNMENT request when initial work was intentionally incomplete or
newly available.

C2 is not a resolver:

- all pairs are caller-supplied;
- pairs must already be nonconflicting;
- no contender wins;
- no alternate task is chosen;
- no optimization, cost, ranking, or matching occurs;
- one invalid pair rejects the whole transaction.

C1 is rejected as the first implementation granularity because it adds
unnecessary sequential publication/version churn for the ordinary multi-robot
initial assignment while providing no stronger semantic guarantee.

## Initial claim request contract

The conceptual InitialClaimRequest is immutable, factory-only, B-private, and
no-alias. It binds:

~~~text
exact AssignmentSourceBaseline object identity
exact opaque request context identity/token
selected_env_ids [K]
requested_task_by_robot [K,M]
NO_CLAIM == -1
~~~

It excludes:

~~~text
policy action or log probability
proposal probability
Top-K/local set
cost/path estimator
mask or DVM
preemption/transfer
PPO/HARL metadata
lifecycle facts/result/events
writer/coordinator/lock capability
~~~

The request is deterministic transaction input. It is not a policy proposal.

The factory captures and validates tensor dtype, rank, shape, device,
contiguity, no-grad, IDs, sentinel domain, and source/domain identity. Caller
mutation cannot alter the request or source baseline.

## Exact claim legality

For every requested pair (e,i,j), the exact source must satisfy:

~~~text
termination_reason[e] == NONE
published terminated[e] == false
published truncated[e] == false
robot_state[e,i] == NEEDS_ASSIGNMENT
robot i is not UNAVAILABLE
robot i owns no active task
task_state[e,j] == AVAILABLE
ownership[e,j] == -1
cumulative_failed_pairs[e,i,j] == false
task j is not COMPLETED
task j is not TEAM_INFEASIBLE
terminal slot for env e is empty under G2
~~~

The whole source prestate must already satisfy the frozen task/robot/ownership,
TEAM, C1, count, reason, profile, domain, generation, device, and enum
invariants.

The whole candidate must satisfy:

~~~text
one robot owns at most one active task
one task has at most one owner
every active task has one exact owner
EXECUTING iff one active task is owned
healthy unowned robot projection is exact
UNAVAILABLE owns nothing
completed/TEAM states and ownership are unchanged
failed pairs/count/reason are unchanged
~~~

No path, cost, Top-K, cooldown, budget, retry cadence, or policy value affects
legality.

## Assignment-owned poststate derivation

For each requested pair:

~~~text
task_state[e,j] = CLAIMED
ownership[e,j] = i
~~~

All other task state and ownership entries remain exact.

Robot state is then recomputed for every robot in each selected env using the
frozen structural projection:

~~~text
if prior robot is UNAVAILABLE:
  robot1 = UNAVAILABLE
elif robot owns exactly one active task after claims:
  robot1 = EXECUTING
elif exists unowned AVAILABLE task j
     with cumulative_failed_pairs[i,j] == false:
  robot1 = NEEDS_ASSIGNMENT
else:
  robot1 = WAITING_FOR_TASK
~~~

Thus each claimant becomes EXECUTING. A healthy unclaimed peer remains
NEEDS_ASSIGNMENT only while structurally eligible unowned work remains;
otherwise it becomes WAITING_FOR_TASK.

For every selected and unselected row, these fields remain bit-exact:

~~~text
cumulative_failed_pairs
completion_count
termination_reason
episode_generation
physical transition_generation
lifecycle result/history/events/facts/receipts
terminal slots
~~~

Every unselected environment row's task/robot/ownership tensors are also
bit-exact.

## EffectiveAssignmentCommitArtifact

The successful artifact is immutable, factory-only, no-alias, and B-private. It
binds:

~~~text
exact canonical profile/domain identity
exact request object identity
exact request token/context identity
exact source publication object/opaque identity
exact source per-row kinds
exact source global StateStore version
exact committed global StateStore version
selected env IDs
unchanged episode generations
unchanged physical transition generations
requested task-per-robot rows
committed effective task-per-robot rows
pre-assignment task/robot/ownership projection
post-assignment task/robot/ownership projection
exact immediate predecessor provenance
exact root transition/reset provenance
exact source LifecycleTransitionResult when the root is a transition
~~~

For this conflict-free first slice, requested and effective pair values are
equal after success, but they remain separate captured fields and objects.
Future resolver acceptance/rejection must not overwrite the request.

The artifact holds no StateStore, clock, ledger, coordinator, deriver, lock,
writer capability, mutable registry, or policy buffer.

Failure creates no effective artifact.

## No-op, version, and mixed-batch rules

### No-op

A fully empty transaction is invalid. A selected env row containing only
NO_CLAIM is invalid. No successful no-op exists.

Therefore every successful transaction changes at least one
AVAILABLE/NEEDS_ASSIGNMENT pair and increments the global Store version.

### Version and generations

On success:

~~~text
StateStore global version:
  +1 exactly once

episode generations:
  unchanged for all rows

physical transition generations:
  unchanged for all rows

unselected env state:
  bit-exact
~~~

One or multiple claims do not change the version delta.

### Mixed-batch atomicity

All selected rows and pairs form one transaction. Any invalid selected row,
pair, duplicate task, stale source, occupied G2 slot, or consumed context
rejects the whole batch before StateStore mutation, request consume, artifact
installation, or publication.

Partial successful rows are forbidden.

## Assignment authority and capability ownership

### Selected architecture

The existing LifecycleAuthorityTransactionCoordinator is extended later with a
private initial-claim transaction route. It remains the sole holder of:

- StateStore writer capability;
- publication lock;
- current publication pointer;
- poison state;
- terminal-slot storage/capability checks.

StateStore is extended later only with a typed private
prepare-initial-claim-replacement route. That route validates the exact old
state/version and the assignment-owned field delta, prepares one version-plus-
one replacement, and returns a capability-bound swap. It is not a generic
setter and cannot alter lifecycle-owned fields or generations.

A separate pure B-private InitialClaimDeriver may validate and derive the
assignment-owned candidate. It has no lifecycle authority stamp, ledger,
StateStore writer, publication capability, terminal consumer, or clock writer.

This selects coordinator model C, with a pure helper. It rejects:

- reusing LifecycleAuthorityRuntime for policy/assignment choice;
- creating an independent AssignmentCoordinator with a second lock or writer;
- granting resolver/environment direct StateStore access.

### Retained domain ownership

The retained EventProfileLifecycleRuntimeDomain owns:

~~~text
one InitialClaimDeriver
one private request-token allocator/consume registry
one narrow assignment-request port
the existing coordinator
the existing operation lock
one future inter-step assignment-window authority before production wiring
~~~

The future resolver receives only the narrow request port or an equivalent
factory/commit capability. The environment receives none of these assignment
capabilities in the first pure implementation.

The module remains B-private and default-off. No public package export or
runtime-ready gate changes.

## Locking and concurrency matrix

Lock order remains:

~~~text
retained domain operation lock
  -> coordinator publication lock
     -> StateStore internal lock
~~~

The assignment port takes the same domain operation lock already used by
physical-transition finalization and episode rebuild, then invokes the private
coordinator route. This serializes those three transactions, but it does not by
itself cover the earlier action/physics portion of a real environment step.

The first B1 implementation is pure, dormant, and has no environment assignment
port, so it has no real in-flight physics interval. Before any production
environment wiring is authorized, the environment/domain boundary must add an
opaque inter-step assignment-window capability with these semantics:

~~~text
open:
  only after the complete reset or step call, including finalization and any
  synchronous pre-reset/episode rebuild, has returned

revoke:
  atomically before admission of the next action/physics step

claim request:
  binds the exact currently-open window identity

claim commit:
  requires the same window still open and current
~~~

The capability is a phase/concurrency admission fence, not a scheduler
opportunity, cadence, generation clock, or assignment tick. No numeric cadence
or retry rule is introduced. Production activation remains blocked until that
capability is designed and integrated with the real step-admission boundary.

Terminal read/ack and current read use the coordinator publication lock only
and never acquire the operation lock in reverse.

| Interaction | Rule |
|---|---|
| assignment vs physical-transition finalization | operation lock serializes; assignment first means the next I3 prestate sees the claim, finalization first makes the old request stale |
| assignment vs in-flight action/physics | impossible in pure dormant B1; future production wiring must require the exact open inter-step window and revoke it before step admission |
| assignment vs episode rebuild | operation lock serializes; rebuild first invalidates source/version/generation, assignment first may later be reset normally |
| assignment vs terminal ack | publication lock serializes; G2 is rechecked at commit; ack first may unblock exact still-current request |
| assignment vs current read | publication lock serializes; reader sees coherent old or coherent new aggregate |
| assignment vs assignment | operation/publication locks serialize; first success makes every old-source competing request stale |
| assignment vs poison | poison guard rejects before any fresh baseline/read/commit |
| assignment vs terminal slot on other env | G2 permits the selected nonblocked env transaction; R3 still blocks the next physical step globally |

A source baseline captured and then superseded by any StateStore/publication
operation is stale. It is never rebased or interpreted against new state.

## Exact transaction order

The private route executes while holding the domain operation lock and then the
coordinator publication lock:

~~~text
1.  poison and exact profile/domain/capability guard; when production-wired,
    require the exact current open inter-step window
2.  capture the exact current discriminated publication aggregate
3.  capture writer-capability StateStore snapshot
4.  prove aggregate/state/version/generation equality
5.  validate exact source baseline and current object identity
6.  apply G2 selected-row terminal-slot check
7.  validate exact request context/token and request tensor contract
8.  validate every source row and claim pair
9.  derive the full-domain assignment-owned poststate without mutation
10. validate every poststate invariant and unchanged field
11. prepare the complete version+1 StateStore replacement
12. prepare nested result-absent PublishedLifecycleView for new state
13. prepare EffectiveAssignmentCommitArtifact
14. prepare replacement per-row provenance and full current aggregate
15. prepare the one-use request consume replacement
16. revalidate StateStore/current aggregate/generations/G2/context and, when
    production-wired, the exact inter-step window
17. enter the no-fail success tail
18. commit one prepared StateStore pointer swap
19. commit the prepared request-consumed marker
20. install the prepared current publication aggregate/effective artifact
21. return the immutable artifact and release locks
~~~

The physical generation clock is not advanced or called by this route.

## Precise no-fail tail and publication atomicity

Every tensor clone, validation, artifact allocation, provenance merge, version
overflow check, token check, and terminal-slot check completes before step 17.

The success tail consists only of prevalidated identity checks and pointer/state
swaps:

~~~text
StateStore prepared swap
-> request-consumed prepared swap
-> current publication prepared pointer install
~~~

The coordinator publication lock prevents all fresh readers, terminal
operations, and other assignment/lifecycle transactions from observing between
these operations. The domain operation lock additionally prevents physical
finalization or rebuild interleaving. It does not claim to lock the whole real
physics step; that safety property belongs to the required inter-step window.

Publication completion is the authoritative assignment-transaction success
boundary. The returned effective artifact is the exact artifact already
installed in the assignment row provenance.

No callback, logger, debug hook, environment hook, or external artifact may
observe the prepared state before publication.

## Failure and poison semantics

### Ordinary failure before success tail

Any stale, terminal-gated, duplicate, semantically invalid, wrong-domain,
wrong-device, overflow, or request-integrity failure before the StateStore swap
has:

~~~text
StateStore unchanged
publication unchanged
request context unconsumed
terminal slots unchanged
episode/transition generations unchanged
no effective artifact
no poison
~~~

The same exact context may be retried only if its immutable source is still
current and the blocking condition was transient. It cannot be corrected or
rebased.

### Unexpected failure after StateStore swap

The tail is designed to be no-fail. If an impossible failure occurs after the
Store swap:

~~~text
publish nothing further
mark coordinator/domain poisoned
permit no fresh current read or normal operation
do not roll back StateStore
do not unconsume/reconsume the request
do not retry
do not install a substitute artifact
require teardown
~~~

If failure occurs after the request marker but before publication, that marker
remains consumed and the runtime is poisoned. If it occurs before the marker,
the marker remains unconsumed but poison still forbids retry.

Already retained old immutable publications and historical artifacts remain
coherent data but cannot authorize runtime continuation.

## Lifecycle result and event boundary

Initial claim is not an execution lifecycle event. B1 adds no TASK_CLAIMED
LifecycleEvent, no causal-source enum, no event-record schema, and no fake
LifecycleTransitionResult.

A source LifecycleTransitionResult permanently retains its original
updated_ownership, task/robot state, reason, events, token, and receipt even
after current StateStore ownership changes.

The assignment artifact is the sole initial-claim history record. It does not
enter the lifecycle event tuple and cannot alter completion, release, failure,
TEAM, reason, counts, facts, receipts, terminal artifacts, or coverage/reward
evidence.

Ordinary CLAIMED to NAVIGATING to ALIGNING progression remains deferred.

## Future pure implementation test oracle

A separately authorized B1 implementation must freeze and pass at least:

1. B1-T1 canonical reset source success, including episode 0/transition -1;
2. B1-T2 finalized nonterminal lifecycle-transition source success;
3. B1-T3 POST_ASSIGNMENT second claim and exact provenance chain;
4. B1-T4 C2 multi-robot independent batch success;
5. B1-T5 unavailable/non-NEEDS_ASSIGNMENT robot rejection;
6. B1-T6 occupied/non-AVAILABLE/completed/TEAM task rejection;
7. B1-T7 cumulative failed-pair rejection;
8. B1-T8 duplicate task, duplicate env, invalid ID, and conflict rejection;
9. B1-T9 terminal row and G2 occupied selected-row rejection;
10. B1-T10 exact source object/Store version/episode/transition/state stale rejection;
11. B1-T11 request versus effective artifact separation and no-alias behavior;
12. B1-T12 assignment-owned-only state changes and exact robot projection;
13. B1-T13 historical LifecycleTransitionResult and terminal artifact identity;
14. B1-T14 publication reader old/old versus new/new atomicity;
15. B1-T15 injected post-swap failure poison with no rollback/retry/publication;
16. B1-T16 duplicate consume/replay rejection;
17. B1-T17 exact profile/default-off/no production wiring/no capability leak;
18. B1-T18 complete B0 and frozen Phase-A regression preservation;
19. B1-T19 no-op rejection, selected-batch atomicity, and version delta one;
20. B1-T20 operation-lock finalization/rebuild concurrency, pure-mode absence of
    an environment assignment port, and partial-row provenance preservation.

Any later environment-integration test plan must separately prove exact-window
issuance/revocation and rejection during in-flight action/physics before the
route may be activated.

Concurrency tests use bounded threading.Event interlocks, never sleep-based
races. Pure runners use namespace-only canonical loading and do not import
Isaac, AppLauncher, Omni, PXr, HARL, or task discovery.

## Deferred work

B1D does not design or authorize:

- policy proposal/log-probability storage;
- assignment scheduler/opportunity generation or retry cadence;
- Top-K, local sets, cost, masks, or DVM;
- conflict arbitration, matching, runner-up choice, or optimizer;
- preemption, transfer, swap, chain, or cycle;
- CLAIMED to NAVIGATING to ALIGNING progression;
- environment, wrapper, resolver, controller, or HARL wiring;
- terminal consumer integration or real terminal Isaac smoke;
- reward, sidecar, buffer, GAE, proper-time-limit, or learner semantics;
- profile readiness activation;
- checkpoint-ready V3;
- training, playback, evaluation, or performance work.

All eleven numeric TBD values remain unresolved and unnecessary:

~~~text
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
~~~

Transformer, Set Transformer, GNN, arbitrary-cardinality policy, variable
robot/task checkpoint, and variable-cardinality work remain forbidden.

## STOP-condition audit

| STOP condition | Result | Rationale |
|---|---|---|
| B1D assignment provenance gap | not triggered | P2 distinguishes reset, transition, and post-assignment per row |
| Current-publication authority gap | not triggered | one StateStore, one wrapper aggregate, one publication lock |
| Bootstrap generation gap | not triggered | B-private reset/post-assignment source accepts exact transition -1 |
| Phase-B terminal dependency gap | not triggered | G2 uses existing terminal slots; no wrapper/HARL capability is needed |
| Frozen-contract gap | not triggered | all new roles are B-private; frozen DTOs/enums unchanged |
| Scope expansion required | not triggered | C2 legality needs no scheduler, cost, policy, resolver, or HARL route |

## Documentation-only repository boundary

The authorized B1D delta is limited to:

~~~text
AgentRead/202608/20260821/PHASE_B1D_PURE_INITIAL_CLAIM_TRANSACTION_TARGETED_DESIGN.md
AgentRead/TASK_PROGRESS.md
~~~

No TASK_PROGRESS archive is required: the current handoff is within the
AGENTS.md target and can be updated in place without losing linked B0 history.

No Python, test, frozen contract, environment, wrapper, runtime domain,
lifecycle runtime, authority, resolver, HARL, profile/readiness, checkpoint,
configuration, installed-package, training, playback, evaluation, or commit
change is authorized.

## Next gate

This targeted design is complete and awaits GPT/user review. A later phase may
authorize a pure/default-off B1 implementation and its dedicated runner.

That later authorization must name the code/test scope explicitly. This
document does not authorize implementation, production wiring, runtime-ready
activation, or any further phase.
