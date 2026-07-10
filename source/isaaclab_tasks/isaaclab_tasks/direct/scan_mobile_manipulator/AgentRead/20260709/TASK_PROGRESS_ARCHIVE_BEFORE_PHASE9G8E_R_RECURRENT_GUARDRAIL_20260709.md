# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8E is implemented but not fully accepted.

Classification:

```text
PASS WITH REQUIRED FIXES
```

Phase 9G-8D was accepted with the `lifecycle_ablation` budget-tracker clarification resolved by Option A.

Phase 9G-8E integrated lifecycle-aware available-actions and verified most PPO/HARL historical-mask replay boundaries, but the installed HARL recurrent actor-buffer generator fails before yielding masks.

Resolver-enabled training remains prohibited.

## Latest Completed Work

`lifecycle_ablation` now explicitly resolves to:

```text
resolver disabled
budget tracker / trigger disabled
lifecycle observation enabled
lifecycle Contract C mask disabled
snapshot-derived physical/noop available-actions
```

Invalid `lifecycle_ablation` combinations hard-fail when they enable:

```text
assignment_cooldown_enabled
assignment_redirect_guardrail_enabled
assignment_failed_pair_memory_enabled
```

`lifecycle_contract_c` now uses the lifecycle mask:

```text
idle targets require valid/available/feasible/uncovered
not teammate-owned
not self failed/released
noop always available
```

Executing robot mask:

```text
current active target + noop only
```

Actor observations, shared observations, and lifecycle available-actions use one snapshot generation in lifecycle modes:

```text
actor_generation
==
shared_generation
==
available_actions_generation
==
lifecycle_snapshot_generation
```

Legacy mask behavior remains unchanged. The default legacy no-overlay path is exact against `make_assignment_action_mask(...)`, and an explicit legacy cooldown overlay still masks through the old path.

No installed HARL package was modified.

## Blocking Issue

The installed HARL recurrent actor-buffer generator fails with PyTorch tensors:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py
  recurrent_generator_actor(...)
    -> harl.utils.trans_tools._sa_cast(self.obs[:-1])

C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\utils\trans_tools.py
  _sa_cast(value)
    -> value.transpose(1, 0, 2)
```

Observed error:

```text
TypeError: transpose() received an invalid combination of arguments - got (int, int, int)
```

Feed-forward and naive recurrent historical-mask replay pass. `HAPPO`, `HAA2C`, and `HATRPO` update-path spies verify `evaluate_actions` receives the generated historical mask batch.

Phase 9G-8E cannot become `PASS` until the recurrent generator path is fixed or formally excluded from supported lifecycle training profiles.

## Key Files

Created:

```text
scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8E_MASK_REPLAY_INTEGRATION_20260708.md
```

Modified in Phase 9G-8E:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_lifecycle_observation_integration.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Previously modified by Phase 9G-8D and still part of the working tree:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

## Latest Verification

Passed:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py scripts/environments/test_assignment_lifecycle_observation_pure.py scripts/environments/test_assignment_lifecycle_observation_integration.py scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_pure.py --json

conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_integration.py --json

git diff --check
```

Failed as expected due the installed HARL recurrent-generator blocker:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py --json
```

Result summary:

```text
9 / 10 Phase 9G-8E cases passed
failed: test_harl_actor_buffer_generators_replay_historical_masks
failing subpath: recurrent_generator_actor
```

No Isaac Sim/AppLauncher runtime smoke was run.

No training, short training smoke, playback, evaluation, checkpoint loading, video recording, or commit occurred.

## Not Implemented

Checkpoint manifest persistence, SHA-256 fingerprinting, and checkpoint compatibility loaders are not implemented.

Forward/backward readiness and checkpoint save/load validation are not implemented.

No resolver behavior, Contract C behavior, ownership semantics, arbitration semantics, budget trigger/release behavior, retry, TTL, or active-target infeasibility-release behavior changed.

## Do Not Do

Do not run resolver-enabled training.

Do not run short training smoke, playback, evaluation, or Isaac Sim from this handoff.

Do not load an RL checkpoint.

Do not commit unless explicitly asked.

Do not modify installed HARL package files without an explicit follow-up decision.

## Next Step

The next possible phase title is:

```text
Phase 9G-8F:
Checkpoint / Loader / Buffer / Forward-Backward Readiness
```

Before resolver-enabled training can become legal, resolve or formally exclude the installed HARL recurrent generator historical-mask replay blocker.

## Detailed Reports / Archives

Phase 9G-8E report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
```

Phase 9G-8E TASK_PROGRESS archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8E_MASK_REPLAY_INTEGRATION_20260708.md
```

Phase 9G-8D report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8D_LIFECYCLE_ACTOR_SHARED_OBSERVATION_INTEGRATION_REPORT.md
```
