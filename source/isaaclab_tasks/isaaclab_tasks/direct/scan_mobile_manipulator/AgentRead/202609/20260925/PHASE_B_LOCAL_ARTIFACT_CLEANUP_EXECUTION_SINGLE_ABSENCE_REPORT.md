# Phase-B Approved Local Artifact Cleanup: Single-Absence Execution

Date: 2026-09-25 (Asia/Shanghai).
Classification: **PHASE-B-LOCAL-ARTIFACT-CLEANUP-EXECUTED**.
Phase B: **COMPLETE / GPT REVIEW PASS / CLOSED**.
Approved local cleanup: **COMPLETE**.

## Actual result

| Field | Value |
|---|---:|
| originally_approved_files | 50639 |
| originally_approved_logical_bytes | 12122958520 |
| already_absent_files | 1 |
| already_absent_manifest_bytes | 36178 |
| effective_delete_files | 50638 |
| effective_delete_logical_bytes | 12122922342 |
| actually_deleted_files | 50638 |
| actually_deleted_logical_bytes | 12122922342 |
| failed_or_remaining_files | 0 |
| added_targets | 0 |
| file_delete_errors | 0 |
| directories_deleted | 0 |
| tracked_deletions | 0 |
| unapproved_deletions | 0 |

DELETE_STRONG actually removed: 692 files / 13,791,106 bytes.
DELETE_RECOMMENDED actually removed: 49,946 files / 12,109,131,236 bytes.
Only exact verified files were removed; all original directories remain.

Actual logical deletion: 12.122922342 decimal GB.
Physical available-space change was **not measured**. Logical file lengths are
not a claim of exact NTFS allocation or disk free-space increase.
The already-absent ZIP contributes zero to this task's deletion/reclaim result.

## Exact authority and sole exception

The latest explicit user supplement authorizes execution of the original two
allowlists minus precisely this repository-relative file:

`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260925/phase_b_git_closeout_artifacts.zip`

Original entry: DELETE_STRONG / file / 1 / 36,178 bytes; original ZIP review
recorded six entries identical to their originals. It was already absent.
Its disappearance cause/time remains UNKNOWN. No recreation, copy or download
was performed. No other absent file was skipped and no target was added.

Frozen original inputs, unchanged:

| Input | SHA-256 |
|---|---|
| delete_strong_allowlist.json | 51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce |
| delete_recommended_allowlist.json | a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009 |
| verify_delete_allowlists.ps1 | b1acbaf7fa51d9e56ac4cf8638515586fab302b18eee50cc952deb53259f3d7a |

The minimal validator copy is
[verify_delete_allowlists_single_absence.ps1](phase_b_local_artifact_cleanup_execution/verify_delete_allowlists_single_absence.ps1),
SHA-256 `e25f89256ee96578687bf91e73b81c9e163e35355a7da14f13f6746d444a3095`.
It verifies original input identities on every pass, resolves the sole exception,
checks its ancestors/parent, successfully enumerates the parent, and accepts
only an actual file-not-found error (Win32 2) for that exact absent leaf.
Access, enumeration, path-resolution and reparse errors are not absence.
Reappearance also stops verification. Original manifests, validator, audits
and their historical NOT_GRANTED wording were not edited.

All other original path/type/count/size/time/membership, overlap/case alias,
reparse, tracked, source/report/Git protection and ACTIVE dependency checks
remain in force. The original exact approval-string comparison is retained;
authority is the explicit user instruction, not a claimed interactive input.

## Execution chronology and preserved stops

- Original execution: missing ZIP; STOP-PRECHECK, 0 files / 0 bytes.
  [Original report](PHASE_B_LOCAL_ARTIFACT_CLEANUP_EXECUTION_REPORT.md) and
  [original result](phase_b_local_artifact_cleanup_execution/execution_result.json)
  remain byte-for-byte unchanged.
- First single-absence wrapper: exact target verification passed; bookkeeping
  then failed on an empty ARCHIVE_OPTIONAL list's absent Sum property under
  strict mode. It never reached bound Recheck/deletion. Its
  [STOP result](phase_b_local_artifact_cleanup_execution/execution_result_single_absence.json),
  log, authority and script remain unchanged; deleted 0 / 0.
- The [final wrapper](phase_b_local_artifact_cleanup_execution/execute_approved_cleanup_single_absence_final.ps1)
  differs only in empty-list byte summation (explicit 0) and new output names.
  This fixes aggregation, not a file/IO/permission drift and not a wider exception.
  Syntax parsing and empty/nonempty summation tests passed.
  Wrapper SHA-256:
  `ca1d69f014861a44dc12067832186c89d04539da9fd6408869b8a08d0a19ec30`.
- Final execution began 20:20:55 +08:00; full precheck, protection baseline and
  bound fresh Recheck completed before deletion started at 20:27:27 +08:00.
  Execution and postchecks finished 20:41:02 +08:00.
- No file deletion failed, no file-delete retry occurred, and no old execution
  result was overwritten. The additional read-only completion verification
  finished at 20:43:41 +08:00.

## Safety and outcome verification

Both frozen manifest hashes and the original validator hash match.
The four required Phase-B commits remain ancestors of current HEAD.
Point-in-time known-writer inspection found no known candidate writer; no user
process was killed. This is not an OS-wide lock or a hostile-race guarantee.

The exact original set difference is one file / 36,178 bytes; added paths: 0.
All 6,660 remaining manifest entries and their expanded 50,638 files passed
the original metadata/membership checks, followed by the bound fresh Recheck.
All keep/unknown manifests were read; their 4,466 members are disjoint from
deletion targets. Every file removal retained index, boundary, ancestor-reparse,
type, size and LastWriteTime checks, using only:

`Remove-Item -LiteralPath $taskAbsolute -Force -ErrorAction Stop`

The append-only log has 50,638 unique successful deletion records, correct
running totals, one bound-Recheck event and one deletion-start event; no stop
event. A separate read-only pass checked every logged path is absent, each is
under an original approved entry, and every effective entry's file/byte total
matches. No post-delete existence dry-run of the old validator was attempted.

Deletion log SHA-256:
`2842861611163eb3f2154161f7af31c37a10f06295fa051e14462614775f6d35`.

All 6,326 pre-existing non-target files retained size/time/content hashes
through deletion and postcheck; 2,884 original directories remain.
This covers project source, historical reports, original audit inputs,
old execution records and current handoff before its authorized update.

| Retained category | Files | Current pre-handoff logical bytes | Result |
|---|---:|---:|---|
| KEEP_REQUIRED | 646 | 8,035,858 | PRESERVED |
| KEEP_COMPACT_EVIDENCE | 211 | 1,281,434 | PRESERVED |
| KEEP_LOCAL_USEFUL | 7 | 3,343,441 | PRESERVED |
| UNKNOWN_REVIEW_REQUIRED | 3,602 | 459,942,298 | RETAINED / NOT CLEANED |
| ARCHIVE_OPTIONAL | 0 | 0 | EMPTY / NO ACTION |

Final 23 compact JSON plus all seven canonical R14 ledgers match their original
audit SHA-256 values (30/30). CKPT1's 19 compact JSON match pre-delete hashes.
Eleven prior/static execution files, including the original execution report,
were also explicitly rehashed and remain unchanged.

Audited retained scope before this final handoff update: 4,466 files /
472,603,031 bytes. The +2,171-byte difference from the old audit's 472,600,860
is the previously authorized TASK_PROGRESS update, not target drift.
New audit/execution records and the new handoff archive are outside the old
inventory denominator. The current handoff is intentionally updated only after
all deletion/protection checks, with a byte-exact archive first.

HEAD: `5e62cd58d631946aa5d68a64c27c8132ae5aef84` (main).
Index SHA-256:
`2712362dd719e06b45c376989caa51dfe38c8a8c919bfbd3cb3d31a04ace7e8e`.
HEAD/index/tag refs/root .gitignore/.git/info/exclude are unchanged.
No tracked deletions, unapproved deletions or protected content changes.
The existing lifecycle tag was not repaired or moved.

## Handoff, accepted losses and records

[TASK_PROGRESS archive](TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_SINGLE_ABSENCE_20260925.md):
8,707 bytes; byte-by-byte comparison passed before editing current handoff.
SHA-256:
`40d8668cecc7c0ab131ab03abd1cf3ab6f16e57e2b8f916ee752a814c5435bbc`.
Only the current TASK_PROGRESS existing document was then updated.
All new/modified files remain unstaged/uncommitted.

Nine approved smoke-checkpoint tensor payloads are deleted; the exact old
checkpoint can no longer be loaded. Partial historical raw replay and the
audit's 294 detail-link occurrences in 14 historical reports intentionally
lose targets. Historical reports were not rewritten to hide these losses.
Deleted untracked bytes cannot be restored through Git. No deleted-content
backup, move or compression was made; the handoff archive is the required
documentation-only exception, not an artifact backup.

Runtime / training / experiments / checkpoint load-save: **0**.
Git add / commit / push / tag / ignore modifications: **0**.
Production, test, harness and installed HARL source changes: **0**.

- [Final execution authority and protection baseline](phase_b_local_artifact_cleanup_execution/execution_authority_single_absence_final.json)
- [Append-only deletion log](phase_b_local_artifact_cleanup_execution/deletion_log_single_absence_final.jsonl)
- [Final execution result and completion checks](phase_b_local_artifact_cleanup_execution/execution_result_single_absence_final.json)
- [Original cleanup audit](PHASE_B_LOCAL_ARTIFACT_CLEANUP_AUDIT.md)
- [Original execution plan](PHASE_B_LOCAL_ARTIFACT_DELETE_EXECUTION_PLAN.md)

STOP: approved cleanup is complete. No UNKNOWN cleanup, tag repair, Git write,
runtime experiment or new cleanup phase follows. PAPER-1 implementation and
protocol require separate authorization.
