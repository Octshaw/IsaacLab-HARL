# TASK_PROGRESS

## Current status

```text
classification:
  PHASE-B0-2-PURE-LIFECYCLE-AUTHORITY-TRANSACTION-COMPLETE-AWAITING-GPT-REVIEW

Phase A:
  final review passed; previously committed by user

B0-1A:
  REVIEW PASS; pure facts producer complete; 9/9

B0-1B:
  REVIEW PASS; retained generation clock complete; 12/12

B0-2D / B0-2D-R:
  semantic conditions closed

B0-2:
  pure/default-off transaction foundation complete
  awaiting GPT/user review

C1 / C2:
  implemented and tested

frozen authority changes / production wiring:
  none; final scope/hash audit passed

event-profile readiness:
  interface_only / Phase-A blocked

B0-3+ and Phase B/C/D/E:
  not entered; not authorized

Isaac/AppLauncher/training/playback/evaluation:
  not run

commit:
  none
```

## Latest completed phase

B0-2 implements this dormant pure chain:

```text
canonical ExecutionTransitionFacts
  -> writer-capability transaction-private lifecycle snapshot
  -> full-batch receipt-independent authority derivation/validation
  -> deterministic events and final termination reason
  -> TransitionConsumeLedger.consume() once
  -> frozen LifecycleTransitionResultFactory.finalize() once normally
  -> atomic StateStore replacement, version +1
  -> explicit generation-clock commit
  -> matching immutable state/generation/result publication
```

The implementation is deliberately isolated in
`assignment_lifecycle_transaction_runtime.py`. This preserves B0-1A/B0-1B
static guards proving that `assignment_lifecycle_authority_runtime.py`
contains no later StateStore, authority, ledger/result, event, or coordinator
capability.

### C1 — failed active owner rejection

```text
task0[j] in {CLAIMED, NAVIGATING, ALIGNING}
AND owner0[j] == i
=> failed0[i,j] MUST be false
```

A violation rejects the complete batch before candidate derivation or ledger
consume, even when another robot remains feasible. It causes no release,
event, repair, state swap, generation commit, publication, or poison.

### C2 — external old/old or new/new publication

The coordinator holds one publication/transaction lock across private state
capture, revalidation, ledger/result, StateStore swap, clock commit, and
publication. Every supported fresh external current-state read uses
`coordinator.read_published_view()` and receives only old-state/old-generation
or new-state/new-generation.

After coordinator writer claim, `store.snapshot()` fails closed. `transact()`
accepts canonical facts plus exact clock contexts, never a caller snapshot.
The retained raw clock is confined to trusted bootstrap/producer and
transaction-private orchestration; integration must not distribute it or its
raw snapshot capability to external current readers. The coordinator public
surface exposes neither raw store nor clock.

An unexpected post-receipt failure poisons the coordinator and publishes
nothing. Fresh reads/transactions fail; there is no rollback, cancellation,
second consume, automatic retry, or continuation. If clock commit fails after
the swap, the swapped internal state and outstanding uncommitted candidate
remain while the old immutable publication remains historical.

## Active architecture / implementation path

```text
trusted pure bootstrap
  -> exact event profile + explicit StateStore + retained clock
  -> one coordinator claims the unique StateStore lifecycle writer

EnvironmentExecutionFactsProducer (B0-1A)
  -> canonical immutable facts only

LifecycleGenerationClock (B0-1B)
  -> episode generation and exact outstanding transition contexts

LifecycleAuthorityRuntime (B0-2)
  -> sole lifecycle semantic authority
  -> C/F/R/U/Rc, TEAM, robot projection, reason, events

LifecycleStateStore (B0-2)
  -> sole lifecycle state writer; immutable versioned replacement

LifecycleAuthorityTransactionCoordinator (B0-2)
  -> ordering, capability confinement, poison, publication lock

PublishedLifecycleView (B0-2)
  -> immutable external current state + committed generation + result

environment integration / B0-3+
  -> absent and unauthorized
```

## Key files

Runtime foundations:

- `assignment_lifecycle_authority_runtime.py`
- `assignment_lifecycle_transaction_runtime.py`

Dedicated pure suites:

- `scripts/environments/test_assignment_phase_b0_1a_execution_facts_producer_pure.py`
- `scripts/environments/test_assignment_phase_b0_1b_generation_clock_pure.py`
- `scripts/environments/test_assignment_phase_b0_2_lifecycle_authority_transaction_pure.py`

Frozen and unchanged:

- `assignment_lifecycle_transition_contract.py`
- `assignment_event_contract.py`
- `assignment_profile_contract.py`
- `assignment_event_profile_schema_contract.py`

No environment, wrapper, resolver, controller, HARL, config, checkpoint, or
installed-package file changed in B0-2.

## Repository and artifact identity

```text
starting/ending HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

branch / index / commit:
  main / empty / none

transaction runtime SHA256:
  478DD5045E8FA243CD2F9EAF1C9E88AEA824CB5C39C659A18F0BB6E4B9AFC936

B0-2 runner SHA256:
  F689138E57BE200AE069211549BCD9ECFE0616C7F0DDD3353BE6CCF847C7E46A
```

The new pre-rewrite archive is:

`AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_2_IMPLEMENTATION_20260814.md`

It is byte-identical to the prior 300-line top-level handoff; both had SHA256
`EC58E4774E64B64D7A47EB07EE58AF0D9B1B4FE02A76C6F19127900BF64297EA`.
Closeout verification confirmed that exact byte identity. Documentation
landing changed no Python file.

## Latest verification

```text
py_compile all five current untracked Python files:
  passed

B0-2 normal / isolated -I -B:
  18/18 / 18/18 passed

B0-1A / B0-1B:
  9/9 / 12/12 passed

lifecycle-transition / event-gated MRTA:
  12/12 / 13/13 passed

profile / event-profile schema:
  16/16 / 9/9 passed

default-off identity / production wiring:
  16/16 / 10/10 passed

diff, whitespace, scope, frozen hashes, runtime RNG, numeric TBD audit:
  passed; no production refs, RNG use, or numeric selections
```

T1-T18 cover state invariants/versioning, all 32 simultaneous-cause rows, C1,
completion attribution, TEAM, robot projection, phase preservation, ordered
events, termination, exact success counts, batch rejection, token/generation
independence, receipt versus fail-stop, C2 concurrency, post-swap poison,
capability isolation, and default-off/profile side effects. T14-T16 use
`threading.Event`, no sleep race, and `finally` release/join paths.

## Known issues / unfinished work

- Environment pre-reset invocation and real physical reporters are absent.
- Autoreset and `_get_dones()`/`_reset_idx()`/`_get_rewards()` integration are
  absent.
- Mailbox/terminal sidecar and wrapper/HARL transport are absent.
- Phase-B assignment commit, resolver, retry, Top-K/local sets, component
  solving, cost, masks, and DVM are absent.
- `CLAIMED -> NAVIGATING -> ALIGNING` progression is not implemented because
  frozen facts provide no authoritative progress edge.
- Event runtime readiness remains fail-closed.
- Isaac runtime identity, training, playback, evaluation, checkpoint-ready V3,
  and weight use remain deferred; no performance claim is made.

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

## Do not do

Without explicit authorization:

- do not begin B0-3+, environment integration, or Phase B/C/D/E;
- do not wire environment/package/wrapper/resolver/controller/HARL paths;
- do not distribute raw StateStore/clock current-read capabilities externally;
- do not add rollback, cancellation, auto-retry, or a second authority;
- do not change frozen contracts/readiness or select numeric TBDs;
- do not run Isaac, AppLauncher, training, playback, evaluation, real
  checkpoint tensor I/O, or commit.

## Next step

Send the uncommitted B0-2 foundation and report to GPT/user review. First
confirm documented hashes and `18/18` still hold. Await explicit next-phase
authorization; do not infer B0-3+ or environment-integration permission.

## Detailed reports / archives

- `AgentRead/20260814/PHASE_B0_2_PURE_LIFECYCLE_AUTHORITY_TRANSACTION_IMPLEMENTATION_REPORT.md`
- `AgentRead/20260814/PHASE_B0_2DR_TARGETED_LIFECYCLE_AUTHORITY_SEMANTIC_REVISION.md`
- `AgentRead/20260814/PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md`
- `AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_2_IMPLEMENTATION_20260814.md`
- `AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_2DR_TARGETED_SEMANTIC_REVISION_20260814.md`
- `AgentRead/20260809/PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md`
- `AgentRead/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md`
- `AgentRead/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md`

Detailed history remains in dated reports/archives. This is the concise
current handoff.
