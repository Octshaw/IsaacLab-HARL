#requires -Version 7.0
# Execution wrapper: reuses the reviewed deletion block without changing the validator.
[CmdletBinding()]
param([switch]$ExecuteApproved)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if(-not $ExecuteApproved){throw 'Explicit authorized execution switch required.'}
$env:GIT_OPTIONAL_LOCKS='0'
$taskRepoRoot='E:\Project\IsaacLab_HARL'
$taskAr='source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead'
$taskAuditRoot=Join-Path $taskRepoRoot "$taskAr/202609/20260925/phase_b_local_artifact_cleanup_audit"
$taskExecutionRoot=$PSScriptRoot
$taskRootPrefix=[IO.Path]::GetFullPath($taskRepoRoot).TrimEnd('\')+'\'
if(-not $taskExecutionRoot.StartsWith($taskRootPrefix,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path $taskExecutionRoot -Leaf) -ne 'phase_b_local_artifact_cleanup_execution'){throw 'Unexpected execution directory.'}
foreach($name in @('execution_authority.json','deletion_log.jsonl','execution_result.json')){
 if(Test-Path -LiteralPath (Join-Path $taskExecutionRoot $name)){throw 'Existing execution records: no automatic retry or resume.'}
}
function Read-Git([string[]]$Arguments){
 $info=[Diagnostics.ProcessStartInfo]::new('git')
 $info.WorkingDirectory=$taskRepoRoot;$info.UseShellExecute=$false;$info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 $info.Environment['GIT_OPTIONAL_LOCKS']='0'
 foreach($arg in @('--no-optional-locks','-c','core.longpaths=true','-c','core.quotepath=false')+$Arguments){[void]$info.ArgumentList.Add($arg)}
 $proc=[Diagnostics.Process]::Start($info)
 try{$ot=$proc.StandardOutput.ReadToEndAsync();$et=$proc.StandardError.ReadToEndAsync();$proc.WaitForExit()
 if($proc.ExitCode -ne 0){throw "Read-only Git query failed: $($et.Result)"};$ot.Result}finally{$proc.Dispose()}
}
function File-Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save-NewJson([string]$Name,[object]$Value){
 $path=Join-Path $taskExecutionRoot $Name
 $json=($Value|ConvertTo-Json -Depth 15)+[char]10
 $stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$data=[Text.UTF8Encoding]::new($false).GetBytes($json);$stream.Write($data,0,$data.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
function Git-State{
 [ordered]@{
 branch=(Read-Git @('branch','--show-current')).Trim();head=(Read-Git @('rev-parse','HEAD')).Trim()
 index_sha256=(File-Hash (Join-Path $taskRepoRoot '.git/index'))
 tag_refs=(Read-Git @('show-ref','--tags'));status=(Read-Git @('status','--short'))
 tracked_deletions=@((Read-Git @('ls-files','--deleted','-z')).Split([char]0,[StringSplitOptions]::RemoveEmptyEntries))
 root_ignore_sha256=(File-Hash (Join-Path $taskRepoRoot '.gitignore'))
 local_exclude_sha256=(File-Hash (Join-Path $taskRepoRoot '.git/info/exclude'))}
}
function Assert-Quiescent{
 $processes=@(Get-CimInstance Win32_Process)
 $risks=@($processes|Where-Object{
 $_.ProcessId -ne $PID -and (
 $_.Name -match '^(python|pythonw|kit|isaac.*|git|robocopy|rsync|7z)\.exe$' -or
 ($_.Name -match '^(pwsh|powershell|cmd)\.exe$' -and $_.CommandLine -match '(?i)(execute_approved_cleanup|Remove-Item|git clean|test_assignment_|train\.py|evaluate.*\.py|isaaclab\.bat)'))
 }|Select-Object ProcessId,ParentProcessId,Name,CommandLine)
 if($risks.Count -gt 0){throw ("Concurrent writer risk: "+($risks|ConvertTo-Json -Compress))}
 [ordered]@{checked_utc=[DateTime]::UtcNow.ToString('o');known_writer_risks=0
 limitation='Point-in-time known-process inspection plus member Recheck, not an OS-wide lock.'
 shells=@($processes|Where-Object{$_.ProcessId -ne $PID -and $_.Name -match '^(pwsh|powershell)\.exe$'}|Select-Object ProcessId,ParentProcessId,Name,CommandLine)}
}
function Read-SafeFiles([string]$Absolute){
 $pending=[Collections.Generic.Stack[string]]::new();$items=[Collections.Generic.List[object]]::new();$pending.Push($Absolute)
 while($pending.Count -gt 0){
 $item=Get-Item -LiteralPath $pending.Pop() -Force
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Reparse point: $($item.FullName)"}
 if(-not $item.FullName.StartsWith($taskRootPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Protection snapshot escapes repository.'}
 if($item.PSIsContainer){foreach($child in $item.GetFileSystemInfos()){$pending.Push($child.FullName)}}else{$items.Add($item)}
 };,$items.ToArray()
}
function Repository-Snapshot{
 $pending=[Collections.Generic.Stack[string]]::new();$pending.Push($taskRepoRoot)
 $files=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::OrdinalIgnoreCase)
 $dirs=[Collections.Generic.List[string]]::new()
 while($pending.Count -gt 0){foreach($item in Get-ChildItem -LiteralPath $pending.Pop() -Force){
 $rel=[IO.Path]::GetRelativePath($taskRepoRoot,$item.FullName).Replace('\','/')
 if($rel -eq '.git' -or $item.FullName -eq $taskExecutionRoot){continue}
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Unexpected project reparse path: $rel"}
 if($item.PSIsContainer){$dirs.Add($rel);$pending.Push($item.FullName)}
 else{$files.Add($rel,[pscustomobject]@{relative_path=$rel;size_bytes=[long]$item.Length;last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString()})}
 }}
 [pscustomobject]@{Files=$files;Directories=$dirs.ToArray()}
}
function Record-Event([object]$Event){$taskLogWriter.WriteLine(($Event|ConvertTo-Json -Depth 5 -Compress));$taskLogWriter.Flush()}
$taskDeletedCount=0L;$taskDeletedBytes=0L;$taskFailure=$null;$taskStage='PRECHECK';$taskActivePath=$null
$taskVerified=$null;$taskRepoBefore=$null;$taskGitBefore=$null;$taskPost=$null
$taskSurvivors=[Collections.Generic.List[object]]::new()
$taskKeepBaseline=[ordered]@{}
$taskKeepPaths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$taskDeletePaths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$taskStarted=[DateTime]::UtcNow.ToString('o')
$taskAuthority=[ordered]@{
 task='PHASE-B-LOCAL-ARTIFACT-CLEANUP-EXECUTION'
 authorization_source='Explicit user attachment 13306daa-bfbc-4c6c-a80b-58396441f73c/Pasted text.txt'
 authorization_attachment_sha256=(File-Hash 'C:\Users\33506\.codex\attachments\13306daa-bfbc-4c6c-a80b-58396441f73c\Pasted text.txt')
 authorized_files=50639;authorized_logical_bytes=12122958520
 authorized_strong_sha256='51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce'
 authorized_recommended_sha256='a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'
 authorized_validator_sha256='b1acbaf7fa51d9e56ac4cf8638515586fab302b18eee50cc952deb53259f3d7a'
 noninteractive_gate='Exact user-approved string; not claimed to have been typed interactively.'
 started_utc=$taskStarted;wrapper_sha256=(File-Hash $PSCommandPath)
 runtime_allowed=$false;git_mutations_allowed=$false;backups_moves_compression_allowed=$false
}
$taskLogStream=[IO.FileStream]::new((Join-Path $taskExecutionRoot 'deletion_log.jsonl'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough)
$taskLogWriter=[IO.StreamWriter]::new($taskLogStream,[Text.UTF8Encoding]::new($false));$taskLogWriter.AutoFlush=$true
try{
 $taskGitBefore=Git-State;$taskAuthority.git_before=$taskGitBefore
 $taskAuthority.quiescence_initial=Assert-Quiescent
 Write-Output 'PRECHECK: authority and known-writer inspection; reading reviewed validator.'

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
    git --no-optional-locks -c core.longpaths=true -c core.quotepath=false -C $taskRepoRoot merge-base --is-ancestor $taskCommit HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Closure commit precondition changed.' }
}
$taskVerified = & $taskVerifier -PassThru
$taskExpectedGate = 'APPROVE DELETE 51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'
$taskGate = 'APPROVE DELETE 51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'
if ($taskGate -cne $taskExpectedGate) { throw 'Approval gate not satisfied.' }


# Additional required protection baseline; not a deletion classification.
$taskAuthority.initial_validator_summary=$taskVerified.Summary
foreach($f in $taskVerified.Files){[void]$taskDeletePaths.Add($f.RelativePath)}
$taskManifestReads=[Collections.Generic.List[object]]::new()
foreach($name in @('delete_strong_allowlist.json','delete_recommended_allowlist.json','keep_required.json','keep_compact_evidence.json','keep_local_useful.json','unknown_review_required.json','archive_optional_allowlist.json')){
 $path=Join-Path $taskAuditRoot $name;$manifest=([IO.File]::ReadAllText($path)|ConvertFrom-Json)
 $taskManifestReads.Add([pscustomobject]@{file=$name;sha256=(File-Hash $path);entries=@($manifest.entries).Count;classification=$manifest.classification})
 if($manifest.classification -in @('DELETE_STRONG','DELETE_RECOMMENDED')){continue}
 $members=[Collections.Generic.List[object]]::new()
 foreach($entry in $manifest.entries){
 $absolute=[IO.Path]::GetFullPath((Join-Path $taskRepoRoot $entry.relative_path))
 if(-not $absolute.StartsWith($taskRootPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Keep path escapes repository.'}
 $actual=Read-SafeFiles $absolute
 if($actual.Count -ne [long]$entry.file_count){throw "Keep membership count drift: $($entry.relative_path)"}
 foreach($item in $actual){
 $rel=[IO.Path]::GetRelativePath($taskRepoRoot,$item.FullName).Replace('\','/')
 if($taskDeletePaths.Contains($rel)){throw "Delete/KEEP intersection: $rel"}
 if(-not $taskKeepPaths.Add($rel)){throw "Duplicate KEEP membership: $rel"}
 $members.Add([pscustomobject]@{relative_path=$rel;size_bytes=[long]$item.Length;last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString()})
 }}
 $taskKeepBaseline[$manifest.classification]=[ordered]@{files=$members.Count;bytes=[long](($members|Measure-Object size_bytes -Sum).Sum);audit_files=$manifest.totals.files;audit_bytes=$manifest.totals.bytes;members=$members.ToArray()}
}
if($taskKeepPaths.Count -ne 4466 -or $taskKeepBaseline.UNKNOWN_REVIEW_REQUIRED.files -ne 3602 -or $taskKeepBaseline.UNKNOWN_REVIEW_REQUIRED.bytes -ne 459942298 -or $taskKeepBaseline.KEEP_LOCAL_USEFUL.files -ne 7 -or $taskKeepBaseline.KEEP_LOCAL_USEFUL.bytes -ne 3343441){throw 'Retained required counts changed.'}
$taskAuthority.fully_read_manifests=$taskManifestReads.ToArray();$taskAuthority.keep_baseline=$taskKeepBaseline
Write-Output 'PRECHECK: retaining 4,466 KEEP/UNKNOWN files; hashing all non-target project files.'
$taskRepoBefore=Repository-Snapshot
foreach($rel in $taskDeletePaths){if(-not $taskRepoBefore.Files.ContainsKey($rel)){throw "Approved target missing from workspace baseline: $rel"}}
foreach($record in $taskRepoBefore.Files.Values){
 if($taskDeletePaths.Contains($record.relative_path)){continue}
 $record|Add-Member -NotePropertyName sha256 -NotePropertyValue (File-Hash (Join-Path $taskRepoRoot $record.relative_path))
 $taskSurvivors.Add($record)
}
$taskAuthority.non_target_baseline=$taskSurvivors.ToArray();$taskAuthority.directories_before=$taskRepoBefore.Directories
$taskAuthority.scope_before_files=$taskRepoBefore.Files.Count
$taskAuthority.quiescence_before_recheck=Assert-Quiescent;$taskAuthority.ready_for_bound_recheck=$true
Save-NewJson 'execution_authority.json' $taskAuthority
Write-Output 'PRECHECK: running original bound Recheck immediately before approved deletion.'

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

if((File-Hash (Join-Path $taskRepoRoot '.git/index')) -cne $taskGitBefore.index_sha256 -or (Read-Git @('rev-parse','HEAD')).Trim() -cne $taskGitBefore.head){throw 'Git boundary changed during prechecks.'}
$taskFinalQuiet=Assert-Quiescent;$taskStage='DELETE'
Record-Event ([ordered]@{event='approved_deletion_start';utc=[DateTime]::UtcNow.ToString('o');files=$taskVerified.Files.Count;bytes=$taskVerified.Summary.verified_exact_size_bytes;quiescence=$taskFinalQuiet})
Write-Output 'DELETE START: all prechecks passed; exact files only, no directories.'
foreach ($taskFile in $taskVerified.Files) {
    $taskActivePath=$taskFile.RelativePath
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
    Record-Event ([ordered]@{event='deleted';relative_path=$taskFile.RelativePath;logical_bytes=$taskFile.SizeBytes;classification=$taskFile.Classification;cumulative_files=$taskDeletedCount;cumulative_logical_bytes=$taskDeletedBytes;utc=[DateTime]::UtcNow.ToString('o')})
    if($taskDeletedCount % 1000 -eq 0){Write-Output ("DELETE PROGRESS: {0}/50639 files; {1} logical bytes" -f $taskDeletedCount,$taskDeletedBytes)}
}
[pscustomobject]@{ deleted_files=$taskDeletedCount; logical_bytes=$taskDeletedBytes }
# Do not recursively remove parent/empty directories. Do not touch keep/unknown data.

 $taskStage='POSTCHECK'
 Write-Output 'POSTCHECK: confirming target absence, retained content and Git invariants.'
}catch{
 $taskFailure=[ordered]@{stage=$taskStage;path=$taskActivePath;message=$_.Exception.Message;detail=$_.ToString();utc=[DateTime]::UtcNow.ToString('o')}
 try{Record-Event ([ordered]@{event='stop';failure=$taskFailure;deleted_files=$taskDeletedCount;deleted_logical_bytes=$taskDeletedBytes})}catch{}
}finally{$taskLogWriter.Dispose()}
# Never rerun pre-deletion existence dry-run after deletion.
try{
 if($null -ne $taskVerified){
 $remaining=[Collections.Generic.List[string]]::new()
 foreach($f in $taskVerified.Files){if(Test-Path -LiteralPath $f.FullPath){$remaining.Add($f.RelativePath)}}
 $missingProtected=[Collections.Generic.List[string]]::new();$changedProtected=[Collections.Generic.List[object]]::new()
 foreach($record in $taskSurvivors){
 $p=Join-Path $taskRepoRoot $record.relative_path
 if(-not(Test-Path -LiteralPath $p)){$missingProtected.Add($record.relative_path);continue}
 $now=Get-Item -LiteralPath $p -Force
 if($now.Length -ne $record.size_bytes -or $now.LastWriteTimeUtc.Ticks.ToString() -cne $record.last_write_time_utc_ticks -or (File-Hash $p) -cne $record.sha256){
 $changedProtected.Add([pscustomobject]@{relative_path=$record.relative_path;current_size=[long]$now.Length;original_size=$record.size_bytes})
 }}
 $missingDirectories=@()
 if($null -ne $taskRepoBefore){$missingDirectories=@($taskRepoBefore.Directories|Where-Object{-not(Test-Path -LiteralPath (Join-Path $taskRepoRoot $_) -PathType Container)})}
 $gitAfter=Git-State;$keepChecks=[ordered]@{}
 foreach($category in $taskKeepBaseline.Keys){
 $b=$taskKeepBaseline[$category];$missing=@($b.members|Where-Object{-not(Test-Path -LiteralPath (Join-Path $taskRepoRoot $_.relative_path))})
 $keepChecks[$category]=[ordered]@{baseline_files=$b.files;baseline_bytes=$b.bytes;missing=$missing.Count;content_verified_by_non_target_snapshot=$true;preserved=($missing.Count -eq 0 -and $missingProtected.Count -eq 0 -and $changedProtected.Count -eq 0)}
 }
 $scopeBytes=0L;foreach($category in $taskKeepBaseline.Keys){$scopeBytes+=$taskKeepBaseline[$category].bytes}
 $taskPost=[ordered]@{
 remaining_approved_files=$remaining.Count;remaining_approved_paths=$remaining.ToArray()
 protected_files_hashed=$taskSurvivors.Count;missing_non_target_files=$missingProtected.ToArray();changed_non_target_files=$changedProtected.ToArray()
 missing_original_directories=$missingDirectories;keep_checks=$keepChecks
 audited_remaining_files=$taskKeepPaths.Count;audited_remaining_actual_logical_bytes=$scopeBytes
 original_audit_remaining_bytes=472600860;preexisting_retained_size_delta=$scopeBytes-472600860
 git_after=$gitAfter;head_unchanged=($gitAfter.head -ceq $taskGitBefore.head);index_unchanged=($gitAfter.index_sha256 -ceq $taskGitBefore.index_sha256)
 tag_refs_unchanged=($gitAfter.tag_refs -ceq $taskGitBefore.tag_refs);root_ignore_unchanged=($gitAfter.root_ignore_sha256 -ceq $taskGitBefore.root_ignore_sha256)
 local_exclude_unchanged=($gitAfter.local_exclude_sha256 -ceq $taskGitBefore.local_exclude_sha256)
 tracked_deletions=$gitAfter.tracked_deletions.Count;unapproved_deletions=$missingProtected.Count
 }
 if($null -eq $taskFailure -and ($taskDeletedCount -ne 50639 -or $taskDeletedBytes -ne 12122958520 -or $remaining.Count -ne 0 -or $missingProtected.Count -ne 0 -or $changedProtected.Count -ne 0 -or $missingDirectories.Count -ne 0 -or -not $taskPost.head_unchanged -or -not $taskPost.index_unchanged -or -not $taskPost.tag_refs_unchanged -or -not $taskPost.root_ignore_unchanged -or -not $taskPost.local_exclude_unchanged -or $gitAfter.tracked_deletions.Count -ne 0)){throw 'Postcheck discrepancy; actual deletion is not rolled back.'}
 }
}catch{if($null -eq $taskFailure){$taskFailure=[ordered]@{stage='POSTCHECK';message=$_.Exception.Message;detail=$_.ToString();utc=[DateTime]::UtcNow.ToString('o')}}}
if(-not(Test-Path -LiteralPath (Join-Path $taskExecutionRoot 'execution_authority.json'))){Save-NewJson 'execution_authority.json' $taskAuthority}
$classification=if($null -eq $taskFailure){'PHASE-B-LOCAL-ARTIFACT-CLEANUP-EXECUTED'}elseif($taskDeletedCount -eq 0){'PHASE-B-LOCAL-ARTIFACT-CLEANUP-STOP-PRECHECK'}else{'PHASE-B-LOCAL-ARTIFACT-CLEANUP-PARTIAL-STOP'}
$result=[ordered]@{
 task='PHASE-B-LOCAL-ARTIFACT-CLEANUP-EXECUTION';classification=$classification;phase_b='COMPLETE / GPT REVIEW PASS / CLOSED'
 started_utc=$taskStarted;finished_utc=[DateTime]::UtcNow.ToString('o')
 approved_files=50639;approved_logical_bytes=12122958520
 approved_manifest_sha256=@{'delete_strong_allowlist.json'='51f4861085f56fa5a41869f55dc1ed7f422444f62db7235f5a5dc492dfe3fdce';'delete_recommended_allowlist.json'='a78979c4b005fbb2b0c468c7d92bab2c15bba841c38c0438bb04818563417009'}
 approved_validator_sha256='b1acbaf7fa51d9e56ac4cf8638515586fab302b18eee50cc952deb53259f3d7a'
 actual_deleted_files=$taskDeletedCount;actual_deleted_logical_bytes=$taskDeletedBytes;failed_operations=[int]($null -ne $taskFailure);remaining_approved_files=50639-$taskDeletedCount
 first_error=$taskFailure;postcheck=$taskPost
 accepted_losses=@('9 smoke checkpoint tensors: exact old checkpoint no longer loadable','Partial historical raw forensic replay unavailable','14 historical reports / 294 detail links lose targets','Untracked deleted bytes cannot be restored through Git')
 backup_or_content_copy_created=$false;files_moved=0;files_compressed=0;directories_deleted=0
 runtime_executed=0;checkpoint_operations=0;git_mutations=0
 physical_free_space_change_measured=$false;logical_bytes_are_not_physical_free_space_delta=$true
 handoff='Not updated yet; update only after this execution result and retained-file checks.'
}
Save-NewJson 'execution_result.json' $result
[pscustomobject]@{classification=$classification;deleted_files=$taskDeletedCount;deleted_logical_bytes=$taskDeletedBytes;error=$taskFailure;remaining=50639-$taskDeletedCount}|ConvertTo-Json -Depth 5 -Compress
if($null -ne $taskFailure){exit 1}
