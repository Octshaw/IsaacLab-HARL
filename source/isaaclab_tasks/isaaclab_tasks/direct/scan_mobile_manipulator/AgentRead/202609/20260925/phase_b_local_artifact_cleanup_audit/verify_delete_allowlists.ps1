#requires -Version 7.0
<#
Read-only review of the two exact Phase-B cleanup allowlists.
This helper neither grants approval nor changes files, Git, or artifact state.
Default output is a JSON summary. -PassThru returns Files, ManifestHashes,
Summary and a Recheck scriptblock for a separately approved execution plan.
#>
[CmdletBinding()]
param([switch]$PassThru)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$expectedRoot = [IO.Path]::GetFullPath('E:\Project\IsaacLab_HARL').TrimEnd('\', '/')
$rootPrefix = $expectedRoot + [IO.Path]::DirectorySeparatorChar
$ordinalIgnoreCase = [StringComparison]::OrdinalIgnoreCase
$scriptFile = $PSCommandPath
$scriptHash = (Get-FileHash -LiteralPath $scriptFile -Algorithm SHA256).Hash.ToLowerInvariant()
$protectedExtensions = @('.md', '.markdown', '.py', '.pyi', '.ps1', '.psm1', '.psd1',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.config')
$broadRoots = @('source', 'scripts', 'logs', 'results', 'output', 'outputs',
    'AgentRead', 'configs', 'config', '.git', '.vscode', '.github')
$manifestSpecs = @(
    @{ Name = 'delete_strong_allowlist.json'; Classification = 'DELETE_STRONG' },
    @{ Name = 'delete_recommended_allowlist.json'; Classification = 'DELETE_RECOMMENDED' }
)

function Assert-NoReparseAncestor([string]$AbsolutePath) {
    $cursor = [IO.Path]::GetFullPath($AbsolutePath)
    while ($true) {
        $item = Get-Item -LiteralPath $cursor -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse point is forbidden: $cursor"
        }
        $parent = [IO.Directory]::GetParent($cursor)
        if ($null -eq $parent) { break }
        $cursor = $parent.FullName
    }
}

function Resolve-ReviewedPath([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or
        [IO.Path]::IsPathRooted($RelativePath) -or
        $RelativePath -match '[:*?\[\]\x00-\x1f]' -or
        $RelativePath.Contains('\')) {
        throw "Non-canonical, rooted or wildcard path: $RelativePath"
    }
    $canonical = $RelativePath.TrimEnd('/')
    $segments = $canonical.Split('/')
    $isCacheTarget = $segments[-1] -eq '__pycache__' -or (
        $segments.Count -gt 1 -and $segments[-2] -eq '__pycache__' -and
        [IO.Path]::GetExtension($canonical) -eq '.pyc')
    if ($segments.Count -eq 0 -or @($segments | Where-Object {
        $_ -in @('', '.', '..', '.git') -or $_ -ne $_.TrimEnd(' ', '.')
    }).Count -ne 0) {
        throw "Unsafe path segment: $RelativePath"
    }
    if ($canonical -in $broadRoots -or $segments[-1] -eq 'AgentRead' -or (
        -not $isCacheTarget -and
        @($segments | Where-Object { $_ -in @('config', 'configs') }).Count -ne 0)) {
        throw "Broad or protected directory target: $RelativePath"
    }
    $absolute = [IO.Path]::GetFullPath((Join-Path $expectedRoot $canonical))
    if (-not $absolute.StartsWith($rootPrefix, $ordinalIgnoreCase)) {
        throw "Target escapes the expected repository: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $absolute)) {
        throw "Reviewed target is missing: $RelativePath"
    }
    Assert-NoReparseAncestor $absolute
    $resolved = (Resolve-Path -LiteralPath $absolute).ProviderPath
    if (-not $resolved.StartsWith($rootPrefix, $ordinalIgnoreCase) -or
        -not [string]::Equals($resolved, $absolute, $ordinalIgnoreCase)) {
        throw "Resolved target differs or escapes repository: $RelativePath"
    }
    [pscustomobject]@{
        RelativePath = $canonical
        FullPath = $absolute
        IsCacheTarget = $isCacheTarget
    }
}

function Assert-NonOverlappingTarget([string]$RelativePath) {
    if (-not $entryPaths.Add($RelativePath)) {
        throw "Duplicate manifest target: $RelativePath"
    }
    if ($entryAncestorPrefixes.Contains($RelativePath)) {
        throw "Target contains an earlier reviewed target: $RelativePath"
    }
    $ancestor = $RelativePath
    while (($separator = $ancestor.LastIndexOf('/')) -ge 0) {
        $ancestor = $ancestor.Substring(0, $separator)
        if ($entryPaths.Contains($ancestor)) {
            throw "Overlapping manifest targets: $ancestor / $RelativePath"
        }
        [void]$entryAncestorPrefixes.Add($ancestor)
    }
}

function Read-Git([string[]]$Arguments) {
    $info = [Diagnostics.ProcessStartInfo]::new('git')
    $info.WorkingDirectory = $expectedRoot
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.Environment['GIT_OPTIONAL_LOCKS'] = '0'
    foreach ($arg in @('--no-optional-locks', '-c', 'core.longpaths=true',
        '-c', 'core.quotepath=false') + $Arguments) {
        [void]$info.ArgumentList.Add($arg)
    }
    $process = [Diagnostics.Process]::Start($info)
    try {
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) {
            throw "Read-only Git query failed: $($stderr.Result)"
        }
        $stdout.Result
    } finally {
        $process.Dispose()
    }
}

function Read-Members([string]$AbsolutePath) {
    $members = [Collections.Generic.List[object]]::new()
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($AbsolutePath)
    while ($pending.Count -gt 0) {
        $next = $pending.Pop()
        $item = Get-Item -LiteralPath $next -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Reparse point encountered in reviewed membership: $next"
        }
        if ($item.PSIsContainer) {
            foreach ($child in $item.GetFileSystemInfos()) {
                if (($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                    throw "Reparse child encountered; traversal refused: $($child.FullName)"
                }
                $pending.Push($child.FullName)
            }
        } else {
            $relative = [IO.Path]::GetRelativePath($expectedRoot, $item.FullName).Replace('\', '/')
            if (-not $item.FullName.StartsWith($rootPrefix, $ordinalIgnoreCase) -or
                $relative -match '[\x00-\x1f]' -or
                $relative.Split('/') -contains '.git') {
                throw "Invalid member path: $relative"
            }
            $members.Add([pscustomobject]@{
                RelativePath = $relative
                FullPath = $item.FullName
                SizeBytes = [long]$item.Length
                LastWriteTimeUtcTicks = $item.LastWriteTimeUtc.Ticks.ToString(
                    [Globalization.CultureInfo]::InvariantCulture)
            })
        }
    }
    # Emit an array as one object, including the empty-directory case.
    ,$members.ToArray()
}

function Get-MembershipDigest([object[]]$Members) {
    $ordered = [Collections.Generic.SortedDictionary[string, object]]::new(
        [StringComparer]::Ordinal)
    foreach ($member in $Members) {
        if ($ordered.ContainsKey($member.RelativePath)) {
            throw "Duplicate membership path: $($member.RelativePath)"
        }
        $ordered.Add($member.RelativePath, $member)
    }
    $rows = [Collections.Generic.List[string]]::new()
    foreach ($member in $ordered.Values) {
        $rows.Add($member.RelativePath + '|' +
            $member.SizeBytes.ToString([Globalization.CultureInfo]::InvariantCulture) +
            '|' + $member.LastWriteTimeUtcTicks)
    }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes([string]::Join("`n", $rows))
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { [Convert]::ToHexString($hasher.ComputeHash($bytes)).ToLowerInvariant() }
    finally { $hasher.Dispose() }
}

Assert-NoReparseAncestor $expectedRoot
Assert-NoReparseAncestor $scriptFile
if (-not $scriptFile.StartsWith($rootPrefix, $ordinalIgnoreCase)) {
    throw 'Validator must reside inside the expected repository.'
}
$gitRoot = [IO.Path]::GetFullPath((Read-Git @('rev-parse', '--show-toplevel')).Trim()).TrimEnd('\', '/')
if (-not [string]::Equals($gitRoot, $expectedRoot, $ordinalIgnoreCase)) {
    throw "Unexpected Git root: $gitRoot"
}
$tracked = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($path in (Read-Git @('ls-files', '-z')).Split([char]0,
    [StringSplitOptions]::RemoveEmptyEntries)) {
    [void]$tracked.Add($path)
}
$files = [Collections.Generic.SortedDictionary[string, object]]::new(
    [StringComparer]::Ordinal)
$seenCaseInsensitive = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
$entryPaths = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
$entryAncestorPrefixes = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase)
$manifestHashes = [ordered]@{}
$classTotals = [ordered]@{}
$entryCount = 0
foreach ($spec in $manifestSpecs) {
    $manifestPath = Join-Path $PSScriptRoot $spec.Name
    Assert-NoReparseAncestor $manifestPath
    $manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
    if ($manifest.classification -cne $spec.Classification -or
        $manifest.approval -cne 'NOT_GRANTED' -or
        $null -eq $manifest.entries -or $manifest.entries -isnot [array]) {
        throw "Unexpected manifest schema, classification or planning approval state: $manifestPath"
    }
    $classFiles = 0L
    $classBytes = 0L
    foreach ($entry in $manifest.entries) {
        if ($entry.type -cnotin @('file', 'directory') -or
            $entry.code_dependency -cnotin @('NONE', 'HISTORICAL_ONLY') -or
            [long]$entry.tracked_file_count -ne 0 -or
            [long]$entry.file_count -lt 0 -or [long]$entry.size_bytes -lt 0 -or
            $entry.membership_sha256 -cnotmatch '^[0-9a-f]{64}$') {
            throw "Unsafe or invalid manifest entry: $($entry.relative_path)"
        }
        $target = Resolve-ReviewedPath $entry.relative_path
        Assert-NonOverlappingTarget $target.RelativePath
        $isDirectory = (Get-Item -LiteralPath $target.FullPath -Force).PSIsContainer
        if (($entry.type -eq 'directory') -ne $isDirectory) {
            throw "Entry type changed: $($target.RelativePath)"
        }
        $members = Read-Members $target.FullPath
        $bytes = 0L
        foreach ($member in $members) {
            $extension = [IO.Path]::GetExtension($member.RelativePath)
            if ($target.IsCacheTarget -and $extension -ne '.pyc') {
                throw "Cache target contains a non-pyc member: $($member.RelativePath)"
            }
            if ($tracked.Contains($member.RelativePath)) {
                throw "Tracked file is protected: $($member.RelativePath)"
            }
            if ($extension -in $protectedExtensions -or
                $member.RelativePath.Split('/') -contains '.git' -or (
                -not ($target.IsCacheTarget -and $extension -eq '.pyc') -and
                @($member.RelativePath.Split('/') | Where-Object {
                    $_ -in @('config', 'configs')
                }).Count -gt 0)) {
                throw "Source, documentation or config member is protected: $($member.RelativePath)"
            }
            if (-not $seenCaseInsensitive.Add($member.RelativePath)) {
                throw "Duplicate or overlapping member: $($member.RelativePath)"
            }
            $member | Add-Member -NotePropertyName Classification -NotePropertyValue $spec.Classification
            $files.Add($member.RelativePath, $member)
            $bytes += $member.SizeBytes
        }
        if ($members.Count -ne [long]$entry.file_count -or $bytes -ne [long]$entry.size_bytes) {
            throw "Membership count or size drift: $($target.RelativePath)"
        }
        if ((Get-MembershipDigest $members) -cne $entry.membership_sha256) {
            throw "Membership digest drift: $($target.RelativePath)"
        }
        $classFiles += $members.Count
        $classBytes += $bytes
        $entryCount++
    }
    if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifestHash) {
        throw "Manifest changed while being validated: $manifestPath"
    }
    $manifestHashes[$spec.Name] = $manifestHash
    $classTotals[$spec.Classification] = [ordered]@{ files = $classFiles; bytes = $classBytes }
}
$totalBytes = 0L
foreach ($member in $files.Values) { $totalBytes += $member.SizeBytes }
$summary = [ordered]@{
    mode = 'DRY_RUN_ONLY'
    approval = 'NOT_GRANTED'
    repository = $expectedRoot
    head = (Read-Git @('rev-parse', 'HEAD')).Trim()
    manifest_sha256 = $manifestHashes
    manifest_entries = $entryCount
    verified_exact_file_count = $files.Count
    verified_exact_size_bytes = $totalBytes
    classification_totals = $classTotals
    tracked_files_affected = 0
    active_code_dependencies_affected = 0
    files_changed = 0
    git_mutations = 0
    membership_digest_format = 'Ordinal-sorted repo-relative paths; path|size|LastWriteTimeUtc.Ticks; UTF-8 without BOM or final newline'
}
if (-not $PassThru) {
    $summary | ConvertTo-Json -Depth 8
    return
}
# The fresh pass must match these exact manifest and validator bytes.
$boundScriptFile = $scriptFile
$boundScriptHash = $scriptHash
$boundManifestHashes = $manifestHashes
$recheck = {
    if ((Get-FileHash -LiteralPath $boundScriptFile -Algorithm SHA256).Hash.ToLowerInvariant() -cne $boundScriptHash) {
        throw 'Validator bytes changed after the review pass.'
    }
    $fresh = & $boundScriptFile -PassThru
    foreach ($name in $boundManifestHashes.Keys) {
        if ($fresh.ManifestHashes[$name] -cne $boundManifestHashes[$name]) {
            throw "Reviewed manifest bytes changed: $name"
        }
    }
    $fresh
}.GetNewClosure()
[pscustomobject]@{
    Summary = $summary
    ManifestHashes = $manifestHashes
    Files = @($files.Values)
    Recheck = $recheck
}
