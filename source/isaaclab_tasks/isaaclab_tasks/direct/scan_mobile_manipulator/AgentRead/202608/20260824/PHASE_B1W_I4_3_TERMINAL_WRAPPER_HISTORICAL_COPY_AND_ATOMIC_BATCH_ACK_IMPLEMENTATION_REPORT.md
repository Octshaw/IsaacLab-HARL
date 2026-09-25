# Phase B1W-I4-3 Terminal Wrapper Historical Copy and Atomic Batch ACK Implementation Report

## Classification

```text
PHASE-B1W-I4-3-TERMINAL-WRAPPER-HISTORICAL-COPY-AND-ATOMIC-BATCH-ACK-COMPLETE-AWAITING-GPT-REVIEW
```

Terminal capture, bounded immutable history copy, full-copy validation, one
atomic multi-key exact ACK, wrapper-private handoff, and post-ACK recovery are
implemented and pure/static verified. B1W-I4-4 was not entered. Runtime
readiness remains blocked.

## Repository boundary and execution gate

```text
repository: E:\Project\IsaacLab_HARL
branch: main
HEAD: 912b3b59831fcad8dd29ac575b2a1851bf2c21d1
preflight index: empty
working tree: existing reviewed phase cohort preserved
commit: none
interpreter: C:\isaacenvs\isaac45_harl\python.exe
```

No real Isaac/AppLauncher run, HARL process, training, playback, evaluation, or
runtime smoke was started. No public learned-policy event route was activated.

## Changed and new files

Production implementation:

- `assignment_lifecycle_transaction_runtime.py`: sole-authority batch ACK.
- `assignment_event_profile_runtime_domain.py`: same-domain designated consumer batch port.
- `assignment_event_profile_synchronous_runtime.py`: narrow O1 batch forwarding method.
- `assignment_event_runtime_facade.py`: shared terminal capture/copy/ACK finalizer for continuation and proposal routes.
- `assignment_event_terminal_transport.py`: new B-private immutable historical transport.
- `assignment_harl_wrapper.py`: bounded latest-result side channel and terminal cache clearing.

Pure/static evidence:

- new `scripts/environments/test_assignment_phase_b1w_i4_3_terminal_wrapper_handoff_pure.py` with 26 meaningful cases;
- I4-2 and I4-1 terminal boundary oracles advanced from the formerly deferred failure to I4-3 success;
- Phase-A wrapper digest refreshed after the authorized wrapper change;
- I3 and B0-I2 capability inventories include the new batch method;
- B0-3I4 environment scope evidence recognizes private I4-3 transport while continuing to prohibit environment-owned ACK and public facade capture/ACK.

No frozen contract, environment production path, controller, RL interface, B1,
fence, resolver, proposal adapter, training, runner, or configuration file was
changed by I4-3.

## Atomic batch exact ACK

The coordinator method is `_acknowledge_terminal_batch(keys, capability)`. It
runs under the existing `_publication_lock`, uses the existing
`_terminal_slots`, unique designated consumer capability, and coordinator
poison authority, and performs this order:

1. require a healthy coordinator and the exact issued consumer capability;
2. require an exact tuple of exact `_TerminalTransitionKey` values;
3. reject duplicate keys and duplicate environment rows;
4. validate every addressed slot and its exact `(env_id, episode_generation, transition_generation)` binding;
5. prepare the env-ID-ascending exact stored-artifact return tuple;
6. prepare the full replacement slot dictionary while the original remains untouched;
7. execute the sole authoritative mutation, `self._terminal_slots = replacement`;
8. return the already-prepared exact stored artifact identities.

There is no `pop`, sequential delete, second registry, second lock, ACK cache,
generation/tick, transaction coordinator, or second poison state. All
validation and allocations occur before publication; after the one assignment,
the method only returns the prepared tuple. Therefore one bad row removes zero
slots, full success removes all addressed rows, and partial successful ACK is
impossible by construction. An empty exact tuple validates health/capability
and returns `()`. The pre-existing single-key `acknowledge_terminal` method and
its exact identity semantics remain unchanged.

Dedicated T1-T8, T21, and T23 prove E=2 success, canonical return order, exact
returned object identities, repeatable capture identities, foreign consumer
rejection, malformed input rejection, duplicate/missing/wrong second-key
all-or-none retention, empty no-op, preserved single-key ACK, one slot-map
publication in the batch method, and no new lock or second authority.

## Capability chain

```text
sole coordinator _terminal_slots
  -> designated _EventProfileTerminalConsumerPort
  -> EventProfileSynchronousRuntimeCoordinator O1
  -> EventAssignmentRuntimeFacade private finalizer
  -> bounded wrapper step-result value
```

The consumer adds `acknowledge_terminal_batch(exact_keys)`. O1 adds
`acknowledge_terminal_artifacts(exact_keys)` and only forwards to that exact
same-domain port. O1 retains no artifacts, keys, terminal cache, learner
lifetime, Store/P2 authority, window authority, or terminal state machine. The
wrapper never receives the raw consumer, coordinator, domain, or slot map. The
facade exposes no raw capture or ACK public/private method to wrapper callers;
its terminal finalizer uses only the already-composed O1 capability.

## Historical DTO and raw-artifact copy map

`EventTerminalHistoricalRow` is frozen, slotted, `eq=False`, factory
controlled, private (`__all__ == ()`), and bounded to one facade/wrapper step
result. Direct construction is rejected. It never stores a
`_TerminalHandoffArtifact` reference.

| Runtime artifact evidence | Historical row field |
|---|---|
| exact key | `env_id`, `episode_generation`, `transition_generation` |
| authoritative flags | `termination_reason`, `terminated`, `truncated` |
| consume/receipt evidence | `facts_consume_token`, `authority_receipt_id` |
| finalized result identity | `result_schema_version`, `authority_contract_version`, `facts_producer_id`, `authority_id` |
| published terminal view | `published_store_version`, copied `completion_count` |
| pre-reset evidence | copied `coverage_after_transition` |
| finalized lifecycle result rows | copied `completed_tasks`, `released_tasks`, `new_failed_pairs`, `updated_failed_pairs`, `new_team_infeasible_tasks`, `updated_task_state`, `updated_robot_state`, `updated_ownership` |
| lifecycle history | distinct copied lifecycle records and payload objects |
| deferred critic evidence | `optional_sidecar = None` |

Every tensor is detached, cloned, and made contiguous at construction. Tensor
properties return another detached clone, so a caller cannot mutate the stored
historical value. T9 checks all ten copied tensor fields, distinct storage, and
getter isolation. Lifecycle records and their immutable payloads are copied by
value with distinct identities. T20 verifies `optional_sidecar is None`, no
critic synthesis, and no package export.

## Copy-before-ACK and lifetime validation

After the physical O1 call has completed Ak and opened the exact next window,
the shared facade finalizer:

1. captures all pending artifacts in canonical env-ID order;
2. requires nonterminal return iff capture is empty, or exact terminal-row/capture correspondence;
3. copies every captured artifact;
4. validates full cardinality, key/generation/reason/flag/token/receipt bindings, event copies, and tensor no-alias properties;
5. validates historical episode `e`, transition `t` against current post-autoreset P2 episode `e+1`, transition `t`, `result=None`, reason `NONE`, and nonterminal flags;
6. derives the canonical exact-key tuple only from the completed historical copies;
7. calls O1 batch ACK exactly once;
8. requires the ACK return to contain the exact captured artifact objects;
9. verifies ACK changed neither P2 identity/version/generations nor the OPEN window/poison state and left no slot pending.

T10 observes that all runtime slots remain occupied after a successful full
copy and before ACK. T11 injects a terminal-return mismatch and proves copy
failure performs zero ACK, preserves exact slot identities, and leaves R3
blocking the next step. Wrong, missing, stale, duplicate, malformed, and
foreign-capability batch failures likewise preserve the whole batch. T14
proves successful ACK changes only terminal-slot occupancy.

The authoritative reason is copied from the artifact and is never inferred
from environment done flags. Historical data is never reconstructed from the
current reset P2, and current P2 is never overwritten by history.

## Facade and wrapper integration

Both existing private physical routes call the same terminal finalizer:

- no-new-claim continuation: `step_without_new_claim`;
- proposal interpretation / zero-or-one M1 commit: `step_resolved_proposals`.

Nonterminal results retain the exact `terminal_historical_payload == ()`
behavior. Terminal results contain the bounded historical row tuple and the
current raw environment observation remains the post-reset/current
observation. The proposal route preserves its exact B1 artifact cardinality,
final P2 -> Ak controller source, and committed interpretation diagnostics.

On a terminal result the wrapper clears proposal/effective/assignment and old
facade-result convenience caches, then retains only the newly returned bounded
step result. It owns no terminal queue or episode history. Reset clears the
bounded result, and the next step replaces it; nonterminal cache behavior is
unchanged. T12-T18 prove both terminal routes, cache clearing, historical/current
separation, current observation identity, bounded value lifetime, exact ACK,
and post-ACK recovery to a fresh OPEN window without poison.

## Preserved stop boundary

Public `AssignmentHarlWrapper.step(actions)` for the exact event profile still
fails closed before environment mutation. Lifecycle actor/shared observation
identity, action mask/DVM, forced-row actor sampling, critic sidecar, learner
transport, runner transport, and TIME_LIMIT GAE semantics remain absent. No
synthetic current observation, mask, critic state, or pre-reset physical
sidecar was introduced. Existing four non-event profiles remain isolated.
Runtime readiness remains `INTERFACE_ONLY`/blocked. I4-4 was not entered.

## Dedicated and regression evidence

Every row passed in both normal and `python -I -B` modes:

| Suite | Result per mode |
|---|---:|
| I4-3 terminal copy / atomic batch ACK | 26/26 |
| I4-2 proposal/effective commit | 22/22 |
| I4-1 facade/reset/continuation | 15/15 |
| Phase-A default-off identity | 16/16 |
| profile contract | 16/16 |
| profile production wiring | 10/10 |
| B1 initial claim | 23/23 |
| B1W fence | 26/26 |
| B1W-I1 coordinator/environment admission | 28/28 |
| B1W-I3 terminal consumer | 13/13 |
| B0-3I1 rebuild transaction | 12/12 |
| B0-3I2 runtime domain | 12/12 |
| B0-3I3 staged reporter | 16/16 |
| B0-3I4 terminal handoff | 16/16 |
| B0-3I4 environment integration | 12/12 |
| frozen lifecycle transition contract | 12/12 |
| frozen event profile schema contract | 9/9 |
| frozen event-gated MRTA contract | 13/13 |

This is 297 passing cases per mode. The I4-3 process audit also verified
unchanged Python/Torch/NumPy RNG, cwd, environment, `sys.path`, logging/profile
registries, filesystem inventory, and absence of Isaac, Omni, pxr, and HARL
imports. The dedicated suite introduced no child process.

`py_compile` passed for all six production implementation modules and the
dedicated test. `git diff --check` passed.

## Protected hashes

Preflight and postflight hashes are identical for every protected production
file:

```text
C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA  assignment_initial_claim_runtime.py
17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609  assignment_interstep_claim_window_runtime.py
28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317  assignment_controller.py
3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59  assignment_rl_interface.py
C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99  scan_mobile_manipulator_env.py
7F64183C638697F16EFA45769978127C7E3575599E87CFA76A5BA26F20EABADB  assignment_lifecycle_resolver.py
03483727573974BB57F96309D9D8A1EC446D87580915747BC57014BB4CC7F754  assignment_lifecycle_resolver_runtime.py
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
B6F32510AE663B3E443891CDD09219DD9A5C9CEB9DE9C720C73192C7488597FD  assignment_harl_training.py
7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31  direct_marl_env.py
```

Authorized production postflight hashes:

```text
F7B80540EF1CA39CA103855B7D1DB2FFEDDE950242EC223061D0BF01F32E7C5C  assignment_lifecycle_transaction_runtime.py
A86B1BCF6A494C570B4DBD048915B2D2EAFBC2E8D9EB055C2934728C166E1822  assignment_event_profile_runtime_domain.py
C7C7200FDEFF4A41756335AF3F274C2F195BC6D2B3E619C07BCD3A88B77912BC  assignment_event_profile_synchronous_runtime.py
036082D8DF61514AA3F3C424AE6559FA678536097B66BFD5BD6F632CA3479478  assignment_event_runtime_facade.py
3DB780B7C9879EAC12D41E0B5BC2FE77F31D7F495EDE7A6AC664C542476973A5  assignment_event_terminal_transport.py
F238536C8A4BED53DA984E4F2D81150F7B634915E49B601D86EB407FAE9FA2AE  assignment_harl_wrapper.py
```

The proposal adapter stayed byte-identical at
`874B4C7B71E6C42F9E6DABEEFA25A708D25D8518E3366FE91B86B9B1A739BEDD`.

## Final status

```text
terminal capture: PASS
bounded immutable historical copy: PASS
raw runtime artifact alias: NONE
full-copy validation before ACK: PASS
multi-row ACK: ATOMIC_BATCH_EXACT_ACK / PASS
full-batch prevalidation: PASS
terminal slot publication: ONE MUTATION
partial successful ACK: IMPOSSIBLE
single-key ACK: PRESERVED
ACK neutrality: PASS
historical terminal / current reset P2: SEPARATED
next-step recovery after ACK: PASS / PURE-STATIC
P2 sole authority: PRESERVED
Ak-only controller: PRESERVED
proposal/M1 semantics: PRESERVED
legacy profiles: UNCHANGED
public learned-policy event step: BLOCKED
critic sidecar: NOT IMPLEMENTED
learner transport: NOT IMPLEMENTED
lifecycle obs/mask/DVM: NOT IMPLEMENTED
Isaac: NOT RUN
HARL: NOT RUN
training/playback/evaluation: NOT RUN
B1W-I4-4: NOT ENTERED
runtime readiness: BLOCKED
commit: NONE
```
