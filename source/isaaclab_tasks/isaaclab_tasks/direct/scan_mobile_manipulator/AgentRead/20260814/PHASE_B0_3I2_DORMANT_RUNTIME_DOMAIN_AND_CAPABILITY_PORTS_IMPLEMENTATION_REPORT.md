# Phase B0-3I2 Dormant Runtime Domain and Capability Ports Implementation Report

## Classification

```text
PHASE-B0-3I2-DORMANT-RUNTIME-DOMAIN-AND-CAPABILITY-PORTS-COMPLETE-AWAITING-GPT-REVIEW
```

B0-3I2 is complete only at the pure, dormant, default-off domain-composition
level. No environment, wrapper, resolver, controller, HARL, task entrypoint,
configuration, checkpoint, training, playback, or evaluation route constructs
this domain.

## Repository boundary

```text
starting HEAD: 912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:   912b3b59831fcad8dd29ac575b2a1851bf2c21d1
branch:        main
index:         empty
commit:        none
```

The worktree already contained the uncommitted/untracked B0-1A, B0-1B, B0-2,
B0-3I1, design, test, and report cohort. Those files were preserved. The
authorized B0-3I2 implementation delta is:

1. Added
   `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_profile_runtime_domain.py`.
2. Added
   `scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py`.
3. Added this implementation report.
4. Archived the prior concise handoff before its substantial I2 rewrite.
5. Updated `AgentRead/TASK_PROGRESS.md`.

No frozen contract or existing runtime/environment production file was edited.

## Domain class and construction spec

The new canonical, B0-private module contains:

```text
_EventProfileLifecycleDomainSpec
_EventProfileLifecycleRuntimeDomain
_EventProfileLifecycleEnvironmentPort
_EventProfileLifecycleCurrentReadPort
_EnvironmentEpisodeRebuildContext
```

The module has an exact canonical module-identity guard, is not imported by the
task package, and exports an empty `__all__`.

`_EventProfileLifecycleDomainSpec` is a frozen, no-alias construction identity
binding:

```text
exact ResolvedEventGatedAssignmentProfile object
explicit torch.device
stable unique nonnegative int64 env IDs
E
positive exact-int M
positive exact-int N
```

It rejects four existing profiles, raw enums, strings, mappings, `None`,
lookalikes, duplicate/negative/empty/rank/dtype/device-invalid environment IDs,
and invalid M/N. It performs no resolver, CLI, YAML, or string fallback.

The domain captures an independent internal copy of the spec. Caller mutation
of the source environment tensor, a previously issued identity record, or a
returned environment-ID accessor cannot retarget the live domain.

## Canonical pre-bootstrap state

Construction creates one dormant lifecycle state:

```text
task_state                 AVAILABLE
robot_state                NEEDS_ASSIGNMENT
ownership                  -1
cumulative_failed_pairs    false
completion_count           0
termination_reason         NONE
store_version              0
episode_generation         -1
transition_generation      -1
result                     None
terminated/truncated       false
```

Construction is not episode bootstrap. It does not call `advance_episode`,
request a transition candidate, allocate a facts token, consume the ledger,
issue a receipt, or fabricate a result/event. The first delegated I1 rebuild
performs `episode -1 -> 0`.

## Retained authority ownership

One domain instance constructs and retains exactly one:

```text
EnvironmentExecutionFactsProducer
LifecycleGenerationClock
LifecycleStateStore
LifecycleAuthorityTransactionCoordinator
```

The coordinator constructs its reviewed unique:

```text
LifecycleAuthorityRuntime
TransitionConsumeLedger
LifecycleTransitionResultFactory
```

The domain retains aliases to the coordinator's exact authority and ledger; it
does not construct alternates. Thus the domain owns one composition graph, not
a parallel producer/clock/store/authority/ledger stack.

All construction inputs are validated before the domain is returned. Ports are
created only after component construction, canonical pre-bootstrap validation,
and exact profile/domain cross-checks succeed. A failed constructor exposes no
partially usable domain or port.

No module-level mutable registry, env-ID singleton map, or process-wide domain
singleton was introduced. One retained domain per live vector environment
remains a future composition-root ownership obligation.

## Lifetime semantics

Episode rebuild never reconstructs the domain, producer, clock, StateStore,
coordinator, authority, ledger, or ports. Observable repeated rebuild evidence
is:

```text
constructed: version 0, episode -1, transition -1
rebuild 1:   version 1, episode  0, transition -1
rebuild 2:   version 2, episode  1, transition -1
rebuild 3:   version 3, episode  2, transition -1
```

The environment and read ports remain the same retained capability objects
across this sequence. No transition generation or token is created.

## Environment lifecycle port

The exact supported method surface is:

```python
episode_rebuild(
    *,
    selected_env_ids,
    initial_task_state,
    initial_robot_state,
    initial_ownership,
)
```

The environment-style caller does not provide profile, device, domain E/M/N,
store, clock, coordinator, or writer capability. The port injects the exact
domain-owned canonical profile/device into `_EpisodeRebuildInputs`, then only
delegates to the existing I1 coordinator primitive.

The returned `_EnvironmentEpisodeRebuildContext` exposes exactly:

```text
commit_physical_reset_complete
```

Its context-manager entry/exit delegates to I1 and preserves the reviewed
success sequence:

```text
StateStore prepared swap
-> LifecycleGenerationClock.advance_episode(selected)
-> reset PublishedLifecycleView publication
```

It adds no second mutation, episode advance, publication, consume, result, or
event operation. A direct-I1 oracle and port-driven rebuild produce equal
state/version/generation/result views.

## Current read port

The exact supported method surface is:

```text
read_current
```

It directly delegates to `coordinator.read_published_view()`. It never calls
`StateStore.snapshot()` or `LifecycleGenerationClock.snapshot()` and never
reassembles a view outside the C2 publication boundary.

The returned `PublishedLifecycleView` is immutable and generation-bound. Its
tensor accessors return clones; caller mutation of episode or state copies does
not affect a later read.

## Intentionally unexposed capabilities

The domain's supported surface contains only:

```text
identity
environment_port
current_read_port
```

Neither port, the rebuild wrapper, nor the domain provides a supported getter
or operation for:

```text
producer
clock or clock snapshot
StateStore or raw snapshot
authority
ledger
coordinator
result factory
receipt
authority stamp
writer capability
raw lock
episode advance
transition request/commit
publication installation
components/debug_components escape hatch
```

The construction identity exposes only the canonical profile object, device,
environment IDs, and E/M/N. All capability ports are frozen and permanently
bound to their parent domain.

## Poison propagation

No domain-level poison flag was added. Coordinator poison remains the sole
authority. A controlled I1 post-swap failure proves:

```text
coordinator poisoned
-> current read port rejects fresh read
-> environment rebuild context entry rejects
```

There is no normal state where the domain reports healthy while the coordinator
is poisoned, and no reset/retry/rollback/cancellation escape hatch.

## No authority use during rebuild

Around a port-driven rebuild the test snapshots the coordinator ledger and the
producer's process-lifetime token allocation state. It proves:

```text
ledger unchanged
facts tokens unchanged
LifecycleTransitionResult absent
transition generation unchanged
```

The retained producer establishes lifetime only; I2 does not invoke it.

## Explicitly absent I3 functionality

The environment port does not expose or implement:

```text
finalize_physical_transition
reserve_transition_context
build_facts
raw scan report
owner-qualified completion
physical_terminated mapping
coverage/reward writes
failure/release/health reporter
```

No placeholder method that only raises `NotImplementedError` was added.

## Explicitly absent I4 functionality

The domain and ports do not expose or implement:

```text
terminal slot/store
read_terminal
ack_terminal or acknowledge_terminal
designated destructive consumer
terminal observer port
synchronous terminal-ack-required error
pre-step physical permission guard
```

R2/R3 remain design-only. There is no partial terminal subsystem in I2.

## Dedicated tests

`test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py` contains
exactly twelve standalone groups:

1. I2-T1 canonical domain construction and pre-bootstrap state;
2. I2-T2 exact profile/domain rejection;
3. I2-T3 retained lifetime across repeated rebuild;
4. I2-T4 environment-port delegation against direct I1 oracle;
5. I2-T5 partial rebuild through the port;
6. I2-T6 immutable/no-alias current read;
7. I2-T7 capability-surface and export isolation;
8. I2-T8 no terminal capability;
9. I2-T9 no transition reporter/facts adapter;
10. I2-T10 coordinator poison propagation;
11. I2-T11 no authority/token/ledger use during rebuild;
12. I2-T12 default-off, no-wiring, and global side-effect boundary.

Results:

```text
normal: status=passed, num_tests=12, passed=12, failed=0
-I -B:  status=passed, num_tests=12, passed=12, failed=0
```

## Regression results

```text
B0-3I1 episode rebuild transaction          12/12 passed
B0-2 lifecycle authority transaction        18/18 passed
B0-1A execution facts producer               9/9 passed
B0-1B generation clock                      12/12 passed
lifecycle transition contract               12/12 passed
assignment profile contract                 16/16 passed
event-profile schema contract                9/9 passed
Phase-A default-off identity                 16/16 passed
profile production wiring                   10/10 passed
event-gated MRTA contract                   13/13 passed
```

The I1 regression preserves direct rebuild preparation, pre-signal abort,
post-signal poison, publication atomicity, and StateStore/clock/publication
order. B0-2 and B0-1 behavior remains exact.

## Interpreter and verification

```text
C:\isaacenvs\isaac45_harl\python.exe
```

The prescribed conda interpreter ran `py_compile` for the two new Python files,
the I2 suite in normal and `-I -B` modes, and every regression listed above.
No Isaac/AppLauncher process was started.

Final static checks cover:

```text
git diff --check
trailing whitespace
Markdown fences and classification/path checks
frozen hash audit
production wiring search
scope and module export audit
forbidden I3/I4 capability search
HEAD/branch/empty-index audit
```

## Hash audit

New I2 artifacts:

```text
BEADA445A453D5FF1E52FFBC615364E1BD299BB4DAD4DD6BC8F6B97757E0A4F6  assignment_event_profile_runtime_domain.py
BA3BD4C5F612F7714CE004631EDC7AAEA570A9CD8531E3745005FED2D8770E22  test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
```

Retained B0 foundations remained byte-identical:

```text
CA7774808FB8901DBC209F61A8915713106A5DC9DA739D1BCE30C8952A21E10E  assignment_lifecycle_authority_runtime.py
E4FBF20137637445AFA770ABC0E236F635C2A7BC372A515F5DA4EE5A659CF308  assignment_lifecycle_transaction_runtime.py
```

Frozen contracts remained byte-identical:

```text
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
```

Production integration boundaries remained byte-identical:

```text
2CBCE531BF8B4A1847C838BCCAA4EA17B82F1CAF53DD49C1B54FE17B488C7F74  scan_mobile_manipulator_env.py
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
```

## Default-off and production wiring

Repository searches prove the new module/domain symbol appears only in the
new private module, dedicated pure test, and documentation. It does not appear
in the environment, task `__init__`, wrapper, resolver, controller, HARL,
scenario/configuration, training, or playback entrypoints.

The event profile remains:

```text
runtime readiness: interface_only
training support:  phase_a_blocked
playback support:  blocked
```

`require_assignment_profile_runtime_ready()` was not modified and continues to
reject normal production execution.

The clean boundary proves no Python/Torch RNG, filesystem inventory, logger,
cwd, environment, or `sys.path` mutation and no Isaac/Omni/PXr/HARL import.

## Unresolved boundaries

B0-3I2 does not implement or authorize B0-3I3, B0-3I4, production composition,
real reset/autoreset, reporter/facts orchestration, terminal handoff/ack, or any
Phase B/C/D/E path.

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

B0-3I2 is complete and awaiting GPT/user review at the pure/default-off retained
domain and capability-port level only. Do not infer authorization for B0-3I3,
B0-3I4, or real environment integration.
