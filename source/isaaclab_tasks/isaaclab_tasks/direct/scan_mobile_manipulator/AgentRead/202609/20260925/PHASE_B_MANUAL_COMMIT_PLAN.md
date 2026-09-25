# Phase-B Manual Commit Plan

Date: 2026-09-25 (Asia/Shanghai)
Status: READY FOR USER MANUAL COMMIT — NOTHING STAGED/COMMITTED BY CODEX

## Preconditions and grouping

Run from E:\Project\IsaacLab_HARL in PowerShell. Review this plan and the
[change classification](PHASE_B_GIT_CLOSEOUT_CHANGE_CLASSIFICATION.md) first.
The exact allowlist is
[phase_b_manual_commit_paths.json](phase_b_git_closeout_artifacts/phase_b_manual_commit_paths.json).
It contains individual files, not broad directory pathspecs.

| Commit | Purpose / exact allowlist | Current state | Exclusions |
|---|---|---|---|
| A | 361 destinations: 359 monthly moves, AR/AGENTS.md, 20260901 migration report; 359 old paths already staged deleted | 359 R100 staged; 266 destinations additionally edited; AGENTS unstaged; report untracked | All implementation/tests/closure reports/runtime data, .vscode edit |
| B | 11 production paths (manifest B) | 2 modified + 9 untracked | Tests, documentation, generated data |
| C | 96 test/helper paths + 23 final JSON + 19 CKPT1 JSON + root .gitignore = 139 | Tests/evidence untracked; root ignore unstaged | All tensors/logs and other historical raw data; docs D |
| D | 233 documentation paths (manifest D): current handoff, dated reports/archives, compact offline audits, all current closeout files | Handoff unstaged, remaining untracked | Migration already A, root ignore already C, all local-only/unrelated paths |

Four commits are justified: independent migration, runtime implementation, tests/
selected compact evidence, and substantial documentation. The 359 staged entries
are already the correct migration group. Do not commit them before adding their
266 path fixes and two supporting migration documents. No unstage/reset is
needed for the audited index. If the index differs, STOP and review rather than
automatically unstaging unknown user work.

All paths not present in a commit's explicit allowlist are excluded. In
particular, no git add -A, directory-wide AgentRead add, force-add, stash, clean,
hard reset or historical artifact rewrite belongs in this plan.

## 1. Inspect and establish the exact baseline

The commands below are recommendations for the USER. Codex has NOT executed
any staging, commit, tag or push command. The initial guard intentionally stops
if HEAD, branch or index changed since the audit. Check working-tree edits too:
a same-path content edit after this audit requires renewed review.

```powershell
Set-Location -LiteralPath 'E:\Project\IsaacLab_HARL'
$ErrorActionPreference = 'Stop'
$env:GIT_OPTIONAL_LOCKS = '0'
function Invoke-Git {
    & git --no-optional-locks -c core.longpaths=true -c core.quotepath=false @args
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $args" }
}
$manifestPath = 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260925/phase_b_git_closeout_artifacts/phase_b_manual_commit_paths.json'
$plan = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ((Invoke-Git branch --show-current) -cne $plan.base_branch) { throw 'Branch changed: review first' }
if ((Invoke-Git rev-parse HEAD) -cne $plan.base_head) { throw 'HEAD changed: review first' }
$indexPath = Invoke-Git rev-parse --git-path index
if ((Get-FileHash -LiteralPath $indexPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.initial_index_sha256) {
    throw 'Index changed: review first; do not overwrite it'
}
Invoke-Git status --short
Invoke-Git diff --cached --stat
Invoke-Git diff --cached
```

The local origin/main reference matched HEAD at audit; no fetch was performed.
Per-command core.longpaths=true is necessary for this Windows workspace and
does not modify Git configuration.

## 2. Define explicit-path staging with an index-scope guard

This helper only stages files from the audited JSON allowlist. It handles long
lists as NUL-delimited UTF-8 through standard input, avoiding Windows pipe CRLF
ambiguity and a huge command line. It never commits.
Keep this PowerShell session open for the following blocks.

```powershell
function Expand-PathGroups($Groups) {
    foreach ($group in $Groups) {
        foreach ($relative in $group.relative_paths) {
            if ($group.root -eq '.') { $relative }
            else { "$($group.root)/$relative" }
        }
    }
}
function Assert-StagedPaths([string[]]$Expected) {
    $actual = @(Invoke-Git diff --cached --name-only --no-renames)
    $expectedUnique = @($Expected | Sort-Object -Unique)
    if (($actual.Count -ne $expectedUnique.Count) -or
        (@($actual | Where-Object { $_ -cnotin $expectedUnique }).Count -ne 0)) {
        throw 'Unexpected staged membership: STOP and inspect; no automatic reset/unstage'
    }
}
function Stage-ReviewedGroup([string]$Id) {
    $group = @($plan.commits | Where-Object id -CEQ $Id)
    if ($group.Count -ne 1) { throw 'Unknown commit group' }
    $paths = @(Expand-PathGroups $group[0].groups)
    $removed = @(Expand-PathGroups $group[0].removed_groups)
    if ($Id -eq 'A') {
        $migrationDestinations = @($paths | Where-Object { $_ -match '/AgentRead/20260[678]/' })
        Assert-StagedPaths @($migrationDestinations + $removed)
    } else {
        Assert-StagedPaths @()
    }
    foreach ($path in $paths) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing file: $path" }
    }
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = 'git'
    $start.Arguments = '--no-optional-locks -c core.longpaths=true -c core.quotepath=false --literal-pathspecs add --pathspec-from-file=- --pathspec-file-nul'
    $start.WorkingDirectory = (Get-Location).Path
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($start)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes(([string]::Join([char]0, [string[]]$paths)) + [char]0)
    $process.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
    $process.StandardInput.Close()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "Staging failed; inspect index: $($stderrTask.Result)" }
    if ($stdoutTask.Result) { Write-Output $stdoutTask.Result }
    Assert-StagedPaths @($paths + $removed)
    Invoke-Git diff --cached --stat
    Invoke-Git diff --cached
}
```

Stage-ReviewedGroup A expects exactly 718 raw staged paths before adding:
359 original deletions and 359 new destinations. After adding migration fixes,
AGENTS and its report, it expects 720 raw paths. Rename detection may still
display fewer logical lines; the scope guard deliberately uses --no-renames.
Later groups require an empty index first. Stop on any failure; do not continue
to the commit command.

## 3. Commit A — monthly archive migration

Review only migration destinations and path-reference changes. Earlier report
content must remain historical. This is logically independent of Phase-B source.

```powershell
Stage-ReviewedGroup 'A'
# Read the staged diff; only then execute:
Invoke-Git commit -m 'docs(agentread): migrate records to monthly archive structure'
Assert-StagedPaths @()
```

## 4. Commit B — actual production implementation

The exact 11 paths are nine event-training/optimization modules plus the runner
and canonical ValueNorm extraction changes. Lifecycle/event-return foundations
already in HEAD are not restaged as invented new changes.

```powershell
Stage-ReviewedGroup 'B'
# Read the staged diff; only then execute:
Invoke-Git commit -m 'feat(mrta): complete lifecycle-aware Phase B training backbone'
Assert-StagedPaths @()
```

## 5. Commit C — qualification and compact closure evidence

All 96 qualification/helper files remain historical source; committing them
does not request execution. Include 23 final JSON and 19 CKPT1 compact results
only. The root .gitignore rule keeps the smoke tensors local, while existing
rules already ignore the two process logs.

```powershell
Stage-ReviewedGroup 'C'
# Read the staged diff; verify no .pt/.log/ZIP or large forensic dump; only then:
Invoke-Git commit -m 'test(mrta): close Phase B with fresh-process checkpoint continuation'
Assert-StagedPaths @()
```

## 6. Commit D — handoff and documentation

Includes all current closeout documents, the exact manual manifest itself,
the byte-exact pre-closeout handoff archive and the accepted current handoff.
Historical AWAITING-GPT-REVIEW and STOP labels remain unchanged. The substantial
report history justifies a separate docs commit.

```powershell
Stage-ReviewedGroup 'D'
# Read the staged diff; only then execute:
Invoke-Git commit -m 'docs(mrta): finalize Phase B closure records'
Assert-StagedPaths @()
Invoke-Git log -4 --oneline
Invoke-Git status --short
```

A fully clean worktree is NOT expected: bulk historical generated artifacts
and .vscode/.gitignore remain outside these commits. Do not sweep them into
a fifth commit or delete them just to obtain clean status. The manual manifest
and authority report retain their pre-commit audit identities intentionally.

## 7. Optional annotated tag and optional push

Only after all four commits have succeeded and been inspected:

```powershell
Invoke-Git tag -a lifecycle-mrta-phase-b-complete -m 'Lifecycle-aware MRTA Phase B complete'
# Optional, only when you intend to publish:
Invoke-Git push origin main
Invoke-Git push origin lifecycle-mrta-phase-b-complete
```

Do not force-push or overwrite an existing tag. A non-fast-forward rejection is
a stop-for-review condition, not authorization to reset/rebase/merge.

## Evidence and next phase

A fresh clone contains the code, reports, compact final evidence and checkpoint
metadata, but not the loadable binary smoke checkpoint or complete raw
historical forensic directories. Source/HEAD freeze receipts describe the
original successful run: do not update them to the new commit hashes or rerun
the smoke as part of these commands.

After manual commits (and optional tag), the next project phase is
PAPER-1 EXPERIMENT IMPLEMENTATION AND PROTOCOL. No baselines, ablations,
disturbance/scale/multi-seed runs, long training or evaluation were started here.
