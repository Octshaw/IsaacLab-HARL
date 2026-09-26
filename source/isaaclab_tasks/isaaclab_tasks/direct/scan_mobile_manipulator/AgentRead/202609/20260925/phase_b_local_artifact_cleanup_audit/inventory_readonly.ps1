param([string]$Mode='summary',[int]$Offset=0,[int]$Limit=500)
$ErrorActionPreference='Stop'
$env:GIT_OPTIONAL_LOCKS='0'
$root=(Get-Location).Path
$ar='source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead'
$audit="$ar/202609/20260925/phase_b_local_artifact_cleanup_audit"
$alternate='source/isaac_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead'
function Git([string[]]$Arguments) {
 $info=[Diagnostics.ProcessStartInfo]::new('git')
 $info.WorkingDirectory=$root
 $info.UseShellExecute=$false; $info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
 foreach($arg in @('--no-optional-locks','-c','core.longpaths=true','-c','core.quotepath=false')+$Arguments){[void]$info.ArgumentList.Add($arg)}
 $proc=[Diagnostics.Process]::Start($info)
 $ot=$proc.StandardOutput.ReadToEndAsync(); $et=$proc.StandardError.ReadToEndAsync(); $proc.WaitForExit()
 if($proc.ExitCode -ne 0){throw "Read-only git query failed: $($et.Result)"}
 $ot.Result
}
function Digest([string[]]$Lines) {
 [Array]::Sort($Lines,[StringComparer]::Ordinal)
 [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes(($Lines -join "`n")))).ToLowerInvariant()
}
$tracked=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($p in (Git @('ls-files','-z')).Split([char]0,[StringSplitOptions]::RemoveEmptyEntries)){[void]$tracked.Add($p)}
$retain=@{}
$rules="$audit/retention_rules.json"
if(Test-Path -LiteralPath $rules){
 foreach($r in (Get-Content -LiteralPath $rules -Raw | ConvertFrom-Json).entries){$retain[$r.relative_path]=$r}
}
$files=[Collections.Generic.List[object]]::new()
$skipped=[Collections.Generic.List[string]]::new()
foreach($base in @($ar,$alternate)){
 $stack=[Collections.Generic.Stack[string]]::new(); $stack.Push((Join-Path $root $base))
 while($stack.Count -gt 0){
  foreach($item in Get-ChildItem -LiteralPath $stack.Pop() -Force){
   $p=[IO.Path]::GetRelativePath($root,$item.FullName).Replace('\','/')
   if($p -eq $audit -or $p -match '/(PHASE_B_LOCAL_ARTIFACT_CLEANUP_AUDIT.md|PHASE_B_LOCAL_ARTIFACT_DELETE_EXECUTION_PLAN.md|TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_AUDIT_20260925.md)$'){continue}
   if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){$skipped.Add($p); continue}
   if($item.PSIsContainer){$stack.Push($item.FullName);continue}
   $phase=if($p -match '/([^/]+_artifacts)(?:/|\.zip$)'){$Matches[1]}else{'protected_documentation'}
   $c='DELETE_RECOMMENDED'; $why='superseded_raw'; $code='HISTORICAL_ONLY'
   if($tracked.Contains($p) -or $item.Extension -in @('.md','.py','.ps1','.yaml','.yml','.toml','.ini','.cfg')){
    $c='KEEP_REQUIRED'; $why='protected_source_report_or_tracked_evidence'; $code='NONE'
   }elseif($retain.ContainsKey($p)){
    $c=$retain[$p].classification; $why=$retain[$p].reason
   }elseif($item.Extension -eq '.zip'){$c='DELETE_STRONG';$why='byte_verified_duplicate_zip';$code='NONE'
   }elseif($item.Extension -eq '.tmp'){$c='DELETE_STRONG';$why='incomplete_atomic_write_temp_with_retained_failure_receipt'
   }elseif($item.Extension -eq '.pt'){$why='closed_smoke_checkpoint_not_paper_policy'
   }elseif($item.Extension -eq '.log'){$why='closed_process_log_redundant_to_compact_result'
   }elseif($item.Extension -eq '.json' -and $item.Length -le 100000 -and $item.Name -match '(?:^|_)(final_result|failure_receipt|formal_supervisor_result|process_quiescence|stop_receipt|root_cause|failure_reproduction)\.json$'){
    $c='KEEP_COMPACT_EVIDENCE';$why='compact_historical_outcome_or_stop_provenance'
   }elseif($item.Extension -notin @('.json','.jsonl','.log','.pt','.zip','.pyc')){$c='UNKNOWN_REVIEW_REQUIRED';$why='unrecognized_generated_format';$code='NONE'}
   $files.Add([pscustomobject]@{p=$p;s=[long]$item.Length;t=$item.LastWriteTimeUtc.Ticks.ToString();c=$c;r=$why;phase=$phase;code=$code;tracked=$tracked.Contains($p)})
  }
 }
}
$files=@($files | Sort-Object p)
$dirs=@{}
foreach($f in $files){
 $d=$f.p.Substring(0,$f.p.LastIndexOf('/'))
 while($d.StartsWith($ar,[StringComparison]::Ordinal) -or $d.StartsWith($alternate,[StringComparison]::Ordinal)){
  if(!$dirs.ContainsKey($d)){$dirs[$d]=[Collections.Generic.List[object]]::new()}
  $dirs[$d].Add($f)
  if($d -eq $ar -or $d -eq $alternate){break}
  $d=$d.Substring(0,$d.LastIndexOf('/'))
 }
}
$entries=[Collections.Generic.List[object]]::new()
$covered=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($d in @($dirs.Keys | Sort-Object Length)){
 if($covered.Contains($d)){continue}
 $members=$dirs[$d]
 $cats=@($members.c | Select-Object -Unique)
 # Directory deletion is used only for fully homogeneous, non-protected trees.
 if($cats.Count -eq 1 -and $members.Count -gt 1 -and $d -ne $ar -and $d -ne $alternate){
  $reasons=@($members.r | Select-Object -Unique)
  $code=if($members.code -contains 'HISTORICAL_ONLY'){'HISTORICAL_ONLY'}else{'NONE'}
  $lines=@($members | ForEach-Object {"$($_.p)|$($_.s)|$($_.t)"})
  $entries.Add([pscustomobject]@{p=$d;type='directory';n=$members.Count;s=[long](($members | Measure-Object s -Sum).Sum);digest=(Digest $lines);c=$cats[0];r=($reasons -join ';');phase=$members[0].phase;code=$code;tracked_count=@($members | Where-Object tracked).Count})
  foreach($f in $members){[void]$covered.Add($f.p)}
  foreach($child in $dirs.Keys){if($child.StartsWith($d+'/',[StringComparison]::Ordinal)){[void]$covered.Add($child)}}
 }
}
foreach($f in $files){
 if(!$covered.Contains($f.p)){
  $entries.Add([pscustomobject]@{p=$f.p;type='file';n=1;s=$f.s;t=$f.t;digest=(Digest @("$($f.p)|$($f.s)|$($f.t)"));c=$f.c;r=$f.r;phase=$f.phase;code=$f.code;tracked_count=[int]$f.tracked})
 }
}
$entries=@($entries | Sort-Object p)
if($Mode -eq 'entries'){
 @($entries | Select-Object -Skip $Offset -First $Limit) | ConvertTo-Json -Compress -Depth 10
 exit
}
$groups=@($files | Group-Object phase | ForEach-Object{
 $ms=$_.Group
 [pscustomobject]@{phase=$_.Name;files=$ms.Count;bytes=[long](($ms | Measure-Object s -Sum).Sum);categories=@($ms|Group-Object c|ForEach-Object{[pscustomobject]@{classification=$_.Name;files=$_.Count;bytes=[long](($_.Group|Measure-Object s -Sum).Sum)}})}
})
[pscustomobject]@{
 scope='All pre-existing files in both AgentRead roots; this audit outputs excluded. Global tracked/source/docs protection applies outside scope too.'
 files=$files.Count; bytes=[long](($files|Measure-Object s -Sum).Sum);entry_count=$entries.Count
 metadata_digest=(Digest @($files|ForEach-Object{"$($_.p)|$($_.s)|$($_.t)"}))
 skipped_reparse=$skipped.ToArray()
 categories=@($files|Group-Object c|ForEach-Object{[pscustomobject]@{classification=$_.Name;files=$_.Count;bytes=[long](($_.Group|Measure-Object s -Sum).Sum)}})
 phases=$groups
 top50_files=@($files|Sort-Object s -Descending|Select-Object -First 50)
 top50_directories=@($dirs.Keys|ForEach-Object{
  $m=$dirs[$_]; [pscustomobject]@{p=$_;files=$m.Count;bytes=[long](($m|Measure-Object s -Sum).Sum);categories=@($m.c|Select-Object -Unique)}
 }|Sort-Object bytes -Descending|Select-Object -First 50)
 thresholds=@(100000,1000000,10000000,50000000,100000000,500000000,1000000000|ForEach-Object{
  $v=$_;$m=@($files|Where-Object s -gt $v);[pscustomobject]@{strictly_greater_than_bytes=$v;files=$m.Count;bytes=[long](($m|Measure-Object s -Sum).Sum)}
 })
} | ConvertTo-Json -Compress -Depth 12
