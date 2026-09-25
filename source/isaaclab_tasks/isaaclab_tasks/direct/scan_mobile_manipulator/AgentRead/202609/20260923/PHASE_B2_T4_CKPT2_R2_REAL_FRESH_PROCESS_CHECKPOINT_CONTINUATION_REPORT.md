# Phase B2-T4 CKPT2-R2 Real Fresh-Process Checkpoint Continuation Report

Date: 2026-09-23  
Run ID: `b2-t4-ckpt2-r2-20260923-real01-c94e7b31`  
Primary classification: **PHASE-B2-T4-CKPT2-R2-STOP-TRANSACTION-LEDGER**  
Inherited worker receipt: **PHASE-B2-T4-CKPT2-R2-STOP-PROCESS-A-UPDATE**  
Parent adjudication: **PHASE-B2-T4-CKPT2-R2-STOP-PROCESS-A-SEMANTIC-GATE**  
Retry count: **0**; retry permitted: **false**

## A. HISTORICAL PRESERVATION

CKPT2 and CKPT2-R1 remain **GPT REVIEW STOP CONFIRMED / HISTORICAL**. Pre-runtime preservation checks passed for both artifact inventories, harnesses, and reports. CKPT1 production sources and installed HARL hashes were unchanged. No historical PID, run ID, learner, environment, or checkpoint namespace was reused.

## B. R1 LEDGER-SCHEMA DEFECT

R1 attempted `dict(transaction.exact_execution_counts)['event_return_computations']`, but that key exists only in the campaign aggregate assembled after all transactions. The actual per-transaction count mapping contains actor/critic/ValueNorm and S10 counts, not the campaign aggregate key. The pure fixture reproduced `KeyError('event_return_computations')`.

## C. TRANSACTION EVENT-RETURN AUTHORITY

Source inspection and the R2 runtime both confirmed the transaction-local authority:

`transaction.real_audit.event_return_compute_count`

Its real runtime type was `int` and tx001 value was exactly `1`. The R1 `KeyError('event_return_computations')` did not recur. However, the separate transaction-identity binding described below was wrong, so no accepted ledger row was published.

## D. LEDGER MAPPING REPAIR

The event-return mapping itself crossed the historical R1 failure boundary. The R2 binder then incorrectly assumed transaction identity at `transaction.r5_transaction.transaction_id`. The real nested object type was `B2RFullLearnerUpdateEvidenceV1`, which has no `transaction_id` field. The source-backed identity is available through its quiescence evidence (`transaction.r5_transaction.quiescence_evidence.update_id`), while the full update authority owns the separate transaction ID before the returned evidence is constructed.

The pre-runtime positive fixture modeled the nested identity incorrectly and therefore did not faithfully cover the production result schema. Runtime raised:

`AttributeError: 'B2RFullLearnerUpdateEvidenceV1' object has no attribute 'transaction_id'`

This is a test-side ledger-schema binding failure. Per the source freeze and no-retry rule, the harness was not edited and the attempt was not repeated.

## E. LR/FINGERPRINT REPAIR PRESERVATION

Pre-runtime preservation passed. Runtime tx001 completed collection immutability and reached the real learner transaction; the historical LR/fingerprint mismatch did not recur.

## F. PROCESS-A SEMANTIC-GATE PRESERVATION

The gate remained fail-closed. Process A later returned OS code 0 during `SimulationApp.close()`, but had no success receipt, three accepted ledger rows, checkpoint, or validation. The parent wrote `DENY` and did not launch B.

## G. PRE-RUNTIME QUALIFICATION

- CKPT1 focused suite: **6/6 PASS**, expected negative matrix **25/25 PASS**.
- R1 KeyError reproduction: **PASS**.
- Ledger positive fixture: **PASS**, but later shown incomplete for the production identity schema.
- Ledger negative matrix: **7/7 expected STOP**.
- Silent defaults: **0**.
- LR repair preservation and A→B gate preservation: **PASS**.
- Frozen R2 harness SHA-256: `ff152638626cef06c79641c0e032d94b0537965e7a07136cc539584311d2e2f7`.

The production-shaped-fixture claim is narrowed by the runtime result: it was adequate for event-return authority but not for nested transaction identity.

## H. PROCESS-A TX001-TX003

Process A PID `36600` used one fresh interpreter, one CUDA readiness path, one AppLauncher, one environment, and one persistent learner. tx001 completed two physical collection steps and the real learner transaction returned successfully. Evidence recorded 15 actor optimizer steps, 10 critic optimizer steps, and 10 live ValueNorm updates. The ledger binder validated event-return count `1`, then stopped on the invalid transaction-ID path before append. tx002 and tx003 were not started. Learner mutation occurred; the route reported `learner_poisoned=false`; the process was discarded.

## I. CHECKPOINT SAVE

Not reached. Save count and published generation count are **0**. No checkpoint root, manifest, or `latest.json` exists.

## J. PARENT A→B ADJUDICATION

The parent observed A inactive but found no A semantic-success receipt, no accepted ledger rows, no save, and no generation. Decision: **DENY**. Process B launch count: **0**.

## K. PROCESS-B STRICT LOAD

Not reached because B was not launched. Strict-load count: **0**.

## L. CUDA DEVICE RESTORATION

Not reached. Process A CUDA execution was real, but no checkpoint state was restored into B.

## M. CROSS-PROCESS STATE EQUALITY

Not established; A produced no pre-save checkpoint state and B did not exist.

## N. OPTIMIZER CONTINUITY

Not established across a fresh process. tx001 performed real optimizer mutation in A only.

## O. VALUENORM CONTINUITY

Not established across a fresh process. tx001 performed 10 real ValueNorm updates in A only.

## P. PROGRESSION / LR CONTINUITY

Not established across a checkpoint boundary. tx001 progression advanced in the discarded process, but no progression checkpoint was published.

## Q. PROCESS-B TX004-TX006

tx004, tx005, tx006, and tx007 were **not started**.

## R. PROCESS QUIESCENCE

Process A PID `36600` and parent PID `29300` are inactive. Matching R2 worker count after termination is **0**. Environment close recorded **PASS**. There was no retry, second A, or B.

## S. FINAL CHECKPOINT-CONTINUATION VERDICT

**STOP — PHASE-B2-T4-CKPT2-R2-STOP-TRANSACTION-LEDGER.** R2 crossed the historical event-return `KeyError` boundary but did not establish a correct complete transaction-ledger schema binding. Real fresh-process optimization checkpoint continuation remains **NOT ESTABLISHED**. The failure was post-update and test-side; learner mutation occurred, the route was not marked poisoned, checkpoint generation remained zero, and B was not launched. No GPT PASS is claimed. R15, evaluation/playback, paper-scale training, and public learned-policy activation remain unauthorized.

## Ledger table

| Transaction | Event-return authority path | Event-return count | Update returned | Ledger appended | Result |
|---|---|---:|---:|---:|---|
| A tx001 | `transaction.real_audit.event_return_compute_count` | 1 | Yes | No | STOP — invalid transaction identity path |
| A tx002 | Not started | N/A | No | No | NOT STARTED |
| A tx003 | Not started | N/A | No | No | NOT STARTED |
| B tx004 | Not started | N/A | No | No | NOT STARTED |
| B tx005 | Not started | N/A | No | No | NOT STARTED |
| B tx006 | Not started | N/A | No | No | NOT STARTED |

## Continuity table

| State | A pre-save | B post-load | Equal | B after tx004 | Continuity |
|---|---|---|---:|---|---:|
| actor weights | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| actor Adam steps/moments | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| critic weights | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| critic Adam steps/moments | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| ValueNorm | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| progression | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| LR schedule position | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| semantic config | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |

## Evidence index

- `b2_t4_ckpt2_r2_artifacts/process_a/failure_receipt.json`
- `b2_t4_ckpt2_r2_artifacts/process_a/core_tx1_pre_mutation.json`
- `b2_t4_ckpt2_r2_artifacts/process_a_parent_adjudication.json`
- `b2_t4_ckpt2_r2_artifacts/process_b_launch_gate.json`
- `b2_t4_ckpt2_r2_artifacts/parent/parent_process_inventory.json`
- `b2_t4_ckpt2_r2_artifacts/failure_receipt.json`
- `b2_t4_ckpt2_r2_artifacts/transaction_event_return_authority_inventory.json`
- `b2_t4_ckpt2_r2_artifacts/transaction_ledger_positive_qualification.json`
- `b2_t4_ckpt2_r2_artifacts/ckpt2_r2_pre_runtime_freeze.json`
