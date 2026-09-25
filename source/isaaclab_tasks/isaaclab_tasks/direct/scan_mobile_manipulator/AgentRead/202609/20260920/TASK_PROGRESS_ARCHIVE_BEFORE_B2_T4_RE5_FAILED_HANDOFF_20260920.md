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
  GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED
  one authorized fresh formal attempt; no retry
  raw: PHASE-B2-T4-RE4-STOP-FORMAL-WORKER-FAILURE
  classification: PHASE-B2-T4-RE4-STOP-EVIDENCE-PERSISTENCE-PERMISSION-DENIED-AFTER-MUTATION
  tx130 S6 critic-progress atomic replace: PermissionError [WinError 5]
  tx001–tx129 production S10 + ledger qualified; tx130 partial update

B2-T4-PW:
  GPT REVIEW PASS / CLOSED
  PHASE-B2-T4-PW-WINDOWS-EVIDENCE-PERSISTENCE-ATOMIC-WRITE-ROBUSTNESS-QUALIFIED-AWAITING-GPT-REVIEW
  pure Windows/NTFS persistence contract, not RE5
  failure class established / specific RE4 lock owner unresolved
  canonical future helper: b2_t4_pw_immutable_progress_v1
B2-T4-RE5: EXPLICITLY AUTHORIZED / PREFLIGHT IN PROGRESS / FORMAL NOT STARTED
checkpoint continuation: NOT ESTABLISHED
long training: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## Latest completed phase

PW is now GPT REVIEW PASS / CLOSED. It traced the frozen RE4 tx130 `PermissionError [WinError 5]` to `os.replace` of a complete, fsynced, closed `critic_progress.json.tmp` over an existing event-27 destination. The event-28 temp is parseable; the seven critic optimizer steps and seven ValueNorm updates remain irreversible. A held-open Windows destination and an independent rapid reader reproduced the same failure family with the exact current helper. The historical RE4 lock owner is not identifiable from retained evidence.

The new test-side helper uses immutable per-progress JSON, unique fsynced temp, same-volume atomic no-overwrite hard-link publication, immediate readback and digests. It does not weaken fail-closed observer semantics or change production S10/ledger authority. Expected current critic-progress writes: 41 per transaction, `W_expected_160=6,560`. Frozen fresh processes 2 and 3 each passed 65,600 writes over 1,600 evidence-only transactions (0 unexpected PermissionErrors, missing/duplicate records, digest mismatches, or successful-path temp residue). A third earlier process also passed but is additional diagnostic evidence. The 160-tx simulation, 28-event tx130 payload copy replay, and 19/19 fail-closed negative matrix passed. PW did not launch Isaac, environment, or learner.

## Active implementation and scope

- New reusable test-only helper: `scripts/environments/_assignment_phase_b2_t4_windows_evidence_persistence.py` (SHA-256 `e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b`).
- Pure qualification runner: `scripts/environments/test_assignment_phase_b2_t4_pw_windows_evidence_persistence.py` (SHA-256 `c2b1a3fa30922c43bb740faef297ef15a4367149f13afcbf92ac4634052fb725`); paced-reproduction and field-classification scripts are listed in the PW source manifest.
- PW report: `202609/20260916/PHASE_B2_T4_PW_WINDOWS_EVIDENCE_PERSISTENCE_ATOMIC_WRITE_ROBUSTNESS_QUALIFICATION_REPORT.md`; machine evidence: `202609/20260916/b2_t4_pw_artifacts/`.
- RE5 has separate authorization for one fresh formal attempt, conditional on its own preflight and exact-runner readiness. No current learner route was changed by PW.

## Latest verification

Approved interpreter `C:\isaacenvs\isaac45_harl\python.exe`; 18 pure/static Python invocations. Relevant `py_compile` PASS. Three repaired stress processes each passed 65,600 writes; frozen final pair wrote 131,200 records / 2,698,151,252 bytes with all integrity and residue gates zero. Current-helper isolated held-target and concurrent-reader failures reproduced; repaired held-previous-record test passed. tx130 payload replay and 160-tx simulation passed. Fourteen key historical RE4 files matched prior length/SHA-256. Production modifications 0; RE4 harness modifications 0; AppLauncher/environment/resets/physical steps/learner constructions/mutations/checkpoint/public/evaluation: all 0.

## Repository preservation

Branch `main`; `HEAD`, `origin/main`, and merge-base remain `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing staged monthly migration remains 359 paths with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-PW-handoff archive is `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_PW_HANDOFF_20260916.md`, 7,141 bytes, SHA-256 `ce97cd04d4687a13aff7c16ea033bbe91bdd0578002ef91c515c6eca5d1b50a0`. Earlier RE4 and EP-Q archives remain intact.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Known issues / claim boundary

RE4 remains a poisoned STOP after irreversible mutation; PW does not reclassify or resume it. PW establishes a pure local-NTFS process-crash persistence contract, not power-loss directory durability, non-NTFS portability, or an identified RE4 lock owner. RE4's 129-transaction completed prefix is not a successful normal-horizon training qualification. No runtime-quality, checkpoint-continuation, public-route, or long-training claim follows.

## Do not do

Do not retry, resume, patch, or reuse poisoned RE4 or edit its formal artifacts. Do not self-issue RE5 GPT REVIEW PASS or launch the sole RE5 formal worker before its required preflight and exact-runner readiness pass. Do not start B2-R6, perform checkpoint I/O, activate the public route, evaluate/play back, or begin long training. Do not stage, commit, push, reset, checkout, or clean.

## Next step

Prepare RE5 static preflight and exact-runner readiness. Its one fresh formal attempt may start only after both pass, must bind the exact reviewed PW helper, and must preserve RE4's historical poisoned STOP.

## Detailed reports / archives

- `202609/20260916/PHASE_B2_T4_PW_WINDOWS_EVIDENCE_PERSISTENCE_ATOMIC_WRITE_ROBUSTNESS_QUALIFICATION_REPORT.md`
- `202609/20260916/b2_t4_pw_artifacts/final_result.json`
- `202609/20260916/b2_t4_pw_artifacts/repaired_stress_run_02.json`
- `202609/20260916/b2_t4_pw_artifacts/repaired_stress_run_03.json`
- `202609/20260916/b2_t4_pw_artifacts/tx130_payload_replay.json`
- `202609/20260916/b2_t4_pw_artifacts/source_identity_manifest.json`
- `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_PW_HANDOFF_20260916.md`
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
