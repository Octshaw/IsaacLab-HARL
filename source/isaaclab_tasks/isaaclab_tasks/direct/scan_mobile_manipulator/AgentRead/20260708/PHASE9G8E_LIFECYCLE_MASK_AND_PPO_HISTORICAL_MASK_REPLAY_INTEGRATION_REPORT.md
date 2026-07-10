# Phase 9G-8E Lifecycle Mask And PPO Historical-Mask Replay Integration Report

Date: 2026-07-08

## Classification

```text
PASS
```

Lifecycle-aware available-action mask integration is implemented and passes the project-local lifecycle mask, wrapper generation, profile validation, legacy non-regression, feed-forward/naive HARL buffer replay, and actor `evaluate_actions` historical-mask checks.

Phase 9G-8E-R formally closes the prior recurrent-generator blocker by freezing `lifecycle_contract_c_v1` as feed-forward only. All officially supported observation, shared-observation, mask, feed-forward actor-buffer replay, and `evaluate_actions` paths pass. Project-local startup guards prevent lifecycle recurrent configurations from reaching runner, environment, actor, buffer, restore, or training-loop construction.

Known, guarded, unsupported installed-HARL incompatibility:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py
  recurrent_generator_actor(...)
    -> harl.utils.trans_tools._sa_cast(self.obs[:-1])

C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\utils\trans_tools.py
  _sa_cast(value)
    -> value.transpose(1, 0, 2)
```

For the current PyTorch tensor buffer, `Tensor.transpose(1, 0, 2)` raises:

```text
TypeError: transpose() received an invalid combination of arguments - got (int, int, int)
```

No installed HARL package file was modified.

Naive recurrent historical-mask replay remains tested at the historical-mask boundary, but both naive and chunked recurrent modes are outside the official `lifecycle_contract_c_v1` support matrix.

## Files Created / Modified

Created:

```text
scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8E_LIFECYCLE_MASK_AND_PPO_HISTORICAL_MASK_REPLAY_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8E_MASK_REPLAY_INTEGRATION_20260708.md
```

Modified:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_lifecycle_observation_integration.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Existing Phase 9G-8D modified files remain modified in the working tree:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

Inspected but not modified:

```text
assignment_lifecycle_resolver.py
assignment_lifecycle_resolver_runtime.py
assignment_rl_interface.py
assignment_state.py
```

Installed HARL files inspected but not modified:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_base_runner.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\actors\on_policy_base.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\actors\happo.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\actors\hatrpo.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\actors\haa2c.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\policy_models\stochastic_policy.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\act.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\distributions.py
```

## Lifecycle Ablation Correction

`lifecycle_ablation` is now frozen as:

```text
resolver: disabled
budget-release contract: disabled
lifecycle observation: enabled
lifecycle-aware Contract C mask: disabled
legacy guardrail profile: lifecycle_no_legacy_guardrails_v1
available-actions: snapshot-derived physical/noop mask
```

Startup validation hard-fails if `lifecycle_ablation` enables behavior-producing guardrails:

```text
assignment_cooldown_enabled=True
assignment_redirect_guardrail_enabled=True
assignment_failed_pair_memory_enabled=True
```

The valid profile keeps:

```text
active_target_id = -1
task_owner_robot_id = -1
pair_state = PAIR_NONE
budget_attempt_target = -1
budget_attempt_steps = 0
budget_attempt_budget_steps = 0
critic budget block = 0
```

Repeated synthetic diagnostic updates under valid `lifecycle_ablation` keep budget state inactive and actor/critic lifecycle outputs zero.

## Profile Startup Validation

`lifecycle_contract_c` now requires:

```text
assignment_cooldown_enabled=True
assignment_cooldown_trigger_mode in {"budget", "budget_and_streak"}
assignment_cooldown_duration_steps > 0
assignment_cooldown_apply_to_action_mask=False
assignment_redirect_guardrail_enabled=False
assignment_failed_pair_memory_enabled=False
```

This keeps the budget tracker/trigger as the only budget-release source and prevents simultaneous legacy guardrail ownership.

Training remains blocked for `lifecycle_contract_c` with the updated reason:

```text
checkpoint manifest/fingerprint, loader compatibility, forward/backward readiness,
and save/load validation are not yet ready
```

## Mask Builder Location

Implemented in:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py
```

New result and builders:

```text
LifecycleAvailableActionsResult
build_lifecycle_ablation_available_action_tensors(snapshot)
build_lifecycle_contract_c_available_action_tensors(snapshot)
```

Mask contract names:

```text
lifecycle_ablation_physical_mask_v1
lifecycle_contract_c_mask_v1
```

## Mask Tensor Contract

Shape:

```text
[E,M,N+1]
```

Dtype:

```text
torch.float32
```

Raw target ids:

```text
0 ... N-1
```

Raw noop id:

```text
N
```

Decoded noop remains:

```text
-1
```

The result carries `snapshot_generation` as diagnostics metadata only. The generation value is not part of the network input.

## Idle Mask Semantics

For `lifecycle_contract_c`, an idle robot target `j` is available only when:

```text
task_valid[e,j]
and available_mask[e,r,j]
and feasible_mask[e,r,j]
and not viewpoints_covered[e,j]
and not task_owned_by_teammate[e,r,j]
and not self_pair_failed_or_released[e,r,j]
```

Tests cover invalid task slots, unavailable targets, infeasible targets, covered targets, teammate-owned targets, failed pairs, and released pairs.

## Executing Mask Semantics

For active target `k`:

```text
target k = 1
noop = 1
all j != k = 0
```

The current active target remains available even if the current physical availability or feasibility becomes false. No active-target infeasibility release was added.

Snapshot validation now rejects stale covered-active states before mask construction:

```text
active target invariant failed: active targets must not already be covered
```

## Noop Semantics

Noop is always available for idle and executing robots.

All-zero action rows are rejected as implementation errors.

## Ownership / Failed-Pair Masking

For idle robots:

```text
teammate-owned target -> 0
PAIR_FAILED_BUDGET -> 0
PAIR_RELEASED_BUDGET -> 0
```

For the executing owner:

```text
current active target remains 1
```

Unrelated robot-target failed/released pairs do not mask other robots.

## Simultaneous Claims

The same unowned target may remain available for multiple idle robots before sampling.

The mask does not preselect a winner. Arbitration remains resolver-side:

```text
lowest selected path cost
then robot-id tie-break
```

## Resolver Final Boundary

Resolver checks were not removed or weakened.

Project-local tests compare lifecycle mask rejection against resolver rejection reasons for:

```text
unavailable target
covered target
teammate-owned target
same-robot released pair
executing switch
```

The resolver remains the final safety boundary for stale masks, external callers, simultaneous claims, invalid ids, and bypassed policy support.

## Wrapper Integration

`AssignmentHarlWrapper._build_available_actions()` now branches by profile:

```text
legacy:
  existing legacy mask path unchanged

lifecycle_ablation:
  build_lifecycle_ablation_available_action_tensors(snapshot)

lifecycle_contract_c:
  build_lifecycle_contract_c_available_action_tensors(snapshot)

diagnostics_hidden_state:
  existing legacy/diagnostic mask path
```

For lifecycle modes, actor observations, shared observations, and available-actions consume the same captured lifecycle decision snapshot.

Verified equality:

```text
actor_generation
==
shared_generation
==
available_actions_generation
==
lifecycle_snapshot_generation
```

## Legacy Mask Non-Regression

Default legacy masks remain exact for configurations without legacy overlays:

```text
legacy available_actions == make_assignment_action_mask(problem, include_noop=True)
```

An explicit lightweight legacy cooldown-overlay configuration was also tested to ensure the old overlay path was not bypassed:

```text
assignment_cooldown_enabled=True
assignment_cooldown_apply_to_action_mask=True
```

The configured cooldown target is still masked and noop remains available.

## In-Memory Manifest Update

The wrapper manifest now includes:

```text
mask_contract_version
available_actions_shape
available_actions_dtype
noop_always_available
resolver_final_safety_boundary
historical_mask_replay_contract
budget_release_contract
legacy_guardrail_profile
```

No checkpoint manifest file, SHA-256 fingerprint, or checkpoint compatibility loader was implemented.

## HARL Actor-Buffer Static Audit

Actual installed path:

```text
OnPolicyBaseRunner.warmup()
  env.reset() -> available_actions
  actor_buffer[agent_id].available_actions[0] = available_actions[:, agent_id].clone()

OnPolicyBaseRunner.collect(step)
  actor.get_actions(..., actor_buffer[agent_id].available_actions[step])

OnPolicyBaseRunner.insert(data)
  actor_buffer[agent_id].insert(..., available_actions[:, agent_id])

OnPolicyActorBuffer.insert(...)
  self.available_actions[self.step + 1] = available_actions.clone()
```

Sampling alignment:

```text
obs[t]
available_actions[t]
action[t]
action_log_prob[t]
```

Next-state insertion:

```text
next_obs[t+1]
next_available_actions[t+1]
```

Generator alignment intended by installed HARL:

```text
self.available_actions[:-1]
```

No historical mask regeneration from current resolver state was found.

## Feed-Forward / Recurrent Generator Audit

Feed-forward generator:

```text
feed_forward_generator_actor(...)
available_actions = self.available_actions[:-1].reshape(...)
available_actions_batch = available_actions[indices]
```

Result:

```text
passed
```

Naive recurrent generator:

```text
naive_recurrent_generator_actor(...)
available_actions_batch = _flatten(T, N, self.available_actions[:-1, ids])
```

Result:

```text
passed
```

Recurrent generator:

```text
recurrent_generator_actor(...)
available_actions = _sa_cast(self.available_actions[:-1])
```

Result:

```text
failed before mask replay could be verified
```

Failure:

```text
harl.utils.trans_tools._sa_cast(...)
  value.transpose(1, 0, 2)

TypeError for torch.Tensor
```

This remains a documented installed-dependency incompatibility outside the supported feed-forward lifecycle path. It is not a lifecycle observation, mask, resolver, or checkpoint defect.

## Evaluate-Actions Historical-Mask Evidence

Project-local spies verified the actor update path passes the generated historical mask batch to `evaluate_actions` for:

```text
HAPPO.update(...)
HAA2C.update(...)
HATRPO.update(...)
```

The spy receives the exact `available_actions_batch` yielded by the actor-buffer generator and verifies sample-id alignment.

Model path inspection confirms:

```text
OnPolicyBase.evaluate_actions(...)
  -> StochasticPolicy.evaluate_actions(..., available_actions)
  -> ACTLayer.evaluate_actions(..., available_actions)
  -> Categorical.forward(..., available_actions)
```

`Categorical.forward` applies the mask by setting unavailable logits to `-1e10`.

## Tests And Results

Syntax:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_observation.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py scripts/environments/test_assignment_lifecycle_observation_pure.py scripts/environments/test_assignment_lifecycle_observation_integration.py scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
```

Result:

```text
passed
```

Previous tests:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_pure.py --json
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_integration.py --json
```

Results:

```text
Phase 9G-8C pure tests: passed, 11 cases
Phase 9G-8D integration tests: passed, 6 cases
```

Original pre-closure Phase 9G-8E test:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py --json
```

Historical result before the Phase 9G-8E-R support freeze:

```text
failed: 1 / 10 cases
```

Passed cases:

```text
lifecycle idle mask semantics
lifecycle executing mask semantics
failed/released-pair masking
noop/nonzero rows and covered-active invariant
ablation physical/noop snapshot mask
mask/resolver deterministic rejection agreement
lifecycle_ablation budget-disabled validation and repeated updates
contract_c generation equality and legacy guardrail non-regression
HAPPO/HAA2C/HATRPO evaluate_actions receives historical masks
```

Failed case:

```text
test_harl_actor_buffer_generators_replay_historical_masks
```

Failing subpath:

```text
recurrent_generator_actor
```

Feed-forward and naive recurrent subpaths pass before the recurrent-generator failure.

Whitespace:

```powershell
git diff --check
```

Result:

```text
passed
```

Git emitted CRLF conversion warnings only.

## Runtime Smoke Details

No Isaac Sim/AppLauncher smoke was run.

No policy checkpoint was loaded.

No training, short training smoke, playback, evaluation, video recording, or performance comparison was run.

## Known Limitations / Closure

Resolver-enabled training remains prohibited.

Phase 9G-8E-R formally excludes recurrent policies from `lifecycle_contract_c_v1`, enforces that exclusion before runner construction, and closes Phase 9G-8E as `PASS` for its official feed-forward support matrix. The installed chunked recurrent incompatibility remains documented and unsupported.

Checkpoint manifest persistence, SHA-256 fingerprinting, loader compatibility checks, forward/backward readiness, and checkpoint save/load validation remain unimplemented.

No compact shared Option B was implemented.

No retry, TTL, active-target infeasibility release, abort/switch/release action, explicit continue action, resolver behavior change, Contract C change, ownership change, arbitration change, or budget trigger/release behavior change was implemented.

## Training Prohibition

`lifecycle_contract_c` remains blocked for normal training.

The next possible phase remains:

```text
Phase 9G-8F:
Checkpoint / Loader / Buffer / Forward-Backward Readiness
```

The recurrent branch is now explicitly ruled out for lifecycle contract version 1. Resolver-enabled training remains prohibited for the independent Phase 9G-8F checkpoint, loader, forward/backward, and save/load readiness work.
