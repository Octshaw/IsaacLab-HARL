# Lifecycle-aware Dynamic MRTA — TASK_PROGRESS

Updated: 2026-09-23

## Current status

- B2-T4-CSR1: **GPT REVIEW PASS / CLOSED**
- B2-T4-CKPT1: **GPT REVIEW PASS / CLOSED**
- B2-T4-CKPT2: **GPT REVIEW STOP CONFIRMED / HISTORICAL / HARNESS FAILURE / NOT POISONED**
- B2-T4-CKPT2-R1: **EXPLICITLY AUTHORIZED / PRE-RUNTIME HARNESS REPAIR**
- Real optimization checkpoint continuation: **NOT ESTABLISHED**
- R15: **NOT AUTHORIZED**
- Evaluation/playback: **NOT AUTHORIZED**
- Paper-scale training: **NOT AUTHORIZED**

Current CKPT2-R1 classification: **PRE-RUNTIME / NOT YET EXECUTED**

## CKPT2 result

The only authorized CKPT2 attempt used run ID `b2-t4-ckpt2-20260923-real01-6f72c9ad`.

- Pure preflight: **6/6 PASS; negative matrix 25/25 PASS**
- Installed HARL preservation: **PASS**
- Source freeze before Process A: **PASS**
- Process A PID: **30844**
- Process B PID: **29312**
- Fresh PID separation: **PASS**
- Process A completed physical collection transitions: **2**
- Process A completed update transactions: **0/3**
- Process B completed update transactions: **0/3**
- Checkpoint save/load successes: **0/0**
- Published checkpoint generations: **0**
- tx007: **NOT STARTED**
- Matching worker count after cleanup: **0**
- Retry count: **0**
- Production source edits after Process A start: **0**
- Git add/commit/push: **0/0/0**

## First STOP boundary

Process A completed the two collection steps for tx001 and then stopped before the first full learner transaction:

`STOP — B2-T0 TX1_COLLECTION_MUTATED_LEARNER`

The CKPT2 test-side LR hook changed optimizer param-group LR after the inherited harness captured its pre-collection fingerprint. The collection-immutability gate therefore compared unlike schedule boundaries. This does **not** establish a production checkpoint defect. No actor/critic backward, optimizer step, or ValueNorm update had started. Process A's learner is **not poisoned / process discarded**.

## Secondary boundary

`SimulationApp.close()` ended Process A with process code 0 after its semantic failure. The parent incorrectly used that code as semantic success instead of requiring a durable A success/checkpoint sentinel and therefore created Process B. Process B strict validation stopped before target mutation because `checkpoint/latest.json` did not exist. Process B is **not poisoned / process discarded**.

This parent/controller behavior is a CKPT2 harness defect discovered after Process A started. Per the authorization, it was not repaired and the run was not retried.

## Preserved prior state

CKPT1 remains closed with schema `lifecycle_mrta_optimization_checkpoint_v1`, complete state coverage 7/7, CPU full-state round trip PASS, controlled post-load update EXACT PASS, and 25/25 expected negative rejections. CSR1 and all historical poisoned/non-reusable boundaries remain unchanged. R12 and R14 learners, authority, binding, PIDs, and run identities were not reused.

## CKPT2-R1 authorized repair boundary

Only two test-side defects may be repaired before runtime: LR application must finish before the pre-collection fingerprint, and Process B must require a durable Process-A semantic-success/checkpoint gate rather than return code alone. CKPT1 production, lifecycle, learner, and installed HARL semantics must not change.

CKPT2-R1 permits exactly one fresh Process A and at most one fresh Process B after the A semantic gate passes, with 3+3 bounded real updates and no retry. Runtime has not started.

## Do not do

Do not alter historical CKPT2 artifacts, modify production checkpoint/lifecycle/learner semantics, start Process B without the full A semantic gate, retry after Process A starts, claim real checkpoint continuation before evidence completes, launch R15, run evaluation/playback, begin long/paper-scale training, activate a public learned-policy route, or stage/commit/push.

## Next step

Create and purely qualify the new CKPT2-R1 harness, freeze it, then execute exactly one authorized fresh attempt. Stop after success or the first source-backed STOP.

## Detailed reports / archives

- [CKPT2 STOP report](202609/20260923/PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md)
- [CKPT2 retained evidence](202609/20260923/b2_t4_ckpt2_artifacts/)
- [Byte-exact pre-CKPT2-R1 archive](202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_CKPT2_R1_20260923.md)
- [Byte-exact pre-final CKPT2 archive](202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_CKPT2_FINAL_20260923.md)
- [Byte-exact pre-CKPT2 archive](202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_CKPT2_20260923.md)
- [CKPT1 report](202609/20260923/PHASE_B2_T4_CKPT1_OPTIMIZATION_CONTINUATION_CHECKPOINT_IMPLEMENTATION_REPORT.md)
- [CKPT1 evidence](202609/20260923/b2_t4_ckpt1_artifacts/)
- [CSR1 report](202609/20260923/PHASE_B2_T4_CSR1_CLOSURE_SCOPE_REDUCTION_REPORT.md)
