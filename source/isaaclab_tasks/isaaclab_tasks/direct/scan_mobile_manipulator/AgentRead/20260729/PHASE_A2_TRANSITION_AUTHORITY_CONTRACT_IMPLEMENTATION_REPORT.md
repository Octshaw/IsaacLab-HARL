# Phase A2 Transition Authority Contract Implementation Report

## 1. Classification

```text
classification:
  PHASE-A2-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

authorized slice:
  A2 only

A2:
  complete by pure/schema evidence

A3–A6:
  not entered

Phase B0/B/C/D/E:
  not entered

commit:
  not authorized
```

This report separates evidence into three classes:

- **pure/schema evidence**: behavior established by the canonical A2 module and
  pure tests that do not launch Isaac Lab;
- **runtime evidence**: none in this phase;
- **deferred runtime evidence**: environment capture, lifecycle-authority
  placement, state mutation, resolver integration, and all training paths.

The implementation has no identified A2 design blocker. The A2 pure suite
passes 11/11 groups, all three required A1 regression scripts pass, and the
final repository-state audit passes. This report must not be read as evidence
that Phase A as a whole is complete.

## 2. Authorization and scope

The authorized production behavior is limited to a pure process-local
contract:

```text
raw execution facts
→ exact producer identity
→ exact generation/token validation
→ logical batch-atomic consume-once receipt
→ lifecycle-authority-only result finalization
→ alias-isolated lifecycle transition result
```

Implemented A2 responsibilities:

- canonical producer and authority identities and stamps;
- exact facts, receipt, and result schemas;
- pair-attributed raw-signal validation;
- explicit per-environment generation expectations;
- consume-once token, ledger, and immutable receipt;
- result finalization bound to the issuing ledger and lifecycle authority;
- exact empty `lifecycle_events` boundary pending A3;
- supported-path tensor alias isolation and mutation detection;
- deterministic, deeply read-only public schema descriptor.

Explicitly outside this implementation:

- `DirectMARLEnv.step()` or pre-reset capture;
- any environment, wrapper, resolver, runner, buffer, trainer, actor, critic,
  observation, action-mask, reward, or checkpoint connection;
- lifecycle state-machine execution;
- runtime failed-pair accumulation;
- `TEAM_INFEASIBLE` derivation;
- termination-reason derivation from raw physical terminal conditions;
- assignment tick, local set, Top-K, DVM, or policy sampling;
- lifecycle-authority runtime component placement;
- A3 typed events/MRTA contracts;
- training, playback, formal evaluation, and checkpoint I/O.

No environment hook or runtime authority is implied merely because factory and
ledger types now exist.

## 3. Starting repository state

The read-only baseline audit recorded:

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

git log -3 --oneline:
  dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f initial-condition profiles and compatibility contracts (abridged)

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

index:
  empty

git diff --check:
  exit 0
  existing LF-to-CRLF warnings only
```

Before A2 edits, `git status --short --untracked-files=all` contained exactly
22 known Phase A/A1a–A1c paths: 10 tracked modifications and 12 untracked
files. A set comparison against the documented A1 cohort produced:

```text
unknown paths:
  0

missing expected A1 cohort paths:
  0
```

At that baseline, all three A2 target files were absent. No unknown code,
configuration, result, or checkpoint change was detected.

## 4. Files changed

A2-authorized change set:

- added
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_transition_contract.py`;
- added
  `scripts/environments/test_assignment_lifecycle_transition_contract.py`;
- added this report,
  `AgentRead/20260729/PHASE_A2_TRANSITION_AUTHORITY_CONTRACT_IMPLEMENTATION_REPORT.md`;
- updated top-level `AgentRead/TASK_PROGRESS.md` with a targeted in-place
  handoff edit performed separately from this report edit.

The production contract is new and is not imported by any existing runtime
path. The A2 implementation must not modify the A1 authority files:

- `assignment_profile_contract.py`;
- `scenario_config.py`;
- `assignment_harl_wrapper.py`;
- `assignment_lifecycle_training_contract.py`;
- `assignment_harl_training.py`.

It also must not modify the environment, state, resolver, diagnostics,
checkpoint, formal entrypoint, YAML/JSON, or installed HARL files listed in the
authorization. The final root-agent path-boundary result is recorded in
section 14.

No `TASK_PROGRESS` archive was created. The starting handoff was 299 lines and
8,844 bytes, within the repository's approximate 200–300 line guidance. The
top-level file receives a targeted in-place update rather than an
archive-plus-condense rewrite or mechanical history append.

## 5. Canonical module identity

The sole production module key is:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract
```

The source checks `__name__` immediately after string constants and before
importing Torch or declaring any enum, dataclass, or exception. Execution under
a bare or otherwise incorrect key raises `ImportError` before a second
identity-bearing type family can be created.

The production file does not:

- support `import assignment_lifecycle_transition_contract`;
- add a relative-to-bare fallback;
- create a bare `sys.modules` alias;
- modify package `__init__.py`.

The public enums, stamps, DTOs, ledger, factory, and exceptions therefore
derive their `__module__` identity from the one canonical package-qualified
key. The final A2 pure suite passed canonical `isinstance()` identity,
wrong-key fail-fast, public `__module__`, no-alias, and clean-child
source-key-uniqueness checks.

The exported exception hierarchy is:

```text
AssignmentTransitionContractError
├── TransitionSchemaError
├── TransitionGenerationError
├── DuplicateTransitionConsumeError
├── TransitionTokenMismatchError
├── ExecutionFactsProducerMismatchError
├── LifecycleAuthorityMismatchError
└── FinalizedSnapshotMutationError
```

Errors include a stable `failure_code`, schema version, and applicable
environment, expected/actual generation, token, producer, and authority
context rather than an unqualified `ValueError`.

## 6. `ExecutionTransitionFacts` schema

Exact versions and producer identity:

```text
schema_version:
  execution_transition_facts_v1

producer_contract_version:
  execution_facts_producer_contract_v1

producer_id:
  env_execution_facts_producer_v1
```

`ExecutionTransitionFacts` is a frozen, slotted, `init=False` type. Its direct
constructor fails; the public construction route is
`ExecutionTransitionFacts.from_mapping(...)` with an exact
`ExecutionFactsProducerStamp` and explicit `torch.device`.

Exact public field order:

| Field | Shape/type | Exact dtype |
|---|---:|---|
| `schema_version` | scalar | `str` |
| `producer_contract_version` | scalar | `str` |
| `producer_id` | scalar enum | `ExecutionFactsProducerId` |
| `env_id` | `[E]` | `torch.int64` |
| `episode_generation` | `[E]` | `torch.int64` |
| `transition_generation` | `[E]` | `torch.int64` |
| `physical_terminated` | `[E]` | `torch.bool` |
| `physical_truncated` | `[E]` | `torch.bool` |
| `time_limit_reached` | `[E]` | `torch.bool` |
| `bad_transition` | `[E]` | `torch.bool` |
| `completion_signals` | `[E,M,N]` | `torch.bool` |
| `terminal_pair_failure_signals` | `[E,M,N]` | `torch.bool` |
| `forced_release_signals` | `[E,M,N]` | `torch.bool` |
| `robot_unavailable_signals` | `[E,M]` | `torch.bool` |
| `robot_recovered_signals` | `[E,M]` | `torch.bool` |
| `coverage_before_reset` | `[E,N]` | `torch.bool` |
| `task_state_before_transition` | `[E,N]` | `torch.int64` |
| `robot_state_before_transition` | `[E,M]` | `torch.int64` |
| `ownership_before_transition` | `[E,N]` | `torch.int64` |
| `consume_once_token` | `[E]` | `torch.int64` |

Construction validates the complete mapping before returning a facts object:

- exact key set; missing and unknown keys fail;
- all derived fields prohibited by the authorization are rejected, including
  `TEAM_INFEASIBLE`, `termination_reason`, updated lifecycle state,
  completed/released task outputs, failed-pair outputs, lifecycle events, and
  authority receipt IDs;
- `E > 0`, `M > 0`, and `N > 0`;
- exact tensor shapes and a common explicit device;
- exact `torch.int64`/`torch.bool` dtypes;
- no implicit device move or dtype cast;
- `requires_grad=True` is rejected;
- `env_id` values are unique;
- episode generation, transition generation, and token are non-negative;
- ownership is in `-1..M-1`;
- `time_limit_reached` or `bad_transition` implies
  `physical_truncated == true`;
- all pair and availability invariants in section 10.

Accepted tensors are detached, cloned, made contiguous, and placed behind
private storage. Source-tensor mutation after construction therefore cannot
change the facts snapshot. Every public tensor property and `to_mapping()`
returns a fresh clone after integrity validation.

## 7. `LifecycleTransitionResult` schema

Exact versions and identities:

```text
schema_version:
  lifecycle_transition_result_v1

authority_contract_version:
  unique_lifecycle_authority_v1

facts_producer_id:
  env_execution_facts_producer_v1

authority_id:
  lifecycle_authority_v1
```

Exact public field order:

| Field | Shape/type | Exact dtype |
|---|---:|---|
| `schema_version` | scalar | `str` |
| `authority_contract_version` | scalar | `str` |
| `facts_producer_id` | scalar enum | `ExecutionFactsProducerId` |
| `authority_id` | scalar enum | `LifecycleAuthorityId` |
| `env_id` | `[E]` | `torch.int64` |
| `episode_generation` | `[E]` | `torch.int64` |
| `transition_generation` | `[E]` | `torch.int64` |
| `completed_tasks` | `[E,N]` | `torch.bool` |
| `released_tasks` | `[E,N]` | `torch.bool` |
| `new_failed_pairs` | `[E,M,N]` | `torch.bool` |
| `updated_failed_pairs` | `[E,M,N]` | `torch.bool` |
| `new_team_infeasible_tasks` | `[E,N]` | `torch.bool` |
| `updated_task_state` | `[E,N]` | `torch.int64` |
| `updated_robot_state` | `[E,M]` | `torch.int64` |
| `updated_ownership` | `[E,N]` | `torch.int64` |
| `termination_reason` | `[E]` | `torch.int64` |
| `lifecycle_events` | immutable tuple | exact `()` in A2 |
| `facts_consume_token` | `[E]` | `torch.int64` |
| `authority_receipt_id` | `[E]` | `torch.int64` |

The frozen termination encoding is exactly:

```text
NONE = 0
ALL_TASKS_COMPLETED = 1
NO_FEASIBLE_TASKS_REMAIN = 2
TIME_LIMIT = 3
```

There is no `OTHER`, `UNKNOWN`, or `ENV_TERMINATED`.

The factory validates:

- result environment IDs and generations are copied exactly from facts;
- `facts_consume_token` is copied exactly from facts;
- `authority_receipt_id` is copied from the matching ledger receipt;
- all result tensors match facts `E/M/N`, device, and exact dtype;
- `completed_tasks == completion_signals.any(dim=1)`;
- each completed task has `updated_ownership == -1`;
- each completed task has the caller-supplied
  `task_completed_state_encoding`;
- `new_failed_pairs` has no overlap with the caller-supplied prior snapshot;
- `updated_failed_pairs == prior_failed_pairs | new_failed_pairs`;
- `updated_ownership` remains in `-1..M-1`;
- termination values are members of the exact enum domain;
- `lifecycle_events` is the exact empty tuple.

`new_team_infeasible_tasks` is validated only for shape, device, and dtype.
The contract deliberately does not claim to derive all-robots-failed or
`TEAM_INFEASIBLE`; that remains B0 runtime work.

## 8. Facts producer and lifecycle authority separation

The identities are deliberately disjoint:

```text
ExecutionFactsProducerId:
  ENV_EXECUTION_FACTS_PRODUCER_V1

ExecutionFactsProducerStamp version:
  execution_facts_producer_contract_v1

LifecycleAuthorityId:
  LIFECYCLE_AUTHORITY_V1

LifecycleAuthorityStamp version:
  unique_lifecycle_authority_v1
```

Both stamps are frozen/slotted and require their exact canonical enum class,
member, and version. They cannot be substituted for one another by structural
similarity.

Authority separation is enforced as follows:

1. raw facts require the producer stamp and carry producer identity only;
2. the ledger requires a lifecycle-authority stamp;
3. a receipt binds the facts producer, issuing ledger, lifecycle authority,
   environment rows, generations, tokens, and receipt IDs;
4. the result factory must be bound to the same ledger and authority;
5. a result receives a private finalization seal tied to the factory, ledger,
   and receipt issuance;
6. direct public construction of a receipt or valid result fails.

The environment is therefore defined only as a future raw-facts producer. A2
does not select the future Python class that owns either producer or authority,
and it does not deploy authority into the environment, wrapper, or resolver.

## 9. Generation, token, ledger, and receipt

### Public token and expectation

`TransitionConsumeToken` is a frozen/slotted, hashable scalar record:

```text
producer_id
env_id
episode_generation
transition_generation
consume_once_token
```

No tensor is used as a dictionary/set key. `TransitionGenerationExpectation`
provides exact per-environment expected episode and transition generation. The
ledger requires an immutable tuple containing exactly one expectation for each
facts `env_id`.

### Ledger bindings

The minimum consume-once key is:

```text
(
  producer_id,
  env_id,
  episode_generation,
  transition_generation,
  consume_once_token,
)
```

The ledger additionally keeps:

- generation-to-token binding keyed by
  `(producer_id, env_id, episode_generation, transition_generation)`;
- last consumed `(episode_generation, transition_generation)` per `env_id`;
- a deterministic monotonic receipt counter per `env_id`;
- registered receipt issuance capabilities;
- successfully finalized receipt capabilities.

This allows duplicate, same-generation/different-token, stale, future,
wrong-environment, wrong-episode, and wrong-producer cases to remain distinct.

### Logical batch atomicity

`consume()` performs:

```text
validate canonical facts type and integrity
→ re-run full facts semantics
→ validate producer stamp/binding
→ validate exact expected-generation tuple and env set
→ validate every row and construct every scalar token
→ calculate all receipt IDs
→ construct and validate one immutable receipt batch
→ prepare copy-on-write next ledger state
→ perform one ledger-state swap
```

Any exception before the final state swap leaves consumed keys, generation
bindings, last-consumed state, counters, and issued-receipt registrations
unchanged. A corrected batch may therefore be retried after an invalid atomic
attempt.

This is **logical batch atomicity for the public API**. It is not a
multi-thread transaction, distributed transaction, or cryptographic claim.

### Receipt IDs

`authority_receipt_id` is:

- deterministic and owned by the ledger/authority;
- monotonic per environment;
- produced without RNG;
- semantically separate from the producer token;
- forced not to equal the corresponding raw token value.

The receipt schema version is
`transition_consume_receipt_v1`. Receipt tensor fields are exact `[E]`
`torch.int64` values for environment ID, episode generation, transition
generation, facts token, and authority receipt ID.

### Required generation matrix

| Case | Contract result | Pure-test evidence |
|---|---|---|
| correct first consume | receipt batch | PASS |
| exact duplicate | `DuplicateTransitionConsumeError`, `duplicate` | PASS |
| same generation, different token | `TransitionTokenMismatchError`, `generation_token` | PASS |
| stale transition | `TransitionGenerationError`, `stale` | PASS |
| future transition | `TransitionGenerationError`, `future` | PASS |
| wrong environment set | `TransitionGenerationError`, `env_id` | PASS |
| wrong episode generation | `TransitionGenerationError`, `episode` | PASS |
| wrong producer | `ExecutionFactsProducerMismatchError` | PASS |
| one invalid row in batch | whole batch rejected; no state change | PASS |
| two valid rows | one atomic receipt batch | PASS |
| corrected retry after failure | allowed | PASS |
| per-env receipt monotonicity/no RNG | deterministic distinct IDs | PASS |

## 10. Pair-attributed signal assertions

For every environment, robot, and task:

```text
owner_match[e,i,j] :=
  ownership_before_transition[e,j] == i
```

The implemented assertion matrix is:

| Condition | Result/failure code |
|---|---|
| at most one completion robot per environment/task | pass |
| two robots complete one task | `TransitionSchemaError(completion_cardinality)` |
| completion and terminal failure on one pair | `TransitionSchemaError(pair_signal_conflict)` |
| completion from non-owner or unowned task | `TransitionSchemaError(completion_owner)` |
| forced release from non-owner or unowned task | `TransitionSchemaError(release_owner)` |
| terminal pair failure from non-owner or unowned task | `TransitionSchemaError(failure_owner)` |
| unavailable and recovered on one robot/transition | `TransitionSchemaError(availability_edge_conflict)` |
| valid owner-attributed completion | task-level completion derived by factory |

These invariants are validated during facts construction and again before
ledger consume/factory finalization. A bad row invalidates the complete facts
batch; no partial facts object, receipt, ledger update, or result is produced.

A future external/system non-owner release requires a new typed cause/record.
The A2 boolean invariant is intentionally not relaxed.

The A2 pure suite confirms that all invalid pair batches leave the ledger
unchanged and that valid task-level completion is derived from the
pair-attributed source facts.

## 11. Result factory and finalization authority

`LifecycleTransitionResultFactory` requires:

- the exact canonical `TransitionConsumeLedger`;
- the exact canonical `LifecycleAuthorityStamp`;
- equality between the factory authority and ledger authority.

`finalize()` requires facts, an issued and not-yet-finalized receipt, all
caller-derived tensors, a prior failed-pair snapshot, completed-state encoding,
and the exact empty A2 lifecycle-event tuple.

Authority/binding matrix:

| Case | Enforced result | Pure-test evidence |
|---|---|---|
| matching facts/receipt/ledger/authority | finalized result | PASS |
| no receipt | receipt-type/authority failure | PASS |
| receipt from another ledger | `receipt_issuer` failure | PASS |
| wrong authority stamp/factory authority | authority failure | PASS |
| receipt authority differs | `receipt_authority` failure | PASS |
| receipt producer differs from facts | producer failure | PASS |
| receipt/facts environment mismatch | generation `env_id` failure | PASS |
| receipt/facts episode mismatch | generation `episode` failure | PASS |
| receipt/facts transition mismatch | generation `transition` failure | PASS |
| receipt/facts token mismatch | `TransitionTokenMismatchError` | PASS |
| duplicate successful finalization | `duplicate_finalization` | PASS |
| direct result constructor | `factory_required` failure | PASS |
| direct receipt constructor | `ledger_receipt_required` failure | PASS |
| completed derivation/ownership/state mismatch | schema failure | PASS |
| result shape/device/dtype mismatch | schema failure | PASS |
| non-empty lifecycle events | `lifecycle_events_a2_empty` | PASS |
| finalized result validation | pass | PASS |

All derived validation and result construction occur before the receipt is
claimed as finalized. A failed finalization can be corrected and retried with
the same valid receipt. After successful finalization, the ledger atomically
records the issuance capability as finalized and rejects reuse.

The private finalization seal is process-local defense in depth. The report
does not claim cryptographic unforgeability or protection against arbitrary
Python reflection/private-state manipulation.

## 12. Observable alias-isolation and mutation detection

The exact public claim is:

```text
frozen metadata
+ no public writable tensor alias
+ supported-path mutation detection
```

Implemented behavior:

- facts, stamps, token, expectation, receipt metadata, and result metadata use
  frozen/slotted types where applicable;
- exact dtype/device/shape and no-grad checks precede capture;
- construction detaches, clones, and makes tensor storage contiguous;
- inference-mode input is cloned outside inference mode so the protected copy
  retains supported version tracking;
- source tensors are not retained;
- every public tensor accessor returns a fresh detached contiguous clone;
- `to_mapping()` returns a read-only mapping whose tensor values are clones;
- normal in-place mutation of protected backing is detected before supported
  accessor, mapping, consume, or finalize paths;
- metadata, tensor-index, receipt, and result-seal validation detects
  supported-path corruption;
- frozen field rebinding fails.

The current detector uses private replaceable integrity metadata, including
normal tensor mutation-version observation. That mechanism is an
implementation regression detail, not public schema or compatibility identity.

Required behavior tests:

| Case | Expected | Evidence |
|---|---|---|
| mutate construction source | internal snapshot unchanged | PASS |
| mutate facts accessor clone | facts unchanged | PASS |
| mutate result accessor clone | result unchanged | PASS |
| rebind frozen field | rejected | PASS |
| normal internal in-place facts corruption | detected before consume/access | PASS |
| normal internal in-place result corruption | detected before access/mapping | PASS |
| detector-private key search in public mapping/descriptor | absent | PASS |

Not claimed:

- defense against adversarial reflection;
- defense against `.data` or raw-storage manipulation;
- defense against arbitrary private-attribute replacement;
- absolute tensor immutability;
- cryptographic tamper evidence.

## 13. Public schema descriptor

`get_assignment_lifecycle_transition_schema_descriptor()` returns a
deterministic deeply read-only mapping with:

- contract version
  `assignment_lifecycle_transition_contract_v1`;
- facts schema version, producer version/identity, exact field order, symbolic
  shapes, and dtypes;
- result schema version, authority version/identity, source producer identity,
  exact field order, symbolic shapes, and dtypes;
- pair attribution version
  `pair_attributed_execution_signals_v1`;
- observable immutability version
  `assignment_tensor_alias_isolation_v1`;
- the three supported public immutability guarantees.

The descriptor deliberately excludes:

- tensor `_version`;
- storage pointer/identity;
- detector/digest implementation;
- private field names/layout;
- producer or authority runtime class placement;
- checkpoint family, manifest, or fingerprint.

A2 defines no v3 checkpoint module and computes no checkpoint fingerprint.
The A2 pure suite passed deep-read-only behavior, deterministic equality, exact
field order, and exclusion of all detector-private keys.

## 14. Tests and command results

Only pure/static commands are permitted. No AppLauncher, Isaac environment,
wrapper smoke, resolver, checkpoint integration, actor update, training,
playback, or formal evaluation command belongs in this section.

### Baseline command results

| Command | Result |
|---|---|
| `git rev-parse HEAD` | exit 0; expected HEAD |
| `git log -3 --oneline` | exit 0 |
| `git status --short --untracked-files=all` | exit 0; known A1 cohort only |
| `git diff --name-status` | exit 0 |
| `git diff --check` | exit 0; line-ending warnings only |
| `git diff --cached --name-status` | exit 0; empty |
| conda interpreter check | exit 0; `C:\isaacenvs\isaac45_harl\python.exe` |

### A2 and regression commands

| Command | Required result | Recorded result |
|---|---|---|
| `python -m py_compile <A2 contract> <A2 test>` | exit 0 | exit 0 |
| `python scripts/environments/test_assignment_lifecycle_transition_contract.py --json` | all A2 cases pass | exit 0; 11/11 |
| `python scripts/environments/test_assignment_profile_contract.py --json` | A1a/A1b pass | exit 0; 16/16: A1a 11, A1b 5 |
| `python scripts/environments/test_assignment_profile_production_wiring.py --json` | A1c pass | exit 0; 10/10 |
| `python scripts/environments/test_assignment_initial_condition_contract.py --json` | historical regression passes | exit 0; 9/9 |
| A2 implementation-file `git diff --check` | exit 0 | exit 0 |
| final repository `git diff --check` | exit 0 | exit 0; inherited LF-to-CRLF warnings only |
| final index check | empty | empty |
| final HEAD/path-boundary check | unchanged/authorized only | HEAD unchanged at `dca976001d8c53a9cfb424b468fa58d9fca367f6`; exact baseline cohort plus three new A2 files and the authorized `TASK_PROGRESS.md` update |

The first A2 suite run was 10/11 because the test's own static authority-string
scan falsely classified the public immutability version. The pure test was
corrected; no production-contract change was needed for that failure. The final
run passed 11/11.

The 11 final A2 groups cover:

- canonical module identity and strict class identity;
- versions, stamps, exceptions, and public descriptor;
- `E=1,M=1,N=1` and `E=2,M=3,N=5`;
- valid non-contiguous and inference-mode input cloning;
- 17 facts shape failures, 17 facts dtype failures, all 12 forbidden derived
  fields, generic unknown fields, device/dimension/generation/ownership/
  truncation failures;
- nine pair-attribution rejection cases and valid task-level completion;
- duplicate/token/stale/future/environment/episode/producer/expectation/history
  ledger failures;
- batch atomicity, receipt identity, monotonic receipt IDs, and RNG stability;
- no/cross-ledger receipt, environment/episode/transition/token mismatch,
  invalid-finalization retry, and successful-receipt reuse rejection;
- ten result shape and ten result dtype failures plus
  derivation/ownership/state/failed-pair/events/termination assertions;
- construction/accessor alias isolation and supported internal-mutation
  detection;
- descriptor privacy and deep read-only behavior;
- clean-child RNG/cwd/environment/path/logger/files/stdout/stderr/import
  side-effect checks.

Four targeted contract review points also passed:

- inference-mode clone behavior;
- private factory sentinel/finalization seal;
- semantic mutation diagnostics;
- absence of an unintended device whitelist.

## 15. Side-effect audit

Static production-code evidence:

- no Python, NumPy, or Torch RNG call;
- no file read/write;
- no current-directory or environment-variable mutation;
- no `sys.path` or logger mutation;
- no environment/wrapper/resolver/checkpoint/profile-runtime import;
- no AppLauncher, Isaac, HARL, training, playback, or evaluation call;
- no A1 registry mutation;
- import-time behavior is limited to identity validation, definitions, and
  deterministic schema-descriptor construction after canonical import.

The module necessarily imports Torch to define and validate tensor contracts.
That does not constitute Isaac/AppLauncher or runtime integration.

The final clean-child group confirms that import/construction/consume/finalize
preserve Python and Torch RNG, cwd, environment, `sys.path`, logger state, file
set, and stdout/stderr. It also confirms that NumPy remains unimported and that
Isaac/AppLauncher/HARL/checkpoint/profile-runtime modules are not imported.

No prohibited runtime command was run while drafting or validating A2.

## 16. Deferred B0 runtime placement and hook

The following evidence is explicitly deferred to B0:

- where the environment captures pre-reset facts;
- how raw facts are preserved across reset;
- which runtime component owns the sole lifecycle authority;
- generation expectation and token production ownership;
- lifecycle state-machine mutation;
- cumulative failed-pair runtime updates;
- all-robots-failed and `TEAM_INFEASIBLE` derivation;
- termination-reason derivation and physical-terminal fail-closed handling;
- resolver-pre baseline publication;
- environment-step, wrapper, and resolver call ordering.

No A2 source is imported by the environment, wrapper, resolver, runner, or
entrypoint. Consequently:

```text
pre-reset capture:
  not implemented

runtime lifecycle authority:
  not placed

failed-pair runtime:
  not active

TEAM_INFEASIBLE runtime:
  not active
```

If raw physical termination cannot map to one of the four frozen reasons, B0
must fail closed and request a method decision rather than inventing an
`OTHER`/`UNKNOWN` code.

## 17. Deferred A3 typed event/MRTA contracts

A2 intentionally uses:

```text
lifecycle_events:
  exact empty tuple only
```

It does not define a temporary event enum, universal event dictionary, mutable
payload, or checkpoint-visible provisional schema.

Deferred to A3:

- formal `LifecycleEventRecord` types;
- event/opportunity/resolver-diagnostic namespace separation;
- cost/path validity contracts;
- local set, one-round owner expansion, Top-K, and current-task retention;
- global action IDs and action-mask contracts;
- decision/forced/terminal masks and DVM;
- proposal/effective assignment separation;
- transfer component and rejection DTOs;
- reward and diagnostics semantic schemas;
- unresolved numeric parameter interfaces.

A3 is not authorized by A2 completion and must begin only after an explicit
review gate.

## 18. Risks and blockers

### Current blockers

None. The A2 pure suite, all required A1 regressions, and final
HEAD/index/path/diff checks pass.

### Residual risks

1. **No runtime evidence.** Pure contract success does not establish correct
   pre-reset capture, authority placement, lifecycle update order, or resolver
   integration.
2. **Expected-generation ownership is deferred.** B0 must define the runtime
   source of exact expectations without weakening stale/future detection.
3. **Logical, not concurrent, atomicity.** The copy-on-write state swap is a
   single-thread API guarantee; no lock or multi-thread transaction is claimed.
4. **Process-local finalization defense.** Factory/ledger/issuance capabilities
   prevent supported public bypass, but are not cryptographic or
   reflection-proof.
5. **Detector portability.** Current supported-path detection observes normal
   tensor mutation behavior. Its mechanism must remain private and replaceable,
   and A4 must not fingerprint it.
6. **Strict owner attribution.** System/non-owner release cannot reuse the
   current booleans; a future typed cause is required.
7. **`TEAM_INFEASIBLE` remains caller supplied.** A2 validates its result tensor
   but does not prove the all-robots-failed derivation.
8. **Termination completeness remains a method boundary.** Unmappable physical
   terminal states must fail closed in B0.
9. **In-memory ledger only.** Receipt counters and capabilities are not
   checkpoint contracts and do not imply persistence/restart semantics.
10. **Canonical test harness required.** Tests must load the source under the
    package-qualified key without adding a production `__init__.py` alias.

Any need to edit environment, wrapper, resolver, runner, state, checkpoint,
entrypoint, YAML/JSON, or installed HARL code is an A2 boundary violation, not
an invitation to expand this implementation.

## 19. Final classification

```text
classification:
  PHASE-A2-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A1:
  complete
  review passed

A2:
  complete by pure/schema evidence
  stopped for GPT/user review

runtime evidence:
  none

A3–A6:
  not entered

Phase B0/B/C/D/E:
  not entered

commit:
  none
```

No A3 or runtime implementation may start automatically after that
classification.
