# Phase 9G-8F-6: Checkpoint / Training Readiness and Commit Review

Date: 2026-07-09

## 1. Executive Classifications

Technical readiness:

```text
READY WITH REQUIRED FIXES
```

Commit readiness:

```text
NOT COMMIT-READY
```

Rationale:

The Phase 9G-8F checkpoint, loader, model, buffer, historical-mask, and validated-weight-continuation evidence is strong and the accepted regression suites reran successfully at `114/114`. However, the current source still blocks `lifecycle_contract_c` training at the wrapper profile boundary:

```text
assignment_harl_wrapper.py:
  lifecycle_contract_c.training_allowed = False
  training_blocked_reason = ASSIGNMENT_LIFECYCLE_MASK_PENDING_ERROR

assignment_harl_training.py:
  AssignmentIsaacLabEnv raises RuntimeError when training_allowed is false.
```

Therefore one future controlled resolver-enabled short training smoke cannot be authorized without a source change. This review phase is read-only, so the required correction is deferred.

Required corrective phase:

```text
Phase 9G-8F-6R:
Controlled Training Gate Activation and Review Closure
```

That phase should narrowly update the stale training gate/message, preserve all frozen contracts, and rerun this review's required evidence before any smoke is attempted.

## 2. Reviewed Phase And File Scope

Reviewed accepted reports:

| phase | reported status | review result |
| --- | --- | --- |
| 9G-8B | CONTRACT-FREEZE READY | Consistent with implemented schema/mask/checkpoint direction |
| 9G-8C | PASS | Pure snapshot/tensor layer remains intact |
| 9G-8D | PASS | Actor/shared lifecycle integration remains intact |
| 9G-8E | PASS | Lifecycle mask and historical-mask replay remain intact |
| 9G-8E-R | PASS | Feed-forward-only lifecycle support guard remains intact |
| 9G-8F-0 | DESIGN-READY | Split checkpoint plan was followed |
| 9G-8F-1 | PASS | Contract/fingerprint core passes |
| 9G-8F-2 | PASS | Save metadata/coordinator passes |
| 9G-8F-3 | PASS | Shared loader and entry-point coverage passes |
| 9G-8F-4 | PASS | Real HARL forward/backward readiness passes |
| 9G-8F-5 | PASS | Save/load/continuation smoke passes |

Changed implementation files inspected:

| file | status | phase introduced | expected in eventual commit? | reason |
| --- | --- | --- | --- | --- |
| `assignment_lifecycle_observation.py` | new | 9G-8C/8E | Yes after fix | Snapshot, actor lifecycle tensors, critic budget tensors, lifecycle masks |
| `assignment_lifecycle_training_contract.py` | new | 9G-8E-R | Yes after fix | Feed-forward-only sequence guard |
| `assignment_checkpoint_contract.py` | new | 9G-8F-1 | Yes after fix | Manifest, canonical JSON, fingerprint, compatibility core |
| `assignment_checkpoint_save.py` | new | 9G-8F-2 | Yes after fix | Atomic native save coordinator and runtime capture |
| `assignment_checkpoint_load.py` | new | 9G-8F-3 | Yes after fix | Shared strict assignment checkpoint loader |
| `assignment_harl_wrapper.py` | modified | 9G-8D/8E/8F | Yes after fix | Lifecycle profile/schema/mask integration; contains current blocking training gate |
| `assignment_harl_training.py` | modified | 9G-8E-R/8F | Yes after fix | Feed-forward guard, save/load routing, continuation acknowledgement |
| `scenario_config.py` | modified | 9G-8D/8E | Yes after fix | Profile/config parsing |
| `scan_mobile_manipulator_env.py` | modified | 9G-8D/8E | Yes after fix | Config/profile exposure |
| `train.py` | modified | 9G-8E-R/8F | Yes after fix | Early sequence validation and continuation acknowledgement plumbing |
| `play.py` | modified | 9G-8F-3 | Yes after fix | Assignment hard-reject before unvalidated generic restore |
| `play_assignment.py` | modified | 9G-8F-3 | Yes after fix | Shared loader evaluation path |
| `evaluate_assignment_rl_playback_diagnostics.py` | modified | 9G-8F-3 | Yes after fix | Shared loader diagnostics path |
| `evaluate_assignment_methods.py` | modified | 9G-8F-3 | Yes after fix | Unsupported assignment-RL comparison hard reject |

New test files inspected:

| file | status | phase introduced | expected in eventual commit? | reason |
| --- | --- | --- | --- | --- |
| `test_assignment_lifecycle_observation_pure.py` | new | 9G-8C | Yes after fix | Pure snapshot/tensor tests |
| `test_assignment_lifecycle_observation_integration.py` | new | 9G-8D | Yes after fix | Actor/shared integration tests |
| `test_assignment_lifecycle_mask_and_harl_replay.py` | new | 9G-8E | Yes after fix | Mask and historical replay tests |
| `test_assignment_lifecycle_feed_forward_guard.py` | new | 9G-8E-R | Yes after fix | Feed-forward guard tests |
| `test_assignment_checkpoint_contract_core.py` | new | 9G-8F-1 | Yes after fix | Contract core tests |
| `test_assignment_checkpoint_save_metadata_integration.py` | new | 9G-8F-2 | Yes after fix | Save metadata tests |
| `test_assignment_checkpoint_all_loader_integration.py` | new | 9G-8F-3 | Yes after fix | Shared loader and entry-point tests |
| `test_assignment_actor_critic_buffer_forward_backward_readiness.py` | new | 9G-8F-4 | Yes after fix | Real HARL model/buffer/update tests |
| `test_assignment_checkpoint_save_load_continuation_smoke.py` | new | 9G-8F-5 | Yes after fix | End-to-end checkpoint continuation smoke |

Reports and archives:

| file group | status | phase introduced | expected in eventual commit? | reason |
| --- | --- | --- | --- | --- |
| `AgentRead/20260708/PHASE9G8A...` through `PHASE9G8E...` | new | 9G-8A to 9G-8E | Yes after fix | Historical design and integration reports |
| `AgentRead/20260709/PHASE9G8E_R...` through `PHASE9G8F5...` | new | 9G-8E-R to 9G-8F-5 | Yes after fix | Historical support and checkpoint reports |
| `AgentRead/20260709/PHASE9G8F6...` | new | 9G-8F-6 | Yes after fix | This review |
| `AgentRead/20260708/TASK_PROGRESS_ARCHIVE...` and `AgentRead/20260709/TASK_PROGRESS_ARCHIVE...` | new | 9G-8A to 9G-8F-6 | Yes after fix | Required progress archives |
| `AgentRead/TASK_PROGRESS.md` | modified | rolling handoff | Yes after fix | Current concise handoff |

Generated artifact audit:

`git status --short --untracked-files=all` does not place `models/`, `best_model/`, `results/`, `logs/`, `videos/`, TensorBoard events, checkpoint artifacts, temporary JSON, `.pyc`, or `__pycache__/` files in the commit scope. Ignored historical `results/`, `logs/`, and `__pycache__/` entries exist in the working tree and must remain excluded.

## 3. Frozen Lifecycle Support Contract

The official first lifecycle target remains:

| field | reviewed value |
| --- | --- |
| profile | `lifecycle_contract_c` |
| algorithm | `HAPPO` |
| HARL state type | `EP` |
| actor count | `3` |
| actor sharing | `false` |
| policy sequence | feed-forward |
| `use_recurrent_policy` | `false` |
| `use_naive_recurrent_policy` | `false` |
| actor dimension | `1059` for `M=3,N=50` |
| shared dimension | `3183` for `M=3,N=50` |
| action dimension | `51` |
| raw noop | `50` |
| decoded noop | `-1` |
| actor hidden sizes | `[256,256]` |
| effective critic hidden sizes | `[256,256]` |
| ValueNorm | enabled |
| checkpoint serialization | `state_dict` only |

The raw configured `hidden_sizes_critic=[512,256]` is documented as unused by the effective VCritic model path. Phase 9G-8F-4 checks the effective critic structure rather than treating that raw field as the live architecture.

Blocking inconsistency:

All structural contracts agree, but the wrapper profile still reports `training_allowed=False` for `lifecycle_contract_c`. That prevents the controlled-smoke authorization requested by this review.

## 4. Observation / Shared / Mask / Snapshot Consistency

Review result:

```text
PASS for implemented runtime contracts
```

Confirmed contracts:

| contract | result |
| --- | --- |
| Actor lifecycle fields | `self_active_target`, `task_owned_by_teammate`, `self_pair_failed_or_released` |
| Actor row placement | lifecycle fields appended inside each task row |
| Actor dimension formula | `100 + 3M + 19N` |
| Shared Option A | concatenated lifecycle actor observations plus `2M` critic budget block |
| Shared dimension formula | `M * (100 + 3M + 19N) + 2M` |
| Snapshot generation | actor/shared/mask builders use snapshot generation metadata |
| PPO historical masks | sampled masks are stored and replayed from actor buffer |
| Contract C executing mask | current active target plus noop |
| Contract C idle mask | valid, available, feasible, uncovered, not teammate-owned, not own failed/released, plus noop |
| Legacy isolation | legacy profile keeps old schema/mask path |

No reviewed checkpoint changes modify resolver ownership, arbitration, release semantics, reward, controller behavior, or observation ordering.

## 5. Sequence And HARL Support Matrix

Supported first official profile:

```text
HAPPO + EP + feed-forward + 3 independent actors + state_dict checkpoint
```

Unsupported in lifecycle version 1:

```text
chunked recurrent lifecycle
naive recurrent lifecycle
FP critic lifecycle
share_param=true lifecycle
HATRPO lifecycle
HAA2C lifecycle
```

The project-local feed-forward guard is present in:

```text
assignment_lifecycle_training_contract.py
train.py before runner construction
AssignmentOnPolicyHARunner.__init__ before normal runner setup
```

The installed HARL branch mapping remains:

| resolved mode | flags | selected actor generator | lifecycle v1 support |
| --- | --- | --- | --- |
| Feed-forward | both recurrent flags false | `feed_forward_generator_actor` | Supported |
| Naive recurrent | `use_naive_recurrent_policy=true` | `naive_recurrent_generator_actor` | Unsupported official profile |
| Chunked recurrent | `use_recurrent_policy=true` | `recurrent_generator_actor` | Unsupported; installed dependency incompatibility documented |

No report or code path reviewed makes naive recurrent an official lifecycle training mode.

## 6. Checkpoint Contract Review

Review result:

```text
PASS
```

Confirmed:

| item | result |
| --- | --- |
| Manifest | one ordered immutable project contract manifest |
| Canonical JSON | UTF-8 canonical JSON with preserved ordered lists |
| Fingerprint | complete SHA-256 integrity fingerprint |
| Compatibility | purpose-aware, not fingerprint-only |
| File inventory | checkpoint-local file inventory with size/SHA-256 |
| Tensor inventory | exact key/shape/dtype inventory |
| Normal evaluation | ignores training-only differences while enforcing inference semantics |
| Validated continuation | requires complete training contract and acknowledgement |
| Fine-tuning | deferred / unsupported |
| Exact resume | explicitly unsupported |

## 7. Save Architecture Review

Review result:

```text
PASS
```

Supported native assignment save paths route through `AssignmentCheckpointSaveCoordinator`:

```text
regular models/
best_model/
episode snapshot
explicit final save
```

Confirmed save properties:

| property | result |
| --- | --- |
| Same-directory temporary artifact | yes |
| Flush/fsync where supported | yes |
| Atomic replacement | `os.replace` |
| Directory fsync | yes, best effort |
| File size/SHA-256 | recorded |
| Tensor inventory | recorded |
| Run-root contract | written and compared |
| Checkpoint-local contract | written and compared |
| Completion marker | training-state manifest written last |
| Failed save | no completion marker |
| Generation advance | after successful save only |
| Critic and ValueNorm | saved once |
| Lifecycle full-model pickle | rejected |

## 8. Loader Architecture Review

Review result:

```text
PASS
```

The shared loader owns:

```text
metadata discovery
completion-marker enforcement
manifest/fingerprint validation
purpose compatibility
file size/SHA-256 checks
CPU weights_only deserialization
tensor inventory comparison
strict live loading
rollback on unexpected mutation failure
```

All required artifacts are inspected before the first live model mutation. Live loads use:

```text
module.load_state_dict(state_dict, strict=True)
```

No assignment load path uses `strict=False`, full-model pickle loading, prefix rewriting, padding/truncation, silent dtype casting, or exception swallowing followed by random weights.

## 9. Five Entry-Point Review

| entry point | reviewed behavior |
| --- | --- |
| Training `train.py --dir` | uses validated weight continuation and explicit reset acknowledgement; no inherited HARL assignment restore |
| Generic HARL play | assignment tasks hard-rejected before unvalidated restore; non-assignment behavior preserved |
| Assignment play | normal evaluation, named lifecycle ablation evaluation, and explicit unversioned legacy fallback route through shared loader |
| Playback diagnostics | routes through shared loader and reads checkpoint kind from completion marker |
| Comparison evaluation | unsupported assignment-RL path hard-rejects before loading |

The helper name `_build_and_load_assignment_actors` remains in assignment play/diagnostics, but static inspection shows it constructs live actor modules and calls `load_assignment_checkpoint`; it is not a direct `torch.load` bypass.

## 10. Continuation Semantics

Review result:

```text
PASS
```

Validated weight continuation restores:

```text
three actor state_dicts
critic state_dict
ValueNorm state when enabled
```

It intentionally does not restore:

```text
actor optimizers
critic optimizer
training/update counters
best reward
RNG
environment/resolver state
rollout buffers
```

Training continuation requires explicit acknowledgement:

```text
--acknowledge-weight-continuation-reset
```

No reviewed CLI guard, report, or loader path upgrades this into exact resume. `EXACT_TRAINING_RESUME` and training initialization/fine-tuning purposes are rejected before load.

## 11. Model / Buffer / Backward Evidence

Review result:

```text
PASS
```

Phase 9G-8F-4 exercised the installed:

```text
HAPPO
StochasticPolicy
VCritic
VNet
OnPolicyActorBuffer
OnPolicyCriticBufferEP
ValueNorm
HAPPO.update
VCritic.update
```

For lifecycle and legacy dimensions, the tests covered actor forward, critic forward, masked `evaluate_actions`, actor/critic buffer insertion, feed-forward generator alignment, backward, gradient clipping, Adam step, finite parameter updates, actor independence, and ValueNorm update behavior.

No project-local PPO or simplified critic loss was substituted.

## 12. End-To-End Save / Load Evidence

Review result:

```text
PASS
```

Phase 9G-8F-5 evidence reran successfully:

| evidence | result |
| --- | --- |
| Source model real HARL preparation update | pass |
| Native checkpoint save through coordinator | pass |
| Fresh target differed before load | pass |
| Target loaded through shared loader | pass |
| State key equality | `51/51` exact |
| Actor output max difference | `0.0` |
| Critic output max difference | `0.0` |
| ValueNorm output max difference | `0.0` |
| Target optimizer semantics | fresh until post-load updates |
| Real post-load HAPPO/VCritic update | pass |
| Source state unchanged | pass |
| Re-save generation | `0 -> 1` |
| Fingerprint stability | pass |
| Corruption/mismatch rejection | no partial mutation |

Normal evaluation and named lifecycle ablation load actors only. Native legacy output equivalence passed.

## 13. Static Direct-Load Audit

Searches covered:

```text
torch.load
torch.save
load_state_dict
strict=False
restore(
_load_assignment_actors
_actor_checkpoint_path
_full.pt
save_entire_model
```

Relevant production findings:

| occurrence | classification |
| --- | --- |
| `assignment_checkpoint_load.py:379` `torch.load(path, map_location="cpu", weights_only=True)` | shared native loader |
| `assignment_checkpoint_load.py:693` `torch.load(path, map_location="cpu", weights_only=True)` | explicit unversioned legacy fallback |
| `assignment_checkpoint_load.py:448,453` `load_state_dict(..., strict=True)` | shared live load and rollback |
| `assignment_checkpoint_save.py:526` `torch.save` | shared atomic save coordinator |
| `assignment_checkpoint_load.py` / `assignment_checkpoint_save.py` `_full.pt` scans | explicit full-model conflict rejection |
| `assignment_harl_training.py:681` `super().restore()` | non-assignment branch only |
| `play_assignment.py` and diagnostics `_build_and_load_assignment_actors` | builds actor modules, then calls shared loader |
| Installed HARL `on_policy_base_runner.py` `torch.load`/`torch.save` | installed non-assignment behavior; assignment training restore/save is overridden or guarded |

No production assignment `strict=False` occurrence was found. No direct assignment `torch.load` bypass was found outside the shared loader and explicit legacy fallback.

## 14. Regression Rerun Results

Environment:

```text
Python: C:\isaacenvs\isaac45_harl\python.exe
Conda command: D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl
```

Rerun:

| suite | result |
| --- | --- |
| 9G-8F-1 contract core | PASS, `27/27` |
| 9G-8F-2 save integration | PASS, `15/15` |
| 9G-8F-3 loader integration | PASS, `15/15` |
| 9G-8F-4 model readiness | PASS, `15/15` |
| 9G-8F-5 continuation smoke | PASS, `22/22` |
| 9G-8E mask/HARL replay | PASS, `11/11` |
| 9G-8E-R feed-forward guard | PASS, `9/9` |

Total:

```text
PASS, 114/114
```

Additional validation:

| command | result |
| --- | --- |
| `python -m py_compile` for changed/new Python files | PASS |
| direct assignment load scan | PASS |
| `git diff --check` | PASS with LF-to-CRLF warnings only |

No Isaac Sim, AppLauncher, training, playback, evaluation, checkpoint development experiment, or real checkpoint load was run.

## 15. Worktree And Commit-Scope Table

`git status --short --untracked-files=all` shows expected Phase 9G-8 source/test/report changes only. The current review added this report and the 9G-8F-6 TASK_PROGRESS archive/update.

Commit readiness is still:

```text
NOT COMMIT-READY
```

Reason:

The worktree contains a known blocking source/report mismatch for the requested readiness decision: `lifecycle_contract_c` remains hard-blocked for training by `training_allowed=False` and a stale reason string. A commit titled "complete lifecycle training checkpoint readiness" would be premature until Phase 9G-8F-6R closes that gate deliberately and reruns the review evidence.

## 16. Remaining Unsupported Capabilities

| capability | status |
| --- | --- |
| Fresh lifecycle HAPPO feed-forward training | Not authorized yet; gate fix required |
| Controlled short training smoke | Prohibited in current source |
| Long lifecycle training | Not authorized |
| Native lifecycle checkpoint save | Supported |
| Native lifecycle evaluation restore | Supported |
| Named lifecycle ablation restore | Supported |
| Validated weight continuation | Supported |
| Exact training resume | Unsupported |
| Fine-tuning with changed contract | Deferred |
| Unversioned legacy evaluation fallback | Supported with explicit restrictions |
| Unversioned legacy continuation | Unsupported |
| Lifecycle recurrent | Unsupported |
| FP lifecycle critic | Unsupported |
| `share_param=true` lifecycle | Unsupported |
| HATRPO lifecycle | Unsupported |
| HAA2C lifecycle | Unsupported |

## 17. Controlled Training-Smoke Decision

Decision:

```text
controlled training-smoke authorization: prohibited
```

Reason:

`CONTROLLED-TRAINING-SMOKE-READY` requires that one fresh-start short lifecycle smoke can be authorized without changing source code. Current code fails that standard because `AssignmentIsaacLabEnv` raises on the wrapper profile's `training_allowed=False`.

The complete training prohibition remains in effect.

## 18. Controlled-Smoke Preconditions

These are not yet activated. They should become enforceable only after Phase 9G-8F-6R changes the gate and passes review:

```text
1. Current reviewed code plus gate fix is committed first.
2. Training uses a new unique experiment directory.
3. No old checkpoint is supplied.
4. lifecycle_contract_c is explicitly selected.
5. Recurrent flags remain false.
6. EP and share_param=false remain active.
7. save_entire_model remains false.
8. Any contract mismatch is a hard stop.
9. Any NaN/Inf is a hard stop.
10. The run remains short and bounded.
11. The result is reviewed before longer training.
```

No final command is frozen in this phase.

## 19. Commit Readiness Decision

Decision:

```text
NOT COMMIT-READY
```

Blocking issue:

```text
lifecycle_contract_c.training_allowed remains False.
The associated blocked reason still says checkpoint manifest/fingerprint,
loader compatibility, forward/backward readiness, and save/load validation
are not ready, although Phase 9G-8F evidence now passes.
```

This is a narrow source-level consistency/gating issue, not a failure of the implemented checkpoint contract, loader, save coordinator, model/buffer evidence, or continuation smoke.

## 20. Recommended Commit Contents / Message

No commit should be made from the current state.

After Phase 9G-8F-6R passes, the provisional included content should be:

```text
source lifecycle observation/mask/profile/checkpoint modules
assignment HARL wrapper/training integration
assignment train/play/evaluation entry-point loader routing
project-local lifecycle/checkpoint tests
AgentRead phase reports and TASK_PROGRESS archives
```

Explicit exclusions:

```text
ignored results/
ignored logs/
ignored videos/
ignored __pycache__/
ignored .pyc files
any temporary checkpoint/model artifacts
any installed HARL or Conda files
```

Provisional future commit title:

```text
feat(assignment): complete lifecycle training checkpoint readiness
```

Provisional future commit body:

```text
- integrate lifecycle actor/shared observations and Contract C masks
- freeze lifecycle_contract_c as feed-forward only
- add ordered checkpoint contract manifests and SHA-256 fingerprints
- route native assignment saves through the atomic project coordinator
- route all assignment loads through the strict shared loader
- validate real HARL actor/critic/buffer forward-backward paths
- validate end-to-end weight continuation and re-save semantics
- preserve legacy observation/mask/checkpoint isolation
```

## 21. Remaining Risks

| risk | status |
| --- | --- |
| Training gate stale / disabled | Blocking, requires 9G-8F-6R |
| First real resolver-enabled training loop | Not yet run |
| Long training stability/performance | Not evaluated |
| Exact resume | Unsupported by design |
| Recurrent lifecycle | Unsupported by design and guarded |
| Installed HARL chunked recurrent issue | Documented unsupported dependency branch |
| Ignored historical results/logs in working tree | Excluded from commit scope |

## 22. Final Recommendation

Final technical recommendation:

```text
READY WITH REQUIRED FIXES
```

Final commit recommendation:

```text
NOT COMMIT-READY
```

Proceed next with only:

```text
Phase 9G-8F-6R:
Controlled Training Gate Activation and Review Closure
```

Do not run the controlled training smoke until that corrective phase passes and the reviewed source is committed. General or long resolver-enabled training remains prohibited.

Confirmation:

```text
review only
no production Python behavior changed
no tests modified
no YAML/runtime defaults modified
no checkpoint contract/schema/save/load behavior changed
no resolver, Contract C, observation, mask, reward, or controller behavior changed
no checkpoint development artifact created
no resolver-enabled training run
no playback/evaluation run
no Isaac Sim/AppLauncher launched
no installed HARL or Conda modification
no commit made
```
