# Phase 9G-8F-2 Checkpoint Save Metadata Integration Report

Date: 2026-07-09

## Classification

```text
PASS
```

Phase 9G-8F-2 integrates the accepted checkpoint contract into the project-local assignment save boundary. All four current save paths route through one native coordinator for supported state-dict profiles. The checkpoint-local training-state manifest is committed last and is the sole completion marker.

No loader integration, checkpoint weight loading, model execution, or training occurred.

## Files

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_checkpoint_save.py

scripts/environments/
  test_assignment_checkpoint_save_metadata_integration.py

AgentRead/20260709/
  PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F2_SAVE_METADATA_INTEGRATION_20260709.md
```

Modified:

```text
assignment_checkpoint_contract.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_checkpoint_contract_core.py
AgentRead/TASK_PROGRESS.md
```

The checkpoint core modification is narrow:

```text
official save-kind values:
  regular
  best
  episode_snapshot
  final

continuation classification:
  validated_weight_continuation_candidate
```

Explicitly not modified in this phase:

```text
assignment_harl_wrapper.py
assignment_lifecycle_resolver.py
assignment_lifecycle_resolver_runtime.py
observation or available-action construction
play.py
play_assignment.py
playback diagnostics loader
comparison evaluation loader
installed HARL
Conda environment
YAML/runtime defaults
```

The worktree contains earlier uncommitted Phase 9G changes in some of those project files; Phase 9G-8F-2 did not alter them.

## Save-Path Audit

Read-only inspection of installed `OnPolicyBaseRunner` established:

| save kind | actual caller | destination | project routing |
|---|---|---|---|
| Regular | `OnPolicyBaseRunner.run()` interval branch | `run_root/models` | overridden `AssignmentOnPolicyHARunner.save()` infers `regular` |
| Best | `OnPolicyBaseRunner.run()` reward branch | `run_root/best_model` | overridden save infers `best` |
| Episode snapshot | `OnPolicyBaseRunner.run()` checkpoint branch | `run_root/models/checkpoints/episode_<n>` | overridden save infers kind and episode index |
| Final | project `train.py` after `runner.run()` | `run_root/models` | explicit `checkpoint_kind="final"` |

The inherited runner calls `self.save(...)`, so the project subclass override covers regular, best, and episode saves without modifying installed HARL. The final project call is explicitly classified and cannot be confused with an interval save.

Installed HARL's original save method writes critic and ValueNorm inside the actor loop. Native assignment saves no longer use that branch: the coordinator writes each actor once, then one critic and one ValueNorm artifact.

## Runtime Manifest Builder

Implementation:

```text
capture_assignment_checkpoint_runtime_state(runner)
build_assignment_checkpoint_contract_manifest(runtime_state)
```

Actual runtime sources:

| manifest area | source of truth |
|---|---|
| Profile/schema/order | `AssignmentHarlWrapper.assignment_observation_schema_manifest` |
| Observation row/block layout | `AssignmentHarlWrapper.assignment_observation_layout` |
| Actor input dimensions | constructed actor wrappers' `obs_space_size` |
| Critic input dimension | constructed `VCritic.share_obs_space` |
| Action dimensions | constructed Categorical linear output and actor action space |
| Actor identities/order | wrapper `agents`, aligned to runner actor list |
| Actor/model classes | constructed HAPPO, StochasticPolicy, Categorical objects |
| Critic classes | constructed VCritic and VNet objects |
| Hidden sizes | constructed actor and critic policy objects |
| Activation/feature normalization | constructed actor/critic MLP bases |
| Recurrent contract | constructed policies and installed-generator selection |
| Optimizer class/settings | constructed actor and critic optimizer owners |
| PPO/loss settings | constructed HAPPO and VCritic objects |
| Gamma/GAE/time limits/rollout shape | constructed critic buffer |
| ValueNorm | actual object presence checked against resolved config |

The builder does not construct the manifest from raw YAML alone.

## Effective Model Validation

The runtime capture records:

```text
actor hidden sizes: [256,256]
critic hidden sizes: [256,256]
```

The unused YAML `hidden_sizes_critic=[512,256]` is not represented as effective structure. A synthetic constructed-runner test includes that unused YAML field and proves the manifest still records the actual VNet `[256,256]`.

Before a native save, hard checks cover:

```text
wrapper actor dimensions == constructed actor inputs
wrapper shared dimension == constructed critic input
wrapper action dimension == every Categorical action head
wrapper agent order == actor artifact order
one distinct actor policy per identity
share_param == false for native v1
lifecycle profile == HAPPO + EP + feed-forward
actor/critic activation, normalization, recurrence and optimizer settings agree
ValueNorm config == actual ValueNorm presence
serialization == state_dict
```

Dimension, shared-parameter, recurrent, and EP/FP mismatch tests hard-fail before artifact replacement.

## State-Dict Boundary

`lifecycle_contract_c` requires:

```text
save_entire_model = false
serialization_mode = state_dict
three independent actor state dictionaries
one critic state dictionary
ValueNorm state dictionary when enabled
```

Lifecycle full-model saving raises before writing.

Canonical names:

```text
actor_agent_robot_0.pt
actor_agent_robot_1.pt
actor_agent_robot_2.pt
critic_agent.pt
value_normalizer.pt
```

Numeric actor fallbacks, unexpected actor identities, conflicting critic/ValueNorm names, and `*_full.pt` artifacts hard-fail with a clean-directory error.

## Atomic Artifact Protocol

Each state dictionary is saved through:

```text
same-directory unique temporary file
-> torch.save(state_dict, open temporary stream)
-> flush
-> fsync(file)
-> os.replace(temp, final)
-> best-effort fsync(directory)
```

The temporary and final path share a filesystem. Temporary names never enter metadata and are removed on failure where possible. Complete model objects are never passed to the native coordinator.

Synthetic tests write real CPU state-dict files with this path. They do not read those files with `torch.load`.

## Run-Root Metadata

Authoritative run-root files:

```text
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
```

Behavior:

```text
neither exists:
  atomically create canonical pair

both exist:
  parse and validate schema
  require canonical UTF-8 JSON plus LF
  verify lowercase SHA-256 plus LF
  require exact current runtime contract equality

only one exists:
  hard error

different contract:
  hard error before checkpoint artifact replacement
```

The persisted manifest is canonical bytes plus one LF. The fingerprint is still computed from canonical bytes without that LF.

## Child Metadata

Recognized children are limited to:

```text
run_root/models
run_root/best_model
run_root/models/checkpoints/episode_<n>
```

Every complete child contains:

```text
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
assignment_training_state_manifest.json
```

Child contract copies are byte-identical to the run-root pair. Partial child pairs and root/child disagreement hard-fail before artifact replacement. No arbitrary parent search exists.

## Completion Marker

Overwrite protocol:

```text
1. Build and validate effective runtime manifest.
2. Validate/write run-root contract.
3. Validate child contract and conflicting artifacts.
4. Remove old assignment_training_state_manifest.json.
5. Atomically save all actors.
6. Atomically save critic once.
7. Atomically save ValueNorm once when enabled.
8. Hash final files and construct tensor inventories.
9. Write/validate child contract pair.
10. Atomically write assignment_training_state_manifest.json last.
```

The final file is the completion marker. If any operation after marker invalidation fails, the coordinator removes any new marker and leaves the directory explicitly incomplete.

Event-order testing proves `training_state_manifest_committed` is last.

## Checkpoint Generation

`AssignmentOnPolicyHARunner` owns:

```text
_assignment_checkpoint_generation
```

It starts at `0`. The current value is passed into the coordinator and increments only after a successful complete save. A coordinator exception leaves it unchanged.

Routing tests prove successful generations:

```text
regular: 0
best: 1
episode snapshot: 2
final: 3
```

The episode snapshot also records its parsed episode index. This counter is run-local metadata and does not imply exact resume.

## File Digests

Artifact SHA-256 is computed after final-file replacement:

```text
stream final bytes in 1 MiB chunks
record final file size
compare pre/post size and modification identity
emit lowercase 64-character SHA-256
```

Tests compare every recorded size and digest against final bytes. Changing one actor state changes its recorded file digest. Training-state metadata contains only normalized relative file names.

## Tensor Inventory

Inventories are built from the exact in-memory mappings passed to `torch.save`, without deserialization.

Recorded per entry:

```text
tensor key
ordered shape
stable dtype
```

Keys are lexicographically normalized and `tensor_inventory_sha256` is recorded. Unsupported non-tensor state entries hard-fail with their key/type; no state entry is silently omitted.

No `torch.load`, `load_state_dict`, prefix rewriting, partial loading, padding, or truncation exists in this phase.

## Training-State Manifest

Format:

```text
assignment_training_state_v1
```

It records:

```text
contract fingerprint binding
checkpoint kind
checkpoint generation
optional episode/update index
validated_weight_continuation_candidate
ordered actor artifact inventory
critic artifact inventory
ValueNorm inventory when enabled
file sizes and SHA-256
tensor inventories and inventory digests
```

Current unavailable state is accurately false:

```text
actor optimizer
critic optimizer
training counters
RNG
environment/resolver
rollout buffer
```

Exact resume is not claimed.

## ValueNorm

When enabled, the coordinator requires a ValueNorm state dictionary and records its file/inventory digests. When disabled, it requires no ValueNorm state, writes no file, and records no ValueNorm artifact.

Config/object disagreement hard-fails. Critic and ValueNorm save-event counts are each exactly one per completed native save.

## Legacy Non-Regression

Supported native legacy state-dict saves use:

```text
legacy actor dimension: 909
legacy shared dimension: 2727
canonical named actor artifacts
native contract and training-state metadata
```

Legacy `save_entire_model=True` preserves the inherited HARL path and creates no native assignment metadata claim.

Other non-native legacy configurations, such as parameter sharing or non-HAPPO algorithms, also preserve the inherited legacy save branch rather than being mislabeled with the HAPPO independent-actor v1 contract.

No legacy observation, mask, training, or loader behavior changed.

## Failure Injection

Deterministic failures were injected after:

```text
old completion-marker invalidation
first actor save
all actor saves
critic save
ValueNorm save
child contract metadata write
```

For every point:

```text
old marker was not left stale
no new completion marker remained
current-operation temporary files were cleaned
checkpoint remained incomplete
runner generation did not increment on coordinator failure
```

No process termination testing was needed.

## Validation

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Results:

| validation | result |
|---|---|
| `py_compile` for changed/new Python files | PASS |
| Phase 9G-8F-1 core tests | PASS, 27/27 |
| Phase 9G-8F-2 save metadata tests | PASS, 15/15 |
| Phase 9G-8E lifecycle mask/HARL replay regression | PASS, 11/11 |
| Phase 9G-8E-R feed-forward guard regression | PASS, 9/9 |
| `git diff --check` | PASS; line-ending warnings only |
| `git status --short --untracked-files=all` | Expected Phase 9G worktree plus 8F-2 files |

The tests used temporary directories and synthetic CPU tensors only. The Gym deprecation message emitted during lightweight project module import is an existing dependency warning, not a test failure.

## Known Limitations

- No checkpoint loader or compatibility enforcement is integrated.
- No checkpoint file was deserialized.
- No live actor/critic forward or output-equivalence smoke was run.
- No optimizer, counter, RNG, environment, resolver, or rollout state is saved.
- Exact training resume remains unsupported.
- Fine-tuning remains deferred.
- Native legacy metadata currently targets the official independent HAPPO state-dict structure; other legacy save configurations retain inherited behavior without a native claim.
- No training or Isaac Sim runtime save was executed; runner routing is validated with project-local fakes.
- Resolver-enabled training remains prohibited.

## Non-Modification Confirmation

```text
installed HARL: not modified
Conda environment: not modified
checkpoint loaders: not integrated
checkpoint weights: never loaded
model load_state_dict: not called
actor/critic forward: not run
backward/optimizer step: not run
training/playback/evaluation: not run
Isaac Sim/AppLauncher: not launched
commit: not made
```

## Next Phase Boundary

The next possible phase is:

```text
Phase 9G-8F-3:
All-Loader Compatibility Integration
```

No Phase 9G-8F-3 implementation was started.

## Final Decision

```text
PASS
```

All four save paths use one project-local state-dict coordinator, runtime metadata reflects constructed behavior, root/child contracts are strict, real saved-file digests and tensor inventories are recorded, the completion marker is last, and injected failures cannot leave a completed checkpoint claim.
