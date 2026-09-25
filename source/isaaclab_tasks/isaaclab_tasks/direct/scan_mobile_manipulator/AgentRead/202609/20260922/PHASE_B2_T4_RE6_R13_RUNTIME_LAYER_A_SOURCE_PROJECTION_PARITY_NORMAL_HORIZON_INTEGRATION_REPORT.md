# Phase B2-T4-RE6-R13 Runtime Layer-A Source-Projection Parity Normal-Horizon Integration Report

Date: 2026-09-22  
Run ID: `b2-t4-re6-r13-20260922-formal01-339ec669e33b4f40be9dfea9347a0ed7`  
Final classification: **PHASE-B2-T4-RE6-R13-STOP-RUNTIME**

## Executive result

R13 does not qualify. Pure Stage A established the requested shared canonical-artifact-to-Layer-A source-map builder and passed the complete 179-path source inventory/removal matrix, six semantic negatives, the 43/90 Layer-A positive, inherited 39/39 predicates, and RACQ 9/9 predicates. The frozen live attempt then stopped at the blocked PID-bound, pre-release boundary because a write-once source-phase authority artifact already existed in the formal run directory.

The single formal supervisor invocation created one blocked worker handshake and one live RACQ PID binding, but it did not release the worker. CUDA, AppLauncher, environment construction, physical transitions, transactions, and learner mutation all remained zero. Therefore `partial_update=false`, `route_poisoned=false`, and retry count is zero. No source was edited after Stage-A freeze and R13 was not retried.

## RUNTIME LAYER-A SOURCE PROJECTION

| Projection boundary | Builder | Required paths | Unmapped | Value mismatches | Alternate builders | W7 qualified count | Result |
|---|---|---:|---:|---:|---:|---:|---|
| Pure Stage A | `build_layer_a_source_map_from_canonical_artifacts` | 179 | 0 | 0 | 0 | 160 | PASS |
| Live-bound pre-release smoke | same frozen implementation | not reached | n/a | n/a | 0 | n/a | NOT EVALUATED |
| Actual runtime | same frozen implementation | not reached | n/a | n/a | 0 | n/a | NOT EVALUATED |

The R12 failure was reproduced in Stage A by removing only `witnesses.W7.qualified_count`; the reviewed Layer-A projector stopped with `MISSING-SOURCE:W7.qualified_count`. The repaired shared builder reads W7 from `W7_runtime_p2_immutability.json` and projects the canonical value `160`. This proves the Stage-A projection slice only; the runtime projection was not reached in R13.

## Required source inventory and lineage

- Required source paths: 179.
- Explicit lineage rows: 179.
- Unmapped paths: 0.
- Full one-at-a-time removal controls: 179 STOP / 0 unexpected PASS.
- Representative semantic controls: 6 STOP / 0 unexpected PASS.
- Stage-A Layer-A receipt: 43/43 top-level fields and 90/90 nested PPQ fields.
- Inherited predicates: 39/39 PASS.
- RACQ predicates: 9/9 PASS.
- Deferred test-side negatives: 0.

Canonical evidence is in `layer_a_required_source_path_inventory.json`, `layer_a_runtime_source_lineage.json`, `runtime_layer_a_projection_parity.json`, `runtime_layer_a_projection_value_crosscheck.json`, `shared_builder_required_source_negative_matrix.json`, `shared_builder_semantic_negative_matrix.json`, and `stage_a_layer_a_positive.json`.

## Stage-A repairs and freeze

Four minor test-side repairs were completed before freeze:

1. R12's Stage-A/runtime source-map divergence was replaced by one shared canonical-artifact builder.
2. Supervisor handling of an upstream Layer-A STOP was guarded so success-only artifacts are not unconditionally read.
3. Collection-level witness lineage was mapped to the complete W1-W7 canonical artifact set.
4. Two semantic-negative mutations were aligned with predicates actually enforced by the reviewed LAQ validator.

The full Stage-A suite was rerun after the last repair. Final Stage A passed with supervisor/worker/CUDA counts of 0/0/0, unresolved repairs 0, unexpected PASS 0, and failure-path supervisor handling PASS. The frozen harness SHA-256 is `4ae682ca45ef89f718519ebdf88adefbd20de67c1a6f604f3dc905814be7a356`; `stage_a_final_readiness.json` SHA-256 is `4cf527393ed2a36c469ae7a1f851e01aa8c0600a617114e7206358810f447cea`.

One pre-official fixture-only namespace residue was detected by the namespace-exists guard and moved intact to `C:\Users\33506\AppData\Local\Temp\r13_official_namespace_residue_20260922_212913` for preservation. It contained 16 canonical projection-fixture files and no run identity, live authority, supervisor, worker, or CUDA evidence. The official Stage A was then run once against an absent namespace and passed.

## Failure-path supervisor behavior

The Stage-A negative for an upstream Layer-A STOP passed: Layer-A remained STOP, the success gate was `NOT_EVALUATED`, no secondary `FileNotFoundError` was generated, and no false PASS occurred.

The actual R13 stop happened earlier than Layer A. Post-run adjudication likewise preserves the original authority-collision cause and records success gate 77 as `NOT_EVALUATED`; it does not reinterpret absent success artifacts as another failure.

## Artifact lifecycle and exact failure boundary

The live runtime authority and RACQ run binding were created after freeze. The formal supervisor then launched blocked worker PID `38620` and persisted `worker_pid_handshake.json` with state `BLOCKED_PRE_RUNTIME`. During `prepare_worker_release`, the source-phase binding helper attempted to publish:

`ppq_source_phase_authority/offline-b2-t4-re6-r13-formal-source-phase.source_phase_authority.json`

The path already existed. Its companion source-phase run binding carried worker PID `31916`, the earlier Stage-A process identity, while the live RACQ binding and blocked-worker handshake carried PID `38620`. The write-once producer correctly raised `ARTIFACT-ALREADY-EXISTS` instead of overwriting the artifact. This is an unresolved post-freeze runtime setup/artifact-lifecycle failure. Under the no-source-repair-after-freeze and no-retry rules, execution stopped permanently at that boundary.

`formal_supervisor_result.json` was not produced because the supervisor stopped before its canonical result-publication boundary. Post-run evidence is explicitly separated in `post_run_supervisor_exception_adjudication.json`, `failure_receipt.json`, `success_gate_77.json`, and `final_result.json`.

## Primary process table

| Stage | Supervisor invocations | Worker processes | PID binding | Release | CUDA | Learner mutation |
|---|---:|---:|---:|---:|---:|---:|
| Pure Stage A | 0 | 0 | 0 | 0 | 0 | 0 |
| Live pre-process | 0 | 0 | 0 | 0 | 0 | 0 |
| Blocked PID-bound failure | 1 | 1 | 1 | 0 | 0 | 0 |

Final counts: live authority/supervisor/worker/PID binding/release/retry = 1/1/1/1/0/0. Both PID `38620` and stale Stage-A binding PID `31916` were inactive at post-run audit; matching active process count was zero.

## Runtime, PW, NORM, PPQ, W1-W7, Layer A, and Layer B

| Slice | R13 result | Evidence boundary |
|---|---|---|
| Runtime | NOT STARTED | worker never released |
| Physical transitions / transactions / S10 / ledger / bridges | 0 / 0 / 0 / 0 / 0 | pre-release STOP |
| PW runtime campaign | NOT STARTED | 0 critic / 0 actor-factor runtime records |
| NORM-R1 runtime normalization | NOT STARTED | canonical runtime result absent |
| PPQ runtime receipt | NOT STARTED | candidate receipt absent |
| W1-W7 runtime witnesses | NOT STARTED | runtime witness set absent |
| Runtime Layer A | NOT EVALUATED | source projection was not invoked |
| Layer B | NOT EVALUATED | blocked before runtime |
| Success gate 77 | NOT EVALUATED | 0/77 adjudicated as success |
| Process quiescence | PASS | no matching live process |

The successful Stage-A fixtures do not substitute for these missing live-runtime results.

## Repository and historical preservation

- Historical R12 remains `GPT REVIEW STOP CONFIRMED / POST-MUTATION / POISONED / RETAINED / NEVER REUSE` and was not rerun or modified.
- Frozen R12 report, harness, Stage-A, final, failure, quiescence, W7, and candidate identities passed the R13 preservation gate.
- Production, lifecycle, resolver, controller, learner, NORM-R1, PPQ, LAQ, RACQ/RACQ-R1, installed HARL, and installed-package sources were not modified.
- HEAD remained `b71d85a32f51be6ada324f870813a56bb45dd396`; the staged set remained 359 entries with raw staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
- This task issued no `git add`, `git commit`, or `git push`.

## Retained nonclaims and GPT-review handoff

R13 does not establish runtime source-projection parity, live positive consistency, bounded normal-horizon learned-training integration, PW/NORM/PPQ/W1-W7 runtime success, Layer-A PASS, Layer-B PASS, success-gate 77 PASS, checkpoint continuation, long/paper-scale training readiness, evaluation/playback readiness, or public-route activation.

The R13 learner was never constructed or mutated, so this attempt is not poisoned; nevertheless its authority, run identity, bindings, and worker PID are retired and must not be reused. Do not retry R13, do not launch R14, do not start transaction 161, and do not begin checkpoint continuation or long/paper-scale training without a new explicit instruction.
