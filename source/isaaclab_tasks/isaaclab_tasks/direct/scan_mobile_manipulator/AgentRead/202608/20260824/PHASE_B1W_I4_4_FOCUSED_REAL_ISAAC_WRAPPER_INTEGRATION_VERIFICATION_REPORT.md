# Phase B1W-I4-4 Focused Real-Isaac Wrapper Integration Verification Report

Date: 2026-08-24

## Classification

```text
PHASE-B1W-I4-4-FOCUSED-REAL-ISAAC-WRAPPER-INTEGRATION-VERIFICATION-PASS-AWAITING-GPT-REVIEW
```

B1W-I4-3 is `REVIEW PASS / CLOSED`. The bounded private exact-event wrapper
route is verified against a real `ScanMobileManipulatorEnv`. Public learned-policy
event stepping and runtime readiness remain blocked.

## Scope and repository preflight

- Repository: `E:\Project\IsaacLab_HARL`
- Branch: `main`
- HEAD: `912b3b59831fcad8dd29ac575b2a1851bf2c21d1`
- Index: empty before and after verification
- Commit: none
- Existing dirty worktree: preserved; no reset, checkout, clean, stash, stage,
  or unrelated-file repair was performed
- Production edits in I4-4: none
- Authorized I4-4 code delta: one bounded supervisor/worker smoke fixture:
  `scripts/environments/test_assignment_phase_b1w_i4_4_real_isaac_wrapper_integration_smoke.py`

The smoke used the required interpreter at
`C:\isaacenvs\isaac45_harl\python.exe`, launched Isaac headlessly, enforced a
240-second supervisor timeout, and closed both the environment and
`SimulationApp`.

## Exact runtime identity and composition

```text
E = 2
M = 3
N = 12
device = cuda:0
profile = event_gated_local_mrta
environment = ScanMobileManipulatorEnv
wrapper count = 1
legacy resolver = None
```

Observed shape identities:

```text
ownership:             [2, 12]
cumulative_failed_pair:[2, 3, 12]
feasible_mask:         [2, 3, 12]
cost_matrix:           [2, 3, 12]
controller assignment: [2, 3]
```

The private composition graph was exactly:

```text
real ScanMobileManipulatorEnv
  -> retained _EventProfileLifecycleRuntimeDomain
  -> EventProfileSynchronousRuntimeCoordinator (O1)
  -> _compose_event_assignment_runtime_facade
  -> one AssignmentHarlWrapper
```

The event branch did not construct or call the stateful legacy resolver. A call
guard around the real environment recorded zero direct wrapper-originated raw
`reset` calls and zero direct wrapper-originated raw `step` calls; admission was
owned by the facade/O1 route.

## Bounded real-Isaac evidence

### Reset and initial authority

The admitted reset returned canonical P2 publication serial 1 / Store version
1 for both rows:

```text
episode_generation    = [0, 0]
transition_generation = [-1, -1]
provenance            = canonical_episode_reset for both rows
result                = None
terminated/truncated  = false/false
ownership             = all -1
fence                 = OPEN, window serial 0
poison                 = false
```

This was a real environment reset admitted through the exact WR-C composition,
not a synthetic lifecycle transaction.

### Real proposal, M1/B1, P2, Ak, and controller

The fixture copied the real environment's feasibility, cost, and availability
snapshots on `cuda:0`. For each environment it chose robot 0 / task 9 from an
actually feasible pair; the observed real cost was `7.655880451202393`. The
selection rule is explicitly test-fixture-only and is not production policy.

The resolved task-disjoint proposal produced exactly one coherent batch
artifact. Store advanced once from 1 to 2 for B1, and the physical lifecycle
transition then produced Store version 3 / publication serial 3. Final P2,
admitted Ak, and action-builder/controller assignment were exactly:

```text
[[9, -1, -1],
 [9, -1, -1]]
```

Every real continuous action record was finite and remained on `cuda:0`. No
proposal tensor, M1 request, commit artifact, wrapper cache, or local diagnostic
became controller authority: the observed path remained final P2 -> Ak ->
controller. A subsequent real no-new-claim step preserved the same assignment
and completed nonterminally.

Store mutation accounting through the bounded run was:

```text
reset P2                  Store 1
one M1/B1 batch           Store 2  (delta exactly +1)
proposal physical step    Store 3
continuation/drive        Store 4..6
terminal transition + R2 Store 7
atomic ACK                Store 7  (neutral)
post-ACK recovery         Store 8
```

No second Store, coordinator, lock, tick, poison flag, or terminal registry was
introduced by the smoke.

### Real terminal, autoreset, historical copy, and exact ACK

At bounded physical step 4 both real rows reached terminal and installed the
sole coordinator's exact terminal slots:

```text
(env_id, episode_generation, transition_generation)
(0, 0, 3)
(1, 0, 3)
```

The wrapper/facade observed both slots before ACK. The same Ak completion then
performed autoreset and opened Wnext, yielding current canonical reset P2:

```text
episode_generation    = [1, 1]
transition_generation = [3, 3]
publication serial    = 7
Store version         = 7
result                = None
window serial         = 4, OPEN
raw episode_length    = [0, 0]
```

The copied terminal DTOs remained historical episode 0 rows while current P2
was already episode 1. The wrapper returned the exact two historical keys,
retained no raw runtime artifact, and returned `optional_sidecar=None`.

One facade-owned `ATOMIC_BATCH_EXACT_ACK` removed both captured slots:

```text
slots before ACK = 2
slots after ACK  = 0
```

ACK preserved the exact current P2 object, Store version 7, episode/transition
generations, OPEN window identity/serial, and `poison=false`. The existing
single-key direct ACK capability remains preserved as an I3 diagnostic API; it
was not substituted for the wrapper batch handoff.

### Post-ACK recovery and shutdown

The next real step succeeded nonterminally, advanced current transition
generation to `[4, 4]`, published Store version 8 / serial 8, and completed to a
fresh OPEN window serial 5 with no active Ak, no terminal slot, and no poison.

The worker requested clean environment close, exited with code 0, and was not
alive after supervisor wait. The supervisor exited code 0; timeout was false.
The final real-smoke classification was the PASS classification at the top of
this report.

## Verification stages

The emitted audit sequence was S0 through S18:

1. preflight identity and AppLauncher/environment composition;
2. admitted canonical reset and OPEN W1;
3. real feasibility/cost snapshot;
4. one real M1/B1 commit and final P2 -> Ak -> controller step;
5. real no-new-claim continuation;
6. bounded real terminal and two pre-ACK slots;
7. same-Ak autoreset and wrapper historical copy;
8. atomic batch exact ACK and history/current split;
9. real post-ACK recovery;
10. wrapper raw-call isolation, blocked public route, final OPEN/no-slot/no-poison;
11. clean close and supervisor-confirmed process-tree exit.

## Pure/static regression matrix

All suites below were run after the real smoke in both normal and `-I -B`
modes. Each mode passed 213/213; combined result was 426/426.

| Suite | normal | `-I -B` |
|---|---:|---:|
| I4-3 terminal wrapper handoff | 26/26 | 26/26 |
| I4-2 proposal/effective commit | 22/22 | 22/22 |
| I4-1 facade/reset/continuation | 15/15 | 15/15 |
| Phase-A default-off identity | 16/16 | 16/16 |
| profile production wiring | 10/10 | 10/10 |
| B1 initial claim | 23/23 | 23/23 |
| B1W inter-step fence | 26/26 | 26/26 |
| B1W-I1 environment/O1 | 28/28 | 28/28 |
| B1W-I3 terminal consumer | 13/13 | 13/13 |
| frozen lifecycle transition contract | 12/12 | 12/12 |
| frozen event-profile schema | 9/9 | 9/9 |
| frozen event-gated MRTA contract | 13/13 | 13/13 |

The I4-4 smoke fixture also passed `py_compile` in normal and `-I -B` modes.
`git diff --check` returned 0.

Static inspection plus the retained pure suites confirmed:

- P2 remains sole lifecycle authority and Ak remains the sole controller source;
- proposal, M1, and commit artifact are diagnostics/transaction inputs, not
  controller sources;
- wrapper event reset/step routes use facade/O1 admission and the terminal route
  uses atomic batch ACK;
- no second Store/coordinator/lock/tick/poison/terminal registry exists;
- public event `.step(actions)` still raises before policy routing;
- lifecycle actor/shared observations and action mask/DVM remain absent.

## Protected production hashes

All protected hashes were captured before the smoke and recomputed after the
real smoke/regressions. Every full SHA-256 value was an exact pre/post match.

| Protected file | SHA-256 pre = post |
|---|---|
| `assignment_lifecycle_transaction_runtime.py` | `F7B80540EF1CA39CA103855B7D1DB2FFEDDE950242EC223061D0BF01F32E7C5C` |
| `assignment_event_profile_runtime_domain.py` | `A86B1BCF6A494C570B4DBD048915B2D2EAFBC2E8D9EB055C2934728C166E1822` |
| `assignment_event_profile_synchronous_runtime.py` | `C7C7200FDEFF4A41756335AF3F274C2F195BC6D2B3E619C07BCD3A88B77912BC` |
| `assignment_event_runtime_facade.py` | `036082D8DF61514AA3F3C424AE6559FA678536097B66BFD5BD6F632CA3479478` |
| `assignment_event_terminal_transport.py` | `3DB780B7C9879EAC12D41E0B5BC2FE77F31D7F495EDE7A6AC664C542476973A5` |
| `assignment_event_proposal_adapter.py` | `874B4C7B71E6C42F9E6DABEEFA25A708D25D8518E3366FE91B86B9B1A739BEDD` |
| `assignment_harl_wrapper.py` | `F238536C8A4BED53DA984E4F2D81150F7B634915E49B601D86EB407FAE9FA2AE` |
| `assignment_initial_claim_runtime.py` | `C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA` |
| `assignment_interstep_claim_window_runtime.py` | `17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609` |
| `assignment_controller.py` | `28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317` |
| `assignment_rl_interface.py` | `3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59` |
| `scan_mobile_manipulator_env.py` | `C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99` |
| `assignment_harl_training.py` | `B6F32510AE663B3E443891CDD09219DD9A5C9CEB9DE9C720C73192C7488597FD` |
| `source/isaaclab/isaaclab/envs/direct_marl_env.py` | `7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31` |
| `assignment_lifecycle_transition_contract.py` | `1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9` |
| `assignment_event_contract.py` | `22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A` |
| `assignment_profile_contract.py` | `ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500` |
| `assignment_event_profile_schema_contract.py` | `04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF` |

## Harness corrections during verification

Two preliminary runs exposed smoke-fixture omissions only:

1. the local real-environment config initially retained raw profile `legacy`
   while the exact event profile was injected; the fixture was corrected to
   bind the same authoritative profile identity before environment construction;
2. the semantic run then passed S0-S18, but final JSON emission attempted to
   serialize diagnostic tensors directly; the fixture's result writer was
   corrected to use its existing tensor-to-JSON conversion.

Neither condition changed production code or revealed a production semantic
gap. The final rerun, including explicit E/M/N shape assertions, passed and
shut down cleanly.

## Explicit non-claims and phase boundary

```text
real WR-C composition:                 PASS
real admitted reset:                   PASS
real continuation:                     PASS
real proposal/M1:                      PASS
explicit feasibility real snapshot:   PASS
final P2 -> Ak -> controller:          PASS
real lifecycle transition:             PASS
real terminal/autoreset:               PASS
real wrapper historical copy:          PASS
real atomic batch exact ACK:            PASS
real post-ACK recovery:                PASS
single-key direct ACK:                 PRESERVED
P2 sole authority:                     PRESERVED
Ak-only controller:                    PRESERVED
proposal/M1 semantics:                 PRESERVED
default-off:                           PRESERVED
public learned-policy event step:      BLOCKED
lifecycle obs/shared obs:              NOT IMPLEMENTED
action mask/DVM:                       NOT IMPLEMENTED
forced-row runner:                     NOT IMPLEMENTED
terminal critic sidecar:               NOT IMPLEMENTED
learner transport:                     NOT IMPLEMENTED
HARL:                                  NOT RUN
training/playback/evaluation:          NOT RUN
runtime readiness:                     BLOCKED
production source behavior changes:    NONE
commit:                                NONE
```

This report closes only the authorized focused I4-4 verification. It does not
authorize public event activation or entry into any later phase.
