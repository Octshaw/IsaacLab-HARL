# Phase A4a V3 Interface Descriptor and Semantic Dispatch Report

## 1. Classification

```text
classification:
  PHASE-A4A-BLOCKED-AWAITING-GPT-REVIEW

stop reason:
  STOP — A3 SCHEMA-FREEZE GAP
```

Phase A4a did not pass its pre-implementation schema-freeze gate. No V3
manifest, dispatcher, or A4a test module was created. This is the prescribed
fail-closed outcome, not a partial implementation.

## 2. Authorization and scope

The authorization covered only:

- pure `assignment_checkpoint_contract_v3`;
- pure `assignment_checkpoint_semantic_dispatch`;
- exact V2 byte/hash/classification preservation;
- interface-descriptor-only V3 build/parse/canonicalize/fingerprint;
- an always-fail-closed Phase-A checkpoint-ready builder.

A4b, A5–A6, and Phase B0/B/C/D/E remain unauthorized and were not entered.
Checkpoint file/tensor I/O, runtime behavior changes, Isaac/AppLauncher,
training, playback, evaluation, installed-HARL changes, and commits remained
prohibited.

## 3. Starting repository state

```text
starting/current HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

interpreter used for the V2 pure baseline:
  C:\isaacenvs\isaac45_harl\python.exe

starting index:
  empty

known starting worktree:
  33-path inherited Phase A/A1/A2/A3 cohort
```

The preflight inventory matched the documented cohort. No unknown worktree
change was found.

## 4. Files changed

Created:

- `AgentRead/20260729/PHASE_A4A_V3_INTERFACE_DESCRIPTOR_AND_SEMANTIC_DISPATCH_REPORT.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

Not created because of the mandatory stop:

- `assignment_checkpoint_contract_v3.py`;
- `assignment_checkpoint_semantic_dispatch.py`;
- `scripts/environments/test_assignment_checkpoint_semantic_dispatch.py`.

No production Python file, A1–A3 descriptor/test, V2 checkpoint contract,
save/load/audit/playback file, runtime file, scenario file, or installed HARL
file was changed by A4a.

## 5. Pre-edit V2 golden capture

The existing pure-core fixture was executed directly before any A4a edit:

```text
test:
  scripts/environments/test_assignment_checkpoint_contract_core.py --json

result:
  28/28 passed

legacy v2:
  canonical byte length: 5509
  canonical SHA-256:
    1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f
  NORMAL_EVALUATION:
    allowed=true
    classification=normal_evaluation
  STRUCTURAL_INSPECTION:
    allowed=true
    classification=structurally_compatible

lifecycle_contract_c v2:
  canonical byte length: 7234
  canonical SHA-256:
    88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398
  NORMAL_EVALUATION:
    allowed=true
    classification=normal_evaluation
  STRUCTURAL_INSPECTION:
    allowed=true
    classification=structurally_compatible
```

The captured source hashes were:

```text
assignment_checkpoint_contract.py:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

test_assignment_checkpoint_contract_core.py:
  b644211865f884cf6e3150595c819d6a51bd8c0499e28b6ce4dc4e794696b1a4
```

These are the primary A4a V2 goldens and their fixture provenance is explicit.
No V2 expected value was updated.

For provenance completeness, a second read-only capture used the existing
production builder with the save-integration `_runtime_state` fixture, without
performing checkpoint file or tensor I/O:

| Fixture provenance | Legacy bytes / SHA-256 | Contract-C bytes / SHA-256 |
|---|---|---|
| Pure core `_manifest` | `5509` / `1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f` | `7234` / `88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398` |
| Production builder + save-integration runtime state | `8417` / `61f442db8deb75b2f4c8813b231f2724d623fa2054ad20d0fb7d6a2303ef63b4` | `10136` / `95fbb012c43ea49e89ae9e7d57fd61d6b06ffc513ecbb86c8cc00a4046ac3cdb` |

The mappings have different fixture provenance and serialized detail, so their
hashes are intentionally not interchangeable.

Because A4a stopped before its test module was created, §7's complete golden
package was not materialized as literal expected canonical bytes plus every
ordered mismatch record. The direct byte lengths, hashes, core
classifications, and read-only compatibility inventory were captured, but a
future re-authorized A4a must recapture the full bytes directly from unchanged
V2 and pin them in the new test; it must not reconstruct them from this report
or from a future dispatcher.

## 6. Canonical module identities

The existing V2 canonical module remains:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_contract
```

The two approved A4a canonical module names were read from the authority:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_contract_v3
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_semantic_dispatch
```

They were not created because their exact schemas could not be authoritatively
constructed.

## 7. V3 artifact kinds and Phase-A boundary

The two approved exact kinds remain:

```text
interface_semantic_descriptor
checkpoint_ready_manifest
```

The intended Phase-A boundary is unambiguous:

- only an `interface_semantic_descriptor` could be built, parsed,
  canonicalized, fingerprinted, and evaluated for `INTERFACE_AUDIT`;
- it could not authorize checkpoint weight use;
- a `checkpoint_ready_manifest` builder would always raise a typed
  Phase-A-not-authorized error.

No artifact of either kind was constructed. In particular, there is no V3
checkpoint-ready manifest and no V3 weight authorization.

## 8. Exact top-level and section schemas

The approved top-level order has 21 keys: two discriminators followed by 19
typed sections.

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

This top-level list alone is not enough to implement the manifest. The required
dedicated `actor_schema` and `shared_schema` section key inventories cannot be
frozen from current approved sources. Therefore:

```text
section classes instantiated:
  none

serialized section key orders produced:
  none

free-form fallback used:
  no
```

The A4a text also uses the phrase “exact 20-section schema.” The explicit list
and suggested class inventory consistently resolve to 21 top-level keys,
including `manifest_format_version`, and 19 section dataclasses; equivalently,
there are 20 entries after the version key when `manifest_kind` is counted.
No twentieth semantic section was invented.

## 9. A1–A3 descriptor bindings

### 9.1 Bindings that are present

A1 freezes the event-profile identity:

```text
profile:
  event_gated_local_mrta
profile_contract_version:
  assignment_resolved_profile_v1
checkpoint_family:
  assignment_checkpoint_contract_v3
runtime_route:
  event_gated_phase_a_interface_only_v1
runtime_readiness:
  interface_only
event_target_semantics_contract:
  event_gated_target_semantics_v1
training_semantics:
  event_gated_happo_ep_feed_forward_v1
```

A1 also freezes these observation-related identity strings:

```text
actor_schema_version:
  event_gated_global_actor_observation_v1
shared_schema_version:
  event_gated_global_centralized_observation_v1
shared_construction_mode:
  global_fixed_width_centralized_v1
```

The required A2/A3 public descriptor getters exist:

```text
get_assignment_lifecycle_transition_schema_descriptor
get_assignment_event_contract_descriptor
get_assignment_mrta_contract_descriptor
get_assignment_team_reward_contract_descriptor
get_assignment_event_gated_diagnostics_descriptor
```

They freeze transition, event, MRTA, reward, and diagnostics semantics. They do
not freeze the missing event-profile observation layouts described below.

### 9.2 Blocking observation-schema gap

None of the approved sources provides all of the following for
`event_gated_global_actor_observation_v1`:

- exact ordered actor feature/field names;
- exact block shapes and dtypes;
- exact actor dimension or dimension formula;
- exact flatten/concatenation order.

None provides all of the following for
`event_gated_global_centralized_observation_v1`:

- exact ordered centralized feature blocks;
- exact block shapes and dtypes;
- exact shared-observation dimension or dimension formula;
- exact construction/flatten order.

Authoritative V2.1 freezes only the strategy
`global fixed-dimensional observation + local action mask`, fixed global
robot/task identity, and the prohibition on local repacking/renumbering. It
does not define the serialized feature layout.

The current V2 Contract-C schemas cannot fill the gap. They are
profile-specific identities (`lifecycle_v1_actor_3n` and
`lifecycle_v1_shared_option_a_budget2m`) on an existing runtime route. The
event profile deliberately has different schema-version strings, a different
shared-construction identity, a distinct checkpoint family, and an
interface-only route. Reusing Contract-C dimensions or fields would be a
semantic guess and could incorrectly certify equal-shape compatibility.

This directly triggers:

```text
A4a §6.3:
  STOP — A3 SCHEMA-FREEZE GAP

A4a §11:
  STOP when exact field/order/value cannot be obtained

A4a §35 item 8:
  required A1–A3 descriptor semantics missing
```

### 9.3 Additional descriptor-binding gaps

The pre-implementation inventory found further items that need an explicit
authority decision before a complete key/type freeze:

- `local_candidate_contract`: the MRTA descriptor exposes request/result/Top-K
  schemas, one owner-expansion round, and fail-closed overflow, but not the
  complete seed, overlap-merge, and post-merge recomputation equations;
- `cost_path_contract`: it exposes the cost DTO, `navigation + alignment`, and
  invalid-path encoding, but not the expected-time/current-owner-remaining-cost
  rules in its public descriptor;
- `component_contract`: it exposes component DTOs and validation boundaries,
  but not the exact pair/component objective gates and transfer-count formula
  in its public descriptor;
- `failure_termination_contract`: A2 exposes a termination field and the
  `TerminationReason` enum exists, but the public descriptor does not freeze
  all task/robot lifecycle state enum orders and cumulative failure equations;
- event-specific `model_structure` and the full nested `training_contract`
  inventory do not have a dedicated public event descriptor. Current V2
  model/config identity and A1 training identity are available, but the exact
  event-profile projection and serialized key order still require approval.

Some of these semantics are described in Authoritative V2.1, but A4a §14 also
requires every V3 section to be traceable to and drift-checked against the
public A1–A3 descriptor set. A4a did not choose between copying documentary
text into V3 and first extending the public descriptors.

## 10. Unresolved parameter and readiness handling

A second independent freeze gap exists in the unresolved-parameter inventory.

Authoritative V2.1 lists:

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

A3 provides the typed shape
`UnresolvedParameterSpec(name, owner_phase, semantic_purpose)`. The team-reward
contract authoritatively freezes the exact triple for
`rejection_penalty_scale`. The MRTA descriptor otherwise exposes only the
generic three-field schema; its DTO slots do not freeze authoritative
name/owner/purpose triples. Its tests intentionally use synthetic
`<name>_semantic` purposes and cannot supply an authoritative fixture.
`alignment_time_constant` and `assignment_retry_cadence` are not represented
as A3 MRTA descriptor/DTO parameter slots.

The design table's human-readable phase owners such as `A/B`, `B/E`, and
`A/B/E` cannot be silently converted into canonical strings such as
`phase_a_b` or `phase_b_e`. A4a §17 requires exact canonical triples and
forbids synthetic values. Selecting those triples in A4a would therefore also
be speculative.

The intended readiness values are nevertheless clear:

```text
descriptor_schema_valid:
  only after the missing schemas are frozen
runtime_executable:
  false
checkpoint_weights_loadable:
  false
checkpoint_weights_savable:
  false
```

## 11. Canonical bytes and fingerprint

No V3 object was built, so no V3 canonical bytes or SHA-256 were generated.
Generating a hash from invented section layouts would turn an unresolved
schema question into a false compatibility authority.

```text
v3 fingerprint:
  not produced
reason:
  required semantic schema incomplete
```

## 12. Generic V2/V3 dispatcher

The dispatcher was not implemented. Consequently:

```text
v2 direct vs dispatched bytes:
  not evaluated
v2 direct vs dispatched SHA-256:
  not evaluated
v2 direct vs dispatched classification:
  not evaluated
unknown/missing version dispatch:
  not evaluated
```

The direct V2 baseline remains green and unchanged. Creating a dispatcher
without a constructible strict V3 type would be a speculative partial patch,
which the stop rule explicitly forbids.

## 13. V2 preservation matrix

| Check | Result |
|---|---|
| V2 production contract edited | No |
| V2 core pre-edit test | 28/28 passed |
| Legacy canonical hash captured | Yes |
| Contract-C canonical hash captured | Yes |
| Existing direct classifications captured | Yes |
| V2 expected values changed | No |
| Direct/dispatch equality | Not applicable; dispatcher not created |

The read-only direct-API compatibility inventory was:

| Direct V2 case | Allowed | Classification | Ordered mismatch summary |
|---|---:|---|---|
| Legacy exact native | Yes | `normal_evaluation` | None |
| Contract-C exact native | Yes | `normal_evaluation` | None |
| Contract-C exact structural | Yes | `structurally_compatible` | None |
| Contract-C → named lifecycle ablation | Yes | `explicit_ablation_evaluation` | None |
| Same ablation under normal purpose | No | `evaluation_semantic_mismatch` | profile, training profile, budget, mask, resolver order |
| Same ablation under continuation | No | `continuation_contract_mismatch` | same semantic order |
| Legacy → Contract-C structural check | No | `structural_mismatch` | actor dimension, per-agent actor dimension, shared dimension |
| Actor hidden-size change | No | `structural_mismatch` | `model_structure.actor_hidden_sizes` |
| Named ablation with no name | No | `unknown_or_missing_ablation` | None |
| Training initialization/fine-tuning | No | `unsupported_deferred` | None |
| Exact training resume | No | `unsupported_exact_resume` | None |

Current continuation classifications, in evaluator check order, are:

```text
continuation_contract_mismatch
missing_training_state_manifest
training_state_binding_mismatch
actor_inventory_identity_mismatch
missing_critic_inventory
missing_value_normalizer_inventory
acknowledgement_required
validated_weight_continuation
```

Metadata/fingerprint classifications are
`missing_native_metadata`, `missing_fingerprint`, `invalid_fingerprint`, and
`fingerprint_mismatch`. Tensor-inventory classifications are
`tensor_inventory_match`, `tensor_inventory_mismatch`, and
`invalid_tensor_inventory`.

The “diagnostics blocked” case is not a V2 evaluator classification. Its
authority is the A1 registry identity (`checkpoint_family=none`,
`training_support=existing_blocked`, `playback_support=diagnostics`).
Metadata-free legacy policy is also outside the future manifest dispatcher and
must not be used as version fallback.

## 14. V3 interface-only compatibility matrix

| Case | Result |
|---|---|
| Interface descriptor build | Blocked before implementation |
| `INTERFACE_AUDIT` | Not evaluated |
| Weight-use purpose | Not evaluated; remains unauthorized by design |
| Checkpoint-ready build | Not implemented; remains unauthorized |
| V2/V3 equal-shape mismatch | Not evaluated |
| Runtime readiness | Interface-only target; not certified by a manifest |

No row is being reported as passing V3 compatibility.

## 15. Key/type inventory

The approved 21-key top-level order is recorded in §8. A complete section
class/key inventory was deliberately not manufactured.

The minimum authority needed to unblock A4a is:

1. an approved public actor-schema descriptor with exact version, ordered
   fields/blocks, shapes/dtypes, dimension formula, and flatten order;
2. an approved public shared-schema descriptor with the same exact information
   plus its centralized construction rule;
3. an approved ordered unresolved-parameter inventory containing the exact
   canonical `name`, `owner_phase`, and `semantic_purpose` triple for every V3
   parameter, including `alignment_time_constant` and
   `assignment_retry_cadence`;
4. an explicit decision on which A1–A3 public descriptor owns each new frozen
   item;
5. a decision whether the partial local-candidate, cost/path, component,
   failure/termination, model, and training bindings listed in §9.3 must first
   be added to a public A3.x descriptor or may be frozen directly from the
   named documentary/current-config authorities;
6. confirmation that the explicit 21-key top-level list means 19 semantic
   section dataclasses and that no additional semantic section is intended.

This should be supplied by a separately authorized narrow schema-freeze
revision. A4a must not backfill A3 itself.

## 16. Tests and command results

Executed before the stop and repeated after the documentation-only update:

```text
D:\miniconda3\Scripts\conda.exe run
  -p C:\isaacenvs\isaac45_harl
  python scripts/environments/test_assignment_checkpoint_contract_core.py
    --json

result:
  pre-edit: 28/28 passed
  final direct rerun: 28/28 passed

final V2 contract file SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

git diff --check:
  exit 0

git diff --cached --name-status:
  empty

ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6
```

Read-only/static checks also inspected the A1 resolved event subtype, the A2/A3
descriptor getters, Authoritative V2.1, the approved Phase-A plan, V2
save/load/audit routing, and the current worktree inventory.

Not run because A4a stopped before code creation:

- A4a dispatcher/V3 tests;
- direct-versus-dispatch tests;
- V3 compatibility matrix tests;
- V2/V3 equal-shape tests;
- full A1–A3 regression reruns.

The last completed A3 handoff remains the current regression evidence for the
unchanged A1–A3 code: 72/72 combined pure/static checks.

## 17. Side-effect audit

```text
checkpoint files/tensors read:
  no
checkpoint files/tensors written:
  no
checkpoint weights loaded:
  no
checkpoint weights saved:
  no
actor/critic constructed:
  no
Isaac/AppLauncher run:
  no
training run:
  no
playback run:
  no
evaluation/diagnosis run:
  no
runtime behavior changed:
  no
installed HARL changed:
  no
commit:
  none
```

No `TASK_PROGRESS` archive was created. The current handoff was updated in
place, as requested by the A4a instruction, and was not mechanically
condensed.

## 18. Deferred A4b work

A4b was not entered. Save/load/playback/audit integration, checkpoint-ready
manifest use, weight compatibility, and any runtime evidence remain deferred
and unauthorized.

## 19. Risks and blockers

The primary risk is false semantic equivalence: copying the current Contract-C
observation dimensions into the event profile could yield apparently
shape-compatible artifacts while violating the distinct event semantic
family.

The secondary risk is fingerprint drift: choosing ad hoc owner/purpose strings
for unresolved parameters would make the V3 hash depend on an unreviewed
inventory and later force an avoidable contract change.

The blocker is resolvable through a narrow authoritative schema-freeze review;
it is not evidence of an architectural conflict.

## 20. Final classification

```text
classification:
  PHASE-A4A-BLOCKED-AWAITING-GPT-REVIEW

blocking condition:
  STOP — A3 SCHEMA-FREEZE GAP

required next action:
  approve a narrow actor/shared observation schema and unresolved-parameter
  identity freeze, then re-authorize A4a from its pre-implementation gate

v3 fingerprint:
  not produced

checkpoint-ready manifest:
  not constructible in Phase A

checkpoint weights:
  not read
  not written
  not load-authorized

runtime event profile:
  still not executable
```

A4a:
  stopped for GPT/user review

A4b:
  not entered

A5–A6:
  not entered

Phase B0/B/C/D/E:
  not entered
