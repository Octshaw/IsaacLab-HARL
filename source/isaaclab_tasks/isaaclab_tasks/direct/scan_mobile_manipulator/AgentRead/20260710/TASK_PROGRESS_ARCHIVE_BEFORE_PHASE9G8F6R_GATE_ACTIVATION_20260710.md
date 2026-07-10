# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-6 completed the checkpoint / training-readiness / commit review.

Technical classification:

```text
READY WITH REQUIRED FIXES
```

Commit classification:

```text
NOT COMMIT-READY
```

Phase 9G-8F-1 through 9G-8F-5 checkpoint, loader, model, buffer, and validated-weight-continuation evidence was reviewed and rerun successfully.

Resolver-enabled training remains prohibited.

## Blocking Issue

The current source still hard-blocks `lifecycle_contract_c` training:

```text
assignment_harl_wrapper.py:
  lifecycle_contract_c.training_allowed = False

assignment_harl_training.py:
  AssignmentIsaacLabEnv raises RuntimeError when training_allowed is false.
```

The blocked reason is now stale because checkpoint manifest/fingerprint, loader compatibility, forward/backward readiness, and save/load validation have passed. This must be fixed in a narrow corrective phase before any controlled training smoke is authorized.

## Latest Verification

Environment:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Regression suites:

```text
Phase 9G-8F-1 contract core:       PASS, 27/27
Phase 9G-8F-2 save integration:    PASS, 15/15
Phase 9G-8F-3 loader integration:  PASS, 15/15
Phase 9G-8F-4 model readiness:     PASS, 15/15
Phase 9G-8F-5 continuation smoke:  PASS, 22/22
Phase 9G-8E mask/HARL replay:      PASS, 11/11
Phase 9G-8E-R feed-forward guard:  PASS, 9/9

Total: PASS, 114/114
```

Additional checks:

```text
py_compile changed/new Python files: PASS
direct assignment load scan: PASS
git diff --check: PASS with LF-to-CRLF warnings only
```

No Isaac Sim, AppLauncher, training, playback, evaluation, checkpoint development experiment, real checkpoint load, installed HARL modification, Conda modification, or commit occurred.

## Active Architecture

Current supported implementation evidence:

```text
lifecycle actor dim: 1059 for M=3,N=50
lifecycle shared dim: 3183 for M=3,N=50
action dim: 51
raw noop: 50
decoded noop: -1
policy sequence: feed-forward only
algorithm/state: HAPPO + EP
actor sharing: false
checkpoint serialization: state_dict only
validated weight continuation: supported
exact resume: unsupported
fine-tuning with changed contract: deferred
```

The checkpoint path uses ordered manifests, canonical JSON, SHA-256 fingerprints, atomic native saves, a shared strict loader, and purpose-aware compatibility.

## Files Changed By Latest Phase

Created:

```text
AgentRead/20260709/PHASE9G8F6_CHECKPOINT_TRAINING_READINESS_AND_COMMIT_REVIEW.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F6_READINESS_REVIEW_20260709.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

No production Python, tests, YAML/runtime defaults, installed HARL files, Conda files, resolver behavior, Contract C behavior, observation behavior, mask behavior, checkpoint contracts, save/load behavior, model/buffer behavior, reward, or controller behavior changed in Phase 9G-8F-6.

## Do Not Do

Do not run resolver-enabled training before the corrective review phase.

Do not describe validated weight continuation as exact resume.

Do not modify installed HARL or the Conda environment.

Do not commit the current worktree yet.

## Next Step

```text
Phase 9G-8F-6R:
Controlled Training Gate Activation and Review Closure
```

This next phase should be narrow: update the stale `lifecycle_contract_c` training gate/message, preserve all existing contracts, rerun the 9G-8F-6 evidence, and only then decide whether exactly one fresh-start short controlled training smoke may be authorized.

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F6_CHECKPOINT_TRAINING_READINESS_AND_COMMIT_REVIEW.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F6_READINESS_REVIEW_20260709.md
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```
