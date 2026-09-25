# Phase B2-T4-RE2 Normal-Horizon Learned-Training Integration Qualification Report

Date: 2026-09-14

Classification:
`PHASE-B2-T4-RE2-STOP-TX2-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE`

## A. Repository authority

The run used branch `main` at `b71d85a32f51be6ada324f870813a56bb45dd396`; `HEAD`, `origin/main`, and their merge-base were equal. The pre-existing 359 staged monthly-archive migration paths remained outside RE2 and were not touched. Their staged-index SHA-256 remained `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; the monthly path-set SHA-256 remained `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No RE2 path was staged.

## B. Reviewed starting authority

B2-R0 through B2-R7 and B2-T0 through B2-T3 remain `GPT REVIEW PASS / CLOSED`. This run used only the reviewed private learned-training route. It does not revise any earlier review result.

## C. Historical B2-T4 preservation

The original B2-T4 attempt remains `STOPPED / HISTORICAL / NOT COMPLETE` with classification `PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`.

## D. B2-T4-NR authority

B2-T4-NR remains `GPT REVIEW PASS / CLOSED`. Its conditional terminal reconciliation, empty/empty nonterminal handling, mixed-grid behavior, and fail-closed contracts were re-run pre-runtime: 5/5 suite cases and 14/14 terminal-matrix cases passed.

## E. B2-T4-RE1 poisoned-history preservation

B2-T4-RE1 remains `STOPPED / HISTORICAL / POISONED / NOT COMPLETE`. Its tx001 S10 artifact and serializer failure remain immutable historical evidence. RE2 neither continued nor reused the RE1 learner, optimizer, ValueNorm, process, or route.

## F. B2-T4-SR authority

Per the authorization, B2-T4-SR is `GPT REVIEW PASS / CLOSED`. Its serializer suite was replayed before RE2 and passed 7/7 positive cases, 12/12 negative cases, the retained RE1 tx001 replay, ledger roundtrip, and complete post-S10 bookkeeping replay.

## G. Production source identities

Production semantics were not modified. The two primary production identities were exact:

- `assignment_event_training_full_transaction.py`: `a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de`
- `assignment_event_training_real_isaac_adapter.py`: `b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014`

The full repo and installed-HARL identity set is retained in `re2_static_authority.json` and the formal process-config artifact.

## H. SR runner/helper identities

- SR-qualified RE1 candidate: `44ef0a289225a34c21bb31451465422e33fa20a713eb9a3ed4a715e97a0ff5d6`
- SR reason-grid helper: `dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358`
- Retained RE1 tx001 S10: `e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649`
- RE2 wrapper: `263d48ca5988ab809ff63c5e11b4c8364d04159bd0cd96f4e0675d2465f8b40b`
- RE2 transformed source: `518a102d9f7328c5c704032984bff00846a9968c52636e1ead29e19db493ecb9`

## I. Schema identifier audit

The live implementation and machine artifacts use `b2_t4_sr_termination_reason_grid_v1` and `b2_t4_sr_classification_precedence_v1`. Historical SR prose used the descriptive token `b2_t4_sr_termination_reason_grid_T_E_1_v1`; that prose/implementation naming discrepancy was recorded without altering semantics. Runtime geometry remained canonical `[T,E,1]`, here `[2,2,1]`.

## J. Files created/modified

RE2 created the test-side wrapper, preflight artifacts, formal evidence artifacts, failure adjudication, this report, and a byte-exact TASK_PROGRESS archive. `AgentRead/TASK_PROGRESS.md` was updated after the archive. Production source modifications attributable to RE2: 0. Installed HARL modifications: 0.

Two pre-mutation test-side wiring corrections were made before the final readiness PASS:

1. The retained qualified artifact key `re1_step_details` was preserved as an artifact-schema field instead of being renamed with run identity.
2. Readiness summary success was read from the existing `s7_s8_s9_s10` vector instead of a nonexistent `s10_complete` field.

Neither correction changed production semantics. No correction occurred after formal mutation began.

## K. Pre-runtime qualification

Twenty Python invocations were made before formal launch. The approved interpreter, compilation, static authority, final readiness replay, NR, SR, I5b, lifecycle-decision, controlled full-transaction/zero-DVM, real-shape, critic-CG, ValueNorm fingerprint, and T2/T3 observer nonmutation gates passed. The exact sequence and the two stopped pre-mutation wiring attempts are recorded in `re2_preflight_summary.json`.

The focused critic and ValueNorm qualifications exercised CUDA tensors, but they were preflight qualifications, not the formal same-worker CUDA/CUBLAS readiness receipt. Preflight created no AppLauncher, real environment, or formal persistent learner.

## L. RE2 runner-readiness replay

The final qualified replay count was exactly 1 PASS. It exercised the exact RE2 serializer and append-ledger path, canonical shape `[2,2,1]`, all eight applicable bookkeeping ledgers, classification metadata, source/payload nonmutation, and zero learner mutations. The two earlier invocations stopped before serializer/ledger/learner mutation and are retained as pre-mutation wiring attempts, not formal retries.

## M. CUDA/CUBLAS readiness

The formal worker executed exactly one same-process CUDA/CUBLAS probe before AppLauncher. `torch.mm` on two 2x2 FP32 CUDA tensors returned `[[19,22],[43,50]]`; classification was PASS. No retry occurred.

## N. Fresh formal process

One formal supervisor launched one mutation-bearing worker with PID 13316. The worker created one AppLauncher, one environment, one explicit initial reset, and one persistent learner. `fresh_process=true`, `historical_route_reused=false`, and `distinct_learner_constructions=1`. The worker result was valid but failed; the supervisor classified the run failed. Formal retries: 0.

## O. Exact runtime config

| Field | Value |
|---|---|
| Environment | `Isaac-Scan-Mobile-Manipulator-Direct-v0` |
| Profile | `event_gated_local_mrta` |
| Device | `cuda:0` |
| E / M / N | 2 / 3 / 12 |
| T | 2 |
| Actor epochs / minibatches | 5 / 2 |
| Critic epochs / minibatches | 5 / 2 |
| ValueNorm | enabled |
| Sim dt / control decimation / control step | 1/60 s / 6 / 0.1 s |
| Environment horizon | 30.0 s / max 300 steps |
| Fixed order | false |
| Harness horizon override | false |

## P. Horizon separation

The normal environment horizon remained 30.0 seconds / 300 control steps while learner rollout length remained `T=2`. No short-horizon override leaked into the environment. Four physical transitions were executed before STOP; this is not normal-horizon completion evidence.

## Q. Update/ledger success definition

A qualified update requires production S7/S8/S9/S10 plus all applicable append-only ledger rows and an unpoisoned bridge to the next update. tx001 reached S10 and its applicable ledgers. tx002 collected a valid fresh rollout but failed before its learner mutation because every actor row was continuation-only (`active-and-DVM=0`). Therefore RE2 is incomplete and poisoned even though tx001 was individually quiescent.

## R. Update-ID inventory

- `b2-t4-re2-normal-horizon-training-13316-tx001`: S10 complete; one transaction-ledger row.
- `b2-t4-re2-normal-horizon-training-13316-tx002`: collection validated; failed before learner mutation; no S10 or transaction-ledger row.
- tx003 through tx160: not started.
- tx161: not started.

## S. Episode/update/physical-step timeline

| Tx | Physical steps | Episode generation | Result |
|---:|---:|---:|---|
| 1 | 1–2 | `[0,0] -> [0,0]` | S10 quiescent, ledger row written |
| 2 | 3–4 | 0 | collection valid; STOP before learner mutation |
| 3–160 | — | — | not started |

There were zero terminal/autoreset events and zero learner-boundary environment resets.

## T. Lifecycle decision summary

tx001 contained six policy-decision rows at step 1 and six forced-continuation rows at step 2. tx002 contained twelve forced-continuation rows, zero policy calls, zero DVM rows, and preserved learner state exactly during collection. Missing, duplicate, continuation-resample, and observer-mutation faults were 0 in the retained evidence.

## U. Actor order distribution

Only tx001 reached actor training. Its order was `[1,2,0]`; distribution: one occurrence. No multi-update distribution claim is established.

## V. Zero-DVM runtime statistics

tx001 DVM rows by actor were `{0:2,1:2,2:2}`. tx002 had zero DVM rows for every actor across the full batch. The real adapter fail-closed with `real batch has no active-and-DVM actor training opportunity`; hence the mandatory successful real zero-DVM actor witness was not established.

## W. Actor plan/update counts

tx001 expected and observed actor backward/optimizer-step counts were `[5,5,5]` / `[5,5,5]`, total 15/15. tx002 performed 0/0 because it stopped before mutation. Campaign total: 15 backward and 15 optimizer steps.

## X. Factor audits

tx001 factor transitions were finite, strictly positive, recurrence-exact, and off-DVM exact-one. All three actor segments completed. No tx002 factor audit exists because no actor update plan was admitted.

## Y. Critic classifications

tx001 produced `VALID_NONZERO_UPDATE: 5` and `VALID_ZERO_EFFECTIVE_UPDATE: 5`; every zero-effective minibatch carried its mathematical clipped-plateau evidence. tx002 produced no critic classification.

## Z. Critic/ValueNorm counts

Campaign totals were critic backward 10, critic optimizer-step 10, and live ValueNorm.update 10, all from tx001. The tx001 counts matched the 5 epochs x 2 minibatches plan.

## AA. Nonterminal bootstrap evidence

tx001 passed the real nonterminal bootstrap contract: four NONE rows, no terminal rows, final current value evaluated, event-return path used once, and stock `compute_returns` unused. This is one candidate, not the required 160-update campaign result.

## AB. Terminal/bootstrap evidence

No terminal occurred in four physical steps. Expected and observed terminal keys were empty for tx001; tx002 also retained empty terminal history. Normal-horizon terminal/autoreset evidence was not reached.

## AC. NR terminal reconciliation runtime evidence

tx001 reconciliation passed with missing=0, extra=0, duplicates=0 and expected/observed `0/0`. No tx002 ledger row was appended. Campaign qualification was not established.

## AD. SR serializer runtime evidence

The SR serializer successfully encoded tx001's `[2,2,1]` all-NONE grid and its applicable ledgers. Serializer faults: 0. The run failed later in tx002 real-evidence binding, not serialization.

## AE. Actor Adam continuity

tx001 showed monotonic Adam progression through five steps per actor and finite optimizer state. Cross-update continuity was not established because tx002 did not enter mutation.

## AF. Critic Adam continuity

tx001 showed monotonic Adam progression through ten critic steps and finite optimizer state. Cross-update continuity was not established.

## AG. ValueNorm continuity

tx001 performed ten live, finite ValueNorm mutations. Cross-update continuity was not established.

## AH. 159-bridge summary

Required: 159/159. Observed qualified bridge rows: 0/159. Bridge-1 pre/post-collection artifacts were written and show collection preserved the persistent learner, but the inherited real-evidence binding rejected the continuation-only tx002 batch before the bridge ledger could be qualified. `bridge_failed=true`.

## AI. Collection learner immutability

tx002 learner state digest was exactly `f6cb5f45a109cf24de1bfb27fe71070dcaf347592c68347c6ade178f7df5b5c0` before and after physical steps 3–4. Collection did not mutate the learner.

## AJ. Learner-update runtime/P2 immutability

tx001 passed: lifecycle/runtime digest before and after the learner update was equal, learner did not advance simulation, and source/config identity was unchanged. Count: 1/160 PASS. tx002 had no learner update.

## AK. W1 cross-update ownership

A partial cross-boundary candidate exists: env0/robot0 claimed task 10 in tx001 and remained its owner through tx002 steps 3–4 without policy calls. However bridge qualification did not complete, so W1 is **NOT ESTABLISHED**.

| Physical step | Tx | Episode gen | Robot | Task | Owner | Robot state | Task state | Decision? | Policy call | Effective task | Progress | Learner boundary | Event | Coverage |
|---:|---:|---:|---:|---:|---:|---|---|---|---:|---:|---|---|---|---:|
| 1 | 1 | 0 | 0 | 10 proposal | 10 after | NEEDS_ASSIGNMENT | claimed | yes | 1 | 10 | local 1 | no | task_claimed | 0 |
| 2 | 1 | 0 | 0 | 10 | 10 | EXECUTING | claimed | no | 0 | 10 | local 2 | S10 after row | none | 0 |
| 3 | 2 | 0 | 0 | 10 | 10 | EXECUTING | claimed | no | 0 | 10 | continuation | first post-S10 row | none | 0 |
| 4 | 2 | 0 | 0 | 10 | 10 | EXECUTING | claimed | no | 0 | 10 | continuation | tx002 collection end | none | 0 |

## AL. W2 multi-update completion

No TASK_COMPLETED event occurred. W2 is **NOT ESTABLISHED**.

## AM. W3 real zero-DVM actor

tx002 supplied a real all-zero-DVM batch, but the adapter rejected it before a valid skipped-actor transaction could complete. W3 is **NOT ESTABLISHED**.

## AN. W4 real nonterminal bootstrap

tx001 is a valid real nonterminal bootstrap candidate, but the formal W1–W7 postprocessor was never reached. Overall W4 qualification is **NOT ESTABLISHED** for RE2.

## AO. W5 normal-horizon terminal/autoreset

No terminal/autoreset was observed. W5 is **NOT ESTABLISHED**.

## AP. W6 post-autoreset learned training

No autoreset occurred. W6 is **NOT ESTABLISHED**.

## AQ. W7 runtime/P2 immutability

One transaction passed and 159 were required: `1/160 PASS`. W7 is **NOT ESTABLISHED**.

## AR. Task-progress trajectory

Across physical steps 1–4, six tasks remained owned/executing, completed tasks remained 0, episode generation remained 0, and coverage remained 0. No positive task-progress claim is available.

## AS. Completion/P2/coverage consistency

Observed values were internally consistent at zero: TASK_COMPLETED=0, completed-task delta=0, coverage max/final=0/0. The mandatory positive completion/coverage gate failed by absence of evidence.

## AT. Completion -> decision reopen

Not reached; no completion occurred.

## AU. Terminal-ledger continuity

tx001 terminal reconciliation and empty terminal-ledger rollover passed. No terminal boundary and no tx002 S10 existed, so campaign continuity is not established.

## AV. Serializer/bookkeeping continuity

tx001 wrote all applicable ledgers successfully. tx002 failed before append bookkeeping; transaction ledger rows are 1/160 and bridge ledger rows are 0/159. Campaign continuity is not established.

## AW. Event-return compute-once

Event-return computations: 1, all in tx001. Stock `compute_returns`: 0. tx002 did not reach returns.

## AX. S7/S8/S9/S10 summary

Observed production receipts: `1/1/1/1`; required: `160/160/160/160`. tx001 was quiescent; tx002 stopped after collection and before mutation.

## AY. Numerical health

All retained tx001 actor, critic, optimizer, ValueNorm, loss, gradient, factor, and rolling-health data were finite. This is one-update numerical evidence only; 160-update numerical health is not established.

## AZ. Diagnostic training metrics

tx001 actor loss mean was `-0.4232252656`, actor gradient-norm mean `3.4599605901`, critic loss mean `1.2040432155`, critic gradient-norm mean `17.9020537114`, and diagnostic team reward sum `-0.0706666689`. These metrics are descriptive and do not support a training-quality claim.

## BA. Rolling health

One finite rolling-health row was written with `route_poisoned=false` at tx001 S10. The later tx002 failure authoritatively poisons the overall route; the tx001 row must not be read as final campaign health.

## BB. Artifact inventory

Primary artifacts under `202609/20260914/b2_t4_re2_artifacts/`:

- `re2_static_authority.json` — 206,887 bytes — SHA-256 `97908f50de00d63ae88c3538d6d3401364c92207a3dbde04918fdf22037da724`
- `re2_runner_readiness_replay.json` — 57,099 bytes — SHA-256 `1c27cc064e8be006343e78f4f9ea6056656af397280f9e887369e79616d3eb0c`
- `re2_preflight_summary.json` — 3,358 bytes — SHA-256 `50af30f0f2fe547fe8ce3e5d89fc673255fa833968bc8f6c6f891812671933e9`
- `b2_t4_re2_formal_supervisor_result.json` — 228,609 bytes — SHA-256 `690af90b443e62a77c19e88c52de14c92a28850be8cf746cdb2cc99019802e9a`
- `..._cuda_cublas_readiness.json` — SHA-256 `a57b28dc04fd0c0f283eab0ca1de6c3170b8a9330e832d42509ca0211d17a212`
- `..._process_config_authority.json` — SHA-256 `51fa1f06db0f772fdd752bf27c18d7d4880f126557eb0f388ca765f85704cef8`
- `..._tx1_s10.json` — SHA-256 `90dfae198af17ee49362bd43f1de0eabe078bf01b46388034aba745f6d17af71`
- `..._tx2_rollout_decision_evidence.json` — SHA-256 `93b4624167ce8b8dd052e4d3ab4c3cf105b34cd1a140ee840313edc2f8935fda`
- `..._final_result.json` — SHA-256 `0f50df029eec40f5e4dcc69f3420078232b2882cf9a7061ece7efc0890529185`
- `re2_failure_adjudication.json` — 1,654 bytes — SHA-256 `2659989026f652458867fa61931a871da94e499792d3573fbfe7dc535da39160`; reporting-only adjudication created after STOP.

Also retained are tx001 pre-mutation, rollout, actor/factor, critic, eight applicable JSONL ledgers, bridge-1 pre/post-collection evidence, and the complete SR preflight directory. No model checkpoint was written.

## BC. Static/private/public guards

Static authority and private-route guards passed. Production semantic modifications=0, public activations=0, checkpoint weight I/O=0, and evaluation/playback=0. Public learned-policy route remains `DORMANT / BLOCKED`.

## BD. Exact execution counts

```text
pre-runtime qualification invocations: 20
final RE2 runner-readiness replay: 1 PASS
formal CUDA/CUBLAS probes: 1 PASS
formal supervisor: 1
mutation-bearing worker: 1
formal retries: 0
AppLauncher: 1
environment: 1
explicit initial reset: 1
persistent learner: 1
physical environment steps: 4
production S10 transactions: 1 / 160
ledger-qualified transactions: 1 / 160
bridges: 0 / 159
actor backward / optimizer.step: 15 / 15
critic backward / optimizer.step: 10 / 10
ValueNorm.update: 10
event returns / stock compute_returns: 1 / 0
S7 / S8 / S9 / S10: 1 / 1 / 1 / 1
runtime/P2 immutability: 1 / 160 PASS
terminal/autoreset: 0
TASK_COMPLETED / completed delta: 0 / 0
coverage max / final: 0 / 0
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
production semantic modifications: 0
tx161 started: 0
```

The worker subprocess returned code 0 with a valid `status=failed` result; the authoritative supervisor returned failure because the worker status was not passed. No result was reinterpreted as success.

### Primary transaction status table

| Tx | S10 complete | Ledger qualified | Episode gen | Policy rows | Continuation rows | Zero-DVM actors | Terminal? | Completion? | Bridge PASS |
|---:|---|---|---:|---:|---:|---:|---|---|---|
| 001 | yes | yes | 0 | 6 | 6 | 0 | no | no | N/A before next collection |
| 002 | no | no | 0 | 0 | 12 | 3 | no | no | no — failed before append |
| 003–160 | not started | not started | — | — | — | — | — | — | — |

## BE. Retained nonclaims

RE2 does not establish W1–W7 overall qualification, 160-update stability, normal-horizon terminal behavior, positive task progress, long-training execution readiness, checkpoint continuation, training quality, convergence, public learned-policy readiness, or paper-scale readiness. B2-R6 remains separate and not started.

## BF. Final quiescence

tx001 individually reached `S10_QUIESCENT`, but the run later failed at tx002 after irreversible tx001 mutation. Authoritative learner-route state: `partial_update=true`, `route_poisoned=true`, so campaign quiescence is **FAIL / NOT QUALIFIED**. Process/resource quiescence passed: formal worker PID 13316 was absent and no RE2 Python runner remained. No learner reconstruction, optimizer reset, ValueNorm reset, checkpoint reload, or continuation was performed.

## BG. Final classification

`PHASE-B2-T4-RE2-STOP-TX2-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE`

Cause: tx002 was a legitimate normal-horizon continuation-only rollout (12 continuation rows, 0 policy calls, 0 DVM rows). The inherited real-adapter evidence binding required at least one active-and-DVM actor training opportunity and raised before tx002 learner mutation. Because tx001 had already irreversibly mutated the persistent learner, the authorized failure policy mandates `partial_update=true`, `route_poisoned=true`, and STOP. No patch or retry is permitted for this run.

## BH. GPT-review handoff

B2-T4-RE2 is stopped, poisoned, and not complete. B2-T4-SR remains closed; RE1 and original B2-T4 histories remain preserved. Independent GPT review should inspect whether the continuation-only batch is a valid normal-horizon condition that conflicts with the inherited per-transaction evidence binding. This report does not authorize a repair, a new retry, tx161, B2-R6, checkpoint I/O, public activation, evaluation/playback, or long/paper-scale training.

The byte-exact pre-rewrite TASK_PROGRESS archive is `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE2_STOP_HANDOFF_20260914.md`: 10,416 bytes, SHA-256 `7ff65ea0b79eb1aa99c69d1c3ccbff5ce148cd61d6e06ee31c0b1728b0cf9f71`.

No `git add`, commit, push, reset, checkout, or clean operation was performed.
