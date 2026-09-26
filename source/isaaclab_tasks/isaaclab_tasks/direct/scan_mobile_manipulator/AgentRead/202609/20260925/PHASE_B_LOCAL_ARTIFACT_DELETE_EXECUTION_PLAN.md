# Phase-B Local Artifact Delete Execution Plan

Date: 2026-09-25. **PLANNING ONLY. No execution approval has been granted.**

This file is not a cleanup script invocation. Phase B remains COMPLETE /
GPT REVIEW PASS / CLOSED; cleanup remains NOT EXECUTED.
Read [the audit](PHASE_B_LOCAL_ARTIFACT_CLEANUP_AUDIT.md) and its partial/manual
legacy-data boundary first.

## Exact proposed scope

Only the following two frozen manifests are eligible for separate approval:

| Manifest | Files | Bytes | SHA256 |
|---|---:|---:|---|
| delete_strong_allowlist.json | 693 | 13,827,284 | 51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce |
| delete_recommended_allowlist.json | 49,946 | 12,109,131,236 | a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009 |

Total: 50,639 exact files / 12,122,958,520 logical bytes.
All paths are below E:\Project\IsaacLab_HARL.
UNKNOWN, required, compact and local-useful manifests are **not** deletion
inputs. Optional archive is empty. The 3,602 legacy unknown files remain.

Deletion would lose original raw forensic replay and exact archived checkpoint
loading. Compact reports/digests cannot recreate those bytes. Untracked raw
files are not recoverable through Git after deletion. If a separate backup is
wanted, authorize/review that operation first; none was created by this audit.

Only homogeneous subdirectories have directory-prefix entries. Mixed parents,
including R1, R14 and final checkpoint metadata, are never blanket targets.
The verifier expands directories into an exact checked file list. The future
block below removes files only and deliberately leaves empty directories.

## Preconditions and dry run (read-only)

1. Obtain explicit user approval of these exact hashes, both categories and the
   irreversible raw/checkpoint-replay loss. Approval of this audit or prior
   commits/ignore rules is not deletion approval.
2. Confirm the four Phase-B commits are still ancestors of current HEAD.
   Later audit-document commits are permissible; never infer approval from a
   tag, clean status or ignored status.
3. Stop if any task, editor automation, simulation, training worker, Git writer
   or other process can modify candidate paths. Require a quiescent workspace.
   No validator can atomically lock the entire repository against races.
4. Read all keep/unknown manifests and inspect the exact delete entries.
5. Run this read-only verification in PowerShell 7, from the repository:

~~~powershell
$taskAuditRoot = 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\AgentRead\202609\20260925\phase_b_local_artifact_cleanup_audit'
& (Join-Path $taskAuditRoot 'verify_delete_allowlists.ps1')
~~~

The verifier checks:

- exact repository/path resolution and existence; no absolute/traversal/glob,
  broad root, Git metadata, source/report/config or unsafe path targets;
- every ancestor/member for reparse points; no links followed;
- current NUL-delimited Git tracked set with optional locks disabled and
  long paths enabled; tracked-file rejection;
- exact file/directory type, total count, bytes and membership SHA256;
- duplicate/overlapping targets, case aliases and ACTIVE dependencies;
- metadata membership is ordinal-sorted repository-relative
  path|size|LastWriteTimeUtc.Ticks, UTF8 without BOM, LF, no final newline;
- an explicit narrow exception allows pure .pyc caches inside config
  ancestors; real config files remain protected.

Any change aborts. Do not regenerate/relax allowlists to make a failed dry run
pass under old approval: reassess changed paths and seek fresh approval.
Membership digests bind names/lengths/timestamps, not every raw content byte.
This is a quiescent-filesystem safety check, not tamper-proof attestation
against deliberate same-length/same-timestamp content replacement.
ZIP/selected evidence hashes are independently recorded in the package review.

The inventory helper is **not** an execution authority. Never rerun generic
classification and silently add newly appeared JSON/PT/ZIP files to approval.
No git clean, broad recursive deletion, all-untracked deletion, all-JSON,
all-PT or entire-AgentRead operation is permitted.

[Recorded dry-run and bound Recheck](phase_b_local_artifact_cleanup_audit/dry_run_verification.json).
A passing dry run grants no permission.

## Actual deletion block — DO NOT RUN UNTIL USER APPROVES THE AUDIT

The following block is documentation only and was **not executed**. A future
authorized operator must first obtain explicit user approval outside this
script. The typed gate below is an additional guard, not a substitute for that
authorization. It intentionally requires the complete manifest hashes.

~~~powershell
# DO NOT RUN UNTIL USER APPROVES THE AUDIT.
# Run only in an otherwise quiescent workspace after separately granted approval.
$ErrorActionPreference = 'Stop'
$env:GIT_OPTIONAL_LOCKS = '0'
$taskRepoRoot = 'E:\Project\IsaacLab_HARL'
$taskAuditRoot = Join-Path $taskRepoRoot 'source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\AgentRead\202609\20260925\phase_b_local_artifact_cleanup_audit'
$taskVerifier = Join-Path $taskAuditRoot 'verify_delete_allowlists.ps1'
$taskApprovedVerifierHash = 'b1acbaf7fa51d9e56ac4cf8638515586fab302b18eee50cc952deb53259f3d7a'
$taskApprovedManifestHashes = @{
    'delete_strong_allowlist.json' = '51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce'
    'delete_recommended_allowlist.json' = 'a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'
}
if ((Get-FileHash -LiteralPath $taskVerifier -Algorithm SHA256).Hash.ToLowerInvariant() -cne $taskApprovedVerifierHash) {
    throw 'Verifier bytes changed; stop for review.'
}
foreach ($taskName in $taskApprovedManifestHashes.Keys) {
    if ((Get-FileHash -LiteralPath (Join-Path $taskAuditRoot $taskName) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $taskApprovedManifestHashes[$taskName]) {
        throw "Manifest bytes changed: $taskName"
    }
}
foreach ($taskCommit in @(
    'c107a6c892eb90ff643d549d928c555ec9f9be5b',
    '5e7367ce28f0dfc3d4de86fa90d751284f1159c3',
    '947f9261864945ab120a7958f3cc08b38b37e44a',
    '5e62cd58d631946aa5d68a64c27c8132ae5aef84'
)) {
    git --no-optional-locks -C $taskRepoRoot merge-base --is-ancestor $taskCommit HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Closure commit precondition changed.' }
}
$taskVerified = & $taskVerifier -PassThru
$taskExpectedGate = 'APPROVE DELETE 51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'
$taskGate = Read-Host 'Only after user approval: type the exact APPROVE DELETE string from this plan'
if ($taskGate -cne $taskExpectedGate) { throw 'Approval gate not satisfied.' }

# Full fresh verification immediately before starting; still performs no deletion.
$taskVerified = & $taskVerified.Recheck
foreach ($taskName in $taskApprovedManifestHashes.Keys) {
    if ($taskVerified.ManifestHashes[$taskName] -cne $taskApprovedManifestHashes[$taskName]) {
        throw 'Approved manifest binding changed.'
    }
}
if ($taskVerified.Files.Count -ne 50639 -or
    $taskVerified.Summary.verified_exact_size_bytes -ne 12122958520) {
    throw 'Reviewed totals changed.'
}
$taskIndexPath = Join-Path $taskRepoRoot '.git\index'
$taskIndexHash = (Get-FileHash -LiteralPath $taskIndexPath -Algorithm SHA256).Hash
$taskRootPrefix = [IO.Path]::GetFullPath($taskRepoRoot).TrimEnd('\') + '\'
$taskDeletedCount = 0L
$taskDeletedBytes = 0L
foreach ($taskFile in $taskVerified.Files) {
    # Exact in-memory files only. Never pass the manifest directory to removal.
    if ((Get-FileHash -LiteralPath $taskIndexPath -Algorithm SHA256).Hash -cne $taskIndexHash) {
        throw 'Git index changed during cleanup; stop immediately.'
    }
    $taskAbsolute = [IO.Path]::GetFullPath($taskFile.FullPath)
    if (-not $taskAbsolute.StartsWith($taskRootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Target escaped repository.'
    }
    $taskCursor = $taskAbsolute
    while ($null -ne $taskCursor) {
        $taskAncestor = Get-Item -LiteralPath $taskCursor -Force
        if ($taskAncestor.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw 'Reparse path appeared after verification.'
        }
        $taskParent = [IO.Directory]::GetParent($taskCursor)
        $taskCursor = if ($null -eq $taskParent) { $null } else { $taskParent.FullName }
    }
    $taskItem = Get-Item -LiteralPath $taskAbsolute -Force
    if ($taskItem.PSIsContainer -or $taskItem.Length -ne $taskFile.SizeBytes -or
        $taskItem.LastWriteTimeUtc.Ticks.ToString() -cne $taskFile.LastWriteTimeUtcTicks) {
        throw 'File changed after verification; stop immediately.'
    }

    # ACTUAL IRREVERSIBLE OPERATION -- ONLY AFTER SEPARATE USER APPROVAL.
    Remove-Item -LiteralPath $taskAbsolute -Force -ErrorAction Stop
    $taskDeletedCount++
    $taskDeletedBytes += $taskFile.SizeBytes
}
[pscustomobject]@{ deleted_files=$taskDeletedCount; logical_bytes=$taskDeletedBytes }
# Do not recursively remove parent/empty directories. Do not touch keep/unknown data.
~~~

This is not transactional: if an I/O error occurs after some approved files
have been removed, stop and report the partial count. Do not automatically
rerun the now-drifted original manifests, expand targets, or suppress errors.
The file-level checks reduce accidental drift but cannot eliminate hostile
concurrent filesystem races; quiescence remains mandatory.

## After a future separately approved execution

Report actual removed paths/count/bytes and recovery limitations; verify all
kept compact evidence/source/docs still exist, Git index/HEAD are unchanged
by deletion, and status reflects no tracked removals. Record any partial
failure. Only then, under that future task's scope, update the cleanup handoff.
Do not label cleanup complete in this planning audit.

Current actions: files deleted 0; moved 0; compressed 0; runtime 0; Git mutations 0.
Next: return the audit and exact manifests to the user for review.
