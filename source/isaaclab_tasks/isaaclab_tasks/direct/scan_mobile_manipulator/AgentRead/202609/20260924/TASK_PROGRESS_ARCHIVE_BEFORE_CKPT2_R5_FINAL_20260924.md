# TASK_PROGRESS

## Current status

`B2-T4-CKPT2-R4` is closed as:

`PHASE-B2-T4-CKPT2-R4-STOP-TRANSACTION-LEDGER`

The single authorized R4 attempt was consumed. Retry count is zero and no further R4 attempt is authorized. Independent GPT review is the next gate.

## Latest completed phase

- Repaired the R3 import-namespace side effect through OS-process isolation.
- Completed clean-interpreter and pure production-schema qualification before A.
- Launched one real CUDA/Isaac Process A in a fresh interpreter.
- Proved real package identity, Gym registration, and environment creation.
- Completed and ledgered real tx001.
- Stopped after real tx002 returned with actor step counts `(5, 5, 10)`, which violated the frozen R3-derived ledger expectation `(5, 5, 5)`.
- Denied Process B; no checkpoint save/load occurred.
- Produced final evidence and the required R4 report.

## Active architecture / implementation path

- Historical CKPT2/R1/R2/R3 remain frozen and preserved.
- R4 parent PID 19096, clean PID 26612, pure PID 38384, and A PID 24152 are inactive.
- `ONE_TO_ONE_BOUND`, CASE C, returned `update_id`, and `transaction.real_audit.event_return_compute_count` remain the identity/event-return contracts.
- The final STOP is test-side transaction-ledger adjudication. Evidence does not yet decide whether `(5,5,10)` is valid dynamic actor participation or whether the real update violated a future intended count contract.

## Key files

- R4 harness: `scripts/environments/test_assignment_phase_b2_t4_ckpt2_r4_real_fresh_process_checkpoint_continuation.py`
- Evidence: `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/b2_t4_ckpt2_r4_artifacts/`
- Report: `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R4_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`

## Latest verification

- Expected interpreter: PASS (`C:\isaacenvs\isaac45_harl\python.exe`).
- R4 harness `py_compile`: PASS.
- CKPT1 suite: 6/6 PASS; 25/25 expected negative rejections.
- Pure/runtime process isolation: PASS.
- Process-A real package identity: PASS.
- Process-A environment registration and creation: PASS.
- tx001 ledger/event-return/LR boundary: REAL PASS.
- tx002 ledger predicate: STOP, expected `(5,5,5)`, observed `(5,5,10)`.
- A→B semantic gate: DENY as required.
- Checkpoint saves/loads: 0/0.
- Process quiescence: PASS; matching Python worker count 0.
- Frozen R4 harness hash remains `f330ba2f27ef3fd40cb232853fd9be9d53846e9cbed8973321a691f38bee967d`.

## Known issues / blockers

- The actor-step count contract needs independent review before any new authorization. Do not silently loosen the ledger predicate or treat the observed tuple as automatically valid.
- 3+3 checkpoint continuation, strict load, CUDA restoration after load, and optimizer/ValueNorm/progression continuity are NOT ESTABLISHED.

## Do not do

- Do not launch another CKPT2-R4 attempt or retry this run.
- Do not edit the frozen R4 harness to reinterpret the completed attempt.
- Do not edit historical CKPT2/R1/R2/R3 evidence.
- Do not modify CKPT1 production sources or installed HARL.
- Do not launch R15, evaluation, playback, paper-scale training, or activate the public learned-policy route.
- Do not git add, commit, push, reset, checkout, or clean.

## Next step

Perform an independent GPT review of the R4 evidence, focusing on the tx002 actor-step tuple and the correct authoritative ledger contract. Any repair or new real run requires a new explicit authorization and phase/run identity.

## Detailed reports / archives

- `AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R4_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`
- `AgentRead/202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R4_START_20260923.md`
- `AgentRead/202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R4_FINAL_20260923.md`
- `AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R3_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`
