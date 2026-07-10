# Phase 9G-8F-1 Manifest / Canonical JSON / Fingerprint / Compatibility Core Report

Date: 2026-07-09

## Classification

```text
PASS
```

Phase 9G-8F-1 implements the accepted pure checkpoint-contract core. Canonical serialization, integrity fingerprints, purpose-aware compatibility, named ablation, training-state/file inventory, and exact tensor-inventory comparison are independently testable without HARL, Torch, Isaac Sim, or live models.

No runtime save or load path imports this module.

## Scope And Files

Created:

```text
assignment_checkpoint_contract.py
scripts/environments/test_assignment_checkpoint_contract_core.py
AgentRead/20260709/
  PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F1_CONTRACT_CORE_20260709.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

Inspected as contract sources:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
assignment_harl_wrapper.py
assignment_lifecycle_training_contract.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
agents/harl_happo_cfg.yaml
```

Explicitly not modified:

```text
assignment_harl_wrapper.py
assignment_lifecycle_training_contract.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
agents/harl_happo_cfg.yaml
all runner save/restore paths
all playback/evaluation loaders
installed HARL
the Conda environment
```

## Immutable Contract Types

The pure module defines:

```text
AssignmentCheckpointContractManifest
AssignmentTrainingStateManifest
ArtifactFileInventoryEntry
StateDictTensorInventoryEntry
CompatibilityRequest
CompatibilityMismatch
CompatibilityDecision
CompatibilityPurpose
```

Public contract dataclasses are frozen. Nested mappings are recursively converted to `FrozenDict`; lists become tuples. `FrozenDict` rejects item mutation and attribute rebinding. Conversion methods return fresh validated JSON-compatible mappings, so callers cannot mutate internal contract state through returned dictionaries.

The immutable manifest format is:

```text
assignment_checkpoint_contract_v1
```

Top-level ordered schema:

| section | contract contents |
|---|---|
| `identity` | profile, training-time profile, HAPPO, EP/FP, shared mode, `state_dict` |
| `scale` | `M`, `N`, agent count, semantic ordered agent identities |
| `actor_schema` | schema version, dimensions, ordered feature/task-row/tail definitions |
| `shared_schema` | schema version, dimension, construction mode, ordered blocks, budget schema |
| `action_contract` | `Discrete(N+1)`, target range, raw and decoded noop |
| `lifecycle_behavior_contract` | snapshot, resolver, mask, budget, guardrail, ownership, arbitration |
| `policy_sequence_contract` | sequence version/mode, recurrent flags, actor-buffer generator |
| `model_structure` | effective actor/critic/distribution classes and constructed network structure |
| `training_contract` | effective optimizer, PPO, loss, discount, ValueNorm, time-limit, rollout fields |

Unknown fields are rejected. A generic metadata bag is not present. Absolute paths, drive-qualified paths, backslash paths, timestamp-like values, and machine/provenance field names are rejected from the fingerprinted contract.

Lifecycle contracts reject non-`state_dict` serialization. The accepted lifecycle fixture records:

```text
profile: lifecycle_contract_c
algorithm: HAPPO
state type: EP
share_param: false
three ordered independent actors
actor hidden sizes: [256,256]
critic hidden sizes: [256,256]
feed-forward sequence contract
M=3, N=50
actor dimension: 1059
shared dimension: 3183
action dimension: 51
raw noop: 50
decoded noop: -1
```

The accepted legacy fixture records actor/shared dimensions `909/2727`. Dimension checks use the general `M,N` formulas rather than only the fixed fixture.

## Canonical JSON

`canonical_manifest_bytes(...)` always parses/validates a mapping through the immutable schema and emits:

```text
UTF-8
object keys sorted lexicographically
semantic list order preserved
separators "," and ":"
no whitespace
ensure_ascii=true
allow_nan=false
no BOM
no trailing newline
```

Pretty-printing and a human-readable final LF do not affect the fingerprint because input is parsed, validated, and recanonicalized before hashing.

Dictionary insertion order is non-semantic. Agent, feature, task-row, tail, shared-block, layer-size, tensor-shape, and actor-artifact list order remains semantic where the schema defines it.

## Number Canonicalization

Schema-owned decimal fields are normalized to plain canonical decimal strings.

Accepted inputs:

```text
Python int
finite float
Decimal
syntactically numeric string
```

Rules:

```text
NaN and positive/negative infinity rejected
boolean rejected as numeric
negative zero -> "0"
trailing fractional zeros removed
scientific input -> plain decimal output
equivalent 0.0005 / 5e-4 / Decimal("0.0005000") -> "0.0005"
integer schema fields remain JSON integers
boolean schema fields remain JSON booleans
```

The implementation uses `Decimal` after a strict numeric grammar and does not depend on locale or platform formatting.

## SHA-256 Integrity

Definition:

```text
SHA-256(canonical_contract_manifest_bytes)
```

The external form is exactly 64 lowercase hexadecimal characters. Verification:

1. validates and recanonicalizes the manifest;
2. validates the fingerprint form;
3. recomputes SHA-256;
4. compares with `hmac.compare_digest`.

Wrong length, non-hex, uppercase, changed fields, and changed ordered lists fail. There is no bypass flag.

The fingerprint proves immutable manifest integrity. It is not the sole compatibility decision. Two manifests may have different full fingerprints and still be compatible for normal evaluation when the only differences are training-only fields.

## Purpose-Aware Compatibility

Supported decision purposes:

| purpose | Phase 9G-8F-1 decision |
|---|---|
| `STRUCTURAL_INSPECTION` | Compare model/state-dict structure only |
| `NORMAL_EVALUATION` | Require inference semantics; ignore training-only fields |
| `EXPLICIT_ABLATION_EVALUATION` | Require the exact validator-owned named policy |
| `VALIDATED_WEIGHT_CONTINUATION` | Require complete contract and artifact inventory |
| `TRAINING_INITIALIZATION_OR_FINE_TUNING` | Unsupported/deferred |
| `EXACT_TRAINING_RESUME` | Unsupported |

Every decision carries:

```text
allowed
classification
requested purpose
ordered mismatch list
first mismatch
reason
required acknowledgement, if any
next action, if any
```

Malformed fingerprint input returns a structured `invalid_fingerprint` rejection rather than escaping the compatibility boundary as an exception.

## Structural Comparison

Structural inspection compares:

```text
algorithm/model family
EP/FP state type
serialization mode
agent count and ordered identities
actor count and ordered actor identities
share_param
actor dimensions by ordered agent
shared dimension
action-space type and action dimension
actor/critic/distribution classes
actor and critic hidden sizes
activation
feature-normalization module presence
recurrent flags and recurrent layer count
critic architecture
```

It intentionally does not authorize evaluation or continuation. A passing result points only to future CPU `weights_only` inventory inspection.

## Normal Evaluation Comparison

Normal evaluation first requires structural compatibility, then compares:

```text
profile and training-time profile identity
ordered agent identity
actor schema, feature semantics, normalization, task-row and tail order
shared schema and ordered blocks
action target/noop semantics
snapshot/resolver/mask/budget/guardrail/ownership/arbitration contracts
policy sequence contract
model forward structure
```

It intentionally ignores:

```text
optimizer class and optimizer hyperparameters
actor/critic learning rates
PPO epochs and minibatch counts
clip/value/entropy coefficients
gradient clipping settings
gamma and GAE lambda
ValueNorm training contract fields
episode length and rollout thread count
initialization method and action gain
```

Tests prove that learning-rate, PPO-epoch, and rollout-thread changes alter the complete fingerprint but remain normal-evaluation compatible. Feature order, shared-block order, mask, budget, noop, and agent-order differences fail.

## Named Ablation

The only Phase 9G-8F-1 ablation policy is code-owned:

```text
lifecycle_contract_c_checkpoint_to_lifecycle_ablation_evaluation_v1
```

It requires:

```text
checkpoint profile: lifecycle_contract_c
current profile: lifecycle_ablation
purpose: explicit ablation evaluation
explicit exact policy name
matching actor/shared/action/model/sequence structure
```

Only these exact behavior differences are permitted:

```text
profile/training-time profile -> lifecycle_ablation
resolver contract -> disabled
budget release contract -> disabled
Contract C mask -> lifecycle ablation physical/noop mask
```

Missing the explicit name, omitting a declared difference, or adding any unapproved difference hard-fails. No caller-provided whitelist exists. This policy cannot authorize continuation.

## Validated Weight Continuation

Validated weight continuation requires:

```text
valid native manifest and fingerprint
structural compatibility
field-by-field equality of the complete immutable contract
state_dict serialization
complete ordered actor inventory bound to contract actor identities
critic inventory
ValueNorm inventory when enabled
training-state manifest bound to the same contract fingerprint
explicit acknowledgement of fresh optimizer/counter/RNG/environment/buffer state
```

Training-contract changes, including learning rate, optimizer epsilon, gamma, GAE lambda, and ValueNorm settings, reject continuation with field-level mismatches.

The required acknowledgement is:

```text
actor and critic optimizers, counters, RNG, environment, resolver,
and rollout buffers reset
```

This is validated weight continuation, not exact resume.

## Deferred And Unsupported Purposes

`TRAINING_INITIALIZATION_OR_FINE_TUNING` is explicitly `unsupported_deferred`. Contract v1 does not reinterpret it as continuation.

`EXACT_TRAINING_RESUME` is explicitly unsupported even for identical fingerprints. Current checkpoints lack:

```text
actor and critic optimizer state
training counters and best-reward state
RNG state
environment/resolver/budget state
rollout-buffer state
```

## Missing Metadata / Legacy

The pure missing-metadata helper freezes:

| request | result |
|---|---|
| Structural inspection | May proceed only to future CPU weights-only inventory inspection |
| Explicit legacy normal evaluation, resolver off, fallback requested | Restricted legacy fallback |
| Lifecycle normal evaluation | Hard error |
| Legacy continuation | Hard error |
| Fine-tuning | Hard error |
| Exact resume | Hard error |

No native lifecycle manifest is fabricated for an old checkpoint.

## Training-State And File Inventory

Training-state format:

```text
assignment_training_state_v1
```

It contains:

```text
immutable contract fingerprint binding
checkpoint kind and generation
optional episode/update index
continuation classification
ordered actor identities and actor artifacts
critic artifact
ValueNorm artifact
optimizer/counter/RNG/environment-resolver/buffer availability
```

Artifact entries contain:

```text
role
normalized relative file name
file size
file SHA-256
state_dict serialization mode
actor identity where applicable
normalized tensor inventory
tensor-inventory SHA-256
```

Paths normalize `\` to `/`; absolute paths and `..` traversal fail. Duplicate artifact paths, unknown/partial actor identities, duplicate tensor keys, unsupported dtypes, and digest disagreement fail.

Training-state manifests support validated mapping round trips. This phase computes only synthetic metadata digests; it does not hash or serialize real model artifacts.

## Tensor Inventory Comparison

State-dict inventory entries are normalized by lexicographically sorted tensor key while preserving shape dimension order and stable dtype names.

The pure exact comparator reports:

```text
missing keys
unexpected keys
shape mismatches
dtype mismatches
duplicate/invalid inventory
```

It provides no partial-load, prefix-guess, key-rewrite, padding, truncation, or `strict=False` mode.

The future three-stage load order remains:

```text
1. metadata/schema/fingerprint/purpose validation
2. trusted CPU weights_only state-dict deserialization and inventory comparison
3. live model.load_state_dict(..., strict=True)
```

Only stage 1 and pure synthetic inventory comparison exist in this phase. No deserialization or live model mutation was performed.

## Validation

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Commands:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl `
  python -m py_compile `
  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_checkpoint_contract.py `
  scripts/environments/test_assignment_checkpoint_contract_core.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl `
  python scripts/environments/test_assignment_checkpoint_contract_core.py

git diff --check
git status --short --untracked-files=all
```

Results:

```text
py_compile: PASS
pure checkpoint-contract tests: PASS, 27/27
canonical determinism: PASS
ordered-list semantic sensitivity: PASS
purpose-aware compatibility matrix: PASS
training-state JSON round trip: PASS
runtime non-integration assertion: PASS
git diff --check: PASS
git status: expected Phase 9G-8F-1 files plus pre-existing uncommitted Phase 9G work
```

No earlier pure suite was required because the new module imports no prior lifecycle module and changes no shared pure dependency.

## Known Limitations

- Runtime manifest construction and persistence do not exist yet.
- No file digest has been computed for a real actor, critic, or ValueNorm artifact.
- No checkpoint path resolution or atomic metadata write exists.
- No loader calls the compatibility core.
- Stage 2 trusted `weights_only` deserialization and stage 3 strict state loading are not implemented.
- Fine-tuning remains deferred.
- Exact resume remains unsupported.
- Unversioned legacy fallback is only a decision contract; no file was read.
- Recurrent lifecycle policy support remains outside `lifecycle_contract_c_v1`.
- Resolver-enabled training remains prohibited.

## Next Phase Boundary

The next possible phase is:

```text
Phase 9G-8F-2:
Checkpoint Save Metadata Integration
```

No Phase 9G-8F-2 runtime integration was started.

## Non-Modification Confirmation

```text
runner save/load integration: not implemented
playback/evaluation loader integration: not implemented
checkpoint actor/critic/ValueNorm weights: not saved or loaded
model forward/backward/optimizer step: not run
training/playback/evaluation: not run
Isaac Sim/AppLauncher: not launched
installed HARL/Conda environment: not modified
commit: not made
```

## Final Decision

```text
PASS
```

All Phase 9G-8F-1 pure-contract acceptance criteria pass. Manifest integrity and load-purpose compatibility are distinct, exact named ablation is validator-owned, continuation binds the full contract and artifact inventory, and unsupported purposes cannot be silently downgraded.
