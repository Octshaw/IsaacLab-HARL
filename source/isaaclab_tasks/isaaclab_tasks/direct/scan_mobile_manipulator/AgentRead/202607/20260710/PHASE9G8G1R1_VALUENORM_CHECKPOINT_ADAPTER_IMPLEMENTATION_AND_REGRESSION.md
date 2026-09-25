# Phase 9G-8G-1R-1: ValueNorm Checkpoint Adapter Implementation and Regression

Date: 2026-07-10

## Classification

SMOKE-RETRY-READY

The project-side HARL ValueNorm checkpoint adapter, checkpoint contract v2, strict save/load path, and rollback coverage are complete. All required non-environment regressions pass, including forced CPU conversion and actual CUDA runtime-style ValueNorm cases. The failed 9G-8G-1 smoke was not retried.

## Scope And Files

Inputs included the accepted 9G-8G-1 execution report, 9G-8G-1R-0 design, 9G-8F-4/5 reports, project checkpoint boundaries, tests, and installed HARL `valuenorm.py` / `v_critic.py` read-only.

Created:

- `assignment_value_normalizer_checkpoint.py`
- `scripts/environments/test_assignment_value_normalizer_checkpoint_adapter.py`
- this report
- `TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R1_VALUENORM_IMPLEMENTATION_20260710.md`

Modified:

- `assignment_checkpoint_contract.py`
- `assignment_checkpoint_save.py`
- `assignment_checkpoint_load.py`
- `assignment_harl_training.py`
- checkpoint contract/save/loader/continuation regression tests
- `AgentRead/TASK_PROGRESS.md`

No resolver, Contract C, lifecycle observation/shared-observation ordering, lifecycle-mask semantics, rewards, controller, YAML/runtime defaults, installed HARL, or Conda files were modified.

## Adapter Implementation

Project-local module: `assignment_value_normalizer_checkpoint.py`.

Frozen artifact field order:

1. `running_mean`
2. `running_mean_sq`
3. `debiasing_term`

Public operations are `inspect_value_normalizer_target`, `build_value_normalizer_contract`, `export_value_normalizer_checkpoint_state`, `validate_value_normalizer_checkpoint_state`, `validate_value_normalizer_target_contract`, and `restore_value_normalizer_checkpoint_state(..., strict=True)`.

Inspection reads the installed `harl.common.valuenorm.ValueNorm` live attributes directly and records exact field shape, dtype, device, Tensor/Parameter classification, input shape, norm axes, beta, epsilon, and per-element update mode. Implementation identity is strict compatibility: `harl.common.valuenorm.ValueNorm`.

Export requires exactly the three finite fields, uses `detach().clone().cpu()`, preserves dtype, returns an `OrderedDict`, and does not mutate the live object. Restore completes exact key/order, tensor, finite, shape, dtype, target-layout, and target-contract validation before its first mutation. It uses `torch.no_grad()` and `copy_` only, never `setattr`, object replacement, dtype conversion, or generic ValueNorm `load_state_dict()`.

The adapter backs up all fields and rolls them back on copy/verification failure. Tensor/Parameter classification and object identity are preserved. The shared loader now includes ValueNorm in its actor/critic global transaction; an injected ValueNorm restore failure proves global actor, critic, and ValueNorm rollback.

## Contract V2 And Disabled Mode

`MANIFEST_FORMAT_VERSION` is now `assignment_checkpoint_contract_v2`.

The exact enabled `training_contract.value_normalizer_contract` binds `enabled`, adapter version, artifact format, strict implementation identity, `input_shape`, `norm_axes`, `beta`, `epsilon`, `per_element_update`, canonical `float32` dtype, and canonical state-key order. It participates in canonical JSON and SHA-256.

`float32` is the sole normalized spelling. Device is intentionally excluded so a CPU checkpoint tensor can restore into a compatible CUDA target without dtype conversion. Implementation identity is strict because the adapter depends on the installed HARL layout.

Disabled ValueNorm is exactly `{\"enabled\": false}`. It forbids the artifact, export, target inspection, restore, and inventory. An enabled/disabled runtime-contract mismatch is a hard error. Native v1 lifecycle manifests are not silently accepted for v2 continuation; the explicit unversioned legacy actor-only evaluation fallback remains.

## Save, Load, And Evaluation Isolation

`AssignmentOnPolicyHARunner.save()` now exports through the adapter. The coordinator remains the only artifact writer and preserves atomic `value_normalizer.pt`, inventory/SHA-256, manifest binding, generation, and completion-marker-last behavior. Invalid/nonfinite state fails before marker creation.

The shared loader remains the only native artifact reader. It CPU-deserializes with `weights_only=True`, validates files and tensor inventories, validates v2 ValueNorm artifact semantics, and validates live target semantics before any mutation. Validated continuation strictly restores actor/critic and adapter-restores ValueNorm. Wrong target input shape, dtype, or ValueNorm configuration rejects before actor mutation.

Normal evaluation and named lifecycle ablation remain actor-only and neither require nor mutate a live ValueNorm target. Optimizer state remains fresh after validated weight continuation.

## Regression Evidence

Adapter suite: `8 passed`.

- CPU no-op registered-Parameter diagnostic: PASS
- Forced CPU effective-conversion Tensor diagnostic: PASS
- CUDA runtime-style Tensor export/restore: PASS; it executed and was not skipped.
- Export order, detached CPU clones, finite checks, and update evidence: PASS.
- Registered and unregistered round-trip output equivalence: PASS.
- Strict rejection, no mutation, and object-identity preservation: PASS.
- Adapter copy-failure rollback: PASS.
- Target-contract and disabled-contract validation: PASS.

The v2 contract suite covers canonical stability, enabled/disabled exact objects, dtype normalization, beta/epsilon/input-shape/norm-axes/per-element fingerprints, canonical key order, adapter format, and implementation identity.

The loader suite covers registered CPU Parameter continuation, forced CPU and CUDA unregistered Tensor continuation through 8F-5, CPU artifact to CUDA target restoration, live shape/dtype/config prevalidation, global actor/critic/ValueNorm rollback, and evaluation/ablation isolation.

8F-5 no longer relies on CPU no-op registration. It routes all ValueNorm save, inventory, and equality checks through production adapter/save/load code. Its added round trip asserts native `state_dict()` is empty while adapter export is nonempty for forced CPU and CUDA runtime-style objects, then checks exact fields plus normalize/denormalize equivalence.

Validation totals:

- Adapter + v2 contract + loader: `52 passed`.
- Save + forward/backward + 8F-5: `53 passed`.
- 8C/8D observation integration: `6 passed`.
- 8E mask/replay, 8E-R feed-forward guard, 8F-6R gate: `30 passed`.
- Consolidated required suites: `141 passed in 26.74s` on the final rerun.
- `py_compile` for every changed/new Python file: PASS.

## Direct Save/Load Audit

| Search | Result |
| --- | --- |
| `value_normalizer.state_dict` | No assignment runtime save use; test diagnostics only. |
| `value_normalizer.load_state_dict` | No assignment runtime load use. |
| `torch.save` | Native artifact writes remain only in the save coordinator. |
| `torch.load` | Native reads remain only in the shared loader, CPU `weights_only=True`. |
| `strict=False` | No production use; rejection test only. |
| `value_normalizer.pt` | Coordinator/loader naming and integrity validation only. |
| v1 contract identifier | Stale production wording updated; v2 is active. |

## Remaining Limits And Next Boundary

The adapter deliberately supports only the pinned installed HARL ValueNorm layout and frozen float32 lifecycle contract. It does not broaden recurrent support, make native v1 lifecycle checkpoints continuation-compatible, or authorize general training. No real result checkpoint was loaded or inspected.

After review, the next boundary is Phase 9G-8G-1R-2: ValueNorm-Fixed Controlled Training Smoke Retry. It must use a fresh experiment name and exactly one headless fresh-start 300-step/one-update smoke. It must not load, reuse, delete, or overwrite the failed result, and must not run playback/evaluation. No retry command was provided or executed here.

## Worktree And Prohibitions

`git diff --check` and final worktree inspection are recorded with the handoff. No generated checkpoint, model, TensorBoard, result, CUDA dump, or temporary diagnostic file was added.

No `train.py`, AppLauncher, Isaac Sim, assignment environment, smoke retry, playback, evaluation, visual inspection, long training, installed HARL/Conda modification, or commit occurred.
