# Phase 9G-8F-3 All-Loader Compatibility Integration Report

Date: 2026-07-09

## Classification

```text
PASS
```

One project-level assignment loader now owns native metadata discovery, purpose-aware compatibility, artifact integrity, CPU `weights_only` inspection, and strict live state loading.

All five audited assignment checkpoint entry points are either routed through this loader or hard-rejected before any unvalidated restore.

## Files

Created:

```text
assignment_checkpoint_load.py
scripts/environments/test_assignment_checkpoint_all_loader_integration.py
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F3_ALL_LOADER_INTEGRATION_20260709.md
```

Modified:

```text
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play.py
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_checkpoint_contract_core.py
AgentRead/TASK_PROGRESS.md
```

Narrow contract/save corrections:

```text
continuation acknowledgement now explicitly includes best-reward reset
runtime manifest builder may represent lifecycle_ablation only when
  allow_evaluation_only_profile=True
native save eligibility remains unchanged
```

Explicitly not modified:

```text
installed HARL
Conda environment
checkpoint artifact save/completion ordering
actor/critic architecture
observation/shared/action schemas
lifecycle resolver or Contract C
reward/environment control
YAML defaults
```

## Shared Loader

Implementation:

```text
assignment_checkpoint_load.py
  load_assignment_checkpoint(...)
  build_assignment_evaluation_contract_manifest(...)
```

Named result:

```text
AssignmentCheckpointLoadResult
```

It records:

```text
checkpoint directory
load purpose
checkpoint kind and generation
contract fingerprint
structured compatibility decision
loaded actor identities
critic and ValueNorm loaded flags
legacy fallback use
named ablation
continuation acknowledgement
warnings
```

Errors use project-local metadata, integrity, compatibility, inventory, and load exception classes. Loader failures are raised; none are converted to warnings followed by random weights.

## Three-Stage Validation

### Stage 1

Before `torch.load`:

```text
resolve selected directory
validate local manifest/fingerprint pair
require native completion marker
validate recognized run-root agreement
parse assignment_checkpoint_contract_v1
verify canonical manifest SHA-256
parse assignment_training_state_v1
verify contract-fingerprint binding
run purpose-aware compatibility
validate canonical artifact roles/names
verify every declared file exists, size and SHA-256
```

Normal actor-only evaluation still validates every actor, critic, and ValueNorm file declared by the completed checkpoint. Only actors proceed to Stage 2.

### Stage 2

Purpose-required artifacts are loaded exactly through:

```python
torch.load(path, map_location="cpu", weights_only=True)
```

Each mapping is checked against:

```text
declared tensor key/shape/dtype inventory
declared tensor-inventory SHA-256
current live module key/shape/dtype inventory
```

No prefix rewriting, guessing, casting, partial load, padding, truncation, or `strict=False` exists.

### Stage 3

Only after every required artifact passes Stages 1 and 2:

```python
module.load_state_dict(state_dict, strict=True)
```

Actors load in manifest order. Continuation then loads critic and ValueNorm when required.

Current live states are cloned before mutation. An unexpected Stage-3 failure triggers strict rollback and raises with the failing artifact and any rollback error.

## Discovery And Completion

Native local metadata supports:

```text
run_root/models
run_root/best_model
run_root/models/checkpoints/episode_<n>
self-contained copied checkpoint directory
```

For recognized parent relationships, available run-root metadata must exactly match child canonical bytes and fingerprint. The loader does not walk arbitrary ancestors.

A native contract pair without:

```text
assignment_training_state_manifest.json
```

is incomplete and hard-fails before deserialization. A marker without a contract pair also fails.

Manifest-only and fingerprint-only states are rejected.

## Artifact Integrity

Every completion-marker artifact must:

```text
resolve inside the selected checkpoint directory
be a regular file
match recorded byte size
match recorded SHA-256
use its canonical role/name
```

Native completed checkpoints require complete ordered actors and `critic_agent.pt`. ValueNorm presence must match the immutable training contract.

Rejected:

```text
missing or partial actor inventory
unknown/numeric native actor files
full-model pickle files
unexpected critic/ValueNorm variants
disabled-but-present ValueNorm
duplicate/traversing artifact paths
```

Tests cover different-size modification and same-size SHA-only modification.

## Inventory And Atomic Mutation

Tests inject invalid state dictionaries at:

```text
third actor
critic
ValueNorm
```

They cover missing key, unexpected key, shape mismatch, dtype mismatch, non-tensor value, and inventory-digest mismatch.

All targets remain byte-for-byte unchanged and have zero `load_state_dict` calls when any Stage-2 inspection fails. This proves actor 0 cannot be mutated before actor 2, critic, or ValueNorm validation completes.

Strict-call spies confirm every successful live load receives `strict=True`.

## Training Weight Continuation

`AssignmentOnPolicyHARunner.restore()` now owns assignment continuation.

Flow:

```text
models constructed
-> project restore override
-> current runtime manifest captured from actual runner
-> VALIDATED_WEIGHT_CONTINUATION
-> all actor/critic/ValueNorm inspection
-> strict live load
```

Assignment checkpoints never call inherited HARL restore. The retained `super().restore()` branch applies only when `assignment_rl=False`.

Native matching legacy metadata may use the same exact continuation contract. Metadata-free legacy continuation is rejected.

## Continuation Acknowledgement

Project CLI:

```text
--acknowledge-weight-continuation-reset
```

With assignment `--dir`, the flag is mandatory before AppLauncher and runner construction. Supplying it without both assignment mode and `--dir` also fails.

Acknowledged resets:

```text
actor and critic optimizers
training counters
best-reward state
RNG
environment/resolver state
rollout buffers
```

Missing acknowledgement rejects before artifact inspection or live mutation.

## Entry-Point Coverage

### Training

```text
train.py --dir
-> AssignmentOnPolicyHARunner.restore()
-> shared loader
-> VALIDATED_WEIGHT_CONTINUATION
```

No double loading occurs.

### Generic HARL Play

Selected decision:

```text
hard-reject assignment task names before AppLauncher/runner construction
guide user to play_assignment.py
```

Non-assignment generic play behavior is unchanged. Assignment checkpoints cannot reach inherited unvalidated restore.

### Assignment Play

`play_assignment.py` constructs actors, builds the current evaluation contract from wrapper/actors/resolved config, and calls the shared loader.

Supported:

```text
NORMAL_EVALUATION
EXPLICIT_ABLATION_EVALUATION
explicit unversioned legacy evaluation fallback
```

The duplicated actor checkpoint finder and direct `torch.load` were removed.

### Playback Diagnostics

Playback diagnostics uses the same actor construction and shared loader boundary.

The checkpoint kind now comes from the training-state completion marker, not the directory basename. Diagnostic metadata records:

```text
checkpoint generation
load purpose
named ablation
legacy fallback
```

### Comparison Evaluation

The comparison script still prohibits assignment RL for its existing Stage 4A scope.

Its duplicated direct actor loader was removed. Both the public main guard and internal assignment-RL branch hard-reject before any checkpoint load.

## Named Ablation

The only supported policy remains:

```text
lifecycle_contract_c_checkpoint_to_lifecycle_ablation_evaluation_v1
```

It requires native lifecycle metadata, current `lifecycle_ablation`, the exact explicit name, and only the validator-owned profile/resolver/mask/budget differences.

Missing/wrong name, an extra guardrail difference, and continuation requests fail before deserialization. The result records the accepted name.

The save-side runtime builder's evaluation-only profile switch permits constructing the current ablation contract; it does not permit saving ablation checkpoints.

## Unversioned Legacy Fallback

Allowed only when all are explicit:

```text
purpose = NORMAL_EVALUATION or STRUCTURAL_INSPECTION
current profile = legacy
resolver contract = disabled
actor dimension = 909
action dimension = 51
raw noop = 50
explicit fallback request = true
```

It accepts one unambiguous canonical or numeric actor filename per identity, loads CPU `weights_only`, checks exact live key/shape/dtype inventory, and uses strict loading.

Rejected:

```text
missing explicit fallback
lifecycle current profile
duplicate canonical/numeric actor candidates
full-model pickle
partial actor set
training continuation
```

No native manifest is fabricated. The result marks `legacy_fallback_used=True` and warns that no immutable digest metadata exists.

## ValueNorm

Normal evaluation validates the declared ValueNorm file size/digest but does not deserialize or load it.

Validated continuation requires:

```text
manifest enables ValueNorm
completion marker declares value_normalizer.pt
live ValueNorm object exists
file and tensor inventories pass
strict load succeeds
```

When disabled, no ValueNorm artifact or live requirement is accepted.

## Direct-Load Scan

Audited entry points contain no direct `torch.load`, direct `load_state_dict`, `_load_assignment_actors`, or `_actor_checkpoint_path`.

Remaining relevant occurrences:

| occurrence | classification |
|---|---|
| `assignment_checkpoint_load.py` native `torch.load` | Shared Stage 2; CPU and `weights_only=True` |
| `assignment_checkpoint_load.py` legacy `torch.load` | Explicit legacy fallback; CPU and `weights_only=True` |
| `assignment_checkpoint_load.py` `load_state_dict` | Shared Stage 3 and rollback; always `strict=True` |
| `AssignmentOnPolicyHARunner.__init__ -> self.restore()` | Dynamically reaches project override for assignment |
| `AssignmentOnPolicyHARunner.restore -> super().restore()` | Non-assignment branch only |
| Installed HARL restore | Unmodified; unreachable for native assignment paths |

No `strict=False` occurs in the shared loader.

## Tests

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Results:

| suite | result |
|---|---|
| Phase 9G-8F-1 core | PASS, 27/27 |
| Phase 9G-8F-2 save integration | PASS, 15/15 |
| Phase 9G-8F-3 all-loader integration | PASS, 15/15 |
| Phase 9G-8E mask/HARL replay | PASS, 11/11 |
| Phase 9G-8E-R feed-forward guard | PASS, 9/9 |
| `py_compile` changed/new files | PASS |
| Direct assignment load scan | PASS |
| `git diff --check` | PASS |

Tests use temporary native checkpoints created by the 8F-2 coordinator, synthetic CPU modules, and state dictionaries. They exercise safe deserialization and strict loading without actor/critic forward calls.

The Gym deprecation message during lightweight module import is an existing dependency warning and not a test failure.

## Known Limitations

- No real training checkpoint was loaded.
- No actor/critic output-equivalence test was run.
- No actor/critic forward, backward, optimizer step, or buffer readiness smoke was run.
- Generic assignment playback remains intentionally unavailable through generic `play.py`.
- Comparison-method assignment RL remains intentionally disabled.
- Unversioned legacy fallback cannot offer cryptographic file integrity.
- Fine-tuning remains deferred.
- Exact training resume remains unsupported.
- Resolver-enabled training remains prohibited.

## Non-Modification Confirmation

```text
installed HARL: not modified
Conda environment: not modified
checkpoint save completion semantics: unchanged
resolver/Contract C/reward/environment behavior: unchanged
actor/critic forward: not run
backward/optimizer step: not run
training/playback/evaluation: not run
Isaac Sim/AppLauncher: not launched
commit: not made
```

## Next Phase Boundary

The next possible phase is:

```text
Phase 9G-8F-4:
Actor / Critic / Buffer Forward-Backward Readiness
```

No Phase 9G-8F-4 work was started.

## Final Decision

```text
PASS
```

Native assignment loads now require a complete checkpoint, verified immutable contract, purpose authorization, all-declared-file integrity, exact tensor inventories, and all-artifact preinspection before strict mutation. No audited assignment entry point can bypass this boundary.
