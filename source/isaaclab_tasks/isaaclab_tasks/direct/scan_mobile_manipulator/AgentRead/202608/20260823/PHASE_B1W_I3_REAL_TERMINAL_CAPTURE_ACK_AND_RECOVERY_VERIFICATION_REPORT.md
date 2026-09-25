# Phase B1W-I3 — Real Terminal Capture, Ack, and Recovery Verification Report

## Classification

```text
classification:
  PHASE-B1W-I3-REAL-TERMINAL-CAPTURE-ACK-AND-RECOVERY-PASS-AWAITING-GPT-REVIEW

B0:                                      CLOSED
B1 / B1W:                                REVIEW PASS
B1W-I-D:                                 REVIEW PASS / FROZEN
B1W-I1:                                  REVIEW PASS / CLOSED
B1W-I2:                                  REVIEW PASS / CLOSED
B1W-I3 terminal discovery/capture:       IMPLEMENTED
B1W-I3 designated exact ack:             IMPLEMENTED
B1W-I3 O1 terminal-first facade:         IMPLEMENTED
real terminal lifecycle/autoreset:       VERIFIED
slot survival through autoreset:         VERIFIED
pre-ack primary R3:                      VERIFIED / NEUTRAL
post-ack recovery and nonterminal step:  VERIFIED
B1W-I4 wrapper facade:                   NOT ENTERED
runtime readiness:                       BLOCKED
training/playback/evaluation:            NOT RUN
commit:                                  NONE
```

This phase implements and verifies only the authorized terminal discovery,
capture, exact acknowledgement, and direct HARL-independent O1 integration.
It does not activate the event profile or enter wrapper/HARL transport.

Following `AgentRead/AGENTS.md`, this new report is stored in the current local
date folder `AgentRead/202608/20260823/`. The earlier prompt-local `20260822` example
was not used as the write destination.

## Repository boundary

```text
working directory: E:\Project\IsaacLab_HARL
branch:            main
HEAD:              912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             no phase commit
worktree:          pre-existing Phase-A/B0/B1/B1W cohort preserved
commit:            none
```

No reset, cleanup, normalization, or commit was performed. Existing unrelated
and prior-phase worktree content was preserved.

## Implemented production delta

### Existing coordinator store

`assignment_lifecycle_transaction_runtime.py` adds one private operation:

```text
_capture_pending_terminal_artifacts(*, exact designated consumer capability)
  -> acquire the existing coordinator publication lock
  -> validate the already-issued unique consumer capability
  -> read the existing per-env _terminal_slots dictionary
  -> return the exact stored artifact objects
  -> order deterministically by ascending env_id
  -> return an immutable tuple
```

An empty slot set returns `()`. Capture does not delete, replace, acknowledge,
reconstruct, copy from current P2, allocate a key, or alter a terminal artifact.
No lock, slot registry, cache, tick, pointer, or health authority was added.

### Domain consumer capability

`assignment_event_profile_runtime_domain.py` extends only the already unique
`_EventProfileTerminalConsumerPort` with:

```text
domain_identity
capture_pending_terminal_artifacts()
```

The existing exact-key `read_terminal()` and `acknowledge_terminal()` remain
unchanged. Diagnostic observer ports do not gain discovery or ack authority.
The environment retains no terminal consumer.

### HARL-independent O1 facade

`assignment_event_profile_synchronous_runtime.py` now requires the exact
same-domain designated terminal consumer port and exposes two separate calls:

```text
capture_pending_terminal_artifacts()
acknowledge_terminal_artifact(exact_key)
```

There is no automatic acknowledgement, delivery cache, background consumer,
pending-transition resume, terminal sidecar, or wrapper transport. O1 still
owns no Store, terminal registry, lifecycle writer, raw fence, poison writer,
policy, scheduler, resolver, wrapper, or HARL object.

## Frozen TA1 ordering

The verified route is:

```text
terminal Ak admitted
-> real physics and exact-Ak I3 finalization
-> exact terminal artifact/slot publication
-> internal autoreset under the same Ak
-> external env.step return
-> explicit Ak success completion
-> OPEN Wnext + occupied terminal slots
-> exact stored-artifact capture
-> deliberate pre-ack O1 begin-step rejection through primary R3
-> exact-key acknowledgements
-> post-ack O1 step admission
-> one real nonterminal physical step
-> explicit Ak completion
-> OPEN next window, no slot, no poison
```

Capture and ack are deliberately separate. Capture alone leaves G2/R3 in
force. Ack removes terminal-slot lifetime state only; it does not publish P2,
advance Store/generations, open a window, execute physics, or poison.

## Dedicated pure verification

Runner:

```text
scripts/environments/test_assignment_phase_b1w_i3_terminal_consumer_integration_pure.py
```

Results:

```text
normal:  I3-T1..I3-T13  13/13 passed
-I -B:   I3-T1..I3-T13  13/13 passed
```

Coverage includes:

1. empty capture as an ordinary immutable tuple;
2. one pending artifact and repeat identity;
3. multi-row ascending env-ID order from an intentionally unsorted domain;
4. capture read-only neutrality and continued R3 obligation;
5. exact acknowledgement identity and P2/Store/window neutrality;
6. wrong, stale, foreign-env, and duplicate acknowledgement rejection;
7. G2 selected-row rejection with slot/window preservation;
8. pre-ack O1 primary-R3 rejection before Ak/environment work and without poison;
9. post-ack retry, nonterminal fake step, explicit completion, and OPEN;
10. frozen artifact/key and coverage no-alias behavior;
11. cross-domain consumer rejection;
12. exact consumer/O1 capability confinement;
13. one slot store, existing publication lock, and no new mutex/cache/tick.

## Focused real-Isaac terminal smoke

Runner:

```text
scripts/environments/test_assignment_phase_b1w_i3_real_isaac_terminal_smoke.py
```

Invocation:

```text
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl \
  python scripts/environments/test_assignment_phase_b1w_i3_real_isaac_terminal_smoke.py \
  --num-envs 2 --timeout-seconds 240 --json
```

Final result:

```text
status:                  passed
classification:          PHASE-B1W-I3-REAL-TERMINAL-CAPTURE-ACK-AND-RECOVERY-PASS-AWAITING-GPT-REVIEW
device:                  cuda:0
domain/env/O1 count:     1 / 1 / 1
E / M / N:               2 / 3 / 12
physical steps:          4 (bound <= 32)
worker exit:             0
timeout:                 false
shutdown observed:       true
worker alive after wait: false
```

### Fixture boundary

The smoke uses the existing `episode_length_s` time-limit mechanism only. A
smoke-local cfg instance is set to four configured environment-step periods:

```text
physics dt:               1/60 s
decimation:               6
environment step:         0.1 s
smoke episode length:     0.4 s
computed max step count:  4
```

This is `TEST FIXTURE ONLY`. No production cfg class, YAML, lifecycle semantic,
terminal reason, threshold contract, or runtime-ready setting changed. The
initial reset receives one legal deterministic claim per row: robot 0 to the
farthest feasible task 9. Later steps use admitted continuation; the post-reset
recovery step uses the canonical empty ownership publication.

### Exact real evidence

The terminal transition occurred on the third pre-reset physical step:

```text
terminal Ak serial:          3
terminal env rows:           0, 1
terminal episode:            0
terminal transition:         2
reason:                      TIME_LIMIT (3)
terminated:                  [false, false]
truncated:                   [true, true]
facts consume token:         2 for both rows
authority receipt id:        3 for both rows
```

The post-autoreset current publication was distinct historical/current state:

```text
current episode:             [1, 1]
current transition:          [2, 2]
current result:              None
current termination reason:  NONE
current Store version:       6
current publication serial:  6
terminal slots:              still 2
window serial:               3 / OPEN
poisoned:                    false
```

Capture returned the exact stored artifact objects in env order `[0, 1]`.
Repeated capture returned the same object identities. Each artifact retained
its exact terminal result/published-view identity and remained separate from
the new-episode current P2.

### T0-T9 stage result

```text
T0   terminal step admitted with Ak serial 3
T1   terminal lifecycle finalized for env 0 and 1
T2   two exact per-row slots installed
T3   autoreset latch consumed under the same Ak; episode advanced to 1
T4   external step returned truncated=[true,true]
T5   Ak completed; OPEN W serial 3 with both slots retained
T6   exact stored artifacts captured; repeat identity true
T6B  deliberate next O1 step rejected terminal_ack_required
T7   exact keys (0,0,2) and (1,0,2) acknowledged
T8   post-ack primary R3 passed; Ak serial 4 admitted from W serial 3
T9   one real nonterminal step completed; OPEN W serial 4
```

The T6B snapshot covered current publication identity, Store/generation,
window/active admission, poison, episode counter, common counter, action and
previous-action buffers, dwell, coverage, and captured slot identities. All
were unchanged. No action builder or environment hook executed.

Ack returned the exact captured artifact identities, removed exactly the two
addressed slots, and preserved the current P2 and W3 identities. The T9 step
then produced:

```text
episode generation:       [1, 1]
transition generation:    [3, 3]
terminated / truncated:   [false,false] / [false,false]
Store version:            7
publication serial:       7
slot count:               0
fence:                    OPEN W serial 4
active Ak:                none
poisoned:                 false
```

## Regression result

```text
B1W-I3 pure normal / -I -B             13/13 + 13/13
B1W-I1 pure normal / -I -B             28/28 + 28/28
B1W pure normal / -I -B                26/26 + 26/26
B1 pure normal / -I -B                 23/23 + 23/23

B0-3I4 terminal handoff                       16/16
B0-3I4 environment static                     12/12
B0-3I3 staged adapter                         16/16
B0-3I2 runtime domain                         12/12
B0-3I1 episode rebuild                        12/12
B0-2 authority transaction                    18/18
B0-1A facts producer                           9/9
B0-1B generation clock                        12/12
B0 subtotal                                  107/107

lifecycle transition contract                 12/12
assignment profile contract                   16/16
event-profile schema                           9/9
Phase-A default-off identity                  16/16
profile production wiring                     10/10
event-gated MRTA contract                     13/13
frozen subtotal                               76/76

all recorded pure/static executions          363/363
```

The first B0-3I2 run exposed only its stale expected consumer surface. Its
authorized static oracle was updated to recognize discovery plus opaque domain
identity, then rerun successfully 12/12. No product/runtime semantic failure
occurred.

## File identities

Authorized production post-hashes:

```text
FFB1885B2440DC510B7D04469B0216143BE380798B5A2F236FFFE99F9B30CAA0  assignment_lifecycle_transaction_runtime.py
545274EEF630977E97C1064D831F5841DC97E8A38AA720E4474DEB7BEC7197B7  assignment_event_profile_runtime_domain.py
56A7A81160A007413D56F62B982A500DEFC66F4F37E884ABB7A0C96313CAF496  assignment_event_profile_synchronous_runtime.py
```

Dedicated runner hashes:

```text
837EECD642A7A3A5F9BC077EDD5244F5FE423DCCEFA14C689A189536A82940B1  test_assignment_phase_b1w_i3_terminal_consumer_integration_pure.py
9C09A811745F505E2A76C23585904EBBAD17554855C946BBD6DC8C839E17D585  test_assignment_phase_b1w_i3_real_isaac_terminal_smoke.py
```

Protected identities remained exact:

```text
17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609  assignment_interstep_claim_window_runtime.py
C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99  scan_mobile_manipulator_env.py
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31  direct_marl_env.py
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317  assignment_controller.py
3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59  assignment_rl_interface.py
```

## Static and scope audit

```text
py_compile changed/new Python:           passed
git diff --check:                        passed (pre-existing CRLF warnings only)
wrapper terminal/O1 wiring:              zero
training/playback terminal/O1 wiring:    zero
package public export:                   zero; __all__ remains empty
new mutex/cache/tick/state authority:    zero
environment/DirectMARLEnv change:        zero
controller/RL interface change:          zero
config/readiness change:                 zero
terminal sidecar/learner transport:      zero
```

## Phase boundary

B1W-I3 is complete and awaiting GPT/user review. B1W-I4 is not entered. Event
runtime readiness remains blocked. No wrapper facade, HARL terminal transport,
policy/scheduler/resolver integration, learner/critic sidecar, training,
playback, evaluation, numeric TBD selection, or commit is authorized by this
result.

Stop here. Do not proceed automatically into B1W-I4 or runtime activation.
