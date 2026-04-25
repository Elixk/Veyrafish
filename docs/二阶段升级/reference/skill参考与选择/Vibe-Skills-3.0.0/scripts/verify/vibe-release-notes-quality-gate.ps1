[CmdletBinding()]
param(
    [string[]]$Path,
    [string]$RepoRoot,
    [string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

$runnerPath = Join-Path $RepoRoot 'scripts\verify\runtime_neutral\release_notes_quality.py'
if (-not (Test-Path -LiteralPath $runnerPath)) {
    throw "release notes quality runner missing: $runnerPath"
}

$pythonCommand = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
    throw 'Python is required to run vibe-release-notes-quality-gate.'
}

$args = @(
    $runnerPath
    '--repo-root', $RepoRoot
    '--write-artifacts'
)
foreach ($item in @($Path)) {
    if ([string]::IsNullOrWhiteSpace([string]$item)) {
        continue
    }
    $args += @('--path', (Resolve-Path $item).Path)
}
if ($OutputDirectory) {
    $args += @('--output-directory', $OutputDirectory)
}

& $pythonCommand.Source @args
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw "vibe-release-notes-quality-gate failed with exit code $exitCode"
}

Write-Host '[PASS] vibe-release-notes-quality-gate passed' -ForegroundColor Green
