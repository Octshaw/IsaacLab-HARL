# Phase B0-3I4 Terminal Handoff and Environment Integration Implementation Report

## Classification

```text
PHASE-B0-3I4-TERMINAL-HANDOFF-AND-ENVIRONMENT-INTEGRATION-COMPLETE-AWAITING-GPT-REVIEW
```

B0-3I4 is complete at the authorized terminal-handoff and direct-environment
integration foundation level. The event profile remains `interface_only` and
Phase-A blocked. Wrapper/HARL terminal transport, runtime-ready activation,
assignment commit, Phase B/C/D/E, training, playback, and evaluation remain
unauthorized and unimplemented.

No B0 contract/runtime or composition-root profile-identity stop condition was
reached. The exact canonical resolved event profile and the one retained
runtime domain are supplied by the composition root as constructor objects;
the environment performs no string/YAML/enum resolution and constructs no
parallel domain.

## Repository boundary

```text
starting HEAD: 912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:   912b3b59831fcad8dd29ac575b2a1851bf2c21d1
branch:        main
index:         empty
commit:        none
```

The pre-existing uncommitted B0 cohort was preserved. The I4 implementation
delta is limited to:

1. `scan_mobile_manipulator_env.py` for exact profile/domain transport,
   event-only staged scan/done/reward/reset hooks, and the synchronous R3
   permission check.
2. `assignment_event_profile_runtime_domain.py` for terminal observer,
   designated consumer, environment permission/failure ports, terminal keys,
   and terminal-aware I3 finalization.
3. `assignment_lifecycle_transaction_runtime.py` for the private terminal slot
   store and the same-lock terminal-aware coordinator success tail.
4. New I4 terminal and environment integration tests.
5. Narrow I2/I3 static-oracle updates recognizing the authorized I4 extension.
6. The intentional default-off environment source digest refresh after the
   legacy-preserving branch addition.
7. This report and the concise top-level handoff.

No frozen Phase-A contract, wrapper, resolver, controller, HARL adapter,
training/playback/evaluation entrypoint, checkpoint schema, scenario YAML, or
numeric selection policy changed.

## Canonical composition and capability split

The event environment constructor accepts only:

```text
resolved_assignment_profile       exact ResolvedEventGatedAssignmentProfile
event_lifecycle_runtime_domain    exact _EventProfileLifecycleRuntimeDomain
```

The domain's retained profile object must be the same Python object as the
transported resolved profile. Device, full env-ID vector, M, and N must match
the constructed environment exactly. Raw strings, mappings, foreign resolved
types, missing event domains, and event domains on existing/default routes are
rejected.

The composition root retains the domain and therefore can distribute:

```text
current_read_port
terminal_observer_port()          repeatable read-only ports
terminal_consumer_port            exactly one designated read/ack port
```

The environment retains only `_EventProfileLifecycleEnvironmentPort`. It has
no terminal read or acknowledgement method and receives no store, clock,
ledger, receipt, authority, coordinator, or terminal-store capability.

The four existing profiles and the absent/default legacy route receive no
event domain and continue through the prior scan, done, reward, and reset
branches.

## Terminal artifact and one-slot store

Each terminal row installs one immutable artifact under:

```text
(env_id, episode_generation, transition_generation)
```

The artifact binds:

```text
exact LifecycleTransitionResult identity
exact pre-reset PublishedLifecycleView identity
authoritative termination reason and done projection
canonical coverage_after_transition row
facts consume token
authority receipt ID
row-scoped lifecycle events
optional sidecar = None
```

Coverage storage is detached, cloned, contiguous, and returned through a
cloned accessor. Result and published-view objects are already immutable
canonical artifacts. There is exactly one slot per environment row.

An occupied terminal row is rejected during receipt-free prevalidation before
ledger consume. No overwrite, latest-slot replacement, automatic drop, or
implicit acknowledgement exists.

Observer reads are exact-key, repeatable, and non-destructive. The unique
consumer can read and acknowledge only the exact occupied key. Wrong, stale,
foreign, empty, and duplicate operations reject without mutation or poison.
Acknowledgement removes exactly one row.

## Same-lock publication boundary

The reviewed public B0-2 coordinator API remains exactly:

```text
poisoned
read_published_view()
transact(*, facts, transition_contexts)
```

I4 adds only a private terminal-aware transaction route used by the retained
domain. Under the existing coordinator publication lock it performs:

```text
capture exact StateStore snapshot and clock reservations
derive and receipt-free prevalidate the full candidate
validate terminal capacity
ledger.consume once
factory.finalize once
prepare immutable published view and replacement terminal-slot map
StateStore pointer swap
generation-clock commit
install current published view
install prepared terminal-slot map
release publication lock
```

All external current-view, terminal-read, terminal-ack, and physical-step
permission operations acquire the same publication lock. Therefore no reader
can observe the new terminal lifecycle publication without its matching slot.

Failure after receipt issuance poisons the coordinator. There is no rollback,
retry, second consume, cancellation, automatic acknowledgement, or continued
fresh read. An injected terminal-install failure proves the finalized receipt
and committed authority state are not misrepresented as a successful
publication.

## Synchronous R3 permission rule

`ScanMobileManipulatorEnv._pre_physics_step()` begins with the exact executable
statement:

```python
self._assert_event_physical_step_allowed()
```

For the event route this enters the coordinator publication lock and rejects
with `failure_code="terminal_ack_required"` if any row is occupied. One blocked
row blocks the full vector-domain physical step. The check does not wait,
poll, auto-ack, mutate actions, copy previous actions, integrate task-space
state, or mark debug state.

`DirectMARLEnv.step()` moves action tensors to the environment device before
the task hook. Its optional action-noise stage is also before the hook, so the
event constructor rejects any non-`None` action-noise configuration before
base environment construction. The current event route therefore satisfies
the required zero-work guard boundary without modifying Isaac Lab core.

## Event scan/done/reward order

The event-only hook order is:

```text
R3 permission guard
action preparation and physics
episode counters
nonmutating scan predicate and dwell_next staging
raw [E,M,N] candidate + horizon report
I3 owner qualification and B0 authority transaction
terminal view + slot installed under one lock
commit dwell/coverage/reward evidence
existing reward formula
authoritative terminated/truncated return
autoreset through I1
new-episode observation
```

The staged detector does not mutate dwell, coverage, reward evidence, actions,
or lifecycle state. The adapter still owner-qualifies completion against the
exact active prestate. Passive/non-owner scan candidates produce no completion,
coverage, event, or own reward attribution.

Environment bookkeeping commits only:

```text
dwell_counter              staged dwell_next
viewpoints_covered         outcome.coverage_after_transition
global coverage gain       result.completed_tasks count
own coverage gain          canonical completion_signals count
duplicate scans            staged physical duplicate evidence
```

The existing reward equation and scales remain unchanged. If environment
bookkeeping raises after authority publication, the exact outcome is reported
through the narrow environment port and the coordinator is poisoned; no
rollback or continuation is attempted.

Event `_get_dones()` returns only the authoritative outcome projection.
Timeout mapping remains:

```text
physical_truncated == time_limit_reached
bad_transition == false
```

The existing route continues to call `_update_scan_progress()` and derives its
legacy coverage/time-limit done tensors exactly as before.

## Episode rebuild integration

The composition root constructs the domain before constructing/resetting the
event environment. Domain construction itself leaves episode and transition
generations at `-1`.

Every event `_reset_idx(selected_env_ids)` executes:

```text
enter environment_port.episode_rebuild(selected rows)
super()._reset_idx(selected rows)
reset selected native scan/action/reward/debug buffers
commit_physical_reset_complete()
exit rebuild/publication lock
```

The first reset advances selected episode rows `-1 -> 0`; later manual,
partial, and autoreset calls use the same primitive. Transition generations are
preserved across rebuild. Terminal slots are not reset and remain readable by
their historical exact key while the current publication advances to the new
episode with `result=None`.

Native reset and scan-buffer reset do not call a lifecycle read/transaction
port, so there is no lifecycle-lock re-entry and no `RLock` workaround.

## Tests

### New I4 terminal suite

```text
scripts/environments/test_assignment_phase_b0_3i4_terminal_handoff_pure.py --json
status=passed, num_tests=16, passed=16, failed=0
```

The groups cover exact artifact installation, reset survival, repeatable
observers, designated exact acknowledgement, wrong/stale/duplicate keys,
foreign consumer rejection, observer isolation, per-row release, occupied
receipt-free rejection, install failure poison, publication/slot atomicity,
historical/current coexistence, R3 block/release, full-domain block, and the
explicit absent sidecar/HARL/readiness boundary.

### New environment integration audit

```text
scripts/environments/test_assignment_phase_b0_3i4_environment_integration.py --json
status=passed, num_tests=12, passed=12, failed=0
```

This parses the actual environment and DirectMARLEnv methods and freezes exact
constructor transport, first-statement R3 placement, base action order,
nonmutating staging, authority-before-bookkeeping order, authoritative
coverage/reward/done evidence, reset wrapping, legacy branch preservation, and
the no-wrapper/readiness boundary.

### Required regressions

```text
B0-3I3 staged adapter              16/16 passed
B0-3I2 retained domain             12/12 passed
B0-3I1 episode rebuild             12/12 passed
B0-2 authority transaction         18/18 passed
B0-1A facts producer                9/9 passed
B0-1B generation clock             12/12 passed
lifecycle transition contract      12/12 passed
assignment profile contract        16/16 passed
event-profile schema                9/9 passed
Phase-A default-off identity        16/16 passed
profile production wiring          10/10 passed
event-gated MRTA contract           13/13 passed
```

The default-off source hash was intentionally refreshed only after the event
branch was added. The full default-off suite then passed 16/16, providing the
legacy/default identity regression rather than relying on the digest alone.

### Headless smoke boundary

The focused `num_envs=2` event/legacy smoke was attempted only after all pure
gates were green. Two bounded attempts produced no application or scene log
before timeout:

```text
attempt 1: 604 seconds, exit 124
attempt 2: 244 seconds, exit 124, conda --no-capture-output
```

Both runs retained responsive, CPU-active Python processes. The exact child
PIDs were terminated after their command timeouts. There was no exception,
traceback, environment-step result, or runtime identity evidence to diagnose.
Accordingly:

```text
headless smoke: ATTEMPTED / NO AUDITABLE RESULT / NOT CLAIMED PASSED
```

No training, playback, evaluation, HARL wrapper, checkpoint, or performance
run was started.

## Final file identities

```text
030efb1be030c6f1bb22bb2dcf5918d0235305cb5d543d01569c1066836501d5  scan_mobile_manipulator_env.py
8491398d03a16fa34ab0c7e5e62b858d81308ffffadc959d5b59f8b71aa2dc7a  assignment_event_profile_runtime_domain.py
f77ba9b713e4ab394b389edff16d19b992d944c5851cad232b4dbca42088d803  assignment_lifecycle_transaction_runtime.py
49cd8e0f51503d58bb549d32a5786646f825d7c454f2cb7f8f39b01139776db0  test_assignment_phase_b0_3i4_terminal_handoff_pure.py
fa8c3836ca60a42226e064e4a5abbb746f6ea0ce3a763e8bc17d3d60e2ffc5ba  test_assignment_phase_b0_3i4_environment_integration.py
```

## Deferred boundaries

The following remain explicitly deferred:

1. Runtime readiness and profile-gate activation.
2. Wrapper/HARL terminal artifact capture and exact-key acknowledgement.
3. Assignment/claim/transfer commit and ordinary lifecycle phase progression.
4. Physical structural failure, forced release, unavailable, and recovery
   reporters beyond the frozen zero-valued I3 adapter fields.
5. Optional terminal diagnostic sidecar.
6. Checkpoint, actor/shared observation, mask, policy, training, playback, and
   evaluation integration.
7. A successful focused Isaac headless runtime smoke.

## Final authorization state

```text
B0-3I4 implementation:                 complete, awaiting GPT/user review
event runtime readiness:               interface_only / blocked
wrapper/HARL terminal transport:       not implemented / not authorized
Phase B/C/D/E:                          not entered / not authorized
training/playback/evaluation:           not run
headless runtime smoke:                 attempted, no auditable result
commit:                                 none
```
