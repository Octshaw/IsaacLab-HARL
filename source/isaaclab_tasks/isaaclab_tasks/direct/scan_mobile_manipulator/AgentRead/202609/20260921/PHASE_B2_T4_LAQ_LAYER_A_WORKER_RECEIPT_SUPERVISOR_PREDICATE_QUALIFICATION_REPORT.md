# Phase B2-T4-LAQ — Layer-A worker-receipt/supervisor predicate qualification

Date: 2026-09-21. **Final classification: `PHASE-B2-T4-LAQ-STOP-RAW-RECEIPT-CROSSCHECK-INCOMPLETE`.** This was a pure/offline attempt. The one frozen hypothetical positive dry run and original-R3 negative control initially gave the expected answers, but a subsequent independent 39-predicate corruption audit found that a valid-looking, wrong `filesystem_precondition_digest` is accepted by the supervisor. The earlier LAQ PASS-looking [result is preserved](b2_t4_laq_artifacts/final_result_before_post_final_audit.json) and superseded by the [independent audit](b2_t4_laq_artifacts/post_final_predicate_negative_audit.json) and corrected [final result](b2_t4_laq_artifacts/final_result.json). Do not interpret this as a qualified Layer-A path or as RE6-R4 authority.

## A. Repository authority

Branch `main`; HEAD, `origin/main`, and merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. Before the first LAQ write, full porcelain had 25,222 rows, SHA-256 `3ba9d6e4137139287cbb6e9aa1072c89559e85df63428f69280215d033b2601c`. The staged migration remained 359 paths with staged-index SHA `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. The [repository record](b2_t4_laq_artifacts/repository_authority.json) also retains the full porcelain at qualification time. Git add/commit/push/reset/checkout/clean: none.

## B. Reviewed starting authority

The user supplies PPQ-V2, PPQ-v1, W2E/W2I/PW/EP-Q and prior B2 gates as GPT REVIEW PASS / CLOSED in their bounded scopes. RE5 and RE6-R1 are poisoned historical STOPs; RE6 and RE6-R2 are pre-runtime STOPs. RE6-R3 is **GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED**, reviewed classification `PHASE-B2-T4-RE6-R3-INCOMPLETE-LAYER-A-WORKER-RECEIPT-AFTER-MUTATION-REVIEW-STOP`. [Authority record](b2_t4_laq_artifacts/reviewed_starting_authority.json).

## C. Historical R3 preservation

No R3 worker receipt, supervisor result, final result, post-supervisor audit, failure receipt, learner or artifact was edited or reused. A full path/size/content SHA tree digest of R3, R1 and R2, plus protected file hashes, matched [before](b2_t4_laq_artifacts/protected_source_identity_before.json) and [after](b2_t4_laq_artifacts/protected_source_identity_after.json) qualification/final controls. R3's original supervisor PASS remains a preserved historical artifact, not a valid phase PASS.

## D. Exact R3 qualification defect

R3's custom supervisor checked a reduced Layer A and passed a worker receipt with defaults. The later independent R3 audit supersedes it. This LAQ investigation does not retroactively repair the R3 receipt.

| Predicate | Raw R3 | Original R3 receipt | Original supervisor | Finding |
|---|---:|---:|---|---|
| environment constructions | 1 | 0 | omitted | defaulted |
| initial reset | 1 | 0 | omitted | defaulted |
| persistent learner | 1 | 0 | omitted | defaulted |
| event returns | 160 | 0 | omitted | defaulted |
| TASK_COMPLETED | 22 | 0 | omitted | defaulted |
| learner map | populated | `{}` | omitted | omitted |
| contract map | populated authority available | `{}` | omitted | omitted |
| final in-worker quiescence | raw read-only check true | false | omitted | defaulted |

## E. Complete historical Layer-A inventory

The RE5 `_layer_a_validate` source AST yields **39** named success predicates. All are individually listed with source line, purpose, receipt fields, R3 population/check status and V2 mapping in the [inventory](b2_t4_laq_artifacts/complete_layer_a_predicate_inventory.json). Classification: 12 preserved, 11 omitted, 14 defaulted, 2 reduced. This is the complete inherited *named check* inventory, not an assertion that the new implementation is qualified.

## F. Omitted/defaulted predicate analysis

The omitted/defaulted cluster includes environment/reset/learner counts, task progress, full learner and contract maps, event returns, and worker quiescence. R3's shallow canonical-witness check did not replace detailed W1–W7 and W7-count gates. [Original receipt negative](b2_t4_laq_artifacts/historical_r3_original_receipt_negative.json) records the raw mismatches and STOP.

## G. Superseded predicate analysis

PPQ-V2's reviewed validator is reused for its exact flat receipt, while additional V2 fields retain RE5 worker/process gates. Every RE5 named predicate is mapped; none was declared obsolete without proof. The mapping artifact reports zero *unmapped names*, but the post-final audit proves the resulting end-to-end crosscheck is incomplete. Mapping is not sufficient qualification.

## H. Layer-A receipt V2 contract

The pure [helper](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_laq_worker_receipt.py) defines `b2_t4_layer_a_worker_receipt_v2` and a digest-bound envelope. The [contract](b2_t4_laq_artifacts/layer_a_receipt_contract_v2.json) and [schema](b2_t4_laq_artifacts/layer_a_receipt_schema_v2.json) require 120 direct fields: the full reviewed PPQ-V2 flat set plus worker-local construction, learner/contracts, quiescence, close and persistence facts. Missing/null fields fail closed. This is a **failed candidate** because of the digest-binding gap in Y/AF.

## I. Process/runtime fields

Run ID/PID and CUDA/AppLauncher/environment/reset/learner counts are direct. The corrected hypothetical R3 projection reads 1/1/1/1/1 from raw counters and worker-local probe evidence, not R3's zero templates. The validator requires one of each for the current formal config.

## J. Campaign fields

The intended config is T=2 and 160 transactions: physical 320, S10/ledger 160/160, bridges 159, tx161 false. Projection reads raw exact counters and append-only ledgers. The 57-case matrix corrupts each count separately.

## K. Learner fields

The populated learner map binds actor planned/observed backward/step, critic planned/observed backward/step, valid critic classes, invalid class 0, ValueNorm expected/actual, Adam/ValueNorm continuity and numerical health. The raw R3 values are actor 165/165, critic 1600/1600, classes 1576+24, ValueNorm 1600. Factor and persistent learner continuity are separate inherited gates.

## L. Return fields

The receipt directly includes event returns 160 and stock `compute_returns` 0. The latter is a legitimate source-backed zero, not permission to fill an absent source with zero.

## M. Task/terminal fields

Task-completed events and normalized completion delta are 22, maximum coverage 11, terminal/autoreset 2, post-reset learned transaction true. Future values are evidence-derived, not R3 constants in the helper.

## N. Reviewed-contract map

The nonempty map binds W2E/W2I/PW/PPQ-V2, normalizer, LAQ version, production/config identities, and explicit NR/ZD/SR/bookkeeping/policy fault counts. Empty maps STOP. The accepted wrong filesystem digest shows another authority binding is still missing; the contract map's existence cannot rescue it.

## O. Witness map

W1, W2E, W3–W7 are separately sourced from canonical artifacts and crosschecked to PPQ statuses; W7 count must equal transactions. The historical R3 witness map was only shallow pass flags.

## P. PW map

Reviewed PW verification supplies 6560 critic and 640 actor/factor records and zero missing/duplicate/order/digest/temp/old-path faults. These are evidence-persistence facts, not training quality.

## Q. Route-health fields

Candidate success needs `campaign_status=SUCCESS`, `partial_update=false`, `route_poisoned=false`. R3's post-review historical attempt remains logically poisoned (`true/true`) even though its preserved pre-audit worker candidate reported `false/false`.

## R. Worker quiescence semantics

`final_in_worker_quiescence_pass` is the raw engine's in-worker read-only learner/route state check before shutdown, **not** EP-Q's external process Layer B. The corrected hypothetical projection takes its true value from raw final; the original R3 worker receipt left it false. It must be independently and finally bound in a future fresh worker.

## S. Close-handoff semantics

The worker receipt binds `env_close_pass`, `app_close_invoked`, and receipt pre-App-close fsync/readback/order flags. This does not claim `SimulationApp.close()` returned normally or every Kit callback completed. EP-Q Layer B separately checks the exited process.

## T. Forbidden actions

Checkpoint I/O, public activation and evaluation/playback counts must each be source-backed zero. This LAQ phase executed none.

## U. Template-default policy

Absent, null and wrong-type required fields fail closed; 38 tested default/absent-source cases STOPped. Legitimate zero for stock returns or checkpoint I/O is accepted only with explicit source. This suite did not include a wrong-but-well-formed filesystem digest, which the post-final audit exposed.

## V. Raw-to-receipt projection architecture

The helper copies the complete PPQ-V2 candidate only after checking its field set, then adds worker/process data from explicit raw final, normalized learner, ledgers, PW verifier, canonical witnesses and worker close handoff. No supervisor field repair or historical R3 outcome constant is used. [Projection](b2_t4_laq_artifacts/corrected_r3_projection_positive.json) is hypothetical only.

## W. Receipt source map

All 120 fields have a [source-map entry](b2_t4_laq_artifacts/layer_a_receipt_source_map.json). However, the map described `filesystem_precondition_digest` as worker-local identity without enforcing equality against the actual precondition artifact. Thus source-map presence is not source binding.

## X. Complete supervisor validator

The candidate validator checks the digest-bound envelope, 120 field presence/types, full reviewed PPQ-V2 validator, inherited RE5 worker/process gates, learner/contracts/witness/PW maps, route flags, close and forbidden actions. Its implementation had 167 checks on the frozen positive. **It is not complete for this task** because a valid-looking wrong filesystem digest survives.

## Y. Raw-vs-receipt crosscheck

The frozen positive compared 96 raw/receipt relations including environment/reset/learner, S10/ledger/bridges, learner/returns/task/terminal/W2/PW/route flags. [Crosscheck](b2_t4_laq_artifacts/raw_receipt_crosscheck.json) passed for uncorrupted R3 evidence, but did **not** compare `filesystem_precondition_digest` with raw artifact bytes. The [exact gap witness](b2_t4_laq_artifacts/raw_receipt_crosscheck_gap.json) changes the source-matching SHA to 64 zero hex characters; validator, raw crosscheck and supervisor all still PASS. This is the decisive STOP.

## Z. Original R3 receipt negative

The immutable original R3 envelope fails the new V2 schema and raw crosscheck, including the known 0/0/0, returns 0, task 0, empty maps and false quiescence. [Negative](b2_t4_laq_artifacts/historical_r3_original_receipt_negative.json). Historical R3 remains STOP.

## AA. Corrected R3 projection positive

The hypothetical corrected projection passed the implemented predicates on unchanged raw R3 evidence. This is a bounded positive for the observed values, not proof that all wrong values are rejected. [Evidence](b2_t4_laq_artifacts/corrected_r3_projection_positive.json).

## AB. Supervisor positive replay

The frozen candidate supervisor reported Layer A PASS, raw crosscheck PASS and Layer B PASS on the corrected hypothetical projection. The post-final wrong-digest counterexample supersedes any overall-qualification inference from that replay. [Replay](b2_t4_laq_artifacts/supervisor_replay_positive.json).

## AC. Original R3 supervisor negative replay

Original R3 receipt + preserved EP-Q Layer B PASS yields Layer A FAIL and overall STOP. Layer B cannot rescue Layer A. [Replay](b2_t4_laq_artifacts/supervisor_replay_original_r3_negative.json).

## AD. Field-by-field negative matrix

The requested A–BE [matrix](b2_t4_laq_artifacts/field_negative_matrix.json) yielded 57/57 STOP, unexpected PASS 0 **within that enumerated matrix**. Case BD changed an individually PPQ-valid W2 candidate count: local validator stayed PASS, but raw crosscheck STOPped it. The missed filesystem-digest mutation was outside this matrix.

| Group | Cases | Expected STOP | Actual STOP | Unexpected PASS |
|---|---:|---:|---:|---:|
| runtime construction A–E | 5 | 5 | 5 | 0 |
| campaign F–J | 5 | 5 | 5 | 0 |
| learner K–T | 10 | 10 | 10 | 0 |
| returns/task U–Z | 6 | 6 | 6 | 0 |
| contracts/terminal AA–AE | 5 | 5 | 5 | 0 |
| witnesses AF–AM | 8 | 8 | 8 | 0 |
| PW AN–AP | 3 | 3 | 3 | 0 |
| route/close AQ–AY | 9 | 9 | 9 | 0 |
| schema/raw AZ–BE | 6 | 6 | 6 | 0 |

## AE. Default-value matrix

The [matrix](b2_t4_laq_artifacts/template_default_fail_closed_matrix.json) tested `0`, `false`, `{}`, `[]`, `None`, and missing against six mandatory fields, plus two missing-source/legitimate-zero cases: 38/38 STOP. It is a bounded sentinel test, not complete identity-mismatch coverage.

## AF. Gate-equivalence audit

The [initial table](b2_t4_laq_artifacts/layer_a_gate_equivalence.json) mapped all 39 RE5 check names and reported no unexplained *name* omissions. Some entries used a generic missing-version negative rather than a predicate-specific negative, so it was inadequate proof of full equivalence. The subsequent [39-predicate audit](b2_t4_laq_artifacts/post_final_predicate_negative_audit.json) gives 38 validator STOP and **one unexpected validator/supervisor PASS**: wrong `filesystem_precondition_digest`. Gate equivalence for the required raw-to-receipt chain is **NOT ESTABLISHED**.

| Historical predicate | V2 check | Initial classification | Predicate-specific audit |
|---|---|---|---|
| envelope, schema, digest, phase, run/PID | envelope + complete PPQ-V2 | identical/stronger | STOP on corruption |
| source/config/PW identities | identity predicates | stronger | STOP on corruption |
| filesystem authority | 64-hex syntax only | claimed stronger | **wrong 64-hex digest PASS** |
| runtime/campaign/learner/returns | direct + PPQ/learner maps | stronger | STOP on corruption |
| contracts/witness/PW/route/close | direct maps and handoff | stronger | STOP on corruption |

## AG. Supervisor predicate coverage

All 120 mandatory fields had a missing-field STOP in the [presence coverage](b2_t4_laq_artifacts/supervisor_predicate_coverage.json): 120/120. This is **field-presence coverage**, not semantic mutation coverage. The latter failed 38/39 in the supplemental audit; do not report unqualified “100% predicate coverage.”

## AH. Layer A vs Layer B truth table

The four [truth-table cases](b2_t4_laq_artifacts/layer_a_layer_b_truth_table.json) matched PASS only for A PASS/B PASS; other combinations STOP. A valid-looking wrong filesystem digest is incorrectly classified A PASS by the candidate, so the truth table alone does not establish Layer-A correctness.

## AI. PPQ-V2 relation

PPQ-V2's reviewed candidate schema/durable readback and W1–W7 publication are separate and remain valid within scope. They cannot replace the worker-receipt Layer-A path. PPQ-V2 PASS + canonical W1–W7 + invalid Layer A must yield STOP; original R3 reproduces this defect class.

## AJ. Post-mutation failure semantics

The pure [post-mutation contract](b2_t4_laq_artifacts/post_mutation_failure_semantics.json) yields `partial_update=true`, `route_poisoned=true`, no success publication. This is a future hypothetical failure path, not mutation of R3's exited in-memory route.

## AK. Pre-mutation failure semantics

The pure [pre-mutation contract](b2_t4_laq_artifacts/pre_mutation_failure_semantics.json) yields `false/false` and no success publication. LAQ itself has no learner mutation; its qualification STOP is not a poisoned runtime attempt.

## AL. Final frozen offline dry run

Exactly one frozen positive offline dry run was executed. Its [immutable result](b2_t4_laq_artifacts/final_dry_run_result.json) reports hypothetical PASS for the uncorrupted R3 projection, using 96 crosschecks and 167 validator checks. After that run, no positive final rerun occurred. The subsequent independent counterexample invalidates its sufficiency; the file is preserved as a bounded pre-audit observation.

## AM. Final historical R3 negative control

Exactly one [original-R3 receipt negative control](b2_t4_laq_artifacts/final_original_r3_negative_control.json) followed: Layer A FAIL, Layer B PASS, overall STOP. This is expected and does not reclassify R3.

## AN. Protected-source preservation

The full historical R3/R1/R2 path-size-content digests and all named production, W2E/W2I/PW, PPQ-v1/v2, normalizer and R3 harness hashes matched before/after and after the final controls. Production modifications 0; PPQ-V2 modifications 0; historical R3 modifications 0.

## AO. LAQ candidate identities

Frozen [source manifest](b2_t4_laq_artifacts/laq_source_identity_manifest.json): helper `597a3b6ad1e6765d7efcfcce4bc289458ca47c48e65905a243ccf5ac786f4de9`, runner `80d0025b25a8825823a39d937a83710b2ba1c889a553e264d5d12966fd8562cf`, schema `992ff940919d45be9694deda6d5a4d75fbb76e131cf6b9770dec0b4618e71f85`, one-final-positive result `5be313cc50f8675d32efef547d5db4f50913c3790360ac21f73b3462b438c847`. These are **frozen failed-candidate identities**, not review PASS.

## AP. Future RE6-R4 integration plan

The [design-only plan](b2_t4_laq_artifacts/future_re6_r4_integration_plan.json) calls for fresh worker projection, exact reviewed source bindings, full Layer A before supervisor adjudication, unchanged PPQ-V2/W2E/W2I/PW, EP-Q Layer B, fresh namespace, one worker/zero retries, and no R3 learner reuse. It is provisional; the filesystem digest binding must be repaired and independently requalified before any R4 authorization.

## AQ. Exact execution counts

Formal supervisors/workers/retries, CUDA probes, AppLauncher, environments, resets, physical steps, learner constructions/mutations, checkpoint I/O, public activation, evaluation/playback and RE6-R4 attempts were all **0**. One qualification artifact-generation invocation, one final frozen positive offline dry run, and one final original-R3 negative control were run; no second final positive. `py_compile` was invoked for the helper once and later for helper+runner once. Named A–BE negatives 57/57 STOP; default/absence 38/38 STOP; field-presence 120/120 STOP; Layer-A/B truth table 4/4; supplemental historical-predicate negatives 38/39 STOP, **one unexpected PASS**. Exploratory approved-interpreter/quoting probes occurred; a reliable all-command total was not captured and is not invented. Git add/commit/push 0/0/0.

## AR. Retained nonclaims

No Layer-A qualification PASS, GPT REVIEW PASS, RE6-R4 authorization, checkpoint continuation, long/paper-scale training, public learned-policy readiness, training quality, evaluation/playback, or historical R3 repair is established. The uncorrupted hypothetical R3 projection does not validate all adversarial receipt values. The public route stays DORMANT/BLOCKED.

## AS. Final classification

`PHASE-B2-T4-LAQ-STOP-RAW-RECEIPT-CROSSCHECK-INCOMPLETE`. The source-backed blocker is a wrong-but-well-formed filesystem authority digest accepted by the candidate supervisor. The candidate's initial PASS-looking final file was archived byte-exact at SHA-256 `9fb1e41da16d1d39e194243d2f6cff2ca178adfd0dba84eec4514de74c479aa7`, then superseded in the corrected final result. Historical RE6-R3 remains **GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED**. RE6-R4 remains NOT AUTHORIZED.

## AT. GPT-review handoff

Review the frozen helper/runner/schema, 39 RE5 source checks, R3 original-vs-raw mismatch, 57 requested negatives, 120 field-presence negatives, the one final positive and one negative control, and especially the 39-predicate post-final audit's filesystem-digest counterexample. A separately authorized repair/qualification must bind that digest to authoritative filesystem-precondition bytes and audit all other valid-looking identities before any new final dry run or R4 attempt. Do not repair R3 in place, reuse its learner, launch Isaac/AppLauncher/CUDA, perform checkpoint I/O, activate public route, stage or commit under this instruction.
