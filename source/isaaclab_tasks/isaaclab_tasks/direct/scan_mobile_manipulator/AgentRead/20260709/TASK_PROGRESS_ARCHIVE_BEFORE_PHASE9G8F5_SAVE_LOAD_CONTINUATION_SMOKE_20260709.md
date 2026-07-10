# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-4 completed actor / critic / buffer forward-backward readiness.

Classification:

```text
PASS
```

Accepted prerequisites:

```text
Phase 9G-8F-1: PASS
Phase 9G-8F-2: PASS
Phase 9G-8F-3: PASS
```

Resolver-enabled training remains prohibited.

## Latest Completed Phase

Synthetic CPU validation exercised the real installed HARL:

```text
3 independent HAPPO actors
1 centralized VCritic
3 OnPolicyActorBuffer instances
1 OnPolicyCriticBufferEP
1 ValueNorm
feed_forward_generator_actor
feed_forward_generator_critic
HAPPO.update
VCritic.update
Adam optimizer steps
```

No simplified project-local actor or critic loss was used.

## Readiness Results

Official lifecycle dimensions:

```text
actor: 1059
shared: 3183
action: 51
raw noop: 50
```

Legacy dimensions:

```text
actor: 909
shared: 2727
action: 51
raw noop: 50
```

Both profiles passed:

```text
actor forward and masked categorical behavior
critic forward
actor-buffer insertion/indexing/after_update
EP critic-buffer insertion/returns/after_update
actor historical-mask minibatch alignment
critic minibatch alignment
actor loss/backward/finite gradients/optimizer step
critic loss/backward/finite gradients/optimizer step
finite parameter changes
independent actor update isolation
ValueNorm update
```

Effective actor and critic hidden sizes remain `[256,256]`.

## Files

Created:

```text
scripts/environments/test_assignment_actor_critic_buffer_forward_backward_readiness.py
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F4_FORWARD_BACKWARD_READINESS_20260709.md
```

Modified:

```text
AgentRead/TASK_PROGRESS.md
```

No runtime Python source, installed HARL, Conda, YAML, model architecture, observation/mask contract, resolver, reward, checkpoint save/load, or environment behavior was modified.

## Validation

```text
Python: C:\isaacenvs\isaac45_harl\python.exe
PyTorch: 2.5.1+cu121
Device: CPU

Phase 9G-8F-4 readiness: PASS, 15/15
Phase 9G-8F-1 core: PASS, 27/27
Phase 9G-8F-2 save: PASS, 15/15
Phase 9G-8F-3 loader: PASS, 15/15
Phase 9G-8E mask/HARL replay: PASS, 11/11
Phase 9G-8E-R guard: PASS, 9/9

Total: PASS, 92/92
py_compile: PASS
git diff --check: PASS
```

No checkpoint was saved or loaded.

No assignment environment, AppLauncher, Isaac Sim, environment rollout, training loop, playback, or evaluation ran.

## Known Boundaries

Checkpoint output-equivalence and validated post-load continuation smoke remain unimplemented.

Lifecycle recurrent, FP critic, `share_param=true`, HATRPO, and HAA2C are outside the official first support matrix.

Exact resume and fine-tuning remain unsupported.

Resolver-enabled training remains prohibited pending the remaining Phase 9G-8F save/load continuation smoke and readiness review.

## Do Not Do

Do not run resolver-enabled training.

Do not claim checkpoint output equivalence or post-load continuation from Phase 9G-8F-4.

Do not claim exact resume or fine-tuning support.

Do not modify installed HARL or the Conda environment.

Do not commit unless explicitly requested.

## Next Step

```text
Phase 9G-8F-5:
Checkpoint Save / Load / Continuation Smoke
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F4_FORWARD_BACKWARD_READINESS_20260709.md
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F3_ALL_LOADER_INTEGRATION_20260709.md
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
```
