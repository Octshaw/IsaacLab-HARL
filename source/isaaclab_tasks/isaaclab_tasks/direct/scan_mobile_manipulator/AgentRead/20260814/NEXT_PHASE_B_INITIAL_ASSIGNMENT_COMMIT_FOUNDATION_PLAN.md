# Next Phase B Initial Assignment Commit Foundation Plan

## Status

~~~text
document type:
  DESIGN-ONLY NEXT-PHASE PLAN

recommended next phase:
  Phase B1D — Pure Assignment-Tick and Initial Claim Commit Transaction Design

Phase-B entry gate:
  PHASE-B-ENTRY-CONDITIONAL-PASS

implementation authorization:
  none

runtime wiring authorization:
  none

event-profile runtime readiness:
  unchanged / blocked

training/playback/evaluation:
  unauthorized

numeric selection:
  none

commit:
  none
~~~

This plan accompanies
PHASE_B0_LIFECYCLE_FOUNDATION_CLOSEOUT_AND_PHASE_B_READINESS_REVIEW.md.
It is not an implementation authorization and does not reopen B0.

## Why targeted design comes before code

The B0 foundation already supplies the semantic baseline, StateStore,
publication lock, episode/transition generations, and default-off composition.
Two Phase-B-specific choices are intentionally not frozen yet:

1. Initial assignment must work from a canonical episode-reset publication,
   where the lifecycle result is absent by design, as well as from a finalized
   nonterminal transition a0.
2. After assignment changes live ownership/task/robot state, the historical
   lifecycle result no longer matches the new current state and cannot remain
   attached as that state's result. Phase B needs a distinct immutable commit
   artifact and exact current-publication semantics.

These are Phase-B transaction and publication questions. They do not require a
new lifecycle fact, a Phase-A schema revision, a terminal HARL consumer, or a
second StateStore. They must nevertheless be resolved in a targeted design
before code is safe.

## Goal of the first slice

Prove one assignment-owned state transition:

~~~text
healthy NEEDS_ASSIGNMENT robot
+ AVAILABLE task
+ owner == -1
+ cumulative_failed_pair == false
+ exact nonterminal source baseline
+ exact version/generation binding
-> one immutable staged claim
-> atomic assignment-owned state commit
-> one immutable effective-assignment artifact
~~~

Expected poststate for the selected pair:

~~~text
task_state:   AVAILABLE -> CLAIMED
ownership:    -1 -> robot_id
robot_state:  NEEDS_ASSIGNMENT -> EXECUTING
~~~

Everything outside the assignment-owned projection remains bit-exact.

## Existing B0 capabilities to reuse

The design must reuse, not duplicate:

- the exact resolved event-gated profile identity;
- the retained event-profile lifecycle runtime domain;
- the single LifecycleStateStore identity and version;
- the coordinator publication lock and poison boundary;
- immutable lifecycle snapshots and current publication reads;
- episode and transition generations;
- the C1 failed-owner invariant and all poststate inverse invariants;
- terminal slot/R3 capability checks;
- default-off route separation.

The environment, wrapper, resolver, and policy must not receive StateStore,
clock, ledger, factory, or lifecycle-authority writer capabilities.

## Source baseline model to freeze

The design needs one B-private assignment baseline discriminated by source
kind. Candidate names below are descriptive, not yet authorized API names.

### Transition baseline

~~~text
source kind:             FINALIZED_LIFECYCLE_TRANSITION
source current view:     exact immutable object
source result:           exact finalized LifecycleTransitionResult
source_baseline_ownership: result.updated_ownership, the finalized a0
reason:                  NONE
terminal slot:           absent everywhere in the retained vector domain
~~~

The result task/robot/ownership/failure/reason tensors must exactly match the
source view, as B0 already requires.

### Episode-reset baseline

~~~text
source kind:             CANONICAL_EPISODE_RESET
source current view:     exact immutable object
source result:           None by design
source_baseline_ownership: source lifecycle_state.ownership, not an a0
reason:                  NONE
terminal slot:           absent everywhere in the retained vector domain
~~~

The reset source must satisfy the I1 reset equations. Phase B must not create a
fake transition generation, token, receipt, reason, event, or lifecycle result
to make the reset look like a transition.

### Common binding

Both source kinds must bind:

~~~text
exact resolved profile/domain identity
exact current publication identity
exact StateStore identity and store_version
env_id set and row order
episode_generation
transition_generation
baseline task_state
baseline robot_state
source_baseline_ownership; this is a0 only for a transition source
cumulative_failed_pairs
termination_reason
~~~

A request built from one source kind cannot be replayed against the other.
For the canonical reset source, `transition_generation` may still be the B0
initial sentinel `-1` because no physical transition has occurred. The B1
private bootstrap protocol must bind that exact value; it must not fabricate
transition `0`.

## Candidate B-private artifacts

The targeted design should freeze the smallest private protocol, likely with
three immutable/no-alias roles:

1. Initial claim request
   - exact source-baseline binding;
   - selected env ID, robot ID, and task ID;
   - assignment-tick generation and a distinct consume-once capability;
   - no policy log-prob, cost, Top-K, mask, or transfer payload.
2. Prepared claim candidate
   - transaction-private;
   - exact request/source identity;
   - fully derived replacement state and effective pair;
   - no public mutation/finalization capability.
3. Effective assignment commit artifact
   - immutable;
   - distinguishes requested pair from committed pair;
   - binds source publication/version and committed StateStore version;
   - binds unchanged episode/transition generations;
   - binds the immutable source publication and, for a transition source, its
     exact lifecycle result without rewriting either;
   - exposes no StateStore, clock, or coordinator capability.

Assignment-tick generation and consume-once protection are separate
requirements. B1D must freeze a per-env process-lifetime tick clock whose
committed value begins at `-1`, whose first candidate/commit is `0`, and which
does not reset at episode rebuild. A separate private token/context must prove
single use. Store version rejects stale state, but it is not a substitute for
either tick generation or consume-once identity.

Existing Phase-A A3 proposal/local-set/component DTOs reject a negative source
transition generation. The private bootstrap-claim protocol must therefore not
instantiate those DTOs while the canonical reset source still has transition
`-1`. If a later initial policy tick requires those frozen DTOs before the
first physical transition, B1D must STOP for a targeted generation-contract
review rather than forge a transition or weaken validation.

No new Phase-A public DTO, checkpoint field, event type, termination reason, or
frozen lifecycle contract is presumed.

## Current-publication question

PublishedLifecycleView may carry no lifecycle result, and its factory requires
any attached result to match current task, robot, ownership, failed-pair,
reason, and generation tensors. Therefore attaching the pre-assignment
lifecycle result to post-assignment state is invalid.

B1D must select and prove one coherent option, for example:

- install a new current lifecycle-state publication with no attached lifecycle
  result and publish a separate assignment commit artifact that binds its
  immutable source lifecycle view; or
- introduce a B-private discriminated current-publication wrapper whose
  assignment variant carries the new state and separate assignment commit
  artifact while historical lifecycle results remain separate.

Selection criteria:

- one atomic current-read authority;
- no ambiguity between reset and assignment provenance;
- exact source and committed version/generation binding;
- no rewrite of LifecycleTransitionResult;
- no second StateStore or public writer;
- no change to Phase-A frozen profile schemas;
- compatibility with later scheduling and proposal/effective separation;
- default-off/no-wiring proof in the first implementation.

The option must be frozen during B1D. This plan does not silently choose it.

## Exact semantic validation for one claim

Before any mutation, the whole selected batch must prove:

- exact event profile and same retained runtime domain;
- exact source publication is still current;
- exact Store identity/version and exact episode/transition generations;
- source reason is NONE and selected rows are nonterminal;
- no occupied terminal slot exists anywhere in the retained vector domain;
- request IDs have exact type, domain, shape, uniqueness, and device rules;
- requested robot state is NEEDS_ASSIGNMENT and not UNAVAILABLE;
- requested robot owns no active task;
- requested task state is AVAILABLE and ownership is -1;
- requested pair is not cumulative failed;
- no robot receives more than one active task;
- no task receives more than one owner;
- task/robot/ownership inverse relations hold before and after the candidate;
- completed, TEAM, reason, failure, and counters are unchanged;
- every unselected environment row is bit-exact;
- within a selected environment, assignment-owned robot projection is exact:
  active owners are `EXECUTING`, `UNAVAILABLE` stays unavailable, and each
  healthy unowned peer is `NEEDS_ASSIGNMENT` iff eligible unowned `AVAILABLE`
  work remains for that robot, otherwise `WAITING_FOR_TASK`;
- the request has not already been consumed.

Any invalid row rejects the whole selected batch before a StateStore swap,
publication change, or consume-once success marker. The first slice performs
no repair, reassignment, retry, fallback, runner-up selection, partial commit,
or hidden optimization.

The no-outstanding-slot condition above is a conservative B1D scheduling rule,
not a retroactive expansion of B0 R3. Frozen R3 itself requires exact ack before
the next physical step. The initial slice deliberately also requires capture
and ack before any new-episode assignment commit.

## Transaction sequence to freeze

The design should preserve this order under the same external publication
lock:

~~~text
1. poison and runtime-capability guard
2. exact current source-publication capture
3. terminal-slot/R3 eligibility check
4. request and full-prestate validation
5. independent assignment equation/poststate prevalidation
6. prepare every replacement tensor and publication artifact
7. validate consume-once context and StateStore version again
8. perform one no-fail StateStore assignment-owned swap
9. commit the assignment consume-once identity as final internal success marker
10. install the coherent current publication and effective artifact
11. release the lock and return an immutable result
~~~

No observer may see a post-claim StateStore state with a pre-claim current
publication. Unexpected failure after the StateStore swap must poison the
composition and prevent fresh reads/continued execution; no rollback, retry,
second consume, or automatic repair is allowed. B1D must determine the precise
ordering of the StateStore swap, private success marker, and publication so all
ordinary failures occur before the no-fail tail.

Episode and physical transition generations remain unchanged by an assignment
tick. The StateStore version changes exactly once. A later physical transition
must capture the post-assignment ownership as its exact prestate.

## Proposal versus effective assignment

The first request is a deterministic test/runtime input, not yet a sampled
policy proposal. Even so, the protocol must preserve the future distinction:

~~~text
requested claim != effective assignment artifact
~~~

The effective artifact records only what was committed. It must never
overwrite a future PPO action/proposal buffer. Rejected input produces no
effective assignment. The first slice does not add accepted/rejected learning
semantics, policy sampling, log-probabilities, action masks, or DVM.

## Explicitly deferred from the first slice

- multiple contenders and conflict arbitration;
- switching, preemption, transfer chains, or cycles;
- component closure and component objectives;
- CLAIMED to NAVIGATING to ALIGNING runtime progression;
- scheduled retry cadence;
- local sets and owner expansion;
- Top-K and overflow policy;
- navigation/alignment cost estimators;
- proposal sampling and resolver integration;
- observations, action masks, and DVM;
- environment, wrapper, HARL, runner, or trainer wiring;
- reward, rollout buffer, critic sidecar, GAE, or proper-time-limit work;
- checkpoint and runtime-ready activation;
- real terminal or disturbance runtime work.

## Numeric and architecture boundary

The slice requires none of these values:

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

It also excludes Transformer, Set Transformer, GNN, variable robot/task count,
arbitrary-cardinality policy, and variable-cardinality checkpoint work.

## Proposed pure verification groups for a later implementation phase

The B1D design should define exact oracles for at least:

1. exact event-profile/default-off gate;
2. canonical reset-baseline claim success;
3. finalized nonterminal transition-baseline claim success;
4. request/effective artifact identity separation and no aliases;
5. failed-pair, terminal-task, unavailable-robot, and occupied-task rejection;
6. stale publication/version/episode/transition/source rejection;
7. duplicate request and consume-once rejection;
8. mixed-batch validation atomicity and unselected-row identity;
9. assignment-owned-only field changes and historical result immutability;
10. publication-lock reader atomicity around the success tail;
11. post-swap injected failure poison behavior;
12. default-off identity and no production wiring;
13. B0-1A/B0-1B/B0-2/I1-I4 regression preservation;
14. RNG, logger, filesystem, cwd, environment, registry, and import side-effect
    neutrality for the pure route.

No runner is authorized by this document.

## Runtime activation gates not pulled into B1D

The following stay mandatory before activation but are not dependencies of the
pure claim transaction:

- real-Isaac terminal transition smoke;
- designated wrapper terminal capture/consumer/ack;
- combined terminal/reset/claim/next-step smoke;
- reporters required by the selected disturbance scenario;
- scheduling, proposal/effective, resolver, masks, and DVM;
- wrapper/HARL and actor/shared-observation integration;
- checkpoint identity and Phase C/D learner semantics;
- explicit runtime/training readiness review.

## Stop conditions for B1D

Stop and report rather than widening the phase if:

- a claim requires changing a frozen Phase-A public DTO;
- the canonical reset baseline cannot be represented without a fake lifecycle
  result;
- post-assignment current state cannot be published atomically through the
  existing single authority boundary;
- a second StateStore/current-state authority would be required;
- terminal or stale requests cannot be rejected before mutation;
- claim legality fundamentally requires HARL terminal transport;
- one of the eleven numeric TBDs becomes necessary;
- Top-K, cost, transfer, scheduler, policy, or runtime wiring becomes necessary;
- testing the pure slice would require weakening the default-off runtime gate.

## Recommended phase sequence

~~~text
current:
  GPT/user review of B0 closeout and this plan

next, only if explicitly authorized:
  Phase B1D targeted design and contract-level review

then, only under a separate implementation authorization:
  pure/dormant B1 initial-claim transaction implementation + runner

later:
  scheduling and retry
  proposal/effective route
  conflicts and component transfer
  observation/mask/DVM integration
  environment/wrapper/HARL activation gates
~~~

Do not begin implementation from this plan alone.
