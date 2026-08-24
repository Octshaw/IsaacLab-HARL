# Phase B0-3I3 Staged Pre-reset Reporter and Facts Adapter Implementation Report

## Classification

```text
PHASE-B0-3I3-STAGED-PRE-RESET-REPORTER-AND-FACTS-ADAPTER-COMPLETE-AWAITING-GPT-REVIEW
```

B0-3I3 is complete only at the pure, dormant, default-off staged-report and
facts-adapter level. It adds no Isaac environment hook, terminal slot/ack,
pre-step guard, production entrypoint, runtime-ready route, reward formula, or
environment coverage mutation.

No prescribed stop condition was reached:

```text
B0-3I3 PRESTATE-CAPABILITY GAP:       not reached
B0 CONTRACT/RUNTIME GAP:              not reached
B0-3I3 BAD-TRANSITION ADAPTER GAP:    not reached
B0-3I3 PENDING-TRANSITION RETRY GAP:  not reached
B0-3I3 SCOPE EXPANSION REQUIRED:      not reached
```

## Repository boundary

```text
starting HEAD: 912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:   912b3b59831fcad8dd29ac575b2a1851bf2c21d1
branch:        main
index:         empty
commit:        none
```

The pre-existing uncommitted B0 cohort was preserved. The authorized I3 delta
is:

1. Extended
   `assignment_event_profile_runtime_domain.py` with the staged report,
   retained adapter orchestration, immutable outcome, and narrow port method.
2. Added one private exact-prestate capture operation to
   `assignment_lifecycle_transaction_runtime.py`; its reviewed public
   coordinator surface and `transact()` signature remain unchanged.
3. Added
   `test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py`.
4. Narrowly updated the I2 static regression to recognize the authorized I3
   `finalize_physical_transition` port while continuing to reject raw
   clock/store/facts capabilities and all I4 capabilities.
5. Added this report, archived the prior handoff, and rewrote
   `AgentRead/TASK_PROGRESS.md`.

No frozen contract, environment, wrapper, resolver, controller, HARL,
configuration, checkpoint, installed-package, or numeric-policy file changed.

## Staged raw report DTO

`_StagedPreResetPhysicalReport` is a B0-private, immutable/no-alias record with
exact fields:

```text
device                       exact torch.device
coverage_before_transition   [E,N] bool
raw_new_candidate            [E,M,N] bool
physical_truncated           [E] bool
time_limit_reached           [E] bool
```

It stores detached, cloned, contiguous tensors and returns cloned accessors.
It rejects wrong rank, E/M/N, dtype, device, layout, gradient state, and
unsupported truncation mapping. Noncontiguous strided ingress is captured into
canonical contiguous storage.

The DTO intentionally contains no:

```text
profile or env IDs
generation
ownership or lifecycle state
physical_terminated
bad_transition
completion_signals
failure/release/health signals
reward or termination reason
```

Thus the caller provides only material available from the physical detector
and current horizon boundary before coverage/reset mutation.

## Deferred reporter policy

The current scan skeleton has no real reporters for:

```text
terminal_pair_failure_signals
forced_release_signals
robot_unavailable_signals
robot_recovered_signals
```

The adapter supplies canonical all-false tensors internally. These false edges
mean only that the reporter is unavailable for the current skeleton. The
environment port cannot invent these signals, and B0-2 remains the lower-level
oracle for their semantic behavior.

## Exact bad-transition and timeout mapping

The current scan runtime exposes only its episode-horizon timeout:

```text
time_out = episode_length_buf >= max_episode_length - 1
```

There is no independent bad-transition or non-time-limit truncation reporter.
I3 therefore freezes the narrow mapping:

```text
physical_truncated == time_limit_reached
bad_transition = false, generated inside the adapter
```

The staged DTO has no bad-transition input. A mismatch between physical
truncation and time limit rejects before transition-context reservation. No
unsupported terminal/truncation route can be fabricated by the caller.

## Environment port surface

The supported environment port surface is exactly:

```text
episode_rebuild(...)
finalize_physical_transition(staged_report)
```

The separate current-read port remains exactly:

```text
read_current()
```

The environment receives no producer, generation clock/context, StateStore or
snapshot, coordinator, authority, ledger, receipt, result factory, writer
capability, or raw publication lock.

## Transition reservation and pending identity

`finalize_physical_transition()` validates the immutable full-E report first,
then requests one transition candidate for every retained environment row from
the one retained `LifecycleGenerationClock`. It never reserves before the raw
report exists and never accepts caller-supplied generations.

The domain retains one private `_PendingPhysicalTransition` binding:

```text
exact staged report object identity
exact all-E TransitionGenerationContext tuple
exact StateStore identity/version/prestate once captured
```

While pending, a different report object fails with
`pending_report_identity`. The adapter never cancels the context, requests a
replacement, skips a generation, or starts another physical transition.

Successful B0-2 transaction commit clears the pending record. The clock's own
commit clears the exact outstanding contexts; I3 performs no second commit.

## Exact prestate binding and C2

The coordinator now has one B0-private method:

```text
_capture_execution_prestate(env_ids, transition_contexts)
```

It acquires the same publication lock as `transact()`, rejects poison, captures
the writer-capability StateStore snapshot, requires the exact full domain, and
validates the exact outstanding contexts. It is not public/exported and is
never exposed through an environment port.

The adapter captures and binds this snapshot after all-E reservation. On every
attempt, including retry, it recaptures under the publication boundary and
requires exact:

```text
store identity
store version
env/task/robot/owner state
failed pairs
completion counts
termination reason
```

The all-E outstanding contexts block supported episode rebuild and competing
transition reservation. The retained domain operation lock serializes its
episode-rebuild and physical-finalize capabilities. Finally, unchanged B0-2
`transact()` independently captures current state and proves the facts prestate
matches it before consume.

Therefore:

```text
owner-gating prestate
== facts prestate
== coordinator-validated prestate
```

No `read_current()`-then-later-transact race or raw StateStore capability was
introduced.

## R1 owner qualification

The exact equations are:

```text
active0[e,j] =
  task0[e,j] in {CLAIMED, NAVIGATING, ALIGNING}

completion_signals[e,i,j] =
  raw_new_candidate[e,i,j]
  AND active0[e,j]
  AND ownership0[e,j] == i

canonical_task_completion[e,j] =
  any_i completion_signals[e,i,j]

prospective_coverage[e,j] =
  coverage_before_transition[e,j]
  OR canonical_task_completion[e,j]

physical_terminated[e] =
  all_j prospective_coverage[e,j]
```

The adapter validates `sum_i completion_signals[e,i,j] <= 1` before producer
use. Passive non-owner raw candidates remain physical diagnostics and produce
no canonical completion, coverage, count, event, or terminal assertion.

## Canonical facts production

The adapter constructs the existing private `ExecutionTransitionInput` with:

```text
retained env IDs
episode/transition generations from exact contexts
R1 physical_terminated
supported timeout/truncation and bad_transition=false
owner-qualified completion_signals
four deferred reporter tensors=false
raw coverage-before-transition basis
exact bound task/robot/ownership prestate
```

It calls the one retained `EnvironmentExecutionFactsProducer.build_facts()`.
The producer alone allocates tokens and constructs the frozen
`ExecutionTransitionFacts`, including:

```text
coverage_before_reset =
  coverage_before_transition OR completion_signals.any(dim=1)
```

I3 defines no parallel facts DTO, producer, token allocator, authority, ledger,
or result-finalization path.

## B0-2 transaction reuse

After facts construction, the adapter invokes unchanged:

```python
coordinator.transact(
    facts=facts,
    transition_contexts=exact_pending_contexts,
)
```

B0-2 remains responsible for completion/release/failure equations, C1, TEAM,
robot projection, reason priority, events, ledger consume, result finalize,
StateStore swap, clock commit, poison, and publication.

A no-event physical step still processes all E rows and produces exactly one
full-batch result, one global StateStore version increment, one contiguous
transition generation per row, and an empty lifecycle event tuple.

## Immutable physical-transition outcome

`_EnvironmentPhysicalTransitionOutcome` contains:

```text
PublishedLifecycleView
finalized LifecycleTransitionResult
completion_signals             [E,M,N] bool
canonical_task_completion      [E,N] bool
coverage_before_transition     [E,N] bool
coverage_after_transition      [E,N] bool
terminated                     [E] bool
truncated                      [E] bool
```

All outcome tensors are detached, cloned, contiguous, and returned through
clone accessors. The view/result are the immutable generation-bound canonical
objects produced by B0-2.

Coverage evidence is exact:

```text
coverage_after_transition =
  coverage_before_transition OR result.completed_tasks
```

It is not derived from raw candidate reduction. I3 performs no environment
coverage copy, dwell write, reward computation, reward-buffer mutation, reset,
or observation publication.

## Receipt-free failure and explicit retry

Facts/producer or receipt-independent authority failure leaves:

```text
same staged report identity retained
same TransitionGenerationContext tuple outstanding
same bound StateStore prestate/version retained
committed transition generation unchanged
StateStore/publication unchanged
no coverage/reward/outcome
```

There is no automatic retry API. Explicitly calling
`finalize_physical_transition()` again with the same report object reuses the
same pending context and requires the same exact prestate. A different report
cannot overwrite it.

Controlled evidence proves:

```text
first successful token: q
failed next build burns: q+1
same-report retry token: q+2

facts token delta:              2
committed transition delta:     1
```

A deterministic prestate interlock changes the store version after the bound
capture. Revalidation rejects `stale_bound_prestate` before consume and
preserves the outstanding candidate.

## Timeout and terminal behavior without I4

The supported horizon-only transition yields `TIME_LIMIT`, `terminated=false`,
and `truncated=true`. Simultaneous canonical completion at the horizon retains
B0-2 priority and yields `ALL_TASKS_COMPLETED`, `terminated=true`, and
`truncated=false`.

I3 can return a terminal outcome, but it adds no persistent terminal slot,
read/ack port, destructive consumer, terminal observer, autoreset integration,
or synchronous ack-before-step guard. Those remain B0-3I4 work.

## Dedicated I3 tests

The standalone pure runner contains exactly sixteen groups:

1. staged report validation and alias isolation;
2. no-event all-E transition;
3. passive non-owner counterexample;
4. exact owner completion/count/event;
5. owner completes the last task;
6. mixed owner/non-owner raw candidates;
7. structural reporters remain deferred;
8. timeout and terminal-over-timeout priority;
9. canonical coverage outcome;
10. producer/consume/finalize/swap/clock/publication success counts;
11. receipt-free producer failure and same-report/context retry;
12. stale prestate/version rejection;
13. immutable/no-alias outcome;
14. terminal outcome without I4 side effects;
15. capability/export isolation;
16. existing-profile/default-off/no-production-wiring boundary.

Results:

```text
normal: status=passed, num_tests=16, passed=16, failed=0
-I -B:  status=passed, num_tests=16, passed=16, failed=0
```

## Regression results

```text
B0-3I2 retained domain/capability ports       12/12 passed
B0-3I1 episode rebuild transaction            12/12 passed
B0-2 lifecycle authority transaction          18/18 passed
B0-1A execution facts producer                 9/9 passed
B0-1B generation clock                        12/12 passed
lifecycle transition contract                 12/12 passed
assignment profile contract                   16/16 passed
event-profile schema contract                  9/9 passed
Phase-A default-off identity                   16/16 passed
profile production wiring                     10/10 passed
event-gated MRTA contract                     13/13 passed
```

The I2 regression was updated only where its historical I3-absence oracle was
superseded. It still proves retained lifetime, exact ports, rebuild purity,
poison propagation, no raw authority leak, no I4 capability, and default-off
isolation.

## Interpreter and runtime boundary

All Python checks used:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

The prescribed conda runner performed `py_compile`, I3 normal and `-I -B`, and
all regressions above. No Isaac, AppLauncher, Omni, PXr, HARL runtime, training,
playback, evaluation, or installed-package edit was used.

## Hash audit

I3 runtime and test artifacts:

```text
D260FE28B745E32BE28A2388ECA54EF174A5252DAAB3F20E0C88475258244173  assignment_event_profile_runtime_domain.py
3CF60E4A00C9DF772DF250C3B34D004D7E057AE937F30DEB13C7CE816B0122F2  assignment_lifecycle_transaction_runtime.py
1C6DF31F8E10B6BAC5C5632AA0301FB992CB608E1A66B0FDACDB709274F608E0  test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
553D917A179A5B1BD53F90C055173CD954D77007C2BA0909D7319216E03D5714  test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py
```

Frozen contracts remained byte-identical:

```text
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
```

Production boundaries remained byte-identical:

```text
2CBCE531BF8B4A1847C838BCCAA4EA17B82F1CAF53DD49C1B54FE17B488C7F74  scan_mobile_manipulator_env.py
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
```

## Default-off, scope, and readiness

Repository searches find the I3 runtime symbols only in the private runtime,
dedicated pure tests, and documentation. There is no construction or import in
the environment, package initializer, wrapper, resolver, controller, HARL,
config, training, or playback path.

The event profile remains:

```text
runtime readiness: interface_only
training support:  phase_a_blocked
playback support:  blocked
```

`require_assignment_profile_runtime_ready()` is unchanged and still rejects.
The four existing profiles construct no I3 domain/capability.

## Deferred and unauthorized

Still not implemented or authorized:

```text
real failure/release/unavailable/recovered reporters
environment _get_dones/_get_rewards/_reset_idx wiring
coverage, dwell, reward, action, or observation mutation
terminal slot/store/read/ack/designated consumer
R3 pre-step permission guard
real autoreset integration
B0-3I4
Phase B/C/D/E
```

All eleven numeric TBDs remain unresolved:

```text
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
```

## Final boundary

B0-3I3 is complete and awaiting GPT/user review at the pure/dormant staged
report and facts-adapter level only. Do not infer authorization for B0-3I4,
real environment integration, event-profile runtime readiness, or any later
phase.
