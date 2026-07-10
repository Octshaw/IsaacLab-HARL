# TASK_PROGRESS

## Current Status

Phase 9G-8G-1R-1 implemented the project-side strict ValueNorm checkpoint adapter and checkpoint contract v2.

Classification: `SMOKE-RETRY-READY`.

Runtime-style CUDA ValueNorm state is exported through the project adapter, not generic `ValueNorm.state_dict()`. Validated continuation restores it through strict attribute copy with target prevalidation and both adapter-level and global actor/critic/ValueNorm rollback.

## Active Checkpoint Boundary

- Manifest format: `assignment_checkpoint_contract_v2`.
- Canonical ValueNorm fields: `running_mean`, `running_mean_sq`, `debiasing_term`.
- The enabled contract binds installed implementation identity, layout, beta, epsilon, dtype, canonical key order, and adapter artifact format.
- The disabled contract is exactly `{"enabled": false}`.
- The coordinator remains the only native checkpoint writer; the shared loader remains the only native artifact reader.
- Evaluation and named ablation remain actor-only. Validated continuation restores actor, critic, and ValueNorm with fresh optimizer semantics.

## Latest Verification

- Runtime-style CUDA adapter export/restore: PASS.
- Forced CPU effective-conversion adapter/save/load: PASS.
- Global actor/critic/ValueNorm rollback: PASS.
- V2 contract/fingerprint and disabled path: PASS.
- 8F-5 continuation blind-spot closure: PASS.
- Consolidated non-environment regression: `141 passed in 26.74s`.
- `py_compile`: PASS.

## Do Not Do

- Do not run general or long resolver-enabled training.
- Do not load or continue from the failed 9G-8G-1 result.
- Do not run playback, evaluation, comparison, or additional seeds.
- Do not change resolver, Contract C, lifecycle observations/masks, or YAML defaults.
- Do not modify installed HARL or the Conda environment.

## Next Step

After review, the next allowed boundary is:

`Phase 9G-8G-1R-2: ValueNorm-Fixed Controlled Training Smoke Retry`.

It may execute one fresh-name, headless, 300-step controlled smoke only. It must not reuse, load, delete, or overwrite the failed result, and must stop for review after that single run.

## Detailed Reports / Archives

- `AgentRead/20260710/PHASE9G8G1R1_VALUENORM_CHECKPOINT_ADAPTER_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R1_VALUENORM_IMPLEMENTATION_20260710.md`
- `AgentRead/20260710/PHASE9G8G1R0_VALUENORM_CHECKPOINT_ROOT_CAUSE_AND_ADAPTER_DESIGN.md`
- `AgentRead/20260710/PHASE9G8G1_CONTROLLED_TRAINING_SMOKE_EXECUTION_REPORT.md`
- `AgentRead/20260710/PHASE9G8G0_CONTROLLED_TRAINING_SMOKE_DESIGN_AND_PREFLIGHT.md`
