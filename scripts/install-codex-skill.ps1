param(
    [string]$CodexHome = $env:CODEX_HOME,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $CodexHome) {
    $CodexHome = Join-Path $HOME ".codex"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $repoRoot "skill"
$targetRoot = Join-Path $CodexHome "skills"
$targetDir = Join-Path $targetRoot "brand-reputation-monitor"

if (-not (Test-Path $sourceDir)) {
    throw "Source skill directory not found: $sourceDir"
}

New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null

if (Test-Path $targetDir) {
    if (-not $Force) {
        throw "Target already exists: $targetDir . Re-run with -Force to replace it."
    }
    Remove-Item -Recurse -Force $targetDir
}

Copy-Item -Recurse -Force $sourceDir $targetDir

Write-Host "Installed brand-reputation-monitor to $targetDir"
