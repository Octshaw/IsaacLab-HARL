# Phase B2-T4-RE4 normal-horizon learned-training integration qualification report

Date: 2026-09-16. **Final result: STOP / POISONED / NOT QUALIFIED.** This is the one authorized RE4 formal attempt. The narrower evidence classification is `PHASE-B2-T4-RE4-STOP-EVIDENCE-PERSISTENCE-PERMISSION-DENIED-AFTER-MUTATION`; the immutable raw supervisor classification is `PHASE-B2-T4-RE4-STOP-FORMAL-WORKER-FAILURE`. The worker failed during tx130 `S6_CRITIC_SEQUENCE` while atomically replacing `tx130_critic_progress.json.tmp` with `tx130_critic_progress.json`: Windows `PermissionError [WinError 5]`. No repair or formal retry was performed.

Artifact references below are relative to [b2_t4_re4_artifacts](b2_t4_re4_artifacts/). A completed transaction means its production S10 *and* its append-only transaction ledger row are durable. It is not a claim that the 160-transaction qualification succeeded.

## A. repository authority

Branch `main`; HEAD, `origin/main`, and merge-base remained `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing 359 staged archive-migration paths were preserved; frozen staged-index digest `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, monthly path-set digest `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No add, commit, push, reset, checkout, or clean was run.

## B. reviewed starting authority

B2-R0–R7 and B2-T0–T3 were closed; NR, SR, ZD, and EP-Q were `GPT REVIEW PASS / CLOSED`. Original T4, RE1, RE2, RE3, EP, and EP-P were historical STOPs. This authorization was only for one fresh RE4 qualification.

## C. historical STOP preservation

Original T4 nonterminal-bootstrap STOP, RE1 and RE2 poisoned STOPs, RE3 unpoisoned pre-environment STOP, EP evidence-persistence STOP, and EP-P old process-quiescence STOP remain unchanged. No historical process, learner, optimizer, ValueNorm, route, or artifact was reused as formal runtime state.

## D. NR authority

The fresh preflight NR suite returned 5/5 PASS and its terminal expectation matrix 14/14. Its pure/source-faithful evidence is not a substitute for RE4's incomplete formal run.

## E. SR authority

The frozen SR suite was replayed in a child process with only its two historical source-hash literals rebound *in memory* to the reviewed ZD baseline. It passed 7/7 serializer positives, 12/12 fail-closed negatives, retained RE1 tx001 replay, ledger roundtrip, and post-S10 bookkeeping. The initial direct SR invocation stopped at its obsolete pre-ZD hash guard; this occurred before formal launch and is included in invocation accounting. The historical SR source file was not changed.

## F. ZD authority

The fresh ZD suite passed actor-rich, partial-zero, and all-zero positives, 10 fail-closed negatives, and retained RE2 tx002 replay. The formal run's tx001–tx129 zero-DVM ledger contains 362 actor/transaction rows, but the RE4-wide 160-update gate remains unmet.

## G. EP/EP-P historical preservation

EP and EP-P source/artifact histories were not edited or reclassified. EP-P's historical shutdown-marker STOP is retained even though EP-Q subsequently reviewed the generic v2 process predicate.

## H. EP-Q authority

EP-Q v2 was reviewed closed before RE4. RE4 uses its generic Layer-B process predicates only. It does not copy EP-Q's zero-step/zero-learner Layer A. The RE4-specific Layer A failed; Layer B independently passed.

## I. production source identities

Frozen [static authority](b2_t4_re4_artifacts/re4_static_authority.json) passed. Full-transaction SHA-256 `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`; real-adapter SHA-256 `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`. Production semantic modifications: 0. Installed HARL identities were exact in the static manifest.

## J. RE4 worker/supervisor identities

The new test-side RE4 harness SHA-256 frozen for formal use was `f04ba511f5d644fcb2bbba61d44e73b6b791301b90a0f9b1c264ebff1af4542e`. It called the reviewed RE3 training engine (`02fcba5b1798c9c77be0af7d9ae4de9ce1ea7c392e9ea69c1cf52eb1e33f0ce1`) directly to place receipt persistence before App close. EP-Q helper SHA-256 was `bb56c8c6ebe7b93353640b4c161845f88ed281a6bc991acf35a376ad6b39b52d`. Formal worker PID: 26444.

## K. RE4 Layer-A contract

`b2_t4_re4_training_worker_receipt_v1` binds run ID, PID, source/config digests, runtime counts, 160-update targets, witnesses, learner and contract checks, poison state, and close ordering inside a digest-checked durable envelope. The [formal receipt](b2_t4_re4_artifacts/formal_worker_receipt.json) is a valid *failure* receipt; it does not pass success Layer A.

## L. EP-Q Layer-B binding

Layer B requires completed wait, no timeout, zero return code, original PID absent, and no matching formal worker. All five predicates passed. Shutdown-marker text was absent and non-authoritative. Worker return code 0 cannot override the failed Layer A.

## M. pre-runtime qualification

Approved interpreter `C:\isaacenvs\isaac45_harl\python.exe`, relevant `py_compile`, static identities, EP import regression, receipt success/failure and missing/malformed/stale negatives, Layer-B positives/negatives, NR, SR, ZD, I5b 14/14, LD 13/13, controlled R5, row geometry, CG, ValueNorm 53 assertions, T2/T3 observer nonmutation, and static/private/public guards passed. [Preflight summary](b2_t4_re4_artifacts/re4_preflight_summary.json) records 24 pre-runtime Python invocations including a pre-formal SR hash-guard STOP, its corrected replay, and one superseded pre-final readiness PASS. No AppLauncher was launched during preflight.

## N. exact-runner readiness

The final [readiness replay](b2_t4_re4_artifacts/re4_runner_readiness_replay.json) passed A–D: retained RE1 SR/bookkeeping, retained RE2 ZD continuation-only, RE4 receipt synthetic qualification, and EP-Q Layer-B synthetic qualification. A preceding PASS was preserved as `re4_runner_readiness_replay_superseded_before_entry_point_constant_fix.json` after a pre-formal package-entry-point constant correction; final qualified replay count is one. Neither replay used AppLauncher or a real environment.

## O. CUDA/CUBLAS readiness

The one formal worker ran exactly one deterministic `torch.mm` probe on `cuda:0` before AppLauncher. [CUDA receipt](b2_t4_re4_artifacts/re4_cuda_cublas_readiness.json): result `[[19,22],[43,50]]`, one probe, zero retries, PASS.

## P. canonical import/registration ordering

The worker verified no `isaaclab_tasks` package contamination before AppLauncher, then executed AppLauncher → canonical `import isaaclab_tasks` → `gym.spec` → exact class identity → `gym.make`. The registered entry point is the package export `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`. Resolution passed and one environment was constructed.

## Q. fresh formal process

One supervisor launched one fresh worker (PID 26444), one AppLauncher, one environment, one initial reset, and one persistent learner. Formal retries: 0. The worker is externally absent after termination. The worker's `SimulationApp.close()` return to Python is not claimed.

## R. runtime configuration

Formal [process authority](b2_t4_re4_artifacts/re4_process_config_authority.json) specifies `Isaac-Scan-Mobile-Manipulator-Direct-v0`, `event_gated_local_mrta`, `cuda:0`, T/E/M/N `2/2/3/12`, actor and critic epochs/minibatches `5/2`, ValueNorm enabled, `fixed_order=false`, environment horizon 30.0 s / max 300 / control step 0.1 s. No short-horizon override was used.

## S. horizon separation

T=2 was the learner rollout length, not the environment episode horizon. The worker collected 260 physical transitions before stopping at tx130. Because max 300 was not reached, no normal-horizon terminal/autoreset witness exists.

## T. transaction success definition

Only a production S10 followed by append-only ledger write/readback counts. Thus tx001–tx129 count; tx130 has partial S6 mutation but no S10 and no qualified ledger row. tx131–tx160 and tx161 were not started.

## U. transaction inventory

The 129 qualified rows have distinct chronological update IDs under the single worker's inherited RE3 engine identity. Exactly 128 bridges were durable. The one formal process did not reuse any historical update ID or learner object; no second process was launched.

## V. transaction status table

The per-transaction authoritative values are in `b2_t4_re4_normal_horizon_20260916_formal01_transaction_ledger.jsonl` and the episode/bridge ledgers. Because this is a STOP, the table groups only identical adjudication states rather than implying a 160/160 PASS.

| Tx | S10 | Ledger-qualified | Episode gen | Policy rows | Continuations | Zero-DVM actors | All-zero-DVM | Terminal | Completion | Bridge |
|---:|---|---|---|---|---|---|---|---|---|---|
| 001–129 | yes, 129/129 | yes, 129/129 | 0 throughout | 33 total | 1,092 total | 362 actor/tx rows | 109 tx | 0 | 22 events | 128/128 to next tx |
| 130 | no; stopped in S6 | no | 0 | rollout exists; not ledger-qualified | rollout exists; not ledger-qualified | not ledger-qualified | not adjudicated | 0 | not adjudicated | no post-S10 bridge |
| 131–160 | not started | no | — | — | — | — | — | — | — | — |
| 161 | NOT STARTED | no | — | — | — | — | — | — | — | — |

The 129 completed rows also contain 423 forced-noop nondecision rows; policy/continuation/noop totals are 33/1,092/423 across 1,548 robot-step rows.

## W. episode/update/physical timeline

The initial reset created episode generation 0. tx001–tx129 consumed physical steps 1–258; tx130 collected steps 259–260, then failed after entering learner mutation. Episode generation stayed 0, with no autoreset. No learner-boundary environment reset was made.

## X. lifecycle decision summary

Across completed rows: 33 policy-required, 1,092 forced-continuation, 423 forced-noop; total 1,548. This is a read-only description of tx001–tx129, not a 160-update lifecycle qualification.

## Y. actor DVM statistics

The completed transaction ledger records 33 actor DVM rows and 150 actor backward/optimizer steps each. There are 362 zero-DVM actor/tx ledger rows. All-zero-DVM transactions: 109 among the 129 completed rows; no full-run claim is made.

## Z. all-zero-DVM runtime

The 109 completed all-zero-DVM transactions show zero actor training for their zero-DVM actors in their durable ledger rows. tx130's actor backward/step counts were 0/0/0, but tx130 is a failed partial critic update and is excluded from qualified transaction totals.

## AA. actor update plans

Completed rows report actor backward/optimizer step `150/150`; tx130 pre-mutation actor/critic plan digests were durable, but tx130's entire plan did not complete. Therefore the required 160-plan exactness gate fails.

## AB. actor evidence reconciliation

The actor-evidence ledger has 129 rows and the completed S10 rows passed source-faithful reconciliation. No actor-evidence ledger row exists for tx130. The 160/160 requirement is unmet.

## AC. factor audits

Completed S10 transactions carry their inherited factor audit evidence. tx130 records only four factor-progress events before failure. The 160-transaction factor gate is not qualified.

## AD. critic classifications

Completed rows contain 1,269 `VALID_NONZERO_UPDATE` and 21 `VALID_ZERO_EFFECTIVE_UPDATE`, totaling 1,290 valid critic minibatches. tx130 reached seven critic optimizer steps and seven ValueNorm updates, then stopped; it has no complete critic classification/plan receipt.

## AE. critic/ValueNorm counts

Qualified tx001–tx129: critic backward/optimizer `1,290/1,290`, ValueNorm.update `1,290`. Failed tx130 adds seven observed critic optimizer steps and seven ValueNorm updates but does **not** add a qualified transaction or S10. Do not merge the poisoned partial update into successful counts.

## AF. event-return audit

Completed transactions have 129 event-return computations and zero stock `compute_returns` calls. The full 160-return gate is unmet; tx130's local return state is not promoted to a qualified row.

## AG. nonterminal bootstrap

The nonterminal-bootstrap ledger has 129 completed rows; no terminal rows were observed before failure. This supports only the bounded completed prefix, not the required final 160-update witness suite.

## AH. terminal/bootstrap

Formal terminal/autoreset events: 0 by physical step 260. The 30.0 s / max 300 terminal boundary was not reached. W5 and W6 cannot pass.

## AI. terminal reconciliation

The terminal-reconciliation ledger has 129 rows with no observed terminal key. NR pure qualification passed, but RE4 did not exercise a real normal-horizon terminal/autoreset in this run.

## AJ. serializer continuity

The completed-prefix SR ledger serializations and preflight were durable. tx130 failed on filesystem atomic replacement of the critic-progress JSON, not on termination-reason-grid serialization. Nevertheless RE4-wide serialization/bookkeeping success is not established.

## AK. bookkeeping continuity

Ten required prefixed JSONL ledgers were preserved at their last durable positions: transaction 129, bridge 128, episode 129, lifecycle 129, terminal 129, bootstrap 129, runtime immutability 129, training metric 129, rolling health 129, and zero-DVM actor rows 362. Actor-evidence reconciliation also has 129 rows. The tx130 `.json.tmp` residue is preserved exactly; it was not renamed, deleted, or treated as authoritative.

## AL. collection learner immutability

The inherited per-transaction completed-prefix evidence passed collection learner-state preservation. The qualification of all 160 collections is unavailable after the tx130 STOP.

## AM. actor Adam continuity

The completed-prefix actor backward/optimizer totals agree at 150/150. Adam continuity for a full 160-update run is not established; the poisoned learner was not reused or reconstructed.

## AN. critic Adam continuity

The completed prefix has 1,290 critic optimizer steps. tx130 performed seven more before the evidence-persistence error. No post-failure Adam inspection or continuation was attempted; full-run continuity is not established.

## AO. ValueNorm continuity

The completed prefix has 1,290 ValueNorm updates; tx130's failure evidence records seven further updates. The partial state is poisoned, not a checkpoint or continuation point.

## AP. bridge summary

128/159 bridges were durable. The tx129→tx130 bridge existed and established the next S0; no tx130→tx131 bridge exists. No new worker was allowed to fill the gap.

## AQ. W1

Cross-update ownership is **NOT QUALIFIED** as the final RE4 W1. The completed-prefix lifecycle ledger and tx130 decision evidence contain continuation candidates, but the required final witness adjudication was not reached after the S6 STOP.

## AR. W2

Multi-update task completion is **NOT QUALIFIED** as final RE4 W2. Twenty-two completion events appear in the completed-prefix lifecycle ledger, but no final W2 witness file or 160-update closeout exists.

## AS. W3

Real zero-DVM actor is **NOT QUALIFIED** as final RE4 W3. The completed prefix has 362 zero-DVM actor/tx rows; a poisoned partial tx130 cannot be promoted into a full-run witness.

## AT. W4

Real nonterminal bootstrap is **NOT QUALIFIED** as final RE4 W4. The 129-row bootstrap ledger remains useful bounded evidence; the required final witness adjudication was not reached.

## AU. W5

Normal-horizon terminal/autoreset is **NOT ESTABLISHED**: zero observed terminal/autoreset events before the tx130 STOP.

## AV. W6

Post-autoreset learned training is **NOT ESTABLISHED** because no formal autoreset occurred.

## AW. W7

Runtime/P2 immutability ledger: 129/129 completed-prefix rows passed; required RE4 count is 160/160. tx130 did not reach S10, so W7 is **NOT QUALIFIED**.

## AX. task progress

The completed-prefix lifecycle ledger records 22 `task_completed` events, with maximum covered-viewpoint count 11. These are diagnostics and cannot override the failed 160-update target.

## AY. completion/P2/coverage

Completed-prefix task-completion and coverage signals were nonzero, but no final RE4 completion/P2/coverage consistency witness was emitted. Full-gate status: NOT ESTABLISHED.

## AZ. completion → decision reopen

The relevant lifecycle rows are preserved in the append-only ledger. The final W2/reopen adjudication was not reached; this report makes no unverified causal PASS claim.

## BA. numerical health

The 129 completed transaction rows are finite; tx130 failed from evidence-file replacement after seven critic/ValueNorm mutations. This is not evidence of a numerical failure, but full 160-update numerical health is unqualified.

## BB. rolling health

The rolling-health ledger has 129 rows. There is no tx160 terminal rolling-health receipt. Reward, loss, gradient, and coverage trajectories are descriptive, not performance success gates.

## BC. RE4 Layer-A durable receipt

The digest-checked final worker envelope was durably written and read back before App close. It reports `status=failure`, tx130, 129 ledger-qualified transactions, irreversible mutation, `partial_update=true`, and `route_poisoned=true`. [Receipt SHA-256](b2_t4_re4_artifacts/formal_worker_receipt.json): `821cdbe63e9143ba6d2209e40e1458daa64e90e4e5f0da2b890d11b3c0df8f7c`. Layer-A success gate: FAIL.

## BD. env close

The receipt records `env_close_attempted=true`, `env_close_pass=true`, and `app_close_invoked=true` before `SimulationApp.close()` was called. No mandatory worker evidence write after App close is claimed; close return to Python is not established.

## BE. EP-Q Layer-B process quiescence

| Predicate | RE4 value | Hard/diagnostic |
|---|---|---|
| Layer-A worker success receipt valid | false | HARD |
| wait completed | true | HARD |
| timeout | false | HARD |
| return code | 0 | HARD |
| worker PID absent | true | HARD |
| matching formal workers | empty | HARD |
| shutdown marker | false | DIAGNOSTIC |
| external Layer-B quiescence | true | HARD |
| overall RE4 qualification | false | HARD |

## BF. shutdown diagnostics

The captured shutdown marker was absent; EP-Q v2 correctly treats it as diagnostic only. Process-level quiescence passed; no inference is made that every Kit callback ran or `SimulationApp.close()` returned.

## BG. supervisor adjudication

[Supervisor result](b2_t4_re4_artifacts/formal_supervisor_result.json): one supervisor, one worker, zero retries, Layer A false, Layer B true, overall failed. The raw worker exit code was 0 despite its valid failure receipt; the supervisor did not convert exit code into success. [Final result](b2_t4_re4_artifacts/final_result.json) remains failed.

## BH. artifact inventory

The formal artifact directory contains 934 files (including retained large per-transaction details), approximately 175.7 MB. Required success-only W1–W7 and canonical alias ledgers were not fabricated after failure; the prefixed append-only ledgers, tx130 pre-mutation/rollout/actor/critic/failure details, unpromoted `.tmp`, worker receipt, supervisor, process quiescence, static, preflight, readiness, process config, CUDA, and final result are preserved. No model checkpoint was created.

## BI. static/private/public guards

Preflight static/private/public guards passed; production semantic modifications 0. Checkpoint I/O, public activation, and evaluation/playback remained 0. Public learned-policy route remains DORMANT / BLOCKED.

## BJ. exact execution counts

Pre-runtime Python invocations 24; final exact-runner readiness 1 PASS; formal supervisors/workers/retries `1/1/0`; CUDA probes/AppLaunchers/environments/initial resets/persistent learners `1/1/1/1/1`; physical transitions 260/320; production S10 129/160; ledger-qualified 129/160; bridges 128/159; episode generations observed `{0}`; terminal/autoreset 0; policy/continuation/forced-noop rows over qualified tx `33/1,092/423`; zero-DVM actor/tx rows 362; all-zero-DVM qualified tx 109; qualified actor backward/step `150/150`; qualified critic backward/step `1,290/1,290`; qualified critic classes `1,269/21`; qualified ValueNorm.update 1,290; qualified event returns 129; stock compute_returns 0. Failed tx130 additionally recorded critic optimizer steps 7 and ValueNorm updates 7, S10 0. W1–W6 not qualified; W7 129/160. Checkpoint/public/evaluation and git add/commit/push all 0. tx161 NOT STARTED.

## BK. retained nonclaims

RE4 normal-horizon learned-training integration is **NOT QUALIFIED**. This run does not establish W1–W7, a normal-horizon terminal/autoreset, post-autoreset training, 160-update numerical/Adam/ValueNorm continuity, checkpoint continuation, long/paper-scale training, public-policy readiness, reward improvement, convergence, or evaluation/playback readiness. Process quiescence says only that the original worker process terminated.

## BL. final classification

`PHASE-B2-T4-RE4-STOP-EVIDENCE-PERSISTENCE-PERMISSION-DENIED-AFTER-MUTATION` (source-backed handoff refinement). The raw immutable supervisor field remains `PHASE-B2-T4-RE4-STOP-FORMAL-WORKER-FAILURE`. RE4 is STOPPED / POISONED / NOT COMPLETE; its one authorized formal attempt is closed. No repair, retry, second worker, learner reconstruction, optimizer/ValueNorm reset, or checkpoint reload is permitted in this task.

## BM. GPT-review handoff

Independent review should inspect the tx130 failure receipt and `.tmp` residue, compare 129 S10 rows with the 129 append-only transaction rows and 128 bridges, confirm tx130's seven critic/ValueNorm mutations and no S10, and verify the failure receipt/Layer-B separation. Any investigation or repair of the Windows atomic-replacement failure requires a separately authorized phase. Do not resume from this poisoned learner, start tx161 or B2-R6, begin long training, save/load a checkpoint, activate the public route, stage, or commit.
