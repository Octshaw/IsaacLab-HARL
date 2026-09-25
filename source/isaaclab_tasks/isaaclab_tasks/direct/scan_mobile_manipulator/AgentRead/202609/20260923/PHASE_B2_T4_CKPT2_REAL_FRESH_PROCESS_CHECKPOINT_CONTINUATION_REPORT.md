# Phase B2-T4-CKPT2 Real Fresh-Process Checkpoint Continuation Report

Date: 2026-09-23  
Run ID: `b2-t4-ckpt2-20260923-real01-6f72c9ad`  
Classification: **PHASE-B2-T4-CKPT2-STOP-PROCESS-A-UPDATE**

CKPT2 stopped on its only authorized attempt. It did not establish real fresh-process optimization continuation. No retry, production repair, R15, evaluation/playback, public-route activation, or paper-scale training was performed.

## A. CKPT1 PRESERVATION

CKPT1 remains **GPT REVIEW PASS / CLOSED**. The pre-runtime CPU suite passed 6/6 tests and 25/25 expected negative cases. Installed HARL hashes matched the retained authority. The checkpoint implementation sources retained their frozen pre-runtime hashes:

- `assignment_optimization_checkpoint.py`: `b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9`
- `assignment_harl_training.py`: `31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787`

The CKPT2 harness was frozen before Process A at SHA-256 `3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551`. No source edit occurred after Process A started.

## B. PROCESS-A REAL TRAINING

Process A PID was `30844`. CUDA readiness, one AppLauncher, one Isaac environment, and one fresh learner were constructed. Process A completed the two physical collection transitions for tx001, then stopped before the first full learner transaction.

The first failure was:

`STOP — B2-T0 TX1_COLLECTION_MUTATED_LEARNER`

The compared digests were:

- pre-collection: `83464fa7ba7dd699137cfb8a243b087bc82b8a72313b73b3ba53f626356e49b3`
- post-collection: `cdda5575941dea5d77b6e8736570e885213658252e2e66e92df8ae58d5ce0e8b`

This does not prove a production checkpoint defect. The CKPT2 test-side LR hook changed optimizer param-group LR after the inherited harness had captured its pre-collection fingerprint. Its collection-immutability gate therefore compared unlike schedule boundaries. No actor/critic backward, optimizer step, or ValueNorm update had begun. Process A completed 0/3 update transactions and its discarded learner is classified **not poisoned**.

## C. CHECKPOINT SAVE

Not reached. Save count was 0, published generation count was 0, and no `latest.json` exists. There is no checkpoint generation to review.

## D. FRESH-PROCESS BOUNDARY

Physical separation passed: A PID `30844` exited and was inactive before B PID `29312` was created; the PIDs differ and no Python objects could be shared.

The semantic start gate failed. `SimulationApp.close()` ended Process A with process code 0 after the failure receipt. The parent treated that code as success instead of requiring a durable A success/checkpoint sentinel, so it incorrectly created Process B. This is a CKPT2 harness/controller defect discovered after Process A had started; it was not repaired or retried.

## E. PROCESS-B RECONSTRUCTION

Process B PID was `29312`. It independently constructed CUDA readiness, one AppLauncher, one environment, and one fresh learner. This consumed the one authorized Process B instance; no second B was launched.

## F. STRICT LOAD

Strict load stopped during validation with `optimization checkpoint latest.json is missing`. The target was not mutated, rollback was not required, and the reconstructed learner is classified **not poisoned / discarded**. Successful strict-load count was 0.

## G. CUDA DEVICE RESTORATION

Not reached. CUDA readiness passed in both processes, but there was no checkpoint state to restore and therefore no optimizer-state device-restoration claim.

| Component | Parameter device | Optimizer-state device | Expected | Result |
|---|---|---|---|---|
| actor 0 | CUDA at fresh construction | not loaded | `cuda:0` after load | NOT REACHED |
| actor 1 | CUDA at fresh construction | not loaded | `cuda:0` after load | NOT REACHED |
| actor 2 | CUDA at fresh construction | not loaded | `cuda:0` after load | NOT REACHED |
| critic | CUDA at fresh construction | not loaded | `cuda:0` after load | NOT REACHED |
| ValueNorm | CUDA at fresh construction | not loaded | implementation-consistent | NOT REACHED |

## H. CROSS-PROCESS STATE EQUALITY

Not reached because Process A produced no checkpoint or pre-save state.

| State | A pre-save | B post-load | Equal after load | B after tx004 | Continuity |
|---|---|---|---:|---|---:|
| actor weights | absent | absent | no | not reached | STOP |
| actor Adam steps/moments | absent | absent | no | not reached | STOP |
| critic weights | absent | absent | no | not reached | STOP |
| critic Adam steps/moments | absent | absent | no | not reached | STOP |
| ValueNorm | absent | absent | no | not reached | STOP |
| completed/next update | 0 / 1 initial only | 0 / 1 fresh only | not a checkpoint comparison | not reached | STOP |
| LR schedule position | 1 initial only | 1 fresh only | not a checkpoint comparison | not reached | STOP |
| semantic config | configured | configured | checkpoint comparison absent | not reached | STOP |

## I. REAL OPTIMIZER CONTINUITY

Not established. There was no completed Process A optimizer step, saved Adam state, successful load, or tx004.

## J. VALUENORM CONTINUITY

Not established. There was no completed ValueNorm update, save, or load.

## K. PROGRESSION / LR CONTINUITY

Not established. The intended schedule total was 12, but tx001 did not complete and progression remained at the initial boundary. The test-side LR placement caused the first STOP.

## L. POST-LOAD REAL UPDATES

No Process B update transaction started. tx004, tx005, tx006, and tx007 were not started.

| Process | Transaction | Physical steps | Update complete | Learner poisoned | Result |
|---|---:|---:|---:|---:|---|
| A | tx001 | 2 | no | no; process discarded | STOP before update |
| A | tx002 | 0 | no | no | NOT STARTED |
| A | tx003 | 0 | no | no | NOT STARTED |
| B | tx004 | 0 | no | no; load target unmutated and discarded | NOT STARTED |
| B | tx005 | 0 | no | no | NOT STARTED |
| B | tx006 | 0 | no | no | NOT STARTED |

## M. PROCESS QUIESCENCE

PIDs `30844`, `29312`, and parent PID `32672` are inactive. Matching worker count is 0. tx007 was not started. Process cleanup passed, while the overall semantic run remains STOP.

## N. FINAL CHECKPOINT-CONTINUATION VERDICT

**PHASE-B2-T4-CKPT2-STOP-PROCESS-A-UPDATE**

- Process A updates: **0/3**
- Process B updates: **0/3**
- Checkpoint save/load: **0/0 successful**
- Checkpoint generation: **none**
- Real checkpoint continuation: **NOT ESTABLISHED**
- Poison status: **A not poisoned/discarded; B not poisoned/discarded**
- Retry: **not authorized and not performed**
- Production changes after freeze: **0**
- Evaluation/playback: **0**
- R15 / paper-scale training: **not authorized**
- Git add/commit/push: **0/0/0**

The next permissible action is independent GPT review of this STOP package. A new runtime attempt or harness correction requires separate authorization.
