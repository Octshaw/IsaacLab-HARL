# Phase B0-3D-R Targeted Environment Integration Semantic Revision

## 1. Classification

    classification:
      PHASE-B0-3DR-TARGETED-ENVIRONMENT-INTEGRATION-SEMANTIC-REVISION-COMPLETE-AWAITING-GPT-REVIEW

    B0-1A / B0-1B / B0-2:
      review passed

    B0-3D:
      conditional review completed

    B0-3D-R:
      targeted semantic revision complete

    R1 owner-consistent physical termination:
      frozen

    R2 single destructive terminal ack authority:
      frozen

    Phase-A contract revision:
      none

    B0 contract/runtime gap:
      none

    Python/runtime changes:
      none

    B0-3 implementation:
      not authorized

    Phase B/C/D/E:
      not entered

    Isaac/training/playback/evaluation:
      not run

    commit:
      none

No stop condition was reached:

    STOP — B0-3 PHYSICAL TERMINATION CONTRACT GAP:
      not reached

    STOP — B0-3 TERMINAL HANDOFF CONTRACT GAP:
      not reached

    STOP — B0-3D-R DESIGN CONFLICT:
      not reached

This is a documentation-only targeted semantic revision. It authorizes no
environment, runtime, wrapper, resolver, controller, HARL, test, configuration,
or checkpoint implementation.

## 2. Base authority, scope, and precedence

The base authority remains:

    PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md

This revision controls only:

    R1:
      physical_terminated derivation, source, and timing

    R2:
      terminal handoff destructive acknowledgement capability and lifecycle

Every other B0-3D conclusion remains exact, including:

- the pre-reset hook inside the event-profile _get_dones path;
- transition-context reservation timing;
- all-E physical transition identity, including no-event rows;
- coverage and reward mutation after authority success;
- final TerminationReason to Gym projection;
- episode rebuild StateStore/clock/publication order;
- initial/manual/autoreset/partial reset semantics;
- existing-profile/default-off isolation;
- poison/no-rollback behavior;
- implementation slicing and numeric deferral.

Where the base design previously exposed read_terminal and ack_terminal together
as one generic future external surface, R2 below narrows that surface. Where the
base reporter matrix described physical_terminated only as a prospective
terminal task condition, R1 below freezes its exact canonical source.

No other base wording is superseded.

## 3. Source and frozen-contract findings

### 3.1 Current scan physical terminal meaning

The current scan task computes:

    raw physical pair candidate
    -> dwell_met AND uncovered
    -> newly_covered = any(raw candidate, dim=1)
    -> viewpoints_covered OR= newly_covered
    -> all_covered = viewpoints_covered.all(dim=1)

Evidence is scan_mobile_manipulator_env.py:2930-2983 and 3012-3020.
Therefore the current skeleton has a real physical all-scan-tasks-covered
terminal meaning; physical_terminated is not merely redundant decoration.

The event route must preserve that meaning after replacing fractional/passive
candidate reduction with canonical owner attribution.

### 3.2 Frozen facts and authority mapping

ExecutionTransitionFacts already contains independent:

    physical_terminated [E] bool
    completion_signals [E,M,N] bool
    coverage_before_reset [E,N] bool
    ownership_before_transition [E,N] int64

The frozen facts validator requires completion to match pre-transition owner
and permits at most one completing robot per task. It does not require
physical_terminated to be derived from an unqualified raw detector.

The B0-2 authority derives final reason from final task state and time limit.
Its receipt-free mapping check is one-way:

    physical_terminated true
      requires final reason ALL_TASKS_COMPLETED
      or NO_FEASIBLE_TASKS_REMAIN

It legally permits:

    physical_terminated false
    with a lifecycle-derived terminal reason

Evidence is assignment_lifecycle_transaction_runtime.py:1909-1972 and the
frozen descriptor at assignment_lifecycle_transition_contract.py:2858-2877.

Thus both a false-only narrow physical reporter and a canonical all-covered
reporter could fit the frozen DTO. The selected design below uses canonical
all-covered because that preserves the current task's actual independent
physical terminal semantics without a false positive.

### 3.3 Current terminal transport

The current Python environment/wrapper/runtime has no terminal slot,
read_terminal, ack_terminal, or HARL terminal transport implementation. There
is therefore no existing consumer whose destructive capability must be
preserved. R2 can freeze a B0-private capability split without a frozen schema
or runtime compatibility change.

## 4. R1 — Exact authoritative pipeline

The event-profile adapter MUST use this order:

    1 stage raw physical scan candidate
    2 capture exact transaction-private lifecycle prestate
    3 owner-gate the raw pair candidate
    4 finalize canonical completion_signals
    5 derive canonical task completion
    6 derive prospective canonical coverage
    7 derive supported physical_terminated
    8 construct ExecutionTransitionFacts

Owner qualification MUST precede physical_terminated finalization.

The staged environment report contains only facts that exist before lifecycle
prestate qualification:

    coverage_before_transition [E,N] bool
    raw_new_candidate [E,M,N] bool
    dwell_next and raw detector diagnostics
    physical_truncated [E] bool
    time_limit_reached [E] bool
    supported raw bad-transition input
    any future real typed failure/release/health reporter inputs

It MUST NOT contain a finalized physical_terminated derived from raw candidate
reduction.

## 5. R1 — Exact equations

Let:

    active0[e,j] =
      task0[e,j] in {CLAIMED, NAVIGATING, ALIGNING}

    owner_match[e,i,j] =
      owner0[e,j] == i

Then:

    completion_signals[e,i,j] =
      raw_new_candidate[e,i,j]
      AND active0[e,j]
      AND owner_match[e,i,j]

    canonical_task_completion[e,j] =
      any_i completion_signals[e,i,j]

    prospective_coverage[e,j] =
      coverage_before_transition[e,j]
      OR canonical_task_completion[e,j]

For the current event scan skeleton:

    physical_terminated[e] =
      all_j prospective_coverage[e,j]

This is the only authorized current-skeleton physical_terminated derivation.
Do not substitute:

    raw_new_candidate.any(dim=1)
    old newly_covered
    prematurely mutated viewpoints_covered
    wrapper post-step observation
    reward/global-gain buffer
    lifecycle final TerminationReason

The first four are either unqualified/resettable observations; the last is the
authority result rather than a raw physical fact.

## 6. R1 — Passive non-owner counterexample

For the last uncovered task j:

    raw_new_candidate[e, passive_robot, j] = true
    owner0[e,j] != passive_robot
    raw_new_candidate[e, owner0[e,j], j] = false

The required result is:

    completion_signals[e,:,j] = false
    canonical_task_completion[e,j] = false
    prospective_coverage[e,j] = false
    physical_terminated[e] = false

No false raw terminal assertion is created. The authority may therefore retain
reason NONE unless another canonical terminal cause exists. The passive raw
candidate may be logged as an immutable diagnostic but creates no completion,
coverage, workload, reward, event, or termination authority.

## 7. R1 — Relationship to lifecycle termination

The source classes remain distinct:

| Value | Owner | Meaning |
|---|---|---|
| raw_new_candidate | physical detector | geometric/dwell candidate before owner compatibility |
| completion_signals | trusted B0-3 adapter | owner-qualified raw execution fact |
| prospective_coverage | trusted B0-3 adapter | canonical task-level physical projection |
| physical_terminated | environment facts reporter | supported physical all-covered assertion |
| TerminationReason | LifecycleAuthorityRuntime | final semantic result with B0-2 priority |

physical_terminated does not override task state. It only asserts that the
physical all-covered boundary occurred. The B0-2 authority still derives:

    ALL_TASKS_COMPLETED
    > NO_FEASIBLE_TASKS_REMAIN
    > TIME_LIMIT
    > NONE

If canonical structural failure makes all tasks terminal while physical
coverage is incomplete, physical_terminated remains false and the authority
may correctly derive NO_FEASIBLE_TASKS_REMAIN.

If physical_terminated is true but final task state is not terminal, the
existing B0-2 receipt-free mapping check rejects the full transaction. R1 does
not weaken that fail-closed guard.

## 8. R1 — Coverage, reward, and retry semantics

Coverage/reward order remains:

    raw detection without mutation
    -> transaction-private prestate
    -> canonical facts including physical_terminated
    -> B0-2 authoritative success
    -> coverage bookkeeping write from result.completed_tasks
    -> reward
    -> autoreset

R1 does not move viewpoints_covered mutation earlier.

On receipt-free/facts failure:

    same TransitionGenerationContext remains outstanding
    same immutable staged physical report remains retained
    no coverage/reward/reset/next physics occurs

Owner qualification, prospective_coverage, and physical_terminated are derived
inside the port after capturing the exact current prestate. They are not
irreversibly embedded in the raw report.

Retry uses the same raw report and context. It recaptures/revalidates the same
bound StateStore version/prestate under the transaction boundary and derives
the canonical fields again. If that version no longer matches, retry fails
closed; it does not silently reinterpret the physical step against new state.
A producer token may be burned, but the transition generation is not skipped.

## 9. R1 — Existing-profile isolation

R1 applies only to the future event_gated_local_mrta route.

The existing profiles:

    legacy
    lifecycle_contract_c
    lifecycle_ablation
    diagnostics_hidden_state

continue their current _update_scan_progress, _get_dones, reward, reset, and
wrapper behavior. They do not construct the staged owner-gated terminal
adapter or event runtime aggregate.

## 10. R1 decision and contract-gap verdict

R1 is expressible entirely with existing private adapter inputs and frozen
facts fields. It changes neither shape, dtype, enum, factory, result, event,
profile, nor checkpoint schema.

    selected R1 scheme:
      owner-qualified canonical prospective coverage

    false-only alternative:
      not selected for current scan skeleton

    reason:
      current runtime has a real all-covered physical terminal semantic

    STOP — B0-3 PHYSICAL TERMINATION CONTRACT GAP:
      not reached

## 11. R2 — Capability split

Terminal artifact storage is one B0-private per-env slot keyed by:

    (env_id, episode_generation, transition_generation)

R2 freezes two distinct capability classes.

### 11.1 Read-only terminal observer

Approved diagnostics, logger, debugger, evaluation inspector, and visualizer
code may receive an observer port with only:

    read_terminal(exact_key)

It cannot:

    acknowledge_terminal
    clear_terminal
    overwrite_terminal
    install_terminal
    list/ack latest
    access slot storage directly

Many read-only observer ports may exist. Repeated reads return the same
immutable no-alias artifact and do not change slot state.

### 11.2 Designated terminal consumer

Exactly one consumer capability is bound once per event runtime domain. A
future wrapper/HARL terminal transport is the intended class of owner, but no
specific HARL class is bound in B0-3D-R.

Its narrow port has:

    read_terminal(exact_key)
    acknowledge_terminal(exact_key)

The acknowledge method is destructive for slot lifetime only. It cannot mutate
current lifecycle state, generations, historical artifact contents, result,
events, StateStore, or clock.

There is no generic public ack method on the observer/current-read/environment
ports.

## 12. R2 — Capability identity and lifetime

The designated consumer capability is:

    one opaque unforgeable object identity
    constructed and bound once per EventProfileLifecycleRuntimeDomain
    retained for that domain lifetime
    not recreated per episode
    not handed to observers or environment reporters
    not serializable
    not checkpointed
    not reconstructible in B0-3

The terminal store accepts destructive acknowledgement only when:

    supplied capability is the exact designated object
    exact key matches the occupied slot

Future consumer replacement/rebinding requires a separate reviewed capability
handoff design. This revision does not add one.

## 13. R2 — Exact read semantics

read_terminal requires exact:

    env_id
    episode_generation
    transition_generation

On success it:

    returns immutable no-alias terminal artifact
    does not mutate or consume the slot
    does not mark it read
    does not change generation
    does not change current PublishedLifecycleView
    permits repeated reads by approved observers and consumer

Wrong env, episode, transition, stale/future key, or absent slot receives a
typed read rejection. An invalid external read does not poison the domain.

There is no read-latest, read-by-env-only, wildcard, clear-all, or implicit
key normalization API.

## 14. R2 — Exact acknowledgement semantics

The only legal destructive sequence is:

    designated consumer reads exact immutable artifact
    -> consumer successfully captures/transports artifact
    -> same designated consumer acknowledges exact key
    -> slot becomes empty

Read never automatically acknowledges. Capture/transport failure leaves the
slot occupied. Acknowledge before successful capture is a consumer protocol
violation.

An acknowledgement validates, before mutation:

    exact designated capability identity
    exact env row
    exact episode generation
    exact transition generation
    slot exists and is occupied
    slot key equals request key

Wrong env/episode/transition, stale/future key, no slot, already acknowledged,
or foreign/forged capability all fail closed with a typed rejection and no
slot/current-view/generation mutation.

The slot removal is one atomic internal state replacement under the terminal
store/publication synchronization boundary. Successful ack frees only that
row's terminal slot.

Slot installation, occupied-slot prevalidation, and destructive ack all
acquire the coordinator publication lock and then the terminal store's private
lock, never in reverse order. Observer reads cross the same supported terminal
read boundary before receiving an immutable artifact. This serializes ack with
the receipt-free capacity check and Stage-9 installation without exposing
either lock or making ack a lifecycle-state publication.

## 15. R2 — Chosen one-slot progression policy

Choose:

    one-slot persistence without blocking ordinary nonterminal work

An unacknowledged old terminal slot:

    does not block its associated episode rebuild
    survives that rebuild
    does not block ordinary new-episode nonterminal transitions
    does block commitment/installation of the next terminal handoff
      for the same env row

Strict backpressure on every post-reset physical step is rejected. DirectMARLEnv
steps a vector batch together; globally stalling ordinary work merely because
a transport observer has not acknowledged one historical artifact is stronger
than the one-slot safety requirement.

This policy bounds storage to one outstanding terminal artifact per env while
allowing normal nonterminal progress.

## 16. R2 — Next-terminal backpressure and retry

Because B0-2 transactions are all-E atomic, occupied-slot capacity is checked
after the authority has derived the candidate final reason but before ledger
consume.

If a new terminal candidate targets an occupied row:

    reject receipt-free with typed terminal_slot_occupied backpressure
    consume no receipt
    finalize no result
    mutate no StateStore
    commit no transition generation
    publish no result/current view
    write no coverage/reward
    perform no reset
    retain same staged report and outstanding transition context

After the designated consumer acknowledges the old exact slot, the same
physical report/context may retry through the existing B0-3 receipt-free retry
rule. The whole vector batch remains paused only at this terminal-capacity
boundary, not during ordinary preceding nonterminal work.

This check must be inside the coordinator's B0-private receipt-independent
prevalidation/publication boundary. It cannot be a post-return environment
check.

For a vector batch, every terminal candidate row is checked before consume; one
occupied terminal row rejects the complete all-E transaction. The publication
lock remains held from this check through successful terminal slot installation,
so another supported operation cannot create an occupied slot in between.

If a slot becomes occupied after the successful receipt-free reservation check
but before terminal installation, synchronization/capability ordering has been
violated. That impossible internal overwrite attempt is fatal and poisons the
domain. No existing slot is overwritten or auto-acknowledged.

## 17. R2 — Installation, autoreset, and current view

The retained B0-3D order remains:

    terminal transition authoritative success
    -> install exact terminal slot under publication lock
    -> expose done result
    -> reward
    -> environment autoreset

Episode reset MUST NOT clear the terminal slot.

After reset, both coexist:

    historical slot:
      episode p
      transition g
      terminal result and pre-reset artifact

    current PublishedLifecycleView:
      episode p+1
      transition g
      reset lifecycle state
      result None

read_current cannot infer or consume the terminal artifact. read_terminal
cannot mutate current lifecycle state. Successful terminal ack does not rewrite
the current view.

## 18. R2 — Rejection versus poison

| Condition | Classification | Mutation | Poison |
|---|---|---:|---:|
| observer reads wrong/absent key | typed external rejection | none | no |
| designated consumer acks wrong/stale/already-acked key | typed external rejection | none | no |
| foreign capability attempts ack | typed capability rejection | none | no |
| new terminal candidate sees occupied slot before consume | typed receipt-free backpressure | none | no |
| internal code attempts overwrite after authoritative success | impossible invariant failure | none to old slot | yes |
| slot/result/generation identity differs during installation | impossible invariant failure | no publication | yes |

Stale reads and invalid consumer requests are not runtime corruption. They fail
closed without poisoning. Poison is reserved for an internal path that would
lose, overwrite, or misbind an authoritative terminal artifact.

## 19. R2 decision and contract-gap verdict

R2 uses only B0-private store/port/capability records. LifecycleTransitionResult
already supplies exact env, episode, transition, token, receipt, reason, state,
and events needed to bind the artifact. No result or event field is required to
express destructive ownership.

    terminal storage:
      one per-env exact-generation slot

    observer count:
      multiple approved read-only capabilities allowed

    destructive authority count:
      exactly one designated consumer capability per domain

    ordinary nonterminal work with old slot:
      allowed

    next terminal with old slot:
      receipt-free backpressure until exact ack

    STOP — B0-3 TERMINAL HANDOFF CONTRACT GAP:
      not reached

## 20. Semantics not reopened

R1/R2 do not change:

- the full all-E transaction batch;
- no-event transition commits;
- completion/release/failure/health authority equations;
- C1, TEAM, robot projection, event order, or final reason priority;
- coverage/reward success ordering;
- autoreset/manual/partial reset algorithms;
- StateStore-before-clock success tails;
- reset result=None publication;
- existing-profile paths;
- event runtime readiness;
- real reporter deferrals;
- terminal critic-sidecar deferral;
- Phase-B assignment deferral;
- eleven numeric TBDs.

## 21. Future implementation verification oracle

No tests are run in B0-3D-R. A later authorized implementation must include:

### R1

1. last uncovered task, passive non-owner raw candidate only:
   completion false, prospective coverage false, physical_terminated false;
2. exact owner completes last uncovered task:
   completion true, prospective coverage true, physical_terminated true;
3. mixed raw owner/non-owner candidates:
   only owner contributes;
4. pre-existing canonical coverage all true:
   physical_terminated true even with no new raw candidate;
5. retry with same staged report/context:
   canonical terminal fields rederived from exact bound prestate;
6. existing four profiles preserve current behavior.

### R2

7. multiple observer reads are no-alias and non-destructive;
8. only exact designated consumer capability may ack;
9. wrong env/episode/transition, no-slot, and duplicate ack reject atomically;
10. successful transport then exact ack frees one row only;
11. terminal slot survives autoreset and coexists with reset current view;
12. unacked slot permits ordinary new-episode nonterminal transactions;
13. next terminal on occupied row rejects before consume and can retry after ack;
14. impossible overwrite/identity mismatch poisons without losing old slot;
15. observer/current/environment ports expose no destructive ack capability;
16. default-off/readiness and no-production-wiring checks remain exact.

## 22. Numeric and phase boundary

All eleven numeric TBDs remain unresolved:

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

No value is selected.

This revision does not implement EventProfileLifecycleRuntimeDomain,
environment ports, episode rebuild, staged reporters, terminal slots,
acknowledgement capability, _get_dones/_reset_idx hooks, reward integration, or
terminal critic transport.

## 23. Final handoff

    classification:
      PHASE-B0-3DR-TARGETED-ENVIRONMENT-INTEGRATION-SEMANTIC-REVISION-COMPLETE-AWAITING-GPT-REVIEW

    base authority:
      PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md

    targeted precedence:
      R1 and R2 only

    selected R1:
      owner-qualified canonical prospective coverage
      then physical_terminated = all tasks prospectively covered

    selected R2:
      many read-only observers
      one designated destructive consumer capability
      nonterminal progress allowed with old slot
      next terminal receipt-free backpressure until exact ack

    Phase-A frozen schema change:
      none

    B0-3 implementation:
      not authorized

    next action:
      GPT/user review; do not begin B0-3I1 or environment integration
