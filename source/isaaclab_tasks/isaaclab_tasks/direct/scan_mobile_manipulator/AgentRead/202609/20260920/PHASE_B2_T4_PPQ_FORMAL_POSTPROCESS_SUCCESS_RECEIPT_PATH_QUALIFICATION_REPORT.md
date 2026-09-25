# Phase B2-T4-PPQ — Formal postprocess and success-receipt path qualification

Date: 2026-09-20. Classification: `PHASE-B2-T4-PPQ-FORMAL-POSTPROCESS-SUCCESS-RECEIPT-PATH-QUALIFIED-AWAITING-GPT-REVIEW`. This is a **pure/static/offline candidate qualification**, not a runtime retry or an independent GPT review pass. The immutable RE6-R1 attempt remains GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED.

## A. Repository authority

Branch `main`; HEAD, `origin/main`, and merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. Before PPQ writes, full porcelain had 17,046 lines and SHA-256 `98ee50da98d0deb5a24e92562554fcdd761a6c1b096582e4c03a29647e319f1c`; the staged migration had 359 paths, staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. The [captured authority](b2_t4_ppq_artifacts/repository_authority.json) records the later full porcelain after the initial byte-exact progress archive and PPQ-in-progress note; the staged digests remained exact. No staging or commit was performed.

## B. Reviewed starting authority

B2-R0–R7, T0–T3, and T4-NR/SR/ZD/EP-Q/PW/W2E/W2I are GPT REVIEW PASS / CLOSED. RE5 is historical poisoned STOP; RE6 is pre-runtime STOP, not poisoned; RE6-R1 is reviewed historical poisoned STOP. PPQ is separately authorized only for offline postprocessing. RE6-R2 is not authorized.

## C. Historical RE6-R1 preservation

All 7,331 files under `b2_t4_re6_r1_artifacts/` (1,938,776,606 bytes) were SHA-256 inventoried before replay and re-hashed after the one final dry run; all paths, sizes, and hashes matched. See [artifact identity](b2_t4_ppq_artifacts/re6_r1_artifact_identity.json) and [candidate identity manifest](b2_t4_ppq_artifacts/ppq_source_identity_manifest.json). No historical artifact was rewritten, appended, or removed. Historical W1–W7 remain provisional, not success certificates.

## D. Exact RE6-R1 failure

The sole historical formal attempt completed 320 physical transitions, 160 S10/ledger rows, 159 bridges, and mutation-bearing learner updates. After RE3's inherited witness postprocessor had published W1–W7, RE5's inherited worker raised `KeyError('_base_atomic_json')` while rewriting the final result. The durable worker receipt says `failure_stage=postprocess_and_witness_gates`, `partial_update=true`, `route_poisoned=true`; Layer A failed and EP-Q Layer B passed. The raw classification remains `PHASE-B2-T4-RE6-R1-STOP-FORMAL-WORKER-FAILURE`; the source-backed narrower classification remains `PHASE-B2-T4-RE6-R1-STOP-INHERITED-POSTPROCESS-KEYERROR-AFTER-MUTATION`; reviewed classification is `PHASE-B2-T4-RE6-R1-INHERITED-POSTPROCESS-KEYERROR-AFTER-MUTATION-REVIEW-STOP`.

## E. `_base_atomic_json` source trace

| Question | Finding | Source evidence |
|---|---|---|
| Where accessed? | `engine['_base_atomic_json']` in RE5 `run_formal_worker`, line 1144, after `RE3._postprocess_success` returns and before PW reconciliation/success receipt. | `scripts/environments/test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py:1132-1148` |
| Caller? | RE6-R1 main invokes `_ENGINE['run_formal_worker']`. | `scripts/environments/test_assignment_phase_b2_t4_re6_r1_normal_horizon_learned_training_integration.py:312` |
| Who supplied the alias historically? | RE1 outer module saved `_base_atomic_json = _INNER['_atomic_json']` before installing a ledger-aware inner wrapper. RE3 accesses the outer alias correctly. | RE1 harness lines 667-678, 1022-1030; RE3 harness lines 278-324 |
| Was it production authority? | No. It is a test-harness serialization alias; no production lifecycle or learner source supplies this key. | RE1/RE3 harness source chain in [trace](b2_t4_ppq_artifacts/inherited_postprocess_keyerror_trace.json) |
| Was it guaranteed by engine construction? | No. RE5 chooses `engine = RE3._RE3['_INNER']`; the alias belongs to outer `_RE3`, not the inner engine. | RE5 line 1079; RE1 line 678; RE3 lines 311, 320 |
| Why did preflight miss it? | Synthetic Layer-A validation and readiness exercised receipt predicates, not the inherited success-postprocess lookup at RE5 line 1144. | RE6-R1 preflight/readiness artifacts and historical failure receipt |
| Future persistence authority? | Explicit PPQ test-side `persistence_writer` and `receipt_reader` arguments, with schema and readback/digest checks. | [dependency contract](b2_t4_ppq_artifacts/postprocess_dependency_contract.json), new PPQ helper |

The persisted [trace](b2_t4_ppq_artifacts/inherited_postprocess_keyerror_trace.json) is source-derived. The old RE1/RE3 postprocessor also publishes canonical witnesses before later gates and deletes non-retained detail files; PPQ never invokes it against historical evidence.

## F. Dependency-authority classification

Primary category **B**: historical test-harness helper accidentally addressed through `engine`. It also has a redundant-alias aspect (category C), but is not a production/runtime dependency. The precise RE5 inner-dictionary lookup had no contract. PPQ did not insert a magic key, monkeypatch the engine, or use a silent fallback. See [classification](b2_t4_ppq_artifacts/base_atomic_json_authority_classification.json).

## G. Why preflight missed it

The RE6-R1 preflight's synthetic success payload made its Layer-A predicates pass; the sole readiness replay did not call the full inherited postprocessor through the RE5 final rewrite. Thus neither reached the failing key access or tested publication ordering. Passing preflight did not establish full success-path qualification.

## H. Repaired postprocess architecture

The new candidate [pure PPQ helper](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_ppq_postprocess.py) accepts evidence, selector, PW reconciliation, reviewed identity, writer, reader, and namespace explicitly. It re-adjudicates the full campaign, constructs a versioned Layer-A candidate, validates, writes and reads back its receipt, validates the digest, then publishes canonical aliases. It has no Isaac, HARL learner, CUDA, or production import.

## I. Explicit dependency contract

Mandatory arguments are transaction/bridge/lifecycle/actor evidence, reviewed W2E selector, W2I digest, reviewed PW verifier output, explicit persistence writer, explicit readback reader, and output namespace. Missing dependencies STOP before publication. Mutable `engine` and `_base_atomic_json` are forbidden evidence keys. See [contract](b2_t4_ppq_artifacts/postprocess_dependency_contract.json).

## J. Reviewed W2E/W2I bindings

The current reviewed W2E selector raw SHA-256 is `8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0`. The reviewed W2I binding manifest raw SHA-256 is `3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b`. Both are direct success-receipt fields, not indirect engine metadata. The exact selector was called on normalized real RE6-R1 lifecycle, transaction, and bridge ledgers, reproducing its retained 29-candidate/12-valid inventory and env1/robot1/task10 tx12→15→16 witness.

## K. PW persistence authority

The unchanged reviewed PW helper SHA-256 is `e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b`. Its `verify_transaction` checked all 160 transactions' immutable files (41 critic and four actor/factor records per transaction), totaling 6,560 and 640. PW campaign and transaction reconciliation rows agreed; missing, duplicate, order, digest, and temp-residue faults were all zero. This did not substitute a new PW mechanism.

## L. Layer-A success receipt schema

The strict [`b2_t4_ppq_formal_success_receipt_v1` schema](b2_t4_ppq_artifacts/success_receipt_schema.json) requires exactly its declared fields and types, known version and identity hashes, finite values, mutually consistent counters, positive witness identities, and healthy route flags. Missing, extra, wrong-type, nonfinite, digest, count, W2, and poison contradictions STOP. See [schema tests](b2_t4_ppq_artifacts/success_receipt_schema_tests.json). The PPQ success receipt is hypothetical and does not overwrite historical RE6-R1's poisoned failure receipt.

## M. Campaign fields

Direct fields bind physical=320, S10=160, ledger=160, bridges=159, `tx161_started=false`, terminal/autoreset=2, post-autoreset learned transaction=true, TASK_COMPLETED=22, and max coverage=11. These were reconciled to the real final/ledger evidence.

## N. Witness fields

W1, W2E, and W3–W7 each bind direct PASS status. W2E binds 29/12 and selected env1/robot1/task10, claim tx12/step23, completion tx15/step30, and reopen tx16/step31. W7 binds 160/160. W5 binds TIME_LIMIT=2 at tx150; W6 binds a fresh post-autoreset update at tx151.

## O. Learner fields

Direct fields bind actor backward/step=165/165, critic backward/step=1600/1600, critic classes 1576 nonzero plus 24 zero-effective, ValueNorm.update=1600, event returns=160, stock compute_returns=0, actor/critic Adam continuity, ValueNorm continuity, exact plans/factor audits, and numerical health. PPQ inspected retained snapshots/ledgers; it did not construct or mutate a learner.

## P. Route-health fields

Every candidate success requires `partial_update=false` and `route_poisoned=false`; either true is schema-invalid. These values describe **only the hypothetical PPQ candidate**. Historical RE6-R1 remains `true/true` and poisoned.

## Q. Success publication ordering

W1–W7 candidates stay in memory until full payload construction, schema validation, durable candidate receipt write, readback, digest equality, and readback schema validation all pass. Only then are canonical aliases written in `final_dry_run/`. Premature and stale-provisional publication negatives STOP. See [order contract](b2_t4_ppq_artifacts/success_publication_order_contract.json).

## R. Real RE6-R1 positive offline replay

The [positive replay](b2_t4_ppq_artifacts/re6_r1_positive_offline_replay.json) used the real immutable completed campaign. All 24 ordered stages passed. Its first full pass used an in-memory receipt store to test end-to-end semantics without creating canonical files; the final frozen pass used durable PPQ-only files. Neither replay reclassifies RE6-R1.

## S. W1 adjudication

Retained W1 ownership witness passed, and all 160 actor reconciliation rows were exact with zero faults. This is PPQ replay PASS only.

## T. W2E adjudication

The exact reviewed selector independently returned 29 candidates/12 valid, matching the retained inventory and selected identity. The old textual-claim W2 is not authoritative. This is PPQ replay PASS only.

## U. W3–W7 adjudication

W3 zero-DVM actor, W4 nonterminal bootstrap, W5 terminal/autoreset, W6 post-autoreset transaction, and W7 160/160 runtime P2 immutability all passed source-backed checks. Historical canonical-looking RE6-R1 files remain provisional because their original publication preceded the fatal KeyError.

## V. PW reconciliation

All actual immutable PW files were verified by the reviewed helper, agreeing with 160 transaction PW rows and the campaign summary: critic 6560/6560, actor/factor 640/640, five fault counts zero. A prior read-only PW probe and the positive/final PPQ passes used the same reviewed verifier; no PW file changed.

## W. Success receipt construction

The [candidate receipt](b2_t4_ppq_artifacts/final_dry_run/candidate_success_receipt.json) directly contains all required campaign, identity, PW, witness, learner, route, and classification fields. Key examples:

| Category | Required field | RE6-R1 PPQ replay value | PASS |
|---|---|---:|---|
| Identity | W2E selector SHA / W2I binding SHA | exact reviewed SHA / exact reviewed SHA | Yes |
| Campaign | physical / S10 / ledger / bridges | 320 / 160 / 160 / 159 | Yes |
| PW | critic / actor-factor | 6560 / 640 | Yes |
| W2E | candidates / valid / selected | 29 / 12 / env1 robot1 task10, tx12→15→16 | Yes |
| W1–W7 | statuses | all PASS; W7 160/160 | Yes |
| Learner | actor step / critic step / ValueNorm | 165 / 1600 / 1600 | Yes |
| Returns | event / stock | 160 / 0 | Yes |
| Route | partial_update / route_poisoned | false / false **in hypothetical PPQ success only** | Yes |

## X. Durable publication

The final pass wrote a candidate receipt through the explicitly passed PPQ-only fsync/atomic-replace writer. It wrote to `b2_t4_ppq_artifacts/final_dry_run/`, not the historical RE6-R1 tree. The in-memory positive pass used the same dependency contract and ordering.

## Y. Readback/digest validation

The receipt was read back, compared structurally, compared by SHA-256 to the writer result and canonical payload digest, and schema-validated again before aliases. The final receipt's exact digest and all eight candidate file hashes are in [final dry-run result](b2_t4_ppq_artifacts/final_dry_run_result.json). Synthetic readback and digest corruption both STOP.

## Z. Negative matrix

The [matrix](b2_t4_ppq_artifacts/postprocess_negative_matrix.json) has 36 formal cases, 36 expected STOP, 36 actual STOP, unexpected PASS 0. It includes all requested A–AD plus six schema/counter extensions.

| Case group | Expected | Actual | PASS |
|---|---|---|---|
| A–F missing persistence/hidden engine/W2E-W2I digests | STOP | STOP | Yes |
| G–I missing/zero/inconsistent W2 | STOP | STOP | Yes |
| J–L PW counts/digest fault | STOP | STOP | Yes |
| M–Q tx/bridge/W7/W5/W6 mismatch | STOP | STOP | Yes |
| R–V actor/critic/Adam/ValueNorm/numerical fault | STOP | STOP | Yes |
| W–X poisoned success payload | STOP | STOP | Yes |
| Y–AC write/readback/digest/premature/stale publication | STOP | STOP | Yes |
| AD–AJ malformed/missing/type/version/nonfinite/counter/W2 schema | STOP | STOP | Yes |

## AA. Failure receipt qualification

The [post-mutation failure receipt](b2_t4_ppq_artifacts/failure_receipt_matrix.json) retained stage, exception, completed tx=160, ledger=160, bridges=159, W1–W7 provisional states, W2E 29/12, PW state, and `partial_update=true`/`route_poisoned=true`. It published no canonical success witness.

## AB. Pre-mutation failure qualification

The [pre-mutation failure receipt](b2_t4_ppq_artifacts/pre_mutation_failure_matrix.json) retained its preflight stage and exception with zero counts, `partial_update=false`/`route_poisoned=false`, and no canonical success witness.

## AC. Final frozen dry run

Exactly one final full-postprocess dry run was executed after helper/schema/negative verification. All campaign, W1–W7, W2E/W2I, PW, receipt, persistence, readback, digest, and publication-order gates passed. The [result](b2_t4_ppq_artifacts/final_dry_run_result.json) records 24 ordered stages and exactly eight PPQ-only candidate files. No hidden engine key was accessed.

## AD. Historical artifact preservation

The before/after full-tree identity comparison passed for 7,331 RE6-R1 files. Neither the dry run nor synthetic negatives wrote into the RE6-R1 namespace. Historical RE5 and RE6 STOP evidence was not modified.

## AE. Protected-source preservation

Production full transaction, real adapter, environment, W2E selector, W2I binding, PW helper, and historical RE6-R1 harness hashes matched before/after. See [before identity](b2_t4_ppq_artifacts/protected_source_identity.json) and [before/after equality](b2_t4_ppq_artifacts/protected_source_identity_after.json). Production semantic modifications: zero.

## AF. PPQ helper identity

The [candidate manifest](b2_t4_ppq_artifacts/ppq_source_identity_manifest.json) freezes helper SHA-256 `1bc419e96fe095ef15b70483abbbacca57580345d803d6ce83b211e68054352d`, runner SHA-256 `c922a352c284dcef2fd1a761ceab1c06c4254d0e84c95b9b508b93c82b1bcfba`, success-schema artifact SHA-256 `9423742d525acb154c789c4b99922cc366bc596decef1be783c0ac1ffc98e5f6`, and final dry-run-result SHA-256 `e92258a881a3fa47d3fe8c0aaf6c3b9281920430582f184a7b7073e563213d7c`. Status is **CANDIDATE / AWAITING GPT REVIEW**, not self-reviewed.

## AG. Future RE6-R2 integration plan

The [design-only plan](b2_t4_ppq_artifacts/future_re6_r2_integration_plan.json) imports the PPQ helper; passes normalized ledgers, exact W2E selector, reviewed PW verifier, W2I and source identities, writer/reader, and a fresh namespace explicitly; retires the RE3 inherited success postprocessor plus RE5 hidden-key final rewrite; constructs Layer A before publication; writes failure receipt before environment close and poisons after observed mutation; checks candidate helper/runner/schema and reviewed dependency SHAs in preflight. It does **not** create, authorize, or run RE6-R2.

## AH. Exact execution counts

Explicit approved-interpreter checks: 2 (standalone executable check and runner guard); `py_compile`: one invocation covering two new files; targeted source-trace `rg` invocations: 5 (including two unsuccessful shell-pattern probes), plus three numbered source-window inspections. Exploratory payload-only real-evidence build: 1. Full in-memory positive end-to-end PPQ replays: 2 (preflight sanity and retained qualification); formal retained negative matrix: 36/36, plus 36/36 earlier in-memory sanity executions; unexpected negative PASS: 0. Failure-path cases: 1; pre-mutation cases: 1. Reviewed PW all-record verification: 3 read-only passes. Final frozen durable full-postprocess dry runs: **exactly 1**. AppLauncher/environment/reset/physical steps/learner constructions/learner mutations/formal supervisor/formal worker/CUDA probes/RE6-R2 attempts/checkpoint I/O/public activation/evaluation-playback: **all 0**. Production, historical RE5, RE6, and RE6-R1 modifications: **all 0**. Git add/commit/push: **0/0/0**.

## AI. Retained nonclaims

This is not runtime success, learner-update readiness for a future run, checkpoint-continuation qualification, long/paper-scale training authority, public learned-policy readiness, evaluation/playback evidence, or GPT REVIEW PASS. It does not rescue or reclassify historical RE6-R1, RE5, or RE6. RE6-R1's learner must never be resumed, repaired, checkpointed, or reused.

## AJ. Final classification

`PHASE-B2-T4-PPQ-FORMAL-POSTPROCESS-SUCCESS-RECEIPT-PATH-QUALIFIED-AWAITING-GPT-REVIEW`. B2-T4-PPQ: **COMPLETE / AWAITING GPT REVIEW**. Postprocess/receipt blocker: **QUALIFIED OFFLINE / AWAITING GPT REVIEW**. Production lifecycle, W2E, and PW defects: **NOT ESTABLISHED**. RE6-R2: **NOT AUTHORIZED**. Public route: **DORMANT / BLOCKED**. Commit: **NONE**.

## AK. GPT-review handoff

Review the candidate helper and runner against the source trace, all 36 negative cases, receipt schema, final dry run, historical/protected hashes, and future integration plan. Independently confirm that the retained RE6-R1 STOP and its poisoned learner stay immutable. Do not launch RE6-R2, AppLauncher, an environment, a learner, checkpoint I/O, or public activation without a separate explicit authorization after review.
