# Phase A4a V3 Interface Descriptor and Semantic Dispatch Implementation Report

## 1. Classification

```text
classification:
  PHASE-A4A-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A4a:
  complete by pure manifest evidence
  stopped for GPT/user review

A4b:
  not entered
  not authorized

A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```

This classification is interface-only. It does not claim that the event-gated
profile is runtime-executable, trainable, playable, evaluable, checkpoint-ready,
or compatible with checkpoint weights.

## 2. Authorization and scope

The implemented slice is exactly A4a-R:

- a pure `assignment_checkpoint_contract_v3`;
- a pure `assignment_checkpoint_semantic_dispatch`;
- exact preservation and dispatch delegation of checkpoint contract V2;
- in-memory V3 interface build, parse, canonicalize, SHA-256, and interface audit;
- an always-fail-closed Phase-A checkpoint-ready builder;
- one pure A4a-R test suite;
- this report and the concise `TASK_PROGRESS.md` handoff.

The slice did not authorize or perform checkpoint weight I/O, checkpoint
save/load integration, runtime behavior changes, model construction, HARL
trainer/runner work, Isaac/AppLauncher startup, training, playback, evaluation,
diagnosis, configuration changes, installed-package changes, A4b, or commit.

## 3. Starting repository state

The required preflight established:

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

recent commits:
  dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f deterministic baseline / cyclic pose-slot profile work

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

starting index:
  empty

starting worktree:
  38 status entries in the documented A1--A4a/A3x cohort
  no unknown path

starting git diff --check:
  exit 0
  inherited LF/CRLF notices only
```

No reset, clean, checkout, or overwrite of inherited work was used.

Before either new A4a module existed, the unchanged V2 core suite passed
`28/28`, and its source/goldens matched the required hashes.

## 4. Files changed

New production modules:

- `assignment_checkpoint_contract_v3.py`;
- `assignment_checkpoint_semantic_dispatch.py`.

New pure test:

- `scripts/environments/test_assignment_checkpoint_semantic_dispatch.py`.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No V2 checkpoint source, A1--A3x descriptor authority, environment, wrapper,
state, resolver, runner, trainer, buffer, reward runtime, scenario/YAML,
checkpoint save/load/audit, entrypoint, or installed HARL file was modified by
A4a-R.

## 5. Pre-edit V2 golden package

The frozen source provenance is:

```text
assignment_checkpoint_contract.py SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

test_assignment_checkpoint_contract_core.py SHA-256:
  b644211865f884cf6e3150595c819d6a51bd8c0499e28b6ce4dc4e794696b1a4

V2 core before A4a edits:
  28/28 passed
```

The new A4a test embeds compressed literal copies of the complete canonical
UTF-8 byte strings captured from the direct V2 API. Decompression produces the
frozen canonical mapping fixtures; no V2 expected value is derived from the new
dispatcher.

| Direct V2 fixture | Canonical bytes | SHA-256 |
|---|---:|---|
| legacy native | 5,509 | `1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f` |
| lifecycle Contract C native | 7,234 | `88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398` |

The fixed compatibility package covers full decision mappings, including
reason, acknowledgement, next action, and every ordered mismatch record's
path, category, expected value, actual value, and message.

| Frozen V2 case | Allowed | Classification | Ordered mismatch paths |
|---|---:|---|---|
| legacy native evaluation | yes | `normal_evaluation` | none |
| Contract C native evaluation | yes | `normal_evaluation` | none |
| Contract C structural inspection | yes | `structurally_compatible` | none |
| Contract C to named lifecycle ablation | yes | `explicit_ablation_evaluation` | none |
| same ablation under normal evaluation | no | `evaluation_semantic_mismatch` | profile name; training-time profile; budget release; mask; resolver |
| same ablation under continuation | no | `continuation_contract_mismatch` | same five paths in the same order |
| legacy to Contract C structural inspection | no | `structural_mismatch` | actor dimension; per-agent actor dimensions; shared dimension |
| actor hidden-size drift | no | `structural_mismatch` | `model_structure.actor_hidden_sizes` |
| named ablation without the exact name | no | `unknown_or_missing_ablation` | none |
| training initialization/fine-tuning | no | `unsupported_deferred` | none |
| exact training resume | no | `unsupported_exact_resume` | none |

Fingerprint/metadata classes are fixed as
`missing_fingerprint`, `invalid_fingerprint`, `fingerprint_mismatch`, and
`missing_native_metadata`. Continuation inventory order is fixed as:

```text
missing_training_state_manifest
training_state_binding_mismatch
actor_inventory_identity_mismatch
missing_critic_inventory
missing_value_normalizer_inventory
acknowledgement_required
validated_weight_continuation
```

For the legacy and Contract-C mapping fixtures, direct V2 and dispatched V2
parsed mappings, canonical bytes, and SHA-256 are exact-equal. Across the full
compatibility matrix, complete direct/dispatched decision mappings,
classifications, and mismatch order are exact-equal. Metadata absence remains
outside the dispatcher.

## 6. Canonical module identities

```text
isaaclab_tasks.direct.scan_mobile_manipulator.
  assignment_checkpoint_contract_v3

isaaclab_tasks.direct.scan_mobile_manipulator.
  assignment_checkpoint_semantic_dispatch
```

Both sources place the canonical `__name__` guard before enum, dataclass,
exception, and dependency imports. Bare/wrong-key imports fail before declaring
identity-bearing types. No bare fallback, `sys.modules` alias, or package
`__init__.py` change exists. V2 public classes remain owned by the unchanged V2
module.

## 7. V3 manifest kinds and Phase-A boundary

Exact version:

```text
assignment_checkpoint_contract_v3
```

Exact kind order:

```text
interface_semantic_descriptor
checkpoint_ready_manifest
```

Only `interface_semantic_descriptor` can be built, parsed, canonicalized,
fingerprinted, and evaluated in Phase A. `INTERFACE_AUDIT` is the sole typed
operation purpose; it is not an invented twenty-second serialized key.

The mapping parser requires the version and kind discriminators to be exact
primitive strings. Typed manifests, including subclasses, are serialized and
fully reparsed against the 21-key schema and canonical authority before hashing
or evaluation; an overridden `to_mapping()` cannot bypass kind, schema, or
readiness validation.

Any declared or requested `checkpoint_ready_manifest` raises
`CheckpointReadyManifestNotAuthorizedError`. It never returns a partial ready
object and never authorizes weight use.

## 8. 21-key / 19-section typed schema

The exact top-level order is:

```text
manifest_format_version
manifest_kind
identity
scale
actor_schema
shared_schema
action_contract
transition_contract
event_tick_contract
local_candidate_contract
cost_path_contract
decision_valid_training_contract
sequential_factor_contract
component_contract
reward_contract
failure_termination_contract
diagnostics_contract
policy_sequence_contract
model_structure
training_contract
runtime_readiness_contract
```

There are two discriminators and exactly 19 semantic sections. Each section has
its own frozen/slotted dataclass with exact named fields:

```text
CheckpointV3IdentitySection
CheckpointV3ScaleSection
CheckpointV3ActorSchemaSection
CheckpointV3SharedSchemaSection
CheckpointV3ActionContractSection
CheckpointV3TransitionContractSection
CheckpointV3EventTickContractSection
CheckpointV3LocalCandidateContractSection
CheckpointV3CostPathContractSection
CheckpointV3DecisionValidTrainingContractSection
CheckpointV3SequentialFactorContractSection
CheckpointV3ComponentContractSection
CheckpointV3RewardContractSection
CheckpointV3FailureTerminationContractSection
CheckpointV3DiagnosticsContractSection
CheckpointV3PolicySequenceContractSection
CheckpointV3ModelStructureSection
CheckpointV3TrainingContractSection
CheckpointV3RuntimeReadinessSection
```

`AssignmentCheckpointContractManifestV3` is also frozen/slotted and has exact
fields equal to the 21-key inventory. No semantic section is a generic
`payload`, `data`, or free-form mapping bag.

## 9. Ownership-driven descriptor assembly

The builder requires caller-resolved scale and calls the A3x-1 public aggregate
getter. It independently compares the getter output with the public aggregate
builder, then validates every ownership record through the public A3x-1
validator and fixed canonical owner imports. Arbitrary module paths, dynamic
imports, bare imports, Markdown fallback, and Contract-C fallback are absent.

| # | V3 section | Owner/version | Descriptor path | Mode |
|---:|---|---|---|---|
| 1 | identity | profile `assignment_resolved_profile_v1` | `resolved_event_profile_mapping` | canonical reference |
| 2 | scale | event-profile v1 | `scale_contract` | inline |
| 3 | actor schema | event-profile v1 | `actor_schema` | inline |
| 4 | shared schema | event-profile v1 | `shared_schema` | inline |
| 5 | action contract | MRTA v2 | `action_contract` | canonical reference |
| 6 | transition contract | transition v2 | `$` | canonical reference |
| 7 | event-tick contract | event v2 | `$` | canonical reference |
| 8 | local-candidate contract | MRTA v2 | `local_candidate_semantics` | canonical reference |
| 9 | cost/path contract | MRTA v2 | `cost_path_semantics` | canonical reference |
| 10 | decision-valid training | event-profile v1 | `decision_valid_training_contract` | inline |
| 11 | sequential factor | event-profile v1 | `sequential_factor_contract` | inline |
| 12 | component contract | MRTA v2 | `component_semantics` | canonical reference |
| 13 | reward contract | reward v1 | `$` | canonical reference |
| 14 | failure/termination | transition v2 | `failure_termination_semantics` | canonical reference |
| 15 | diagnostics contract | diagnostics v1 | `$` | canonical reference |
| 16 | policy sequence | profile v1 | `resolved_event_profile_mapping.event_gated_target_semantics` | canonical reference |
| 17 | model structure | event-profile v1 | `model_structure` | inline |
| 18 | training contract | event-profile v1 | `training_contract` | inline |
| 19 | runtime readiness | event-profile v1 | `runtime_readiness_contract` | inline |

All 19 owner/module/version/path/mode records resolve. Tests validate every
canonical row, tamper every row's module/version/path/mode through the public
validator, exercise the production row-validation path, reject aggregate
getter-versus-public-builder drift, and reject changed manifest content for
every semantic section.

The identity section is the A4a-defined exact seven-key typed projection of the
resolved-profile mapping. Other sections preserve their exact public descriptor
projection. No semantic value is copied from Markdown.

## 10. Identity and scale

The exact V3 identity is:

```text
profile: event_gated_local_mrta
profile_contract_version: assignment_resolved_profile_v1
checkpoint_family: assignment_checkpoint_contract_v3
runtime_route: event_gated_phase_a_interface_only_v1
runtime_readiness: interface_only
event_target_semantics_contract: event_gated_target_semantics_v1
training_semantics: event_gated_happo_ep_feed_forward_v1
```

Legacy runtime booleans and legacy-wrapper projection are excluded.

Scale is the exact 11-key `event_gated_scale_contract_v1` projection. It keeps
`M`, `N`, ordered global IDs, scene/control timing, and horizon identity. It
does not copy action-owned fields or add an A4a-specific restriction to the
A3x-owned agent-name domain. Machine provenance is excluded by the exact key
schemas rather than by scanning legitimate semantic string values.

## 11. Actor/shared and terminal semantics

Actor and shared sections are consumed from A3x-1, not rebuilt in A4a:

```text
actor:
  18 keys
  15 blocks x 12 fields
  dimension = 6MN + 30M + 14N + 2
  M=3,N=50 -> 1692

shared:
  19 keys
  19 blocks x 10 fields
  semantic dimension = 6MN + 31M + 15N + 8
  M=3,N=50 -> 1751
  semantic / runner / critic = [E,S] / [E,M,S] / [B,S]
```

The terminal contract remains fingerprinted exactly:

- ordinary nonterminal no-tick: one forced storage action, DVM false, actor not
  called;
- terminal: zero legal actions, all masks false, forced ID `-1`, no storage,
  proposal, forced row, resolver, or component;
- terminal shared state: finalized pre-reset critic sidecar, not an extra
  physical transition, actor row, or critic-loss sample.

## 12. MRTA/event/transition/reward/diagnostics bindings

The action section preserves the exact ten-key
`event_gated_action_contract_v1` descriptor literals. Its formula bindings
remain `scale_contract.M`, `scale_contract.N + 1`, and `scale_contract.N`; V3
validates them against scale semantics without replacing them with a second
numeric authority. Noop decoded value remains `-1`.

The local candidate, cost/path, and component sections are exact MRTA v2
projections. V3 fingerprints but does not execute local-set creation, Top-K,
path estimation, pair gates, component closure, objective evaluation, or atomic
commit.

The event section fingerprints the seven lifecycle event types, one independent
scheduled retry opportunity type, three trigger-ineligible resolver diagnostic
types, and retry-cadence reference. Retry remains an opportunity, not a
lifecycle event.

The transition/failure projections include exact task, robot, and termination
orders; facts/result schema descriptors; cumulative pair failure;
`TEAM_INFEASIBLE`; release/termination/generation semantics; and the terminal
boundary. Private ledger layout, receipt capability, tensor pointers, and
mutation-detector mechanisms are excluded.

Reward remains `assignment_team_reward_contract_v1`. Diagnostics remain
`assignment_event_gated_diagnostics_contract_v1`. No reward or logger runtime
behavior changed.

## 13. Unresolved parameter inventory

The runtime-readiness section carries the complete six-key inventory mapping,
the seven-field reference record schema, and exactly these 11 ordered names:

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

Every record fingerprints name, owner module/version/path, expected concrete
type, unit, and legal domain. Each domain-owned triple is revalidated. There is
no twelfth parameter, bare `TBD`, chosen default, or synthetic value in the
interface descriptor.

## 14. Model/training semantic identity

The exact model projection binds:

```text
actor: HAPPO/StochasticPolicy
critic: VCritic/VNet
distribution: Categorical
actor hidden sizes: (256,256)
critic hidden sizes: (256,256)
state type: EP
share_param: false
recurrent flags: false / false
serialization: state_dict
save_entire_model: false
state-dict inventory: deferred
```

The unused YAML `hidden_sizes_critic=(512,256)` is not introduced.

Training identity is descriptor-only. It preserves fixed physical-step
rollout, standard GAE, all-valid-step critic returns/ValueNorm, DVM-valid actor
loss/entropy/advantage semantics, zero-valid skip, singleton raw finite
advantage fallback, rejected-proposal inclusion, and sequential-factor
nondecision identity through the exact A3x-1 projections. No policy, optimizer,
forward, backward, buffer, trainer, or model was created or run.

## 15. Runtime-readiness fail-closed behavior

The interface manifest is exact:

```text
manifest_kind: interface_semantic_descriptor
runtime_readiness: interface_only
runtime_execution_authorized: false
checkpoint_weight_use_authorized: false
unresolved_parameter_resolution_status: all_11_unresolved
```

Checkpoint-ready rejection matrix:

| Request | Result |
|---|---|
| no resolved parameter mapping | typed reject; `all_11_unresolved` |
| all 11 caller values supplied | typed reject; values are unverified and unauthorized |
| declared ready manifest parsed | typed Phase-A reject before downgrade |
| runtime evidence supplied | typed reject; caller evidence is not Phase-A verified |
| state-dict inventory supplied | typed reject; inventory remains deferred |
| training/continuation/evaluation/playback/weight-load purpose | `CheckpointManifestPurposeError` |

Errors include requested kind, interface-only readiness, parameter status,
missing runtime-evidence categories, and state-dict inventory status. No partial
ready manifest is returned.

## 16. Canonical bytes and V3 interface fingerprint

Canonicalization uses UTF-8, `ensure_ascii=true`, `allow_nan=false`, compact
separators, lexicographically sorted JSON object keys, preserved semantic
sequence order, no whitespace/BOM/trailing newline, JSON integers for ints,
JSON booleans for bools, and finite JSON numbers for floats. Parser input
mapping insertion order is not confused with dataclass schema inventory order.

The first frozen V3 fixture uses:

```text
M/N: 3 / 50
agents: robot_0, robot_1, robot_2
task IDs: 0..49
scene spacing: 12.0
sim dt / decimation / physical step: 0.01 / 4 / 0.04
episode time / horizon: 40.01 / 1001

canonical byte length:
  67794

interface semantic SHA-256:
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a
```

This is an **interface semantic fingerprint only**. It is not checkpoint-ready,
weight-load compatible, runtime verified, training compatible, or playback
compatible.

Reordered input mapping keys and pretty JSON produce the same bytes/hash.
Ordered agent identity changes the hash. NaN/Infinity, bool-as-int drift,
unknown/missing keys, noncanonical semantic content, and extra provenance
fields are rejected.

Canonicalization reparses typed objects through the strict mapping parser.
Runtime Enum discriminator objects and typed subclasses that forge a ready kind
or an extra provenance field therefore fail instead of bypassing authority.

## 17. Generic V2/V3 dispatcher

The dispatcher consumes an already available in-memory mapping only. It first
reads `manifest_format_version` and then delegates:

```text
assignment_checkpoint_contract_v2
  -> unchanged V2 from_mapping / canonical bytes / SHA-256 / evaluator

assignment_checkpoint_contract_v3
  -> strict V3 parser / canonical bytes / SHA-256 / INTERFACE_AUDIT
```

It does not open a file, scan a directory, read JSON from disk, call
`torch.load`, inspect state dicts, construct a policy, or implement a
metadata-free fallback. `None`, non-mappings, missing versions, and unknown
versions fail with typed errors.

When current/checkpoint versions differ, family mismatch is raised before V3
schema or shape inspection. Equal M/N, actor/shared/action dimensions, and
hidden sizes therefore cannot make V2 and V3 compatible.

## 18. V2 preservation matrix

| Preservation check | Result |
|---|---|
| V2 production source modified | no |
| V2 source SHA-256 | exact |
| V2 core | 28/28 passed |
| legacy mapping/bytes/hash direct vs dispatch | exact |
| Contract-C mapping/bytes/hash direct vs dispatch | exact |
| full compatibility decisions direct vs dispatch | exact |
| ordered mismatch records | exact |
| classification names/order | unchanged |
| metadata-free behavior moved into dispatcher | no |
| Contract-C semantics reused for V3 | no |

## 19. V3 interface compatibility matrix

| Case | Result |
|---|---|
| valid V3 interface build/parse | exact V3 typed manifest |
| exact V3 interface audit | schema/semantics true; runtime/weight false |
| different valid V3 semantics | semantic fingerprint mismatch |
| ready kind | typed Phase-A block |
| V3 used for a weight/runtime purpose | typed purpose block |
| V2 versus V3, even equal shape | typed family mismatch |
| missing/unknown version | typed unsupported-version |
| `None`, list, or string | typed input error |
| unknown manifest kind | typed unsupported-kind |
| runtime Enum used as a mapping kind | typed unsupported-kind |
| forged typed manifest subclass | fully reparsed and typed rejected |
| missing/extra root or nested field | typed schema error |

## 20. Tests and command results

The verification interpreter was the required environment, invoked directly or
through the equivalent reproducible `conda run` form:

```text
D:\miniconda3\Scripts\conda.exe run
  -p C:\isaacenvs\isaac45_harl
  python ...
```

The final changed Python files passed joint `py_compile`. The complete matrix
was rerun after strict typed-object reparsing and the final A3x authority-boundary
correction.

| Suite | Result |
|---|---:|
| new A4a-R semantic-dispatch suite | 12/12 |
| A3x-1 event-profile descriptor | 9/9 |
| MRTA descriptor/DTO | 13/13 |
| lifecycle transition | 12/12 |
| team reward | 6/6 |
| event-gated diagnostics | 8/8 |
| profile contract | 16/16 |
| profile production wiring | 10/10 |
| initial-condition boundary | 9/9 |
| V2 checkpoint core | 28/28 |

```text
new A4a-R:
  12/12 passed

A1--A3x regressions excluding V2:
  83/83 passed

V2 core:
  28/28 passed

combined pure evidence:
  123/123 passed
```

## 21. Side-effect audit

Clean-child and static/spied checks establish for the new pure boundary:

- Python and Torch RNG state unchanged;
- NumPy import absence preserved when applicable;
- cwd, environment, `sys.path`, logger state, profile registry, and directory
  contents unchanged;
- no stdout/stderr;
- no bare module alias;
- no Isaac/AppLauncher, HARL runtime/model, environment, trainer, or runner
  import;
- no built-in/`io`/`os`/`Path` file open, text/byte read/write, glob, directory
  iteration/walk, `torch.load/save`, `load_state_dict`, checkpoint-directory
  scan, or actor construction call;
- no root or named-logger mutation.

Repository-level boundary:

```text
checkpoint weight files/tensors read:
  no
checkpoint weights written:
  no
actor/critic/optimizer constructed:
  no
Isaac/AppLauncher:
  not run
training/playback/evaluation/diagnosis:
  not run
runtime behavior:
  unchanged
installed HARL:
  unchanged
commit:
  none
```

## 22. Deferred A4b work

A4b was not entered and is not authorized. The following remain separately
gated:

- save/load/playback/offline-audit integration;
- metadata pair and loader ordering;
- state-dict inventory construction;
- runtime-evidence IDs;
- successful/authorized checkpoint-ready manifest construction and integration;
- any weight save/load or continuation path.

## 23. Risks and blockers

No architectural or schema blocker remains inside A4a-R.

Material deferred risks are:

1. all 11 method parameters remain unresolved;
2. the first V3 fixture is scale-specific and must not be generalized to a
   runtime/checkpoint claim;
3. any reviewed owner descriptor change must produce a reviewed V3 semantic
   change/fingerprint rather than a fallback;
4. runtime observation, terminal-sidecar transport, DVM/factor training, and
   component resolver behavior remain unimplemented;
5. state-dict inventory and loader-before-I/O guards remain A4b work.

The highest immediate misuse risk is treating the interface fingerprint as a
loadable checkpoint contract. The kind/readiness/purpose errors explicitly
prevent that in the implemented pure facade.

## 24. Final classification

```text
classification:
  PHASE-A4A-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

V2 checkpoint:
  unchanged
  golden preserved

V3 interface descriptor/fingerprint:
  implemented

V3 checkpoint-ready:
  Phase-A fail-closed

semantic dispatcher:
  implemented without file/tensor I/O

runtime:
  unchanged and not verified for the event profile

ending HEAD / final index:
  dca976001d8c53a9cfb424b468fa58d9fca367f6 / empty

final worktree / git diff --check:
  42 known entries after four A4a-R additions / passed; inherited LF/CRLF notices only

TASK_PROGRESS archive:
  not created; targeted in-place handoff remains 299 lines and was not condensed

checkpoint weight I/O:
  none

commit:
  none
```

A4a:
  stopped for GPT/user review

A4b:
  not entered
  not authorized

A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered
