# Phase B0-1B Pure Generation Clock Implementation Report

## 1. Classification

```text
classification:
  PHASE-B0-1B-PURE-GENERATION-CLOCK-COMPLETE-AWAITING-GPT-REVIEW

B0-1A:
  review passed
  complete

B0-1B:
  complete at pure/default-off level

episode generation authority:
  implemented

transition generation candidate/commit authority:
  implemented

token independence:
  verified

environment reset integration:
  not implemented

lifecycle authority/state mutation:
  not implemented

ledger/result:
  not implemented

mailbox/sidecar:
  not implemented

event runtime readiness:
  still blocked

B0-2:
  not authorized

Phase B/C/D/E:
  not entered

commit:
  none
```

No Phase-A frozen-contract change, generic candidate cancellation, or early
lifecycle-runtime expansion was required. B0-1B stops at an explicit pure
generation candidate/commit protocol.

## 2. Repository baseline and scope

```text
starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch:
  main

HEAD subject:
  feat(assignment): complete lifecycle-aware MRTA Phase A interface contracts

index at B0-1B preflight:
  empty

preserved uncommitted cohort at preflight:
  B0 design report
  B0-1A runtime module
  B0-1A pure test
  B0-1A implementation report
  TASK_PROGRESS B0-1A update

commit made by B0-1B:
  none
```

The existing uncommitted B0 design/B0-1A cohort was preserved. B0-1B extends
the same dormant runtime module and adds only its dedicated pure test, this
report, and an in-place progress update.

## 3. Changed and new files

Narrowly extended production foundation:

- `assignment_lifecycle_authority_runtime.py`

New pure test:

- `scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py`

New report:

- `AgentRead/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md`

Updated in place:

- `AgentRead/TASK_PROGRESS.md`

Phase-A frozen files changed:

```text
assignment_profile_contract.py:
  unchanged

assignment_lifecycle_transition_contract.py:
  unchanged

other Phase-A authorities:
  unchanged
```

No environment, wrapper, resolver, controller, HARL, configuration,
checkpoint, installed-package, or numeric-policy file changed.

## 4. Clock ownership and domain identity

`LifecycleGenerationClock` is the sole writer of two private per-row vectors:

```text
episode_generation
committed transition_generation
```

The exact B0-1B ownership interpretation is:

```text
domain identity:
  one opaque clock identity

domain rows:
  one constructor-declared unique int64 env_id universe

process lifetime:
  the environment domain must retain/inject the same clock instance for its
  entire process lifetime

unique writer:
  only that retained clock instance can mutate the domain generations

numeric env_id scope:
  row identity inside a vector-environment domain, not a process-global
  environment-instance key
```

A second clock object, even with the same numeric row IDs, creates a distinct
opaque domain. It cannot commit a context from the first clock. It is not a
reconstruction or continuation of the first domain. B0-1B does not claim
state survival across clock reconstruction and exposes no reset, restore,
seed, serialization, checkpoint, or reconstruction API.

This instance/domain interpretation is intentional: common vector-environment
rows such as `0..E-1` can coexist in separate environment instances, so a
module-global generation map keyed only by numeric row ID would merge unrelated
domains. The later authorized environment integration must construct exactly
one clock for its domain and retain it; B0-1B does not wire or create that
environment owner.

## 5. Initial conventions and episode API

The private immutable clock state starts every declared row at:

```text
episode_generation:
  -1

transition_generation:
  -1

outstanding transition candidate:
  none
```

The episode capability is:

```python
clock.advance_episode(env_ids)
```

Its semantics are:

```text
first selected advance:
  -1 -> 0

later selected advance:
  p -> p + 1

untouched rows:
  bit-exact unchanged

outstanding candidate on any selected row:
  full batch rejected
  candidate preserved

at int64 max:
  full batch rejected
  no wrap/clamp/reset
```

The API is only a pure reset/rebuild-facing capability. It is not connected to
`_reset_idx()`, explicit reset, or autoreset.

## 6. Transition candidate and commit APIs

The candidate capability is:

```python
contexts = clock.request_transition_candidate(env_ids)
```

For each selected row:

```text
current committed generation:
  g

new candidate:
  g + 1

committed generation after request:
  still g
```

Candidate request requires an episode generation of at least zero, rejects a
second outstanding candidate for the same row, rejects int64 exhaustion, and
is full-batch atomic. Different free rows remain independent.

The commit capability is:

```python
clock.commit_transition(env_ids, contexts)
```

The explicit `env_ids` target prevents a caller from silently committing a
valid context for the wrong intended row. Commit accepts only an exact tuple
of exact `TransitionGenerationContext` objects and validates:

```text
clock identity
target env identity
current episode identity
exact contiguous generation == committed + 1
exact outstanding object identity
exact reserved scalar contents
```

It rejects wrong-clock, wrong-env, wrong-episode, duplicate, stale, future,
non-outstanding, copied, forged, and altered contexts before state mutation.
There is no automatic commit.

`TransitionGenerationContext` and `GenerationClockSnapshotRow` are unversioned
B0-private runtime protocol records. They add no Phase-A schema, semantic
descriptor, checkpoint field, V3 identity, serialization format, or public
frozen-contract revision.

## 7. Outstanding behavior and no cancellation

Each environment row has at most one active candidate:

```text
candidate g outstanding on env e
  -> another request including e rejects atomically
```

An outstanding candidate also blocks `advance_episode(e)`. A mixed batch with
one blocked row advances no selected row. The clock never silently discards a
candidate.

No generic cancellation or rollback API was added. A facts construction
failure leaves the same candidate active so that the caller can correct the
facts input and retry it.

## 8. Atomicity and external-context hardening

The clock stores Python integers in one frozen `_GenerationClockState` aligned
to the constructor-declared row order. Each mutating operation uses one
instance lock and follows:

```text
capture one current immutable state
validate every selected row
prepare replacement tuples
assign self._state exactly once
```

No operation mutates row-by-row while later rows remain unvalidated.

Commit snapshots all externally held context scalars under the clock lock,
compares them with the private `_OutstandingTransition` reservation, stages
the internal reserved generation, and uses only that staged internal integer
for the final state swap. It never rereads `context.transition_generation`
after validation. This closes the adversarial forced-mutation/TOCTOU boundary;
even bypassing `frozen=True` cannot inject an unvalidated generation.

Snapshots contain detached Python scalars and no reference to the internal
state or active context. Mutating or replacing a returned snapshot/context
cannot mutate the clock.

## 9. Overflow and input boundary

Episode and transition generations use Python integers internally but enforce
the signed-int64 semantic maximum:

```text
max - 1 -> max:
  allowed

next increment/request:
  GenerationClockRuntimeError

mixed valid + overflow batch:
  no selected mutation/reservation
```

The public env-row inputs require an exact nonempty rank-one, unique,
materializable, strided `torch.int64` tensor on the declared device. Unknown
rows and duplicate selections fail closed. This boundary does not cast, move,
normalize, or invent row IDs.

## 10. Token independence and B0-1A composition

The facts producer API and state remain unchanged:

```text
EnvironmentExecutionFactsProducer public methods:
  build_facts only

producer slots:
  _profile
  _producer_stamp

clock inside producer:
  none
```

The clock and producer use different locks and different storage. The clock
does not reference the token allocator or `build_facts`; the producer does not
reference the clock.

The strongest composition scenario proved:

```text
candidate transition 0
  -> valid facts token q
  -> explicit commit transition 0

candidate transition 1
  -> invalid post-token facts input burns q + 1
  -> committed transition remains 0
  -> same candidate 1 remains outstanding
  -> corrected retry gets token q + 2
  -> explicit commit transition 1
```

Observed dedicated evidence:

```text
first token:
  0

retry token:
  2

token delta:
  2

committed transition delta:
  1
```

The absolute equality of a token and generation is never required. Token gaps
do not create transition-generation gaps.

## 11. Event-profile gate and default-off boundary

The clock accepts only:

```text
type(profile) is ResolvedEventGatedAssignmentProfile
```

It rejects all four existing resolved profiles and raw enum/string/mapping
inputs with `AssignmentProfileRouteError`. It never invokes a resolver,
normalizer, fallback, or existing-profile validator.

The event profile remains:

```text
runtime route:
  event_gated_phase_a_interface_only_v1

runtime readiness:
  interface_only

training support:
  phase_a_blocked

playback support:
  blocked
```

`require_assignment_profile_runtime_ready()` remains unchanged and still
raises the exact `PhaseAExecutionNotAuthorizedError` for the event profile.

## 12. Dedicated G1-G12 evidence

| Group | Result | Evidence |
|---|---:|---|
| G1 initial/input boundary | pass | all rows `-1/-1/none`; exact type, dtype, shape, uniqueness, materialization, and known-domain gates |
| G2 episode advance | pass | selected `-1->0->1`; untouched exact; max boundary and mixed-batch overflow atomic |
| G3 candidate | pass | pre-episode reject; first `0`, next `1`; request does not commit; transition overflow atomic |
| G4 explicit commit | pass | ordered multirow exact contexts commit to `[0,0]`; active reservations cleared |
| G5 invalid commits | pass | wrong env/clock/episode, duplicate, stale, future, copied identity rejected; valid+invalid batch commits none |
| G6 one outstanding | pass | second same-row request and mixed blocked/free batch reject; free row remains independently usable |
| G7 episode blocking | pass | outstanding row blocks single and mixed episode advance; candidate preserved; other row independently advances |
| G8 cross-episode transition | pass | episode reaches `1`; committed transition stays `0`; next transition commits `1` |
| G9 token independence | pass | failed facts build burns one token; same candidate retries; token delta `2`, transition delta `1` |
| G10 purity/alias | pass | constructor and operations preserve Python/Torch RNG, files, logger, cwd, environment, `sys.path`; snapshots isolated; copied/tampered active contexts rejected |
| G11 profile/default-off | pass | exact event accepted; four existing plus three raw forms rejected; zero resolver calls; readiness still blocked |
| G12 scope/static | pass | four exact clock methods, B0-1A producer unchanged, later capabilities/heavy imports/production wiring absent |

Final dedicated JSON result:

```text
status=passed
num_tests=12
passed=12
failed=0
```

The suite also passed in an isolated `python -I -B` process.

## 13. Verification commands and results

Interpreter:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Result:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Compilation:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_authority_runtime.py scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py
```

Result: passed.

B0-1A dedicated producer regression:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py --json
```

Result: `9/9` passed.

B0-1B dedicated generation-clock suite:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -I -B scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py --json
```

Result: `12/12` passed.

Frozen lifecycle-transition contract regression:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_contract.py --json
```

Result: `12/12` passed.

Frozen profile-contract regression:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_profile_contract.py --json
```

Result: `16/16` passed (`A1a 11/11`, `A1b 5/5`).

Focused default-off identity regression:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_phase_a_default_off_identity.py --json
```

Result: `16/16` passed; runtime identity remains
`DEFERRED-RUNTIME-IDENTITY-EVIDENCE`.

Final scope checks include `git diff --check`, explicit untracked-file
inspection, trailing-whitespace inspection, frozen-file status, module import
search, and environment/wrapper/resolver/controller/package no-wiring search.

No Isaac or AppLauncher command was run.

## 14. Explicit non-implementation inventory

```text
LifecycleAuthorityRuntime:
  not implemented

LifecycleStateStore:
  not implemented

lifecycle state mutation:
  none

TransitionConsumeLedger / receipt:
  not implemented

LifecycleTransitionResult runtime:
  not implemented

derived lifecycle completion/release/failure/termination/events:
  not implemented

mailbox / handoff protocol:
  not implemented

terminal critic sidecar:
  not implemented

generic cancellation / rollback:
  not implemented

environment pre-reset or reset hook:
  not implemented

wrapper/resolver/controller integration:
  none

scheduler/retry/local sets/Top-K/cost/component resolver/DVM:
  not implemented

HARL/team reward runtime:
  not implemented

checkpoint-ready V3 / weight use:
  not implemented

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

checkpoint tensor I/O:
  none

installed HARL:
  unchanged

11 numeric TBDs:
  unresolved
```

## 15. Stop boundary and next gate

B0-1B required no frozen semantic revision and no generic candidate-discard
protocol, so neither prescribed STOP condition was reached.

The next action is independent GPT/user review of this pure/default-off
foundation. This report does not authorize environment integration, lifecycle
authority/state, result/ledger, mailbox/sidecar, B0-2, or Phase B/C/D/E work.

```text
B0-1B:
  complete
  stopped for GPT/user review

B0-2:
  not entered
  not authorized

Phase B/C/D/E:
  not entered
  not authorized
```
