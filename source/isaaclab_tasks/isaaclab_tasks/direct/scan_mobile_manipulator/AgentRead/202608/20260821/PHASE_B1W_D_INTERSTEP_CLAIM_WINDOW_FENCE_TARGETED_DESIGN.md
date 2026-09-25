# Phase B1W-D Inter-Step Claim-Window Fence Targeted Design

## Classification

~~~text
classification:
  PHASE-B1W-D-INTERSTEP-CLAIM-WINDOW-FENCE-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

B0:
  CLOSED

B1 pure/default-off:
  REVIEW PASS

fence state machine:
  FROZEN

vector-domain scope:
  one global retained-domain fence
  FROZEN

window identity:
  opaque, immutable, domain-lifetime unique
  FROZEN

claim-window / P2 separation:
  F1 / outside P2
  FROZEN

production request window binding:
  W2 / immutable runtime admission envelope
  FROZEN

physical-step admission:
  S4 / caller-close plus environment validation handshake
  FROZEN

window-open owner:
  O1 / synchronous runtime coordinator
  FROZEN

active physical-step admission identity:
  REQUIRED

reset admission:
  explicit full-domain synchronous-call admission
  FROZEN

autoreset:
  remains inside STEP_IN_FLIGHT; never opens a window
  FROZEN

terminal behavior:
  G2 selected-row claim block plus R3 global next-step block
  FROZEN

abnormal step/reset exit:
  no reopen; existing coordinator/domain fail-stop authority
  FROZEN

control-action order:
  effective ownership -> close window -> continuous action -> env.step
  FROZEN

B1 semantic changes:
  none

frozen Phase-A/B0 changes:
  none

Python/test/runtime changes:
  none

environment/wrapper/HARL wiring:
  none

implementation:
  none

runtime readiness:
  blocked

numeric TBD:
  unresolved

training/playback/evaluation:
  not run

commit:
  none
~~~

This is a documentation-only targeted design. It freezes the missing
production concurrency protocol without implementing it. No STOP condition was
triggered: the protocol can be implemented later without changing Isaac Lab
core, P2, pure B1, lifecycle facts/results, or Phase-A DTOs.

## Scope and evidence basis

The design preserves the reviewed authority stack:

~~~text
one retained EventProfileLifecycleRuntimeDomain
  one domain operation/admission serialization lock
  one LifecycleAuthorityTransactionCoordinator
  one coordinator publication lock and poison authority
  one LifecycleStateStore identity and writer capability
  one P2 current-publication pointer
~~~

The required B0 closeout, B0-3I4 integration, B0-3I4-R smoke, B1D design, B1
implementation report, current handoff, and the actual production sources were
read. The source audit established these concrete boundaries:

- `DirectMARLEnv.reset()` calls full-domain `_reset_idx()`, then constructs
  observations, then returns.
- `DirectMARLEnv.step()` converts actions to the environment device and may
  apply action noise before `_pre_physics_step()`.
- It then performs physics, done/finalization, reward, internal autoreset,
  interval events, observation/noise construction, and only then returns.
- The event route rejects action noise today, but fence correctness does not
  depend on that current configuration.
- Event `_pre_physics_step()` currently begins with R3, then mutates action and
  high-level task-space buffers.
- Event `_reset_idx()` is shared by initial reset, standalone reset, and
  autoreset, so it cannot own window opening.
- The current wrapper resolves its assignment proposal and constructs
  continuous environment actions before calling `env.step()`.
- The B1 operation lock serializes claim, lifecycle finalization, and episode
  rebuild, but is released throughout the earlier action/physics interval.

These facts reject S3 as the primary fence and support a split S4 handshake.
They do not create a control-order STOP: future narrow wiring can insert step
admission after effective assignment is final and before
`assignment_to_env_actions()`; the current wrapper is not production-wired to
B1 and is not modified by this phase.

## Final architectural verdict table

| Question | Frozen verdict |
|---|---|
| Fence scope | one full vector-domain fence; claims may still select subsets |
| Fence states | `PREBOOTSTRAP_CLOSED`, `OPEN`, `STEP_IN_FLIGHT`, `RESET_IN_FLIGHT`, derived `FAULTED` |
| Window identity | opaque immutable factory object; unique for domain lifetime; never reused |
| Window location | F1, retained runtime-admission state outside P2 and StateStore |
| Production request binding | W2, `RuntimeClaimAdmissionEnvelope` around the unchanged B1 request |
| Step architecture | S4, caller closes before continuous-action generation; environment validates exact active admission |
| Open owner | O1, synchronous runtime coordinator or dedicated smoke coordinator |
| Step admission identity | required, exact-domain and single-use |
| Reset admission | explicit full-domain admission from prebootstrap or OPEN |
| Internal autoreset | remains part of the active step; never opens or replaces a window |
| Terminal slot while OPEN | allowed; G2 blocks selected rows and R3 blocks the next global step |
| R3 order | under admission serialization, check first; failure leaves the same OPEN window |
| Step failure | no reopen; poison/fail-stop or remain in-flight if the call hangs |
| Reset failure | no reopen; poison/fail-stop or remain in-flight if the call hangs |
| StateStore/P2 effect | none from window/admission transitions |

## What the fence is and is not

The fence answers one question:

> May assignment-owned live state be changed at this instant?

It is a concurrency/admission capability. It is not an assignment tick,
scheduler opportunity, retry cadence, policy action, proposal identity,
physical-transition generation, lifecycle event, or StateStore transaction.

One synchronous `DirectMARLEnv.step()` advances all retained rows. Therefore
the fence is global to the retained vector domain:

~~~text
STEP_IN_FLIGHT or RESET_IN_FLIGHT
  -> production claims forbidden for every row

OPEN
  -> a claim transaction may still select any legal subset K
~~~

No row-local physical-step window is introduced.

## Exact state machine

The retained domain owns the phase state under its operation/admission lock.
`FAULTED` is not an independent health flag: it is the fence projection of the
existing coordinator/domain poison authority.

~~~text
construction
  -> PREBOOTSTRAP_CLOSED

PREBOOTSTRAP_CLOSED
  -- begin admitted initial full reset --> RESET_IN_FLIGHT(R0)

OPEN(Wk)
  -- begin admitted physical step, R3 passes --> STEP_IN_FLIGHT(Ak, source=Wk)
  -- begin admitted standalone full reset --> RESET_IN_FLIGHT(Rk, source=Wk)
  -- claim commit --> OPEN(Wk)
  -- terminal ack --> OPEN(Wk)
  -- R3 admission rejection --> OPEN(Wk)

STEP_IN_FLIGHT(Ak)
  -- complete external env.step return --> OPEN(Wk+1)
  -- signalled abnormal exit/poison --> FAULTED
  -- hang --> remains STEP_IN_FLIGHT; teardown required

RESET_IN_FLIGHT(Rk)
  -- complete external env.reset return --> OPEN(Wk+1)
  -- signalled abnormal exit/poison --> FAULTED
  -- hang --> remains RESET_IN_FLIGHT; teardown required

any phase with existing coordinator poison
  -> FAULTED
~~~

Forbidden transitions include direct prebootstrap-to-OPEN, raw OPEN-to-OPEN
replacement, an autoreset-driven OPEN, claim-driven window replacement,
ack-driven window replacement, and any FAULTED recovery. Teardown constructs a
new domain; it does not repair the old one.

## Window identity

Each `OPEN` interval owns an immutable private `_ClaimWindowIdentity` created
by the domain factory. It binds the exact domain identity and a monotonic
domain-lifetime serial. It is never RNG-derived, reused, caller-constructed, or
accepted by value equality. Serial gaps are legal and carry no cadence or
scheduling meaning.

The first identity is created only after the first admitted external reset has
fully returned and its success is explicitly confirmed. A new identity is
created only after:

- a successfully returned external physical step; or
- a successfully returned admitted standalone reset.

Assignment commits, terminal reads/acks, current reads, R3 rejection, and
no-op time between calls do not replace the identity. Multiple commits can
therefore share Wk while P2 identity and Store version advance independently.

## F1: runtime admission remains outside P2

P2 remains the sole semantic current-state publication:

~~~text
state + episode/transition generations + per-row provenance
~~~

The fence remains retained-domain runtime-admission state. Opening, closing,
validating, or completing a window/admission:

- does not swap StateStore;
- does not increment Store version;
- does not allocate a P2 publication identity;
- does not change episode or transition generations;
- does not fabricate assignment or lifecycle provenance;
- does not modify a lifecycle result or facts DTO.

Claims bind P2 and the runtime window separately. F2 is rejected because it
would create semantic publications for concurrency-only transitions and blur
the already frozen P2 provenance model.

## W2: production claim admission envelope

Pure B1 remains unchanged. Its dormant `InitialClaimRequest`, token registry,
consume-once behavior, P2 binding, C2 semantics, and G2 checks do not acquire a
window field.

Future production wiring adds a private immutable factory-only envelope:

~~~text
RuntimeClaimAdmissionEnvelope
  exact retained domain identity
  exact InitialClaimRequest object
  exact OPEN window object identity
  opaque envelope identity/integrity binding
~~~

The production claim port, not the pure port, creates and commits this
envelope. Preparation executes under the domain operation/admission lock:

1. require the existing coordinator is healthy;
2. require exact `OPEN(Wk)`;
3. invoke the already-locked private B1 request preparation route;
4. bind the returned exact request to Wk;
5. release without changing window, P2, Store, or generations.

Commit executes under the same lock:

1. validate exact envelope, domain, request, and Wk identity;
2. require the state is still the same `OPEN(Wk)`;
3. invoke the existing private B1 commit route while retaining the operation
   lock;
4. let B1 revalidate exact P2/current Store/G2/context and commit atomically;
5. return the unchanged B1 effective artifact; keep Wk OPEN.

The production route must call an already-locked private coordinator/domain
primitive; it must not call the public dormant port while holding the same
non-reentrant operation lock. No `RLock` is introduced.

An envelope prepared in W1 is permanently invalid once W1 closes. It cannot be
rebased or rebound to W2 even if P2 happens to be object-identical. Rejection
does not consume the underlying B1 context; the immutable old-window binding
makes it permanently non-committable. No cancellation API is required for this
slice; abandoned contexts remain domain-lifetime resources under the existing
B1 policy.

Typed failure priority is frozen as follows:

~~~text
coordinator/domain poisoned:
  existing runtime poison failure wins

production prepare while STEP_IN_FLIGHT:
  runtime_step_in_flight

production prepare while PREBOOTSTRAP_CLOSED or RESET_IN_FLIGHT:
  claim_window_not_open

production envelope commit when its exact W is not the current OPEN W:
  stale_claim_window

foreign/altered envelope:
  claim_window_context
~~~

All are fail-closed. The port does not wait, poll, queue, cancel, rebase, or
retry automatically.

## Shared linearization boundary

Claim prepare/commit, step admission, and standalone reset admission compete
for the same retained-domain operation/admission lock. The retained lock order
remains:

~~~text
domain operation/admission lock
  -> coordinator publication lock
     -> StateStore internal lock
~~~

If a claim commit acquires first, it completes fully, publishes new P2, and
releases before step/reset admission captures the new baseline and closes W.
If step/reset admission acquires first, it closes W atomically before release;
the later claim rejects before mutation. A prepare that finishes before step
admission still requires an exact-window check at commit and therefore cannot
cross the close boundary.

## S4 physical-step admission handshake

S4 is selected. S1 alone would close before entering `env.step()` but could be
too late if continuous control was already derived. S2 would require an
environment `step()` override and still would not cover caller-side control
generation. S3 is too late because base `DirectMARLEnv.step()` already handles
actions before the task hook. S4 covers both caller and environment boundaries
without changing Isaac Lab core.

The future narrow port is conceptualized as:

~~~text
with step_admission_port.admit_physical_step() as admission:
    env_actions = build_continuous_action_from(admission.admitted_publication)
    result = env.step(env_actions)
    admission.commit_successful_return()
~~~

`admit_physical_step()` performs, under operation/admission then publication
locking:

1. require healthy `OPEN(Wk)`;
2. perform the primary full-domain R3 terminal-slot check;
3. on R3 failure, reject and leave the exact same Wk OPEN;
4. capture exact current P2 object/identity and Store version;
5. create `_PhysicalStepAdmission Ak` bound to the domain, Wk, P2, version,
   and synchronous call context;
6. atomically transition `OPEN(Wk) -> STEP_IN_FLIGHT(Ak)`;
7. release the locks before control construction and physics.

The close therefore occurs before continuous-action construction, device
conversion, action noise, `_pre_physics_step()`, task-space mutation, and
physics. No production claim can commit after step admission because every
production claim must first reacquire the operation/admission lock and observe
`STEP_IN_FLIGHT`.

## Active admission identity and environment validation

The active `_PhysicalStepAdmission` is required. It is immutable,
factory/capability-bound, domain-lifetime unique, single-use, and binds:

~~~text
exact retained domain
exact source OPEN window Wk
exact admitted P2 object and publication identity
exact admitted Store version
exact synchronous call scope
environment-entry validation latch
physical-finalization validation latch
successful-return completion latch
~~~

The admission context installs an unforgeable call-local binding for the
synchronous caller. The event environment's first `_pre_physics_step()` action
uses a narrow validation port to require that the call-local identity is the
exact active Ak and to consume its one environment-entry latch. A foreign
thread/call, raw `env.step()`, duplicate step in one context, stale callback,
or reuse after completion rejects.

The existing R3 statement remains in that first hook as a defensive invariant
check. It verifies both the exact active Ak and the absence of an impossible
terminal-slot contradiction; it is no longer the primary window-closing gate.
Action device conversion occurs before this hook in Isaac Lab, but claims were
already closed before the action was constructed, so that ordering is safe.

The environment I3 finalization port also requires the same exact active Ak and
consumes the one finalization latch before capturing execution prestate. This
associates lifecycle finalization with the admitted P2/Store baseline without
adding Ak to `ExecutionTransitionFacts` or any frozen DTO.

`commit_successful_return()` is accepted exactly once only after the
environment-entry and physical-finalization latches were satisfied and the
Python `env.step()` call returned normally. Under the operation/admission lock
it rechecks exact Ak and coordinator health, marks Ak complete, creates Wk+1,
and transitions to OPEN. Context `__exit__`, `__del__`, garbage collection, or
weak references never imply success.

## Exact control and step order

Future production sequencing is frozen as:

~~~text
previous external reset/step returned and was explicitly completed
  -> OPEN Wk
  -> read exact P2
  -> optional assignment proposal/scheduler/resolver work
  -> zero or more Wk-bound claim commits
  -> terminal capture/ack as required
  -> begin step admission; primary R3; atomically close Wk
  -> Ak binds final current P2 and Store version
  -> generate/finalize continuous physical control from Ak's ownership
  -> DirectMARLEnv.step(actions)
       device conversion / optional noise
       first task hook validates exact Ak and defensive R3
       action/task-space mutation and physics
       I3 finalization validates exact Ak
       reward/done/bookkeeping
       any internal autoreset remains inside Ak
       observations/noise
       synchronous return
  -> explicit successful-return completion
  -> OPEN Wk+1
~~~

The external HARL/discrete action is an assignment-policy proposal and may be
decoded while Wk is OPEN. It is not the continuous robot control action. The
continuous action must be derived after Ak captures final effective ownership.
The current wrapper's `assignment_to_env_actions()` location must move inside
the later admission context when production B1 wiring is authorized. That is a
future narrow integration change, not a contradiction and not authorized now.

## Standalone reset admission

Standalone direct-environment reset uses a parallel explicit synchronous-call
context. A wrapper or dedicated smoke coordinator must call:

~~~text
with reset_admission_port.admit_full_reset() as admission:
    result = env.reset(...)
    admission.commit_successful_return()
~~~

Admission is allowed from `PREBOOTSTRAP_CLOSED` for the first reset and from
`OPEN(Wk)` for later standalone full reset. It acquires the same operation /
admission serialization, creates a unique `_StandaloneResetAdmission`, and
atomically enters `RESET_IN_FLIGHT` before `DirectMARLEnv.reset()` is called.
A reset admitted from OPEN permanently closes Wk.

At event `_reset_idx()` entry, the episode-rebuild port verifies either:

- the exact active standalone reset admission; or
- the exact active physical-step admission for an internal autoreset.

A raw external reset or direct `_reset_idx()` call while OPEN has neither and
rejects before reset mutation. Current `DirectMARLEnv.reset()` is full-domain;
there is no supported public standalone partial-reset entrypoint. Private
row-selected `_reset_idx()` remains valid only as autoreset within an admitted
step. Any future public partial reset requires a targeted review.

For standalone reset, native reset, I1 rebuild, scan-buffer reset, and
observation construction all finish while `RESET_IN_FLIGHT`. Only after the
external `env.reset()` call returns normally and explicit success is committed
does the admission create the first/new OPEN window. I1 never opens a window.

Standalone reset is not R3-blocked by an occupied historical terminal slot:
the frozen B0 store permits a slot to survive reset. After return, the window
may be OPEN with that slot still occupied; G2 and R3 continue to enforce their
respective boundaries.

## Autoreset

Internal autoreset is part of the already admitted outer physical step:

~~~text
STEP_IN_FLIGHT(Ak)
  -> terminal lifecycle publication and slot
  -> selected-row I1 episode rebuild
  -> post-reset observation
  -> external step return
  -> explicit completion
  -> OPEN Wk+1
~~~

Episode-rebuild success does not create or open a window. This remains true
for one or many reset rows and prevents assignment from entering between
terminal finalization, reset, reward/observation completion, and external
return.

## Terminal slots, G2, R3, and acknowledgement

The selected combination is the existing G2 plus R3 model:

~~~text
after a terminal step returns:
  OPEN Wk+1 may coexist with occupied terminal rows

claim selecting occupied row:
  G2 rejects the whole C2 request

claim selecting only other rows:
  may commit if every other B1/window check passes

next global physical-step admission:
  primary R3 rejects and leaves Wk+1 OPEN

exact terminal ack:
  removes only the slot; Wk+1 remains the same identity

retry step admission:
  may now close Wk+1
~~~

Terminal acknowledgement never opens, closes, or replaces a window and does
not change P2, Store version, or generations. If ack clears a selected row's
G2 block while P2 and the window remain exact-current, the same unconsumed
production envelope may be explicitly retried under existing B1 semantics.
Ack may linearize under the publication lock while a step/reset is in flight,
but it never reopens claims.

## Multiple claims and outstanding requests

Multiple successful claims in one window are legal:

~~~text
OPEN W1 / P2 v10
  -> claim A -> P2 v11 / W1
  -> recapture claim B from v11 -> P2 v12 / W1
  -> begin step -> close W1
~~~

Multiple outstanding envelopes may bind W1 and the same P2. The first
successful B1 commit changes global Store/P2 identity; competitors reject as
stale source. If no claim commits and step/reset closes W1, all W1 envelopes
become permanently invalid because of stale window. Requests never carry into
W2 automatically.

A no-op inter-step interval is equally legal: Wk may contain zero claim
commits before the next admitted step. OPEN grants safety, not a requirement or
cadence to schedule assignment work.

## Abnormal exit and the one health authority

Once step/reset admission closes a window, no exception path automatically
reopens it. If action construction, environment entry, physics, lifecycle
finalization, reset, bookkeeping, observations, or explicit completion raises,
the admission context reports failure through a narrow domain capability that
sets the existing coordinator/domain poison authority. Fence state then reads
as derived `FAULTED`; it is not a second recoverable poison bit.

If the coordinator has already poisoned during lifecycle or bookkeeping work,
the admission completion observes that same authority and cannot open a
window. No rollback, guessed recovery, alternate publication, or retry occurs.
If the synchronous call hangs and no failure callback can run, the phase stays
`STEP_IN_FLIGHT` or `RESET_IN_FLIGHT`; claims remain closed and external
watchdog/teardown policy is required.

Already published immutable history remains readable only under the existing
poison rules; it cannot authorize continuation.

## Narrow capability surface

Future implementation should expose distinct capabilities:

~~~text
production claim port
  prepare/commit RuntimeClaimAdmissionEnvelope only

physical-step admission port
  create one capability-bound synchronous admission context

standalone reset admission port
  create one capability-bound synchronous reset context

environment validation port
  validate exact active call admission at step/reset/finalization boundaries

terminal consumer port
  unchanged exact read/ack only
~~~

No caller receives the fence state writer, allocator, raw identity factory,
`open_window()`, `close_window()`, `set_state()`, coordinator lock, Store,
writer capability, or arbitrary completion callback. Wrapper and smoke helper
orchestrate calls; neither becomes lifecycle authority.

The port can be driven by a future HARL wrapper or by a dedicated direct-
environment smoke coordinator. Fence correctness therefore has no dependency
on implementing scheduler, resolver, HARL learner transport, or a policy.

## Physical execution consistency proof

The design closes the original mismatch:

1. All assignment commits occur while exact Wk is OPEN.
2. Begin-step admission competes with those commits under the same lock.
3. Ak atomically closes Wk and captures final P2/Store ownership.
4. No later production claim can pass while Ak is active.
5. Continuous control is derived from Ak's captured effective ownership.
6. Environment entry and I3 finalization validate the exact same Ak.
7. Therefore the physical action, execution interval, and lifecycle prestate
   all refer to the final assignment baseline admitted for that step.

Lifecycle finalization and internal episode rebuild remain allowed because
they close the same admitted transition. Future transfer/preemption or other
assignment-owned writers must inherit this fence or undergo targeted review.

## Deterministic concurrency matrix

| Race | Linearized result |
|---|---|
| claim commit vs step admission | winner holds operation/admission lock; claim-first is visible to Ak, step-first makes claim stale-window |
| claim prepare vs step admission | prepare may return Wk envelope; commit must reject if Wk closed |
| claim commit vs standalone reset | claim-first completes then reset may erase it normally; reset-first closes and rejects claim |
| step admission vs terminal ack | publication lock orders R3 with ack; occupied-first rejects without closing, ack-first permits close |
| claim vs terminal ack | publication lock plus G2 orders them; ack may unblock exact still-current envelope |
| step completion vs stale callback | exact Ak and single-use completion latch reject duplicates |
| raw concurrent env.step | missing/foreign call-local Ak rejects at the first environment hook |
| autoreset vs claim | phase remains STEP_IN_FLIGHT, so claim rejects |

Future tests use `threading.Event`, barriers, and explicit checkpoints; no
sleep-based race establishes correctness.

## Future pure implementation test matrix

A separately authorized fence implementation must pass at least:

1. **W-T1** construction is `PREBOOTSTRAP_CLOSED`; production prepare rejects.
2. **W-T2** admitted first full reset opens exactly one first window only after
   external return confirmation.
3. **W-T3** multiple successful claims change P2/version but retain one window
   identity.
4. **W-T4** begin physical-step admission atomically closes the exact window.
5. **W-T5** claim prepare/commit after close rejects before mutation.
6. **W-T6** an envelope from W1 cannot commit during the step or in W2 and is
   not rebound or consumed by that rejection.
7. **W-T7** deterministic claim-versus-step interlocks prove both lock orders.
8. **W-T8** normal step return plus explicit completion opens exactly W2.
9. **W-T9** autoreset/I1 completion cannot open early.
10. **W-T10** standalone reset closes W, stays closed through observations,
    and opens a new identity only after external return confirmation.
11. **W-T11** deterministic reset-versus-claim interlocks prove both orders.
12. **W-T12** OPEN plus selected occupied terminal row preserves G2 rejection.
13. **W-T13** OPEN plus unselected occupied row permits a legal other-row claim.
14. **W-T14** R3 admission rejection leaves the exact same window OPEN.
15. **W-T15** exact terminal ack creates no window identity.
16. **W-T16** ack permits explicit retry in the same window when P2 is unchanged.
17. **W-T17** step/action/observation exception never reopens; shared poison or
    in-flight fail-stop is observed.
18. **W-T18** reset exception never reopens and uses the same health authority.
19. **W-T19** active step/reset admission identity and entry/completion latches
    are exact, foreign-resistant, and single-use.
20. **W-T20** every fence transition leaves StateStore, episode generation,
    transition generation, and lifecycle result unchanged.
21. **W-T21** opening/closing alone leaves P2 object/publication identity exact.
22. **W-T22** no raw open/close/state-writer/identity-factory capability leaks.
23. **W-T23** all B1 and B0 regressions remain unchanged, including pure B1
    without a production envelope.

Additional static oracles must verify the caller closes before continuous
action construction, the first environment hook validates Ak, I3 validates
the same Ak, I1 never opens, and no Isaac Lab core edit exists.

## Future real-runtime smoke matrix

The later authorized Isaac smoke must show, with flushed stage evidence:

~~~text
admitted reset returns -> OPEN W1
production claim succeeds -> P2 changes, W1 unchanged
begin step -> STEP_IN_FLIGHT A1
continuous action derived from A1 publication
claim attempt while A1 active -> typed rejection, no mutation
physical step returns -> explicit completion -> OPEN W2
~~~

The terminal path must additionally show:

~~~text
terminal step + internal autoreset -> no early OPEN
external return -> OPEN Wnext with terminal slot retained
G2 blocks that row but permits legal other-row claim
R3 blocks next step and leaves Wnext OPEN
exact ack leaves the same Wnext
next admitted step succeeds
~~~

This smoke is future evidence only. It is not run in B1W-D.

## Twelve required answers

1. **What is the window?** A global retained-domain concurrency capability for
   assignment-owned mutations. It is not a clock, tick, proposal, scheduler,
   or physical transition.
2. **When does it first open?** Only after an admitted first full reset has
   completed I1, observations, external return, and explicit success.
3. **Does claim success create a window?** No. It changes P2/Store version and
   retains the exact window identity.
4. **Where does the next step close it?** At caller-side S4 begin admission,
   before continuous-action generation and before entering `env.step()`.
5. **How does the physical step prove admission?** A call-local exact Ak is
   validated once at the first environment hook and again by I3 finalization.
6. **Who reopens after return?** The O1 synchronous coordinator explicitly
   completes Ak after normal `env.step()` return.
7. **Why can autoreset not open early?** I1 only rebuilds semantic state; the
   fence remains `STEP_IN_FLIGHT` until outer call completion.
8. **How does standalone reset work?** Explicit reset admission closes/prevents
   claims before `env.reset()` and opens a new window only after normal return.
9. **Can a slot coexist with OPEN?** Yes. This preserves G2 per-row claims and
   R3 global next-step blocking.
10. **How do G2 and R3 coexist?** G2 is checked on selected claim rows; R3 is
    checked globally before the OPEN-to-STEP transition and failure keeps OPEN.
11. **Why is a W1 request invalid in W2?** The immutable production envelope
    binds exact W1 identity; identities are never reused or rebound.
12. **How is execution tied to final ownership?** Ak closes the window after
    all claims, captures final P2/Store, gates control construction, and is
    verified by environment entry and finalization.

## STOP-condition audit

| STOP condition | Result | Reason |
|---|---|---|
| Step-admission boundary gap | not triggered | S4 closes before control construction and needs no Isaac core edit |
| Control-order integration gap | not triggered | later narrow wrapper wiring can move continuous-action construction inside Ak |
| Second health authority | not triggered | `FAULTED` derives from the existing coordinator/domain poison authority |
| P2 pollution | not triggered | F1 keeps admission state entirely outside P2/Store |
| B1 contract rewrite | not triggered | W2 wraps the unchanged pure request and effective artifact |
| Wrapper/HARL dependency | not triggered | the domain ports can be driven by a dedicated smoke coordinator |

## Deferred and prohibited work

B1W-D does not implement or authorize:

- the fence objects, ports, contexts, or tests;
- environment, wrapper, resolver, controller, or HARL wiring;
- scheduler opportunities, assignment cadence, proposal sampling, or retry;
- transfer, preemption, swaps, chains, or lifecycle phase progression;
- mask, DVM, observation, buffer, learner, or terminal sidecar transport;
- runtime-readiness activation;
- real terminal Isaac smoke;
- training, playback, evaluation, or commit.

All eleven numeric TBD values remain unresolved:

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

Transformer, Set Transformer, GNN, arbitrary M/N policy,
variable-cardinality checkpoint, and related work remain outside scope.

## Documentation boundary and next gate

The B1W-D delta is limited to this report and the concise top-level
`TASK_PROGRESS.md`. No archive is required: the handoff can be updated in place
without losing the linked B0/B1 history.

The next gate is GPT/user review. Even after review, production assignment
wiring and runtime readiness remain blocked until a separately authorized
fence implementation and its pure/static verification complete. This report
does not authorize that implementation.
