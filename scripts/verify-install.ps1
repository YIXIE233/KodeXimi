#!/usr/bin/env pwsh
#Requires -Version 7.0
# coding: utf-8
[CmdletBinding()]
param(
    [switch]$Installed,
    [string]$Path
)

$ErrorActionPreference = "Stop"
if ($Path) { $Target = $Path }
elseif ($Installed) { $Target = Join-Path $HOME ".kodeximi" }
else { $Target = Split-Path -Parent $PSScriptRoot }

$checks = @{
    "Taskflow directory" = Test-Path -LiteralPath $Target
    "CLI script"        = Test-Path -LiteralPath (Join-Path $Target "cli\kodeximi.ps1")
    "Kimi agent YAML"   = Test-Path -LiteralPath (Join-Path $Target "kimi\agents\codex-worker.yaml")
    "Kimi system MD"    = Test-Path -LiteralPath (Join-Path $Target "kimi\agents\codex-worker-system.md")
    "Task templates"    = Test-Path -LiteralPath (Join-Path $Target "templates\task\TASK.md")
    "Batch templates"   = Test-Path -LiteralPath (Join-Path $Target "templates\batch\BATCH_MANIFEST.json")
}

$failed = $checks.GetEnumerator() | Where-Object { -not $_.Value }
if (-not $failed) {
    Write-Host "verify-install: OK ($Target)" -ForegroundColor Green
    exit 0
}
Write-Host "verify-install: MISSING ($Target)" -ForegroundColor Red
foreach ($f in $failed) { Write-Host "  MISSING: $($f.Key)" }
exit 1



