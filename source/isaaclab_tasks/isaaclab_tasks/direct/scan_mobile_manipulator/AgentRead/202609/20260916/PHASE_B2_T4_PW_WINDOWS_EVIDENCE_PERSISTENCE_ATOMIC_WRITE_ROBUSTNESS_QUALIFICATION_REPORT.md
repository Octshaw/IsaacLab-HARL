# Phase B2-T4-PW — Windows evidence-persistence / atomic-write robustness qualification

Date: 2026-09-16. **PW qualification result: COMPLETE / AWAITING GPT REVIEW.** This is a pure, test-side persistence phase, **not RE5**. Historical RE4 remains `GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED`, classified `PHASE-B2-T4-RE4-STOP-EVIDENCE-PERSISTENCE-PERMISSION-DENIED-AFTER-MUTATION`. No RE4 artifact, source, learner, or process was resumed or repaired. PW's final adjudication is in section AM; it is not a self-issued GPT REVIEW PASS.

The machine evidence lives in [b2_t4_pw_artifacts](b2_t4_pw_artifacts/). Historical inputs remained under the separate, immutable `b2_t4_re4_artifacts/` directory.

## A. repository authority

Before PW edits: branch `main`; HEAD, `origin/main`, and merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. Full porcelain was scanned: 1,585 lines, SHA-256 `becec3940dab63817e4f2c187a3681fc121f752fcd8e4c7c33be820039cf47d0`. The pre-existing 359 staged monthly-migration paths had `git ls-files --stage` SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No Git index mutation is authorized.

## B. starting reviewed authority

B2-R0–R7, B2-T0–T3, NR, SR, ZD, and EP-Q are reviewed closed. Original T4, RE1–RE3, EP, and EP-P remain historical STOPs. Independent review confirmed RE4's poisoned STOP; this PW investigation cannot reclassify it. EP-Q is process-quiescence authority only, not a training or persistence PASS.

## C. historical RE4 preservation

The [RE4 report](PHASE_B2_T4_RE4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md), one formal worker receipt, supervisor result, final result, tx001–tx130 evidence, JSONL ledgers, and tx130 `.tmp` were read-only. [Pre-analysis SHA-256 inventory](b2_t4_pw_artifacts/re4_failure_artifact_identity.json) includes the key files. The tx130 residue was not deleted, renamed, promoted, or rewritten.

## D. exact tx130 failure boundary

| Property | RE4 tx130 value |
|---|---|
| Stage | `S6_CRITIC_SEQUENCE` |
| Critic optimizer steps before failure | 7 |
| ValueNorm updates before failure | 7 |
| Failed operation | `os.replace(temp, existing final)` |
| Temp path | `...formal01_tx130_critic_progress.json.tmp` |
| Final path | `...formal01_tx130_critic_progress.json` |
| Temp parseable | yes, complete JSON, 556,512 bytes |
| Temp sequence | event 28, `S6_CRITIC_MINIBATCH_COMPLETE` |
| Final existed | yes, event 27, 494,464 bytes |
| Exception | `PermissionError [WinError 5]` |
| S10 / ledger-qualified | 0 / no |
| `partial_update` / `route_poisoned` | true / true |

The temporary file had been flushed, fsynced and closed; the exception was at the replacement call, not at write, fsync, close, or readback. [Forensic JSON](b2_t4_pw_artifacts/tx130_forensic_audit.json) records hashes, metadata, payload and failure evidence.

## E. tx130 irreversible learner mutation

The preserved tx130 failure artifact and receipt record seven critic optimizer steps and seven live ValueNorm updates before the failed evidence publication. The actor sequence had 0 actor optimizer steps in this transaction. No production S10 or transaction-ledger row followed. The only qualified prefix remains tx001–tx129 (129 S10 and 129 ledger rows, 128 bridges); tx131–tx161 were not started. This learner state is poisoned and cannot be resumed.

## F. historical artifact identities

SHA-256: worker receipt `821cdbe63e9143ba6d2209e40e1458daa64e90e4e5f0da2b890d11b3c0df8f7c`; supervisor result `f6631654898a07fc60892506330a203b091e464c56e1ab97d45553ef5054e2f0`; final result `22d1ba623b524f9e16203fc3699d7aa69bfd36466223a73d00155c77947e9ced`; tx130 target `c8f0f2695caeb2ac72ad7cdc90b3ed9ff0677a871f6455d031352e5e8d5aa371`; tx130 temp `adf4e257d4c00a5ad1ac0f5c8b397b355cafff598d70d36fdb6d2f392f67bf16`; tx130 failure `a661c3608d0587e7dffd35fac0a2ba76c93850fd9b0db5eb1e81cfdd56954364`. All 14 inventoried files matched byte length and SHA-256 in the final post-analysis comparison.

The historical RE4 report itself has SHA-256 `f9ae83089798ca68bb5ee813131a318daa285d0339c10942bda08f15e0d9929c`; its harness has SHA-256 `f04ba511f5d644fcb2bbba61d44e73b6b791301b90a0f9b1c264ebff1af4542e`.

## G. persistence source call chain

The retained traceback and exact source show: `test_assignment_phase_b2_t4_re4_normal_horizon_learned_training_integration.py:812` → inherited T0 repeated smoke `test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py:1469–1515,1608` → real adapter `assignment_event_training_real_isaac_adapter.py:1530–1532` → full transaction `assignment_event_training_full_transaction.py:1067,983` → critic sequence and observed receipt `assignment_event_training_real_isaac_adapter.py:402` → `persist_critic`/`persist_progress` → T0 `_atomic_json` → `test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py:1693–1700` → `os.replace` failure. The adapter's failure observer emitted the tx130 failure artifact; RE4 `run_formal_worker` caught the propagated exception and wrote the durable failure receipt. [Source trace](b2_t4_pw_artifacts/current_persistence_source_trace.json) separates the actual source locations from transformed traceback line mapping.

## H. current atomic-write implementation

The current helper creates `<target>.tmp` in the target directory; opens it with text mode `w` and UTF-8; serializes normalized, indented, sorted JSON; flushes and `os.fsync`s; exits the `with` block (closing the handle); then calls `os.replace(temp, target)`. It does **not** immediately reopen/read back or validate a progress-payload digest. The later S10 path stats and hashes the final progress file. A failed replacement leaves a complete temp and the preceding final.

## I. critic-progress write frequency

The adapter emits, per critic minibatch, ValueNorm pre, ValueNorm post, pre-backward diagnostic, and minibatch-complete callbacks: **4 writes**. Five epochs × two minibatches = ten minibatches, followed by one sequence-complete callback: **41 writes per transaction** to the **same target**. tx129's final JSON has exactly 41 events; tx130 final/temp have 27/28. Therefore `W_expected_160 = 160 × 41 = 6,560`, and the stress minimum is `max(10,000, 10 × 6,560) = 65,600` writes **per canonical qualification run**. Actor/factor progress writes the same per-tx destination four times: three actor-segment events plus one sequence-complete event (640 planned over 160 tx). [Frequency JSON](b2_t4_pw_artifacts/current_write_frequency.json).

## J. tx001–tx129 completed-prefix persistence audit

All 129 final critic-progress files parse and have 41 events. They establish 5,289 successful `os.replace` calls for these critic files, of which 5,160 replaced an already-existing target. tx130 then durably reached event 27 (27 further successful calls, 26 replacing an existing target) before the event-28 replacement failed. No earlier matching `.tmp` residue was found. The transaction/training-metric/rolling-health ledgers have 129 rows each. Only final-file timestamps survive, so per-write timing or a timing trend near tx130 cannot be reconstructed. [Prefix audit](b2_t4_pw_artifacts/completed_prefix_persistence_audit.json).

## K. tx130 temp/final forensic audit

The target existed at failure: archive attribute, inherited ACL, owner `XXSYS203-1\\xxsys203_1`, 494,464 bytes, event 27, SHA-256 above. The temp: same observed owner/ACL class and archive attribute, 556,512 bytes, fully parseable event 28, seven critic steps and seven ValueNorm updates. The last target write was about 03:32:04.606 UTC and temp write about 03:32:04.918 UTC. The target and temp are distinct files; the exact RE4 lock owner cannot be read retrospectively from these artifacts.

## L. file-handle lifecycle audit

The existing helper's `with temporary.open('w')` closes before `os.replace`; no target readback handle exists in that helper. The T0 per-minibatch callback retains Python event lists, not open files. The RE4 supervisor waits before reading the receipt/result and does not tail the live critic-progress target. The next progress write starts a new file operation. [Handle audit](b2_t4_pw_artifacts/self_handle_audit.json).

## M. self-handle findings

Source excludes a self-retained temp handle, self-retained target readback handle, and self-retained JSON reader handle across the failing replacement. It does **not** prove that no external process had either path open at tx130. There is no handle-capture trace of the historical failure instant.

## N. concurrent-reader findings

In a new isolated workspace, an independent process holding the current destination without delete sharing caused the exact current helper to raise `PermissionError [WinError 5]`. A rapid open/read/close child overlapped 200 attempted rewrites: 26 succeeded, 174 failed with permission errors; the reader itself recorded 862 reads and 29 permission denials. These counts are a controlled reproduction, not RE4 historical lock attribution. A separate independent child held a prior immutable PW record open while the new helper successfully published the next sequence. [Concurrent evidence](b2_t4_pw_artifacts/concurrent_reader_audit.json).

## O. Windows replace-existing semantics exposure

Repeatedly replacing an existing destination makes every later event dependent on Windows delete-sharing behavior of any holder of that target. The controlled held-open and rapid-reader tests reproduce the same error family without Isaac or learner state. This exposure is established. Whether the RE4 event was a target reader, temp access, indexer, antivirus, sync client, ACL transition, or other OS/filesystem condition is **not** established.

Microsoft's [CreateFileW sharing contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew) confirms that a handle without `FILE_SHARE_DELETE` prevents later delete/rename access. This supports the mechanism of the controlled reproduction, not attribution of the historical RE4 handle.

## P. temp-name collision/stale-temp analysis

Current `<target>.tmp` plus open mode `w` reuses and truncates the same temp on every callback. A crash residue can be silently overwritten by a subsequent attempt; concurrent writers could collide. The observed RE4 prefix had no earlier temp residue, and only one formal worker ran, so collision is not proved as the cause of tx130. PW uses an exclusive, unique `*.tmp.<pid>.<uuid>` for each deterministic final identity; a matching stale temp blocks publication and is never auto-promoted or deleted. [Collision audit](b2_t4_pw_artifacts/temp_collision_audit.json).

## Q. root-cause/failure-family classification

**FAILURE CLASS ESTABLISHED / SPECIFIC LOCK OWNER UNRESOLVED.** Exact historical boundary: Windows denied `os.replace` of a complete, closed temp over an existing target. The source plus controlled reproductions demonstrate replace-existing sharing exposure; they do not establish who held what at 03:32:04.918 UTC. Static ACL denial is disfavored by 5,316 preceding successful critic-progress calls and unchanged owner/ACL class, not logically excluded as a transient factor. [Classification JSON](b2_t4_pw_artifacts/failure_family_analysis.json).

## R. evidence criticality classification

Production transaction authority is the full learner transaction's S10 plus append-only transaction ledger, **not** a critic-progress snapshot. Progress identity, stage, event sequence, cumulative optimizer/ValueNorm counters, and receipt-completion fields are required crash-forensics evidence under the current fail-closed observer contract. Loss/gradient/Adam/ValueNorm detailed numerical fields are diagnostic contents of those required snapshots. No field is promoted into an S10 substitute. Reclassifying progress publication as nonblocking would change the formal contract and is **not** done here.

The [field-by-field classification](b2_t4_pw_artifacts/critic_progress_field_criticality.json) exhausts the preserved tx130 temp's 13 top-level fields and 53 unique nested event fields. Category A contains no progress field; category B marks identity/sequence/counters/receipts needed to reconstruct a partial update; category C marks diagnostic numerical contents. This classification does not change the current requirement to persist the whole snapshot or fail closed on publication error.

## S. repair alternatives considered

Unique temp plus replace-existing retains the demonstrated target-sharing exposure. Bounded `os.replace` retries could duplicate or obscure exact progress attempts and were not justified; retries remain zero. Append-only JSONL would require additional Windows append-sharing, partial-tail framing, and recovery rules. A nonblocking diagnostic path would weaken RE4's fail-closed behavior and needs separate authorization. [Repair decision](b2_t4_pw_artifacts/repair_decision.json).

## T. selected repair

One canonical **test-side** contract: immutable per-progress JSON records, each published from a unique same-directory temp by `os.link(temp, final)` with create-if-absent semantics. After file flush/fsync and handle close, link publication never replaces an existing final; the helper unlinks its own temp, then immediately reads back and validates the record. Duplicates, out-of-order progress, stale temp, write/link/unlink/readback failure all raise and stop. No production or historical RE4 harness edit; no file-operation retry. The helper is `_assignment_phase_b2_t4_windows_evidence_persistence.py`, not bound to RE5.

This choice is explicitly NTFS-scoped: both the isolated C: test volume and future E: workspace volume were observed as NTFS. Microsoft documents [CreateHardLinkW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createhardlinkw) as NTFS file-only and same-volume; the helper uses a same-directory temp. Python documents `os.link` availability on Windows in its [OS API reference](https://docs.python.org/3/library/os.html#os.link). Other filesystems are not qualified.

## U. before/after persistence contract

| Property | RE4 current path | PW-qualified future path |
|---|---|---|
| File identity | one mutable JSON per tx/side | deterministic run/tx/side/sequence JSON |
| Existing destination repeatedly replaced | yes, 41 critic writes/tx | no |
| Temp naming | fixed `<target>.tmp`, `w` truncation | unique `*.tmp.<pid>.<uuid>`, `xb` |
| Append/immutable semantics | cumulative mutable snapshot | immutable per-event records |
| flush/fsync | temp, before replace | temp, before no-overwrite publish |
| readback | none per progress write | immediate bytes/JSON/digest |
| duplicate detection | no explicit progress identity gate | final-exists fails closed |
| stale temp | next write can truncate | matching temp blocks; never auto-promoted |
| Windows held-open behavior | held target can deny replacement | held old final does not block next identity |
| crash recovery | old final + temp ambiguous | temp non-authoritative; explicit review, no resume |
| fail-closed | observer exception stops learner | writer/verification exception stops caller |

## V. progress identity/versioning

Schema `b2_t4_pw_immutable_progress_v1`; every record binds `run_id`, `tx_id`, `stage`, `actor_or_critic`, `progress_sequence`, `planned_sequence_count`, and payload SHA-256, plus a canonical whole-record digest. Final path deterministically binds run/tx/side/sequence. Duplicate final identity fails even with identical bytes. The next sequence requires the preceding sequence to validate. The full transaction verifier rejects missing/extra records, malformed content, digest drift, and temp residue. [Contract JSON](b2_t4_pw_artifacts/persistence_contract_v1.json).

## W. crash-safety contract

No write started: missing required sequence → STOP. Partial or fsynced temp only: non-authoritative; stale temp → STOP, no auto-promotion. Published final before temp unlink: caller has not returned success; temp residue requires explicit review and full verification fails. Published final after unlink/readback: record-qualified. Duplicate identity: STOP. A crashed/poisoned learner may **not** resume merely because progress records exist. File fsync, atomic same-volume no-overwrite link, and readback establish the tested process-crash boundary; Windows directory-entry power-loss durability is not claimed.

## X. negative matrix

[Base matrix](b2_t4_pw_artifacts/negative_matrix.json): 18/18 fail-closed witnesses, including duplicate/out-of-order, wrong run/tx, digest drift, stale/temp-only, injected publication permission denial, held-open existing identity, readback mismatch, malformed final, and missing required record. [Extension](b2_t4_pw_artifacts/negative_matrix_extension.json) additionally verifies a non-JSON-finite payload is rejected before publication. The base matrix's `malformed_payload` case actually exercises missing identity; the extension supplies the malformed numeric payload. No unexpected negative PASS.

## Y. current-helper reproduction

The exact AST of the current `atomic_json` function was isolated from its original source file and executed with primitive JSON payloads, without importing Isaac. Forty-one repeated writes to one target passed without a reader. An independently controlled held-open target then produced `PermissionError [WinError 5]`, leaving an isolated complete `.tmp`. The temporary workspace was separate from RE4. [Reproduction](b2_t4_pw_artifacts/current_helper_reproduction.json).

A second fresh-process [paced reproduction](b2_t4_pw_artifacts/current_helper_cadence_reproduction.json) used cumulative ≈19 KB events, 0.12 s between writes, and grew the same target from 19,139 to 781,612 bytes over 41 writes (RE4 tx129 final: 796,580 bytes). Holding the destination after this realistic-size sequence again produced `WinError 5`. These reproductions establish a mechanism, not RE4's specific historical locker.

## Z. repaired helper implementation

The new pure helper validates identity and JSON-finite payload, writes one temp via exclusive `xb`, flushes/fsyncs/closes, publishes via no-overwrite hard link, unlinks temp, reads back bytes and decoded JSON, and validates payload/record SHA-256. `read_record` and `verify_transaction` perform fail-closed inspection. It imports no Isaac, CUDA, environment, learner, or HARL module. There are no retry loops and no silent `PermissionError` suppression.

## AA. held-open target qualification

Current helper: controlled destination handle denying delete-sharing → exact WinError 5 and closed failure. New helper: an independent child holds sequence 1 open while sequence 2 publishes and verifies; PASS. Attempting to republish sequence 1 is rejected as a duplicate, not overwritten. This distinction is the structural repair's principal Windows witness.

## AB. concurrent-reader qualification

An independent rapid reader and current writer reproduced repeated write and read permission denials. For the new path, the independent held reader of an earlier immutable record did not interfere with the next publication. These pure tests show the repair avoids replacement dependence; they are not a guarantee against all external denials of a new temp or final directory entry.

## AC. repaired stress run 1

An initial independent process (PID 24988) wrote 65,600 immutable records over 1,600 synthetic transactions, 1,349,075,626 bytes. It passed full verification with 0 unexpected PermissionErrors, missing/duplicate/digest-mismatch records, stale-temp promotions, or successful-operation temp residue. Its 476.81 s write/periodic-check result and latency distribution are [retained](b2_t4_pw_artifacts/repaired_stress_run_01.json). This is **additional diagnostic** evidence: the runner gained only non-stress reader/negative-test code while this process was active. The helper and stress function were unchanged, but the strict final two-process gate uses runs 2 and 3 under the same frozen runner identity.

## AD. repaired stress run 2

Frozen-runner fresh processes PID 17936 and PID 9076 each passed **65,600 required writes** and full verification of **1,600 × 41** records. Their respective [run 2](b2_t4_pw_artifacts/repaired_stress_run_02.json) and [run 3](b2_t4_pw_artifacts/repaired_stress_run_03.json) JSONs bind process IDs, counts, bytes, digests, performance, and zero-error gates. Together they wrote 131,200 records and 2,698,151,252 bytes. The single-process/readback path, per-tx sequence reset, periodic full-file checks, fresh-process repeat, held-open negative, and independent-reader evidence passed.

| Test | Writes | Processes | Contention | Expected | Result |
|---|---:|---:|---|---|---|
| Initial diagnostic sequential | 65,600 | 1 | none | PASS | PASS |
| Frozen run 2, sequential + readback | 65,600 | 1 | overlap with independent run | PASS | PASS, 0 errors |
| Frozen run 3, fresh repeat + readback | 65,600 | 1 | overlap with independent run | PASS | PASS, 0 errors |
| Periodic and complete verification | 131,200 | 2 | none within each tx | PASS | PASS, all records |
| Current held-open target | 1 failure probe | 2 | held delete-denying target | fail closed | `WinError 5` |
| New held-open previous record | 1 next-sequence write | 2 | held old final | PASS | PASS |
| Current rapid independent reader | 200 attempts | 2 | rapid reader | diagnostic | 26 writes / 174 denials |
| 160-tx evidence-only slice | 6,560 per run | 2 | source-equivalent | PASS | PASS × 2 |

## AE. RE4-scale 160-transaction simulation

The [160-tx machine witness](b2_t4_pw_artifacts/re4_scale_160tx_simulation.json) records 160 transactions × 41 records = 6,560 records in the initial run. Frozen runs 2 and 3 independently reported `simulation_160tx_pass=true` and then verified all 1,600 transactions. Each synthetic transaction resets the 1–41 sequence under a distinct tx identity. This is evidence-only; no actor/critic math or learner exists.

## AF. tx130 payload replay

[Replay](b2_t4_pw_artifacts/tx130_payload_replay.json): the preserved tx130 temp was read only. Its 28 real event payloads were copied into a fresh PW workspace with the original event stages and new deterministic PW identity. All 28 published and verified, including event 28 `S6_CRITIC_MINIBATCH_COMPLETE`; final digest/readback matched. No learner state was reconstructed.

## AG. record-integrity audit

Each successful write validated exact bytes and decoded record immediately; full transaction verification validated the expected sequence set and both digests. The negative matrix demonstrated tamper rejection. Frozen runs 2 and 3 each had 0 missing records, 0 duplicate records, 0 digest mismatches, 0 malformed accepted records, and 0 out-of-order accepted records. The repaired helper never suppressed an evidence error.

## AH. temp-residue audit

The historical tx130 temp remains untouched. PW intentional permission-denial injection left a temp and the next same-identity attempt stopped on stale residue. A successful publication unlinked its own temp before returning; transaction verification rejected any temp residue. Frozen runs 2 and 3 each had **zero** unreconciled temp residues after successful operations and zero stale-temp promotions.

## AI. performance diagnostics

Each frozen run wrote 1,349,075,626 bytes. Run 2: 491.90 s, mean 7.470 ms, p50 7.286, p95 8.223, p99 9.581, max 5,051.922 ms. Run 3: 485.40 s, mean 7.372 ms, p50 7.018, p95 8.164, p99 10.464, max 2,002.103 ms. These elapsed figures cover writes and periodic checks; complete final verification and temporary-workspace cleanup followed. The long maximum latencies occurred under concurrent pure stress; no arbitrary performance threshold was imposed.

## AJ. production/source preservation

Protected SHA-256 before and after PW: full transaction `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`; real adapter `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`; scan environment `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363`; frozen RE4 harness `f04ba511f5d644fcb2bbba61d44e73b6b791301b90a0f9b1c264ebff1af4542e`. The historical RE4 report and 14 inventoried formal files also matched prior digests. New helper `e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b`; frozen PW runner `c2b1a3fa30922c43bb740faef297ef15a4367149f13afcbf92ac4634052fb725`. [Source manifest](b2_t4_pw_artifacts/source_identity_manifest.json). Production and historical RE4 harness modifications: 0/0.

## AK. exact execution counts

Pure/static Python invocations: **18** (interpreter identity 1; syntax commands 6; audit 1; initial qualification 1; payload replay 1; negative extension 1; concurrency attempts 2, of which the first exposed and then fixed a reader-side test exception; pure stress 3; paced current reproduction 1; field classification 1). Completed current-helper reproductions: **3** (initial, paced, concurrent reader); one earlier reader-side harness attempt was superseded, not counted as PASS. Synthetic fail-closed negative cases: 19/19, plus current held-target and concurrent-reader witnesses. Repaired positive stress processes: 3 total, of which frozen runs 2 and 3 satisfy the two-process gate. `W_expected_160=6,560`; minimum **65,600 per run**; actual repaired writes 196,800 total / 131,200 final frozen pair. Unexpected repaired-path PermissionErrors, missing, duplicate, digest-mismatch, stale-promoted, and successful-path temp residue: 0 each. tx130 payload replays: 1; RE4-scale simulations: 3 (one separately recorded). AppLauncher/environments/resets/physical steps/learners/learner mutations: `0/0/0/0/0/0`; checkpoint I/O/public activation/evaluation-playback/RE5 starts: `0/0/0/0`; Git add/commit/push: `0/0/0`.

## AL. retained nonclaims

PW cannot establish RE4 training completion, a 160-update learner run, terminal/autoreset, reward improvement, checkpoint continuation, long training, public-route readiness, or a specific historical lock owner. Stress on pure NTFS evidence writes is not a RE5 formal run. The new helper is not automatically bound to RE5, and no change to S10/ledger authority or progress criticality is authorized.

The NTFS hard-link path is not a claim of power-loss directory durability or portability to non-NTFS filesystems/network shares. A future RE5 binding would need to enforce this filesystem precondition and the same fail-closed authority boundary.

## AM. final classification

All PW success gates passed within the explicitly bounded **NTFS, pure test-side, process-crash** contract. Classification:

`PHASE-B2-T4-PW-WINDOWS-EVIDENCE-PERSISTENCE-ATOMIC-WRITE-ROBUSTNESS-QUALIFIED-AWAITING-GPT-REVIEW`

State: `B2-T4-PW COMPLETE / AWAITING GPT REVIEW`; Windows persistence stress PASS / AWAITING GPT REVIEW. Historical B2-T4-RE4 remains `GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED`, with its exact earlier classification and one formal attempt. Failure-family precision remains **FAILURE CLASS ESTABLISHED / SPECIFIC LOCK OWNER UNRESOLVED**. The canonical future helper is `b2_t4_pw_immutable_progress_v1`, still **not bound to RE5**. This is not a self-issued GPT REVIEW PASS.

## AN. GPT-review handoff

Review the exact source trace, tx130 event-27/event-28 files and hashes, controlled reader reproductions, no-overwrite publication and crash states, negative matrix, both independent stress receipts, 160-tx simulation, payload replay, and final protected-source/RE4 artifact identity comparison. Do not self-issue GPT REVIEW PASS, start RE5, resume RE4, stage, or commit.
