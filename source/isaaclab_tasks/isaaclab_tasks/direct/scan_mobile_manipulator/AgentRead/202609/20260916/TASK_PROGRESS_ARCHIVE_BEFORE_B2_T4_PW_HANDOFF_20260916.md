# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-16

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 through B2-T3: GPT REVIEW PASS / CLOSED

B2-T4 original: STOPPED / HISTORICAL / NOT COMPLETE
B2-T4-NR: GPT REVIEW PASS / CLOSED
B2-T4-RE1: STOPPED / HISTORICAL / POISONED / NOT COMPLETE
B2-T4-SR: GPT REVIEW PASS / CLOSED
B2-T4-RE2: STOPPED / HISTORICAL / POISONED / NOT COMPLETE
B2-T4-ZD: GPT REVIEW PASS / CLOSED

B2-T4-RE3:
  STOPPED / HISTORICAL / NOT COMPLETE
  NO LEARNER MUTATION / NOT POISONED
  PHASE-B2-T4-RE3-STOP-PRE-ENVIRONMENT-ENTRY-POINT-RESOLUTION-NOT-COMPLETE

B2-T4-EP:
  STOPPED / HISTORICAL / NOT QUALIFIED
  PHASE-B2-T4-EP-STOP-FORMAL-EVIDENCE-PERSISTENCE-ORDERING-NOT-QUALIFIED

B2-T4-EP-P:
  STOPPED / HISTORICAL / NOT QUALIFIED
  PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED

B2-T4-EP-Q:
  GPT REVIEW PASS / CLOSED
  process-quiescence v2 contract only

process-quiescence v2: GPT REVIEW PASS / CLOSED
shutdown marker: DIAGNOSTIC / NON-BLOCKING
immutable EP-P evidence replay under v2: PASS / EP-P HISTORICAL STOP UNCHANGED

B2-T4-RE4:
  STOPPED / POISONED / NOT QUALIFIED
  one authorized fresh formal attempt; no retry
  raw: PHASE-B2-T4-RE4-STOP-FORMAL-WORKER-FAILURE
  refined evidence: PHASE-B2-T4-RE4-STOP-EVIDENCE-PERSISTENCE-PERMISSION-DENIED-AFTER-MUTATION
  tx130 S6 critic-progress atomic replace: PermissionError [WinError 5]
  tx001–tx129 production S10 + ledger qualified; tx130 partial update
checkpoint continuation: NOT ESTABLISHED
long training: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## Latest attempted phase

One fresh B2-T4-RE4 normal-horizon formal worker was launched under the EP-Q v2 supervisor. It failed at tx130 `S6_CRITIC_SEQUENCE` after seven critic optimizer steps and seven ValueNorm updates in that transaction. The failure was a Windows access denial while replacing the temporary critic-progress JSON; the temporary file and all formal artifacts are preserved. The production failure artifact and final receipt mark `partial_update=true` and `route_poisoned=true`. No repair, resume, or second formal process was attempted.

The completed prefix has 129/160 S10-and-ledger-qualified transactions, 128/159 bridges, and 260/320 physical transitions including tx130 collection. It does not qualify the requested 160-transaction horizon. The final worker receipt is a durable **failure** receipt; supervisor Layer A failed and process-quiescence Layer B passed. Worker return code 0 and the absent shutdown marker do not turn a failure receipt into success. The historical original T4, RE1–RE3, EP, and EP-P STOPs remain unchanged; EP-Q remains closed for its narrow process-quiescence contract.

## Evidence and scope

- Formal test-side runner: `scripts/environments/test_assignment_phase_b2_t4_re4_normal_horizon_learned_training_integration.py`; reviewed hash `f04ba511f5d644fcb2bbba61d44e73b6b791301b90a0f9b1c264ebff1af4542e`.
- Final failure receipt: `202609/20260916/b2_t4_re4_artifacts/formal_worker_receipt.json`; SHA-256 `821cdbe63e9143ba6d2209e40e1458daa64e90e4e5f0da2b890d11b3c0df8f7c`.
- Supervisor final result: `202609/20260916/b2_t4_re4_artifacts/formal_supervisor_result.json`; SHA-256 `22d1ba623b524f9e16203fc3699d7aa69bfd36466223a73d00155c77947e9ced`.
- Detailed A–BM report: `202609/20260916/PHASE_B2_T4_RE4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`.
- Source-backed evidence supports only a bounded completed prefix and a poisoned failure at tx130, not RE4 completion or training readiness.

## Latest verification

One initial reset, one environment, one AppLauncher, one persistent learner, one formal worker and supervisor. Pre-runtime Python invocations: 24. Completed-prefix actor backward/optimizer 150/150; critic backward/optimizer 1290/1290; ValueNorm updates 1290. tx130 additionally had seven critic optimizer and seven ValueNorm updates before the persistence failure. No tx131–tx161; no terminal/autoreset before the 300-step maximum. Process quiescence passed all five hard external predicates. No checkpoint I/O, public route activation, evaluation/playback, or long training.

## Repository preservation

Branch `main`; `HEAD`, `origin/main`, and merge-base remain `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing staged monthly migration remains 359 paths with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-RE4-failed-handoff archive is `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE4_FAILED_HANDOFF_20260916.md`, 7,103 bytes, SHA-256 `e6da5a404cac735aebefdda463e46313f7d90d8f5b11f0435fb4d358af0724bf`. Earlier EP-Q archive remains intact.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Known issues / claim boundary

The RE4 failure is after irreversible learner mutation; this worker and learner route are poisoned. The 129 qualified prefix is not a successful normal-horizon RE4 result. EP-Q Layer B establishes only external worker-process quiescence, not that `SimulationApp.close()` returned to Python or all internal callbacks ran. No runtime-quality, checkpoint-continuation, public-route, or long-training claim follows.

## Do not do

Do not retry, resume, patch, or reuse the poisoned RE4 run or edit its formal artifacts. Do not reclassify historical STOPs, begin B2-R6, perform checkpoint I/O, activate the public learned-policy route, run evaluation/playback, or begin long/paper-scale training without new explicit authorization. Do not stage, commit, push, reset, checkout, or clean.

## Next step

Await independent review and a separately authorized recovery design. Do not self-issue RE4 PASS, retry the formal run, or proceed to another phase.

## Detailed reports / archives

- `202609/20260916/PHASE_B2_T4_RE4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`
- `202609/20260916/b2_t4_re4_artifacts/formal_worker_receipt.json`
- `202609/20260916/b2_t4_re4_artifacts/formal_supervisor_result.json`
- `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE4_FAILED_HANDOFF_20260916.md`
- `202609/20260916/PHASE_B2_T4_EP_Q_PROCESS_QUIESCENCE_CONTRACT_RECONCILIATION_REPORT.md`
- `202609/20260916/b2_t4_ep_q_artifacts/old_quiescence_contract.json`
- `202609/20260916/b2_t4_ep_q_artifacts/process_quiescence_contract_v2.json`
- `202609/20260916/b2_t4_ep_q_artifacts/positive_matrix.json`
- `202609/20260916/b2_t4_ep_q_artifacts/negative_matrix.json`
- `202609/20260916/b2_t4_ep_q_artifacts/marker_nonauthority_tests.json`
- `202609/20260916/b2_t4_ep_q_artifacts/ep_p_artifact_identity.json`
- `202609/20260916/b2_t4_ep_q_artifacts/ep_p_formal_quiescence_replay.json`
- `202609/20260916/b2_t4_ep_q_artifacts/source_identity_manifest.json`
- `202609/20260916/b2_t4_ep_q_artifacts/final_result.json`
- `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_EP_Q_HANDOFF_20260916.md`
- `202609/20260916/PHASE_B2_T4_EP_P_FORMAL_EVIDENCE_PERSISTENCE_SUPERVISOR_QUALIFICATION_REPORT.md`
