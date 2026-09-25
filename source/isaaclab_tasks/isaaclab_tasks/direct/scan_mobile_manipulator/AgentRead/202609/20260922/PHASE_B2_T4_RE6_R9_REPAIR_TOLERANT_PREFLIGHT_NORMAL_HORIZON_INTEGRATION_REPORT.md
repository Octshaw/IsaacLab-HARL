# Phase B2-T4-RE6-R9 Repair-Tolerant Preflight Normal-Horizon Integration Report

Date: 2026-09-22

Classification: `PHASE-B2-T4-RE6-R9-STOP-POISONED-RETAINED`

Status: **STOP / POST-RELEASE RUNTIME FAILURE / POISONED / NO RETRY**

R9 completed its repair-tolerant pre-runtime preparation and released exactly one formal worker. The underlying runtime produced the complete 160-transaction evidence set and NORM-R1 normalized it successfully. The R9 worker then stopped in `runtime_normalization` when it attempted an exclusive second creation of an already existing `pw_transaction_reconciliation.jsonl`. Because learner mutation had already occurred, the retained route is poisoned and the learner must never be reused. This report does not promote the underlying runner's local success label to an R9 qualification.

## PRE-RUNTIME REPAIRS

| Repair ID | Initial failure | Classification | Changed file | Semantic impact | Revalidation | Result |
|---|---|---|---|---|---|---|
| R9-PRE-001 | `KeyError: s7_ledger_unchanged` | `MINOR_PRE_RUNTIME_REPAIR` | `scripts/environments/test_assignment_phase_b2_t4_re6_r9_repair_tolerant_normal_horizon_integration.py` | NONE | R8 blocker reproduction; complete LAQ source-shape projection; 43/90 structural composition | RESOLVED |
| R9-PRE-002 | `PPQV2R1Stop:PHASE-AUTHORITY-FILENAME` | `MINOR_PRE_RUNTIME_REPAIR` | same R9 harness | NONE | deterministic authority filename; synthetic PPQ; downstream pre-authority chain | RESOLVED |
| R9-PRE-003 | `LayerAStop:MISSING-SOURCE:raw.counts.valid_nonzero_update` | `MINOR_PRE_RUNTIME_REPAIR` | same R9 harness | NONE | complete LAQ projection; all downstream pre-authority gates | RESOLVED |
| R9-PRE-004 | `REPOSITORY-STARTING-PORCELAIN` with one unfiltered R9 harness path | `MINOR_PRE_RUNTIME_REPAIR` | same R9 harness | NONE | repository authority; complete static preflight; downstream gates | RESOLVED |

All four repairs were test-side, contract-preserving, production-neutral, learner-neutral, completed before final freeze, and recorded in `pre_runtime_repair_log.json`. Unresolved repairs: **0**. Pre-runtime major findings: **0**. The failed pre-authority/static iterations did not create or consume a live R9 authority; the temporary empty run namespace from the failed static iteration was removed before the formal authority was created.

## Source-shape required-field table

The reviewed projection path was `LAQ.project_layer_a_worker_receipt`. The complete machine-readable inventory is `layer_a_synthetic_source_shape_contract.json`; it contains **179/179 required projection entries**. The table below accounts for every entry by collection.

| Source collection | Required entries | Required content | Real producer |
|---|---:|---|---|
| `normalized` | 19 | container, normalized learner fields, derived task completion and coverage | NORM-R1 normalized/derived evidence |
| `normalizer_sha256` | 1 | reviewed normalizer identity | R9 source builder / reviewed normalizer |
| `ppq_v2_candidate` | 91 | candidate container plus all 90 PPQ-V2-R1 fields | reviewed PPQ-V2-R1 builder |
| `ppq_v2_candidate_file_sha256` | 1 | durable PPQ candidate digest | PPQ durable publication |
| `ppq_v2_readback` | 2 | readback container and `pass` | PPQ durable readback |
| `pw_verifier` | 9 | container plus critic, actor-factor and fault counts | reviewed PW verifier |
| `raw_final` | 18 | runtime counters, persistent identity, quiescence and transaction fields | runtime final result and transaction evidence |
| `terminal_rows` | 3 | container, `pass`, `s7_ledger_unchanged` | terminal reconciliation ledger |
| `transaction_rows` | 3 | container, `s7_s8_s9_s10`, `finite` | transaction ledger |
| `witnesses` | 16 | container, W1-W7 objects/pass fields and W7 count | canonical witness producers |
| `worker_handoff` | 14 | container plus status, identities, CUDA/launcher/close and receipt fields | formal worker handoff |
| `zero_dvm_rows` | 2 | container and `pass` | zero-DVM actor ledger |
| **Total** | **179** | complete reviewed projection source shape | — |

Terminal-row detail:

| Collection | Field | Type/shape | Synthetic producer | Required |
|---|---|---|---|---|
| `terminal_rows` | `terminal_rows.0.pass` | bool | `_r9_preauthority_fixture` | yes |
| `terminal_rows` | `terminal_rows.0.s7_ledger_unchanged` | bool | `_r9_preauthority_fixture` | yes |

The reviewed projection has no separately applicable nonterminal-row required-field set.

## Source-shape parity and negative controls

| Gate | Expected | Actual | Result |
|---|---:|---:|---|
| Required fields present | 179 | 179 | PASS |
| Required minus synthetic | 0 | 0 | PASS |
| Unexpected authority-bearing fields | 0 | 0 | PASS |
| Per-field removal STOPs | 179 | 179 | PASS |
| Per-field unexpected PASS | 0 | 0 | PASS |
| Representative type/shape STOPs | 5 | 5 | PASS |
| Representative unexpected PASS | 0 | 0 | PASS |
| R8 blocker reproduced | yes | yes | PASS |
| Repaired LAQ projection | PASS | PASS | PASS |
| Synthetic Layer-A composition | 43 top-level / 90 nested PPQ | 43 / 90 | PASS |

## Live authority, binding, registry and identity

| Item | Count | Digest / identity | Result |
|---|---:|---|---|
| Live R9 runtime authority | 1 | `afe2c088c7ff51769c4a66e526600c082ca44b2285479989aa89c14f8e7b563a` | PASS |
| Canonical `LIVE_FORMAL_RUNTIME` validation context | 1 | `b2_t4_layer_a_validation_context_v1` | PASS |
| Live R9 run binding | 1 | `3db313a0bf6194e1adc0e90ae65584ac8a6b1d9e3994f119b51ce32c38799519` | PASS |
| R9 registry instance | 1 | `457979a446b9855029657db404842917806840573fd650e08764c69250a26322` | PASS |
| Trusted NORM-R1 context | 1 | `fdf0d4602d1d0346f7136eed5e8172732383fe5407bb305b0bc4353e89bf6b3f` | PASS |
| Reviewed identities | 20 | 20 current hashes equal frozen expectations | PASS |
| Reviewed-contract / production modifications | 0 / 0 | none | PASS |

Run ID: `b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1`.

Final frozen harness SHA-256: `117196c23c44404ae9a6f6632ceb9240bfe872c1d705fc0d53093a4588721a1a`; current readback matches. Source edits after freeze: **0**.

## Pre-runtime readiness

| Gate | Result |
|---|---|
| Pre-authority readiness | PASS |
| NORM-R1 positive | PASS |
| NORM-R1 expected-negative / unexpected-pass | 6/6 / 0 |
| RACQ-R1 mode positive | PASS |
| RACQ-R1 mode expected-negative / unexpected-pass | 4/4 / 0 |
| Complete synthetic chain inherited / RACQ predicates | 39/39 / 9/9 PASS |
| Complete synthetic-chain negative controls | 8/8 STOP; 0 unexpected PASS |
| Coupling regression | PASS |
| Static preflight | PASS |
| Final static readiness | PASS |
| Harness freeze before release | PASS |
| Worker release | exactly 1 |

Static preflight observed CUDA/AppLauncher/environment/learner counts of 0/0/0/0 and created exactly one live authority. Its inherited preflight launched 14 child Python checks. No live worker had been released at final static-readiness publication.

## Normalization table

| Property | Expected | Actual | Result |
|---|---|---|---|
| Normalizer | NORM-R1 | NORM-R1 | PASS |
| Raw source phase | B2-T4-RE6-R9 | B2-T4-RE6-R9 | PASS |
| Run ID / namespace | exact live R9 binding | exact | PASS |
| Historical R3 fresh-runtime normalizer calls | 0 | 0 | PASS |
| Runtime normalization | PASS | PASS | PASS |
| Raw/normalized crosscheck | PASS | PASS | PASS |
| Raw-source rows: transactions / physical / bridges | 160 / 320 / 159 | 160 / 320 / 159 | PASS |
| W1-W7 in normalized evidence | all PASS | all PASS | PASS inside normalized evidence only |
| Durable PPQ-V2-R1 success receipt | required for R9 success | not produced | NOT STARTED / STOP |

Normalization completed and its artifacts are retained. R9 stopped after normalization and before the PPQ success-receipt stage.

## Runtime table

| Gate | Target | Retained runtime evidence | R9 adjudication |
|---|---:|---:|---|
| CUDA/CUBLAS probe | 1 | 1 PASS, 0 retries | PASS |
| AppLauncher lifetime | 1 | 1 | runtime occurred |
| Environment construction / initial reset | 1 / 1 | 1 / 1 | runtime occurred |
| Persistent learner construction | 1 | 1 | mutation-bearing learner; **never reuse** |
| Physical transitions | 320 | 320 | normalized evidence PASS |
| Transactions / S10 / transaction ledger | 160 / 160 / 160 | 160 / 160 / 160 | normalized evidence PASS |
| Bridges | 159 | 159 | normalized evidence PASS |
| PW critic / actor-factor | 6560 / 640 | 6560 / 640, all fault counts 0 | normalized evidence PASS |
| W7 qualified | 160 | 160 | normalized evidence PASS |
| Event returns / stock returns | 160 / 0 | 160 / 0 | normalized evidence PASS |
| tx161 | not started | false | PASS |
| Checkpoint / public / evaluation | 0 / 0 / 0 | 0 / 0 / 0 | PASS |
| Formal PPQ / Layer-A publication | required | absent / absent | STOP |

The raw runtime runner emitted its inherited local `passed` classification, but R9 is a larger authority/normalization/PPQ/Layer-A/supervisor chain. The later R9 worker failure is authoritative for the phase result.

## W2 witness table

| Property | Actual | Result |
|---|---|---|
| Candidate / valid count | 29 / 12 | PASS |
| Selected identity | env 1, robot 1, task 10, generation 0 | PASS |
| Claim | tx12, physical step 23 | PASS |
| Continuity bridges | tx12, tx13, tx14 | PASS |
| Completion | tx15, physical step 30 | PASS |
| Ownership clear | true | PASS |
| Decision reopen | tx16, physical step 31 | PASS |
| Layers A/B/C/D/E | true/true/true/true/true | PASS |

## Post-release failure

| Property | Evidence |
|---|---|
| Failure stage | `runtime_normalization` |
| Exception | `FileExistsError: [Errno 17] File exists` |
| Exact target | `.../<run-id>/pw_transaction_reconciliation.jsonl` |
| Root condition | the inherited runtime had already durably created the PW transaction reconciliation ledger; the wrapper then used `Path.open("xb")` to create the same path again |
| Worker state at failure | current tx 160; irreversible learner mutation observed |
| Worker receipt | valid envelope and identity; `status=failure` |
| Normalizer | PASS |
| PPQ / Layer-A | NOT_STARTED / NOT_STARTED |
| Partial update / poisoned | true / true |
| Retry | 0; forbidden after release |
| tx161 | false |

This is a post-release orchestration/harness failure. It was not eligible for the pre-runtime minor-repair loop. The frozen harness was not edited and no second authority, supervisor, worker, or release was created.

## Layer-A table

| Gate | Expected | Actual | Result |
|---|---:|---:|---|
| Synthetic pre-runtime shape | 43 / 90 | 43 / 90 | PASS (readiness only) |
| Runtime NORM-R1 | PASS | PASS | PASS |
| Runtime PPQ-V2-R1 receipt | PASS | not produced | STOP |
| Runtime Layer-A receipt | 43 / 90 | not produced | STOP |
| Worker receipt envelope / identity | PASS / PASS | PASS / PASS | PASS |
| Worker success | true | false | STOP |
| Environment close | true | true in final worker receipt | PASS |
| App-close handoff attestation | true | false | STOP |
| Counts / route health | valid / healthy | incomplete receipt / poisoned | STOP |
| Reviewed Layer-A validation | PASS | `RECEIPT-FIELDS-MISSING-OR-UNKNOWN` | STOP |

The early `failure_receipt.json` records the pre-finally close state; the later formal worker receipt records `env_close_attempted=true` and `env_close_pass=true`. It does not attest `app_close_invoked=true`, so no Layer-A close-handoff claim is made.

## Layer-B result

Layer B: **PASS**.

| Hard predicate | Actual |
|---|---|
| Supervisor wait completed | true |
| Timed out | false |
| Process return code | 0 |
| Worker PID 12068 absent | true |
| Matching formal-worker PID set empty | true |
| Authoritative shutdown marker | absent / not claimed |

External process quiescence passed. Layer B does not override the Layer-A failure or poisoned-route rule.

## Exact execution counts

| Item | Actual |
|---|---:|
| Top-level Python invocations | 12 |
| Interpreter verification / `py_compile` / self-check | 1 / 4 / 1 |
| Pre-authority checks | 3 total: 2 repaired STOP, 1 PASS |
| Static preflight invocations | 2 total: 1 repaired STOP, 1 PASS |
| Formal supervisor invocations | 1 |
| Inherited static-preflight child Python invocations | 14 |
| Live authorities / Layer-A contexts / run bindings / registries / trusted NORM contexts | 1 / 1 / 1 / 1 / 1 |
| Supervisors / workers started / workers released / retries | 1 / 1 / 1 / 0 |
| CUDA probes / retries | 1 / 0 |
| AppLauncher / environments / resets / persistent learners | 1 / 1 / 1 / 1 |
| Physical / transactions / S10 / ledger / bridges | 320 / 160 / 160 / 160 / 159 |
| PW critic / PW actor-factor / PW faults | 6560 / 640 / 0 |
| Actor backward / actor step | 165 / 165 |
| Critic backward / critic step / ValueNorm.update | 1600 / 1600 / 1600 |
| Valid nonzero / valid zero-effective critic updates | 1576 / 24 |
| W2 candidates / valid | 29 / 12 |
| `TASK_COMPLETED` / completion delta / max coverage | 22 / 22 / 11 |
| Terminal-autoreset / post-autoreset learned transaction | 2 / true |
| Event returns / stock returns | 160 / 0 |
| Runtime NORM / PPQ success receipts / Layer-A receipts | 1 PASS / 0 / 0 |
| Checkpoint / public / evaluation | 0 / 0 / 0 |
| tx161 | NOT STARTED |
| Git add / commit / push | 0 / 0 / 0 |

## Repository preservation

- Branch / HEAD / origin-main / merge-base: `main` / `b71d85a32f51be6ada324f870813a56bb45dd396` / same / same.
- Starting full porcelain: 25,628 lines, SHA-256 `bacbb0e696f574e68b8e319d7a6b1905ce7b088e1fcc323be1785c2e6c9771d0`.
- Staged paths remain 359.
- Staged-index SHA-256 remains `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
- Monthly staged path-set SHA-256 remains `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.
- No staging, commit, or push was performed.

## Retained nonclaims

- R9 is **not qualified** and is not `COMPLETE / AWAITING GPT REVIEW`.
- The poisoned learner and route must never be reused.
- Runtime PPQ-V2-R1, runtime Layer-A-v3, and final supervisor success are **not established**.
- A passing normalized runtime slice does not establish checkpoint continuation, public learned-policy readiness, evaluation readiness, long/paper-scale training quality, or general performance.
- Checkpoint continuation remains **NOT ESTABLISHED**.
- Long/paper-scale training remains **NOT AUTHORIZED**.
- Public route remains **DORMANT / BLOCKED**.
- No R9 retry, tx161, R10, checkpoint operation, evaluation/playback, public activation, stage, commit, or push is authorized by this result.

## GPT-review handoff

Historical R8 remains `GPT REVIEW STOP CONFIRMED / HISTORICAL`. R9 repaired four minor pre-runtime defects, left zero unresolved pre-runtime repairs and zero pre-runtime major findings, passed final static readiness, then incurred a post-release runtime failure after mutation. The final authoritative classification is:

`PHASE-B2-T4-RE6-R9-STOP-POISONED-RETAINED`

Independent GPT review should evaluate the retained evidence and the exclusive-create collision before authorizing any new phase. Do not repair or retry R9 in place, do not launch R10, do not start tx161, do not reuse the learner, and do not commit.
