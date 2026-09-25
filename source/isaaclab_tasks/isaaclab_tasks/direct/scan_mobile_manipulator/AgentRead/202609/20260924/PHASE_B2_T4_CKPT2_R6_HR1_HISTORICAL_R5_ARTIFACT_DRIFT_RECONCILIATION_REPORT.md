# Phase B2-T4 CKPT2-R6-HR1 Historical R5 Artifact Drift Reconciliation Report

Classification:

`PHASE-B2-T4-CKPT2-R6-HR1-INVENTORY-ALGORITHM-DRIFT-RECONCILED-AWAITING-GPT-REVIEW`

This was a pure, offline, read-only investigation of the historical R5 root. It launched no AppLauncher, Isaac Sim, environment, CUDA operation, learner, transaction, or checkpoint operation. No R5/R6 historical file was modified.

## A. R6 STOP CONTEXT

R6 remains historical as `PHASE-B2-T4-CKPT2-R6-STOP-PRE-RUNTIME-HISTORICAL-R5-DRIFT`. It stopped before the R6 pure child and before Process A because the expected 42-file aggregate `d9d940c8...` did not equal the R5 `_inventory()` result `21dd70b5...`. R6 retry and R7 remain unauthorized.

## B. ORIGINAL R5 INVENTORY AUTHORITY

The value `d9d940c8d10ea30945d438ec9b2c10cfca9e028de3c3993bc447dee41c68a8c1` was created during R6 preparation by an ad-hoc read-only command preserved in the Codex session log at JSONL lines 40963 and 40966, ordinals 40962 and 40965. It was not emitted by the R5 harness and no per-file manifest was saved with it.

The command constructed 42 sorted rows with `path`, `bytes`, and content `sha256`, serialized them with compact, key-sorted ASCII JSON, then appended a Python string literal whose actual terminal bytes were `5c6e`: backslash plus lowercase `n`.

## C. INVENTORY ALGORITHM

The R5 harness symbol `_inventory` is in `scripts/environments/test_assignment_phase_b2_t4_ckpt2_r5_real_fresh_process_checkpoint_continuation.py`, lines 108-114, source SHA-256 `e6546bdae034a7abb18d1ad70e16a4e2f5eab897251ba4561acf2e5d604fd039`.

Both algorithms use:

- `sorted(root.rglob("*"))`, files only;
- root-relative POSIX paths;
- byte size and SHA-256 of file content;
- compact `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`;
- no mtime, creation time, file mode, locale, absolute path, or self-manifest entry.

They differ only at the serialized inventory terminator:

| Algorithm | Terminal bytes | Meaning | Encoded bytes | Digest |
|---|---|---|---:|---|
| R6-preparation ad-hoc lock | `5c6e` | literal `\n` | 5654 | `d9d940c8d10ea30945d438ec9b2c10cfca9e028de3c3993bc447dee41c68a8c1` |
| R5 harness `_inventory()` | `0a` | one LF byte | 5653 | `21dd70b567c737efcd1dfe776ea4a1db0370acfbca3988db26a1dd392d4dc609` |

## D. CURRENT DIGEST REPRODUCTION

The current 42 rows serialize to a 5652-byte body with SHA-256 `18d5c4fee2800abe5dff09cb357e776041b2c247eb8b36e123634659b8ca7244`.

Appending `5c6e` exactly reproduces `d9d940c8...`; appending `0a` to the same body exactly reproduces `21dd70b5...`. No approximate algorithm, metadata, alternate path set, or changed input row is required.

## E. LOCK-TIME INVENTORY RECOVERABILITY

Classification: `AGGREGATE_ONLY`.

The aggregate command, output, count, timestamp, and digest are recoverable. A historical per-file manifest was not persisted, so old per-file sizes and hashes below are explicitly `UNAVAILABLE`; current hashes are not relabeled as historical hashes. The complete current row set nevertheless reproduces the old aggregate under the exact recorded old algorithm.

## F. FILE-BY-FILE RECONCILIATION

No byte-changed or metadata-only file is established. Individual old byte identity remains unavailable for all 42 rows; the aggregate mismatch is fully reproduced as an algorithm-only terminator difference.

| Path | Old SHA | Current SHA | Byte equal | Authority class | Impact |
|---|---|---|---:|---|---|
| `actor_plan_count_authority_inventory.json` | UNAVAILABLE | `32db3a31221725645bd180e798d115bb7e61d9537dd2c5c2963970c2e3b5a313` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `actor_plan_count_negative_matrix.json` | UNAVAILABLE | `49709200c2733dc170bbcff220e52885cb994f196e7547982d8bc9a36b9f1745` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `actor_plan_dynamic_positive_matrix.json` | UNAVAILABLE | `53047ed79b7c3ddaefb28190213c4bab4249fbeb1a2ac414c337f38b80c28281` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `ckpt1_preservation.json` | UNAVAILABLE | `e7c389e3ed4ccbe45c000905164f0d718fc0d0cf819d800557f1965c4cdfece9` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `ckpt2_r5_pre_runtime_freeze.json` | UNAVAILABLE | `8207d759d14a24acc75c831e2c55949ccf8e9f16e8d24ad8b94a9b4e1a082438` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `ckpt2_r5_preflight.json` | UNAVAILABLE | `96ac0f39b48d34a3f8941b22c164ddfc4b62532ab07bd828469fcb74d2c090f1` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `ckpt2_r5_run_identity.json` | UNAVAILABLE | `0c9740b4d612b3156a5320e7d2b3fd64473310c071ac6d218d659a9a3984599e` | NOT INDIVIDUALLY PROVABLE | OTHER | No byte change established; aggregate difference is algorithm-only |
| `clean_interpreter_baseline.json` | UNAVAILABLE | `7f3680f6aa901dae589cd6ed0c9fcb28f2e96c5e15dc9453ef1f33063228b667` | NOT INDIVIDUALLY PROVABLE | DIAGNOSTIC | No byte change established; aggregate difference is algorithm-only |
| `failure_receipt.json` | UNAVAILABLE | `0adb1b716d607ae755c8bb71ae433371fc504338657318ddfbd3d2c761acbd91` | NOT INDIVIDUALLY PROVABLE | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `final_stop_adjudication.json` | UNAVAILABLE | `67d1459e41f83f630429d4597819691387a31e23de370ff4f02b5b484000ba31` | NOT INDIVIDUALLY PROVABLE | FINAL_ADJUDICATION_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `historical_actor_adam_plan_consistency.json` | UNAVAILABLE | `62e8448c903744c017f35f62858a5f2be78c44497b9395a19b1e8fbc766c6a8a` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `historical_ckpt2_preservation.json` | UNAVAILABLE | `fcd77c938371483ab5df8e6fba909f12828a13be0ff99044aee3a353571f7e55` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `historical_ckpt2_r1_preservation.json` | UNAVAILABLE | `b4a73dedf1f90167a0046f571638e36145f4d2288f0c6bd945ee3f8d8a141b4c` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `historical_ckpt2_r2_preservation.json` | UNAVAILABLE | `4a77ad5a7d11c89928b8cd7211c143a6ef5f586d9a61aee1ca14ae8f86be1166` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `historical_ckpt2_r3_preservation.json` | UNAVAILABLE | `94a2017acab0cdcad4e9e369fca1ba496137b9fc3add63467ba61a38b2e417f5` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `historical_ckpt2_r4_preservation.json` | UNAVAILABLE | `3e005d4988d20b981b5494261498072e79a95b51243ba320dd5169f1e100e69d` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `historical_dynamic_actor_plan_consistency.json` | UNAVAILABLE | `941dfa10db0480d55ee43748c1e3931b0fbe927e51f4b46525f51b099f5dd553` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `inherited_contract_preservation.json` | UNAVAILABLE | `9b21d34b2ea4ab352925ceb79b5b99e5cd6e4f65cec7109f5682cd4ecbaf02d5` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `parent/parent_process_inventory.json` | UNAVAILABLE | `cbfbfc4af7b4a11bd590f6c73e495785614fe86e8cf9e4e7a0ec8d5eaa145461` | NOT INDIVIDUALLY PROVABLE | PROCESS_SHUTDOWN_BOOKKEEPING | No byte change established; aggregate difference is algorithm-only |
| `pre_runtime_harness_repair_log.json` | UNAVAILABLE | `e5a50f85c3871b528e4510c5ea5ab0b02ba285124570ba138e08f4587712386d` | NOT INDIVIDUALLY PROVABLE | DIAGNOSTIC | No byte change established; aggregate difference is algorithm-only |
| `preflight_ckpt1_pure.json` | UNAVAILABLE | `a383d829196bfaed5ef95bc6b501c1748241aabd8267834d38933c60d43b72ae` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `process_a/core_failure.json` | UNAVAILABLE | `d0988fe99517145cdd88542d7fb58f4bee0e2f71574abf2c24715188413da3aa` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/core_process_config_authority.json` | UNAVAILABLE | `7c3cbb68e38de90657a2585ad2c464ac116d9e04e6d6e9990d56b9dbc70e9535` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/core_runtime_checkpoints.jsonl` | UNAVAILABLE | `63509b08a3afa753013f5a3d8521de5cf8331689159b95263746e2f79335d199` | NOT INDIVIDUALLY PROVABLE | DIAGNOSTIC | No byte change established; aggregate difference is algorithm-only |
| `process_a/core_tx1_failure.json` | UNAVAILABLE | `d0988fe99517145cdd88542d7fb58f4bee0e2f71574abf2c24715188413da3aa` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/core_tx1_rollout_decision_evidence.json` | UNAVAILABLE | `5ae871957284a85ca58d08738dee436966f6a695d4353bd7416c5563baa308fe` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/environment_creation.json` | UNAVAILABLE | `7fc469ecd6726ff0f6997366bc09d512b3e1d49857de2e340ad5babe09c521fa` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `process_a/failure_receipt.json` | UNAVAILABLE | `aca17ce11cc5d040e0618326b928a789579cfb134bc04b54288097ea713c1a62` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/initial_state.json` | UNAVAILABLE | `e1849d175e1d792277a315ab2812be3cae19ad2d7a1f394398dcfd577788c092` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/runtime_identity.json` | UNAVAILABLE | `4b4501b67ecb5fef0ec69e19c45a5fdcfd3bce183b94254706b37a9807456bad` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a/shutdown_result.json` | UNAVAILABLE | `b7aecae22191e5a8b86bb99a6600bc90eb1bfb71132fe92ab0d18cb8e4fa8b1a` | NOT INDIVIDUALLY PROVABLE | PROCESS_SHUTDOWN_BOOKKEEPING | No byte change established; aggregate difference is algorithm-only |
| `process_a_environment_creation.json` | UNAVAILABLE | `7fc469ecd6726ff0f6997366bc09d512b3e1d49857de2e340ad5babe09c521fa` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a_environment_registration.json` | UNAVAILABLE | `44d0921abd5f1c0ffab7aa85203785321252d48539a850af5eadb4bdc12eb10d` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a_parent_adjudication.json` | UNAVAILABLE | `4e751596637e3bdf110de8c63c9d638cddd6f40986d279992bfde7b6e3ee03ba` | NOT INDIVIDUALLY PROVABLE | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_a_real_package_identity.json` | UNAVAILABLE | `94b332d75cd3f338f6c193135580ac120a7dac73e7042554d84d4819dff158b8` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_b_launch_gate.json` | UNAVAILABLE | `0816de03c8f41f3b09f3e63f214c3178a4eb570f210fb0a7f6869e8bc5edced4` | NOT INDIVIDUALLY PROVABLE | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `process_quiescence.json` | UNAVAILABLE | `1f775dbeb6d220704ebbfeedb5cb7a49c449164c5aa754aace97260ab81810ab` | NOT INDIVIDUALLY PROVABLE | PROCESS_SHUTDOWN_BOOKKEEPING | No byte change established; aggregate difference is algorithm-only |
| `pure_qualification_result.json` | UNAVAILABLE | `f331e8ada258e61e9fa39c98635818ce96d76140af7bb5074edbe486f9fc8800` | NOT INDIVIDUALLY PROVABLE | CORE_SEMANTIC_AUTHORITY | No byte change established; aggregate difference is algorithm-only |
| `pure_runtime_process_isolation.json` | UNAVAILABLE | `1117886d762c3c663a8bb223f638911b24d9363ac6353fa7aa0d0211943bf0ab` | NOT INDIVIDUALLY PROVABLE | DIAGNOSTIC | No byte change established; aggregate difference is algorithm-only |
| `r4_fixed_actor_count_predicate_failure_reproduction.json` | UNAVAILABLE | `d8cb646de9da5eb6c2fdb1ab558ead114d0b9b0cbcbf4b2f0554934bf05bc7a8` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |
| `repository_authority.json` | UNAVAILABLE | `a829e8df1f87f6e2492babc040728a9725903cf0a7428c3dc28df7a9f726dc78` | NOT INDIVIDUALLY PROVABLE | REPOSITORY_PRESERVATION | No byte change established; aggregate difference is algorithm-only |
| `transaction_ledger_actor_plan_binding_v1.json` | UNAVAILABLE | `76ee828ce4d6713154983d3e1a2d81d7d0d772d515247586a31519cbe07d69f6` | NOT INDIVIDUALLY PROVABLE | DERIVED_SUMMARY | No byte change established; aggregate difference is algorithm-only |

## G. INVENTORY STABILITY

The algorithms do not depend on mtime, creation time, absolute root, temp paths, locale, file modes, directory iteration order, platform separators, or a self-referential manifest. The historical lock occurred after all 42 files and the final report were complete. The sole explanatory variable is an unversioned terminator-policy change (`5c6e` versus `0a`) between two otherwise identical algorithms.

## H. LOCK-TIMING AUDIT

- Process A shutdown artifact: `2026-09-24T00:59:38.1346777Z`.
- Process-quiescence artifact: `2026-09-24T01:00:51.9410606Z`.
- Final adjudication and latest R5 artifact: `2026-09-24T01:03:42.3056308Z`.
- R5 report final mtime: `2026-09-24T01:03:42.3066230Z`.
- Old aggregate lock output: `2026-09-24T01:56:12.389Z`.
- R6 gate failure: `2026-09-24T02:04:52.2534932Z`.

The lock was after final immutable closure; CASE D does not apply.

## I. ARTIFACT AUTHORITY CLASSIFICATION

Every R5 artifact was classified from its content and dependency, not from its filename alone.

| Path | Authority class | Supports claim | Hard-block future continuation? |
|---|---|---|---:|
| `actor_plan_count_authority_inventory.json` | CORE_SEMANTIC_AUTHORITY | Frozen-plan expected-count authority and observer transport | YES |
| `actor_plan_count_negative_matrix.json` | DERIVED_SUMMARY | Detailed pure negative fixtures | NO |
| `actor_plan_dynamic_positive_matrix.json` | DERIVED_SUMMARY | Detailed pure positive fixtures | NO |
| `ckpt1_preservation.json` | REPOSITORY_PRESERVATION | Inherited production and installed-HARL identity | YES |
| `ckpt2_r5_pre_runtime_freeze.json` | REPOSITORY_PRESERVATION | Frozen harness and production identities | YES |
| `ckpt2_r5_preflight.json` | DERIVED_SUMMARY | Consolidated pre-runtime result summary | NO |
| `ckpt2_r5_run_identity.json` | OTHER | Attempt identity and zero-retry policy | NO |
| `clean_interpreter_baseline.json` | DIAGNOSTIC | Pure-process import cleanliness | NO |
| `failure_receipt.json` | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | Parent gate denial and absent checkpoint | YES |
| `final_stop_adjudication.json` | FINAL_ADJUDICATION_AUTHORITY | Canonical final STOP and zero-mutation claims | YES |
| `historical_actor_adam_plan_consistency.json` | DERIVED_SUMMARY | Retrospective RE1 plan/Adam comparison | NO |
| `historical_ckpt2_preservation.json` | REPOSITORY_PRESERVATION | Earlier CKPT2 preservation | NO |
| `historical_ckpt2_r1_preservation.json` | REPOSITORY_PRESERVATION | Earlier CKPT2-R1 preservation | NO |
| `historical_ckpt2_r2_preservation.json` | REPOSITORY_PRESERVATION | Earlier CKPT2-R2 preservation | NO |
| `historical_ckpt2_r3_preservation.json` | REPOSITORY_PRESERVATION | Earlier CKPT2-R3 preservation | NO |
| `historical_ckpt2_r4_preservation.json` | REPOSITORY_PRESERVATION | Earlier CKPT2-R4 preservation | NO |
| `historical_dynamic_actor_plan_consistency.json` | DERIVED_SUMMARY | Retrospective RE1 dynamic-plan comparison | NO |
| `inherited_contract_preservation.json` | DERIVED_SUMMARY | Inherited identity/event/gate contract summary | NO |
| `parent/parent_process_inventory.json` | PROCESS_SHUTDOWN_BOOKKEEPING | Parent/worker PID lifecycle | NO |
| `pre_runtime_harness_repair_log.json` | DIAGNOSTIC | R5 harness-only repair scope | NO |
| `preflight_ckpt1_pure.json` | DERIVED_SUMMARY | Detailed inherited CKPT1 matrix | NO |
| `process_a/core_failure.json` | CORE_SEMANTIC_AUTHORITY | Durable failure state and counters; duplicate of tx-scoped authority | NO |
| `process_a/core_process_config_authority.json` | CORE_SEMANTIC_AUTHORITY | Real process, learner, config, and source identity | YES |
| `process_a/core_runtime_checkpoints.jsonl` | DIAGNOSTIC | Runtime checkpoint trace | NO |
| `process_a/core_tx1_failure.json` | CORE_SEMANTIC_AUTHORITY | Tx001 S5 failure and exact zero mutation counters | YES |
| `process_a/core_tx1_rollout_decision_evidence.json` | CORE_SEMANTIC_AUTHORITY | Tx001 rollout provenance and collection preservation | YES |
| `process_a/environment_creation.json` | DERIVED_SUMMARY | Duplicate environment-creation receipt | NO |
| `process_a/failure_receipt.json` | CORE_SEMANTIC_AUTHORITY | Causal traceback and process-local STOP | YES |
| `process_a/initial_state.json` | CORE_SEMANTIC_AUTHORITY | Fresh learner semantic/optimizer state | YES |
| `process_a/runtime_identity.json` | CORE_SEMANTIC_AUTHORITY | Fresh process, CUDA readiness, and learner count | YES |
| `process_a/shutdown_result.json` | PROCESS_SHUTDOWN_BOOKKEEPING | Environment and SimulationApp shutdown | YES |
| `process_a_environment_creation.json` | CORE_SEMANTIC_AUTHORITY | Parent-visible real environment creation | YES |
| `process_a_environment_registration.json` | CORE_SEMANTIC_AUTHORITY | Reviewed real Gym entry point | YES |
| `process_a_parent_adjudication.json` | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | A-to-B denial conditions | YES |
| `process_a_real_package_identity.json` | CORE_SEMANTIC_AUTHORITY | Repository production package identity | YES |
| `process_b_launch_gate.json` | CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY | Durable Process-B denial | YES |
| `process_quiescence.json` | PROCESS_SHUTDOWN_BOOKKEEPING | Final inactivity, no B, no retry | YES |
| `pure_qualification_result.json` | CORE_SEMANTIC_AUTHORITY | Canonical R5 pure qualification summary | YES |
| `pure_runtime_process_isolation.json` | DIAGNOSTIC | Pure/runtime OS-process isolation | NO |
| `r4_fixed_actor_count_predicate_failure_reproduction.json` | DERIVED_SUMMARY | Historical R4 defect reproduction | NO |
| `repository_authority.json` | REPOSITORY_PRESERVATION | Branch/commit/index/worktree provenance | NO |
| `transaction_ledger_actor_plan_binding_v1.json` | DERIVED_SUMMARY | Plan/observed equality schema summary | NO |

## J. CORE HISTORICAL AUTHORITY SET

The minimum hard-blocking set contains 19 R5-root artifacts plus two external anchors: the frozen R5 harness and final R5 report. It preserves final adjudication, exact failure counters and cause, real process/package/environment identity, source freeze, pure qualification, Process-B denial, shutdown, and quiescence. The remaining 23 R5-root files are classified as advisory noncore evidence; their later drift should be reported but should not independently invalidate the reviewed semantic STOP.

The exact paths, hashes, supported claims, and downstream dependencies are recorded in `r5_core_historical_authority_set.json` and `r5_noncore_artifact_set.json`.

## K. DRIFT IMPACT ADJUDICATION

Primary category: `CASE C — METADATA_OR_INVENTORY_ALGORITHM_DRIFT`.

More specifically, this is inventory-algorithm drift, not metadata drift. Byte-changed files established: `0`. Metadata-only files established: `0`. Core-authority changed files established: `0`. Noncore changed files established: `0`.

R5 core authority integrity is `PASS`: the same complete current byte-row body exactly reproduces both disputed aggregates under their recorded terminators, the lock occurred after finalization, and the separately locked R5 harness/report hashes remain unchanged. Individual old per-file hashes remain unavailable and are not fabricated.

## L. PROSPECTIVE PRESERVATION CONTRACT

`prospective_historical_preservation_contract_v1.json` defines deterministic sorted repository-relative POSIX paths, byte sizes, and content SHA-256 values. Missing or changed core/checkpoint-blocking entries hard-fail. Derived and diagnostic drift is advisory unless a concrete dependency promotes the file into the core set. Mtime, absolute paths, locale, and iteration order are excluded.

The manifest does not hash itself. Its canonical entry payload has its own manifest digest, and the completed manifest file receives the external SHA-256 `1a426b8673a86f05604658dfa21b604de2bda9d4b6838bb7def711ea146d13ec` in a separate receipt.

## M. PURE CONTRACT TESTS

All 8 offline cases passed with no runtime imports:

| Case | Expected behavior | Result |
|---|---|---|
| Same core bytes | PASS | PASS |
| Changed core byte | STOP | PASS |
| Missing core file | STOP | PASS |
| Changed derived diagnostic | ADVISORY | PASS |
| Mtime-only change | PASS | PASS |
| Absolute-root relocation | PASS | PASS |
| Directory iteration reordering | same digest | PASS |
| Extra untracked diagnostic | ADVISORY | PASS |

Prospective preservation contract: `QUALIFIED` for offline use; it was not installed into production or runtime.

## N. R6 RECEIPT-BINDING STATUS

The R6 harness still contains direct frozen-plan count binding: `STATICALLY PRESENT`. Existing `py_compile` remains recorded. R6 pure qualification was not run, and no real R6 transaction ran. Therefore the repair remains `NOT QUALIFIED`.

## O. FINAL VERDICT

`PHASE-B2-T4-CKPT2-R6-HR1-INVENTORY-ALGORITHM-DRIFT-RECONCILED-AWAITING-GPT-REVIEW`

R6's historical STOP is preserved. HR1 explains the aggregate mismatch without rewriting R5 or accepting the current digest blindly. This does not authorize an R6 retry, R7, R15, CUDA/Isaac/learner execution, checkpoint continuation, evaluation, playback, training, staging, or commit. The next gate is independent GPT review of CKPT2-R6-HR1.
