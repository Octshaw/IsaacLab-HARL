# Phase B2-T4-RE5 normal-horizon learned-training integration qualification report

Formal run: 2026-09-16. Retrospective closure: 2026-09-20. **STOP / POISONED / NOT QUALIFIED.** The sole fresh RE5 worker completed 160 production S10 transactions, 160 append-only transaction rows, 159 bridges, and all planned PW records, but the required W2 multi-update-completion witness was `None`. The inherited RE3 postprocessor raised `REQUIRED-WITNESS-GATE` after all learner mutations. This is not a PASS, a repair, or authorization to continue. The immutable formal supervisor classification is `PHASE-B2-T4-RE5-STOP-FORMAL-WORKER-FAILURE`; the source-backed handoff refinement is `PHASE-B2-T4-RE5-STOP-W2-MULTI-UPDATE-COMPLETION-WITNESS-NOT-ESTABLISHED-AFTER-MUTATION`.

Machine evidence is under [b2_t4_re5_artifacts](b2_t4_re5_artifacts/). The formal [worker receipt](b2_t4_re5_artifacts/formal_worker_receipt.json), [supervisor result](b2_t4_re5_artifacts/formal_supervisor_result.json), and [final result](b2_t4_re5_artifacts/final_result.json) are preserved unmodified. [Failure adjudication](b2_t4_re5_artifacts/re5_failure_adjudication.json) and [PW reconciliation](b2_t4_re5_artifacts/pw_campaign_reconciliation.json) are explicitly postmortem diagnostics, not retroactive worker success artifacts.

## A. repository authority

Starting branch `main`; HEAD, `origin/main`, and merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. Before RE5 edits, full `git status --porcelain=v1 -uall` had 1,614 lines and UTF-8/LF SHA-256 `236abd9f7b5d3da88419d828ccc43084acb8fdba7f5966fda2402bacdf8a3740`. The 359 pre-existing staged migration paths retained exact `git ls-files --stage` SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` after the run. The prior reviewed monthly path-set SHA-256 is `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`; its old calculation recipe was not independently reconstructed here. See [repository authority](b2_t4_re5_artifacts/re5_repository_authority.json). No Git add, commit, push, reset, checkout, or clean was run.

## B. reviewed starting authority

B2-R0–R7, B2-T0–T3, NR, SR, ZD, EP-Q, and PW entered RE5 as reviewed closed. Original T4, RE1–RE3, EP, EP-P, and RE4 retained their historical STOPs. This authorization covered one fresh RE5 formal attempt only.

## C. historical RE4 preservation

RE4 remains `GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED`, with tx130 seven critic optimizer steps and seven ValueNorm updates before `WinError 5`. The RE4 harness SHA-256 remained `f04ba511f5d644fcb2bbba61d44e73b6b791301b90a0f9b1c264ebff1af4542e`; its report and preserved tx130 final/temp hashes matched the frozen preflight identities. No RE4 learner, process, artifact path, or update ID was used as RE5 runtime state. The tx130 comparison reads RE4 evidence only.

## D. PW authority

PW is `GPT REVIEW PASS / CLOSED` for the NTFS same-volume immutable progress contract. It is evidence persistence, not a replacement for production S10 or the transaction ledger. The exact reviewed helper was bound to RE5; the PW pure stress evidence was not counted as RE5 training.

## E. PW helper identity

`_assignment_phase_b2_t4_windows_evidence_persistence.py` SHA-256 remained `e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b` before and after the formal run. The new harness imports that helper rather than reimplementing no-overwrite publication. [Static authority](b2_t4_re5_artifacts/re5_static_authority.json) records this gate.

## F. NTFS/same-volume qualification

The actual E: artifact volume was NTFS (`\\?\Volume{1c0fb2c1-65d6-4959-a684-3afeb68b8c4a}\`). The helper derives its unique temp with `final.with_name(...)` and publishes with `os.link(temp, final)`, so temp and final reside in the same directory/volume. [Filesystem precondition](b2_t4_re5_artifacts/filesystem_precondition.json): `NTFS_pass`, `temp_final_same_volume`, and `helper_same_directory_temp_contract` all true. No non-NTFS or power-loss durability claim follows.

## G. production source identities

Frozen full-transaction, real-adapter, and environment SHA-256 values remained respectively `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`, `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`, and `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363`. Production semantic modifications: 0.

## H. RE5 harness identity

The new test-side `test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py` and `_assignment_phase_b2_t4_re5_progress_binding.py` were frozen in [static authority](b2_t4_re5_artifacts/re5_static_authority.json). Historical RE4/RE3/PW sources were not patched. The RE3 engine remained the inherited test-side training execution substrate; RE5 rebound only its generated progress-observer function in the fresh worker namespace.

## I. old/new progress-path binding audit

[Binding map](b2_t4_re5_artifacts/re5_progress_persistence_binding.json) records exactly 41 critic and 4 actor/factor progress events per transaction. Both old fixed-target per-progress `_atomic_json` calls were removed from the RE5 generated function; S10's durable-artifact references point at the final immutable PW records. No duplicate old/new publication or old mutable critic/actor progress file was observed. One-shot S10, pre-mutation, failure, and campaign evidence writes retain their separate existing authority.

## J. RE5 Layer-A

The RE5 training-aware digest-checked receipt binds run/PID, source/config/PW/filesystem identities, learner and environment counts, PW populations, witnesses, poison state, and pre-App-close persistence. Synthetic success/failure and missing/malformed/stale negatives passed preflight. The actual [formal receipt](b2_t4_re5_artifacts/formal_worker_receipt.json) is a valid **failure** receipt: `status=failure`, `failure_stage=postprocess_and_witness_gates`, `partial_update=true`, `route_poisoned=true`. Actual Layer-A success: **FAIL**.

## K. EP-Q Layer-B

The reviewed EP-Q external predicate was applied independently. Wait completed, no timeout, worker return code 0, original PID absent, and no matching formal worker: Layer-B **PASS**. Exit code 0 and process quiescence cannot override the failed Layer A. Shutdown marker was absent and diagnostic only.

## L. pre-runtime qualification

The final frozen preflight [summary](b2_t4_re5_artifacts/re5_preflight_summary.json) passed approved interpreter, `py_compile`, production and PW hashes, NTFS/same-volume, import ordering, PW positive/duplicate/out-of-order/stale-temp cases, actual bound-callback replay on retained RE4 tx129 event payloads, after-tx bookkeeping replay, receipt/Layer-B negatives, NR/SR/ZD, I5b, LD, controlled R5, geometry, CG, ValueNorm, T2/T3 observer, and static/private/public guards. The frozen preflight process plus its launched children counted 14 Python invocations. Additional earlier development/read-only probes were performed; their exact combined turn-wide count was not durably recorded. No preflight AppLauncher was started.

## M. exact-runner readiness

The sole final [readiness replay](b2_t4_re5_artifacts/re5_runner_readiness_replay.json) passed retained RE1 SR/bookkeeping, retained RE2 ZD, real-payload bound callback PW critic 41/41 and actor/factor 4/4, one synthetic transaction, RE5 Layer-A receipt, and EP-Q Layer B. Readiness replay count: 1 PASS. This did not prove W2 would occur in the formal trajectory.

## N. CUDA/CUBLAS

Exactly one pre-AppLauncher `torch.mm` probe on `cuda:0` passed; retries 0. [CUDA receipt](b2_t4_re5_artifacts/re5_cuda_cublas_readiness.json) is diagnostic infrastructure readiness, not a training result.

## O. canonical import ordering

The fresh worker checked no task-package contamination before AppLauncher, then performed AppLauncher → canonical `import isaaclab_tasks` → `gym.spec` → exact package/defining-class identity → `gym.make`. Entry point passed. No environment-registration source was changed.

## P. fresh formal process

One supervisor launched one fresh worker, PID `26096`, with run ID `b2-t4-re5-20260916-formal01-ab67c2b8ba0c40b8bcdef425687fb20a`. Formal workers/retries: 1/0. AppLauncher, environment, initial reset, and persistent learner were each constructed once. The worker and matching formal-worker set are now absent. No second worker was launched after the STOP.

## Q. runtime configuration

[Process authority](b2_t4_re5_artifacts/re5_process_config_authority.json) binds `Isaac-Scan-Mobile-Manipulator-Direct-v0`, `event_gated_local_mrta`, `cuda:0`, T/E/M/N `2/2/3/12`, actor/critic epochs-minibatches `5/2`, ValueNorm enabled, `fixed_order=false`, episode length 30.0 s, max 300, and 0.1 s control step. No short-horizon override.

## R. horizon separation

T=2 was the learner collection length; 30.0 s/300 steps remained the environment horizon. The worker collected 320 physical transitions. A genuine TIME_LIMIT/autoreset appeared at tx150 (two env events), and tx151 trained after the reset. These bounded observations do not overcome W2 failure.

## S. PW critic progress contract

Every tx001–tx160 has 41 ordered, digest-validated critic PW records: 6,560/6,560. Each record binds run/tx/stage/side/sequence and cumulative event payload; the final PW record is the S10 referenced critic progress artifact. Publication/readback or integrity failures were not observed.

## T. PW actor/factor progress contract

Source-bound cadence is three actor-segment callbacks plus one sequence-complete callback per transaction, 4 × 160 = 640. Retrospective full verification found 640/640 immutable actor-side PW records and zero old mutable actor/factor progress files.

## U. transaction success definition

Production S10 plus mandatory append-only transaction bookkeeping/readback is the transaction authority. By that bounded definition, tx001–tx160 have S10 and ledger rows. This is **not** overall RE5 qualification: W2 and Layer A failed after learner mutation. PW records alone were never promoted into S10 authority.

## V. transaction inventory

There are 160 distinct update IDs, one persistent learner, 320 physical transitions, 160 S10 artifacts, 160 transaction ledger rows, and 159 bridges. tx161 was not started. The raw RE3 training-engine artifact says `status=passed` for its local transaction slice; it is not a RE5 final success result because the required postprocessor witness gate then failed.

## W. transaction status table

All rows below have production S10 and ledger qualification, but no row or range grants overall RE5 PASS. `PW` means that transaction's 4 actor/factor and 41 critic records passed verification. Bridge is to the next qualified transaction.

| Tx | S10 | Ledger | Episode gen | Policy | Continuation | Zero-DVM actors | Terminal | Completion | PW integrity | Bridge |
|---:|---|---|---:|---:|---:|---:|---|---:|---|---|
| 001 | yes | yes | 0 | 6 | 6 | 0 | no | 0 | PASS | yes |
| 002 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 003 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 004 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 005 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 006 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 007 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 008 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 009 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 010 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 011 | yes | yes | 0 | 1 | 11 | 2 | no | 2 | PASS | yes |
| 012 | yes | yes | 0 | 1 | 11 | 2 | no | 0 | PASS | yes |
| 013 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 014 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 015 | yes | yes | 0 | 0 | 12 | 3 | no | 1 | PASS | yes |
| 016 | yes | yes | 0 | 3 | 9 | 1 | no | 1 | PASS | yes |
| 017 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 018 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 019 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 020 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 021 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 022 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 023 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 024 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 025 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 026 | yes | yes | 0 | 1 | 11 | 2 | no | 2 | PASS | yes |
| 027 | yes | yes | 0 | 1 | 11 | 2 | no | 0 | PASS | yes |
| 028 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 029 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 030 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 031 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 032 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 033 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 034 | yes | yes | 0 | 1 | 11 | 2 | no | 1 | PASS | yes |
| 035 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 036 | yes | yes | 0 | 0 | 12 | 3 | no | 1 | PASS | yes |
| 037 | yes | yes | 0 | 1 | 11 | 2 | no | 0 | PASS | yes |
| 038 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 039 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 040 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 041 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 042 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 043 | yes | yes | 0 | 2 | 10 | 1 | no | 3 | PASS | yes |
| 044 | yes | yes | 0 | 1 | 11 | 2 | no | 0 | PASS | yes |
| 045 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 046 | yes | yes | 0 | 1 | 11 | 2 | no | 1 | PASS | yes |
| 047 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 048 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 049 | yes | yes | 0 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 050 | yes | yes | 0 | 0 | 12 | 3 | no | 1 | PASS | yes |
| 051 | yes | yes | 0 | 2 | 10 | 2 | no | 0 | PASS | yes |
| 052 | yes | yes | 0 | 2 | 10 | 2 | no | 0 | PASS | yes |
| 053 | yes | yes | 0 | 3 | 9 | 1 | no | 1 | PASS | yes |
| 054 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 055 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 056 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 057 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 058 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 059 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 060 | yes | yes | 0 | 1 | 9 | 2 | no | 1 | PASS | yes |
| 061 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 062 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 063 | yes | yes | 0 | 1 | 9 | 2 | no | 1 | PASS | yes |
| 064 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 065 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 066 | yes | yes | 0 | 0 | 10 | 3 | no | 0 | PASS | yes |
| 067 | yes | yes | 0 | 0 | 10 | 3 | no | 1 | PASS | yes |
| 068 | yes | yes | 0 | 1 | 8 | 2 | no | 1 | PASS | yes |
| 069 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 070 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 071 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 072 | yes | yes | 0 | 0 | 8 | 3 | no | 1 | PASS | yes |
| 073 | yes | yes | 0 | 2 | 6 | 2 | no | 0 | PASS | yes |
| 074 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 075 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 076 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 077 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 078 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 079 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 080 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 081 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 082 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 083 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 084 | yes | yes | 0 | 1 | 7 | 2 | no | 1 | PASS | yes |
| 085 | yes | yes | 0 | 1 | 7 | 2 | no | 0 | PASS | yes |
| 086 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 087 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 088 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 089 | yes | yes | 0 | 0 | 8 | 3 | no | 0 | PASS | yes |
| 090 | yes | yes | 0 | 0 | 8 | 3 | no | 1 | PASS | yes |
| 091 | yes | yes | 0 | 0 | 6 | 3 | no | 0 | PASS | yes |
| 092 | yes | yes | 0 | 0 | 6 | 3 | no | 0 | PASS | yes |
| 093 | yes | yes | 0 | 0 | 6 | 3 | no | 0 | PASS | yes |
| 094 | yes | yes | 0 | 0 | 6 | 3 | no | 1 | PASS | yes |
| 095 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 096 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 097 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 098 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 099 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 100 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 101 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 102 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 103 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 104 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 105 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 106 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 107 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 108 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 109 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 110 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 111 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 112 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 113 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 114 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 115 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 116 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 117 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 118 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 119 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 120 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 121 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 122 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 123 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 124 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 125 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 126 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 127 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 128 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 129 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 130 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 131 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 132 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 133 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 134 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 135 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 136 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 137 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 138 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 139 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 140 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 141 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 142 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 143 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 144 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 145 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 146 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 147 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 148 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 149 | yes | yes | 0 | 0 | 4 | 3 | no | 0 | PASS | yes |
| 150 | yes | yes | 0 | 6 | 2 | 0 | yes | 0 | PASS | yes |
| 151 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 152 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 153 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 154 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 155 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 156 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 157 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 158 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 159 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | yes |
| 160 | yes | yes | 1 | 0 | 12 | 3 | no | 0 | PASS | — |

## X. episode/update timeline

Initial reset created generation 0. Every tx collected two physical transitions without learner-boundary environment resets. tx150 reached the normal-horizon TIME_LIMIT/autoreset, and tx151 onward used the next episode generation. The [episode/update timeline ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_episode_update_timeline_ledger.jsonl) and 159 bridge rows preserve the physical/update order.

## Y. lifecycle decision summary

Across all 1,920 robot-step rows: policy-required 39, forced-continuation 1,294, forced-noop nondecision 587; lifecycle policy-call fault counters 0. The [lifecycle ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_lifecycle_task_progress_ledger.jsonl) records 22 `task_completed` and zero `task_claimed` event entries. Zero recorded claim events is an evidence statement, not proof that ownership was never claimed in runtime.

## Z. zero-DVM statistics

The transaction ledger contains 452 zero-DVM actor/transaction pairs and 139 all-zero-DVM transactions. This includes real continuation-only actor populations; a zero-DVM actor is not silently treated as missing evidence.

## AA. all-zero-DVM transactions

For the 139 all-zero-DVM rows, the source-bound actor plan and S10 records show zero actor backward/optimizer steps and an identity factor contribution, while critic/ValueNorm/event returns continue. They remain a bounded completed-prefix observation inside the poisoned overall RE5 attempt.

## AB. actor plans

Actor population is `active AND DVM`; ledger actor backward/optimizer totals are 165/165. Per-transaction production receipts and controlled plan checks were reached, including valid zero plans. No separate overall actor-plan qualification is asserted after W2 failure.

## AC. actor evidence reconciliation

The source-bound actor-evidence ledger has 160 rows and the W3 witness passed. The final postprocessor recorded actor evidence reconciliation 160/160, faults 0. This does not fill the missing W2 claim-event chain.

## AD. factor audits

The inherited full transactions reached their reviewed per-actor factor audit and S10; 160 × 3 actor segments were expected. Zero-DVM segments remained identity. No factor math or order was changed by PW binding.

## AE. critic classifications

Of 1,600 completed critic minibatches, 1,576 were `VALID_NONZERO_UPDATE` and 24 `VALID_ZERO_EFFECTIVE_UPDATE`; invalid classes 0 in the retained completed ledger. Classification counts are bounded evidence, not overall formal success.

## AF. critic/ValueNorm

Critic backward/optimizer steps were 1,600/1,600 and live ValueNorm updates 1,600. The critic used physical rows independently of DVM. The final overall route is poisoned because post-mutation W2 qualification failed, not because these counters were deficient.

## AG. event returns

Reviewed event-return computations were 160; stock HARL `compute_returns` calls 0. Each transaction's source-bound return check completed before S10.

## AH. bootstrap

The [nonterminal bootstrap ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_nonterminal_bootstrap_ledger.jsonl) has 160 rows, including a real all-NONE current-next-value witness. NR empty/empty terminal reconciliation remained valid when no terminal was expected.

## AI. terminal reconciliation

The [terminal ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_terminal_reconciliation_ledger.jsonl) has 160 rows. W5 selected tx150 TIME_LIMIT with exact expected/observed keys for both environments and no missing/extra/duplicate keys. W6 selected tx151 after autoreset.

## AJ. serializer

The reviewed SR `[T,E,1]` reason-grid serializer preflight passed 7/7 positives, 12/12 negatives, retained RE1 replay, ledger roundtrip, and post-S10 bookkeeping. The formal terminal/bootstrap ledgers were written through the source-bound path; no serializer error caused this STOP.

## AK. bookkeeping

The append-only prefixed transaction, bridge, episode, lifecycle, terminal, bootstrap, zero-DVM, runtime-immutability, training-metric, rolling-health, and actor-evidence ledgers are retained. Canonical success-only alias ledgers and W1–W7 output files were **not fabricated** after the W2 gate failed. The formal failure receipt remained durable and read back.

## AL. collection learner immutability

The inherited per-transaction collection checks and 159 bridges completed without collection-time learner mutation; this is bounded evidence. The poisoned learner cannot be reused or checkpointed merely because the collection invariant held.

## AM. actor Adam

Source-bound per-tx Adam step-delta checks completed for actor optimizer steps totaling 165. Zero-DVM actor deltas were 0. Overall RE5 success is still false.

## AN. critic Adam

Source-bound per-tx critic Adam step-delta checks completed for 1,600 optimizer steps without observed reset/decrement. This does not license learner continuation after the postprocess STOP.

## AO. ValueNorm

ValueNorm remained live and finite across the 160 recorded transactions and 159 bridges, with 1,600 updates through the critic path. The final route is poisoned despite this bounded continuity.

## AP. bridge summary

159/159 S10-to-next-S0 bridges were durable; tx160 had no tx161. The [bridge ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_bridge_ledger.jsonl) is evidence of one persistent learner, not W2 claim history.

## AQ. W1

**PASS as an individual witness:** tx001→tx002 preserved robot/task ownership, used continuation, and made zero fresh policy calls. Overall RE5 remains STOP.

## AR. W2

**NOT ESTABLISHED / decisive STOP.** The exact inherited predicate requires a recorded `task_claimed` event for the same `(env, robot, task)` at `claim_tx < completion_tx`, then completed P2 state, ownership cleared and decision reopened. The 160-row lifecycle ledger has 22 `task_completed` entries but **zero `task_claimed` entries**. Therefore no eligible claim/completion pair exists and `_find_witnesses` returned `W2_MULTI_UPDATE_COMPLETION=None`; `_postprocess_success` raised `REQUIRED-WITNESS-GATE`. The 22 completions, coverage, and W1 ownership cannot substitute for that required event chain. No posthoc witness was invented.

## AS. W3

**PASS as an individual witness:** a real zero-DVM actor had expected/observed population 0/0, zero backward/step/Adam delta, and identity factor. Overall RE5 remains STOP.

## AT. W4

**PASS as an individual witness:** a real nonterminal all-NONE transaction used current-next critic bootstrap, empty/empty NR reconciliation, event returns, S10, and ledger. Overall RE5 remains STOP.

## AU. W5

**PASS as an individual witness:** tx150 observed genuine 30 s/max-300 TIME_LIMIT/autoreset with exact terminal keys for both environments. Overall RE5 remains STOP.

## AV. W6

**PASS as an individual witness:** tx151 collected a fresh post-autoreset generation rollout and reached S10/ledger. Overall RE5 remains STOP.

## AW. W7

**PASS as an individual witness:** runtime/P2 immutability was equal in all 160/160 transaction rows. Overall RE5 remains STOP.

## AX. task progress

The ledger records `TASK_COMPLETED=22`, positive completed delta, and maximum covered viewpoint count 11. These capability signals are not a W2 claim-before-completion witness.

## AY. completion/P2/coverage

Completion signals and coverage were nonzero, and P2 task completion states were recorded. The missing causal claim event means the required multi-update completion/decision-reopen chain is unqualified.

## AZ. decision reopen

The required W2 post-completion decision-reopen condition was not adjudicated for any qualified claim/completion pair, because the pair set was empty. Do not infer it solely from later policy rows.

## BA. PW per-tx reconciliation

The [PW per-tx ledger](b2_t4_re5_artifacts/pw_transaction_reconciliation.jsonl) has 160 ordered rows, each with 4 actor/factor and 41 critic records and zero local integrity faults. This ledger was written after each S10/transaction row and read back. It does not override W2 or Layer A.

## BB. PW campaign reconciliation

The worker did not reach its success-only campaign reconciliation because W2 failed first. A read-only postmortem called reviewed `PW.verify_transaction` for all 320 `(tx, side)` populations and created the separately labeled retrospective [reconciliation](b2_t4_re5_artifacts/pw_campaign_reconciliation.json): 640 actor/factor and 6,560 critic records, missing/extra/out-of-order/digest faults 0, temp residue 0, old mutable progress paths 0. PW integrity PASS; RE5 qualification FAIL.

| Item | Expected | Actual |
|---|---:|---:|
| Filesystem | NTFS | NTFS |
| Same-volume temp/final | yes | yes |
| PW helper SHA-256 | exact reviewed | exact reviewed |
| Critic records/tx | 41 | 41 each |
| Critic records/160 | 6,560 | 6,560 |
| Actor/factor records/tx | 4 source-derived | 4 each |
| Actor/factor records/160 | 640 | 640 |
| Missing / duplicate / out-of-order / digest mismatch | 0 each | 0 each |
| Temp residue / old mutable progress paths | 0 / 0 | 0 / 0 |

## BC. RE4-vs-RE5 tx130 persistence comparison

The formal [tx130 comparison](b2_t4_re5_artifacts/re4_re5_tx130_persistence_comparison.json) was emitted after RE5 tx130. It compares persistence only, not learner equivalence.

| Property | Historical RE4 tx130 | Fresh RE5 tx130 |
|---|---|---|
| Learner source | historical poisoned | fresh RE5 |
| Critic persistence | mutable replace-existing | immutable PW |
| Progress events reached | 28 before STOP | 41 verified |
| PermissionError | `WinError 5` | none observed |
| PW missing/duplicate/digest fault | N/A | 0/0/0 |
| S10 | 0 | 1 |
| Historical learner reuse | forbidden | none |

Reaching tx130 did not establish final RE5 success; the subsequent W2 gate failed after tx160.

## BD. numerical health

All 160 transaction-ledger `finite` flags were true; recorded actor/critic losses, gradients, parameters, optimizers and ValueNorm passed inherited per-transaction checks. No numerical failure caused the STOP, and no post-failure learner continuation was attempted.

## BE. rolling health

The inherited [rolling-health ledger](b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_rolling_health_ledger.jsonl) has 160 rows. The RE5 [PW rolling sentinel ledger](b2_t4_re5_artifacts/pw_rolling_health.jsonl) has 12 entries at tx001/002/003/010/025/050/075/100/125/130/150/160, including S10/ledger/bridge/PW counts, finite state and ValueNorm fingerprints. These are bounded diagnostics, not RE5 overall PASS or reward-quality evidence.

## BF. RE5 Layer-A receipt

The failure receipt was persisted and read back before App close. It reports W2 `REQUIRED-WITNESS-GATE`, `production_s10=160`, `ledger_qualified_transactions=160`, irreversible learner mutation, `partial_update=true`, and `route_poisoned=true`. Layer-A success is false. The absence of a success-only `pw_campaign_reconciliation.json` from the worker was not repaired or backfilled as a worker claim.

## BG. env close

The receipt records `env_close_attempted=true`, `env_close_pass=true`, and `app_close_invoked=true`. No mandatory worker evidence after `SimulationApp.close()` is claimed; its return to Python is not established.

## BH. EP-Q Layer-B

External [process evidence](b2_t4_re5_artifacts/process_quiescence.json) passed: wait complete, timeout false, return code 0, original PID absent, matching formal-worker set empty. This establishes only process-level quiescence, not learner qualification.

## BI. shutdown diagnostics

Captured shutdown marker: false. Under reviewed EP-Q v2 it is diagnostic/non-blocking. A marker cannot override W2 failure, and its absence does not invalidate direct process termination evidence.

## BJ. supervisor adjudication

The [supervisor](b2_t4_re5_artifacts/formal_supervisor_result.json) recorded one worker and zero retries, Layer A false, Layer B true, overall failed, `partial_update=true`, `route_poisoned=true`. Worker return code 0 was not mistaken for success. The raw formal [final result](b2_t4_re5_artifacts/final_result.json) remains failed and unedited.

## BK. artifacts

Present: static/filesystem/binding/preflight/readiness/config/CUDA, one formal receipt, supervisor/process/final, prefixed transaction and bridge evidence, lifecycle/terminal/bootstrap/zero-DVM/immutability/training/rolling ledgers, PW per-tx and rolling ledgers, all immutable PW records, and tx130 comparison. Retrospective failure adjudication and PW campaign reconciliation are explicitly labeled as postmortem. Success-only W1–W7 files and canonical alias ledgers were not fabricated after STOP. No model checkpoint was created.

## BL. exact counts

Final frozen preflight parent plus launched children: 14 Python invocations; final readiness: 1 PASS. Formal supervisors/workers/retries `1/1/0`; CUDA probes/AppLauncher/environments/initial resets/persistent learners `1/1/1/1/1`; physical transitions 320; production S10/ledger 160/160; bridges 159; PW critic/actor records 6,560/640; PW faults and residue 0; terminal/autoreset events 2; event returns 160; stock returns 0; actor backward/step 165/165; critic backward/step 1,600/1,600; critic classes 1,576 nonzero / 24 zero-effective; ValueNorm updates 1,600; zero-DVM actor/tx pairs 452; all-zero-DVM transactions 139; lifecycle policy/continuation/noop rows 39/1,294/587; W1,W3–W7 true, W2 absent; Layer A false, Layer B true; checkpoint I/O/public activation/evaluation-playback 0/0/0; production and historical RE4 modifications 0/0; Git add/commit/push 0/0/0; tx161 not started. Overall pre-runtime ad hoc diagnostic invocation count was not durably tracked across the interrupted turn; no exact number is invented.

## BM. retained nonclaims

RE5 did **not** qualify normal-horizon learned-training integration, W1–W7 as a set, checkpoint continuation, long/paper-scale training, reward improvement, convergence, public-policy readiness, or evaluation/playback readiness. Complete S10/PW counts do not erase the missing W2 witness or poisoned outcome. PW remains NTFS/process-crash scoped, not power-loss durability or non-NTFS portability.

## BN. final classification

Raw immutable classification: `PHASE-B2-T4-RE5-STOP-FORMAL-WORKER-FAILURE`. Narrow source-backed handoff: `PHASE-B2-T4-RE5-STOP-W2-MULTI-UPDATE-COMPLETION-WITNESS-NOT-ESTABLISHED-AFTER-MUTATION`. State: `B2-T4-RE5 STOPPED / HISTORICAL / POISONED / NOT QUALIFIED`. RE4 remains its own historical poisoned STOP. PW remains `GPT REVIEW PASS / CLOSED`. No self-issued GPT REVIEW PASS.

## BO. GPT-review handoff

Review the immutable failure receipt and supervisor result, the exact inherited W2 predicate, zero recorded claim events versus 22 completions, 160 S10/ledger and 159 bridges, PW record verification, tx150/151 terminal/post-reset witnesses, and the Layer-A/Layer-B separation. Do not resume or repair this learner, run a second RE5 worker, start tx161 or B2-R6, save/load a checkpoint, begin long training, activate the public route, stage, or commit. Any future W2 contract diagnosis or fresh attempt requires a separately authorized phase.
