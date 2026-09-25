# Phase B0-3I1 Pure Episode Rebuild Transaction Implementation Report

## Classification

```text
PHASE-B0-3I1-PURE-EPISODE-REBUILD-TRANSACTION-COMPLETE-AWAITING-GPT-REVIEW
```

This phase is complete only at the pure/default-off episode-rebuild primitive
level. It does not authorize or claim environment `_reset_idx` integration,
autoreset integration, terminal handoff/acknowledgement, a pre-reset reporter,
or event-profile production readiness.

## Repository boundary

```text
starting HEAD: 912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:   912b3b59831fcad8dd29ac575b2a1851bf2c21d1
branch:        main
index:         empty
commit:        none
```

The worktree was already dirty and contained the untracked B0-1A, B0-1B, and
B0-2 runtime/test/report cohort plus the B0-3 design documentation. Those
pre-existing files were preserved. The B0-3I1 authorized delta is:

1. Modified:
   `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_transaction_runtime.py`
2. Added:
   `scripts/environments/test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py`
3. Added this report.
4. Added:
   `AgentRead/202608/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I1_IMPLEMENTATION_20260814.md`
5. Rewrote the concise top-level `AgentRead/TASK_PROGRESS.md` handoff.

No frozen contract, environment, wrapper, resolver, controller, HARL,
configuration, checkpoint, or installed-package file was changed.

## Implemented B0-private protocol

The implementation stays in the reviewed B0-2 transaction module and reuses
its StateStore, generation clock, coordinator publication lock, poison state,
and `PublishedLifecycleView`. No new public/frozen contract family was added.

The exact pure call shape is:

```python
inputs = _EpisodeRebuildInputs(...)
with coordinator._episode_rebuild(inputs) as rebuild:
    reset_view = rebuild.commit_physical_reset_complete()
```

The leading underscore is intentional. The environment has not been wired,
and B0-2's reviewed public coordinator surface and module `__all__` remain
unchanged.

### Reset input

`_EpisodeRebuildInputs` is an unversioned B0-private immutable/no-alias record.
It binds:

- the exact canonical `ResolvedEventGatedAssignmentProfile` object;
- explicit device;
- nonempty unique selected environment IDs;
- selected initial task-state rows;
- selected initial robot-state rows;
- selected initial ownership rows.

Ingress tensors are exact strided tensors, exact dtype/device/shape, detached,
cloned, and contiguous. Public-style accessors return clones. The coordinator
requires the canonical reset values:

```text
task_state:    AVAILABLE
robot_state:   NEEDS_ASSIGNMENT
ownership:     -1
```

Failed pairs, completion counts, and termination reason are not caller-selected
reset values. The coordinator derives their exact initialization as false,
zero, and NONE.

### Prepared reset candidate

`_EpisodeRebuildCandidate` is another unversioned, transaction-private record.
It binds:

- exact StateStore identity and version;
- selected environment IDs and full-domain row indices;
- one merged full-domain lifecycle state;
- expected full-domain episode vector;
- unchanged full-domain transition vector.

The StateStore's `_prepare_episode_rebuild_swap` validates and allocates the
entire replacement plus replacement snapshot before physical completion is
signalled. The success tail therefore uses the existing guarded one-pointer
swap.

### Narrow completion capability

`_EpisodeRebuildContext` exposes only:

```text
commit_physical_reset_complete
```

It does not expose the store, clock, writer capability, raw episode-advance
operation, publication installation, ledger, receipt, authority stamp, result
factory, rollback, cancellation, or retry capability.

## Preparation and success order

The context acquires and retains the coordinator publication lock throughout
preparation, the simulated physical-reset boundary, and the success tail.

Before yielding the context it performs:

1. poison rejection;
2. exact reset input/profile/device/domain validation;
3. current StateStore snapshot/version capture;
4. full generation-clock capture;
5. exact StateStore/current-publication/clock consistency validation;
6. selected-row outstanding-candidate rejection;
7. full-domain state merge;
8. full reset-state invariant validation;
9. StateStore replacement preparation;
10. expected episode-vector and unchanged transition-vector preparation;
11. `PublishedLifecycleView(result=None)` preparation;
12. final no-mutation store/clock/publication revalidation.

Exiting without the physical completion signal releases the lock and performs
no StateStore, clock, publication, ledger, or poison mutation.

After the signal, the exact no-fail success tail is:

```text
StateStore prepared replacement swap
< LifecycleGenerationClock.advance_episode(selected rows)
< exact selected/full-domain clock validation
< reset PublishedLifecycleView installation
```

The StateStore version increases once globally, including a partial reset.
The clock increments only selected episode generations. Transition generation
is preserved for every row.

## Initial bootstrap and later rebuild

The same primitive handles both cases:

```text
initial bootstrap:
  episode_generation -1 -> 0
  transition_generation remains -1

later rebuild:
  episode_generation k -> k + 1
  transition_generation remains the last committed generation
```

There is no second bootstrap-specific path and no reset of transition history.

## Partial reset

Selected rows are rebuilt to:

```text
task_state                 AVAILABLE
robot_state                NEEDS_ASSIGNMENT
ownership                  -1
cumulative_failed_pairs    false
completion_count           0
termination_reason         NONE
episode_generation         prior + 1
transition_generation      unchanged
```

All unselected lifecycle tensors, episode generations, transition generations,
and outstanding clock entries remain exact. The full-domain StateStore version
still increases exactly once.

## Reset publication

The already-reviewed `PublishedLifecycleView` represents reset unambiguously:

```text
lifecycle_state:       merged reset state
store_version:         prior + 1
episode_generation:    selected + 1, unselected unchanged
transition_generation: unchanged
result:                None
terminated:            false
truncated:             false
```

No `publication_kind`, fake reason, fake transition, or public schema extension
was required. Therefore no B0 contract/runtime or publication-view gap was
encountered.

## Not a lifecycle transition

Episode rebuild performs none of the following:

- `ExecutionTransitionFacts` construction;
- facts token allocation;
- `TransitionConsumeLedger.consume`;
- receipt issuance or finalization;
- `LifecycleTransitionResult` creation;
- lifecycle event creation;
- reward derivation;
- transition generation request or increment.

The dedicated order test also snapshots the consume ledger and proves it is
unchanged by a successful rebuild.

## Failure and poison semantics

### Before physical completion

Ordinary validation errors and a context exit without a completion signal:

```text
StateStore unchanged
clock unchanged
publication unchanged
ledger unchanged
coordinator not poisoned
```

A selected outstanding transition candidate rejects before the signal and is
not cancelled, cleared, or implicitly committed.

### After physical completion

The success tail is treated as no-fail. Any exception poisons the coordinator,
installs no new publication, and permits no normal continuation.

The two dedicated injected failures prove:

1. StateStore swap success followed by clock-stage failure retains the new
   internal state, leaves the clock old, publishes nothing, and poisons.
2. StateStore swap and episode advance followed by publication-stage failure
   retain both internal mutations, publish nothing, and poison.

No rollback, cancellation, retry, second consume, or continued fresh read is
provided. A historical immutable view may still exist in a caller, but fresh
coordinator reads reject after poison.

## Publication atomicity

The reset operation and external current-view reader share the same coordinator
publication lock. The Event-only concurrency test pauses after StateStore swap
and before episode advance, starts a reader, proves the reader is blocked, then
releases the success tail.

Observable pairs are therefore only:

```text
old lifecycle state + old episode + old transition
```

or:

```text
reset lifecycle state + new episode + same transition
```

No sleep-based race was used.

## Dedicated test groups

`test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py` contains
exactly 12 standalone groups:

1. I1-T1 canonical initial bootstrap;
2. I1-T2 ordinary later rebuild;
3. I1-T3 episode-sensitive state clearing;
4. I1-T4 partial reset;
5. I1-T5 selected rows have no outstanding transition;
6. I1-T6 invalid reset inputs and profile/domain gates;
7. I1-T7 abort before physical completion;
8. I1-T8 exact success count/order and untouched ledger;
9. I1-T9 injected clock failure after StateStore swap;
10. I1-T10 injected publication failure after episode advance;
11. I1-T11 Event-based publication atomicity;
12. I1-T12 default-off/profile/capability/side-effect isolation.

Results:

```text
normal:  status=passed, num_tests=12, passed=12, failed=0
-I -B:   status=passed, num_tests=12, passed=12, failed=0
```

## Regression results

```text
B0-2 lifecycle authority transaction       18/18 passed
B0-1A execution facts producer              9/9 passed
B0-1B generation clock                     12/12 passed
lifecycle transition contract              12/12 passed
assignment profile contract                16/16 passed
event-profile schema contract               9/9 passed
Phase-A default-off identity                16/16 passed
profile production wiring                  10/10 passed
event-gated MRTA contract                  13/13 passed
```

The B0-2 regression proves the transition authority, StateStore transition
swap, generation commit, C1/C2 semantics, poison behavior, coordinator public
surface, and module export surface remain exact.

## Verification commands

The prescribed interpreter was verified:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

All Python commands used:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile <changed/new Python files>
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py --json
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -I -B scripts/environments/test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py --json
```

The same interpreter ran each regression script listed above with `--json`.

## Frozen and stability hashes

Frozen files remained unchanged:

```text
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
```

Other stable integration boundaries:

```text
CA7774808FB8901DBC209F61A8915713106A5DC9DA739D1BCE30C8952A21E10E  assignment_lifecycle_authority_runtime.py
2CBCE531BF8B4A1847C838BCCAA4EA17B82F1CAF53DD49C1B54FE17B488C7F74  scan_mobile_manipulator_env.py
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
```

B0-3I1 implementation artifacts:

```text
E4FBF20137637445AFA770ABC0E236F635C2A7BC372A515F5DA4EE5A659CF308  assignment_lifecycle_transaction_runtime.py
90DCAC31AE2F93B1E12C41717DB3ED6C75D137815EEA6D6A22895803EDB14C3A  test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py
```

The transaction runtime's pre-B0-3I1 captured hash was:

```text
478DD5045E8FA243CD2F9EAF1C9E88AEA824CB5C39C659A18F0BB6E4B9AFC936
```

## Scope and side-effect audit

Repository searches found no B0-3I1 reset symbol in the environment, wrapper,
resolver runtime, controller, or task package entrypoint. The dedicated clean
boundary proves:

- no Isaac, Omni, PXr, or HARL module import;
- no RNG mutation;
- no logger mutation;
- no cwd, environment, or `sys.path` mutation;
- no filesystem inventory change during the pure test;
- four existing profiles and raw/lookalike profile values reject;
- event runtime readiness remains `interface_only` and Phase-A blocked.

Final closeout checks passed:

```text
git diff --check
trailing-whitespace scan
Markdown fence balance
report/path/classification checks
frozen hash audit
production-wiring search
changed-scope audit
HEAD and empty-index audit
```

No Isaac/AppLauncher, environment, training, playback, evaluation, or commit
was run.

## Unresolved boundaries

B0-3I1 does not implement or authorize:

- environment `_reset_idx` or DirectMARLEnv autoreset wiring;
- the B0-3I2 dormant aggregate/capability ports;
- the B0-3I3 pre-reset reporter/facts adapter;
- the B0-3I4 terminal slot, destructive ack, or pre-step guard;
- physical termination/reward/coverage reconstruction;
- real failure/release/unavailable/recovered reporters;
- wrapper/resolver/controller/HARL integration;
- Phase-B assignment scheduling or commit;
- checkpoint, training, playback, evaluation, or performance claims.

All numeric TBDs remain unresolved:

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

B0-3I1 is complete and awaiting review at the pure/default-off episode-rebuild
transaction level only. The next session must not infer B0-3I2 or production
environment-integration authorization from this report.
