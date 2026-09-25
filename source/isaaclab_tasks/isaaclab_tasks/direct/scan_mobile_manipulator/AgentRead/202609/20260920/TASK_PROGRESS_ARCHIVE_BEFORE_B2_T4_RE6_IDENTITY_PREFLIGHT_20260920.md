# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-20

## Current status

B2-R0–R7, B2-T0–T3, and B2-T4-NR/SR/ZD/EP-Q/PW remain GPT REVIEW PASS / CLOSED. Earlier historical STOPs remain unchanged; RE4 is GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED.

B2-T4-RE5: **GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED**. Its raw formal classification remains `PHASE-B2-T4-RE5-STOP-FORMAL-WORKER-FAILURE`; refined handoff classification remains `PHASE-B2-T4-RE5-STOP-W2-MULTI-UPDATE-COMPLETION-WITNESS-NOT-ESTABLISHED-AFTER-MUTATION`. Formal `partial_update=true`, `route_poisoned=true`; the learner must never be resumed, repaired, checkpointed or reused.

B2-T4-W2E: **COMPLETE / AWAITING GPT REVIEW**, not self-reviewed PASS. This is an offline versioned evidence-contract reconciliation, not RE6. The old RE5 W2=`None` was reproduced from 0 recorded `task_claimed` versus 22 `task_completed` events. Production B1/P2 claim authority is a StateStore ownership/task-state mutation, not a canonical `task_claimed` lifecycle event. New pure v2 retrospective replay found 12 valid chains among 29 candidates; the deterministic first is env 1/robot 1/task 10, claim tx12/step23 → qualified bridges tx12–14 → completion/clear tx15/step30 → reopen tx16/step31. This does **not** reclassify RE5 or unpoison its learner.

Checkpoint continuation: NOT ESTABLISHED. RE6, B2-R6, long/paper-scale training: NOT AUTHORIZED. Public learned-policy route: DORMANT / BLOCKED.

## Latest work and evidence

The [W2E report](202609/20260920/PHASE_B2_T4_W2E_CLAIM_MULTI_UPDATE_COMPLETION_EVIDENCE_CONTRACT_RECONCILIATION_REPORT.md) has sections A–AL, claim-authority and old-vs-v2 tables, and all 12 retrospective valid chains. [W2E artifacts](202609/20260920/b2_t4_w2e_artifacts/) include source/artifact identities, old replay, v2 contract and 29-candidate inventory, selected witness, 3/3 positive and 18/18 negative synthetic cases, and final result. The new pure test-side selector and offline replay/matrix script live at `scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py` and `scripts/environments/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py`.

Historical [RE5 report](202609/20260916/PHASE_B2_T4_RE5_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) and 14 consumed formal artifact hashes were checked before and after W2E and remained byte-identical. RE5 still has 160/160 S10/ledger, 159/159 bridges, W1 and W3–W7 individually passing, W2 absent, Layer A failure and Layer B pass. PW remains GPT REVIEW PASS / CLOSED within its prior scope.

## Verification and repository boundary

Approved interpreter `C:\isaacenvs\isaac45_harl\python.exe` verified. Changed pure Python files passed `py_compile`; four offline matrix/replay runs passed. Across W2E: 9 pure/static Python invocations, 4 old W2 replays, 84 v2 reconciler calls; final matrix 3 positive and 18 negative cases, unexpected negative PASS 0. AppLauncher/environment/physical steps/learner constructions/mutations/checkpoint I/O/public activation/evaluation-playback: all 0. Production semantic and historical RE5 modifications: 0/0.

Branch `main`; HEAD/origin/main/merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing 359 staged monthly-migration paths remain intact; staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. Git add/commit/push: 0/0/0.

Before this rewrite, a byte-exact 4,419-byte [TASK_PROGRESS archive](202609/20260920/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_W2E_HANDOFF_20260920.md) was created, SHA-256 `4437f7aee07d5700becc6231c4a90f297e6e7b8a3b8bac01dba69217a8b42b94`. Prior [RE5 failed-handoff archive](202609/20260920/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE5_FAILED_HANDOFF_20260920.md) remains intact.

## Next decision

Await independent GPT review of W2E's source-backed P2/B1 claim contract and retrospective witness. Do not rerun RE5, launch RE6, construct Isaac/learner runtime, start tx161 or B2-R6, checkpoint, activate the public route, evaluate/play back, stage or commit without separate explicit authorization.
