# Phase B2-T4-RE3 Normal-Horizon Learned-Training Integration Qualification Report

Date: 2026-09-15

## A. repository authority

Branch `main`; `HEAD`, `origin/main`, and their merge-base are all `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing 359 staged monthly-archive migration paths remained untouched. Their staged-index SHA-256 remained `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; the monthly path-set SHA-256 remained `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

## B. reviewed starting authority

B2-R0 through B2-R7 and B2-T0 through B2-T3 were closed. Original B2-T4 remained historical STOP; NR and SR were closed; RE1 and RE2 remained historical poisoned STOPs; ZD was accepted as `GPT REVIEW PASS / CLOSED` before RE3 execution.

## C. historical B2-T4 preservation

The original `PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED` result was retained and was not reclassified.

## D. NR authority

The source-faithful NR suite passed 5/5, including its 14/14 terminal expectation matrix. No NR production semantics were changed.

## E. RE1 poisoned-history preservation

RE1 remains `STOPPED / HISTORICAL / POISONED / NOT COMPLETE`. Its retained tx001 S10 artifact SHA-256 is `e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649`. No RE1 learner, process, or route was reused.

## F. SR authority

The SR serializer SHA-256 remained `dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358`. A full replay bound in memory to the current ZD production hashes passed 7/7 positive and 12/12 negative cases, retained-RE1 replay, ledger round-trip, and post-S10 bookkeeping.

## G. RE2 poisoned-history preservation

RE2 remains `STOPPED / HISTORICAL / POISONED / NOT COMPLETE`. The retained tx002 decision-evidence SHA-256 is `93b4624167ce8b8dd052e4d3ab4c3cf105b34cd1a140ee840313edc2f8935fda`. No RE2 learner, optimizer, ValueNorm state, process, or route was reused.

## H. ZD authority

ZD remained `GPT REVIEW PASS / CLOSED`. Its dedicated preflight passed three positives, ten fail-closed negatives, and the retained RE2 tx002 zero-DVM replay. Empty expected/observed actor populations remained valid when identical.

## I. production source identities

`assignment_event_training_full_transaction.py` was `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`; `assignment_event_training_real_isaac_adapter.py` was `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`. All frozen repo and installed-HARL identities in `re3_static_authority.json` passed. RE3 made zero production semantic modifications.

## J. runner/helper identities

The final RE3 wrapper SHA-256 was `b6325c78189ab5b62c7daaf7452745c036eb7acd629f3c705cbded24eda86f6c`. It was derived from the qualified RE2 wrapper `263d48ca5988ab809ff63c5e11b4c8364d04159bd0cd96f4e0675d2465f8b40b`; the transformed runner source digest was `cdd62c187b04b9a392aacca7de62bf5ec2ae50b55a9d3a06fd4007bd93cd23e6`.

One pre-mutation readiness attempt stopped because the wrapper bound the historical `_re1_*` private name instead of the `_re3_*` name produced by the qualified RE2-to-RE3 transform. The test-only binding was corrected before formal launch, recompiled, and the final readiness replay passed. No production source changed.

## K. files created/modified

Created: the RE3 wrapper; this report; the byte-exact task-progress archives; `b2_t4_re3_artifacts/` preflight, readiness, static, formal, supervisor, and adjudication evidence. Modified: `AgentRead/TASK_PROGRESS.md`. No production semantic file was modified. No file was staged or committed.

## L. pre-runtime qualification

There were 28 approved-interpreter Python invocations before formal launch, including diagnostics and the two readiness attempts. `py_compile`, approved interpreter, current ZD identities/suite, NR, current-ZD-baseline SR, I5b 14/14, LD 13/13, terminal-rich controlled R5, real-shape/row geometry, critic CG, ValueNorm 53 assertions, T2/T3 observer nonmutation, and R1 static/private/public guards all passed. Preflight CUDA exercises were not counted as the formal same-worker CUDA/CUBLAS receipt.

## M. RE3 exact-runner readiness replay

Final qualified replay count: 1 PASS. The retained RE1 S10 replay produced one row in each of eight required SR/bookkeeping ledgers. The retained RE2 zero-DVM replay produced expected=observed `[[0,0],[1,0],[2,0]]`, actor backward/step/Adam delta `[0,0,0]`, identity factor, critic backward/step `1/1`, ValueNorm update 1, event returns 1, and S7-S10 PASS. It used no AppLauncher or real Isaac environment.

## N. CUDA/CUBLAS readiness

Exactly one formal same-worker CUDA/CUBLAS probe passed before AppLauncher. The `torch.mm` result was `[[19,22],[43,50]]` on `cuda:0`.

## O. fresh formal process

Exactly one formal supervisor launched one fresh intended mutation-bearing worker (PID 7712), with retry count 0. A preceding PTY transport request was rejected by Windows before any process existed and is not a formal attempt. The formal worker created one AppLauncher lifetime, then stopped before environment construction. No second formal process was launched.

## P. runtime configuration

The runner was configured for `Isaac-Scan-Mobile-Manipulator-Direct-v0`, `event_gated_local_mrta`, `T/E/M/N=2/2/3/12`, actor and critic epochs/minibatches `5/2`, ValueNorm enabled, `fixed_order=false`, `cuda:0`, 30.0 s / max 300 / control 0.1 s. The environment entry point failed to resolve, so no environment-side configuration was instantiated or runtime-qualified.

## Q. horizon separation

Configured rollout horizon T=2 and environment horizon 30.0 s/max 300 were distinct, but no environment or rollout was constructed. Runtime horizon separation is therefore not qualified.

## R. success-accounting definition

A transaction would count only after S0-S10, SR/bookkeeping, NR/ZD receipts, append-only ledger write, and durable readback. No transaction reached the entry boundary, so the count is 0.

## S. update-ID inventory

Empty. No formal update ID was admitted.

## T. transaction-status table

| Scope | Status | S10 | Ledger-qualified |
|---|---|---:|---:|
| tx001 | NOT ENTERED; pre-environment entry-point resolution STOP | 0 | 0 |
| tx002-tx160 | NOT STARTED | 0 | 0 |
| tx161 | NOT STARTED | 0 | 0 |

## U. episode/update/physical-step timeline

No episode generation, update, or physical transition exists. Physical transitions: 0/320.

## V. lifecycle decision summary

Not reached. Policy-required rows, continuation rows, forced-noop rows, and policy calls are all 0; runtime fault counts are not meaningfully exercised.

## W. actor-order distribution

Not reached; no actor order was sampled for a formal transaction.

## X. actor DVM population statistics

Not reached; no formal rollout rows exist.

## Y. all-zero-DVM runtime transactions

0 formal runtime transactions. The preflight/readiness zero-DVM replay passed, but it is not runtime evidence.

## Z. actor plan/update counts

Formal actor backward/optimizer-step: 0/0. No actor plan was frozen.

## AA. actor-evidence reconciliation

No formal receipt was produced; reconciliation count 0 and runtime reconciliation faults 0. ZD preflight/readiness passed but does not substitute for the missing runtime slice.

## AB. factor audits

Not reached; formal factor audit count 0.

## AC. critic classifications

`VALID_NONZERO_UPDATE: 0`; `VALID_ZERO_EFFECTIVE_UPDATE: 0`. No formal critic minibatch ran.

## AD. critic/ValueNorm counts

Formal critic backward/optimizer-step: 0/0. Formal live ValueNorm updates: 0.

## AE. nonterminal bootstrap

Not reached; no formal next-state bootstrap was evaluated.

## AF. terminal/bootstrap

Not reached; terminal/autoreset events: 0.

## AG. terminal reconciliation

Not reached; no formal terminal ledger existed. NR preflight passed only its bounded source-faithful qualification.

## AH. SR serializer continuity

Preflight and readiness passed. Formal runtime serializer continuity was not reached.

## AI. bookkeeping continuity

Preflight and readiness passed. Formal ledger append/readback count: 0.

## AJ. actor Adam continuity

Not established because the formal persistent learner was never constructed.

## AK. critic Adam continuity

Not established because the formal persistent learner was never constructed.

## AL. ValueNorm continuity

Not established because the formal persistent learner was never constructed.

## AM. 159-bridge summary

0/159. No bridge was created.

## AN. collection learner immutability

No formal learner or collection step existed; runtime evidence unavailable.

## AO. learner-update runtime/P2 immutability

0/160 runtime/P2 immutability receipts; W7 not established.

## AP. W1 cross-update ownership

FAIL / NOT ESTABLISHED: no update or bridge existed.

## AQ. W2 multi-update completion

FAIL / NOT ESTABLISHED: 0 successful updates.

## AR. W3 real zero-DVM actor

FAIL / NOT ESTABLISHED in runtime. The pure/readiness zero-DVM evidence remains PASS but is not a formal real-Isaac witness.

## AS. W4 real nonterminal bootstrap

FAIL / NOT ESTABLISHED.

## AT. W5 normal-horizon terminal/autoreset

FAIL / NOT ESTABLISHED; terminal/autoreset count 0.

## AU. W6 post-autoreset learned training

FAIL / NOT ESTABLISHED.

## AV. W7 runtime/P2 immutability

FAIL / NOT ESTABLISHED: 0/160.

## AW. task-progress trajectory

Not reached. No formal task-progress row was observed.

## AX. completion/P2/coverage consistency

Not established. `TASK_COMPLETED=0`, completed delta=0, and coverage maximum/final are unavailable.

## AY. completion -> reopen

Not reached.

## AZ. terminal-ledger continuity

Not reached; no terminal or generation boundary existed.

## BA. event-return compute-once

Formal event-return computations: 0/160. Stock `compute_returns`: 0.

## BB. S7/S8/S9/S10

Formal counts: `0/0/0/0`; required `160/160/160/160` not met.

## BC. numerical health

No formal learner tensor was created. CUDA probe finiteness passed, but learned-training numerical health is not established.

## BD. diagnostic training metrics

No formal training metrics exist.

## BE. rolling health

No rolling-health ledger exists; 0 qualified transactions.

## BF. artifact inventory

- `re3_static_authority.json`: 220,124 bytes, SHA-256 `ba7156760472ffbee626a782a49ba80b94c7b60d4c3920b9cb6f9c11934d9337`.
- `re3_runner_readiness_replay.json`: 224,431 bytes, SHA-256 `e021ea6e2a399b192adea0da1a03e68f61d28308fb04f7c389906deceadd493c`.
- `re3_preflight_summary.json`: 3,445 bytes, SHA-256 `f62b2a4285a1309690594bd4fc4d5f3f00f71544b996b555acbc29005ee60a8f`.
- formal CUDA receipt: 213 bytes, SHA-256 `a57b28dc04fd0c0f283eab0ca1de6c3170b8a9330e832d42509ca0211d17a212`.
- formal process authority: 218,325 bytes, SHA-256 `5d8dcaebdc797b864cf1b81b068f2b8d34dfdb834d041f72675bf2a5d567e783`.
- raw formal result: 1,546 bytes, SHA-256 `75ed7bb44ced4bf1e9f8bfdc704c8a101ce21ef1c97623f080ef7ef3311f2408`.
- `b2_t4_re3_formal_supervisor_result.json` and `re3_failure_adjudication.json` preserve the supervisor/adjudicated view.
- `preflight/zd/` and `preflight/sr/` preserve their generated qualification artifacts.

## BG. static/private/public guards

PASS before formal launch. Production semantic modifications 0; checkpoint I/O 0; public activation 0; evaluation/playback 0. Public learned-policy route remains dormant/blocked.

## BH. exact execution counts

Pre-runtime Python invocations 28; final exact-runner readiness 1 PASS; formal CUDA/CUBLAS probes 1 PASS; formal supervisors 1; formal workers 1; formal retries 0; AppLauncher 1; environments 0; initial resets 0; persistent learners 0; physical transitions 0; production S10 0; ledger-qualified 0; bridges 0; episode generations 0; actor backward/step 0/0; critic backward/step 0/0; ValueNorm updates 0; event returns 0; stock compute_returns 0; checkpoint I/O 0; public activation 0; evaluation/playback 0; production semantic modifications 0; post-mutation retries 0; tx161 not started; commit none.

## BI. retained nonclaims

RE3 normal-horizon integration is not qualified. Long-training execution readiness is not established. Checkpoint continuation is not established. No checkpoint, public learned-policy readiness, evaluation/playback, B2-R6, or long/paper-scale training claim is made.

## BJ. final quiescence

The worker PID was absent after supervisor return and no RE3 Python worker remained. Resource/process quiescence passed. Learner-route quiescence is vacuous because no learner or mutation was created. `mutation_had_begun=false`, `partial_update=false`, and `route_poisoned=false`; nevertheless, the formal attempt is closed and may not be retried under this task.

## BK. final classification

`PHASE-B2-T4-RE3-STOP-PRE-ENVIRONMENT-ENTRY-POINT-RESOLUTION-NOT-COMPLETE`

The raw inherited worker classification named tx1 bounded-smoke failure, but the traceback establishes a more precise pre-environment boundary: Gymnasium could not resolve `ScanMobileManipulatorEnv` from `isaaclab_tasks.direct.scan_mobile_manipulator`. No environment, reset, physical step, transaction, learner, or mutation occurred.

## BL. GPT-review handoff

Independent review should inspect the entry-point export/registration boundary and the evidence distinction between readiness PASS and formal runtime STOP. This report does not authorize a repair, a fourth retry, B2-R6, checkpoint I/O, public activation, evaluation/playback, or long/paper-scale training. Stop and wait for new explicit authorization.
