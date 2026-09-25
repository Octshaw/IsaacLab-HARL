# Phase B2-T4-CKPT1 Optimization-Continuation Checkpoint Implementation Report

Classification: `PHASE-B2-T4-CKPT1-OPTIMIZATION-CONTINUATION-CHECKPOINT-IMPLEMENTATION-AND-PURE-QUALIFICATION-COMPLETE-AWAITING-GPT-REVIEW`

This phase implemented and CPU-qualified the project-owned complete learner checkpoint. It did not start CUDA, `AppLauncher`, an Isaac environment, a formal supervisor/worker, a real rollout, a real learner continuation, evaluation, playback, CKPT2, R15, or paper-scale training.

## A. BEFORE CKPT1

CSR1 is treated as GPT REVIEW PASS/CLOSED. Its report and final-result hashes are preserved in `b2_t4_ckpt1_artifacts/csr1_preservation.json`. The R14 run remains historical, poisoned, retained, and never reused; its report and freeze evidence are preserved in `historical_r14_preservation.json`.

The pre-write repository authority snapshot matched CSR1 exactly: branch `main`; HEAD, `origin/main`, and merge-base all `b71d85a32f51be6ada324f870813a56bb45dd396`; 50,543 porcelain paths; 359 staged historical paths. No pre-existing user change was staged, reset, cleaned, or overwritten.

Before CKPT1, the native assignment checkpoint provided actor/critic weights and project ValueNorm state, but not actor Adam state, critic Adam state, or update/LR progression. It therefore remained a weights-continuation format rather than a complete optimization-continuation format.

## B. CHECKPOINT STATE CONTRACT

The new schema is `lifecycle_mrta_optimization_checkpoint_v1`. Its complete state is:

| State | Required | Qualified |
|---|---:|---:|
| All actor weights, ordered by stable agent identity | yes | PASS |
| All actor Adam optimizer states and parameter groups | yes | PASS |
| Critic weights | yes | PASS |
| Critic Adam optimizer state and parameter groups | yes | PASS |
| Project-owned ValueNorm mutable fields | when enabled | PASS |
| Completed/next update and linear-LR schedule position | yes | PASS |
| Semantic reconstruction configuration | yes | PASS |

State coverage is 7/7 and complete. Simulator, environment, rollout-buffer, and RNG snapshots are deliberately outside this optimization-continuation contract; a continuation begins with fresh environment and buffer state at a clean post-update boundary.

## C. IMPLEMENTATION

`assignment_optimization_checkpoint.py` owns the format and exposes `save_optimization_checkpoint`, `validate_optimization_checkpoint`, and `load_optimization_checkpoint`. `AssignmentOnPolicyHARunner` exposes separate optimization-continuation save/validate/restore APIs, tracks clean/poisoned update boundaries, advances progress only after inherited HA training returns successfully, and can apply the exact next saved linear-LR schedule position.

The existing weight-only `save()/restore()` path remains separate for evaluation and explicitly acknowledged weight continuation. Installed HARL files were read only; modification count is zero.

## D. SAVE BOUNDARY

A save is accepted only when the transaction is complete, optimizer and ValueNorm mutation are complete, and there is no partial update, active backward pass, active optimizer step, active load, or poison. Eight focused dirty-boundary cases were rejected 8/8.

The runner marks rollout/update entry dirty, marks a failed inherited update poisoned, and marks a successful inherited update clean only after all learner mutations have returned.

## E. ATOMIC SAVE

Each generation is built in a hidden temporary directory. Component files are written and flushed first, the authoritative manifest is written last, every digest and component is read back, and only then is the directory atomically renamed to `generation_NNNNNNNN`. A separately written `latest.json` is atomically replaced to publish authority.

An injected failure after full readback but before generation publication left the previous `latest.json` byte-identical and preserved all prior immutable generations. Result: PASS.

## F. STRICT LOAD

Load resolves the authoritative pointer, verifies its manifest digest, requires an exact schema/purpose/status, rejects unlisted or missing files, verifies every SHA-256, checks exact component counts and actor identity/order, validates tensor keys/shapes/dtypes/finiteness, checks Adam group cardinality, validates ValueNorm shape/dtype, validates progression invariants, and compares the semantic configuration before changing any target.

If application fails after mutation begins, every actor, every actor optimizer, the critic, critic optimizer, ValueNorm, and progression are restored. The injected post-actor-optimizer failure produced an exact target rollback. An incomplete rollback would raise an explicit poisoned-target error rather than return a usable runner.

## G. OPTIMIZER CONTINUITY

The CPU fixture uses two distinct actors, two populated Adam actor optimizers, one critic, and one populated Adam critic optimizer. Save/load round-trip comparison was recursive tensor-exact and scalar-exact. After load, the source and restored learners received the same scheduled LR and deterministic controlled update; weights and all Adam moments/steps remained exact. Result: PASS.

## H. VALUENORM CONTINUITY

The format calls the existing project-owned ValueNorm adapter rather than relying on generic module state. Nontrivial `running_mean`, `running_mean_sq`, and `debiasing_term` values round-tripped exactly and remained exact after the controlled post-load update. A target shape mismatch was rejected before mutation. Result: PASS.

## I. PROGRESSION CONTINUITY

The fixture saved completed update `p=1` of 12, restored next update and linear schedule position `p+1=2`, applied `lr = initial_lr - initial_lr * 2/12`, and advanced to completed update 2 only after the controlled update succeeded. The schedule did not restart at zero. Result: PASS.

## J. LEGACY COMPATIBILITY

Legacy weights-only checkpoints remain available to the pre-existing evaluation/explicit weight-loading path. They are rejected for optimization continuation with `OPTIMIZER_STATE_REQUIRED_FOR_OPTIMIZATION_CONTINUATION`; optimizer state is never silently reinitialized. Result: PASS.

## K. NEGATIVE MATRIX

| Group | Named cases | Expected reject | Unexpected |
|---|---:|---:|---:|
| Dirty/poisoned save boundary | 8 | 8 | 0 |
| Missing/corrupt/unexpected artifacts and pointer | 5 | 5 | 0 |
| Manifest/schema/coverage/identity incompatibility | 4 | 4 | 0 |
| Progression/model/optimizer incompatibility | 5 | 5 | 0 |
| Semantic config and ValueNorm incompatibility | 2 | 2 | 0 |
| Legacy weights-only continuation | 1 | 1 | 0 |
| **Total** | **25** | **25** | **0** |

The dedicated qualification completed 6/6 tests with 25/25 expected negative rejections. Existing independent CPU regressions also passed: checkpoint contract 28/28, ValueNorm adapter PASS, entry guard 10/10, and semantic dispatch 12/12. Two historical integration scripts were excluded because their direct CPU import path requires unavailable `omni.kit`; they did not launch `AppLauncher` or instantiate an environment and are not part of this qualification claim.

## L. NEXT PHASE

Next is independent GPT review of CKPT1. This report establishes project-side implementation and synthetic CPU/static qualification only. It does not establish real checkpoint continuation, training quality, CUDA/Isaac behavior, public-route readiness, CKPT2, R15, evaluation/playback, or paper-scale training. Those remain not authorized.

Counts: runtime `false`; CUDA/AppLauncher/environment `0/0/0`; formal supervisor/worker `0/0`; installed HARL modifications `0`; git add/commit/push `0/0/0`.

Evidence root: `b2_t4_ckpt1_artifacts/`.
