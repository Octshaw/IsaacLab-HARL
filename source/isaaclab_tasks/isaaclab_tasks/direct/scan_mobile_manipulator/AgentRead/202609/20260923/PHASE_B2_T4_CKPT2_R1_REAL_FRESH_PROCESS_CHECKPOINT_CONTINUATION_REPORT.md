# Phase B2-T4 CKPT2-R1 Real Fresh-Process Checkpoint Continuation Report

Date: 2026-09-23  
Run ID: `b2-t4-ckpt2-r1-20260923-real01-a83f5d2c`  
Primary classification: **PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-UPDATE**  
Parent adjudication: **PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-SEMANTIC-GATE**  
Retry count: **0**; retry permitted: **false**

## A. HISTORICAL CKPT2 PRESERVATION

Historical CKPT2 remains **GPT REVIEW STOP CONFIRMED / HISTORICAL / PRE-CHECKPOINT-SAVE / NOT POISONED / NO RETRY**. Its 35-file artifact inventory, old harness, and report passed preservation checks. Old harness SHA-256 is `3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551`; old report SHA-256 is `ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7`.

## B. LR BOUNDARY DEFECT AND REPAIR

The pure fixture reproduced the old order-dependent fingerprint mismatch. CKPT2-R1 applied each intended LR before the inherited pre-collection learner fingerprint and prohibited LR mutation between the pre- and post-collection fingerprints. In the only runtime transaction, tx001 reached the post-collection equality guard without the former `TX1_COLLECTION_MUTATED_LEARNER` failure. This establishes the bounded repair observation for tx001 only; the overall continuation attempt stopped later.

## C. PROCESS-A SEMANTIC SUCCESS GATE REPAIR

The repaired parent did not treat OS return code 0 as semantic success. Although `SimulationApp.close()` again left Process A with return code 0, the durable success receipt, three accepted ledger rows, checkpoint publication, and independent validation conditions were false. The parent wrote `DENY` and did not create Process B. The gate repair therefore behaved as designed.

## D. PRE-RUNTIME QUALIFICATION

- CKPT1 pure qualification: **6/6 PASS**.
- Expected negative matrix: **25/25 PASS**.
- LR boundary fixture: **PASS**.
- Process-B launch-gate matrix: **5/5 PASS**.
- Historical CKPT2, CKPT1 production files, and installed HARL hashes: **PASS / preserved**.
- Frozen R1 harness SHA-256: `c11774e887045bd96aae8cb2241f2bee953bf1eb92a411888a7fc58927abe324`.
- Two pre-runtime corrections were completed and recorded before freeze: inventory-LF digest expectation and direct pure-module import avoiding premature `omni.kit` import.

## E. PROCESS-A TX001-TX003

Process A used PID `29636`, one fresh interpreter, one AppLauncher, one environment, and one persistent learner on `cuda:0`. tx001 completed two physical collection steps and the real learner transaction returned; evidence shows 15 actor optimizer steps, 10 critic optimizer steps, and 10 live ValueNorm updates. The post-transaction R1 ledger hook then raised `KeyError('event_return_computations')`: it indexed a per-transaction count map with the aggregate-summary field name. The failure occurred after learner mutation, before a durable transaction-ledger row was appended. tx002 and tx003 were not started. The route reported `learner_poisoned=false`; the process was discarded.

## F. CHECKPOINT SAVE

No checkpoint save was attempted. There is no checkpoint root, generation directory, manifest, or `latest.json`; published generation count is **0**.

## G. PARENT A→B ADJUDICATION

The parent observed A inactive, read no A success receipt, found zero durable ledger rows and zero checkpoint generations, and independently denied B launch. The downstream gate classification is `PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-SEMANTIC-GATE`.

## H. FRESH PROCESS B

Process B was **not launched**. No Process-B PID exists.

## I. STRICT LOAD

Not reached. Strict checkpoint load count is **0**.

## J. CUDA DEVICE RESTORATION

Not reached because B was not launched.

## K. CROSS-PROCESS STATE EQUALITY

Not established; there was no A checkpoint and no B post-load state.

## L. OPTIMIZER CONTINUITY

Not established across a fresh process. tx001 performed real optimizer mutation only inside Process A.

## M. VALUENORM CONTINUITY

Not established across a fresh process. tx001 performed 10 live ValueNorm updates before the test-side evidence-hook failure.

## N. PROGRESSION / LR CONTINUITY

Not established across a checkpoint boundary. The tx001 LR/fingerprint boundary passed, but no saved progression state was published.

## O. PROCESS-B TX004-TX006

tx004, tx005, and tx006 were **not started**.

## P. PROCESS QUIESCENCE

Process A PID `29636` and parent PID `9356` are inactive. Matching CKPT2-R1 worker count after termination is **0**. Environment close recorded **PASS**. No retry, second A, or B was launched.

## Q. FINAL CHECKPOINT-CONTINUATION VERDICT

**STOP — PHASE-B2-T4-CKPT2-R1-STOP-PROCESS-A-UPDATE.** Real fresh-process optimization checkpoint continuation remains **NOT ESTABLISHED**. The source-backed boundary is the tx001 post-update, pre-ledger test-side evidence hook. Learner mutation occurred, the route was not marked poisoned, no checkpoint generation exists, and B was not launched. No GPT PASS is claimed. R15, evaluation/playback, paper-scale training, and public learned-policy activation remain unauthorized.

## Execution table

| Process | Transaction | LR set before fingerprint | Collection immutable | Update complete | Poisoned | Result |
|---|---:|---:|---:|---:|---:|---|
| A | tx001 | Yes | Yes | Yes, learner transaction returned | No | STOP in post-update ledger hook |
| A | tx002 | Not started | Not started | No | No | NOT STARTED |
| A | tx003 | Not started | Not started | No | No | NOT STARTED |
| B | tx004 | Not started | Not started | No | No | NOT STARTED |
| B | tx005 | Not started | Not started | No | No | NOT STARTED |
| B | tx006 | Not started | Not started | No | No | NOT STARTED |

## A→B gate table

| Condition | Required | Actual | Result |
|---|---|---|---|
| A return code=0 | Yes | Yes | PASS |
| A semantic status PASS | Yes | No success receipt | FAIL |
| A tx count=3 | Yes | 0 durable ledger rows; failure receipt records 1 mutated transaction | FAIL |
| A quiescent | Yes | Not attested by success receipt | FAIL |
| checkpoint save PASS | Yes | No save | FAIL |
| generation=1 | Yes | 0 | FAIL |
| manifest PASS | Yes | Absent | FAIL |
| `latest.json` PASS | Yes | Absent | FAIL |
| validation PASS | Yes | Not possible | FAIL |
| A success receipt durable | Yes | Absent | FAIL |
| A PID inactive | Yes | Yes | PASS |
| B launch allowed | All prior conditions | DENY | PASS — fail closed |

## Continuity table

| State | A pre-save | B post-load | Equal | B after tx004 | Continuity |
|---|---|---|---:|---|---:|
| actor weights | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| actor Adam moments/steps | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| critic weights | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| critic Adam moments/steps | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| ValueNorm | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| progression | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| LR schedule position | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |
| semantic config | Absent | Not reached | N/A | Not reached | NOT ESTABLISHED |

## Evidence index

- `b2_t4_ckpt2_r1_artifacts/process_a/failure_receipt.json`
- `b2_t4_ckpt2_r1_artifacts/process_a_parent_adjudication.json`
- `b2_t4_ckpt2_r1_artifacts/process_b_launch_gate.json`
- `b2_t4_ckpt2_r1_artifacts/parent/parent_process_inventory.json`
- `b2_t4_ckpt2_r1_artifacts/failure_receipt.json`
- `b2_t4_ckpt2_r1_artifacts/ckpt2_r1_pre_runtime_freeze.json`
- `b2_t4_ckpt2_r1_artifacts/pre_runtime_harness_repair_log.json`
