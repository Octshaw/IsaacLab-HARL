# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8E-R is complete.

Classification:

```text
PASS
```

Phase 9G-8E lifecycle observation, shared observation, available-action mask, and PPO historical-mask replay integration is implemented and now closes as `PASS` for its official support matrix.

Resolver-enabled training remains prohibited pending Phase 9G-8F.

## Latest Completed Work

The remaining recurrent-generator blocker was closed by freezing:

```text
lifecycle_contract_c_v1:
  policy sequence mode: feed-forward only
  model.use_recurrent_policy: false
  model.use_naive_recurrent_policy: false
  actor-buffer generator: feed_forward_generator_actor
```

A shared project-local validator reads the fully resolved environment profile and HARL `model` flags without mutating them.

Guard timing:

```text
resolved Hydra/scenario config
-> lifecycle policy-sequence validator
-> runner construction
```

`AssignmentOnPolicyHARunner.__init__` repeats the same validator before environment, actor, buffer, restore, or training-loop construction.

Unsupported lifecycle chunked, naive, contradictory, missing, or non-boolean recurrent settings hard-fail. The guard is profile-specific; legacy recurrent policy support is unchanged.

`lifecycle_ablation` remains:

```text
resolver disabled
budget tracker/trigger disabled
lifecycle observation enabled
lifecycle Contract C mask disabled
normal training prohibited
```

## Installed HARL Boundary

Installed selection precedence for HAPPO, HAA2C, and HATRPO:

```text
use_recurrent_policy -> recurrent_generator_actor
else use_naive_recurrent_policy -> naive_recurrent_generator_actor
else -> feed_forward_generator_actor
```

The installed chunked generator still calls `_sa_cast(torch_tensor)`, which calls `tensor.transpose(1, 0, 2)` and is incompatible with the current PyTorch tensor buffer.

This is a documented, guarded, unsupported dependency branch. It is not a lifecycle observation, mask, resolver, or checkpoint defect.

The naive recurrent historical-mask boundary was tested successfully, but naive recurrent is intentionally outside `lifecycle_contract_c_v1`.

No installed HARL file or Conda package was modified.

## Key Files

Created in Phase 9G-8E-R:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_training_contract.py
scripts/environments/test_assignment_lifecycle_feed_forward_guard.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8E_R_RECURRENT_GUARDRAIL_20260709.md
```

Modified in Phase 9G-8E-R:

```text
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Earlier 9G-8A through 9G-8E changes remain uncommitted in the working tree.

## Latest Verification

```text
Python interpreter: C:\isaacenvs\isaac45_harl\python.exe
py_compile: PASS
Phase 9G-8C pure tests: PASS, 11/11
Phase 9G-8D observation integration tests: PASS, 6/6
Revised Phase 9G-8E mask/replay tests: PASS, 11/11
Phase 9G-8E-R guard tests: PASS, 9/9
git diff --check: PASS, line-ending warnings only
```

Feed-forward actor-buffer historical-mask replay and HAPPO `evaluate_actions` identity pass. Existing lightweight HAA2C/HATRPO identity checks also pass.

No Isaac Sim/AppLauncher smoke ran.

## Not Implemented

```text
checkpoint manifest persistence
canonical JSON / SHA-256 fingerprinting
checkpoint loader compatibility
actor/critic/buffer forward-backward readiness
checkpoint save/load validation
```

No resolver, Contract C, ownership, arbitration, budget trigger/release, retry, TTL, or infeasibility-release behavior changed.

## Do Not Do

Do not run resolver-enabled training.

Do not run a short training smoke, playback, evaluation, checkpoint loading, or Isaac Sim from this handoff.

Do not patch installed HARL or the Conda environment.

Do not commit unless explicitly asked.

## Next Step

The next possible phase is:

```text
Phase 9G-8F:
Checkpoint / Loader / Buffer / Forward-Backward Readiness
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8E_R_RECURRENT_GUARDRAIL_20260709.md
AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
AgentRead/20260708/PHASE9G8C_PURE_LIFECYCLE_SNAPSHOT_AND_TENSOR_BUILDERS_REPORT.md
AgentRead/20260708/PHASE9G8B_LIFECYCLE_OBSERVATION_MASK_CHECKPOINT_CONTRACT_REVISION_AND_FREEZE.md
```
