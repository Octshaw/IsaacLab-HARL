# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-0 completed a documentation-only checkpoint/loader/model-buffer readiness design audit.

Classification:

```text
DESIGN-READY
```

Phase 9G-8E-R is accepted as `PASS`.

Resolver-enabled training remains prohibited. Phase 9G-8F implementation may begin only after the 9G-8F-0 design is reviewed and accepted.

## Frozen 9G-8F Design

Official first lifecycle checkpoint target:

```text
HAPPO
EP shared state
three independent actors
feed-forward only
state_dict checkpoint files
```

Metadata contract:

```text
one ordered immutable assignment contract manifest
one SHA-256 over canonical UTF-8 JSON bytes
one checkpoint-local training-state/file-inventory manifest
one shared compatibility validator before every load
```

Compatibility categories:

```text
structural inspection
normal evaluation
explicit named ablation evaluation
validated weight continuation
```

Exact training resume is unsupported because current HARL does not save optimizer, counter, RNG, environment, resolver, or rollout-buffer state.

Unversioned checkpoints are supported only for explicit resolver-disabled legacy playback/evaluation after strict state-dict shape validation.

## Audit Findings

Five user-facing RL load entry points exist:

```text
training --dir
generic HARL play.py --dir
assignment play_assignment.py --dir
assignment playback diagnostics --dir
comparison-method assignment actor loader
```

They currently use one inherited HARL restore path and three duplicated actor-only loaders. No project-level contract validator exists.

Current HARL saves:

```text
actor weights
critic weights
ValueNorm state when enabled
```

It does not save:

```text
actor/critic optimizers
training episode/update count
best reward state
RNG state
environment/resolver state
rollout buffers
```

Installed HARL restore catches load failures and continues. Lifecycle loaders must bypass that behavior and hard-fail through the future shared validator.

Current effective actor and critic hidden sizes are both `[256,256]`; the YAML `hidden_sizes_critic` field is not consumed by the current project runner.

## Files Created

```text
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F0_READINESS_DESIGN_AUDIT_20260709.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

No Python, YAML, runtime configuration, installed HARL, or Conda file was modified in Phase 9G-8F-0.

## Validation

Documentation-only checks:

```text
git diff --check: PASS, line-ending warnings only
git status --short --untracked-files=all: expected uncommitted Phase 9G files plus new 9G-8F-0 docs
```

No checkpoint was loaded or saved. No forward/backward, optimizer step, training, playback, evaluation, or Isaac Sim/AppLauncher run occurred.

## Do Not Do

Do not run resolver-enabled training.

Do not load or save a checkpoint until the relevant Phase 9G-8F implementation phase explicitly permits temporary test artifacts.

Do not modify installed HARL or the Conda environment.

Do not commit unless explicitly requested.

## Next Step

After design acceptance:

```text
Phase 9G-8F-1:
Manifest / Canonical JSON / Fingerprint / Compatibility Core
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F0_READINESS_DESIGN_AUDIT_20260709.md
AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```
