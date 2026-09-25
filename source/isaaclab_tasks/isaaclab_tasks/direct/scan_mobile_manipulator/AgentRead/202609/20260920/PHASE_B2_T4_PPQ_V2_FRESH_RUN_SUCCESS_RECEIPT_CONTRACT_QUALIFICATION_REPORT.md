# Phase B2-T4-PPQ-V2 — Fresh-run success-receipt contract qualification

Date: 2026-09-20. Classification: `PHASE-B2-T4-PPQ-V2-FRESH-RUN-SUCCESS-RECEIPT-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`. This is a **pure/static/offline candidate**, not an independent GPT REVIEW PASS or authorization to start RE6-R3.

## A. Repository authority

The read-only starting audit found branch `main`, HEAD/origin/main/merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`, and the pre-existing 359 staged monthly-migration paths. The staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab` matched. Full porcelain was inspected before source edits; [repository authority](b2_t4_ppq_v2_artifacts/repository_authority.json) records a hashed full `-uall` porcelain snapshot immediately before qualification-artifact writes. No index operation or commit occurred.

## B. Reviewed starting authority

B2-R0–R7, B2-T0–T3, and T4-NR/SR/ZD/EP-Q/PW/W2E/W2I/PPQ-v1 remain GPT REVIEW PASS / CLOSED in their reviewed scopes. RE5 and RE6-R1 remain reviewed historical poisoned STOPs; RE6 and RE6-R2 remain pre-runtime STOPs, not poisoned. [Authority snapshot](b2_t4_ppq_v2_artifacts/reviewed_starting_authority.json).

## C. PPQ-v1 preservation

The reviewed v1 helper SHA `1bc419e96fe095ef15b70483abbbacca57580345d803d6ce83b211e68054352d` and schema SHA `9423742d525acb154c789c4b99922cc366bc596decef1be783c0ac1ffc98e5f6` match. All 26 v1 artifact paths and hashes matched the in-phase before/after snapshot; none was rewritten. [Preservation](b2_t4_ppq_v2_artifacts/ppq_v1_preservation.json).

## D. Historical RE6-R1 preservation

The 7,331 immutable historical artifact files (1,938,776,606 bytes) matched the prior per-file manifest before and after qualification and after the final dry run. The historical harness SHA `858656975abef50adf6a143fe7f6bc68731756d2ad6378430acc6b9e3f3d049c` matched. Its poisoned learner was not constructed, resumed, or reused. Historical RE6-R1 stays GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED.

## E. Historical RE6-R2 preservation

All eight diagnostic artifact SHA-256 values matched the recorded starting set. RE6-R2 stays GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED, classification `PHASE-B2-T4-RE6-R2-PPQ-FRESH-SUCCESS-RECEIPT-CONTRACT-GAP-REVIEW-STOP`. No harness or formal attempt was created.

## F. RE6-R2 contract-gap reproduction

The frozen v1 validator requires RE6-R1/`STOP-POISONED`, rejects mandatory new direct fields, fixes W2 29/12 and tx12→15→16, fixes TASK_COMPLETED=22/coverage=11, and requires an RE6-R1-specific PW schema. These source-backed conflicts are recorded in the [gap reproduction](b2_t4_ppq_v2_artifacts/re6_r2_contract_gap_reproduction.json), alongside the reviewed [RE6-R2 STOP report](PHASE_B2_T4_RE6_R2_PPQ_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md).

## G. PPQ-v1 scope boundary

V1 remains valid only as the reviewed historical RE6-R1 offline replay contract. V2 does not edit, overwrite, relabel, or retroactively expand v1. Its historical-evidence positive is explicitly hypothetical and never consumes the poisoned historical success/failure receipt as fresh success.

## H. PPQ-V2 design objective

The new `b2_t4_ppq_fresh_run_success_receipt_v2` separates immutable reviewed identities, candidate V2 identities, current-campaign normalized observations, and relations required for success. [Contract](b2_t4_ppq_v2_artifacts/fresh_receipt_contract_v2.json), [helper](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py), and [qualification runner](../../../../../../../../scripts/environments/test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract.py) are test-side only.

## I. Fixed-vs-derived field classification

| Field | Class | Authority | Historical fixed value allowed? |
|---|---|---|---|
| W2E selector SHA | frozen identity | reviewed W2E/W2I | Yes, identity only |
| W2I binding SHA | frozen identity | reviewed W2I | Yes, identity only |
| PPQ-V2 helper/schema SHA | candidate identity | this frozen V2 candidate | Yes after candidate freeze |
| source phase | caller-bound | fresh attempt | No historical fixed phase |
| W2 candidates/valid/selected | runtime-derived | exact reviewed selector output | No |
| TASK_COMPLETED/coverage | runtime-derived | normalized lifecycle evidence | No |
| terminal count | runtime-derived | normalized terminal evidence | No |
| transaction count | config-derived | this intended 160-tx formal config | Yes for this config, not RE6-R1 provenance |
| physical count | relational | T × transactions | No historical provenance |
| bridge count | relational | transactions − 1 | No historical provenance |

## J. Fresh source-phase contract

The closed allowed family is `B2-T4-RE6-R3`, `B2-T4-RE6-R3-SYNTHETIC`, and `B2-T4-PPQ-V2-HISTORICAL-FIXTURE`; receipt source must equal the caller's explicit expected phase. The historical `B2-T4-RE6-R1` phase is not a fresh success phase. Two valid fresh caller phases passed; an actual-vs-expected mismatch STOPped. [Phase contract](b2_t4_ppq_v2_artifacts/fresh_source_phase_contract.json).

## K. Direct identity contract

The flat closed receipt directly contains contract/source/run/PID, W2E version/SHA, W2I SHA, PPQ-V2 helper/schema SHA, PW SHA, and production/config digests. The helper checks its own raw-byte SHA, generated schema digest, reviewed W2E callable source SHA, W2I manifest bytes, PW helper bytes, three production source hashes aggregated into a digest, and the caller's config digest. Missing/wrong direct identities fail. [Identity contract](b2_t4_ppq_v2_artifacts/fresh_identity_contract.json).

## L. W2E fresh contract

V2 invokes the exact reviewed `reconcile` function; accepts candidate≥1 and 1≤valid≤candidate; requires selected equality with deterministic first selector-valid inventory row and with the provisional W2 witness; checks all five W2 layers, ownership clear, qualified bridge, exact identity/generation, and claim/completion/reopen ordering. Same-transaction completion→reopen is allowed only when physical-step order increases, consistent with reviewed W2E. No historical candidate count or witness coordinates are built in. [W2 contract](b2_t4_ppq_v2_artifacts/fresh_w2_contract.json).

## M. Task-progress fresh contract

The normalized current-campaign task observations are copied to the receipt and must satisfy TASK_COMPLETED≥1, completion delta>0, coverage>0. No historical 22/11 requirement remains. The synthetic values are fixture data, not measured RE6-R3 runtime results. [Task contract](b2_t4_ppq_v2_artifacts/fresh_task_progress_contract.json).

## N. Terminal fresh contract

The receipt requires terminal/autoreset≥1, canonical terminal-reason-priority check true, and a post-autoreset learned transaction true; no historical terminal count is fixed. The historical fixture derives its terminal count and W5 priority assertion from retained W5/count evidence. Synthetic fixtures supply explicit normalized assertions; future formal normalization must bind them to real terminal ledgers. [Terminal contract](b2_t4_ppq_v2_artifacts/fresh_terminal_contract.json).

## O. PW fresh contract

The generic `b2_t4_ppq_fresh_campaign_pw_result_v2` requires matching run/transaction identity, critic and actor/factor actual counts equal transaction count × source-derived cadence (41/4 for this frozen config), and five fault counters zero. Historical RE6-R1 PW records were reverified with the reviewed PW helper for the compatibility fixture; its historical schema name is not a V2 requirement. Synthetic PW outputs test the generic interface, not real fresh persistence. [PW contract](b2_t4_ppq_v2_artifacts/fresh_pw_contract.json).

## P. Campaign invariants

For the explicitly qualified intended config, expected transactions=160 and T=2 imply 320 physical transitions, 160 production S10 and ledger rows, 159 contiguous qualified bridges, and tx161 not started. The helper checks all 160 transaction rows, bridge indices and update-ID continuity, and cross-binds W2E transaction/bridge input to the campaign inventory. [Invariants](b2_t4_ppq_v2_artifacts/fresh_campaign_invariants.json).

## Q. W1-W7 contract

All seven statuses must PASS, W2E is independently recalculated by the exact selector, and W7 qualified count must equal the campaign transaction count. Canonical success aliases are not published until the durable receipt is read back, digest-checked and schema-revalidated. [Witness contract](b2_t4_ppq_v2_artifacts/fresh_witness_contract.json).

## R. Learner contract

The receipt carries actor/critic backward and optimizer-step planned/observed counts, nonzero/zero-effective critic classes, ValueNorm expected/actual updates, Adam/ValueNorm continuity and numerical health. The validator enforces observed=planned, critic classes sum to critic plan, and ValueNorm equals critic updates. It does not require historical actor 165 or critic 1600. [Learner contract](b2_t4_ppq_v2_artifacts/fresh_learner_contract.json).

## S. Route-health contract

Success requires `campaign_status=SUCCESS`, `partial_update=false`, `route_poisoned=false`. Any poisoned or partial flag invalidates the receipt. These flags in the historical compatibility fixture are explicitly hypothetical V2 candidate flags, not the actual RE6-R1 attempt state. [Route contract](b2_t4_ppq_v2_artifacts/fresh_route_health_contract.json).

## T. Forbidden-action contract

The direct receipt fields `checkpoint_io_count`, `public_activation_count`, and `evaluation_playback_count` must each be zero. The qualification itself performed none of those actions.

## U. Explicit dependency contract

The helper accepts normalized campaign evidence, exact W2E selector, W2I path, fresh PW verifier, expected phase, formal config, production source paths, PW helper path, identity map, explicit writer/reader and output namespace. No mandatory `engine['_...']` lookup exists; a hidden engine key in evidence is rejected. [Dependency contract](b2_t4_ppq_v2_artifacts/fresh_dependency_contract_v2.json).

## V. PPQ-V2 helper architecture

`build_receipt` reconciles ledgers/PW, invokes W2E, adjudicates witness/route relations, then constructs and schema-validates the flat receipt. `finalize_campaign` writes it durably, reads it back, checks payload/digest, revalidates schema, then publishes seven canonical aliases. `failure_record` is a separate durable failure-path primitive with explicit mutation flags. No Isaac, CUDA, HARL learner, or production import is used.

## W. Success receipt schema v2

The [closed schema](b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json) lists every direct field and rejects unknown fields, missing fields, wrong Python types and nonfinite values. Its raw-byte SHA is `0742a9a0ed44cb1f3410fae8885e348f7a40b7dbc35ac089ca6cf920d89126d5`.

## X. Publication ordering

All three positive traces and the final durable trace show: reconcile → adjudicate → build → schema validate → durable write → readback → digest validate → schema revalidate → canonical W1–W7 publication. Premature publication and stale provisional-witness promotion are separate expected STOP cases.

## Y. Positive fixture 1

The immutable RE6-R1 completed ledgers, W2E inventory, W1–W7 observations and reverified PW records were used only as synthetic historical-evidence compatibility input, with an explicit fresh-fixture phase. It accepted 29/12, env1/robot1/task10, tx12→15→16, 22 completed tasks, coverage 11, terminals 2 because those values came from evidence. It did **not** reclassify or unpoison RE6-R1. [Fixture result](b2_t4_ppq_v2_artifacts/positive_fixture_historical_evidence.json).

## Z. Positive fixture 2

Synthetic fresh variant 1 accepted 1/1 W2 candidate/valid, env1/robot0/task0, tx1→2→3, TASK_COMPLETED 3, coverage 2, terminal 1. [Fixture result](b2_t4_ppq_v2_artifacts/positive_fixture_fresh_variant_1.json).

## AA. Positive fixture 3

Synthetic fresh variant 2 accepted 2/1 W2 candidate/valid, env2/robot0/task1, tx1→3→4, TASK_COMPLETED 7, coverage 5, terminal 3. [Fixture result](b2_t4_ppq_v2_artifacts/positive_fixture_fresh_variant_2.json).

## AB. Positive matrix

| Fixture | Source phase | W2 candidates/valid | Selected witness | TASK_COMPLETED | Coverage | Terminals | Result |
|---|---|---:|---|---:|---:|---:|---|
| Historical-evidence compatibility | `B2-T4-PPQ-V2-HISTORICAL-FIXTURE` | 29/12 | env1/robot1/task10, tx12→15→16 | 22 | 11 | 2 | PASS |
| Fresh synthetic 1 | `B2-T4-RE6-R3-SYNTHETIC` | 1/1 | env1/robot0/task0, tx1→2→3 | 3 | 2 | 1 | PASS |
| Fresh synthetic 2 | `B2-T4-RE6-R3-SYNTHETIC` | 2/1 | env2/robot0/task1, tx1→3→4 | 7 | 5 | 3 | PASS |

Total 3/3 PASS. [Full positive matrix](b2_t4_ppq_v2_artifacts/positive_matrix.json).

## AC. Negative matrix

| Group | Cases | Expected STOP | Actual STOP | Unexpected PASS |
|---|---:|---:|---:|---:|
| Source/identity/hidden dependency (A–P, BS, BU–BV) | 19 | 19 | 19 | 0 |
| W2 semantics (Q–Y) | 9 | 9 | 9 | 0 |
| Task/terminal (Z–AD, BT) | 6 | 6 | 6 | 0 |
| Campaign counts (AE–AJ) | 6 | 6 | 6 | 0 |
| PW (AK–AQ) | 7 | 7 | 7 | 0 |
| Witnesses (AR–AW) | 6 | 6 | 6 | 0 |
| Learner/returns (AX–BD) | 7 | 7 | 7 | 0 |
| Route/forbidden (BE–BI) | 5 | 5 | 5 | 0 |
| Persistence/publication/schema (BJ–BR) | 9 | 9 | 9 | 0 |
| **Total** | **74** | **74** | **74** | **0** |

71 cases use explicit `PPQV2Stop`; the missing-selected-input case raises a fail-closed `TypeError`, and injected writer/readback failures raise `OSError`. Each is an expected STOP; none publishes canonical success. [Per-case reasons](b2_t4_ppq_v2_artifacts/negative_matrix.json).

## AD. Historical-value decoupling

Both synthetic variants passed with W2, task, coverage and terminal values different from the historical 29/12, tx12→15→16, 22/11/2. [Decoupling](b2_t4_ppq_v2_artifacts/historical_value_decoupling.json).

## AE. Source-phase decoupling

`B2-T4-RE6-R3-SYNTHETIC` and explicitly expected `B2-T4-RE6-R3` both passed; a mismatch stopped. `B2-T4-RE6-R1` is neither required nor allowed for fresh success. [Decoupling](b2_t4_ppq_v2_artifacts/source_phase_decoupling.json).

## AF. PW schema decoupling

V2 requires its generic PW result version, not the RE6-R1 reconciliation schema name; the historical PW records are only a verified fixture source. [Decoupling](b2_t4_ppq_v2_artifacts/pw_fresh_contract_decoupling.json).

## AG. Direct identity validation

All mandatory direct SHA/digest fields are schema-recognized; negative cases E–P and BU–BV cover missing/wrong direct identities. The helper binds actual source bytes and config to supplied authority. [Validation](b2_t4_ppq_v2_artifacts/direct_identity_field_validation.json).

## AH. Post-mutation failure contract

A simulated post-mutation failure produces a durable [failure record](b2_t4_ppq_v2_artifacts/failure_record_simulation/failure_record_v2.json) with `partial_update=true`, `route_poisoned=true`, no success receipt and no canonical success witnesses. [Contract result](b2_t4_ppq_v2_artifacts/post_mutation_failure_contract.json).

## AI. Pre-mutation failure contract

The pure pre-mutation simulation produces `false/false`, no success receipt and no canonical success witnesses. It is an in-memory qualification of failure semantics, not a formal process receipt. [Contract result](b2_t4_ppq_v2_artifacts/pre_mutation_failure_contract.json).

## AJ. Final frozen fresh dry run

After qualification and candidate source freeze, exactly one durable dry run used synthetic fresh variant 2 under [final_dry_run](b2_t4_ppq_v2_artifacts/final_dry_run/). Its receipt SHA is `b1ecce2cba3ce6b655fa7fa0613ae0ca55baf920637143601aefd42311e0696e`; all seven canonical files were published after receipt readback/digest/schema gates. No historical fixture was used as the sole final input. [Result](b2_t4_ppq_v2_artifacts/final_dry_run_result.json).

## AK. Protected source preservation

The three production sources, reviewed W2E/W2I/PW, PPQ-v1 helper/schema, RE6-R1 harness, all historical RE6-R1 artifacts, all eight RE6-R2 diagnostics and 26 PPQ-v1 artifacts matched [before](b2_t4_ppq_v2_artifacts/protected_source_identity_before.json) and [after](b2_t4_ppq_v2_artifacts/protected_source_identity_after.json). A further read-only post-final check found the same identities. Production semantic edits: 0.

## AL. PPQ-V2 helper identity

The [candidate manifest](b2_t4_ppq_v2_artifacts/ppq_v2_source_identity_manifest.json) freezes helper SHA `115d681d5e8473aa171e6232b6beca8c985139a58926d6d15850c2940785f903`, runner SHA `134a8c290949385854a4bf4e0cea11748f447a94fba503b4c6f2454118ab92dc`, schema SHA `0742a9a0ed44cb1f3410fae8885e348f7a40b7dbc35ac089ca6cf920d89126d5`, and final-result SHA `6ca9c2f9bb36d8c5915d34e6017a3a4d233d0550b9645d51160cf4b4bf2c8ef2`. All are **CANDIDATE / AWAITING GPT REVIEW**, not reviewed identities.

## AM. Future RE6-R3 integration plan

The [design-only plan](b2_t4_ppq_v2_artifacts/future_re6_r3_integration_plan.json) specifies a future fresh harness's explicit inputs, current-ledger normalization, `B2-T4-RE6-R3` phase, reviewed W2E/PW authorities, PPQ-V2 Layer A, EP-Q Layer B, failure record before env/App close, fresh namespace and historical preservation. It creates no RE6-R3 harness or worker and imports no PPQ-v1 success helper as formal authority.

## AN. Exact execution counts

Approved-interpreter checks: 1. `py_compile` invocations: 3 (both changed Python files each time). Other Python contract/static invocations: 13, including one pre-artifact fixture-shape error corrected before qualification and one corrected path-set-hash calculation. Final qualification: 3 positive fixtures/3 PASS; 74 negative cases/74 STOP/0 unexpected PASS; one simulated post-mutation and one pre-mutation failure case; exactly one final durable fresh-fixture dry run. Formal supervisors/workers: 0/0; CUDA probes/AppLauncher/environments/resets/physical steps/learner constructions/learner mutations: all 0; RE6-R3 attempts, checkpoint I/O, public activation, evaluation/playback: all 0; production/PPQ-v1/historical RE6-R1/historical RE6-R2 modifications: 0/0/0/0; git add/commit/push: 0/0/0. The only prior in-task failed `check` occurred before qualification artifacts and before the one final durable run.

## AO. Retained nonclaims

Synthetic progress, terminal and PW observations are fixture inputs, not measured RE6-R3 runtime values. The offline contract cannot establish a real fresh-run receipt, actual runtime normalization correctness, learner training quality, checkpoint continuation, long/paper-scale training, evaluation, public readiness, or EP-Q Layer B for RE6-R3. Historical RE6-R1's `partial_update=true`/`route_poisoned=true` and poisoned learner remain immutable.

## AP. Final classification

`PHASE-B2-T4-PPQ-V2-FRESH-RUN-SUCCESS-RECEIPT-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`. PPQ-v1 remains GPT REVIEW PASS / CLOSED for historical offline scope; RE6-R1 and RE6-R2 retain their reviewed STOP states. The fresh-run receipt blocker is **QUALIFIED OFFLINE / AWAITING GPT REVIEW**. RE6-R3 remains **NOT AUTHORIZED**. Public route remains DORMANT / BLOCKED.

## AQ. GPT-review handoff

Independently review V2 helper/runner/schema identities, whether the normalized fresh-evidence interface and synthetic fixtures sufficiently bind task/terminal/PW aggregates, the 74 per-case STOPs, publication order, failure records and protected-source manifests. Do not self-issue GPT REVIEW PASS from this report; do not start RE6-R3, AppLauncher, environment, learner, checkpoint, public route, evaluation/playback or long training. Commit remains the user's decision after review.
