# TASK_PROGRESS

## Current status

`B2-T4-CKPT2-R6` is explicitly authorized as:

`PRE-RUNTIME RECEIPT-BINDING REPAIR`

R5 is independently reviewed as a historical pre-mutation test-harness config-binding STOP with no learner mutation and no poison. R6 may repair only the receipt binding and perform one fresh real 3+3 checkpoint-continuation attempt; retry count is zero.

## Latest completed phase

- Independently confirmed R4 as a historical test-side fixed-predicate STOP, not a learner defect.
- Established `B2RActorUpdatePlanV1.expected_*_count_by_actor` as the frozen per-transaction actor-count authority.
- Passed CKPT1 6/6, CKPT1 negative 25/25, actor-plan positive 5/5, and actor-count negative 12/12 pure qualification.
- Retrospectively reconciled RE1 plan/observed/Adam tuples `(5,5,5)`, `(5,5,10)`, and `(10,5,5)`.
- Launched one real CUDA/Isaac Process A in a fresh interpreter.
- Proved real package identity, Gym registration, and environment creation.
- Stopped in tx001 at S5 pre-mutation receipt emission because the new R5 harness treated the frozen `B2RResolvedConfigV1` payload value as though it had to be a `Mapping` and therefore derived `epoch_count=0`.
- Confirmed frozen expected counts `((0,5),(1,5),(2,5))` were available, while actor/critic/ValueNorm mutation counts all remained zero.
- Denied Process B; no transaction completed and no checkpoint save/load occurred.
- Produced final STOP evidence and the required R5 report.

R6 startup has captured repository authority and is preparing a new isolated harness. No R6 Process A has started.

## Active architecture / implementation path

- Historical CKPT2/R1/R2/R3/R4/R5 remain frozen and preserved.
- R5 parent PID 29060 and A PID 23952 are inactive; Process B was not launched.
- `ONE_TO_ONE_BOUND`, CASE C, returned `update_id`, and `transaction.real_audit.event_return_compute_count` remain the identity/event-return contracts.
- The authoritative count contract is frozen-plan expected counts versus returned per-actor observed counts; fixed `(5,5,5)` is rejected as an R4-only historical harness predicate.
- R6 will consume `expected_backward_count_by_actor` and `expected_optimizer_step_count_by_actor` directly from the frozen-plan observer fields. `resolved_config` is provenance only and cannot determine expected counts.

## Key files

- R5 harness: `scripts/environments/test_assignment_phase_b2_t4_ckpt2_r5_real_fresh_process_checkpoint_continuation.py`
- Evidence: `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260924/b2_t4_ckpt2_r5_artifacts/`
- Report: `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260924/PHASE_B2_T4_CKPT2_R5_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`

## Latest verification

- Expected interpreter: PASS (`C:\isaacenvs\isaac45_harl\python.exe`).
- R5 harness `py_compile`: PASS before freeze.
- CKPT1 suite: 6/6 PASS; 25/25 expected negative rejections.
- Actor-plan qualification: 5/5 positive; 12/12 expected negative STOP.
- Historical dynamic-plan/Adam consistency: PASS.
- Pure/runtime process isolation: PASS; pure child exited before A.
- Process-A real package identity: PASS.
- Process-A environment registration and creation: PASS.
- tx001 frozen expected counts: `((0,5),(1,5),(2,5))` available before mutation.
- tx001 mutation counts before failure: actor backward `(0,0,0)`, actor steps `(0,0,0)`, critic `0`, ValueNorm `0`.
- tx001 completion/ledger: 0/1 and 0 rows; stopped in R5 harness pre-mutation receipt logic.
- A→B semantic gate: DENY as required.
- Checkpoint saves/loads: 0/0.
- Route poisoned: false; partial update: false.
- Process quiescence: PASS; matching R5 Python worker count 0.
- Frozen R5 harness hash remains `e6546bdae034a7abb18d1ad70e16a4e2f5eab897251ba4561acf2e5d604fd039`.

## Known issues / blockers

- The R5 pre-mutation receipt callback mishandled the frozen `B2RResolvedConfigV1` dataclass at the direct observer boundary. The frozen plan counts themselves were present and internally consistent.
- 3+3 checkpoint continuation, strict load, CUDA restoration after load, and optimizer/ValueNorm/progression continuity are NOT ESTABLISHED.

## Do not do

- Do not launch another CKPT2-R5 attempt or retry this run.
- Do not edit the frozen R5 harness to reinterpret the completed attempt.
- Do not edit historical CKPT2/R1/R2/R3/R4 evidence.
- Do not modify CKPT1 production sources or installed HARL.
- Do not launch R15, evaluation, playback, paper-scale training, or activate the public learned-policy route.
- Do not git add, commit, push, reset, checkout, or clean.

## Next step

Complete R6 pure receipt qualification, freeze the new harness, then execute the single authorized fresh A/B attempt only if every preflight gate passes.

## Detailed reports / archives

- `AgentRead/202609/20260924/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R6_START_20260924.md`
- `AgentRead/202609/20260924/PHASE_B2_T4_CKPT2_R5_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`
- `AgentRead/202609/20260924/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R5_FINAL_20260924.md`
- `AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R4_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`
- `AgentRead/202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R4_START_20260923.md`
- `AgentRead/202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R4_FINAL_20260923.md`
- `AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R3_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`
