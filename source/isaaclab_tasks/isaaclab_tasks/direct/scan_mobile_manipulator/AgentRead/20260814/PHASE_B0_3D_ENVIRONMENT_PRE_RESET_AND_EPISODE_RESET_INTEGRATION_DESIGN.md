# Phase B0-3D Environment Pre-reset and Episode Reset Integration Design

## 1. Classification and decision

```text
classification:
  PHASE-B0-3D-ENVIRONMENT-PRE-RESET-AND-EPISODE-RESET-INTEGRATION-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

B0-1A / B0-1B / B0-2:
  review passed

B0-3D:
  design complete

B0-3 implementation:
  not authorized

Phase B/C/D/E:
  not entered; not authorized

Python/runtime changes:
  none

Isaac/AppLauncher/training/playback/evaluation:
  not run

commit:
  none
```

This document is the authoritative design oracle for the later, separately
authorized B0-3 implementation. It does not activate the event profile, weaken
the Phase-A readiness barrier, or authorize a runtime edit.

The design audit found no stop condition:

```text
STOP — B0-3 PRE-RESET FACTS GAP:
  not reached

STOP — B0 CONTRACT/RUNTIME GAP:
  not reached

STOP — B0-3 CAPABILITY GAP:
  not reached

STOP — B0-3 RESET ATOMICITY GAP:
  not reached
```

The pair-shaped candidate exists before reduction/reset; the frozen facts
already carry every B0 raw edge and prestate field; a narrow aggregate can
reserve generations without exposing clock/store capabilities; and episode
rebuild can reuse the B0-2 publication/poison model. No Phase-A frozen contract
revision is required.

## 2. Normative sources and precedence

This design uses, in order:

1. unchanged Phase-A profile, event, and lifecycle-transition contracts;
2. B0-2D-R for C1/C2;
3. B0-2D for authority equations, reason priority, and transaction order;
4. the reviewed B0-2 transaction implementation/report;
5. the reviewed B0-1A producer and B0-1B clock implementations/reports;
6. this design for environment pre-reset, handoff, and episode rebuild only.

It does not reopen completion/release/failure/health precedence, C1,
TEAM_INFEASIBLE, robot projection, event ordering, receipt semantics, or the
B0-2 state-swap-before-clock-commit order.

## 3. Exact current source and runtime order audit

### 3.1 DirectMARLEnv order

The current base order is fixed by
`source/isaaclab/isaaclab/envs/direct_marl_env.py:328-415`:

```text
_pre_physics_step(actions)
-> decimated _apply_action / write / sim.step / render / scene.update
-> episode_length_buf += 1
-> common_step_counter += 1
-> _get_dones()
-> _get_rewards()
-> _reset_idx(done env rows)
-> interval events
-> _get_observations()
-> return post-reset observations plus pre-reset reward/done tensors
```

The explicit reset route is
`DirectMARLEnv.reset():298-325 -> _reset_idx(all rows):319 ->
_get_observations():322`. Base `_reset_idx():626-650` resets scene/event/
noise state and writes `episode_length_buf[ids] = 0`.

The integration MUST NOT override or copy the whole base `step()` or reset
implementation. It uses the task `_get_dones()` and `_reset_idx()` overrides.

### 3.2 Scan task order and last safe pre-reset point

Current task evidence is:

- `_pre_physics_step():2805-2843` mutates proxy base/scanner pose;
- `_update_scan_progress():2930-2983` forms the local physical candidate,
  mutates dwell, reduces pair identity, writes reward diagnostics, and mutates
  coverage;
- `new_candidate = dwell_met & uncovered [E,M,N]` exists at line 2975;
- `newly_covered = any(new_candidate, dim=1) [E,N]` discards pair identity at
  line 2978;
- `viewpoints_covered |= newly_covered` mutates coverage at line 2983;
- `_get_dones():3012-3020` invokes scan progress before done classification;
- `_reset_idx():3022-3047` overwrites pose, coverage, dwell, reward, action,
  and diagnostic buffers before post-reset observations.

The authoritative hook is therefore inside the event-profile branch of
`_get_dones()`, after physical predicates and staged dwell computation, but
before pair reduction, coverage/reward mutation, return to base `step()`, or
autoreset.

### 3.3 Wrapper reconstruction is invalid

`assignment_harl_wrapper.py:461-560` reads `pre_step_problem` before
`env.step()` and `post_step_problem` only after autoreset. The problem
mapping exposes live pose/coverage aliases, so saved coverage can be
mutated/reset before wrapper use. The environment has no authoritative
assignment tensor, and continuous controller actions do not invert uniquely
to ownership. The wrapper MUST NOT reconstruct event-profile completion,
terminal facts, or old-episode lifecycle state.

## 4. Event-profile runtime ownership and lifetime

One vector-environment domain owns exactly one retained aggregate:

```text
EventProfileLifecycleRuntimeDomain
  exact ResolvedEventGatedAssignmentProfile object
  stable env_id universe and device
  one EnvironmentExecutionFactsProducer
  one LifecycleGenerationClock
  one LifecycleStateStore
  one LifecycleAuthorityTransactionCoordinator
  one publication lock/poison domain
  one terminal-handoff store
  narrow environment and external-read ports
```

The future event-only composition root constructs this aggregate after the scan
environment has allocated its task buffers and before the first external
`reset()`. It binds exactly one narrow environment port. The environment may
retain that port so the aggregate lifetime follows the environment, but it
does not receive the raw aggregate components.

The aggregate is never reconstructed for the same live domain. B0-3 adds no
serialization, restore, clock reset, or domain reconstruction protocol.
Initial coordinator state remains episode `-1`, transition `-1`, result
absent until the first ordinary reset performs bootstrap `-1 -> 0`.

## 5. Coordinator/environment capability boundary

### 5.1 Environment port

The environment receives one B0-private port with only:

```text
finalize_physical_transition(staged_raw_report)
episode_rebuild(selected_env_ids, reset_initial_inputs)
```

The first operation internally reserves contexts, builds facts, invokes B0-2,
stores terminal handoffs, and returns one immutable environment outcome. The
second is a reset transaction/context so native Isaac reset mechanics remain
in the environment while lifecycle publication remains atomic.

The environment never receives:

```text
EnvironmentExecutionFactsProducer
LifecycleGenerationClock or snapshot capability
LifecycleStateStore or writer/snapshot capability
LifecycleAuthorityRuntime
TransitionConsumeLedger or receipt
LifecycleTransitionResultFactory or authority stamp
PublishedLifecycleView installation capability
```

### 5.2 External readers

Future consumers receive only:

- `read_current()`, returning the immutable current state/generation view
  under the C2 publication lock;
- `read_terminal(env, episode, transition)`;
- `ack_terminal(env, episode, transition)`.

They cannot request contexts, rebuild episodes, write state, finalize results,
or bypass the publication lock. A retained old view is historical data, not a
live capability.

The environment supplies physical observations and invokes the port. The
aggregate coordinates ordering. `LifecycleAuthorityRuntime` remains the sole
semantic authority, StateStore the sole state writer, and the clock the sole
generation writer.

## 6. Transition-context reservation ownership and timing

Choose reservation Option B: inside the pre-reset port after physical
step/counter update and staged reporter capture, immediately before B0-1A
facts construction. Do not reserve before physics. This shortens outstanding
lifetime and still binds the old-episode generation before reset.

Every successful physical step transacts all `E` rows, including no-event
rows. `transition_generation` identifies every authoritative physical
transition, not only lifecycle-changing transitions. A no-event step therefore
still gets contexts, facts, result, StateStore version increment, and a
contiguous generation commit. Reset selects done rows and creates no physical
transition or transition generation.

The port owns the contexts and never returns them to the environment. On a
pre-consume/facts failure it retains the same contexts and immutable staged
report. A reviewed explicit retry may rebuild facts with that same context; a
burned facts token is not reused. Until retry or teardown there is no next
physics, reset, reward/coverage commit, cancellation, or generation advance.
Any post-receipt failure poisons the aggregate and permits no retry/reset.

## 7. Raw execution reporter source matrix

`E` is the full batch, `M` robots, and `N` tasks. Owner attribution means
the exact robot/task cause reaches facts, not merely a robot-shaped raw tensor.

| Frozen facts field | Current runtime source | Exact current shape | Pre-reset available | Owner attribution preserved | B0-3 status |
|---|---|---|---:|---:|---|
| `env_id` | aggregate stable row IDs | `[E] int64` | yes | n/a | READY |
| `episode_generation` | retained clock through port | `[E] int64` | yes | n/a | READY |
| `transition_generation` | port-reserved contexts | `[E] int64` | yes | n/a | READY |
| `physical_terminated` | prospective terminal task condition before coverage write | `[E] bool` | yes | n/a | NEEDS NARROW ADAPTER |
| `physical_truncated` | current horizon timeout | `[E] bool` | yes | n/a | READY |
| `time_limit_reached` | current episode-length comparison | `[E] bool` | yes | n/a | READY |
| `bad_transition` | no independent current reporter; narrow skeleton supports the time-limit edge | `[E] bool` | narrow mapping only | n/a | NEEDS NARROW ADAPTER |
| `completion_signals` | local `new_candidate` before reduction, gated by prior owner/active state | `[E,M,N] bool` | yes | after adapter | NEEDS NARROW ADAPTER |
| `terminal_pair_failure_signals` | no real structural-failure reporter | `[E,M,N] bool` | no | no | DEFERRED REAL REPORTER |
| `forced_release_signals` | no real typed release reporter | `[E,M,N] bool` | no | no | DEFERRED REAL REPORTER |
| `robot_unavailable_signals` | no real health falling-edge reporter | `[E,M] bool` | no | explicit if added | DEFERRED REAL REPORTER |
| `robot_recovered_signals` | no real health recovery reporter | `[E,M] bool` | no | explicit if added | DEFERRED REAL REPORTER |
| coverage input basis | cloned coverage before mutation plus canonical completion | `[E,N] bool` | yes | task projection | NEEDS NARROW ADAPTER |
| `task_state_before_transition` | transaction-private StateStore snapshot | `[E,N] int64` | yes | canonical | READY |
| `robot_state_before_transition` | transaction-private StateStore snapshot | `[E,M] int64` | yes | canonical | READY |
| `ownership_before_transition` | transaction-private StateStore snapshot | `[E,N] int64` | yes | canonical | READY |
| `consume_once_token` | B0-1A allocator | `[E] int64` | constructed pre-reset | per row | READY |

All-false pure fixtures are `SYNTHETIC TEST ONLY`; they do not prove that
failure/release/health reporters exist. Future independent non-time-limit
truncation also requires a real reporter and the existing fail-closed mapping.

## 8. Completion attribution and staged scan hook

### 8.1 Detector split

For the event profile only, split current scan progress into this staged order:

    prepare_scan_transition_report()
      compute physical predicates
      compute dwell_next without writing dwell_counter
      clone coverage_before_transition
      compute raw new_candidate [E,M,N]
      perform no coverage/reward/dwell mutation

    port.finalize_physical_transition(report)
      combine candidate with exact transaction-private ownership/task state
      build canonical facts and finalize B0-2 transaction

    commit_scan_transition_outcome(outcome)
      write prepared dwell_next
      write authoritative coverage/reward diagnostics

Existing profiles continue to use the current method and mutation order
unchanged.

### 8.2 Canonical owner gate

For each task j:

    owner_qualified[e,i,j] =
      raw_new_candidate[e,i,j]
      AND task0[e,j] in {CLAIMED, NAVIGATING, ALIGNING}
      AND owner0[e,j] == i

completion_signals is this owner-qualified tensor. Passive non-owner
candidates are diagnostics only: no completion, workload, coverage credit,
event, or reward. If more than one owner-qualified robot appears for one task,
the full batch fails before consume. Ownership comes only from the versioned
StateStore snapshot, never actions, nearest geometry, or wrapper state.

## 9. Coverage mutation ordering

The event route does not mutate coverage during raw detection:

    coverage0 = clone(viewpoints_covered)
    -> raw pair detector
    -> owner-gated completion facts
    -> B0-2 authority/result/state/generation publication
    -> coverage1 = coverage0 OR result.completed_tasks
    -> success-only environment coverage write

B0-1A still forms prospective coverage_before_reset as coverage0 OR
completion_signals.any(dim=1). Post-authority environment coverage MUST match
that projection in the current scan skeleton. Duplicate diagnostics may use
raw candidates against coverage0, but cannot change canonical completion.

An unexpected failure while applying prepared dwell/coverage/reward
bookkeeping after authority success is fatal: poison, no autoreset, no
observation publication, no rollback, and no normal continuation.

All bookkeeping tensors and index sets must be prepared before facts consume so
the post-authority writes are a bounded no-allocation success tail. If an
impossible write still fails, the environment reports a typed fatal condition
through the same narrow domain port; that port may mark poison but exposes no
store/clock/ledger capability.

## 10. Authority position, termination, and reward

### 10.1 Event-specific _get_dones order

    stage scan dwell/raw pair candidate/coverage0
    -> stage horizon and supported physical flags
    -> pre-reset port for all E rows
       -> reserve contexts
       -> capture transaction-private prestate
       -> build canonical ExecutionTransitionFacts
       -> B0-2 consume/finalize/store swap/clock commit/publication
       -> install terminal slots before return
    -> validate immutable EnvironmentTransitionOutcome
    -> commit scan dwell/coverage/reward bookkeeping
    -> return outcome terminated/truncated dictionaries

This is inside _get_dones, before base _get_rewards and autoreset.

### 10.2 Final reason to Gym projection

The environment supplies raw physical flags; it does not choose the final
reason. B0-2 retains:

    ALL_TASKS_COMPLETED
    > NO_FEASIBLE_TASKS_REMAIN
    > TIME_LIMIT
    > NONE

| Final reason | terminated | truncated |
|---|---:|---:|
| NONE | false | false |
| ALL_TASKS_COMPLETED | true | false |
| NO_FEASIBLE_TASKS_REMAIN | true | false |
| TIME_LIMIT | false | true |

The event branch MUST NOT OR in the old independent all_covered output.
Unsupported raw terminal/truncation mapping fails before authority commit.

### 10.3 Reward order

    authority success
    -> environment bookkeeping commit
    -> _get_rewards reads same-transition committed buffers
    -> autoreset

Own gain belongs only to the canonical completing owner; global gain derives
from result.completed_tasks. Reward may read the result but cannot mutate
result, state, reason, counters, or events. Failed/poisoned transactions emit
no reward.

## 11. Terminal pre-reset handoff and mailbox decision

Two artifacts have different lifetimes:

1. an immutable full-batch EnvironmentTransitionOutcome for the step being
   returned, retained through the current wrapper call;
2. a persistent per-env terminal slot only for rows that will autoreset.

The full-batch outcome is not a persistent mailbox. It preserves same-step
reward/done/result information while per-env slots prevent a terminal
old-episode artifact from being lost or overwritten by partial resets.

| Option | Overwrite safety | Partial reset | Generation identity | Wrapper transport | Complexity | Decision |
|---|---|---|---|---|---|---|
| single latest batch handoff | unsafe on replacement | awkward | batch only | simple | low | reject as persistent store |
| per-env terminal slot | overwrite rejected per row | natural | exact row key | sufficient | low | base storage |
| generation-keyed mailbox | safe | natural | strongest | more than needed | high | defer |
| read/ack mailbox | safe with exact ack | natural | exact key | sufficient | medium | chosen protocol |

The chosen minimal protocol is per-env terminal slots with exact read/ack:

    key:
      (env_id, episode_generation, transition_generation)

    payload:
      immutable finalized LifecycleTransitionResult binding
      immutable pre-reset lifecycle snapshot/view
      final reason and Gym projection
      coverage_before_reset
      facts token and authority receipt identity already in result
      reserved placeholder for a later terminal critic sidecar

Installation occurs under the publication lock after transition success and
before returning done flags. A slot owns cloned/frozen storage and survives
_reset_idx. Reset never clears it. A second terminal write to an unacknowledged
row is fatal; wrong/stale ack is rejected.

The current B0-2 transact method releases its lock when it returns. Therefore
the future implementation MUST extend the B0-private coordinator publication
tail so terminal payload preparation and slot installation occur before that
release. It MUST NOT install the slot through an environment callback or a
second post-transaction raw-lock acquisition. This is a private capability
extension, not a frozen result/mailbox schema change.

Historical terminal handoff and post-reset current view are different:

    terminal handoff:
      old episode p, committed transition g, terminal state/result

    current view after reset:
      episode p+1, same transition g, initial lifecycle state, result None

No wrapper may reconstruct the former from the latter.

## 12. Episode reset lifecycle semantics

### 12.1 Canonical reset state

For selected rows:

    task_state:
      AVAILABLE for every scenario task
    ownership:
      -1 for every task
    cumulative_failed_pairs:
      false
    completion_count:
      0
    termination_reason:
      NONE
    robot_state:
      NEEDS_ASSIGNMENT for each healthy robot with AVAILABLE work
      UNAVAILABLE only from a future real typed reset-health input

Reset does not derive TEAM_INFEASIBLE from path, cost, budget, or static
feasibility. It performs no assignment/claim and emits no lifecycle event.
The current skeleton has no real unavailable reset reporter, so healthy is the
only READY initialization.

### 12.2 Generation and version rules

    episode_generation:
      selected rows +1 exactly once per explicit/autoreset rebuild
      first reset -1 -> 0
    transition_generation:
      unchanged across reset; never reset between episodes
    facts token / receipt IDs:
      unchanged process-lifetime authorities
    StateStore version:
      global version +1 once per episode rebuild transaction

The global version increment conservatively stales all prior full-domain
snapshots. Unselected row values remain bit-exact.

### 12.3 Published view after reset

Existing PublishedLifecycleView is sufficient. It accepts result=None, binds
state plus full episode/transition vectors, and derives false done flags from
reset reason NONE. No publication-kind field is needed.

    transition publication:
      updated state, same episode, newly committed transition, finalized result

    episode rebuild publication:
      reset selected state, incremented selected episode
      unchanged transition vector, result None

Reset invents no facts, transition, result, reward, receipt, or terminal
handoff.

## 13. Unified manual/autoreset integration boundary

Every path reaches the same task _reset_idx(selected_env_ids) override:

- first explicit reset selects all rows;
- later explicit reset selects all rows unless a reviewed partial API selects a
  subset;
- autoreset selects done rows.

The task override uses one reset transaction context:

    with lifecycle_port.episode_rebuild(selected_ids, reset_inputs) as rebuild:
      super()._reset_idx(selected_ids)
      reset task physical/progress/action/reward buffers
      rebuild.commit_physical_reset_complete()

The context acquires the publication lock and performs lifecycle/generation
validation and preparation before yielding. The task remains responsible for
native scene and scan reset. The lifecycle module only prepares/commits state,
generation, and publication.

If physical reset raises before completion, the context exits without
StateStore/clock/publication mutation. Physical buffers may be partial, so the
environment call fails and cannot continue; no observation is built.

For the event profile, wrapper-local lifecycle generation MUST NOT increment as
a second authority. Existing profiles keep current wrapper behavior unchanged.

## 14. Exact episode rebuild transaction

The following order is frozen for initial, manual, and autoreset rebuilds.
All work is under the same coordinator publication lock used by B0-2.

### 14.1 Prepare before physical reset

1. Reject poison; validate exact event profile, selected nonempty unique env IDs,
   device/domain identity, and reset-input type/shape.
2. Prove every selected row has no outstanding transition candidate. For
   terminal autoreset, the just-finished transition must already be committed
   and cleared. Prove episode increment does not overflow.
3. Capture one transaction-private current StateStore snapshot/version, one
   clock snapshot, and the current published view. Validate their full-domain
   state/episode/transition identity.
4. Validate that every selected terminal autoreset row has the exact installed
   terminal handoff for its current episode/transition. Initial/manual reset
   does not fabricate this requirement when no terminal transition exists.
5. Merge canonical initial lifecycle rows into a cloned full-domain state;
   leave unselected rows bit-exact.
6. Validate all reset poststate invariants, including enum domains, no owners,
   robot inverse, failed=false, counts zero, reason NONE, and no TEAM state.
7. Prepare all allocations and copies:
   - a B0-private prepared reset StateStore replacement at version +1;
   - the expected full episode vector with selected rows +1;
   - the unchanged full transition vector;
   - an immutable reset PublishedLifecycleView with result=None.
8. Revalidate StateStore identity/version and exact clock values/no-outstanding
   while still holding the publication lock.

Only after these steps does the reset context yield to the task's native
physical reset implementation.

### 14.2 Native physical reset

9. The task calls base _reset_idx and performs its existing scan-buffer resets.
   The lifecycle module neither duplicates nor substitutes scene reset.
10. The task signals physical-reset completion. No external current lifecycle
    reader can enter because the publication lock remains held.

### 14.3 No-fail lifecycle success tail

11. Revalidate that prepared StateStore and clock identities are unchanged.
12. Commit the already prepared StateStore replacement as one pointer/state
    swap. This is the first lifecycle mutation.
13. Call clock.advance_episode(selected_env_ids). The clock operation is the
    final internal success marker; it must return exactly the expected selected
    episode +1, unchanged transition values, and no outstanding candidate.
14. Install the already prepared reset PublishedLifecycleView.
15. Mark rebuild successful and release the publication lock. Only now may
    post-reset observations or a fresh external current read occur.

StateStore goes before clock for the same reason as B0-2: every allocation and
semantic check is prepared before mutation, StateStore commit is one guarded
pointer swap, and the independently guarded clock update is the final success
marker. Nothing is published between them.

The reset preparation needs a new narrow B0-private reset candidate/prepared
swap capability in the StateStore/coordinator runtime. It is not a new frozen
facts/result/event/profile schema and is inaccessible to environment readers.

## 15. Reset poison and failure analysis

| Failure point | Internal state effect | Generation effect | Publication | Required response |
|---|---|---|---|---|
| validation/preparation before native reset | none | none | old view remains | reject; no physical reset |
| native physical reset raises before lifecycle commit | no lifecycle mutation | none | old view remains historical | fail environment call; no observation/continuation |
| prepared StateStore commit unexpectedly fails | none by required one-swap contract | none | none new | fatal/poison if after physical reset |
| StateStore swap succeeds, episode advance fails | reset state may exist internally | old episode retained | install nothing | poison, teardown, no fresh read, no rollback |
| episode advance succeeds, reset-view install unexpectedly fails | reset state/new episode internal | selected +1 | install nothing | poison, teardown, no fresh read |
| success | reset state | selected episode +1; transition unchanged | reset view installed once | continue to observations |

The reverse clock-first order is rejected. If clock advance succeeded and the
StateStore preparation/swap then failed, generation would advance without its
state and the only recovery would still be poison. Using the already
prevalidated StateStore swap first preserves the reviewed B0-2 success-tail
model.

After any post-physical-reset or post-StateStore impossible failure:

    publish nothing
    mark the domain poisoned
    block fresh reads, transition calls, and reset calls
    create no observation/reward/handoff
    do not rollback state or clock
    do not cancel a candidate
    do not retry automatically
    require teardown

An already retained old immutable view or terminal handoff remains coherent
historical data but cannot authorize continuation.

## 16. Initial bootstrap, later reset, and partial reset

### 16.1 One reset semantic

Initial bootstrap is not a separate constructor initializer:

    construct dormant domain at episode=-1, transition=-1
    -> first ordinary environment reset
    -> run exact episode rebuild transaction
    -> selected episode -1 -> 0

Later autoreset/manual reset uses the same transaction:

    episode k -> k+1
    transition generation unchanged

This avoids both missed explicit-reset increments and double increments from a
wrapper plus environment reset.

### 16.2 Partial vector reset

Each physical step transacts all E rows. Afterwards, DirectMARLEnv may select a
done subset R for autoreset:

    rows in R:
      physical buffers reset
      lifecycle rows rebuilt
      episode +1

    rows not in R:
      physical and lifecycle row values bit-exact
      episode and transition generations unchanged by reset

The reset transaction is atomic for the selected subset but prepares one
merged full-domain StateStore replacement and one full-domain view. The global
StateStore version increments once, not once per row.

The preceding full-batch transition result cannot remain the result field of a
mixed post-reset current view because its state/episode binding would be false.
Therefore reset publication uses result=None for the full current view.
Same-step full-batch transition output remains in the ephemeral environment
outcome; each terminal row remains in its persistent read/ack slot.

## 17. Published reader behavior across autoreset

There are three supported observations:

1. before transition success, readers retain old state/old generation;
2. after transition publication but before reset commit, internal code can form
   terminal handoff while external readers are excluded by environment call
   ordering/publication lock;
3. after reset publication, fresh readers get reset state/new episode/same
   transition generation.

No reader can obtain:

- post-reset state with the old episode;
- terminal state with the new episode;
- reset state carrying the old transition result;
- new lifecycle state with an uncommitted generation;
- raw store/clock snapshots assembled through separate calls.

The step-return transport may expose the immutable same-step outcome after
autoreset, but it is explicitly historical and generation-bound.

## 18. Existing-profile isolation and readiness

The exact canonical profile subtype is selected before domain construction.

For the four existing profiles:

    no event runtime aggregate
    no B0 publication lock
    no clock/store/producer/coordinator construction
    no staged scan branch
    current _update_scan_progress and reward/done/reset behavior unchanged
    current wrapper-local diagnostics/generation behavior unchanged

For the event profile:

    exact subtype only
    dormant stack construction only after a later implementation authorization
    environment keeps narrow port only

The global event route remains:

    runtime route: event_gated_phase_a_interface_only_v1
    runtime readiness: interface_only
    training support: phase_a_blocked
    playback support: blocked

require_assignment_profile_runtime_ready and all frozen profile/schema
identities remain unchanged. B0-3 implementation slices MUST remain dormant
and unavailable to normal gym/HARL entrypoints until a later atomic readiness
review.

## 19. No Phase-B or numeric semantics

B0-3 performs no assignment commit, claim, transfer, scheduling, local-set
build, Top-K, cost, cooldown, retry, component solve, resolver, DVM, or
checkpoint tensor use. Reset produces NEEDS_ASSIGNMENT state but does not
choose a task.

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

## 20. Small independently reviewable implementation slices

To avoid ambiguity with this B0-3D design phase, future implementation slices
use I-suffixed names until review assigns final labels:

### B0-3I1 — Pure episode rebuild transaction

- add B0-private reset candidate/prepared StateStore replacement;
- prepare/swap/clock-advance/reset-view ordering;
- partial rows, versioning, poison, and manual/initial equivalence;
- pure tests only; no environment wiring.

### B0-3I2 — Dormant domain aggregate and capability ports

- exact event-profile aggregate construction/lifetime;
- internal context reservation and current/terminal read ports;
- raw clock/store confinement and default-off proof;
- no normal entrypoint readiness.

### B0-3I3 — Staged pre-reset reporter and facts adapter

- event-only staged scan detector;
- owner-gated pair completion;
- facts source adapters, no-event all-E transitions, coverage/reward outcome;
- deferred real reporters remain disabled and explicitly labeled.

### B0-3I4 — Terminal handoff and reset integration

- _get_dones, _get_rewards, and _reset_idx narrow hooks;
- persistent per-env read/ack slots;
- manual/autoreset/partial reset unification;
- still dormant/default-off, with no HARL training route.

Each slice requires an independent authorization and review. None is authorized
by this design.

## 21. Future test and evidence plan

B0-3D designs but does not run these tests:

| ID | Required proof |
|---|---|
| P1 | exact physical/dones/reward/autoreset/observation hook order |
| P2 | no-event physical transition commits one contiguous generation |
| P3 | pair-attributed completion is captured before reduction |
| P4 | completion authority precedes reward and coverage write |
| P5 | terminal result/handoff is finalized before autoreset |
| P6 | terminal handoff survives reset and exact read/ack works |
| P7 | reset clears failed pairs, counts, reason, owner, and terminal task state |
| P8 | selected episode_generation advances exactly once |
| P9 | transition_generation remains unchanged by reset |
| P10 | partial reset changes selected rows only; one global version increment |
| P11 | initial/manual/autoreset use the same rebuild semantics |
| P12 | four existing profiles preserve byte/behavior identity |
| P13 | pre-consume failure blocks reward, coverage, reset, and next physics |
| P14 | post-receipt poison blocks reset/publication/continuation |
| P15 | successful reset publishes state/new episode/same transition atomically |
| P16 | injected post-swap clock failure poisons with no mixed external view |
| P17 | environment/external readers cannot access raw clock/store capabilities |
| P18 | event profile remains blocked by the existing runtime-ready gate |

Pure tests should use deterministic tensor fixtures, clone/alias checks, exact
types, batch-atomic failures, and Event-based interlocks without sleeps.
Isaac/AppLauncher evidence remains a later separately authorized phase.

## 22. Evidence basis, scope, and final handoff

### 22.1 Read-only evidence

The design audit inspected:

- DirectMARLEnv reset/step/autoreset order;
- scan environment construction, staged physical buffers, completion detector,
  dones, reward, observation, and reset paths;
- wrapper pre/post problem aliases and wrapper-local episode counter;
- B0-1A producer and B0-1B clock APIs;
- B0-2 StateStore, PublishedLifecycleView, transaction coordinator, C1/C2,
  poison, and publication behavior;
- frozen profile, event, and transition semantics through their reviewed
  reports/designs.

No Python test, Isaac runtime, AppLauncher, training, playback, or evaluation
was run.

### 22.2 Design decisions frozen here

    current runtime order: audited
    pre-reset integration point: frozen
    runtime stack ownership/lifetime: frozen
    environment capability boundary: frozen
    transition-context timing: frozen
    all-E no-event transition identity: frozen
    reporter source matrix: frozen
    completion owner gate: frozen
    coverage/reward ordering: frozen
    reason/Gym projection: frozen
    terminal read/ack strategy: frozen
    episode rebuild transaction: frozen
    episode/transition/version reset semantics: frozen
    reset publication and poison: frozen
    initial/manual/autoreset/partial semantics: frozen
    existing-profile isolation: frozen

### 22.3 Deferred and unauthorized

- all real failure/release/health reporters;
- terminal critic-sidecar tensor definition and HARL transport;
- all B0-3 implementation slices;
- global runtime readiness;
- Phase B/C/D/E;
- any numeric selection;
- runtime/performance claims.

Final state:

    classification:
      PHASE-B0-3D-ENVIRONMENT-PRE-RESET-AND-EPISODE-RESET-INTEGRATION-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

    Phase-A contract revision:
      none

    B0 contract/runtime gap:
      none

    B0-3 implementation:
      not authorized

    next action:
      GPT/user review; do not begin implementation
