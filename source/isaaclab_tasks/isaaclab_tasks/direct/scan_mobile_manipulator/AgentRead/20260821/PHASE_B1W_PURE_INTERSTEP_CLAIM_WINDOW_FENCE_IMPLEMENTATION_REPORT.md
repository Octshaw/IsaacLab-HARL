# Phase B1W Pure Inter-Step Claim-Window Fence Implementation Report

## Classification

```text
classification:
  PHASE-B1W-PURE-INTERSTEP-CLAIM-WINDOW-FENCE-COMPLETE-AWAITING-GPT-REVIEW

B0:
  CLOSED
B1:
  REVIEW PASS
B1W-D:
  REVIEW PASS / FROZEN

global vector-domain fence:
  IMPLEMENTED
fence state machine:
  IMPLEMENTED
window identity:
  IMPLEMENTED
S4 admission capability:
  IMPLEMENTED FOR PURE/DEFAULT-OFF SCOPE
O1 synchronous completion:
  IMPLEMENTED FOR PURE/DEFAULT-OFF SCOPE
W2 production envelope:
  IMPLEMENTED / DORMANT
F1 admission/P2 separation:
  VERIFIED
physical-step admission identity:
  IMPLEMENTED
standalone-reset admission:
  IMPLEMENTED
autoreset no-open semantics:
  VERIFIED
G2/R3 interaction:
  VERIFIED
step/reset failure:
  FAIL-STOP VERIFIED
existing poison authority:
  REUSED
B1 semantics:
  UNCHANGED
P2 / Store / generation neutrality:
  VERIFIED

production environment validation wiring:
  NOT IMPLEMENTED
production wrapper orchestration:
  NOT IMPLEMENTED
continuous control ordering:
  NOT YET RUNTIME WIRED
real Isaac fence smoke:
  NOT RUN
runtime readiness:
  BLOCKED
training/playback/evaluation:
  NOT RUN
numeric TBD:
  unresolved
commit:
  none
```

This phase implements only the frozen B1W-D pure/default-off authority
foundation. It does not activate the fence in the real environment, wrapper,
resolver, controller, HARL, configuration, training, playback, or evaluation
paths.

## Repository boundary

```text
working directory: E:\Project\IsaacLab_HARL
branch:            main
starting HEAD:     912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:       912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             empty before and after B1W
worktree:          pre-existing uncommitted B0/B1/Phase-A work preserved
commit:            none
```

The existing dirty worktree was not normalized, reverted, or committed.
Environment and wrapper content remained byte-identical to their B1W
preflight snapshots.

## Changed and new files

Phase-owned runtime and test changes:

```text
NEW  assignment_interstep_claim_window_runtime.py
MOD  assignment_lifecycle_transaction_runtime.py
MOD  assignment_event_profile_runtime_domain.py
NEW  scripts/environments/test_assignment_phase_b1w_interstep_claim_window_fence_pure.py
MOD  scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
MOD  scripts/environments/test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py
NEW  AgentRead/20260821/PHASE_B1W_PURE_INTERSTEP_CLAIM_WINDOW_FENCE_IMPLEMENTATION_REPORT.md
MOD  AgentRead/TASK_PROGRESS.md
```

The two B0 runner changes update only their exact dormant-domain capability
inventory oracle. Their B0 semantic assertions are unchanged.

## Fence authority and state

Each retained event-profile runtime domain owns exactly one
`_InterStepClaimWindowFence`. The fence owns no mutex, StateStore, publication
pointer, terminal slot store, or independent poison bit. It is driven only
while the domain's existing operation lock is held.

The five-state projection is:

```text
PREBOOTSTRAP_CLOSED
OPEN(Wk)
STEP_IN_FLIGHT(Ak)
RESET_IN_FLIGHT(Ak)
FAULTED  (derived from the existing coordinator poison authority)
```

`FAULTED` is a read projection, not a second health writer. The fence has no
`_faulted` field. An admitted step/reset abnormal exit calls the existing
coordinator poison route and cannot reopen a window.

No raw public open/close writer exists. `_open_next_window()` is a private
event-completion primitive reachable only after the exact step/reset success
latches have been satisfied.

## Window and admission identities

Window identities, step/reset admission identities, and W2 envelope serials
are immutable, factory-only, domain-bound, monotonic int64 identities. They do
not use Python or Torch RNG and are not assignment ticks.

The physical-step admission binds:

```text
exact retained domain
source OPEN window
exact current P2 publication object
exact P2 publication identity
admitted Store version
physical-step admission identity
```

The standalone-reset admission is a separate type and binds either the source
OPEN window or `None` for the first prebootstrap reset. Step and reset
admissions cannot be substituted for one another or reused. A per-fence
`ContextVar` supplies call-local/thread-local identity validation without
adding a mutex.

## F1 separation and semantic neutrality

Fence OPEN/CLOSE and admission transitions do not:

```text
increment LifecycleStateStore.version
create or replace P2
change P2 publication identity or provenance
advance lifecycle generation
create a lifecycle result
create an assignment artifact
consume B1 request tokens
```

W-T20 and W-T21 verified exact Store, P2, publication-identity, generation,
and result neutrality across fence-only transitions. Claims retain the
existing B1 semantics and may legitimately change Store/P2 while the exact
same claim window remains OPEN.

## W2 production envelope

The dormant production claim port prepares the unchanged B1
`InitialClaimRequest` and wraps it in an immutable
`RuntimeClaimAdmissionEnvelope` bound to the current exact OPEN window. Commit
first validates the envelope's domain/factory/window binding, then delegates
to the existing B1 commit transaction.

Multiple claims may prepare and commit in one window. Closing W1 permanently
invalidates every W1 envelope; an old envelope is never rebound to W2. Failure
priority is intentional:

```text
same OPEN window + stale P2 source -> existing B1 stale_source
closed/old window + otherwise-current P2 -> B1W stale_claim_window
```

The B1 C2 batching, G2 selected-row terminal gating, request consume-once
semantics, and `EffectiveAssignmentCommitArtifact` remain unchanged.

## S4 step admission and O1 completion

Physical-step begin runs under the domain operation lock. It reuses the
coordinator publication lock to recheck health, apply the existing R3 terminal
slot guard, and capture the exact current P2 before atomically moving
`OPEN(Wk) -> STEP_IN_FLIGHT(Ak)`.

The pure environment-validation capability must consume the same exact
admission at entry and finalization. Explicit successful outer return is the
only step path that clears the admission and creates exactly one next window.
Duplicate entry, finalization, or success calls reject as already consumed.

Standalone full-reset begin accepts only `PREBOOTSTRAP_CLOSED` or `OPEN`, moves
to `RESET_IN_FLIGHT`, and requires exact reset-entry validation. Explicit
successful outer reset return creates exactly one next window. The first
window therefore appears only after the first admitted external reset fully
returns.

Internal autoreset during an admitted physical step does not open a window:
the fence remains `STEP_IN_FLIGHT(Ak)` across I3, terminal publication, and I1.
Only the outer step's explicit successful return opens the next window.

## Lock ordering and terminal interaction

The exact retained lock order is:

```text
domain operation/admission lock
  -> coordinator publication lock
    -> LifecycleStateStore lock (only inside existing semantic transactions)
```

No `Lock` or `RLock` is imported or constructed by the B1W fence module. The
domain continues to own its one existing operation lock; the coordinator and
StateStore remain the sole publication and semantic-state authorities.

G2 and R3 retain distinct responsibilities:

- G2 rejects selected terminal-occupied rows during a claim but permits
  unselected rows.
- R3 rejects the next global physical-step admission when any terminal slot is
  occupied.
- R3 rejection allocates no admission, does not poison, and leaves the exact
  OPEN window unchanged.
- Exact terminal acknowledgement changes neither P2, Store, nor the window;
  a claim retry in that same window is allowed.

## Capability confinement and production boundary

The domain exposes separate private capabilities for production claim,
physical-step admission, standalone-reset admission, future environment
validation, and read-only fence inspection. The actual existing environment
port did not gain a B1W writer or validation method.

Static and runtime audits verified:

```text
B1W module __all__ == ()
no package __init__ export
no raw public OPEN/CLOSE writer
no second fence singleton or second mutex
no independent poison writer
no assignment/claim/admission tick
no B1W production symbol in 73 environment/wrapper/resolver/controller/
  HARL/config/training/playback/evaluation candidate files
```

Accordingly, S4/O1/W2 exist only as dormant pure capabilities. Real
environment validation, continuous-control placement, and wrapper orchestration
remain unimplemented.

## Dedicated B1W verification

Runner:

```text
scripts/environments/test_assignment_phase_b1w_interstep_claim_window_fence_pure.py
```

Results:

```text
normal:  W-T1..W-T26  26/26 passed
-I -B:   W-T1..W-T26  26/26 passed
```

The matrix covers prebootstrap closure, first reset open, multiple claims,
atomic step close, old-window rejection, deterministic claim/step and
claim/reset races using `threading.Event` without sleep, exactly-once success,
autoreset, G2, R3, terminal ack, fail-stop, identity/single-use/thread-local
checks, semantic/P2 neutrality, capability confinement, default-off wiring,
stale-source priority, stale-window priority, and derived FAULTED state.

Both modes reported all global side-effect checks true for Python RNG, Torch
RNG, cwd, `sys.path`, environment, root/named logger configuration, filesystem
inventory, and assignment-profile registry identity/content.

## B1 and B0 regressions

```text
B1 pure normal                            23/23 passed
B1 pure -I -B                             23/23 passed
I4 terminal handoff pure                  16/16 passed
I4 environment integration static         12/12 passed
I3 staged pre-reset adapter                16/16 passed
I2 runtime domain                          12/12 passed
I1 episode rebuild                         12/12 passed
B0-2 lifecycle authority transaction       18/18 passed
B0-1A execution facts producer              9/9 passed
B0-1B generation clock                     12/12 passed
```

The B0 regression total is 107/107. B1 normal and isolated modes total 46/46.

## Frozen Phase-A and contract regressions

```text
lifecycle transition contract              12/12 passed
assignment profile contract                 16/16 passed
event-profile schema                         9/9 passed
Phase-A default-off identity                16/16 passed
profile production wiring                   10/10 passed
event-gated MRTA contract                   13/13 passed
```

Total: 76/76 passed.

## Frozen hashes

```text
assignment_event_contract.py
  22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A
assignment_lifecycle_transition_contract.py
  1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9
assignment_profile_contract.py
  ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500
assignment_event_profile_schema_contract.py
  04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF
scan_mobile_manipulator_env.py
  030EFB1BE030C6F1BB22BB2DCF5918D0235305CB5D543D01569C1066836501D5
assignment_harl_wrapper.py
  DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A
```

All values exactly match B1W preflight.

## Other verification

```text
py_compile changed/new Python: passed
production no-wiring audit:    passed (0 hits across 73 candidates)
package export audit:          passed
capability leak audit:         passed
forbidden assignment tick:     passed
AST mutex audit:               passed (no threading import/Lock/RLock call)
git diff --check:              passed (pre-existing line-ending warnings only)
```

No Isaac, AppLauncher, GUI/headless simulation, training, playback, or
evaluation was started.

## Deferred and unresolved

```text
inter-step real environment wiring: NOT IMPLEMENTED
continuous control integration:     NOT IMPLEMENTED
production claim activation:        NOT IMPLEMENTED
wrapper/HARL orchestration:          NOT IMPLEMENTED
real Isaac fence smoke:              NOT RUN
runtime readiness:                   BLOCKED
training/playback/evaluation:        NOT RUN
11 numeric TBD values:               unresolved
variable-cardinality policy:         not entered
```

## Next gate

Stop after this implementation and await GPT/user review. Do not proceed
automatically into environment or wrapper fence wiring, continuous-control
relocation, production claim activation, scheduler/resolver, mask/DVM, HARL,
runtime-ready activation, Isaac runtime smoke, training, playback, or
evaluation.
