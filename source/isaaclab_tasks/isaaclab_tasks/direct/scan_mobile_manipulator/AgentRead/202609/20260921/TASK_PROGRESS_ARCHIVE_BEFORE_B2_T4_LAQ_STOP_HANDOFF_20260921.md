# Lifecycle-aware Dynamic MRTA — TASK_PROGRESS

Updated: 2026-09-20

## Current classification

Phase B2-T4-RE6-R3: **STOP / POISONED / RETAINED / NOT QUALIFIED**. Final independent classification: `PHASE-B2-T4-RE6-R3-STOP-INCOMPLETE-LAYER-A-WORKER-RECEIPT-AFTER-MUTATION`. One authorized fresh formal supervisor and worker ran, with no retry. The worker completed 160 learned transactions and the original supervisor reported Layer A and EP-Q Layer B PASS. A subsequent independent audit found that inherited mandatory worker-receipt Layer-A fields were left at template zeros/empty values and the custom R3 supervisor omitted their RE5 checks. Thus the reported PASS does not establish the required unchanged gate equivalence. After irreversible learner mutation, qualification flags are `partial_update=true`, `route_poisoned=true`; never reuse this learner or attempt. Preserve the original supervisor/worker receipts unchanged alongside the [independent STOP audit](202609/20260920/b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json) and [failure receipt](202609/20260920/b2_t4_re6_r3_artifacts/failure_receipt.json).

PPQ-V2 remains **GPT REVIEW PASS / CLOSED** for its reviewed fresh-run receipt contract. PPQ-v1 remains GPT REVIEW PASS / CLOSED for historical RE6-R1 offline scope only. RE6-R1 is historical poisoned STOP; RE6-R2 is historical pre-runtime STOP with zero formal attempts and no poison. RE5 and RE6 historical STOPs are unchanged. Earlier B2-R0–R7, B2-T0–T3 and T4-NR/SR/ZD/EP-Q/PW/W2E/W2I remain GPT REVIEW PASS / CLOSED in their reviewed scopes.

Normal-horizon learned-training integration is **NOT QUALIFIED** after this attempt. Checkpoint continuation is **NOT ESTABLISHED**; long/paper-scale training is **NOT AUTHORIZED**; the public learned-policy route remains **DORMANT / BLOCKED**. Do not launch a retry or advance to the next phase without separate authorization.

## B2-T4-RE6-R3 evidence and boundary

The frozen pure R3 normalizer SHA-256 is `316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3`; the R3 harness SHA-256 is `60301bdb94515019b6d57c54421428afc568c68acc708f45a5f05e3dc6dc5ae9`. Historical normalization reconstructed RE6-R1 160/320/159, W2E 29/12, task completions 22, coverage 11, terminal events 2 and PW 6,560/640 without reclassifying it. A different synthetic fresh variant and 14/14 negative STOP cases passed. The full synthetic PPQ-V2 chain used actual reviewed PW file operations for 7,200 records and validated publication order. One final static readiness replay returned PASS, but it missed the inherited worker-receipt projection gap.

Fresh raw runtime evidence is positive within its scope: AppLauncher/environment/reset/persistent learner 1/1/1/1; physical 320; S10/transactions 160/160; bridges 159; tx161 not started; actor backward/step 165/165; critic backward/step 1,600/1,600; ValueNorm updates 1,600; PW critic/actor-factor 6,560/640 with zero PW faults; W1–W7 PASS; W2E 29 candidates/12 valid, env 1/robot 1/task 10, tx12→15→16; task completions 22, coverage 11, terminal/autoreset 2, post-reset learned transaction true; event returns 160, stock `compute_returns` 0. The PPQ-V2 candidate receipt passed its own schema, durable readback/digest and post-validation witness publication. EP-Q Layer B passed (exit 0, PID absent, matching workers empty). These facts do **not** cure the incomplete inherited Layer-A gate.

Exact defect: the original [worker receipt](202609/20260920/b2_t4_re6_r3_artifacts/formal_worker_receipt.json) says environment/reset/learner `0/0/0`, event returns 0, task completions 0, empty learner/contract maps and `final_in_worker_quiescence_pass=false`; raw engine evidence says `1/1/1`, 160 and 22. The original [supervisor result](202609/20260920/b2_t4_re6_r3_artifacts/formal_supervisor_result.json) checked a reduced custom Layer-A set and returned PASS. Those original artifacts remain untouched. The [A–BS report](202609/20260920/PHASE_B2_T4_RE6_R3_PPQ_V2_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) explains the superseding STOP and source map.

## Preservation and next authorized work

No production lifecycle/learner source, PPQ-v1/v2, W2E/W2I/PW reviewed helper, or historical RE5/RE6/R1/R2 attempt was modified. The pre-existing 359 staged monthly migration entries remained unchanged; git add/commit/push were 0/0/0. No model checkpoint, public activation, evaluation or playback was performed. The fresh R3 artifact namespace is [here](202609/20260920/b2_t4_re6_r3_artifacts/).

Before any separately authorized new attempt, design and qualify a full worker-receipt/Layer-A predicate-preserving replacement, with an explicit pre-runtime replay that fails on exactly the mismatches seen here. Do not repair this attempt in place, reuse its learner, or treat the original supervisor PASS as final qualification. Independent GPT review should inspect both the positive PPQ-V2/runtime evidence and the superseding STOP audit.

Byte-exact archives: [before R3 start](202609/20260920/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE6_R3_20260920.md), 6,789 bytes, SHA-256 `9bce09e70177c947592b311754045676082568919cfcc298e5f418e1c1848ee6`; [before this final rewrite](202609/20260920/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE6_R3_FINAL_20260920.md), 7,593 bytes, SHA-256 `2711cf64e70bc227f879d7b1c4a9f14319b6c39e45122176cf87a3c369548b9f`.
