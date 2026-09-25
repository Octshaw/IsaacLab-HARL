# PHASE B2-T4 CKPT2-R4 REAL FRESH-PROCESS CHECKPOINT CONTINUATION REPORT

Classification: `PHASE-B2-T4-CKPT2-R4-STOP-TRANSACTION-LEDGER`

Run ID: `b2-t4-ckpt2-r4-20260923-real01-7d4e2a91`

This was the single authorized R4 attempt. It is closed with zero retries and awaits independent GPT review. R4 repaired the R3 import-namespace failure and reached real Process-A learner execution, but it did not qualify checkpoint continuation.

## A. HISTORICAL PRESERVATION

CKPT2, R1, R2, and R3 harnesses, reports, and artifact inventories passed their frozen hash/count checks. CKPT1 production sources and the four installed HARL files passed their expected hashes. No historical evidence was rewritten.

## B. R3 IMPORT-SIDE-EFFECT ROOT CAUSE

R3 loaded production schema helpers by inserting synthetic `isaaclab_tasks` package objects in its runtime interpreter. The synthetic `scan_mobile_manipulator` package had no `ScanMobileManipulatorEnv`, so Gym entry-point resolution failed before environment construction.

R4 reproduced that exact condition only in PID 38384, the short-lived pure qualification subprocess. It did not remove modules from `sys.modules`; process isolation was the repair.

## C. PURE/RUNTIME PROCESS ISOLATION

- Orchestration parent: PID 19096.
- Clean baseline: PID 26612, no production task package loaded, exited before A.
- Pure schema qualification: PID 38384, production dataclass/schema checks PASS, exited before A.
- Process A: PID 24152, fresh interpreter and real package import after AppLauncher.
- All four PIDs are inactive. Cross-process Python object sharing was impossible by construction.

## D. IDENTITY/LEDGER CONTRACT PRESERVATION

The preserved contract is `ONE_TO_ONE_BOUND`, CASE C. The ledger identity remains `transaction_index` plus `transaction.r5_transaction.quiescence_evidence.update_id`; no returned `transaction_id` was invented. Event-return authority remains `transaction.real_audit.event_return_compute_count`.

Pure qualification passed production schema parity, the ledger-v2 positive fixture, and 8/8 expected identity STOP cases. Real tx001 appended one compliant row. Real tx002 returned learner evidence but failed the frozen actor-step ledger predicate before append.

## E. PRE-RUNTIME QUALIFICATION

- CKPT1 focused tests: 6/6 PASS.
- CKPT1 negative cases: 25/25 expected rejection; zero unexpected acceptance.
- Clean interpreter baseline: PASS.
- R3 import failure reproduction: PASS.
- Production schema parity: PASS.
- LR/fingerprint pure boundary and A→B gate matrices: PASS.
- Source freeze before A: PASS; R4 harness SHA-256 `f330ba2f27ef3fd40cb232853fd9be9d53846e9cbed8973321a691f38bee967d`.

## F. PROCESS-A REAL PACKAGE IDENTITY

PASS. PID 24152 resolved the package to the repository `__init__.py`, observed a real `ScanMobileManipulatorEnv` class from `scan_mobile_manipulator_env`, and observed no synthetic placeholder. Gym registration resolved to `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`.

## G. PROCESS-A ENVIRONMENT CREATION

PASS. `gym.make` returned one environment whose unwrapped type was `ScanMobileManipulatorEnv`. This confirms R4 crossed the exact pre-environment boundary that stopped R3.

## H. PROCESS-A TX001-TX003

- tx001: real transaction returned; ledger row appended; actor steps `(5, 5, 5)`; critic steps 10; ValueNorm updates 10; event-return count 1; LR/fingerprint boundary PASS.
- tx002: real learner transaction returned, but ledger append STOPPED because actor steps were `(5, 5, 10)` while the frozen R3-derived binder required `(5, 5, 5)`.
- tx003: NOT STARTED.

The STOP is source-backed at `LEDGER-ACTOR-UPDATES`. The evidence establishes a mismatch between the real returned count tuple and the frozen test-side ledger predicate. It does not, by itself, adjudicate whether the real actor-2 count or the uniform-count predicate is the correct future contract.

## I. CHECKPOINT SAVE

NOT REACHED. Save count is 0; no checkpoint directory or generation was published.

## J. PROCESS-A SEMANTIC SUCCESS / PARENT GATE

STOP. Process A had no success receipt, only 1/3 durable ledger rows, and no checkpoint. The parent correctly denied B. Process B was not launched.

The worker's raw failure receipt used `STOP-PROCESS-A-UPDATE`; the final narrow adjudication is `STOP-TRANSACTION-LEDGER` because the real tx002 learner call returned and the failure arose in the post-return ledger binder.

## K. PROCESS-B FRESH PACKAGE / ENVIRONMENT

NOT REACHED. No Process-B PID exists.

## L. STRICT CHECKPOINT LOAD

NOT REACHED. Load count is 0.

## M. CUDA DEVICE RESTORATION

NOT REACHED for B. Process A CUDA warm-up and real execution succeeded, but no checkpoint load occurred.

## N. CROSS-PROCESS STATE EQUALITY

NOT REACHED because no checkpoint was saved and B was not launched.

## O. OPTIMIZER CONTINUITY

NOT REACHED. No A-pre-save/B-post-load comparison exists.

## P. VALUENORM CONTINUITY

NOT REACHED. No A-pre-save/B-post-load comparison exists.

## Q. PROGRESSION / LR CONTINUITY

Cross-process continuation was NOT REACHED. Within real tx001, LR was applied before the pre-collection fingerprint, no LR mutation occurred during collection, progression advanced once, and the next LR was primed at the post-update boundary.

## R. PROCESS-B TX004-TX006

NOT STARTED. tx004, tx005, tx006, and tx007 were not started.

## S. PROCESS QUIESCENCE

PASS. Parent PID 19096, clean PID 26612, pure PID 38384, and A PID 24152 are inactive. Matching Python worker count is zero. Environment close was PASS. The route was not reported poisoned. Retry count is zero.

## T. FINAL CHECKPOINT-CONTINUATION VERDICT

`PHASE-B2-T4-CKPT2-R4-STOP-TRANSACTION-LEDGER`

R4 proves that the R3 import-side-effect repair works through real package identity, registration, environment construction, and real Process-A learner execution. It does not prove a 3+3 continuation, checkpoint save/load, cross-process state equality, or optimizer/ValueNorm/progression continuation. No R15, evaluation, playback, paper-scale training, or public-route activation is authorized.

## Import-isolation table

| Process | Production schema import | Synthetic package allowed | Real task package required | Result |
|---|---:|---:|---:|---|
| Parent | No | No | No | PASS |
| Pure qualification subprocess | Yes | Yes, isolated only | No | PASS |
| Process A | Runtime modules only | No | Yes | PASS |
| Process B | Not launched | No | Yes if reached | NOT REACHED |

## Ledger table

| Tx | transaction_index | update_id | Event-return count | Ledger appended | Result |
|---|---:|---|---:|---:|---|
| A tx001 | 1 | `b2-t4-ckpt2-r4-20260923-real01-7d4e2a91-tx1` | 1 | Yes | PASS |
| A tx002 | 2 | expected run-local tx2 identity; returned transaction not durably ledgered | 1 | No | STOP: actor steps `(5,5,10)` |
| A tx003 | 3 | — | — | No | NOT STARTED |
| B tx004 | 4 | — | — | No | NOT STARTED |
| B tx005 | 5 | — | — | No | NOT STARTED |
| B tx006 | 6 | — | — | No | NOT STARTED |

## Continuity table

| State | A pre-save | B post-load | Equal | B after tx004 | Continuity |
|---|---|---|---:|---|---:|
| actor weights | Not produced | Not reached | — | Not reached | NOT ESTABLISHED |
| actor Adam steps/moments | Not produced | Not reached | — | Not reached | NOT ESTABLISHED |
| critic weights | Not produced | Not reached | — | Not reached | NOT ESTABLISHED |
| critic Adam steps/moments | Not produced | Not reached | — | Not reached | NOT ESTABLISHED |
| ValueNorm | Not produced | Not reached | — | Not reached | NOT ESTABLISHED |
| progression | tx001 advanced locally; no pre-save state | Not reached | — | Not reached | NOT ESTABLISHED |
| LR schedule position | tx001 local boundary PASS | Not reached | — | Not reached | NOT ESTABLISHED |
| semantic config | Frozen R4 config | Not reached | — | Not reached | NOT ESTABLISHED |

## Evidence index and non-claims

Primary evidence is under `b2_t4_ckpt2_r4_artifacts/`, especially `final_result.json`, `transaction_ledger_failure_adjudication.json`, `failure_receipt.json`, `process_a/failure_receipt.json`, `process_a/transaction_ledger.jsonl`, `process_a_parent_adjudication.json`, `process_b_launch_gate.json`, and `process_quiescence.json`.

No production checkpoint code or installed HARL file was changed. Git add/commit/push counts are 0/0/0. This STOP must not be promoted to checkpoint-continuation qualification or public learned-policy readiness.
