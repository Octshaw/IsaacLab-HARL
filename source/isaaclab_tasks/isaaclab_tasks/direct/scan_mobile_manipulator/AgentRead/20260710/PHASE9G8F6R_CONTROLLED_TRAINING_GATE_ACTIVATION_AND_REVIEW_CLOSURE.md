# Phase 9G-8F-6R: Controlled Training Gate Activation and Review Closure

Date: 2026-07-10

Path note:

The phase prompt listed `AgentRead/20260709/...` paths, but the current local date is 2026-07-10 and `AgentRead/AGENTS.md` requires new phase reports and archives to use the current `YYYYMMDD` folder. This report and the TASK_PROGRESS archive are therefore under `AgentRead/20260710/`.

## 1. Executive Classifications

Technical classification:

```text
CONTROLLED-TRAINING-SMOKE-READY
```

Commit classification:

```text
COMMIT-READY
```

The reviewed `lifecycle_contract_c` profile is now training-allowed only under the existing official support guards. The phase did not run the controlled training smoke.

## 2. Exact Blocking Issue Corrected

Phase 9G-8F-6 found this blocking inconsistency:

```text
lifecycle_contract_c.training_allowed = False
training_blocked_reason = stale checkpoint-readiness pending message
```

Phase 9G-8F-6R corrected it narrowly:

```text
lifecycle_contract_c.training_allowed = True
training_blocked_reason = absent, matching allowed-profile convention
```

The stale runtime constant `ASSIGNMENT_LIFECYCLE_MASK_PENDING_ERROR` was removed. Historical reports were preserved unchanged as historical evidence.

## 3. Files Modified

Created:

| file | purpose |
| --- | --- |
| `scripts/environments/test_assignment_lifecycle_controlled_training_gate.py` | New synthetic controlled-gate tests |
| `AgentRead/20260710/PHASE9G8F6R_CONTROLLED_TRAINING_GATE_ACTIVATION_AND_REVIEW_CLOSURE.md` | This report |
| `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F6R_GATE_ACTIVATION_20260710.md` | Required TASK_PROGRESS archive |

Modified:

| file | purpose |
| --- | --- |
| `assignment_harl_wrapper.py` | Activate only the reviewed `lifecycle_contract_c` profile gate |
| `assignment_lifecycle_training_contract.py` | Keep lifecycle HAPPO/EP/share-param/state-dict/feed-forward guards mandatory |
| `scripts/reinforcement_learning/harl/train.py` | Pass resolved algorithm into the lifecycle validator before runner construction |
| `AgentRead/TASK_PROGRESS.md` | Current concise handoff |

Explicitly not modified:

```text
resolver behavior
Contract C mask semantics
ownership/arbitration/release behavior
reward/controller behavior
observation/shared/action ordering
checkpoint contract/schema behavior
save/load behavior
installed HARL
Conda environment
YAML defaults
```

## 4. Gate Before / After

| profile | before | after |
| --- | --- | --- |
| `legacy` | training allowed as before | unchanged |
| `lifecycle_ablation` | training prohibited | unchanged |
| `lifecycle_contract_c` | training prohibited by stale readiness gate | training allowed subject to mandatory official support guards |
| `diagnostics_hidden_state` | training prohibited | unchanged |
| unknown profile | hard error | unchanged |

`AssignmentIsaacLabEnv` still enforces:

```text
if not profile.training_allowed:
    raise RuntimeError(...)
```

The environment-side prohibited-profile guard remains active.

## 5. Profiles Still Prohibited

| profile | status |
| --- | --- |
| `lifecycle_ablation` | Training-prohibited; explicit observation/mask ablation profile |
| `diagnostics_hidden_state` | Training-prohibited; diagnostics-only |
| invalid profile | Hard error; no fallback to trainable lifecycle profile |

The new tests verify all three boundaries.

## 6. Existing Sequence / Model / Checkpoint Guards

The official `lifecycle_contract_c` training path still requires:

| guard | implementation |
| --- | --- |
| HAPPO only | `validate_assignment_lifecycle_policy_sequence()` rejects non-`happo` resolved algorithm |
| EP only | validator rejects `state_type != "EP"` |
| Independent actors | validator rejects `algo.share_param=True` |
| Feed-forward only | validator rejects both recurrent flags |
| State-dict only | validator rejects `train.save_entire_model=True`; runner save still rejects lifecycle full-model saves |
| Actor count / shape | model-readiness tests still enforce `M=3,N=50`, actor dim `1059`, shared dim `3183`, action dim `51` |

The activation is composed as:

```text
profile allows training
AND
sequence/model/checkpoint guards validate resolved configuration
```

It is not a broad bypass.

## 7. Training-Entry Validation Ordering

Static source review confirms:

```text
train.py:
  resolved algorithm is copied to env_args["algorithm"]
  validate_assignment_lifecycle_policy_sequence(...) runs
  runner construction follows only after validation

AssignmentOnPolicyHARunner.__init__:
  validates the lifecycle sequence contract before normal runner setup

AssignmentIsaacLabEnv:
  retains the prohibited-profile training_allowed guard
```

Unsupported lifecycle recurrent, non-HAPPO, FP, share-param, and full-model configurations fail before runner construction in the project-local training path.

## 8. Stale-Message Audit

Search terms:

```text
ASSIGNMENT_LIFECYCLE_MASK_PENDING_ERROR
checkpoint readiness pending
forward/backward readiness pending
checkpoint manifest/fingerprint
training_allowed
training_blocked_reason
lifecycle training is blocked
resolver-enabled training remains prohibited
```

Current runtime/source classification:

| occurrence | classification |
| --- | --- |
| `assignment_harl_wrapper.py` `training_allowed=True` for legacy and Contract C | expected |
| `assignment_harl_wrapper.py` `training_allowed=False` and blocked reason for ablation | expected |
| `assignment_harl_wrapper.py` `training_allowed=False` for diagnostics | expected |
| `assignment_harl_training.py` `training_allowed` gate | expected prohibited-profile safety check |
| New gate tests | expected assertions |
| `AgentRead/TASK_PROGRESS.md` old blocking text | updated in this phase |

No stale runtime pending-readiness message remains in Python source.

## 9. New Gate-Test Results

Command:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python scripts/environments/test_assignment_lifecycle_controlled_training_gate.py
```

Result:

```text
PASS 10/10 controlled lifecycle gate tests
```

Covered:

```text
official lifecycle_contract_c activation
lifecycle_ablation remains prohibited
diagnostics remains prohibited
unknown profile hard error
recurrent and naive recurrent hard errors
FP hard error
share_param=true hard error
HATRPO/HAA2C hard errors
save_entire_model=true hard error
fake AssignmentIsaacLabEnv gate behavior without real environment construction
train.py validation ordering
```

## 10. Full 114-Test Regression Results

Rerun:

| suite | result |
| --- | --- |
| Phase 9G-8F-1 contract core | PASS, `27/27` |
| Phase 9G-8F-2 save integration | PASS, `15/15` |
| Phase 9G-8F-3 loader integration | PASS, `15/15` |
| Phase 9G-8F-4 model readiness | PASS, `15/15` |
| Phase 9G-8F-5 continuation smoke | PASS, `22/22` |
| Phase 9G-8E mask/HARL replay | PASS, `11/11` |
| Phase 9G-8E-R feed-forward guard | PASS, `9/9` |

Existing total:

```text
PASS, 114/114
```

With the new 9G-8F-6R gate suite:

```text
PASS, 124/124
```

## 11. Static Contract Re-Review

Reviewed official values after the gate change:

| field | value |
| --- | --- |
| profile | `lifecycle_contract_c` |
| algorithm | `HAPPO` |
| state type | `EP` |
| `share_param` | `false` |
| sequence | feed-forward |
| actor dimension | `1059` |
| shared dimension | `3183` |
| action dimension | `51` |
| raw noop | `50` |
| decoded noop | `-1` |
| actor hidden sizes | `[256,256]` |
| effective critic hidden sizes | `[256,256]` |
| ValueNorm | enabled |
| checkpoint serialization | `state_dict` only |

No dimension, field order, mask rule, resolver rule, checkpoint field, or network architecture changed in this phase.

## 12. Direct Save / Load Audit

Production assignment scan result:

| occurrence | classification |
| --- | --- |
| `assignment_checkpoint_load.py` native `torch.load(..., map_location="cpu", weights_only=True)` | shared loader |
| `assignment_checkpoint_load.py` legacy fallback `torch.load(..., map_location="cpu", weights_only=True)` | explicit unversioned legacy fallback |
| `assignment_checkpoint_load.py` `load_state_dict(..., strict=True)` | strict live load / rollback |
| `assignment_checkpoint_save.py` `torch.save` | atomic state-dict save coordinator |
| `_full.pt` scans | full-model conflict/rejection checks |
| `assignment_harl_training.py` `super().restore()` | non-assignment branch only |
| `play_assignment.py` / diagnostics `_build_and_load_assignment_actors` | constructs actors and calls shared loader |

No production assignment `strict=False` or direct loader bypass was found.

## 13. Worktree And Commit Scope

`git status --short --untracked-files=all`, `git diff --name-status`, `git diff --stat`, and `git diff --check` were inspected.

Commit scope is expected for the accumulated Phase 9G-8 work:

```text
new lifecycle/checkpoint source modules
modified assignment wrapper/training/entry scripts
new project-local tests
AgentRead reports and TASK_PROGRESS archives
```

Excluded from commit scope:

```text
models/
best_model/
results/
logs/
videos/
TensorBoard events
__pycache__/
.pyc files
temporary checkpoint files
temporary JSON files
editor artifacts
installed HARL / Conda files
```

`git diff --check` passed with LF-to-CRLF warnings only.

## 14. Controlled-Smoke Authorization

Decision:

```text
controlled training-smoke authorization: allowed
```

Technical classification:

```text
CONTROLLED-TRAINING-SMOKE-READY
```

This authorizes exactly one future controlled smoke after the reviewed code is committed. It does not authorize long or general resolver-enabled training.

## 15. Controlled-Smoke Restrictions

The future smoke is restricted to:

```text
fresh start
no --dir
new unique experiment directory
lifecycle_contract_c explicitly selected
HAPPO
EP
share_param=false
feed-forward
state_dict-only checkpoint
save_entire_model=false
M=3
N=50
minimal practical num_envs
short bounded smoke only
runtime integration validation, not policy-performance evaluation
```

Hard stops:

```text
any contract mismatch
any NaN/Inf
any checkpoint save/load exception
any recurrent flag enabled
any non-HAPPO lifecycle algorithm
any FP or share_param=true lifecycle configuration
```

General or long resolver-enabled training remains prohibited until the controlled smoke result is reviewed.

## 16. Commit-Readiness Decision

Commit classification:

```text
COMMIT-READY
```

Reasons:

```text
stale gate corrected narrowly
unsupported profiles remain prohibited
official support guards remain mandatory
existing 114 tests pass
new 10 gate tests pass
py_compile passes
direct load/save audit passes
git diff --check passes
no generated runtime artifact entered commit scope
reports and TASK_PROGRESS match current source
installed HARL and Conda are unchanged
```

Do not run `git add` or `git commit` in this phase.

## 17. Recommended Commit Message

Title:

```text
feat(assignment): complete lifecycle training checkpoint readiness
```

Body:

```text
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

## 18. Remaining Unsupported Capabilities

| capability | status |
| --- | --- |
| General/long lifecycle training | Not yet authorized |
| Exact training resume | Unsupported |
| Fine-tuning with changed contract | Deferred |
| Lifecycle recurrent | Unsupported |
| FP lifecycle critic | Unsupported |
| `share_param=true` lifecycle | Unsupported |
| HATRPO lifecycle | Unsupported |
| HAA2C lifecycle | Unsupported |
| Unversioned legacy continuation | Unsupported |

## 19. Final Recommendation

Final recommendation:

```text
COMMIT the reviewed Phase 9G-8 work before running the one authorized controlled smoke.
```

After commit, the next phase may run exactly one fresh-start short bounded `lifecycle_contract_c` HAPPO/EP/feed-forward controlled training smoke under the restrictions above.

Confirmation:

```text
no resolver-enabled training run
no real environment construction
no playback/evaluation run
no Isaac Sim/AppLauncher launched
no installed HARL modification
no Conda modification
no commit made
```
