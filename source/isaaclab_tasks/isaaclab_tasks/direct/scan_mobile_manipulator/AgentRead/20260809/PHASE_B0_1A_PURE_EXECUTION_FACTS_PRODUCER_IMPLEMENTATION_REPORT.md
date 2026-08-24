# Phase B0-1A Pure Execution Facts Producer Implementation Report

## 1. Classification

```text
classification:
  PHASE-B0-1A-PURE-EXECUTION-FACTS-PRODUCER-COMPLETE-AWAITING-GPT-REVIEW

B0-1A:
  complete

ExecutionTransitionFacts runtime producer foundation:
  implemented at pure/default-off level

environment pre-reset integration:
  not implemented

lifecycle authority:
  not implemented

state mutation:
  none

ledger/result:
  not implemented

mailbox/sidecar:
  not implemented

event runtime readiness:
  still blocked

B0-1B:
  not authorized

B0-2+:
  not authorized

Phase B/C/D/E:
  not entered

training/playback/evaluation:
  not run

commit:
  none
```

No frozen-contract change or runtime incompatibility was required. B0-1A
stops at the explicit raw-input-to-canonical-facts boundary.

## 2. Repository baseline and ending state

```text
starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch:
  main

HEAD subject:
  feat(assignment): complete lifecycle-aware MRTA Phase A interface contracts

index at B0-1A preflight:
  empty

worktree at B0-1A preflight:
  contained the preserved, uncommitted B0 design documentation delta

commit made by B0-1A:
  none
```

The pre-existing B0 design report and its `TASK_PROGRESS.md` update were
preserved. They were not treated as B0-1A production changes.

## 3. Changed and new files

New production foundation:

- `assignment_lifecycle_authority_runtime.py`

New pure test:

- `scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py`

New report:

- `AgentRead/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md`

Updated in place:

- `AgentRead/TASK_PROGRESS.md`

Preserved pre-existing untracked design artifact:

- `AgentRead/20260809/PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md`

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
checkpoint, logger, or installed-package file changed.

## 4. Exact implementation boundary

The implemented dataflow is only:

```text
explicit ExecutionTransitionInput
        |
        v
EnvironmentExecutionFactsProducer.build_facts()
        |
        v
ExecutionTransitionFacts.from_mapping()
        |
        v
canonical immutable ExecutionTransitionFacts
```

The module has no production caller. It is not imported by the task package,
environment, wrapper, resolver, or resolver runtime. Normal entrypoints remain
unchanged and the event profile remains unreachable at the Phase-A readiness
barrier.

## 5. Producer API and profile gate

The public B0-1A capability is:

```python
EnvironmentExecutionFactsProducer(
    profile: ResolvedEventGatedAssignmentProfile,
)

producer.build_facts(
    transition_input: ExecutionTransitionInput,
) -> ExecutionTransitionFacts
```

The constructor uses exact canonical type identity:

```text
type(profile) is ResolvedEventGatedAssignmentProfile
```

It rejects the four `ResolvedExistingAssignmentProfile` variants as well as
raw strings, mappings, `None`, and lookalikes through
`AssignmentProfileRouteError`. It retains the exact already-resolved object.
It does not call profile normalization, profile resolution, scenario parsing,
checkpoint parsing, or a raw-boolean mapping.

The module uses its canonical package key and imports the two Phase-A
authorities by relative canonical import. No alternate identity-bearing
producer family is declared.

## 6. Private explicit transition input

`ExecutionTransitionInput` is a private runtime-boundary container, not a new
frozen public semantic contract. It carries:

```text
device
env_id
episode_generation
transition_generation
physical_terminated
physical_truncated
time_limit_reached
bad_transition
completion_signals
terminal_pair_failure_signals
forced_release_signals
robot_unavailable_signals
robot_recovered_signals
coverage_before_transition
task_state_before_transition
robot_state_before_transition
ownership_before_transition
```

It contains no resolver output, wrapper reconstruction, result field,
receipt, event, derived failed-pair state, or termination reason.

The final facts object is created only through the frozen
`ExecutionTransitionFacts.from_mapping()` factory using the exact
`ExecutionFactsProducerStamp`. The factory remains responsible for exact
field inventory, shape, dtype, device, clone/detach/contiguous behavior,
immutability, pair ownership/cardinality, truncation relations, and all other
frozen facts assertions.

## 7. Producer identity

The implementation consumes unchanged Phase-A identities:

```text
schema_version:
  execution_transition_facts_v1

producer_contract_version:
  execution_facts_producer_contract_v1

producer_id:
  ENV_EXECUTION_FACTS_PRODUCER_V1
  serialized value: env_execution_facts_producer_v1
```

It does not add or accept an alternate stamp, string producer ID, field,
field order, shape, dtype, or device-conversion path.

## 8. Coverage direction

The private input carries raw physical `coverage_before_transition [E,N]` and
explicit pair-attributed `completion_signals [E,M,N]`. The producer computes:

```text
coverage_before_reset =
  coverage_before_transition
  OR completion_signals.any(dim=1)
```

This is a prospective raw physical pre-reset snapshot. It is formed before
factory construction and has no dependency on any lifecycle result. The
pair-shaped completion tensor is separately passed unchanged to the factory;
only the coverage projection is task-level.

The implementation does not read or modify `viewpoints_covered`, scan dwell,
controller action, reward credit, wrapper effective assignment, or any reset
buffer.

## 9. Generation semantics

`episode_generation [E]` and `transition_generation [E]` are caller-supplied.
B0-1A passes them unchanged to the frozen factory. It does not reserve,
increment, commit, reset, infer, or reconcile either generation.

There is no episode clock, transition clock, reset handshake, assignment-tick
clock, or facts/result consume generation in this slice. Those remain later
work.

## 10. Token semantics

The module owns one private process-lifetime allocator:

```text
key:
  env_id

first candidate:
  0

increment:
  once for every allocated facts row

reset API:
  none

RNG:
  none
```

The allocator is module-lifetime rather than producer-instance-local. A second
producer object using the same environment ID continues the same token
sequence and cannot restart at zero. Allocation is protected by one lock and
is batch-atomic with respect to token reservation.

Tokens are allocated before prospective-coverage and final frozen-factory
validation. If later construction fails, the allocated values remain burned.
They are never rolled back or reused. Exhaustion beyond signed int64 fails
instead of wrapping.

This is only token allocation. The module does not import, construct, or call
a consume ledger; issue a receipt; assign a receipt ID; classify consume
status; or finalize a result.

## 11. Pure test coverage

The new standalone suite contains nine groups:

| Group | Result | Evidence |
|---|---:|---|
| T1 exact event-profile gate | pass | event exact subtype accepted; four existing profiles plus three raw/fallback forms rejected; resolver calls zero |
| T2 exact full-batch facts | pass | nonzero `E=2,M=3,N=5`; exact 20 fields, shapes, dtypes, device, contents, producer ID |
| T3 alias isolation | pass | all 17 tensor fields unchanged after input/accessor/mapping mutation |
| T4 pair attribution | pass | two exact completion, failure, and release `(env,robot,task)` coordinates retained |
| T5 external generations | pass | episode `[101,4]` and transition `[1001,77]` preserved exactly |
| T6 token/RNG | pass | per-env strict monotonicity, row-order independence, producer-reconstruction survival, Python/Torch RNG unchanged |
| T7 failed construction | pass | invalid post-allocation construction mutated no input/file/logger; token gap proved burn/no reuse |
| T8 no derived result | pass | forbidden authority/result/event/state capabilities absent; only public method is `build_facts` |
| T9 existing-profile side effects | pass | RNG, files, logger, cwd, environment, `sys.path`, registry identity unchanged; event readiness still blocked |

The suite uses canonical namespace-only module loading and deterministic tensor
literals. It does not execute the normal task-package initializer.

## 12. Verification commands and exact results

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
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_authority_runtime.py scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py
```

Result: passed.

New B0-1A pure suite:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py --json
```

Result:

```text
status=passed
passed=9
failed=0
num_tests=9
```

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

Final documentation/scope checks include `git diff --check`, trailing
whitespace inspection, frozen-file status, and production-entrypoint reference
inspection. All passed: there are no whitespace errors, no frozen/prohibited
file diffs, and no environment/wrapper/resolver/package entrypoint reference to
the new producer.

## 13. Explicit non-implementation inventory

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

derived completion/release/failure/TEAM_INFEASIBLE/termination/events:
  not implemented

mailbox / read-ack handoff:
  not implemented

terminal critic sidecar:
  not implemented

environment pre-reset hook:
  not implemented

wrapper/resolver/controller integration:
  none

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

## 14. Default-off and next gate

The event profile remains exactly:

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

`require_assignment_profile_runtime_ready()` is unchanged. No normal
production entrypoint imports or constructs the producer.

The next action is independent GPT/user review of B0-1A. This report does not
authorize B0-1B, a lifecycle authority, environment integration, B0-2+, or any
Phase B/C/D/E work.

```text
B0-1A:
  complete
  stopped for GPT/user review

B0-1B:
  not entered
  not authorized

B0-2+:
  not entered
  not authorized
```
