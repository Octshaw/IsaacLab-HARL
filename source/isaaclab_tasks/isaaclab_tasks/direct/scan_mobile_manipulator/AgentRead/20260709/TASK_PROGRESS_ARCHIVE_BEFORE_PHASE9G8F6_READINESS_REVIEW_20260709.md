# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-5 completed the native checkpoint save/load/continuation smoke.

Classification:

```text
PASS
```

Accepted prerequisites:

```text
Phase 9G-8F-1: PASS
Phase 9G-8F-2: PASS
Phase 9G-8F-3: PASS
Phase 9G-8F-4: PASS
```

Resolver-enabled training remains prohibited pending Phase 9G-8F-6 review.

## Latest Completed Phase

Synthetic CPU evidence completed:

```text
real installed HARL source models
real HAPPO/VCritic source preparation updates
project AssignmentCheckpointSaveCoordinator
native manifest/fingerprint/completion metadata
shared load_assignment_checkpoint
fresh real HARL target models
exact state and deterministic output equivalence
validated weight continuation
real post-load actor/critic updates
continuation re-save
```

No real prior training checkpoint was used.

## Checkpoint Result

Lifecycle contract:

```text
actor dimension: 1059
shared dimension: 3183
action dimension: 51
actor count: 3
ValueNorm: enabled
```

First temporary checkpoint:

```text
kind: final
generation: 0
checkpoint-local files: 8
total size: 7,828,369 bytes
state equality: 51/51 keys exact
actor output max difference: 0.0
critic output max difference: 0.0
ValueNorm output max difference: 0.0
```

Target optimizers remained empty after load. Adam state appeared only after the real post-load HAPPO/VCritic updates.

This is validated weight continuation, not exact resume.

The same coordinator owner re-saved generation `1`; the contract fingerprint remained stable and updated actor/critic artifact SHA-256 values changed.

## Purpose And Negative Paths

```text
NORMAL_EVALUATION:
  actors loaded; critic and ValueNorm untouched

named lifecycle ablation:
  exact validator-owned ablation passed actor-only

native legacy:
  909/2727/51 actor output equivalence passed

different-size and same-size corruption:
  rejected without live mutation

missing completion marker:
  rejected before deserialization

semantic mismatch:
  rejected before deserialization

training-only difference:
  evaluation allowed; continuation rejected

wrong live actor structure:
  inventory rejection without partial mutation
```

## Files

Created:

```text
scripts/environments/test_assignment_checkpoint_save_load_continuation_smoke.py
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F5_SAVE_LOAD_CONTINUATION_SMOKE_20260709.md
```

Modified:

```text
AgentRead/TASK_PROGRESS.md
```

No production source, installed HARL, Conda, YAML, model architecture, observation/mask contract, resolver, reward, or environment behavior changed.

## Validation

```text
Python: C:\isaacenvs\isaac45_harl\python.exe
PyTorch: 2.5.1+cu121
Device: CPU

Phase 9G-8F-5 smoke: PASS, 22/22
Phase 9G-8F-4 readiness: PASS, 15/15
Phase 9G-8F-3 loader: PASS, 15/15
Phase 9G-8F-2 save: PASS, 15/15
Phase 9G-8F-1 core: PASS, 27/27
Phase 9G-8E mask/HARL replay: PASS, 11/11
Phase 9G-8E-R guard: PASS, 9/9

Total: PASS, 114/114
py_compile: PASS
direct assignment load scan: PASS
git diff --check: PASS
```

## Known Boundaries

Fine-tuning and exact resume remain unsupported.

Lifecycle recurrent, FP critic, `share_param=true`, HATRPO, and HAA2C remain outside the official first support matrix.

Resolver-enabled training remains prohibited pending:

```text
Phase 9G-8F-6:
Phase 9G-8F Readiness Review
```

## Do Not Do

Do not run resolver-enabled training before Phase 9G-8F-6 review.

Do not describe validated weight continuation as exact resume.

Do not modify installed HARL or the Conda environment.

Do not commit unless explicitly requested.

## Next Step

```text
Phase 9G-8F-6:
Phase 9G-8F Readiness Review
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F5_SAVE_LOAD_CONTINUATION_SMOKE_20260709.md
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F4_FORWARD_BACKWARD_READINESS_20260709.md
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
```
