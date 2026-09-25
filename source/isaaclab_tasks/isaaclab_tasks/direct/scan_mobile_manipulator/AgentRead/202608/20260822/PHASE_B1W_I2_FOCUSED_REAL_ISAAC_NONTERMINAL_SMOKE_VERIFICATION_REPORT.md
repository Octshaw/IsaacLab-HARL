# Phase B1W-I2 — Focused Real-Isaac Nonterminal Smoke Verification Report

## Classification

```text
classification:
  PHASE-B1W-I2-FOCUSED-REAL-ISAAC-NONTERMINAL-SMOKE-PASS-AWAITING-GPT-REVIEW

B0:                              CLOSED
B1:                              REVIEW PASS
B1W:                             REVIEW PASS
B1W-I1:                          REVIEW PASS / CLOSED
AppLauncher:                     PASS
exact event composition:         PASS
admitted real reset:             PASS
first OPEN W1:                   PASS
deterministic production claim:  PASS
Ak-bound controller source:      PASS
real nonterminal env.step:       PASS
environment exact-Ak entry:      PASS
same-Ak I3:                      PASS
transition generation:           VERIFIED (-1 -> 0)
outer Ak completion:             PASS
OPEN W2:                         PASS
terminal slot:                   NONE
poison:                          FALSE
production source:               BYTE-IDENTICAL
wrapper:                         NOT USED / UNCHANGED
terminal discovery/ack:          NOT IMPLEMENTED / NOT USED
B1W-I3 / B1W-I4:                 NOT ENTERED
runtime readiness:               BLOCKED
training/playback/evaluation:    NOT RUN
commit:                          NONE
```

This phase supplies only the focused runtime evidence authorized for B1W-I2.
It does not modify the B1W-I1 production mechanism or activate the event
profile for wrapper, HARL, training, playback, or evaluation.

## Repository and execution boundary

```text
working directory: E:\Project\IsaacLab_HARL
branch:            main
starting HEAD:     912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:       912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             empty before and after
worktree:          pre-existing Phase-A/B0/B1/B1W changes preserved
commit:            none
```

The only executable file added by B1W-I2 is:

```text
scripts/environments/test_assignment_phase_b1w_i2_real_isaac_nonterminal_smoke.py
```

The same file contains a public bounded supervisor and one private worker mode.
No separate supervisor file was necessary. The worker emits flushed JSON stage
records, writes one temporary pre-shutdown JSON result, and then closes the
environment and SimulationApp. The supervisor launches exactly one worker,
streams its output, enforces a 180-second upper bound, reads the temporary
result, and removes the temporary directory on exit.

One PTY-based shell launch was rejected by Windows before the conda command or
worker was created (`CreateProcessW: Access denied`). The same command was then
started through ordinary pipes. This was not a smoke attempt and created no
AppLauncher process. The one actual worker attempt passed.

## Interpreter and AppLauncher

```text
conda prefix:       C:\isaacenvs\isaac45_harl
python executable:  C:\isaacenvs\isaac45_harl\python.exe
headless:           true
Isaac device:       cuda:0
experience:         apps/isaaclab.python.headless.kit
supervisor PID:     6716
worker PID:         4940
worker timeout:     false
child exit code:    0
shutdown observed:  true
worker elapsed:     20.375 seconds
supervisor elapsed: 21.750 seconds
```

AppLauncher returned successfully. Isaac selected the NVIDIA RTX 4060 Ti.
Warnings about OmniHub, deprecated dynamic control, rendering-mode config, and
the unsupported Intel integrated GPU were non-fatal and match the historical
B0 focused-runtime environment class.

## Exact real composition

```text
canonical event_gated_local_mrta profile (formal entrypoint)
  -> exactly one _EventProfileLifecycleRuntimeDomain
  -> lifecycle environment capability
  -> exact environment admission-validation capability
  -> current-P2 / production-claim / step-admission / reset-admission ports
  -> read-only inter-step fence capability
  -> one real ScanMobileManipulatorEnv
  -> one EventProfileSynchronousRuntimeCoordinator (O1)
```

Observed vector identity:

```text
E:                2
M:                3
N:                12
device:           cuda:0
profile:          event_gated_local_mrta
domain count:     1
fence count:      1
O1 count:         1
environment type: ScanMobileManipulatorEnv
```

The environment retained the exact lifecycle and admission-validation ports
issued by the same domain. The wrapper, scheduler, resolver, policy, terminal
consumer, and readiness-gated HARL construction helper were not imported or
constructed.

## S0-S14 evidence

| Stage | Result | Observation mode | Evidence |
|---|---|---|---|
| S0 | reached | live | exact profile/domain/env/O1 ready; `PREBOOTSTRAP_CLOSED`; P2 serial 0, Store 0, ep/tr `-1/-1` |
| S1 | reached | live | reset admission serial 0; `RESET_IN_FLIGHT`; no OPEN window |
| S2 | reached | verified post-return | real `_reset_idx()` consumed the exact R1 reset-entry latch |
| S3 | reached | live after call return | real `DirectMARLEnv.reset()` returned its two-tuple |
| S4 | reached | live | explicit R1 completion opened W1 serial 0; reset P2 serial 1, Store 1 |
| S5 | reached | live | production claim committed for both vector rows; Store 1 -> 2; W1 unchanged |
| S6 | reached | live | P2 serial 2; both rows `ASSIGNMENT_COMMIT`; ep/tr `0/-1` |
| S7 | reached | live | caller-side primary R3 passed from W1 |
| S8 | reached | live | Ak admission serial 1; W1 closed; P2 serial 2 / Store 2 captured exactly |
| S9 | reached | live | Ak ownership mapped to `[[9,-1,-1],[9,-1,-1]]`; all real actions finite `[2,9]` on `cuda:0` |
| S10 | reached | verified post-return | real first event hook consumed exact Ak entry latch before task mutation/physics |
| S11 | reached | verified post-return | real `_get_dones()` consumed the same-Ak I3 latch and finalized lifecycle |
| S12 | reached | live after call return | real `DirectMARLEnv.step()` returned five values; all rows nonterminal/nontruncated |
| S13 | reached | live | O1 explicitly completed the exact Ak after normal external return |
| S14 | reached | live | W2 serial 1 OPEN; W2 differs from W1 |

S2, S10, and S11 are labelled `VERIFIED_POST_RETURN` because the production
environment has no diagnostic callback at those hooks. The smoke read the
existing single-use test-diagnostic latch state without mutation, and the
subsequent exact O1 completion prerequisites also passed. They are not claimed
as live callback emissions.

## Reset and W1 evidence

Prebootstrap P2 was canonical:

```text
publication serial:      0
Store version:           0
episode generation:      [-1, -1]
transition generation:   [-1, -1]
provenance:              [PREBOOTSTRAP, PREBOOTSTRAP]
result:                  None
terminated/truncated:    false / false
```

O1 began exact R1 before the real reset. The event hook consumed R1, native
reset and I1 completed, observations were constructed, and the external reset
returned before O1 opened W1. Reset P2 was:

```text
W1 serial:               0
publication serial:      1
Store version:           1
episode generation:      [0, 0]
transition generation:   [-1, -1]
provenance:              [CANONICAL_EPISODE_RESET, CANONICAL_EPISODE_RESET]
termination reason:      [NONE, NONE]
result:                  None
```

## Deterministic legal claim fixture

Selection was strictly **TEST-FIXTURE ONLY**: for each row, choose the lowest-ID
structurally assignable robot, then the greatest-distance task among the
currently available, unowned, nonfailed, environment-feasible tasks. It is not
a resolver, scheduler, policy, or research cost rule and introduced no
lifecycle threshold.

Exact pairs:

| env_id | robot_id | task_id | reset geometry distance |
|---:|---:|---:|---:|
| 0 | 0 | 9 | 7.655880451202393 |
| 1 | 0 | 9 | 7.655880451202393 |

Both robots were `NEEDS_ASSIGNMENT`; both tasks were `AVAILABLE`, unowned, not
failed for the selected robot, uncovered, and feasible. The one C2 batch was
already task-disjoint per environment row.

The production W2 claim port produced an immutable
`EffectiveAssignmentCommitArtifact`:

```text
source Store version:    1
committed Store version: 2
post-claim P2 serial:    2
post-claim provenance:   [ASSIGNMENT_COMMIT, ASSIGNMENT_COMMIT]
ownership task 9:        robot 0 in both rows
robot 0 state:           EXECUTING in both rows
task 9 state:            CLAIMED in both rows
episode/transition:      [0,0] / [-1,-1]
W1 after claim:          exact same serial 0 identity
```

The artifact snapshot remained byte-value identical after the real lifecycle
transition; current P2 legitimately moved to lifecycle-finalized provenance
without patching the historical assignment artifact.

## Ak-bound control and real physics

Primary R3 passed with no pending terminal requirement. Ak admission serial 1
captured the exact post-claim P2 object, publication serial 2, Store version 2,
and source W1 serial 0. No production claim occurred after Ak.

O1 derived this controller assignment only from Ak-admitted ownership:

```text
env 0: [9, -1, -1]
env 1: [9, -1, -1]
```

The smoke invoked the existing `assignment_to_env_actions()` controller path.
It only inspected the returned actions and returned them unchanged:

```text
robot_0: shape [2,9], cuda:0, finite
robot_1: shape [2,9], cuda:0, finite
robot_2: shape [2,9], cuda:0, finite
NaN/Inf: none
```

The actual `DirectMARLEnv.step()` entered the event `_pre_physics_step()`, ran
the physics interval, staged the report, validated and finalized I3 under the
same Ak, computed rewards/bookkeeping and observations, and returned the real
five-tuple normally.

## Final lifecycle and W2 evidence

```text
final publication serial:    3
final Store version:         3
episode generation:          [0, 0]
transition generation:       [0, 0]
provenance:                  [FINALIZED_LIFECYCLE_TRANSITION,
                              FINALIZED_LIFECYCLE_TRANSITION]
terminated:                  [false, false]
truncated:                   [false, false]
termination reason:          [NONE, NONE]
lifecycle event count:       0
completed tasks:             none in either row
task 9 state:                CLAIMED in both rows
task 9 ownership:            robot 0 in both rows
terminal slot:               none
coordinator poisoned:        false
final fence:                 OPEN W2 serial 1
```

Terminal-slot absence was proven without terminal discovery: the domain was
fresh and the existing R3 permission guard passed before admission and again
after W2 opened. No pending key was enumerated, captured, or acknowledged.

## Production hash audit

Every protected file matched its preflight SHA-256 after the smoke:

| File | Preflight and postflight SHA-256 |
|---|---|
| `scan_mobile_manipulator_env.py` | `C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99` |
| `assignment_event_profile_runtime_domain.py` | `484808FDA25CBC2DE74249B972005A6F4FF3C10D2C41D67457F5A48E9B565232` |
| `assignment_interstep_claim_window_runtime.py` | `17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609` |
| `assignment_event_profile_synchronous_runtime.py` | `EFA334C1745F9BBDA17798A57A5E5EE21418B60FDB54771CFDD52FD71A94A309` |
| `assignment_initial_claim_runtime.py` | `C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA` |
| `assignment_lifecycle_transaction_runtime.py` | `28D61BAEA7760F091EE47AC1C3E818DDC7D911EC7BEB587C22023D27DE5593A7` |
| `assignment_harl_wrapper.py` | `DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A` |
| `direct_marl_env.py` | `7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31` |
| `assignment_controller.py` | `28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317` |
| `assignment_rl_interface.py` | `3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59` |
| `assignment_lifecycle_transition_contract.py` | `1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9` |
| `assignment_event_contract.py` | `22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A` |
| `assignment_profile_contract.py` | `ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500` |
| `assignment_event_profile_schema_contract.py` | `04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF` |

Smoke-only runner hash:

```text
170DEA2C0D02370E76C729559ED9903DD8365A9AD1764BD714A30A4801401623
```

## Verification and cleanup

```text
required interpreter check:              passed
smoke-only py_compile:                    passed
one bounded real-Isaac worker:            passed
S0-S14:                                   15/15 reached in exact order
worker timeout:                           false
worker exit:                              0
SimulationApp shutdown observed:          true
post-run attributable process count:      0
production pre/post hashes:               exact
wrapper/resolver/scheduler/terminal-ack
  symbols in smoke:                       0
337/337 pure/static matrix:                retained; not rerun
```

The temporary JSON result was intentionally not retained as source. Its full
evidence was emitted by the supervisor and distilled into this report.

No production Python, config, wrapper, controller, RL interface, resolver,
HARL, Isaac core, site-packages, readiness gate, or frozen contract changed.
No policy, scheduler, terminal consumer, terminal discovery/ack, training,
playback, evaluation, checkpoint, TensorBoard, or optional zero-claim second
step ran.

## Remaining boundary

The focused nonterminal direct route is now verified in real Isaac. Runtime
readiness remains blocked. B1W-I3 real terminal/autoreset/discovery/capture/ack
and B1W-I4 wrapper facade integration are separate, unentered phases. No
scheduler/resolver/policy or learner/critic transport conclusion follows from
this smoke.

Stop after this report and the concise TASK_PROGRESS update. Await GPT/user
review; do not enter B1W-I3, B1W-I4, readiness, training, playback, or
evaluation without explicit authorization.
