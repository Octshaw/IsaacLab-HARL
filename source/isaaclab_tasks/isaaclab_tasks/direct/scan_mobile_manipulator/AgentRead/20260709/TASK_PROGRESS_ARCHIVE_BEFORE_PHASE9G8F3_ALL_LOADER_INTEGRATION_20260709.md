# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-2 completed checkpoint save metadata integration.

Classification:

```text
PASS
```

Accepted prerequisites:

```text
Phase 9G-8F-0: DESIGN-READY
Phase 9G-8F-1: PASS
```

Resolver-enabled training remains prohibited.

## Latest Completed Phase

The checkpoint contract is now integrated into the project-local save boundary.

Native state-dict checkpoints contain:

```text
run-root contract manifest and SHA-256 fingerprint
checkpoint-local contract copies
canonical named actor state dictionaries
critic state dictionary
ValueNorm state dictionary when enabled
real artifact file size and SHA-256
tensor key/shape/dtype inventories and inventory digests
checkpoint-local training-state manifest
```

`assignment_training_state_manifest.json` is written last and is the checkpoint completion marker.

## Active Save Architecture

One `AssignmentCheckpointSaveCoordinator` handles:

```text
regular models/
best_model/
models/checkpoints/episode_<n>/
explicit final models/
```

Runtime manifests are built from actual resolved wrapper, profile, constructed actor/critic/action-head, optimizer, buffer, ValueNorm, and training values. The effective actor and critic hidden sizes are `[256,256]`; unused YAML `hidden_sizes_critic` is excluded.

Native lifecycle saves are HAPPO, EP, independent feed-forward actors, and state-dict only. Lifecycle full-model saves hard-fail.

Native legacy HAPPO state-dict saving is supported. Legacy full-model and other non-native legacy configurations preserve inherited HARL behavior without native metadata.

## Files

Created:

```text
assignment_checkpoint_save.py
scripts/environments/test_assignment_checkpoint_save_metadata_integration.py
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F2_SAVE_METADATA_INTEGRATION_20260709.md
```

Modified:

```text
assignment_checkpoint_contract.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_checkpoint_contract_core.py
AgentRead/TASK_PROGRESS.md
```

Installed HARL, Conda, YAML defaults, wrapper observations/masks, resolver behavior, and loader/playback/evaluation files were not modified.

## Validation

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Results:

```text
py_compile: PASS
Phase 9G-8F-1 core tests: PASS, 27/27
Phase 9G-8F-2 save tests: PASS, 15/15
Phase 9G-8E mask/HARL replay: PASS, 11/11
Phase 9G-8E-R feed-forward guard: PASS, 9/9
git diff --check: PASS
```

Failure injection passed after marker invalidation, first/all actor saves, critic, ValueNorm, and child metadata. Every failed overwrite left no completion marker and did not advance runner generation.

Tests wrote synthetic CPU state-dict artifacts in temporary directories. No checkpoint weight was loaded or deserialized.

## Known Boundaries

No loader invokes the checkpoint compatibility core yet.

No real actor/critic forward, backward, optimizer step, output-equivalence load smoke, training, playback, evaluation, or Isaac Sim run occurred.

Exact training resume remains unsupported. Fine-tuning remains deferred.

## Do Not Do

Do not run resolver-enabled training.

Do not bypass the completion marker or run-root/child contract agreement.

Do not use inherited HARL restore for native lifecycle checkpoints.

Do not modify installed HARL or the Conda environment.

Do not commit unless explicitly requested.

## Next Step

```text
Phase 9G-8F-3:
All-Loader Compatibility Integration
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F2_SAVE_METADATA_INTEGRATION_20260709.md
AgentRead/20260709/PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F1_CONTRACT_CORE_20260709.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
```
