#Requires -Version 5.1
<#
.SYNOPSIS
  Rebuild git history from commit-manifest.json with backdated research-milestone commits.

.DESCRIPTION
  Decomposes the finished portfolio codebase into a six-month narrative timeline.
  Uses GIT_AUTHOR_DATE / GIT_COMMITTER_DATE for organic timestamps.
  Run from repository root: .\scripts\build_research_history.ps1
#>
param(
    [string]$ManifestPath = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $ManifestPath) { $ManifestPath = Join-Path $PSScriptRoot "commit-manifest.json" }

Set-Location $RepoRoot

function Get-RepoFiles {
    param([string[]]$Paths, [double]$Fraction = 1.0)
    $files = @()
    foreach ($p in $Paths) {
        $full = Join-Path $RepoRoot $p
        if (-not (Test-Path $full)) {
            Write-Warning "Path not found, skipping: $p"
            continue
        }
        if (Test-Path $full -PathType Container) {
            $files += Get-ChildItem -Path $full -Recurse -File | ForEach-Object {
                $_.FullName.Substring($RepoRoot.Path.Length + 1) -replace '\\', '/'
            }
        } else {
            $files += ($p -replace '\\', '/')
        }
    }
    return $files | Sort-Object -Unique
}

function Apply-Fraction {
    param([string]$RelativePath, [double]$Fraction)
    $full = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path $full -PathType Leaf)) { return }
    $lines = Get-Content -Path $full -Encoding UTF8
    if ($lines.Count -le 4) { return }
    $take = [math]::Max(2, [int]($lines.Count * $Fraction))
    $lines[0..($take - 1)] | Set-Content -Path $full -Encoding UTF8 -NoNewline:$false
}

function Restore-FromSnapshot {
    param([string]$SnapshotRoot)
    if (-not (Test-Path $SnapshotRoot)) { return }
    robocopy $SnapshotRoot $RepoRoot /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
}

# Snapshot pristine tree before any fraction mutations
$SnapshotRoot = Join-Path $env:TEMP "ai-research-history-snapshot-$(Get-Random)"
Write-Host "Snapshotting source tree to $SnapshotRoot ..."
robocopy $RepoRoot $SnapshotRoot /E /XD .git .venv .venv_repro .pytest_cache node_modules __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
Write-Host "Loaded $($manifest.Count) commits from manifest."

if (-not $DryRun) {
    $null = git checkout master 2>&1
    $null = git checkout --orphan research-history-rebuild 2>&1
    $null = git rm -rf --cached . 2>&1
}

$commitCount = 0
foreach ($entry in $manifest) {
    Restore-FromSnapshot $SnapshotRoot

    $fraction = 1.0
    if ($entry.PSObject.Properties.Name -contains 'fraction') {
        $fraction = [double]$entry.fraction
    }

    if ($entry.PSObject.Properties.Name -contains 'copy') {
        foreach ($prop in $entry.copy.PSObject.Properties) {
            $src = Join-Path $RepoRoot $prop.Name
            $dst = Join-Path $RepoRoot $prop.Value
            Copy-Item -Path $src -Destination $dst -Force
        }
    }

    $paths = @()
    if ($entry.PSObject.Properties.Name -contains 'paths') {
        $paths = @($entry.paths)
    }

    $files = Get-RepoFiles -Paths $paths -Fraction $fraction
    if ($files.Count -eq 0 -and $paths.Count -eq 0) {
        Write-Warning "No paths for commit: $($entry.message)"
        continue
    }

    foreach ($f in $files) {
        if ($fraction -lt 1.0) {
            Apply-Fraction -RelativePath $f -Fraction $fraction
        }
    }

    if ($entry.PSObject.Properties.Name -contains 'templates') {
        foreach ($prop in $entry.templates.PSObject.Properties) {
            $dest = Join-Path $RepoRoot $prop.Name
            $src = Join-Path $RepoRoot ([string]$prop.Value)
            if (Test-Path $src) {
                Copy-Item -Path $src -Destination $dest -Force
            }
        }
    }

    if ($DryRun) {
        Write-Host "[DRY] $($entry.date) $($entry.message) ($($files.Count) files)"
        continue
    }

    foreach ($f in $files) {
        git add -- "$f" 2>$null | Out-Null
    }

    $ts = "$($entry.date)T$($entry.time)"
    $env:GIT_AUTHOR_DATE = $ts
    $env:GIT_COMMITTER_DATE = $ts
    git commit -m $entry.message --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Commit failed (maybe empty?): $($entry.message)"
    } else {
        $commitCount++
        Write-Host "[$commitCount] $($entry.date) $($entry.message)"
    }
}

if (-not $DryRun) {
    # Final parity: anything not yet tracked (respecting .gitignore)
    Restore-FromSnapshot $SnapshotRoot
    git add -A
    $pending = git status --porcelain
    if ($pending) {
        $env:GIT_AUTHOR_DATE = "2026-08-31T12:40:00"
        $env:GIT_COMMITTER_DATE = $env:GIT_AUTHOR_DATE
        git commit -m "Integration pass: sync remaining research artifacts" --quiet
        $commitCount++
        Write-Host "[parity] Remaining files committed."
    }

    Remove-Item env:GIT_AUTHOR_DATE -ErrorAction SilentlyContinue
    Remove-Item env:GIT_COMMITTER_DATE -ErrorAction SilentlyContinue

    git branch -D master 2>$null
    git branch -m master
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "History rebuild complete: $commitCount commits on master" -ForegroundColor Green
    Write-Host "Verify: git log --oneline --graph --date=short" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
}

Remove-Item -Recurse -Force $SnapshotRoot -ErrorAction SilentlyContinue
