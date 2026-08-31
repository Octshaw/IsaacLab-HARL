# TASK_PROGRESS

## Current status

```text
classification:
  PHASE-B2-D-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

design:
  REVISED / AWAITING GPT REVIEW

Phase A:
  final review passed; previously committed by user
Lifecycle Runtime Backbone + Wrapper Integration:
  COMMITTED / CLOSED CHECKPOINT AT 14993dee344bade0230d2eb97b5f22171331f44a
B0 lifecycle/direct-environment foundation:
  CLOSED
focused Isaac nonterminal runtime:
  B0 baseline PASS; B1W-I2 admitted O1 route PASS
real-Isaac terminal transition:
  VERIFIED through direct HARL-independent O1

wrapper event route:
  REAL WR-C RESET / CONTINUATION / PRIVATE PROPOSAL-M1 / TERMINAL HANDOFF VERIFIED
  activation remains blocked
proposal -> effective B1 commit:
  IMPLEMENTED / PURE-STATIC VERIFIED
terminal wrapper handoff:
  BOUNDED IMMUTABLE HISTORICAL COPY / IMPLEMENTED
Phase-B entry:
  CONDITIONAL PASS
  pure/default-off B1 complete
  production activation conditions remain blocked
Phase B overall:
  NOT COMPLETE
policy/learner readiness architecture design:
  B2-D TARGETED REVISION COMPLETE / AWAITING GPT REVIEW
  DESIGN ONLY / NO IMPLEMENTATION
implementation:
  NOT STARTED

B1D:
  review pass / frozen
B1 implementation:
  pure / dormant / default-off complete
B1W-D:
  review pass / frozen
B1W implementation:
  pure / dormant / default-off complete
  B1W-I1 exact-event production-boundary wiring implemented
B1W-I-D: review pass / frozen
B1W-I1:
  REVIEW PASS / CLOSED
environment admission validation: exact event profile implemented
generic synchronous coordinator: implemented / HARL-independent
real Isaac admitted nonterminal runtime: VERIFIED
B1W-I2: REVIEW PASS / CLOSED
B1W-I3: REVIEW PASS / CLOSED
B1W-I4-D: REVIEW PASS / FROZEN
B1W-I4-D-R: REVIEW PASS / CLOSED
conflict candidate model: EXPLICIT-FEASIBILITY-FIRST / FROZEN
terminal multi-row ACK model: ATOMIC_BATCH_EXACT_ACK / FROZEN
B1W-I4-1:
  REVIEW PASS / CLOSED
B1W-I4-2:
  REVIEW PASS / CLOSED
B1W-I4-3:
  REVIEW PASS / CLOSED
B1W-I4-4:
  GPT REVIEW PASS / CLOSED
  FOCUSED REAL-ISAAC WRAPPER INTEGRATION VERIFIED
event proposal adapter: IMPLEMENTED
explicit-feasibility-first: IMPLEMENTED / PURE-STATIC VERIFIED
conflict arbitration: IMPLEMENTED / PURE-STATIC VERIFIED
M1 zero-or-one B1 commit: IMPLEMENTED / PURE-STATIC VERIFIED
event composition: IMPLEMENTED / activation still blocked
event admitted wrapper reset: REAL ISAAC VERIFIED
no-new-claim continuation: REAL ISAAC VERIFIED
real proposal/M1: VERIFIED
real final P2 -> Ak -> controller: VERIFIED
continuation: REAL ISAAC VERIFIED / PRESERVED
P2 sole authority: PRESERVED
Ak-only controller: PRESERVED
stateful legacy resolver exact-event route: NOT CONSTRUCTED / NOT USED
public learned-policy event step:
  BLOCKED
  lifecycle actor/shared observation identity incomplete
  lifecycle action mask / DVM incomplete
  forced-row sampling not integrated
terminal direct O1 capture/single-key ACK:
  IMPLEMENTED BY B1W-I3 / PRESERVED
terminal wrapper historical copy:
  REAL ISAAC VERIFIED / NO RAW ARTIFACT RETENTION
ATOMIC_BATCH_EXACT_ACK:
  REAL ISAAC VERIFIED / ALL-OR-NONE / ONE SLOT-MAP PUBLICATION
W-T1:
  PRESERVED
ACK-A:
  IMPLEMENTED AT WRAPPER/FACADE PRIVATE ROUTE
historical/current separation:
  REAL ISAAC VERIFIED
real terminal/autoreset: VERIFIED
real post-ACK recovery: VERIFIED
terminal critic sidecar:
  NOT IMPLEMENTED / READINESS BLOCKER
event-profile runtime readiness:
  BLOCKED; wrapper/readiness gates remain
policy readiness:
  BLOCKED
learner readiness:
  BLOCKED
training readiness:
  BLOCKED
training authorization:
  NOT AUTHORIZED

current publication architecture:
  P2 discriminated per-row provenance aggregate
assignment tick clock:
  NOT REQUIRED
terminal gating / granularity:
  G2 per-env / C2 batched independent claims

inter-step fence design:
  global vector-domain / S4 split admission / O1 open owner
  W2 production envelope / F1 outside P2
inter-step fence implementation:
  pure/default-off implemented; FAULTED derives from existing poison

Phase C/D/E:
  not entered / not authorized

training/playback/evaluation:
  not run
Isaac/HARL in B2-D:
  NOT RUN

TASK_PROGRESS consistency: PASS
Python: NO PRODUCTION MODIFICATIONS IN B2-D; MARKDOWN DESIGN ONLY
tests: NOT RUN IN B2-D; PRIOR I4-4 EVIDENCE NOT RERUN

current phase delta: targeted documentation revision of TIME_LIMIT projection,
                     HAPPO factor indexing, immutable I1/I2 bundle boundary,
                     identity/model-input separation, and I3/I5 slicing

commit: none
```

## Latest completed phase

B2-D targeted design revision is complete and awaits a second independent GPT
review. The first GPT classification was `PHASE-B2-D-CONDITIONAL-PASS`, not a
final review pass. The revised report
closes its five requested documentation issues: typed terminal audit versus
TIME_LIMIT bootstrap critic projection; canonical full-rollout `(t,env)` HAPPO
factor scatter; immutable I1 evidence snapshot versus I2 final decision bundle;
identity metadata versus model-input separation; and I3a/I3b plus I5a/I5b
implementation slicing. No Python, tests, Isaac, HARL, training, playback,
evaluation, checkpoint, readiness change, optimizer, or commit occurred.

The design keeps fixed M/N HAPPO/EP/feed-forward semantics and freezes P2 sole
authority, proposal/effective separation, Ak-only control, continuation,
terminal/current separation, copy-before-ACK, and default-off. It defines
NEEDS-only policy rows, deterministic EXECUTING continuation, deterministic
WAITING/UNAVAILABLE noop, and terminal no-row semantics. Installed HARL requires
repo-local subset sampling plus DVM-aware actor training/factor math;
`active_masks` alone is insufficient. TIME_LIMIT requires a typed pre-reset
bootstrap critic projection built from exact physical/finalized-P2 evidence;
final reason remains audit metadata and never leaks into that critic input.
True terminals retain audit evidence but do not bootstrap or trigger terminal
critic evaluation. Installed proper-time-limit math cannot supply this behavior.

No fundamental DirectMARLEnv/P2/Ak/variable-cardinality dependency gap was
found. The mandatory first implementation dependency is a versioned no-tick
schema reconciliation: Phase-A DTOs still name `assignment_tick_generation`,
while the committed runtime binds decisions to current P2 publication,
episode/transition, and exact OPEN-window identity and requires no tick. No new
clock or window-as-tick alias is permitted, and identity generations remain
validation metadata rather than model features. Public event step, policy/
learner/runtime/training readiness, and all implementation remain blocked
pending review.

B1W-I4-4 focused verification is GPT REVIEW PASS / CLOSED. A bounded headless
real-Isaac supervisor/worker smoke composed exactly one private event wrapper
over `ScanMobileManipulatorEnv` with E=2, M=3, N=12 on `cuda:0` and exact
`event_gated_local_mrta` identity. Real admitted reset produced canonical P2
episode 0 / transition -1 and OPEN W1. A real feasibility/cost snapshot drove
one task-disjoint M1/B1 batch, exactly one Store increment, final P2 -> Ak ->
controller assignment `[[9,-1,-1],[9,-1,-1]]`, finite CUDA actions, and a real
no-new-claim continuation.

Both rows then reached a bounded real terminal with exact keys `(0,0,3)` and
`(1,0,3)`. Same-Ak autoreset published current episode 1 while the wrapper
returned immutable episode 0 history and `optional_sidecar=None`. One atomic
batch exact ACK changed two occupied slots to zero without changing P2, Store,
generations, window, or poison. The next real step recovered to Store 8 /
transition 4 / OPEN window 5; the worker closed cleanly with exit code 0 and no
timeout.

The targeted I4-3/I4-2/I4-1/Phase-A/profile/B1/B1W/I1/I3/frozen matrix passes
213/213 in normal and `-I -B` modes. All 18 protected production SHA-256 values
match preflight exactly; `git diff --check`, empty-index verification, and smoke
`py_compile` pass. No production source changed in I4-4. No HARL, training,
playback, evaluation, or commit occurred. Public learned-policy event
`.step(actions)`, lifecycle observations, mask/DVM, forced-row sampling, critic
sidecar, learner transport, TIME_LIMIT GAE, and runtime readiness remain blocked.

B1W-I4-2 is REVIEW PASS / CLOSED. It adds a B-private pure proposal adapter and extends the private event
facade route through explicit feasibility-first arbitration, one task-disjoint
C2/M1 request, zero-or-one authoritative B1 artifact, final P2 capture, and the
existing O1 Ak-only physical admission. Decision evidence is bound to the exact
P2 publication identity, episode/transition generations, and OPEN-window
identity. Stale P2 or window evidence is rejected without rebinding.

Structural legality is evaluated before explicit physical feasibility. Cost is
ranking evidence only and cannot make an infeasible pair eligible. Eligible
finite candidates use minimum cost then lowest robot ID; an all-NaN/inf
already-feasible set uses lowest robot ID without infeasible re-entry. One
action batch produces no B1 artifact for K=0 or exactly one full-batch artifact
and Store increment for K>0. Mixed continuation plus new claim preserves the
existing owner while committing only the new claim. Wrapper caches, proposals,
winner masks, M1 requests, and artifacts never become controller authority;
physical control remains final P2 -> Ak -> controller.

The dedicated suite passes 22/22 in normal and `-I -B` modes. The full recorded
I4-2/I4-1/Phase-A/profile/B1/B1W/I1/I3/B0/frozen matrix passes 271 cases per
mode. Protected environment/controller/RL/B1/domain/fence/resolver/contracts/
training hashes are unchanged. Public event `.step(actions)` remains blocked
because lifecycle observation/mask identity is absent. Terminal wrapper copy
and atomic batch exact ACK remain deferred to I4-3. No Isaac, HARL, training,
playback, evaluation, runtime smoke, or commit occurred.

B1W-I4-1 is review pass / closed. Its facade-only reset and no-new-claim
continuation remain intact and continue to pass 15/15 in both modes.

B1W-I4-D-R resolves both conditional design issues without reopening WR-C,
W-T1, ACK-A, P2/Ak authority, continuation/noop semantics, M1 zero-or-one
batching, or default-off. Conflict handling is now explicitly
feasibility-first: P2 structural legality and the separate current physical
feasibility signal determine candidate eligibility; cost ranks only survivors.
Finite cost cannot rescue an infeasible pair. When an already-feasible conflict
set has no finite cost, lowest robot ID provides totality without re-entry.

Multi-row terminal delivery is now `ATOMIC_BATCH_EXACT_ACK`: after the full
bounded immutable copy validates, the narrow same-domain consumer path validates
the entire canonical exact-key tuple under the existing publication lock,
prepares exact stored return identities and the replacement slot map, then
performs one slot-map publication. Any row failure removes none; partial
successful ACK is impossible. Existing single-key ACK remains unchanged.
No Python, tests, Isaac, HARL, or implementation execution occurred in D-R.

B1W-I3 passed one bounded real-Isaac E=2 terminal route. A legal deterministic
initial claim was followed by admitted O1 physical steps until the existing
time-limit mechanism produced exact terminal transition generation 2 for both
rows. The same Ak finalized I3, installed two immutable slots, survived
autoreset to episode 1, returned, and completed to OPEN. O1 captured the exact
stored artifacts, a deliberate pre-ack step rejected neutrally through R3,
exact keys `(0,0,2)` and `(1,0,2)` were acknowledged, and the next real
nonterminal step completed to a new OPEN window without a stranded Ak.

The narrow production delta is confined to the existing terminal coordinator,
designated consumer port, and HARL-independent O1 facade. Discovery returns an
env-ID-ordered immutable tuple of the exact stored artifact objects under the
existing publication lock. Capture never acknowledges. O1 exposes separate
capture and exact-key ack methods and retains no terminal cache or second state
authority. Runtime readiness remains blocked.

B1W-I2 previously passed the bounded real-Isaac E=2 nonterminal admitted route
and is now review pass / closed.

B1W-I1 implements the B-private HARL-independent O1 coordinator and exact-event
environment validation for reset, step entry, I3, and internal autoreset. No
accepted B1W, B1, B0, or Phase-A contract changes.

```text
scope:       one global synchronous vector-domain fence
states:      PREBOOTSTRAP_CLOSED / OPEN / STEP_IN_FLIGHT /
             RESET_IN_FLIGHT / derived FAULTED
window:      opaque domain-lifetime identity; not an assignment tick
binding:     W2 immutable production envelope around unchanged B1 request
publication: F1 admission state outside P2 and StateStore
step:        S4 caller-close plus exact environment/I3 admission validation
open owner:  O1 synchronous runtime coordinator
control:     final P2 -> Ak -> Ak-derived action -> env.step
failure:     no reopen; existing coordinator/domain fail-stop authority
```

The first window opens only after an admitted reset explicitly completes.
Claims may commit multiple times in one window; they change P2/Store version,
not the window. Step admission checks R3 and atomically closes the window under
the same operation/admission lock used by claims. R3 failure keeps the same
window open. A successful step/reset creates the next window only after
explicit success in the pure protocol; internal autoreset never opens one.
The generic fake/direct call path admits reset before `env.reset()` and opens W1
only after return. O1 performs primary R3 and admits Ak before Ak-derived control
construction; event entry then performs exact-Ak validation followed by
defensive R3. I3 and autoreset validate the same Ak. Real Isaac has now verified
both the prior nonterminal path and the B1W-I3 terminal/autoreset/capture/ack/
recovery path.

An OPEN window may coexist with terminal slots. G2 blocks selected occupied
rows, R3 blocks the next global step, and exact ack changes neither P2 nor the
window. An envelope bound to W1 is permanently invalid after W1 closes and is
never rebound to W2.

## Active architecture / implementation path

The retained composition remains:

```text
resolved_assignment_profile
event_lifecycle_runtime_domain
  -> one domain operation lock
  -> one coordinator publication lock
  -> one LifecycleStateStore writer
```

The pure initial-claim deriver has no writer capability. The existing
coordinator remains the sole transaction/publication owner and owns the private
claim route. The domain owns a narrow request port and single-use request
registry. Its operation lock is also the implemented dormant fence's admission
linearization boundary. B1W-I1 implemented production-boundary validation,
B1W-I2 verified the real admitted nonterminal route, and B1W-I3 verified the
real terminal/autoreset/capture/ack/recovery route. No tick clock, second mutex,
StateStore, coordinator, or poison authority is introduced.

Private capabilities are separated into production claim, physical-step
admission, standalone-reset admission, environment validation, read-only
fence inspection, and terminal consumer ports. No raw open/close/state-writer
capability escapes. Fence state remains outside P2; `FAULTED` derives from the
existing poison authority.

Existing/default routes receive no event domain and retain legacy behavior.

The event environment retains lifecycle and admission-validation ports only.
O1 retains current-P2 read, production-claim, step/reset-admission, designated
terminal-consumer, and environment-call capabilities. The private I4
composition injects only a narrow facade into the exact-event wrapper; I4-2
extends that private path with proposal interpretation, explicit feasibility,
conflict arbitration, and M1/B1 routing. The wrapper retains neither the raw
domain nor O1. Formal activation remains blocked and event noise remains
prohibited.

## Terminal handoff

One immutable exact-generation artifact is stored per row. Exact designated ack
removes one slot; slots survive reset and reject invalid operations. No
overwrite, auto-ack, or optional sidecar exists. The designated consumer can
capture all pending exact stored artifacts as an immutable env-ID-ordered tuple;
capture is repeatable/read-only and does not reconstruct from reset P2.

## Publication and poison boundary

The coordinator holds one publication lock through Store/generation/P2/slot
installation; reads, terminal operations, and permission checks share it. Any
post-authority bookkeeping failure poisons without rollback, retry, auto-ack,
or normal continuation.

## Event environment order

```text
O1 primary step admission / R3 -> STEP_IN_FLIGHT Ak
Ak-bound continuous action construction -> env.step()
first event hook: exact active-Ak validation -> defensive R3 -> event mutation
physics -> episode counters -> staged report
exact same-Ak I3 validation -> lifecycle authority -> terminal publication if any
reward/bookkeeping -> optional internal autoreset under the same Ak
observation -> external return -> O1 explicit Ak success completion
OPEN next window
```

Primary R3 is the caller-side O1 begin-step admission before
`OPEN -> STEP_IN_FLIGHT`. Defensive R3 is the environment's first event hook,
after exact-Ak validation and before task mutation or physics.

The event constructor rejects non-`None` action noise before base environment
construction because DirectMARLEnv applies noise before the task hook.

The event detector does not mutate coverage or dwell before authority. Passive
non-owner candidates remain non-events. Coverage and reward evidence come from
the authoritative outcome.

Legacy `_update_scan_progress`, done, reward, and reset paths remain present
for the four existing/default profiles.

## Episode rebuild

Event `_reset_idx(selected)` wraps native reset and selected scan-buffer reset
inside `environment_port.episode_rebuild(...)`, then signals
`commit_physical_reset_complete()`.

```text
standalone reset: O1 admitted Rk -> reset-entry validation -> I1
                  -> external return -> explicit Rk completion -> OPEN
internal autoreset: same active Ak -> reset-entry validation -> I1
                    -> remain STEP_IN_FLIGHT -> outer return -> Ak completion
                    -> OPEN
```

The first reset advances episode `-1 -> 0`; partial/manual/autoreset use the
same primitive. Terminal slots survive rebuild. Native reset does not re-enter
a lifecycle port and no `RLock` was introduced.

## Verification

B1W-I4-2 accepted recorded verification (not rerun in B1W-I4-2-R):

```text
I4-2 dedicated normal / -I -B                   22/22 + 22/22
full recorded matrix normal / -I -B             271/271 + 271/271
dedicated facade/wrapper normal / -I -B        15/15 + 15/15
Phase-A default-off normal / -I -B             16/16 + 16/16
profile contract normal / -I -B                16/16 + 16/16
profile production wiring normal / -I -B       10/10 + 10/10
B1W-I3 terminal consumer normal / -I -B        13/13 + 13/13
B1W-I1 environment/O1 normal / -I -B           28/28 + 28/28
B1W fence normal / -I -B                       26/26 + 26/26
B1 initial claim normal / -I -B                23/23 + 23/23
B0-3I2 domain normal / -I -B                   12/12 + 12/12
B0-3I4 environment normal / -I -B              12/12 + 12/12
frozen transition/schema/event normal/-I -B    34/34 + 34/34
py_compile / diff / side effects               pass / pass / unchanged
protected production hashes                    exact
```

No Isaac/AppLauncher, real environment, HARL, training, playback, evaluation,
checkpoint, or readiness run occurred in I4-1.

## Key and changed files

B1W-I4-2 production/test/report delta:

```text
assignment_event_proposal_adapter.py
assignment_event_runtime_facade.py
assignment_event_profile_synchronous_runtime.py
assignment_harl_wrapper.py
scripts/environments/test_assignment_phase_b1w_i4_2_proposal_effective_commit_pure.py
AgentRead/20260824/PHASE_B1W_I4_2_PROPOSAL_INTERPRETATION_AND_EFFECTIVE_COMMIT_IMPLEMENTATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

B1W-I4-1 production/test/report delta:

```text
assignment_event_runtime_facade.py
assignment_event_profile_synchronous_runtime.py
assignment_harl_wrapper.py
scripts/environments/test_assignment_phase_b1w_i4_1_event_facade_wrapper_integration_pure.py
six existing pure/static boundary-oracle fixtures
AgentRead/20260823/PHASE_B1W_I4_1_EVENT_FACADE_COMPOSITION_RESET_CONTINUATION_IMPLEMENTATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

B1W-I3 production/test/report delta:

```text
assignment_lifecycle_transaction_runtime.py
assignment_event_profile_runtime_domain.py
assignment_event_profile_synchronous_runtime.py
scripts/environments/test_assignment_phase_b1w_i3_terminal_consumer_integration_pure.py
scripts/environments/test_assignment_phase_b1w_i3_real_isaac_terminal_smoke.py
scripts/environments/test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py
scripts/environments/test_assignment_phase_b1w_i2_real_isaac_nonterminal_smoke.py
scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
AgentRead/20260823/PHASE_B1W_I3_REAL_TERMINAL_CAPTURE_ACK_AND_RECOVERY_VERIFICATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

B1W-I1 implementation files remain:

```text
assignment_interstep_claim_window_runtime.py
assignment_event_profile_runtime_domain.py
assignment_event_profile_synchronous_runtime.py
scan_mobile_manipulator_env.py
scripts/environments/test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py
scripts/environments/test_assignment_phase_b1w_interstep_claim_window_fence_pure.py
scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
scripts/environments/test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py
scripts/environments/test_assignment_phase_b0_3i4_environment_integration.py
scripts/environments/test_assignment_phase_a_default_off_identity.py
AgentRead/20260822/PHASE_B1W_I1_ENVIRONMENT_VALIDATION_AND_SYNCHRONOUS_COORDINATOR_IMPLEMENTATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

No frozen contract, environment, training/runner, resolver/controller,
RL-interface, readiness, checkpoint, config/YAML, Isaac core, or
installed-package file changed in I4-1. Fixture edits only track the authorized
private composition boundary and wrapper digest. No TASK_PROGRESS archive was
needed.

## Detailed reports

Current:

```text
AgentRead/20260824/PHASE_B2_D_EVENT_PROFILE_POLICY_LEARNER_READINESS_ARCHITECTURE_DESIGN.md
AgentRead/20260824/PHASE_B1W_I4_4_FOCUSED_REAL_ISAAC_WRAPPER_INTEGRATION_VERIFICATION_REPORT.md
AgentRead/20260824/PHASE_B1W_I4_3_TERMINAL_WRAPPER_HISTORICAL_COPY_AND_ATOMIC_BATCH_ACK_IMPLEMENTATION_REPORT.md
AgentRead/20260824/PHASE_B1W_I4_2_PROPOSAL_INTERPRETATION_AND_EFFECTIVE_COMMIT_IMPLEMENTATION_REPORT.md
AgentRead/20260823/PHASE_B1W_I4_1_EVENT_FACADE_COMPOSITION_RESET_CONTINUATION_IMPLEMENTATION_REPORT.md
AgentRead/20260823/PHASE_B1W_I4_D_WRAPPER_FACADE_AND_EFFECTIVE_COMMIT_INTEGRATION_TARGETED_DESIGN.md
AgentRead/20260823/PHASE_B1W_I3_REAL_TERMINAL_CAPTURE_ACK_AND_RECOVERY_VERIFICATION_REPORT.md
AgentRead/20260822/PHASE_B1W_I2_FOCUSED_REAL_ISAAC_NONTERMINAL_SMOKE_VERIFICATION_REPORT.md
AgentRead/20260822/PHASE_B1W_I1_ENVIRONMENT_VALIDATION_AND_SYNCHRONOUS_COORDINATOR_IMPLEMENTATION_REPORT.md
AgentRead/20260822/PHASE_B1W_I_D_PRODUCTION_FENCE_INTEGRATION_TARGETED_DESIGN.md
AgentRead/20260821/PHASE_B1W_PURE_INTERSTEP_CLAIM_WINDOW_FENCE_IMPLEMENTATION_REPORT.md
AgentRead/20260821/PHASE_B1W_D_INTERSTEP_CLAIM_WINDOW_FENCE_TARGETED_DESIGN.md
AgentRead/20260821/PHASE_B1_PURE_INITIAL_CLAIM_TRANSACTION_IMPLEMENTATION_REPORT.md
AgentRead/20260821/PHASE_B1D_PURE_INITIAL_CLAIM_TRANSACTION_TARGETED_DESIGN.md
```

## Deferred / do not do

Until separately authorized:

```text
do not implement revised B2-D slices (I0/I1/I2/I3a/I3b/I4/I5a/I5b/I6)
or versioned schema reconciliation
do not flip event runtime readiness
environment admission-validation wiring and generic HARL-independent O1 are implemented
proposal interpretation / explicit-feasibility-first arbitration /
M1 B1 commit routing are implemented in the private exact-event path
terminal direct O1 capture/single-key ACK is implemented by B1W-I3
terminal wrapper historical copy and ATOMIC_BATCH_EXACT_ACK are implemented by B1W-I4-3
do not activate public learned-policy event step
do not add lifecycle actor/shared observations
do not add lifecycle action mask/DVM
do not modify forced-row runner behavior
do not add terminal critic sidecar
do not add learner buffer transport
do not select any of the 11 numeric TBD values
do not add Transformer/GNN/variable-cardinality support
do not run additional Isaac/AppLauncher smoke or HARL/training/playback/evaluation
do not commit
```

## Next action

B1W-I4-1 through B1W-I4-4 are REVIEW PASS / CLOSED and the Lifecycle Runtime
Backbone checkpoint is committed. B2-D policy/learner readiness architecture
targeted revision is complete and awaits a second independent GPT review; it is
not yet review-pass/frozen. Preserve WR-C, W-T1 / ACK-A, P2 sole authority,
proposal/effective separation, Ak-only controller source, S4/O1/W2/F1, G2/C2,
default-off behavior, fixed M/N, blocked public event `.step(actions)`, and
runtime/policy/learner/training readiness BLOCKED. Do not implement B2-I0 or any
later revised slice, run Isaac/HARL/training/playback/evaluation, perform an
optimizer update, choose numeric TBDs, change checkpoints, or commit. Wait for
the next explicit authorization.
