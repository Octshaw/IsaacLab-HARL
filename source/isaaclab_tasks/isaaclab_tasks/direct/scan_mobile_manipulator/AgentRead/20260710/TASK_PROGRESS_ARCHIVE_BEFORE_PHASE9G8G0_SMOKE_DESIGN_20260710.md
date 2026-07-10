# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-6R narrowly activated the reviewed `lifecycle_contract_c` training gate and closed the readiness review.

Technical classification:

```text
CONTROLLED-TRAINING-SMOKE-READY
```

Commit classification:

```text
COMMIT-READY
```

The reviewed Phase 9G-8 work should be committed before running the first controlled smoke.

## Active Training Boundary

`lifecycle_contract_c` is now training-allowed only under the existing official support guards:

```text
HAPPO
EP
feed-forward
share_param=false
state_dict checkpoint
save_entire_model=false
M=3,N=50 current official scale
```

Evaluation-only `lifecycle_ablation` and diagnostics profiles remain training-prohibited.

General or long resolver-enabled training remains prohibited until the first controlled smoke is reviewed.

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

Existing total: PASS, 114/114
```

New Phase 9G-8F-6R gate tests:

```text
controlled lifecycle gate: PASS, 10/10

Combined total: PASS, 124/124
```

Additional checks:

```text
py_compile changed/new Python files: PASS
direct assignment load/save scan: PASS
git diff --check: PASS with LF-to-CRLF warnings only
```

No real assignment environment, Isaac Sim, AppLauncher, training, playback, evaluation, checkpoint development experiment, real checkpoint load, installed HARL modification, Conda modification, or commit occurred.

## Files Changed By Latest Phase

Created:

```text
scripts/environments/test_assignment_lifecycle_controlled_training_gate.py
AgentRead/20260710/PHASE9G8F6R_CONTROLLED_TRAINING_GATE_ACTIVATION_AND_REVIEW_CLOSURE.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F6R_GATE_ACTIVATION_20260710.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_training_contract.py
scripts/reinforcement_learning/harl/train.py
AgentRead/TASK_PROGRESS.md
```

No resolver behavior, Contract C semantics, observation/shared/action ordering, checkpoint schema/save/load behavior, reward/controller behavior, installed HARL files, Conda files, or YAML defaults changed.

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

## Controlled Smoke Boundary

Exactly one future controlled smoke is authorized after commit:

```text
fresh start
no --dir
new unique experiment directory
lifecycle_contract_c explicitly selected
HAPPO
EP
feed-forward
share_param=false
state_dict-only
save_entire_model=false
M=3,N=50
minimal practical num_envs
short bounded runtime integration validation only
```

The smoke is not a long training run, convergence experiment, performance comparison, or final experiment.

## Remaining Unsupported

```text
general/long lifecycle training
exact training resume
fine-tuning with changed contract
lifecycle recurrent
FP lifecycle critic
share_param=true lifecycle
HATRPO lifecycle
HAA2C lifecycle
unversioned legacy continuation
```

## Do Not Do

Do not run the controlled smoke before committing the reviewed code.

Do not run long/general resolver-enabled training until the controlled smoke is reviewed.

Do not describe validated weight continuation as exact resume.

Do not modify installed HARL or the Conda environment.

Do not run playback/evaluation as part of the smoke authorization step.

## Next Step

Commit the reviewed Phase 9G-8 work.

Recommended commit message:

```text
feat(assignment): complete lifecycle training checkpoint readiness

- integrate lifecycle actor/shared observations and Contract C masks
- enforce feed-forward-only lifecycle training support
- activate the reviewed lifecycle_contract_c controlled-training gate
- add immutable checkpoint manifests and SHA-256 fingerprints
- add atomic native assignment checkpoint saving
- add strict purpose-aware checkpoint loading
- validate real HARL actor/critic/buffer update paths
- validate end-to-end weight continuation and re-save
- preserve legacy and evaluation-only profile isolation
```

After commit, the next phase may run exactly one fresh-start short bounded controlled training smoke under the boundary above.

## Detailed Reports / Archives

```text
AgentRead/20260710/PHASE9G8F6R_CONTROLLED_TRAINING_GATE_ACTIVATION_AND_REVIEW_CLOSURE.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F6R_GATE_ACTIVATION_20260710.md
AgentRead/20260709/PHASE9G8F6_CHECKPOINT_TRAINING_READINESS_AND_COMMIT_REVIEW.md
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
