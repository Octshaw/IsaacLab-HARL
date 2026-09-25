# Phase B2-T4-LAQ-R1 — Raw-receipt authority binding repair and requalification

Date: 2026-09-21. **Classification: `PHASE-B2-T4-LAQ-R1-RAW-RECEIPT-AUTHORITY-BINDING-QUALIFIED-AWAITING-GPT-REVIEW`.** This is a pure/static/offline candidate, not a self-issued GPT REVIEW PASS and not authorization for RE6-R4.

## A. Repository authority

Before the first R1 write, branch `main`; HEAD, `origin/main`, and merge-base were `b71d85a32f51be6ada324f870813a56bb45dd396`. Full porcelain had 25,257 rows and SHA-256 `b4e1362846f69fad5bebd7757ef65dfe61946c8873a0f77f95d290ae1a2016b7`. The pre-existing migration stayed at 359 staged paths, staged-index SHA `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, monthly path-set SHA `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. [Machine record](b2_t4_laq_r1_artifacts/repository_authority.json). No add/commit/push/reset/checkout/clean occurred.

## B. Reviewed starting authority

B2-R0–R7, B2-T0–T3, and B2-T4-NR/SR/ZD/EP-Q/PW/W2E/W2I/PPQ-v1/PPQ-V2 retain their supplied reviewed states. RE6-R3 remains **GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED** and its learner remains unusable. LAQ remains **STOP / NOT QUALIFIED**. [Snapshot](b2_t4_laq_r1_artifacts/reviewed_starting_authority.json).

## C. Failed LAQ preservation

The failed LAQ helper `597a3b6a…62e9`, runner `80d0025b…62cf`, schema `992ff940…f85` and complete 30-file artifact tree remain byte-identical to the preserved pre-R1 baseline. R1 uses new files and never amends the failed candidate into PASS. [Preservation](b2_t4_laq_r1_artifacts/failed_laq_preservation.json).

## D. Decisive LAQ defect

The exact prior corruption sets `filesystem_precondition_digest` to 64 zero hex characters. The frozen failed LAQ again yields structural PASS, raw-crosscheck PASS, supervisor PASS. R1 independently hashes the exact `filesystem_precondition.json` bytes and yields authority FAIL and supervisor STOP. [Reproduction and repair](b2_t4_laq_r1_artifacts/filesystem_digest_gap_reproduction_and_repair.json).

## E. Scope of R1 repair

R1 adds only a test-side authority overlay and offline qualification runner. It does not change production, PPQ-v1/v2, W2E/W2I/PW, normalizer, R3 harness, historical evidence, environment, learner, CUDA, or process behavior. Its purpose is exact `authoritative source → receipt → crosscheck → Layer A → supervisor` binding.

## F. Mandatory-field classification

All 120 mandatory fields have one of seven explicit categories: direct runtime observation, relational runtime derivation, reviewed source identity, artifact-content digest, multi-source composite digest, caller-bound identity, or contract-version identity. Each entry gives purpose, exact authority, computation, raw-byte availability, prior LAQ behavior, and repair status. [Inventory](b2_t4_laq_r1_artifacts/authority_bound_field_inventory.json).

## G. Authority-bound field inventory

The inventory contains 120 unique mandatory fields. All 120 have structural validation, semantic runtime/source equality, a type-preserving semantic corruption control, and supervisor consumption. This defines authority coverage over this closed receipt, not generic production coverage.

## H. Digest/identity field inventory

There are 12 receipt-carried digest/identity paths: nine fixed-file raw-byte identities and three canonical/composite identities. Three R1 self-identities are externally frozen rather than trusted from the receipt. [Digest inventory](b2_t4_laq_r1_artifacts/digest_identity_field_inventory.json).

## I. Authority source registry

The frozen [registry](b2_t4_laq_r1_artifacts/authority_source_registry.json) assigns exactly one authority definition to every mandatory field. The validator rejects any registry drift and does not accept caller-selected arbitrary files. No receipt field self-authorizes its digest.

## J. Source snapshot

The [snapshot](b2_t4_laq_r1_artifacts/authority_source_snapshot.json) records 30 fixed file authorities by repository-relative path, raw byte count, SHA-256, and semantic role. It contains identities, not copied protected source bytes.

## K. Filesystem digest binding

`filesystem_precondition_digest` equals SHA-256 of raw bytes from the exact historical `filesystem_precondition.json`, `5f141577f750664cbc1da5a74532664f8b5153e9364c51ac267d119d3e5462bd`. Content validation also requires its version, NTFS assertion, resolved volume, same directory/volume temp-final policy, artifact-root containment, and qualification flag. The separately bound static authority must identify the reviewed PW helper, so a correct hash of semantically invalid content cannot pass. [Contract](b2_t4_laq_r1_artifacts/filesystem_digest_binding_contract.json).

## L. Production composite digest

The production digest uses a fixed sorted name/path map for environment, full transaction, and real adapter. Each component is SHA-256 of raw bytes; sorted-key compact UTF-8 JSON of the name-to-SHA map is then hashed. It has no timestamps, absolute paths, or iteration-order dependence. [Contract](b2_t4_laq_r1_artifacts/production_identity_digest_contract.json).

## M. Config digest

The process-config authority is canonical sorted-key compact UTF-8 JSON of `process_config_authority.config`; its digest must also equal the artifact's recorded value. The PPQ config identity separately hashes the explicit four-field qualified cadence map. Run ID, PID, phase, T, and transaction count are cross-bound to raw evidence. [Contract](b2_t4_laq_r1_artifacts/config_identity_digest_contract.json).

## N. Reviewed source SHA bindings

W2E selector, W2I manifest, PW helper, PPQ-V2 helper/schema and normalizer values are independently recomputed from their exact bytes. W2I additionally validates its referenced selector, offline runner and contract artifact. PPQ-V2 schema bytes must parse to the helper-generated schema document.

## O. Self-identity binding

The receipt carries no R1 helper/schema self-claims. After qualification, the helper, runner, contract and registry were externally frozen; final modes compare current raw-byte SHA values to the pre-final manifest before doing any work. [Pre-final freeze](b2_t4_laq_r1_artifacts/laq_r1_source_identity_pre_final.json).

## P. Source-path policy

Authority is both exact-path-bound and content-bound. Absolute/traversal paths, symlinks, directories, aliases, arbitrary replacement paths, and relocation-by-content-only are rejected. A future fresh run requires a separately reviewed run-specific registry; this historical R3 registry is not a formal R4 runner. [Policy](b2_t4_laq_r1_artifacts/source_path_binding_policy.json).

## Q. Projection helper architecture

The new pure [R1 helper](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_laq_r1_worker_receipt.py) reuses LAQ's structural projection only after every supplied raw object equals its fixed-path decoded artifact and all file/composite identities are recomputed. Candidate construction does not confer authority.

## R. Independent authority validator

`validate_receipt_authority_bindings` accepts the receipt, raw evidence, registry and schema, independently recomputes expected values, and compares all 120 fields plus 12 source digest paths. Receipt-supplied expected SHA strings, cached helper digests and summary claims are never authority.

## S. Runtime/source crosscheck V2

The [V2 crosscheck](b2_t4_laq_r1_artifacts/raw_receipt_crosscheck_v2.json) passes 96 runtime relations, 12 identity paths, four artifact-digest groups and two composite groups; 30 source files are bound and unbound mandatory fields equal zero.

## T. Previous counterexample reproduction

The old supervisor PASS is source-faithfully reproduced without changing old files. The identical wrong SHA under R1 yields structural PASS but authority binding FAIL, source crosscheck FAIL and overall STOP. This closes the exact LAQ counterexample class.

## U. Valid-looking wrong-digest matrix

All 12 receipt digest/identity paths were replaced individually with a different syntactically valid lowercase 64-hex value. **12/12 STOP; unexpected PASS 0.** [Matrix](b2_t4_laq_r1_artifacts/valid_looking_wrong_digest_matrix.json).

## V. Wrong-source digest matrix

Each of the 12 paths was replaced by a valid SHA computed from a different authoritative artifact. **12/12 STOP; unexpected PASS 0.** [Matrix](b2_t4_laq_r1_artifacts/wrong_source_digest_matrix.json).

## W. Composite digest negative matrix

Production and config composites were tested for changed component, changed order representation, omitted component, unrelated substitution, and changed canonicalization. **10/10 STOP; unexpected PASS 0.** [Matrix](b2_t4_laq_r1_artifacts/composite_digest_negative_matrix.json).

## X. Reviewed SHA negative matrix

Valid-looking wrong SHAs for W2E, W2I, PW, PPQ-V2 helper, PPQ-V2 schema and normalizer all traverse the receipt-to-authority-to-supervisor path. **6/6 STOP; unexpected PASS 0.** [Matrix](b2_t4_laq_r1_artifacts/reviewed_sha_identity_negative_matrix.json).

## Y. Source-path substitution tests

W2E→PW, filesystem→PPQ candidate, and PPQ helper→unreviewed path substitutions all STOP. **3/3 STOP; unexpected PASS 0.** [Matrix](b2_t4_laq_r1_artifacts/source_path_substitution_matrix.json).

## Z. Retained structural/default tests

The immutable LAQ artifacts retain 57/57 requested field negatives, 38/38 default/absent-source cases, and 120/120 missing-field cases. R1 separately adds 120/120 type-preserving semantic field corruptions. These are reported as separate structural and semantic metrics. [Summary](b2_t4_laq_r1_artifacts/retained_structural_negative_summary.json).

## AA. Inherited 39-predicate semantic audit

The same 39 named RE5 Layer-A checks were replayed with predicate-specific corruptions. The filesystem case is a valid-looking wrong SHA. **39/39 STOP; unexpected PASS 0**, replacing LAQ's failed 38/39 audit. [Audit](b2_t4_laq_r1_artifacts/inherited_39_predicate_semantic_audit.json).

## AB. New V2 authority semantic audit

Eight identity authorities added beyond the historical predicate set were independently corrupted. **8/8 STOP; unexpected PASS 0.** [Audit](b2_t4_laq_r1_artifacts/new_v2_authority_semantic_audit.json).

## AC. Supervisor integration

R1 adjudication requires the complete frozen LAQ structural validator **and** raw runtime crosscheck **and** independent authority validator **and** Layer B. A deep copy before adjudication proves that the supervisor does not overwrite, fill, or reconstruct receipt fields.

## AD. Corrected R3 hypothetical positive

Immutable R3 raw evidence projected by the new helper passes structure, runtime crosscheck, authority binding, Layer A and preserved Layer B. This is hypothetical only and does not reclassify R3. [Evidence](b2_t4_laq_r1_artifacts/corrected_r3_projection_positive.json).

## AE. Original R3 negative

The original R3 receipt yields Layer A FAIL, Layer B PASS, overall STOP. Historical artifacts are unchanged. [Negative](b2_t4_laq_r1_artifacts/historical_r3_original_receipt_negative.json).

## AF. Authority-mutated R3 negatives

Starting with the corrected hypothetical receipt, every one of the 12 authority digest paths was individually replaced with a valid-looking wrong SHA. **12/12 STOP.** [Matrix](b2_t4_laq_r1_artifacts/authority_digest_mutated_r3_negative_matrix.json).

## AG. Layer-A vs Layer-B truth table

The four combinations retain the expected conjunction: only A PASS/B PASS produces PASS; A FAIL/B PASS, A PASS/B FAIL and A FAIL/B FAIL produce STOP. R1's A PASS definition includes source authority. [Table](b2_t4_laq_r1_artifacts/layer_a_layer_b_truth_table.json).

## AH. Source-binding coverage

Defined metrics: mandatory-field structural coverage 120/120; authority semantic equality 120/120; type-preserving semantic corruption 120/120; supervisor consumption 120/120. Authority semantic coverage is therefore 100% under this closed offline contract. This is not a generic “100% predicate coverage” claim. [Coverage](b2_t4_laq_r1_artifacts/source_binding_coverage.json).

## AI. Failure semantics

Pure qualification failure constructs no learner and poisons no runtime. Future post-mutation source-binding failure records `partial_update=true`, `route_poisoned=true`; pre-mutation failure records false/false. [Post-mutation](b2_t4_laq_r1_artifacts/post_mutation_failure_semantics.json), [pre-mutation](b2_t4_laq_r1_artifacts/pre_mutation_failure_semantics.json).

## AJ. Final freeze

Only after every qualification matrix passed, the R1 helper, runner, contract and registry were frozen. Final modes reject any SHA drift before projecting evidence. No source edit occurred after freeze.

## AK. Final positive dry run

Exactly **one** frozen positive offline dry run passed the complete pipeline with zero authority mismatches: immutable R3 evidence → projection → structure → runtime → source recomputation → authority validator → Layer A → preserved Layer B → hypothetical overall PASS. It was not rerun. [Result](b2_t4_laq_r1_artifacts/final_positive_dry_run_result.json).

## AL. Final decisive filesystem negative

After the positive, exactly **one** decisive control replaced the filesystem digest with 64 zeroes. Layer A FAIL, Layer B PASS, overall STOP, authority binding FAIL. [Result](b2_t4_laq_r1_artifacts/final_decisive_filesystem_negative_control.json).

## AM. Final multi-digest spot-check

Post-freeze corruption of production identity, config identity, W2E SHA, PPQ-V2 helper SHA and normalizer SHA produced **5/5 STOP**, unexpected PASS 0. These are negative controls, not additional positive runs. [Result](b2_t4_laq_r1_artifacts/final_multi_digest_spotcheck.json).

## AN. Protected-source preservation

Production transaction/adapter/environment, W2E/W2I/PW, PPQ-v1/v2, R3 normalizer/harness, failed LAQ identities/artifact tree, and full R3/R1/R2 evidence-tree digests match [before](b2_t4_laq_r1_artifacts/protected_source_identity_before.json) and [after](b2_t4_laq_r1_artifacts/protected_source_identity_after.json). Production, PPQ and historical modifications: zero.

## AO. LAQ-R1 candidate identities

The final [manifest](b2_t4_laq_r1_artifacts/laq_r1_source_identity_manifest.json) marks **CANDIDATE / AWAITING GPT REVIEW**:

- helper: `22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3`
- runner: `9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904`
- contract/schema: `677839292827599fdef36128c05deaa96f0e9cb1f76e3975f338259231f68956`
- registry: `3f79dfe33e252c13b13fccb26a9f476b00aeb72bf73eae2c2fff5684a7247751`
- final positive result: `b2f25a8df30142bdbe89787042492ab36920c8a95e7db453d50e63a83087b5c9`

## AP. Future RE6-R4 integration plan

The [design-only plan](b2_t4_laq_r1_artifacts/future_re6_r4_integration_plan.json) requires a fresh namespace, fresh raw evidence, run-specific exact-path registry, no defaults, independent digest recomputation, complete Layer-A subgates, unchanged PPQ-V2/W2E/W2I/PW, independent EP-Q Layer B, one worker/zero retry, and no R3 learner reuse. RE6-R4 was not created or run.

## AQ. Exact execution counts

Approved-interpreter identity checks: 1. Approved-interpreter Python invocations: 12 total: two `py_compile` commands (three file compilations: helper twice, runner once), six pure diagnostic/prototype/integrity checks, one qualification invocation, exactly one final positive invocation, exactly one final negative/spot-check invocation. Authority-bound fields 120; receipt digest/identity fields 12; valid-looking wrong-digest 12/12 STOP; wrong-source 12/12; composite 10/10; reviewed SHA 6/6; path substitution 3/3; retained structural 57/57 + 38/38 + 120/120; inherited semantic 39/39; new V2 authority 8/8; per-field semantic 120/120. Formal supervisor/worker, CUDA, AppLauncher, environment, reset, learner construction/mutation, physical steps, checkpoint, public activation, evaluation/playback and RE6-R4 attempts: all 0. Production/PPQ/historical R3/failed LAQ modifications: 0. Git add/commit/push: 0/0/0.

## AR. Retained nonclaims

This does not issue GPT REVIEW PASS, authorize RE6-R4, repair or unpoison R3, make its learner reusable, establish checkpoint continuation, training quality, convergence, long/paper-scale training, public-route readiness, evaluation, or playback. The public route remains DORMANT/BLOCKED.

## AS. Final classification

`PHASE-B2-T4-LAQ-R1-RAW-RECEIPT-AUTHORITY-BINDING-QUALIFIED-AWAITING-GPT-REVIEW`. Layer-A structural/presence and offline semantic source binding are qualified as a candidate awaiting independent review. Historical LAQ stays STOP; historical R3 stays poisoned STOP; RE6-R4 stays NOT AUTHORIZED. [Final result](b2_t4_laq_r1_artifacts/final_result.json).

### Primary authority-binding table

| Receipt field | Category | Authoritative source | Computation | Semantic equality checked? | Negative corruption PASS? |
|---|---|---|---|---|---|
| `source_authority_digest` | artifact digest | exact R3 static authority | SHA256(raw bytes) + content links | Yes | Yes |
| `filesystem_precondition_digest` | artifact digest | exact filesystem precondition | SHA256(raw bytes) + content predicates | Yes | Yes |
| `ppq_v2_candidate_sha256` | artifact digest | exact candidate receipt | SHA256(raw bytes) + readback | Yes | Yes |
| `production_identity_digest` | composite | three fixed production paths | canonical component-SHA map | Yes | Yes |
| `config_authority_digest` | config artifact | process-config object | canonical config JSON | Yes | Yes |
| `config_identity_digest` | config contract | explicit PPQ cadence | canonical config JSON | Yes | Yes |
| W2E selector SHA | reviewed source | selector `.py` | SHA256(raw bytes) | Yes | Yes |
| W2I binding SHA | reviewed artifact | manifest + referenced files | SHA256(raw bytes) | Yes | Yes |
| PW helper SHA | reviewed source | helper `.py` | SHA256(raw bytes) | Yes | Yes |
| PPQ-V2 helper SHA | reviewed source | helper `.py` | SHA256(raw bytes) | Yes | Yes |
| PPQ-V2 schema SHA | reviewed artifact | schema JSON + generated schema | SHA256(raw bytes) | Yes | Yes |
| normalizer SHA | frozen source | normalizer `.py` | SHA256(raw bytes) | Yes | Yes |
| R1 helper/schema/registry | external self identity | frozen candidate files | external SHA256(raw bytes) | Yes | Yes, pre-run freeze gate |

### Primary semantic negative table

| Group | Fields/cases | Expected STOP | Actual STOP | Unexpected PASS |
|---|---:|---:|---:|---:|
| Valid-looking wrong digest | 12 | 12 | 12 | 0 |
| Wrong-source digest | 12 | 12 | 12 | 0 |
| Composite digest corruption | 10 | 10 | 10 | 0 |
| Reviewed SHA corruption | 6 | 6 | 6 | 0 |
| Path/source substitution | 3 | 3 | 3 | 0 |
| 39 inherited predicates | 39 | 39 | 39 | 0 |
| New V2 authorities | 8 | 8 | 8 | 0 |

## AT. GPT-review handoff

Independently inspect the fixed-path registry, raw-byte and semantic artifact checks, full 120-field equality, 39 inherited and eight new-authority audits, pre-final identity freeze, one positive run, one decisive filesystem control, five final digest controls, and protected-source comparison. Do not launch RE6-R4, reuse R3's learner, alter historical R3/LAQ, modify PPQ-V2, start AppLauncher/environment/learner, perform checkpoint I/O, activate the public route, or begin long training. Commit remains the user's decision.
