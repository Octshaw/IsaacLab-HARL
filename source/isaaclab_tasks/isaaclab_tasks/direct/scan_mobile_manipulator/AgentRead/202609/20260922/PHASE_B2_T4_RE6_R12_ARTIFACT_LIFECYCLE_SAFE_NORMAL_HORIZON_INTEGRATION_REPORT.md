# Phase B2-T4-RE6-R12 Artifact-Lifecycle-Safe Normal-Horizon Integration Report

Date: 2026-09-22  
Run ID: `b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2`  
Final classification: **PHASE-B2-T4-RE6-R12-STOP-POISONED-RETAINED**

## Executive result

R12 does not qualify. The one authorized formal attempt completed the bounded runtime, PW, NORM-R1, PPQ, and W1-W7 evidence production, but the formal worker stopped at the Layer-A projection boundary with `MISSING-SOURCE:W7.qualified_count`. Learner mutation had already occurred, so `partial_update=true`, `route_poisoned=true`, and the retained learner must never be reused. No retry was performed.

The R12 artifact-lifecycle objective itself passed: the preflight normalization template and canonical trusted live context used separate paths; the canonical path was absent before PID binding and was created exactly once afterward. That bounded result does not override the post-mutation Layer-A failure and is not a training-integration qualification.

## ARTIFACT LIFECYCLE OWNERSHIP

| Artifact | Lifecycle class | Earliest producer boundary | Canonical producer | Preflight path | Canonical path | Early occupation | Result |
|---|---|---|---|---|---|---:|---|
| normalization-context template | PREFLIGHT_TEMPLATE | Stage A | Stage-A template producer | `preflight/templates/r12_normalization_context_template.json` | n/a | 0 | PASS |
| canonical trusted normalization context | LIVE_CANONICAL | NORM_CONTEXT after PID binding | PID-bound live binding/context preparation | template above | `r12_normalization_context.json` | 0 | PASS; created once |
| runtime authority | LIVE_CANONICAL | LIVE_AUTHORITY | reviewed RACQ authority builder | n/a | `runtime_authority/b2_t4_re6_r12.json` | 0 | PASS |
| run binding | LIVE_CANONICAL | PID_BINDING | reviewed RACQ binding builder | n/a | `run_binding/b2_t4_re6_r12/<run-id>.json` | 0 | PASS |
| transaction ledger | RUNTIME_CANONICAL | RELEASED_RUNTIME | released runtime | n/a | `<run-id>/transaction_ledger.jsonl` | 0 | PASS |
| PW transaction reconciliation | RUNTIME_CANONICAL | RELEASED_RUNTIME | reviewed PW runtime producer | n/a | `<run-id>/pw_transaction_reconciliation.jsonl` | 0 | PASS |
| normalized runtime result | POST_RUNTIME_CANONICAL | NORMALIZED_RUNTIME | NORM-R1 consumer | n/a | `<run-id>/runtime_normalization_result.json` | 0 | PASS |
| PPQ success receipt and W1-W7 | POST_RUNTIME_CANONICAL | PPQ | PPQ publication route | n/a | `<run-id>/candidate_success_receipt_v2_1.json`, W1-W7 | 0 | PASS |
| Layer-A receipt | POST_RUNTIME_CANONICAL | LAYER_A | formal worker Layer-A producer | n/a | `<run-id>/layer_a_v3_worker_receipt.json` | 0 | **NOT CREATED / STOP** |

The 25-artifact ownership matrix passed with 0 ownership ambiguities and 0 duplicate producers. The 10-boundary collision matrix passed with 0 early occupations, duplicate producers, illegal overwrites, illegal appends, or consumer-to-producer violations.

## Primary lifecycle table

| Boundary | Template allowed | Live canonical allowed | Runtime canonical allowed | Post-runtime canonical allowed |
|---|---|---|---|---|
| Stage A | yes | no | no | no |
| Live authority / pre-PID | preflight only | authority-specific only | no | no |
| PID binding complete | no new template | PID-bound live yes | no | no |
| Worker released | no | read/verify live | runtime producer yes | no |
| Runtime complete | no | read-only | read-only | post-runtime producer yes |

## R11 reproduction and R12 repair

The isolated Stage-A fixture reproduced the R11 `FileExistsError`: the PID-independent template and PID-bound producer attempted to occupy the same root canonical path. Repair `R12-A-001` moved the template to `preflight/templates/r12_normalization_context_template.json` and reserved `r12_normalization_context.json` for PID-bound live preparation. The complete downstream Stage-A suite was rerun; unresolved Stage-A repairs were 0.

The final pre-process audit confirmed that the template existed while the canonical path did not. After worker PID 29544 and the run binding existed, the live ownership check recorded `prior_existence=false`, `create_count=1`, exact authority/binding/run identity, and `template_live_alias=false`.

## Freeze and live setup

- Official Stage A: PASS.
- Frozen harness SHA-256: `c53cc67edff2e3a8cdb6a3edb3a9ec6a60fe8b7b92eb7becfe89d42925d20286`.
- Source edits after freeze: 0.
- Final pre-process path audit: PASS.
- Live authority / supervisor / worker / PID binding / release: 1 / 1 / 1 / 1 / 1.
- Retry count: 0.
- CUDA/CUBLAS probe: 1/1 PASS on `cuda:0`, no retry.
- Live positive smoke and worker release gate: PASS.

## Primary process table

| Stage | Supervisor | Worker | PID binding | Release | CUDA | Source repair |
|---|---:|---:|---:|---:|---:|---|
| Pure Stage A | 0 | 0 | 0 | 0 | 0 | one test-side repair, resolved before freeze |
| Live pre-PID | 0 | 0 | 0 | 0 | 0 | no |
| Blocked PID-bound | 1 | 1 | 1 | 0 | 0 | no |
| Released runtime | 1 | 1 | 1 | 1 | 1 | no |

## Runtime and evidence results

| Slice | Result | Evidence boundary |
|---|---|---|
| Runtime | bounded execution completed | 320 physical transitions; 160 transactions; 160 production S10; 160 ledger rows; 159 bridges |
| PW | PASS | 6,560 critic and 640 actor-factor records; 0 missing/duplicate/order/digest/temp faults |
| NORM-R1 | PASS | raw/normalized crosscheck passed |
| PPQ | PASS | 90-field candidate receipt passed and durable readback passed |
| W1 | PASS | cross-update ownership witness |
| W2E | PASS | 12 valid of 29 candidates; selected completion/reopen witness passed |
| W3 | PASS | real zero-DVM actor witness |
| W4 | PASS | real nonterminal bootstrap witness |
| W5 | PASS | two normal-horizon terminal autoresets at transaction 150 |
| W6 | PASS | fresh post-autoreset transaction 151 |
| W7 | PASS as canonical witness | `qualified_count=160`, `required=160` |
| Layer-A | **STOP / NOT STARTED** | projection input was missing `W7.qualified_count`; canonical W7 artifact itself contained the field |
| Layer-B | NOT STARTED | blocked by Layer-A STOP |
| Environment close | PASS | `env_close_result.json` |
| SimulationApp close intent | FAIL/false | worker failure receipt records `app_close_invoked=false` |
| Process quiescence | PASS | worker PID inactive; 0 matching R12 processes after exit |

## Exact failure boundary

The worker produced `candidate_success_receipt_v2_1.json` with `W7_qualified_count=160` and published `W7_runtime_p2_immutability.json` with `qualified_count=160`. While projecting the future Layer-A worker receipt, `_assignment_phase_b2_t4_laq_worker_receipt.py:202` required `witnesses["W7"]["qualified_count"]`; the source map supplied to that projection lacked the key, producing `LayerAStop: MISSING-SOURCE:W7.qualified_count`.

The worker durably recorded:

- `failure_stage=layer_a_v3`;
- `layer_a_status=NOT_STARTED`;
- `partial_update=true`;
- `route_poisoned=true`;
- `tx161_started=false`;
- `env_close_pass=true`.

The supervisor then encountered `FileNotFoundError` while its final 86-gate path attempted to read the absent `layer_a_v3_predicate_adjudication.json`. Post-run adjudication therefore records `success_gate_86=NOT_EVALUATED`, not 86/86 PASS. The harness-native `formal_supervisor_result.json` was not produced and remains absent because only the formal supervisor owns that canonical path. `post_run_supervisor_exception_adjudication.json`, `success_gate_86.json`, and `final_result.json` explicitly identify their post-run STOP provenance rather than claiming to be success receipts.

## Repository and preservation

- Historical R9: POISONED / RETAINED / NEVER REUSE.
- Historical R10: PRE-RELEASE STOP / RETAINED.
- Historical R11: PRE-RELEASE STOP / RETAINED.
- Frozen R9/R10/R11 harnesses and evidence were not modified or rerun.
- Production, lifecycle, resolver, controller, learner, NORM-R1, PPQ, LAQ, RACQ/RACQ-R1, installed HARL, and installed package sources were not modified.
- Existing staged set remained exactly 359 entries with no staged-entry change.
- This task issued no `git add`, `git commit`, or `git push`.

## Retained nonclaims and GPT-review handoff

This attempt does not establish R12 qualification, Layer-A PASS, Layer-B PASS, checkpoint continuation, long/paper-scale training readiness, evaluation/playback readiness, public-route activation, or reusable learner state. The successful bounded runtime sub-slices and artifact-lifecycle repair remain evidence only for their named boundaries.

Do not retry R12, do not reuse worker PID 29544 or this run's learner/binding, do not edit the frozen R12 harness under this authorization, and do not begin R13. Any next attempt requires fresh explicit GPT authorization and a new run identity after design review of the Layer-A projection source mapping.
